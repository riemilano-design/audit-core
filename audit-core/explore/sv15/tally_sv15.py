# -*- coding: utf-8 -*-
"""便 SV15 の答え直す項目の決めと、照合・集計(封 explore/sv15/SEAL.md §1・§2)。

使い方:
  python3 -I tally_sv15.py list  <explore> <scratchpad の根> <SV15 の根>
      SV15 の根の f13・f10(SV13・SV10 の根の写し)で、S1〜S6・S10′ を通り S11 の形 A が止めた項目を社ごとに
      <SV15 の根>/redo/<流れ>/<社>.json に書く。
  python3 -I tally_sv15.py tally <explore> <scratchpad の根> <SV15 の根> <record.json の path>
      <SV15 の根>/redo/<流れ>/<社>/答え直し.json で、写しの r1/out<社>/答え.json の該当項目を置き換え、
      SV14 の流れ(S11 形 A + S8 + S9)と、答え直した項目の数を数える。記録は数だけ。
"""
import json
import os
import shutil
import sys

CMD, EXPLORE, SCRATCH, ROOT = sys.argv[1:5]
OUT = sys.argv[5] if CMD == "tally" else os.devnull
F13, F10 = os.path.join(ROOT, "f13"), os.path.join(ROOT, "f10")
sys.path.insert(0, os.path.join(EXPLORE, "sv14"))
sys.argv = ["", EXPLORE, SCRATCH, F13, F10, os.devnull]
import tally_sv14 as X  # noqa: E402
V, T, tally, tally_sv10 = X.V, X.T, X.tally, X.tally_sv10
FLOWS = [("f13", F13, ["18", "19", "20"]), ("f10", F10, ["15", "16", "17"])]


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def stopped(root, nums):
    """S1〜S6・S10′ を通り、S11 の形 A が止めた項目(社ごと)。"""
    T.TEXT_MODE = "A"
    tally.COMPANIES = nums
    out = {}
    for n in nums:
        co = X.S11Company(os.path.join(root, "r1", "conv"), n)
        items = []
        for item in tally.ITEMS:
            a = co.answers.get(item) or {}
            v, src = a.get("値"), a.get("出どころ") or []
            if v is None:
                continue
            X.MODE = None
            if V.judge(co, V.SetCompany, item, v, src) is not None:
                continue
            X.MODE = "A"
            if co.s11(item, src) is not None:
                items.append(item)
            X.MODE = None
        out[n] = items
    return out


def do_list():
    for name, root, nums in FLOWS:
        X.flow(root, nums, None)  # r1/conv を作る
        d = os.path.join(ROOT, "redo", name)
        os.makedirs(d, exist_ok=True)
        for n, items in stopped(root, nums).items():
            with open(os.path.join(d, n + ".json"), "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False)
            print(name, n, len(items))


def do_tally():
    rec = {"流れ": {}, "答え直し": {}}
    for name, root, nums in FLOWS:
        before = {n: load(os.path.join(ROOT, "redo", name, n + ".json")) for n in nums}  # list で決めた項目
        g = {"答え直す項目": 0, "正しく出し直して照合を通った": 0, "正しく出し直したが照合で止めた": 0,
             "null にした": 0, "違う値で照合に止められた": 0, "違う値で照合を通った": 0}
        for n in nums:
            items = before[n]
            if not items:
                continue
            redo = load(os.path.join(ROOT, "redo", name, n, "答え直し.json")).get("行") or []
            redo = {r.get("項目"): r for r in redo if r.get("項目") in items}
            p = os.path.join(root, "r1", "out" + n, "答え.json")
            keep = p + ".sv15_before"
            if not os.path.exists(keep):
                shutil.copy(p, keep)
            ans = load(keep)
            for r in ans["行"]:
                if r.get("項目") in items:
                    x = redo.get(r["項目"]) or {"値": None, "出どころ": []}
                    r["値"], r["出どころ"] = x.get("値"), x.get("出どころ") or []
            with open(p, "w", encoding="utf-8") as f:
                json.dump(ans, f, ensure_ascii=False)
            g["答え直す項目"] += len(items)
        rec["流れ"][name] = X.flow(root, nums, "A")
        # 置き換えた後の答えを、置き換えた項目だけ照合で見る(S1〜S6・S10′・S11 形 A。S8・S9 は流れの数に入る)
        X.MODE = "A"
        for n in nums:
            co = X.S11Company(os.path.join(root, "r1", "conv"), n)
            for item in before[n]:
                a = co.answers.get(item) or {}
                v, src = a.get("値"), a.get("出どころ") or []
                if v is None:
                    g["null にした"] += 1
                    continue
                w = V.judge(co, X.S11Company, item, v, src) or co.s11(item, src)
                if v == co.gold[item]:
                    g["正しく出し直して照合を通った" if w is None else "正しく出し直したが照合で止めた"] += 1
                else:
                    g["違う値で照合を通った" if w is None else "違う値で照合に止められた"] += 1
        X.MODE = None
        rec["答え直し"][name] = g
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    do_list() if CMD == "list" else do_tally()
