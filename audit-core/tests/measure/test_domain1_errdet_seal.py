# -*- coding: utf-8 -*-
"""誤り検出の封(docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md)を固定する。

守るのは封 §9 の 18 つ。**この実験は Core の優位性を測るものではない**という
人間の字が落ちないことも門で見る。
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_ERRDET_SEAL_2026-10-17.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class PurposeTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_this_is_not_about_core_winning(self):
        head = self.t[:self.t.index("\n## §1")]   # 表題は先頭なので改行が無い
        self.assertIn("**大事なのは、Core が LLM より優れていると"
                      "証明することではありません。", head)
        self.assertIn("**この実験は Core の優位性を測るものではない。**", head)
        self.assertIn("**Core 単体(B)は参考群**", head)
        self.assertIn("**B が勝っても製品の結論にしない。**", head)

    def test_2_the_gold_comes_from_the_source_and_the_change_log(self):
        b = sec(self.t, "## §1 材料", "### §1-1")
        self.assertIn("**改変前の原資料と、機械が作った改変記録から確定する。**"
                      "Core の判定規則を使わない", b)
        self.assertIn("**誤りは正解集合の 24 件にだけ植える。**", b)
        self.assertIn("**生成** | **しない。文字列の置換だけ。費用 0 USD**",
                      b.replace("| 生成", "**生成**"))

    def test_3_one_error_per_variant_and_the_bundle_is_cross_checked(self):
        b = sec(self.t, "### §1-1", "## §2")
        self.assertIn("**1 つの変種は 1 つの誤りしか持たない**", b)
        self.assertIn("injected-errors-contaminate-each-other", b)
        self.assertIn("同じ文に 2 件入れない。**", b)
        self.assertIn("**変わったら、束ねた変種を LLM 側に使わない。**", b)


class ErrorGenerationTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_4_targets_are_chosen_by_rule_not_by_me(self):
        b = sec(self.t, "### §2-1", "### §2-2")
        self.assertIn("**私が選ばない**", b)
        self.assertIn("**文 17 は使わない。**", b)
        self.assertIn("§2-4 の罠", b)
        self.assertIn("**8 文・8 件**", b)

    def test_5_two_groups_two_types_each_with_postconditions(self):
        b = sec(self.t, "### §2-2", "### §2-3")
        for k in ("**I-1 桁の入れ替え**", "**I-2 末尾 1 桁の差**",
                  "**II-1 列の取り違え**", "**II-2 別の科目の値**"):
            self.assertIn(k, b, k)
        self.assertIn("**原資料との照合だけで機械的に検出できる**", b)
        self.assertIn("**文脈の理解が必要**", b)
        self.assertIn("**抜粋の 176 セルに 0 件**かつ**索引 4,209 行に 0 件**", b)
        self.assertIn("**抜粋に在る**こと。かつ**正しい参照先の値と違う**こと", b)
        self.assertIn("**同じ文の中に既に出ている数と一致しない**", b)

    def test_6_the_assignment_is_material_driven_and_stratified(self):
        b = sec(self.t, "### §2-3", "### §2-4")
        self.assertIn("**材料が決める。私が決めない**", b)
        self.assertIn("**「作れる文の数」の昇順**", b)
        self.assertIn("**層化に Core の結果(結べた / 結べなかった)を使う。"
                      "正解ラベルには使っていない。**", b)
        self.assertIn("**8 件そろわなければ「そろわなかった」と書く。"
                      "規則を緩めない。**", b)

    def test_7_the_false_alarm_trap_is_r035_only(self):
        b = sec(self.t, "### §2-4", "## §3")
        self.assertIn("`R035`", b)
        self.assertIn("**報告文は正しい。**", b)
        self.assertIn("**だから検出率の分母に入れない。偽警報の側で別に数える。**", b)
        self.assertIn("**罠は `R035` の 1 件だけで測る。**", b)


class ScoringTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_8_detect_hold_and_miss_are_exclusive(self):
        b = sec(self.t, "### §3-1", "### §3-2")
        self.assertIn("**互いに排他**", b)
        self.assertIn("**保留は検出ではない。**", b)
        self.assertIn("保留を検出に数えると「全部保留する道具」が最高点を取る", b)
        for k in ("**検出**", "**保留**", "**見落とし**"):
            self.assertIn(k, b, k)

    def test_9_three_separate_scores_and_a_fixed_vocabulary(self):
        b = sec(self.t, "### §3-2", "### §3-3")
        self.assertIn("**検出-1 誤りだと言えたか**", b)
        self.assertIn("**検出-2 正しい根拠を提示できたか**", b)
        self.assertIn("**検出-3 誤りの種類を特定できたか**", b)
        vocab = ("値が原資料に無い", "列の取り違え", "別の科目の値",
                 "親階層の取り違え", "単位・符号の表記", "不明")
        for v in vocab:
            self.assertIn(v, b, v)
        self.assertEqual(len(vocab), 6, "固定語彙は 6 語")

    def test_10_false_alarm_and_hold_are_separated(self):
        b = sec(self.t, "### §3-3", "### §3-4")
        self.assertIn("**偽警報と保留を分ける**", b)
        self.assertIn("**27 件**", b)
        self.assertIn("**1 件。別記する**", b)

    def test_11_thresholds_are_set_before_measuring(self):
        b = sec(self.t, "### §3-4", "## §4")
        ids = re.findall(r"(?m)^\| \*\*E-(\d)\*\*", b)
        self.assertEqual(ids, ["1", "2", "3", "4"], "E-1〜E-4")
        self.assertIn("**見落とし = 0 件**", b)
        self.assertIn("**E-4 は予測であって合否ではない**", b)
        self.assertIn("**天井が在ることを失敗とは書かない**", b)

    def test_12_eight_predictions(self):
        b = sec(self.t, "## §4 予測", "## §5")
        ids = re.findall(r"(?m)^\| \*\*F-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)], "F-1〜F-8")
        self.assertIn("**測る前に書く。外れは外れとして残す**", b)


class AversusCTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_13_three_arms_with_b_as_a_reference_group(self):
        b = sec(self.t, "### §5-1", "### §5-2")
        self.assertIn("**主比較は A 対 C。B は参考群**", b)
        self.assertIn("**参考群。製品の結論にしない**", b)
        self.assertIn("**入力差はゼロである。**", b)
        self.assertIn("**同じ 1 回の生成**", b)

    def test_14_what_the_llm_sees_is_fixed_and_the_reading_is_disclosed(self):
        b = sec(self.t, "### §5-2", "### §5-3")
        self.assertIn("**Core の候補一覧・Core の状態・正解ラベル・誤りの件数・"
                      "誤りの型の割り当て**", b)
        self.assertIn("**「根拠情報」を「抜粋(原資料の行)」と読んだ。"
                      "Core の候補一覧は渡さない。**", b)
        self.assertIn("**人間の意図が「Core の候補も渡す」であれば、"
                      "LLM 側の実行前に差し替える**", b)
        self.assertIn("**これは交絡である。**", b)

    def test_15_the_verifier_has_four_values_and_uses_m3_prime(self):
        b = sec(self.t, "### §5-3", "### §5-4")
        self.assertIn("`reach()`(M-3′)を使う。**", b)
        self.assertIn("**M-3 の数も併記する。**", b)
        for v in ("**確認できない(参照先が無い)**",
                  "**確認できない(値が一意でない)**",
                  "**原資料と一致しない**", "**確認済み**"):
            self.assertIn(v, b, v)
        self.assertIn("**C の出力はこの 4 値だけである。"
                      "LLM の断定をそのまま顧客に出さない。**", b)

    def test_16_c_wins_only_if_misses_fall_and_false_alarms_do_not_rise(self):
        b = sec(self.t, "### §5-4", "### §5-5")
        ids = re.findall(r"(?m)^\| \*\*G-(\d)\*\*", b)
        self.assertEqual(ids, ["1", "2", "3"], "G-1〜G-3")
        self.assertIn("**G-3 を満たさなければ「上回った」と書かない。**", b)
        self.assertIn("**「A と C の差がなければ、機械検証を加える価値が"
                      "今回の条件では確認できない」**", b)
        self.assertIn("**C が優れても、別の誤り種類や別資料で再現するかは別問題**", b)

    def test_17_the_estimate_is_not_a_guarantee(self):
        b = sec(self.t, "### §5-5", "## §6")
        self.assertIn("**Core 単体(§3・§4)は 0 USD。**", b)
        self.assertIn("見込み 2 USD ― これは見込みであって保証値ではない**", b)
        self.assertIn("**上限は実測で 4 USD。**", b)
        self.assertIn("**超えそうなら実行前に止める。超えたら打ち切って"
                      "途中までを記録する。**", b)

    def test_18_failures_and_limits(self):
        f = sec(self.t, "## §6 失敗条件", "## §7")
        self.assertIn("**結果を見てから誤りの生成規則・採点基準・閾値を変えた**", f)
        self.assertIn("**人工の誤りでの成功を、顧客価値や販売可能性の証明として"
                      "書いた**", f)
        b = sec(self.t, "## §7 示せないこと", "## §8")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 9)], "限界は 8 本")
        self.assertIn("**人工的な誤りを検出できても、実際の文書で起きる誤りを"
                      "検出できるとは限らない**", b)
        self.assertIn("**`R035` 型(抽出の符号落ち)は私の欠陥であって"
                      "文書の誤りではない。**", b)
        self.assertIn("**Core の優位性を証明するものではない**", b)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md"
    AFTER = ("measure/sheet_errdet_make_2026-10-17.py",
             "measure/sheet_errdet_core_2026-10-17.py",
             "measure/sheet_errdet_question_2026-10-17.py",
             "fixtures/sheet/errdet_make_2026-10-17.json",
             "fixtures/sheet/errdet_core_2026-10-17.json")

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

    def test_19_seal_precedes_everything(self):
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


if __name__ == "__main__":
    unittest.main()
