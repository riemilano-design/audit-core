# -*- coding: utf-8 -*-
"""条件4: 規則 4 除外版(規則 1・3・5・6 のみ)の再測定。Golden 期待値は変更しない。"""
import json, os, sys
HERE = sys.argv[1]
sys.path.insert(0, HERE)
from tests.golden import _instrument as INST
from adapters.xbrl import vocabulary as V
from collections import Counter

ZIP = os.environ["AC_ZIP"]
def zb():
    with open(ZIP, "rb") as f:
        return f.read()

recipe_list, results_by_id, pointer_metas = INST.run_verification("S100Z4Q1", V.P7, zb)

LAB = json.load(open(os.environ["AC_LABELS"]))
ids60 = [r["id"] for r in LAB["rows"]]
verdict = {r["id"]: r["判定"] for r in LAB["rows"]}

def snap(i):
    r = results_by_id.get(i)
    if r is None: return None
    return {"state": r.state.value, "pointer": list(r.pointers), "reason": r.reason}

out = {i: snap(i) for i in ids60}
print("60 件:", dict(Counter(v["state"] for v in out.values())))
stop60 = [i for i, v in out.items() if v["state"] != "GROUNDED"]
print("停止:", len(stop60), stop60)
print("停止の理由別:", dict(Counter((out[i]["state"], out[i]["reason"]) for i in stop60)))
print()
for i in ("N219", "N289", "T023", "T038", "T086", "T087", "N021", "N138", "N264", "N137", "N143", "N192"):
    print("  %-5s %s" % (i, json.dumps(snap(i), ensure_ascii=False)))
print()
pop53 = "N003,N009,N011,N014,N021,N024,N026,N063,N066,N089,N105,N112,N130,N131,N137,N138,N143,N168,N170,N172,N174,N175,N178,N179,N181,N187,N191,N192,N193,N205,N214,N218,N241,N264,N267,N278,N282,N288,N291,N298,N303,T018,T026,T037,T044,T049,T066,T068,T070,T072,T092,T097,T102".split(",")
assert len(pop53) == 53
g53 = [i for i in pop53 if results_by_id.get(i) and results_by_id[i].state.value == "GROUNDED"]
s53 = [(i, results_by_id[i].state.value, results_by_id[i].reason) for i in pop53 if i not in g53]
print("53 件: GROUNDED", len(g53), "/ 停止", len(s53))
print("  停止:", s53)
json.dump({"60": out, "stop60": stop60, "53_grounded": g53, "53_stopped": s53,
           "special": {i: snap(i) for i in ("N219","N289","T023","T038","T086","T087","N021","N138","N264","N137","N143","N192")}},
          open(os.environ["AC_OUT"], "w"), ensure_ascii=False, indent=1)
