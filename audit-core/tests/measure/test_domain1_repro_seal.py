# -*- coding: utf-8 -*-
"""別資料での再現性の封(docs/DOMAIN1_REPRO_SEAL_2026-10-17.md)を固定する。

**「救済しない」「parser を直さない」「生成前に人間の再判断」が落ちないことを門で見る。**
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_REPRO_SEAL_2026-10-17.md")
FILES = (("op20250114_05kessan_01_soukatu.xlsx", "17,339"),
         ("op20250114_05kessan_02_sainyuu.xlsx", "100,564"),
         ("op20250114_05kessan_03_saisyutu.xlsx", "94,966"),
         ("op20250114_05kessan_04_jikoubetu_sainyuu.xlsx", "754,510"),
         ("op20250114_05kessan_05_jikoubetu_saisyutu.xlsx", "2,047,161"))


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

    def test_1_the_purpose_is_the_difference_not_superiority(self):
        head = self.t[:self.t.index("\n## §1")]
        self.assertIn("**測るのは差の再現である。**", head)
        self.assertIn("**「Core が優れている」と書くための封ではない。**", head)
        for k in ("**採点基準と予測を、生成前に封印してコミットする。**",
                  "**比較の中心は C′ 対 D′ とし、検出数だけでなく、"
                  "本来の参照先の正確性を測る。**",
                  "**別資料を使い、今回の人工誤りへの調整と、別資料でも通用する"
                  "能力を区別する。**",
                  "**予算は上限 3 USD を目安とし、超過が必要なら実行前に再判断する。**",
                  "**結果が悪くても、基準を変更して救済しない。**"):
            self.assertIn(k, head, k)


class MaterialTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_2_five_files_with_sizes_and_the_excluded_one(self):
        b = sec(self.t, "## §1 別資料", "### §1-1")
        for name, size in FILES:
            self.assertIn("`%s`" % name, b, name)
            self.assertIn("**%s**" % size, b, size)
        self.assertIn("op20250114_05kessan_06_jissitusyuusi.xlsx", b)
        self.assertIn("**取らないもの**", b)
        self.assertIn("CC BY 4.0", b)
        self.assertIn("**鍵は要らない**", b)

    def test_3_the_same_year_on_both_sides(self):
        b = sec(self.t, "## §1 別資料", "### §1-1")
        self.assertIn("**年度をまたいだ汚染**", b)
        self.assertIn("**だから同じ年度でそろえる。**", b)

    def test_4_the_parser_is_not_patched_to_make_it_pass(self):
        b = sec(self.t, "### §1-1", "## §2")
        self.assertIn("**parser を直して通すことはしない**", b)
        self.assertIn("そこで止めて", b)

    def test_5_only_the_file_changes(self):
        b = sec(self.t, "## §2 材料", "### §2-1")
        self.assertIn("**差し替えるのは「どの年度の file を読むか」の 1 か所だけである。**",
                      b)
        self.assertIn("**規則・閾値・語彙・表層形の表・採点器は 1 文字も変えない。**", b)
        c = sec(self.t, "### §2-1", "## §3")
        self.assertIn("**規則を緩めて 8 件にしない。**", c)


class ScoringTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_6_three_axes_and_four_independent_buckets(self):
        b = sec(self.t, "## §3 採点基準", "### §3-1")
        self.assertIn("**軸 1 誤りの存在**", b)
        self.assertIn("**軸 2 誤りの種類**", b)
        self.assertIn("**軸 3 本来の参照先**", b)
        self.assertIn("**集計は独立に 4 つ**", b)
        self.assertIn("**罠は別記。**", b)

    def test_7_the_main_comparison_is_c_prime_vs_d_prime(self):
        b = sec(self.t, "### §3-1", "### §3-2")
        self.assertIn("**主比較は C′ 対 D′。**", b)
        self.assertIn("**検出数だけで結論しない。軸 3(本来の参照先)の正確性を"
                      "必ず並べる**", b)
        ids = re.findall(r"(?m)^\| \*\*(A|B|C′|D|D′)\*\*", b)
        self.assertEqual(ids, ["A", "B", "C′", "D", "D′"])

    def test_8_tuning_and_transferable_ability_are_separated(self):
        b = sec(self.t, "### §3-2", "## §4")
        ids = re.findall(r"(?m)^\| \*\*K-(\d)\*\*", b)
        self.assertEqual(ids, ["1", "2", "3", "4", "5"], "K-1〜K-5")
        self.assertIn("**K-1〜K-5 のどれかが別資料で崩れたら、それは"
                      "「今回の材料への調整だった」ことの\n証拠である。"
                      "隠さずそう書く。**", b)

    def test_9_ten_predictions_sealed_before_generating(self):
        b = sec(self.t, "## §4 予測", "## §5")
        ids = re.findall(r"(?m)^\| \*\*J-(\d+)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 11)], "J-1〜J-10")
        self.assertIn("**まだ 1 行も見ていない。**", b)
        self.assertIn("**J-7 は算術で決まる。当たっても手柄にしない。**", b)
        self.assertIn("**この封の肝は J-8・J-9 である**", b)


class CostAndFailureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_10_the_estimate_exceeds_the_guideline_and_stops(self):
        b = sec(self.t, "## §5 費用", "## §6")
        self.assertIn("**3.11 USD**", b)
        self.assertIn("**3.11 USD は人間の目安 3 USD を超える。"
                      "だから生成の前に止めて人間に再判断を求める。**", b)
        ids = re.findall(r"(?m)^\| \*\*費-(\d)\*\*", b)
        self.assertEqual(ids, ["1", "2"], "費-1 と費-2")
        self.assertIn("**2.76 USD**", b)
        self.assertIn("**どちらも「見込み」であって保証値ではない。**", b)

    def test_11_no_rescue(self):
        b = sec(self.t, "## §6 失敗条件", "## §7")
        self.assertIn("**結果が悪いのを見てから、基準・閾値・予測・採点器を変えた**", b)
        self.assertIn("**8 件そろわないのを見てから、誤りの規則を緩めた**", b)
        self.assertIn("**人間の再判断を得ずに生成した**", b)
        self.assertIn("**別資料の結果を同じ材料の結果と同じ表に混ぜた**", b)

    def test_12_seven_limits(self):
        b = sec(self.t, "## §7 示せないこと", "## §8")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 8)], "限界は 7 本")
        self.assertIn("**別の自治体・別の様式での再現性は測っていない。**", b)
        self.assertIn("**既存製品(Google・NVIDIA・商用の照合製品)は測れない。**", b)
        self.assertIn("**買い手が安価に代替できる範囲を絞り込む**", b)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_REPRO_SEAL_2026-10-17.md"
    AFTER = ("measure/sheet_repro_fetch_2026-10-17.py",
             "measure/sheet_repro_material_2026-10-17.py",
             "measure/sheet_repro_score_2026-10-17.py",
             "fixtures/sheet/repro_opened_2026-10-17.json",
             "fixtures/sheet/repro_material_2026-10-17.json",
             "fixtures/sheet/repro_score_2026-10-17.json",
             "docs/DOMAIN1_REPRO_RESULT_2026-10-17.md")

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

    def test_13_seal_precedes_the_fetch_and_everything_after(self):
        self.assertTrue(self._tracked(self.SEAL_REL), "pathspec の誤り")
        seal = self._added(self.SEAL_REL)
        self.assertIsNotNone(seal, "封がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(seal, other), rel)


if __name__ == "__main__":
    unittest.main()
