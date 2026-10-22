# -*- coding: utf-8 -*-
"""C′・C″ の合成規則を固定する(封 docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md §1)。

**規則の性質を全組み合わせで当てる**(席 3 値 × 検証器 4 値 + None = 15 通り)。
"""
import ast
import importlib.util
import io
import itertools
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PATH = os.path.join(ROOT, "measure", "sheet_errdet_cprime_2026-10-19.py")


def _mod():
    sp = importlib.util.spec_from_file_location("cprime_under_test", PATH)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


M = _mod()
ALL = list(itertools.product(M.SEAT_KINDS, list(M.VERIFIER_OUTS) + [None]))


class RuleTest(unittest.TestCase):
    def test_1_every_combination_lands_on_one_of_the_eight_rows(self):
        rows = set()
        for sk, vo in ALL:
            st, row, note = M.compose_cprime(sk, vo)
            self.assertIn(row, range(1, 9), (sk, vo))
            self.assertIn(st, M.SEAT_KINDS)
            rows.add(row)
        self.assertEqual(rows, set(range(1, 9)), "8 行のどれかが一度も出ない")

    def test_2_the_verifier_never_lowers_the_seats_suspicion(self):
        for sk, vo in ALL:
            st, _r, _n = M.compose_cprime(sk, vo)
            self.assertGreaterEqual(M.SUSPICION[st], M.SUSPICION[sk], (sk, vo, st))

    def test_3_a_seat_detection_stays_a_detection_whatever_the_verifier_says(self):
        for vo in list(M.VERIFIER_OUTS) + [None]:
            st, row, _n = M.compose_cprime("検出", vo)
            self.assertEqual(st, "検出", vo)
            self.assertIn(row, (1, 2, 3, 4), vo)

    def test_4_the_verifier_moves_only_a_confirmed_seat(self):
        self.assertEqual(M.compose_cprime("確認済み", "確認済み")[:2], ("確認済み", 6))
        self.assertEqual(M.compose_cprime("確認済み", "原資料と一致しない")[:2], ("検出", 7))
        for vo in ("確認できない(参照先が無い)", "確認できない(値が一意でない)"):
            self.assertEqual(M.compose_cprime("確認済み", vo)[:2], ("保留", 8), vo)

    def test_5_a_hold_is_inherited(self):
        for vo in list(M.VERIFIER_OUTS) + [None]:
            self.assertEqual(M.compose_cprime("保留", vo)[:2], ("保留", 5), vo)

    def test_6_row_one_is_the_origin_confirmed_case(self):
        self.assertEqual(M.compose_cprime("検出", "確認済み"), ("検出", 1, "出どころ確認済み"))

    def test_7_unknown_inputs_raise(self):
        with self.assertRaises(ValueError):
            M.compose_cprime("合格", "確認済み")
        with self.assertRaises(ValueError):
            M.compose_cprime("検出", "VALID")

    def test_8_kind_follows_the_seal(self):
        for row in (1, 2, 3, 4):
            self.assertEqual(M.kind_of_cprime(row, "列の取り違え"), "列の取り違え")
        self.assertEqual(M.kind_of_cprime(7, "列の取り違え"), "値が原資料に無い")
        for row in (5, 6, 8):
            self.assertEqual(M.kind_of_cprime(row, "列の取り違え"), "不明")

    def test_9_c_double_prime_moves_state_only_on_core_mismatch_of_a_confirmed_seat(self):
        for row in range(1, 9):
            for st in M.SEAT_KINDS:
                for b in ("GROUNDED", "VALUE_MISMATCH", "UNVERIFIABLE", "POINTER_NOT_FOUND"):
                    out, _n = M.compose_cdouble(st, row, b)
                    if row in (6, 8) and b == "VALUE_MISMATCH":
                        self.assertEqual(out, "検出", (row, st, b))
                    else:
                        self.assertEqual(out, st, (row, st, b))

    def test_10_verdict_word_is_tri_state(self):
        self.assertEqual(M.verdict_word(True), "当たり")
        self.assertEqual(M.verdict_word(False), "外れ")
        self.assertEqual(M.verdict_word(None), "未測定")
        for bad in (1, 0, "", [], "yes"):
            with self.assertRaises(ValueError):
                M.verdict_word(bad)


class ImportNotRewriteTest(unittest.TestCase):
    def test_11_the_scoring_functions_are_imported_not_rewritten(self):
        with io.open(PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for forbidden in ("classify_seat", "verify", "reach", "same_row", "resolve",
                          "ref_of", "run_core", "six"):
            self.assertNotIn(forbidden, names, forbidden)
        self.assertTrue(M.SC.classify_seat.__code__.co_filename.endswith(
            "sheet_errdet_score_2026-10-17.py"))
        self.assertTrue(M.CO.ref_of.__code__.co_filename.endswith(
            "sheet_errdet_core_2026-10-17.py"))


if __name__ == "__main__":
    unittest.main()
