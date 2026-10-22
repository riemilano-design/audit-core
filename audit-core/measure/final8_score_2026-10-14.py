# -*- coding: utf-8 -*-
"""最終評価用 8 書類(docs/FINAL_EVAL_8_SEAL_2026-10-14.md)の採点。**回答が 1 つも無い状態で書いて固定する。**

段 0 ``rates``  (開封直後。ラベルに依らない封 §3 の数): k、主張の件数、N-0(A 群で P16 と P20 の
                (state, pointers) が違う行。claim id で対にした数と、内容の鍵で対にならない行の数)、
                R-1/R-2(P16/P20 の GROUNDED 率)、書類レベルの沈黙。
段 1 ``labels`` 2 席の回答から確定ラベルを作る(P16 の限定確認と同じ規則)。判定不能(両側)の行には
                両席の「判定不能の理由」を残す(U_absent で使う)。
段 2 ``dumps``  P16・P20 を 8 書類で回し、行の鍵ごとに state・pointers を書く(claim id で対応)。
段 3 ``score``  封 §4 の表だけを出す:
                A 群(P16): R-S1 = E1'/L ≥ 0.50, R-S2 = E2/G ≤ 0.10, R-S3 = E3/L ≤ 0.40
                B 群(P20): N-1 = E1'/L ≥ 0.50, N-2 = E2/G ≤ 0.10, N-3 = E2_member + U_absent = 0
                E2_member = GROUNDED ∧ 厳密不一致 ∧ 要素の局所名の集合は同じ ∧ context の member の集合が違う
                U_absent  = 両席とも判定不能で理由が「対象が文書に無い」∧ P20 が GROUNDED
通信しない。engine は変えない。回答ファイルは読むだけで書き換えない。
"""

import collections
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, HERE)

import grounds_eval as GE  # noqa: E402

DATE = "2026-10-14"
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")
BASE = os.environ.get("FINAL8_BASE") or os.path.join(ROOT, "fixtures", "xbrl", "final8")
PROFILES = ("P16", "P20")
THRESH = {"RS1_E1_over_L_min": 0.50, "RS2_E2_over_G_max": 0.10, "RS3_E3_over_L_max": 0.40,
          "N1_E1_over_L_min": 0.50, "N2_E2_over_G_max": 0.10, "N3_max": 0}
L_A_MIN, L_B_MIN = 100, 40
ABSENT = "対象が文書に無い"


def docs():
    env = os.environ.get("FINAL8_DOCS")
    if env:
        return tuple(x for x in env.split(",") if x)
    return tuple(json.load(io.open(SPLIT, encoding="utf-8"))["final_eval_sealed"])


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def local(name):
    return name.split(":", 1)[-1]


def fact_set(row):
    return {(local(f["要素"]), f["context"]) for f in row.get("fact") or []}


def v0(s):
    return {(GE.canon(e), c) for e, c in s}


def groups():
    rec = json.load(io.open(os.path.join(BASE, "classify_%s.json" % DATE), encoding="utf-8"))
    return {r["docID"]: r["group"] for r in rec["docs"]}


def _zip(doc):
    from adapters.xbrl import edinet
    return open(edinet.cache_path(doc), "rb").read()


def _run(doc, prof):
    from tests.golden import _instrument as H
    from adapters.xbrl import recipes as R
    zb = _zip(doc)
    rl, res, _ = H.run_verification(doc, prof, lambda: zb)
    num, txt = R.build_raw_claims(zb, prof)
    raw = {c["id"]: c for c in num + txt}
    assert set(raw) == {r.claim.id for r in rl}, "claim id の集合が build_raw_claims と run_verification で違う"
    out = {}
    for r in rl:
        x = res[r.claim.id]
        c = raw.get(r.claim.id, {})
        ptrs = [(q if isinstance(q, str) else q.scheme + ":" + q.locator) for q in x.pointers]
        out[r.claim.id] = {"state": x.state.name, "pointers": ptrs,
                           "subject": r.claim.subject, "span": r.claim.provenance.get("span"), "reason": x.reason,
                           "ckey": "%s|%s|%s" % (c.get("span"), c.get("value"), c.get("word")),
                           "ckey_noform": "%s|%s|%s" % (c.get("span"), c.get("value"), c.get("word"))}
    return out


def _profile(name):
    from adapters.xbrl import vocabulary as V
    return V.PROFILES[name]


# ---------------------------------------------------------------- 段 0
def rates():
    grp = groups()
    out = {"k": sum(1 for g in grp.values() if g == "B"), "docs": {}, "N0": {}, "R": {}}
    tot = {p: collections.Counter() for p in PROFILES}
    for doc in docs():
        runs = {p: _run(doc, _profile(p)) for p in PROFILES}
        d = {"group": grp[doc], "claims": len(runs["P16"])}
        for p in PROFILES:
            st = collections.Counter(v["state"] for v in runs[p].values())
            d[p] = {"states": dict(st), "grounded_pct": round(100.0 * st["GROUNDED"] / (len(runs[p]) or 1), 1),
                    "document_unverifiable": st["GROUNDED"] == 0}
            tot[p].update(st)
        if grp[doc] == "A":
            a, b = runs["P16"], runs["P20"]
            changed = [i for i in a if (a[i]["state"], a[i]["pointers"]) != (b[i]["state"], b[i]["pointers"])]
            ka = collections.Counter(v["ckey"] for v in a.values())
            kb = collections.Counter(v["ckey"] for v in b.values())
            out["N0"][doc] = {"changed_by_id": len(changed), "changed_ids": changed[:20],
                              "unpaired_by_content_key": sum((ka - kb).values()) + sum((kb - ka).values()),
                              "dup_keys_P16": sum(1 for v in ka.values() if v > 1)}
        out["docs"][doc] = d
    n = sum(tot["P16"].values())
    for p in PROFILES:
        out["R"][p] = {"claims": n, "grounded": tot[p]["GROUNDED"],
                       "grounded_pct": round(100.0 * tot[p]["GROUNDED"] / (n or 1), 1), "states": dict(tot[p])}
    out["N0_total"] = {"changed_by_id": sum(v["changed_by_id"] for v in out["N0"].values()),
                       "unpaired_by_content_key": sum(v["unpaired_by_content_key"] for v in out["N0"].values())}
    p = os.path.join(BASE, "rates_%s.json" % DATE)
    if os.path.exists(p):
        raise SystemExit("既に在る。上書きしない: %s" % p)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"k": out["k"], "N0_total": out["N0_total"], "R": out["R"]}, ensure_ascii=False, indent=1))
    print("rates ->", p)


# ---------------------------------------------------------------- 段 1
def build_labels():
    out, counts = [], collections.Counter()
    for doc in docs():
        p1 = os.path.join(BASE, "answers_seat1", "answer_%s.json" % doc)
        p2 = os.path.join(BASE, "answers_seat2", "answer_%s.json" % doc)
        a1 = json.load(io.open(p1, encoding="utf-8"))
        a2 = json.load(io.open(p2, encoding="utf-8"))
        mat = json.load(io.open(os.path.join(BASE, "seat", "material_%s.json" % doc), encoding="utf-8"))
        keys = [r["行の鍵"] for r in mat["行"]]
        r1 = {r["行の鍵"]: r for r in a1["行"]}
        r2 = {r["行の鍵"]: r for r in a2["行"]}
        for k in keys:
            x, y = r1.get(k), r2.get(k)
            row = {"id": "%s:%s" % (doc, k), "docID": doc, "鍵": k}
            if x is None or y is None:
                row["分類"] = "回答なし(%s)" % ("席1" if x is None else "席2")
            else:
                j1, j2 = x.get("判定") == "独立判定", y.get("判定") == "独立判定"
                row["形"] = [x.get("形"), y.get("形")]
                if j1 and j2:
                    s1, s2 = fact_set(x), fact_set(y)
                    if s1 == s2:
                        row["分類"], row["厳密一致"], row["v0_only"] = "確定(同値類v0)", True, False
                    elif v0(s1) == v0(s2):
                        row["分類"], row["厳密一致"], row["v0_only"] = "確定(同値類v0)", False, True
                    else:
                        row["分類"] = "不一致"
                    row["fact"] = sorted(s1) if row["分類"].startswith("確定") else None
                    cands = [[c.get("要素"), c.get("context")] for r in (x, y) for c in (r.get("同値の他の候補") or [])]
                    if row.get("v0_only"):
                        cands += [[e, c] for e, c in sorted(s2)]
                    row["同値の他の候補"] = cands
                    if row["分類"] == "不一致":
                        row["席1"], row["席2"] = sorted(s1), sorted(s2)
                elif j1 or j2:
                    row["分類"] = "判定不能(片側)"
                else:
                    row["分類"] = "判定不能(両側)"
                    row["判定不能の理由"] = [x.get("判定不能の理由"), y.get("判定不能の理由")]
            counts[(doc, row["分類"])] += 1
            out.append(row)
    rec = {"purpose": "最終評価用 8 書類の確定ラベル(2 席 memoryless、同値類 v0 で集合一致した行だけ)",
           "seal": "docs/FINAL_EVAL_8_SEAL_2026-10-14.md",
           "sources_sha256": {doc: {"seat1": sha_file(os.path.join(BASE, "answers_seat1", "answer_%s.json" % doc)),
                                    "seat2": sha_file(os.path.join(BASE, "answers_seat2", "answer_%s.json" % doc))}
                              for doc in docs()},
           "counts": {"%s|%s" % k: v for k, v in sorted(counts.items())},
           "labels": out}
    p = os.path.join(BASE, "labels_final8_%s.json" % DATE)
    if os.path.exists(p):
        raise SystemExit("既に在る。上書きしない: %s" % p)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=1)
    print(json.dumps(rec["counts"], ensure_ascii=False, indent=1))
    print("labels ->", p, sha_file(p)[:16])


# ---------------------------------------------------------------- 段 2
def build_dumps():
    for doc in docs():
        key = json.load(io.open(os.path.join(BASE, "commander_only", "key_%s.json" % doc), encoding="utf-8"))
        for pn in PROFILES:
            run = _run(doc, _profile(pn))
            dump, missing = {}, 0
            for r in key["rows_map"]:
                v = run.get(r["claim_id"])
                if v is None:
                    missing += 1
                    continue
                dump["%s:%s" % (doc, r["行の鍵"])] = {kk: vv for kk, vv in v.items() if not kk.startswith("ckey")}
            p = os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (pn, doc))
            with io.open(p, "w", encoding="utf-8") as fh:
                json.dump(dump, fh, ensure_ascii=False, indent=1)
            print("%-6s %s rows %3d missing %2d" % (pn, doc, len(dump), missing))


# ---------------------------------------------------------------- 段 3
def _load_dump(pn, which):
    d = {}
    for doc in which:
        d.update(json.load(io.open(os.path.join(BASE, "commander_only", "dump_%s_%s.json" % (pn, doc)), encoding="utf-8")))
    return d


def _members(doc_contexts, cid):
    c = doc_contexts.get(cid) or {}
    return frozenset(local(m) for m in (c.get("members") or []))


def e2_member_rows(rows, contexts_by_doc):
    out = []
    for r in rows:
        if r["state"] != "GROUNDED" or r["strict"]:
            continue
        doc = r["id"].split(":", 1)[0]
        ctx = contexts_by_doc[doc]
        la = {GE.canon(e) for e, _ in r["arm"]}
        ll = {GE.canon(e) for e, _ in r["label"]}
        if la != ll:
            continue
        ma = {_members(ctx, c) for _, c in r["arm"]}
        ml = {_members(ctx, c) for _, c in r["label"]}
        if ma != ml:
            out.append({"id": r["id"], "arm": r["arm"], "label": r["label"]})
    return out


def u_absent_rows(labels_raw, dump_p20):
    out = []
    for row in labels_raw["labels"]:
        if row["分類"] != "判定不能(両側)":
            continue
        reasons = row.get("判定不能の理由") or [None, None]
        if not all(x == ABSENT for x in reasons):
            continue
        q = dump_p20.get(row["id"])
        if q and q["state"] == "GROUNDED":
            out.append({"id": row["id"], "pointers": q["pointers"]})
    return out


def score():
    grp = groups()
    A = [d for d in docs() if grp[d] == "A"]
    B = [d for d in docs() if grp[d] == "B"]
    lp = os.path.join(BASE, "labels_final8_%s.json" % DATE)
    labels = GE.load_labels(lp)
    labels_raw = json.load(io.open(lp, encoding="utf-8"))
    contexts_by_doc = {d: json.load(io.open(os.path.join(BASE, "seat", "contexts_%s.json" % d), encoding="utf-8"))
                       for d in docs()}

    def sub(which):
        return {i: v for i, v in labels.items() if i.split(":", 1)[0] in which}

    out = {"thresholds": THRESH, "k": len(B), "A": A, "B": B, "labels_sha256": sha_file(lp)}

    # Q1 / Q3 側: A 群は P16 で採点(P20 と同じはず。両方出す)
    for pn in PROFILES:
        rows = GE.score(_load_dump(pn, A), sub(A)) if A else []
        out["A_%s" % pn] = GE.summarize(rows)
        for d in A:
            out["A_%s" % pn][d] = GE.summarize(rows, lambda r, d=d: r["id"].startswith(d))
    mA = out["A_P16"]
    LA, GA = mA["L"], mA["G"] or 1
    rs = {"L_A": LA, "L_A_ok": LA >= L_A_MIN,
          "RS1": {"value": round(mA["E1_strict"] / (LA or 1), 4), "pass": mA["E1_strict"] / (LA or 1) >= THRESH["RS1_E1_over_L_min"]},
          "RS2": {"value": round(mA["E2_strict"] / GA, 4), "pass": mA["E2_strict"] / GA <= THRESH["RS2_E2_over_G_max"]},
          "RS3": {"value": round(mA["E3"] / (LA or 1), 4), "pass": mA["E3"] / (LA or 1) <= THRESH["RS3_E3_over_L_max"]}}
    rs["judgement"] = ("判定不能(L_A < %d)" % L_A_MIN) if not rs["L_A_ok"] else ("通過" if all(rs[x]["pass"] for x in ("RS1", "RS2", "RS3")) else "外れ")
    out["Q1"] = rs

    # Q2 側: B 群は P20 で採点
    if B:
        rowsB = GE.score(_load_dump("P20", B), sub(B))
        mB = GE.summarize(rowsB)
        for d in B:
            mB[d] = GE.summarize(rowsB, lambda r, d=d: r["id"].startswith(d))
        rowsB16 = GE.score(_load_dump("P16", B), sub(B))
        mB16 = GE.summarize(rowsB16)
        em = e2_member_rows(rowsB, contexts_by_doc)
        ua = u_absent_rows(labels_raw, _load_dump("P20", B))
        LB, GB = mB["L"], mB["G"] or 1
        n = {"L_B": LB, "L_B_ok": LB >= L_B_MIN,
             "N1": {"value": round(mB["E1_strict"] / (LB or 1), 4), "pass": mB["E1_strict"] / (LB or 1) >= THRESH["N1_E1_over_L_min"]},
             "N2": {"value": round(mB["E2_strict"] / GB, 4), "pass": mB["E2_strict"] / GB <= THRESH["N2_E2_over_G_max"]},
             "N3": {"E2_member": len(em), "U_absent": len(ua), "value": len(em) + len(ua),
                    "pass": (len(em) + len(ua)) <= THRESH["N3_max"], "rows": em + ua},
             "P16_on_B_grounded(構造上 0 のはず)": mB16["G"]}
        n["judgement_N1_N2"] = ("判定不能(L_B < %d)" % L_B_MIN) if not n["L_B_ok"] else ("通過" if n["N1"]["pass"] and n["N2"]["pass"] else "外れ")
        out["B_P20"], out["B_P16"], out["Q2"] = mB, mB16, n
    else:
        out["Q2"] = {"judgement": "測れない(k = 0)"}

    p = os.path.join(BASE, "commander_only", "score_report_%s.json" % DATE)
    with io.open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"k": out["k"], "Q1": out["Q1"], "Q2": {kk: vv for kk, vv in out["Q2"].items() if kk != "N3"} | ({"N3": {kk: vv for kk, vv in out["Q2"]["N3"].items() if kk != "rows"}} if "N3" in out["Q2"] else {})},
                     ensure_ascii=False, indent=1))
    print("report ->", p)


if __name__ == "__main__":
    {"rates": rates, "labels": build_labels, "dumps": build_dumps, "score": score}[sys.argv[1]]()
