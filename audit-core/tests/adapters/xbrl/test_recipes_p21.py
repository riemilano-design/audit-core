# -*- coding: utf-8 -*-
"""P21(名指しの直し)の試験。封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md §0。

P21 = P20 + 旗 ``last_branch_cues``。旗が真のときだけ、``recipes._direct_value_claim`` の
「値が一致する fact が無いときの最後の枝」(従来は CurrentYear の先頭の fact を 1 本名指すだけ)が
3 つのことを先に見る。**各直しについて「P21 で当たる」と「P20 では従来どおり」を対にして留める。**

  F1′ 期の手がかり : 数の直前が「前期は」など・増減の語が無い → Prior1Year の fact を名指す
  F2′ セグメントの枠 : セグメント利益・損失で member が取れていない → 名指さない(no_element)
  F3b 増減の文     : 増減の語があり当期の残高(Instant)を選んだ → 残高の対 [当期, 前期, formula:a-b]

合成の instance(facts と contexts を直接組む)で ``_direct_value_claim`` を呼ぶ。通信しない。
"""
import dataclasses
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

SEG = "m:ParkingSegmentMember"


def fact(name, ctx, value):
    return {"name": "jppfs_cor:" + name, "context": ctx, "unit": "JPY", "value": float(value)}


def contexts_for(facts, members=None):
    members = members or {}
    return {f["context"]: {"members": list(members.get(f["context"], []))} for f in facts}


def call(profile_name, sentence, number, unit, subj, elems, facts, member=None, members=None):
    """``sentence`` の中の ``number``(数の字面)について ``_direct_value_claim`` を呼ぶ。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None,
             "result": None, "recomputed": None}
    R._direct_value_claim(claim, sentence, a, b, 1, float(number.replace(",", "")), unit, None, subj, elems, member,
                          facts, contexts_for(facts, members), V.PROFILES[profile_name])
    return claim


class FlagShapeTest(unittest.TestCase):
    def test_p21_is_p20_plus_exactly_the_one_flag(self):
        self.assertEqual(dataclasses.replace(V.P20, name="P21", last_branch_cues=True), V.P21)
        self.assertIs(V.PROFILES["P21"], V.P21)
        self.assertFalse(V.P20.last_branch_cues)

    def test_only_p21_has_the_flag_on(self):
        # 2026-10-20 P22 = P21 + period_bind は last_branch_cues を引き継ぐ(封 XBRL_PERIOD_BIND_SEAL_2026-10-20 の追記)
        # 2026-10-21 P23 = P22 + 率の旗 + truncate_abs_band も引き継ぐ(封 XBRL_ROUNDING_SEAL_2026-10-21)
        # 2026-10-21 P24 = P23 + 旗 2 つ も引き継ぐ(封 XBRL_VOCAB_SEAL_2026-10-21)
        self.assertEqual(["P21", "P22", "P23", "P24"], sorted(n for n, p in V.PROFILES.items() if p.last_branch_cues))

    def test_the_default_profile_was_p21_from_step_2_and_is_p22_since_period_bind_step_2(self):
        """段 1(5eb80a2)では既定は P20 のままだった。段 2(2026-10-20)で P21 に切り替えた
        (封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md §0・§5。N-4・N-5 が当たったとき)。
        同じ日の期を縛る P22 の段 2(封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の E-8。人間の決定「任せる」)で既定は P22 になった。
        P22 は P21 から作るので P21 の旗は引き継がれ、P21 の字は消えていない(明示で呼べる)。"""

        self.assertEqual("P22", V.DEFAULT_PROFILE)
        self.assertIn("P21", V.PROFILES)
        self.assertTrue(V.PROFILES[V.DEFAULT_PROFILE].last_branch_cues)


class PriorCueTest(unittest.TestCase):
    """F1′ ― 「前期は…」の数は、値が合わなくても前期の fact を名指す(増減の語が無いときだけ)。"""

    def setUp(self):
        self.facts = [fact("NetSales", "CurrentYearDuration", 5000000), fact("NetSales", "Prior1YearDuration", 7000000)]

    def test_p21_names_the_prior_year_fact(self):
        c = call("P21", "売上高は、前期は999千円となった。", "999", "千円", "売上高", ["NetSales"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:NetSales@Prior1YearDuration", c["pointer"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(7000000.0, c["recomputed"])
        self.assertTrue(c["bound"])

    def test_p20_still_names_the_current_year_fact(self):
        c = call("P20", "売上高は、前期は999千円となった。", "999", "千円", "売上高", ["NetSales"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])
        self.assertEqual(5000000.0, c["recomputed"])

    def test_without_the_cue_p21_keeps_the_current_year_fact(self):
        c = call("P21", "売上高は999千円となった。", "999", "千円", "売上高", ["NetSales"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])

    def test_a_difference_word_blocks_it(self):
        """増減の語(is_diff)があれば前期の fact に寄せない ― 括弧内の前期の増減額を前期の残高に結ばないため。"""
        c = call("P21", "売上高は、前期は999千円増加した。", "999", "千円", "売上高", ["NetSales"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])

    def test_without_a_prior_fact_p21_falls_back_to_the_current_year_fact(self):
        only_cur = [self.facts[0]]
        c = call("P21", "売上高は、前期は999千円となった。", "999", "千円", "売上高", ["NetSales"], only_cur)
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])

    def test_a_matching_value_is_still_decided_before_the_last_branch(self):
        """値が一致する fact が在れば最後の枝には来ない(従来どおり GROUNDED)。"""
        c = call("P21", "売上高は、前期は5,000千円となった。", "5,000", "千円", "売上高", ["NetSales"], self.facts)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])


class PriorYearStopIsKeptTest(unittest.TestCase):
    """§1b の止め(前々期が無い「前連結会計年度は…」)は人間の決定。P21 の 3 つの直しはその**後**に置くので、
    止めた主張を名指しに戻さない。(最初の実装は 3 つを止めの前に置き、無改変の 40 書類で止めた 2 行が名指しに戻った。)"""

    def test_p21_keeps_the_stop_for_a_prior_year_phrase_with_a_prior_fact(self):
        facts = [fact("NetSales", "CurrentYearDuration", 5000000), fact("NetSales", "Prior1YearDuration", 7000000)]
        c = call("P21", "売上高は、前連結会計年度は999千円となった。", "999", "千円", "売上高", ["NetSales"], facts)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(c["reason"], c["result"]))

    def test_p21_keeps_the_stop_for_a_prior_year_difference_on_a_balance(self):
        facts = [fact("CashAndDeposits", "CurrentYearInstant", 10000000), fact("CashAndDeposits", "Prior1YearInstant", 8000000)]
        c = call("P21", "現金及び預金は、前連結会計年度は500千円増加した。", "500", "千円", "現金及び預金", ["CashAndDeposits"], facts)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertEqual("direct_value", c["form"])


class SegmentWithoutFrameTest(unittest.TestCase):
    """F2′ ― セグメント利益・損失で member が取れていなければ、全社の fact を名指さない。"""

    def setUp(self):
        self.facts = [fact("OperatingIncome", "CurrentYearDuration", 5000000)]
        self.seg_facts = self.facts + [fact("OperatingIncome", "CurrentYearDuration_ParkingSegmentMember", 3000000)]

    def test_p21_stops_without_naming_for_segment_profit(self):
        c = call("P21", "セグメント利益は999千円となった。", "999", "千円", "セグメント利益", ["OperatingIncome"], self.facts)
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["result"])
        self.assertEqual("no_element", c["reason"])
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(c["reason"], c["result"]))

    def test_p21_stops_for_segment_loss_too(self):
        c = call("P21", "セグメント損失は999千円となった。", "999", "千円", "セグメント損失", ["OperatingIncome"], self.facts)
        self.assertIsNone(c["pointer"])
        self.assertEqual("no_element", c["reason"])

    def test_p20_still_names_the_company_wide_fact(self):
        c = call("P20", "セグメント利益は999千円となった。", "999", "千円", "セグメント利益", ["OperatingIncome"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration", c["pointer"])
        self.assertEqual("VALUE_MISMATCH", c["result"])

    def test_with_a_member_p21_still_names_the_segment_fact(self):
        c = call("P21", "セグメント利益は999千円となった。", "999", "千円", "セグメント利益", ["OperatingIncome"], self.seg_facts,
                 member=SEG, members={"CurrentYearDuration_ParkingSegmentMember": [SEG]})
        self.assertEqual("xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration_ParkingSegmentMember", c["pointer"])
        self.assertEqual("VALUE_MISMATCH", c["result"])

    def test_another_subject_is_not_stopped(self):
        c = call("P21", "営業利益は999千円となった。", "999", "千円", "営業利益", ["OperatingIncome"], self.facts)
        self.assertEqual("xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration", c["pointer"])


class BalancePairForDifferenceTest(unittest.TestCase):
    """F3b ― 増減の文が当期の残高を選んだときは、残高の対(当期 − 前期)にする。"""

    def setUp(self):
        self.facts = [fact("CashAndDeposits", "CurrentYearInstant", 10000000), fact("CashAndDeposits", "Prior1YearInstant", 8000000)]
        self.s = "現金及び預金は、前期末に比べて500千円増加した。"

    def call(self, profile, facts=None):
        return call(profile, self.s, "500", "千円", "現金及び預金", ["CashAndDeposits"], facts or self.facts)

    def test_p21_names_the_pair_with_the_difference_formula(self):
        c = self.call("P21")
        self.assertEqual(["xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant",
                          "xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant", "formula:a-b"], c["pointer"])
        self.assertEqual("derived_value", c["form"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(2000000.0, c["recomputed"])
        self.assertTrue(c["bound"])

    def test_p20_still_names_the_single_balance(self):
        c = self.call("P20")
        self.assertEqual("xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant", c["pointer"])
        self.assertEqual("direct_value", c["form"])
        self.assertEqual(10000000.0, c["recomputed"])

    def test_a_flow_fact_is_not_turned_into_a_pair(self):
        flow = [fact("CashAndDeposits", "CurrentYearDuration", 10000000), fact("CashAndDeposits", "Prior1YearDuration", 8000000)]
        c = self.call("P21", flow)
        self.assertEqual("xbrl:jppfs_cor:CashAndDeposits@CurrentYearDuration", c["pointer"])
        self.assertEqual("direct_value", c["form"])

    def test_without_a_prior_balance_p21_keeps_the_single_balance(self):
        c = self.call("P21", [self.facts[0]])
        self.assertEqual("xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant", c["pointer"])

    def test_a_matching_difference_is_still_grounded_by_the_earlier_branch(self):
        c = call("P21", "現金及び預金は、前期末に比べて2,000千円増加した。", "2,000", "千円", "現金及び預金", ["CashAndDeposits"],
                 self.facts)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("derived_value", c["form"])


if __name__ == "__main__":
    unittest.main()
