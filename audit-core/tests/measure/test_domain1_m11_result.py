# -*- coding: utf-8 -*-
"""段 11 の結果の文書(docs/DOMAIN1_M11_RESULT_2026-10-16.md)を記録に結び付ける。

**文書の数は記録(fixtures)が正本である。**ずれたら赤くする。
守るのは 10 つ。
  1. **三層(判定 / 観測 / 解釈)**に分かれていること(人間の指示)
  2. **総合が失敗**と書かれ、合格と書かれていないこと
  3. 7 本の線の数が**記録と一致**すること
  4. **増分 0 件**・**解除は起きていない**と書かれていること
  5. **診断が再現しなかった理由**(鍵が一意にならない)が在ること
  6. **β = 0 の空振り**を安全性の証拠にしないと書かれていること
  7. **X-2 が未測定でない**根拠(結んだ主張 16 件・機会 466 行)が記録と一致
  8. 費用・回数が**記録と一致**すること
  9. 予測の照合が **16 本**在り、**外れを外れと書いている**こと
 10. 限界、特に **6 段続けて未検証**・**人工材料は実データの証明でない**・
     **6a・6b は安全の規則ではない**・**顧客価値は証明されていない**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M11_RESULT_2026-10-16.md")


def load(name):
    with io.open(os.path.join(FX, name), encoding="utf-8") as fh:
        return json.load(fh)


class ResultDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with io.open(DOC, encoding="utf-8") as fh:
            cls.t = fh.read()
        cls.score = load("m11_score_2026-10-16.json")
        cls.binds = load("m11_binds_2026-10-16.json")
        cls.opp = load("m11_opportunity_2026-10-16.json")
        cls.rep = load("m11_report_2026-10-16.json")
        cls.mat = load("m11_material_2026-10-16.json")

    def test_1_three_layers(self):
        for k in ("# 第 1 層 ― 判定", "# 第 2 層 ― 観測", "# 第 3 層 ― 解釈"):
            self.assertIn(k, self.t, k)
        self.assertIn("判定 / 観測 / 解釈の三層", self.t)

    def test_2_the_verdict_is_failure(self):
        self.assertIn("**総合判定: 失敗。**", self.t)
        self.assertIn("**6 本通って 1 本落ちた → 失敗**", self.t)
        self.assertIn("**線を動かさない。**", self.t)
        self.assertIn("**2 回続けて同じ線で落ちている。**", self.t)
        self.assertIn("失敗", self.score["主実験の判定"])

    def test_3_line_numbers_match_the_record(self):
        lines = self.score["主実験の線(7 本)"]
        g1p = lines["G-1′(新)③で止めた主張を除いた接続の正確さ"]
        self.assertIn("**%.1f%%(%d/%d)**" % (g1p["rate"] * 100, g1p["num"],
                                             g1p["den"]), self.t)
        self.assertIn("| A-1(旧) | 旧 engine で③が発火した主張 | **%d 件** | ≥ 1 件 | ○ |"
                      % lines["A-1(旧)③が発火した主張"]["count"], self.t)
        self.assertIn("**%d 件** | ≥ 20 | ○" % lines["G-5 母数"]["count"], self.t)

    def test_4_the_increment_is_zero_and_no_release_happened(self):
        inc = self.score["記録のみ(線にしない)"]["N-接続-増(合否に入れない)"]
        self.assertEqual(inc["count"], 0)
        self.assertIn("**N-接続-増 = 0 件**", self.t)
        self.assertIn("**解除は起きていない。**", self.t)
        self.assertIn("「**安全に解除できた**」ではなく", self.t)

    def test_5_why_the_diagnosis_did_not_transfer(self):
        self.assertIn("**診断(P-5)の +12 件が再現しなかった ― 理由を測った**",
                      self.t)
        self.assertIn("**別名を直しても 6 欄が一意にならない。**", self.t)
        self.assertIn("標本の性質に懸かっていた", self.t)
        self.assertIn("**診断は性能の予測にならない**", self.t)
        shrank = sum(1 for b in self.binds["binds_new"]
                     if (b.get("distinct_keys") or 0) <
                     ({x["claim_id"]: x for x in self.binds["binds_old"]}
                      [b["claim_id"]].get("distinct_keys") or 0))
        self.assertEqual(shrank, 7, "鍵の通り数が減った主張の数が文書と違う")
        self.assertIn("**7 件で 6 欄の鍵の通り数が減った**", self.t)

    def test_6_beta_vacuous_is_disclosed(self):
        b = self.score["β と 5 欄(封 §5。循環を切る)"]
        self.assertEqual(b["β 別名表に依って一致した主張"], 0)
        self.assertIn("**β = 0 件。**", self.t)
        self.assertIn("**空振りを「安全性の証拠」として書かない。**", self.t)
        self.assertIn("**解決したのではない。**", self.t)

    def test_7_x2_is_not_unmeasured(self):
        x = self.score["X-2 の 3 通り(封 §4)"]
        self.assertEqual(x["結んだ主張"], 16)
        self.assertIn("結んだ主張が **16 件**在り", self.t)
        o8 = self.opp["O-8 X-2 の機会(新。封 §4)"]
        self.assertIn("**%d 行**" % o8["O-8 索引に在って抜粋に無い行"], self.t)
        self.assertIn("**{:,} 件**".format(o8["O-8′ 抜粋に無い行だけが持つ値"]), self.t)
        self.assertIn("**X-2 は未測定ではない**", self.t)

    def test_8_cost_and_runs_match(self):
        self.assertEqual(self.rep["runs"], 1)
        self.assertIn("**{:,} トークン**".format(
            self.rep["cost"]["使ったトークン(実測)"]).replace("**", ""), self.t)
        self.assertIn("**2.89 USD**", self.t)
        self.assertIn("やり直し | **0 回**", self.t)
        self.assertIn("{:,} 字(上限 {:,})".format(
            self.rep["report_chars"], self.rep["limit_report_chars"]), self.t)
        self.assertTrue(self.rep["cost"]["上限の中か"])

    def test_9_sixteen_predictions_with_misses_named(self):
        block = self.t.split("## §2-6")[1].split("# 第 3 層")[0]
        ids = re.findall(r"(?m)^\| U-(\d+) \|", block)
        self.assertEqual(ids, [str(i) for i in range(1, 17)], "予測は 16 本")
        self.assertIn("**外れ**", block)
        self.assertIn("**半分外れ**", block)
        self.assertIn("**外れは 4 本 + 半分外れ 3 本。**", block)
        self.assertIn("**予測は封のまま編集していない。**", block)
        self.assertEqual(block.count("**外れ**"), 4, "外れの数が合わない")
        self.assertEqual(block.count("**半分外れ**"), 3)

    def test_10_limits_are_stated(self):
        block = self.t.split("## §3-2")[1].split("## §3-3")[0]
        self.assertIn("6 段続けて未検証である。**", block)
        self.assertIn("は人工材料であり、実データの証拠ではない。**", block)
        self.assertIn("**6a・6b は独立性の規則であり、安全の規則ではない**", block)
        self.assertIn("閾値 3 と値の完全一致である", block)
        self.assertIn("**顧客価値は証明されていない**", block)
        self.assertIn("**「別名規則の安全性が改善した」とも書かない。**", block)

    def test_11_the_next_question_changed(self):
        block = self.t.split("## §3-3")[1].split("## §4")[0]
        self.assertIn("**「6 欄の鍵が一意にならない主張を、安全に 1 本に絞れるか」である。**",
                      block)
        self.assertIn("**この判断は人間に出す。**", block)
        self.assertIn("**どれも未検証。ここで決めない**", block)

    def test_12_seal_correspondence(self):
        block = self.t.split("## §4 封との対応")[1]
        self.assertIn("**全部一致**", block)
        self.assertIn("**段 9 と 1 文字も同じ**", block)
        self.assertIn("**ラベルより先**", block)
        self.assertIn("**失敗を記録して終える。再調整はしない。**", block)
        self.assertEqual(self.score["min_independent"], 3)


if __name__ == "__main__":
    unittest.main()
