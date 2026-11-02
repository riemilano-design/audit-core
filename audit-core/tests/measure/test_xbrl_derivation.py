# -*- coding: utf-8 -*-
u"""門: 導出の検証の診断(前半)(封 docs/XBRL_DERIVATION_DIAG_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_2026-11-02.json の形(封・HEAD・script の sha256・配線の門・key_leaks・docID 無し)。
- 予測 B-1〜B-10 を、記録の集計と封 §3 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 集計を行から数え直す(式ごとの帯の中・判定・母数・新しく説明が付いた行・最小 e/G)。行の式の値を自分で計算し直す。
- F1 の段が前の便の記録(decimals)と同じ(再現)。
- 文書の表の実測の欄と散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
- script が標準ライブラリだけで engine を import しない。順序(封 < script・記録・文書・門)。変異で赤くなる。
"""
from __future__ import print_function

import ast
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_DERIVATION_DIAG_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_DIAG_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation.py"
INPUT_REL = "fixtures/xbrl/delta_naming_2026-10-30.json"
PREV_REL = "fixtures/xbrl/delta_decimals_2026-11-01.json"
SEAL_COMMIT_SHORT = "67efc7a"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"B-%d" % i for i in range(1, 11))
FORMULAS = (u"F1", u"F3", u"F4", u"F5", u"F1k", u"F1m", u"F3k", u"F3m", u"F4k", u"F4m")
SCALE_FORMULAS = (u"F1k", u"F1m", u"F3k", u"F3m", u"F4k", u"F4m")
STAGES = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F", u"不一致", u"比較不能")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
CLAIM_ID_RE = re.compile(r"\bN\d{3}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "io", "json", "os", "re", "subprocess", "sys", "__future__"}
FORBIDDEN = (u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


# ---------------------------------------------------------------- 封 §3 の幅

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(B-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            cells = [c.strip() for c in body.split(u" | ")]
            out[m.group(1)] = tuple(cells)
    return out


def num(s):
    return int(s.replace(u",", u""))


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"B-1", u"B-2", u"B-3", u"B-4", u"B-5", u"B-6", u"B-7", u"B-8"):
        m = re.search(r"\*\*(\d+)〜(\d+) ?行?\*\*", rows[i][0])
        b[i] = (num(m.group(1)), num(m.group(2)))
    b[u"B-9"] = num(re.search(r"\*\*0〜(\d+)%\*\*", rows[u"B-9"][0]).group(1))
    return b


# ---------------------------------------------------------------- 求め直し

def ref_pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"B-1"] = b[u"B-1"][0] <= T[u"母数のうち F3 が帯の中"] <= b[u"B-1"][1]
    J[u"B-2"] = b[u"B-2"][0] <= T[u"母数のうち F4 が帯の中"] <= b[u"B-2"][1]
    J[u"B-3"] = b[u"B-3"][0] <= T[u"母数のうち F5 が帯の中"] <= b[u"B-3"][1]
    J[u"B-4"] = b[u"B-4"][0] <= T[u"倍率の変種のどれかが帯の中(母数)"] <= b[u"B-4"][1]
    J[u"B-5"] = b[u"B-5"][0] <= T[u"新しく説明が付いた行"] <= b[u"B-5"][1]
    J[u"B-6"] = b[u"B-6"][0] <= T[u"母数のうち保留"] <= b[u"B-6"][1]
    J[u"B-7"] = b[u"B-7"][0] <= T[u"母数のうち本便でも不一致"] <= b[u"B-7"][1]
    J[u"B-8"] = b[u"B-8"][0] <= T[u"前の便で比較不能のうち F3 が帯の中"] <= b[u"B-8"][1]
    share = ref_pct(T[u"新しく説明が付いた行の型"].get(u"増減の型", 0), T[u"新しく説明が付いた行"])
    J[u"B-9"] = share is not None and share <= b[u"B-9"]
    top = list(T[u"導出一致の式(母数)"].items())
    J[u"B-10"] = bool(top) and top[0][0] == u"F4" and (len(top) == 1 or top[0][1] > top[1][1])
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    out[u"B-9 の割合"] = share
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    T[u"式ごとの帯の中"] = collections.OrderedDict((n, sum(1 for r in rows if r[u"式"][n][u"段"] in IN_BAND)) for n in FORMULAS)
    T[u"判定"] = collections.OrderedDict((v, sum(1 for r in rows if r[u"判定"] == v)) for v in (u"導出一致", u"保留", u"不一致", u"比較不能"))
    outside = [r for r in rows if r[u"前の便で帯の外"]]
    T[u"前の便で帯の外の行(母数)"] = len(outside)
    new = [r for r in outside if r[u"新しく説明が付いた"]]
    T[u"新しく説明が付いた行"] = len(new)
    T[u"母数のうち本便でも不一致"] = sum(1 for r in outside if r[u"判定"] == u"不一致")
    T[u"母数のうち保留"] = sum(1 for r in outside if r[u"判定"] == u"保留")
    T[u"倍率の変種のどれかが帯の中(母数)"] = sum(1 for r in outside if any(r[u"式"][n][u"段"] in IN_BAND for n in SCALE_FORMULAS))
    for f in (u"F3", u"F4", u"F5"):
        T[u"母数のうち %s が帯の中" % f] = sum(1 for r in outside if r[u"式"][f][u"段"] in IN_BAND)
    T[u"前の便で比較不能のうち F3 が帯の中"] = sum(1 for r in rows if r[u"前の便の段"] == u"比較不能" and r[u"式"][u"F3"][u"段"] in IN_BAND)
    best = sorted(min(x[u"e"] / x[u"G"] for x in r[u"式"].values() if x[u"e"] is not None) for r in outside)
    n = len(best)
    T[u"最小 e/G"] = (round(best[0], 2), round(best[n // 10], 2), round(best[n // 2], 2), sum(1 for v in best if v < 2), sum(1 for v in best if v < 10))
    return T


def ref_formula(name, t, u, c, p, g_c, g_p):
    need = {u"F1": (u"c", u"p"), u"F3": (u"c",), u"F4": (u"p",), u"F5": (u"c", u"p")}[name.rstrip(u"km")]
    scale = {u"k": 1e3, u"m": 1e-3}.get(name[-1], 1.0)
    facts = {u"c": (c, g_c), u"p": (p, g_p)}
    if any(facts[k][0] is None or facts[k][1] is None for k in need):
        return u"比較不能", None
    v = {u"F1": lambda: c - p, u"F3": lambda: c, u"F4": lambda: p, u"F5": lambda: c + p}[name.rstrip(u"km")]()
    G = sum(facts[k][1] for k in need) + u * scale
    e = abs(abs(v) - t * scale)
    stage = u"完全一致" if e == 0 else u"丸めの帯 H" if e <= G / 2.0 else u"丸めの帯 F" if e <= G else u"不一致"
    return stage, e


def g_of(dec):
    return None if dec is None else float(10) ** (-int(dec))


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(B-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    q = T[u"母数の各行の最小 e/G"]
    return {
        u"B-1": [u"%d" % T[u"母数のうち F3 が帯の中"]], u"B-2": [u"%d" % T[u"母数のうち F4 が帯の中"]],
        u"B-3": [u"%d" % T[u"母数のうち F5 が帯の中"]], u"B-4": [u"%d" % T[u"倍率の変種のどれかが帯の中(母数)"]],
        u"B-5": [u"%d" % T[u"新しく説明が付いた行"]], u"B-6": [u"%d" % T[u"母数のうち保留"]],
        u"B-7": [u"%d" % T[u"母数のうち本便でも不一致"]], u"B-8": [u"%d" % T[u"前の便で比較不能のうち F3 が帯の中"]],
        u"B-9": [u"母数 0" if T[u"新しく説明が付いた行"] == 0 else u"%"], u"B-10": [u"導出一致が無い" if not T[u"導出一致の式(母数)"] else u"F"],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が B-1〜B-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        if cells[2] != u"**%s**" % J[i]:
            p.append(u"%s の判定が %s でない" % (i, J[i]))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"B-1", u"B-2", u"B-3", u"B-4", u"B-5", u"B-6", u"B-7", u"B-8"):
            if not re.fullmatch(r"\d+(\(.*\))?", cells[1]):
                p.append(u"%s の実測の欄が数で始まらない: %s" % (i, cells[1]))
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J[i] == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    # 2-1 の分位・最も近い式の分布
    q = T[u"母数の各行の最小 e/G"]
    for s in (u"最小 %s" % q[u"min"], u"10 分位 %s" % q[u"p10"], u"中央値 %s" % q[u"p50"], u"2 未満の行 %d" % q[u"2 未満の行"], u"10 未満の行 %d" % q[u"10 未満の行"]):
        if s not in doc:
            p.append(u"2-1 に %s が無い" % s)
    near = u"・".join(u"%s %d" % (k, v) for k, v in T[u"母数の各行で最も近い式"].items())
    if near not in doc:
        p.append(u"2-1 の最も近い式の分布が記録の順と数でない")
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"B-\d+|§\d+(-\d+)*|10[³⁻]", u" ", s)
        for n in re.findall(r"\d[\d,.]*\d|\d", s):
            flat = n.replace(u",", u"")
            if len(re.sub(r"\D", u"", flat)) >= 3 and NOT_GATED not in ln and n not in rec_text and flat not in rec_text:
                p.append(u"%s … %s" % (n, ln[:50]))
    for w in FORBIDDEN:
        if w in doc:
            p.append(u"禁止語 %s" % w)
    return p


def script_problems(src):
    p = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    p.append(u"import %s" % a.name)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
            p.append(u"from %s import" % node.module)
    for bad in ("adapters", "audit_core", "zipfile", "urllib", "http"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    return p


def added_commits(path):
    rc, out = git("log", "--diff-filter=A", "--format=%H", "--", path)
    return [l for l in out.splitlines() if l.strip()] if rc == 0 else []


def is_anc(a, b):
    return a is not None and b is not None and git("merge-base", "--is-ancestor", a, b)[0] == 0


def order_problems():
    p = []
    s = added_commits(PREFIX + SEAL_REL)
    if len(s) != 1 or not HEX40.match(s[0]):
        return [u"封を足した commit がちょうど 1 つに決まらない(%d)" % len(s)]
    S = s[0]
    if not S.startswith(SEAL_COMMIT_SHORT):
        p.append(u"封の commit が %s でない" % SEAL_COMMIT_SHORT)
    if not is_anc(S, "HEAD"):
        p.append(u"封の commit が HEAD の祖先でない")
    for rel in (SCRIPT_REL, REC_REL, DOC_REL, GATE_REL):
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            continue
        if a[-1] == S or not is_anc(S, a[-1]):
            p.append(u"%s が封の後でない" % rel)
    return p


def load_script():
    spec = importlib.util.spec_from_file_location("derivation_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ================================================================ tests

class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)
        cls.inp = jload(os.path.join(ROOT, INPUT_REL))
        cls.prev = jload(os.path.join(ROOT, PREV_REL))

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ入力の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(len(self.rec[u"行"]), 296)
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertTrue(all(v for k, v in W.items() if k.startswith(u"(") and isinstance(v, bool)), W)
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        with io.open(os.path.join(ROOT, INPUT_REL), "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"読んだ入力の sha256"])
        self.assertEqual(self.rec_text.count("scratchpad"), 0)

    def test_a_2_no_docid_claimid_or_pointer_in_record_doc_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        self.assertEqual(CLAIM_ID_RE.findall(self.rec_text), [])
        self.assertNotIn(u"pointers", self.rec_text)
        for p in (DOC, SCRIPT, __file__):
            t = jtext(p)
            self.assertEqual(DOCID_RE.findall(t), [], p)
            self.assertEqual(CLAIM_ID_RE.findall(t), [], p)

    def test_b_1_rows_recomputed_from_the_input(self):
        u"""行ごとに式の値・段を自分で計算し直す。前の便の段は decimals の記録の同じ位置の行から。"""
        self.assertEqual(len(self.inp[u"行"]), 296)
        self.assertEqual(len(self.prev[u"行"]), 296)
        for r, q, s in zip(self.inp[u"行"], self.prev[u"行"], self.rec[u"行"]):
            self.assertEqual((r[u"位置"], q[u"位置"]), (s[u"位置"], s[u"位置"]))
            t, u, c = r[u"文の値"], r[u"帯の幅"], r[u"当期の値"]
            p = r[u"前期の値"] if r[u"前期の fact 在り"] else None
            g_c, g_p = g_of(r[u"当期の decimals"]), (g_of(r[u"前期の decimals"]) if r[u"前期の fact 在り"] else None)
            hit = []
            for n in FORMULAS:
                stage, e = ref_formula(n, t, u, c, p, g_c, g_p)
                self.assertEqual(stage, s[u"式"][n][u"段"], (s[u"位置"], n))
                if e is not None:
                    self.assertAlmostEqual(e, s[u"式"][n][u"e"])
                if stage in IN_BAND:
                    hit.append(n)
            verdict = u"導出一致" if len(hit) == 1 else u"保留" if len(hit) >= 2 else u"不一致"
            self.assertEqual(verdict, s[u"判定"], s[u"位置"])
            self.assertEqual(hit, s[u"帯の中の式"])
            self.assertEqual(s[u"前の便の段"], q[u"段"])
            self.assertEqual(s[u"前の便で帯の外"], q[u"段"] in (u"不一致", u"比較不能"))
            self.assertEqual(s[u"新しく説明が付いた"], s[u"前の便で帯の外"] and verdict in (u"導出一致", u"保留"))

    def test_b_2_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in (u"式ごとの帯の中", u"判定", u"前の便で帯の外の行(母数)", u"新しく説明が付いた行", u"母数のうち本便でも不一致", u"母数のうち保留",
                  u"倍率の変種のどれかが帯の中(母数)", u"母数のうち F3 が帯の中", u"母数のうち F4 が帯の中", u"母数のうち F5 が帯の中", u"前の便で比較不能のうち F3 が帯の中"):
            self.assertEqual(T[k], R[k], k)
        q = R[u"母数の各行の最小 e/G"]
        self.assertEqual(T[u"最小 e/G"], (q[u"min"], q[u"p10"], q[u"p50"], q[u"2 未満の行"], q[u"10 未満の行"]))
        self.assertEqual(R[u"前の便で帯の外の行(母数)"], 246)

    def test_b_3_f1_reproduces_the_previous_record(self):
        prev_stages = self.prev[u"集計"][u"stages"][u"段"] if u"stages" in self.prev[u"集計"] else self.prev[u"集計"][u"全体"][u"stages"][u"段"]
        f1 = collections.OrderedDict((s, sum(1 for r in self.rec[u"行"] if r[u"式"][u"F1"][u"段"] == s)) for s in STAGES)
        for s in STAGES:
            self.assertEqual(f1[s], prev_stages.get(s, 0), s)
        self.assertEqual(f1[u"丸めの帯 H"], 50)
        # 行ごとにも(位置で引く): F1 の段 = decimals の記録の段(監査の気づき 2026-11-02)
        for s, q in zip(self.rec[u"行"], self.prev[u"行"]):
            self.assertEqual(s[u"位置"], q[u"位置"])
            self.assertEqual(s[u"式"][u"F1"][u"段"], q[u"段"], s[u"位置"])

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 10)

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"B-1": (0, 10), u"B-2": (5, 30), u"B-3": (0, 3), u"B-4": (3, 20), u"B-5": (10, 50),
                                             u"B-6": (0, 8), u"B-7": (190, 236), u"B-8": (0, 4), u"B-9": 30})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_is_stdlib_only_and_agrees(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        mod = load_script()
        self.assertEqual(mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        rows = mod.build_rows(self.inp[u"行"], self.prev[u"行"])
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(mod.judge(mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])
        # 合成の行で式が効くこと(0 件の結果が実装の欠陥でない)
        for name, t in ((u"F4", 31172e6), (u"F3k", 37006e3), (u"F5", 37006e6 + 31172e6), (u"F1m", 5834e9), (u"F1", 5834e6)):
            pf = collections.OrderedDict((n, mod.eval_formula(n, t, 1e6, 37006e6, 31172e6, 1e6, 1e6)) for n in mod.FORMULAS)
            self.assertEqual(mod.verdict_of(pf), (u"導出一致", [name]), name)

    def test_i_1_order(self):
        rc, _ = git("cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(order_problems(), [])


class MutationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)

    def test_m_1_flipping_a_judgement_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"予測の判定"][u"B-5"] = u"当たり"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"母数のうち F4 が帯の中"] = 7
        T = ref_tally(rec[u"行"])
        self.assertNotEqual(T[u"母数のうち F4 が帯の中"], rec[u"集計"][u"母数のうち F4 が帯の中"])

    def test_m_3_changing_a_row_stage_is_caught_by_recompute(self):
        rec = json.loads(self.rec_text)
        r = rec[u"行"][0]
        r[u"式"][u"F4"][u"段"] = u"丸めの帯 H"
        inp = jload(os.path.join(ROOT, INPUT_REL))[u"行"][0]
        t, u, c, p = inp[u"文の値"], inp[u"帯の幅"], inp[u"当期の値"], inp[u"前期の値"]
        stage, _ = ref_formula(u"F4", t, u, c, p, g_of(inp[u"当期の decimals"]), g_of(inp[u"前期の decimals"]))
        self.assertNotEqual(stage, r[u"式"][u"F4"][u"段"])

    def test_m_4_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_5_doc_number_change_is_caught(self):
        bad = self.doc.replace(u"| 246(母数の全部) |", u"| 245(母数の全部) |")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**190〜236 行**", u"**190〜250 行**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_7_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_8_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])


if __name__ == "__main__":
    unittest.main()
