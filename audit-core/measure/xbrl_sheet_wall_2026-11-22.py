# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md(XA0 ― 受理済みの有報の数の fact の属性は、表の「行ごと・列ごとの決め」でどれだけ決まるか。人が 1 つずつ書かなければならない欄はどれだけ残るか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。道具(Arelle)も呼ばない。** engine(``core/``・``adapters/``)は読まない・変えない。書類の選び方・包みの開き方・剥がす関数(``strip_text``)は前の便(XB0・XG0)の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_sheet_wall_2026-11-22.py            # 67 本を数えて記録 fixtures/xbrl/cd8/sheet_wall_2026-11-22.json を書く(5 本と 62 本を別の塊で)。本番は 1 回
    python3 measure/xbrl_sheet_wall_2026-11-22.py --check    # 記録の形・合計を検査し、置き場から数え直して記録と照らす
    python3 measure/xbrl_sheet_wall_2026-11-22.py --dev      # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かず stdout に数

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 表・行・cell の読み方: ``table``・``tr``・``td``・``th`` の開きタグ・閉じタグだけを、元の字の中から読む(``<!-- -->`` の中は読まない)。入れ子は厳密に ``table > tr > (td か th)``。
  次のどれかなら「1 通りに読めない」: ``tr`` の親が ``table`` でない・``td``/``th`` の親が ``tr`` でない・閉じタグが今開いている要素(``td`` は ``td``・``th`` は ``th``)と合わない・開いたまま file が終わる・何も開いていない所で閉じる。
  ``/>`` で終わる開きタグは中身の無い要素(積まない。``td``・``th`` は列の和には数える)。
  この読みは、``ix:nonFraction`` を 1 つ以上持つ file だけに掛ける(fact の置き場が決まらないのは fact を持つ file の話なので。fact の無い file の表の形は見ない)。
- fact の位置: ``strip_text`` の表 F の行(開きタグの順)と、元の字の ``ix:`` の開きタグ(``ix:header`` の中を除く)を同じ順で対応させる。数・種類が合わなければ断る。
- ``colspan`` の読み方: 値の字が 10 進の整数(``\\d+``)で 1 以上ならその数・そのほかは 1。
- 最頻が並んだ線: 線の上の fact(書類の中の順)のうち、並んだ値を持つ最初の fact の値(線の上だけで見る)。書類全体の先頭ではない。
- 書式の最頻が並んだ類: 書類の中の順で、その類の中で先に現れた値。
- fact の中の字・符号の字: タグ(``<...>``)を落とし、実体参照は直さない(``&#160;`` などは「そのほか」に入る)・前後の空白は ``str.strip``。
- 書式の類 (2) は空でない字だけ(空の字は (3))。
- 「向き B の方が決まる fact が多かった表の数」は「向き B を選んだ表の数」と必ず同じ数になる(同じ数のときは向き A)。両方を並べて書く。
- 書く欄の数の「空の fact の数 × 1」は、書類の中の空の fact 全部(表の外の空の fact も数える。表の外の fact の項にも 7 で入る)。
  「書類で現れた書式の類の数」は、書類の中の空でない fact 全部の字の類(表の中・外を問わない)。
- 断った書類は fact の数・書く欄の数を持たない(分母から除く。断った数と理由は別に書く)。fact が 0 の書類は断らない(分母の数は書く)。
- ``sign`` は ``-`` であることを「sign が在る」と読む。符号が合わない 2 つの数は、「負と読んだが sign が ``-`` でない」と「sign が ``-`` だが負と読めない」。
- 率は四捨五入(0.5 は上げる)で小数第 1 位。判定に要る数は丸める前の整数も書く。
"""
from __future__ import print_function

import argparse
import collections
import importlib.util
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

INLINE_NAME = "_xa0_inline_build_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load_sibling(INLINE_NAME, "xbrl_inline_build_2026-11-21.py")      # 便 XB0 の script
W = B.W                                                                  # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_SHEET_WALL_SEAL_2026-11-22.md"
SEAL_COMMIT = "3062223e"
SCRIPT_REL = "measure/xbrl_sheet_wall_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT
DEV_COUNT = 5
PUBLICDOC = B.PUBLICDOC

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format")
NIL_ATTRS = ("name", "contextRef", "unitRef")
NIL_ATTR = "xsi:nil"
SIGN_CHARS = u"△▲-－−‐"
DASH_CHARS = u"－―‐-—−"
NUM_CHARS = u"0123456789０１２３４５６７８９,，.．"
FORMAT_CLASSES = ("1", "2", "3")
ORIENTS = ("A", "B")
CELL_ATTR_PER_ELEMENT_LINE = 4          # name・unitRef・decimals・scale
CELL_PER_CONTEXT_LINE = 1               # contextRef
CELL_PER_TABLE = 1                      # 向き
CELLS_PER_FACT = 7
NOMODE = u"\x00線に値が無い"
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) の % か None。XA0-6 は本数。
#: 下限は含む。上限は XA0-2・XA0-4 は含まない・そのほかは含む(封の字: 「75% 以上 95% 未満」「35% 以上 60% 未満」「5% 以上 30% 以下」)
BOUNDS = collections.OrderedDict([
    ("XA0-1", (97, None)), ("XA0-2", (75, 95)), ("XA0-3", (98, None)), ("XA0-4", (35, 60)), ("XA0-5", (5, 30)), ("XA0-6", (None, 30)), ("XA0-7", (98, None))])
BOUNDS_UPPER_EXCLUSIVE = ("XA0-2", "XA0-4")
DOC_FULL_PCT = 90
SUSPECT_ABSENT_FACTS_PCT = 50
SUSPECT_DECLINED = 6
RULES = [
    u"対象は ix:nonFraction の全部(PublicDoc の htm。便 XB0 の strip_text の表 F)",
    u"見る属性 7 つ: name・contextRef・unitRef・decimals・scale・sign・format。属性が無いことは「無い」という 1 つの値",
    u"空の fact(xsi:nil が true)は name・contextRef・unitRef だけを見る",
    u"fact の表は、開きタグの位置で開いている table のうち最も内側。行・cell はその表に直に属する開いている tr・td か th。どれかが無ければ表の外",
    u"行の番号は表に直に属する tr の開きタグの順。列の番号は行の中で前に在る td・th の colspan の和(rowspan は見ない)",
    u"向き A は要素の線が行・文脈の線が列。向き B は逆。表ごとに決まる fact が多い向きを選ぶ。同じなら向き A",
    u"線の決めは線の上の fact の最頻の値(unitRef は空の fact も含む・decimals と scale は空でない fact だけ)。並んだら先に現れた fact の値",
    u"符号は cell の開きタグの終わりから fact の開きタグの始まりまでの字(タグを除く)に △▲-－−‐ のどれかが在れば負",
    u"書式は fact の中の字を 3 つの類(ダッシュだけ・数字と , . だけ・そのほか)に分け、書類の同じ類の最頻の format と同じなら合う",
    u"書く欄の数は 向き 1 + 要素の線 × 4 + 文脈の線 × 1(表ごと)+ 書式の類の数 + 空の fact の数 + 表の中で全部決まらない fact × 7 + 表の外の fact × 7",
]
LIMITS = [
    u"線の決めは答え(その線の上の fact の最頻の値)から作っている。人が紙に書く値が正しいかは測っていない。「人が書く量はこれだけで済む」とは読まない。",
    u"線の上の fact が 1 つだけなら、その fact は決めと必ず同じになる。書く欄の比はこの分を数えているが、「全部決まる fact」の率は甘く出る。1 つだけの線の数は別に書く。",
    u"rowspan を見ないので、列の番号は見た目の列とずれることが在る(決まらない側に数えられる)。",
    u"数の fact だけ。文の fact・脚注は数えない。要素を選ぶこと自体・文脈を作ること・提出者別タクソノミの中身は、この便の数に入っていない。",
    u"受理済みの書類を答えとして読んだ数で、原稿から作った数ではない。67 本は無作為ではない。有報だけ。",
    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
od = collections.OrderedDict
sha256_bytes = W.sha256_bytes
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1

TAG_RE = re.compile(r"<[^>]*>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TABLE_TAG_RE = re.compile(r"<(/?)(table|tr|td|th)(?=[\s/>])([^>]*)>", re.I)
COLSPAN_RE = re.compile(r"""\bcolspan\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))""", re.I)
INT_RE = re.compile(r"^\d+$")


class Refuse(Exception):
    u"""読めない形(その書類を断る)。``reason`` は固定の字(材料の字を入れない)。"""

    def __init__(self, reason):
        Exception.__init__(self, reason)
        self.reason = reason


R_TABLE = u"表の開き閉じが 1 通りに読めない"
R_ALIGN = u"ix の開きタグが表 F と合わない"
R_ENC = u"文字の符号化が読めない"
R_EXC = u"剥がす途中の例外"


# ======================================================================================================
# 字の読み方(封 §1)
def strip_tags(s):
    return TAG_RE.sub(u"", s)


def colspan_of(attr_text):
    u"""``colspan`` の値の字が 10 進の整数で 1 以上ならその数・そのほかは 1。"""
    m = COLSPAN_RE.search(attr_text)
    if not m:
        return 1
    v = next(g for g in m.groups() if g is not None).strip()
    if not INT_RE.match(v):
        return 1
    n = int(v)
    return n if n >= 1 else 1


def table_tokens(text):
    u"""[(start, end, closing, name, attrs, selfclosed)]。``<!-- -->`` の中は読まない。"""
    masked = [(m.start(), m.end()) for m in COMMENT_RE.finditer(text)]
    out = []
    j = 0
    for m in TABLE_TAG_RE.finditer(text):
        while j < len(masked) and masked[j][1] <= m.start():
            j += 1
        if j < len(masked) and masked[j][0] <= m.start() < masked[j][1]:
            continue
        attrs = m.group(3)
        out.append((m.start(), m.end(), m.group(1) == "/", m.group(2).lower(), attrs, attrs.rstrip().endswith("/")))
    return out


def step_token(stack, counter, tok):
    u"""開閉の 1 つを積み直す。1 通りに読めなければ ``Refuse``。``counter`` は [これまでに開いた table の数]。"""
    _start, end, closing, name, attrs, selfc = tok
    if closing:
        if not stack or stack[-1][0] != name:
            raise Refuse(R_TABLE)
        stack.pop()
    elif name == "table":
        if not selfc:
            stack.append(["table", counter[0], 0])
        counter[0] += 1
    elif name == "tr":
        if not stack or stack[-1][0] != "table":
            raise Refuse(R_TABLE)
        row = stack[-1][2]
        stack[-1][2] += 1
        if not selfc:
            stack.append(["tr", row, 0])
    else:
        if not stack or stack[-1][0] != "tr":
            raise Refuse(R_TABLE)
        col = stack[-1][2]
        stack[-1][2] += colspan_of(attrs)
        if not selfc:
            stack.append([name, col, end])


def cell_of_stack(stack):
    u"""いま開いている要素の積み → (表の番号, 行の番号, 列の番号, cell の開きタグの終わり) か None(表の外)。最も内側の table の直下の tr・その中の td か th。"""
    k = None
    for i in range(len(stack) - 1, -1, -1):
        if stack[i][0] == "table":
            k = i
            break
    if k is not None and len(stack) >= k + 3 and stack[k + 1][0] == "tr" and stack[k + 2][0] in ("td", "th"):
        return (stack[k][1], stack[k + 1][1], stack[k + 2][1], stack[k + 2][2])
    return None


def place_positions(text, positions):
    u"""元の字の中の位置(昇順)ごとに、(表の番号, 行の番号, 列の番号, cell の開きタグの終わり) か None(表の外)を返す。1 通りに読めなければ ``Refuse``。"""
    toks = table_tokens(text)
    stack = []
    counter = [0]
    out = []
    ti = 0
    for p in positions:
        while ti < len(toks) and toks[ti][0] < p:
            step_token(stack, counter, toks[ti])
            ti += 1
        out.append(cell_of_stack(stack))
    while ti < len(toks):
        step_token(stack, counter, toks[ti])
        ti += 1
    if stack:
        raise Refuse(R_TABLE)
    return out


def open_positions(text):
    u"""元の字の ``ix:`` の開きタグ(``ix:header`` の中と ``ix:header`` 自身を除く)の [(位置, 種類)]。表 F の行と同じ順(便 XB0 の ``strip_text`` と同じ数え方)。"""
    out = []
    in_header = False
    for m in B.IX_TAG_RE.finditer(text):
        closing, name = m.group(1) == "/", m.group(2)
        if in_header:
            if name == "ix:header":
                in_header = False
            continue
        if name == "ix:header":
            in_header = True
            continue
        if closing:
            continue
        out.append((m.start(), name[3:]))
    return out


def facts_of_text(text):
    u"""元の ``.htm`` の字 → [fact(dict)]。``nonFraction`` だけ。順は開きタグの順。知らない形は ``Refuse``(便 XB0 の断りも ``Refuse`` に直す)。"""
    try:
        plain, F, _H = B.strip_text(text)
    except B.Decline as exc:
        raise Refuse(exc.reason)
    except Exception:                                      # noqa: BLE001  知らない形は断る
        raise Refuse(R_EXC)
    opens = open_positions(text)
    if len(opens) != len(F) or any(k != e["kind"] for (_p, k), e in zip(opens, F)):
        raise Refuse(R_ALIGN)
    idx = [i for i, e in enumerate(F) if e["kind"] == "nonFraction"]
    if not idx:
        return []
    cells = place_positions(text, [opens[i][0] for i in idx])
    out = []
    for i, cell in zip(idx, cells):
        e = F[i]
        p = opens[i][0]
        attrs = dict(e["attrs"])
        f = dict(attrs=attrs, nil=attrs.get(NIL_ATTR) == "true", text=strip_tags(plain[e["start"]:e["end"]]).strip(), table=None, row=None, col=None, between=u"")
        if cell is not None:
            f["table"], f["row"], f["col"] = cell[0], cell[1], cell[2]
            f["between"] = strip_tags(text[cell[3]:p])
        out.append(f)
    return out


def facts_of_files(files):
    u"""[(名, 字)] → [fact]。名の昇順・各 file の中は開きタグの順。表の番号は file をまたいで重ならない。"""
    out = []
    for fi, (_n, text) in enumerate(sorted(files, key=lambda p: p[0])):
        for f in facts_of_text(text):
            if f["table"] is not None:
                f["table"] = (fi, f["table"])
            out.append(f)
    return out


# ======================================================================================================
# 数える(封 §1・§2)
def mode_first(values):
    u"""最頻の値。並んだら、並んだ値のうち先に現れたもの。値が無ければ ``NOMODE``。"""
    if not values:
        return NOMODE
    counts = od()
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.values())
    for v, c in counts.items():
        if c == best:
            return v


def format_class(s):
    u"""fact の中の字(タグを除き前後の空白を落とした字)の類: 1 ダッシュだけ・2 数字と , . だけ・3 そのほか(空の字も 3)。"""
    if s and all(ch in DASH_CHARS for ch in s):
        return "1"
    if s and all(ch in NUM_CHARS for ch in s):
        return "2"
    return "3"


def reads_negative(between):
    return any(ch in SIGN_CHARS for ch in between)


def line_keys(f, orient):
    u"""(要素の線, 文脈の線)。向き A は (行, 列)・向き B は (列, 行)。"""
    return (f["row"], f["col"]) if orient == "A" else (f["col"], f["row"])


def mismatches(items, orient):
    u"""表の中の fact の並び → [(name, contextRef, unitRef, decimals, scale が線の決めと違うか の 5 つの真偽)]。"""
    el, cx = {}, {}
    for i, f in enumerate(items):
        e, c = line_keys(f, orient)
        el.setdefault(e, []).append(i)
        cx.setdefault(c, []).append(i)
    dec = {}
    for e, ids in el.items():
        a = [items[i]["attrs"] for i in ids]
        live = [x for i, x in zip(ids, a) if not items[i]["nil"]]
        dec[e] = (mode_first([x.get("name") for x in a]), mode_first([x.get("unitRef") for x in a]),
                  mode_first([x.get("decimals") for x in live]), mode_first([x.get("scale") for x in live]))
    cdec = dict((c, mode_first([items[i]["attrs"].get("contextRef") for i in ids])) for c, ids in cx.items())
    out = []
    for f in items:
        e, c = line_keys(f, orient)
        a = f["attrs"]
        d = dec[e]
        out.append((a.get("name") != d[0], a.get("contextRef") != cdec[c], a.get("unitRef") != d[1],
                    (not f["nil"]) and a.get("decimals") != d[2], (not f["nil"]) and a.get("scale") != d[3]))
    return out


def decided_count(flags):
    return sum(1 for fl in flags if not any(fl))


def lines_of(items, orient):
    u"""(要素の線の数, 文脈の線の数, 1 つだけの要素の線の数)。"""
    el, cx = {}, set()
    for f in items:
        e, c = line_keys(f, orient)
        el[e] = el.get(e, 0) + 1
        cx.add(c)
    return len(el), len(cx), sum(1 for n in el.values() if n == 1)


REASONS = (u"name が線の決めと違う", u"contextRef が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う")
ACC_KEYS = ("fact", "nil", "outside", "inside", "tables", "tables_A", "tables_B", "tables_B_more", "tables_single", "decided",
            "r_name", "r_context", "r_unit", "r_decimals", "r_scale", "live_inside", "sign_ok", "sign_neg_no_attr", "sign_attr_no_neg", "format_ok", "format_bad",
            "full", "single_lines", "single_facts", "c_orient", "c_elem", "c_ctx", "c_formats", "c_nil", "c_undecided", "c_outside", "elem_lines", "ctx_lines")


def new_acc():
    return od((k, 0) for k in ACC_KEYS)


def count_facts(facts):
    u"""書類 1 本の fact の並び → 数(``ACC_KEYS``)。"""
    acc = new_acc()
    acc["fact"] = len(facts)
    acc["nil"] = sum(1 for f in facts if f["nil"])
    acc["outside"] = sum(1 for f in facts if f["table"] is None)
    acc["inside"] = acc["fact"] - acc["outside"]
    live = [f for f in facts if not f["nil"]]
    modes = {}
    for k in FORMAT_CLASSES:
        modes[k] = mode_first([f["attrs"].get("format") for f in live if format_class(f["text"]) == k])
    acc["c_formats"] = len(set(format_class(f["text"]) for f in live))
    tables = od()
    for i, f in enumerate(facts):
        if f["table"] is not None:
            tables.setdefault(f["table"], []).append(i)
    full_ids = set()
    for ids in tables.values():
        items = [facts[i] for i in ids]
        fa, fb = mismatches(items, "A"), mismatches(items, "B")
        da, db = decided_count(fa), decided_count(fb)
        orient, flags = ("B", fb) if db > da else ("A", fa)
        acc["tables"] += 1
        acc["tables_" + orient] += 1
        if orient == "B":
            acc["tables_B_more"] += 1
        if len(items) == 1:
            acc["tables_single"] += 1
        el, cx, one = lines_of(items, orient)
        acc["elem_lines"] += el
        acc["ctx_lines"] += cx
        acc["single_lines"] += one
        acc["single_facts"] += one
        acc["decided"] += decided_count(flags)
        for fl in flags:
            for key, hit in zip(("r_name", "r_context", "r_unit", "r_decimals", "r_scale"), fl):
                acc[key] += 1 if hit else 0
        for i, f, fl in zip(ids, items, flags):
            ok = not any(fl)
            if not f["nil"]:
                acc["live_inside"] += 1
                neg = reads_negative(f["between"])
                has = f["attrs"].get("sign") == "-"
                if neg == has:
                    acc["sign_ok"] += 1
                elif neg:
                    acc["sign_neg_no_attr"] += 1
                else:
                    acc["sign_attr_no_neg"] += 1
                fmt_ok = f["attrs"].get("format") == modes[format_class(f["text"])]
                acc["format_ok"] += 1 if fmt_ok else 0
                acc["format_bad"] += 0 if fmt_ok else 1
                ok = ok and neg == has and fmt_ok
            if ok:
                full_ids.add(i)
    acc["full"] = len(full_ids)
    acc["c_orient"] = acc["tables"] * CELL_PER_TABLE
    acc["c_elem"] = acc["elem_lines"] * CELL_ATTR_PER_ELEMENT_LINE
    acc["c_ctx"] = acc["ctx_lines"] * CELL_PER_CONTEXT_LINE
    acc["c_nil"] = acc["nil"]
    acc["c_undecided"] = (acc["inside"] - acc["full"]) * CELLS_PER_FACT
    acc["c_outside"] = acc["outside"] * CELLS_PER_FACT
    return acc


def cells_of(acc):
    u"""書く欄の数(項の合計)。"""
    return acc["c_orient"] + acc["c_elem"] + acc["c_ctx"] + acc["c_formats"] + acc["c_nil"] + acc["c_undecided"] + acc["c_outside"]


def cells_if_all_decided(acc):
    return cells_of(acc) - acc["c_undecided"]


def add_into(tot, acc):
    for k in ACC_KEYS:
        tot[k] += acc[k]


# ======================================================================================================
# 書類・塊
def doc_texts(zip_path):
    u"""元の包みの PublicDoc の .htm を [(名, 字)] で(名の昇順)。置き場の zip は開くだけ。"""
    out = []
    for info, data in B.load_package(zip_path):
        if B.is_public_htm(info.filename):
            try:
                out.append((info.filename, data.decode("utf-8")))
            except UnicodeDecodeError:
                raise Refuse(R_ENC)
    out.sort(key=lambda t: t[0])
    return out


def count_zip(zip_path):
    u"""(数 か None, 断った理由 か 空の字)。"""
    try:
        return count_facts(facts_of_files(doc_texts(zip_path))), u""
    except Refuse as exc:
        return None, exc.reason


def doc_row(n, acc, reason):
    if acc is None:
        return od([(u"番号", n), (u"断った", True), (u"断った理由", reason), (u"fact の数", None), (u"表の外の fact の数", None), (u"全部決まる fact の数", None), (u"書く欄の数", None)])
    return od([(u"番号", n), (u"断った", False), (u"断った理由", u""), (u"fact の数", acc["fact"]), (u"表の外の fact の数", acc["outside"]),
               (u"全部決まる fact の数", acc["full"]), (u"書く欄の数", cells_of(acc))])


def rate(n, d):
    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])


def chunk_of(rows, accs):
    u"""書類の行(``doc_row``)と数の並び(断った書類は None)→ 塊の §2 の数。"""
    tot = new_acc()
    reasons = od()
    kept = 0
    for r, a in zip(rows, accs):
        if a is None:
            reasons[r[u"断った理由"]] = reasons.get(r[u"断った理由"], 0) + 1
        else:
            kept += 1
            add_into(tot, a)
    c = cells_of(tot)
    base = tot["fact"] * CELLS_PER_FACT
    c_full = cells_if_all_decided(tot)
    out = od()
    out[u"書類の数"] = len(rows)
    out[u"断った書類の数"] = len(rows) - kept
    out[u"断った理由ごとの数"] = od(sorted(reasons.items()))
    out[u"断らなかった書類の数"] = kept
    out[u"fact の数"] = tot["fact"]
    out[u"空の fact の数"] = tot["nil"]
    out[u"表の外の fact の数"] = tot["outside"]
    out[u"表の中の fact の数"] = tot["inside"]
    out[u"fact の在る表の数"] = tot["tables"]
    out[u"向き A を選んだ表の数"] = tot["tables_A"]
    out[u"向き B を選んだ表の数"] = tot["tables_B"]
    out[u"向き B の方が決まる fact が多かった表の数"] = tot["tables_B_more"]
    out[u"fact が 1 つだけの表の数"] = tot["tables_single"]
    out[u"表の決めで決まる fact の数"] = tot["decided"]
    out[u"決まらなかった理由ごとの fact の数(重ねて数える)"] = od(zip(REASONS, (tot["r_name"], tot["r_context"], tot["r_unit"], tot["r_decimals"], tot["r_scale"])))
    out[u"表の中の空でない fact の数"] = tot["live_inside"]
    out[u"符号が合う fact の数"] = tot["sign_ok"]
    out[u"符号が合わない fact の数(負と読んだが sign が - でない)"] = tot["sign_neg_no_attr"]
    out[u"符号が合わない fact の数(sign が - だが負と読めない)"] = tot["sign_attr_no_neg"]
    out[u"書式が合う fact の数"] = tot["format_ok"]
    out[u"書式が合わない fact の数"] = tot["format_bad"]
    out[u"全部決まる fact の数"] = tot["full"]
    out[u"書く欄の数(項ごと)"] = od([(u"向き(表ごとに 1)", tot["c_orient"]), (u"要素の線 × 4", tot["c_elem"]), (u"文脈の線 × 1", tot["c_ctx"]), (u"書式の類の数", tot["c_formats"]),
                                   (u"空の fact の数 × 1", tot["c_nil"]), (u"表の中で全部決まらない fact × 7", tot["c_undecided"]), (u"表の外の fact × 7", tot["c_outside"])])
    out[u"要素の線の数(fact の在る)"] = tot["elem_lines"]
    out[u"文脈の線の数(fact の在る)"] = tot["ctx_lines"]
    out[u"書く欄の数"] = c
    out[u"fact の数 × 7"] = base
    out[u"書く欄の比"] = rate(c, base)
    out[u"表の中の fact が全部決まる場合の書く欄の数"] = c_full
    out[u"表の中の fact が全部決まる場合の比"] = rate(c_full, base)
    out[u"線の上の fact が 1 つだけの要素の線の数"] = tot["single_lines"]
    out[u"その線の上の fact の数"] = tot["single_facts"]
    out[u"全部決まる fact が %d%% 以上の書類の数" % DOC_FULL_PCT] = docs_full(accs)
    out[u"fact が 1 つ以上在る書類の数(断らなかった)"] = sum(1 for a in accs if a is not None and a["fact"] > 0)
    return out


def docs_full(accs):
    return sum(1 for a in accs if a is not None and a["fact"] > 0 and 100 * a["full"] >= DOC_FULL_PCT * a["fact"])


def judged(ch, accs):
    u"""XA0-1〜XA0-7 の判定に要る数(丸める前の整数と %)。当たり・外れは書かない。"""
    tot = new_acc()
    for a in accs:
        if a is not None:
            add_into(tot, a)
    return od([
        (u"XA0-1 表の中の fact / fact", rate(tot["inside"], tot["fact"])),
        (u"XA0-2 全部決まる fact / fact", rate(tot["full"], tot["fact"])),
        (u"XA0-3 符号が合う fact / 表の中の空でない fact", rate(tot["sign_ok"], tot["live_inside"])),
        (u"XA0-4 書く欄の数 / fact の数 × 7", rate(cells_of(tot), tot["fact"] * CELLS_PER_FACT)),
        (u"XA0-5 向き B の方が決まる fact が多かった表 / fact の在る表", rate(tot["tables_B_more"], tot["tables"])),
        (u"XA0-6 全部決まる fact が %d%% 以上の書類 / fact が 1 つ以上在る書類" % DOC_FULL_PCT,
         od([(u"書類", docs_full(accs)), (u"分母", sum(1 for a in accs if a is not None and a["fact"] > 0))])),
        (u"XA0-7 書式が合う fact / 表の中の空でない fact", rate(tot["format_ok"], tot["live_inside"]))])


def suspicions(ch):
    u"""封 §4 の「先に自分の欠陥を疑う場合」に当たる条件の名前の並び。"""
    out = []
    f = ch[u"fact の数"]
    if f and ch[u"全部決まる fact の数"] == f:
        out.append(u"全部決まる fact がちょうど 100%")
    if ch[u"断らなかった書類の数"] and ch[u"表の外の fact の数"] == 0:
        out.append(u"表の外の fact がちょうど 0")
    if f and 100 * ch[u"表の中の fact の数"] < SUSPECT_ABSENT_FACTS_PCT * f:
        out.append(u"表の中の fact が 50% 未満")
    if ch[u"断った書類の数"] >= SUSPECT_DECLINED:
        out.append(u"断った書類が 6 本以上")
    return out


# ======================================================================================================
# 記録
def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・表の字)が無いか。在れば止める。secret = (表の字の集まり, 要素の名・文脈の名の集まり, docID の並び, EDINET コードの集まり)。"""
    W.check_clean(rec, text, secret)
    if re.search(r"\.(?:htm|xsd|xml|zip)\b", W.HEX_RE.sub(u"", text), re.I):
        raise Stop(u"**記録に file の名の形の字が在る。止める**")


def build_record(docs_dir=None, want=DOCS_WANT, dev_count=DEV_COUNT, progress=None):
    u"""置き場 → (記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    rows, accs = [], []
    names, ctxs = set(), set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        files = None
        try:
            files = doc_texts(p)
            facts = facts_of_files(files)
            acc, reason = count_facts(facts), u""
            for f in facts:
                names.add((f["attrs"].get("name") or u"").split(u":")[-1])
                c = f["attrs"].get("contextRef") or u""
                if re.search(r"[A-Za-z]", c):
                    ctxs.add(c)
        except Refuse as exc:
            acc, reason = None, exc.reason
        rows.append(doc_row(n, acc, reason))
        accs.append(acc)
        if progress is not None:
            progress(u"doc %d/%d(%.1f 秒)" % (n, len(docs), time.time() - t0))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (set(), set(e for e in names if len(e) >= 3) | ctxs, [d[0] for d in docs], ecodes)
    return assemble(rows, accs, W.order_sha256([d[0] for d in docs]), dev_count), secret


def assemble(rows, accs, order_sha, dev_count=DEV_COUNT):
    dev_rows, dev_accs = rows[:dev_count], accs[:dev_count]
    prod_rows, prod_accs = rows[dev_count:], accs[dev_count:]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XA0(受理済みの有報の数の fact の属性は、表の行ごと・列ごとの決めでどれだけ決まるか。人が 1 つずつ書かなければならない欄はどれだけ残るか)(0 USD・engine は読まない・道具は呼ばない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(rows)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"見る属性", list(ATTRS)), (u"空の fact が見る属性", list(NIL_ATTRS)), (u"script の決めの字", list(RULES))])
    rec[u"書類"] = rows
    rec[u"開発の 5 本"] = chunk_of(dev_rows, dev_accs)
    rec[u"本番だけの 62 本"] = chunk_of(prod_rows, prod_accs)
    rec[u"予測の判定に要る数(XA0-1〜XA0-7。本番だけの 62 本のうち断らなかった書類を合わせた fact。当たり・外れは結果の文書で)"] = judged(rec[u"本番だけの 62 本"], prod_accs)
    rec[u"限界"] = list(LIMITS)
    return rec


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(置き場は読まない)。違えば止まる。"""
    rows = rec.get(u"書類")
    if not isinstance(rows, list) or len(rows) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, r in enumerate(rows, 1):
        if r.get(u"番号") != i or list(r) != [u"番号", u"断った", u"断った理由", u"fact の数", u"表の外の fact の数", u"全部決まる fact の数", u"書く欄の数"]:
            raise Stop(u"**記録の書類の形が違う。止める**")
        if r[u"断った"] != bool(r[u"断った理由"]) or r[u"断った"] != (r[u"fact の数"] is None):
            raise Stop(u"**断った書類の形が違う。止める**")
        if not r[u"断った"] and (r[u"表の外の fact の数"] > r[u"fact の数"] or r[u"全部決まる fact の数"] > r[u"fact の数"] - r[u"表の外の fact の数"]):
            raise Stop(u"**書類の数が合わない。止める**")
    for key, part in ((u"開発の 5 本", rows[:dev_count]), (u"本番だけの 62 本", rows[dev_count:])):
        ch = rec[key]
        kept = [r for r in part if not r[u"断った"]]
        pairs = ((u"書類の数", len(part)), (u"断った書類の数", len(part) - len(kept)), (u"断らなかった書類の数", len(kept)), (u"fact の数", sum(r[u"fact の数"] for r in kept)),
                 (u"表の外の fact の数", sum(r[u"表の外の fact の数"] for r in kept)), (u"全部決まる fact の数", sum(r[u"全部決まる fact の数"] for r in kept)),
                 (u"書く欄の数", sum(r[u"書く欄の数"] for r in kept)))
        for k, v in pairs:
            if ch[k] != v:
                raise Stop(u"**塊の数が書類ごとの数と合わない: %s。止める**" % k)
        if sum(ch[u"断った理由ごとの数"].values()) != ch[u"断った書類の数"] or ch[u"表の中の fact の数"] != ch[u"fact の数"] - ch[u"表の外の fact の数"]:
            raise Stop(u"**塊の導き方が合わない。止める**")
        if ch[u"向き A を選んだ表の数"] + ch[u"向き B を選んだ表の数"] != ch[u"fact の在る表の数"] or ch[u"向き B を選んだ表の数"] != ch[u"向き B の方が決まる fact が多かった表の数"]:
            raise Stop(u"**表の向きの数が合わない。止める**")
        if sum(ch[u"書く欄の数(項ごと)"].values()) != ch[u"書く欄の数"] or ch[u"fact の数 × 7"] != 7 * ch[u"fact の数"]:
            raise Stop(u"**書く欄の数の項が合わない。止める**")
        if ch[u"符号が合う fact の数"] + ch[u"符号が合わない fact の数(負と読んだが sign が - でない)"] + ch[u"符号が合わない fact の数(sign が - だが負と読めない)"] != ch[u"表の中の空でない fact の数"]:
            raise Stop(u"**符号の数が合わない。止める**")
        if ch[u"書式が合う fact の数"] + ch[u"書式が合わない fact の数"] != ch[u"表の中の空でない fact の数"]:
            raise Stop(u"**書式の数が合わない。止める**")
        if ch[u"全部決まる fact が %d%% 以上の書類の数" % DOC_FULL_PCT] != sum(1 for r in kept if r[u"fact の数"] > 0 and 100 * r[u"全部決まる fact の数"] >= DOC_FULL_PCT * r[u"fact の数"]):
            raise Stop(u"**全部決まる書類の数が合わない。止める**")
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


def run(root=ROOT, docs=None, out=None, want=DOCS_WANT, say=print, dev_count=DEV_COUNT, progress=None):
    rec, secret = build_record(docs, want, dev_count, progress)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, docs=None, rec_path=None, want=DOCS_WANT, say=print, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査し、置き場から数え直して記録と照らす。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want, dev_count)
    now, secret = build_record(docs, want, dev_count)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(書類 %d)" % now[u"材料"][u"書類の本数"])
    return now


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XB0 の関数。残りの zip は開かない)。"""
    return B.dev_docs(docs_dir, count)


def dev_run(docs_dir=None, say=print, count=DEV_COUNT):
    u"""開発の 5 本だけ(記録は書かない)。(塊, 判定に要る数)。"""
    docs = dev_docs(docs_dir or DOCS_DIR, count)
    rows, accs = [], []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        acc, reason = count_zip(p)
        rows.append(doc_row(n, acc, reason))
        accs.append(acc)
        say(u"doc %d(%.1f 秒): 断った=%s(%s) fact=%s 表の外=%s 全部決まる=%s 書く欄=%s" % (
            n, time.time() - t0, acc is None, reason, rows[-1][u"fact の数"], rows[-1][u"表の外の fact の数"], rows[-1][u"全部決まる fact の数"], rows[-1][u"書く欄の数"]))
    ch = chunk_of(rows, accs)
    say(u"開発の 5 本の合計: %.1f 秒" % (time.time() - t_all))
    say(json.dumps(ch, ensure_ascii=False, indent=2))
    say(json.dumps(judged(ch, accs), ensure_ascii=False, indent=2))
    say(u"先に自分の欠陥を疑う場合に当たったもの: %s" % (u"・".join(suspicions(ch)) or u"なし"))
    return ch, accs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録を検査し、置き場から数え直して照らす")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ数える。記録は書かない")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root, docs=a.docs)
        return
    if a.dev:
        dev_run(docs_dir=a.docs)
        return
    run(root=a.root, docs=a.docs, progress=lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
