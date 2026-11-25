# -*- coding: utf-8 -*-
"""便 TR8 の単体試験(封の前提)。表は作り物。走らせ方: python3 -E test_tr8.py <audit-core>"""
import copy
import os
import sys
import unittest

AC = sys.argv.pop(1)
for d in ("tr2", "tr6", "tr7"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_tr2 as L  # noqa: E402
import ledger8 as G  # noqa: E402
import reconf8 as R8  # noqa: E402

BOOK = {"BS": [["貸借対照表"], ["(単位:千円)"], ["科目", "前期末", "当期末"],
               ["流動資産", None, None], ["現金", 1, 2], ["普通預金", 10, 20], ["その他", 4, 5], ["流動資産合計", 15, 27],
               ["流動負債", None, None], ["短期借入金", 3, 4], ["その他", 6, 9], ["流動負債合計", 9, 13]]}
DEC = {"シート": {"BS": {"使う": True, "見出しの行": 3, "行の見出しの列": "科目", "単位": "千円"}},
       "項目": [{"項目": "現金及び預金", "期": "当期末", "成分": [{"シート": "BS", "行": "現金", "何番目": 1, "列": "当期末", "符号": 1},
                                                          {"シート": "BS", "行": "普通預金", "何番目": 1, "列": "当期末", "符号": 1}]},
               {"項目": "短期借入金", "期": "当期末", "成分": [{"シート": "BS", "行": "短期借入金", "何番目": 1, "列": "当期末", "符号": 1}]}],
       "使わない行": [{"シート": "BS", "行": x, "何番目": k} for x, k in (("流動資産", 1), ("その他", 1), ("流動資産合計", 1),
                                                                 ("流動負債", 1), ("その他", 2), ("流動負債合計", 1))]}
LED = G.make(DEC, BOOK)


class T(unittest.TestCase):
    def test_learns_section_sums(self):
        tot = sorted({(r["合計"][0], r["列"]) for r in LED["検算"]})
        self.assertEqual(tot, [("流動負債合計", "前期末"), ("流動負債合計", "当期末"), ("流動資産合計", "前期末"), ("流動資産合計", "当期末")])

    def test_same_book_reads(self):
        r = G.read(DEC, LED, BOOK)
        self.assertEqual(r[0], "読めた")
        self.assertEqual(r[1]["現金及び預金@当期末"], 22000)

    def test_duplicate_label_swap_stops(self):
        b = copy.deepcopy(BOOK)
        b["BS"][6], b["BS"][10] = b["BS"][10], b["BS"][6]
        self.assertEqual(L.read(LED, b)[0], "読めた")  # TR2 の台帳は止まらない
        r = G.read(DEC, LED, b)
        self.assertEqual(r[0], "止める")
        self.assertEqual({d["規則"] for d in r[1]}, {"S6"})

    def test_value_swap_stops(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5][1:], b["BS"][9][1:] = b["BS"][9][1:], b["BS"][5][1:]
        self.assertEqual(G.read(DEC, LED, b)[0], "止める")

    def test_rounding_within_tolerance_reads(self):
        b = copy.deepcopy(BOOK)
        b["BS"][7][2] = 28  # 3 行の和 27 に 1 の差
        self.assertEqual(G.read(DEC, LED, b)[0], "読めた")
        b["BS"][7][2] = 30
        self.assertEqual(G.read(DEC, LED, b)[0], "止める")

    def test_duplicate_column_flagged_and_waits(self):
        b = copy.deepcopy(BOOK)
        for i, r in enumerate(b["BS"][2:], 2):
            r.insert(2, "当期末" if i == 2 else (None if r[1] is None else 99))
        ch = R8.diff8(DEC, LED, b)
        self.assertEqual([c["種類"] for c in ch], ["同じ見出しの列の追加"])
        self.assertIsNone(ch[0]["案"])
        self.assertEqual(R8.waiting8(DEC, ch, b), {"現金及び預金@当期末", "短期借入金@当期末"})
        led2 = G.make(DEC, b)
        self.assertEqual(G.read(DEC, led2, b)[0], "止める")  # 確定し直しても S5 が止める

    def test_added_row_notes_candidates(self):
        b = copy.deepcopy(BOOK)
        b["BS"].insert(10, ["短期借入金(F)", 0, 1])
        ch = R8.diff8(DEC, LED, b)
        self.assertEqual(ch[0]["入りうる項目"], ["現金及び預金@当期末", "短期借入金@当期末"])
        self.assertIn("未決", R8.note(ch[0]))

    def test_rename_notes_old_label_absent(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5][0] = "投資信託"
        ch = R8.diff8(DEC, LED, b)
        self.assertFalse(ch[0]["前の字が今も在る"])

    def test_screen_has_column_header(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5][0] = "投資信託"
        ch = R8.diff8(DEC, LED, b)
        h = R8.screen8(1, "s1", ch, DEC, b, None, {})
        self.assertIn("<th>前期末</th>", h)


if __name__ == "__main__":
    unittest.main()
