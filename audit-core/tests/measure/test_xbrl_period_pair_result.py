# -*- coding: utf-8 -*-
u"""期間の対(PP)の実測(docs/XBRL_PERIOD_PAIR_RESULT_2026-10-19.md)の門。

**本文の数は `period_pair_2026-10-19.json` を正本に突き合わせる。**
外れ 2 欄(H-4・H-10)が外れとして残ること、「精度」の主張が上がっていないことを固定する。
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_PERIOD_PAIR_RESULT_2026-10-19.md")
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "period_pair_2026-10-19.json")
SEAL_REL = "docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md"


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p=REC):
    return json.load(io.open(p, encoding="utf-8"))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = rec()
        self.pred = self.r[u"**予測との照合**"]

    def test_1_rows_and_sibling_distribution(self):
        self.assertEqual(self.r[u"行"][u"率の主張(％/%)"], 37)
        self.assertEqual(self.r[u"行"][u"うち参照先 1 本"], 17)
        self.assertEqual(self.r[u"行"][u"参照先なし"], 20)
        d = self.r[u"**第 1 部 兄弟の本数**"]
        self.assertEqual((d.get("1"), d.get("2"), d.get("0", 0)), (13, 4, 0))

    def test_2_sign_and_state(self):
        s2 = self.r[u"**第 2 部 符号・検算**"]
        signs = s2[u"符号の分布"]
        self.assertEqual(sum(signs.values()), 13)
        self.assertNotIn("None", signs)
        self.assertEqual(s2[u"state の分布(13 行)"], {"GROUNDED": 12, "VALUE_MISMATCH": 1})

    def test_3_r017_detail_found_no_matching_element(self):
        h4 = self.r[u"R017 の明細(H-4)"]
        self.assertEqual(h4[u"同じセグメント枠の別の要素"], [])
        self.assertEqual(h4[u"参照先"]["name"], "jppfs_cor:OrdinaryIncome")

    def test_4_controls_all_thirteen(self):
        c = self.r[u"**対照(13 行すべて)**"]
        self.assertEqual(c[u"値"], {"VALUE_MISMATCH": 13})
        self.assertEqual(c[u"符号"], {"VALUE_MISMATCH": 13})
        self.assertEqual(c[u"前期を消す"], {"('UNPROVABLE', 'prior_sibling:0')": 13})
        self.assertEqual(c[u"前期を増やす"], {"('UNPROVABLE', 'prior_sibling:2')": 13})

    def test_5_h9_h10_h11(self):
        self.assertEqual(self.r[u"H-9 当てていない行数"],
                         {u"参照先なし": 20, u"金額の主張": 155, u"PP を当てた行数": 0})
        self.assertEqual(self.r[u"H-10 (d)PU の発火(13 行)"], {"d": 1, "P": 0, "U": 0})
        self.assertEqual(self.r[u"H-11 実証できた行"], {u"v1(合成の後)": 62, u"PP を足した後": 75})

    def test_6_tally_nine_hits_two_misses_among_stage1(self):
        ids_true = [p[u"記号"] for p in self.pred[u"欄ごと"] if p[u"当たり"] is True]
        ids_false = [p[u"記号"] for p in self.pred[u"欄ごと"] if p[u"当たり"] is False]
        ids_stage2 = [p[u"記号"] for p in self.pred[u"欄ごと"] if p[u"当たり"] == u"段 2 で測る"]
        self.assertEqual(len(ids_true), 9)
        self.assertEqual(ids_false, ["H-4", "H-10"])
        self.assertEqual(ids_stage2, ["H-12", "H-13", "H-14", "H-15"])
        self.assertEqual(self.pred[u"当たり"], 9)
        self.assertEqual(self.pred[u"外れ"], 2)

    def test_7_fifteen_predictions_in_order(self):
        ids = [p[u"記号"] for p in self.pred[u"欄ごと"]]
        self.assertEqual(ids, ["H-%d" % i for i in range(1, 16)])


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_8_headline_tally(self):
        self.assertIn(u"**予測 当たり 9 / 外れ 2(段 1の 11 欄)**", self.t)

    def test_9_state_table_matches_the_record(self):
        s2 = self.r[u"**第 2 部 符号・検算**"][u"state の分布(13 行)"]
        self.assertIn(u"**12 / 13 が検算一致(`GROUNDED`)。**", self.t)
        self.assertEqual(s2["GROUNDED"], 12)
        self.assertEqual(s2["VALUE_MISMATCH"], 1)

    def test_10_control_section_matches_the_record(self):
        c = self.r[u"**対照(13 行すべて)**"]
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"**`VALUE_MISMATCH` 13 / 13**", b)
        self.assertEqual(c[u"値"][u"VALUE_MISMATCH"], 13)
        self.assertEqual(len(re.findall(u"13 / 13", b)), 4)

    def test_11_h9_h10_h11_stated(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"当てた行数 0", b)
        self.assertIn(u"発火は `d` 1・`P` 0・`U` 0", b)
        self.assertIn(u"62 → 75", b)

    def test_12_prediction_tally_and_both_misses(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn(u"**当たり 9 / 外れ 2(段 1 の 11 欄。H-12〜H-15 は段 2 で測る)。**", b)
        self.assertEqual(len(re.findall(r"\| \*\*当たり\*\* \|", b)), 9)
        self.assertRegex(b, r"\| \*\*H-4\*\* \|.*\| \*\*外れ\*\* \|")
        self.assertRegex(b, r"\| \*\*H-10\*\* \|.*\| \*\*外れ\*\* \|")
        self.assertIn(u"**封は直さない。**", b)
        self.assertEqual(len(re.findall(u"\\*\\*封は直さない。\\*\\*", b)), 2)

    def test_13_no_claim_of_accuracy_gain(self):
        self.assertIn(u"**精度は上げていない。**", self.t)
        self.assertIn(u"**同じ 8 書類である。**", self.t)
        for m in re.finditer(u"精度は上", self.t):
            ctx = self.t[m.start():m.end() + 12]
            self.assertTrue(u"上げていない" in ctx or u"上がっていない" in ctx or u"上がらない" in ctx, ctx)

    def test_14_the_seal_commit_is_the_one_that_added_the_seal(self):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h", "--", SEAL_REL],
                             cwd=ROOT, capture_output=True, text=True).stdout.split()
        if not out:
            self.skipTest(u"封が未 commit")
        self.assertIn(u"commit `%s`" % out[-1][:7], self.t)


if __name__ == "__main__":
    unittest.main()
