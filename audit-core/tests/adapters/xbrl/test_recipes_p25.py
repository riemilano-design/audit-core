# -*- coding: utf-8 -*-
"""P25(最後の枝の名指しは証拠があるときだけ「違う」と言う)の試験。封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md §1。

P25 = P24 + 旗 ``last_branch_names_only_if_evidence``。段 1 では既定にしない(``DEFAULT_PROFILE`` = P22 のまま)。

最後の枝(主語があり、値が合う fact が無く、導出 a-b も合わず、§1b の止め・F2′・P24 frame_rebind・F1′・F3b のどれにも当たらない)で、
主語の当期の先頭 fact(「名指す fact」)を名指して VALUE_MISMATCH にする直前に、旗が真なら証拠を見る。
  (i)   名指す fact と同じ要素名・同じ枠で context が違う JPY の fact が、文の値と照合の帯で合う(期の取り違え)。
  (ii)  min(|名指す値 - 文の値|, ||名指す値| - |文の値||) <= 2 × 主張の桁(桁の打ち間違い)。
  (iii) n ∈ (±1, ±2, ±3, ±6, ±9) のどれかで、名指す値が 文の値 × 10^-n と帯「書かれた数の精度 × 10^-n」で合う(桁・単位の取り違え)。
どれも偽なら pointer を付けず POINTER_NOT_FOUND、reason は登録簿の固定の名前 ``no_same_value``、名指しは ``Claim.provenance["no_same_value"]``。

**各挙動について「当たる例」と「当たらない例」を置き、実物の 1 行はコメントに出典(書類・id・文)を書く。**
合成の instance(facts と contexts を直接組む)に、手元の cache の実物の書類(sha256 を固定。無ければ失敗。skip しない)を足す。通信しない。
"""
import dataclasses
import hashlib
import inspect
import os
import re
import unittest

import audit_core as core

from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import resolve as RV
from adapters.xbrl import instance as I
from adapters.xbrl import verify_document as VD
from adapters.xbrl import vocabulary as V

from . import _material as M
from .test_recipes_p24 import BATTERY, FRAME_CONTEXTS, contexts_for, fact, num_claims, text_claims, by_value

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
PRI2 = "Prior2YearDuration"
CUR_I = "CurrentYearInstant"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

#: 実物の書類(2026-10-21 時点の手元の cache の sha256)。
DOCS = {
    "S100YYK8": "512b316c0739e2cb83c465ec7ffae4474efebf4ffbc234a70270346cf1e1caad",
    "S100YZ7E": "bd2fe7969c31528f9c1609c85cb2dd8bb26aad2469ee060e3227b7f9367353f3",
    "S100Z3JY": "5851a52ff80044bbb31f622f847461b1fccb5fc802a555dba868fd983372efbf",
    "S100Z42X": "c9337c162e23e2808f73cb0318cfd96e36c25915cc6aaaa8a9eccc974557bbbc",
    "S100YWGX": "11a87aa7ddda60db6d51910decfbf8a643621e520f582ba920ecece743604cec",
    "S100YXGH": "29b7eb0b24e579a5b2ae9ce664d58af2d1d3cd0ffe4aec23fd7a45bd7fc36cbf",
    "S100YYQX": "a0313840d8ecc13e8470e34f54451a0207c5510ffd0a9c3860e50c9640a9cdf0",
    "S100YUHC": "cd212b810b33d07bd9723ed9518c299dcfaf88fc434f7026211206a9d5f6d450",
}
_ZIPS = {}
_VERIFIED = {}


def load_doc(doc_id):
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
        _VERIFIED[key] = {c["id"]: c for c in VD.verify_document(load_doc(doc_id), profile)["claims"]}
    return _VERIFIED[key]


NSV = "no_same_value"
#: 旗を偽にした P25 = P24 と同じ(名前だけ違う)。
P25_OFF = dataclasses.replace(V.P25, name="P25_OFF", last_branch_names_only_if_evidence=False)


def lb(p, sentence, number, unit, facts, sign=1, subj="売上高", elems=("NetSales",), member=None):
    """``_direct_value_claim`` を直接呼ぶ(最後の枝まで落ちる 1 文)。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
    prof = V.PROFILES[p] if isinstance(p, str) else p
    R._direct_value_claim(claim, sentence, a, b, sign, float(number.replace(",", "")), unit, None, subj, list(elems), member,
                          facts, contexts_for(facts), prof)
    return claim


def sentence_of(number, unit="千円"):
    return "売上高は%s%sとなりました。" % (number, unit)


def evidence(target, scale, named, facts, rounding=None, mag_trunc=False):
    return R._last_branch_evidence(target, scale, rounding, mag_trunc, named, facts)


def nfact(value, ctx=CUR, name="NetSales"):
    return fact(name, ctx, value)


def assertNamed(tc, c, ctx=CUR, name="NetSales", value=None):
    tc.assertEqual("VALUE_MISMATCH", c["result"])
    tc.assertEqual("xbrl:jppfs_cor:%s@%s" % (name, ctx), c["pointer"])
    tc.assertTrue(c["bound"])
    tc.assertEqual("value differs(segment/other period?)", c["reason"])
    tc.assertNotIn(NSV, c)
    if value is not None:
        tc.assertEqual(value, c["recomputed"])


def assertUnnamed(tc, c, named_ctx=CUR, name="NetSales", value=5000000.0):
    tc.assertIsNone(c["result"])
    tc.assertIsNone(c["pointer"])
    tc.assertFalse(c["bound"])
    tc.assertIsNone(c["recomputed"])
    tc.assertEqual(NSV, c["reason"])
    tc.assertEqual({"named": "xbrl:jppfs_cor:%s@%s" % (name, named_ctx), "value": value}, c[NSV])
    tc.assertIsNone(c["last_branch_evidence"])


# ====================================================================================================
class FlagShapeTest(unittest.TestCase):
    def test_p25_is_p24_plus_exactly_the_one_flag(self):
        self.assertEqual(dataclasses.replace(V.P24, name="P25", last_branch_names_only_if_evidence=True), V.P25)
        self.assertIs(V.PROFILES["P25"], V.P25)

    def test_the_flag_is_false_by_default_and_true_only_for_p25(self):
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        self.assertIs(False, fields["last_branch_names_only_if_evidence"].default)
        self.assertEqual(["P25"], sorted(n for n, p in V.PROFILES.items() if p.last_branch_names_only_if_evidence))

    def test_with_the_flag_false_p25_is_p24(self):
        self.assertEqual(dataclasses.replace(V.P24, name="P25_OFF"), P25_OFF)

    def test_the_default_profile_is_still_p22_in_step_1(self):
        self.assertEqual("P22", V.DEFAULT_PROFILE)
        self.assertFalse(V.PROFILES[V.DEFAULT_PROFILE].last_branch_names_only_if_evidence)

    def test_the_profiles_literal_line_is_not_touched(self):
        """``PROFILES = {...}`` の行の字は変えない(P25 は ``PROFILES["P25"] = P25`` で足す)。"""
        path = inspect.getsourcefile(V)
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        literal = [l for l in lines if l.startswith("PROFILES = {")]
        self.assertEqual(1, len(literal))
        self.assertNotIn("P25", literal[0])
        self.assertEqual(1, lines.count('PROFILES["P25"] = P25'))

    def test_the_constants_are_pinned_in_letters(self):
        self.assertEqual(2, R.LAST_BRANCH_DIGIT_K)
        self.assertEqual((1, -1, 2, -2, 3, -3, 6, -6, 9, -9), R.LAST_BRANCH_SCALE_EXPONENTS)
        self.assertEqual("no_same_value", R.NO_SAME_VALUE)

    def test_no_same_value_is_registered_in_the_two_places(self):
        self.assertIn(NSV, RS._POINTER_NOT_FOUND_REASONS)
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(NSV, None))
        self.assertNotIn(NSV, RS._UNVERIFIABLE_REASONS)


# ====================================================================================================
class FlagsOffIsP24Test(unittest.TestCase):
    """旗が偽なら 1 行も変わらない(封 §1)。"""

    CASES = [
        # (名前, 文, 数, 単位, facts, 符号)  最後の枝まで落ちる 6 通り(P25 で動くもの 3・動かないもの 3)
        ("証拠なし", sentence_of("7,777"), "7,777", "千円", [nfact(5000000), nfact(4000000, PRI)], 1),
        ("(i) 期の取り違え", sentence_of("7,777"), "7,777", "千円", [nfact(5000000), nfact(7777000, PRI)], 1),
        ("(ii) 桁の打ち間違い", sentence_of("5,001"), "5,001", "千円", [nfact(5000000), nfact(4000000, PRI)], 1),
        ("(iii) 単位の取り違え", sentence_of("50,000"), "50,000", "千円", [nfact(5000000), nfact(4000000, PRI)], 1),
        ("証拠なし(損失)", "営業損失は7,777千円となりました。", "7,777", "千円", [fact("OperatingIncome", CUR, -5000000)], -1),
        ("値が合う", sentence_of("5,000"), "5,000", "千円", [nfact(5000000), nfact(4000000, PRI)], 1),
    ]

    def run_cases(self, p):
        out = []
        for name, s, n, u, facts, sg in self.CASES:
            elems = ("OperatingIncome",) if "損失" in s else ("NetSales",)
            subj = "営業損失" if "損失" in s else "売上高"
            out.append((name, lb(p, s, n, u, facts, sign=sg, subj=subj, elems=elems)))
        return out

    def test_every_case_is_identical_to_p24_with_the_flag_off(self):
        self.assertEqual(self.run_cases("P24"), self.run_cases(P25_OFF))

    def test_the_cases_do_change_with_the_flag_on_only_where_there_is_no_evidence(self):
        """電池が空振りでないこと: 旗が真の P25 で P24 と違うのは証拠なしの 2 通りだけ。"""
        strip = lambda rows: dict((n, dict((k, v) for k, v in c.items() if k != "last_branch_evidence")) for n, c in rows)
        a, b = strip(self.run_cases("P24")), strip(self.run_cases("P25"))
        self.assertEqual(["証拠なし", "証拠なし(損失)"], [n for n, *_ in self.CASES if a[n] != b[n]])
        # 証拠があって名指す 3 通りは、結果が P24 と同じで、証拠の種類だけを ``last_branch_evidence`` に足す
        e = dict((n, c.get("last_branch_evidence")) for n, c in self.run_cases("P25"))
        self.assertEqual({"(i) 期の取り違え": "same_element:" + PRI, "(ii) 桁の打ち間違い": "digit_within_k", "(iii) 単位の取り違え": "scale_10^1"},
                         dict((n, v) for n, v in e.items() if v))

    def test_the_p24_battery_is_identical_in_p25(self):
        """P24 の電池 5 件(語彙・ポイント・CF 合計・枠の取り直し)は最後の枝に落ちず、P25 でも 1 行も変わらない。"""
        for name, kind, s, facts, member in BATTERY:
            ctxs = contexts_for(facts, FRAME_CONTEXTS)
            fn = num_claims if kind == "num" else text_claims
            self.assertEqual(fn("P24", s, facts, ctxs, member), fn("P25", s, facts, ctxs, member), name)

    def test_a_real_document_is_identical_to_p24_with_the_flag_off(self):
        zb = M.load_zip_1()
        V.PROFILES["P25_OFF"] = P25_OFF
        try:
            off = VD.verify_document(zb, "P25_OFF")["claims"]
        finally:
            V.PROFILES.pop("P25_OFF", None)
        self.assertNotIn("P25_OFF", V.PROFILES)
        self.assertEqual(VD.verify_document(zb, "P24")["claims"], off)

    def test_no_other_profile_is_touched_by_the_branch(self):
        """P1〜P24 は旗を持たない(偽)ので、証拠なしの文でも P21 の名指しのまま。"""
        facts = [nfact(5000000), nfact(4000000, PRI)]
        for p in sorted(V.PROFILES):
            if p == "P25":
                continue
            c = lb(p, sentence_of("7,777"), "7,777", "千円", facts)
            self.assertNotEqual(NSV, c["reason"], p)
            self.assertNotIn("last_branch_evidence", c, p)


# ====================================================================================================
class NoEvidenceTest(unittest.TestCase):
    """証拠が無ければ名指さず POINTER_NOT_FOUND(no_same_value)。名指しは provenance に残る。"""

    FACTS = [nfact(5000000), nfact(4000000, PRI)]

    def test_p24_names_and_p25_does_not(self):
        s = sentence_of("7,777")
        assertNamed(self, lb("P24", s, "7,777", "千円", self.FACTS), value=5000000.0)
        assertUnnamed(self, lb("P25", s, "7,777", "千円", self.FACTS))

    def test_the_unnamed_claim_keeps_the_named_fact_in_provenance_through_the_recipe(self):
        c = lb("P25", sentence_of("7,777"), "7,777", "千円", self.FACTS)
        raw = dict(c, id="N001", sentence=0, span="x", unit="千円", subject="売上高")
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(NSV, recipe.not_found_reason)
        self.assertIsNone(recipe.unverifiable_reason)
        self.assertEqual({"named": "xbrl:jppfs_cor:NetSales@" + CUR, "value": 5000000.0}, recipe.claim.provenance[NSV])
        self.assertEqual([], list(recipe.pointers))

    def test_core_turns_it_into_pointer_not_found_with_the_registered_reason_and_no_pointer(self):
        zb = load_doc("S100YWGX")
        inst = I.load_instance(zb)
        recs = R.build_recipes(zb, V.PROFILES["P25"])
        res = {r.claim_id: r for r in core.verify_all(recs, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))}
        # 実物: S100YWGX N083「営業外費用は支払利息等、合計445百万円(前連結会計年度比20.2%増)となりました。」(名指しは支払利息 336 百万円)
        rc = [r for r in recs if r.claim.id == "N083"][0]
        self.assertEqual("xbrl:jppfs_cor:InterestExpensesNOE@" + CUR, rc.claim.provenance[NSV]["named"])
        self.assertEqual(336000000.0, rc.claim.provenance[NSV]["value"])
        self.assertEqual("POINTER_NOT_FOUND", res["N083"].state.name)
        self.assertEqual(NSV, res["N083"].reason)
        self.assertEqual(0, len(res["N083"].pointers))

    def test_a_subject_less_number_does_not_enter_the_last_branch(self):
        """主語が無い数は最後の枝に入らない: 値が合えば案ア no_subject、合わなければ no_element。P25 でも P24 と同じで、no_same_value にならない。"""
        for s, v, want in (("5,000千円となりました。", 5000000, "no_subject"), ("7,777千円となりました。", 7777000, "no_element")):
            c25 = by_value(num_claims("P25", s, self.FACTS), v)
            self.assertEqual(want, c25["reason"], s)
            self.assertEqual(by_value(num_claims("P24", s, self.FACTS), v), c25, s)


# ====================================================================================================
class EvidenceITest(unittest.TestCase):
    """(i) 名指す fact と同じ要素名・同じ枠で context が違う JPY の fact が、文の値と照合の帯で合う。"""

    # 実物: S100YYK8 N058「財務活動による資金の増加は758,178千円(前期同期は623,129千円の資金の減少)となりました。」
    #       (誤字「前期同期は」。623,129 千円は同じ要素の Prior1YearDuration と合う。名指しは当期の 758,178 千円)
    def test_the_prior_period_of_the_same_element_and_frame_is_evidence(self):
        facts = [nfact(5000000), nfact(7777000, PRI)]
        c = lb("P25", sentence_of("7,777"), "7,777", "千円", facts)
        assertNamed(self, c, value=5000000.0)
        self.assertEqual("same_element:" + PRI, c["last_branch_evidence"])

    def test_the_prior2_period_is_evidence_too(self):
        """Prior2Year の同じ要素・同じ枠も証拠(最後の枝の文は Prior2Year に値で結ばれると GROUNDED になるので、関数を直接呼ぶ)。"""
        facts = [nfact(5000000), nfact(7777000, PRI2)]
        self.assertEqual("same_element:" + PRI2, evidence(7777000.0, 1000.0, facts[0], facts))

    def test_the_band_is_the_matching_band_not_exact_equality(self):
        """帯は ``match_value`` の帯(千円なら 文の値 -500〜+1000 円)。帯の中は証拠、外は証拠でない。"""
        for v, want in ((7777400, True), (7777900, True), (7776400, False), (7779000, False)):
            facts = [nfact(5000000), nfact(v, PRI)]
            c = lb("P25", sentence_of("7,777"), "7,777", "千円", facts)
            self.assertEqual(want, c["reason"] != NSV, v)

    def test_a_different_frame_is_not_evidence(self):
        """同じ要素・前期でも、別の枠(member)の fact は証拠にしない。"""
        facts = [nfact(5000000), nfact(7777000, "Prior1YearDuration_SegAMember")]
        named = facts[0]
        self.assertIsNone(evidence(7777000.0, 1000.0, named, facts))
        c = lb("P25", sentence_of("7,777"), "7,777", "千円", facts)
        assertUnnamed(self, c)

    def test_a_different_element_is_not_evidence(self):
        facts = [nfact(5000000), fact("OperatingIncome", PRI, 7777000)]
        self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts))
        assertUnnamed(self, lb("P25", sentence_of("7,777"), "7,777", "千円", facts))

    def test_a_non_jpy_fact_is_not_evidence(self):
        for unit in ("USD", "pure", "shares", "JP", ""):
            facts = [nfact(5000000), fact("NetSales", PRI, 7777000, unit=unit)]
            self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts), unit)

    def test_a_jpy_prefixed_unit_is_evidence(self):
        """単位の字が JPY で始まる(大文字小文字を問わない)fact は証拠にする。"""
        for unit in ("JPY", "jpy", "JPYPerShare"):
            facts = [nfact(5000000), fact("NetSales", PRI, 7777000, unit=unit)]
            self.assertEqual("same_element:" + PRI, evidence(7777000.0, 1000.0, facts[0], facts), unit)

    def test_the_named_fact_itself_is_not_evidence(self):
        """名指す fact 自身(同じ context)は証拠にならない: 証拠は context が違うものだけ。"""
        facts = [nfact(7777000)]
        # 名指しの値 = 文の値なら、そもそも値が合って最後の枝に来ない。ここは関数を直接呼ぶ。
        self.assertEqual("digit_within_k", evidence(7777000.0, 1000.0, facts[0], facts))   # (i) でなく (ii)
        facts = [nfact(5000000), nfact(5000000)]    # 同じ context の fact が 2 つ(重複)
        self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts))

    def test_a_plain_frame_vs_a_member_frame_of_the_same_period_is_not_evidence(self):
        facts = [nfact(5000000), nfact(7777000, "CurrentYearDuration_SegAMember")]
        self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts))

    def test_the_frame_is_compared_after_removing_the_period_prefix(self):
        facts = [nfact(5000000, "CurrentYearDuration_SegAMember"), nfact(7777000, "Prior1YearDuration_SegAMember"),
                 nfact(7777000, "Prior1YearDuration_SegBMember")]
        self.assertEqual("same_element:Prior1YearDuration_SegAMember", evidence(7777000.0, 1000.0, facts[0], facts))
        facts = facts[:1] + facts[2:]
        self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts))

    def test_instant_contexts_work_the_same(self):
        facts = [nfact(5000000, CUR_I), nfact(7777000, "Prior1YearInstant")]
        self.assertEqual("same_element:Prior1YearInstant", evidence(7777000.0, 1000.0, facts[0], facts))

    def test_the_matching_band_follows_the_document_rounding(self):
        """書類の丸め方(truncate)の帯: 切り捨ての書類では fact が文の値より 1 単位未満だけ大きい値が合う。"""
        facts = [nfact(5000000), nfact(7777800, PRI)]
        self.assertEqual("same_element:" + PRI, evidence(7777000.0, 1000.0, facts[0], facts, rounding="truncate"))
        self.assertIsNone(evidence(7777000.0, 1000.0, facts[0], facts, rounding="round"))

    def test_the_truncation_band_is_by_magnitude_when_the_flag_says_so(self):
        """P23 ``_mag_trunc``(人間の決定): 切り捨ての書類の負の金額は絶対値の帯で当てる。P25 の (i) の帯もその帯を使う。
        文「△23百万円」に対し、同じ要素の前期が △22.989 百万円: 符号つきの帯なら合って(証拠)しまうが、絶対値の帯なら合わない。"""
        facts = [nfact(5000000), nfact(-22989000, PRI)]
        self.assertEqual("same_element:" + PRI, evidence(-23000000.0, 1000000.0, facts[0], facts, rounding="truncate", mag_trunc=False))
        self.assertIsNone(evidence(-23000000.0, 1000000.0, facts[0], facts, rounding="truncate", mag_trunc=True))
        # 同じ要素の前期が △23.5 百万円なら、絶対値の帯の中(切り捨てで 23)= 証拠
        facts = [nfact(5000000), nfact(-23500000, PRI)]
        self.assertEqual("same_element:" + PRI, evidence(-23000000.0, 1000000.0, facts[0], facts, rounding="truncate", mag_trunc=True))

    def test_real_documents_through_verify_document(self):
        # 実物: S100YYK8 N058「財務活動による資金の増加は758,178千円(前期同期は623,129千円の資金の減少)となりました。」
        # 実物: S100Z3JY N084「財務活動の結果使用した資金は、139百万円(前連結会計年度に使用した資金は0百万円)となりました。」
        for doc, cid, ctx in (("S100YYK8", "N058", PRI), ("S100Z3JY", "N084", PRI)):
            c24, c25 = verified(doc, "P24")[cid], verified(doc, "P25")[cid]
            self.assertEqual("VALUE_MISMATCH", c24["state"], (doc, cid))
            self.assertEqual(c24, c25, (doc, cid))


# ====================================================================================================
class EvidenceIITest(unittest.TestCase):
    """(ii) min(|名指す値 - 文の値|, ||名指す値| - |文の値||) <= 2 × 主張の桁。"""

    FACTS = [nfact(5000000), nfact(4000000, PRI)]

    def test_within_two_units_is_evidence_and_three_units_is_not(self):
        for n, want in (("5,001", True), ("5,002", True), ("5,003", False), ("4,999", True), ("4,998", True), ("4,997", False)):
            c = lb("P25", sentence_of(n), n, "千円", self.FACTS)
            self.assertEqual(want, c["reason"] != NSV, n)
            if want:
                assertNamed(self, c, value=5000000.0)       # 証拠があれば**名指す**(証拠の種類だけを見ない: 判定の結果を捨てる変異で黙らないように)
                self.assertEqual("digit_within_k", c["last_branch_evidence"], n)

    def test_the_unit_is_the_claim_digit_not_a_yen(self):
        """桁は主張の桁(百万円なら 1,000,000 円): 百万円の文は 2 百万円まで、千円の文は 2 千円まで。"""
        facts = [nfact(5000000000), nfact(4000000000, PRI)]
        for n in ("5,001", "5,002"):
            c = lb("P25", "売上高は%s百万円となりました。" % n, n, "百万円", facts)
            assertNamed(self, c, value=5000000000.0)
            self.assertEqual("digit_within_k", c["last_branch_evidence"], n)
        assertUnnamed(self, lb("P25", "売上高は5,003百万円となりました。", "5,003", "百万円", facts), value=5000000000.0)
        # 千円なら 2,000 円差でも 百万円なら 0.002 単位 = 範囲内、百万円で 3 単位(300 万円)差は千円では 3,000 単位 = 範囲外
        assertUnnamed(self, lb("P25", sentence_of("8,000"), "8,000", "千円", self.FACTS))

    def test_the_sign_is_ignored_through_the_absolute_value(self):
        """符号が逆でも絶対値の差が 2 単位以内なら証拠: 名指しが負の fact・文が正の値。"""
        facts = [nfact(-5000000)]
        c = lb("P25", sentence_of("5,001"), "5,001", "千円", facts, elems=("NetSales",))
        assertNamed(self, c, value=-5000000.0)
        self.assertEqual("digit_within_k", c["last_branch_evidence"])
        c = lb("P25", sentence_of("5,003"), "5,003", "千円", facts)
        self.assertEqual(NSV, c["reason"])

    def test_a_loss_sentence_uses_the_signed_target(self):
        # 実物の形: 営業損失の文は sign = -1(target が負)。名指しが負の営業利益 -5,000,000 なら 5,001 千円の損失は 1 単位差。
        facts = [fact("OperatingIncome", CUR, -5000000)]
        c = lb("P25", "営業損失は5,001千円となりました。", "5,001", "千円", facts, sign=-1, subj="営業損失", elems=("OperatingIncome",))
        assertNamed(self, c, name="OperatingIncome", value=-5000000.0)
        self.assertEqual("digit_within_k", c["last_branch_evidence"])

    def test_the_two_unit_line_is_inclusive(self):
        self.assertEqual("digit_within_k", evidence(5002000.0, 1000.0, nfact(5000000), [nfact(5000000)]))
        self.assertIsNone(evidence(5002001.0, 1000.0, nfact(5000000), [nfact(5000000)]))

    # 実物: S100YZ7E N050「…利息及び配当金の受取りによる収入額965百万円、…及びその他の収入等1百万円ありましたが、…」
    #       (名指しは 1 株当たり配当 400 円(JPY の fact)。1 百万円との差は 1 単位 = 偶然の近さ)
    # 実物: S100YZ7E N060「…有形・無形固定資産の取得による支出112百万円及びその他の支出が68百万円あった…」(名指しは無形のみ -111.15 百万円)
    def test_real_documents(self):
        for cid in ("N050", "N060"):
            c24, c25 = verified("S100YZ7E", "P24")[cid], verified("S100YZ7E", "P25")[cid]
            self.assertEqual("VALUE_MISMATCH", c24["state"], cid)
            self.assertEqual(c24, c25, cid)


# ====================================================================================================
#: 封 §1 (iii) の n の一覧を**字で**留める(engine の定数から作ると、定数から n を 1 つ外した変異で試験も同じ表を使って黙る)。
EXPONENTS = (1, -1, 2, -2, 3, -3, 6, -6, 9, -9)


def scaled_cases(target_yen):
    """各 n について 名指す値 = 文の値 × 10^-n の fact を返す(n ごとに 1 件)。"""
    return {n: target_yen * 10.0 ** (-n) for n in EXPONENTS}


class EvidenceIIITest(unittest.TestCase):
    """(iii) n ∈ (±1, ±2, ±3, ±6, ±9) で 名指す値 が 文の値 × 10^-n と帯「書かれた数の精度 × 10^-n」で合う。"""

    T = 7777000.0     # 「7,777千円」

    def ev(self, named_value, target=None, scale=1000.0):
        named = nfact(named_value)
        return evidence(self.T if target is None else target, scale, named, [named])

    def test_each_exponent_is_evidence(self):
        for n, v in scaled_cases(self.T).items():
            self.assertEqual("scale_10^%d" % n, self.ev(v), n)

    def test_each_exponent_end_to_end(self):
        for n, v in scaled_cases(self.T).items():
            facts = [nfact(v)]
            c = lb("P25", sentence_of("7,777"), "7,777", "千円", facts)
            assertNamed(self, c, value=v)
            self.assertEqual("scale_10^%d" % n, c["last_branch_evidence"], n)

    def test_plus_and_minus_nine_are_evidence(self):
        """n = ±9(千円 → 兆円 の取り違えの桁)。"""
        self.assertEqual("scale_10^9", self.ev(self.T * 1e-9))
        self.assertEqual("scale_10^-9", self.ev(self.T * 1e9))

    def test_an_exponent_outside_the_list_is_not_evidence(self):
        for n in (4, -4, 5, -5, 7, -7, 8, -8, 12, -12):
            self.assertIsNone(self.ev(self.T * 10.0 ** (-n)), n)

    def test_the_sign_is_not_asked(self):
        for n, v in scaled_cases(self.T).items():
            self.assertEqual("scale_10^%d" % n, self.ev(-v), n)

    def test_the_band_is_the_written_precision_times_ten_to_the_minus_n(self):
        """書かれた数の精度 = 主張の桁(末尾の 0 が無ければ)。n = 2 の帯は 1,000 × 10^-2 = 10 円: 77,770 に 5 円差まで合い、30 円差は外れる。"""
        self.assertEqual("scale_10^2", self.ev(77770.0 + 4))
        self.assertIsNone(self.ev(77770.0 + 30))

    def test_for_a_negative_n_the_band_is_the_precision_times_ten_to_the_abs_n(self):
        """n が負のとき帯は 精度 × 10^|n| に広がる: 文「500千円」(精度 100,000 円)の n = -1 は帯 1,000,000 円。"""
        T = 500000.0
        self.assertEqual("scale_10^-1", self.ev(5000000.0 + 400000, T))     # 5,400,000: 帯の中(広がっていなければ 100,000 の外)
        self.assertEqual("scale_10^-1", self.ev(5000000.0 - 400000, T))
        self.assertIsNone(self.ev(5000000.0 + 1100000, T))                  # 帯の外
        self.assertIsNone(self.ev(5000000.0 - 600000, T))

    def test_the_band_widens_with_trailing_zeros_of_the_written_number(self):
        """書かれた数の末尾の 0 が多いと精度が粗くなり、帯が広がる: 文「50,000千円」(精度 10,000,000 円)は n=1 で 5,000,000 円 ± 帯 1,000,000。"""
        self.assertEqual("scale_10^1", self.ev(5000000.0 + 400000, 50000000.0))
        self.assertIsNone(self.ev(5000000.0 + 1100000, 50000000.0))
        # 末尾の 0 が無い 「7,777千円」では同じ 40 万円の差は帯の外
        self.assertIsNone(self.ev(777700.0 + 400000))

    # ---- 書かれた数の精度
    def test_written_precision_is_scale_times_ten_to_the_trailing_zero_count(self):
        for target, want in ((7777000.0, 1000.0), (7770000.0, 10000.0), (7700000.0, 100000.0), (7000000.0, 1000000.0),
                             (50000000.0, 10000000.0), (1000.0, 1000.0), (0.0, 1000.0)):
            self.assertEqual(want, R._written_precision(target, 1000.0), target)

    def test_written_precision_uses_the_absolute_value(self):
        self.assertEqual(R._written_precision(7700000.0, 1000.0), R._written_precision(-7700000.0, 1000.0))

    def test_written_precision_rounds_half_to_even_like_python_round(self):
        """round は Python の偶数丸め: 10.5 → 10(末尾の 0 が 1 つ)、11.5 → 12(0 なし)、20.5 → 20、21.5 → 22。四捨五入なら 11・12・21・22 で別の精度になる。"""
        s = 1000.0
        self.assertEqual(10000.0, R._written_precision(10500.0, s))
        self.assertEqual(1000.0, R._written_precision(11500.0, s))
        self.assertEqual(10000.0, R._written_precision(20500.0, s))
        self.assertEqual(1000.0, R._written_precision(21500.0, s))
        self.assertEqual(1000.0, R._written_precision(500.0, s))      # 0.5 → 0
        self.assertEqual(1000.0, R._written_precision(1500.0, s))     # 1.5 → 2

    # ---- 当たらない例
    # 実物: S100Z42X N020「…売上高168百万円(前年同期比9.8%減少)、セグメント損失11百万円(前年同期はセグメント損失1百万円)となりました。」
    #       (「1百万円」と 当期のセグメントの売上 168,466,000 円 × 10^-2。偶然の近さ。VALUE_MISMATCH に残る)
    # 実物: S100YYK8 N041「…社債が20,000千円、リース債務が7,828千円…それぞれ減少したことによるもの」(長期借入金 1,987,490,000 円 × 10^-2。
    #       末尾の 0 が 4 つで精度 10,000,000 円 → 帯が広がって偶然に合う。封 §3 の限界)
    def test_real_documents_keep_value_mismatch_by_coincidence(self):
        for doc, cid in (("S100Z42X", "N020"), ("S100YYK8", "N041")):
            c24, c25 = verified(doc, "P24")[cid], verified(doc, "P25")[cid]
            self.assertEqual("VALUE_MISMATCH", c24["state"], (doc, cid))
            self.assertEqual(c24, c25, (doc, cid))
        self.assertEqual("VALUE_MISMATCH", verified("S100Z42X", "P25")["N020"]["state"])


# ====================================================================================================
class OrderOfEvidenceTest(unittest.TestCase):
    def test_i_wins_over_ii_and_iii(self):
        """(i) → (ii) → (iii) の順に見て、最初に真のものを返す。"""
        facts = [nfact(5000000), nfact(5001000, PRI)]
        self.assertEqual("same_element:" + PRI, evidence(5001000.0, 1000.0, facts[0], facts))
        self.assertEqual("digit_within_k", evidence(5001000.0, 1000.0, facts[0], facts[:1]))
        self.assertEqual("scale_10^1", evidence(50000000.0, 1000.0, facts[0], facts[:1]))

    def test_the_first_exponent_in_the_tuple_wins(self):
        named = nfact(5000000)
        # 7,777千円 の 10^-1 ではなく、50,000千円 は 1 と -1 を試し 1 が先
        self.assertEqual("scale_10^1", evidence(50000000.0, 1000.0, named, [named]))


# ====================================================================================================
class HumanDecisionsTest(unittest.TestCase):
    """触る枝の中の人間の決定(封 §1 の 8 つ)の振る舞いは P25 でも同じ。字の門は別に(period_bind_seal・rounding_seal・vocab_seal ほか)。"""

    PS = ("P22", "P23", "P24", "P25")

    def test_1_anshi_a_no_subject(self):
        """2026-10-08 案ア: 主語が取れない数は束縛しない(no_subject)。"""
        facts = [nfact(5000000)]
        for p in self.PS:
            c = by_value(num_claims(p, "5,000千円となりました。", facts), 5000000)
            self.assertEqual("no_subject", c["reason"], p)
            self.assertIsNone(c["pointer"], p)

    def test_2_1b_no_prior2_stops_without_substituting(self):
        """§1b: 前々期が無い「前期は…」の増減の語は代用せず止める(P25 の証拠の判定より先)。"""
        facts = [nfact(5000000), nfact(4000000, PRI)]
        for p in self.PS:
            c = text_claims(p, "売上高は、前期は増加しました。", facts)[0]
            self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"], p)

    def test_3_c2_period_cue_ties_to_the_prior_year(self):
        facts = [nfact(5000000), nfact(999000, PRI)]
        for p in self.PS:
            c = by_value(num_claims(p, "売上高は、前期は999千円となった。", facts), 999000)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:jppfs_cor:NetSales@" + PRI, c["pointer"], p)

    def test_4_c1g_point_diff_function_is_untouched_and_still_grounds(self):
        """C-1g §1-3 ``_build_point_diff_claim``: P25 でも同じ。本体の sha16 は P23 のとき(7d530cc)と同じ。"""
        F = [fact("EquityToAssetRatioSummaryOfBusinessResults", CUR_I, 0.436, "pure", "jpcrp_cor:"),
             fact("EquityToAssetRatioSummaryOfBusinessResults", "Prior1YearInstant", 0.385, "pure", "jpcrp_cor:")]
        s = "この結果、自己資本比率については前事業年度末と比較して5.1ポイント上昇し、43.6%となりました。"
        for p in ("P24", "P25"):
            c = by_value(num_claims(p, s, F), 5.1)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("formula:a-b(pure)", c["pointer"][-1], p)
        with open(inspect.getsourcefile(R), encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("def _build_point_diff_claim(")
        body = src[i:src.index("\ndef ", i + 1)]
        self.assertEqual("bec5cf7bd1a06b6e", hashlib.sha256(body.encode("utf-8")).hexdigest()[:16])

    def test_5_p21_last_branch_names_the_current_year_fact_when_there_is_evidence(self):
        """P21 の最後の枝: 当期の先頭 fact を名指して VALUE_MISMATCH(P21〜P25 同じ)。P25 が止めるのは証拠が無いときだけ。"""
        for s, n in ((sentence_of("5,001"), "5,001"), (sentence_of("5,002"), "5,002")):
            for p in ("P21", "P22", "P23", "P24", "P25"):
                c = lb(p, s, n, "千円", [nfact(5000000), nfact(4000000, PRI)])
                assertNamed(self, c, value=5000000.0)
        # 証拠が無いとき P21〜P24 は名指し、P25 だけ止める
        for p in ("P21", "P22", "P23", "P24"):
            assertNamed(self, lb(p, sentence_of("7,777"), "7,777", "千円", [nfact(5000000)]), value=5000000.0)
        assertUnnamed(self, lb("P25", sentence_of("7,777"), "7,777", "千円", [nfact(5000000)]))

    def test_6_p22_period_bind_does_not_tie_a_prior_value_without_a_cue_and_p25_keeps_naming_the_current_fact(self):
        """P22 ``period_bind``(``subj and``): 手がかりの無い数は Prior1Year の fact に値だけで結ばない。当期を名指す。
        P25 では Prior1Year の同じ要素に値が合う = (i) の証拠なので、同じく当期を名指す(結ばないことは変わらない)。"""
        facts = [nfact(5000000), nfact(4000000, PRI)]
        for p in self.PS:
            c = lb(p, sentence_of("4,000"), "4,000", "千円", facts)
            assertNamed(self, c, value=5000000.0)
        c = lb("P25", sentence_of("4,000"), "4,000", "千円", facts)
        self.assertEqual("same_element:" + PRI, c["last_branch_evidence"])
        # 主語が無ければ (subj and) 案ア
        for p in self.PS:
            self.assertEqual("no_subject", by_value(num_claims(p, "4,000千円となりました。", facts), 4000000)["reason"], p)

    def test_7_p23_truncation_band_is_kept(self):
        """P23 の ``_mag_trunc``: 「営業損失は23百万円」を実際の △22.989 百万円に対して止める(P25 でも VALUE_MISMATCH。差は 1 単位未満で (ii) の証拠)。"""
        facts = [fact("OperatingIncome", CUR, -22989000)]
        for p in ("P23", "P24", "P25"):
            claims = R._build_raw_num_claims(["営業損失は23百万円となった。"], facts, contexts_for(facts), V.PROFILES[p], lambda si, pos: (None, "t"), "truncate")
            c = by_value(claims, 23000000)
            self.assertEqual("VALUE_MISMATCH", c["result"], p)
        self.assertEqual("digit_within_k", c["last_branch_evidence"])

    def test_8_p24_flags_still_act_in_p25(self):
        """P24 の 2 つの旗(語彙・枠の取り直し)は P25 でも同じ結果(電池は ``FlagsOffIsP24Test`` に)。枠の取り直しは最後の枝の前で UNVERIFIABLE にする。"""
        name, kind, s, facts, member = BATTERY[4]
        ctxs = contexts_for(facts, FRAME_CONTEXTS)
        c = num_claims("P25", s, facts, ctxs, member)
        self.assertTrue(c[0]["reason"].startswith("other_frame("))
        self.assertEqual(num_claims("P24", s, facts, ctxs, member), c)
        self.assertNotIn(NSV, c[0])


# ====================================================================================================
class DocumentLevelTest(unittest.TestCase):
    """実物の書類 8 件で P24 → P25 の動きの種類を固定する(動くのは VALUE_MISMATCH → POINTER_NOT_FOUND(no_same_value)だけ)。"""

    def test_only_value_mismatch_moves_and_only_to_no_same_value(self):
        moved = 0
        for doc in DOCS:
            a, b = verified(doc, "P24"), verified(doc, "P25")
            self.assertEqual(sorted(a), sorted(b), doc)
            for cid, c in a.items():
                d = b[cid]
                if (c["state"], c["reason"], c["pointers"], c["recomputed"]) == (d["state"], d["reason"], d["pointers"], d["recomputed"]):
                    continue
                moved += 1
                self.assertEqual("VALUE_MISMATCH", c["state"], (doc, cid))
                self.assertEqual(("POINTER_NOT_FOUND", NSV, []), (d["state"], d["reason"], d["pointers"]), (doc, cid))
        self.assertGreater(moved, 0)

    def test_grounded_and_unverifiable_never_move(self):
        for doc in DOCS:
            a, b = verified(doc, "P24"), verified(doc, "P25")
            for cid, c in a.items():
                if c["state"] in ("GROUNDED", "UNVERIFIABLE"):
                    self.assertEqual(c, b[cid], (doc, cid))

    # 実物の動いた行(P25 で VALUE_MISMATCH → POINTER_NOT_FOUND)
    # S100YWGX N083「営業外費用は支払利息等、合計445百万円(前連結会計年度比20.2%増)となりました。」(名指しは支払利息 336 百万円)
    # S100YWGX N067「…配当金の支払額438百万円、借入金の純減額406百万円…」(406 を配当金の支払額 -438 百万円と照合)
    # S100YYK8 N042「…社債が20,000千円、リース債務が7,828千円、繰延税金負債が94,927千円それぞれ減少したことによるものであります。」(リース債務 10,582 千円)
    # S100YUHC N008「以上の結果、売上高は1,005億71百万円(前年同期比 0.4%増、3億96百万円増)…」(切り出した 71百万円を売上 1,005億71百万円と照合)
    def test_real_moved_rows(self):
        for doc, cid in (("S100YWGX", "N083"), ("S100YWGX", "N067"), ("S100YYK8", "N042"), ("S100YUHC", "N008")):
            c24, c25 = verified(doc, "P24")[cid], verified(doc, "P25")[cid]
            self.assertEqual("VALUE_MISMATCH", c24["state"], (doc, cid))
            self.assertEqual(("POINTER_NOT_FOUND", NSV, []), (c25["state"], c25["reason"], c25["pointers"]), (doc, cid))

    def test_real_rows_that_stay_value_mismatch(self):
        """証拠がある 6 行((i) 2・(ii) 2・(iii) 2)は P25 でも VALUE_MISMATCH で、結果は P24 と同じ。"""
        for doc, cid in (("S100YYK8", "N058"), ("S100Z3JY", "N084"), ("S100YZ7E", "N050"), ("S100YZ7E", "N060"),
                         ("S100Z42X", "N020"), ("S100YYK8", "N041")):
            self.assertEqual("VALUE_MISMATCH", verified(doc, "P25")[cid]["state"], (doc, cid))
            self.assertEqual(verified(doc, "P24")[cid], verified(doc, "P25")[cid], (doc, cid))

    def test_a_real_document_through_the_recipe_keeps_the_named_fact_in_provenance(self):
        zb = load_doc("S100YYK8")
        recs = {r.claim.id: r for r in R.build_recipes(zb, V.PROFILES["P25"])}
        rc = recs["N042"]
        self.assertEqual(NSV, rc.not_found_reason)
        self.assertEqual("xbrl:jppfs_cor:LeaseObligationsCL@" + "CurrentYearInstant", rc.claim.provenance[NSV]["named"])
        self.assertEqual(10582000.0, rc.claim.provenance[NSV]["value"])


if __name__ == "__main__":
    unittest.main()
