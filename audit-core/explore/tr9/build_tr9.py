# -*- coding: utf-8 -*-
"""便 TR9: 素材(封 §1)。TR2・TR6・TR8 の build を変えずに読む。AI を使わない。

使い方: python3 -E build_tr9.py <audit-core> <TR2 の根> <TR9 の根>
TR2 と同じ乱数で期 1〜3 を作り直し、期 1・期 2 が TR2 の file と同じことを確かめてから:
  偶然の和(期 1 だけ): 貸借の表の当期末で、投資有価証券の値を機械装置 + 土地 にする(固定資産合計と資産合計も合わせる)。
      前期末の列では成り立たない。この file で台帳の検算を覚え、TR2 のふつうの期 2 を読む。
  同じ見出しの列(手がかりあり)(期 2・期 3): TR8 と同じく当期末の列の前に同じ見出しの列(予算)を足し、
      列の見出しのすぐ上の行の、その 2 列の所に「予算」「実績」と書く。読むべきは 2 本目。
  同じ見出しの列(手がかりなし)(期 2・期 3): TR8 と同じ(上の行に字を書かない)。どちらの列かは file から決まらない。
書くもの: co{n}/{種類}/{期}/書き出し.xlsx・co{n}/正解.json
"""
import json
import os
import random
import sys

AC, TR2, OUT = sys.argv[1:4]
sys.argv = [sys.argv[0], OUT]
for d in ("tr2", "tr6", "tr8"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
import build_tr2 as B  # noqa: E402
sys.argv = [sys.argv[0], AC, TR2, OUT]
import build_tr6 as B6  # noqa: E402
sys.argv = [sys.argv[0], AC, TR2, OUT]  # build_tr6 が引数を書き換えるので、build_tr8 の前に並べ直す
import build_tr8 as B8  # noqa: E402


def accidental(c, sheets):
    s = {k: [list(r) for r in v] for k, v in sheets.items()}
    bs = s[c["bs"]]
    h = B.hdr_row(bs)
    j = (len(bs[h]) - 1) if not c["cur_first"] else (len(bs[h]) - 2)
    r = {lab: B.find_row(bs, lab) for lab in ("機械装置", "土地", "投資有価証券", "固定資産合計", "資産合計")}
    new = bs[r["機械装置"]][j] + bs[r["土地"]][j]
    delta = new - bs[r["投資有価証券"]][j]
    bs[r["投資有価証券"]][j] = new
    bs[r["固定資産合計"]][j] += delta
    bs[r["資産合計"]][j] += delta
    return s


def dup_col(c, sheets, hint):
    s = B8.mutate8(c, sheets, "同じ見出しの列の追加")
    if hint:
        bs = s[c["bs"]]
        h = B.hdr_row(bs)
        j = (len(bs[h]) - 2) if not c["cur_first"] else (len(bs[h]) - 3)  # 足した後の予算の列
        row = bs[h - 1]
        row += [None] * (j + 2 - len(row))
        row[j], row[j + 1] = "予算", "実績"
    return s


def main():
    for n in B.NUMS:
        c = B.CFG[n]
        rng = random.Random(n)
        S = rng.randint(800, 5000) * 1000000
        f1 = rng.uniform(0.92, 1.15)
        f2 = f1 * rng.uniform(0.92, 1.15)
        y0, y1, y2 = B.year(rng, c, S, 1.0), B.year(rng, c, S, f1), B.year(rng, c, S, f2)
        f3 = f2 * rng.uniform(0.92, 1.15)
        y3 = B.year(rng, c, S, f3)
        s1, s2, s3 = B.book(c, n, y0, y1), B.book(c, n, y1, y2), B.book(c, n, y2, y3)
        assert B6.same_book(s1, os.path.join(TR2, "co%d" % n, "期1", "書き出し.xlsx")), n
        assert B6.same_book(s2, os.path.join(TR2, "co%d" % n, "期2", "書き出し.xlsx")), n
        root = os.path.join(OUT, "co%d" % n)
        B.write_xlsx(accidental(c, s1), os.path.join(root, "偶然の和", "期1", "書き出し.xlsx"))
        vals = {"偶然の和": {"期2": B.truth(c, y1, y2)}}
        for kind, hint in (("同じ見出しの列(手がかりあり)", True), ("同じ見出しの列(手がかりなし)", False)):
            vals[kind] = {}
            for per, sh, t in (("期2", s2, B.truth(c, y1, y2)), ("期3", s3, B.truth(c, y2, y3))):
                B.write_xlsx(dup_col(c, sh, hint), os.path.join(root, kind, per, "書き出し.xlsx"))
                vals[kind][per] = t
        with open(os.path.join(root, "正解.json"), "w", encoding="utf-8") as f:
            json.dump({"値": vals}, f, ensure_ascii=False, indent=1)
        print(n, "期1・期2 は TR2 と同じ", list(vals))


if __name__ == "__main__":
    main()
