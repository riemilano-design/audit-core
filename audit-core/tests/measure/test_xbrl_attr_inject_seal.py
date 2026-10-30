# -*- coding: utf-8 -*-
"""属性注入の封(docs/XBRL_ATTR_INJECT_SEAL_2026-10-17.md)と
誤拒否の原因分析(docs/XBRL_FALSE_REJECT_DIAG_2026-10-17.md)を固定する。
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_ATTR_INJECT_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
DIAG = os.path.join(ROOT, "docs", "XBRL_FALSE_REJECT_DIAG_2026-10-17.md")
V1 = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "contract_v1_2026-10-17.json")
AFTER = ("measure/xbrl_attr_inject_2026-10-17.py",
         "fixtures/xbrl/cd8/attr_inject_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    return t[i:t.index("\n" + end, i)] if end else t[i:]


class DiagTest(unittest.TestCase):
    """**原因分析は既存の記録と一致していること。**"""

    def setUp(self):
        self.t = text(DIAG)
        self.r = json.load(io.open(V1, encoding="utf-8"))

    def test_1_the_row_is_the_one_in_the_record(self):
        d = self.r[u"R-2 正しい主張を不一致にした(無改変)"][u"明細"]
        self.assertEqual(len(d), 1)
        self.assertEqual((d[0][u"doc"], d[0][u"id"]), ("S100YZEV", "R017"))
        self.assertIn(u"**`S100YZEV` の `R017`**", self.t)
        self.assertIn(d[0][u"席の参照先"], self.t)

    def test_2_the_claimed_number_and_unit_come_from_the_record(self):
        d = self.r[u"R-2 正しい主張を不一致にした(無改変)"][u"明細"][0]
        self.assertEqual(d[u"単位"], u"千円")
        self.assertEqual(d[u"値"], 119947.0)
        self.assertIn(u"**119,947**(単位 千円)", self.t)
        self.assertIn(u"119,947,000 円", self.t)

    def test_3_the_cause_is_the_third_one(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"| 規則が厳しすぎた | **違う** |", b)
        self.assertIn(u"| **主張の種類の取り違え** | **これが原因** |", b)
        self.assertIn(u"**119,947 千円は差分であって残高ではない。**", b)
        self.assertIn(u"`diff(a-b)`", b)

    def test_4_it_does_not_claim_the_fix_works(self):
        b = sec(self.t, "## §3")
        self.assertIn(u"**「消える」は見込みであって、測っていない。**", b)
        self.assertIn(u"**既存の数は 1 つも変えていない**", b)


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.r = json.load(io.open(V1, encoding="utf-8"))

    def test_5_the_purpose_is_to_count_not_to_show_the_hole(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"**穴の存在を示すだけでは足りない**", b)
        self.assertIn(u"**この封が足すのは「実材料の上で、その穴が何件の誤通過を"
                      u"生むか」である。**", b)

    def test_6_four_branches_including_a_control(self):
        b = sec(self.t, "### 第 1 部", "### 第 2 部")
        for k in (u"| **対照** |", u"| **単位** |", u"| **期間** |", u"| **次元** |"):
            self.assertIn(k, b, k)
        self.assertIn(u"**ここが GROUNDED でない行は無効にする**", b)
        self.assertIn(u"**変えるのは注入した fact の属性 1 つだけで、値は変えない。**", b)

    def test_7_the_second_part_measures_exposure_without_injection(self):
        b = sec(self.t, "### 第 2 部", "## §2")
        for k in (u"**別の期間**", u"**別の次元**", u"**別の単位**"):
            self.assertIn(k, b, k)
        self.assertIn(u"**これが「値の照合では捕まらない取り違え」が"
                      u"実データに何件あるかの代理指標である。**", b)

    def test_8_the_denominator_is_the_24_passing_rows_of_the_record(self):
        n = len([x for x in self.r["rows"]
                 if x[u"**B′ の最終判定**"] == u"検査通過"])
        self.assertEqual(n, 24)
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"**分母は %d 行**" % n, b)
        self.assertIn(u"**対照が `GROUNDED` でない行は両部から外す**", b)

    def test_9_eight_predictions_with_failure_conditions(self):
        b = sec(self.t, "## §3", "## §4")
        ids = re.findall(r"(?m)^\| \*\*Q-(\d)\*\*", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(re.findall(u"外れ", b)), 9)
        self.assertIn(u"**この封の新しい数は第 2 部(Q-5〜Q-7)である。**", b)

    def test_10_what_cannot_be_shown(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn(u"**誤通過の件数は、注入を作った私の手で決まる。**", b)
        self.assertIn(u"**危険度は第 2 部の露出で語る。**", b)

    def test_11_zero_does_not_mean_safe(self):
        b = sec(self.t, "## §5", "## §6")
        self.assertIn(u"**0 件でも「放置してよい」とは書かない**", b)
        self.assertIn(u"**「第 1 層を直すべき」と書かない。**", b)

    def test_12_what_is_not_done(self):
        b = sec(self.t, "## §6", "## §7")
        for k in (u"**engine を直さない**", u"**規則を増やさない**",
                  u"**既存の記録を書き換えない**", u"**席を呼ばない。**",
                  u"**注入した fact を repo に残さない**"):
            self.assertIn(k, b, k)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                              "--", rel], cwd=ROOT, capture_output=True,
                             text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_13_the_seal_precedes_the_measurement(self):
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
