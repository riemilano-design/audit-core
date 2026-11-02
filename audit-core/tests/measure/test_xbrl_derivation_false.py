# -*- coding: utf-8 -*-
u"""門: 偽の数に導出一致を出す率(誤受理)(封 docs/XBRL_DERIVATION_FALSE_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_false_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 G-1〜G-9 を、記録の集計と封 §3 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 集計を行から数え直す。偽の数(V1・V2・V3)を門自身の code で前の便の記録から作り直し、記録の t と一致させる。
- 各変種の K0 の候補の数を、前々便の derive と門自身の残す条件で出し直し、記録と一致させる(全行・全変種)。
- V0 が前の便の記録(判定・候補の数)を再現すること。H までの判定が候補の段から数え直せること。
- 文書の表の実測の欄・散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
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

SEAL_REL = "docs/XBRL_DERIVATION_FALSE_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_FALSE_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_false_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_false_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation_false.py"
SEAL_COMMIT_SHORT = "79dba8b"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"G-%d" % i for i in range(1, 10))
VARIANTS = (u"V0", u"V1", u"V2", u"V3")
FALSE_VARIANTS = (u"V1", u"V2", u"V3")
VERDICTS = (u"導出一致", u"保留", u"不一致")
TIGHT = (u"完全一致", u"丸めの帯 H")
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
        m = re.match(r"^\| \*\*(G-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"G-1", u"G-2", u"G-3", u"G-5"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    b[u"G-4"] = int(re.search(r"\*\*(\d+)% 以上\*\*", rows[u"G-4"][0]).group(1))
    b[u"G-6"] = int(re.search(r"\*\*(\d+) / \d+\*\*", rows[u"G-6"][0]).group(1))
    b[u"G-7"] = int(re.search(r"\*\*(\d+)% 以下\*\*", rows[u"G-7"][0]).group(1))
    b[u"G-8"] = 0 if u"全件が V0 の候補と別の fact" in rows[u"G-8"][0] else None
    return b


# ---------------------------------------------------------------- 求め直し

def pct(a, b):
    return None if not b else round(100.0 * a / b, 1)


def _cnt(items):
    c = collections.Counter(items)
    return collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"G-1"] = b[u"G-1"][0] <= T[u"V1 の K0 の判定(手がかりあり)"][u"導出一致"] <= b[u"G-1"][1]
    J[u"G-2"] = b[u"G-2"][0] <= T[u"V2 の K0 の判定(手がかりあり)"][u"導出一致"] <= b[u"G-2"][1]
    J[u"G-3"] = b[u"G-3"][0] <= T[u"V3 の K0 の判定(手がかりあり)"][u"導出一致"] <= b[u"G-3"][1]
    J[u"G-4"] = T[u"偽の数で K0 が退けた割合"] is not None and T[u"偽の数で K0 が退けた割合"] >= b[u"G-4"]
    J[u"G-5"] = b[u"G-5"][0] <= T[u"V1 の全探索で帯の中(候補 1 以上。手がかりあり)"] <= b[u"G-5"][1]
    J[u"G-6"] = T[u"V0 で前の便の記録と一致した行(手がかりあり)"] == b[u"G-6"]
    J[u"G-7"] = T[u"対照の V1 で K0 が導出一致の割合"] is not None and T[u"対照の V1 で K0 が導出一致の割合"] <= b[u"G-7"]
    J[u"G-8"] = T[u"誤受理で V0 の候補と同じ fact(合計)"] == b[u"G-8"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"G-9"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"母数"]]
    ctl = [r for r in rows if r[u"対照"]]
    clue = [r for r in pop if r[u"手がかりあり"]]
    T[u"母数"] = len(pop)
    T[u"対照"] = len(ctl)
    T[u"手がかりあり"] = len(clue)
    T[u"手がかりなし"] = len(pop) - len(clue)
    T[u"V0 で前の便の記録と一致した行(全行)"] = sum(1 for r in rows if r[u"V0"][u"前の便の記録と一致"])
    T[u"V0 で前の便の記録と一致した行(手がかりあり)"] = sum(1 for r in clue if r[u"V0"][u"前の便の記録と一致"])
    for V in VARIANTS:
        T[u"%s の K0 の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"K0 の判定"] == v)) for v in VERDICTS)
        T[u"%s の全探索の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"全探索の判定"] == v)) for v in VERDICTS)
        T[u"%s の全探索で帯の中(候補 1 以上。手がかりあり)" % V] = sum(1 for r in clue if r[V][u"全探索の候補の数"] >= 1)
        T[u"%s の H までの判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"H までの判定"] == v)) for v in VERDICTS)
        if V != u"V0":
            T[u"%s の誤受理で V0 の候補と同じ fact" % V] = sum(1 for r in clue if r[V][u"K0 の判定"] == u"導出一致" and r[V][u"V0 の候補と同じ fact"])
            T[u"%s の誤受理の候補の段" % V] = _cnt(r[V][u"候補"][0][u"段"] for r in clue if r[V][u"K0 の判定"] == u"導出一致")
    total = len(clue) * len(FALSE_VARIANTS)
    T[u"偽の数の件数(手がかりあり × 3)"] = total
    T[u"偽の数で K0 が導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"導出一致")
    T[u"偽の数で K0 が保留"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"保留")
    T[u"偽の数で K0 が不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"K0 の判定"] == u"不一致")
    T[u"偽の数で K0 が退けた割合"] = pct(T[u"偽の数で K0 が不一致(退けた)"], total)
    T[u"偽の数で全探索が不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"全探索の判定"] == u"不一致")
    T[u"偽の数で全探索が退けた割合"] = pct(T[u"偽の数で全探索が不一致(退けた)"], total)
    T[u"誤受理で V0 の候補と同じ fact(合計)"] = sum(T[u"%s の誤受理で V0 の候補と同じ fact" % V] for V in FALSE_VARIANTS)
    T[u"偽の数で H までで導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"H までの判定"] == u"導出一致")
    T[u"偽の数で H までで不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"H までの判定"] == u"不一致")
    T[u"偽の数で H までで退けた割合"] = pct(T[u"偽の数で H までで不一致(退けた)"], total)
    T[u"V0 で H までで導出一致(真の数の受理)"] = T[u"V0 の H までの判定(手がかりあり)"][u"導出一致"]
    T[u"対照の V1 で K0 が導出一致"] = sum(1 for r in ctl if r[u"V1"][u"K0 の判定"] == u"導出一致")
    T[u"対照の V1 で K0 が導出一致の割合"] = pct(T[u"対照の V1 で K0 が導出一致"], len(ctl))
    T[u"対照の V1 の K0 の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V1"][u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"対照の V1 で全探索が帯の中"] = sum(1 for r in ctl if r[u"V1"][u"全探索の候補の数"] >= 1)
    T[u"対照の V0 の K0 の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V0"][u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"対照の V1 で H までで導出一致"] = sum(1 for r in ctl if r[u"V1"][u"H までの判定"] == u"導出一致")
    T[u"対照の V1 で H までで導出一致の割合"] = pct(T[u"対照の V1 で H までで導出一致"], len(ctl))
    T[u"対照の V0 で H までで導出一致"] = sum(1 for r in ctl if r[u"V0"][u"H までの判定"] == u"導出一致")
    for V in VARIANTS:
        T[u"%s の片側の判定(手がかりあり)" % V] = collections.OrderedDict((v, sum(1 for r in clue if r[V][u"片側の判定"] == v)) for v in VERDICTS)
    T[u"偽の数で片側で導出一致(誤受理)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"片側の判定"] == u"導出一致")
    T[u"偽の数で片側で不一致(退けた)"] = sum(1 for r in clue for V in FALSE_VARIANTS if r[V][u"片側の判定"] == u"不一致")
    T[u"偽の数で片側で退けた割合"] = pct(T[u"偽の数で片側で不一致(退けた)"], total)
    T[u"V0 で片側で導出一致(真の数の受理)"] = T[u"V0 の片側の判定(手がかりあり)"][u"導出一致"]
    T[u"V1 の片側の誤受理の id"] = [r[u"id"] for r in clue if r[u"V1"][u"片側の判定"] == u"導出一致"]
    T[u"対照の V1 で片側で導出一致"] = sum(1 for r in ctl if r[u"V1"][u"片側の判定"] == u"導出一致")
    T[u"対照の V1 で片側で導出一致の割合"] = pct(T[u"対照の V1 で片側で導出一致"], len(ctl))
    T[u"対照の V0 で片側で導出一致"] = sum(1 for r in ctl if r[u"V0"][u"片側の判定"] == u"導出一致")
    T[u"対照の V0 の片側の判定"] = collections.OrderedDict((v, sum(1 for r in ctl if r[u"V0"][u"片側の判定"] == v)) for v in VERDICTS)
    return T


def ref_one_sided(c, t, u, money):
    if not money:
        return True
    d = abs(c[u"v"]) - t
    return -(c[u"G"] - u) - 1e-9 * max(1.0, t) <= d < u - 1e-9 * max(1.0, t)


# ---------------------------------------------------------------- 門自身の偽の数・残す条件(script とは別に書く)

def ref_variants(prev_clue_rows):
    u"""封 §1 の字から偽の数を作り直す。prev_clue_rows は前の便の記録の手がかりあり 34(記録の順 = id の順)。"""
    out = collections.OrderedDict()
    n = len(prev_clue_rows)
    for i, r in enumerate(prev_clue_rows):
        t, u = r[u"t'"], r[u"u"]
        v2 = round(t * 1.1 / u) * u
        if abs(v2 - t) <= 1e-9 * max(1.0, t):
            v2 = t + 2 * u
        v3 = None
        for step in range(1, n):
            o = prev_clue_rows[(i + step) % n]
            if o[u"unit"] == r[u"unit"] and abs(o[u"t'"] - t) > 1e-9 * max(1.0, t):
                v3 = (o[u"t'"], o[u"id"])
                break
        out[r[u"id"]] = {u"V0": t, u"V1": t + u, u"V2": v2, u"V3": v3}
    return out


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
        m = re.match(r"^\| \*\*(G-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    return {
        u"G-1": [u"%d" % T[u"V1 の K0 の判定(手がかりあり)"][u"導出一致"]], u"G-2": [u"%d" % T[u"V2 の K0 の判定(手がかりあり)"][u"導出一致"]],
        u"G-3": [u"%d" % T[u"V3 の K0 の判定(手がかりあり)"][u"導出一致"]],
        u"G-4": [u"%s%%(%d / %d)" % (T[u"偽の数で K0 が退けた割合"], T[u"偽の数で K0 が不一致(退けた)"], T[u"偽の数の件数(手がかりあり × 3)"])],
        u"G-5": [u"%d" % T[u"V1 の全探索で帯の中(候補 1 以上。手がかりあり)"]],
        u"G-6": [u"%d / %d" % (T[u"V0 で前の便の記録と一致した行(手がかりあり)"], T[u"手がかりあり"])],
        u"G-7": [u"%s%%(%d / %d)" % (T[u"対照の V1 で K0 が導出一致の割合"], T[u"対照の V1 で K0 が導出一致"], T[u"対照"])],
        u"G-8": [u"同じ fact %d" % T[u"誤受理で V0 の候補と同じ fact(合計)"], u"誤受理 %d" % T[u"偽の数で K0 が導出一致(誤受理)"]],
        u"G-9": [u"手がかりなし %d" % T[u"手がかりなし"], u"判定不能 %d" % T[u"判定不能の num"], u"偽 %d" % T[u"偽の num"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が G-1〜G-9 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"G-9" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"G-1", u"G-2", u"G-3", u"G-5") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    for V in VARIANTS:
        k = T[u"%s の K0 の判定(手がかりあり)" % V]
        f = T[u"%s の全探索の判定(手がかりあり)" % V]
        h = T[u"%s の H までの判定(手がかりあり)" % V]
        line = u"| **%s**" % V
        want = u"| %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (k[u"導出一致"], k[u"保留"], k[u"不一致"], f[u"導出一致"], f[u"保留"], f[u"不一致"], h[u"導出一致"], h[u"保留"], h[u"不一致"])
        if not any(l.startswith(line) and l.endswith(want) for l in doc.splitlines()):
            p.append(u"変種の表の %s の行(%s)" % (V, want))
    for V in FALSE_VARIANTS:
        for i in T[u"%s の誤受理の id と候補の要素" % V]:
            if i not in doc:
                p.append(u"%s の誤受理の id %s が文書に無い" % (V, i))
    for i in T[u"V1 の片側の誤受理の id"]:
        if i not in doc:
            p.append(u"V1 の片側の誤受理の id %s が文書に無い" % i)
        st = T[u"%s の誤受理の候補の段" % V]
        s = u"%s の誤受理の段: %s" % (V, u"・".join(u"%s %d" % (k, v) for k, v in st.items()))
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    for s in (u"全探索は %s%%(%d / %d)" % (T[u"偽の数で全探索が退けた割合"], T[u"偽の数で全探索が不一致(退けた)"], T[u"偽の数の件数(手がかりあり × 3)"]),
              u"H までで退けた %s%%(%d / %d)" % (T[u"偽の数で H までで退けた割合"], T[u"偽の数で H までで不一致(退けた)"], T[u"偽の数の件数(手がかりあり × 3)"]),
              u"H までで誤受理 %d" % T[u"偽の数で H までで導出一致(誤受理)"],
              u"真の数の受理は 15 → %d" % T[u"V0 で H までで導出一致(真の数の受理)"],
              u"対照の V1 は H までで %s%%(%d / %d)" % (T[u"対照の V1 で H までで導出一致の割合"], T[u"対照の V1 で H までで導出一致"], T[u"対照"]),
              u"対照の V0 は H までで %d" % T[u"対照の V0 で H までで導出一致"],
              u"V0 で前の便の記録と一致した行 %d / %d" % (T[u"V0 で前の便の記録と一致した行(全行)"], len(rec[u"行"])),
              u"対照の V1 は全探索で %d / %d が帯の中" % (T[u"対照の V1 で全探索が帯の中"], T[u"対照"]),
              u"保留 %d" % T[u"偽の数で K0 が保留"],
              u"片側の帯では偽の数の誤受理 %d(V1 %d・V2 %d・V3 %d)" % (T[u"偽の数で片側で導出一致(誤受理)"], T[u"V1 の片側の判定(手がかりあり)"][u"導出一致"],
                                                             T[u"V2 の片側の判定(手がかりあり)"][u"導出一致"], T[u"V3 の片側の判定(手がかりあり)"][u"導出一致"]),
              u"退けた %s%%(%d / %d)" % (T[u"偽の数で片側で退けた割合"], T[u"偽の数で片側で不一致(退けた)"], T[u"偽の数の件数(手がかりあり × 3)"]),
              u"真の数の受理は %d のまま" % T[u"V0 で片側で導出一致(真の数の受理)"],
              u"対照の V1 は %s%%(%d / %d)" % (T[u"対照の V1 で片側で導出一致の割合"], T[u"対照の V1 で片側で導出一致"], T[u"対照"]),
              u"対照の V0 の導出一致は %d → %d" % (T[u"対照の V0 の K0 の判定"][u"導出一致"], T[u"対照の V0 で片側で導出一致"])):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"G-\d+|F-\d+|E-\d+|C-\d+|K\d|V\d|D\d|P\d+|§\d+(-\d+)*", u" ", s)
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
        if m != "prev_script":
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
        cls.mod = load(SCRIPT, "derivation_false_under_test")
        cls.subj, cls.full = cls.mod.load_prev()
        cls.prev_rec = jload(os.path.join(ROOT, cls.mod.MATERIALS[u"prev_rec"][0]))
        zpath = os.path.join(ROOT, cls.mod.MATERIALS[u"zip"][0])
        cls.facts, _ = cls.full.parse_facts(zpath)
        cls.arcs, _ = cls.full.parse_cal(zpath)

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertEqual(W[u"(e) V0 で前の便の記録と一致した行(全行)"], len(self.rec[u"行"]))
        self.assertEqual(W[u"(e) derive が返した t が一致しなかった行×変種"], 0)
        self.assertTrue(W[u"(f) V3 の出所が全行で決まった"])
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

    def test_a_3_false_numbers_rebuilt_from_the_seal_text(self):
        u"""V1・V2・V3 を封 §1 の字から門自身の code で作り直し、記録の t と出所の id に一致させる。"""
        clue_prev = [r for r in self.prev_rec[u"行"] if r[u"母数"] and r[u"手がかりあり"]]
        ids = [r[u"id"] for r in clue_prev]
        self.assertEqual(ids, sorted(ids), u"前の便の記録の手がかりあり 34 が id の順でない")
        ref = ref_variants(clue_prev)
        for r in self.rec[u"行"]:
            if not (r[u"母数"] and r[u"手がかりあり"]):
                continue
            v = ref[r[u"id"]]
            for V in (u"V0", u"V1", u"V2"):
                self.assertAlmostEqual(r[V][u"t"], v[V], places=6, msg=u"%s %s" % (r[u"id"], V))
            self.assertAlmostEqual(r[u"V3"][u"t"], v[u"V3"][0], places=6, msg=r[u"id"])
            self.assertEqual(r[u"V3 の出所の id"], v[u"V3"][1], r[u"id"])
            self.assertNotEqual(r[u"V3 の出所の id"], r[u"id"])
            for V in FALSE_VARIANTS:
                self.assertGreater(abs(r[V][u"t"] - r[u"V0"][u"t"]), 0, u"%s %s が元の数と同じ" % (r[u"id"], V))
        for r in self.rec[u"行"]:
            if r[u"対照"]:
                self.assertEqual(sorted(k for k in r if k.startswith(u"V")), [u"V0", u"V1"])
                self.assertAlmostEqual(r[u"V1"][u"t"], r[u"t"] + r[u"u"], places=6)

    def test_b_1_rows_recomputed_by_the_script(self):
        rows = self.mod.build_rows(self.subj, self.full, self.prev_rec[u"行"], self.full.Index(self.facts, self.arcs))
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(self.mod.judge(self.mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_candidates_per_variant_recomputed_with_the_gates_own_keep(self):
        u"""各変種の全探索・K0 の候補の数を、前々便の derive と門自身の近傍・残す条件で出し直し、全行一致させる。"""
        idx = self.full.Index(self.facts, self.arcs)
        prev = {r[u"id"]: r for r in self.prev_rec[u"行"]}
        for r in self.rec[u"行"]:
            N = ref_neighbourhood(r[u"S"], self.arcs)
            s = self.full.UNIT_SCALE.get(r[u"unit"], 1.0)
            for V in VARIANTS:
                if V not in r:
                    continue
                cands, u, t = self.full.derive({u"unit": r[u"unit"], u"value": r[V][u"t"] / s, u"u": r[u"u"]}, idx)
                self.assertAlmostEqual(t, r[V][u"t"], delta=1e-6 * max(1.0, abs(t)))
                self.assertEqual(len(cands), r[V][u"全探索の候補の数"], u"%s %s" % (r[u"id"], V))
                if r[u"S"]:
                    kept = [c for c in cands if ref_keep(c, N)]
                    self.assertEqual(len(kept), r[V][u"K0 の候補の数"], u"%s %s" % (r[u"id"], V))
                    self.assertEqual(r[V][u"K0 の判定"], u"導出一致" if len(kept) == 1 else u"保留" if len(kept) >= 2 else u"不一致")
                    tight = sum(1 for c in kept if c[u"段"] in TIGHT)
                    self.assertEqual(tight, r[V][u"H までの候補の数"], u"%s %s" % (r[u"id"], V))
                    self.assertEqual(r[V][u"H までの判定"], u"導出一致" if tight == 1 else u"保留" if tight >= 2 else u"不一致")
                    one = sum(1 for c in kept if ref_one_sided(c, r[V][u"t"], r[u"u"], r[u"unit"] in self.full.UNIT_SCALE))
                    self.assertEqual(one, r[V][u"片側の候補の数"], u"%s %s" % (r[u"id"], V))
                    self.assertEqual(r[V][u"片側の判定"], u"導出一致" if one == 1 else u"保留" if one >= 2 else u"不一致")
                    self.assertLessEqual(one, len(kept))
                    for c in r[V][u"候補"]:
                        self.assertTrue(ref_keep(c, N))
                        self.assertLessEqual(abs(abs(c[u"v"]) - r[V][u"t"]), c[u"G"] + 1e-6)
                else:
                    self.assertEqual(r[V][u"K0 の判定"], u"手がかりなし")
            self.assertEqual(r[u"V0"][u"前の便の記録と一致"], True)
            self.assertEqual(r[u"K0 の判定(前の便の記録)"], prev[r[u"id"]][u"判定"])
            if r[u"S"]:
                self.assertEqual(r[u"V0"][u"K0 の判定"], prev[r[u"id"]][u"判定"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)

    def test_b_4_same_fact_flag_recomputed(self):
        u"""「V0 の候補と同じ fact」を V0 の候補の一覧と照らして数え直す(G-8)。"""
        for r in self.rec[u"行"]:
            if not (r[u"母数"] and r[u"手がかりあり"]):
                continue
            v0 = r[u"V0"][u"候補"]
            for V in FALSE_VARIANTS:
                if r[V][u"K0 の判定"] != u"導出一致":
                    self.assertIsNone(r[V][u"V0 の候補と同じ fact"])
                    continue
                c = r[V][u"候補"][0]
                same = any(c[u"型"] == c0[u"型"] and [dict(f) for f in c[u"fact"]] == [dict(f) for f in c0[u"fact"]] for c0 in v0)
                self.assertEqual(r[V][u"V0 の候補と同じ fact"], same, u"%s %s" % (r[u"id"], V))

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 8)
        want = dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items())
        self.assertEqual(want, dict(self.bounds), u"script の幅が封の字と違う")

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"G-1": (0, 3), u"G-2": (0, 2), u"G-3": (0, 4), u"G-4": 80, u"G-5": (15, 30), u"G-6": 34, u"G-7": 5, u"G-8": 0})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_imports_and_variants_on_synthetic_values(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m = self.mod
        self.assertEqual(m.v2_of(945e6, 1e6), 1040e6)                      # 1039.5 → round → 1040
        self.assertEqual(m.v2_of(3.0, 1.0), 5.0)                             # 3.3 → 3 = t なので t + 2u
        rows = [{u"id": u"A", u"unit": u"円", u"t'": 10.0, u"u": 1.0}, {u"id": u"B", u"unit": u"%", u"t'": 2.0, u"u": 0.1},
                {u"id": u"C", u"unit": u"円", u"t'": 10.0, u"u": 1.0}, {u"id": u"D", u"unit": u"円", u"t'": 30.0, u"u": 1.0}]
        self.assertEqual(m.v3_of(0, rows), (30.0, u"D"))                     # C は同じ値なので飛ばして D
        self.assertEqual(m.v3_of(3, rows), (10.0, u"A"))                     # 末尾は先頭へ
        self.assertEqual(m.v3_of(1, rows), (None, None))                     # % は 1 行だけ
        vs, src = m.variants_of(0, rows)
        self.assertEqual((vs[u"V0"], vs[u"V1"], vs[u"V2"], vs[u"V3"], src), (10.0, 11.0, 11.0, 30.0, u"D"))
        # 帯の性質: t + u は、v = t の fact の帯(G = g + u)に必ず入る(封 G-8 の見立てはここが誤り)
        self.assertEqual(self.full.stage_of(1e6, 1e6 + 1e6), u"丸めの帯 H")        # g = u のとき e = u = H
        self.assertEqual(self.full.stage_of(1e6, 0.0 + 1e6), u"丸めの帯 F")        # g = 0(INF)のとき e = u = G
        # 片側の帯(参考): fact 37,144 千円 に対して 文 37 百万円 は入り、38 百万円(t + u)と 36 百万円は入らない
        c = {u"v": 37144000.0, u"G": 1000.0 + 1e6}
        self.assertTrue(m.one_sided(c, 37e6, 1e6, True))
        self.assertFalse(m.one_sided(c, 38e6, 1e6, True))
        self.assertFalse(m.one_sided(c, 36e6, 1e6, True))
        self.assertTrue(m.one_sided({u"v": 36999500.0, u"G": 1000.0 + 1e6}, 37e6, 1e6, True))   # fact の桁 g の分だけ下に許す
        self.assertTrue(m.one_sided(c, 38e6, 1e6, False))                                       # 金額以外は K0 の帯のまま

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
        rec[u"予測の判定"][u"G-1"] = u"当たり" if rec[u"予測の判定"][u"G-1"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"偽の数で K0 が導出一致(誤受理)"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"偽の数で K0 が導出一致(誤受理)"], rec[u"集計"][u"偽の数で K0 が導出一致(誤受理)"])

    def test_m_3_changing_a_false_number_in_the_record_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"母数"] and x[u"手がかりあり"]][0]
        prev = jload(os.path.join(ROOT, "fixtures/xbrl/derivation_subject_2026-11-02.json"))
        clue_prev = [x for x in prev[u"行"] if x[u"母数"] and x[u"手がかりあり"]]
        ref = ref_variants(clue_prev)[r[u"id"]]
        self.assertAlmostEqual(r[u"V1"][u"t"], ref[u"V1"], places=6)
        r[u"V1"][u"t"] = r[u"V1"][u"t"] + r[u"u"]
        self.assertNotAlmostEqual(r[u"V1"][u"t"], ref[u"V1"], places=6)

    def test_m_4_moving_a_variant_verdict_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"母数"] and x[u"手がかりあり"] and x[u"V2"][u"K0 の判定"] == u"不一致"][0]
        r[u"V2"][u"K0 の判定"] = u"導出一致"
        n = r[u"V2"][u"K0 の候補の数"]
        self.assertNotEqual(u"導出一致" if n == 1 else u"保留" if n >= 2 else u"不一致", r[u"V2"][u"K0 の判定"])

    def test_m_5_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_doc_variant_table_change_is_caught(self):
        k = self.rec[u"集計"][u"V1 の K0 の判定(手がかりあり)"]
        f = self.rec[u"集計"][u"V1 の全探索の判定(手がかりあり)"]
        h = self.rec[u"集計"][u"V1 の H までの判定(手がかりあり)"]
        tail = u"| %d | %d | %d | %d | %d | %d | %d | %d | %d |" % (k[u"導出一致"], k[u"保留"], k[u"不一致"], f[u"導出一致"], f[u"保留"], f[u"不一致"], h[u"導出一致"], h[u"保留"], h[u"不一致"])
        line = [l for l in self.doc.splitlines() if l.startswith(u"| **V1**") and l.endswith(tail)]
        self.assertEqual(len(line), 1)
        bad = self.doc.replace(line[0], line[0].replace(u"| %d |" % k[u"導出一致"], u"| %d |" % (k[u"導出一致"] - 1), 1))
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_7_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**0〜3**", u"**0〜30**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_8_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_9_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT).replace(u'load_module(MATERIALS[u"prev_script"]', u'load_module(MATERIALS[u"zip"]')), [])

    def test_m_10_same_fact_flag_flip_is_caught(self):
        rec = json.loads(self.rec_text)
        rows = [x for x in rec[u"行"] if x[u"母数"] and x[u"手がかりあり"] and x[u"V1"][u"K0 の判定"] == u"導出一致"]
        self.assertGreater(len(rows), 0)
        r = rows[0]
        r[u"V1"][u"V0 の候補と同じ fact"] = not r[u"V1"][u"V0 の候補と同じ fact"]
        T = ref_tally(rec[u"行"])
        self.assertNotEqual(T[u"誤受理で V0 の候補と同じ fact(合計)"], rec[u"集計"][u"誤受理で V0 の候補と同じ fact(合計)"])


if __name__ == "__main__":
    unittest.main()
