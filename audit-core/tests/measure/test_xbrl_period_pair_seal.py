# -*- coding: utf-8 -*-
u"""期間の対(PP)の封(docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("measure/xbrl_period_pair_rule_2026-10-19.py", "measure/xbrl_period_pair_2026-10-19.py",
         "fixtures/xbrl/cd8/period_pair_2026-10-19.json", "docs/XBRL_PERIOD_PAIR_RESULT_2026-10-19.md",
         "tests/measure/test_period_pair_rule.py", "tests/measure/test_xbrl_period_pair_result.py")


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

    def test_1_the_human_instruction_and_the_value_definition_are_named(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"**システムの価値そのものを向上させてね**", head)
        self.assertIn(u"**この封は「実証できる行の割合」を上げる**", head)
        self.assertIn(u"**0 USD・席は呼ばない。**", head)

    def test_2_the_rule_is_executable_and_does_not_choose_among_siblings(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"**ちょうど 1 本**", b)
        self.assertIn(u"**0 本・2 本以上なら `UNPROVABLE`、理由 `prior_sibling:<本数>`**", b)
        self.assertIn(u"`PCT_TOLERANCE_DEFAULT = 0.15`。新しい閾値は作らない", b)
        self.assertIn(u"**増・伸・上回**", b)
        self.assertIn(u"**減・下回・落ち**", b)
        self.assertIn(u"`derived_pointers`", b)
        self.assertIn(u"当たる例:", b)
        self.assertEqual(len(re.findall(u"当たらない例:", b)), 2)

    def test_3_denominators_are_literal_and_the_survey_is_declared(self):
        b = sec(self.t, "## §1", "## §2")
        for k in (u"**37**", u"**17**", u"1 本: **13**・2 本: **4**・0 本: 0", u"0.15 pt"):
            self.assertIn(k, b, k)
        self.assertIn(u"**下見で見たのは兄弟の本数だけ**", b)

    def test_4_four_controls_one_change_each(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"**故障を作って当てる。1 回に 1 件**", b)
        self.assertEqual(len(re.findall(r"(?m)^\| (値|符号|前期を消す|前期を増やす) \|", b)), 4)

    def test_5_fourteen_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*H-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 16)])
        for line in re.findall(r"(?m)^\| \*\*H-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**本当に測っているのは H-3〜H-8 である。**", b)
        self.assertIn(u"**62 → 75**", b)

    def test_6_limits(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn(u"**同じ 8 書類である。**", b)
        self.assertIn(u"**方向だけの主張(数が付かない 52 行の型)は触らない。**", b)
        self.assertIn(u"**PP は「席が当期を正しく名指した」ことを前提にする。**", b)

    def test_7_the_file_list_is_closed(self):
        b = sec(self.t, "## §5", "## §6")
        self.assertIn(u"**これ以外に触らない。**", b)
        for rel in AFTER:
            self.assertIn("`%s`" % rel, b, rel)
        self.assertIn(u"`core/py/` は 0 行", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_8_the_seal_precedes_the_implementation(self):
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
