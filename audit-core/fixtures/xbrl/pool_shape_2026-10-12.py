# -*- coding: utf-8 -*-
"""規則 4 で停止した Claim の候補集合の形を測る(実装はしない。構造だけ)。"""
import json, os, sys
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V
from adapters.xbrl import instance as I

ZIP = os.environ["AC_ZIP"]
zb = open(ZIP, "rb").read()
rec = {}
_orig = R._direct_value_claim
def wrapped(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts):
    cid = claim.get("id")
    is_diff = bool(R._MONEY_UNIT_RE_AFTER.search(s[b:b + 4])) or bool(R._MONEY_DIFF_PHRASE_RE.search(s[max(0, a - 25):a]))
    prev = R._PREV_YEAR_PHRASE in s[max(0, a - 15):a]
    def pool_of(want):
        return [{"name": f["name"], "ctx": f["context"], "value": f["value"]}
                for f in I.facts_for(elems, facts, contexts, member, want_ctx=want)
                if f["unit"] and f["unit"].upper().startswith("JPY")]
    if is_diff:
        wa, wb = ("Prior1Year", "Prior2Year") if prev else ("CurrentYear", "Prior1Year")
    else:
        wa, wb = "CurrentYear", None
    out = _orig(claim, s, a, b, sign, num, unit, prec, subj, elems, member, facts, contexts)
    if claim.get("reason") == "ambiguous(elements)" and subj:
        rec[cid] = {"subj": subj, "elems": list(elems or []), "is_diff": is_diff,
                    "want_a": wa, "want_b": wb,
                    "pool_a": pool_of(wa), "pool_b": pool_of(wb) if wb else None,
                    "ambiguous_count": claim.get("ambiguous_count")}
    return out
R._direct_value_claim = wrapped
num, text = R.build_raw_claims(zb, V.P7)

LAB = json.load(open(os.environ["AC_LABELS"]))
ids60 = set(r["id"] for r in LAB["rows"])

def collapse(pool):
    """(ア)別名対 + (イ)同じ要素の重複 を畳んだときの候補数。"""
    seen = {}
    for f in pool:
        l = f["name"].split(":")[-1]
        base = l[:-len("SummaryOfBusinessResults")] if l.endswith("SummaryOfBusinessResults") else l
        base = base.replace("IncomeLoss", "Income")
        key = (base, f["ctx"], f["value"])
        seen.setdefault(key, []).append(f)
    return seen

print("規則 4(ambiguous)で停止した Claim: %d 件(うち封の 60 件に在る: %d)" % (len(rec), len(set(rec) & ids60)))
pred_recover, pred_stay = [], []
for cid in sorted(rec):
    e = rec[cid]
    ca = collapse(e["pool_a"]); cb = collapse(e["pool_b"]) if e["pool_b"] else None
    na, nb = len(ca), (len(cb) if cb else None)
    mark = "回復" if (na == 1 and (nb in (None, 1))) else "停止のまま"
    (pred_recover if mark == "回復" else pred_stay).append(cid)
    inset = "★" if cid in ids60 else " "
    print("%s%-6s %-5s a:%d→%d  b:%s  %s" % (inset, cid, e["is_diff"], len(e["pool_a"]), na,
          ("%d→%d" % (len(e["pool_b"]), nb)) if cb else "-", mark))
    if mark != "回復":
        for k, v in ca.items():
            print("        a群 %-46s %d 件 %s" % (str(k[0])[:46], len(v), sorted({f["name"] for f in v})))
print()
print("畳んだら候補 1 件になる(=回復すると予測):", len(pred_recover), pred_recover)
print("畳んでも複数のまま(=停止が残ると予測):", len(pred_stay), pred_stay)
print("封の 60 件のうち 回復:", sorted(set(pred_recover) & ids60), " 停止のまま:", sorted(set(pred_stay) & ids60))
json.dump({"rec": rec, "recover": pred_recover, "stay": pred_stay}, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1)
