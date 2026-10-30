# -*- coding: utf-8 -*-
"""誤りを通す率の道具(``measure/false_pass_2026-10-14.py``)の試験。

この道具は**人間に渡す数そのもの**を作る(「誤りを通す率」)。2026-10-14 に
測り方の欠陥を 2 つ出した ― (1) 変え方を行の順番で割り振ったので profile 間で
同じ行に違う変え方が当たった、(2) 1 行に 1 通りだけ当てたので、限界の型
(丸めの帯の中)が割り当て次第で標本から外れた。どちらも**数を読み違える**欠陥で、
出力を見ても分からない。ここで字で留める。

実物の書類は読まない(合成の文字列だけ)。通信しない。
"""

import importlib.util
import os
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_TOOL = os.path.join(_AUDIT_CORE, "measure", "false_pass_2026-10-14.py")


def _tool_source():
    with open(_TOOL, encoding="utf-8") as fh:
        return fh.read()


def _load():
    spec = importlib.util.spec_from_file_location("false_pass_tool", _TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FP = _load()


class MutationKindTest(unittest.TestCase):
    """欠陥 (1) の留め: 変え方は **claim の id だけ**で決まる(並び順・profile に依らない)。"""

    def test_kind_depends_only_on_the_id(self):
        self.assertEqual(FP.mutation_kind("N002"), FP.mutation_kind("N002"))
        self.assertEqual(FP.mutation_kind("N002"), "V1")
        self.assertEqual(FP.mutation_kind("N003"), "V2")
        self.assertEqual(FP.mutation_kind("T010"), "V1")
        self.assertEqual(FP.mutation_kind("T011"), "V2")

    def test_both_kinds_occur(self):
        kinds = {FP.mutation_kind("N%03d" % i) for i in range(1, 50)}
        self.assertEqual(kinds, {"V1", "V2"})

    def test_run_doc_takes_a_fixed_kind(self):
        # 欠陥 (2) の留め: 既定で両方の変え方を当てられるよう、kind は引数で受ける。
        import inspect
        self.assertIn("kind", inspect.signature(FP.run_doc).parameters)
        src = _tool_source()
        self.assertIn('kinds = ["V1", "V2"]', src)        # 既定は両方
        self.assertIn('how = kind or mutation_kind(', src)


class MutateTest(unittest.TestCase):
    def test_v1_multiplies_by_ten_keeping_separators(self):
        self.assertEqual(FP.mutate("2,523,449", "V1"), "25,234,490")
        self.assertEqual(FP.mutate("186", "V1"), "1860")
        self.assertEqual(FP.mutate("2.3", "V1"), "23")
        self.assertEqual(FP.mutate("27.65", "V1"), "276.5")

    def test_v2_changes_the_last_digit_by_one(self):
        self.assertEqual(FP.mutate("275,052", "V2"), "275,053")
        self.assertEqual(FP.mutate("2.3", "V2"), "2.4")
        self.assertEqual(FP.mutate("18.9", "V2"), "18.8")   # 9 は 8 へ
        self.assertEqual(FP.mutate("190", "V2"), "191")

    def test_mutation_always_changes_the_text(self):
        for raw in ("2,523,449", "2.3", "18.9", "100", "0.5"):
            for how in ("V1", "V2"):
                self.assertNotEqual(FP.mutate(raw, how), raw, (raw, how))

    def test_unit_and_sign_are_kept(self):
        self.assertEqual(FP.mutate("△1,234", "V2"), "△1,235")
        self.assertEqual(FP.mutate("1,234千円", "V2"), "1,235千円")

    def test_a_text_without_digits_is_not_mutable(self):
        self.assertIsNone(FP.mutate("千円", "V1"))
        self.assertIsNone(FP.mutate("", "V2"))


class DigitsPartTest(unittest.TestCase):
    def test_splits_prefix_digits_suffix(self):
        self.assertEqual(FP._digits_part("△1,234千円"), ("△", "1,234", "千円"))
        self.assertEqual(FP._digits_part("2.3%"), ("", "2.3", "%"))
        self.assertEqual(FP._digits_part("186"), ("", "186", ""))


class ExpectedValueTest(unittest.TestCase):
    """変えた後の値が 1 通りに読めない行は、通した件数に数えない(``id_shift``)。"""

    def test_single_number_gives_its_value(self):
        self.assertEqual(FP.expected_value({"raw": "2.3%"}, "2.4%"), 2.4)
        self.assertEqual(FP.expected_value({"raw": "1,234千円"}, "1,235千円"), 1235.0)

    def test_text_with_two_numbers_is_none(self):
        self.assertIsNone(FP.expected_value({"raw": "x"}, "1,235千円 と 2.4%"))


class OutcomeVocabularyTest(unittest.TestCase):
    """「通した」の字は 1 つだけ(集計が静かに変わらないように)。"""

    def test_passed_and_detected_spellings_are_pinned(self):
        src = _tool_source()
        self.assertIn('outcome = "PASSED"', src)
        self.assertIn('outcome = "detected:" + c["state"]', src)
        self.assertIn('outcome = "id_shift"', src)
        self.assertIn('outcome = "missing"', src)
