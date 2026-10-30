# -*- coding: utf-8 -*-
"""別資料の結果の文書(docs/DOMAIN1_REPRO_RESULT_2026-10-17.md)を固定する。

**「止めた」「parser を直していない」「原因は道具の側」が落ちないことを門で見る。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "DOMAIN1_REPRO_RESULT_2026-10-17.md")
REC = os.path.join(ROOT, "fixtures", "sheet", "repro_material_2026-10-17.json")
SAME = os.path.join(ROOT, "docs", "DOMAIN1_VERIFY2_RESULT_2026-10-17.md")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = json.load(io.open(REC, encoding="utf-8"))

    def test_1_three_layers_and_it_is_a_separate_document(self):
        for k in ("# 第 1 層 判定", "# 第 2 層 観測", "# 第 3 層 解釈"):
            self.assertIn(k, self.t, k)
        head = self.t[:self.t.index("\n# 第 1 層")]
        self.assertIn("**費用 0 USD。報告文も席も 1 回も生成していない。**", head)
        self.assertIn("と同じ表に混ぜない。**", head)
        self.assertIn("DOMAIN1_VERIFY2_RESULT_2026-10-17.md", head)
        self.assertTrue(os.path.exists(SAME), "同じ材料の文書が別に在る")

    def test_2_the_stop_matches_the_record(self):
        b = sec(self.t, "## §1-1", "## §1-2")
        self.assertIn("**0 行** | **止める**", b)
        self.assertIn("**止めた。parser を直していない。生成していない。**", b)
        self.assertEqual(self.r["counts"]["表2_行"], 0)
        self.assertTrue(self.r["**止めた**"])

    def test_3_the_cause_is_named_as_mine(self):
        b = sec(self.t, "## §1-2", "## §1-3")
        self.assertIn("**「別資料は同じ構造だったが、"
                      "道具が年度の字に縛られていて読めなかった。」**", b)
        rows = re.findall(r"(?m)^\| `measure/", b)
        self.assertEqual(len(rows), 3, "判定に使っている 3 件を字で並べる")
        d = self.r["診断: 年度の字で動いている所"]["判定に使っている"]
        self.assertEqual(len(d), 3)

    def test_4_the_prompt_conflict_is_handed_to_the_human(self):
        b = sec(self.t, "## §1-3", "# 第 2 層")
        self.assertIn("**どちらも私が勝手に選ばない。人間に判断を求める。**", b)
        self.assertIn("令和６年度の歳入歳出決算の抜粋です", b)

    def test_5_my_module_instance_bug_is_disclosed(self):
        b = sec(self.t, "## §2-2", "## §2-3")
        self.assertIn("**byte 一致**", b)
        self.assertIn("捕まえたのは門 `test_11`", b)
        self.assertIn("**門が無ければ、令和６年度の材料を"
                      "「別資料の結果」として報告していた。**", b)

    def test_6_the_estimate_was_not_spent(self):
        b = sec(self.t, "## §2-3", "## §2-4")
        self.assertIn("**止めたので 1 円も使っていない。**", b)
        self.assertIn("**3.1071 USD**", b)

    def test_7_j1_missed_and_the_rest_is_unmeasured(self):
        b = sec(self.t, "## §2-4", "# 第 3 層")
        self.assertIn("**外れ**", b)
        self.assertIn("**未測定**(生成していない)", b)
        self.assertIn("**「未測定」を「当たり」にも「外れ」にも数えない**", b)
        self.assertIn("**J-1 の外れは「自分の道具の汎用性を高く見ていた」"
                      "向きである。**", b)

    def test_8_the_scope_of_the_fix_is_not_measured(self):
        b = sec(self.t, "## §3-2", "## §3-3")
        self.assertIn("**しかし「ほかに様式に縛られた所が在るか」は"
                      "数えていない**", b)
        self.assertIn("**別の自治体・別の様式に対する耐性は 1 件も"
                      "測っていない。**", b)

    def test_9_three_options_and_the_audit_requirement(self):
        b = sec(self.t, "## §3-3", "## §4")
        opts = re.findall(r"(?m)^\| \*\*\((a|b|c)\)\*\*", b)
        self.assertEqual(opts, ["a", "b", "c"], "選択肢は 3 つ")
        self.assertIn("**独立した監査の GO が要る**", b)
        self.assertIn("**令和６年度の結果が 1 つも動かないこと**を門で確かめる", b)
        self.assertIn("**私は (b) → (a) の順を推す。**", b)

    def test_10_six_limits(self):
        b = sec(self.t, "## §4 示せないこと")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 7)], "限界は 6 本")
        self.assertIn("**「差が別資料でも残るか」は**まだ答えていない。**", b)


if __name__ == "__main__":
    unittest.main()
