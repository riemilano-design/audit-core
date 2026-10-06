# -*- coding: utf-8 -*-
"""Unit tests for ``recipes.build_recipes``: id rule, ``form``,
``value``/``None``, bound Contract vs. ``not_found_reason``, and the
``counterEvidence`` -> always-``UNVERIFIABLE`` rule."""

import unittest

import audit_core as core

from adapters.shogi import recipes as R
from adapters.shogi import resolve as RV
from tests.adapters.shogi import _material as M


class BuildRecipesTest(unittest.TestCase):
    def setUp(self):
        self.packet = M.synthetic_packet()
        envelope = M.synthetic_seat_envelope()
        self.recipes = R.build_recipes([("run001", "seat_gpt.json", envelope)], self.packet)
        self.by_id = {rc.claim.id: rc for rc in self.recipes}

    def test_observation_without_packet_ref_is_not_built(self):
        # o4 has no packetRef.path -> not represented as any Recipe.
        for claim_id in self.by_id:
            self.assertNotIn("o4", self.by_id[claim_id].claim.provenance.get("obs_id", ""))
        self.assertEqual(len(self.recipes), 4)  # o1, o2, o3, ce1

    def test_grounded_candidate_id_and_fields(self):
        claim_id = "run001/seat_gpt.json#H-z1-time-001/observations[0]"
        self.assertIn(claim_id, self.by_id)
        rc = self.by_id[claim_id]
        self.assertEqual(rc.claim.form, core.Form.AGGREGATE)
        self.assertEqual(rc.claim.subject, "aggregates.groups.core.games.value")
        self.assertEqual(rc.claim.value, 20.0)
        self.assertIsNone(rc.not_found_reason)
        self.assertIsNone(rc.unverifiable_reason)
        self.assertEqual(rc.contract.comparator, "canonical_json_equals")
        self.assertEqual(rc.contract.params["expected"], 20)
        self.assertEqual(rc.pointers, (core.Pointer("packet", "aggregates.groups.core.games.value"),))
        self.assertEqual(rc.claim.provenance["obs_id"], "o1")
        self.assertEqual(rc.claim.provenance["hypothesis_id"], "H-z1-time-001")
        self.assertEqual(rc.claim.provenance["kind"], "finding")
        self.assertTrue(rc.claim.provenance["value_is_number"])
        self.assertEqual(rc.claim.provenance["raw_value"], 20)
        self.assertEqual(rc.claim.provenance["at"], "observations[0]")

    def test_value_mismatch_candidate_still_bound(self):
        claim_id = "run001/seat_gpt.json#H-z1-time-001/observations[1]"
        rc = self.by_id[claim_id]
        self.assertIsNone(rc.not_found_reason)
        self.assertEqual(rc.contract.params["expected"], 99)  # the (wrong) claimed value

    def test_pointer_not_found_candidate_has_no_contract(self):
        claim_id = "run001/seat_gpt.json#H-z1-time-001/observations[2]"
        rc = self.by_id[claim_id]
        self.assertIsNone(rc.contract)
        self.assertEqual(rc.not_found_reason, RV.NO_ROW)
        self.assertEqual(rc.claim.form, core.Form.AGGREGATE)

    def test_counter_evidence_is_always_unverifiable(self):
        claim_id = "run001/seat_gpt.json#H-z1-time-001/counterEvidence.items[0].observations[0]"
        rc = self.by_id[claim_id]
        self.assertEqual(rc.unverifiable_reason, R.NO_PACKET_REF_REASON)
        self.assertIsNone(rc.contract)
        self.assertEqual(rc.pointers, ())
        self.assertEqual(rc.claim.subject, "facts.moves[0].usi")
        self.assertEqual(rc.claim.form, core.Form.DIRECT_VALUE)
        self.assertIsNone(rc.claim.value)  # "7g7f" is a string, not a number

    def test_modifiers_always_empty(self):
        for rc in self.recipes:
            self.assertIsNone(rc.claim.modifiers.population)
            self.assertEqual(rc.claim.modifiers.time_range, ())
            self.assertIsNone(rc.claim.modifiers.normalization)

    def test_statement_never_read_into_provenance(self):
        envelope = M.synthetic_seat_envelope()
        envelope["items"][0]["statement"] = "顧客に見せる文(読んではいけない)"
        recipes = R.build_recipes([("run001", "seat_gpt.json", envelope)], self.packet)
        for rc in recipes:
            self.assertNotIn("statement", rc.claim.provenance)


class BuildRecipesMultipleEnvelopesTest(unittest.TestCase):
    def test_skips_envelopes_without_items_list(self):
        envelope_without_items = {"not_items": []}
        recipes = R.build_recipes([("r", "seat_gpt.json", envelope_without_items)], M.synthetic_packet())
        self.assertEqual(recipes, [])


if __name__ == "__main__":
    unittest.main()
