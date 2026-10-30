# -*- coding: utf-8 -*-
import unittest

import audit_core as core

from adapters.kokkai import comparators as C


def _ev(speaker, speech):
    return (core.Resolved(value=None, unit=None, precision=None, meta={"speaker": speaker, "speech": speech}),)


def _claim(value=None, unit=None):
    return core.Claim(id="c", form=core.Form.DIRECT_VALUE, subject=None, value=value, unit=unit,
                      modifiers=core.Modifiers(), provenance={})


class SpeakerEqualsTest(unittest.TestCase):
    def test_same_name_matches_ignoring_spaces(self):
        r = C.speaker_equals(_ev("山田 太郎", ""), _claim(), core.Contract("speaker_equals", {"expected": "山田太郎"}))
        self.assertTrue(r.match)

    def test_different_name_does_not_match(self):
        r = C.speaker_equals(_ev("山田太郎", ""), _claim(), core.Contract("speaker_equals", {"expected": "佐藤花子"}))
        self.assertFalse(r.match)

    def test_empty_expected_never_matches(self):
        r = C.speaker_equals(_ev("", ""), _claim(), core.Contract("speaker_equals", {"expected": ""}))
        self.assertFalse(r.match)


class QuoteInSpeechTest(unittest.TestCase):
    SPEECH = "○山田委員　暫定予算は三百億円で、\r\n　期間は一か月であります。"

    def test_verbatim_quote_is_found(self):
        r = C.quote_in_speech(_ev("x", self.SPEECH), _claim(), core.Contract("quote_in_speech", {"quote": "暫定予算は三百億円で"}))
        self.assertTrue(r.match)

    def test_quote_across_a_line_break_is_found_after_whitespace_removal(self):
        r = C.quote_in_speech(_ev("x", self.SPEECH), _claim(), core.Contract("quote_in_speech", {"quote": "三百億円で、期間は一か月"}))
        self.assertTrue(r.match)

    def test_one_changed_character_is_not_found(self):
        r = C.quote_in_speech(_ev("x", self.SPEECH), _claim(), core.Contract("quote_in_speech", {"quote": "暫定予算は三百万円で"}))
        self.assertFalse(r.match)

    def test_empty_quote_is_not_found(self):
        r = C.quote_in_speech(_ev("x", self.SPEECH), _claim(), core.Contract("quote_in_speech", {"quote": ""}))
        self.assertFalse(r.match)

    def test_full_width_digits_are_unified_by_nfkc(self):
        r = C.quote_in_speech(_ev("x", "Ｇ７の会談"), _claim(), core.Contract("quote_in_speech", {"quote": "G7の会談"}))
        self.assertTrue(r.match)


class NumberInSpeechTest(unittest.TestCase):
    SPEECH = "一・一兆円の規模で、一五％の伸びです。一九九一年以来、三回目。"

    def test_value_and_unit_present_matches(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(1.1e12, "円"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)
        self.assertEqual(r.recomputed, 1.1e12)
        self.assertEqual(r.detail["matched_raw"], "一・一兆円")

    def test_unit_alias_in_claim_is_normalized(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(15.0, "パーセント"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)

    def test_value_present_but_unit_differs_does_not_match(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(15.0, "円"), core.Contract("number_in_speech", {}))
        self.assertFalse(r.match)

    def test_value_absent_does_not_match(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(1.2e12, "円"), core.Contract("number_in_speech", {}))
        self.assertFalse(r.match)
        self.assertIsNone(r.recomputed)

    def test_ten_times_the_value_does_not_match(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(1.1e13, "円"), core.Contract("number_in_speech", {}))
        self.assertFalse(r.match)

    def test_year_positional(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(1991.0, "年"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)

    def test_none_claim_value_does_not_match(self):
        r = C.number_in_speech(_ev("x", self.SPEECH), _claim(None, "円"), core.Contract("number_in_speech", {}))
        self.assertFalse(r.match)


class Round2NumberInSpeechTest(unittest.TestCase):
    def test_eighty_percent_matches_hachiwari(self):
        r = C.number_in_speech(_ev("x", "ＬＮＧは輸入量の約八割を長期契約で"), _claim(80.0, "％"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)
        self.assertEqual(r.detail["matched_raw"], "八割")

    def test_eight_wari_claim_also_matches(self):
        r = C.number_in_speech(_ev("x", "約八割を"), _claim(8.0, "割"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)

    def test_eighty_three_people_matches_mei(self):
        r = C.number_in_speech(_ev("x", "合計八十三名を派遣"), _claim(83.0, "人"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)

    def test_forty_five_ships(self):
        r = C.number_in_speech(_ev("x", "四十五隻が入域"), _claim(45.0, "隻"), core.Contract("number_in_speech", {}))
        self.assertTrue(r.match)

    def test_wari_does_not_make_eight_percent_match(self):
        r = C.number_in_speech(_ev("x", "約八割を"), _claim(8.0, "％"), core.Contract("number_in_speech", {}))
        self.assertFalse(r.match)
