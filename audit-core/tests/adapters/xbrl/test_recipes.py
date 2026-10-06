# -*- coding: utf-8 -*-
import unittest

import audit_core as core

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V


class ClaimToRecipeDirectValueTest(unittest.TestCase):
    def test_grounded_direct_value(self):
        raw = {
            "id": "N001", "sentence": 0, "span": "x", "value": 100.0, "unit": "円",
            "subject": "売上高", "form": "direct_value",
            "pointer": "xbrl:jppfs_cor:NetSales@CurrentYearDuration",
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 100.0, "match": "round",
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.claim.id, "N001")
        self.assertEqual(recipe.claim.form, core.Form.DIRECT_VALUE)
        self.assertEqual(recipe.claim.modifiers.population, "consolidated")
        self.assertEqual(recipe.claim.modifiers.time_range, ("CurrentYear/Duration",))
        self.assertEqual(recipe.claim.modifiers.normalization, "round")
        self.assertEqual(len(recipe.pointers), 1)
        self.assertEqual(str(recipe.pointers[0]), "xbrl:jppfs_cor:NetSales@CurrentYearDuration")
        self.assertIsNone(recipe.unverifiable_reason)
        self.assertIsNone(recipe.not_found_reason)
        self.assertEqual(recipe.contract.comparator, "equals_within")

    def test_percent_unit_uses_pure_comparator(self):
        raw = {
            "id": "N002", "value": 61.7, "unit": "%", "subject": "自己資本比率", "form": "direct_value",
            "pointer": "xbrl:jpcrp_cor:EquityToAssetRatio@CurrentYearInstant", "bound": True,
            "reason": None, "result": "GROUNDED", "recomputed": 61.7,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "equals_within(pure*100)")
        # C-1d §3.1: params carry the real numbers the comparator reads
        # (tolerance 0.15 / pure_threshold 1.5), not the C-1c placeholder
        # descriptive string "0.15pt".
        self.assertEqual(recipe.contract.params["tolerance"], 0.15)
        self.assertEqual(recipe.contract.params["pure_threshold"], 1.5)

    def test_unbound_no_element_is_pointer_not_found(self):
        raw = {"id": "N003", "value": 1.0, "unit": "円", "subject": None, "form": "direct_value",
               "pointer": None, "bound": False, "reason": "no_element", "result": None}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.pointers, ())
        self.assertIsNone(recipe.contract)
        self.assertEqual(recipe.not_found_reason, "no_element")
        self.assertIsNone(recipe.unverifiable_reason)

    def test_unbound_no_subject_is_unverifiable(self):
        raw = {"id": "N004", "value": 1.0, "unit": "円", "subject": None, "form": "direct_value",
               "pointer": None, "bound": False, "reason": "no_subject", "result": None}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.unverifiable_reason, "no_subject")

    def test_ambiguous_elements_count_is_unverifiable(self):
        raw = {"id": "N005", "value": 1.0, "unit": "円", "subject": None, "form": "direct_value",
               "pointer": None, "bound": False, "reason": "ambiguous(3 elements)", "result": None}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.unverifiable_reason, "ambiguous(3 elements)")

    def test_value_mismatch_result_passes_through(self):
        raw = {"id": "N006", "value": 1.0, "unit": "円", "subject": "資産合計", "form": "direct_value",
               "pointer": "xbrl:jppfs_cor:Assets@CurrentYearInstant", "bound": True,
               "reason": "value differs(segment/other period?)", "result": "VALUE_MISMATCH", "recomputed": 2.0}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertIsNone(recipe.unverifiable_reason)
        self.assertIsNone(recipe.not_found_reason)
        self.assertIsNotNone(recipe.contract)

    def test_prior_is_zero_is_unverifiable_even_when_bound(self):
        raw = {"id": "N007", "value": 10.0, "unit": "%", "subject": "売上高", "form": "derived_value",
               "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration"],
               "bound": True, "reason": "prior is 0", "result": "UNVERIFIABLE", "recomputed": None}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.unverifiable_reason, "prior is 0")
        self.assertEqual(len(recipe.pointers), 2)


class ClaimToRecipeFlowSignTest(unittest.TestCase):
    """Core 接続 C-1g §1-2: flow_convention/claim_direction が raw claim に
    乗っているときの Contract(profile P6 のみが作る raw claim の形)。
    """

    def test_direct_value_with_flow_convention_uses_signed_params(self):
        raw = {
            "id": "N030", "sentence": 0, "span": "x", "value": 300297000.0, "unit": "円",
            "subject": "業務未払金", "form": "direct_value",
            "pointer": "xbrl:jppfs_cor:IncreaseDecreaseInAccountsPayableOther@CurrentYearDuration",
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": -300297000.0,
            "match": "round", "unit_scale": 1.0, "claim_scale": 1000.0,
            "flow_convention": 1, "claim_direction": -1,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "equals_within")
        self.assertEqual(recipe.contract.params["flow_convention"], 1)
        self.assertEqual(recipe.contract.params["claim_direction"], -1)
        self.assertEqual(recipe.contract.params["unit_scale"], 1.0)
        self.assertEqual(recipe.contract.params["claim_scale"], 1000.0)

    def test_direct_value_without_flow_convention_has_no_extra_params(self):
        raw = {
            "id": "N031", "value": 100.0, "unit": "円", "subject": "資産合計", "form": "direct_value",
            "pointer": "xbrl:jppfs_cor:Assets@CurrentYearInstant", "bound": True,
            "reason": None, "result": "GROUNDED", "recomputed": 100.0,
            "unit_scale": 1.0, "claim_scale": 1000.0,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertNotIn("flow_convention", recipe.contract.params)
        self.assertNotIn("claim_direction", recipe.contract.params)

    def test_text_claim_with_flow_convention_uses_flow_sign_comparator(self):
        raw = {
            "id": "T026", "word": "増加", "subject": "売上債権", "form": "threshold",
            "pointer": ["xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTrade@CurrentYearDuration",
                        "builtin:flow_sign(cur)==direction"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": -802686000.0,
            "direction": 1, "flow_convention": -1,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:flow_sign(cur)==direction")
        self.assertEqual(recipe.contract.params["direction"], 1)
        self.assertEqual(recipe.contract.params["flow_convention"], -1)
        self.assertEqual(len(recipe.pointers), 2)

    def test_text_claim_without_flow_convention_uses_sign_comparator(self):
        raw = {
            "id": "T002", "word": "増収", "subject": "売上高", "form": "threshold",
            "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration", "builtin:sign(cur-prior)"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 10.0, "direction": 1,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:sign(cur-prior)==direction")
        self.assertNotIn("flow_convention", recipe.contract.params)


class ClaimToRecipePointDiffTest(unittest.TestCase):
    """Core 接続 C-1g §1-3: ポイント差の derived_value(``formula:a-b(pure)``)。"""

    def test_point_diff_formula_uses_diff_pure100_comparator(self):
        raw = {
            "id": "N066", "value": 2.9, "unit": "ポイント", "subject": "自己資本比率", "form": "derived_value",
            "pointer": ["xbrl:jpcrp_cor:EquityToAssetRatio@CurrentYearInstant",
                        "xbrl:jpcrp_cor:EquityToAssetRatio@Prior1YearInstant", "formula:a-b(pure)"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 3.0,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "diff(a-b)(pure*100)")
        self.assertEqual(recipe.contract.params["tolerance"], 0.15)
        self.assertEqual(recipe.claim.modifiers.time_range, ("CurrentYear/Instant", "Prior1Year/Instant"))

    def test_point_without_prior_phrase_is_pointer_not_found(self):
        raw = {"id": "N088", "value": 1.3, "unit": "ポイント", "subject": "ROE", "form": "direct_value",
               "pointer": None, "bound": False, "reason": "no_element(point without prior phrase)", "result": None}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.not_found_reason, "no_element(point without prior phrase)")
        self.assertIsNone(recipe.unverifiable_reason)


class ClaimToRecipeDerivedValueTest(unittest.TestCase):
    def test_ratio_formula_uses_ratio100_comparator(self):
        raw = {
            "id": "N010", "value": 106.0, "unit": "%", "subject": "受注高", "form": "derived_value",
            "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration", "formula:cur/prior*100"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 106.0,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "ratio*100")
        self.assertEqual(recipe.claim.modifiers.time_range, ("CurrentYear/Duration", "Prior1Year/Duration"))

    def test_diff_formula_uses_diff_comparator(self):
        raw = {
            "id": "N011", "value": 100.0, "unit": "円", "subject": "資産合計", "form": "derived_value",
            "pointer": ["xbrl:a@CurrentYearInstant", "xbrl:a@Prior1YearInstant", "formula:a-b"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 100.0,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "diff(a-b) equals_within")

    def test_pct_change_without_formula_pointer_uses_default_comparator(self):
        raw = {
            "id": "N012", "value": 3.3, "unit": "%", "subject": "売上高", "form": "derived_value",
            "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 3.3, "sign_token": "3.3%増加",
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "pct_change(cur,prior)")
        self.assertEqual(recipe.claim.provenance["sign_token"], "3.3%増加")


class ClaimToRecipeTextTest(unittest.TestCase):
    def test_threshold_uses_sign_comparator(self):
        raw = {
            "id": "T001", "word": "増収", "subject": "売上高", "form": "threshold",
            "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration", "builtin:sign(cur-prior)"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 10.0,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:sign(cur-prior)==direction")
        # C-1d §3.1: this comparator's params carry "direction", not
        # "tolerance" (the raw dict here has no "word"/"direction" key,
        # so it resolves to None).
        self.assertIsNone(recipe.contract.params["direction"])
        self.assertIsNone(recipe.claim.value)
        self.assertIsNone(recipe.claim.unit)

    def test_state_word_is_unverifiable_no_line(self):
        raw = {"id": "T002", "word": "堅調", "subject": None, "form": "threshold",
               "pointer": None, "bound": False, "reason": "state_word(no line)", "result": "UNVERIFIABLE"}
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.unverifiable_reason, "state_word(no line)")


class PopulationFromMemberFieldTest(unittest.TestCase):
    def test_unbound_claim_carries_member_population(self):
        raw = {
            "id": "T017", "word": "減収", "subject": None, "form": "threshold",
            "pointer": None, "bound": False, "reason": "no_subject", "result": None,
            "member": "jpcrp030000-asr_E05055-000:FranchiseReportableSegmentMember",
            "member_source": "claim",
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.claim.modifiers.population, "member:FranchiseReportableSegmentMember")
        self.assertEqual(recipe.claim.provenance["member_source"], "claim")

    def test_bound_claim_member_population_from_pointer_context(self):
        raw = {
            "id": "N020", "value": 1.0, "unit": "千円", "subject": "売上高", "form": "direct_value",
            "pointer": "xbrl:jppfs_cor:NetSales@CurrentYearDuration_fooMember",
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 1000.0,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.claim.modifiers.population, "member:fooMember")


class ClaimToRecipeExpenditureSignTest(unittest.TestCase):
    """Core 接続 C-1h §1-1: expenditure_convention が raw claim に乗っている
    ときの Contract(profile P7 のみが作る raw claim の形)。
    """

    def test_text_claim_with_expenditure_convention_uses_abs_diff_comparator(self):
        raw = {
            "id": "T022", "word": "減少", "subject": "法人税等の支払額", "form": "threshold",
            "pointer": ["xbrl:jppfs_cor:IncomeTaxesPaid@CurrentYearDuration",
                        "xbrl:jppfs_cor:IncomeTaxesPaid@Prior1YearDuration", "builtin:sign(|cur|-|prior|)"],
            "bound": True, "reason": None, "result": "VALUE_MISMATCH", "recomputed": 19499000.0,
            "direction": -1, "expenditure_convention": True,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:sign(|cur|-|prior|)==direction")
        self.assertEqual(recipe.contract.params["direction"], -1)
        self.assertNotIn("flow_convention", recipe.contract.params)
        self.assertEqual(len(recipe.pointers), 3)

    def test_text_claim_without_expenditure_convention_uses_plain_sign_comparator(self):
        raw = {
            "id": "T002", "word": "増収", "subject": "売上高", "form": "threshold",
            "pointer": ["xbrl:a@CurrentYearDuration", "xbrl:a@Prior1YearDuration", "builtin:sign(cur-prior)"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 10.0, "direction": 1,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:sign(cur-prior)==direction")

    def test_flow_convention_takes_priority_over_expenditure_convention(self):
        # 仕様上この組は recipes.py の分岐で同時には立たないが、
        # claim_to_recipe 側の優先順位(flow が先)を直接固定する。
        raw = {
            "id": "T026", "word": "増加", "subject": "x", "form": "threshold",
            "pointer": ["xbrl:a@CurrentYearDuration", "builtin:flow_sign(cur)==direction"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": -1.0,
            "direction": 1, "flow_convention": -1, "expenditure_convention": True,
        }
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.contract.comparator, "builtin:flow_sign(cur)==direction")


class ClaimToRecipeTargetOrPlanTest(unittest.TestCase):
    """Core 接続 C-1h §1-2: ``target_or_plan`` は UNVERIFIABLE。"""

    def test_target_or_plan_is_unverifiable(self):
        raw = {"id": "N087", "value": 8.6, "unit": "%", "subject": None, "form": "direct_value",
               "pointer": None, "bound": False, "reason": "target_or_plan", "result": "UNVERIFIABLE"}
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.unverifiable_reason, "target_or_plan")
        self.assertIsNone(recipe.not_found_reason)
        self.assertEqual(recipe.pointers, ())
        self.assertIsNone(recipe.contract)


class ClaimToRecipeTextReasonSplitTest(unittest.TestCase):
    """Core 接続 C-1h §1-3: 文章 Claim の対が無い 2 つの新しい理由は
    POINTER_NOT_FOUND のまま。
    """

    def test_needs_money_fact_is_pointer_not_found(self):
        raw = {"id": "T045", "value": None, "unit": None, "subject": "自己資本比率", "form": "threshold",
               "pointer": None, "bound": False, "reason": "no_element(text needs money fact)", "result": None}
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.not_found_reason, "no_element(text needs money fact)")
        self.assertIsNone(recipe.unverifiable_reason)

    def test_no_prior_for_text_is_pointer_not_found(self):
        raw = {"id": "T050", "value": None, "unit": None, "subject": "資産合計", "form": "threshold",
               "pointer": None, "bound": False, "reason": "no_element(no prior for text)", "result": None}
        recipe = R.claim_to_recipe(raw, "text")
        self.assertEqual(recipe.not_found_reason, "no_element(no prior for text)")
        self.assertIsNone(recipe.unverifiable_reason)


class TargetOrPlanWindowTest(unittest.TestCase):
    """Core 接続 C-1h §1-2: 数の手前 10 字の窓(``_TARGET_WINDOW``)。文章
    Claim には掛からない・数の後ろの語は見ない。
    """

    @staticmethod
    def _claim_member(si, pos):
        return (None, None)

    def test_target_within_ten_chars_before_number_is_unverifiable(self):
        # "目標" (2 字) + 8 字の空白 = ちょうど 10 字手前。
        s = "目標" + ("x" * 8) + "8.6%にした。"
        claims = R._build_raw_num_claims([s], [], {}, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["reason"], "target_or_plan")
        self.assertEqual(claims[0]["result"], "UNVERIFIABLE")

    def test_target_eleven_chars_before_number_is_not_caught(self):
        # 1 字分だけ遠ざけると(11 字手前)窓の外。
        s = "目標" + ("x" * 9) + "8.6%にした。"
        claims = R._build_raw_num_claims([s], [], {}, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertNotEqual(claims[0]["reason"], "target_or_plan")

    def test_target_word_after_number_is_not_caught(self):
        # 1 社目 N013 型: 語が数の後ろにあるときは直らない(C-1h 予測の前提)。
        s = "ROEを10%以上とすることを目標とする。"
        claims = R._build_raw_num_claims([s], [], {}, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertNotEqual(claims[0]["reason"], "target_or_plan")

    def test_target_word_does_not_affect_text_claims(self):
        # 文章 Claim には掛けない: 同じ「目標」つきの文でも方向語の Claim の
        # reason は target_or_plan にならない。
        s = "目標として自己資本比率は増加した。"
        facts = [{"name": "jppfs_cor:CapitalAdequacyRatio", "context": "CurrentYearDuration", "unit": "pure", "value": 0.5}]
        claims = R._build_raw_text_claims([s], facts, {"CurrentYearDuration": {"members": []}}, V.P7, self._claim_member)
        self.assertTrue(claims)
        for c in claims:
            self.assertNotEqual(c.get("reason"), "target_or_plan")

    def test_p1_p5f_p6_are_unaffected_by_target_word(self):
        s = "目標" + ("x" * 8) + "8.6%にした。"
        for profile in (V.P1, V.P5F, V.P6):
            claims = R._build_raw_num_claims([s], [], {}, profile, self._claim_member)
            self.assertEqual(len(claims), 1)
            self.assertNotEqual(claims[0]["reason"], "target_or_plan")


class ExpenditureConventionTextClaimBuildTest(unittest.TestCase):
    """Core 接続 C-1h §1-1: ``_build_raw_text_claims`` が実際に作る raw claim
    (3 社目 T022/T025 を単純化した合成版)。
    """

    @staticmethod
    def _claim_member(si, pos):
        return (None, None)

    def test_magnitude_increase_mismatches_decrease_word(self):
        # |-86046| - |-66547| = +19499 (大きさは増えた) != 「減少」。
        facts = [
            {"name": "jppfs_cor:IncomeTaxesPaid", "context": "CurrentYearDuration", "unit": "JPY", "value": -86046.0},
            {"name": "jppfs_cor:IncomeTaxesPaid", "context": "Prior1YearDuration", "unit": "JPY", "value": -66547.0},
        ]
        contexts = {"CurrentYearDuration": {"members": []}, "Prior1YearDuration": {"members": []}}
        claims = R._build_raw_text_claims(
            ["法人税等の支払額86百万円等の減少。"], facts, contexts, V.P7, self._claim_member
        )
        self.assertEqual(len(claims), 1)
        c = claims[0]
        self.assertTrue(c["bound"])
        self.assertTrue(c["expenditure_convention"])
        self.assertEqual(c["result"], "VALUE_MISMATCH")
        self.assertEqual(c["recomputed"], 19499.0)
        self.assertEqual(c["pointer"][-1], "builtin:sign(|cur|-|prior|)")

    def test_magnitude_decrease_matches_decrease_word(self):
        # |-143940| - |-219930| = -75990 (大きさは減った) == 「減少」。
        facts = [
            {"name": "jppfs_cor:PurchaseOfInvestmentSecurities", "context": "CurrentYearDuration", "unit": "JPY", "value": -143940.0},
            {"name": "jppfs_cor:PurchaseOfInvestmentSecurities", "context": "Prior1YearDuration", "unit": "JPY", "value": -219930.0},
        ]
        contexts = {"CurrentYearDuration": {"members": []}, "Prior1YearDuration": {"members": []}}
        claims = R._build_raw_text_claims(
            ["投資有価証券の取得による支出143百万円等の減少。"], facts, contexts, V.P7, self._claim_member
        )
        self.assertEqual(len(claims), 1)
        c = claims[0]
        self.assertEqual(c["result"], "GROUNDED")
        self.assertEqual(c["recomputed"], -75990.0)

    def test_non_expenditure_subject_is_never_flagged(self):
        # 語彙上の elems が「支出」系の接頭辞を持たない主語(例: 「資産合計」
        # -> ["Assets"])は、profile.expenditure_sign が真でも
        # expenditure_convention が立たない(V.expenditure_convention の
        # 判定は elems の列に対して行うので、対応する語彙が無ければ無関係)。
        facts = [
            {"name": "jppfs_cor:Assets", "context": "CurrentYearDuration", "unit": "JPY", "value": 100.0},
            {"name": "jppfs_cor:Assets", "context": "Prior1YearDuration", "unit": "JPY", "value": 50.0},
        ]
        contexts = {"CurrentYearDuration": {"members": []}, "Prior1YearDuration": {"members": []}}
        claims = R._build_raw_text_claims(["資産合計は増加した。"], facts, contexts, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertNotIn("expenditure_convention", claims[0])
        self.assertEqual(claims[0]["pointer"][-1], "builtin:sign(cur-prior)")


class TextUnboundReasonSplitBuildTest(unittest.TestCase):
    """Core 接続 C-1h §1-3: ``_build_raw_text_claims`` で対が無い場合の
    理由の分割((a)/(b)/(c))。P6 は不変(§1-3 は profile.text_reason_split
    が真のときだけ)。
    """

    @staticmethod
    def _claim_member(si, pos):
        return (None, None)

    def test_a_pure_only_fact_needs_money_fact(self):
        facts = [{"name": "jppfs_cor:CapitalAdequacyRatio", "context": "CurrentYearDuration", "unit": "pure", "value": 0.5}]
        contexts = {"CurrentYearDuration": {"members": []}}
        claims = R._build_raw_text_claims(["自己資本比率は増加した。"], facts, contexts, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["reason"], "no_element(text needs money fact)")

    def test_b_jpy_current_without_prior_needs_prior_for_text(self):
        facts = [{"name": "jppfs_cor:Assets", "context": "CurrentYearDuration", "unit": "JPY", "value": 100.0}]
        contexts = {"CurrentYearDuration": {"members": []}}
        claims = R._build_raw_text_claims(["資産合計は増加した。"], facts, contexts, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["reason"], "no_element(no prior for text)")

    def test_c_no_fact_at_all_stays_no_element(self):
        claims = R._build_raw_text_claims(["退職給付に係る負債は増加した。"], [], {}, V.P7, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["reason"], "no_element")

    def test_p6_is_unaffected_by_reason_split(self):
        # 同じ材料でも P6(text_reason_split=False)は従来どおり no_element。
        facts = [{"name": "jppfs_cor:CapitalAdequacyRatio", "context": "CurrentYearDuration", "unit": "pure", "value": 0.5}]
        contexts = {"CurrentYearDuration": {"members": []}}
        claims = R._build_raw_text_claims(["自己資本比率は増加した。"], facts, contexts, V.P6, self._claim_member)
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["reason"], "no_element")


class WindowBoundaryTest(unittest.TestCase):
    """Core 接続 C-1h §1-4(人間の決定、2026-10-06): 窓幅を字で留める試験。
    境界の両側(字が入る/入らない)を直接呼び出しで確かめる。
    """

    def test_flow_direction_word_catches_word_at_fourth_char_after_number(self):
        # subj の直後に数(a==len(subj))、数の直後(window2)の 4 字目までに
        # 語の末尾が収まるケース。
        subj = "業務未払金"
        s = subj + "100" + "ab" + "減少" + "。"
        a = len(subj)
        b = a + 3
        self.assertEqual(R._flow_direction_word(s, subj, a, b), -1)

    def test_flow_direction_word_does_not_catch_word_at_fifth_char(self):
        subj = "業務未払金"
        s = subj + "100" + "abc" + "減少" + "。"
        a = len(subj)
        b = a + 3
        self.assertIsNone(R._flow_direction_word(s, subj, a, b))

    def _point_diff_claim_at(self, gap):
        """前期の語(「前年」)が数の手前ちょうど ``25 - gap`` 字目に来るように
        組んだ合成文で ``_build_point_diff_claim`` を直接呼ぶ。facts は空
        (対が無いので reason だけを見る)。
        """

        phrase = "前年"
        a = 30
        prefix = ("x" * gap) + phrase + ("y" * (a - gap - len(phrase)))
        self.assertEqual(len(prefix), a)
        s = prefix + "2.9ポイント増加。"
        b = a + 3
        claim = {"reason": None, "bound": False, "form": None, "pointer": None, "value": None, "result": None}
        R._build_point_diff_claim(claim, s, a, b, ["EquityToAssetRatio"], None, [], {}, 2.9)
        return claim

    def test_point_diff_prior_phrase_caught_at_window_edge(self):
        # phrase が窓のちょうど先頭(a - 25)に来る(gap=5 -> 前年は index5-6、
        # window は s[5:30])。
        claim = self._point_diff_claim_at(gap=5)
        self.assertNotEqual(claim["reason"], "no_element(point without prior phrase)")

    def test_point_diff_prior_phrase_missed_one_char_earlier(self):
        # phrase を 1 字早めると(gap=4)、窓の外側に 1 字こぼれて見つからない。
        claim = self._point_diff_claim_at(gap=4)
        self.assertEqual(claim["reason"], "no_element(point without prior phrase)")

    def _direct_value_claim_is_diff(self, gap):
        """「比べて」が数の手前ちょうど ``25 - gap`` 字目に来るように組んだ
        合成文で ``_direct_value_claim`` を呼び、is_diff が立ったかどうかを
        claim["form"] の変化(pair 探索なら "derived_value" になる)で見る。
        """

        phrase = "比べて"
        a = 30
        prefix = ("x" * gap) + phrase + ("y" * (a - gap - len(phrase)))
        self.assertEqual(len(prefix), a)
        s = prefix + "100千円。"
        b = a + 3
        facts = [
            {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration", "unit": "JPY", "value": 100000.0},
            {"name": "jppfs_cor:NetSales", "context": "Prior1YearDuration", "unit": "JPY", "value": 0.0},
        ]
        contexts = {"CurrentYearDuration": {"members": []}, "Prior1YearDuration": {"members": []}}
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None}
        R._direct_value_claim(claim, s, a, b, 1, 100.0, "千円", None, "売上高", ["NetSales"], None, facts, contexts)
        return claim

    def test_direct_value_diff_phrase_caught_at_window_edge(self):
        claim = self._direct_value_claim_is_diff(gap=5)
        self.assertEqual(claim["form"], "derived_value")

    def test_direct_value_diff_phrase_missed_one_char_earlier(self):
        claim = self._direct_value_claim_is_diff(gap=4)
        self.assertEqual(claim["form"], "direct_value")


if __name__ == "__main__":
    unittest.main()
