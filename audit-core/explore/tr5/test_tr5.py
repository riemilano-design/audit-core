# -*- coding: utf-8 -*-
"""便 TR5 の単体試験(封の前提)。値は全部作り物。走らせ方: python3 -I test_tr5.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tr4"))
import rules_tr5 as T  # noqa: E402
import numbers_tr4 as N  # noqa: E402
import judge_tr4 as J  # noqa: E402

DOC = """# 業績(第 31 社)

(単位: 百万円)

| 項目 | 当期 | 前期 |
|---|---:|---:|
| 売上高 | 4,629 | 4,000 |
| 期末の従業員数(人) | 150 | ― |

売上高は 4,000 百万円となり、前期の 4,000 百万円から横ばいでした。
売上高は 4,629 百万円となり、前期の 4,000 百万円に比べ増えました。
純資産合計は 4,370 百万円となりました。
前期末の純資産合計は 4,370 百万円でした。
売上高は 4,629 百万円でした。前期の売上高は 4,000 百万円でした。
"""


def line_of(start):
    return next(i for i, l in enumerate(DOC.split("\n")) if l.startswith(start))


RECS = N.extract_all(DOC)


def rec(line, text, k=1):
    return [r for r in RECS if r["行"] == line and r["字"] == text][k - 1]


def tag(item, per, kind="金額"):
    return {"項目": item, "期": per, "種類": kind}


class TestR2(unittest.TestCase):
    def test_prior_without_word_is_stopped(self):
        # TR4 の期の隠しの形: 「純資産合計は X となり」に前期末の札
        r = rec(line_of("純資産合計は"), "4,370")
        self.assertTrue(T.r2(r, tag("純資産合計", "前期末"))[0])

    def test_prior_with_word_passes(self):
        r = rec(line_of("前期末の純資産合計"), "4,370")
        self.assertFalse(T.r2(r, tag("純資産合計", "前期末"))[0])
        r = rec(line_of("売上高は 4,629 百万円となり"), "4,000")
        self.assertFalse(T.r2(r, tag("売上高", "前期"))[0])

    def test_current_tag_not_touched(self):
        r = rec(line_of("純資産合計は"), "4,370")
        self.assertFalse(T.r2(r, tag("純資産合計", "当期末"))[0])

    def test_change_tag_not_touched(self):
        r = rec(line_of("純資産合計は"), "4,370")
        self.assertFalse(T.r2(r, tag("純資産合計", "前期末", "増減額"))[0])

    def test_table_prior_column_passes(self):
        r = rec(line_of("| 売上高"), "4,000")
        self.assertFalse(T.r2(r, tag("売上高", "前期"))[0])


class TestR1(unittest.TestCase):
    def test_two_prior_tags_in_one_sentence(self):
        li = line_of("売上高は 4,000 百万円となり")
        a, b = rec(li, "4,000", 1), rec(li, "4,000", 2)
        got = T.r1(DOC, [(a, tag("売上高", "前期"), "x"), (b, tag("売上高", "前期"), "y")])
        self.assertEqual(got, {"x", "y"})

    def test_current_and_prior_pass(self):
        li = line_of("売上高は 4,629 百万円となり")
        a, b = rec(li, "4,629"), rec(li, "4,000")
        self.assertEqual(T.r1(DOC, [(a, tag("売上高", "当期"), "x"), (b, tag("売上高", "前期"), "y")]), set())

    def test_different_sentences_pass(self):
        li = line_of("売上高は 4,629 百万円でした。")
        a, b = rec(li, "4,629"), rec(li, "4,000")
        self.assertEqual(T.r1(DOC, [(a, tag("売上高", "前期"), "x"), (b, tag("売上高", "前期"), "y")]), set())


class TestUnitFromText(unittest.TestCase):
    def test_people_in_table(self):
        # TR3 の表の従業員数 150 の形。本文の単位は人
        li = line_of("| 期末の従業員数")
        s = DOC.split("\n")[li].index("150")
        self.assertEqual(T.unit_at(DOC, li, s), "人")
        self.assertTrue(J.is_correct("150", 150, T.unit_at(DOC, li, s), {("期末の従業員数", "当期末"): 150}))

    def test_money_in_text(self):
        li = line_of("純資産合計は")
        s = DOC.split("\n")[li].index("4,370")
        self.assertEqual(T.unit_at(DOC, li, s), "百万円")

    def test_none_when_not_a_number(self):
        self.assertIsNone(T.unit_at(DOC, 0, 0))


if __name__ == "__main__":
    unittest.main()
