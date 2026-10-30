"""欠陥 A の候補の差分を使用済み 16 書類に当てた観測を固定する。

守りたいのは 3 つ。
  1. 奪った 2 件が記録から消えないこと(数も、どちらの向きかも)
  2. 止めた記録の文書が、その 2 件と門の本数を**自分の表の行**として持つこと
  3. この測定が**未使用の封じた書類に当たっていない**こと(holdout を焼かない)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "fixtures", "xbrl", "defect_a")
IMPACT = os.path.join(BASE, "used_docs_impact_2026-10-14.json")
DRAW = os.path.join(BASE, "draw_2026-10-14.json")
DOC = os.path.join(ROOT, "docs", "DEFECT_A_ADOPTION_STOP_2026-10-14.md")
PATCH = os.path.join(ROOT, "docs", "DEFECT_A_PATCH_CANDIDATE_2026-10-14.patch")
SCRIPT = os.path.join(ROOT, "measure", "defect_a_used_docs_impact_2026-10-14.py")
STOLEN = ("S100Z3CO:N063", "S100Z4Q1:N050")


def _mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ImpactTest(unittest.TestCase):
    def setUp(self):
        self.d = json.load(io.open(IMPACT, encoding="utf-8"))
        self.r = self.d["result"]

    def test_the_claim_total_is_the_same_on_both_sides(self):
        for prof in ("P20", "P16"):
            self.assertEqual(self.r[prof]["claims"], 1909, prof)

    def test_the_moved_counts(self):
        self.assertEqual(self.r["P20"]["moved"], 38)
        self.assertEqual(self.r["P16"]["moved"], 32)

    def test_two_existing_bindings_were_taken_in_both_profiles(self):
        for prof in ("P20", "P16"):
            rows = self.r[prof]["other_rows"]
            self.assertEqual(len(rows), 2, prof)
            self.assertEqual(tuple(sorted(o["id"] for o in rows)), tuple(sorted(STOLEN)), prof)

    def test_the_taken_rows_were_grounded_before_and_after(self):
        """欄だけ見ると動いていない。**根拠が差し替わった**ことが問題である。"""
        for prof in ("P20", "P16"):
            for o in self.r[prof]["other_rows"]:
                self.assertEqual(o["before"]["result"], "GROUNDED", o["id"])
                self.assertEqual(o["after"]["result"], "GROUNDED", o["id"])
                self.assertEqual(o["before"]["form"], "direct_value", o["id"])
                self.assertEqual(o["after"]["form"], "derived_value", o["id"])
                self.assertNotEqual(o["before"]["pointer"], o["after"]["pointer"], o["id"])

    def test_one_taken_row_is_far_from_the_stated_number(self):
        """3億円 の行に 1.569 単位ずれた差を当てた。近いだけで一致にしない原則に反する。"""
        o = [x for x in self.r["P20"]["other_rows"] if x["id"] == "S100Z4Q1:N050"][0]
        self.assertEqual(o["offset_units"], 1.569)
        self.assertEqual(o["before"]["recomputed"], -300297000.0)
        self.assertEqual(o["after"]["recomputed"], -456901000.0)

    def test_every_moved_row_is_exactly_one_written_unit_off(self):
        self.assertEqual(self.r["P20"]["moved_offset_units"], {"1.0": 38})
        self.assertEqual(self.r["P16"]["moved_offset_units"], {"1.0": 32})

    def test_the_moved_rows_are_disjoint_from_the_taken_rows(self):
        for prof in ("P20", "P16"):
            self.assertEqual(set(self.r[prof]["moved_ids"]) & set(STOLEN), set(), prof)


class SampleHygieneTest(unittest.TestCase):
    """**未使用の封じた書類に当てていない**ことを門にする。"""

    def setUp(self):
        self.impact = _mod(SCRIPT, "impact_mod")
        self.draw = json.load(io.open(DRAW, encoding="utf-8"))

    def test_the_sixteen_documents_are_not_the_evaluation_sample(self):
        self.assertEqual(set(self.impact.DOCS) & set(self.draw["docs"]), set())

    def test_the_sixteen_documents_are_outside_the_sealed_order(self):
        """封じた並び(pool)に 1 件も入っていない = 使用済みの古い書類だけ。"""
        drawer = _mod(os.path.join(ROOT, "measure", "defect_a_draw_2026-10-14.py"), "draw_mod")
        order = set(drawer.order_and_check())
        self.assertEqual(set(self.impact.DOCS) & order, set())

    def test_the_document_list_is_sixteen_and_recorded(self):
        self.assertEqual(len(self.impact.DOCS), 16)
        self.assertEqual(self.impact.DOCS, self.d_docs())

    def d_docs(self):
        return json.load(io.open(IMPACT, encoding="utf-8"))["docs"]


class PatchTest(unittest.TestCase):
    def setUp(self):
        with io.open(PATCH, encoding="utf-8") as fh:
            self.p = fh.read()

    def test_the_patch_touches_one_file_only(self):
        files = [l for l in self.p.splitlines() if l.startswith("+++ ")]
        self.assertEqual(files, ["+++ b/audit-core/adapters/xbrl/recipes.py"])

    def test_the_patch_removes_nothing(self):
        removed = [l for l in self.p.splitlines() if l.startswith("-") and not l.startswith("---")]
        self.assertEqual(removed, [])

    def test_the_patch_does_not_touch_the_round_band(self):
        added = "\n".join(l[1:] for l in self.p.splitlines()
                          if l.startswith("+") and not l.startswith("+++"))
        self.assertIn("2 * scale", added)
        self.assertNotIn("scale / 2", added)
        self.assertNotIn("scale/2", added.replace("``|v - t| <= scale/2``", ""))


class DocumentTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_each_taken_row_has_its_own_table_row_with_both_grounds(self):
        for cid, before, after in (("S100Z3CO:N063", "434,055", "434,056"),
                                   ("S100Z4Q1:N050", "−300,297,000", "−456,901,000")):
            hit = self._row(cid)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (cid, len(hit)))
            self.assertTrue(any(before in c for c in hit[0]), "%s 修正前: %s" % (cid, hit[0]))
            self.assertTrue(any(after in c for c in hit[0]), "%s 修正後: %s" % (cid, hit[0]))

    def test_the_counts_table_binds_each_profile_to_its_own_row(self):
        for label, moved in (("P20(既定)", "38"), ("P16", "32")):
            hit = [r for r in self._row(label) if "1909" in " ".join(r)]
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (label, len(hit)))
            self.assertTrue(any(c == moved for c in hit[0]), "%s: %s" % (label, hit[0]))
            self.assertTrue(any(c == "2" for c in hit[0]), "%s: %s" % (label, hit[0]))

    def test_the_gate_counts_are_in_their_own_rows(self):
        clean = [r for r in self.rows if any("714 passed" in c for c in r)]
        dirty = [r for r in self.rows if any("8 failed" in c for c in r)]
        self.assertEqual(len(clean), 1)
        self.assertEqual(len(dirty), 1)

    def test_the_document_says_the_fix_is_not_adopted(self):
        self.assertIn("本体(`adapters/`)には入れていない", self.doc)

    def test_the_document_keeps_the_sealed_result_unchanged(self):
        self.assertIn("封じた合格線は 1 つも動かしていない", self.doc)

    def test_the_document_records_the_prediction_that_failed_outside_the_sample(self):
        self.assertIn("予測 P-4", self.doc)

    def test_the_document_does_not_claim_the_thirty_eight_were_rescued(self):
        self.assertIn("ラベルは付けていない", self.doc)


if __name__ == "__main__":
    unittest.main()
