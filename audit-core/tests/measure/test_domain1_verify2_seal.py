# -*- coding: utf-8 -*-
"""検証層の直しの封(docs/DOMAIN1_VERIFY2_SEAL_2026-10-17.md)を固定する。

**「同じ材料の数を性能と書かない」「既存製品は測れない」が落ちないことを門で見る。**
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_VERIFY2_SEAL_2026-10-17.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class ArithmeticDisclosureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_the_human_four_conditions_are_quoted(self):
        head = self.t[:self.t.index("\n## §0")]
        for k in ("**LLM が申告した誤りを、検証器が勝手に消さない。**",
                  "**「誤りの存在」「誤りの種類」「本来の参照先」を別々に採点する。**",
                  "**検出・見落とし・偽警報・保留を独立して集計する。**",
                  "**同じ材料での修正結果と、未使用の別資料での結果を"
                  "分けて報告する。**"):
            self.assertIn(k, head, k)

    def test_2_what_is_arithmetic_is_separated_from_what_is_measured(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn("この便の数のほとんどは算術で決まる**", b)
        self.assertIn("これは性能の証拠ではない。**", b)
        self.assertIn("**だからこの便の結果に「性能」という語を使わない。**", b)
        self.assertIn("**性能は未使用の別資料((2))でしか測れない**", b)
        self.assertIn("commit `1ab6a79`", b)


class CompositionRuleTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_3_the_seat_is_never_overwritten(self):
        b = sec(self.t, "### §1-1", "### §1-2")
        self.assertIn("**席が何か言ったときは消さない。"
                      "席が黙っているときだけ検証器が決める。**", b)
        self.assertIn("**検証器が独自に見つけた不一致は足す(論理和)。**", b)
        rows = [l for l in b.split("\n") if l.startswith("| ") and "---" not in l]
        self.assertEqual(len(rows), 5, "見出し 1 行 + 4 行")

    def test_4_the_verifier_does_not_claim_what_it_cannot_say(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        self.assertIn("**検証器は `列の取り違え` などを言えない**", b)
        self.assertIn("**言えないものを言ったことにしない。**", b)
        self.assertIn("Core 単体 2/8", b)

    def test_5_the_two_rows_are_not_scored_by_one_metric(self):
        b = sec(self.t, "### §1-3", "## §2")
        self.assertIn("**席が出した住所は「誤った値の出どころ」として"
                      "別の欄に残す。**", b)
        self.assertIn("**2 つを同じ指標で採点しない**", b)

    def test_6_four_buckets_are_independent(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn("**4 つを別々に数える。足し合わせた 1 つの数にしない。**", b)
        for k in ("**検出**", "**見落とし**", "**保留**", "**偽警報**"):
            self.assertIn(k, b, k)
        self.assertIn("**1 件。別記**", b)


class ArmsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_7_five_arms_with_grep_standing_in_for_products(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*(A|B|C′|D|D′)\*\*", b)
        self.assertEqual(ids, ["A", "B", "C′", "D", "D′"], "5 方式")
        self.assertIn("**既存製品(Google・NVIDIA・商用の照合製品)は"
                      "ライセンスと接続の都合で\n手元で測れない。"
                      "だから「既存製品と比べた」とは書かない。**", b)
        self.assertIn("**書けるのは「素朴な値一致照合と比べた」だけである。**", b)

    def test_8_two_main_comparisons(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn("**C′ 対 A**", b)
        self.assertIn("**C′ 対 D′**", b)
        self.assertIn("grep を超えるか", b)

    def test_9_predictions_per_arm_and_axis(self):
        b = sec(self.t, "## §4 予測", "## §5")
        ids = re.findall(r"(?m)^\| \*\*H-(\d+)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 11)], "H-1〜H-10")
        self.assertIn("**A 対 C の予測が 1 本も無かった。**", b)
        self.assertIn("**H-1・H-4・H-8 は算術で決まる。当たっても手柄にしない。**", b)
        self.assertIn("**測る意味が在るのは H-3・H-5・H-7・H-10 である。**", b)


class FailureAndSplitTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_10_failure_conditions(self):
        b = sec(self.t, "## §5 失敗条件", "## §6")
        self.assertEqual(b.count("**実験は無効**"), 1)
        self.assertEqual(b.count("**失敗**"), 5)
        self.assertIn("**同じ材料の結果を「性能」と書いた**", b)
        self.assertIn("**「既存製品と比べた」と書いた**", b)
        self.assertIn("**算術で決まる数を成果として書いた**", b)

    def test_11_same_material_and_new_material_are_split(self):
        b = sec(self.t, "## §6", "## §7")
        self.assertIn("**「同じ材料での修正結果」と見出しに書く。**", b)
        self.assertIn("同じ表に混ぜない", b)
        self.assertIn("**この封では (2) の採点基準を決めない**", b)
        self.assertIn("**人間の許可が要る。**", b)

    def test_12_eight_limits(self):
        b = sec(self.t, "## §7 示せないこと", "## §8")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 9)], "限界は 8 本")
        self.assertIn("**設計の確認**であって性能ではない", b)
        self.assertIn("**既存製品は測れない**", b)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_VERIFY2_SEAL_2026-10-17.md"
    AFTER = ("measure/sheet_verify2_2026-10-17.py",
             "fixtures/sheet/verify2_2026-10-17.json",
             "docs/DOMAIN1_VERIFY2_RESULT_2026-10-17.md")
    FROZEN = ("fixtures/sheet/errdet_answers_seat1_2026-10-17.json",
              "fixtures/sheet/errdet_answers_seat2_2026-10-17.json")

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

    def test_13_seal_precedes_the_fix(self):
        self.assertTrue(self._tracked(self.SEAL_REL), "pathspec の誤り")
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)

    def test_14_the_seat_answers_were_frozen_before_the_seal(self):
        """**席の答えは直しより先に凍結されている**(後から選べない)。"""
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.FROZEN:
            a = self._added(rel)
            self.assertIsNotNone(a, rel)
            self.assertTrue(self._ancestor(a, seal), "**席の答えが封より後**: %s"
                            % rel)


if __name__ == "__main__":
    unittest.main()
