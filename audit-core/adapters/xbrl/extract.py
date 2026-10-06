# -*- coding: utf-8 -*-
"""Sentence splitting, number extraction, subject matching, direction/state
words, and member attribution (sentence-level and Claim-level).

A transcription of ``fixtures/xbrl/xbrl_probe.py`` (``NUM_RE``,
``AMOUNT_JP_RE``, ``EXCLUDE_AFTER``, ``EXCLUDE_CONTEXT``, ``PCT_DIR_RE``,
``PCT_RATIO_RE``, ``iter_numbers``, ``subject_of``, ``DIRECTION_WORDS``,
``STATE_WORDS``), ``fixtures/xbrl/xbrl_probe3.py`` (``paragraph_index``,
``build_registry``, ``resolve_members``, ``CARRY_BACK``, ``AMBIG``), and
``fixtures/xbrl/xbrl_probe4.py`` / ``xbrl_probe5.py`` (``claim_member_B``,
``MARK_CONSOL``, ``CONN_RE``, ``own_sign_match``). Not imported from the
originals; compared value-for-value by ``tests/adapters/xbrl/test_lineage.py``.
"""

import json
import os
import re
import unicodedata

from . import vocabulary as V

# ---------------------------------------------------------------------------
# 文は NFKC で正規化してから当てる(全角数字・全角 % を半角に。道具の直し P-1)
# ---------------------------------------------------------------------------
NUM_RE = re.compile(
    r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s*"
    r"(百万円|千円|億円|兆円|円|％|%|ポイント|名|人|店舗|店|件|社|倍|台|千株|株|トン|kl|ｋｌ)"
)
# 漢数字混じりの金額(380億6千4百万円 / 3億円 / 9千3百万円 / 26億5百万円)。道具の直し P-1
AMOUNT_JP_RE = re.compile(
    r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*(?:(\d+(?:\.\d+)?)兆)?(?:(\d+(?:\.\d+)?)億)?"
    r"(?:(\d+)千)?(?:(\d+)百)?(?:(\d+)?(万))?円"
)
EXCLUDE_AFTER = re.compile(r"^(年|月|日|期|頁|ページ|四半期|号|条|項|回目)")
EXCLUDE_CONTEXT = re.compile(r"(第\s*\d+\s*四半期|\d{4}年\d{1,2}月|\d{1,2}月\d{1,2}日|令和\s*\d+|平成\s*\d+|※\s*\d|注\s*\d)")
PCT_DIR_RE = re.compile(r"(前年同期比|前期比|前連結会計年度比|前年度比|前年比)\s*(\d+(?:\.\d+)?)\s*(％|%)\s*(増|減)|(\d+(?:\.\d+)?)\s*(％|%)\s*(増|減|増加|減少)")
# 「前連結会計年度比 106.0%」「(同 102.9%)」= 当期 / 前期 × 100 の比(道具の直し P-2)
PCT_RATIO_RE = re.compile(r"(前連結会計年度比|前年同期比|前期比|前年度比|前年比|同)\s*(\d+(?:\.\d+)?)\s*(％|%)(?!\s*(増|減))")

DIRECTION_WORDS = {
    "増収": +1, "増益": +1, "増加": +1, "増え": +1, "上回": +1, "伸び": +1, "増大": +1, "拡大": +1, "改善": +1,
    "減収": -1, "減益": -1, "減少": -1, "減り": -1, "下回": -1, "縮小": -1, "悪化": -1, "低下": -1,
}
STATE_WORDS = ["堅調", "好調", "底堅", "厳しい", "低調", "回復", "軟調", "横ばい", "順調", "不透明", "持ち直し", "足踏み", "減速", "加速"]

CARRY_BACK = 5  # xbrl_probe3.py §3.1-2: 同じ段落で 5 文以内
AMBIG = "<ambiguous>"  # 1 文に 2 つ以上の事業名
MARK_CONSOL = "全社"  # xbrl_probe4.py 変更 B の連結の印(「連結」は印にしない)
CONN_RE = re.compile(r"^[、,及びおよびとや・\s]*$")  # 列挙の接続語だけか

XLINK = "{http://www.w3.org/1999/xlink}"


def iter_numbers(s):
    """文の中の数を位置順に (start, end, 値, 単位, 主張の精度) で返す。
    漢数字混じりの金額は円に直し、精度は書かれた最小の位。xbrl_probe.py: iter_numbers の写し。
    """

    return sorted(_iter_numbers(s), key=lambda t: t[0])


def _iter_numbers(s):
    taken = []
    for m in AMOUNT_JP_RE.finditer(s):
        if not any(m.group(i) for i in (2, 3, 4, 5, 6)):
            continue
        big = bool(m.group(2) or m.group(3) or m.group(7))
        mults = {2: 1e12, 3: 1e8, 4: 1e7 if big else 1e3, 5: 1e6 if big else 1e2, 6: 1e4}
        yen = 0.0
        prec = None
        for i in (2, 3, 4, 5, 6):
            if m.group(i):
                yen += float(m.group(i)) * mults[i]
                prec = mults[i]
        if m.group(7) and not m.group(6) and prec is None:
            continue
        sign = -1 if m.group(1) else 1
        taken.append((m.start(), m.end()))
        yield m.start(), m.end(), sign * yen, "円", prec
    for m in NUM_RE.finditer(s):
        if any(a <= m.start() < b for a, b in taken):
            continue
        sign = -1 if m.group(1) else 1
        num = float(m.group(2).replace(",", "") + (m.group(3) or ""))
        unit = m.group(4)
        yield m.start(), m.end(), sign * num, unit, (V.UNIT_SCALE.get(unit) or 1.0)


def subject_of(sentence, pos, subjects):
    """数の直前(同じ文)でいちばん近い主語。終わりの位置が最も右のものを取り、
    同じなら長い語(「純資産合計」>「資産合計」)。道具の直し P-3。xbrl_probe.py: subject_of の写し
    (差分は固定の SUBJECTS グローバルの代わりに引数で受け取るだけ)。
    """

    head = sentence[:pos]
    best = None
    for word, elems in subjects:
        i = head.rfind(word)
        if i < 0:
            continue
        end = i + len(word)
        if best is None or end > best[0] or (end == best[0] and len(word) > len(best[1])):
            best = (end, word, elems)
    return (best[1], best[2]) if best else (None, None)


def own_sign_match(window, num):
    """P-8。窓の中の PCT_DIR_RE の一致を全部見て、数字がこの数と同じものだけを
    返す。xbrl_probe5.py: own_sign_match の写し。
    """

    for pm in PCT_DIR_RE.finditer(window):
        g = pm.group(2) or pm.group(5)
        if g is not None and abs(float(g) - num) < 1e-9:
            return pm
    return None


def paragraph_index(text, sentences):
    """凍結の文の切り方(re.split(r"(?<=。)|\\n"))と同じ列になることを確かめ
    ながら、文ごとの段落番号を作る。xbrl_probe3.py: paragraph_index の写し。
    """

    paras, check = [], []
    for pi, para in enumerate(text.split("\n")):
        for s in re.split(r"(?<=。)", para):
            if s and s.strip():
                paras.append(pi)
                check.append(unicodedata.normalize("NFKC", s.strip()))
    assert check == sentences, "paragraph split diverged from frozen sentence split"
    return paras


def split_sentences(text):
    """xbrl_probe.py main(): NFKC + 文の切り方(re.split(r"(?<=。)|\\n"))の写し。"""

    return [unicodedata.normalize("NFKC", s.strip()) for s in re.split(r"(?<=。)|\n", text) if s and s.strip()]


def build_registry(members, id2label, text, run3, registry_path=None):
    """Run L: ラベルが MD&A の本文に現れる member だけ(人は書かない)。
    Run R: 手書きの登録簿 {事業名: member} を足す。xbrl_probe3.py: build_registry の写し。
    """

    reg = {}
    rows = []
    for m in members:
        mid = m.replace(":", "_")
        lab = id2label.get(mid)
        in_text = bool(lab) and lab in text
        rows.append({"member": m, "label": lab, "label_in_mdna": in_text, "source": "label" if in_text else None})
        if in_text:
            reg[m] = lab
    hand = {}
    if run3 == "R" and registry_path and os.path.exists(registry_path):
        hand = json.load(open(registry_path, encoding="utf-8"))
        for name, m in hand.items():
            if m in reg:
                continue
            reg[m] = unicodedata.normalize("NFKC", name)
            for r in rows:
                if r["member"] == m:
                    r["source"] = "hand"
    return reg, rows, hand


def resolve_members(sentences, paras, reg, carry_back=CARRY_BACK):
    """§3.1-2。文ごとに (member, source)。source は sentence / carried / ambiguous / None。
    xbrl_probe3.py: resolve_members の写し。
    """

    res = []
    for si, s in enumerate(sentences):
        hits = sorted({m for m, name in reg.items() if name and name in s})
        if len(hits) == 1:
            res.append((hits[0], "sentence"))
        elif len(hits) >= 2:
            res.append((AMBIG, "ambiguous"))
        else:
            found = None
            for sj in range(si - 1, max(-1, si - 1 - carry_back), -1):
                if paras[sj] != paras[si]:
                    break
                if res[sj][1] == "sentence":
                    found = res[sj][0]
                    break
            res.append((found, "carried" if found else None))
    return res


def claim_member_B(s, pos, reg, fallback, mark_consol=MARK_CONSOL, conn_re=CONN_RE):
    """予測 §3.2。head = 文の Claim より前。いちばん右の印で決める。印が無ければ
    3 本目の文単位の値(fallback)。xbrl_probe4.py: claim_member_B の写し。
    """

    head = s[:pos]
    marks = []
    for mem, name in reg.items():
        for mm in re.finditer(re.escape(name), head):
            marks.append((mm.start(), mm.end(), "seg", mem))
    for mm in re.finditer(mark_consol, head):
        marks.append((mm.start(), mm.end(), "all", None))
    if not marks:
        return fallback
    marks.sort()
    last = marks[-1]
    if last[2] == "all":
        return (None, "consolidated")
    group = [last]
    cur = last
    for mk in reversed(marks[:-1]):
        if mk[2] != "seg":
            break
        if conn_re.match(head[mk[1]:cur[0]]):
            group.append(mk)
            cur = mk
        else:
            break
    if len({g[3] for g in group}) == 1:
        return (last[3], "claim")
    return (AMBIG, "ambiguous")
