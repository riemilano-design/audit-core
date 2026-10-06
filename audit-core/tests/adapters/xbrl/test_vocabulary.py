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


if __name__ == "__main__":
    unittest.main()
