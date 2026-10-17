# -*- coding: utf-8 -*-
"""P20 の封(docs/XBRL_P20_SEAL_2026-10-17.md)を固定する。

**封が実測より先に commit されていること**を git の順で確かめる。
**予測の file が動いていないこと**を sha256 で固定する。
"""
import hashlib
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_P20_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
PRED_REL = "fixtures/xbrl/cd8/branch_a_predictions_2026-10-17.json"
AFTER = ("measure/xbrl_p20_rerun_2026-10-17.py",
         "fixtures/xbrl/cd8/p20_rerun_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    return t[i:t.index("\n" + end, i)] if end else t[i:]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_the_purpose_is_not_performance(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"**性能改善の証明ではない。**", b)
        self.assertIn(u"**製品価値の実証ではない。**", b)
        self.assertIn(u"A 対 C′", b)
        self.assertIn(u"**この便では engine のコードを 1 行も変えない。**", b)

    def test_2_one_variable_only(self):
        b = sec(self.t, "## §1", "## §2")
        self.assertIn(u"`P16` → `P20`", b)
        self.assertIn(u"**呼ばない。費用 0 USD**", b)
        self.assertIn(u"**この 1 行を門で確かめる**", b)

    def test_3_two_profiles_differ_in_exactly_one_field(self):
        """**封が主張している「1 変数」をここで実際に確かめる。**"""
        import dataclasses
        import sys
        sys.path.insert(0, ROOT)
        from adapters.xbrl import vocabulary as V
        a = dataclasses.asdict(V.PROFILES["P16"])
        b = dataclasses.asdict(V.PROFILES["P20"])
        diff = {k for k in a if a[k] != b[k]}
        self.assertEqual(diff, {"name", "nonconsolidated_fallback"},
                         u"**1 変数でない: %s**" % sorted(diff))

    def test_4_six_measures_and_two_denominators(self):
        b = sec(self.t, "## §2", "## §3")
        ids = re.findall(r"(?m)^\| \*\*M-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 7)], u"M-1〜M-6")
        self.assertIn(u"**T5 の全部の行(50)と、1 対 1 の行だけ(26)の 2 つ**", b)
        self.assertIn(u"**M-3 を書かずに M-2 だけを報告しない。**", b)

    def test_5_the_prediction_file_is_pinned_and_untouched(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"**この file を編集しない。**", b)
        self.assertIn(u"cf4f5c9", b)
        out = subprocess.run(["git", "show", "cf4f5c9:./" + PRED_REL],
                             cwd=ROOT, capture_output=True)
        self.assertEqual(out.returncode, 0, u"予測が commit cf4f5c9 に無い")
        now = io.open(os.path.join(ROOT, PRED_REL), "rb").read()
        self.assertEqual(hashlib.sha256(out.stdout).hexdigest(),
                         hashlib.sha256(now).hexdigest(),
                         u"**予測の file が動いている**")

    def test_6_failure_conditions_are_written_before(self):
        b = sec(self.t, "## §4", "## §5")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, ["1", "2", "3", "4"])
        self.assertIn(u"**止めて報告する。**測り直さない。", b)
        self.assertIn(u"**1 変数でないので止める。**", b)

    def test_7_what_is_not_done(self):
        b = sec(self.t, "## §5", "## §6")
        for k in (u"**engine のコードを変えない**",
                  u"**fallback の適用条件を変えない。**",
                  u"**語彙・主語(仮説 B)に触らない。**",
                  u"**席を呼ばない。**",
                  u"**A 対 C′ を測り直さない。**"):
            self.assertIn(k, b, k)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True,
                             text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_8_the_seal_precedes_the_measurement(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない(この便で commit する)")
        seal = self._added(SEAL_REL)
        self.assertIsNotNone(seal)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, u"同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)
            self.assertFalse(self._ancestor(other, seal), rel)


if __name__ == "__main__":
    unittest.main()
