"""下見(標準ライブラリで xlsx を読む)の数が動かないことを門にする。

材料は script が自分で作る合成ブックなので、外部の材料に依らず毎回走る。
**精度の門ではない。**「案 (A) で値と式が取れる」という下見の結論が崩れたら赤くする。
"""
import importlib.util
import io
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "sheet_reader_probe_2026-10-15.py")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SHEET_DESIGN_2026-10-15.md")

spec = importlib.util.spec_from_file_location("sheet_probe", SCRIPT)
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)


class ProbeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="sheet-probe-test-")
        cls.a = os.path.join(cls.dir, "a.xlsx")
        cls.b = os.path.join(cls.dir, "b.xlsx")
        P.make_openpyxl_book(cls.a)
        P.make_shared_strings_book(cls.b)
        cls.ra = P.compare(cls.a)
        cls.rb = P.compare(cls.b)

    def test_values_and_formulas_agree_on_both_books(self):
        for r in (self.ra, self.rb):
            self.assertEqual(r["value_diff"], 0)
            self.assertEqual(r["formula_diff"], 0)

    def test_the_only_difference_is_a_builtin_number_format(self):
        self.assertEqual(self.ra["format_diff"], 1)
        self.assertEqual(self.rb["format_diff"], 0)
        row = self.ra["rows"][0]
        self.assertEqual(row["ref"], "B9")
        self.assertEqual(row["std"]["number_format"], "10")
        self.assertEqual(row["openpyxl"]["number_format"], "0.00%")

    def test_the_cell_counts_are_pinned(self):
        self.assertEqual(self.ra["same"], 39)
        self.assertEqual(self.rb["same"], 4)

    def test_the_shared_strings_path_is_actually_exercised(self):
        """実物の Excel が使う経路。ここが読めないなら下見の結論は無効。"""
        cells = P.read(self.b)["決算"]["cells"]
        self.assertEqual(cells["A1"]["value"], "単位:千円")
        self.assertEqual(cells["A2"]["value"], "売上高")

    def test_a_formula_cell_carries_both_the_formula_and_the_saved_value(self):
        cells = P.read(self.b)["決算"]["cells"]
        self.assertEqual(cells["B3"]["formula"], "=SUM(B2:B2)")
        self.assertEqual(cells["B3"]["value"], 9648)

    def test_a_formula_cell_without_a_saved_value_reads_as_none(self):
        """openpyxl が保存した本には計算結果が無い。engine は**無い場合**を扱う必要がある。"""
        cells = P.read(self.a)["月次"]["cells"]
        self.assertEqual(cells["B6"]["formula"], "=SUM(B3:B5)")
        self.assertIsNone(cells["B6"]["value"])

    def test_merged_cells_are_reported(self):
        self.assertEqual(P.read(self.a)["月次"]["merged"], ["A1:D1"])


class DocumentTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def test_the_probe_numbers_are_in_their_own_table_rows(self):
        for label, want in (("値", "0 件"), ("式", "0 件"), ("表示形式", "1 件")):
            hit = [r for r in self.rows if r and r[0] == label]
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (label, len(hit)))
            self.assertTrue(any(want in c for c in hit[0]), "%s: %s" % (label, hit[0]))

    def test_the_document_discloses_that_the_material_is_synthetic(self):
        self.assertIn("実物ではない", self.doc)

    def test_the_document_keeps_the_untested_list(self):
        for word in ("日付", "共有数式"):
            self.assertIn(word, self.doc)


if __name__ == "__main__":
    unittest.main()
