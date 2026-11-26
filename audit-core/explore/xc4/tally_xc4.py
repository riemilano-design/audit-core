# -*- coding: utf-8 -*-
u"""便 XC4 の数え: out/dev.json・out/held.json(と ../xc3/out/held.json)→ record.json。組の番号と数・道具の符号だけ。"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def total(rows):
    t = collections.Counter()
    for r in rows:
        t.update(dict((k, v) for k, v in r.items() if isinstance(v, int) and k != u"番号"))
    t = od(sorted(t.items()))
    c = collections.Counter()
    for r in rows:
        c.update(r[u"組んだ側だけで鳴った符号"].keys())
    t[u"組んだ側だけで鳴った符号(その符号の鳴った組の数)"] = od(sorted(c.items(), key=lambda q: (-q[1], q[0])))
    t[u"組んだ側だけで E の符号が鳴った組"] = sum(1 for r in rows if r[u"組んだ側だけで鳴った E の符号の数"] >= 1)
    t[u"組んだ包みを道具が最後まで読んだ組"] = sum(1 for r in rows if r[u"道具の類: 元・組んだ"][1] == u"走った")
    return t


def main():
    dev = json.load(open(os.path.join(HERE, "out", "dev.json"), encoding="utf-8"))
    held = json.load(open(os.path.join(HERE, "out", "held.json"), encoding="utf-8"))
    h = total(held)
    codes = h[u"組んだ側だけで鳴った符号(その符号の鳴った組の数)"]
    j = od()
    j["XC4-1"] = od([("予測", u"組んだ側だけで arelle:nonIxdsDocument が鳴った組は 2 以下"), ("出た", codes.get("arelle:nonIxdsDocument", 0))])
    j["XC4-1"]["判定"] = u"当たり" if j["XC4-1"]["出た"] <= 2 else u"外れ"
    e2, e5 = codes.get("EDINET.EC3002E", 0), codes.get("EDINET.EC3005E", 0)
    j["XC4-2"] = od([("予測", u"組んだ側だけで EC3002E・EC3005E が鳴った組はどちらも 4 以下(便 XC3 では 35・35)"), ("出た", "%d・%d" % (e2, e5))])
    j["XC4-2"]["判定"] = u"当たり" if e2 <= 4 and e5 <= 4 else u"外れ"
    j["XC4-3"] = od([("予測", u"組んだ側だけで E の符号が鳴った組は 38 以上(まだ検査に通らない)"), ("出た", h[u"組んだ側だけで E の符号が鳴った組"])])
    j["XC4-3"]["判定"] = u"当たり" if h[u"組んだ側だけで E の符号が鳴った組"] >= 38 else u"外れ"
    r4 = pct(h[u"位置: 一致"], h[u"位置: 答えの文の fact"])
    j["XC4-4"] = od([("予測", u"文の fact の置き場と属性が答えと同じは、答えの文の fact の 22% 以上 36% 以下"), ("出た", r4)])
    j["XC4-4"]["判定"] = u"当たり" if 22 <= r4 <= 36 else u"外れ"
    r5 = pct(h[u"位置: 置いた文の fact"] - h[u"位置: 一致"], h[u"位置: 置いた文の fact"])
    j["XC4-5"] = od([("予測", u"置いた文の fact のうち答えと違う(置き場か属性)は 10% 以下"), ("出た", r5)])
    j["XC4-5"]["判定"] = u"当たり" if r5 <= 10 else u"外れ"
    j["XC4-6"] = od([("予測", u"道具が読んだ数の fact で元と同じ行は 31500 以上(便 XC3 は 32124)"), ("出た", h[u"数の fact: 元と同じ行"])])
    j["XC4-6"]["判定"] = u"当たり" if h[u"数の fact: 元と同じ行"] >= 31500 else u"外れ"
    stopped = len(held) - h[u"組んだ包みを道具が最後まで読んだ組"]
    j["XC4-7"] = od([("予測", u"組んだ包みで道具が途中で止まった組は 12 以下"), ("出た", stopped)])
    j["XC4-7"]["判定"] = u"当たり" if stopped <= 12 else u"外れ"
    xs = codes.get("xmlSchema:syntax", 0)
    j["XC4-8"] = od([("予測", u"組んだ側だけで xmlSchema:syntax が鳴った組は 10 以上(新しく鳴る符号が在る)"), ("出た", xs)])
    j["XC4-8"]["判定"] = u"当たり" if xs >= 10 else u"外れ"
    rec = od([(u"便", u"XC4(文の fact を前の年から置き、包みを道具 P に読ませる)"), (u"集計 作りの 23 組", total(dev)), (u"集計 判定の 40 組", h),
              (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", dev), ("held", held)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
