# -*- coding: utf-8 -*-
"""数の読み取り N(万・億の数のコンマ)の試験。封 docs/XBRL_NUMBER_READER_ENGINE_SEAL_2026-11-04.md §1・§2-1。

``extract.iter_numbers_2026_11_04`` は ``iter_numbers_2026_10_27`` を包み、「1,234万円」「12億3,456万円」「1万2,345円」を 1 つの数(円)に読む。
旗 ``numbers_man_comma_2026_11_04`` が真の profile は P29 と P29E だけ(既定 P27 は不変)。封 §1-4 の例を 1 本ずつ字で留める。
**この file の例の字と数は全部作り物**。通信しない。
"""
import dataclasses
import unittest

from adapters.xbrl import extract as E
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

from .test_recipes_p24 import contexts_for, fact, num_claims

KEY = "numbers_man_comma_2026_11_04"


def n11(s):
    return E.iter_numbers_2026_11_04(s)


class HitTest(unittest.TestCase):
    """封 §1-4: いまは読まない -> 読む。"""

    def test_1234_man(self):
        self.assertEqual([(0, 7, 12340000.0, "円", 10000.0)], n11("1,234万円"))

    def test_12_oku_3456_man(self):
        self.assertEqual([(0, 10, 1234560000.0, "円", 10000.0)], n11("12億3,456万円"))

    def test_1234_oku_5678_man(self):
        self.assertEqual([(0, 13, 123456780000.0, "円", 10000.0)], n11("1,234億5,678万円"))

    def test_decimal_man(self):
        self.assertEqual([(0, 5, 15000.0, "円", 1000.0)], n11("1.5万円"))

    def test_negative_triangle(self):
        self.assertEqual([(0, 8, -12340000.0, "円", 10000.0)], n11("△1,234万円"))

    def test_not_read_before(self):
        # 「いまは読まない」: 旗が偽の読みでは 1,234万円 は 1 つの数にならない。
        self.assertNotEqual(n11("1,234万円"), E.iter_numbers_2026_10_27("1,234万円"))
        self.assertNotIn(12340000.0, [t[2] for t in E.iter_numbers_2026_10_27("1,234万円")])


class JoinTest(unittest.TestCase):
    """封 §1-4: いまは下の桁だけ別の数として読む -> 1 つの数に。"""

    def test_man_comma_yen(self):
        s = "1万2,345円"
        self.assertEqual([(0, 8, 12345.0, "円", 1.0)], n11(s))
        # いまの読み「2,345円」は捨てる。
        self.assertIn(2345.0, [t[2] for t in E.iter_numbers_2026_10_27(s)])
        self.assertNotIn(2345.0, [t[2] for t in n11(s)])

    def test_oku_man(self):
        s = "1,234億5万円"
        self.assertEqual([(0, 9, 123400050000.0, "円", 10000.0)], n11(s))
        self.assertIn(5.0 * 1e4, [t[2] for t in E.iter_numbers_2026_10_27(s)])
        self.assertNotIn(5.0 * 1e4, [t[2] for t in n11(s)])


class MissTest(unittest.TestCase):
    """封 §1-4: 既存の読みが全部覆うので変えない。出力は ``iter_numbers_2026_10_27`` と同じ列。"""

    def check(self, s, expect=None):
        self.assertEqual(E.iter_numbers_2026_10_27(s), n11(s))
        if expect is not None:
            self.assertEqual(expect, n11(s))

    def test_12_oku(self):
        self.check("12億円", [(0, 4, 1200000000.0, "円", 100000000.0)])

    def test_12_3_oku(self):
        self.check("12.3億円", [(0, 6, 1230000000.0, "円", 10000000.0)])

    def test_1234_oku_unit_stays(self):
        # 単位が「億円」のまま(§1-3 の 1 を外すと「円」に変わって赤)。
        self.check("1,234億円", [(0, 7, 1234.0, "億円", 100000000.0)])

    def test_2cho_3471_oku(self):
        self.check("2兆3,471億円", [(0, 9, 2347100000000.0, "円", 100000000.0)])

    def test_380_oku_6sen_4hyaku_man(self):
        self.check("380億6千4百万円", [(0, 10, 38064000000.0, "円", 1000000.0)])

    def test_6man_5sen(self):
        self.check("6万5千円", [(0, 5, 65000.0, "円", 1000.0)])

    def test_148_yen_22_sen(self):
        self.check("148円22銭", [(0, 7, 148.22, "円", 0.01)])

    def test_1234_yen(self):
        # 兆・億・万のどれも無い当たりは使わない。
        self.check("1,234円", [(0, 6, 1234.0, "円", 1)])

    def test_1234_hyakuman(self):
        self.check("1,234百万円", [(0, 8, 1234.0, "百万円", 1000000.0)])

    def test_8420000_sen(self):
        self.check("8,420,000千円", [(0, 11, 8420000.0, "千円", 1000.0)])

    def test_percent(self):
        self.check("3.5%", [(0, 4, 3.5, "%", 1.0)])

    def test_people(self):
        self.check("1,234人", [(0, 6, 1234.0, "人", 1.0)])

    def test_man_then_space_yen_stays_unread(self):
        # 代価: 「1,234万 円」(空白あり)は当たらない(いまも読まない)。
        self.check("1,234万 円", [])


class WhitespaceTest(unittest.TestCase):
    def test_space_between_numbers_and_sign(self):
        # 文の中の 2 つの数: 先の「1,234万円」は 1 つの数、後の「5万円」は既存の読みが全部覆うので既存のまま。
        s = "売上は1,234万円で、前期は 5万円"
        got = n11(s)
        self.assertEqual([(3, 10, 12340000.0, "円", 10000.0)], got[:1])
        self.assertEqual(2, len(got))
        self.assertEqual((50000.0, "円", 10000.0), got[1][2:])
        self.assertEqual([t for t in E.iter_numbers_2026_10_27(s) if t[0] >= 10], got[1:])

    def test_positions_ordered(self):
        s = "A1万2,345円とB1,234万円と3.5%"
        got = n11(s)
        self.assertEqual(sorted(got, key=lambda t: t[0]), got)
        self.assertEqual([12345.0, 12340000.0, 3.5], [t[2] for t in got])
        # 封 §1-3 の 3(返す列は位置順): 新しく読む数が既存の読みの後ろ / 前に来る文。試験の本数(覆いの記録)を変えないため、同じ method の中の 2 つの場合(subTest)にした。
        for name, text, want in (
                ("new_after_existing", "5%と1,234万円", [(0, 2, 5.0, "%", 1.0), (3, 10, 12340000.0, "円", 10000.0)]),
                ("new_before_existing", "1,234万円と5%", [(0, 7, 12340000.0, "円", 10000.0), (8, 10, 5.0, "%", 1.0)])):
            with self.subTest(name):
                got = n11(text)
                self.assertEqual(sorted(t[0] for t in got), [t[0] for t in got])
                self.assertEqual(want, got)


class ProfileTest(unittest.TestCase):
    def test_flag_on_only_p29_and_p29e(self):
        self.assertTrue(getattr(V.P29, KEY))
        self.assertTrue(getattr(V.P29E, KEY))
        for p in (V.P27, V.P27E, V.P28, V.P28E):
            self.assertFalse(getattr(p, KEY), p.name)
        self.assertEqual(["P29", "P29E", "P30E", "P32E"], sorted(n for n, p in V.PROFILES.items() if getattr(p, KEY)))

    def test_registered_and_composed(self):
        self.assertIs(V.PROFILES["P29"], V.P29)
        self.assertIs(V.PROFILES["P29E"], V.P29E)
        self.assertEqual(dataclasses.replace(V.P28, name="P29", **{KEY: True}), V.P29)
        self.assertEqual(dataclasses.replace(V.P28E, name="P29E", **{KEY: True}), V.P29E)

    def test_default_is_still_p27_and_flag_defaults_false(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        self.assertIs(False, fields[KEY].default)

    def test_flag_position(self):
        order = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(order.index("numbers_2026_10_21") + 1, order.index(KEY))
        # 2026-11-04 RB(封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md §0-2 の 3)が旗 rounding_mixed_2026_11_04 をこの旗の直後に足した: この旗 → RB の旗 → written_precision_2026_10_27 の順
        self.assertEqual(order.index(KEY) + 1, order.index("rounding_mixed_2026_11_04"))
        # 2026-11-06 PB(封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §1)が旗 prior_cue_bind_2026_11_06 を RB の旗の直後に足した: この旗 → RB の旗 → PB の旗 → written_precision_2026_10_27 の順
        self.assertEqual(order.index(KEY) + 2, order.index("prior_cue_bind_2026_11_06"))
        self.assertEqual(order.index(KEY) + 3, order.index("written_precision_2026_10_27"))

    def test_flag_off_p29_equals_p28_except_name(self):
        off = dataclasses.replace(V.P29, **{KEY: False})
        self.assertEqual(dataclasses.replace(V.P28, name="P29"), off)
        off_e = dataclasses.replace(V.P29E, **{KEY: False})
        self.assertEqual(dataclasses.replace(V.P28E, name="P29E"), off_e)


class WiringTest(unittest.TestCase):
    def test_numbers_of_reads_man_comma_only_with_flag(self):
        s = "売上高は1,234万円でした。"
        self.assertEqual(n11(s), R._numbers_of(V.P29E, s))
        self.assertEqual(n11(s), R._numbers_of(V.P29, s))
        self.assertEqual([(4, 11, 12340000.0, "円", 10000.0)], R._numbers_of(V.P29E, s))
        for p in (V.P27, V.P27E, V.P28, V.P28E):
            self.assertEqual(E.iter_numbers_2026_10_27(s), R._numbers_of(p, s), p.name)
            self.assertNotIn(12340000.0, [t[2] for t in R._numbers_of(p, s)], p.name)

    def test_numbers_of_older_profiles_unchanged(self):
        s = "売上高は1,234万円でした。"
        self.assertEqual(E.iter_numbers_2026_10_21(s), R._numbers_of(V.P26, s))


class BehaviourTest(unittest.TestCase):
    """配線の振る舞い: P28E で claim にならない「1,234万円」が P29E で数の claim になり、書類の値に結ぶ。"""

    S = "売上高は1,234万円でした。"
    FS = [fact("NetSales", "CurrentYearDuration", 12340000)]

    def claims(self, p):
        return num_claims(p, self.S, self.FS, contexts_for(self.FS))

    def test_p28e_makes_no_man_comma_claim(self):
        self.assertEqual([], self.claims("P28E"))

    def test_p29e_makes_one_numeric_claim_and_grounds_it(self):
        cs = self.claims("P29E")
        self.assertEqual(1, len(cs), cs)
        c = cs[0]
        self.assertEqual(12340000.0, c["value"])
        self.assertEqual("円", c["unit"])
        self.assertEqual(10000.0, c["claim_scale"])
        self.assertEqual("売上高", c["subject"])
        self.assertEqual("GROUNDED", c["result"])

    def test_p29e_value_off_by_a_man_is_not_grounded(self):
        # 書類の値が 1,235万円なら、1,234万円は帯(万の位)の外で GROUNDED にならない。
        fs = [fact("NetSales", "CurrentYearDuration", 12350000)]
        cs = num_claims("P29E", self.S, fs, contexts_for(fs))
        self.assertEqual(1, len(cs))
        self.assertNotEqual("GROUNDED", cs[0]["result"])


if __name__ == "__main__":
    unittest.main()
