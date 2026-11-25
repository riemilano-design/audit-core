# -*- coding: utf-8 -*-
"""便 TR9: 3 つの直しを測る(封 §3)。AI を使わない。

使い方: python3 -E run_tr9.py {machine|prep|seat} <audit-core> <TR2> <TR6> <TR8> <TR9>
席の答え(reply/{n}.json)は信頼しない data として JSON で読むだけ。正解は読んだ値と比べるためだけに読む。
"""
import json
import os
import random
import sys

MODE, AC, TR2, TR6, TR8, ROOT = sys.argv[1:7]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "prep", AC, TR2, TR6]
for d in ("tr2", "tr6", "tr7", "tr8"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, HERE)
import run_tr6 as RN  # noqa: E402
import partial_tr7 as P  # noqa: E402
import ledger8 as G8  # noqa: E402
import reconf8 as R8  # noqa: E402
import ledger9 as G9  # noqa: E402
import reconf9 as R9  # noqa: E402

R, L = RN.R, RN.L
DUP = ["同じ見出しの列(手がかりあり)", "同じ見出しの列(手がかりなし)"]


def dump(obj, *parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def state(r, truth):
    if r[0] != "読めた":
        return {"状態": "止める", "規則": sorted({d.get("規則") for d in r[1]})}
    return {"状態": "読めた", "違う": RN.compare(r[1], truth)}


def bk9(n, kind, per):
    return L.load_book(os.path.join(ROOT, "co%d" % n, kind, per, "書き出し.xlsx"))


def machine():
    out = {}
    for n in RN.B.NUMS:
        conf = RN.load(os.path.join(TR2, "confirm", "%d.applied.json" % n))
        b1 = L.load_book(os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx"))
        led, led9 = L.make_ledger(conf, b1), G9.make(conf, b1)
        t2 = RN.load(os.path.join(TR2, "co%d" % n, "正解", "値.json"))
        o = {"検算の式(TR8)": len(G8.learn(conf, b1)), "検算の式(TR9)": len(led9["検算"]), "A": {}}
        for per in ("期1", "期2"):
            o["A"][per] = state(G9.read(conf, led9, L.load_book(os.path.join(TR2, "co%d" % n, per, "書き出し.xlsx"))), t2[per])
        tr6 = RN.load(os.path.join(TR6, "out", "seat", "%d.json" % n))
        tv = RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]
        for kind in RN.KINDS:
            bk = RN.book(n, kind, "期2")
            d2, _ = R.apply(conf, R.diff(conf, led, bk), {int(k): v for k, v in tr6[kind]["決め"].items()})
            l2 = G9.make(d2, bk)
            for per in ("期2", "期3"):
                o["A"]["%s・%s" % (kind, per)] = state(G9.read(d2, l2, RN.book(n, kind, per)), tv[kind][per])
        # B 偶然の和
        t9 = RN.load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"]
        acc = bk9(n, "偶然の和", "期1")
        b2 = L.load_book(os.path.join(TR2, "co%d" % n, "期2", "書き出し.xlsx"))
        o["B"] = {"TR8 の覚え方": state(G8.read(conf, G8.make(conf, acc), b2), t2["期2"]),
                  "TR9 の覚え方": state(G9.read(conf, G9.make(conf, acc), b2), t2["期2"])}
        # C TR8 の入れ替わりの素材
        t8 = RN.load(os.path.join(TR8, "co%d" % n, "正解.json"))["値"]
        o["C"] = {k: state(G9.read(conf, led9, L.load_book(os.path.join(TR8, "co%d" % n, k, "期2", "書き出し.xlsx"))), t8[k]["期2"])
                  for k in t8 if k != "同じ見出しの列の追加"}
        # D 同じ見出しの列: 案だけ・部分の読み・2 本目と決めた時の読み(機械の確かめ)
        o["D"] = {}
        for kind in DUP:
            bk = bk9(n, kind, "期2")
            ch = R9.diff9(conf, led, bk)
            d2, bad = R9.apply(conf, ch, R.plan_only(ch))
            w = R8.waiting8(conf, ch, bk)
            got = P.read_some(conf, bk, set(t9[kind]["期2"]) - w)
            ideal = {c["番号"]: ({"列の何番目": 2} if c["種類"] == "同じ見出しの列の追加" else c["案"]) for c in ch}
            d3, bad3 = R9.apply(conf, ch, ideal)
            l3 = G9.make(d3, bk)
            o["D"][kind] = {"変わった所": [c["種類"] for c in ch], "案だけ": "読まない" if bad else state(G9.read(d2, G9.make(d2, bk), bk), t9[kind]["期2"]),
                            "部分の読み": {"先に読んだ": len(got), "違う": sum(1 for k, v in got.items() if v != t9[kind]["期2"][k])},
                            "2 本目と決めた時": {per: state(G9.read(d3, l3, bk9(n, kind, per)), t9[kind][per]) for per in ("期2", "期3")}}
        out[n] = o
        print(n, o["検算の式(TR8)"], o["検算の式(TR9)"], o["B"], {k: v["状態"] for k, v in o["C"].items()},
              {k: (v["案だけ"] if isinstance(v["案だけ"], str) else v["案だけ"]["状態"], v["部分の読み"]["違う"],
                   v["2 本目と決めた時"]["期2"]["状態"], len(v["2 本目と決めた時"]["期2"].get("違う", [])),
                   v["2 本目と決めた時"]["期3"]["状態"]) for k, v in o["D"].items()})
    dump(out, "out", "machine.json")


def screens(n):
    conf, led = RN.base(n)
    items = [(kind, bk9(n, kind, "期2"), RN.load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"][kind]["期2"]) for kind in DUP]
    if n == 54:
        items.append(("意味の変わる改名", RN.book(n, "意味の変わる改名", "期2"),
                      RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]["意味の変わる改名"]["期2"]))
    random.Random(n * 17).shuffle(items)
    return conf, led, items


def prep():
    for n in RN.B.NUMS:
        conf, led, items = screens(n)
        key = {}
        for k, (kind, bk, t) in enumerate(items, 1):
            sk = "s%d" % k
            key[sk] = kind
            ch = R9.diff9(conf, led, bk)
            early = P.read_some(conf, bk, set(t) - R8.waiting8(conf, ch, bk))
            d2, bad = R9.apply(conf, ch, R.plan_only(ch))
            plan_read = None
            if not bad:
                r2 = G9.read(d2, G9.make(d2, bk), bk)
                if r2[0] == "読めた":
                    plan_read = {a: r2[1][a] for a in sorted({a for c in ch for a in c["影響"]})}
            p = os.path.join(ROOT, "screen", str(n), sk + ".html")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(R9.screen9(n, sk, ch, conf, bk, plan_read, early))
        dump(key, "key", "%d.json" % n)
        print(n, key)


def seat():
    for n in RN.B.NUMS:
        conf, led, items = screens(n)
        key = RN.load(os.path.join(ROOT, "key", "%d.json" % n))
        rp = os.path.join(ROOT, "reply", "%d.json" % n)
        reply = RN.load(rp) if os.path.exists(rp) else {}
        out = {}
        for sk, kind in key.items():
            _, bk, t = next(x for x in items if x[0] == kind)
            ch = R9.diff9(conf, led, bk)
            ans = ((reply.get("画面") or {}).get(sk) or {})
            dec = {}
            for x in ans.get("決め") or []:
                if not isinstance(x, dict) or not isinstance(x.get("番号"), int):
                    continue
                c = next((c for c in ch if c["番号"] == x["番号"]), None)
                if x.get("選び") == "案のまま" and c is not None and c["案"] is not None:
                    dec[x["番号"]] = c["案"]
                elif x.get("選び") == "決める" and isinstance(x.get("決め"), dict):
                    dec[x["番号"]] = x["決め"]
            d2, bad = R9.apply(conf, ch, dec)
            res = {"決め": {str(k): v for k, v in dec.items()}, "当てられなかった": ["%s: %s" % b for b in bad], "気づき": ans.get("気づき", "")}
            if not bad:
                l2 = G9.make(d2, bk)
                res["期2"] = state(G9.read(d2, l2, bk), t)
                if kind in DUP:
                    res["期3"] = state(G9.read(d2, l2, bk9(n, kind, "期3")), RN.load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"][kind]["期3"])
            out[kind] = res
        dump(out, "out", "seat", "%d.json" % n)
        print(n, {k: (v["当てられなかった"], v.get("期2", {}).get("状態"), len(v.get("期2", {}).get("違う", [])), v.get("期3", {}).get("状態")) for k, v in out.items()})


if __name__ == "__main__":
    {"machine": machine, "prep": prep, "seat": seat}[MODE]()
