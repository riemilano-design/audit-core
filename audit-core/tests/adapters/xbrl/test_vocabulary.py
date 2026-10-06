# -*- coding: utf-8 -*-
import unittest

from adapters.xbrl import vocabulary as V


class SubjectsTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(V.SUBJECTS_BASE_39), 39)
        self.assertEqual(len(V.SUBJECTS_RUN_B_EXTRA_34), 34)
        self.assertEqual(len(V.SUBJECTS_73), 73)
        self.assertEqual(len(V.SUBJECTS_74), 74)

    def test_order_extra_before_base(self):
        self.assertEqual(V.SUBJECTS_73[:34], V.SUBJECTS_RUN_B_EXTRA_34)
        self.assertEqual(V.SUBJECTS_73[34:], V.SUBJECTS_BASE_39)

    def test_vocab4_is_first_in_74(self):
        self.assertEqual(V.SUBJECTS_74[0], V.VOCAB4)
        self.assertEqual(V.SUBJECTS_74[1:], list(V.SUBJECTS_73))

    def test_elements_are_lists_of_str(self):
        for word, elems in V.SUBJECTS_74:
            self.assertIsInstance(word, str)
            self.assertIsInstance(elems, list)
            self.assertTrue(all(isinstance(e, str) for e in elems))


class MatchValueTest(unittest.TestCase):
    def test_round_exact(self):
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")

    def test_round_within_half_unit(self):
        self.assertEqual(V.match_value(100.4, 100.0, 1.0), "round")

    def test_truncate(self):
        # fact slightly above target, within one full unit -> truncate
        self.assertEqual(V.match_value(100.9, 100.0, 1.0), "truncate")

    def test_abs_round(self):
        self.assertEqual(V.match_value(-100.0, 100.0, 1.0), "abs+round")

    def test_no_match(self):
        self.assertIsNone(V.match_value(50.0, 100.0, 1.0))

    def test_sign_mode_order_prefers_plain_over_abs(self):
        # fact already matches without abs; must not report "abs+round".
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")


class TolOfTest(unittest.TestCase):
    def test_decimals_drives_tolerance(self):
        self.assertEqual(V.tol_of({"decimals": "-6"}, 1e3), 0.5e6)

    def test_claim_scale_floor(self):
        self.assertEqual(V.tol_of({"decimals": "0"}, 1e6), 0.5e6)

    def test_missing_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({}, 1e3), 0.5e3)

    def test_inf_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({"decimals": "INF"}, 1e3), 0.5e3)

    def test_bad_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({"decimals": "not-a-number"}, 1e3), 0.5e3)


class ProfileTest(unittest.TestCase):
    def test_p1_is_member_off(self):
        self.assertFalse(V.P1.member_on)
        self.assertFalse(V.P1.claim_level_member)
        self.assertIsNone(V.P1.run3)
        self.assertEqual(len(V.P1.subjects), 73)

    def test_p5f_is_member_on_claim_level(self):
        self.assertTrue(V.P5F.member_on)
        self.assertTrue(V.P5F.claim_level_member)
        self.assertEqual(V.P5F.run3, "L")
        self.assertEqual(len(V.P5F.subjects), 74)

    def test_profiles_registry(self):
        self.assertEqual(V.PROFILES["P1"], V.P1)
        self.assertEqual(V.PROFILES["P5F"], V.P5F)

    def test_p1_and_p5f_flags_are_all_off(self):
        # Core 接続 C-1g §1: P1・P5F の定義は不変(3 つの新フラグは既定 False)。
        for profile in (V.P1, V.P5F):
            self.assertFalse(profile.flow_sign)
            self.assertFalse(profile.point_diff)
            self.assertFalse(profile.segment_denominator)

    def test_p1_p5f_p6_c1h_flags_are_all_off(self):
        # Core 接続 C-1h §1: P1・P5F・P6 の定義は不変(3 つの新フラグは既定
        # False のまま)。
        for profile in (V.P1, V.P5F, V.P6):
            self.assertFalse(profile.expenditure_sign)
            self.assertFalse(profile.target_word)
            self.assertFalse(profile.text_reason_split)


class P6ProfileTest(unittest.TestCase):
    """Core 接続 C-1g §1(人間の承認、2026-10-06): profile P6 の語彙 7 行と
    3 つのフラグ。P1/P5F はこれらに触れない。
    """

    def test_p6_flags_all_on(self):
        self.assertTrue(V.P6.flow_sign)
        self.assertTrue(V.P6.point_diff)
        self.assertTrue(V.P6.segment_denominator)
        self.assertTrue(V.P6.member_on)
        self.assertTrue(V.P6.claim_level_member)
        self.assertEqual(V.P6.run3, "L")

    def test_p6_in_profiles_registry(self):
        self.assertEqual(V.PROFILES["P6"], V.P6)
        # Core 接続 C-1h: PROFILES は P7 を足して 4 件になった(この行は
        # C-1h の実装担当が更新。P6 自体の登録は不変)。
        self.assertIn("P6", V.PROFILES)

    def test_subjects_p6_extra_7_count(self):
        self.assertEqual(len(V.SUBJECTS_P6_EXTRA_7), 7)

    def test_subjects_p6_extra_7_words(self):
        words = [w for w, _elems in V.SUBJECTS_P6_EXTRA_7]
        self.assertEqual(
            words,
            [
                "流動負債", "固定負債", "投資有価証券の取得による支出",
                "1年内返済予定の長期借入金", "持分法による投資利益", "ROE", "退職給付に係る負債",
            ],
        )

    def test_subjects_p6_is_extra_7_plus_74_in_order(self):
        self.assertEqual(len(V.SUBJECTS_P6), 81)
        self.assertEqual(V.SUBJECTS_P6[:7], tuple(V.SUBJECTS_P6_EXTRA_7))
        self.assertEqual(V.SUBJECTS_P6[7:], tuple(V.SUBJECTS_74))
        self.assertEqual(V.P6.subjects, V.SUBJECTS_P6)

    def test_extra_7_words_absent_from_p1_and_p5f(self):
        p1_words = {w for w, _e in V.P1.subjects}
        p5f_words = {w for w, _e in V.P5F.subjects}
        for word, _elems in V.SUBJECTS_P6_EXTRA_7:
            self.assertNotIn(word, p1_words)
            self.assertNotIn(word, p5f_words)


class FlowConventionTest(unittest.TestCase):
    """Core 接続 C-1g §1-2: CF 流量項目の符号の規約(b、人間の決定、
    2026-10-06)。
    """

    def test_decrease_increase_prefix_is_minus_one(self):
        self.assertEqual(V.flow_convention("DecreaseIncreaseInNotesAndAccountsReceivableTrade"), -1)

    def test_increase_decrease_prefix_is_plus_one(self):
        self.assertEqual(V.flow_convention("IncreaseDecreaseInNotesAndAccountsPayableTrade"), 1)

    def test_net_increase_decrease_prefix_is_plus_one(self):
        self.assertEqual(V.flow_convention("NetIncreaseDecreaseInCashAndCashEquivalents"), 1)

    def test_net_decrease_increase_prefix_is_minus_one(self):
        self.assertEqual(V.flow_convention("NetDecreaseIncreaseInSomething"), -1)

    def test_company_extension_prefix_uses_local_name_only(self):
        self.assertEqual(V.flow_convention("e01234-asr_E00001-000:IncreaseDecreaseInProvisionForWarranties"), 1)
        self.assertEqual(V.flow_convention("e01234-asr_E00001-000:DecreaseIncreaseInTradeReceivables"), -1)

    def test_non_flow_element_is_none(self):
        self.assertIsNone(V.flow_convention("NetSales"))
        self.assertIsNone(V.flow_convention("jppfs_cor:CurrentLiabilities"))


class P7ProfileTest(unittest.TestCase):
    """Core 接続 C-1h §1(人間の決定、2026-10-06): profile P7 = P6 + 3 つの
    フラグ。P7 の語彙は P6 と同じ(``SUBJECTS_P6``)。
    """

    def test_p7_flags_all_on(self):
        self.assertTrue(V.P7.expenditure_sign)
        self.assertTrue(V.P7.target_word)
        self.assertTrue(V.P7.text_reason_split)
        # P6 の 3 フラグも引き続き真(P7 は P6 の全部を引き継ぐ)。
        self.assertTrue(V.P7.flow_sign)
        self.assertTrue(V.P7.point_diff)
        self.assertTrue(V.P7.segment_denominator)
        self.assertTrue(V.P7.member_on)
        self.assertTrue(V.P7.claim_level_member)
        self.assertEqual(V.P7.run3, "L")

    def test_p7_in_profiles_registry(self):
        self.assertEqual(V.PROFILES["P7"], V.P7)
        self.assertEqual(sorted(V.PROFILES.keys()), ["P1", "P5F", "P6", "P7"])

    def test_p7_subjects_same_as_p6(self):
        self.assertEqual(V.P7.subjects, V.P6.subjects)
        self.assertEqual(len(V.P7.subjects), 81)


class ExpenditureConventionTest(unittest.TestCase):
    """Core 接続 C-1h §1-1(人間の決定、2026-10-06): CF の「支出」系項目。"""

    def test_purchase_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PurchaseOfPropertyPlantAndEquipment"))

    def test_payments_for_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PaymentsForRetirementBenefits"))

    def test_payments_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PaymentsOfSomething"))

    def test_repayments_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RepaymentsOfLongTermLoansPayable"))

    def test_repayment_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RepaymentOfLoansPayable"))

    def test_redemption_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RedemptionOfBonds"))

    def test_dividends_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("DividendsPaid"))

    def test_income_taxes_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("IncomeTaxesPaid"))

    def test_interest_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("InterestPaid"))

    def test_proceeds_from_prefix_is_not_expenditure(self):
        self.assertFalse(V.expenditure_convention("ProceedsFromLongTermLoansPayable"))

    def test_increase_decrease_prefix_is_not_expenditure(self):
        # flow_convention(DecreaseIncreaseIn…/IncreaseDecreaseIn…) が先に
        # 効く対象で、expenditure_convention はここでは False。
        self.assertFalse(V.expenditure_convention("IncreaseDecreaseInNotesAndAccountsPayableTrade"))
        self.assertFalse(V.expenditure_convention("DecreaseIncreaseInNotesAndAccountsReceivableTrade"))

    def test_company_extension_prefix_uses_local_name_only(self):
        self.assertTrue(V.expenditure_convention("e01234-asr_E00001-000:PurchaseOfInvestmentSecurities"))

    def test_non_expenditure_element_is_false(self):
        self.assertFalse(V.expenditure_convention("NetSales"))
        self.assertFalse(V.expenditure_convention("Assets"))


if __name__ == "__main__":
    unittest.main()
