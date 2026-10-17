# -*- coding: utf-8 -*-
"""役割を替える実験の封(docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("measure/xbrl_role_swap_2026-10-17.py",
         "fixtures/xbrl/cd8/role_swap_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    return t[i:t.index("\n" + end, i)] if end else t[i:]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_three_arms_and_the_composition_is_written(self):
        b = sec(self.t, "## §1", "## §2")
        for k in (u"| **A** |", u"| **B** |", u"| **C** |"):
            self.assertIn(k, b, k)
        self.assertIn(u"**席の申告は上書きしない**", b)
        rules = re.findall(r"(?m)^\| `?(確認済み|誤りが在る|判定できない)", b)
        self.assertEqual(len(rules), 5, u"合成規則の行")
        self.assertIn(u"**実証不能**", b)

    def test_2_the_three_human_conditions_are_fixed(self):
        b = sec(self.t, "## §2", "## §3")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, ["1", "2", "3"])
        self.assertIn(u"**「正しい」とは書かない。**", b)
        self.assertIn(u"**単位・期間・次元(連結区分)・重複の 4 つ**", b)
        self.assertIn(u"**実験を成立させるために contract を足さない。**", b)
        self.assertIn(u"**差分・率の主張(参照先が 2 本要る行)を別集計にする。**", b)

    def test_3_seven_measures_with_denominators(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*R-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 8)])
        self.assertIn(u"**`実証不能` はどちらでも「正しい」に数えない。**", b)

    def test_4_the_predenominators_are_disclosed(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn(u"**この表は封の前に数えた。**", b)
        for row in (u"| 検証できた | 42 | 32 | 10 |",
                    u"| contract が無い | 24 | 10 | 14 |",
                    u"| 主張が無い | 12 | 1 | 11 |",
                    u"| 参照先が 2 本要る | 7 | 0 | 7 |"):
            self.assertIn(row, b, row)

    def test_5_what_this_material_cannot_show(self):
        b = sec(self.t, "## §5", "## §6")
        self.assertIn(u"**A の危険な誤通過は 0 件である**", b)
        self.assertIn(u"**したがって「B が危険な誤通過を減らす」ことは"
                      u"この材料では示せない。**", b)

    def test_6_eight_predictions_each_with_a_failure_condition(self):
        b = sec(self.t, "## §6", "## §7")
        ids = re.findall(r"(?m)^\| \*\*P-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(re.findall(u"外れ", b)), 9, u"外れる条件が各行に在る")
        self.assertIn(u"**同じなら上回っていない。**", b)

    def test_7_the_verdict_rule_is_the_humans_four_axes(self):
        b = sec(self.t, "## §7", "## §8")
        nums = re.findall(r"(?m)^(\d)\. \*\*", b)
        self.assertEqual(nums, ["1", "2", "3", "4"])
        self.assertIn(u"**等しいなら上回っていない。**", b)
        self.assertIn(u"**危険な誤通過(R-1)が増えたら、他が良くても"
                      u"「継続」と書かない。**", b)

    def test_8_what_is_not_done(self):
        b = sec(self.t, "## §8", "## §9")
        for k in (u"**engine を直さない**", u"**正解データで調整しない。**",
                  u"**実験を成立させるために contract を足さない**",
                  u"**席を呼ばない。**", u"**新しい指標を足さない。**"):
            self.assertIn(k, b, k)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True,
                             text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_9_the_seal_precedes_the_measurement(self):
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
                subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                               cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
