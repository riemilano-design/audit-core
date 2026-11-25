# -*- coding: utf-8 -*-
u"""便 XC2 の数え: out/{dev,held}_{none,R3,R4,R3R4}.json → record.json。組の番号と数だけ。"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict
KEYS = ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた", "規則で替えて一致", "規則で替えて黙って違う", "規則で替えて余計",
        "使った文脈", "使った文脈の定義が元と同じ")
SETS = ("none", "R3", "R4", "R3R4")


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def load(side, s):
    return json.load(open(os.path.join(HERE, "out", "%s_%s.json" % (side, s)), encoding="utf-8"))


def total(rows):
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    for k in ("違う欄", "止めた理由"):
        c = collections.Counter()
        for r in rows:
            c.update(r[k])
        t[k] = od(sorted(c.items(), key=lambda q: -q[1]))
    return t


def main():
    rec = od()
    T = {}
    for side, label in (("dev", u"作りの 23 組"), ("held", u"判定の 40 組")):
        T[side] = od((s, total(load(side, s))) for s in SETS)
        rec[u"集計 " + label] = T[side]
    x1 = json.load(open(os.path.join(HERE, "..", "xc1", "out", "held_R1R2.json"), encoding="utf-8"))
    base1 = od((k, sum(r[k] for r in x1)) for k in ("答えの数の fact", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた"))
    same1 = all(base1[k] == T["held"]["none"][k] for k in base1)
    rec[u"判定の 40 組の規則なしの数が便 XC1(R1+R2)の記録と同じ"] = same1
    h = T["held"]
    n0, n34 = h["none"], h["R3R4"]
    D = n0["答えの数の fact"]
    j = od()
    du = pct(n34["一致"] - n0["一致"], D)
    j["XC2-1"] = od([("予測", u"一致は 2.5 ポイント以上 7.0 ポイント以下ふえる"), ("出た", du)])
    j["XC2-1"]["判定"] = u"当たり" if 2.5 <= du <= 7.0 else u"外れ"
    ds = pct(n0["止めた"] - n34["止めた"], n0["止めた"])
    j["XC2-2"] = od([("予測", u"止めたは 35% 以上 65% 以下減る"), ("出た", ds)])
    j["XC2-2"]["判定"] = u"当たり" if 35 <= ds <= 65 else u"外れ"
    ch = n34["規則で替えて一致"] + n34["規則で替えて黙って違う"] + n34["規則で替えて余計"]
    pc = pct(n34["規則で替えて一致"], ch)
    j["XC2-3"] = od([("予測", u"規則が替えた fact のうち一致は 92% 以上"), ("出た", pc)])
    j["XC2-3"]["判定"] = u"当たり" if pc >= 92 else u"外れ"
    dw = pct(n34["黙って違う"] - n0["黙って違う"], D)
    j["XC2-4"] = od([("予測", u"黙って違うのふえ方は答えの fact の 0.4 ポイント以下"), ("出た", dw)])
    j["XC2-4"]["判定"] = u"当たり" if dw <= 0.4 else u"外れ"
    de = n34["余計に置いた"] - n0["余計に置いた"]
    j["XC2-5"] = od([("予測", u"余計に置いたのふえ方は 5 以下"), ("出た", de)])
    j["XC2-5"]["判定"] = u"当たり" if de <= 5 else u"外れ"
    j["XC2-6"] = od([("予測", u"R3 だけ・R4 だけのどちらでも一致がふえる"), ("出た", "%d・%d(規則なし %d)" % (h["R3"]["一致"], h["R4"]["一致"], n0["一致"]))])
    j["XC2-6"]["判定"] = u"当たり" if h["R3"]["一致"] > n0["一致"] and h["R4"]["一致"] > n0["一致"] else u"外れ"
    dk = pct(abs(n34["置かない"] - n0["置かない"]), D)
    j["XC2-7"] = od([("予測", u"置かないの変わり方は答えの fact の 0.2 ポイント以内"), ("出た", dk)])
    j["XC2-7"]["判定"] = u"当たり" if dk <= 0.2 else u"外れ"
    rec[u"予測の判定"] = j
    rec[u"組ごと(番号と数だけ)"] = od((side + "_" + s, load(side, s)) for side in ("dev", "held") for s in SETS)
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(od([("XC1 と同じ", same1), ("判定", j)]), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
