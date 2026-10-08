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
        # XBRL 直し(2026-10-08)で P8 を足した。P1/P5F/P6/P7 の 4 つが在ること
        # と、P8 がこの 4 つに加わっていることを両方見る。
        self.assertEqual(sorted(V.PROFILES.keys()),
                         ["P1", "P10", "P11", "P12", "P13", "P14", "P5F", "P6", "P7", "P8", "P9"])

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


class MatchValueModeTest(unittest.TestCase):
    """XBRL 直し §2(2026-10-08): ``match_value`` の ``mode``。

    桁 ``unit`` を 1.0、目標を 100.0 に固定して、3 つの帯を両側から当てる。
    ``-0.4`` は round だけ・``+0.9`` は truncate だけが通る帯であり、
    ``mode=None``(既存)は**両方**通す = 許容幅が実質 1.5 倍であることを数で残す。
    """

    def test_mode_none_accepts_both_sides(self):
        self.assertEqual(V.match_value(99.6, 100.0, 1.0), "round")
        self.assertEqual(V.match_value(100.9, 100.0, 1.0), "truncate")

    def test_round_only_rejects_the_truncate_side(self):
        self.assertEqual(V.match_value(99.6, 100.0, 1.0, "round"), "round")
        self.assertIsNone(V.match_value(100.9, 100.0, 1.0, "round"))

    def test_truncate_only_rejects_the_negative_side(self):
        self.assertEqual(V.match_value(100.9, 100.0, 1.0, "truncate"), "truncate")
        self.assertIsNone(V.match_value(99.6, 100.0, 1.0, "truncate"))

    def test_truncate_only_still_labels_the_overlap_as_truncate(self):
        # 差が 0 以上 unit/2 以下の重なりの帯は、梯子では round の札が付くが、
        # 書類の丸め方を truncate に決めたら truncate の札になる。
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")
        self.assertEqual(V.match_value(100.0, 100.0, 1.0, "truncate"), "truncate")

    def test_abs_prefix_survives_each_mode(self):
        self.assertEqual(V.match_value(-100.9, 100.0, 1.0, "truncate"), "abs+truncate")
        self.assertEqual(V.match_value(-99.6, 100.0, 1.0, "round"), "abs+round")

    def test_mode_none_is_identical_to_the_frozen_ladder(self):
        # 恒等: mode を渡さないことと None を渡すことが同じ。
        for fv in (99.4, 99.6, 100.0, 100.4, 100.9, 101.2, -100.0, 0.0):
            self.assertEqual(V.match_value(fv, 100.0, 1.0), V.match_value(fv, 100.0, 1.0, None))


class DecideRoundingTest(unittest.TestCase):
    """XBRL 直し §2: 書類単位の丸め方の決め方。``(差, 桁)`` の列から決める。"""

    def test_truncate_when_truncate_only_evidence_wins(self):
        self.assertEqual(V.decide_rounding([(0.9, 1.0), (0.8, 1.0), (-0.3, 1.0)]), ("truncate", 1, 2))

    def test_round_when_round_only_evidence_wins(self):
        self.assertEqual(V.decide_rounding([(-0.3, 1.0), (-0.2, 1.0), (0.9, 1.0)]), ("round", 2, 1))

    def test_tie_falls_back_to_the_written_default(self):
        self.assertEqual(V.DOC_ROUNDING_DEFAULT, "round")
        self.assertEqual(V.decide_rounding([(0.9, 1.0), (-0.3, 1.0)]), ("round", 1, 1))

    def test_no_evidence_falls_back_to_the_written_default(self):
        self.assertEqual(V.decide_rounding([]), ("round", 0, 0))

    def test_overlap_band_is_evidence_for_neither(self):
        # 差が 0..unit/2 の重なりの帯は、どちらの丸め方でも説明できるので
        # R にも T にも数えない。
        self.assertEqual(V.decide_rounding([(0.0, 1.0), (0.4, 1.0), (0.5, 1.0)]), ("round", 0, 0))

    def test_unit_is_read_per_row(self):
        # 桁は行ごと。0.9 は桁 1.0 なら truncate だけの帯だが、桁 10.0 なら重なり。
        self.assertEqual(V.decide_rounding([(0.9, 1.0)]), ("truncate", 0, 1))
        self.assertEqual(V.decide_rounding([(0.9, 10.0)]), ("round", 0, 0))


class SubjectsP8Test(unittest.TestCase):
    """XBRL 直し §1a(2026-10-08): 「資産合計」に ``TotalAssets`` を足す。
    主語の数は増やしていない・P6 の語彙は不変。
    """

    def test_same_number_of_subjects_as_p6(self):
        self.assertEqual(len(V.SUBJECTS_P8), len(V.SUBJECTS_P6))

    def test_only_the_total_assets_rows_differ_from_p6(self):
        differ = [(a, b) for a, b in zip(V.SUBJECTS_P6, V.SUBJECTS_P8) if a != b]
        self.assertTrue(differ)
        for a, b in differ:
            self.assertEqual(a[0], "資産合計")
            self.assertEqual(b, ("資産合計", ["Assets", "TotalAssets"]))

    def test_p6_total_assets_is_still_assets_only_somewhere(self):
        # 直す前の非対称(「純資産合計」は Summary が引けるのに「資産合計」は
        # 引けない)が P6 に残っていることを固定する。
        self.assertIn(("資産合計", ["Assets"]), list(V.SUBJECTS_P6))
        self.assertIn(("純資産合計", ["NetAssets"]), list(V.SUBJECTS_P6))

    def test_p8_total_assets_can_reach_the_summary_element(self):
        # 語彙には「資産合計」の行が 2 つある(RUN=="B" の 34 語と基礎の 39 語)。
        # ``subject_of`` は同じ語・同じ長さなら**先に来た行**を採るので、
        # ``dict()`` で引くと(後の行が勝って)実際とは違う答えになる。
        # そこで実際に主語を引く経路で見る。
        # ``facts_for`` は 要素名 + "SummaryOfBusinessResults" を完全一致に数える。
        from adapters.xbrl import extract as X
        s = "当連結会計年度末における資産合計は、278億円となりました。"
        pos = s.index("278")
        _w8, elems8 = X.subject_of(s, pos, V.SUBJECTS_P8)
        _w6, elems6 = X.subject_of(s, pos, V.SUBJECTS_P6)
        self.assertEqual(elems8, ["Assets", "TotalAssets"])
        self.assertEqual(elems6, ["Assets"])
        self.assertIn("TotalAssetsSummaryOfBusinessResults", [e + "SummaryOfBusinessResults" for e in elems8])
        self.assertNotIn("TotalAssetsSummaryOfBusinessResults", [e + "SummaryOfBusinessResults" for e in elems6])


class P8ProfileTest(unittest.TestCase):
    """XBRL 直し(2026-10-08): P8 = P7 + 5 つのフラグ。既存 profile は不変。"""

    FLAGS = ("prior2_required", "doc_rounding", "target_both", "paren_sentence", "drop_qualitative")

    def test_p8_turns_all_five_on(self):
        for f in self.FLAGS:
            self.assertTrue(getattr(V.P8, f), f)

    def test_existing_profiles_keep_all_five_off(self):
        for p in (V.P1, V.P5F, V.P6, V.P7):
            for f in self.FLAGS:
                self.assertFalse(getattr(p, f), "%s.%s" % (p.name, f))

    def test_p8_keeps_every_p7_flag(self):
        for f in ("member_on", "claim_level_member", "flow_sign", "point_diff", "segment_denominator",
                  "expenditure_sign", "target_word", "text_reason_split"):
            self.assertEqual(getattr(V.P8, f), getattr(V.P7, f), f)
        self.assertEqual(V.P8.run3, V.P7.run3)

    def test_p8_uses_the_p8_subjects(self):
        self.assertEqual(V.P8.subjects, V.SUBJECTS_P8)
        self.assertEqual(V.P7.subjects, V.SUBJECTS_P6)


class SubjectsP12Test(unittest.TestCase):
    """XBRL 直し §7c(人間の判断、2026-10-08): 手書きの語彙そのものを直す。

    直すのは 2 語だけ。標準タクソノミ(jppfs 2025-11-01)で機械確認した結果、
    「要素が実在しない + 同じ日本語ラベルの実在の要素が在る + 3 書類とも fact 0」
    の 3 つを同時に満たすのがこの 2 語しかなかった。
    """

    def test_the_two_words_gain_the_element_that_actually_exists(self):
        d = dict(V.SUBJECTS_P12)
        self.assertEqual(d["退職給付に係る資産"], ["RetirementBenefitAsset", "NetDefinedBenefitAsset"])
        self.assertEqual(d["退職給付に係る負債"], ["RetirementBenefitLiability", "NetDefinedBenefitLiability"])

    def test_the_old_name_is_kept_not_replaced(self):
        # 会社拡張が古い名前を使っている書類がありうるので**消さずに足す**。
        for word, elems in V.SUBJECTS_P12_FIXES.items():
            self.assertEqual(elems[0], dict(V.SUBJECTS_P8)[word][0], word)
            self.assertGreater(len(elems), len(dict(V.SUBJECTS_P8)[word]))

    def test_p6_and_p8_are_not_touched(self):
        """**ここが動くと P7(「直す前」)と P10 の既に測った数が黙って動く。**

        ``dict(...)`` は使わない ― 一覧には同じ語が 2 行在ることがあり
        (``資産合計`` は P6 で 2 行)、``dict`` は**最後**を返すのに
        ``subject_of`` は**先**を採る。前にこの取り違えで試験を 1 本間違えた。
        """

        def first(subjects, word):
            return next(e for w, e in subjects if w == word)

        self.assertEqual(first(V.SUBJECTS_P8, "退職給付に係る負債"), ["RetirementBenefitLiability"])
        self.assertEqual(first(V.SUBJECTS_P6, "退職給付に係る負債"), ["RetirementBenefitLiability"])
        self.assertEqual(first(V.SUBJECTS_P8, "退職給付に係る資産"), ["RetirementBenefitAsset"])
        self.assertEqual(first(V.SUBJECTS_P6, "退職給付に係る資産"), ["RetirementBenefitAsset"])
        # §1a で足した 資産合計 の 1 行目は P6 では ["Assets"] のまま。
        self.assertEqual(first(V.SUBJECTS_P6, "資産合計"), ["Assets"])

    def test_only_the_two_words_differ_from_p8(self):
        self.assertEqual(len(V.SUBJECTS_P12), len(V.SUBJECTS_P8))
        differ = [a[0] for a, b in zip(V.SUBJECTS_P12, V.SUBJECTS_P8) if a != b]
        self.assertEqual(sorted(set(differ)), ["退職給付に係る負債", "退職給付に係る資産"])

    def test_the_word_order_is_unchanged(self):
        self.assertEqual([w for w, _e in V.SUBJECTS_P12], [w for w, _e in V.SUBJECTS_P8])


class P12P13P14ProfileTest(unittest.TestCase):
    """XBRL 直し §7a/§7b/§7c/§8 の profile。既存の定義は 1 行も書き換えない。"""

    def test_p13_is_p12_plus_only_the_taxonomy_flag(self):
        import dataclasses
        a = dataclasses.replace(V.P12, name="x", taxonomy_labels=True)
        self.assertEqual(a, dataclasses.replace(V.P13, name="x"))

    def test_p14_is_p13_plus_only_the_namespace_flag(self):
        import dataclasses
        a = dataclasses.replace(V.P13, name="x", taxonomy_labels_all_ns=True)
        self.assertEqual(a, dataclasses.replace(V.P14, name="x"))

    def test_p12_to_p14_use_the_fixed_hand_vocabulary(self):
        for p in (V.P12, V.P13, V.P14):
            self.assertIs(p.subjects, V.SUBJECTS_P12, p.name)
        for p in (V.P8, V.P9, V.P10, V.P11):
            self.assertIs(p.subjects, V.SUBJECTS_P8, p.name)

    def test_profiles_registry_lists_every_profile(self):
        self.assertEqual(sorted(V.PROFILES),
                         ["P1", "P10", "P11", "P12", "P13", "P14", "P5F", "P6", "P7", "P8", "P9"])
        for name, p in V.PROFILES.items():
            self.assertEqual(p.name, name)
