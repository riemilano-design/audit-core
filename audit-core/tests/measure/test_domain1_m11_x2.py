# -*- coding: utf-8 -*-
"""X-2 の計数器と歯(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §4・§4-1)を固定する。

守るのは 11 つ。
  1. 鍵の作り方を**1 か所しか持たない**(`key4` の所有者は機会の script)
  2. **対称**: 別名の字と正本の字が同じ鍵になる
  3. **非対称**: 段 9 の数え方では**偽の X-2 が出る**(実測)
  4. **三欄**: 会計を外すと別名表に依らない
  5. 結んでいない主張は数えない
  6. `verdict` の 3 つの枝(合格・不合格・**未測定**)が壊した入力で発火する
  7. 歯-1〜歯-3 の記録が**その場で当て直した数と一致する**
  8. 記録に「**engine の安全性を何も示さない**」が在ること
  9. 記録が**人工材料であると明記**していること
 10. **歯が 6 本すべて通っている**こと
 11. 歯-3 の結論(段 9 の数え方で偽の X-2)が記録に在ること
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
REC = os.path.join(FX, "m11_x2_teeth_2026-10-16.json")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


ALIAS = {"東京都と場会計": {"canonical": "と場会計"}}
CELLS = [{"scope": "と場会計", "level": "目", "parent": "と場費 > と場管理費",
          "name": "管理費", "column": "支出済額", "value": 100},
         {"scope": "一般会計", "level": "項", "parent": "総務費",
          "name": "総務管理費", "column": "支出済額", "value": 200}]


def bind(scope, level, parent, name, state="GROUNDED"):
    return {"state": state,
            "evidence": {"scope": scope, "level": level, "parent": parent,
                         "name": name}}


class CounterHasOneOwnerTest(unittest.TestCase):
    def setUp(self):
        self.x2 = _mod("x2_t", "sheet_m11_x2_2026-10-16.py")

    def test_1_key_is_not_reimplemented(self):
        self.assertIs(self.x2.key4, self.x2.OPP11.key4,
                      "鍵の作り方を 2 か所に持っている")
        self.assertIs(self.x2.alias_fold, self.x2.OPP11.alias_fold)


class SymmetryTest(unittest.TestCase):
    def setUp(self):
        self.x2 = _mod("x2_t2", "sheet_m11_x2_2026-10-16.py")

    def test_2_alias_and_canonical_agree_when_folded(self):
        out = self.x2.count(
            {"a": bind("と場会計", "目", "と場費 > と場管理費", "管理費")},
            CELLS, ALIAS)
        self.assertEqual(out["X-2対称"], 0, "正本で結んだのに抜粋に無いと数えた")
        self.assertEqual(out["X-1対称"], 1)

    def test_3_the_stage9_way_produces_a_false_x2(self):
        """**歯**: 抜粋が `東京都と場会計` でも、engine は正本で結ぶ。"""
        cells = [dict(CELLS[0], scope="東京都と場会計"), CELLS[1]]
        out = self.x2.count(
            {"a": bind("と場会計", "目", "と場費 > と場管理費", "管理費")},
            cells, ALIAS)
        self.assertEqual(out["X-2対称"], 0, "対称なら 0 件")
        self.assertEqual(out["X-2非対称"], 1,
                         "**段 9 の数え方で偽の X-2 が出ないなら、封 §4 の前提が崩れる**")
        self.assertEqual(out["X-2三欄"], 0, "会計を外せば 0 件")

    def test_4_three_fields_ignore_the_alias_table(self):
        cells = [dict(CELLS[0], scope="東京都と場会計"), CELLS[1]]
        a = self.x2.count(
            {"a": bind("と場会計", "目", "と場費 > と場管理費", "管理費")},
            cells, ALIAS)
        b = self.x2.count(
            {"a": bind("と場会計", "目", "と場費 > と場管理費", "管理費")},
            cells, {})
        self.assertEqual(a["X-2三欄"], b["X-2三欄"],
                         "三欄が別名表に依っている(裏取りにならない)")

    def test_5_a_row_outside_the_extract_is_counted(self):
        out = self.x2.count({"a": bind("と場会計", "目", "と場費 > と場管理費", "別の目")},
                            CELLS, ALIAS)
        self.assertEqual(out["X-2対称"], 1)
        self.assertEqual(out["X-2三欄"], 1)

    def test_6_unbound_claims_are_not_counted(self):
        for st in ("VALUE_MISMATCH", "POINTER_NOT_FOUND", "UNVERIFIABLE"):
            out = self.x2.count({"a": bind("と場会計", "目", "x", "別の目", st)},
                                CELLS, ALIAS)
            self.assertEqual(out["結んだ主張"], 0, st)
            self.assertEqual(out["X-2対称"], 0, st)


class VerdictTest(unittest.TestCase):
    """封 §6 の線。**正常な入力では 1 つの枝しか通らないので、壊した入力で当てる。**"""

    def setUp(self):
        self.x2 = _mod("x2_t3", "sheet_m11_x2_2026-10-16.py")

    def test_7_pass_fail_and_unmeasured(self):
        ok = self.x2.verdict({"結んだ主張": 5, "X-2対称": 0, "X-2三欄": 0,
                              "X-2非対称": 12})
        self.assertTrue(ok["合格"])
        self.assertIn("非対称 = 12 件は開示だけ", ok["理由"])
        for bad in ({"結んだ主張": 5, "X-2対称": 1, "X-2三欄": 0, "X-2非対称": 0},
                    {"結んだ主張": 5, "X-2対称": 0, "X-2三欄": 1, "X-2非対称": 0}):
            v = self.x2.verdict(bad)
            self.assertFalse(v["合格"], bad)
            self.assertIn("不合格", v["判定"])
        un = self.x2.verdict({"結んだ主張": 0, "X-2対称": 0, "X-2三欄": 0,
                              "X-2非対称": 0})
        self.assertFalse(un["合格"], "結んだ主張 0 件を合格にしてはいけない")
        self.assertIn("未測定", un["判定"])
        self.assertIn("合格の根拠に含めない", un["理由"])


class TeethRecordTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)
        cls.m = _mod("x2teeth_t", "sheet_m11_x2_teeth_2026-10-16.py")

    def test_8_all_six_teeth_bite(self):
        self.assertEqual(len(self.rec["検査"]), 6, "歯は 6 本")
        self.assertTrue(self.rec["すべて通ったか"], self.rec["落ちた検査"])
        self.assertEqual(self.rec["落ちた検査"], [])
        self.assertEqual(self.rec["歯-1"]["X-2対称"], 1)
        self.assertEqual(self.rec["歯-2"]["X-2対称"], 0)
        self.assertEqual(self.rec["歯-3"]["X-2対称"], 0)
        self.assertEqual(self.rec["歯-3"]["X-2非対称"], 1)
        self.assertEqual(self.rec["歯-3"]["X-2三欄"], 0)

    def test_9_the_record_is_reproduced_by_recounting(self):
        """**記録を読むだけにしない。**同じ行をその場で当て直す。"""
        x2 = self.m.X2
        mat = load(MAT)
        cells = self.m.OPP11.OPP.cells_of(self.m.OPP11.OPP.extract_of(mat))
        r1 = self.rec["歯-1 の行(抜粋に無い)"]
        got = x2.count({"T1": self.m.bind_of(r1["会計"], r1["階層"], r1["親"],
                                             r1["科目名"])},
                       cells, self._alias())
        self.assertEqual(got["X-2対称"], self.rec["歯-1"]["X-2対称"])
        r3 = self.rec["歯-3 の行(抜粋は別名の形)"]
        got3 = x2.count({"T3": self.m.bind_of(r3["engine が結ぶ正本"], r3["階層"],
                                              r3["親"], r3["科目名"])},
                        cells, self._alias())
        self.assertEqual(got3["X-2対称"], 0)
        self.assertEqual(got3["X-2非対称"], 1)

    def _alias(self):
        m = self.m
        books = {}
        for f in (m.M2.SOUKATU, m.M2.KESSAN, m.M2.MEISAI):
            books[f], _ = m.M2.M1.read(os.path.join(m.M2.CACHE, f))
        raw = m.E.fix_total_level(m.E.build_index(
            m.M2.parse_soukatu(books[m.M2.SOUKATU]),
            m.M2.parse_kessan(books[m.M2.KESSAN]),
            m.M2.parse_meisai(books[m.M2.MEISAI])))
        return m.SE.alias_table(raw)["table"]

    def test_10_the_record_separates_artificial_from_real(self):
        self.assertTrue(self.rec["artificial"])
        k = "**この結果は engine の安全性を何も示さない**"
        self.assertIn(k, self.rec)
        self.assertIn("計数器が数えられることだけを示す", self.rec[k])
        self.assertIn("実データでの安全性の証明とは分けて記録する", self.rec[k])
        self.assertIn("費用 0 USD", self.rec["step"])

    def test_10b_each_expectation_can_be_broken(self):
        """**歯**: 期待の 1 本ずつが、壊した実測で False になる。

        変異の走りは記録を作り直さないので、記録の数を読むだけでは
        「期待を緩める変異」が黙る(2026-10-16 の S8 で実測)。
        """
        good = ({"X-2対称": 1, "X-2三欄": 1, "X-2非対称": 1},
                {"X-2対称": 0, "X-2三欄": 0, "X-2非対称": 0},
                {"X-2対称": 0, "X-2三欄": 0, "X-2非対称": 1})
        base = self.m.checks_of(*good)
        self.assertEqual(len(base), 6)
        self.assertTrue(all(ok for _, ok, _ in base), "正しい入力で落ちている")
        broken = [({"X-2対称": 0, "X-2三欄": 1, "X-2非対称": 1}, good[1], good[2], 0),
                  ({"X-2対称": 1, "X-2三欄": 0, "X-2非対称": 1}, good[1], good[2], 1),
                  (good[0], {"X-2対称": 1, "X-2三欄": 0, "X-2非対称": 0}, good[2], 2),
                  (good[0], good[1], {"X-2対称": 1, "X-2三欄": 0, "X-2非対称": 1}, 3),
                  (good[0], good[1], {"X-2対称": 0, "X-2三欄": 0, "X-2非対称": 0}, 4),
                  (good[0], good[1], {"X-2対称": 0, "X-2三欄": 1, "X-2非対称": 1}, 5)]
        for a, b, c, i in broken:
            got = self.m.checks_of(a, b, c)
            self.assertFalse(got[i][1],
                             "期待 %d 本目が壊した入力で通った: %s" % (i + 1, got[i][0]))

    def test_11_the_conclusion_names_the_stage9_defect(self):
        self.assertIn("**段 9 の数え方をそのまま当てると偽の X-2 が出る**",
                      self.rec["結論"])
        self.assertIn("非対称は開示だけ", self.rec["結論"])
        self.assertNotEqual(self.rec["歯-3 の行(抜粋は別名の形)"]["抜粋の字"],
                            self.rec["歯-3 の行(抜粋は別名の形)"]["engine が結ぶ正本"],
                            "別名と正本が同じ字なら歯-3 は何も示していない")


if __name__ == "__main__":
    unittest.main()
