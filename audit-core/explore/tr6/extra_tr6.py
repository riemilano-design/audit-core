# -*- coding: utf-8 -*-
"""便 TR6 の補足(結果を見てから足した。封 §4 に無い)。単位の変更(円 → 千円)の file は升が千円に丸めてあり、
円の正解はどの台帳でも読めない。違った値が、file の丸め(成分 1 つにつき 500 円以内)で説明できるかを数える。

使い方: python3 -E extra_tr6.py <audit-core> <TR2 の根> <TR6 の根>
"""
import json
import os
import sys

AC, TR2, ROOT = sys.argv[1:4]
sys.argv = [sys.argv[0], "prep", AC, TR2, ROOT]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_tr6 as RN  # noqa: E402

R, L = RN.R, RN.L


def within(decided, bk, truth):
    led = L.make_ledger(decided, bk)
    r = L.read(led, bk)
    if led["誤り"] or r[0] != "読めた":
        return None
    out = {"違う": 0, "丸めの内": 0}
    for key, t in truth.items():
        v = r[1][key]
        if v != t:
            out["違う"] += 1
            out["丸めの内"] += abs(v - t) <= 500 * len(led["項目"][key])
    return out


def main():
    g = {}
    for n in RN.B.NUMS:
        conf, led = RN.base(n)
        truth = RN.load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"]
        seat = RN.load(os.path.join(ROOT, "out", "seat", "%d.json" % n))
        for kind in RN.KINDS:
            bk = RN.book(n, kind, "期2")
            changes = R.diff(conf, led, bk)
            for who, dec in (("案だけ", R.plan_only(changes)), ("席の後", {int(k): v for k, v in seat[kind]["決め"].items()})):
                d2, _ = R.apply(conf, changes, dec)
                w = within(d2, bk, truth[kind]["期2"])
                if w and w["違う"]:
                    x = g.setdefault("%s・%s" % (who, kind), {"止め": 0, "違う値": 0, "丸めの内": 0, "違う値が全部丸めの内の止め": 0})
                    x["止め"] += 1
                    x["違う値"] += w["違う"]
                    x["丸めの内"] += w["丸めの内"]
                    x["違う値が全部丸めの内の止め"] += w["違う"] == w["丸めの内"]
    RN.dump(g, "out", "extra.json")
    print(json.dumps(g, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
