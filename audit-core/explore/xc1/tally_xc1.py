# -*- coding: utf-8 -*-
u"""便 XC1 の数え: out/{dev,held}_{none,R1,R2,R1R2}.json → record.json。組の番号と数だけ(会社の名・コード・file の名は書かない)。"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict
KEYS = ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた", "使った文脈", "使った文脈の定義が元と同じ")
SETS = ("none", "R1", "R2", "R1R2")


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def load(side, s):
    return json.load(open(os.path.join(HERE, "out", "%s_%s.json" % (side, s)), encoding="utf-8"))


def total(rows):
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    for k in ("違う欄", "止めた理由", "規則で替えた", "規則で替えて一致", "規則で替えて黙って違う", "規則で替えて余計"):
        c = collections.Counter()
        for r in rows:
            c.update(r[k])
        t[k] = od(sorted(c.items(), key=lambda q: -q[1]))
    return t


def main():
    rec = od()
    T = {}
    for side in ("dev", "held"):
        T[side] = od((s, total(load(side, s))) for s in SETS)
        rec[u"集計 " + {"dev": u"作りの 23 組(訓練 3 + 判定の番号の小さい 20)", "held": u"判定の 40 組"}[side]] = T[side]
    # 規則なしの数が便 XC0 の記録と同じか(作りの確かめ)
    xc0 = json.load(open(os.path.join(HERE, "..", "xc0", "out", "train.json"), encoding="utf-8")) + json.load(open(os.path.join(HERE, "..", "xc0", "out", "judge.json"), encoding="utf-8"))
    nos = set(r[u"番号"] for r in load("held", "none"))
    base0 = od((k, sum(r[k] for r in xc0 if r[u"番号"] in nos)) for k in ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた"))
    same0 = all(base0[k] == T["held"]["none"][k] for k in base0)
    rec[u"判定の 40 組の規則なしの数が便 XC0 の記録と同じ"] = same0
    h = T["held"]
    D = h["none"]["答えの数の fact"]
    j = od()
    w0, w12 = h["none"]["黙って違う"], h["R1R2"]["黙って違う"]
    j["XC1-1"] = od([("予測", u"R1+R2 の黙って違うは規則なしの 55% 以下"), ("出た", pct(w12, w0))])
    j["XC1-1"]["判定"] = u"当たり" if j["XC1-1"]["出た"] <= 55 else u"外れ"
    du = pct(h["R1R2"]["一致"] - h["none"]["一致"], D)
    j["XC1-2"] = od([("予測", u"R1+R2 の一致は規則なしより 0 ポイント以上 2.0 ポイント以下ふえる"), ("出た", du)])
    j["XC1-2"]["判定"] = u"当たり" if 0 <= du <= 2.0 else u"外れ"
    j["XC1-3"] = od([("予測", u"R1+R2 の余計に置いたは置いた fact の 0.5% 以下"), ("出た", pct(h["R1R2"]["余計に置いた"], h["R1R2"]["置いた"]))])
    j["XC1-3"]["判定"] = u"当たり" if j["XC1-3"]["出た"] <= 0.5 else u"外れ"
    ds = pct(h["R1R2"]["止めた"] - h["none"]["止めた"], D)
    j["XC1-4"] = od([("予測", u"R1+R2 の止めたのふえ方は答えの fact の 1.5 ポイント以下"), ("出た", ds)])
    j["XC1-4"]["判定"] = u"当たり" if ds <= 1.5 else u"外れ"
    j["XC1-5"] = od([("予測", u"R1 だけ・R2 だけのどちらでも、黙って違うは規則なしより少ない"), ("出た", "%d・%d(規則なし %d)" % (h["R1"]["黙って違う"], h["R2"]["黙って違う"], w0))])
    j["XC1-5"]["判定"] = u"当たり" if h["R1"]["黙って違う"] < w0 and h["R2"]["黙って違う"] < w0 else u"外れ"
    j["XC1-6"] = od([("予測", u"R1+R2 の黙って違うは答えの fact の 1.2% 以下"), ("出た", pct(w12, D))])
    j["XC1-6"]["判定"] = u"当たり" if j["XC1-6"]["出た"] <= 1.2 else u"外れ"
    rec[u"予測の判定"] = j
    rec[u"組ごと(番号と数だけ)"] = od((side + "_" + s, load(side, s)) for side in ("dev", "held") for s in SETS)
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(od([("XC0 と同じ", same0), ("判定", j)]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
