# -*- coding: utf-8 -*-
u"""門: AI の文を P27E と P27 で再判定する便(封 docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md)。

縛る物:
- 封の字(§0 の材料 8 本の sha256・§1 の出力 file 名・§3 の幅)と script の定数が一致する。script は engine を import して走らせる
  (儀式の script と同じ)が、網(urllib・http・socket)を使わず、engine の字(core/・adapters/)を書かない。
- script の engine を使わない部分(行の対応・根拠の形・期・集計・判定・docID の消し込み)を、P16 の記録を新しい記録の代わりに流して
  (ラベル file が無くても走る)確かめる。53 行・12 行・8 行・249 行の数が材料と一致する。
- 記録 fixtures/xbrl/rerun_p27e_2026-11-02.json が在るとき: 形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)、
  entry 2 つの形(profile・zip の sha256・claim の数・state の分布)、行を門自身の code で作り直し、集計を数え直し、
  予測 M-1〜M-10 を封の幅から求め直し、文書の表と散文の 3 桁以上の数を記録に縛る。記録が無ければ skip(封 §5)。
- 順序(封 < script・記録・文書・門)。変異で赤くなる(記録が無い間は P16 を流した代わりの記録で)。
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

SEAL_REL = "docs/XBRL_P27E_RERUN_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_P27E_RERUN_2026-11-02.md"
REC_REL = "fixtures/xbrl/rerun_p27e_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_rerun_p27e_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_rerun_p27e.py"
ENTRY_RELS = collections.OrderedDict([(u"P27E", "fixtures/xbrl/entry_output_ai_prose_p27e_2026-11-02.json"), (u"P27", "fixtures/xbrl/entry_output_ai_prose_p27_2026-11-02.json")])
SEAL_COMMIT_SHORT = "35f624c"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"M-%d" % i for i in range(1, 11))
PROFILES = (u"P27E", u"P27")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
TYPES_T = (u"T1 指せず", u"T2 同じ fact", u"T3 導出の量", u"T4 同じ要素・別の期", u"T5 別の要素", u"T6 導出も決めない")
FORMS = (u"同(略した根拠)", u"数式(導出の文)", u"要素名を書きうる")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "importlib", "io", "json", "os", "re", "subprocess", "sys", "__future__", "adapters"}
ALLOWED_ENGINE = {"adapters.xbrl", "adapters.xbrl.instance", "adapters.xbrl.verify_document"}
FORBIDDEN = (u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def jtext(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 封の字

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(M-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    m = re.search(r"\((\d+)・(\d+)・(\d+)・(\d+)\)", rows[u"M-1"][0])
    b[u"M-1"] = collections.OrderedDict(zip((u"GROUNDED", u"POINTER_NOT_FOUND", u"UNVERIFIABLE", u"VALUE_MISMATCH"), (int(x) for x in m.groups())))
    b[u"M-2"] = int(re.search(r"\*\*(\d+) / \d+\*\*", rows[u"M-2"][0]).group(1))
    for i in (u"M-3", u"M-4", u"M-5", u"M-6", u"M-7", u"M-9"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    return b


def seal_materials(seal):
    u"""§0 の表: file → sha256。"""
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| [^|]+ \| `([^`]+)` \| `([0-9a-f]{64})` \|\s*$", l)
        if m:
            out[m.group(1)] = m.group(2)
    return out


# ---------------------------------------------------------------- 門自身の作り直し(script とは別に書く)

def g_key(c):
    return (c.get(u"span"), c.get(u"value"), c.get(u"unit"))


def g_align(old, new):
    m, used = collections.OrderedDict(), set()
    for i, c in enumerate(old):
        if i < len(new) and g_key(new[i]) == g_key(c):
            m[c[u"id"]] = new[i]
            used.add(i)
        else:
            m[c[u"id"]] = None
    for c in old:
        if m[c[u"id"]] is None:
            for j, n in enumerate(new):
                if j not in used and g_key(n) == g_key(c):
                    m[c[u"id"]], _ = n, used.add(j)
                    break
    return m


def g_period(pointers):
    for p in pointers or []:
        mm = re.match(r"^xbrl:[^@]+@([A-Za-z0-9_\-]+)$", p)
        if mm:
            return u"当期" if mm.group(1).startswith(u"CurrentYear") else (u"前期" if mm.group(1).startswith(u"Prior1Year") else u"他")
    return None


def g_in_grounds(pointers, grounds):
    els = [re.match(r"^xbrl:([^@]+)@", p).group(1) for p in pointers or [] if re.match(r"^xbrl:([^@]+)@", p)]
    return None if not els else any(e.split(u":")[-1] in (grounds or u"") for e in els)


def g_form(form, grounds):
    g = grounds or u""
    return FORMS[0] if g.startswith(u"同") else (FORMS[1] if form == u"derived_value" else FORMS[2])


def g_sets(stopped, other, period):
    return {u"53": collections.OrderedDict((r[u"id"], r[u"型"]) for r in stopped[u"行"]),
            u"12": collections.OrderedDict((r[u"id"], r[u"R1 の判定"]) for r in other[u"行"] if r[u"その他の行"] and r[u"札"] == u"真"),
            u"8": collections.OrderedDict((r[u"id"], True) for r in period[u"行"] if r.get(u"取り違えの中身(参考)") == u"札が文の期と合う(engine の期の取り違え)" and r.get(u"取り違え(engine)") == u"前期の文 × engine 当期")}


def g_rows(entry16, new_entries, labels, sets):
    maps = dict((pf, g_align(entry16[u"claims"], new_entries[pf][u"claims"])) for pf in PROFILES)
    out = collections.OrderedDict()
    for c in entry16[u"claims"]:
        cid, lab = c[u"id"], labels.get(c[u"id"]) or {}
        r = collections.OrderedDict([(u"札", lab.get(u"札")), (u"kind", c.get(u"kind")), (u"P16 の state", c.get(u"state"))])
        for pf in PROFILES:
            n = maps[pf][cid]
            r[u"%s で対応" % pf] = n is not None
            r[u"%s の state" % pf] = n.get(u"state") if n else None
            r[u"%s の期" % pf] = g_period(n.get(u"pointers")) if n else None
            r[u"%s で GROUNDED の要素が根拠に在る" % pf] = g_in_grounds(n.get(u"pointers"), lab.get(u"根拠")) if (n and n.get(u"state") == u"GROUNDED" and lab.get(u"札") == u"真") else None
        r[u"P27E と P27 で state が違う"] = (r[u"P27E の state"] != r[u"P27 の state"]) if (r[u"P27E で対応"] and r[u"P27 で対応"]) else None
        r[u"根拠の形(参考)"] = g_form(c.get(u"form"), lab.get(u"根拠"))
        r[u"53 行"], r[u"型(53 行)"] = cid in sets[u"53"], sets[u"53"].get(cid)
        r[u"12 行"], r[u"R1 の判定(12 行)"] = cid in sets[u"12"], sets[u"12"].get(cid)
        r[u"8 行"] = cid in sets[u"8"]
        r[u"249 行(P16 で GROUNDED・札 真・num)"] = lab.get(u"札") == u"真" and c.get(u"kind") == u"num" and c.get(u"state") == u"GROUNDED"
        out[cid] = r
    return out


def _d(items):
    items = list(items)  # 2026-11-02: 生成器を 1 回で使い切り GROUNDED 以外が 0 になる欠陥の直し(script の _dist と同じ型。desktop の実走で発覚)
    return collections.OrderedDict((s, sum(1 for x in items if x == s)) for s in STATES)


def ref_tally(rows):
    u"""記録の「行」から集計を数え直す(entry の全 claim の分布は entry から別に見る)。"""
    T = collections.OrderedDict()
    T[u"P16 の claim"] = len(rows)
    pop = [r for r in rows if r[u"札"] == u"真" and r[u"kind"] == u"num"]
    T[u"札 真・num の行"] = len(pop)
    for pf in PROFILES:
        T[u"%s で対応した行" % pf] = sum(1 for r in rows if r[u"%s で対応" % pf])
        T[u"P16 → %s の state(札 真・num)" % pf] = collections.OrderedDict((s, _d(r[u"%s の state" % pf] for r in pop if r[u"P16 の state"] == s)) for s in STATES)
    s53 = [r for r in rows if r[u"53 行"]]
    T[u"53 行"] = len(s53)
    for pf in PROFILES:
        T[u"53 行の %s の state" % pf] = _d(r[u"%s の state" % pf] for r in s53)
        T[u"53 行で %s で GROUNDED" % pf] = sum(1 for r in s53 if r[u"%s の state" % pf] == u"GROUNDED")
        T[u"53 行で %s で GROUNDED の id" % pf] = [r[u"id"] for r in s53 if r[u"%s の state" % pf] == u"GROUNDED"]
        T[u"53 行で %s で GROUNDED(型ごと)" % pf] = collections.OrderedDict((t, sum(1 for r in s53 if r[u"型(53 行)"] == t and r[u"%s の state" % pf] == u"GROUNDED")) for t in TYPES_T)
        T[u"53 行で %s で GROUNDED の要素が根拠に在る" % pf] = sum(1 for r in s53 if r[u"%s の state" % pf] == u"GROUNDED" and r[u"%s で GROUNDED の要素が根拠に在る" % pf])
    s12 = [r for r in rows if r[u"12 行"]]
    T[u"12 行"] = len(s12)
    for pf in PROFILES:
        T[u"12 行の %s の state" % pf] = _d(r[u"%s の state" % pf] for r in s12)
        T[u"12 行で P16 が VALUE_MISMATCH の 9 行のうち %s で GROUNDED" % pf] = sum(1 for r in s12 if r[u"P16 の state"] == u"VALUE_MISMATCH" and r[u"%s の state" % pf] == u"GROUNDED")
        T[u"12 行で R1 が決まった 8 行のうち %s で GROUNDED" % pf] = sum(1 for r in s12 if r[u"R1 の判定(12 行)"] == u"決まる" and r[u"%s の state" % pf] == u"GROUNDED")
        T[u"12 行で %s で GROUNDED の id" % pf] = [r[u"id"] for r in s12 if r[u"%s の state" % pf] == u"GROUNDED"]
    T[u"12 行で P16 が VALUE_MISMATCH"] = sum(1 for r in s12 if r[u"P16 の state"] == u"VALUE_MISMATCH")
    s8 = [r for r in rows if r[u"8 行"]]
    T[u"8 行"] = len(s8)
    for pf in PROFILES:
        T[u"8 行の %s の state" % pf] = _d(r[u"%s の state" % pf] for r in s8)
        T[u"8 行で %s で GROUNDED" % pf] = sum(1 for r in s8 if r[u"%s の state" % pf] == u"GROUNDED")
        T[u"8 行の %s の期" % pf] = collections.OrderedDict((k, sum(1 for r in s8 if r[u"%s の期" % pf] == k)) for k in (u"当期", u"前期", u"他", None))
        T[u"8 行の %s の state と期(id ごと)" % pf] = collections.OrderedDict((r[u"id"], u"%s / %s" % (r[u"%s の state" % pf], r[u"%s の期" % pf])) for r in s8)
    g249 = [r for r in rows if r[u"249 行(P16 で GROUNDED・札 真・num)"]]
    T[u"249 行"] = len(g249)
    for pf in PROFILES:
        # 2026-11-02: 対応しない行(新しい state が無い)は「GROUNDED でなくなった」に数えず、数だけ別に持つ(封 §2「対応しない行は数だけ」)
        T[u"249 行で %s で対応しない" % pf] = sum(1 for r in g249 if not r[u"%s の state" % pf])
        T[u"249 行で %s で GROUNDED でなくなった" % pf] = sum(1 for r in g249 if r[u"%s の state" % pf] and r[u"%s の state" % pf] != u"GROUNDED")
        T[u"249 行で %s で GROUNDED でなくなった id" % pf] = [r[u"id"] for r in g249 if r[u"%s の state" % pf] and r[u"%s の state" % pf] != u"GROUNDED"]
        T[u"249 行で %s で GROUNDED でなくなった state" % pf] = _d(r[u"%s の state" % pf] for r in g249 if r[u"%s の state" % pf] and r[u"%s の state" % pf] != u"GROUNDED")
    both = [r for r in rows if r[u"P27E と P27 で state が違う"] is not None]
    T[u"P27E と P27 で state が違う行"] = sum(1 for r in both if r[u"P27E と P27 で state が違う"])
    T[u"P27E と P27 で state が違う id"] = [r[u"id"] for r in both if r[u"P27E と P27 で state が違う"]]
    T[u"P27E と P27 で state が違う行(P27E → P27)"] = collections.OrderedDict((r[u"id"], u"%s → %s" % (r[u"P27E の state"], r[u"P27 の state"])) for r in both if r[u"P27E と P27 で state が違う"])
    for pf in PROFILES:
        gr = [r for r in pop if r[u"%s の state" % pf] == u"GROUNDED"]
        T[u"%s で GROUNDED の 札 真・num" % pf] = len(gr)
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い" % pf] = sum(1 for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False)
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い id" % pf] = [r[u"id"] for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False]
        T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い(根拠の形ごと。参考)" % pf] = collections.OrderedDict(
            (f, sum(1 for r in gr if r[u"%s で GROUNDED の要素が根拠に在る" % pf] is False and r[u"根拠の形(参考)"] == f)) for f in FORMS)
    fake = [r for r in rows if r[u"札"] == u"偽"]
    T[u"札 偽 の行"] = collections.OrderedDict((r[u"id"], collections.OrderedDict([(u"P16", r[u"P16 の state"])] + [(pf, r[u"%s の state" % pf]) for pf in PROFILES])) for r in fake)
    T[u"札 偽 が P27E・P27 とも GROUNDED でない"] = all(r[u"%s の state" % pf] != u"GROUNDED" for r in fake for pf in PROFILES) if fake else None
    T[u"判定不能 の行"] = sum(1 for r in rows if r[u"札"] == u"判定不能")
    T[u"札の無い行(P16 の entry にあって札に無い)"] = sum(1 for r in rows if r[u"札"] is None)
    return T


def ref_judge(T, b, p27_dist, align_counts):
    J = collections.OrderedDict()
    J[u"M-1"] = dict(p27_dist) == dict(b[u"M-1"])
    J[u"M-2"] = all(align_counts[pf][u"同じ位置で対応"] == b[u"M-2"] and align_counts[pf][u"対応しない P16 の行"] == 0 for pf in PROFILES) and T[u"P16 の claim"] == b[u"M-2"]
    J[u"M-3"] = b[u"M-3"][0] <= T[u"53 行で P27E で GROUNDED"] <= b[u"M-3"][1]
    J[u"M-4"] = b[u"M-4"][0] <= T[u"249 行で P27E で GROUNDED でなくなった"] <= b[u"M-4"][1]
    J[u"M-5"] = b[u"M-5"][0] <= T[u"8 行で P27E で GROUNDED"] <= b[u"M-5"][1]
    J[u"M-6"] = b[u"M-6"][0] <= T[u"12 行で P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED"] <= b[u"M-6"][1]
    J[u"M-7"] = b[u"M-7"][0] <= T[u"P27E と P27 で state が違う行"] <= b[u"M-7"][1]
    J[u"M-8"] = T[u"札 偽 が P27E・P27 とも GROUNDED でない"] is True
    J[u"M-9"] = b[u"M-9"][0] <= T[u"P27E で GROUNDED の 札 真・num のうち要素が根拠に無い"] <= b[u"M-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"M-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


# ---------------------------------------------------------------- 文書(結果の文書が従う形。記録から作る)

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(M-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(rec):
    T, W = rec[u"集計"], rec[u"配線の門"]
    d27 = T[u"P27 の state の分布(全 claim)"]
    return {
        u"M-1": [u"%d・%d・%d・%d" % (d27[u"GROUNDED"], d27[u"POINTER_NOT_FOUND"], d27[u"UNVERIFIABLE"], d27[u"VALUE_MISMATCH"])],
        u"M-2": [u"%d / %d" % (W[u"(e) 行の対応"][pf][u"同じ位置で対応"], T[u"P16 の claim"]) for pf in PROFILES],
        u"M-3": [u"%d" % T[u"53 行で P27E で GROUNDED"]], u"M-4": [u"%d" % T[u"249 行で P27E で GROUNDED でなくなった"]],
        u"M-5": [u"%d" % T[u"8 行で P27E で GROUNDED"]], u"M-6": [u"%d" % T[u"12 行で P16 が VALUE_MISMATCH の 9 行のうち P27E で GROUNDED"]],
        u"M-7": [u"%d" % T[u"P27E と P27 で state が違う行"]],
        u"M-8": [u"P27E %s・P27 %s" % tuple(T[u"札 偽 の行"][i][pf] for i in list(T[u"札 偽 の行"].keys())[:1] for pf in PROFILES)],
        u"M-9": [u"%d" % T[u"P27E で GROUNDED の 札 真・num のうち要素が根拠に無い"]],
        u"M-10": [u"判定不能 %d" % T[u"判定不能 の行"]],
    }


def expected_lines(rec, p16_dist):
    u"""文書に字どおり在るべき行と句。"""
    T = rec[u"集計"]
    L = []
    for name, d in ((u"P16", p16_dist), (u"P27E", T[u"P27E の state の分布(全 claim)"]), (u"P27", T[u"P27 の state の分布(全 claim)"])):
        L.append(u"| **%s** | %d | %d | %d | %d |" % ((name,) + tuple(d[s] for s in STATES)))
    for pf in PROFILES:
        for s in STATES:
            X = T[u"P16 → %s の state(札 真・num)" % pf][s]
            L.append(u"| %s | **%s** | %d | %d | %d | %d |" % ((pf, s) + tuple(X[t] for t in STATES)))
    n53 = collections.Counter(r[u"型(53 行)"] for r in rec[u"行"] if r[u"53 行"])
    for t in TYPES_T:
        L.append(u"| **%s** | %d | %d | %d |" % (t, n53[t], T[u"53 行で P27E で GROUNDED(型ごと)"][t], T[u"53 行で P27 で GROUNDED(型ごと)"][t]))
    for i in T[u"8 行の P27E の state と期(id ごと)"]:
        L.append(u"| %s | %s | %s |" % (i, T[u"8 行の P27E の state と期(id ごと)"][i], T[u"8 行の P27 の state と期(id ごと)"][i]))
    for pf in PROFILES:
        F = T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い(根拠の形ごと。参考)" % pf]
        L.append(u"| **%s** | %d | %d | %d | %d |" % ((pf, T[u"%s で GROUNDED の 札 真・num のうち要素が根拠に無い" % pf]) + tuple(F[f] for f in FORMS)))
    L.append(u"53 行で P27E で GROUNDED %d" % T[u"53 行で P27E で GROUNDED"])
    L.append(u"53 行で P27 で GROUNDED %d" % T[u"53 行で P27 で GROUNDED"])
    L.append(u"249 行で P27E で GROUNDED でなくなった %d" % T[u"249 行で P27E で GROUNDED でなくなった"])
    L.append(u"249 行で P27 で GROUNDED でなくなった %d" % T[u"249 行で P27 で GROUNDED でなくなった"])
    L.append(u"P27E と P27 で state が違う行 %d" % T[u"P27E と P27 で state が違う行"])
    L.append(u"12 行で R1 が決まった 8 行のうち P27E で GROUNDED %d" % T[u"12 行で R1 が決まった 8 行のうち P27E で GROUNDED"])
    return L


def table_problems(doc, rec, p16_dist):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が M-1〜M-10 でない: %s" % list(rows.keys())]
    J = rec[u"予測の判定"]
    exp = expected_cells(rec)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"M-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"M-3", u"M-4", u"M-5", u"M-6", u"M-7", u"M-9") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if misses and u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    for s in expected_lines(rec, p16_dist):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    T = rec[u"集計"]
    for i in (T[u"53 行で P27E で GROUNDED の id"] + T[u"249 行で P27E で GROUNDED でなくなった id"] + T[u"P27E と P27 で state が違う id"]
              + T[u"12 行で P27E で GROUNDED の id"] + list(T[u"札 偽 の行"].keys())):
        if i not in doc:
            p.append(u"id %s が文書に無い" % i)
    for key in (u"53 行で P27E で GROUNDED の id", u"249 行で P27E で GROUNDED でなくなった id", u"P27E と P27 で state が違う id"):
        if T[key] and u"(%s)" % u"・".join(T[key]) not in doc:
            p.append(u"%s の列(括弧の中・順も同じ)が文書に無い" % key)
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"M-\d+|R\d|T\d|P\d+|§\d+(-\d+)*", u" ", s)
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
                if a.name.split(".")[0] not in ALLOWED_IMPORTS or (a.name.startswith("adapters") and a.name not in ALLOWED_ENGINE):
                    p.append(u"import %s" % a.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] not in ALLOWED_IMPORTS or (mod.startswith("adapters") and mod not in ALLOWED_ENGINE):
                p.append(u"from %s import" % mod)
            elif mod.startswith("adapters"):
                for a in node.names:
                    if "%s.%s" % (mod, a.name) not in ALLOWED_ENGINE:
                        p.append(u"from %s import %s" % (mod, a.name))
    for bad in ("urllib", "http", "socket", "requests", "core", "audit_core"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_open = (isinstance(node.func, ast.Attribute) and node.func.attr == "open") or (isinstance(node.func, ast.Name) and node.func.id == "open")
        if not is_open or not node.args:
            continue
        modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)] + [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
        if any(str(m).startswith(("w", "a", "x")) or "+" in str(m) for m in modes):
            target = ast.get_source_segment(src, node.args[0])
            if target not in ("os.path.join(ROOT, rel)", "a.out"):
                p.append(u"決めた出力の外に書く: %s" % target)
    if re.search(r'verify_document\([^)]*"P16"', src):
        p.append(u"P16 で走らせている")
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
    for rel in (SCRIPT_REL, REC_REL, DOC_REL, GATE_REL) + tuple(ENTRY_RELS.values()):
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue                                       # まだ無い file(記録・文書)は順序を問わない(封 §5: ラベル file が無ければ記録は無い)
        a = added_commits(PREFIX + rel)
        if not a:
            p.append(u"%s を足した commit が無い(未 commit)" % rel)
            continue
        if a[-1] == S or not is_anc(S, a[-1]):
            p.append(u"%s が封の後でない" % rel)
    return p


# ---------------------------------------------------------------- 材料(封 §0。ラベル file が無くても読める)

class Materials(object):
    _cache = None

    @classmethod
    def get(cls):
        if cls._cache is None:
            mod = load(SCRIPT, "rerun_p27e_under_test")
            M = mod.MATERIALS
            rel = lambda k: os.path.join(ROOT, M[k][0])
            entry16 = jload(rel(u"entry16"))
            labels = {x[u"id"]: x for x in jload(rel(u"labels"))[u"labels"]}
            sets = g_sets(jload(rel(u"stopped")), jload(rel(u"other")), jload(rel(u"period")))
            cls._cache = (mod, entry16, labels, sets)
        return cls._cache


def proxy_record(mod, entry16, labels, sets):
    u"""P16 の entry を新しい entry の代わりに流した、記録の形の物(ラベル file が無くても作れる。変異の試験と script の確かめに使う)。"""
    new = collections.OrderedDict((pf, entry16) for pf in PROFILES)
    rows, ac = mod.build_rows(entry16, new, labels, sets)
    T = mod.tally(rows, new)
    rec = collections.OrderedDict([(u"行", rows), (u"集計", T), (u"予測の判定", mod.judge(T, ac)),
                                   (u"配線の門", collections.OrderedDict([(u"(e) 行の対応", ac)]))])
    return json.loads(json.dumps(rec, ensure_ascii=False))


# ================================================================ tests

class SealAndScriptTest(unittest.TestCase):
    u"""記録が無くても走る: 封の字と script の定数、script の engine を使わない部分、順序。"""

    @classmethod
    def setUpClass(cls):
        cls.seal = jtext(SEAL)
        cls.bounds = seal_bounds(cls.seal)
        cls.mod, cls.entry16, cls.labels, cls.sets = Materials.get()

    def test_a_1_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds[u"M-1"]), {u"GROUNDED": 340, u"POINTER_NOT_FOUND": 25, u"UNVERIFIABLE": 33, u"VALUE_MISMATCH": 14})
        self.assertEqual(dict((k, v) for k, v in self.bounds.items() if k != u"M-1"),
                         {u"M-2": 412, u"M-3": (5, 15), u"M-4": (0, 12), u"M-5": (0, 3), u"M-6": (0, 2), u"M-7": (0, 10), u"M-9": (0, 10)})

    def test_a_2_script_constants_match_the_seal(self):
        m = self.mod
        self.assertEqual(m.SEAL_COMMIT, SEAL_COMMIT_SHORT)
        self.assertEqual(m.SEAL_REL, SEAL_REL)
        self.assertEqual(m.OUT_REL, REC_REL)
        self.assertEqual(dict(m.ENTRY_REL), dict(ENTRY_RELS))
        self.assertEqual(tuple(m.PROFILES), PROFILES)
        self.assertEqual(dict(m.RITUAL_PLAIN), dict(self.bounds[u"M-1"]))
        self.assertEqual(dict((k, v) for k, v in m.BOUNDS.items() if k != u"M-1"), dict((k, v) for k, v in self.bounds.items() if k != u"M-1"))
        self.assertEqual(dict(m.BOUNDS[u"M-1"]), dict(self.bounds[u"M-1"]))
        sm = seal_materials(self.seal)
        self.assertEqual(len(sm), 8)
        self.assertEqual(dict((rel, s) for rel, s in m.MATERIALS.values()), dict(sm), u"script の材料の sha256 が封 §0 と違う")
        for rel, want in sm.items():
            self.assertEqual(sha(os.path.join(ROOT, rel)), want, rel)
        for rel in ENTRY_RELS.values():
            self.assertIn(u"`%s`" % rel, self.seal)
        self.assertIn(u"`%s`" % REC_REL, self.seal)

    def test_a_3_script_imports_engine_only_as_the_seal_says(self):
        src = jtext(SCRIPT)
        self.assertEqual(script_problems(src), [])
        self.assertIn(u"from adapters.xbrl import verify_document as VD", src)
        self.assertIn(u'VD.verify_document(zb, profile, None)', src)       # text は渡さない(封 §1)
        self.assertEqual(DOCID_RE.findall(src), [])
        self.assertEqual(DOCID_RE.findall(jtext(__file__)), [])

    def test_b_1_scrub_and_helpers_on_synthetic_input(self):
        m = self.mod
        fake = u"S" + u"100" + u"ABCD"                       # 合成の docID(この file に字として置かない)
        self.assertEqual(m.scrub({u"a": u"entry_output_%s_x" % fake, u"b": [fake, 1, None]}), {u"a": u"entry_output_<docID>_x", u"b": [u"<docID>", 1, None]})
        self.assertEqual(m.period_of([u"xbrl:a:X@CurrentYearDuration"]), u"当期")
        self.assertEqual(m.period_of([u"xbrl:a:X@Prior1YearInstant", u"xbrl:a:X@CurrentYearInstant"]), u"前期")
        self.assertEqual(m.period_of([u"xbrl:a:X@FilingDateInstant"]), u"他")
        self.assertEqual(m.period_of([u"formula:a-b"]), None)
        self.assertEqual(m.period_of([]), None)
        self.assertTrue(m.elements_in_grounds([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"], u"jppfs_cor:NetSales/CY=1"))
        self.assertFalse(m.elements_in_grounds([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration"], u"同/前期=1"))
        self.assertIsNone(m.elements_in_grounds([u"formula:a-b"], u"x"))
        self.assertEqual(m.grounds_form(u"direct_value", u"同元素/前期末=1"), FORMS[0])
        self.assertEqual(m.grounds_form(u"derived_value", u"1-2=3"), FORMS[1])
        self.assertEqual(m.grounds_form(u"direct_value", u"jppfs_cor:X/CY=1"), FORMS[2])
        self.assertEqual(m.grounds_form(u"derived_value", u"同/前期=1"), FORMS[0])   # 「同」が先

    def test_b_2_align_on_synthetic_claims(self):
        m = self.mod
        old = [{u"id": u"A", u"span": u"s1", u"value": u"1", u"unit": u"円"}, {u"id": u"B", u"span": u"s2", u"value": u"2", u"unit": u"円"},
               {u"id": u"C", u"span": u"s3", u"value": u"3", u"unit": u"円"}]
        new = [dict(old[0], id=u"X"), dict(old[2], id=u"Y"), dict(old[1], id=u"Z"), {u"id": u"W", u"span": u"s9", u"value": u"9", u"unit": u"円"}]
        mp, counts = m.align(old, new)
        self.assertEqual([mp[u"A"][u"id"], mp[u"B"][u"id"], mp[u"C"][u"id"]], [u"X", u"Z", u"Y"])
        self.assertEqual(dict(counts), {u"同じ位置で対応": 1, u"探し直して対応": 2, u"対応しない P16 の行": 0, u"対応しない P16 の id": [], u"新しい方の余り": 1})
        mp, counts = m.align(old, new[:1])
        self.assertEqual(counts[u"対応しない P16 の id"], [u"B", u"C"])
        self.assertEqual(m.key_of({u"span": u"s", u"value": u"1", u"unit": u"円", u"kind": u"num"}), (u"s", u"1", u"円"))   # 封 §2 の鍵

    def test_b_3_sets_from_the_materials(self):
        self.assertEqual(tuple(len(self.sets[k]) for k in (u"53", u"12", u"8")), (53, 12, 8))
        self.assertEqual(list(self.sets[u"8"]), [u"N039", u"N041", u"N081", u"N124", u"N145", u"N220", u"N239", u"N294"])
        self.assertEqual(sum(1 for v in self.sets[u"12"].values() if v == u"決まる"), 8)
        self.assertEqual(collections.Counter(self.sets[u"53"].values()), collections.Counter({TYPES_T[0]: 30, TYPES_T[5]: 11, TYPES_T[4]: 7, TYPES_T[2]: 3, TYPES_T[3]: 1, TYPES_T[1]: 1}))

    def test_b_4_script_rows_with_p16_as_proxy_match_the_gates_own_rows(self):
        rec = proxy_record(self.mod, self.entry16, self.labels, self.sets)
        ref = g_rows(self.entry16, dict((pf, self.entry16) for pf in PROFILES), self.labels, self.sets)
        self.assertEqual([r[u"id"] for r in rec[u"行"]], list(ref.keys()))
        for r in rec[u"行"]:
            x = ref[r[u"id"]]
            for k in x:
                self.assertEqual(r[k], x[k], u"%s %s" % (r[u"id"], k))
        T = rec[u"集計"]
        self.assertEqual((T[u"P16 の claim"], T[u"53 行"], T[u"12 行"], T[u"8 行"], T[u"249 行"], T[u"12 行で P16 が VALUE_MISMATCH"]), (412, 53, 12, 8, 249, 9))
        self.assertEqual(dict(rec[u"配線の門"][u"(e) 行の対応"][u"P27E"]), {u"同じ位置で対応": 412, u"探し直して対応": 0, u"対応しない P16 の行": 0, u"対応しない P16 の id": [], u"新しい方の余り": 0})
        self.assertEqual(list(T[u"札 偽 の行"].keys()), [u"T087"])
        self.assertEqual(T[u"判定不能 の行"], 22)
        self.assertEqual(T[u"札の無い行(P16 の entry にあって札に無い)"], 0)
        R = ref_tally(rec[u"行"])
        for k in R:
            self.assertEqual(json.loads(json.dumps(R[k], ensure_ascii=False)), T[k], k)
        d16 = collections.OrderedDict((s, sum(1 for c in self.entry16[u"claims"] if c[u"state"] == s)) for s in STATES)
        self.assertEqual(dict(d16), {u"GROUNDED": 330, u"POINTER_NOT_FOUND": 16, u"UNVERIFIABLE": 41, u"VALUE_MISMATCH": 25})
        self.assertEqual(dict(ref_judge(T, self.bounds, T[u"P27 の state の分布(全 claim)"], rec[u"配線の門"][u"(e) 行の対応"])), rec[u"予測の判定"])
        self.assertEqual(rec[u"予測の判定"][u"M-1"], u"外れ")          # P16 の分布は儀式の P27 と違う(代わりの記録なので当然)
        self.assertEqual(rec[u"予測の判定"][u"M-2"], u"当たり")

    def test_b_5_m1_compares_contents_not_order(self):
        u"""監査で見つかった誤り(OrderedDict の並びの順まで比べて常に外れ)が戻らないこと。"""
        T = {u"P27 の state の分布(全 claim)": collections.OrderedDict([(u"GROUNDED", 340), (u"VALUE_MISMATCH", 14), (u"UNVERIFIABLE", 33), (u"POINTER_NOT_FOUND", 25)])}
        src = jtext(SCRIPT)
        self.assertIn(u'dict(T[u"P27 の state の分布(全 claim)"]) == dict(b[u"M-1"])', src)
        self.assertNotIn(u'T[u"P27 の state の分布(全 claim)"] == b[u"M-1"]', src)
        self.assertTrue(dict(T[u"P27 の state の分布(全 claim)"]) == dict(self.mod.RITUAL_PLAIN))
        self.assertFalse(T[u"P27 の state の分布(全 claim)"] == self.mod.RITUAL_PLAIN)

    def test_c_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_c_2_order(self):
        rc, _ = git("cat-file", "-e", SEAL_COMMIT_SHORT + "^{commit}")
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(order_problems(), [])

    def test_c_3_record_doc_and_entries_come_together(self):
        have = [os.path.exists(os.path.join(ROOT, r)) for r in (REC_REL, DOC_REL) + tuple(ENTRY_RELS.values())]
        self.assertIn(sum(have), (0, len(have)), u"記録・文書・entry 2 つは揃って在るか揃って無い")


class RecordTest(unittest.TestCase):
    u"""記録が在るときだけ(封 §5: ラベル file が無ければ記録は無い → skip)。"""

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(REC):
            raise unittest.SkipTest(u"記録 %s が無い(ラベル file のある席で script を走らせると出来る)" % REC_REL)
        cls.rec = jload(REC)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)
        cls.seal = jtext(SEAL)
        cls.doc = jtext(DOC)
        cls.bounds = seal_bounds(cls.seal)
        cls.mod, cls.entry16, cls.labels, cls.sets = Materials.get()
        cls.entries = collections.OrderedDict((pf, jload(os.path.join(ROOT, rel))) for pf, rel in ENTRY_RELS.items())
        cls.p16_dist = collections.OrderedDict((s, sum(1 for c in cls.entry16[u"claims"] if c[u"state"] == s)) for s in STATES)

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"書いた entry", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(HEX40.match(self.rec[u"HEAD の commit"] or u""))
        self.assertEqual(self.rec[u"key_leaks"], [])
        self.assertEqual(sha(SCRIPT), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            self.assertEqual(sha(os.path.join(ROOT, rel)), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(dict(self.rec[u"書いた entry"]), dict(ENTRY_RELS))
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertTrue(W[u"(a) 材料の sha256 が封の値"])
        self.assertEqual(sorted(W[u"(b) ラベル file(cache。repo の外)"].keys()), sorted(l.split()[1] for l in jtext(os.path.join(ROOT, "fixtures/xbrl/taxonomy_labels_sha256.txt")).splitlines() if l.strip()))
        self.assertTrue(all(v[u"在る"] and v[u"sha256 が名簿と合う"] for v in W[u"(b) ラベル file(cache。repo の外)"].values()))
        self.assertTrue(HEX64.match(W[u"(c) engine の bundle の sha256(core/・adapters/)"]))
        self.assertEqual(W[u"(c) engine の未 commit の file"], 0)
        fb = load(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"), "frozen_bundle_sha_for_rerun_gate")
        self.assertEqual(W[u"(c) engine の bundle の sha256(core/・adapters/)"], "864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054", u"走らせたときの engine が測った時点の凍結の束と違う")   # 2026-11-02: 「その他」の主語の結び直し(封 XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02)で最新の世代は動いた。測った時点の世代(候補の欄を足した世代)を字で留め、世代の一覧に在ることを確かめる
        self.assertIn("864b1f96292f1615c7e5b7e3bbd6924ebd9955b8354b3c5d51400ba9a01fb054", [g[0] for g in fb.FROZEN_BUNDLE_GENERATIONS])
        self.assertEqual(W[u"(c) engine の file の数"], fb.FROZEN_COUNT)
        self.assertEqual(dict(W[u"(d) 53 行・12 行・8 行の数"]), {u"53": 53, u"12": 12, u"8": 8})
        self.assertEqual(len(self.rec[u"行"]), 412)
        self.assertEqual(self.rec_text.count("scratchpad"), 0)

    def test_a_2_no_docid_anywhere(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for pf, e in self.entries.items():
            self.assertEqual(DOCID_RE.findall(json.dumps(e, ensure_ascii=False)), [], pf)
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_a_3_entries_shape(self):
        zip_sha = self.mod.MATERIALS[u"zip"][1]
        fps = set()
        for pf, e in self.entries.items():
            self.assertEqual(e[u"profile"], pf)
            self.assertEqual(e[u"input"][u"zip_sha256"], zip_sha, u"%s の entry の ZIP が材料と違う" % pf)
            self.assertFalse(e[u"input"].get(u"text_replaced"), u"%s: text を渡していない(封 §1)" % pf)
            self.assertEqual(len(e[u"claims"]), self.rec[u"集計"][u"%s の claim" % pf])
            dist = collections.OrderedDict((s, sum(1 for c in e[u"claims"] if c[u"state"] == s)) for s in STATES)
            self.assertEqual(dict(dist), dict(self.rec[u"集計"][u"%s の state の分布(全 claim)" % pf]))
            self.assertEqual(dict(e[u"document"][u"states"]), dict(dist))
            fps.add(json.dumps(e[u"engine"], sort_keys=True))
            for c in e[u"claims"]:
                self.assertIn(c[u"state"], STATES)
        self.assertEqual(len(fps), 1, u"2 つの entry の engine の指紋が違う")

    def test_b_1_rows_recomputed_by_the_script_and_by_the_gate(self):
        rows, ac = self.mod.build_rows(self.entry16, self.entries, self.labels, self.sets)
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(ac, ensure_ascii=False)), self.rec[u"配線の門"][u"(e) 行の対応"])
        ref = g_rows(self.entry16, self.entries, self.labels, self.sets)
        self.assertEqual([r[u"id"] for r in self.rec[u"行"]], list(ref.keys()))
        for r in self.rec[u"行"]:
            x = ref[r[u"id"]]
            for k in x:
                self.assertEqual(r[k], x[k], u"%s %s" % (r[u"id"], k))
            self.assertEqual(r[u"札"], (self.labels.get(r[u"id"]) or {}).get(u"札"))

    def test_b_2_tally_recomputed(self):
        R, T = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in R:
            self.assertEqual(json.loads(json.dumps(R[k], ensure_ascii=False)), T[k], k)
        self.assertEqual(T[u"P16 の claim"], len(self.entry16[u"claims"]))

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        J = ref_judge(self.rec[u"集計"], self.bounds, self.rec[u"集計"][u"P27 の state の分布(全 claim)"], self.rec[u"配線の門"][u"(e) 行の対応"])
        self.assertEqual(dict(J), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)
        self.assertEqual(self.rec[u"配線の門"][u"(f) P27 の state の分布が儀式の記録の素の書類と一致"], self.rec[u"予測の判定"][u"M-1"] == u"当たり")

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec, self.p16_dist), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])


class MutationTest(unittest.TestCase):
    u"""記録が在ればそれで、無ければ P16 を流した代わりの記録で、門が赤くなることを確かめる。"""

    @classmethod
    def setUpClass(cls):
        cls.mod, cls.entry16, cls.labels, cls.sets = Materials.get()
        cls.seal = jtext(SEAL)
        cls.bounds = seal_bounds(cls.seal)
        cls.p16_dist = collections.OrderedDict((s, sum(1 for c in cls.entry16[u"claims"] if c[u"state"] == s)) for s in STATES)
        if os.path.exists(REC):
            cls.rec, cls.doc = jload(REC), jtext(DOC)
        else:
            cls.rec = proxy_record(cls.mod, cls.entry16, cls.labels, cls.sets)
            cls.doc = cls.synthetic_doc(cls.rec)
        cls.rec_text = json.dumps(cls.rec, ensure_ascii=False)

    @staticmethod
    def synthetic_doc(rec):
        J, exp = rec[u"予測の判定"], expected_cells(rec)
        misses = [i for i in IDS if J.get(i) == u"外れ"]
        L = [u"# 結果 ― **予測 当たり %d / 外れ %d(%s)**" % (J[u"当たり"], J[u"外れ"], u"・".join(misses)), u""]
        for i in IDS:
            L.append(u"| **%s** | 予測 | %s | %s |" % (i, u"、".join(exp[i]), u"判定しない" if i == u"M-10" else u"**%s**" % J[i]))
        L += expected_lines(rec, collections.OrderedDict((s, sum(1 for r in rec[u"行"] if r[u"P16 の state"] == s)) for s in STATES))
        T = rec[u"集計"]
        for key in (u"53 行で P27E で GROUNDED の id", u"249 行で P27E で GROUNDED でなくなった id", u"P27E と P27 で state が違う id", u"12 行で P27E で GROUNDED の id"):
            L.append(u"%s(%s)" % (key, u"・".join(T[key])))
        L.append(u"札 偽 %s" % u"・".join(T[u"札 偽 の行"].keys()))
        return u"\n".join(L) + u"\n"

    def test_m_0_the_reference_doc_passes(self):
        self.assertEqual(table_problems(self.doc, self.rec, self.p16_dist), [])

    def test_m_1_flipping_a_judgement_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"予測の判定"][u"M-3"] = u"当たり" if rec[u"予測の判定"][u"M-3"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds, rec[u"集計"][u"P27 の state の分布(全 claim)"], rec[u"配線の門"][u"(e) 行の対応"])), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"53 行で P27E で GROUNDED"] += 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"53 行で P27E で GROUNDED"], rec[u"集計"][u"53 行で P27E で GROUNDED"])

    def test_m_3_changing_a_row_state_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"P27E の state"] == u"GROUNDED" and x[u"札"] == u"真" and x[u"kind"] == u"num"][0]
        r[u"P27E の state"] = u"VALUE_MISMATCH"
        new = self.entries() if os.path.exists(REC) else dict((pf, self.entry16) for pf in PROFILES)
        self.assertNotEqual(g_rows(self.entry16, new, self.labels, self.sets)[r[u"id"]][u"P27E の state"], r[u"P27E の state"])
        self.assertNotEqual(ref_tally(rec[u"行"])[u"P16 → P27E の state(札 真・num)"], rec[u"集計"][u"P16 → P27E の state(札 真・num)"])

    def entries(self):
        return collections.OrderedDict((pf, jload(os.path.join(ROOT, rel))) for pf, rel in ENTRY_RELS.items())

    def test_m_4_doc_verdict_swap_is_caught(self):
        J = self.rec[u"予測の判定"]
        i = [k for k in IDS if J.get(k) in (u"当たり", u"外れ")][0]
        bad = self.doc.replace(u"| **%s** |" % J[i], u"| **%s** |" % (u"外れ" if J[i] == u"当たり" else u"当たり"), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.p16_dist), [])

    def test_m_5_doc_table_change_is_caught(self):
        T = self.rec[u"集計"]
        d = T[u"P27E の state の分布(全 claim)"]
        line = u"| **P27E** | %d | %d | %d | %d |" % tuple(d[s] for s in STATES)
        self.assertIn(line, self.doc)
        bad = self.doc.replace(line, u"| **P27E** | %d | %d | %d | %d |" % ((d[STATES[0]] + 1, d[STATES[1]] - 1) + tuple(d[s] for s in STATES[2:])), 1)
        self.assertNotEqual(table_problems(bad, self.rec, self.p16_dist), [])
        line = [l for l in self.doc.splitlines() if l.startswith(u"| **%s** |" % TYPES_T[0])][0]
        n = int(line.split(u"|")[2])
        bad = self.doc.replace(line, line.replace(u"| %d |" % n, u"| %d |" % (n + 1), 1), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.p16_dist), [])
        bad = self.doc.replace(u"| N039 |", u"| N038 |")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.p16_dist), [])

    def test_m_6_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**0〜12**", u"**0〜1200**")
        self.assertNotEqual(bad, self.seal)
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"249 行で P27E で GROUNDED でなくなった"] = 500
        J0 = ref_judge(rec[u"集計"], self.bounds, rec[u"集計"][u"P27 の state の分布(全 claim)"], rec[u"配線の門"][u"(e) 行の対応"])
        J1 = ref_judge(rec[u"集計"], seal_bounds(bad), rec[u"集計"][u"P27 の state の分布(全 claim)"], rec[u"配線の門"][u"(e) 行の対応"])
        self.assertEqual((J0[u"M-4"], J1[u"M-4"]), (u"外れ", u"当たり"))
        bad = self.seal.replace(u"(340・25・33・14)", u"(330・16・41・25)")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(seal_bounds(bad)[u"M-1"]), dict(self.bounds[u"M-1"]))

    def test_m_7_unbound_prose_number_is_caught(self):
        self.assertEqual(prose_problems(u"記録に在る数 412 の行。\n", self.rec_text), [])
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])
        self.assertEqual(prose_problems(u"記録に無い 123456 を書いた行【門なし】。\n", self.rec_text), [])

    def test_m_8_network_or_core_import_is_caught(self):
        src = jtext(SCRIPT)
        self.assertNotEqual(script_problems(src + u"\nimport urllib.request\n"), [])
        self.assertNotEqual(script_problems(src + u"\nfrom core import x\n"), [])
        self.assertNotEqual(script_problems(src + u"\nimport adapters.xbrl.comparators\n"), [])
        self.assertNotEqual(script_problems(src + u"\nfrom adapters.xbrl import comparators\n"), [])      # 監査で見つかった穴
        self.assertNotEqual(script_problems(src + u"\nfrom adapters.xbrl import verify_document, vocabulary\n"), [])
        self.assertNotEqual(script_problems(src + u'\nio.open(os.path.join(ROOT, "adapters", "x.py"), "w")\n'), [])
        self.assertNotEqual(script_problems(src + u'\nopen(os.path.join(ROOT, "core", "x.py"), mode="w")\n'), [])
        self.assertNotEqual(script_problems(src + u'\nio.open(os.path.join(ROOT, "docs", "x.md"), "a")\n'), [])
        self.assertEqual(script_problems(src + u'\nio.open(os.path.join(ROOT, "docs", "x.md"), "r")\n'), [])     # 読むのは咎めない
        self.assertNotEqual(script_problems(src + u'\nVD.verify_document(zb, "P16", None)\n'), [])

    def test_m_9_m1_order_regression_is_caught(self):
        u"""script の M-1 の比較の字を、監査前の形(OrderedDict 同士)に戻すと、中身が同じで順が違う分布で偽になる(= 常に外れ)ことを、その字を動かして見る。"""
        src = jtext(SCRIPT)
        good = u'dict(T[u"P27 の state の分布(全 claim)"]) == dict(b[u"M-1"])'
        bad = u'T[u"P27 の state の分布(全 claim)"] == b[u"M-1"]'
        self.assertIn(good, src)
        self.assertNotIn(bad, src.replace(good, u""))
        env = {u"T": {u"P27 の state の分布(全 claim)": collections.OrderedDict([(u"GROUNDED", 340), (u"VALUE_MISMATCH", 14), (u"UNVERIFIABLE", 33), (u"POINTER_NOT_FOUND", 25)])},
               u"b": {u"M-1": self.mod.RITUAL_PLAIN}}
        self.assertTrue(eval(good, {}, env))
        self.assertFalse(eval(bad, {}, env))                 # 監査前の形はここで偽 → M-1 が常に外れになる
        env[u"T"][u"P27 の state の分布(全 claim)"][u"GROUNDED"] = 339
        self.assertFalse(eval(good, {}, env))                # 中身が違えば直した形も偽

    def test_m_10_dropping_an_id_from_the_doc_is_caught(self):
        T = self.rec[u"集計"]
        ids = T[u"53 行で P27E で GROUNDED の id"] or T[u"249 行で P27E で GROUNDED でなくなった id"] or list(T[u"札 偽 の行"].keys())
        self.assertTrue(ids)
        bad = self.doc.replace(ids[0], u"N000")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec, self.p16_dist), [])


if __name__ == "__main__":
    unittest.main()
