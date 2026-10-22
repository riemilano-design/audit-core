"""段 4 の封を門にする(**報告文を生成する前に** commit される試験)。

守るのは 3 つ。
  1. 封の字と材料の script が食い違わないこと(モデル・上限・行数・指示文)
  2. 生成側に渡さないものが材料に**混ざっていない**こと(盲検)
  3. 合格線・分母・除外・予測が封に在り、後から足せないこと
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M4_SEAL_2026-10-15.md")
MAT = os.path.join(ROOT, "fixtures", "sheet", "m4_material_2026-10-15.json")
SCRIPT = os.path.join(ROOT, "measure", "sheet_m4_material_2026-10-15.py")

spec = importlib.util.spec_from_file_location("m4mat", SCRIPT)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class SealTest(unittest.TestCase):
    def setUp(self):
        with io.open(SEAL, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in
                      l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]
        self.mat = json.load(io.open(MAT, encoding="utf-8"))

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_the_five_pass_lines_each_have_their_own_row(self):
        want = {"G-1 接続の正確さ": "≥ 50%", "G-2 誤接続": "= 0 件",
                "G-3 根拠なしの接続": "= 0 件", "G-4 保留の適切さ": "≥ 80%",
                "G-5 母数": "≥ 20"}
        for sym, line in want.items():
            hit = self._row(sym)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (sym, len(hit)))
            self.assertTrue(any(line in c for c in hit[0]), "%s: %s" % (sym, hit[0]))

    def test_the_six_predictions_each_have_their_own_row(self):
        for sym in ("P-1", "P-2", "P-3", "P-4", "P-5", "P-6"):
            self.assertEqual(len(self._row(sym)), 1, sym)

    def test_the_prediction_contradicts_the_pass_line_on_purpose(self):
        """P-2 は 1〜3 件、G-2 は 0 件。**予測が当たれば失敗する**ことを封が書いている。"""
        self.assertIn("予測が当たれば段 4 は失敗する", self.doc)
        self.assertTrue(any("0 件とは予測しない" in c for c in self._row("P-2")[0]))

    def test_the_seal_forbids_tuning_after_the_result(self):
        self.assertIn("同じ報告文で規則を直して再採点し、合格扱いにしない", self.doc)
        self.assertIn("合格線を動かさず「この基準では判定不能」と記録する", self.doc)

    def test_the_seal_refuses_to_reuse_stage3_as_evidence(self):
        self.assertIn("接続精度の実績として数えない", self.doc)
        self.assertIn("段 3 の 1,061/1,061 を根拠にしない", self.doc)

    def test_the_seal_has_the_independent_check_procedure(self):
        self.assertIn("人が独立に確かめる手順", self.doc)
        self.assertIn("この手順だけで確かめられないラベルは、確定ラベルにしない", self.doc)

    def test_the_two_label_seats_use_different_models(self):
        self.assertIn("Claude Haiku", self.doc)
        self.assertIn("主張の並びを逆順", self.doc)

    def test_the_engine_must_be_committed_before_generation(self):
        self.assertIn("engine(主張の切り出しと接続)の実装", self.doc)
        self.assertIn("報告文を見てから書かない", self.doc)

    def test_the_exclusions_are_defined_before_the_text_exists(self):
        for word in ("対象外(分母に入れない。事前に定義)", "判定不能(分母に入れる。除外しない)",
                     "都合の悪い主張を後から除外しない"):
            self.assertIn(word, self.doc)


class MaterialTest(unittest.TestCase):
    def setUp(self):
        self.mat = json.load(io.open(MAT, encoding="utf-8"))
        with io.open(SEAL, encoding="utf-8") as fh:
            self.doc = fh.read()

    def test_the_model_and_run_count_match_the_seal(self):
        self.assertEqual(self.mat["model"], S.MODEL)
        self.assertEqual(self.mat["runs"], 1)
        self.assertIn(S.MODEL, self.doc)

    def test_the_limits_match_the_seal(self):
        self.assertEqual(self.mat["limits"], {"extract_chars": 24000, "report_chars": 1200})
        self.assertIn("24,000 字以内", self.doc)
        self.assertIn("1,200 字以内", self.doc)
        self.assertLessEqual(self.mat["extract_chars"], 24000)

    def test_the_row_counts_are_the_sealed_rule(self):
        self.assertEqual(self.mat["counts"], {"表1_行": 20, "表2_行": 37, "表3_行": 60})
        self.assertEqual(S.MOKU_HEAD, 60)
        self.assertIn("20 行", self.doc)
        self.assertIn("款 37 件すべて", self.doc)
        self.assertIn("先頭から 60 件", self.doc)

    def test_the_prompt_is_the_sealed_wording(self):
        for line in ("この表だけを根拠に", "金額を少なくとも 15 か所",
                     "表に無い数は書かない", "本文だけを書いてください"):
            self.assertIn(line, self.mat["prompt"])
            self.assertIn(line, self.doc)

    def test_the_material_leaks_nothing_from_the_engine(self):
        """前回の反省: 材料のファイル全体を読む(note 欄から漏れた前例)。"""
        blob = json.dumps(self.mat, ensure_ascii=False)
        for banned in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND",
                       "range_identified", "value_match", "C-1", "C-7", "pointer"):
            self.assertNotIn(banned, self.mat["prompt"], banned)
        self.assertEqual(sorted(self.mat["withheld"])[:2], ["engine の判定", "仕様"])
        self.assertNotIn("1,061", blob)

    def test_the_extract_is_built_by_rule_not_by_choice(self):
        self.assertIn("内容で選ばない", self.mat["rule"])
        self.assertIn("これは規則の帰結であり、選んだのではない", self.doc)

    def test_the_material_script_refuses_to_rebuild(self):
        with self.assertRaises(SystemExit):
            S.main()


if __name__ == "__main__":
    unittest.main()
