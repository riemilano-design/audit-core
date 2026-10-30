# -*- coding: utf-8 -*-
u"""規則 P・U と合成(measure/xbrl_period_unit_hold_rule_2026-10-19.py)の単体試験。

封 `docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md` の条件・除外・遷移を 1 本ずつ当てる。
**除外条件は正常な材料では黙るので、故障を作って当てる。**
"""
import copy
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_sp = importlib.util.spec_from_file_location(
    "pu_hold_rule", os.path.join(ROOT, "measure", "xbrl_period_unit_hold_rule_2026-10-19.py"))
R = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(R)

TOL = 1000000.0


def fact(name, ctx, value, unit="JPY"):
    return {"name": name, "context": ctx, "value": value, "unit": unit}


def ok(pointers=("a@CurrentYearDuration",), state="GROUNDED"):
    return {"state": state, "pointers": tuple(pointers), "rule": u"単一の値(金額)", "reason": None}


class PeriodRuleTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)

    def test_1_fires_on_a_same_value_period_sibling(self):
        g = fact("ns", "Prior1YearDuration", 100.0)
        out, sibs = R.apply_period_hold(ok(), self.f, [self.f, g], TOL)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertTrue(out["held"])
        self.assertEqual(out["reason"], "ambiguous_period:1")
        self.assertEqual(sibs, [g])

    def test_2_fires_inside_a_dimension_too(self):
        f = fact("ns", "CurrentYearDuration_Seg", 100.0)
        g = fact("ns", "Prior1YearDuration_Seg", 100.0)
        self.assertEqual(R.period_siblings([f, g], f, TOL), [g])

    def test_3_dimension_only_sibling_does_not_fire(self):
        g = fact("ns", "CurrentYearDuration_Seg", 100.0)
        out, sibs = R.apply_period_hold(ok(), self.f, [self.f, g], TOL)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(sibs, [])

    def test_4_unit_only_sibling_does_not_fire(self):
        g = fact("ns", "Prior1YearDuration", 100.0, unit="USD")
        self.assertEqual(R.period_siblings([self.f, g], self.f, TOL), [])

    def test_5_different_element_or_none_value_does_not_fire(self):
        self.assertEqual(R.period_siblings([self.f, fact("other", "Prior1YearDuration", 100.0)], self.f, TOL), [])
        self.assertEqual(R.period_siblings([self.f, fact("ns", "Prior1YearDuration", None)], self.f, TOL), [])

    def test_6_tolerance_is_a_closed_band(self):
        inside = fact("ns", "Prior1YearDuration", 100.0 + TOL)
        outside = fact("ns", "Prior1YearDuration", 100.0 + TOL + 1)
        self.assertEqual(len(R.period_siblings([self.f, inside], self.f, TOL)), 1)
        self.assertEqual(len(R.period_siblings([self.f, outside], self.f, TOL)), 0)

    def test_7_count_in_the_reason(self):
        gs = [fact("ns", "Prior1YearDuration", 100.0), fact("ns", "Prior2YearDuration", 100.0)]
        out, _s = R.apply_period_hold(ok(), self.f, [self.f] + gs, TOL)
        self.assertEqual(out["reason"], "ambiguous_period:2")


class UnitRuleTest(unittest.TestCase):
    def test_8_claim_classes_are_the_sealed_table(self):
        for u in (u"百万円", u"千円", u"億円", u"兆円", u"円"):
            self.assertEqual(R.claim_class(u), "JPY", u)
        for u in (u"%", u"％"):
            self.assertEqual(R.claim_class(u), "pure", u)
        for u in (None, u"株", u"人", u""):
            self.assertIsNone(R.claim_class(u), u)

    def test_9_fires_on_usd_for_a_money_claim(self):
        f = fact("ns", "CurrentYearDuration_UnitTest", 100.0, unit="USD")
        out, fired = R.apply_unit_hold(ok(), f, u"百万円")
        self.assertTrue(fired)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(out["reason"], "unit_class_mismatch:JPY/USD")

    def test_10_fires_when_a_money_claim_points_at_shares_or_pure(self):
        for fu in ("shares", "pure", "JPYPerShares"):
            f = fact("ns", "CurrentYearDuration", 100.0, unit=fu)
            self.assertTrue(R.apply_unit_hold(ok(), f, u"千円")[1], fu)

    def test_11_does_not_fire_on_the_same_class(self):
        self.assertFalse(R.apply_unit_hold(ok(), fact("ns", "c", 1.0, "JPY"), u"百万円")[1])
        self.assertFalse(R.apply_unit_hold(ok(), fact("ns", "c", 0.1, "pure"), u"％")[1])

    def test_12_none_claim_unit_or_none_fact_unit_is_not_judged(self):
        self.assertFalse(R.apply_unit_hold(ok(), fact("ns", "c", 1.0, "USD"), None)[1])
        self.assertFalse(R.apply_unit_hold(ok(), fact("ns", "c", 1.0, None), u"百万円")[1])
        self.assertFalse(R.apply_unit_hold(ok(), fact("ns", "c", 1.0, "USD"), u"株")[1])


class StateTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        self.g = fact("ns", "Prior1YearDuration", 100.0, unit="USD")

    def test_13_non_grounded_states_are_untouched_by_both_rules(self):
        for st in ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNPROVABLE"):
            out = ok(state=st)
            self.assertEqual(R.apply_period_hold(out, self.f, [self.f, self.g], TOL), (out, []), st)
            self.assertEqual(R.apply_unit_hold(out, self.f, u"百万円"), (out, False), st)
            new, fired = R.apply_all(out, self.f, [self.f, self.g], TOL, u"百万円")
            self.assertEqual(new, out, st)
            self.assertEqual(fired, {"d": False, "P": False, "U": False}, st)

    def test_14_unresolved_pointer_is_untouched(self):
        out = ok()
        self.assertEqual(R.apply_period_hold(out, None, [self.g], TOL), (out, []))
        self.assertEqual(R.apply_unit_hold(out, None, u"百万円"), (out, False))

    def test_15_composition_concatenates_reasons_in_order_d_p_u(self):
        f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        facts = [f, fact("ns", "CurrentYearDuration_Seg", 100.0, unit="USD"),
                 fact("ns", "Prior1YearDuration", 100.0, unit="USD")]
        new, fired = R.apply_all(ok(), f, facts, TOL, u"百万円")
        self.assertEqual(fired, {"d": True, "P": True, "U": True})
        self.assertEqual(new["state"], "UNPROVABLE")
        self.assertEqual(new["reason"],
                         "ambiguous_dimension:1;ambiguous_period:1;unit_class_mismatch:JPY/USD")
        self.assertEqual(new["hold_rules"], ("d", "P", "U"))

    def test_16_composition_leaves_grounded_when_nothing_fires(self):
        f = fact("ns", "CurrentYearDuration", 100.0)
        out = ok()
        new, fired = R.apply_all(out, f, [f, fact("ns", "Prior1YearDuration", 100.0 + TOL + 1)], TOL, u"百万円")
        self.assertEqual(new, out)
        self.assertEqual(fired, {"d": False, "P": False, "U": False})

    def test_17_pointers_and_inputs_are_never_changed(self):
        f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        facts = [f, fact("ns", "Prior1YearDuration", 100.0, unit="USD")]
        out = ok()
        snap = (copy.deepcopy(out), copy.deepcopy(facts))
        new, _fired = R.apply_all(out, f, facts, TOL, u"百万円")
        self.assertEqual(new["pointers"], out["pointers"])
        self.assertEqual((out, facts), snap)

    def test_18_dim_of_is_the_d_rules_function(self):
        self.assertTrue(R.dim_of.__code__.co_filename.endswith("xbrl_dim_hold_rule_2026-10-17.py"))
        self.assertTrue(R.D.apply_hold.__code__.co_filename.endswith("xbrl_dim_hold_rule_2026-10-17.py"))


if __name__ == "__main__":
    unittest.main()
