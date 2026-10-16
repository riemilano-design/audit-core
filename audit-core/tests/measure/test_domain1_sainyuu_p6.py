# -*- coding: utf-8 -*-
"""P-6 誤った別名の対照(docs/DOMAIN1_SAIIRU_P6_2026-10-16.md)を固定する。

守るのは 7 つ。
  1. `MIN_INDEPENDENT = 3` のまま・記録も 3
  2. **その場で測り直して** D-1 = 18/18・D-2 = 0/324 が出ること
  3. **分母の出どころ**(324 = 18 × 18)が記録と文書に在り、段 10 の 342 と**混ぜない**
  4. **対照に歯が在る** ― 閾値を 1 にすると 324/324・値の一致を外すと 286/324(実測)
  5. **6a・6b は誤った対に効かない**(0 件)ことが測ってあり、文書でも
     「安全の規則ではなく独立性の規則」と書き分けてあること
  6. `accept()` の緩める旗が**既定では全部効いている**こと(歯の測定専用)
  7. 文書が「実物の文に対する安全性は未検証」「安全性が改善したとは書かない」と言うこと
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
REC = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p6_2026-10-16.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SAIIRU_P6_2026-10-16.md")
SRC = os.path.join(MEASURE, "sheet_sainyuu_p6_2026-10-16.py")
ENGINE = os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


_C = {}


def live():
    if "b" in _C:
        return _C["m"], _C["b"]
    sp = importlib.util.spec_from_file_location("p6_live", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    _C["m"], _C["b"] = m, m.build()
    return _C["m"], _C["b"]


class PinnedTest(unittest.TestCase):
    def test_1_min_independent_is_three(self):
        self.assertIn("MIN_INDEPENDENT = 3", text(ENGINE))
        self.assertEqual(load(REC)["min_independent"], 3)
        m, _ = live()
        self.assertEqual(m.MIN, 3)


class LiveControlTest(unittest.TestCase):
    def setUp(self):
        self.m, b = live()
        (self.kk, self.mk, self.mn, self.al, self.out_vals,
         self.det, self.holders, self.existing, self.unconf) = b
        self.args = (self.kk, self.mk, self.det, self.holders,
                     self.out_vals, self.existing)
        self.rec = load(REC)

    def _pairs(self):
        return self.m.wrong_pairs(self.unconf, self.kk)

    def test_11_the_wrong_pairs_are_really_wrong(self):
        """**組の作り方に歯を付ける。**正しい対が 1 組でも混ざったら対照が壊れる。"""
        wrong = set(self.m.wrong_pairs(self.unconf, self.kk))
        right = set(self.m.correct_pairs(self.unconf))
        self.assertEqual(len(wrong), 324)
        self.assertEqual(len(right), 18)
        self.assertEqual(wrong & right, set(), "誤った対に正しい対が混ざっている")
        # 正しい対はすべて受理される(= 対照の向きが逆になっていない)
        for x, c in right:
            self.assertTrue(self.m.accept(x, c, *self.args)[0], (x, c))

    def test_2_d1_is_eighteen_of_eighteen(self):
        n = sum(1 for u in self.unconf
                if self.m.accept(self.m.norm(u["name"]),
                                 self.m.norm(u["canonical"]), *self.args)[0])
        self.assertEqual(n, 18)
        self.assertEqual(self.rec["D-1 正しい対の受理"]["accepted"], 18)
        self.assertEqual(self.rec["D-1 正しい対の受理"]["of"], 18)

    def test_3_d2_is_zero_of_324(self):
        pairs = self._pairs()
        self.assertEqual(len(pairs), 324, "分母が 324 でない")
        bad = [(x, c) for x, c in pairs if self.m.accept(x, c, *self.args)[0]]
        self.assertEqual(bad, [], "**誤った対を受理した**")
        self.assertEqual(self.rec["D-2 誤った対の受理"]["accepted"], 0)
        self.assertEqual(self.rec["D-2 誤った対の受理"]["of"], 324)

    def test_4_the_control_has_teeth(self):
        """**段 10 で足りなかったところ。**緩めたら通ること。"""
        pairs = self._pairs()
        loose = sum(1 for x, c in pairs
                    if self.m.accept(x, c, *self.args, min_independent=1)[0])
        self.assertEqual(loose, 324, "閾値を 1 にしても通らないなら歯が無い")
        nocheck = sum(1 for x, c in pairs
                      if self.m.accept(x, c, *self.args,
                                       use_value_check=False)[0])
        self.assertEqual(nocheck, 286)
        self.assertGreater(nocheck, 0)
        self.assertTrue(self.rec["has_teeth"])

    def test_5_6a_and_6b_do_not_guard_against_wrong_pairs(self):
        """**6a・6b は独立性の規則で、誤った対には効かない**(混ぜて書かない)。"""
        pairs = self._pairs()
        for kw in ({"use_6a": False}, {"use_6b": False}):
            n = sum(1 for x, c in pairs if self.m.accept(x, c, *self.args, **kw)[0])
            self.assertEqual(n, 0, kw)
        n6d = sum(1 for x, c in pairs
                  if self.m.accept(x, c, *self.args, use_6d=False)[0])
        self.assertEqual(n6d, 2)

    def test_6_the_flags_are_all_on_by_default(self):
        """緩める旗は**歯の測定専用**。既定で効いていなければ本番の判定が緩い。"""
        import inspect
        sig = inspect.signature(self.m.accept)
        for name in ("use_value_check", "use_6a", "use_6b", "use_6d",
                     "use_existing"):
            self.assertIs(sig.parameters[name].default, True, name)
        self.assertEqual(sig.parameters["min_independent"].default, 3)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.rec = load(REC)

    def test_7_numbers_and_denominator_origin(self):
        self.assertIn("| **D-1 正しい対の受理** | **18 / 18** |", self.t)
        self.assertIn("| **D-2 誤った対の受理** | **0 / 324** |", self.t)
        self.assertIn("**分母の出どころ**", self.t)
        self.assertIn("段 10 の 342 組(18 × 19)とは**分母が違う**", self.t)
        self.assertIn("**率として並べて比べない**", self.t)

    def test_8_teeth_table_matches_the_record(self):
        t = self.rec["D-3 歯の測定(規則を緩めたら誤った対が何件通るか)"]
        self.assertIn("| **`MIN_INDEPENDENT` を 1 にする** | **%d / 324** |"
                      % t["MIN_INDEPENDENT を 1 にする"], self.t)
        self.assertIn("| **値の食い違いを無視する** | **%d / 324** |"
                      % t["値の食い違いを無視する"], self.t)
        self.assertIn("| 6d(一意性)を外す | **%d / 324** |" % t["6d を外す"], self.t)
        self.assertIn("| 6a(歳出側の値と一致)を外す | %d / 324 |" % t["6a を外す"],
                      self.t)

    def test_9_rules_are_split_into_safety_and_independence(self):
        self.assertIn("**6a・6b は「安全」の規則ではなく「独立性」の規則である。**",
                      self.t)
        self.assertIn("**この 2 つを安全の根拠として書いてはいけない。**", self.t)

    def test_10_limits_are_stated(self):
        block = self.t.split("## §3")[1]
        self.assertIn("**人工材料での診断結果は、実データでの安全性の証明とは分けて記録する**",
                      block)
        self.assertIn("**③の実物の文に対する安全性は、依然として未検証である。**", block)
        self.assertIn("**「別名規則の安全性が改善した」とは書かない。**", block)
        self.assertIn("**接続が増えたかは P-5 でまだ測っていない。**", block)


if __name__ == "__main__":
    unittest.main()
