# -*- coding: utf-8 -*-
"""便 SV1: 札の付いた file から貯めた行(貯め.csv)を作る(封 explore/sv1/SEAL.md §1)。

使い方: python3 -I build_store.py <sv0 の tally.py の folder> <SV0 の素材と席の出力の根> <出力の根>
出力: <出力の根>/store{9,10,11}/貯め.csv(席に渡す)と <出力の根>/map{9,10,11}.json(番号 → 升。司令塔だけ)。
"""
import csv
import json
import os
import sys

sys.path.insert(0, sys.argv[1])
import tally  # noqa: E402  SV0 の照合(数の読み方・札の決め方)をそのまま使う


def period_text(p):
    if not p:
        return ""
    if p.get("種類") == "期間":
        return "期間 %s〜%s" % (p.get("始まり"), p.get("終わり"))
    if p.get("種類") == "時点":
        return "時点 %s" % p.get("日")
    return ""


def main():
    root, out = sys.argv[2], sys.argv[3]
    for num in tally.COMPANIES:
        co = tally.Company(root, num)
        rows, mp, n = [], {}, 0
        for name in sorted(co.tags):
            tag = co.tags[name]
            if tag.get("扱い") != "貯める":
                continue
            t = co.table(name)
            if t is None:
                continue
            for r, line in enumerate(t, 1):
                head_row = " / ".join(x.strip() for x in line if x.strip() and tally.cell_number(x) is None)
                for c, text in enumerate(line, 1):
                    v = tally.cell_number(text)
                    if v is None:
                        continue
                    above = [t[i][c - 1].strip() for i in range(r - 1)
                             if c <= len(t[i]) and t[i][c - 1].strip() and tally.cell_number(t[i][c - 1]) is None]
                    lab = co.label({"file": name, "行": r, "列": c})
                    n += 1
                    mp[n] = {"file": name, "行": r, "列": c}
                    rows.append([n, os.path.splitext(name)[0], head_row, " / ".join(above[-2:]), v,
                                 period_text(lab.get("期")), lab.get("単位") or "",
                                 lab.get("性質") or "", lab.get("範囲") or ""])
        d = os.path.join(out, "store" + num)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "貯め.csv"), "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["番号", "表", "行の見出し", "列の見出し", "値", "期", "単位", "性質", "範囲"])
            w.writerows(rows)
        with open(os.path.join(out, "map%s.json" % num), "w", encoding="utf-8") as f:
            json.dump(mp, f, ensure_ascii=False)
        print(num, len(rows))


if __name__ == "__main__":
    main()
