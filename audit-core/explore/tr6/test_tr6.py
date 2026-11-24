# -*- coding: utf-8 -*-
"""便 TR6 の単体試験(封の前提)。表は全部作り物。走らせ方: python3 -I test_tr6.py <audit-core>"""
import copy
import os
import sys
import unittest

AC = sys.argv.pop(1)
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_tr2 as L  # noqa: E402
import reconf_tr6 as R  # noqa: E402

BOOK = {"BS": [["貸借対照表"], ["(単位:千円)"], ["科目", "前期末", "当期末"],
               ["現金", 1, 2], ["普通預金", 10, 20], ["短期借入金(A銀行)", 3, 4], ["買掛金", 5, 6], ["負債合計", 50, 60]],
        "PL": [["損益"], ["科目", "当期"], ["売上高", 100]]}
DEC = {"シート": {"BS": {"使う": True, "見出しの行": 3, "行の見出しの列": "科目", "単位": "千円"},
                 "PL": {"使う": True, "見出しの行": 2, "行の見出しの列": "科目", "単位": "千円"}},
       "項目": [{"項目": "現金及び預金", "期": "当期末", "成分": [{"シート": "BS", "行": "現金", "何番目": 1, "列": "当期末", "符号": 1},
                                                          {"シート": "BS", "行": "普通預金", "何番目": 1, "列": "当期末", "符号": 1}]},
               {"項目": "短期借入金", "期": "当期末", "成分": [{"シート": "BS", "行": "短期借入金(A銀行)", "何番目": 1, "列": "当期末", "符号": 1}]},
               {"項目": "負債合計", "期": "当期末", "成分": [{"シート": "BS", "行": "負債合計", "何番目": 1, "列": "当期末", "符号": 1}]},
               {"項目": "売上高", "期": "当期", "成分": [{"シート": "PL", "行": "売上高", "何番目": 1, "列": "当期", "符号": 1}]}],
       "使わない行": [{"シート": "BS", "行": "買掛金", "何番目": 1}]}
LED = L.make_ledger(DEC, BOOK)


def run(book, decisions=None):
    ch = R.diff(DEC, LED, book)
    d2, bad = R.apply(DEC, ch, R.plan_only(ch) if decisions is None else decisions(ch))
    led2 = L.make_ledger(d2, book)
    return ch, bad, L.read(led2, book)


class T(unittest.TestCase):
    def test_same_book_no_change(self):
        self.assertEqual(R.diff(DEC, LED, BOOK), [])

    def test_column_insert_one_line(self):
        b = copy.deepcopy(BOOK)
        for r in b["BS"][2:]:
            r.insert(2, "増減" if r[0] == "科目" else 0)
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["列の追加"])
        self.assertEqual(r[0], "読めた")
        self.assertEqual(r[1]["現金及び預金@当期末"], 22000)

    def test_swap_is_one_move(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5], b["BS"][6] = b["BS"][6], b["BS"][5]
        ch, bad, r = run(b)
        self.assertEqual(len(ch), 1)
        self.assertEqual(ch[0]["種類"], "行の順の変更")
        self.assertEqual(r[0], "読めた")

    def test_row_rename_plan_maps(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5][0] = "短期借入金 A銀行"
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["行の字の変更"])
        self.assertEqual(ch[0]["影響"], ["短期借入金@当期末"])
        self.assertEqual(r[1]["短期借入金@当期末"], 4000)

    def test_row_rename_unused_drops_component(self):
        b = copy.deepcopy(BOOK)
        b["BS"][4][0] = "投資信託"
        ch, bad, r = run(b, lambda ch: {ch[0]["番号"]: {"使わない": True}})
        self.assertEqual(r[0], "読めた")
        self.assertEqual(r[1]["現金及び預金@当期末"], 2000)

    def test_row_insert_needs_decision(self):
        b = copy.deepcopy(BOOK)
        b["BS"].insert(6, ["短期借入金(F銀行)", 0, 7])
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["行の追加"])
        self.assertIsNone(ch[0]["案"])
        self.assertEqual(r[0], "止める")
        ch, bad, r = run(b, lambda ch: {ch[0]["番号"]: {"項目": ["短期借入金@当期末"], "符号": 1}})
        self.assertEqual(r[1]["短期借入金@当期末"], 11000)
        ch, bad, r = run(b, lambda ch: {ch[0]["番号"]: {"使わない": True}})
        self.assertEqual(r[1]["短期借入金@当期末"], 4000)

    def test_sheet_rename(self):
        b = {("PL(2)" if k == "PL" else k): v for k, v in BOOK.items()}
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["シートの名の変更"])
        self.assertEqual(r[1]["売上高@当期"], 100000)

    def test_unit_change(self):
        b = copy.deepcopy(BOOK)
        b["BS"][1][0] = "(単位:円)"
        for r in b["BS"][3:]:
            r[1], r[2] = r[1] * 1000, r[2] * 1000
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["単位の変更"])
        self.assertEqual(r[1]["負債合計@当期末"], 60000)

    def test_column_rename(self):
        b = copy.deepcopy(BOOK)
        b["BS"][2][2] = "当期末残高"
        ch, bad, r = run(b)
        self.assertEqual([c["種類"] for c in ch], ["列の字の変更"])
        self.assertEqual(r[1]["現金及び預金@当期末"], 22000)

    def test_missing_decision_is_reported(self):
        b = copy.deepcopy(BOOK)
        b["BS"].insert(6, ["リース債務", 0, 7])
        ch = R.diff(DEC, LED, b)
        _, bad = R.apply(DEC, ch, {})
        self.assertEqual(len(bad), 1)


if __name__ == "__main__":
    unittest.main()
