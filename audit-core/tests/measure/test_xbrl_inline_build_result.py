# -*- coding: utf-8 -*-
u"""結果の門: 封 docs/XBRL_INLINE_BUILD_SEAL_2026-11-21.md(9c528c49)の結果の文書 docs/XBRL_INLINE_BUILD_RESULT_2026-11-21.md。

封の門 ``test_xbrl_inline_build_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(道具(Arelle)も置き場も読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封の sha256(字で留める)と、記録の script の sha256・封の commit の欄・記録の限界の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、3 群の集計・混ぜ物・予測の判定に要る数を数え直して記録と同じことを見る。
   書類ごとの「鳴り方が同じ」の旗は、元と組み直しの符号ごとの行から数え直す。「fact が同じ」の旗は、行の数が同じ(必要条件)までを数え直す
 c 予測 XB0-1〜XB0-7 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し、文書 §1 の表・件数と同じことを見る。
   封 §4 の自己点検の条・封 §6 の 2 つの決め(XB0-6 が外れたら・XB0-1 と XB0-6 がどちらも当たりなら)と文書が合う
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。
   §3 は記録に欄の無い読みの節で、数は字で留めた小さい集合だけ(その外の節に記録に無い数が漏れていない)
 e 文書の要点の字・頭の負けと限界・禁止語・「通る」「作れる」を肯定で書かない・docID と EDINET コードの形
 f 封・script・記録・封の門が commit の blob と一致(結果の便で 0 行)・engine は封の commit から 0 行・順序・文書が書く commit の字
この file は docID の字を持たない。
"""
import collections
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"
sys.path.insert(0, ROOT)


def load_module(rel, name):
    u"""importlib で読み込む。読み込みの前に居た名前は、読み込みの後に元の object へ戻す(自分の名前 ``name`` は残す)。"""
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        for k, v in before.items():
            if k != name and sys.modules.get(k) is not v:
                sys.modules[k] = v
    return mod


SG = load_module("tests/measure/test_xbrl_inline_build_seal.py", "xbrl_inline_build_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.load_helpers()
MS = SG.MS

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_inline_build_result.py"
DOC_REL = "docs/XBRL_INLINE_BUILD_RESULT_2026-11-21.md"
SCRIPT_COMMIT_SHORT = "82b44aef"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "288d7b6d"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "5f3924764e91f2837664fc105ae771f737646798d8387781e1734030531f9d1e"),
    (SCRIPT_REL, "03985ac79614e22ac028f543b6aa2e23c7e7c30e3bbb25de83e0aef753643bbf"),
    (SEAL_GATE_REL, "38d5be665d7ef2b23b11d72731da57ec33d74007d4a5d2e0200f40bddf3b6470"),
    (SEAL_REL, "9d1596c572ade846dd66877e9a241429b3f6ccf634270ee76614fe4c4ec3d6bc")])

CLASSES = (u"走った", u"止まった", u"走らなかった")
TAG_KINDS = (u"nonFraction", u"nonNumeric", u"footnote")
MIX_KINDS = (u"抜く", u"文脈を替える", u"符号を返す")
DEV_COUNT = 5
PRED_KEY = u"予測の判定に要る数(XB0-1〜XB0-7。当たり・外れは結果の文書で)"
PK = (u"XB0-1 fact が同じ書類", u"XB0-2 断った書類", u"XB0-3 鳴り方が同じ書類", u"XB0-4 ix:header を持たない file のうち字が同じもの",
      u"XB0-5 ix:header を持つ file のうち字が同じもの", u"XB0-6 混ぜ物のうち fact が同じでないもの", u"XB0-7 混ぜ物のうち鳴り方が元と違うもの")
GROUPS = (u"開発の 5 本", u"本番だけの 62 本", u"全部")
BOUND_SEAL_PHRASES = (u"56 本以上", u"4 本以下", u"50% 以上", u"10 本以下", u"15 個", u"5 個以下",
                      u"fact が同じ書類が 62 本で、字が同じ file が全部だったら、先に自分の欠陥を疑う",
                      u"XB0-6 が外れたら、XB0-1・XB0-3 は当たり外れを書いたうえで「比べ方が効いていない」と結果の頭に書く",
                      u"XB0-1 と XB0-6 がどちらも当たりなら、次の便の候補を人間に示す")
HEAD_PHRASES = (u"先に負けと限界を書く", u"当たり 4・外れ 3", u"外れは XB0-4・XB0-5・XB0-7", u"端の数(62/62)", u"「XBRL を作れる」を示していない",
                u"タグを決める力は測っていない", u"元の file のまま", u"原稿(Word など)ではない", u"司令塔が 1 行を直したもので、本家の版ではない",
                u"EDINET の本物の検査とは照らしていない", u"engine では読み戻していない", u"無作為ではない。有報だけ", u"この便からは言えない",
                u"LLM の席は呼んでいない", u"本番は 1 回だけ走らせた", u"元の書き方の跡が 1 つ残っている")
SEAL7_PHRASES = (u"タグを決める力は測っていない", u"元のまま", u"原稿(Word など)ではない", u"1 行を直したもの", u"無作為ではない。有報だけ", u"「EDINET の検査に通る」")
PHRASES = (u"測っていない", u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"記録に欄の無い読み", u"人間が決めること",
           u"62 本の全部を別の実装で掛け直してはいない", u"記録の 15 個の全部について書類ごとの符号の差を並べたものではない", u"比べる相手が同じ file になっていない",
           u"頭の部を持つ file の 30 本で字が違う理由は、記録に無く、分けていない", u"「検査が鳴らない」は「fact が抜けていない」を言わない")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
# 記録に欄の無い読み(§3)が持つ数。記録から導けないので字で留める(これ以外の数が §3 に在れば赤)。
SEC3_NUMBERS = (u"1", u"2", u"4", u"6", u"9", u"15", u"30", u"62", u"67")
STRUCTURAL = set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10"])


# ======================================================================================================
def read(rel, root=ROOT):
    with io.open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def sha_file(rel, root=ROOT):
    with open(os.path.join(root, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def guard(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as exc:                   # noqa: BLE001  変異で落ちた検査は「問題」として数える
        return [u"例外: %s" % type(exc).__name__]


class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


# ======================================================================================================
# b 数え直し(script の関数は使わない)
def sound_of(d):
    u"""元と組み直しの 1 回の類と符号ごとの行が同じか(断った書類は同じでない)。"""
    a, b = d[u"元の 1 回"], d[u"組み直しの 1 回"]
    if d[u"断った"] or b is None:
        return False
    return a[u"類"] == b[u"類"] and dict(a[u"符号ごとの行"]) == dict(b[u"符号ごとの行"])


def group_recount(docs):
    cls = collections.OrderedDict((c, 0) for c in CLASSES)
    files = collections.OrderedDict([(u"持たない", collections.OrderedDict([(u"数", 0), (u"字が同じ", 0)])), (u"持つ", collections.OrderedDict([(u"数", 0), (u"字が同じ", 0)]))])
    tags = collections.OrderedDict((k, 0) for k in TAG_KINDS)
    dec = fs = ss = rows = zero = 0
    reasons = collections.Counter()
    for d in docs:
        if d[u"断った"]:
            dec += 1
            reasons[d[u"断った理由"]] += 1
        else:
            cls[d[u"組み直しの 1 回"][u"類"]] += 1
        fs += 1 if d[u"fact が同じ"] else 0
        ss += 1 if d[u"鳴り方が同じ"] else 0
        rows += d[u"元の fact の行の数"]
        zero += 1 if d[u"元の fact の行の数"] == 0 else 0
        for k in (u"持たない", u"持つ"):
            for f in (u"数", u"字が同じ"):
                files[k][f] += d[u"字の file"][k][f]
        for k in TAG_KINDS:
            tags[k] += d[u"タグの数"][k]
    return collections.OrderedDict([
        (u"書類", len(docs)), (u"断った書類", dec), (u"断った理由ごと", collections.OrderedDict(sorted(reasons.items()))), (u"fact が同じ書類", fs), (u"鳴り方が同じ書類", ss),
        (u"組み直した包みの 1 回の類ごと", cls), (u"file", files), (u"元の fact の行の数の合計", rows), (u"元の fact の行が 0 の書類", zero), (u"ix のタグの数の合計", tags)])


def mix_recount(docs):
    n = made = fd = sd = 0
    for d in docs:
        for m in d[u"混ぜ物"]:
            n += 1
            made += 1 if m[u"作った"] else 0
            fd += 0 if m[u"fact が同じ"] else 1
            sd += 0 if m[u"鳴り方が同じ"] else 1
    return collections.OrderedDict([(u"混ぜ物の数", n), (u"作れた数", made), (u"fact が同じでない数", fd), (u"鳴り方が同じでない数", sd)])


def mix_by_kind(docs):
    u"""種類ごとの (作れた, fact が同じでない, 鳴り方が同じでない)。"""
    out = collections.OrderedDict((k, [0, 0, 0]) for k in MIX_KINDS)
    for d in docs:
        for m in d[u"混ぜ物"]:
            r = out[m[u"種類"]]
            r[0] += 1 if m[u"作った"] else 0
            r[1] += 0 if m[u"fact が同じ"] else 1
            r[2] += 0 if m[u"鳴り方が同じ"] else 1
    return out


def totals(rec):
    docs = rec[u"書類"]
    dev, prod = docs[:DEV_COUNT], docs[DEV_COUNT:]
    return collections.OrderedDict([(GROUPS[0], group_recount(dev)), (GROUPS[1], group_recount(prod)), (GROUPS[2], group_recount(docs)), (u"混ぜ物", mix_recount(dev))])


def pred_expected(tot):
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    nh, wh = prod[u"file"][u"持たない"], prod[u"file"][u"持つ"]

    def dn(k, x, y):
        return collections.OrderedDict([(k, x), (u"分母", y)])
    return collections.OrderedDict([
        (PK[0], dn(u"書類", prod[u"fact が同じ書類"], prod[u"書類"])), (PK[1], dn(u"書類", prod[u"断った書類"], prod[u"書類"])), (PK[2], dn(u"書類", prod[u"鳴り方が同じ書類"], prod[u"書類"])),
        (PK[3], dn(u"file", nh[u"字が同じ"], nh[u"数"])), (PK[4], dn(u"file", wh[u"字が同じ"], wh[u"数"])),
        (PK[5], dn(u"個", mx[u"fact が同じでない数"], mx[u"混ぜ物の数"])), (PK[6], dn(u"個", mx[u"鳴り方が同じでない数"], mx[u"混ぜ物の数"]))])


def judge(tot):
    u"""封 §4 の境と記録から XB0-1〜XB0-7 の当たり外れを決め直す。"""
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    nh, wh = prod[u"file"][u"持たない"], prod[u"file"][u"持つ"]
    out = collections.OrderedDict()
    out[u"XB0-1"] = prod[u"fact が同じ書類"] >= 56
    out[u"XB0-2"] = prod[u"断った書類"] <= 4
    out[u"XB0-3"] = prod[u"鳴り方が同じ書類"] >= 56
    out[u"XB0-4"] = nh[u"字が同じ"] * 2 >= nh[u"数"]
    out[u"XB0-5"] = wh[u"字が同じ"] <= 10
    out[u"XB0-6"] = mx[u"fact が同じでない数"] >= 15
    out[u"XB0-7"] = mx[u"鳴り方が同じでない数"] <= 5
    return out


def pct(a, b):
    return u"%.1f%%" % (100.0 * a / b)


def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    if c.rec[u"限界"] != MS.LIMITS:
        out.append(u"記録の限界の欄が script の字と違う")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, 68)) or rec[u"材料"][u"書類の本数"] != 67 or rec[u"材料"][u"開発の 5 本の番号"] != list(range(1, 6)):
        out.append(u"書類の番号・材料の書類の本数・開発の 5 本の番号が違う")
    if rec[u"材料"][u"混ぜ物の種類"] != list(MIX_KINDS):
        out.append(u"混ぜ物の種類が違う")
    for d in docs:
        n = d[u"番号"]
        if d[u"断った"] or d[u"組み直しの 1 回"] is None:
            out.append(u"書類 %d が断った" % n)
            continue
        for k in (u"元の 1 回", u"組み直しの 1 回"):
            e = d[k]
            nl = e[u"出力の行の数"]
            if e[u"類"] not in CLASSES or e[u"時間の上限を超えた"]:
                out.append(u"書類 %d の %s の類・時間の上限が違う" % (n, k))
            if not isinstance(nl, int) or isinstance(nl, bool) or nl < sum(e[u"符号ごとの行"].values()):
                out.append(u"書類 %d の %s の出力の行の数が指摘の行の数より少ない" % (n, k))
        if d[u"鳴り方が同じ"] != sound_of(d):
            out.append(u"書類 %d の鳴り方が同じの旗が符号ごとの行から数え直した値と違う" % n)
        if d[u"fact が同じ"] and (d[u"元の fact の行の数"] == 0 or d[u"元の fact の行の数"] != d[u"組み直しの fact の行の数"]):
            out.append(u"書類 %d は fact が同じなのに fact の行の数が違う・0 行" % n)
        if n <= DEV_COUNT and [m[u"種類"] for m in d[u"混ぜ物"]] != list(MIX_KINDS):
            out.append(u"書類 %d の混ぜ物の種類が違う" % n)
        if n > DEV_COUNT and d[u"混ぜ物"]:
            out.append(u"書類 %d に混ぜ物が在る(本番だけの書類は混ぜ物を持たない)" % n)
        for k in (u"持たない", u"持つ"):
            f = d[u"字の file"][k]
            if not 0 <= f[u"字が同じ"] <= f[u"数"]:
                out.append(u"書類 %d の字の file の数が違う" % n)
    tot = totals(rec)
    if json.loads(json.dumps(rec[u"集計"])) != json.loads(json.dumps(tot)):
        out.append(u"集計が書類ごとの数から数え直した値と違う")
    if json.loads(json.dumps(rec[PRED_KEY])) != json.loads(json.dumps(pred_expected(tot))):
        out.append(u"予測の判定に要る数が数え直しと違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        MS.check_clean(c.rec, text)
    except SystemExit:
        out.append(u"記録の検査(欄・形・file の名)が止める")
    if DOCID_FORM.search(re.sub(r"[0-9a-fA-F]{32,}", u"", text)) or ECODE_FORM.search(text):
        out.append(u"記録に docID か EDINET コードの形が在る")
    return out


def bound_problems(c):
    return [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]


def section(doc, head, nxt):
    i = doc.index(head)
    j = doc.index(nxt, i + len(head)) if nxt else len(doc)
    return doc[i:j]


# ======================================================================================================
def prod_stats(c):
    u"""本番だけの 62 本の、字が同じ file の分かれ方・fact の行の最小と最大。"""
    prod = c.rec[u"書類"][DEV_COUNT:]
    allsame = nonesame = part = 0
    for d in prod:
        f = d[u"字の file"]
        n = f[u"持たない"][u"数"] + f[u"持つ"][u"数"]
        s = f[u"持たない"][u"字が同じ"] + f[u"持つ"][u"字が同じ"]
        if s == n:
            allsame += 1
        elif s == 0:
            nonesame += 1
        else:
            part += 1
    rows = [d[u"元の fact の行の数"] for d in prod]
    return allsame, nonesame, part, min(rows), max(rows)


def expected_verdict_cells(c):
    tot = totals(c.rec)
    j = judge(tot)
    prod, mx = tot[GROUPS[1]], tot[u"混ぜ物"]
    nh, wh = prod[u"file"][u"持たない"], prod[u"file"][u"持つ"]
    actual = {u"XB0-1": u"%d/%d" % (prod[u"fact が同じ書類"], prod[u"書類"]), u"XB0-2": u"%d/%d" % (prod[u"断った書類"], prod[u"書類"]),
              u"XB0-3": u"%d/%d" % (prod[u"鳴り方が同じ書類"], prod[u"書類"]), u"XB0-4": u"%d/%d(%s)" % (nh[u"字が同じ"], nh[u"数"], pct(nh[u"字が同じ"], nh[u"数"])),
              u"XB0-5": u"%d/%d" % (wh[u"字が同じ"], wh[u"数"]), u"XB0-6": u"%d/%d" % (mx[u"fact が同じでない数"], mx[u"混ぜ物の数"]),
              u"XB0-7": u"%d/%d" % (mx[u"鳴り方が同じでない数"], mx[u"混ぜ物の数"])}
    lower_bound = (u"XB0-1", u"XB0-3", u"XB0-4", u"XB0-6")                   # 「以上」の境。外れは下に外れる。残りは「以下」の境で上に外れる
    edge = {u"XB0-1": prod[u"fact が同じ書類"] == prod[u"書類"], u"XB0-3": prod[u"鳴り方が同じ書類"] == prod[u"書類"]}
    cells = collections.OrderedDict()
    for k in j:
        if j[k]:
            cell = u"当たり(端の数)" if edge.get(k) else u"当たり"
        else:
            cell = u"**外れ**(%s)" % (u"下に外れた" if k in lower_bound else u"上に外れた")
        cells[k] = (actual[k], cell)
    return cells


def verdict_problems(c):
    tot = totals(c.rec)
    j = judge(tot)
    want = expected_verdict_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XB0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XB0-1〜XB0-7 でない"]
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    hits = sum(1 for v in j.values() if v)
    if u"- 当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"当たり %d・外れ %d" % (hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    misses = u"・".join(k for k, v in j.items() if not v)
    if u"外れは %s。" % misses not in head:
        out.append(u"文書の頭の外れの名が決め直した外れと違う")
    sec1, sec5 = section(c.doc, u"## §1 ", u"## §2 "), section(c.doc, u"## §5 ", None)
    # 封 §6: XB0-6 が外れたら「比べ方が効いていない」を頭に書く / 当たりなら書かない
    if j[u"XB0-6"]:
        if u"比べ方が効いていない" in head or u"XB0-6 が当たりなので、封 §6 の「比べ方が効いていない」は書かない" not in sec1:
            out.append(u"XB0-6 が当たりなのに、封 §6 の「比べ方が効いていない」の扱いが文書と合わない")
    elif u"比べ方が効いていない" not in head:
        out.append(u"XB0-6 が外れたのに、頭に「比べ方が効いていない」が無い")
    # 封 §6: XB0-1 と XB0-6 がどちらも当たりなら次の便の候補を示す
    both = j[u"XB0-1"] and j[u"XB0-6"]
    if both != (u"人間に示す次の便の候補(封 §6。XB0-1 と XB0-6 がどちらも当たりなので示す)" in sec5):
        out.append(u"封 §6 の決め(XB0-1 と XB0-6 がどちらも当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if both and not (u"(i) 提出者別タクソノミ" in sec5 and u"(ii) 組む部品で書類を 1 か所だけ壊し" in sec5):
        out.append(u"§5 の次の便の候補 (i)(ii) が封 §6 の字と違う")
    # 封 §4 の自己点検の条
    prod = tot[GROUPS[1]]
    allsame = prod[u"file"][u"持たない"][u"字が同じ"] + prod[u"file"][u"持つ"][u"字が同じ"]
    allfile = prod[u"file"][u"持たない"][u"数"] + prod[u"file"][u"持つ"][u"数"]
    fired = (prod[u"fact が同じ書類"] == 62 and allsame == allfile) or prod[u"元の fact の行が 0 の書類"] > 0
    if fired:
        out.append(u"封 §4 の自己点検の条(fact が同じ書類が 62 本で字が同じ file が全部・fact の行が 0 の書類)が発火している")
    if u"字が同じ file は全部ではない(%d/%d)ので、字のうえでは発火しない" % (allsame, allfile) not in c.doc:
        out.append(u"文書の自己点検の言い切り(字のうえでは発火しない)が記録の数と合わない")
    if u"「元の包みの fact の行が 0 の書類」は %d 本で、発火しない" % prod[u"元の fact の行が 0 の書類"] not in c.doc:
        out.append(u"文書の自己点検の言い切り(fact の行が 0 の書類)が記録の数と合わない")
    return out


# ======================================================================================================
def expected_lines(c):
    tot = totals(c.rec)
    out = []
    for name in (GROUPS[1], GROUPS[0], GROUPS[2]):
        t = tot[name]
        nh, wh = t[u"file"][u"持たない"], t[u"file"][u"持つ"]
        out.append(u"| %s | %d | %d | %d | %d | %d | %d / %d | %d / %d | %d |" % (
            name, t[u"書類"], t[u"断った書類"], t[u"fact が同じ書類"], t[u"鳴り方が同じ書類"], t[u"組み直した包みの 1 回の類ごと"][u"走った"],
            nh[u"字が同じ"], nh[u"数"], wh[u"字が同じ"], wh[u"数"], t[u"元の fact の行の数の合計"]))
    for kind, (made, fd, sd) in mix_by_kind(c.rec[u"書類"][:DEV_COUNT]).items():
        out.append(u"| %s | %d | %d | %d |" % (kind, made, fd, sd))
    return out


def expected_fragments(c):
    rec = c.rec
    tot = totals(rec)
    docs = rec[u"書類"]
    prod, allg, mx = tot[GROUPS[1]], tot[GROUPS[2]], tot[u"混ぜ物"]
    nh, wh = prod[u"file"][u"持たない"], prod[u"file"][u"持つ"]
    allsame, nonesame, part, rmin, rmax = prod_stats(c)
    kinds = mix_by_kind(docs[:DEV_COUNT])
    tg, tp = allg[u"ix のタグの数の合計"], prod[u"ix のタグの数の合計"]
    not_run = sum(1 for d in docs for k in (u"組み直しの 1 回",) if d[k][u"類"] != u"走った")
    over = sum(1 for d in docs for k in (u"元の 1 回", u"組み直しの 1 回") if d[k][u"時間の上限を超えた"])
    f = []
    f.append(u"外れ 3" if False else u"当たり 4・外れ 3")
    f.append(u"頭の部を持たないfile" if False else u"頭の部を持たない file のうち字が同じものは %d/%d(%s)で、予測の下の境(50%%)に届かなかった" % (nh[u"字が同じ"], nh[u"数"], pct(nh[u"字が同じ"], nh[u"数"])))
    f.append(u"頭の部を持つ file のうち字が同じものは %d/%d で、予測の上の境(10 本)を超えた" % (wh[u"字が同じ"], wh[u"数"]))
    f.append(u"鳴り方が元と違ったのは %d 個で、予測の上の境(5 個)を超えた" % mx[u"鳴り方が同じでない数"])
    f.append(u"混ぜ物 %d 個のうち" % mx[u"混ぜ物の数"])
    f.append(u"**主の予測 XB0-1 は当たりだが、端の数(%d/%d)。**" % (prod[u"fact が同じ書類"], prod[u"書類"]))
    f.append(u"fact が同じ書類は本番だけの %d 本の全部、鳴り方が同じ書類も %d 本の全部、断った書類は %d" % (prod[u"fact が同じ書類"], prod[u"鳴り方が同じ書類"], prod[u"断った書類"]))
    f.append(u"fact が同じ書類は %d 本だが字が同じ file は全部ではない(%d/%d)" % (prod[u"fact が同じ書類"], nh[u"字が同じ"] + wh[u"字が同じ"], nh[u"数"] + wh[u"数"]))
    f.append(u"組み直した包みの 1 回が止まった・走らなかった書類は %d。時間の上限(%d 秒)を超えた回は %d" % (not_run, rec[u"材料"][u"時間の上限(秒)"], over))
    f.append(u"`ix:nonFraction` %d・`ix:nonNumeric` %d・`ix:footnote` %d(封 §0 で字で数えた数と同じ)" % tuple(tg[k] for k in TAG_KINDS))
    f.append(u"本番だけの 62 本では %d・%d・%d" % tuple(tp[k] for k in TAG_KINDS))
    f.append(u"最も少ない書類で %d・最も多い書類で %d" % (rmin, rmax))
    f.append(u"全部が元と bytes で同じ書類が %d 本・1 つも同じでない書類が %d 本・一部だけ同じ書類が %d 本" % (allsame, nonesame, part))
    f.append(u"混ぜ物(開発の 5 本 × 3 種類 = %d 個。作れた数は %d)" % (mx[u"混ぜ物の数"], mx[u"作れた数"]))
    f.append(u"(頭の部を持たない file で %s)" % pct(nh[u"字が同じ"], nh[u"数"]))
    f.append(u"fact が元と同じだった書類は %d 本・検査の鳴り方が同じだった書類は %d 本" % (prod[u"fact が同じ書類"], prod[u"鳴り方が同じ書類"]))
    f.append(u"組み方を決めた 5 本を足した %d 本でも、どちらも %d 本" % (allg[u"fact が同じ書類"], allg[u"鳴り方が同じ書類"]))
    f.append(u"fact の比べは 3 種類の 1 か所の違いを %d 個の全部で見つけた" % mx[u"fact が同じでない数"])
    f.append(u"文脈の取り違えと符号の逆は %d 個の全部で鳴り方が変わり、fact を 1 つ抜いたものは %d 個の全部で鳴り方が変わらなかった" % (
        kinds[MIX_KINDS[1]][2] + kinds[MIX_KINDS[2]][2], mx[u"混ぜ物の数"] // 3 - kinds[MIX_KINDS[0]][2]))
    f.append(u"頭の部を持つ file の %d 本で字が違う理由は、記録に無く、分けていない" % (wh[u"数"] - wh[u"字が同じ"]))
    return f


def sanity_problems(c):
    u"""文書の言い切りが書類ごとの数に合う: 頭の部を持つ file は各書類に 1 つ・3 file に 2 file が元と違う・混ぜ物の 5/5/0・5/5/5・5/5/5・「10 個」「5 個」。"""
    rec = c.rec
    tot = totals(rec)
    prod = tot[GROUPS[1]]
    nh = prod[u"file"][u"持たない"]
    out = []
    if any(d[u"字の file"][u"持つ"][u"数"] != 1 for d in rec[u"書類"]):
        out.append(u"頭の部を持つ file が各書類に 1 つずつでない")
    diff = float(nh[u"数"] - nh[u"字が同じ"]) / nh[u"数"]
    if abs(diff - 2.0 / 3.0) > 0.02:
        out.append(u"「3 file に 2 file は元と bytes では違う」が記録の数と合わない(%.3f)" % diff)
    kinds = mix_by_kind(rec[u"書類"][:DEV_COUNT])
    if [kinds[k] for k in MIX_KINDS] != [[5, 5, 0], [5, 5, 5], [5, 5, 5]]:
        out.append(u"混ぜ物の種類ごとの数が 5/5/0・5/5/5・5/5/5 でない")
    if (kinds[MIX_KINDS[1]][2] + kinds[MIX_KINDS[2]][2], kinds[MIX_KINDS[0]][2]) != (10, 0):
        out.append(u"文脈と符号で鳴り方が変わる 10 個・抜くで変わらない 5 個が記録と合わない")
    allsame, nonesame, part, rmin, rmax = prod_stats(c)
    if (allsame, nonesame, part, rmin, rmax) != (31, 30, 1, 640, 2068):
        out.append(u"本番だけの 62 本の分かれ方・fact の行の最小と最大が文書の言う数と違う")
    if (nh[u"字が同じ"], nh[u"数"], prod[u"file"][u"持つ"][u"字が同じ"], prod[u"file"][u"持つ"][u"数"]) != (280, 865, 32, 62) or pct(280, 865) != u"32.4%":
        out.append(u"32.4%(280/865)・32/62 が記録と合わない")
    if (tot[GROUPS[1]][u"file"][u"持たない"][u"字が同じ"] + tot[GROUPS[1]][u"file"][u"持つ"][u"字が同じ"],
            tot[GROUPS[1]][u"file"][u"持たない"][u"数"] + tot[GROUPS[1]][u"file"][u"持つ"][u"数"]) != (312, 927):
        out.append(u"312/927 が記録と合わない")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    return out


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"XB0-\d", u" ", s)
    s = re.sub(r"EC\d{4}[A-Z]", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def ints_in(o, acc):
    if isinstance(o, dict):
        for v in o.values():
            ints_in(v, acc)
    elif isinstance(o, list):
        for v in o:
            ints_in(v, acc)
    elif isinstance(o, int) and not isinstance(o, bool):
        acc.add(str(o))


def derived_numbers(c):
    tot = totals(c.rec)
    out = set()
    ints_in(tot, out)
    ints_in(pred_expected(tot), out)
    allsame, nonesame, part, rmin, rmax = prod_stats(c)
    out |= set(str(x) for x in (allsame, nonesame, part, rmin, rmax, 3 * 5, 50, 56, 4, 10, 5, 15, 62, 67, 600))
    out.add(str(c.rec[u"材料"][u"時間の上限(秒)"]))
    prod = tot[GROUPS[1]]
    nh, wh = prod[u"file"][u"持たない"], prod[u"file"][u"持つ"]
    out.add(pct(nh[u"字が同じ"], nh[u"数"])[:-1])
    out.add(str(nh[u"字が同じ"] + wh[u"字が同じ"]))
    out.add(str(nh[u"数"] + wh[u"数"]))
    out.add(str(wh[u"数"] - wh[u"字が同じ"]))
    kinds = mix_by_kind(c.rec[u"書類"][:DEV_COUNT])
    out.add(str(kinds[MIX_KINDS[1]][2] + kinds[MIX_KINDS[2]][2]))
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    sec3 = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        if ln in sec3.splitlines():
            continue                                       # §3 は sec3_problems が小さい集合で見る
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。数は字で留めた小さい集合の内。見出しと、記録から導けない旨の字が在る。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    for ln in s.splitlines():
        for t in doc_number_tokens(ln):
            if t not in SEC3_NUMBERS:
                out.append(u"§3 に字で留めた集合の外の数 %s" % t)
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    for p in (u"62 本の全部を別の実装で掛け直してはいない", u"確かめたのはこの 6 本"):
        if p not in s:
            out.append(u"§3 に字が無い: %s" % p)
    if re.search(u"62 本の全部を別の実装で掛け直した(?!てはいない)", s):
        out.append(u"§3 が「62 本の全部を別の実装で掛け直した」と肯定している")
    return out


def affirm_problems(c):
    u"""「EDINET の検査に通る」「XBRL を作れる」は、その行に「言えない」か「示していない」が在るときだけ(肯定の形で書かない)。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for w in (u"EDINET の検査に通る", u"XBRL を作れる"):
            if w in ln and u"言えない" not in ln and u"示していない" not in ln:
                out.append(u"文書の %d 行目が「%s」を否定の外で書いている" % (i, w))
    for w in (u"検査に通る。", u"検査に通ります", u"作れます", u"作れる。"):
        if w in c.doc.replace(u"「XBRL を作れる」", u""):
            out.append(u"文書に肯定の字: %s" % w)
    return out


# ======================================================================================================
def phrase_problems(c):
    out = [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]
    out += [u"封 §7 に字が無い: %s" % p for p in SEAL7_PHRASES if p not in c.seal.split(u"## §7", 1)[-1]]
    return out


def head_problems(c):
    head = c.doc.split(u"## §1")[0]
    return [u"文書の頭(§1 の前)に無い: %s" % p for p in HEAD_PHRASES if p not in head]


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"\b[0-9a-f]{8}\b", u" ", c.doc)
    if DOCID_FORM.search(scan):
        out.append(u"文書に docID の形が在る")
    if ECODE_FORM.search(scan):
        out.append(u"文書に EDINET コードの形が在る")
    return out


def doc_commit_problems(c):
    out = []
    want = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)
    for w in want:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    if not set(re.findall(r"\b[0-9a-f]{8}\b", c.doc)) <= set(want):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems),
    (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems), (u"affirm", affirm_problems),
    (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
def blob_problems(root, prefix, at):
    out = []
    for rel, commit in at.items():
        r = subprocess.run(["git", "-C", root, "show", "%s:%s" % (commit, prefix + rel)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode != 0:
            out.append(u"commit %s に %s が無い" % (commit, rel))
            continue
        with open(os.path.join(root, prefix, rel), "rb") as fh:
            if fh.read() != r.stdout:
                out.append(u"%s が commit %s の blob と違う" % (rel, commit))
    return out


def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    out.extend(blob_problems(root, PREFIX, BLOB_AT))
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ script と封の門 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL, SEAL_GATE_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    for rel in (SCRIPT_REL, SEAL_GATE_REL):
        added = PR.added_commits(root, PREFIX + rel)
        if len(added) != 1 or not added[0].startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s を足した commit が %s でない" % (rel, SCRIPT_COMMIT_SHORT))
        rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + rel)
        if not last.startswith(SCRIPT_COMMIT_SHORT):
            out.append(u"%s の最後の commit が %s でない(記録を書いた後に変わった)" % (rel, SCRIPT_COMMIT_SHORT))
    rec = PR.added_commits(root, PREFIX + RECORD_REL)
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    else:
        rc, lastrec = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + RECORD_REL)
        if not lastrec.startswith(RECORD_COMMIT_SHORT):
            out.append(u"記録の最後の commit が %s でない" % RECORD_COMMIT_SHORT)
        for rel in (SCRIPT_REL, SEAL_GATE_REL):
            added = PR.added_commits(root, PREFIX + rel)
            if added and not PR.is_anc(root, added[0], rec[0]):
                out.append(u"記録が %s より前" % rel)
    return out


# ======================================================================================================
PREDICT = u"""
(変異を実行する前に書いた予測。右 = 赤になるべき検査)
M1  記録の sha256 の写しを違う値に                                                    -> sha
M2  記録の「この script の sha256」を 1 字替える                                      -> sha
M3  記録の限界の欄の 1 行を消す                                                       -> sha
M4  書類 10 の元の fact の行の数を 1 増やす(集計は直さない)                            -> recount
M5  集計の本番だけの 62 本の fact が同じ書類 62 → 61                                   -> recount
M6  予測の欄 XB0-4 の file 280 → 281                                                  -> recount
M7  材料の書類の本数 67 → 68                                                          -> recount
M8  書類 10 の鳴り方が同じの旗を False に(符号は同じのまま・集計は直さない)             -> recount
M9  書類 20 の字の file の「持たない」の字が同じを数より多くする                       -> recount
M10 書類 20 を断ったに(組み直しの 1 回を None・旗を False・集計は直さない)              -> recount
M11 記録に docid の欄を足す                                                           -> clean
M12 封の写しから「56 本以上」を消す                                                   -> bound
M13 封の写しから「XB0-1 と XB0-6 がどちらも当たりなら…」の字を消す                      -> bound
M14 文書の XB0-4 の判定「**外れ**(下に外れた)」を「当たり」に                           -> verdict
M15 文書の件数の行 当たり 4・外れ 3 → 当たり 5・外れ 2                                  -> verdict
M16 文書の XB0-1 のセルの「当たり(端の数)」を「当たり」に                                -> verdict
M17 文書の XB0-6 のセル 15/15 → 14/15                                                  -> verdict
M18 §5 の「人間に示す次の便の候補」の見出しの字を消す                                   -> verdict・phrases
M19 文書の「字のうえでは発火しない」の括弧の数 312/927 → 312/926                        -> verdict・frag
M20 本番の 7 書類の fact が同じを False にして集計・予測も整合して直す(XB0-1 が外れ)     -> verdict(recount は緑)
M21 開発の 5 本の混ぜ物 5 個を fact が同じ=True にして整合(XB0-6 が外れ)                -> verdict(recount は緑)
M22 文書の §2 の本番の行の fact の行の合計 81143 → 81144                               -> frag・numbers
M23 文書の 32.4% → 32.5%                                                              -> frag・numbers
M24 文書の「31 本」を「32 本」に                                                       -> frag
M25 混ぜ物の表の「| 抜く | 5 | 5 | 0 |」を「| 抜く | 5 | 5 | 1 |」に                    -> frag
M26 文書に 999 本という数の言い切りを足す                                              -> numbers
M27 文書の「最も少ない書類で 640」を 641 に                                            -> frag・numbers
M28 全書類の字の file「持つ」の数を書類 3 だけ 2 にして整合                             -> sanity(recount は緑)
M29 書類 20 の組み直しの fact の行の数を 1 増やす(fact が同じ旗は True のまま)         -> recount・sanity(実測: sanity は黙った。この条は recount が持つので表を recount だけに直した)
M30 混ぜ物 1 個の鳴り方が同じを入れ替え(抜く を False に)して整合                       -> sanity(recount は緑)
M31 §3 に「7 本」を足す                                                               -> sec3
M32 §3 の「62 本の全部を別の実装で掛け直してはいない」を消す                             -> sec3・phrases
M33 文書に「XBRL を作れます。」を足す                                                   -> affirm
M34 文書に「この道具は EDINET の検査に通る」を足す                                       -> affirm
M35 文書の「言えないこと」を消す                                                       -> phrases
M36 頭の「この便からは言えない」を消す                                                  -> head
M37 頭の「先に負けと限界を書く」を消す                                                  -> head
M38 頭の「タグを決める力は測っていない」を消す                                          -> head
M39 頭の「LLM の席は呼んでいない」を消す                                               -> head
M40 文書に「保証」を足す                                                               -> forbidden
M41 文書に docID の形を足す                                                            -> forbidden
M42 文書の commit の字 288d7b6d を 288d7b6e に                                         -> commits
M43 文書の頭の「(62/62)」を「(61/62)」に                                                 -> frag・verdict(実測: verdict は頭の端の数の字を読まず黙った。frag だけに直した)
"""


def rebuild(rec):
    u"""書類ごとの数はそのままに、集計と予測の判定に要る数を作り直す(整合した変更)。"""
    tot = totals(rec)
    rec[u"集計"] = tot
    rec[PRED_KEY] = pred_expected(tot)


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def drop_all(c, phrase):
    assert phrase in c.doc, phrase
    c.doc = c.doc.replace(phrase, u"X")


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


def add_sec3(c, text):
    rep(c, u"## §4 ", text + u"\n\n## §4 ")


def m_3(c):
    c.rec[u"限界"] = c.rec[u"限界"][1:]


def m_8(c):
    c.rec[u"書類"][9][u"鳴り方が同じ"] = False


def m_9(c):
    f = c.rec[u"書類"][19][u"字の file"][u"持たない"]
    f[u"字が同じ"] = f[u"数"] + 1


def m_10(c):
    d = c.rec[u"書類"][19]
    d[u"断った"] = True
    d[u"断った理由"] = u"x"
    d[u"組み直しの 1 回"] = None
    d[u"fact が同じ"] = False
    d[u"鳴り方が同じ"] = False


def m_20(c):
    for d in c.rec[u"書類"][DEV_COUNT:DEV_COUNT + 7]:
        d[u"fact が同じ"] = False
    rebuild(c.rec)


def m_21(c):
    for d in c.rec[u"書類"][:DEV_COUNT]:
        d[u"混ぜ物"][0][u"fact が同じ"] = True
    rebuild(c.rec)


def m_28(c):
    c.rec[u"書類"][2][u"字の file"][u"持つ"][u"数"] = 2
    rebuild(c.rec)


def m_29(c):
    c.rec[u"書類"][19][u"組み直しの fact の行の数"] += 1


def m_30(c):
    c.rec[u"書類"][0][u"混ぜ物"][0][u"鳴り方が同じ"] = False
    rebuild(c.rec)


MUTATIONS = (
    (u"M1 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M2 記録の script の sha256 を 1 字替える", lambda c: c.rec.__setitem__(u"この script の sha256", u"f" + c.rec[u"この script の sha256"][1:]), (u"sha",)),
    (u"M3 記録の限界の欄の 1 行を消す", m_3, (u"sha",)),
    (u"M4 書類 10 の元の fact の行の数を 1 増やす", lambda c: c.rec[u"書類"][9].__setitem__(u"元の fact の行の数", c.rec[u"書類"][9][u"元の fact の行の数"] + 1), (u"recount",)),
    (u"M5 集計の fact が同じ書類 62 → 61", lambda c: c.rec[u"集計"][GROUPS[1]].__setitem__(u"fact が同じ書類", 61), (u"recount",)),
    (u"M6 予測の欄 XB0-4 の file 280 → 281", lambda c: c.rec[PRED_KEY][PK[3]].__setitem__(u"file", 281), (u"recount",)),
    (u"M7 材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M8 書類 10 の鳴り方が同じの旗を False に", m_8, (u"recount",)),
    (u"M9 書類 20 の字が同じを数より多く", m_9, (u"recount",)),
    (u"M10 書類 20 を断ったに", m_10, (u"recount",)),
    (u"M11 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M12 封の写しから「56 本以上」を消す", lambda c: rep(c, u"56 本以上", u"X", attr="seal", count=9), (u"bound",)),
    (u"M13 封の写しから「XB0-1 と XB0-6 がどちらも当たりなら」の字を消す", lambda c: rep(c, u"XB0-1 と XB0-6 がどちらも当たりなら、次の便の候補を人間に示す", u"X", attr="seal"), (u"bound",)),
    (u"M14 XB0-4 の判定を当たりに", lambda c: rep(c, u"**外れ**(下に外れた)", u"当たり"), (u"verdict",)),
    (u"M15 件数の行を当たり 5・外れ 2 に", lambda c: rep(c, u"- 当たり 4・外れ 3。", u"- 当たり 5・外れ 2。"), (u"verdict",)),
    (u"M16 XB0-1 のセルの(端の数)を消す", lambda c: rep(c, u"| 62/62 | 当たり(端の数) |", u"| 62/62 | 当たり |"), (u"verdict",)),
    (u"M17 XB0-6 のセル 15/15 → 14/15", lambda c: rep(c, u"| 15/15 | 当たり |", u"| 14/15 | 当たり |"), (u"verdict",)),
    (u"M18 §5 の次の便の候補の見出しの字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XB0-1 と XB0-6 がどちらも当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M19 自己点検の括弧の数 312/927 → 312/926", lambda c: rep(c, u"(312/927)ので", u"(312/926)ので"), (u"verdict", u"frag")),
    (u"M20 本番の 7 書類の fact が同じを False にして整合(XB0-1 が外れ)", m_20, (u"verdict",)),
    (u"M21 混ぜ物 5 個を fact が同じ=True にして整合(XB0-6 が外れ)", m_21, (u"verdict",)),
    (u"M22 本番の行の fact の行の合計 81143 → 81144", lambda c: rep(c, u"| 81143 |", u"| 81144 |"), (u"frag", u"numbers")),
    (u"M23 32.4% → 32.5%", lambda c: rep(c, u"32.4%", u"32.5%", count=9), (u"frag", u"numbers")),
    (u"M24 「31 本」を「32 本」に", lambda c: rep(c, u"同じ書類が 31 本", u"同じ書類が 32 本"), (u"frag",)),
    (u"M25 混ぜ物の表の抜くの行を 5 | 5 | 1 に", lambda c: rep(c, u"| 抜く | 5 | 5 | 0 |", u"| 抜く | 5 | 5 | 1 |"), (u"frag",)),
    (u"M26 文書に 999 本の言い切りを足す", lambda c: add_doc(c, u"fact の行は 999 本に近い。"), (u"numbers",)),
    (u"M27 「最も少ない書類で 640」を 641 に", lambda c: rep(c, u"最も少ない書類で 640", u"最も少ない書類で 641"), (u"frag", u"numbers")),
    (u"M28 書類 3 の字の file「持つ」の数を 2 にして整合", m_28, (u"sanity",)),
    (u"M29 書類 20 の組み直しの fact の行の数を 1 増やす", m_29, (u"recount",)),
    (u"M30 混ぜ物の鳴り方が同じを 1 個入れ替えて整合", m_30, (u"sanity",)),
    (u"M31 §3 に「7 本」を足す", lambda c: add_sec3(c, u"- 別に 7 本で確かめた。"), (u"sec3",)),
    (u"M32 §3 の「62 本の全部を別の実装で掛け直してはいない」を消す", lambda c: rep(c, u"62 本の全部を別の実装で掛け直してはいない", u"X"), (u"sec3", u"phrases")),
    (u"M33 文書に「XBRL を作れます。」を足す", lambda c: add_doc(c, u"XBRL を作れます。"), (u"affirm",)),
    (u"M34 文書に「EDINET の検査に通る」を肯定で足す", lambda c: add_doc(c, u"この道具は EDINET の検査に通る。"), (u"affirm",)),
    (u"M35 文書の「言えないこと」を消す", lambda c: drop_all(c, u"言えないこと"), (u"phrases",)),
    (u"M36 頭の「この便からは言えない」を消す", lambda c: rep(c, u"この便からは言えない", u"X"), (u"head",)),
    (u"M37 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M38 頭の「タグを決める力は測っていない」を消す", lambda c: rep(c, u"タグを決める力は測っていない", u"X"), (u"head",)),
    (u"M39 頭の「LLM の席は呼んでいない」を消す", lambda c: rep(c, u"LLM の席は呼んでいない", u"X"), (u"head",)),
    (u"M40 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M41 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M42 文書の commit の字 288d7b6d を 1 字替える", lambda c: rep(c, u"288d7b6d", u"288d7b6e", count=9), (u"commits",)),
    (u"M43 頭の「(62/62)」を「(61/62)」に", lambda c: rep(c, u"端の数(62/62)", u"端の数(61/62)"), (u"frag",)),
)


def run_mutations(base=None):
    base = base or Ctx()
    out = []
    for name, fn, checks in MUTATIONS:
        c = base.copy()
        fn(c)
        res = [(k, bool(guard(CHECKS[k], c))) for k in checks]
        out.append((name, res))
    return out


# ======================================================================================================
class RealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = Ctx()

    def test_a_1_sha256_and_provenance(self):
        self.assertEqual([], sha_problems(self.c))

    def test_b_1_the_record_numbers_recount_without_the_script_functions(self):
        self.assertEqual([], recount_problems(self.c))

    def test_b_2_the_record_has_no_forbidden_fields_or_forms(self):
        self.assertEqual([], record_clean_problems(self.c))

    def test_b_3_the_derived_numbers_the_document_states(self):
        tot = totals(self.c.rec)
        prod = tot[GROUPS[1]]
        self.assertEqual((62, 0, 62, 62), (prod[u"書類"], prod[u"断った書類"], prod[u"fact が同じ書類"], prod[u"鳴り方が同じ書類"]))
        self.assertEqual((280, 865, 32, 62), (prod[u"file"][u"持たない"][u"字が同じ"], prod[u"file"][u"持たない"][u"数"], prod[u"file"][u"持つ"][u"字が同じ"], prod[u"file"][u"持つ"][u"数"]))
        self.assertEqual(u"32.4%", pct(280, 865))
        self.assertEqual((31, 30, 1, 640, 2068), prod_stats(self.c))
        self.assertEqual(collections.OrderedDict([(u"混ぜ物の数", 15), (u"作れた数", 15), (u"fact が同じでない数", 15), (u"鳴り方が同じでない数", 10)]), tot[u"混ぜ物"])
        self.assertEqual({u"抜く": [5, 5, 0], u"文脈を替える": [5, 5, 5], u"符号を返す": [5, 5, 5]}, dict(mix_by_kind(self.c.rec[u"書類"][:DEV_COUNT])))
        self.assertEqual((81143, 6444, 87587), (prod[u"元の fact の行の数の合計"], tot[GROUPS[0]][u"元の fact の行の数の合計"], tot[GROUPS[2]][u"元の fact の行の数の合計"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(totals(self.c.rec))
        self.assertEqual(4, sum(1 for v in j.values() if v))
        self.assertEqual([u"XB0-4", u"XB0-5", u"XB0-7"], [k for k, v in j.items() if not v])

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_the_pinned_small_numbers(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_the_important_phrases_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms_and_no_affirmation(self):
        self.assertEqual([], forbidden_problems(self.c))
        self.assertEqual([], affirm_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_f_1_the_seal_history_the_blobs_and_the_engine(self):
        self.assertEqual([], git_problems())

    def test_f_2_order_the_seal_then_script_then_record_then_the_document_and_the_gate(self):
        u"""結果の文書と門のどちらかが未 commit なら赤(足した commit が無い。skip にしない)。両方 commit された後で初めて緑。"""
        self.assertEqual([], order_problems_real())

    def test_f_3_the_order_check_is_green_for_good_history_and_red_for_bad(self):
        r = PR.Repo()
        r.put("docs/seal.md")
        s = r.commit("docs/seal.md")
        r.put("measure/s.py")
        r.commit("measure/s.py")
        others = ["fix/r.json", "docs/d.md", "tests/g.py"]
        for f in others:
            r.put(f)
        r.commit(*others)
        self.assertEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others))
        r.put("docs/new.md")
        self.assertNotEqual([], PR.order_problems(r.d, PREFIX, "docs/seal.md", s[:7], ["measure/s.py"], others + ["docs/new.md"]))

    def test_f_4_the_blob_check_is_green_for_an_untouched_file_and_red_for_a_changed_one(self):
        r = PR.Repo()
        r.put("measure/s.py")
        c1 = r.commit("measure/s.py")
        at = {"measure/s.py": c1[:8]}
        self.assertEqual([], blob_problems(r.d, PREFIX, at))
        with open(os.path.join(r.d, PREFIX, "measure/s.py"), "a", encoding="utf-8") as fh:
            fh.write(u"# 結果の便で足した 1 行\n")
        self.assertNotEqual([], blob_problems(r.d, PREFIX, at))
        self.assertNotEqual([], blob_problems(r.d, PREFIX, {"measure/s.py": "0000000"}))

    def test_f_5_the_blob_check_lists_the_four_frozen_files_at_their_commits(self):
        self.assertEqual([SEAL_REL, SCRIPT_REL, SEAL_GATE_REL, RECORD_REL], list(BLOB_AT))
        self.assertEqual([SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT], list(BLOB_AT.values()))


class MutationTest(unittest.TestCase):
    def test_g_1_every_mutation_turns_its_checks_red_and_the_files_are_unchanged(self):
        before = tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL])
        base = Ctx()
        results = run_mutations(base)
        self.assertEqual(before, tuple(sha_file(r) for r in list(SHA_PIN) + [DOC_REL]))
        self.assertEqual(len(MUTATIONS), len(results))
        silent = [(n, k) for n, res in results for k, red in res if not red]
        self.assertEqual([], silent)
        self.assertGreaterEqual(len(MUTATIONS), 40)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        c = Ctx().copy()
        m_20(c)
        self.assertEqual([], recount_problems(c))
        self.assertNotEqual([], verdict_problems(c))
        self.assertFalse(judge(totals(c.rec))[u"XB0-1"])
        c = Ctx().copy()
        m_21(c)
        self.assertEqual([], recount_problems(c))
        self.assertNotEqual([], verdict_problems(c))
        self.assertFalse(judge(totals(c.rec))[u"XB0-6"])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数: XB0-1 は 56 本が当たり・55 本が外れ。XB0-5 は 10 本が当たり・11 本が外れ。XB0-7 は 5 個が当たり・6 個が外れ。"""
        c = Ctx().copy()
        for n, want in ((56, True), (55, False)):
            for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                d[u"fact が同じ"] = i < n
            rebuild(c.rec)
            self.assertEqual(want, judge(totals(c.rec))[u"XB0-1"], n)
        c = Ctx().copy()
        for n, want in ((10, True), (11, False)):
            for i, d in enumerate(c.rec[u"書類"][DEV_COUNT:]):
                d[u"字の file"][u"持つ"][u"字が同じ"] = 1 if i < n else 0
            rebuild(c.rec)
            self.assertEqual(want, judge(totals(c.rec))[u"XB0-5"], n)
        c = Ctx().copy()
        flat = [m for d in c.rec[u"書類"][:DEV_COUNT] for m in d[u"混ぜ物"]]
        for n, want in ((5, True), (6, False)):
            for i, m in enumerate(flat):
                m[u"鳴り方が同じ"] = i >= n
            rebuild(c.rec)
            self.assertEqual(want, judge(totals(c.rec))[u"XB0-7"], n)

    def test_g_6_the_edge_cell_follows_the_record(self):
        u"""XB0-1 が 61/62 になれば「(端の数)」を期待しない。"""
        c = Ctx().copy()
        c.rec[u"書類"][DEV_COUNT][u"fact が同じ"] = False
        rebuild(c.rec)
        self.assertEqual(u"当たり", expected_verdict_cells(c)[u"XB0-1"][1])


if __name__ == "__main__":
    unittest.main()
