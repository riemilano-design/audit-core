# -*- coding: utf-8 -*-
"""Core end-to-end test (C-2 plan §5 計器 7's shape, run on synthetic
material instead of the real c5 Golden Master, per this STEP's
instruction not to read ``scripts/playtest/out/``): one synthetic packet
+ one synthetic seat envelope run all the way through
``audit_core.verify_all``, producing one GROUNDED, one VALUE_MISMATCH,
one POINTER_NOT_FOUND and one UNVERIFIABLE result."""

import unittest

import audit_core as core

from adapters.shogi import recipes as R
from adapters.shogi import registry_setup as RS
from adapters.shogi import resolve as RV
from tests.adapters.shogi import _material as M


class EndToEndTest(unittest.TestCase):
    def setUp(self):
        self.packet = M.synthetic_packet()
        envelope = M.synthetic_seat_envelope()
        self.recipes = R.build_recipes([("run001", "seat_gpt.json", envelope)], self.packet)
        self.resolver = RV.make_resolver(self.packet)
        self.registry = RS.register_all(core.Registry.default())
        self.results = core.verify_all(self.recipes, self.resolver, self.registry)
        self.by_id = dict(zip((rc.claim.id for rc in self.recipes), self.results))

    def test_one_of_each_state(self):
        states = [r.state for r in self.results]
        self.assertEqual(states.count(core.State.GROUNDED), 1)
        self.assertEqual(states.count(core.State.VALUE_MISMATCH), 1)
        self.assertEqual(states.count(core.State.POINTER_NOT_FOUND), 1)
        self.assertEqual(states.count(core.State.UNVERIFIABLE), 1)
        self.assertEqual(len(self.results), 4)

    def test_grounded_result(self):
        result = self.by_id["run001/seat_gpt.json#H-z1-time-001/observations[0]"]
        self.assertEqual(result.state, core.State.GROUNDED)
        self.assertEqual(result.recomputed, 20.0)
        self.assertEqual(result.comparator, "canonical_json_equals")
        self.assertEqual(result.pointers, ("packet:aggregates.groups.core.games.value",))

    def test_value_mismatch_result(self):
        result = self.by_id["run001/seat_gpt.json#H-z1-time-001/observations[1]"]
        self.assertEqual(result.state, core.State.VALUE_MISMATCH)
        self.assertEqual(result.recomputed, 7.0)  # the packet's actual value
        self.assertEqual(
            result.provenance["comparison"],
            {"expected_canonical": "99", "actual_canonical": "7"},
        )

    def test_pointer_not_found_result(self):
        result = self.by_id["run001/seat_gpt.json#H-z1-time-001/observations[2]"]
        self.assertEqual(result.state, core.State.POINTER_NOT_FOUND)
        self.assertEqual(result.reason, RV.NO_ROW)

    def test_unverifiable_result(self):
        result = self.by_id["run001/seat_gpt.json#H-z1-time-001/counterEvidence.items[0].observations[0]"]
        self.assertEqual(result.state, core.State.UNVERIFIABLE)
        self.assertEqual(result.reason, R.NO_PACKET_REF_REASON)


if __name__ == "__main__":
    unittest.main()
