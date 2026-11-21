# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TAG_NARROW_SEAL_2026-11-21.md(1bda1997)の結果の文書 docs/XBRL_TAG_NARROW_RESULT_2026-11-21.md。

封の門 ``test_xbrl_tag_narrow_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封の sha256(字で留める)と、記録の script の sha256・封の commit の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、集計・予測の判定に要る数・書類ごとの率を数え直して記録と同じことを見る。段 0 は便 XG0 の記録の表 L2 と同じ
 c 予測 XG1-1〜XG1-7 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し(丸める前の数で)、文書 §1 の表・件数と同じことを見る。封 §6 と文書 §5 が合う
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。§3 は記録に無い行数・% を持たない
 e 文書の要点の字・頭の負けと限界・禁止語・docID と EDINET コードと要素の名の形
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


SG = load_module("tests/measure/test_xbrl_tag_narrow_seal.py", "xbrl_tag_narrow_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
PRIOR_RECORD_REL = SG.PRIOR_RECORD_REL
GATE_REL = "tests/measure/test_xbrl_tag_narrow_result.py"
DOC_REL = "docs/XBRL_TAG_NARROW_RESULT_2026-11-21.md"
SCRIPT_COMMIT_SHORT = "762d361e"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "b2f80974"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "f6873eeaab3eb2b51eaf89aac33dc708289cc8b5f91208ff947111443968d3ff"),
    (SCRIPT_REL, "24159344be6b2ecf6957339b1356d8049bfe90cab1f4660be5b2f7151a7d6a33"),
    (SEAL_GATE_REL, "4341851bfad8ed2bf3b1743b5dc9c824fedbe907ce87d68b7a6b31baf2d5dd7e"),
    (SEAL_REL, "58bce5588c9c8e2506e38f49ec207fb20eebecfbdc6e2cddd4a4006007ebb235")])

STAGES = (u"段 0", u"段 1", u"段 2", u"段 3")
CLS = (u"U", u"A", u"W", u"N")
KINDS = (u"bs", u"pl", u"ss", u"cf")
KEY_PRED = u"予測の判定に要る数(XG1-1〜XG1-7。当たり・外れは結果の文書で)"
KEY_RATE = u"段 3 の U の率(%)"
PRED_KEYS = (u"XG1-1 段 1 の類 U / 計算書の行", u"XG1-2 段 2 の類 U / 計算書の行", u"XG1-3 段 3 の類 U / 計算書の行", u"XG1-4 段 3 の類 A / 計算書の行",
             u"XG1-5 段 3 で正しい要素を落とした行 / 計算書の行", u"XG1-6 種類 K が決まらない行 / 計算書の行", u"XG1-7 段 3 の U の率が 90% 以上の書類 / 計算書の行が 1 行以上在る書類")
#: 封 §4 の境(整数の %)。封の文書にこの字が在ることを ``bound_problems`` が見る
BOUND_SEAL_PHRASES = (u"61% 以上 68% 以下", u"68% 以上 84% 以下", u"80% 以上 93% 以下", u"5% 以上 15% 以下", u"3% 以下", u"10% 以下", u"25 本以下",
                      u"段 3 の U が 97% を超えたら", u"段 3 で落とした行が 10% を超えても同じ", u"XG1-3 が当たり(段 3 の U が 80% 以上 93% 以下)で XG1-5 が当たり(落とした行が 3% 以下)なら、次の便の候補を人間に示す")
HEAD_PHRASES = (u"先に負けと限界を書く", u"この便からは言えない", u"無作為ではない", u"「上の限り」", u"専用の道具が組んだ後の字", u"LLM の席は呼んでいない", u"XG1-4 は外れ",
                u"主の予測 XG1-3 は当たりだが、境に近い", u"正しい要素を捨てることが在る", u"業種の段は、ほぼ 1 つの業種でしか試されていない")
PHRASES = (u"測っていない見立て", u"言えること", u"言えないこと", u"封 §0 の申告の誤り", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"記録に理由の欄は無い",
           u"残りの 2 割は表の引き当てでは決まらず", u"その部品で決まるかは測っていない", u"行をまたぐ値を読むことを縛る試験を監査の指摘で足してある")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
ELEMENT_FORM = re.compile(r"jp[a-z]*_cor[:_][A-Za-z]")


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


def tenths(n, d):
    u"""n/d の % を 0.1 刻みの整数で(四捨五入は整数の計算。門の側で独立に書く)。"""
    return (n * 2000 + d) // (2 * d)


def pct1(n, d):
    return u"%d.%d" % divmod(tenths(n, d), 10)


def tstr(t):
    return u"%d.%d" % divmod(t, 10)


class Ctx(object):
    u"""検査が見る写し。変異はこの写しを変える(木の file は変えない)。"""

    def __init__(self):
        self.rec = json.loads(read(RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.prior = json.loads(read(PRIOR_RECORD_REL), object_pairs_hook=collections.OrderedDict)
        self.doc = read(DOC_REL)
        self.seal = read(SEAL_REL)
        self.shas = collections.OrderedDict((rel, sha_file(rel)) for rel in SHA_PIN)

    def copy(self):
        c = Ctx.__new__(Ctx)
        c.rec = copy.deepcopy(self.rec)
        c.prior = copy.deepcopy(self.prior)
        c.doc = self.doc
        c.seal = self.seal
        c.shas = collections.OrderedDict(self.shas)
        return c


def figures(rec):
    u"""書類ごとの数から、門の側で集計を作る(script の関数は使わない)。"""
    docs = rec[u"書類"]
    f = dict(ndocs=len(docs))
    f["rows"] = sum(x[u"計算書の行の数"] for x in docs)
    f["st"] = collections.OrderedDict((s, collections.OrderedDict((k, sum(x[u"段ごとの類別"][s][k] for x in docs)) for k in CLS)) for s in STAGES)
    f["drop"] = collections.OrderedDict((s, sum(x[u"段ごとの落とした行"][s] for x in docs)) for s in STAGES[1:])
    f["kinds"] = collections.OrderedDict((k, sum(x[u"種類 K ごとの行"][k] for x in docs)) for k in KINDS)
    f["k_none"] = sum(x[u"K が決まらない行"] for x in docs)
    f["i_none"] = sum(x[u"K が決まり I が決まらない行"] for x in docs)
    f["k_none_docs"] = sum(1 for x in docs if x[u"K が決まらない行"] > 0)
    with_rows = [x for x in docs if x[u"計算書の行の数"] > 0]
    f["with_rows"] = len(with_rows)
    f["rates"] = sorted(tenths(x[u"段ごとの類別"][u"段 3"][u"U"], x[u"計算書の行の数"]) for x in with_rows)
    f["u90"] = sum(1 for x in with_rows if x[u"段ごとの類別"][u"段 3"][u"U"] * 100 >= 90 * x[u"計算書の行の数"])
    n = len(f["rates"])
    f["median"] = f["rates"][n // 2] if n % 2 else (f["rates"][n // 2 - 1] + f["rates"][n // 2] + 1) // 2
    f["bands"] = collections.Counter(t // 100 * 10 for t in f["rates"])
    f["drop_docs"] = [x for x in docs if x[u"段ごとの落とした行"][u"段 3"] > 0]
    return f


def judge(rec):
    u"""封 §4 の境と記録から XG1-1〜XG1-7 の当たり外れを決め直す(整数の計算。判定は丸める前の数)。"""
    f = figures(rec)
    st, rows = f["st"], f["rows"]
    out = collections.OrderedDict()
    out[u"XG1-1"] = 61 * rows <= 100 * st[u"段 1"]["U"] <= 68 * rows
    out[u"XG1-2"] = 68 * rows <= 100 * st[u"段 2"]["U"] <= 84 * rows
    out[u"XG1-3"] = 80 * rows <= 100 * st[u"段 3"]["U"] <= 93 * rows
    out[u"XG1-4"] = 5 * rows <= 100 * st[u"段 3"]["A"] <= 15 * rows
    out[u"XG1-5"] = 100 * f["drop"][u"段 3"] <= 3 * rows
    out[u"XG1-6"] = 100 * f["k_none"] <= 10 * rows
    out[u"XG1-7"] = f["u90"] <= 25
    return out


def direction(rec, key):
    f = figures(rec)
    st, rows = f["st"], f["rows"]
    pairs = {u"XG1-1": (61, 68, st[u"段 1"]["U"]), u"XG1-2": (68, 84, st[u"段 2"]["U"]), u"XG1-3": (80, 93, st[u"段 3"]["U"]), u"XG1-4": (5, 15, st[u"段 3"]["A"])}
    if key in pairs:
        lo, hi, n = pairs[key]
        return u"下" if 100 * n < lo * rows else u"上"
    return u""


def need_rows_for_80(rows):
    u"""段 3 の U が 80% に届く最小の行数。"""
    return (80 * rows + 99) // 100


def pred_expected(f):
    st, rows = f["st"], f["rows"]

    def rr(n):
        return dict([(u"行", n), (u"分母", rows), (u"%", float(pct1(n, rows)))])
    return collections.OrderedDict([
        (PRED_KEYS[0], rr(st[u"段 1"]["U"])), (PRED_KEYS[1], rr(st[u"段 2"]["U"])), (PRED_KEYS[2], rr(st[u"段 3"]["U"])), (PRED_KEYS[3], rr(st[u"段 3"]["A"])),
        (PRED_KEYS[4], rr(f["drop"][u"段 3"])), (PRED_KEYS[5], rr(f["k_none"])), (PRED_KEYS[6], dict([(u"書類", f["u90"]), (u"分母", f["with_rows"])]))])


# ======================================================================================================
# a. sha256・来歴の欄
def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    rec = c.rec
    if rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (rec[u"seal"], rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    return out


# ======================================================================================================
# b. 記録の数え直し
def recount_problems(c):
    rec = c.rec
    out = []
    f = figures(rec)
    docs = rec[u"書類"]
    if [x[u"番号"] for x in docs] != list(range(1, f["ndocs"] + 1)) or rec[u"材料"][u"書類の本数"] != f["ndocs"]:
        out.append(u"書類の番号・材料の書類の本数が違う")
    for x in docs:
        n, rows = x[u"番号"], x[u"計算書の行の数"]
        for s in STAGES:
            if sum(x[u"段ごとの類別"][s].values()) != rows:
                out.append(u"書類 %d の %s の和が計算書の行の数と違う" % (n, s))
        if sum(x[u"種類 K ごとの行"].values()) + x[u"K が決まらない行"] != rows:
            out.append(u"書類 %d の種類ごとの行の和が計算書の行の数と違う" % n)
        if rows > 0 and x[KEY_RATE] != float(pct1(x[u"段ごとの類別"][u"段 3"][u"U"], rows)):
            out.append(u"書類 %d の U の率が数え直しと違う" % n)
    agg = rec[u"集計"]
    if agg[u"計算書の行の数"] != f["rows"]:
        out.append(u"集計の計算書の行の数が書類ごとの和と違う")
    if agg[u"段ごとの類別"] != dict((s, dict(v)) for s, v in f["st"].items()):
        out.append(u"集計の段ごとの類別が書類ごとの和と違う")
    if agg[u"段ごとの落とした行"] != dict(f["drop"]) or agg[u"種類 K ごとの行"] != dict(f["kinds"]):
        out.append(u"集計の落とした行・種類ごとの行が書類ごとの和と違う")
    if agg[u"K が決まらない行"] != f["k_none"] or agg[u"K が決まり I が決まらない行"] != f["i_none"] or agg[u"計算書の行が 1 行以上在る書類の数"] != f["with_rows"]:
        out.append(u"集計の K・I・書類の数の欄が違う")
    pred = rec[KEY_PRED]
    want = pred_expected(f)
    if list(pred.keys()) != list(want.keys()):
        out.append(u"予測の判定に要る数の欄の名・順が違う")
    for k, v in want.items():
        if dict(pred.get(k, {})) != v:
            out.append(u"予測の判定に要る数が数え直しと違う: %s" % k[:6])
    return out


def stage0_problems(c):
    u"""段 0 の数(と行の数)が便 XG0 の記録の表 L2 の数と同じ。"""
    f = figures(c.rec)
    agg = c.prior[u"集計"]
    out = []
    if agg[u"計算書の行の数"] != f["rows"] or dict(agg[u"類別(表 L2)"]) != dict(f["st"][u"段 0"]):
        out.append(u"段 0 の数が便 XG0 の記録の表 L2 と違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    scan = re.sub(r"[0-9a-fA-F]{32,}", u"", text)
    out = []
    if DOCID_FORM.search(scan) or ECODE_FORM.search(scan):
        out.append(u"記録に docID か EDINET コードの形が在る")
    bad = [k for k in SG.MS.W.walk_keys(c.rec) if str(k).lower() in SG.MS.W.FORBIDDEN_KEYS]
    if bad:
        out.append(u"記録に禁止の欄が在る")
    return out


# ======================================================================================================
# c. 予測の当たり外れ
def bound_problems(c):
    return [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]


def expected_verdict_cells(c):
    f = figures(c.rec)
    j = judge(c.rec)
    st, rows = f["st"], f["rows"]

    def cell(n):
        return u"%d/%d(%s%%)" % (n, rows, pct1(n, rows))
    actual = {u"XG1-1": cell(st[u"段 1"]["U"]), u"XG1-2": cell(st[u"段 2"]["U"]), u"XG1-3": cell(st[u"段 3"]["U"]), u"XG1-4": cell(st[u"段 3"]["A"]),
              u"XG1-5": cell(f["drop"][u"段 3"]), u"XG1-6": cell(f["k_none"]), u"XG1-7": u"%d/%d" % (f["u90"], f["with_rows"])}
    out = collections.OrderedDict()
    for k in j:
        if j[k]:
            verdict = u"当たり"
            if k == u"XG1-3" and st[u"段 3"]["U"] - need_rows_for_80(rows) < 100:
                verdict = u"当たり(下の境に近い)"
        else:
            d = direction(c.rec, k)
            verdict = u"**外れ**" + (u"(%sに外れた)" % d if d else u"")
        out[k] = (actual[k], verdict)
    return out


def verdict_problems(c):
    u"""文書 §1 の表と件数・頭の言い切り・§5 の次の便の候補が、記録から決め直した判定と同じ。"""
    j = judge(c.rec)
    want = expected_verdict_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XG1-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XG1-1〜XG1-7 でない"]
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[1] != want[k][0]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        if cells[2] != want[k][1]:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want[k][1]))
    hits = sum(1 for v in j.values() if v)
    line = u"- 当たり %d・外れ %d。" % (hits, len(j) - hits)
    if line not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    if u"当たり %d・外れ %d。" % (hits, len(j) - hits) not in head:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    for k, v in j.items():
        if not v:
            if u"%s は外れ" % k not in head:
                out.append(u"文書の頭が外れた %s を言っていない" % k)
        elif u"%s は外れ" % k in head:
            out.append(u"文書の頭が当たった %s を外れと言う" % k)
    sec5 = section(c.doc, u"## §5 ", None)
    both = j[u"XG1-3"] and j[u"XG1-5"]
    if both != (u"人間に示す次の便の候補(封 §6。XG1-3 と XG1-5 がどちらも当たりなので示す)" in sec5):
        out.append(u"封 §6 の決め(XG1-3 と XG1-5 がどちらも当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if not both and u"外れ方を書いて" not in sec5:
        out.append(u"どちらかが外れたときの封 §6 の決めが §5 に無い")
    return out


# ======================================================================================================
# d. 文書の数
def section(doc, head, nxt):
    i = doc.index(head)
    j = doc.index(nxt, i + len(head)) if nxt else len(doc)
    return doc[i:j]


def expected_lines(c):
    f = figures(c.rec)
    st, rows = f["st"], f["rows"]
    s0, s1, s2, s3 = (st[s] for s in STAGES)
    d = f["drop"]
    m = c.rec[u"材料"]
    k = f["kinds"]
    r = f["rates"]
    return [
        u"| 段 0(便 XG0 と同じ。絞らない) | %d(%s%%) | %d(%s%%) | %d | %d | ― |" % (s0["U"], pct1(s0["U"], rows), s0["A"], pct1(s0["A"], rows), s0["W"], s0["N"]),
        u"| 段 1(数を持てる要素だけ) | %d(%s%%) | %d | %d | %d | %d |" % (s1["U"], pct1(s1["U"], rows), s1["A"], s1["W"], s1["N"], d[u"段 1"]),
        u"| 段 2(+ 計算書の種類) | %d(%s%%) | %d | %d | %d | %d |" % (s2["U"], pct1(s2["U"], rows), s2["A"], s2["W"], s2["N"], d[u"段 2"]),
        u"| 段 3(+ 業種の科目の一覧) | %d(%s%%) | %d(%s%%) | %d | %d | %d |" % (s3["U"], pct1(s3["U"], rows), s3["A"], pct1(s3["A"], rows), s3["W"], s3["N"], d[u"段 3"]),
        u"- 計算書の種類ごとの行: 貸借対照表 %d・損益計算書(包括利益を含む)%d・株主資本等変動計算書 %d・キャッシュ・フロー計算書 %d。種類が決まらない行は %d(%s%%)で、1 行以上在る書類は %d 本。種類が決まって業種が決まらない行は %d。" % (
            k[u"bs"], k[u"pl"], k[u"ss"], k[u"cf"], f["k_none"], pct1(f["k_none"], rows), f["k_none_docs"], f["i_none"]),
        u"- 材料: 要素の表の要素 %d・段 1 が残す要素 %d・業種の folder %d・科目の一覧 %d・表 L2 のラベルの字 %d。" % (
            m[u"要素の表の要素の数"], m[u"段 1 が残す要素の数"], m[u"業種の folder の数"], m[u"科目の一覧の数"], m[u"表 L2 のラベルの字の数"]),
        u"- 書類ごとの段 3 の U の率(%d 本): 最小 %s%%・中央 %s%%・最大 %s%%。50%% 台が %d 本・70%% 台が %d 本・80%% 台が %d 本。90%% 以上は %d 本。最小の 1 本を除くと %s%% 以上。" % (
            f["with_rows"], tstr(r[0]), tstr(f["median"]), tstr(r[-1]), f["bands"][50], f["bands"][70], f["bands"][80], f["u90"], tstr(r[1])),
        u"- どの段も合計は %d。段 0 の数は便 XG0 の記録の表 L2 の数と同じ。" % rows]


def expected_fragments(c):
    f = figures(c.rec)
    st, rows = f["st"], f["rows"]
    s0, s3 = st[u"段 0"], st[u"段 3"]
    u3, a3, w3, n3 = s3["U"], s3["A"], s3["W"], s3["N"]
    dropped = f["drop"][u"段 3"]
    miss = need_rows_for_80(rows)
    lower = u3 - (miss - 1)
    dd = sorted((x[u"段ごとの落とした行"][u"段 3"] for x in f["drop_docs"]), reverse=True)
    minrate_doc = min(f["drop_docs"] + [x for x in c.rec[u"書類"] if x[u"計算書の行の数"] > 0], key=lambda x: tenths(x[u"段ごとの類別"][u"段 3"][u"U"], x[u"計算書の行の数"]))
    return [
        u"段 3 の類 U は %d/%d(%s%%)で、予測の下の境は 80%%。あと %d 行少なければ外れていた" % (u3, rows, pct1(u3, rows), lower),
        u"正しい要素が候補に在るのに 1 つに決まらない行(類 A)は %d/%d(%s%%)で、予測の上の境(15%%)を超えた" % (a3, rows, pct1(a3, rows)),
        u"段 3 で正しい要素を候補から落とした行は %d(%s%%)。類 W(1 つに決まるが違う)は段 0 の %d から段 3 で %d に、類 N(候補が無い)は %d から %d に増えた" % (
            dropped, pct1(dropped, rows), s0["W"], w3, s0["N"], n3),
        u"落とした %d 行は %d 本の書類に在る(%s)" % (dropped, len(dd), u"・".join(str(x) for x in dd)),
        u"段 3 の U の率が最小(%s%%)の書類は、この %d 行の書類" % (tstr(f["rates"][0]), max(dd)),
        u"要素が 1 つに決まり正しかった行は %s%%(絞る前は %s%%)。絞りで正しい要素を落とした行は %s%%。絞った後も %s%% は候補が 2 つ以上残り、%s%% は 1 つに決まって違い、%s%% は候補が無い" % (
            pct1(u3, rows), pct1(s0["U"], rows), pct1(dropped, rows), pct1(a3, rows), pct1(w3, rows), pct1(n3, rows)),
        u"決まる行は 6 割弱から 8 割に上がる",
        u"5 行に 1 行は決まらないか違う",
        u"監査の席が script の関数を使わずに %d 本の全部を数え直し" % f["ndocs"],
        u"書類は便 XG0 と同じ %d 本" % f["ndocs"]], minrate_doc


def sanity_problems(c):
    u"""文書の言い回し(「6 割弱から 8 割」「5 行に 1 行」「境に近い」「最小の書類は落とした行が最多の書類」)が記録の数に合う。"""
    f = figures(c.rec)
    st, rows = f["st"], f["rows"]
    out = []
    p0, p3 = 100 * st[u"段 0"]["U"] / float(rows), 100 * st[u"段 3"]["U"] / float(rows)
    if not (55 <= p0 < 60 and 78 <= p3 < 82):
        out.append(u"「6 割弱から 8 割」が記録の数に合わない")
    miss = (rows - st[u"段 3"]["U"]) / float(rows)
    if not (0.15 <= miss <= 0.25):
        out.append(u"「5 行に 1 行は決まらないか違う」が記録の数に合わない")
    if not st[u"段 3"]["U"] - need_rows_for_80(rows) < 100:
        out.append(u"「境に近い」が記録の数に合わない")
    frags, minrate_doc = expected_fragments(c)
    if minrate_doc[u"段ごとの落とした行"][u"段 3"] != max(x[u"段ごとの落とした行"][u"段 3"] for x in c.rec[u"書類"]):
        out.append(u"段 3 の U の率が最小の書類が、落とした行が最多の書類でない")
    if len(f["drop_docs"]) != 4:
        out.append(u"落とした行の在る書類が 4 本でない")
    return out


def fragment_problems(c):
    out = []
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    frags, _ = expected_fragments(c)
    for frag in frags:
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    return out


def structural_numbers():
    return set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"8", u"10", u"15", u"50", u"70", u"90", u"97"])


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"XG[01]-\d", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


BOUND_NUMBERS = (61, 68, 84, 93, 80, 5, 15, 3, 10, 25, 97)


def derived_numbers(c):
    f = figures(c.rec)
    st, rows = f["st"], f["rows"]
    m = c.rec[u"材料"]
    out = set(str(x) for x in (rows, f["ndocs"], f["with_rows"], f["u90"], f["k_none"], f["i_none"], f["k_none_docs"]))
    for s in STAGES:
        out |= set(str(v) for v in st[s].values())
    out |= set(str(v) for v in f["drop"].values())
    out |= set(str(v) for v in f["kinds"].values())
    out |= set(str(f["bands"][b]) for b in (50, 60, 70, 80))
    out |= set(str(x[u"段ごとの落とした行"][u"段 3"]) for x in f["drop_docs"])
    out.add(str(len(f["drop_docs"])))
    out |= set(str(m[k]) for k in (u"要素の表の要素の数", u"段 1 が残す要素の数", u"業種の folder の数", u"科目の一覧の数", u"表 L2 のラベルの字の数"))
    out |= set(pct1(st[s][k], rows) for s in STAGES for k in CLS)
    out |= set([pct1(f["drop"][u"段 3"], rows), pct1(f["k_none"], rows), tstr(f["rates"][0]), tstr(f["rates"][1]), tstr(f["median"]), tstr(f["rates"][-1])])
    out.add(str(f["st"][u"段 3"]["U"] - (need_rows_for_80(rows) - 1)))
    out |= set(str(x) for x in BOUND_NUMBERS)
    return out


def allowed_numbers(c):
    return set(structural_numbers()) | derived_numbers(c)


def doc_number_problems(c):
    u"""数字を含む行は全部、記録から組んだ数の並びの内(許す数の外の数字は赤)。"""
    allowed = allowed_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in doc_number_tokens(ln):
            t = tok.replace(u",", u"")
            if t not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は「記録に理由の欄は無い」読みの節。数字は、記録から導ける数(落とした 163 とその内訳・書類の本数・最小の率)と、番号・封の申告の数だけ。記録に無い行数・% を持たない。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    f = figures(c.rec)
    allowed = set([u"0", u"1", u"2", u"3", u"15"])
    allowed.add(str(f["drop"][u"段 3"]))
    allowed.add(str(len(f["drop_docs"])))
    allowed |= set(str(x[u"段ごとの落とした行"][u"段 3"]) for x in f["drop_docs"])
    allowed.add(tstr(f["rates"][0]))
    out = []
    for ln in s.splitlines():
        for t in doc_number_tokens(ln):
            if t.replace(u",", u"") not in allowed:
                out.append(u"§3 に記録から導けない数 %s" % t)
    if u"記録に理由の欄は無い" not in s:
        out.append(u"§3 が「記録に理由の欄は無い」と言っていない")
    if u"15" in [t for ln in s.splitlines() for t in doc_number_tokens(ln)] and u"空が 15" not in c.seal:
        out.append(u"§3 の 15 が封 §0 の申告の字と合わない")
    return out


# ======================================================================================================
# e. 要点の字・頭の負けと限界・禁止
def phrase_problems(c):
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]


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
    if ELEMENT_FORM.search(c.doc):
        out.append(u"文書に要素の名の形が在る")
    return out


def doc_commit_problems(c):
    out = []
    want = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)
    for w in want:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    found = set(re.findall(r"\b[0-9a-f]{8}\b", c.doc))
    if not found <= set(want):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"stage0", stage0_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems),
    (u"numbers", doc_number_problems), (u"frag", fragment_problems), (u"sanity", sanity_problems), (u"sec3", sec3_problems), (u"phrases", phrase_problems), (u"head", head_problems),
    (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
# f. git(blob・封・順序・engine・commit)
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
# 変異。予測は実行の前に書いた(下の PREDICT)。1 つの変異が赤にすべき検査の名前の並びを持つ
PREDICT = u"""
M1  書類 1 の段 3 の U を 1 減らす(合計は直さない)                  -> recount・numbers が赤
M2  集計の段 3 の U を 1 増やす                                     -> recount が赤
M3  予測の欄 XG1-3 の行を 1 増やす                                  -> recount が赤
M4  文書の §2 の段 3 の行の 13477 を 13478 にする                    -> frag・numbers が赤
M5  文書の XG1-4 の判定を「当たり」にする                            -> verdict が赤
M6  文書から「測っていない見立て」を消す                             -> phrases が赤
M7  文書に docID の形を足す                                          -> forbidden が赤
M8  記録の段 3 の類 A の一部を U へ整合したまま移し XG1-4 を 15% 以下に -> verdict が赤(recount は緑のまま)
M9  文書の「80% 台が 47 本」を 46 本にする                           -> frag が赤
M10 記録の sha256 の写しを違う値にする                                -> sha が赤
M11 文書の commit の字 762d361e を 762d361f にする                   -> commits が赤
M12 文書 §3 に「約 2800 行」を足す                                    -> sec3・numbers が赤
M13 文書の「当たり 6・外れ 1」を「当たり 7・外れ 0」にする            -> verdict が赤
M14 文書の頭から「この便からは言えない」を消す                        -> head が赤
M15 記録の材料の書類の本数 67 → 68                                   -> recount が赤
M16 文書に「保証」を足す                                             -> forbidden が赤
M17 記録に docid の欄を足す                                          -> clean が赤
M18 文書に 7792 という数字の言い切りを足す                            -> numbers が赤
M19 封の写しから境の字「80% 以上 93% 以下」を消す                      -> bound が赤
M20 文書の頭から「先に負けと限界を書く」を消す                        -> head が赤
M21 文書の「あと 67 行少なければ外れていた」を 66 行にする            -> frag が赤
M22 文書の XG1-4 の「(上に外れた)」を「(下に外れた)」にする          -> verdict が赤
M23 文書 §5 の「80.4%(絞る前は 57.1%)」を 57.2% にする               -> frag が赤
M24 封の写しの「25 本以下」を消す                                     -> bound が赤
M25 記録の書類 3 の U の率を 1 つ変える                               -> recount が赤
M26 文書の「落とした 163 行は 4 本の書類に在る(129・16・15・3)」を(129・16・15・2)にする -> frag が赤(sec3 は 2 を許すので緑)
M27 文書の除いた行ではなく K が決まらない 856 を 855 にする            -> frag・numbers が赤
M28 記録の段 0 の U を 1 増やし A を 1 減らす(整合)                   -> stage0 が赤
M29 文書に要素の名 jppfs_cor:Assets を足す                           -> forbidden が赤
M30 文書の頭の「主の予測 XG1-3 は当たりだが、境に近い」を外れに        -> head・verdict が赤
M31 文書 §3 の「記録に理由の欄は無い」を消す                          -> sec3 が赤
M32 文書の「最小の 1 本を除くと 74.6% 以上」を 74.7% にする           -> frag が赤
M33 文書の XG1-7 の実測 0/67 → 1/67                                  -> verdict が赤
M34 文書 §3 に「2 割」ではなく「400 行」を足す                         -> sec3・numbers が赤
M35 文書の「6 割弱から 8 割」を「5 割弱から 8 割」にする               -> frag が赤
M36 記録の K が決まらない行を書類 1 で 1 増やす(種類の和と合わない)    -> recount が赤
M37 §5 の「次の便の候補」の字を消す(両方当たりなので要る)              -> verdict が赤
M38 記録の落とした行を書類 41 で 129 → 130(整合を直さず)             -> recount・frag が赤
M39 書類 41 の段 3 の U を 100 増やし A を 100 減らす                   -> recount・sanity が赤
"""


def shift_a_to_u(rec, per_doc):
    u"""整合したまま、書類ごとに段 3 の類 A の行を per_doc だけ U へ移す(書類の率・集計・予測の欄も直す)。"""
    for x in rec[u"書類"]:
        x[u"段ごとの類別"][u"段 3"][u"A"] -= per_doc
        x[u"段ごとの類別"][u"段 3"][u"U"] += per_doc
        x[KEY_RATE] = float(pct1(x[u"段ごとの類別"][u"段 3"][u"U"], x[u"計算書の行の数"]))
    f = figures(rec)
    rec[u"集計"][u"段ごとの類別"] = dict((s, dict(v)) for s, v in f["st"].items())
    rec[KEY_PRED] = collections.OrderedDict(pred_expected(f))


def stage0_shift(rec):
    x = rec[u"書類"][0][u"段ごとの類別"][u"段 0"]
    x[u"U"] += 1
    x[u"A"] -= 1
    f = figures(rec)
    rec[u"集計"][u"段ごとの類別"] = dict((s, dict(v)) for s, v in f["st"].items())


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def drop_all(c, phrase):
    assert phrase in c.doc
    c.doc = c.doc.replace(phrase, u"X")


def m_8(c):
    shift_a_to_u(c.rec, 8)


def m_36(c):
    c.rec[u"書類"][0][u"K が決まらない行"] += 1


def m_38(c):
    x = [d for d in c.rec[u"書類"] if d[u"段ごとの落とした行"][u"段 3"] == 129][0]
    x[u"段ごとの落とした行"][u"段 3"] = 130


def m_39(c):
    x = [d for d in c.rec[u"書類"] if d[u"段ごとの落とした行"][u"段 3"] == 129][0][u"段ごとの類別"][u"段 3"]
    x[u"U"] += 100
    x[u"A"] -= 100


MUTATIONS = (
    (u"M1 書類 1 の段 3 の U を 1 減らす", lambda c: c.rec[u"書類"][0][u"段ごとの類別"][u"段 3"].__setitem__(u"U", c.rec[u"書類"][0][u"段ごとの類別"][u"段 3"][u"U"] - 1), (u"recount",)),
    (u"M2 集計の段 3 の U を 1 増やす", lambda c: c.rec[u"集計"][u"段ごとの類別"][u"段 3"].__setitem__(u"U", c.rec[u"集計"][u"段ごとの類別"][u"段 3"][u"U"] + 1), (u"recount",)),
    (u"M3 予測の欄 XG1-3 の行を 1 増やす", lambda c: c.rec[KEY_PRED][PRED_KEYS[2]].__setitem__(u"行", c.rec[KEY_PRED][PRED_KEYS[2]][u"行"] + 1), (u"recount",)),
    (u"M4 文書の §2 の段 3 の行の 13477 を 13478 に", lambda c: rep(c, u"| 段 3(+ 業種の科目の一覧) | 13477(80.4%)", u"| 段 3(+ 業種の科目の一覧) | 13478(80.4%)"), (u"frag", u"numbers")),
    (u"M5 文書の XG1-4 の判定を当たりに", lambda c: rep(c, u"**外れ**(上に外れた)", u"当たり"), (u"verdict",)),
    (u"M6 「測っていない見立て」を消す", lambda c: drop_all(c, u"測っていない見立て"), (u"phrases",)),
    (u"M7 文書に docID の形を足す", lambda c: setattr(c, "doc", c.doc + u"\n書類 S100ABCD。\n"), (u"forbidden",)),
    (u"M8 記録の段 3 の類 A の一部を U へ整合したまま移す(判定が変わる)", m_8, (u"verdict",)),
    (u"M9 文書の「80% 台が 47 本」を 46 本に", lambda c: rep(c, u"80% 台が 47 本", u"80% 台が 46 本"), (u"frag",)),
    (u"M10 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M11 文書の commit の字を 1 字替える", lambda c: rep(c, u"762d361e", u"762d361f", count=9), (u"commits",)),
    (u"M12 文書 §3 に「約 2800 行」を足す", lambda c: rep(c, u"- この読みから:", u"約 2800 行が該当する。\n- この読みから:"), (u"sec3", u"numbers")),
    (u"M13 文書の件数を当たり 7・外れ 0 に", lambda c: rep(c, u"- 当たり 6・外れ 1。", u"- 当たり 7・外れ 0。"), (u"verdict",)),
    (u"M14 頭から「この便からは言えない」を消す", lambda c: rep(c, u"この便からは言えない", u"X", count=1), (u"head",)),
    (u"M15 記録の材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M16 文書に「保証」を足す", lambda c: setattr(c, "doc", c.doc + u"\n保証する。\n"), (u"forbidden",)),
    (u"M17 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M18 文書に 7792 の言い切りを足す", lambda c: setattr(c, "doc", c.doc + u"\n除いた行は 7792 に近い。\n"), (u"numbers",)),
    (u"M19 封の写しから境の字を消す", lambda c: rep(c, u"80% 以上 93% 以下", u"X", attr="seal", count=9), (u"bound",)),
    (u"M20 頭から「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M21 「あと 67 行」を 66 行に", lambda c: rep(c, u"あと 67 行少なければ外れていた", u"あと 66 行少なければ外れていた"), (u"frag",)),
    (u"M22 XG1-4 の外れの向きを替える", lambda c: rep(c, u"**外れ**(上に外れた)", u"**外れ**(下に外れた)"), (u"verdict",)),
    (u"M23 §5 の 57.1% を 57.2% に", lambda c: rep(c, u"(絞る前は 57.1%)", u"(絞る前は 57.2%)"), (u"frag", u"numbers")),
    (u"M24 封の写しの「25 本以下」を消す", lambda c: rep(c, u"25 本以下", u"X", attr="seal", count=9), (u"bound",)),
    (u"M25 記録の書類 3 の U の率を変える", lambda c: c.rec[u"書類"][2].__setitem__(KEY_RATE, 57.0), (u"recount",)),
    (u"M26 「(129・16・15・3)」を「(129・16・15・2)」に", lambda c: rep(c, u"(129・16・15・3)", u"(129・16・15・2)"), (u"frag",)),
    (u"M27 K が決まらない 856 を 855 に", lambda c: rep(c, u"種類が決まらない行は 856(5.1%)", u"種類が決まらない行は 855(5.1%)"), (u"frag", u"numbers")),
    (u"M28 記録の段 0 の U を 1 増やし A を 1 減らす(整合)", lambda c: stage0_shift(c.rec), (u"stage0",)),
    (u"M29 文書に要素の名を足す", lambda c: setattr(c, "doc", c.doc + u"\n要素 jppfs_cor:Assets。\n"), (u"forbidden",)),
    (u"M30 頭の「主の予測 XG1-3 は当たりだが、境に近い」を外れに", lambda c: rep(c, u"主の予測 XG1-3 は当たりだが、境に近い", u"主の予測 XG1-3 は外れ"), (u"head", u"verdict")),
    (u"M31 §3 の「記録に理由の欄は無い」を消す", lambda c: rep(c, u"記録に理由の欄は無い", u"X"), (u"sec3", u"phrases")),
    (u"M32 「74.6% 以上」を 74.7% に", lambda c: rep(c, u"最小の 1 本を除くと 74.6% 以上", u"最小の 1 本を除くと 74.7% 以上"), (u"frag", u"numbers")),
    (u"M33 XG1-7 の実測を 1/67 に", lambda c: rep(c, u"| 0/67 |", u"| 1/67 |"), (u"verdict",)),
    (u"M34 §3 に「400 行」を足す", lambda c: rep(c, u"- この読みから:", u"400 行が該当する。\n- この読みから:"), (u"sec3", u"numbers")),
    (u"M35 「6 割弱から 8 割」を「5 割弱から 8 割」に", lambda c: rep(c, u"6 割弱から 8 割", u"5 割弱から 8 割"), (u"frag",)),
    (u"M36 記録の K が決まらない行を書類 1 で 1 増やす", m_36, (u"recount",)),
    (u"M37 §5 の「次の便の候補」の字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XG1-3 と XG1-5 がどちらも当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M39 書類 41 の段 3 の U を 100 増やし A を 100 減らす(書類ごとの和は合う。最小の率の書類が替わる)", m_39, (u"recount", u"sanity")),
    (u"M38 記録の落とした行を書類 41 で 129 → 130(整合を直さず)", m_38, (u"recount", u"frag")),
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

    def test_b_2_stage0_equals_the_previous_record(self):
        self.assertEqual([], stage0_problems(self.c))

    def test_b_3_the_record_has_no_forbidden_fields_or_forms(self):
        self.assertEqual([], record_clean_problems(self.c))

    def test_b_4_the_per_document_figures_the_document_states(self):
        f = figures(self.c.rec)
        self.assertEqual((509, 810, 896, 746), (f["rates"][0], f["median"], f["rates"][-1], f["rates"][1]))
        self.assertEqual({50: 1, 70: 19, 80: 47}, dict(f["bands"]))
        self.assertEqual(63, f["k_none_docs"])
        self.assertEqual([129, 16, 15, 3], sorted([x[u"段ごとの落とした行"][u"段 3"] for x in f["drop_docs"]], reverse=True))
        self.assertEqual("0.4", pct1(f["st"][u"段 3"]["W"], f["rows"]))
        self.assertEqual("2.4", pct1(f["st"][u"段 3"]["N"], f["rows"]))
        rows, u3 = f["rows"], f["st"][u"段 3"]["U"]
        self.assertEqual(67, u3 - (need_rows_for_80(rows) - 1))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual([u"XG1-4"], [k for k, v in j.items() if not v])
        self.assertEqual(6, sum(1 for v in j.values() if v))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_no_number_the_record_lacks(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_the_important_phrases_without_digits_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms(self):
        self.assertEqual([], forbidden_problems(self.c))

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
        self.assertGreaterEqual(len(MUTATIONS), 30)

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        c = Ctx().copy()
        m_8(c)
        self.assertEqual([], recount_problems(c))
        self.assertNotEqual([], verdict_problems(c))
        self.assertTrue(judge(c.rec)[u"XG1-4"])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_is_made_on_unrounded_numbers(self):
        u"""段 3 の U が 80% に届く最小の行数の 1 行手前は外れ・その数は当たり(丸めると 80.0% になる数でも)。"""
        c = Ctx().copy()
        f = figures(c.rec)
        need = need_rows_for_80(f["rows"])
        d0 = c.rec[u"書類"][0][u"段ごとの類別"][u"段 3"]
        d0[u"U"] += need - 1 - f["st"][u"段 3"]["U"]
        self.assertFalse(judge(c.rec)[u"XG1-3"])
        d0[u"U"] += 1
        self.assertTrue(judge(c.rec)[u"XG1-3"])


if __name__ == "__main__":
    unittest.main()
