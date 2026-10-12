# -*- coding: utf-8 -*-
"""条件1: N137・N143・N192 が止まらなかった実際の経路を特定する。
引数・分岐・候補集合を記録する。sys.argv[1] = audit-core の道。"""
import sys, json, os
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import vocabulary as V
from adapters.xbrl import recipes as R
from adapters.xbrl import instance as I

ZIP = os.environ["AC_ZIP"]
with open(ZIP, "rb") as f:
    zb = f.read()

WATCH = set("N137 N143 N192 N026 N063 N066 N130 N289 N219 N131 N170 N278".split())
rec = {}
_orig = R._direct_value_claim

def wrapped(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts):
    cid = claim.get("id")
    entry = None
    if cid in WATCH:
        scale = prec if unit == "円" else V.UNIT_SCALE[unit]
        unit_scale = 1.0 if unit == "円" else V.UNIT_SCALE[unit]
        target = sign * num * unit_scale
        is_diff = bool(R._MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
        def pool_of(want):
            p = I.facts_for(elems, facts, contexts, member, want_ctx=want) if want else I.facts_for(elems, facts, contexts, member)
            return [{"name": f["name"], "ctx": f["context"], "value": f["value"], "unit": f["unit"]}
                    for f in p if f["unit"] and f["unit"].upper().startswith("JPY")]
        all_pool = pool_of(None)
        cur_pool = pool_of("CurrentYear")
        pri_pool = pool_of("Prior1Year")
        hits = [(f["name"] + "@" + f["ctx"], V.match_value(f["value"], target, scale)) for f in all_pool]
        hits = [h for h in hits if h[1]]
        entry = {
            "id": cid, "reached_direct_value": True, "subj": subj, "elems": list(elems or []),
            "member": member, "unit": unit, "num": num, "sign": sign, "prec": prec,
            "scale": scale, "unit_scale": unit_scale, "target": target,
            "is_diff": is_diff,
            "after4": repr(s[b:b + 4]), "before25": repr(s[max(0, a - 25):a]),
            "pool_all_n": len(all_pool), "pool_cur_n": len(cur_pool), "pool_pri_n": len(pri_pool),
            "pool_cur": cur_pool, "pool_pri": pri_pool,
            "hits_on_all_pool": hits,
        }
    out = _orig(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts)
    if entry is not None:
        entry["claim_after"] = {k: claim.get(k) for k in ("form", "result", "pointer", "reason", "bound", "recomputed", "match", "value")}
        rec[cid] = entry
    return out

R._direct_value_claim = wrapped
num_claims, text_claims = R.build_raw_claims(zb, V.P7)
by = {c["id"]: c for c in num_claims}
for cid in sorted(WATCH):
    c = by.get(cid)
    if cid not in rec:
        rec[cid] = {"id": cid, "reached_direct_value": False,
                    "claim_final": {k: (c or {}).get(k) for k in ("form", "result", "pointer", "reason", "bound", "recomputed", "subject", "unit", "value")}}
    else:
        rec[cid]["claim_final"] = {k: (c or {}).get(k) for k in ("form", "result", "pointer", "reason", "bound", "recomputed", "subject", "unit", "value")}
print(json.dumps(rec, ensure_ascii=False, indent=1, default=str))
