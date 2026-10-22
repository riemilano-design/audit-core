# -*- coding: utf-8 -*-
"""段 5 の**手続き**を門にする(結果の数には依存しない)。

結果が合格でも失敗でも判定不能でも、ここは同じことを要求する:
生成は 1 回・ラベルは 2 席で別モデル・並びは逆順・分母は縮めない・
`agree_4` で合否を出さない・新規が 10 件未満なら独立の確認と呼ばない。
"""
import hashlib
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m5_material_2026-10-15.json")
REPORT = os.path.join(FX, "m5_report_2026-10-15.json")
BINDS = os.path.join(FX, "m5_binds_2026-10-15.json")
LABMAT = os.path.join(FX, "m5_label_material_2026-10-15.json")
SCORE = os.path.join(FX, "m5_score_2026-10-15.json")
SEATS = [os.path.join(FX, "m5_answers_seat%d_2026-10-15.json" % i) for i in (1, 2)]
SCORER = os.path.join(ROOT, "measure", "sheet_m5_score_2026-10-15.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class GenerationTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REPORT)

    def test_generated_once_and_not_redone(self):
        self.assertEqual(self.r["runs"], 1)
        self.assertFalse(self.r["regenerated"])

    def test_within_the_sealed_length(self):
        self.assertTrue(self.r["within_limit"])
        self.assertLessEqual(self.r["report_chars"], self.r["limit_report_chars"])
        self.assertEqual(self.r["limit_report_chars"], 1200)

    def test_the_prompt_is_the_committed_one(self):
        mat = load(MAT)
        self.assertEqual(
            self.r["prompt_sha256"],
            hashlib.sha256(mat["prompt"].encode("utf-8")).hexdigest())

    def test_only_the_prompt_was_handed_over(self):
        self.assertEqual(self.r["handed_to_seat"],
                         ["prompt.txt のみ(他のファイルを読まないよう指示)"])

    def test_the_previous_stage_was_withheld(self):
        for w in ("engine の判定", "合否ラベル", "封の内容",
                  "段 4 の報告文と採点結果", "診断の結果"):
            self.assertIn(w, self.r["withheld"], w)


class EngineApplicationTest(unittest.TestCase):
    def setUp(self):
        self.b = load(BINDS)

    def test_applied_once(self):
        self.assertEqual(self.b["applied_times"], 1)

    def test_the_engine_is_the_committed_one(self):
        self.assertEqual(self.b["engine"], "measure/sheet_m5_engine_2026-10-15.py")

    def test_the_three_counts_add_up_to_the_claims(self):
        s = self.b["counts"]["split"]
        self.assertEqual(sum(s.values()), self.b["counts"]["claims"])
        for k in ("接続数", "保留数", "対象外数"):
            self.assertIn(k, s)

    def test_every_hold_has_a_named_reason(self):
        held = [x for x in self.b["binds"] if x["state"] == "UNVERIFIABLE"]
        self.assertEqual(len(held), self.b["counts"]["split"]["保留数"])
        for x in held:
            self.assertTrue(x["hold_reason"], x["claim_id"])

    def test_the_alias_rule_was_in_force(self):
        self.assertEqual(self.b["alias_passed"], ["東京都一般会計"])
        self.assertEqual(self.b["alias_unconfirmed"], 18)

    def test_no_level_was_excluded_for_duplication(self):
        self.assertEqual(self.b["duplication"]["levels_not_unique"], [])

    def test_nothing_bound_to_an_unconfirmed_account(self):
        """封 §5。未確認の会計に結んだら失敗。**件数 0 を門にする。**"""
        bad = [x["claim_id"] for x in self.b["binds"]
               if x["state"] == "GROUNDED" and x.get("unconfirmed_scope")]
        self.assertEqual(bad, [])


class LabelMaterialTest(unittest.TestCase):
    def setUp(self):
        self.m = load(LABMAT)
        self.texts = {}
        for s in self.m["files"]:
            if os.path.exists(s["path"]):
                self.texts[s["seat"]] = io.open(s["path"], encoding="utf-8").read()

    def test_two_seats_with_reversed_order(self):
        files = {s["seat"]: s for s in self.m["files"]}
        self.assertEqual(sorted(files), ["seat1", "seat2"])
        self.assertEqual(files["seat1"]["first_id"], files["seat2"]["last_id"])
        self.assertEqual(files["seat1"]["last_id"], files["seat2"]["first_id"])
        orders = sorted(s["order"] for s in self.m["seats"])
        self.assertEqual(orders, ["そのまま", "逆順"])

    def test_the_question_asks_for_six_fields(self):
        q = self.m["question"]
        for f in ("会計", "階層", "親", "科目名", "列", "値"):
            self.assertIn(f, q, f)

    def test_the_total_row_convention_is_given_with_an_example(self):
        q = self.m["question"]
        self.assertIn("会計 = 合計 / 階層 = 合計", q)
        self.assertIn("\"会計\": \"合計\"", q)

    def test_the_seats_are_told_not_to_guess_the_parent(self):
        self.assertIn("推測で埋めないでください", self.m["question"])

    def test_the_banned_words_are_absent_from_every_handed_file(self):
        if not self.texts:
            self.skipTest("材料のファイルが残っていない(scratchpad は消える)")
        for seat, t in self.texts.items():
            for w in self.m["banned_checked"]:
                self.assertNotIn(w, t, "%s に %r" % (seat, w))


class ScorerTest(unittest.TestCase):
    """採点器は**ラベルを見る前に** commit した。規則が後から動いていないこと。"""

    def setUp(self):
        self.src = io.open(SCORER, encoding="utf-8").read()

    def test_the_sealed_thresholds_are_literal_in_the_scorer(self):
        for s in ('"pass": "≥ 50%"', '"pass": "= 0 件"', '"pass": "≥ 80%"',
                  '"pass": "≥ 20"'):
            self.assertIn(s, self.src, s)
        self.assertIn(">= 0.50", self.src)
        self.assertIn(">= 0.80", self.src)
        self.assertIn("n >= 20", self.src)

    def test_the_verdict_uses_agree_6_not_agree_4(self):
        self.assertIn('row["agree_6"]', self.src)
        self.assertIn("参考", self.src)
        # agree_4 は g1/g2/g3 の判定に使われていないこと
        for line in self.src.splitlines():
            if "agree_4" in line:
                self.assertNotIn("g1 +=", line)
                self.assertNotIn("g2 +=", line)
                self.assertNotIn("g3 +=", line)

    def test_e2_is_the_sum_of_the_two_false_acceptance_kinds(self):
        self.assertIn("e2 = g2 + g3", self.src)

    def test_disagreeing_seats_stay_in_the_denominator(self):
        self.assertIn('return ("verdict", norm("判定不能")), False', self.src)
        self.assertIn("hold_total += 1", self.src)


class ScoreRecordTest(unittest.TestCase):
    """採点の記録があるときだけ見る(結果の数には踏み込まない)。"""

    def setUp(self):
        if not os.path.exists(SCORE):
            self.skipTest("まだ採点していない")
        self.s = load(SCORE)

    def test_the_thresholds_in_the_record_are_the_sealed_ones(self):
        p = {k: v["pass"] for k, v in self.s["lines"].items()}
        self.assertEqual(p, {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                             "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                             "G-5 母数": "≥ 20"})

    def test_the_denominator_is_every_scorable_claim(self):
        b = load(BINDS)
        self.assertEqual(self.s["scorable"], b["counts"]["scorable"])
        self.assertEqual(len(self.s["rows"]), self.s["scorable"])
        self.assertEqual(self.s["missing_answers"], [])

    def test_e2_equals_g2_plus_g3(self):
        self.assertEqual(self.s["E2_誤受理"],
                         self.s["lines"]["G-2 誤接続"]["count"]
                         + self.s["lines"]["G-3 根拠なしの接続"]["count"])

    def test_a_short_denominator_is_undecidable_not_a_pass(self):
        if self.s["scorable"] < 20:
            self.assertEqual(self.s["overall"], "判定不能(母数不足)")

    def test_the_overall_follows_the_lines_mechanically(self):
        ok = all(v["ok"] for v in self.s["lines"].values())
        if self.s["scorable"] >= 20:
            self.assertEqual(self.s["overall"], "合格" if ok else "失敗")

    def test_the_novelty_rule_is_applied(self):
        n = self.s["novelty"].get("新規", 0)
        self.assertEqual(self.s["independent_confirmation"], n >= 10)

    def test_both_seats_answered_every_claim_with_a_usable_shape(self):
        for p in SEATS:
            if not os.path.exists(p):
                self.skipTest("席の回答がまだ無い")
            d = load(p)
            ids = {a["id"] for a in d["answers"]}
            self.assertEqual({r["id"] for r in self.s["rows"]} - ids, set(), p)
            for a in d["answers"]:
                if a.get("verdict"):
                    self.assertIn(a["verdict"], ("根拠なし", "判定不能"), a["id"])

    def test_the_two_seats_used_different_models(self):
        models = []
        for p in SEATS:
            if not os.path.exists(p):
                self.skipTest("席の回答がまだ無い")
            models.append(load(p)["model"])
        self.assertEqual(len(set(models)), 2, models)

    def test_the_hold_reasons_are_recorded(self):
        if self.s["split"]["保留数"]:
            self.assertTrue(self.s["hold_reasons"])
            self.assertEqual(sum(self.s["hold_reasons"].values()),
                             self.s["split"]["保留数"])


if __name__ == "__main__":
    unittest.main()
