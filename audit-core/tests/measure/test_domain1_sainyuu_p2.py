# -*- coding: utf-8 -*-
"""P-2・P-3・P-4(docs/DOMAIN1_SAIIRU_P2_2026-10-16.md)を固定する。

守るのは 9 つ。
  1. `MIN_INDEPENDENT = 3` が字で在り、記録も 3 であること
  2. **その場で測り直して**記録と一致すること(款の数・P-4・落ちた理由)
  3. **6b は行ごとに落ちる**こと(列ごとに全部成立を要求すると緩い) ― 歯つき
  4. **`款 = Σ項` が 480/480 で成立**(項を落とす根拠を測ってある)
  5. **6a・6d に歯が在る**こと(壊した入力で落とす/落とさないが変わる)
  6. 文書の数が記録と一致すること
  7. **予測の照合が 4 本の外れを隠していない**こと
  8. 文書が「接続が増えたかは未測定」「誤った別名の受理は未測定」と書いていること
  9. **「安全性が改善した」と書いていない**こと
"""
import collections
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
REC = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p2_2026-10-16.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SAIIRU_P2_2026-10-16.md")
SRC = os.path.join(MEASURE, "sheet_sainyuu_p2_2026-10-16.py")
ENGINE = os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


_C = {}


def live():
    """**実物を読み直す。**記録を読むだけの門は変異に黙る。"""
    if "m" in _C:
        return _C["m"], _C["kk"], _C["mk"], _C["kn"], _C["mn"]
    sp = importlib.util.spec_from_file_location("p2_live", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    p1 = load(os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json"))
    sk, _ = m.P1M.read(m.P1M.SAINYUU)
    sm, _ = m.P1M.read(m.P1M.MEISAI_SAINYUU)
    kk, kn = m.kessan_kan(sk)
    mk, mn = m.meisai_kan(sm, p1["meisai_sainyuu"]["toc"])
    _C.update({"m": m, "kk": kk, "mk": mk, "kn": kn, "mn": mn, "sk": sk})
    return m, kk, mk, kn, mn


class PinnedTest(unittest.TestCase):
    def test_1_min_independent_is_three(self):
        self.assertIn("MIN_INDEPENDENT = 3", text(ENGINE))
        self.assertEqual(load(REC)["min_independent"], 3)


class LiveMeasurementTest(unittest.TestCase):
    def setUp(self):
        self.m, self.kk, self.mk, self.kn, self.mn = live()
        self.rec = load(REC)

    def test_2_kan_counts_match_the_record(self):
        hist = collections.Counter()
        for name, v in self.rec["per_account"].items():
            x = self.m.norm(name)
            self.assertEqual(len(self.mn.get(x, [])), v["kan_count_sainyuu"], name)
            hist[len(self.mn.get(x, []))] += 1
        self.assertEqual({str(k): v for k, v in hist.items()},
                         self.rec["P-3 歳入側の款の数の分布"])
        self.assertNotIn(1, hist, "歳入側に款が 1 つだけの会計が在る")

    def test_3_kan_equals_sum_of_ko(self):
        """**項を落とす根拠。**測らずに落としてはいけない。"""
        got = self.m.kan_is_sum_of_ko(_C["sk"])
        self.assertEqual(got, self.rec["6b 款 = Σ項"])
        self.assertTrue(got["all"])
        self.assertEqual(got["holds"], got["checked"])
        self.assertGreater(got["checked"], 400)

    def test_4_6b_is_applied_per_row_not_per_column(self):
        """**行ごと。**列ごとに「全部成立」を要求すると 91 行を数えてしまう。"""
        det, counts = self.m.determined_keys(self.kk)
        self.assertEqual(counts, self.rec["6b 行ごとに落とした件数"])
        col = self.rec["6b 列ごとの参考"]["調定額"]
        self.assertLess(col["holds"], col["checked"],
                        "列ごとに全部成立なら行ごとにする意味が無い")
        self.assertEqual(counts["調定額 を落とした"], col["holds"])

    def test_5_6b_has_teeth(self):
        """壊した入力: 関係が崩れた行は**落とさない**こと。"""
        norm = self.m.norm
        good = {"A": {(norm("甲"), norm("調定額")): 10,
                      (norm("甲"), norm("収入済額")): 7,
                      (norm("甲"), norm("不納欠損額")): 2,
                      (norm("甲"), norm("収入未済額")): 1}}
        det, _ = self.m.determined_keys(good)
        self.assertIn((norm("甲"), norm("調定額")), det.get("A", set()))
        bad = {"A": dict(good["A"])}
        bad["A"][(norm("甲"), norm("調定額"))] = 11      # 関係が崩れる
        det2, _ = self.m.determined_keys(bad)
        self.assertNotIn((norm("甲"), norm("調定額")), det2.get("A", set()),
                         "関係が崩れた行まで落としている")


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.rec = load(REC)

    def test_6_p4_and_reasons(self):
        p4 = self.rec["P-4 3 本に達する会計"]
        self.assertEqual(p4["of"], 18)
        self.assertEqual(p4["count"], 18)
        why = collections.Counter()
        for v in self.rec["per_account"].values():
            for k, n in v["dropped_why"].items():
                why[k] += n
        self.assertEqual(why["6a 歳出側の値と一致"], 99)
        self.assertEqual(why["6d 値を持つ正本が 2 つ以上"], 11)
        self.assertEqual(why["6b 代数的に決まる(行ごと)"], 80)
        for v in self.rec["per_account"].values():
            self.assertGreaterEqual(v["merged_independent_total"], 3)

    def test_7_every_account_had_6a_applied(self):
        """**6a が 1 件も効いていなければ、6a は当たっていない。**"""
        n = sum(1 for v in self.rec["per_account"].values()
                if v["dropped_why"].get("6a 歳出側の値と一致"))
        self.assertEqual(n, 18, "6a が効かなかった会計が在る")


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.rec = load(REC)

    def test_8_numbers_match_the_record(self):
        p4 = self.rec["P-4 3 本に達する会計"]
        self.assertIn("| **P-4 3 本に達する会計** | **%d / %d** |" % (p4["count"], p4["of"]),
                      self.t)
        self.assertIn("**1 款だけの会計は 0 件**", self.t)
        self.assertIn("**99 件**", self.t)
        self.assertIn("**480 行中 480 行で成立**", self.t)

    def test_9_four_misses_are_recorded(self):
        block = self.t.split("## §3")[1].split("## §4")[0]
        self.assertEqual(block.count("**外れ**"), 4, "外れの数が 4 本でない")
        self.assertEqual(block.count("**当たり**"), 3)
        self.assertIn("**0 件でも 18 件でもないと予測する**", block)
        self.assertIn("**外れ 4 本のうち 3 本は同じ向き ― 歳入側の情報量を低く見ていた。**",
                      block)

    def test_10_the_doc_stops_short(self):
        block = self.t.split("## §4")[1]
        self.assertIn("**これは「3 本に達した」だけである。接続が増えたかは未測定。**", block)
        self.assertIn("**誤った別名を受理しないかは未測定。**", block)
        self.assertIn("**封 §5 の停止規則は生きている**", block)
        self.assertIn("**「別名規則の安全性が改善した」とは書かない**", block)
        self.assertIn("「数が独立に観測された」ことの\n   証拠ではない", block)
        self.assertIn("明細と決算書は同じ台帳の 2 つの見せ方である。", block)

    def test_11_no_claim_of_improved_safety(self):
        self.assertNotIn("安全性が改善した。", self.t)
        self.assertNotIn("安全性を確認できた", self.t)


class DecisionTest(unittest.TestCase):
    """**判定そのものに当てる。**記録を読むだけでは 6a・6b・6d・値の食い違いを
    外す変異が全部黙る(2026-10-16 の変異 Q1〜Q4 で実測した)。"""

    def setUp(self):
        self.m, self.kk, self.mk, self.kn, self.mn = live()
        self.rec = load(REC)
        self.det, _ = self.m.determined_keys(self.kk)
        self.holders = self.m.value_holders(self.kk)
        self.out_vals = _C.setdefault(
            "ov", self.m.saisyutu_values()[2])

    def test_12_live_judgement_matches_the_record(self):
        norm = self.m.norm
        for name, v in self.rec["per_account"].items():
            x, c = norm(name), norm(v["canonical"])
            hits, why = self.m.judge_account(
                x, c, self.mk.get(x, {}), self.kk.get(c, {}),
                self.det, self.holders, self.out_vals)
            self.assertEqual(why, v["dropped_why"], name)
            ind, _ = self.m.E._independent(hits)
            self.assertEqual(len(ind), v["sainyuu_independent_new"], name)

    def _toy(self):
        """1 行だけの材料。**壊して当てるための土台。**"""
        norm = self.m.norm
        key = (norm("繰入金"), norm("収入済額"))
        mine = {key: 12345}
        theirs = {key: 12345}
        return mine, theirs, key

    def test_13_a_clean_row_is_counted(self):
        mine, theirs, _ = self._toy()
        hits, why = self.m.judge_account("x", "c", mine, theirs, {}, {}, {})
        self.assertEqual(len(hits), 1, why)

    def test_14_6a_drops_a_value_seen_on_the_saisyutu_side(self):
        mine, theirs, _ = self._toy()
        hits, why = self.m.judge_account(
            "x", "c", mine, theirs, {}, {}, {"c": {12345}})
        self.assertEqual(hits, [])
        self.assertEqual(why, {"6a 歳出側の値と一致": 1})

    def test_15_6b_drops_a_determined_row(self):
        mine, theirs, key = self._toy()
        hits, why = self.m.judge_account(
            "x", "c", mine, theirs, {"c": {key}}, {}, {})
        self.assertEqual(hits, [])
        self.assertEqual(why, {"6b 代数的に決まる(行ごと)": 1})

    def test_16_6d_drops_a_value_held_by_two_canonicals(self):
        mine, theirs, key = self._toy()
        holders = {(key[1], 12345): {"c", "other"}}
        hits, why = self.m.judge_account("x", "c", mine, theirs, {}, holders, {})
        self.assertEqual(hits, [])
        self.assertEqual(why, {"6d 値を持つ正本が 2 つ以上": 1})

    def test_17_a_value_mismatch_is_never_counted(self):
        """**値が食い違う行を数えない。**ここが緩むと誤った対が通る。"""
        mine, theirs, key = self._toy()
        theirs = {key: 99999}
        hits, why = self.m.judge_account("x", "c", mine, theirs, {}, {}, {})
        self.assertEqual(hits, [])
        self.assertEqual(why, {"値が食い違う": 1})

    def test_18_a_missing_row_is_never_counted(self):
        mine, theirs, key = self._toy()
        hits, why = self.m.judge_account("x", "c", mine, {}, {}, {}, {})
        self.assertEqual(hits, [])
        self.assertEqual(why, {"決算書に同じ行が無い": 1})

    def test_19_kan_equals_sum_has_teeth(self):
        """**壊した表では `款 = Σ項` が成立しないこと。**

        記録と突き合わせるだけでは、検査を常に真にする変異が黙る(変異 Q6)。
        """
        sk = _C["sk"]
        import copy
        broken = copy.deepcopy(sk)
        cells = broken["歳入"]["cells"]
        # 款 01(行 10)の 予算現額 を 1 円ずらす -> Σ項 と合わなくなる
        self.assertIn("D10", cells)
        cells["D10"] = {"value": 1, "formula": None,
                        "number_format": "General", "type": "n"}
        got = self.m.kan_is_sum_of_ko(broken)
        self.assertLess(got["holds"], got["checked"], "壊しても全部成立になっている")
        self.assertFalse(got["all"])


if __name__ == "__main__":
    unittest.main()
