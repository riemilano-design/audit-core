# -*- coding: utf-8 -*-
"""保留規則 (d)・P・U(``adapters/xbrl/holds.py``)と枠の軸(``instance.load_instance`` の ``axes``)。

封 `docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md`。**合成の材料だけで動く**(変異の砂場でも走る)。
``measure/`` の規則の試験(``tests/measure/test_dim_hold_rule.py``・``test_period_unit_hold_rule.py``)の写し
に、軸の記録と「写しが `measure/` の規則と同じ答えを出す」同値の試験を足した。
"""
import copy
import importlib.util
import io
import itertools
import os
import unittest
import zipfile

from adapters.xbrl import holds as H
from adapters.xbrl import instance as I

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
TOL = 1000000.0


def fact(name, ctx, value, unit="JPY"):
    return {"name": name, "context": ctx, "value": value, "unit": unit}


def ok(state="GROUNDED", pointers=("a@CurrentYearDuration",)):
    return {"state": state, "pointers": tuple(pointers), "rule": u"単一の値(金額)", "reason": None}


class DimensionRuleTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)

    def test_fires_on_a_same_value_dimension_sibling_symmetrically(self):
        g = fact("ns", "CurrentYearDuration_SegMember", 100.0)
        self.assertEqual(H.dimension_siblings([self.f, g], self.f, TOL), [g])
        self.assertEqual(H.dimension_siblings([self.f, g], g, TOL), [self.f])

    def test_period_only_unit_only_other_element_none_value_do_not_fire(self):
        for g in (fact("ns", "Prior1YearDuration", 100.0),
                  fact("ns", "CurrentYearDuration_X", 100.0, unit="USD"),
                  fact("other", "CurrentYearDuration_X", 100.0),
                  fact("ns", "CurrentYearDuration_X", None)):
            self.assertEqual(H.dimension_siblings([self.f, g], self.f, TOL), [], g)

    def test_tolerance_is_a_closed_band(self):
        inside = fact("ns", "CurrentYearDuration_X", 100.0 + TOL)
        outside = fact("ns", "CurrentYearDuration_X", 100.0 + TOL + 1)
        self.assertEqual(len(H.dimension_siblings([self.f, inside], self.f, TOL)), 1)
        self.assertEqual(len(H.dimension_siblings([self.f, outside], self.f, TOL)), 0)


class PeriodRuleTest(unittest.TestCase):
    def setUp(self):
        self.f = fact("ns", "CurrentYearDuration", 100.0)

    def test_fires_on_a_same_value_period_sibling_also_inside_a_dimension(self):
        self.assertEqual(H.period_siblings([self.f, fact("ns", "Prior1YearDuration", 100.0)], self.f, TOL),
                         [fact("ns", "Prior1YearDuration", 100.0)])
        f = fact("ns", "CurrentYearDuration_Seg", 100.0)
        g = fact("ns", "Prior1YearDuration_Seg", 100.0)
        self.assertEqual(H.period_siblings([f, g], f, TOL), [g])

    def test_dimension_only_sibling_does_not_fire_for_p(self):
        g = fact("ns", "CurrentYearDuration_Seg", 100.0)
        self.assertEqual(H.period_siblings([self.f, g], self.f, TOL), [])
        # しかし (d) は拾う ― 2 つの規則は同じ兄弟を二重に数えない
        self.assertEqual(H.dimension_siblings([self.f, g], self.f, TOL), [g])

    def test_unit_only_or_other_element_does_not_fire(self):
        for g in (fact("ns", "Prior1YearDuration", 100.0, unit="USD"),
                  fact("other", "Prior1YearDuration", 100.0)):
            self.assertEqual(H.period_siblings([self.f, g], self.f, TOL), [], g)


class UnitRuleTest(unittest.TestCase):
    def test_classes(self):
        for u in (u"百万円", u"千円", u"億円", u"兆円", u"円"):
            self.assertEqual(H.claim_class(u), "JPY", u)
        for u in (u"%", u"％"):
            self.assertEqual(H.claim_class(u), "pure", u)
        for u in (None, u"株", u""):
            self.assertIsNone(H.claim_class(u), u)
        self.assertIsNone(H.fact_class(None))
        self.assertIsNone(H.fact_class(""))
        self.assertEqual(H.fact_class("JPYPerShares"), "JPYPerShares")

    def test_mismatch_and_not_judged(self):
        self.assertEqual(H.unit_mismatch(u"百万円", fact("n", "c", 1.0, "USD")), (True, "JPY", "USD"))
        self.assertEqual(H.unit_mismatch(u"％", fact("n", "c", 1.0, "pure"))[0], False)
        self.assertEqual(H.unit_mismatch(None, fact("n", "c", 1.0, "USD"))[0], False)
        self.assertEqual(H.unit_mismatch(u"百万円", fact("n", "c", 1.0, None))[0], False)


class ApplyHoldsTest(unittest.TestCase):
    def test_grounded_without_siblings_is_untouched(self):
        f = fact("ns", "CurrentYearDuration", 100.0)
        out = ok()
        new, fired = H.apply_holds(out, f, [f, fact("ns", "Prior1YearDuration", 100.0 + TOL + 1)], TOL, u"百万円")
        self.assertIs(new, out)
        self.assertEqual(fired, {"d": False, "P": False, "U": False})

    def test_non_grounded_states_are_never_moved(self):
        f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        facts = [f, fact("ns", "Prior1YearDuration", 100.0, unit="USD"),
                 fact("ns", "CurrentYearDuration_X", 100.0, unit="USD")]
        for st in ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNPROVABLE"):
            out = ok(state=st)
            new, fired = H.apply_holds(out, f, facts, TOL, u"百万円")
            self.assertEqual(new, out, st)
            self.assertEqual(fired, {"d": False, "P": False, "U": False}, st)

    def test_unresolved_pointer_is_untouched(self):
        out = ok()
        self.assertEqual(H.apply_holds(out, None, [], TOL, u"百万円"), (out, {"d": False, "P": False, "U": False}))

    def test_all_three_fire_and_reasons_concatenate_in_order(self):
        f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        facts = [f, fact("ns", "CurrentYearDuration_Seg", 100.0, unit="USD"),
                 fact("ns", "Prior1YearDuration", 100.0, unit="USD")]
        new, fired = H.apply_holds(ok(), f, facts, TOL, u"百万円")
        self.assertEqual(fired, {"d": True, "P": True, "U": True})
        self.assertEqual(new["state"], "UNPROVABLE")
        self.assertTrue(new["held"])
        self.assertEqual(new["reason"], "ambiguous_dimension:1;ambiguous_period:1;unit_class_mismatch:JPY/USD")
        self.assertEqual(new["hold_rules"], ("d", "P", "U"))

    def test_single_rules(self):
        f = fact("ns", "CurrentYearDuration", 100.0)
        new, fired = H.apply_holds(ok(), f, [f, fact("ns", "CurrentYearDuration_Seg", 100.0)], TOL, u"百万円")
        self.assertEqual((new["reason"], new["hold_rules"]), ("ambiguous_dimension:1", ("d",)))
        new, fired = H.apply_holds(ok(), f, [f, fact("ns", "Prior1YearDuration", 100.0)], TOL, u"百万円")
        self.assertEqual((new["reason"], new["hold_rules"]), ("ambiguous_period:1", ("P",)))
        g = fact("ns", "CurrentYearDuration", 100.0, unit="shares")
        new, fired = H.apply_holds(ok(), g, [g], TOL, u"百万円")
        self.assertEqual((new["reason"], new["hold_rules"]), ("unit_class_mismatch:JPY/shares", ("U",)))

    def test_pointers_and_inputs_are_never_changed(self):
        f = fact("ns", "CurrentYearDuration", 100.0, unit="USD")
        facts = [f, fact("ns", "Prior1YearDuration", 100.0, unit="USD")]
        out = ok()
        snap = (copy.deepcopy(out), copy.deepcopy(facts))
        new, _fired = H.apply_holds(out, f, facts, TOL, u"百万円")
        self.assertEqual(new["pointers"], out["pointers"])
        self.assertEqual((out, facts), snap)

    def test_checks_and_unchecked_are_pinned(self):
        self.assertEqual(H.CHECKS, (u"存在", u"値", u"同額の次元兄弟", u"同額の期間兄弟", u"単位の種類"))
        self.assertEqual(H.UNCHECKED, (u"重複", u"単位の倍率", u"期間(同額の兄弟が無いとき)",
                                       u"次元(同額の兄弟が無いとき)", u"要素の取り違え"))
        self.assertTrue(H.UNCHECKED, u"unchecked を空にしない(封 §1-1)")


class AxesTest(unittest.TestCase):
    """(d) の発火に**どの軸が違うか**を付ける。規則の判定そのものは軸を見ない。"""

    CTX = {"CurrentYearDuration": {"members": [], "axes": []},
           "CurrentYearDuration_SegA": {"members": ["x:SegA"], "axes": [["x:OperatingSegmentsAxis", "x:SegA"]]},
           "CurrentYearDuration_NonCons": {"members": ["x:NonConsolidatedMember"],
                                           "axes": [["x:ConsolidatedOrNonConsolidatedAxis", "x:NonConsolidatedMember"]]},
           "CurrentYearDuration_SegB": {"members": ["x:SegB"], "axes": [["x:OperatingSegmentsAxis", "x:SegB"]]}}

    def test_axes_of_and_differing_axes(self):
        f = fact("ns", "CurrentYearDuration", 100.0)
        sibs = [fact("ns", "CurrentYearDuration_SegA", 100.0), fact("ns", "CurrentYearDuration_NonCons", 100.0)]
        self.assertEqual(H.differing_axes(self.CTX, f, sibs),
                         ["x:ConsolidatedOrNonConsolidatedAxis", "x:OperatingSegmentsAxis"])
        # 同じ軸で枠の名だけ違う
        fa = fact("ns", "CurrentYearDuration_SegA", 100.0)
        self.assertEqual(H.differing_axes(self.CTX, fa, [fact("ns", "CurrentYearDuration_SegB", 100.0)]),
                         ["x:OperatingSegmentsAxis"])
        self.assertEqual(H.differing_axes(None, f, sibs), [])

    def test_hold_axes_is_recorded_on_d_and_empty_otherwise(self):
        f = fact("ns", "CurrentYearDuration", 100.0)
        new, _f = H.apply_holds(ok(), f, [f, fact("ns", "CurrentYearDuration_SegA", 100.0)], TOL, u"百万円", self.CTX)
        self.assertEqual(new["hold_axes"], ["x:OperatingSegmentsAxis"])
        new, _f = H.apply_holds(ok(), f, [f, fact("ns", "Prior1YearDuration", 100.0)], TOL, u"百万円", self.CTX)
        self.assertEqual(new["hold_axes"], [])


class AxesInInstanceTest(unittest.TestCase):
    """``load_instance`` が ``members`` と 1:1 で ``axes`` を保持する(.xbrl と iXBRL の両方)。"""

    XBRL = (u'<?xml version="1.0" encoding="UTF-8"?>'
            u'<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
            u'xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:jppfs_cor="http://example/jppfs">'
            u'<xbrli:context id="CurrentYearDuration"><xbrli:period><xbrli:startDate>2025-04-01</xbrli:startDate>'
            u'<xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>'
            u'<xbrli:context id="CurrentYearDuration_NonConsolidatedMember"><xbrli:period>'
            u'<xbrli:startDate>2025-04-01</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period>'
            u'<xbrli:scenario><xbrldi:explicitMember dimension="jppfs_cor:ConsolidatedOrNonConsolidatedAxis">'
            u'jppfs_cor:NonConsolidatedMember</xbrldi:explicitMember></xbrli:scenario></xbrli:context>'
            u'<jppfs_cor:NetSales contextRef="CurrentYearDuration" unitRef="JPY" decimals="-6">100000000</jppfs_cor:NetSales>'
            u'</xbrli:xbrl>')

    IXBRL = (u'<html><body><xbrli:context id="CurrentYearDuration"><xbrli:period><xbrli:startDate>2025-04-01'
             u'</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period></xbrli:context>'
             u'<xbrli:context id="CurrentYearDuration_SegAMember"><xbrli:period><xbrli:startDate>2025-04-01'
             u'</xbrli:startDate><xbrli:endDate>2026-03-31</xbrli:endDate></xbrli:period><xbrli:scenario>'
             u'<xbrldi:explicitMember dimension="jppfs_cor:OperatingSegmentsAxis">jppfs_cor:SegAMember'
             u'</xbrldi:explicitMember></xbrli:scenario></xbrli:context>'
             u'<ix:nonFraction contextRef="CurrentYearDuration" name="jppfs_cor:NetSales" unitRef="JPY" '
             u'decimals="-6" scale="6">100</ix:nonFraction></body></html>')

    @staticmethod
    def _zip(name, body):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("XBRL/PublicDoc/" + name, body.encode("utf-8"))
        return buf.getvalue()

    def test_xbrl_path_keeps_axes_one_to_one(self):
        inst = I.load_instance(self._zip("a.xbrl", self.XBRL))
        c = inst["contexts"]
        self.assertEqual(c["CurrentYearDuration"]["axes"], [])
        self.assertEqual(c["CurrentYearDuration"]["members"], [])
        self.assertEqual(c["CurrentYearDuration_NonConsolidatedMember"]["axes"],
                         [["jppfs_cor:ConsolidatedOrNonConsolidatedAxis", "jppfs_cor:NonConsolidatedMember"]])
        self.assertEqual(c["CurrentYearDuration_NonConsolidatedMember"]["members"], ["jppfs_cor:NonConsolidatedMember"])
        for cid, ctx in c.items():
            self.assertEqual(len(ctx["axes"]), len(ctx["members"]), cid)
            self.assertEqual([m for _a, m in ctx["axes"]], ctx["members"], cid)
        self.assertEqual(sorted(c["CurrentYearDuration"].keys()), ["axes", "end", "instant", "members", "start"])

    def test_ixbrl_path_keeps_axes_one_to_one(self):
        inst = I.load_instance(self._zip("a_ixbrl.htm", self.IXBRL))
        c = inst["contexts"]
        self.assertEqual(c["CurrentYearDuration_SegAMember"]["axes"],
                         [["jppfs_cor:OperatingSegmentsAxis", "jppfs_cor:SegAMember"]])
        self.assertEqual(c["CurrentYearDuration"]["axes"], [])
        for cid, ctx in c.items():
            self.assertEqual([m for _a, m in ctx["axes"]], ctx["members"], cid)
        self.assertEqual(inst["facts"][0]["value"], 100000000.0)


class EquivalenceWithMeasureRulesTest(unittest.TestCase):
    """写しが ``measure/`` の規則((d)・P・U)と**同じ答え**を出すことを合成の格子で確かめる。

    砂場(変異の試験)には ``measure/`` が無いので、その場合は飛ばす。
    """

    @classmethod
    def setUpClass(cls):
        p = os.path.join(_ROOT, "measure", "xbrl_period_unit_hold_rule_2026-10-19.py")
        if not os.path.exists(p):
            raise unittest.SkipTest("measure/ が無い(変異の砂場)")
        sp = importlib.util.spec_from_file_location("pu_rule_for_equiv", p)
        cls.R = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(cls.R)

    def test_grid(self):
        base = fact("ns", "CurrentYearDuration", 100.0)
        sibling_kinds = {
            "dim": fact("ns", "CurrentYearDuration_Seg", 100.0),
            "period": fact("ns", "Prior1YearDuration", 100.0),
            "dim_far": fact("ns", "CurrentYearDuration_Seg", 100.0 + TOL + 1),
            "period_usd": fact("ns", "Prior1YearDuration", 100.0, unit="USD"),
            "other": fact("other", "CurrentYearDuration_Seg", 100.0),
        }
        n = 0
        for state in ("GROUNDED", "VALUE_MISMATCH", "UNPROVABLE"):
            for unit_f in ("JPY", "USD", "pure"):
                for claim_unit in (u"百万円", u"％", None):
                    for k in range(0, len(sibling_kinds) + 1):
                        for combo in itertools.combinations(sorted(sibling_kinds), k):
                            f = dict(base, unit=unit_f)
                            facts = [f] + [dict(sibling_kinds[c], unit=(unit_f if c != "period_usd" else "USD"))
                                           for c in combo]
                            out = ok(state=state)
                            a, fa = H.apply_holds(out, f, facts, TOL, claim_unit)
                            b, fb = self.R.apply_all(out, f, facts, TOL, claim_unit)
                            self.assertEqual(fa, fb, (state, unit_f, claim_unit, combo))
                            self.assertEqual(a["state"], b["state"], (state, unit_f, claim_unit, combo))
                            self.assertEqual(a.get("reason"), b.get("reason"), (state, unit_f, claim_unit, combo))
                            n += 1
        self.assertGreater(n, 800)


if __name__ == "__main__":
    unittest.main()
