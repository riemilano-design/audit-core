# -*- coding: utf-8 -*-
u"""門: `docs/PACKAGING_RESULT_2026-10-20.md` の数を
`fixtures/packaging_2026-10-20.json`(正本)に縛る。

**この file は試験を走らせない。**記録と文書の数が一致しているかだけを確かめる
(重い venv・wheel の実測は `test_packaging.py` の `AUDIT_CORE_PACKAGING=1` の方)。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REC_PATH = os.path.join(ROOT, "fixtures", "packaging_2026-10-20.json")
DOC_PATH = os.path.join(ROOT, "docs", "PACKAGING_RESULT_2026-10-20.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load():
    with io.open(REC_PATH, encoding="utf-8") as fh:
        return json.load(fh)


class RecordInternalConsistencyTest(unittest.TestCase):
    u"""記録そのものの内部整合(G-3 の本数が揃っているか等)。"""

    def setUp(self):
        self.rec = load()

    def test_1_g3_py_count_equals_frozen_count(self):
        g3 = self.rec["G-3"]
        self.assertEqual(g3["py_count"], g3["frozen_count"])
        self.assertEqual(g3["py_count"] + len(g3["non_py_files"]), g3["total_entries"])

    def test_2_g1_hit_is_false_and_matches_the_rcs(self):
        g1 = self.rec["G-1"]
        self.assertFalse(g1["hit"])
        self.assertEqual(g1["editable"]["install_rc"], 0)
        self.assertNotEqual(g1["editable"]["import_rc"], 0)

    def test_3_summary_hits_and_misses_count(self):
        s = self.rec["summary"]
        g_ids = ["G-1", "G-2", "G-3", "G-4", "G-5", "G-6"]
        hits = sum(1 for g in g_ids if self.rec[g]["hit"])
        misses = len(g_ids) - hits
        self.assertEqual(s["hits"], hits)
        self.assertEqual(s["misses"], misses)
        self.assertEqual(s["predictions"], len(g_ids))
        self.assertEqual(s["miss_ids"], [g for g in g_ids if not self.rec[g]["hit"]])

    def test_4_g5_plus_two_arithmetic(self):
        g5 = self.rec["G-5"]
        self.assertEqual(g5["test_files_on_disk_after"]
                         - g5["test_files_on_disk_before"], 2)
        self.assertEqual(g5["tests_measure_after"] - g5["tests_measure_before"], 2)
        self.assertEqual(g5["missed_discover_before"], g5["missed_discover_after"])

    def test_5_g3_sha256_observed_are_pairwise_distinct(self):
        shas = self.rec["G-3"]["sha256_observed"]
        self.assertEqual(len(shas), len(set(shas)),
                         u"3 回の wheel 構築が同じ sha256 になった"
                         u"(再現性ありに書き換わった可能性。測り直すこと)")
        self.assertTrue(self.rec["G-3"]["sha256_is_not_reproducible_across_rebuilds"])


class ResultDocMatchesRecordTest(unittest.TestCase):
    u"""結果文書の数が記録と一致すること(**文書の数の改ざんで赤くなる**ことが門の歯)。"""

    def setUp(self):
        self.t = text(DOC_PATH)
        self.rec = load()

    def test_6_summary_line_matches(self):
        s = self.rec["summary"]
        self.assertIn(u"**予測 当たり %d / 外れ %d(G-1)**" % (s["hits"], s["misses"]),
                     self.t)

    def test_7_per_field_verdicts_match(self):
        for g in ("G-1", "G-2", "G-3", "G-4", "G-5", "G-6"):
            verdict = u"当たり" if self.rec[g]["hit"] else u"**外れ**"
            rows = re.findall(r"(?m)^\| \*\*%s\*\* \|.*\|\s*$" % g, self.t)
            self.assertEqual(len(rows), 1, g)
            self.assertIn(verdict, rows[0], g)

    def test_8_g3_py_count_is_stated(self):
        g3 = self.rec["G-3"]
        self.assertIn(u"%d 本" % g3["py_count"], self.t)
        self.assertIn(g3["wheel_filename"], self.t)

    def test_9_g4_before_after_numbers_are_stated(self):
        g4 = self.rec["G-4"]
        self.assertIn("%d → %d"
                      % (g4["before_pyproject_collected"],
                         g4["after_pyproject_setup_cfg_setup_py_collected"]), self.t)

    def test_10_g5_before_after_numbers_are_stated(self):
        g5 = self.rec["G-5"]
        self.assertIn("%d → " % g5["test_files_on_disk_before"], self.t)
        self.assertIn("**%d**" % g5["test_files_on_disk_after"], self.t)
        self.assertIn("**%d**" % g5["tests_measure_after"], self.t)
        for f in g5["missed_discover_after"]:
            self.assertIn(f, self.t)

    def test_11_g1_root_cause_mentions_pep660_and_egg_link(self):
        self.assertIn("PEP 660", self.t)
        self.assertIn("egg-link", self.t)
        self.assertIn(self.rec["G-1"]["editable"]["import_stderr_tail"], self.t)

    def test_12_g1_non_editable_extra_measurement_is_disclosed(self):
        ne = self.rec["G-1"]["non_editable_extra_measurement"]
        self.assertEqual(ne["install_rc"], 0)
        self.assertEqual(ne["import_rc"], 0)
        self.assertIn(u"**追加の実測(封 G-1 の判定には使わない)**", self.t)

    def test_13_g3_sha256_non_reproducibility_is_disclosed(self):
        self.assertIn(u"**3 回とも違う sha256**", self.t)
        for sha in self.rec["G-3"]["sha256_observed"]:
            self.assertIn(sha, self.t)

    def test_14_limits_section_present(self):
        self.assertIn(u"**数は 1 つも増えていない。**", self.t)
        self.assertIn(u"**editable install は依然 rc=1。**", self.t)

    def test_15_no_engine_change_disclosed(self):
        self.assertIn(u"engine(`core/`・`adapters/`)は 0 行変更", self.t)


class SealPrecedesResultTest(unittest.TestCase):
    u"""封(予測)が結果より先に commit されていること(commit 済みのときだけ確かめる)。"""

    def test_16_seal_referenced_with_its_commit(self):
        self.assertIn("docs/PACKAGING_SEAL_2026-10-20.md", text(DOC_PATH))
        self.assertIn("`f4d956b`", text(DOC_PATH))


if __name__ == "__main__":
    unittest.main()
