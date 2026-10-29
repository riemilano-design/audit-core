# -*- coding: utf-8 -*-
u"""診断: P27 が「証拠が無く名指さない」で止めた行で、engine が内側に持つ「名指さなかった fact」は原本の fact か ― 2026-10-29。

封 ``docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md``(commit ``d31371e``)§2 と、その §6-4 の追記(W-3 (ii) の字の補い)の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。出力の形(``verify_document.py`` の ``CLAIM_FIELDS``・``report_customer.py``)も 0 行。
既存の記録(``stop_reason_2026-10-29.json``・``inject_reach_2026-10-28.json``・``fresh/fresh_2026-10-21.json``・``p27/regress97_2026-10-27.json``・``default_p27_2026-10-28.json``)は書き換えない(別の記録を足す)。**
0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。評価用・調整用(``~/.cache/audit-core/edinetdb-p27/``)は開かない。

    cd audit-core
    python3 measure/xbrl_unnamed_fact_2026-10-29.py --procs 6                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_unnamed_fact_2026-10-29.py --docs 2 --out <scratch の file>   # 試走(先頭 n 書類。配線の門はその n 書類の分)

配線(封 §2-1): 止めた理由の script ``measure/xbrl_stop_reason_2026-10-29.py``(以下 SR)を読み込み、SR が読み込んだ前の便の module ``SR.RE``(= ``measure/xbrl_inject_reach_2026-10-28.py``。以下 RE)を使う。
  ``RE.OBS = ("P27",)`` だけを替える(観測するのは P27 だけ。``RE.ALLP`` は P22〜P27 の 6 つ = 前の便の 2026-10-28 の走らせ方と同じ。P22〜P26 は ``RE.work_doc`` の配線の門のために走り、観測しない)。
  書類ごとに ``RE.work_doc(a)`` を呼ぶ(``run_doc`` の中)。**自分で注入の規則・対応付けを書かない**(材料・注入・対応付けは RE の中で ``xbrl_fresh_2026-10-21.py`` の関数が使われる)。
  raw の拾い方: ``RE.LB.verify_raw`` を、返り値を変えない包みに ``RE.work_doc`` の間だけ替える。包みは P27 の呼び出しごとに ``{id: raw の claim の no_same_value と reason}`` を積み、
  無改変の P27 と P22 のときは出力の claims も積む。積んだ順 = 行の順(``RE.work_doc`` は注入の行 1 件につき P27 の ``verify_raw`` を 1 回だけ呼び、行を同じ順で積む)。戻せていなければ止める。
  前の便の script・止めた理由の script の file は触らない。

配線の門(1 つでも違えば記録を書かずに止める):
  W-1 (i) 前の便の門(741 / 741 の 4 欄・id の集合・注入の件数 120 組)、(ii) P27 の注入後の claim(10 欄 + recomputed)が記録 ``stop_reason_2026-10-29.json`` と行ごとに一致(state・reason・pointers は欄ごとにも)。
  W-2 無改変の 30 書類の P27 と P22 の 4 state が ``regress97`` と書類ごとに一致、P27 の和が ``default_p27_2026-10-28.json`` の S3 の 4 state と一致。
  W-3 (i) 捕捉の回数(注入後 = 行数、無改変 = 書類数)、(ii) 行の claim の id が raw に在り、(出力の reason が no_same_value)と(raw の reason が no_same_value)が同じ真偽(封 §6-4)、
      (iii) raw に no_same_value の鍵が None でない値で在る行の数 = 出力の reason が no_same_value の行の数(食い違い 0)。
一致の語(6 語)は ``agree_word`` の 1 か所、比・帯・10 の冪は ``ratio_of`` の 1 か所。要素と context の切り方は ``SR.split_pointer``(自分で書かない)。
"""
from __future__ import print_function

import argparse
import collections
import concurrent.futures
import importlib.util
import io
import json
import math
import multiprocessing
import os
import shutil
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


SR = _mod("measure/xbrl_stop_reason_2026-10-29.py", "stop_reason_for_unnamed")
RE = SR.RE
RE.OBS = ("P27",)                                                 # 封 §2-1: 観測するのは P27 だけ
RE.ALLP = tuple(sorted(set(RE.PROFILES5) | set(RE.OBS)))         # P22〜P27 の 6 つ(前の便の 2026-10-28 と同じ)
FR, VD, ED, IJ, V, LB = RE.FR, RE.VD, RE.ED, RE.IJ, RE.V, RE.LB

SEAL_REL = "docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md"
SEAL_COMMIT = "d31371e"
OUT_REL = "fixtures/xbrl/unnamed_fact_2026-10-29.json"
STOP_REL = SR.OUT_REL
REGRESS_REL = SR.REGRESS_REL
DEFAULT27_REL = "fixtures/xbrl/default_p27_2026-10-28.json"
FRESH_REC_REL = RE.FRESH_REC_REL
FETCHED_REL = RE.FETCHED_REL
INJECT_TYPES = RE.INJECT_TYPES
NSV = "no_same_value"
STATES4 = ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND")
INPUT_RELS = (STOP_REL, FRESH_REC_REL, FETCHED_REL, REGRESS_REL, DEFAULT27_REL)
#: 記録の行に写す claim の欄(span は書かない = 封 §2-2)
ROW_CLAIM_KEYS = ("id", "kind", "form", "value", "unit", "state", "reason", "pointers", "recomputed")

# 一致の語 6 語(封 §2-3)
A_NONAMED, A_NOHEAD, A_SAME = u"(named なし)", u"(照らす先なし)", u"(同じ)"
A_CTX, A_ELEM, A_BOTH = u"(context だけ違う)", u"(要素だけ違う)", u"(両方違う)"
AGREE_WORDS = (A_NONAMED, A_NOHEAD, A_SAME, A_CTX, A_ELEM, A_BOTH)
# 比の帯(封 §2-4)
B_15, B_2, B_10, B_10K, B_OVER, B_NONE = u"(15% 以内)", u"(2 倍以内)", u"(10 倍以内)", u"(10,000 倍以内)", u"(10,000 倍超)", u"(比なし)"
BANDS = (B_15, B_2, B_10, B_10K, B_OVER, B_NONE)


def agree_word(named, h):
    u"""封 §2-3: ``named``(字)と照らす先頭の pointer ``h`` から一致の語を 1 つ(一致の語を決める 1 か所)。"""
    if named is None:
        return A_NONAMED
    if h is None:
        return A_NOHEAD
    if named == h:
        return A_SAME
    a, b = SR.split_pointer(named), SR.split_pointer(h)
    if a[u"scheme"] == u"xbrl" and b[u"scheme"] == u"xbrl":
        if a[u"要素名"] == b[u"要素名"] and a[u"context"] != b[u"context"]:
            return A_CTX
        if a[u"context"] == b[u"context"] and a[u"要素名"] != b[u"要素名"]:
            return A_ELEM
    return A_BOTH


def ratio_of(claim_value, unit, named_value):
    u"""封 §2-4: 文の値(円)・比・帯・10 の冪に近いか(比と帯を決める 1 か所)。比は判定に使わない。"""
    scale = V.UNIT_SCALE.get(unit) if unit is not None else None
    sent = None if (claim_value is None or scale is None) else claim_value * scale
    if sent is None or named_value is None or named_value == 0:
        return {u"文の値": sent, u"比": None, u"帯": B_NONE, u"10 の冪に近い": None, u"k": None}
    r = abs(sent) / abs(named_value)
    if r == 0:
        return {u"文の値": sent, u"比": 0.0, u"帯": B_OVER, u"10 の冪に近い": False, u"k": None}
    if 0.85 <= r <= 1.15:
        band = B_15
    elif 0.5 <= r <= 2:
        band = B_2
    elif 0.1 <= r <= 10:
        band = B_10
    elif 0.0001 <= r <= 10000:
        band = B_10K
    else:
        band = B_OVER
    lg = math.log10(r)
    k = int(round(lg))
    return {u"文の値": sent, u"比": r, u"帯": band, u"10 の冪に近い": abs(lg - k) <= 0.01, u"k": k}


def dumps(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False)


def after_of(r):
    x = r[u"profile"]["P27"]
    return x["claim"] if r[u"型"] == "T3_ABSENT" else x[u"注入後"]["claim"]


def run_doc(a):
    u"""書類 1 本(別の process)。``RE.work_doc`` を包みの中で呼び、P27 の raw の no_same_value と P22・P27 の無改変の出力の claims を拾う。"""
    cap = {u"P27 注入後": [], u"P27 無改変": [], u"P22 無改変": []}
    orig = LB.verify_raw

    def tapped(tap, zb, prof, text=None):
        out, raw, sents = orig(tap, zb, prof, text)                  # 返り値は変えない
        if prof == "P27":
            item = {u"nsv": dict((cid, c.get(NSV)) for cid, c in raw.items()),
                    u"raw reason": dict((cid, c.get("reason")) for cid, c in raw.items())}
            if text is None:
                item[u"claims"] = out["claims"]
                cap[u"P27 無改変"].append(item)
            else:
                cap[u"P27 注入後"].append(item)
        elif prof == "P22" and text is None:
            cap[u"P22 無改変"].append({u"claims": out["claims"]})
        return out, raw, sents

    LB.verify_raw = tapped
    try:
        r = RE.work_doc(a)
    finally:
        LB.verify_raw = orig
    if LB.verify_raw is not orig:
        raise SystemExit(u"**verify_raw を戻せていない。止める**")
    r[u"cap"] = cap
    return r


def head_of(c):
    return ((c or {}).get("pointers") or [None])[0]


def g(c, k):
    return None if c is None else c.get(k)


def row_claim(c):
    return None if c is None else dict((k, c.get(k)) for k in ROW_CLAIM_KEYS)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    ap.add_argument("--docs", type=int, default=None, help="先頭 n 書類だけ(試走。正本の記録は 30 書類全部)")
    ap.add_argument("--procs", type=int, default=6)
    args = ap.parse_args()
    if os.path.exists(args.out):
        print(u"既に在る(測り直さない): %s" % args.out)
        return
    t_start = time.time()
    # engine の sha16 が止めた理由の記録と違えば、走らせる前に止める
    stop = RE.jload(STOP_REL)
    engine_now = dict((rel, RE.sha16(rel)) for rel in RE.ENGINE_FILES)
    if stop[u"engine sha16"] != engine_now:
        raise SystemExit(u"**engine の sha16 が記録 stop_reason と違う: %s。走らせずに止める**" % dumps(engine_now))
    rec_fresh = RE.jload(FRESH_REC_REL)
    reg = RE.jload(REGRESS_REL)
    d27 = RE.jload(DEFAULT27_REL)
    rows_rec = rec_fresh[u"注入の行"]
    by_id = dict((r["id"], r) for r in rows_rec)
    srow = dict((r["id"], r) for r in stop[u"rows"])
    docs_all, rows_fetched, fetched = FR.used_docs()
    docs = docs_all if args.docs is None else docs_all[:args.docs]
    cache0 = {u"edinet": RE.count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": RE.count_zip(FR.FRESH_DIR)}
    seed, meta = IJ.verify_seed_sealed(FR.SEED_FILE)
    work_root = tempfile.mkdtemp(prefix="unnamed_fact_")
    jobs = []
    for d in docs:
        w = os.path.join(work_root, d)
        os.makedirs(w)
        jobs.append((d, rows_fetched, seed, w, by_id, rec_fresh[u"注入の件数(書類別)"][d]))
    ED.CACHE_DIR = FR.FRESH_DIR
    ctx = multiprocessing.get_context("fork")
    res = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.procs, mp_context=ctx) as ex:
        futs = dict((ex.submit(run_doc, j), j[0]) for j in sorted(jobs, key=lambda j: -rows_fetched[j[0]]["bytes"]))
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            res[r["doc"]] = r
            print(u"完了 %d / %d 書類 (%d 行, %d 秒)" % (len(res), len(docs), len(r[u"rows"]), r[u"秒"]), file=sys.stderr)
            sys.stderr.flush()
    shutil.rmtree(work_root, ignore_errors=True)
    wiring = [x for d in docs for x in res[d][u"wiring"]]

    # ---- fresh の P26(無改変の照らす相手)
    fresh_nsv26 = set()
    for d in docs:
        for x in rec_fresh[u"claims"][d]:
            if x["reasons"][4] == NSV:
                fresh_nsv26.add((d, x["id"]))
    fresh_named26 = {}
    for x in rec_fresh[u"動いた行"]:
        dp = (x.get("dossier") or {}).get("P26")
        if isinstance(dp, dict):
            fresh_named26[(x["doc"], x["id"])] = dp.get(u"名指した fact")

    out_rows, plain_rows = [], []
    w1_f = collections.Counter()
    w3 = collections.Counter()
    per_doc = {}
    regd = dict((x["docID"], x) for x in reg[u"書類"])
    w2_p27 = w2_p22 = 0
    tot27 = collections.Counter()
    for d in docs:
        r = res[d]
        rows, cap = r[u"rows"], r[u"cap"]
        w3[u"行"] += len(rows)
        w3[u"捕捉 注入後"] += len(cap[u"P27 注入後"])
        w3[u"捕捉 無改変"] += len(cap[u"P27 無改変"])
        if len(cap[u"P27 注入後"]) != len(rows):
            raise SystemExit(u"**捕捉の回数が行数と違う: %s %d != %d。記録を書かずに止める**" % (d, len(cap[u"P27 注入後"]), len(rows)))
        if len(cap[u"P27 無改変"]) != 1 or len(cap[u"P22 無改変"]) != 1:
            raise SystemExit(u"**無改変の捕捉が 1 回でない: %s。記録を書かずに止める**" % d)
        for i, row in enumerate(rows):
            c = after_of(row)
            item = cap[u"P27 注入後"][i]
            o = srow[row["id"]]
            if row[u"型"] == "T3_ABSENT":
                oc = o[u"profile"]["P27"]["claim"]
                base_head, p22c = None, o[u"profile"]["P22"]["claim"]
                base_form = None
            else:
                oc = o[u"profile"]["P27"][u"注入後"]["claim"]
                bc = o[u"profile"]["P27"][u"無改変"]["claim"]
                base_head, base_form = head_of(bc), (bc or {}).get("form")
                p22c = o[u"profile"]["P22"][u"注入後"]["claim"]
            # W-1 (ii)
            w1_f[u"全欄"] += int(dumps(c) == dumps(oc))
            w1_f["state"] += int(g(c, "state") == g(oc, "state"))
            w1_f["reason"] += int(g(c, "reason") == g(oc, "reason"))
            w1_f["pointers"] += int(g(c, "pointers") == g(oc, "pointers"))
            # W-3
            if c is None:
                named, nv = None, None
                w3[u"claim なし"] += 1
            else:
                cid = c["id"]
                in_raw = cid in item[u"nsv"]
                raw_nsv = item[u"raw reason"].get(cid) == NSV
                w3[u"id と reason の照合の分母"] += 1
                w3[u"id が raw に在る"] += int(in_raw)
                w3[u"id と reason の照合"] += int(in_raw and ((c["reason"] == NSV) == raw_nsv))
                key = item[u"nsv"].get(cid)
                w3[u"鍵が在る行"] += int(key is not None)
                w3[u"reason が no_same_value の行"] += int(c["reason"] == NSV)
                w3[u"鍵と reason が食い違う行"] += int((key is not None) != (c["reason"] == NSV))
                named = None if key is None else key.get("named")
                nv = None if key is None else key.get("value")
            p22_head = head_of(p22c)
            p22_rec = g(p22c, "recomputed")
            rr = ratio_of(g(c, "value"), g(c, "unit"), nv)
            out_rows.append({
                u"doc": d, u"id": row["id"], u"型": row[u"型"], u"state": g(c, "state"), u"reason": g(c, "reason"), u"claim": row_claim(c),
                u"named": named, u"named の value": nv, u"基準の先頭": base_head, u"基準の form": base_form,
                u"P22 の注入後の先頭": p22_head, u"P22 の recomputed": p22_rec,
                u"一致(基準)": agree_word(named, base_head), u"一致(P22)": agree_word(named, p22_head),
                u"value = P22 の recomputed": None if (nv is None or p22_rec is None) else (nv == p22_rec),
                u"文の値": rr[u"文の値"], u"比": rr[u"比"], u"帯": rr[u"帯"], u"10 の冪に近い": rr[u"10 の冪に近い"], u"k": rr[u"k"]})
        # 無改変
        p27 = cap[u"P27 無改変"][0]
        p22 = dict((c["id"], c) for c in cap[u"P22 無改変"][0][u"claims"])
        st = {}
        for p, cl in (("P27", p27[u"claims"]), ("P22", list(p22.values()))):
            c_ = collections.Counter(c["state"] for c in cl)
            st[p] = dict((k, c_.get(k, 0)) for k in STATES4)
        good27 = all(st["P27"][k] == regd[d][u"4 state"]["P27"].get(k, 0) for k in STATES4)
        good22 = all(st["P22"][k] == regd[d][u"4 state"]["P22"].get(k, 0) for k in STATES4)
        w2_p27 += int(good27)
        w2_p22 += int(good22)
        tot27.update(st["P27"])
        n_keys = sum(1 for cid, v in p27[u"nsv"].items() if v is not None)
        n_reason = sum(1 for c in p27[u"claims"] if c["reason"] == NSV)
        n_mis = sum(1 for c in p27[u"claims"] if (p27[u"nsv"].get(c["id"]) is not None) != (c["reason"] == NSV))
        w3[u"無改変 鍵"] += n_keys
        w3[u"無改変 reason"] += n_reason
        w3[u"無改変 食い違い"] += n_mis
        w3[u"無改変 id が raw に在る"] += sum(1 for c in p27[u"claims"] if c["id"] in p27[u"nsv"])
        w3[u"無改変 claim"] += len(p27[u"claims"])
        for c in p27[u"claims"]:
            if c["reason"] != NSV:
                continue
            key = p27[u"nsv"].get(c["id"])
            named = None if key is None else key.get("named")
            nv = None if key is None else key.get("value")
            q = p22.get(c["id"])
            q_head = head_of(q)
            f26 = fresh_named26.get((d, c["id"]))
            rr = ratio_of(c["value"], c["unit"], nv)
            plain_rows.append({
                u"doc": d, u"id": c["id"], u"state": c["state"], u"reason": c["reason"], u"named": named, u"named の value": nv,
                u"P22 の state": g(q, "state"), u"P22 の reason": g(q, "reason"), u"P22 の先頭": q_head, u"P22 の recomputed": g(q, "recomputed"),
                u"一致(P22)": agree_word(named, q_head), u"fresh P26 の 名指した fact": f26,
                u"一致(fresh P26)": None if f26 is None else (named == f26), u"fresh P26 の no_same_value に在る": (d, c["id"]) in fresh_nsv26,
                u"unit": c["unit"], u"claim の value": c["value"], u"文の値": rr[u"文の値"], u"比": rr[u"比"], u"帯": rr[u"帯"],
                u"10 の冪に近い": rr[u"10 の冪に近い"], u"k": rr[u"k"]})
        per_doc[d] = {u"材料の sha256": rows_fetched[d]["sha256"], u"材料の sha256 が取得の記録と一致": True, u"注入の件数": r[u"counts"],
                      u"claims": r[u"claims"], u"無改変の 4 state": st, u"P27 の no_same_value の行数(無改変)": n_reason,
                      u"捕捉": {u"注入後": len(cap[u"P27 注入後"]), u"無改変": len(cap[u"P27 無改変"])},
                      u"文の数": r[u"文の数"], u"秒": r[u"秒"]}

    # ---- W-1 (i)
    rec_ids = sorted(r["id"] for r in rows_rec if r["doc"] in docs)
    mine_ids = sorted(w["id"] for w in wiring)
    n_match = sum(1 for w in wiring if w[u"一致"][u"4 欄とも一致"])
    n_pairs = len(docs) * len(INJECT_TYPES)
    n_pairs_ok = sum(1 for d in docs for t in INJECT_TYPES if res[d][u"counts"][t][u"3 つの数が記録と一致"])
    n_rows = len(out_rows)
    missing = sum(1 for r in out_rows if r["id"] not in srow)
    w1 = {u"前の便の門(4 欄とも一致)": [n_match, len(wiring)], u"記録の注入の行(対象の書類)": len(rec_ids), u"id の集合が記録と同じ": rec_ids == mine_ids,
          u"注入の件数の組": [n_pairs_ok, n_pairs], u"stop_reason に無い行": missing, u"行": n_rows,
          u"P27 の state": w1_f["state"], u"P27 の reason": w1_f["reason"], u"P27 の pointers": w1_f["pointers"], u"P27 の全欄(10 欄 + recomputed)": w1_f[u"全欄"]}
    w1[u"通った"] = bool(w1[u"id の集合が記録と同じ"] and n_match == len(wiring) == len(rec_ids) and n_pairs_ok == n_pairs and missing == 0
                      and all(w1_f[k] == n_rows for k in ("state", "reason", "pointers", u"全欄")))
    # ---- W-2
    sums_ok = True if args.docs is not None else dict((k, tot27.get(k, 0)) for k in STATES4) == d27["S3"][u"既定の 4 state"]
    w2 = {u"P27 の 4 state が regress97 と一致": [w2_p27, len(docs)], u"P22 の 4 state が regress97 と一致": [w2_p22, len(docs)],
          u"P27 の和": dict((k, tot27.get(k, 0)) for k in STATES4), u"default_p27 S3 の既定の 4 state": d27["S3"][u"既定の 4 state"],
          u"和が default_p27 と一致(全書類のときだけ照らす)": sums_ok}
    w2[u"通った"] = bool(w2_p27 == w2_p22 == len(docs) and sums_ok)
    # ---- W-3
    by_t = collections.Counter(r[u"型"] for r in out_rows if r["reason"] == NSV)
    w3d = {u"捕捉 注入後 / 行": [w3[u"捕捉 注入後"], w3[u"行"]], u"捕捉 無改変 / 書類": [w3[u"捕捉 無改変"], len(docs)],
           u"id と reason の照合": [w3[u"id と reason の照合"], w3[u"id と reason の照合の分母"]], u"claim が None の行(raw を見ない)": w3[u"claim なし"],
           u"鍵が在る行(注入後)": w3[u"鍵が在る行"], u"reason が no_same_value の行(注入後)": w3[u"reason が no_same_value の行"],
           u"reason が no_same_value の行の型別": dict(by_t), u"鍵と reason が食い違う行(注入後)": w3[u"鍵と reason が食い違う行"],
           u"無改変 鍵が在る行": w3[u"無改変 鍵"], u"無改変 reason が no_same_value の行": w3[u"無改変 reason"], u"無改変 鍵と reason が食い違う行": w3[u"無改変 食い違い"],
           u"無改変 claim の id が raw に在る": [w3[u"無改変 id が raw に在る"], w3[u"無改変 claim"]]}
    w3d[u"通った"] = bool(w3[u"捕捉 注入後"] == w3[u"行"] == n_rows and w3[u"捕捉 無改変"] == len(docs)
                       and w3[u"id と reason の照合"] == w3[u"id と reason の照合の分母"] == n_rows - w3[u"claim なし"]
                       and w3[u"鍵が在る行"] == w3[u"reason が no_same_value の行"] and w3[u"鍵と reason が食い違う行"] == 0
                       and w3[u"無改変 鍵"] == w3[u"無改変 reason"] and w3[u"無改変 食い違い"] == 0
                       and w3[u"無改変 id が raw に在る"] == w3[u"無改変 claim"] and len(plain_rows) == w3[u"無改変 reason"])
    gate = {u"W-1": w1, u"W-2": w2, u"W-3": w3d}
    gate[u"通った"] = bool(w1[u"通った"] and w2[u"通った"] and w3d[u"通った"])
    if not gate[u"通った"]:
        raise SystemExit(u"**配線の門が通らない: %s。記録を書かずに止める**" % dumps(gate))

    cache1 = {u"edinet": RE.count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": RE.count_zip(FR.FRESH_DIR)}
    rec = collections.OrderedDict()
    rec[u"注意"] = u"診断の記録(封 docs/XBRL_UNNAMED_FACT_DIAG_SEAL_2026-10-29.md §5)。engine は 0 行。stop_reason_2026-10-29.json・inject_reach_2026-10-28.json・fresh_2026-10-21.json・regress97_2026-10-27.json・default_p27_2026-10-28.json は書き換えない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": RE.git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT}
    rec[u"全書類"] = args.docs is None
    rec[u"HEAD"] = RE.git("rev-parse", "HEAD")
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"engine sha16"] = engine_now
    rec[u"種"] = meta
    rec[u"読んだ入力の sha256"] = dict((rel, RE.sha64(rel)) for rel in INPUT_RELS)
    rec[u"観測する profile"] = list(RE.OBS)
    rec[u"書類(出てくる順)"] = docs
    rec[u"書類ごと"] = per_doc
    rec[u"配線の門"] = gate
    rec[u"cache"] = {u"開始": cache0, u"終了": cache1}
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"『同じ』は字の一致であり、人の目は入らない。named が基準の先頭と同じでも、その fact が文の言う数の出所として正しいかは測っていない。基準の結び付きが正しいかも測っていない。",
        u"出力に named を出す変更の是非は、この便で決めない(adapters/ の変更 = 人間の承認)。この便は判断の材料(同じ行の数と無改変で候補が付く行の数)を数えるだけ。",
        u"無改変の候補の正しさは測れない。無改変の no_same_value の行は正解が無い。",
        u"P27E は測らない。無改変の 24 行は regress97 の記録で足りる。",
        u"比は『文の値 / |named の value|』で、engine の target(claim_scale・丸め・符号の扱い)と同じ数とは限らない。判定に使わない。",
        u"30 書類・741 行・1 書類あたり型ごとに 40 件までの IJ.select の順の観測。他の書類・他の site で同じ分布になるとは言えない。Core 全体の振る舞いを断定しない。",
        u"cur[0] が P22 と P27 で同じかを engine の中の変数で直接は見ない。named と P22 の先頭の字の一致から間接に読む。",
        u"仮説は測るまで断定しない。読みは無い(機械の値)。",
    ]
    rec[u"rows"] = out_rows
    rec[u"plain_rows"] = plain_rows
    rec[u"配線の行ごと"] = wiring
    rowkeys = (u"rows", u"plain_rows", u"配線の行ごと")
    blob = RE.dump_record(rec, rowkeys)
    leaks = FR.key_leaks(blob)
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    rec[u"key_leaks"] = []
    blob = RE.dump_record(rec, rowkeys)
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"配線の門 W-1 %s W-2 %s W-3 %s" % (dumps(w1), dumps(w2), dumps(w3d)))
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", args.out)


if __name__ == "__main__":
    main()
