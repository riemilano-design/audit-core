# -*- coding: utf-8 -*-
import unittest

from adapters.kokkai import recipes as R
from adapters.kokkai import registry_setup as RS
from tests.adapters.kokkai import _material as M


class BuildRecipesTest(unittest.TestCase):
    def test_speaker_only_claim_yields_one_recipe(self):
        rs = R.build_recipes(M.summary([M.claim("K-1")]))
        self.assertEqual([r.claim.id for r in rs], ["K-1/speaker"])
        self.assertEqual(rs[0].contract.comparator, "speaker_equals")
        self.assertEqual(rs[0].contract.params["expected"], "山田太郎")
        self.assertEqual(str(rs[0].pointers[0]), "kokkai:%s#1" % M.ISSUE)

    def test_quote_and_number_add_recipes_in_order(self):
        rs = R.build_recipes(M.summary([M.claim("K-1", quote="三百億円", number={"text": "三百億円", "value": 3e10, "unit": "円"})]))
        self.assertEqual([r.claim.id for r in rs], ["K-1/speaker", "K-1/quote", "K-1/number"])
        self.assertEqual(rs[1].contract.comparator, "quote_in_speech")
        self.assertEqual(rs[1].contract.params["quote"], "三百億円")
        self.assertEqual(rs[2].contract.comparator, "number_in_speech")
        self.assertEqual(rs[2].claim.value, 3e10)
        self.assertEqual(rs[2].claim.unit, "円")

    def test_number_unit_is_normalized(self):
        rs = R.build_recipes(M.summary([M.claim("K-1", number={"text": "一五パーセント", "value": 15, "unit": "パーセント"})]))
        self.assertEqual(rs[1].claim.unit, "％")

    def test_missing_order_is_unverifiable_no_pointer_given(self):
        c = M.claim("K-1"); del c["speech_order"]
        rs = R.build_recipes(M.summary([c]))
        self.assertEqual(len(rs), 1)
        self.assertEqual(rs[0].unverifiable_reason, RS.NO_POINTER_GIVEN)
        self.assertEqual(rs[0].pointers, ())

    def test_non_int_order_is_unverifiable(self):
        rs = R.build_recipes(M.summary([M.claim("K-1", order="1")]))
        self.assertEqual(rs[0].unverifiable_reason, RS.NO_POINTER_GIVEN)
        rs = R.build_recipes(M.summary([M.claim("K-1", order=True)]))
        self.assertEqual(rs[0].unverifiable_reason, RS.NO_POINTER_GIVEN)

    def test_missing_speaker_is_unverifiable_but_quote_still_checked(self):
        rs = R.build_recipes(M.summary([M.claim("K-1", speaker="", quote="三百億円")]))
        self.assertEqual([r.claim.id for r in rs], ["K-1/speaker", "K-1/quote"])
        self.assertEqual(rs[0].unverifiable_reason, RS.NO_SPEAKER_GIVEN)
        self.assertIsNone(rs[1].unverifiable_reason)

    def test_empty_quote_and_number_without_value_add_nothing(self):
        rs = R.build_recipes(M.summary([M.claim("K-1", quote="  ", number={"text": "x", "value": None, "unit": "円"})]))
        self.assertEqual([r.claim.id for r in rs], ["K-1/speaker"])

    def test_provenance_carries_claim_id_check_and_text(self):
        rs = R.build_recipes(M.summary([M.claim("K-7", text="文です", quote="q")]))
        self.assertEqual(rs[1].claim.provenance["claim_id"], "K-7")
        self.assertEqual(rs[1].claim.provenance["check"], "quote")
        self.assertEqual(rs[1].claim.provenance["text"], "文です")
        self.assertEqual(rs[1].claim.provenance["word"], "q")
