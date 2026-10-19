# -*- coding: utf-8 -*-
u"""製品の経路への封(docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md)を固定する。"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("adapters/xbrl/holds.py", "adapters/xbrl/verify_external.py",
         "tests/adapters/xbrl/test_holds.py", "tests/adapters/xbrl/test_verify_external.py",
         "docs/XBRL_HOLDS_PRODUCT_PATH_RESULT_2026-10-19.md")


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

    def test_1_the_decision_and_its_source_are_named(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"**本当に制約はない**", head)
        self.assertIn(u"司令塔が **engine 変更の構造の決定**", head)
        self.assertIn(u"独立監査(`step-auditor`)の GO を経てから commit する", head)
        self.assertIn(u"`main` へのマージは人間", head)

    def test_2_no_new_rule_and_only_axes_added(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"**規則は 1 つも新しく作らない。**", b)
        self.assertIn(u"足す engine の情報は **軸(dimension)だけ**", b)
        self.assertIn(u"**精度は測らない**", b)

    def test_3_the_file_list_is_closed(self):
        b = sec(self.t, "## §1", "### §1-1")
        rows = re.findall(r"(?m)^\| (\d) \| `", b)
        self.assertEqual(rows, [str(i) for i in range(1, 8)])
        self.assertIn(u"**既存の鍵(`instant`/`start`/`end`/`members`)は 1 文字も変えない。他の関数は触らない**", b)
        self.assertIn(u"**`audit_core` を import しない**", b)
        self.assertIn(u"**触らない**: `core/py/`(0 行)", b)
        for name in ("recipes.py", "verify_document.py", "resolve.py", "comparators.py",
                     "registry_setup.py", "vocabulary.py"):
            self.assertIn("`%s`" % name, b, name)

    def test_4_response_fields_are_pinned_and_unchecked_is_not_empty(self):
        b = sec(self.t, "### §1-1", "## §2")
        self.assertIn(u'**`("存在", "値", "同額の次元兄弟", "同額の期間兄弟", "単位の種類")`**', b)
        self.assertIn(u'**`("重複", "単位の倍率", "期間(同額の兄弟が無いとき)", "次元(同額の兄弟が無いとき)", "要素の取り違え")`**', b)
        self.assertIn(u"**`unchecked` を空にしない。**", b)

    def test_5_denominators_are_literal(self):
        b = sec(self.t, "## §2", "## §3")
        for k in (u"**786 本**", u"**89 件**", u"**192 行**", u"**22 本**", u"`2c2af15a…`"):
            self.assertIn(k, b, k)

    def test_6_twelve_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*F-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 13)])
        for line in re.findall(r"(?m)^\| \*\*F-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**本当に測っているのは F-3・F-4・F-5・F-7・F-9 である。**", b)

    def test_7_limits(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn(u"**精度は上がらない。**", b)
        self.assertIn(u"「どの軸の違いなら不一致か」は決めない", b)
        self.assertIn(u"**この決定はそこには書かない**", b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_8_the_seal_precedes_the_engine_change(self):
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
