# -*- coding: utf-8 -*-
"""contract v1 の封(docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_CONTRACT_V1_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("adapters/xbrl/verify_external.py",
         "measure/xbrl_contract_v1_2026-10-17.py",
         "fixtures/xbrl/cd8/contract_v1_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    return t[i:t.index("\n" + end, i)] if end else t[i:]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_the_four_human_points(self):
        b = sec(self.t, "## §0", "## §1")
        nums = re.findall(r"(?m)^(\d)\. \*\*", b)
        self.assertEqual(nums, ["1", "2", "3", "4"])
        self.assertIn(u"**規則が無い場合は、引き続き「実証不能」とする。**", b)

    def test_2_only_one_new_file_and_no_new_arithmetic(self):
        b = sec(self.t, "## §1", "## §2")
        self.assertIn(u"`adapters/xbrl/verify_external.py`", b)
        self.assertIn(u"**比較の算術は 1 つも新しく書かない。**", b)
        self.assertIn(u"**既存の経路を 1 行も変えない**", b)

    def test_3_three_rules_and_a_fallthrough(self):
        b = sec(self.t, "## §2", "## §3")
        rows = re.findall(r"(?m)^\| \*\*?(単一の値|差分|変化率)", b)
        self.assertEqual(rows, [u"単一の値", u"差分", u"変化率"])
        self.assertIn(u"**規則が無い → `実証不能`**", b)
        self.assertIn(u"**規則を増やさない。**", b)

    def test_4_same_composition_as_the_role_swap_seal(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md", b)
        self.assertIn(u"**判定の対応表を変えない**", b)

    def test_5_the_denominators_are_disclosed(self):
        b = sec(self.t, "## §4", "## §5")
        for row in (u"| 千円 | 37 |", u"| 百万円 | 31 |", u"| ％ | 17 |"):
            self.assertIn(row, b, row)
        self.assertIn(u"**だから「検証を試みられる行」は最大 68 である**", b)
        self.assertIn(u"**したがって 2 本要る規則(差分・変化率)は"
                      u"この材料では 1 件も発火しない。**", b)

    def test_6_what_cannot_be_shown_is_written_first(self):
        b = sec(self.t, "## §5", "## §6")
        self.assertIn(u"**B′ は検出も偽警報も動かせない。**", b)
        self.assertIn(u"**`判定できない` は 0 行**", b)
        self.assertIn(u"**この実験は「覆いと誤拒否の交換」を測るものである。**", b)

    def test_7_eight_predictions_with_failure_conditions(self):
        b = sec(self.t, "## §6", "## §7")
        ids = re.findall(r"(?m)^\| \*\*P-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(re.findall(u"外れ", b)), 10)
        self.assertIn(u"**P-5 は「同じ」の予測である。**当たっても"
                      u"**上回ったとは書かない。**", b)

    def test_8_the_verdict_counts_the_cost(self):
        b = sec(self.t, "## §7", "## §8")
        self.assertIn(u"**R-2 が増えたら、それは代価である。**", b)
        self.assertIn(u"**両方を同じ表に並べる。**", b)
        self.assertIn(u"**R-1 が 1 件でも出たら、覆いが増えても"
                      u"「進める」と書かない。**", b)

    def test_9_what_is_not_done(self):
        b = sec(self.t, "## §8", "## §9")
        for k in (u"**既存の経路を変えない**",
                  u"**単位・期間・次元の検査を足さない。**",
                  u"**リンクベースを読まない。**",
                  u"**規則を v1 の 3 つから増やさない。**",
                  u"**席を呼ばない。**",
                  u"**正解データで規則を調整しない。**"):
            self.assertIn(k, b, k)

    def test_10_an_independent_audit_is_in_the_plan(self):
        b = sec(self.t, "## §9")
        self.assertIn(u"**独立した監査を通す**", b)
        self.assertIn(u"CLAUDE.md の委任条件 1", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True,
                             text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_11_the_seal_precedes_implementation_and_measurement(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない(この便で commit する)")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(
                subprocess.run(["git", "merge-base", "--is-ancestor", seal,
                                other], cwd=ROOT,
                               capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
