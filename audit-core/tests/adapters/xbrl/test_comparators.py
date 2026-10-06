# -*- coding: utf-8 -*-
"""C-1d §G (and C-1f): unit tests for the six comparators in
``adapters/xbrl/comparators.py``. Each gets a match case, a mismatch
case, and (where the spec calls one out) a boundary case; answers are
chosen so they do not coincide with any nearby nor previously-used number
in this suite.

C-1f (2026-10-06) fixed two of the "原本の癖" this file originally
pinned: pure100/ratio100 now compare to the *signed* ``claim.value``
(not ``abs(claim.value)``), and sign-direction now treats a difference
of exactly 0 as neither an increase nor a decrease. Only claims with a
*negative* ``claim.value`` are affected by the first fix (a positive
claim.value gives the same result either way), so the two tests that
pinned the old behaviour with a negative claim --
``test_compares_against_absolute_claim_value`` in both
``EqualsWithinPure100Test`` and ``Ratio100Test`` -- and the one test
that pinned the old sign-zero behaviour --
``test_zero_difference_counts_as_decrease`` in
``BuiltinSignDirectionTest`` -- are replaced here with tests of the new
behaviour (renamed to match; this is 3 existing tests, not the 1 the
C-1f prediction §2/§3 anticipated -- see the implementation report for
C-1f, which records this as a discovered gap in that prediction, not a
silent correction of it).
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

    def test_negative_claim_value_mismatches_positive_fact(self):
        # C-1f fix to 原本の癖 a: a negative claim.value ("△5.8%") no
        # longer matches a positive fact via abs() -- it is compared
        # signed, so this now mismatches.
        evidence = (_resolved(0.058),)
        claim = _claim(value=-5.8, unit="%")
        contract = _contract("equals_within(pure*100)", tolerance=0.15, pure_threshold=1.5)
        result = C.equals_within_pure100(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 5.8)

    def test_positive_claim_value_matches_same_fact(self):
        # Same fact/magnitude as above with a positive claim.value: the
        # signed comparison matches directly.
        evidence = (_resolved(0.058),)
        claim = _claim(value=5.8, unit="%")
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

    def test_negative_claim_value_mismatches_positive_ratio(self):
        # C-1f fix to 原本の癖 a: a negative claim.value no longer
        # matches a positive ratio via abs() -- compared signed, this
        # now mismatches.
        evidence = (_resolved(94.0), _resolved(100.0))
        claim = _claim(value=-94.0, unit="%")
        contract = _contract("ratio*100", tolerance=0.15)
        result = C.ratio100(evidence, claim, contract)
        self.assertFalse(result.match)


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


class EqualsWithinFlowSignTest(unittest.TestCase):
    """Core 接続 C-1g §1-2(profile P6 のみ): ``equals_within`` の新しい分岐
    (``flow_convention``/``claim_direction`` が params にあるとき)。P1/P5F は
    これらの鍵を一度も渡さないので、既存の ``EqualsWithinLadderTest`` の
    挙動(abs を落とさない梯子)に触れない。
    """

    def test_sign_and_magnitude_both_match(self):
        # fact は -802,686,000(DecreaseIncreaseIn 系、規約 -1 = 減少)。
        # claim は「増加額 802,686,000」(claim_direction=+1)。
        # sign(fact)=-1, -1 * -1 = +1 == +1 の claim_direction と一致する。
        evidence = (_resolved(-802686000.0),)
        claim = _claim(value=802686000.0, unit="円")
        contract = _contract(
            "equals_within", unit_scale=1.0, claim_scale=1000.0,
            flow_convention=-1, claim_direction=1,
        )
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "round")

    def test_sign_mismatch_with_matching_magnitude(self):
        # 同じ magnitude だが claim_direction が逆(減少額のつもり)。
        evidence = (_resolved(-802686000.0),)
        claim = _claim(value=802686000.0, unit="円")
        contract = _contract(
            "equals_within", unit_scale=1.0, claim_scale=1000.0,
            flow_convention=-1, claim_direction=-1,
        )
        result = C.equals_within(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["normalization"], "round")

    def test_normalization_drops_abs_prefix(self):
        # 梯子は abs を落とした "round"/"truncate" のどちらかで、
        # "abs+round"/"abs+truncate" にはならない(§1-2)。
        evidence = (_resolved(-802686700.0),)
        claim = _claim(value=802686000.0, unit="円")
        contract = _contract(
            "equals_within", unit_scale=1.0, claim_scale=1000.0,
            flow_convention=-1, claim_direction=1,
        )
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "truncate")

    def test_fact_value_zero_sign_matches_no_direction(self):
        evidence = (_resolved(0.0),)
        claim = _claim(value=0.0, unit="円")
        contract = _contract(
            "equals_within", unit_scale=1.0, claim_scale=1000.0,
            flow_convention=1, claim_direction=1,
        )
        result = C.equals_within(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["fact_sign"], 0)

    def test_without_flow_params_behaves_as_before(self):
        # flow_convention/claim_direction が無ければ従来どおり abs 付きの
        # 梯子(回帰確認、既存の EqualsWithinLadderTest と同じ入力)。
        evidence = (_resolved(-38064274000.0),)
        claim = _claim(value=38064.0, unit="百万円")
        contract = _contract("equals_within", unit_scale=1e6, claim_scale=1e6)
        result = C.equals_within(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.detail["normalization"], "abs+round")


class BuiltinFlowSignDirectionTest(unittest.TestCase):
    """Core 接続 C-1g §1-2: ``builtin:flow_sign(cur)==direction``。evidence
    は当期の fact 1 件だけ。
    """

    def test_increase_matches_positive_direction(self):
        evidence = (_resolved(786000000.0),)
        claim = _claim()
        contract = _contract("builtin:flow_sign(cur)==direction", direction=1, flow_convention=1)
        result = C.builtin_flow_sign_direction(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 786000000.0)

    def test_decrease_convention_with_negative_fact_matches_increase_direction(self):
        # DecreaseIncreaseIn 系(規約 -1)の fact が負 -> 実質「増加」。
        evidence = (_resolved(-802686000.0),)
        claim = _claim()
        contract = _contract("builtin:flow_sign(cur)==direction", direction=1, flow_convention=-1)
        result = C.builtin_flow_sign_direction(evidence, claim, contract)
        self.assertTrue(result.match)

    def test_mismatch(self):
        evidence = (_resolved(61270000.0),)
        claim = _claim()
        contract = _contract("builtin:flow_sign(cur)==direction", direction=1, flow_convention=-1)
        result = C.builtin_flow_sign_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["actual"], -1)

    def test_zero_value_matches_no_direction(self):
        evidence = (_resolved(0.0),)
        claim = _claim()
        contract = _contract("builtin:flow_sign(cur)==direction", direction=1, flow_convention=1)
        result = C.builtin_flow_sign_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["actual"], 0)
        contract_neg = _contract("builtin:flow_sign(cur)==direction", direction=-1, flow_convention=1)
        self.assertFalse(C.builtin_flow_sign_direction(evidence, claim, contract_neg).match)


class DiffAbPure100Test(unittest.TestCase):
    """Core 接続 C-1g §1-3: ``diff(a-b)(pure*100)``(ポイント差)。"""

    def test_match_positive_point_increase(self):
        evidence = (_resolved(0.525), _resolved(0.495))
        claim = _claim(value=2.9, unit="ポイント")
        contract = _contract("diff(a-b)(pure*100)", tolerance=0.15)
        result = C.diff_ab_pure100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 3.0)

    def test_match_negative_point_decrease(self):
        evidence = (_resolved(0.061), _resolved(0.073))
        claim = _claim(value=-1.2, unit="ポイント")
        contract = _contract("diff(a-b)(pure*100)", tolerance=0.15)
        result = C.diff_ab_pure100(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, -1.2)

    def test_mismatch(self):
        evidence = (_resolved(0.10), _resolved(0.05))
        claim = _claim(value=1.0, unit="ポイント")
        contract = _contract("diff(a-b)(pure*100)", tolerance=0.15)
        result = C.diff_ab_pure100(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 5.0)

    def test_tolerance_boundary(self):
        evidence = (_resolved(0.10), _resolved(0.0985))
        claim = _claim(value=0.0, unit="ポイント")
        contract = _contract("diff(a-b)(pure*100)", tolerance=0.15)
        result = C.diff_ab_pure100(evidence, claim, contract)
        self.assertTrue(result.match)

    def test_mismatch_just_outside_015_tolerance(self):
        # diff == 1.0 point: mismatches the real tolerance (0.15) but would
        # wrongly match a hardcoded 1.5 (mutations.json: G-R3).
        evidence = (_resolved(0.50), _resolved(0.49))
        claim = _claim(value=0.0, unit="ポイント")
        contract = _contract("diff(a-b)(pure*100)", tolerance=0.15)
        result = C.diff_ab_pure100(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 1.0)


class BuiltinSignAbsDiffDirectionTest(unittest.TestCase):
    """Core 接続 C-1h §1-1: ``builtin:sign(|cur|-|prior|)==direction``
    (CF の「支出」系項目。大きさ(絶対値)の増減を見る)。
    """

    def test_magnitude_decrease_matches_decrease_direction(self):
        # |-143,940| - |-219,930| = -75,990 -> 大きさは減った。
        evidence = (_resolved(-143940.0), _resolved(-219930.0))
        claim = _claim()
        contract = _contract("builtin:sign(|cur|-|prior|)==direction", direction=-1)
        result = C.builtin_sign_abs_diff_direction(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, -75990.0)

    def test_magnitude_increase_mismatches_decrease_direction(self):
        # |-86,046| - |-66,547| = +19,499 -> 大きさは増えた(「減少」とは
        # 一致しない)。
        evidence = (_resolved(-86046.0), _resolved(-66547.0))
        claim = _claim()
        contract = _contract("builtin:sign(|cur|-|prior|)==direction", direction=-1)
        result = C.builtin_sign_abs_diff_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.recomputed, 19499.0)
        self.assertEqual(result.detail["actual"], 1)

    def test_zero_magnitude_difference_matches_no_direction(self):
        evidence = (_resolved(-500.0), _resolved(500.0))
        claim = _claim()
        contract_dec = _contract("builtin:sign(|cur|-|prior|)==direction", direction=-1)
        contract_inc = _contract("builtin:sign(|cur|-|prior|)==direction", direction=1)
        self.assertFalse(C.builtin_sign_abs_diff_direction(evidence, claim, contract_dec).match)
        self.assertFalse(C.builtin_sign_abs_diff_direction(evidence, claim, contract_inc).match)

    def test_positive_fact_values_also_use_magnitude(self):
        # 正の値(通常の「支出」は負で記録されるが、符号そのものではなく
        # 大きさだけを見ることを確かめる)。
        evidence = (_resolved(300.0), _resolved(100.0))
        claim = _claim()
        contract = _contract("builtin:sign(|cur|-|prior|)==direction", direction=1)
        result = C.builtin_sign_abs_diff_direction(evidence, claim, contract)
        self.assertTrue(result.match)
        self.assertEqual(result.recomputed, 200.0)


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

    def test_zero_difference_mismatches_positive_direction(self):
        # C-1f fix to 原本の癖 b: diff == 0 -> actual = 0, which matches
        # neither direction (previously actual = -1, "a decrease").
        evidence = (_resolved(500.0), _resolved(500.0))
        claim = _claim()
        contract = _contract("builtin:sign(cur-prior)==direction", direction=1)
        result = C.builtin_sign_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["actual"], 0)

    def test_zero_difference_mismatches_negative_direction(self):
        # Same fix, the other direction: diff == 0 also mismatches
        # direction=-1 now (previously it matched, since -1 == -1).
        evidence = (_resolved(777.0), _resolved(777.0))
        claim = _claim()
        contract = _contract("builtin:sign(cur-prior)==direction", direction=-1)
        result = C.builtin_sign_direction(evidence, claim, contract)
        self.assertFalse(result.match)
        self.assertEqual(result.detail["actual"], 0)


if __name__ == "__main__":
    unittest.main()
