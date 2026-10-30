# -*- coding: utf-8 -*-
"""PoC の正解集合(封 docs/DOMAIN1_POC_ABC_SEAL_2026-10-17.md §2)を固定する。

守るのは 10 つ。
  1. **第 1 段の 3 分類**が記録に在り、合計が 35 件になること
  2. **第 1 段だけでは正解にならない**(一意 28 件 > 正解集合 24 件)
  3. G-独立-2〜4 が**壊した入力で 1 本ずつ落ちる**(歯)
  4. **Core の規則を使っていない**(別名表・6 欄の鍵・接続の規則を import していない)
  5. 正解集合の各件が、**抜粋に在る値を 1 件だけ持つセル**であること(作り直して確認)
  6. 別枠の理由が**件ごとに**記録されていること
  7. **厳格な列(表層形なし)の数も在る**こと
  8. 表層形の表が封の字と一致し、**盲検でないと書かれている**こと
  9. `scope_forms` が**別名表を使わず**印字形と接頭辞なしの形を返すこと
 10. 正解集合が**封の予測の幅(18〜28 件)**の中に在ること(外れたら文書を直す合図)
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
REC = os.path.join(FX, "poc_gold_2026-10-17.json")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_POC_ABC_SEAL_2026-10-17.md")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class TwoStagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _mod("gold_t", "sheet_poc_gold_2026-10-17.py")
        cls.rec = load(REC)

    def test_1_three_classes_sum_to_all_claims(self):
        k = self.rec["第 1 段(値の分類。**正解と断定しない**)"]
        self.assertEqual(set(k), {"値の候補が一意", "値だけでは曖昧", "値が不一致"})
        self.assertEqual(sum(k.values()), len(self.rec["rows"]))
        self.assertEqual(len(self.rec["rows"]), 35)

    def test_2_stage_one_alone_is_not_the_gold(self):
        k = self.rec["第 1 段(値の分類。**正解と断定しない**)"]
        self.assertGreater(k["値の候補が一意"], self.rec["正解集合"]["件数"],
                           "**値の一意性だけで正解を確定している疑い**")
        self.assertEqual(self.rec["正解集合"]["件数"] + self.rec["別枠"]["件数"], 35)

    def test_3_each_independent_condition_can_fail(self):
        """**歯**: 文を壊すと G-独立-2 / 3 / 4 が 1 本ずつ落ちる。"""
        cell = {"scope": "東京都と場会計", "level": "目",
                "parent": "と場事業費 > と場事業費", "name": "運営費",
                "column": "補正予算額"}
        good = "と場会計の運営費は補正予算額がマイナス48,327,000円であった"
        ok, miss = self.m.independent_check(cell, good)
        self.assertEqual(miss, [], ok)
        self.assertEqual(len(ok), 3)
        ok2, miss2 = self.m.independent_check(cell, good.replace("運営費", "管理費"))
        self.assertTrue(any("G-独立-2" in m for m in miss2), miss2)
        ok3, miss3 = self.m.independent_check(
            cell, "運営費は補正予算額がマイナス48,327,000円であった")
        self.assertTrue(any("G-独立-3" in m for m in miss3), miss3)
        ok4, miss4 = self.m.independent_check(
            cell, "と場会計の運営費はマイナス48,327,000円であった")
        self.assertTrue(any("G-独立-4" in m for m in miss4), miss4)

    def test_4_the_surface_table_is_only_a_relaxation_of_the_column(self):
        cell = {"scope": "一般会計", "level": "項", "parent": "総務費",
                "name": "子供政策連携費", "column": "予算現額"}
        s = "一般会計の総務費のうち子供政策連携費が予算現在額10,169,000,000円"
        ok, miss = self.m.independent_check(cell, s)
        self.assertEqual(miss, [], "表層形が効いていない")
        ok2, miss2 = self.m.independent_check(cell, s, strict_column=True)
        self.assertTrue(any("G-独立-4" in m for m in miss2),
                        "**厳格にしても落ちない ― 厳格版が意味を持たない**")

    def test_5_core_rules_are_not_used(self):
        src = io.open(os.path.join(MEASURE, "sheet_poc_gold_2026-10-17.py"),
                      encoding="utf-8").read()
        for banned in ("alias_table", "canonicalize", "field_key", "bind(",
                       "sheet_m7_engine", "sheet_sainyuu_engine", "_independent"):
            self.assertNotIn(banned, src, "**Core の規則を使っている: %s**" % banned)
        self.assertIn("**Core の規則を使っていない**", self.rec)

    def test_6_scope_forms_does_not_use_an_alias_table(self):
        self.assertEqual(self.m.scope_forms("東京都と場会計"),
                         ("と場会計", "東京都と場会計"))
        self.assertEqual(self.m.scope_forms("一般会計"), ("一般会計",))
        self.assertEqual(self.m.scope_forms(None), ("",))


class RebuiltFromSourceTest(unittest.TestCase):
    """**記録を読むだけにしない。**正解集合をその場で作り直して突き合わせる。"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("gold_t2", "sheet_poc_gold_2026-10-17.py")
        cls.rec = load(REC)
        cls.b = cls.m.build()
        cls.strict = cls.m.build(strict_column=True)

    def test_7_gold_ids_match(self):
        self.assertEqual(self.b["gold"], self.rec["正解集合"]["ids"])
        self.assertEqual(self.b["apart"], self.rec["別枠"]["ids"])
        self.assertEqual(self.strict["gold"], self.rec["厳格な列(表層形なし)"]["ids"])

    def test_8_every_gold_value_appears_exactly_once_in_the_extract(self):
        mat = load(os.path.join(FX, "m11_material_2026-10-16.json"))
        cells = self.m.OPP.cells_of(self.m.OPP.extract_of(mat))
        for r in self.b["rows"]:
            if not r["正解"]:
                continue
            n = sum(1 for c in cells if c["value"] == r["値"])
            self.assertEqual(n, 1, "%s の値が抜粋に %d 件" % (r["id"], n))

    def test_9_apart_rows_carry_their_reason(self):
        for r in self.b["rows"]:
            if r["正解"]:
                continue
            self.assertTrue(r.get("別枠の理由"), r["id"])
            for m in r["別枠の理由"]:
                self.assertTrue(m.startswith("G-独立-"), m)

    def test_10_strict_column_count_is_recorded_and_smaller(self):
        s = self.rec["厳格な列(表層形なし)"]
        self.assertEqual(s["正解集合"], len(self.strict["gold"]))
        self.assertEqual(s["減った件数"],
                         self.rec["正解集合"]["件数"] - s["正解集合"])
        self.assertGreater(s["減った件数"], 0,
                           "**厳格版が同じ数なら、表層形の開示に意味が無い**")

    def test_11_within_the_sealed_prediction_band(self):
        n = self.rec["正解集合"]["件数"]
        self.assertTrue(18 <= n <= 28,
                        "**封の予測 V-1(18〜28 件)の外。結果の文書に外れとして書くこと**")
        t = io.open(SEAL, encoding="utf-8").read()
        self.assertIn("正解集合は **18〜28 件**", t)


if __name__ == "__main__":
    unittest.main()
