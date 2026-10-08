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


class ParenSentenceSplitTest(unittest.TestCase):
    """XBRL 直し §4(2026-10-08): 丸括弧の中の句点では文を切らない。

    ``paren_aware`` が偽のときは凍結の切り方(``re.split(r"(?<=。)|\n")``)と
    1 文字も変わらないことを、同じ入力で両方当てて確かめる。
    """

    PAREN = "当連結会計年度末における現金及び現金同等物(以下「資金」という。)は、2億9千3百万円減少しました。"

    def test_frozen_split_breaks_inside_the_parenthesis(self):
        # 直す前の振る舞い(主語を失う側)を固定する。
        got = E.split_sentences(self.PAREN)
        self.assertEqual(len(got), 2)
        self.assertTrue(got[1].startswith(")は、"))
        self.assertNotIn("現金及び現金同等物", got[1])

    def test_paren_aware_split_keeps_the_sentence_whole(self):
        got = E.split_sentences(self.PAREN, True)
        self.assertEqual(len(got), 1)
        self.assertIn("現金及び現金同等物", got[0])
        self.assertIn("減少しました。", got[0])

    def test_newline_still_splits_and_resets_the_paren_depth(self):
        # 改行では切る(段落の構造は改行が決める)。括弧の深さは行をまたいで
        # 持ち越さないので、2 行目の 。 は守られない ― 既知の帰結として固定する。
        got = E.split_sentences("あ(以下「資\n金」という。)は減った。", True)
        self.assertEqual(got, ["あ(以下「資", "金」という。", ")は減った。"])

    def test_fullwidth_and_halfwidth_parens_both_count(self):
        for op, cl in (("(", ")"), ("（", "）")):
            got = E.split_sentences("あ%sいう。%sは減った。" % (op, cl), True)
            self.assertEqual(len(got), 1, (op, cl))

    def test_kuten_outside_the_parenthesis_still_splits(self):
        got = E.split_sentences("あ(い)。うえ。", True)
        self.assertEqual(len(got), 2)

    def test_nested_parens_are_counted_by_depth(self):
        got = E.split_sentences("あ(い(う。)え。)お。", True)
        self.assertEqual(len(got), 1)

    def test_stray_closing_paren_does_not_collapse_the_rest(self):
        # 深さは 0 より下げない。閉じ括弧が余っていても後ろの文は切れる。
        self.assertEqual(E.split_after_kuten_outside_parens(")あ。い。"), [")あ。", "い。", ""])

    def test_unclosed_opening_paren_swallows_the_rest(self):
        # 開いたまま閉じない括弧は、その行の終わりまで 1 文になる(既知の帰結)。
        got = E.split_sentences("あ(い。う。", True)
        self.assertEqual(len(got), 1)

    def test_text_without_parens_is_split_identically_both_ways(self):
        # 不変: 括弧が無い本文では 2 つの切り方が同じ列を返す。
        t = "一つめ。二つめ。\n三つめ。"
        self.assertEqual(E.split_sentences(t), E.split_sentences(t, True))

    def test_paragraph_index_agrees_with_each_split(self):
        t = "あ(以下「資金」という。)は減った。\n次の段落。"
        self.assertEqual(E.paragraph_index(t, E.split_sentences(t)), [0, 0, 1])
        self.assertEqual(E.paragraph_index(t, E.split_sentences(t, True), True), [0, 1])

    def test_paragraph_index_refuses_a_mismatched_sentence_list(self):
        # 文の列と段落の数え方がずれたら黙らずに落ちる。
        t = "あ(以下「資金」という。)は減った。"
        with self.assertRaises(AssertionError):
            E.paragraph_index(t, E.split_sentences(t), True)
