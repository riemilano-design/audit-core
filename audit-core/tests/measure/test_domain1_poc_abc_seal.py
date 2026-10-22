# -*- coding: utf-8 -*-
"""顧客向け PoC 第 1 便の封(docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md)を固定する。

**封は正解集合より先・採点より先・C を走らせるより先に commit する。**
守るのは 14 つ(封 §10)。
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_POC_ABC_SEAL_2026-10-17.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    """**節を見出しの行頭で切り出す。**

    `t.split("## §6")` は `### §6-1` にも当たって**空の節を返す**
    (2026-10-17 に私の門が踏んだ)。だから**行頭 + 見出しの字**で切る。
    """
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class GoldIsTwoStageTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_value_uniqueness_is_not_the_gold(self):
        b = self.t.split("### §2-1")[1].split("### §2-2")[0]
        for k in ("**値の候補が一意**", "**値だけでは曖昧**", "**値が不一致**"):
            self.assertIn(k, b, k)
        self.assertIn("**「値の候補が一意」は、そのセルが参照先であることを意味しない。**", b)
        self.assertIn("**この段では正解集合を作らない。**", b)

    def test_2_four_independent_conditions_all_required(self):
        b = self.t.split("### §2-2")[1].split("### §2-3")[0]
        for i in (1, 2, 3, 4):
            self.assertIn("**G-独立-%d**" % i, b)
        self.assertIn("**4 つすべてを満たしたものだけを正解集合に入れる。**", b)
        self.assertIn("**1 つでも欠けたら別枠にし、"
                      "「どの条件が欠けたか」を件ごとに記録する。**", b)
        self.assertIn("**Core の規則(索引・別名表・親の絞り・6 欄の鍵・値の照合)を"
                      "一切使わない。**", b)

    def test_3_shared_and_not_shared_is_disclosed(self):
        b = self.t.split("### §2-3")[1].split("### §2-4")[0]
        self.assertIn("**共有している**", b)
        self.assertIn("**共有していない**", b)
        self.assertIn("**だから「完全に独立した正解」ではない。**", b)
        self.assertIn("**独立しているのは「Core の判定規則から」である。**", b)

    def test_4_surface_forms_are_not_blind(self):
        b = self.t.split("### §2-4")[1].split("## §3")[0]
        self.assertIn("`予算現在額`", b)
        self.assertIn("**盲検ではない。**", b)
        self.assertIn("**G-独立-4 を表層形なしで厳格にした数も併記する。**", b)
        self.assertIn("**この表は結果を見てから書き換えない。**", b)


class DoubleScoringTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_5_scope_is_scored_both_ways(self):
        b = sec(self.t, "## §3 会計の欄の二重採点", "## §4 指標")
        self.assertIn("**主採点(寛容)**", b)
        self.assertIn("**併記(厳格)**", b)
        self.assertIn("**A にも B にも同じ寛容さを当てる**", b)
        self.assertIn("**主採点と同じ表に並べる。埋もれさせない**", b)
        self.assertIn("**どちらか一方だけを性能の結論に使わない**", b)


class MetricsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_6_five_metrics_with_written_denominators(self):
        b = sec(self.t, "## §4 指標", "### §4-1")
        rows = [l for l in b.split("\n") if l.startswith("| **M-")]
        self.assertEqual(len(rows), 5, rows)
        for r in rows:
            self.assertEqual(r.count("|"), 4, "分母の欄が無い: %s" % r)
        self.assertIn("**正解集合**(別枠を含まない)", b)
        self.assertIn("**M-1 と必ず並べる**", b)

    def test_7_pointer_is_not_in_the_m3_denominator(self):
        b = self.t.split("### §4-1")[1].split("### §4-2")[0]
        self.assertIn("**A にも B にも C にも同じものを当てる**", b)
        self.assertIn("**pointer の有無を M-3 の分母にしない**", b)
        self.assertIn("A を弱い条件で比べることになる", b)

    def test_8_every_claim_is_recorded(self):
        b = self.t.split("### §4-2")[1].split("## §5")[0]
        self.assertIn("**35 件すべてを 1 行ずつ記録する**", b)
        self.assertIn("接続 / 保留 / 判定不能", b)
        self.assertIn("**正解不明の件数を隠さない。**", b)


class CostAndFairnessTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_9_estimate_is_not_a_measurement(self):
        b = sec(self.t, "## §5 費用と回数", "## §6 予測")
        self.assertIn("**これは見積もりであって実測ではない**", b)
        self.assertIn("**C を走らせる前に人間へ報告して許可を得る。**", b)
        self.assertIn("**A・B は 0 USD**", b)
        self.assertIn("**やり直しをしない。**", b)

    def test_10_the_general_llm_is_not_handicapped(self):
        b = self.t.split("### §1-1")[1].split("## §2")[0]
        self.assertIn("**これは A に有利な条件である。**", b)
        self.assertIn("**A の答えはこの封より先に commit されている。**", b)
        self.assertIn("**席は正解基準の存在を知らずに答えた**", b)
        self.assertIn("入力の差は「Core の証拠情報を足した」1 点だけ", b)
        self.assertIn("**結果を見てから採点条件を変えない。**", b)


class PredictionsAndInterpretationTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_11_predictions_are_split_blind_and_informed(self):
        b = sec(self.t, "## §6 予測", "## §7 結果の解釈")
        self.assertIn("**A・B の性能に関する予測は盲検ではない。当たっても手柄にしない。**",
                      b)
        v = re.findall(r"(?m)^\| \*\*V-(\d+)\*\*", b)
        w = re.findall(r"(?m)^\| \*\*W-(\d+)\*\*", b)
        self.assertEqual(v, [str(i) for i in range(1, 7)], "盲検は 6 本")
        self.assertEqual(w, [str(i) for i in range(1, 6)], "既知は 5 本")
        self.assertIn("**測ったあとに書き換えない。", b)

    def test_12_four_branches_and_three_first_questions(self):
        b = sec(self.t, "## §7 結果の解釈", "## §8 示せないこと")
        self.assertIn("**Core の差別化は弱い。売り方か製品設計を見直す**", b)
        self.assertIn("**保留を増やすだけでは価値にならない可能性**", b)
        self.assertIn("**証拠検証レイヤーとしての価値を示す有力な結果**", b)
        self.assertIn("**汎用的な資産価値はまだ主張しない**", b)
        self.assertIn("**差が出なければ「差が出なかった」と書く。**", b)
        self.assertIn("**差が出ないのに開発を続ける理由を作らない。**", b)
        nums = re.findall(r"(?m)^(\d)\. \*\*", b)
        self.assertEqual(nums, ["1", "2", "3"], "最初に見る 3 点")

    def test_13_seven_limits(self):
        b = sec(self.t, "## §8 示せないこと", "## §9 手順")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 8)], "限界は 7 本")
        self.assertIn("「完全に独立」ではない", b)
        self.assertIn("**A に有利な条件**", b)
        self.assertIn("**工数(時間)は測らない。**", b)
        self.assertIn("**顧客が買うかどうかは測れない。**", b)


class CommitOrderTest(unittest.TestCase):
    """**封が正解集合・採点より先**、かつ **A の答えが封より先**。"""

    SEAL_REL = "docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md"
    AFTER = ("fixtures/sheet/poc_gold_2026-10-17.json",
             "fixtures/sheet/poc_ab_score_2026-10-17.json",
             "fixtures/sheet/poc_c_answers_seat1_2026-10-17.json")
    BEFORE = ("fixtures/sheet/m11_answers_seat1_2026-10-16.json",
              "fixtures/sheet/m11_answers_seat2_2026-10-16.json",
              "fixtures/sheet/m11_binds_2026-10-16.json")

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

    def _seal_or_fail(self):
        sha = self._added(self.SEAL_REL)
        self.assertIsNotNone(sha, "封がまだ commit されていない(順を測れない)")
        return sha

    def test_14_seal_is_committed(self):
        self.assertTrue(self._tracked(self.SEAL_REL),
                        "道が git に当たっていない(pathspec の誤り)")
        self.assertIsNotNone(self._added(self.SEAL_REL), "封がまだ commit されていない")

    def test_15_seal_precedes_the_gold_and_the_scores(self):
        seal = self._seal_or_fail()
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "封と %s が同じ commit に在る" % rel)
            self.assertTrue(self._ancestor(seal, other),
                            "封が %s より後に commit されている" % rel)
            self.assertFalse(self._ancestor(other, seal))

    def test_16_the_general_llm_answered_before_the_seal(self):
        """**A の答えは封より先。**席は正解基準を知らずに答えた。"""
        seal = self._seal_or_fail()
        for rel in self.BEFORE:
            other = self._added(rel)
            self.assertIsNotNone(other, rel)
            self.assertTrue(self._ancestor(other, seal),
                            "**%s が封より後に commit されている ― 盲検が崩れる**" % rel)
            self.assertFalse(self._ancestor(seal, other))


if __name__ == "__main__":
    unittest.main()
