"""段 4 の結果を固定する(**失敗**として)。

守るのは 3 つ。
  1. 合格線は封のまま(後から緩められない)
  2. 失敗の数と原因が記録から消えない
  3. 「同じ報告文で直して合格扱いにしない」が文書に残る
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m4_score_2026-10-15.json")
BINDS = os.path.join(FX, "m4_binds_2026-10-15.json")
REPORT = os.path.join(FX, "m4_report_2026-10-15.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M4_SEAL_2026-10-15.md")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M4_RESULT_2026-10-15.md")
SEATS = [os.path.join(FX, "m4_answers_seat%d_2026-10-15.json" % i) for i in (1, 2)]


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = json.load(io.open(SCORE, encoding="utf-8"))

    def test_the_overall_verdict_is_failure(self):
        self.assertEqual(self.s["overall"], "失敗")

    def test_the_five_lines_keep_their_sealed_thresholds(self):
        want = {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                "G-5 母数": "≥ 20"}
        for k, v in want.items():
            self.assertEqual(self.s["lines"][k]["pass"], v, k)

    def test_the_measured_numbers(self):
        L = self.s["lines"]
        self.assertEqual((L["G-1 接続の正確さ"]["num"], L["G-1 接続の正確さ"]["den"]), (10, 24))
        self.assertAlmostEqual(L["G-1 接続の正確さ"]["rate"], 10 / 24.0, places=6)
        self.assertEqual(L["G-2 誤接続"]["count"], 5)
        self.assertEqual(L["G-3 根拠なしの接続"]["count"], 0)
        self.assertEqual((L["G-4 保留の適切さ"]["num"], L["G-4 保留の適切さ"]["den"]), (2, 5))
        self.assertEqual(L["G-5 母数"]["count"], 24)

    def test_the_denominator_was_not_shrunk_by_disagreement(self):
        """2 席が食い違った 3 件は分母に残る(封 §4-1)。"""
        self.assertEqual(self.s["seats_agree"], 21)
        self.assertEqual(self.s["scorable"], 24)

    def test_the_two_notation_rows_are_still_counted_as_false_links(self):
        rows = {r["id"]: r for r in self.s["rows"]}
        for cid in ("R015", "R016"):
            self.assertEqual(rows[cid]["verdict"], "誤接続", cid)
            self.assertEqual(rows[cid]["wrong_fields"], ["会計"], cid)

    def test_the_two_equal_column_rows_were_grounded_instead_of_held(self):
        rows = {r["id"]: r for r in self.s["rows"]}
        for cid in ("R023", "R024"):
            self.assertEqual(rows[cid]["engine_state"], "GROUNDED", cid)
            self.assertEqual(rows[cid]["label"][1], "判定不能", cid)

    def test_no_route_other_than_r1_fired(self):
        self.assertEqual(self.s["routes"], {"R-1": 15})


class MaterialTest(unittest.TestCase):
    def test_the_report_was_generated_once_and_not_redone(self):
        r = json.load(io.open(REPORT, encoding="utf-8"))
        self.assertEqual(r["runs"], 1)
        self.assertFalse(r["regenerated"])
        self.assertTrue(r["within_limit"])

    def test_the_two_seats_used_different_models(self):
        models = [json.load(io.open(p, encoding="utf-8"))["model"] for p in SEATS]
        self.assertEqual(len(set(models)), 2, models)
        orders = [json.load(io.open(p, encoding="utf-8"))["order"] for p in SEATS]
        self.assertEqual(sorted(orders), ["そのまま", "逆順"])

    def test_every_claim_has_an_answer_from_both_seats(self):
        claims = {c["id"] for c in json.load(io.open(BINDS, encoding="utf-8"))["claims"]}
        for p in SEATS:
            ids = {a["id"] for a in json.load(io.open(p, encoding="utf-8"))["answers"]}
            self.assertEqual(claims - ids, set(), p)
        self.assertEqual(json.load(io.open(SCORE, encoding="utf-8"))["missing_answers"], [])


class DocumentTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in
                      l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_each_line_has_its_own_row_with_the_measured_value(self):
        for sym, got in (("G-1 接続の正確さ", "41.7%(10/24)"), ("G-2 誤接続", "5 件"),
                         ("G-3 根拠なしの接続", "0 件"), ("G-4 保留の適切さ", "40.0%(2/5)"),
                         ("G-5 母数", "24 件")):
            hit = self._row(sym)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (sym, len(hit)))
            self.assertTrue(any(got in c for c in hit[0]), "%s: %s" % (sym, hit[0]))

    def test_each_prediction_has_its_own_row_and_the_misses_are_kept(self):
        for sym in ("P-1", "P-2", "P-3", "P-4", "P-5", "P-6"):
            self.assertEqual(len(self._row(sym)), 1, sym)
        self.assertIn("外れたまま記録する", self.doc)

    def test_the_document_says_it_failed(self):
        self.assertIn("総合: 失敗", self.doc)

    def test_the_four_causes_are_recorded(self):
        for word in ("原因 1 ― 列の手がかりの実装欠陥", "原因 2 ― 会計名が材料の中で 2 通り",
                     "原因 3 ― 同値の 2 列から 1 つを選んだ", "原因 4 ― 封の問いの定義の弱さ"):
            self.assertIn(word, self.doc)

    def test_the_document_refuses_to_rescore_the_same_sample(self):
        self.assertIn("同じ報告文で engine を直して再採点し、合格扱いにする", self.doc)
        self.assertIn("直したら新しい報告文を別に生成して測る", self.doc)

    def test_the_document_denies_that_stage3_predicted_this(self):
        self.assertIn("段 3 の 1,061/1,061 は、接続精度を何も保証しなかった", self.doc)

    def test_the_seal_is_unchanged_in_its_thresholds(self):
        with io.open(SEAL, encoding="utf-8") as fh:
            seal = fh.read()
        for line in ("**≥ 50%**", "**= 0 件**", "**≥ 80%**", "**≥ 20**"):
            self.assertIn(line, seal)


if __name__ == "__main__":
    unittest.main()
