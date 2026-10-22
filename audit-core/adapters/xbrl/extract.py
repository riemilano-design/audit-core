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


# ---------------------------------------------------------------------------
# P26 G5(封 docs/XBRL_P26_SEAL_2026-10-21.md §1): 数の読み取りの 3 つの連結。profile.numbers_2026_10_21 が真のときだけ
# recipes から呼ばれる。``iter_numbers`` は 1 字も変えない(写し元との照合 test_lineage はそのまま)。
#   兆と億: 「2兆3,471億円」(億の数にカンマ。既存の AMOUNT_JP_RE は億の数にカンマを許さず、NUM_RE が「3,471億円」だけを読む)
#   万と千: 「6万5千円」(既存は 千 を 万 の前の位として読むので「5千円」だけを読む)
#   円と銭: 「148円22銭」(既存は「148円」だけを読む)
# 当たった範囲は既存の読みより先に取り、既存の読みのうち範囲が重なるものは捨てる。単位は「円」、精度は書かれた最小の位。
# ---------------------------------------------------------------------------
_SIGN_2026_10_21 = r"(?<![\d.,])(△|▲|－|-|マイナス)?\s*"
_CHO_OKU_RE_2026_10_21 = re.compile(_SIGN_2026_10_21 + r"(\d+(?:\.\d+)?)兆(\d{1,3}(?:,\d{3})+)億円")
_MAN_SEN_RE_2026_10_21 = re.compile(_SIGN_2026_10_21 + r"(\d{1,3}(?:,\d{3})+|\d+)万(\d+)千(?:(\d+)百)?円")
_YEN_SEN_RE_2026_10_21 = re.compile(_SIGN_2026_10_21 + r"(\d{1,3}(?:,\d{3})+|\d+)円(\d{1,2})銭")


def _joined_numbers_2026_10_21(s):
    for m in _CHO_OKU_RE_2026_10_21.finditer(s):
        yen = float(m.group(2)) * 1e12 + float(m.group(3).replace(",", "")) * 1e8
        yield m.start(), m.end(), (-1 if m.group(1) else 1) * yen, "円", 1e8
    for m in _MAN_SEN_RE_2026_10_21.finditer(s):
        yen = float(m.group(2).replace(",", "")) * 1e4 + float(m.group(3)) * 1e3
        prec = 1e3
        if m.group(4):
            yen += float(m.group(4)) * 1e2
            prec = 1e2
        yield m.start(), m.end(), (-1 if m.group(1) else 1) * yen, "円", prec
    for m in _YEN_SEN_RE_2026_10_21.finditer(s):
        yen = float(m.group(2).replace(",", "")) + float(m.group(3)) / 100.0
        yield m.start(), m.end(), (-1 if m.group(1) else 1) * yen, "円", 0.01


def iter_numbers_2026_10_21(s):
    """``iter_numbers`` に G5 の 3 つの連結を足した読み。連結に当たった範囲と重なる既存の読みは捨てる。"""

    joined = sorted(_joined_numbers_2026_10_21(s), key=lambda t: t[0])
    kept = []
    for t in joined:
        if not any(a < t[1] and t[0] < b for a, b, _v, _u, _p in kept):
            kept.append(t)
    rest = [t for t in _iter_numbers(s) if not any(a < t[1] and t[0] < b for a, b, _v, _u, _p in kept)]
    return sorted(kept + rest, key=lambda t: t[0])


# P17 B1(計画 docs/P17_PLAN_2026-10-14.md §1): 原因の印。字で書く。
CAUSE_MARK_RE = re.compile(r"により|による|によって")


def _is_topic(sentence, i, word):
    """語の直後が「は」(「営業外費用は、」)なら、その語は文の主題。"""

    return sentence[i + len(word):i + len(word) + 1] == "は"


def subject_of(sentence, pos, subjects, skip=None, cause_topic=False):
    """数の直前(同じ文)でいちばん近い主語。終わりの位置が最も右のものを取り、
    同じなら長い語(「純資産合計」>「資産合計」)。道具の直し P-3。xbrl_probe.py: subject_of の写し
    (差分は固定の SUBJECTS グローバルの代わりに引数で受け取るだけ)。

    ``skip``(主語の規則の直し、人間の判断 1、2026-10-08)は
    ``skip(sentence, i, word) -> bool`` の関数で、真を返した候補は**採らずに
    次の候補へ進む。** 順位の付け方(終わりがいちばん右 → 長い語 → 一覧の
    早い方)は**変えない** ― 変えるのは「その候補を採ってはいけない形」を
    足すところだけである。

    ``skip`` が ``None`` のとき、返す値は写し元と 1 つも変わらない
    (P1〜P14 はすべて ``None``)。順位どおりに並べて先頭を採るのは、
    写し元の「``end > best`` か(``end ==`` かつ長い)で置き換える」と同じ
    勝ち方である ― 同じ終わり・同じ長さなら**一覧の早い方**が勝つ。
    これは ``tests/adapters/xbrl/test_lineage.py`` が実物の 2 書類の全部の文で
    写し元と照合しており、``test_extract.py`` が 4 書類 × P13 の語彙で
    写し元の書き方そのものと照合する。
    """

    head = sentence[:pos]
    ranked = []
    for order, (word, elems) in enumerate(subjects):
        i = head.rfind(word)
        if i < 0:
            continue
        ranked.append((-(i + len(word)), -len(word), order, i, word, elems))
    ranked.sort()
    # P17 B1: ``cause_topic`` が真のときだけ。候補と数の間に原因の印が在り、
    # その候補より前に「〜は」の候補が在れば、その候補を飛ばす(主題の候補
    # 自身は、それより前に主題が無い限り飛ばさない)。偽なら 1 つも変わらない。
    topic_starts = [i for (_e, _l, _o, i, word, _el) in ranked if _is_topic(sentence, i, word)] if cause_topic else []
    for (_e, _l, _o, i, word, elems) in ranked:
        if skip is not None and skip(sentence, i, word):
            continue
        if cause_topic and any(t < i for t in topic_starts) and CAUSE_MARK_RE.search(sentence[i + len(word):pos]):
            continue
        return (word, elems)
    return (None, None)


# ---------------------------------------------------------------------------
# 主語の規則の直し(人間の判断 1、2026-10-08)― **採ってはいけない形**。
# 広い規則(「は」が付く語を優先する)は 4 書類で測って却下した
# (docs/XBRL_SUBJECT_RULE_PLAN_2026-10-08.md §0)。ここに在るのは
# ``subject_of`` の順位を変えずに**候補を 2 つの形で拒否する**規則だけである。
#
# 字は字で書く(定数から土台を作らない)。
# ---------------------------------------------------------------------------
COORDINATORS = ("及び", "並びに")       # S1・S3 の並立の接続語
CAUSE_SUFFIXES = ("による", "により")   # S1 の原因の言い方
AGGREGATE_SUFFIXES = ("の合計", "の合計額")  # S3 の「合計」の言い方
CLAUSE_BREAKS = "、。，（）()"           # 節の切れ目


def clause_span(sentence, start, end):
    """``sentence[start:end]`` を含む**節**の範囲 ``(左, 右)``。
    節の切れ目は ``、。``・全角半角の丸括弧。文に区切りが無ければ文全体。

    節に限るのは、**文に限ると列挙の文で他の項目の材料を拾う**からである。
    """

    left = 0
    for k in range(start - 1, -1, -1):
        if sentence[k] in CLAUSE_BREAKS:
            left = k + 1
            break
    right = len(sentence)
    for k in range(end, len(sentence)):
        if sentence[k] in CLAUSE_BREAKS:
            right = k
            break
    return left, right


# 並立の成分かどうかを見るときに「ここで句が切れる」と見なす助詞。字で書く。
# 「特別損失**は**固定資産除却損及び…」の「特別損失」を並立の成分に
# 数えないために要る。
PARTICLES = ("は", "が", "を", "に")


def _is_coordinated(sentence, start, end):
    """候補の語が並立の成分か。次のどちらかなら真。

    (a) 並立の接続語に**直に**隣り合っている(前でも後ろでもよい)。
    (b) 候補の終わりから節の終わりへ右に進んだとき、**最初に当たるのが
        並立の接続語**である(助詞 ``は``/``が``/``を``/``に`` が先に来たら偽)。

    (b) が要るのは、(a) だけだと**飛ばした語の部分文字列が残る**からである ―
    「特別損失は固定資産除却損及び減損損失による25百万円」で
    「減損損失」と「固定資産除却損」を飛ばしても、語彙に在る「固定資産」が
    「固定資産除却損」の中に残り、「特別損失」より右で終わるので勝ってしまう
    (**1 回目の実測でこれが起きた。** 封じた予測「N069 が GROUNDED」は
    この穴で外れた)。(b) は「固定資産」の右が「除却損及び」= 助詞より先に
    並立の接続語なので真になり、部分文字列も一緒に飛ぶ。

    「特別損失」の右は ``は`` なので (b) は偽 ― **落ちない。**
    """

    for c in COORDINATORS:
        if sentence[max(0, start - len(c)):start] == c:
            return True
        if sentence[end:end + len(c)] == c:
            return True
    _left, right = clause_span(sentence, start, end)
    tail = sentence[end:right]
    first = None
    for token in COORDINATORS + PARTICLES:
        i = tail.find(token)
        if i < 0:
            continue
        if first is None or i < first[0]:
            first = (i, token)
    return first is not None and first[1] in COORDINATORS


def skip_coordinated_cause(sentence, start, word):
    """S1。候補が並立の成分で、その先(同じ節の中)に ``による``/``により`` が
    在るなら採らない。名指しされているのは**原因の並び**であって、
    その文の数の持ち主ではない。
    """

    end = start + len(word)
    if not _is_coordinated(sentence, start, end):
        return False
    _left, right = clause_span(sentence, start, end)
    tail = sentence[end:right]
    return any(suffix in tail for suffix in CAUSE_SUFFIXES)


def skip_part_of_aggregate(sentence, start, word):
    """S3。候補が並立の成分で、その先(同じ節の中)に ``の合計``/``の合計額`` が
    在るなら採らない。名指しされているのは**合計**であって成分ではない。
    """

    end = start + len(word)
    if not _is_coordinated(sentence, start, end):
        return False
    _left, right = clause_span(sentence, start, end)
    tail = sentence[end:right]
    return any(suffix in tail for suffix in AGGREGATE_SUFFIXES)


# S2(主語の規則の直し): 「<名詞>を増加/減少」。向きが掛かっているのは
# **その目的語**である。節を跨がないように ``[^、。]`` で区切る。
# 向きの語は字で書く(``DIRECTION_WORDS`` から土台を作らない ― この形を採る
# のは「他動詞として使える向きの語」だけで、`拡大`・`伸び` は入れない)。
DIRECTION_OBJECT_RE = re.compile(r"([^、。]{2,12})を(増加|減少|改善|悪化|押し上げ|押し下げ)")


def direction_object(sentence, pos):
    """S2。``sentence`` の ``pos`` から始まる向きの語が「<名詞>を」の形の
    他動詞として使われていれば、その名詞。そうでなければ ``None``。
    """

    for m in DIRECTION_OBJECT_RE.finditer(sentence):
        if m.start(2) == pos:
            return m.group(1)
    return None


def subject_skip_for(profile):
    """profile の 2 つのフラグから ``subject_of`` に渡す ``skip`` を作る。
    どちらも偽なら ``None`` を返す ― **P1〜P14 はここで ``None`` になり、
    ``subject_of`` の振る舞いが 1 つも変わらない。**
    """

    rules = []
    if getattr(profile, "subject_skip_coordinated_cause", False):
        rules.append(skip_coordinated_cause)
    if getattr(profile, "subject_not_part_of_aggregate", False):
        rules.append(skip_part_of_aggregate)
    if not rules:
        return None

    def skip(sentence, start, word):
        return any(rule(sentence, start, word) for rule in rules)

    return skip


def own_sign_match(window, num):
    """P-8。窓の中の PCT_DIR_RE の一致を全部見て、数字がこの数と同じものだけを
    返す。xbrl_probe5.py: own_sign_match の写し。
    """

    for pm in PCT_DIR_RE.finditer(window):
        g = pm.group(2) or pm.group(5)
        if g is not None and abs(float(g) - num) < 1e-9:
            return pm
    return None


# ---------------------------------------------------------------------------
# XBRL 直し §4(人間の決定、2026-10-08): 括弧の中の句点では文を切らない。
# ``profile.paren_sentence`` が真のときだけ使う(P1/P5F/P6/P7 は偽で、
# 凍結の切り方 ``re.split(r"(?<=。)|\n")`` のまま 1 文字も変わらない)。
# 開き括弧・閉じ括弧の字は字で書く(定数から土台を作らない)。
# ---------------------------------------------------------------------------
PAREN_OPEN = "(（"
PAREN_CLOSE = ")）"


def split_after_kuten_outside_parens(line, paren_open=PAREN_OPEN, paren_close=PAREN_CLOSE):
    """1 行を 。 の直後で切る。ただし丸括弧の中の 。 では切らない。

    「(以下「資金」という。)は、…減少し、26 億 5 百万円となりました。」が
    2 つに切れて主語を失うのを防ぐのが目的(``N043``/``T025``)。
    閉じ括弧が余っていても深さは 0 より下げない(壊れた括弧で全体が
    1 文に潰れないため)。
    """

    out, depth, start = [], 0, 0
    for i, ch in enumerate(line):
        if ch in paren_open:
            depth += 1
        elif ch in paren_close:
            depth = depth - 1 if depth > 0 else 0
        elif ch == "。" and depth == 0:
            out.append(line[start:i + 1])
            start = i + 1
    out.append(line[start:])
    return out


def _split_lines(text, paren_aware):
    """段落(``\n`` で切った 1 行)ごとの文の列。段落の番号を数えるのと
    文の列を作るのが同じ 1 か所から出るようにしておく。
    """

    for pi, para in enumerate(text.split("\n")):
        pieces = split_after_kuten_outside_parens(para) if paren_aware else re.split(r"(?<=。)", para)
        for s in pieces:
            if s and s.strip():
                yield pi, unicodedata.normalize("NFKC", s.strip())


def paragraph_index(text, sentences, paren_aware=False):
    """文の切り方(``paren_aware`` が偽なら凍結の ``re.split(r"(?<=。)|\\n")``)
    と同じ列になることを確かめながら、文ごとの段落番号を作る。
    xbrl_probe3.py: paragraph_index の写し(``paren_aware`` の枝だけが新しい)。
    """

    paras, check = [], []
    for pi, s in _split_lines(text, paren_aware):
        paras.append(pi)
        check.append(s)
    assert check == sentences, "paragraph split diverged from the sentence split"
    return paras


def split_sentences(text, paren_aware=False):
    """xbrl_probe.py main(): NFKC + 文の切り方(``re.split(r"(?<=。)|\\n")``)の
    写し。``paren_aware`` が真のときだけ、丸括弧の中の 。 では切らない(§4)。
    """

    if not paren_aware:
        return [unicodedata.normalize("NFKC", s.strip()) for s in re.split(r"(?<=。)|\n", text) if s and s.strip()]
    return [s for _pi, s in _split_lines(text, True)]


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


# P17 A''(計画 docs/P17_PLAN_2026-10-14.md §5・§6。A は 16 書類で GROUNDED を 71 件失って棄却、
# A' は従来の段落内の引き継ぎを消していて 3 件失った): 従来の引き継ぎ(同じ段落で 5 文以内)は
# そのままに、**結果の文**にだけ段落をまたいだ引き継ぎを足す。印は字で書く。
TOPIC_MARK_RE = re.compile(r"につきましては")
RESULT_HEAD_RE = re.compile(r"^(以上の結果|この結果|その結果|結果として)")
CONSOL_WORDS_IN_RESULT = ("当社グループ", "連結", "全社")   # 結果の文自身に在れば引き継がない
CONSOL_WORDS_BETWEEN = ("当社グループ", "全社")             # 途中の文に在れば引き継がない(「連結」は途中では印にしない: 「当連結会計年度におきましては」が事業の段落の中に在る)


def resolve_members_to_result_sentence(sentences, paras, reg, carry_back=CARRY_BACK, topic_re=TOPIC_MARK_RE,
                                       result_re=RESULT_HEAD_RE, consol_in_result=CONSOL_WORDS_IN_RESULT,
                                       consol_between=CONSOL_WORDS_BETWEEN):
    """P17 A''。``resolve_members``(段落内の引き継ぎ)の結果を土台に、事業名が
    付かなかった**結果の文**(``result_re`` で始まり ``consol_in_result`` を含まない)
    にだけ、段落に関係なく ``carry_back`` 文以内の直前の「文の事業名」
    (source == "sentence")を引き継ぐ。途中の文に新しい話題の印(``topic_re``)・
    ``consol_between`` の語が在るか、途中の文が曖昧(2 事業)なら引き継がない。"""

    res = list(resolve_members(sentences, paras, reg, carry_back))
    for si, s in enumerate(sentences):
        if res[si][1] is not None:
            continue
        if not (result_re.search(s) and not any(w in s for w in consol_in_result)):
            continue
        found = None
        for sj in range(si - 1, max(-1, si - 1 - carry_back), -1):
            if res[sj][1] == "sentence":
                found = res[sj][0]
                break
            if res[sj][1] == "ambiguous":
                break
            if topic_re.search(sentences[sj]) or any(w in sentences[sj] for w in consol_between):
                break
        if found:
            res[si] = (found, "carried")
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
