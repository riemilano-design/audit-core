# -*- coding: utf-8 -*-
"""方式 C の材料(measure/sheet_poc_c_material_2026-10-17.py)を固定する。

**生成の前に赤くなる門。**守るのは
  * **A が 1 文字も変わらず接頭**になっていること(偽なら実験は無効)
  * **指示の字は封から取る**(手で写していない ― 封を変えれば材料も変わる)
  * **言い換えは内部の状態名を書かない**。知らない状態が来たら**止まる**
  * **候補の列挙は 8 通りまで**(人が決めた数)
  * **禁じ語を当てる**(壊した字で赤になる)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "poc_c_material_2026-10-17.json")
LAB11 = os.path.join(FX, "m11_label_material_2026-10-16.json")
BINDS = os.path.join(FX, "m11_binds_2026-10-16.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_POC_C_SEAL_2026-10-17.md")


def _mod(name, rel):
    sp = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "measure", rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


M = _mod("c_material_for_test", "sheet_poc_c_material_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)

    def test_1_a_is_a_prefix_and_the_sizes_add_up(self):
        for f in self.r["files"]:
            self.assertTrue(f["A が接頭"], f["seat"])
            self.assertEqual(f["C の字数"] - f["A の字数"], f["足した字数"])
            self.assertGreater(f["足した字数"], 0)

    def test_2_the_a_side_is_identical_to_stage_11(self):
        want = {f["seat"]: f["chars"] for f in load(LAB11)["files"]}
        for f in self.r["files"]:
            self.assertEqual(f["A の字数"], want[f["seat"]],
                             "**A が段 11 と違う(%s)**" % f["seat"])

    def test_3_same_models_and_orders_as_stage_11(self):
        want = {s["seat"]: (s["model"], s["order"])
                for s in load(LAB11)["seats"]}
        for f in self.r["files"]:
            self.assertEqual((f["model"], f["order"]), want[f["seat"]])
        ids = [c["id"] for c in load(BINDS)["claims"] if not c.get("skipped")]
        by = {f["seat"]: f for f in self.r["files"]}
        self.assertEqual(by["seat1"]["先頭の id"], ids[0])
        self.assertEqual(by["seat2"]["先頭の id"], ids[-1])

    def test_4_evidence_comes_from_b_not_from_the_scope_experiment(self):
        self.assertIn("binds_new", self.r["証拠の出どころ"])
        self.assertTrue(self.r["**B′(抜粋 76 行)は使っていない**"])
        self.assertTrue(self.r["再現が段 11 の記録と一致"])
        self.assertIn("候補範囲実験の結果", self.r["足していないもの"])
        self.assertIn("A の答え", self.r["足していないもの"])

    def test_5_the_listing_cap_is_eight_and_the_split_is_recorded(self):
        self.assertEqual(self.r["上限"], 8)
        self.assertEqual(M.MAX_LISTED_KEYS, 8)
        key = "鍵を並べなかった件(上限 8 通り超え)"
        self.assertEqual(self.r[key]["件数"], len(self.r[key]["ids"]))
        self.assertEqual(self.r["鍵を並べた件"]["件数"],
                         len(self.r["鍵を並べた件"]["ids"]))

    def test_6_the_instruction_is_taken_from_the_seal(self):
        self.assertEqual(self.r["(C) の指示"], M.instruction_from_seal())


class InstructionIsNotHardcodedTest(unittest.TestCase):
    """**封を変えれば材料の字も変わる**ことを、壊した封で当てる。"""

    def test_7_a_doctored_seal_changes_the_instruction(self):
        t = io.open(SEAL, encoding="utf-8").read()
        i = t.index("\n### §2-4")
        j = t.index("\n### §2-5", i)
        body = t[i:j]
        self.assertIn("> ", body)
        doctored = t[:i] + body.replace(
            "> (A) と (B) だけで答えてもかまいません。",
            "> **道具の答えをそのまま写してください。**") + t[j:]
        p = os.path.join(os.path.dirname(REC), "_doctored_seal_for_test.md")
        try:
            io.open(p, "w", encoding="utf-8").write(doctored)
            got = M.instruction_from_seal(p)
        finally:
            if os.path.exists(p):
                os.remove(p)
        self.assertIn("道具の答えをそのまま写してください。", got)
        self.assertNotIn("**", got, "強調の印は外して渡す")
        self.assertNotEqual(got, M.instruction_from_seal())


class WordingTest(unittest.TestCase):
    """`say()` は**判定を 1 か所に置いた**ので、壊した入力で 1 本ずつ当てられる。"""

    def test_8_unknown_state_stops_the_material(self):
        with self.assertRaises(AssertionError):
            M.say({"state": "SOMETHING_NEW", "hold_reason": None}, [])
        with self.assertRaises(AssertionError):
            M.say({"state": "UNVERIFIABLE", "hold_reason": "知らない理由"}, [])

    def test_9_key_count_must_agree_with_the_reason(self):
        b = {"state": "UNVERIFIABLE",
             "hold_reason": "6 欄が一意でない(3 通り。値で選ばない)"}
        with self.assertRaises(AssertionError):
            M.say(b, [{"会計": "x", "階層": "款", "親": "", "科目名": "y",
                       "列": "予算現額", "値": [1], "位置": ["sheet:a!A1"]}])

    def test_10_value_mismatch_prints_the_rows_value(self):
        b = {"state": "VALUE_MISMATCH", "hold_reason": None,
             "recomputed": -48327000, "pointer": "sheet:明細!G51"}
        k = [{"会計": "と場会計", "階層": "目", "親": "と場事業費",
              "科目名": "運営費", "列": "補正予算額", "値": [-48327000],
              "位置": ["sheet:明細!G51"]}]
        head, lines = M.say(b, k)
        self.assertIn("その行の値は主張の金額と一致しない", head)
        self.assertIn("-48327000", head)
        self.assertIn("列=補正予算額", lines[0])

    def test_11_over_the_cap_the_keys_are_not_listed(self):
        n = M.MAX_LISTED_KEYS + 1
        b = {"state": "UNVERIFIABLE",
             "hold_reason": "6 欄が一意でない(%d 通り。値で選ばない)" % n}
        keys = [{"会計": "x", "階層": "款", "親": "", "科目名": "y%d" % i,
                 "列": "予算現額", "値": [i], "位置": ["sheet:a!A%d" % i]}
                for i in range(n)]
        head, lines = M.say(b, keys)
        self.assertIn("候補が %d 通り在り" % n, head)
        self.assertEqual(len(lines), 1)
        self.assertIn("並べていない", lines[0])
        for k in keys:
            self.assertNotIn(k["科目名"], "\n".join(lines))

    def test_12_at_the_cap_the_keys_are_listed(self):
        n = M.MAX_LISTED_KEYS
        b = {"state": "UNVERIFIABLE",
             "hold_reason": "6 欄が一意でない(%d 通り。値で選ばない)" % n}
        keys = [{"会計": "x", "階層": "款", "親": "", "科目名": "y%d" % i,
                 "列": "予算現額", "値": [i], "位置": ["sheet:a!A%d" % i]}
                for i in range(n)]
        head, lines = M.say(b, keys)
        body = "\n".join(lines)
        for k in keys:
            self.assertIn(k["科目名"], body)
        self.assertIn("候補1:", body)
        self.assertIn("候補%d:" % n, body)


class GuardTest(unittest.TestCase):
    def test_13_banned_words_are_caught(self):
        self.assertTrue(M.check_banned("ふつうの字"))
        for w in ("pointer", "GROUNDED", "正解", "封"):
            with self.assertRaises(AssertionError):
                M.check_banned("… %s …" % w)

    def test_14_prefix_guard_catches_a_changed_a(self):
        self.assertTrue(M.check_prefix("abc", "ab"))
        with self.assertRaises(AssertionError):
            M.check_prefix("Xbc", "ab")

    def test_15_the_banned_list_is_stage_11s(self):
        """**禁じ語を緩めていない**こと(封 §2-5)。"""
        lab = _mod("lab11_for_c_test",
                   "sheet_m11_label_material_2026-10-16.py")
        self.assertEqual(M.BANNED, lab.BANNED)
        self.assertEqual(load(REC)["banned_checked"], lab.BANNED)


if __name__ == "__main__":
    unittest.main()
