# -*- coding: utf-8 -*-
"""P27・P27E(外部の数の文のための engine の直し)の試験。封 docs/XBRL_P27_SEAL_2026-10-27.md §1・§2-1。

P27 = P26 + A・C1・C2・C3(出どころに依らない直し)。P27E = P27 + B(外部の数の文のための名指し。既定の候補にしない)。
**既定は段 1 の commit までは P26 のまま**(``DEFAULT_PROFILE``)。2026-10-28 の既定を P27 に切り替える段 2(封 ``docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md``)で P27 になった(P27E は既定にしない)。どの旗も偽なら P1〜P26 の振る舞いは 1 行も変わらない。

  A  ``written_precision_2026_10_27``   : 書かれた小数部の桁数で精度を細かくする(「12.3億円」は 1 億円でなく 0.1 億円で照合)。
  B  ``last_branch_relative_2026_10_27``: 最後の枝で、P25 の証拠が無く相対の差が ρ = 0.15 以内なら名指す(P27E だけ)。
  C1 ``per_share_window_2026_10_27``    : 数の手前 20 字に「株当たり|EPS|BPS」があれば概念の門 G1 の per_share_subject を真にする。
  C2 ``per_unit_counter_2026_10_27``    : 「1人当たり」「1株当たり」の「1」は数の主張にしない(UNVERIFIABLE、理由 ``per_unit_counter``)。
  C3 ``future_period_2026_10_27``       : 当期末より後の「YYYY年M月期」の後ろの数は UNVERIFIABLE(既存の ``target_or_plan``)。

**この file の例の字と数は全部作り物**(封 §1 の例のとおり。調整用の文・DB の値・XBRL の値を写していない)。**各挙動について「当たる例」「当たらない例」
(と、封が代価に挙げた「当たってしまう例」)を置き、旗が偽なら P26 と同じ出力になることを対にして留める。**
合成の instance(facts と contexts を直接組む)に、手元の cache の実物の書類(sha256 を固定。無ければ失敗。skip しない)を足す。通信しない。
"""
import ast
import dataclasses
import hashlib
import inspect
import os
import unittest

from adapters.xbrl import extract as E
from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import report_customer as RC
from adapters.xbrl import verify_document as VD
from adapters.xbrl import vocabulary as V

from .test_recipes_p24 import contexts_for, fact, num_claims

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
FLAGS = ("written_precision_2026_10_27", "last_branch_relative_2026_10_27", "per_share_window_2026_10_27",
         "per_unit_counter_2026_10_27", "future_period_2026_10_27")
OFF = dict((f, False) for f in FLAGS)
#: 旗を全部偽にした P27 = P26 と同じ(名前だけ違う)。
P27_OFF = dataclasses.replace(V.P27, name="P27_OFF", **OFF)
P27E_OFF = dataclasses.replace(V.P27E, name="P27E_OFF", **OFF)
VM_REASON = "value differs(segment/other period?)"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")


def only(flag):
    """P26 に旗を 1 つだけ足した profile(測定と同じ作り。engine には登録しない)。"""
    return dataclasses.replace(V.P26, name="P27_only_" + flag, **{flag: True})


def gated(p, sentence, facts, contexts=None):
    """``build_raw_claims`` と同じ並び(数の claim を作る → ``_p27_gate`` を全部に → 概念の門)を、合成の instance に当てた数の claim の列。"""
    prof = V.PROFILES[p] if isinstance(p, str) else p
    ctx = contexts if contexts is not None else contexts_for(facts)
    claims = num_claims(prof, sentence, facts, ctx)
    if (prof.per_share_window_2026_10_27 or prof.per_unit_counter_2026_10_27 or prof.future_period_2026_10_27):
        for c in claims:
            R._p27_gate(c, [sentence], ctx, prof)
    if prof.concept_gate:
        by_key = dict(((f["name"], f["context"]), f) for f in facts)
        for c in claims:
            R._concept_gate(c, prof, by_key)
    return claims


def the(claims, unit=None):
    """claim が 1 件に決まるとき、その claim。unit で絞れる。"""
    got = [c for c in claims if unit is None or c["unit"] == unit]
    assert len(got) == 1, [(c["id"], c["unit"], c["value"]) for c in claims]
    return got[0]


def row(c):
    """比べる欄(state の決まり方と pointer。provenance の旗の印は含めない)。"""
    return (c["result"], c["reason"], c["pointer"], c["bound"], c["recomputed"], c.get("match"))


NS = [fact("NetSales", CUR, 820000000)]


# ====================================================================================================
class FlagShapeTest(unittest.TestCase):
    def test_p27_is_p26_plus_exactly_the_four_flags(self):
        want = dataclasses.replace(V.P26, name="P27", written_precision_2026_10_27=True, per_share_window_2026_10_27=True,
                                   per_unit_counter_2026_10_27=True, future_period_2026_10_27=True)
        self.assertEqual(want, V.P27)
        self.assertIs(V.PROFILES["P27"], V.P27)

    def test_p27e_is_p27_plus_exactly_the_relative_flag(self):
        self.assertEqual(dataclasses.replace(V.P27, name="P27E", last_branch_relative_2026_10_27=True), V.P27E)
        self.assertIs(V.PROFILES["P27E"], V.P27E)
        self.assertFalse(V.P27.last_branch_relative_2026_10_27)

    def test_the_flags_are_false_by_default_in_declared_order(self):
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        for n in FLAGS:
            self.assertIs(False, fields[n].default, n)
        order = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(list(FLAGS), [n for n in order if n in FLAGS])               # 封 §1-5 の順

    def test_only_p27_and_p27e_have_any_flag(self):
        for n, p in sorted(V.PROFILES.items()):
            have = [f for f in FLAGS if getattr(p, f)]
            if n == "P27":
                want = [f for f in FLAGS if f != "last_branch_relative_2026_10_27"]
            elif n == "P27E":
                want = list(FLAGS)
            else:
                want = []
            self.assertEqual(want, have, n)

    def test_with_all_flags_false_p27_and_p27e_are_p26(self):
        self.assertEqual(dataclasses.replace(V.P26, name="P27_OFF"), P27_OFF)
        self.assertEqual(dataclasses.replace(V.P26, name="P27E_OFF"), P27E_OFF)

    def test_no_per_flag_profile_is_registered_and_the_default_is_p27_since_default_p27_step_2(self):
        self.assertEqual(["P27", "P27E"], sorted(n for n in V.PROFILES if "P27" in n))
        # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 既定は P27。P27 の旗 4 つは真・B の旗(last_branch_relative_2026_10_27)は偽(P27E は既定にしない)
        self.assertEqual("P27", V.DEFAULT_PROFILE)
        self.assertIs(V.PROFILES[V.DEFAULT_PROFILE], V.P27)
        self.assertIsNot(V.PROFILES[V.DEFAULT_PROFILE], V.P27E)
        for f in FLAGS:
            self.assertEqual(f != "last_branch_relative_2026_10_27", getattr(V.PROFILES[V.DEFAULT_PROFILE], f), f)

    def test_the_constants_are_pinned_in_letters(self):
        self.assertEqual(0.15, R.LAST_BRANCH_REL_RHO)
        self.assertEqual(20, R.PER_SHARE_WINDOW)
        self.assertEqual("株当たり|EPS|BPS", R.PER_SHARE_RE.pattern)
        self.assertEqual("per_unit_counter", R.PER_UNIT_COUNTER)
        self.assertEqual(("人", "名", "株", "千株", "台", "店", "店舗", "社", "件"), R.PER_UNIT_COUNTER_UNITS)
        self.assertEqual(("当たり", "あたり"), R.PER_UNIT_COUNTER_AFTER)
        self.assertEqual(r"(\d{4})年(\d{1,2})月期", R._FUTURE_PERIOD_RE.pattern)
        self.assertEqual(r"(\d[\d,]*)(?:\.(\d+))?(?=\D*$)", E._LAST_DIGITS_RE_2026_10_27.pattern)
        self.assertEqual(2, R.LAST_BRANCH_NAMED_MIN_K)         # B が G2 と同じ字で (ii) を見直す


# ====================================================================================================
class AWrittenPrecisionTest(unittest.TestCase):
    """A(封 §1-1)。"""

    def test_hits_the_last_digit_group_with_a_decimal_part(self):
        for s, prec26, prec27 in (("売上高は12.3億円", 1e8, 1e7),                  # 小数 1 桁: 1 億円 -> 0.1 億円
                                  ("1,234.5百万円", 1e6, 1e5),                    # 1 百万円 -> 0.1 百万円
                                  ("1株当たり利益は132.47円", 1, 0.01),            # 小数 2 桁: 1 円 -> 0.01 円
                                  ("営業利益は1.5兆円", 1e12, 1e11)):
            a = [t for t in E.iter_numbers_2026_10_21(s) if t[3] in V.UNIT_SCALE]
            b = [t for t in E.iter_numbers_2026_10_27(s) if t[3] in V.UNIT_SCALE]
            self.assertEqual(1, len(a), s)
            self.assertEqual(prec26, a[0][4], s)
            self.assertEqual(prec27, b[0][4], s)
            self.assertEqual(a[0][:4], b[0][:4], s)             # 開始・終わり・値・単位は変えない

    def test_divides_by_an_integer_power_of_ten_not_multiplying_by_a_float(self):
        t = [t for t in E.iter_numbers_2026_10_27("売上高は12.3億円") if t[3] == "円"][0]
        self.assertEqual(1e8 / 10, t[4])
        self.assertEqual(10000000.0, t[4])                       # 1e8 * 0.1 でも同じ値になる桁では区別できないので、2 桁の例も置く
        u = [t for t in E.iter_numbers_2026_10_27("売上高は12.34億円") if t[3] == "円"][0]
        self.assertEqual(1e8 / 100, u[4])
        self.assertEqual(1000000.0, u[4])

    def test_does_not_hit_without_a_decimal_part_or_outside_the_yen_family(self):
        for s in ("売上高は12億円", "売上高は380億6千4百万円", "仕入は6万5千円", "売上高は1,234百万円", "営業利益率は3.5%",
                  "売上高は1.5億3千万円", "売上高は1.5億3千4百万円",       # 小数部は途中の組にだけ在る(最後の組『3』『4』に小数部が無い)
                  "従業員は240人", "前期比2.5ポイント", "株価は148円22銭"):
            a = E.iter_numbers_2026_10_21(s)
            b = E.iter_numbers_2026_10_27(s)
            self.assertEqual(a, b, s)

    def test_the_older_readers_are_unchanged(self):
        self.assertEqual(1e8, E.iter_numbers("売上高は12.3億円")[0][4])
        self.assertEqual(1e8, E.iter_numbers_2026_10_21("売上高は12.3億円")[0][4])

    def test_numbers_of_uses_it_only_when_the_flag_is_true(self):
        s = "売上高は12.3億円"
        self.assertEqual(E.iter_numbers_2026_10_27(s), R._numbers_of(V.P27, s))
        self.assertEqual(E.iter_numbers_2026_10_27(s), R._numbers_of(V.P27E, s))
        self.assertEqual(E.iter_numbers_2026_10_21(s), R._numbers_of(V.P26, s))
        self.assertEqual(E.iter_numbers(s), R._numbers_of(V.P25, s))
        self.assertEqual(E.iter_numbers_2026_10_21(s), R._numbers_of(P27_OFF, s))

    def test_the_band_is_the_written_precision_p27_but_the_old_band_in_p26(self):
        """fact 8.2 億円。『8.2億円』は一致。『8.25億円』は P26(帯 ±0.5 億円)では一致、P27(帯 ±0.05 億円)では一致しない(代価: 書き手が書類と違う丸め方で書いた文)。"""
        c26 = the(num_claims("P26", "売上高は8.25億円となりました。", NS))
        c27 = the(num_claims("P27", "売上高は8.25億円となりました。", NS))
        self.assertEqual("GROUNDED", c26["result"])
        self.assertEqual(1e8, c26["claim_scale"])
        self.assertIsNone(c27["result"])
        self.assertEqual(1e6, c27["claim_scale"])
        self.assertEqual(R.NO_SAME_VALUE, c27["reason"])
        g = the(num_claims("P27", "売上高は8.2億円となりました。", NS))
        self.assertEqual("GROUNDED", g["result"])
        self.assertEqual(1e7, g["claim_scale"])

    def test_units_read_by_the_number_pattern_use_the_written_precision_too(self):
        """『1,234.5百万円』『1,234.5千円』は金額の漢数字の読みでなく数字+単位の読み(単位が百万円・千円)。scale は単位の倍率でなく書かれた精度(0.1 百万円・0.1 千円)。
        fact 1,234,950,000 円: 差 0.45 百万円は P26 の帯(±0.5 百万円)の中、P27 の帯(±0.05 百万円)の外。"""
        for unit, num, fact_value, scale26, scale27 in (("百万円", "1,234.5", 1234950000, 1e6, 1e5), ("千円", "1,234.5", 1234950, 1e3, 1e2)):
            facts = [fact("NetSales", CUR, fact_value)]
            s = "売上高は%s%sとなりました。" % (num, unit)
            c26 = the(num_claims("P26", s, facts), unit)
            c27 = the(num_claims("P27", s, facts), unit)
            self.assertEqual(scale26, c26["claim_scale"], unit)
            self.assertEqual(scale27, c27["claim_scale"], unit)
            self.assertEqual("GROUNDED", c26["result"], unit)
            self.assertNotEqual("GROUNDED", c27["result"], unit)

    def test_a_wide_miss_is_grounded_in_p26_only(self):
        """封 §1-1 の当たる例: fact 12.7 億円・文『12.3億円』は、P26 では |0.4| ≤ 0.5 億で一致、P27 では 0.4 > 0.05 億で一致しない。"""
        facts = [fact("NetSales", CUR, 1270000000)]
        self.assertEqual("GROUNDED", the(num_claims("P26", "売上高は12.3億円となりました。", facts))["result"])
        self.assertNotEqual("GROUNDED", the(num_claims("P27", "売上高は12.3億円となりました。", facts))["result"])
        near = [fact("NetSales", CUR, 1234000000)]                     # |12.34 − 12.3| = 0.04 億 ≤ 0.05 億 は一致のまま
        self.assertEqual("GROUNDED", the(num_claims("P27", "売上高は12.3億円となりました。", near))["result"])
        self.assertEqual("GROUNDED", the(num_claims("P26", "売上高は12.3億円となりました。", near))["result"])

    def test_a_number_without_a_decimal_part_is_the_same_in_p26_and_p27(self):
        for p in ("P26", "P27", "P27E"):
            c = the(num_claims(p, "売上高は8億円となりました。", [fact("NetSales", CUR, 820000000)]))
            self.assertEqual(1e8, c["claim_scale"], p)
            self.assertEqual("GROUNDED", c["result"], p)        # |8.2 − 8| = 0.2 億 ≤ 0.5 億

    def test_direct_call_with_no_precision_keeps_the_unit_scale(self):
        """``_direct_value_claim`` は prec が None のまま呼べる(試験の補助の呼び方)。旗が真でも scale は単位の倍率のまま。"""
        sentence = "売上高は9億円となりました。"
        a = sentence.index("9")
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        R._direct_value_claim(claim, sentence, a, a + 3, 1, 9.0, "億円", None, "売上高", ["NetSales"], None, NS, contexts_for(NS), V.P27)
        self.assertEqual(1e8, claim["claim_scale"])

    def test_the_older_profiles_never_read_the_written_precision(self):
        for p in ("P22", "P25", "P26"):
            self.assertEqual(1e8, the(num_claims(p, "売上高は8.25億円となりました。", NS))["claim_scale"], p)

    def test_the_text_claim_amounts_keep_the_old_reader(self):
        """向きの語の金額(A1)は ``E.iter_numbers`` を直接呼ぶので A の精度は効かない(封 §1-1・§2-2 の 10)。"""
        src = inspect.getsource(R._direction_amount_check)
        self.assertIn("E.iter_numbers(", src)
        self.assertNotIn("2026_10_27", src)


# ====================================================================================================
def named_claim(rho_case, p="P27E"):
    return the(num_claims(p, "売上高は%s億円となりました。" % rho_case, NS))


class BRelativeTest(unittest.TestCase):
    """B(封 §1-2)。P27E だけ。"""

    def test_hit_example_names_the_original_value(self):
        """封の当たる例: 文 9.1 億円・当期の fact 8.2 億円・証拠なし -> 11.0% ≤ 15% で名指して原本の値を返す。"""
        c = named_claim("9.1")
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"])
        self.assertTrue(c["bound"])
        self.assertEqual(820000000.0, c["recomputed"])
        self.assertEqual(VM_REASON, c["reason"])
        self.assertEqual("relative_within_rho", c["last_branch_evidence"])
        for k in ("no_same_value", "last_branch_digit_floor"):
            self.assertNotIn(k, c)

    def test_same_example_in_p27_and_p26(self):
        c27 = the(num_claims("P27", "売上高は9.1億円となりました。", NS))
        self.assertIsNone(c27["result"])
        self.assertEqual(R.NO_SAME_VALUE, c27["reason"])
        self.assertEqual({"named": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "value": 820000000.0}, c27["no_same_value"])
        self.assertIsNone(c27["last_branch_evidence"])
        c26 = the(num_claims("P26", "売上高は9.1億円となりました。", NS))
        self.assertEqual("VALUE_MISMATCH", c26["result"])                 # P26 は帯が広く (ii) で名指す(測った事実 §0-2)
        self.assertEqual("digit_within_k", c26["last_branch_evidence"])

    def test_not_hit_when_the_difference_is_large(self):
        """封の当たらない例: 文 11.5 億円・fact 8.2 億円(40%)-> no_same_value。"""
        c = named_claim("11.5")
        self.assertIsNone(c["result"])
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["recomputed"])
        self.assertEqual(R.NO_SAME_VALUE, c["reason"])
        self.assertEqual({"named": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "value": 820000000.0}, c["no_same_value"])
        self.assertIsNone(c["last_branch_evidence"])

    def test_the_rho_boundary(self):
        """ρ = 0.15 の両側と境目(10%/12% は名指す、15% ちょうどは名指す、18% は名指さない)。"""
        facts = [fact("NetSales", CUR, 1000)]
        for target, named in ((1100, True), (1120, True), (1150, True), (1151, False), (1180, False), (850, True), (840, False)):
            claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
            got = R._last_branch_decide_2026_10_27(claim, float(target), 1.0, None, False, facts[0], facts)
            self.assertTrue(got, target)
            self.assertEqual(named, claim["result"] == "VALUE_MISMATCH", target)
            self.assertEqual(not named, claim["reason"] == R.NO_SAME_VALUE, target)
            self.assertEqual("relative_within_rho" if named else None, claim["last_branch_evidence"], target)

    def test_the_relative_difference_is_taken_on_absolute_values(self):
        """||名指す値| − |文の値|| なので、符号が違っても(損失を利益と書いた等)絶対値の近さで見る。"""
        facts = [fact("NetSales", CUR, -1000)]
        for target in (1100.0, -1100.0):
            claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
            self.assertTrue(R._last_branch_decide_2026_10_27(claim, target, 1.0, None, False, facts[0], facts))
            self.assertEqual("VALUE_MISMATCH", claim["result"], target)
            self.assertEqual(-1000.0, claim["recomputed"], target)
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        self.assertTrue(R._last_branch_decide_2026_10_27(claim, -1300.0, 1.0, None, False, facts[0], facts))
        self.assertEqual(R.NO_SAME_VALUE, claim["reason"])

    def test_evidence_present_returns_false_and_writes_nothing(self):
        """(i) 同じ要素・同じ枠の別の期に同じ値: この関数は何もせず False(下の G2・P25 の行が今までどおり名指す)。"""
        facts = [fact("NetSales", CUR, 820000000), fact("NetSales", PRI, 910000000)]
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        before = dict(claim)
        self.assertFalse(R._last_branch_decide_2026_10_27(claim, 910000000.0, 1e7, None, False, facts[0], facts))
        self.assertEqual(before, claim)
        # 文の通り: P27E は P27 と同じ claim を作る(前期の値が合うので名指しの理由は P25 の証拠 (i))
        s = "売上高は9.1億円となりました。"
        a = the(num_claims("P27", s, facts))
        b = the(num_claims("P27E", s, facts))
        self.assertEqual(VM_REASON, a["reason"])
        self.assertEqual(a, {k: v for k, v in b.items()})
        self.assertEqual("same_element:%s" % PRI, b["last_branch_evidence"])

    def test_digit_floor_is_kept_like_g2(self):
        """(ii) は名指す値が 2 × 主張の桁 より小さいときは証拠にしない(G2 の字のまま)。小さい値は (iii) だけ見直し、無ければ no_same_value か相対。"""
        facts = [fact("NetSales", CUR, 1)]
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        self.assertTrue(R._last_branch_decide_2026_10_27(claim, 3.0, 1.0, None, False, facts[0], facts))
        self.assertEqual(R.NO_SAME_VALUE, claim["reason"])          # (ii) の d=2 ≤ 2 だが |1| < 2 なので証拠にしない。相対は 200%
        self.assertTrue(claim["last_branch_digit_floor"])
        self.assertIsNone(claim["last_branch_evidence"])
        big = [fact("NetSales", CUR, 5)]
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        self.assertFalse(R._last_branch_decide_2026_10_27(claim, 7.0, 1.0, None, False, big[0], big))      # |5| ≥ 2 なので (ii) が証拠
        self.assertEqual({"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}, claim)

    def test_scale_evidence_iii_is_checked_after_the_floor(self):
        """名指す値が小さくて (ii) を数えないときも、桁・単位の取り違え (iii) は見る(10^n)。"""
        facts = [fact("NetSales", CUR, 1)]
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        self.assertFalse(R._last_branch_decide_2026_10_27(claim, 10.0, 1.0, None, False, facts[0], facts))
        self.assertNotIn("last_branch_digit_floor", claim)

    def test_no_flag_means_the_p26_output(self):
        for s in ("売上高は9.1億円となりました。", "売上高は11.5億円となりました。", "売上高は8.2億円となりました。"):
            a = num_claims(V.P27, s, NS)
            b = num_claims(P27E_OFF, s, NS)
            c = num_claims(dataclasses.replace(V.P27E, name="x", written_precision_2026_10_27=False, last_branch_relative_2026_10_27=False), s, NS)
            d = num_claims("P26", s, NS)
            self.assertEqual(d, b, s)
            self.assertEqual(d, c, s)
            self.assertEqual(len(d), len(a), s)

    def test_p27_never_names_by_relative_closeness(self):
        for s in ("売上高は9.1億円となりました。", "売上高は8.9億円となりました。"):
            self.assertNotIn("relative_within_rho", [c.get("last_branch_evidence") for c in num_claims("P27", s, NS)], s)

    def test_g1_still_stops_a_named_per_share_fact(self):
        """名指した後も G1(概念の門)は当たる: 総額の主語に 1 株当たりの fact を名指したら other_concept。"""
        facts = [fact("NetSales", CUR, 820000000, unit="JPYPerShares")]
        c = the(gated("P27E", "売上高は9.1億円となりました。", facts))
        self.assertIsNone(c["result"])
        self.assertEqual(R.OTHER_CONCEPT, c["reason"])
        self.assertTrue(c["concept_gate"].startswith("unit_family"))
        self.assertEqual("relative_within_rho", c["last_branch_evidence"])
        plain = the(gated("P27E", "売上高は9.1億円となりました。", NS))
        self.assertEqual("VALUE_MISMATCH", plain["result"])

    def test_the_branch_sits_after_human_decision_rows_and_before_g2(self):
        """配置: 最後の枝の B の呼び出しは、P26 G3・F3b(人間の決定の行を含む)の後ろ、P26 G2 の行の前(封 §1-2・§2-2 の 2)。"""
        src = inspect.getsource(R._direct_value_claim)
        i_b = src.index("_last_branch_decide_2026_10_27(")
        self.assertGreater(i_b, src.index("# F3b: 増減の文が当期の残高を選んだときは"))
        self.assertGreater(i_b, src.index('ROUNDED_DIFF_HOLD'))
        self.assertGreater(i_b, src.index("no_element(no prior2 for prior-year diff)"))
        self.assertLess(i_b, src.index("_last_branch_unname_2026_10_21("))
        self.assertLess(i_b, src.index("_last_branch_unname(claim"))


# ====================================================================================================
BATTERY_PER = ["EPSは前期の120.5円に対し98.2円となりました。", "1株当たり配当は30円、配当金の総額は5.1億円となりました。",
               "売上高は188億円となりました。", "BPSは1,200円となりました。"]


def hand_claim(sentence, number, unit, **kw):
    """合成の数の claim(``_p27_gate`` を単独で当てる)。pos は文の中の数の開始。"""
    c = {"id": "N001", "sentence": 0, "pos": sentence.index(number), "value": 0.0, "unit": unit, "subject": "売上高", "form": "direct_value",
         "pointer": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 1.0, "match": "round"}
    c.update(kw)
    return c


class C1PerShareWindowTest(unittest.TestCase):
    """C1(封 §1-3)。"""

    def mark(self, sentence, number, unit="円", profile=V.P27, **kw):
        c = hand_claim(sentence, number, unit, **kw)
        R._p27_gate(c, [sentence], contexts_for([]), profile)
        return c

    def test_marks_a_money_number_with_the_word_in_the_window(self):
        for s, n in (("EPSは前期の120.5円に対し98.2円となりました。", "98.2"), ("1株当たりの当期純利益は98.2円となりました。", "98.2"),
                     ("BPSは1,200円となりました。", "1,200")):
            self.assertTrue(self.mark(s, n).get("per_share_window_2026_10_27"), s)

    def test_does_not_mark_without_the_word_or_outside_the_window(self):
        self.assertNotIn("per_share_window_2026_10_27", self.mark("売上高は188億円となりました。", "188", "円"))
        self.assertNotIn("per_share_window_2026_10_27", self.mark("純資産は188億円となりました。", "188", "円"))

    def test_the_window_is_exactly_twenty_characters(self):
        """『株当たり』の開始が数の 20 字手前なら窓の中(印)、21 字手前なら窓の外(『株当たり』の 1 字目が窓から出る)。"""
        for filler, want in ((16, True), (17, False)):
            s = "株当たり" + "あ" * filler + "98.2円となりました。"
            self.assertEqual(want, self.mark(s, "98.2").get("per_share_window_2026_10_27", False), filler)
        s = "EPS" + "あ" * 17 + "98.2円"
        self.assertTrue(self.mark(s, "98.2").get("per_share_window_2026_10_27"))
        s = "EPS" + "あ" * 18 + "98.2円"
        self.assertFalse(self.mark(s, "98.2").get("per_share_window_2026_10_27", False))

    def test_only_the_yen_family_units_are_marked(self):
        for unit, number, s in (("%", "5.2", "1株当たり利益は前期比5.2%増"), ("人", "240", "1株当たりの従業員は240人")):
            self.assertNotIn("per_share_window_2026_10_27", self.mark(s, number, unit), unit)

    def test_flag_false_marks_nothing(self):
        for p in (V.P26, only("per_unit_counter_2026_10_27"), P27_OFF):
            self.assertNotIn("per_share_window_2026_10_27", self.mark("EPSは98.2円となりました。", "98.2", profile=p))

    def test_g1_hit_example_stops_the_total_fact_as_other_concept(self):
        """封の当たる例: 『EPSは…98.2円』の 98.2 円が、主語『売上高』(総額の fact・単位 JPY)に名指されて VALUE_MISMATCH -> other_concept。"""
        facts = [fact("NetSales", CUR, 98.13)]           # 総額の fact(単位 JPY)。書かれた精度 0.1 円の帯(丸め ±0.05・切り捨て 0〜0.1)の外で、差 0.07 円は (ii) の証拠になる -> P27 でも名指す
        c = the(gated("P27", "売上高のEPSは98.2円となりました。", facts), "円")
        self.assertIsNone(c["result"])
        self.assertEqual(R.OTHER_CONCEPT, c["reason"])
        self.assertTrue(c["per_share_window_2026_10_27"])
        self.assertTrue(c["concept_gate"].startswith("unit_family:JPY/per_share_subject"))
        # C1 の旗だけ偽なら窓の印は付かず、今までどおり VALUE_MISMATCH(P26 は帯が広く、この fact を一致にする)
        no_c1 = the(gated(dataclasses.replace(V.P27, name="P27_noC1", per_share_window_2026_10_27=False), "売上高のEPSは98.2円となりました。", facts), "円")
        self.assertEqual("VALUE_MISMATCH", no_c1["result"])
        self.assertNotIn("per_share_window_2026_10_27", no_c1)
        self.assertEqual("GROUNDED", the(gated("P26", "売上高のEPSは98.2円となりました。", facts), "円")["result"])

    def test_g1_does_not_touch_a_grounded_row(self):
        """当たらない例: 同じ数が GROUNDED の行(窓に語があっても一致の行には触らない)。"""
        facts = [fact("NetSales", CUR, 98)]
        c = the(gated("P27", "売上高のEPSは98円となりました。", facts), "円")
        self.assertEqual("GROUNDED", c["result"])
        self.assertTrue(c["per_share_window_2026_10_27"])

    def test_costly_example_a_real_mismatch_after_a_per_share_word_is_weakened(self):
        """代価(封 §1-3): 『1株当たり配当は30円、配当金の総額は5.1億円』の 5.1 億円が VALUE_MISMATCH なら、窓に『株当たり』が入るので other_concept に止まる。"""
        s = "1株当たり配当は30円、売上高は5.1億円となりました。"
        facts = [fact("NetSales", CUR, 503000000)]
        c = [x for x in gated("P27", s, facts) if x["unit"] == "円" and x["value"] > 1e6][0]
        self.assertTrue(c["per_share_window_2026_10_27"])
        self.assertIsNone(c["result"])
        self.assertEqual(R.OTHER_CONCEPT, c["reason"])
        no_c1 = [x for x in gated(dataclasses.replace(V.P27, name="P27_noC1", per_share_window_2026_10_27=False), s, facts)
                 if x["unit"] == "円" and x["value"] > 1e6][0]
        self.assertEqual("VALUE_MISMATCH", no_c1["result"])
        self.assertNotIn("per_share_window_2026_10_27", no_c1)

    def test_g1_reads_the_mark_only_where_per_share_subject_is_decided(self):
        """印が真なら per_share_subject を真にする 2 行の効き: 総額の fact(JPY)で食い違い、1 株当たりの fact(JPYPerShares)なら食い違わない。"""
        c = {"pointer": "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "unit": "円", "subject": "売上高", "per_share_window_2026_10_27": True}
        by_total = {("jppfs_cor:NetSales", "CurrentYearDuration"): {"unit": "JPY"}}
        by_share = {("jppfs_cor:NetSales", "CurrentYearDuration"): {"unit": "JPYPerShares"}}
        self.assertTrue((R._concept_gate_why(c, None, by_total, ("unit_family",)) or "").startswith("unit_family"))
        self.assertIsNone(R._concept_gate_why(c, None, by_share, ("unit_family",)))
        c2 = dict(c)
        del c2["per_share_window_2026_10_27"]
        self.assertIsNone(R._concept_gate_why(c2, None, by_total, ("unit_family",)))
        self.assertTrue((R._concept_gate_why(c2, None, by_share, ("unit_family",)) or "").startswith("unit_family"))


# ====================================================================================================
class C2PerUnitCounterTest(unittest.TestCase):
    """C2(封 §1-4)。"""

    def gate(self, sentence, number, unit, profile=V.P27, **kw):
        c = hand_claim(sentence, number, unit, **kw)
        R._p27_gate(c, [sentence], contexts_for([]), profile)
        return c

    def test_hit_examples_clear_the_binding_and_become_per_unit_counter(self):
        for s, n, u in (("1人当たり売上高は5億円となりました。", "1", "人"), ("1株当たり利益は132円となりました。", "1", "株")):
            c = self.gate(s, n, u)
            self.assertIsNone(c["pointer"])
            self.assertFalse(c["bound"])
            self.assertIsNone(c["recomputed"])
            self.assertIsNone(c["result"])
            self.assertNotIn("match", c)
            self.assertEqual("per_unit_counter", c["reason"])
            self.assertEqual("per_unit_counter", c["p27_gate"])
            self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]))

    def test_the_stale_binding_keys_are_cleared_too(self):
        """前の束縛を説明していた欄(名指さなかった fact・合った枠・最後の枝の証拠など)も消す: 消さないと Recipe の provenance に古い名指しが残る。"""
        stale = dict((k, "x") for k in R._P27_STALE_KEYS)
        c = self.gate("1人当たり売上高は5億円となりました。", "1", "人", **stale)
        for k in R._P27_STALE_KEYS:
            self.assertNotIn(k, c, k)
        self.assertEqual(("match", "no_same_value", "other_frame", "rounded_diff_hold", "last_branch_evidence", "last_branch_digit_floor", "ambiguous_count"),
                         R._P27_STALE_KEYS)

    def test_every_unit_and_both_spellings(self):
        for unit in R.PER_UNIT_COUNTER_UNITS:
            for after in R.PER_UNIT_COUNTER_AFTER:
                s = "1%s%s売上高は5億円となりました。" % (unit, after)
                c = self.gate(s, "1", unit)
                self.assertEqual("per_unit_counter", c["reason"], (unit, after))

    def test_end_to_end_numbers_are_read_with_the_real_reader(self):
        """読み取り(NUM_RE)を通した claim でも当たる: 1人当たり・1店舗当たり・1千株当たり・1台あたり。"""
        for s in ("1人当たり売上高は5億円。", "1店舗当たり売上高は5億円。", "1店当たり売上高は5億円。", "1千株当たり利益は5億円。", "1台あたり売上高は5億円。",
                  "1名当たり売上高は5億円。", "1社当たり売上高は5億円。", "1件当たり売上高は5億円。"):
            claims = gated("P27", s, NS)
            one = [c for c in claims if c["value"] == 1.0]
            self.assertEqual(1, len(one), s)
            self.assertEqual("per_unit_counter", one[0]["reason"], s)
            self.assertEqual("per_unit_counter", one[0]["p27_gate"], s)

    def test_not_hit_examples(self):
        """当たらない例: 『従業員数は240人』(後ろが『当たり』でない)・『1株につき』・『1人』の後ろが『当』だけ・単位が一覧に無い『倍』『%』『円』。"""
        for s, n, u in (("従業員数は240人となりました。", "240", "人"), ("1株につき30円を配当しました。", "1", "株"), ("1人当社の売上です。", "1", "人"),
                        ("1倍当たり売上高です。", "1", "倍"), ("1円当たり売上高です。", "1", "円"), ("5%当たり売上高です。", "5", "%"),
                        ("1人当た売上高です。", "1", "人")):
            c = self.gate(s, n, u)
            self.assertNotIn("p27_gate", c, s)
            self.assertEqual("GROUNDED", c["result"], s)
            self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration", c["pointer"], s)

    def test_flag_false_does_nothing_even_when_other_p27_flags_are_true(self):
        for p in (V.P26, P27_OFF, only("future_period_2026_10_27"), only("per_share_window_2026_10_27")):
            c = self.gate("1人当たり売上高は5億円となりました。", "1", "人", profile=p)
            self.assertNotIn("p27_gate", c)
            self.assertEqual("GROUNDED", c["result"])

    def test_a_target_or_plan_claim_is_not_touched(self):
        c = self.gate("1人当たり売上高の目標は5億円です。", "1", "人", reason="target_or_plan", result="UNVERIFIABLE", pointer=None, bound=False, recomputed=None)
        self.assertNotIn("p27_gate", c)
        self.assertEqual("target_or_plan", c["reason"])

    def test_it_applies_to_grounded_and_unbound_claims_alike(self):
        c = self.gate("1人当たり売上高は5億円となりました。", "1", "人", pointer=None, bound=False, result=None, recomputed=None, match=None, reason="no_element")
        self.assertEqual("per_unit_counter", c["reason"])

    def test_it_stops_at_c2_and_does_not_fall_through_to_c3(self):
        """『1人当たり』の『1』は数の主張ではないので、先の決算期の字があっても理由は per_unit_counter のまま(target_or_plan に上書きしない)。"""
        s = "2027年5月期の1人当たり売上高は5億円となりました。"
        c = hand_claim(s, "1人", "人")
        ctx = {"CurrentYearInstant": {"instant": "2026-05-31"}}
        R._p27_gate(c, [s], ctx, V.P27)
        self.assertEqual("per_unit_counter", c["reason"])
        self.assertEqual("per_unit_counter", c["p27_gate"])
        self.assertIsNone(c["result"])

    def test_registry_state_and_report_wording(self):
        self.assertIn("per_unit_counter", RS._UNVERIFIABLE_REASONS)
        self.assertNotIn("per_unit_counter", RS._POINTER_NOT_FOUND_REASONS)
        self.assertEqual((10, 10), (len(RS._POINTER_NOT_FOUND_REASONS), len(RS._UNVERIFIABLE_REASONS)))      # 19 -> 20
        self.assertEqual("UNVERIFIABLE", R._state_of("per_unit_counter", None))
        self.assertEqual("「1人当たり」「1株当たり」の「1」で、数の主張ではない", RC.REASON_JA["per_unit_counter"])
        self.assertNotIn("per_unit_counter", R.UNBOUND_REASON_STATE)
        with self.assertRaises(KeyError):
            R._state_of("per_unit_counter_x", None)

    def test_a_per_unit_counter_claim_becomes_a_recipe_without_pointers(self):
        sentence = "1人当たり売上高は5億円となりました。"
        c = the(gated("P27", sentence, NS), "人")
        self.assertEqual("per_unit_counter", c["reason"])
        rec = R.claim_to_recipe(c, "num")
        self.assertEqual("per_unit_counter", rec.unverifiable_reason)
        self.assertEqual((), rec.pointers)
        self.assertIsNone(rec.contract)


# ====================================================================================================
CTX_2026_05 = {"CurrentYearInstant": {"instant": "2026-05-31"}}


class C3FuturePeriodTest(unittest.TestCase):
    """C3(封 §1-4)。"""

    def gate(self, sentence, number, unit, contexts=CTX_2026_05, profile=V.P27, **kw):
        c = hand_claim(sentence, number, unit, **kw)
        R._p27_gate(c, [sentence], contexts, profile)
        return c

    def assertFuture(self, c):
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["recomputed"])
        self.assertEqual("UNVERIFIABLE", c["result"])
        self.assertEqual("target_or_plan", c["reason"])
        self.assertEqual("future_period", c["p27_gate"])
        self.assertNotIn("match", c)
        self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]))

    def test_hit_example_both_the_amount_and_the_percent(self):
        """封の当たる例: 当期末 2026-05-31 の書類で『2027年5月期の業績予想では営業収益を52億円(4.1%増)とする』の 52 億円と 4.1%。"""
        s = "2027年5月期の業績予想では営業収益を52億円(4.1%増)とする。"
        self.assertFuture(self.gate(s, "52", "円"))
        self.assertFuture(self.gate(s, "4.1", "%"))

    def test_the_stale_binding_keys_are_cleared_too(self):
        stale = dict((k, "x") for k in R._P27_STALE_KEYS)
        c = self.gate("2027年5月期の業績予想では営業収益を52億円とする。", "52", "円", **stale)
        for k in R._P27_STALE_KEYS:
            self.assertNotIn(k, c, k)
        self.assertEqual("future_period", c["p27_gate"])

    def test_not_hit_examples(self):
        """当たらない例: 当期『2026年5月期』・前期『2025年5月期』・年月期の字が無い『来期の予想は』。"""
        for s in ("2026年5月期の売上高は52億円となりました。", "2025年5月期の売上高は52億円となりました。", "来期の予想は営業収益を52億円とする。"):
            c = self.gate(s, "52", "円")
            self.assertNotIn("p27_gate", c, s)
            self.assertEqual("GROUNDED", c["result"], s)

    def test_the_comparison_is_year_then_month_and_strictly_later(self):
        for ym, want in (("2026年5月期", False), ("2026年6月期", True), ("2026年12月期", True), ("2026年4月期", False),
                         ("2027年1月期", True), ("2025年12月期", False), ("2027年5月期", True)):
            c = self.gate("%sの売上高は52億円となりました。" % ym, "52", "円")
            self.assertEqual(want, c.get("p27_gate") == "future_period", ym)

    def test_another_balance_date(self):
        ctx = {"CurrentYearInstant": {"instant": "2026-12-31"}}
        self.assertEqual("future_period", self.gate("2027年1月期の売上高は52億円です。", "52", "円", contexts=ctx).get("p27_gate"))
        self.assertNotIn("p27_gate", self.gate("2026年12月期の売上高は52億円です。", "52", "円", contexts=ctx))

    def test_the_last_period_before_the_number_decides(self):
        """『最後の』年月期: 先の期の字の後ろに当期の字が続けば当期の数(当たらない)、逆なら先の期の数(当たる)。"""
        a = self.gate("2027年5月期は増収を見込む。2026年5月期の売上高は52億円となりました。", "52", "円")
        self.assertNotIn("p27_gate", a)
        b = self.gate("2026年5月期は52億円で、2027年5月期は60億円を見込む。", "60", "円")
        self.assertEqual("future_period", b["p27_gate"])
        c = self.gate("2026年5月期は52億円で、2027年5月期は60億円を見込む。", "52", "円")
        self.assertNotIn("p27_gate", c)                    # 52 の手前には 2026年5月期 しか無い

    def test_costly_example_a_current_result_after_a_future_period_is_also_stopped(self):
        """代価(封 §1-4): 『2027年5月期の予想は…で、当期の営業利益は5.9億円』のように、先の期の字の後ろに同じ文で当期の実績が続くと、実績の数も UNVERIFIABLE。"""
        s = "2027年5月期の予想は60億円で、当期の営業利益は5.9億円となりました。"
        self.assertFuture(self.gate(s, "5.9", "円"))

    def test_no_current_instant_context_means_no_rule(self):
        s = "2027年5月期の業績予想では営業収益を52億円とする。"
        for ctx in ({}, {"CurrentYearInstant": {"instant": None}}, {"CurrentYearInstant": {}}, {"Prior1YearInstant": {"instant": "2025-05-31"}}):
            self.assertNotIn("p27_gate", self.gate(s, "52", "円", contexts=ctx))

    def test_only_the_text_before_the_number_is_read(self):
        s = "売上高は52億円で、2027年5月期の予想は60億円。"
        self.assertNotIn("p27_gate", self.gate(s, "52", "円"))

    def test_flag_false_and_target_or_plan_claims(self):
        s = "2027年5月期の業績予想では営業収益を52億円とする。"
        for p in (V.P26, P27_OFF, only("per_unit_counter_2026_10_27"), only("per_share_window_2026_10_27")):
            self.assertNotIn("p27_gate", self.gate(s, "52", "円", profile=p))
        c = self.gate(s, "52", "円", reason="target_or_plan", result="UNVERIFIABLE", pointer=None, bound=False, recomputed=None)
        self.assertNotIn("p27_gate", c)

    def test_the_registered_name_is_the_existing_one_and_no_new_reason_is_added_for_c3(self):
        self.assertEqual("UNVERIFIABLE", R.UNBOUND_REASON_STATE["target_or_plan"])
        self.assertIn("target_or_plan", RS._UNVERIFIABLE_REASONS)
        self.assertEqual("目標・計画の数(実績ではない)", RC.REASON_JA["target_or_plan"])


# ====================================================================================================
class FlagFalseIsP26Test(unittest.TestCase):
    """旗が偽なら P26 と同じ出力(合成の文の束)。"""

    SENTENCES = ["売上高は9.1億円となりました。", "売上高は8.2億円となりました。", "売上高は8.25億円となりました。", "売上高は11.5億円となりました。",
                 "1人当たり売上高は5億円となりました。", "1株当たり利益は132.47円となりました。", "2027年5月期の業績予想では営業収益を52億円(4.1%増)とする。",
                 "EPSは前期の120.5円に対し98.2円となりました。", "1株当たり配当は30円、配当金の総額は5.1億円となりました。",
                 "売上高は1,234.5百万円、営業利益は148円22銭となりました。"]

    def test_p27_off_and_p27e_off_equal_p26(self):
        ctx = dict(contexts_for(NS), **CTX_2026_05)
        for s in self.SENTENCES:
            want = gated("P26", s, NS, ctx)
            self.assertEqual(want, gated(P27_OFF, s, NS, ctx), s)
            self.assertEqual(want, gated(P27E_OFF, s, NS, ctx), s)

    def test_each_single_flag_only_changes_what_it_owns(self):
        ctx = dict(contexts_for(NS), **CTX_2026_05)
        for flag in FLAGS:
            p = only(flag)
            for s in self.SENTENCES:
                got, base = gated(p, s, NS, ctx), gated("P26", s, NS, ctx)
                self.assertEqual(len(base), len(got), (flag, s))            # 旗 1 つで claim の数は変わらない
        # C2 だけ: C2 に当たる claim 以外は P26 と同じ
        for s in self.SENTENCES:
            got, base = gated(only("per_unit_counter_2026_10_27"), s, NS, ctx), gated("P26", s, NS, ctx)
            for g, b in zip(got, base):
                if g.get("p27_gate") != "per_unit_counter":
                    self.assertEqual(b, g, s)
        # C3 だけ
        for s in self.SENTENCES:
            got, base = gated(only("future_period_2026_10_27"), s, NS, ctx), gated("P26", s, NS, ctx)
            for g, b in zip(got, base):
                if g.get("p27_gate") != "future_period":
                    self.assertEqual(b, g, s)

    def test_the_gate_is_not_called_when_no_flag_is_true(self):
        """build_raw_claims の配線(ast): _p27_gate の呼び出しは 3 つの旗の or の下にあり、G4 の後・G1 の前。"""
        tree = ast.parse(inspect.getsource(R.build_raw_claims))
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", None)
                if name in ("_cause_item_gate", "_p27_gate", "_concept_gate"):
                    calls.append((node.lineno, name))
        names = [n for _l, n in sorted(calls)]
        self.assertEqual(["_cause_item_gate", "_p27_gate", "_concept_gate"], names)
        src = inspect.getsource(R.build_raw_claims)
        head = src[src.index("_p27_gate") - 700:src.index("_p27_gate")]
        for f in ("per_share_window_2026_10_27", "per_unit_counter_2026_10_27", "future_period_2026_10_27"):
            self.assertIn(f, head)
        self.assertIn("for c in num_claims:", head)

    def test_the_claim_building_stage_is_untouched(self):
        """数の claim を作る段(_target_or_plan の行。人間の決定)の字は変えない: 段の中に P27 の語が無い。"""
        src = inspect.getsource(R._build_raw_num_claims)
        self.assertIn("if _target_or_plan(s, a, b, profile):", src)
        self.assertNotIn("2026_10_27", src)
        self.assertNotIn("p27", src)

    def test_the_human_decision_rows_do_not_name_p27(self):
        for fn in (R._target_or_plan, R._prior_cue, R._prior_cue_clause, R._mag_trunc, R.pct_tolerance):
            self.assertNotIn("2026_10_27", inspect.getsource(fn), fn.__name__)


# ====================================================================================================
#: 実物の書類(2026-10-27 時点の手元の cache の sha256。手元の 67 書類のうち。評価用の書類は使わない)。
DOCS = {
    "S100Z3HP": "a3170c66ce46185f02e8f5274c9d4f646ef97b089d13e6f7f4e65539e8d69719",      # C2 が 1 行(N049)
    "S100Z38F": "02358db58564bca3b19b58bb60b0cca0c01f2b8c305366a7ea1083ed1edd9d70",      # C2 が 8 行・C3 が 1 行(N024)・B が 1 行(N068)・C1 の窓が 2 行
    "S100Z35K": "53991c2cc3021f050fac8ff1f1c16a3b7f3c2c8cd1a923706977f0d1f4a403ed",      # C3 が 6 行・B が 1 行(N060)+ 名指した後に G1 で止まる 1 行(N069)
    "S100YYQX": "a0313840d8ecc13e8470e34f54451a0207c5510ffd0a9c3860e50c9640a9cdf0",      # B が 8 行
    "S100YMFV": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",      # C2 が 1 行(N082)・C1 の窓が 1 行(state は動かない)
}
_ZIPS = {}
_VERIFIED = {}


def zip_of(doc_id):
    """手元の cache の実物。無い・sha256 が違うときは失敗する(skip しない)。"""
    if doc_id not in _ZIPS:
        with open(os.path.join(CACHE, "%s.zip" % doc_id), "rb") as fh:
            data = fh.read()
        got = hashlib.sha256(data).hexdigest()
        if got != DOCS[doc_id]:
            raise ValueError("sha256 mismatch for %s: %s" % (doc_id, got))
        _ZIPS[doc_id] = data
    return _ZIPS[doc_id]


def verified(doc_id, profile):
    """``verify_document`` の claims を id で引ける形に(同じ書類・profile は 1 回だけ走らせる)。"""
    key = (doc_id, profile)
    if key not in _VERIFIED:
        _VERIFIED[key] = dict((c["id"], c) for c in VD.verify_document(zip_of(doc_id), profile)["claims"])
    return _VERIFIED[key]


def rowstate(c):
    return (c["state"], c["reason"], tuple(c["pointers"]))


def moved(doc_id, a, b):
    """profile a -> b で state・reason・pointers が違う id -> ((前), (後))。"""
    A, B = verified(doc_id, a), verified(doc_id, b)
    assert list(A) == list(B), doc_id
    return dict((i, (rowstate(A[i]), rowstate(B[i]))) for i in A if rowstate(A[i]) != rowstate(B[i]))


class RealDocumentWiringTest(unittest.TestCase):
    """build_raw_claims -> verify_document の配線(合成の試験が通らない所): 動いた行は封の予測のとおりの id・向きだけ。"""

    def test_c2_one_row_in_a_real_document(self):
        m = moved("S100Z3HP", "P26", "P27")
        self.assertEqual(["N049"], sorted(m))
        before, after = m["N049"]
        self.assertEqual(("POINTER_NOT_FOUND", "no_element", ()), before)
        self.assertEqual(("UNVERIFIABLE", "per_unit_counter", ()), after)
        self.assertEqual({}, moved("S100Z3HP", "P27", "P27E"))

    def test_c2_eight_rows_and_c3_one_row_in_another_document(self):
        m = moved("S100Z38F", "P26", "P27")
        c2 = sorted(i for i, (_a, b) in m.items() if b[1] == "per_unit_counter")
        c3 = sorted(i for i, (_a, b) in m.items() if b[1] == "target_or_plan")
        self.assertEqual(["N002", "N003", "N011", "N012", "N014", "N016", "N017", "N027"], c2)
        self.assertEqual(["N024"], c3)
        self.assertEqual(sorted(c2 + c3), sorted(m))
        for i, (a, b) in m.items():
            self.assertEqual("POINTER_NOT_FOUND", a[0], i)
            self.assertEqual("UNVERIFIABLE", b[0], i)
            self.assertEqual((), b[2], i)

    def test_c3_six_rows_in_a_document_with_a_forecast_paragraph(self):
        m = moved("S100Z35K", "P26", "P27")
        self.assertEqual(["N080", "N081", "N082", "N084", "N085", "N086"], sorted(m))
        for i, (a, b) in m.items():
            self.assertEqual("POINTER_NOT_FOUND", a[0], i)
            self.assertEqual(("UNVERIFIABLE", "target_or_plan", ()), b, i)

    def test_b_names_and_g1_still_stops_in_real_documents(self):
        m = moved("S100YYQX", "P27", "P27E")
        self.assertEqual(["N001", "N025", "N045", "N046", "N056", "N057", "N065", "N069"], sorted(m))
        for i, (a, b) in m.items():
            self.assertEqual(("POINTER_NOT_FOUND", "no_same_value", ()), a, i)
            self.assertEqual("VALUE_MISMATCH", b[0], i)
            self.assertTrue(b[2], i)                               # 名指した pointer が在る
        self.assertEqual({}, moved("S100YYQX", "P26", "P27"))      # P27 は P26 と同じ(この書類では A・C1・C2・C3 が当たらない)
        n = moved("S100Z35K", "P27", "P27E")
        self.assertEqual(["N060", "N069"], sorted(n))
        self.assertEqual("VALUE_MISMATCH", n["N060"][1][0])
        self.assertEqual(("POINTER_NOT_FOUND", "no_same_value", ()), n["N069"][0])
        self.assertEqual(("POINTER_NOT_FOUND", "other_concept", ()), n["N069"][1])          # 名指した後に G1 が止める

    def test_nothing_moves_to_grounded_or_value_mismatch_in_p27(self):
        for doc in DOCS:
            for i, (a, b) in moved(doc, "P26", "P27").items():
                self.assertNotEqual("GROUNDED", b[0], (doc, i))
                self.assertNotEqual("VALUE_MISMATCH", b[0], (doc, i))
                self.assertNotEqual("GROUNDED", a[0], (doc, i))

    def test_p27e_never_changes_a_grounded_row(self):
        for doc in DOCS:
            A, B = verified(doc, "P27"), verified(doc, "P27E")
            self.assertEqual([i for i in A if A[i]["state"] == "GROUNDED"], [i for i in B if B[i]["state"] == "GROUNDED"], doc)
            for i in A:
                if A[i]["state"] == "GROUNDED":
                    self.assertEqual(rowstate(A[i]), rowstate(B[i]), (doc, i))

    def test_raw_claims_carry_the_gate_marks_and_the_counts_are_what_was_measured(self):
        nums, _t = R.build_raw_claims(zip_of("S100Z38F"), V.P27)
        self.assertEqual(8, sum(1 for c in nums if c.get("p27_gate") == "per_unit_counter"))
        self.assertEqual(1, sum(1 for c in nums if c.get("p27_gate") == "future_period"))
        self.assertEqual(2, sum(1 for c in nums if c.get("per_share_window_2026_10_27")))
        nums_e, _t = R.build_raw_claims(zip_of("S100Z38F"), V.P27E)
        self.assertEqual(1, sum(1 for c in nums_e if c.get("last_branch_evidence") == "relative_within_rho"))
        self.assertEqual(0, sum(1 for c in nums if c.get("last_branch_evidence") == "relative_within_rho"))
        # C1: 窓に入った行はあるが、state は動かない(P27 で止めた行 0)
        nums1, _t = R.build_raw_claims(zip_of("S100YMFV"), V.P27)
        self.assertEqual(1, sum(1 for c in nums1 if c.get("per_share_window_2026_10_27")))
        self.assertEqual(0, sum(1 for c in nums1 if c.get("per_share_window_2026_10_27") and c.get("reason") == R.OTHER_CONCEPT))

    def test_with_every_flag_false_the_raw_claims_equal_p26_byte_for_byte(self):
        for doc in DOCS:
            a = R.build_raw_claims(zip_of(doc), V.P26)
            self.assertEqual(a, R.build_raw_claims(zip_of(doc), P27_OFF), doc)
            self.assertEqual(a, R.build_raw_claims(zip_of(doc), P27E_OFF), doc)

    def test_the_recipes_are_valid_for_the_core_and_the_new_reason_is_registered(self):
        out = VD.verify_document(zip_of("S100Z3HP"), "P27")
        got = [c for c in out["claims"] if c["id"] == "N049"][0]
        self.assertEqual("UNVERIFIABLE", got["state"])
        self.assertEqual("per_unit_counter", got["reason"])


if __name__ == "__main__":
    unittest.main()
