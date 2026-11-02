# -*- coding: utf-8 -*-
u"""門: 近傍の深さ 2 と型 2 つ(D7 二項の和・D8 比率の差)(封 docs/XBRL_DERIVATION_DEPTH_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_depth_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 F-1〜F-10 を、記録の集計と封 §3 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 集計を行から数え直す。深さ 2 の近傍・D7・D8 を門自身の code で作り直し、全行・全条件の候補の数を記録と一致させる(6 型の候補は前々便の derive)。
- script の build_rows の呼び直し。合成の fact で D7・D8 が効くこと。K0 の判定は前の便の記録の判定と一致すること。
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

SEAL_REL = "docs/XBRL_DERIVATION_DEPTH_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_DEPTH_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_depth_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_depth_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation_depth.py"
SEAL_COMMIT_SHORT = "cb3ba0d"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"F-%d" % i for i in range(1, 11))
CONDITIONS = (u"K1", u"K2", u"K3")
VERDICTS = (u"導出一致", u"保留", u"不一致")
TYPES = (u"D1", u"D2", u"D3", u"D4", u"D5", u"D6", u"D7", u"D8")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "__future__"}
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


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封 §3 の幅

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(F-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"F-1", u"F-2", u"F-3", u"F-4", u"F-5", u"F-6", u"F-7"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    for i in (u"F-8", u"F-9"):
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
    J[u"F-1"] = b[u"F-1"][0] <= T[u"K0 の不一致のうち K1 で導出一致か保留"] <= b[u"F-1"][1]
    J[u"F-2"] = b[u"F-2"][0] <= T[u"K0 の導出一致のうち K1 で保留"] <= b[u"F-2"][1]
    J[u"F-3"] = b[u"F-3"][0] <= T[u"2 項の和の 5 行で K2 の D7 が帯の中"] <= b[u"F-3"][1]
    J[u"F-4"] = b[u"F-4"][0] <= T[u"ポイント 2 行で K2 の D8 の候補で導出一致"] <= b[u"F-4"][1]
    J[u"F-5"] = b[u"F-5"][0] <= T[u"K0 の導出一致のうち K2 で保留"] <= b[u"F-5"][1]
    J[u"F-6"] = b[u"F-6"][0] <= T[u"K3 の判定(手がかりあり)"][u"導出一致"] <= b[u"F-6"][1]
    J[u"F-7"] = b[u"F-7"][0] <= T[u"K3 の判定(手がかりあり)"][u"不一致"] <= b[u"F-7"][1]
    J[u"F-8"] = T[u"K3 の対照の割合(型を問わず)"] is not None and T[u"K3 の対照の割合(型を問わず)"] >= b[u"F-8"]
    J[u"F-9"] = T[u"K3 の導出一致で根拠に名か値の割合"] is not None and T[u"K3 の導出一致で根拠に名か値の割合"] >= b[u"F-9"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"F-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def ref_tally(rows, sum_ids, point_ids):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"母数"]]
    ctl = [r for r in rows if r[u"対照"]]
    clue = [r for r in pop if r[u"手がかりあり"]]
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(pop) - len(clue)
    T[u"K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in clue if r[u"K0 の判定"] == v)) for v in VERDICTS)
    for K in CONDITIONS:
        T[u"%s の判定(手がかりあり)" % K] = collections.OrderedDict((v, sum(1 for r in clue if r[K][u"判定"] == v)) for v in VERDICTS)
        T[u"%s の遷移(K0 → %s)" % (K, K)] = collections.OrderedDict(
            (u"%s → %s" % (a, b), sum(1 for r in clue if r[u"K0 の判定"] == a and r[K][u"判定"] == b)) for a in VERDICTS for b in VERDICTS)
        T[u"%s の型ごとの帯の中の行(手がかりあり)" % K] = collections.OrderedDict((k, sum(1 for r in clue if r[K][u"型ごとの候補の数"][k] > 0)) for k in TYPES)
        one = [r for r in clue if r[K][u"判定"] == u"導出一致"]
        T[u"%s の導出一致で根拠に要素名" % K] = sum(1 for r in one if r[K][u"根拠に要素名"])
        T[u"%s の導出一致で根拠に名か値" % K] = sum(1 for r in one if r[K][u"根拠に名か値"])
        T[u"%s の導出一致で根拠に名か値の割合" % K] = pct(T[u"%s の導出一致で根拠に名か値" % K], len(one))
        T[u"%s で K0 の導出一致のうち同じ候補で導出一致" % K] = sum(1 for r in clue if r[u"K0 の判定"] == u"導出一致" and r[K][u"K0 の導出一致と同じ候補"] is True)
        T[u"%s の対照のうち どの型かに recomputed の値が在る" % K] = sum(1 for r in ctl if r[K][u"どの型かに recomputed の値が在る"])
        T[u"%s の対照の割合(型を問わず)" % K] = pct(T[u"%s の対照のうち どの型かに recomputed の値が在る" % K], len(ctl))
        T[u"%s の対照の判定" % K] = collections.OrderedDict((v, sum(1 for r in ctl if r[K][u"判定"] == v)) for v in VERDICTS)
    was_miss = [r for r in clue if r[u"K0 の判定"] == u"不一致"]
    was_one = [r for r in clue if r[u"K0 の判定"] == u"導出一致"]
    T[u"K0 の不一致のうち K1 で導出一致か保留"] = sum(1 for r in was_miss if r[u"K1"][u"判定"] != u"不一致")
    T[u"K0 の導出一致のうち K1 で保留"] = sum(1 for r in was_one if r[u"K1"][u"判定"] == u"保留")
    T[u"K0 の導出一致のうち K2 で保留"] = sum(1 for r in was_one if r[u"K2"][u"判定"] == u"保留")
    T[u"K0 の導出一致のうち K3 で保留"] = sum(1 for r in was_one if r[u"K3"][u"判定"] == u"保留")
    byid = {r[u"id"]: r for r in clue}
    T[u"2 項の和の 5 行で K2 の D7 が帯の中"] = sum(1 for i in sum_ids if byid[i][u"K2"][u"型ごとの候補の数"][u"D7"] > 0)
    T[u"ポイント 2 行で K2 の D8 の候補で導出一致"] = sum(1 for i in point_ids if byid[i][u"K2"][u"判定"] == u"導出一致" and byid[i][u"K2"][u"候補"][0][u"型"] == u"D8")
    return T


# ---------------------------------------------------------------- 門自身の近傍・D7・D8(script とは別に書く)

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


def stage_in_band(v, t, G):
    e = abs(abs(v) - t)
    return e <= G


def ref_d7_count(facts, N, t, u):
    by_ctx = collections.defaultdict(list)
    for f in facts:
        if f[u"unit"] == "JPY" and f[u"name"] in N:
            by_ctx[f[u"context"]].append(f)
    n = 0
    for fs in by_ctx.values():
        for i in range(len(fs)):
            for j in range(i + 1, len(fs)):
                if fs[i][u"name"] != fs[j][u"name"] and stage_in_band(fs[i][u"value"] + fs[j][u"value"], t, fs[i][u"g"] + fs[j][u"g"] + u):
                    n += 1
    return n


def ref_d8_count(facts, N, t, u):
    by_name = collections.defaultdict(dict)
    for f in facts:
        if f[u"unit"] == "JPY" and f[u"name"] in N:
            by_name[f[u"name"]][f[u"context"]] = f
    n = 0
    names = sorted(by_name)
    for x in names:
        for y in names:
            if x == y:
                continue
            ctxs = sorted(c for c in by_name[x] if c in by_name[y] and by_name[y][c][u"value"] != 0)
            for i in range(len(ctxs)):
                for j in range(i + 1, len(ctxs)):
                    x1, y1, x2, y2 = by_name[x][ctxs[i]], by_name[y][ctxs[i]], by_name[x][ctxs[j]], by_name[y][ctxs[j]]
                    v = (x1[u"value"] / abs(y1[u"value"]) - x2[u"value"] / abs(y2[u"value"])) * 100.0
                    G = u + 100.0 * sum(xx[u"g"] / abs(yy[u"value"]) + yy[u"g"] * abs(xx[u"value"]) / (yy[u"value"] ** 2) for xx, yy in ((x1, y1), (x2, y2)))
                    if stage_in_band(v, t, G):
                        n += 1
    return n


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(F-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    return {
        u"F-1": [u"%d" % T[u"K0 の不一致のうち K1 で導出一致か保留"]], u"F-2": [u"%d" % T[u"K0 の導出一致のうち K1 で保留"]],
        u"F-3": [u"%d" % T[u"2 項の和の 5 行で K2 の D7 が帯の中"]], u"F-4": [u"%d" % T[u"ポイント 2 行で K2 の D8 の候補で導出一致"]],
        u"F-5": [u"%d" % T[u"K0 の導出一致のうち K2 で保留"]], u"F-6": [u"%d" % T[u"K3 の判定(手がかりあり)"][u"導出一致"]],
        u"F-7": [u"%d" % T[u"K3 の判定(手がかりあり)"][u"不一致"]], u"F-8": [u"%s%%" % T[u"K3 の対照の割合(型を問わず)"]],
        u"F-9": [u"%s%%(%d / %d)" % (T[u"K3 の導出一致で根拠に名か値の割合"], T[u"K3 の導出一致で根拠に名か値"], T[u"K3 の判定(手がかりあり)"][u"導出一致"])],
        u"F-10": [u"手がかりなし %d" % T[u"手がかりなし"], u"判定不能 %d" % T[u"判定不能の num"], u"偽 %d" % T[u"偽の num"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が F-1〜F-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"F-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"F-1", u"F-2", u"F-3", u"F-4", u"F-5", u"F-6", u"F-7") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    # 条件ごとの判定の表(K0〜K3)
    k0 = T[u"K0 の判定(手がかりあり)"]
    if u"| **K0**(深さ 1・6 型。前の便) | %d | %d | %d |" % tuple(k0[v] for v in VERDICTS) not in doc:
        p.append(u"条件の表の K0 の行")
    for K in CONDITIONS:
        kk = T[u"%s の判定(手がかりあり)" % K]
        c = T[u"%s の対照の判定" % K]
        line = u"| **%s**" % K
        want = u"| %d | %d | %d | %d / %d / %d | %s%% |" % (kk[u"導出一致"], kk[u"保留"], kk[u"不一致"], c[u"導出一致"], c[u"保留"], c[u"不一致"], T[u"%s の対照の割合(型を問わず)" % K])
        found = any(l.startswith(line) and l.endswith(want) for l in doc.splitlines())
        if not found:
            p.append(u"条件の表の %s の行(%s)" % (K, want))
        tr = T[u"%s の遷移(K0 → %s)" % (K, K)]
        for a in VERDICTS:
            row = u"| %s | %s(%d) | %d | %d | %d |" % (K, a, sum(tr[u"%s → %s" % (a, b)] for b in VERDICTS), tr[u"%s → 導出一致" % a], tr[u"%s → 保留" % a], tr[u"%s → 不一致" % a])
            if row not in doc:
                p.append(u"遷移表の行 %s" % row)
        byt = u"・".join(u"%s %d" % (k, v) for k, v in T[u"%s の型ごとの帯の中の行(手がかりあり)" % K].items())
        if u"%s: %s" % (K, byt) not in doc:
            p.append(u"%s の型ごとの行" % K)
    for s in (u"K1 で %d・K2 で %d・K3 で %d" % (T[u"K0 の導出一致のうち K1 で保留"], T[u"K0 の導出一致のうち K2 で保留"], T[u"K0 の導出一致のうち K3 で保留"]),
              u"全探索の候補の数が前の便の記録と一致した行 %d / %d" % (T[u"全探索の候補の数が前の便の記録と一致した行"], len(rec[u"行"])),
              u"K0 を出し直して記録と一致した行 %d" % T[u"K0 を出し直して記録と一致した行"],
              u"名か値で K1 %d・K2 %d・K3 %d" % (T[u"K1 の導出一致で根拠に名か値"], T[u"K2 の導出一致で根拠に名か値"], T[u"K3 の導出一致で根拠に名か値"])):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    for i, (v, n) in T[u"ポイント 2 行の K2 の判定と D8 の候補の数"].items():
        if u"%s(%s。D8 の候補 %d)" % (i, v, n) not in doc:
            p.append(u"ポイントの行 %s の字" % i)
    for i in T[u"K0 の不一致のうち K1 で導出一致か保留の id と判定"]:
        if i not in doc:
            p.append(u"F-1 の id %s が文書に無い" % i)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"F-\d+|E-\d+|C-\d+|K\d|D\d|P\d+|§\d+(-\d+)*", u" ", s)
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
    for f in re.findall(r"spec_from_file_location\([^,]+,\s*([^)]*)\)", src):
        if "ROOT, rel" not in f:
            p.append(u"importlib で読む file が材料の経路でない: %s" % f)
    for m in re.findall(r'load_module\(MATERIALS\[u"([a-z_]+)"\]', src):
        if m not in ("prev_script",):
            p.append(u"importlib で読む材料が前の便の script でない: %s" % m)
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
        cls.mod = load(SCRIPT, "derivation_depth_under_test")
        cls.subj, cls.full = cls.mod.load_prev()

    def materials(self):
        m = self.mod
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"claims"][0]))[u"claims"]}
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, m.MATERIALS[u"labels"][0]))[u"labels"]}
        prev_rec = jload(os.path.join(ROOT, m.MATERIALS[u"prev_rec"][0]))
        zpath = os.path.join(ROOT, m.MATERIALS[u"zip"][0])
        facts, _ = self.full.parse_facts(zpath)
        arcs, _ = self.full.parse_cal(zpath)
        return texts, labels, prev_rec, facts, arcs

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertTrue(W[u"(f) K0 の判定(手がかりあり)が 15・5・14"])
        self.assertEqual(W[u"(e) 全探索の候補の数が前の便の記録と一致した行"], len(self.rec[u"行"]))
        self.assertEqual(W[u"(e) K0 を出し直して記録と一致した行"], len(self.rec[u"行"]))
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(self.rec_text.count("scratchpad"), 0)
        self.assertEqual(self.mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_a_3_k0_is_the_previous_record_and_seal_lists_the_same_ids(self):
        texts, labels, prev_rec, facts, arcs = self.materials()
        prev = {r[u"id"]: r for r in prev_rec[u"行"]}
        for r in self.rec[u"行"]:
            self.assertEqual(r[u"K0 の判定"], prev[r[u"id"]][u"判定"], r[u"id"])
            self.assertEqual(r[u"K0 の候補の数"], prev[r[u"id"]][u"制約つきの候補の数"], r[u"id"])
            self.assertEqual(r[u"S"], prev[r[u"id"]][u"S"], r[u"id"])
            self.assertEqual(r[u"手がかりあり"], prev[r[u"id"]][u"手がかりあり"], r[u"id"])
        self.assertEqual(tuple(self.rec[u"定数"][u"2 項の和の 5 行"]), self.mod.SUM_IDS)
        self.assertEqual(tuple(self.rec[u"定数"][u"ポイント 2 行"]), self.mod.POINT_IDS)
        for i in self.mod.SUM_IDS + self.mod.POINT_IDS:
            self.assertIn(i, self.seal, u"封 §3 に %s が無い" % i)

    def test_b_1_rows_recomputed_by_the_script(self):
        texts, labels, prev_rec, facts, arcs = self.materials()
        rows = self.mod.build_rows(self.subj, self.full, prev_rec[u"行"], labels, texts, self.full.Index(facts, arcs))
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(self.mod.judge(self.mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_depth2_d7_d8_recomputed_by_the_gate(self):
        u"""深さ 2 の近傍・D7・D8 を門自身の code で作り直し、全行・全条件の候補の数を記録と一致させる。6 型の候補は前々便の derive。"""
        texts, labels, prev_rec, facts, arcs = self.materials()
        idx = self.full.Index(facts, arcs)
        for r in self.rec[u"行"]:
            S = r[u"S"]
            N1 = ref_neighbourhood(S, arcs)
            N2 = ref_neighbourhood(sorted(N1), arcs)
            self.assertEqual(r[u"N1 の大きさ"], len(N1), r[u"id"])
            self.assertEqual(set(r[u"N2"]), N2, r[u"id"])
            self.assertTrue(N1 <= N2)
            tx = texts[r[u"id"]]
            u0, _ = self.full.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
            cands, u, t = self.full.derive({u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}, idx)
            self.assertEqual(len(cands), r[u"全探索の候補の数"], r[u"id"])
            money, point = tx[u"単位"] in self.full.UNIT_SCALE, tx[u"単位"] == u"ポイント"
            for K, N, extra in ((u"K1", N2, False), (u"K2", N1, True), (u"K3", N2, True)):
                if not S:
                    self.assertEqual(r[K][u"判定"], u"手がかりなし")
                    continue
                n = sum(1 for c in cands if ref_keep(c, N))
                if extra:
                    n += (ref_d7_count(facts, N, t, u) if money else 0) + (ref_d8_count(facts, N, t, u) if point else 0)
                self.assertEqual(n, r[K][u"候補の数"], u"%s %s" % (r[u"id"], K))
                self.assertEqual(r[K][u"判定"], u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致")
                self.assertEqual(sum(r[K][u"型ごとの候補の数"].values()), n)
                self.assertEqual(len(r[K][u"候補"]), min(n, 20))
                for c in r[K][u"候補"]:
                    if c[u"型"] in (u"D7", u"D8"):
                        self.assertTrue(all(f[u"name"] in N for f in c[u"fact"]), u"%s %s の %s が N の外" % (r[u"id"], K, c[u"型"]))
                        self.assertTrue(extra)
                    else:
                        self.assertTrue(ref_keep(c, N))
                    self.assertLessEqual(abs(abs(c[u"v"]) - t), c[u"G"])
                    if c[u"型"] == u"D7":
                        self.assertEqual(c[u"fact"][0][u"context"], c[u"fact"][1][u"context"])
                        self.assertNotEqual(c[u"fact"][0][u"name"], c[u"fact"][1][u"name"])
                    if c[u"型"] == u"D8":
                        self.assertEqual(len(c[u"fact"]), 4)
                        self.assertNotEqual(c[u"fact"][0][u"context"], c[u"fact"][2][u"context"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"], self.mod.SUM_IDS, self.mod.POINT_IDS), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)
        self.assertEqual(dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items()), dict(self.bounds), u"script の幅が封の字と違う")

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"F-1": (2, 5), u"F-2": (3, 8), u"F-3": (0, 1), u"F-4": (1, 2), u"F-5": (0, 3), u"F-6": (12, 18), u"F-7": (7, 11), u"F-8": 95, u"F-9": 80})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_d_3_k0_row_of_the_condition_table_is_bound_to_the_previous_record(self):
        u"""§2-2 の K0 の行(対照の判定 186 / 62 / 1、再現 99.6%)は本便の記録に無い数なので、前の便の記録(封 §0 の材料)と照らす。"""
        prev_rec = jload(os.path.join(ROOT, self.mod.MATERIALS[u"prev_rec"][0]))
        T0 = prev_rec[u"集計"]
        k0 = self.rec[u"集計"][u"K0 の判定(手がかりあり)"]
        c = T0[u"対照の判定"]
        row = u"| **K0**(深さ 1・6 型。前の便) | %d | %d | %d | %d / %d / %d(前の便の記録) | %s%% |" % (
            k0[u"導出一致"], k0[u"保留"], k0[u"不一致"], c[u"導出一致"], c[u"保留"], c[u"不一致"], T0[u"対照の割合(型を問わず)"])
        self.assertIn(row, self.doc)
        self.assertEqual(dict(T0[u"手がかりありの判定"]), dict(k0))
        bad = self.doc.replace(row, row.replace(u"%d / " % c[u"導出一致"], u"%d / " % (c[u"導出一致"] - 6), 1))
        self.assertNotEqual(bad, self.doc)
        self.assertNotIn(row, bad)

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_imports_and_d7_d8_fire_on_synthetic_facts(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m, full = self.mod, self.full
        F = lambda name, ctx, val, g: {u"name": name, u"context": ctx, u"unit": "JPY", u"value": val, u"g": g}
        facts = [F(u"a:X", u"CY", 300e6, 1e6), F(u"a:Y", u"CY", 210e6, 1e6), F(u"a:Z", u"CY", 50e6, 1e6),
                 F(u"a:Sales", u"CY", 1000e6, 1e6), F(u"a:Cost", u"CY", 702e6, 1e6), F(u"a:Sales", u"PY", 900e6, 1e6), F(u"a:Cost", u"PY", 607.5e6, 1e6)]
        idx = full.Index(facts, {})
        d7 = m.d7_candidates(full, idx, [u"a:X", u"a:Y"], 510e6, 1e6)
        self.assertEqual([sorted(f[u"name"] for f in c[u"fact"]) for c in d7], [[u"a:X", u"a:Y"]])          # 300 + 210。Z は N の外
        self.assertEqual(m.d7_candidates(full, idx, [u"a:X"], 510e6, 1e6), [])                               # 両方 ∈ N が要る
        self.assertEqual(m.d7_candidates(full, idx, [u"a:X", u"a:Y", u"a:Z"], 350e6, 1e6)[0][u"型"], u"D7")   # 300 + 50
        d8 = m.d8_candidates(full, idx, [u"a:Sales", u"a:Cost"], 2.7, 0.1)                                   # 70.2 − 67.5 = 2.7 ポイント
        self.assertEqual(len(d8), 1)
        self.assertEqual([f[u"name"] for f in d8[0][u"fact"]], [u"a:Cost", u"a:Sales", u"a:Cost", u"a:Sales"])
        self.assertEqual(m.d8_candidates(full, idx, [u"a:Sales"], 2.7, 0.1), [])
        arcs = {u"a:P": {u"a:X": 1.0, u"a:Y": 1.0}, u"a:T": {u"a:P": 1.0, u"a:Q": 1.0}, u"a:Q": {u"a:Z": 1.0}}
        N1 = self.subj.neighbourhood([u"a:X"], arcs)
        N2 = self.subj.neighbourhood(N1, arcs)
        self.assertEqual(set(N1), {u"a:X", u"a:P", u"a:Y"})
        self.assertEqual(set(N2), {u"a:X", u"a:P", u"a:Y", u"a:T", u"a:Q"})                                  # 深さ 2 で祖父と叔父。従兄弟 Z は深さ 3

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
        cls.mod = load(SCRIPT, "derivation_depth_for_mutation")

    def test_m_1_flipping_a_judgement_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"予測の判定"][u"F-6"] = u"当たり" if rec[u"予測の判定"][u"F-6"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"K3 の判定(手がかりあり)"][u"保留"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"], self.mod.SUM_IDS, self.mod.POINT_IDS)[u"K3 の判定(手がかりあり)"], rec[u"集計"][u"K3 の判定(手がかりあり)"])

    def test_m_3_moving_a_condition_verdict_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"母数"] and x[u"手がかりあり"] and x[u"K3"][u"判定"] == u"保留"][0]
        r[u"K3"][u"判定"] = u"導出一致"
        n = r[u"K3"][u"候補の数"]
        self.assertNotEqual(u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致", r[u"K3"][u"判定"])

    def test_m_4_widening_n2_in_the_record_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"手がかりあり"]][0]
        arcs, _ = self.mod.load_prev()[1].parse_cal(os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"))
        N2 = ref_neighbourhood(sorted(ref_neighbourhood(r[u"S"], arcs)), arcs)
        self.assertEqual(set(r[u"N2"]), N2)
        r[u"N2"].append(u"jppfs_cor:NotInTheNeighbourhood")
        self.assertNotEqual(set(r[u"N2"]), N2)

    def test_m_5_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_doc_transition_number_change_is_caught(self):
        tr = self.rec[u"集計"][u"K3 の遷移(K0 → K3)"]
        n = tr[u"導出一致 → 保留"]
        row = u"| K3 | 導出一致(%d) | %d | %d | %d |" % (sum(tr[u"導出一致 → %s" % b] for b in VERDICTS), tr[u"導出一致 → 導出一致"], n, tr[u"導出一致 → 不一致"])
        self.assertIn(row, self.doc)
        bad = self.doc.replace(row, row.replace(u"| %d |" % n, u"| %d |" % (n + 1), 1))
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_7_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**12〜18**", u"**5〜18**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_8_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_9_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT).replace(u'load_module(MATERIALS[u"prev_script"]', u'load_module(MATERIALS[u"zip"]')), [])

    def test_m_10_d7_with_one_side_outside_n_is_caught(self):
        u"""D7 を「片方 ∈ N」に緩めると、記録の K2 の候補の数と合わなくなる行が在る。"""
        texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json"))[u"claims"]}
        subj, full = self.mod.load_prev()
        zpath = os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")
        facts, _ = full.parse_facts(zpath)
        arcs, _ = full.parse_cal(zpath)
        changed = 0
        for r in self.rec[u"行"]:
            if not (r[u"母数"] and r[u"手がかりあり"] and r[u"unit"] in full.UNIT_SCALE):
                continue
            tx = texts[r[u"id"]]
            u0, _ = full.written_granularity(tx.get(u"文"), tx[u"数"], tx[u"単位"])
            _, u, t = full.derive({u"unit": tx[u"単位"], u"value": tx[u"数"], u"u": u0}, full.Index(facts, arcs))
            N1 = ref_neighbourhood(r[u"S"], arcs)
            by_ctx = collections.defaultdict(list)
            for f in facts:
                if f[u"unit"] == "JPY":
                    by_ctx[f[u"context"]].append(f)
            loose = 0
            for fs in by_ctx.values():
                for i in range(len(fs)):
                    for j in range(i + 1, len(fs)):
                        a, b = fs[i], fs[j]
                        if a[u"name"] != b[u"name"] and (a[u"name"] in N1 or b[u"name"] in N1) and stage_in_band(a[u"value"] + b[u"value"], t, a[u"g"] + b[u"g"] + u):
                            loose += 1
            if loose != r[u"K2"][u"型ごとの候補の数"][u"D7"]:
                changed += 1
        self.assertGreater(changed, 0)


if __name__ == "__main__":
    unittest.main()
