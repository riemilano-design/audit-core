# -*- coding: utf-8 -*-
"""候補範囲 76 行の封(docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md)を固定する。

守るのは 10 つ(封 §8)。
"""
import hashlib
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_SCOPE76_SEAL_2026-10-17.md")
FROZEN = {"sheet_m7_engine_2026-10-15.py": "4574c3ea013d05a1",
          "sheet_sainyuu_engine_2026-10-16.py": "3a70b599672832d3",
          "sheet_m5_engine_2026-10-15.py": "6eb5723ef518e1b4"}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class OneVariableOnlyTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_only_the_candidate_population_changes(self):
        b = sec(self.t, "### §1-1", "### §1-2")
        self.assertIn("**変えるのは 1 つだけ**", b)
        self.assertIn("**索引 4,209 行(全部)**", b)
        self.assertIn("**抜粋 76 行に在る行だけ**", b)

    def test_2_the_rules_are_untouched(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        for k in ("6 欄の鍵・接続の一意性条件", "別名規則", "親の規則",
                  "主張の切り出し"):
            self.assertIn(k, b, k)
        self.assertIn("**だから限定するのは `bind` の候補だけである。**", b)
        self.assertIn("**`extract_claims` の結果が段 11 と同じ 35 件であることを"
                      "門で確かめる。**", b)

    def test_3_engine_shas_are_pinned_and_match(self):
        for name, want in FROZEN.items():
            p = os.path.join(MEASURE, name)
            with io.open(p, "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], want,
                                 "**%s が動いている**" % name)
        self.assertIn("`MIN_INDEPENDENT = 3`", self.t)
        self.assertIn("engine の sha が動いた", self.t)

    def test_4_both_sides_get_the_same_fold(self):
        b = sec(self.t, "### §1-3", "## §2")
        self.assertIn("engine が使っているのと同じ別名表", b)
        self.assertIn("**新しい別名規則は作らない。**", b)


class WhatIsMeasuredTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_5_seven_things_and_the_verdict_is_r4(self):
        b = sec(self.t, "## §2 測ること", "## §3")
        ids = re.findall(r"(?m)^\| \*\*R-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 8)], "R-1〜R-7")
        self.assertIn("← **これが判定**", b)
        self.assertIn("**判定は R-4 である。R-3 が増えても R-4 が増えなければ"
                      "成功と書かない。**", b)

    def test_6_the_cost_of_narrowing_is_measured(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn("**歯-A**", b)
        self.assertIn("**歯-B**", b)
        self.assertIn("**消えた分の代価を測らないと片側しか見ていない。**", b)
        self.assertIn("**人工材料での診断結果は、実データでの安全性の証明とは"
                      "分けて記録する**", b)
        self.assertIn("無ければ「この材料では作れない」と書く", b)

    def test_7_failure_conditions(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn("**差を「誤接続」として書く。接続数の増加で相殺しない**", b)
        self.assertIn("**規則を緩めて救済しない**", b)
        self.assertIn("**実験を無効にする**", b)
        self.assertIn("**この実験の結果で C の評価条件を作らない**", b)

    def test_8_eight_predictions(self):
        b = sec(self.t, "## §5 予測", "## §6")
        ids = re.findall(r"(?m)^\| \*\*S-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)], "予測は 8 本")
        self.assertIn("**まだ実装していない**", b)

    def test_9_five_limits_including_the_obvious_one(self):
        b = sec(self.t, "## §6 示せないこと", "## §7")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 6)], "限界は 5 本")
        self.assertIn("**候補を絞れば曖昧さが減るのは当たり前である。**", b)
        self.assertIn("「**母集団を変えると解ける**」である", b)
        self.assertIn("**顧客がその 76 行を照合対象として指定できるかは、"
                      "ここでは測れない。**", b)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md"
    AFTER = ("measure/sheet_scope76_2026-10-17.py",
             "fixtures/sheet/scope76_2026-10-17.json")

    @staticmethod
    def _added(rel):
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
            cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _tracked(rel):
        return subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                              cwd=ROOT, capture_output=True).returncode == 0

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_10_seal_precedes_the_implementation(self):
        self.assertTrue(self._tracked(self.SEAL_REL), "pathspec の誤り")
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)
            self.assertFalse(self._ancestor(other, seal))


if __name__ == "__main__":
    unittest.main()
