# -*- coding: utf-8 -*-
"""PoC 第 1 便 A / B の採点(封 §4)と M-3 の追記を固定する。

守るのは 12 つ。
  1. **A1 と A2 を別々に採点**している(2 席の一致を証拠に数えない)
  2. **同じ関数**で 3 方式を採点している(`score_arm` / `resolve` は 1 つ)
  3. 分母が**正解集合 24 件**で、3 方式とも同じ
  4. **主採点と厳格採点の両方**が記録に在る
  5. 数が**その場で採点し直した数と一致**する
  6. **35 件すべてが件ごとに記録**されている
  7. `same_row` が**欄を 1 つずつ壊すと落ちる**(歯)
  8. `resolve` の「値が違う」枝が**壊した入力で発火**する(歯)
  9. **封の M-3 の数が追記で書き換えられていない**
 10. 追記に**順位が変わったかの判定**が在ること
 11. **別枠での「根拠のない確認」**が方式ごとに数えられていること
 12. 封の予測 W-4(A に誤接続が 1 件以上)が**外れた**ことが分かる形で残ること
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
REC = os.path.join(FX, "poc_ab_score_2026-10-17.json")
ADD = os.path.join(FX, "poc_m3_addendum_2026-10-17.json")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


ARMS = ("A1 一般 LLM(sonnet)", "A2 一般 LLM(haiku)", "B Audit Core")


class SameTreatmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)
        cls.m = _mod("abscore_t", "sheet_poc_ab_score_2026-10-17.py")

    def test_1_two_seats_are_scored_separately(self):
        self.assertEqual(tuple(self.rec["主採点(寛容な会計)"]), ARMS)
        self.assertIn("**2 席の一致は証拠に数えない**", self.rec)
        self.assertIn("一致率は書かない", self.rec["**2 席の一致は証拠に数えない**"])
        for k in self.rec:
            self.assertNotIn("席の一致率", str(k))

    def test_2_one_function_for_every_arm(self):
        src = io.open(os.path.join(MEASURE, "sheet_poc_ab_score_2026-10-17.py"),
                      encoding="utf-8").read()
        self.assertEqual(src.count("def score_arm("), 1)
        self.assertEqual(src.count("def resolve("), 1)
        self.assertEqual(src.count("def same_row("), 1)
        self.assertIn("**pointer の有無を分母にしていない。**", self.rec["M-3 の注"])
        self.assertIn("canonicalize を通していない", self.rec["M-3 の注"])

    def test_3_the_denominator_is_the_gold_set_for_all_arms(self):
        gold = load(GOLD)["正解集合"]["件数"]
        self.assertEqual(self.rec["正解集合"], gold)
        for a in ARMS:
            v = self.rec["主採点(寛容な会計)"][a]
            self.assertEqual(v["M-1 誤接続率"]["den"], gold, a)
            self.assertEqual(v["M-2 回収率"]["den"], gold, a)

    def test_4_both_lenient_and_strict_are_recorded(self):
        strict = self.rec["**厳格な会計(印字のみ)。埋もれさせない**"]
        self.assertEqual(tuple(strict), ARMS)
        for a in ARMS:
            self.assertIn("M-2 回収率", strict[a])
            self.assertIn("M-1 誤接続率", strict[a])

    def test_5_every_claim_is_recorded(self):
        per = self.rec["件ごとの記録(35 件すべて)"]
        self.assertEqual(len(per), 35)
        for line in per:
            for a in ARMS:
                self.assertIn(a, line)
                self.assertIn("判定", line[a])
            self.assertIn("正解集合か", line)


class RescoredTest(unittest.TestCase):
    """**記録を読むだけにしない。**その場で採点し直して突き合わせる。"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("abscore_t2", "sheet_poc_ab_score_2026-10-17.py")
        cls.rec = load(REC)
        cls.gold = load(GOLD)
        b = load(os.path.join(FX, "m11_binds_2026-10-16.json"))
        cls.claims = {c["id"]: c for c in b["claims"]}
        bn = {x["claim_id"]: x for x in b["binds_new"]}
        s1 = {a["id"]: a for a in
              load(os.path.join(FX, "m11_answers_seat1_2026-10-16.json"))["answers"]}
        cls.arms = {
            "A1 一般 LLM(sonnet)": {r["id"]: cls.m.answer_of_seat(s1.get(r["id"]))
                                 for r in cls.gold["rows"]},
            "B Audit Core": {r["id"]: cls.m.answer_of_core(bn[r["id"]])
                             for r in cls.gold["rows"]}}

    def test_6_numbers_reproduce(self):
        for name, ans in self.arms.items():
            got = self.m.score_arm(name, ans, self.gold["rows"], self.claims)
            want = self.rec["主採点(寛容な会計)"][name]
            self.assertEqual(got["正解集合"], want["正解集合"], name)
            self.assertEqual(got["別枠"], want["別枠"], name)
            self.assertEqual(got["M-2 回収率"]["num"], want["M-2 回収率"]["num"], name)

    def test_7_same_row_fails_when_any_field_is_broken(self):
        gold = [r for r in self.gold["rows"] if r["正解"]][0]["正解"]
        good = {"会計": gold["会計(印字)"], "階層": gold["階層"], "親": gold["親"],
                "科目名": gold["科目名"], "列": gold["列"], "値": gold["値"]}
        self.assertTrue(self.m.same_row(good, gold))
        for f, bad in (("階層", "款"), ("親", "別の親"), ("科目名", "別の科目"),
                       ("列", "不用額"), ("値", 1), ("会計", "別会計")):
            a = dict(good)
            a[f] = bad
            self.assertFalse(self.m.same_row(a, gold), "%s を壊しても通った" % f)

    def test_8_resolve_detects_a_value_that_is_not_there(self):
        a = {"会計": "東京都と場会計", "階層": "目",
             "親": "と場事業費 > と場事業費", "科目名": "運営費",
             "列": "補正予算額", "値": 48327000}
        ok, why, cell = self.m.resolve(a, 48327000)
        self.assertFalse(ok)
        self.assertIn("値が主張と違う", why)
        ok2, why2, _ = self.m.resolve(a, -48327000)
        self.assertTrue(ok2, why2)


class AddendumTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.add = load(ADD)
        cls.rec = load(REC)

    def test_9_the_sealed_number_is_not_rewritten(self):
        sealed = cls_sealed = self.add["M-3(封の字。残す)"]
        for a in ARMS:
            self.assertEqual(sealed[a]["num"],
                             self.rec["主採点(寛容な会計)"][a]["M-3 根拠の再現性"]["num"],
                             "**封の M-3 の数が書き換わっている**")
        self.assertIn("封の数は残し", self.add["**なぜ追記が要るのか**"])
        self.assertIn("**これは追記であって、封の採点条件の変更ではない。**",
                      "\n".join(self.add["limits"]))

    def test_10_the_order_change_is_disclosed(self):
        o = self.add["順位は変わったか"]
        self.assertIn("変わった", o)
        self.assertIsInstance(o["変わった"], bool)
        self.assertEqual(len(o["封の順"]), 3)
        self.assertEqual(len(o["追記の順"]), 3)
        self.assertIn("結論を追記の側で書き直す", o["注"])

    def test_11_unfounded_confirmations_are_counted(self):
        u = self.add["別枠での根拠のない確認(**原資料に無い数を在るかのように答えた**)"]
        self.assertEqual(tuple(u), ARMS)
        for a in ARMS:
            self.assertIn("件数", u[a])
        self.assertEqual(u["B Audit Core"]["件数"], 0)
        self.assertGreaterEqual(u["A1 一般 LLM(sonnet)"]["件数"], 1,
                                "A の根拠のない確認が 0 件になったら結果の文も直すこと")

    def test_12_prediction_w4_was_wrong(self):
        """封の W-4「A には誤接続が 1 件以上出る」は**外れた**(誤接続 0 件)。"""
        for a in ("A1 一般 LLM(sonnet)", "A2 一般 LLM(haiku)"):
            self.assertEqual(
                self.rec["主採点(寛容な会計)"][a]["M-1 誤接続率"]["num"], 0,
                "**W-4 の照合が変わる。結果の文書を直すこと**")


if __name__ == "__main__":
    unittest.main()
