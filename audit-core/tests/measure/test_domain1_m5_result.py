# -*- coding: utf-8 -*-
"""段 5 の結果(docs/DOMAIN1_M5_RESULT_2026-10-15.md)を固定する。

**失敗を失敗として残すこと**、外れた予測を外れたまま残すこと、
片方の席との一致を成績にしないことを門にする。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m5_score_2026-10-15.json")
BINDS = os.path.join(FX, "m5_binds_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M5_RESULT_2026-10-15.md")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M5_SEAL_2026-10-15.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)

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
        self.assertEqual((L["G-1 接続の正確さ"]["num"], L["G-1 接続の正確さ"]["den"]),
                         (19, 25))
        self.assertEqual(L["G-2 誤接続"]["count"], 5)
        self.assertEqual(L["G-3 根拠なしの接続"]["count"], 0)
        self.assertEqual((L["G-4 保留の適切さ"]["num"], L["G-4 保留の適切さ"]["den"]),
                         (1, 6))
        self.assertEqual(L["G-5 母数"]["count"], 25)
        self.assertEqual(self.s["E2_誤受理"], 5)

    def test_the_denominator_was_not_shrunk_by_disagreement(self):
        self.assertEqual(self.s["seats_agree_6"], 20)
        self.assertEqual(self.s["scorable"], 25)
        self.assertEqual(len(self.s["rows"]), 25)

    def test_the_split_is_recorded(self):
        self.assertEqual(self.s["split"], {"接続数": 24, "保留数": 1, "対象外数": 0})
        self.assertEqual(sum(self.s["hold_reasons"].values()), 1)

    def test_the_only_hold_is_the_equal_column_row(self):
        rows = {r["id"]: r for r in self.s["rows"]}
        self.assertEqual(rows["R010"]["verdict"], "正しく保留")
        self.assertIn("列 の手がかりが 2 つ以上", rows["R010"]["hold_reason"])

    def test_the_five_false_acceptances_differ_only_in_the_account_field(self):
        """原因は 1 つ。**`会計` の欄だけ**が食い違った。"""
        bad = [r for r in self.s["rows"] if not r["seats_agree"]]
        self.assertEqual([r["id"] for r in bad],
                         ["R021", "R022", "R023", "R024", "R025"])
        for r in bad:
            diff = [f for f, x, y in zip(("会計", "階層", "親", "科目名", "列", "値"),
                                         r["seat1"][1], r["seat2"][1]) if x != y]
            self.assertEqual(diff, ["会計"], r["id"])
            self.assertEqual(r["verdict"], "根拠なし/判定不能なのに接続した", r["id"])

    def test_the_novelty_rule_blocks_the_independence_claim(self):
        self.assertEqual(self.s["novelty"], {"再出": 19, "新規": 6})
        self.assertFalse(self.s["independent_confirmation"])

    def test_the_parent_field_changed_nothing_on_this_sample(self):
        self.assertEqual(self.s["reference_only"]["only_4"], 0)
        self.assertEqual(self.s["reference_only"]["agree_4"], 19)

    def test_no_route_other_than_r1_fired(self):
        self.assertEqual(self.s["routes"], {"R-1": 24})


class DocumentTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)
        self.rows = [[c.strip().replace("*", "").replace("`", "")
                      for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_each_pass_line_has_its_own_row_with_the_measured_value(self):
        for sym, got in (("G-1 接続の正確さ", "76.0%"), ("G-2 誤接続", "5 件"),
                         ("G-3 根拠なしの接続", "0 件"),
                         ("G-4 保留の適切さ", "16.7%"), ("G-5 母数", "25 件")):
            hit = self._row(sym)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (sym, len(hit)))
            self.assertTrue(any(got in c for c in hit[0]), "%s: %s" % (sym, hit[0]))

    def test_every_prediction_has_its_own_row_and_misses_are_kept(self):
        for i in range(1, 11):
            self.assertEqual(len(self._row("Q-%d" % i)), 1, "Q-%d" % i)
        self.assertIn("当たり 5 本・外れ 5 本", self.doc)
        self.assertIn("外れた 5 本は外れたまま記録する", self.doc)

    def test_it_says_it_failed(self):
        self.assertIn("**失敗**", self.doc)
        self.assertIn("総合: 失敗。主指標 E2(誤受理)= 5 件", self.doc)

    def test_it_refuses_to_claim_the_engine_was_right(self):
        self.assertIn("engine が正しかったとは、この結果からは言えない", self.doc)
        self.assertIn("片方の席と一致した数を成績にするのは", self.doc)
        self.assertIn("**総合は失敗のまま。再採点しない。**", self.doc)
        self.assertIn("engine は席 2 と 24/25 一致したから実質合格", self.doc)

    def test_it_names_the_cause_as_its_own_question(self):
        self.assertIn("封と、席に渡した問いが食い違っていた", self.doc)
        self.assertIn("席に渡す問いにその規則を写していなかった", self.doc)
        self.assertIn("席に渡す問いの字へ写していなかった", self.doc)
        self.assertIn("席の誤りではない", self.doc)
        self.assertIn("2 回続けて、問いが原因だった", self.doc)

    def test_it_refuses_to_generalise_the_single_hold(self):
        self.assertIn("「保留は 1 件だけだった」を一般化できない", self.doc)
        self.assertIn("別名の規則は、この報告文では 1 件も効いていない", self.doc)
        self.assertIn("未確認の 18 会計について、保留がどれだけ増えるかは測っていない",
                      self.doc)

    def test_it_refuses_the_independence_wording(self):
        self.assertIn("「別の報告文で独立に確認した」とは表現しない", self.doc)
        self.assertIn("同じ材料・似た報告文での再測定", self.doc)

    def test_it_does_not_celebrate_g1(self):
        self.assertIn("G-1 が合格線を越えたが、合格ではない", self.doc)
        self.assertIn("1 本だけ取り出して「76% 当たった」と書かない", self.doc)

    def test_the_seal_thresholds_are_unchanged(self):
        seal = text(SEAL)
        for line in ("| G-1 接続の正確さ | ≥ 50% |", "| G-2 誤接続 | = 0 件 |",
                     "| G-4 保留の適切さ | ≥ 80% |", "| G-5 母数 | ≥ 20 件 |"):
            self.assertIn(line, seal, line)


class NextStepsTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_first_next_step_is_a_gate_on_the_question(self):
        self.assertIn("封の欄の規則と、席に渡す問いの字を、機械で突き合わせる門を作る",
                      self.doc)
        self.assertIn("封の規則文と問いの字が一致しない限り材料を作れない", self.doc)

    def test_the_untested_holes_are_listed(self):
        for s in ("未確認の会計を含む抜粋", "親の欄が効く行", "新規の主張を 10 件以上"):
            self.assertIn(s, self.doc, s)


if __name__ == "__main__":
    unittest.main()
