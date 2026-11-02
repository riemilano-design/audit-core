# -*- coding: utf-8 -*-
u"""門: 主語の制約つきの導出(封 docs/XBRL_DERIVATION_SUBJECT_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_subject_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 E-1〜E-10 を、記録の集計と封 §3 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 集計を行から数え直す。手がかり(A1・A2・A3)と近傍 N を門自身の code で entry と計算リンクから作り直し、記録の S・N と一致させる。
- 前の便の script の derive を呼び、門自身の「残す条件」で絞った候補の数が記録と一致すること。script の build_rows の呼び直し。
- 文書の表の実測の欄・遷移表・散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
- script が標準ライブラリ + 前の便の script(importlib)だけで engine を import しない。順序(封 < script・記録・文書・門)。変異で赤くなる。
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

SEAL_REL = "docs/XBRL_DERIVATION_SUBJECT_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_SUBJECT_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_subject_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_subject_2026-11-02.py"
PREV_SCRIPT_REL = "measure/xbrl_derivation_full_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation_subject.py"
SEAL_COMMIT_SHORT = "ab09aa6"
SEAL, DOC, REC, SCRIPT, PREV_SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL, PREV_SCRIPT_REL))

IDS = tuple(u"E-%d" % i for i in range(1, 11))
VERDICTS = (u"導出一致", u"保留", u"不一致")
NO_CLUE = u"手がかりなし"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "__future__"}
FORBIDDEN = (u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")
WINDOW, NEIGHBOURS = 12, 3


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封 §3 の幅

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(E-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"E-1", u"E-2", u"E-3", u"E-4", u"E-5", u"E-8", u"E-9"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    for i in (u"E-6", u"E-7"):
        b[i] = int(re.search(r"\*\*(\d+)% 以上\*\*", rows[i][0]).group(1))
    return b


# ---------------------------------------------------------------- 求め直し

def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"E-1"] = b[u"E-1"][0] <= T[u"手がかりありの判定"][u"導出一致"] <= b[u"E-1"][1]
    J[u"E-2"] = b[u"E-2"][0] <= T[u"手がかりありの判定"][u"保留"] <= b[u"E-2"][1]
    J[u"E-3"] = b[u"E-3"][0] <= T[u"手がかりありの判定"][u"不一致"] <= b[u"E-3"][1]
    J[u"E-4"] = b[u"E-4"][0] <= T[u"全探索で保留のうち制約で導出一致"] <= b[u"E-4"][1]
    J[u"E-5"] = b[u"E-5"][0] <= T[u"全探索で導出一致のうち同じ候補で導出一致"] <= b[u"E-5"][1]
    J[u"E-6"] = T[u"導出一致で根拠に要素名の割合"] is not None and T[u"導出一致で根拠に要素名の割合"] >= b[u"E-6"]
    J[u"E-7"] = T[u"対照の割合(型を問わず)"] is not None and T[u"対照の割合(型を問わず)"] >= b[u"E-7"]
    J[u"E-8"] = b[u"E-8"][0] <= T[u"% のうち導出一致"] <= b[u"E-8"][1]
    J[u"E-9"] = b[u"E-9"][0] <= T[u"全探索で候補 20 超のうち制約後 3 以下"] <= b[u"E-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"E-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"母数"]]
    ctl = [r for r in rows if r[u"対照"]]
    clue = [r for r in pop if r[u"手がかりあり"]]
    none = [r for r in pop if not r[u"手がかりあり"]]
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(none)
    T[u"手がかりの出所"] = _cnt(r[u"手がかりの出所"] for r in pop)
    T[u"手がかりなしの全探索の判定"] = _cnt(r[u"全探索の判定"] for r in none)
    T[u"手がかりありの判定"] = collections.OrderedDict((v, sum(1 for r in clue if r[u"判定"] == v)) for v in VERDICTS)
    T[u"遷移(全探索 → 制約つき。手がかりあり)"] = collections.OrderedDict(
        (u"%s → %s" % (a, b), sum(1 for r in clue if r[u"全探索の判定"] == a and r[u"判定"] == b)) for a in VERDICTS for b in VERDICTS)
    held = [r for r in clue if r[u"全探索の判定"] == u"保留"]
    T[u"全探索で保留(手がかりあり)"] = len(held)
    T[u"全探索で保留のうち制約で導出一致"] = sum(1 for r in held if r[u"判定"] == u"導出一致")
    was_one = [r for r in clue if r[u"全探索の判定"] == u"導出一致"]
    T[u"全探索で導出一致(手がかりあり)"] = len(was_one)
    T[u"全探索で導出一致のうち同じ候補で導出一致"] = sum(1 for r in was_one if r[u"全探索の導出一致と同じ候補"] is True)
    T[u"全探索で導出一致のうち制約で不一致"] = sum(1 for r in was_one if r[u"判定"] == u"不一致")
    one = [r for r in clue if r[u"判定"] == u"導出一致"]
    T[u"導出一致で根拠に要素名"] = sum(1 for r in one if r[u"根拠に要素名"])
    T[u"導出一致で根拠に要素名の割合"] = pct(T[u"導出一致で根拠に要素名"], len(one))
    T[u"導出一致で根拠に候補の fact の値(参考)"] = sum(1 for r in one if r[u"根拠に候補の fact の値"])
    T[u"導出一致で根拠に要素名か値のどちらか(参考)"] = sum(1 for r in one if r[u"根拠に要素名"] or r[u"根拠に候補の fact の値"])
    T[u"保留の候補の数の分布"] = _cnt(min(r[u"制約つきの候補の数"], 21) for r in clue if r[u"判定"] == u"保留")
    T[u"対照のうち D1 に recomputed の値が在る"] = sum(1 for r in ctl if r[u"D1 に recomputed の値が在る"])
    T[u"対照のうち どの型かに recomputed の値が在る"] = sum(1 for r in ctl if r[u"どの型かに recomputed の値が在る"])
    T[u"対照の割合(型を問わず)"] = pct(T[u"対照のうち どの型かに recomputed の値が在る"], len(ctl))
    T[u"対照の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"判定"] == v)) for v in VERDICTS + (NO_CLUE,))
    pc = [r for r in clue if r[u"unit"] == u"%"]
    T[u"% の手がかりあり"] = len(pc)
    T[u"% のうち導出一致"] = sum(1 for r in pc if r[u"判定"] == u"導出一致")
    many = [r for r in clue if r[u"全探索の候補の数"] > 20]
    T[u"全探索で候補 20 超(手がかりあり)"] = len(many)
    T[u"全探索で候補 20 超のうち制約後 3 以下"] = sum(1 for r in many if r[u"制約つきの候補の数"] <= 3)
    return T


# ---------------------------------------------------------------- 門自身の手がかり・近傍・残す条件(script とは別に書く)

def ref_elems(pointers):
    out = []
    for p in pointers or []:
        if isinstance(p, str) and p.startswith("xbrl:") and "@" in p:
            e = p[5:].split("@")[0]
            if e not in out:
                out.append(e)
    return out


def ref_overlap(a, b):
    a, b = a or u"", b or u""
    return len(a) >= WINDOW and len(b) >= WINDOW and (a[:WINDOW] in b or a[-WINDOW:] in b or b[:WINDOW] in a or b[-WINDOW:] in a)


def ref_anchors(cid, entry_claims, texts, use_a2):
    pos = {c[u"id"]: i for i, c in enumerate(entry_claims)}
    i = pos[cid]
    c = entry_claims[i]
    a1 = ref_elems(c.get(u"pointers"))
    a2 = []
    if use_a2 and not a1 and c.get(u"subject"):
        for o in entry_claims:
            if o.get(u"subject") == c[u"subject"]:
                for e in ref_elems(o.get(u"pointers")):
                    if e not in a2:
                        a2.append(e)
    a3 = []
    for j in range(max(0, i - NEIGHBOURS), min(len(entry_claims), i + NEIGHBOURS + 1)):
        o = entry_claims[j]
        if j != i and o.get(u"kind") == "num" and ref_overlap(texts[cid].get(u"文"), (texts.get(o[u"id"]) or {}).get(u"文")):
            for e in ref_elems(o.get(u"pointers")):
                if e not in a3:
                    a3.append(e)
    S = []
    for e in a1 + a2 + a3:
        if e not in S:
            S.append(e)
    return {u"A1": a1, u"A2": a2, u"A3": a3}, S


def ref_neighbourhood(S, arcs):
    N = set(S)
    for s in S:
        for p, ch in arcs.items():
            if s in ch:
                N.add(p)
                N.update(ch.keys())
        N.update(arcs.get(s, {}).keys())
    return N


def ref_keep(c, N):
    names = [f[u"name"] for f in c[u"fact"]]
    if c[u"型"] in (u"D1", u"D2", u"D3", u"D6"):
        return names[0] in N
    if c[u"型"] == u"D4":
        return c.get(u"親") in N or all(n in N for n in names)
    return names[0] in N and names[1] in N


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(E-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    return {
        u"E-1": [u"%d" % T[u"手がかりありの判定"][u"導出一致"]], u"E-2": [u"%d" % T[u"手がかりありの判定"][u"保留"]],
        u"E-3": [u"%d" % T[u"手がかりありの判定"][u"不一致"]], u"E-4": [u"%d" % T[u"全探索で保留のうち制約で導出一致"]],
        u"E-5": [u"%d(不一致に落ちたのが %d)" % (T[u"全探索で導出一致のうち同じ候補で導出一致"], T[u"全探索で導出一致のうち制約で不一致"])],
        u"E-6": [u"%s%%(%d / %d)" % (T[u"導出一致で根拠に要素名の割合"], T[u"導出一致で根拠に要素名"], T[u"手がかりありの判定"][u"導出一致"])],
        u"E-7": [u"%s%%" % T[u"対照の割合(型を問わず)"]],
        u"E-8": [u"%d" % T[u"% のうち導出一致"]], u"E-9": [u"%d" % T[u"全探索で候補 20 超のうち制約後 3 以下"]],
        u"E-10": [u"手がかりなし %d" % T[u"手がかりなし"], u"保留 %d" % T[u"手がかりなしの全探索の判定"].get(u"保留", 0),
                  u"導出一致 %d" % T[u"手がかりなしの全探索の判定"].get(u"導出一致", 0), u"判定不能 %d" % T[u"判定不能の num"], u"偽 %d" % T[u"偽の num"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が E-1〜E-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"E-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"E-1", u"E-2", u"E-3", u"E-4", u"E-5", u"E-8", u"E-9") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    for s in (u"導出一致 %d・保留 %d・不一致 %d" % tuple(T[u"手がかりありの判定"][v] for v in VERDICTS),
              u"手がかりあり %d・なし %d" % (T[u"手がかりあり"], T[u"手がかりなし"]),
              u"A1(自身の pointer)%d・A2(同じ主語の字に engine が結んだ要素)%d・A3(隣の主張の pointer)%d" % tuple(T[u"手がかりの出所"].get(k, 0) for k in (u"A1", u"A2", u"A3")),
              u"全探索の候補の数が前の便の記録と一致した行 %d / %d" % (T[u"全探索の候補の数が前の便の記録と一致した行"], len(rec[u"行"])),
              u"導出一致 %d・保留 %d・不一致 %d で、GROUNDED" % tuple(T[u"対照の判定"][v] for v in VERDICTS),
              u"D1 で %d" % T[u"対照のうち D1 に recomputed の値が在る"],
              u"%d / %d(%s%%。E-6 外れ)" % (T[u"導出一致で根拠に要素名"], T[u"手がかりありの判定"][u"導出一致"], T[u"導出一致で根拠に要素名の割合"]),
              u"では %d / %d。名か値のどちらかでは %d / %d" % (T[u"導出一致で根拠に候補の fact の値(参考)"], T[u"手がかりありの判定"][u"導出一致"],
                                                        T[u"導出一致で根拠に要素名か値のどちらか(参考)"], T[u"手がかりありの判定"][u"導出一致"])):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    tr = T[u"遷移(全探索 → 制約つき。手がかりあり)"]
    for a in VERDICTS:
        line = u"| %s(%d) | %d | %d | %d |" % (a, sum(tr[u"%s → %s" % (a, b)] for b in VERDICTS), tr[u"%s → 導出一致" % a], tr[u"%s → 保留" % a], tr[u"%s → 不一致" % a])
        if line not in doc:
            p.append(u"遷移表の行 %s" % line)
    for s in (u"**保留 → 導出一致 %d**" % tr[u"保留 → 導出一致"], u"**導出一致 → 不一致 %d**" % tr[u"導出一致 → 不一致"], u"**保留 → 不一致 %d**" % tr[u"保留 → 不一致"]):
        if s not in doc:
            p.append(u"2-3 に %s が無い" % s)
    for i in T[u"導出一致の id と候補の要素"]:
        if i not in doc:
            p.append(u"導出一致の id %s が文書に無い" % i)
    for i in T[u"不一致の id と全探索の候補の数"]:
        if i not in doc:
            p.append(u"不一致の id %s が文書に無い" % i)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"E-\d+|C-\d+|D\d|P\d+|§\d+(-\d+)*", u" ", s)
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
    for bad in ("adapters", "audit_core", "core", "urllib", "http", "socket"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    files = re.findall(r"spec_from_file_location\([^,]+,\s*([^)]*)\)", src)
    for f in files:
        if "prev_script" not in f:
            p.append(u"importlib で読む file が前の便の script でない: %s" % f)
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


# ================================================================ tests

class RecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)
        cls.mod = load(SCRIPT, "derivation_subject_under_test")
        cls.prev = load(PREV_SCRIPT, "derivation_full_for_subject_gate")

    def materials(self):
        m = self.mod
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"claims"][0]))[u"claims"]}
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"labels"][0]))[u"labels"]}
        entry = jload(os.path.join(ROOT, m.MATERIALS[u"entry"][0]))
        prev_rec = jload(os.path.join(ROOT, m.MATERIALS[u"prev_rec"][0]))
        zpath = os.path.join(ROOT, m.MATERIALS[u"zip"][0])
        facts, _ = self.prev.parse_facts(zpath)
        arcs, _ = self.prev.parse_cal(zpath)
        return texts, labels, entry, prev_rec, facts, arcs

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertTrue(W[u"(f) 手がかりあり 34・なし 19(封 §1 の層)"])
        self.assertEqual(W[u"(e) 全探索の候補の数が前の便の記録と一致した行"], len(self.rec[u"行"]))
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertIn(PREV_SCRIPT_REL, self.rec[u"読んだ材料の sha256"])
        self.assertEqual(self.rec_text.count("scratchpad"), 0)
        self.assertEqual(self.mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_a_3_seal_strata_match_the_record(self):
        u"""封 §1 の層(手がかりあり 34 / なし 19、A1 23・A2 7・A3 4、全探索の判定の内訳)が記録と合う。"""
        T = self.rec[u"集計"]
        seal = self.seal
        self.assertIn(u"| 手がかりあり | **%d**(A1 %d・A2 %d・A3 %d" % (T[u"手がかりあり"], T[u"手がかりの出所"][u"A1"], T[u"手がかりの出所"][u"A2"], T[u"手がかりの出所"][u"A3"]), seal)
        self.assertIn(u"| 手がかりなし | **%d** | 導出一致 %d・保留 %d |" % (T[u"手がかりなし"], T[u"手がかりなしの全探索の判定"][u"導出一致"], T[u"手がかりなしの全探索の判定"][u"保留"]), seal)
        clue_prev = collections.Counter(r[u"全探索の判定"] for r in self.rec[u"行"] if r[u"母数"] and r[u"手がかりあり"])
        self.assertIn(u"導出一致 %d・保留 %d・不一致 %d |" % (clue_prev[u"導出一致"], clue_prev[u"保留"], clue_prev[u"不一致"]), seal)
        self.assertIn(u"候補が 20 を超えた行は **%d**" % T[u"全探索で候補 20 超(手がかりあり)"], seal)

    def test_b_1_rows_recomputed_by_the_script(self):
        texts, labels, entry, prev_rec, facts, arcs = self.materials()
        rows = self.mod.build_rows(self.prev, prev_rec[u"行"], entry[u"claims"], labels, texts, self.prev.Index(facts, arcs))
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        T = self.mod.tally(rows)
        self.assertEqual(json.loads(json.dumps(self.mod.judge(T), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_anchors_neighbourhood_and_kept_candidates_recomputed_by_the_gate(self):
        u"""手がかり・近傍・残す条件を門自身の code で作り直し、全行の S・N・制約つきの候補の数を記録と一致させる(候補は前の便の derive)。"""
        texts, labels, entry, prev_rec, facts, arcs = self.materials()
        idx = self.prev.Index(facts, arcs)
        prev_rows = {r[u"id"]: r for r in prev_rec[u"行"]}
        for r in self.rec[u"行"]:
            A, S = ref_anchors(r[u"id"], entry[u"claims"], texts, use_a2=bool(r[u"母数"]))
            self.assertEqual(dict(r[u"手がかり"]), A, r[u"id"])
            self.assertEqual(r[u"S"], S, r[u"id"])
            self.assertEqual(r[u"手がかりあり"], bool(S))
            N = ref_neighbourhood(S, arcs)
            self.assertEqual(set(r[u"N"]), N, r[u"id"])
            self.assertEqual(r[u"N の大きさ"], len(N))
            tx = texts[r[u"id"]]
            u0, _ = self.prev.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
            cands, _, _ = self.prev.derive({u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}, idx)
            self.assertEqual(len(cands), prev_rows[r[u"id"]][u"候補の数"], r[u"id"])
            kept = [c for c in cands if ref_keep(c, N)] if S else []
            self.assertEqual(len(kept), r[u"制約つきの候補の数"], r[u"id"])
            self.assertEqual(r[u"判定"], (u"導出一致" if len(kept) == 1 else u"保留" if len(kept) >= 2 else u"不一致") if S else NO_CLUE)
            self.assertEqual(r[u"全探索の判定"], prev_rows[r[u"id"]][u"判定"])
            for c in r[u"候補"]:
                self.assertTrue(ref_keep(c, N), u"%s の候補が N の外" % r[u"id"])
            self.assertEqual(sum(r[u"型ごとの候補の数"].values()), r[u"制約つきの候補の数"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)

    def test_b_4_grounds_value_reference_recomputed(self):
        u"""参考の欄「根拠に候補の fact の値」を、札と fact から数え直す。"""
        texts, labels, entry, prev_rec, facts, arcs = self.materials()
        val = {(f[u"name"], f[u"context"], f[u"unit"]): f[u"value"] for f in facts}
        for r in self.rec[u"行"]:
            if r[u"判定"] != u"導出一致":
                self.assertIsNone(r[u"根拠に候補の fact の値"])
                continue
            g = labels[r[u"id"]].get(u"根拠") or u""
            want = all(u"{:,}".format(int(abs(val[(f[u"name"], f[u"context"], f[u"unit"])]))) in g for f in r[u"候補"][0][u"fact"])
            self.assertEqual(r[u"根拠に候補の fact の値"], want, r[u"id"])

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)
        self.assertEqual(dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items()), dict(self.bounds), u"script の幅が封の字と違う")

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"E-1": (14, 24), u"E-2": (4, 12), u"E-3": (3, 10), u"E-4": (10, 18), u"E-5": (6, 8), u"E-6": 70, u"E-7": 90, u"E-8": (1, 3), u"E-9": (5, 7)})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_imports_and_constraint_on_synthetic_facts(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m = self.mod
        arcs = {u"a:Parent": {u"a:X": 1.0, u"a:Y": 1.0}, u"a:Top": {u"a:Parent": 1.0, u"a:Z": 1.0}}
        N = m.neighbourhood([u"a:X"], arcs)
        self.assertEqual(set(N), {u"a:X", u"a:Parent", u"a:Y"})                      # 親・兄弟。祖父(Top)と叔父(Z)は深さ 2 で入らない
        self.assertEqual(set(m.neighbourhood([u"a:Parent"], arcs)), {u"a:Parent", u"a:Top", u"a:Z", u"a:X", u"a:Y"})
        self.assertEqual(m.neighbourhood([u"a:Lonely"], arcs), [u"a:Lonely"])
        F = lambda names: {u"型": None, u"fact": [{u"name": n, u"context": u"CY", u"unit": "JPY"} for n in names]}
        c = F([u"a:X"]); c[u"型"] = u"D1"
        self.assertTrue(m.keep(c, N)) and self.assertFalse(m.keep(c, [u"a:Z"]))
        c = F([u"a:X", u"a:Y"]); c[u"型"] = u"D5"
        self.assertTrue(m.keep(c, N))
        self.assertFalse(m.keep(c, [u"a:X"]))                                        # D5 は両方
        c = F([u"a:X", u"a:Shares"]); c[u"型"] = u"D6"
        self.assertTrue(m.keep(c, [u"a:X"]))                                         # D6 は金額だけ
        c = F([u"a:X", u"a:Y"]); c[u"型"] = u"D4"; c[u"親"] = u"a:Parent"
        self.assertTrue(m.keep(c, [u"a:Parent"])) and self.assertFalse(m.keep(c, [u"a:X"]))
        self.assertEqual(m.elems_of([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"formula:a-b", u"builtin:sign(cur-prior)", u"xbrl:jppfs_cor:NetSales@Prior1YearDuration"]), [u"jppfs_cor:NetSales"])
        self.assertTrue(m.window_overlap(u"売上高の伸び率2.9%を大きく上回る原価の", u"となった結果、売上高の伸び率2.9%を大きく"))
        self.assertFalse(m.window_overlap(u"短い", u"短い文"))

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
        rec[u"予測の判定"][u"E-3"] = u"当たり"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"手がかりありの判定"][u"不一致"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"手がかりありの判定"], rec[u"集計"][u"手がかりありの判定"])

    def test_m_3_moving_a_row_verdict_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"判定"] == u"不一致" and x[u"母数"]][0]
        r[u"判定"] = u"導出一致"
        self.assertNotEqual(u"導出一致" if r[u"制約つきの候補の数"] == 1 else u"保留" if r[u"制約つきの候補の数"] >= 2 else u"不一致", r[u"判定"])

    def test_m_4_widening_the_neighbourhood_in_the_record_is_caught(self):
        u"""N に要素を 1 つ足した記録は、門の近傍の作り直しと合わない。"""
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"手がかりあり"]][0]
        zpath = os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")
        prev = load(PREV_SCRIPT, "derivation_full_for_mutation")
        arcs, _ = prev.parse_cal(zpath)
        self.assertEqual(set(r[u"N"]), ref_neighbourhood(r[u"S"], arcs))
        r[u"N"].append(u"jppfs_cor:NotInTheNeighbourhood")
        self.assertNotEqual(set(r[u"N"]), ref_neighbourhood(r[u"S"], arcs))

    def test_m_5_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_doc_transition_number_change_is_caught(self):
        n = self.rec[u"集計"][u"遷移(全探索 → 制約つき。手がかりあり)"][u"保留 → 導出一致"]
        bad = self.doc.replace(u"**保留 → 導出一致 %d**" % n, u"**保留 → 導出一致 %d**" % (n + 1))
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_7_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**3〜10**", u"**3〜20**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_8_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_9_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT).replace(u'MATERIALS[u"prev_script"][0]', u'"core/engine.py"')), [])

    def test_m_10_dropping_the_d5_both_sides_rule_is_caught(self):
        u"""D5 を「片方で残す」に緩めると、記録の制約つきの候補の数と合わなくなる行が在る(% の行)。"""
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json"))[u"claims"]}
        prev = load(PREV_SCRIPT, "derivation_full_for_mutation_d5")
        zpath = os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")
        facts, _ = prev.parse_facts(zpath)
        arcs, _ = prev.parse_cal(zpath)
        idx = prev.Index(facts, arcs)
        changed = 0
        for r in self.rec[u"行"]:
            if not (r[u"手がかりあり"] and r[u"unit"] == u"%"):
                continue
            tx = texts[r[u"id"]]
            u0, _ = prev.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
            cands, _, _ = prev.derive({u"unit": u"%", u"value": tx[u"数"], u"u": u0}, idx)
            N = set(r[u"N"])
            loose = [c for c in cands if ((c[u"fact"][0][u"name"] in N or c[u"fact"][1][u"name"] in N) if c[u"型"] == u"D5" else ref_keep(c, N))]
            if len(loose) != r[u"制約つきの候補の数"]:
                changed += 1
        self.assertGreater(changed, 0)


if __name__ == "__main__":
    unittest.main()
