# -*- coding: utf-8 -*-
u"""封 docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md(XA1 ― 行・列の紙に収まらなかった fact の文脈を、終わりの日と member の組に分けて別々の線で決めると、どれだけ収まるか)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。通信しない。道具(Arelle)も呼ばない。** engine(``core/``・``adapters/``)は読まない・変えない。書類の選び方・包みの開き方・表の読み方・線の決め・数え方は
前の便(XA0)の script の関数を importlib で呼ぶ(写さない・変えない)。

    python3 measure/xbrl_sheet_context_2026-11-22.py            # 67 本を数えて記録 fixtures/xbrl/cd8/sheet_context_2026-11-22.json を書く(5 本と 62 本を別の塊で)。本番は 1 回
    python3 measure/xbrl_sheet_context_2026-11-22.py --check    # 記録の形・合計を検査し、置き場から数え直して記録と照らす
    python3 measure/xbrl_sheet_context_2026-11-22.py --dev      # 開発の 5 本だけ(置き場の並びの頭の 5 本の zip だけ開く)。記録は書かず stdout に数

**段 0 が便 XA0 の記録と全部の数で同じでなければ止まる(rc が 0 でない)。** 本番・--check・--dev のどれも、数え終えた直後にこの照らしを通る。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 文脈の定義の読み方: ``<局所名が context の要素>`` の開きタグから、次の閉じタグまでの中身を読む。``<!-- -->`` の中は読まない。自己閉じの ``context`` は定義に数えない。``id`` は属性名がちょうど ``id``(``xml:id`` でない)。
  期間: ``instant`` が在れば時点・無くて ``endDate`` が在れば期間・どちらも無ければ「なし」(終わりの日は空の字・断らない)。日の字は前後の空白を落とすだけ(日付として直さない)。
  member: ``explicitMember`` と ``typedMember`` の (``dimension`` の字, 中身の字) の組。``typedMember`` の中身はタグを除いて前後の空白を落とす。両方を 1 つの組に並べ、字の順に並べる。
- 同じ ``id`` の定義が 2 つ以上在り中身(期間の種類・始まり・終わり・member の組)が同じでなければ「断った」。封の字は「2 つ以上の file に在るとき」だが、同じ file の中の重なりも同じ扱いにした(どちらを使うか決められないため)。
- ``contextRef`` の属性が無い・指す ``id`` の定義が無い fact が 1 つでも在る書類は「断った」。
- 段 0 の数は便 XA0 の ``count_facts`` が返す数のまま。便 XA0 の断りで断った書類は、この便でも同じ理由で断る。この便が足す断り(文脈)は、段 0 の照らしの母集団には入れる(便 XA0 が数えた書類の全部)。
- 段 1 は fact の ``contextRef`` を (終わりの日, member の組) の対に置き換えた fact の並びを、便 XA0 の ``count_facts`` に渡して数える。
- 段 2 の表ごとの 8 通り: 向き(A・B)× 終わりの日の線(文脈の線 C・要素の線 E)× member の組の線(C・E)。決まる fact の数が多いもの(同数は ACC・ACE・AEC・AEE・BCC・BCE・BEC・BEE の先)。
  ``name``・``unitRef``・``decimals``・``scale`` の決めは便 XA0 の ``mismatches`` の値を使う(要素の線)。終わりの日・member の組の決めは、選んだ側の線の上の全部の fact(空の fact も含む)の最頻の値(並んだら線の上で先の fact の値)。
- 段 2 の全部決まる fact: 表の決めで決まる fact のうち、空でない fact は便 XA0 と同じ符号・書式の規則を満たすもの(書類の書式の最頻は便 XA0 と同じ関数で数える)。
- 書く欄の数(段 2): 表ごとに 3 + 要素の線の数 × 4 + 終わりの日を決める側の線の数 + member の組を決める側の線の数。それに、書類で現れた書式の類の数・空の fact の数・表の中で全部決まらない fact の数 × 7・表の外の fact の数 × 7。
- 期間の種類が 2 つ在る ``name``: 書類の中で、時点の文脈と期間の文脈の両方を指す fact が在る ``name``(属性の字のまま)。期間の種類「なし」の文脈は数えない。
- 始まりの日が違う期間の文脈を指す fact: 期間の文脈を (終わりの日, member の組) で束ね、束の中の始まりの日が 2 種類以上なら、その束の文脈(同じ中身の別の ``id`` も含む)を指す fact の数。
- ``--dev`` と ``--check`` の便 XA0 の記録は ``fixtures/xbrl/cd8/sheet_wall_2026-11-22.json``。
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

PRIOR_NAME = "_xa1_sheet_wall_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


X = _load_sibling(PRIOR_NAME, "xbrl_sheet_wall_2026-11-22.py")         # 便 XA0 の script
W = X.W                                                                  # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_SHEET_CONTEXT_SEAL_2026-11-22.md"
SEAL_COMMIT = "d46f92aa"
SCRIPT_REL = "measure/xbrl_sheet_context_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/sheet_context_2026-11-22.json"
PRIOR_RECORD_REL = "fixtures/xbrl/cd8/sheet_wall_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT
DEV_COUNT = 5

# ---- 封 §1 の決めごと(字で留める。封の門が封の字と照らす)
ORIENTS = ("A", "B")
LINE_SRCS = ("C", "E")                  # 終わりの日・member の組を決める線: 文脈の線 C・要素の線 E
COMBOS = tuple(o + e + m for o in ORIENTS for e in LINE_SRCS for m in LINE_SRCS)
CELL_PER_TABLE = 3                      # 向き・終わりの日を決める線・member の組を決める線
CELL_PER_ELEMENT_LINE = 4               # name・unitRef・decimals・scale
CELL_PER_END_LINE = 1
CELL_PER_MEMBER_LINE = 1
CELLS_PER_FACT = X.CELLS_PER_FACT       # 7
DOC_FULL_PCT = 90
SUSPECT_DECLINED = 6
KIND_INSTANT, KIND_DURATION, KIND_NONE = "I", "D", "N"
STAGE_LABELS = (u"段 0", u"段 1", u"段 2")
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限) の % か 数。XA1-4 は文字の予測なので None
BOUNDS = collections.OrderedDict([
    ("XA1-1", (82, 92)), ("XA1-2", (90, None)), ("XA1-3", (None, 3500)), ("XA1-4", None), ("XA1-5", (31, None)), ("XA1-6", (25, 38)), ("XA1-7", (None, 0.5)), ("XA1-8", (15, None))])
BOUNDS_UPPER_EXCLUSIVE = ("XA1-1", "XA1-6")
RULES = [
    u"書類・対象の fact・置き場・行と列の番号・空の fact・符号の規則・書式の規則・断りの掛け方は便 XA0 のとおり(便 XA0 の script の関数を呼ぶ)",
    u"文脈の定義は局所名が context の要素。id・期間(instant か startDate と endDate)・explicitMember の dimension と中身の字の組。同じ id で中身が違う・定義が無い contextRef は断る",
    u"typedMember を持つ文脈を指す fact が在っても断らず、その member は dimension の字と中身の字(タグを除く)の組として扱う",
    u"終わりの日は instant の日か endDate の日。member の組は dimension と member の字の組を字の順に並べたもの。期間の種類と始まりの日は線で決めない(数えるだけ)",
    u"段 0 は便 XA0 と同じ。段 0 の全部の数が便 XA0 の記録と同じでなければ止める",
    u"段 1 は contextRef の字の代わりに (終わりの日, member の組) の対を文脈の線が決める。ほかは段 0 と同じ(向きの選び方も)",
    u"段 2 は表ごとに 向き(A・B)× 終わりの日の線(文脈の線・要素の線)× member の組の線(文脈の線・要素の線)の 8 通りを試し、決まる fact が最も多いものを選ぶ。同じなら 向き A・終わりの日は文脈の線・member の組は文脈の線の順に先",
    u"線の決めは線の上の fact の最頻の値。並んだら線の上で先に現れた fact の値",
    u"書く欄の数(段 2)は 表ごとに 3 + 要素の線 × 4 + 終わりの日を決める側の線の数 + member の組を決める側の線の数。それに 書式の類の数 + 空の fact + 表の中で全部決まらない fact × 7 + 表の外の fact × 7",
]
LIMITS = [
    u"線の決めは答え(その線の上の fact の最頻の値)から作っている。人が紙に書く値が正しいかは測っていない。「人が書く量はこれだけで済む」とは読まない。8 通りからの選びも答えを見て選んでいる(人は表ごとに選びを書かなければならない)。",
    u"便 XA0 の限界の全部: 線の上の fact が 1 つだけなら必ず決まる・rowspan を見ない・数の fact だけ・答えから作った決め・67 本は無作為でない・有報だけ。",
    u"段 2 は表ごとに 8 通りから良いものを選ぶので、段 0・段 1 より決まる fact が増えるのは作りから当たり前。増えた量だけを読む。",
    u"字の比べなので、同じ member を別の字で書いた文脈は別の member に数える。",
    u"終わりの日・member の組から文脈の id と定義を作ること、期間の種類と始まりの日を要素から決めることは、この便では作っていない(数えただけ)。",
    u"62 本は便 XA0 で数えた書類で、段 2 の決めは便 XA0 の結果を見てから作った。未使用の書類での確かめではない。",
    u"「XBRL を作れる」「専用の道具が要らない」は、この便からは言えない。"]

Stop = W.Stop
Refuse = X.Refuse
od = collections.OrderedDict
sha256_file = W.sha256_file
dumps = W.dumps
pct1 = W.pct1

R_CTX_DUP = u"同じ id で中身の違う文脈が在る"
R_CTX_MISSING = u"contextRef の指す定義が無い"

NAME = r"[\w.\-]+"
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
CTX_OPEN_RE = re.compile(r"<(?:%s:)?context(?=[\s>/])([^>]*)>" % NAME)
CTX_CLOSE_RE = re.compile(r"</(?:%s:)?context\s*>" % NAME)
ID_RE = re.compile(r"""(?<![\w:.\-])id\s*=\s*(?:"([^"]*)"|'([^']*)')""")
INSTANT_RE = re.compile(r"<(?:%s:)?instant\s*>(.*?)</(?:%s:)?instant\s*>" % (NAME, NAME), re.S)
START_RE = re.compile(r"<(?:%s:)?startDate\s*>(.*?)</(?:%s:)?startDate\s*>" % (NAME, NAME), re.S)
END_RE = re.compile(r"<(?:%s:)?endDate\s*>(.*?)</(?:%s:)?endDate\s*>" % (NAME, NAME), re.S)
EXPLICIT_RE = re.compile(r"<(?:%s:)?explicitMember(?=[\s>])([^>]*)>(.*?)</(?:%s:)?explicitMember\s*>" % (NAME, NAME), re.S)
TYPED_RE = re.compile(r"<(?:%s:)?typedMember(?=[\s>])([^>]*)>(.*?)</(?:%s:)?typedMember\s*>" % (NAME, NAME), re.S)
DIM_RE = re.compile(r"""(?<![\w:.\-])dimension\s*=\s*(?:"([^"]*)"|'([^']*)')""")
DATE_FORM_RE = re.compile(r"(?<![0-9A-Za-z_])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")


# ======================================================================================================
# 文脈の定義(封 §1)
def attr_value(rx, attr_text):
    m = rx.search(attr_text)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def first_text(rx, body):
    m = rx.search(body)
    return X.strip_tags(m.group(1)).strip() if m else None


def read_context(attr_text, body):
    u"""1 つの ``context`` の中身 → (id か None, 内容)。内容 = (期間の種類, 始まり, 終わり, member の組, typedMember が在るか)。"""
    cid = attr_value(ID_RE, attr_text)
    inst, start, end = first_text(INSTANT_RE, body), first_text(START_RE, body), first_text(END_RE, body)
    if inst is not None:
        kind, s, e = KIND_INSTANT, u"", inst
    elif end is not None:
        kind, s, e = KIND_DURATION, start or u"", end
    else:
        kind, s, e = KIND_NONE, u"", u""
    members = []
    for m in EXPLICIT_RE.finditer(body):
        members.append((attr_value(DIM_RE, m.group(1)) or u"", X.strip_tags(m.group(2)).strip()))
    typed = [(attr_value(DIM_RE, m.group(1)) or u"", X.strip_tags(m.group(2)).strip()) for m in TYPED_RE.finditer(body)]
    return cid, (kind, s, e, tuple(sorted(members + typed)), bool(typed))


def contexts_of_text(text):
    u"""元の ``.htm`` の字 → [(id, 内容)]。``id`` の無い定義は数えない。"""
    text = COMMENT_RE.sub(u"", text)
    out = []
    for m in CTX_OPEN_RE.finditer(text):
        if m.group(1).rstrip().endswith("/"):
            continue
        close = CTX_CLOSE_RE.search(text, m.end())
        if not close:
            continue
        cid, content = read_context(m.group(1), text[m.end():close.start()])
        if cid is not None:
            out.append((cid, content))
    return out


def context_defs(files):
    u"""[(名, 字)] → {id: 内容}。同じ id で内容が違えば ``Refuse``。"""
    defs = {}
    for _n, text in sorted(files, key=lambda p: p[0]):
        for cid, content in contexts_of_text(text):
            if cid in defs and defs[cid] != content:
                raise Refuse(R_CTX_DUP)
            defs[cid] = content
    return defs


def resolve_facts(facts, defs):
    u"""fact ごとの文脈の内容の並び。``contextRef`` が無い・定義が無ければ ``Refuse``。"""
    out = []
    for f in facts:
        ref = f["attrs"].get("contextRef")
        if ref is None or ref not in defs:
            raise Refuse(R_CTX_MISSING)
        out.append(defs[ref])
    return out


def end_of(content):
    return content[2]


def members_of(content):
    return content[3]


def pair_of(content):
    return (content[2], content[3])


# ======================================================================================================
# 数える(封 §1・§2)
def line_flags(line_keys, values):
    u"""線の番号の並びと値の並び → 値が、その線の上の全部の値の最頻(並んだら先)と違うかの並び。"""
    on_line = {}
    for k, v in zip(line_keys, values):
        on_line.setdefault(k, []).append(v)
    mode = dict((k, X.mode_first(vs)) for k, vs in on_line.items())
    return [v != mode[k] for k, v in zip(line_keys, values)]


def sign_format_flags(facts):
    u"""fact ごとに、符号も書式も合うか(空の fact は True)。便 XA0 と同じ規則・同じ関数。"""
    live = [f for f in facts if not f["nil"]]
    modes = {}
    for k in X.FORMAT_CLASSES:
        modes[k] = X.mode_first([f["attrs"].get("format") for f in live if X.format_class(f["text"]) == k])
    out = []
    for f in facts:
        if f["nil"]:
            out.append(True)
            continue
        neg = X.reads_negative(f["between"])
        has = f["attrs"].get("sign") == "-"
        out.append(neg == has and f["attrs"].get("format") == modes[X.format_class(f["text"])])
    return out


def choose_combo(items, ends, mems):
    u"""表の中の fact の並び・終わりの日の並び・member の組の並び → (決まる fact の数, 8 通りの名, fact ごとの 6 つの真偽, (要素の線の数, 文脈の線の数, 1 つだけの要素の線の数), 8 通りそれぞれの決まる fact の数)。
    6 つの真偽 = (name, 終わりの日, member の組, unitRef, decimals, scale が線の決めと違うか)。"""
    per = {}
    for orient in ORIENTS:
        base = X.mismatches(items, orient)
        keys = [X.line_keys(f, orient) for f in items]
        el_keys, cx_keys = [k[0] for k in keys], [k[1] for k in keys]
        per[orient] = (base, {"C": line_flags(cx_keys, ends), "E": line_flags(el_keys, ends)}, {"C": line_flags(cx_keys, mems), "E": line_flags(el_keys, mems)},
                       X.lines_of(items, orient))
    best = None
    tally = od()
    for orient in ORIENTS:
        base, ef, mf, _lines = per[orient]
        for es in LINE_SRCS:
            for ms in LINE_SRCS:
                flags = [(b[0], e, m, b[2], b[3], b[4]) for b, e, m in zip(base, ef[es], mf[ms])]
                d = sum(1 for fl in flags if not any(fl))
                tally[orient + es + ms] = d
                if best is None or d > best[0]:
                    best = (d, orient + es + ms, flags, per[orient][3])
    return best + (tally,)


S2_KEYS = (("fact", "inside", "tables", "decided", "full", "r_name", "r_end", "r_member", "r_unit", "r_decimals", "r_scale", "r_endmember_any", "tables_not_cc")
           + tuple("k_" + c for c in COMBOS) + ("c_table", "c_elem", "c_end", "c_member", "c_formats", "c_nil", "c_undecided", "c_outside"))
S2_REASON_KEYS = ("r_name", "r_end", "r_member", "r_unit", "r_decimals", "r_scale")


def new_acc2():
    return od((k, 0) for k in S2_KEYS)


def count_stage2(facts, ends, mems, formats_in_doc):
    u"""書類 1 本 → 段 2 の数(``S2_KEYS``)。``formats_in_doc`` は書類で現れた書式の類の数(便 XA0 の数)。"""
    acc = new_acc2()
    acc["fact"] = len(facts)
    nil = sum(1 for f in facts if f["nil"])
    outside = sum(1 for f in facts if f["table"] is None)
    acc["inside"] = acc["fact"] - outside
    sf = sign_format_flags(facts)
    tables = od()
    for i, f in enumerate(facts):
        if f["table"] is not None:
            tables.setdefault(f["table"], []).append(i)
    full_ids = set()
    for ids in tables.values():
        items = [facts[i] for i in ids]
        d, combo, flags, (el, cx, _one), _tally = choose_combo(items, [ends[i] for i in ids], [mems[i] for i in ids])
        es, ms = combo[1], combo[2]
        acc["tables"] += 1
        acc["k_" + combo] += 1
        if (es, ms) != ("C", "C"):
            acc["tables_not_cc"] += 1
        acc["decided"] += d
        acc["c_table"] += CELL_PER_TABLE
        acc["c_elem"] += el * CELL_PER_ELEMENT_LINE
        acc["c_end"] += (cx if es == "C" else el) * CELL_PER_END_LINE
        acc["c_member"] += (cx if ms == "C" else el) * CELL_PER_MEMBER_LINE
        for i, fl in zip(ids, flags):
            for key, hit in zip(S2_REASON_KEYS, fl[:6]):
                acc[key] += 1 if hit else 0
            if fl[1] or fl[2]:
                acc["r_endmember_any"] += 1
            if not any(fl) and sf[i]:
                full_ids.add(i)
    acc["full"] = len(full_ids)
    acc["c_formats"] = formats_in_doc
    acc["c_nil"] = nil
    acc["c_undecided"] = (acc["inside"] - acc["full"]) * CELLS_PER_FACT
    acc["c_outside"] = outside * CELLS_PER_FACT
    return acc


def cells2(acc):
    u"""書く欄の数(段 2。項の合計)。"""
    return acc["c_table"] + acc["c_elem"] + acc["c_end"] + acc["c_member"] + acc["c_formats"] + acc["c_nil"] + acc["c_undecided"] + acc["c_outside"]


def pair_facts(facts, contents):
    u"""段 1: ``contextRef`` を (終わりの日, member の組) の対に置き換えた fact の並び(元の fact は変えない)。"""
    out = []
    for f, c in zip(facts, contents):
        g = dict(f)
        g["attrs"] = dict(f["attrs"])
        g["attrs"]["contextRef"] = pair_of(c)
        out.append(g)
    return out


XKEYS = ("ctx_defs", "member_facts", "typed_facts", "mixed_names", "mixed_facts", "startdiff_facts")


def context_stats(facts, defs, contents):
    u"""文脈の数え(``XKEYS``)。"""
    st = od((k, 0) for k in XKEYS)
    st["ctx_defs"] = len(defs)
    st["member_facts"] = sum(1 for c in contents if members_of(c))
    st["typed_facts"] = sum(1 for c in contents if c[4])
    kinds = {}
    for f, c in zip(facts, contents):
        kinds.setdefault(f["attrs"].get("name"), set()).add(c[0])
    mixed = set(n for n, ks in kinds.items() if KIND_INSTANT in ks and KIND_DURATION in ks)
    st["mixed_names"] = len(mixed)
    st["mixed_facts"] = sum(1 for f in facts if f["attrs"].get("name") in mixed)
    groups = {}
    for content in defs.values():
        if content[0] == KIND_DURATION:
            groups.setdefault(pair_of(content), set()).add(content[1])
    diff = set(p for p, starts in groups.items() if len(starts) >= 2)
    st["startdiff_facts"] = sum(1 for c in contents if c[0] == KIND_DURATION and pair_of(c) in diff)
    return st


def count_doc(facts, defs, a0):
    u"""fact の並び・文脈の定義・便 XA0 の数 → {"a0", "a1", "a2", "x"}。断れば ``Refuse``。"""
    contents = resolve_facts(facts, defs)
    return {"a0": a0, "a1": X.count_facts(pair_facts(facts, contents)),
            "a2": count_stage2(facts, [end_of(c) for c in contents], [members_of(c) for c in contents], a0["c_formats"]),
            "x": context_stats(facts, defs, contents)}


def local_of(s):
    return s.split(u":")[-1]


def secret_strings(facts, defs):
    u"""記録に書いてはならない字(要素の局所名・文脈の名・dimension と member の局所名)。"""
    out = set()
    for f in facts:
        out.add(local_of(f["attrs"].get("name") or u""))
        c = f["attrs"].get("contextRef") or u""
        if re.search(r"[A-Za-z]", c):
            out.add(c)
    for content in defs.values():
        for dim, mem in content[3]:
            out.add(local_of(dim))
            out.add(local_of(mem))
    return out


def read_doc(zip_path):
    u"""置き場の zip 1 つ → (便 XA0 の数 か None, 便 XA0 の断りの理由, この便の数 か None, この便の断りの理由, 記録に書かない字の集まり)。"""
    try:
        files = X.doc_texts(zip_path)
        facts = X.facts_of_files(files)
    except Refuse as exc:
        return None, exc.reason, None, exc.reason, set()
    a0 = X.count_facts(facts)
    try:
        defs = context_defs(files)
    except Refuse as exc:
        return a0, u"", None, exc.reason, secret_strings(facts, {})
    secrets = secret_strings(facts, defs)
    try:
        return a0, u"", count_doc(facts, defs, a0), u"", secrets
    except Refuse as exc:
        return a0, u"", None, exc.reason, secrets


# ======================================================================================================
# 段 0 の照らし(封 §1)
def stage0_problems(rows0, accs0, prior, dev_count, whole):
    u"""便 XA0 の数え(``X.doc_row``・``X.chunk_of``)で、書類ごとの行と塊の数が、便 XA0 の記録と全部同じか。違いの字の並び。
    ``whole`` が真なら 62 本の塊も照らす(``rows0`` が全部の書類のとき)。"""
    out = []
    pr = prior.get(u"書類", [])
    for i, r in enumerate(rows0):
        if i >= len(pr) or dumps(r) != dumps(pr[i]):
            out.append(u"書類 %d の行が便 XA0 の記録と違う" % (i + 1))
    if dumps(X.chunk_of(rows0[:dev_count], accs0[:dev_count])) != dumps(prior.get(u"開発の 5 本")):
        out.append(u"開発の 5 本の塊の数が便 XA0 の記録と違う")
    if whole and dumps(X.chunk_of(rows0[dev_count:], accs0[dev_count:])) != dumps(prior.get(u"本番だけの 62 本")):
        out.append(u"本番だけの 62 本の塊の数が便 XA0 の記録と違う")
    return out


def load_prior(path):
    if not os.path.isfile(path):
        raise Stop(u"**便 XA0 の記録が無い。止める**")
    with io.open(path, encoding="utf-8") as fh:
        return json.loads(fh.read(), object_pairs_hook=collections.OrderedDict)


def require_stage0(rows0, accs0, prior, dev_count, whole):
    bad = stage0_problems(rows0, accs0, prior, dev_count, whole)
    if bad:
        raise Stop(u"**段 0 が便 XA0 の記録と違う(自分の欠陥)。止める: %s**" % u"・".join(bad[:3]))


# ======================================================================================================
# 塊
def doc_row(n, d, reason):
    if d is None:
        return od([(u"番号", n), (u"断った", True), (u"断った理由", reason), (u"fact の数", None), (u"段 0 の全部決まる fact の数", None), (u"段 1 の全部決まる fact の数", None), (u"段 2 の全部決まる fact の数", None)])
    return od([(u"番号", n), (u"断った", False), (u"断った理由", u""), (u"fact の数", d["a0"]["fact"]), (u"段 0 の全部決まる fact の数", d["a0"]["full"]),
               (u"段 1 の全部決まる fact の数", d["a1"]["full"]), (u"段 2 の全部決まる fact の数", d["a2"]["full"])])


def rate(n, d):
    return od([(u"数", n), (u"分母", d), (u"%", pct1(n, d))])


def add_keys(tot, acc, keys):
    for k in keys:
        tot[k] += acc[k]


def totals(docs):
    u"""断らなかった書類の数の合計(段 0・段 1・段 2・文脈の数え)。"""
    t0, t1, t2, tx = X.new_acc(), X.new_acc(), new_acc2(), od((k, 0) for k in XKEYS)
    for d in docs:
        if d is not None:
            X.add_into(t0, d["a0"])
            X.add_into(t1, d["a1"])
            add_keys(t2, d["a2"], S2_KEYS)
            add_keys(tx, d["x"], XKEYS)
    return t0, t1, t2, tx


def stage_block(tot, cells, reasons, accs):
    base = tot["fact"] * CELLS_PER_FACT
    out = od()
    out[u"表の決めで決まる fact の数"] = tot["decided"]
    out[u"全部決まる fact の数"] = tot["full"]
    out[u"全部決まる fact が %d%% 以上の書類の数" % DOC_FULL_PCT] = X.docs_full(accs)
    out[u"書く欄の数"] = cells
    out[u"fact の数 × 7"] = base
    out[u"書く欄の比"] = rate(cells, base)
    out[u"決まらなかった理由ごとの fact の数(重ねて数える)"] = od(reasons)
    return out


def chunk_of(rows, docs):
    u"""書類の行(``doc_row``)と数の並び(断った書類は None)→ 塊の §2 の数。"""
    t0, t1, t2, tx = totals(docs)
    reasons = od()
    kept = 0
    for r, d in zip(rows, docs):
        if d is None:
            reasons[r[u"断った理由"]] = reasons.get(r[u"断った理由"], 0) + 1
        else:
            kept += 1
    out = od()
    out[u"書類の数"] = len(rows)
    out[u"断った書類の数"] = len(rows) - kept
    out[u"断った理由ごとの数"] = od(sorted(reasons.items()))
    out[u"断らなかった書類の数"] = kept
    out[u"fact の数"] = t0["fact"]
    out[u"文脈の定義の数"] = tx["ctx_defs"]
    out[u"member を 1 つ以上持つ文脈を指す fact の数"] = tx["member_facts"]
    out[u"typedMember を持つ文脈を指す fact の数"] = tx["typed_facts"]
    a0s, a1s, a2s = [[d[k] for d in docs if d is not None] for k in ("a0", "a1", "a2")]
    out[STAGE_LABELS[0]] = stage_block(t0, X.cells_of(t0), zip(X.REASONS, (t0["r_name"], t0["r_context"], t0["r_unit"], t0["r_decimals"], t0["r_scale"])), a0s)
    out[STAGE_LABELS[1]] = stage_block(t1, X.cells_of(t1), zip((u"name が線の決めと違う", u"対が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う", u"scale が線の決めと違う"),
                                                              (t1["r_name"], t1["r_context"], t1["r_unit"], t1["r_decimals"], t1["r_scale"])), a1s)
    out[STAGE_LABELS[2]] = stage_block(t2, cells2(t2), zip((u"name が線の決めと違う", u"終わりの日が線の決めと違う", u"member の組が線の決めと違う", u"unitRef が線の決めと違う", u"decimals が線の決めと違う",
                                                           u"scale が線の決めと違う"), (t2["r_name"], t2["r_end"], t2["r_member"], t2["r_unit"], t2["r_decimals"], t2["r_scale"])), a2s)
    s2 = out[STAGE_LABELS[2]]
    s2[u"終わりの日か member の組が線の決めと違う fact の数(どちらかが違えば 1)"] = t2["r_endmember_any"]
    s2[u"fact の在る表の数"] = t2["tables"]
    s2[u"8 通りのそれぞれを選んだ表の数"] = od((c, t2["k_" + c]) for c in COMBOS)
    s2[u"文脈の線・文脈の線を選ばなかった表の数"] = t2["tables_not_cc"]
    s2[u"書く欄の数(項ごと)"] = od([(u"表ごとの 3", t2["c_table"]), (u"要素の線 × 4", t2["c_elem"]), (u"終わりの日を決める側の線 × 1", t2["c_end"]), (u"member の組を決める側の線 × 1", t2["c_member"]),
                                   (u"書式の類の数", t2["c_formats"]), (u"空の fact の数 × 1", t2["c_nil"]), (u"表の中で全部決まらない fact × 7", t2["c_undecided"]), (u"表の外の fact × 7", t2["c_outside"])])
    out[u"期間の種類が 2 つ在る name の数"] = tx["mixed_names"]
    out[u"期間の種類が 2 つ在る name の fact の数"] = tx["mixed_facts"]
    out[u"始まりの日が違う期間の文脈を指す fact の数"] = tx["startdiff_facts"]
    out[u"fact が 1 つ以上在る書類の数(断らなかった)"] = sum(1 for a in a0s if a["fact"] > 0)
    return out


def judged(docs):
    u"""XA1-1〜XA1-8 の判定に要る数(丸める前の整数と %)。当たり・外れは書かない。"""
    t0, t1, t2, tx = totals(docs)
    a2s = [d["a2"] for d in docs if d is not None]
    withfact = sum(1 for a in a2s if a["fact"] > 0)
    reasons = od(zip((u"name の違い", u"終わりの日の違い", u"member の組の違い", u"unitRef の違い", u"decimals の違い", u"scale の違い"), (t2[k] for k in S2_REASON_KEYS)))
    top = max(reasons.values()) if reasons else 0
    return od([
        (u"XA1-1 段 1 の全部決まる fact / fact", rate(t1["full"], t1["fact"])),
        (u"XA1-2 段 2 の全部決まる fact / fact", rate(t2["full"], t2["fact"])),
        (u"XA1-3 段 2 で終わりの日か member の組が線の決めと違う fact の数", od([(u"数", t2["r_endmember_any"])])),
        (u"XA1-4 段 2 の決まらなかった理由ごとの fact の数と、いちばん多い理由", od([(u"理由ごとの数", reasons), (u"いちばん多い理由", [k for k, v in reasons.items() if v == top])])),
        (u"XA1-5 段 2 の全部決まる fact が %d%% 以上の書類 / fact が 1 つ以上在る書類" % DOC_FULL_PCT, od([(u"書類", X.docs_full(a2s)), (u"分母", withfact)])),
        (u"XA1-6 段 2 の書く欄の数 / fact の数 × 7", rate(cells2(t2), t2["fact"] * CELLS_PER_FACT)),
        (u"XA1-7 期間の種類が 2 つ在る name の fact / fact", rate(tx["mixed_facts"], t0["fact"])),
        (u"XA1-8 文脈の線・文脈の線を選ばなかった表 / fact の在る表", rate(t2["tables_not_cc"], t2["tables"]))])


def suspicions(ch):
    u"""封 §4 の「先に自分の欠陥を疑う場合」に当たる条件の名前の並び(段 0 が便 XA0 と違う場合は止まるのでここには出ない)。"""
    out = []
    f = ch[u"fact の数"]
    s0, s1, s2 = (ch[l][u"全部決まる fact の数"] for l in STAGE_LABELS)
    if f and s2 == f:
        out.append(u"段 2 の全部決まる fact がちょうど 100%")
    if s2 < s1:
        out.append(u"段 2 が段 1 より少ない")
    if s1 < s0:
        out.append(u"段 1 が段 0 より少ない")
    if ch[u"断った書類の数"] >= SUSPECT_DECLINED:
        out.append(u"断った書類が 6 本以上")
    return out


# ======================================================================================================
# 記録
def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・会社の名・EDINET コード・file の名・fact の値・要素の名・文脈の名・member の名・日付・表の字)が無いか。在れば止める。"""
    X.check_clean(rec, text, secret)
    if DATE_FORM_RE.search(W.HEX_RE.sub(u"", text)):
        raise Stop(u"**記録に日付の形の字が在る。止める**")


def build_record(docs_dir=None, want=DOCS_WANT, dev_count=DEV_COUNT, prior_path=None, progress=None):
    u"""置き場 → (記録, secret)。書かない。段 0 が便 XA0 の記録と違えば止まる。"""
    prior_path = prior_path or os.path.join(ROOT, PRIOR_RECORD_REL)
    prior = load_prior(prior_path)
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    rows0, accs0, rows, ds = [], [], [], []
    names = set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        a0, r0, d, reason, strs = read_doc(p)
        names |= strs
        rows0.append(X.doc_row(n, a0, r0))
        accs0.append(a0)
        rows.append(doc_row(n, d, reason))
        ds.append(d)
        if progress is not None:
            progress(u"doc %d/%d(%.1f 秒)" % (n, len(docs), time.time() - t0))
    require_stage0(rows0, accs0, prior, dev_count, True)
    secret = secret_of(docs, names)
    return assemble(rows, ds, W.order_sha256([d[0] for d in docs]), dev_count, W.sha256_file(prior_path)), secret


def secret_of(docs, names):
    u"""記録に書いてはならない字の集まり(要素の局所名・文脈の名・member の名・docID・EDINET コード)。``names`` は書類を読んだときに集めた字。"""
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    return (set(), set(e for e in names if len(e) >= 3), [d[0] for d in docs], ecodes)


def assemble(rows, ds, order_sha, dev_count, prior_sha):
    dev_rows, dev_ds = rows[:dev_count], ds[:dev_count]
    prod_rows, prod_ds = rows[dev_count:], ds[dev_count:]
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XA1(行・列の紙に収まらなかった fact の文脈を、終わりの日と member の組に分けて別々の線で決めると、どれだけ収まるか)(0 USD・engine は読まない・道具は呼ばない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(rows)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"便 XA0 の記録の sha256", prior_sha), (u"script の決めの字", list(RULES))])
    rec[u"書類"] = rows
    rec[u"開発の 5 本"] = chunk_of(dev_rows, dev_ds)
    rec[u"本番だけの 62 本"] = chunk_of(prod_rows, prod_ds)
    rec[u"予測の判定に要る数(XA1-1〜XA1-8。本番だけの 62 本のうち断らなかった書類を合わせた fact。当たり・外れは結果の文書で)"] = judged(prod_ds)
    rec[u"限界"] = list(LIMITS)
    return rec


ROW_KEYS = [u"番号", u"断った", u"断った理由", u"fact の数", u"段 0 の全部決まる fact の数", u"段 1 の全部決まる fact の数", u"段 2 の全部決まる fact の数"]


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(置き場は読まない)。違えば止まる。"""
    rows = rec.get(u"書類")
    if not isinstance(rows, list) or len(rows) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    for i, r in enumerate(rows, 1):
        if r.get(u"番号") != i or list(r) != ROW_KEYS:
            raise Stop(u"**記録の書類の形が違う。止める**")
        if r[u"断った"] != bool(r[u"断った理由"]) or r[u"断った"] != (r[u"fact の数"] is None):
            raise Stop(u"**断った書類の形が違う。止める**")
        if not r[u"断った"] and not (r[u"段 0 の全部決まる fact の数"] <= r[u"fact の数"] and r[u"段 1 の全部決まる fact の数"] <= r[u"fact の数"] and r[u"段 2 の全部決まる fact の数"] <= r[u"fact の数"]):
            raise Stop(u"**書類の数が合わない。止める**")
    for key, part in ((u"開発の 5 本", rows[:dev_count]), (u"本番だけの 62 本", rows[dev_count:])):
        ch = rec[key]
        kept = [r for r in part if not r[u"断った"]]
        pairs = [(u"書類の数", len(part)), (u"断った書類の数", len(part) - len(kept)), (u"断らなかった書類の数", len(kept)), (u"fact の数", sum(r[u"fact の数"] for r in kept))]
        for k, v in pairs:
            if ch[k] != v:
                raise Stop(u"**塊の数が書類ごとの数と合わない: %s。止める**" % k)
        for label, rk in zip(STAGE_LABELS, (u"段 0 の全部決まる fact の数", u"段 1 の全部決まる fact の数", u"段 2 の全部決まる fact の数")):
            if ch[label][u"全部決まる fact の数"] != sum(r[rk] for r in kept):
                raise Stop(u"**塊の全部決まる fact の数が書類ごとの数と合わない: %s。止める**" % label)
            if ch[label][u"全部決まる fact が %d%% 以上の書類の数" % DOC_FULL_PCT] != sum(1 for r in kept if r[u"fact の数"] > 0 and 100 * r[rk] >= DOC_FULL_PCT * r[u"fact の数"]):
                raise Stop(u"**全部決まる書類の数が合わない: %s。止める**" % label)
            blk = ch[label]
            if blk[u"fact の数 × 7"] != CELLS_PER_FACT * ch[u"fact の数"] or blk[u"書く欄の比"][u"数"] != blk[u"書く欄の数"] or blk[u"書く欄の比"][u"分母"] != blk[u"fact の数 × 7"]:
                raise Stop(u"**書く欄の比の数が合わない: %s。止める**" % label)
            if blk[u"全部決まる fact の数"] > blk[u"表の決めで決まる fact の数"]:
                raise Stop(u"**決まる fact の数が合わない: %s。止める**" % label)
        if sum(ch[u"断った理由ごとの数"].values()) != ch[u"断った書類の数"]:
            raise Stop(u"**塊の導き方が合わない。止める**")
        s2 = ch[STAGE_LABELS[2]]
        if sum(s2[u"8 通りのそれぞれを選んだ表の数"].values()) != s2[u"fact の在る表の数"] or s2[u"文脈の線・文脈の線を選ばなかった表の数"] != s2[u"fact の在る表の数"] - s2[u"8 通りのそれぞれを選んだ表の数"][u"ACC"] - s2[u"8 通りのそれぞれを選んだ表の数"][u"BCC"]:
            raise Stop(u"**8 通りの表の数が合わない。止める**")
        if list(s2[u"8 通りのそれぞれを選んだ表の数"]) != list(COMBOS) or sum(s2[u"書く欄の数(項ごと)"].values()) != s2[u"書く欄の数"]:
            raise Stop(u"**段 2 の書く欄の項が合わない。止める**")
        if s2[u"終わりの日か member の組が線の決めと違う fact の数(どちらかが違えば 1)"] > s2[u"決まらなかった理由ごとの fact の数(重ねて数える)"][u"終わりの日が線の決めと違う"] + s2[u"決まらなかった理由ごとの fact の数(重ねて数える)"][u"member の組が線の決めと違う"]:
            raise Stop(u"**終わりの日か member の組の数が合わない。止める**")
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


def run(root=ROOT, docs=None, out=None, want=DOCS_WANT, say=print, dev_count=DEV_COUNT, prior_path=None, progress=None):
    rec, secret = build_record(docs, want, dev_count, prior_path, progress)
    out = out or os.path.join(root, RECORD_REL)
    write_record(out, rec, secret)
    say(u"-> %s(書類 %d)" % (os.path.basename(out), rec[u"材料"][u"書類の本数"]))
    return rec


def check(root=ROOT, docs=None, rec_path=None, want=DOCS_WANT, say=print, dev_count=DEV_COUNT, prior_path=None):
    u"""記録の形・合計・禁止のものを検査し、置き場から数え直して記録と照らす。"""
    p = rec_path or os.path.join(root, RECORD_REL)
    if not os.path.isfile(p):
        raise Stop(u"**在る記録が無い。止める**")
    with io.open(p, encoding="utf-8") as fh:
        text = fh.read()
    rec = json.loads(text, object_pairs_hook=collections.OrderedDict)
    verify_record(rec, text, want, dev_count)
    now, secret = build_record(docs, want, dev_count, prior_path)
    if dumps(now) != dumps(rec):
        raise Stop(u"**置き場から数え直した記録が、今の記録と違う。止める**")
    check_clean(rec, text, secret)
    say(u"--check: 記録は置き場から数え直した数と同じ(書類 %d)" % now[u"材料"][u"書類の本数"])
    return now


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(便 XA0 経由の便 XB0 の関数。残りの zip は開かない)。"""
    return X.dev_docs(docs_dir, count)


def dev_run(docs_dir=None, say=print, count=DEV_COUNT, prior_path=None):
    u"""開発の 5 本だけ(記録は書かない)。(塊, 判定に要る数, 数の並び)。段 0 が便 XA0 の記録と違えば止まる。"""
    prior = load_prior(prior_path or os.path.join(ROOT, PRIOR_RECORD_REL))
    docs = dev_docs(docs_dir or DOCS_DIR, count)
    rows0, accs0, rows, ds = [], [], [], []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        a0, r0, d, reason, _strs = read_doc(p)
        rows0.append(X.doc_row(n, a0, r0))
        accs0.append(a0)
        rows.append(doc_row(n, d, reason))
        ds.append(d)
        say(u"doc %d(%.1f 秒): 断った=%s(%s) fact=%s 全部決まる 段 0=%s 段 1=%s 段 2=%s" % (
            n, time.time() - t0, d is None, reason, rows[-1][u"fact の数"], rows[-1][u"段 0 の全部決まる fact の数"], rows[-1][u"段 1 の全部決まる fact の数"],
            rows[-1][u"段 2 の全部決まる fact の数"]))
    require_stage0(rows0, accs0, prior, count, False)
    say(u"段 0 は便 XA0 の記録(開発の 5 本)と全部の数で同じ")
    ch = chunk_of(rows, ds)
    say(u"開発の 5 本の合計: %.1f 秒" % (time.time() - t_all))
    say(json.dumps(ch, ensure_ascii=False, indent=2))
    say(json.dumps(judged(ds), ensure_ascii=False, indent=2))
    say(u"先に自分の欠陥を疑う場合に当たったもの: %s" % (u"・".join(suspicions(ch)) or u"なし"))
    return ch, ds


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
