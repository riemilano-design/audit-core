# -*- coding: utf-8 -*-
"""段 7 の診断(docs/DOMAIN1_M7_DIAGNOSTIC_2026-10-15.md)を固定する。

守るのは 5 つ。
  1. **診断であって性能の証拠ではない**という印が消えないこと
  2. 予測を**封の文書から読んで**いること(script に数を写していない)
  3. **外れた D-6 が外れたまま**残ること(私の写し間違いも)
  4. **段 6 の 13 件が壊れていないこと**と、**①が②に侵入していないこと**
  5. N-1(親が取れた)と N-3(接続できた)を**別に**書いていること
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "m7_diagnostic_2026-10-15.json")
M6S = os.path.join(FX, "m6_score_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M7_DIAGNOSTIC_2026-10-15.md")
SCRIPT = os.path.join(ROOT, "measure", "sheet_m7_diagnostic_2026-10-15.py")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M7_SEAL_2026-10-15.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class NotEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)
        self.d = text(DOC)

    def test_the_record_marks_itself_as_not_performance_evidence(self):
        self.assertTrue(self.r["not_performance_evidence"])
        self.assertEqual(self.r["applied_times"], 1)

    def test_the_doc_title_says_it_is_not_an_evaluation(self):
        self.assertIn("**性能の評価ではない**", self.d.split("\n")[0])

    def test_the_doc_discloses_that_i_already_read_the_sentences(self):
        self.assertIn("**私は段 6 の 25 件の文を既に読んでいるので、"
                      "ここで当たっても一般に効く証拠にはならない。**", self.d)

    def test_stage_6_verdict_is_not_touched(self):
        self.assertIn("**段 6 の合否は動かさない**", self.d)
        self.assertIn("段 6 の G-1 52.0% と総合「合格」は `c4e84e8` のまま動かない。", self.d)
        self.assertEqual(load(M6S)["overall"], "合格")
        self.assertEqual(load(M6S)["lines"]["G-1 接続の正確さ"]["num"], 13)


class PredictionFromTheSealTest(unittest.TestCase):
    def test_the_script_reads_the_prediction_from_the_document(self):
        src = text(SCRIPT)
        self.assertIn("def read_prediction()", src)
        self.assertIn("DOMAIN1_M7_SEAL_2026-10-15.md", src)
        self.assertIn("script に数を写さない", src)
        self.assertEqual(load(REC)["prediction_read_from"],
                         "docs/DOMAIN1_M7_SEAL_2026-10-15.md §7")

    def test_the_script_refuses_a_group_whose_count_and_ids_disagree(self):
        """封の群の件数と id の数が合わなければ**例外で止まる**こと。"""
        src = text(SCRIPT)
        self.assertIn("raise AssertionError(\"封の群 %r は %d 件と書いてあるが id は %d 件\"",
                      src)
        self.assertIn('raise AssertionError("封の群の id が 25 件でない: %d" % len(rows))',
                      src)

    def test_every_row_hit_its_sealed_prediction(self):
        r = load(REC)
        self.assertEqual((r["scorable"], r["prediction_hits"], r["prediction_misses"]),
                         (25, 25, 0))
        self.assertIn("**25 件すべて予測どおり。外れ 0 件。**", text(DOC))


class MissIsKeptTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_d6_is_recorded_as_a_miss(self):
        m = re.search(r"\| D-6 \|.*?\|.*?\|\s*\*\*外れ(.*?)\*\*\s*\|", self.d)
        self.assertTrue(m, "D-6 が『外れ』で残っていない")

    def test_the_miss_names_my_own_transcription_error(self):
        self.assertIn("**変わる元の並びを間違えて書いた。**", self.d)
        self.assertIn("`427` を先頭に書いたのは私の写し間違いである", self.d)
        self.assertIn("**直さずに外れとして残す。**", self.d)

    def test_the_other_error_in_the_seal_is_disclosed_too(self):
        self.assertIn("**封 §7 の `理由` の欄にも誤りが在る。**", self.d)
        self.assertIn("実装の順序は**列で 61 → 親で 1** である", self.d)

    def test_the_old_reasons_in_the_record_match_what_the_doc_says(self):
        rows = {x["id"]: x for x in load(REC)["rows"]}
        want = {"R026": 30, "R027": 427, "R028": 427, "R025": 61}
        for cid, n in want.items():
            self.assertIn("%d 通り" % n, rows[cid]["old_hold"], cid)
        self.assertIn("R026 **30** / R027 **427** / R028 **427**", self.d)

    def test_the_seal_still_contains_the_wrong_numbers(self):
        """**封は直さない。**外れた字が封に残っていること。"""
        self.assertIn("**427 / 30 / 427 通り**", text(SEAL))
        self.assertIn("427 → 7 候補、列で 1 件", text(SEAL))


class RegressionAndScopeTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)
        self.d = text(DOC)

    def test_no_stage_6_bind_broke(self):
        self.assertEqual(self.r["broke_stage6_binds"], [])
        self.assertIn("| **段 6 の接続が壊れた主張** | **0 件** |", self.d)

    def test_only_one_row_changed_state(self):
        self.assertEqual(self.r["changed_state"], ["R025"])
        self.assertEqual((self.r["grounded_old"], self.r["grounded_new"],
                          self.r["grounded_delta"]), (13, 14, 1))

    def test_the_kan_kou_twins_are_still_held(self):
        """**①が②へ侵入していない**ことの門。ここが緑のまま 4 件が接続に変わったら赤。"""
        rows = {x["id"]: x for x in self.r["rows"]}
        for cid in ("R016", "R017", "R022", "R023"):
            self.assertNotEqual(rows[cid]["new_state"], "GROUNDED", cid)
            self.assertEqual(rows[cid]["old_hold"], rows[cid]["new_hold"], cid)
            self.assertFalse(rows[cid]["parent_filtered"], cid)
        self.assertIn("**4 件とも保留のまま**", self.d)
        self.assertIn("**そうしなかった。**", self.d)

    def test_the_doc_says_the_twins_would_have_bound_if_p5_were_loosened(self):
        self.assertIn("**親の無い行を既定にすれば 4 件が接続に変わった。**", self.d)


class FiveCountsTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)
        self.d = text(DOC)

    def test_the_counts_are_recorded_separately(self):
        self.assertEqual(self.r["N-1_親を正しく抽出"], 4)
        self.assertEqual(self.r["N-2_親を誤って抽出"], 0)
        self.assertEqual(self.r["N-1_判定できず"], 0)
        self.assertEqual(self.r["診断の E2"], 0)

    def test_n1_is_not_used_as_evidence_for_n3(self):
        self.assertIn("**N-1 = 4 件に対し、接続が増えたのは 1 件だけである。**", self.d)
        self.assertIn("**親が正しく取れても、列が分からなければ接続にならない。**", self.d)
        self.assertIn("**N-1 を N-3 の証拠にしない**", self.d)

    def test_the_e2_zero_is_labelled_as_a_diagnostic_number(self):
        self.assertIn("**診断の数**", self.d)
        self.assertIn("**新しい報告文での E2 は、まだ 1 件も測っていない。**", self.d)
        self.assertIn("段 6 の合否は動かさない", self.r["E2_note"])

    def test_the_parent_filter_numbers_in_the_doc_match_the_record(self):
        rows = {x["id"]: x for x in self.r["rows"]}
        for cid, before, after in (("R025", 61, 1), ("R026", 32, 7),
                                   ("R027", 427, 7), ("R028", 427, 7)):
            self.assertEqual((rows[cid]["parent_before"], rows[cid]["parent_after"]),
                             (before, after), cid)
            self.assertIn("| %s | %d | " % (cid, before), self.d)


class CannotClaimTest(unittest.TestCase):
    def setUp(self):
        self.d = text(DOC)

    def test_the_doc_refuses_to_claim_performance(self):
        self.assertIn("**性能が上がったとは言えない。**", self.d)
        self.assertIn("**接続が増えるとは言えない。**", self.d)
        self.assertIn("**誤った親を取る危険が無いとは言えない。**", self.d)
        self.assertIn("**正しい親を与えても一意にならない行が 262 行**在る", self.d)

    def test_the_doc_refuses_generalisation(self):
        self.assertIn("他の自治体・他の年度・一般の会計資料に通じるとは結論しない", self.d)

    def test_the_doc_warns_that_the_next_sample_may_be_unmeasured(self):
        self.assertIn("**報告文が列の名前を書かなければ接続にならない。**", self.d)
        self.assertIn("**報告文の書き方を誘導しない。**", self.d)
        self.assertIn("`未測定` になる可能性が在ることを、先に書いておく", self.d)

    def test_the_doc_stops_before_the_new_sample(self):
        self.assertIn("**ここで人間の判断を仰ぐ**", self.d)


if __name__ == "__main__":
    unittest.main()
