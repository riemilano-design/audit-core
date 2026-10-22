# -*- coding: utf-8 -*-
"""修正前予測の封(docs/DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md)を門にする。

封じた件数・持ち越した合格線・やらないことが、**後から動かないこと**を見る。
診断の記録が出来たら、それが**合格の証拠に使われていないこと**も見る。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md")
M4SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M4_SEAL_2026-10-15.md")
RESULT = os.path.join(ROOT, "docs", "DOMAIN1_M4_RESULT_2026-10-15.md")
SCORE = os.path.join(ROOT, "fixtures", "sheet", "m4_score_2026-10-15.json")
DIAG = os.path.join(ROOT, "fixtures", "sheet", "m4_fix_diagnostic_2026-10-15.json")

# 封 §3-1 で「変わらない」と予測した行。壊したら失敗(§4 の検出条件)
MUST_NOT_BREAK = ("R004", "R007", "R008", "R009",
                  "R017", "R018", "R019", "R020", "R021", "R022")


def text(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


class SealTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_moved_row_counts_are_sealed(self):
        """§3-2 の件数。1 つでも書き換わったら赤。"""
        for s in ("**13 件**", "**11 件**", "**3 件**(R016・R023・R024)",
                  "**7 件**(R005・R006・R010〜R014)", "**2 件**(R002・R003)",
                  "**1 件**(R015"):
            self.assertIn(s, self.doc, s)

    def test_the_predicted_lines_are_sealed(self):
        for s in ("**75.0%(18/24)**", "**3 件**", "**0 件**", "**40.0%(2/5)**", "**24 件**"):
            self.assertIn(s, self.doc, s)

    def test_the_prediction_does_not_claim_a_pass(self):
        self.assertIn("予測しても総合は「失敗」のままである", self.doc)
        self.assertIn("この数で段 4 を合格扱いにしない", self.doc)
        self.assertIn("段 4 の判定は `1ea40d1` の**失敗で確定。**", self.doc)

    def test_the_six_fixes_each_have_their_own_section(self):
        for f in ("F-1", "F-2", "F-3", "F-4", "F-5", "F-6"):
            self.assertIn(f, self.doc, f)
        for c in ("C-1", "C-2", "C-3", "C-4", "C-5", "C-6", "C-7"):
            self.assertIn(c, self.doc, c)

    def test_identity_is_not_decided_by_the_string_alone(self):
        """人間の指示: 文字列が違うだけで同一と決めない。"""
        self.assertIn("文字列が違うだけで同一と決めない", self.doc)
        self.assertIn("**前方一致は認めない。**", self.doc)
        self.assertIn("値の裏づけ", self.doc)
        self.assertIn("別名候補・未確認", self.doc)

    def test_the_rows_that_must_not_break_are_named(self):
        """§4 の検出条件の行そのものを見る(文書のどこかに id が在るだけでは通さない)。"""
        hit = [l for l in self.doc.splitlines() if "正しい接続` から外れたら失敗" in l]
        self.assertEqual(len(hit), 1, hit)
        row = hit[0]
        for cid in MUST_NOT_BREAK:
            if cid in ("R018", "R019", "R020", "R021"):
                continue  # R017〜R022 の範囲表記に含まれる
            self.assertIn(cid, row, "%s が §4 の行に無い" % cid)
        self.assertIn("R017〜R022", row)
        self.assertIn("の %d 件が" % len(MUST_NOT_BREAK), row)
        self.assertIn("1 件でも外れたら原因を書いて止める", row)

    def test_tests_may_not_be_loosened_to_go_green(self):
        self.assertIn("試験を直して緑にするのは禁止", self.doc)

    def test_the_things_it_refuses_to_do(self):
        for s in ("閾値を緩めない。採点規則を変えない。分母を選び直さない。",
                  "今回のラベルを**取り直さない**",
                  "not_performance_evidence",
                  "他年度・他自治体に通じる証拠にしない"):
            self.assertIn(s, self.doc, s)

    def test_the_least_likely_predictions_are_disclosed(self):
        for s in ("(a)", "(b)", "(c)", "(d)", "(e)"):
            self.assertIn(s, self.doc, s)
        self.assertIn("外れようのない予測になる", self.doc)


class CarriedLinesTest(unittest.TestCase):
    """§6-1 は前回の封の線を**字句のまま**持ち越していること。"""

    LINES = ("≥ 50%", "= 0 件", "= 0 件", "≥ 80%", "≥ 20")

    SECTION = ("### 6-1", "### 6-2")
    ROWS = (("G-1 接続の正確さ", "≥ 50%"), ("G-2 誤接続", "= 0 件"),
            ("G-3 根拠なしの接続", "= 0 件"), ("G-4 保留の適切さ", "≥ 80%"),
            ("G-5 母数", "≥ 20 件"))

    def _carried_section(self):
        doc = text(DOC)
        a = doc.index(self.SECTION[0])
        b = doc.index(self.SECTION[1])
        return doc[a:b]

    def test_each_carried_line_is_a_row_of_the_carried_table(self):
        """§6-1 の表の行として見る。**文書の別の場所に同じ字が在っても通さない。**"""
        sec = self._carried_section()
        prev = text(M4SEAL)
        for name, line in self.ROWS:
            self.assertIn("| %s | %s |" % (name, line), sec, name)
            self.assertIn(line.replace(" 件", ""), prev, line)

    def test_the_carried_table_has_exactly_five_rows(self):
        sec = self._carried_section()
        rows = [l for l in sec.splitlines() if l.startswith("| G-")]
        self.assertEqual(len(rows), 5, rows)

    def test_the_carried_lines_match_the_frozen_score_record(self):
        s = json.load(io.open(SCORE, encoding="utf-8"))["lines"]
        self.assertEqual(s["G-1 接続の正確さ"]["pass"], "≥ 50%")
        self.assertEqual(s["G-2 誤接続"]["pass"], "= 0 件")
        self.assertEqual(s["G-3 根拠なしの接続"]["pass"], "= 0 件")
        self.assertEqual(s["G-4 保留の適切さ"]["pass"], "≥ 80%")
        self.assertEqual(s["G-5 母数"]["pass"], "≥ 20")

    def test_the_new_primary_metric_is_a_count_not_a_rate(self):
        self.assertIn("**E2 = 誤受理**", text(DOC))
        self.assertIn("率ではなく件数で報告する", text(DOC))
        self.assertIn("誤接続 0 件を母数なしで誇らない", text(DOC))


class ResultDocCorrectionTest(unittest.TestCase):
    """結果文書の追記が、件数の誤りを**直さずに訂正**していること。"""

    def setUp(self):
        self.res = text(RESULT)
        self.rows = json.load(io.open(SCORE, encoding="utf-8"))["rows"]

    def test_the_body_still_carries_the_original_wrong_count(self):
        """本文は書き換えない(**6 件が誤停止** のまま残っていること)。"""
        self.assertIn("**6 件が誤停止**", self.res)

    def test_the_addendum_corrects_it_to_the_measured_number(self):
        self.assertIn("**正しくは 7 件。**", self.res)
        unbound = [r["id"] for r in self.rows if r["verdict"].startswith("結べなかった")]
        self.assertEqual(len(unbound), 7, unbound)

    def test_the_addendum_discloses_the_four_lucky_correct_rows(self):
        self.assertIn("R017・R018・R020・R021", self.res)
        self.assertIn("値だけで 1 セルが選ばれていた", self.res)

    def test_the_overall_verdict_is_still_failure(self):
        self.assertEqual(json.load(io.open(SCORE, encoding="utf-8"))["overall"], "失敗")
        self.assertIn("§1 の総合「失敗」は動かさない", self.res)


class DiagnosticRecordTest(unittest.TestCase):
    """診断の記録が出来たら、合格の証拠に使われていないことを見る。"""

    def test_the_diagnostic_record_is_marked_as_not_evidence(self):
        if not os.path.exists(DIAG):
            self.skipTest("診断はまだ走っていない(修正前)")
        d = json.load(io.open(DIAG, encoding="utf-8"))
        self.assertTrue(d["not_performance_evidence"])
        self.assertNotIn("overall", d)
        self.assertNotIn("lines", d)

    def test_the_frozen_score_record_was_not_touched_by_the_fix(self):
        s = json.load(io.open(SCORE, encoding="utf-8"))
        self.assertEqual(s["overall"], "失敗")
        self.assertEqual(s["lines"]["G-1 接続の正確さ"]["num"], 10)
        self.assertEqual(s["lines"]["G-2 誤接続"]["count"], 5)


if __name__ == "__main__":
    unittest.main()
