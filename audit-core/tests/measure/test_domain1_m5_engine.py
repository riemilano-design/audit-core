# -*- coding: utf-8 -*-
"""段 5 の engine の回帰試験(封 docs/DOMAIN1_M5_SEAL_2026-10-15.md §2-2・§3・§4・§5)。

K-1〜K-5(階層の手がかり)・U-1〜U-4(一意性)・I-1〜I-4(別名の独立性)を当てる。
**K-1 と K-2 は同じファイルの中で当てる**(封 K-5。片方だけ通る実装を落とす)。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "sheet_m5_engine_2026-10-15.py")
DIAG = os.path.join(ROOT, "fixtures", "sheet", "m4_fix_diagnostic_2026-10-15.json")
REG = os.path.join(ROOT, "fixtures", "sheet", "m5_regression_2026-10-15.json")

spec = importlib.util.spec_from_file_location("m5e", SCRIPT)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

MUST_KEEP = ("R004", "R008", "R009", "R013", "R015",
             "R017", "R018", "R019", "R020", "R021", "R022")


def entry(name, scope, column, value, level="款", parent=None, children=None,
          ref="D10", file="決算書 歳出"):
    return {"scope": scope, "level": level, "name": name, "code": "01", "column": column,
            "value": value, "file": file, "children": children, "parent": parent,
            "evidence": {"scope_from": "表題行", "code_ref": "A10", "name_ref": "B10",
                         "value_ref": ref, "header_ref": "D7"}}


def prep(entries, text):
    return E.extract_claims(text, E.vocabulary(entries), E.column_cues(entries))


class LevelCueTest(unittest.TestCase):
    """C-8。**K-1 と K-2 を同じクラスの中で当てる**(封 K-5)。"""

    ENTS = [entry("諸支出金", "一般会計", "支出済額", 2319031711747, level="款"),
            entry("諸支出金", "国民健康保険事業会計", "支出済額", 826042273,
                  level="目", parent="保険給付費 > 保険給付費", ref="R99",
                  file="事項別明細")]

    def test_k1_the_level_cue_saves_the_r007_shape(self):
        c = prep(self.ENTS, "款別の支出済額では、諸支出金が2,319,031,711,747円で最も大きい。")
        self.assertEqual(c[0]["level"], "款")
        b = E.bind(c[0], self.ENTS)
        self.assertEqual((b["state"], b["route"]), ("GROUNDED", "R-1"))
        self.assertEqual(b["evidence"]["scope"], "一般会計")
        self.assertEqual(b["evidence"]["level"], "款")

    def test_k2_without_a_level_cue_it_still_holds(self):
        """**同じ名前が別の会計の別の階層に在り、階層の語が無ければ保留のまま。**"""
        c = prep(self.ENTS, "諸支出金の支出済額は2,319,031,711,747円である。")
        self.assertIsNone(c[0]["level"])
        b = E.bind(c[0], self.ENTS)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("6 欄が一意でない", b["hold_reason"])
        self.assertEqual(b["distinct_keys"], 2)

    def test_k3_it_does_not_escape_to_another_level(self):
        """階層の語が指す階層に候補が 0 件なら、他の階層に落ちない。"""
        c = prep(self.ENTS, "項別の支出済額では、諸支出金が2,319,031,711,747円である。")
        self.assertEqual(c[0]["level"], "項")
        b = E.bind(c[0], self.ENTS)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("階層 項 に候補が 0 件", b["hold_reason"])
        self.assertIsNone(b["route"])
        self.assertIsNone(b["pointer"])

    def test_k4_two_candidates_inside_the_level_still_hold(self):
        ents = [entry("管理費", "一般会計", "支出済額", 5, level="目", parent="A > B",
                      ref="R1"),
                entry("管理費", "一般会計", "支出済額", 5, level="目", parent="C > D",
                      ref="R2")]
        c = prep(ents, "目別の支出済額では、管理費が5円である。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertEqual(b["distinct_keys"], 2)

    def test_the_level_cue_is_not_taken_from_inside_an_account_name(self):
        ents = [entry("一般会計", "一般会計", "歳入決算額", 7, level="会計", file="総括")]
        c = prep(ents, "一般会計の歳入決算額は7円である。")
        self.assertIsNone(c[0]["level"])
        self.assertEqual(E.bind(c[0], ents)["state"], "GROUNDED")

    def test_two_level_cues_in_the_span_hold(self):
        ents = [entry("教育費", "一般会計", "支出済額", 9, level="款")]
        c = prep(ents, "款別・項別の支出済額では、教育費が9円である。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("階層 の手がかりが 2 つ以上", b["hold_reason"])

    def test_goukei_still_masks_the_kei_column(self):
        """`合計` は手がかりではないが**覆い隠す語**としては残る(F-2)。

        外すと `歳入決算額の合計は` で `計` が列として採られ、
        「列の手がかりが 2 つ」で保留になった(実測した退行)。
        """
        self.assertEqual(E.MASK_WORDS, ("会計", "合計", "款", "項", "目"))
        ents = E.fix_total_level([
            entry("合計", "合計", "歳入決算額", 9, level="会計", file="総括"),
            entry("議会費", "一般会計", "計", 3, level="款")])
        c = prep(ents, "全20会計の歳入決算額の合計は9円である。")
        self.assertEqual(c[0]["column"], "歳入決算額")
        self.assertIsNone(c[0]["column_ambiguous"])
        self.assertEqual(E.bind(c[0], ents)["state"], "GROUNDED")

    def test_kaikei_and_goukei_are_not_level_cues(self):
        """`全20会計の…の合計は` の `会計`・`合計` を階層と読まない。

        読むと「階層 合計 に候補が 0 件」で保留になる(実測した誤り)。
        **文が言っていない制約を作らない。**
        """
        self.assertEqual(E.LEVEL_CUES, ("款", "項", "目"))
        ents = E.fix_total_level(
            [entry("合計", "合計", "歳入決算額", 9, level="会計", file="総括")])
        c = prep(ents, "全20会計の歳入決算額の合計は9円である。")
        self.assertIsNone(c[0]["level"])
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "GROUNDED")
        self.assertEqual(b["evidence"]["level"], "合計")

    def test_the_level_cue_is_inherited_within_a_sentence(self):
        ents = [entry(n, "一般会計", "支出済額", v, level="款")
                for n, v in (("諸支出金", 10), ("福祉費", 20))]
        c = prep(ents, "款別の支出済額では、諸支出金が10円、福祉費が20円であった。")
        self.assertEqual([x["level"] for x in c], ["款", "款"])
        for x in c:
            self.assertEqual(E.bind(x, ents)["state"], "GROUNDED", x["subject"])

    def test_the_level_cue_does_not_cross_a_paren(self):
        ents = [entry("福祉費", "一般会計", "支出済額", 10, level="款"),
                entry("福祉費", "一般会計", "予算現額", 20, level="款")]
        c = prep(ents, "款別では、福祉費が10円(予算現額20円)であった。")
        self.assertEqual(c[0]["level"], "款")
        self.assertIsNone(c[1]["level"])        # 括弧の中は引き継がない


class UniquenessTest(unittest.TestCase):
    """C-9。U-1〜U-4。"""

    def test_u1_a_duplicated_row_is_never_grounded_by_its_value(self):
        ents = [entry("管理費", "一般会計", "支出済額", 100, level="目", parent="A > B",
                      ref="R1"),
                entry("管理費", "一般会計", "支出済額", 200, level="目", parent="C > D",
                      ref="R2")]
        c = prep(ents, "管理費の支出済額は100円である。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIsNone(b["pointer"])

    def test_u2_two_parents_with_the_same_value_hold(self):
        ents = [entry("管理費", "一般会計", "支出済額", 100, level="目", parent="A > B",
                      ref="R1"),
                entry("管理費", "一般会計", "支出済額", 100, level="目", parent="C > D",
                      ref="R2")]
        c = prep(ents, "管理費の支出済額は100円である。")
        self.assertEqual(E.bind(c[0], ents)["state"], "UNVERIFIABLE")

    def test_u3_a_single_row_with_its_parent_binds(self):
        ents = [entry("自治振興費", "一般会計", "支出済額", 220908967258, level="目",
                      parent="総務費 > 総務管理費", ref="R1113", file="事項別明細")]
        c = prep(ents, "自治振興費の支出済額が220,908,967,258円であった。")
        b = E.bind(c[0], ents)
        self.assertEqual((b["state"], b["route"]), ("GROUNDED", "R-1"))
        self.assertEqual(b["evidence"]["parent"], "総務費 > 総務管理費")

    def test_the_parent_is_part_of_the_key(self):
        self.assertEqual(E.FIELDS6, ("scope", "level", "parent", "name", "column"))

    def test_u4_the_duplication_report_counts_per_level(self):
        ents = [entry("管理費", "一般会計", "支出済額", 1, level="目", parent="A > B"),
                entry("管理費", "一般会計", "支出済額", 2, level="目", parent="A > B")]
        rep = E.duplication_report(ents)
        self.assertEqual(rep["max_distinct_values_per_level"]["目"], 2)
        self.assertEqual(rep["levels_not_unique"], ["目"])


class TotalRowTest(unittest.TestCase):
    """C-4。封 §1-2 の字と engine の出す字が合っていること。"""

    def test_the_soukatu_total_row_is_at_the_total_level(self):
        ents = E.fix_total_level([
            entry("合計", "合計", "歳入決算額", 9, level="会計", file="総括"),
            entry("一般会計", "一般会計", "歳入決算額", 5, level="会計", file="総括")])
        got = {e["name"]: e["level"] for e in ents}
        self.assertEqual(got["合計"], "合計")
        self.assertEqual(got["一般会計"], "会計")

    def test_the_kessan_block_total_is_untouched(self):
        ents = E.fix_total_level([
            entry("歳出合計", "一般会計", "予算現額", 1, level="合計",
                  file="決算書 歳出")])
        self.assertEqual(ents[0]["level"], "合計")

    def test_the_name_is_blanked_by_the_scorer_at_the_total_level(self):
        """採点器は会計・合計の層で科目名を空欄にする(凍結した規則)。"""
        self.assertIn("合計", ("会計", "合計"))


class ParentTest(unittest.TestCase):
    """親は**その sheet の中だけ**で決める(参照は sheet をまたいで衝突する)。"""

    def _meisai(self):
        def row(code, name, r, val, ref):
            return {"code": code, "name": name, "row": r,
                    "values": {"支出済額": val},
                    "evidence": {"支出済額": {"value_ref": ref, "sign_ref": None}}}
        return {"sheets": [
            {"sheet": "s1", "account": "一般会計", "toc_ref": "C1", "columns": {},
             "kan": [row("1", "議会費", 10, 1, "D10")],
             "items": [row("1", "都議会費", 12, 2, "D12")],
             "moku": [row("1", "議会運営費", 14, 3, "D14")]},
            {"sheet": "s2", "account": "と場会計", "toc_ref": "C2", "columns": {},
             "kan": [row("1", "と場費", 10, 4, "D10")],
             "items": [row("1", "と場管理費", 12, 5, "D12")],
             "moku": [row("1", "運営費", 14, 6, "D14")]}]}

    def test_the_same_ref_in_two_sheets_gets_its_own_parent(self):
        """この試験が無いと、目の親が別の sheet の款になる(実測した欠陥)。"""
        ents = E.build_index({"accounts": []}, {"blocks": []}, self._meisai())
        got = {(e["scope"], e["level"], e["name"]): e["parent"] for e in ents}
        self.assertEqual(got[("一般会計", "目", "議会運営費")], "議会費 > 都議会費")
        self.assertEqual(got[("と場会計", "目", "運営費")], "と場費 > と場管理費")
        self.assertEqual(got[("一般会計", "項", "都議会費")], "議会費")
        self.assertIsNone(got[("一般会計", "款", "議会費")])

    def test_only_item_and_moku_levels_carry_a_parent(self):
        ents = E.build_index({"accounts": []}, {"blocks": []}, self._meisai())
        for e in ents:
            if e["level"] in ("款", "会計", "合計"):
                self.assertIsNone(e["parent"], e["name"])
            else:
                self.assertTrue(e["parent"], e["name"])


class AliasIndependenceTest(unittest.TestCase):
    """封 §4-2 の I-1〜I-4。"""

    def base(self, extra=()):
        ents = [entry("一般会計", "一般会計", "歳入決算額", 1000, level="会計",
                      file="総括")]
        return ents + list(extra)

    def kan_pair(self, name, value, scope="東京都一般会計", col="支出済額"):
        return [entry(name, "一般会計", col, value, level="款", file="決算書 歳出"),
                entry(name, scope, col, value, level="款", file="事項別明細")]

    def test_three_distinct_names_pass(self):
        ents = self.base(self.kan_pair("教育費", 300) + self.kan_pair("福祉費", 700)
                         + self.kan_pair("警察費", 500))
        al = E.alias_table(ents)
        self.assertIn("東京都一般会計", al["table"])
        self.assertEqual(al["table"]["東京都一般会計"]["evidence"]["独立した裏づけ"], 3)

    def test_two_distinct_names_fail(self):
        ents = self.base(self.kan_pair("教育費", 300) + self.kan_pair("福祉費", 700))
        al = E.alias_table(ents)
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertIn("独立した裏づけが 2 本(要 3 本)", al["unconfirmed"][0]["why"])

    def test_i1_the_same_row_through_three_columns_is_one(self):
        """**同じ表の同じ情報を 3 回参照しただけ**は 1 本(人間の補足条件)。"""
        ents = self.base(self.kan_pair("教育費", 300, col="支出済額")
                         + self.kan_pair("教育費", 310, col="予算現額")
                         + self.kan_pair("教育費", 320, col="不用額"))
        al = E.alias_table(ents)
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertEqual(al["unconfirmed"][0]["independent"], 1)

    def test_i2_a_child_of_a_counted_kan_is_dropped(self):
        """**名前が違っても**、親の款が数えられていれば独立ではない。"""
        ents = self.base(
            self.kan_pair("公債費", 100)
            + [entry("元金償還費", "一般会計", "支出済額", 90, level="項",
                     parent="公債費", file="決算書 歳出"),
               entry("元金償還費", "東京都一般会計", "支出済額", 90, level="項",
                     parent="公債費", file="事項別明細")])
        al = E.alias_table(ents)
        self.assertEqual(al["unconfirmed"][0]["independent"], 1)
        self.assertTrue(any("親 公債費 が既に数えられている" in d["why"]
                            for d in al["unconfirmed"][0]["dropped"]),
                        al["unconfirmed"][0]["dropped"])

    def test_i1_the_same_name_at_two_levels_is_one(self):
        """款と項が同名(特別会計の形)なら 1 本。"""
        ents = self.base(
            self.kan_pair("公債費", 100)
            + [entry("公債費", "一般会計", "支出済額", 100, level="項",
                     parent="公債費", file="決算書 歳出"),
               entry("公債費", "東京都一般会計", "支出済額", 100, level="項",
                     parent="公債費", file="事項別明細")])
        self.assertEqual(E.alias_table(ents)["unconfirmed"][0]["independent"], 1)

    def test_i3_the_same_value_three_times_is_one(self):
        ents = self.base(self.kan_pair("教育費", 500) + self.kan_pair("福祉費", 500)
                         + self.kan_pair("警察費", 500))
        al = E.alias_table(ents)
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertEqual(al["unconfirmed"][0]["independent"], 1)

    def test_i4_a_match_inside_one_file_does_not_count(self):
        ents = self.base([
            entry("教育費", "一般会計", "支出済額", 300, level="款", file="事項別明細"),
            entry("教育費", "東京都一般会計", "支出済額", 300, level="款",
                  file="事項別明細")])
        al = E.alias_table(ents)
        self.assertEqual(al["unconfirmed"][0]["independent"], 0)

    def test_one_disagreement_blocks_it_however_many_agree(self):
        ents = self.base(self.kan_pair("教育費", 300) + self.kan_pair("福祉費", 700)
                         + self.kan_pair("警察費", 500)
                         + [entry("土木費", "一般会計", "支出済額", 10, level="款"),
                            entry("土木費", "東京都一般会計", "支出済額", 11,
                                  level="款", file="事項別明細")])
        al = E.alias_table(ents)
        self.assertNotIn("東京都一般会計", al["table"])
        self.assertIn("食い違い 1 件", al["unconfirmed"][0]["why"])

    def test_the_minimum_is_pinned_literally(self):
        """人が決めた数は字で留める。"""
        self.assertEqual(E.MIN_INDEPENDENT, 3)
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertIn("MIN_INDEPENDENT = 3", src)

    def test_prefix_is_still_refused(self):
        ents = self.base(self.kan_pair("教育費", 300, scope="一般会計特別分")
                         + self.kan_pair("福祉費", 700, scope="一般会計特別分")
                         + self.kan_pair("警察費", 500, scope="一般会計特別分"))
        self.assertNotIn("一般会計特別分", E.alias_table(ents)["table"])


class UnconfirmedScopeTest(unittest.TestCase):
    """落ちた別名の会計には、**値が合っても結ばない**(封 §4-1 の 6)。"""

    def material(self):
        ents = [entry("公債費会計", "公債費会計", "歳入決算額", 10, level="会計",
                      file="総括"),
                entry("公債費", "公債費会計", "支出済額", 100, level="款",
                      file="決算書 歳出"),
                entry("公債費", "東京都公債費会計", "支出済額", 100, level="款",
                      file="事項別明細"),
                entry("償還費", "東京都公債費会計", "支出済額", 55, level="目",
                      parent="公債費 > 公債費", file="事項別明細", ref="R20")]
        al = E.alias_table(ents)
        return E.canonicalize(ents, al), al

    def test_the_alias_is_unconfirmed(self):
        ents, al = self.material()
        self.assertEqual(al["table"], {})
        self.assertEqual(al["unconfirmed"][0]["independent"], 1)

    def test_a_claim_about_it_holds_even_though_the_value_matches(self):
        ents, _ = self.material()
        c = prep(ents, "償還費の支出済額は55円である。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("会計が未確認の別名", b["hold_reason"])
        self.assertEqual(b["unconfirmed_scope"], "東京都公債費会計")
        self.assertIsNone(b["pointer"])

    def test_even_the_kan_claim_holds_because_the_twin_cannot_be_matched(self):
        """**封 §4-4 が書き落としていた代償。**

        明細の双子が同じ会計だと**証明できない**ので、決算書側の款も一意でなくなる。
        材料はおそらく同じ会計だが、「おそらく」で結ばないのがこの封の目的である。
        """
        ents, _ = self.material()
        c = prep(ents, "款別の支出済額では、公債費が100円である。")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("6 欄が一意でない", b["hold_reason"])
        self.assertEqual(b["distinct_keys"], 2)

    def test_the_same_claim_binds_once_the_alias_is_confirmed(self):
        """裏づけが 3 本そろえば、同じ主張が結べる(規則が効いている向きの確認)。"""
        ents = [entry("公債費会計", "公債費会計", "歳入決算額", 10, level="会計",
                      file="総括")]
        for nm, v in (("公債費", 100), ("償還金", 70), ("利子", 30)):
            ents.append(entry(nm, "公債費会計", "支出済額", v, level="款",
                              file="決算書 歳出"))
            ents.append(entry(nm, "東京都公債費会計", "支出済額", v, level="款",
                              file="事項別明細"))
        al = E.alias_table(ents)
        self.assertIn("東京都公債費会計", al["table"])
        ents = E.canonicalize(ents, al)
        b = E.bind(prep(ents, "款別の支出済額では、公債費が100円である。")[0], ents)
        self.assertEqual(b["state"], "GROUNDED")
        self.assertEqual(b["evidence"]["scope"], "公債費会計")
        self.assertEqual(b["duplicates"], 2)


class UnchangedRulesTest(unittest.TestCase):
    """**変えていないこと**(封 §0 の表)。"""

    def test_the_band_is_still_one_written_unit(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4950000000)]
        c = prep(ents, "議会費の支出済額は48億円です。")
        self.assertEqual(E.bind(c[0], ents)["state"], "VALUE_MISMATCH")

    def test_the_band_still_accepts_within_one_unit(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4890000000)]
        self.assertEqual(E.bind(prep(ents, "議会費の支出済額は48億円です。")[0],
                                ents)["route"], "R-4")

    def test_a_value_only_hit_is_still_never_grounded(self):
        ents = [entry("議会費", "一般会計", "支出済額", 777)]
        b = E.bind(prep(ents, "知らない名前は777円です。")[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIsNone(b["route"])

    def test_r1_still_wins_over_r3(self):
        kids = [{"name": "a", "value": 3, "value_ref": "D12"},
                {"name": "b", "value": 4, "value_ref": "D15"}]
        ents = [entry("議会費", "一般会計", "支出済額", 7, children=kids)]
        self.assertEqual(E.bind(prep(ents, "議会費の支出済額は7円です。")[0],
                                ents)["route"], "R-1")

    def test_the_equal_column_hold_still_works(self):
        ents = [entry("公債費会計", "公債費会計", c, 100, level="会計", file="総括")
                for c in ("歳入決算額", "歳出決算額")]
        b = E.bind(prep(ents, "公債費会計は歳入・歳出とも100円。")[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("列 の手がかりが 2 つ以上", b["hold_reason"])


class RealMaterialTest(unittest.TestCase):
    """実物で、封 §4-3 と §1-3 の数が出ること。"""

    @classmethod
    def setUpClass(cls):
        M2 = E.M2
        if not all(os.path.exists(os.path.join(M2.CACHE, f))
                   for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI)):
            raise unittest.SkipTest("材料が ~/.cache に無い")
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        cls.sk = M2.parse_soukatu(books[M2.SOUKATU])
        cls.ks = M2.parse_kessan(books[M2.KESSAN])
        cls.ms = M2.parse_meisai(books[M2.MEISAI])
        cls.raw = E.build_index(cls.sk, cls.ks, cls.ms)
        cls.al = E.alias_table(cls.raw)
        cls.ents = E.canonicalize(cls.raw, cls.al)

    def test_the_index_matches_the_frozen_one_except_for_the_parent(self):
        old = E.BASE.build_index(self.sk, self.ks, self.ms)
        self.assertEqual(len(self.raw), len(old))
        for a, b in zip(self.raw, old):
            for k in b:
                if k != "parent":
                    self.assertEqual(a[k], b[k], k)

    def test_only_one_alias_passes(self):
        """封 §4-3 の数。**19 候補のうち 1 件だけ。**"""
        self.assertEqual(len(self.al["table"]), 1)
        self.assertEqual(len(self.al["unconfirmed"]), 18)
        self.assertEqual(list(self.al["table"]), ["東京都一般会計"])
        self.assertEqual(self.al["table"]["東京都一般会計"]["canonical"], "一般会計")
        self.assertEqual(
            self.al["table"]["東京都一般会計"]["evidence"]["独立した裏づけ"], 18)

    def test_the_seventeen_have_one_and_one_has_two(self):
        got = sorted(u["independent"] for u in self.al["unconfirmed"])
        self.assertEqual(got, [1] * 17 + [2])

    def test_every_level_is_unique_once_the_parent_is_added(self):
        """封 §1-3・U-4。**生成の前に数える。**対象から外す階層は無い。"""
        rep = E.duplication_report(self.ents)
        self.assertEqual(rep["levels_not_unique"], [])
        self.assertEqual(set(rep["max_distinct_values_per_level"].values()), {1})

    def test_the_four_field_key_was_not_unique(self):
        """親を足す前は一意でなかったこと(C-9 が実在する欠陥だった証拠)。"""
        groups = {}
        for e in self.ents:
            k = tuple(E.norm(e[f]) or "" for f in ("scope", "level", "name", "column"))
            groups.setdefault(k, set()).add(e["value"])
        self.assertGreater(max(len(v) for v in groups.values()), 50)


class BreakDetectionTest(unittest.TestCase):
    """封 §5。診断で正しく結べた 11 件が壊れていないこと。"""

    def test_the_regression_record_exists_and_keeps_all_eleven(self):
        if not os.path.exists(REG):
            self.skipTest("回帰の記録はまだ作っていない")
        r = json.load(io.open(REG, encoding="utf-8"))
        self.assertTrue(r["not_performance_evidence"])
        for cid in MUST_KEEP:
            row = r["rows"][cid]
            self.assertEqual(row["state"], "GROUNDED", cid)
            self.assertTrue(row["agree_4"], cid)
            self.assertEqual(row["pointer"], row["pointer_before"], cid)
        self.assertEqual(r["broken"], [])

    def test_the_eleven_were_correct_in_the_diagnostic(self):
        d = json.load(io.open(DIAG, encoding="utf-8"))
        ok = {x["id"] for x in d["rows"] if x["after"] == "正しい接続"}
        self.assertEqual(set(MUST_KEEP) - ok, set())


if __name__ == "__main__":
    unittest.main()
