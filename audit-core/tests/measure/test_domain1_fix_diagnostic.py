# -*- coding: utf-8 -*-
"""24 件の診断(docs/DOMAIN1_FIX_DIAGNOSTIC_2026-10-15.md)を門にする。

いちばん大事な門は「**この数が性能の証拠として使われていないこと**」である。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "DOMAIN1_FIX_DIAGNOSTIC_2026-10-15.md")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_FIX_PREDICTION_SEAL_2026-10-15.md")
DIAG = os.path.join(ROOT, "fixtures", "sheet", "m4_fix_diagnostic_2026-10-15.json")
SCORE = os.path.join(ROOT, "fixtures", "sheet", "m4_score_2026-10-15.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class NotEvidenceTest(unittest.TestCase):
    """**この 24 件を性能の証拠にしない**(人間の指示)。"""

    def setUp(self):
        self.d = json.load(io.open(DIAG, encoding="utf-8"))
        self.doc = text(DOC)

    def test_the_record_is_flagged(self):
        self.assertTrue(self.d["not_performance_evidence"])
        self.assertIn("新しい性能の証拠に", self.d["human_instruction"])

    def test_the_record_carries_no_pass_lines(self):
        """合格線を 1 本も計算していないこと。"""
        for k in ("overall", "lines", "G-1", "pass"):
            self.assertNotIn(k, self.d)

    def test_it_was_applied_once(self):
        self.assertEqual(self.d["applied_times"], 1)
        self.assertIn("取り直していない", self.d["labels"])

    def test_the_document_refuses_to_claim_performance(self):
        for s in ("性能の数として読んではいけない",
                  "段 4 の判定は `1ea40d1` の「失敗」で確定している",
                  "この 17/24 を**性能の数として報告しない**"):
            self.assertIn(s, self.doc, s)

    def test_the_frozen_failure_record_is_untouched(self):
        s = json.load(io.open(SCORE, encoding="utf-8"))
        self.assertEqual(s["overall"], "失敗")
        self.assertEqual(s["lines"]["G-1 接続の正確さ"]["num"], 10)
        self.assertEqual(s["lines"]["G-2 誤接続"]["count"], 5)


class PredictionDiffTest(unittest.TestCase):
    """予測と実測の差が、**外れたまま**記録されていること。"""

    def setUp(self):
        self.d = json.load(io.open(DIAG, encoding="utf-8"))
        self.doc = text(DOC)

    def test_the_row_level_hits_and_misses(self):
        self.assertEqual(self.d["prediction_hits"], 23)
        self.assertEqual(self.d["prediction_misses"], 1)
        miss = [r["id"] for r in self.d["rows"] if not r["prediction_hit"]]
        self.assertEqual(miss, ["R007"])

    def test_the_misses_are_written_as_misses(self):
        for s in ("**外れ**(R007 が増えた)", "**外れ**", "**24 件中 23 件 当たり・1 件 外れ**"):
            self.assertIn(s, self.doc, s)

    def test_the_counts_match_the_record(self):
        c = self.d["counts"]
        self.assertEqual(c["動いた"], 14)
        self.assertEqual(c["動かない"], 10)
        self.assertEqual(c["GROUNDED から保留へ"], 4)
        self.assertEqual(c["未接続から正しい接続へ"], 7)
        self.assertEqual(c["保留から誤受理へ"], 2)
        self.assertEqual(c["残る誤受理"], 3)

    def test_the_sealed_numbers_are_still_the_sealed_numbers(self):
        """封の予測は**書き換えられていない**(13 件・75.0% のまま)。"""
        seal = text(SEAL)
        self.assertIn("**13 件**", seal)
        self.assertIn("**75.0%(18/24)**", seal)

    def test_the_diagnostic_quotes_both_sealed_and_measured(self):
        self.assertIn("| 状態が動く件数 | 13 件 | **14 件** |", self.doc)
        self.assertIn("70.8%(17/24)", self.doc)

    def test_the_hold_count_did_not_improve(self):
        """G-4 は 1 ポイントも動かない(率の中身が入れ替わっただけ)。"""
        v = self.d["verdicts"]
        self.assertEqual(v["正しく保留"], 2)
        self.assertIn("40.0% の中身が入れ替わっただけ", self.doc)
        held = {r["id"] for r in self.d["rows"] if r["after"] == "正しく保留"}
        self.assertEqual(held, {"R023", "R024"})


class HoldReasonTest(unittest.TestCase):
    """保留した 4 件が、**理由を名前で持っている**こと。"""

    def setUp(self):
        self.d = json.load(io.open(DIAG, encoding="utf-8"))

    def test_every_hold_has_a_reason(self):
        held = [r for r in self.d["rows"] if r["state"] != "GROUNDED"]
        self.assertEqual(len(held), 4)
        for r in held:
            self.assertTrue(r["hold_reason"], r["id"])
            self.assertIsNone(r["route"], r["id"])

    def test_the_equal_column_rows_hold_for_the_right_reason(self):
        rows = {r["id"]: r for r in self.d["rows"]}
        for cid in ("R023", "R024"):
            self.assertIn("列の手がかりが 2 つ以上", rows[cid]["hold_reason"], cid)
            self.assertEqual(rows[cid]["column_ambiguous"], ["歳入決算額", "歳出決算額"], cid)

    def test_the_non_unique_rows_hold_without_using_the_value(self):
        rows = {r["id"]: r for r in self.d["rows"]}
        for cid, keys in (("R007", 2), ("R016", 7)):
            self.assertIn("値で選ばない", rows[cid]["hold_reason"], cid)
            self.assertEqual(rows[cid]["distinct_keys"], keys, cid)


class NewFindingsTest(unittest.TestCase):
    """新たに見つけた 2 つが、**次の封へ送られていること**。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_c8_the_level_cue_is_recorded_and_not_fixed_now(self):
        self.assertIn("C-8", self.doc)
        self.assertIn("階層の手がかり", self.doc)
        self.assertIn("**今回は直さない**", self.doc)

    def test_c9_the_answer_shape_cannot_identify_a_moku_row(self):
        self.assertIn("C-9", self.doc)
        self.assertIn("55 行", self.doc)
        self.assertIn("engine の欠陥ではなく、封が決めた「答えの形」の欠陥", self.doc)

    def test_the_value_backing_is_disclosed_as_unexercised(self):
        self.assertIn("実物では 1 件も落としていない", self.doc)
        self.assertIn("条件 3 が効いていることを示せていない", self.doc)
        self.assertIn("「効いた」と書かない", self.doc)

    def test_the_thin_alias_evidence_is_disclosed(self):
        self.assertIn("2 本が 17 件", self.doc)
        d = json.load(io.open(DIAG, encoding="utf-8"))
        thin = [k for k, v in d["alias"]["table"].items()
                if v["evidence"]["一致した款と列"] <= 2]
        self.assertEqual(len(thin), 17)
        self.assertEqual(d["alias"]["unconfirmed"], [])
        self.assertEqual(d["alias"]["fan_in"], {})

    def test_the_ambiguous_sealed_wording_is_disclosed_not_rewritten(self):
        self.assertIn("封の §3-2 の 1 行は字が曖昧だった", self.doc)
        self.assertIn("**封の字を今から直さない。**", self.doc)
        self.assertIn("**0 件 / 1 件**", self.doc)

    def test_the_pyc_trap_is_disclosed(self):
        self.assertIn("pyc の罠", self.doc)


class AliasTest(unittest.TestCase):
    def setUp(self):
        self.d = json.load(io.open(DIAG, encoding="utf-8"))

    def test_every_alias_is_a_suffix_with_zero_disagreement(self):
        for name, rec in self.d["alias"]["table"].items():
            self.assertTrue(name.replace(" ", "").endswith(rec["canonical"]), name)
            self.assertEqual(rec["evidence"]["食い違い"], 0, name)
            self.assertGreaterEqual(rec["evidence"]["一致した款と列"], 1, name)

    def test_no_item_level_name_became_an_alias(self):
        """`公債費`(款)のような科目名が別名表に入っていないこと。"""
        for name, rec in self.d["alias"]["table"].items():
            self.assertTrue(rec["canonical"].endswith("会計"), rec["canonical"])


if __name__ == "__main__":
    unittest.main()
