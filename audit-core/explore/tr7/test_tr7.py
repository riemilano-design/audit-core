# -*- coding: utf-8 -*-
"""便 TR7 の単体試験(封の前提)。表は TR6 の試験と同じ作り物。走らせ方: python3 -E test_tr7.py <audit-core>"""
import copy
import os
import sys
import unittest

AC = sys.argv.pop(1)
sys.path.insert(0, os.path.join(AC, "explore", "tr2"))
sys.path.insert(0, os.path.join(AC, "explore", "tr6"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv.insert(1, AC)
import test_tr6 as T6  # noqa: E402  (import の時に argv[1] を取る)
import reconf_tr6 as R  # noqa: E402
import partial_tr7 as P  # noqa: E402

DEC, LED, BOOK = T6.DEC, T6.LED, T6.BOOK
BS = {"現金及び預金@当期末", "短期借入金@当期末", "負債合計@当期末"}


def w(book):
    return P.waiting(DEC, R.diff(DEC, LED, book), book)


class T(unittest.TestCase):
    def test_column_insert_waits_nothing(self):
        b = copy.deepcopy(BOOK)
        for r in b["BS"][2:]:
            r.insert(2, "増減" if r[0] == "科目" else 0)
        self.assertEqual(w(b), set())
        self.assertEqual(P.read_some(DEC, b, BS)["現金及び預金@当期末"], 22000)

    def test_row_add_waits_whole_sheet(self):
        b = copy.deepcopy(BOOK)
        b["BS"].insert(6, ["短期借入金(F銀行)", 0, 7])
        self.assertEqual(w(b), BS)
        self.assertEqual(P.read_some(DEC, b, {"売上高@当期"}), {"売上高@当期": 100000})

    def test_column_rename_waits_users(self):
        b = copy.deepcopy(BOOK)
        b["BS"][2][2] = "当期末残高"
        self.assertEqual(w(b), BS)

    def test_unit_change_waits_sheet(self):
        b = copy.deepcopy(BOOK)
        b["BS"][1][0] = "(単位:円)"
        self.assertEqual(w(b), BS)

    def test_move_of_duplicate_label_waits(self):
        b = copy.deepcopy(BOOK)
        b["BS"].insert(4, ["その他", 0, 1])
        b["BS"].insert(8, ["その他", 0, 2])
        dec = copy.deepcopy(DEC)
        dec["使わない行"] += [{"シート": "BS", "行": "その他", "何番目": 1}, {"シート": "BS", "行": "その他", "何番目": 2}]
        led = T6.L.make_ledger(dec, b)
        b2 = copy.deepcopy(b)
        b2["BS"][4], b2["BS"][5] = b2["BS"][5], b2["BS"][4]
        ch = R.diff(dec, led, b2)
        self.assertEqual([c["種類"] for c in ch], ["行の順の変更"])
        self.assertEqual(P.waiting(dec, ch, b2), BS)

    def test_plain_move_waits_nothing(self):
        b = copy.deepcopy(BOOK)
        b["BS"][5], b["BS"][6] = b["BS"][6], b["BS"][5]
        self.assertEqual(w(b), set())


if __name__ == "__main__":
    unittest.main()
