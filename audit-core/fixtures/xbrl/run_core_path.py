# -*- coding: utf-8 -*-
"""1 書類を Adapter + Core(verify_all)で回し、Claim の層と結果の層と集計を 1 本の JSON に書く計測 script。Core のコードではない。
使う前の門: S100Z4Q1(P1)と S100Z4B6(P5F)で core_expectation_{1B,5F}.json と state・pointers・recomputed が全件一致すること(--gate)。
  python3 fixtures/xbrl/run_core_path.py --doc S100Z4B6 --profile P5F --out <path> [--zip-sha256 <sha>] [--gate fixtures/xbrl/core_expectation_5F.json]
通信はしない(ZIP は ~/.cache/audit-core/edinet/ から)。
"""
import argparse, collections, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "core", "py"))
import audit_core as core
from adapters.xbrl import edinet as E, instance as I, recipes as R, resolve as RV, registry_setup as RS, vocabulary as V


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True); ap.add_argument("--profile", required=True, choices=sorted(V.PROFILES.keys()))
    ap.add_argument("--out", required=True); ap.add_argument("--zip-sha256", default=None); ap.add_argument("--gate", default=None)
    a = ap.parse_args(argv)
    path = E.cache_path(a.doc)
    zb = open(path, "rb").read()
    sha = hashlib.sha256(zb).hexdigest()
    if a.zip_sha256 and sha != a.zip_sha256:
        print("ZIP sha mismatch", sha); return 4
    inst = I.load_instance(zb)
    recipes = list(R.build_recipes(zb, V.PROFILES[a.profile]))
    resolver = RV.make_resolver(inst["facts"])
    registry = RS.register_all(core.Registry.default())
    results = core.verify_all(recipes, resolver, registry)
    rows = []
    for rc, rs in zip(recipes, results):
        c = rc.claim
        rows.append({"id": c.id, "form": c.form.value, "subject": c.subject, "value": c.value, "unit": c.unit,
                     "modifiers": {"population": c.modifiers.population, "time_range": list(c.modifiers.time_range), "normalization": c.modifiers.normalization},
                     "pointers": list(rs.pointers), "comparator": rs.comparator,
                     "state": rs.state.value, "recomputed": rs.recomputed, "reason": rs.reason,
                     "provenance": {k: v for k, v in c.provenance.items() if k in ("sentence", "span", "word", "sign_token", "member_source", "ambiguous_count", "value_only", "diff_phrase_direct", "kind")}})
    C = collections.Counter
    num = [r for r in rows if r["provenance"].get("kind") == "num"]; txt = [r for r in rows if r["provenance"].get("kind") == "text"]
    bound = lambda rs_: [r for r in rs_ if r["pointers"]]
    tall = {"claims": len(rows), "num": len(num), "text": len(txt), "num_bound": len(bound(num)), "text_bound": len(bound(txt)),
            "state": dict(C(r["state"] for r in rows)), "state_num": dict(C(r["state"] for r in num)), "state_text": dict(C(r["state"] for r in txt)),
            "form": dict(C(r["form"] for r in rows)), "reason": dict(C(r["reason"] for r in rows if r["reason"])),
            "comparator": dict(C(r["comparator"] for r in rows if r["comparator"])), "normalization": dict(C(r["modifiers"]["normalization"] for r in rows if r["modifiers"]["normalization"])),
            "population": dict(C((r["modifiers"]["population"] or "none").split(":")[0] for r in rows)),
            "subjects_unbound_no_subject": len([r for r in rows if r["reason"] == "no_subject"]),
            "sign_token_claims": len([r for r in rows if r["provenance"].get("sign_token")]),
            "member_source": dict(C(r["provenance"].get("member_source") for r in rows if r["provenance"].get("member_source"))),
            "ambiguous_count": dict(C(r["provenance"].get("ambiguous_count") for r in rows if r["provenance"].get("ambiguous_count"))),
            "mdna_sentences": None}
    out = {"tool": "run_core_path", "doc": a.doc, "profile": a.profile, "zip_sha256": sha, "facts_total": len(inst["facts"]), "contexts_total": len(inst["contexts"]),
           "registry": {"comparators": 6, "schemes": 3, "normalizations": 4, "reasons": 9}, "tally": tall, "claims": rows}
    gate = None
    if a.gate:
        exp = json.load(open(a.gate, encoding="utf-8"))["claims"]
        by = {r["id"]: r for r in rows}
        diffs = []
        for e in exp:
            r = by.get(e["id"])
            if r is None: diffs.append((e["id"], "missing")); continue
            if r["state"] != e["result"]["state"]: diffs.append((e["id"], "state", e["result"]["state"], r["state"]))
            if r["pointers"] != e["evidence"]["pointers"]: diffs.append((e["id"], "pointers"))
            if r["recomputed"] != e["result"]["recomputed"]: diffs.append((e["id"], "recomputed", e["result"]["recomputed"], r["recomputed"]))
        gate = {"expectation": os.path.basename(a.gate), "expected": len(exp), "actual": len(rows), "diffs": diffs}
        out["gate"] = gate
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"doc": a.doc, "profile": a.profile, "tally": {k: tall[k] for k in ("claims", "num", "text", "num_bound", "text_bound", "state", "reason")}, "gate": gate}, ensure_ascii=False, indent=1))
    print("written:", a.out)
    return 0 if (gate is None or not gate["diffs"]) else 5


if __name__ == "__main__":
    sys.exit(main())
