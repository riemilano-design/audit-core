# -*- coding: utf-8 -*-
u"""便 XC6 の数え: out/dev.json・out/held.json(と ../xc5/out/held.json)→ record.json。符号の分けは便 XC5 と同じ。"""
import collections
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("_t5", os.path.join(os.path.dirname(HERE), "xc5", "tally_xc5.py"))
T5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T5)
od = collections.OrderedDict


def total(rows):
    t = T5.total(rows)
    for k in ("G1 で置かなかった数の fact", "G2 で置かなかった数の fact"):
        t[k] = sum(r.get(k, 0) for r in rows)
    return t


def main():
    dev = json.load(open(os.path.join(HERE, "out", "dev.json"), encoding="utf-8"))
    held = json.load(open(os.path.join(HERE, "out", "held.json"), encoding="utf-8"))
    x5 = T5.total(json.load(open(os.path.join(HERE, "..", "xc5", "out", "held.json"), encoding="utf-8")))
    h = total(held)
    codes = h[u"組んだ側だけで鳴った符号(その符号の鳴った組の数)"]
    j = od()

    def judge(key, pred, got, ok):
        j[key] = od([("予測", pred), ("出た", got), ("判定", u"当たり" if ok else u"外れ")])
    a0 = h[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"]
    judge("XC6-1", u"誤りの符号が 1 つも鳴らなかった組は 26 以上 30 以下(便 XC5 は %d)" % x5[u"組んだ側だけで誤りの符号が 1 つも鳴らなかった組"], a0, 26 <= a0 <= 30)
    e0 = h[u"組んだ側だけで EDINET の E の符号が鳴らなかった組"]
    judge("XC6-2", u"EDINET の E の符号が鳴らなかった組は 29 以上(便 XC5 は %d)" % x5[u"組んだ側だけで EDINET の E の符号が鳴らなかった組"], e0, e0 >= 29)
    judge("XC6-3", u"EDINET.EC8024E が鳴った組は 1 以下(便 XC5 は 5)", codes.get("EDINET.EC8024E", 0), codes.get("EDINET.EC8024E", 0) <= 1)
    xm = codes.get("xbrldie:ExplicitMemberUndefinedQNameError", 0)
    judge("XC6-4", u"xbrldie:ExplicitMemberUndefinedQNameError が鳴った組は 0(便 XC5 は 2)", xm, xm == 0)
    judge("XC6-5", u"道具が読んだ数の fact で元と同じ行は 32150 以上(便 XC5 は %d)" % x5[u"数の fact: 元と同じ行"], h[u"数の fact: 元と同じ行"], h[u"数の fact: 元と同じ行"] >= 32150)
    ran = h[u"組んだ包みを道具が最後まで読んだ組"]
    judge("XC6-6", u"道具が最後まで読んだ組は 36 以上(便 XC5 は %d)" % x5[u"組んだ包みを道具が最後まで読んだ組"], ran, ran >= 36)
    rec = od([(u"便", u"XC6(G1 無いメンバー・G2 食い違う重なり)"), (u"集計 作りの 23 組", total(dev)), (u"集計 判定の 40 組", h),
              (u"便 XC5 の判定の 40 組(比べる土台)", x5), (u"予測の判定", j), (u"組ごと(番号と数だけ)", od([("dev", dev), ("held", held)]))])
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
