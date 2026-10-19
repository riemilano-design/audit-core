# -*- coding: utf-8 -*-
u"""期間・単位の保留規則の封(docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("measure/xbrl_period_unit_hold_rule_2026-10-19.py",
         "measure/xbrl_period_unit_hold_2026-10-19.py",
         "fixtures/xbrl/cd8/period_unit_hold_2026-10-19.json",
         "docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md")


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

    def test_1_purpose_is_not_accuracy_and_engine_is_untouched(self):
        head = self.t[:self.t.index("\n## §1")]
        self.assertIn(u"**engine(`core/`・`adapters/`)は変更しない。**", head)
        self.assertIn(u"**目的は精度の向上ではない。**", head)
        self.assertIn(u"**0 USD・席は呼ばない。**", head)

    def test_2_rule_p_has_five_conditions_and_reuses_dim_of(self):
        b = sec(self.t, "### §1-1", "### §1-2")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b), ["1", "2", "3", "4", "5"])
        self.assertIn(u"`dim_of(g.context) == dim_of(f.context)` かつ `g.context != f.context`", b)
        self.assertIn(u"**そのまま import**", b)
        self.assertIn(u"`ambiguous_period:<件数>`", b)

    def test_3_rule_u_compares_unit_classes_and_skips_none(self):
        b = sec(self.t, "### §1-2", "### §1-3")
        self.assertIn(u"`百万円 / 千円 / 億円 / 兆円 / 円` → `JPY`", b)
        self.assertIn(u"`% / ％` → `pure`", b)
        self.assertIn(u"**`None`(判定しない)**", b)
        self.assertIn(u"`unit_class_mismatch:<claim_class>/<fact_class>`", b)
        self.assertIn(u"**U は兄弟を数えない。**", b)

    def test_4_composition_order_and_untouched_states(self):
        b = sec(self.t, "### §1-3", "## §2")
        self.assertIn(u"(d) → P → U の順", b)
        self.assertIn(u"**`GROUNDED` 以外の状態は 1 文字も変えない。参照先を増やさない・選び直さない**", b)

    def test_5_transition_table(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"| `GROUNDED` | 0 | 0 | 0 | `GROUNDED`(**変えない**) |", b)
        self.assertIn(u"**`UNPROVABLE`**(理由を連結)", b)
        self.assertIn(u"| `VALUE_MISMATCH` | 問わない | | | `VALUE_MISMATCH`(**変えない**) |", b)

    def test_6_denominators_are_literal(self):
        b = sec(self.t, "## §4", "## §5")
        for k in (u"| **24** |", u"| **85** |", u"| **42** |", u"| **50** |"):
            self.assertIn(k, b, k)
        self.assertIn(u"**1 回に 1 件だけ**", b)
        self.assertIn(u"単位: 参照先は**注入した fact の key**", b)

    def test_7_fourteen_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §6", "## §7")
        ids = re.findall(r"(?m)^\| \*\*E-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 15)])
        for line in re.findall(r"(?m)^\| \*\*E-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**本当に測っているのは E-6・E-7(穴が閉じるか)と E-9〜E-13(代価)である。**", b)

    def test_8_limits(self):
        b = sec(self.t, "## §7", "## §8")
        self.assertIn(u"**精度は上がらない。**", b)
        self.assertIn(u"**規則 U は単位の「種類」しか見ない。**", b)
        self.assertIn(u"**同じ 8 書類である。**", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_9_the_seal_precedes_implementation_and_measurement(self):
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
            self.assertTrue(subprocess.run(
                ["git", "merge-base", "--is-ancestor", seal, other],
                cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
