# -*- coding: utf-8 -*-
"""便 TR3 の集計(封 §3)。記録は数だけ。

使い方: python3 -I tally_tr3.py <TR0 の根> <TR1 の根> <TR3 の根> <record.json の path>
言い過ぎの判定は TR1 の tally_tr1.same_as_material の写し(材料は TR0 の材料。誤りを入れていない)。
比べの TR1 の新しい資料は、誤りを入れた項目を参照しない数だけを数える(TR1 の言い過ぎの数え方と同じ)。
"""
import json
import os
import re
import sys

TR0, TR1, TR3, OUT = sys.argv[1:5]
NUMS = [str(i) for i in range(31, 42)]
KIND = {"31": "甲", "32": "乙", "33": "丙", "34": "甲", "35": "乙", "36": "丙", "37": "甲", "38": "乙", "39": "丙", "40": "甲", "41": "乙"}
SCALE = {"円": 1, "千円": 1000, "百万円": 1000000, "億円": 100000000}
STOCK = ("現金及び預金", "流動資産合計", "資産合計", "短期借入金", "長期借入金", "負債合計", "純資産合計", "期末の従業員数")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def periods(item):
    return ("当期末", "前期末") if item in STOCK else ("当期", "前期")


def decimals_of(s):
    m = re.search(r"\.(\d+)", s)
    return len(m.group(1)) if m else 0


def same_as_material(r, mat):
    """tally_tr1.same_as_material の写し。"""
    item = r.get("項目")
    if item is None:
        return False
    cur, pri = periods(item)
    v = {p: mat.get((item, p)) for p in (cur, pri, r.get("期"))}
    u = r["単位"]
    if u in ("人", "名"):
        return v.get(r["期"]) is not None and abs(r["値"]) == v[r["期"]]
    if r["種類"] == "single_value" and u in SCALE:
        return v.get(r["期"]) is not None and round(v[r["期"]] / SCALE[u]) == round(r["値"])
    if v[cur] is None or v[pri] is None:
        return False
    if r["種類"] == "difference" and u in SCALE:
        d = round((v[cur] - v[pri]) / SCALE[u])
        return d == round(abs(r["値"]) * (r.get("符号") or 1)) or (r.get("符号") is None and abs(d) == round(abs(r["値"])))
    if r["種類"] == "ratio_change" and v[pri]:
        k = decimals_of(r["字"])
        p = round((v[cur] - v[pri]) / abs(v[pri]) * 100, k)
        return p == round(abs(r["値"]) * (r.get("符号") or 1), k) or (r.get("符号") is None and abs(p) == round(abs(r["値"]), k))
    return False


def cls(r):
    if r["区分"] == "要確認":
        return "軽量確認" if r["info"].get("held") else "要修正・精査"
    return r["区分"]


def blank():
    return {"拾った数": 0, "確認済み": 0, "要修正・精査": 0, "軽量確認": 0, "人の判断が必要": 0, "点検していない": 0,
            "言い過ぎ": 0, "書く席の誤りの候補": 0, "数えた字": 0, "拾わなかった字": 0}


def main():
    g = {"資料": len(NUMS), "TR3": blank(), "種類ごと": {k: blank() for k in ("甲", "乙", "丙")}, "比べ: TR1 の新しい資料": blank()}
    for n in NUMS:
        mat = {(m["項目"], m["期"]): m["値"] for m in load(os.path.join(TR0, "mat", n + ".json"))["項目"]}
        for key, recs, miss in (("TR3", load(os.path.join(TR3, "check", n + ".json")), load(os.path.join(TR3, "miss", n + ".json"))),
                                ("比べ: TR1 の新しい資料", load(os.path.join(TR1, "check_A", n + ".json")), load(os.path.join(TR3, "miss_tr1", n + ".json")))):
            if key != "TR3":
                cor = {(c["項目"], c["期"]) for c in load(os.path.join(TR1, "corrupt", n + ".json"))}
                mat1 = {(m["項目"], m["期"]): m["値"] for m in load(os.path.join(TR1, "mat", n + ".json"))["項目"]}
            targets = [g[key]] + ([g["種類ごと"][KIND[n]]] if key == "TR3" else [])
            for t in targets:
                t["数えた字"] += miss["数えた字"]
                t["拾わなかった字"] += len(miss["拾わなかった"])
            for r in recs:
                c = cls(r)
                if key != "TR3" and r.get("項目") and (any((r["項目"], p) in cor for p in periods(r["項目"]))
                                                     if r["種類"] != "single_value" else (r["項目"], r["期"]) in cor):
                    continue
                for t in targets:
                    t["拾った数"] += 1
                    t[c] += 1
                    if c == "要修正・精査":
                        over = same_as_material(r, mat if key == "TR3" else mat1)
                        t["言い過ぎ"] += over
                        t["書く席の誤りの候補"] += not over
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
