# -*- coding: utf-8 -*-
"""段 8 の材料・機会の件数・採点器を、**報告文を生成する前に**固定する。

守るのは 6 つ。
  1. 指示文が段 4 と 1 文字も違わないこと / 問いが段 6 と同一であること
  2. 既出の値と、段 6・段 7 の抜粋の行が入っていないこと
  3. **款名は裏づけ 3 本がそろった項にだけ書き、足りない行は落とす**こと
  4. **O-5(6 欄すべてが抜粋から読める)が全セル**であること ― 段 7 の失敗の型が消えたこと
  5. **O-4 が表 3 の 12 セルしか無い**ことと、**G-7 が 0 になりうる**ことを先に書いてあること
  6. 採点器が X-1〜X-4 を持ち、G-7 / G-8 と N-1〜N-5 を持ち、分母 0 を `未測定` にすること
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m8_material_2026-10-16.json")
OPP = os.path.join(FX, "m8_opportunity_2026-10-16.json")
BACK = os.path.join(FX, "parent_backing_2026-10-16.json")
SCORE_SRC = os.path.join(ROOT, "measure", "sheet_m8_score_2026-10-16.py")
RUN_SRC = os.path.join(ROOT, "measure", "sheet_m8_run_2026-10-16.py")
LAB_SRC = os.path.join(ROOT, "measure", "sheet_m8_label_material_2026-10-16.py")
MAT_SRC = os.path.join(ROOT, "measure", "sheet_m8_material_2026-10-16.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def extract_of(mat):
    return (mat["prompt"].split("----- 表(ここから) -----")[1]
            .split("----- 表(ここまで) -----")[0].strip())


class PromptTest(unittest.TestCase):
    def test_the_instruction_is_byte_identical_to_stage_4(self):
        spec = importlib.util.spec_from_file_location(
            "m4mat_t8", os.path.join(ROOT, "measure", "sheet_m4_material_2026-10-15.py"))
        M4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(M4)
        mat = load(MAT)
        self.assertEqual(mat["prompt"].split("----- 表(ここから) -----")[0],
                         M4.PROMPT.split("----- 表(ここから) -----")[0])
        self.assertTrue(mat["prompt_identical_to_stage4"])

    def test_the_label_material_refuses_a_question_that_differs_from_m6(self):
        src = text(LAB_SRC)
        self.assertIn('raise AssertionError("問いが段 6 と違う(封 §5 に反する)")', src)
        self.assertIn("L.check_question(question)", src)


class NoveltyTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.extract = extract_of(self.mat)

    def test_no_previously_claimed_value_is_in_the_extract(self):
        used = set()
        for f in ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
                  "m6_binds_2026-10-15.json", "m7_binds_2026-10-15.json"):
            for c in load(os.path.join(FX, f))["claims"]:
                v = c.get("value")
                if v is not None and v != 0:
                    used.add(v)
        hit = [v for v in used if "{:,}".format(v) in self.extract]
        self.assertEqual(hit, [], "既出の値が抜粋に在る: %s" % hit[:5])
        self.assertEqual(self.mat["excluded_values"], len(used))

    def test_rows_from_the_two_previous_extracts_are_excluded(self):
        self.assertGreater(self.mat["excluded_rows_from_previous_extracts"], 0)
        prev = set()
        for f in ("m6_material_2026-10-15.json", "m7_material_2026-10-15.json"):
            b = extract_of(load(os.path.join(FX, f)))
            for line in b.split("\n"):
                c = [x.strip() for x in line.split("\t")]
                if len(c) in (5, 7) and c[0] != "会計" and c[1] and c[2] and c[3]:
                    prev.add((c[1], c[2], c[3]))
        now = set()
        for line in self.extract.split("\n"):
            c = [x.strip() for x in line.split("\t")]
            if len(c) == 7 and c[0] != "会計" and c[1] and c[2] and c[3]:
                now.add((c[1], c[2], c[3]))
        self.assertTrue(now, "表 3 の行が読めていない")
        self.assertEqual(now & prev, set(), "前の抜粋と同じ目の行が在る")


class BackingInMaterialTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.extract = extract_of(self.mat)

    def test_table_2_has_a_kan_name_column(self):
        self.assertIn("会計\t階層\t款名\t科目名\t予算現額\t支出済額\t不用額", self.extract)
        self.assertIn("**表 2 に `款名` の欄が増えたことだけ。**",
                      self.mat["change_from_m7"])

    def test_every_kou_row_has_a_kan_name_and_every_kan_row_has_none(self):
        for x in self.mat["chosen"]["表2"]:
            if x["階層"] == "項":
                self.assertTrue(x["款名"], "項に款名が無い: %s" % x)
            else:
                self.assertEqual(x["款名"], "", "款の行に款名が在る: %s" % x)

    def test_the_kan_names_come_from_the_three_backings(self):
        spec = importlib.util.spec_from_file_location(
            "backing_t8", os.path.join(ROOT, "measure",
                                       "sheet_parent_backing_2026-10-16.py"))
        B = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(B)
        M2 = B.M2
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        ks = M2.parse_kessan(books[M2.KESSAN])
        ms = M2.parse_meisai(books[M2.MEISAI])
        raw = B.E.fix_total_level(B.E.build_index(
            M2.parse_soukatu(books[M2.SOUKATU]), ks, ms))
        ok, _, _ = B.kou_parents(ks, ms, B.E.alias_table(raw)["table"])
        for x in self.mat["chosen"]["表2"]:
            if x["階層"] != "項":
                continue
            key = (M2.norm("一般会計"), M2.norm(x["科目名"]))
            self.assertIn(key, ok, "裏づけの無い款名が材料に在る: %s" % x)
            self.assertEqual(M2.norm(ok[key]), M2.norm(x["款名"]))

    def test_rows_without_the_three_backings_were_dropped_not_guessed(self):
        self.assertGreater(self.mat["counts"]["表2_裏づけが足りず落とした項"], 0)
        self.assertIn("**推測で補完しない**", text(MAT_SRC))

    def test_the_moku_backing_is_recorded_as_weaker(self):
        pb = self.mat["parent_backing"]
        self.assertEqual(len(pb["項の款名"]), 3)
        self.assertEqual(len(pb["目の親"]), 2)
        self.assertIn("**同じ強さの根拠として扱わない。**", pb["注"])
        self.assertEqual(len(load(BACK)["backings"]["目"]), 2)

    def test_the_seal_wording_correction_is_recorded(self):
        self.assertIn("**封は直さない。**", self.mat["seal_wording_correction"])
        self.assertIn("件数 2 は合っている", self.mat["seal_wording_correction"])


class OpportunityTest(unittest.TestCase):
    def setUp(self):
        self.o = load(OPP)

    def test_it_is_counted_before_generation_and_is_not_a_pass_condition(self):
        self.assertTrue(self.o["not_a_pass_condition"])
        self.assertIn("生成の前に数えた", self.o["purpose"])
        self.assertIn("この数を見て標本を選び直さない", self.o["will_not_reselect"])
        self.assertIn("主張は生成されるまで存在しない", self.o["unit"])

    def test_every_cell_is_readable_in_six_fields(self):
        """**段 7 の失敗の型が消えたこと。**"""
        self.assertEqual(self.o["O-5 6 欄すべてが抜粋から読めるセル"], self.o["cells"])
        self.assertIn("段 7 の失敗の型(抜粋から 6 欄が読めない)はこの標本では起きない",
                      self.o["unverifiable_prediction"])

    def test_the_increment_can_only_come_from_table_3(self):
        self.assertEqual(self.o["O-4 の表ごとの内訳"], {"表 3": 12})
        self.assertIn("**O-4 は表 3 の 4 行(12 セル)からしか出ない。**", self.o["limit"])

    def test_the_risk_that_g7_is_zero_is_written_before_generation(self):
        self.assertIn("書かなければ G-7 = 0 で失敗になる", self.o["limit"])
        self.assertIn("**この数を見て表 3 を増やすことはしない**", self.o["limit"])

    def test_the_counts_match_the_rows(self):
        rows = self.o["rows"]
        self.assertEqual(len(rows), self.o["cells"])
        self.assertEqual(sum(1 for r in rows if r["six_fields_readable"]),
                         self.o["O-5 6 欄すべてが抜粋から読めるセル"])
        self.assertEqual(
            sum(1 for r in rows if r["parent_named_in_extract"]
                and r["ambiguous_without_parent"] and r["unique_with_parent"]),
            self.o["O-4 旧では保留・新では接続になりうるセル"])


class ScorerTest(unittest.TestCase):
    def setUp(self):
        self.src = text(SCORE_SRC)

    def test_the_sealed_lines_are_in_the_scorer(self):
        for s in ('"pass": "≥ 50%"', '"pass": "= 0 件"', '"pass": "≥ 80%"',
                  '"G-7 正しい接続の増分": {"count": g7, "pass": "≥ 1 件"',
                  '"G-8 誤受理の増分": {"count": g8, "pass": "= 0 件"'):
            self.assertIn(s, self.src, s)

    def test_the_four_x_indicators_are_computed(self):
        for k in ("X-1 抜粋に在る行に結んだ", "X-2 抜粋に無い行に結んだ",
                  "X-3 X-2 のうち誤受理", "X-4 抜粋に在る行に結んで誤受理"):
            self.assertIn(k, self.src, k)
        self.assertIn("X-1 抜粋に在る行に結んだ主張", text(RUN_SRC))
        self.assertIn("X-2 抜粋に無い行に結んだ主張", text(RUN_SRC))

    def test_the_verdict_comes_from_the_new_engine_only(self):
        self.assertIn("**合否は新 engine の数で出す。旧は増分のためだけに並べ、"
                      "良い方を選ばない**", self.src)

    def test_an_empty_denominator_is_unmeasured(self):
        self.assertIn('main_status = "未測定" if n1_den == 0', self.src)
        self.assertIn('"status": ("未測定" if new["hold_total"] == 0', self.src)

    def test_the_five_counts_are_recorded_separately(self):
        for k in ("N-1_親を正しく抽出", "N-2_親を誤って抽出", "N-3_正しく接続",
                  "N-4_誤接続", "N-5_保留"):
            self.assertIn('"%s"' % k, self.src, k)

    def test_the_stage_7_x_numbers_are_quoted_for_comparison(self):
        self.assertIn("段 7 の実測は X-1 20・X-2 6・X-3 6・X-4 0", self.src)


if __name__ == "__main__":
    unittest.main()
