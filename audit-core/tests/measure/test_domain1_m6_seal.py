# -*- coding: utf-8 -*-
"""段 6 の封(docs/DOMAIN1_M6_SEAL_2026-10-15.md)を門にする。"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M6_SEAL_2026-10-15.md")
M5SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M5_SEAL_2026-10-15.md")
M5SCORE = os.path.join(ROOT, "fixtures", "sheet", "m5_score_2026-10-15.json")
SCORER = os.path.join(ROOT, "measure", "sheet_m6_score_2026-10-15.py")
LABELER = os.path.join(ROOT, "measure", "sheet_m6_label_material_2026-10-15.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def section(doc, a, b=None):
    i = doc.index(a)
    j = doc.index(b) if b else len(doc)
    return doc[i:j]


class HumanInstructionTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_three_instructions_are_quoted(self):
        for s in ("封に書いた正解規則が、採点者に渡す問いへ正確に転記されなかった",
                  "実験手順そのものの欠陥として塞ぐべきです",
                  "問いを直した後、今回の同じ報告文を再採点してはいけません",
                  "正解の定義を実験の最後まで一貫して守る仕組みを作ること"):
            self.assertIn(s, self.doc, s)

    def test_stage5_is_not_rescored(self):
        self.assertIn("段 5 の報告文を再採点しない", self.doc)
        self.assertIn("新しい規則は段 6 から適用", self.doc)
        self.assertEqual(json.load(io.open(M5SCORE, encoding="utf-8"))["overall"], "失敗")


class MechanismTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_question_is_generated_from_a_single_spec(self):
        sec = section(self.doc, "### 1-1.", "### 1-2.")
        self.assertIn("`SPEC` から問いを組み立てる", sec)
        self.assertIn("問いの字を手で書かない", sec)
        self.assertIn("一つでも欠けたら例外で止まり、ラベル材料を作れない", sec)

    def test_the_missing_rule_from_stage5_is_now_in_the_question(self):
        sec = section(self.doc, "### 1-2.", "### 1-3.")
        self.assertIn("`東京都` を外した表 1 の名前", sec)
        self.assertIn("段 5 の失敗の全部(誤受理 5 件)がこの 1 行の欠落だった", sec)

    def test_the_builder_has_no_hand_written_question(self):
        src = text(LABELER)
        self.assertNotIn("QUESTION = ", src)
        self.assertIn("L.check_question(question)", src)

    def test_string_equality_is_not_identity(self):
        self.assertIn("文字列を揃えることと、対象が同一であることは別", self.doc)
        self.assertIn("裏づけの無い `東京都○○会計` は**直さない**", self.doc)


class RepresentationTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_all_six_fields_have_a_row(self):
        sec = section(self.doc, "## 2. 表記の割れ", "### 2-2.")
        for f in ("会計", "階層", "親", "科目名", "列", "値"):
            self.assertIn("| %s |" % f, sec, f)

    def test_the_value_only_pairs_are_refused(self):
        sec = section(self.doc, "### 2-2.", "## 3.")
        self.assertIn("| `予算現額` | `計` | 92 |", sec)
        self.assertIn("**した**", sec)
        self.assertIn("**しない**", sec)
        self.assertIn("値が 49 行・28 行も一致していても、構造の証拠が無いので同一と決めない",
                      sec)


class SampleTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_three_conditions_each_have_a_row(self):
        sec = section(self.doc, "## 3. 標本", "### 3-1.")
        for c in ("未確認の会計を含む", "親が効く行を含む", "新規 10 件以上"):
            self.assertIn("| %s |" % c, sec, c)
        self.assertIn("**14 会計**", sec)
        self.assertIn("**31 行 / 14 会計**", sec)
        self.assertIn("**34 通りの親**", sec)

    def test_novelty_is_not_generalisation(self):
        sec = section(self.doc, "### 3-1.", "## 4.")
        self.assertIn("統計的な独立性や", sec)
        self.assertIn("分けて報告します", sec)
        self.assertIn("「新規 10 件を満たしたから一般化できる」とは書かない", sec)

    def test_the_zero_exception_is_written_down(self):
        self.assertIn("0 を除く", self.doc)
        self.assertIn("主張の新規・再出の印は変えない", self.doc)


class HonestyAboutTheSampleTest(unittest.TestCase):
    """**この標本は G-1 を下げる**ことを先に書いてあるか。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_it_says_the_sample_lowers_g1(self):
        sec = section(self.doc, "## 4. **この標本は G-1 を下げる**", "### 4-1.")
        self.assertIn("保留になるように選んだ行", sec)
        self.assertIn("**E2(誤受理)には入らない**", sec)
        self.assertIn("**G-1 の分子には入らない**", sec)
        self.assertIn("G-1 が 50% を割って失敗しても、閾値も標本も作り直さない", sec)

    def test_the_vacuous_g4_hole_is_closed(self):
        sec = section(self.doc, "### 4-1.", "## 5.")
        self.assertIn("分母が 0 のときは、G-4 を「合格」と書かない。`未測定` と書く", sec)
        self.assertIn("「保留の適切さを確かめた」とは書かない", sec)
        self.assertIn("線を厳しくする側の変更", sec)

    def test_the_scorer_implements_the_unmeasured_rule(self):
        src = text(SCORER)
        self.assertIn('"status": ("未測定" if hold_total == 0', src)
        self.assertIn('g4_unmeasured', src)
        self.assertIn('"合格(ただし G-4 は未測定)"', src)

    def test_the_scorer_takes_the_field_mapping_from_the_spec(self):
        src = text(SCORER)
        self.assertIn("F6 = L.FIELDS", src)
        self.assertIn("L.engine_label(b, ALIAS_FOR_NORM)", src)
        self.assertIn("L.normalize_answer(a, ALIAS_FOR_NORM)", src)
        self.assertNotIn('BLANK_PARENT = ', src)


class LinesAndPredictionsTest(unittest.TestCase):
    ROWS = (("G-1 接続の正確さ", "≥ 50%"), ("G-2 誤接続", "= 0 件"),
            ("G-3 根拠なしの接続", "= 0 件"), ("G-4 保留の適切さ", "≥ 80%"),
            ("G-5 母数", "≥ 20 件"))

    def setUp(self):
        self.doc = text(DOC)

    def test_the_carried_lines_are_a_table_of_exactly_five_rows(self):
        sec = section(self.doc, "### 5-1.", "### 5-2.")
        prev = text(M5SEAL)
        for name, line in self.ROWS:
            self.assertIn("| %s | %s |" % (name, line), sec, name)
            self.assertIn(line.replace(" 件", ""), prev, line)
        self.assertEqual(len([l for l in sec.splitlines() if l.startswith("| G-")]), 5)

    def test_e2_is_still_the_primary_and_zero(self):
        self.assertIn("主張は E2 = 誤受理の件数(= G-2 + G-3)。線は 0 件。"
                      "誤接続ゼロは緩めない。".replace("主張は", "主指標は"), self.doc)

    def test_ten_predictions_each_have_a_row(self):
        sec = section(self.doc, "### 5-4.", "### 5-5.")
        for i in range(1, 11):
            self.assertIn("| S-%d |" % i, sec, "S-%d" % i)

    def test_the_prediction_admits_possible_failure(self):
        self.assertIn("50% を割る可能性を認める", self.doc)
        self.assertIn("**1 件でも出れば失敗**", self.doc)

    def test_the_failure_conditions_forbid_rescue(self):
        sec = section(self.doc, "### 5-5.", "## 6.")
        self.assertIn("閾値も対象範囲も変えて救済しない", sec)
        self.assertIn("同じ標本で閾値・採点規則・分母を調整して合格扱いにしない", sec)

    def test_the_things_it_refuses(self):
        sec = section(self.doc, "## 6. やらないこと", "## 7.")
        for s in ("段 5 の報告文を再採点しない", "誤接続ゼロを緩めない",
                  "一般化の根拠にしない",
                  "保留が増えたことを「安全になった」と書かない"):
            self.assertIn(s, sec, s)


if __name__ == "__main__":
    unittest.main()
