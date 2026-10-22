"""欠陥 A の評価の封(docs/DEFECT_A_EVAL_SEAL_2026-10-14.md)を留める。

封じた標本・合格線・予測が後から動かないことを門にする。
**開封(取得)の前は 8 書類の ZIP が手元に無いことも確かめる** ―
開封の記録(``opened_2026-10-14.json``)が出来たら、その確認は役目を終える。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
import sys
sys.path.insert(0, ROOT)
from adapters.xbrl import edinet  # noqa: E402

SEAL = os.path.join(ROOT, "docs", "DEFECT_A_EVAL_SEAL_2026-10-14.md")
DRAW = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "draw_2026-10-14.json")
OPENED = os.path.join(ROOT, "fixtures", "xbrl", "defect_a", "opened_2026-10-14.json")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")


def _draw_module():
    p = os.path.join(ROOT, "measure", "defect_a_draw_2026-10-14.py")
    spec = importlib.util.spec_from_file_location("defect_a_draw", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class DrawTest(unittest.TestCase):
    def setUp(self):
        self.m = _draw_module()
        self.rec = json.load(io.open(DRAW, encoding="utf-8"))
        with io.open(SEAL, encoding="utf-8") as fh:
            self.seal = fh.read()

    def test_the_draw_reproduces(self):
        self.assertEqual(self.m.draw(), self.rec["docs"])

    def test_eight_documents(self):
        self.assertEqual(len(self.rec["docs"]), 8)
        self.assertEqual(len(set(self.rec["docs"])), 8)

    def test_the_three_sealed_groups_still_reproduce(self):
        order = self.m.order_and_check()
        split = json.load(io.open(SPLIT, encoding="utf-8"))
        self.assertEqual(split["final_eval_sealed"], order[14:22])

    def test_no_overlap_with_the_twenty_six_used_documents(self):
        order = self.m.order_and_check()
        self.assertEqual(set(self.rec["docs"]) & set(order[:26]), set())

    def test_the_sample_is_not_the_final_eval_eight(self):
        split = json.load(io.open(SPLIT, encoding="utf-8"))
        self.assertEqual(set(self.rec["docs"]) & set(split["final_eval_sealed"]), set())

    def test_every_drawn_document_is_named_in_the_seal(self):
        for d in self.rec["docs"]:
            self.assertIn(d, self.seal, d)

    def test_the_seal_names_no_other_document(self):
        import re
        named = set(re.findall(r"S100[A-Z0-9]{4}", self.seal))
        self.assertEqual(named, set(self.rec["docs"]))

    def test_the_draw_script_refuses_to_overwrite(self):
        self.assertTrue(os.path.exists(DRAW))
        with self.assertRaises(SystemExit):
            self.m.main()


class SealTextTest(unittest.TestCase):
    def setUp(self):
        with io.open(SEAL, encoding="utf-8") as fh:
            self.seal = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in l.strip().strip("|").split("|")]
                     for l in self.seal.splitlines() if l.strip().startswith("|")]

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_the_four_pass_lines_are_fixed(self):
        for sym, line in (("F-1", "≥ 90%"), ("F-2", "= 0"), ("F-3", "= 0"), ("F-4", "≥ 20")):
            hit = self._row(sym)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (sym, len(hit)))
            self.assertEqual(hit[0][-1], line, "%s: %s" % (sym, hit[0]))

    def test_the_five_predictions_are_fixed(self):
        for sym in ("P-1", "P-2", "P-3", "P-4", "P-5"):
            self.assertEqual(len(self._row(sym)), 1, sym)
        self.assertIn("4", self._row("P-1")[0][-1])
        self.assertIn("7", self._row("P-2")[0][-1])
        self.assertIn("20", self._row("P-3")[0][-1])
        self.assertIn("0", self._row("P-4")[0][-1])

    def test_the_seal_says_the_thresholds_do_not_move(self):
        self.assertIn("結果を見て閾値を変更しない", self.seal)
        self.assertIn("この基準では判定不能", self.seal)
        self.assertIn("失敗したら閾値を緩めず、原因を記録して止める", self.seal)

    def test_the_seal_forbids_reusing_the_final_eval_eight(self):
        self.assertIn("再利用しない", self.seal)

    def test_the_seal_only_names_the_key_by_its_variable_name(self):
        self.assertIn("EDINET_API_KEY", self.seal)
        self.assertIn("鍵はチャットにもログにも出さない", self.seal)


class NotYetOpenedTest(unittest.TestCase):
    """開封の記録が出来るまで、8 書類の ZIP が手元に無いことを留める。"""

    def test_the_cache_path_layout_is_still_what_this_test_assumes(self):
        p = edinet.cache_path("S100Z448")
        self.assertTrue(p.endswith(os.path.join("edinet", "S100Z448.zip")), p)

    def test_the_zips_are_absent_until_the_opening_is_recorded(self):
        if os.path.exists(OPENED):
            self.skipTest("開封済み(記録あり)。この確認は役目を終えた")
        docs = json.load(io.open(DRAW, encoding="utf-8"))["docs"]
        present = [d for d in docs if os.path.exists(edinet.cache_path(d))]
        self.assertEqual(present, [], "封を開ける前に取得されている: %s" % present)


if __name__ == "__main__":
    unittest.main()
