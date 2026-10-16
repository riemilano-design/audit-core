# -*- coding: utf-8 -*-
"""段 8 の結果(docs/DOMAIN1_M8_RESULT_2026-10-16.md)を固定する。

**合格した側の歯止めが本体。**守るのは 7 つ。
  1. 数が記録と一致し、閾値が封のままであること
  2. **款名で増えたのは「接続」ではなく「採点できること」**だと書いてあること
     (項の 4 件は旧でも結べた / 増分は目の 2 件だけ)
  3. **G-1 を段 7 と比べない**・この標本は易しいと書いてあること
  4. **席の一致率を成果にしない**(人間の指示)
  5. 外れた T-3 と**未検証の T-6 後半**が残っていること
  6. 採点器の X の誤りを**結果の後に直したこと**を開示し、合否が動いていないこと
  7. ②③と G-4 が**まだ発火していない**と書いてあること
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m8_score_2026-10-16.json")
BINDS = os.path.join(FX, "m8_binds_2026-10-16.json")
OPP = os.path.join(FX, "m8_opportunity_2026-10-16.json")
REPORT = os.path.join(FX, "m8_report_2026-10-16.json")
M7S = os.path.join(FX, "m7_score_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M8_RESULT_2026-10-16.md")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M8_SEAL_2026-10-16.md")


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

    def test_the_overall_verdict_is_pass(self):
        self.assertEqual(self.s["overall"], "合格")
        self.assertIn("**合格**", self.d.split("\n")[0])

    def test_the_sealed_lines_are_unchanged(self):
        want = {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                "G-5 母数": "≥ 20", "G-7 正しい接続の増分": "≥ 1 件",
                "G-8 誤受理の増分": "= 0 件"}
        for k, v in want.items():
            self.assertEqual(self.s["lines"][k]["pass"], v, k)

    def test_the_measured_numbers(self):
        self.assertEqual(self.s["scorable"], 25)
        self.assertEqual(self.s["E2_誤受理"], 0)
        self.assertEqual(self.s["lines"]["G-1 接続の正確さ"]["num"], 19)
        self.assertEqual(self.s["lines"]["G-7 正しい接続の増分"]["count"], 2)
        self.assertEqual(self.s["lines"]["G-8 誤受理の増分"]["count"], 0)
        self.assertEqual(self.s["seats_agree_6"], 24)
        self.assertEqual(self.s["hold_total"], 1)

    def test_the_doc_numbers_match_the_record(self):
        self.assertIn("**76.0%(19/25)**", self.d)
        self.assertIn("**+2 件**(旧 17 → 新 19)", self.d)
        self.assertIn("**主指標 E2(誤受理)= 0 件。総合: 合格。**", self.d)

    def test_stage_7_stays_a_failure(self):
        self.assertEqual(load(M7S)["overall"], "失敗")
        self.assertEqual(load(M7S)["E2_誤受理"], 6)
        self.assertIn("**段 7 は失敗として固定したままである**", self.d)
        self.assertIn("**段 8 は別の標本・別の報告文で測った。**", self.d)


class XTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_x2_is_zero_and_matches_the_run_record(self):
        self.assertEqual(self.s["X"]["X-2 抜粋に無い行に結んだ"], 0)
        self.assertEqual(self.s["X"]["X-1 抜粋に在る行に結んだ"], 19)
        b = load(BINDS)["claim_level_counts"]
        self.assertEqual(b["X-2 抜粋に無い行に結んだ主張"],
                         self.s["X"]["X-2 抜粋に無い行に結んだ"])
        self.assertEqual(b["X-1 抜粋に在る行に結んだ主張"],
                         self.s["X"]["X-1 抜粋に在る行に結んだ"])

    def test_the_doc_compares_x_with_stage_7(self):
        self.assertIn("| **X-2 抜粋に無い行に結んだ** | **6** | **0** |", self.d)
        self.assertIn("## 2. 段 7 の失敗の型は再発しなかった(封 §4-1 の X)", self.d)

    def test_the_pre_generation_prediction_is_quoted(self):
        o = load(OPP)
        self.assertEqual(o["O-5 6 欄すべてが抜粋から読めるセル"], o["cells"])
        self.assertIn("**O-5(6 欄すべてが抜粋から読めるセル)が 132 / 132 = 全セル**", self.d)


class WhatTheKanNameBoughtTest(unittest.TestCase):
    """**款名で増えたのは「接続」ではなく「採点できること」。**ここが本体。"""

    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_the_doc_says_so_in_those_words(self):
        self.assertIn("**款名を足して増えたのは「接続」ではなく「採点できること」である。**",
                      self.d)

    def test_the_four_kou_rows_were_already_bound_by_the_old_engine(self):
        old = {r["id"]: r for r in self.s["rows_old"]}
        for cid in ("R010", "R013", "R015", "R018"):
            self.assertEqual(old[cid]["state"], "GROUNDED", cid)
            self.assertIn("| **増やしていない** |", self.d)

    def test_only_two_moku_rows_were_gained(self):
        gained = [r["id"] for r in self.s["rows"]
                  if r["state"] == "GROUNDED"
                  and {x["id"]: x for x in self.s["rows_old"]}[r["id"]]["state"]
                  != "GROUNDED"]
        self.assertEqual(gained, ["R020", "R023"])
        self.assertIn("**接続が増えたのは目の 2 件だけである。**", self.d)
        self.assertEqual(load(OPP)["O-4 の表ごとの内訳"], {"表 3": 12})
        self.assertIn("**増分は予告どおり表 3 からしか出ていない。**", self.d)

    def test_n2_is_zero(self):
        self.assertEqual(self.s["N-2_親を誤って抽出"], 0)
        self.assertEqual(self.s["N-1_親を正しく抽出"], 6)


class CannotClaimTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.d = text(DOC)

    def test_the_doc_refuses_to_compare_g1_with_stage_7(self):
        self.assertIn("**G-1 76.0% を段 7 の 51.3% と比べて「良くなった」とは言えない。**",
                      self.d)
        self.assertIn("**標本が違い、しかもこの標本は易しい。**", self.d)
        self.assertIn("旧の G-1 は **68.0%**", self.d)
        self.assertEqual(self.s["old"]["g1"], 17)

    def test_the_doc_does_not_treat_seat_agreement_as_a_result(self):
        self.assertIn("**これを成果として扱わない。**", self.d)
        self.assertIn("**一致しやすくなったことは engine の接続が正しい証拠ではない。**",
                      self.d)
        self.assertIn("**席の一致率が上がったことを成果として書かない。**", text(SEAL))

    def test_g4_is_still_not_confirmed(self):
        self.assertEqual(self.s["lines"]["G-4 保留の適切さ"]["den"], 1)
        both = [r for r in self.s["rows"]
                if r["label6"][0] == "verdict" and r["seats_agree"]]
        self.assertEqual(both, [])
        self.assertIn("**段 6 と同じ注意が要る: 保留の適切さを確かめたとは書けない。**",
                      self.d)

    def test_the_doc_says_only_two_of_25_gained(self):
        self.assertIn("接続を増やしたのは **25 件中 2 件**である", self.d)

    def test_the_doc_says_the_moku_parent_has_a_weaker_backing(self):
        self.assertIn("**目の親の裏づけは 2 本しか無い**", self.d)
        self.assertIn("**目で正しく結べた 2 件は、裏づけ 2 本の親に頼っている。**", self.d)

    def test_the_doc_refuses_generalisation(self):
        self.assertIn("他の自治体・他の年度・一般の会計資料に通じるとは結論しない", self.d)
        self.assertIn("**1 本の報告文・1 回の生成である。**", self.d)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_t3_is_recorded_as_a_miss(self):
        self.assertRegex(self.d, r"\| T-3 \|.*?\|.*?\|\s*\*\*外れ(.*?)\*\*\s*\|")
        self.assertIn("**T-3 は外れである。**", self.d)
        self.assertIn("**上に外したので「良い方に外れた」が、外れは外れとして残す。**", self.d)

    def test_t6_second_half_is_recorded_as_unverified(self):
        self.assertIn("**T-6 の後半は当たっていない。未検証である。**", self.d)
        self.assertIn("**0 件だったことを「予測が当たった」と書かない。**", self.d)

    def test_the_header_counts_the_unverified_one_separately(self):
        self.assertIn("**10 本中 9 本当たり・1 本外れ・1 本は未検証**", self.d)

    def test_t8_is_marked_as_not_a_result(self):
        self.assertIn("当たり(**ただし成果ではない。§5**)", self.d)


class DisclosureTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_the_x_bug_fixed_after_the_result_is_disclosed(self):
        self.assertIn("**採点器の X の計算に誤りが在り、結果を見た後に直した。**", self.d)
        self.assertIn("**直したのは X の比較だけで、合否の 7 本(G-1〜G-8)には触っていない。**",
                      self.d)
        self.assertIn("**X 以外の 30 欄すべてが一致し、総合も `合格` のまま**", self.d)
        self.assertIn("**同じ型(両側に同じ正規化を掛けていない)を繰り返した。**", self.d)

    def test_the_scorer_now_normalises_both_sides(self):
        src = text(os.path.join(ROOT, "measure", "sheet_m8_score_2026-10-16.py"))
        self.assertIn("**両側に同じ正規化を掛ける。**", src)
        self.assertIn("return tuple(norm(x) or \"\" for x in (scope, level, parent, name))",
                      src)

    def test_the_seal_wording_error_is_disclosed_and_the_seal_is_not_edited(self):
        self.assertIn("**封 §2-1 の字に誤りが在る**(封は直さない)", self.d)
        self.assertIn("**件数 2 は合っている。**", self.d)
        self.assertIn("**427 / 30 / 427 通り**", text(
            os.path.join(ROOT, "docs", "DOMAIN1_M7_SEAL_2026-10-15.md")))

    def test_the_only_material_change_is_the_kan_name_column(self):
        self.assertIn("**材料の形を段 7 から変えたのは表 2 の `款名` の欄だけ**", self.d)
        self.assertIn("**engine は旧も新も 1 行も変えていない。**", self.d)

    def test_the_thin_table_3_is_disclosed(self):
        self.assertIn("**表 3 は 4 行しか無い。**", self.d)
        self.assertIn("**この数を見て表 3 を増やすことはしなかった。**", self.d)


class RemainingHolesTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)
        self.s = load(SCORE)

    def test_the_remaining_holes_are_counted(self):
        for k in ("② 階層の手がかりを 1 文の中で引き継ぐか",
                  "③ 未確認の別名が判定に入る標本",
                  "親の成分が 1 つの場合(項)で**接続が増えるか**",
                  "保留の適切さ(G-4)", "目の親の裏づけ"):
            self.assertIn(k, self.d, k)

    def test_the_alias_still_never_fired(self):
        self.assertEqual(self.s["new_hold_reasons"].get("会計が未確認の別名", 0), 0)
        self.assertIn("**段 6・段 7・段 8 で 1 度も発火していない**", self.d)

    def test_the_doc_repeats_that_a_silent_defect_is_not_a_fixed_one(self):
        self.assertIn("**発火しなかった欠陥は消えた欠陥ではない**", self.d)
        self.assertIn("段 7 でそれを実証した", self.d)

    def test_the_human_decides_next(self):
        self.assertIn("**新しい封を立てる前に人間の判断が要る。**", self.d)


class FrozenTest(unittest.TestCase):
    def test_the_report_was_generated_once(self):
        r = load(REPORT)
        self.assertEqual(r["runs"], 1)
        self.assertFalse(r["regenerated"])
        self.assertEqual(r["report_chars"], 867)
        self.assertTrue(r["within_limit"])

    def test_both_engines_were_applied_once(self):
        b = load(BINDS)
        self.assertEqual(b["applied_times"], 1)
        self.assertEqual(b["old_engine"], "measure/sheet_m5_engine_2026-10-15.py")
        self.assertEqual(b["new_engine"], "measure/sheet_m7_engine_2026-10-15.py")

    def test_the_question_is_identical_to_stage_6(self):
        m8 = load(os.path.join(FX, "m8_label_material_2026-10-16.json"))
        m6 = load(os.path.join(FX, "m6_label_material_2026-10-15.json"))
        self.assertEqual(m8["question"], m6["question"])

    def test_the_two_seats_differ_in_model_and_order(self):
        s1 = load(os.path.join(FX, "m8_answers_seat1_2026-10-16.json"))
        s2 = load(os.path.join(FX, "m8_answers_seat2_2026-10-16.json"))
        self.assertNotEqual(s1["model"], s2["model"])
        self.assertEqual(s2["order"], "逆順")
        self.assertEqual((len(s1["answers"]), len(s2["answers"])), (25, 25))

    def test_the_old_engine_is_still_the_stage_5_file(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out)

    def test_the_new_engine_was_not_touched_in_stage_8(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m7_engine_2026-10-15.py"]).decode()
        self.assertIn("段 7", out, "新 engine が段 8 で変更されている: %s" % out)


if __name__ == "__main__":
    unittest.main()
