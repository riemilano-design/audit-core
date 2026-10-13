# -*- coding: utf-8 -*-
import unittest

import audit_core as core

from adapters.kokkai import load as L
from adapters.kokkai import resolve as RV
from tests.adapters.kokkai import _material as M


class ResolverTest(unittest.TestCase):
    def setUp(self):
        self.resolver = RV.make_resolver(L.index_meeting(M.MEETING))

    def test_existing_order_resolves_to_speaker_and_speech(self):
        r = self.resolver(core.Pointer("kokkai", M.ISSUE + "#2"))
        self.assertIsNotNone(r)
        self.assertIsNone(r.value)
        self.assertEqual(r.meta["speaker"], "佐藤花子")
        self.assertIn("一・一兆円", r.meta["speech"])
        self.assertEqual(r.meta["speechOrder"], 2)

    def test_missing_order_is_none(self):
        self.assertIsNone(self.resolver(core.Pointer("kokkai", M.ISSUE + "#99")))

    def test_other_issue_is_none(self):
        self.assertIsNone(self.resolver(core.Pointer("kokkai", "OTHER#1")))

    def test_bad_locator_is_none(self):
        self.assertIsNone(self.resolver(core.Pointer("kokkai", M.ISSUE)))
        self.assertIsNone(self.resolver(core.Pointer("kokkai", M.ISSUE + "#x")))

    def test_parse_locator(self):
        self.assertEqual(RV.parse_locator("A#12"), ("A", 12))
        self.assertIsNone(RV.parse_locator("A"))
        self.assertIsNone(RV.parse_locator("A#"))


class IndexMeetingTest(unittest.TestCase):
    def test_duplicate_order_raises(self):
        data = {"meetingRecord": [{"issueID": "X", "speechRecord": [
            {"speechOrder": 1, "speaker": "a", "speech": ""}, {"speechOrder": 1, "speaker": "b", "speech": ""}]}]}
        with self.assertRaises(ValueError):
            L.index_meeting(data)

    def test_two_records_raise(self):
        with self.assertRaises(ValueError):
            L.index_meeting({"meetingRecord": [{}, {}]})
