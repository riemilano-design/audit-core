# -*- coding: utf-8 -*-
"""便 TR8: 新しい穴を試す素材(封 §1)。TR2 の build_tr2 と TR6 の build_tr6 を変えずに読む。AI を使わない。

使い方: python3 -E build_tr8.py <audit-core> <TR2 の根> <TR8 の根>
TR2 と同じ乱数で期 2 を作り直し、TR2 の期 2 の file と同じことを確かめてから、期 2 に 1 つずつ当てる:
  同じ見出しの列の追加(6 社): 貸借の表の当期末の列の前に、同じ見出しの列(予算の値。当期末の 1.05 倍)を足す。
  値の入れ替わり(6 社): 貸借の表の、預金の最後の行と短期借入金の最初の行の値を入れ替える(行の見出しはそのまま)。
  同じ字の行の入れ替え(第 56 社だけ): 貸借の表の 2 つの「その他」の行を丸ごと入れ替える。
正解は期 2 の値(入れ替わった file も、本来の値は期 2)。書くもの: co{n}/{種類}/期2/書き出し.xlsx・co{n}/正解.json
"""
import copy
import json
import os
import random
import sys

AC, TR2, OUT = sys.argv[1:4]
sys.argv = [sys.argv[0], OUT]
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, os.path.join(AC, "explore", "tr6"))
import build_tr2 as B  # noqa: E402
import build_tr6 as B6  # noqa: E402

KINDS = ["同じ見出しの列の追加", "値の入れ替わり", "同じ字の行の入れ替え"]


def mutate8(c, sheets, kind):
    s = copy.deepcopy(sheets)
    bs = s[c["bs"]]
    h = B.hdr_row(bs)
    lc = B.label_col(bs)
    if kind == "同じ見出しの列の追加":
        j = (len(bs[h]) - 1) if not c["cur_first"] else (len(bs[h]) - 2)
        for i, row in enumerate(bs):
            if i < h:
                continue
            if i == h:
                row.insert(j, row[j])
            elif len(row) > j:
                x = row[j]
                row.insert(j, int(round(x * 1.05)) if isinstance(x, int) else None)
        return s
    if kind == "値の入れ替わり":
        a, b = B.find_row(bs, c["cash"][-1]), B.find_row(bs, c["st"][0])
        for j in range(len(bs[a])):
            if j != lc and not (c["code"] and j == 0):
                bs[a][j], bs[b][j] = bs[b][j], bs[a][j]
        return s
    if kind == "同じ字の行の入れ替え":
        idx = [i for i, row in enumerate(bs) if i > h and len(row) > lc and row[lc] == "その他"]
        a, b = idx[0], idx[1]
        bs[a], bs[b] = bs[b], bs[a]
        return s
    raise ValueError(kind)


def main():
    for n in B.NUMS:
        c = B.CFG[n]
        rng = random.Random(n)
        S = rng.randint(800, 5000) * 1000000
        f1 = rng.uniform(0.92, 1.15)
        f2 = f1 * rng.uniform(0.92, 1.15)
        y0, y1, y2 = B.year(rng, c, S, 1.0), B.year(rng, c, S, f1), B.year(rng, c, S, f2)
        s2 = B.book(c, n, y1, y2)
        assert B6.same_book(s2, os.path.join(TR2, "co%d" % n, "期2", "書き出し.xlsx")), ("期2 が TR2 と違う", n)
        t2 = B.truth(c, y1, y2)
        kinds = [k for k in KINDS if k != "同じ字の行の入れ替え" or c["dup"]]
        for kind in kinds:
            B.write_xlsx(mutate8(c, s2, kind), os.path.join(OUT, "co%d" % n, kind, "期2", "書き出し.xlsx"))
        with open(os.path.join(OUT, "co%d" % n, "正解.json"), "w", encoding="utf-8") as f:
            json.dump({"値": {k: {"期2": t2} for k in kinds}}, f, ensure_ascii=False, indent=1)
        print(n, kinds)


if __name__ == "__main__":
    main()
