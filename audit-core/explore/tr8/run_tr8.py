# -*- coding: utf-8 -*-
"""便 TR8: 小さな穴を直した形を測る(封 §3)。AI を使わない。

使い方:
  python3 -E run_tr8.py machine <audit-core> <TR2> <TR6> <TR8>  止めすぎ(A)と新しい穴の素材(B)
  python3 -E run_tr8.py prep    <audit-core> <TR2> <TR6> <TR8>  TR6 の 54 の止めの、直した画面を作る(C)
  python3 -E run_tr8.py seat    <audit-core> <TR2> <TR6> <TR8>  席の決めを当てて読む(C)
席の答え(reply/{n}.json)は信頼しない data として JSON で読むだけ。正解は読んだ値と比べるためだけに読む。
"""
import json
import os
import random
import sys

MODE, AC, TR2, TR6, ROOT = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "prep", AC, TR2, TR6]
for d in ("tr2", "tr6", "tr7"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, HERE)
import run_tr6 as RN  # noqa: E402
import partial_tr7 as P  # noqa: E402
import ledger8 as G  # noqa: E402
import reconf8 as R8  # noqa: E402

R, L = RN.R, RN.L
KINDS8 = ["同じ見出しの列の追加", "値の入れ替わり", "同じ字の行の入れ替え"]


def dump(obj, *parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def state(r, truth):
    if r[0] != "読めた":
        return {"状態": "止める", "規則": sorted({d.get("規則") for d in r[1]})}
    return {"状態": "読めた", "違う": RN.compare(r[1], truth)}


def b1(n):
    return L.load_book(os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx"))


def machine():
    out = {"A": {}, "B": {}}
    for n in RN.B.NUMS:
        conf = RN.load(os.path.join(TR2, "confirm", "%d.applied.json" % n))
        bk1 = b1(n)
        led = L.make_ledger(conf, bk1)
        led8 = G.make(conf, bk1)
        t2 = RN.load(os.path.join(TR2, "co%d" % n, "正解", "値.json"))
        a = {"検算の式": len(led8["検算"])}
        for per in ("期1", "期2"):
            bk = L.load_book(os.path.join(TR2, "co%d" % n, per, "書き出し.xlsx"))
            a[per] = state(G.read(conf, led8, bk), t2[per])
        # TR6 の席の決めで確定し直した台帳で、期 2 の変異の file と期 3 を読む
        tr6 = RN.load(os.path.join(TR6, "out", "seat", "%d.json" % n))
        tv = RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]
        a["確定し直した台帳"] = {}
        for kind in RN.KINDS:
            bk = RN.book(n, kind, "期2")
            changes = R.diff(conf, led, bk)
            d2, _ = R.apply(conf, changes, {int(k): v for k, v in tr6[kind]["決め"].items()})
            l2 = G.make(d2, bk)
            a["確定し直した台帳"][kind] = {per: state(G.read(d2, l2, RN.book(n, kind, per)), tv[kind][per]) for per in ("期2", "期3")}
        out["A"][n] = a
        truth8 = RN.load(os.path.join(ROOT, "co%d" % n, "正解.json"))["値"]
        b = {}
        for kind in truth8:
            bk = L.load_book(os.path.join(ROOT, "co%d" % n, kind, "期2", "書き出し.xlsx"))
            t = truth8[kind]["期2"]
            x = {"TR2 の読み": state(L.read(led, bk), t), "TR8 の読み": state(G.read(conf, led8, bk), t)}
            if x["TR2 の読み"]["状態"] == "止める":
                old = R.diff(conf, led, bk)
                d2, _ = R.apply(conf, old, R.plan_only(old))
                x["TR6 の案だけ"] = state(L.read(L.make_ledger(d2, bk), bk), t)
                new = R8.diff8(conf, led, bk)
                d3, bad = R.apply(conf, new, R.plan_only(new))
                x["TR8 の案だけ"] = {"状態": "決めていない所が在る", "数": len(bad)} if bad else state(G.read(d3, G.make(d3, bk), bk), t)
                for name, w in (("TR7 の部分の読み", P.waiting(conf, old, bk)), ("TR8 の部分の読み", R8.waiting8(conf, new, bk))):
                    got = P.read_some(conf, bk, set(t) - w)
                    x[name] = {"先に読んだ": len(got), "違う": sorted(k for k, v in got.items() if v != t[k])}
            b[kind] = x
        out["B"][n] = b
        print(n, a["期1"], a["期2"], a["検算の式"], {k: (v["TR2 の読み"]["状態"], v["TR8 の読み"]["状態"]) for k, v in b.items()})
    dump(out, "out", "machine.json")


def prep():
    for n in RN.B.NUMS:
        conf, led = RN.base(n)
        truth = RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]
        order = RN.KINDS[:]
        random.Random(n * 13).shuffle(order)
        key = {}
        for k, kind in enumerate(order, 1):
            sk = "s%d" % k
            key[sk] = kind
            bk = RN.book(n, kind, "期2")
            changes = R8.diff8(conf, led, bk)
            d2, bad = R.apply(conf, changes, R.plan_only(changes))
            plan_read = None
            if not bad:
                r2 = L.read(L.make_ledger(d2, bk), bk)
                if r2[0] == "読めた":
                    plan_read = {a: r2[1][a] for a in sorted({a for ch in changes for a in ch["影響"]})}
            early = P.read_some(conf, bk, set(truth[kind]["期2"]) - R8.waiting8(conf, changes, bk))
            p = os.path.join(ROOT, "screen", str(n), sk + ".html")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(R8.screen8(n, sk, changes, conf, bk, plan_read, early))
        dump(key, "key", "%d.json" % n)
        print(n, "画面", len(key))


def seat():
    for n in RN.B.NUMS:
        conf, led = RN.base(n)
        truth = RN.load(os.path.join(TR6, "co%d" % n, "正解.json"))["値"]
        key = RN.load(os.path.join(ROOT, "key", "%d.json" % n))
        rp = os.path.join(ROOT, "reply", "%d.json" % n)
        reply = RN.load(rp) if os.path.exists(rp) else {}
        out = {}
        for sk, kind in key.items():
            bk = RN.book(n, kind, "期2")
            changes = R8.diff8(conf, led, bk)
            ans = ((reply.get("画面") or {}).get(sk) or {})
            dec, form = {}, []
            for x in ans.get("決め") or []:
                if not isinstance(x, dict) or not isinstance(x.get("番号"), int):
                    form.append("読めない決め")
                    continue
                ch = next((c for c in changes if c["番号"] == x["番号"]), None)
                if x.get("選び") == "案のまま" and ch is not None and ch["案"] is not None:
                    dec[x["番号"]] = ch["案"]
                elif x.get("選び") == "決める" and isinstance(x.get("決め"), dict):
                    dec[x["番号"]] = x["決め"]
                else:
                    form.append("番号 %s の選びが読めない" % x["番号"])
            d2, bad = R.apply(conf, changes, dec)
            l2 = G.make(d2, bk)
            res = {"決め": {str(k): v for k, v in dec.items()}, "形の誤り": form + ["%s: %s" % b for b in bad],
                   "案から変えた": sum(1 for c in changes if c["番号"] in dec and c["案"] is not None and dec[c["番号"]] != c["案"]),
                   "期2": state(G.read(d2, l2, bk), truth[kind]["期2"]), "気づき": ans.get("気づき", "")}
            if res["期2"]["状態"] == "読めた":
                res["期3"] = state(G.read(d2, l2, RN.book(n, kind, "期3")), truth[kind]["期3"])
            out[kind] = res
        dump(out, "out", "seat", "%d.json" % n)
        print(n, {k: (v["期2"]["状態"], len(v["期2"].get("違う", [])), v.get("期3", {}).get("状態"), v["案から変えた"]) for k, v in out.items()})


if __name__ == "__main__":
    {"machine": machine, "prep": prep, "seat": seat}[MODE]()
