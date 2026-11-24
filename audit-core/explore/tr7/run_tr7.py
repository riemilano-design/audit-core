# -*- coding: utf-8 -*-
"""便 TR7: TR6 の 54 の止めで、部分の読みを測る(封 §3)。AI を使わない。

使い方: python3 -E run_tr7.py <audit-core> <TR2 の根> <TR6 の根> <record.json の行き先>
"""
import json
import os
import sys

AC, TR2, TR6, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "prep", AC, TR2, TR6]
sys.path.insert(0, os.path.join(AC, "explore", "tr6"))
sys.path.insert(0, HERE)
import run_tr6 as RN  # noqa: E402
import partial_tr7 as P  # noqa: E402

R = RN.R


def main():
    kinds = {}
    tot = {"止め": 0, "項目": 0, "先に読んだ": 0, "先に読んで正しい": 0, "先に読んで違う": 0, "待った": 0}
    for n in RN.B.NUMS:
        conf, led = RN.base(n)
        truth = RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]
        for kind in RN.KINDS:
            bk = RN.book(n, kind, "期2")
            changes = R.diff(conf, led, bk)
            w = P.waiting(conf, changes, bk)
            keys = set(truth[kind]["期2"]) - w
            got = P.read_some(conf, bk, keys)
            t = truth[kind]["期2"]
            k = kinds.setdefault(kind, {"止め": 0, "先に読んだ": 0, "先に読んで違う": 0, "待った": 0, "素朴: 先に読んで違う": 0})
            # 比べ(素朴な部分の読み): 影響する項目(成分にその行・列・シートを使う項目)と、単位・シートの変わったシートの項目だけを待たせる
            nw = {a for ch in changes for a in ch["影響"]}
            nkeys = set(t := truth[kind]["期2"]) - nw
            ng = P.read_some(conf, bk, nkeys)
            k["素朴: 先に読んで違う"] += sum(1 for x, v in ng.items() if v != t[x])
            tot["素朴: 先に読んで違う"] = tot.get("素朴: 先に読んで違う", 0) + sum(1 for x, v in ng.items() if v != t[x])
            k["止め"] += 1
            k["先に読んだ"] += len(got)
            bad = sum(1 for x, v in got.items() if v != t[x])
            k["先に読んで違う"] += bad
            k["待った"] += len(w)
            tot["止め"] += 1
            tot["項目"] += len(t)
            tot["先に読んだ"] += len(got)
            tot["先に読んで正しい"] += len(got) - bad
            tot["先に読んで違う"] += bad
            tot["待った"] += len(w)
    rec = {"計": tot, "種類ごと": kinds, "注": "数だけ。TR6 の素材(作り物の 6 社 × 9 種)の期 2 の変異の file。"}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
