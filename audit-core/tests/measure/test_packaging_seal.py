# -*- coding: utf-8 -*-
u"""包装の封(docs/PACKAGING_SEAL_2026-10-20.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/PACKAGING_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("pyproject.toml", "setup.cfg", "setup.py", "README.en.md",
         "tests/measure/test_packaging.py", "docs/PACKAGING_RESULT_2026-10-20.md",
         "tests/measure/test_packaging_result.py", "fixtures/packaging_2026-10-20.json")
RECORDS_README_MAY_CITE = (
    "fixtures/xbrl/cd8/attr_inject_2026-10-17.json",
    "fixtures/xbrl/cd8/holds_product_path_2026-10-19.json",
    "fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json",
    "fixtures/sheet/poc_ab_score_2026-10-17.json",
    "fixtures/sheet/errdet_cprime_2026-10-19.json",
    "fixtures/kokkai/false_pass_round12_2026-10-15.json",
    "fixtures/suite_coverage_2026-10-16.json",
)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_no_engine_change_and_no_new_capability(self):
        self.assertIn(u"**engine のコードは 1 行も変えない**", self.t)
        self.assertIn(u"**判定の規則・比較の算術・Adapter の中身は触らない。**", self.t)
        self.assertIn(u"**依存 0**", self.t)
        self.assertIn(u"`--no-build-isolation`", self.t)

    def test_2_four_items_two_console_scripts_and_a_closed_file_list(self):
        b = sec(self.t, "## §0", "### §0-1")
        self.assertEqual(re.findall(r"(?m)^\| (\d) \| ", b), ["1", "2", "3", "4"])
        self.assertIn("`pyproject.toml`・`setup.cfg`・`setup.py`", b)
        self.assertIn("`audit-core-verify-document` = `adapters.xbrl.verify_document:main`", b)
        self.assertIn("`audit-core-verify-external` = `adapters.xbrl.verify_external:main`", b)
        self.assertIn(u"**`AUDIT_CORE_PACKAGING=1` のときだけ**", b)
        self.assertIn(u"**これ以外に触らない**", b)
        for rel in AFTER:
            self.assertIn("`%s`" % rel, b, rel)
        self.assertIn(u"OSS の classifier を付けない", b)

    def test_3_the_records_the_readme_may_cite_are_listed(self):
        b = sec(self.t, "### §0-1", "## §1")
        for rel in RECORDS_README_MAY_CITE:
            self.assertIn("`%s`" % rel, b, rel)
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_4_six_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §1", "## §2")
        ids = re.findall(r"(?m)^\| \*\*G-(\d)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 7)])
        for line in re.findall(r"(?m)^\| \*\*G-\d\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], line)
        self.assertIn(u"**保護面の 36 本**", b)
        self.assertIn(u"**+2**", b)

    def test_5_limits(self):
        b = sec(self.t, "## §2")
        self.assertIn(u"**数は 1 つも増えない。**", b)
        self.assertIn(u"「正しい」の証拠ではない", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_6_the_seal_precedes_the_packaging(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
