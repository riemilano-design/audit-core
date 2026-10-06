# -*- coding: utf-8 -*-
"""Unit tests for ``resolve.resolve_packet_path`` (the 5 failure kinds and
the success path) and ``resolve.make_resolver``."""

import unittest

from adapters.shogi import resolve as RV
from tests.adapters.shogi import _material as M


class ResolvePacketPathSuccessTest(unittest.TestCase):
    def setUp(self):
        self.packet = M.synthetic_packet()

    def test_aggregate_value(self):
        ok, value, reason = RV.resolve_packet_path(self.packet, "aggregates.groups.core.games.value")
        self.assertTrue(ok)
        self.assertEqual(value, 20)
        self.assertIsNone(reason)

    def test_aggregate_numerator_denominator(self):
        ok, value, _reason = RV.resolve_packet_path(self.packet, "aggregates.side_match.attack.numerator")
        self.assertTrue(ok)
        self.assertEqual(value, 7)
        ok, value, _reason = RV.resolve_packet_path(self.packet, "aggregates.side_match.attack.denominator")
        self.assertTrue(ok)
        self.assertEqual(value, 20)

    def test_facts_array_index_field(self):
        ok, value, _reason = RV.resolve_packet_path(self.packet, "facts.moves[1].usi")
        self.assertTrue(ok)
        self.assertEqual(value, "3c3d")

    def test_facts_recognition_rows(self):
        ok, value, _reason = RV.resolve_packet_path(self.packet, "facts.recognition.rows[0].selfSignature")
        self.assertTrue(ok)
        self.assertEqual(value, "ibisha")


class ResolvePacketPathFailureTest(unittest.TestCase):
    def setUp(self):
        self.packet = M.synthetic_packet()

    def test_packet_absent_is_missing_key(self):
        ok, kind, reason = RV.resolve_packet_path(None, "aggregates.groups.core.games.value")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.MISSING_KEY)
        self.assertEqual(reason, "packet が無い")

    def test_bad_grammar_is_grammar(self):
        ok, kind, reason = RV.resolve_packet_path(self.packet, "aggregates.groups.core.games")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.GRAMMAR)
        self.assertIn("文法", reason)

    def test_unknown_aggregate_row_is_no_row(self):
        ok, kind, reason = RV.resolve_packet_path(self.packet, "aggregates.no_such.value")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.NO_ROW)
        self.assertIn("行が無い", reason)

    def test_aggregates_array_absent_is_no_row(self):
        ok, kind, _reason = RV.resolve_packet_path({"facts": {}}, "aggregates.no_such.value")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.NO_ROW)

    def test_wrong_fraction_field_is_no_field(self):
        # side_match.attack の行は numerator/denominator だけ(value は無い)。
        ok, kind, reason = RV.resolve_packet_path(self.packet, "aggregates.side_match.attack.value")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.NO_FIELD)
        self.assertIn("取り違え", reason)

    def test_index_out_of_range(self):
        ok, kind, reason = RV.resolve_packet_path(self.packet, "facts.moves[99].usi")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.INDEX_OUT_OF_RANGE)
        self.assertIn("列の外", reason)

    def test_missing_object_key(self):
        ok, kind, reason = RV.resolve_packet_path(self.packet, "facts.moves[0].noSuchField")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.MISSING_KEY)
        self.assertIn("packet に無い", reason)

    def test_stepping_into_non_array_with_index_is_missing_key(self):
        packet = {"facts": {"moves": {"usi": "x"}}}
        ok, kind, reason = RV.resolve_packet_path(packet, "facts.moves[0].usi")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.MISSING_KEY)
        self.assertIn("列でない", reason)

    def test_stepping_into_scalar_is_missing_key(self):
        packet = {"facts": {"moves": [1, 2]}}
        ok, kind, reason = RV.resolve_packet_path(packet, "facts.moves[0].usi")
        self.assertFalse(ok)
        self.assertEqual(kind, RV.MISSING_KEY)
        self.assertIn("引けない", reason)


class MakeResolverTest(unittest.TestCase):
    def setUp(self):
        self.packet = M.synthetic_packet()
        self.resolver = RV.make_resolver(self.packet)

    def test_resolves_numeric_value(self):
        import audit_core as core

        resolved = self.resolver(core.Pointer("packet", "aggregates.groups.core.games.value"))
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.value, 20.0)
        self.assertEqual(resolved.meta["raw"], 20)

    def test_resolves_string_value_with_none_float(self):
        import audit_core as core

        resolved = self.resolver(core.Pointer("packet", "facts.moves[1].usi"))
        self.assertIsNotNone(resolved)
        self.assertIsNone(resolved.value)
        self.assertEqual(resolved.meta["raw"], "3c3d")

    def test_unresolvable_pointer_is_none(self):
        import audit_core as core

        resolved = self.resolver(core.Pointer("packet", "aggregates.no_such.value"))
        self.assertIsNone(resolved)


if __name__ == "__main__":
    unittest.main()
