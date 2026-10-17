# -*- coding: utf-8 -*-
"""(ア) の封(docs/XBRL_A_CORE_VS_GREP_SEAL_2026-10-17.md)を固定する(封 §8)。"""
import hashlib
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_A_CORE_VS_GREP_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
FROZEN = {"measure/inject.py": "92d34774c4cc76bb",
          "measure/prepare_material.py": "b1a0010df9bc725d",
          "measure/lib/sites.py": None,       # 下で実測して固定しない(封に無い)
          "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
          "adapters/xbrl/vocabulary.py": "bcf559308bda0cc6",
          "measure/SEED.json": "f74146592f68b88d"}


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

    def test_1_material_is_the_already_used_eight(self):
        b = sec(self.t, "## §1 材料", "### §1-1")
        self.assertIn("**2026-10-14 に 1 度開封した最終評価 8 件**", b)
        self.assertIn("**未使用の 8 件は本番(席つき)のために残す。**", b)
        self.assertIn("**`adapters` を import しない道具**", b)
        self.assertEqual(len(re.findall(r"`S100[A-Z0-9]{4}`", b)), 8)
        self.assertIn("**だから「未使用データでも通用する」とは書かない**", self.t)

    def test_2_one_text_for_every_arm(self):
        b = sec(self.t, "### §1-1", "## §2")
        self.assertIn("全部に同じまま渡す", b)
        self.assertIn("normalize-both-sides-of-a-comparison", b)

    def test_3_four_type_rows_and_t2_excluded(self):
        """封 H-2。**T2 を入れない理由が字で在る。**"""
        b = sec(self.t, "## §2 注入", "## §3")
        rows = [l for l in b.splitlines()
                if l.startswith("| ") and not l.startswith("|---")
                and "| 軸3 の正解 |" not in l]
        self.assertEqual(len(rows), 4, "型の表は 4 行")
        self.assertIn("~~T2_UNIT~~", b)
        self.assertIn("**桁は同じで値は原資料に在る。**", b)
        self.assertIn("**1 件注入して 1 回 Core を回す**", b)
        self.assertIn("**規則を 1 文字も変えない**", b)

    def test_4_three_arms_and_five_metrics(self):
        """封 H-3。"""
        b = sec(self.t, "## §3 腕", "### §3-1")
        ids = re.findall(r"(?m)^\| \*\*(Core|D′|D″)\*\* \|", b)
        self.assertEqual(ids, ["Core", "D′", "D″"], "腕は 3 つ")
        self.assertIn("**判定は P16**", b)
        self.assertIn("**D′・D″ に element・context の意味的選別は足さない。"
                      "Core の丸め規約も渡さない。**", b)
        m = sec(self.t, "## §4 採点", "## §5")
        met = re.findall(r"(?m)^\| \*\*(特定率|誤認定率|保留率|T1 の通し|T3 の名指し)\*\*", m)
        self.assertEqual(len(met), 5, "指標は 5 つ")
        self.assertIn("1 つの率にまとめない", m)
        self.assertIn("**「対応が付かない」として別に数える。推測で埋めない。**", m)

    def test_5_normalisation_is_one_function_on_all_sides(self):
        """封 H-6 の字。"""
        b = sec(self.t, "### §3-1", "## §4")
        self.assertIn("**`norm_pointer()` を 1 つ書き、Core・D′・D″・正解の 4 つ全部に"
                      "掛ける。**", b)
        self.assertIn("**往復を門で確かめる**", b)

    def test_6_eight_predictions_with_fail_modes(self):
        """封 H-4。"""
        b = sec(self.t, "## §5 予測", "## §6")
        rows = re.findall(r"(?m)^\| \*\*Y-(\d)\*\* \| (.+?) \| (.+?) \|$", b)
        self.assertEqual([r[0] for r in rows], [str(i) for i in range(1, 9)])
        for num, pred, how in rows:
            self.assertTrue(len(how.strip()) >= 5, "Y-%s の外れ方が薄い" % num)
        self.assertIn("**Y-1 と Y-4 が両方外れたら、「Core は参照先で勝る」は"
                      "この標本では支持されない。**", b)

    def test_7_six_stops_and_six_limits(self):
        """封 H-5。"""
        s = sec(self.t, "## §6 止める条件", "## §7")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", s), [str(i) for i in range(1, 7)])
        self.assertIn("**この便の結果で 8 書類の本番の封を変えない。**", s)
        li = sec(self.t, "## §7 示せないこと", "## §8")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", li), [str(i) for i in range(1, 7)])
        self.assertIn("LLM + Core という製品全体の優位性を直接証明するものではない。**", li)
        self.assertIn("**Core 単体の差が小さくても、LLM との相互補完は否定されない**", li)

    def test_8_gates_are_seven(self):
        g = sec(self.t, "## §8 門")
        self.assertEqual(re.findall(r"(?m)^\| \*\*(H-\d)\*\*", g),
                         ["H-%d" % i for i in range(1, 8)])


class FrozenTest(unittest.TestCase):
    def test_9_tools_have_not_moved(self):
        """封 H-7。**この便で道具を直したら赤くなる。**"""
        for rel, want in FROZEN.items():
            if want is None:
                self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)
                continue
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            self.assertEqual(got, want, "**%s が動いている**" % rel)


class CommitOrderTest(unittest.TestCase):
    AFTER = ("measure/xbrl_a_core_vs_grep_2026-10-17.py",
             "fixtures/xbrl/cd8/a_core_vs_grep_2026-10-17.json",
             "docs/XBRL_A_CORE_VS_GREP_RESULT_2026-10-17.md")

    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_10_seal_precedes_the_implementation(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        self.assertTrue(tracked, "pathspec の誤り")
        seal = self._added(SEAL_REL)
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
