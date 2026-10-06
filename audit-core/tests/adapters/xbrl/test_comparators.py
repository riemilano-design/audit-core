# -*- coding: utf-8 -*-
"""C-1d §G: unit tests for the six comparators in
``adapters/xbrl/comparators.py``. Each gets a match case, a mismatch
case, and (where the spec calls one out) a boundary case; answers are
chosen so they do not coincide with any nearby nor previously-used number
in this suite.
"""

import unittest

import audit_core as core

from adapters.xbrl import comparators as C


def _resolved(value, unit="JPY", precision=None, **meta):
    return core.Resolved(value=value, unit=unit, precision=precision, meta=meta)


def _claim(value=None, unit=None):
    return core.Claim(
        id="X", form=core.Form.DIRECT_VALUE, subject="s", value=value, unit=unit,
        modifiers=core.Modifiers(), provenance={},
    )


def _contract(comparator, **params):
    return core.Contract(comparator=comparator, params=params)


class EqualsWithinLadderTest(unittest.TestCase):
    def test_exact_round_match(self):
        evidence = (_resolved(38064274000.0),)
        claim = _claim(value=38064.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 38064274000.0)
        self.assertEqual(result.detail["normalization"], "round")

    def test_mismatch(self):
        evidence = (_resolved(5000000.0),)
        claim = _claim(value=1.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertIsNone(result.detail["normalization"])

    def test_round_boundary_exactly_half_unit(self):
        # unit=1e6, |fv - target| == 5e5 == unit/2 -> round (<=, not <).
        evidence = (_resolved(1500000.0),)
        claim = _claim(value=1.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "round")

    def test_truncate_just_inside_unit(self):
        # 0 <= fv - target < unit, outside the round band.
        evidence = (_resolved(1700001.0),)
        claim = _claim(value=1.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "truncate")

    def test_abs_round_on_sign_mismatch(self):
        evidence = (_resolved(-38064274000.0),)
        claim = _claim(value=38064.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "abs+round")

    def test_abs_tolerance_branch_match(self):
        evidence = (_resolved(412.0, unit="pure"),)
        claim = _claim(value=412.0, unit="名")
        contract = _contract("equals_within", abs_tolerance=0.5)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 412.0)
        self.assertNotIn("normalization", result.detail)

    def test_abs_tolerance_branch_mismatch(self):
        evidence = (_resolved(400.0, unit="pure"),)
        claim = _claim(value=412.0, unit="名")
        contract = _contract("equals_within", abs_tolerance=0.5)
        result = C.equals_within(evidence, claim, contract)
        self.assertFalse(result.match)


class EqualsWithinPure100Test(unittest.TestCase):
    def test_scaled_match(self):
        evidence = (_resolved(0.102),)
        claim = _claim(value=10.2, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 10.2)

    def test_mismatch(self):
        evidence = (_resolved(0.058),)
        claim = _claim(value=10.0, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 5.8)

    def test_pure_threshold_boundary_not_rescaled(self):
        # |fv| == pure_threshold exactly -> rescaled branch (<=).
        evidence = (_resolved(1.5),)
        claim = _claim(value=150.0, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 150.0)

    def test_above_pure_threshold_left_as_is(self):
        # |fv| > pure_threshold -> not multiplied by 100 (原本の癖 a-adjacent).
        evidence = (_resolved(61.7),)
        claim = _claim(value=61.7, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 61.7)

    def test_compares_against_absolute_claim_value(self):
        # 原本の癖 a: a negative claim.value is compared via abs().
        evidence = (_resolved(0.102),)
        claim = _claim(value=-10.2, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertTrue(result.match)


class Ratio100Test(unittest.TestCase):
    def test_match(self):
        evidence = (_resolved(102940000.0), _resolved(100000000.0))
        claim = _claim(value=102.9, unit="%")
        contract = _contract("ratio*100", tolerance=0.15)
        result = C.ratio100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 102.94)

    def test_mismatch(self):
        evidence = (_resolved(200.0), _resolved(100.0))
        claim = _claim(value=106.0, unit="%")
        contract = _contract("ratio*100", tolerance=0.15)
        result = C.ratio100(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 200.0)

    def test_tolerance_boundary_just_inside_and_outside(self):
        # Avoid asserting exactly at |diff| == 0.15 (0.15 is not exact in
        # binary float, so "just inside" / "just outside" bracket it
        # instead of landing on it).
        evidence_inside = (_resolved(1001.49), _resolved(1000.0))
        claim = _claim(value=100.0, unit="%")
        contract = _contract("ratio*100", tolerance=0.15)
        self.assertTrue(C.ratio100(evidence_inside, claim, contract).match)

        evidence_outside = (_resolved(1001.52), _resolved(1000.0))
        self.assertFalse(C.ratio100(evidence_outside, claim, contract).match)

    def test_compares_against_absolute_claim_value(self):
        evidence = (_resolved(94.0), _resolved(100.0))
        claim = _claim(value=-94.0, unit="%")
        contract = _contract("ratio*100", tolerance=0.15)
        result = C.ratio100(evidence, claim, contract)
        self.assertTrue(result.match)


class PctChangeTest(unittest.TestCase):
    def test_match(self):
        evidence = (_resolved(38064274000.0), _resolved(36990000000.0))
        claim = _claim(value=2.9, unit="%")
        contract = _contract("pct_change(cur,prior)", tolerance=0.15)
        result = C.pct_change(evidence, claim, contract)
        self.assertTrue(result.match)

    def test_mismatch(self):
        evidence = (_resolved(110.0), _resolved(100.0))
        claim = _claim(value=5.0, unit="%")
        contract = _contract("pct_change(cur,prior)", tolerance=0.15)
        result = C.pct_change(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 10.0)

    def test_signed_claim_value_not_absolute(self):
        # 原本の癖: unlike ratio100/pure100, pct_change compares to the
        # *signed* claim.value directly.
        evidence = (_resolved(90.0), _resolved(100.0))
        claim = _claim(value=-10.0, unit="%")
        contract = _contract("pct_change(cur,prior)", tolerance=0.15)
        result = C.pct_change(evidence, claim, contract)
        self.assertTrue(result.match)
        claim_wrong_sign = _claim(value=10.0, unit="%")
        result_wrong_sign = C.pct_change(evidence, claim_wrong_sign, contract)
        self.assertFalse(result_wrong_sign.match)


class DiffAbEqualsWithinTest(unittest.TestCase):
    def test_match(self):
        evidence = (_resolved(5283746000.0), _resolved(3002000000.0))
        claim = _claim(value=2282.0, unit="百万円")
        contract = _contract("diff(a-b) equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.diff_ab_equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 2281746000.0)
        self.assertEqual(result.detail["normalization"], "round")

    def test_mismatch(self):
        evidence = (_resolved(5000000.0), _resolved(1000000.0))
        claim = _claim(value=1.0, unit="百万円")
        contract = _contract("diff(a-b) equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.diff_ab_equals_within(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 4000000.0)


class BuiltinSignDirectionTest(unittest.TestCase):
    def test_increase_matches_positive_direction(self):
        evidence = (_resolved(1200.0), _resolved(1000.0))
        claim = _claim()
        contract = _contract("builtin:sign(cur-prior)==direction", direction=1)
        result = C.builtin_sign_direction(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 200.0)

    def test_decrease_mismatches_positive_direction(self):
        evidence = (_resolved(800.0), _resolved(1000.0))
        claim = _claim()
        contract = _contract("builtin:sign(cur-prior)==direction", direction=1)
        result = C.builtin_sign_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, -200.0)

    def test_zero_difference_counts_as_decrease(self):
        # 原本の癖 b: diff == 0 -> actual = -1 (strict > 0, not >= 0).
        evidence = (_resolved(1000.0), _resolved(1000.0))
        claim = _claim()
        contract_pos = _contract("builtin:sign(cur-prior)==direction", direction=1)
        contract_neg = _contract("builtin:sign(cur-prior)==direction", direction=-1)
        result_pos = C.builtin_sign_direction(evidence, claim, contract_pos)
        result_neg = C.builtin_sign_direction(evidence, claim, contract_neg)
        self.assertFalse(result_pos.match)
        self.assertTrue(result_neg.match)
        self.assertEqual(result_pos.detail["actual"], -1)


if __name__ == "__main__":
    unittest.main()
