# -*- coding: utf-8 -*-
"""段 7 の結果(docs/DOMAIN1_M7_RESULT_2026-10-16.md)を固定する。

**失敗を失敗として残す門**。守るのは 7 つ。
  1. 総合が「失敗」で、E2 = 6 件であること(閾値も分母も封のまま)
  2. **主目的(親の規則)を満たしたことを合格扱いにしていない**こと
  3. 誤受理 6 件が **engine の指したセルの誤りではない**と書き、
     それでも**規則どおり失敗**と書いていること
  4. **G-2 と G-4 が同じ 6 行**だと書いてあること
  5. 生成前に書いた限界と**結論が違った**ことを、外れとして残していること
  6. 「6 件を除けば E2 は 0」の計算を**しない**と書いてあること
  7. 次の 3 案を並べ、**どれも正解の定義に触る**と書いてあること
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m7_score_2026-10-15.json")
BINDS = os.path.join(FX, "m7_binds_2026-10-15.json")
OPP = os.path.join(FX, "m7_opportunity_2026-10-15.json")
REPORT = os.path.join(FX, "m7_report_2026-10-15.json")
M6S = os.path.join(FX, "m6_score_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M7_RESULT_2026-10-16.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_the_overall_verdict_is_failure(self):
        self.assertEqual(self.s["overall"], "失敗")
        self.assertIn("**失敗**", self.d.split("\n")[0])

    def test_the_sealed_lines_are_unchanged(self):
        want = {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                "G-5 母数": "≥ 20", "G-7 正しい接続の増分": "≥ 1 件",
                "G-8 誤受理の増分": "= 0 件"}
        for k, v in want.items():
            self.assertEqual(self.s["lines"][k]["pass"], v, k)

    def test_the_measured_numbers(self):
        self.assertEqual(self.s["scorable"], 39)
        self.assertEqual(self.s["E2_誤受理"], 6)
        self.assertEqual(self.s["lines"]["G-1 接続の正確さ"]["num"], 20)
        self.assertEqual(self.s["lines"]["G-7 正しい接続の増分"]["count"], 3)
        self.assertEqual(self.s["lines"]["G-8 誤受理の増分"]["count"], 0)
        self.assertEqual(self.s["lines"]["G-4 保留の適切さ"]["num"], 0)
        self.assertEqual(self.s["lines"]["G-4 保留の適切さ"]["den"], 6)
        self.assertEqual(self.s["seats_agree_6"], 33)

    def test_the_doc_numbers_match_the_record(self):
        self.assertIn("**51.3%(20/39)**", self.d)
        self.assertIn("**6 件**", self.d)
        self.assertIn("**+3 件**(旧 17 → 新 20)", self.d)
        self.assertIn("**0 件**(旧 6 → 新 6)", self.d)
        self.assertIn("**主指標 E2(誤受理)= 6 件。総合: 失敗。**", self.d)

    def test_the_verdict_comes_from_the_new_engine(self):
        self.assertIn("新 engine", self.s["verdict_from"])
        self.assertIn("良い方を選ばない", self.s["verdict_from"]
                      + text(os.path.join(ROOT, "measure",
                                          "sheet_m7_score_2026-10-15.py")))


class NotExcusedTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_meeting_the_main_objective_is_not_called_a_pass(self):
        self.assertEqual(self.s["main_objective_status"], "合格")
        self.assertEqual(self.s["overall"], "失敗")
        self.assertIn("**それでも総合は失敗である。**", self.d)
        self.assertIn("**「主目的は満たしたから合格扱い」にはしない。**", self.d)

    def test_the_doc_says_the_engine_pointed_at_the_right_cell_and_still_failed(self):
        self.assertIn("**engine が指したセルは間違っていない。**", self.d)
        self.assertIn("**採点は規則どおり失敗である。**", self.d)

    def test_the_doc_refuses_to_recompute_without_the_six(self):
        self.assertIn("**「6 件を除けば E2 は 0」という計算はしない。**", self.d)
        self.assertIn("分母を選び直すことだから", self.d)
        for bad in ("除けば E2 は 0 件", "実質は合格", "6 件を除外して"):
            self.assertNotIn(bad, self.d)

    def test_the_doc_refuses_to_blame_the_material_as_an_excuse(self):
        self.assertIn("**E2 = 6 件を「材料の欠陥だから数えない」とは言わない。**", self.d)

    def test_stage_6_verdict_is_untouched(self):
        self.assertEqual(load(M6S)["overall"], "合格")
        self.assertIn("**段 6 の合否を動かさない**", self.d)


class CauseTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_all_six_false_links_are_the_kou_rows(self):
        bad = [r["id"] for r in self.s["rows"]
               if r["verdict"] == "根拠なし/判定不能なのに接続した"]
        self.assertEqual(bad, ["R025", "R026", "R027", "R028", "R029", "R030"])
        self.assertIn("**項**の行である(R025〜R030)", self.d)

    def test_the_old_engine_had_the_same_six(self):
        self.assertEqual(self.s["old"]["e2"], 6)
        self.assertIn("旧エンジンも同じ 6 件で誤受理している", self.d)

    def test_g2_and_g4_are_the_same_six_rows(self):
        holds = [r["id"] for r in self.s["rows"] if r["label6"][0] == "verdict"]
        self.assertEqual(holds, ["R025", "R026", "R027", "R028", "R029", "R030"])
        both = [r for r in self.s["rows"] if r["label6"][0] == "verdict"
                and r["seats_agree"]]
        self.assertEqual(both, [])
        self.assertIn("**G-2 と G-4 は別の指標だが、原因は 1 つしかない。**", self.d)
        self.assertIn("**2 つ失敗したのではなく、1 つの原因が 2 つの線を割った。**", self.d)

    def test_the_asymmetry_is_named(self):
        self.assertIn("**engine はブック全体(4,209 セル)を読む。席は抜粋だけを読む。**",
                      self.d)
        self.assertIn("**この非対称は段 4 から在ったが、誤受理として現れたのは"
                      "今回が初めてである。**", self.d)

    def test_the_three_rows_the_parent_rule_fixed_are_recorded(self):
        fixed = [r["id"] for r in self.s["rows"]
                 if r["parent_filtered"] and r["verdict"] == "正しい接続"]
        self.assertEqual(fixed, ["R031", "R034", "R037"])
        self.assertEqual(self.s["N-1_親を正しく抽出"], 3)
        self.assertEqual(self.s["N-2_親を誤って抽出"], 0)
        for cid in fixed:
            self.assertIn("| %s |" % cid, self.d)


class PredictionMissTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)
        self.o = load(OPP)

    def test_the_pre_written_limit_is_quoted_from_the_record(self):
        self.assertIn("**親の成分が 1 つの場合(項)は、この標本では試されない。**",
                      self.o["limit"])
        self.assertIn("**親の成分が 1 つの場合(項)は、この標本では試されない。**", self.d)

    def test_the_doc_records_the_conclusion_as_a_miss(self):
        self.assertIn("**同じ欠陥を指していたが、結論を外した。**", self.d)
        self.assertIn("**「評価できない」と「安全側に落ちる」は別である。**", self.d)
        self.assertIn("**この外れを直さずに残す。**", self.d)

    def test_the_doc_admits_the_seal_had_no_count_prediction(self):
        self.assertIn("**件数の予測を書かなかった。**", self.d)
        self.assertIn("次の封では、**新しい標本についても外れうる数を書く。**", self.d)


class CannotClaimTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)
        self.s = load(SCORE)

    def test_the_doc_says_the_rule_fired_on_only_three_of_39(self):
        self.assertIn("**親抽出規則が実用になるとは言えない。**", self.d)
        self.assertIn("発火したのは **39 件中 3 件**だけである", self.d)
        self.assertEqual(self.s["N-1_分母_親で絞った主張"], 3)

    def test_the_doc_says_the_one_component_case_is_still_unevaluated(self):
        self.assertIn("**親の成分が 1 つの場合(項)は、まだ 1 度も正しく評価できていない。**",
                      self.d)

    def test_the_doc_refuses_generalisation(self):
        self.assertIn("他の自治体・他の年度・一般の会計資料に通じるとは結論しない", self.d)

    def test_the_doc_does_not_rewrite_the_rules_after_seeing_the_result(self):
        self.assertIn("**P-1〜P-7 を結果を見てから書き換えない。**", self.d)


class NextStepTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_three_options_are_listed_and_all_touch_the_definition(self):
        for k in ("(a) 材料に款名の欄を足す", "(b) 問いを直す", "(c) 採点規則で分ける"):
            self.assertIn(k, self.d, k)
        self.assertIn("**どれも正解の定義に触る。**", self.d)
        self.assertIn("いちばん危ない", self.d)

    def test_the_recommendation_does_not_erase_the_failure(self):
        self.assertIn("**(a) を選んでも、段 7 の失敗は失敗として残る。**", self.d)
        self.assertIn("作り直した標本は別の実験になる", self.d)

    def test_the_human_decides(self):
        self.assertIn("**人間の判断。私は選ばない**", self.d)

    def test_two_and_three_were_not_touched(self):
        self.assertIn("②(階層の手がかりの引き継ぎ)と③(未確認の別名)は、"
                      "封のとおり手を付けていない。", self.d)


class FrozenTest(unittest.TestCase):
    def test_the_report_was_generated_once(self):
        r = load(REPORT)
        self.assertEqual(r["runs"], 1)
        self.assertFalse(r["regenerated"])
        self.assertEqual(r["report_chars"], 1024)
        self.assertTrue(r["within_limit"])
        self.assertIn("席が自分で report.txt に書いた", r["written_by"])

    def test_both_engines_were_applied_once_to_the_same_report(self):
        b = load(BINDS)
        self.assertEqual(b["applied_times"], 1)
        self.assertEqual(b["old_engine"], "measure/sheet_m5_engine_2026-10-15.py")
        self.assertEqual(b["new_engine"], "measure/sheet_m7_engine_2026-10-15.py")
        self.assertEqual(len(b["binds_old"]), len(b["binds_new"]))

    def test_the_question_was_identical_to_stage_6(self):
        m7 = load(os.path.join(FX, "m7_label_material_2026-10-15.json"))
        m6 = load(os.path.join(FX, "m6_label_material_2026-10-15.json"))
        self.assertEqual(m7["question"], m6["question"])
        self.assertTrue(m7["question_identical_to_m6"])

    def test_the_two_seats_differ_in_model_and_order(self):
        s1 = load(os.path.join(FX, "m7_answers_seat1_2026-10-15.json"))
        s2 = load(os.path.join(FX, "m7_answers_seat2_2026-10-15.json"))
        self.assertNotEqual(s1["model"], s2["model"])
        self.assertEqual(s2["order"], "逆順")
        self.assertEqual((len(s1["answers"]), len(s2["answers"])), (39, 39))

    def test_the_old_engine_is_still_the_stage_5_file(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out, "旧 engine が変更されている: %s" % out)


if __name__ == "__main__":
    unittest.main()
