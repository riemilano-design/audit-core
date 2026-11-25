# -*- coding: utf-8 -*-
"""便 TR11 の単体試験(封の前提)。値は作り物。走らせ方: python3 -E test_tr11.py <audit-core>"""
import os
import sys
import unittest

AC = sys.argv.pop(1)
for d in ("tr2", "tr4", "tr5", "tr6", "tr7", "tr8", "tr9", "tr10"):
    sys.path.insert(0, os.path.join(AC, "explore", d))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flow_tr11 as F  # noqa: E402
import reconf9 as R9  # noqa: E402
import ledger9 as G9  # noqa: E402
import test_tr10 as T10  # noqa: E402

sys.argv.insert(1, AC)
import test_tr9 as T9  # noqa: E402  (import の時に argv[1] を取る)


class T(unittest.TestCase):
    def test_sign_mark_once_per_source(self):
        srcs = dict(T10.SRCS)
        srcs["売上高@当期"] = [{"シート": "PL", "行": "売上", "何番目": 1, "列": "当期", "升の値": 5000000000, "符号": 1},
                         {"シート": "PL", "行": "売上値引", "何番目": 1, "列": "当期", "升の値": 370600000, "符号": -1}]
        rows = F.K.check_doc(T10.DOC, T10.TAGS, T10.LEDGER, srcs)
        h = F.report11(51, rows, "x")
        self.assertIn("升の値 370600000(引く)", h)
        self.assertNotIn("(引く)(引く)", h)
        self.assertNotIn("升の値 5000000000(引く)", h)

    def test_fixed_mark_is_per_item(self):
        srcs = dict(T10.SRCS)
        dep = {"シート": "PL", "行": "減価償却費", "何番目": 1, "列": "当期", "升の値": 1000, "符号": 1}
        srcs["売上高@当期"] = [dict(dep, 行="売上", 升の値=4629400000), dict(dep, 符号=-1)]
        srcs["純資産合計@当期末"] = [dep]
        rows = F.K.check_doc(T10.DOC, T10.TAGS, T10.LEDGER, srcs)
        self.assertIn("純資産合計@当期末: シート「PL」・行「減価償却費」・列「当期」・升の値 1000(引く)", F.report11(51, rows, "x"))  # 封の形の欠陥
        h = F.report11b(51, rows, "x")
        self.assertIn("売上高@当期: シート「PL」・行「減価償却費」・列「当期」・升の値 1000(引く)", h)
        self.assertNotIn("純資産合計@当期末: シート「PL」・行「減価償却費」・列「当期」・升の値 1000(引く)", h)

    def test_dup_column_note_has_head_words(self):
        b = T9.dup(T9.BOOK, hint=True)
        ch = R9.diff9(T9.DEC, T9.LED, b)
        h = F.screen11(1, "s1", ch, T9.DEC, b, None, {})
        self.assertIn("1 本目「予算」・2 本目「実績」", h)
        self.assertIs(R9.note9.__name__, "note9")  # 差し替えを戻した


if __name__ == "__main__":
    unittest.main()
