# -*- coding: utf-8 -*-
u"""門: 文の期の印と engine の context(封 docs/XBRL_PERIOD_MARK_SEAL_2026-11-02.md)。

縛る物:
- 記録 fixtures/xbrl/period_mark_2026-11-02.json の形(封・HEAD・script と材料の sha256・配線の門・key_leaks・docID 無し)。
- 予測 K-1〜K-10 を、記録の集計と封 §4 の幅(封の字から読む)から求め直し、記録の「予測の判定」と文書 §1 の表に一致させる。
- 415 行の印・文の期・engine の期・根拠の期・取り違え・中身(参考)を門自身の code で材料から作り直し、記録と全行一致させる
  (数の位置だけ「その他」の便の script の locate を使う)。
- 集計を行から数え直す。文書の表(§1・§2-2・§2-3)・id・散文の 3 桁以上の数が記録に在る(無い数は【門なし】)。
- script が標準ライブラリ + 「その他」の便の script(importlib)だけで engine を import しない。順序(封 < script・記録・文書・門)。変異で赤くなる。
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

SEAL_REL = "docs/XBRL_PERIOD_MARK_SEAL_2026-11-02.md"
DOC_REL = "docs/XBRL_PERIOD_MARK_2026-11-02.md"
REC_REL = "fixtures/xbrl/period_mark_2026-11-02.json"
SCRIPT_REL = "measure/xbrl_period_mark_2026-11-02.py"
GATE_REL = "tests/measure/test_xbrl_period_mark.py"
SEAL_COMMIT_SHORT = "5a3b2a0"
SEAL, DOC, REC, SCRIPT = (os.path.join(ROOT, r) for r in (SEAL_REL, DOC_REL, REC_REL, SCRIPT_REL))

IDS = tuple(u"K-%d" % i for i in range(1, 11))
MARKS = (u"同", u"前期", u"当期", u"なし")
EP = (u"当期", u"前期", u"2 期前以前", u"他", u"指せず")
DIRS = (u"前期の文 × engine 当期", u"当期の文 × engine 前期")
KINDS = (u"差の文(engine が a − b)", u"札が engine の期と合う(印の読み違い)", u"札が文の期と合う(engine の期の取り違え)", u"札が両方・読めず")
STATES = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
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


# ---------------------------------------------------------------- 封 §4 の幅

def seal_rows(seal):
    out = collections.OrderedDict()
    for l in seal.splitlines():
        m = re.match(r"^\| \*\*(K-\d+)\*\* \| (.*)$", l)
        if m:
            body = m.group(2).rstrip()
            if body.endswith(u"|"):
                body = body[:-1].rstrip()
            out[m.group(1)] = tuple(c.strip() for c in body.split(u" | "))
    return out


def seal_bounds(seal):
    rows = seal_rows(seal)
    b = collections.OrderedDict()
    for i in (u"K-1", u"K-2", u"K-4", u"K-5", u"K-6", u"K-7"):
        m = re.search(r"\*\*(\d+)〜(\d+)\*\*", rows[i][0])
        b[i] = (int(m.group(1)), int(m.group(2)))
    b[u"K-3"] = float(re.search(r"\*\*(\d+)% 以下\*\*", rows[u"K-3"][0]).group(1))
    b[u"K-8"] = int(re.search(r"\*\*(\d+) / \d+\*\*", rows[u"K-8"][0]).group(1))
    b[u"K-9"] = float(re.search(r"\*\*(\d+)% 以下\*\*", rows[u"K-9"][0]).group(1))
    return b


# ---------------------------------------------------------------- 門自身の作り直し(script とは別に書く)

G_PRIOR = (u"前期末", u"前期", u"前年同期", u"前年度", u"前連結会計年度", u"前年")
G_CUR = (u"当期末", u"当期", u"当連結会計年度", u"当年度", u"期末時点")


def g_mark(w):
    if w.endswith(u"(同") or w.endswith(u"(同"):
        return u"同"
    t = w[-14:]
    for x in G_PRIOR:
        if x in t:
            return u"前期"
    for x in G_CUR:
        if x in t:
            return u"当期"
    return u"なし"


def g_engine(pointers):
    for p in pointers or []:
        m = re.match(r"^xbrl:[^@]+@([A-Za-z0-9_\-]+)$", p)
        if m:
            c = m.group(1)
            if c.startswith(u"CurrentYear"):
                return u"当期"
            if c.startswith(u"Prior1Year"):
                return u"前期"
            if re.match(r"^Prior[2-9]Year", c):
                return u"2 期前以前"
            return u"他"
    return u"指せず"


def g_grounds(g):
    g = g or u""
    pr = any(x in g for x in (u"前期", u"Prior1Year", u"前年"))
    cu = any(x in g for x in (u"CY", u"当期", u"CurrentYear", u"当年度"))
    return u"両方" if (pr and cu) else (u"前期" if pr else (u"当期" if cu else u"読めず"))


def g_rows(oth, claims, labels, entry_claims, prev_rows):
    r1 = set(r[u"id"] for r in prev_rows if r.get(u"R1 の判定") == u"決まる")
    out = collections.OrderedDict()
    for c in claims:
        cid = c[u"id"]
        lab = labels.get(cid) or {}
        ec = entry_claims.get(cid) or {}
        text = c.get(u"文") or u""
        r = collections.OrderedDict([(u"数の位置", u"なし"), (u"印", None), (u"文の期", None), (u"取り違え(engine)", None), (u"取り違えの中身(参考)", None),
                                     (u"印の確かめ(札)で違う", None), (u"R1 で決まった行", cid in r1)])
        r[u"engine の期"] = g_engine(ec.get(u"pointers"))
        r[u"根拠の期"] = g_grounds(lab.get(u"根拠")) if lab.get(u"札") == u"真" else None
        rate = c.get(u"単位") in (u"%", u"ポイント")
        if c.get(u"数") is not None:
            toks, hits = oth.locate(text, c[u"数"], c.get(u"単位"))
            r[u"数の位置"] = u"決まる" if len(hits) == 1 else (u"曖昧" if hits else u"なし")
            if len(hits) == 1:
                w = oth.strip_trail(text[:hits[0][u"start"]])
                r[u"印"] = g_mark(w)
                r[u"文の期"] = u"前期" if r[u"印"] in (u"同", u"前期") else u"当期"
                if not rate and r[u"engine の期"] in (u"当期", u"前期"):
                    if r[u"engine の期"] == r[u"文の期"]:
                        r[u"取り違え(engine)"] = u"なし"
                    else:
                        r[u"取り違え(engine)"] = DIRS[0] if r[u"文の期"] == u"前期" else DIRS[1]
                        if ec.get(u"form") == u"derived_value":
                            r[u"取り違えの中身(参考)"] = KINDS[0]
                        elif r[u"根拠の期"] == r[u"engine の期"]:
                            r[u"取り違えの中身(参考)"] = KINDS[1]
                        elif r[u"根拠の期"] == r[u"文の期"]:
                            r[u"取り違えの中身(参考)"] = KINDS[2]
                        else:
                            r[u"取り違えの中身(参考)"] = KINDS[3]
                if r[u"根拠の期"] in (u"当期", u"前期"):
                    r[u"印の確かめ(札)で違う"] = r[u"根拠の期"] != r[u"文の期"]
        out[cid] = r
    return out


def ref_tally(rows):
    T = collections.OrderedDict()
    loc = [r for r in rows if r[u"数の位置"] == u"決まる"]
    T[u"claims"] = len(rows)
    T[u"数の位置"] = collections.OrderedDict((k, sum(1 for r in rows if r[u"数の位置"] == k)) for k in (u"決まる", u"なし", u"曖昧"))
    T[u"位置が決まる行"] = len(loc)
    T[u"印の分布"] = collections.OrderedDict((m, sum(1 for r in loc if r[u"印"] == m)) for m in MARKS)
    T[u"印あり(同 + 前期 + 当期)"] = sum(1 for r in loc if r[u"印"] != u"なし")
    T[u"印 × engine の期"] = collections.OrderedDict((m, collections.OrderedDict((e, sum(1 for r in loc if r[u"印"] == m and r[u"engine の期"] == e)) for e in EP)) for m in MARKS)
    T[u"率の文(位置が決まる)"] = sum(1 for r in loc if r[u"率の文"])
    same = [r for r in loc if r[u"印"] == u"同" and r[u"engine の期"] in (u"当期", u"前期")]
    T[u"印 同 で engine が 当期 か 前期 の行"] = len(same)
    T[u"印 同 で engine が 前期"] = sum(1 for r in same if r[u"engine の期"] == u"前期")
    T[u"印 同 で engine が 前期 の割合"] = None if not same else round(100.0 * T[u"印 同 で engine が 前期"] / len(same), 1)
    mis = [r for r in loc if r[u"取り違え(engine)"] not in (None, u"なし")]
    T[u"取り違え(engine)"] = len(mis)
    T[u"取り違え(engine)の向き"] = collections.OrderedDict((d, sum(1 for r in mis if r[u"取り違え(engine)"] == d)) for d in DIRS)
    T[u"取り違え(engine)の state"] = collections.OrderedDict((s, sum(1 for r in mis if r[u"state"] == s)) for s in STATES)
    T[u"取り違え(engine)の印"] = collections.OrderedDict((m, sum(1 for r in mis if r[u"印"] == m)) for m in MARKS)
    T[u"取り違え(engine)の id"] = [r[u"id"] for r in mis]
    T[u"取り違え(engine)で GROUNDED の id"] = [r[u"id"] for r in mis if r[u"state"] == u"GROUNDED"]
    T[u"取り違えの中身(参考)"] = collections.OrderedDict((k, sum(1 for r in mis if r[u"取り違えの中身(参考)"] == k)) for k in KINDS)
    T[u"取り違えの中身(参考)× 向き"] = collections.OrderedDict((d, collections.OrderedDict((k, sum(1 for r in mis if r[u"取り違え(engine)"] == d and r[u"取り違えの中身(参考)"] == k)) for k in KINDS)) for d in DIRS)
    T[u"取り違えの中身(参考)× GROUNDED"] = collections.OrderedDict((k, sum(1 for r in mis if r[u"state"] == u"GROUNDED" and r[u"取り違えの中身(参考)"] == k)) for k in KINDS)
    T[u"取り違えの中身(参考)の id"] = collections.OrderedDict((k, [r[u"id"] for r in mis if r[u"取り違えの中身(参考)"] == k]) for k in KINDS)
    T[u"取り違え(engine)で R1 で決まった行"] = sum(1 for r in mis if r[u"R1 で決まった行"])
    chk = [r for r in loc if r[u"印の確かめ(札)で違う"] is not None]
    T[u"印の確かめ(札)を当てた行"] = len(chk)
    T[u"印の確かめ(札)で違う"] = sum(1 for r in chk if r[u"印の確かめ(札)で違う"])
    T[u"印の確かめ(札)で違う id"] = [r[u"id"] for r in chk if r[u"印の確かめ(札)で違う"]]
    byid = {r[u"id"]: r for r in rows}
    T[u"配線: N081・N145 が 印 同・engine 当期"] = sum(1 for i in (u"N081", u"N145") if byid[i][u"印"] == u"同" and byid[i][u"engine の期"] == u"当期")
    none_rows = [r for r in loc if r[u"印"] == u"なし" and not r[u"率の文"] and r[u"engine の期"] in (u"当期", u"前期")]
    T[u"印なし(率でなく engine が 当期 か 前期)"] = len(none_rows)
    T[u"印なし で engine が 前期"] = sum(1 for r in none_rows if r[u"engine の期"] == u"前期")
    T[u"印なし で engine が 前期 の割合"] = None if not none_rows else round(100.0 * T[u"印なし で engine が 前期"] / len(none_rows), 1)
    T[u"印なし で engine が 前期 の id"] = [r[u"id"] for r in none_rows if r[u"engine の期"] == u"前期"]
    T[u"engine の期の分布(位置が決まる)"] = collections.OrderedDict((e, sum(1 for r in loc if r[u"engine の期"] == e)) for e in EP)
    return T


def ref_judge(T, b):
    J = collections.OrderedDict()
    J[u"K-1"] = b[u"K-1"][0] <= T[u"印あり(同 + 前期 + 当期)"] <= b[u"K-1"][1]
    J[u"K-2"] = b[u"K-2"][0] <= T[u"印の分布"][u"同"] <= b[u"K-2"][1]
    J[u"K-3"] = T[u"印 同 で engine が 前期 の割合"] is not None and T[u"印 同 で engine が 前期 の割合"] <= b[u"K-3"]
    J[u"K-4"] = b[u"K-4"][0] <= T[u"取り違え(engine)の向き"][DIRS[0]] <= b[u"K-4"][1]
    J[u"K-5"] = b[u"K-5"][0] <= T[u"取り違え(engine)の向き"][DIRS[1]] <= b[u"K-5"][1]
    J[u"K-6"] = b[u"K-6"][0] <= T[u"取り違え(engine)の state"][u"GROUNDED"] <= b[u"K-6"][1]
    J[u"K-7"] = b[u"K-7"][0] <= T[u"印の確かめ(札)で違う"] <= b[u"K-7"][1]
    J[u"K-8"] = T[u"配線: N081・N145 が 印 同・engine 当期"] == b[u"K-8"] and T[u"配線: N039 の印と engine の期"][u"engine の期"] == u"当期"
    J[u"K-9"] = T[u"印なし で engine が 前期 の割合"] is not None and T[u"印なし で engine が 前期 の割合"] <= b[u"K-9"]
    out = collections.OrderedDict((k, u"当たり" if v else u"外れ") for k, v in J.items())
    out[u"K-10"] = u"判定しない"
    out[u"当たり"] = sum(1 for v in J.values() if v)
    out[u"外れ"] = sum(1 for v in J.values() if not v)
    return out


# ---------------------------------------------------------------- 文書

def doc_rows(doc):
    out = collections.OrderedDict()
    for l in doc.splitlines():
        m = re.match(r"^\| \*\*(K-\d+)\*\* \| (.*)\|\s*$", l)
        if m:
            out[m.group(1)] = tuple(c.strip() for c in m.group(2).split(u" | "))
    return out


def expected_cells(T):
    return {
        u"K-1": [u"%d" % T[u"印あり(同 + 前期 + 当期)"]], u"K-2": [u"%d" % T[u"印の分布"][u"同"]],
        u"K-3": [u"%s%%(%d / %d)" % (T[u"印 同 で engine が 前期 の割合"], T[u"印 同 で engine が 前期"], T[u"印 同 で engine が 当期 か 前期 の行"])],
        u"K-4": [u"%d" % T[u"取り違え(engine)の向き"][DIRS[0]]], u"K-5": [u"%d" % T[u"取り違え(engine)の向き"][DIRS[1]]],
        u"K-6": [u"%d" % T[u"取り違え(engine)の state"][u"GROUNDED"]], u"K-7": [u"%d" % T[u"印の確かめ(札)で違う"]],
        u"K-8": [u"%d / 2" % T[u"配線: N081・N145 が 印 同・engine 当期"], u"N039 は engine %s" % T[u"配線: N039 の印と engine の期"][u"engine の期"]],
        u"K-9": [u"%s%%(%d / %d)" % (T[u"印なし で engine が 前期 の割合"], T[u"印なし で engine が 前期"], T[u"印なし(率でなく engine が 当期 か 前期)"])],
        u"K-10": [u"率の文 %d" % T[u"率の文(位置が決まる)"], u"2 期前以前 %d" % T[u"engine の期の分布(位置が決まる)"][u"2 期前以前"],
                  u"位置なし %d" % T[u"数の位置"][u"なし"], u"曖昧 %d" % T[u"数の位置"][u"曖昧"]],
    }


def table_problems(doc, rec):
    p = []
    rows = doc_rows(doc)
    if tuple(rows.keys()) != IDS:
        return [u"表の行が K-1〜K-10 でない: %s" % list(rows.keys())]
    J, T = rec[u"予測の判定"], rec[u"集計"]
    exp = expected_cells(T)
    for i in IDS:
        cells = rows[i]
        if len(cells) != 3:
            p.append(u"%s の欄が 3 でない" % i)
            continue
        want = u"判定しない" if i == u"K-10" else u"**%s**" % J[i]
        if cells[2] != want:
            p.append(u"%s の判定が %s でない" % (i, want))
        for s in exp[i]:
            if s not in cells[1]:
                p.append(u"%s の実測の欄に %s が無い" % (i, s))
        if i in (u"K-1", u"K-2", u"K-4", u"K-5", u"K-6", u"K-7") and not re.match(r"^\d+(\D|$)", cells[1]):
            p.append(u"%s の実測の欄が数で始まらない" % i)
    head = doc.splitlines()[0]
    if u"当たり %d / 外れ %d" % (J[u"当たり"], J[u"外れ"]) not in head:
        p.append(u"見出しの当たり / 外れの数")
    misses = [i for i in IDS if J.get(i) == u"外れ"]
    if u"(%s)" % u"・".join(misses) not in head:
        p.append(u"見出しの外れの ID")
    for m in MARKS:
        X = T[u"印 × engine の期"][m]
        want = u"| **%s** | %d | %d | %d | %d | %d |" % (m, X[u"当期"], X[u"前期"], X[u"2 期前以前"], X[u"他"], X[u"指せず"])
        if want not in doc:
            p.append(u"印 × engine の表の行(%s)" % want)
    for k in KINDS:
        V = T[u"取り違えの中身(参考)× 向き"]
        want = u"| %s | %d | %d | %d | %s |" % (k, V[DIRS[0]][k], V[DIRS[1]][k], T[u"取り違えの中身(参考)× GROUNDED"][k], u"・".join(T[u"取り違えの中身(参考)の id"][k]))
        if want not in doc:
            p.append(u"中身の表の行(%s)" % want)
    for s in (u"位置が決まる %d" % T[u"位置が決まる行"], u"印あり %d" % T[u"印あり(同 + 前期 + 当期)"],
              u"数の位置が前の便の記録と一致した行 %d / %d" % (rec[u"配線の門"][u"(d) 数の位置が「その他」の便の記録と一致した行"], T[u"claims"]),
              u"当期 %d・前期 %d・2 期前以前 %d・他 %d・指せず %d" % tuple(T[u"engine の期の分布(位置が決まる)"].values()),
              u"印なし %d" % T[u"印の分布"][u"なし"], u"率の文 %d" % T[u"率の文(位置が決まる)"],
              u"印なし で engine が 前期 の割合 %s%%" % T[u"印なし で engine が 前期 の割合"],
              u"取り違え %d" % T[u"取り違え(engine)"] if False else u"違う %d 行" % T[u"取り違え(engine)"],
              u"R1 で決まった行 %d" % rec[u"配線の門"][u"(f) R1 で決まった行(前の便の記録)"],
              u"印の確かめ(札)で違う %d" % T[u"印の確かめ(札)で違う"]):
        if s not in doc:
            p.append(u"文書に「%s」が無い" % s)
    for i in T[u"印の確かめ(札)で違う id"] + T[u"印なし で engine が 前期 の id"] + T[u"取り違え(engine)の id"]:
        if i not in doc:
            p.append(u"id %s が文書に無い" % i)
    # 印の確かめで違う 7 の id の列(括弧の中。順も同じ)
    if u"(%s)" % u"・".join(T[u"印の確かめ(札)で違う id"]) not in doc:
        p.append(u"印の確かめで違う id の列が文書に無い")
    if u"(%s)" % u"・".join(T[u"印なし で engine が 前期 の id"]) not in doc:
        p.append(u"印なし で engine が 前期 の id の列が文書に無い")
    # engine の期の取り違え(前期の文 × engine 当期)の印の内訳(§2-4)
    eight = [r for r in rec[u"行"] if r[u"取り違えの中身(参考)"] == KINDS[2] and r[u"取り違え(engine)"] == DIRS[0]]
    s = u"止めた行が %d**(全部 VALUE_MISMATCH。うち %d は「(同」、%d は「前期末」「前期」)" % (len(eight), sum(1 for r in eight if r[u"印"] == u"同"), sum(1 for r in eight if r[u"印"] == u"前期"))
    if s not in doc:
        p.append(u"文書に「%s」が無い" % s)
    if not all(r[u"state"] == u"VALUE_MISMATCH" for r in eight):
        p.append(u"engine の期の取り違え(前期の文 × engine 当期)に VALUE_MISMATCH でない行が在る")
    return p


def prose_problems(doc, rec_text):
    p = []
    for ln in doc.splitlines():
        if ln.startswith(u"|") or ln.startswith(u"#") or not ln.strip():
            continue
        s = re.sub(r"`[^`]*`", u" ", ln)
        s = re.sub(r"\d{4}-\d{2}-\d{2}", u" ", s)
        s = re.sub(r"K-\d+|R\d|T\d|P\d+|§\d+(-\d+)*", u" ", s)
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
    for bad in ("adapters", "audit_core", "core", "urllib", "http", "socket", "zipfile"):
        if re.search(r"^\s*(import|from)\s+%s\b" % bad, src, re.M):
            p.append(u"%s を import" % bad)
    for f in re.findall(r"spec_from_file_location\([^,]+,\s*([^)]*)\)", src):
        if "ROOT, rel" not in f:
            p.append(u"importlib で読む file が材料の経路でない: %s" % f)
    for m in re.findall(r'load_module\(MATERIALS\[u"([a-z_]+)"\]', src):
        if m != "prev_script":
            p.append(u"importlib で読む材料が「その他」の便の script でない: %s" % m)
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
        cls.mod = load(SCRIPT, "period_mark_under_test")
        M = cls.mod.MATERIALS
        cls.oth = load(os.path.join(ROOT, M[u"prev_script"][0]), "other_rule_for_period_mark_gate")
        cls.claims = jload(os.path.join(ROOT, M[u"claims"][0]))[u"claims"]
        cls.labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, M[u"labels"][0]))[u"labels"]}
        cls.entry = jload(os.path.join(ROOT, M[u"entry"][0]))
        cls.entry_claims = {c[u"id"]: c for c in cls.entry[u"claims"]}
        cls.prev = jload(os.path.join(ROOT, M[u"prev_rec"][0]))

    def test_a_1_keys_constants_and_wiring(self):
        for k in (u"注意", u"封", u"HEAD の commit", u"この script の sha256", u"読んだ材料の sha256", u"定数", u"配線の門", u"行", u"集計", u"予測の判定", u"limits", u"key_leaks"):
            self.assertIn(k, self.rec)
        self.assertEqual(self.rec[u"封"], {u"file": SEAL_REL, u"commit": SEAL_COMMIT_SHORT})
        self.assertTrue(self.rec[u"HEAD の commit"].startswith(SEAL_COMMIT_SHORT), u"記録の HEAD が封の commit でない")
        self.assertEqual(self.rec[u"key_leaks"], [])
        W = self.rec[u"配線の門"]
        self.assertTrue(W[u"通った"])
        self.assertEqual(W[u"(c) entry の profile"], u"P16")
        self.assertEqual(W[u"(d) 数の位置が「その他」の便の記録と一致した行"], len(self.rec[u"行"]))
        self.assertEqual(len(self.rec[u"行"]), 415)
        with io.open(SCRIPT, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), self.rec[u"この script の sha256"])
        for rel, want in self.rec[u"読んだ材料の sha256"].items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), want, rel)
        self.assertEqual(sorted(self.rec[u"読んだ材料の sha256"].keys()), sorted(rel for rel, _ in self.mod.MATERIALS.values()))
        self.assertEqual(len(self.mod.MATERIALS), 5)
        self.assertEqual(self.rec_text.count("scratchpad"), 0)
        self.assertEqual(self.mod.SEAL_COMMIT, SEAL_COMMIT_SHORT)

    def test_a_2_no_docid_in_record_doc_script_gate(self):
        self.assertEqual(DOCID_RE.findall(self.rec_text), [])
        for p in (DOC, SCRIPT, __file__):
            self.assertEqual(DOCID_RE.findall(jtext(p)), [], p)

    def test_b_1_rows_recomputed_by_the_script(self):
        rows = self.mod.build_rows(self.oth, self.claims, self.labels, self.entry_claims, self.prev[u"行"])
        self.assertEqual(json.loads(json.dumps(rows, ensure_ascii=False)), self.rec[u"行"])
        self.assertEqual(json.loads(json.dumps(self.mod.judge(self.mod.tally(rows)), ensure_ascii=False)), self.rec[u"予測の判定"])

    def test_b_2_rows_recomputed_with_the_gates_own_code(self):
        ref = g_rows(self.oth, self.claims, self.labels, self.entry_claims, self.prev[u"行"])
        self.assertEqual(list(ref.keys()), [r[u"id"] for r in self.rec[u"行"]])
        prev_loc = {r[u"id"]: r[u"数の位置"] for r in self.prev[u"行"]}
        for r in self.rec[u"行"]:
            x = ref[r[u"id"]]
            for k in (u"数の位置", u"印", u"文の期", u"engine の期", u"根拠の期", u"取り違え(engine)", u"取り違えの中身(参考)", u"印の確かめ(札)で違う", u"R1 で決まった行"):
                self.assertEqual(r[k], x[k], u"%s %s" % (r[u"id"], k))
            self.assertEqual(r[u"数の位置"], prev_loc[r[u"id"]], r[u"id"])
            self.assertEqual(r[u"札"], self.labels[r[u"id"]][u"札"])
            self.assertEqual(r[u"state"], (self.entry_claims.get(r[u"id"]) or {}).get(u"state"))
            self.assertEqual(r[u"form"], (self.entry_claims.get(r[u"id"]) or {}).get(u"form"))
            self.assertEqual(r[u"率の文"], r[u"単位"] in (u"%", u"ポイント"))
            if r[u"印"] is not None:
                self.assertEqual(r[u"文の期"], u"前期" if r[u"印"] in (u"同", u"前期") else u"当期")
                self.assertEqual(r[u"W の末尾"], r[u"W の末尾"][-14:])
            if r[u"取り違え(engine)"] not in (None, u"なし"):
                self.assertFalse(r[u"率の文"])
                self.assertNotEqual(r[u"engine の期"], r[u"文の期"])
                self.assertIn(r[u"engine の期"], (u"当期", u"前期"))
                self.assertIn(r[u"取り違えの中身(参考)"], KINDS)
            else:
                self.assertIsNone(r[u"取り違えの中身(参考)"])

    def test_b_3_tally_recomputed(self):
        T, R = ref_tally(self.rec[u"行"]), self.rec[u"集計"]
        for k in T:
            self.assertEqual(json.loads(json.dumps(T[k], ensure_ascii=False)), R[k], k)
        n = self.rec[u"集計"][u"配線: N039 の印と engine の期"]
        r = [x for x in self.rec[u"行"] if x[u"id"] == u"N039"][0]
        self.assertEqual((n[u"印"], n[u"engine の期"], n[u"根拠の期"]), (r[u"印"], r[u"engine の期"], r[u"根拠の期"]))

    def test_c_1_judgement_recomputed_from_seal_widths(self):
        self.assertEqual(dict(ref_judge(self.rec[u"集計"], self.bounds)), self.rec[u"予測の判定"])
        self.assertEqual(self.rec[u"予測の判定"][u"当たり"] + self.rec[u"予測の判定"][u"外れ"], 9)
        want = dict((k, tuple(v) if isinstance(v, list) else v) for k, v in self.rec[u"定数"][u"予測の幅"].items())
        self.assertEqual(want, dict(self.bounds), u"script の幅が封の字と違う")

    def test_c_2_seal_widths_are_the_sealed_ones(self):
        self.assertEqual(dict(self.bounds), {u"K-1": (90, 180), u"K-2": (20, 60), u"K-3": 50.0, u"K-4": (10, 40), u"K-5": (0, 8), u"K-6": (0, 4), u"K-7": (0, 5), u"K-8": 2, u"K-9": 15.0})

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
        self.assertEqual(m.mark_of(u"その他37百万円(同"), u"同")
        self.assertEqual(m.mark_of(u"従業員数は1,462名(前期末"), u"前期")
        self.assertEqual(m.mark_of(u"前期末の1,751百万円から"), u"前期")              # 差の文も 前期 と読む(封 §1-3 の限界)
        self.assertEqual(m.mark_of(u"額が前期890百万円から当期"), u"前期")            # 前期の字を先に当てる
        self.assertEqual(m.mark_of(u"総資産は期末時点で"), u"当期")
        self.assertEqual(m.mark_of(u"売上高は"), u"なし")
        self.assertEqual(m.mark_of(u"前期末" + u"あ" * 14 + u"売上高"), u"なし")       # 末尾 14 字の外は見ない
        self.assertEqual(m.text_period(u"同"), u"前期")
        self.assertEqual(m.text_period(u"なし"), u"当期")
        self.assertEqual(m.engine_period([u"xbrl:a:X@CurrentYearDuration"])[0], u"当期")
        self.assertEqual(m.engine_period([u"xbrl:a:X@Prior1YearInstant", u"xbrl:a:X@CurrentYearInstant"])[0], u"前期")
        self.assertEqual(m.engine_period([u"xbrl:a:X@Prior2YearDuration"])[0], u"2 期前以前")
        self.assertEqual(m.engine_period([u"xbrl:a:X@FilingDateInstant"])[0], u"他")
        self.assertEqual(m.engine_period([])[0], u"指せず")
        self.assertEqual(m.grounds_period(u"jppfs_cor:X/CY(2025-07-01~2026-06-30)=1円"), u"当期")
        self.assertEqual(m.grounds_period(u"同/前期末(2025-06-30)=1円"), u"前期")
        self.assertEqual(m.grounds_period(u"当期末=1、前期末=1"), u"両方")
        self.assertEqual(m.grounds_period(u"1,000-500=500円"), u"読めず")
        self.assertEqual(m.kind_of(u"derived_value", u"読めず", u"当期", u"前期"), KINDS[0])
        self.assertEqual(m.kind_of(u"direct_value", u"当期", u"当期", u"前期"), KINDS[1])
        self.assertEqual(m.kind_of(u"direct_value", u"前期", u"当期", u"前期"), KINDS[2])
        self.assertEqual(m.kind_of(u"direct_value", u"両方", u"当期", u"前期"), KINDS[3])

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
        rec[u"予測の判定"][u"K-6"] = u"当たり" if rec[u"予測の判定"][u"K-6"] == u"外れ" else u"外れ"
        self.assertNotEqual(dict(ref_judge(rec[u"集計"], self.bounds)), rec[u"予測の判定"])

    def test_m_2_changing_a_tally_is_caught_by_recount(self):
        rec = json.loads(self.rec_text)
        rec[u"集計"][u"取り違え(engine)の state"][u"GROUNDED"] -= 1
        self.assertNotEqual(ref_tally(rec[u"行"])[u"取り違え(engine)の state"], rec[u"集計"][u"取り違え(engine)の state"])

    def test_m_3_moving_a_row_mark_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"印"] == u"同"][0]
        r[u"印"] = u"なし"
        prev = jload(os.path.join(ROOT, "fixtures/xbrl/other_rule_2026-11-02.json"))
        oth = load(os.path.join(ROOT, "measure/xbrl_other_rule_2026-11-02.py"), "other_rule_for_period_mark_mut")
        claims = jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_claims_unlabelled_2026-10-09.json"))[u"claims"]
        labels = {x[u"id"]: x for x in jload(os.path.join(ROOT, "fixtures/xbrl/ai_prose_labels_2026-10-09.json"))[u"labels"]}
        entry = {c[u"id"]: c for c in jload(os.path.join(ROOT, "fixtures/xbrl/entry_output_S100Z4Q1_ai_prose_2026-10-13.json"))[u"claims"]}
        self.assertNotEqual(g_rows(oth, claims, labels, entry, prev[u"行"])[r[u"id"]][u"印"], r[u"印"])

    def test_m_4_doc_verdict_swap_is_caught(self):
        bad = self.doc.replace(u"| **外れ** |", u"| **当たり** |", 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_5_doc_tables_change_is_caught(self):
        X = self.rec[u"集計"][u"印 × engine の期"][u"同"]
        line = u"| **同** | %d | %d |" % (X[u"当期"], X[u"前期"])
        self.assertIn(line, self.doc)
        bad = self.doc.replace(line, u"| **同** | %d | %d |" % (X[u"当期"] + 1, X[u"前期"] - 1), 1)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        k = KINDS[2]
        line = [l for l in self.doc.splitlines() if l.startswith(u"| %s |" % k)][0]
        bad = self.doc.replace(line, line.replace(u"N039", u"N038", 1), 1)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        bad = self.doc.replace(u"(N036・", u"(N035・")      # 印の確かめで違う id の列(文書に 2 か所。両方変える)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])
        bad = self.doc.replace(u"うち 5 は「(同」、3 は", u"うち 3 は「(同」、5 は")   # 監査で見つかった件数の取り違え(2 桁以下の数を縛る例)
        self.assertNotEqual(bad, self.doc)
        self.assertNotEqual(table_problems(bad, self.rec), [])

    def test_m_6_seal_width_change_changes_reference(self):
        bad = self.seal.replace(u"**0〜4**", u"**0〜40**")
        self.assertNotEqual(bad, self.seal)
        self.assertNotEqual(dict(ref_judge(self.rec[u"集計"], seal_bounds(bad))), self.rec[u"予測の判定"])

    def test_m_7_unbound_prose_number_is_caught(self):
        self.assertNotEqual(prose_problems(self.doc + u"\n記録に無い 123456 を書いた行。\n", self.rec_text), [])

    def test_m_8_engine_import_is_caught(self):
        self.assertNotEqual(script_problems(jtext(SCRIPT) + u"\nimport adapters.xbrl.instance\n"), [])
        self.assertNotEqual(script_problems(jtext(SCRIPT).replace(u'load_module(MATERIALS[u"prev_script"]', u'load_module(MATERIALS[u"prev_rec"]')), [])

    def test_m_9_kind_change_in_record_is_caught(self):
        rec = json.loads(self.rec_text)
        r = [x for x in rec[u"行"] if x[u"取り違えの中身(参考)"] == KINDS[0]][0]
        r[u"取り違えの中身(参考)"] = KINDS[2]
        T = ref_tally(rec[u"行"])
        self.assertNotEqual(T[u"取り違えの中身(参考)"], rec[u"集計"][u"取り違えの中身(参考)"])
        self.assertNotEqual(r[u"form"], u"direct_value")   # derived_value の行は 差の文 と決まる(門自身の作り直しで赤くなる)

    def test_m_10_dropping_an_id_from_the_doc_is_caught(self):
        for i in (u"N266", u"N219"):
            bad = self.doc.replace(i, u"N000")
            self.assertNotEqual(bad, self.doc)
            self.assertNotEqual(table_problems(bad, self.rec), [])


if __name__ == "__main__":
    unittest.main()
