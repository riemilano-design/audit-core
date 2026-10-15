# -*- coding: utf-8 -*-
"""直した engine の**原因別**回帰試験(封 docs/DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md §2・§4)。

材料は**手で書いた文**だけ。今回の 24 件の報告文はここでは使わない。
封 §4 の検出条件を試験にする。**赤くなったら、試験を直す前に理由を書く。**
"""
import hashlib
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIX = os.path.join(ROOT, "measure", "sheet_m4_engine_fix_2026-10-15.py")
FROZEN = os.path.join(ROOT, "measure", "sheet_m4_engine_2026-10-15.py")

spec = importlib.util.spec_from_file_location("m4fix", FIX)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def entry(name, scope, column, value, level="款", children=None, ref="D10",
          file="決算書 歳出"):
    return {"scope": scope, "level": level, "name": name, "code": "01", "column": column,
            "value": value, "file": file, "children": children,
            "evidence": {"scope_from": "表題行", "code_ref": "A10", "name_ref": "B10",
                         "value_ref": ref, "header_ref": "D7"}}


def prep(entries, text):
    """索引から手がかりと語彙を作り、文を切り出す(本番と同じ順)。"""
    cues = E.column_cues(entries)
    vocab = E.vocabulary(entries)
    return E.extract_claims(text, vocab, cues), cues


class FrozenEngineTest(unittest.TestCase):
    """**失敗を出した engine は 1 バイトも変えない。**"""

    SHA = None  # 下の試験で測って固定する

    def test_the_frozen_engine_is_a_separate_file(self):
        self.assertNotEqual(os.path.realpath(FIX), os.path.realpath(FROZEN))

    def test_the_frozen_engine_still_has_the_defect(self):
        """直した版と見分けがつくこと(凍結版は並び順で列を選ぶ)。"""
        s = importlib.util.spec_from_file_location("m4old", FROZEN)
        old = importlib.util.module_from_spec(s)
        s.loader.exec_module(old)
        vocab = [("一般会計", "一般会計")]
        c = old.extract_claims("一般会計の歳入決算額は1円、歳出決算額は2円です。", vocab)
        self.assertEqual([x["column"] for x in c], ["歳入決算額", "歳入決算額"])


class F1NearestColumnTest(unittest.TestCase):
    """F-1 列の手がかりは**最も近い**語(C-1)。"""

    ENTS = [entry("一般会計", "一般会計", c, v, level="会計", file="総括")
            for c, v in (("歳入決算額", 10), ("歳出決算額", 20), ("差額", 30))]

    def test_each_number_takes_its_own_column(self):
        c, _ = prep(self.ENTS, "一般会計の歳入決算額は10円、歳出決算額は20円で、差額は30円です。")
        self.assertEqual([x["column"] for x in c], ["歳入決算額", "歳出決算額", "差額"])

    def test_every_one_of_them_binds(self):
        c, _ = prep(self.ENTS, "一般会計の歳入決算額は10円、歳出決算額は20円で、差額は30円です。")
        for x in c:
            b = E.bind(x, self.ENTS)
            self.assertEqual(b["state"], "GROUNDED", x["id"])
            self.assertEqual(b["evidence"]["column"], x["column"], x["id"])

    def test_the_second_number_does_not_take_the_first_column(self):
        """凍結版が間違えた形そのもの。"""
        c, _ = prep(self.ENTS, "一般会計の歳入決算額は10円、歳出決算額は20円です。")
        self.assertEqual(c[1]["column"], "歳出決算額")


class F2MaximalWordTest(unittest.TestCase):
    """F-2 その位置で最長の語でなければ採らない(C-6)。"""

    ENTS = [entry("地方消費税清算会計", "地方消費税清算会計", "歳入決算額", 10, level="会計",
                  file="総括"),
            entry("議会費", "一般会計", "計", 50)]

    def test_kei_inside_kaikei_is_not_a_column_cue(self):
        c, _ = prep(self.ENTS, "地方消費税清算会計は歳入10円です。")
        self.assertNotEqual(c[0]["column"], "計")

    def test_kei_on_its_own_is_still_a_column_cue(self):
        c, _ = prep(self.ENTS, "議会費の計は50円です。")
        self.assertEqual(c[0]["column"], "計")

    def test_a_column_name_inside_an_account_name_is_not_taken(self):
        ents = self.ENTS + [entry("諸支出金", "一般会計", "支出済額", 7)]
        c, _ = prep(ents, "諸支出金が7円でした。")
        self.assertIsNone(c[0]["column"])


class F3HoldTest(unittest.TestCase):
    """F-3 一意に同定できなければ結ばない(C-7・C-3)。**最優先の安全欠陥。**"""

    def test_two_column_cues_before_the_number_hold(self):
        ents = [entry("公債費会計", "公債費会計", c, 100, level="会計", file="総括")
                for c in ("歳入決算額", "歳出決算額")]
        c, _ = prep(ents, "公債費会計は歳入・歳出とも100円で、差額は無い。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("列の手がかりが 2 つ以上", b["hold_reason"])
        self.assertIsNone(b["route"])

    def test_the_value_does_not_choose_between_two_equal_cells(self):
        """**値が一致するだけで選ばない。**"""
        ents = [entry("公債費会計", "公債費会計", c, 100, level="会計", file="総括")
                for c in ("歳入決算額", "歳出決算額")]
        c, _ = prep(ents, "公債費会計は歳入・歳出とも100円。")
        self.assertEqual(E.bind(c[0], ents)["state"], "UNVERIFIABLE")

    def test_candidates_split_across_accounts_hold(self):
        """同じ科目名が 2 つの会計に在り、文が会計を言っていない。"""
        ents = [entry("管理費", "一般会計", "支出済額", 11),
                entry("管理費", "公債費会計", "支出済額", 22)]
        c, _ = prep(ents, "管理費の支出済額は11円でした。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("4 欄が一意でない", b["hold_reason"])
        self.assertEqual(b["distinct_keys"], 2)
        self.assertFalse(b["range_identified"])

    def test_the_same_logical_cell_in_two_files_still_binds(self):
        """4 欄が全部同じで file だけ違うのは**同じセルの重複**。"""
        ents = [entry("教育費", "一般会計", "支出済額", 99, ref="F30", file="事項別明細"),
                entry("教育費", "一般会計", "支出済額", 99, ref="D20", file="決算書 歳出")]
        c, _ = prep(ents, "教育費の支出済額は99円でした。")
        b = E.bind(c[0], ents)
        self.assertEqual((b["state"], b["route"]), ("GROUNDED", "R-1"))
        self.assertEqual(b["duplicates"], 2)
        self.assertEqual(b["pointer"], "sheet:決算書 歳出!D20")   # 先に決めた file の順
        self.assertEqual(len(b["evidence"]["duplicate_pointers"]), 2)

    def test_the_file_order_is_not_chosen_by_value(self):
        self.assertEqual(E.FILE_ORDER, ("総括", "決算書 歳出", "事項別明細"))

    def test_a_single_candidate_is_unaffected(self):
        ents = [entry("議会費", "一般会計", "支出済額", 5)]
        c, _ = prep(ents, "議会費の支出済額は5円です。")
        self.assertEqual(E.bind(c[0], ents)["state"], "GROUNDED")


class F4AliasTest(unittest.TestCase):
    """F-4 別名は**文字列だけでは決めない**(C-2)。"""

    def material(self, meisai_scope="東京都一般会計", agree=True):
        ents = [entry("一般会計", "一般会計", "歳入決算額", 1000, level="会計", file="総括"),
                entry("教育費", "一般会計", "支出済額", 300, file="決算書 歳出"),
                entry("福祉費", "一般会計", "支出済額", 700, file="決算書 歳出"),
                entry("教育費", meisai_scope, "支出済額", 300 if agree else 301,
                      file="事項別明細"),
                entry("福祉費", meisai_scope, "支出済額", 700, file="事項別明細")]
        return ents

    def test_a_suffix_match_with_value_backing_becomes_an_alias(self):
        al = E.alias_table(self.material())
        self.assertIn("東京都一般会計", al["table"])
        self.assertEqual(al["table"]["東京都一般会計"]["canonical"], "一般会計")
        self.assertEqual(al["table"]["東京都一般会計"]["evidence"]["一致した款と列"], 2)
        self.assertEqual(al["table"]["東京都一般会計"]["evidence"]["食い違い"], 0)

    def test_a_prefix_match_is_never_an_alias(self):
        """`公債費`(款)と `公債費会計`(会計)を結ばない。**前方一致は認めない。**"""
        ents = [entry("公債費会計", "公債費会計", "歳入決算額", 10, level="会計", file="総括"),
                entry("公債費", "一般会計", "支出済額", 10, file="決算書 歳出"),
                entry("公債費", "公債費", "支出済額", 10, file="事項別明細")]
        al = E.alias_table(ents)
        self.assertNotIn("公債費", al["table"])

    def test_a_suffix_match_without_value_backing_is_unconfirmed(self):
        al = E.alias_table(self.material(agree=False))
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertEqual(al["unconfirmed"][0]["why"], "値の裏づけが無い")
        self.assertEqual(al["unconfirmed"][0]["mismatch"], 1)

    def test_an_ambiguous_suffix_is_unconfirmed(self):
        """2 つの正本に向く名前は使わない(単射)。"""
        ents = [entry("会計", "会計", "歳入決算額", 1, level="会計", file="総括"),
                entry("一般会計", "一般会計", "歳入決算額", 2, level="会計", file="総括"),
                entry("教育費", "東京都一般会計", "支出済額", 3, file="事項別明細")]
        al = E.alias_table(ents)
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertIn("接尾一致が 2 件", al["unconfirmed"][0]["why"])

    def test_the_table_is_injective_in_the_sense_recorded(self):
        al = E.alias_table(self.material())
        self.assertEqual(al["fan_in"], {})

    def test_canonicalizing_keeps_the_written_name_as_evidence(self):
        ents = E.canonicalize(self.material(), E.alias_table(self.material())["table"])
        m = [e for e in ents if e["file"] == "事項別明細"][0]
        self.assertEqual(m["scope"], "一般会計")
        self.assertEqual(m["evidence"]["scope_as_written"], "東京都一般会計")

    def test_the_alias_makes_the_cross_file_duplicate_bind(self):
        """別名を直すと、決算書と明細が**同じ論理セル**になり結べる。"""
        raw = self.material()
        ents = E.canonicalize(raw, E.alias_table(raw)["table"])
        c, _ = prep(ents, "教育費の支出済額は300円でした。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "GROUNDED")
        self.assertEqual(b["duplicates"], 2)

    def test_without_the_alias_the_same_claim_holds(self):
        """別名を当てなければ 4 欄が割れて保留になる(直しが効いている証拠)。"""
        raw = self.material()
        c, _ = prep(raw, "教育費の支出済額は300円でした。")
        self.assertEqual(E.bind(c[0], raw)["state"], "UNVERIFIABLE")

    def test_no_normalization_is_added_to_item_names(self):
        """科目名には正規化を足さない(封 §2)。"""
        ents = [entry("教育費", "一般会計", "支出済額", 1)]
        al = E.alias_table(ents + [entry("都教育費", "都教育費", "支出済額", 1,
                                         file="事項別明細")])
        self.assertEqual(al["table"], {})


class F5LongestSubjectTest(unittest.TestCase):
    """F-5 主語も最長一致(C-5)。"""

    ENTS = [entry("産業労働費", "一般会計", "支出済額", 628635837776),
            entry("労働費", "一般会計", "支出済額", 55485800000)]

    def test_the_longer_name_wins_at_the_same_place(self):
        c, _ = prep(self.ENTS, "産業労働費が628,635,837,776円であった。")
        self.assertEqual(c[0]["subject"], "産業労働費")

    def test_the_short_name_on_its_own_is_still_found(self):
        c, _ = prep(self.ENTS, "労働費が55,485,800,000円であった。")
        self.assertEqual(c[0]["subject"], "労働費")

    def test_it_binds_to_the_longer_name_cell(self):
        c, _ = prep(self.ENTS, "産業労働費の支出済額が628,635,837,776円であった。")
        b = E.bind(c[0], self.ENTS)
        self.assertEqual((b["state"], b["evidence"]["name"]), ("GROUNDED", "産業労働費"))


class F6PrefixCueTest(unittest.TestCase):
    """F-6 列名の曖昧でない接頭辞(2 文字以上)だけを足す。"""

    ENTS = [entry("公債費会計", "公債費会計", c, v, level="会計", file="総括")
            for c, v in (("歳入決算額", 1), ("歳出決算額", 2))]

    def test_an_unambiguous_prefix_maps_to_its_column(self):
        cues = E.column_cues(self.ENTS)
        self.assertEqual(cues["歳入"], "歳入決算額")
        self.assertEqual(cues["歳出"], "歳出決算額")

    def test_an_ambiguous_prefix_is_not_added(self):
        """`歳` は 2 つの列に当たるので足さない。"""
        cues = E.column_cues(self.ENTS)
        self.assertNotIn("歳", cues)

    def test_a_one_character_prefix_is_never_added(self):
        ents = [entry("議会費", "一般会計", "支出済額", 1)]
        self.assertNotIn("支", E.column_cues(ents))

    def test_the_cues_come_from_the_material_not_a_hand_list(self):
        ents = [entry("議会費", "一般会計", "謎の列", 1)]
        self.assertIn("謎の列", E.column_cues(ents).values())


class ParenScopeTest(unittest.TestCase):
    """括弧の中の手がかりを外に持ち出さない(封 §4 の検出条件)。"""

    ENTS = ([entry(n, "一般会計", "支出済額", v) for n, v in
             (("福祉費", 1066495914576), ("教育費", 973444990806), ("警察費", 654782736144))]
            + [entry("福祉費", "一般会計", "予算現額", 1145795413000),
               entry("福祉費", "一般会計", "不用額", 63616907424)])
    TEXT = ("款別の支出済額では、福祉費が1,066,495,914,576円"
            "(予算現額1,145,795,413,000円、不用額63,616,907,424円)、"
            "教育費が973,444,990,806円、警察費が654,782,736,144円であった")

    def test_the_columns_are_assigned_per_depth(self):
        c, _ = prep(self.ENTS, self.TEXT)
        got = [(x["subject"], x["column"], x["paren_depth"]) for x in c]
        self.assertEqual(got, [("福祉費", "支出済額", 0),
                               ("福祉費", "予算現額", 1),
                               ("福祉費", "不用額", 1),
                               ("教育費", "支出済額", 0),
                               ("警察費", "支出済額", 0)])

    def test_the_cue_inside_the_paren_does_not_leak_outside(self):
        c, _ = prep(self.ENTS, self.TEXT)
        self.assertEqual(c[3]["column"], "支出済額")   # 不用額 を引き継がない

    def test_all_five_bind(self):
        c, _ = prep(self.ENTS, self.TEXT)
        for x in c:
            self.assertEqual(E.bind(x, self.ENTS)["state"], "GROUNDED",
                             "%s %s" % (x["subject"], x["column"]))


class UnchangedRulesTest(unittest.TestCase):
    """**変えていないこと**を門にする(封 §2「変えない」)。"""

    def test_the_band_is_still_one_written_unit(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4950000000)]
        c, _ = prep(ents, "議会費の支出済額は48億円です。")
        self.assertEqual(E.bind(c[0], ents)["state"], "VALUE_MISMATCH")

    def test_the_band_still_accepts_within_one_unit(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4890000000)]
        c, _ = prep(ents, "議会費の支出済額は48億円です。")
        b = E.bind(c[0], ents)
        self.assertEqual((b["state"], b["route"]), ("GROUNDED", "R-4"))

    def test_a_value_only_hit_is_still_never_grounded(self):
        ents = [entry("議会費", "一般会計", "支出済額", 777)]
        c, _ = prep(ents, "知らない名前は777円です。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertTrue(b["value_match"])
        self.assertIsNone(b["route"])

    def test_r3_still_only_fires_when_no_cell_matches(self):
        kids = [{"name": "a", "value": 3, "value_ref": "D12"},
                {"name": "b", "value": 4, "value_ref": "D15"}]
        ents = [entry("議会費", "一般会計", "支出済額", 99, children=kids)]
        c, _ = prep(ents, "議会費の支出済額は7円です。")
        b = E.bind(c[0], ents)
        self.assertEqual((b["route"], b["state"]), ("R-3", "GROUNDED"))
        self.assertEqual(b["evidence"]["included"], ["D12", "D15"])

    def test_r1_still_wins_over_r3(self):
        kids = [{"name": "a", "value": 3, "value_ref": "D12"},
                {"name": "b", "value": 4, "value_ref": "D15"}]
        ents = [entry("議会費", "一般会計", "支出済額", 7, children=kids)]
        c, _ = prep(ents, "議会費の支出済額は7円です。")
        self.assertEqual(E.bind(c[0], ents)["route"], "R-1")

    def test_a_number_that_is_not_money_is_still_ignored(self):
        ents = [entry("議会費", "一般会計", "支出済額", 1)]
        self.assertEqual(prep(ents, "一般会計の款は37件あります。")[0], [])

    def test_the_four_states_are_the_only_ones_used(self):
        self.assertEqual(
            {"GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE"},
            {"GROUNDED", "VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE"})


class DuplicateDisagreementTest(unittest.TestCase):
    """同じ 4 欄で file 間の値が食い違ったら**どちらも採らない**(F-3 に足した規則)。"""

    def test_a_cross_file_disagreement_holds(self):
        ents = [entry("教育費", "一般会計", "支出済額", 99, ref="D20", file="決算書 歳出"),
                entry("教育費", "一般会計", "支出済額", 98, ref="F30", file="事項別明細")]
        c, _ = prep(ents, "教育費の支出済額は99円でした。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("file 間で食い違う", b["hold_reason"])
        self.assertIsNone(b["route"])

    def test_the_file_order_decides_the_pointer_not_the_input_order(self):
        """明細を先に並べても、採るのは先に決めた順(決算書)。"""
        ents = [entry("教育費", "一般会計", "支出済額", 99, ref="F30", file="事項別明細"),
                entry("教育費", "一般会計", "支出済額", 99, ref="D20", file="決算書 歳出")]
        c, _ = prep(ents, "教育費の支出済額は99円でした。")
        self.assertEqual(E.bind(c[0], ents)["pointer"], "sheet:決算書 歳出!D20")


class AmbiguousPrefixTest(unittest.TestCase):
    """F-6 の曖昧さの判定を**実際に曖昧な接頭辞**で当てる。"""

    ENTS = [entry("議会費", "一般会計", c, v)
            for c, v in (("歳入決算額", 1), ("歳入見込額", 2), ("支出済額", 3))]

    def test_a_prefix_shared_by_two_columns_is_not_added(self):
        cues = E.column_cues(self.ENTS)
        self.assertNotIn("歳入", cues)        # 2 つの列に当たるので使わない
        # `歳入決` は 1 つの列にしか当たらないので足してよい(曖昧なのは `歳入` だけ)
        self.assertEqual(cues["歳入決"], "歳入決算額")

    def test_the_unambiguous_prefix_of_a_third_column_is_still_added(self):
        self.assertEqual(E.column_cues(self.ENTS)["支出"], "支出済額")

    def test_an_ambiguous_prefix_leaves_the_column_unset(self):
        c, _ = prep(self.ENTS, "議会費は歳入1円です。")
        self.assertIsNone(c[0]["column"])


class PrefixExtensionAliasTest(unittest.TestCase):
    """F-4 長い名前が正本で**始まる**だけなら別名にしない(前方一致の禁止)。"""

    def material(self, meisai_scope):
        return [entry("一般会計", "一般会計", "歳入決算額", 1000, level="会計", file="総括"),
                entry("教育費", "一般会計", "支出済額", 300, file="決算書 歳出"),
                entry("福祉費", "一般会計", "支出済額", 700, file="決算書 歳出"),
                entry("教育費", meisai_scope, "支出済額", 300, file="事項別明細"),
                entry("福祉費", meisai_scope, "支出済額", 700, file="事項別明細")]

    def test_a_name_that_only_starts_with_the_canonical_name_is_not_an_alias(self):
        """値が全部一致していても結ばない。**接尾でなければ別名ではない。**"""
        al = E.alias_table(self.material("一般会計特別分"))
        self.assertNotIn("一般会計特別分", al["table"])
        self.assertIn("接尾一致が 0 件", al["unconfirmed"][0]["why"])

    def test_the_suffix_direction_is_still_an_alias(self):
        al = E.alias_table(self.material("東京都一般会計"))
        self.assertIn("東京都一般会計", al["table"])

    def test_an_item_level_name_is_never_a_canonical_target(self):
        """`公債費`(款)を `公債費会計`(会計)の別名にしない。"""
        ents = [entry("公債費会計", "公債費会計", "歳入決算額", 10, level="会計", file="総括"),
                entry("公債費", "公債費会計", "支出済額", 10, file="決算書 歳出"),
                entry("公債費", "公債費", "支出済額", 10, file="事項別明細")]
        al = E.alias_table(ents)
        self.assertEqual(al["table"], {})
        self.assertNotIn("公債費", [r["name"] for r in al["unconfirmed"]
                                    if r.get("canonical") == "公債費会計"])


class EquivalenceTest(unittest.TestCase):
    """**黙った変異のうち、等価だと証明できたもの**を固定する(封の規律)。

    N1(列を `max`/`min` で選ぶ)と N9(主語を開始位置/終了位置で選ぶ)は
    黙ったが、untested path ではなく**等価**である。等価の理由を試験で押さえる。
    """

    def test_a_span_never_holds_two_different_columns(self):
        """列は区間に 1 種類しか残らない(2 種類あれば保留に落ちる)ので位置比較は無意味。"""
        ents = [entry("議会費", "一般会計", c, v)
                for c, v in (("歳入決算額", 1), ("歳出決算額", 2))]
        c, _ = prep(ents, "議会費は歳入決算額が1円、歳出決算額が2円です。")
        for x in c:
            self.assertIsNone(x["column_ambiguous"], x["id"])
        c2, _ = prep(ents, "議会費は歳入決算額と歳出決算額で3円です。")
        self.assertEqual(c2[0]["column_ambiguous"], ["歳入決算額", "歳出決算額"])

    def test_maximal_hits_never_partially_overlap(self):
        """最長一致の後に残る当たりは、開始順と終了順が一致する(N9 が等価な理由)。"""
        words = {"産業労働費", "労働費", "教育費", "一般会計"}
        hits = E._maximal(E._hits("一般会計の産業労働費と教育費", words))
        by_start = [w for _, _, w in sorted(hits, key=lambda h: h[0])]
        by_end = [w for _, _, w in sorted(hits, key=lambda h: h[1])]
        self.assertEqual(by_start, by_end)
        self.assertNotIn("労働費", by_start)


if __name__ == "__main__":
    unittest.main()
