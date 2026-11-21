# -*- coding: utf-8 -*-
"""結果の門: 封 docs/CTGOV_WALL_SEAL_2026-11-21.md(9e41971b・追記 §8 455c77a6)の結果の文書 docs/CTGOV_WALL_RESULT_2026-11-21.md。

封の門 ``test_ctgov_wall_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(材料は読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封の sha256(字で留める)と、記録の script の sha256・封の commit・追記の commit の欄
 b 記録の数え直し: 対ごとの数から、**script の関数を使わずに**、集計・取り方の数の整合(見た試験 = 対 + 飛ばした試験・呼び出し = 版 1 + ページ + efetch)・予測の判定に要る数(CT0-1〜CT0-7)を数え直して記録と同じことを見る
 c 予測 CT0-1〜CT0-7 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し、文書 §1 の表(判定・実測の字・あと何字で境をまたぐか)・件数と同じことを見る
 d 結果の文書の数: 数字を含む行は全部(塊の外の表の行も)、記録から組んだ数の並びと同じ(許す数の外の数字は赤)。表の行と散文の言い切りは記録から組んだ字とそのまま照らす
 e 文書の要点の字(数字を含まない大事な字)・禁止語・登録番号と PMID の形(門は実際の番号を持たない)
 f 封が commit から 1 字も変わっていない(履歴の 2 commit)・engine は封の commit から 0 行・順序(封 ⊏ 追記 ⊏ script ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤)・文書が書く commit の字
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


SG = load_module("tests/measure/test_ctgov_wall_seal.py", "ctgov_wall_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SEAL_ADDENDUM_SHORT = SG.SEAL_ADDENDUM_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_ctgov_wall_result.py"
DOC_REL = "docs/CTGOV_WALL_RESULT_2026-11-21.md"
RECORD_COMMIT_SHORT = "afea7515"                  # 記録を足した commit(履歴から探した値と照らす)
SCRIPT_COMMIT_SHORT = "859cb911"                  # 記録を書いた版の script の最後の commit
SCRIPT_FIRST_COMMIT_SHORT = "4183b875"            # script を足した commit

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "f3a7dfc55878250170f8a126b62850ab3b9649c9666a22ad8610cb6a4741fed9"),
    (SCRIPT_REL, "945a902558d575c37335a86948da2968fb178b3c41bd62a4f09d0612b5b423a6"),
    (SEAL_GATE_REL, "fa958ecc4d7aaa2bd61c34ea92c54177a7c779c979056e9d4a56b8dc2ebb7909"),
    (SEAL_REL, "515019a0718e298dabed7942bb55191fbe26f6a8b839528701995c6f86fbaee7")])

CLASSES = ("P", "C", "N", "R", "V", "Y", "O")
CLASS_LABEL = {"P": u"P(直後が `%`)", "C": u"C(信頼区間の中)", "N": u"N(人数)", "R": u"R(ハザード比・オッズ比・リスク比)", "V": u"V(p 値)", "Y": u"Y(年)", "O": u"O(それ以外)"}
PAIRS_WANT, STUDIES_STOP = 10, 400                # 封 §1(封の門が封の字と照らす)
# 封 §4 の境(整数の %)。当たりの向きと、境の値。封の文書にこの字が在ることを ``bound_problems`` が見る
BOUND_SEAL_PHRASES = (u"30% 以下", u"31% 以上", u"80% 以上", u"79% 以下", u"5% 以下", u"6% 以上", u"20% 以下", u"21% 以上", u"5 以下", u"6 以上", u"1 行以上", u"400 試験で 9 対以下なら外れ")
KEY_PRED = u"予測の判定に要る数(CT0-1〜CT0-7。当たり・外れは結果の文書で)"
K1, K2, K3, K4, K5, K6, K7 = (u"CT0-1 見た試験と対の数と止めた理由", u"CT0-2 拾った / 数の字の全部", u"CT0-3 類 P で拾った / 類 P", u"CT0-4 類 N・R・V の合計で拾った / 合計",
                              u"CT0-5 類 C で拾った / 類 C", u"CT0-6 分母の外で拾った(10 対の合計)", u"CT0-7 登録の側の値の読める行が 0 の対の数")
PHRASES = (u"実走の間隔は測っていない", u"記録に呼び出しの時刻は無く", u"表に組めるか・結べるかは測っていない", u"門ではない", u"「名の替えが数を変えない」は門で縛っていない", u"測っていない見立て", u"人間に返す", u"当たりやすい予測", u"無作為ではない", u"数の字", u"大半拾わない", u"結ぶところ", u"別の封が先に要る", u"言えないこと", u"言えること",
           u"engine を変える(人間の承認)", u"盲検ではない", u"LLM の席は呼んでいない", u"「医薬で使える」", u"作りの範囲の外", u"先に負けと限界を書く", u"10 本・無作為でない・数の字の分母", u"依頼文 §4(結べた数・止めた数)へは進まずに人間に返す")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
NCT_FORM = re.compile(r"NCT\s*\d", re.I)
PMID_FORM = re.compile(r"PMID|(?<![0-9])\d{7,8}(?![0-9])", re.I)
DOCID_FORM = re.compile(r"S[0-9A-Z]{3}[0-9A-Z]{4}")           # EDINET の docID の形(この門は持たない)


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


def pct1(n, d):
    u"""小数 1 桁の %(四捨五入は整数の計算。門の側で独立に書く)。"""
    return u"%d.%d" % divmod((n * 2000 + d) // (2 * d), 10)


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


def tallies(rec):
    u"""対ごとの数から、門の側で集計を作る(script の関数は使わない)。"""
    den = collections.OrderedDict((c, 0) for c in CLASSES)
    pick = collections.OrderedDict((c, 0) for c in CLASSES)
    outside = 0
    zero = 0
    for p in rec[u"対"]:
        for c in CLASSES:
            den[c] += p[u"類別"][c][u"分母"]
            pick[c] += p[u"類別"][c][u"拾った"]
        outside += p[u"分母の外で拾った数"]
        zero += 1 if p[u"登録の側の値の読める行の数"] == 0 else 0
    return den, pick, outside, zero


def figures(rec):
    u"""記録の数から作る、文書に出る数の一式。"""
    den, pick, outside, zero = tallies(rec)
    d, k = sum(den.values()), sum(pick.values())
    nrv_d, nrv_k = sum(den[c] for c in (u"N", u"R", u"V")), sum(pick[c] for c in (u"N", u"R", u"V"))
    rows = [p[u"登録の側の値の読める行の数"] for p in rec[u"対"]]
    skips = rec[u"取り方の数"][u"飛ばした試験の理由別"]
    return dict(den=den, pick=pick, outside=outside, zero=zero, d=d, k=k, nrv_d=nrv_d, nrv_k=nrv_k, rows=rows, pairs=len(rec[u"対"]),
                seen=rec[u"取り方の数"][u"見た試験"], stop=rec[u"取り方の数"][u"止めた理由"], skips=skips, skipped=sum(skips.values()), calls=rec[u"取り方の数"][u"呼び出しの数"])


def judge(rec):
    u"""封 §4 の境と記録から CT0-1〜CT0-7 の当たり外れを決め直す(整数の計算。境は封の字: ``bound_problems`` が封の文書と照らす)。"""
    f = figures(rec)
    den, pick = f["den"], f["pick"]
    out = collections.OrderedDict()
    out[u"CT0-1"] = f["pairs"] >= PAIRS_WANT and f["seen"] <= STUDIES_STOP
    out[u"CT0-2"] = f["k"] * 100 <= 30 * f["d"]
    out[u"CT0-3"] = den["P"] > 0 and pick["P"] * 100 >= 80 * den["P"]
    out[u"CT0-4"] = f["nrv_d"] > 0 and f["nrv_k"] * 100 <= 5 * f["nrv_d"]
    out[u"CT0-5"] = den["C"] > 0 and pick["C"] * 100 <= 20 * den["C"]
    out[u"CT0-6"] = f["outside"] <= 5
    out[u"CT0-7"] = f["zero"] == 0 and all(r >= 1 for r in f["rows"])
    return out


def to_boundary_ct02(f):
    u"""CT0-2 が外れになるまでに、あと何字拾えばよいか(30% を超える最小の字数 − いまの数)。"""
    return (30 * f["d"]) // 100 + 1 - f["k"]


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
    if (rec[u"seal"], rec[u"封の commit"], rec[u"封の追記の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT, SEAL_ADDENDUM_SHORT):
        out.append(u"記録の封の欄が違う")
    if rec[u"profile"] != u"P27":
        out.append(u"記録の profile が P27 でない")
    return out


# ======================================================================================================
# b. 記録の数え直し
def recount_problems(c):
    rec = c.rec
    out = []
    f = figures(rec)
    for p in rec[u"対"]:
        n = p[u"番号"]
        if sum(p[u"類別"][k][u"分母"] for k in CLASSES) != p[u"数の字の数"]:
            out.append(u"対 %d の数の字の数が類別の分母の和と違う" % n)
        if sum(p[u"類別"][k][u"拾った"] for k in CLASSES) != p[u"拾った数"]:
            out.append(u"対 %d の拾った数が類別の拾ったの和と違う" % n)
        if any(p[u"類別"][k][u"拾った"] > p[u"類別"][k][u"分母"] for k in CLASSES):
            out.append(u"対 %d の拾ったが分母より多い類が在る" % n)
    if [p[u"番号"] for p in rec[u"対"]] != list(range(1, f["pairs"] + 1)):
        out.append(u"対の番号が 1 から順でない")
    agg = rec[u"集計"]
    if (agg[u"対の数"], agg[u"数の字の数"], agg[u"拾った数"], agg[u"分母の外で拾った数"]) != (f["pairs"], f["d"], f["k"], f["outside"]):
        out.append(u"集計の合計が対ごとの数の和と違う")
    for k in CLASSES:
        if (agg[u"類別"][k][u"分母"], agg[u"類別"][k][u"拾った"]) != (f["den"][k], f["pick"][k]):
            out.append(u"集計の類 %s が対ごとの数の和と違う" % k)
    pred = rec[KEY_PRED]
    want = {
        K1: collections.OrderedDict([(u"見た試験", f["seen"]), (u"対", f["pairs"]), (u"止めた理由", f["stop"])]),
        K2: collections.OrderedDict([(u"拾った", f["k"]), (u"分母", f["d"]), (u"%", float(pct1(f["k"], f["d"])))]),
        K3: collections.OrderedDict([(u"拾った", f["pick"]["P"]), (u"分母", f["den"]["P"]), (u"%", float(pct1(f["pick"]["P"], f["den"]["P"])))]),
        K4: collections.OrderedDict([(u"拾った", f["nrv_k"]), (u"分母", f["nrv_d"]), (u"%", float(pct1(f["nrv_k"], f["nrv_d"])))]),
        K5: collections.OrderedDict([(u"拾った", f["pick"]["C"]), (u"分母", f["den"]["C"]), (u"%", float(pct1(f["pick"]["C"], f["den"]["C"])))]),
        K6: f["outside"], K7: f["zero"]}
    if list(pred.keys()) != list(want.keys()):
        out.append(u"予測の判定に要る数の欄の名・順が違う")
    for k, v in want.items():
        if pred.get(k) != v:
            out.append(u"予測の判定に要る数が数え直しと違う: %s" % k[:8])
    # 取り方の整合: 見た試験 = 対 + 飛ばした試験(10 対で止まるとき)・呼び出し = 版 1 + ページ + efetch(RESULT の文献が在った試験 = 対 + 要旨に登録番号が無い試験)
    if f["stop"] == u"10 対そろった" and f["seen"] != f["pairs"] + f["skipped"]:
        out.append(u"見た試験が対と飛ばした試験の和と違う")
    efetch = f["pairs"] + f["skips"].get(u"要旨に登録番号が無い", 0)
    if f["calls"] != 1 + -(-f["seen"] // 10) + efetch:
        out.append(u"呼び出しの数が(版 1 + ページ + efetch)と違う")
    if f["seen"] > STUDIES_STOP:
        out.append(u"見た試験が止めの数を超えている")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    scan = re.sub(r"[0-9a-fA-F]{32,}", u"", text)
    out = []
    if NCT_FORM.search(scan) or PMID_FORM.search(scan):
        out.append(u"記録に登録番号か PMID の形が在る")
    bad = [k for k in SG.MS.walk_keys(c.rec) if str(k).lower() in SG.MS.FORBIDDEN_KEYS]
    if bad:
        out.append(u"記録に禁止の欄が在る")
    return out


# ======================================================================================================
# c. 予測の当たり外れ
def bound_problems(c):
    return [u"封に境の字が無い: %s" % p for p in BOUND_SEAL_PHRASES if p not in c.seal]


def verdict_problems(c):
    u"""文書 §1 の表と件数が、記録から決め直した判定と同じ。"""
    f = figures(c.rec)
    j = judge(c.rec)
    out = []
    expect_cell = {
        u"CT0-1": u"見た試験 %d で %d 対(止めた理由: %s)" % (f["seen"], f["pairs"], f["stop"]),
        u"CT0-2": u"%d/%d(%s%%)" % (f["k"], f["d"], pct1(f["k"], f["d"])),
        u"CT0-3": u"%d/%d(%s%%)" % (f["pick"]["P"], f["den"]["P"], pct1(f["pick"]["P"], f["den"]["P"])),
        u"CT0-4": u"%d/%d(%s%%)" % (f["nrv_k"], f["nrv_d"], pct1(f["nrv_k"], f["nrv_d"])),
        u"CT0-5": u"%d/%d(%s%%)" % (f["pick"]["C"], f["den"]["C"], pct1(f["pick"]["C"], f["den"]["C"])),
        u"CT0-6": u"%d" % f["outside"],
        u"CT0-7": u"0 行の対は %d" % f["zero"]}
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (CT0-\d) \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が CT0-1〜CT0-7 でない"]
    for k, cells in rows.items():
        if len(cells) != 3:
            out.append(u"%s の行の欄の数が違う" % k)
            continue
        if cells[1] != expect_cell[k]:
            out.append(u"%s の実測の字が記録から組んだ字と違う: %s" % (k, cells[1]))
        verdict = u"当たり" if j[k] else u"外れ"
        want = verdict + (u"(あと %d 字拾えば外れ)" % to_boundary_ct02(f) if k == u"CT0-2" and j[k] else u"")
        if cells[2] != want:
            out.append(u"%s の判定が決め直した判定と違う: %s(決め直し: %s)" % (k, cells[2], want))
    hits = sum(1 for v in j.values() if v)
    line = u"- 当たり %d・外れ %d。" % (hits, len(j) - hits)
    if line not in c.doc.splitlines():
        out.append(u"文書の件数の行が決め直した件数と違う")
    if u"(当たり %d・外れ %d)" % (hits, len(j) - hits) not in c.doc:
        out.append(u"文書の先頭の件数が決め直した件数と違う")
    if u"判定した %d 本は全部が当たり" % len(j) not in c.doc and hits == len(j):
        out.append(u"文書が「全部が当たり」と言っていない(決め直しは全部当たり)")
    if hits != len(j) and u"全部が当たり" in c.doc:
        out.append(u"外れが在るのに文書が「全部が当たり」と言う")
    return out


# ======================================================================================================
# d. 文書の数
def expected_lines(c):
    u"""文書に 1 行まるごと在るべき字(表の行・箇条の行)を記録から組む。"""
    f = figures(c.rec)
    out = []
    for k in CLASSES:
        out.append(u"| %s | %d | %d |" % (CLASS_LABEL[k], f["den"][k], f["pick"][k]))
    out.append(u"| 合計 | %d | %d |" % (f["d"], f["k"]))
    for p in c.rec[u"対"]:
        out.append(u"| %d | %d | %d | %d |" % (p[u"番号"], p[u"数の字の数"], p[u"拾った数"], p[u"登録の側の値の読める行の数"]))
    sk = f["skips"]
    out.append(u"- 見た試験 %d・対 %d・止めた理由「%s」。飛ばした試験 %d の理由は、RESULT の文献(番号つき)が無い %d・要旨に登録番号が無い %d。呼び出しは %d 回(script は呼び出しの開始から次の開始まで 1 秒以上あける作り。記録に呼び出しの時刻は無く、実走の間隔は測っていない)。" % (
        f["seen"], f["pairs"], f["stop"], f["skipped"], sk[u"RESULT の文献(番号つき)が無い"], sk[u"要旨に登録番号が無い"], f["calls"]))
    out.append(u"- どの対でも、拾った数はその対の類 P の数と同じ。分母の外で拾った字は %d。" % f["outside"])
    out.append(u"- 登録の側は %d 対の全部で値の読める行が在る(%d から %d)。表に組めるか・結べるかは測っていない。" % (f["pairs"], min(f["rows"]), max(f["rows"])))
    return out


def expected_fragments(c):
    u"""文書の散文に在るべき字(数を含む言い切り)を記録から組む。"""
    f = figures(c.rec)
    den, pick = f["den"], f["pick"]
    return [
        u"engine が拾ったのは要旨の数の字 %d のうち %d(%s%%)" % (f["d"], f["k"], pct1(f["k"], f["d"])),
        u"拾った %d は全部が直後に `%%` の付いた字(類 P の %d のうち %d)" % (f["k"], den["P"], pick["P"]),
        u"ほかの類の %d は 1 つも拾っていない" % (f["d"] - den["P"]),
        u"類 O(%d)が大きい" % den["O"],
        u"判定した %d 本は全部が当たり" % len(judge(c.rec)),
        u"字 %d のうち、いまの engine が読めたのは `%%` の付いた %d だけ" % (f["d"], f["k"]),
        u"類 R は %d だけ" % den["R"],
        u"取った日 %s" % c.rec[u"取った日付"],
        u"API v2 の版 %s・データの時刻 %s" % (c.rec[u"出どころの版"][u"登録側の API の版"], c.rec[u"出どころの版"][u"登録側のデータの時刻"]),
    ]


def structural_numbers():
    u"""記録の外の、文書が言う数(封・script の字で決まっているもの)。"""
    return set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"12", u"16", u"20", u"30", u"31", u"79", u"80", u"400", u"21", u"6"])


NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}(?:T[\d:]+)?", u" ", s)
    s = re.sub(r"CT0-\d", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    s = re.sub(r"U\+\d+", u" ", s)
    s = re.sub(r"\bAPI v2\b|\bP27\b|\bPhase \d(?:/\d)?|\b2\.0\.5\b", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def doc_number_problems(c):
    u"""数字を含む行は全部、記録から組んだ数の並びの内(許す数の外の数字は赤)・表の行・言い切りは記録から組んだ字と同じ。塊(表)の外の行も同じに見る。"""
    f = figures(c.rec)
    allowed = set(structural_numbers())
    for k in CLASSES:
        allowed |= set([str(f["den"][k]), str(f["pick"][k])])
    for p in c.rec[u"対"]:
        allowed |= set([str(p[u"番号"]), str(p[u"数の字の数"]), str(p[u"拾った数"]), str(p[u"登録の側の値の読める行の数"])])
    allowed |= set(str(x) for x in (f["d"], f["k"], f["d"] - f["den"]["P"], f["nrv_d"], f["nrv_k"], f["seen"], f["pairs"], f["skipped"], f["calls"], f["outside"], f["zero"], to_boundary_ct02(f)))
    allowed |= set(str(v) for v in f["skips"].values())
    allowed |= set(pct1(n, d) for n, d in [(f["k"], f["d"]), (f["pick"]["P"], f["den"]["P"]), (f["nrv_k"], f["nrv_d"]), (f["pick"]["C"], f["den"]["C"])])
    allowed |= set([u"2442", u"18"])
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
    # 言い切りの根拠を記録から直接確かめる
    if any(p[u"拾った数"] != p[u"類別"][u"P"][u"拾った"] for p in c.rec[u"対"]) or f["outside"] != 0:
        out.append(u"「どの対でも拾った数は類 P の数と同じ・分母の外は 0」が記録と違う")
    if any(f["pick"][k] != 0 for k in CLASSES if k != u"P"):
        out.append(u"「P のほかの類は 1 つも拾っていない」が記録と違う")
    if f["pick"]["P"] != f["den"]["P"] and u"類 P の %d のうち %d" % (f["den"]["P"], f["den"]["P"]) in c.doc:
        out.append(u"類 P の言い切りが記録と違う")
    if min(f["rows"]) < 1:
        out.append(u"登録の側の「全部で値の読める行が在る」が記録と違う")
    return out


# ======================================================================================================
# e. 要点の字・禁止
def phrase_problems(c):
    return [u"文書に要点の字が無い: %s" % p for p in PHRASES if p not in c.doc]


def forbidden_problems(c):
    out = [u"文書に禁止語: %s" % w for w in FORBIDDEN_WORDS if w in c.doc]
    scan = re.sub(r"\d{4}-\d{2}-\d{2}(?:T[\d:]+)?", u" ", c.doc)
    scan = re.sub(r"\b[0-9a-f]{8}\b", u" ", scan)
    if NCT_FORM.search(scan):
        out.append(u"文書に登録番号の形が在る")
    if PMID_FORM.search(scan):
        out.append(u"文書に PMID の形が在る")
    if DOCID_FORM.search(c.doc):
        out.append(u"文書に docID の形が在る")
    return out


def doc_commit_problems(c):
    u"""文書が書く commit の字が封・追記・script・記録の commit と同じ。"""
    out = []
    for want in (SEAL_COMMIT_SHORT, SEAL_ADDENDUM_SHORT, SCRIPT_FIRST_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT):
        if want not in c.doc:
            out.append(u"文書に commit の字が無い: %s" % want)
    found = set(re.findall(r"commit ([0-9a-f]{8})", c.doc)) | set(re.findall(r"追記 §8 ([0-9a-f]{8})", c.doc)) | set(re.findall(r"・([0-9a-f]{8})(?:[(（]|\b)", c.doc))
    if not found <= set([SEAL_COMMIT_SHORT, SEAL_ADDENDUM_SHORT, SCRIPT_FIRST_COMMIT_SHORT, SCRIPT_COMMIT_SHORT, RECORD_COMMIT_SHORT]):
        out.append(u"文書が知らない commit の字を書いている")
    return out


CHECKS = collections.OrderedDict([
    (u"sha", sha_problems), (u"recount", recount_problems), (u"clean", record_clean_problems), (u"bound", bound_problems), (u"verdict", verdict_problems),
    (u"numbers", doc_number_problems), (u"phrases", phrase_problems), (u"forbidden", forbidden_problems), (u"commits", doc_commit_problems)])


# ======================================================================================================
# f. git(封・順序・engine・commit)
def git_problems(root=REPO):
    out = []
    out.extend(SG.seal_history_problems(root))
    out.extend(SG.engine_zero_problems(root))
    return out


def order_problems_real(root=REPO):
    u"""封 ⊏ 追記 ⊏ script ⊏ 記録 ⊏ 結果の文書と門。未 commit は赤。記録を足した commit が afea7515・script の最後の commit が 859cb911。"""
    out = list(PR.order_problems(root, PREFIX, SEAL_REL, SEAL_COMMIT_SHORT, [SCRIPT_REL], [RECORD_REL, DOC_REL, GATE_REL]))
    rc, first = PR.git_in(root, "log", "--diff-filter=A", "--format=%H", "--", PREFIX + SCRIPT_REL)
    first = [x for x in first.split() if x]
    if len(first) != 1 or not first[0].startswith(SCRIPT_FIRST_COMMIT_SHORT):
        out.append(u"script を足した commit が %s でない" % SCRIPT_FIRST_COMMIT_SHORT)
    elif not PR.is_anc(root, SEAL_ADDENDUM_SHORT, first[0]) or first[0].startswith(SEAL_ADDENDUM_SHORT):
        out.append(u"封の追記の commit が script より前でない")
    rc, last = PR.git_in(root, "log", "-1", "--format=%H", "--", PREFIX + SCRIPT_REL)
    if not last.startswith(SCRIPT_COMMIT_SHORT):
        out.append(u"script の最後の commit が %s でない(記録を書いた後に script が変わった)" % SCRIPT_COMMIT_SHORT)
    rec = [x for x in PR.added_commits(root, PREFIX + RECORD_REL)]
    if len(rec) != 1 or not rec[0].startswith(RECORD_COMMIT_SHORT):
        out.append(u"記録を足した commit が %s でない" % RECORD_COMMIT_SHORT)
    elif not PR.is_anc(root, last, rec[0]):
        out.append(u"記録が script の最後の commit より前")
    return out


# ======================================================================================================
# 変異。予測は実行の前に書いた(下の PREDICT)。1 つの変異が赤にすべき検査の名前の並びを持つ
PREDICT = u"""
M1  対 1 の類 P の拾ったを 1 減らす(合計は直さない)        -> recount・numbers が赤
M2  集計の拾った数を 80 → 81                                -> recount が赤
M3  予測の欄 CT0-2 の拾ったを 1 増やす                       -> recount が赤
M4  文書の表の分母 331 を 332 にする                          -> numbers が赤
M5  文書の CT0-2 の判定を「外れ」にする                       -> verdict が赤
M6  文書から「測っていない見立て」を消す                      -> phrases が赤
M7  文書に登録番号の形を足す                                  -> forbidden が赤
M8  記録の類 C の拾ったを整合したまま 19 に(記録の全部の欄を直す) -> 当たり外れが変わる: verdict が赤(recount は緑のまま)
M9  文書の対の表の 1 行の数を入れ替える                        -> numbers が赤
M10 記録の sha256 の写しを違う値にする                          -> sha が赤
M11 文書の commit の字 859cb911 を 859cb912 にする             -> commits が赤
M12 文書の「どの対でも…類 P の数と同じ」を別の言い切りにする    -> numbers が赤
M13 文書の「当たり 7・外れ 0」を「当たり 6・外れ 1」にする      -> verdict が赤
M14 文書から「人間に返す」を消す                                -> phrases が赤
M15 記録の呼び出しの数 51 → 52                                  -> recount・numbers が赤
M16 文書に PMID の語を足す                                       -> forbidden が赤
M17 記録に NCT の字を足す                                        -> clean が赤
M18 文書の本文に 332 という数字の言い切りを足す                   -> numbers が赤
M19 封の写しから境の字「30% 以下」を消す                          -> bound が赤
M20 文書から「実走の間隔は測っていない」を消す                    -> phrases が赤
M21 文書の間隔の句を「1 秒以上あけた」(測ったかの言い方)に戻す    -> numbers が赤(表の行が記録から組んだ字と違う)
M22 文書の「表に組めるか・結べるかは測っていない」を「組める形で在る」に戻す -> numbers が赤
"""


def bump_class(rec, pair_idx, cls, delta):
    u"""整合したまま、ある対のある類の拾ったを delta 増やす(対の拾った数・集計・予測の欄も直す)。"""
    p = rec[u"対"][pair_idx]
    p[u"類別"][cls][u"拾った"] += delta
    p[u"拾った数"] += delta
    rec[u"集計"][u"拾った数"] += delta
    rec[u"集計"][u"類別"][cls][u"拾った"] += delta
    f = figures(rec)
    pred = rec[KEY_PRED]
    pred[K2][u"拾った"] = f["k"]
    pred[K2][u"%"] = float(pct1(f["k"], f["d"]))
    if cls == u"C":
        pred[K5][u"拾った"] = f["pick"]["C"]
        pred[K5][u"%"] = float(pct1(f["pick"]["C"], f["den"]["C"]))


def m_1(c):
    c.rec[u"対"][0][u"類別"][u"P"][u"拾った"] -= 1


def m_2(c):
    c.rec[u"集計"][u"拾った数"] += 1


def m_3(c):
    c.rec[KEY_PRED][K2][u"拾った"] += 1


def m_4(c):
    s = c.doc.replace(u"| 合計 | 331 | 80 |", u"| 合計 | 332 | 80 |")
    assert s != c.doc
    c.doc = s


def m_5(c):
    s = c.doc.replace(u"| 当たり(あと 20 字拾えば外れ) |", u"| 外れ |")
    assert s != c.doc
    c.doc = s


def _drop(c, phrase):
    assert phrase in c.doc
    c.doc = c.doc.replace(phrase, u"X", 1)


def m_8(c):
    for i in (1, 3, 6):                                          # 類 C の分母のある 3 対で、拾ったを分母と同じにする(18 / 19 は境の 20% を超える)
        n = c.rec[u"対"][i][u"類別"][u"C"][u"分母"]
        bump_class(c.rec, i, u"C", n)


def m_9(c):
    s = c.doc.replace(u"| 7 | 33 | 6 | 2442 |", u"| 7 | 33 | 6 | 2441 |")
    assert s != c.doc
    c.doc = s


def m_10(c):
    c.shas[RECORD_REL] = u"0" * 64


def m_11(c):
    s = c.doc.replace(u"859cb911", u"859cb912")
    assert s != c.doc
    c.doc = s


def m_12(c):
    s = c.doc.replace(u"どの対でも、拾った数はその対の類 P の数と同じ。", u"どの対でも、拾った数は 0。")
    assert s != c.doc
    c.doc = s


def m_13(c):
    s = c.doc.replace(u"- 当たり 7・外れ 0。", u"- 当たり 6・外れ 1。")
    assert s != c.doc
    c.doc = s


def m_15(c):
    c.rec[u"取り方の数"][u"呼び出しの数"] += 1


def m_16(c):
    c.doc = c.doc + u"\nPMID の欄。\n"


def m_17(c):
    c.rec[u"対"][0][u"材料の sha256"][u"x"] = u"NCT00000001"


def m_18(c):
    c.doc = c.doc + u"\n拾った割合は 332 に近い。\n"


def m_19(c):
    c.seal = c.seal.replace(u"30% 以下", u"X")


def m_7(c):
    c.doc = c.doc + u"\n登録番号 NCT00000123 の試験。\n"


def m_21(c):
    s = c.doc.replace(u"script は呼び出しの開始から次の開始まで 1 秒以上あける作り。記録に呼び出しの時刻は無く、実走の間隔は測っていない", u"1 回ごとに 1 秒以上あけた。呼び出しの開始から次の開始まで")
    assert s != c.doc
    c.doc = s


def m_22(c):
    s = c.doc.replace(u"表に組めるか・結べるかは測っていない。", u"出所の表の側は組める形で在る。")
    assert s != c.doc
    c.doc = s


MUTATIONS = (
    (u"M1 対 1 の類 P の拾ったを 1 減らす", m_1, (u"recount", u"numbers")),
    (u"M2 集計の拾った数を 1 増やす", m_2, (u"recount",)),
    (u"M3 予測の欄 CT0-2 の拾ったを 1 増やす", m_3, (u"recount",)),
    (u"M4 文書の表の分母 331 を 332 に", m_4, (u"numbers",)),
    (u"M5 文書の CT0-2 の判定を外れに", m_5, (u"verdict",)),
    (u"M6 「測っていない見立て」を消す", lambda c: _drop(c, u"測っていない見立て"), (u"phrases",)),
    (u"M7 文書に登録番号の形を足す", m_7, (u"forbidden",)),
    (u"M8 記録の類 C の拾ったを整合したまま増やす(判定が変わる)", m_8, (u"verdict",)),
    (u"M9 文書の対の表の 1 行の数を替える", m_9, (u"numbers",)),
    (u"M10 記録の sha256 の写しを違う値に", m_10, (u"sha",)),
    (u"M11 文書の commit の字を 1 字替える", m_11, (u"commits",)),
    (u"M12 文書の「類 P の数と同じ」の言い切りを替える", m_12, (u"numbers",)),
    (u"M13 文書の件数を当たり 6・外れ 1 に", m_13, (u"verdict",)),
    (u"M14 「人間に返す」を消す", lambda c: _drop(c, u"人間に返す"), (u"phrases",)),
    (u"M15 記録の呼び出しの数を 1 増やす", m_15, (u"recount", u"numbers")),
    (u"M16 文書に PMID の語を足す", m_16, (u"forbidden",)),
    (u"M17 記録に NCT の字を足す", m_17, (u"clean",)),
    (u"M18 文書に 332 の言い切りを足す", m_18, (u"numbers",)),
    (u"M19 封の写しから境の字を消す", m_19, (u"bound",)),
    (u"M20 「実走の間隔は測っていない」を消す", lambda c: _drop(c, u"実走の間隔は測っていない"), (u"phrases",)),
    (u"M21 間隔の句を測ったかの言い方に戻す", m_21, (u"numbers",)),
    (u"M22 「表に組めるか・結べるかは測っていない」を戻す", m_22, (u"numbers", u"phrases")),
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

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        self.assertEqual(7, sum(1 for v in judge(self.c.rec).values() if v))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_e_1_the_important_phrases_without_digits_are_present(self):
        self.assertEqual([], phrase_problems(self.c))

    def test_e_2_the_document_has_no_forbidden_words_or_forms(self):
        self.assertEqual([], forbidden_problems(self.c))

    def test_e_3_the_commits_the_document_names(self):
        self.assertEqual([], doc_commit_problems(self.c))

    def test_f_1_the_seal_history_and_the_engine(self):
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

    def test_g_4_ct02_boundary_is_the_first_count_over_thirty_percent(self):
        f = figures(Ctx().rec)
        k = to_boundary_ct02(f)
        self.assertGreater((f["k"] + k) * 100, 30 * f["d"])
        self.assertLessEqual((f["k"] + k - 1) * 100, 30 * f["d"])


if __name__ == "__main__":
    unittest.main()
