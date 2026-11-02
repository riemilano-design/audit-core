# -*- coding: utf-8 -*-
u"""門: engine が止めた真の文 53 の中身(封 docs/XBRL_DERIVATION_STOPPED_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/derivation_stopped_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 J-1〜J-10 を、記録の集計と封 §4 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 53 行を門自身の code で材料(主語の制約の便の記録・entry・札)から作り直し、型 T1〜T6・根拠の照合・正した形を記録と全行一致させる。
- 集計を行から数え直す。
- 文書の表の実測の欄・型の表・id・散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
- script が標準ライブラリだけで engine も前の便の script も読まない。順序(封 < script・記録・文書・門)。変異で赤くなる。
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

SEAL_REL = "docs/XBRL_DERIVATION_STOPPED_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_DERIVATION_STOPPED_2026-11-02.md"
REC_REL = "fixtures/xbrl/derivation_stopped_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_derivation_stopped_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_derivation_stopped.py"
SEAL_COMMIT_SHORT = "ab2ad5b"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"J-%d" % i for i in range(1, 11))
STATES = (u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
TYPES_T = (u"T1 指せず", u"T2 同じ fact", u"T3 導出の量", u"T4 同じ要素・別の期", u"T5 別の要素", u"T6 導出も決めない")
VERDICTS = (u"導出一致", u"保留", u"不一致")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
DOCID_RE = re.compile(r"\bS100[A-Z0-9]{4}\b")
NOT_GATED = u"【門なし】"
ALLOWED_IMPORTS = {"argparse", "collections", "hashlib", "io", "json", "os", "re", "subprocess", "sys", "__future__"}
FORBIDDEN = (u"accurate", u"guarantee", u"正確", u"保証", u"世界初", u"出所として正しい証拠が得られた")
POINTER_RE = re.compile(r"^xbrl:([A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)@([A-Za-z0-9_\-]+)$")


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
        m = re.match(r"^\| \*\*(J-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    b[u"J-1"] = int(re.search(r"\*\*(\d+) / \d+\*\*", rows[u"J-1"][0]).group(1))
    for i in (u"J-2", u"J-3", u"J-4", u"J-5", u"J-6", u"J-8", u"J-9"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    b[u"J-7"] = int(re.search(r"\*\*1 種類に (\d+) 以上\*\*", rows[u"J-7"][0]).group(1))
    return b


def seal_state_counts(seal):
    m = re.search(r"VALUE_MISMATCH (\d+)・UNVERIFIABLE (\d+)・POINTER_NOT_FOUND (\d+)", seal)
    return collections.OrderedDict([(u"VALUE_MISMATCH", int(m.group(1))), (u"UNVERIFIABLE", int(m.group(2))), (u"POINTER_NOT_FOUND", int(m.group(3)))])


# ---------------------------------------------------------------- 門自身の型・照合(script とは別に書く)

def ref_pointers(pointers):
    out = []
    for p in pointers or []:
        m = POINTER_RE.match(p)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def ref_in(elements, grounds):
    elements = list(elements)
    if not elements:
        return None
    return any(e.split(u":")[-1] in (grounds or u"") for e in elements)


def ref_type(ptrs, clue, verdict, cand):
    if not ptrs:
        return TYPES_T[0]
    if not (clue and verdict == u"導出一致" and cand):
        return TYPES_T[5]
    if cand[u"型"] != u"D1":
        return TYPES_T[2]
    f = cand[u"fact"][0]
    if (f[u"name"], f[u"context"]) in set(ptrs):
        return TYPES_T[1]
    if f[u"name"] in set(e for e, _ in ptrs):
        return TYPES_T[3]
    return TYPES_T[4]


def ref_rows(prev_rows, entry_claims, labels):
    u"""53 行の型と照合の旗を材料から作り直す(記録の行と比べる最小の欄)。"""
    out = collections.OrderedDict()
    for pr in prev_rows:
        if not pr.get(u"母数"):
            continue
        ec, lab = entry_claims[pr[u"id"]], labels[pr[u"id"]]
        ptrs = ref_pointers(ec.get(u"pointers"))
        clue = bool(pr.get(u"手がかりあり"))
        verdict = pr.get(u"判定") if clue else None
        cand = (pr.get(u"候補") or [None])[0] if (clue and verdict == u"導出一致") else None
        g = lab.get(u"根拠") or u""
        eng_in = ref_in((e for e, _ in ptrs), g)
        cand_in = ref_in((f[u"name"] for f in cand[u"fact"]), g) if cand else None
        out[pr[u"id"]] = collections.OrderedDict([
            (u"state", ec.get(u"state")), (u"札", lab.get(u"札")), (u"form", ec.get(u"form")), (u"reason", ec.get(u"reason")),
            (u"pointers", [(e, c) for e, c in ptrs]), (u"K0 の判定", verdict), (u"候補の型", cand[u"型"] if cand else None),
            (u"engine の要素が根拠に在る", eng_in), (u"候補の要素が根拠に在る", cand_in),
            (u"engine の要素が候補の要素に在る", (any(e in set(f[u"name"] for f in cand[u"fact"]) for e, _ in ptrs) if (cand and ptrs) else None)),
            (u"型", ref_type(ptrs, clue, verdict, cand)),
            (u"導出が engine の取り違えを正した形", bool(cand and ptrs and cand_in and eng_in is False)),
        ])
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    T[u"母数"] = len(rows)
    T[u"手がかりあり"] = sum(1 for r in rows if r[u"手がかりあり"])
    T[u"手がかりなし"] = T[u"母数"] - T[u"手がかりあり"]
    T[u"札が 真"] = sum(1 for r in rows if r[u"札"] == u"真")
    T[u"state の分布"] = collections.OrderedDict((s, sum(1 for r in rows if r[u"state"] == s)) for s in STATES)
    T[u"state が前の便の記録と一致した行"] = sum(1 for r in rows if r[u"state が前の便の記録と一致"])
    T[u"型の件数"] = collections.OrderedDict((t, sum(1 for r in rows if r[u"型"] == t)) for t in TYPES_T)
    T[u"state × 型"] = collections.OrderedDict((s, collections.OrderedDict((t, sum(1 for r in rows if r[u"state"] == s and r[u"型"] == t)) for t in TYPES_T)) for s in STATES)
    T[u"型ごとの id"] = collections.OrderedDict((t, [r[u"id"] for r in rows if r[u"型"] == t]) for t in TYPES_T)
    vm = [r for r in rows if r[u"state"] == u"VALUE_MISMATCH"]
    T[u"VALUE_MISMATCH"] = len(vm)
    T[u"VALUE_MISMATCH で engine の要素が根拠に無い"] = sum(1 for r in vm if r[u"engine の要素が根拠に在る"] is False)
    T[u"VALUE_MISMATCH で engine の要素が根拠に無い id"] = [r[u"id"] for r in vm if r[u"engine の要素が根拠に在る"] is False]
    T[u"VALUE_MISMATCH で engine の要素が根拠に在る"] = sum(1 for r in vm if r[u"engine の要素が根拠に在る"] is True)
    T[u"VALUE_MISMATCH で form が derived_value"] = sum(1 for r in vm if r[u"form"] == u"derived_value")
    un = [r for r in rows if r[u"state"] == u"UNVERIFIABLE"]
    T[u"UNVERIFIABLE"] = len(un)
    c = collections.Counter((r[u"reason"] or u"(無し)") for r in un)
    T[u"UNVERIFIABLE の reason の分布"] = collections.OrderedDict(sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0]))))
    T[u"UNVERIFIABLE の reason の最多"] = max(c.values()) if un else 0
    T[u"UNVERIFIABLE で pointers が空でない"] = sum(1 for r in un if r[u"pointers"])
    pnf = [r for r in rows if r[u"state"] == u"POINTER_NOT_FOUND"]
    T[u"POINTER_NOT_FOUND"] = len(pnf)
    T[u"POINTER_NOT_FOUND で pointers が空"] = sum(1 for r in pnf if not r[u"pointers"])
    T[u"POINTER_NOT_FOUND の K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in pnf if r[u"K0 の判定"] == v)) for v in VERDICTS)
    T[u"導出が engine の取り違えを正した形"] = sum(1 for r in rows if r[u"導出が engine の取り違えを正した形"])
    T[u"導出が engine の取り違えを正した形の id"] = [r[u"id"] for r in rows if r[u"導出が engine の取り違えを正した形"]]
    t3 = [r for r in rows if r[u"型"] == TYPES_T[2]]
    T[u"T3 で engine の要素が候補の要素に在る"] = sum(1 for r in t3 if r[u"engine の要素が候補の要素に在る"])
    T[u"手がかりあり で pointers が空でない"] = sum(1 for r in rows if r[u"手がかりあり"] and r[u"pointers"])
    T[u"手がかりあり で engine の要素が S に在る"] = sum(1 for r in rows if r[u"手がかりあり"] and r[u"pointers"] and r[u"engine の要素が S に在る"])
    T[u"K0 の判定(手がかりあり)"] = collections.OrderedDict((v, sum(1 for r in rows if r[u"K0 の判定"] == v)) for v in VERDICTS)
    return T


def ref_judge(T, b, seal_counts):
    J = collections.OrderedDict()
    J[u"J-1"] = (T[u"state の分布"] == seal_counts and T[u"state が前の便の記録と一致した行"] == b[u"J-1"])
    J[u"J-2"] = b[u"J-2"][0] <= T[u"VALUE_MISMATCH で engine の要素が根拠に無い"] <= b[u"J-2"][1]
    J[u"J-3"] = b[u"J-3"][0] <= T[u"型の件数"][TYPES_T[1]] <= b[u"J-3"][1]
    J[u"J-4"] = b[u"J-4"][0] <= T[u"T3 で engine の要素が候補の要素に在る"] <= b[u"J-4"][1]
    J[u"J-5"] = b[u"J-5"][0] <= T[u"型の件数"][TYPES_T[3]] <= b[u"J-5"][1]
    J[u"J-6"] = b[u"J-6"][0] <= T[u"型の件数"][TYPES_T[4]] <= b[u"J-6"][1]
    J[u"J-7"] = T[u"UNVERIFIABLE の reason の最多"] >= b[u"J-7"]
    J[u"J-8"] = b[u"J-8"][0] <= T[u"導出が engine の取り違えを正した形"] <= b[u"J-8"][1]
    J[u"J-9"] = b[u"J-9"][0] <= T[u"VALUE_MISMATCH で form が derived_value"] <= b[u"J-9"][1]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"J-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(J-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def type_blocks(doc):
    u"""§2-3 の型ごとの箇条書き(「- **T1 指せず 30**: …」から次の型の箇条書きか見出しまで)を型ごとに切り出す。"""
    out = collections.OrderedDict()
    cur = None
    for ln in doc.splitlines():
        m = re.match(r"^- \*\*(T\d [^*]+?) \d+\*\*", ln)
        if m and m.group(1) in TYPES_T:
            cur = m.group(1)
            out[cur] = ln
            continue
        if cur is not None:
            if ln.startswith(u"#") or ln.startswith(u"- **") or ln.startswith(u"|"):
                cur = None
            else:
                out[cur] += u"\n" + ln
    return out


def first_sentence_ids(text):
    u"""括弧の外(深さ 0)の最初の文(「。」まで)に在る claim id の列(重複もそのまま)。"""
    depth, out = 0, []
    for ch in text:
        if ch in u"((":
            depth += 1
        elif ch in u"))":
            depth = max(0, depth - 1)
        elif depth == 0:
            if ch == u"。":
                break
            out.append(ch)
    return re.findall(r"\bN\d{3}\b", u"".join(out))


def expected_cells(T):
    top = list(T[u"UNVERIFIABLE の reason の分布"].items())[0]
    return {
        u"J-1": [u"%d / %d" % (T[u"state が前の便の記録と一致した行"], T[u"母数"]), u"VALUE_MISMATCH %d・UNVERIFIABLE %d・POINTER_NOT_FOUND %d" % tuple(T[u"state の分布"].values())],
        u"J-2": [u"%d / %d" % (T[u"VALUE_MISMATCH で engine の要素が根拠に無い"], T[u"VALUE_MISMATCH"])],
        u"J-3": [u"%d" % T[u"型の件数"][TYPES_T[1]]],
        u"J-4": [u"%d / %d" % (T[u"T3 で engine の要素が候補の要素に在る"], T[u"型の件数"][TYPES_T[2]])],
        u"J-5": [u"%d" % T[u"型の件数"][TYPES_T[3]]],
        u"J-6": [u"%d" % T[u"型の件数"][TYPES_T[4]]],
        u"J-7": [u"%s %d" % (top[0], top[1])],
        u"J-8": [u"%d" % T[u"導出が engine の取り違えを正した形"]],
        u"J-9": [u"%d" % T[u"VALUE_MISMATCH で form が derived_value"]],
        u"J-10": [u"手がかりなし %d" % T[u"手がかりなし"], u"truncate で入る %d" % T[u"T2 の engine の帯の参考"][u"truncate で入る"], u"round で入る %d" % T[u"T2 の engine の帯の参考"][u"round で入る"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が J-1〜J-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"J-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"J-3", u"J-5", u"J-6", u"J-8", u"J-9") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    blocks = type_blocks(doc)
    for t in TYPES_T:
        n = T[u"型の件数"][t]
        want = u"| **%s** | %d | %d | %d | %d |" % (t, n, T[u"state × 型"][u"VALUE_MISMATCH"][t], T[u"state × 型"][u"UNVERIFIABLE"][t], T[u"state × 型"][u"POINTER_NOT_FOUND"][t])
        if want not in doc:
            p.append(u"型の表の行(%s)" % want)
        block = blocks.get(t, u"")
        if not block.startswith(u"- **%s %d**" % (t, n)):
            p.append(u"%s の箇条書きが「%s %d」で始まらない" % (t, t, n))
        if t == TYPES_T[0]:
            m = re.search(r"T1 の id\((\d+)\): (.*?)。", block)
            listed = sorted(re.findall(r"\bN\d{3}\b", m.group(2))) if m else []
            if not m or int(m.group(1)) != n or listed != sorted(T[u"型ごとの id"][t]) or len(listed) != n:
                p.append(u"T1 の id の列が記録と違う: %s" % listed)
        else:
            listed = first_sentence_ids(block.split(u":", 1)[1] if u":" in block else block)
            if sorted(listed) != sorted(T[u"型ごとの id"][t]) or len(listed) != n:
                p.append(u"%s の箇条書きの id の列が記録と違う: %s" % (t, listed))
        for i in re.findall(r"\bN\d{3}\b", block):
            if i not in T[u"型ごとの id"][t] and not (t == TYPES_T[4] and i in T[u"導出が engine の取り違えを正した形の id"]):
                p.append(u"%s の箇条書きに別の型の id %s" % (t, i))
    t5 = blocks.get(TYPES_T[4], u"")
    tail = t5.split(u"正した形", 1)[1] if u"正した形" in t5 else u""
    fixed = first_sentence_ids(tail)
    want_fixed = T[u"導出が engine の取り違えを正した形の id"]
    if sorted(fixed) != sorted(want_fixed) or len(fixed) != len(want_fixed):
        p.append(u"「正した形」の後の id の列が記録と違う: %s" % fixed)
    vm = [r for r in rec[u"行"] if r[u"state"] == u"VALUE_MISMATCH"]
    other = sum(1 for r in vm if r[u"engine の要素が根拠に在る"] is False and r[u"型"] != TYPES_T[1] and not (r[u"型"] == TYPES_T[2] and r[u"engine の要素が候補の要素に在る"]))
    for s in (u"別の要素と読める %d" % other, u"別の要素と読めるのが %d" % other):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    if u"別の要素と読める %d" % other not in doc.splitlines()[0]:
        p.append(u"見出しに「別の要素と読める %d」が無い" % other)
    r = T[u"UNVERIFIABLE の reason の分布"]
    for s in (u"state が前の便の記録と一致した行 %d / %d" % (T[u"state が前の便の記録と一致した行"], T[u"母数"]),
              u"engine の要素が手がかり S に在る %d / %d" % (T[u"手がかりあり で engine の要素が S に在る"], T[u"手がかりあり で pointers が空でない"]),
              u"reason は %s" % u"・".join(u"%s %d" % kv for kv in r.items()),
              u"engine の要素が札の根拠に在る %d" % T[u"VALUE_MISMATCH で engine の要素が根拠に在る"],
              u"無い %d" % T[u"VALUE_MISMATCH で engine の要素が根拠に無い"],
              u"derived_value %d" % T[u"VALUE_MISMATCH で form が derived_value"],
              u"導出一致 %d・保留 %d・不一致 %d" % tuple(T[u"POINTER_NOT_FOUND の K0 の判定(手がかりあり)"].values()),
              u"engine の要素が候補の要素に在るのは N120 だけ(%d / %d)" % (T[u"T3 で engine の要素が候補の要素に在る"], T[u"型の件数"][TYPES_T[2]]),
              u"手がかりなし %d はこの型に全部入る" % T[u"手がかりなし"]):
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
        s = re.sub(r"J-\d+|G-\d+|E-\d+|K\d|V\d|D\d|T\d|P\d+|§\d+(-\d+)*", u" ", s)
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
    for bad in ("adapters", "audit_core", "core", "urllib", "http", "socket", "importlib"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    if "spec_from_file_location" in src or "zipfile" in src:
        p.append(u"他の script や ZIP を読んでいる")
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
        cls.seal_counts = seal_state_counts(cls.seal)
        cls.mod = load(SCRIPT, "derivation_stopped_under_test")
        M = cls.mod.MATERIALS
        cls.prev_rec = jload(os.path.join(ROOT, M[u"prev_rec"][0]))
        cls.entry = jload(os.path.join(ROOT, M[u"entry"][0]))
        cls.entry_claims = {c[u"id"]: c for c in cls.entry[u"claims"]}
        cls.labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, M[u"labels"][0]))[u"labels"]}
        cls.texts = {x[u"id"]: x for x in jload(os.path.join(ROOT, M[u"claims"][0]))[u"claims"]}

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertEqual(W[u"(e) state が前の便の記録と一致した行"], len(self.rec[u"行"]))
        self.assertEqual(W[u"(f) 読めなかった pointer の在る行"], 0)
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        self.assertEqual(self.entry.get(u"profile"), u"P16")
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(len(self.mod.MATERIALS), 4)
        self.assertEqual(self.rec_text.count("scratchpad"), 0)
        self.assertEqual(self.mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_a_3_population_is_the_previous_runs_population(self):
        ids = [r[u"id"] for r in self.rec[u"行"]]
        prev_ids = [r[u"id"] for r in self.prev_rec[u"行"] if r[u"母数"]]
        self.assertEqual(ids, prev_ids)
        self.assertEqual(len(ids), 53)
        for r in self.rec[u"行"]:
            self.assertEqual(r[u"札"], u"真", r[u"id"])
            self.assertEqual(self.labels[r[u"id"]][u"札"], u"真")
            self.assertEqual(self.entry_claims[r[u"id"]][u"kind"], u"num")
            self.assertNotEqual(r[u"state"], u"GROUNDED")
            self.assertEqual(r[u"state"], self.entry_claims[r[u"id"]][u"state"])

    def test_b_1_rows_recomputed_by_the_script(self):
        rows = self.mod.build_rows(self.prev_rec[u"行"], self.entry_claims, self.labels, self.texts)
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(self.mod.judge(self.mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_types_and_flags_recomputed_with_the_gates_own_code(self):
        ref = ref_rows(self.prev_rec[u"行"], self.entry_claims, self.labels)
        self.assertEqual(list(ref.keys()), [r[u"id"] for r in self.rec[u"行"]])
        for r in self.rec[u"行"]:
            x = ref[r[u"id"]]
            for k in (u"state", u"札", u"form", u"reason", u"K0 の判定", u"候補の型", u"engine の要素が根拠に在る", u"候補の要素が根拠に在る",
                      u"engine の要素が候補の要素に在る", u"型", u"導出が engine の取り違えを正した形"):
                self.assertEqual(r[k], x[k], u"%s %s" % (r[u"id"], k))
            self.assertEqual([(p[u"要素"], p[u"context"]) for p in r[u"pointers"]], x[u"pointers"], r[u"id"])
            # 型の条件を行の欄からも確かめる
            if r[u"型"] == TYPES_T[0]:
                self.assertEqual(r[u"pointers"], [])
            else:
                self.assertTrue(r[u"pointers"])
            if r[u"型"] in TYPES_T[1:5]:
                self.assertEqual(r[u"K0 の判定"], u"導出一致")
                self.assertEqual(len(r[u"候補の fact"]), 2 if r[u"候補の型"] in (u"D2", u"D3", u"D5") else len(r[u"候補の fact"]))
            if r[u"型"] == TYPES_T[1]:
                self.assertEqual(r[u"候補の型"], u"D1")
                self.assertIn(dict(r[u"候補の fact"][0]), [dict(p) for p in r[u"pointers"]])
                self.assertIsNotNone(r[u"engine の帯の参考(T2)"])
            else:
                self.assertIsNone(r[u"engine の帯の参考(T2)"])
            if r[u"型"] == TYPES_T[2]:
                self.assertNotEqual(r[u"候補の型"], u"D1")
            if r[u"型"] == TYPES_T[3]:
                self.assertEqual(r[u"候補の型"], u"D1")
                self.assertIn(r[u"候補の fact"][0][u"要素"], [p[u"要素"] for p in r[u"pointers"]])
                self.assertNotIn(r[u"候補の fact"][0][u"context"], [p[u"context"] for p in r[u"pointers"] if p[u"要素"] == r[u"候補の fact"][0][u"要素"]])
            if r[u"型"] == TYPES_T[4]:
                self.assertEqual(r[u"候補の型"], u"D1")
                self.assertNotIn(r[u"候補の fact"][0][u"要素"], [p[u"要素"] for p in r[u"pointers"]])
            if r[u"型"] == TYPES_T[5]:
                self.assertTrue((not r[u"手がかりあり"]) or r[u"K0 の判定"] != u"導出一致")
            # 根拠の照合の旗を札の字から確かめる
            g = self.labels[r[u"id"]][u"根拠"] or u""
            if r[u"pointers"]:
                self.assertEqual(r[u"engine の要素が根拠に在る"], any(p[u"要素"].split(u":")[-1] in g for p in r[u"pointers"]))
            else:
                self.assertIsNone(r[u"engine の要素が根拠に在る"])
            if r[u"候補の fact"]:
                self.assertEqual(r[u"候補の要素が根拠に在る"], any(f[u"要素"].split(u":")[-1] in g for f in r[u"候補の fact"]))
            # 候補は前の便の記録の候補そのもの
            pr = [x for x in self.prev_rec[u"行"] if x[u"id"] == r[u"id"]][0]
            if r[u"候補の fact"]:
                c0 = pr[u"候補"][0]
                self.assertEqual(r[u"候補の型"], c0[u"型"])
                self.assertEqual([(f[u"要素"], f[u"context"]) for f in r[u"候補の fact"]], [(f[u"name"], f[u"context"]) for f in c0[u"fact"]])
                self.assertEqual(r[u"候補の v"], c0[u"v"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)
        t2 = [r for r in self.rec[u"行"] if r[u"型"] == TYPES_T[1]]
        for r in t2:
            d = abs(r[u"候補の v"]) - abs(r[u"t'"])
            self.assertAlmostEqual(r[u"engine の帯の参考(T2)"][u"|v| − |t|"], d, places=6)
            self.assertEqual(r[u"engine の帯の参考(T2)"][u"round(|d| ≤ u / 2)"], abs(d) <= r[u"u"] / 2.0)
            self.assertEqual(r[u"engine の帯の参考(T2)"][u"truncate(0 ≤ d < u)"], 0 <= d < r[u"u"])
        self.assertEqual(R[u"T2 の engine の帯の参考"][u"truncate で入る"], sum(1 for r in t2 if r[u"engine の帯の参考(T2)"][u"truncate(0 ≤ d < u)"]))
        self.assertEqual(R[u"T2 の engine の帯の参考"][u"round で入る"], sum(1 for r in t2 if r[u"engine の帯の参考(T2)"][u"round(|d| ≤ u / 2)"]))

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds, self.seal_counts)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)
        want = dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items())
        self.assertEqual(want, dict(self.bounds), u"script の幅が封の字と違う")
        self.assertEqual(self.rec[u"定数"][u"封の state の分布"], self.seal_counts)

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"J-1": 53, u"J-2": (10, 18), u"J-3": (0, 2), u"J-4": (3, 6), u"J-5": (1, 4), u"J-6": (3, 8), u"J-7": 10, u"J-8": (6, 12), u"J-9": (0, 5)})
        self.assertEqual(dict(self.seal_counts), {u"VALUE_MISMATCH": 23, u"UNVERIFIABLE": 18, u"POINTER_NOT_FOUND": 12})

    def test_d_1_doc_table_matches_record(self):
        self.assertEqual(table_problems(self.doc, self.rec), [])

    def test_d_2_doc_prose_numbers_in_record_or_marked(self):
        self.assertEqual(prose_problems(self.doc, self.rec_text), [])

    def test_e_1_seal_unchanged_since_its_commit(self):
        rc, committed = git("show", "%s:%s%s" % (SEAL_COMMIT_SHORT, PREFIX, SEAL_REL))
        if rc != 0:
            self.skipTest(u"封の commit %s が無い clone" % SEAL_COMMIT_SHORT)
        self.assertEqual(committed.rstrip(u"\n"), self.seal.rstrip(u"\n"), u"**封が結果の後で変わっている**")

    def test_f_1_script_imports_and_type_rules_on_synthetic_rows(self):
        self.assertEqual(script_problems(jtext(SCRIPT)), [])
        m = self.mod
        self.assertEqual(m.parse_pointers([u"xbrl:jppfs_cor:NetSales@CurrentYearDuration", u"text:abc"]), ([(u"jppfs_cor:NetSales", u"CurrentYearDuration")], [u"text:abc"]))
        d1 = {u"型": u"D1", u"fact": [{u"name": u"a:X", u"context": u"CY"}], u"v": 1.0}
        d2 = {u"型": u"D2", u"fact": [{u"name": u"a:X", u"context": u"PY"}, {u"name": u"a:X", u"context": u"CY"}], u"v": 1.0}
        P = [(u"a:X", u"CY")]
        self.assertEqual(m.classify([], True, u"導出一致", d1), TYPES_T[0])                       # pointers が空なら T1 が先
        self.assertEqual(m.classify(P, True, u"導出一致", d1), TYPES_T[1])                        # 同じ fact
        self.assertEqual(m.classify(P, True, u"導出一致", d2), TYPES_T[2])                        # 差
        self.assertEqual(m.classify(P, True, u"導出一致", {u"型": u"D1", u"fact": [{u"name": u"a:X", u"context": u"PY"}], u"v": 1.0}), TYPES_T[3])
        self.assertEqual(m.classify(P, True, u"導出一致", {u"型": u"D1", u"fact": [{u"name": u"a:Y", u"context": u"CY"}], u"v": 1.0}), TYPES_T[4])
        self.assertEqual(m.classify(P, True, u"保留", None), TYPES_T[5])
        self.assertEqual(m.classify(P, False, None, None), TYPES_T[5])
        self.assertTrue(m.in_grounds(u"jppfs_cor:OtherNOI", u"jppfs_cor:OtherNOI/CY=37,144,000円"))
        self.assertFalse(m.in_grounds(u"jppfs_cor:RealEstateRentNOI", u"jppfs_cor:OtherNOI/CY=37,144,000円"))
        self.assertIsNone(m.any_in_grounds([], u"x"))
        b = m.band_reference({u"v": -802686000.0}, 802000000.0, 1000000.0)
        self.assertEqual((b[u"round(|d| ≤ u / 2)"], b[u"truncate(0 ≤ d < u)"]), (False, True))
        b = m.band_reference({u"v": 781972000.0}, 782000000.0, 1000000.0)
        self.assertEqual((b[u"round(|d| ≤ u / 2)"], b[u"truncate(0 ≤ d < u)"]), (True, False))

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
        cls.counts = seal_state_counts(cls.seal)

    def test_m_1_flipping_a_judgement_is_caught(self):
        rec = json.loads(self.rec_text)
        rec[u"予測の判定"][u"J-2"] = u"当たり" if rec[u"予測の判定"][u"J-2"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds, self.counts)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"VALUE_MISMATCH で engine の要素が根拠に無い"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"VALUE_MISMATCH で engine の要素が根拠に無い"], rec[u"集計"][u"VALUE_MISMATCH で engine の要素が根拠に無い"])

    def test_m_3_moving_a_row_type_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"型"] == TYPES_T[4]][0]
        r[u"型"] = TYPES_T[3]
        prev = jload(os.path.join(ROOT, "fixtures/xbrl/derivation_subject_2026-11-02.json"))
        entry = {c[u"id"]: c for c in jload(os.path.join(ROOT, "fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json"))[u"claims"]}
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_labels_2026-10-09.json"))[u"labels"]}
        self.assertNotEqual(ref_rows(prev[u"行"], entry, labels)[r[u"id"]][u"型"], r[u"型"])

    def test_m_4_flipping_the_grounds_flag_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"engine の要素が根拠に在る"] is False][0]
        r[u"engine の要素が根拠に在る"] = True
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_labels_2026-10-09.json"))[u"labels"]}
        g = labels[r[u"id"]][u"根拠"]
        self.assertNotEqual(any(p[u"要素"].split(u":")[-1] in g for p in r[u"pointers"]), r[u"engine の要素が根拠に在る"])

    def test_m_5_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_doc_type_table_change_is_caught(self):
        n = self.rec[u"集計"][u"型の件数"][TYPES_T[4]]
        line = u"| **%s** | %d |" % (TYPES_T[4], n)
        self.assertIn(line, self.doc)
        bad = self.doc.replace(line, u"| **%s** | %d |" % (TYPES_T[4], n - 1), 1)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_7_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**10〜18**", u"**10〜30**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad), self.counts)), self.rec[u"予測の判定"])

    def test_m_8_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_9_engine_or_other_script_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport importlib.util\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nspec_from_file_location('x', 'y')\n"), [])

    def test_m_10_dropping_an_id_from_the_doc_is_caught(self):
        i = self.rec[u"集計"][u"導出が engine の取り違えを正した形の id"][0]
        bad = self.doc.replace(i, u"N000")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_11_changing_one_id_inside_a_type_bullet_is_caught(self):
        u"""同じ id が文書の別の場所にも在っても、その型の箇条書きの中の 1 つを書き換えれば赤くなる(T2・T4・T5・正した形)。"""
        blocks = type_blocks(self.doc)
        self.assertEqual(list(blocks.keys()), list(TYPES_T))
        for t, old, new in ((TYPES_T[1], u"N283", u"N284"), (TYPES_T[3], u"N039", u"N038"), (TYPES_T[4], u"N290", u"N291"), (TYPES_T[4], u"N080", u"N081")):
            block = blocks[t]
            self.assertIn(old, block)
            bad = self.doc.replace(block, block.replace(old, new, 1), 1)
            self.assertNotEqual(bad, self.doc)
            self.assertNotEqual(table_problems(bad, self.rec), [], u"%s %s → %s" % (t, old, new))
        # 「正した形」の後の列だけを書き換えても赤くなる
        t5 = blocks[TYPES_T[4]]
        head, tail = t5.split(u"正した形", 1)
        bad = self.doc.replace(t5, head + u"正した形" + tail.replace(u"N290", u"N291", 1), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        # 「別の要素と読める 20」の数
        bad = self.doc.replace(u"別の要素と読める 20", u"別の要素と読める 21")
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])


if __name__ == "__main__":
    unittest.main()
