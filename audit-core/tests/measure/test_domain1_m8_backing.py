# -*- coding: utf-8 -*-
"""段 8 の裏づけ B-1〜B-5(封 §2)を固定する。**材料を作る前に赤くなる門。**

守るのは 5 つ。
  1. B-2 / B-5 の連番の判定が**1 つ欠けても False** になること
  2. 3 本そろわない項を**落とす**(推測で補完しない)こと
  3. **未確認の別名の会計は B-3 が成立しない**こと(同じ会計だと確かめられない file を数えない)
  4. 目の裏づけが **2 本**であり、項の 3 本と**同じ強さとして扱わない**と書いてあること
  5. 実測の数(72 / 2 / 20 / 365)が元資料から出ること
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "measure", "sheet_parent_backing_2026-10-16.py")
REC = os.path.join(ROOT, "fixtures", "sheet", "parent_backing_2026-10-16.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M8_SEAL_2026-10-16.md")

spec = importlib.util.spec_from_file_location("backing8", SRC)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class SequenceTest(unittest.TestCase):
    def test_a_restarting_sequence_is_accepted(self):
        self.assertTrue(B._is_restarting_sequence(["01", "02", "03"]))
        self.assertTrue(B._is_restarting_sequence(["01"]))

    def test_a_gap_is_refused(self):
        self.assertFalse(B._is_restarting_sequence(["01", "03"]))

    def test_not_starting_at_one_is_refused(self):
        self.assertFalse(B._is_restarting_sequence(["02", "03"]))

    def test_out_of_order_is_refused(self):
        self.assertFalse(B._is_restarting_sequence(["02", "01"]))

    def test_a_missing_code_is_refused(self):
        self.assertFalse(B._is_restarting_sequence(["01", None]))
        self.assertFalse(B._is_restarting_sequence([]))

    def test_a_non_numeric_code_is_refused(self):
        self.assertFalse(B._is_restarting_sequence(["01", "0x"]))


class EquivalenceTest(unittest.TestCase):
    """変異 J2(`all(codes)` を外す)が黙った理由を**証明して留める**。

    `all(codes)` を外しても `int(None)` が TypeError を投げ、
    同じ except で False になる。**等価であって、試験の穴ではない。**
    欠けたコードを「連番」と数える経路は作れないことを、入力の形で示す。
    """

    def test_a_none_code_is_refused_with_or_without_the_all_guard(self):
        self.assertFalse(B._is_restarting_sequence(["01", None]))
        self.assertFalse(B._is_restarting_sequence([None]))
        self.assertFalse(B._is_restarting_sequence(["01", ""]))

    def test_the_guard_and_the_except_refuse_the_same_inputs(self):
        def without_all_guard(codes):
            if not codes:
                return False
            try:
                nums = [int(x) for x in codes]
            except (TypeError, ValueError):
                return False
            return nums == list(range(1, len(nums) + 1))
        for codes in ([], ["01"], ["01", "02"], ["01", None], [None],
                      ["01", ""], ["02"], ["01", "03"], ["0x"]):
            self.assertEqual(B._is_restarting_sequence(codes),
                             without_all_guard(codes), codes)


class KouBackingTest(unittest.TestCase):
    """手で作った小さな表で、**3 本の要求**を 1 本ずつ外して確かめる。"""

    def _kessan(self, items=None, kan=None):
        return {"blocks": [{"account": "一般会計",
                            "kan": kan or [{"row": 10, "name": "総務費", "code": "02"}],
                            "items": items or [{"row": 11, "name": "区市町村振興費",
                                                "code": "01", "parent_row": 10}]}]}

    def _meisai(self, kan_name="総務費", acc="一般会計", item="区市町村振興費"):
        return {"sheets": [{"account": acc, "sheet": "s1",
                            "kan": [{"row": 5, "name": kan_name, "code": "02"}],
                            "items": [{"row": 6, "name": item, "code": "01"}],
                            "moku": []}]}

    def test_all_three_present_passes(self):
        ok, why, _ = B.kou_parents(self._kessan(), self._meisai())
        self.assertEqual(list(ok.values()), ["総務費"])
        self.assertEqual(why, {})

    def test_b2_fails_when_the_code_does_not_start_at_01(self):
        items = [{"row": 11, "name": "区市町村振興費", "code": "02", "parent_row": 10}]
        ok, why, _ = B.kou_parents(self._kessan(items), self._meisai())
        self.assertEqual(ok, {})
        self.assertIn("B-2 コードが 01 からの連番でない", why)

    def test_b1_fails_when_no_kan_is_above(self):
        items = [{"row": 11, "name": "区市町村振興費", "code": "01", "parent_row": None}]
        ok, why, _ = B.kou_parents(self._kessan(items), self._meisai())
        self.assertEqual(ok, {})
        self.assertIn("B-1 款の行が上に無い", why)

    def test_b3_fails_when_the_meisai_has_no_matching_kou(self):
        ok, why, _ = B.kou_parents(self._kessan(), self._meisai(item="別の項"))
        self.assertEqual(ok, {})
        self.assertIn("B-3 明細に対応する項が無い", why)

    def test_b3_fails_when_the_two_files_disagree(self):
        ok, why, _ = B.kou_parents(self._kessan(), self._meisai(kan_name="教育費"))
        self.assertEqual(ok, {})
        self.assertIn("B-3 明細と決算書で款が食い違う", why)

    def test_b3_fails_when_the_meisai_offers_two_kan(self):
        m = self._meisai()
        m["sheets"].append({"account": "一般会計", "sheet": "s2",
                            "kan": [{"row": 5, "name": "教育費", "code": "03"}],
                            "items": [{"row": 6, "name": "区市町村振興費", "code": "01"}],
                            "moku": []})
        ok, why, _ = B.kou_parents(self._kessan(), m)
        self.assertEqual(ok, {})
        self.assertIn("B-3 明細の款が 2 通り以上", why)

    def test_an_unconfirmed_alias_account_cannot_provide_b3(self):
        """**同じ会計だと確かめられない file を 2 本目に数えない。**"""
        m = self._meisai(acc="東京都一般会計")
        ok, why, _ = B.kou_parents(self._kessan(), m, alias={})
        self.assertEqual(ok, {})
        self.assertIn("B-3 明細に対応する項が無い", why)

    def test_a_confirmed_alias_account_does_provide_b3(self):
        m = self._meisai(acc="東京都一般会計")
        alias = {"東京都一般会計": {"canonical": "一般会計"}}
        ok, _, _ = B.kou_parents(self._kessan(), m, alias=alias)
        self.assertEqual(list(ok.values()), ["総務費"])

    def test_the_same_kou_name_under_two_kan_is_dropped(self):
        kan = [{"row": 10, "name": "総務費", "code": "02"},
               {"row": 20, "name": "教育費", "code": "03"}]
        items = [{"row": 11, "name": "施設整備費", "code": "01", "parent_row": 10},
                 {"row": 21, "name": "施設整備費", "code": "01", "parent_row": 20}]
        ok, why, detail = B.kou_parents(self._kessan(items, kan),
                                        self._meisai(item="施設整備費"))
        self.assertEqual(ok, {})
        self.assertIn("B-1 決算書の中で款が 2 通り", why)
        self.assertTrue(detail)


class MokuBackingTest(unittest.TestCase):
    def _meisai(self, moku=None, items=None):
        return {"sheets": [{"account": "一般会計", "sheet": "s1",
                            "kan": [{"row": 5, "name": "教育費", "code": "09"}],
                            "items": items or [{"row": 6, "name": "高等学校費",
                                                "code": "01"}],
                            "moku": moku or [{"row": 7, "name": "管理費",
                                              "code": "01"}]}]}

    def test_two_backings_pass(self):
        ok, why = B.moku_parents(self._meisai())
        self.assertEqual(list(ok.values()), [("教育費", "高等学校費")])
        self.assertEqual(why, {})

    def test_b5_fails_when_the_code_does_not_start_at_01(self):
        ok, why = B.moku_parents(self._meisai(moku=[{"row": 7, "name": "管理費",
                                                     "code": "02"}]))
        self.assertEqual(ok, {})
        self.assertIn("B-5 コードが 01 からの連番でない", why)

    def test_b4_fails_without_a_kou_above(self):
        m = self._meisai()
        m["sheets"][0]["items"] = []
        ok, why = B.moku_parents(m)
        self.assertEqual(ok, {})
        self.assertIn("B-4 款か項の行が上に無い", why)

    def test_the_record_says_the_moku_has_one_backing_fewer(self):
        r = load(REC)
        self.assertEqual(len(r["backings"]["項"]), 3)
        self.assertEqual(len(r["backings"]["目"]), 2)
        self.assertIn("**この差を同じ強さの根拠として扱わない。**", r["note"])
        self.assertIn("**この差を「同じ強さの根拠」として扱わない。**", text(SEAL))


class MeasuredTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)

    def test_the_counts_match_the_seal(self):
        self.assertEqual(self.r["項の款名_3本そろった"], 72)
        self.assertEqual(self.r["項の款名_一般会計で成立"], 72)
        self.assertEqual(self.r["項の款名_落ちた理由"]
                         ["B-3 明細に対応する項が無い"], 20)
        self.assertEqual(self.r["項の款名_落ちた理由"]
                         ["B-1 決算書の中で款が 2 通り"], 2)
        self.assertEqual(self.r["目の親_2本そろった"], 365)
        s = text(SEAL)
        self.assertIn("| **3 本そろう(B-1 = B-3、候補 1 通り)** | **72** |", s)
        self.assertIn("| 明細に対応する項が無い | **20** |", s)

    def test_only_the_confirmed_alias_is_used(self):
        self.assertEqual(self.r["別名_裏づけの通った会計"], ["東京都一般会計"])

    def test_the_index_parent_rule_was_not_changed(self):
        """この file は**索引の親の決め方を変えない**。"""
        src = text(SRC)
        self.assertIn("**索引の親の決め方を変えない**", src)
        self.assertIn("決めるのは「**材料に書いてよいか**」だけである", src)
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out)


if __name__ == "__main__":
    unittest.main()
