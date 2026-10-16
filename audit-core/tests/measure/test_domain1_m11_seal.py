# -*- coding: utf-8 -*-
"""段 11 本実験の封(docs/DOMAIN1_M11_SEAL_2026-10-16.md)を固定する。

**封は材料より先・生成より先・採点より先に commit する。**
守るのは 12 つ(封 §12)。

  1. §1 の **13 本の sha が実測と一致**し、`MIN_INDEPENDENT = 3` が字で在る
  2. §2-2 の「**歳入側の engine で材料を作らない**」(歯が消える理由つき)
  3. §2-3 の **3 つの停止条件**
  4. §3 の「**新 engine では A-1・A-3 が構造的に 0**」が**生成より先に**在る
  5. §4 の **X-2 の 3 通り**と合格の条件
  6. §4-1 の **歯-1・歯-2・歯-3** と「**人工材料は実データの証明と分ける**」
  7. §5 の **β** と「**5 欄が食い違えば正しい接続に数えない**」
  8. §6 の線が **7 本**・**N-接続-増 を合否に入れない**・§6-1 の 5 つの数え方
  9. §7 の費用と回数(**生成 3 本**・**4 USD**・**再生成しない**・**採点器は先**)
 10. §8 の「**誤接続を正しい接続の増加で相殺しない**」
 11. §9 の限界が **10 本**・§10 の予測が **16 本**
 12. **封が材料・機会・報告文・採点器より先に commit されたこと**(commit の順)
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
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M11_SEAL_2026-10-16.md")

# 封 §1 の表。**実測の sha と一致すること**
FROZEN = {
    "sheet_m5_engine_2026-10-15.py": "6eb5723ef518e1b4",
    "sheet_m7_engine_2026-10-15.py": "4574c3ea013d05a1",
    "sheet_parent_backing_2026-10-16.py": "8e387958c69398e8",
    "sheet_sainyuu_engine_2026-10-16.py": "3a70b599672832d3",
    "sheet_sainyuu_p1_2026-10-16.py": "91b15e0f7eaa5442",
    "sheet_sainyuu_p2_2026-10-16.py": "671c7dd81cea0ffe",
    "sheet_m8_score_2026-10-16.py": "fbb81c52f0e8cbd3",
    "sheet_label_spec_2026-10-15.py": "5c5755572dbca1b6",
    "sheet_label_spec_m9_2026-10-16.py": "b0d0cb530f4824fe",
    "sheet_m9_material_2026-10-16.py": "a1c82749583947f0",
    "sheet_m9_opportunity_2026-10-16.py": "eace3e1bbd2c480b",
    "sheet_m9_run_2026-10-16.py": "acbae516bc325853",
    "sheet_m4_material_2026-10-15.py": "54d0833f86ea722b",
}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sha16(p):
    with io.open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


class SealFreezesTheFrozenTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_thirteen_shas_match_the_measured_files(self):
        self.assertEqual(len(FROZEN), 13, "凍結するのは 13 本")
        for name, want in sorted(FROZEN.items()):
            p = os.path.join(MEASURE, name)
            self.assertTrue(os.path.exists(p), name)
            self.assertEqual(sha16(p), want, "**%s が動いている**" % name)
            self.assertIn("`%s`" % want, self.t, "封に sha が無い: %s" % name)
            self.assertIn("`measure/%s`" % name, self.t, name)

    def test_2_min_independent_is_three_in_letters(self):
        self.assertIn("**`MIN_INDEPENDENT = 3`**", self.t)
        self.assertIn("**2 にする選択肢は取らない。**", self.t)
        src = text(os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py"))
        self.assertIn("MIN_INDEPENDENT = 3", src, "engine の字が 3 でない")

    def test_3_scoring_器_is_reused_not_rewritten(self):
        self.assertIn("段 8 の file をそのまま呼ぶ", self.t)
        self.assertIn("**新しく書かない。**", self.t)
        self.assertIn("段 9 の問いと 1 文字も違わないこと", self.t)
        for n in ("G-1′ の線 50%", "G-4 の線 80%", "G-5 の線 20 件"):
            self.assertIn(n, self.t, n)


class MaterialRuleTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_4_material_is_built_with_the_old_alias_table(self):
        block = self.t.split("### §2-2")[1].split("### §2-3")[0]
        self.assertIn("歳入側の engine で材料を作ると", block)
        self.assertIn("抜粋に別名の形が 1 行も載らなくなる", block)
        self.assertIn("試験の歯がそこで消える", block)
        self.assertIn("旧 engine(`sheet_m5_engine`)の別名表", block)

    def test_5_three_stop_conditions_before_generation(self):
        block = self.t.split("### §2-3")[1].split("## §3")[0]
        self.assertIn("**表 3b(未確認会計の目)が 0 行なら生成しない。**", block)
        self.assertIn("表 3b に載る会計が 0 件なら生成しない", block)
        self.assertIn("20 未満なら生成しない", block)
        self.assertIn("**規則を緩めて機会を作り直さない。**", block)

    def test_6_only_the_excluded_range_changes(self):
        block = self.t.split("### §2-1")[1].split("### §2-2")[0]
        self.assertIn("`build()` を**そのまま呼ぶ。**", block)
        self.assertIn("選び方の規則は 1 行も書き直さない", block)
        self.assertIn("m9_binds_2026-10-16.json", block)
        self.assertIn("m9_material_2026-10-16.json", block)


class StructuralZeroIsSealedBeforeGenerationTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_7_a1_and_a3_are_structurally_zero_for_the_new_engine(self):
        block = self.t.split("## §3")[1].split("## §4")[0]
        self.assertIn("**未確認の別名が 0 件になる**", block)
        self.assertIn("**A-1(③の発火)と A-3(未確認の行に結んだ数)は構造的に 0 になる。**",
                      block)
        self.assertIn("旧 engine でしか観測できない", block)
        self.assertIn("**生成より先にこの封に書いた構造の事実**", block)

    def test_8_both_engines_are_named_and_frozen(self):
        block = self.t.split("## §3")[1].split("## §4")[0]
        self.assertIn("`measure/sheet_m7_engine_2026-10-15.py`", block)
        self.assertIn("`measure/sheet_sainyuu_engine_2026-10-16.py`", block)
        self.assertIn("どちらも凍結する", block)


class X2IsEvaluatedIndependentlyTest(unittest.TestCase):
    """人間の必須条件: **X-2 を独立して評価する。非対称な正規化で演出しない。**"""

    def setUp(self):
        self.t = text(SEAL)

    def test_9_three_ways_of_counting_x2(self):
        block = self.t.split("## §4")[1].split("### §4-1")[0]
        for k in ("**X-2対称**", "**X-2非対称**", "**X-2三欄**"):
            self.assertIn(k, block, k)
        self.assertIn("**合否に使う**", block)
        self.assertIn("**開示する。性能として書かない**", block)
        self.assertIn("**別名表に依らない**", block)
        self.assertIn("**合格の条件は「X-2対称 = 0 かつ X-2三欄 = 0」。**", block)
        self.assertIn("「未測定」と書き、合格の根拠に含めない", block)

    def test_10_the_asymmetric_trap_is_named(self):
        block = self.t.split("## §4")[1].split("### §4-1")[0]
        self.assertIn("段 9 の数え方をそのまま当てると", block)
        self.assertIn("全部 X-2 に数えられる", block)
        self.assertIn("**人間が禁じた非対称そのものである。**", block)

    def test_11_the_counter_gets_teeth_from_artificial_material(self):
        block = self.t.split("### §4-1")[1].split("## §5")[0]
        self.assertIn("**歯-1**", block)
        self.assertIn("**歯-2**", block)
        self.assertIn("**歯-3**", block)
        self.assertIn("計数器が動いていないだけ", block)
        self.assertIn("**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**",
                      block)


class CircularityIsBrokenTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_12_beta_is_defined_and_five_fields_decide(self):
        block = self.t.split("## §5")[1].split("## §6")[0]
        self.assertIn("試している写像そのもので席の答えを直す", block)
        self.assertIn("**β = 「別名表に依って一致した主張」の数**", block)
        self.assertIn("会計の欄を除いた 5 欄", block)
        self.assertIn("**別名表を切った状態で**", block)
        self.assertIn("**β 件のうち 5 欄が食い違うものが 1 件でも在れば、"
                      "その件は正しい接続に数えない。**", block)
        self.assertIn("**実データでの証拠は無い。**", block)


class ScoringLinesTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.block = self.t.split("## §6")[1].split("### §6-1")[0]

    def test_13_seven_lines_all_required(self):
        self.assertIn("**7 本すべてを満たして初めて合格**", self.block)
        rows = [l for l in self.block.split("\n")
                if l.startswith("| **") and "|" in l[3:]]
        self.assertEqual(len(rows), 7, "線は 7 本: %s" % rows)
        for k in ("A-1(旧)", "E2(新・対称)", "X-2対称(新)", "X-2三欄(新)",
                  "β の 5 欄", "G-5", "G-1′(新)"):
            self.assertTrue(any(k in r for r in rows), k)

    def test_14_increment_is_not_a_line(self):
        self.assertIn("**N-接続-増**", self.block)
        self.assertIn("**増えても合格にしない。減っても失敗にしない**", self.block)
        self.assertIn("**席の一致率。成果として書かない。**", self.block)
        self.assertIn("6 段続けて未測定", self.block)

    def test_15_five_separate_counts(self):
        block = self.t.split("### §6-1")[1].split("### §6-2")[0]
        for k in ("N-接続-正", "N-接続-誤", "N-保留", "N-別名-通", "N-別名-止"):
            self.assertIn(k, block, k)


class CostAndOnceTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.block = self.t.split("## §7")[1].split("## §8")[0]

    def test_16_one_generation_three_calls_four_usd(self):
        self.assertIn("**報告文の生成は 1 回だけ。**", self.block)
        self.assertIn("claude-sonnet-4-5", self.block)
        self.assertIn("claude-haiku-4-5", self.block)
        self.assertIn("**生成は合計 3 本**", self.block)
        self.assertIn("**上限 4 USD。超えたら打ち切る。**", self.block)
        self.assertIn("再生成しない", self.block)
        self.assertIn("**追加生成・再採点・条件を変えた再実験をしない。**", self.block)

    def test_17_scorer_before_labels(self):
        self.assertIn("**採点器はラベルを見る前に commit する。**", self.block)

    def test_18_human_permission_is_quoted(self):
        head = self.t.split("## §1")[0]
        for k in ("上限 4 USD", "封を維持する", "X-2 を独立して評価する",
                  "結果を三層に分けて記録する", "失敗しても再調整しない",
                  "正しい接続の増加で相殺せず"):
            self.assertIn(k, head, k)


class FailureAndLimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_19_failure_conditions(self):
        block = self.t.split("## §8")[1].split("## §9")[0]
        self.assertIn("**安全性の問題として記録する。正しい接続の増加で相殺しない**",
                      block)
        self.assertIn("**未測定と明記し、合格の根拠に含めない**", block)
        self.assertIn("**結果を無効にする**", block)
        self.assertIn("**不合格でも再調整しない。**", block)
        self.assertIn("**別の封を切る。**", block)

    def test_20_ten_limits_named(self):
        block = self.t.split("## §9")[1].split("## §10")[0]
        nums = re.findall(r"(?m)^(\d+)\. ", block)
        self.assertEqual(nums, [str(i) for i in range(1, 11)], "限界は 10 本")
        self.assertIn("**6 段続けて**", block)
        self.assertIn("**6a・6b は独立性の規則であり、安全の規則ではない**", block)
        self.assertIn("閾値 3 と値の完全一致である", block)
        self.assertIn("**別名規則の安全性が改善した**", block)
        self.assertIn("**顧客価値が証明されたとも書かない。**", block)

    def test_21_sixteen_predictions_in_counts(self):
        block = self.t.split("## §10")[1].split("## §11")[0]
        ids = re.findall(r"(?m)^\| U-(\d+) \|", block)
        self.assertEqual(ids, [str(i) for i in range(1, 17)], "予測は 16 本")
        self.assertIn("**材料をまだ作っていない。件数で・外れうる粒度で**", block)
        self.assertIn("**予測を測ったあとに書き換えない。", block)
        self.assertIn("今回は両方向に外れうる幅で書いた", block)


class CommitOrderTest(unittest.TestCase):
    """**封が材料・機会・報告文・採点器より先に commit されたこと。**

    道は `cwd=ROOT`(= audit-core/)からの相対で書く ― repo ルートからの道を渡すと
    pathspec が当たらず、空振りを「未 commit」と読み違える(2026-10-16 に踏んだ)。
    """

    SEAL_REL = "docs/DOMAIN1_M11_SEAL_2026-10-16.md"
    AFTER = ("measure/sheet_m11_material_2026-10-16.py",
             "fixtures/sheet/m11_material_2026-10-16.json",
             "fixtures/sheet/m11_opportunity_2026-10-16.json",
             "fixtures/sheet/m11_x2_teeth_2026-10-16.json",
             "fixtures/sheet/m11_report_2026-10-16.json",
             "measure/sheet_m11_score_2026-10-16.py",
             "fixtures/sheet/m11_answers_seat1_2026-10-16.json")

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

    def test_22_seal_is_committed(self):
        self.assertTrue(self._tracked(self.SEAL_REL),
                        "道が git に当たっていない(pathspec の誤り)")
        self.assertIsNotNone(self._added(self.SEAL_REL), "封がまだ commit されていない")

    def test_23_seal_precedes_material_generation_and_scorer(self):
        seal = self._added(self.SEAL_REL)
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue                      # まだ無いものは測らない
            self.assertNotEqual(seal, other,
                                "封と %s が同じ commit に入っている(順を測れない)" % rel)
            self.assertTrue(self._ancestor(seal, other),
                            "封が %s より後に commit されている" % rel)
            self.assertFalse(self._ancestor(other, seal))   # 歯: 逆向きは偽

    def test_24_a_wrong_pathspec_is_detected(self):
        wrong = "audit-core/" + self.SEAL_REL
        self.assertIsNone(self._added(wrong))
        self.assertFalse(self._tracked(wrong))


if __name__ == "__main__":
    unittest.main()
