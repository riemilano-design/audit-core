# -*- coding: utf-8 -*-
"""Golden 期待値との差を id 単位で数え、原因で分類する。期待値は読むだけ。"""
import json, os, sys
HERE = sys.argv[1]
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tests", "adapters", "xbrl"))
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V
from tests.adapters.xbrl import test_claim_layer as T
from tests.adapters.xbrl import _material as M

def run(tag, doc, profile, exp_name):
    zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
    recipe_list = R.build_recipes(zb, profile)
    actual = {r.claim.id: r for r in recipe_list}
    expectation = T._load_expectation(exp_name)
    changed = {}
    for row in expectation["claims"]:
        rid = row["id"]
        if rid not in actual:
            changed[rid] = ["MISSING"]; continue
        e = T._expected_fields(row); a = T._actual_fields(actual[rid])
        diff = [f for f in T._COMPARED_FIELDS if e[f] != a[f]]
        if diff:
            changed[rid] = {"fields": diff,
                            "exp_form": e["form"], "act_form": a["form"],
                            "exp_tr": e["time_range"], "act_tr": a["time_range"],
                            "exp_ptr": e["pointers"], "act_ptr": a["pointers"]}
    return changed

out = {}
for tag, doc, prof, exp in (("1B", M.DOC_1, V.P1, "core_expectation_1B.json"),
                            ("5F", M.DOC_5, V.P5F, "core_expectation_5F.json")):
    ch = run(tag, doc, prof, exp)
    out[tag] = ch
    # 原因で分類
    def cause(d):
        if d == ["MISSING"]: return "MISSING"
        if not d["act_ptr"]: return "候補0件→停止(規則3)"
        if d["exp_form"] == "derived_value" and d["act_form"] == "direct_value": return "対の形→単一fact(値での再探索の禁止)"
        if d["exp_form"] == "direct_value" and d["act_form"] == "derived_value": return "単一fact→対の形(is_diff)"
        ep = set(p.split("@")[-1] for p in d["exp_ptr"] if "@" in p)
        ap = set(p.split("@")[-1] for p in d["act_ptr"] if "@" in p)
        ee = set(p.split("@")[0] for p in d["exp_ptr"] if "@" in p)
        ae = set(p.split("@")[0] for p in d["act_ptr"] if "@" in p)
        if ee != ae: return "別の要素に束縛(概念)"
        if ep != ap: return "別の期間に束縛(期間の既定値)"
        return "その他(欄だけの差)"
    from collections import Counter
    cc = Counter(cause(v) for v in ch.values())
    print("%s: 変わった id %d 件" % (tag, len(ch)))
    for k, n in cc.most_common():
        ids = sorted(i for i, v in ch.items() if cause(v) == k)
        print("   %-34s %2d  %s" % (k, n, ",".join(ids)))
json.dump(out, open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1, default=str)
