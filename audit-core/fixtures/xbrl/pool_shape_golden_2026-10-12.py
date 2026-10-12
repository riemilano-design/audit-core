# -*- coding: utf-8 -*-
import json, os, sys
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V
from adapters.xbrl import instance as I
from tests.adapters.xbrl import _material as M

def collapse(pool):
    seen = {}
    for f in pool:
        l = f["name"].split(":")[-1]
        base = l[:-len("SummaryOfBusinessResults")] if l.endswith("SummaryOfBusinessResults") else l
        base = base.replace("IncomeLoss", "Income")
        seen.setdefault((base, f["context"], f["value"]), []).append(f)
    return seen

def run(tag, zb, profile):
    rec = {}
    _orig = R._direct_value_claim
    def wrapped(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts):
        cid = claim.get("id")
        is_diff = bool(R._MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
        prev = R._PREV_YEAR_PHRASE in s[max(0, a - 15):a]
        if is_diff:
            wa, wb = ("Prior1Year", "Prior2Year") if prev else ("CurrentYear", "Prior1Year")
        else:
            wa, wb = "CurrentYear", None
        def pool_of(w):
            return [f for f in I.facts_for(elems, facts, contexts, member, want_ctx=w)
                    if f["unit"] and f["unit"].upper().startswith("JPY")]
        out = _orig(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts)
        if claim.get("reason") == "ambiguous(elements)" and subj:
            pa, pb = pool_of(wa), (pool_of(wb) if wb else None)
            na = len(collapse(pa)); nb = len(collapse(pb)) if pb else None
            rec[cid] = {"recover": bool(na == 1 and nb in (None, 1)), "subj": subj, "elems": list(elems or []),
                        "a": [(f["name"].split(":")[-1], f["value"]) for f in pa]}
        return out
    R._direct_value_claim = wrapped
    R.build_raw_claims(zb, profile)
    R._direct_value_claim = _orig
    rec_rec = sorted(i for i, e in rec.items() if e["recover"])
    rec_stay = sorted(i for i, e in rec.items() if not e["recover"])
    print("%s: 規則4で停止 %d 件 / 畳んで回復 %d / 停止のまま %d" % (tag, len(rec), len(rec_rec), len(rec_stay)))
    print("    回復:", rec_rec)
    print("    停止のまま:", rec_stay)
    for i in rec_stay:
        same_val = len({v for _, v in rec[i]["a"]}) == 1
        print("      %-6s 値が同じ=%-5s %s" % (i, same_val, rec[i]["a"][:4]))
    return {"recover": rec_rec, "stay": rec_stay, "rec": rec}

out = {}
out["1B"] = run("1B(P1)", M.load_zip_bytes(M.DOC_1["docID"], M.DOC_1["sha256"]), V.P1)
out["5F"] = run("5F(P5F)", M.load_zip_bytes(M.DOC_5["docID"], M.DOC_5["sha256"]), V.P5F)
json.dump(out, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1)
