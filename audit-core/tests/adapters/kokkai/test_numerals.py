# -*- coding: utf-8 -*-
import unittest

from adapters.kokkai import numerals as N


class ParseNumberTest(unittest.TestCase):
    def test_place_value_forms(self):
        self.assertEqual(N.parse_number("三百億"), 3e10)
        self.assertEqual(N.parse_number("千五百"), 1500.0)
        self.assertEqual(N.parse_number("一兆二千億"), 1.2e12)
        self.assertEqual(N.parse_number("二十四"), 24.0)
        self.assertEqual(N.parse_number("十"), 10.0)

    def test_positional_forms(self):
        self.assertEqual(N.parse_number("一九九一"), 1991.0)
        self.assertEqual(N.parse_number("一五"), 15.0)
        self.assertEqual(N.parse_number("二〇二二"), 2022.0)
        self.assertEqual(N.parse_number("八"), 8.0)

    def test_decimal_with_and_without_big_unit(self):
        self.assertEqual(N.parse_number("一・一兆"), 1.1e12)
        self.assertEqual(N.parse_number("二十八・五兆"), 2.85e13)
        self.assertAlmostEqual(N.parse_number("百七十七・七"), 177.7)

    def test_arabic_digits_half_and_full_width(self):
        self.assertEqual(N.parse_number("15"), 15.0)
        self.assertEqual(N.parse_number("１５"), 15.0)

    def test_unreadable_returns_none(self):
        self.assertIsNone(N.parse_number("円"))
        self.assertIsNone(N.parse_number(""))
        self.assertIsNone(N.parse_number(None))
        self.assertIsNone(N.parse_number("三百億円"))  # 単位つきは parse_number の外(number_tokens の仕事)


class NumberTokensTest(unittest.TestCase):
    def test_tokens_carry_normalized_units(self):
        toks = N.number_tokens("三百億円で一五パーセント、二カ月で三案。")
        self.assertEqual([(v, u) for v, u, _ in toks],
                         [(3e10, "円"), (15.0, "％"), (2.0, "か月"), (3.0, "案")])

    def test_token_without_unit_has_none(self):
        toks = N.number_tokens("一つの案")
        self.assertEqual([(v, u) for v, u, _ in toks], [(1.0, None)])

    def test_raw_is_the_matched_text(self):
        toks = N.number_tokens("一・一兆円")
        self.assertEqual(toks[0][2], "一・一兆円")

    def test_normalize_unit(self):
        self.assertEqual(N.normalize_unit("パーセント"), "％")
        self.assertEqual(N.normalize_unit("%"), "％")
        self.assertEqual(N.normalize_unit(" 円 "), "円")
        self.assertIsNone(N.normalize_unit(""))
        self.assertIsNone(N.normalize_unit(None))


class Round2UnitsTest(unittest.TestCase):
    """2 回目(計画 KOKKAI_DEMO_ROUND2_PLAN §1)の U1・U2。"""

    def test_u1_units_from_round1_holes(self):
        toks = N.number_tokens("四十五隻が入域し、五十九時間の審議、十二基の原発。")
        self.assertEqual([(v, u) for v, u, _ in toks], [(45.0, "隻"), (59.0, "時間"), (12.0, "基")])

    def test_u2_wari_is_also_percent(self):
        toks = N.number_tokens("約八割を長期契約で")
        self.assertEqual([(v, u) for v, u, _ in toks], [(8.0, "割"), (80.0, "％")])

    def test_u2_mei_is_hito(self):
        self.assertEqual(N.normalize_unit("名"), "人")
        toks = N.number_tokens("八十三名を派遣")
        self.assertEqual([(v, u) for v, u, _ in toks], [(83.0, "人")])

    def test_round1_tokens_are_unchanged(self):
        toks = N.number_tokens("三百億円で一五パーセント、二カ月で三案。")
        self.assertEqual([(v, u) for v, u, _ in toks], [(3e10, "円"), (15.0, "％"), (2.0, "か月"), (3.0, "案")])


class LongestUnitWinsTest(unittest.TestCase):
    """監査の REVISE(2 回目、2026-10-14): 短い単位が長い単位の接頭辞になる組(人/人分、世帯/世帯分、
    か月/か月分、年/年度、市/市町村、社/社員、項/項目、トン/トン分、キロ/キロメートル・キロワット)は
    2 回目で初めて生まれた。長い方が勝つことを 1 組ずつ留める。"""

    CASES = (
        ("五十世帯分を対象に", (50.0, "世帯分")),
        ("百人分の食料", (100.0, "人分")),
        ("三か月分の備蓄", (3.0, "か月分")),
        ("令和八年度の予算", (8.0, "年度")),
        ("千七百十八市町村", (1718.0, "市町村")),
        ("二百社員が", (200.0, "社員")),
        ("五項目の要望", (5.0, "項目")),
        ("十トン分の燃料", (10.0, "トン分")),
        ("三キロメートル先", (3.0, "キロメートル")),
        ("二十キロワットの発電", (20.0, "キロワット")),
    )

    def test_longest_unit_wins_over_its_prefix(self):
        for text, expected in self.CASES:
            toks = [(v, u) for v, u, _ in N.number_tokens(text)]
            self.assertEqual(toks[:1], [expected], text)

    def test_short_unit_still_works_alone(self):
        self.assertEqual([(v, u) for v, u, _ in N.number_tokens("五十世帯が")], [(50.0, "世帯")])
        self.assertEqual([(v, u) for v, u, _ in N.number_tokens("八年が")], [(8.0, "年")])
