# -*- coding: utf-8 -*-
"""便 TR5 の数え(封 §4)。check_tr5.py の出力 <TR5>/out から数だけを record.json に書く。

使い方: python3 -I tally_tr5.py <TR5 の根> <record.json の行き先>
"""
import glob
import json
import os
import sys

TR5, OUT = sys.argv[1:3]
KS = ("確認済み", "要修正・精査", "軽量確認", "点検していない")


def tally(name):
    t = {"区分": {k: 0 for k in KS}, "R1 で止めた": 0, "R2 で止めた": 0, "言い過ぎ": 0, "札": 0,
         "(b) 期の隠し": {"文": [0, 0], "表": [0, 0]}, "(d) 項目の隠し": [0, 0], "(a′) 数と札の字": [0, 0]}
    for f in sorted(glob.glob(os.path.join(TR5, "out", name, "*.json"))):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        for k in KS:
            t["区分"][k] += d["区分"][k]
        t["R1 で止めた"] += d["R1"]
        t["R2 で止めた"] += d["R2"]
        t["言い過ぎ"] += d["言い過ぎ"]
        t["札"] += d["札"]
        for x in d["誤り"]["b"]:
            t["(b) 期の隠し"][x["場所"]][0] += 1
            t["(b) 期の隠し"][x["場所"]][1] += x["止めた"]
        for key, k2 in (("d", "(d) 項目の隠し"), ("a2", "(a′) 数と札の字")):
            t[k2][0] += len(d["誤り"][key])
            t[k2][1] += sum(x["止めた"] for x in d["誤り"][key])
    t["(b) 期の隠し"]["計"] = [sum(v[i] for v in t["(b) 期の隠し"].values()) for i in (0, 1)]
    return t


rec = {"新しい資料": tally("新しい"), "TR4 の資料": tally("TR4")}
with open(os.path.join(TR5, "out", "regress.json"), encoding="utf-8") as fh:
    g = json.load(fh)
rec["回帰"] = {"判定し直した": g["TR3 の要修正・精査"] + g["TR0 の要確認"],
              "正しい数とした": g["そのうち本文の単位で正しい数"] + g["そのうち本文の単位で正しい数(TR0)"]}
xb = os.path.join(TR5, "out", "extra_b.json")
if os.path.exists(xb):  # 結果の後の補足(extra_b_tr5.py)
    with open(xb, encoding="utf-8") as fh:
        rec["補足(結果の後)"] = json.load(fh)
rec["注"] = "[入れた, 止めた] の対。数だけ。会社・項目・値は書かない。"
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(rec, fh, ensure_ascii=False, indent=1)
print(json.dumps(rec, ensure_ascii=False, indent=1))
