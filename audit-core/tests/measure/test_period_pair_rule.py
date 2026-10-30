# -*- coding: utf-8 -*-
u"""規則 PP(measure/xbrl_period_pair_rule_2026-10-19.py)の単体試験。

封 `docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md` §0 の条件・除外・符号・対照を 1 本ずつ当てる。
**合成の fact で当てる**(実物の 8 書類は別に `tests/measure/test_xbrl_period_pair_result.py` で固定)。
"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, ROOT)

import audit_core as core                           # noqa: E402
from adapters.xbrl import registry_setup as RS        # noqa: E402

_sp = importlib.util.spec_from_file_location(
    "pp_rule_test", os.path.join(ROOT, "measure", "xbrl_period_pair_rule_2026-10-19.py"))
R = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(R)

REGISTRY = RS.register_all(core.Registry.default())


def fact(name, ctx, value, unit=u"JPY"):
    return {"name": name, "context": ctx, "value": value, "unit": unit}


class PeriodTagTest(unittest.TestCase):
    def test_1_period_tag_is_before_the_first_underscore(self):
        self.assertEqual(R.period_tag("CurrentYearDuration"), "CurrentYearDuration")
        self.assertEqual(R.period_tag("CurrentYearDuration_Seg"), "CurrentYearDuration")
        self.assertEqual(R.period_tag("Prior1YearDuration_Seg_Member"), "Prior1YearDuration")


class PriorSiblingsTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns:NetSales", "CurrentYearDuration", 100.0, u"％")

    def test_2_fires_with_exactly_one_sibling(self):
        g = fact("ns:NetSales", "Prior1YearDuration", 90.0, u"JPY")
        sibs = R.prior_siblings([self.f, g], self.f)
        self.assertEqual(sibs, [g])

    def test_3_zero_siblings_is_an_empty_list_not_none(self):
        sibs = R.prior_siblings([self.f], self.f)
        self.assertEqual(sibs, [])

    def test_4_a_duplicate_prior_year_fact_counts_as_two_siblings(self):
        u"""実物の 8 書類の「2 本」は次元違いではなく、instance 内の重複
        (同じ name・同じ context の fact が 2 回出る)である(2026-10-19 実測、
        `S100YWGX` R004)。重複の判定は PP の仕事ではない ― 本数だけ数える。"""
        g1 = fact("ns:NetSales", "Prior1YearDuration", 90.0)
        g2 = fact("ns:NetSales", "Prior1YearDuration", 90.0)
        sibs = R.prior_siblings([self.f, g1, g2], self.f)
        self.assertEqual(len(sibs), 2)

    def test_5_a_sibling_in_a_different_dimension_is_not_counted(self):
        u"""封の当たらない例の 1 つ目: 兄弟が `Prior1YearDuration` と
        `Prior1YearDuration_XMember` の 2 本(次元が違う)→ `dim_of` が違うので 1 本。"""
        same = fact("ns:NetSales", "Prior1YearDuration", 90.0)
        other_dim = fact("ns:NetSales", "Prior1YearDuration_XMember", 90.0)
        sibs = R.prior_siblings([self.f, same, other_dim], self.f)
        self.assertEqual(sibs, [same])

    def test_6_a_sibling_must_share_the_dimension_of_f_too(self):
        f = fact("ns:NetSales", "CurrentYearDuration_Seg", 100.0)
        same_dim = fact("ns:NetSales", "Prior1YearDuration_Seg", 90.0)
        other_dim = fact("ns:NetSales", "Prior1YearDuration_Other", 90.0)
        sibs = R.prior_siblings([f, same_dim, other_dim], f)
        self.assertEqual(sibs, [same_dim])

    def test_7_a_different_element_is_not_a_sibling(self):
        g = fact("ns:OrdinaryIncome", "Prior1YearDuration", 90.0)
        self.assertEqual(R.prior_siblings([self.f, g], self.f), [])

    def test_8_does_not_apply_to_a_fact_that_is_not_current_year(self):
        u"""封の当たらない例の 2 つ目: 期間の札が `Prior1YearDuration` の fact を
        名指した主張には PP を当てない(`None` を返す)。"""
        g = fact("ns:NetSales", "Prior1YearDuration", 90.0)
        self.assertIsNone(R.prior_siblings([self.f, g], g))
        self.assertIsNone(R.prior_siblings([self.f], fact("ns:NetSales", "InstantDuration", 1.0)))


class SignFromTextTest(unittest.TestCase):
    def test_9_up_words_give_plus_one(self):
        for w in (u"増", u"伸", u"上回"):
            excerpt = u"セグメント利益は258.0％%sました" % w
            self.assertEqual(R.sign_from_text(excerpt, "258.0"), 1, w)

    def test_10_down_words_give_minus_one(self):
        for w in (u"減", u"下回", u"落ち"):
            excerpt = u"前期比9.2％%sました" % w
            self.assertEqual(R.sign_from_text(excerpt, "9.2"), -1, w)

    def test_11_neither_word_is_sign_unknown(self):
        excerpt = u"前期比9.2％でした変わらず"
        self.assertIsNone(R.sign_from_text(excerpt, "9.2"))

    def test_12_a_word_outside_the_window_does_not_count(self):
        far = u"9.2％" + (u"ア" * R.SIGN_WINDOW) + u"増加"
        self.assertIsNone(R.sign_from_text(far, "9.2"))

    def test_13_repeated_number_text_uses_the_first_occurrence(self):
        u"""数の字面が複数回出るなら、最初に出た位置を採る。"""
        excerpt = u"9.2％減でした。別の場所でも9.2％増と書かれている"
        self.assertEqual(R.sign_from_text(excerpt, "9.2"), -1)

    def test_14_number_text_not_found_is_sign_unknown(self):
        self.assertIsNone(R.sign_from_text(u"全く関係ない文章", "9.2"))


class ApplyPpTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns:NetSales", "CurrentYearDuration", 100.0, u"JPY")
        self.g = fact("ns:NetSales", "Prior1YearDuration", 90.0, u"JPY")
        self.facts = [self.f, self.g]
        # pct = (100 - 90) / 90 * 100 = 11.111...

    def spec(self, value, sign=1, unit=u"％"):
        return {"kind": "ratio_change", "value": value, "unit": unit,
                "pointers": ["ns:NetSales@CurrentYearDuration"], "sign": sign}

    def test_15_one_sibling_signed_match_is_grounded(self):
        out = R.apply_pp(self.spec(11.11, sign=1), self.f, self.facts, REGISTRY)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertAlmostEqual(out["recomputed"], 11.11, places=2)
        self.assertEqual(out["derived_pointers"], ["ns:NetSales@Prior1YearDuration"])
        self.assertTrue(out["sign_checked"])

    def test_16_one_sibling_value_mismatch(self):
        out = R.apply_pp(self.spec(50.0, sign=1), self.f, self.facts, REGISTRY)
        self.assertEqual(out["state"], "VALUE_MISMATCH")

    def test_17_flipping_the_sign_turns_a_match_into_a_mismatch(self):
        u"""対照 符号: 増 <-> 減 を入れ替えると VALUE_MISMATCH になる。"""
        matched = R.apply_pp(self.spec(11.11, sign=1), self.f, self.facts, REGISTRY)
        flipped = R.apply_pp(self.spec(11.11, sign=-1), self.f, self.facts, REGISTRY)
        self.assertEqual(matched["state"], "GROUNDED")
        self.assertEqual(flipped["state"], "VALUE_MISMATCH")

    def test_18_zero_siblings_is_unprovable_with_the_count_in_the_reason(self):
        out = R.apply_pp(self.spec(11.11), self.f, [self.f], REGISTRY)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(out["reason"], "prior_sibling:0")
        self.assertEqual(out["derived_pointers"], [])

    def test_19_two_siblings_is_unprovable_with_the_count_in_the_reason(self):
        g2 = fact("ns:NetSales", "Prior1YearDuration", 90.0)
        out = R.apply_pp(self.spec(11.11), self.f, self.facts + [g2], REGISTRY)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(out["reason"], "prior_sibling:2")

    def test_20_does_not_apply_when_f_is_not_current_year(self):
        out = R.apply_pp(self.spec(11.11), self.g, self.facts, REGISTRY)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(out["reason"], "not_current_year")

    def test_21_sign_unknown_compares_the_absolute_value(self):
        out_pos = R.apply_pp(self.spec(11.11, sign=None), self.f, self.facts, REGISTRY)
        self.assertFalse(out_pos["sign_checked"])
        self.assertEqual(out_pos["state"], "GROUNDED")

    def test_22_the_claims_own_pointer_is_never_changed(self):
        spec = self.spec(11.11, sign=1)
        before = list(spec["pointers"])
        R.apply_pp(spec, self.f, self.facts, REGISTRY)
        self.assertEqual(spec["pointers"], before)

    def test_23_no_fact_resolved_is_unprovable(self):
        out = R.apply_pp(self.spec(11.11), None, self.facts, REGISTRY)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(out["reason"], "no_fact")

    def test_24_comparator_is_the_sealed_pct_change_only(self):
        u"""比較器は既存の `pct_change(cur,prior)` だけ(新しい閾値を作らない)。"""
        out = R.apply_pp(self.spec(11.11, sign=1), self.f, self.facts, REGISTRY)
        self.assertEqual(out["recomputed"], round((100.0 - 90.0) / 90.0 * 100, 2))

    def test_25_dim_of_is_the_engines_own_function(self):
        self.assertTrue(R.dim_of.__code__.co_filename.endswith("holds.py"))


if __name__ == "__main__":
    unittest.main()
