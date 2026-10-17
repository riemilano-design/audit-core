# -*- coding: utf-8 -*-
"""様式への耐性の封(docs/DOMAIN1_FORMDEP_SEAL_2026-10-17.md)を固定する。

守るのは 7 つ(封 §7)。**封の字を後から緩められないようにする。**
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
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_FORMDEP_SEAL_2026-10-17.md")

# 封 §1-2 の 7 file。**測定の前後で動いていないこと**(封 G-7)
FROZEN = {
    "sheet_read_m1_2026-10-15.py": "f9941555a55a1bb8",
    "sheet_m2_structure_2026-10-15.py": "5945c9461f0dedb0",
    "sheet_sainyuu_p1_2026-10-16.py": "91b15e0f7eaa5442",
    "sheet_sainyuu_p2_2026-10-16.py": "671c7dd81cea0ffe",
    "sheet_m7_engine_2026-10-15.py": "4574c3ea013d05a1",
    "sheet_sainyuu_engine_2026-10-16.py": "3a70b599672832d3",
    "sheet_m5_engine_2026-10-15.py": "6eb5723ef518e1b4",
}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class WhatIsMeasuredTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_three_measurements_and_no_fixing(self):
        b = sec(self.t, "## §1 測るもの", "### §1-1")
        ids = re.findall(r"(?m)^\| \*\*測-(\d)\*\*", b)
        self.assertEqual(ids, ["1", "2", "3"], "測-1〜測-3")
        self.assertIn("**抽出器・parser・engine は 1 文字も変えない。**", b)
        self.assertIn("**測-3 は材料を数えるだけであり、parser を直して通すこと"
                      "ではない。**", b)
        self.assertIn("**独立した監査の GO を経るまで実装しない。**", b)

    def test_2_the_rule_has_hitting_and_non_hitting_examples(self):
        """封 G-2。**実装者が 1 通りに書ける字で書く**(記憶 seal-rule-wording)。"""
        b = sec(self.t, "### §1-1", "### §1-2")
        rows = [l for l in b.splitlines()
                if l.startswith("| ") and not l.startswith("|---")
                and "| 例 |" not in l]
        self.assertEqual(len(rows), 9, "当たる 6 行 + 当たらない 3 行")
        for k in ("比較の相手", "所属の検査", "`startswith` / `endswith` の引数",
                  "読み出しの添字", "module 直下の代入に在る字"):
            self.assertIn(k, b, k)
        for k in ("**書き込みの添字**(Store / AugAssign)", "docstring・コメント"):
            self.assertIn(k, b, k)
        self.assertIn("**黙って 0 件にしない**", b)

    def test_3_the_seven_files_exist(self):
        """封 G-3。**範囲は字で固定し、実在を確かめる。**"""
        b = sec(self.t, "### §1-2", "### §1-3")
        names = re.findall(r"`measure/([a-z0-9_\-]+\.py)`", b)
        self.assertEqual(len(names), 7, "7 file")
        self.assertEqual(sorted(names), sorted(FROZEN), "封と門の file が違う")
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(MEASURE, n)), n)
        self.assertIn("**数えなかった範囲は結果に書く。**", b)

    def test_4_seven_layers(self):
        b = sec(self.t, "### §1-3", "## §2 測-2")
        ids = re.findall(r"(?m)^\| \*\*(L\d)", b)
        self.assertEqual(ids, ["L%d" % i for i in range(1, 8)], "L1〜L7")
        self.assertIn("**層の割り当ては、その字が現れた判定の種類で決める**", b)
        self.assertIn("**割り当てが 2 つに跨る字は「跨いだ」として別に数える。**", b)

    def test_5_three_exclusive_classes_and_the_caveat(self):
        b = sec(self.t, "## §2 測-2", "## §2-1")
        self.assertIn("**排他。**", b)
        for k in ("**両年度に在る**", "**令和６にだけ在る**", "**材料に無い**"):
            self.assertIn(k, b, k)
        self.assertIn("**「字が材料に在る」ことは「判定が通る」ことではない**", b)
        self.assertIn("**手で分類しない。**", b)

    def test_6_probe_does_not_rewrite_the_parser(self):
        b = sec(self.t, "## §2-1", "## §3")
        self.assertIn("^令和６年度東京都(.+)歳入歳出決算書$", b)
        self.assertIn("^令和.+年度東京都(.+)歳入歳出決算書$", b)
        self.assertIn("**その字を書き換えない**", b)


class StopAndPredictTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_7_six_stop_conditions(self):
        b = sec(self.t, "## §3 止める条件", "## §4")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 7)], "止める条件は 6 本")
        self.assertIn("**判定に使う字が 0 件なら止める**", b)
        self.assertIn("**この便で抽出処理を直さない。**", b)
        self.assertIn("日付つきの追記だけを足す", b)
        self.assertIn("**予測が外れても基準を変えない**", b)

    def test_8_ten_predictions_each_with_a_way_to_fail(self):
        """記憶 prediction-must-be-able-to-fail: **外れ方の欄を空にしない。**"""
        b = sec(self.t, "## §4 予測", "## §5")
        rows = re.findall(r"(?m)^\| \*\*F-(\d+)\*\* \| (.+?) \| (.+?) \|$", b)
        self.assertEqual([r[0] for r in rows], [str(i) for i in range(1, 11)],
                         "F-1〜F-10")
        for num, pred, how in rows:
            self.assertTrue(pred.strip(), num)
            self.assertTrue(len(how.strip()) >= 4, "F-%s の外れ方が薄い" % num)
        self.assertIn("`blocks = 19`", b)
        self.assertIn("**実装より先に書く。外れたら外れたと書く**", b)

    def test_9_six_limits(self):
        b = sec(self.t, "## §5 示せないこと", "## §6")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 7)], "限界は 6 本")
        self.assertIn("**別自治体・別様式の資料は 1 件も測っていない。**", b)
        self.assertIn("**「直せば通る」とは言えない。**", b)

    def test_10_zero_cost_and_seven_gates(self):
        self.assertIn("**0 USD。**席を 1 回も呼ばない。", self.t)
        self.assertIn("**鍵を使わない。**", self.t)
        b = sec(self.t, "## §7 門")
        ids = re.findall(r"(?m)^\| \*\*(G-\d)\*\*", b)
        self.assertEqual(ids, ["G-%d" % i for i in range(1, 8)], "G-1〜G-7")


class ExtractorsAreFrozenTest(unittest.TestCase):
    def test_11_extraction_files_have_not_moved(self):
        """封 G-7。**測定の便で抽出処理を直したら赤くなる。**"""
        for name, want in FROZEN.items():
            with io.open(os.path.join(MEASURE, name), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            self.assertEqual(got, want, "**%s が動いている**" % name)


class CommitOrderTest(unittest.TestCase):
    SEAL_REL = "docs/DOMAIN1_FORMDEP_SEAL_2026-10-17.md"
    AFTER = ("measure/sheet_formdep_2026-10-17.py",
             "fixtures/sheet/formdep_2026-10-17.json",
             "docs/DOMAIN1_FORMDEP_RESULT_2026-10-17.md")

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

    def test_12_seal_precedes_the_implementation(self):
        """封 G-1。**「まだ無い」では書かない。commit の順で書く。**"""
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
