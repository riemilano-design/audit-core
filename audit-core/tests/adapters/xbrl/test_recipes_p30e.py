# -*- coding: utf-8 -*-
"""P30E(丸め方の根拠が混ざる桁は両方の帯で照らす RB)の試験。封 docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md §1・§2-1。

P30E = P29E + 旗 ``rounding_mixed_2026_11_04``。既定にしない(``DEFAULT_PROFILE`` = P27 のまま)。

* 規則 RB: ``build_raw_claims`` の 1 周目の根拠 ``(差, 桁)`` を桁 ``claim_scale`` ごとに分け、桁ごとの ``decide_rounding`` の R > 0 かつ T > 0
  (round しか説明できない件と truncate しか説明できない件が両方在る)桁を「混ざる桁」とする。混ざる桁の数の claim だけ、両方の帯
  (mode ``"both"``)で照らした 3 周目の同じ位置の claim に差し替える。書類の決定・他の桁・文字の claim・G3 の保留は 2 周目のまま。
* mode ``"both"``: ``vocabulary.match_value`` と ``comparators._match_value`` の先頭で ``None`` として扱う(写し元の梯子)。

**当たる例と当たらない例を、小さい文と fact で置く。** ``build_raw_claims`` は合成の instance(``load_instance`` などを差し替え)に当てる。
通信しない・cache を読まない。
"""
import dataclasses
import inspect
import unittest
from unittest import mock

from adapters.xbrl import comparators as C
from adapters.xbrl import instance as I
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

from .test_recipes_p24 import contexts_for, fact
from .test_recipes_p26 import BAL, REASON_HOLD, bal_hold

CUR = "CurrentYearDuration"
SEAL = "docs/XBRL_ROUNDING_MIXED_ENGINE_SEAL_2026-11-04.md"


def build(profile, text, facts, info=None):
    """``recipes.build_raw_claims`` を合成の instance で(zip を読む関数だけ差し替える。他は本番のまま)。"""
    inst = {"facts": facts, "contexts": {f["context"]: {"members": [], "axes": []} for f in facts},
            "textblocks": {"jpcrp_cor:ManagementAnalysisTextBlock": text}, "names": []}
    with mock.patch.object(I, "load_instance", return_value=inst), \
            mock.patch.object(R, "_label_subjects", side_effect=lambda zb, i, p: (list(p.subjects), [], {})), \
            mock.patch.object(R, "_flow_items_by_base", return_value={"base": {}, "sign": {}}), \
            mock.patch.object(R, "_member_material", side_effect=lambda zb, i, t, sents, p: ([(None, None)] * len(sents), {})):
        return R.build_raw_claims(b"", profile, info)


def by_id(claims):
    return {c["id"]: c for c in claims}


# 売上高 12,345,678 円(1,234 万円に切り捨てると 12,340,000 = 差 +5,678 > 桁/2: truncate しか説明できない)
# 営業利益 5,675,432 円(568 万円に四捨五入すると 5,680,000 = 差 −4,568 < 0: round しか説明できない)
MIXED_FACTS = [fact("NetSales", CUR, 12345678), fact("OperatingIncome", CUR, 5675432), fact("OrdinaryIncome", CUR, 3200000)]
MIXED_TEXT = "売上高は1,234万円となりました。営業利益は568万円となりました。"
#: 桁 10^4 は混ざるが、10^6 の claim(経常利益 3,200,000 円 = 3 百万円: 差 +200,000 で round にも truncate にも説明できる)は混ざらない
MIXED_TEXT_WITH_MILLION = MIXED_TEXT + "経常利益は3百万円となりました。"
#: 桁 10^4 の根拠が round だけ(営業利益 5,675,432 円 = 568 万円。売上高 12,339,000 円 = 1,234 万円: 差 −1,000 < 0)
ROUND_ONLY_FACTS = [fact("NetSales", CUR, 12339000), fact("OperatingIncome", CUR, 5675432)]
#: 桁 10^4 の根拠が truncate だけ(売上高 12,345,678 円 = 1,234 万円: 差 +5,678。営業利益 5,686,000 円 = 568 万円: 差 +6,000。どちらも桁/2 を超える)
TRUNC_ONLY_FACTS = [fact("NetSales", CUR, 12345678), fact("OperatingIncome", CUR, 5686000)]


class MixedScaleTest(unittest.TestCase):
    """当たる例: 桁 10^4 の根拠が round と truncate の両方に在る書類。"""

    def test_p29e_leaves_the_truncate_row_as_value_mismatch(self):
        info = {}
        n, _t = build(V.P29E, MIXED_TEXT, MIXED_FACTS, info)
        c = by_id(n)
        self.assertEqual(("round", 1, 1), (info["rounding"], info["rounding_round_only"], info["rounding_truncate_only"]))
        self.assertNotIn("rounding_mixed_scales_2026_11_04", info)
        self.assertEqual("VALUE_MISMATCH", c["N001"]["result"])
        self.assertEqual("round", c["N001"]["rounding"])
        self.assertEqual("GROUNDED", c["N002"]["result"])

    def test_p30e_grounds_both_rows_with_the_both_band(self):
        info = {}
        n, _t = build(V.P30E, MIXED_TEXT, MIXED_FACTS, info)
        c = by_id(n)
        self.assertEqual([10000.0], info["rounding_mixed_scales_2026_11_04"])
        self.assertEqual("round", info["rounding"])             # 書類の決定は 2 周目のまま
        self.assertEqual(("GROUNDED", "both", "truncate"), (c["N001"]["result"], c["N001"]["rounding"], c["N001"]["match"]))
        self.assertEqual(("GROUNDED", "both", "round"), (c["N002"]["result"], c["N002"]["rounding"], c["N002"]["match"]))

    def test_the_row_that_p29e_already_grounded_stays_grounded_and_nothing_is_lost(self):
        a = by_id(build(V.P29E, MIXED_TEXT, MIXED_FACTS)[0])
        b = by_id(build(V.P30E, MIXED_TEXT, MIXED_FACTS)[0])
        self.assertEqual(sorted(a), sorted(b))
        for k, c in a.items():
            if c["result"] == "GROUNDED":
                self.assertEqual("GROUNDED", b[k]["result"], k)

    def test_the_recipe_carries_both_in_the_contract_params(self):
        c = by_id(build(V.P30E, MIXED_TEXT, MIXED_FACTS)[0])["N001"]
        rc = R.claim_to_recipe(c, "num")
        self.assertEqual("both", rc.contract.params["rounding"])

    def test_the_third_pass_runs_only_when_a_scale_is_mixed_and_with_both(self):
        calls = []
        real = R._build_raw_num_claims

        def spy(sentences, facts, contexts, profile, claim_member, rounding=None, flow_base=None):
            calls.append(rounding)
            return real(sentences, facts, contexts, profile, claim_member, rounding, flow_base=flow_base)

        with mock.patch.object(R, "_build_raw_num_claims", spy):
            build(V.P29E, MIXED_TEXT, MIXED_FACTS)
            self.assertEqual([None, "round"], calls)
            del calls[:]
            build(V.P30E, MIXED_TEXT, MIXED_FACTS)
            self.assertEqual([None, "round", "both"], calls)
            del calls[:]
            build(V.P30E, MIXED_TEXT, ROUND_ONLY_FACTS)
            self.assertEqual([None, "round"], calls)

    def test_a_scale_that_is_not_mixed_keeps_the_second_pass(self):
        """桁 10^4 が混ざっても、10^6 の claim は 2 周目のまま(``rounding`` は書類の決定、P29E と同じ claim)。"""
        info = {}
        a, _ = build(V.P29E, MIXED_TEXT_WITH_MILLION, MIXED_FACTS)
        b, _ = build(V.P30E, MIXED_TEXT_WITH_MILLION, MIXED_FACTS, info)
        self.assertEqual([10000.0], info["rounding_mixed_scales_2026_11_04"])
        ca, cb = by_id(a), by_id(b)
        self.assertEqual(1000000.0, cb["N003"]["claim_scale"])
        self.assertIn(cb["N003"]["rounding"], ("round", "truncate"))
        self.assertEqual(ca["N003"], cb["N003"])
        self.assertEqual("both", cb["N001"]["rounding"])
        self.assertEqual("both", cb["N002"]["rounding"])

    def test_two_mixed_scales_are_listed_ascending_and_both_replaced(self):
        """桁 10^4 と 10^6 の両方が混ざる書類: 昇順の列で、両方の桁の claim が両方の帯。"""
        facts = MIXED_FACTS[:2] + [fact("OrdinaryIncome", CUR, 3700000), fact("GrossProfit", CUR, 2700000)]
        text = MIXED_TEXT + "経常利益は3百万円となりました。売上総利益は3百万円となりました。"
        info = {}
        n, _t = build(V.P30E, text, facts, info)
        self.assertEqual([10000.0, 1000000.0], info["rounding_mixed_scales_2026_11_04"])
        self.assertEqual(["both"] * 4, [c["rounding"] for c in n])
        self.assertEqual(["GROUNDED"] * 4, [c["result"] for c in n])

    def test_a_third_pass_of_a_different_length_stops(self):
        real = R._build_raw_num_claims

        def short(sentences, facts, contexts, profile, claim_member, rounding=None, flow_base=None):
            got = real(sentences, facts, contexts, profile, claim_member, rounding, flow_base=flow_base)
            return got[:-1] if rounding == "both" else got

        with mock.patch.object(R, "_build_raw_num_claims", short):
            with self.assertRaises(ValueError):
                build(V.P30E, MIXED_TEXT, MIXED_FACTS)

    def test_text_claims_are_not_touched(self):
        text = MIXED_TEXT + "売上高は前期に比べ増加しました。"
        facts = MIXED_FACTS + [fact("NetSales", "Prior1YearDuration", 10000000)]
        n_a, t_a = build(V.P29E, text, facts)
        n_b, t_b = build(V.P30E, text, facts)
        self.assertTrue(t_a)
        self.assertEqual(t_a, t_b)
        self.assertTrue(all(c.get("rounding") in (None, "round") for c in t_b))


class NotMixedTest(unittest.TestCase):
    """当たらない例: 混ざらない書類では P29E と P30E の出力が同じ。"""

    def test_round_only_evidence_is_the_same_as_p29e(self):
        info = {}
        a = build(V.P29E, MIXED_TEXT, ROUND_ONLY_FACTS)
        b = build(V.P30E, MIXED_TEXT, ROUND_ONLY_FACTS, info)
        self.assertEqual(a, b)
        self.assertEqual([], info["rounding_mixed_scales_2026_11_04"])
        self.assertTrue(all(c["rounding"] == "round" for c in b[0]))

    def test_truncate_only_evidence_is_the_same_as_p29e(self):
        info = {}
        a = build(V.P29E, MIXED_TEXT, TRUNC_ONLY_FACTS)
        b = build(V.P30E, MIXED_TEXT, TRUNC_ONLY_FACTS, info)
        self.assertEqual(a, b)
        self.assertEqual([], info["rounding_mixed_scales_2026_11_04"])
        self.assertTrue(all(c["rounding"] == "truncate" for c in b[0]))

    def test_the_flag_off_is_p29e_in_every_document(self):
        off = dataclasses.replace(V.P30E, name="P30E_OFF", rounding_mixed_2026_11_04=False)
        for facts in (MIXED_FACTS, ROUND_ONLY_FACTS, TRUNC_ONLY_FACTS):
            for text in (MIXED_TEXT, MIXED_TEXT_WITH_MILLION):
                self.assertEqual(build(V.P29E, text, facts), build(off, text, facts))
        self.assertEqual(dataclasses.replace(V.P29E, name="P30E_OFF"), off)

    def test_no_evidence_at_all_is_not_mixed(self):
        info = {}
        a = build(V.P29E, "営業利益は568万円となりました。", [fact("Assets", CUR, 1)])
        b = build(V.P30E, "営業利益は568万円となりました。", [fact("Assets", CUR, 1)], info)
        self.assertEqual(a, b)
        self.assertEqual([], info["rounding_mixed_scales_2026_11_04"])

    def test_mixed_rule_needs_both_counts_per_scale(self):
        """混ざる桁の判定は桁ごと: 全部をまとめると R > 0 かつ T > 0 でも、桁ごとに分ければ混ざらない書類(10^4 は round だけ・10^6 は truncate だけ)。"""
        facts = [fact("NetSales", CUR, 12339000), fact("OperatingIncome", CUR, 5675432), fact("OrdinaryIncome", CUR, 3700000)]
        text = MIXED_TEXT + "経常利益は3百万円となりました。"
        # 桁 10^4: 売上高 差 −1,000(R)・営業利益 差 −4,568(R)。桁 10^6: 経常利益 差 +700,000 > 桁/2(T)。まとめると R = 2・T = 1 だが、桁ごとには R だけ・T だけ
        info = {}
        a = build(V.P29E, text, facts)
        b = build(V.P30E, text, facts, info)
        self.assertEqual([], info["rounding_mixed_scales_2026_11_04"])
        self.assertEqual(a, b)


class BothModeTest(unittest.TestCase):
    """mode ``"both"`` は ``None`` と同じ(vocabulary と comparators の両方)。"""

    CASES = [
        (12345678.0, 12340000.0, 10000.0),     # truncate
        (5675432.0, 5680000.0, 10000.0),       # round
        (5680000.0, 5680000.0, 10000.0),       # 同じ値(round)
        (-12345678.0, 12340000.0, 10000.0),    # abs+round / abs+truncate の側
        (-5675432.0, 5680000.0, 10000.0),
        (5675432.0, -5680000.0, 10000.0),
        (12345678.0, 12400000.0, 10000.0),     # どちらでもない
        (5000.0, 9000000.0, 10000.0),
        (12349999.0, 12340000.0, 10000.0),     # 帯の縁
        (12350000.0, 12340000.0, 10000.0),
        (12335000.0, 12340000.0, 10000.0),
        (12334999.0, 12340000.0, 10000.0),
    ]

    def test_vocabulary_both_equals_none(self):
        for fv, t, u in self.CASES:
            for mt in (False, True):
                self.assertEqual(V.match_value(fv, t, u, None, mt), V.match_value(fv, t, u, "both", mt), (fv, t, u, mt))

    def test_comparators_both_equals_none(self):
        for fv, t, u in self.CASES:
            for mt in (False, True):
                self.assertEqual(C._match_value(fv, t, u, None, mt), C._match_value(fv, t, u, "both", mt), (fv, t, u, mt))

    def test_both_is_wider_than_either_single_band(self):
        self.assertEqual("truncate", V.match_value(12345678.0, 12340000.0, 10000.0, "both"))
        self.assertIsNone(V.match_value(12345678.0, 12340000.0, 10000.0, "round"))
        self.assertEqual("round", V.match_value(5675432.0, 5680000.0, 10000.0, "both"))
        self.assertIsNone(V.match_value(5675432.0, 5680000.0, 10000.0, "truncate"))
        self.assertEqual("truncate", C._match_value(12345678.0, 12340000.0, 10000.0, "both"))
        self.assertEqual("round", C._match_value(5675432.0, 5680000.0, 10000.0, "both"))
        self.assertEqual("abs+round", V.match_value(-5675432.0, 5680000.0, 10000.0, "both"))
        self.assertEqual("abs+round", C._match_value(-5675432.0, 5680000.0, 10000.0, "both"))
        self.assertIsNone(V.match_value(12400000.0, 12340000.0, 10000.0, "both"))
        self.assertIsNone(C._match_value(12400000.0, 12340000.0, 10000.0, "both"))

    def test_single_modes_and_none_are_unchanged(self):
        for fv, t, u in self.CASES:
            for m in ("round", "truncate"):
                got = V.match_value(fv, t, u, m)
                self.assertEqual(got, C._match_value(fv, t, u, m))
                self.assertTrue(got is None or got.endswith(m), (fv, t, u, m, got))

    def test_the_both_line_sits_before_the_ladder_loop(self):
        for fn in (V.match_value, C._match_value):
            src = inspect.getsource(fn)
            self.assertIn('if mode == "both":', src)
            self.assertLess(src.index('if mode == "both":'), src.index("for sign_mode, fv in"))

    def test_mag_trunc_is_false_for_both(self):
        """``recipes._mag_trunc``: P23 の切り捨ての絶対値の帯は ``"both"`` に掛からない(P23 の旗だけの profile で偽)。"""
        p23 = V.PROFILES["P23"]
        self.assertTrue(R._mag_trunc(p23, "truncate"))
        self.assertFalse(R._mag_trunc(p23, "both"))


class G3HoldTest(unittest.TestCase):
    """P26 G3 ``rounded_diff_hold`` は ``"both"`` でも残る(``rounding is not None``)。"""

    def test_hold_stays_with_both(self):
        c = bal_hold("4,041", p="P30E", rounding="both")
        self.assertIsNone(c["result"])
        self.assertIsNone(c["pointer"])
        self.assertEqual(REASON_HOLD, c["reason"])
        self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]))
        self.assertEqual({"named": ["xbrl:jppfs_cor:CurrentLiabilities@CurrentYearInstant", "xbrl:jppfs_cor:CurrentLiabilities@Prior1YearInstant"],
                          "diff": 4042000000.0}, c["rounded_diff_hold"])
        self.assertEqual(c, bal_hold("4,041", p="P29E", rounding="round"))     # 保留の結果は 2 周目の丸め方に依らない

    def test_the_exact_difference_is_still_grounded(self):
        c = bal_hold("4,042", p="P30E", rounding="both")
        self.assertEqual("GROUNDED", c["result"])
        self.assertNotIn("rounded_diff_hold", c)

    def test_hold_is_off_without_the_rounding_pass(self):
        self.assertNotEqual(REASON_HOLD, bal_hold("4,041", p="P30E", rounding=None)["reason"])


class ProfileShapeTest(unittest.TestCase):
    def test_p30e_is_p29e_plus_exactly_the_flag(self):
        self.assertEqual(dataclasses.replace(V.P29E, name="P30E", rounding_mixed_2026_11_04=True), V.P30E)
        self.assertIs(V.PROFILES["P30E"], V.P30E)
        self.assertNotIn("P30", V.PROFILES)

    def test_flag_true_only_for_p30e(self):
        # 2026-11-06: P32E(= P30E + PB。封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md)も RB の旗を引き継ぐ
        self.assertEqual(["P30E", "P32E"], sorted(n for n, p in V.PROFILES.items() if p.rounding_mixed_2026_11_04))
        for p in (V.P29E, V.P29, V.P28E, V.P28, V.P27E, V.P27):
            self.assertFalse(p.rounding_mixed_2026_11_04, p.name)
        self.assertIs(False, {f.name: f for f in dataclasses.fields(V.Profile)}["rounding_mixed_2026_11_04"].default)

    def test_p30e_inherits_every_other_flag_of_p29e(self):
        for f in dataclasses.fields(V.Profile):
            if f.name in ("name", "rounding_mixed_2026_11_04"):
                continue
            self.assertEqual(getattr(V.P29E, f.name), getattr(V.P30E, f.name), f.name)

    def test_the_default_is_still_p27(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)

    def test_the_flag_field_sits_right_after_numbers_man_comma(self):
        names = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(names.index("numbers_man_comma_2026_11_04") + 1, names.index("rounding_mixed_2026_11_04"))

    def test_the_flag_is_wired_in_the_build_and_the_seal_is_named(self):
        src = inspect.getsource(R.build_raw_claims)
        self.assertIn('getattr(profile, "rounding_mixed_2026_11_04", False)', src)
        self.assertIn(SEAL, src)
        self.assertIn(SEAL, inspect.getsource(V.match_value))
        self.assertIn(SEAL, inspect.getsource(C._match_value))


if __name__ == "__main__":
    unittest.main()
