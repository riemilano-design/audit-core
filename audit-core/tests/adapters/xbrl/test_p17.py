# -*- coding: utf-8 -*-
"""P17(計画 docs/P17_PLAN_2026-10-14.md)の規則の単体試験。
規則ごとに「当たる例」と「当たらない例」、旗が偽なら 1 つも変わらないこと。"""

import dataclasses
import unittest

from adapters.xbrl import extract as E
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

REG = {"m:Parking": "駐車場事業", "m:Props": "不動産事業"}


class ProfileShapeTest(unittest.TestCase):
    def test_p17_is_p16_plus_five_flags(self):
        p16, p17 = V.P16, V.P17
        flags = ("segment_carry_to_result_sentence", "external_revenue_for_sales", "subject_skip_before_cause_marker",
                 "loss_variants", "prefer_net_when_labelled")
        for f in flags:
            self.assertFalse(getattr(p16, f), f)
            self.assertTrue(getattr(p17, f), f)
        self.assertEqual(dataclasses.replace(p17, name="P16", **{f: False for f in flags}), p16)
        self.assertIs(V.PROFILES["P17"], p17)

    def test_p1_to_p16_keep_the_five_flags_off(self):
        for name, p in V.PROFILES.items():
            if name in ("P17", "P18", "P19"):
                continue
            self.assertFalse(p.segment_carry_to_result_sentence or p.external_revenue_for_sales
                             or p.subject_skip_before_cause_marker or p.loss_variants or p.prefer_net_when_labelled, name)

    def test_default_profile_is_p26(self):
        """2026-10-14 の人間の決定で P16 -> P20、2026-10-20(段 2)に P20 -> P21(封 XBRL_NAMING_FIX_SEAL_2026-10-20)、
        同じ日の期を縛る P22 の段 2 で P21 -> P22(封 XBRL_PERIOD_BIND_SEAL_2026-10-20。人間の決定「任せる」)、
        2026-10-23 の P26 の段 2 で P22 -> P26(封 XBRL_DEFAULT_P26_SEAL_2026-10-23。人間の決定 2026-10-21「あとは全て任せる」)。"""

        self.assertEqual(V.DEFAULT_PROFILE, "P26")


class SegmentCarryTest(unittest.TestCase):
    def test_carry_across_paragraphs_to_the_result_sentence(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "既存の活性化も進めました。", "以上の結果、売上高7,056,648千円となりました。"]
        res = E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)
        self.assertEqual(res, [("m:Parking", "sentence"), (None, None), ("m:Parking", "carried")])

    def test_old_rule_does_not_carry_across_paragraphs(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "以上の結果、売上高7,056,648千円となりました。"]
        self.assertEqual(E.resolve_members(sents, [0, 1], REG)[1], (None, None))

    def test_in_paragraph_carry_of_the_old_rule_is_kept(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "売上高は40億62百万円となりました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, [0, 0], REG)[1], ("m:Parking", "carried"))

    def test_consolidated_word_between_in_the_segment_paragraph_does_not_stop(self):
        sents = ["メディカル事業につきましては、賃貸を行いました。", "当連結会計年度におきましては、賃貸収入が堅調でした。", "以上の結果、売上高259,831千円となりました。"]
        reg = {"m:Med": "メディカル事業"}
        self.assertEqual(E.resolve_members_to_result_sentence(sents, [0, 1, 2], reg)[2], ("m:Med", "carried"))

    def test_non_result_sentence_is_not_carried_into(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "総資産が前連結会計年度末に比べ167億円増加しました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[1], (None, None))

    def test_result_sentence_with_consolidated_word_is_not_carried_into(self):
        for s2 in ("この結果、当社グループの業績は売上高67,099百万円となりました。",
                   "以上の結果、総資産は10,232,043千円となり、前連結会計年度末に比べ増加しました。",
                   "以上の結果、全社の営業利益は29,431千円となりました。"):
            sents = ["駐車場事業につきましては、開発に注力しました。", s2]
            self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[1], (None, None), s2)

    def test_new_topic_marker_in_between_stops_the_carry(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "また、その他につきましては販売を進めました。", "以上の結果、営業利益29,431千円となりました。"]
        res = E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)
        self.assertEqual(res[1], (None, None))
        self.assertEqual(res[2], (None, None))

    def test_group_word_in_between_stops_the_carry(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "当社グループ全体では費用が増えました。", "以上の結果、営業損失521,333千円となりました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[2], (None, None))

    def test_ambiguous_sentence_stops_the_carry(self):
        sents = ["駐車場事業につきましては、開発に注力しました。", "駐車場事業と不動産事業の両方で増収でした。", "以上の結果、売上高100千円となりました。"]
        res = E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)
        self.assertEqual(res[1], (E.AMBIG, "ambiguous"))
        self.assertEqual(res[2], (None, None))

    def test_carry_is_limited_to_five_sentences(self):
        sents = ["不動産事業につきましては、竣工しました。"] + ["販売も進みました。"] * 5 + ["以上の結果、売上高2,523,449千円となりました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[6], (None, None))
        sents = ["不動産事業につきましては、竣工しました。"] + ["販売も進みました。"] * 4 + ["以上の結果、売上高2,523,449千円となりました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[5], ("m:Props", "carried"))

    def test_a_later_segment_sentence_wins_over_an_earlier_one(self):
        sents = ["駐車場事業につきましては、開発しました。", "不動産事業につきましては、竣工しました。", "以上の結果、売上高2,523,449千円となりました。"]
        self.assertEqual(E.resolve_members_to_result_sentence(sents, list(range(len(sents))), REG)[2], ("m:Props", "carried"))


SUBJECTS = (("営業外費用", ["NonOperatingExpenses"]), ("支払利息", ["InterestExpensesNOE"]),
            ("受注高", ["Orders"]), ("受注残高", ["Backlog"]),
            ("営業活動によるキャッシュ・フロー", ["CFO"]), ("法人税等の支払額", ["Tax"]))


class CauseMarkerSubjectTest(unittest.TestCase):
    S = "営業外費用は、支払利息138,206千円等の計上により158,783千円となりました"

    def test_total_after_cause_marker_takes_the_topic(self):
        self.assertEqual(E.subject_of(self.S, self.S.index("158,783"), SUBJECTS, None, cause_topic=True)[0], "営業外費用")

    def test_component_number_keeps_its_own_subject(self):
        self.assertEqual(E.subject_of(self.S, self.S.index("138,206"), SUBJECTS, None, cause_topic=True)[0], "支払利息")

    def test_flag_off_is_unchanged(self):
        self.assertEqual(E.subject_of(self.S, self.S.index("158,783"), SUBJECTS, None)[0], "支払利息")
        self.assertEqual(E.subject_of(self.S, self.S.index("158,783"), SUBJECTS, None, cause_topic=False)[0], "支払利息")

    def test_enumeration_without_cause_marker_is_unchanged(self):
        s = "受注高は394億円、受注残高は214億円となりました"
        self.assertEqual(E.subject_of(s, s.index("214"), SUBJECTS, None, cause_topic=True)[0], "受注残高")

    def test_cause_clause_inside_the_topic_word_is_not_a_marker(self):
        s = "営業活動によるキャッシュ・フローは、法人税等の支払額等の支出額を上回ったことにより、4,075百万円の純収入となりました"
        self.assertEqual(E.subject_of(s, s.index("4,075"), SUBJECTS, None, cause_topic=True)[0], "営業活動によるキャッシュ・フロー")

    def test_no_topic_before_the_candidate_means_no_skip(self):
        s = "支払利息の計上により158,783千円となりました"
        self.assertEqual(E.subject_of(s, s.index("158,783"), SUBJECTS, None, cause_topic=True)[0], "支払利息")


def _profile(**kw):
    return dataclasses.replace(V.P16, name="T", **kw)


class FirstMatchingPairTest(unittest.TestCase):
    PAIRS = [({"value": 7106655.0}, {"value": 7004381.0}), ({"value": 7056648.0}, {"value": 7002314.0})]

    def test_flag_on_takes_the_first_matching_pair(self):
        m = lambda c, p: abs((c["value"] - p["value"]) / abs(p["value"]) * 100 - 0.8) <= 0.15
        self.assertEqual(R._first_matching_pair(self.PAIRS, m, V.P17), self.PAIRS[1])

    def test_flag_off_takes_the_first_pair(self):
        m = lambda c, p: True
        self.assertEqual(R._first_matching_pair(self.PAIRS, m, V.P16), self.PAIRS[0])
        self.assertEqual(R._first_matching_pair(self.PAIRS, m, None), self.PAIRS[0])

    def test_flag_on_without_a_match_falls_back_to_the_first_pair(self):
        self.assertEqual(R._first_matching_pair(self.PAIRS, lambda c, p: False, V.P17), self.PAIRS[0])


class AugmentSubjectRowsTest(unittest.TestCase):
    HAND = [("売上高", ["NetSales"]), ("営業利益", ["OperatingIncome"]), ("営業損失", ["OperatingIncome"]), ("建物及び構築物", ["BuildingsAndStructures"])]
    ADDED = [("経常利益", ["OrdinaryIncome"])]
    LABELS = {"建物及び構築物(純額)": ["BuildingsAndStructuresNet"], "建物及び構築物": ["BuildingsAndStructures"]}

    def test_all_flags_off_changes_nothing(self):
        h, a = R.augment_subject_rows(self.HAND, self.ADDED, self.LABELS, lambda e: True, V.P16)
        self.assertEqual((h, a), (self.HAND, self.ADDED))

    def test_external_revenue_appended_only_when_fact_exists(self):
        h, _ = R.augment_subject_rows(self.HAND, self.ADDED, {}, lambda e: e == "RevenuesFromExternalCustomers",
                                      _profile(external_revenue_for_sales=True))
        self.assertEqual(dict(h)["売上高"], ["NetSales", "RevenuesFromExternalCustomers"])
        h2, _ = R.augment_subject_rows(self.HAND, self.ADDED, {}, lambda e: False, _profile(external_revenue_for_sales=True))
        self.assertEqual(dict(h2)["売上高"], ["NetSales"])

    def test_external_revenue_is_not_duplicated(self):
        hand = [("売上高", ["NetSales", "RevenuesFromExternalCustomers"])]
        h, _ = R.augment_subject_rows(hand, [], {}, lambda e: True, _profile(external_revenue_for_sales=True))
        self.assertEqual(dict(h)["売上高"], ["NetSales", "RevenuesFromExternalCustomers"])

    def test_loss_variants_added_at_the_end_of_added_without_duplicates(self):
        _, a = R.augment_subject_rows(self.HAND, self.ADDED, {}, lambda e: True, _profile(loss_variants=True))
        self.assertEqual(a, [("経常利益", ["OrdinaryIncome"]), ("経常損失", ["OrdinaryIncome"])])  # 営業損失は既に在る

    def test_net_element_goes_first_when_labelled(self):
        h, _ = R.augment_subject_rows(self.HAND, self.ADDED, self.LABELS, lambda e: True, _profile(prefer_net_when_labelled=True))
        self.assertEqual(dict(h)["建物及び構築物"], ["BuildingsAndStructuresNet", "BuildingsAndStructures"])

    def test_net_rule_without_label_changes_nothing(self):
        h, _ = R.augment_subject_rows(self.HAND, self.ADDED, {}, lambda e: True, _profile(prefer_net_when_labelled=True))
        self.assertEqual(dict(h)["建物及び構築物"], ["BuildingsAndStructures"])

    def test_full_width_paren_label_is_also_accepted(self):
        labels = {"建物及び構築物（純額）": ["BuildingsAndStructuresNet"]}
        h, _ = R.augment_subject_rows(self.HAND, self.ADDED, labels, lambda e: True, _profile(prefer_net_when_labelled=True))
        self.assertEqual(dict(h)["建物及び構築物"][0], "BuildingsAndStructuresNet")

    def test_returns_new_lists(self):
        h, a = R.augment_subject_rows(self.HAND, self.ADDED, self.LABELS, lambda e: True, V.P17)
        self.assertIsNot(h, self.HAND)
        self.assertEqual(self.HAND[0], ("売上高", ["NetSales"]))


class PctToleranceTest(unittest.TestCase):
    def test_p18_is_p17_plus_the_tolerance_flag(self):
        self.assertTrue(V.P18.pct_tolerance_from_decimals)
        self.assertEqual(dataclasses.replace(V.P18, name="P17", pct_tolerance_from_decimals=False), V.P17)
        for name, p in V.PROFILES.items():
            if name not in ("P18", "P19", "P23", "P24", "P25", "P26", "P27", "P27E"):    # 2026-10-27 P27 = P26 + 旗 4 つ・P27E = P27 + 旗 1 つ(封 XBRL_P27_SEAL_2026-10-27)も引き継ぐ。P23 = P22 + 率の旗 + truncate_abs_band(封 XBRL_ROUNDING_SEAL_2026-10-21、2026-10-21)、P24 = P23 + 旗 2 つ(封 XBRL_VOCAB_SEAL_2026-10-21)、P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)、P26 = P25 + 旗 5 つ(封 XBRL_P26_SEAL_2026-10-21)
                self.assertFalse(p.pct_tolerance_from_decimals, name)

    def test_default_is_015_for_flag_off(self):
        s = "売上高(前期比2.3%増)"
        a, b = s.index("2.3"), s.index("2.3") + 4
        self.assertEqual(R.pct_tolerance(V.P17, s, a, b), 0.15)
        self.assertEqual(R.pct_tolerance(None, s, a, b), 0.15)
        self.assertEqual(R.PCT_TOLERANCE_DEFAULT, 0.15)

    def test_one_decimal_gives_006(self):
        s = "売上高(前期比2.3%増)"
        a, b = s.index("2.3"), s.index("2.3") + 4
        self.assertAlmostEqual(R.pct_tolerance(V.P18, s, a, b), 0.06)

    def test_zero_decimals_gives_051_and_two_decimals_0015(self):
        s = "比率は15%で、利益率は3.25%"
        self.assertAlmostEqual(R.pct_tolerance(V.P18, s, s.index("15"), s.index("15") + 3), 0.51)
        self.assertAlmostEqual(R.pct_tolerance(V.P18, s, s.index("3.25"), s.index("3.25") + 5), 0.015)

    def test_a_tenth_of_a_point_change_is_outside_the_p18_tolerance(self):
        self.assertGreater(abs(2.4 - 2.3), R.pct_tolerance(V.P18, "2.3%", 0, 4))
        self.assertLessEqual(abs(2.4 - 2.3), R.PCT_TOLERANCE_DEFAULT)


class MagnitudeTruncateTest(unittest.TestCase):
    """P19(計画 §8): 切り捨ての帯を絶対値で当てる。負の値で「実際より絶対値が 1 単位
    大きい額」を通さない(実測 2 件 ― fact −300,297,000 に対して「4億円」)。"""

    FACT = -300297000.0        # 業務未払金の減少(S100Z4Q1)
    UNIT = 1e8                 # 「億円」で書かれた主張の桁

    def test_p19_is_p18_plus_the_flag(self):
        self.assertTrue(V.P19.truncate_on_magnitude)
        self.assertEqual(dataclasses.replace(V.P19, name="P18", truncate_on_magnitude=False), V.P18)
        for name, p in V.PROFILES.items():
            if name != "P19":
                self.assertFalse(p.truncate_on_magnitude, name)

    def test_wrong_bigger_magnitude_is_rejected_only_with_the_flag(self):
        self.assertEqual(V.match_value(self.FACT, -4e8, self.UNIT, "truncate", False), "truncate")
        self.assertIsNone(V.match_value(self.FACT, -4e8, self.UNIT, "truncate", True))

    def test_the_right_value_still_matches(self):
        # 旗が偽のときは符号つきの枝が外れて絶対値の枝で当たる("abs+truncate")。
        # 旗が真のときは最初の枝が絶対値で当たる("truncate")。**どちらも一致**。
        self.assertEqual(V.match_value(self.FACT, -3e8, self.UNIT, "truncate", False), "abs+truncate")
        self.assertEqual(V.match_value(self.FACT, -3e8, self.UNIT, "truncate", True), "truncate")

    def test_legitimate_truncation_of_a_negative_value_still_matches(self):
        # fact −3.9 億を「3億円」と書く(絶対値を切り捨てる書き方)。旗の有無で札は違うが両方一致。
        self.assertIsNotNone(V.match_value(-390000000.0, -3e8, self.UNIT, "truncate", False))
        self.assertEqual(V.match_value(-390000000.0, -3e8, self.UNIT, "truncate", True), "truncate")

    def test_positive_values_are_unchanged(self):
        for flag in (False, True):
            self.assertEqual(V.match_value(390000000.0, 3e8, self.UNIT, "truncate", flag), "truncate", flag)
            self.assertIsNone(V.match_value(300297000.0, 4e8, self.UNIT, "truncate", flag), flag)

    def test_round_branch_is_untouched(self):
        for flag in (False, True):
            self.assertEqual(V.match_value(-360000000.0, -4e8, self.UNIT, "round", flag), "round", flag)

    def test_comparators_copy_takes_the_same_argument(self):
        from adapters.xbrl import comparators as C
        self.assertEqual(C._match_value(self.FACT, -4e8, self.UNIT, "truncate", False), "truncate")
        self.assertIsNone(C._match_value(self.FACT, -4e8, self.UNIT, "truncate", True))

    def test_the_two_copies_agree_on_a_grid(self):
        from adapters.xbrl import comparators as C
        for fv in (-4e8, -3.9e8, -3.003e8, -3e8, 0.0, 3e8, 3.003e8, 3.9e8, 4e8):
            for t in (-4e8, -3e8, 3e8, 4e8):
                for mode in (None, "round", "truncate"):
                    for flag in (False, True):
                        self.assertEqual(V.match_value(fv, t, self.UNIT, mode, flag),
                                         C._match_value(fv, t, self.UNIT, mode, flag), (fv, t, mode, flag))
