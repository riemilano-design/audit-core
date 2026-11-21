# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_TAG_WALL_SEAL_2026-11-21.md(3374e504)の結果の文書 docs/XBRL_TAG_WALL_RESULT_2026-11-21.md。

封の門 ``test_xbrl_tag_wall_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封の sha256(字で留める)と、記録の script の sha256・封の commit の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、集計・予測の判定に要る数(XG0-1〜XG0-6)・書類ごとの率を数え直して記録と同じことを見る
 c 予測 XG0-1〜XG0-6 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し、文書 §1 の表・件数と同じことを見る
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びと同じ(許す数の外の数字は赤)。表の行・散文の言い切りは記録から組んだ字とそのまま照らす。§3 は記録に無い数を持たない
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


SG = load_module("tests/measure/test_xbrl_tag_wall_seal.py", "xbrl_tag_wall_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_tag_wall_result.py"
DOC_REL = "docs/XBRL_TAG_WALL_RESULT_2026-11-21.md"
SCRIPT_COMMIT_SHORT = "5305f855"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "2889cc99"                  # 記録を足した commit
# file ごとの「足した commit」(blob が一致するはずの commit)
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "73de444f7a0a83bd63e221dcc570288a22c37142f9bf7832e93794156b0c2eab"),
    (SCRIPT_REL, "f62a13e8d8b8357c9a8fff02c6ef651a12a071c286f4d20b6f286fe3853f4d55"),
    (SEAL_GATE_REL, "86bbf0020af40614e82d7e1545c0c95dee429cf922b137e95c088274de2d1920"),
    (SEAL_REL, "525104ebc6e5c8f04075984f926f3105360d3b962a08055495664aa63ff73493")])

K_STD, K_SUB = u"標準", u"提出者別"
K_B, K_C, K_D = u"(b) 名が 2 つ以上", u"(c) 接頭辞が jppfs_cor 以外", u"(d) 行の字が無い"
KEY_PRED = u"予測の判定に要る数(XG0-1〜XG0-6。当たり・外れは結果の文書で)"
K1, K2, K3, K4, K5, K6 = (u"XG0-1 提出者別のタグ / 全部のタグ", u"XG0-2 類 U / 計算書の行(表 L2)", u"XG0-3 類 W / 計算書の行(表 L2)",
                          u"XG0-4 類 A / 計算書の行(表 L2)", u"XG0-5 U の率が 90% 以上の書類(表 L2)", u"XG0-6 表 L1 と表 L2 の U の率")
L2, L1 = u"類別(表 L2)", u"類別(表 L1)"
CLS = (u"U", u"A", u"W", u"N")
KEY_RATE = u"U の率(表 L2。%)"
# 封 §4 の境の字(整数の %)。封の文書にこの字が在ることを ``bound_problems`` が見る
BOUND_SEAL_PHRASES = (u"5% 以下", u"60% 以上 85% 以下", u"5% 以上 25% 以下", u"90% 以上", u"10 本以下", u"11 本以上なら外れ", u"5 ポイント以上低い", u"日本基準が 65 本")
HEAD_PHRASES = (u"先に負けと限界を書く", u"この便からは言えない", u"無作為ではない", u"「上の限り」", u"人間に返す", u"専用の道具が組んだ後の字", u"LLM の席は呼んでいない")
PHRASES = (u"測っていない見立て", u"この便からは言えない", u"言えること", u"言えないこと", u"提案はしない", u"分母の外", u"数は記録に無いので書かない", u"盲検ではない",
           u"一部の書類だけが低いのではなく", u"設計として黙る", u"本物の書類の行の字で差が出るかは測っていない", u"人間に返すこと", u"原稿(Word・Excel)の字では、これより下がる見込み",
           u"「科目名から要素を引くだけ」では 4 割強の行が決まらない", u"位置や計算書の種類で絞れば何 % になるか", u"封じる前に 1 本の書類のタグの数を見てから立てた",
           u"類 A は標準タクソノミのラベルの表の性質から出ている", u"絞った後に 1 つに決まる行がどれだけかは **測っていない**")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")
ELEMENT_FORM = re.compile(r"jp[a-z]*_cor[:_][A-Za-z]")                    # 要素の名(接頭辞だけの `jppfs_cor` は可)


# ======================================================================================================
# 道具
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


def figures(rec):
    u"""書類ごとの数から、門の側で集計を作る(script の関数は使わない)。"""
    docs = rec[u"書類"]
    f = dict(ndocs=len(docs))
    f["std"] = sum(x[u"タグの数"][K_STD] for x in docs)
    f["sub"] = sum(x[u"タグの数"][K_SUB] for x in docs)
    f["rows"] = sum(x[u"計算書の行の数"] for x in docs)
    f["b"], f["c"], f["d"] = [sum(x[u"分母に入れなかった行の数"][k] for x in docs) for k in (K_B, K_C, K_D)]
    f["excluded"] = f["b"] + f["c"] + f["d"]
    f["L2"] = collections.OrderedDict((k, sum(x[L2][k] for x in docs)) for k in CLS)
    f["L1"] = collections.OrderedDict((k, sum(x[L1][k] for x in docs)) for k in CLS)
    with_rows = [x for x in docs if x[u"計算書の行の数"] > 0]
    f["with_rows"] = len(with_rows)
    f["rates"] = sorted(tenths(x[L2][u"U"], x[u"計算書の行の数"]) for x in with_rows)        # 0.1 刻みの整数
    f["u90"] = sum(1 for x in with_rows if x[L2][u"U"] * 100 >= 90 * x[u"計算書の行の数"])
    n = len(f["rates"])
    f["median"] = f["rates"][n // 2] if n % 2 else (f["rates"][n // 2 - 1] + f["rates"][n // 2] + 1) // 2
    f["bands"] = collections.Counter(t // 100 * 10 for t in f["rates"])                 # 40・50・60 台の本数
    f["w_docs"] = sum(1 for x in docs if x[L2][u"W"] > 0)
    f["w_max"] = max(x[L2][u"W"] for x in docs)
    return f


def tstr(t):
    return u"%d.%d" % divmod(t, 10)


def judge(rec):
    u"""封 §4 の境と記録から XG0-1〜XG0-6 の当たり外れを決め直す(整数の計算。判定は丸める前の数。境は封の字: ``bound_problems`` が封の文書と照らす)。"""
    f = figures(rec)
    u2, u1, a2, w2, rows = f["L2"]["U"], f["L1"]["U"], f["L2"]["A"], f["L2"]["W"], f["rows"]
    out = collections.OrderedDict()
    out[u"XG0-1"] = f["sub"] * 100 <= 5 * (f["std"] + f["sub"])
    out[u"XG0-2"] = 60 * rows <= 100 * u2 <= 85 * rows
    out[u"XG0-3"] = 100 * w2 <= 5 * rows
    out[u"XG0-4"] = 5 * rows <= 100 * a2 <= 25 * rows
    out[u"XG0-5"] = f["u90"] <= 10
    out[u"XG0-6"] = (u2 - u1) * 100 >= 5 * rows
    return out


def direction(rec, key):
    u"""外れの向き(境の下か上か)。"""
    f = figures(rec)
    if key == u"XG0-2":
        return u"下" if 100 * f["L2"]["U"] < 60 * f["rows"] else u"上"
    if key == u"XG0-4":
        return u"下" if 100 * f["L2"]["A"] < 5 * f["rows"] else u"上"
    return u""


def pred_expected(f):
    return collections.OrderedDict([
        (K1, dict([(u"タグ", f["sub"]), (u"分母", f["std"] + f["sub"]), (u"%", float(pct1(f["sub"], f["std"] + f["sub"])))])),
        (K2, dict([(u"行", f["L2"]["U"]), (u"分母", f["rows"]), (u"%", float(pct1(f["L2"]["U"], f["rows"])))])),
        (K3, dict([(u"行", f["L2"]["W"]), (u"分母", f["rows"]), (u"%", float(pct1(f["L2"]["W"], f["rows"])))])),
        (K4, dict([(u"行", f["L2"]["A"]), (u"分母", f["rows"]), (u"%", float(pct1(f["L2"]["A"], f["rows"])))])),
        (K5, dict([(u"書類", f["u90"]), (u"分母", f["with_rows"])])),
        (K6, dict([(u"表 L2 の U の行", f["L2"]["U"]), (u"表 L1 の U の行", f["L1"]["U"]), (u"分母", f["rows"]),
                   (u"表 L2 の %", float(pct1(f["L2"]["U"], f["rows"]))), (u"表 L1 の %", float(pct1(f["L1"]["U"], f["rows"]))),
                   (u"L2 から L1 を引いた差(ポイント)", float(pct1(f["L2"]["U"] - f["L1"]["U"], f["rows"])))]))])


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
    if [x[u"番号"] for x in docs] != list(range(1, f["ndocs"] + 1)):
        out.append(u"書類の番号が 1 から順でない")
    if rec[u"材料"][u"書類の本数"] != f["ndocs"]:
        out.append(u"材料の書類の本数が書類の数と違う")
    for x in docs:
        n, rows = x[u"番号"], x[u"計算書の行の数"]
        for key in (L2, L1):
            if sum(x[key][k] for k in CLS) != rows:
                out.append(u"書類 %d の %s の和が計算書の行の数と違う" % (n, key))
        if rows > 0 and x[KEY_RATE] != float(pct1(x[L2][u"U"], rows)):
            out.append(u"書類 %d の U の率が数え直しと違う" % n)
    agg = rec[u"集計"]
    if agg[u"タグの数"] != {K_STD: f["std"], K_SUB: f["sub"]}:
        out.append(u"集計のタグの数が書類ごとの和と違う")
    if agg[u"計算書の行の数"] != f["rows"]:
        out.append(u"集計の計算書の行の数が書類ごとの和と違う")
    if agg[u"分母に入れなかった行の数"] != {K_B: f["b"], K_C: f["c"], K_D: f["d"]}:
        out.append(u"集計の分母に入れなかった行の数が書類ごとの和と違う")
    if agg[L2] != dict(f["L2"]) or agg[L1] != dict(f["L1"]):
        out.append(u"集計の類別が書類ごとの和と違う")
    if agg[u"計算書の行が 1 行以上在る書類の数"] != f["with_rows"] or agg[u"計算書の行が 0 で書類ごとの数から外した書類の数"] != f["ndocs"] - f["with_rows"]:
        out.append(u"集計の書類の数の欄が違う")
    pred = rec[KEY_PRED]
    want = pred_expected(f)
    if list(pred.keys()) != list(want.keys()):
        out.append(u"予測の判定に要る数の欄の名・順が違う")
    for k, v in want.items():
        if dict(pred.get(k, {})) != v:
            out.append(u"予測の判定に要る数が数え直しと違う: %s" % k[:6])
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    scan = re.sub(r"[0-9a-fA-F]{32,}", u"", text)
    out = []
    if DOCID_FORM.search(scan) or ECODE_FORM.search(scan):
        out.append(u"記録に docID か EDINET コードの形が在る")
    bad = [k for k in SG.MS.walk_keys(c.rec) if str(k).lower() in SG.MS.FORBIDDEN_KEYS]
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
    tot = f["std"] + f["sub"]
    actual = {
        u"XG0-1": u"%d/%d(%s%%)" % (f["sub"], tot, pct1(f["sub"], tot)),
        u"XG0-2": u"%d/%d(%s%%)" % (f["L2"]["U"], f["rows"], pct1(f["L2"]["U"], f["rows"])),
        u"XG0-3": u"%d/%d(%s%%)" % (f["L2"]["W"], f["rows"], pct1(f["L2"]["W"], f["rows"])),
        u"XG0-4": u"%d/%d(%s%%)" % (f["L2"]["A"], f["rows"], pct1(f["L2"]["A"], f["rows"])),
        u"XG0-5": u"%d/%d" % (f["u90"], f["with_rows"]),
        u"XG0-6": u"L2 %s%%・L1 %s%%(差 %s ポイント)" % (pct1(f["L2"]["U"], f["rows"]), pct1(f["L1"]["U"], f["rows"]), pct1(f["L2"]["U"] - f["L1"]["U"], f["rows"]))}
    out = collections.OrderedDict()
    for k in j:
        if j[k]:
            verdict = u"当たり"
        else:
            d = direction(c.rec, k)
            verdict = u"**外れ**" + (u"(%sに外れた)" % d if d else u"")
        out[k] = (actual[k], verdict)
    return out


def verdict_problems(c):
    u"""文書 §1 の表と件数が、記録から決め直した判定と同じ。"""
    j = judge(c.rec)
    want = expected_verdict_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XG0-\d) \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XG0-1〜XG0-6 でない"]
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
    if u"当たり %d・外れ %d。" % (hits, len(j) - hits) not in c.doc.split(u"## §1")[0]:
        out.append(u"文書の頭の件数が決め直した件数と違う")
    head = c.doc.split(u"## §1")[0]
    for k, v in j.items():
        if not v:
            if u"%s は外れ" % k not in head and u"%s も外れ" % k not in head:
                out.append(u"文書の頭が外れた %s を言っていない" % k)
        else:
            if u"%s は外れ" % k in head or u"%s も外れ" % k in head:
                out.append(u"文書の頭が当たった %s を外れと言う" % k)
    if not j[u"XG0-2"] and u"主の予測 XG0-2 は外れ" not in head:
        out.append(u"主の予測の外れを頭が言っていない")
    if not j[u"XG0-2"] and u"次の便" not in head:
        out.append(u"XG0-2 が外れたときの封 §6 の決め(次の便は提案しない)が頭に無い")
    return out


# ======================================================================================================
# d. 文書の数
def section(doc, head, nxt):
    u"""``head`` で始まる節の本文(次の節の見出しまで)。"""
    i = doc.index(head)
    j = doc.index(nxt, i + len(head)) if nxt else len(doc)
    return doc[i:j]


def expected_lines(c):
    u"""文書に 1 行まるごと在るべき字(表の行)を記録から組む。"""
    f = figures(c.rec)
    out = [u"| U(1 つに決まり、正しい) | %d | %d |" % (f["L2"]["U"], f["L1"]["U"]),
           u"| A(候補に在るが 1 つに決まらない) | %d | %d |" % (f["L2"]["A"], f["L1"]["A"]),
           u"| W(当たるが違う) | %d | %d |" % (f["L2"]["W"], f["L1"]["W"]),
           u"| N(当たらない) | %d | %d |" % (f["L2"]["N"], f["L1"]["N"]),
           u"| 合計(計算書の行) | %d | %d |" % (f["rows"], f["rows"]),
           u"| | 表 L2(主。役割 %d・ラベルの字 %d) | 表 L1(副。標準の役割だけ・ラベルの字 %d) |" % (
               c.rec[u"材料"][u"表 L2 の role の数"], c.rec[u"材料"][u"表 L2 のラベルの字の数"], c.rec[u"材料"][u"表 L1 のラベルの字の数"]),
           u"- タグの数: 標準 %d・提出者別 %d(合計 %d)。" % (f["std"], f["sub"], f["std"] + f["sub"]),
           u"- 書類ごとの U の率(表 L2。%d 本): 最小 %s%%・中央 %s%%・最大 %s%%。%d0%% 台が %d 本・%d0%% 台が %d 本・%d0%% 台が %d 本。**書類による差は小さい** ― 一部の書類だけが低いのではなく、どの書類でも 4 割前後の行が 1 つに決まらない。" % (
               f["with_rows"], tstr(f["rates"][0]), tstr(f["median"]), tstr(f["rates"][-1]),
               4, f["bands"][40], 5, f["bands"][50], 6, f["bands"][60]),
           u"- 類 W が 1 行以上在る書類は %d 本(1 本の中で最大 %d 行)。引き当てだけで付けると黙って違う要素になる行は少ないが、0 ではない。" % (f["w_docs"], f["w_max"])]
    return out


def expected_fragments(c):
    u"""文書の散文に在るべき字(数を含む言い切り)を記録から組む。"""
    f = figures(c.rec)
    u2, a2, w2, n2, u1, rows = f["L2"]["U"], f["L2"]["A"], f["L2"]["W"], f["L2"]["N"], f["L1"]["U"], f["rows"]
    tot = f["std"] + f["sub"]
    return [
        u"類 U)は %d/%d(%s%%)" % (u2, rows, pct1(u2, rows)),
        u"類 A)は %d/%d(%s%%)" % (a2, rows, pct1(a2, rows)),
        u"除いた行は %d(名が 2 つ以上 %d・接頭辞が `jppfs_cor` 以外 %d・行の字が無い %d)" % (f["excluded"], f["b"], f["c"], f["d"]),
        u"計算書の行 %d の半分に近い量" % rows,
        u"置き場に在った有価証券報告書 %d 本" % f["ndocs"],
        u"提出者別の要素のタグは全部のタグの %s%%" % pct1(f["sub"], tot),
        u"言えること: この %d 本の有価証券報告書の、名が 1 つで `jppfs_cor` の計算書の行 %d のうち" % (f["ndocs"], rows),
        u"要素が 1 つに決まって正しかったのは %s%%。%s%% は正しい要素が候補に在るが 1 つに決まらず、%s%% は違う要素だけに当たり、%s%% は当たらなかった" % (
            pct1(u2, rows), pct1(a2, rows), pct1(w2, rows), pct1(n2, rows)),
        u"標準の役割のラベルだけ(表 L1)では %s%% に下がる" % pct1(u1, rows),
        u"監査の席が script の関数を使わずに %d 本の全部を数え直し" % f["ndocs"],
    ]


def structural_numbers():
    u"""記録の外の、文書が言う数(封・script の字・文書の言い回しで決まっているもの)。"""
    return set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"9", u"10", u"20", u"25", u"40", u"50", u"60", u"85", u"90", u"95", u"65", u"67"])


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"XG0-\d", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def allowed_numbers(c):
    f = figures(c.rec)
    allowed = set(structural_numbers())
    allowed |= set(str(x) for x in (f["std"], f["sub"], f["std"] + f["sub"], f["rows"], f["excluded"], f["b"], f["c"], f["d"], f["ndocs"], f["with_rows"], f["u90"],
                                    f["w_docs"], f["w_max"], f["L2"]["U"], f["L2"]["A"], f["L2"]["W"], f["L2"]["N"], f["L1"]["U"], f["L1"]["A"], f["L1"]["W"], f["L1"]["N"]))
    allowed |= set(str(f["bands"][b]) for b in (40, 50, 60))
    m = c.rec[u"材料"]
    allowed |= set(str(m[k]) for k in (u"表 L2 の role の数", u"表 L2 のラベルの字の数", u"表 L1 のラベルの字の数"))
    u2, u1, rows, tot = f["L2"]["U"], f["L1"]["U"], f["rows"], f["std"] + f["sub"]
    allowed |= set([pct1(f["sub"], tot), pct1(u2, rows), pct1(f["L2"]["A"], rows), pct1(f["L2"]["W"], rows), pct1(f["L2"]["N"], rows), pct1(u1, rows), pct1(u2 - u1, rows),
                    tstr(f["rates"][0]), tstr(f["median"]), tstr(f["rates"][-1])])
    return allowed


def sec3_problems(c):
    u"""§3 は「数は記録に無いので書かない」節。数字は番号・「3 つ」「2 度」・本数の 67 だけ。行数・% を持たない。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    toks = []
    for ln in s.splitlines():
        toks.extend(doc_number_tokens(ln))
    allowed = set([u"1", u"2", u"3", u"67"])
    for t in toks:
        if t not in allowed:
            out.append(u"§3 に記録に無い数 %s" % t)
    if re.search(r"\d\s*(行|%|％|割|件|倍)", re.sub(r"`[^`]*`", u"", s)):
        out.append(u"§3 に数と単位(行・%・割・件・倍)の並びが在る")
    if u"数は記録に無いので書かない" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「数は記録に無いので書かない」でない")
    return out


def doc_number_problems(c):
    u"""数字を含む行は全部、記録から組んだ数の並びの内(許す数の外の数字は赤)・表の行・言い切りは記録から組んだ字と同じ。塊(表)の外の行も同じに見る。"""
    f = figures(c.rec)
    allowed = allowed_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in doc_number_tokens(ln):
            t = tok.replace(u",", u"")
            if t not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    lines = c.doc.splitlines()
    for want in expected_lines(c):
        if want not in lines:
            out.append(u"文書に記録から組んだ行が無い: %s" % want[:40])
    for frag in expected_fragments(c):
        if frag not in c.doc:
            out.append(u"文書に記録から組んだ字が無い: %s" % frag[:40])
    if not (4 * f["excluded"] <= 3 * f["rows"] and 2 * f["excluded"] >= f["rows"] * 0.8):          # 「半分に近い」(40% 台〜75% 以下)
        out.append(u"除いた行が計算書の行の「半分に近い量」でない")
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
    u"""文書が書く commit の字が封・script・記録の commit と同じ。"""
    out = []
    want = (SEAL_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT)
    for w in want:
        if w not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % w)
    found = set(re.findall(r"\b[0-9a-f]{8}\b", c.doc))
    if not found <= set(want):
        out.append(u"文書が知らない commit の字を書いている")
    return out


def silent_by_design_problems(c):
    u"""§4 の「設計として黙る変異が 2 本」が封の門の申告の本数と同じ。"""
    out = []
    n = len(SG.SILENT_BY_DESIGN)
    if u"設計として黙る」と申告した変異が %d 本" % n not in c.doc:
        out.append(u"文書の黙る変異の本数が封の門の申告と違う")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems),
    (u"numbers", doc_number_problems), (u"sec3", sec3_problems), (u"phrases", phrase_problems), (u"head", head_problems), (u"forbidden", forbidden_problems),
    (u"commits", doc_commit_problems), (u"silent", silent_by_design_problems)])


# ======================================================================================================
# f. git(blob・封・順序・engine・commit)
def blob_problems(root, prefix, at):
    u"""``at`` = {相対 path: 足した commit}。木の file が、その commit の blob と 1 byte も違わない。"""
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
    u"""封 ⊏ script と封の門 ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。script と封の門を足した commit が 5305f855・記録を足した commit が 2889cc99。"""
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
M1  書類 1 の表 L2 の U を 1 減らす(合計は直さない)              -> recount・numbers が赤
M2  集計の表 L2 の U を 9571 → 9572                             -> recount が赤
M3  予測の欄 XG0-2 の行を 1 増やす                               -> recount が赤
M4  文書の表の合計 16763 を 16764 にする                          -> numbers が赤
M5  文書の XG0-2 の判定を「当たり」にする                         -> verdict が赤
M6  文書から「測っていない見立て」を消す                          -> phrases が赤
M7  文書に docID の形を足す                                       -> forbidden が赤
M8  記録の類 A の一部を U へ整合したまま移し XG0-2 を 60% 以上に(記録の全部の欄を直す) -> verdict が赤(recount は緑のまま)
M9  文書の「50% 台が 54 本」を 53 本にする                        -> numbers が赤
M10 記録の sha256 の写しを違う値にする                             -> sha が赤
M11 文書の commit の字 5305f855 を 5305f856 にする                -> commits が赤
M12 文書 §3 に「約 2800 行」を足す                                -> sec3 が赤(numbers も)
M13 文書の「当たり 4・外れ 2」を「当たり 5・外れ 1」にする         -> verdict が赤
M14 文書から「人間に返す」を消す(頭の「人間に返す」「人間に返すこと」の全部) -> head が赤
M15 記録の材料の書類の本数 67 → 68                                -> recount が赤
M16 文書に「保証」を足す                                          -> forbidden が赤
M17 記録に docid の欄を足す                                       -> clean が赤
M18 文書の本文に 7792 という数字の言い切りを足す                    -> numbers が赤
M19 封の写しから境の字「60% 以上 85% 以下」を消す                   -> bound が赤
M20 文書の頭から「先に負けと限界を書く」を消す                      -> head が赤
M21 文書の XG0-6 の「差 17.5 ポイント」を 17.4 にする               -> verdict が赤
M22 文書の XG0-4 の「(上に外れた)」を「(下に外れた)」にする         -> verdict が赤
M23 文書 §5 の「57.1%。41.0% は」を「57.2%。41.0% は」にする         -> numbers が赤
M24 封の写しの「日本基準が 65 本」を消す                            -> bound が赤
M25 記録の書類 3 の U の率を 56.0 → 57.0                           -> recount が赤
M26 文書の「最大 9 行」を「最大 8 行」にする                         -> numbers が赤
M27 文書の除いた行 7791 を 7790 にする                              -> numbers が赤
M28 文書の頭から「この便からは言えない」を全部消す                   -> head が赤
M29 文書に要素の名 jppfs_cor:Assets を足す                          -> forbidden が赤
M30 文書の頭の「主の予測 XG0-2 は外れ」を「主の予測 XG0-2 は当たり」に -> verdict が赤
M31 文書 §3 の見出しの「数は記録に無いので書かない」を消す           -> sec3 が赤
M32 文書の「設計として黙る」と申告した変異の 2 本 → 3 本            -> silent が赤
M33 文書の XG0-5 の実測 0/67 → 1/67                                -> verdict が赤
M34 文書 §3 に「2 割」を足す(割は数の単位)                         -> sec3 が赤
"""


def bump(rec, doc_idx, cls, delta):
    rec[u"書類"][doc_idx][L2][cls] += delta


def shift_a_to_u(rec, per_doc):
    u"""整合したまま、書類ごとに類 A の行を per_doc だけ U へ移す(書類の率・集計・予測の欄も直す)。"""
    for x in rec[u"書類"]:
        x[L2][u"A"] -= per_doc
        x[L2][u"U"] += per_doc
        x[KEY_RATE] = float(pct1(x[L2][u"U"], x[u"計算書の行の数"]))
    f = figures(rec)
    rec[u"集計"][L2] = dict(f["L2"])
    rec[KEY_PRED] = collections.OrderedDict(pred_expected(f))


def m_1(c):
    bump(c.rec, 0, u"U", -1)


def m_2(c):
    c.rec[u"集計"][L2][u"U"] += 1


def m_3(c):
    c.rec[KEY_PRED][K2][u"行"] += 1


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def m_8(c):
    shift_a_to_u(c.rec, 8)


def m_17(c):
    c.rec[u"書類"][0][u"docid"] = u"x"


def m_25(c):
    c.rec[u"書類"][2][KEY_RATE] = 57.0


def m_30(c):
    rep(c, u"主の予測 XG0-2 は外れ", u"主の予測 XG0-2 は当たり")


def drop_all(c, phrase):
    assert phrase in c.doc
    c.doc = c.doc.replace(phrase, u"X")


MUTATIONS = (
    (u"M1 書類 1 の表 L2 の U を 1 減らす(合計は直さない)", m_1, (u"recount", u"numbers")),
    (u"M2 集計の表 L2 の U を 1 増やす", m_2, (u"recount",)),
    (u"M3 予測の欄 XG0-2 の行を 1 増やす", m_3, (u"recount",)),
    (u"M4 文書の表の合計を 16764 に", lambda c: rep(c, u"| 合計(計算書の行) | 16763 | 16763 |", u"| 合計(計算書の行) | 16764 | 16763 |"), (u"numbers",)),
    (u"M5 文書の XG0-2 の判定を当たりに", lambda c: rep(c, u"**外れ**(下に外れた)", u"当たり"), (u"verdict",)),
    (u"M6 「測っていない見立て」を消す", lambda c: drop_all(c, u"測っていない見立て"), (u"phrases",)),
    (u"M7 文書に docID の形を足す", lambda c: setattr(c, "doc", c.doc + u"\n書類 S100ABCD。\n"), (u"forbidden",)),
    (u"M8 記録の類 A の一部を U へ整合したまま移す(判定が変わる)", m_8, (u"verdict",)),
    (u"M9 文書の「50% 台が 54 本」を 53 本に", lambda c: rep(c, u"50% 台が 54 本", u"50% 台が 53 本"), (u"numbers",)),
    (u"M10 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M11 文書の commit の字を 1 字替える", lambda c: rep(c, u"5305f855", u"5305f856", count=9), (u"commits",)),
    (u"M12 文書 §3 に「約 2800 行」を足す", lambda c: rep(c, u"1. **業種別の要素", u"約 2800 行が該当する。\n1. **業種別の要素"), (u"sec3", u"numbers")),
    (u"M13 文書の件数を当たり 5・外れ 1 に", lambda c: rep(c, u"- 当たり 4・外れ 2。", u"- 当たり 5・外れ 1。"), (u"verdict",)),
    (u"M14 「人間に返す」を全部消す", lambda c: drop_all(c, u"人間に返す"), (u"head",)),
    (u"M15 記録の材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M16 文書に「保証」を足す", lambda c: setattr(c, "doc", c.doc + u"\n保証する。\n"), (u"forbidden",)),
    (u"M17 記録に docid の欄を足す", m_17, (u"clean",)),
    (u"M18 文書に 7792 の言い切りを足す", lambda c: setattr(c, "doc", c.doc + u"\n除いた行は 7792 に近い。\n"), (u"numbers",)),
    (u"M19 封の写しから境の字を消す", lambda c: rep(c, u"60% 以上 85% 以下", u"X", attr="seal", count=9), (u"bound",)),
    (u"M20 頭から「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M21 XG0-6 の差を 17.4 に", lambda c: rep(c, u"差 17.5 ポイント", u"差 17.4 ポイント"), (u"verdict",)),
    (u"M22 XG0-4 の外れの向きを替える", lambda c: rep(c, u"**外れ**(上に外れた)", u"**外れ**(下に外れた)"), (u"verdict",)),
    (u"M23 §5 の 57.1% を 57.2% に", lambda c: rep(c, u"57.1%。41.0% は", u"57.2%。41.0% は"), (u"numbers",)),
    (u"M24 封の写しの「日本基準が 65 本」を消す", lambda c: rep(c, u"日本基準が 65 本", u"X", attr="seal"), (u"bound",)),
    (u"M25 記録の書類 3 の U の率を 57.0 に", m_25, (u"recount",)),
    (u"M26 「最大 9 行」を「最大 8 行」に", lambda c: rep(c, u"最大 9 行", u"最大 8 行"), (u"numbers",)),
    (u"M27 除いた行 7791 を 7790 に", lambda c: rep(c, u"除いた行は 7791", u"除いた行は 7790"), (u"numbers",)),
    (u"M28 頭から「この便からは言えない」を全部消す", lambda c: drop_all(c, u"この便からは言えない"), (u"head",)),
    (u"M29 文書に要素の名を足す", lambda c: setattr(c, "doc", c.doc + u"\n要素 jppfs_cor:Assets。\n"), (u"forbidden",)),
    (u"M30 頭の「主の予測 XG0-2 は外れ」を当たりに", m_30, (u"verdict",)),
    (u"M31 §3 の見出しの「数は記録に無いので書かない」を消す", lambda c: rep(c, u"数は記録に無いので書かない", u"数あり"), (u"sec3",)),
    (u"M32 黙る変異の本数 2 本を 3 本に", lambda c: rep(c, u"申告した変異が 2 本", u"申告した変異が 3 本"), (u"silent",)),
    (u"M33 XG0-5 の実測を 1/67 に", lambda c: rep(c, u"| 0/67 |", u"| 1/67 |"), (u"verdict",)),
    (u"M34 §3 に「2 割」を足す", lambda c: rep(c, u"1. **業種別の要素", u"2 割が該当する。\n1. **業種別の要素"), (u"sec3",)),
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

    def test_b_3_the_per_document_figures_the_document_states(self):
        f = figures(self.c.rec)
        self.assertEqual((49.6, 57.0, 65.2), (f["rates"][0] / 10.0, f["median"] / 10.0, f["rates"][-1] / 10.0))
        self.assertEqual({40: 1, 50: 54, 60: 12}, dict(f["bands"]))
        self.assertEqual((30, 9), (f["w_docs"], f["w_max"]))
        self.assertEqual(7791, f["excluded"])
        self.assertEqual("1.5", pct1(f["L2"]["N"], f["rows"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(self.c.rec)
        self.assertEqual([u"XG0-2", u"XG0-4"], [k for k, v in j.items() if not v])
        self.assertEqual(4, sum(1 for v in j.values() if v))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_section3_holds_no_number_the_record_lacks(self):
        self.assertEqual([], sec3_problems(self.c))

    def test_e_1_the_important_phrases_without_digits_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_losses_and_limits_are_at_the_head(self):
        self.assertEqual([], head_problems(self.c))

    def test_e_3_the_document_has_no_forbidden_words_or_forms(self):
        self.assertEqual([], forbidden_problems(self.c))

    def test_e_4_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_e_5_the_silent_mutation_count_the_document_states(self):
        self.assertEqual([], silent_by_design_problems(self.c))

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
        r2 = PR.Repo()
        r2.put("fix/r.json")
        r2.commit("fix/r.json")
        r2.put("docs/seal.md")
        s2 = r2.commit("docs/seal.md")
        r2.put("measure/s.py")
        r2.commit("measure/s.py")
        self.assertNotEqual([], PR.order_problems(r2.d, PREFIX, "docs/seal.md", s2[:7], ["measure/s.py"], ["fix/r.json"]))

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

    def test_g_2_the_unmutated_copy_is_green_on_every_check(self):
        c = Ctx().copy()
        for k, fn in CHECKS.items():
            self.assertEqual([], fn(c), k)

    def test_g_3_the_recount_stays_green_when_the_data_changes_consistently_but_the_verdict_does_not(self):
        c = Ctx().copy()
        m_8(c)
        self.assertEqual([], recount_problems(c))
        self.assertNotEqual([], verdict_problems(c))
        self.assertTrue(judge(c.rec)[u"XG0-2"])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_is_made_on_unrounded_numbers(self):
        u"""丸めると境の内に入る数でも、丸める前の数で外れなら外れ(XG0-2 の境 60% の 1 行手前)。"""
        c = Ctx().copy()
        f = figures(c.rec)
        need = (60 * f["rows"] + 99) // 100                      # 60% に届く最小の行数
        c.rec[u"書類"][0][L2][u"U"] += need - 1 - f["L2"]["U"]
        self.assertFalse(judge(c.rec)[u"XG0-2"])
        c.rec[u"書類"][0][L2][u"U"] += 1
        self.assertTrue(judge(c.rec)[u"XG0-2"])


if __name__ == "__main__":
    unittest.main()
