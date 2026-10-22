# -*- coding: utf-8 -*-
"""(ア) の実装と結果の門。

**文書の数は記録 JSON を正本にして突き合わせる。**
判定の関数(`judge` / `_say` / `norm_pointer`)は**壊した入力で赤くなることを確かめる。**
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "xbrl_a_core_vs_grep_2026-10-17.py")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "a_core_vs_grep_2026-10-17.json")
REC20 = os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                     "a_core_vs_grep_P20_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "XBRL_A_CORE_VS_GREP_RESULT_2026-10-17.md")


def _mod():
    sp = importlib.util.spec_from_file_location("a_core_vs_grep", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class NormPointerTest(unittest.TestCase):
    """封 H-6。**4 つの形が同じ字になる。掛け忘れが一致率を作る。**"""

    def setUp(self):
        self.A = _mod()

    def test_1_all_three_shapes_normalise_to_one(self):
        f = self.A.norm_pointer
        want = "netsales@currentyearduration"
        for s in ("xbrl:jppfs_cor:NetSales@CurrentYearDuration",
                  "jppfs_cor:NetSales@CurrentYearDuration",
                  "NetSales@CurrentYearDuration",
                  "  NetSales@CurrentYearDuration  "):
            self.assertEqual(f(s), want, s)
        self.assertIsNone(f(None))

    def test_2_context_is_kept_and_distinguishes_members(self):
        """**context を落としたら別物が同じ字になる** ― 落としていないこと。"""
        f = self.A.norm_pointer
        a = f("xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration")
        b = f("OperatingIncome@CurrentYearDuration_SegmentMember")
        self.assertNotEqual(a, b)

    def test_3_the_search_arms_normalise_their_hits(self):
        """**`_say` が生の鍵を返したら赤くなる**(2026-10-17 に実際そうだった)。"""
        idx = {round(1.0, 6): [{"key": "NetSales@CurrentYearDuration",
                                "value": 1.0}]}
        said = self.A.d_prime(1.0, idx)
        self.assertEqual(said["参照先"], "netsales@currentyearduration")
        self.assertEqual(said["言うこと"], "確認済み")


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.A = _mod()

    def _inj(self, t):
        return {"type": t, "new_value": 1.0, "replacement": "1",
                "detail": {"true_ref_key": "A@C1", "coincident_ref_key": "B@C2",
                           "inserted_sentence": "x"}}

    def test_4_t5_hit_miss_and_hold(self):
        A = self.A
        g = A.gold_of(self._inj("T5_COINCIDENT"))
        hit = A.judge(self._inj("T5_COINCIDENT"), {"言うこと": "確認済み",
                                                 "参照先": "a@c1"}, g)
        self.assertTrue(hit["特定"])
        self.assertFalse(hit["誤認定"])
        wrong = A.judge(self._inj("T5_COINCIDENT"), {"言うこと": "確認済み",
                                                   "参照先": "b@c2"}, g)
        self.assertFalse(wrong["特定"])
        self.assertTrue(wrong["誤認定"])
        self.assertTrue(wrong["偶然一致する側だった"])
        held = A.judge(self._inj("T5_COINCIDENT"), {"言うこと": "一意でない",
                                                  "参照先": None}, g)
        self.assertTrue(held["保留"])
        self.assertFalse(held["誤認定"])

    def test_5_t3_naming_anything_is_wrong_and_t1_confirming_is_wrong(self):
        A = self.A
        g3 = A.gold_of(self._inj("T3_ABSENT"))
        self.assertTrue(A.judge(self._inj("T3_ABSENT"),
                                {"言うこと": "確認済み", "参照先": "x@y"}, g3)["誤認定"])
        self.assertFalse(A.judge(self._inj("T3_ABSENT"),
                                 {"言うこと": "原資料と一致しない", "参照先": None},
                                 g3)["誤認定"])
        g1 = A.gold_of(self._inj("T1_VALUE"))
        self.assertTrue(A.judge(self._inj("T1_VALUE"),
                                {"言うこと": "確認済み", "参照先": "x@y"}, g1)["誤認定"])
        self.assertFalse(A.judge(self._inj("T1_VALUE"),
                                 {"言うこと": "止めた(VALUE_MISMATCH)", "参照先": None},
                                 g1)["誤認定"])

    def test_6_the_two_core_readings_differ_on_a_stopped_claim(self):
        """**封の指標の欠陥そのものを固定する**(止めた Core の参照先の扱い)。"""
        A = self.A
        claim = {"state": "VALUE_MISMATCH", "value": 1.0,
                 "pointers": ["xbrl:jppfs_cor:A@C1"]}
        self.assertIsNone(A.core_say(claim)["参照先"])
        self.assertEqual(A.core_pointer_say(claim)["参照先"], "a@c1")
        g = {"state": "GROUNDED", "value": 1.0, "pointers": ["xbrl:jppfs_cor:A@C1"]}
        self.assertEqual(A.core_say(g)["参照先"], "a@c1")

    def test_7_dprime_says_three_things_only(self):
        A = self.A
        idx = {1.0: [{"key": "A@C1", "value": 1.0}, {"key": "B@C2", "value": 1.0}]}
        self.assertEqual(A.d_prime(1.0, idx)["言うこと"], "一意でない")
        self.assertEqual(A.d_prime(9.0, idx)["言うこと"], "原資料と一致しない")
        self.assertEqual(A.d_prime(1.0, {1.0: [{"key": "A@C1", "value": 1.0}]})
                         ["言うこと"], "確認済み")

    def test_8_ddouble_adds_multipliers_and_a_band_only(self):
        A = self.A
        idx = {1000.0: [{"key": "A@C1", "value": 1000.0}]}
        self.assertEqual(A.d_prime(1.0, idx)["言うこと"], "原資料と一致しない")
        self.assertEqual(A.d_double(1.0, idx, "1")["言うこと"], "確認済み")
        self.assertEqual(A.last_digit_step("27.6"), 0.1)
        self.assertEqual(A.last_digit_step("1,234"), 1.0)


class RecordAndDocTest(unittest.TestCase):
    def setUp(self):
        self.r = json.load(io.open(REC, encoding="utf-8"))
        self.t = text(DOC)

    def test_9_no_seat_was_called(self):
        self.assertIn("0 USD・席を呼ばない・通信しない", self.r["step"])
        s = text(SCRIPT)
        for bad in ("anthropic", "Task(", "subagent", "messages.create"):
            self.assertNotIn(bad, s, bad)
        self.assertIn("未使用の 8 件は使っていない",
                      self.t + json.dumps(self.r, ensure_ascii=False))

    def test_10_the_headline_table_matches_the_record(self):
        for arm, label in (("Core", "**Core(封の厳しい読み方)**"),
                           ("Core-P", "**Core-P(止めても pointer を読む)**"),
                           ("D′", "**D′**"), ("D″", "**D″**(強くした値検索)")):
            v = self.r["採点"][arm]
            ident = v["特定率(分母 = T5 の件数)"]
            self.assertIn("| %s | **%s**(%d/%d) |"
                          % (label, fmt(ident["率"]), ident["分子"], ident["分母"]),
                          self.t, "見出しの表が記録と違う: %s" % arm)

    def test_11_misidentification_ownership_split(self):
        """**誤認定の中身の違い**が記録と一致する(観測の核)。"""
        own = {a: self.r["採点"][a]["偶然一致する側を採った件"]
               for a in ("Core-P", "D′", "D″")}
        self.assertEqual(own["Core-P"], 0)
        self.assertEqual(own["D′"], 17)
        self.assertIn("| **Core-P** | 18 件 | **0 件** |", self.t)
        self.assertIn("| **D′** | 17 件 | **%d 件(全部)** |" % own["D′"], self.t)
        self.assertIn("| **D″** | 26 件 | **%d 件** |" % own["D″"], self.t)

    def test_12_unmapped_rows_are_disclosed_with_a_second_denominator(self):
        un = self.r["**対応が付かなかった件**"]
        self.assertEqual(un["件数"], 19)
        self.assertIn("**対応が付かなかった 19 件", self.t)
        self.assertIn("対応が付いた 20 件だけで数えても 0 件だった", self.t)
        self.assertIn("zero-count-may-be-my-own-bug", self.t)

    def test_13_p20_is_reported_as_identical(self):
        a = json.load(io.open(REC, encoding="utf-8"))["採点"]
        b = json.load(io.open(REC20, encoding="utf-8"))["採点"]
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))
        self.assertIn("**P20 は P16 と 1 件も違わなかった**", self.t)

    def test_14_the_metric_defect_and_my_bug_are_disclosed(self):
        self.assertIn("**つまり「正しく振る舞うほど 0 点になる指標」を封じていた**",
                      self.t)
        self.assertIn("metric-must-not-fall-when-component-works", self.t)
        self.assertIn("normalize-both-sides-of-a-comparison", self.t)
        self.assertIn("これで 6 回目である", self.t)
        self.assertIn("**封の数は書き換えない。**", self.t)

    def test_15_predictions_are_tallied_with_misses_named(self):
        self.assertIn("**当たり 4 / 外れ 1 / 読み方で分かれる 2 / 判定不能 1。**", self.t)
        self.assertIn("**外れ**(D′ の方がよく黙る)", self.t)
        self.assertIn("**この便の結果で本番の封は 1 文字も変えていない。**", self.t)

    def test_16_limits_are_seven_and_include_the_gold_doubt(self):
        b = self.t[self.t.index("## §3-2"):self.t.index("## §3-3")]
        import re
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 8)], "限界は 7 本")
        self.assertIn("**正解そのものが誤りうる**", b)
        self.assertIn("**値検索に有利な側に倒してある。**", b)


def fmt(x):
    return "判定不能" if x is None else "%.1f%%" % x


if __name__ == "__main__":
    unittest.main()
