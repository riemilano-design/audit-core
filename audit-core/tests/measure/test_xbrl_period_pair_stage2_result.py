# -*- coding: utf-8 -*-
u"""期間の対 PP ― 段 2(engine)の追記(`docs/XBRL_PERIOD_PAIR_RESULT_2026-10-19.md` の
「## 段 2(engine。2026-10-20)」節)の門。

**数は記録 `fixtures/xbrl/cd8/period_pair_stage2_2026-10-19.json` を正本に突き合わせる。**
段 1 の本文・段 1 の門(`test_xbrl_period_pair_result.py`)は変えない。この門は**追記した節だけ**を縛る。
外れ 3 欄(H-12・H-14・H-17)が外れとして残ることを固定する(封は書き換えない)。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_PERIOD_PAIR_RESULT_2026-10-19.md")
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "period_pair_stage2_2026-10-19.json")


def text(p=DOC):
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

    def test_1_commits_and_head(self):
        self.assertEqual(self.r["seal_commit"], "790a5c5")
        self.assertEqual(self.r["seal_addendum_commit"], "78a04f5")
        self.assertEqual(self.r["engine_commit"], "ac8c3ff")

    def test_2_row_split_is_13_4_175(self):
        g = self.r[u"行"]
        self.assertEqual(
            (g[u"192 行"], g[u"率の主張・参照先 1 本(17 行)"],
             g[u"うち段1 兄弟1本(13)"], g[u"うち段1 兄弟2本=重複(4)"], g[u"他(175 行)"]),
            (192, 17, 13, 4, 175))

    def test_3_h12_thirteen_lines_twelve_match(self):
        d = self.r[u"**H-12 段1の13行との一致(行ごと)**"]
        self.assertEqual(len(d), 13)
        mismatched = [x for x in d if not x[u"一致"]]
        self.assertEqual([(x["doc"], x["id"]) for x in mismatched], [("S100YYRV", "R014")])
        self.assertEqual(mismatched[0][u"段2"]["state"], "UNPROVABLE")
        self.assertEqual(mismatched[0][u"段2"]["reason"], "ambiguous_dimension:1")
        self.assertEqual(mismatched[0][u"段1"]["state"], "GROUNDED")

    def test_4_h16_h17_duplicate_group(self):
        d = self.r[u"**H-16/H-17 重複4行の PP-2 後**"]
        self.assertEqual(len(d), 4)
        self.assertTrue(all(x[u"1本になった"] for x in d))
        self.assertTrue(all(x[u"後の兄弟本数(PP-2)"] == 1 and x[u"duplicate_values"] is False for x in d))
        self.assertEqual(self.r[u"**H-17 重複4行の state 分布**"], {"GROUNDED": 3, "UNPROVABLE": 1})

    def test_5_h18_both_definitions(self):
        task = self.r[u"**H-18(task) 他175行と③の一致**"]
        self.assertEqual((task[u"一致"], task[u"行"]), (175, 175))
        self.assertEqual(task[u"不一致の明細"], [])
        seal = self.r[u"**H-18(封) 13行はPP-2で変わらない**"]
        self.assertEqual(len(seal), 13)
        self.assertTrue(all(x[u"変わらない"] for x in seal))

    def test_6_controls_thirteen_lines(self):
        c = self.r[u"**対照(13行すべて)**"]
        self.assertEqual(c[u"値"], {"VALUE_MISMATCH": 13})
        self.assertEqual(c[u"符号"], {"VALUE_MISMATCH": 13})
        self.assertEqual(c[u"前期を消す"], {"('UNPROVABLE', 'prior_sibling:0')": 13})
        self.assertEqual(c[u"前期を増やす(H-19)"],
                         {"('UNPROVABLE', 'prior_sibling:2;duplicate_values')": 13})

    def test_7_proven_rows(self):
        p = self.r[u"**実証できた行**"]
        self.assertEqual(p[u"175行(③と同じ組み立て)"], 62)
        self.assertEqual(p[u"17行(PP。段2)"], 15)
        self.assertEqual(p[u"192行の合計(段2)"], 77)
        self.assertEqual(p[u"段1(参考。H-11)"], 75)

    def test_8_mutations_pp_r1_to_r4_all_red(self):
        m = self.r[u"**H-13 変異 PP-R1〜R4**"]
        self.assertEqual(len(m), 4)
        self.assertEqual([x["id"] for x in m],
                         ["PP-R1-sign-ignored", "PP-R2-two-siblings-picks-the-first",
                          "PP-R3-dimension-different-prior-counted",
                          "PP-R4-duplicate-differing-values-collapsed"])
        self.assertTrue(all(x[u"色"] == "red" for x in m))

    def test_9_tally_five_hits_three_misses(self):
        ids_true = [p[u"記号"] for p in self.pred[u"欄ごと"] if p[u"当たり"] is True]
        ids_false = [p[u"記号"] for p in self.pred[u"欄ごと"] if p[u"当たり"] is False]
        self.assertEqual(ids_true, ["H-13", "H-15", "H-16", "H-18", "H-19"])
        self.assertEqual(ids_false, ["H-12", "H-14", "H-17"])
        self.assertEqual(self.pred[u"当たり"], 5)
        self.assertEqual(self.pred[u"外れ"], 3)

    def test_10_eight_predictions_in_order(self):
        ids = [p[u"記号"] for p in self.pred[u"欄ごと"]]
        self.assertEqual(ids, ["H-12", "H-13", "H-14", "H-15", "H-16", "H-17", "H-18", "H-19"])


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text()
        self.r = rec()

    def test_11_section_exists(self):
        self.assertIn(u"## 段 2(engine。2026-10-20)", self.t)

    def test_12_headline_numbers_in_doc(self):
        b = sec(self.t, "## 段 2(engine。2026-10-20)", "### §7")
        self.assertIn(u"12 / 13", b)
        self.assertIn(u"S100YYRV", b)
        self.assertIn(u"R014", b)
        self.assertIn(u"175 / 175", b)
        self.assertIn(u"4 / 4", b)
        self.assertIn(u"S100YWGX", b)
        self.assertIn(u"R008", b)
        self.assertIn(u"62 + 15 = 77", b)

    def test_13_tally_table_matches_the_record(self):
        b = sec(self.t, "### §7", "### §8")
        self.assertIn(u"**当たり 5 / 外れ 3(H-12・H-14・H-17)。**", b)
        self.assertEqual(len(re.findall(r"\| \*\*外れ\*\* \|", b)), 3)
        self.assertEqual(len(re.findall(r"\| 当たり \|", b)), 5)
        for h in ("H-12", "H-14", "H-17"):
            self.assertRegex(b, r"\| %s \|.*\| \*\*外れ\*\* \|" % h)
        self.assertEqual(len(re.findall(u"\\*\\*封は直さない。\\*\\*", b)), 3)

    def test_14_does_not_rewrite_stage1_body(self):
        # 段1の本文の代表行(段1の門が別に縛る)がそのまま残っている(書き換えていない証拠)
        self.assertIn(u"**予測 当たり 9 / 外れ 2(段 1の 11 欄)**", self.t)
        self.assertIn(u"**12 / 13 が検算一致(`GROUNDED`)。**", self.t)
        self.assertIn(u"**当たり 9 / 外れ 2(段 1 の 11 欄。H-12〜H-15 は段 2 で測る)。**", self.t)


if __name__ == "__main__":
    unittest.main()
