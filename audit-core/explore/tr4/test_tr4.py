# -*- coding: utf-8 -*-
"""便 TR4 の単体試験(封の前提)。判定 judge_tr4 と、数を拾う numbers_tr4。値は全部作り物。

走らせ方: cd explore/tr4 && python3 -I -m unittest test_tr4 -v
判定の試験は、TR0 と TR3 で言い過ぎが漏れた形(増減額の読み違い・前期の値の読み違い・別の項目への結び付き・
表の人数・増減率)を、作り物の値で写したもの。どれも「正しい数」と判定されないといけない。
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_tr4 as J  # noqa: E402
import numbers_tr4 as N  # noqa: E402

MAT = {("売上高", "当期"): 4629400000, ("売上高", "前期"): 4000000000,
       ("営業利益", "当期"): -330200000, ("営業利益", "前期"): -299400000,
       ("経常利益", "当期"): 1326000000, ("当期純利益", "当期"): 250000000,
       ("短期借入金", "当期末"): 800000000, ("長期借入金", "当期末"): 635520000,
       ("純資産合計", "当期末"): 4070000000, ("純資産合計", "前期末"): 4370000000,
       ("期末の従業員数", "当期末"): 150, ("売上高_丸め", "当期"): 0}
MAT.pop(("売上高_丸め", "当期"))
TRUNC = {("売上高", "当期"): 21728642000, ("売上高", "前期"): 20000000000}


class TestJudge(unittest.TestCase):
    def test_signature_takes_no_reading(self):
        # 判定は拾った読み(項目・期・種類)も札も受け取らない
        self.assertEqual(list(inspect.signature(J.matches).parameters), ["text", "value", "unit", "mat"])

    def test_value(self):
        self.assertTrue(J.is_correct("4,629", 4629, "百万円", MAT))
        self.assertTrue(J.is_correct("4,629,400", 4629400, "千円", MAT))

    def test_difference_read_as_value(self):
        # TR0 の 23・TR3 の 18 の形: 増減額(「629 百万円の増収」「赤字幅が 31 百万円拡大」)
        self.assertTrue(J.is_correct("629", 629, "百万円", MAT))
        self.assertTrue(J.is_correct("31", 31, "百万円", MAT))
        self.assertTrue(J.is_correct("300", 300, "百万円", MAT))  # 純資産の減少

    def test_prior_read_as_current(self):
        # TR3 の 6 の形: 「前期の売上高 4,000 百万円」「前期の営業損失 299 百万円」
        self.assertTrue(J.is_correct("4,000", 4000, "百万円", MAT))
        self.assertTrue(J.is_correct("299", 299, "百万円", MAT))

    def test_other_item(self):
        # TR3 の 2 の形: 「借入金は短期 800 百万円、長期 636 百万円」
        self.assertTrue(J.is_correct("800", 800, "百万円", MAT))
        self.assertTrue(J.is_correct("636", 636, "百万円", MAT))

    def test_people_in_table(self):
        # TR3 の 1 の形: 表の「(人)」。人数として正しい
        self.assertTrue(J.is_correct("150", 150, "人", MAT))
        self.assertFalse(J.is_correct("151", 151, "人", MAT))

    def test_ratio(self):
        self.assertTrue(J.is_correct("15.7", 15.7, "%", MAT))      # 売上高の増減率 15.735…
        self.assertTrue(J.is_correct("10.3", 10.3, "%", MAT))      # 営業損失の拡大率 10.28…(四捨五入)
        self.assertTrue(J.is_correct("6.9", 6.9, "%", MAT))        # 純資産の減少率 6.86…
        self.assertFalse(J.is_correct("15.9", 15.9, "%", MAT))

    def test_sign_is_ignored(self):
        self.assertTrue(J.is_correct("△330", -330, "百万円", MAT))

    def test_wrong_numbers(self):
        self.assertFalse(J.is_correct("4,631", 4631, "百万円", MAT))
        self.assertFalse(J.is_correct("629", 629, "千円", MAT))
        self.assertFalse(J.is_correct("1,327", 1327, "百万円", MAT))

    def test_round_and_truncate(self):
        self.assertTrue(J.is_correct("21,729", 21729, "百万円", TRUNC))
        self.assertTrue(J.is_correct("21,728", 21728, "百万円", TRUNC))
        self.assertFalse(J.is_correct("21,727", 21727, "百万円", TRUNC))


DOC = """# 業績の説明(第 31 社)

対象期間: 2025年7月1日〜2026年6月30日(2025-07-01 から)

## 1. 損益の状況

(単位: 百万円)

| 項目 | 当期 | 前期 | 増減 | 増減率 |
|---|---:|---:|---:|---:|
| 売上高 | 4,629 | 4,000 | +629 | +15.7% |
| 営業利益 | △330 | △299 | △31 | 赤字幅 10.3% 拡大 |
| 期末の従業員数(人) | 150 | ― | ― | ― |

当期の売上高は 4,629 百万円となりました。
売上高は前年同期比 15.7% 増の 4,629 百万円でした。
売上高は前年同期比で増加し、4,629 百万円となりました。
営業利益は前期の 1,493 百万円に対し 1,321 百万円にとどまりました。
前期の当期純利益 250 百万円に対し、増益となりました。
経常利益は 1,326 百万円です。
"""


def find(recs, line_no, text):
    return next(r for r in recs if r["行"] == line_no and r["字"] == text)


class TestNumbers(unittest.TestCase):
    def setUp(self):
        self.recs = N.extract_all(DOC)
        self.lines = DOC.split("\n")

    def line_of(self, start):
        return next(i for i, l in enumerate(self.lines) if l.startswith(start))

    def test_table_change_columns_are_extracted(self):
        # TR3 で拾わなかった 11 の形: +・%・赤字幅 Z% 拡大
        li = self.line_of("| 売上高")
        got = [r["字"] for r in self.recs if r["行"] == li]
        self.assertEqual(got, ["4,629", "4,000", "+629", "+15.7"])
        self.assertEqual(find(self.recs, li, "+15.7")["単位"], "%")
        self.assertEqual(find(self.recs, li, "+629")["単位"], "百万円")
        li2 = self.line_of("| 営業利益")
        self.assertEqual([r["字"] for r in self.recs if r["行"] == li2], ["△330", "△299", "△31", "10.3"])
        self.assertEqual(find(self.recs, li2, "△31")["値"], -31)

    def test_people_unit_from_row_label(self):
        li = self.line_of("| 期末の従業員数")
        self.assertEqual(find(self.recs, li, "150")["単位"], "人")

    def test_dates_and_numbering_are_excluded(self):
        for start in ("# 業績", "対象期間", "## 1."):
            li = self.line_of(start)
            self.assertEqual([r["字"] for r in self.recs if r["行"] == li], [], start)

    def test_period_conflict(self):
        li = self.line_of("当期の売上高")
        r = find(self.recs, li, "4,629")
        self.assertEqual(N.conflicts(r, {"項目": "売上高", "期": "前期", "種類": "金額"}), [("期の字", "当期")])
        self.assertEqual(N.conflicts(r, {"項目": "売上高", "期": "当期", "種類": "金額"}), [])

    def test_comparison_word_is_not_period(self):
        li = self.line_of("売上高は前年同期比")
        r = find(self.recs, li, "4,629")
        self.assertEqual(N.conflicts(r, {"項目": "売上高", "期": "当期", "種類": "金額"}), [])
        # 比べる字と数の間に別の数が無い形
        li2 = self.line_of("売上高は前年同期比で増加し")
        r2 = find(self.recs, li2, "4,629")
        self.assertEqual(N.conflicts(r2, {"項目": "売上高", "期": "当期", "種類": "金額"}), [])

    def test_prior_then_current_in_one_sentence(self):
        li = self.line_of("営業利益は前期の")
        self.assertEqual(N.conflicts(find(self.recs, li, "1,321"), {"項目": "営業利益", "期": "当期", "種類": "金額"}), [])
        self.assertEqual(N.conflicts(find(self.recs, li, "1,493"), {"項目": "営業利益", "期": "前期", "種類": "金額"}), [])
        self.assertEqual(N.conflicts(find(self.recs, li, "1,493"), {"項目": "営業利益", "期": "当期", "種類": "金額"}),
                         [("期の字", "前期")])

    def test_item_word_inside_period_word(self):
        # 「当期純利益」の「当期」を期の字と読まない
        li = self.line_of("前期の当期純利益")
        r = find(self.recs, li, "250")
        self.assertEqual(N.conflicts(r, {"項目": "当期純利益", "期": "前期", "種類": "金額"}), [])

    def test_item_conflict(self):
        li = self.line_of("経常利益は")
        r = find(self.recs, li, "1,326")
        self.assertEqual(N.conflicts(r, {"項目": "売上高", "期": "当期", "種類": "金額"}), [("項目の字", "経常利益")])
        self.assertEqual(N.conflicts(r, {"項目": "経常利益", "期": "当期", "種類": "金額"}), [])

    def test_table_period_from_header(self):
        li = self.line_of("| 売上高")
        r = find(self.recs, li, "4,000")
        self.assertEqual(N.conflicts(r, {"項目": "売上高", "期": "当期", "種類": "金額"}), [("期の字", "前期")])

    def test_snippet(self):
        li = self.line_of("当期の売上高")
        self.assertIn("当期の売上高は 4,629 百万円", N.snippet(DOC, find(self.recs, li, "4,629")))


if __name__ == "__main__":
    unittest.main()
