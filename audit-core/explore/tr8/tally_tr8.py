# -*- coding: utf-8 -*-
"""便 TR8 の数え(封 §3・§4)。数だけを record.json に書く。

使い方: python3 -I tally_tr8.py <TR6 の根> <TR8 の根> <record.json の行き先>
"""
import json
import os
import re
import sys

TR6, ROOT, OUT = sys.argv[1:4]
NUMS = ["51", "52", "53", "54", "55", "56"]
HOLES = {"H1": r"列.{0,10}見出し.{0,10}(無|な)|見出し.{0,10}(無|な).{0,10}列", "H2": r"影響.{0,10}(なし|無し)",
         "H3": r"シート.{0,20}(残|在る|ある)", "H4": r"(前後の行|生の).{0,20}(出|見え|無|な)", "H5": r"(行|預金).{0,15}(見当たら|残って|残る)"}


def load(*p):
    with open(os.path.join(*p), encoding="utf-8") as f:
        return json.load(f)


def holes(root):
    c = {k: 0 for k in HOLES}
    for n in NUMS:
        p = os.path.join(root, "reply", n + ".json")
        if not os.path.exists(p):
            continue
        for v in (load(p).get("画面") or {}).values():
            t = str(v.get("気づき") or "")
            for k, rx in HOLES.items():
                c[k] += bool(re.search(rx, t))
    c["計"] = sum(c.values())
    return c


m = load(ROOT, "out", "machine.json")
a = {"読んだ file": 0, "S5・S6 で止めた": 0, "ほかで止めた": 0, "検算の式の最小": min(v["検算の式"] for v in m["A"].values())}
for n, v in m["A"].items():
    for st in [v["期1"], v["期2"]] + [x for k in v["確定し直した台帳"].values() for x in k.values()]:
        a["読んだ file"] += 1
        if st["状態"] == "止める":
            a["S5・S6 で止めた" if set(st["規則"]) <= {"S5", "S6"} else "ほかで止めた"] += 1
b = {}
for n, v in m["B"].items():
    for kind, x in v.items():
        k = b.setdefault(kind, {"file": 0})
        k["file"] += 1
        for name in ("TR2 の読み", "TR8 の読み", "TR6 の案だけ", "TR8 の案だけ"):
            if name in x:
                st = x[name]
                lab = st["状態"] if st["状態"] != "読めた" else ("読めた・全部正しい" if not st["違う"] else "読めた・黙って違う")
                k.setdefault(name, {})
                k[name][lab] = k[name].get(lab, 0) + 1
        for name in ("TR7 の部分の読み", "TR8 の部分の読み"):
            if name in x:
                k.setdefault(name, {"先に読んだ": 0, "違う": 0})
                k[name]["先に読んだ"] += x[name]["先に読んだ"]
                k[name]["違う"] += len(x[name]["違う"])
c = {"止め": 0, "期2 全部正しい": 0, "期3 止めずに全部正しい": 0, "期2 全部正しいのに期3 が止まるか違う": 0,
     "案から変えた(意味の変わる改名を除く)": 0, "案から変えた(意味の変わる改名)": 0, "形の誤り": 0}
for n in NUMS:
    p = os.path.join(ROOT, "out", "seat", n + ".json")
    if not os.path.exists(p):
        continue
    for kind, s in load(p).items():
        c["止め"] += 1
        ok2 = s["期2"]["状態"] == "読めた" and not s["期2"]["違う"]
        ok3 = s.get("期3", {}).get("状態") == "読めた" and not s.get("期3", {}).get("違う")
        c["期2 全部正しい"] += ok2
        c["期3 止めずに全部正しい"] += ok3
        c["期2 全部正しいのに期3 が止まるか違う"] += ok2 and not ok3
        c["案から変えた(意味の変わる改名)" if kind == "意味の変わる改名" else "案から変えた(意味の変わる改名を除く)"] += s["案から変えた"]
        c["形の誤り"] += len(s["形の誤り"])
c["気づきの穴の形(TR8 の席)"] = holes(ROOT)
c["気づきの穴の形(TR6 の席・同じ数え方)"] = holes(TR6)
rec = {"A 止めすぎ": a, "B 新しい穴": b, "C 画面": c, "注": "数だけ。素材は作り物。"}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print(json.dumps(rec, ensure_ascii=False, indent=1))
