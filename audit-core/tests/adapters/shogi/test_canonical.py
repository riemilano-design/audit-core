# -*- coding: utf-8 -*-
"""Unit tests for ``canonical.canonical_json``. Expected strings are the
real ``canonicalJson`` (``scripts/playtest/lib/observationPacket.ts``)'s
own output, obtained by calling it with ``npx tsx`` during this STEP's
implementation (recorded in the implementer's report; the probe script
itself is scratch material, not checked in). No ``node``/``npx`` call
happens inside this test -- the expected strings are written here as
literals, per the task instruction ("試験の中で node を呼ばない")."""

import unittest

from adapters.shogi import canonical as J


class CanonicalJsonNumberTest(unittest.TestCase):
    def test_integers_and_zero(self):
        self.assertEqual(J.canonical_json(0), "0")
        self.assertEqual(J.canonical_json(-0), "0")
        self.assertEqual(J.canonical_json(-0.0), "0")
        self.assertEqual(J.canonical_json(1), "1")
        self.assertEqual(J.canonical_json(-1), "-1")
        self.assertEqual(J.canonical_json(100), "100")
        self.assertEqual(J.canonical_json(1000000), "1000000")
        self.assertEqual(J.canonical_json(-1000000), "-1000000")
        self.assertEqual(J.canonical_json(300), "300")
        self.assertEqual(J.canonical_json(-300), "-300")

    def test_decimals(self):
        self.assertEqual(J.canonical_json(1.5), "1.5")
        self.assertEqual(J.canonical_json(-1.5), "-1.5")
        self.assertEqual(J.canonical_json(0.001), "0.001")
        self.assertEqual(J.canonical_json(0.0001), "0.0001")
        self.assertEqual(J.canonical_json(0.00001), "0.00001")
        self.assertEqual(J.canonical_json(0.000001), "0.000001")
        self.assertEqual(J.canonical_json(5.8), "5.8")
        self.assertEqual(J.canonical_json(-5.8), "-5.8")
        self.assertEqual(J.canonical_json(0.5), "0.5")
        self.assertEqual(J.canonical_json(12.34), "12.34")
        self.assertEqual(J.canonical_json(53.333333333333336), "53.333333333333336")

    def test_exponential_notation_thresholds(self):
        # JS crosses to exponential below 1e-6 and at/above 1e21.
        self.assertEqual(J.canonical_json(0.0000001), "1e-7")
        self.assertEqual(J.canonical_json(1e20), "100000000000000000000")
        self.assertEqual(J.canonical_json(1e21), "1e+21")
        self.assertEqual(J.canonical_json(1e22), "1e+22")

    def test_large_integers_within_float64_precision(self):
        self.assertEqual(J.canonical_json(123456789012345680000), "123456789012345680000")
        self.assertEqual(J.canonical_json(9999999999999998), "9999999999999998")
        self.assertEqual(J.canonical_json(2 ** 53), "9007199254740992")

    def test_booleans_are_not_numbers(self):
        self.assertEqual(J.canonical_json(True), "true")
        self.assertEqual(J.canonical_json(False), "false")

    def test_nan_and_infinite_map_to_null(self):
        self.assertEqual(J.canonical_json(float("nan")), "null")
        self.assertEqual(J.canonical_json(float("inf")), "null")
        self.assertEqual(J.canonical_json(float("-inf")), "null")


class CanonicalJsonStringTest(unittest.TestCase):
    def test_plain_and_non_ascii(self):
        self.assertEqual(J.canonical_json("abc"), '"abc"')
        self.assertEqual(J.canonical_json("日本語のテスト"), '"日本語のテスト"')

    def test_escapes(self):
        self.assertEqual(J.canonical_json('quote"here'), '"quote\\"here"')
        self.assertEqual(J.canonical_json("back\\slash"), '"back\\\\slash"')
        self.assertEqual(J.canonical_json("ctrlchar"), '"ctrl\\u0001char"')
        self.assertEqual(J.canonical_json("newline\nhere"), '"newline\\nhere"')


class CanonicalJsonStructureTest(unittest.TestCase):
    def test_null_and_empty(self):
        self.assertEqual(J.canonical_json(None), "null")
        self.assertEqual(J.canonical_json([]), "[]")
        self.assertEqual(J.canonical_json({}), "{}")

    def test_array_order_preserved(self):
        self.assertEqual(J.canonical_json([1, "a", None, True, False]), '[1,"a",null,true,false]')

    def test_object_keys_sorted(self):
        self.assertEqual(J.canonical_json({"z": 1, "a": 2, "m": [1, 2]}), '{"a":2,"m":[1,2],"z":1}')

    def test_nested(self):
        self.assertEqual(
            J.canonical_json({"nested": {"z": 1, "y": [1, {"d": 2, "c": 1}]}}),
            '{"nested":{"y":[1,{"c":1,"d":2}],"z":1}}',
        )


if __name__ == "__main__":
    unittest.main()
