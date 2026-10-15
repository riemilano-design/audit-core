"""M-2 段 2・段 3 を固定する(新領域①)。

守るのは 4 つ。
  1. 段 3 の**件数**(状態だけ見ると、検査が静かに消えても緑に見える)
  2. 範囲の証拠が無い一致を `GROUNDED` にしないこと(仕様 §4 / 人間の指示 3)
  3. 含める行・除く行の規則(二重計上の防止)
  4. 変異 8 本が黙らないこと
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC = os.path.join(ROOT, "fixtures", "sheet", "m2_structure_2026-10-15.json")
MUT = os.path.join(ROOT, "fixtures", "sheet", "m2_mutations_2026-10-15.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M2_RESULT_2026-10-15.md")
SPEC = os.path.join(ROOT, "docs", "DOMAIN1_M2_SPEC_2026-10-15.md")
SCRIPT = os.path.join(ROOT, "measure", "sheet_m2_structure_2026-10-15.py")

spec = importlib.util.spec_from_file_location("m2", SCRIPT)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

FAMILIES = {"C-1 款 = Σ項": 148, "C-2 歳出合計 = Σ款": 76,
            "C-3 総括 = 決算書(支出済額)": 19, "C-4 総括 合計 = Σ会計": 2,
            "C-5 明細 款 = Σ項": 74, "C-5 明細 項 = Σ目": 202,
            "C-6 明細の款 = 決算書の款(支出済額)": 37,
            "C-7 明細 計 = 当初+補正+繰越+流用": 503}


class Stage2Test(unittest.TestCase):
    def setUp(self):
        self.s2 = json.load(io.open(REC, encoding="utf-8"))["stage2"]

    def test_the_counts_are_pinned(self):
        self.assertEqual(self.s2["soukatu"]["accounts"], 20)
        self.assertEqual(self.s2["kessan"], {"blocks": 19, "kan": 37, "items": 101,
                                             "totals": 19, "rows_excluded": 38,
                                             "not_identified": 0})
        m = self.s2["meisai"]
        self.assertEqual((m["toc_entries"], m["sheets"], m["kan"], m["items"], m["moku"]),
                         (19, 19, 37, 101, 365))

    def test_nothing_was_left_unidentified(self):
        self.assertEqual(self.s2["soukatu"]["unidentified"], 0)
        self.assertEqual(self.s2["kessan"]["not_identified"], 0)
        self.assertEqual(self.s2["meisai"]["not_identified"], 0)
        self.assertEqual(self.s2["meisai"]["sheets_without_toc_entry"], [])
        self.assertEqual(self.s2["meisai"]["toc_keys_without_sheet"], [])

    def test_the_normalizations_are_recorded(self):
        self.assertTrue(any("NFKC" in n for n in self.s2["normalizations"]))


class Stage3Test(unittest.TestCase):
    def setUp(self):
        self.s3 = json.load(io.open(REC, encoding="utf-8"))["stage3"]

    def test_every_family_has_its_pinned_count(self):
        """件数を縛る。状態だけ縛ると、検査が静かに消えても緑に見える(変異 7)。"""
        got = {k: sum(v.values()) for k, v in self.s3["grouped"].items()}
        self.assertEqual(got, FAMILIES)
        self.assertEqual(self.s3["checks"], 1061)

    def test_all_checks_are_grounded(self):
        self.assertEqual(self.s3["by_state"], {"GROUNDED": 1061})
        self.assertEqual(self.s3["not_grounded"], [])

    def test_two_families_cross_files(self):
        for name in ("C-3 総括 = 決算書(支出済額)", "C-6 明細の款 = 決算書の款(支出済額)"):
            self.assertIn(name, self.s3["grouped"])


class RuleTest(unittest.TestCase):
    """仕様 §4 の規則そのものに当てる(実データでは発火していない経路)。"""

    def test_a_value_match_without_range_evidence_is_not_grounded(self):
        c = S.check("試験", "scope", 100, 100, {}, [])
        self.assertTrue(c["value_match"])
        self.assertFalse(c["range_identified"])
        self.assertEqual(c["state"], "UNVERIFIABLE")

    def test_a_missing_evidence_field_blocks_grounding(self):
        c = S.check("試験", "scope", 100, 100, {"code": "A1", "name": None}, ["B1"])
        self.assertEqual(c["state"], "UNVERIFIABLE")

    def test_range_without_value_match_is_a_mismatch(self):
        c = S.check("試験", "scope", 100, 101, {"code": "A1"}, ["B1"])
        self.assertEqual(c["state"], "VALUE_MISMATCH")
        self.assertEqual(c["diff"], 1)

    def test_both_present_is_grounded(self):
        self.assertEqual(S.check("試験", "s", 7, 7, {"code": "A1"}, ["B1"])["state"], "GROUNDED")

    def test_children_stop_at_the_next_sibling(self):
        kids = [{"row": 5}, {"row": 7}, {"row": 12}]
        self.assertEqual(S.children_between(kids, 4, [4, 10]), [{"row": 5}, {"row": 7}])

    def test_the_parent_row_is_never_a_child(self):
        kids = [{"row": 4}, {"row": 5}]
        self.assertEqual(S.children_between(kids, 4, [4, 10]), [{"row": 5}])

    def test_a_missing_child_value_makes_the_sum_none(self):
        total, refs = S.sum_children([{"values": {"x": None}, "code_ref": "A1"}], "x")
        self.assertIsNone(total)

    def test_the_minus_sign_is_a_separate_cell(self):
        self.assertEqual(S.MINUS, "△")


class MutationTest(unittest.TestCase):
    def setUp(self):
        self.m = json.load(io.open(MUT, encoding="utf-8"))

    def test_no_mutation_was_silent(self):
        self.assertEqual(self.m["silent"], [])
        self.assertEqual(len(self.m["mutations"]), 8)

    def test_the_sign_rule_is_actually_exercised(self):
        """△ を見ない変異が赤くなること(C-7 を足す前は 0 件だった)。"""
        for i in (2, 3):
            r = self.m["mutations"][i]["result"]
            self.assertEqual(r["states"].get("VALUE_MISMATCH"), 186, r)
            self.assertEqual(list(r["not_grounded_by_check"]), ["C-7 明細 計 = 当初+補正+繰越+流用"])

    def test_dropping_normalization_silently_removes_checks(self):
        r = self.m["mutations"][6]["result"]
        self.assertEqual(r["checks"], 245)
        self.assertEqual(r["states"], {"GROUNDED": 245})
        self.assertEqual(r["sheets_without_toc_entry"], 19)

    def test_the_range_rules_bite(self):
        self.assertEqual(self.m["mutations"][0]["result"]["states"]["VALUE_MISMATCH"], 208)
        self.assertEqual(self.m["mutations"][7]["result"]["states"]["VALUE_MISMATCH"], 447)


class DocumentTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "").replace(",", "") for c in
                      l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def test_each_family_has_its_own_row_with_its_count(self):
        for name, n in FAMILIES.items():
            head = name.split(" ")[0]
            hit = [r for r in self.rows if r and r[0].startswith(head) and str(n) in r]
            self.assertEqual(len(hit), 1, "%s(%d)の行が %d 本" % (name, n, len(hit)))

    def test_the_total_row_is_bound(self):
        hit = [r for r in self.rows if r and r[0] == "合計" and "1061" in r]
        self.assertEqual(len(hit), 1)

    def test_the_document_separates_m1_from_accuracy(self):
        self.assertIn("接続精度(段 4)は 1 件も測っていない", self.doc)
        self.assertIn("読み取りの根拠としてのみ使った", self.doc)

    def test_the_document_discloses_the_silent_sign_rule(self):
        self.assertIn("最初は 1 件も通っていなかった", self.doc)

    def test_the_document_discloses_the_no_op_mutation(self):
        self.assertIn("空振り", self.doc)

    def test_the_document_warns_that_zero_is_not_a_proof(self):
        self.assertIn("「0 件」は「その経路が正しい」ことの証明ではない", self.doc)

    def test_the_spec_was_committed_before_measuring(self):
        with io.open(SPEC, encoding="utf-8") as fh:
            self.assertIn("測定の前に commit する", fh.read())


if __name__ == "__main__":
    unittest.main()
