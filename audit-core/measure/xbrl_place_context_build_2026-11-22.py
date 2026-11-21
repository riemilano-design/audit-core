# -*- coding: utf-8 -*-
u"""封 docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md(XH0 ― 数の置き場を表の cell の字から決め、文脈と単位の定義を紙から作って包みを組むと、道具が読む fact は元と同じになるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** 道具(Arelle。便 XV0 の道具 P)は呼ぶ(repo の外)。engine(``core/``・``adapters/``)は読まない・変えない。
書類の選び方・表の読み方・文脈の読み方・線の選び方・紙・属性を作る命令・包みの落とし方と組み方・道具の掛け方・比べ方は前の便(XA0・XA1・XB0・XP0・XS0)の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_place_context_build_2026-11-22.py --tool-p <venv の場所>           # 道具を確かめて 67 本を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_place_context_build_2026-11-22.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_place_context_build_2026-11-22.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ。記録は書かない
    python3 measure/xbrl_place_context_build_2026-11-22.py paper <zip> <紙の folder>        # 紙(便 XS0)と紙 2 を作る命令(答えを読む。元の包みを読む)
    python3 -I measure/xbrl_place_context_build_2026-11-22.py place <紙の folder> <出す folder>     # 置き場を作る命令(答えを読まない。別の process)
    python3 -I measure/xbrl_place_context_build_2026-11-22.py context <置いた folder> <出す folder>  # 文脈と単位を作る命令(答えを読まない。別の process)
    (属性を作る命令は便 XS0 の ``attrs``。組む命令は便 XP0 の ``build``。どちらも別の process で ``python3 -I``)

紙の folder の中身: 便 XP0 の原稿の folder(目次・素の本文・タクソノミの表。本文の表は表 F の ``nonFraction`` の行が 1 つも無く、表 H の ``resources`` の文脈と単位が無い)・便 XS0 の紙 ``sheet.json``・紙 2 ``paper2.json``。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 持ち込みの表 F は ``nonFraction`` でない行だけ。その行の ``parent`` は持ち込みの行だけの中の番号(持ち込みの行の親は持ち込みの行)。表 H の ``before`` は「持ち込みの行の中で頭の部より前の行の数」。
  組むときは数の fact の行を ``start`` の昇順に挟み、``before`` を「持ち込みの行で前に在るもの + ``start`` が頭の部の位置より前の数の fact の行」に直す。
- 行の並び: ``start`` の昇順。``start`` が同じなら、数の fact を囲む持ち込みの行(自己閉じでなく、``end`` が数の fact の ``end`` 以上)の最後の行までを先に出し、そうでなければ数の fact が先。
  数の fact の ``parent`` は、先に出した持ち込みの行のうち、自己閉じでなく ``start`` が数の fact の ``start`` 以下・``end`` が数の fact の ``end`` 以上の、最も後ろの行。無ければ -1。
- 数の並びは、タグ(``<`` から ``>``)と文字参照(``&`` と英数と ``#`` と ``;``)を別の字に置き換えてから、``NUM_CHARS`` が続く並びを取る。数字は半角と全角の 0〜9。``※`` の判定はタグを飛ばして前の 1 字。
- 空の fact を置く字の位置は、タグと文字参照の外の最初の横棒の字。その手前が ``span`` の開きタグなら、その開きタグの前(重なれば繰り返す)。
- 紙 2: 空の fact の形は ``nil_form``(``self`` か ``pair``)。1 つずつ書く fact は ``hand``(file の番号・start・end・自己閉じか)。例外の cell は ``exceptions``(file の番号・表の番号・行・列・その cell の 1 つずつ書く fact でない fact の
  (start, end, 自己閉じか)の並び。fact が無ければ空)。1 つずつ書く fact の在る cell の中の、1 つずつ書く fact でない fact も、その cell を例外の cell として書く(規則を当てない cell なので)。
- 例外の cell の分け方: 決めの在る cell(1 つずつ書く fact の在る cell を除く)で、規則の答えの並び((start, end, 自己閉じか)の並び)が元の 1 つずつ書く fact でない fact の並びと違う cell。
- 期の表は ``periods``(期の名 → 期の行([タグ, 字] の並び)。定義の ``id`` から分けた期の名。出てきた順)。member の表は ``members``([member の字, 軸] の並び。出てきた順。分けられた定義の member だけ)。
  単位の表は ``units``(単位の行そのまま。出てきた順)。識別子と scheme は最初の定義のもの。``id`` を分けられない定義は表に載せない。
- 期の表の引き: (期間の種類, 終わりの日(前後の空白を落とす))が同じ期の名がちょうど 1 つ。member の字: 接頭辞が ``_cor`` で終わるなら local name・そうでなければ接頭辞 + local name(``:`` が無ければ全体)。
- 混ぜ物(期): 数の fact が 2 つ以上指す期の名のうち、日付を持つ(時点か期間)最初の 1 つ(期の表の並び)。引きは元の表のままにし、出す定義の日付だけを ``1900-01-01``(時点ならその日・期間なら終わりの日)にする
  (期の表の日付を替えると(ア)の ``id`` が引けず断るため)。
- 混ぜ物(置き場): 紙 2 の ``nil_form`` を逆にして置き場を作り直す。変わる行は、規則が置いた空の fact(1 つずつ書く fact でなく例外の cell にも無い)の自己閉じの印だけ。
- 紙の欄の数: 便 XS0 の紙の欄の数(紙の file を読み戻して数える) + 紙 2 の欄(``paper2.json`` を読み戻して数える)。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import itertools
import json
import os
import re
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_PATH = os.path.abspath(__file__)

SHEET_NAME = "_xh0_sheet_build_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


S = _load_sibling(SHEET_NAME, "xbrl_sheet_build_2026-11-22.py")             # 便 XS0 の script
A1 = S.A1                                                                    # 便 XA1 の script
X = S.X                                                                      # 便 XA0 の script
P = S.P                                                                      # 便 XP0 の script
B = S.B                                                                      # 便 XB0 の script
T = S.T                                                                      # 便 XT0 の script
W = S.W                                                                      # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_PLACE_CONTEXT_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT = "97eff9a2"
SCRIPT_REL = "measure/xbrl_place_context_build_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/place_context_build_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT
DEV_COUNT = 5

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
TOOL_VERSION = S.TOOL_VERSION
SHA_P = S.SHA_P
YEAR = S.YEAR
TIMEOUT_SEC = S.TIMEOUT_SEC
NIL_ATTR = S.NIL_ATTR
MIX_DATE = "1900-01-01"
CNC_AXIS = "ConsolidatedOrNonConsolidatedAxis"
COR_SUFFIX = "_cor"
CELLS_NIL_FORM = 1                     # 空の fact の形
CELLS_PER_HAND_PLACE = 2               # 1 つずつ書く fact の始まりと終わり
CELLS_PER_EXC_CELL = 1                 # 例外の cell
CELLS_PER_EXC_FACT = 2                 # 例外の cell の中の fact の始まりと終わり
CELLS_IDENT = 1
CELLS_SCHEME = 1
CELLS_PER_MEMBER = 2                   # member と軸
CELLS_PER_UNIT = 2                     # 単位の id と定義
STAGES = (u"紙を作る", u"置き場を作る", u"文脈と単位を作る", u"属性を作る", u"組む")
PAPER2_FILE = "paper2.json"
EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = S.EXIT_USAGE, S.EXIT_DECLINE, S.EXIT_ERROR
DECLINE_PREFIX = S.DECLINE_PREFIX
SUSPECT_DECLINED = 10
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) か None。XH0-8 は「作れた数に等しい」
BOUNDS = collections.OrderedDict([
    ("XH0-1", (97, None)), ("XH0-2", (None, 3)), ("XH0-3", (55, None)), ("XH0-4", (None, 5)), ("XH0-5", (55, None)), ("XH0-6", (55, None)), ("XH0-7", (None, 5)),
    ("XH0-8", (u"作れた数", None)), ("XH0-9", (40, 44)), ("XH0-10", (None, 0))])
BOUNDS_UPPER_EXCLUSIVE = ("XH0-9",)
RULES = [
    u"対象は ix:nonFraction の全部。書類・行と列の番号・符号の規則・書式の類・断りの掛け方・紙・1 つずつ書く fact は便 XS0 のとおり(前の便の script の関数を呼ぶ)",
    u"命令は 3 つ足す: 紙 2 を作る命令(答えを読む)・置き場を作る命令(答えを読まない。python3 -I の別の process)・文脈と単位を作る命令(答えを読まない。python3 -I の別の process)",
    u"置き場の規則: cell の中身のタグと文字参照を数の字として読まない・数の並び = NUM_CHARS が続く最も長い並びで数字を 1 つ以上含み、すぐ前(タグは飛ばす)が ※ でないもの",
    u"cell の中に表が在れば fact を付けない・数の並びがちょうど 1 つならその並びに中身の在る fact・数の並びが 0 で字が全部横棒なら最初の横棒の前に空の fact(すぐ前が span の開きタグならその前)・それ以外は付けない",
    u"1 つずつ書く fact の在る cell と例外の cell は紙 2 のとおりにし、規則を当てない。例外の cell は規則の答えが元と違う cell",
    u"文脈の id = 期の名 + member ごとに _ + member の字(連結・個別の軸の member が先)。id を期の表の期の名と member の表の member の字に分け、分け方がちょうど 1 通りでなければ断る。単位は単位の表のとおり",
    u"表 F の数の fact の parent は囲む最も内側の持ち込みの行。比べ方 1 は置き場・比べ方 2 は定義(id で引く。member の並びと定義の並びは見ない)・比べ方 3 は道具",
    u"混ぜ物: 期の表の日付を封の字の日付に変えて文脈を作り直す・紙 2 の空の fact の形を逆にして置き場を作り直す",
    u"紙の欄の数 = 便 XS0 の紙の欄の数 + 紙 2 の欄の数。比 = 紙の欄の数 ÷ (fact の数 × 7)。持ち込みは数えない",
]
LIMITS = [
    u"紙も紙 2 も答え(元の書類)から作っている。例外の cell は元と比べて決めている。「人が紙を書けば XBRL が作れる」とは読まない。人が書く紙が正しいかは測っていない。",
    u"「置き場が同じ」は例外の cell を元と比べて決めるので作りから当たる。情報は例外の cell の数の側に在る。",
    u"持ち込み(素の本文・文の fact と脚注の行・見えない fact・参照・提出者別タクソノミの表)はこの便でも作っていない。とくに、文の fact(どの文にどの要素を付けるか)は元から写している。",
    u"置き場の規則は開発の 5 本を見て作った。62 本で当たっても、未使用の書類で同じ率になるとは言えない。",
    u"置き場は字の番号(start・end)で比べている。1 つずつ書く fact と例外の cell の置き場は紙 2 に字の番号で書く(人が書く形ではない)。",
    u"文脈の定義は中身で比べ、member の並びと定義の並びは見ていない。包みは元と byte では同じにならない見込み。",
    u"member の表・期の表・単位の表は元の定義から写している(標準の表や提出者別タクソノミの表から引いていない)。",
    u"混ぜ物は 1 本につき 2 つだけ。ほかの決めを変えた確かめは封の門の作り物だけ。",
    u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない(便 XV0 の限界のまま)。",
    u"便 XA0・便 XA1・便 XB0・便 XT0・便 XP0・便 XS0 の限界の全部(答えから作った決め・rowspan を見ない・67 本は無作為でない・有報だけ・道具 P は本家の版でない・script は前の便の script を経て engine の module を間接に読み込む)。",
    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
Refuse = X.Refuse
od = collections.OrderedDict
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
ATTR_LABELS = S.ATTR_LABELS
HAND_REASONS = S.HAND_REASONS

R_P2 = u"紙 2 が読めない形"
R_FOLDER = u"紙の folder が読めない形"
R_PERIOD = u"期の名が 1 つに決まらない"
R_SPLIT = u"id が期の名と member の字に 1 通りに分けられない"
R_NOHDR = u"表 H が無い"
R_SHEET_ERR = u"紙を作る途中の例外"
R_PLACE_ERR = u"置き場を作る途中の例外"
R_CONTEXT_ERR = u"文脈と単位を作る途中の例外"
R_BUILD_OUT = S.R_BUILD_OUT

CELL_KEYS = tuple(S.CELL_KEYS) + (u"空の fact の形", u"1 つずつ書く fact の始まりと終わり", u"例外の cell", u"例外の cell の中の fact の始まりと終わり", u"識別子と scheme", u"期の表", u"member の表", u"単位の表")

MASK_RE = re.compile(r"<[^>]*>|&[#A-Za-z0-9]+;")
SPAN_OPEN_END_RE = re.compile(r"<span\b[^>]*>\Z", re.I)
DIGITS = u"0123456789０１２３４５６７８９"
STAR = u"※"
TAG_MASK, REF_MASK = u"\x00", u"\x01"


# ======================================================================================================
# 置き場の規則(封 §1。置き場を作る命令と、紙 2 を作る側の両方が同じ関数を呼ぶ)
def cells_of(plain):
    u"""素の本文 → [(表の番号, 行の番号, 列の番号, 中身の始まり, 中身の終わり)]。cell の閉じタグごと(便 XA0 の積み方)。"""
    toks = X.table_tokens(plain)
    stack = []
    counter = [0]
    out = []
    for tok in toks:
        if tok[2] and stack and stack[-1][0] in ("td", "th") and tok[3] == stack[-1][0]:
            k = max(i for i in range(len(stack)) if stack[i][0] == "table")
            out.append((stack[k][1], stack[k + 1][1], stack[-1][1], stack[-1][2], tok[0]))
        X.step_token(stack, counter, tok)
    if stack:
        raise Refuse(X.R_TABLE)
    return out


def masked(raw):
    u"""cell の中身 → 文字の並び(タグは ``\\x00``・文字参照は ``\\x01`` に替える)。"""
    m = list(raw)
    for mm in MASK_RE.finditer(raw):
        c = TAG_MASK if raw[mm.start()] == u"<" else REF_MASK
        for i in range(mm.start(), mm.end()):
            m[i] = c
    return m


def number_runs(m, raw):
    u"""数の並び [(始まり, 終わり)]。``NUM_CHARS`` が続く最も長い並びで数字を 1 つ以上含み、すぐ前(タグは飛ばす)が ``※`` でないもの。"""
    spans = []
    cur = None
    for i, ch in enumerate(m):
        if ch in X.NUM_CHARS:
            cur = [cur[0], i + 1] if cur else [i, i + 1]
        elif cur:
            spans.append(tuple(cur))
            cur = None
    if cur:
        spans.append(tuple(cur))
    out = []
    for s, e in spans:
        if not any(c in DIGITS for c in raw[s:e]):
            continue
        j = s - 1
        while j >= 0 and m[j] == TAG_MASK:
            j -= 1
        if j >= 0 and m[j] == STAR:
            continue
        out.append((s, e))
    return out


def dash_only(m):
    u"""cell の字(タグを除き、文字参照は空白に読み、前後の空白を除く)が空でなく、全部が横棒の字か。"""
    vis = u"".join(u" " if c == REF_MASK else c for c in m if c != TAG_MASK).strip()
    return vis != u"" and all(ch in X.DASH_CHARS for ch in vis)


def nil_position(raw, m):
    u"""空の fact を置く所。最初の横棒の字(タグ・文字参照の外)の前。そのすぐ前が span の開きタグならその開きタグの前(重なれば繰り返す)。"""
    k = [i for i, ch in enumerate(m) if ch in X.DASH_CHARS][0]
    while True:
        q = SPAN_OPEN_END_RE.search(raw[:k])
        if not q:
            return k
        k = q.start()


def predict_cell(raw, nil_self):
    u"""cell の中身 → 規則の答え [(始まり, 終わり, 自己閉じか)](中身の中の位置)。表が在れば・数の並びが 2 つ以上なら・それ以外なら空の並び。"""
    if u"<table" in raw.lower():
        return []
    m = masked(raw)
    runs = number_runs(m, raw)
    if len(runs) == 1:
        return [(runs[0][0], runs[0][1], False)]
    if len(runs) == 0 and dash_only(m):
        k = nil_position(raw, m)
        return [(k, k, bool(nil_self))]
    return []


def decided_cell(ts, r, col):
    u"""cell の決め(紙の表の決め)が在るか: 要素の線の name の決め・終わりの日の決め・member の組の決めの 3 つが全部在る。"""
    if ts is None:
        return False
    e, c = X.line_keys({"row": r, "col": col}, ts["orient"])
    el = ts["elements"].get(str(e))
    endv = ts["ends"].get(str(c if ts["end_src"] == "C" else e))
    memv = ts["members"].get(str(c if ts["member_src"] == "C" else e))
    return el is not None and el[0] is not None and endv is not None and memv is not None


def file_placements(plain, fi, tabs, hand, exc, nil_self):
    u"""1 つの ``.htm``。(置き場の並び [(start, end, 自己閉じか)] を (start, end) の昇順で, 規則が置いた空の fact の (start, end) の集まり)。
    ``hand`` = [(start, end, 自己閉じか)]・``exc`` = {(表, 行, 列): [(start, end, 自己閉じか)]}。1 つずつ書く fact の在る cell と例外の cell は紙 2 のとおりにする。"""
    out = list(hand)
    hs = sorted(set(s for s, _e, _x in hand))
    hand_cells = set()
    if hs:
        for cell in X.place_positions(plain, hs):
            if cell is not None:
                hand_cells.add((cell[0], cell[1], cell[2]))
    rule_empty = set()
    for t, r, col, oe, cs in cells_of(plain):
        key = (t, r, col)
        if key in exc:
            out.extend(exc[key])
            continue
        if key in hand_cells:
            continue
        if not decided_cell(tabs.get((fi, t)), r, col):
            continue
        for s, e, sf in predict_cell(plain[oe:cs], nil_self):
            out.append((oe + s, oe + e, sf))
            if s == e:
                rule_empty.add((oe + s, oe + e))
    out.sort(key=lambda p: (p[0], p[1]))
    return out, rule_empty


def encloses(row, s, e):
    return (not row["self"]) and row["start"] <= s and e <= row["end"]


def merge_rows(carried, numbers):
    u"""持ち込みの行(``parent`` は持ち込みの行の中の番号)と数の fact の置き場 [(start, end, 自己閉じか)](昇順)→ (行の並び, [(``c`` か ``n``, 持ち込みの番号か置き場の番号)])。
    ``start`` の昇順。同じ ``start`` なら、数の fact を囲む行の最後までを先に出す。数の fact の ``parent`` は先に出した行のうち囲む最も後ろの持ち込みの行。"""
    order = []
    pending = []
    ci = 0
    ni = 0
    n_c, n_n = len(carried), len(numbers)
    stack = []
    while ci < n_c or ni < n_n:
        take_c = False
        if ci < n_c and ni < n_n:
            s, e, _x = numbers[ni]
            cs = carried[ci]["start"]
            if cs < s:
                take_c = True
            elif cs == s:
                k = ci
                last = None
                while k < n_c and carried[k]["start"] == s:
                    if encloses(carried[k], s, e):
                        last = k
                    k += 1
                take_c = last is not None
        elif ci < n_c:
            take_c = True
        if take_c:
            order.append((u"c", ci))
            if not carried[ci]["self"]:
                stack.append(ci)
            ci += 1
        else:
            s, e, _x = numbers[ni]
            while stack and not encloses(carried[stack[-1]], s, e):
                stack.pop()
            pending.append(stack[-1] if stack else -1)
            order.append((u"n", ni))
            ni += 1
    new_index = {}
    for pos, (k, i) in enumerate(order):
        if k == u"c":
            new_index[i] = pos
    rows = []
    ps = iter(pending)
    for k, i in order:
        if k == u"c":
            row = od((kk, vv) for kk, vv in carried[i].items())
            row["parent"] = new_index[carried[i]["parent"]] if carried[i]["parent"] >= 0 else -1
            rows.append(row)
        else:
            s, e, sf = numbers[i]
            p = next(ps)
            rows.append(od([("kind", "nonFraction"), ("self", bool(sf)), ("start", s), ("end", e), ("parent", new_index[p] if p >= 0 else -1), ("attrs", {})]))
    return rows, order


def header_before(H, order, numbers):
    u"""頭の部の ``before``(持ち込みの行の中で前に在る行の数)→ 組んだ表 F の中で前に在る行の数。"""
    cb = H["before"]
    pos = H["pos"]
    return sum(1 for k, i in order if (k == u"c" and i < cb) or (k == u"n" and numbers[i][0] < pos))


# ======================================================================================================
# 文脈と単位の規則(封 §1)
def token_of(member):
    u"""member の字: 接頭辞が ``_cor`` で終わるなら local name・そうでなければ接頭辞 + local name。``:`` が無ければ全体。"""
    if u":" not in member:
        return member
    prefix, local = member.split(u":", 1)
    return local if prefix.endswith(COR_SUFFIX) else prefix + local


def is_cnc(dim):
    return dim.split(u":")[-1] == CNC_AXIS


def id_of_triple(key, pmap):
    u"""(期間の種類, 終わりの日, member の組) → 文脈の id。期の名がちょうど 1 つでなければ ``Refuse``。連結・個別の軸の member が先、残りは組の並びの順。"""
    kind, end, mem = key
    names = pmap.get((kind, end), [])
    if len(names) != 1:
        raise Refuse(R_PERIOD)
    first = [x for x in mem if is_cnc(x[0])]
    rest = [x for x in mem if not is_cnc(x[0])]
    return names[0] + u"".join(u"_" + token_of(m) for _d, m in first + rest)


def split_id(cid, names, by_token):
    u"""``id`` → 分け方の並び [(期の名, [member の字の並び])](多くても 2 つで切る)。期の名 + (``_`` + member の字)の 0 個以上の並び。"""
    out = []

    def walk(rest, name, acc):
        if len(out) >= 2:
            return
        if rest == u"":
            out.append((name, list(acc)))
            return
        for tok in by_token:
            if tok and rest.startswith(u"_" + tok):
                for mem in by_token[tok]:
                    acc.append(mem)
                    walk(rest[1 + len(tok):], name, acc)
                    acc.pop()
    for nm in names:
        if nm and cid.startswith(nm):
            walk(cid[len(nm):], nm, [])
    return out


def period_map(periods):
    u"""期の表 [[期の名, 期の行]] → {(期間の種類, 終わりの日): [期の名]}。便 XS0 の文脈の読み方で。"""
    pm = {}
    for name, per in periods:
        _i, (kind, end, _m) = S.read_context({"id": name, "period": per, "members": []})
        pm.setdefault((kind, end), []).append(name)
    return pm


class _Probe(dict):
    u"""便 XS0 の ``decided_attrs`` が引く (期間の種類, 終わりの日, member の組) を覚え、1 つの仮の id を返す。"""

    def __init__(self):
        dict.__init__(self)
        self.asked = []

    def get(self, key, default=None):
        self.asked.append(key)
        return [u"\x00probe"]


def needed_ids(files, sheet, pm):
    u"""文脈と単位を作る命令が要る id の並び。{id: 集合 {ア, イ, ウ}}(出てきた順)と、数の fact ごとの id の並び。(ア) = 1 つずつ書く fact でない数の fact・(イ) = 1 つずつ書く fact の contextRef・(ウ) = 持ち込み。"""
    tabs = S.table_lookup(sheet)
    rows = dict(((r["file"], r["index"]), r) for r in sheet["facts"])
    ids = od()
    per_fact = []

    def add(cid, tag):
        if cid is not None:
            ids.setdefault(cid, set()).add(tag)
    for fi, (_name, plain, F, H) in enumerate(files):
        idx = [i for i, e in enumerate(F) if e["kind"] == "nonFraction"]
        cells = X.place_positions(plain, [F[i]["start"] for i in idx]) if idx else []
        for i, cell in zip(idx, cells):
            e = F[i]
            row = rows.get((fi, i), {})
            if "values" in row:
                cid = S.values_attrs(row).get("contextRef")
                add(cid, u"イ")
            else:
                if cell is None:
                    raise Refuse(S.R_PAPER)
                t = tabs.get((fi, cell[0]))
                if t is None:
                    raise Refuse(S.R_PAPER)
                f = od([("row", cell[1]), ("col", cell[2]), ("between", X.strip_tags(plain[cell[3]:e["start"]])),
                        ("text", X.strip_tags(plain[e["start"]:e["end"]]).strip())])
                probe = _Probe()
                S.decided_attrs(f, t, sheet, probe, row)
                cid = id_of_triple(probe.asked[-1], pm)
                add(cid, u"ア")
            per_fact.append(cid)
        for e in F:
            if e["kind"] != "nonFraction":
                add(e["attrs"].get("contextRef"), u"ウ")
        if H is not None:
            for h in H["hidden"]:
                add(h["attrs"].get("contextRef"), u"ウ")
    return ids, per_fact


def context_resources(files, sheet, p2, overlay=None):
    u"""表 H の ``resources`` の行の並びと、数えるための情報。断りは ``Refuse``。
    書く並び: 持ち込みの参照の行・文脈(期の表の並び、同じ期の名の中は id の字の順)・単位(単位の表の並び)。``overlay`` = {期の名: 期の行} は出す定義の期だけを替える(混ぜ物)。"""
    hi = [i for i, f in enumerate(files) if f[3] is not None]
    if not hi:
        raise Refuse(R_NOHDR)
    periods = [(n, per) for n, per in p2["periods"]]
    pm = period_map(periods)
    ids, per_fact = needed_ids(files, sheet, pm)
    names = [n for n, _p in periods]
    axis_of = od((m, a) for m, a in p2["members"])
    by_token = od()
    for m in axis_of:
        by_token.setdefault(token_of(m), []).append(m)
    parsed = od()
    for cid in ids:
        sp = split_id(cid, names, by_token)
        if len(sp) != 1:
            raise Refuse(R_SPLIT)
        parsed[cid] = sp[0]
    per_of = od(periods)
    rows = [r for r in files[hi[0]][3]["resources"] if r.get("type") == "ref"]
    ctx_rows = []
    for nm in names:
        for cid in sorted(c for c, (n, _m) in parsed.items() if n == nm):
            mems = parsed[cid][1]
            per = (overlay or {}).get(nm, per_of[nm])
            ctx_rows.append(od([("type", "context"), ("id", cid), ("scheme", p2["scheme"]), ("ident", p2["ident"]), ("period", [list(x) for x in per]),
                                ("members", [[axis_of[m], m] for m in mems]), ("has_scenario", len(mems) >= 1)]))
    unit_rows = [od([("type", "unit"), ("id", u["id"]), ("measures", list(u["measures"])), ("divide", u["divide"])]) for u in p2["units"]]
    info = od([("ids", ids), ("per_fact", per_fact), ("names", od((c, n) for c, (n, _m) in parsed.items())), ("periods", periods), ("hi", hi[0])])
    return rows + ctx_rows + unit_rows, info


# ======================================================================================================
# 答えを読まない 2 つの命令(別の process。folder だけを読む)
def read_paper_folder(folder):
    u"""紙の folder(または置いた folder)→ (目次, 紙, 紙 2, [(名, 素の本文, 表 F, 表 H)])。読めなければ ``Refuse``。"""
    try:
        index = P.jload(P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
        sheet = P.jload(P.read_bytes(os.path.join(folder, S.SHEET_FILE)))
        p2 = P.jload(P.read_bytes(os.path.join(folder, PAPER2_FILE)))
        files = P.load_htm_tables(folder, index)
        for k in ("nil_form", "hand", "exceptions", "scheme", "ident", "periods", "members", "units"):
            if k not in p2:
                raise Refuse(R_P2)
    except Refuse:
        raise
    except Exception:                                      # noqa: BLE001
        raise Refuse(R_FOLDER)
    return index, sheet, p2, files


def place_tables(folder):
    u"""置き場を作る命令の中身。紙の folder だけを読み、(目次, 紙, 紙 2, 数の fact の行を足した [(名, 素の本文, 表 F, 表 H)], 規則が置いた空の fact の (start, end) の集まりの並び) を返す。"""
    index, sheet, p2, files = read_paper_folder(folder)
    tabs = S.table_lookup(sheet)
    nil_self = p2["nil_form"] == "self"
    out = []
    empties = []
    for fi, (name, plain, F, H) in enumerate(files):
        hand = [(s, e, sf) for f, s, e, sf in p2["hand"] if f == fi]
        exc = dict(((t, r, c), [(s, e, sf) for s, e, sf in fs]) for f, t, r, c, fs in p2["exceptions"] if f == fi)
        nums, rule_empty = file_placements(plain, fi, tabs, hand, exc, nil_self)
        rows, order = merge_rows(F, nums)
        H2 = None
        if H is not None:
            H2 = od((k, v) for k, v in H.items())
            H2["before"] = header_before(H, order, nums)
        out.append((name, plain, rows, H2))
        empties.append(rule_empty)
    return index, sheet, p2, out, empties


def copy_folder(folder, out, replace):
    u"""folder の file をそのまま出す folder に写す(``replace`` の名の file だけ bytes を替える)。"""
    os.makedirs(out)
    for fn in sorted(os.listdir(folder)):
        path = os.path.join(folder, fn)
        if os.path.isfile(path):
            P.write_bytes(os.path.join(out, fn), replace[fn] if fn in replace else P.read_bytes(path))


def tables_bytes(index, files):
    return dict((P.safe_local(item["tables"]), P.jdump(od([("F", F), ("H", H)]))) for item, (_n, _p, F, H) in zip(index["htm"], files))


def write_place_folder(folder, out):
    index, _sheet, _p2, files, _e = place_tables(folder)
    copy_folder(folder, out, tables_bytes(index, files))


def context_tables(folder, overlay=None):
    u"""文脈と単位を作る命令の中身。置いた folder だけを読み、(目次, 表 H の ``resources`` を作った [(名, 素の本文, 表 F, 表 H)], 情報)を返す。"""
    index, sheet, p2, files = read_paper_folder(folder)
    resources, info = context_resources(files, sheet, p2, overlay)
    out = []
    for fi, (name, plain, F, H) in enumerate(files):
        if fi == info["hi"]:
            H = od((k, v) for k, v in H.items())
            H["resources"] = resources
        out.append((name, plain, F, H))
    return index, out, info


def write_context_folder(folder, out):
    index, files, _info = context_tables(folder)
    copy_folder(folder, out, tables_bytes(index, files))


def step_main(args, usage, writer):
    u"""置き場を作る命令・文脈と単位を作る命令の入口。引数は folder 2 つだけ(元の包みの path を受け取れない)。終わりの値: 0・64(使い方)・2(断り)・1(例外)。"""
    if len(args) != 2:
        print(usage, file=sys.stderr)
        return EXIT_USAGE
    try:
        writer(args[0], args[1])
    except (Refuse, P.Refuse) as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


def place_main(args):
    return step_main(args, u"使い方: place <紙の folder> <出す folder>", write_place_folder)


def context_main(args):
    return step_main(args, u"使い方: context <置いた folder> <出す folder>", write_context_folder)


def step_command(name, folder, out):
    return [sys.executable, "-I", SCRIPT_PATH, name, folder, out]


def place_command(folder, out):
    return step_command("place", folder, out)


def context_command(folder, out):
    return step_command("context", folder, out)


def exec_step(name, label, folder, out, cwd, proc=None):
    u"""置き場を作る命令・文脈と単位を作る命令を別の process で 1 回。(成功か, 断りの理由, 秒)。"""
    proc = proc or P.run_process
    t0 = time.time()
    rc, err, timed_out = proc(step_command(name, folder, out), cwd, TIMEOUT_SEC)
    secs = time.time() - t0
    if timed_out:
        return False, label + u"命令が時間の上限を超えた", secs
    if rc != 0:
        reason = P.decline_reason(err)
        return False, (reason if reason is not None else label + u"命令が 0 でない終わりの値で終わった"), secs
    return True, u"", secs


# ======================================================================================================
# 紙 2 を作る(答えを読む)
def member_pairs(row):
    return [(d or u"", m) for d, m in row["members"]]


def split_definition(row):
    u"""元の文脈の定義 → 期の名(``id`` から member の字の並びを除いたもの)か ``None``。member の並びは、書いた順・連結・個別の軸が先・並べ替えの全部(3 つまで)の順に試す。"""
    members = member_pairs(row)
    orders = [list(members), [x for x in members if is_cnc(x[0])] + [x for x in members if not is_cnc(x[0])]]
    if 1 < len(members) <= 3:
        orders.extend(list(p) for p in itertools.permutations(members))
    for order in orders:
        suffix = u"".join(u"_" + token_of(m) for _d, m in order)
        if row["id"].endswith(suffix) and len(row["id"]) > len(suffix):
            return row["id"][:len(row["id"]) - len(suffix)]
    return None


def make_paper2(files, ids, hand, sheet):
    u"""元の (名, 素の本文, 表 F, 表 H) の並びと 1 つずつ書く fact の印・紙 → (紙 2, 数える情報)。"""
    tabs = S.table_lookup(sheet)
    hand_set = set(i for i, h in zip(ids, hand) if h)
    empties_self = empties_pair = 0
    for fi, (_n, _p, F, _h) in enumerate(files):
        for i, e in enumerate(F):
            if e["kind"] == "nonFraction" and (fi, i) not in hand_set and e["end"] == e["start"]:
                if e["self"]:
                    empties_self += 1
                else:
                    empties_pair += 1
    nil_self = empties_self >= empties_pair
    hand_rows = []
    exc_rows = []
    st = od((k, 0) for k in (u"決めの在る cell", u"1 つずつ書く fact の在る cell", u"例外 付ける", u"例外 違う", u"1 つずつ書く fact の在る cell の中の fact", u"1 つずつ書く fact でない fact",
                              u"規則が当てた fact", u"決めの在る cell の外の fact"))
    for fi, (_n, plain, F, _h) in enumerate(files):
        idx = [i for i, e in enumerate(F) if e["kind"] == "nonFraction"]
        cells = X.place_positions(plain, [F[i]["start"] for i in idx]) if idx else []
        truth = collections.defaultdict(list)
        hand_cell = set()
        for i, cell in zip(idx, cells):
            e = F[i]
            if (fi, i) in hand_set:
                hand_rows.append([fi, e["start"], e["end"], bool(e["self"])])
                if cell is not None:
                    hand_cell.add((cell[0], cell[1], cell[2]))
            else:
                st[u"1 つずつ書く fact でない fact"] += 1
                truth[(cell[0], cell[1], cell[2]) if cell is not None else None].append((e["start"], e["end"], bool(e["self"])))
        seen = set()
        for t, r, col, oe, cs in cells_of(plain):
            key = (t, r, col)
            seen.add(key)
            ts = decided_cell(tabs.get((fi, t)), r, col)
            tr = sorted(truth.get(key, []))
            if ts:
                st[u"決めの在る cell"] += 1
            if key in hand_cell:
                if ts:
                    st[u"1 つずつ書く fact の在る cell"] += 1
                if tr:
                    st[u"1 つずつ書く fact の在る cell の中の fact"] += len(tr)
                    exc_rows.append([fi, t, r, col, [list(x) for x in tr]])
                continue
            if not ts:
                if tr:
                    st[u"決めの在る cell の外の fact"] += len(tr)
                    exc_rows.append([fi, t, r, col, [list(x) for x in tr]])
                continue
            pred = sorted((oe + s, oe + e, sf) for s, e, sf in predict_cell(plain[oe:cs], nil_self))
            if pred == tr:
                st[u"規則が当てた fact"] += len(tr)
            else:
                st[u"例外 付ける" if not tr else u"例外 違う"] += 1
                exc_rows.append([fi, t, r, col, [list(x) for x in tr]])
        for key, tr in truth.items():
            if key is None or key not in seen:
                st[u"決めの在る cell の外の fact"] += len(tr)
    defs = []
    units = []
    for _n, _p, _F, H in files:
        if H is None:
            continue
        for r in H["resources"]:
            if r.get("type") == "context":
                defs.append(r)
            elif r.get("type") == "unit":
                units.append(od([("id", r["id"]), ("measures", list(r["measures"])), ("divide", r["divide"])]))
    periods = od()
    members = od()
    for r in defs:
        nm = split_definition(r)
        if nm is None:
            continue
        periods.setdefault(nm, [list(x) for x in r["period"]])
        for d, m in member_pairs(r):
            members.setdefault(m, d)
    p2 = od([("nil_form", u"self" if nil_self else u"pair"), ("hand", hand_rows), ("exceptions", exc_rows),
             ("scheme", defs[0]["scheme"] if defs else None), ("ident", defs[0]["ident"] if defs else None),
             ("periods", [[n, per] for n, per in periods.items()]), ("members", [[m, d] for m, d in members.items()]), ("units", units)])
    return p2, st


def paper2_cells(p2):
    u"""紙 2 に実際に書いた値の数(項ごと)。"""
    out = od()
    out[u"空の fact の形"] = CELLS_NIL_FORM
    out[u"1 つずつ書く fact の始まりと終わり"] = CELLS_PER_HAND_PLACE * len(p2["hand"])
    out[u"例外の cell"] = CELLS_PER_EXC_CELL * len(p2["exceptions"])
    out[u"例外の cell の中の fact の始まりと終わり"] = CELLS_PER_EXC_FACT * sum(len(x[4]) for x in p2["exceptions"])
    out[u"識別子と scheme"] = CELLS_IDENT + CELLS_SCHEME
    out[u"期の表"] = sum(1 + sum(1 for _tag, val in per if val != u"") for _n, per in p2["periods"])
    out[u"member の表"] = CELLS_PER_MEMBER * len(p2["members"])
    out[u"単位の表"] = CELLS_PER_UNIT * len(p2["units"])
    return out


def carried_tables(files, p2_unused=None):
    u"""元の (名, 素の本文, 表 F, 表 H) → 持ち込みの (名, 素の本文, 表 F, 表 H)。表 F は ``nonFraction`` でない行だけ(``parent`` は持ち込みの行の中の番号)。
    表 H は ``resources`` から文脈と単位を除き、``before`` を持ち込みの行の中の数に直す。"""
    out = []
    for _n, plain, F, H in files:
        cmap = {}
        rows = []
        for i, e in enumerate(F):
            if e["kind"] == "nonFraction":
                continue
            cmap[i] = len(rows)
            row = od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items())
            row["parent"] = cmap[e["parent"]] if e["parent"] >= 0 else -1
            rows.append(row)
        H2 = None
        if H is not None:
            H2 = od((k, v) for k, v in H.items())
            H2["before"] = sum(1 for i in range(H["before"]) if F[i]["kind"] != "nonFraction")
            H2["resources"] = [r for r in H["resources"] if r.get("type") == "ref"]
        out.append((_n, plain, rows, H2))
    return out


def make_paper_folder(entries, zip_path, folder):
    u"""紙を作る命令の中身(答えを読む)。元の包みから便 XS0 の紙の folder を書き、表を持ち込みだけに替えて紙 2 を足す。(紙, 測りの側の持ち物, 元の表の並び, 紙 2, 数える情報)。
    断りは ``Refuse``。"""
    sheet, info, files, _facts = S.make_sheet_folder(entries, zip_path, folder)
    try:
        ids = S.fact_ids(files)
        p2, st = make_paper2(files, ids, info["hand"], sheet)
        index = P.jload(P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
        for item, (_n, _p, F, H) in zip(index["htm"], carried_tables(files)):
            P.write_bytes(os.path.join(folder, P.safe_local(item["tables"])), P.jdump(od([("F", F), ("H", H)])))
        P.write_bytes(os.path.join(folder, PAPER2_FILE), P.jdump(p2))
    except (Refuse, P.Refuse):
        shutil.rmtree(folder, ignore_errors=True)
        raise
    except Exception:                                      # noqa: BLE001
        shutil.rmtree(folder, ignore_errors=True)
        raise Refuse(u"folder に書けない形")
    return sheet, info, files, p2, st


def paper_main(args):
    u"""紙(便 XS0)と紙 2 を作る命令。引数は zip と folder。"""
    if len(args) != 2:
        print(u"使い方: paper <zip> <紙の folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        make_paper_folder(B.load_package(args[0]), args[0], args[1])
    except (Refuse, P.Refuse) as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


# ======================================================================================================
# 渡す folder に元の行が無いこと・比べ方
def tables_of(folder):
    index = P.jload(P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
    return [P.jload(P.read_bytes(os.path.join(folder, P.safe_local(item["tables"])))) for item in index["htm"]]


def resource_rows(tab):
    return [r for r in (tab["H"]["resources"] if tab["H"] is not None else []) if r.get("type") in ("context", "unit")]


def leak_place_problems(folder):
    u"""置き場を作る命令に渡す folder に在ってはならない行の数: 数の fact の行(``nonFraction``)・表 H の文脈と単位の行。"""
    n = 0
    for tab in tables_of(folder):
        n += sum(1 for e in tab["F"] if e["kind"] == "nonFraction")
        n += len(resource_rows(tab))
    return n


def leak_context_problems(folder):
    u"""文脈と単位を作る命令に渡す folder に在ってはならない行の数: ``attrs`` を持つ数の fact の行・表 H の文脈と単位の行。"""
    n = 0
    for tab in tables_of(folder):
        n += sum(1 for e in tab["F"] if e["kind"] == "nonFraction" and e["attrs"])
        n += len(resource_rows(tab))
    return n


def number_rows(files):
    return [[(e["start"], e["end"], bool(e["self"]), e["parent"]) for e in F if e["kind"] == "nonFraction"] for _n, _p, F, _h in files]


def all_rows(files):
    u"""表 F の全部の行((kind, 自己閉じか, start, end, parent))と、頭の部の位置((before, pos) か ``None``)。"""
    return [([(e["kind"], bool(e["self"]), e["start"], e["end"], e["parent"]) for e in F], None if H is None else (H["before"], H["pos"])) for _n, _p, F, H in files]


def definition_map(files):
    u"""[(名, 素の本文, 表 F, 表 H)] → ({id: (scheme, 識別子, 期, member の組の集まり, has_scenario)}, [id の並び], {id: (member の並び)})。"""
    defs = od()
    mem_order = {}
    for _n, _p, _F, H in files:
        if H is None:
            continue
        for r in H["resources"]:
            if r.get("type") != "context":
                continue
            defs[r["id"]] = (r["scheme"], r["ident"], tuple(tuple(x) for x in r["period"]), frozenset((d or u"", m) for d, m in r["members"]), bool(r["has_scenario"]))
            mem_order[r["id"]] = tuple((d or u"", m) for d, m in r["members"])
    return defs, list(defs), mem_order


def unit_map(files):
    out = od()
    order = []
    for _n, _p, _F, H in files:
        if H is None:
            continue
        for r in H["resources"]:
            if r.get("type") == "unit":
                dv = r["divide"]
                out[r["id"]] = (tuple(r["measures"]), None if dv is None else (tuple(dv["num"]), tuple(dv["den"])))
                order.append(r["id"])
    return out, order


def compare_definitions(orig_files, new_files):
    u"""比べ方 2。dict(元の数・作った数・中身が違う・元にだけ・作った側にだけ・文脈が同じ・単位が同じ・定義の並びまで同じ)。"""
    a, a_order, a_mem = definition_map(orig_files)
    b, b_order, b_mem = definition_map(new_files)
    both = [i for i in a if i in b]
    differ = sum(1 for i in both if a[i] != b[i])
    only_a = sum(1 for i in a if i not in b)
    only_b = sum(1 for i in b if i not in a)
    ua, _ua = unit_map(orig_files)
    ub, _ub = unit_map(new_files)
    return od([(u"元", len(a)), (u"作った", len(b)), (u"中身が違う", differ), (u"元にだけ", only_a), (u"作った側にだけ", only_b),
               (u"文脈が同じ", differ == 0 and only_a == 0 and only_b == 0), (u"単位が同じ", ua == ub),
               (u"並びまで同じ", a_order == b_order and all(a_mem[i] == b_mem[i] for i in a_order) and a == b)])


# ======================================================================================================
# 混ぜ物
def period_change(per):
    u"""期の行 → 日付を 1900-01-01 に替えた行(時点ならその日・期間なら終わりの日)。日付が無ければ ``None``。"""
    tags = [t for t, _v in per]
    if tags == ["xbrli:instant"]:
        return [[per[0][0], MIX_DATE]]
    if tags == ["xbrli:startDate", "xbrli:endDate"]:
        return [list(per[0]), [per[1][0], MIX_DATE]]
    return None


def period_target(info):
    u"""混ぜ物(期)の当て先。数の fact が 2 つ以上指す期の名のうち、日付を持つ最初の 1 つ(期の表の並び)。(期の名, 替えた期の行) か ``None``。"""
    counts = collections.Counter(info["names"][c] for c in info["per_fact"])
    for name, per in info["periods"]:
        if counts[name] >= 2 and period_change(per) is not None:
            return (name, period_change(per))
    return None


def mix_period_effect(folder):
    u"""混ぜ物(期)。(作れたか, 効いたか)。道具は呼ばない。置いた folder から、同じ process の中で文脈を作る関数を 2 回呼ぶ(元の表と日付を替えた出力)。"""
    _ix, base_files, info = context_tables(folder)
    target = period_target(info)
    if target is None:
        return False, False
    try:
        _ix2, mixed, _i2 = context_tables(folder, {target[0]: target[1]})
    except (Refuse, P.Refuse):
        return True, False
    a = base_files[info["hi"]][3]["resources"]
    b = mixed[info["hi"]][3]["resources"]
    if len(a) != len(b):
        return True, False
    changed = 0
    for ra, rb in zip(a, b):
        if ra.get("type") == "context" and info["names"].get(ra["id"]) == target[0]:
            want = od((k, v) for k, v in ra.items())
            want["period"] = target[1]
            if rb != want or ra["period"] == rb["period"]:
                return True, False
            changed += 1
        elif ra != rb:
            return True, False
    for fi, ((_n, _p, F, H), (_n2, _p2, F2, H2)) in enumerate(zip(base_files, mixed)):
        if fi != info["hi"] and (F != F2 or H != H2):
            return True, False
    return True, changed >= 1


def mix_place_effect(folder, scratch):
    u"""混ぜ物(置き場)。(作れたか, 効いたか)。道具は呼ばない。紙 2 の ``nil_form`` を逆にした写しの folder で置き場を作り直す。"""
    _ix, _sh, p2, base, empties = place_tables(folder)
    if sum(len(x) for x in empties) == 0:
        return False, False
    copy = os.path.join(scratch, "mixed_place")
    shutil.copytree(folder, copy)
    flipped = json.loads(json.dumps(p2), object_pairs_hook=od)
    flipped["nil_form"] = u"pair" if p2["nil_form"] == u"self" else u"self"
    P.write_bytes(os.path.join(copy, PAPER2_FILE), P.jdump(flipped))
    try:
        _ix2, _sh2, _p22, mixed, _e2 = place_tables(copy)
    except (Refuse, P.Refuse):
        return True, False
    flips = 0
    for fi, ((_n, _p, F, H), (_n2, _p2, F2, H2)) in enumerate(zip(base, mixed)):
        if len(F) != len(F2) or H != H2:
            return True, False
        for e, e2 in zip(F, F2):
            if e["kind"] == "nonFraction" and (e["start"], e["end"]) in empties[fi]:
                want = od((k, v) for k, v in e.items())
                want["self"] = not e["self"]
                if e2 != want:
                    return True, False
                flips += 1
            elif e != e2:
                return True, False
    return True, flips == sum(len(x) for x in empties)


# ======================================================================================================
# 書類 1 本
def new_doc_rec():
    rec = od()
    rec[u"断った"] = False
    rec[u"断った段"] = u""
    rec[u"断った理由"] = u""
    rec[u"fact の数"] = None
    rec[u"1 つずつ書く fact の数"] = None
    rec[u"1 つずつ書く fact の理由(重ねて数える)"] = od((r, 0) for r in HAND_REASONS)
    rec[u"そのほかの属性を持つ fact の数"] = None
    rec[u"決めの在る cell の数"] = None
    rec[u"1 つずつ書く fact の在る cell の数"] = None
    rec[u"例外の cell の数(元は fact が無いのに規則が付ける)"] = None
    rec[u"例外の cell の数(元は fact が在るのに規則が違う)"] = None
    rec[u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact の数"] = None
    rec[u"1 つずつ書く fact でない fact の数"] = None
    rec[u"規則が当てた fact の数"] = None
    rec[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] = None
    rec[u"紙の欄の数(項ごと)"] = None
    rec[u"紙の欄の数"] = None
    rec[u"置き場を作れた"] = False
    rec[u"置き場が同じ"] = False
    rec[u"表 F の行が全部同じ"] = False
    rec[u"文脈と単位を作れた"] = False
    rec[u"元の文脈の定義の数"] = None
    rec[u"作った定義の数"] = None
    rec[u"中身が違う id の数"] = None
    rec[u"元にだけ在る id の数"] = None
    rec[u"作った側にだけ在る id の数"] = None
    rec[u"文脈が同じ"] = False
    rec[u"単位が同じ"] = False
    rec[u"定義の並びまで同じ"] = False
    rec[u"期の名の数"] = None
    rec[u"member の数"] = None
    rec[u"単位の数"] = None
    rec[u"(ア)だけが指す id の数"] = None
    rec[u"属性を作れた"] = False
    rec[u"表 F が同じ"] = False
    rec[u"attrs が違う fact の数"] = None
    rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"] = od((ATTR_LABELS[k], 0) for k in B.NUM_ATTRS)
    rec[u"組めた"] = False
    rec[u"2 回組んで同じ"] = False
    rec[u"タクソノミが同じ"] = False
    rec[u"fact が同じ"] = False
    rec[u"鳴り方が同じ"] = False
    rec[u"全部同じ"] = False
    rec[u"包みが元と byte で同じ"] = False
    rec[u"混ぜ物(期)"] = od([(u"作れた", False), (u"効いた", False)])
    rec[u"混ぜ物(置き場)"] = od([(u"作れた", False), (u"効いた", False)])
    rec[u"置き場を作る命令の秒"] = None
    rec[u"文脈と単位を作る命令の秒"] = None
    rec[u"属性を作る命令の秒"] = None
    rec[u"組む命令の秒"] = None
    rec[u"組み直しの 1 回"] = None
    return rec


def declined_rec(rec, stage, reason):
    rec[u"断った"], rec[u"断った段"], rec[u"断った理由"] = True, stage, reason
    rec[u"組めた"] = False
    return rec


def same_bytes(entries, tree):
    u"""組んだ包みの file の全部が元の包みの同じ名の file と byte で同じか。"""
    orig = dict((info.filename, data) for info, data in entries)
    return all((P.PUBLICDOC + rel) in orig and orig[P.PUBLICDOC + rel] == data for rel, data in tree.items())


def measure_one(tool, zip_path, tmp_root=None, runner=None, proc=None):
    u"""書類 1 本。紙と紙 2 を作る → 置き場を作る(別の process)→ 比べ方 1 → 文脈と単位を作る(別の process)→ 比べ方 2 → 混ぜ物 2 つ → 属性を作る(便 XS0 の命令)→ 比べ方 1 の属性 → 組む → 比べ方 3(道具)。"""
    entries = B.load_package(zip_path)
    rec = new_doc_rec()
    d = tempfile.mkdtemp(prefix="xh0_", dir=tmp_root)
    try:
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        folder = os.path.join(d, "paper")
        try:
            sheet, info, files, p2, st = make_paper_folder(entries, zip_path, folder)
        except Refuse as exc:
            return declined_rec(rec, STAGES[0], exc.reason)
        except Exception:                                  # noqa: BLE001
            return declined_rec(rec, STAGES[0], R_SHEET_ERR)
        back = P.jload(P.read_bytes(os.path.join(folder, S.SHEET_FILE)))
        back2 = P.jload(P.read_bytes(os.path.join(folder, PAPER2_FILE)))
        cells = S.sheet_cells(back)
        cells.update(paper2_cells(back2))
        if S.leak_problems(folder) or leak_place_problems(folder):
            raise Stop(u"**置き場を作る命令に渡す folder に元の行が在る(自分の欠陥)。止める**")
        rec[u"fact の数"] = info["fact_count"]
        rec[u"1 つずつ書く fact の数"] = sum(1 for h in info["hand"] if h)
        rec[u"1 つずつ書く fact の理由(重ねて数える)"] = od(info["reasons"])
        rec[u"そのほかの属性を持つ fact の数"] = info["other_facts"]
        rec[u"決めの在る cell の数"] = st[u"決めの在る cell"]
        rec[u"1 つずつ書く fact の在る cell の数"] = st[u"1 つずつ書く fact の在る cell"]
        rec[u"例外の cell の数(元は fact が無いのに規則が付ける)"] = st[u"例外 付ける"]
        rec[u"例外の cell の数(元は fact が在るのに規則が違う)"] = st[u"例外 違う"]
        rec[u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact の数"] = st[u"1 つずつ書く fact の在る cell の中の fact"]
        rec[u"1 つずつ書く fact でない fact の数"] = st[u"1 つずつ書く fact でない fact"]
        rec[u"規則が当てた fact の数"] = st[u"規則が当てた fact"]
        rec[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] = st[u"決めの在る cell の外の fact"]
        rec[u"紙の欄の数(項ごと)"] = cells
        rec[u"紙の欄の数"] = sum(cells.values())
        placed = os.path.join(d, "placed")
        ok, reason, secs = exec_step("place", u"置き場を作る", folder, placed, cwd, proc)
        rec[u"置き場を作る命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[1], reason)
        rec[u"置き場を作れた"] = True
        pindex = P.jload(P.read_bytes(os.path.join(placed, P.INDEX_FILE)))
        pfiles = P.load_htm_tables(placed, pindex)
        rec[u"置き場が同じ"] = number_rows(files) == number_rows(pfiles)
        rec[u"表 F の行が全部同じ"] = all_rows(files) == all_rows(pfiles)
        if leak_context_problems(placed):
            raise Stop(u"**文脈と単位を作る命令に渡す folder に元の行が在る(自分の欠陥)。止める**")
        made_p, eff_p = mix_place_effect(folder, d)
        rec[u"混ぜ物(置き場)"] = od([(u"作れた", made_p), (u"効いた", eff_p)])
        ctxf = os.path.join(d, "ctx")
        ok, reason, secs = exec_step("context", u"文脈と単位を作る", placed, ctxf, cwd, proc)
        rec[u"文脈と単位を作る命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[2], reason)
        rec[u"文脈と単位を作れた"] = True
        cindex = P.jload(P.read_bytes(os.path.join(ctxf, P.INDEX_FILE)))
        cfiles = P.load_htm_tables(ctxf, cindex)
        cmp2 = compare_definitions(files, cfiles)
        rec[u"元の文脈の定義の数"] = cmp2[u"元"]
        rec[u"作った定義の数"] = cmp2[u"作った"]
        rec[u"中身が違う id の数"] = cmp2[u"中身が違う"]
        rec[u"元にだけ在る id の数"] = cmp2[u"元にだけ"]
        rec[u"作った側にだけ在る id の数"] = cmp2[u"作った側にだけ"]
        rec[u"文脈が同じ"] = bool(cmp2[u"文脈が同じ"])
        rec[u"単位が同じ"] = bool(cmp2[u"単位が同じ"])
        rec[u"定義の並びまで同じ"] = bool(cmp2[u"並びまで同じ"])
        rec[u"期の名の数"] = len(back2["periods"])
        rec[u"member の数"] = len(back2["members"])
        rec[u"単位の数"] = len(back2["units"])
        _cx, _cf, cinfo = context_tables(placed)
        rec[u"(ア)だけが指す id の数"] = sum(1 for tags in cinfo["ids"].values() if tags == set([u"ア"]))
        made_c, eff_c = mix_period_effect(placed)
        rec[u"混ぜ物(期)"] = od([(u"作れた", made_c), (u"効いた", eff_c)])
        out1 = os.path.join(d, "attrs1")
        ok, reason, secs = S.exec_attrs(ctxf, out1, cwd, proc)
        rec[u"属性を作る命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[3], reason)
        rec[u"属性を作れた"] = True
        out_index = P.jload(P.read_bytes(os.path.join(out1, P.INDEX_FILE)))
        new_files = P.load_htm_tables(out1, out_index)
        diff, by = S.compare_attrs(files, new_files)
        rec[u"attrs が違う fact の数"] = diff
        rec[u"表 F が同じ"] = diff == 0
        for k, n in by.items():
            lab = ATTR_LABELS.get(k, u"属性 そのほか")
            rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"][lab] = rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"].get(lab, 0) + n
        bout1 = os.path.join(d, "built1")
        ok, reason, secs = P.exec_build(out1, bout1, cwd, proc)
        rec[u"組む命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[4], reason)
        tree = P.read_tree(bout1)
        if set(tree) != P.expected_names(out_index):
            return declined_rec(rec, STAGES[4], R_BUILD_OUT)
        rec[u"組めた"] = True
        rec[u"包みが元と byte で同じ"] = same_bytes(entries, tree)
        bout2 = os.path.join(d, "built2")
        ok2, _r2, _s2 = P.exec_build(out1, bout2, cwd, proc)
        rec[u"2 回組んで同じ"] = bool(ok2 and P.read_tree(bout2) == tree)
        orig_zip = os.path.join(d, "orig.zip")
        B.write_package(entries, orig_zip)
        orig, orig_outs, orig_facts = T.run_package(tool, orig_zip, d, "orig", runner)
        new_zip = os.path.join(d, "new.zip")
        B.write_package(P.rebuilt_pack(entries, tree), new_zip)
        new, new_outs, new_facts = T.run_package(tool, new_zip, d, "new", runner)
        rec[u"組み直しの 1 回"] = new
        cmp = od()
        T.compare_into(cmp, orig_outs, orig_facts, orig, new_outs, new_facts, new)
        for k in (u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ"):
            rec[k] = bool(cmp[k])
        return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 数える(封 §2)
def group_totals(entries):
    u"""書類ごとの数の並び → §2 の数。"""
    declined = collections.Counter()
    reasons = collections.Counter()
    out = od()
    made = [e for e in entries if e[u"fact の数"] is not None]
    placed = [e for e in entries if e[u"置き場を作れた"]]
    ctx_ok = [e for e in entries if e[u"文脈と単位を作れた"]]
    attrs_ok = [e for e in entries if e[u"属性を作れた"]]
    hand_reasons = od((r, sum(e[u"1 つずつ書く fact の理由(重ねて数える)"][r] for e in made)) for r in HAND_REASONS)
    attr_diff = od((ATTR_LABELS[k], sum(e[u"attrs が違う属性ごとの fact の数(重ねて数える)"][ATTR_LABELS[k]] for e in attrs_ok)) for k in B.NUM_ATTRS)
    for e in entries:
        if e[u"断った"]:
            declined[e[u"断った段"]] += 1
            reasons[(e[u"断った段"], e[u"断った理由"])] += 1
    cells = od()
    for k in CELL_KEYS:
        cells[k] = sum(e[u"紙の欄の数(項ごと)"][k] for e in made)
    facts = sum(e[u"fact の数"] for e in made)
    cell_total = sum(cells.values())
    nh = sum(e[u"1 つずつ書く fact でない fact の数"] for e in made)
    out[u"書類の数"] = len(entries)
    out[u"断った書類の数"] = sum(declined.values())
    out[u"断った段ごとの数"] = od((s, declined[s]) for s in STAGES)
    out[u"断った理由ごとの数"] = od((u"%s: %s" % (s, r), n) for (s, r), n in sorted(reasons.items()))
    out[u"紙を作れた書類の数"] = len(made)
    out[u"fact の数(紙を作れた書類)"] = facts
    out[u"1 つずつ書く fact の数"] = sum(e[u"1 つずつ書く fact の数"] for e in made)
    out[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"] = hand_reasons
    out[u"そのほかの属性を持つ fact の数"] = sum(e[u"そのほかの属性を持つ fact の数"] for e in made)
    out[u"決めの在る cell の数"] = sum(e[u"決めの在る cell の数"] for e in made)
    out[u"1 つずつ書く fact の在る cell の数"] = sum(e[u"1 つずつ書く fact の在る cell の数"] for e in made)
    out[u"例外の cell の数(元は fact が無いのに規則が付ける)"] = sum(e[u"例外の cell の数(元は fact が無いのに規則が付ける)"] for e in made)
    out[u"例外の cell の数(元は fact が在るのに規則が違う)"] = sum(e[u"例外の cell の数(元は fact が在るのに規則が違う)"] for e in made)
    out[u"例外の cell の数"] = out[u"例外の cell の数(元は fact が無いのに規則が付ける)"] + out[u"例外の cell の数(元は fact が在るのに規則が違う)"]
    out[u"例外の cell が在る書類の数"] = sum(1 for e in made if e[u"例外の cell の数(元は fact が無いのに規則が付ける)"] + e[u"例外の cell の数(元は fact が在るのに規則が違う)"] > 0)
    out[u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact の数"] = sum(e[u"1 つずつ書く fact の在る cell の中の 1 つずつ書く fact でない fact の数"] for e in made)
    out[u"1 つずつ書く fact でない fact の数"] = nh
    out[u"規則が当てた fact の数"] = sum(e[u"規則が当てた fact の数"] for e in made)
    out[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] = sum(e[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] for e in made)
    out[u"置き場を作れた書類の数"] = len(placed)
    out[u"置き場が同じ書類の数"] = sum(1 for e in entries if e[u"置き場が同じ"])
    out[u"表 F の行が全部同じ書類の数"] = sum(1 for e in entries if e[u"表 F の行が全部同じ"])
    out[u"文脈と単位を作れた書類の数"] = len(ctx_ok)
    out[u"元の文脈の定義の数"] = sum(e[u"元の文脈の定義の数"] for e in ctx_ok)
    out[u"作った定義の数"] = sum(e[u"作った定義の数"] for e in ctx_ok)
    out[u"中身が違う id の数"] = sum(e[u"中身が違う id の数"] for e in ctx_ok)
    out[u"元にだけ在る id の数"] = sum(e[u"元にだけ在る id の数"] for e in ctx_ok)
    out[u"元にだけ在る id が 1 つ以上在る書類の数"] = sum(1 for e in ctx_ok if e[u"元にだけ在る id の数"] >= 1)
    out[u"作った側にだけ在る id の数"] = sum(e[u"作った側にだけ在る id の数"] for e in ctx_ok)
    out[u"文脈が同じ書類の数"] = sum(1 for e in entries if e[u"文脈が同じ"])
    out[u"単位が同じ書類の数"] = sum(1 for e in entries if e[u"単位が同じ"])
    out[u"定義の並びまで同じ書類の数"] = sum(1 for e in entries if e[u"定義の並びまで同じ"])
    out[u"期の名の数"] = sum(e[u"期の名の数"] for e in ctx_ok)
    out[u"member の数"] = sum(e[u"member の数"] for e in ctx_ok)
    out[u"単位の数"] = sum(e[u"単位の数"] for e in ctx_ok)
    out[u"(ア)だけが指す id の数"] = sum(e[u"(ア)だけが指す id の数"] for e in ctx_ok)
    out[u"属性を作れた書類の数"] = len(attrs_ok)
    out[u"fact の数(属性を作れた書類)"] = sum(e[u"fact の数"] for e in attrs_ok)
    out[u"表 F が同じ書類の数"] = sum(1 for e in entries if e[u"表 F が同じ"])
    out[u"attrs が違う fact の数"] = sum(e[u"attrs が違う fact の数"] for e in attrs_ok)
    out[u"attrs が違う属性ごとの fact の数(重ねて数える)"] = attr_diff
    out[u"組めた書類の数"] = sum(1 for e in entries if e[u"組めた"])
    out[u"fact が同じ書類の数"] = sum(1 for e in entries if e[u"fact が同じ"])
    out[u"鳴り方が同じ書類の数"] = sum(1 for e in entries if e[u"鳴り方が同じ"])
    out[u"タクソノミが同じ書類の数"] = sum(1 for e in entries if e[u"タクソノミが同じ"])
    out[u"全部同じ書類の数"] = sum(1 for e in entries if e[u"全部同じ"])
    out[u"2 回組んで同じ書類の数"] = sum(1 for e in entries if e[u"2 回組んで同じ"])
    out[u"包みが元と byte で同じ書類の数"] = sum(1 for e in entries if e[u"包みが元と byte で同じ"])
    out[u"混ぜ物(期)を作れた書類の数"] = sum(1 for e in entries if e[u"混ぜ物(期)"][u"作れた"])
    out[u"混ぜ物(期)が効いた書類の数"] = sum(1 for e in entries if e[u"混ぜ物(期)"][u"効いた"])
    out[u"混ぜ物(置き場)を作れた書類の数"] = sum(1 for e in entries if e[u"混ぜ物(置き場)"][u"作れた"])
    out[u"混ぜ物(置き場)が効いた書類の数"] = sum(1 for e in entries if e[u"混ぜ物(置き場)"][u"効いた"])
    out[u"紙の欄の数(項ごと)"] = cells
    out[u"紙の欄の数"] = cell_total
    out[u"fact の数 × 7"] = facts * 7
    out[u"紙の欄の比"] = od([(u"数", cell_total), (u"分母", facts * 7), (u"%", pct1(cell_total, facts * 7))])
    for key, label in ((u"置き場を作る命令の秒", u"置き場を作る命令の秒の合計"), (u"文脈と単位を作る命令の秒", u"文脈と単位を作る命令の秒の合計"),
                       (u"属性を作る命令の秒", u"属性を作る命令の秒の合計"), (u"組む命令の秒", u"組む命令の秒の合計")):
        out[label] = round(sum(e[key] for e in entries if e[key] is not None), 1)
    return out


def totals_of(per_doc, dev_count=DEV_COUNT):
    return od([(u"開発の 5 本", group_totals(per_doc[:dev_count])), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(per_doc[dev_count:])), (u"全部", group_totals(per_doc))])


def rate(n, d):
    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])


def judged(tot):
    u"""封 §4 の判定に要る数(丸める前の整数と %)。当たり・外れは書かない。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    n = prod[u"書類の数"]
    return od([
        (u"XH0-1 規則が当てた fact / 1 つずつ書く fact でない fact", rate(prod[u"規則が当てた fact の数"], prod[u"1 つずつ書く fact でない fact の数"])),
        (u"XH0-2 例外の cell / 決めの在る cell(1 つずつ書く fact の在る cell を除く)", rate(prod[u"例外の cell の数"], prod[u"決めの在る cell の数"] - prod[u"1 つずつ書く fact の在る cell の数"])),
        (u"XH0-3 文脈が同じ書類", od([(u"書類", prod[u"文脈が同じ書類の数"]), (u"分母", n)])),
        (u"XH0-4 文脈と単位を作る命令が断った書類", od([(u"書類", prod[u"断った段ごとの数"][STAGES[2]]), (u"分母", n)])),
        (u"XH0-5 道具が読む fact が同じ書類", od([(u"書類", prod[u"fact が同じ書類の数"]), (u"分母", n)])),
        (u"XH0-6 鳴り方が同じ書類", od([(u"書類", prod[u"鳴り方が同じ書類の数"]), (u"分母", n)])),
        (u"XH0-7 元にだけ在る id が 1 つ以上在る書類", od([(u"書類", prod[u"元にだけ在る id が 1 つ以上在る書類の数"]), (u"分母", n)])),
        (u"XH0-8 混ぜ物が効いた書類 / 作れた書類", od([(u"期", od([(u"書類", prod[u"混ぜ物(期)が効いた書類の数"]), (u"分母", prod[u"混ぜ物(期)を作れた書類の数"])])),
                                          (u"置き場", od([(u"書類", prod[u"混ぜ物(置き場)が効いた書類の数"]), (u"分母", prod[u"混ぜ物(置き場)を作れた書類の数"])]))])),
        (u"XH0-9 紙の欄の数 / fact の数 × 7", prod[u"紙の欄の比"]),
        (u"XH0-10 包みが元と byte で同じ書類", od([(u"書類", prod[u"包みが元と byte で同じ書類の数"]), (u"分母", n)]))])


def suspicions(ch, whole=True):
    u"""封 §4 の「先に自分の欠陥を疑う場合」に当たる条件の名前の並び。``whole`` が偽(開発の 5 本)なら、62 本の全部で 0 かどうかは掛けない。"""
    out = []
    if ch[u"決めの在る cell の外に在る 1 つずつ書く fact でない fact の数"] > 0:
        out.append(u"決めの在る cell の外に 1 つずつ書く fact でない fact が在る")
    if ch[u"置き場を作れた書類の数"] and ch[u"置き場が同じ書類の数"] < ch[u"置き場を作れた書類の数"]:
        out.append(u"置き場が同じでない書類が在る")
    if whole and ch[u"紙を作れた書類の数"] and ch[u"例外の cell の数"] == 0:
        out.append(u"例外の cell が全部の書類で 0")
    if ch[u"文脈と単位を作れた書類の数"] and ch[u"文脈が同じ書類の数"] > ch[u"fact が同じ書類の数"]:
        out.append(u"文脈が同じなのに道具が読む fact が違う書類が在る")
    if ch[u"断った書類の数"] >= SUSPECT_DECLINED:
        out.append(u"断った書類が 10 本以上")
    if ch[u"混ぜ物(期)を作れた書類の数"] < ch[u"文脈と単位を作れた書類の数"] or ch[u"混ぜ物(置き場)を作れた書類の数"] < ch[u"置き場を作れた書類の数"]:
        out.append(u"混ぜ物を作れなかった書類が在る")
    return out


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    return S.check_tool(tool, runner, sha_reader, want_version, want_sha)


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XB0 の関数。残りの zip は開かない)。"""
    return B.dev_docs(docs_dir, count)


def doc_secret_strings(zip_path):
    u"""記録に書かない字(要素の局所名・文脈の名・member の名)。書類を読むだけ。読めなければ空。"""
    return S.doc_secret_strings(zip_path)


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, dev_count=DEV_COUNT, proc=None, progress=None):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    per_doc = []
    names = set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        r = measure_one(tool_p, p, tmp_root, runner, proc)
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        names |= doc_secret_strings(p)
        if progress is not None:
            progress(u"doc %d/%d(%.0f 秒)" % (n, len(docs), time.time() - t0))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (set(), set(e for e in names if len(e) >= 3), [d[0] for d in docs], ecodes)
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XH0(数の置き場を表の cell の字から決め、文脈と単位の定義を紙から作って包みを組むと、道具が読む fact は元と同じになるか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"時間の上限(秒)", TIMEOUT_SEC), (u"script の決めの字", list(RULES))])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XH0-1〜XH0-10。本番だけの 62 本。当たり・外れは結果の文書で)"] = judged(tot)
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字・紙の中身)が無いか。在れば止める。"""
    S.check_clean(rec, text, secret)


DOC_KEYS = [u"番号"] + list(new_doc_rec().keys())


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i or list(d) != DOC_KEYS:
            raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != bool(d[u"断った理由"]) or d[u"断った"] != bool(d[u"断った段"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"断った"] and (d[u"全部同じ"] or d[u"fact が同じ"] or d[u"鳴り方が同じ"] or d[u"組めた"] or d[u"2 回組んで同じ"]):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"全部同じ"] != (d[u"タクソノミが同じ"] and d[u"fact が同じ"]):
            raise Stop(u"**全部同じの導き方が違う。止める**")
        if d[u"表 F が同じ"] != (d[u"attrs が違う fact の数"] == 0 and d[u"属性を作れた"]):
            raise Stop(u"**表 F が同じの導き方が違う。止める**")
        if d[u"文脈が同じ"] and not d[u"文脈と単位を作れた"]:
            raise Stop(u"**文脈が同じの導き方が違う。止める**")
        if d[u"文脈が同じ"] and (d[u"中身が違う id の数"] or d[u"元にだけ在る id の数"] or d[u"作った側にだけ在る id の数"]):
            raise Stop(u"**文脈が同じの導き方が違う。止める**")
        if d[u"置き場が同じ"] and not d[u"置き場を作れた"]:
            raise Stop(u"**置き場が同じの導き方が違う。止める**")
        if d[u"fact の数"] is not None:
            if list(d[u"紙の欄の数(項ごと)"]) != list(CELL_KEYS) or d[u"紙の欄の数"] != sum(d[u"紙の欄の数(項ごと)"].values()):
                raise Stop(u"**紙の欄の数の項が合わない。止める**")
            if list(d[u"1 つずつ書く fact の理由(重ねて数える)"]) != list(HAND_REASONS) or not (0 <= d[u"1 つずつ書く fact の数"] <= d[u"fact の数"]):
                raise Stop(u"**1 つずつ書く fact の数が合わない。止める**")
            if d[u"1 つずつ書く fact の数"] > sum(d[u"1 つずつ書く fact の理由(重ねて数える)"].values()) or d[u"紙の欄の数(項ごと)"][u"1 つずつ書く fact × 7"] != 7 * d[u"1 つずつ書く fact の数"]:
                raise Stop(u"**1 つずつ書く fact の数が合わない。止める**")
            if d[u"1 つずつ書く fact でない fact の数"] != d[u"fact の数"] - d[u"1 つずつ書く fact の数"]:
                raise Stop(u"**1 つずつ書く fact でない fact の数が合わない。止める**")
            if d[u"規則が当てた fact の数"] > d[u"1 つずつ書く fact でない fact の数"] or d[u"1 つずつ書く fact の在る cell の数"] > d[u"決めの在る cell の数"]:
                raise Stop(u"**置き場の数が合わない。止める**")
            if d[u"紙の欄の数(項ごと)"][u"1 つずつ書く fact の始まりと終わり"] != 2 * d[u"1 つずつ書く fact の数"]:
                raise Stop(u"**紙 2 の欄の数が合わない。止める**")
        for k in (u"混ぜ物(期)", u"混ぜ物(置き場)"):
            if d[k][u"効いた"] and not d[k][u"作れた"]:
                raise Stop(u"**混ぜ物の形が違う。止める**")
        if list(d[u"attrs が違う属性ごとの fact の数(重ねて数える)"]) != [ATTR_LABELS[k] for k in B.NUM_ATTRS]:
            raise Stop(u"**属性ごとの欄が違う。止める**")
    tot = totals_of(docs, dev_count)
    if dumps(tot) != dumps(rec[u"集計"]) or dumps(judged(tot)) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
        raise Stop(u"**記録の合計が書類ごとの数と合わない。止める**")
    check_clean(rec, text if text is not None else dumps(rec))


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


def run(tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, say=print, dev_count=DEV_COUNT, proc=None, progress=None):
    rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count, proc, progress)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, rec_path=None, say=print, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する。置き場も道具も読まない。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want, dev_count)
    say(u"--check: 記録の形・合計・禁止のものの検査は通った(書類 %d)" % len(rec[u"書類"]))
    return rec


def dev_run(tool_p, docs_dir=None, runner=None, tmp_root=None, say=print, proc=None, count=DEV_COUNT):
    u"""開発の 5 本だけ(記録は書かない)。(書類ごとの数の並び)。"""
    docs = dev_docs(docs_dir or DOCS_DIR, count)
    check_tool(tool_p, runner)
    per = []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        r = measure_one(tool_p, p, tmp_root, runner, proc)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d(%.0f 秒): 断った=%s(%s・%s) fact=%s 1つずつ=%s 決めの在るcell=%s 例外=%s+%s 当てた=%s/%s 置き場同じ=%s 文脈同じ=%s 表F同じ=%s 組めた=%s fact同じ=%s 鳴り方=%s 期混ぜ=%s 置混ぜ=%s 紙の欄=%s" % (
            n, time.time() - t0, r[u"断った"], r[u"断った段"], r[u"断った理由"], r[u"fact の数"], r[u"1 つずつ書く fact の数"], r[u"決めの在る cell の数"],
            r[u"例外の cell の数(元は fact が無いのに規則が付ける)"], r[u"例外の cell の数(元は fact が在るのに規則が違う)"], r[u"規則が当てた fact の数"], r[u"1 つずつ書く fact でない fact の数"],
            r[u"置き場が同じ"], r[u"文脈が同じ"], r[u"表 F が同じ"], r[u"組めた"], r[u"fact が同じ"], r[u"鳴り方が同じ"], dict(r[u"混ぜ物(期)"]), dict(r[u"混ぜ物(置き場)"]), r[u"紙の欄の数"]))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    tot = group_totals(per)
    say(json.dumps(tot, ensure_ascii=False, indent=2))
    say(u"先に自分の欠陥を疑う場合に当たったもの: %s" % (u"・".join(suspicions(tot, whole=False)) or u"なし"))
    return per


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "place":
        sys.exit(place_main(argv[1:]))
    if argv and argv[0] == "context":
        sys.exit(context_main(argv[1:]))
    if argv and argv[0] == "paper":
        sys.exit(paper_main(argv[1:]))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ掛ける。記録は書かない")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
        return
    if not a.tool_p:
        raise Stop(u"**--tool-p が要る。止める**")
    if a.dev:
        dev_run(a.tool_p, docs_dir=a.docs)
        return
    run(a.tool_p, root=a.root, docs=a.docs, progress=lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
