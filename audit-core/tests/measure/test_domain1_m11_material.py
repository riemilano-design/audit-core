# -*- coding: utf-8 -*-
"""段 11 の材料(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §2)を固定する。

守るのは 9 つ。
  1. 除外の範囲に**段 9 が足されている**(それ以外の規則は段 9 の字のまま)
  2. 規則の出どころが**凍結した段 9 の `build()`** であること・sha が動いていないこと
  3. **凍結した module を汚さない**(`build()` の後に `PREV` が戻っている)
  4. **抜粋に別名の形が載っている**(封 §2-2 の歯。歳入側 engine で作ると消える)
  5. `check_alias_forms_are_printed` は**別名の形が無い抜粋で赤になる**(歯)
  6. `stop_check` の **3 つの理由が壊した入力でそれぞれ発火する**(歯)
  7. 記録の数が**その場で作り直した材料と一致する**(記録を読むだけにしない)
  8. **重複の開示の数が独立に数え直した数と一致する**(封 §13-2)
  9. 封 §13 の追記(**行は新しくない**・**数え方の欠陥**)が在ること
"""
import hashlib
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "m11_material_2026-10-16.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M11_SEAL_2026-10-16.md")
M9_SHA = "a1c82749583947f0"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class RuleComesFromStage9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11mat_t", "sheet_m11_material_2026-10-16.py")
        cls.rec = load(REC)

    def test_1_stage9_is_added_to_the_excluded_range(self):
        prev, prev_mat = self.m.widened()
        self.assertIn("m9_binds_2026-10-16.json", prev)
        self.assertIn("m9_material_2026-10-16.json", prev_mat)
        self.assertEqual(prev[:-1], tuple(self.m.M9.PREV),
                         "段 9 以外の範囲を触っている")
        self.assertEqual(prev_mat[:-1], tuple(self.m.M9.PREV_MAT))
        self.assertEqual(list(prev), self.rec["excluded_stages"])

    def test_2_the_frozen_stage9_builder_is_unchanged(self):
        p = os.path.join(MEASURE, "sheet_m9_material_2026-10-16.py")
        with io.open(p, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], M9_SHA,
                             "**段 9 の材料の script が動いている**")
        self.assertEqual(self.rec["rule_source"],
                         "measure/sheet_m9_material_2026-10-16.py の build()")
        self.assertTrue(self.rec["prompt_identical_to_stage4"])
        self.assertEqual(self.rec["prompt"].count("----- 表(ここから) -----"), 1)

    def test_3_the_frozen_module_is_restored_after_build(self):
        before = (tuple(self.m.M9.PREV), tuple(self.m.M9.PREV_MAT))
        self.m.build()
        self.assertEqual((tuple(self.m.M9.PREV), tuple(self.m.M9.PREV_MAT)), before,
                         "凍結した module を汚したまま戻していない")


class AliasFormsArePrintedTest(unittest.TestCase):
    """封 §2-2 の歯。**歳入側の engine で材料を作ると、ここが赤になる。**"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11mat_t2", "sheet_m11_material_2026-10-16.py")
        cls.rec = load(REC)

    def test_4_the_extract_prints_alias_forms(self):
        forms = self.rec["alias_forms_in_extract"]
        self.assertGreaterEqual(len(forms), 1, "別名の形が抜粋に無い")
        for f in forms:
            self.assertTrue(f.startswith("東京都"), f)
        extract = self.rec["prompt"].split("----- 表(ここから) -----")[1]
        self.assertEqual(sorted(self.m.check_alias_forms_are_printed(extract)),
                         sorted(forms))
        self.assertIn("旧 engine", self.rec["alias_table_from"])

    def test_5_an_extract_without_alias_forms_is_red(self):
        with self.assertRaises(AssertionError) as cm:
            self.m.check_alias_forms_are_printed(
                "会計\t階層\t科目名\n一般会計\t款\t総務費\n")
        self.assertIn("歳入側の engine で材料を作った疑い", str(cm.exception))


class StopCheckHasTeethTest(unittest.TestCase):
    """封 §2-3。**正常な入力では発火しない守りなので、壊した入力で当てる。**"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11mat_t3", "sheet_m11_material_2026-10-16.py")
        cls.rec = load(REC)

    def test_6_real_material_passes(self):
        st = self.rec["stop_check"]
        self.assertTrue(st["生成してよいか"], st["止める理由"])
        self.assertEqual(st["止める理由"], [])

    def test_7_no_table3b_rows_stops_generation(self):
        out = self.m.stop_check({"表3b_行": 0, "表3b_の会計": ["x"]}, 100)
        self.assertFalse(out["生成してよいか"])
        self.assertIn("表 3b が 0 行(③の機会が無い)", out["止める理由"])

    def test_8_no_table3b_accounts_stops_generation(self):
        out = self.m.stop_check({"表3b_行": 5, "表3b_の会計": []}, 100)
        self.assertFalse(out["生成してよいか"])
        self.assertIn("表 3b に載る会計が 0 件", out["止める理由"])

    def test_9_too_few_cells_stops_generation(self):
        out = self.m.stop_check({"表3b_行": 5, "表3b_の会計": ["x"]},
                                self.m.MIN_CELLS - 1)
        self.assertFalse(out["生成してよいか"])
        self.assertTrue(any("G-5 の線" in r for r in out["止める理由"]))
        ok = self.m.stop_check({"表3b_行": 5, "表3b_の会計": ["x"]}, self.m.MIN_CELLS)
        self.assertTrue(ok["生成してよいか"], "境界で止めすぎている")

    def test_10_the_line_is_the_same_number_as_g5(self):
        self.assertEqual(self.m.MIN_CELLS, 20, "G-5 の線と同じ 20 件")


class RecordMatchesAFreshBuildTest(unittest.TestCase):
    """**記録を読むだけの門にしない。**その場で作り直して突き合わせる。"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11mat_t4", "sheet_m11_material_2026-10-16.py")
        cls.rec = load(REC)
        cls.b = cls.m.build()

    def test_11_counts_match(self):
        self.assertEqual(self.b["counts"], self.rec["counts"])
        self.assertEqual(self.b["excluded_values"], self.rec["excluded_values"])
        self.assertEqual(len(self.b["extract"]), self.rec["extract_chars"])

    def test_12_value_cells_match(self):
        cells = self.m.OPP.cells_of(self.b["extract"])
        self.assertEqual(len(cells), self.rec["value_cells"])
        self.assertGreaterEqual(len(cells), 20)

    def test_13_table3b_rows_and_accounts(self):
        c = self.rec["counts"]
        self.assertGreaterEqual(c["表3b_行"], 1)
        self.assertGreaterEqual(len(c["表3b_の会計"]), 1)
        for a in c["表3b_の会計"]:
            self.assertTrue(a.startswith("東京都"),
                            "表 3b の会計が別名の形で載っていない: %s" % a)

    def test_14_claimed_values_of_stage4_to_9_are_excluded(self):
        prev, _ = self.m.widened()
        used = set()
        for f in prev:
            for c in load(os.path.join(FX, f))["claims"]:
                v = c.get("value")
                if v is not None and v != 0:
                    used.add(v)
        self.assertEqual(len(used), self.rec["excluded_values"])
        # **セルの値で突き合わせる。字で探すと部分一致で嘘になる**
        # (`692,038,469` は `692,038` を含む。2026-10-16 に私の門が踏んだ)
        cells = self.m.OPP.cells_of(self.b["extract"])
        hit = sorted({c["value"] for c in cells} & used)
        self.assertEqual(hit, [], "過去に主張された値が抜粋に残っている: %s" % hit[:3])
        self.assertGreater(len(cells), 0)

    def test_14b_a_substring_match_is_not_an_equality_match(self):
        """**歯**: 字で探す数え方は部分一致で偽の当たりを出す。"""
        body = self.b["extract"]
        self.assertIn("692,038,469", body)
        self.assertTrue("692,038" in body, "部分一致は在る")
        cells = self.m.OPP.cells_of(body)
        self.assertNotIn(692038, {c["value"] for c in cells},
                         "セルの値としては在ってはいけない")


class OverlapDisclosureTest(unittest.TestCase):
    """封 §13-2。**凍結した数え方の欠陥を、別に数えて開示する。**"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11mat_t5", "sheet_m11_material_2026-10-16.py")
        cls.rec = load(REC)

    def test_15_disclosure_matches_an_independent_count(self):
        d = self.rec["過去の抜粋と重複した行(正しい数。開示)"]
        extract = self.rec["prompt"].split("----- 表(ここから) -----")[1]
        got = self.m.overlap_disclosure(extract)
        self.assertEqual(got["表2"], d["表2"])
        self.assertEqual(got["表3"], d["表3"])

    def test_16_the_frozen_counter_misses_the_six_column_table(self):
        """**歯**: 6 欄の表 3 は凍結した数え方に当たらない(だから開示が要る)。"""
        m9 = load(os.path.join(FX, "m9_material_2026-10-16.json"))
        body = (m9["prompt"].split("----- 表(ここから) -----")[1]
                .split("----- 表(ここまで) -----")[0])
        six = [l for l in body.split("\n")
               if len([x for x in l.split("\t")]) == 6 and "\t" in l]
        self.assertGreater(len(six), 10, "段 9 の表 3 が 6 欄で印字されていない")
        base = self.m.M9.rows_in_previous_extracts()
        old = tuple(self.m.M9.PREV_MAT)
        self.m.M9.PREV_MAT = old + ("m9_material_2026-10-16.json",)
        try:
            wide = self.m.M9.rows_in_previous_extracts()
        finally:
            self.m.M9.PREV_MAT = old
        self.assertEqual(len(wide - base), 0,
                         "段 9 を足したら増えた ― 開示の前提が変わった")
        self.assertGreater(self.rec["過去の抜粋と重複した行(正しい数。開示)"]["表3"], 0,
                           "正しい数が 0 なら開示の意味が無い")


class SealAddendumTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_17_the_addendum_is_dated_and_before_generation(self):
        self.assertIn("## §13 追記(2026-10-16・**材料を作ってから測った。"
                      "生成より先に書く**)", self.t)
        self.assertIn("**§9 の限界の表は編集しない。**", self.t)

    def test_18_rows_are_not_new(self):
        block = self.t.split("### §13-1")[1].split("### §13-2")[0]
        self.assertIn("**52 行(全部)**", block)
        self.assertIn("「主張される値が新しい」という意味であり", block)
        self.assertIn("「一度も見せていない行」という意味ではない", block)
        self.assertIn("行の新規性は主張しない", block)
        rec = load(REC)["過去の抜粋と重複した行(正しい数。開示)"]
        self.assertEqual(rec["表3"], 52, "文書の数が実測と違う")
        self.assertEqual(rec["表2"], 20)
        self.assertIn("**20 行**", block)

    def test_19_the_counting_defect_is_disclosed_not_fixed(self):
        block = self.t.split("### §13-2")[1]
        self.assertIn("**5 欄か 7 欄**", block)
        self.assertIn("**段 9 の表 3 を 1 行も数えていない。**", block)
        self.assertIn("**規則は凍結した側の字なので変えない。**", block)
        self.assertIn("**標本の選び方には影響しない。**", block)


if __name__ == "__main__":
    unittest.main()
