# -*- coding: utf-8 -*-
"""A / C の問い・材料・凍結器・採点器を固定する(**生成の前に commit する門**)。

  * **段 11 の問いが接頭**で、足したのは「不一致の種類」の 1 欄だけ
  * 検査は**段 11 の `check()` そのもの**。足した欄は**貼り直す**(語彙外は `不明`)
  * 採点は **A / B の採点器と追記の `reach()` を import する**。書き直さない
  * **封が書いていなかった 2 点**(申告の境目・住所が無い答えの扱い)を
    **答えを見る前に**関数として固定した
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


Q = _mod("q_for_test", "sheet_errdet_question_2026-10-17.py")
F = _mod("freeze_for_test", "sheet_errdet_freeze_2026-10-17.py")
SC = _mod("score_for_test", "sheet_errdet_score_2026-10-17.py")


def src(rel):
    with io.open(os.path.join(MEASURE, rel), encoding="utf-8") as fh:
        return fh.read()


class QuestionTest(unittest.TestCase):
    def test_1_stage_11_question_is_a_prefix(self):
        q = Q.question_text()
        self.assertTrue(q.startswith(Q.base_question()))
        self.assertTrue(Q.check(q))
        self.assertGreater(len(q), len(Q.base_question()))

    def test_2_the_six_words_are_pinned(self):
        self.assertEqual(Q.VOCAB,
                         ("値が原資料に無い", "列の取り違え", "別の科目の値",
                          "親階層の取り違え", "単位・符号の表記", "不明"))
        tail = Q.question_text()[len(Q.base_question()):]
        for w in Q.VOCAB:
            self.assertIn(w, tail, w)

    def test_3_a_doctored_question_is_caught(self):
        with self.assertRaises(AssertionError):
            Q.check("先頭が違う" + Q.question_text())
        with self.assertRaises(AssertionError):
            Q.check(Q.base_question())           # 足した欄が無い


class FreezeTest(unittest.TestCase):
    def test_4_the_check_is_stage_11s(self):
        self.assertTrue(F.check.__code__.co_filename.endswith(
            "sheet_m11_freeze_answers_2026-10-16.py"))
        names = {n.name for n in ast.walk(ast.parse(
            src("sheet_errdet_freeze_2026-10-17.py")))
            if isinstance(n, ast.FunctionDef)}
        self.assertNotIn("check", names, "**検査を書き直してはいけない**")

    def test_5_attach_kind_falls_back_to_unknown_and_records_it(self):
        ok = [{"id": "R001"}, {"id": "R002"}, {"id": "R003"}]
        raw = [{"id": "R001", "不一致の種類": "列の取り違え"},
               {"id": "R002", "不一致の種類": "でっちあげ"},
               {"id": "R003"}]
        got, bad = F.attach_kind(ok, raw)
        self.assertEqual([g["不一致の種類"] for g in got],
                         ["列の取り違え", "不明", "不明"])
        self.assertEqual(len(bad), 2)
        self.assertIn("語彙に無い", bad[0]["理由"])
        self.assertIn("が無い", bad[1]["理由"])

    def test_6_cost_is_per_seat_and_capped_on_the_total(self):
        self.assertEqual(F.USD_PER_M_OUTPUT, {"seat1": 15.0, "seat2": 5.0})
        self.assertEqual(F.CAP_USD, 4.0)
        self.assertEqual(
            F.cost_upper_bound("seat1", 1000000)["費用の上限(全部が出力だと仮定)"],
            15.0)
        t = F.running_total("seat1", 3.9)
        self.assertEqual(t["人間が決めた上限"], 4.0)
        self.assertEqual(t["上限の中か"], t["2 席の合計の上限"] <= 4.0)


class ScoreRulesTest(unittest.TestCase):
    """**封が書いていなかった 2 点**を、壊した入力で 1 本ずつ当てる。"""

    SIX = {"会計": "一般会計", "階層": "項", "親": "総務費", "科目名": "x",
           "列": "支出済額", "値": 100}

    def test_7_no_ground_is_detection_hold_is_hold(self):
        self.assertEqual(SC.classify_seat({"verdict": "根拠なし"}), "検出")
        self.assertEqual(SC.classify_seat({"verdict": "判定不能"}), "保留")

    def test_8_six_fields_plus_a_kind_is_a_declared_mismatch(self):
        a = dict(self.SIX, **{"不一致の種類": "列の取り違え"})
        self.assertEqual(SC.classify_seat(a), "検出")
        b = dict(self.SIX, **{"不一致の種類": "不明"})
        self.assertEqual(SC.classify_seat(b), "確認済み")
        self.assertEqual(SC.classify_seat(dict(self.SIX)), "確認済み",
                         "欄が無ければ不明と同じ")

    def test_9_c_inherits_the_seat_when_there_is_no_address(self):
        kind, out, _why = SC.classify_c({"verdict": "根拠なし"}, 100)
        self.assertEqual(kind, "検出")
        self.assertIn("引き継いだ", out)
        kind, out, _why = SC.classify_c({"verdict": "判定不能"}, 100)
        self.assertEqual(kind, "保留")

    def test_10_the_verifier_has_the_four_sealed_values(self):
        got = set()
        for a, want in (({"会計": "無い会計", "階層": "項", "親": "", "科目名": "z",
                          "列": "支出済額", "値": 1}, 1),):
            out, _why = SC.verify(a, want)
            got.add(out)
        self.assertTrue(got <= {"確認済み", "原資料と一致しない",
                                "確認できない(参照先が無い)",
                                "確認できない(値が一意でない)"}, got)
        self.assertIn("確認できない(参照先が無い)", got)

    def test_11_the_grader_is_imported_not_rewritten(self):
        names = {n.name for n in ast.walk(ast.parse(
            src("sheet_errdet_score_2026-10-17.py")))
            if isinstance(n, ast.FunctionDef)}
        for forbidden in ("same_row", "resolve", "reach", "score_arm",
                          "col_match", "scope_match"):
            self.assertNotIn(forbidden, names, forbidden)
        self.assertTrue(SC.S.same_row.__code__.co_filename.endswith(
            "sheet_poc_ab_score_2026-10-17.py"))
        self.assertTrue(SC.A3.reach.__code__.co_filename.endswith(
            "sheet_poc_m3_addendum_2026-10-17.py"))

    def test_12_both_m3_definitions_are_reported(self):
        t = src("sheet_errdet_score_2026-10-17.py")
        self.assertIn("封の M-3 での見落とし", t)
        self.assertIn("封の M-3 での偽警報", t)
        self.assertIn("strict=True", t)


if __name__ == "__main__":
    unittest.main()
