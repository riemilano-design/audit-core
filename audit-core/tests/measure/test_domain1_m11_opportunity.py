# -*- coding: utf-8 -*-
"""段 11 の機会(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §11 の 3)を固定する。

守るのは 8 つ。
  1. **O-1〜O-7 は段 9 の script の字のまま**(sha が動いていない)
  2. 記録の O-1〜O-7 が**その場で数え直した数と一致する**
  3. **O-2 > 0**(③の発火機会が材料に在る)。会計ごとの内訳が別名の形で在る
  4. **O-8 > 0**(X-2 の機会が在る) ― X-2 = 0 を「結べなかった」と読まないため
  5. **O-8 は別名表を両側に当てて数えている**(片側だけにすると数が跳ねる歯)
  6. **新 engine の未確認が 0 件**であること(封 §3 の構造の事実)
  7. 記録に「**0 件は安全性の証明にしない**」が在ること
  8. **機会を見て標本を選び直さないと書いてあること**
"""
import hashlib
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "m11_opportunity_2026-10-16.json")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
OPP9_SHA = "eace3e1bbd2c480b"


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class CountsComeFromStage9Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11opp_t", "sheet_m11_opportunity_2026-10-16.py")
        cls.rec = load(REC)

    def test_1_the_frozen_counter_is_unchanged(self):
        p = os.path.join(MEASURE, "sheet_m9_opportunity_2026-10-16.py")
        with io.open(p, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], OPP9_SHA)
        self.assertIn("sheet_m9_opportunity_2026-10-16.py",
                      self.rec["O-1〜O-7 の出どころ"])
        self.assertIn("数え方を書き直していない", self.rec["O-1〜O-7 の出どころ"])

    def test_2_o1_matches_a_fresh_count(self):
        cells = self.m.OPP.cells_of(self.m.OPP.extract_of(load(MAT)))
        self.assertEqual(len(cells), self.rec["O-1 抜粋の値のセル"])
        self.assertEqual(len(cells), load(MAT)["value_cells"])

    def test_3_o2_has_opportunity_and_is_printed_as_an_alias(self):
        self.assertGreater(self.rec["O-2 ③が発火し得るセル(会計が未確認の別名)"], 0,
                           "③の発火機会が材料に無い")
        by = self.rec["O-2 の会計ごとの内訳"]
        self.assertGreaterEqual(len(by), 1)
        for name in by:
            self.assertTrue(name.startswith("東京都"),
                            "O-2 の会計が別名の形で載っていない: %s" % name)


class X2OpportunityTest(unittest.TestCase):
    """**O-8。**X-2 = 0 を「engine が結べなかった」と読まないための数(封 §4)。"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11opp_t2", "sheet_m11_opportunity_2026-10-16.py")
        cls.rec = load(REC)
        cls.o8 = cls.rec["O-8 X-2 の機会(新。封 §4)"]

    def test_4_there_are_rows_outside_the_extract(self):
        self.assertGreater(self.o8["O-8 索引に在って抜粋に無い行"], 0,
                           "抜粋の外に結べる先が無い ― X-2 の機会が無い")
        self.assertGreater(self.o8["O-8′ 抜粋に無い行だけが持つ値"], 0)
        self.assertGreater(self.o8["索引の行"], self.o8["抜粋の行"])

    def test_5_the_fold_is_applied_to_both_sides(self):
        """**歯**: 別名表を片側だけにすると O-8 が跳ねる(封 §4 の非対称の罠)。"""
        cells = self.m.OPP.cells_of(self.m.OPP.extract_of(load(MAT)))
        books = {}
        for f in (self.m.M2.SOUKATU, self.m.M2.KESSAN, self.m.M2.MEISAI):
            books[f], _ = self.m.M2.M1.read(os.path.join(self.m.M2.CACHE, f))
        args = (self.m.M2.parse_soukatu(books[self.m.M2.SOUKATU]),
                self.m.M2.parse_kessan(books[self.m.M2.KESSAN]),
                self.m.M2.parse_meisai(books[self.m.M2.MEISAI]))
        raw = self.m.E.fix_total_level(self.m.E.build_index(*args))
        al = self.m.SE.alias_table(raw)
        ents = self.m.E.canonicalize(raw, al)
        fold = self.m.alias_fold(al["table"])
        self.assertGreater(len(fold), 0, "別名表が空")
        sym = self.m.x2_opportunity(cells, ents, fold)
        asym = self.m.x2_opportunity(cells, ents, {})     # **片側だけ畳まない**
        self.assertEqual(sym["O-8 索引に在って抜粋に無い行"],
                         self.o8["O-8 索引に在って抜粋に無い行"])
        self.assertGreater(asym["O-8 索引に在って抜粋に無い行"],
                           sym["O-8 索引に在って抜粋に無い行"],
                           "**片側だけ畳んでも数が変わらない ― 歯が無い**")

    def test_6_an_empty_index_has_no_opportunity(self):
        """**歯**: 退化値。索引が空なら O-8 = 0。"""
        cells = self.m.OPP.cells_of(self.m.OPP.extract_of(load(MAT)))
        out = self.m.x2_opportunity(cells, [], {})
        self.assertEqual(out["O-8 索引に在って抜粋に無い行"], 0)
        self.assertEqual(out["O-8′ 抜粋に無い行だけが持つ値"], 0)

    def test_7_key4_folds_the_scope_on_both_sides(self):
        f = {"東京都と場会計": "と場会計"}
        a = self.m.key4("東京都と場会計", "目", "と場費 > と場管理費", "管理費", f)
        b = self.m.key4("と場会計", "目", "と場費 > と場管理費", "管理費", f)
        self.assertEqual(a, b, "別名と正本が同じ鍵にならない")
        c = self.m.key4("東京都と場会計", "目", "と場費 > と場管理費", "管理費", {})
        self.assertNotEqual(a, c, "畳まなくても同じ鍵になる ― 歯が無い")


class StructuralFactsAndDisclosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)

    def test_8_the_new_engine_has_no_unconfirmed_alias(self):
        a = self.rec["別名表"]
        self.assertEqual(a["未確認のまま"], 0,
                         "新 engine に未確認の別名が残っている(封 §3 の前提が崩れる)")
        self.assertEqual(a["歳入で昇格した"], 18)
        self.assertIn("A-1・A-3 は構造的に 0", a["注"])
        self.assertIn("旧 engine でしか観測できない", a["注"])

    def test_9_zero_is_not_evidence_of_safety(self):
        joined = "\n".join(self.rec["limit"])
        self.assertIn("機会は在ったが発火しなかった", joined)
        self.assertIn("安全性の証明にしない", joined)
        self.assertIn("片側だけ畳むと", joined)

    def test_10_the_sample_is_not_reselected(self):
        self.assertIn("表を増やしたり減らしたりしない", self.rec["will_not_reselect"])
        self.assertIn("標本を選び直さない", self.rec["will_not_reselect"])
        self.assertTrue(self.rec["not_a_pass_condition"])


if __name__ == "__main__":
    unittest.main()
