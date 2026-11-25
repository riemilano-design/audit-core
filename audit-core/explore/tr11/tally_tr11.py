# -*- coding: utf-8 -*-
"""便 TR11 の数え(封 §3)。数だけを record.json に書く。使い方: python3 -I tally_tr11.py <TR11 の根> <record.json の行き先>"""
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1:3]
NUMS = ["51", "52", "53", "54", "55", "56"]


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


rec = {"社ごと": {}, "計": {"止めた": 0, "先に読んだ": 0, "先に読んで違う": 0, "決めた所": 0, "読み直しで全部正しい社": 0,
                            "確認済み": 0, "要修正・精査": 0, "点検していない": 0, "札": 0, "札の付かない数": 0, "言い過ぎ": 0,
                            "元の升を欠く": 0, "引く升": 0, "引く升の印": 0, "誤り": {}}}
t = rec["計"]
for n in NUMS:
    s, r, c = load("out", "stop", n + ".json"), load("out", "reread", n + ".json"), load("out", "check", n + ".json")
    rec["社ごと"][n] = {"決めた所": r["決めた所"], "読み直し": r.get("読み直し"), "違う": r.get("違う"), "引く升": c["引く升"], "引く升の印": c["引く升の印"]}
    t["止めた"] += s["止めた"]
    t["先に読んだ"] += s["先に読んだ"]
    t["先に読んで違う"] += s["先に読んで違う"]
    t["決めた所"] += r["決めた所"]
    t["読み直しで全部正しい社"] += r.get("読み直し") == "読めた" and not r.get("違う")
    for k in ("確認済み", "要修正・精査", "点検していない"):
        t[k] += c["区分"][k]
    for k in ("札", "札の付かない数", "言い過ぎ", "引く升", "引く升の印"):
        t[k] += c[k]
    t["元の升を欠く"] += c["確認済みで元の升を欠く"]
    for k, (a, b) in c["誤り"].items():
        x = t["誤り"].setdefault(k, [0, 0])
        x[0] += a
        x[1] += b
r56 = load("out", "reread", "56.json")
rec["第 56 社の気づきに分かりにくいの形"] = bool(re.search(r"つながり|結びつき|分かりにく|気づきにく|別の所", str(r56.get("気づき") or "")))
rec["注"] = "数だけ。素材は作り物の 6 社。誤りは [入れた, 止めた]。"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print(json.dumps(rec, ensure_ascii=False, indent=1))
