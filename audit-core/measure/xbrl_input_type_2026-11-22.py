# -*- coding: utf-8 -*-
u"""封 docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md(XM0 ― 機械の側が決めた入力の型(第 0 版)と対応表だけから、fact の属性と文脈・単位の定義を作ると、公開の道具が読む fact は元と意味として同じになるか。型に入らない fact は何か)の測定。
**0 USD。LLM の席は呼ばない。鍵は使わない。** engine(``core/``・``adapters/``)は読まない・変えない。剥がす・組む・書き出しの比べ・道具の掛け方・書類の選び方は、前の便(XB0・XT0・XP0)の script の関数を importlib で呼ぶ(写さない)。

    python3 measure/xbrl_input_type_2026-11-22.py --tool-p <venv の場所>           # 道具を確かめて 67 本を掛け、記録を書く(本番は 1 回)
    python3 measure/xbrl_input_type_2026-11-22.py --check                         # 記録の形・合計・禁止のものを検査する。道具は呼ばない・掛け直さない
    python3 measure/xbrl_input_type_2026-11-22.py --dev --tool-p <venv の場所>     # 開発の 5 本だけ。記録は書かない
    python3 measure/xbrl_input_type_2026-11-22.py ... --keep <folder>              # 書類ごとの folder(型・組んだ原稿)を残す(記録は変わらない)
    python3 measure/xbrl_input_type_2026-11-22.py derive <zip> <型の folder>       # 型を作る命令(答えを読む)
    python3 -I measure/xbrl_input_type_2026-11-22.py make <型の folder> <原稿の folder>   # 型から作る命令(別の process で呼ぶ。型の folder のほかを読まない)

型の folder の中身(書類 1 本に 1 つ。元の包み・元の htm・元の属性・元の文脈と単位の定義は置かない):
``index.json``・``t0000.txt``…(素の本文)・``c0000.json``…(持ち込み)・``type.json``(書類の決めと型の行)・``map.json``(対応表)・``outside.json``(型の外)・``taxonomy.json``。
型から作る命令の出す「原稿の folder」は、便 XP0 の原稿の folder と同じ形(便 XP0 の組む命令にそのまま渡せる)。

実装の注(封の字では 1 通りに決まらなかった所の決め。実装より先に決め、結果を見て変えない。報告にも書く):
- 書類の決めの提出者の識別子と scheme は、``id`` が ``CurrentYearInstant`` で始まる文脈の(scheme, 識別子)が 1 通りに決まるときの値(決まらなければ断る)。``CurrentYearInstant``・``CurrentYearDuration``・``FilingDateInstant`` で始まる id の文脈は、期が形(時点・期間)と違うか日が 1 通りに決まらなければ断る。
- 文脈の定義は書類全体で id から引く(同じ id で中身が違えば断る)。頭の部の ``resources`` の部が在る file が 2 つ以上なら断る(作った定義を置く先が 1 通りに決まらない)。fact が指す文脈の定義が無ければ断る。fact に ``name`` が無ければ断る。
- 数の fact の ``unitRef`` が無い・指す定義が無いときは理由 (d)。``sign`` が ``-`` 以外・表示の字が「数字と , と . だけ」でも値にならない(``[0-9]+`` か ``[0-9]+.[0-9]+``。`,` は取り除く)ときは理由 (f)。``decimals`` か ``scale`` の絶対値が 1000 を超えるときは (e)(桁あふれの守り)。
- 空の fact = ``xsi:nil`` の属性が在る数の fact。``format`` は空の fact では (e) の検査から外し(「空の fact は format を持たないのが形」の読み)、持っていれば (h)。
- 対応表は、型の行に現れた名(科目・軸・member。個別を表す軸と member は型の欄の ``個別`` なので含めない)から作る。型の行の番号は fact の並び(file の名の昇順・file の中は表 F の順の後に隠しの fact の順)で、最初に出た鍵の順。
- 空の scenario の文脈は member が無いものとして比べる。文脈の定義の比べは (提出者の scheme・識別子・期・member の組の集まり)、単位は (measure の並び・割り算の分子と分母)。
- 違った fact の数は、属性の名ごとに「その名の値が両側で違う(片側に無いを含む)」fact を数える(``contextRef`` と ``unitRef`` は定義の中身で比べる)。属性が意味として同じ書類 = 全部の対象の fact で全部の名が同じ。
- 元に在って作らなかった定義 = 元の文脈(単位)の定義のうち、中身(id を除く)が、作った定義にも型の外で写した定義にも無いもの(id が違っても中身が同じなら作ったと数える)。
- 混ぜ物の効いた = 作った fact の行から ``contextRef`` を除き ``unitRef`` を measure に置き換えた行の集まりが、混ぜ物なしと比べて、対象の fact の数だけ行が変わり、その行が全部「次元の組が 1 つ増えた同じ行」で、ほかの行が 1 つも変わらないこと。
- 道具の 1 回: 掛け方 A の 1 回だけ(便 XT0 の掛け方 A の字のまま。掛け方 B は fact の一覧に効かないので掛けない)。道具で断った = 組み直した包みの 1 回が「止まった」で元が止まっていないこと。
- JSON の書き方・別の process・時間の上限は便 XP0 のとおり。
"""
from __future__ import print_function

import argparse
import calendar
import collections
import csv
import datetime
import decimal
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

PACK_NAME = "_xm0_pack_build_2026_11_22"


def _load_sibling(name, fname):
    u"""前の便の script を、他と重ならない一意の名で読む(関数は呼ぶだけ。写さない)。"""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


P = _load_sibling(PACK_NAME, "xbrl_pack_build_2026-11-22.py")     # 便 XP0 の script
T = P.T                                            # 便 XT0 の script
B = P.B                                            # 便 XB0 の script
V = P.V                                            # 便 XV0 の script
W = P.W                                            # 便 XG0 の script(Stop の型を 1 つにするため同じ object を使う)

SEAL_REL = "docs/XBRL_INPUT_TYPE_SEAL_2026-11-22.md"
SEAL_COMMIT = "34afe495"
SCRIPT_REL = "measure/xbrl_input_type_2026-11-22.py"
RECORD_REL = "fixtures/xbrl/cd8/input_type_2026-11-22.json"
DOCS_DIR = W.DOCS_DIR
DOCS_WANT = W.DOCS_WANT

# ---- 封 §1 の決めごと(道具・掛け方・時間の上限は便 XT0・XP0 のとおり)
TOOL_VERSION = P.TOOL_VERSION
SHA_P = P.SHA_P
YEAR = P.YEAR
TIMEOUT_SEC = P.TIMEOUT_SEC
DEV_COUNT = P.DEV_COUNT
PUBLICDOC = P.PUBLICDOC
FILE_KINDS = P.FILE_KINDS
KIND_NUM, KIND_TEXT = u"数", u"文"
TARGET_IND, TARGET_DEF = u"個別", u"既定"
VALUE_NONE = u"無い"
UNIT_SHARES, UNIT_PURE = u"株", u"純数"
FORMAT_OK = "ixt:numdotdecimal"
AXIS_CONS = "jppfs_cor:ConsolidatedOrNonConsolidatedAxis"
MEMBER_IND = "jppfs_cor:NonConsolidatedMember"
ID_END, ID_START, ID_FILING = "CurrentYearInstant", "CurrentYearDuration", "FilingDateInstant"
PERIOD_CUR, PERIOD_FILING = "CurrentYear", "FilingDate"
NUM_TYPED = ("name", "contextRef", "unitRef", "decimals", "scale", "sign", "format", "xsi:nil")     # 数の fact で型が持つ属性(持ち込みに入れない)
TEXT_TYPED = ("name", "contextRef")                                                                  # 文の fact で型が持つ属性
REASONS = ("a", "b", "c", "d", "e", "f", "g", "h")
STAGES = (u"型を作る", u"型から作る", u"組む", u"道具")
MAX_EXP = 1000
CODE_PREFIX = collections.OrderedDict([(u"科目", "K"), (u"軸", "A"), (u"member", "M")])
MIX_KIND = u"対象を個別に変える"
#: 封 §4 の予測の境(記録には判定を書かない。封の門が封の表と照らす)。(下限, 上限, 上限を含むか)。None = 無い。割合は (分子の名, 分母の名) で書く
BOUNDS = collections.OrderedDict([
    ("XM0-1", (58, None, False)), ("XM0-2", (45, None, False)), ("XM0-3", (None, u"0.5%", True)), ("XM0-4", (None, None, False)), ("XM0-5", (50, None, False)),
    ("XM0-6", (None, 10, True)), ("XM0-7", (45, None, False)), ("XM0-8", (u"作れた書類の数", None, False)), ("XM0-9", (u"94%", u"98%", False)), ("XM0-10", (u"99%", None, False))])
LIMITS = [
    u"型・対応表・持ち込み・型の外は、どれも答え(受理済みの XBRL)から作った。型の外の fact は元から写すので、その fact が元と同じになるのは当たり前。会社がこの型で情報を用意できるか・対応表を作れるか・埋めた中身が正しいかは測っていない。",
    u"持ち込み(素の本文・fact の置き場・どの置き場がどの数か・文の中身・脚注・提出者別タクソノミの表)はこの便では作っていない。",
    u"型の欄と規則(期の名の 3 つの型・単位の 4 つの形・format の 1 通り・個別の軸と member)は開発の 5 本を見て決めた。62 本は前の便で数えた書類で、未使用ではない。67 本は無作為ではない。有報だけ。",
    u"比べ方 2 は contextRef の字を見ず、unitRef は measure に置き換えて比べる。字まで同じかは別の数で書く。道具 1 つ(道具 P)の fact の一覧だけで、EDINET の本物の検査とは照らしていない。",
    u"混ぜ物は 1 本につき 1 つ・対象の欄だけ。ほかの欄を変えた確かめは封の門の作り物だけ。文の fact は、型が持つのは科目・期間・対象・次元だけで、文の中身と書式の属性は持ち込み。",
    u"「XBRL を作れる」「専用の道具が要らない」「どんな資料も作れる」「誤りが無くなる」は、この便からは言えない。"]

Stop = W.Stop
Refuse = P.Refuse
od = collections.OrderedDict
sha256_file = W.sha256_file
dumps = W.dumps
jdump, jload, read_bytes, write_bytes = P.jdump, P.jload, P.read_bytes, P.write_bytes
CTX = decimal.Context(prec=400)

# ---- 型の folder の file の名
INDEX_FILE, TYPE_FILE, MAP_FILE, OUTSIDE_FILE, TAXONOMY_FILE = "index.json", "type.json", "map.json", "outside.json", "taxonomy.json"
CARRY_FMT = "c%04d.json"
EXIT_USAGE, EXIT_DECLINE, EXIT_ERROR = P.EXIT_USAGE, P.EXIT_DECLINE, P.EXIT_ERROR
DECLINE_PREFIX = P.DECLINE_PREFIX
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)
INT_RE = re.compile(r"-?[0-9]+", re.ASCII)
DISPLAY_RE = re.compile(r"[0-9,.]+", re.ASCII)
NUMBER_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?", re.ASCII)
UNIT_FORM_RE = re.compile(u"^通貨:([^:÷\\s]+)(÷株)?$")


# ======================================================================================================
# 日・期の名
def parse_date(s):
    u"""``YYYY-MM-DD`` の字 → date。形が違う・無い日なら ``None``。"""
    if not isinstance(s, str) or not DATE_RE.fullmatch(s):
        return None
    try:
        return datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        return None


def years_before(d, n):
    u"""``d`` の ``n`` 年前の日(同じ月・同じ日。元の日がその月の末日なら引いた先の月の末日)。作れなければ ``None``。"""
    y = d.year - n
    if n < 1 or y < 1:
        return None
    if d.day == calendar.monthrange(d.year, d.month)[1]:
        return datetime.date(y, d.month, calendar.monthrange(y, d.month)[1])
    return datetime.date(y, d.month, d.day)


def prior_n(x, base):
    u"""``x`` が ``base`` の N 年前の日なら N(1 以上)。無ければ ``None``。"""
    n = base.year - x.year
    if n >= 1 and years_before(base, n) == x:
        return n
    return None


def period_name(kind, dates, dec):
    u"""期の名(``CurrentYear``・``FilingDate``・``Prior<N>Year``)か ``None``。kind = ``instant``・``duration``。dates = 日の字の並び。dec = 書類の決め。"""
    ds = [parse_date(x) for x in dates]
    end, start, filing = parse_date(dec["end"]), parse_date(dec["start"]), parse_date(dec["filing"])
    if end is None or start is None or filing is None or any(x is None for x in ds):
        return None
    if kind == "instant" and len(ds) == 1:
        x = ds[0]
        if x == end:
            return PERIOD_CUR
        if x == filing:
            return PERIOD_FILING
        n = prior_n(x, end)
        return "Prior%dYear" % n if n else None
    if kind == "duration" and len(ds) == 2:
        s, e = ds
        if (s, e) == (start, end):
            return PERIOD_CUR
        n = prior_n(e, end)
        if n and years_before(start, n) == s:
            return "Prior%dYear" % n
        return None
    return None


# ======================================================================================================
# 文脈・単位(便 XB0 の表 H の entry を読む)
def canon_ctx(c):
    u"""文脈の定義の中身(id を除く)。"""
    return (c["scheme"], c["ident"], tuple(tuple(p) for p in c["period"]), tuple(sorted(tuple(m) for m in c["members"])))


def canon_unit(u):
    u"""単位の定義の中身(id を除く)。"""
    d = u.get("divide")
    return (tuple(u.get("measures") or ()), None if d is None else (tuple(d["num"]), tuple(d["den"])))


def unit_text(u):
    u"""単位の定義 → measure の字(``measure`` を ``,`` でつなぐ。割り算は ``分子/分母``)。道具の fact の一覧の突き合わせに使う。"""
    d = u.get("divide")
    if d is not None:
        return u",".join(d["num"]) + u"/" + u",".join(d["den"])
    return u",".join(u.get("measures") or ())


def unit_form(u):
    u"""単位の定義 → 型の欄の 4 つの形の字。どれでもなければ ``None``。"""
    ms, d = list(u.get("measures") or ()), u.get("divide")

    def cur(x):
        return x[len("iso4217:"):] if isinstance(x, str) and x.startswith("iso4217:") and len(x) > len("iso4217:") and ":" not in x[len("iso4217:"):] and not re.search(r"\s", x) else None
    if d is None:
        if len(ms) != 1:
            return None
        if ms[0] == "xbrli:shares":
            return UNIT_SHARES
        if ms[0] == "xbrli:pure":
            return UNIT_PURE
        c = cur(ms[0])
        return u"通貨:" + c if c else None
    if ms or len(d["num"]) != 1 or len(d["den"]) != 1 or d["den"][0] != "xbrli:shares":
        return None
    c = cur(d["num"][0])
    return u"通貨:" + c + u"÷株" if c else None


def unit_from_form(form):
    u"""型の欄の単位の形 → (id, 定義)。知らない形は ``Refuse``。"""
    if form == UNIT_SHARES:
        return "shares", od([("type", "unit"), ("id", "shares"), ("measures", ["xbrli:shares"]), ("divide", None)])
    if form == UNIT_PURE:
        return "pure", od([("type", "unit"), ("id", "pure"), ("measures", ["xbrli:pure"]), ("divide", None)])
    m = UNIT_FORM_RE.match(form) if isinstance(form, str) else None
    if not m:
        raise Refuse(u"単位の形が知らない形")
    cur = "iso4217:" + m.group(1)
    if m.group(2):
        uid = m.group(1) + "PerShares"
        return uid, od([("type", "unit"), ("id", uid), ("measures", []), ("divide", od([("num", [cur]), ("den", ["xbrli:shares"])]))])
    return m.group(1), od([("type", "unit"), ("id", m.group(1)), ("measures", [cur]), ("divide", None)])


def member_str(m):
    u"""member の名 → 文脈の id に入れる字。接頭辞が ``_cor`` で終わる名なら局所名、そうでなければ接頭辞と局所名を区切りの字なしで続けた字。"""
    prefix, local = m.split(":", 1) if ":" in m else ("", m)
    return local if prefix.endswith("_cor") else prefix + local


def context_id(pname, kind, members):
    u"""文脈の id。members = [(軸の名, member の名)](型の欄の対象と次元を合わせたもの)。個別の member が先、次に軸の名の昇順。"""
    ind = [m for ax, m in members if ax == AXIS_CONS]
    rest = sorted((ax, m) for ax, m in members if ax != AXIS_CONS)
    return pname + (u"Instant" if kind == "instant" else u"Duration") + u"".join(u"_" + member_str(m) for m in ind + [m for _a, m in rest])


def context_def(cid, dec, kind, dates, members):
    u"""作る文脈の定義(``members`` は軸の名の昇順に並べる)。"""
    period = [("xbrli:instant", dates[0])] if kind == "instant" else [("xbrli:startDate", dates[0]), ("xbrli:endDate", dates[1])]
    mem = sorted((ax, m) for ax, m in members)
    return od([("type", "context"), ("id", cid), ("scheme", dec["scheme"]), ("ident", dec["ident"]), ("period", [list(p) for p in period]),
               ("members", [list(x) for x in mem]), ("has_scenario", bool(mem))])


def ctx_info(c, dec):
    u"""文脈の定義 → (理由の集まり, 期の種類, 日, 期の名, 対象, 次元)。理由は (a)(b)(c)。"""
    reasons = set()
    kind = dates = pname = None
    per = [tuple(p) for p in c["period"]]
    names = [k for k, _v in per]
    if names == ["xbrli:instant"]:
        kind, dates = "instant", [per[0][1]]
    elif names == ["xbrli:startDate", "xbrli:endDate"]:
        kind, dates = "duration", [per[0][1], per[1][1]]
    if kind is not None:
        pname = period_name(kind, dates, dec)
    if pname is None:
        reasons.add("a")
    if (c["scheme"], c["ident"]) != (dec["scheme"], dec["ident"]):
        reasons.add("b")
    axes = [ax for ax, _m in c["members"]]
    target, dims = TARGET_DEF, []
    bad = len(set(axes)) != len(axes)
    for ax, m in c["members"]:
        if ax == AXIS_CONS:
            if m != MEMBER_IND:
                bad = True
            else:
                target = TARGET_IND
        else:
            dims.append((ax, m))
    if bad:
        reasons.add("c")
    return reasons, kind, dates, pname, target, sorted(dims)


# ======================================================================================================
# 数の fact
def int_attr(s):
    u"""整数の字(``-`` のあとに数字)なら int・桁あふれの守りで ``MAX_EXP`` を超えるときと整数の字でないときは ``None``。"""
    if not isinstance(s, str) or not INT_RE.fullmatch(s):
        return None
    n = int(s)
    return n if abs(n) <= MAX_EXP else None


def number_value(content, shift, sign):
    u"""表示の字 → 符号つきの本当の大きさの 10 進の字。作れなければ ``None``。負の印つきの 0 は ``-0``。"""
    if not DISPLAY_RE.fullmatch(content or ""):
        return None
    digits = content.replace(",", "")
    if not NUMBER_RE.fullmatch(digits):
        return None
    mag = CTX.normalize(CTX.scaleb(CTX.create_decimal(digits), shift))
    text = u"0" if mag == 0 else format(mag, "f")
    return (u"-" if sign == "-" else u"") + text


def display_text(value, shift, prec):
    u"""型の値・表示の位・精度から本文の fact の字を書く(値の大きさ ÷ 10 の表示の位乗を、小数点より後ろ ``max(0, 精度 + 表示の位)`` 桁・3 桁ごとの ``,`` つきで)。"""
    mag = CTX.create_decimal(value[1:] if value.startswith(u"-") else value)
    places = max(0, prec + shift)
    q = CTX.quantize(CTX.scaleb(mag, -shift), decimal.Decimal(1).scaleb(-places))
    return format(q, ",.%df" % places)


# ======================================================================================================
# 型を作る(答えを読む)
def collect_resources(files):
    u"""書類全体の文脈・単位の定義と、``resources`` の部を持つ file の番号の並び。違う中身の同じ id・resources の部が 2 つ以上なら ``Refuse``。"""
    ctxs, units, hosts = od(), od(), []
    for fi, (_n, _p, _F, H) in enumerate(files):
        if H is None:
            continue
        if "ix:resources" in H["sections"]:
            hosts.append(fi)
        for r in H["resources"]:
            if r["type"] == "context":
                if r["id"] in ctxs and canon_ctx(ctxs[r["id"]]) != canon_ctx(r):
                    raise Refuse(u"文脈の id が重なる")
                ctxs.setdefault(r["id"], r)
            elif r["type"] == "unit":
                if r["id"] in units and canon_unit(units[r["id"]]) != canon_unit(r):
                    raise Refuse(u"単位の id が重なる")
                units.setdefault(r["id"], r)
    if len(hosts) > 1:
        raise Refuse(u"resources の部が 2 つ以上")
    return ctxs, units, hosts


def decide_document(ctxs):
    u"""書類の決め。1 通りに決まらなければ ``Refuse``。"""
    ends, starts, filings, ents = set(), set(), set(), set()
    for cid, c in ctxs.items():
        for pref, bag in ((ID_END, ends), (ID_START, starts), (ID_FILING, filings)):
            if cid.startswith(pref):
                per = [tuple(p) for p in c["period"]]
                names = [k for k, _v in per]
                if pref == ID_START and names == ["xbrli:startDate", "xbrli:endDate"]:
                    bag.add(per[0][1])
                elif pref != ID_START and names == ["xbrli:instant"]:
                    bag.add(per[0][1])
                else:
                    raise Refuse(u"書類の決めの文脈の期の形が違う")
                if pref == ID_END:
                    ents.add((c["scheme"], c["ident"]))
    for bag in (ends, starts, filings):
        if len(bag) != 1 or parse_date(next(iter(bag))) is None:
            raise Refuse(u"書類の決めが 1 通りに決まらない")
    if len(ents) != 1:
        raise Refuse(u"書類の決めの提出者が 1 通りに決まらない")
    scheme, ident = next(iter(ents))
    return od([("scheme", scheme), ("ident", ident), ("start", next(iter(starts))), ("end", next(iter(ends))), ("filing", next(iter(filings)))])


def target_facts(files):
    u"""対象の fact の並び(file の名の昇順・file の中は表 F の順の後に隠しの fact)。1 つは dict(fi・where・idx・kind・attrs・content)。"""
    out = []
    for fi, (_n, plain, F, H) in enumerate(files):
        for i, e in enumerate(F):
            if e["kind"] in ("nonFraction", "nonNumeric"):
                out.append(od([("fi", fi), ("where", "F"), ("idx", i), ("kind", e["kind"]), ("attrs", e["attrs"]), ("content", plain[e["start"]:e["end"]])]))
        if H is not None:
            for j, h in enumerate(H["hidden"]):
                out.append(od([("fi", fi), ("where", "H"), ("idx", j), ("kind", h["kind"]), ("attrs", h["attrs"]), ("content", h["text"])]))
    return out


def judge_number(a, content, ctxs_units):
    u"""数の fact 1 つ → (理由の集まり, 単位の定義か None, 値の字か None, 単位の形か None, 表示の位か None, 精度か None, 空か)。"""
    reasons = set()
    nil = "xsi:nil" in a
    unit = ctxs_units.get(a.get("unitRef"))
    form = unit_form(unit) if unit is not None else None
    if form is None:
        reasons.add("d")
    shift = prec = value = None
    if nil:
        if a.get("xsi:nil") != "true" or any(k in a for k in ("decimals", "scale", "sign", "format")):
            reasons.add("h")
        value = VALUE_NONE
    else:
        if a.get("format") != FORMAT_OK:
            reasons.add("e")
        prec = int_attr(a.get("decimals")) if "decimals" in a else None
        shift = int_attr(a["scale"]) if "scale" in a else 0
        if prec is None or shift is None:
            reasons.add("e")
            shift = prec = None
        sign = a.get("sign")
        if sign is not None and sign != "-":
            reasons.add("f")
        elif shift is not None:
            value = number_value(content, shift, sign)
            if value is None:
                reasons.add("f")
        elif not DISPLAY_RE.fullmatch(content or "") or not NUMBER_RE.fullmatch((content or "").replace(",", "")):
            reasons.add("f")
    return reasons, unit, value, form, shift, prec, nil


def analyze(files):
    u"""表の並び → 型の解析。``Refuse`` は断り。返り値 dict: ``dec``・``facts``(対象の fact ごとの判定)・``rows``(型の行)・``outside``(型の外の fact の並び)・``ctxs``・``units``・``hosts``・``maps``。"""
    ctxs, units, hosts = collect_resources(files)
    dec = decide_document(ctxs)
    facts = target_facts(files)
    for f in facts:
        a = f["attrs"]
        if "name" not in a:
            raise Refuse(u"fact に name が無い")
        cref = a.get("contextRef")
        if cref not in ctxs:
            raise Refuse(u"文脈の定義が無い fact")
        reasons, kind, dates, pname, target, dims = ctx_info(ctxs[cref], dec)
        f["reasons"] = set(reasons)
        f["period"] = (kind, dates)
        f["target"], f["dims"] = target, dims
        f["isnum"] = f["kind"] == "nonFraction"
        f["unit"] = f["value"] = f["form"] = f["shift"] = f["prec"] = None
        f["nil"] = False
        if f["isnum"]:
            r, unit, value, form, shift, prec, nil = judge_number(a, f["content"], units)
            f["reasons"] |= r
            f["unit"], f["value"], f["form"], f["shift"], f["prec"], f["nil"] = unit, value, form, shift, prec, nil
    # 同じ鍵の数の fact の食い違い(理由 (g))
    groups = collections.OrderedDict()
    for f in facts:
        if not f["reasons"]:
            f["key"] = (f["isnum"], f["attrs"]["name"], tuple(f["period"][1]), f["period"][0], f["target"], tuple(f["dims"]))
            groups.setdefault(f["key"], []).append(f)
    for key, fs in groups.items():
        if key[0]:
            vals = set((x["value"], x["form"], x["shift"], x["prec"]) for x in fs)
            if len(vals) > 1:
                for x in fs:
                    x["reasons"].add("g")
    rows, row_of = [], {}
    for f in facts:
        if f["reasons"]:
            continue
        k = f["key"]
        if k not in row_of:
            row_of[k] = len(rows)
            rows.append(od([("kind", KIND_NUM if f["isnum"] else KIND_TEXT), ("name", f["attrs"]["name"]), ("period", list(f["period"][1])), ("pkind", f["period"][0]), ("target", f["target"]),
                            ("dims", [list(x) for x in f["dims"]]), ("value", f["value"]), ("unit", f["form"]), ("shift", f["shift"]), ("prec", f["prec"]), ("count", 0)]))
        rows[row_of[k]]["count"] += 1
        f["row"] = row_of[k]
    outside = [f for f in facts if f["reasons"]]
    for j, f in enumerate(outside):
        f["out"] = j
    return od([("dec", dec), ("facts", facts), ("rows", rows), ("outside", outside), ("ctxs", ctxs), ("units", units), ("hosts", hosts)])


def code_maps(rows):
    u"""型の行に現れた名から対応表を作る(種類ごとに名の昇順に並べた番号)。(対応表, 名 → コードの表 3 つ)。"""
    names = od((k, set()) for k in CODE_PREFIX)
    for r in rows:
        names[u"科目"].add(r["name"])
        for ax, m in r["dims"]:
            names[u"軸"].add(ax)
            names[u"member"].add(m)
    maps, inv = od(), od()
    for kind, pre in CODE_PREFIX.items():
        table = od(("%s%04d" % (pre, i), n) for i, n in enumerate(sorted(names[kind]), 1))
        maps[kind] = table
        inv[kind] = od((n, c) for c, n in table.items())
    return maps, inv


def row_to_json(r, inv):
    u"""型の行(名つき) → folder に書く型の行(コードつき)。"""
    o = od([("kind", r["kind"]), ("code", inv[u"科目"][r["name"]]), ("period", r["period"]), ("pkind", r["pkind"]), ("target", r["target"]),
            ("dims", [[inv[u"軸"][ax], inv[u"member"][m]] for ax, m in r["dims"]])])
    if r["kind"] == KIND_NUM:
        o["value"], o["unit"] = r["value"], r["unit"]
        if r["value"] != VALUE_NONE:
            o["shift"], o["prec"] = r["shift"], r["prec"]
    return o


def carried_attrs(f):
    typed = NUM_TYPED if f["isnum"] else TEXT_TYPED
    return dict((k, v) for k, v in sorted(f["attrs"].items()) if k not in typed)


def write_type_folder(folder, files, names, tables, an):
    u"""型の folder を書く。元の字・元の属性・元の文脈と単位の定義は置かない(型の外だけは写す)。"""
    os.makedirs(folder)
    maps, inv = code_maps(an["rows"])
    by_where = {}
    for f in an["facts"]:
        by_where[(f["fi"], f["where"], f["idx"])] = f
    index = od([("htm", []), ("taxonomy", od([("file", TAXONOMY_FILE), ("names", od((k, P.rel_of(names[k])) for k in FILE_KINDS))]))])
    for fi, (name, plain, F, H) in enumerate(files):
        write_bytes(os.path.join(folder, P.TEXT_FMT % fi), plain.encode("utf-8"))
        cf = []
        for i, e in enumerate(F):
            o = od([("kind", e["kind"]), ("self", e["self"]), ("start", e["start"]), ("end", e["end"]), ("parent", e["parent"])])
            f = by_where.get((fi, "F", i))
            if f is None:
                o["attrs"] = e["attrs"]
            elif "row" in f:
                o["row"], o["carry"] = f["row"], carried_attrs(f)
            else:
                o["out"] = f["out"]
            cf.append(o)
        ch = None
        if H is not None:
            hid = []
            for j, h in enumerate(H["hidden"]):
                f = by_where[(fi, "H", j)]
                o = od([("kind", h["kind"]), ("self", h["self"]), ("text", h["text"])])
                if "row" in f:
                    o["row"], o["carry"] = f["row"], carried_attrs(f)
                else:
                    o["out"] = f["out"]
                hid.append(o)
            ch = od([("pos", H["pos"]), ("before", H["before"]), ("sections", H["sections"]), ("hidden", hid), ("references", H["references"]),
                     ("resources", [r for r in H["resources"] if r["type"] == "ref"])])
        write_bytes(os.path.join(folder, CARRY_FMT % fi), jdump(od([("F", cf), ("H", ch)])))
        index["htm"].append(od([("name", P.rel_of(name)), ("text", P.TEXT_FMT % fi), ("carry", CARRY_FMT % fi)]))
    write_bytes(os.path.join(folder, TYPE_FILE), jdump(od([("decision", an["dec"]), ("rows", [row_to_json(r, inv) for r in an["rows"]])])))
    write_bytes(os.path.join(folder, MAP_FILE), jdump(maps))
    ofacts, used_ctx, used_unit = [], set(), set()
    for f in an["outside"]:
        ofacts.append(od([("kind", f["kind"]), ("reasons", sorted(f["reasons"])), ("attrs", f["attrs"])]))
        used_ctx.add(f["attrs"]["contextRef"])
        if f["isnum"] and f["attrs"].get("unitRef") in an["units"]:
            used_unit.add(f["attrs"]["unitRef"])
    write_bytes(os.path.join(folder, OUTSIDE_FILE), jdump(od([("facts", ofacts), ("contexts", [c for i, c in an["ctxs"].items() if i in used_ctx]),
                                                               ("units", [u for i, u in an["units"].items() if i in used_unit])])))
    write_bytes(os.path.join(folder, TAXONOMY_FILE), jdump(od([("tables", tables)])))
    write_bytes(os.path.join(folder, INDEX_FILE), jdump(index))
    return index


def derive_folder(entries, folder):
    u"""元の包みから型の folder を作る。(解析, 表の並び)。断りは ``Refuse``。"""
    files, names, tables = P.peel_tables(entries)
    an = analyze(files)
    try:
        write_type_folder(folder, files, names, tables, an)
    except Refuse:
        raise
    except Exception:                                      # noqa: BLE001
        shutil.rmtree(folder, ignore_errors=True)
        raise Refuse(u"folder に書けない形")
    return an, files


# ======================================================================================================
# 型から作る(型の folder だけを読む。別の process の命令の中身)
def build_definitions(dec, rows, maps, inv_unused=None):
    u"""型の行 → (作った文脈の定義の並び, 作った単位の定義の並び, 文脈ごとの id の表)。id が違う組で重なれば ``Refuse``。"""
    ctx_ids = od()
    defs = {}
    for r in rows:
        members = [(maps[u"軸"][ax], maps[u"member"][m]) for ax, m in r["dims"]]
        if r["target"] == TARGET_IND:
            members.append((AXIS_CONS, MEMBER_IND))
        elif r["target"] != TARGET_DEF:
            raise Refuse(u"型の対象が知らない値")
        kind = r["pkind"]
        if kind not in ("instant", "duration"):
            raise Refuse(u"型の期の種類が知らない値")
        dates = list(r["period"])
        pname = period_name(kind, dates, dec)
        if pname is None:
            raise Refuse(u"期の名が作れない")
        cid = context_id(pname, kind, members)
        group = (kind, tuple(dates), tuple(sorted(members)))
        if cid in defs and defs[cid][0] != group:
            raise Refuse(u"文脈の id が違う組で重なる")
        defs.setdefault(cid, (group, context_def(cid, dec, kind, dates, members)))
    ctxs = [defs[k][1] for k in sorted(defs)]
    units = od()
    for r in rows:
        if r["kind"] == KIND_NUM:
            uid, u = unit_from_form(r["unit"])
            units.setdefault(uid, u)
    return ctxs, [units[k] for k in sorted(units)]


def merge_outside(built, outs):
    u"""型の外の定義を足す(作った id と同じ id で中身が同じなら足さない・違えば ``Refuse``)。"""
    ids = dict((d["id"], d) for d in built)
    out = list(built)
    for d in outs:
        if d["id"] in ids:
            same = canon_ctx(ids[d["id"]]) == canon_ctx(d) if d["type"] == "context" else canon_unit(ids[d["id"]]) == canon_unit(d)
            if not same:
                raise Refuse(u"型の外の定義が作った定義と同じ id で中身が違う")
            continue
        ids[d["id"]] = d
        out.append(d)
    return out


def make_attrs(row, maps, cid, uid, carry):
    u"""型の行 + 持ち込みの属性 → 作る fact の属性(名の昇順)。"""
    forbidden = NUM_TYPED if row["kind"] == KIND_NUM else TEXT_TYPED
    if any(k in forbidden for k in carry):
        raise Refuse(u"持ち込みに型の属性が在る")
    a = {"name": maps[u"科目"][row["code"]], "contextRef": cid}
    if row["kind"] == KIND_NUM:
        a["unitRef"] = uid
        if row["value"] == VALUE_NONE:
            a["xsi:nil"] = "true"
        else:
            a["decimals"], a["scale"], a["format"] = str(row["prec"]), str(row["shift"]), FORMAT_OK
            if row["value"].startswith(u"-"):
                a["sign"] = "-"
    elif row["kind"] != KIND_TEXT:
        raise Refuse(u"型の種類が知らない値")
    a.update(carry)
    return dict(sorted(a.items()))


def render_manuscript(folder):
    u"""型の folder → (表の並び [(名, 素の本文, 表 F, 表 H)], 名, 表)。型の folder の中の file のほかを読まない。知らない形・例外は ``Refuse``。"""
    try:
        index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
        typ = jload(read_bytes(os.path.join(folder, TYPE_FILE)))
        maps = jload(read_bytes(os.path.join(folder, MAP_FILE)))
        outside = jload(read_bytes(os.path.join(folder, OUTSIDE_FILE)))
        dec, rows = typ["decision"], typ["rows"]
        mp = od([(u"科目", maps[u"科目"]), (u"軸", maps[u"軸"]), (u"member", maps[u"member"])])
        ctxs, units = build_definitions(dec, rows, mp)
        rowinfo = []
        for r in rows:
            members = [(mp[u"軸"][ax], mp[u"member"][m]) for ax, m in r["dims"]]
            if r["target"] == TARGET_IND:
                members.append((AXIS_CONS, MEMBER_IND))
            rowinfo.append((context_id(period_name(r["pkind"], list(r["period"]), dec), r["pkind"], members), unit_from_form(r["unit"])[0] if r["kind"] == KIND_NUM else None))
        ctxs = merge_outside(ctxs, outside["contexts"])
        units = merge_outside(units, outside["units"])
        files, host = [], None
        for item in index["htm"]:
            plain = read_bytes(os.path.join(folder, P.safe_local(item["text"]))).decode("utf-8")
            carry = jload(read_bytes(os.path.join(folder, P.safe_local(item["carry"]))))
            F = []
            for e in carry["F"]:
                a = e.get("attrs")
                if "row" in e:
                    cid, uid = rowinfo[e["row"]]
                    a = make_attrs(rows[e["row"]], mp, cid, uid, e["carry"])
                elif "out" in e:
                    a = dict(sorted(outside["facts"][e["out"]]["attrs"].items()))
                else:
                    a = dict(sorted(a.items()))
                F.append(od([("kind", e["kind"]), ("self", e["self"]), ("start", e["start"]), ("end", e["end"]), ("parent", e["parent"]), ("attrs", a)]))
            H = None
            ch = carry["H"]
            if ch is not None:
                hid = []
                for h in ch["hidden"]:
                    if "row" in h:
                        cid, uid = rowinfo[h["row"]]
                        a = make_attrs(rows[h["row"]], mp, cid, uid, h["carry"])
                    else:
                        a = dict(sorted(outside["facts"][h["out"]]["attrs"].items()))
                    hid.append(od([("kind", h["kind"]), ("self", h["self"]), ("attrs", a), ("text", h["text"])]))
                res = list(ch["resources"])
                if "ix:resources" in ch["sections"]:
                    host = True
                    res = res + ctxs + units
                H = od([("sections", ch["sections"]), ("hidden", hid), ("references", ch["references"]), ("resources", res), ("pos", ch["pos"]), ("before", ch["before"])])
            files.append((PUBLICDOC + P.safe_rel(item["name"]), plain, F, H))
        if (ctxs or units) and not host:
            raise Refuse(u"作った定義を置く頭の部が無い")
        tax = index["taxonomy"]
        tables = jload(read_bytes(os.path.join(folder, P.safe_local(tax["file"]))))["tables"]
        names = od((k, PUBLICDOC + P.safe_rel(tax["names"][k])) for k in FILE_KINDS)
        return files, names, tables
    except Refuse:
        raise
    except (B.Decline, T.Decline) as exc:
        raise Refuse(exc.reason)
    except Exception:                                      # noqa: BLE001  知らない形は断る
        raise Refuse(u"作る途中の例外")


def make_main(args):
    u"""型から作る命令。引数は folder 2 つだけ。終わりの値: 0・64(使い方)・2(断り)・1(例外)。"""
    if len(args) != 2:
        print(u"使い方: make <型の folder> <原稿の folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        files, names, tables = render_manuscript(args[0])
        P.write_folder(args[1], files, names, tables)
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


def derive_main(args):
    u"""型を作る命令。引数は zip と folder。"""
    if len(args) != 2:
        print(u"使い方: derive <zip> <型の folder>", file=sys.stderr)
        return EXIT_USAGE
    try:
        derive_folder(B.load_package(args[0]), args[1])
    except Refuse as exc:
        print(DECLINE_PREFIX + exc.reason, file=sys.stderr)
        return EXIT_DECLINE
    except Exception:                                      # noqa: BLE001
        print(u"ERROR", file=sys.stderr)
        return EXIT_ERROR
    return 0


# ======================================================================================================
# 別の process で作る
def make_command(folder, out):
    return [sys.executable, "-I", SCRIPT_PATH, "make", folder, out]


def exec_make(folder, out, cwd, proc=None):
    u"""型から作る命令を別の process で 1 回。(成功か, 断りの理由, 秒)。"""
    proc = proc or P.run_process
    t0 = time.time()
    rc, err, timed_out = proc(make_command(folder, out), cwd, TIMEOUT_SEC)
    secs = time.time() - t0
    if timed_out:
        return False, u"型から作る命令が時間の上限を超えた", secs
    if rc != 0:
        reason = P.decline_reason(err)
        return False, (reason if reason is not None else u"型から作る命令が 0 でない終わりの値で終わった"), secs
    return True, u"", secs


def carry_forbidden(folder):
    u"""型の folder の持ち込みに入れないもの(型に入った fact の型の属性・文脈と単位の定義)が在れば、その説明の並び。無ければ空。"""
    bad = []
    index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
    rows = jload(read_bytes(os.path.join(folder, TYPE_FILE)))["rows"]

    def check(e, what):
        typed = NUM_TYPED if rows[e["row"]]["kind"] == KIND_NUM else TEXT_TYPED
        if "attrs" in e or any(k in typed for k in e["carry"]):
            bad.append(what + u"の型の属性が持ち込みに在る")
    for item in index["htm"]:
        carry = jload(read_bytes(os.path.join(folder, item["carry"])))
        for e in carry["F"]:
            if "row" in e:
                check(e, u"型に入った fact")
        ch = carry["H"]
        if ch is not None:
            for h in ch["hidden"]:
                if "row" in h:
                    check(h, u"型に入った隠しの fact")
            for r in ch["resources"]:
                if r.get("type") != "ref":
                    bad.append(u"持ち込みに文脈か単位の定義が在る")
    return bad


# ======================================================================================================
# 比べる
def context_view(H_list):
    u"""表 H の並び → (id → 文脈の定義, id → 単位の定義)。"""
    c, u = {}, {}
    for H in H_list:
        if H is None:
            continue
        for r in H["resources"]:
            if r["type"] == "context":
                c.setdefault(r["id"], r)
            elif r["type"] == "unit":
                u.setdefault(r["id"], r)
    return c, u


def fact_attr_list(files):
    u"""対象の fact の属性の並び(``target_facts`` と同じ順)。"""
    return [f["attrs"] for f in target_facts(files)]


def unit_same(a_ref, b_ref, ou, nu):
    u"""単位の参照が、定義の中身(measure)で同じか。両側とも参照が無いか、両側とも定義が無くて字が同じなら同じ。"""
    if a_ref is None or b_ref is None:
        return a_ref is None and b_ref is None
    ua, ub = ou.get(a_ref), nu.get(b_ref)
    if ua is None or ub is None:
        return ua is None and ub is None and a_ref == b_ref
    return canon_unit(ua) == canon_unit(ub)


def compare_attrs(orig_files, new_files):
    u"""比べ方 1。(属性が意味として同じか, 文脈の名(contextRef の字)も全部同じか, 違った fact の数, 属性の名ごとの違った fact の数)。"""
    oc, ou = context_view([x[3] for x in orig_files])
    nc, nu = context_view([x[3] for x in new_files])
    oa, na = fact_attr_list(orig_files), fact_attr_list(new_files)
    if len(oa) != len(na):
        return False, False, max(len(oa), len(na)), od([(u"fact の数", 1)])
    diff_facts = 0
    per = collections.Counter()
    names_same = True
    for a, b in zip(oa, na):
        bad = set()
        for k in set(a) | set(b):
            if k not in ("contextRef", "unitRef") and ((k in a) != (k in b) or a.get(k) != b.get(k)):
                bad.add(k)
        ca, cb = oc.get(a.get("contextRef")), nc.get(b.get("contextRef"))
        if ca is None or cb is None or canon_ctx(ca) != canon_ctx(cb):
            bad.add("contextRef")
        if a.get("contextRef") != b.get("contextRef"):
            names_same = False
        if not unit_same(a.get("unitRef"), b.get("unitRef"), ou, nu):
            bad.add("unitRef")
        if bad:
            diff_facts += 1
            per.update(bad)
    return diff_facts == 0, names_same, diff_facts, od(sorted(per.items()))


def read_fact_rows(path):
    u"""道具の fact の一覧の csv → (見出し, 行の並び)。file が無ければ (None, [])。"""
    if not os.path.isfile(path):
        return None, []
    csv.field_size_limit(2 ** 31 - 1)
    with io.open(path, encoding="utf-8", newline="") as fh:
        rows = [tuple(r) for r in csv.reader(fh)]
    if not rows:
        return None, []
    return rows[0], rows[1:]


def normalize_rows(header, rows, unit_map):
    u"""比べ方 2 の正規化: 行から ``contextRef`` の列を除き、``unitRef`` の列を、その側の包みの単位の定義の measure の字に置き換える。並べ替えた並び。見出しが読めなければ ``None``。"""
    if not header:
        return None
    names = [h.lstrip(u"﻿") for h in header]
    if u"contextRef" not in names or u"unitRef" not in names:
        return None
    ci, ui = names.index(u"contextRef"), names.index(u"unitRef")
    out = []
    for r in rows:
        r = list(r)
        r[ui] = unit_map.get(r[ui], r[ui]) if r[ui] else r[ui]
        out.append(tuple(x for i, x in enumerate(r) if i != ci))
    return sorted(out)


def unit_map_of(files):
    c, u = context_view([x[3] for x in files])
    return dict((k, unit_text(v)) for k, v in u.items())


def run_facts(tool, zip_path, workdir, tag, runner=None):
    u"""掛け方 A を 1 回。(1 回分の数, 見出し, 行の並び)。"""
    runner = runner or V.exec_cmd
    paths = T.csv_paths(workdir, tag)
    text, to = runner(T.SEED_PREFIX + T.command_a(tool, zip_path, paths), TIMEOUT_SEC)
    one = V.count_one(text, to)
    header, rows = read_fact_rows(paths["facts"])
    return one, header, rows


def mix_row_index(rows):
    u"""混ぜ物の当て先の型の行の番号(型の行の番号の昇順で最初)。無ければ ``None``。"""
    keys = set((r["kind"], r["code"], tuple(r["period"]), r["pkind"], r["target"], tuple(tuple(d) for d in r["dims"])) for r in rows)
    for i, r in enumerate(rows):
        if r["kind"] == KIND_NUM and r["target"] == TARGET_DEF and not r["dims"] and r["value"] != VALUE_NONE:
            if (r["kind"], r["code"], tuple(r["period"]), r["pkind"], TARGET_IND, ()) not in keys:
                return i
    return None


def mix_folder(folder):
    u"""混ぜ物: 型の folder の file を disk の上で 1 か所だけ変える。(変えた行の番号, その行を指す fact の数) か ``None``。"""
    tp = os.path.join(folder, TYPE_FILE)
    typ = jload(read_bytes(tp))
    i = mix_row_index(typ["rows"])
    if i is None:
        return None
    typ["rows"][i]["target"] = TARGET_IND
    write_bytes(tp, jdump(typ))
    index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
    n = 0
    for item in index["htm"]:
        carry = jload(read_bytes(os.path.join(folder, item["carry"])))
        n += sum(1 for e in carry["F"] if e.get("row") == i)
        if carry["H"] is not None:
            n += sum(1 for h in carry["H"]["hidden"] if h.get("row") == i)
    return i, n


def mix_effect(base, mixed, count):
    u"""混ぜ物が効いたか: ``base``・``mixed`` は正規化した行の並び。``count`` 行が「次元の組が 1 つ増えた同じ行」に変わり、ほかが同じ。"""
    if base is None or mixed is None or not base:
        return False
    cb, cm = collections.Counter(base), collections.Counter(mixed)
    removed, added = list((cb - cm).elements()), list((cm - cb).elements())
    if len(removed) != count or len(added) != count or count < 1:
        return False
    extra = (AXIS_CONS, MEMBER_IND)
    rem = collections.Counter(removed)
    for a in added:
        if tuple(a[-2:]) != extra:
            return False
        key = tuple(a[:-2])
        if rem[key] < 1:
            return False
        rem[key] -= 1
    return True


def display_check(folder):
    u"""表示の字の検査: 型に入った空でない数の fact ごとに、型の値から書いた表示の字が本文の字と同じか。(掛けた数, 合った数)。型の folder だけを読む。"""
    index = jload(read_bytes(os.path.join(folder, INDEX_FILE)))
    typ = jload(read_bytes(os.path.join(folder, TYPE_FILE)))
    rows = typ["rows"]
    tried = ok = 0
    for item in index["htm"]:
        plain = read_bytes(os.path.join(folder, item["text"])).decode("utf-8")
        carry = jload(read_bytes(os.path.join(folder, item["carry"])))
        for e in carry["F"]:
            if "row" in e:
                r = rows[e["row"]]
                if r["kind"] == KIND_NUM and r["value"] != VALUE_NONE:
                    tried += 1
                    ok += 1 if display_text(r["value"], r["shift"], r["prec"]) == plain[e["start"]:e["end"]] else 0
        if carry["H"] is not None:
            for h in carry["H"]["hidden"]:
                if "row" in h:
                    r = rows[h["row"]]
                    if r["kind"] == KIND_NUM and r["value"] != VALUE_NONE:
                        tried += 1
                        ok += 1 if display_text(r["value"], r["shift"], r["prec"]) == h["text"] else 0
    return tried, ok


# ======================================================================================================
# 書類 1 本
def zero_rec():
    def two():
        return od([(KIND_NUM, 0), (KIND_TEXT, 0)])
    return od([
        (u"断った", False), (u"断った段", u""), (u"断った理由", u""),
        (u"対象の fact", od([(KIND_NUM, 0), (KIND_TEXT, 0), (u"隠し", 0), (u"脚注", 0)])),
        (u"型に入った fact", two()),
        (u"型の外の fact", od([(u"理由ごと", od((r, two()) for r in REASONS)), (u"合計", two())])),
        (u"型の行", od([(KIND_NUM, 0), (KIND_TEXT, 0), (u"2 つ以上の fact をまとめた行", 0), (u"値が -0 の行", 0)])),
        (u"対応表の行", od([(u"科目", 0), (u"軸", 0), (u"member", 0), (u"_cor で終わらない名", 0)])),
        (u"持ち込みの属性を持つ fact", od([(KIND_NUM, 0), (KIND_TEXT, 0), (u"属性ごと", od())])),
        (u"文脈の定義", od([(u"作った", 0), (u"作らなかった", 0)])),
        (u"単位の定義", od([(u"作った", 0), (u"作らなかった", 0)])),
        (u"比べ方 1", od([(u"属性が意味として同じ", False), (u"文脈の名も同じ", False), (u"違った fact", 0), (u"属性ごとの違った fact", od())])),
        (u"比べ方 2", od([(u"組めた", False), (u"fact が意味として同じ", False), (u"字も含めて行が同じ", False), (u"鳴り方が同じ", False), (u"2 回が同じ", False)])),
        (u"混ぜ物", od([(u"作れた", False), (u"効いた", False)])),
        (u"表示の字の検査", od([(u"掛けた fact", 0), (u"合った fact", 0)])),
        (u"秒", od([(u"型から作る命令", None)])),
    ])


def fill_type_stats(rec, an):
    facts = an["facts"]
    for f in facts:
        k = KIND_NUM if f["isnum"] else KIND_TEXT
        rec[u"対象の fact"][k] += 1
        if f["where"] == "H":
            rec[u"対象の fact"][u"隠し"] += 1
        if f["reasons"]:
            rec[u"型の外の fact"][u"合計"][k] += 1
            for r in f["reasons"]:
                rec[u"型の外の fact"][u"理由ごと"][r][k] += 1
        else:
            rec[u"型に入った fact"][k] += 1
            c = carried_attrs(f)
            if c:
                rec[u"持ち込みの属性を持つ fact"][k] += 1
                for name in c:
                    rec[u"持ち込みの属性を持つ fact"][u"属性ごと"][name] = rec[u"持ち込みの属性を持つ fact"][u"属性ごと"].get(name, 0) + 1
    rec[u"持ち込みの属性を持つ fact"][u"属性ごと"] = od(sorted(rec[u"持ち込みの属性を持つ fact"][u"属性ごと"].items()))
    for r in an["rows"]:
        rec[u"型の行"][r["kind"]] += 1
        rec[u"型の行"][u"2 つ以上の fact をまとめた行"] += 1 if r["count"] >= 2 else 0
        rec[u"型の行"][u"値が -0 の行"] += 1 if r["value"] == u"-0" else 0
    maps, _inv = code_maps(an["rows"])
    for kind in (u"科目", u"軸", u"member"):
        rec[u"対応表の行"][kind] = len(maps[kind])
        rec[u"対応表の行"][u"_cor で終わらない名"] += sum(1 for n in maps[kind].values() if not (n.split(":", 1)[0] if ":" in n else "").endswith("_cor"))


def fill_footnotes(rec, files):
    rec[u"対象の fact"][u"脚注"] = sum(1 for x in files for e in x[2] if e["kind"] == "footnote")


def built_ids(an):
    u"""型の行から作る文脈・単位の id の集まり(型の外で写すものは含めない)。"""
    dec = an["dec"]
    cids, uids = set(), set()
    for r in an["rows"]:
        members = list(r["dims"]) + ([(AXIS_CONS, MEMBER_IND)] if r["target"] == TARGET_IND else [])
        cids.add(context_id(period_name(r["pkind"], r["period"], dec), r["pkind"], members))
        if r["kind"] == KIND_NUM:
            uids.add(unit_from_form(r["unit"])[0])
    return cids, uids


def fill_definition_stats(rec, orig_files, new_files, an):
    u"""作った定義の数と、元に在って作らなかった定義の数(中身(id を除く)が、作った側にも型の外で写した側にも無いもの。作った側の定義は型の外で写したものを含む)。"""
    oc, ou = context_view([x[3] for x in orig_files])
    nc, nu = context_view([x[3] for x in new_files])
    cids, uids = built_ids(an)
    new_ctx = set(canon_ctx(c) for c in nc.values())
    new_unit = set(canon_unit(u) for u in nu.values())
    rec[u"文脈の定義"][u"作った"], rec[u"単位の定義"][u"作った"] = len(cids), len(uids)
    rec[u"文脈の定義"][u"作らなかった"] = len([c for c in oc.values() if canon_ctx(c) not in new_ctx])
    rec[u"単位の定義"][u"作らなかった"] = len([u for u in ou.values() if canon_unit(u) not in new_unit])


def decline(rec, stage, reason):
    rec[u"断った"], rec[u"断った段"], rec[u"断った理由"] = True, stage, reason
    return rec


def load_manuscript(folder):
    u"""組んだ原稿の folder → [(名, 素の本文, 表 F, 表 H)]。"""
    index = jload(read_bytes(os.path.join(folder, P.INDEX_FILE)))
    return P.load_htm_tables(folder, index)


def process_doc(tool, zip_path, tmp_root=None, runner=None, proc=None, keep=None):
    u"""書類 1 本。書類ごとの数。元の包みと組み直した包みを同じ掛け方で 1 回ずつ。``keep`` が在れば型の folder と組んだ原稿をそこへ残す。"""
    entries = B.load_package(zip_path)
    rec = zero_rec()
    d = tempfile.mkdtemp(prefix="xm0_", dir=tmp_root)
    try:
        orig_zip = os.path.join(d, "orig.zip")
        B.write_package(entries, orig_zip)
        orig, oh, orows = run_facts(tool, orig_zip, d, "orig", runner)
        cwd = os.path.join(d, "cwd")
        os.makedirs(cwd)
        tf = os.path.join(d, "type")
        try:
            an, files = derive_folder(entries, tf)
        except Refuse as exc:
            return decline(rec, STAGES[0], exc.reason)
        except Exception:                                  # noqa: BLE001
            return decline(rec, STAGES[0], u"型を作る途中の例外")
        fill_type_stats(rec, an)
        fill_footnotes(rec, files)
        rec[u"表示の字の検査"][u"掛けた fact"], rec[u"表示の字の検査"][u"合った fact"] = display_check(tf)
        if carry_forbidden(tf):
            raise Stop(u"**型の folder の持ち込みに入れないものが在る。止める**")
        out1 = os.path.join(d, "man1")
        ok, reason, secs = exec_make(tf, out1, cwd, proc)
        rec[u"秒"][u"型から作る命令"] = round(secs, 1)
        if not ok:
            return decline(rec, STAGES[1], reason)
        new_files = load_manuscript(out1)
        a1, names_same, ndiff, per = compare_attrs(files, new_files)
        rec[u"比べ方 1"] = od([(u"属性が意味として同じ", bool(a1)), (u"文脈の名も同じ", bool(names_same)), (u"違った fact", ndiff), (u"属性ごとの違った fact", per)])
        fill_definition_stats(rec, files, new_files, an)
        if keep:
            shutil.copytree(tf, os.path.join(keep, "type"))
            shutil.copytree(out1, os.path.join(keep, "manuscript"))
        out2 = os.path.join(d, "man2")
        ok2, _r2, _s2 = exec_make(tf, out2, cwd, proc)
        tree_same = bool(ok2 and P.read_tree(out2) == P.read_tree(out1))
        b1 = os.path.join(d, "pack1")
        okb, reason, _sb = P.exec_build(out1, b1, cwd, proc)
        if not okb:
            return decline(rec, STAGES[2], reason)
        tree = P.read_tree(b1)
        if set(tree) != P.expected_names(jload(read_bytes(os.path.join(out1, P.INDEX_FILE)))):
            return decline(rec, STAGES[2], u"出す folder の file の名が目次と合わない")
        b2 = os.path.join(d, "pack2")
        okb2, _rb2, _sb2 = P.exec_build(out2, b2, cwd, proc) if ok2 else (False, u"", 0)
        rec[u"比べ方 2"][u"2 回が同じ"] = bool(tree_same and okb2 and P.read_tree(b2) == tree)
        new_zip = os.path.join(d, "new.zip")
        B.write_package(P.rebuilt_pack(entries, tree), new_zip)
        new, nh, nrows = run_facts(tool, new_zip, d, "new", runner)
        if new[u"類"] == V.CLS_STOPPED and orig[u"類"] != V.CLS_STOPPED:
            return decline(rec, STAGES[3], u"道具が組み直した包みで止まった")
        om = normalize_rows(oh, orows, unit_map_of(files))
        nm = normalize_rows(nh, nrows, unit_map_of(new_files))
        c2 = rec[u"比べ方 2"]
        c2[u"組めた"] = True
        c2[u"fact が意味として同じ"] = bool(om and nm and om == nm)
        c2[u"字も含めて行が同じ"] = B.facts_same(sorted(orows), sorted(nrows))
        c2[u"鳴り方が同じ"] = B.sounds_same(orig, new)
        # 混ぜ物
        mf = os.path.join(d, "mixtype")
        shutil.copytree(tf, mf)
        mixed = mix_folder(mf)
        if mixed is not None:
            mo = os.path.join(d, "mixman")
            okm, _rm, _sm = exec_make(mf, mo, cwd, proc)
            if okm:
                mb = os.path.join(d, "mixpack")
                okmb, _rmb, _smb = P.exec_build(mo, mb, cwd, proc)
                if okmb:
                    mtree = P.read_tree(mb)
                    if set(mtree) == P.expected_names(jload(read_bytes(os.path.join(mo, P.INDEX_FILE)))):
                        mz = os.path.join(d, "mix.zip")
                        B.write_package(P.rebuilt_pack(entries, mtree), mz)
                        _one, mh, mrows = run_facts(tool, mz, d, "mix", runner)
                        mm = normalize_rows(mh, mrows, unit_map_of(load_manuscript(mo)))
                        rec[u"混ぜ物"][u"作れた"] = True
                        rec[u"混ぜ物"][u"効いた"] = mix_effect(nm, mm, mixed[1])
        return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)


# ======================================================================================================
# 数える(封 §2)
def sum_nested(items):
    u"""同じ形の dict の並び → 数(bool・int)の合計の dict。字・None は数えない。"""
    first = items[0] if items else None
    if isinstance(first, dict):
        keys = []
        for it in items:
            for k in it:
                if k not in keys:
                    keys.append(k)
        out = od()
        for k in keys:
            vals = [it[k] for it in items if k in it]
            if any(isinstance(v, dict) for v in vals):
                out[k] = sum_nested([v for v in vals if isinstance(v, dict)])
            elif any(isinstance(v, (bool, int)) for v in vals):
                out[k] = sum(int(v) for v in vals if isinstance(v, (bool, int)))
        return out
    return od()


def group_totals(entries):
    u"""書類ごとの数の並び → §2 の数。"""
    body = [od((k, v) for k, v in e.items() if k not in (u"番号", u"断った段", u"断った理由", u"秒")) for e in entries]
    tot = sum_nested(body) if body else od()
    reasons = collections.Counter((e[u"断った段"], e[u"断った理由"]) for e in entries if e[u"断った"])
    stage = od((s, od(sorted((r, n) for (st, r), n in reasons.items() if st == s))) for s in STAGES)
    zero_out = sum(1 for e in entries if not e[u"断った"] and e[u"型の外の fact"][u"合計"][KIND_NUM] + e[u"型の外の fact"][u"合計"][KIND_TEXT] == 0)
    out = od([(u"書類", len(entries)), (u"断った書類", sum(1 for e in entries if e[u"断った"])), (u"断った段と理由ごと", stage), (u"型の外の fact が 0 の書類", zero_out)])
    out[u"数"] = tot
    out[u"作らなかった文脈の定義が 1 つ以上在る書類"] = sum(1 for e in entries if e[u"文脈の定義"][u"作らなかった"] >= 1)
    out[u"型から作る命令の秒の合計"] = round(sum(e[u"秒"][u"型から作る命令"] or 0 for e in entries), 1)
    return out


def totals_of(per_doc, dev_count=DEV_COUNT):
    dev, prod = per_doc[:dev_count], per_doc[dev_count:]
    return od([(u"開発の 5 本", group_totals(dev)), (u"本番だけの %d 本" % (len(per_doc) - dev_count), group_totals(prod)), (u"全部", group_totals(per_doc))])


def judged(tot, n=DOCS_WANT):
    u"""封 §4 の判定に要る数(当たり・外れは書かない)。"""
    prod = tot[[k for k in tot if k.startswith(u"本番だけの")][0]]
    z = prod[u"数"]
    out_tot = z[u"型の外の fact"][u"合計"]
    in_tot = z[u"型に入った fact"]
    tgt = z[u"対象の fact"]
    reasons = od((r, z[u"型の外の fact"][u"理由ごと"][r][KIND_NUM] + z[u"型の外の fact"][u"理由ごと"][r][KIND_TEXT]) for r in REASONS)
    mix = z[u"混ぜ物"]
    return od([
        (u"XM0-1 fact が意味として同じ書類", od([(u"書類", z[u"比べ方 2"][u"fact が意味として同じ"]), (u"分母", prod[u"書類"])])),
        (u"XM0-2 型の外の fact が 0 の書類", od([(u"書類", prod[u"型の外の fact が 0 の書類"]), (u"分母", prod[u"書類"])])),
        (u"XM0-3 型の外の fact", od([(u"fact", out_tot[KIND_NUM] + out_tot[KIND_TEXT]), (u"分母(対象の fact)", tgt[KIND_NUM] + tgt[KIND_TEXT])])),
        (u"XM0-4 型の外の理由ごとの fact", reasons),
        (u"XM0-5 文脈の名も同じ書類", od([(u"書類", z[u"比べ方 1"][u"文脈の名も同じ"]), (u"分母", prod[u"書類"])])),
        (u"XM0-6 作らなかった文脈の定義が 1 つ以上在る書類", od([(u"書類", prod[u"作らなかった文脈の定義が 1 つ以上在る書類"]), (u"分母", prod[u"書類"])])),
        (u"XM0-7 鳴り方が同じ書類", od([(u"書類", z[u"比べ方 2"][u"鳴り方が同じ"]), (u"分母", prod[u"書類"])])),
        (u"XM0-8 混ぜ物が効いた書類", od([(u"効いた", mix[u"効いた"]), (u"作れた", mix[u"作れた"])])),
        (u"XM0-9 数の型の行", od([(u"行", z[u"型の行"][KIND_NUM]), (u"分母(型に入った数の fact)", in_tot[KIND_NUM])])),
        (u"XM0-10 表示の字が合った fact", od([(u"合った", z[u"表示の字の検査"][u"合った fact"]), (u"分母(掛けた fact)", z[u"表示の字の検査"][u"掛けた fact"])]))])


# ======================================================================================================
# 道具の確かめ・記録
def check_tool(tool, runner=None, sha_reader=sha256_file, want_version=TOOL_VERSION, want_sha=SHA_P):
    return T.check_tool(tool, runner, sha_reader, want_version, want_sha)


def dev_docs(docs_dir, count=DEV_COUNT):
    u"""置き場の並びの頭から ``count`` 本だけを選ぶ(残りの zip は開かない)。"""
    return B.dev_docs(docs_dir, count)


def build_record(tool_p, docs_dir=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, dev_count=DEV_COUNT, proc=None, progress=None, keep=None):
    u"""道具を確かめてから、書類を 1 本ずつ掛ける。(記録, secret)。書かない。"""
    docs = W.select_docs(docs_dir or DOCS_DIR, want)
    info = check_tool(tool_p, runner, sha_reader, want_version, want_sha)
    per_doc = []
    elems, labels = set(), set()
    for n, (_stem, p, _xs) in enumerate(docs, 1):
        t0 = time.time()
        kdir = None
        if keep:
            kdir = os.path.join(keep, "doc%02d" % n)
            os.makedirs(kdir)
        r = process_doc(tool_p, p, tmp_root, runner, proc=proc, keep=kdir)
        per_doc.append(od([(u"番号", n)] + list(r.items())))
        el, lb = T.secret_of([B.load_package(p)])
        elems |= el
        labels |= lb
        if progress is not None:
            progress(u"doc %d/%d(%.0f 秒)" % (n, len(docs), time.time() - t0))
    ecodes = set()
    for _stem, _p, xs in docs:
        for x in xs:
            ecodes.update(re.findall(r"E\d{5}", x))
    secret = (labels, elems, [d[0] for d in docs], ecodes, set())
    return assemble(per_doc, W.order_sha256([d[0] for d in docs]), info, dev_count), secret


def assemble(per_doc, order_sha, info, dev_count=DEV_COUNT):
    tot = totals_of(per_doc, dev_count)
    rec = od()
    rec[u"seal"] = SEAL_REL
    rec[u"封の commit"] = SEAL_COMMIT
    rec[u"step"] = u"XM0(機械の側が決めた入力の型(第 0 版)と対応表だけから fact の属性と文脈・単位の定義を作ると、公開の道具が読む fact は元と意味として同じになるか。型に入らない fact は何か)(0 USD・engine は読まない)"
    rec[u"この script の sha256"] = sha256_file(os.path.abspath(__file__))
    rec[u"材料"] = od([
        (u"書類の本数", len(per_doc)), (u"書類の file 名の並びの sha256", order_sha), (u"開発の 5 本の番号", list(range(1, dev_count + 1))),
        (u"道具の版", info[u"版"]), (u"道具 P の ModelValue.py の sha256", info[u"ModelValue.py の sha256"]), (u"道具 P の package の一覧の sha256", info[u"package の一覧の sha256"]),
        (u"Python の版(道具 P)", info[u"Python の版"]), (u"規則の年", YEAR), (u"混ぜ物の種類", [MIX_KIND]), (u"時間の上限(秒)", TIMEOUT_SEC)])
    rec[u"script の決めの字"] = od([
        (u"型の外の理由", list(REASONS)), (u"単位の形", [u"通貨:XXX", UNIT_SHARES, UNIT_PURE, u"通貨:XXX÷株"]), (u"format", FORMAT_OK), (u"桁あふれの守り", MAX_EXP),
        (u"期の名", [PERIOD_CUR, PERIOD_FILING, u"Prior<N>Year"]), (u"書類の決めの id の頭", [ID_END, ID_START, ID_FILING])])
    rec[u"書類"] = per_doc
    rec[u"集計"] = tot
    rec[u"予測の判定に要る数(XM0-1〜XM0-10。当たり・外れは結果の文書で)"] = judged(tot, len(per_doc))
    rec[u"限界"] = list(LIMITS)
    return rec


def check_clean(rec, text, secret=None):
    u"""記録に書かないもの(docID・EDINET コード・file の名・要素の名・文脈の名・本文の字・URI)が無いか。在れば止める。"""
    T.check_clean(rec, text, secret)


def verify_record(rec, text=None, want=DOCS_WANT, dev_count=DEV_COUNT):
    u"""記録の形・合計・禁止のものを検査する(道具は呼ばない・掛け直さない)。違えば止まる。"""
    docs = rec.get(u"書類")
    if not isinstance(docs, list) or len(docs) != want or rec[u"材料"][u"書類の本数"] != want:
        raise Stop(u"**記録の書類が 67 本でない。止める**")
    shape = list(zero_rec())
    for i, d in enumerate(docs, 1):
        if d.get(u"番号") != i or list(d)[1:] != shape:
            raise Stop(u"**記録の書類の形が違う。止める**")
        if d[u"断った"] != bool(d[u"断った段"]) or d[u"断った"] != bool(d[u"断った理由"]) or (d[u"断った"] and d[u"断った段"] not in STAGES):
            raise Stop(u"**断った書類の形が違う。止める**")
        if d[u"断った"] and (d[u"比べ方 2"][u"fact が意味として同じ"] or d[u"混ぜ物"][u"効いた"]):
            raise Stop(u"**断った書類に比べ方 2・混ぜ物の結果が在る。止める**")
        o, t = d[u"型の外の fact"][u"合計"], d[u"型に入った fact"]
        for k in (KIND_NUM, KIND_TEXT):
            if o[k] + t[k] != d[u"対象の fact"][k]:
                raise Stop(u"**型に入った fact と型の外の fact の合計が対象の fact と合わない。止める**")
            if max(d[u"型の外の fact"][u"理由ごと"][r][k] for r in REASONS) > o[k]:
                raise Stop(u"**理由ごとの数が合計より多い。止める**")
        if d[u"混ぜ物"][u"効いた"] and not d[u"混ぜ物"][u"作れた"]:
            raise Stop(u"**作れなかった混ぜ物が効いた。止める**")
        if d[u"表示の字の検査"][u"合った fact"] > d[u"表示の字の検査"][u"掛けた fact"]:
            raise Stop(u"**表示の字の検査の数が合わない。止める**")
    tot = totals_of(docs, dev_count)
    if dumps(tot) != dumps(rec[u"集計"]) or dumps(judged(tot, len(docs))) != dumps(rec[[k for k in rec if k.startswith(u"予測の判定に要る数")][0]]):
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


def run(tool_p, root=ROOT, docs=None, out=None, want=DOCS_WANT, runner=None, sha_reader=sha256_file, tmp_root=None, want_version=TOOL_VERSION, want_sha=SHA_P, say=print, dev_count=DEV_COUNT, proc=None, progress=None, keep=None):
    rec, secret = build_record(tool_p, docs, want, runner, sha_reader, tmp_root, want_version, want_sha, dev_count, proc, progress, keep)
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


def dev_run(tool_p, docs_dir=None, runner=None, tmp_root=None, say=print, proc=None, keep=None):
    u"""開発の 5 本だけ(記録は書かない)。(書類ごとの数の並び)。"""
    docs = dev_docs(docs_dir or DOCS_DIR, DEV_COUNT)
    check_tool(tool_p, runner)
    per = []
    t_all = time.time()
    for n, (_s, p, _x) in enumerate(docs, 1):
        t0 = time.time()
        kdir = None
        if keep:
            kdir = os.path.join(keep, "doc%02d" % n)
            os.makedirs(kdir)
        r = process_doc(tool_p, p, tmp_root, runner, proc=proc, keep=kdir)
        per.append(od([(u"番号", n)] + list(r.items())))
        say(u"doc %d(%.0f 秒): %s" % (n, time.time() - t0, json.dumps(r, ensure_ascii=False)))
    say(u"開発の 5 本の合計: %.0f 秒" % (time.time() - t_all))
    return per


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "make":
        sys.exit(make_main(argv[1:]))
    if argv and argv[0] == "derive":
        sys.exit(derive_main(argv[1:]))
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="記録の形・合計・禁止のものを検査する。道具は呼ばない")
    ap.add_argument("--dev", action="store_true", help="開発の 5 本だけ掛ける。記録は書かない")
    ap.add_argument("--tool-p", default=None, help="道具 P(1 行の直し)の venv の場所")
    ap.add_argument("--keep", default=None, help="書類ごとの型の folder と組んだ原稿を残す場所(空の場所)")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--docs", default=None, help="書類の置き場(既定は封の字)")
    a = ap.parse_args(argv)
    if a.check:
        check(root=a.root)
        return
    if not a.tool_p:
        raise Stop(u"**--tool-p が要る。止める**")
    if a.keep:
        os.makedirs(a.keep, exist_ok=True)
        if os.listdir(a.keep):
            raise Stop(u"**--keep の場所が空でない。止める**")
    if a.dev:
        dev_run(a.tool_p, docs_dir=a.docs, keep=a.keep)
        return
    run(a.tool_p, root=a.root, docs=a.docs, progress=lambda s: print(s, file=sys.stderr), keep=a.keep)


if __name__ == "__main__":
    main()
