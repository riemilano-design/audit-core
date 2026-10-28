# -*- coding: utf-8 -*-
u"""診断: 注入 T2(単位の差し替え)で P22〜P26 の全部が通した 5 行を、engine の出力と instance の fact で見る ― 2026-10-28。

封 ``docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md``(commit ``2726563``)§2 と、その §6-5 の追記(分類 (ウ-a)/(ウ-b) は字の包含でなく token の位置で分ける)の測定。
**診断だけ。engine(``core/``・``adapters/``)は 0 行。** 0 USD・通信なし・鍵の値は読まない・席(LLM)は呼ばない。

    cd audit-core
    python3 measure/xbrl_t2_pass_diag_2026-10-28.py                       # 既に出力が在れば測り直さない
    python3 measure/xbrl_t2_pass_diag_2026-10-28.py --out <scratch の file>   # 試し

書類: 取得の記録 ``fixtures/xbrl/fresh/fetched_2026-10-21.json`` の「使う」30 件のうち、通した 5 行が載る 3 書類
(S100YYHK・S100YW7F・S100YYH7。記録 ``fresh_2026-10-21.json`` の ``注入の行`` から機械で選ぶ ― 字で留めない)。
生 ZIP は ``~/.cache/audit-core/edinet-fresh-2026-10-21/`` から読み、sha256 を取得の記録と照らす。既存の cache ``~/.cache/audit-core/edinet/``(281)は読まず書かない。
``edinetdb-p27/`` は開かない。

配線(封 §2-1): 材料・注入・対応付けは ``measure/xbrl_fresh_2026-10-21.py`` の関数をそのまま使う(``_mod`` で読み込む)。
``IJ.select(text, refs, "xbrl", seed, doc, INJECT_CAP, types=["T2_UNIT"])`` を測定と同じ引数で呼ぶ。**自分で注入の規則を書かない。**
配線の門: 3 書類の T2_UNIT の注入の行 13 行を作り直し、``元の字``・``後の字``・``基準の claim``・``結果``(P22〜P26)の 4 欄が記録の同じ ``id`` の行と全部一致すること。
1 行でも違えば**記録を書かずに止める**(私の配線が測定と違うなら、観測は測定の観測ではない)。

位置の求め方(封 §6-5 の実装): engine の文の一覧(``_RawTap`` + ``verify_raw``。claim ごとに文の番号 ``sentence`` と文の中の位置 ``pos``)を、
**無改変の run と差し替えた run で比べ**、文が違う番号を「差し替えた token がある文」とする(1 か所だけが違うことを要求し、違えば記録に ``None`` と書く)。
本文(材料)の文字列から文を探し直さない(engine の文は NFKC と strip を通っていて、材料の本文の部分文字列とは限らない ― 下調べで P22 の文 221・376・149 のうち 98・111・38 が材料の本文に見つからなかった)。
分類 (ウ-a): 無改変の基準の claim の文の番号が、token がある文の番号と違う。(ウ-b): 同じ。
"""
from __future__ import print_function

import argparse
import collections
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

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


FR = _mod("measure/xbrl_fresh_2026-10-21.py", "fresh_for_t2_pass_diag")
A1, IJ, LB = FR.A1, FR.IJ, FR.LB
N = IJ.N

from adapters.xbrl import edinet as ED           # noqa: E402
from adapters.xbrl import instance as I          # noqa: E402
from adapters.xbrl import verify_document as VD  # noqa: E402
from adapters.xbrl import vocabulary as V        # noqa: E402

SEAL_REL = "docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md"
SEAL_COMMIT = "2726563"
OUT_REL = "fixtures/xbrl/t2_pass_diag_2026-10-28.json"
FRESH_REC_REL = "fixtures/xbrl/fresh/fresh_2026-10-21.json"
PROFILES5 = tuple(FR.PROFILES)          # P22〜P26(配線の門)
OBS = ("P22", "P26", "P27")              # 観測する profile(封 §2-1)
TOL = FR.TOL
ENGINE_FILES = ("adapters/xbrl/extract.py", "adapters/xbrl/vocabulary.py", "adapters/xbrl/recipes.py",
                "adapters/xbrl/resolve.py", "adapters/xbrl/comparators.py", "adapters/xbrl/verify_document.py")

K_BOTH, K_VALUE, K_NONE = u"値と字", u"値だけ", u"対応が付かない"
C_I, C_U_A, C_U_B, C_A1, C_A2, C_E = u"(イ)", u"(ウ-a)", u"(ウ-b)", u"(ア-1)", u"(ア-2)", u"(エ)"


def jload(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def count_zip(d):
    return len([f for f in os.listdir(d) if f.endswith(".zip")]) if os.path.isdir(d) else None


def git(*a):
    r = subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


# ----------------------------------------------------------------------------------------------------------------
# 対応付け(本物の関数と同じ順で、どの枝で 1 件に決まったかを返す。本物の関数が指す claim と同じことを呼び出し側で確かめる)
def base_match(base_claims, inj, text):
    d = inj["detail"]
    v0, s0 = inj["new_value"], d["digits_unchanged"]
    c1 = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL and c.get("span") and s0 in c["span"]]
    if len(c1) == 1:
        return K_BOTH, c1[0]
    c2 = [c for c in base_claims if c.get("value") is not None and abs(c["value"] - v0) <= TOL]
    return (K_VALUE, c2[0]) if len(c2) == 1 else (K_NONE, None)


def after_match(claims, inj):
    v = inj["new_value"]
    c1 = [c for c in claims if c.get("value") is not None and abs(c["value"] - v) <= TOL and c.get("span") and inj["replacement"] in c["span"]]
    if len(c1) == 1:
        return K_BOTH, c1[0]
    c2 = [c for c in claims if c.get("value") is not None and abs(c["value"] - v) <= TOL]
    return (K_VALUE, c2[0]) if len(c2) == 1 else (K_NONE, None)


def number_text(sentence, pos):
    u"""claim の数の字: 文の ``pos``(符号の位置を含みうる)以降の最初の数の字(``lib/numbers.NUM_RE``。``digits_unchanged`` と同じ正規表現)。
    pos から数の頭までに数字が入ることはない(search の定義)。間が 3 字を超えるなら None(別の数を拾わない)。"""
    if sentence is None or pos is None or pos > len(sentence):
        return None
    m = N.NUM_RE.search(sentence, pos)
    if m is None or m.start() - pos > 3:
        return None
    return m.group(0)


def view(c):
    if c is None:
        return None
    return {k: c.get(k) for k in VD.CLAIM_FIELDS}


def facts_at(inst, pointers):
    idx = collections.defaultdict(list)
    for f in inst["facts"]:
        idx[u"%s@%s" % (f["name"], f["context"])].append(f)
    out = []
    for p in pointers:
        loc = p.split(":", 1)[1] if ":" in p else p
        out.append({u"pointer": p, u"facts": [{k: f.get(k) for k in ("name", "context", "unit", "decimals", "value")} for f in idx.get(loc, [])]})
    return out


def first_fact_value(facts):
    return facts[0][u"facts"][0]["value"] if facts and facts[0][u"facts"] else None


def ratio(a, b):
    if a is None or b is None:
        return None
    if b == 0:
        return u"fact が 0"
    return a / float(b)


def diff_sentence(s0, s1):
    u"""(差し替えた token がある文の番号, 文の中で最初に違う位置)。1 か所だけが違うときだけ。"""
    if len(s0) != len(s1):
        return None, None
    idx = [i for i in range(len(s0)) if s0[i] != s1[i]]
    if len(idx) != 1:
        return None, None
    a, b = s0[idx[0]], s1[idx[0]]
    k = 0
    while k < min(len(a), len(b)) and a[k] == b[k]:
        k += 1
    return idx[0], k


def claims_in_sentence(claims, raw, si):
    u"""文の番号 ``si`` に在る claim(engine の出力の claim)。"""
    if si is None:
        return []
    out = []
    for c in claims:
        r = raw.get(c["id"], {})
        if r.get("sentence") == si:
            out.append({u"id": c["id"], u"pos": r.get("pos"), u"kind": c["kind"], u"form": c["form"], u"value": c["value"], u"unit": c["unit"],
                        u"state": c["state"], u"reason": c["reason"], u"pointers": c["pointers"], u"recomputed": c["recomputed"]})
    return sorted(out, key=lambda x: (x[u"pos"] is None, x[u"pos"], x[u"id"]))


def classify(base, after, token_in_claim_sentence, sentence_known):
    u"""封 §2-3(§6-5 で (ウ-a)/(ウ-b) を位置で分ける)。base・after は claim の view(None なら (エ))。"""
    if base is None or after is None:
        return C_E
    if base["pointers"] != after["pointers"]:
        return C_I
    if base["unit"] == after["unit"]:
        if not sentence_known:
            return C_E
        return C_U_B if token_in_claim_sentence else C_U_A
    if after["state"] == "GROUNDED":
        s0, s1 = V.UNIT_SCALE.get(base["unit"]), V.UNIT_SCALE.get(after["unit"])
        return C_A1 if (s0 is None and s1 is None) else C_A2
    return C_E


def observe(doc, zb, inst, inj, text, tampered, plain_by_p, tam_by_p, base_by_p):
    u"""1 行・3 profile の観測。plain_by_p[p] = (out, raw, sentences)(無改変)、tam_by_p[p] = (out, raw, sentences)(差し替え後)。"""
    row = {u"profile": {}}
    d = inj["detail"]
    for p in OBS:
        out0, raw0, s0 = plain_by_p[p]
        out1, raw1, s1 = tam_by_p[p]
        kind0, c0 = base_by_p[p]
        claims1 = out1["claims"]
        kind1, c1 = after_match(claims1, inj)
        c1_real = A1.claim_for(claims1, inj)
        tidx, toff = diff_sentence(s0, s1)
        r0 = raw0.get((c0 or {}).get("id"), {})
        r1 = raw1.get((c1 or {}).get("id"), {})
        in_sentence = (tidx is not None and r0.get("sentence") == tidx)
        f0 = facts_at(inst, (c0 or {}).get("pointers") or [])
        f1 = facts_at(inst, (c1 or {}).get("pointers") or [])
        fv0, fv1 = first_fact_value(f0), first_fact_value(f1)
        u0, u1 = (c0 or {}).get("unit"), (c1 or {}).get("unit")
        s_0, s_1 = V.UNIT_SCALE.get(u0), V.UNIT_SCALE.get(u1)
        sv0 = None if c0 is None or c0.get("value") is None else c0["value"] * (s_0 if s_0 is not None else 1)
        sv1 = None if c1 is None or c1.get("value") is None else c1["value"] * (s_1 if s_1 is not None else 1)
        num0 = number_text(s0[r0["sentence"]] if r0.get("sentence") is not None else None, r0.get("pos"))
        num1 = number_text(s1[r1["sentence"]] if r1.get("sentence") is not None else None, r1.get("pos"))
        v0, v1 = view(c0), view(c1)
        cmp = {
            u"pointers が同じ": (c0 or {}).get("pointers") == (c1 or {}).get("pointers"),
            u"unit が変わった": u0 != u1,
            u"value が同じ": (c0 or {}).get("value") == (c1 or {}).get("value"),
            u"recomputed が同じ": (c0 or {}).get("recomputed") == (c1 or {}).get("recomputed"),
            u"state が同じ": (c0 or {}).get("state") == (c1 or {}).get("state"),
            u"同じ claim id": (c0 or {}).get("id") == (c1 or {}).get("id"),
            u"後の字が注入後の span に在る(字の包含)": bool(c1 and c1.get("span") and inj["replacement"] in c1["span"]),
            u"元の token の位置が無改変の claim の文の中に在る": in_sentence,
            u"倍率(無改変, 注入後)": [s_0, s_1],
            u"value×倍率(無改変, 注入後)": [sv0, sv1],
            u"fact の値(先頭)(無改変, 注入後)": [fv0, fv1],
            u"注入後 value×倍率 / fact": ratio(sv1, fv1),
            u"無改変 value×倍率 / fact": ratio(sv0, fv0),
        }
        row[u"profile"][p] = {
            u"無改変": {u"対応の付け方": kind0, u"digits_unchanged が claim の数の字と完全一致": (num0 == d["digits_unchanged"]) if num0 is not None else None,
                       u"claim の数の字": num0, u"文の番号": r0.get("sentence"), u"文の中の位置": r0.get("pos"), u"claim": v0, u"fact": f0},
            u"注入後": {u"対応の付け方": kind1, u"claim_for と同じ": (c1_real or {}).get("id") == (c1 or {}).get("id"),
                       u"digits_unchanged が claim の数の字と完全一致": (num1 == d["digits_unchanged"]) if num1 is not None else None,
                       u"claim の数の字": num1, u"文の番号": r1.get("sentence"), u"文の中の位置": r1.get("pos"), u"claim": v1, u"fact": f1},
            u"token": {u"差し替えた token がある文の番号": tidx, u"文の中で最初に違う位置": toff,
                       u"token の位置を文に持つ claim の数(無改変, 注入後)": [len(claims_in_sentence(out0["claims"], raw0, tidx)), len(claims_in_sentence(claims1, raw1, tidx))],
                       u"その文の claim": {u"無改変": claims_in_sentence(out0["claims"], raw0, tidx), u"注入後": claims_in_sentence(claims1, raw1, tidx)}},
            u"比較": cmp,
            u"fact が 0": (fv1 == 0) if fv1 is not None else None,
            u"分類": classify(v0, v1, in_sentence, tidx is not None),
        }
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(ROOT, OUT_REL))
    args = ap.parse_args()
    if os.path.exists(args.out):
        print(u"既に在る(測り直さない): %s" % args.out)
        return

    rec_fresh = jload(FRESH_REC_REL)
    rows_rec = rec_fresh[u"注入の行"]
    passed = [r for r in rows_rec if all((r[u"結果"].get(p) or [None])[0] == "GROUNDED" for p in PROFILES5)]
    passed_any = [r for r in rows_rec if any((r[u"結果"].get(p) or [None])[0] == "GROUNDED" for p in PROFILES5)]
    if [r["id"] for r in passed] != [r["id"] for r in passed_any]:
        raise SystemExit(u"**どれか 1 つの profile で GROUNDED の行が、全部 GROUNDED の行と違う。止める**")
    passed_ids = [r["id"] for r in passed]
    target_docs = []
    for r in passed:
        if r["doc"] not in target_docs:
            target_docs.append(r["doc"])
    by_id = {r["id"]: r for r in rows_rec}
    t2_rec = [r for r in rows_rec if r[u"型"] == "T2_UNIT" and r["doc"] in target_docs]

    docs_all, rows_fetched, fetched = FR.used_docs()
    cache0 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    seed, meta = IJ.verify_seed_sealed(FR.SEED_FILE)
    work_root = os.path.join(os.environ.get("TMPDIR") or ROOT, "t2_pass_diag_work")

    saved = ED.CACHE_DIR
    ED.CACHE_DIR = FR.FRESH_DIR
    per_doc, wiring_rows, out_rows = {}, [], []
    try:
        for doc in target_docs:
            zb = FR.read_zip(doc, rows_fetched)               # sha256 を取得の記録と照らす(違えば止める)
            inst = I.load_instance(zb)
            work = os.path.join(work_root, doc)
            os.makedirs(work, exist_ok=True)
            old_tmp, A1.TMP = A1.TMP, work
            try:
                text, refs = A1.material(doc)
            finally:
                A1.TMP = old_tmp
            chosen, cat, _a, _w = IJ.select(text, refs, "xbrl", seed, doc, FR.INJECT_CAP, types=["T2_UNIT"])
            with LB._RawTap() as tap:
                plain = {}
                for p in sorted(set(PROFILES5) | set(OBS)):
                    plain[p] = LB.verify_raw(tap, zb, p)
                base = plain["P22"][0]["claims"]
                n_rows = 0
                for inj in chosen:
                    tampered, placements = IJ.apply_edits(text, [inj])
                    if IJ.revert(tampered, [inj], placements, text) != text:
                        raise SystemExit(u"**round-trip が合わない: %s %s。止める**" % (doc, inj["id"]))
                    bc = FR._find_base_claim(base, inj, text)
                    if bc is None or bc["state"] != "GROUNDED":
                        continue
                    n_rows += 1
                    tam, res = {}, {}
                    for p in sorted(set(PROFILES5) | set(OBS)):
                        tam[p] = LB.verify_raw(tap, zb, p, tampered)
                        c = A1.claim_for(tam[p][0]["claims"], inj)
                        res[p] = None if c is None else [c["state"], c["reason"]]
                    rr = by_id.get(inj["id"])
                    flags = {
                        u"記録に同じ id の行が在る": rr is not None,
                        u"元の字": rr is not None and rr[u"元の字"] == text[inj["span"][0]:inj["span"][1]],
                        u"後の字": rr is not None and rr[u"後の字"] == inj["replacement"],
                        u"基準の claim": rr is not None and rr[u"基準の claim"] == bc["id"],
                        u"結果(P22〜P26)": rr is not None and all(rr[u"結果"][p] == res[p] for p in PROFILES5),
                    }
                    flags[u"4 欄とも一致"] = all(flags[k] for k in (u"元の字", u"後の字", u"基準の claim", u"結果(P22〜P26)"))
                    wiring_rows.append({u"doc": doc, u"id": inj["id"], u"型": inj["type"], u"元の字": text[inj["span"][0]:inj["span"][1]],
                                        u"後の字": inj["replacement"], u"基準の claim": bc["id"], u"結果": dict((p, res[p]) for p in PROFILES5),
                                        u"一致": flags})
                    if inj["id"] not in passed_ids:
                        continue
                    base_by_p = {}
                    for p in OBS:
                        k0, c0 = base_match(plain[p][0]["claims"], inj, text)
                        real = FR._find_base_claim(plain[p][0]["claims"], inj, text)
                        if (real or {}).get("id") != (c0 or {}).get("id"):
                            raise SystemExit(u"**対応付けの枝の判定が本物の _find_base_claim と違う: %s %s %s。止める**" % (doc, inj["id"], p))
                        base_by_p[p] = (k0, c0)
                    obs = observe(doc, zb, inst, inj, text, tampered, dict((p, plain[p]) for p in OBS), dict((p, tam[p]) for p in OBS), base_by_p)
                    row = {u"doc": doc, u"id": inj["id"], u"元の字": text[inj["span"][0]:inj["span"][1]], u"後の字": inj["replacement"],
                           u"元の token の span(材料の本文)": list(inj["span"]), u"digits_unchanged": inj["detail"]["digits_unchanged"],
                           u"基準の claim": bc["id"], u"結果": res}
                    row.update(obs)
                    out_rows.append(row)
            per_doc[doc] = {u"材料の sha256": rows_fetched[doc]["sha256"], u"材料の sha256 が取得の記録と一致": True,
                            u"T2 の行": n_rows, u"配線の一致": sum(1 for w in wiring_rows if w[u"doc"] == doc and w[u"一致"][u"4 欄とも一致"]),
                            u"claims(P22)": len(base), u"claims(P27)": len(plain["P27"][0]["claims"]), u"facts": len(inst["facts"]),
                            u"T2 の作れる site": cat["T2_UNIT"], u"採った": len(chosen)}
    finally:
        ED.CACHE_DIR = saved

    # 配線の門(封 §2-1): 記録の T2_UNIT の行(3 書類)と作り直した行が id の集合として同じで、4 欄が全部一致。
    rec_ids = sorted(r["id"] for r in t2_rec)
    mine_ids = sorted(w["id"] for w in wiring_rows)
    n_match = sum(1 for w in wiring_rows if w[u"一致"][u"4 欄とも一致"])
    gate = {u"行": len(wiring_rows), u"一致": n_match, u"記録の T2_UNIT の行(3 書類)": len(t2_rec), u"id の集合が記録と同じ": rec_ids == mine_ids,
            u"通した行の id が記録から機械で選んだ行と一致": sorted(r["id"] for r in out_rows) == sorted(passed_ids),
            u"行ごと": wiring_rows}
    gate[u"通った"] = bool(gate[u"id の集合が記録と同じ"] and n_match == len(wiring_rows) == len(t2_rec) and gate[u"通した行の id が記録から機械で選んだ行と一致"])
    if not gate[u"通った"]:
        raise SystemExit(u"**配線の門が通らない(%d / %d)。記録を書かずに止める**" % (n_match, len(wiring_rows)))
    # 記録の ``注入の件数(書類別)`` の ``注入の行になった`` と同じ数
    counts = rec_fresh[u"注入の件数(書類別)"]
    for doc in target_docs:
        want = counts[doc]["T2_UNIT"][u"注入の行になった"]
        if per_doc[doc][u"T2 の行"] != want:
            raise SystemExit(u"**注入の行になった数が記録と違う: %s %d != %d。止める**" % (doc, per_doc[doc][u"T2 の行"], want))

    cache1 = {u"edinet": count_zip(FR.EXISTING_CACHE), u"edinet-fresh-2026-10-21": count_zip(FR.FRESH_DIR)}
    rec = {
        u"注意": u"診断の記録(封 docs/XBRL_T2_PASS_DIAG_SEAL_2026-10-28.md §5)。engine は 0 行。fresh_2026-10-21.json は書き換えない。",
        u"封": {u"file": SEAL_REL, u"commit": git("log", "--diff-filter=A", "--format=%h", "--", SEAL_REL), u"期待する commit": SEAL_COMMIT},
        u"HEAD": git("rev-parse", "HEAD"), u"DEFAULT_PROFILE": V.DEFAULT_PROFILE,
        u"engine sha16": dict((rel, sha16(rel)) for rel in ENGINE_FILES),
        u"種": meta,
        u"通した行(記録から)": passed_ids,
        u"書類(出てくる順)": target_docs,
        u"書類ごと": per_doc,
        u"配線の門": gate,
        u"rows": out_rows,
        u"cache": {u"開始": cache0, u"終了": cache1},
        u"limits": [
            u"5 行・3 書類・4 claim の観測。T2_UNIT 263 行・注入 741 回・Core 全体の振る舞いを断定しない。",
            u"新しい標本 30 書類の 741 回だけ。67 書類側の属性注入とは別の種・別の作り方。",
            u"差し替えた token がある文は、無改変と差し替え後の engine の文の一覧を比べ、違う文が 1 つのときだけ決める(材料の本文から文を探し直さない)。",
            u"分類は欄から機械で決まる型で、意味(なぜそうなるか)は文書の仮説の節。比べる側の分岐(recipes・resolve・comparators)はこの便では読んでいない。",
            u"『その文の claim』は封にない欄(token の文に在る claim の state を無改変と差し替え後で並べたもの)。判定には使わない。",
        ],
    }
    blob = json.dumps(rec, ensure_ascii=False, indent=1)
    leaks = FR.key_leaks(blob)
    rec[u"key_leaks"] = leaks
    if leaks:
        raise SystemExit(u"**鍵らしい字が在る: %s。書かずに止める**" % leaks)
    with io.open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
        fh.write(u"\n")
    print(u"配線の門: %d / %d" % (n_match, len(wiring_rows)))
    for r in out_rows:
        print(u"%s %s -> %s | %s" % (r["id"], r[u"元の字"], r[u"後の字"], u" ".join(u"%s:%s" % (p, r[u"profile"][p][u"分類"]) for p in OBS)))
    print(u"cache", cache0, cache1, u"DEFAULT_PROFILE", V.DEFAULT_PROFILE)
    print(u"->", args.out)


if __name__ == "__main__":
    main()
