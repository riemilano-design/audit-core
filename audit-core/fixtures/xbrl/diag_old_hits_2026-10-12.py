# -*- coding: utf-8 -*-
"""条件3: 旧コードの暗黙選択(hits[0])を 60 件で測る。
各 Claim について、値が一致した候補 fact の件数(= hits の長さ)と、
その中で hits[0] が選ばれた事実、独立監査の判定を並べる。"""
import sys, json, os
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import vocabulary as V
from adapters.xbrl import recipes as R
from adapters.xbrl import instance as I

ZIP = os.environ["AC_ZIP"]
with open(ZIP, "rb") as f:
    zb = f.read()

LAB = json.load(open(os.environ["AC_LABELS"]))
verdict = {r["id"]: r["判定"] for r in LAB["rows"]}
IDS60 = [r["id"] for r in LAB["rows"]]

rec = {}
_orig = R._direct_value_claim

def wrapped(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts):
    cid = claim.get("id")
    scale = prec if unit == "円" else V.UNIT_SCALE[unit]
    unit_scale = 1.0 if unit == "円" else V.UNIT_SCALE[unit]
    target = sign * num * unit_scale
    pool = I.facts_for(elems, facts, contexts, member) if subj else [f for f in facts if I.ctx_ok(f["context"], contexts, member)]
    pool = [f for f in pool if f["unit"] and f["unit"].upper().startswith("JPY")]
    is_diff = bool(R._MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
    hits = [(f, V.match_value(f["value"], target, scale)) for f in pool]
    hits = [(f, how) for f, how in hits if how]
    names = ["%s@%s" % (f["name"], f["context"]) for f, _ in hits]
    out = _orig(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts)
    rec[cid] = {
        "subj": subj, "is_diff": is_diff, "pool_n": len(pool), "hits_n": len(hits),
        "hits": names, "hits_distinct_elements": len(sorted({f["name"] for f, _ in hits})),
        "chose_hits0": bool(hits) and not (is_diff and subj) and bool(subj),
        "result": claim.get("result"), "pointer": claim.get("pointer"), "reason": claim.get("reason"),
        "form": claim.get("form"),
    }
    return out

R._direct_value_claim = wrapped
num_claims, text_claims = R.build_raw_claims(zb, V.P7)
by = {c["id"]: c for c in num_claims}
res = {}
for cid in IDS60:
    e = dict(rec.get(cid) or {"reached_direct_value": False})
    e["verdict"] = verdict[cid]
    c = by.get(cid)
    if c is not None:
        e["final_result"] = c.get("result"); e["final_pointer"] = c.get("pointer"); e["final_form"] = c.get("form")
    res[cid] = e
json.dump(res, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1, default=str)

# 集計
from collections import Counter
multi = [i for i, e in res.items() if e.get("chose_hits0") and e.get("hits_n", 0) >= 2]
multi_elem = [i for i, e in res.items() if e.get("chose_hits0") and e.get("hits_distinct_elements", 0) >= 2]
print("60 件中、_direct_value_claim に届いた:", sum(1 for e in res.values() if "hits_n" in e))
print("hits[0] で束縛した(subj かつ hits あり かつ not is_diff):", sum(1 for e in res.values() if e.get("chose_hits0")))
print("うち候補が 2 件以上(fact の数):", len(multi))
print("うち候補の要素名が 2 種類以上:", len(multi_elem))
print()
print("候補 2 件以上で hits[0] が選ばれた件の判定:", dict(Counter(res[i]["verdict"] for i in multi)))
print("  id:", multi)
print("要素名 2 種以上:", dict(Counter(res[i]["verdict"] for i in multi_elem)), multi_elem)
print()
print("全 60 件の判定:", dict(Counter(e["verdict"] for e in res.values())))
