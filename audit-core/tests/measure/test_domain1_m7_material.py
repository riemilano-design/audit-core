# -*- coding: utf-8 -*-
"""段 7 の材料・機会の件数・採点器を、**報告文を生成する前に**固定する。

守るのは 6 つ。
  1. 指示文が段 4 と 1 文字も違わないこと
  2. 抜粋に**既出の値**と**段 6 の抜粋の行**が入っていないこと
  3. 材料の形を段 6 から変えた 3 点が**開示されている**こと
     (とくに「表 1 に値を載せないので G-1 が下がる。下がっても作り直さない」)
  4. 機会の件数が**行の単位**だと書かれ、**主張の単位と並べない**と書かれていること
  5. 採点器が G-7 / G-8 と N-1〜N-5 を持ち、**分母 0 を `未測定`** にすること
  6. 問いが段 6 と同一であること(材料の script がそれを門にしていること)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
MAT = os.path.join(FX, "m7_material_2026-10-15.json")
OPP = os.path.join(FX, "m7_opportunity_2026-10-15.json")
M6MAT = os.path.join(FX, "m6_material_2026-10-15.json")
SCORE_SRC = os.path.join(ROOT, "measure", "sheet_m7_score_2026-10-15.py")
RUN_SRC = os.path.join(ROOT, "measure", "sheet_m7_run_2026-10-15.py")
LAB_SRC = os.path.join(ROOT, "measure", "sheet_m7_label_material_2026-10-15.py")
MAT_SRC = os.path.join(ROOT, "measure", "sheet_m7_material_2026-10-15.py")


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
            "m4mat_t7", os.path.join(ROOT, "measure", "sheet_m4_material_2026-10-15.py"))
        M4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(M4)
        mat = load(MAT)
        head = mat["prompt"].split("----- 表(ここから) -----")[0]
        self.assertEqual(head, M4.PROMPT.split("----- 表(ここから) -----")[0])
        self.assertTrue(mat["prompt_identical_to_stage4"])

    def test_the_report_limit_is_unchanged(self):
        self.assertEqual(load(MAT)["limits"], {"extract_chars": 24000,
                                               "report_chars": 1200})


class NoveltyTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.extract = extract_of(self.mat)

    def test_no_previously_claimed_value_is_in_the_extract(self):
        used = set()
        for f in ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json",
                  "m6_binds_2026-10-15.json"):
            for c in load(os.path.join(FX, f))["claims"]:
                v = c.get("value")
                if v is not None and v != 0:
                    used.add(v)
        self.assertTrue(used, "既出の値が読めていない")
        hit = [v for v in used if "{:,}".format(v) in self.extract]
        self.assertEqual(hit, [], "既出の値が抜粋に在る: %s" % hit[:5])
        self.assertEqual(self.mat["excluded_values"], len(used))

    def test_rows_from_the_stage_6_extract_are_excluded(self):
        self.assertGreater(self.mat["excluded_rows_from_m6_extract"], 0)
        m6 = extract_of(load(M6MAT))
        m6_moku = set()
        for line in m6.split("\n"):
            c = [x.strip() for x in line.split("\t")]
            if len(c) == 5 and c[1] and c[2] and c[3] and c[0] != "会計":
                m6_moku.add((c[1], c[2], c[3]))
        now = set()
        for line in self.extract.split("\n"):
            c = [x.strip() for x in line.split("\t")]
            if len(c) == 7 and c[1] and c[2] and c[3] and c[0] != "会計":
                now.add((c[1], c[2], c[3]))
        self.assertTrue(now, "表 3 の行が読めていない")
        self.assertEqual(now & m6_moku, set(), "段 6 の抜粋と同じ目の行が在る")


class ShapeChangeDisclosureTest(unittest.TestCase):
    def setUp(self):
        self.mat = load(MAT)
        self.src = text(MAT_SRC)

    def test_all_three_shape_changes_are_disclosed_in_the_record(self):
        d = self.mat["shape_change_from_m6"]
        self.assertEqual(len(d), 3)
        joined = "".join(d)
        self.assertIn("診断で「列の手がかりが無いと親が取れても接続にならない」と"
                      "分かった後に決めた変更", joined)
        self.assertIn("材料を engine の都合に合わせた変更として開示する", joined)

    def test_the_record_says_this_sample_lowers_g1_and_will_not_be_reselected(self):
        joined = "".join(self.mat["shape_change_from_m6"])
        self.assertIn("会計の層の主張が作れないので、この標本は G-1 がさらに下がる方向である。"
                      "下がっても作り直さない", joined)

    def test_table_1_carries_no_values(self):
        self.assertFalse(self.mat["counts"]["表1_に値を載せたか"])
        for line in extract_of(self.mat).split("\n"):
            if line.startswith("【表 2】"):
                break
            self.assertNotIn(",", line, "表 1 に値が載っている: %r" % line)

    def test_table_3_uses_the_meisai_column_name(self):
        self.assertEqual(self.mat["value_columns"]["表3"][0], "計")
        self.assertEqual(self.mat["value_columns"]["表2"][0], "予算現額")
        self.assertIn("問いは 1 文字も変えない", self.src)

    def test_the_parent_matters_for_the_moku_rows(self):
        dup = self.mat["counts"]["表3_同名で親が違う目"]
        self.assertGreaterEqual(dup.get("管理費", 0), 2)
        self.assertGreaterEqual(self.mat["counts"]["表3_行"], 20)


class OpportunityTest(unittest.TestCase):
    def setUp(self):
        self.o = load(OPP)

    def test_it_is_counted_before_generation_and_is_not_a_pass_condition(self):
        self.assertTrue(self.o["not_a_pass_condition"])
        self.assertIn("生成の前に数えた", self.o["purpose"])
        self.assertIn("この数を見て標本を選び直さない", self.o["will_not_reselect"])

    def test_the_unit_is_rows_not_claims(self):
        self.assertIn("主張は生成されるまで存在しない", self.o["unit"])
        self.assertIn("単位が違うので並べて比べない", text(RUN_SRC))

    def test_the_four_counts_the_human_asked_for_are_present(self):
        for k in ("O-1 親の成分が全部抜粋に在るセル",
                  "O-2 そのうち親が無いと 4 欄で一意にならないセル",
                  "O-3 列の見出しが抜粋に在るセル",
                  "O-3 列の見出しが抜粋に無いセル",
                  "O-4 旧では保留・新では接続になりうるセル"):
            self.assertIn(k, self.o, k)

    def test_the_limit_of_this_sample_is_written_down(self):
        """**項(親の成分 1 つ)はこの標本では試されない**ことを先に書いてある。"""
        self.assertIn("**親の成分が 1 つの場合(項)は、この標本では試されない。**",
                      self.o["limit"])
        self.assertIn("この数を見て表 2 に款名の欄を足すことはしない", self.o["limit"])

    def test_the_counts_match_the_rows(self):
        rows = self.o["rows"]
        self.assertEqual(len(rows), self.o["cells"])
        self.assertEqual(sum(1 for r in rows if r["parent_named_in_extract"]),
                         self.o["O-1 親の成分が全部抜粋に在るセル"])
        self.assertEqual(
            sum(1 for r in rows if r["parent_named_in_extract"]
                and r["ambiguous_without_parent"] and r["unique_with_parent"]),
            self.o["O-4 旧では保留・新では接続になりうるセル"])
        self.assertGreaterEqual(self.o["O-4 旧では保留・新では接続になりうるセル"], 1,
                                "規則を試す機会が 0 件なら、先に分かるべき")


class ScorerTest(unittest.TestCase):
    """**ラベルより先に**採点器を固定する。"""

    def setUp(self):
        self.src = text(SCORE_SRC)

    def test_the_sealed_lines_are_in_the_scorer(self):
        for s in ('"pass": "≥ 50%"', '"pass": "= 0 件"', '"pass": "≥ 80%"',
                  '"pass": "≥ 20"', '"G-7 正しい接続の増分": {"count": g7, "pass": "≥ 1 件"',
                  '"G-8 誤受理の増分": {"count": g8, "pass": "= 0 件"'):
            self.assertIn(s, self.src, s)

    def test_the_verdict_comes_from_the_new_engine_only(self):
        self.assertIn("**合否は新 engine の数で出す。旧は増分のためだけに並べ、"
                      "良い方を選ばない**", self.src)
        self.assertIn('"verdict_from": "新 engine。旧は増分のためだけに並べた(封 §4)"',
                      self.src)

    def test_the_same_tally_is_applied_to_both_engines(self):
        self.assertIn("**旧にも新にも同じ関数を当てる。**", self.src)
        self.assertIn("old = tally(bo, claims, scorable, s1, s2)", self.src)
        self.assertIn("new = tally(bn, claims, scorable, s1, s2)", self.src)

    def test_an_empty_denominator_is_unmeasured(self):
        self.assertIn('main_status = "未測定" if n1_den == 0', self.src)
        self.assertIn('"status": ("未測定" if new["hold_total"] == 0', self.src)
        self.assertIn('"合格(ただし主目的は未測定)"', self.src)

    def test_the_five_counts_are_recorded_separately(self):
        for k in ("N-1_親を正しく抽出", "N-2_親を誤って抽出", "N-3_正しく接続",
                  "N-4_誤接続", "N-5_保留"):
            self.assertIn('"%s"' % k, self.src, k)

    def test_the_label_material_refuses_a_question_that_differs_from_m6(self):
        src = text(LAB_SRC)
        self.assertIn('raise AssertionError("問いが段 6 と違う(封 §5 に反する)")', src)
        self.assertIn("L.check_question(question)", src)


if __name__ == "__main__":
    unittest.main()
