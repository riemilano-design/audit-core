# -*- coding: utf-8 -*-
"""便 TR6: 止めた後の確定し直しの素材(封 §1)。TR2 の build_tr2 を変えずに読んで使う。AI を使わない。

使い方: python3 -E build_tr6.py <audit-core> <TR2 の根> <TR6 の根>
TR2 と同じ乱数で期 0〜2 を作り直し、TR2 の期 2 の file と升が全部同じことを確かめてから、期 3(翌々期の同じ様式)を足す。
変異は 9 種(TR2 の 7 種 + 意味の変わる改名 + 紛れの科目の追加)。それぞれ期 2 から作る file(確定し直す file)と、
同じ変異を期 3 に当てた file(確定し直した台帳で次に読む file)を書く。
書くもの: co{n}/{種類}/{期2|期3}/書き出し.xlsx・co{n}/正解.json(種類 → 期2・期3 の項目@期 → 円)
"""
import copy
import json
import os
import random
import sys

AC, TR2, OUT = sys.argv[1:4]
sys.argv = [sys.argv[0], OUT]
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
import build_tr2 as B  # noqa: E402
import ledger_tr2 as L  # noqa: E402

KINDS = B.KINDS + ["意味の変わる改名", "紛れの科目の追加"]


def mutate2(c, sheets, kind):
    """TR6 で足す 2 種。返すのは (新しい sheets, 変異の所, 正解の差し替え)。値は sheets の升から取る。"""
    s = copy.deepcopy(sheets)
    bs = s[c["bs"]]
    h = B.hdr_row(bs)
    lc = B.label_col(bs)
    q = 1000 if c["unit"] == "千円" else 1
    cur_j = (len(bs[h]) - 1) if not c["cur_first"] else (len(bs[h]) - 2)
    if kind == "意味の変わる改名":
        # 預金の最後の行が、同じ位置・同じ値のまま、預金でない科目(投資信託)に替わる。預金の小計の行が在れば小計から外す
        old = c["cash"][-1]
        i = B.find_row(bs, old)
        v = bs[i][cur_j]
        bs[i][lc] = "投資信託"
        if c["cash_sub"]:
            bs[B.find_row(bs, "現金及び預金合計")][cur_j] -= v
        return s, {"シート": c["bs"], "種類": "行の見出し", "字": "投資信託"}, {"現金及び預金@当期末": -v * q}
    if kind == "紛れの科目の追加":
        # 借入金の行の後に、借入金でない科目(リース債務)の行を足す。額は普通預金にも足して表を合わせる
        x = 30000000
        new = "リース債務(F社)"
        i = B.find_row(bs, c["st"][-1])
        line = ([""] if c["code"] else []) + [new] + ([0, x // q] if not c["cur_first"] else [x // q, 0])
        bs.insert(i + 1, line)
        for lab in ("普通預金", "流動資産合計", "資産合計", "流動負債合計", "負債合計", "負債純資産合計") + (("現金及び預金合計",) if c["cash_sub"] else ()):
            bs[B.find_row(bs, lab)][cur_j] += x // q
        return s, {"シート": c["bs"], "種類": "行の見出し", "字": new}, {"現金及び預金@当期末": x, "流動資産合計@当期末": x,
                                                                    "資産合計@当期末": x, "負債合計@当期末": x}
    raise ValueError(kind)


def mut(c, n, sheets, y_cur, y_prior, kind):
    if kind in B.KINDS:
        return B.mutate(c, n, sheets, y_cur, y_prior, kind)
    return mutate2(c, sheets, kind)


def same_book(sheets, path):
    got = L.load_book(path)
    if list(got) != list(sheets):
        return False
    for k, g in sheets.items():
        a = [[x for x in row] for row in g]
        b = got[k]
        for i in range(max(len(a), len(b))):
            ra = [x for x in (a[i] if i < len(a) else []) if x not in (None, "")]
            rb = [x for x in (b[i] if i < len(b) else []) if x not in (None, "")]
            if ra != rb:
                return False
    return True


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
        s2 = B.book(c, n, y1, y2)
        assert same_book(s2, os.path.join(TR2, "co%d" % n, "期2", "書き出し.xlsx")), ("期2 が TR2 と違う", n)
        for kind in B.KINDS:
            sm, _, _ = B.mutate(c, n, s2, y2, y1, kind)
            assert same_book(sm, os.path.join(TR2, "co%d" % n, "変異", kind, "書き出し.xlsx")), ("変異が TR2 と違う", n, kind)
        s3 = B.book(c, n, y2, y3)
        t2, t3 = B.truth(c, y1, y2), B.truth(c, y2, y3)
        vals, where = {}, {}
        for kind in KINDS:
            vals[kind] = {}
            for per, sh, t, yc, yp in (("期2", s2, t2, y2, y1), ("期3", s3, t3, y3, y2)):
                sm, w, fix = mut(c, n, sh, yc, yp, kind)
                B.write_xlsx(sm, os.path.join(OUT, "co%d" % n, kind, per, "書き出し.xlsx"))
                tv = dict(t)
                for k, v in fix.items():
                    tv[k] += v
                vals[kind][per] = tv
                where[kind] = w
        with open(os.path.join(OUT, "co%d" % n, "正解.json"), "w", encoding="utf-8") as f:
            json.dump({"値": vals, "変異の所": where}, f, ensure_ascii=False, indent=1)
        print(n, "期2 と TR2 の変異 7 種は TR2 の file と同じ。種類", len(KINDS))


if __name__ == "__main__":
    main()
