# -*- coding: utf-8 -*-
"""誤りの生成と Core 単体の測定を固定する(封 docs/DOMAIN1_ERRDET_SEAL_2026-10-17.md)。

**壊した入力で 1 本ずつ当てられるように、判定は関数に切り出してある。**
"""
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
MAKE = os.path.join(FX, "errdet_make_2026-10-17.json")
CORE = os.path.join(FX, "errdet_core_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_ERRDET_CORE_RESULT_2026-10-17.md")
GOLD = os.path.join(FX, "poc_gold_2026-10-17.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")


def _mod(name, rel):
    sp = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "measure", rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


MK = _mod("errdet_make_for_test", "sheet_errdet_make_2026-10-17.py")
CO = _mod("errdet_core_for_test", "sheet_errdet_core_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class GenerationRulesTest(unittest.TestCase):
    def test_1_swap_digits_keeps_the_length_and_the_lead(self):
        for v in (33285483000, 48000000, 10169000000):
            for got in MK.swap_digits(v):
                self.assertEqual(len(str(got)), len(str(v)), v)
                self.assertNotEqual(got, v)
                self.assertNotEqual(str(got)[0], "0")
        self.assertEqual(MK.swap_digits(1100), [1010])   # 同じ数字の組は飛ばす

    def test_2_last_digit_moves_by_one_and_handles_nine(self):
        self.assertEqual(MK.last_digit(46526037000)[0], 46526037001)
        self.assertEqual(MK.last_digit(5942803689)[0], 5942803688)
        self.assertEqual(len(MK.last_digit(10)), 9, "+1 と +2〜+9")

    def test_3_postconditions_reject_the_wrong_group(self):
        cell = {"scope": "一般会計", "level": "項", "parent": "総務費",
                "name": "x", "column": "予算現額", "value": 100}
        cells = [dict(cell), {"scope": "一般会計", "level": "項",
                              "parent": "総務費", "name": "y",
                              "column": "予算現額", "value": 200}]
        # 群 I: 抜粋に在る値は通さない
        ok, why = MK.ok_value("I-1", 200, cell, cells, set(), set())
        self.assertFalse(ok)
        self.assertIn("抜粋に在る", why)
        # 群 I: 索引に在る値も通さない
        ok, why = MK.ok_value("I-1", 300, cell, cells, {300}, set())
        self.assertFalse(ok)
        self.assertIn("索引", why)
        # 群 II: 抜粋に無い値は通さない
        ok, why = MK.ok_value("II-1", 999, cell, cells, set(), set())
        self.assertFalse(ok)
        self.assertIn("抜粋に無い", why)
        # どの型でも: 同じ文に在る数・正しい値そのものは通さない
        ok, why = MK.ok_value("II-1", 200, cell, cells, set(), {200})
        self.assertFalse(ok)
        self.assertIn("同じ文", why)
        ok, why = MK.ok_value("I-1", 100, cell, cells, set(), set())
        self.assertFalse(ok)
        self.assertIn("正しい参照先の値と同じ", why)
        # 通る場合
        ok, why = MK.ok_value("II-1", 200, cell, cells, set(), set())
        self.assertTrue(ok)
        self.assertIsNone(why)

    def test_4_replacement_targets_the_right_occurrence(self):
        """**同じ表記が 2 回出ても、k 番目の主張の位置を置き換える。**"""
        t = "aは372,000,000円、bは0円、cは372,000,000円である"
        claims = [{"id": "X1", "text": "372,000,000円"},
                  {"id": "X2", "text": "0円"},
                  {"id": "X3", "text": "372,000,000円"}]
        self.assertTrue(MK.check_alignment(t, claims))
        got = MK.replace_at(t, claims, {"X3": "999円"})
        self.assertEqual(got, "aは372,000,000円、bは0円、cは999円である")
        got2 = MK.replace_at(t, claims, {"X1": "111円", "X3": "999円"})
        self.assertEqual(got2, "aは111円、bは0円、cは999円である")

    def test_5_alignment_guard_fires_when_the_text_drifts(self):
        with self.assertRaises(AssertionError):
            MK.check_alignment("aは1円である", [{"id": "X1", "text": "2円"}])
        with self.assertRaises(AssertionError):
            MK.check_alignment("aは1円、bは2円である", [{"id": "X1", "text": "1円"}])


class MakeRecordTest(unittest.TestCase):
    def setUp(self):
        self.r = load(MAKE)

    def test_6_eight_errors_two_per_type_balanced_by_stratum(self):
        self.assertEqual(self.r["植えた件数"], 8)
        self.assertEqual(self.r["型ごとの件数"],
                         {"I-1": 2, "I-2": 2, "II-1": 2, "II-2": 2})
        self.assertEqual(self.r["層ごとの件数"],
                         {"結べた": 4, "結べなかった": 4})
        self.assertEqual(self.r["作れなかった組み合わせ"], [])

    def test_7_one_error_per_sentence_and_17_is_skipped(self):
        sents = [p["文"] for p in self.r["植えた誤り"]]
        self.assertEqual(len(sents), len(set(sents)), "同じ文に 2 件入れない")
        self.assertNotIn(17, sents, "文 17 は罠が在るので使わない")
        self.assertEqual(self.r["使った文"], sorted(set(sents)))
        self.assertIn("R035", self.r["**文 17 を使わない理由**"])

    def test_8_the_gold_label_is_the_pre_change_row(self):
        gold = {x["id"]: x for x in load(GOLD)["rows"]}
        for p in self.r["植えた誤り"]:
            self.assertEqual(p["正しい参照先(改変前)"], gold[p["id"]]["正解"],
                             p["id"])
            self.assertEqual(p["元の値"], gold[p["id"]]["値"], p["id"])
            self.assertNotEqual(p["植えた値"], p["元の値"], p["id"])
        self.assertIn("Core の判定規則を使っていない",
                      self.r["正解ラベルの出どころ"])
        self.assertIn("層化", self.r["層化の開示"])

    def test_9_stratum_matches_the_frozen_core_result(self):
        bn = {b["claim_id"]: b for b in load(BINDS)["binds_new"]}
        for p in self.r["植えた誤り"]:
            self.assertEqual(p["Core が結べた主張か"],
                             bn[p["id"]]["state"] == "GROUNDED", p["id"])

    def test_10_group_two_values_exist_in_the_source_group_one_do_not(self):
        import importlib
        opp = _mod("opp_for_errtest", "sheet_m9_opportunity_2026-10-16.py")
        mat = load(os.path.join(FX, "m11_material_2026-10-16.json"))
        cells = opp.cells_of(opp.extract_of(mat))
        vals = {c["value"] for c in cells}
        for p in self.r["植えた誤り"]:
            if p["群"] == "群 II":
                self.assertIn(p["植えた値"], vals, "%s は原資料に在る値" % p["id"])
            else:
                self.assertNotIn(p["植えた値"], vals,
                                 "%s は原資料に無い値" % p["id"])


class ClassifyTest(unittest.TestCase):
    """**検出 / 保留 / 確認済みは排他。**壊した状態で 1 本ずつ当てる。"""

    def test_11_three_exclusive_buckets(self):
        self.assertEqual(CO.classify({"state": "GROUNDED"}), "確認済み")
        self.assertEqual(CO.classify({"state": "VALUE_MISMATCH"}), "検出")
        self.assertEqual(CO.classify({"state": "UNVERIFIABLE"}), "保留")
        self.assertEqual(CO.classify({"state": "POINTER_NOT_FOUND"}), "保留")

    def test_12_core_can_only_say_one_kind(self):
        self.assertEqual(CO.kind_of_core({"state": "VALUE_MISMATCH"}),
                         "値が原資料に無い")
        for st in ("GROUNDED", "UNVERIFIABLE", "POINTER_NOT_FOUND"):
            self.assertEqual(CO.kind_of_core({"state": st}), "不明")
        self.assertEqual(len(CO.VOCAB), 6, "固定語彙は 6 語")

    def test_13_variant_guard_catches_a_drifting_claim(self):
        c0 = [{"id": "X1", "sentence_index": 1, "value": 1},
              {"id": "X2", "sentence_index": 1, "value": 2}]
        ok, why = CO.check_variant(
            [{"id": "X1", "sentence_index": 1, "value": 9},
             {"id": "X2", "sentence_index": 1, "value": 2}], c0, {"X1"})
        self.assertTrue(ok, why)
        # 変えていない方が動いた
        ok, why = CO.check_variant(
            [{"id": "X1", "sentence_index": 1, "value": 9},
             {"id": "X2", "sentence_index": 1, "value": 7}], c0, {"X1"})
        self.assertFalse(ok)
        self.assertIn("変えていない", why)
        # 変えたはずが変わっていない
        ok, why = CO.check_variant(c0, c0, {"X1"})
        self.assertFalse(ok)
        self.assertIn("変わっていない", why)
        # 件数・文が違う
        self.assertFalse(CO.check_variant(c0[:1], c0, {"X1"})[0])
        self.assertFalse(CO.check_variant(
            [{"id": "X1", "sentence_index": 2, "value": 9}, c0[1]],
            c0, {"X1"})[0])


class CoreResultTest(unittest.TestCase):
    def setUp(self):
        self.r = load(CORE)

    def test_14_it_passed_and_nothing_slipped_through(self):
        v = self.r["**判定(封 §3-4)**"]
        self.assertTrue(v["E-1 見落とし = 0 件"]["満たした"])
        self.assertEqual(v["E-1 見落とし = 0 件"]["実測"], 0)
        self.assertTrue(v["E-2 偽警報 ≦ 1 件"]["満たした"])
        self.assertTrue(v["E-3 結べた 4 件の誤りは全部検出"]["満たした"])
        self.assertEqual(self.r["合否"], "**合格**")

    def test_15_detection_is_bounded_by_binding(self):
        s = self.r["層ごと(結べた / 結べなかった)"]
        self.assertEqual(s["結べた"], {"検出": 4})
        self.assertEqual(s["結べなかった"], {"保留": 4})

    def test_16_each_type_has_one_detected_and_one_held(self):
        for kind, v in self.r["型ごと"].items():
            self.assertEqual(v, {"検出": 1, "保留": 1}, kind)

    def test_17_the_three_scores_are_separated(self):
        self.assertEqual(self.r["検出-2 正しい根拠を提示"]["件数"], 4)
        self.assertEqual(self.r["検出-3 種類を特定"]["件数"], 2)
        self.assertEqual(self.r["検出-3 種類を特定"]["ids"], ["R010", "R012"])

    def test_18_the_trap_is_a_false_alarm_at_the_document_level(self):
        t = self.r["罠(R035)"]
        self.assertEqual(t["1 件ずつの変種での答え"], ["検出"])
        self.assertEqual(t["束ねた変種での答え"], "検出")
        self.assertIn("検出率の分母に入れない", t["注"])

    def test_19_the_bundle_agrees_with_the_singles(self):
        c = self.r["**束ねた変種と 1 件ずつの食い違い**"]
        self.assertEqual(c["件数"], 0)
        self.assertIn("一致", c["判定"])

    def test_20_the_control_reproduced_stage_11(self):
        self.assertTrue(self.r["対照が段 11 の記録と一致"])
        self.assertIn("Core の優位性ではない", self.r["**B は参考群である**"])


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = load(CORE)

    def test_21_three_layers_and_the_reference_group_disclaimer(self):
        for k in ("# 第 1 層 判定", "# 第 2 層 観測", "# 第 3 層 解釈"):
            self.assertIn(k, self.t, k)
        head = self.t[:self.t.index("\n# 第 1 層")]
        self.assertIn("**この測定は参考群(B)である**", head)
        self.assertIn("**だからこの数で製品の結論を書かない。**", head)

    def test_22_the_numbers_match_the_record(self):
        b = sec(self.t, "## §1-1", "## §1-2")
        self.assertIn("**0 件** | **満たした**", b)
        c = sec(self.t, "## §1-2", "# 第 2 層")
        self.assertIn("**完全に層で分かれた。**", c)
        self.assertEqual(self.r["層ごと(結べた / 結べなかった)"]["結べた"],
                         {"検出": 4})
        d = sec(self.t, "## §2-2", "## §2-3")
        self.assertIn("**検出-3 誤りの種類を特定できた** | **2 件**", d)
        self.assertIn("**顧客に渡せる情報の粒度はここで止まる**", d)

    def test_23_the_trap_is_not_counted_as_a_win(self):
        b = sec(self.t, "## §2-4", "## §2-5")
        self.assertIn("**報告文は正しい**", b)
        self.assertIn("罠を入れると 1/27 である。**", b)
        self.assertIn("**「検出できた」とは書かない**", b)

    def test_24_the_miss_and_its_direction_are_recorded(self):
        b = sec(self.t, "## §2-6", "# 第 3 層")
        ids = re.findall(r"(?m)^\| F-(\d) ", b)
        self.assertEqual(ids, [str(i) for i in range(1, 9)], "F-1〜F-8")
        self.assertEqual(b.count("**外れ**"), 1, "外れは 1 本")
        self.assertIn("**外れた 1 本(F-5)は「Core を低く見ていた」向きである。**", b)
        self.assertIn("**向きが逆の外れとして記録する**", b)

    def test_25_what_it_cannot_say(self):
        b = sec(self.t, "## §3-2", "## §3-3")
        self.assertIn("**人工の誤りである。**", b)
        self.assertIn("**保留 14〜17 件の実務的な重さは測っていない。**", b)
        self.assertIn("**検証器の精度は切り出しの精度で上から抑えられる。**", b)
        n = sec(self.t, "## §3-3")
        self.assertIn("**実行には人間の許可が要る。**", n)
        self.assertIn("見込み 2 USD(保証値ではない)", n)
        self.assertIn("**両方でなければ「上回った」と書かない**", n)


if __name__ == "__main__":
    unittest.main()
