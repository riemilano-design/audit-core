# -*- coding: utf-8 -*-
"""P24(語彙の登録と枠の取り直しの直し)の試験。封 docs/XBRL_VOCAB_SEAL_2026-10-21.md §1。

P24 = P23 + 旗 ``vocab_2026_10_21`` + 旗 ``frame_rebind``。段 1 では既定にしない(``DEFAULT_PROFILE`` = P22 のまま)。

* 旗 ``vocab_2026_10_21``: (1) 同じ節の前期の手がかり語に「前連結会計年度末残高」「前年は」「(前期␣」 (2) ポイントの前期の語に「(同」
  「前事業年度」「前事業年度末」 (3) 資金の主語の句 19 通り(当期と Prior1Year にだけ値で結ぶ) (4) CF 合計の文字の主張は前期の手がかりがあるときだけ
  Prior1Year の値そのものの符号で照合。
* 旗 ``frame_rebind``: 取った枠で値が合わず同じ要素の別の枠(当期)で合うとき、VALUE_MISMATCH をやめて UNVERIFIABLE
  (``other_frame`` / ``ambiguous(member)``)。**GROUNDED を作らない。pointer を付けない。**

**各挙動について「P24 で効く」と「P23 では従来どおり」を対にして留め、「当たる例」と「当たらない例」を実物の 1 行(コメントに出典)で置く。**
合成の instance(facts と contexts を直接組む)に、手元の cache の実物の書類(sha256 を固定。無ければ失敗。skip しない)を足す。通信しない。
"""
import dataclasses
import hashlib
import inspect
import os
import re
import unittest

import audit_core as core

from adapters.xbrl import instance as I
from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import resolve as RV
from adapters.xbrl import verify_document as VD
from adapters.xbrl import vocabulary as V

from . import _material as M

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
PRI2 = "Prior2YearDuration"
CUR_I = "CurrentYearInstant"
PRI_I = "Prior1YearInstant"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

#: 実物の書類(2026-10-21 時点の手元の cache の sha256)。
DOCS = {
    "S100Z4DE": "5f154b2a5ba081abe7495fabc2cf6aae795cf92b1ad02808954d2befe424aa43",
    "S100YYS4": "02fcaa9a52e52943108f905abc115daea2243eba97bfdc5f56f51f783fe792de",
    "S100YYVN": "20d381114819b7608f4113d37fcd8920357a5da05f37f4542aaf6b5b3e92198d",
    "S100YXGH": "29b7eb0b24e579a5b2ae9ce664d58af2d1d3cd0ffe4aec23fd7a45bd7fc36cbf",
    "S100YYK8": "512b316c0739e2cb83c465ec7ffae4474efebf4ffbc234a70270346cf1e1caad",
    "S100YUHC": "cd212b810b33d07bd9723ed9518c299dcfaf88fc434f7026211206a9d5f6d450",
    "S100YWGX": "11a87aa7ddda60db6d51910decfbf8a643621e520f582ba920ecece743604cec",
    "S100YYQX": "a0313840d8ecc13e8470e34f54451a0207c5510ffd0a9c3860e50c9640a9cdf0",
}
_ZIPS = {}


def load_doc(doc_id):
    """手元の cache の実物。無い・sha256 が違うときは失敗する(skip しない)。"""
    if doc_id not in _ZIPS:
        path = os.path.join(CACHE, "%s.zip" % doc_id)
        with open(path, "rb") as fh:
            data = fh.read()
        got = hashlib.sha256(data).hexdigest()
        if got != DOCS[doc_id]:
            raise ValueError("sha256 mismatch for %s: %s" % (doc_id, got))
        _ZIPS[doc_id] = data
    return _ZIPS[doc_id]


def fact(name, ctx, value, unit="JPY", prefix="jppfs_cor:"):
    return {"name": prefix + name, "context": ctx, "unit": unit, "value": float(value)}


def contexts_for(facts, extra=None):
    d = {f["context"]: {"members": []} for f in facts}
    d.update(extra or {})
    return d


def prof(p):
    return V.PROFILES[p] if isinstance(p, str) else p


#: 旗を両方偽にした P24 = P23 と同じ(名前だけ違う)。
P24_OFF = dataclasses.replace(V.P24, name="P24_OFF", vocab_2026_10_21=False, frame_rebind=False)
P24_VOCAB_ONLY = dataclasses.replace(V.P23, name="P24_VOCAB_ONLY", vocab_2026_10_21=True)
P24_FRAME_ONLY = dataclasses.replace(V.P23, name="P24_FRAME_ONLY", frame_rebind=True)


def num_claims(p, sentence, facts, contexts=None, member=None):
    """文 1 つの数の主張(raw)。``member`` は (member 名 or None) = 主張の枠。"""
    return R._build_raw_num_claims([sentence], facts, contexts if contexts is not None else contexts_for(facts), prof(p),
                                   lambda si, pos: (member, "test"))


def text_claims(p, sentence, facts, contexts=None, member=None):
    return R._build_raw_text_claims([sentence], facts, contexts if contexts is not None else contexts_for(facts), prof(p),
                                    lambda si, pos: (member, "test"))


def by_value(claims, value):
    """``value``(円または率・ポイントの字の値)で 1 件に絞る。主張の value は文の字の値のことも円に直した値のこともある(``claim_scale``)ので両方見る。"""
    def hits(c):
        v = c.get("value")
        if v is None:
            return False
        sc = c.get("claim_scale") or 1.0
        return any(abs(x - value) < 1e-6 * max(1.0, abs(value)) for x in (v, v * sc))
    got = [c for c in claims if hits(c)]
    assert len(got) == 1, [(c["id"], c.get("value"), c.get("claim_scale")) for c in claims]
    return got[0]


def call(p, sentence, number, unit, subj, elems, facts, member=None, sign=1):
    """``_direct_value_claim`` を直接呼ぶ(P22 の試験と同じ呼び方)。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
    R._direct_value_claim(claim, sentence, a, b, sign, float(number.replace(",", "")), unit, None, subj, elems, member,
                          facts, contexts_for(facts), prof(p))
    return claim


# ====================================================================================================
class FlagShapeTest(unittest.TestCase):
    def test_p24_is_p23_plus_exactly_the_two_flags(self):
        self.assertEqual(dataclasses.replace(V.P23, name="P24", vocab_2026_10_21=True, frame_rebind=True), V.P24)
        self.assertIs(V.PROFILES["P24"], V.P24)

    def test_the_flags_are_false_by_default_and_for_every_other_profile(self):
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        self.assertIs(False, fields["vocab_2026_10_21"].default)
        self.assertIs(False, fields["frame_rebind"].default)
        # 2026-10-21 P25 = P24 + 旗 1 つ(封 XBRL_LASTBRANCH_SEAL_2026-10-21)は P24 の旗 2 つを引き継ぐ
        # 2026-10-22 P26 = P25 + 旗 5 つ(封 XBRL_P26_SEAL_2026-10-21)も引き継ぐ
        self.assertEqual(["P24", "P25", "P26"], sorted(n for n, p in V.PROFILES.items() if p.vocab_2026_10_21))
        self.assertEqual(["P24", "P25", "P26"], sorted(n for n, p in V.PROFILES.items() if p.frame_rebind))

    def test_with_both_flags_false_p24_is_p23(self):
        self.assertEqual(dataclasses.replace(V.P23, name="P24_OFF"), P24_OFF)

    def test_the_default_profile_is_still_p22_in_step_1(self):
        """段 1 では既定にしない(封 §1)。"""
        self.assertEqual("P22", V.DEFAULT_PROFILE)
        self.assertFalse(V.PROFILES[V.DEFAULT_PROFILE].vocab_2026_10_21)
        self.assertFalse(V.PROFILES[V.DEFAULT_PROFILE].frame_rebind)

    def test_other_frame_is_a_registered_unverifiable_reason(self):
        self.assertIn("other_frame", RS._UNVERIFIABLE_REASONS)
        self.assertIn("ambiguous(member)", RS._UNVERIFIABLE_REASONS)


# ====================================================================================================
# 旗が偽なら P23 と同一
BATTERY = [
    # (name, kind, sentence, facts, member)
    ("前連結会計年度末残高", "num", "当連結会計年度末における流動負債の残高は118億93百万円(前連結会計年度末残高78億51百万円)となり40億42百万円増加しました。",
     [fact("CurrentLiabilities", CUR_I, 11893000000), fact("CurrentLiabilities", PRI_I, 7851000000)], None),
    ("前年は", "num", "親会社株主に帰属する当期純利益は137,498千円(前年は68,147千円の親会社株主に帰属する当期純損失)となりました。",
     [fact("ProfitLossAttributableToOwnersOfParent", CUR, 137498000), fact("ProfitLossAttributableToOwnersOfParent", PRI, -68147000)], None),
    ("ポイント(前事業年度末)", "num", "この結果、自己資本比率については前事業年度末と比較して5.1ポイント上昇し、43.6%となりました。",
     [fact("EquityToAssetRatioSummaryOfBusinessResults", CUR_I, 0.436, "pure", "jpcrp_cor:"),
      fact("EquityToAssetRatioSummaryOfBusinessResults", PRI_I, 0.385, "pure", "jpcrp_cor:")], None),
    ("CF 合計の符号(前年同期は)", "text", "当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(前年同期は3,255,173千円の増加)。",
     [fact("NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults", CUR, 3334024000, prefix="jpcrp_cor:"),
      fact("NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults", PRI, 3255173000, prefix="jpcrp_cor:"),
      fact("NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults", PRI2, 4000000000, prefix="jpcrp_cor:")], None),
    ("枠の取り直し(直接)", "num", "売上高130,123百万円(前連結会計年度比9.2%増)となりました。",
     [fact("NetSales", CUR, 130123e6), fact("NetSales", PRI, 119000e6), fact("NetSales", "CurrentYearDuration_SegAMember", 50000e6),
      fact("NetSales", "Prior1YearDuration_SegAMember", 45000e6)], "SegAMember"),
]
FRAME_CONTEXTS = {"CurrentYearDuration_SegAMember": {"members": ["SegAMember"]}, "Prior1YearDuration_SegAMember": {"members": ["SegAMember"]},
                  "CurrentYearDuration_SegBMember": {"members": ["SegBMember"]}, "Prior1YearDuration_SegBMember": {"members": ["SegBMember"]}}


def run_battery(p, **kw):
    out = []
    for name, kind, s, facts, member in BATTERY:
        ctxs = contexts_for(facts, FRAME_CONTEXTS)
        fn = num_claims if kind == "num" else text_claims
        out.append((name, fn(p, s, facts, ctxs, member)))
    return out


class FlagsOffIsP23Test(unittest.TestCase):
    """旗が偽なら 1 行も変わらない(封 §1)。"""

    def test_every_battery_case_is_identical_to_p23_with_the_flags_off(self):
        self.assertEqual(run_battery("P23"), run_battery(P24_OFF))

    def test_the_battery_does_change_with_the_flags_on(self):
        """電池が空振りでないこと: 旗が真の P24 では電池のうち 5 件すべてが P23 と違う。"""
        a, b = dict(run_battery("P23")), dict(run_battery("P24"))
        self.assertEqual([n for n, *_ in BATTERY], [n for n in a if a[n] != b[n]])

    def test_a_real_document_is_identical_to_p23_with_the_flags_off(self):
        zb = M.load_zip_1()
        V.PROFILES["P24_OFF"] = P24_OFF
        try:
            off = VD.verify_document(zb, "P24_OFF")["claims"]
        finally:
            V.PROFILES.pop("P24_OFF", None)
        self.assertNotIn("P24_OFF", V.PROFILES)
        self.assertEqual(VD.verify_document(zb, "P23")["claims"], off)

    def test_each_flag_acts_alone(self):
        """語彙の旗だけでは枠の取り直しは起きず、枠の旗だけでは語彙の登録は効かない。"""
        name, kind, s, facts, member = BATTERY[4]
        ctxs = contexts_for(facts, FRAME_CONTEXTS)
        v_only = num_claims(P24_VOCAB_ONLY, s, facts, ctxs, member)
        f_only = num_claims(P24_FRAME_ONLY, s, facts, ctxs, member)
        base = num_claims("P23", s, facts, ctxs, member)
        self.assertEqual(base, v_only)
        self.assertTrue(f_only[0]["reason"].startswith("other_frame("))
        name, kind, s, facts, member = BATTERY[1]
        base = num_claims("P23", s, facts, None, member)
        self.assertEqual(base, num_claims(P24_FRAME_ONLY, s, facts, None, member))
        self.assertNotEqual(base, num_claims(P24_VOCAB_ONLY, s, facts, None, member))


# ====================================================================================================
class PriorCueWordsTest(unittest.TestCase):
    """(1) 同じ節の前期の手がかり語に「前連結会計年度末残高」「前年は」「(前期␣」を足す。"""

    # 実物: S100Z4DE N030(流動資産の語は label 由来なので、ここでは手書きの語 流動負債 に替えた)
    S_ZANDAKA = "当連結会計年度末における流動負債の残高は118億93百万円(前連結会計年度末残高78億51百万円)となり40億42百万円増加しました。"
    F_ZANDAKA = [fact("CurrentLiabilities", CUR_I, 11893000000), fact("CurrentLiabilities", PRI_I, 7851000000)]
    # 実物: S100YYS4 N008
    S_ZENNEN = "以上の結果、営業利益は191,612千円(前年比94.0%増)、親会社株主に帰属する当期純利益は137,498千円(前年は68,147千円の親会社株主に帰属する当期純損失)となりました。"
    F_ZENNEN = [fact("ProfitLossAttributableToOwnersOfParent", CUR, 137498000), fact("ProfitLossAttributableToOwnersOfParent", PRI, -68147000),
                fact("OperatingIncome", CUR, 191612000), fact("OperatingIncome", PRI, 98700000)]
    # 実物: S100YYVN N010
    S_ZENKI = "親会社株主に帰属する当期純損失3億40百万円(前期 親会社株主に帰属する当期純利益6億69百万円)となりました。"
    F_ZENKI = [fact("ProfitLossAttributableToOwnersOfParent", CUR, -340000000), fact("ProfitLossAttributableToOwnersOfParent", PRI, 669000000)]

    def assertGroundsPrior(self, c, name, ctx):
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:jppfs_cor:%s@%s" % (name, ctx), c["pointer"])

    def test_zandaka_ties_the_value_to_the_prior_year_instant_in_p24_only(self):
        n23 = by_value(num_claims("P23", self.S_ZANDAKA, self.F_ZANDAKA), 7851000000)
        n24 = by_value(num_claims("P24", self.S_ZANDAKA, self.F_ZANDAKA), 7851000000)
        self.assertEqual("VALUE_MISMATCH", n23["result"])
        self.assertEqual("xbrl:jppfs_cor:CurrentLiabilities@%s" % CUR_I, n23["pointer"])
        self.assertGroundsPrior(n24, "CurrentLiabilities", PRI_I)

    def test_zennen_wa_ties_the_value_to_the_prior_year_in_p24_only(self):
        n23 = by_value(num_claims("P23", self.S_ZENNEN, self.F_ZENNEN), 68147000)
        n24 = by_value(num_claims("P24", self.S_ZENNEN, self.F_ZENNEN), 68147000)
        self.assertEqual("VALUE_MISMATCH", n23["result"])
        self.assertGroundsPrior(n24, "ProfitLossAttributableToOwnersOfParent", PRI)

    def test_zenki_space_ties_the_value_to_the_prior_year_in_p24_only(self):
        n23 = by_value(num_claims("P23", self.S_ZENKI, self.F_ZENKI), 669000000)
        n24 = by_value(num_claims("P24", self.S_ZENKI, self.F_ZENKI), 669000000)
        self.assertEqual("VALUE_MISMATCH", n23["result"])
        self.assertGroundsPrior(n24, "ProfitLossAttributableToOwnersOfParent", PRI)

    def test_a_wrong_value_after_the_new_cue_is_not_grounded(self):
        """手がかりを足しても値が違えば GROUNDED にならない(前期の値でなければ止まる)。"""
        s = self.S_ZENNEN.replace("68,147", "69,147")
        n24 = by_value(num_claims("P24", s, self.F_ZENNEN), 69147000)
        self.assertEqual("VALUE_MISMATCH", n24["result"])

    # ---- 当たらない例
    def test_zenrenketsu_ni_is_not_a_cue(self):
        """「前連結会計年度に」は足さない(得 ≤ 1・代価 2)。実物の言い回し: 「前連結会計年度に比べ」「前連結会計年度にM&Aにより取得」。"""
        s = "当連結会計年度末における流動負債の残高は118億93百万円で、前連結会計年度に78億51百万円となり40億42百万円増加しました。"
        for p in ("P23", "P24"):
            n = by_value(num_claims(p, s, self.F_ZANDAKA), 7851000000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)
            self.assertEqual("xbrl:jppfs_cor:CurrentLiabilities@%s" % CUR_I, n["pointer"], p)

    def test_zenki_douki_is_not_a_cue(self):
        """「前期同期」は誤字に合わせない(封 §1)。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        for p in ("P23", "P24"):
            n = by_value(num_claims(p, "売上高は、前期同期は999千円となりました。", facts), 999000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)

    def test_zenki_without_a_space_is_not_the_new_cue(self):
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        for p in ("P23", "P24"):
            n = by_value(num_claims(p, "売上高は5,000千円(前期売上高999千円)となりました。", facts), 999000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)

    def test_the_cue_must_be_in_the_same_clause(self):
        """読点・句点で切れた後ろの節の数には前の節の手がかりは効かない。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        s = "前年は不振でした。売上高は999千円となりました。"
        for p in ("P23", "P24"):
            n = by_value(num_claims(p, s, facts), 999000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)

    def test_a_cue_inside_an_earlier_closed_parenthesis_does_not_count(self):
        """閉じた括弧の中の手がかりは、その後ろの数には効かない(既存の ``_prior_cue_clause`` と同じ切り方)。実物の形: 括弧の注記「(前年は…)」の後の数。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        s = "売上高は(前年は不振でした)が999千円となりました。"
        for p in ("P23", "P24"):
            n = by_value(num_claims(p, s, facts), 999000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)
        s_open = "売上高は、前年は不振で999千円となりました。"       # 括弧が無ければ同じ節の手がかりとして効く
        self.assertEqual("GROUNDED", by_value(num_claims("P24", s_open, facts), 999000)["result"])

    def test_the_period_bind_decision_is_kept_without_a_cue(self):
        """人間の決定 P22: 手がかりが無い数は前期の fact にだけ値が合っても GROUNDED にしない。P24 でも P22 と同じ。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        for p in ("P22", "P23", "P24"):
            n = by_value(num_claims(p, "売上高は999千円となった。", facts), 999000)
            self.assertEqual("VALUE_MISMATCH", n["result"], p)
            self.assertEqual("xbrl:jppfs_cor:NetSales@%s" % CUR, n["pointer"], p)

    def test_a_current_year_value_still_wins_when_both_periods_match(self):
        facts = [fact("NetSales", PRI, 999000), fact("NetSales", CUR, 999000)]
        n = by_value(num_claims("P24", "売上高は999千円となった。", facts), 999000)
        self.assertEqual("xbrl:jppfs_cor:NetSales@%s" % CUR, n["pointer"])

    # ---- 実物の書類
    def test_real_documents(self):
        want = {("S100Z4DE", "N030"): ("VALUE_MISMATCH", "Prior1YearInstant"),
                ("S100YYS4", "N008"): ("VALUE_MISMATCH", "Prior1YearDuration"),
                ("S100YYVN", "N010"): ("VALUE_MISMATCH", "Prior1YearDuration")}
        for (doc, cid), (before, ctx) in want.items():
            zb = load_doc(doc)
            c23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}[cid]
            c24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}[cid]
            self.assertEqual(before, c23["state"], (doc, cid))
            self.assertEqual("GROUNDED", c24["state"], (doc, cid))
            self.assertTrue(c24["pointers"][0].endswith("@" + ctx), (doc, cid, c24["pointers"]))


# ====================================================================================================
class PointPhraseTest(unittest.TestCase):
    """(2) ポイントの前期の語に「(同」「前事業年度」「前事業年度末」を足す。``_build_point_diff_claim`` は字を変えない。"""

    F = [fact("EquityToAssetRatioSummaryOfBusinessResults", CUR_I, 0.436, "pure", "jpcrp_cor:"),
         fact("EquityToAssetRatioSummaryOfBusinessResults", PRI_I, 0.385, "pure", "jpcrp_cor:")]
    PTR = ["xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@" + CUR_I, "xbrl:jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults@" + PRI_I,
           "formula:a-b(pure)"]
    NO_PHRASE = "no_element(point without prior phrase)"

    def point(self, p, s, value):
        return by_value(num_claims(p, s, self.F), value)

    def test_zenjigyonendo_matsu(self):
        # 実物: S100YXGH N080
        s = "この結果、自己資本比率については前事業年度末と比較して5.1ポイント上昇し、43.6%となりました。"
        self.assertEqual(self.NO_PHRASE, self.point("P23", s, 5.1)["reason"])
        c = self.point("P24", s, 5.1)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual(self.PTR, c["pointer"])

    def test_zenjigyonendo(self):
        s = "この結果、自己資本比率は前事業年度と比較して5.1ポイント上昇し、43.6%となりました。"
        self.assertEqual(self.NO_PHRASE, self.point("P23", s, 5.1)["reason"])
        self.assertEqual("GROUNDED", self.point("P24", s, 5.1)["result"])

    def test_dou(self):
        # 実物の形: S100Z37J N062「売上総利益率は、19.9%(同0.9ポイント増)」
        s = "この結果、自己資本比率は43.6%(同5.1ポイント増)となりました。"
        self.assertEqual(self.NO_PHRASE, self.point("P23", s, 5.1)["reason"])
        self.assertEqual("GROUNDED", self.point("P24", s, 5.1)["result"])

    def test_a_wrong_value_is_stopped_not_rubber_stamped(self):
        s = "この結果、自己資本比率については前事業年度末と比較して6.1ポイント上昇し、43.6%となりました。"
        c = self.point("P24", s, 6.1)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(self.PTR, c["pointer"])

    def test_the_direction_word_still_sets_the_sign(self):
        """向きの語(減少)は符号を負にする: 実際の差は +5.1 なので、減少と言う文は止まる。"""
        s = "この結果、自己資本比率については前事業年度末と比較して5.1ポイント減少し、43.6%となりました。"
        c = self.point("P24", s, -5.1)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(self.PTR, c["pointer"])

    # ---- 当たらない例
    def test_zenki_space_is_not_a_point_phrase(self):
        """(前期␣ は (1) の語で、(2) のポイントの語には足さない。"""
        s = "この結果、自己資本比率は43.6%(前期 5.1ポイント増)となりました。"
        for p in ("P23", "P24"):
            self.assertEqual(self.NO_PHRASE, self.point(p, s, 5.1)["reason"], p)

    def test_the_old_phrases_are_unchanged(self):
        for s in ("この結果、自己資本比率は前期比5.1ポイント上昇し、43.6%となりました。",
                  "この結果、自己資本比率は前連結会計年度に比べ5.1ポイント上昇し、43.6%となりました。"):
            a, b = self.point("P23", s, 5.1), self.point("P24", s, 5.1)
            self.assertEqual(a, b)
            self.assertEqual("GROUNDED", b["result"])

    def test_the_window_is_still_25_chars(self):
        """窓(数の手前 25 字)は変えない: 語がそれより手前なら足した語でも届かない。"""
        s = "この結果、自己資本比率は前事業年度" + "あ" * 25 + "5.1ポイント上昇し、43.6%となりました。"
        for p in ("P23", "P24"):
            self.assertEqual(self.NO_PHRASE, self.point(p, s, 5.1)["reason"], p)

    def test_the_human_decision_function_is_untouched(self):
        """C-1g §1-3 ``_build_point_diff_claim``: def 行・窓の if 行・呼び出しの行は 1 回ずつ、本体の sha16 は P23 のとき(7d530cc)と同じ。"""
        path = inspect.getsourcefile(R)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        lines = src.split("\n")
        for line in ("def _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol=PCT_TOLERANCE_DEFAULT):",
                     "    if not _POINT_PRIOR_PHRASE_RE.search(window):",
                     "            _build_point_diff_claim(claim, s, a, b, elems, member, facts, contexts, num, tol)"):
            self.assertEqual(1, lines.count(line), line)
        i = src.index("def _build_point_diff_claim(")
        body = src[i:src.index("\ndef ", i + 1)]
        self.assertEqual("bec5cf7bd1a06b6e", hashlib.sha256(body.encode("utf-8")).hexdigest()[:16])

    def test_real_document(self):
        zb = load_doc("S100YXGH")
        c23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}["N080"]
        c24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}["N080"]
        self.assertEqual(("POINTER_NOT_FOUND", self.NO_PHRASE), (c23["state"], c23["reason"]))
        self.assertEqual("GROUNDED", c24["state"])
        self.assertEqual("formula:a-b(pure)", c24["pointers"][-1])


# ====================================================================================================
FUND_PHRASES = [
    "営業活動の結果得られた資金", "営業活動により得られた資金", "営業活動による資金の増加", "営業活動の結果増加した資金", "営業活動の結果支出した資金", "営業活動による資金の獲得額",
    "投資活動による資金の減少", "投資活動の結果支出した資金", "投資活動により使用した資金", "投資活動の結果増加した資金", "投資活動による資金の支出額",
    "財務活動の結果支出した資金", "財務活動による資金の増加", "財務活動により獲得した資金", "財務活動により使用した資金", "財務活動の結果得られた資金",
    "財務活動の結果増加した資金", "財務活動により得られた資金", "財務活動による資金の減少"]
EXISTING_FUND_PHRASES = ["営業活動の結果獲得した資金", "営業活動の結果使用した資金", "投資活動の結果使用した資金", "投資活動の結果獲得した資金",
                         "財務活動の結果使用した資金", "財務活動の結果獲得した資金"]


class FundSubjectTest(unittest.TestCase):
    """(3) 資金の主語の句 19 通りを既存 6 句と同じ要素に結ぶ。当期と Prior1Year の fact にだけ値で結ぶ。"""

    def test_the_table_is_the_nineteen_phrases(self):
        table = V.CF_FUND_SUBJECTS_2026_10_21
        self.assertEqual(FUND_PHRASES, [w for w, _e in table])
        self.assertEqual(19, len(set(w for w, _e in table)))

    def test_each_phrase_maps_to_the_cash_flow_element_of_its_activity(self):
        want = {"営業": ["NetCashProvidedByUsedInOperatingActivities"], "投資": ["NetCashProvidedByUsedInInvestingActivities"],
                "財務": ["NetCashProvidedByUsedInFinancingActivities"]}
        for w, e in V.CF_FUND_SUBJECTS_2026_10_21:
            self.assertEqual(want[w[:2]], e, w)

    def test_the_new_phrases_are_not_in_the_old_subject_list_and_the_old_six_are_unchanged(self):
        old = dict(V.P23.subjects)
        for w in FUND_PHRASES:
            self.assertNotIn(w, old, w)
        for w in EXISTING_FUND_PHRASES:
            self.assertIn(w, old, w)
        self.assertEqual(V.P23.subjects, V.P24.subjects)       # 旗は subjects の定義を変えない(build_raw_claims が足す)

    def test_the_new_phrases_do_not_bind_to_prior2year(self):
        """Prior2Year にだけ値が合う文: 既存の句は従来どおり結ぶ(P23 と同じ)。新しい句は P24 では結ばない(P23 は結んだ)。"""
        elems = ["NetCashProvidedByUsedInOperatingActivities"]
        facts = [fact("NetCashProvidedByUsedInOperatingActivities", CUR, 5000000), fact("NetCashProvidedByUsedInOperatingActivities", PRI, 7000000),
                 fact("NetCashProvidedByUsedInOperatingActivities", PRI2, 999000)]
        old, new = "営業活動の結果獲得した資金", "営業活動による資金の増加"
        for p in ("P23", "P24"):
            c = call(p, old + "は999千円となった。", "999", "千円", old, elems, facts)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertTrue(c["pointer"].endswith("@" + PRI2), p)
        c23 = call("P23", new + "は999千円となった。", "999", "千円", new, elems, facts)
        c24 = call("P24", new + "は999千円となった。", "999", "千円", new, elems, facts)
        self.assertEqual("GROUNDED", c23["result"])
        self.assertTrue(c23["pointer"].endswith("@" + PRI2))
        self.assertNotEqual("GROUNDED", c24["result"])
        self.assertFalse((c24["pointer"] or "").endswith("@" + PRI2))

    def test_the_new_phrases_bind_to_current_and_prior1year(self):
        elems = ["NetCashProvidedByUsedInOperatingActivities"]
        facts = [fact("NetCashProvidedByUsedInOperatingActivities", CUR, 5000000), fact("NetCashProvidedByUsedInOperatingActivities", PRI, 7000000),
                 fact("NetCashProvidedByUsedInOperatingActivities", PRI2, 999000)]
        new = "営業活動による資金の増加"
        c = call("P24", new + "は5,000千円となった。", "5,000", "千円", new, elems, facts)
        self.assertEqual("GROUNDED", c["result"])
        self.assertTrue(c["pointer"].endswith("@" + CUR))
        c = call("P24", new + "は、前期は7,000千円となった。", "7,000", "千円", new, elems, facts)
        self.assertEqual("GROUNDED", c["result"])
        self.assertTrue(c["pointer"].endswith("@" + PRI))

    def test_real_document_phrases_are_registered_only_in_p24(self):
        # 実物: S100YUHC N091「営業活動による資金の獲得額は23億18百万円(前年同期は25億98百万円の獲得)となりました。」
        zb = load_doc("S100YUHC")
        d23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}
        d24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}
        want = {"N091": "NetCashProvidedByUsedInOperatingActivities@CurrentYearDuration",
                "N092": "NetCashProvidedByUsedInOperatingActivities@Prior1YearDuration",
                "N097": "NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults@CurrentYearDuration"}
        for cid, ptr in want.items():
            self.assertEqual(("UNVERIFIABLE", "ambiguous(elements)"), (d23[cid]["state"], d23[cid]["reason"]), cid)
            self.assertEqual("GROUNDED", d24[cid]["state"], cid)
            self.assertTrue(d24[cid]["pointers"][0].endswith(ptr), (cid, d24[cid]["pointers"]))
            self.assertEqual(1, len(d24[cid]["pointers"]))


# ====================================================================================================
N_OPE = "NetCashProvidedByUsedInOperatingActivities"
SUM = "SummaryOfBusinessResults"


def cf_facts(cur, p1, p2):
    return [fact(N_OPE + SUM, CUR, cur, prefix="jpcrp_cor:"), fact(N_OPE + SUM, PRI, p1, prefix="jpcrp_cor:"), fact(N_OPE + SUM, PRI2, p2, prefix="jpcrp_cor:")]


class CfTotalSignTest(unittest.TestCase):
    """(4) CF 合計の文字の主張は、前期の手がかりがあるときだけ Prior1Year の値そのものの符号で照合する。手がかりが無ければ P23 のまま。"""

    # 実物: S100YYQX T025「当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(前年同期は3,255,173千円の増加)。」
    CUE = "当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(前年同期は3,255,173千円の%s)。"
    NO_CUE = "当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(3,255,173千円の%s)。"

    def one(self, p, s, facts):
        cs = text_claims(p, s, facts)
        self.assertEqual(1, len(cs))
        return cs[0]

    def ptr(self, kind):
        return ["xbrl:jpcrp_cor:%s@%s" % (N_OPE + SUM, kind), "builtin:flow_sign(cur)==direction"]

    def test_with_a_cue_the_prior_year_value_sign_decides(self):
        """前々期より小さくても、前期の値が正なら「増加」。P23 は前期 − 前々期の差の符号で見て止める。"""
        facts = cf_facts(3334024000, 3255173000, 4000000000)
        c23, c24 = self.one("P23", self.CUE % "増加", facts), self.one("P24", self.CUE % "増加", facts)
        self.assertEqual("VALUE_MISMATCH", c23["result"])
        self.assertEqual("GROUNDED", c24["result"])
        self.assertEqual(self.ptr(PRI), c24["pointer"])
        self.assertEqual(3255173000.0, c24["recomputed"])

    def test_with_a_cue_the_wrong_direction_is_stopped(self):
        facts = cf_facts(3334024000, 3255173000, 4000000000)
        c = self.one("P24", self.CUE % "減少", facts)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(self.ptr(PRI), c["pointer"])

    def test_with_a_negative_prior_year_value_the_decrease_is_right(self):
        facts = cf_facts(3334024000, -446224000, -900000000)
        c = self.one("P24", self.CUE % "減少", facts)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("VALUE_MISMATCH", self.one("P24", self.CUE % "増加", facts)["result"])

    def test_the_other_prior_cues_also_switch_the_branch(self):
        facts = cf_facts(3334024000, 3255173000, 4000000000)
        for s in ("当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(前年は3,255,173千円の増加)。",
                  "当連結会計年度において営業活動の結果獲得した資金は、3,334,024千円(前連結会計年度は3,255,173千円の増加)。"):
            c = self.one("P24", s, facts)
            self.assertEqual(self.ptr(PRI), c["pointer"], s)
            self.assertEqual("GROUNDED", c["result"], s)

    def test_without_a_cue_it_is_p23_unchanged(self):
        """手がかりが無ければ P23 のまま(当期・前期の対の符号)。前々期の値を変えて P23 の枝に入っていることも確かめる。"""
        for p1, p2 in ((3255173000, 4000000000), (3255173000, 100000000)):
            facts = cf_facts(3334024000, p1, p2)
            for w in ("増加", "減少"):
                a, b = self.one("P23", self.NO_CUE % w, facts), self.one("P24", self.NO_CUE % w, facts)
                self.assertEqual(a, b)
                self.assertNotIn("flow_sign", " ".join(b["pointer"]))
                self.assertTrue(b["pointer"][0].endswith("@" + CUR))

    def test_a_non_cash_flow_total_is_unchanged_even_with_a_cue(self):
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 4000000), fact("NetSales", PRI2, 4500000)]
        s = "売上高は、前年同期は4,000千円の増加となりました。"
        self.assertEqual(self.one("P23", s, facts), self.one("P24", s, facts))

    def test_real_documents(self):
        # 実物: S100YYK8 T041「営業活動による資金の増加は454,324千円(前年同期は509,015千円の資金の増加)となりました。」
        zb = load_doc("S100YYK8")
        c23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}["T041"]
        c24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}["T041"]
        self.assertEqual(("UNVERIFIABLE", "no_subject"), (c23["state"], c23["reason"]))
        self.assertEqual("GROUNDED", c24["state"])
        self.assertTrue(c24["pointers"][0].endswith("NetCashProvidedByUsedInOperatingActivities@Prior1YearDuration"))
        self.assertEqual("builtin:flow_sign(cur)==direction", c24["pointers"][1])
        # 実物: S100YYQX T025(GROUNDED のまま参照先だけ前期・前々期の対から前期の値 1 本へ動く)
        zb = load_doc("S100YYQX")
        c23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}["T025"]
        c24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}["T025"]
        self.assertEqual("GROUNDED", c23["state"])
        self.assertEqual("GROUNDED", c24["state"])
        self.assertEqual(3, len(c23["pointers"]))
        self.assertEqual(2, len(c24["pointers"]))


# ====================================================================================================
SEG_A, SEG_B = "SegAMember", "SegBMember"
CTX = {"CurrentYearDuration_SegAMember": {"members": [SEG_A]}, "Prior1YearDuration_SegAMember": {"members": [SEG_A]},
       "CurrentYearDuration_SegBMember": {"members": [SEG_B]}, "Prior1YearDuration_SegBMember": {"members": [SEG_B]}}


def seg_facts(plain=130123e6, a=50000e6, b=20000e6, pplain=119000e6, pa=45000e6, pb=19000e6, name="NetSales"):
    return [fact(name, CUR, plain), fact(name, PRI, pplain),
            fact(name, "CurrentYearDuration_SegAMember", a), fact(name, "Prior1YearDuration_SegAMember", pa),
            fact(name, "CurrentYearDuration_SegBMember", b), fact(name, "Prior1YearDuration_SegBMember", pb)]


def seg(p, s, facts, value):
    return by_value(num_claims(p, s, facts, contexts_for(facts, CTX), SEG_A), value)


class FrameRebindTest(unittest.TestCase):
    """旗 ``frame_rebind``: 取った枠(ここでは SegAMember)で値が合わず、同じ要素の別の枠(当期)で合う → UNVERIFIABLE。GROUNDED を作らない。"""

    # 実物: S100YWGX N001「…売上高130,123百万円(前連結会計年度比9.2%増)となりました。」(取った枠は国内ブックオフ事業 member、合うのは素の枠)
    S_DIRECT = "売上高130,123百万円(前連結会計年度比9.2%増)となりました。"

    def assertRebound(self, c, reason, contexts):
        self.assertIsNone(c["result"])
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["recomputed"])
        self.assertEqual(reason, c["reason"])
        self.assertEqual(sorted(contexts), c["frame_rebind"])

    def test_direct_value_one_other_frame(self):
        facts = seg_facts()
        c23, c24 = seg("P23", self.S_DIRECT, facts, 130123e6), seg("P24", self.S_DIRECT, facts, 130123e6)
        self.assertEqual("VALUE_MISMATCH", c23["result"])
        self.assertEqual("xbrl:jppfs_cor:NetSales@CurrentYearDuration_SegAMember", c23["pointer"])
        self.assertRebound(c24, "other_frame(%s)" % CUR, [CUR])
        self.assertEqual(CUR, c24["other_frame"])

    def test_direct_value_matches_only_a_member_frame(self):
        c = seg("P24", "売上高は20,000百万円となりました。", seg_facts(), 20000e6)
        self.assertRebound(c, "other_frame(CurrentYearDuration_SegBMember)", ["CurrentYearDuration_SegBMember"])

    def test_two_other_frames_are_ambiguous(self):
        c = seg("P24", self.S_DIRECT, seg_facts(b=130123e6), 130123e6)
        self.assertRebound(c, "ambiguous(member)", [CUR, "CurrentYearDuration_SegBMember"])
        self.assertEqual(2, c["ambiguous_count"])
        self.assertNotIn("other_frame", c)

    def test_difference_of_current_and_prior(self):
        # 実物の形: S100YUHC N057「(前年同期比 35.6%増、52百万円増)」の増減の額
        c = seg("P24", "売上高は11,123百万円増加しました。", seg_facts(), 11123e6)
        self.assertRebound(c, "other_frame(%s)" % CUR, [CUR])

    def test_ratio_of_current_to_prior(self):
        c = seg("P24", "売上高は前期比105.3%となりました。", seg_facts(), 105.3)
        self.assertRebound(c, "other_frame(CurrentYearDuration_SegBMember)", ["CurrentYearDuration_SegBMember"])

    def test_percent_change(self):
        c = seg("P24", "売上高は前期比5.3%増となりました。", seg_facts(), 5.3)
        self.assertRebound(c, "other_frame(CurrentYearDuration_SegBMember)", ["CurrentYearDuration_SegBMember"])

    def test_it_never_makes_a_grounded_claim(self):
        """どの型でも結果は GROUNDED にならず、pointer は付かない(値が合う枠がちょうど 1 つでも同定ではない)。"""
        cases = [(self.S_DIRECT, 130123e6), ("売上高は20,000百万円となりました。", 20000e6), ("売上高は11,123百万円増加しました。", 11123e6),
                 ("売上高は前期比105.3%となりました。", 105.3), ("売上高は前期比5.3%増となりました。", 5.3)]
        for s, v in cases:
            c = seg("P24", s, seg_facts(), v)
            self.assertNotEqual("GROUNDED", c["result"], s)
            self.assertIsNone(c["pointer"], s)
            self.assertFalse(c["bound"], s)

    # ---- 当たらない例
    def test_a_value_in_no_frame_stays_value_mismatch(self):
        c = seg("P24", "売上高は77,777百万円となりました。", seg_facts(), 77777e6)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertTrue(c["bound"])

    def test_a_prior_cue_keeps_the_old_behaviour(self):
        """前期の手がかりがある数は取り直さない(前期の枠の話)。"""
        s = "売上高は、前年同期は130,123百万円となりました。"
        for p in ("P23", "P24"):
            c = seg(p, s, seg_facts(), 130123e6)
            self.assertEqual("VALUE_MISMATCH", c["result"], p)
            self.assertNotIn("frame_rebind", c)

    def test_it_does_not_widen_to_a_prior_year_frame(self):
        """値が合うのが前期の枠だけなら取り直さない(別の要素・前期の枠には広げない)。"""
        facts = seg_facts(plain=111e6, pplain=130123e6)
        c = seg("P24", "売上高は130,123百万円となりました。", facts, 130123e6)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertNotIn("frame_rebind", c)

    def test_it_does_not_widen_to_another_element(self):
        facts = seg_facts(plain=111e6) + [fact("OperatingIncome", CUR, 130123e6)]
        c = seg("P24", self.S_DIRECT, facts, 130123e6)
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertNotIn("frame_rebind", c)

    def test_a_member_in_a_multi_member_context_is_not_a_candidate(self):
        """合う fact が 2 つ以上の member を持つ context(内訳の枠)にしか無ければ取り直さない。"""
        ctxs = contexts_for(seg_facts(), dict(CTX, **{"CurrentYearDuration_Seg2Members": {"members": [SEG_A, SEG_B]}}))
        for ctx_id, members, want_rebind in (("CurrentYearDuration_Seg2Members", [SEG_A, SEG_B], False), ("CurrentYearDuration_SegCMember", ["SegCMember"], True)):
            facts = seg_facts(plain=111e6) + [fact("NetSales", ctx_id, 130123e6)]
            ctxs = contexts_for(facts, dict(CTX, **{ctx_id: {"members": members}}))
            c = by_value(num_claims("P24", self.S_DIRECT, facts, ctxs, SEG_A), 130123e6)
            if want_rebind:
                self.assertEqual("other_frame(%s)" % ctx_id, c["reason"])
            else:
                self.assertEqual("VALUE_MISMATCH", c["result"])
                self.assertNotIn("frame_rebind", c)

    def test_the_flag_off_keeps_value_mismatch(self):
        for p in ("P23", P24_OFF, P24_VOCAB_ONLY):
            c = by_value(num_claims(p, self.S_DIRECT, seg_facts(), contexts_for(seg_facts(), CTX), SEG_A), 130123e6)
            self.assertEqual("VALUE_MISMATCH", c["result"])
            self.assertNotIn("frame_rebind", c)

    def test_the_flag_off_keeps_value_mismatch_for_the_pct_forms(self):
        """率の枠の取り直し (ii) は旗 ``frame_rebind`` が偽なら効かない(P24 の独立監査の軽い指摘 2、2026-10-21)。
        P24 では UNVERIFIABLE になる 2 つの率の型(前期比 105.3% の比・前期比 5.3% 増の変化率)が、旗を偽にすると VALUE_MISMATCH のまま
        (取った枠 SegAMember の対で率が合わず、別の枠 SegBMember の対では合う)。両方の型のガードを同じ 1 本で見る。"""
        cases = [("売上高は前期比105.3%となりました。", 105.3), ("売上高は前期比5.3%増となりました。", 5.3)]
        for s, v in cases:
            c24 = seg("P24", s, seg_facts(), v)
            self.assertEqual("other_frame(CurrentYearDuration_SegBMember)", c24["reason"], s)    # 対照: 旗が真なら効く
            for p in ("P23", P24_OFF, P24_VOCAB_ONLY):
                c = seg(p, s, seg_facts(), v)
                name = p if isinstance(p, str) else p.name
                self.assertEqual("VALUE_MISMATCH", c["result"], (name, s))
                self.assertTrue(c["bound"], (name, s))
                self.assertIsNotNone(c["pointer"], (name, s))
                self.assertNotIn("frame_rebind", c, (name, s))
                self.assertNotIn("other_frame", c, (name, s))

    def test_a_matching_taken_frame_is_untouched(self):
        c = seg("P24", "売上高は50,000百万円となりました。", seg_facts(), 50000e6)
        self.assertEqual("GROUNDED", c["result"])
        self.assertTrue(c["pointer"].endswith("CurrentYearDuration_SegAMember"))

    # ---- recipe / Core
    def test_the_recipe_uses_the_registered_reason_and_keeps_the_context_in_provenance(self):
        c = seg("P24", self.S_DIRECT, seg_facts(), 130123e6)
        raw = dict(c, id="N001", sentence=0, span="x", unit="百万円", subject="売上高")
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual("other_frame", recipe.unverifiable_reason)
        self.assertIsNone(recipe.not_found_reason)
        self.assertEqual(CUR, recipe.claim.provenance["other_frame"])
        self.assertEqual([], list(recipe.claim.pointers) if hasattr(recipe.claim, "pointers") else [])

    def test_ambiguous_recipe_has_no_other_frame_provenance(self):
        c = seg("P24", self.S_DIRECT, seg_facts(b=130123e6), 130123e6)
        raw = dict(c, id="N001", sentence=0, span="x", unit="百万円", subject="売上高")
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual("ambiguous(member)", recipe.unverifiable_reason)
        self.assertNotIn("other_frame", recipe.claim.provenance)

    def test_real_documents_through_core(self):
        # 実物: S100YUHC N055「その他事業の売上高は1億99百万円(前年同期比 35.6%増、52百万円増)…」
        member = "CurrentYearDuration_OperatingSegmentsNotIncludedInReportableSegmentsAndOtherRevenueGeneratingBusinessActivitiesMember"
        for doc, cid, ctx in (("S100YUHC", "N055", member), ("S100YWGX", "N001", CUR)):
            zb = load_doc(doc)
            c23 = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}[cid]
            c24 = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}[cid]
            self.assertEqual("VALUE_MISMATCH", c23["state"], (doc, cid))
            self.assertEqual(("UNVERIFIABLE", "other_frame", []), (c24["state"], c24["reason"], c24["pointers"]), (doc, cid))
            inst = I.load_instance(zb)
            recs = R.build_recipes(zb, V.PROFILES["P24"])
            res = {r.claim_id: r for r in core.verify_all(recs, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))}
            rc = [r for r in recs if r.claim.id == cid][0]
            self.assertEqual(ctx, rc.claim.provenance["other_frame"], (doc, cid))
            self.assertEqual("UNVERIFIABLE", res[cid].state.name)
            self.assertEqual("other_frame", res[cid].reason)
            self.assertEqual(0, len(res[cid].pointers))


# ====================================================================================================
class HumanDecisionsTest(unittest.TestCase):
    """触る枝の中の人間の決定の振る舞いは P24 でも同じ(封 §1)。字の門は別に(period_bind_seal・rounding_seal ほか)。"""

    def test_anshi_a_no_subject(self):
        """2026-10-08 案ア: 主語が取れない数は束縛しない(no_subject)。"""
        facts = [fact("NetSales", CUR, 5000000)]
        for p in ("P22", "P23", "P24"):
            c = by_value(num_claims(p, "5,000千円となりました。", facts), 5000000)
            self.assertEqual("no_subject", c["reason"], p)
            self.assertIsNone(c["pointer"], p)

    def test_1b_no_prior2_stops_without_substituting(self):
        """§1b: 前々期が無い「前期は…」の増減の語は代用せず止める。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 4000000)]
        for p in ("P22", "P23", "P24"):
            c = text_claims(p, "売上高は、前期は増加しました。", facts)[0]
            self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"], p)

    def test_c2_period_cue_ties_to_the_prior_year(self):
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]
        for p in ("P22", "P23", "P24"):
            c = by_value(num_claims(p, "売上高は、前期は999千円となった。", facts), 999000)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:jppfs_cor:NetSales@" + PRI, c["pointer"], p)

    def test_p21_last_branch_names_the_current_year_fact(self):
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 4000000)]
        for p in ("P22", "P23", "P24"):
            c = by_value(num_claims(p, "売上高は7,777千円となりました。", facts), 7777000)
            self.assertEqual("VALUE_MISMATCH", c["result"], p)
            self.assertEqual("xbrl:jppfs_cor:NetSales@" + CUR, c["pointer"], p)

    def test_p23_truncation_band_is_kept(self):
        """P23 の ``_mag_trunc``: 切り捨ての書類の負の金額は絶対値の帯。「営業損失は△23百万円」を実際の △22.989 百万円に対して止める。"""
        facts = [fact("OperatingIncome", CUR, -22989000)]
        for p in ("P23", "P24"):
            claims = R._build_raw_num_claims(["営業損失は23百万円となった。"], facts, contexts_for(facts), prof(p), lambda si, pos: (None, "t"), "truncate")
            c = by_value(claims, 23000000)
            self.assertEqual("VALUE_MISMATCH", c["result"], p)


# ====================================================================================================
class DocumentLevelTest(unittest.TestCase):
    """実物の書類 8 件(試験が使う分)で P23 → P24 の動きの種類を固定する。"""

    def test_nothing_that_was_grounded_in_p23_leaves_grounded(self):
        for doc in DOCS:
            zb = load_doc(doc)
            a = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}
            b = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}
            self.assertEqual(sorted(a), sorted(b), doc)
            for cid, c in a.items():
                if c["state"] == "GROUNDED":
                    self.assertEqual("GROUNDED", b[cid]["state"], (doc, cid))

    def test_a_frame_rebind_never_ends_in_grounded(self):
        for doc in DOCS:
            zb = load_doc(doc)
            a = {c["id"]: c for c in VD.verify_document(zb, "P23")["claims"]}
            b = {c["id"]: c for c in VD.verify_document(zb, "P24")["claims"]}
            for cid, c in b.items():
                if c["reason"] in ("other_frame", "ambiguous(member)") and a[cid]["state"] == "VALUE_MISMATCH":
                    self.assertEqual("UNVERIFIABLE", c["state"], (doc, cid))
                    self.assertEqual([], c["pointers"], (doc, cid))


if __name__ == "__main__":
    unittest.main()
