# -*- coding: utf-8 -*-
"""方式 C の直しの封(docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md)を固定する。

守るのは: 規則の 8 行・不変条件・合否の 4 線・予測 10 欄・順序(封が実装より先)。
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("measure/sheet_errdet_cprime_2026-10-19.py",
         "fixtures/sheet/errdet_cprime_2026-10-19.json",
         "docs/DOMAIN1_ERRDET_CPRIME_RESULT_2026-10-19.md")


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

    def test_1_purpose_is_the_composition_rule_not_core(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn("**私の設計**である", b)
        self.assertIn("**本封の結果で製品の優位性を書かない。**", b)
        self.assertIn("**同じ材料・同じ答えの再利用である。**", b)

    def test_2_the_rule_has_exactly_eight_rows(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        rows = re.findall(r"(?m)^\| (\d) \| ", b)
        self.assertEqual(rows, [str(i) for i in range(1, 9)])
        self.assertIn("**C′ ≧ 席** が常に成り立つ", b)
        self.assertIn("**席が検出なら C′ は検出**(行 1〜4)", b)

    def test_3_seat_detection_is_never_overwritten(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        for n in (1, 2, 3, 4):
            self.assertRegex(b, r"(?m)^\| %d \| \*{0,2}検出[^|]*\| [^|]*\| \*{0,2}検出\*{0,2} \|" % n)

    def test_4_verifier_moves_only_the_confirmed_rows(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        self.assertRegex(b, r"(?m)^\| 7 \| 確認済み[^|]*\| 原資料と一致しない \| \*\*検出\*\* \|")
        self.assertRegex(b, r"(?m)^\| 8 \| 確認済み[^|]*\| 確認できない[^|]*\| 保留 \|")
        self.assertRegex(b, r"(?m)^\| 6 \| 確認済み[^|]*\| 確認済み \| 確認済み \|")

    def test_5_c_double_prime_adds_core_row_and_only_mismatch_moves_state(self):
        b = sec(self.t, "### §1-3", "### §1-4")
        self.assertIn("**B が `VALUE_MISMATCH`** なら **検出**", b)
        self.assertIn("**B の保留(`UNVERIFIABLE` / `POINTER_NOT_FOUND`)は状態を動かさない**", b)
        self.assertIn("**「あるべき行」**", b)
        self.assertIn("**「出どころの行」**", b)

    def test_6_forbidden_moves(self):
        b = sec(self.t, "### §1-4", "## §2")
        for k in ("席の答えを書き換えない", "**書き直さない**",
                  "**C′ の状態表に行を足さない。**",
                  "`検出` を `確認済み` に上げる経路を作らない"):
            self.assertIn(k, b, k)

    def test_7_denominators(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn("**8 件 × 2 席**", b)
        self.assertIn("**26 件 × 2 席**", b)
        self.assertIn("**別記**", b)

    def test_8_four_lines_and_g1_is_not_used(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*K-(\d) ", b)
        self.assertEqual(ids, ["1", "2", "3", "4"])
        self.assertIn("G-1「見落としが減る」は、**A seat1 の見落としが 0 件なので原理的に満たせない**", b)
        self.assertIn("**「C′ が A を上回った」は書かない**", b)

    def test_9_ten_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §4", "## §5")
        ids = re.findall(r"(?m)^\| \*\*P-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 11)])
        for line in re.findall(r"(?m)^\| \*\*P-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], "外れ方が空: " + line)
        self.assertIn("**本当に測っているのは P-4・P-5・P-7・P-8・P-9・P-10 である。**", b)

    def test_10_limits_name_the_material_reuse(self):
        b = sec(self.t, "## §6", "## §7")
        self.assertIn("**同じ材料・同じ答えである。**", b)
        self.assertIn("**別資料で同じ数が出るかは測っていない**", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True,
                             text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_11_the_seal_precedes_implementation_and_measurement(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない(この便で commit する)")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(
                subprocess.run(["git", "merge-base", "--is-ancestor", seal,
                                other], cwd=ROOT,
                               capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
