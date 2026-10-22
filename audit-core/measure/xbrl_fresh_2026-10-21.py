# -*- coding: utf-8 -*-
u"""新しい標本 30 書類で P22・P23・P24・P25・P26 を並べ、既定を決める ― 封 ``docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md`` §2〜§4 の測定。

    cd audit-core
    python3 measure/xbrl_fresh_2026-10-21.py --stage plain  --out <scratch の file>              # (A)(B)(C)の行と読むための材料。注入なし(約 五分)
    python3 measure/xbrl_fresh_2026-10-21.py --stage inject --out <scratch の file> [--docs A,B]   # (D)の注入(重い)
    python3 measure/xbrl_fresh_2026-10-21.py --stage all --readings <読みの file> --out fixtures/xbrl/fresh/fresh_2026-10-21.json

**0 USD・通信なし・鍵の値は読まない・席は呼ばない。** 書類は取得の記録 ``fixtures/xbrl/fresh/fetched_2026-10-21.json`` の「使う」30 件(引いた順)で、
生 ZIP は ``~/.cache/audit-core/edinet-fresh-2026-10-21/`` から読む(sha256 を記録と照らす)。**既存の cache ``~/.cache/audit-core/edinet/`` は読まず、書かない。**
engine(``core/``・``adapters/``)は 1 字も変えない。``adapters.xbrl.edinet.CACHE_DIR`` は**この process の中だけ**新しい folder に向ける(注入の道具
``xbrl_a_core_vs_grep`` が ``ED.cache_path`` で書類を読むため。終われば戻す)。

  (A) 無改変: 30 書類の全 claim を P22・P23・P24・P25・P26 で。state の数と率。
  (B) 新 GROUNDED(P22 が GROUNDED でなく、候補が GROUNDED)を候補 P26・P25・P24 ごとに全部。
  (C) 「違う」が弱まった行(P22 が VALUE_MISMATCH、候補が POINTER_NOT_FOUND か UNVERIFIABLE)を候補ごとに全部。
  (D) 注入: 30 書類で P22 が GROUNDED の数の claim に、``measure/inject.py`` の型(T1_VALUE・T2_UNIT・T5_COINCIDENT。T3_ABSENT は挿入文)で 1 回に 1 件。
      種は ``measure/SEED.json``(git に追跡され、コミットの内容と一致していること)。型ごとに 1 書類あたり ``INJECT_CAP`` 件まで(``IJ.select`` の順)。
  F-4  P23 → P25 の新 GROUNDED の claim あたりの率。
  読み  (B)(C)の行は実装席のエージェントが 1 行ずつ読む(**人間の読みではない**)。読みは ``--readings`` の file から行に写す(行と読みは 1 対 1)。
  判定  封 §3 の K-1・K-2・K-3 を候補ごとに記録の数から計算し、P26 → P25 → P24 の順に全部満たす最初を既定にする(満たさなければ P22)。
  予測  封 §4 の F-1〜F-5 を封の字のまま機械で当てる。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import hashlib
import importlib.util
import io
import json
import multiprocessing
import os
import platform
import re
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))


def _mod(rel, name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


LB = _mod("measure/xbrl_lastbranch_2026-10-21.py", "lastbranch_for_fresh")
A1 = _mod("measure/xbrl_a_core_vs_grep_2026-10-17.py", "a_core_for_fresh")
IJ = A1.IJ
FP = LB.FP

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import instance as I          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL = "docs/XBRL_FRESH_SAMPLE_SEAL_2026-10-21.md"
FETCHED_REL = "fixtures/xbrl/fresh/fetched_2026-10-21.json"
DRAW_REL = "fixtures/xbrl/fresh/draw_2026-10-21.json"
OUT_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FRESH_DIR = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-fresh-2026-10-21")
EXISTING_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
SEED_FILE = os.path.join(HERE, "SEED.json")
P26_COMMIT = "b778dd9"                 # P26 段 1(封 §3 の「取得より前に commit された」の対象)
FETCH_SCRIPT_COMMIT = "13575ab"

PROFILES = ("P22", "P23", "P24", "P25", "P26")
CANDIDATES = ("P26", "P25", "P24")     # 封 §3 の順(P26 の commit が取得より前のとき)
STATES = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
TOLD = (u"GROUNDED", u"VALUE_MISMATCH", u"UNVERIFIABLE", u"POINTER_NOT_FOUND")
INJECT_TYPES = ("T1_VALUE", "T2_UNIT", "T5_COINCIDENT", "T3_ABSENT")
INJECT_CAP = 40                        # 型ごと・1 書類あたり(A1.CAP の最大 40 と同じ)。結果を見る前に固定した
TOL = A1.TOL
BASE_67_NEW_G = (148, 7799)            # 封 §4 F-4: 67 書類の P23 → P25 の新 GROUNDED / claim
READ_OK, READ_WRONG, READ_UNSURE = u"正しい文", u"文が本当に違う", u"分からない"
READ_TRUE, READ_FALSE, READ_SEMI = u"正", u"偽", u"準偽"
WORDS_B = (READ_TRUE, READ_FALSE, READ_SEMI)
WORDS_C = (READ_OK, READ_WRONG, READ_UNSURE)
KEY_NAMES = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "EDINET_API_KEY", "OPENAI_API_KEY")


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def frac(a, b):
    return {u"件": a, u"分母": b, u"率": pct(a, b)}


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git(*a):
    return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)


def used_docs():
    f = jload(FETCHED_REL)
    rows = dict((r["docID"], r) for r in f[u"取得した書類"])
    return list(f[u"使う書類"]), rows, f


def read_zip(doc, rows):
    p = os.path.join(FRESH_DIR, "%s.zip" % doc)
    with io.open(p, "rb") as fh:
        b = fh.read()
    if sha_bytes(b) != rows[doc]["sha256"]:
        raise SystemExit(u"**ZIP の sha256 が取得の記録と違う: %s。止める**" % doc)
    return b


# ====================================================================================================
# (A)(B)(C): 無改変
def _pack(c, raw):
    r = raw.get(c["id"], {})
    return {u"state": c["state"], u"reason": c["reason"], u"pointers": list(c["pointers"] or []), u"recomputed": c["recomputed"],
            u"form": c["form"], u"sentence": r.get("sentence"), u"pos": r.get("pos")}


def _dossier(inst, raw_row, c, sent):
    if c["value"] is None or c["unit"] not in V.UNIT_SCALE:
        return {}
    try:
        return LB.dossier(inst, dict(raw_row, pointer=(c["pointers"] or [None])[0], recomputed=c["recomputed"]), sent, c["value"], c["unit"])
    except Exception as e:      # 読むための材料だけ。判定には使わない
        return {u"dossier の失敗": repr(e)}


def plain_doc(doc, zb):
    inst = I.load_instance(zb)
    per, raws, sents, outs = {}, {}, {}, {}
    for p in PROFILES:
        with LB._RawTap() as tap:
            out, raw, sentences = LB.verify_raw(tap, zb, p)
        outs[p], raws[p], sents[p] = out, raw, sentences
        per[p] = dict((c["id"], c) for c in out["claims"])
    ids = [c["id"] for c in outs["P22"]["claims"]]
    mism = dict((p, sorted(set(per[p]) ^ set(ids))) for p in PROFILES if set(per[p]) != set(ids))
    claims, moved = [], []
    for cid in ids:
        base = per["P22"][cid]
        row = {u"id": cid, u"states": [(per[p][cid]["state"] if cid in per[p] else None) for p in PROFILES],
               u"reasons": [(per[p][cid]["reason"] if cid in per[p] else None) for p in PROFILES]}
        claims.append(row)
        v = dict((p, _pack(per[p][cid], raws[p]) if cid in per[p] else None) for p in PROFILES)
        if all(v[p] is not None and v[p][u"state"] == base["state"] for p in PROFILES) and all(
                v[p][u"pointers"] == v["P22"][u"pointers"] for p in PROFILES):
            continue
        # 動いた行(P22 と state か pointers が違う)だけ、読むための材料を持つ
        sent = u""
        si = (v["P22"] or {}).get(u"sentence")
        if si is not None and si < len(sents["P22"]):
            sent = sents["P22"][si]
        dos = {}
        for p in PROFILES:
            if v[p] is None:
                continue
            si_p = v[p][u"sentence"]
            sp = sents[p][si_p] if (si_p is not None and si_p < len(sents[p])) else sent
            dos[p] = _dossier(inst, raws[p].get(cid, {}), per[p][cid], sp)
        moved.append({u"doc": doc, u"id": cid, u"kind": base["kind"], u"subject": base["subject"], u"unit": base["unit"], u"value": base["value"],
                      u"word": base["word"], u"span": base["span"], u"文": sent[:600], u"views": v, u"dossier": dos})
    return {u"doc": doc, u"claims": len(ids), u"states": dict((p, dict(collections.Counter(c["state"] for c in outs[p]["claims"]))) for p in PROFILES),
            u"id が合わない": mism}, claims, moved


def _plain_worker(args):
    doc, zb = args
    return plain_doc(doc, zb)


def run_plain(docs, rows, procs):
    jobs = [(d, read_zip(d, rows)) for d in docs]
    ctx = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(max_workers=procs, mp_context=ctx) as ex:
        res = list(ex.map(_plain_worker, jobs))
    per_doc = [r[0] for r in res]
    claims = dict((r[0][u"doc"], r[1]) for r in res)
    moved = [m for r in res for m in r[2]]
    return per_doc, claims, moved


def state_counts(claims_by_doc, i):
    c = collections.Counter()
    for rows in claims_by_doc.values():
        for r in rows:
            c[r[u"states"][i]] += 1
    return c


def summarize_A(per_doc, claims_by_doc):
    n = sum(d[u"claims"] for d in per_doc)
    out = {u"書類": len(per_doc), u"claim": n}
    for i, p in enumerate(PROFILES):
        c = state_counts(claims_by_doc, i)
        out[p] = dict((s, frac(c.get(s, 0), n)) for s in STATES)
    return out


def reading_key_b(r, cand):
    return u"%s:%s:%s" % (r[u"doc"], r[u"id"], u",".join(r[u"views"][cand][u"pointers"]))


def reading_key_c(r):
    return u"%s:%s" % (r[u"doc"], r[u"id"])


def build_bc(moved):
    u"""(B)(C)の行を候補ごとに。行は moved の (doc, id)。"""
    B, C = {}, {}
    for cand in CANDIDATES:
        B[cand] = [{u"doc": r[u"doc"], u"id": r[u"id"], u"key": reading_key_b(r, cand), u"P22": r[u"views"]["P22"][u"state"], cand: r[u"views"][cand][u"state"]}
                   for r in moved if r[u"views"]["P22"][u"state"] != "GROUNDED" and r[u"views"][cand] and r[u"views"][cand][u"state"] == "GROUNDED"]
        C[cand] = [{u"doc": r[u"doc"], u"id": r[u"id"], u"key": reading_key_c(r), u"P22": r[u"views"]["P22"][u"state"], cand: r[u"views"][cand][u"state"],
                    u"reason": r[u"views"][cand][u"reason"]}
                   for r in moved if r[u"views"]["P22"][u"state"] == "VALUE_MISMATCH" and r[u"views"][cand]
                   and r[u"views"][cand][u"state"] in ("POINTER_NOT_FOUND", "UNVERIFIABLE")]
    return B, C


def new_g_p23_p25(claims_by_doc):
    i23, i25 = PROFILES.index("P23"), PROFILES.index("P25")
    k = 0
    for rows in claims_by_doc.values():
        for r in rows:
            if r[u"states"][i23] != "GROUNDED" and r[u"states"][i25] == "GROUNDED":
                k += 1
    return k


# ====================================================================================================
# (D): 注入
def _find_base_claim(base_claims, inj, text):
    u"""注入の元の数に当たる、無改変の P22 の claim(1 件に決まるときだけ)。"""
    t = inj["type"]
    d = inj["detail"]
    if t == "T3_ABSENT":
        return None
    if t == "T1_VALUE":
        v0, s0 = d["original_value"], text[inj["span"][0]:inj["span"][1]]
    elif t == "T5_COINCIDENT":
        v0, s0 = d["true_value"], text[inj["span"][0]:inj["span"][1]]
    else:
        v0, s0 = inj["new_value"], d["digits_unchanged"]
    cands = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL and c.get("span") and s0 in c["span"]]
    if len(cands) != 1:
        cands = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL]
    return cands[0] if len(cands) == 1 else None


def inject_doc(doc, zb, seed, work, cap=INJECT_CAP):
    u"""1 書類の注入。1 回に 1 件(``IJ.apply_edits(text, [inj])``)。round-trip を確かめる。"""
    old_tmp, A1.TMP = A1.TMP, work
    try:
        text, refs = A1.material(doc)
    finally:
        A1.TMP = old_tmp
    base = VD.verify_document(zb, "P22", None)["claims"]
    out, counts = [], {}
    for t in INJECT_TYPES:
        chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, doc, cap, types=[t])
        counts[t] = {u"作れる site": cat[t], u"採った": len(chosen), u"注入の行になった": 0, u"基準に対応が付かない": 0, u"基準が GROUNDED でない": 0}
        for inj in chosen:
            tampered, placements = IJ.apply_edits(text, [inj])
            if IJ.revert(tampered, [inj], placements, text) != text:
                raise SystemExit(u"**round-trip が合わない: %s %s。止める**" % (doc, inj["id"]))
            bc = _find_base_claim(base, inj, text)
            if t != "T3_ABSENT":
                if bc is None:
                    counts[t][u"基準に対応が付かない"] += 1
                    continue
                if bc["state"] != "GROUNDED":
                    counts[t][u"基準が GROUNDED でない"] += 1
                    continue
            counts[t][u"注入の行になった"] += 1       # T1・T2・T5 は基準が P22 の GROUNDED の数の claim。T3 は挿入文で基準なし
            res = {}
            for p in PROFILES:
                o = VD.verify_document(zb, p, tampered)
                c = A1.claim_for(o["claims"], inj)
                res[p] = None if c is None else [c["state"], c["reason"]]
            out.append({u"doc": doc, u"id": inj["id"], u"型": t, u"元の字": text[inj["span"][0]:inj["span"][1]], u"後の字": inj["replacement"],
                        u"基準の claim": None if bc is None else bc["id"], u"結果": res})
    return doc, out, counts


def _inject_worker(args):
    doc, zb, seed, work = args
    return inject_doc(doc, zb, seed, work)


def run_inject(docs, rows, procs, work_root):
    seed, meta = IJ.verify_seed_sealed(SEED_FILE)
    jobs = []
    for d in docs:
        w = os.path.join(work_root, d)
        os.makedirs(w, exist_ok=True)
        jobs.append((d, read_zip(d, rows), seed, w))
    # 重い書類から先に
    jobs.sort(key=lambda j: -len(j[1]))
    ctx = multiprocessing.get_context("fork")
    with concurrent.futures.ProcessPoolExecutor(max_workers=procs, mp_context=ctx) as ex:
        res = list(ex.map(_inject_worker, jobs))
    res.sort(key=lambda r: docs.index(r[0]))
    inj = [x for r in res for x in r[1]]
    counts = dict((r[0], r[2]) for r in res)
    return inj, counts, meta


def outcome_of(res):
    if res is None:
        return u"対応が付かない"
    s = res[0]
    return {"GROUNDED": u"通した", "VALUE_MISMATCH": u"違う", "POINTER_NOT_FOUND": u"要確認", "UNVERIFIABLE": u"要確認"}.get(s, s)


def summarize_D(inj):
    n = len(inj)
    out = {u"注入": n, u"型別の注入": dict(sorted(collections.Counter(x[u"型"] for x in inj).items()))}
    for p in PROFILES:
        c = collections.Counter(outcome_of(x[u"結果"][p]) for x in inj)
        by = {}
        for t in INJECT_TYPES:
            ct = collections.Counter(outcome_of(x[u"結果"][p]) for x in inj if x[u"型"] == t)
            by[t] = dict(sorted(ct.items()))
        out[p] = {u"通した": c.get(u"通した", 0), u"違う": c.get(u"違う", 0), u"要確認": c.get(u"要確認", 0), u"対応が付かない": c.get(u"対応が付かない", 0),
                  u"通した率": frac(c.get(u"通した", 0), n), u"型別": by,
                  u"通した(T3 を除く)": sum(1 for x in inj if x[u"型"] != "T3_ABSENT" and outcome_of(x[u"結果"][p]) == u"通した"),
                  u"止めのうち違う": frac(c.get(u"違う", 0), c.get(u"違う", 0) + c.get(u"要確認", 0)),
                  u"止めのうち要確認": frac(c.get(u"要確認", 0), c.get(u"違う", 0) + c.get(u"要確認", 0))}
    return out


# ====================================================================================================
# 読み・判定・予測
def attach_readings(rec, readings):
    u"""読みの file = {"B": {key: {読み, 根拠}}, "C": {key: {...}}}。**行と読みは 1 対 1**(足りない・余る・語が違うは止める)。"""
    for part, words, rows_of in ((u"B", WORDS_B, rec[u"B"]), (u"C", WORDS_C, rec[u"C"])):
        want = set(r[u"key"] for c in CANDIDATES for r in rows_of[c])
        got = set(readings.get(part, {}))
        if want != got:
            raise SystemExit(u"**読みと行が 1 対 1 でない(%s): 行の鍵 %d に読み %d(足りない %d・余り %d)。止める**" % (
                part, len(want), len(got), len(want - got), len(got - want)))
        for k, x in readings[part].items():
            if x[u"読み"] not in words or not x.get(u"根拠"):
                raise SystemExit(u"**読みの語か根拠が無い: %s**" % k)
        for c in CANDIDATES:
            for r in rows_of[c]:
                r[u"読み"], r[u"根拠"] = readings[part][r[u"key"]][u"読み"], readings[part][r[u"key"]][u"根拠"]


def reading_summary(rec):
    out = {}
    for c in CANDIDATES:
        B, C = rec[u"B"][c], rec[u"C"][c]
        out[c] = {u"B": {u"行": len(B), READ_TRUE: sum(1 for r in B if r[u"読み"] == READ_TRUE), READ_FALSE: sum(1 for r in B if r[u"読み"] == READ_FALSE),
                        READ_SEMI: sum(1 for r in B if r[u"読み"] == READ_SEMI)},
                  u"C": {u"行": len(C), READ_OK: sum(1 for r in C if r[u"読み"] == READ_OK), READ_WRONG: sum(1 for r in C if r[u"読み"] == READ_WRONG),
                        READ_UNSURE: sum(1 for r in C if r[u"読み"] == READ_UNSURE)}}
    return out


def judge_candidate(rec, cand):
    u"""封 §3 の K-1・K-2・K-3(**記録の数から**)。"""
    d = rec[u"D"]
    k1_c, k1_b = d[cand][u"通した"], d["P22"][u"通した"]
    B = rec[u"B"][cand]
    nB = len(B)
    fB = sum(1 for r in B if r[u"読み"] == READ_FALSE)
    semi = sum(1 for r in B if r[u"読み"] == READ_SEMI)
    C = rec[u"C"][cand]
    nC = len(C)
    wC = sum(1 for r in C if r[u"読み"] == READ_WRONG)
    uC = sum(1 for r in C if r[u"読み"] == READ_UNSURE)
    eff = wC + 0.5 * uC
    k2 = (nB == 0) or (100.0 * fB / nB <= 3.0)
    k3 = (nC == 0) or (100.0 * eff / nC <= 2.0)
    k1 = k1_c <= k1_b
    return {u"K-1": {u"満たす": k1, u"候補が通した": k1_c, u"P22 が通した": k1_b},
            u"K-2": {u"満たす": k2, u"新 GROUNDED": nB, u"偽": fB, u"準偽": semi, u"偽の率": pct(fB, nB)},
            u"K-3": {u"満たす": k3, u"弱まった行": nC, u"文が本当に違う": wC, u"分からない": uC, u"違うに数える": eff, u"率": pct(eff, nC)},
            u"全部満たす": k1 and k2 and k3,
            u"満たさなかった基準": [k for k, ok in ((u"K-1", k1), (u"K-2", k2), (u"K-3", k3)) if not ok]}


def decide(rec):
    order = list(CANDIDATES) if rec[u"順序"][u"P26 は候補"] else ["P25", "P24"]
    j = dict((c, judge_candidate(rec, c)) for c in CANDIDATES)
    chosen = "P22"
    for c in order:
        if j[c][u"全部満たす"]:
            chosen = c
            break
    return {u"候補の順": order, u"候補ごと": j, u"既定": chosen}


def predictions(rec):
    A, D = rec[u"A"], rec[u"D"]
    n = A[u"claim"]
    f1_22 = A["P22"]["VALUE_MISMATCH"][u"率"]
    f1_25 = A["P25"]["VALUE_MISMATCH"][u"率"]
    f2 = A["P25"]["POINTER_NOT_FOUND"][u"率"]
    ng = rec[u"F-4"]
    f5 = D["P25"][u"通した率"][u"率"]
    pre = []
    pre.append({u"#": u"F-1", u"予測": u"P22 の違う率 12〜25%、P25 の違う率 5〜13%", u"実測": u"P22 %.1f%%・P25 %.1f%%" % (f1_22, f1_25),
                u"当たり": 12 <= f1_22 <= 25 and 5 <= f1_25 <= 13, u"参考(P26)": A["P26"]["VALUE_MISMATCH"][u"率"]})
    pre.append({u"#": u"F-2", u"予測": u"P25 の結べない(PNF)率 13〜24%", u"実測": u"%.1f%%" % f2, u"当たり": 13 <= f2 <= 24, u"参考(P26)": A["P26"]["POINTER_NOT_FOUND"][u"率"]})
    d = rec[u"判定"]
    pre.append({u"#": u"F-3", u"予測": u"K-1・K-2・K-3 を全部満たす(= P25 になる)", u"実測": u"既定 %s。P25 の満たさなかった基準 %s" % (d[u"既定"], d[u"候補ごと"]["P25"][u"満たさなかった基準"]),
                u"当たり": d[u"候補ごと"]["P25"][u"全部満たす"]})
    ratio = ng[u"倍率"]
    pre.append({u"#": u"F-4", u"予測": u"P23 → P25 の新 GROUNDED は claim あたり 67 書類の 0.3〜1.5 倍", u"実測": u"倍率 %.2f" % ratio, u"当たり": 0.3 <= ratio <= 1.5})
    pre.append({u"#": u"F-5", u"予測": u"(D) の注入で P25 が誤りを通す率 0〜4%", u"実測": u"%.1f%%" % f5, u"当たり": f5 <= 4.0, u"参考(P26)": D["P26"][u"通した率"][u"率"]})
    return pre


def order_facts(fetched):
    u"""封 §3: P26 の段 1 の commit が取得より前か。commit の時刻と取得の時刻(記録・ZIP の mtime)を機械で比べる。"""
    r = git("log", "-1", "--format=%cI|%H", P26_COMMIT)
    when, full = r.stdout.strip().split("|")
    anc = git("merge-base", "--is-ancestor", P26_COMMIT, "HEAD").returncode == 0
    import datetime
    t_commit = datetime.datetime.fromisoformat(when)
    t_rec = datetime.datetime.strptime(fetched[u"取得した時刻(UTC)"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    mt = [os.path.getmtime(os.path.join(FRESH_DIR, f)) for f in os.listdir(FRESH_DIR) if f.endswith(".zip")]
    t_first = datetime.datetime.fromtimestamp(min(mt), tz=datetime.timezone.utc)
    f = git("log", "-1", "--format=%cI", FETCH_SCRIPT_COMMIT).stdout.strip()
    return {u"P26 の commit": full, u"P26 の commit の時刻": when, u"取得の script の commit": FETCH_SCRIPT_COMMIT, u"取得の script の commit の時刻": f,
            u"取得した時刻(記録・UTC)": fetched[u"取得した時刻(UTC)"], u"最初に置いた ZIP の mtime(UTC)": t_first.strftime("%Y-%m-%dT%H:%M:%SZ"),
            u"P26 の commit は HEAD の祖先": anc,
            u"P26 は候補": bool(anc and t_commit < t_first and t_commit < t_rec)}


def key_leaks(text):
    u"""記録に鍵らしい字が在れば、その種類の一覧(値は返さない)。EDINET の鍵は 32 桁の 16 進。要素の名前は長い英字なので『32 字以上の英数字』では見ない。
    64 桁の 16 進(sha256)の中の 32 桁は数えない(前後が 16 進の字でない 32 桁だけ)。"""
    leaks = []
    if re.search(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{32}(?![0-9A-Fa-f])", text):
        leaks.append(u"32 桁の 16 進")
    if re.search(r"(?i)subscription-key", text):
        leaks.append(u"Subscription-Key")
    if re.search(r"EDINET_API_KEY\s*=\s*['\"]?\w{8,}", text):
        leaks.append(u"EDINET_API_KEY=値")
    return leaks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", choices=("plain", "inject", "all"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--readings", default=None)
    ap.add_argument("--docs", default=None, help="軽い走らせ直し用(コンマ区切り。--stage plain / inject のときだけ)")
    ap.add_argument("--procs", type=int, default=6)
    ap.add_argument("--work", default=None, help="注入の作業 folder(既定: TMPDIR の下)")
    a = ap.parse_args(argv)
    docs, rows, fetched = used_docs()
    if a.docs:
        if a.stage == "all":
            raise SystemExit(u"**--docs は --stage all では使えない(30 書類が正本)**")
        docs = a.docs.split(",")
    elif len(docs) != fetched[u"使う件数"]:
        raise SystemExit(u"**使う書類の数が記録と違う**")
    outp = os.path.abspath(a.out)
    if a.stage == "all" and (os.path.exists(outp) or not a.readings):
        raise SystemExit(u"**出力が既に在るか --readings が無い。止める**")
    # 既存の cache の 1 件にも触らない(読まない)ことの印: 開始時の件数
    n_existing0 = len([f for f in os.listdir(EXISTING_CACHE) if f.endswith(".zip")]) if os.path.isdir(EXISTING_CACHE) else None
    saved = ED.CACHE_DIR
    ED.CACHE_DIR = FRESH_DIR         # この process の中だけ
    t0 = time.time()
    rec = {u"seal": SEAL, u"docs": docs}
    try:
        if a.stage in ("plain", "all"):
            per_doc, claims, moved = run_plain(docs, rows, a.procs)
            rec[u"書類別"] = per_doc
            rec[u"claims"] = claims
            rec[u"動いた行"] = moved
        if a.stage in ("inject", "all"):
            work = a.work or tempfile.mkdtemp(prefix="fresh_inject_", dir=os.environ.get("TMPDIR"))
            inj, counts, meta = run_inject(docs, rows, a.procs, work)
            rec[u"注入の行"] = inj
            rec[u"注入の件数(書類別)"] = counts
            rec[u"注入の種"] = {u"file": "measure/SEED.json", u"sealed_in_commit": meta.get("sealed_in_commit"), u"seed_file_sha256": meta.get("seed_file_sha256")}
    finally:
        ED.CACHE_DIR = saved
    if a.stage != "all":
        with io.open(outp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
        print("-> %s  (%.0f 秒)" % (outp, time.time() - t0))
        return rec

    # ---- all: 集計・読み・判定・予測
    B, C = build_bc(rec[u"動いた行"])
    rec[u"A"] = summarize_A(rec[u"書類別"], rec[u"claims"])
    rec[u"B"], rec[u"C"] = B, C
    rec[u"D"] = summarize_D(rec[u"注入の行"])
    k = new_g_p23_p25(rec[u"claims"])
    n = rec[u"A"][u"claim"]
    rate67 = BASE_67_NEW_G[0] / float(BASE_67_NEW_G[1])
    rec[u"F-4"] = {u"P23 → P25 の新 GROUNDED": k, u"claim": n, u"率": pct(k, n), u"67 書類の件": BASE_67_NEW_G[0], u"67 書類の claim": BASE_67_NEW_G[1],
                  u"67 書類の率": round(100.0 * rate67, 2), u"倍率": round((k / float(n)) / rate67, 3)}
    rec[u"順序"] = order_facts(fetched)
    with io.open(a.readings, encoding="utf-8") as fh:
        readings = json.load(fh)
    attach_readings(rec, readings)
    rec[u"読みの断り"] = u"**読みは実装席のエージェントの読みで、人間の読みではない。** K-2・K-3 の判定はその読みに依る。"
    rec[u"読みの内訳"] = reading_summary(rec)
    rec[u"判定"] = decide(rec)
    rec[u"予測"] = predictions(rec)
    rec[u"入力"] = {u"取得の記録": FETCHED_REL, u"取得の記録の sha256": sha_bytes(io.open(os.path.join(ROOT, FETCHED_REL), "rb").read()),
                  u"draw の sha256": sha_bytes(io.open(os.path.join(ROOT, DRAW_REL), "rb").read()),
                  u"書類の sha256": dict((d, rows[d]["sha256"]) for d in docs),
                  u"既存の cache の件数(開始時)": n_existing0,
                  u"既存の cache の件数(終了時)": len([f for f in os.listdir(EXISTING_CACHE) if f.endswith(".zip")]) if os.path.isdir(EXISTING_CACHE) else None,
                  u"新しい folder": "~/.cache/audit-core/edinet-fresh-2026-10-21/"}
    rec[u"環境"] = {u"python": platform.python_version(), u"所要秒": round(time.time() - t0), u"注入の cap(型ごと・書類ごと)": INJECT_CAP,
                  u"engine の sha256(先頭 16 桁)": dict((rel, sha_bytes(io.open(os.path.join(ROOT, rel), "rb").read())[:16]) for rel in (
                      "adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py", "adapters/xbrl/registry_setup.py",
                      "adapters/xbrl/report_customer.py", "adapters/xbrl/comparators.py")),
                  u"DEFAULT_PROFILE": V.DEFAULT_PROFILE}
    rec[u"limits"] = [u"30 書類は 1 つの母集団(封 431f436 の 256 件)からの引きで、母集団の偏り(提出時期・業種)を引き継ぐ",
                     u"読みは実装席のエージェントで人間ではない。K-2・K-3 の判定はその読みに依る",
                     u"注入は inject.py の 4 型だけで、実際の LLM の誤りの分布ではない。型ごと 1 書類あたり %d 件までで、全部の site ではない" % INJECT_CAP,
                     u"席は 1 回も呼んでいない。通信していない"]
    blob = json.dumps(rec, ensure_ascii=False, indent=1)
    if key_leaks(blob):
        raise SystemExit(u"**鍵らしい字が記録に在る。書かずに止める**")
    with io.open(outp, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"=== 既定 %s ===" % rec[u"判定"][u"既定"])
    print("-> %s" % outp)
    return rec


if __name__ == "__main__":
    main()
