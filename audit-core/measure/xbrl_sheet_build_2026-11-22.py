# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md(XS0 ― 行・列の紙から数の fact の属性を作り直し、便 XP0 の組む命令で包みを組むと、道具が読む fact は元と同じになるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。** 道具(Arelle。便 XV0 の道具 P)は呼ぶ(repo の外)。engine(``core/``・``adapters/``)は読まない・変えない。
書類の選び方・表の読み方・文脈の読み方・線の選び方・包みの落とし方と組み方・道具の掛け方・比べ方は前の便(XA0・XA1・XB0・XP0)の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_sheet_build_2026-11-22.py --tool-p <venv の場所>           # 道具を確かめて 67 本を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_sheet_build_2026-11-22.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_sheet_build_2026-11-22.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かない
    python3 measure/xbrl_sheet_build_2026-11-22.py sheet <zip> <紙の folder>        # 紙を作る命令(答えを読む。元の包みを読む)
    python3 -I measure/xbrl_sheet_build_2026-11-22.py attrs <紙の folder> <出す folder>   # 属性を作る命令(答えを読まない。別の process で呼ぶ。引数は folder 2 つだけ)

紙の folder の中身: 便 XP0 の原稿の folder(目次・素の本文・本文の表・タクソノミの表。ただし表 F の ``nonFraction`` の行の ``attrs`` は空)と、紙 ``sheet.json``。
属性を作る命令は、この folder だけを読み、``nonFraction`` の行の ``attrs`` を作った原稿の folder を出す。出した folder を便 XP0 の組む命令に渡す。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 紙の形(JSON): ``format``(書式の類 → ``format`` の値か null。書類に空でない fact が在る類だけ)・``kinds``(``name`` → 期間の種類 ``I``・``D``・``N``)・``tables``(file の名の昇順の番号と表の番号の昇順。
  ``orient``・``end_src``・``member_src``・``elements``(線の番号 → [name, unitRef, decimals, scale])・``ends``(線の番号 → 終わりの日)・``members``(線の番号 → member の組))・
  ``facts``(file の番号と file の中の表 F の番号の昇順。``nil``・``other``・``values``(7 つの値の並び))。「無い」は null。線の番号は 10 進の字(JSON の鍵)。
- 期間の種類は ``I`` 時点・``D`` 期間・``N`` どちらでもない(``forever``)。「その ``name`` の fact が指す文脈の種類の最頻」は ``N`` も数える(並んだら先)。
- 紙の欄の数は紙の file を読み戻して数える: ``format`` の数 + ``kinds`` の数 + 表ごとの 3 + 要素の線 × 4 + ``ends`` の数 + ``members`` の数 + 空の fact の印 + ``other`` の属性の数 + ``values`` を持つ fact × 7。
- 1 つずつ書く fact の (b) は 「便 XA1 の段 2 の全部決まる fact でない」(表の中。便 XA1 の ``choose_combo``・``sign_format_flags`` の値)。(c) の「同じ文脈の定義」は ``id`` が違う定義の数(同じ ``id`` で同じ中身は 1 つ)。
- 空の fact の ``xsi:nil`` の印は ``xsi:nil`` が ``true`` のときだけ。属性を作る命令は、印の在る fact に ``decimals``・``scale``・``format``・``sign`` を付けない(``values`` の fact は ``values`` のとおり)。
- 属性を作る命令の文脈: 表 H の ``resources`` の ``context`` のうち、(期間の種類・終わりの日・member の組)が同じ ``id`` がちょうど 1 つ。同じ ``id`` が別の中身で 2 つ以上なら断る。終わりの日は前後の空白を落とす。
- 属性を作る命令が断る場合(紙に表・線の決めが無い・``name`` の決めが無い・``kinds`` に ``name`` が無い・文脈の ``id`` がちょうど 1 つでない・表の開き閉じが読めない)は、固定の理由で 2 を返す。
- 比べ方 1 の分母(属性が違う fact の率)は、属性を作る命令が出力した書類の fact。断った書類は表 F が同じを偽とし、違う fact の数は数えない。
- 混ぜ物: ``xs0:Changed`` の ``name`` に替えた紙では、期間の種類の決め(``kinds``)に ``xs0:Changed`` を足し、替える前の ``name`` と同じ値にする(足さないと文脈が決まらず「ほかの属性が変わらない」が成り立たない)。
  属性を作る命令は同じ process の中の関数で呼ぶ(道具は呼ばない)。
- 道具の段で「断った」は無い(組んだ後の道具の読みが違うのは 「fact が同じ」の偽)。断りは 紙を作る・属性を作る・組む の 3 つの段。
- 時間: 属性を作る命令・組む命令 1 回目の秒(小数 1 桁)。
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
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_PATH = os.path.abspath(__file__)

CONTEXT_NAME = "_xs0_sheet_context_2026_11_22"
PACK_NAME = "_xs0_pack_build_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


A1 = _load_sibling(CONTEXT_NAME, "xbrl_sheet_context_2026-11-22.py")      # 便 XA1 の script
X = A1.X                                                                    # 便 XA0 の script
P = _load_sibling(PACK_NAME, "xbrl_pack_build_2026-11-22.py")             # 便 XP0 の script
B = X.B                                                                     # 便 XB0 の script
T = P.T                                                                     # 便 XT0 の script
W = A1.W                                                                    # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_SHEET_BUILD_SEAL_2026-11-22.md"
SEAL_COMMIT = "483e3e93"
SCRIPT_REL = "measure/xbrl_sheet_build_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_build_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT
DEV_COUNT = 5

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
TOOL_VERSION = P.TOOL_VERSION
SHA_P = P.SHA_P
YEAR = P.YEAR
TIMEOUT_SEC = P.TIMEOUT_SEC
OUTPUT_KEYS = P.OUTPUT_KEYS
ATTRS = ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format")     # 1 つずつ書く fact の 7 つ
NIL_ATTR = "xsi:nil"
CELLS_PER_TABLE = 3                    # 向き・終わりの日を決める線・member の組を決める線
CELLS_PER_ELEMENT_LINE = 4             # name・unitRef・decimals・scale
CELLS_PER_HAND_FACT = 7
MIX_NAME = "xs0:Changed"
HAND_REASONS = (u"表の外", u"便 XA1 の段 2 で全部決まらない", u"文脈の定義が 2 つ以上", u"期間の種類が name の決めと違う")
STAGES = (u"紙を作る", u"属性を作る", u"組む")
SHEET_FILE = "sheet.json"
EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = P.EXIT_USAGE, P.EXIT_DECLINE, P.EXIT_ERROR
DECLINE_PREFIX = P.DECLINE_PREFIX
SUSPECT_DECLINED = 6
SUSPECT_HAND_BELOW = 3071
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) か None。XS0-7 は「作れた数に等しい」
BOUNDS = collections.OrderedDict([
    ("XS0-1", (60, None)), ("XS0-2", (None, 0.2)), ("XS0-3", (4.8, 6.5)), ("XS0-4", (60, None)), ("XS0-5", (None, 2)), ("XS0-6", (33.6, 38)), ("XS0-7", (u"作れた数", None)), ("XS0-8", (2, 10))])
BOUNDS_UPPER_EXCLUSIVE = ("XS0-3", "XS0-6", "XS0-8")
RULES = [
    u"対象は ix:nonFraction の全部。置き場・行と列の番号・空の fact・符号の規則・書式の類・文脈の読み方・断りの掛け方は便 XA0・便 XA1 のとおり(それらの script の関数を呼ぶ)",
    u"命令は 2 つ: 紙を作る命令(答えを読む)と属性を作る命令(答えを読まない。python3 -I の別の process。引数は folder 2 つだけ)",
    u"紙: 書式の類ごとの format の値・name ごとの期間の種類・fact の在る表ごとの 便 XA1 の段 2 の選びと線ごとの決め・fact ごとの 空の fact の印・そのほかの属性・1 つずつ書く fact の 7 つの値",
    u"1 つずつ書く fact: (a) 表の外 (b) 便 XA1 の段 2 で全部決まる fact でない (c) 文脈と期間の種類・終わりの日・member の組が同じ定義が 2 つ以上 (d) 文脈の期間の種類が name の決めと違う",
    u"属性を作る命令: name・unitRef・decimals・scale は要素の線の決め・contextRef は 期間の種類・終わりの日・member の組が同じ定義の id がちょうど 1 つ・sign は cell の開きタグの終わりから fact までの字に負の字が在れば -・format は字の類ごとの書類の決め",
    u"比べ方 1: 作った attrs と元の attrs が属性の名と値の組として同じか(並びは見ない)。比べ方 2: 作った表 F で便 XP0 の組む命令を掛けた包みを道具で読み、元と fact・鳴り方を比べる",
    u"混ぜ物: 1 つずつ書く fact でない fact が 2 つ以上乗っている要素の線の最初の 1 本の name の決めを xs0:Changed に変えて作り直す。その線の上の 1 つずつ書く fact でない fact の name だけが変わる",
    u"紙の欄の数は紙の file に書いた値を数える。比 = 紙の欄の数 ÷ (fact の数 × 7)。持ち込みは数えない",
]
LIMITS = [
    u"紙は答え(元の書類)から作っている。人が書く紙が正しいかは測っていない。「人が紙を書けば XBRL が作れる」とは読まない。",
    u"持ち込み(素の本文・数の置き場・表 H の全部・文の fact・脚注・提出者別タクソノミの表)はこの便で作っていない。とくに、どの数に fact を付けるか(置き場)と、文脈・単位の定義は元から写している。",
    u"1 つずつ書く fact は 7 つの値を元から写すので、その fact が元と同じになるのは当たり前。",
    u"混ぜ物は 1 本につき 1 つ・name だけ。ほかの決め(終わりの日・member の組・unitRef・書式)を変えた確かめは封の門の作り物だけ。",
    u"道具が読む fact が元と同じでも、EDINET の本物の検査に通ることは言えない(便 XV0 の限界のまま)。",
    u"便 XA0・便 XA1・便 XB0・便 XT0・便 XP0 の限界の全部(答えから作った決め・rowspan を見ない・数の fact だけ・67 本は無作為でない・有報だけ・道具 P は本家の版でない・script は前の便の script を経て engine の module を間接に読み込む)。",
    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
Refuse = X.Refuse
od = collections.OrderedDict
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1
ATTR_LABELS = od((k, u"属性 " + k) for k in B.NUM_ATTRS)

R_PAPER = u"紙に表か線の決めが無い"
R_KIND = u"紙に name の決めか期間の種類が無い"
R_CTX_AMBIG = u"文脈の id がちょうど 1 つに決まらない"
R_ALIGN = u"表 F の fact と数える fact が合わない"
R_SHEET_ERR = u"紙を作る途中の例外"
R_ATTRS_ERR = u"属性を作る途中の例外"
R_FOLDER = u"紙の folder が読めない形"
R_BUILD_OUT = u"出す folder の file の名が目次と合わない"


# ======================================================================================================
# 小さな部品
def mode_val(values):
    u"""最頻の値(並んだら先)。値が無ければ None(「無い」)。"""
    v = X.mode_first(values)
    return None if v == X.NOMODE else v


def jlist(members):
    return [[d, m] for d, m in members]


def jtuple(members):
    return tuple((d, m) for d, m in members)


def blank_row(e):
    u"""表 F の 1 行の写し。``nonFraction`` の ``attrs`` は空にする(紙の folder に元の attrs を置かない)。"""
    return od((k, ({} if (k == "attrs" and e["kind"] == "nonFraction") else (dict(v) if k == "attrs" else v))) for k, v in e.items())


def fact_ids(files):
    u"""[(名, plain, F, H)] → ``nonFraction`` ごとの (file の番号, 表 F の番号) を file の昇順・F の順で。"""
    return [(fi, i) for fi, (_n, _p, F, _h) in enumerate(files) for i, e in enumerate(F) if e["kind"] == "nonFraction"]


# ======================================================================================================
# 紙を作る(答えを読む)
def table_sheet(items, ends, mems, combo):
    u"""表の中の fact の並び・終わりの日の並び・member の組の並び・選ばれた 8 通りの名 → 表の紙(``elements``・``ends``・``members``)。決めは線の上の全部の fact の最頻(並んだら先)。"""
    orient, es, ms = combo[0], combo[1], combo[2]
    keys = [X.line_keys(f, orient) for f in items]
    by_el = od()
    for i, (e, _c) in enumerate(keys):
        by_el.setdefault(e, []).append(i)
    elements = od()
    for e in sorted(by_el):
        ids = by_el[e]
        a = [items[i]["attrs"] for i in ids]
        live = [x for i, x in zip(ids, a) if not items[i]["nil"]]
        elements[str(e)] = [mode_val([x.get("name") for x in a]), mode_val([x.get("unitRef") for x in a]),
                            mode_val([x.get("decimals") for x in live]), mode_val([x.get("scale") for x in live])]

    def decide(src, values):
        by = od()
        for i, (e, c) in enumerate(keys):
            by.setdefault(c if src == "C" else e, []).append(i)
        return od((str(k), mode_val([values[i] for i in by[k]])) for k in sorted(by))
    return od([("orient", orient), ("end_src", es), ("member_src", ms), ("elements", elements),
               ("ends", decide(es, ends)), ("members", od((k, (jlist(v) if v is not None else None)) for k, v in decide(ms, mems).items()))])


def build_sheet(facts, contents, defs, ids):
    u"""元の fact の並び(便 XA0)・文脈の内容の並び(便 XA1)・文脈の定義・(file の番号, 表 F の番号)の並び → (紙, 測りの側の持ち物)。"""
    n = len(facts)
    live = [f for f in facts if not f["nil"]]
    fmt = od()
    for k in X.FORMAT_CLASSES:
        vals = [f["attrs"].get("format") for f in live if X.format_class(f["text"]) == k]
        if vals:
            fmt[k] = mode_val(vals)
    by_name = od()
    for f, c in zip(facts, contents):
        nm = f["attrs"].get("name")
        if nm is not None:
            by_name.setdefault(nm, []).append(c[0])
    kinds = od((nm, X.mode_first(ks)) for nm, ks in by_name.items())
    sf = A1.sign_format_flags(facts)
    tables = od()
    for i, f in enumerate(facts):
        if f["table"] is not None:
            tables.setdefault(f["table"], []).append(i)
    full = set()
    table_rows = []
    lines = od()
    for key in sorted(tables):
        idx = tables[key]
        items = [facts[i] for i in idx]
        ends = [A1.end_of(contents[i]) for i in idx]
        mems = [A1.members_of(contents[i]) for i in idx]
        _d, combo, flags, _lines, _tally = A1.choose_combo(items, ends, mems)
        ts = table_sheet(items, ends, mems, combo)
        row = od([("file", key[0]), ("table", key[1])])
        row.update(ts)
        table_rows.append(row)
        for i, fl in zip(idx, flags):
            if not any(fl) and sf[i]:
                full.add(i)
        orient = combo[0]
        for i, f in zip(idx, items):
            e, _c = X.line_keys(f, orient)
            lines.setdefault((key[0], key[1], e), []).append(i)
    triple_ids = collections.Counter()
    for content in defs.values():
        triple_ids[(content[0], content[2], content[3])] += 1
    reasons = od((r, 0) for r in HAND_REASONS)
    hand = []
    fact_rows = []
    other_facts = 0
    for i, (f, c) in enumerate(zip(facts, contents)):
        ra = f["table"] is None
        rb = (not ra) and i not in full
        rc = triple_ids[(c[0], c[2], c[3])] >= 2
        rd = kinds.get(f["attrs"].get("name")) != c[0]
        for r, hit in zip(HAND_REASONS, (ra, rb, rc, rd)):
            reasons[r] += 1 if hit else 0
        h = ra or rb or rc or rd
        hand.append(h)
        row = od([("file", ids[i][0]), ("index", ids[i][1])])
        if f["nil"]:
            row["nil"] = True
        other = od((k, v) for k, v in sorted(f["attrs"].items()) if k not in ATTRS and k != NIL_ATTR)
        if other:
            row["other"] = other
            other_facts += 1
        if h:
            row["values"] = [f["attrs"].get(k) for k in ATTRS]
        if len(row) > 2:
            fact_rows.append(row)
    sheet = od([("format", fmt), ("kinds", kinds), ("tables", table_rows), ("facts", fact_rows)])
    info = od([("hand", hand), ("reasons", reasons), ("other_facts", other_facts), ("lines", lines), ("fact_count", n)])
    return sheet, info


def sheet_cells(sheet):
    u"""紙に実際に書いた値の数(項ごと)。持ち込みは数えない。"""
    tables = sheet["tables"]
    facts = sheet["facts"]
    out = od()
    out[u"書式の類の決め"] = len(sheet["format"])
    out[u"name ごとの期間の種類"] = len(sheet["kinds"])
    out[u"表ごとの 3"] = CELLS_PER_TABLE * len(tables)
    out[u"要素の線 × 4"] = CELLS_PER_ELEMENT_LINE * sum(len(t["elements"]) for t in tables)
    out[u"終わりの日を決める側の線 × 1"] = sum(len(t["ends"]) for t in tables)
    out[u"member の組を決める側の線 × 1"] = sum(len(t["members"]) for t in tables)
    out[u"空の fact の印"] = sum(1 for f in facts if f.get("nil"))
    out[u"そのほかの属性"] = sum(len(f["other"]) for f in facts if "other" in f)
    out[u"1 つずつ書く fact × 7"] = CELLS_PER_HAND_FACT * sum(1 for f in facts if "values" in f)
    return out


def make_sheet_folder(entries, zip_path, folder):
    u"""紙を作る命令の中身(答えを読む)。元の包みから紙の folder を書く。(紙, 測りの側の持ち物, 元の (名, plain, F, H) の並び, 元の fact の並び)。
    断りは ``Refuse``(便 XA0・便 XA1・便 XP0 の断りを含む)。"""
    try:
        texts = X.doc_texts(zip_path)
        facts = X.facts_of_files(texts)
        defs = A1.context_defs(texts)
        contents = A1.resolve_facts(facts, defs)
        files, names, tables = P.peel_tables(entries)
    except P.Refuse as exc:
        raise Refuse(exc.reason)
    ids = fact_ids(files)
    if len(ids) != len(facts):
        raise Refuse(R_ALIGN)
    sheet, info = build_sheet(facts, contents, defs, ids)
    blank = [(n, p, [blank_row(e) for e in F], H) for n, p, F, H in files]
    try:
        P.write_folder(folder, blank, names, tables)
        P.write_bytes(os.path.join(folder, SHEET_FILE), P.jdump(sheet))
    except Exception:                                      # noqa: BLE001
        shutil.rmtree(folder, ignore_errors=True)
        raise Refuse(u"folder に書けない形")
    return sheet, info, files, facts


def sheet_main(args):
    u"""紙を作る命令。引数は zip と folder。"""
    if len(args) != 2:
        print(u"使い方: sheet <zip> <紙の folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        make_sheet_folder(B.load_package(args[0]), args[0], args[1])
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


# ======================================================================================================
# 属性を作る(答えを読まない。紙の folder だけを読む)
def read_context(r):
    u"""表 H の ``context`` 1 つ → (id, (期間の種類, 終わりの日, member の組))。便 XA1 の読み方と同じ(日は前後の空白を落とす)。"""
    per = r["period"]
    names = [k for k, _v in per]
    if names == ["xbrli:instant"]:
        kind, end = A1.KIND_INSTANT, per[0][1].strip()
    elif names == ["xbrli:startDate", "xbrli:endDate"]:
        kind, end = A1.KIND_DURATION, per[1][1].strip()
    else:
        kind, end = A1.KIND_NONE, u""
    members = tuple(sorted((d or u"", m.strip()) for d, m in r["members"]))
    return r["id"], (kind, end, members)


def context_index(files):
    u"""[(名, plain, F, H)] → {(期間の種類, 終わりの日, member の組): [id の昇順]}。同じ id で中身が違えば ``Refuse``。"""
    defs = {}
    for _n, _p, _F, H in files:
        if H is None:
            continue
        for r in H["resources"]:
            if r.get("type") != "context":
                continue
            cid, content = read_context(r)
            if cid in defs and defs[cid] != content:
                raise Refuse(A1.R_CTX_DUP)
            defs[cid] = content
    idx = {}
    for cid, content in defs.items():
        idx.setdefault(content, []).append(cid)
    return dict((k, sorted(v)) for k, v in idx.items())


def table_lookup(sheet):
    out = {}
    for t in sheet["tables"]:
        out[(t["file"], t["table"])] = t
    return out


def values_attrs(row):
    u"""紙の 1 つずつ書く fact の 7 つの値 → attrs(「無い」は付けない)。"""
    return dict((k, v) for k, v in zip(ATTRS, row["values"]) if v is not None)


def decided_attrs(f, t, sheet, ctx_idx, row):
    u"""1 つずつ書く fact でない fact(表の中)の attrs。紙の表の決めと、cell の位置と、fact の中の字だけから作る。"""
    orient = t["orient"]
    e, c = X.line_keys(f, orient)
    el = t["elements"].get(str(e))
    if el is None:
        raise Refuse(R_PAPER)
    name, unit, dec, scale = el
    if name is None:
        raise Refuse(R_KIND)
    kind = sheet["kinds"].get(name)
    end = t["ends"].get(str(c if t["end_src"] == "C" else e), u"\x00無い")
    mem = t["members"].get(str(c if t["member_src"] == "C" else e), u"\x00無い")
    if kind is None:
        raise Refuse(R_KIND)
    if end == u"\x00無い" or end is None or mem == u"\x00無い" or mem is None:
        raise Refuse(R_PAPER)
    ids = ctx_idx.get((kind, end, jtuple(mem)), [])
    if len(ids) != 1:
        raise Refuse(R_CTX_AMBIG)
    attrs = {"name": name, "contextRef": ids[0]}
    if unit is not None:
        attrs["unitRef"] = unit
    if row.get("nil"):
        attrs[NIL_ATTR] = "true"
        return attrs
    if dec is not None:
        attrs["decimals"] = dec
    if scale is not None:
        attrs["scale"] = scale
    if X.reads_negative(f["between"]):
        attrs["sign"] = "-"
    fm = sheet["format"].get(X.format_class(f["text"]))
    if fm is not None:
        attrs["format"] = fm
    return attrs


def attrs_tables(folder):
    u"""紙の folder だけを読み、(目次, [(名, plain, F, H)] の F の ``nonFraction`` の attrs を作ったもの) を返す。元の attrs は folder に無い。断りは ``Refuse``。"""
    try:
        index = P.jload(P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
        sheet = P.jload(P.read_bytes(os.path.join(folder, SHEET_FILE)))
        files = P.load_htm_tables(folder, index)
    except Refuse:
        raise
    except Exception:                                      # noqa: BLE001
        raise Refuse(R_FOLDER)
    ctx_idx = context_index(files)
    tabs = table_lookup(sheet)
    rows = dict(((r["file"], r["index"]), r) for r in sheet["facts"])
    out = []
    for fi, (name, plain, F, H) in enumerate(files):
        F2 = [od((k, (dict(v) if k == "attrs" else v)) for k, v in e.items()) for e in F]
        idx = [i for i, e in enumerate(F) if e["kind"] == "nonFraction"]
        cells = X.place_positions(plain, [F[i]["start"] for i in idx]) if idx else []
        for i, cell in zip(idx, cells):
            e = F[i]
            row = rows.get((fi, i), {})
            if "values" in row:
                attrs = values_attrs(row)
                if row.get("nil"):
                    attrs[NIL_ATTR] = "true"
            else:
                if cell is None:
                    raise Refuse(R_PAPER)
                t = tabs.get((fi, cell[0]))
                if t is None:
                    raise Refuse(R_PAPER)
                f = od([("row", cell[1]), ("col", cell[2]), ("between", X.strip_tags(plain[cell[3]:e["start"]])),
                        ("text", X.strip_tags(plain[e["start"]:e["end"]]).strip())])
                attrs = decided_attrs(f, t, sheet, ctx_idx, row)
            for k, v in row.get("other", {}).items():
                attrs[k] = v
            F2[i]["attrs"] = dict(sorted(attrs.items()))
        out.append((name, plain, F2, H))
    return index, out


def write_attrs_folder(folder, out):
    u"""属性を作る命令の中身。紙の folder → 出す folder(便 XP0 の原稿の folder と同じ形)。"""
    index, files = attrs_tables(folder)
    os.makedirs(out)
    P.write_bytes(os.path.join(out, P.INDEX_FILE), P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
    P.write_bytes(os.path.join(out, index["taxonomy"]["file"]), P.read_bytes(os.path.join(folder, P.safe_local(index["taxonomy"]["file"]))))
    for item, (_n, plain, F, H) in zip(index["htm"], files):
        P.write_bytes(os.path.join(out, P.safe_local(item["text"])), P.read_bytes(os.path.join(folder, P.safe_local(item["text"]))))
        P.write_bytes(os.path.join(out, P.safe_local(item["tables"])), P.jdump(od([("F", F), ("H", H)])))
    return index


def attrs_main(args):
    u"""属性を作る命令。引数は folder 2 つだけ(元の包みの path を受け取れない)。終わりの値: 0・64(使い方)・2(断り)・1(例外)。"""
    if len(args) != 2:
        print(u"使い方: attrs <紙の folder> <出す folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        write_attrs_folder(args[0], args[1])
    except (Refuse, P.Refuse) as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


def attrs_command(folder, out):
    return [sys.executable, "-I", SCRIPT_PATH, "attrs", folder, out]


def exec_attrs(folder, out, cwd, proc=None):
    u"""属性を作る命令を別の process で 1 回。(成功か, 断りの理由, 秒)。"""
    proc = proc or P.run_process
    t0 = time.time()
    rc, err, timed_out = proc(attrs_command(folder, out), cwd, TIMEOUT_SEC)
    secs = time.time() - t0
    if timed_out:
        return False, u"属性を作る命令が時間の上限を超えた", secs
    if rc != 0:
        reason = P.decline_reason(err)
        return False, (reason if reason is not None else u"属性を作る命令が 0 でない終わりの値で終わった"), secs
    return True, u"", secs


# ======================================================================================================
# 比べ方 1・混ぜ物
def leak_problems(folder):
    u"""紙の folder の本文の表の ``nonFraction`` の行に属性が在れば、その数(元の attrs が在る)。"""
    index = P.jload(P.read_bytes(os.path.join(folder, P.INDEX_FILE)))
    n = 0
    for item in index["htm"]:
        tab = P.jload(P.read_bytes(os.path.join(folder, item["tables"])))
        n += sum(1 for e in tab["F"] if e["kind"] == "nonFraction" and e["attrs"])
    return n


def compare_attrs(orig_files, new_files):
    u"""元と作った [(名, plain, F, H)] → (違う fact の数, {属性の名: 違う fact の数})。属性の名と値の組が同じか(並びは見ない)。"""
    diff = 0
    by = collections.Counter()
    for (_n, _p, F, _h), (_n2, _p2, F2, _h2) in zip(orig_files, new_files):
        for e, e2 in zip(F, F2):
            if e["kind"] != "nonFraction":
                continue
            a, b = e["attrs"], e2["attrs"]
            if a != b:
                diff += 1
                for k in set(a) | set(b):
                    if a.get(k) != b.get(k):
                        by[k] += 1
    return diff, by


def mix_target(info):
    u"""混ぜ物の当て先: 1 つずつ書く fact でない fact が 2 つ以上乗っている要素の線のうち最初の 1 本(file の番号・表の番号・線の番号の昇順)。(file, table, line, [fact の番号]) か None。"""
    hand = info["hand"]
    for key in sorted(info["lines"]):
        free = [i for i in info["lines"][key] if not hand[i]]
        if len(free) >= 2:
            return key[0], key[1], key[2], free
    return None


def mixed_sheet(sheet, target):
    u"""紙の写しの、当て先の線の name の決めを ``MIX_NAME`` に替えたもの。``kinds`` に ``MIX_NAME`` を足す(替える前の name と同じ値)。"""
    fi, ti, line, _free = target
    out = json.loads(json.dumps(sheet), object_pairs_hook=od)
    for t in out["tables"]:
        if t["file"] == fi and t["table"] == ti:
            old = t["elements"][str(line)][0]
            t["elements"][str(line)][0] = MIX_NAME
            if old is not None and old in out["kinds"]:
                out["kinds"][MIX_NAME] = out["kinds"][old]
    return out


def mix_effect(folder, sheet, info, ids, clean_files, scratch):
    u"""混ぜ物。(作れたか, 効いたか)。道具は呼ばない。紙の folder の写しの紙だけを替え、同じ process の中で属性を作る関数を呼ぶ。"""
    target = mix_target(info)
    if target is None:
        return False, False
    copy = os.path.join(scratch, "mixed_sheet")
    shutil.copytree(folder, copy)
    P.write_bytes(os.path.join(copy, SHEET_FILE), P.jdump(mixed_sheet(sheet, target)))
    try:
        _ix, mixed = attrs_tables(copy)
    except (Refuse, P.Refuse):
        return True, False
    free = set(ids[i] for i in target[3])
    changed = 0
    for fi, ((_n, _p, F, _h), (_n2, _p2, F2, _h2)) in enumerate(zip(clean_files, mixed)):
        for i, (e, e2) in enumerate(zip(F, F2)):
            if e["kind"] != "nonFraction":
                continue
            if (fi, i) in free:
                want = dict(e["attrs"])
                want["name"] = MIX_NAME
                if e2["attrs"] != want:
                    return True, False
                changed += 1
            elif e["attrs"] != e2["attrs"]:
                return True, False
    return True, changed == len(free)


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
    rec[u"紙の欄の数(項ごと)"] = None
    rec[u"紙の欄の数"] = None
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
    rec[u"混ぜ物"] = od([(u"作れた", False), (u"効いた", False)])
    rec[u"属性を作る命令の秒"] = None
    rec[u"組む命令の秒"] = None
    rec[u"組み直しの 1 回"] = None
    return rec


def declined_rec(rec, stage, reason):
    rec[u"断った"], rec[u"断った段"], rec[u"断った理由"] = True, stage, reason
    rec[u"組めた"] = False
    return rec


def measure_one(tool, zip_path, tmp_root=None, runner=None, proc=None):
    u"""書類 1 本。書類ごとの数。紙を作る → 属性を作る(別の process)→ 比べ方 1 → 混ぜ物 → 組む(別の process・2 回)→ 比べ方 2(道具で元と組み直しを 1 回ずつ)。"""
    entries = B.load_package(zip_path)
    rec = new_doc_rec()
    d = tempfile.mkdtemp(prefix="xs0_", dir=tmp_root)
    try:
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        folder = os.path.join(d, "sheet")
        try:
            sheet, info, files, facts = make_sheet_folder(entries, zip_path, folder)
        except Refuse as exc:
            return declined_rec(rec, STAGES[0], exc.reason)
        except Exception:                                  # noqa: BLE001
            return declined_rec(rec, STAGES[0], R_SHEET_ERR)
        ids = fact_ids(files)
        back = P.jload(P.read_bytes(os.path.join(folder, SHEET_FILE)))
        cells = sheet_cells(back)
        if leak_problems(folder):
            raise Stop(u"**紙の folder に元の attrs が在る(自分の欠陥)。止める**")
        rec[u"fact の数"] = info["fact_count"]
        rec[u"1 つずつ書く fact の数"] = sum(1 for h in info["hand"] if h)
        rec[u"1 つずつ書く fact の理由(重ねて数える)"] = od(info["reasons"])
        rec[u"そのほかの属性を持つ fact の数"] = info["other_facts"]
        rec[u"紙の欄の数(項ごと)"] = cells
        rec[u"紙の欄の数"] = sum(cells.values())
        out1 = os.path.join(d, "attrs1")
        ok, reason, secs = exec_attrs(folder, out1, cwd, proc)
        rec[u"属性を作る命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[1], reason)
        rec[u"属性を作れた"] = True
        out_index = P.jload(P.read_bytes(os.path.join(out1, P.INDEX_FILE)))
        new_files = P.load_htm_tables(out1, out_index)
        diff, by = compare_attrs(files, new_files)
        rec[u"attrs が違う fact の数"] = diff
        rec[u"表 F が同じ"] = diff == 0
        for k, n in by.items():
            rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"][ATTR_LABELS.get(k, u"属性 そのほか")] = rec[u"attrs が違う属性ごとの fact の数(重ねて数える)"].get(ATTR_LABELS.get(k, u"属性 そのほか"), 0) + n
        made, effective = mix_effect(folder, sheet, info, ids, files, d)
        rec[u"混ぜ物"] = od([(u"作れた", made), (u"効いた", effective)])
        bout1 = os.path.join(d, "built1")
        ok, reason, secs = P.exec_build(out1, bout1, cwd, proc)
        rec[u"組む命令の秒"] = round(secs, 1)
        if not ok:
            return declined_rec(rec, STAGES[2], reason)
        tree = P.read_tree(bout1)
        if set(tree) != P.expected_names(out_index):
            return declined_rec(rec, STAGES[2], R_BUILD_OUT)
        rec[u"組めた"] = True
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
    out[u"書類の数"] = len(entries)
    out[u"断った書類の数"] = sum(declined.values())
    out[u"断った段ごとの数"] = od((s, declined[s]) for s in STAGES)
    out[u"断った理由ごとの数"] = od((u"%s: %s" % (s, r), n) for (s, r), n in sorted(reasons.items()))
    out[u"紙を作れた書類の数"] = len(made)
    out[u"fact の数(紙を作れた書類)"] = facts
    out[u"1 つずつ書く fact の数"] = sum(e[u"1 つずつ書く fact の数"] for e in made)
    out[u"1 つずつ書く fact の理由ごとの数(重ねて数える)"] = hand_reasons
    out[u"そのほかの属性を持つ fact の数"] = sum(e[u"そのほかの属性を持つ fact の数"] for e in made)
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
    out[u"混ぜ物を作れた書類の数"] = sum(1 for e in entries if e[u"混ぜ物"][u"作れた"])
    out[u"混ぜ物が効いた書類の数"] = sum(1 for e in entries if e[u"混ぜ物"][u"効いた"])
    out[u"紙の欄の数(項ごと)"] = cells
    out[u"紙の欄の数"] = cell_total
    out[u"fact の数 × 7"] = facts * 7
    out[u"紙の欄の比"] = od([(u"数", cell_total), (u"分母", facts * 7), (u"%", pct1(cell_total, facts * 7))])
    out[u"属性を作る命令の秒の合計"] = round(sum(e[u"属性を作る命令の秒"] for e in entries if e[u"属性を作る命令の秒"] is not None), 1)
    out[u"組む命令の秒の合計"] = round(sum(e[u"組む命令の秒"] for e in entries if e[u"組む命令の秒"] is not None), 1)
    return out


CELL_KEYS = (u"書式の類の決め", u"name ごとの期間の種類", u"表ごとの 3", u"要素の線 × 4", u"終わりの日を決める側の線 × 1", u"member の組を決める側の線 × 1", u"空の fact の印",
             u"そのほかの属性", u"1 つずつ書く fact × 7")


def totals_of(per_doc, dev_count=DEV_COUNT):
    return od([(u"開発の 5 本", group_totals(per_doc[:dev_count])), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(per_doc[dev_count:])), (u"全部", group_totals(per_doc))])


def rate(n, d):
    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])


def judged(tot):
    u"""封 §4 の判定に要る数(丸める前の整数と %)。当たり・外れは書かない。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    return od([
        (u"XS0-1 表 F が同じ書類", od([(u"書類", prod[u"表 F が同じ書類の数"]), (u"分母", prod[u"書類の数"])])),
        (u"XS0-2 attrs が違う fact / fact(属性を作れた書類)", rate(prod[u"attrs が違う fact の数"], prod[u"fact の数(属性を作れた書類)"])),
        (u"XS0-3 1 つずつ書く fact / fact(紙を作れた書類)", rate(prod[u"1 つずつ書く fact の数"], prod[u"fact の数(紙を作れた書類)"])),
        (u"XS0-4 道具が読む fact が同じ書類", od([(u"書類", prod[u"fact が同じ書類の数"]), (u"分母", prod[u"書類の数"])])),
        (u"XS0-5 属性を作る命令が断った書類", od([(u"書類", prod[u"断った段ごとの数"][STAGES[1]]), (u"分母", prod[u"書類の数"])])),
        (u"XS0-6 紙の欄の数 / fact の数 × 7", prod[u"紙の欄の比"]),
        (u"XS0-7 混ぜ物が効いた書類 / 作れた書類", od([(u"書類", prod[u"混ぜ物が効いた書類の数"]), (u"分母", prod[u"混ぜ物を作れた書類の数"])])),
        (u"XS0-8 そのほかの属性を持つ fact / fact(紙を作れた書類)", rate(prod[u"そのほかの属性を持つ fact の数"], prod[u"fact の数(紙を作れた書類)"]))])


def suspicions(ch, whole=True):
    u"""封 §4 の「先に自分の欠陥を疑う場合」に当たる条件の名前の並び。``whole`` が偽(開発の 5 本)なら、62 本の数(3071)との比べは掛けない。"""
    out = []
    if whole and ch[u"紙を作れた書類の数"] and ch[u"1 つずつ書く fact の数"] < SUSPECT_HAND_BELOW:
        out.append(u"1 つずつ書く fact が 3071 より少ない")
    if ch[u"属性を作れた書類の数"] and ch[u"表 F が同じ書類の数"] < ch[u"fact が同じ書類の数"]:
        out.append(u"表 F が違うのに道具が読む fact が同じ書類が在る(違う属性が道具に見えない所を読む)")
    if ch[u"断った段ごとの数"][STAGES[1]] >= SUSPECT_DECLINED or ch[u"断った書類の数"] >= SUSPECT_DECLINED:
        out.append(u"断った書類が 6 本以上")
    if ch[u"混ぜ物を作れた書類の数"] < ch[u"書類の数"] and ch[u"書類の数"] - ch[u"混ぜ物を作れた書類の数"] >= SUSPECT_DECLINED:
        out.append(u"混ぜ物を作れなかった書類が 6 本以上")
    return out


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    return P.check_tool(tool, runner, sha_reader, want_version, want_sha)


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XB0 の関数。残りの zip は開かない)。"""
    return B.dev_docs(docs_dir, count)


def doc_secret_strings(zip_path):
    u"""記録に書かない字(要素の局所名・文脈の名・member の名)。書類を読むだけ。読めなければ空。"""
    try:
        texts = X.doc_texts(zip_path)
        facts = X.facts_of_files(texts)
    except Exception:                                      # noqa: BLE001
        return set()
    try:
        defs = A1.context_defs(texts)
    except Exception:                                      # noqa: BLE001
        defs = {}
    return A1.secret_strings(facts, defs)


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
    rec[u"step"] = u"XS0(行・列の紙から数の fact の属性を作り直し、便 XP0 の組む命令で包みを組むと、道具が読む fact は元と同じになるか)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"時間の上限(秒)", TIMEOUT_SEC), (u"script の決めの字", list(RULES))])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XS0-1〜XS0-8。本番だけの 62 本。当たり・外れは結果の文書で)"] = judged(tot)
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字・紙の中身)が無いか。在れば止める。"""
    X.check_clean(rec, text, secret)
    if A1.DATE_FORM_RE.search(W.HEX_RE.sub(u"", text)):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


DOC_KEYS = [u"番号", u"断った", u"断った段", u"断った理由", u"fact の数", u"1 つずつ書く fact の数", u"1 つずつ書く fact の理由(重ねて数える)", u"そのほかの属性を持つ fact の数",
            u"紙の欄の数(項ごと)", u"紙の欄の数", u"属性を作れた", u"表 F が同じ", u"attrs が違う fact の数", u"attrs が違う属性ごとの fact の数(重ねて数える)", u"組めた",
            u"2 回組んで同じ", u"タクソノミが同じ", u"fact が同じ", u"鳴り方が同じ", u"全部同じ", u"混ぜ物", u"属性を作る命令の秒", u"組む命令の秒", u"組み直しの 1 回"]


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
        if d[u"fact の数"] is not None:
            if list(d[u"紙の欄の数(項ごと)"]) != list(CELL_KEYS) or d[u"紙の欄の数"] != sum(d[u"紙の欄の数(項ごと)"].values()):
                raise Stop(u"**紙の欄の数の項が合わない。止める**")
            if list(d[u"1 つずつ書く fact の理由(重ねて数える)"]) != list(HAND_REASONS) or not (0 <= d[u"1 つずつ書く fact の数"] <= d[u"fact の数"]):
                raise Stop(u"**1 つずつ書く fact の数が合わない。止める**")
            if d[u"1 つずつ書く fact の数"] > sum(d[u"1 つずつ書く fact の理由(重ねて数える)"].values()) or d[u"紙の欄の数(項ごと)"][u"1 つずつ書く fact × 7"] != 7 * d[u"1 つずつ書く fact の数"]:
                raise Stop(u"**1 つずつ書く fact の数が合わない。止める**")
        if d[u"混ぜ物"][u"効いた"] and not d[u"混ぜ物"][u"作れた"]:
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
        say(u"doc %d(%.0f 秒): 断った=%s(%s・%s) fact=%s 1つずつ=%s 紙の欄=%s 表F同じ=%s attrs違い=%s 組めた=%s fact同じ=%s 鳴り方=%s 2回=%s 混ぜ物=%s 属性秒=%s 組む秒=%s" % (
            n, time.time() - t0, r[u"断った"], r[u"断った段"], r[u"断った理由"], r[u"fact の数"], r[u"1 つずつ書く fact の数"], r[u"紙の欄の数"], r[u"表 F が同じ"], r[u"attrs が違う fact の数"],
            r[u"組めた"], r[u"fact が同じ"], r[u"鳴り方が同じ"], r[u"2 回組んで同じ"], dict(r[u"混ぜ物"]), r[u"属性を作る命令の秒"], r[u"組む命令の秒"]))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    tot = group_totals(per)
    say(json.dumps(tot, ensure_ascii=False, indent=2))
    say(u"先に自分の欠陥を疑う場合に当たったもの: %s" % (u"・".join(suspicions(tot, whole=False)) or u"なし"))
    return per


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "attrs":
        sys.exit(attrs_main(argv[1:]))
    if argv and argv[0] == "sheet":
        sys.exit(sheet_main(argv[1:]))
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
