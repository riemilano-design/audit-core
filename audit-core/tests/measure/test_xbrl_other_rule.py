# -*- coding: utf-8 -*-
u"""門: 「その他」の行の主語の結びつき(封 docs/XBRL_OTHER_RULE_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/other_rule_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 H-1〜H-8 を、記録の集計と封 §4 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 415 行の数の位置・「同」の辿り・その他の行・期・u・R0・R1 の候補を、門自身の code で材料(claims・札・entry・ZIP)から作り直し、
  記録と全行一致させる(fact と計算リンクの読み方だけ全探索の便の script を使う)。
- 集計を行から数え直す。文書の表(§1・§2-2)・id・散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
- script が標準ライブラリ + 全探索の便の script(importlib)だけで engine を import しない。順序(封 < script・記録・文書・門)。変異で赤くなる。
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

SEAL_REL = "docs/XBRL_OTHER_RULE_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_OTHER_RULE_2026-11-02.md"
REC_REL = "fixtures/xbrl/other_rule_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_other_rule_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_other_rule.py"
SEAL_COMMIT_SHORT = "8d4cf3b"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"H-%d" % i for i in range(1, 9))
VERDICTS = (u"決まる", u"保留", u"無し")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "__future__"}
FORBIDDEN = (u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")

# 門自身の字(封 §1 を別に書く)
G_NUM = re.compile(u"(△|▲|-)?([0-9,]+(?:\\.[0-9]+)?)(百万円|千円|円|%|ポイント|名|人|株|社|件)")
G_SCALE = {u"百万円": 1000000.0, u"千円": 1000.0, u"円": 1.0}
G_OTHER = re.compile(u"その他(の[^、。::()()\\s]{0,8})?$")
G_TRAIL = set(u":" + u":" + u"、はがをでに 　")


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


# ---------------------------------------------------------------- 封 §4 の幅

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(H-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"H-1", u"H-2", u"H-7"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    b[u"H-3"] = float(re.search(r"\*\*(\d+)% 以下\*\*", rows[u"H-3"][0]).group(1))
    b[u"H-4"] = float(re.search(r"\*\*(\d+)% 以上\*\*", rows[u"H-4"][0]).group(1))
    b[u"H-5"] = float(re.search(r"\*\*(\d+)%\*\*", rows[u"H-5"][0]).group(1))
    b[u"H-6"] = int(re.search(r"\*\*(\d+) / \d+\*\*", rows[u"H-6"][0]).group(1))
    return b


# ---------------------------------------------------------------- 門自身の作り直し

def g_tokens(text):
    out = []
    for m in G_NUM.finditer(text or u""):
        d = m.group(2).replace(u",", u"")
        try:
            v = float(d)
        except ValueError:
            continue
        dec = len(d.split(u".")[1]) if u"." in d else 0
        out.append((m.start(), m.end(), m.group(0), v * G_SCALE.get(m.group(3), 1.0), m.group(3), dec))
    return out


def g_strip(w):
    while w and w[-1] in G_TRAIL:
        w = w[:-1]
    return w


def g_subject(text, toks, tok, hops=0):
    w = g_strip(text[:tok[0]])
    if w.endswith(u"(同") or w.endswith(u"(同"):
        prev = [k for k in toks if k[1] <= tok[0]]
        if not prev or hops >= 5:
            return w, True, True
        w2, _, none2 = g_subject(text, toks, prev[-1], hops + 1)
        return w2, True, none2
    return w, False, False


def g_band(v, t, u):
    d = abs(v) - abs(t)
    return abs(d) <= u / 2.0 or 0 <= d < u


def g_period(ctx, prior):
    return (u"_" not in ctx) and ctx.startswith(u"Prior1Year" if prior else u"CurrentYear")


def g_neigh(E, arcs):
    N = set([E])
    for p, ch in arcs.items():
        if E in ch:
            N.add(p)
            N.update(ch.keys())
    N.update(arcs.get(E, {}).keys())
    return N


def g_rows(claims, labels, entry_claims, facts, arcs):
    u"""記録の行と比べる欄だけを、門自身の code で作る。"""
    out = collections.OrderedDict()
    for c in claims:
        cid = c[u"id"]
        ec = entry_claims.get(cid) or {}
        text = c.get(u"文") or u""
        r = collections.OrderedDict([(u"数の位置", u"なし"), (u"その他の行", False), (u"期", None), (u"u", None), (u"同", None),
                                     (u"R0 の候補の数", None), (u"R0 の判定", None), (u"R1 の判定", None), (u"R1 の候補の数", None), (u"engine の要素 E", None)])
        if c.get(u"数") is not None:
            toks = g_tokens(text)
            t = abs(float(c[u"数"])) * G_SCALE.get(c.get(u"単位"), 1.0)
            hits = [k for k in toks if abs(k[3] - t) <= 1e-6 * max(1.0, t)]
            r[u"数の位置"] = u"決まる" if len(hits) == 1 else (u"曖昧" if hits else u"なし")
            if len(hits) == 1:
                tok = hits[0]
                w, same, none = g_subject(text, toks, tok)
                r[u"同"] = same
                r[u"その他の行"] = bool(not none and G_OTHER.search(w))
                if r[u"その他の行"]:
                    r[u"期"] = u"前期" if same else u"当期"
                    u = G_SCALE.get(tok[4], 1.0) * (10.0 ** (-tok[5]) if tok[5] else 1.0)
                    r[u"u"] = u
                    money = tok[4] in (u"円", u"千円", u"百万円")
                    c0 = [f for f in facts if f[u"name"].split(u":")[-1].startswith(u"Other") and (not money or f[u"unit"] == u"JPY")
                          and g_period(f[u"context"], same) and g_band(f[u"value"], tok[3], u)]
                    r[u"R0 の候補の数"] = len(c0)
                    r[u"R0 の判定"] = u"決まる" if len(c0) == 1 else (u"保留" if len(c0) >= 2 else u"無し")
                    ptrs = [p for p in (ec.get(u"pointers") or []) if re.match(r"^xbrl:[^@]+@[^@]+$", p)]
                    if ptrs:
                        E = ptrs[0][len(u"xbrl:"):].split(u"@")[0]
                        N = g_neigh(E, arcs)
                        c1 = [f for f in c0 if f[u"name"] in N]
                        r[u"engine の要素 E"] = E
                        r[u"R1 の候補の数"] = len(c1)
                        r[u"R1 の判定"] = u"決まる" if len(c1) == 1 else (u"保留" if len(c1) >= 2 else u"無し")
                    else:
                        r[u"R1 の判定"] = u"指せず"
        out[cid] = r
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    pop = [r for r in rows if r[u"その他の行"] and r[u"札"] == u"真"]
    oth = [r for r in rows if r[u"その他の行"]]
    T[u"claims"] = len(rows)
    T[u"数の位置"] = collections.OrderedDict((k, sum(1 for r in rows if r[u"数の位置"] == k)) for k in (u"決まる", u"なし", u"曖昧"))
    T[u"その他の行(札を問わず)"] = len(oth)
    T[u"その他の行(札 真)"] = len(pop)
    T[u"その他の行(札 真)の id"] = [r[u"id"] for r in pop]
    T[u"その他の行の期"] = collections.OrderedDict((k, sum(1 for r in pop if r[u"期"] == k)) for k in (u"当期", u"前期"))
    T[u"その他の行の state"] = collections.OrderedDict((s, sum(1 for r in pop if r[u"state"] == s)) for s in STATES)
    T[u"その他の行で GROUNDED の id"] = [r[u"id"] for r in pop if r[u"state"] == u"GROUNDED"]
    T[u"同(主語なし)の行"] = sum(1 for r in rows if r[u"同(主語なし)"])
    T[u"R0 の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"R0 の判定"] == v)) for v in VERDICTS)
    T[u"R0 で決まる割合"] = None if not pop else round(100.0 * T[u"R0 の判定"][u"決まる"] / len(pop), 1)
    T[u"R0 で決まった行で候補の要素が根拠に在る"] = sum(1 for r in pop if r[u"R0 で決まった候補の要素が根拠に在る"])
    T[u"R1 の判定"] = collections.OrderedDict((v, sum(1 for r in pop if r[u"R1 の判定"] == v)) for v in VERDICTS + (u"指せず",))
    r1 = [r for r in pop if r[u"R1 の判定"] in VERDICTS]
    T[u"R1 を当てた行(pointers あり)"] = len(r1)
    T[u"R1 で決まる割合(pointers あり)"] = None if not r1 else round(100.0 * T[u"R1 の判定"][u"決まる"] / len(r1), 1)
    T[u"R1 で決まった行で候補の要素が根拠に在る"] = sum(1 for r in pop if r[u"R1 で決まった候補の要素が根拠に在る"])
    n1 = T[u"R1 の判定"][u"決まる"]
    T[u"R1 で決まった行で候補の要素が根拠に在る割合"] = None if not n1 else round(100.0 * T[u"R1 で決まった行で候補の要素が根拠に在る"] / n1, 1)
    T[u"R1 で決まった行の id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"決まる"]
    T[u"R1 で決まった行で候補の要素が根拠に無い id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"決まる" and not r[u"R1 で決まった候補の要素が根拠に在る"]]
    T[u"R1 で保留の id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"保留"]
    T[u"R1 で無しの id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"無し"]
    T[u"R1 で指せずの id"] = [r[u"id"] for r in pop if r[u"R1 の判定"] == u"指せず"]
    byid = {r[u"id"]: r for r in rows}
    t5 = (u"N080", u"N081", u"N144", u"N145", u"N213", u"N290")
    T[u"配線: T5 の「その他」6 行が その他の行として拾われた"] = sum(1 for i in t5 if byid[i][u"その他の行"])
    T[u"配線: T5 の「その他」6 行で R1 が決まる"] = sum(1 for i in t5 if byid[i][u"R1 の判定"] == u"決まる")
    gr = [r for r in pop if r[u"state"] == u"GROUNDED"]
    T[u"GROUNDED の その他の行で engine の要素が Other"] = sum(1 for r in gr if r[u"engine の要素が Other"])
    T[u"GROUNDED の その他の行で engine の fact が R1 の候補に在る"] = sum(1 for r in gr if r[u"engine の fact が R1 の候補に在る"])
    T[u"その他の行(札 偽・判定不能)"] = len(oth) - len(pop)
    return T


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"H-1"] = b[u"H-1"][0] <= T[u"その他の行(札 真)"] <= b[u"H-1"][1]
    J[u"H-2"] = b[u"H-2"][0] <= T[u"その他の行の state"][u"GROUNDED"] <= b[u"H-2"][1]
    J[u"H-3"] = T[u"R0 で決まる割合"] is not None and T[u"R0 で決まる割合"] <= b[u"H-3"]
    J[u"H-4"] = T[u"R1 で決まる割合(pointers あり)"] is not None and T[u"R1 で決まる割合(pointers あり)"] >= b[u"H-4"]
    J[u"H-5"] = T[u"R1 で決まった行で候補の要素が根拠に在る割合"] is not None and T[u"R1 で決まった行で候補の要素が根拠に在る割合"] >= b[u"H-5"]
    J[u"H-6"] = T[u"配線: T5 の「その他」6 行が その他の行として拾われた"] == b[u"H-6"] and T[u"配線: T5 の「その他」6 行で R1 が決まる"] == b[u"H-6"]
    J[u"H-7"] = b[u"H-7"][0] <= T[u"数の位置"][u"曖昧"] <= b[u"H-7"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"H-8"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(H-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    n = T[u"その他の行(札 真)"]
    return {
        u"H-1": [u"%d" % n], u"H-2": [u"%d" % T[u"その他の行の state"][u"GROUNDED"]],
        u"H-3": [u"%s%%(%d / %d)" % (T[u"R0 で決まる割合"], T[u"R0 の判定"][u"決まる"], n)],
        u"H-4": [u"%s%%(%d / %d)" % (T[u"R1 で決まる割合(pointers あり)"], T[u"R1 の判定"][u"決まる"], T[u"R1 を当てた行(pointers あり)"])],
        u"H-5": [u"%s%%(%d / %d)" % (T[u"R1 で決まった行で候補の要素が根拠に在る割合"], T[u"R1 で決まった行で候補の要素が根拠に在る"], T[u"R1 の判定"][u"決まる"])],
        u"H-6": [u"拾われた %d / 6" % T[u"配線: T5 の「その他」6 行が その他の行として拾われた"], u"決まる %d / 6" % T[u"配線: T5 の「その他」6 行で R1 が決まる"]],
        u"H-7": [u"%d" % T[u"数の位置"][u"曖昧"]],
        u"H-8": [u"札 偽・判定不能 %d" % T[u"その他の行(札 偽・判定不能)"], u"位置なし %d" % T[u"数の位置"][u"なし"], u"GROUNDED %d" % T[u"その他の行の state"][u"GROUNDED"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が H-1〜H-8 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"H-8" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"H-1", u"H-2", u"H-7") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    # §2-2 の表: その他の行 1 行につき 1 行。id・state・期・R0 の候補の数・R1 の判定・根拠に在る
    byid = {r[u"id"]: r for r in rec[u"行"]}
    lines = [l for l in doc.splitlines() if re.match(r"^\| N\d{3} \|", l)]
    ids_in_table = [l.split(u" | ")[0][2:] for l in lines]
    if sorted(ids_in_table) != sorted(T[u"その他の行(札 真)の id"]) or len(ids_in_table) != len(T[u"その他の行(札 真)の id"]):
        p.append(u"§2-2 の表の id の列が記録と違う: %s" % ids_in_table)
    for l in lines:
        cells = [c.strip() for c in l.strip().strip(u"|").split(u"|")]
        if len(cells) != 9:
            p.append(u"§2-2 の表の欄が 9 でない: %s" % cells[0])
            continue
        r = byid.get(cells[0])
        if r is None or not r[u"その他の行"]:
            p.append(u"§2-2 の表に その他の行でない id %s" % cells[0])
            continue
        want = [r[u"state"], r[u"期"], u"%d" % r[u"R0 の候補の数"], r[u"R1 の判定"]]
        got = [cells[1], cells[2], cells[5], cells[6]]
        if got != want:
            p.append(u"§2-2 の %s の欄 %s が記録 %s と違う" % (cells[0], got, want))
        E = (r[u"engine の要素 E"] or u"").split(u":")[-1]
        if cells[4] != E:
            p.append(u"§2-2 の %s の engine の要素が %s でない" % (cells[0], E))
        if r[u"R1 の判定"] == u"決まる":
            cand = r[u"R1 の候補"][0][u"要素"].split(u":")[-1]
            if not cells[7].startswith(cand):
                p.append(u"§2-2 の %s の候補の要素が %s で始まらない" % (cells[0], cand))
            if cells[8] != (u"在る" if r[u"R1 で決まった候補の要素が根拠に在る"] else u"無い"):
                p.append(u"§2-2 の %s の根拠の欄" % cells[0])
        else:
            if cells[7] != u"―" or cells[8] != u"―":
                p.append(u"§2-2 の %s は決まっていないのに候補・根拠の欄が ― でない" % cells[0])
    for s in (u"位置が決まる %d・曖昧 %d・なし %d" % (T[u"数の位置"][u"決まる"] - 0, T[u"数の位置"][u"曖昧"], 0),
              u"数の無い %d" % T[u"数の位置"][u"なし"],
              u"`Other` で始まる要素は %d" % rec[u"配線の門"][u"(e) Other で始まる要素の数"],
              u"同(主語なし)の行 %d" % T[u"同(主語なし)の行"],
              u"R1 で決まる %d" % T[u"R1 の判定"][u"決まる"], u"R1 で無し %d" % T[u"R1 の判定"][u"無し"],
              u"engine の要素が Other %d" % T[u"GROUNDED の その他の行で engine の要素が Other"],
              u"engine の fact が R1 の候補に在る %d" % T[u"GROUNDED の その他の行で engine の fact が R1 の候補に在る"]):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    for i in T[u"R1 で無しの id"] + T[u"その他の行で GROUNDED の id"] + T[u"R1 で決まった行で候補の要素が根拠に無い id"]:
        if i not in doc:
            p.append(u"id %s が文書に無い" % i)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"H-\d+|J-\d+|R\d|T\d|P\d+|§\d+(-\d+)*", u" ", s)
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
        if m != "full_script":
            p.append(u"importlib で読む材料が全探索の便の script でない: %s" % m)
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
        cls.mod = load(SCRIPT, "other_rule_under_test")
        M = cls.mod.MATERIALS
        cls.full = load(os.path.join(ROOT, M[u"full_script"][0]), "derivation_full_for_other_rule_gate")
        cls.claims = jload(os.path.join(ROOT, M[u"claims"][0]))[u"claims"]
        cls.labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, M[u"labels"][0]))[u"labels"]}
        cls.entry = jload(os.path.join(ROOT, M[u"entry"][0]))
        cls.entry_claims = {c[u"id"]: c for c in cls.entry[u"claims"]}
        zpath = os.path.join(ROOT, M[u"zip"][0])
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
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        self.assertEqual(W[u"(e) Other で始まる要素の数"], len(set(f[u"name"] for f in self.facts if f[u"name"].split(u":")[-1].startswith(u"Other"))))
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(len(self.mod.MATERIALS), 6)
        self.assertEqual(self.rec_text.count("scratchpad"), 0)
        self.assertEqual(self.mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        self.assertEqual(len(self.rec[u"行"]), 415)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_b_1_rows_recomputed_by_the_script(self):
        rows = self.mod.build_rows(self.claims, self.labels, self.entry_claims, self.facts, self.arcs)
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(self.mod.judge(self.mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_rows_recomputed_with_the_gates_own_code(self):
        ref = g_rows(self.claims, self.labels, self.entry_claims, self.facts, self.arcs)
        self.assertEqual(list(ref.keys()), [r[u"id"] for r in self.rec[u"行"]])
        for r in self.rec[u"行"]:
            x = ref[r[u"id"]]
            for k in (u"数の位置", u"その他の行", u"期", u"u", u"同", u"R0 の候補の数", u"R0 の判定", u"R1 の判定", u"R1 の候補の数", u"engine の要素 E"):
                self.assertEqual(r[k], x[k], u"%s %s" % (r[u"id"], k))
            self.assertEqual(r[u"札"], self.labels[r[u"id"]][u"札"])
            self.assertEqual(r[u"state"], (self.entry_claims.get(r[u"id"]) or {}).get(u"state"))
            if r[u"その他の行"]:
                g = self.labels[r[u"id"]].get(u"根拠") or u""
                for c in r[u"R0 の候補"]:
                    self.assertTrue(c[u"要素"].split(u":")[-1].startswith(u"Other"))
                    self.assertTrue(g_period(c[u"context"], r[u"期"] == u"前期"))
                    self.assertTrue(g_band(c[u"v"], abs(r[u"数"]) * G_SCALE.get(r[u"単位"], 1.0), r[u"u"]))
                for c in r[u"R1 の候補"]:
                    self.assertIn(c, r[u"R0 の候補"])
                    self.assertIn(c[u"要素"], g_neigh(r[u"engine の要素 E"], self.arcs))
                if r[u"R1 の判定"] == u"決まる":
                    self.assertEqual(r[u"R1 で決まった候補の要素が根拠に在る"], r[u"R1 の候補"][0][u"要素"].split(u":")[-1] in g)
                else:
                    self.assertIsNone(r[u"R1 で決まった候補の要素が根拠に在る"])
                if r[u"R0 の判定"] == u"決まる":
                    self.assertEqual(r[u"R0 で決まった候補の要素が根拠に在る"], r[u"R0 の候補"][0][u"要素"].split(u":")[-1] in g)
            else:
                self.assertIsNone(r[u"R0 の判定"])
                self.assertIsNone(r[u"R1 の判定"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 7)
        want = dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items())
        self.assertEqual(want, dict(self.bounds), u"script の幅が封の字と違う")

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"H-1": (8, 20), u"H-2": (0, 3), u"H-3": 40.0, u"H-4": 60.0, u"H-5": 100.0, u"H-6": 6, u"H-7": (0, 2)})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_imports_and_rules_on_synthetic_text(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m = self.mod
        text = u"不動産賃貸料15百万円(同15百万円)、その他37百万円(同35百万円)です。"
        toks, hits = m.locate(text, 37.0, u"百万円")
        self.assertEqual(len(hits), 1)
        w, same, none = m.subject_of(text, toks, hits[0])
        self.assertTrue(m.is_other(w) and not same)
        toks, hits = m.locate(text, 35000000.0, u"円")
        self.assertEqual(len(hits), 1)
        w, same, none = m.subject_of(text, toks, hits[0])
        self.assertTrue(m.is_other(w) and same and not none)             # (同 → 直前の「その他」へ辿る
        toks, hits = m.locate(text, 15.0, u"百万円")
        self.assertEqual(len(hits), 2)                                    # 位置が曖昧
        self.assertTrue(m.is_other(u"- その他の流動資産"))
        self.assertFalse(m.is_other(u"その他有価証券評価差額金"))
        self.assertFalse(m.is_other(u"「その他」の販管費"))
        self.assertEqual(m.subject_of(u"(同15百万円)", m.tokens_of(u"(同15百万円)"), m.tokens_of(u"(同15百万円)")[0])[1:], (True, True))   # 同(主語なし)
        self.assertEqual(m.u_of({u"単位": u"百万円", u"小数": 0}), 1e6)
        self.assertEqual(m.u_of({u"単位": u"%", u"小数": 1}), 0.1)
        self.assertTrue(m.in_engine_band(37144000.0, 37e6, 1e6))          # truncate
        self.assertTrue(m.in_engine_band(36600000.0, 37e6, 1e6))          # round
        self.assertFalse(m.in_engine_band(38200000.0, 37e6, 1e6))
        self.assertTrue(m.period_ok(u"CurrentYearInstant", False) and m.period_ok(u"Prior1YearDuration", True))
        self.assertFalse(m.period_ok(u"CurrentYearDuration_jppfs_cor_XMember", False))
        self.assertFalse(m.period_ok(u"Prior1YearDuration", False))
        arcs = {u"a:P": {u"a:E": 1.0, u"a:OtherX": 1.0}, u"a:E": {u"a:C": 1.0}}
        self.assertEqual(m.neighbourhood(u"a:E", arcs), set([u"a:E", u"a:P", u"a:C", u"a:OtherX"]))

    def test_f_2_r1_narrows_r0_on_a_synthetic_row(self):
        u"""R0 が 2 以上で R1 が 1 になる合成の行(この書類の 12 行は R0 と R1 が同じなので、絞りは合成でしか縛れない)。"""
        m = self.mod
        facts = [{u"name": u"a:OtherX", u"context": u"CurrentYearInstant", u"unit": u"JPY", u"value": 37144000.0, u"g": 1000.0},
                 {u"name": u"a:OtherFar", u"context": u"CurrentYearInstant", u"unit": u"JPY", u"value": 37500000.0, u"g": 1000.0},
                 {u"name": u"a:OtherX", u"context": u"Prior1YearInstant", u"unit": u"JPY", u"value": 37100000.0, u"g": 1000.0},
                 {u"name": u"a:OtherX", u"context": u"CurrentYearInstant_a_XMember", u"unit": u"JPY", u"value": 37200000.0, u"g": 1000.0}]
        arcs = {u"a:P": {u"a:E": 1.0, u"a:OtherX": 1.0}, u"a:Q": {u"a:OtherFar": 1.0}}
        claims = [{u"id": u"N900", u"文": u"賃貸料15百万円、その他37百万円です。", u"数": 37.0, u"単位": u"百万円"}]
        labels = {u"N900": {u"札": u"真", u"根拠": u"a:OtherX/CY=37,144,000円"}}
        entry = {u"N900": {u"state": u"VALUE_MISMATCH", u"pointers": [u"xbrl:a:E@CurrentYearInstant"]}}
        r = m.build_rows(claims, labels, entry, facts, arcs)[0]
        self.assertTrue(r[u"その他の行"])
        self.assertEqual((r[u"期"], r[u"u"]), (u"当期", 1e6))
        self.assertEqual((r[u"R0 の候補の数"], r[u"R0 の判定"]), (2, u"保留"))          # OtherX 当期と OtherFar(前期・member は除く)
        self.assertEqual((r[u"R1 の候補の数"], r[u"R1 の判定"]), (1, u"決まる"))          # 近傍(a:P の子)にあるのは OtherX だけ
        self.assertEqual(r[u"R1 の候補"][0][u"要素"], u"a:OtherX")
        self.assertTrue(r[u"R1 で決まった候補の要素が根拠に在る"])
        g = g_rows(claims, labels, entry, facts, arcs)[u"N900"]
        self.assertEqual((g[u"R0 の判定"], g[u"R1 の判定"]), (u"保留", u"決まる"))
        # pointers が無ければ 指せず
        r = m.build_rows(claims, labels, {u"N900": {u"state": u"POINTER_NOT_FOUND", u"pointers": []}}, facts, arcs)[0]
        self.assertEqual(r[u"R1 の判定"], u"指せず")

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
        rec[u"予測の判定"][u"H-3"] = u"当たり" if rec[u"予測の判定"][u"H-3"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"R1 の判定"][u"決まる"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"R1 の判定"], rec[u"集計"][u"R1 の判定"])

    def test_m_3_moving_a_row_verdict_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"R1 の判定"] == u"無し"][0]
        r[u"R1 の判定"] = u"決まる"
        self.assertNotEqual(u"決まる" if r[u"R1 の候補の数"] == 1 else u"保留" if r[u"R1 の候補の数"] >= 2 else u"無し", r[u"R1 の判定"])

    def test_m_4_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_5_doc_row_table_change_is_caught(self):
        line = [l for l in self.doc.splitlines() if l.startswith(u"| N162 |")][0]
        bad = self.doc.replace(line, line.replace(u"| 無し |", u"| 決まる |", 1), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        bad = self.doc.replace(line + u"\n", u"", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        line = [l for l in self.doc.splitlines() if l.startswith(u"| N080 |")][0]
        bad = self.doc.replace(line, line.replace(u"| 在る |", u"| 無い |", 1), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**40% 以下**", u"**70% 以下**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_7_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_8_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT).replace(u'load_module(MATERIALS[u"full_script"]', u'load_module(MATERIALS[u"zip"]')), [])

    def test_m_9_rule_change_in_record_is_caught(self):
        u"""記録の R0 の候補を 1 つ落としても(規則の緩め)門自身の作り直しと食い違う。"""
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"R0 の判定"] == u"決まる"][0]
        r[u"R0 の候補の数"] = 2
        claims = jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json"))[u"claims"]
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_labels_2026-10-09.json"))[u"labels"]}
        entry = {c[u"id"]: c for c in jload(os.path.join(ROOT, "fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json"))[u"claims"]}
        full = load(os.path.join(ROOT, "measure/xbrl_derivation_full_2026-11-02.py"), "derivation_full_for_other_rule_mut")
        zpath = os.path.join(ROOT, "fixtures/xbrl/ai_prose_instance_2026-10-09.zip")
        facts, _ = full.parse_facts(zpath)
        arcs, _ = full.parse_cal(zpath)
        self.assertNotEqual(g_rows(claims, labels, entry, facts, arcs)[r[u"id"]][u"R0 の候補の数"], r[u"R0 の候補の数"])

    def test_m_10_dropping_an_id_from_the_doc_is_caught(self):
        for i in (u"N162", u"N299"):
            bad = self.doc.replace(i, u"N000")
            self.assertNotEqual(bad, self.doc)
            self.assertNotEqual(table_problems(bad, self.rec), [])


if __name__ == "__main__":
    unittest.main()
