# -*- coding: utf-8 -*-
"""便 SV10: SV7 の貯めた行の後ろに、文の席が拾った数を 1 つ 1 行で足す(封 explore/sv10/SEAL.md §1)。

使い方: python3 -I build_sv10.py <SV7 の根> <SV10 の根>
<SV10 の根>/out{n}/文の数.json を読み、<SV10 の根>/r1/store{n}/貯め.csv と r1/map{n}.json を書く。
文の行の map は {"file", "行", "列": 0, "文": true, "値", "札": {期・単位・性質・範囲}}。
"""
import csv
import json
import os
import shutil
import sys

NUMS = ["15", "16", "17"]


def period_text(p):
    if not isinstance(p, dict):
        return ""
    if p.get("種類") == "期間":
        return "期間 %s〜%s" % (p.get("始まり"), p.get("終わり"))
    if p.get("種類") == "時点":
        return "時点 %s" % p.get("日")
    return ""


def main():
    sv7, root = sys.argv[1], sys.argv[2]
    for n in NUMS:
        d = os.path.join(root, "r1", "store" + n)
        os.makedirs(d, exist_ok=True)
        src_csv = os.path.join(sv7, "r1", "store" + n, "貯め.csv")
        with open(src_csv, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        with open(os.path.join(sv7, "r1", "map%s.json" % n), encoding="utf-8") as f:
            mp = json.load(f)
        num = max(int(k) for k in mp)
        with open(os.path.join(root, "out" + n, "文の数.json"), encoding="utf-8") as f:
            picked = json.load(f).get("数") or []
        added = 0
        for x in picked:
            v = x.get("値")
            if not isinstance(v, int) or isinstance(v, bool):
                continue
            num += 1
            added += 1
            tag = {k: x.get(k) for k in ("期", "単位", "性質", "範囲")}
            mp[str(num)] = {"file": os.path.basename(str(x.get("file"))), "行": x.get("行"), "列": 0, "文": True, "値": v, "札": tag}
            rows.append([num, os.path.splitext(os.path.basename(str(x.get("file"))))[0], x.get("何の数") or "", "", v,
                         period_text(tag["期"]), tag["単位"] or "", tag["性質"] or "", tag["範囲"] or ""])
        with open(os.path.join(d, "貯め.csv"), "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
        with open(os.path.join(root, "r1", "map%s.json" % n), "w", encoding="utf-8") as f:
            json.dump(mp, f, ensure_ascii=False)
        print(n, "足した行", added)


if __name__ == "__main__":
    main()
