# -*- coding: utf-8 -*-
u"""(d) の規則(measure/xbrl_dim_hold_rule_2026-10-17.py)の単体試験。

**封 `docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md` の条件・除外・遷移を 1 本ずつ当てる。**
**除外条件は正常な材料では黙るので、故障を作って当てる**
(記憶 `guard-that-only-fires-on-failure`)。
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_sp = importlib.util.spec_from_file_location(
    "dim_hold_rule", os.path.join(ROOT, "measure",
                                  "xbrl_dim_hold_rule_2026-10-17.py"))
H = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(H)

TOL = 1000000.0            # 百万円 1 単位分


def fact(name, ctx, value, unit="JPY"):
    return {"name": name, "context": ctx, "value": value, "unit": unit}


def ok(pointers=("a@CurrentYearDuration",)):
    return {"state": "GROUNDED", "pointers": tuple(pointers),
            "rule": u"単一の値(金額)", "reason": None}


class DimOfTest(unittest.TestCase):
    def test_1_dim_of_splits_at_the_first_underscore(self):
        self.assertEqual(H.dim_of("CurrentYearDuration"), "")
        self.assertEqual(H.dim_of("CurrentYearDuration_NonConsolidatedMember"),
                         "NonConsolidatedMember")
        self.assertEqual(H.dim_of("Prior1YearDuration_A_B"), "A_B")

    def test_2_period_only_difference_has_the_same_dim(self):
        self.assertEqual(H.dim_of("Prior1YearDuration_X"),
                         H.dim_of("CurrentYearDuration_X"))


class FiringTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)

    def test_3_fires_on_a_same_value_dimension_sibling(self):
        g = fact("ns", "CurrentYearDuration_SegMember", 100.0)
        out, sibs = H.apply_hold(ok(), self.f, [self.f, g], TOL)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertTrue(out["held"])
        self.assertEqual(out["reason"], "ambiguous_dimension:1")
        self.assertEqual(sibs, [g])

    def test_4_the_count_in_the_reason_is_the_number_of_siblings(self):
        gs = [fact("ns", "CurrentYearDuration_A" , 100.0),
              fact("ns", "CurrentYearDuration_B", 100.0)]
        out, sibs = H.apply_hold(ok(), self.f, [self.f] + gs, TOL)
        self.assertEqual(out["reason"], "ambiguous_dimension:2")
        self.assertEqual(len(sibs), 2)

    def test_5_fires_symmetrically_when_the_pointer_is_dimensioned(self):
        u"""**次元つきの参照先に、次元なしの同額兄弟**が在るときも発火する。"""
        f = fact("ns", "CurrentYearDuration_SegMember", 100.0)
        g = fact("ns", "CurrentYearDuration", 100.0)
        out, sibs = H.apply_hold(ok(), f, [f, g], TOL)
        self.assertEqual(out["state"], "UNPROVABLE")
        self.assertEqual(sibs, [g])

    def test_6_does_not_fire_without_a_sibling(self):
        out, sibs = H.apply_hold(ok(), self.f, [self.f], TOL)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(sibs, [])
        self.assertNotIn("held", out)

    def test_7_tolerance_is_a_closed_band(self):
        inside = fact("ns", "CurrentYearDuration_X", 100.0 + TOL)
        outside = fact("ns", "CurrentYearDuration_X", 100.0 + TOL + 1)
        self.assertEqual(len(H.siblings([self.f, inside], self.f, TOL)), 1)
        self.assertEqual(len(H.siblings([self.f, outside], self.f, TOL)), 0)


class ExclusionTest(unittest.TestCase):
    u"""**除外条件は故障を作って当てる。**"""

    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)

    def test_8_period_only_sibling_does_not_fire(self):
        g = fact("ns", "Prior1YearDuration", 100.0)
        out, sibs = H.apply_hold(ok(), self.f, [self.f, g], TOL)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(sibs, [])

    def test_9_period_only_sibling_inside_a_dimension_does_not_fire(self):
        f = fact("ns", "CurrentYearDuration_SegMember", 100.0)
        g = fact("ns", "Prior1YearDuration_SegMember", 100.0)
        self.assertEqual(H.siblings([f, g], f, TOL), [])

    def test_10_unit_only_sibling_does_not_fire(self):
        g = fact("ns", "CurrentYearDuration_X", 100.0, unit="USD")
        out, sibs = H.apply_hold(ok(), self.f, [self.f, g], TOL)
        self.assertEqual(out["state"], "GROUNDED")
        self.assertEqual(sibs, [])

    def test_11_a_different_element_does_not_fire(self):
        g = fact("other", "CurrentYearDuration_X", 100.0)
        self.assertEqual(H.siblings([self.f, g], self.f, TOL), [])

    def test_12_a_none_value_does_not_fire(self):
        g = fact("ns", "CurrentYearDuration_X", None)
        self.assertEqual(H.siblings([self.f, g], self.f, TOL), [])


class StateTest(unittest.TestCase):
    u"""**封 §4 の表以外の遷移を作っていないこと。**"""

    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)
        self.g = fact("ns", "CurrentYearDuration_X", 100.0)

    def test_13_mismatch_is_never_upgraded_to_a_hold(self):
        out = dict(ok(), state="VALUE_MISMATCH", reason="value")
        new, sibs = H.apply_hold(out, self.f, [self.f, self.g], TOL)
        self.assertEqual(new, out)
        self.assertEqual(sibs, [])

    def test_14_other_states_are_untouched(self):
        for st in ("POINTER_NOT_FOUND", "UNPROVABLE"):
            out = dict(ok(), state=st)
            new, sibs = H.apply_hold(out, self.f, [self.f, self.g], TOL)
            self.assertEqual(new, out, st)
            self.assertEqual(sibs, [], st)

    def test_15_an_unresolved_pointer_is_untouched(self):
        out = ok()
        new, sibs = H.apply_hold(out, None, [self.f, self.g], TOL)
        self.assertEqual(new, out)
        self.assertEqual(sibs, [])

    def test_16_the_pointers_are_never_changed_or_added(self):
        out = ok(("p1@CurrentYearDuration",))
        new, _s = H.apply_hold(out, self.f, [self.f, self.g], TOL)
        self.assertEqual(new["pointers"], out["pointers"])
        self.assertEqual(len(new["pointers"]), 1)
        #: **兄弟は件数としてしか出さない**(封 §3-2)
        self.assertNotIn(self.g["context"], repr(new))
        self.assertEqual(new["hold_siblings"], 1)

    def test_17_the_input_dict_is_not_mutated(self):
        out = ok()
        before = dict(out)
        H.apply_hold(out, self.f, [self.f, self.g], TOL)
        self.assertEqual(out, before)

    def test_18_the_hold_never_becomes_a_pass(self):
        u"""**この規則は減らす方向にしか動かない**(封 §3-2)。"""
        for st in ("GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND",
                   "UNPROVABLE"):
            new, _s = H.apply_hold(dict(ok(), state=st), self.f,
                                   [self.f, self.g], TOL)
            self.assertNotEqual((st, new["state"]), (st, "GROUNDED")
                                if st != "GROUNDED" else (None, None))
            if st != "GROUNDED":
                self.assertEqual(new["state"], st)


if __name__ == "__main__":
    unittest.main()
