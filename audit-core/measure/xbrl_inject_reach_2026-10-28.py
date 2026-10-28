# -*- coding: utf-8 -*-
u"""診断: 新しい標本の注入 741 行の全部で、差し替えが「基準の claim」に届いたかを数える ― 2026-10-28。

封 ``docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md``(commit ``df5c215``)§2 と、その §6-5 の追記(型ごとの対応の関数を自分で持ち、本物の ``_find_base_claim`` と行ごとに一致を確かめる。
P26/P27 でその profile の無改変の一覧から基準が None になる行は、記録の P22 の基準の id で引く)の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。記録 ``fixtures/xbrl/fresh/fresh_2026-10-21.json`` は書き換えない(別の記録を足す)。** 0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。

    cd audit-core
    python3 measure/xbrl_inject_reach_2026-10-28.py --procs 6                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_inject_reach_2026-10-28.py --docs 2 --out <scratch の file>   # 試走(先頭 n 書類。配線の門はその n 書類の分)

書類: 取得の記録 ``fixtures/xbrl/fresh/fetched_2026-10-21.json`` の「使う」30 件(引いた順。先頭は S100YXFQ、2 番目は S100YZ4M)。
生 ZIP は ``~/.cache/audit-core/edinet-fresh-2026-10-21/`` から読み、sha256 を取得の記録と照らす。既存の cache ``~/.cache/audit-core/edinet/``(281)は読まず書かない。
``edinetdb-p27/`` は開かない。

配線(封 §2-1): 材料・注入・対応付けは ``measure/xbrl_fresh_2026-10-21.py`` の関数をそのまま使う(``_mod`` で読み込む)。
``IJ.select(text, refs, "xbrl", seed, doc, INJECT_CAP, types=[t])`` を ``INJECT_TYPES`` の順に測定と同じ引数で呼ぶ。**自分で注入の規則を書かない。**
配線の門: 30 書類の注入の行を作り直し、``元の字``・``後の字``・``基準の claim``・``結果``(P22〜P26)の 4 欄が記録の同じ ``id`` の行と全部一致すること(741 / 741)、id の集合が記録と同じこと、
``注入の件数(書類別)`` の ``注入の行になった``・``基準に対応が付かない``・``基準が GROUNDED でない`` の 3 つの数が 30 書類 × 4 型 = 120 組とも一致すること。
**1 つでも違えば記録を書かずに止める**(私の配線が測定と違うなら、観測は測定の観測ではない)。

観測(封 §2-2): 無改変と差し替え後の両方を ``_RawTap`` + ``verify_raw`` で走らせ(P22・P23・P24・P25・P26・P27)、claim ごとの文の番号と文の中の位置、文の一覧を取る。
基準の claim は ``_find_base_claim`` と同じ順(型ごとの値と字 -> 値だけ)で自前に判定し、指す claim が本物と同じでなければ止める(行ごとの旗を記録する)。
その profile の無改変の一覧から基準が None になる行は、記録の P22 の基準の id をその profile の無改変の一覧から id で引く(封 §6-5)。
分類(封 §2-3)は ``classify_row`` の 1 か所で決める。
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
import shutil
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


FR = _mod("measure/xbrl_fresh_2026-10-21.py", "fresh_for_inject_reach")
T2D = _mod("measure/xbrl_t2_pass_diag_2026-10-28.py", "t2diag_for_inject_reach")
A1, IJ, LB = FR.A1, FR.IJ, FR.LB
N = IJ.N

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL_REL = "docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md"
SEAL_COMMIT = "df5c215"
OUT_REL = "fixtures/xbrl/inject_reach_2026-10-28.json"
FRESH_REC_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
FETCHED_REL = FR.FETCHED_REL
PROFILES5 = tuple(FR.PROFILES)              # P22〜P26(配線の門)
OBS = ("P22", "P26", "P27")                  # 観測する profile(封 §2-1)
ALLP = tuple(sorted(set(PROFILES5) | set(OBS)))
TOL = FR.TOL
INJECT_TYPES = tuple(FR.INJECT_TYPES)
ENGINE_FILES = T2D.ENGINE_FILES
CLAIM_KEYS = ("id", "kind", "form", "value", "unit", "span", "state", "reason", "pointers")

K_BOTH, K_VALUE, K_NONE = T2D.K_BOTH, T2D.K_VALUE, T2D.K_NONE
C_NOMAP, C_NOSENT = u"(対応が付かない)", u"(文が 1 つに決まらない)"
C_RS, C_RP = u"(届いた・止めた)", u"(届いた・通した)"
C_NS, C_NP = u"(届かない・止めた)", u"(届かない・通した)"
CLASSES = (C_NOMAP, C_NOSENT, C_RS, C_RP, C_NS, C_NP)
D_NUM, D_OTHER = u"数の位置が合う", u"同じ文・別の数"
D_DIFFID, D_SAMEID_MOVED, D_SAMEID_SAME = u"注入後の claim が基準と別の id", u"同じ id・state が無改変と違う", u"同じ id・state も無改変と同じ"


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def sha64(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def view(c):
    if c is None:
        return None
    return dict((k, c.get(k)) for k in CLAIM_KEYS)


# ----------------------------------------------------------------------------------------------------------------
# 対応付け(本物の関数と同じ順で、どの枝で 1 件に決まったかを返す。本物が指す claim と同じことを呼び出し側で確かめる)
def base_key(inj, text):
    u"""``_find_base_claim`` の (値, 字)。型ごと(T3 は基準なし)。"""
    t, d = inj["type"], inj["detail"]
    if t == "T1_VALUE":
        return d["original_value"], text[inj["span"][0]:inj["span"][1]]
    if t == "T5_COINCIDENT":
        return d["true_value"], text[inj["span"][0]:inj["span"][1]]
    if t == "T2_UNIT":
        return inj["new_value"], d["digits_unchanged"]
    return None, None


def base_match_typed(base_claims, inj, text):
    v0, s0 = base_key(inj, text)
    if v0 is None:
        return K_NONE, None
    c1 = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL and c.get("span") and s0 in c["span"]]
    if len(c1) == 1:
        return K_BOTH, c1[0]
    c2 = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL]
    return (K_VALUE, c2[0]) if len(c2) == 1 else (K_NONE, None)


def num_span(sentence, pos):
    u"""文の ``pos`` 以降の最初の数の字の (始まり, 終わり, 字)。pos から数の頭までが 3 字を超えるなら None。"""
    if sentence is None or pos is None or pos > len(sentence):
        return None
    m = N.NUM_RE.search(sentence, pos)
    if m is None or m.start() - pos > 3:
        return None
    return m.start(), m.end(), m.group(0)


def inserted_index(s0, s1):
    u"""T3: 注入後の文の一覧が 1 つ長く、1 つを除くと無改変と同じになる番号(1 つに決まらなければ None)と候補の数。"""
    if len(s1) != len(s0) + 1:
        return None, 0
    c = [i for i in range(len(s1)) if s1[:i] + s1[i + 1:] == s0]
    return (c[0] if len(c) == 1 else None), len(c)


def classify_row(after_claim, sentence_known, reached, state):
    u"""封 §2-3(分類 6 語を機械で 1 か所)。先に当たったものを取る。"""
    if after_claim is None:
        return C_NOMAP
    if not sentence_known:
        return C_NOSENT
    if reached:
        return C_RP if state == "GROUNDED" else C_RS
    return C_NP if state == "GROUNDED" else C_NS


def detail_of(cls, reached_sent, reached_num, base_id, after_c, unmod_state):
    u"""細目(記録に持つが分類の順には入れない)。届いた(文)の行は数の位置、届かない・止めた の行は id と state。"""
    if cls in (C_RS, C_RP):
        return D_NUM if reached_num else D_OTHER
    if cls == C_NS:
        if after_c["id"] != base_id:
            return D_DIFFID
        return D_SAMEID_SAME if unmod_state == after_c["state"] else D_SAMEID_MOVED
    return None


# ----------------------------------------------------------------------------------------------------------------
def observe_main(inj, text, bc_id, digits, plain, tam):
    u"""T1_VALUE・T2_UNIT・T5_COINCIDENT の 1 行。plain[p] = verify_raw の出力(無改変)、tam[p] = 同(差し替え後)。"""
    d = inj["detail"]
    out = {}
    for p in OBS:
        out0, raw0, s0 = plain[p]
        out1, raw1, s1 = tam[p]
        by0 = dict((c["id"], c) for c in out0["claims"])
        kind0, own = base_match_typed(out0["claims"], inj, text)
        real = FR._find_base_claim(out0["claims"], inj, text)
        if (real or {}).get("id") != (own or {}).get("id"):
            raise SystemExit(u"**対応付けの枝の判定が本物の _find_base_claim と違う: %s %s %s。止める**" % (inj["id"], p, inj["type"]))
        base_p = by0.get(bc_id)                         # 封 §6-5: 記録の P22 の基準の id をこの profile の無改変の一覧から id で引く
        r0 = raw0.get((base_p or {}).get("id"), {})
        sent0 = s0[r0["sentence"]] if r0.get("sentence") is not None else None
        ns = num_span(sent0, r0.get("pos"))
        tidx, toff = T2D.diff_sentence(s0, s1)
        reached_sent = bool(tidx is not None and base_p is not None and r0.get("sentence") == tidx)
        reached_num = bool(reached_sent and ns is not None and toff is not None and ns[0] <= toff <= ns[1] + 2)
        kind1, c1m = T2D.after_match(out1["claims"], inj)
        c1 = A1.claim_for(out1["claims"], inj)
        if (c1 or {}).get("id") != (c1m or {}).get("id"):
            raise SystemExit(u"**注入後の対応付けの枝の判定が本物の claim_for と違う: %s %s。止める**" % (inj["id"], p))
        r1 = raw1.get((c1 or {}).get("id"), {})
        res = None if c1 is None else [c1["state"], c1["reason"]]
        unmod_same_id = by0.get((c1 or {}).get("id"))
        cls = classify_row(c1, tidx is not None, reached_sent, (c1 or {}).get("state"))
        around = None
        if tidx is not None and toff is not None:
            around = s0[tidx][max(0, toff - 10):toff + 12]
        out[p] = {
            u"無改変": {u"この profile の基準の id": (own or {}).get("id"), u"対応の付け方": kind0, u"基準の id が記録の P22 と同じ": (own or {}).get("id") == bc_id,
                      u"枝が本物の _find_base_claim と同じ": True, u"記録の基準の id が一覧に在る": base_p is not None,
                      u"claim": view(base_p), u"文の番号": r0.get("sentence"), u"文の中の位置": r0.get("pos"),
                      u"数の字": None if ns is None else ns[2], u"数の始まり": None if ns is None else ns[0], u"数の終わり": None if ns is None else ns[1],
                      u"数の字が元の字(T2 は digits_unchanged)と完全一致": None if ns is None else (ns[2] == digits)},
            u"token": {u"文の番号": tidx, u"文の中で最初に違う位置": toff, u"周り(無改変)": around, u"文の数(無改変, 注入後)": [len(s0), len(s1)]},
            u"届いた(文)": reached_sent, u"届いた(数)": reached_num,
            u"注入後": {u"対応の付け方": kind1, u"枝が本物の claim_for と同じ": True, u"claim": view(c1), u"文の番号": r1.get("sentence"),
                      u"記録の基準の id と同じ id": (c1 or {}).get("id") == bc_id,
                      u"無改変の同じ id の state": None if unmod_same_id is None else unmod_same_id["state"],
                      u"state が無改変の同じ id と同じ": None if (c1 is None or unmod_same_id is None) else (unmod_same_id["state"] == c1["state"]),
                      u"後の字が span に在る(字の包含。判定には使わない)": bool(c1 and c1.get("span") and inj["replacement"] in c1["span"])},
            u"結果": FR.outcome_of(res),
            u"分類": cls,
            u"細目": detail_of(cls, reached_sent, reached_num, bc_id, c1, None if unmod_same_id is None else unmod_same_id["state"]),
        }
    return out


def observe_t3(inj, plain, tam):
    u"""T3_ABSENT の 1 行(基準なし。挿入した文が claim になり測定が拾ったか)。"""
    out = {}
    for p in OBS:
        out0, raw0, s0 = plain[p]
        out1, raw1, s1 = tam[p]
        c1 = A1.claim_for(out1["claims"], inj)
        idx, ncand = inserted_index(s0, s1)
        r1 = raw1.get((c1 or {}).get("id"), {})
        reached = bool(idx is not None and c1 is not None and r1.get("sentence") == idx)
        res = None if c1 is None else [c1["state"], c1["reason"]]
        cls = classify_row(c1, idx is not None, reached, (c1 or {}).get("state"))
        out[p] = {
            u"挿入した文の番号": idx, u"候補の数": ncand, u"文の数(無改変, 注入後)": [len(s0), len(s1)],
            u"挿入した文に在る claim の数": len(T2D.claims_in_sentence(out1["claims"], raw1, idx)) if idx is not None else None,
            u"claim": view(c1), u"注入後の claim の文の番号": r1.get("sentence"), u"届いた": reached,
            u"結果": FR.outcome_of(res), u"分類": cls,
        }
    return out


def work_doc(a):
    doc, rows_fetched, seed, work, by_id, counts_rec = a
    t0 = time.time()
    zb = FR.read_zip(doc, rows_fetched)                   # sha256 を取得の記録と照らす(違えば止める)
    old, A1.TMP = A1.TMP, work
    try:
        text, refs = A1.material(doc)
    finally:
        A1.TMP = old
    out_rows, wiring, counts = [], [], {}
    with LB._RawTap() as tap:
        plain = dict((p, LB.verify_raw(tap, zb, p)) for p in ALLP)
        base = plain["P22"][0]["claims"]
        for t in INJECT_TYPES:
            chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, doc, FR.INJECT_CAP, types=[t])
            counts[t] = {u"作れる site": cat[t], u"採った": len(chosen), u"注入の行になった": 0, u"基準に対応が付かない": 0, u"基準が GROUNDED でない": 0}
            for inj in chosen:
                tampered, placements = IJ.apply_edits(text, [inj])
                if IJ.revert(tampered, [inj], placements, text) != text:
                    raise SystemExit(u"**round-trip が合わない: %s %s。止める**" % (doc, inj["id"]))
                bc = FR._find_base_claim(base, inj, text)
                if t != "T3_ABSENT":
                    if bc is None:
                        counts[t][u"基準に対応が付かない"] += 1
                        continue
                    if bc["state"] != "GROUNDED":
                        counts[t][u"基準が GROUNDED でない"] += 1
                        continue
                counts[t][u"注入の行になった"] += 1
                tam, res = {}, {}
                for p in ALLP:
                    tam[p] = LB.verify_raw(tap, zb, p, tampered)
                    c = A1.claim_for(tam[p][0]["claims"], inj)
                    res[p] = None if c is None else [c["state"], c["reason"]]
                rr = by_id.get(inj["id"])
                orig = text[inj["span"][0]:inj["span"][1]]
                flags = {
                    u"記録に同じ id の行が在る": rr is not None,
                    u"元の字": rr is not None and rr[u"元の字"] == orig,
                    u"後の字": rr is not None and rr[u"後の字"] == inj["replacement"],
                    u"基準の claim": rr is not None and rr[u"基準の claim"] == (None if bc is None else bc["id"]),
                    u"結果(P22〜P26)": rr is not None and all(rr[u"結果"][p] == res[p] for p in PROFILES5),
                }
                flags[u"4 欄とも一致"] = all(flags[k] for k in (u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)"))
                wiring.append({u"doc": doc, u"id": inj["id"], u"型": t, u"一致": flags})
                row = {u"doc": doc, u"id": inj["id"], u"型": t, u"元の字": orig, u"後の字": inj["replacement"],
                       u"基準の claim": None if bc is None else bc["id"],
                       u"結果(P22〜P27)": dict((p, FR.outcome_of(res[p])) for p in ALLP),
                       u"結果の state・reason(P22〜P27)": res}
                if t == "T3_ABSENT":
                    row[u"profile"] = observe_t3(inj, dict((p, plain[p]) for p in OBS), dict((p, tam[p]) for p in OBS))
                else:
                    digits = inj["detail"]["digits_unchanged"] if t == "T2_UNIT" else orig
                    row[u"数の字(基準を引く字)"] = digits
                    row[u"profile"] = observe_main(inj, text, bc["id"], digits, dict((p, plain[p]) for p in OBS), dict((p, tam[p]) for p in OBS))
                out_rows.append(row)
        nsent = dict((p, len(plain[p][2])) for p in OBS)
    pairs = {}
    for t in INJECT_TYPES:
        want = counts_rec[t]
        pairs[t] = all(counts[t][k] == want[k] for k in (u"注入の行になった", u"基準に対応が付かない", u"基準が GROUNDED でない"))
        counts[t][u"3 つの数が記録と一致"] = pairs[t]
        counts[t][u"作れる site・採った も記録と一致"] = counts[t][u"作れる site"] == want[u"作れる site"] and counts[t][u"採った"] == want[u"採った"]
    return {u"doc": doc, u"rows": out_rows, u"wiring": wiring, u"counts": counts,
            u"claims": dict((p, len(plain[p][0]["claims"])) for p in OBS), u"文の数": nsent, u"秒": round(time.time() - t0)}


def count_zip(d):
    return len([f for f in os.listdir(d) if f.endswith(".zip")]) if os.path.isdir(d) else None


def dump_record(rec, rowkeys):
    u"""rows と wiring は 1 行 1 件の compact JSON(741 行を indent で広げない)。それ以外は indent=1。妥当な JSON。"""
    parts = []
    for k, v in rec.items():
        if k in rowkeys:
            body = u"[\n" + u",\n".join(u"  " + json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in v) + u"\n ]"
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace(u"\n", u"\n ")
        parts.append(u" %s: %s" % (json.dumps(k, ensure_ascii=False), body))
    return u"{\n" + u",\n".join(parts) + u"\n}\n"


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
    rec_fresh = jload(FRESH_REC_REL)
    rows_rec = rec_fresh[u"注入の行"]
    by_id = dict((r["id"], r) for r in rows_rec)
    docs_all, rows_fetched, fetched = FR.used_docs()
    docs = docs_all if args.docs is None else docs_all[:args.docs]
    cache0 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    seed, meta = IJ.verify_seed_sealed(FR.SEED_FILE)
    work_root = tempfile.mkdtemp(prefix="inject_reach_")
    jobs = []
    for d in docs:
        w = os.path.join(work_root, d)
        os.makedirs(w)
        jobs.append((d, rows_fetched, seed, w, by_id, rec_fresh[u"注入の件数(書類別)"][d]))
    ED.CACHE_DIR = FR.FRESH_DIR
    ctx = multiprocessing.get_context("fork")
    res = {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.procs, mp_context=ctx) as ex:
        futs = dict((ex.submit(work_doc, j), j[0]) for j in sorted(jobs, key=lambda j: -rows_fetched[j[0]]["bytes"]))
        for f in concurrent.futures.as_completed(futs):
            r = f.result()
            res[r["doc"]] = r
            print(u"完了 %d / %d 書類 (%d 行, %d 秒)" % (len(res), len(docs), len(r[u"rows"]), r[u"秒"]), file=sys.stderr)
            sys.stderr.flush()
    shutil.rmtree(work_root, ignore_errors=True)
    out_rows = [x for d in docs for x in res[d][u"rows"]]
    wiring = [x for d in docs for x in res[d][u"wiring"]]

    # 配線の門(封 §2-1)
    rec_ids = sorted(r["id"] for r in rows_rec if r["doc"] in docs)
    mine_ids = sorted(w["id"] for w in wiring)
    n_match = sum(1 for w in wiring if w[u"一致"][u"4 欄とも一致"])
    n_pairs = sum(1 for d in docs for t in INJECT_TYPES)
    n_pairs_ok = sum(1 for d in docs for t in INJECT_TYPES if res[d][u"counts"][t][u"3 つの数が記録と一致"])
    gate = {u"行": len(wiring), u"一致": n_match, u"記録の注入の行(対象の書類)": len(rec_ids), u"id の集合が記録と同じ": rec_ids == mine_ids,
            u"注入の件数の組": n_pairs, u"注入の件数の組の一致": n_pairs_ok}
    gate[u"通った"] = bool(gate[u"id の集合が記録と同じ"] and n_match == len(wiring) == len(rec_ids) and n_pairs_ok == n_pairs)
    if not gate[u"通った"]:
        bad = [w[u"id"] for w in wiring if not w[u"一致"][u"4 欄とも一致"]][:5]
        raise SystemExit(u"**配線の門が通らない(行 %d / %d、組 %d / %d、id の集合 %s)。記録を書かずに止める**(不一致の例 %s)" % (
            n_match, len(wiring), n_pairs_ok, n_pairs, gate[u"id の集合が記録と同じ"], bad))

    cache1 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    per_doc = {}
    for d in docs:
        per_doc[d] = {u"材料の sha256": rows_fetched[d]["sha256"], u"材料の sha256 が取得の記録と一致": True, u"注入の件数": res[d][u"counts"],
                      u"claims": res[d][u"claims"], u"文の数": res[d][u"文の数"], u"秒": res[d][u"秒"]}
    rec = collections.OrderedDict()
    rec[u"注意"] = u"診断の記録(封 docs/XBRL_INJECT_REACH_DIAG_SEAL_2026-10-28.md §5)。engine は 0 行。fresh_2026-10-21.json は書き換えない。"
    rec[u"封"] = {u"file": SEAL_REL, u"commit": git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT}
    rec[u"全書類"] = args.docs is None
    rec[u"HEAD"] = git("rev-parse", "HEAD")
    rec[u"DEFAULT_PROFILE"] = V.DEFAULT_PROFILE
    rec[u"engine sha16"] = dict((rel, sha16(rel)) for rel in ENGINE_FILES)
    rec[u"種"] = meta
    rec[u"読んだ入力の sha256"] = {FRESH_REC_REL: sha64(FRESH_REC_REL), FETCHED_REL: sha64(FETCHED_REL)}
    rec[u"観測する profile"] = list(OBS)
    rec[u"書類(出てくる順)"] = docs
    rec[u"書類ごと"] = per_doc
    rec[u"配線の門"] = gate
    rec[u"cache"] = {u"開始": cache0, u"終了": cache1}
    rec[u"所要秒"] = round(time.time() - t_start)
    rec[u"limits"] = [
        u"30 書類・741 行・1 書類あたり型ごと 40 件までの IJ.select の順の観測。通さなかった site に同じ形が無いとは言えない。Core 全体の振る舞いを断定しない。",
        u"『届いた(文)』は engine の文の一覧の番号の一致で、claim が読む数そのものの一致ではない(届いた(数)は細目)。",
        u"測定の配線と engine を分けて読む。『届かない・止めた』は測定の対応付けの数で、engine の数ではない。",
        u"T3_ABSENT の『届いた』は意味が違う(挿入した文が claim になり測定が拾った)。T1・T2・T5 と混ぜない。",
        u"基準は無改変の P22 で GROUNDED の claim だけ。P26・P27 の基準は記録の P22 の id をその profile の無改変の一覧から引いた claim。",
        u"文の番号は engine の文の一覧の中の番号で、材料の本文の位置ではない。差し替えが文の切り方を変えると『決まらない』になる。",
        u"P22・P26・P27 の 3 profile だけ(P23〜P25 は配線の門)。比べる側の分岐(recipes・resolve・comparators)は読んでいない。読みは無い(機械の値)。",
    ]
    rec[u"rows"] = out_rows
    rec[u"配線の行ごと"] = wiring
    blob = dump_record(rec, (u"rows", u"配線の行ごと"))
    leaks = FR.key_leaks(blob)
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    rec[u"key_leaks"] = []
    blob = dump_record(rec, (u"rows", u"配線の行ごと"))
    with io.open(args.out, "w", encoding="utf-8") as fh:
        fh.write(blob)
    print(u"配線の門: 行 %d / %d・注入の件数の組 %d / %d" % (n_match, len(wiring), n_pairs_ok, n_pairs))
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE, u"所要秒", rec[u"所要秒"])
    print(u"->", args.out)


if __name__ == "__main__":
    main()
