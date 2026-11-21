# -*- coding: utf-8 -*-
"""結果の門: 封 docs/XBRL_EDINET_VALIDATE_SEAL_2026-11-21.md(1bda1997)の結果の文書 docs/XBRL_EDINET_VALIDATE_RESULT_2026-11-21.md。

封の門 ``test_xbrl_edinet_validate_seal.py`` の次の段。**追跡されている記録・script・封・結果の文書と git の履歴だけを読む**(道具(Arelle)も置き場も読まない・通信しない・鍵は読まない)。
検査は「問題の一覧を返す関数」。実物で空・変異で空でない。変異は ``MUTATIONS`` の表で 1 つずつ(木の file は変異させず、``Ctx`` の写しに当てる)。

 a script・記録・封の門・封の sha256(字で留める)と、記録の script の sha256・封の commit の欄
 b 記録の数え直し: 書類ごとの数から、**script の関数を使わずに**、3 通りの集計・予測の判定に要る数を数え直して記録と同じことを見る
 c 予測 XV0-1〜XV0-7 の当たり外れを、封 §4 の字から取った境(封の文書にその字が在ることも見る)と記録から決め直し、文書 §1 の表・件数と同じことを見る。封 §6 と文書 §5 が合う・封 §4 の「5 本以上なら疑う」が発火しない
 d 結果の文書の数: 数字を含む行は全部、記録から組んだ数の並びの内。表の行・言い切りは記録から組んだ字とそのまま照らす。§3 は 3 本・1 本・67 本の数だけ
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


SG = load_module("tests/measure/test_xbrl_edinet_validate_seal.py", "xbrl_edinet_validate_seal_gate_for_result_gate")        # 封の門の部品。門としては走らせない
PR = SG.PR

SEAL_REL = SG.SEAL_REL
SEAL_COMMIT_SHORT = SG.SEAL_COMMIT_SHORT
SCRIPT_REL = SG.SCRIPT_REL
SEAL_GATE_REL = SG.GATE_REL
RECORD_REL = SG.RECORD_REL
GATE_REL = "tests/measure/test_xbrl_edinet_validate_result.py"
DOC_REL = "docs/XBRL_EDINET_VALIDATE_RESULT_2026-11-21.md"
SCRIPT_COMMIT_SHORT = "762d361e"                  # script と封の門を足した commit
RECORD_COMMIT_SHORT = "bf45023c"                  # 記録を足した commit
BLOB_AT = collections.OrderedDict([
    (SEAL_REL, SEAL_COMMIT_SHORT), (SCRIPT_REL, SCRIPT_COMMIT_SHORT), (SEAL_GATE_REL, SCRIPT_COMMIT_SHORT), (RECORD_REL, RECORD_COMMIT_SHORT)])

SHA_PIN = collections.OrderedDict([
    (RECORD_REL, "9689043becb41cbb24ade05883136e6e36a74517a25260ddb393b2a8f6c2d659"),
    (SCRIPT_REL, "b4b7cbc6c6c6f04b2fc09489a6428ed864bcfe346dc445becab91f2a87a61219"),
    (SEAL_GATE_REL, "c42efabdafde406e1cd1b6c2eaa8c178818b2b8512bc19afdb6f33f9bd6d8ea9"),
    (SEAL_REL, "3fde5b99d1beee550f3a8219952522d741881f48d48b7c2f304d3ef3bb36a008")])

RUN_KEYS = (u"道具 R × EDINET-2026", u"道具 P × EDINET-2026", u"道具 P × EDINET-2025")
CLASSES = (u"走った", u"止まった", u"走らなかった")
PRED_KEY = u"予測の判定に要る数(XV0-1〜XV0-7。当たり・外れは結果の文書で)"
PK = (u"XV0-1 道具 R・2026: 止まった書類", u"XV0-2 道具 P・2026: 止まった + 走らなかった書類", u"XV0-3 道具 P・2026: 包みの形のほかの E が 1 行以上在る書類",
      u"XV0-4 道具 P・2026: EC5611W が鳴る書類", u"XV0-5 道具 P・2026: 鳴った EDINET. の符号の種類",
      u"XV0-6 道具 P: 包みの形のほかの E が在る書類(2025・2026・2025 から 2026 を引いた差)", u"XV0-7 道具 P・2026: EC0121E か EC0130E が鳴る書類",
      u"補 道具 P・2026: 指摘の行が 1 行も無い書類(5 本以上なら先に自分の欠陥を疑う)")
E_CODE = re.compile(r"^EDINET\.EC\d{4}E$")
EDI = u"EDINET."
BOUND_SEAL_PHRASES = (u"60 本以上", u"3 本以下", u"33 本以下", u"40 本以上", u"8 以上 30 以下", u"10 本以上多い", u"65 本以上", u"34 本以上で鳴った符号の種類の数",
                      u"道具 P・2026 で指摘の行が 1 行も無い書類が 5 本以上在ったら、先に自分の欠陥を疑う", u"XV0-2 が当たりなら、次の便の候補を人間に示す")
HEAD_PHRASES = (u"先に負けと限界を書く", u"当たり 7・外れ 0", u"67 本のうち 1 本を手で掛けてから立てた", u"67 本の全部で最後まで走らずに止まった", u"E の符号が 1 行も無い書類は 0 本",
                u"「作った XBRL の合否」にそのまま使えない", u"提出の包みそのものではない", u"規則の年は 2 つとも全部の書類に掛けた", u"版の字が 0.0.1", u"本家の版ではない",
                u"無作為ではない", u"この便からは言えない", u"LLM の席は呼んでいない", u"鳴ったことは、規則の誤りとも書類の誤りとも読まない")
PHRASES = (u"測っていない", u"言えること", u"言えないこと", u"人間に示す次の便の候補", u"別の封が先", u"盲検ではない", u"記録に欄の無い読み", u"人間が決めること",
           u"67 本の全部が同じ理由で止まったとは確かめていない", u"鳴らなければ通る」という使い方はまだできない", u"道具 R が止まった後の段については比べる相手が無い")
SEAL7_PHRASES = (u"提出の包みそのものではない", u"規則の年は 2 つとも", u"版の字が 0.0.1", u"道具 P は司令塔が 1 行を直した", u"無作為ではない", u"「EDINET の検査に通る」")
FORBIDDEN_WORDS = (u"精度", u"世界で 1 社", u"LLM より正確", u"保証", u"完璧")
DOCID_FORM = re.compile(r"(?<![0-9A-Za-z])S[0-9A-Z]{7}(?![0-9A-Za-z])")
ECODE_FORM = re.compile(r"(?<![0-9A-Za-z])E\d{5}(?![0-9A-Za-z])")


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


def short(code):
    return code[len(EDI):] if code.startswith(EDI) else code


def run_totals(docs, key):
    u"""書類ごとの数から 1 通りの合計を作る(script の関数は使わない)。記録の集計の欄と同じ形。"""
    cls = collections.OrderedDict((c, 0) for c in CLASSES)
    dby, lby = collections.Counter(), collections.Counter()
    oth = noe = nol = to = pair = 0
    for d in docs:
        e = d[key]
        cls[e[u"類"]] += 1
        to += 1 if e[u"時間の上限を超えた"] else 0
        codes = e[u"符号ごとの行"]
        for c, n in codes.items():
            dby[c] += 1
            lby[c] += n
        if any(E_CODE.match(c) and c[len(EDI) + 2] != u"0" for c in codes):
            oth += 1
        if not any(E_CODE.match(c) for c in codes):
            noe += 1
        if not codes:
            nol += 1
        if u"EDINET.EC0121E" in codes or u"EDINET.EC0130E" in codes:
            pair += 1
    kinds = sum(1 for c in dby if c.startswith(EDI))
    return collections.OrderedDict([
        (u"類別", cls), (u"時間の上限を超えた数", to),
        (u"符号ごと", collections.OrderedDict((c, collections.OrderedDict([(u"書類", dby[c]), (u"行", lby[c])])) for c in sorted(dby))),
        (u"包みの形のほかの E が 1 行以上在る書類", oth), (u"E の符号が 1 行も無い書類", noe), (u"指摘の行が 1 行も無い書類", nol),
        (u"鳴った符号の種類", collections.OrderedDict([(u"EDINET. の符号", kinds), (u"ほかの符号", len(dby) - kinds)])),
        (u"34 本以上で鳴った符号の種類", sum(1 for c in dby if dby[c] >= 34)), (u"EC0121E か EC0130E が鳴る書類", pair)])


def all_totals(rec):
    return collections.OrderedDict((k, run_totals(rec[u"書類"], k)) for k in RUN_KEYS)


def pred_expected(tot):
    r26, p26, p25 = (tot[k] for k in RUN_KEYS)
    n = 67

    def dn(x):
        return collections.OrderedDict([(u"書類", x), (u"分母", n)])
    return collections.OrderedDict([
        (PK[0], dn(r26[u"類別"][u"止まった"])), (PK[1], dn(p26[u"類別"][u"止まった"] + p26[u"類別"][u"走らなかった"])),
        (PK[2], dn(p26[u"包みの形のほかの E が 1 行以上在る書類"])), (PK[3], dn(p26[u"符号ごと"].get(u"EDINET.EC5611W", {}).get(u"書類", 0))),
        (PK[4], p26[u"鳴った符号の種類"][u"EDINET. の符号"]),
        (PK[5], collections.OrderedDict([(u"2025", p25[u"包みの形のほかの E が 1 行以上在る書類"]), (u"2026", p26[u"包みの形のほかの E が 1 行以上在る書類"]),
                                         (u"差", p25[u"包みの形のほかの E が 1 行以上在る書類"] - p26[u"包みの形のほかの E が 1 行以上在る書類"])])),
        (PK[6], dn(p26[u"EC0121E か EC0130E が鳴る書類"])), (PK[7], p26[u"指摘の行が 1 行も無い書類"])])


def judge(tot):
    u"""封 §4 の境と記録から XV0-1〜XV0-7 の当たり外れを決め直す。"""
    r26, p26, p25 = (tot[k] for k in RUN_KEYS)
    out = collections.OrderedDict()
    out[u"XV0-1"] = r26[u"類別"][u"止まった"] >= 60
    out[u"XV0-2"] = p26[u"類別"][u"止まった"] + p26[u"類別"][u"走らなかった"] <= 3
    out[u"XV0-3"] = p26[u"包みの形のほかの E が 1 行以上在る書類"] <= 33
    out[u"XV0-4"] = p26[u"符号ごと"].get(u"EDINET.EC5611W", {}).get(u"書類", 0) >= 40
    out[u"XV0-5"] = 8 <= p26[u"鳴った符号の種類"][u"EDINET. の符号"] <= 30
    out[u"XV0-6"] = p25[u"包みの形のほかの E が 1 行以上在る書類"] - p26[u"包みの形のほかの E が 1 行以上在る書類"] >= 10
    out[u"XV0-7"] = p26[u"EC0121E か EC0130E が鳴る書類"] >= 65
    return out


def codes_of(rec, key):
    return set(rec[u"集計"][key][u"符号ごと"])


# ======================================================================================================
def sha_problems(c):
    out = []
    for rel, want in SHA_PIN.items():
        if c.shas[rel] != want:
            out.append(u"sha256 が字で留めた値と違う: %s" % rel)
    if c.rec[u"この script の sha256"] != SHA_PIN[SCRIPT_REL]:
        out.append(u"記録の script の sha256 が script と違う")
    if (c.rec[u"seal"], c.rec[u"封の commit"]) != (SEAL_REL, SEAL_COMMIT_SHORT):
        out.append(u"記録の封の欄が違う")
    return out


def recount_problems(c):
    rec = c.rec
    out = []
    docs = rec[u"書類"]
    if [d[u"番号"] for d in docs] != list(range(1, 68)) or rec[u"材料"][u"書類の本数"] != 67 or rec[u"材料"][u"3 通り"] != list(RUN_KEYS):
        out.append(u"書類の番号・材料の書類の本数・3 通りの名が違う")
    for d in docs:
        for k in RUN_KEYS:
            e = d[k]
            if e[u"類"] not in CLASSES or (e[u"時間の上限を超えた"] and e[u"類"] != u"止まった"):
                out.append(u"書類 %d の %s の類が違う" % (d[u"番号"], k))
            nl = e[u"出力の行の数"]
            if not isinstance(nl, int) or isinstance(nl, bool) or nl < sum(e[u"符号ごとの行"].values()):
                out.append(u"書類 %d の %s の出力の行の数が指摘の行の数より少ない" % (d[u"番号"], k))
    tot = all_totals(rec)
    for k in RUN_KEYS:
        if json.loads(json.dumps(rec[u"集計"][k])) != json.loads(json.dumps(tot[k])):
            out.append(u"集計が書類ごとの数から数え直した値と違う: %s" % k)
    if json.loads(json.dumps(rec[PRED_KEY])) != json.loads(json.dumps(pred_expected(tot))):
        out.append(u"予測の判定に要る数が数え直しと違う")
    return out


def record_clean_problems(c):
    text = json.dumps(c.rec, ensure_ascii=False)
    out = []
    try:
        SG.MS.check_clean(c.rec, text)
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


def expected_verdict_cells(c):
    tot = all_totals(c.rec)
    j = judge(tot)
    r26, p26, p25 = (tot[k] for k in RUN_KEYS)
    o26, o25 = p26[u"包みの形のほかの E が 1 行以上在る書類"], p25[u"包みの形のほかの E が 1 行以上在る書類"]
    actual = {u"XV0-1": u"%d/67" % r26[u"類別"][u"止まった"], u"XV0-2": u"%d/67" % (p26[u"類別"][u"止まった"] + p26[u"類別"][u"走らなかった"]),
              u"XV0-3": u"%d/67" % o26, u"XV0-4": u"%d/67" % p26[u"符号ごと"].get(u"EDINET.EC5611W", {}).get(u"書類", 0), u"XV0-5": u"%d" % p26[u"鳴った符号の種類"][u"EDINET. の符号"],
              u"XV0-6": u"2025 は %d・2026 は %d・差 %d" % (o25, o26, o25 - o26), u"XV0-7": u"%d/67" % p26[u"EC0121E か EC0130E が鳴る書類"]}
    return collections.OrderedDict((k, (actual[k], u"当たり" if j[k] else u"**外れ**")) for k in j)


def verdict_problems(c):
    tot = all_totals(c.rec)
    j = judge(tot)
    want = expected_verdict_cells(c)
    out = []
    rows = {}
    for ln in c.doc.splitlines():
        m = re.match(r"^\| (XV0-\d)(?:\(主\))? \|(.*)\|$", ln)
        if m:
            rows[m.group(1)] = [x.strip() for x in m.group(2).split(u"|")]
    if sorted(rows) != sorted(j):
        return [u"文書 §1 の表の行が XV0-1〜XV0-7 でない"]
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
    sec5 = section(c.doc, u"## §5 ", None)
    if j[u"XV0-2"] != (u"人間に示す次の便の候補(封 §6。XV0-2 が当たりなので示す)" in sec5):
        out.append(u"封 §6 の決め(XV0-2 が当たりなら次の便の候補を示す)と文書 §5 が合わない")
    if not j[u"XV0-2"] and u"落ちる所の数を書いて" not in sec5:
        out.append(u"XV0-2 が外れたときの封 §6 の決めが §5 に無い")
    no_line = tot[RUN_KEYS[1]][u"指摘の行が 1 行も無い書類"]
    fired = no_line >= 5
    line = u"は、%d 本なので発火しない" % no_line
    if fired or line not in c.doc:
        out.append(u"封 §4 の「指摘の行が 1 行も無い書類が 5 本以上」が発火している・文書の言い切りと合わない")
    return out


# ======================================================================================================
def code_rows(tot):
    u"""道具 P × 2026 の符号ごと(書類の多い順・同数は符号の字の順)。"""
    d = tot[RUN_KEYS[1]][u"符号ごと"]
    return sorted(d.items(), key=lambda kv: (-kv[1][u"書類"], kv[0]))


def expected_lines(c):
    tot = all_totals(c.rec)
    out = []
    for k in RUN_KEYS:
        t = tot[k]
        out.append(u"| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            k, t[u"類別"][u"走った"], t[u"類別"][u"止まった"], t[u"類別"][u"走らなかった"], t[u"鳴った符号の種類"][u"EDINET. の符号"], t[u"鳴った符号の種類"][u"ほかの符号"],
            t[u"34 本以上で鳴った符号の種類"], t[u"包みの形のほかの E が 1 行以上在る書類"], sum(v[u"行"] for v in t[u"符号ごと"].values())))
    for code, v in code_rows(tot):
        out.append(u"| %s | %d | %d |" % (short(code), v[u"書類"], v[u"行"]))
    out.append(u"- どの通りでも、E の符号が 1 行も無い書類は %d・指摘の行が 1 行も無い書類は %d。" % (
        max(tot[k][u"E の符号が 1 行も無い書類"] for k in RUN_KEYS), max(tot[k][u"指摘の行が 1 行も無い書類"] for k in RUN_KEYS)))
    return out


def lines_text(d, code, with_lines):
    v = d[code]
    return u"%d 本・%d 行" % (v[u"書類"], v[u"行"]) if with_lines else u"%d 本" % v[u"書類"]


def expected_fragments(c):
    rec = c.rec
    tot = all_totals(rec)
    r26, p26, p25 = (tot[k] for k in RUN_KEYS)
    s26, s25, sr = p26[u"符号ごと"], p25[u"符号ごと"], r26[u"符号ごと"]
    only25 = sorted(set(s25) - set(s26))
    only26 = sorted(set(s26) - set(s25))
    diff = [k for k in sorted(set(s25) & set(s26)) if s25[k] != s26[k]]
    ponly = sorted(set(s26) - set(sr))
    other_e26 = sorted(k for k in s26 if E_CODE.match(k) and k[len(EDI) + 2] != u"0")
    other_e25 = sorted(k for k in only25 if E_CODE.match(k) and k[len(EDI) + 2] != u"0")
    ntot = sum(1 for k in RUN_KEYS for _ in rec[u"書類"])
    total_to = sum(t[u"時間の上限を超えた数"] for t in tot.values())
    f = []
    f.append(u"判定した 7 本は全部が当たり(当たり 7・外れ 0)")
    f.append(u"手を入れない道具(道具 R)は、67 本の全部で最後まで走らずに止まった(%d/67)" % r26[u"類別"][u"止まった"])
    f.append(u"E の符号が 1 行も無い書類は %d 本" % p26[u"E の符号が 1 行も無い書類"])
    f.append(u"EC0121E・EC0130E は %d 本の全部で鳴り、警告の EC5611W も %d 本の全部で鳴った。34 本以上で鳴った符号は %d 種類" % (
        s26[u"EDINET.EC0121E"][u"書類"], s26[u"EDINET.EC5611W"][u"書類"], p26[u"34 本以上で鳴った符号の種類"]))
    f.append(u"3 通りのそれぞれ(67 本ずつ。合わせて %d 回。時間の上限を超えた回は %d)" % (ntot, total_to))
    f.append(u"%s の符号ごと(鳴った書類の数 / 指摘の行の数。%d 種類)" % (RUN_KEYS[1], len(s26)))
    f.append(u"包みの形のほかの E は %s の %d 種類で、それぞれ別の 1 本で鳴った(合わせて %d 本)" % (
        u" と ".join(short(k) for k in other_e26), len(other_e26), p26[u"包みの形のほかの E が 1 行以上在る書類"]))
    f.append(u"2025 でだけ鳴った符号は %d 種類: %s" % (len(only25), u"・".join(u"%s(%d 本・%d 行)" % (short(k), s25[k][u"書類"], s25[k][u"行"]) for k in only25)))
    f.append(u"包みの形のほかの E が 67 本の全部に在るのは、この %s による" % u" と ".join(short(k) for k in other_e25))
    f.append(u"2026 でだけ鳴った符号は %d 種類: %s" % (len(only26), u"・".join(short(k) for k in only26)))
    parts = []
    for k in diff:
        a, b = s25[k], s26[k]
        wl = not (a[u"書類"] == a[u"行"] and b[u"書類"] == b[u"行"])
        parts.append(u"%s は %s(2026 は %s)" % (short(k), lines_text(s25, k, wl), lines_text(s26, k, wl)))
    f.append(u"同じ符号で数が違うもの")
    f.extend(parts)
    f.append(u"道具 R で鳴った符号は %d 種類で、67 本の全部で、道具 R が止まるまでに出した符号ごとの行の数は、道具 P の同じ符号の行の数と同じだった(%d/67)" % (len(sr), same_count(rec)))
    f.append(u"道具 P でだけ鳴った符号は %d 種類(%s)" % (len(ponly), u"・".join(short(k) for k in ponly)))
    f.append(u"止まらずに走った書類は %d 本で、`EDINET.` の符号は %d 種類が鳴った。手を入れない道具では %d 本だった" % (
        p26[u"類別"][u"走った"], p26[u"鳴った符号の種類"][u"EDINET. の符号"], r26[u"類別"][u"走った"]))
    f.append(u"受理済みの書類で鳴った %d 種類の符号は" % len(s26))
    f.append(u"1 回の時間の上限を %d 秒に置いた(封に無い決め)。超えた回は %d" % (rec[u"材料"][u"時間の上限(秒)"], total_to))
    return f


def same_count(rec):
    u"""道具 R の符号ごとの行の数が、道具 P(2026)の同じ符号の行の数と同じ書類の数(書類ごとに見る)。"""
    n = 0
    for d in rec[u"書類"]:
        r, p = d[RUN_KEYS[0]][u"符号ごとの行"], d[RUN_KEYS[1]][u"符号ごとの行"]
        if all(k in p and p[k] == v for k, v in r.items()):
            n += 1
    return n


def sanity_problems(c):
    u"""文書の言い切りが、書類ごとの数に合う(道具 R は 67 本の全部で止まるまでの数が道具 P と同じ・R の符号は P の部分集合・3 つずつの差・4 つの差)。"""
    rec = c.rec
    tot = all_totals(rec)
    s26, s25, sr = (tot[k][u"符号ごと"] for k in (RUN_KEYS[1], RUN_KEYS[2], RUN_KEYS[0]))
    out = []
    if same_count(rec) != 67:
        out.append(u"67 本の全部で道具 R の符号ごとの行の数が道具 P と同じ、でない(%d/67)" % same_count(rec))
    if not set(sr) <= set(s26):
        out.append(u"道具 R の符号が道具 P の符号の部分集合でない")
    if (len(set(s25) - set(s26)), len(set(s26) - set(s25))) != (3, 3):
        out.append(u"2025 でだけ・2026 でだけ鳴った符号が 3 種類ずつでない")
    if len([k for k in set(s25) & set(s26) if s25[k] != s26[k]]) != 4:
        out.append(u"同じ符号で数が違うものが 4 つでない")
    if (len(sr), len(set(s26) - set(sr)), len(s26)) != (15, 9, 24):
        out.append(u"道具 R の符号 15・道具 P でだけ 9・道具 P の全部 24 の種類の数が違う")
    if tot[RUN_KEYS[1]][u"鳴った符号の種類"][u"EDINET. の符号"] + tot[RUN_KEYS[1]][u"鳴った符号の種類"][u"ほかの符号"] != len(s26):
        out.append(u"符号の種類の足し算が合わない")
    if [sum(v[u"行"] for v in tot[k][u"符号ごと"].values()) for k in RUN_KEYS] != [7643, 7783, 12804]:
        out.append(u"指摘の行の合計が文書の言う数と違う")
    if len([k for k in tot[RUN_KEYS[1]][u"符号ごと"] if tot[RUN_KEYS[1]][u"符号ごと"][k][u"書類"] >= 34]) != 8:
        out.append(u"34 本以上で鳴った符号が 8 種類でない")
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


STRUCTURAL = set([u"0", u"1", u"2", u"3", u"4", u"5", u"6", u"7", u"8", u"9", u"10", u"2025", u"2026", u"0.0", u"2.47"])
BOUND_NUMBERS = (60, 3, 33, 40, 8, 30, 10, 65, 5, 34, 67)
NUM_RE = re.compile(r"(?<![A-Za-z0-9_\-.])(\d[\d,]*(?:\.\d+)?)(?![A-Za-z0-9_])")


def doc_number_tokens(line):
    s = re.sub(r"`[^`]*`", u" ", line)
    s = re.sub(r"\b[0-9a-f]{8}\b", u" ", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
    s = re.sub(r"XV0-\d", u" ", s)
    s = re.sub(r"EC\d{4}[A-Z]", u" ", s)
    s = re.sub(r"§\d(?:-\d)?", u" ", s)
    return [m.group(1) for m in NUM_RE.finditer(s)]


def derived_numbers(c):
    tot = all_totals(c.rec)
    out = set(str(x) for x in BOUND_NUMBERS)
    out.add(str(3 * 67))
    out.add(str(c.rec[u"材料"][u"時間の上限(秒)"]))
    for k in RUN_KEYS:
        t = tot[k]
        out |= set(str(v) for v in t[u"類別"].values())
        out |= set(str(v) for v in t[u"鳴った符号の種類"].values())
        out |= set(str(x) for x in (t[u"時間の上限を超えた数"], t[u"34 本以上で鳴った符号の種類"], t[u"包みの形のほかの E が 1 行以上在る書類"], len(t[u"符号ごと"]),
                                      sum(v[u"行"] for v in t[u"符号ごと"].values())))
        for v in t[u"符号ごと"].values():
            out.add(str(v[u"書類"]))
            out.add(str(v[u"行"]))
    r26, p26, p25 = (tot[k] for k in RUN_KEYS)
    out.add(str(len(r26[u"符号ごと"])))
    out.add(str(len(set(p26[u"符号ごと"]) - set(r26[u"符号ごと"]))))
    out.add(str(len(set(p25[u"符号ごと"]) - set(p26[u"符号ごと"]))))
    out.add(str(p25[u"包みの形のほかの E が 1 行以上在る書類"] - p26[u"包みの形のほかの E が 1 行以上在る書類"]))
    out.add(str(len([k for k in set(p25[u"符号ごと"]) & set(p26[u"符号ごと"]) if p25[u"符号ごと"][k] != p26[u"符号ごと"][k]])))
    out.add(str(same_count(c.rec)))
    out.add(str(p26[u"指摘の行が 1 行も無い書類"]))
    return out


def doc_number_problems(c):
    allowed = set(STRUCTURAL) | derived_numbers(c)
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for tok in doc_number_tokens(ln):
            if tok.replace(u",", u"") not in allowed:
                out.append(u"文書の %d 行目の数 %s が記録から組んだ数の外: %s" % (i, tok, ln[:30]))
    return out


def sec3_problems(c):
    u"""§3 は記録に欄の無い読みの節。数字は 3 本・1 本・67 本の 3 つだけ。「67 本の全部が同じ理由で止まった」と言わず、その否定の字が在る。"""
    s = section(c.doc, u"## §3 ", u"## §4 ")
    out = []
    for ln in s.splitlines():
        for t in doc_number_tokens(ln):
            if t not in (u"3", u"1", u"67", u"0.0", u"2025", u"2026"):
                out.append(u"§3 に 3・1・67 以外の数 %s" % t)
    if u"67 本の全部が同じ理由で止まったとは確かめていない" not in s:
        out.append(u"§3 に「67 本の全部が同じ理由で止まったとは確かめていない」が無い")
    if re.search(u"67 本の全部が同じ理由で止まった(?!とは)", s):
        out.append(u"§3 が「67 本の全部が同じ理由で止まった」と肯定している")
    if u"記録に欄の無い読み" not in s.splitlines()[0]:
        out.append(u"§3 の見出しが「記録に欄の無い読み」でない")
    return out


def affirm_problems(c):
    u"""「EDINET の検査に通る」「XBRL を作れる」は、その行に「言えない」が在るときだけ(肯定の形で書かない)。"""
    out = []
    for i, ln in enumerate(c.doc.splitlines(), 1):
        for w in (u"EDINET の検査に通る", u"XBRL を作れる"):
            if w in ln and u"言えない" not in ln:
                out.append(u"文書の %d 行目が「%s」を言えないの外で書いている" % (i, w))
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
M1  書類 1 の道具 P × 2026 の EC5611W の行を 1 増やす(集計は直さない)        -> recount が赤
M2  集計の道具 P × 2026 の EC5611W の行を 1 増やす                           -> recount が赤
M3  予測の欄 XV0-5 を 23 → 24                                                -> recount が赤
M4  文書 §2 の道具 R の指摘の行の合計 7643 → 7644                            -> frag・numbers が赤(7644 は許す数の外)
M5  文書の XV0-3 の判定を外れにする                                           -> verdict が赤
M6  頭の「67 本のうち 1 本を手で掛けてから立てた」を消す                      -> head が赤
M7  文書に docID の形を足す                                                   -> forbidden が赤
M8  道具 P × 2026 の 34 本に EC1001E を足し集計と判定も整合して直す(XV0-3 が外れになる) -> verdict が赤(recount は緑)
M9  記録の sha256 の写しを違う値に                                            -> sha が赤
M10 文書の commit の字 762d361e を 762d361f に                                -> commits が赤
M11 §3 に「約 2800 行」を足す                                                 -> sec3・numbers が赤
M12 文書の「当たり 7・外れ 0」を「当たり 6・外れ 1」に(件数の行)              -> verdict が赤
M13 頭の「この便からは言えない」を消す                                        -> head が赤
M14 記録の材料の書類の本数 67 → 68                                            -> recount が赤
M15 文書に「保証」を足す                                                      -> forbidden が赤
M16 記録に docid の欄を足す                                                   -> clean が赤
M17 文書に 7792 という数字の言い切りを足す                                    -> numbers が赤
M18 封の写しから「60 本以上」を消す                                           -> bound が赤
M19 頭から「先に負けと限界を書く」を消す                                      -> head が赤
M20 文書の「EC1001E(67 本・1005 行)」を 1006 行に                            -> frag・numbers が赤
M21 文書の XV0-6 のセルの「差 65」を「差 64」に                                -> verdict が赤
M22 §5 の「人間に示す次の便の候補」の字を消す                                  -> verdict・phrases が赤
M23 封の写しの「5 本以上在ったら、先に自分の欠陥を疑う」を消す                  -> bound が赤
M24 書類 3 の道具 P × 2026 の類を 走った → 止まった(集計は直さない)           -> recount が赤
M25 文書の「道具 R で鳴った符号は 15 種類」を 16 種類に                        -> frag・numbers が赤
M26 書類 5 の道具 R の EC0121E の行を 1 増やし集計と判定も整合して直す          -> sanity・frag が赤(recount は緑)
M27 §3 に「67 本の全部が同じ理由で止まった」の肯定を足す                       -> sec3 が赤
M28 文書に「EDINET の検査に通る」を肯定の形で足す                              -> affirm が赤
M29 §3 の「67 本の全部が同じ理由で止まったとは確かめていない」を消す           -> sec3 が赤
M30 書類 2 の道具 P × 2025 を時間の上限を超えた(止まった)にし集計と判定も整合 -> frag が赤(recount は緑)
M31 文書の符号の表の EC5710W の行 86 → 87                                     -> frag が赤(numbers は 87 が許す数の外なら赤)
M32 封の写しの「33 本以下」を消す                                             -> bound が赤
M33 文書の「は、0 本なので発火しない」を「は、5 本なので発火する」に           -> verdict が赤
M34 書類 1 の道具 P × 2026 の符号を全部消し(行の数は残す)集計と判定も整合      -> frag・verdict が赤(指摘 0 の書類が出る)
M35 文書 §1 の XV0-1 のセル 67/67 → 66/67                                      -> verdict が赤
M36 書類 4 の道具 P × 2026 の出力の行の数を指摘の行の数より少なくする            -> recount が赤
M37 頭の「(67/67)」を「(66/67)」に                                           -> frag が赤
M38 文書に「XBRL を作れます」を足す                                            -> affirm が赤
"""


def rebuild(rec):
    u"""書類ごとの数はそのままに、集計と予測の判定に要る数を作り直す(整合した変更)。"""
    tot = all_totals(rec)
    rec[u"集計"] = collections.OrderedDict((k, tot[k]) for k in RUN_KEYS)
    rec[PRED_KEY] = pred_expected(tot)


def rep(c, old, new, attr="doc", count=1):
    s = getattr(c, attr)
    assert old in s, old
    setattr(c, attr, s.replace(old, new, count))


def drop_all(c, phrase):
    assert phrase in c.doc
    c.doc = c.doc.replace(phrase, u"X")


def m_1(c):
    d = c.rec[u"書類"][0][RUN_KEYS[1]][u"符号ごとの行"]
    d[u"EDINET.EC5611W"] += 1


def m_2(c):
    c.rec[u"集計"][RUN_KEYS[1]][u"符号ごと"][u"EDINET.EC5611W"][u"行"] += 1


def m_8(c):
    for d in c.rec[u"書類"][:34]:
        e = d[RUN_KEYS[1]]
        if u"EDINET.EC1001E" not in e[u"符号ごとの行"]:
            e[u"符号ごとの行"][u"EDINET.EC1001E"] = 1
            e[u"出力の行の数"] += 1
    rebuild(c.rec)


def m_26(c):
    e = c.rec[u"書類"][4][RUN_KEYS[0]]
    e[u"符号ごとの行"][u"EDINET.EC0121E"] += 1
    e[u"出力の行の数"] += 1
    rebuild(c.rec)


def m_30(c):
    e = c.rec[u"書類"][1][RUN_KEYS[2]]
    e[u"類"] = u"止まった"
    e[u"時間の上限を超えた"] = True
    rebuild(c.rec)


def m_34(c):
    c.rec[u"書類"][0][RUN_KEYS[1]][u"符号ごとの行"] = collections.OrderedDict()
    rebuild(c.rec)


def m_36(c):
    e = c.rec[u"書類"][3][RUN_KEYS[1]]
    e[u"出力の行の数"] = sum(e[u"符号ごとの行"].values()) - 1


def add_doc(c, text):
    c.doc = c.doc + u"\n" + text + u"\n"


MUTATIONS = (
    (u"M1 書類 1 の道具 P × 2026 の EC5611W の行を 1 増やす", m_1, (u"recount",)),
    (u"M2 集計の道具 P × 2026 の EC5611W の行を 1 増やす", m_2, (u"recount",)),
    (u"M3 予測の欄 XV0-5 を 24 に", lambda c: c.rec[PRED_KEY].__setitem__(PK[4], 24), (u"recount",)),
    (u"M4 文書 §2 の道具 R の行の合計 7643 → 7644", lambda c: rep(c, u"| 7643 |", u"| 7644 |"), (u"frag", u"numbers")),
    (u"M5 XV0-3 の判定を外れに", lambda c: rep(c, u"| 2/67 | 当たり |", u"| 2/67 | **外れ** |"), (u"verdict",)),
    (u"M6 頭の「1 本を手で掛けてから立てた」を消す", lambda c: rep(c, u"67 本のうち 1 本を手で掛けてから立てた", u"X"), (u"head",)),
    (u"M7 文書に docID の形を足す", lambda c: add_doc(c, u"書類 S100ABCD。"), (u"forbidden",)),
    (u"M8 道具 P × 2026 の 34 本に EC1001E を足し整合(XV0-3 が外れになる)", m_8, (u"verdict",)),
    (u"M9 記録の sha256 の写しを違う値に", lambda c: c.shas.__setitem__(RECORD_REL, u"0" * 64), (u"sha",)),
    (u"M10 文書の commit の字を 1 字替える", lambda c: rep(c, u"762d361e", u"762d361f", count=9), (u"commits",)),
    (u"M11 §3 に「約 2800 行」を足す", lambda c: rep(c, u"- 封 §7 の「直しが", u"約 2800 行が該当する。\n- 封 §7 の「直しが"), (u"sec3", u"numbers")),
    (u"M12 件数の行を当たり 6・外れ 1 に", lambda c: rep(c, u"- 当たり 7・外れ 0。", u"- 当たり 6・外れ 1。"), (u"verdict",)),
    (u"M13 頭の「この便からは言えない」を消す", lambda c: rep(c, u"この便からは言えない", u"X"), (u"head",)),
    (u"M14 記録の材料の書類の本数を 68 に", lambda c: c.rec[u"材料"].__setitem__(u"書類の本数", 68), (u"recount",)),
    (u"M15 文書に「保証」を足す", lambda c: add_doc(c, u"保証する。"), (u"forbidden",)),
    (u"M16 記録に docid の欄を足す", lambda c: c.rec[u"書類"][0].__setitem__(u"docid", u"x"), (u"clean",)),
    (u"M17 文書に 7792 の言い切りを足す", lambda c: add_doc(c, u"指摘の行は 7792 に近い。"), (u"numbers",)),
    (u"M18 封の写しから「60 本以上」を消す", lambda c: rep(c, u"60 本以上", u"X", attr="seal", count=9), (u"bound",)),
    (u"M19 頭の「先に負けと限界を書く」を消す", lambda c: drop_all(c, u"先に負けと限界を書く"), (u"head",)),
    (u"M20 「EC1001E(67 本・1005 行)」を 1006 行に", lambda c: rep(c, u"EC1001E(67 本・1005 行)", u"EC1001E(67 本・1006 行)"), (u"frag", u"numbers")),
    (u"M21 XV0-6 のセルの差 65 → 64", lambda c: rep(c, u"差 65", u"差 64", count=1), (u"verdict",)),
    (u"M22 §5 の次の便の候補の字を消す", lambda c: rep(c, u"人間に示す次の便の候補(封 §6。XV0-2 が当たりなので示す)", u"X"), (u"verdict", u"phrases")),
    (u"M23 封の写しの「5 本以上在ったら、先に自分の欠陥を疑う」を消す", lambda c: rep(c, u"5 本以上在ったら、先に自分の欠陥を疑う", u"X", attr="seal"), (u"bound",)),
    (u"M24 書類 3 の道具 P × 2026 の類を止まったに", lambda c: c.rec[u"書類"][2][RUN_KEYS[1]].__setitem__(u"類", u"止まった"), (u"recount",)),
    (u"M25 「道具 R で鳴った符号は 15 種類」を 16 に", lambda c: rep(c, u"道具 R で鳴った符号は 15 種類", u"道具 R で鳴った符号は 16 種類"), (u"frag", u"numbers")),
    (u"M26 書類 5 の道具 R の EC0121E の行を 1 増やし整合", m_26, (u"sanity", u"frag")),
    (u"M27 §3 に「67 本の全部が同じ理由で止まった」を足す", lambda c: rep(c, u"- 封 §7 の「直しが", u"67 本の全部が同じ理由で止まった。\n- 封 §7 の「直しが"), (u"sec3",)),
    (u"M28 文書に「EDINET の検査に通る」を肯定で足す", lambda c: add_doc(c, u"この道具は EDINET の検査に通る。"), (u"affirm",)),
    (u"M29 §3 の否定の字を消す", lambda c: rep(c, u"67 本の全部が同じ理由で止まったとは確かめていない", u"X"), (u"sec3", u"phrases")),
    (u"M30 書類 2 の道具 P × 2025 を時間の上限を超えたにして整合", m_30, (u"frag",)),
    (u"M31 符号の表の EC5710W の行 86 → 87", lambda c: rep(c, u"| EC5710W | 31 | 86 |", u"| EC5710W | 31 | 87 |"), (u"frag", u"numbers")),
    (u"M32 封の写しから「33 本以下」を消す", lambda c: rep(c, u"33 本以下", u"X", attr="seal", count=9), (u"bound",)),
    (u"M33 「は、0 本なので発火しない」を 5 本・発火するに", lambda c: rep(c, u"は、0 本なので発火しない", u"は、5 本なので発火する"), (u"verdict",)),
    (u"M34 書類 1 の道具 P × 2026 の符号を全部消して整合", m_34, (u"frag", u"verdict")),
    (u"M35 XV0-1 のセル 67/67 → 66/67", lambda c: rep(c, u"| 67/67 | 当たり |", u"| 66/67 | 当たり |"), (u"verdict",)),
    (u"M36 書類 4 の道具 P × 2026 の出力の行の数を指摘の行より少なく", m_36, (u"recount",)),
    (u"M37 頭の「(67/67)」を「(66/67)」に", lambda c: rep(c, u"止まった(67/67)", u"止まった(66/67)"), (u"frag",)),
    (u"M38 文書に「XBRL を作れます」を足す", lambda c: add_doc(c, u"XBRL を作れます。"), (u"affirm",)),
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
        tot = all_totals(self.c.rec)
        self.assertEqual([7643, 7783, 12804], [sum(v[u"行"] for v in tot[k][u"符号ごと"].values()) for k in RUN_KEYS])
        self.assertEqual(201, 3 * len(self.c.rec[u"書類"]))
        self.assertEqual(67, same_count(self.c.rec))
        self.assertEqual((15, 24, 24), tuple(len(tot[k][u"符号ごと"]) for k in RUN_KEYS))
        r26, p26 = tot[RUN_KEYS[0]], tot[RUN_KEYS[1]]
        self.assertEqual(9, len(set(p26[u"符号ごと"]) - set(r26[u"符号ごと"])))
        self.assertEqual([u"EDINET.EC1016E", u"EDINET.EC8024E"], sorted(k for k in p26[u"符号ごと"] if E_CODE.match(k) and k[len(EDI) + 2] != u"0"))
        self.assertEqual((23, 8), (p26[u"鳴った符号の種類"][u"EDINET. の符号"], p26[u"34 本以上で鳴った符号の種類"]))

    def test_c_1_the_seal_has_the_bound_phrases(self):
        self.assertEqual([], bound_problems(self.c))

    def test_c_2_the_verdicts_are_decided_again_and_equal_the_document(self):
        self.assertEqual([], verdict_problems(self.c))
        j = judge(all_totals(self.c.rec))
        self.assertEqual(7, sum(1 for v in j.values() if v))

    def test_d_1_every_number_in_the_document_is_bound_to_the_record(self):
        self.assertEqual([], doc_number_problems(self.c))

    def test_d_2_the_table_rows_and_the_statements_equal_the_record(self):
        self.assertEqual([], fragment_problems(self.c))
        self.assertEqual([], sanity_problems(self.c))

    def test_d_3_section3_holds_only_three_one_and_sixty_seven(self):
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
        self.assertFalse(judge(all_totals(c.rec))[u"XV0-3"])

    def test_g_4_every_check_name_a_mutation_names_exists_and_every_check_has_a_mutation(self):
        named = set(k for _, _, ks in MUTATIONS for k in ks)
        self.assertEqual(set(CHECKS), named)

    def test_g_5_the_judgement_edges_at_the_seal_bounds(self):
        u"""境の 1 つ手前と境の数: XV0-3 は 33 本が当たり・34 本が外れ。"""
        c = Ctx().copy()
        for n, want in ((33, True), (34, False)):
            for i, d in enumerate(c.rec[u"書類"]):
                e = d[RUN_KEYS[1]][u"符号ごとの行"]
                e.pop(u"EDINET.EC1001E", None)
                e.pop(u"EDINET.EC1016E", None)
                e.pop(u"EDINET.EC8024E", None)
                if i < n:
                    e[u"EDINET.EC1001E"] = 1
            rebuild(c.rec)
            self.assertEqual(want, judge(all_totals(c.rec))[u"XV0-3"], n)


if __name__ == "__main__":
    unittest.main()
