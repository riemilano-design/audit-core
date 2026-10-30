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


# ---------------------------------------------------------------------------
# 主語の規則の直し(人間の判断 1、2026-10-08)。計画と予測は
# docs/XBRL_SUBJECT_RULE_PLAN_2026-10-08.md(実装前に封じた)。
# ---------------------------------------------------------------------------

# 実物の文。**ここで字を打ち直さない** ― 書類から取り出した文をそのまま置く
# (打ち直すと「実装が通る文」を作ってしまう)。
SENT_N063 = ("なお、販売費及び一般管理費は、グループ全体で、人員増加や給与水準アップ等の"
             "人的資本への投資、及び支払手数料並びに株主優待制度への取り組みに係る費用等の"
             "増加により、前連結会計年度比7億18百万円増加しております。")
SENT_N069 = ("当連結会計年度は、特別利益は固定資産売却益による19百万円、"
             "特別損失は固定資産除却損及び減損損失による25百万円を計上しております。")
SENT_T020 = ("これは主として、新株予約権の行使により資本金及び資本剰余金の合計が"
             "8億96百万円増加し、利益剰余金についても、配当金支払による8億40百万円の"
             "減少があったものの、親会社株主に帰属する当期純利益21億29百万円の計上により"
             "12億89百万円増加したことによるものであります。")
SENT_T046 = ("また、法人税等調整額は、前連結会計年度は△3億48百万円となり、"
             "利益を増加させておりましたが、当連結会計年度は21百万円となり、"
             "利益を減少させております。")


def _frozen_subject_of(sentence, pos, subjects):
    """``subject_of`` の**写し元の書き方そのまま**(置き換えの梯子)。
    並べ替えに書き換えた新しい実装がこれと 1 件も違わないことを、
    実物の 4 書類の全部の文で確かめるためだけに在る。
    """

    head = sentence[:pos]
    best = None
    for word, elems in subjects:
        i = head.rfind(word)
        if i < 0:
            continue
        end = i + len(word)
        if best is None or end > best[0] or (end == best[0] and len(word) > len(best[1])):
            best = (end, word, elems)
    return (best[1], best[2]) if best else (None, None)


class SubjectOfSkipNoneIsUnchangedTest(unittest.TestCase):
    """``skip=None`` のとき、写し元の梯子と 1 件も違わない。"""

    def test_equivalent_to_the_frozen_ladder_on_all_four_documents(self):
        from adapters.xbrl import edinet as _E, instance as _I, recipes as _R
        import dataclasses
        checked = 0
        for doc in ("S100Z4Q1", "S100Z4B6", "S100YMFV", "S100Z37J"):
            zb = open(_E.cache_path(doc), "rb").read()
            inst = _I.load_instance(zb)
            hand_rows, added, _ov = _R._label_subjects(zb, inst, V.PROFILES["P13"])
            profile = dataclasses.replace(V.PROFILES["P13"], subjects=tuple(hand_rows) + tuple(added))
            tbs = inst["textblocks"]
            name = _I.select_mdna(tbs)
            text = _I.strip_html(tbs[name]) if name else ""
            import re as _re
            for s in E.split_sentences(text, True):
                # 数の位置と**向きの語の位置**の両方で当てる(``subject_of`` は
                # 両方から呼ばれる)。
                places = [a for (a, _b, _sg, _u, _p) in E.iter_numbers(s)]
                for w in E.DIRECTION_WORDS:
                    places += [m.start() for m in _re.finditer(w, s)]
                for a in places:
                    self.assertEqual(E.subject_of(s, a, profile.subjects),
                                     _frozen_subject_of(s, a, profile.subjects))
                    checked += 1
        # 「0 件で緑」を防ぐ: 実際に何件当てたかを見る(実測 700 件あまり。
        # 床は低めに取る ― ここは本数を留める場所ではない)。
        self.assertGreater(checked, 200, checked)

    def test_ties_go_to_the_earlier_row_of_the_list(self):
        # 同じ終わり・同じ長さなら**一覧の早い方**が勝つ(``dict`` は最後を
        # 採るので、ここを ``dict`` で書くと逆になる)。
        subjects = [("売上高", ["First"]), ("売上高", ["Second"])]
        self.assertEqual(E.subject_of("売上高は100円", 4, subjects), ("売上高", ["First"]))

    def test_longer_word_wins_at_the_same_end(self):
        subjects = [("資産合計", ["A"]), ("純資産合計", ["B"])]
        self.assertEqual(E.subject_of("純資産合計は100円", 6, subjects)[1], ["B"])

    def test_rightmost_end_wins(self):
        subjects = [("売上高", ["A"]), ("営業利益", ["B"])]
        self.assertEqual(E.subject_of("売上高は、営業利益は100円", 10, subjects)[0], "営業利益")


class SubjectOfSkipTest(unittest.TestCase):
    def test_skip_moves_to_the_next_candidate(self):
        subjects = [("売上高", ["A"]), ("営業利益", ["B"])]
        skip = lambda _s, _i, word: word == "営業利益"
        self.assertEqual(E.subject_of("売上高は、営業利益は100円", 10, subjects, skip)[0], "売上高")

    def test_skipping_every_candidate_returns_none(self):
        subjects = [("売上高", ["A"]), ("営業利益", ["B"])]
        self.assertEqual(E.subject_of("売上高は、営業利益は100円", 10, subjects, lambda *_a: True),
                         (None, None))

    def test_skip_receives_the_position_of_the_candidate(self):
        seen = []
        subjects = [("売上高", ["A"])]
        E.subject_of("売上高は100円", 4, subjects, lambda s, i, w: seen.append((s[i:i + len(w)], i)) or False)
        self.assertEqual(seen, [("売上高", 0)])


class ClauseSpanTest(unittest.TestCase):
    def test_bounded_by_the_japanese_comma(self):
        s = "あああ、いいい、ううう"
        self.assertEqual(E.clause_span(s, 4, 7), (4, 7))

    def test_bounded_by_parens_both_widths(self):
        s = "ああ(いい)うう"
        self.assertEqual(s[slice(*E.clause_span(s, 3, 5))], "いい")
        s2 = "ああ（いい）うう"
        self.assertEqual(s2[slice(*E.clause_span(s2, 3, 5))], "いい")

    def test_whole_sentence_when_there_is_no_break(self):
        s = "ああいいうう"
        self.assertEqual(E.clause_span(s, 2, 4), (0, 6))

    def test_kuten_ends_the_clause(self):
        s = "ああいい。うう"
        self.assertEqual(E.clause_span(s, 2, 4), (0, 4))


class SkipCoordinatedCauseTest(unittest.TestCase):
    """S1。実物の 2 文で、落とす語と**落としてはいけない語**を両方当てる。"""

    def test_n063_drops_only_the_coordinated_members(self):
        for word, expected in (("販売費及び一般管理費", False), ("販売費", False),
                               ("一般管理費", False), ("支払手数料", True)):
            i = SENT_N063.index(word)
            self.assertEqual(E.skip_coordinated_cause(SENT_N063, i, word), expected, word)

    def test_n069_keeps_the_topic_and_drops_both_sides_of_the_coordination(self):
        for word, expected in (("特別利益", False), ("固定資産売却益", False),
                               ("特別損失", False), ("固定資産除却損", True), ("減損損失", True)):
            i = SENT_N069.index(word)
            self.assertEqual(E.skip_coordinated_cause(SENT_N069, i, word), expected, word)

    def test_a_substring_of_a_dropped_member_is_dropped_too(self):
        # 「固定資産」は「固定資産除却損」の中に在る。1 回目の実測ではこれが
        # 残って「特別損失」より右で終わり、封じた予測(N069 が GROUNDED)を
        # 外した。右へ進んで最初に当たるのが並立の接続語なら落とす。
        i = SENT_N069.index("固定資産除却損")
        self.assertTrue(E.skip_coordinated_cause(SENT_N069, i, "固定資産"))

    def test_a_coordination_without_a_cause_is_kept(self):
        s = "売上高及び営業利益は100円増加しました。"
        self.assertFalse(E.skip_coordinated_cause(s, s.index("売上高"), "売上高"))
        self.assertFalse(E.skip_coordinated_cause(s, s.index("営業利益"), "営業利益"))

    def test_a_cause_without_a_coordination_is_kept(self):
        # N068 の型。並立が無ければ落とさない ― これが S1 が「並立」を
        # 要件にしている理由である。
        s = "特別利益は固定資産売却益による19百万円を計上しております。"
        self.assertFalse(E.skip_coordinated_cause(s, s.index("固定資産売却益"), "固定資産売却益"))

    def test_the_cause_must_be_in_the_same_clause(self):
        s = "売上原価及び販売費が増加、前期はのれんの減損による損失がありました。"
        self.assertFalse(E.skip_coordinated_cause(s, s.index("売上原価"), "売上原価"))


class SkipPartOfAggregateTest(unittest.TestCase):
    """S3。「A及びBの合計」の成分を落とす。合計でない並立は落とさない。"""

    def test_t020_drops_both_components_and_keeps_the_others(self):
        for word, expected in (("資本金", True), ("資本剰余金", True),
                               ("利益剰余金", False), ("新株予約権", False)):
            i = SENT_T020.index(word)
            self.assertEqual(E.skip_part_of_aggregate(SENT_T020, i, word), expected, word)

    def test_a_coordination_without_an_aggregate_is_kept(self):
        s = "資本金及び資本剰余金が8億96百万円増加しました。"
        self.assertFalse(E.skip_part_of_aggregate(s, s.index("資本金"), "資本金"))

    def test_the_longer_aggregate_phrase_also_counts(self):
        s = "資本金及び資本剰余金の合計額が8億96百万円増加しました。"
        self.assertTrue(E.skip_part_of_aggregate(s, s.index("資本剰余金"), "資本剰余金"))

    def test_s1_and_s3_do_not_fire_on_each_others_material(self):
        # S1 は「の合計」では落とさない・S3 は「による」では落とさない。
        self.assertFalse(E.skip_coordinated_cause(SENT_T020, SENT_T020.index("資本剰余金"), "資本剰余金"))
        self.assertFalse(E.skip_part_of_aggregate(SENT_N069, SENT_N069.index("減損損失"), "減損損失"))


class DirectionObjectTest(unittest.TestCase):
    """S2。「<名詞>を増加/減少」の目的語。"""

    def test_t046_both_direction_words_point_at_the_object(self):
        self.assertEqual(E.direction_object(SENT_T046, SENT_T046.index("増加")), "利益")
        self.assertEqual(E.direction_object(SENT_T046, SENT_T046.index("減少")), "利益")

    def test_an_intransitive_direction_word_has_no_object(self):
        s = "流動資産は148億86百万円増加し、686億34百万円となりました。"
        self.assertIsNone(E.direction_object(s, s.index("増加")))

    def test_the_object_does_not_cross_a_clause_break(self):
        s = "利益は、を増加させました。"
        self.assertIsNone(E.direction_object(s, s.index("増加")))

    def test_only_the_direction_word_at_that_position_is_answered(self):
        self.assertIsNone(E.direction_object(SENT_T046, 0))


class SubjectSkipForTest(unittest.TestCase):
    """``skip`` は 2 つのフラグからしか生まれない。**P1〜P14 は None。**"""

    def test_none_for_every_profile_up_to_p14(self):
        for name, p in V.PROFILES.items():
            if name == "P15":
                continue
            self.assertIsNone(E.subject_skip_for(p), name)

    def test_p15_has_a_skip(self):
        self.assertIsNotNone(E.subject_skip_for(V.PROFILES["P15"]))

    def test_s1_only_profile_skips_only_the_cause_form(self):
        import dataclasses
        p = dataclasses.replace(V.PROFILES["P13"], subject_skip_coordinated_cause=True)
        skip = E.subject_skip_for(p)
        self.assertTrue(skip(SENT_N069, SENT_N069.index("減損損失"), "減損損失"))
        self.assertFalse(skip(SENT_T020, SENT_T020.index("資本剰余金"), "資本剰余金"))

    def test_s3_only_profile_skips_only_the_aggregate_form(self):
        import dataclasses
        p = dataclasses.replace(V.PROFILES["P13"], subject_not_part_of_aggregate=True)
        skip = E.subject_skip_for(p)
        self.assertTrue(skip(SENT_T020, SENT_T020.index("資本剰余金"), "資本剰余金"))
        self.assertFalse(skip(SENT_N069, SENT_N069.index("減損損失"), "減損損失"))

    def test_both_flags_skip_either_form(self):
        skip = E.subject_skip_for(V.PROFILES["P15"])
        self.assertTrue(skip(SENT_N069, SENT_N069.index("減損損失"), "減損損失"))
        self.assertTrue(skip(SENT_T020, SENT_T020.index("資本剰余金"), "資本剰余金"))
