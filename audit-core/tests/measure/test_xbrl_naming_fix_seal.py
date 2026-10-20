# -*- coding: utf-8 -*-
u"""名指しの直し(P21)の封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md を固定する。engine を変える封なので、過去の門の留めの列挙と予測の固定を門にする。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("adapters/xbrl/recipes.py",            # 変更(新規ではない。順序は sha の遷移で見る)
         "tests/adapters/xbrl/test_recipes_p21.py",
         "measure/xbrl_naming_fix_2026-10-20.py",
         "fixtures/xbrl/naming_fix/p21_2026-10-20.json",
         "docs/XBRL_NAMING_FIX_RESULT_2026-10-20.md",
         "tests/measure/test_xbrl_naming_fix_result.py")
PINNED_GATES = ("tests/measure/test_xbrl_axis3_decision.py", "tests/measure/test_xbrl_cd_seal.py",
                "tests/measure/test_xbrl_branch_a.py", "tests/measure/test_xbrl_p20_result.py",
                "tests/measure/test_xbrl_pnf_diag.py", "tests/measure/test_xbrl_role_swap_result.py",
                "tests/measure/test_xbrl_a_core_vs_grep_seal.py", "fixtures/frozen_bundle_sha.py")


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

    def test_1_human_instruction_and_the_one_branch(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"「さっきコアの精度と言ったけど、アダプターの問題か。とにかく君が精度を改善して。何してもいいから」", head)
        self.assertIn(u"**数を見てから封・予測を直さない。**", head)
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"`_direct_value_claim` の「値が一致する fact が無いときの最後の枝」(309〜328 行)", b)
        self.assertEqual(re.findall(r"(?m)^\| \*\*(F1′|F2′|F3b)", b), [u"F1′", u"F2′", u"F3b"])
        self.assertIn(u"`P21 = dataclasses.replace(P20, name=\"P21\", <旗>=True)`", b)
        self.assertIn(u"**やらないこと(別の封)**", b)
        self.assertIn(u"段 1 では `DEFAULT_PROFILE = \"P20\"` のまま", b)

    def test_2_past_engine_pins_are_listed(self):
        b = sec(self.t, "## §1", "## §2")
        for g in PINNED_GATES:
            self.assertIn("`%s`" % g, b, g)
            self.assertTrue(os.path.exists(os.path.join(ROOT, g)), g)
        self.assertIn(u"**これらの字は変えず、分岐を前に足す**", b)
        self.assertIn(u"**S100Z4N9 の H-124・H-067・H-120・H-122(F1′)と S100Z39P の H-075(F3b)の 5 行だけ**", b)

    def test_3_materials_and_controls(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"`--profile P21`", b)
        self.assertIn(u"**id の一覧を記録に書く**", b)
        self.assertIn(u"**GROUNDED の行で state か参照先が動いた数**", b)
        for c in (u"**M-C1**", u"**M-C2**", u"**M-C3**"):
            self.assertIn(c, b, c)

    def test_4_twelve_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*N-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 13)])
        for line in re.findall(r"(?m)^\| \*\*N-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**26 / 50**(P20 21)、誤認定 **3**(P20 19)", b)
        self.assertIn(u"**GROUNDED の行で state か参照先が動いた数 0**", b)
        self.assertIn(u"**本当に測っているのは N-1・N-4・N-6 である。**N-4 が外れたら段 2 はやらない", b)

    def test_5_limits_and_closed_file_list(self):
        self.assertIn(u"予測の数は診断席の差し替え実測から写した", sec(self.t, "## §4", "## §5"))
        b = sec(self.t, "## §5")
        for rel in AFTER:
            self.assertIn("`%s`" % rel, b, rel)
        self.assertIn(u"**これ以外に触らない。**", b)
        self.assertIn(u"**数を見てから封・予測を直さない。外れは外れとして残す。**", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_6_the_seal_precedes_new_files_and_the_engine_change(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER[1:]:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)
        # recipes.py は変更。封より後の commit でしか変わっていないこと(封の commit 以前の最終変更が 50fd48b)
        out = subprocess.run(["git", "log", "--format=%H", "--", "adapters/xbrl/recipes.py"],
                             cwd=ROOT, capture_output=True, text=True)
        changes = [s for s in out.stdout.split() if s]
        for c in changes:
            if c.startswith("50fd48b"):
                break
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, c],
                                           cwd=ROOT, capture_output=True).returncode == 0,
                            u"封より前に recipes.py が変わっている: " + c)


if __name__ == "__main__":
    unittest.main()
