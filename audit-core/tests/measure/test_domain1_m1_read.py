"""M-1 の読み取りの結果を固定する(新領域①)。

守るのは 3 つ。
  1. 記録の数と文書の表が食い違わないこと
  2. **ふりがなが値に混ざる欠陥**が戻らないこと(実物で踏んだ)
  3. 読み取りが「式を自分で計算して埋める」方向へ動かないこと
材料(`~/.cache/audit-core/sheet/`)が無いときは**落ちる**(skip にしない)。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC = os.path.join(ROOT, "fixtures", "sheet", "m1_read_2026-10-15.json")
OPENED = os.path.join(ROOT, "fixtures", "sheet", "opened_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M1_RESULT_2026-10-15.md")
SCRIPT = os.path.join(ROOT, "measure", "sheet_read_m1_2026-10-15.py")
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")

spec = importlib.util.spec_from_file_location("m1", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def _rec():
    return json.load(io.open(REC, encoding="utf-8"))


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = _rec()
        self.by = {f["label"]: f for f in self.r["files"]}

    def test_the_three_files_are_the_fetched_ones(self):
        opened = json.load(io.open(OPENED, encoding="utf-8"))
        self.assertEqual(sorted(self.by), sorted(v["label"] for v in opened["files"].values()))
        for f in self.r["files"]:
            self.assertIn(f["sha256"], [v["sha256"] for v in opened["files"].values()], f["label"])

    def test_the_counts_are_pinned(self):
        want = {"決算書 総括": (1, 88), "決算書 歳出": (1, 1442), "事項別明細 歳出": (20, 58623)}
        for label, (sheets, cells) in want.items():
            self.assertEqual(self.by[label]["sheets"], sheets, label)
            self.assertEqual(self.by[label]["cells"], cells, label)
        self.assertEqual(sum(f["cells"] for f in self.r["files"]), 60153)

    def test_no_formula_cell_exists_in_this_material(self):
        """この材料には式が 1 件も無い。設計案 §1 の優先順位 2 が使えない根拠。"""
        for f in self.r["files"]:
            self.assertEqual(f["formula_cells"], 0, f["label"])
            self.assertEqual(f["formula_cells_without_value"], 0, f["label"])

    def test_nothing_failed_to_read(self):
        for f in self.r["files"]:
            self.assertEqual(f["notes"]["errors"], [], f["label"])

    def test_the_real_cross_check_against_openpyxl_is_zero_diff(self):
        for f in self.r["files"]:
            cc = f["cross_check_openpyxl"]
            self.assertEqual(cc["value_diff"], 0, f["label"])
            self.assertEqual(cc["format_diff"], 0, f["label"])
            self.assertEqual(cc["same"], f["cells"], f["label"])

    def test_the_probe_gaps_are_answered(self):
        for f in self.r["files"]:
            n = f["notes"]
            self.assertEqual(f["date_formatted_cells"], 0, f["label"])
            self.assertEqual(n["shared_formulas"], 0, f["label"])
            self.assertEqual(n["inline_strings"], 0, f["label"])
            self.assertTrue(n["has_shared_strings"], f["label"])
            self.assertEqual(n["unresolved_number_format_ids"], 0, f["label"])
            self.assertFalse(n["date1904"], f["label"])

    def test_the_phonetic_strings_are_counted(self):
        self.assertEqual(sum(f["notes"]["phonetic_strings"] for f in self.r["files"]), 63)
        self.assertEqual(sum(f["notes"]["shared_strings"] for f in self.r["files"]), 977)


class ReaderTest(unittest.TestCase):
    """材料そのものに当てる門。無ければ落ちる。"""

    @classmethod
    def setUpClass(cls):
        cls.path = os.path.join(CACHE, "op20251218_06kessan_01_soukatu.xlsx")
        if not os.path.exists(cls.path):
            raise AssertionError("材料が無い: %s" % cls.path)
        cls.book, cls.notes = M.read(cls.path)

    def test_the_headers_have_no_ruby(self):
        """ふりがなが値に混ざる欠陥(M-1 で実際に踏んだ)が戻ったら赤。"""
        cells = self.book["総括"]["cells"]
        self.assertEqual(cells["A7"]["value"], "会計別")
        self.assertEqual(cells["D7"]["value"], "歳入決算額")
        self.assertEqual(cells["F7"]["value"], "差額")
        for ref, c in cells.items():
            if isinstance(c["value"], str):
                self.assertNotIn("カイケイ", c["value"], ref)

    def test_the_label_the_unit_and_the_number_sit_on_different_rows(self):
        """主語・単位・数が別の行にある(M-2 の設計に効く構造)。"""
        cells = self.book["総括"]["cells"]
        self.assertEqual(cells["B8"]["value"], "一般会計")      # 対象の行
        self.assertEqual(cells["D8"]["value"], "円 ")            # 単位の行
        self.assertEqual(cells["D9"]["value"], 8962754865176)   # 数の行
        self.assertIn("B8:B10", self.book["総括"]["merged"])     # 対象は 3 行に結合

    def test_a_merged_header_need_not_sit_in_the_value_column(self):
        """「差額」の見出しは F7:G7 の結合で、値は **G** に在る(F は空)。

        見出しと値を**同じ列**で突き合わせる規則は、この材料で外れる。
        """
        sh = self.book["総括"]
        self.assertIn("F7:G7", sh["merged"])
        self.assertEqual(sh["cells"]["F7"]["value"], "差額")
        self.assertIsNone(sh["cells"].get("F9"))
        self.assertEqual(sh["cells"]["G9"]["value"], 238169629884)

    def test_the_reader_never_computes_a_value_itself(self):
        """式のセルに engine が値を入れないこと(人間の指示)。"""
        src = io.open(M.__file__ if hasattr(M, "__file__") else SCRIPT, encoding="utf-8").read()
        self.assertNotIn("eval(", src)
        for sh in self.book.values():
            for ref, c in sh["cells"].items():
                if c["formula"] is not None:
                    self.fail("この材料に式は無いはず: %s" % ref)


class BrokenMaterialTest(unittest.TestCase):
    """**故障を作って**読み取りの守りに当てる。

    正常な材料では `notes["errors"]` の経路が 1 度も走らないので、
    「失敗を黙って捨てる」改変が門をすり抜ける(変異 N2 で実際にすり抜けた)。
    """

    def _book(self, sheet_xml):
        import tempfile
        import zipfile
        S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        PK = "http://schemas.openxmlformats.org/package/2006/relationships"
        path = os.path.join(tempfile.mkdtemp(prefix="m1-broken-"), "broken.xlsx")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("[Content_Types].xml",
                       '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                       '<Default Extension="xml" ContentType="application/xml"/>'
                       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>')
            z.writestr("_rels/.rels",
                       '<?xml version="1.0"?><Relationships xmlns="%s"><Relationship Id="rId1" '
                       'Type="%s/officeDocument" Target="xl/workbook.xml"/></Relationships>'
                       % (PK, R.rsplit("/", 1)[0]))
            z.writestr("xl/workbook.xml",
                       '<?xml version="1.0"?><workbook xmlns="%s" xmlns:r="%s"><sheets>'
                       '<sheet name="壊れ" sheetId="1" r:id="rId1"/></sheets></workbook>' % (S, R))
            z.writestr("xl/_rels/workbook.xml.rels",
                       '<?xml version="1.0"?><Relationships xmlns="%s"><Relationship Id="rId1" '
                       'Type="%s/worksheet" Target="worksheets/sheet1.xml"/></Relationships>' % (PK, R))
            z.writestr("xl/worksheets/sheet1.xml", sheet_xml % S)
        return M.read(path)

    def test_a_cell_that_cannot_be_read_is_recorded_not_dropped(self):
        xml = ('<?xml version="1.0"?><worksheet xmlns="%s"><sheetData>'
               '<row r="1"><c r="A1"><v>abc</v></c><c r="B1"><v>5</v></c></row>'
               '</sheetData></worksheet>')
        book, notes = self._book(xml)
        self.assertEqual([e["ref"] for e in notes["errors"]], ["A1"])
        self.assertEqual(book["壊れ"]["cells"]["B1"]["value"], 5)   # 残りは読める

    def test_a_sheet_that_cannot_be_parsed_is_recorded(self):
        book, notes = self._book('<?xml version="1.0"?><worksheet xmlns="%s"><sheetData><row')
        self.assertEqual([e.get("sheet") for e in notes["errors"]], ["壊れ"])
        self.assertEqual(book, {})


class DocumentTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "").replace(",", "") for c in
                      l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]
        self.r = _rec()

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_each_file_has_its_own_row_with_its_measured_counts(self):
        for f in self.r["files"]:
            hit = self._row(f["label"])
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (f["label"], len(hit)))
            cells = hit[0]
            self.assertIn(str(f["sheets"]), cells)
            self.assertIn(str(f["cells"]), cells)

    def test_the_total_row_carries_the_total(self):
        hit = self._row("合計")
        self.assertEqual(len(hit), 1)
        self.assertIn("60153", hit[0])

    def test_the_document_records_the_phonetic_defect(self):
        self.assertIn("ふりがな", self.doc)
        self.assertIn("63 / 977", self.doc)

    def test_the_document_says_the_formula_priority_cannot_be_used_here(self):
        self.assertIn("この材料では使えない", self.doc)

    def test_the_document_says_no_binding_was_attempted(self):
        self.assertIn("接続は 1 件も試していない", self.doc)

    def test_the_document_has_no_pass_line(self):
        self.assertIn("合格線は無い", self.doc)


if __name__ == "__main__":
    unittest.main()
