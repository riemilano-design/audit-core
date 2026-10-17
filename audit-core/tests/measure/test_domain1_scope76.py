# -*- coding: utf-8 -*-
"""候補範囲 76 行の実験(封 docs/DOMAIN1_SCOPE76_SEAL_2026-10-17.md)を固定する。

守るのは 12 つ。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "scope76_2026-10-17.json")
TEETH = os.path.join(FX, "scope76_teeth_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SCOPE76_RESULT_2026-10-17.md")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class OnlyTheCandidatePoolChangedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)

    def test_1_claims_are_unchanged(self):
        self.assertEqual(self.rec["主張の数"], 35,
                         "**主張が 35 件でない ― 実験は無効**")
        self.assertTrue(self.rec["対照群が段 11 の記録と一致"])

    def test_2_the_rules_are_listed_as_untouched(self):
        for k in ("6 欄の鍵", "接続の一意性条件", "別名規則", "親の規則",
                  "語彙", "列の手がかり", "主張の切り出し"):
            self.assertIn(k, self.rec["変えていないもの"], k)
        self.assertIn("`bind` に渡す候補の母集団だけ", self.rec["変えたもの"])
        self.assertEqual(self.rec["min_independent"], 3)

    def test_3_the_pool_actually_shrank(self):
        r1 = self.rec["R-1 候補に残った行"]
        self.assertLess(r1["候補"], r1["索引の行"] / 10,
                        "母集団が絞れていない")
        self.assertGreater(r1["候補"], 0)

    def test_4_the_verdict_is_r4_not_r3(self):
        r3 = self.rec["R-3 一意に接続した"]["件数"]
        r4 = self.rec["R-4 **判定** 正解と一致した"]["件数"]
        wrong = self.rec["R-3 のうち正解と違った(**誤接続**)"]["件数"]
        self.assertEqual(r3, r4 + wrong, "R-3 = R-4 + 誤接続 になっていない")
        self.assertEqual(r4, 5, "**R-4 が変わったら結果の文書も直すこと**")
        self.assertEqual(wrong, 0)
        self.assertIn("母集団を変えると解ける", self.rec["注"])

    def test_5_nothing_broke(self):
        r5 = self.rec["R-5 既存の接続"]
        self.assertEqual(r5["壊れた"], [])
        self.assertEqual(r5["別の行に動いて誤接続になった"], [])
        self.assertIn("接続数の増加で相殺しない", r5["注"])

    def test_6_each_of_the_twelve_is_recorded(self):
        r2 = self.rec["R-2 保留 12 件それぞれ"]
        self.assertEqual(len(r2), 12)
        for x in r2:
            for side in ("対照群", "限定"):
                self.assertIn("状態", x[side])
                self.assertIn("鍵の通り", x[side])

    def test_7_restrict_is_one_function_with_teeth(self):
        m = _mod("s76_t", "sheet_scope76_2026-10-17.py")
        e = {"scope": "一般会計", "level": "項", "parent": "総務費",
             "name": "子供政策連携費", "column": "支出済額", "value": 1}
        k = m.entry_key(e, {})
        self.assertEqual(m.restrict([e], {k}, {}), [e])
        self.assertEqual(m.restrict([e], set(), {}), [],
                         "**母集団を絞っていない**")
        fold = {"東京都と場会計": "と場会計"}
        e2 = dict(e, scope="東京都と場会計")
        self.assertEqual(m.entry_key(e2, fold)[0], "と場会計",
                         "別名表が両側に当たっていない")


class TeethTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = load(TEETH)

    def test_8_both_teeth_were_built_from_real_material(self):
        self.assertTrue(self.t["artificial"])
        self.assertTrue(self.t["歯-B の材料は在ったか"],
                        "歯-B が作れないなら文書にそう書くこと")
        self.assertEqual(len(self.t["結果"]), 2)
        for x in self.t["結果"]:
            self.assertIn("文(機械で作った)", x)
            self.assertEqual(x["対照群(索引 4,209 行)"]["状態"], "GROUNDED",
                             "対照群で結べないなら歯になっていない")

    def test_9_the_cost_is_a_miss_not_a_wrong_bind(self):
        for name, shape in self.t["代価の形のまとめ"].items():
            self.assertEqual(shape, "**結べない(見落とし)**", name)
        for x in self.t["結果"]:
            self.assertIn("値で選ばない", x["限定(抜粋 76 行)"]["保留の理由"] or "")

    def test_10_artificial_is_separated_from_real(self):
        k = "**この歯は engine の安全性を示すものではない**"
        self.assertIn(k, self.t)
        self.assertIn("実データでの安全性の証明とは分けて記録する", self.t[k])
        joined = "\n".join(self.t["limits"])
        self.assertIn("実データにこの形は無い", joined)
        self.assertIn("安全側の代価であって、安全の証拠ではない", joined)


class ResultDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with io.open(DOC, encoding="utf-8") as fh:
            cls.d = fh.read()
        cls.rec = load(REC)

    def test_11_numbers_match_the_record(self):
        r1 = self.rec["R-1 候補に残った行"]
        self.assertIn("**4,209 → %d 行**" % r1["候補"], self.d)
        self.assertIn("| **R-4** | **そのもち正解集合と一致した** | **5 件** |"
                      .replace("そのもち", "そのうち"), self.d)
        self.assertIn("**50.0% → 70.8%。**", self.d)
        self.assertIn("**まだ 7 件足りない。**", self.d)

    def test_12_the_obvious_caveat_and_the_two_misses(self):
        self.assertIn("**候補を絞れば曖昧さが減るのは当たり前である。**", self.d)
        self.assertIn("「母集団を変えると解ける」である", self.d)
        self.assertIn("**外れ 2 本。", self.d)
        self.assertIn("**S-8 の外れは、engine の「値で選ばない」規則が"
                      "効いていたからである。**", self.d)
        self.assertIn("**顧客がその 76 行を照合対象として指定できるかは、"
                      "ここでは測れない。**", self.d)
        self.assertIn("C の評価条件は**C を走らせる前に別の封で固定する。**",
                      self.d)


if __name__ == "__main__":
    unittest.main()
