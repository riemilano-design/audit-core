# -*- coding: utf-8 -*-
"""段 6 の結果(docs/DOMAIN1_M6_RESULT_2026-10-15.md)を固定する。

**合格したときほど、言えないことを書いた行を門にする。**
守るのは 5 つ。
  1. 採点の数と閾値が封のままであること(文書の数が記録と一致すること)
  2. 外れた予測(S-7)が**外れたまま**書かれていること
  3. 「項・目は 0 件」「親で結べた件数は 0 件」「別名は発火しなかった」が消えないこと
  4. `親が必要だった主張` の**2 通りの数え方**が両方書かれていること
  5. 開示(材料の id の衝突・字だけの直し・費用を測っていないこと)が消えないこと
"""
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m6_score_2026-10-15.json")
BINDS = os.path.join(FX, "m6_binds_2026-10-15.json")
REPORT = os.path.join(FX, "m6_report_2026-10-15.json")
LABMAT = os.path.join(FX, "m6_label_material_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M6_RESULT_2026-10-15.md")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M6_SEAL_2026-10-15.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)

    def test_the_overall_verdict_is_pass(self):
        self.assertEqual(self.s["overall"], "合格")

    def test_the_five_lines_keep_their_sealed_thresholds(self):
        want = {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                "G-5 母数": "≥ 20"}
        for k, v in want.items():
            self.assertEqual(self.s["lines"][k]["pass"], v, k)

    def test_the_measured_numbers(self):
        self.assertEqual(self.s["scorable"], 25)
        self.assertEqual(self.s["lines"]["G-1 接続の正確さ"]["num"], 13)
        self.assertEqual(self.s["E2_誤受理"], 0)
        self.assertEqual(self.s["lines"]["G-2 誤接続"]["count"], 0)
        self.assertEqual(self.s["lines"]["G-3 根拠なしの接続"]["count"], 0)
        self.assertEqual(self.s["hold_total"], 4)
        self.assertEqual(self.s["seats_agree_6"], 22)
        self.assertEqual(self.s["split"], {"接続数": 13, "保留数": 12, "対象外数": 0})

    def test_g4_denominator_is_four_so_the_doc_must_say_it_is_not_proof(self):
        """分母 4 件のうち 3 件は席の食い違い。**確かめたと書かない**。"""
        self.assertEqual(self.s["lines"]["G-4 保留の適切さ"]["den"], 4)
        rows = {r["id"]: r for r in self.s["rows"]}
        both = [r for r in self.s["rows"]
                if r["verdict"] == "正しく保留" and r["seats_agree"]]
        self.assertEqual([r["id"] for r in both], ["R008"])
        self.assertIn("そのうち 3 件は席の食い違いである", text(DOC))
        self.assertIn("保留の適切さを確かめたとは書けない", text(DOC))
        self.assertIn("R008", rows)

    def test_no_row_was_bound_by_value_only(self):
        """13 件すべて R-1。**値だけで絞った接続が無い**ことを門にする。"""
        self.assertEqual(self.s["routes"], {"R-1": 13})

    def test_only_4_is_zero_and_is_not_used_for_the_verdict(self):
        self.assertEqual(self.s["reference_only"]["only_4"], 0)
        self.assertEqual(self.s["reference_only"]["agree_4"], 13)


class DocNumbersTest(unittest.TestCase):
    """**文書の数が記録と一致すること。**文書だけ書き換えても赤くなる。"""

    def setUp(self):
        self.d = text(DOC)
        self.s = load(SCORE)
        self.b = load(BINDS)

    def test_the_g1_line_matches_the_record(self):
        rate = self.s["lines"]["G-1 接続の正確さ"]["rate"]
        self.assertIn("**%.1f%%(%d/%d)**" % (rate * 100, 13, 25), self.d)

    def test_the_e2_line_matches_the_record(self):
        self.assertEqual(self.s["E2_誤受理"], 0)
        self.assertIn("**主指標 E2(誤受理)= 0 件。総合: 合格。**", self.d)

    def test_the_split_matches_the_record(self):
        for k, v in self.s["split"].items():
            self.assertIn("| %s | **%d** |" % (k, v), self.d)

    def test_the_novelty_counts_match_the_record(self):
        self.assertEqual(self.b["counts"]["novelty_scorable"], {"新規": 24, "再出": 1})
        self.assertIn("**新規 24 / 再出 1**", self.d)

    def test_the_seat_agreement_matches_the_record(self):
        self.assertIn("**6 欄すべて一致したのは 22 / 25(88.0%)**", self.d)


class WhatCannotBeClaimedTest(unittest.TestCase):
    """**合格した側の歯止め。**ここが消えたら赤くする。"""

    def setUp(self):
        self.d = text(DOC)
        self.s = load(SCORE)
        self.b = load(BINDS)

    def test_the_doc_says_level_koumoku_bound_zero(self):
        grounded = [r for r in self.s["rows"] if r["state"] == "GROUNDED"]
        levels = [r["engine_key6"][1][1] for r in grounded]
        self.assertEqual(sum(1 for x in levels if x in ("項", "目")), 0)
        self.assertIn("**項・目は 0 件**", self.d)
        self.assertIn("**接続できた 13 件の階層は、会計 11 件・款 2 件。"
                      "項と目は 1 件も結べていない。**", self.d)

    def test_the_doc_says_the_parent_bound_nothing(self):
        self.assertEqual(self.b["parent_required"], 0)
        self.assertIn("**親が効くことは実証していない。**", self.d)
        self.assertIn("**親を使って正しく結んだ件数は 0 件**", self.d)

    def test_the_doc_says_the_alias_never_fired(self):
        self.assertEqual(self.b["counts"]["hold_reasons"].get("会計が未確認の別名", 0), 0)
        self.assertIn("**発火しなかった**", self.d)
        self.assertIn("この条件は未評価のままである", self.d)

    def test_the_doc_does_not_call_holding_safe_on_its_own(self):
        self.assertIn("**「保留が増えたから安全になった」とは書かない。"
                      "接続 13・保留 12 と並べて書く。**", self.d)

    def test_the_doc_prices_the_safety_in_g1_points(self):
        """値で選べば 3 件当たって 64.0% だった、を消させない。"""
        self.assertIn("**3 件**(R026・R027・R028)", self.d)
        self.assertIn("**その方式なら G-1 は 64.0%(16/25)になっていた。**", self.d)

    def test_the_doc_keeps_the_sealed_warning_about_this_sample(self):
        self.assertIn("1 本の報告文・1 回の生成である", self.d)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_s7_is_recorded_as_a_miss(self):
        m = re.search(r"\| S-7 \|.*?\|.*?\|\s*\*\*外れ\*\*\s*\|", self.d)
        self.assertTrue(m, "S-7 の行が『外れ』で残っていない")

    def test_the_miss_is_not_softened(self):
        self.assertIn("**S-7 は「正しく結べたものが 1 件以上」と予測して 0 件だった。"
                      "外れたまま残す。**", self.d)

    def test_s4_and_s5_hit_the_number_but_the_doc_says_the_mechanism_missed(self):
        self.assertIn("**S-4・S-5 は数は当たったが、私が書いた理由は外れている。**", self.d)
        self.assertIn("**当たった数で、外れた機構を隠さない。**", self.d)

    def test_the_doc_does_not_score_itself_by_how_many_predictions_hit(self):
        self.assertIn("**10 本中 9 本当たり・1 本外れ**", self.d)
        for bad in ("当たったので合格", "9 本当たったので"):
            self.assertNotIn(bad, self.d)


class DisclosureTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_the_id_collision_in_the_label_material_is_disclosed(self):
        mat = load(LABMAT)
        ids = re.findall(r'\{"id": "(R\d+)"', mat["question"])
        self.assertIn("R002", ids, "問いの例が R002 を使っていない(開示文と合わない)")
        self.assertIn("**例の `R002`・`R003`・`R004` と実物の id が衝突している。**", self.d)
        self.assertIn("今回は直さず開示する", self.d)

    def test_both_counts_of_parent_required_are_written(self):
        self.assertIn("実装(`sheet_m6_run_…py`)は **`GROUNDED` の行にだけ印を付けた。**",
                      self.d)
        self.assertIn("封の字どおりに数えると **4 件**である", self.d)
        self.assertIn("**S-7 の外れは動かない。**", self.d)

    def test_the_engine_was_not_touched_in_stage_6(self):
        """段 6 で engine を変えていないことを**file で**確かめる。"""
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out, "engine が段 6 で変更されている: %s" % out)
        self.assertIn("**engine は段 5 のものを 1 行も変えずに当てた。**", self.d)

    def test_the_cost_is_not_claimed_in_usd(self):
        self.assertIn("**費用は USD で測っていない。**", self.d)
        self.assertIn("金額は測っていないので書かない", self.d)

    def test_the_text_only_fixes_are_disclosed(self):
        self.assertIn("字だけの直しを 2 件した", self.d)
        self.assertIn("**数・閾値・規則には触れていない**", self.d)


class FrozenMaterialTest(unittest.TestCase):
    def test_the_report_was_generated_once_and_not_regenerated(self):
        r = load(REPORT)
        self.assertEqual(r["runs"], 1)
        self.assertFalse(r["regenerated"])
        self.assertTrue(r["within_limit"])
        self.assertEqual(r["report_chars"], 770)

    def test_the_prompt_is_byte_identical_to_the_material(self):
        import hashlib
        r = load(REPORT)
        mat = load(os.path.join(FX, "m6_material_2026-10-15.json"))
        self.assertEqual(hashlib.sha256(mat["prompt"].encode("utf-8")).hexdigest(),
                         r["prompt_sha256"])
        self.assertTrue(r["prompt_identical_to_stage4"])

    def test_the_question_was_checked_against_the_spec(self):
        mat = load(LABMAT)
        self.assertTrue(mat["question_checked"])
        spec = importlib.util.spec_from_file_location(
            "ls6", os.path.join(ROOT, "measure", "sheet_label_spec_2026-10-15.py"))
        L = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(L)
        L.check_question(mat["question"])      # 落ちたら赤
        self.assertIn("R-会計-2", mat["question"])

    def test_the_two_seats_are_different_models_in_reversed_order(self):
        s1 = load(os.path.join(FX, "m6_answers_seat1_2026-10-15.json"))
        s2 = load(os.path.join(FX, "m6_answers_seat2_2026-10-15.json"))
        self.assertNotEqual(s1["model"], s2["model"])
        self.assertEqual(s2["order"], "逆順")
        self.assertEqual(len(s1["answers"]), 25)
        self.assertEqual(len(s2["answers"]), 25)
        self.assertEqual(s1["answers"][0]["id"], "R002")
        self.assertEqual(s2["answers"][0]["id"], "R028")

    def test_the_result_doc_points_at_the_seal(self):
        self.assertIn("DOMAIN1_M6_SEAL_2026-10-15.md", text(DOC))
        self.assertIn("ba94001", text(DOC))
        self.assertIn("E2 ＝ 0 件", text(SEAL) + text(DOC))


if __name__ == "__main__":
    unittest.main()
