# -*- coding: utf-8 -*-
"""P26(「違う」に出る正しい文の主因を減らす)の試験。封 docs/XBRL_P26_SEAL_2026-10-21.md §1。

P26 = P25 + 旗 5 つ(``concept_gate``・``last_branch_digit_needs_size``・``rounded_diff_hold``・``cause_item_direction``・``numbers_2026_10_21``)。
段 1 では既定にしない(``DEFAULT_PROFILE`` = P22 のまま)。

  G1 概念の門     ``concept_gate``                 : 当てた fact が文の項目と別の概念なら、結ばず POINTER_NOT_FOUND ``other_concept``(GROUNDED には触らない)。
  G2 (ii) の穴    ``last_branch_digit_needs_size`` : P25 の証拠 (ii) は、名指す値が 2 × 主張の桁 以上のときだけ。
  G3 丸めた差     ``rounded_diff_hold``            : 丸めた 2 つの残高の差が文の数と 1 単位ずれるときは、結ばず UNVERIFIABLE ``rounded_diff_within_double_band``(**GROUNDED にはしない**)。
  G4 要因の項目   ``cause_item_direction``         : 向きの語が主語でなく要因の項目にかかる形は、結ばず UNVERIFIABLE ``direction_on_cause_item``。
  G5 数の読み取り ``numbers_2026_10_21``           : 「N兆M,MMM億円」「N万M千(L百)円」「N円MM銭」を 1 つの数に読む。

**各挙動について「当たる例」と「当たらない例」を置く。** 実物の 1 行はコメントに出典(書類・id・文)を書く。
合成の instance(facts と contexts を直接組む)に、手元の cache の実物の書類(sha256 を固定。無ければ失敗。skip しない)を足す。通信しない。
"""
import ast
import dataclasses
import hashlib
import inspect
import os
import re
import unittest

import audit_core as core

from adapters.xbrl import extract as E
from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import report_customer as RC
from adapters.xbrl import resolve as RV
from adapters.xbrl import instance as I
from adapters.xbrl import verify_document as VD
from adapters.xbrl import vocabulary as V

from . import _material as M
from .test_recipes_p24 import BATTERY, FRAME_CONTEXTS, contexts_for, fact, num_claims, text_claims, by_value
from .test_recipes_p25 import lb, nfact, sentence_of

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
CUR_I = "CurrentYearInstant"
PRI_I = "Prior1YearInstant"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")

#: 実物の書類(2026-10-22 時点の手元の cache の sha256)。
DOCS = {
    "S100YMFV": "4a5982e7447d6e0614c6ad12e7c091d462ca61a0128c2ce2af957a8bdfe1d52c",
    "S100YXGH": "29b7eb0b24e579a5b2ae9ce664d58af2d1d3cd0ffe4aec23fd7a45bd7fc36cbf",
    "S100YZ7E": "bd2fe7969c31528f9c1609c85cb2dd8bb26aad2469ee060e3227b7f9367353f3",
    "S100YYQX": "a0313840d8ecc13e8470e34f54451a0207c5510ffd0a9c3860e50c9640a9cdf0",
    "S100Z5CH": "818194e233e7ceea8f3070289776425a8f314ed647310d917a180a5bf3d5d30e",
    "S100Z3HP": "a3170c66ce46185f02e8f5274c9d4f646ef97b089d13e6f7f4e65539e8d69719",
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


FLAGS = ("concept_gate", "last_branch_digit_needs_size", "rounded_diff_hold", "cause_item_direction", "numbers_2026_10_21")
OFF = dict(concept_gate=(), last_branch_digit_needs_size=False, rounded_diff_hold=False, cause_item_direction=False, numbers_2026_10_21=False)
#: 旗を全部偽にした P26 = P25 と同じ(名前だけ違う)。
P26_OFF = dataclasses.replace(V.P26, name="P26_OFF", **OFF)
REASON_CONCEPT, REASON_DIR, REASON_HOLD = "other_concept", "direction_on_cause_item", "rounded_diff_within_double_band"


def only(flag):
    """P25 に旗を 1 つだけ足した profile(測定と同じ作り。engine には登録しない)。"""
    return dataclasses.replace(V.P25, name="P26_only_" + flag, **{flag: getattr(V.P26, flag)})


# ====================================================================================================
class FlagShapeTest(unittest.TestCase):
    def test_p26_is_p25_plus_exactly_the_five_flags(self):
        want = dataclasses.replace(V.P25, name="P26", concept_gate=("unit_family", "loose_prefix"), last_branch_digit_needs_size=True,
                                   rounded_diff_hold=True, cause_item_direction=True, numbers_2026_10_21=True)
        self.assertEqual(want, V.P26)
        self.assertIs(V.PROFILES["P26"], V.P26)

    def test_the_flags_are_false_by_default_in_the_declared_types(self):
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        self.assertEqual(((), False, False, False, False), tuple(fields[n].default for n in FLAGS))
        self.assertIsInstance(fields["concept_gate"].default, tuple)
        order = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(list(FLAGS), [n for n in order if n in FLAGS])       # 封 §1 の順

    def test_only_p26_has_any_flag_and_p26_is_the_only_new_profile(self):
        for n, p in sorted(V.PROFILES.items()):
            have = [f for f in FLAGS if getattr(p, f) != OFF[f]]
            self.assertEqual(list(FLAGS) if n == "P26" else [], have, n)
        self.assertEqual(["P26"], sorted(n for n in V.PROFILES if "P26" in n))      # 旗 1 つずつの profile・P26b は engine に登録しない

    def test_with_all_flags_false_p26_is_p25(self):
        self.assertEqual(dataclasses.replace(V.P25, name="P26_OFF"), P26_OFF)

    def test_the_default_profile_is_still_p22_in_step_1(self):
        self.assertEqual("P22", V.DEFAULT_PROFILE)
        for f in FLAGS:
            self.assertEqual(OFF[f], getattr(V.PROFILES[V.DEFAULT_PROFILE], f))

    def test_the_constants_are_pinned_in_letters(self):
        self.assertEqual(2, R.LAST_BRANCH_NAMED_MIN_K)
        self.assertEqual(2, R.ROUNDED_DIFF_BAND_X)
        self.assertEqual(REASON_HOLD, R.ROUNDED_DIFF_HOLD)
        self.assertEqual(REASON_DIR, R.CAUSE_ITEM_DIRECTION)
        self.assertEqual(REASON_CONCEPT, R.OTHER_CONCEPT)
        self.assertEqual(("百万円", "千円", "億円", "兆円", "円"), R.CONCEPT_GATE_MONEY_UNITS)
        self.assertEqual("株当たり", R.CONCEPT_GATE_PER_SHARE_WORD)
        self.assertEqual(("", "Cash", "NetCashProvidedByUsedIn", "CashFlowsFromUsedIn"), R.CONCEPT_GATE_PREFIX_OK)
        self.assertEqual(("等の", "などの"), R.CAUSE_ITEM_LIST_TAILS)
        self.assertEqual(("等によ", "などによ"), R.CAUSE_ITEM_AFTER)
        self.assertEqual(("や", "・", "、"), R.CAUSE_ITEM_ENUM_HEADS)
        self.assertEqual(("などの", "等の", "の"), R.CAUSE_ITEM_ENUM_TAILS)

    def test_the_three_reasons_are_registered_in_the_right_state_and_nothing_else_is(self):
        self.assertIn(REASON_CONCEPT, RS._POINTER_NOT_FOUND_REASONS)
        self.assertNotIn(REASON_CONCEPT, RS._UNVERIFIABLE_REASONS)
        for r in (REASON_DIR, REASON_HOLD):
            self.assertIn(r, RS._UNVERIFIABLE_REASONS)
            self.assertNotIn(r, RS._POINTER_NOT_FOUND_REASONS)
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(REASON_CONCEPT, None))
        self.assertEqual("UNVERIFIABLE", R._state_of(REASON_DIR, None))
        self.assertEqual("UNVERIFIABLE", R._state_of(REASON_HOLD, None))
        registry = RS.register_all(core.Registry.default())
        self.assertEqual(core.State.POINTER_NOT_FOUND, registry.reason_state(REASON_CONCEPT))
        self.assertEqual(core.State.UNVERIFIABLE, registry.reason_state(REASON_DIR))
        self.assertEqual(core.State.UNVERIFIABLE, registry.reason_state(REASON_HOLD))
        # 正規化は足さない(G3 は一致にする照合を作らない)・比較器も足さない
        self.assertEqual(("round", "truncate", "abs+round", "abs+truncate"), tuple(RS._NORMALIZATIONS))
        self.assertEqual(10, len(RS._COMPARATORS))

    def test_the_report_has_the_three_reason_lines_in_the_to_check_section(self):
        want = {REASON_CONCEPT: "道具が当てた出典の数が、文の項目と別のもの(1 株当たりの数や、名前の一部だけが同じ別の項目)だった。文の項目の数を確かめる",
                REASON_DIR: "増加・減少の語が文の主語でなく、要因に挙げた項目にかかる。主語が増えたか減ったかは道具は判断していない",
                REASON_HOLD: "出典の前期と当期の差と 1 単位だけずれる。丸めた数どうしの差で出るずれか、1 単位の書き誤りかを道具は見分けられない。元の数で確かめる"}
        for r, ja in want.items():
            self.assertEqual(ja, RC.REASON_JA[r])
            st = "POINTER_NOT_FOUND" if r == REASON_CONCEPT else "UNVERIFIABLE"
            self.assertEqual(RC.SECTION_CHECK, RC.section_of({"state": st, "reason": r}), r)
        # 登録簿の理由 19 の全部が表にある
        reasons = set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS)
        self.assertEqual(19, len(reasons))
        self.assertEqual([], sorted(r for r in reasons if r not in RC.REASON_JA))


# ====================================================================================================
class FlagsOffIsP25Test(unittest.TestCase):
    """旗が偽なら 1 行も変わらない(封 §1)。"""

    def test_real_documents_are_identical_to_p25_with_the_flags_off(self):
        """旗の行が動く書類(G3 の S100Z5CH N051・N071、G1 の S100YYQX、G1 と G2 の S100YZ7E、G4 の S100YUHC、G4 と G5 の S100YMFV)で、
        旗を全部偽にした P26 は P25 と同じ(旗が偽なら 1 行も変わらない)。どの旗の行も、動く書類で比べる。"""
        for doc in ("S100YUHC", "S100YZ7E", "S100YMFV", "S100Z5CH", "S100YYQX"):
            zb = load_doc(doc)
            V.PROFILES["P26_OFF"] = P26_OFF
            try:
                off = VD.verify_document(zb, "P26_OFF")["claims"]
            finally:
                V.PROFILES.pop("P26_OFF", None)
            self.assertNotIn("P26_OFF", V.PROFILES)
            self.assertEqual(VD.verify_document(zb, "P25")["claims"], off, doc)
            self.assertNotEqual(VD.verify_document(zb, "P25")["claims"], VD.verify_document(zb, "P26")["claims"], doc)       # 電池が空振りでない

    def test_the_p24_battery_is_identical_in_p26(self):
        """P24 の電池 5 件(語彙・ポイント・CF 合計・枠の取り直し)は、P26 でも 1 行も変わらない。"""
        for name, kind, s, facts, member in BATTERY:
            ctxs = contexts_for(facts, FRAME_CONTEXTS)
            fn = num_claims if kind == "num" else text_claims
            self.assertEqual(fn("P25", s, facts, ctxs, member), fn("P26", s, facts, ctxs, member), name)

    def test_the_p25_last_branch_cases_are_identical_in_p26(self):
        """P25 の最後の枝の電池(証拠なし・(i)・(ii)・(iii)・値が合う)。(ii) は名指す値が 2 × 桁 以上なので G2 は動かない。"""
        cases = [("証拠なし", "7,777", [nfact(5000000), nfact(4000000, PRI)]), ("(i)", "7,777", [nfact(5000000), nfact(7777000, PRI)]),
                 ("(ii)", "5,001", [nfact(5000000), nfact(4000000, PRI)]), ("(iii)", "50,000", [nfact(5000000), nfact(4000000, PRI)]),
                 ("合う", "5,000", [nfact(5000000), nfact(4000000, PRI)])]
        for name, n, facts in cases:
            a = lb("P25", sentence_of(n), n, "千円", facts)
            b = lb("P26", sentence_of(n), n, "千円", facts)
            self.assertEqual(a, b, name)

    def test_the_flags_alone_change_only_their_own_rows(self):
        """旗を 1 つずつ足した profile は、実物 1 書類で P25 からそれぞれの理由の行だけ動かす(電池が空振りでないこと)。"""
        zb = load_doc("S100YMFV")
        base = verified("S100YMFV", "P25")
        moved = {}
        for f in FLAGS:
            p = only(f)
            V.PROFILES[p.name] = p
            try:
                got = {c["id"]: c for c in VD.verify_document(zb, p.name)["claims"]}
            finally:
                V.PROFILES.pop(p.name, None)
            moved[f] = sorted(i for i in got if (got[i]["state"], got[i]["reason"], got[i]["pointers"]) != (base[i]["state"], base[i]["reason"], base[i]["pointers"])
                              or got[i]["value"] != base[i]["value"])
        self.assertEqual(["T021", "T022", "T025", "T027", "T028"], moved["cause_item_direction"])
        self.assertEqual(["N016", "N072"], moved["numbers_2026_10_21"])
        self.assertEqual([], moved["concept_gate"])
        self.assertEqual([], moved["last_branch_digit_needs_size"])
        self.assertEqual([], moved["rounded_diff_hold"])


# ====================================================================================================
class NumbersTest(unittest.TestCase):
    """G5 ``iter_numbers_2026_10_21``。「N兆M,MMM億円」「N万M千(L百)円」「N円MM銭」を 1 つの数(円)に読む。精度は書かれた最小の位。"""

    def read(self, s):
        return [(a, b, v, u, p) for a, b, v, u, p in E.iter_numbers_2026_10_21(s)]

    def test_cho_oku_joins_into_one_number(self):
        # 実物: S100YZ7E N012「第105基準日(令和7年3月31日)比1.3%減の2兆3,471億円(当社推計)」。既存の読みは「3,471億円」だけ。
        self.assertEqual([(0, 9, 2347100000000.0, "円", 1e8)], self.read("2兆3,471億円"))
        self.assertEqual([(2, 9, 3471.0, "億円", 1e8)], E.iter_numbers("2兆3,471億円"))          # iter_numbers の字は変えない
        self.assertEqual(3840700000000.0, self.read("3兆8,407億円")[0][2])                        # S100YYRV N003
        self.assertEqual(1566900000000.0, self.read("負債総額は1兆5,669億円で")[0][2])             # S100Z4PA N037

    def test_man_sen_hyaku_joins(self):
        # 実物: S100YZ7E N010「概ね6万円から6万5千円程度のレンジ」。既存の読みは「6万円」と「5千円」。
        self.assertEqual([(0, 3, 60000.0, "円", 1e4), (5, 10, 65000.0, "円", 1e3)], self.read("6万円から6万5千円程度"))
        self.assertEqual([(0, 3, 60000.0, "円", 1e4), (7, 10, 5000.0, "円", 1e3)], E.iter_numbers("6万円から6万5千円程度"))
        self.assertEqual([(0, 7, 65500.0, "円", 1e2)], self.read("6万5千5百円"))

    def test_yen_sen_joins_with_two_decimals(self):
        # 実物: S100YMFV N016「1ドル=148円22銭」・S100Z3L6 N068「1株当たり当期純利益は142円23銭」。既存の読みは「148円」。
        self.assertEqual([(0, 7, 148.22, "円", 0.01)], self.read("148円22銭"))
        self.assertEqual([(0, 4, 148.0, "円", 1)], E.iter_numbers("148円22銭"))
        self.assertEqual(2096.83, self.read("2,096円83銭")[0][2])

    def test_a_minus_sign_is_carried(self):
        self.assertEqual(-2347100000000.0, self.read("△2兆3,471億円")[0][2])
        self.assertEqual(-148.22, self.read("△148円22銭")[0][2])

    def test_forms_that_do_not_join_are_read_as_before(self):
        for s in ("3,471億円", "5千円", "148円", "5万7千人", "2兆1億円", "1兆5,669億円で、前年から29.4%を", "売上高は5,000百万円"):
            old = [(a, b, v, u, p) for a, b, v, u, p in E.iter_numbers(s)]
            new = self.read(s)
            if s.startswith("1兆5,669億円"):
                self.assertEqual(old[1:], new[1:], s)          # 兆と億だけが変わり、後ろの率は同じ
            else:
                self.assertEqual(old, new, s)

    def test_the_flag_chooses_the_reader(self):
        s = "2兆3,471億円"
        self.assertEqual(E.iter_numbers(s), R._numbers_of(V.P25, s))
        self.assertEqual(E.iter_numbers_2026_10_21(s), R._numbers_of(V.P26, s))
        self.assertEqual(E.iter_numbers(s), R._numbers_of(P26_OFF, s))

    def test_the_claim_carries_the_joined_value_only_when_the_flag_is_true(self):
        s = "預り金残高は、前年比1.3%減の2兆3,471億円となりました。"
        old = [c for c in num_claims("P25", s, []) if c["unit"] != "%"]
        new = [c for c in num_claims("P26", s, []) if c["unit"] != "%"]
        self.assertEqual([("億円", 3471.0)], [(c["unit"], c["value"]) for c in old])
        self.assertEqual([("円", 2347100000000.0)], [(c["unit"], c["value"]) for c in new])


# ====================================================================================================
class DigitNeedsSizeTest(unittest.TestCase):
    """G2。P25 の証拠 (ii)(差 ≤ 2 単位)は、名指す値の絶対値が 2 × 主張の桁 以上のときだけ。"""

    # 実物: S100YZ7E N050「…その他の収入等1百万円ありましたが…」(名指しは 1 株当たり配当 400 円 = 差 999,600 円 ≤ 2 百万円 の偶然の近さ)
    SMALL = [fact("DividendPaidPerShareSummaryOfBusinessResults", CUR, 400, "JPYPerShares", "jpcrp_cor:")]

    def test_p25_names_a_small_value_by_digit_within_k_and_p26_does_not(self):
        s = "その他の収入等は1百万円となりました。"
        c25 = lb("P25", s, "1", "百万円", self.SMALL, subj="売上高", elems=("DividendPaidPerShareSummaryOfBusinessResults",))
        self.assertEqual("digit_within_k", c25["last_branch_evidence"])
        self.assertEqual("VALUE_MISMATCH", c25["result"])
        c26 = lb("P26", s, "1", "百万円", self.SMALL, subj="売上高", elems=("DividendPaidPerShareSummaryOfBusinessResults",))
        self.assertEqual("no_same_value", c26["reason"])
        self.assertIsNone(c26["pointer"])
        self.assertIsNone(c26["result"])
        self.assertFalse(c26["bound"])
        self.assertTrue(c26["last_branch_digit_floor"])
        self.assertIsNone(c26["last_branch_evidence"])
        self.assertEqual({"named": "xbrl:jpcrp_cor:DividendPaidPerShareSummaryOfBusinessResults@" + CUR, "value": 400.0}, c26["no_same_value"])

    def test_a_value_of_at_least_two_units_keeps_the_evidence(self):
        """名指す値 5,000,000 円 ≥ 2 × 1,000(千円の桁)なら (ii) は証拠のまま。P25 と同じ名指し。"""
        facts = [nfact(5000000), nfact(4000000, PRI)]
        c = lb("P26", sentence_of("5,001"), "5,001", "千円", facts)
        self.assertEqual("digit_within_k", c["last_branch_evidence"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(lb("P25", sentence_of("5,001"), "5,001", "千円", facts), c)

    def test_the_boundary_is_two_times_the_unit(self):
        """名指す値 1,999,999 円(< 2,000,000)は証拠にならず、2,000,000 円は証拠のまま(境界は < 2 × 主張の桁)。"""
        for value, want in ((1999999, "no_same_value"), (2000000, "value differs(segment/other period?)")):
            facts = [nfact(value)]
            c = lb("P26", "売上高は3百万円となりました。", "3", "百万円", facts)
            self.assertEqual(want, c["reason"], value)

    def test_evidence_iii_survives_a_small_named_value(self):
        """名指す値が 2 × 桁 より小さく、(iii)(桁・単位の取り違え = 10^n の帯)の証拠があるとき、G2 は (ii) を捨てて (iii) で見直し、いままでどおり名指す。
        2 百万円の文に名指す値 200,000 円: 差 1,800,000 円 ≤ 2 × 桁(P25 は (ii) で名指す)、|200,000| < 2 × 桁(G2 は (ii) を数えない)、10^1 の帯で 2 百万円 × 10^−1 に合う。"""
        facts = [nfact(200000)]
        s = "売上高は2百万円となりました。"
        c25 = lb("P25", s, "2", "百万円", facts)
        self.assertEqual("digit_within_k", c25["last_branch_evidence"])
        c = lb("P26", s, "2", "百万円", facts)
        self.assertEqual("VALUE_MISMATCH", c["result"])        # 名指しのまま(後ろの P25 の行が (ii) の字で再評価して名指す。G2 の見直しの結果は no_same_value にしないこと)
        self.assertNotEqual("no_same_value", c["reason"])
        self.assertTrue(c["last_branch_digit_floor"])
        self.assertEqual(c25["pointer"], c["pointer"])

    def test_evidence_i_survives_a_small_named_value(self):
        """同じ要素の別の期に文の値と同じ値(i)があれば、名指す値が小さくても名指しのまま(G2 は (ii) だけに条件を足す)。"""
        facts = [nfact(1200000), nfact(3000000, PRI)]          # 名指す値 1,200,000 円 < 2 × 1,000,000 円。前期の同じ要素が文の値(3 百万円)と同じ
        c = lb("P26", "売上高は3百万円となりました。", "3", "百万円", facts)
        self.assertEqual("same_element:" + PRI, c["last_branch_evidence"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual(lb("P25", "売上高は3百万円となりました。", "3", "百万円", facts), c)

    def test_it_needs_the_p25_flag_too(self):
        no_p25 = dataclasses.replace(V.P26, name="P26_NO_P25", last_branch_names_only_if_evidence=False)
        c = lb(no_p25, "その他の収入等は1百万円となりました。", "1", "百万円", self.SMALL, subj="売上高", elems=("DividendPaidPerShareSummaryOfBusinessResults",))
        self.assertEqual("value differs(segment/other period?)", c["reason"])
        self.assertNotIn("last_branch_digit_floor", c)

    def test_a_real_document_row(self):
        c25, c26 = verified("S100YZ7E", "P25")["N050"], verified("S100YZ7E", "P26")["N050"]
        self.assertEqual(("VALUE_MISMATCH", None), (c25["state"], c25["reason"]))
        self.assertEqual(("POINTER_NOT_FOUND", "no_same_value"), (c26["state"], c26["reason"]))
        self.assertEqual([], c26["pointers"])


# ====================================================================================================
def bfact(name, ctx, value, decimals):
    f = fact(name, ctx, value)
    f["decimals"] = decimals
    return f


def hold(p, sentence, number, unit, facts, sign=1, rounding="truncate", subj="流動負債", elems=("CurrentLiabilities",)):
    """``_direct_value_claim`` を書類の丸め方つきで直接呼ぶ(G3 は丸め方が決まった 2 周目だけ)。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
    prof = V.PROFILES[p] if isinstance(p, str) else p
    R._direct_value_claim(claim, sentence, a, b, sign, float(number.replace(",", "")), unit, None, subj, list(elems), None,
                          facts, contexts_for(facts), prof, rounding)
    return claim


BAL = [bfact("CurrentLiabilities", CUR_I, 11893000000, -6), bfact("CurrentLiabilities", PRI_I, 7851000000, -6)]      # 差 4,042 百万円
BAL_S = "流動負債は前期末に比べ%s百万円増加しました。"


def bal_hold(sentence_n, **kw):
    n = sentence_n
    return hold(kw.pop("p", "P26"), BAL_S % n, n, "百万円", kw.pop("facts", BAL), **kw)


class RoundedDiffHoldTest(unittest.TestCase):
    """G3。増減の文が当期末の残高の対(F3b)を選び、2 つの fact が主張の桁に丸めた値で 0 ≤ |a − b| − |文の数| < 2 × 桁 のとき、結ばず UNVERIFIABLE。GROUNDED にはしない。"""

    NAMED = ["xbrl:jppfs_cor:CurrentLiabilities@" + CUR_I, "xbrl:jppfs_cor:CurrentLiabilities@" + PRI_I]

    def test_one_unit_short_is_held_not_named(self):
        # 差 4,042 百万円 に対して文は 4,041 百万円(丸めた 2 つの残高の差で出る 1 単位のずれ)。P25 は F3b で VALUE_MISMATCH。
        c25 = bal_hold("4,041", p="P25")
        self.assertEqual(("VALUE_MISMATCH", "derived_value", self.NAMED + ["formula:a-b"]), (c25["result"], c25["form"], c25["pointer"]))
        c = bal_hold("4,041")
        self.assertIsNone(c["result"])
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["recomputed"])
        self.assertEqual(REASON_HOLD, c["reason"])
        self.assertEqual({"named": self.NAMED, "diff": 4042000000.0}, c["rounded_diff_hold"])
        self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]))

    def test_the_exact_difference_is_still_grounded_by_the_existing_rule_not_by_g3(self):
        c = bal_hold("4,042")
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual(bal_hold("4,042", p="P25"), c)
        self.assertNotIn("rounded_diff_hold", c)

    def test_g3_never_makes_a_grounded_row_over_a_grid(self):
        """文の数を差の前後 ±3 単位で動かして P25 と P26 を並べる: P26 が GROUNDED なのは P25 も GROUNDED のときだけ(新しい GROUNDED 0)。"""
        for k in range(-3, 4):
            n = "{:,}".format(4042 + k)
            a, b = bal_hold(n, p="P25"), bal_hold(n)
            if b["result"] == "GROUNDED":
                self.assertEqual("GROUNDED", a["result"], k)
        held = [k for k in range(-3, 4) if bal_hold("{:,}".format(4042 + k))["reason"] == REASON_HOLD]
        self.assertEqual([-1], held)         # 文が差より 1 単位小さい行だけ(0 ≤ |a−b| − |文| < 2 × 桁 のうち、一致の帯の外は k = -1 だけ)

    def test_two_units_short_or_larger_than_the_difference_is_not_held(self):
        for n in ("4,040", "4,039", "4,043", "4,100"):
            c = bal_hold(n)
            self.assertNotEqual(REASON_HOLD, c["reason"], n)
            self.assertEqual("VALUE_MISMATCH", c["result"], n)
            self.assertEqual(bal_hold(n, p="P25"), c, n)

    def test_the_lower_bound_is_zero_a_difference_smaller_than_the_sentence_is_not_matched(self):
        """帯の下限は 0(封 §1 G3: 0 <= |a − b| − |文の数|)。fact の差が文の数より小さい(負)ときは当てない。
        文の数が桁の整数倍でない形(1.5 百万円。facts は百万円の桁)で、差 1 百万円 − 1.5 百万円 = −0.5 百万円 は帯の外。
        (下限を −桁 にした変異は、桁の整数倍どうしの差では動かないので、この直接の試験が要る。)"""
        fa, fb = {"value": 5e6, "decimals": "-6"}, {"value": 4e6, "decimals": "-6"}
        self.assertFalse(R._rounded_diff_match(fa, fb, 1.5e6, 1e6))
        self.assertTrue(R._rounded_diff_match(fa, fb, 1.0e6, 1e6))        # 差と文の数が同じ(0)は当たる
        self.assertTrue(R._rounded_diff_match(fa, fb, -1.0e6, 1e6))       # 文の数は絶対値で比べる
        self.assertTrue(R._rounded_diff_match(fa, fb, 0.0, 1e6))           # 差 1 百万円・文の数 0: 1 単位ずれ = 帯の中
        self.assertFalse(R._rounded_diff_match(fa, fb, -1.5e6, 1e6))

    def test_the_round_mode_holds_too(self):
        c = bal_hold("4,041", rounding="round")
        self.assertEqual(REASON_HOLD, c["reason"])
        self.assertNotEqual(REASON_HOLD, bal_hold("4,041", p="P25", rounding="round")["reason"] or "")

    def test_a_decrease_is_held_the_same_way(self):
        facts = [bfact("CurrentLiabilities", CUR_I, 7851000000, -6), bfact("CurrentLiabilities", PRI_I, 11893000000, -6)]
        c = hold("P26", "流動負債は前期末に比べ4,041百万円減少しました。", "4,041", "百万円", facts, sign=-1)
        self.assertEqual(REASON_HOLD, c["reason"])
        self.assertEqual(-4042000000.0, c["rounded_diff_hold"]["diff"])

    def test_the_first_pass_is_not_touched(self):
        """書類の丸め方を決める 1 周目(rounding が None)は P25 のまま(丸めの根拠を数える軸なので動かさない)。"""
        c = bal_hold("4,041", rounding=None)
        self.assertNotEqual(REASON_HOLD, c["reason"])
        self.assertEqual(bal_hold("4,041", p="P25", rounding=None), c)

    def test_the_precision_of_both_facts_must_equal_the_claim_scale(self):
        for d1, d2 in ((-3, -3), (-6, -3), (-3, -6), (None, None), ("INF", "INF"), (-6, None)):
            facts = [bfact("CurrentLiabilities", CUR_I, 11893000000, d1), bfact("CurrentLiabilities", PRI_I, 7851000000, d2)]
            if d1 is None:
                facts[0].pop("decimals")
            if d2 is None:
                facts[1].pop("decimals")
            c = bal_hold("4,041", facts=facts)
            self.assertNotEqual(REASON_HOLD, c["reason"], (d1, d2))
        c = bal_hold("4,041", facts=BAL)
        self.assertEqual(REASON_HOLD, c["reason"])

    def test_only_a_current_balance_with_a_prior_pair_and_a_difference_sentence(self):
        # 期間(Duration)の fact: F3b の対ではない
        dur = [bfact("CurrentLiabilities", CUR, 11893000000, -6), bfact("CurrentLiabilities", PRI, 7851000000, -6)]
        self.assertNotEqual(REASON_HOLD, bal_hold("4,041", facts=dur)["reason"])
        # 前期の対が無い
        self.assertNotEqual(REASON_HOLD, bal_hold("4,041", facts=BAL[:1])["reason"])
        # 増減の文でない(値そのものの文): 12,000 は 当期末の残高ではない値
        c = hold("P26", "流動負債は11,892百万円となりました。", "11,892", "百万円", BAL)
        self.assertNotEqual(REASON_HOLD, c["reason"])

    def test_the_flag_alone_is_enough_and_false_means_p25(self):
        self.assertEqual(REASON_HOLD, bal_hold("4,041", p=only("rounded_diff_hold"))["reason"])
        self.assertEqual("VALUE_MISMATCH", bal_hold("4,041", p="P25")["result"])       # 旗の無い側が止めていること(対の両方が止めていると、旗のガードを外す変異が黙る)
        self.assertEqual(bal_hold("4,041", p="P25"), bal_hold("4,041", p=P26_OFF))

    def test_the_recipe_keeps_the_named_pair_in_provenance_and_no_pointer(self):
        c = bal_hold("4,041")
        raw = dict(c, id="N001", sentence=0, span="x", unit="百万円", subject="流動負債")
        rc = R.claim_to_recipe(raw, "num")
        self.assertEqual(REASON_HOLD, rc.unverifiable_reason)
        self.assertIsNone(rc.not_found_reason)
        self.assertEqual([], list(rc.pointers))
        self.assertEqual({"named": self.NAMED, "diff": 4042000000.0}, rc.claim.provenance["rounded_diff_hold"])

    def test_real_document_rows(self):
        # 実物: S100Z5CH N071「純資産の残高は、936,812千円(前事業年度は935,386千円)となり1,425千円増加しました。」(差 1,426 千円)
        c25, c26 = verified("S100Z5CH", "P25")["N071"], verified("S100Z5CH", "P26")["N071"]
        self.assertEqual("VALUE_MISMATCH", c25["state"])
        self.assertEqual(("UNVERIFIABLE", REASON_HOLD, []), (c26["state"], c26["reason"], c26["pointers"]))
        # 実物の書類で P26 が GROUNDED にした行は、P25 でも GROUNDED(新しい GROUNDED 0)
        a, b = verified("S100Z5CH", "P25"), verified("S100Z5CH", "P26")
        self.assertEqual([], sorted(i for i in b if b[i]["state"] == "GROUNDED" and a[i]["state"] != "GROUNDED"))

    def test_core_turns_it_into_unverifiable_with_the_registered_reason_and_no_pointer(self):
        zb = load_doc("S100Z5CH")
        inst = I.load_instance(zb)
        recs = R.build_recipes(zb, V.PROFILES["P26"])
        res = {r.claim_id: r for r in core.verify_all(recs, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))}
        self.assertEqual("UNVERIFIABLE", res["N071"].state.name)
        self.assertEqual(REASON_HOLD, res["N071"].reason)
        self.assertEqual(0, len(res["N071"].pointers))
        rc = [r for r in recs if r.claim.id == "N071"][0]
        self.assertEqual(2, len(rc.claim.provenance["rounded_diff_hold"]["named"]))


# ====================================================================================================
class CauseItemFormTest(unittest.TestCase):
    """G4。向きの語が主語でなく要因の項目にかかる形 A・C と、主語が列挙の 1 つである除外。"""

    @staticmethod
    def form(s, subj, word):
        return R._cause_item_form(s, s.rfind(word), word, subj)

    def test_form_a_money_then_to_no_then_the_word(self):
        # 実物: S100YMFV T021「…売上債権の減少額61百万円等の増加によるものであります。」(増加は資金の増加要因にかかる)
        s = "税金等調整前当期純利益294百万円、減価償却費133百万円、売上債権の減少額61百万円等の増加によるものであります。"
        self.assertEqual("A", self.form(s, "売上債権", "増加"))
        # S100YUHC T053「…無形固定資産の取得による支出8億15百万円などの減少要因によるものであります。」(などの)
        s2 = "有形固定資産の取得による支出18億44百万円、無形固定資産の取得による支出8億15百万円などの減少要因によるものであります。"
        self.assertEqual("A", self.form(s2, "無形固定資産の取得による支出", "減少"))

    def test_form_a_needs_a_money_number_between_the_subject_and_the_word(self):
        self.assertIsNone(self.form("売上債権等の増加によるものであります。", "売上債権", "増加"))
        self.assertIsNone(self.form("売上債権の増加によるものであります。", "売上債権", "増加"))
        self.assertIsNone(self.form("売上債権の増加額61百万円によるものであります。", "売上債権", "増加"))      # 語の直前が「の」でも金額の後でも「等の」でない

    def test_form_c_no_then_the_word_then_to_yo(self):
        # 実物: S100YXGH T037「販売費及び一般管理費は、委託費の減少等により169,867千円(前年同期比16.8%減)となりました。」
        s = "販売費及び一般管理費は、委託費の減少等により169,867千円(前年同期比16.8%減)となりました。"
        self.assertEqual("C", self.form(s, "販売費及び一般管理費", "減少"))
        self.assertEqual("C", self.form("営業外費用は、譲渡制限付株式関連費用の増加などにより増えた。", "営業外費用", "増加"))

    def test_form_c_does_not_hit_the_subjects_own_direction(self):
        """gap が「の」だけ(主語そのものの増減)は当てない。語の後ろが「等により」でなければ当てない。"""
        self.assertIsNone(self.form("売上高の増加等により営業利益が増えました。", "売上高", "増加"))
        self.assertIsNone(self.form("販売費及び一般管理費は、委託費の減少により減りました。", "販売費及び一般管理費", "減少"))

    def test_the_exclusion_the_subject_is_one_of_an_enumeration(self):
        # 実物: S100Z3HP T005「…減価償却費や水道光熱費の減少等により…」(主語の減価償却費は語のかかる列挙の 1 つ)
        for head in ("や", "・", "、"):
            s = "販売費及び一般管理費は、減価償却費%s水道光熱費の減少等により増えました。" % head
            self.assertIsNone(self.form(s, "減価償却費", "減少"), head)
        for tail in ("などの", "等の"):
            s = "販売費及び一般管理費は、減価償却費や水道光熱費%s減少等により増えました。" % tail
            self.assertIsNone(self.form(s, "減価償却費", "減少"), tail)

    def test_the_exclusion_is_closed_by_digits_particles_and_brackets(self):
        for mid in ("や2店舗の", "や２店舗の", "や費用は異なるものの", "や費用が異なるものの", "や費用を除くものの", "や費用に係るものの", "や費用でのものの",
                    "や費用。次の", "や(費用)の", "や（費用）の", "やの"):
            s = "販売費及び一般管理費は、減価償却費%s減少等により増えました。" % mid
            self.assertEqual("C", self.form(s, "減価償却費", "減少"), mid)

    def test_the_gap_runs_from_the_last_occurrence_of_the_subject(self):
        """主語が語より前に 2 回出るとき、gap は最後の出現の後ろから。最初の出現からだと、前の節の金額が gap に入って形 A に当たってしまう。"""
        s = "売上債権の減少額61百万円と売上債権等の増加によるものです。"
        self.assertIsNone(self.form(s, "売上債権", "増加"))                       # 最後の「売上債権」からの gap は「等の」だけ = 金額なし
        self.assertEqual("A", self.form("売上債権は安定した。売上債権の減少額61百万円等の増加によるものです。", "売上債権", "増加"))   # 最後の出現からでも金額が入る

    def test_a_subject_that_is_not_before_the_word_is_not_hit(self):
        self.assertIsNone(R._cause_item_form("増加等により", 0, "増加", "売上高"))
        self.assertIsNone(R._cause_item_form("売上高の増加等により", 4, "増加", ""))


class CauseItemGateTest(unittest.TestCase):
    SENT = ["販売費及び一般管理費は、委託費の減少等により169,867千円となりました。"]

    def claim(self, **kw):
        c = {"id": "T001", "sentence": 0, "pos": self.SENT[0].index("減少"), "word": "減少", "subject": "販売費及び一般管理費",
             "pointer": ["xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@" + CUR, "builtin:sign(cur-prior)"], "bound": True, "result": "GROUNDED",
             "recomputed": -34286000.0, "reason": None, "match": "x"}
        c.update(kw)
        return c

    def test_a_grounded_row_is_also_unbound(self):
        c = self.claim()
        R._cause_item_gate(c, self.SENT)
        self.assertEqual(REASON_DIR, c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["result"])
        self.assertIsNone(c["recomputed"])
        self.assertNotIn("match", c)
        self.assertEqual({"form": "C", "named": ["xbrl:jppfs_cor:SellingGeneralAndAdministrativeExpenses@" + CUR], "was": "GROUNDED"}, c["cause_item"])
        self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]))

    def test_a_value_mismatch_row_records_was(self):
        c = self.claim(result="VALUE_MISMATCH")
        R._cause_item_gate(c, self.SENT)
        self.assertEqual("VALUE_MISMATCH", c["cause_item"]["was"])

    def test_an_already_unverifiable_row_is_untouched(self):
        for kw in (dict(result=None, reason="target_or_plan", pointer=None, bound=False, recomputed=None),
                   dict(result="UNVERIFIABLE", reason="x")):
            c = self.claim(**kw)
            before = dict(c)
            R._cause_item_gate(c, self.SENT)
            self.assertEqual(before, c)

    def test_a_row_without_word_or_subject_is_untouched(self):
        for kw in (dict(word=None), dict(subject=None), dict(subject="")):
            c = self.claim(**kw)
            before = dict(c)
            R._cause_item_gate(c, self.SENT)
            self.assertEqual(before, c)

    def test_a_row_the_forms_do_not_hit_is_untouched(self):
        c = self.claim(subject="委託費")
        before = dict(c)
        R._cause_item_gate(c, self.SENT)
        self.assertEqual(before, c)

    def test_it_is_applied_in_build_raw_claims_before_the_concept_gate_and_only_with_the_flag(self):
        src = inspect.getsource(R.build_raw_claims)
        tree = ast.parse(src)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        order = [n.func.id for n in sorted(calls, key=lambda n: (n.lineno, n.col_offset)) if n.func.id in ("_cause_item_gate", "_concept_gate")]
        self.assertEqual(["_cause_item_gate", "_concept_gate"], order)
        self.assertIn('getattr(profile, "cause_item_direction", False)', src)
        self.assertIn('getattr(profile, "concept_gate", ())', src)

    def test_real_document_rows(self):
        # 実物: S100YMFV T021・T022・T027・T028(形 A。P25 は「違う」)・T025(P25 は GROUNDED)、S100YXGH T037(形 C。P25 は GROUNDED)
        a, b = verified("S100YMFV", "P25"), verified("S100YMFV", "P26")
        for i in ("T021", "T022", "T027", "T028"):
            self.assertEqual(("VALUE_MISMATCH", "UNVERIFIABLE", REASON_DIR), (a[i]["state"], b[i]["state"], b[i]["reason"]), i)
            self.assertEqual([], b[i]["pointers"])
        self.assertEqual(("GROUNDED", "UNVERIFIABLE", REASON_DIR), (a["T025"]["state"], b["T025"]["state"], b["T025"]["reason"]))
        a, b = verified("S100YXGH", "P25"), verified("S100YXGH", "P26")
        self.assertEqual(("GROUNDED", "UNVERIFIABLE", REASON_DIR), (a["T037"]["state"], b["T037"]["state"], b["T037"]["reason"]))
        # 除外: S100Z3HP T005(減価償却費や水道光熱費の減少等により)は P25 と同じ
        self.assertEqual((verified("S100Z3HP", "P25")["T005"]["state"], verified("S100Z3HP", "P25")["T005"]["reason"]),
                         (verified("S100Z3HP", "P26")["T005"]["state"], verified("S100Z3HP", "P26")["T005"]["reason"]))


# ====================================================================================================
def gate_claim(subject, pointers, unit="千円", **kw):
    c = {"id": "N001", "subject": subject, "unit": unit, "pointer": pointers, "bound": True, "result": "VALUE_MISMATCH", "recomputed": 1.0,
         "reason": "value differs(segment/other period?)", "subject_from": None, "match": None}
    c.update(kw)
    return c


def keyed(*facts):
    return {(f["name"], f["context"]): f for f in facts}


class ConceptGateTest(unittest.TestCase):
    GATE = ("unit_family", "loose_prefix")

    def run_gate(self, claim, facts, gate=None):
        prof = dataclasses.replace(V.P26, name="G", concept_gate=self.GATE if gate is None else gate)
        R._concept_gate(claim, prof, keyed(*facts))
        return claim

    # --- unit_family
    def test_unit_family_a_per_share_fact_for_a_total_subject(self):
        # 実物の型: 総額の主語(売上高)に 1 株当たりの fact(JPYPerShares)を当てた「違う」
        f = fact("NetSales", CUR, 400, "JPYPerShares")
        c = self.run_gate(gate_claim("売上高", "xbrl:jppfs_cor:NetSales@" + CUR), [f])
        self.assertEqual(REASON_CONCEPT, c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertIsNone(c["result"])
        self.assertIsNone(c["recomputed"])
        self.assertEqual({"named": ["xbrl:jppfs_cor:NetSales@" + CUR], "why": "unit_family:JPYPerShares/total_subject"}, c["other_concept"])
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(c["reason"], c["result"]))

    def test_unit_family_a_total_fact_for_a_per_share_subject(self):
        f = fact("NetSales", CUR, 400)
        c = self.run_gate(gate_claim("1株当たり当期純利益", "xbrl:jppfs_cor:NetSales@" + CUR, unit="円"), [f])
        self.assertEqual("unit_family:JPY/per_share_subject", c["other_concept"]["why"])

    def test_unit_family_does_not_hit_matching_families_or_other_units(self):
        f_total, f_ps = fact("NetSales", CUR, 400), fact("NetSales", CUR, 400, "JPYPerShares")
        for subj, f, unit in (("売上高", f_total, "千円"), ("1株当たり当期純利益", f_ps, "円"), ("売上高", fact("NetSales", CUR, 1, "pure"), "千円"),
                              ("売上高", f_ps, "%"), ("売上高", f_ps, "ポイント")):
            c = self.run_gate(gate_claim(subj, "xbrl:jppfs_cor:NetSales@" + CUR, unit=unit), [f], gate=("unit_family",))
            self.assertEqual("value differs(segment/other period?)", c["reason"], (subj, unit))
            self.assertIsNone(c["concept_gate"])
        # 単位なし(増減の語)は金額と同じに扱う
        c = self.run_gate(gate_claim("売上高", "xbrl:jppfs_cor:NetSales@" + CUR, unit=None), [f_ps], gate=("unit_family",))
        self.assertEqual(REASON_CONCEPT, c["reason"])

    def test_unit_family_looks_at_every_xbrl_pointer(self):
        a, b = fact("NetSales", CUR, 1), fact("NetSales", PRI, 400, "JPYPerShares")
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:NetSales@" + CUR, "xbrl:jppfs_cor:NetSales@" + PRI, "formula:a-b"]), [a, b], gate=("unit_family",))
        self.assertEqual(REASON_CONCEPT, c["reason"])
        self.assertEqual(2, len(c["other_concept"]["named"]))          # xbrl の pointer だけ(formula は入れない)

    # --- loose_prefix
    def test_loose_prefix_a_name_that_only_contains_the_vocabulary_element(self):
        # 実物: S100YZ7E T005「売上高は増収基調…」の名指しは UnearnedRevenue(売上高 = NetSales / Revenue の Revenue を含むだけ)
        f = fact("UnearnedRevenue", CUR_I, 0)
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I]), [f], gate=("loose_prefix",))
        self.assertEqual(REASON_CONCEPT, c["reason"])
        self.assertEqual("loose_prefix:UnearnedRevenue", c["other_concept"]["why"])

    def test_loose_prefix_does_not_hit_an_exact_name_or_the_summary_names_or_ok_prefixes(self):
        for name in ("NetSales", "NetSalesSummaryOfBusinessResults", "Revenue", "CashRevenue", "NetCashProvidedByUsedInRevenue", "CashFlowsFromUsedInRevenue"):
            f = fact(name, CUR, 1)
            c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:%s@%s" % (name, CUR)]), [f], gate=("loose_prefix",))
            self.assertEqual("value differs(segment/other period?)", c["reason"], name)

    def test_loose_prefix_income_loss_summary_name_is_exact(self):
        # e の Income を IncomeLoss にして + SummaryOfBusinessResults も完全一致(語彙の要素 OperatingIncome の主語)
        elems = R._elements_for_word(V.P26.subjects, "営業利益")
        e = elems[0]
        name = e.replace("Income", "IncomeLoss") + "SummaryOfBusinessResults"
        c = self.run_gate(gate_claim("営業利益", ["xbrl:jpcrp_cor:%s@%s" % (name, CUR)]), [fact(name, CUR, 1, prefix="jpcrp_cor:")], gate=("loose_prefix",))
        self.assertEqual("value differs(segment/other period?)", c["reason"])

    def test_loose_prefix_needs_all_of_the_matching_elements_to_have_a_bad_prefix(self):
        """主語の語に要素が 2 つ以上あり、1 つでも前置きが許す字(「」・Cash…)なら当てない(その全部で、が条件)。"""
        elems = R._elements_for_word(V.P26.subjects, "売上高")
        self.assertEqual(["NetSales", "Revenue"], list(elems))
        # "CashNetSalesRevenue": NetSales の前は Cash(許す)、Revenue の前は CashNetSales(許さない) → 1 つでも許せば当てない
        f = fact("CashNetSalesRevenue", CUR, 1)
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:CashNetSalesRevenue@" + CUR]), [f], gate=("loose_prefix",))
        self.assertEqual("value differs(segment/other period?)", c["reason"])
        # 全部が許さない前置き
        f = fact("UnearnedNetSalesRevenue", CUR, 1)
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedNetSalesRevenue@" + CUR]), [f], gate=("loose_prefix",))
        self.assertEqual(REASON_CONCEPT, c["reason"])

    def test_loose_prefix_is_skipped_for_flow_item_and_ratio_table_subjects(self):
        f = fact("UnearnedRevenue", CUR_I, 0)
        for sf in ("flow_item", "ratio_table"):
            c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I], subject_from=sf), [f], gate=("loose_prefix",))
            self.assertEqual("value differs(segment/other period?)", c["reason"], sf)
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I], subject_from="label"), [f], gate=("loose_prefix",))
        self.assertEqual(REASON_CONCEPT, c["reason"])

    def test_loose_prefix_uses_the_first_xbrl_pointer_only(self):
        a, b = fact("NetSales", CUR, 1), fact("UnearnedRevenue", PRI, 0)
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:NetSales@" + CUR, "xbrl:jppfs_cor:UnearnedRevenue@" + PRI]), [a, b], gate=("loose_prefix",))
        self.assertEqual("value differs(segment/other period?)", c["reason"])

    def test_the_order_is_unit_family_then_loose_prefix(self):
        f = fact("UnearnedRevenue", CUR_I, 0, "JPYPerShares")
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I]), [f])
        self.assertTrue(c["other_concept"]["why"].startswith("unit_family:"))

    # --- 触らない行
    def test_grounded_unbound_and_pointerless_rows_are_untouched(self):
        f = fact("UnearnedRevenue", CUR_I, 0, "JPYPerShares")
        for kw in (dict(result="GROUNDED"), dict(bound=False), dict(pointer=None), dict(pointer=["formula:a-b"]), dict(pointer=[])):
            c = gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I])
            c.update(kw)
            before = dict(c)
            self.run_gate(c, [f])
            self.assertEqual(before, {k: v for k, v in c.items() if k != "concept_gate"}, kw)      # 門が何も見つけなかった印(concept_gate = None)だけが付く
            self.assertNotEqual(REASON_CONCEPT, c["reason"], kw)

    def test_a_sign_row_with_zero_difference_is_not_counted_as_grounded(self):
        """``builtin:sign(cur-prior)`` を名指し再計算の差がちょうど 0 の行は、raw が GROUNDED でも GROUNDED と数えない(門を通す)。"""
        f = fact("UnearnedRevenue", CUR_I, 0)
        zero = gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I, "builtin:sign(cur-prior)"], result="GROUNDED", recomputed=0)
        self.run_gate(zero, [f], gate=("loose_prefix",))
        self.assertEqual(REASON_CONCEPT, zero["reason"])
        nonzero = gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I, "builtin:sign(cur-prior)"], result="GROUNDED", recomputed=5)
        self.run_gate(nonzero, [f], gate=("loose_prefix",))
        self.assertEqual("GROUNDED", nonzero["result"])

    def test_the_gate_never_makes_a_grounded_row(self):
        f = fact("UnearnedRevenue", CUR_I, 0, "JPYPerShares")
        c = self.run_gate(gate_claim("売上高", ["xbrl:jppfs_cor:UnearnedRevenue@" + CUR_I]), [f])
        self.assertNotEqual("GROUNDED", c["result"])
        self.assertIsNone(c["pointer"])

    def test_an_empty_gate_changes_nothing_in_a_document(self):
        zb = load_doc("S100YZ7E")
        p = dataclasses.replace(V.P25, name="P26_G1_EMPTY", concept_gate=())
        V.PROFILES[p.name] = p
        try:
            got = VD.verify_document(zb, p.name)["claims"]
        finally:
            V.PROFILES.pop(p.name, None)
        self.assertEqual(VD.verify_document(zb, "P25")["claims"], got)

    def test_real_document_rows(self):
        # 実物: S100YZ7E T005・T006・T007・T008・T013(前受収益 UnearnedRevenue を名指していた)、S100YYQX N009(負債合計 → 契約負債)
        a, b = verified("S100YZ7E", "P25"), verified("S100YZ7E", "P26")
        for i in ("T005", "T006", "T007", "T008", "T013"):
            self.assertEqual(("VALUE_MISMATCH", "POINTER_NOT_FOUND", REASON_CONCEPT), (a[i]["state"], b[i]["state"], b[i]["reason"]), i)
            self.assertEqual([], b[i]["pointers"])
        a, b = verified("S100YYQX", "P25"), verified("S100YYQX", "P26")
        self.assertEqual(("VALUE_MISMATCH", "POINTER_NOT_FOUND", REASON_CONCEPT), (a["N009"]["state"], b["N009"]["state"], b["N009"]["reason"]))

    def test_the_recipe_keeps_the_named_facts_in_provenance_and_core_gives_pointer_not_found(self):
        zb = load_doc("S100YZ7E")
        inst = I.load_instance(zb)
        recs = R.build_recipes(zb, V.PROFILES["P26"])
        res = {r.claim_id: r for r in core.verify_all(recs, RV.make_resolver(inst["facts"]), RS.register_all(core.Registry.default()))}
        self.assertEqual("POINTER_NOT_FOUND", res["T005"].state.name)
        self.assertEqual(REASON_CONCEPT, res["T005"].reason)
        self.assertEqual(0, len(res["T005"].pointers))
        rc = [r for r in recs if r.claim.id == "T005"][0]
        self.assertEqual("loose_prefix:UnearnedRevenue", rc.claim.provenance[REASON_CONCEPT]["why"])
        self.assertEqual(2, len(rc.claim.provenance[REASON_CONCEPT]["named"]))


# ====================================================================================================
class HumanDecisionsTest(unittest.TestCase):
    """触る枝の中の人間の決定の字が、P26 の後も同じ(封 §1)。"""

    def test_g5_changes_exactly_one_existing_line_and_iter_numbers_is_untouched(self):
        src = inspect.getsource(R._build_raw_num_claims)
        self.assertIn("for (a, b, signed, unit, prec) in _numbers_of(profile, s):", src)
        self.assertEqual(1, src.count("_numbers_of(profile, s)"))
        self.assertNotIn("E.iter_numbers(s)", src)
        body = inspect.getsource(E.iter_numbers)
        self.assertIn("return sorted(_iter_numbers(s), key=lambda t: t[0])", body)
        self.assertNotIn("2026_10_21", body)

    def test_the_last_branch_p25_line_is_still_in_the_branch(self):
        body = inspect.getsource(R._direct_value_claim)
        self.assertIn('getattr(profile, "last_branch_names_only_if_evidence", False) and _last_branch_unname(claim, target, scale, rounding, mag_trunc, cur[0], facts)', body)
        # G2 はその前に、P25 の旗と一緒のときだけ
        i = body.index("_last_branch_unname_2026_10_21(")
        j = body.index("_last_branch_unname(claim, target")
        self.assertLess(i, j)
        self.assertIn('getattr(profile, "last_branch_digit_needs_size", False)', body[i - 200:i])

    def test_g3_comes_before_f3b_and_only_in_the_second_pass(self):
        body = inspect.getsource(R._direct_value_claim)
        i = body.index('getattr(profile, "rounded_diff_hold", False) and rounding is not None')
        j = body.index("# F3b: 増減の文が当期の残高を選んだときは")
        self.assertLess(i, j)

    def test_the_p21_to_p25_profile_rows_keep_their_letters(self):
        v = inspect.getsource(V)
        self.assertIn('P24 = dataclasses.replace(P23, name="P24", vocab_2026_10_21=True, frame_rebind=True)', v)
        self.assertIn('P25 = dataclasses.replace(P24, name="P25", last_branch_names_only_if_evidence=True)', v)
        self.assertEqual(1, v.count('PROFILES["P26"] = P26'))


if __name__ == "__main__":
    unittest.main()
