# -*- coding: utf-8 -*-
u"""便 XC0 の数え: out/train.json(訓練 3 組)と out/judge.json(判定 60 組)→ record.json。会社の名・コード・file の名は書かない(組の番号と数だけ)。"""
import collections
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
od = collections.OrderedDict
SUM_KEYS = ("答えの数の fact", "うち表の cell の中", "一致", "黙って違う", "止めた", "置かない", "余計に置いた", "置いた", "置かない cell の数",
            "使った文脈", "使った文脈の定義が元と同じ", "使った単位", "使った単位の定義が元と同じ", "組んだ file", "組み直しで置いた fact が戻った file")


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def total(rows):
    t = od((k, sum(r[k] for r in rows)) for k in SUM_KEYS)
    for k in ("違う欄", "止めた理由"):
        c = collections.Counter()
        for r in rows:
            c.update(r[k])
        t[k] = od(sorted(c.items(), key=lambda q: -q[1]))
    return t


def main():
    train = json.load(open(os.path.join(HERE, "out", "train.json"), encoding="utf-8"))
    judge = json.load(open(os.path.join(HERE, "out", "judge.json"), encoding="utf-8"))
    t = total(judge)
    D = t["答えの数の fact"]
    per = [pct(r["一致"], r["答えの数の fact"]) for r in judge]
    placed_judged = t["一致"] + t["黙って違う"]
    j = od()
    j["XC0-1"] = od([("予測", u"一致の率 68% 以上 84% 以下"), ("出た", pct(t["一致"], D))])
    j["XC0-1"]["判定"] = u"当たり" if 68 <= j["XC0-1"]["出た"] <= 84 else u"外れ"
    j["XC0-2"] = od([("予測", u"黙って違うは答えの fact の 2.0% 以下"), ("出た", pct(t["黙って違う"], D))])
    j["XC0-2"]["判定"] = u"当たり" if j["XC0-2"]["出た"] <= 2.0 else u"外れ"
    j["XC0-3"] = od([("予測", u"余計に置いたは置いた fact の 0.5% 以下"), ("出た", pct(t["余計に置いた"], t["置いた"]))])
    j["XC0-3"]["判定"] = u"当たり" if j["XC0-3"]["出た"] <= 0.5 else u"外れ"
    j["XC0-4"] = od([("予測", u"置いて答えと同じ置き場だった fact のうち黙って違うは 2.5% 以下"), ("出た", pct(t["黙って違う"], placed_judged))])
    j["XC0-4"]["判定"] = u"当たり" if j["XC0-4"]["出た"] <= 2.5 else u"外れ"
    j["XC0-5"] = od([("予測", u"組み直しで置いた fact が戻った file は全部"), ("出た", "%d / %d" % (t["組み直しで置いた fact が戻った file"], t["組んだ file"]))])
    j["XC0-5"]["判定"] = u"当たり" if t["組み直しで置いた fact が戻った file"] == t["組んだ file"] else u"外れ"
    j["XC0-6"] = od([("予測", u"使った文脈の定義が元と同じは 95% 以上"), ("出た", pct(t["使った文脈の定義が元と同じ"], t["使った文脈"]))])
    j["XC0-6"]["判定"] = u"当たり" if j["XC0-6"]["出た"] >= 95 else u"外れ"
    j["XC0-7"] = od([("予測", u"使った単位の定義は全部元と同じ"), ("出た", "%d / %d" % (t["使った単位の定義が元と同じ"], t["使った単位"]))])
    j["XC0-7"]["判定"] = u"当たり" if t["使った単位の定義が元と同じ"] == t["使った単位"] else u"外れ"
    ge95 = sum(1 for p in per if p is not None and p >= 95)
    j["XC0-8"] = od([("予測", u"一致の率が 95% 以上の書類は 60 のうち 3 以下"), ("出た", ge95)])
    j["XC0-8"]["判定"] = u"当たり" if ge95 <= 3 else u"外れ"
    rec = od()
    rec[u"便"] = u"XC0(今年の答えを見ずに、素の本文と前の年の XBRL から表の中の数の fact を置く)"
    rec[u"集計 60 組(判定)"] = t
    rec[u"集計 3 組(訓練。規則を作るのに見た)"] = total(train)
    rec[u"60 組の書類ごとの一致の率"] = od([("最小", min(per)), ("中央", statistics.median(per)), ("最大", max(per)), ("95% 以上の書類", ge95)])
    rec[u"予測の判定"] = j
    rec[u"組ごと(番号と数だけ)"] = train + judge
    with open(os.path.join(HERE, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(j, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
