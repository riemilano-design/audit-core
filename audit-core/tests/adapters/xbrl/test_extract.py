# -*- coding: utf-8 -*-
import unittest

from adapters.xbrl import extract as E
from adapters.xbrl import vocabulary as V


class IterNumbersTest(unittest.TestCase):
    def test_simple_yen_amount(self):
        got = E.iter_numbers("当期の売上高は1,234百万円となった。")
        self.assertEqual(len(got), 1)
        a, b, value, unit, prec = got[0]
        self.assertEqual(value, 1234.0)
        self.assertEqual(unit, "百万円")

    def test_kanji_amount(self):
        got = E.iter_numbers("資産合計は380億6千4百万円となった。")
        self.assertEqual(len(got), 1)
        _a, _b, value, unit, _prec = got[0]
        self.assertEqual(unit, "円")
        self.assertAlmostEqual(value, 38064000000.0)

    def test_negative_sign(self):
        # "293百万円" is consumed by AMOUNT_JP_RE (the kanji-amount parser),
        # not by NUM_RE, so the yielded value is already in yen (293e6),
        # matching xbrl_probe.py's AMOUNT_JP_RE/NUM_RE overlap handling.
        got = E.iter_numbers("当期は△293百万円減少した。")
        self.assertEqual(len(got), 1)
        _a, _b, value, unit, _prec = got[0]
        self.assertEqual(unit, "円")
        self.assertEqual(value, -293000000.0)

    def test_two_numbers_sorted_by_position(self):
        got = E.iter_numbers("10％増加し、20百万円となった。")
        self.assertEqual(len(got), 2)
        self.assertLess(got[0][0], got[1][0])

    def test_no_number(self):
        self.assertEqual(E.iter_numbers("数字のない文です。"), [])


class SubjectOfTest(unittest.TestCase):
    def test_finds_nearest_subject(self):
        s = "資産合計は純資産合計を上回る1,000百万円であった。"
        pos = s.index("1,000")
        subj, elems = E.subject_of(s, pos, V.SUBJECTS_73)
        self.assertEqual(subj, "純資産合計")

    def test_prefers_longer_word_on_tie_end(self):
        # C-1c monitor note (XP-C1c-2): the earlier version of this test
        # used only "資産合計" against SUBJECTS_73, where the only two
        # entries spelled that way are the *same* word (a duplicate, not
        # a tie between two different-length words ending at the same
        # position) -- it never exercised `len(word) > len(best[1])`
        # (SUBJECTS_73 happens to always list the longer of any two
        # suffix-related words first, so list order alone -- not the
        # length check -- picked the right one even without this test).
        #
        # This uses a small synthetic ``subjects`` list (``subject_of``
        # takes it as a parameter) with the *shorter* word listed first,
        # so the correct answer requires the length comparison on the
        # tie, not just "whichever came first". "純資産合計" (5 chars)
        # ends with "資産合計" (4 chars) at the exact same position when
        # the sentence's head is "純資産合計は".
        subjects = [("資産合計", ["Assets"]), ("純資産合計", ["NetAssets"])]
        s = "純資産合計は1,000百万円であった。"
        pos = s.index("1,000")
        head = s[:pos]
        self.assertEqual(head.rfind("純資産合計") + len("純資産合計"), head.rfind("資産合計") + len("資産合計"))
        subj, elems = E.subject_of(s, pos, subjects)
        self.assertEqual(subj, "純資産合計")
        self.assertEqual(elems, ["NetAssets"])

    def test_no_subject(self):
        s = "何もない1,000百万円の文。"
        pos = s.index("1,000")
        subj, elems = E.subject_of(s, pos, V.SUBJECTS_73)
        self.assertIsNone(subj)

    def test_subjects_74_sees_segment_profit(self):
        s = "セグメント利益は1,000百万円であった。"
        pos = s.index("1,000")
        subj73, _ = E.subject_of(s, pos, V.SUBJECTS_73)
        subj74, _ = E.subject_of(s, pos, V.SUBJECTS_74)
        self.assertNotEqual(subj73, "セグメント利益")
        self.assertEqual(subj74, "セグメント利益")


class OwnSignMatchTest(unittest.TestCase):
    def test_matches_own_number(self):
        window = "3.3%増加した一方、2.7%減少した"
        m = E.own_sign_match(window, 3.3)
        self.assertIsNotNone(m)
        self.assertIn("3.3", m.group(0))

    def test_rejects_other_number(self):
        window = "3.3%増加した一方、2.7%減少した"
        m = E.own_sign_match(window, 9.9)
        self.assertIsNone(m)


class ResolveMembersTest(unittest.TestCase):
    def test_sentence_hit(self):
        sentences = ["美容事業の売上高が増加した。", "その他の記述。"]
        paras = [0, 1]  # different paragraph: no carry-back
        reg = {"m1": "美容事業"}
        got = E.resolve_members(sentences, paras, reg)
        self.assertEqual(got[0], ("m1", "sentence"))
        self.assertEqual(got[1], (None, None))

    def test_carry_back_within_paragraph(self):
        sentences = ["美容事業の概況。", "売上は増加した。", "利益も伸びた。"]
        paras = [0, 0, 0]
        reg = {"m1": "美容事業"}
        got = E.resolve_members(sentences, paras, reg)
        self.assertEqual(got[0], ("m1", "sentence"))
        self.assertEqual(got[1], ("m1", "carried"))
        self.assertEqual(got[2], ("m1", "carried"))

    def test_carry_back_stops_at_paragraph_boundary(self):
        sentences = ["美容事業の概況。", "別の段落の文。"]
        paras = [0, 1]
        reg = {"m1": "美容事業"}
        got = E.resolve_members(sentences, paras, reg)
        self.assertEqual(got[1], (None, None))

    def test_ambiguous_when_two_hits(self):
        sentences = ["美容事業と理美容事業の両方が伸びた。"]
        paras = [0]
        reg = {"m1": "美容事業", "m2": "理美容事業"}
        got = E.resolve_members(sentences, paras, reg)
        self.assertEqual(got[0], (E.AMBIG, "ambiguous"))


class ClaimMemberBTest(unittest.TestCase):
    def test_consolidated_marker_wins(self):
        s = "全社の売上高は増加した。"
        reg = {}
        got = E.claim_member_B(s, s.index("増加"), reg, (None, None))
        self.assertEqual(got, (None, "consolidated"))

    def test_single_segment_marker(self):
        s = "美容事業の売上高は増加した。"
        reg = {"m1": "美容事業"}
        got = E.claim_member_B(s, s.index("増加"), reg, (None, None))
        self.assertEqual(got, ("m1", "claim"))

    def test_no_marker_falls_back(self):
        s = "売上高は増加した。"
        reg = {"m1": "美容事業"}
        fallback = ("m9", "carried")
        got = E.claim_member_B(s, s.index("増加"), reg, fallback)
        self.assertEqual(got, fallback)

    def test_two_different_segments_connected_are_ambiguous(self):
        s = "美容事業及び理美容事業の売上高は増加した。"
        reg = {"m1": "美容事業", "m2": "理美容事業"}
        got = E.claim_member_B(s, s.index("増加"), reg, (None, None))
        self.assertEqual(got, (E.AMBIG, "ambiguous"))


if __name__ == "__main__":
    unittest.main()
