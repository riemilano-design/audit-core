# -*- coding: utf-8 -*-
"""方式 C の凍結器と採点器を固定する(**生成の前に commit する門**)。

  * 費用の式は**席ごとの単価**を使う(sonnet 15 / haiku 5)。**2 席の合計で 4 USD**
  * 検査は**段 11 の `check()` そのもの**(C 用に緩めていない)
  * 採点器は**A / B のものを import する**。C 用に `same_row` 等を定義し直していない
  * 判定は**封 §4-2 の順**。**検出だけ増えても誤接続 / 回収が悪化したら改善と書かない**
"""
import ast
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")


def _mod(name, rel):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


F = _mod("c_freeze_for_test", "sheet_poc_c_freeze_answers_2026-10-17.py")
SC = _mod("c_score_for_test", "sheet_poc_c_score_2026-10-17.py")


def src(rel):
    with io.open(os.path.join(MEASURE, rel), encoding="utf-8") as fh:
        return fh.read()


class CostTest(unittest.TestCase):
    def test_1_rates_are_per_seat_and_pinned(self):
        self.assertEqual(F.USD_PER_M_OUTPUT, {"seat1": 15.0, "seat2": 5.0})
        self.assertEqual(F.CAP_USD, 4.0)

    def test_2_upper_bound_uses_the_seats_rate(self):
        a = F.cost_upper_bound("seat1", 1000000)
        b = F.cost_upper_bound("seat2", 1000000)
        self.assertEqual(a["費用の上限(全部が出力だと仮定)"], 15.0)
        self.assertEqual(b["費用の上限(全部が出力だと仮定)"], 5.0)
        self.assertEqual(a["使ったトークン(実測)"], 1000000)

    def test_3_the_cap_is_on_the_total_of_both_seats(self):
        """**片側だけ見ると上限をすり抜ける。**合計で見ていることを当てる。"""
        t = F.running_total("seat1", 3.5)
        self.assertEqual(t["人間が決めた上限"], 4.0)
        self.assertIn("2 席の合計の上限", t)
        self.assertEqual(t["2 席の合計の上限"], round(3.5 + t["もう 1 席の上限"], 4))
        self.assertEqual(t["上限の中か"], t["2 席の合計の上限"] <= 4.0)

    def test_4_the_check_is_stage_11s_not_a_loosened_copy(self):
        lab = _mod("fr11_for_test", "sheet_m11_freeze_answers_2026-10-16.py")
        # **module は呼ぶたびに別の実体になる。だから「どの file で定義されたか」で見る**
        self.assertTrue(F.check.__code__.co_filename.endswith(
            "sheet_m11_freeze_answers_2026-10-16.py"),
            "**検査が段 11 の file のものでない**")
        self.assertEqual(F.FIELDS, lab.FIELDS)
        t = src("sheet_poc_c_freeze_answers_2026-10-17.py")
        tree = ast.parse(t)
        names = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
        self.assertNotIn("check", names, "**検査を書き直してはいけない**")


class GraderIsImportedTest(unittest.TestCase):
    def test_5_no_private_comparator_in_the_c_scorer(self):
        tree = ast.parse(src("sheet_poc_c_score_2026-10-17.py"))
        names = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
        for forbidden in ("score_arm", "same_row", "resolve", "col_match",
                          "scope_match", "answer_of_seat", "answer_of_core",
                          "reach"):
            self.assertNotIn(forbidden, names,
                             "**C 用に書き直してはいけない: %s**" % forbidden)

    def test_6_the_imported_functions_are_the_ab_ones(self):
        want = "sheet_poc_ab_score_2026-10-17.py"
        for f in (SC.S.score_arm, SC.S.same_row, SC.S.resolve,
                  SC.S.col_match, SC.S.scope_match):
            self.assertTrue(f.__code__.co_filename.endswith(want),
                            "**%s が A / B の file のものでない**" % f.__name__)
        self.assertTrue(SC.A3.reach.__code__.co_filename.endswith(
            "sheet_poc_m3_addendum_2026-10-17.py"))

    def test_7_pairs_are_by_model(self):
        self.assertEqual(SC.PAIRS, ((SC.C1, SC.A1), (SC.C2, SC.A2)))
        self.assertIn("sonnet", SC.C1)
        self.assertIn("sonnet", SC.A1)
        self.assertIn("haiku", SC.C2)
        self.assertIn("haiku", SC.A2)

    def test_8_core_row_is_none_unless_the_tool_connected(self):
        self.assertIsNone(SC.core_row({"state": "UNVERIFIABLE",
                                       "evidence": None}))
        r = SC.core_row({"state": "GROUNDED",
                         "evidence": {"scope": "一般会計", "level": "項",
                                      "parent": "総務費", "name": "x",
                                      "column": "支出済額", "value": 7}})
        self.assertEqual(r["会計(印字)"], "一般会計")
        self.assertEqual(r["値"], 7)


class VerdictOrderTest(unittest.TestCase):
    """封 §4-2 の**判定の順**を 1 本ずつ当てる(**5 つの枝を全部**)。"""

    @staticmethod
    def _p(wrong, recall, detect):
        return {("C", "A"): {"誤接続の差": wrong, "回収の差": recall,
                             "検出の差": detect}}

    def test_9_more_wrong_links_is_never_improvement(self):
        v = SC.verdict(self._p(1, 0, 5))[0]["判定"]
        self.assertIn("悪化(誤接続が増えた)", v)
        self.assertIn("相殺しない", v)

    def test_10_recall_drop_with_detection_is_a_tradeoff_not_improvement(self):
        v = SC.verdict(self._p(0, -3, 1))[0]["判定"]
        self.assertIn("代価つきの変化", v)
        self.assertIn("改善とは書かない", v)

    def test_11_recall_drop_alone_is_worse(self):
        self.assertIn("悪化(回収が落ちた)", SC.verdict(self._p(0, -1, 0))[0]["判定"])

    def test_12_improvement_needs_all_three(self):
        self.assertIn("改善", SC.verdict(self._p(0, 0, 1))[0]["判定"])

    def test_13_no_difference_is_written_as_no_difference(self):
        self.assertIn("差が出なかった", SC.verdict(self._p(0, 0, 0))[0]["判定"])


class ReproducesATest(unittest.TestCase):
    def test_14_a_doctored_number_stops_the_scoring(self):
        """**A を採り直して記録と一致しなければ採点を書かない。**"""
        import json
        rec = json.load(io.open(os.path.join(ROOT, "fixtures", "sheet",
                                             "poc_ab_score_2026-10-17.json"),
                                encoding="utf-8"))
        res = {}
        for name in (SC.A1, SC.A2, SC.B):
            v = rec["主採点(寛容な会計)"][name]
            res[name] = {m: v[m] for m in ("M-1 誤接続率", "M-2 回収率",
                                           "M-3 根拠の再現性", "正解集合")}
        self.assertTrue(SC.check_a_reproduces(res))
        res[SC.A1]["M-2 回収率"] = {"num": 23, "den": 24, "rate": 23 / 24.0}
        with self.assertRaises(SystemExit):
            SC.check_a_reproduces(res)


if __name__ == "__main__":
    unittest.main()
