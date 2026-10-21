# -*- coding: utf-8 -*-
"""P23(丸めの帯を片側にする直し)の試験。封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md §1。

P23 = P22 + 率の旗 ``pct_tolerance_from_decimals``(P18 の旗、既存)+ 新しい旗 ``truncate_abs_band``。
``truncate_abs_band`` が真で、書類の丸め方が「切り捨て」と決まった 2 周目(``rounding == "truncate"``)だけ、金額の照合の帯を
絶対値で片側(0 <= |fact| - |文| < 桁)にする。**書類の丸め方を決める 1 周目(``rounding`` が None)は P22 のまま** =
``decide_rounding`` の判定の軸は変えない(P19 の ``truncate_on_magnitude`` は軸も変えるので積まない)。
**各挙動について「P23 で効く」と「P22 では従来どおり」を対にして留める。**

合成の instance(facts と contexts を直接組む)で ``_direct_value_claim`` / ``_dispatch_num_claim`` を呼ぶ。通信しない。
"""
import dataclasses
import types
import unittest

from adapters.xbrl import comparators as C
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
PTR = "jppfs_cor:NetSales"


def fact(name, ctx, value, unit="JPY"):
    return {"name": "jppfs_cor:" + name, "context": ctx, "unit": unit, "value": float(value)}


def contexts_for(facts):
    return {f["context"]: {"members": []} for f in facts}


def call(profile_name, sentence, number, unit, subj, elems, facts, rounding=None, sign=1, member=None):
    """``sentence`` の中の ``number`` について ``_direct_value_claim`` を呼ぶ(金額)。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": sign * float(number.replace(",", "")),
             "result": None, "recomputed": None}
    R._direct_value_claim(claim, sentence, a, b, sign, float(number.replace(",", "")), unit, None, subj, elems, member,
                          facts, contexts_for(facts), V.PROFILES[profile_name], rounding)
    if rounding is not None and claim.get("unit_scale") is not None:     # _build_raw_num_claims と同じ(2 周目の札)
        claim["rounding"] = rounding
    return claim


def dispatch(profile_name, sentence, number, unit, subj, elems, facts, rounding=None, sign=1):
    """``_dispatch_num_claim`` を呼ぶ(率・金額の振り分けの入口)。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"id": "N001", "value": sign * float(number.replace(",", "")), "unit": unit, "subject": subj, "form": None,
             "pointer": None, "bound": False, "reason": None, "result": None, "recomputed": None}
    R._dispatch_num_claim(claim, sentence, a, b, sign, float(number.replace(",", "")), unit, None, subj, elems, member=None,
                          facts=facts, contexts=contexts_for(facts), profile=V.PROFILES[profile_name], rounding=rounding)
    return claim


NEG_FACT = [fact("OperatingIncome", CUR, -22989000)]      # △22.989 百万円
NEG_S = "営業損失は△23百万円となった。"                    # 注入後 = 実際の 22.989 を 23 に(絶対値が 1 桁大きい文)


class FlagShapeTest(unittest.TestCase):
    def test_p23_is_p22_plus_exactly_the_two_flags(self):
        self.assertEqual(dataclasses.replace(V.P22, name="P23", pct_tolerance_from_decimals=True, truncate_abs_band=True), V.P23)
        self.assertIs(V.PROFILES["P23"], V.P23)
        self.assertFalse(V.P22.truncate_abs_band)
        self.assertFalse(V.P22.pct_tolerance_from_decimals)

    def test_only_p23_has_the_new_flag_on(self):
        # 2026-10-21 P24 = P23 + 旗 2 つ(封 XBRL_VOCAB_SEAL_2026-10-21)は truncate_abs_band を引き継ぐ
        # 2026-10-21 P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)も引き継ぐ
        self.assertEqual(["P23", "P24", "P25"], sorted(n for n, p in V.PROFILES.items() if p.truncate_abs_band))

    def test_p19_flag_is_not_stacked(self):
        """P19 の ``truncate_on_magnitude`` は判定の軸も変えるので P23 には積まない(封 §0)。"""
        self.assertFalse(V.P23.truncate_on_magnitude)
        self.assertEqual(["P19"], sorted(n for n, p in V.PROFILES.items() if p.truncate_on_magnitude))

    def test_the_default_profile_is_still_p22_in_step_1(self):
        """段 1 では既定にしない(封 §1)。"""
        self.assertEqual("P22", V.DEFAULT_PROFILE)
        self.assertFalse(V.PROFILES[V.DEFAULT_PROFILE].truncate_abs_band)


class NegativeAmountTruncationTest(unittest.TestCase):
    """(a) 負の金額: 符号つきの切り捨て(P22)は「絶対値が 1 桁大きい文」を通す。P23 は止める。"""

    def test_p22_grounds_the_bigger_magnitude_sentence(self):
        c = call("P22", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("truncate", c["match"])

    def test_p23_stops_it_under_a_truncating_document(self):
        c = call("P23", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
        self.assertNotEqual("GROUNDED", c["result"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertTrue(c["bound"])
        self.assertEqual("xbrl:jppfs_cor:OperatingIncome@%s" % CUR, c["pointer"])

    def test_the_right_truncated_sentence_still_grounds_in_p23(self):
        """22.989 を切り捨てて 22 と書く文は P23 でも通る(絶対値の帯 0 <= 22.989 - 22 < 1)。"""
        for p in ("P22", "P23"):
            c = call(p, "営業損失は△22百万円となった。", "22", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
            self.assertEqual("GROUNDED", c["result"], p)

    def test_the_first_pass_is_the_same_as_p22(self):
        """1 周目(``rounding`` が None)は ``decide_rounding`` の根拠を数える軸なので P22 のまま = 判定の軸は変えない。"""
        c22 = call("P22", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding=None, sign=-1)
        c23 = call("P23", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding=None, sign=-1)
        self.assertEqual(c22, c23)
        self.assertNotIn("magnitude_truncate", c23)

    def test_the_rounding_evidence_axis_is_the_same_in_the_first_pass(self):
        """根拠の行(差・桁)は P22 と P23 の 1 周目で 1 行も違わない。"""
        rows = {}
        for p in ("P22", "P23"):
            facts = NEG_FACT + [fact("NetSales", CUR, 1234567000)]
            cs = [call(p, NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], facts, rounding=None, sign=-1),
                  call(p, "売上高は1,234百万円となった。", "1,234", "百万円", "売上高", ["NetSales"], facts, rounding=None)]
            rows[p] = R._rounding_evidence(cs)
        self.assertEqual(rows["P22"], rows["P23"])
        self.assertEqual(2, len(rows["P23"]))

    def test_a_rounding_document_is_untouched(self):
        """書類の丸め方が「四捨五入」と決まれば、切り捨ての枝を試さない = 旗は何も変えない。"""
        facts = [fact("OperatingIncome", CUR, -23400000)]
        for p in ("P22", "P23"):
            c = call(p, NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], facts, rounding="round", sign=-1)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("round", c["match"], p)
        c22 = call("P22", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="round", sign=-1)
        c23 = call("P23", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="round", sign=-1)
        self.assertEqual(c22, c23)


class VerifyTimeTest(unittest.TestCase):
    """検証時の照合(comparators 側の写し)にも旗が届く: params に ``magnitude_truncate`` が載り、``equals_within`` が同じ答えを返す。"""

    def recipe(self, profile_name):
        raw = call(profile_name, NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
        raw.update({"id": "N001", "sentence": 0, "span": "x", "unit": "百万円", "subject": "営業損失"})
        return R.claim_to_recipe(raw, "num")

    def test_p23_carries_the_band_to_the_verifier(self):
        r = self.recipe("P23")
        self.assertEqual("truncate", r.contract.params["rounding"])
        self.assertTrue(r.contract.params["magnitude_truncate"])

    def test_p22_does_not(self):
        r = self.recipe("P22")
        self.assertEqual("truncate", r.contract.params["rounding"])
        self.assertNotIn("magnitude_truncate", r.contract.params)

    def test_the_comparator_agrees_with_the_builder(self):
        ev = (types.SimpleNamespace(value=-22989000.0),)
        claim = types.SimpleNamespace(value=-23.0)
        for name, want in (("P22", True), ("P23", False)):
            r = self.recipe(name)
            cmp_ = C.equals_within(ev, claim, r.contract)
            self.assertEqual(want, cmp_.match, name)


class PercentTest(unittest.TestCase):
    """(b) 率: P23 は書かれた桁の半分 + 0.01(1 桁なら ±0.06)。P22 は ±0.15 固定。"""

    FACTS = [fact("EquityToAssetRatio", "CurrentYearInstant", 0.6168, unit="pure")]
    S = "自己資本比率は%s%%となった。"

    def run_(self, profile_name, num):
        return dispatch(profile_name, self.S % num, num, "%", "自己資本比率", ["EquityToAssetRatio"], self.FACTS)

    def test_a_tenth_off_is_grounded_in_p22_and_stopped_in_p23(self):
        self.assertEqual("GROUNDED", self.run_("P22", "61.8")["result"])            # 61.68 と 61.8 の差 0.12 <= 0.15
        self.assertEqual("VALUE_MISMATCH", self.run_("P23", "61.8")["result"])      # 0.12 > 0.06

    def test_the_rounded_value_is_grounded_in_both(self):
        for p in ("P22", "P23"):
            self.assertEqual("GROUNDED", self.run_(p, "61.7")["result"], p)          # 差 0.02

    def test_the_tolerance_is_the_p18_one(self):
        c = self.run_("P23", "61.7")
        self.assertAlmostEqual(0.06, c["pct_tolerance"])
        self.assertNotIn("pct_tolerance", self.run_("P22", "61.7"))


class P22UnchangedTest(unittest.TestCase):
    """(c) 旗が偽なら 1 行も変わらない: P22 の結果は旗(truncate_abs_band・pct_tolerance_from_decimals)を足す前と同じ。"""

    def test_p22_equals_p22_with_the_new_flag_explicitly_off(self):
        p = dataclasses.replace(V.P22, truncate_abs_band=False)
        self.assertEqual(V.P22, p)

    def test_every_profile_but_p23_keeps_the_signed_band_under_truncate(self):
        for name, p in V.PROFILES.items():
            if name in ("P19", "P23", "P24", "P25"):    # P24 = P23 + 旗 2 つ(封 XBRL_VOCAB_SEAL_2026-10-21)、P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)は P23 の旗を引き継ぐ
                continue
            c = call(name, NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
            self.assertEqual("GROUNDED", c["result"], name)
            self.assertNotIn("magnitude_truncate", c, name)

    def test_p19_still_stops_it_on_its_own_flag(self):
        c = call("P19", NEG_S, "23", "百万円", "営業損失", ["OperatingIncome"], NEG_FACT, rounding="truncate", sign=-1)
        self.assertNotEqual("GROUNDED", c["result"])
        self.assertTrue(c["magnitude_truncate"])


class AmountNormalCasesTest(unittest.TestCase):
    """(e) 金額の正の切り捨て・四捨五入の正常系は P22 と同じ。"""

    POS = [fact("NetSales", CUR, 22989000)]

    def test_positive_truncation(self):
        for p in ("P22", "P23"):
            c = call(p, "売上高は22百万円となった。", "22", "百万円", "売上高", ["NetSales"], self.POS, rounding="truncate")
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("truncate", c["match"], p)

    def test_positive_over_magnitude_is_stopped_in_both(self):
        for p in ("P22", "P23"):
            c = call(p, "売上高は23百万円となった。", "23", "百万円", "売上高", ["NetSales"], self.POS, rounding="truncate")
            self.assertNotEqual("GROUNDED", c["result"], p)

    def test_positive_rounding(self):
        facts = [fact("NetSales", CUR, 22600000)]
        for p in ("P22", "P23"):
            c = call(p, "売上高は23百万円となった。", "23", "百万円", "売上高", ["NetSales"], facts, rounding="round")
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("round", c["match"], p)

    def test_the_whole_claim_is_equal_for_positive_amounts(self):
        for rounding in (None, "round", "truncate"):
            for s, n in (("売上高は22百万円となった。", "22"), ("売上高は23百万円となった。", "23")):
                c22 = call("P22", s, n, "百万円", "売上高", ["NetSales"], self.POS, rounding=rounding)
                c23 = call("P23", s, n, "百万円", "売上高", ["NetSales"], self.POS, rounding=rounding)
                c23.pop("magnitude_truncate", None)
                self.assertEqual(c22, c23, (rounding, n))


class NonNegativeOperandsAreIndifferentTest(unittest.TestCase):
    """CF 流量項目(``_apply_flow_sign``)と向きの語の金額(``_direction_amount_check``)は、両辺を ``abs`` にしてから ``match_value`` を呼ぶ。
    両辺が非負なら帯を符号つきで当てても絶対値で当てても同じ = この 2 か所へ旗を渡すかどうかは結果を変えない(変異 M-8・M-9 が黙るのはこの等価のため。
    engine の変異で確かめた ― 結果文書)。この試験はその等価を格子で留める。"""

    def test_flag_does_not_change_the_ladder_for_non_negative_operands(self):
        vals = [0.0, 1.0, 2.9e7, 3.0e7, 2.2989e7, 2.3e7, 2.4e7, 1e8, 3.9e8, 4e8]
        for unit in (1e6, 1e8):
            for mode in (None, "round", "truncate"):
                for fv in vals:
                    for t in vals:
                        self.assertEqual(V.match_value(fv, t, unit, mode, False), V.match_value(fv, t, unit, mode, True), (fv, t, unit, mode))


class PeriodBindAndOtherDecisionsKeptTest(unittest.TestCase):
    """(d) 触る枝の中の人間の決定(案ア・§1b・C2・P21 の最後の枝・P22 の period_bind と subj and)は P23 でも P22 と同じ。"""

    S = "売上高は999千円となった。"

    def sales(self, cur, prior):
        return [fact("NetSales", CUR, cur), fact("NetSales", PRI, prior)]

    def test_period_bind_prior_only_is_not_grounded(self):
        c = call("P23", self.S, "999", "千円", "売上高", ["NetSales"], self.sales(5000000, 999000))
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, CUR), c["pointer"])

    def test_cue_keeps_the_prior_fact(self):
        c = call("P23", "売上高は、前期は999千円となった。", "999", "千円", "売上高", ["NetSales"], self.sales(5000000, 999000))
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"])

    def test_no_subject_is_the_same_as_p22_down_to_reason_and_state(self):
        for facts in (self.sales(5000000, 999000), self.sales(999000, 7000000)):
            c22 = call("P22", "999千円となった。", "999", "千円", None, [], facts)
            c23 = call("P23", "999千円となった。", "999", "千円", None, [], facts)
            self.assertEqual(c22, c23)
            self.assertEqual("UNVERIFIABLE", R._state_of(c23["reason"], c23["result"]))

    def test_prior_year_stop_of_section_1b(self):
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 7000000)]
        c = call("P23", "売上高は、前連結会計年度は999千円となった。", "999", "千円", "売上高", ["NetSales"], facts)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"])
        self.assertIsNone(c["pointer"])

    def test_p21_last_branch_f3b_still_applies(self):
        facts = [fact("CashAndDeposits", "CurrentYearInstant", 10000000), fact("CashAndDeposits", "Prior1YearInstant", 8000000)]
        c = call("P23", "現金及び預金は、前期末に比べて500千円増加した。", "500", "千円", "現金及び預金", ["CashAndDeposits"], facts)
        self.assertEqual("derived_value", c["form"])
        self.assertEqual("formula:a-b", c["pointer"][-1])


if __name__ == "__main__":
    unittest.main()
