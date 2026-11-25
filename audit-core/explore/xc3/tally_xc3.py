# -*- coding: utf-8 -*-
u"""便 XC3 の数え: out/dev.json・out/held.json → record.json。組の番号と数・道具の符号だけ。"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict
KEYS = ("置いた数の fact", "道具が読んだ: 元の数の fact", "道具が読んだ: 組んだ数の fact", "数の fact: 元と同じ行", "数の fact: 組んだ側だけの行",
        "数の fact: 元の側だけの行", "道具が読んだ: 元の数でない fact", "道具が読んだ: 組んだ数でない fact", "数でない fact: 元と同じ行",
        "数でない fact: 最後の欄(提出日の期)を除けば元と同じ行", "組んだ側だけで鳴った E の符号の数")


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def total(rows):
    t = od((k, sum(r[k] for r in rows)) for k in KEYS)
    t["道具の類(元・組んだ)"] = od(sorted(collections.Counter(" / ".join(r["道具の類: 元・組んだ"]) for r in rows).items()))
    c = collections.Counter()
    for r in rows:
        c.update(r["組んだ側だけで鳴った符号"].keys())
    t["組んだ側だけで鳴った符号(その符号の鳴った組の数)"] = od(sorted(c.items(), key=lambda q: (-q[1], q[0])))
    t["組んだ側だけで E の符号が鳴った組"] = sum(1 for r in rows if r["組んだ側だけで鳴った E の符号の数"] >= 1)
    t["組んだ包みを道具が最後まで読んだ組"] = sum(1 for r in rows if r["道具の類: 元・組んだ"][1] == u"走った")
    return t


def main():
    dev = json.load(open(os.path.join(HERE, "out", "dev.json"), encoding="utf-8"))
    held = json.load(open(os.path.join(HERE, "out", "held.json"), encoding="utf-8"))
    h = total(held)
    j = od()
    r1 = pct(h["数の fact: 元と同じ行"], h["道具が読んだ: 元の数の fact"])
    j["XC3-1"] = od([("予測", u"道具が読んだ数の fact のうち元と同じ行は、元の数の fact の 72% 以上 82% 以下"), ("出た", r1)])
    j["XC3-1"]["判定"] = u"当たり" if 72 <= r1 <= 82 else u"外れ"
    r2 = pct(h["数の fact: 組んだ側だけの行"], h["道具が読んだ: 組んだ数の fact"])
    j["XC3-2"] = od([("予測", u"組んだ側だけの数の fact の行は、組んだ包みから読んだ数の fact の 5% 以下"), ("出た", r2)])
    j["XC3-2"]["判定"] = u"当たり" if r2 <= 5 else u"外れ"
    j["XC3-3"] = od([("予測", u"組んだ包みを道具が最後まで読んだ組は 40 のうち 34 以上"), ("出た", h["組んだ包みを道具が最後まで読んだ組"])])
    j["XC3-3"]["判定"] = u"当たり" if h["組んだ包みを道具が最後まで読んだ組"] >= 34 else u"外れ"
    r4 = pct(h["数でない fact: 最後の欄(提出日の期)を除けば元と同じ行"], h["道具が読んだ: 組んだ数でない fact"])
    j["XC3-4"] = od([("予測", u"組んだ包みの数でない fact(隠しの fact)は、提出日の期を除けば 95% 以上が元と同じ"), ("出た", r4)])
    j["XC3-4"]["判定"] = u"当たり" if r4 >= 95 else u"外れ"
    j["XC3-5"] = od([("予測", u"組んだ側だけで E の符号が鳴った組は 40 のうち 38 以上(まだ検査に通る包みではない)"), ("出た", h["組んだ側だけで E の符号が鳴った組"])])
    j["XC3-5"]["判定"] = u"当たり" if h["組んだ側だけで E の符号が鳴った組"] >= 38 else u"外れ"
    rec = od([(u"便", u"XC3(今年の答えを見ずに組んだ包みを道具 P に読ませる)"), (u"集計 作りの 23 組", total(dev)), (u"集計 判定の 40 組", h),
              (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", dev), ("held", held)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
