# -*- coding: utf-8 -*-
"""便 TR10 の数え(封 §3)。数だけを record.json に書く。

使い方: python3 -I tally_tr10.py <TR10 の根> <record.json の行き先>
"""
import glob
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1:3]
CODES = re.compile(r"\bS\d+\b|R1|R2|GROUNDED|UNPROVABLE|VALUE_MISMATCH")
t = {"区分": {"確認済み": 0, "要修正・精査": 0, "点検していない": 0}, "札": 0, "拾った数": 0, "札の付かない数": 0, "資料に見つからない札": 0,
     "言い過ぎ": 0, "確認済みで元の升を欠く": 0, "台帳に無い項目と期": 0, "誤り": {}, "点検レポートの社内の符号": 0}
for f in sorted(glob.glob(os.path.join(ROOT, "out", "[0-9]*.json"))):
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in t["区分"]:
        t["区分"][k] += d["区分"][k]
    for k in ("札", "札の付かない数", "資料に見つからない札", "言い過ぎ", "確認済みで元の升を欠く"):
        t[k] += d[k]
    t["拾った数"] += sum(d["区分"].values()) - d["資料に見つからない札"]
    t["台帳に無い項目と期"] += sum(r["訳"] == "台帳にこの項目・期が無い" for r in d["点検していない行"])
    for k, v in d["誤り"].items():
        x = t["誤り"].setdefault(k, [0, 0])
        x[0] += len(v)
        x[1] += sum(y["止めた"] for y in v)
    b = t["誤り"].setdefault("b の場所", {})
    for y in d["誤り"]["b"]:
        z = b.setdefault(y["場所"], [0, 0])
        z[0] += 1
        z[1] += y["止めた"]
for f in sorted(glob.glob(os.path.join(ROOT, "report", "*.html"))):
    with open(f, encoding="utf-8") as fh:
        t["点検レポートの社内の符号"] += len(CODES.findall(re.sub(r"<style.*?</style>", "", fh.read(), flags=re.S)))
xp = os.path.join(ROOT, "out", "extra.json")
if os.path.exists(xp):  # 結果の後の補足(extra_tr10.py)
    with open(xp, encoding="utf-8") as fh:
        t["補足(結果の後)"] = json.load(fh)
t["注"] = "[入れた, 止めた] の対。数だけ。素材は作り物の 6 社。"
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(t, fh, ensure_ascii=False, indent=1)
print(json.dumps(t, ensure_ascii=False, indent=1))
