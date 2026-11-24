# -*- coding: utf-8 -*-
"""便 TR6 の数え(封 §4)。run_tr6.py の出力 <TR6>/out から数だけを record.json に書く。

使い方: python3 -I tally_tr6.py <TR6 の根> <record.json の行き先>
"""
import json
import os
import sys

ROOT, OUT = sys.argv[1:3]
NUMS = [51, 52, 53, 54, 55, 56]
TR2_KINDS = ["列の挿入", "行の並べ替え", "シート名の変更", "行の見出しの微修正", "列の見出しの微修正", "科目の追加", "単位の変更"]
KINDS = TR2_KINDS + ["意味の変わる改名", "紛れの科目の追加"]


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        return json.load(f)


rec = {"種類ごと": {}}
tot = {"止めた": 0, "TR2 の形の行": 0, "縮めた行": 0, "縮めた行の最大": 0, "TR2 の 7 種の TR2 の形の行": 0, "TR2 の 7 種の縮めた行": 0,
       "案だけ 読めた・全部正しい": 0, "案だけ 読めた・黙って違う": 0, "案だけ 止める": 0, "案だけ 台帳が作れない": 0,
       "席の後 期2 全部正しい": 0, "席の後 期3 止めずに全部正しい": 0, "期2 全部正しいのに期3 が止まるか違う": 0,
       "案から変えた(意味の変わる改名を除く)": 0, "形の誤り": 0}
for kind in KINDS:
    k = {"止め": 0, "止めた": 0, "TR2 の形の行": 0, "縮めた行": 0, "案だけ": {}, "席の後 期2 全部正しい": 0, "席の後 期3 止めずに全部正しい": 0,
         "案から変えた": 0, "形の誤り": 0, "現金及び預金を正しく": 0, "短期借入金を正しく": 0}
    for n in NUMS:
        p = load("out", "prep", "%d.json" % n)[kind]
        s = load("out", "seat", "%d.json" % n)[kind] if os.path.exists(os.path.join(ROOT, "out", "seat", "%d.json" % n)) else None
        k["止め"] += 1
        k["止めた"] += p["止めた"]
        k["TR2 の形の行"] += p["TR2 の形の行"]
        k["縮めた行"] += p["縮めた行"]
        tot["縮めた行の最大"] = max(tot["縮めた行の最大"], p["縮めた行"])
        a = p["案だけ"]
        lab = a["状態"] if a["状態"] != "読めた" else ("読めた・全部正しい" if not a["違う"] else "読めた・黙って違う")
        k["案だけ"][lab] = k["案だけ"].get(lab, 0) + 1
        if s is None:
            continue
        ok2 = s["期2"]["状態"] == "読めた" and not s["期2"]["違う"]
        ok3 = s.get("期3", {}).get("状態") == "読めた" and not s.get("期3", {}).get("違う")
        k["席の後 期2 全部正しい"] += ok2
        k["席の後 期3 止めずに全部正しい"] += ok3
        tot["期2 全部正しいのに期3 が止まるか違う"] += ok2 and not ok3
        k["案から変えた"] += s["案から変えた"]
        k["形の誤り"] += len(s["形の誤り"])
        if s["期2"]["状態"] == "読めた":
            k["現金及び預金を正しく"] += "現金及び預金@当期末" not in s["期2"]["違う"]
            k["短期借入金を正しく"] += "短期借入金@当期末" not in s["期2"]["違う"]
    rec["種類ごと"][kind] = k
    tot["止めた"] += k["止めた"]
    tot["TR2 の形の行"] += k["TR2 の形の行"]
    tot["縮めた行"] += k["縮めた行"]
    if kind in TR2_KINDS:
        tot["TR2 の 7 種の TR2 の形の行"] += k["TR2 の形の行"]
        tot["TR2 の 7 種の縮めた行"] += k["縮めた行"]
    for lab, v in k["案だけ"].items():
        tot["案だけ " + lab] += v
    tot["席の後 期2 全部正しい"] += k["席の後 期2 全部正しい"]
    tot["席の後 期3 止めずに全部正しい"] += k["席の後 期3 止めずに全部正しい"]
    if kind != "意味の変わる改名":
        tot["案から変えた(意味の変わる改名を除く)"] += k["案から変えた"]
    tot["形の誤り"] += k["形の誤り"]
rec["計"] = tot
xp = os.path.join(ROOT, "out", "extra.json")
if os.path.exists(xp):  # 結果の後の補足(extra_tr6.py)
    rec["補足(結果の後)"] = load("out", "extra.json")
rec["注"] = "数だけ。素材は作り物の 6 社 × 9 種 = 54 の止め。"
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(rec, f, ensure_ascii=False, indent=1)
print(json.dumps(rec["計"], ensure_ascii=False, indent=1))
