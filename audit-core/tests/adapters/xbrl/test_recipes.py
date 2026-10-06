# -*- coding: utf-8 -*-
import unittest

import audit_core as core

from adapters.xbrl import recipes as R


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


if __name__ == "__main__":
    unittest.main()
