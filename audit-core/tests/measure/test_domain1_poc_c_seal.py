# -*- coding: utf-8 -*-
"""PoC 方式 C の封(docs/DOMAIN1_POC_C_SEAL_2026-10-17.md)を固定する。

守るのは封 §10 の 14 つ。**金銭が動く実験の封なので、commit の順も門で見る。**
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_POC_C_SEAL_2026-10-17.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    """**行頭の見出しで割る。**`## §6` が `### §6-1` に当たらないようにする。"""
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class InputIsAPlusOneSectionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_c_is_a_with_one_section_appended(self):
        b = sec(self.t, "## §1 C は何か", "## §2")
        self.assertIn("`c_text.startswith(a_text)`", b)
        self.assertIn("**偽なら実験は無効**", b)
        self.assertIn("**seat1 = `model=sonnet`・順そのまま / "
                      "seat2 = `model=haiku`・逆順**", b)
        self.assertIn("**各席 1 回だけ。やり直しをしない。**", b)
        self.assertIn("commit `a5f6dc6`", b)

    def test_2_model_identity_is_not_machine_checked(self):
        b = sec(self.t, "## §1 C は何か", "## §2")
        self.assertIn("下にある model の id を機械で確かめる手段を持たない", b)
        self.assertIn("**「同じモデルであることを確認した」とは書かない。**", b)

    def test_3_state_wording_table_has_six_rows_and_no_internal_names(self):
        b = sec(self.t, "### §2-2", "### §2-3")
        rows = [l for l in b.split("\n")
                if l.startswith("| ") and "---" not in l]
        self.assertEqual(len(rows), 7, "見出し 1 行 + 6 行")
        self.assertIn("**内部の状態名(英字)・経路の記号・内部の規則名は "
                      "1 つも書かない。**", b)
        for bad in ("GROUNDED", "UNVERIFIABLE", "VALUE_MISMATCH",
                    "POINTER_NOT_FOUND"):
            self.assertNotIn(bad, b, "言い換え表に内部の名前が在る: %s" % bad)

    def test_4_candidate_listing_rule_is_fixed_before_running(self):
        b = sec(self.t, "### §2-3", "### §2-4")
        self.assertIn("**6 欄の鍵が 8 通り以下のときだけ、鍵を全部並べる。"
                      "9 通り以上は件数だけ書き、並べない。**", b)
        self.assertIn("**候補範囲実験の B′(抜粋 76 行)は使わない。**", b)
        self.assertIn("だから抜粋 76 行の外の行も出る。**", b)
        self.assertIn("**値を隠さない。**", b)

    def test_5_the_instruction_wording_is_in_the_seal(self):
        b = sec(self.t, "### §2-4", "### §2-5")
        self.assertIn("**正しいとは保証されていません。**使っても、"
                      "無視してもかまいません。", b)
        self.assertIn("「道具を信じよ」とも「疑え」とも書かない", b)

    def test_6_what_is_not_added(self):
        b = sec(self.t, "### §2-5", "## §3")
        for k in ("正解集合", "**A の答え**",
                  "**候補範囲実験の結果(5 件解けた・76 行に限ると解ける)**",
                  "**Core の判定が正しいかどうか**"):
            self.assertIn(k, b, k)
        self.assertIn("**禁じ語を緩めるためではない。**", b)


class FairnessAndScoringTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_7_c_has_the_advantage_and_it_is_written(self):
        b = sec(self.t, "## §3 公平性", "## §4")
        self.assertIn("**A は証拠を見ていない。C は見ている。**"
                      "これは C に有利な条件である。", b)
        self.assertIn("**2 席の一致を証拠に数えない**", b)

    def test_8_the_grader_is_imported_not_rewritten(self):
        b = sec(self.t, "## §4 採点", "### §4-1")
        self.assertIn("**C 用に書き直さない**", b)
        self.assertIn("`normalize-both-sides-of-a-comparison`", b)
        for m in ("M-1 誤接続率", "M-2 回収率", "M-3 根拠の再現性", "M-3′",
                  "M-4 失敗時の挙動", "M-5 追加価値"):
            self.assertIn(m, b, m)

    def test_9_five_c_specific_metrics(self):
        b = sec(self.t, "### §4-1", "### §4-2")
        ids = re.findall(r"(?m)^\| \*\*D-(\d)", b)
        self.assertEqual(ids, [str(i) for i in range(1, 6)], "D-1〜D-5")

    def test_10_the_order_of_the_verdict(self):
        b = sec(self.t, "### §4-2", "## §5")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, ["1", "2", "3", "4"], "判定の順は 4 段")
        self.assertIn("**3 だけが増えて 1 または 2 が悪化したら"
                      "「改善」と書かない。**", b)
        self.assertIn("**誤接続が出たら、検出の改善で相殺しない。"
                      "安全性の問題として記録する**", b)

    def test_11_success_needs_three_conditions_and_two_void_conditions(self):
        b = sec(self.t, "## §5 成功条件", "## §6")
        nums = re.findall(r"(?m)^(\d)\. \*\*", b)
        self.assertEqual(nums, ["1", "2", "3"], "成功条件は 3 本")
        self.assertIn("**接続数の増加だけにしない**", b)
        self.assertEqual(b.count("**実験は無効**"), 2, "無効の条件は 2 本")
        self.assertIn("**打ち切り、途中までを記録する**", b)


class PredictionsCostAndLimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_12_predictions_are_split_blind_and_informed(self):
        blind = sec(self.t, "### §6-1", "### §6-2")
        known = sec(self.t, "### §6-2", "## §7")
        self.assertEqual(re.findall(r"(?m)^\| \*\*X-(\d)\*\*", blind),
                         [str(i) for i in range(1, 7)], "盲検は 6 本")
        self.assertEqual(re.findall(r"(?m)^\| \*\*Y-(\d)\*\*", known),
                         [str(i) for i in range(1, 6)], "既知は 5 本")
        self.assertIn("**C の答えをまだ 1 文字も見ていない**", blind)
        self.assertIn("**手柄にしない**", known)

    def test_13_cost_target_is_declared_unreachable_before_running(self):
        b = sec(self.t, "## §7 費用", "## §8")
        self.assertIn("**実行前に書く**", b)
        self.assertIn("**1.66 USD**", b)
        self.assertIn("**先に書く: 目標 0.5 USD は、この上限の約束"
                      "(全部が出力だと仮定する)では満たせない見込みである。**", b)
        self.assertIn("**4 USD を超えたら打ち切って途中までを記録する。**", b)
        self.assertIn("推測した実費は書かない", b)

    def test_14_eight_limits(self):
        b = sec(self.t, "## §8 示せないこと", "## §9")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 9)], "限界は 8 本")
        self.assertIn("**A と「同じ資料」ではない。**", b)
        self.assertIn("**A は既に 24/24 である。回収率には改善の余地が無い。**", b)
        self.assertIn("**モデルの id を機械で確かめていない**", b)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_POC_C_SEAL_2026-10-17.md"
    A_ANSWERS = "fixtures/sheet/m11_answers_seat1_2026-10-16.json"
    AFTER = ("measure/sheet_poc_c_material_2026-10-17.py",
             "measure/sheet_poc_c_freeze_answers_2026-10-17.py",
             "measure/sheet_poc_c_score_2026-10-17.py",
             "fixtures/sheet/poc_c_material_2026-10-17.json",
             "fixtures/sheet/poc_c_answers_seat1_2026-10-17.json",
             "fixtures/sheet/poc_c_answers_seat2_2026-10-17.json",
             "fixtures/sheet/poc_c_score_2026-10-17.json")

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

    def test_15_seal_precedes_material_generation_and_scoring(self):
        self.assertTrue(self._tracked(self.SEAL_REL), "pathspec の誤り")
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)
            self.assertFalse(self._ancestor(other, seal), rel)

    def test_16_a_answered_before_the_seal(self):
        """**A は証拠を見ていない。**答えが封より先に commit されていること。"""
        self.assertTrue(self._tracked(self.A_ANSWERS), "pathspec の誤り")
        a = self._added(self.A_ANSWERS)
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(a)
        self.assertIsNotNone(seal)
        self.assertTrue(self._ancestor(a, seal), "**A が封より後に在る**")
        self.assertFalse(self._ancestor(seal, a))


if __name__ == "__main__":
    unittest.main()
