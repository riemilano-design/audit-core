# -*- coding: utf-8 -*-
u"""門: 導出の検証の診断(後半)(封 docs/XBRL_DERIVATION_FULL_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_full_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 C-1〜C-10 を、記録の集計と封 §3 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 集計を行から数え直す。行の候補の e・段を v と t' から計算し直す。D2・D3 の組が同じ fact でないこと。
- script の build_rows を自分で呼び直して記録の行と一致させる(材料は repo の 4 file)。合成の値で各型が効くこと。
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
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
PREFIX = "audit-core/"

SEAL_REL = "docs/XBRL_DERIVATION_FULL_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_FULL_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_full_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_full_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation_full.py"
SEAL_COMMIT_SHORT = "42b51d3"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"C-%d" % i for i in range(1, 11))
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6")
IN_BAND = (u"完全一致", u"丸めの帯 H", u"丸めの帯 F")
VERDICTS = (u"導出一致", u"保留", u"不一致")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "io", "json", "os", "re", "subprocess", "sys", "zipfile", "__future__"}
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
        m = re.match(r"^\| \*\*(C-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    b[u"C-1"] = int(re.search(r"\*\*(\d+)% 以上\*\*", rows[u"C-1"][0]).group(1))
    for i in (u"C-2", u"C-3", u"C-4", u"C-5", u"C-7", u"C-9"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    b[u"C-8"] = int(re.search(r"\*\*(\d+)% 以上\*\*", rows[u"C-8"][0]).group(1))
    return b


# ---------------------------------------------------------------- 求め直し

def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"C-1"] = T[u"対照の割合"] is not None and T[u"対照の割合"] >= b[u"C-1"]
    J[u"C-2"] = b[u"C-2"][0] <= T[u"母数のうち D1 が帯の中"] <= b[u"C-2"][1]
    J[u"C-3"] = b[u"C-3"][0] <= T[u"母数の判定"][u"導出一致"] <= b[u"C-3"][1]
    J[u"C-4"] = b[u"C-4"][0] <= T[u"母数の判定"][u"不一致"] <= b[u"C-4"][1]
    J[u"C-5"] = b[u"C-5"][0] <= T[u"母数の判定"][u"保留"] <= b[u"C-5"][1]
    top = list(T[u"導出一致の型(D1 以外)"].items())
    J[u"C-6"] = bool(top) and top[0][0] == u"D2" and (len(top) == 1 or top[0][1] > top[1][1])
    J[u"C-7"] = b[u"C-7"][0] <= T[u"% のうち D3 か D5 が帯の中"] <= b[u"C-7"][1]
    J[u"C-8"] = T[u"導出一致で根拠に要素名の割合"] is not None and T[u"導出一致で根拠に要素名の割合"] >= b[u"C-8"]
    J[u"C-9"] = b[u"C-9"][0] <= T[u"円 のうち D6 が帯の中"] <= b[u"C-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"C-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def ref_tally(rows):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"母数"]]
    ctl = [r for r in rows if r[u"対照"]]
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"対照の割合"] = pct(sum(1 for r in ctl if r[u"D1 に recomputed の値が在る"]), len(ctl))
    T[u"対照の割合(型を問わず)"] = pct(sum(1 for r in ctl if r[u"どの型かに recomputed の値が在る"]), len(ctl))
    T[u"母数のうち D1 が帯の中"] = sum(1 for r in pop if r[u"D1 が帯の中"])
    T[u"母数の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"判定"] == v)) for v in VERDICTS)
    one = [r for r in pop if r[u"判定"] == u"導出一致"]
    T[u"導出一致の型"] = _cnt(r[u"候補"][0][u"型"] for r in one)
    T[u"導出一致の型(D1 以外)"] = _cnt(r[u"候補"][0][u"型"] for r in one if r[u"候補"][0][u"型"] != u"D1")
    T[u"導出一致で根拠に要素名"] = sum(1 for r in one if r[u"根拠に要素名"])
    T[u"導出一致で根拠に要素名の割合"] = pct(T[u"導出一致で根拠に要素名"], len(one))
    T[u"% のうち D3 か D5 が帯の中"] = sum(1 for r in pop if r[u"unit"] == u"%" and r[u"型ごとの候補の数"][u"D3"] + r[u"型ごとの候補の数"][u"D5"] > 0)
    T[u"円 のうち D6 が帯の中"] = sum(1 for r in pop if r[u"unit"] == u"円" and r[u"型ごとの候補の数"][u"D6"] > 0)
    T[u"母数の型ごとの帯の中の行"] = collections.OrderedDict((k, sum(1 for r in pop if r[u"型ごとの候補の数"][k] > 0)) for k in TYPES)
    T[u"保留の候補の数の分布"] = _cnt(min(r[u"候補の数"], 21) for r in pop if r[u"判定"] == u"保留")
    T[u"保留で候補の型に D1 を含む"] = sum(1 for r in pop if r[u"判定"] == u"保留" and r[u"型ごとの候補の数"][u"D1"] > 0)
    T[u"母数の判定 × state"] = collections.OrderedDict((v, _cnt(r[u"state"] for r in pop if r[u"判定"] == v)) for v in VERDICTS)
    return T


def stage_of(e, G):
    return u"完全一致" if e == 0 else u"丸めの帯 H" if e <= G / 2.0 else u"丸めの帯 F" if e <= G else u"不一致"


def ref_unjudged(entry_claims, labels, texts, rows):
    u"""封 C-10 の数を entry と札から数え直す(行から数えない。単位 株 の 2 件は行にならないので、行から数えると 0 になる)。"""
    row_ids = set(r[u"id"] for r in rows)
    num = [c for c in entry_claims if c.get(u"kind") == "num" and c[u"id"] in labels]
    unj = [c for c in num if labels[c[u"id"]][u"札"] == u"判定不能"]
    return {
        u"札ありの num の主張(entry)": len(num), u"行になった num": len(rows),
        u"行にならなかった num の id と単位(単位が導出 6 型の対象外)": dict((c[u"id"], texts[c[u"id"]].get(u"単位")) for c in num if c[u"id"] not in row_ids),
        u"判定不能の num": len(unj), u"判定不能の num の id と単位": dict((c[u"id"], texts[c[u"id"]].get(u"単位")) for c in unj),
        u"判定不能の num のうち行になった": sum(1 for c in unj if c[u"id"] in row_ids),
        u"偽の num": sum(1 for c in num if labels[c[u"id"]][u"札"] == u"偽"),
        u"偽の text(母数外)": sum(1 for c in entry_claims if c[u"id"] in labels and labels[c[u"id"]][u"札"] == u"偽" and c.get(u"kind") != "num"),
    }


def ref_d4_opportunities(facts, arcs):
    u"""D4 の余地を Index を使わずに数え直す: 親 × 金額の context で子の fact が 2 つ以上そろう組と、そのうち親の fact が無い組。"""
    have = set((f[u"name"], f[u"context"]) for f in facts if f[u"unit"] == "JPY")
    ctxs = sorted(set(f[u"context"] for f in facts if f[u"unit"] == "JPY"))
    pairs = without = 0
    for parent, children in arcs.items():
        for ctx in ctxs:
            if sum(1 for ch in children if (ch, ctx) in have) >= 2:
                pairs += 1
                if (parent, ctx) not in have:
                    without += 1
    return {u"子が 2 つ以上そろう親 × context": pairs, u"そのうち親の fact が無い組(D4 が候補を作れる組)": without}


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(C-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    return {
        u"C-1": [u"%s%%" % T[u"対照の割合"], u"%s%%" % T[u"対照の割合(型を問わず)"]],
        u"C-2": [u"%d" % T[u"母数のうち D1 が帯の中"]], u"C-3": [u"%d" % T[u"母数の判定"][u"導出一致"]],
        u"C-4": [u"%d" % T[u"母数の判定"][u"不一致"]], u"C-5": [u"%d" % T[u"母数の判定"][u"保留"]],
        u"C-6": [u"%s(%d)" % list(T[u"導出一致の型(D1 以外)"].items())[0]] if T[u"導出一致の型(D1 以外)"] else [u"無い"],
        u"C-7": [u"%d" % T[u"% のうち D3 か D5 が帯の中"]],
        u"C-8": [u"%s%%(%d / %d)" % (T[u"導出一致で根拠に要素名の割合"], T[u"導出一致で根拠に要素名"], T[u"母数の判定"][u"導出一致"])],
        u"C-9": [u"%d" % T[u"円 のうち D6 が帯の中"]],
        u"C-10": [u"判定不能 %d" % T[u"判定不能の num"], u"偽 %d" % T[u"偽の num"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が C-1〜C-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"C-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"C-2", u"C-3", u"C-4", u"C-5", u"C-7", u"C-9") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    for s in (u"導出一致 %d" % T[u"母数の判定"][u"導出一致"], u"保留 %d" % T[u"母数の判定"][u"保留"], u"不一致 %d" % T[u"母数の判定"][u"不一致"]):
        if s not in doc:
            p.append(u"文書に %s が無い" % s)
    W = rec[u"配線の門"][u"(f) fact の読み取り"]
    for s in (u"ix:nonFraction %d" % W[u"ix:nonFraction の数"], u"nil・空 %d" % W[u"nil・空"], u"fact %d" % W[u"重複を除いた fact"], u"context %d" % W[u"context の数"],
              u"arc %d" % rec[u"配線の門"][u"(f) 計算リンクの arc"]):
        if s not in doc:
            p.append(u"2-1 に %s が無い" % s)
    byt = u"・".join(u"%s %d" % (k, v) for k, v in T[u"母数の型ごとの帯の中の行"].items())
    if byt not in doc:
        p.append(u"2-2 の型ごとの行が記録の順と数でない")
    D4 = rec[u"配線の門"][u"(f) D4 の余地"]
    for s in (u"子の fact が 2 つ以上そろう組は %d 組" % D4[u"子が 2 つ以上そろう親 × context"],
              u"親の fact が無い組(封 §2 の D4 が候補を作る条件)は %d 組" % D4[u"そのうち親の fact が無い組(D4 が候補を作れる組)"]):
        if s not in doc:
            p.append(u"2-2 に %s が無い" % s)
    for i in T[u"判定不能の num の id と単位"]:
        if i not in doc:
            p.append(u"C-10 に判定不能の num の id %s が無い" % i)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"C-\d+|D\d|P\d+|§\d+(-\d+)*", u" ", s)
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
    for bad in ("adapters", "audit_core", "urllib", "http", "socket"):
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
    spec = importlib.util.spec_from_file_location("derivation_full_under_test", SCRIPT)
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
        cls.mod = load_script()

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertTrue(W[u"(d) 母数が 53"] and W[u"(e) 対照が 249"])
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(self.rec_text.count("scratchpad"), 0)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_a_3_fact_count_reparsed_with_own_regex(self):
        u"""記録の ix:nonFraction の数を、門が自分の正規表現で数え直す。"""
        z = zipfile.ZipFile(os.path.join(ROOT, self.mod.MATERIALS[u"zip"][0]))
        n = 0
        for nm in z.namelist():
            if nm.endswith("_ixbrl.htm") and "/PublicDoc/" in nm:
                n += len(re.findall(r"<ix:nonFraction\b", z.read(nm).decode("utf-8", "replace")))
        self.assertEqual(n, self.rec[u"配線の門"][u"(f) fact の読み取り"][u"ix:nonFraction の数"])

    def test_b_1_rows_recomputed_by_the_script(self):
        u"""script の読み取りと build_rows を呼び直し、記録の行と一致させる(材料は repo の 4 file)。"""
        m = self.mod
        zpath = os.path.join(ROOT, m.MATERIALS[u"zip"][0])
        facts, counts = m.parse_facts(zpath)
        arcs, n_arcs = m.parse_cal(zpath)
        self.assertEqual(json.loads(json.dumps(counts, ensure_ascii=False)), self.rec[u"配線の門"][u"(f) fact の読み取り"])
        self.assertEqual(n_arcs, self.rec[u"配線の門"][u"(f) 計算リンクの arc"])
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"labels"][0]))[u"labels"]}
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"claims"][0]))[u"claims"]}
        entry = jload(os.path.join(ROOT, m.MATERIALS[u"entry"][0]))
        rows = m.build_rows(entry[u"claims"], labels, texts, m.Index(facts, arcs))
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(m.judge(m.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_candidates_stage_and_pairs_recomputed(self):
        for r in self.rec[u"行"]:
            t = r[u"t'"]
            self.assertEqual(sum(r[u"型ごとの候補の数"].values()), r[u"候補の数"])
            self.assertEqual(r[u"判定"], u"導出一致" if r[u"候補の数"] == 1 else u"保留" if r[u"候補の数"] >= 2 else u"不一致")
            self.assertEqual(r[u"候補が 20 を超えた"], r[u"候補の数"] > 20)
            self.assertEqual(len(r[u"候補"]), min(r[u"候補の数"], 20))
            for c in r[u"候補"]:
                self.assertAlmostEqual(c[u"e"], abs(abs(c[u"v"]) - t), places=6)
                self.assertEqual(stage_of(c[u"e"], c[u"G"]), c[u"段"])
                self.assertIn(c[u"段"], IN_BAND)
                if c[u"型"] in (u"D2", u"D3"):
                    self.assertEqual(c[u"fact"][0][u"name"], c[u"fact"][1][u"name"])
                    self.assertNotEqual(c[u"fact"][0][u"context"], c[u"fact"][1][u"context"], u"同じ fact の差")
                if c[u"型"] == u"D5":
                    self.assertEqual(c[u"fact"][0][u"context"], c[u"fact"][1][u"context"])
                if c[u"型"] == u"D4":
                    self.assertGreaterEqual(len(c[u"fact"]), 2)
            self.assertEqual(r[u"母数"], r[u"札"] == u"真" and r[u"state"] != "GROUNDED")
            self.assertEqual(r[u"対照"], r[u"札"] == u"真" and r[u"state"] == "GROUNDED")

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)

    def test_b_4_unjudged_counted_from_entry_and_labels_not_from_rows(self):
        u"""封 C-10 の数(判定不能・偽の num)を entry と札から数え直す。最初の記録は行から数えて 0 と誤った(監査で見つかった)。"""
        m = self.mod
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"labels"][0]))[u"labels"]}
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"claims"][0]))[u"claims"]}
        entry = jload(os.path.join(ROOT, m.MATERIALS[u"entry"][0]))
        U = ref_unjudged(entry[u"claims"], labels, texts, self.rec[u"行"])
        for k, v in U.items():
            self.assertEqual(self.rec[u"集計"][k], v, k)
        self.assertEqual(U[u"判定不能の num"], len(U[u"判定不能の num の id と単位"]))
        self.assertGreater(U[u"判定不能の num"], 0, u"封 §3 C-10 は判定不能の num を 2 件と数えている")
        self.assertEqual(U[u"行になった num"] + len(U[u"行にならなかった num の id と単位(単位が導出 6 型の対象外)"]), U[u"札ありの num の主張(entry)"])
        for i, unit in U[u"行にならなかった num の id と単位(単位が導出 6 型の対象外)"].items():
            self.assertNotIn(unit, list(m.UNIT_SCALE) + list(m.RATIO_UNITS) + list(m.COUNT_UNITS), i)

    def test_b_5_d4_had_no_room_in_this_instance(self):
        u"""D4 が 0 行なのは「当たらなかった」ではなく「親の fact が無い組が 0 で候補を作れなかった」ことを、Index を使わずに数え直す。"""
        m = self.mod
        zpath = os.path.join(ROOT, m.MATERIALS[u"zip"][0])
        facts, _ = m.parse_facts(zpath)
        arcs, _ = m.parse_cal(zpath)
        D4 = ref_d4_opportunities(facts, arcs)
        self.assertEqual(dict(self.rec[u"配線の門"][u"(f) D4 の余地"]), D4)
        self.assertGreater(D4[u"子が 2 つ以上そろう親 × context"], 0)
        if D4[u"そのうち親の fact が無い組(D4 が候補を作れる組)"] == 0:
            self.assertEqual(self.rec[u"集計"][u"母数の型ごとの帯の中の行"][u"D4"], 0)
            self.assertEqual(sum(r[u"型ごとの候補の数"][u"D4"] for r in self.rec[u"行"]), 0)

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"C-1": 95, u"C-2": (10, 25), u"C-3": (15, 35), u"C-4": (8, 25), u"C-5": (5, 20), u"C-7": (3, 5), u"C-8": 60, u"C-9": (5, 20)})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_is_stdlib_only_and_each_type_fires_on_synthetic_facts(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m = self.mod
        self.assertEqual(m.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        F = lambda name, ctx, unit, val, g: {u"name": name, u"context": ctx, u"unit": unit, u"value": val, u"g": g}
        facts = [F(u"a:Sales", u"CY", "JPY", 38064e6, 1e6), F(u"a:Sales", u"PY", "JPY", 36975e6, 1e6), F(u"a:Profit", u"CY", "JPY", 945e6, 1e6),
                 F(u"a:Shares", u"CY", "shares", 8420000.0, 1.0), F(u"a:Ratio", u"CY", "pure", 0.185, 0.001), F(u"a:X", u"CY", "JPY", 300e6, 1e6), F(u"a:Y", u"CY", "JPY", 210e6, 1e6)]
        arcs = {u"a:Parent": {u"a:X": 1.0, u"a:Y": 1.0}}
        idx = m.Index(facts, arcs)
        def types(unit, value, u):
            cands, _, _ = m.derive({u"unit": unit, u"value": value, u"u": u}, idx)
            return sorted(set(c[u"型"] for c in cands))
        self.assertIn(u"D1", types(u"百万円", 38064.0, 1e6))                       # 単一
        self.assertIn(u"D2", types(u"百万円", 1089.0, 1e6))                        # 差 38064 − 36975
        self.assertIn(u"D3", types(u"%", 2.9, 0.1))                               # 増減率
        self.assertIn(u"D4", types(u"百万円", 510.0, 1e6))                         # 合算 300 + 210(親の fact 無し)
        self.assertIn(u"D5", types(u"%", 2.5, 0.1))                               # 比率 945 / 38064
        self.assertIn(u"D6", types(u"円", 112.0, 1.0))                            # 一株あたり 945e6 / 8.42e6 = 112.2
        self.assertIn(u"D1", types(u"%", 18.5, 0.1))                              # pure × 100
        # 文の最下位の桁(文から読む)
        self.assertEqual(m.written_granularity(u"当期純利益は945百万円(同50.8%減)", 945000000.0, u"円"), (1e6, True))
        self.assertEqual(m.written_granularity(u"営業利益は1,465百万円(同46.0%減)", -46.0, u"%"), (0.1, True))
        self.assertEqual(m.written_granularity(u"従業員は1,447名", 1447.0, u"名"), (1.0, True))

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
        rec[u"予測の判定"][u"C-3"] = u"当たり"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"母数の判定"][u"保留"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"母数の判定"], rec[u"集計"][u"母数の判定"])

    def test_m_3_changing_a_row_verdict_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"判定"] == u"保留"][0]
        r[u"判定"] = u"導出一致"
        self.assertNotEqual(u"導出一致" if r[u"候補の数"] == 1 else u"保留" if r[u"候補の数"] >= 2 else u"不一致", r[u"判定"])

    def test_m_4_changing_a_candidate_stage_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"候補の数"] >= 1][0]
        c = r[u"候補"][0]
        c[u"G"] = c[u"e"] / 10.0 if c[u"e"] > 0 else 0.0
        c[u"e"] = c[u"G"] * 5 + 1
        self.assertNotEqual(stage_of(c[u"e"], c[u"G"]), c[u"段"])

    def test_m_5_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_doc_number_change_is_caught(self):
        n = self.rec[u"集計"][u"母数の判定"][u"保留"]
        bad = self.doc.replace(u"| %d |" % n, u"| %d |" % (n + 1))
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_7_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**5〜20**", u"**5〜50**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_8_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_9_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])

    def test_m_10_unjudged_count_reset_to_zero_is_caught(self):
        u"""最初の記録の誤り(判定不能の num 0)を再現すると、文書の表(C-10)との照合と、entry からの数え直しの両方が赤くなる。"""
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"判定不能の num"] = 0
        self.assertNotEqual(table_problems(self.doc, rec), [])
        self.assertNotEqual(rec[u"集計"][u"判定不能の num"], len(rec[u"集計"][u"判定不能の num の id と単位"]))

    def test_m_11_d4_room_change_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"配線の門"][u"(f) D4 の余地"][u"そのうち親の fact が無い組(D4 が候補を作れる組)"] += 1
        self.assertNotEqual(table_problems(self.doc, rec), [])


if __name__ == "__main__":
    unittest.main()
