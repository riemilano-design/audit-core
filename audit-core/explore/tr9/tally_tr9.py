# -*- coding: utf-8 -*-
"""便 TR9 の数え(封 §3・§4)。数だけを record.json に書く。

使い方: python3 -I tally_tr9.py <TR9 の根> <record.json の行き先>
"""
import json
import os
import re
import sys

ROOT, OUT = sys.argv[1:3]
NUMS = ["51", "52", "53", "54", "55", "56"]
DUP = ["同じ見出しの列(手がかりあり)", "同じ見出しの列(手がかりなし)"]


def load(*p):
    with open(os.path.join(*p), encoding="utf-8") as f:
        return json.load(f)


def ok(st):
    return bool(st) and st["状態"] == "読めた" and not st["違う"]


m = load(ROOT, "out", "machine.json")
rec = {"A": {"読んだ file": 0, "止めた": 0, "式の数が TR8 のちょうど半分の社": 0,
             "式の数(TR8・TR9)": {n: [v["検算の式(TR8)"], v["検算の式(TR9)"]] for n, v in m.items()}},
       "B": {"TR8 の覚え方で止めた": 0, "TR9 の覚え方で 15 全部正しく読んだ": 0},
       "C": {"素材": 0, "TR9 で止めた": 0},
       "D": {k: {"案だけ 読まない": 0, "部分の読み 違う": 0, "2 本目 期2 全部正しい": 0, "2 本目 期3 全部正しい": 0} for k in DUP}}
for n, v in m.items():
    for st in v["A"].values():
        rec["A"]["読んだ file"] += 1
        rec["A"]["止めた"] += st["状態"] == "止める"
    rec["A"]["式の数が TR8 のちょうど半分の社"] += v["検算の式(TR8)"] == 2 * v["検算の式(TR9)"]
    rec["B"]["TR8 の覚え方で止めた"] += v["B"]["TR8 の覚え方"]["状態"] == "止める"
    rec["B"]["TR9 の覚え方で 15 全部正しく読んだ"] += ok(v["B"]["TR9 の覚え方"])
    for st in v["C"].values():
        rec["C"]["素材"] += 1
        rec["C"]["TR9 で止めた"] += st["状態"] == "止める"
    for k in DUP:
        d = v["D"][k]
        rec["D"][k]["案だけ 読まない"] += d["案だけ"] == "読まない"
        rec["D"][k]["部分の読み 違う"] += d["部分の読み"]["違う"]
        rec["D"][k]["2 本目 期2 全部正しい"] += ok(d["2 本目と決めた時"]["期2"])
        rec["D"][k]["2 本目 期3 全部正しい"] += ok(d["2 本目と決めた時"]["期3"])
e = {k: {"画面": 0, "2 本目を選んだ": 0, "ほかの何番目を選んだ": 0, "保留": 0, "決めが無いか形が合わない": 0,
         "期2 全部正しい": 0, "期3 全部正しい": 0} for k in DUP}
e["意味の変わる改名(第 54 社・使わない行)"] = {"画面": 0, "期2 全部正しい": 0, "気づきに H2 の形": 0}
for n in NUMS:
    p = os.path.join(ROOT, "out", "seat", n + ".json")
    if not os.path.exists(p):
        continue
    for kind, s in load(p).items():
        if kind in DUP:
            x = e[kind]
            x["画面"] += 1
            ks = [v.get("列の何番目") for v in s["決め"].values() if isinstance(v, dict) and "列の何番目" in v]
            x["2 本目を選んだ"] += ks == [2]
            x["ほかの何番目を選んだ"] += bool(ks) and ks != [2]
            x["保留"] += any(b.endswith("保留") for b in s["当てられなかった"])
            x["決めが無いか形が合わない"] += any(not b.endswith("保留") for b in s["当てられなかった"])
            x["期2 全部正しい"] += ok(s.get("期2"))
            x["期3 全部正しい"] += ok(s.get("期3"))
        else:
            x = e["意味の変わる改名(第 54 社・使わない行)"]
            x["画面"] += 1
            x["期2 全部正しい"] += ok(s.get("期2"))
            x["気づきに H2 の形"] += bool(re.search(r"影響.{0,10}(なし|無し)", str(s.get("気づき") or "")))
rec["E"] = e
rec["注"] = "数だけ。素材は作り物。"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print(json.dumps(rec, ensure_ascii=False, indent=1))
