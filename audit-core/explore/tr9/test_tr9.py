# -*- coding: utf-8 -*-
"""便 TR9 の単体試験(封の前提)。表は作り物。走らせ方: python3 -E test_tr9.py <audit-core>"""
import copy
import os
import sys
import unittest

AC = sys.argv.pop(1)
for d in ("tr2", "tr6", "tr7", "tr8"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv.insert(1, AC)
import test_tr8 as T8  # noqa: E402  (import の時に argv[1] を取る)
import ledger8 as G8  # noqa: E402
import ledger9 as G9  # noqa: E402
import reconf9 as R9  # noqa: E402

DEC, BOOK = T8.DEC, T8.BOOK
LED = G9.make(DEC, BOOK)


def dup(book, hint=False):
    b = copy.deepcopy(book)
    for i, r in enumerate(b["BS"][2:], 2):
        r.insert(2, "当期末" if i == 2 else (None if r[1] is None else r[2] + 100))
    if hint:
        b["BS"][1] = ["(単位:千円)", None, "予算", "実績"]
    return b


class T(unittest.TestCase):
    def test_col_index(self):
        h = ["科目", "前期末", "当期末", "当期末"]
        self.assertIsNone(G9.col_index(h, "当期末"))
        self.assertEqual(G9.col_index(h, "当期末", 2), 3)
        self.assertIsNone(G9.col_index(h, "当期末", 3))
        self.assertEqual(G9.col_index(h, "前期末"), 1)

    def test_learns_only_when_all_columns_hold(self):
        b = copy.deepcopy(BOOK)
        b["BS"][6][2] = 22  # その他(流動資産)の当期末 = 現金 + 普通預金(当期末だけ)
        b["BS"][7][2] = 2 + 20 + 22
        self.assertTrue(any(r["合計"][0] == "その他" for r in G8.learn(DEC, b)))  # TR8 は拾う
        self.assertFalse(any(r["合計"][0] == "その他" for r in G9.learn(DEC, b)))  # TR9 は拾わない
        self.assertEqual(sorted(r["合計"][0] for r in G9.learn(DEC, BOOK)), ["流動負債合計", "流動資産合計"])

    def test_same_book_reads_and_swap_stops(self):
        self.assertEqual(G9.read(DEC, LED, BOOK)[0], "読めた")
        b = copy.deepcopy(BOOK)
        b["BS"][6], b["BS"][10] = b["BS"][10], b["BS"][6]
        self.assertEqual(G9.read(DEC, LED, b)[0], "止める")

    def test_dup_column_needs_ordinal(self):
        b = dup(BOOK)
        led = G9.make(DEC, b)
        self.assertEqual(G9.read(DEC, led, b)[0], "止める")
        d = copy.deepcopy(DEC)
        for it in d["項目"]:
            for c in it["成分"]:
                c["列の何番目"] = 2
        r = G9.read(d, G9.make(d, b), b)
        self.assertEqual(r[0], "読めた")
        self.assertEqual(r[1]["現金及び預金@当期末"], 22000)

    def test_apply_ordinal_and_hold(self):
        b = dup(BOOK, hint=True)
        ch = R9.diff9(DEC, LED, b)
        n = next(c["番号"] for c in ch if c["種類"] == "同じ見出しの列の追加")
        rest = {c["番号"]: c["案"] for c in ch if c["番号"] != n}
        d, bad = R9.apply(DEC, ch, {**rest, n: {"列の何番目": 2}})
        self.assertEqual(bad, [])
        self.assertEqual(G9.read(d, G9.make(d, b), b)[1]["短期借入金@当期末"], 4000)
        _, bad = R9.apply(DEC, ch, {**rest, n: {"保留": True}})
        self.assertEqual(bad, [(n, "保留")])

    def test_unused_row_marked(self):
        b = copy.deepcopy(BOOK)
        b["BS"][6][0] = "投資信託"  # 使わない行「その他」の 1 本目の字が変わる
        ch = R9.diff9(DEC, LED, b)
        self.assertTrue(ch[0]["使わない行だった"])
        self.assertIn("使わない行でした", R9.note9(ch[0]))
        b = copy.deepcopy(BOOK)
        b["BS"][5][0] = "投資信託"  # 使う行
        self.assertFalse(R9.diff9(DEC, LED, b)[0]["使わない行だった"])

    def test_screen_shows_head_for_dup(self):
        b = dup(BOOK, hint=True)
        ch = R9.diff9(DEC, LED, b)
        h = R9.screen9(1, "s1", ch, DEC, b, None, {})
        self.assertIn("<td>予算</td><td>実績</td>", h)


if __name__ == "__main__":
    unittest.main()
