# -*- coding: utf-8 -*-
"""Direct unit tests for ``comparators.canonical_json_equals`` (not
through ``verify_all``), using hand-built ``Resolved``/``Claim``/
``Contract`` objects."""

import unittest

import audit_core as core

from adapters.shogi import comparators as C


def _claim(value):
    return core.Claim(
        id="x", form=core.Form.DIRECT_VALUE, subject="facts.x[0].y",
        value=None, unit=None, modifiers=core.Modifiers(), provenance={},
    )


def _contract(expected):
    return core.Contract(comparator="canonical_json_equals", params={"expected": expected})


def _resolved(raw):
    return core.Resolved(value=None, unit=None, precision=None, meta={"raw": raw})


class CanonicalJsonEqualsTest(unittest.TestCase):
    def test_matching_numbers(self):
        comparison = C.canonical_json_equals((_resolved(20),), _claim(20), _contract(20))
        self.assertTrue(comparison.match)
        self.assertEqual(comparison.recomputed, 20.0)
        self.assertEqual(comparison.depth, "value_match")

    def test_mismatched_numbers(self):
        comparison = C.canonical_json_equals((_resolved(7),), _claim(99), _contract(99))
        self.assertFalse(comparison.match)
        self.assertEqual(comparison.recomputed, 7.0)
        self.assertEqual(comparison.detail["expected_canonical"], "99")
        self.assertEqual(comparison.detail["actual_canonical"], "7")

    def test_matching_strings(self):
        comparison = C.canonical_json_equals((_resolved("四間飛車"),), _claim("四間飛車"), _contract("四間飛車"))
        self.assertTrue(comparison.match)
        self.assertIsNone(comparison.recomputed)  # not a number

    def test_bool_is_not_confused_with_number_one(self):
        # canonicalJson(1) = "1" / canonicalJson(true) = "true" -- a bare
        # Python ``1 == True`` would wrongly match (S-R1's target).
        comparison = C.canonical_json_equals((_resolved(True),), _claim(1), _contract(1))
        self.assertFalse(comparison.match)
        self.assertEqual(comparison.detail["expected_canonical"], "1")
        self.assertEqual(comparison.detail["actual_canonical"], "true")

    def test_nested_structure_equality_is_order_sensitive_for_arrays(self):
        comparison = C.canonical_json_equals(
            (_resolved([1, 2, 3]),), _claim(None), _contract([1, 2, 3])
        )
        self.assertTrue(comparison.match)
        comparison2 = C.canonical_json_equals(
            (_resolved([3, 2, 1]),), _claim(None), _contract([1, 2, 3])
        )
        self.assertFalse(comparison2.match)


if __name__ == "__main__":
    unittest.main()
