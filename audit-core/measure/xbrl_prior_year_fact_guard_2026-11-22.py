# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md(XZ1 ― 前の年の下書きが黙って違う属性を付ける fact を、行の順で番号を振り直す規則と表の頭の字の守りで直す・止める)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** engine(``core/``・``adapters/``)は 1 行も変えない。行の切り方(``_TR_RE``)は engine の関数を呼ぶ。
便 XZ0 の script の関数(``read_rows``・``build_tables``・``stage_ht``・``classify6``・``bundle3``・``texts_rows``・``norm_label``・``TABLE_RE``・``FACT_RE`` など)と、そこから届く便 XY0 の ``make_pairs``・便 XG1 の ``doc_texts`` は
importlib で読んで呼ぶ(写さない)。

    python3 measure/xbrl_prior_year_fact_guard_2026-11-22.py            # 置き場から数えて記録 fixtures/xbrl/cd8/prior_year_fact_guard_2026-11-22.json を排他で書く。通信しない
    python3 measure/xbrl_prior_year_fact_guard_2026-11-22.py --check    # 置き場から数え直して記録と照らす。通信しない

置き場の既定は便 XZ0 と同じ(今年の側 ``~/.cache/audit-core/edinet/``・前の年の側 ``~/.cache/audit-core/edinet-prior-2026-11-02/``)。読むのは PublicDoc の ``_ixbrl.htm`` だけ。
**今年の fact の属性は、類分けにだけ使い、候補(表 HT・表 COL・段 HT・O・G・OG)の作りには渡さない。**
段 HT の組ごとの類の数が便 XZ0 の記録(``fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json``)の同じ番号の「束 3」「HT」と 1 つでも違えば止まる(封 §4)。番号 4 以上の組(60 組)の fact の合計が 61100 でなければ止まる(封 §3)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 組の番号は便 XZ0 の記録と同じ番号(今年の側の 67 本の昇順の位置。除いた書類の番号は飛ぶ)。「60 組」= 番号 4 以上・「3 組」= 番号 3 以下(封 §0 の「番号 4〜63」は番号が 63 組の通し番号でなく便 XZ0 の記録の番号なので、4 以上と読む。合計 61100 がその根拠)。
- 封 §2-1 の「2 つ目より後ろの部品」は、``_`` で切った 2 つ目以降(先頭の部品だけを除く)と読む。根拠: 先頭は期の名で、2 つ目から軸のメンバーが並ぶ。「2 つ目を除く」と読むと単独のメンバーの文脈に形が無くなる。
- 形の字は、当たった部品の数字の並びを ``#`` に置き換えたもの(``No#Member``・``Row#AMember`` のように後ろの字は残す)。段 O の候補は ``#`` を k の字(10 進)に全部置き換える。
- 封 §2-3 の表 COL の鍵 (h, th, td) は、表 HT の鍵の行の字 T を落としたもの(th は便 XZ0 の th)。「同じ表」は (file 名の昇順の位置, 表の通し番号) が同じこと。
- 封 §2-3 の「番号の列を使う fact」の「候補の中に形の在る文脈が 1 つでも在り」は、表 HT の候補(束 3)の contextRef のどれかに形が在ること。
- 封 §2-4 の「最初に数の fact を持つ行」は、``FACT_RE`` に当たる開きタグ(空の欄を含む)を行の字の中に持つ行(行の字 T が空の行も含む)。その表にそういう行が 1 つも無ければ表の全部の行が頭。表の頭の印は行の字を ``|`` でつないだ字(空の字の行も 1 つとして並べる)。
- 数字を除く: ``norm_label`` のあとに ``[0-9]`` を除く(``norm_label`` が全角の数字を半角にするので、全角の数字も除かれる)。
- 封 §2-5 の「同じ鍵 (h, th, T, td) に束を入れた行」は、前の年の側の T が空でない行で、その鍵に fact を 1 つ以上持つ行(空の欄も含む。表 HT と同じ)。段 OG の番号の列を使う fact は、表 COL に束(形の在る文脈の fact)を入れた行の表の頭の印の集まりと比べる。
- 類 S は段 HT(段 O)の類が U・A・W1・W2(候補が 1 つ以上)のときだけ付く。X・N は止めない。
- 封 §2-7 の「違う属性の組」は W1(候補がちょうど 1 つ)の候補と今年の束 3 を属性ごとに比べた、違う属性の集まり(name・contextRef・unitRef の 7 通り)。「番号だけの違い」は contextRef が違い、name と unitRef は同じで、候補と今年の contextRef の両方に形が在り、形が同じ。
- 先に自分の欠陥を疑う旗の S の率は、段 G と段 OG のそれぞれを 60 組の fact の合計で割る(止めず、記録に旗の欄として書く)。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import bisect
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

from adapters.xbrl import verify_document as VD         # noqa: E402


def _load_draft():
    u"""便 XZ0 の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。便 XZ0 の script が便 XY0・XG1・XG0 の script を読む。"""
    name = "_xz1_prior_year_fact_draft_2026_11_22"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "xbrl_prior_year_fact_draft_2026-11-22.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


Z = _load_draft()
Y = Z.Y
N = Z.N
W = Z.W
Stop = Z.Stop
od = collections.OrderedDict
pct1 = Z.pct1
dumps = Z.dumps
norm_label = Z.norm_label
sha256_bytes = Z.sha256_bytes
sha256_file = Z.sha256_file

SEAL_REL = "docs/XBRL_PRIOR_YEAR_FACT_GUARD_SEAL_2026-11-22.md"
SEAL_COMMIT = "2079af62"
SCRIPT_REL = "measure/xbrl_prior_year_fact_guard_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_guard_2026-11-22.json"
DRAFT_RECORD_REL = "fixtures/xbrl/cd8/prior_year_fact_draft_2026-11-22.json"
DOCS_DIR = Z.DOCS_DIR
PRIOR_DIR = Z.PRIOR_DIR
DOCS_WANT = Z.DOCS_WANT
PAIRS_WANT = 63
CLASSES = Z.CLASSES                     # X・U・A・W1・W2・N
STOP_CLASS = "S"
STAGES4 = ("HT", "O", "G", "OG")
ATTRS3 = Z.ATTRS3
#: 組の番号の分け(封 §2-9・§3): 番号がこの値以下 = 見た 3 組(訓練)・それより大きい = 60 組
SEEN_MAX_NO = 3
#: 60 組の fact の合計(封 §3。便 XZ0 の記録から)
SUM60_WANT = 61100
#: 番号つきのメンバー(封 §2-1)
MEMBER_RE = re.compile(r"^(No|Row)([0-9]+)([A-Za-z]*Member)$")
DIGIT_RE = re.compile(r"[0-9]")
TAG_RE = re.compile(r"<[^>]*>")
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。
#: XZ1-1 = 段 OG の W1 の上限 %・XZ1-2 = 段 OG の U の下限 %・XZ1-3 = (段 O の W1 が段 HT より少ない数の下限, 新しく W1 になった数の上限)・XZ1-4 = 段 O の U が段 HT より多い数の下限・
#: XZ1-5 = (段 G が止めた段 HT の U の下限 %, 上限 %)・XZ1-6 = 段 HT の W1 のうち段 G が止めた割合の下限 %・XZ1-7 = (番号だけの違いの下限 %, 上限 %)・XZ1-8 = 段 OG の W1 が 0 の組の下限
BOUNDS = od([("XZ1-1", (1.0,)), ("XZ1-2", (72.0,)), ("XZ1-3", (300, 50)), ("XZ1-4", (400,)), ("XZ1-5", (1.0, 8.0)), ("XZ1-6", (50,)), ("XZ1-7", (10, 45)), ("XZ1-8", (20,))])
#: 封 §4 の「先に自分の欠陥を疑う場合」の残り 3 つの境(止めない。記録に旗の欄として書く)
FLAG_S_OVER = 30
LIMITS = [
    u"規則と守りは 3 組を見て作った。60 組の数が 3 組より悪ければ、それが本当の数。60 組も同じ 63 組の引きの中で、無作為ではない(業種はほぼ一般商工業・有報だけ・年は 1 年の差だけ)。",
    u"番号つきのメンバーの形は No・Row で始まる 2 通りだけ。ほかの付け方の番号は拾わない。",
    u"段 O の行の番号は「今年の表の行の順が、今年の正しい番号の順」という仮定に立つ。仮定が破れる表では W1 を新しく作る。",
    u"表の頭の印は、最初に fact を持つ行より前の行の字だけ。頭の字が同じまま列がずれた表・頭の行に fact が在る表は止められない。数字を除くので、年・期の数字だけが変わった頭は同じと見る。",
    u"便 XZ0 の限界はそのまま(fact の置き場は答えから取っている・どちらの年も専用の道具が組んだ後の字・文脈は名で比べ定義は見ない・sign・format・nil・値・数でない fact は測らない・前の年の XBRL が在る会社だけ)。",
    u"「XBRL を作れる」「EDINET の検査に通る」「専用の道具が要らない」「AI が書ける」「黙って違う fact は無い」は、この便からは言えない。"]


# ======================================================================================================
# 形・行の番号・表の頭の印(封 §2-1・§2-3・§2-4)
def shape_of(ctx):
    u"""contextRef の字 → 形の字か None(封 §2-1)。``_`` で切り、2 つ目以降の部品のうち番号つきのメンバーがちょうど 1 つのとき、その数字の並びを ``#`` に置き換えてつなぎ直す。"""
    if ctx is None:
        return None
    parts = ctx.split("_")
    hits = [i for i, p in enumerate(parts) if i >= 1 and MEMBER_RE.match(p)]
    if len(hits) != 1:
        return None
    m = MEMBER_RE.match(parts[hits[0]])
    parts[hits[0]] = m.group(1) + "#" + m.group(3)
    return "_".join(parts)


def with_number(shape, k):
    u"""形の字の ``#`` を k の字に置き換える(段 O の候補)。"""
    return shape.replace("#", str(k))


def head_mark(row_texts):
    u"""表の頭の行の字(rowtext)の並び → 表の頭の印(タグを除き・norm_label・数字 0-9 を除いたものを ``|`` でつなぐ)。"""
    return u"|".join(DIGIT_RE.sub(u"", norm_label(TAG_RE.sub(u"", t))) for t in row_texts)


def table_rows(texts):
    u"""[(file 名, 字)] → [(h, th, T, facts, 表の識別 (file の位置, 表の通し番号), 表の頭の印)](file 名の昇順)。
    ``read_rows`` の行は engine の ``_TR_RE`` の全部と 1 対 1(違えば止まる)。表の通し番号は ``read_rows`` と同じ数え方(行の始まりより前の ``<table`` の開きタグの数)。"""
    out = []
    for fi, (_n, text) in enumerate(sorted(texts, key=lambda q: q[0])):
        rows, _o = Z.read_rows(text)
        matches = list(Z.I._TR_RE.finditer(text))
        if len(rows) != len(matches):
            raise Stop(u"**行の並びが engine の _TR_RE の全部と 1 対 1 でない。止める**")
        starts = [m.start() for m in Z.TABLE_RE.finditer(text)]
        sers = [(fi, bisect.bisect_left(starts, m.start())) for m in matches]
        head_rows, closed = {}, set()
        for m, ser in zip(matches, sers):
            if Z.FACT_RE.search(m.group(0)):
                closed.add(ser)
            elif ser not in closed:
                head_rows.setdefault(ser, []).append(m.group(0))
        marks = dict((ser, head_mark(r)) for ser, r in head_rows.items())
        for (h, th, T, facts), ser in zip(rows, sers):
            out.append((h, th, T, facts, ser, marks.get(ser, u"")))
    return out


def build_col(prior_rows):
    u"""前の年の側 → (表 HT の頭の印の集まり SIG: (h, th, T, td) → {印}・表 COL: (h, th, td) → {(name, 形, unitRef)}・COL の頭の印の集まり SIGC: (h, th, td) → {印})。T が空の行は入れない。"""
    sig, col, sigc = {}, {}, {}
    for h, th, T, facts, _ser, mark in prior_rows:
        if not T:
            continue
        for td, a in facts:
            b = Z.bundle3(a)
            sig.setdefault((h, th, T, td), set()).add(mark)
            sh = shape_of(b[1])
            if sh is not None:
                col.setdefault((h, th, td), set()).add((b[0], sh, b[2]))
                sigc.setdefault((h, th, td), set()).add(mark)
    return sig, col, sigc


def uses_number_col(cands_ht, key_col, col):
    u"""番号の列を使う fact(封 §2-3): 表 HT の候補が空、または候補の中に形の在る文脈が在り、かつ表 COL に (h, th, td) が在る。"""
    if key_col not in col:
        return False
    return (not cands_ht) or any(shape_of(b[1]) is not None for b in cands_ht)


def diff_key(t, c):
    u"""今年の束 3(t)と候補 1 つ(c)で違う属性の名の並び(``+`` でつなぐ)。"""
    return "+".join(ATTRS3[i] for i in range(3) if t[i] != c[i])


DIFF_KEYS = ("name", "contextRef", "unitRef", "name+contextRef", "name+unitRef", "contextRef+unitRef", "name+contextRef+unitRef")
DIFF_LABELS = od((k, u"違う属性 " + k) for k in DIFF_KEYS)


def number_only(t, c):
    u"""番号だけの違い(封 §2-7): contextRef が違い・name と unitRef は同じ・両方に形が在り形が同じ。"""
    if t[1] == c[1] or t[0] != c[0] or t[2] != c[2]:
        return False
    st, sc = shape_of(t[1]), shape_of(c[1])
    return st is not None and st == sc


def new_acc():
    mat = od((hc, od((oc, 0) for oc in CLASSES)) for hc in CLASSES)
    return od([("facts", 0), ("stages", od([(s, od((c, 0) for c in CLASSES + ((STOP_CLASS,) if s in ("G", "OG") else ()))) for s in STAGES4])),
               ("move", mat), ("stopped_g", od((c, 0) for c in CLASSES)), ("stopped_og", od((c, 0) for c in CLASSES)),
               ("numcol", 0), ("w1_diff", od((k, 0) for k in DIFF_KEYS)), ("w1_number_only", 0)])


def merge(into, other):
    u"""同じ形の入れ子の数の辞書を足す。"""
    for k, v in other.items():
        if isinstance(v, dict):
            merge(into[k], v)
        else:
            into[k] += v


def note_secret(secret, T, mark, h):
    u"""記録に書かない字(行の字・表の頭の印の各行・見出しの字)を secret に入れる。"""
    secret[0].add(T)
    for part in mark.split(u"|"):
        if part:
            secret[0].add(part)
    if h:
        secret[4].add(h)


def count_pair(cur_texts, prior_texts, secret=None):
    u"""組 1 つ(今年の側・前の年の側の [(file 名, 字)])を数える(封 §2)。今年の fact の属性は類分けにだけ使い、候補の作りには渡さない。"""
    cur = table_rows(cur_texts)
    prv = table_rows(prior_texts)
    ht3 = Z.build_tables([r[:4] for r in prv])["HT3"]
    sig, col, sigc = build_col(prv)
    acc = new_acc()
    st = acc["stages"]
    row_no = {}                                                 # 表の識別 → 番号の列を使う fact を持つ行のここまでの数
    for h, th, T, facts, ser, mark in cur:
        plan = []
        numrow = False
        for td, a in facts:
            if not T:
                plan.append((td, a, None, None))
                continue
            cands = Z.stage_ht(ht3, h, th, T, td)
            use = uses_number_col(cands, (h, th, td), col)
            plan.append((td, a, cands, use))
            numrow = numrow or use
        if numrow:
            row_no[ser] = row_no.get(ser, 0) + 1
        k = row_no.get(ser)
        for td, a, cands, use in plan:
            acc["facts"] += 1
            if secret is not None:
                for v in (a.get("name") or u"").split(":")[-1:] + [a.get("contextRef") or u"", a.get("unitRef") or u"", shape_of(a.get("contextRef")) or u""]:
                    secret[1].add(v)
            if cands is None:
                for s in STAGES4:
                    st[s]["X"] += 1
                acc["move"]["X"]["X"] += 1
                continue
            t = Z.bundle3(a)
            x = Z.classify6(t, cands)
            if use:
                acc["numcol"] += 1
                o_cands = set((nm, with_number(shape, k), u) for nm, shape, u in col[(h, th, td)])
                y = Z.classify6(t, o_cands)
                ok_og = mark in sigc.get((h, th, td), ())
            else:
                y = x
                ok_og = mark in sig.get((h, th, T, td), ())
            ok_g = mark in sig.get((h, th, T, td), ())
            st["HT"][x] += 1
            st["O"][y] += 1
            acc["move"][x][y] += 1
            g = x if (x in ("N", "X") or ok_g) else STOP_CLASS
            og = y if (y in ("N", "X") or ok_og) else STOP_CLASS
            st["G"][g] += 1
            st["OG"][og] += 1
            if g == STOP_CLASS:
                acc["stopped_g"][x] += 1
            if og == STOP_CLASS:
                acc["stopped_og"][y] += 1
            if x == "W1":
                c = next(iter(cands))
                acc["w1_diff"][diff_key(t, c)] += 1
                if number_only(t, c):
                    acc["w1_number_only"] += 1
        if secret is not None:
            note_secret(secret, T, mark, h)
    for h, th, T, facts, _ser, mark in prv:
        if secret is not None:
            note_secret(secret, T, mark, h)
            for _td, a in facts:
                for v in [(a.get("name") or u"").split(":")[-1], a.get("contextRef") or u"", a.get("unitRef") or u"", shape_of(a.get("contextRef")) or u""]:
                    secret[1].add(v)
    return acc


def totals(accs):
    tot = new_acc()
    for a in accs:
        merge(tot, a)
    return tot


# ======================================================================================================
# 記録の形
def acc_out(acc):
    u"""数の辞書 → 記録の形(欄の名を日本語に)。"""
    return od([
        (u"行の中の数の fact の数", acc["facts"]),
        (u"段ごとの類別", od((s, od(acc["stages"][s])) for s in STAGES4)),
        (u"段 HT の類 → 段 O の類(行が段 HT の類・列が段 O の類)", od((hc, od(acc["move"][hc])) for hc in CLASSES)),
        (u"段 G が止めた fact の段 HT の類別", od(acc["stopped_g"])),
        (u"段 OG が止めた fact の段 O の類別", od(acc["stopped_og"])),
        (u"番号の列を使った fact の数", acc["numcol"]),
        (u"段 HT の W1 の違う属性の組ごとの数", od((DIFF_LABELS[k], acc["w1_diff"][k]) for k in DIFF_KEYS)),
        (u"段 HT の W1 のうち番号だけの違いの数", acc["w1_number_only"])])


def rate_of(n, d):
    return Z.rate_of(n, d)


def judgment_numbers(t):
    u"""60 組の合計(``t`` = ``new_acc`` の形)から予測 XZ1-1〜XZ1-8 の判定に要る数(当たり・外れは書かない。XZ1-8 は呼ぶ側が足す)。"""
    D = t["facts"]
    S = t["stages"]
    ht, o, g, og = S["HT"], S["O"], S["G"], S["OG"]
    new_w1 = sum(t["move"][hc]["W1"] for hc in CLASSES if hc not in ("W1", "W2"))
    pass_og = og["U"] + og["W1"]
    stopped_og = og["S"]
    return od([
        (u"XZ1-1 段 OG の類 W1 / 行の中の数の fact", rate_of(og["W1"], D)),
        (u"XZ1-1 段 OG の類 W1 / 通した(U + W1)", rate_of(og["W1"], pass_og)),
        (u"XZ1-2 段 OG の類 U / 行の中の数の fact", rate_of(og["U"], D)),
        (u"XZ1-3 段 O の W1 と段 HT の W1", od([
            (u"段 HT の W1", ht["W1"]), (u"段 O の W1", o["W1"]), (u"段 HT の W1 から段 O の W1 を引いた数", ht["W1"] - o["W1"]),
            (u"段 HT で W1 でも W2 でもなかった fact が段 O で W1 になった数", new_w1)])),
        (u"XZ1-4 段 O の U と段 HT の U", od([
            (u"段 HT の U", ht["U"]), (u"段 O の U", o["U"]), (u"段 O の U から段 HT の U を引いた数", o["U"] - ht["U"])])),
        (u"XZ1-5 段 G が止めた段 HT の U / 行の中の数の fact", rate_of(t["stopped_g"]["U"], D)),
        (u"XZ1-6 段 G が止めた段 HT の W1 / 段 HT の W1", rate_of(t["stopped_g"]["W1"], ht["W1"])),
        (u"XZ1-7 段 HT の W1 のうち番号だけの違い / 段 HT の W1", rate_of(t["w1_number_only"], ht["W1"])),
        (u"読み方の 4 区分(段 OG)", od([
            (u"通した(U + W1)", pass_og), (u"止めた(S)", stopped_og), (u"候補が複数(A + W2)", og["A"] + og["W2"]), (u"候補なし(N + X)", og["N"] + og["X"]),
            (u"止めたうち正しかった(段 O の類 U)", t["stopped_og"]["U"]),
            (u"止めたうち正しかった割合(%)", pct1(t["stopped_og"]["U"], stopped_og))]))])


def load_draft(root=ROOT, path=None):
    p = path or os.path.join(root, DRAFT_RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**便 XZ0 の記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        return json.loads(fh.read(), object_pairs_hook=collections.OrderedDict)


def check_against_draft(nos, accs, draft):
    u"""段 HT の組ごとの類の数が便 XZ0 の記録の同じ番号の「束 3」「HT」と 1 つでも違えば止まる(封 §4)。"""
    by_no = dict((d[u"番号"], d) for d in draft[u"書類"])
    for n, acc in zip(nos, accs):
        if n not in by_no:
            raise Stop(u"**便 XZ0 の記録に同じ番号が無い。止める**")
        d = by_no[n]
        want = dict(d[u"束と段ごとの類別"][Z.RECORD_LABELS["b3"]]["HT"])
        got = dict(acc["stages"]["HT"])
        if want != got or d[u"行の中の数の fact の数"] != acc["facts"]:
            raise Stop(u"**段 HT の類の数が便 XZ0 の記録と違う。止める**")


def build_record(docs_dir=None, prior_dir=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, draft="auto", want_sum60=SUM60_WANT):
    u"""置き場 → (記録, 漏れの検査に使う材料)。書かない。``draft`` は便 XZ0 の記録(既定 = 本物を読む・None = 照らさない)。``want_sum60`` が None なら 60 組の合計を照らさない(試験用)。"""
    if draft == "auto":
        draft = load_draft()
    docs, pairs, excluded = Y.make_pairs(docs_dir or DOCS_DIR, prior_dir or PRIOR_DIR, want_docs, want_pairs)
    fp = VD.engine_fingerprint()
    secret = (set(), set(), [d[0] for d in docs] + [p[3] for p in pairs], set(p[5] for p in pairs), set(), set())
    for _stem, _p, xs in docs:
        for x in xs:
            secret[3].update(re.findall(r"E\d{5}", x))
    nos, accs = [], []
    for n, stem, p, pstem, pp, code in pairs:
        with zipfile.ZipFile(p) as z:
            cur = N.doc_texts(z)
        with zipfile.ZipFile(pp) as z:
            prv = N.doc_texts(z)
        nos.append(n)
        accs.append(count_pair(cur, prv, secret))
    if draft is not None:
        check_against_draft(nos, accs, draft)
    seen = [a for n, a in zip(nos, accs) if n <= SEEN_MAX_NO]
    rest = [a for n, a in zip(nos, accs) if n > SEEN_MAX_NO]
    t60, t3, t63 = totals(rest), totals(seen), totals(accs)
    if want_sum60 is not None and t60["facts"] != want_sum60:
        raise Stop(u"**60 組の fact の合計が %d でない(%d)。止める**" % (want_sum60, t60["facts"]))
    rows_out = [od([(u"番号", n)] + list(acc_out(a).items())) for n, a in zip(nos, accs)]
    og_w1_zero = sum(1 for a in rest if a["stages"]["OG"]["W1"] == 0)
    D60 = t60["facts"]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XZ1(前の年の下書きが黙って違う属性を付ける fact を、行の順で番号を振り直す規則と表の頭の字の守りで直す・止める)(0 USD・engine は 0 行)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"engine の指紋"] = od((k, fp[k]) for k in ("adapter_xbrl_py_sha256", "adapter_xbrl_py_files", "core_py_sha256", "core_py_files"))
    rec[u"材料"] = od([
        (u"今年の側の書類の本数", len(docs)),
        (u"今年の側の書類の file 名の並びの sha256", W.order_sha256([d[0] for d in docs])),
        (u"組の数", len(pairs)),
        (u"除いた今年の書類の数", excluded),
        (u"前の年の側の組の相手の file 名の並びの sha256", sha256_bytes(u"\n".join(p[3] for p in pairs).encode("utf-8"))),
        (u"60 組の組の数(番号 %d より大きい組)" % SEEN_MAX_NO, len(rest)),
        (u"3 組の組の数(番号 %d 以下の組。訓練)" % SEEN_MAX_NO, len(seen))])
    rec[u"書類"] = rows_out
    rec[u"集計 60 組(番号 %d より大きい。予測の判定はここだけ)" % SEEN_MAX_NO] = acc_out(t60)
    rec[u"集計 3 組(番号 %d 以下。訓練。規則を作るのに見た組)" % SEEN_MAX_NO] = acc_out(t3)
    rec[u"集計 63 組"] = acc_out(t63)
    rec[u"先に自分の欠陥を疑う旗(止めない。当たり外れではない)"] = od([
        (u"段 OG の類 W1 が 60 組の全部で 0(守りが全部を止めていないか)",
         od([(u"W1 が 0 の組の数", og_w1_zero), (u"60 組の組の数", len(rest)), (u"旗", len(rest) > 0 and og_w1_zero == len(rest))])),
        (u"段 G の S が 60 組の fact の %d%% を超えた(表の頭の印の取り違えか)" % FLAG_S_OVER,
         od([(u"fact", t60["stages"]["G"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["G"]["S"] > FLAG_S_OVER * D60)])),
        (u"段 OG の S が 60 組の fact の %d%% を超えた(表の頭の印の取り違えか)" % FLAG_S_OVER,
         od([(u"fact", t60["stages"]["OG"]["S"]), (u"分母", D60), (u"旗", 100 * t60["stages"]["OG"]["S"] > FLAG_S_OVER * D60)])),
        (u"番号の列を使った fact が 60 組で 0(形の読み違いか)",
         od([(u"fact", t60["numcol"]), (u"旗", t60["numcol"] == 0)]))])
    j = judgment_numbers(t60)
    j[u"XZ1-8 段 OG の W1 が 0 の組の数 / 60 組の組の数"] = od([(u"W1 が 0 の組", og_w1_zero), (u"60 組の組の数", len(rest))])
    rec[u"予測の判定に要る数(XZ1-1〜XZ1-8。60 組だけ。当たり・外れは結果の文書で)"] = j
    rec[u"限界"] = list(LIMITS)
    return rec, secret


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(便 XG1 の検査 + 日付の形)が無いか。在れば止める。secret = 便 XZ0 の形(表の頭の印の字は行の字の集まりに、形の字は要素・文脈・単位の集まりに入れる)。"""
    N.check_clean(rec, text, secret)
    if Z.DATE_RE.search(W.HEX_RE.sub(u"", text).replace(SEAL_REL, u"")):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def record_text(rec, secret=None):
    text = dumps(rec)
    check_clean(rec, text, secret)
    return text


def write_exclusive(path, data):
    with open(path, "xb") as fh:
        fh.write(data)


def write_record(path, rec, secret=None):
    u"""書く前と書いた後に検査する。既に在れば止める(測り直さない)。"""
    if os.path.exists(path):
        raise Stop(u"**記録が既に在る: %s。止める**" % os.path.basename(path))
    text = record_text(rec, secret)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_exclusive(path, text.encode("utf-8"))
    with io.open(path, encoding="utf-8") as fh:
        back = fh.read()
    try:
        check_clean(rec, back, secret)
    except SystemExit:
        os.remove(path)
        raise


def run(root=ROOT, docs=None, prior=None, out=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, draft="auto", want_sum60=SUM60_WANT, say=print):
    if draft == "auto":
        draft = load_draft(root)
    rec, secret = build_record(docs, prior, want_docs, want_pairs, draft, want_sum60)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(組 %d)" % (os.path.basename(out), rec[u"材料"][u"組の数"]))
    return rec


def check(root=ROOT, docs=None, prior=None, rec_path=None, want_docs=DOCS_WANT, want_pairs=PAIRS_WANT, draft="auto", want_sum60=SUM60_WANT, say=print):
    u"""置き場から数え直して記録と照らす。通信しない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    if draft == "auto":
        draft = load_draft(root)
    now, secret = build_record(docs, prior, want_docs, want_pairs, draft, want_sum60)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(組 %d)" % now[u"材料"][u"組の数"])
    return now


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="置き場から数え直して記録と照らす。通信しない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="今年の側の置き場(既定は封の字)")
    ap.add_argument("--prior", default=None, help="前の年の側の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    kw = dict(docs=a.docs, prior=a.prior)
    if a.check:
        check(root=a.root, **kw)
    else:
        run(root=a.root, **kw)


if __name__ == "__main__":
    main()
