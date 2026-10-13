# -*- coding: utf-8 -*-
"""P20(連結・単体の落とし込み)の試験。封 docs/CONSOLIDATION_P20_PLAN_2026-10-14.md。

人間の指示(2026-10-14):「**検出件数を増やすより、違う対象の数値を正しい根拠として
扱わないことが重要**」。この試験はその順に並べる ― 先に「落とさない」ことを留め、
後に「落とす」ことを留める。
"""

import dataclasses
import io
import json
import os
import unittest
import zipfile

from adapters.xbrl import instance as I
from adapters.xbrl import vocabulary as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RESULT = os.path.join(ROOT, "fixtures", "xbrl", "p20", "result_2026-10-14.json")
SPLIT = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17", "split_2026-10-14.json")


def facts(*pairs):
    return [{"name": n, "context": c, "unit": "JPY", "decimals": "-6", "value": 1.0} for n, c in pairs]


def ctxs(**kw):
    return {cid: {"instant": None, "start": None, "end": None, "members": list(members)}
            for cid, members in kw.items()}


class ClassificationTest(unittest.TestCase):
    """``consolidated_element_count`` ― **連結が在るかどうかの判定**。"""

    def test_japanese_gaap_elements_count(self):
        self.assertEqual(2, I.consolidated_element_count(facts(
            ("jppfs_cor:Assets", "CurrentYearInstant"),
            ("jppfs_cor:NetAssets", "CurrentYearInstant"))))

    def test_ifrs_elements_count_too(self):
        """**IFRS だけを使う会社を「連結が無い」に分類しない。**

        2026-10-14 に ``jppfs_cor`` だけで数えて S100YYQX(連結枠 131 要素・
        一致 40%)を実際に誤分類した。封 §1-1 の落とし穴そのもの。
        """

        self.assertEqual(2, I.consolidated_element_count(facts(
            ("jpigp_cor:Assets", "CurrentYearInstant"),
            ("jpigp_cor:Equity", "CurrentYearDuration"))))

    def test_both_prefixes_are_named_in_the_constant(self):
        self.assertEqual(("jppfs_cor:", "jpigp_cor:"), I.FINANCIAL_PREFIXES)

    def test_same_element_twice_counts_once(self):
        self.assertEqual(1, I.consolidated_element_count(facts(
            ("jppfs_cor:Assets", "CurrentYearInstant"),
            ("jppfs_cor:Assets", "Prior1YearInstant"))))

    def test_nonfinancial_elements_do_not_count(self):
        """提出情報(``jpdei_cor``)や本文(``jpcrp_cor``)は連結の証拠にしない。"""

        self.assertEqual(0, I.consolidated_element_count(facts(
            ("jpdei_cor:NumberOfSubmissionDEI", "CurrentYearInstant"),
            ("jpcrp_cor:NetSales", "CurrentYearDuration"))))

    def test_member_contexts_do_not_count(self):
        """単体やセグメントの枠に在る財務の要素は、連結の証拠にしない。"""

        self.assertEqual(0, I.consolidated_element_count(facts(
            ("jppfs_cor:Assets", "CurrentYearInstant_NonConsolidatedMember"),
            ("jppfs_cor:Assets", "CurrentYearDuration_ParkingMember"))))

    def test_one_consolidated_element_is_enough_to_stay_consolidated(self):
        """**1 種でも在れば落とさない。**(判断できない書類では止まる = 保留。)"""

        n = I.consolidated_element_count(facts(("jppfs_cor:Assets", "CurrentYearInstant")))
        self.assertEqual(1, n)
        self.assertNotEqual(0, n)


class DoesNotFireTest(unittest.TestCase):
    """**落とさない**ほうを先に留める(C-1 がこの直しの本体)。"""

    def setUp(self):
        self.contexts = ctxs(CurrentYearInstant=(),
                             CurrentYearInstant_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))

    def test_flag_off_returns_the_same_object(self):
        f = facts()
        out = I.with_nonconsolidated_fallback(self.contexts, f, False)
        self.assertIs(self.contexts, out)
        self.assertFalse(getattr(out, "nonconsolidated_ok", False))

    def test_consolidated_document_returns_the_same_object_even_with_the_flag_on(self):
        f = facts(("jppfs_cor:Assets", "CurrentYearInstant"))
        out = I.with_nonconsolidated_fallback(self.contexts, f, True)
        self.assertIs(self.contexts, out)

    def test_ifrs_document_returns_the_same_object_even_with_the_flag_on(self):
        f = facts(("jpigp_cor:Assets", "CurrentYearInstant"))
        self.assertIs(self.contexts, I.with_nonconsolidated_fallback(self.contexts, f, True))

    def test_without_the_decision_a_nonconsolidated_context_is_not_plain(self):
        self.assertFalse(I.plain_context("CurrentYearInstant_NonConsolidatedMember", self.contexts))

    def test_a_plain_context_stays_plain_in_both_states(self):
        on = I.with_nonconsolidated_fallback(self.contexts, facts(), True)
        self.assertTrue(I.plain_context("CurrentYearInstant", self.contexts))
        self.assertTrue(I.plain_context("CurrentYearInstant", on))

    def test_breakdown_contexts_never_become_plain(self):
        """member が 2 つ以上(資本金・自己株式などの内訳)は**落とさない**。

        内訳を素の枠として扱うと、本文の合計の数が内訳の数に結びつく。
        """

        c = ctxs(CurrentYearInstant_NonConsolidatedMember_CapitalStockMember=(
            "jppfs_cor:NonConsolidatedMember", "jppfs_cor:CapitalStockMember"))
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertTrue(on.nonconsolidated_ok)
        self.assertFalse(I.plain_context(
            "CurrentYearInstant_NonConsolidatedMember_CapitalStockMember", on))

    def test_segment_member_lookup_is_unchanged_by_the_decision(self):
        """``ctx_ok`` に member を渡す引き(セグメント)は 1 行も変えない。"""

        c = ctxs(CurrentYearDuration_ParkingMember=("m:Parking",),
                 CurrentYearInstant_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        for contexts in (c, on):
            self.assertTrue(I.ctx_ok("CurrentYearDuration_ParkingMember", contexts, "m:Parking"))
            self.assertFalse(I.ctx_ok("CurrentYearInstant_NonConsolidatedMember", contexts, "m:Parking"))


class FiresTest(unittest.TestCase):
    """**落とす**ほう。連結が 1 種も無い書類でだけ。"""

    def setUp(self):
        self.contexts = ctxs(CurrentYearInstant=(),
                             CurrentYearInstant_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",),
                             Prior1YearDuration_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))
        self.on = I.with_nonconsolidated_fallback(
            self.contexts, facts(("jpdei_cor:NumberOfSubmissionDEI", "CurrentYearInstant")), True)

    def test_the_decision_is_recorded_on_the_contexts(self):
        self.assertIsNot(self.contexts, self.on)
        self.assertTrue(self.on.nonconsolidated_ok)
        self.assertIsInstance(self.on, I.DocumentContexts)

    def test_the_contents_are_unchanged(self):
        """**context の id も中身も書き換えない。**

        別名を張ると pointer が名乗る枠と値の出どころがずれ、「違う対象の数値を
        正しい根拠として扱う」ことになる(2026-10-14 の人間の指示)。
        """

        self.assertEqual(dict(self.contexts), dict(self.on))
        self.assertEqual(sorted(self.contexts), sorted(self.on))

    def test_single_member_nonconsolidated_contexts_become_plain(self):
        for cid in ("CurrentYearInstant_NonConsolidatedMember", "Prior1YearDuration_NonConsolidatedMember"):
            self.assertTrue(I.plain_context(cid, self.on), cid)

    def test_the_member_value_carries_a_prefix(self):
        """member は ``jppfs_cor:NonConsolidatedMember`` と**接頭辞つき**で入っている。

        2026-10-14 に裸の局所名で比べて 1 件も当たらず、「旗が効かない」と読み違えた
        (記録「『0 件』を根拠にする前に、その 0 が自分の欠陥でないかを確かめる」)。
        接頭辞は会社によって変わりうるので、どちらでも当たらなければならない。
        """

        for member in ("jppfs_cor:NonConsolidatedMember", "jpigp_cor:NonConsolidatedMember",
                       "NonConsolidatedMember"):
            c = ctxs(CurrentYearInstant_NonConsolidatedMember=(member,))
            on = I.with_nonconsolidated_fallback(c, facts(), True)
            self.assertTrue(I.plain_context("CurrentYearInstant_NonConsolidatedMember", on), member)

    def test_another_single_member_context_does_not_become_plain(self):
        """単体以外の member 1 つの枠(セグメント)は素にしない。"""

        c = ctxs(CurrentYearDuration_ParkingMember=("m:Parking",))
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertTrue(on.nonconsolidated_ok)
        self.assertFalse(I.plain_context("CurrentYearDuration_ParkingMember", on))

    def test_unknown_context_id_is_not_plain(self):
        self.assertFalse(I.plain_context("NoSuchContext_NonConsolidatedMember", self.on))


# ---------------------------------------------------------------------------
# 合成の書類 1 件。本文は「総資産は1,234百万円」。fact を置く枠だけを差し替えて
# 2 通りを作る。**書類そのものはこの試験の中で作るが、P16 の既定は
# ``taxonomy_labels=True`` なので標準ラベルのキャッシュ
# (``~/.cache/audit-core/edinet-taxonomy``)は読む**(無ければ ``FileNotFoundError``)。
# 「この試験だけで完結する」とは書かない ― 既存の ``test_recipes`` と同じ前提。
# ---------------------------------------------------------------------------
_XBRL = """<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
 xmlns:jppfs_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/cor"
 xmlns:jpcrp_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/cor"
 xmlns:xbrldi="http://xbrl.org/2006/xbrldi">
 <xbrli:context id="CurrentYearInstant">
  <xbrli:entity><xbrli:identifier scheme="s">E1</xbrli:identifier></xbrli:entity>
  <xbrli:period><xbrli:instant>2026-03-31</xbrli:instant></xbrli:period>
 </xbrli:context>
 <xbrli:context id="CurrentYearInstant_NonConsolidatedMember">
  <xbrli:entity><xbrli:identifier scheme="s">E1</xbrli:identifier>
   <xbrli:segment><xbrldi:explicitMember dimension="jppfs_cor:ConsolidatedOrNonConsolidatedAxis">jppfs_cor:NonConsolidatedMember</xbrldi:explicitMember></xbrli:segment>
  </xbrli:entity>
  <xbrli:period><xbrli:instant>2026-03-31</xbrli:instant></xbrli:period>
 </xbrli:context>
 <xbrli:unit id="JPY"><xbrli:measure>iso4217:JPY</xbrli:measure></xbrli:unit>
 %(FACTS)s
 <jpcrp_cor:ManagementAnalysisOfFinancialPositionTextBlock contextRef="CurrentYearInstant">&lt;p&gt;当期末の総資産は1,234百万円となりました。&lt;/p&gt;</jpcrp_cor:ManagementAnalysisOfFinancialPositionTextBlock>
</xbrli:xbrl>
"""

_NC_FACT = ('<jppfs_cor:Assets contextRef="CurrentYearInstant_NonConsolidatedMember"'
            ' unitRef="JPY" decimals="-6">1234000000</jppfs_cor:Assets>')
# **本文の 1,234 と一致しない**連結の値。連結が在る書類で落とし込みが起きれば、
# 単体の 1,234 を掴んで GROUNDED になってしまう ― それを直接見る。
_CONS_FACT = ('<jppfs_cor:Assets contextRef="CurrentYearInstant"'
              ' unitRef="JPY" decimals="-6">9999000000</jppfs_cor:Assets>')


def synth_zip(facts_xml):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E1_2026-03-31_01_2026-06-01.xbrl",
                   (_XBRL % {"FACTS": facts_xml}).encode("utf-8"))
    return buf.getvalue()


class BehaviourTest(unittest.TestCase):
    """**本番の経路を端から端まで通す。**``build_raw_claims`` から見た振る舞い。"""

    def rows(self, facts_xml, profile):
        from adapters.xbrl import recipes as R
        num, _ = R.build_raw_claims(synth_zip(facts_xml), V.PROFILES[profile])
        self.assertEqual(1, len(num))
        return num[0]

    def test_nonconsolidated_only_stops_under_p16(self):
        row = self.rows(_NC_FACT, "P16")
        self.assertEqual("総資産", row["subject"])
        self.assertIsNone(row["result"])
        self.assertEqual("no_element", row["reason"])

    def test_nonconsolidated_only_grounds_under_p20(self):
        row = self.rows(_NC_FACT, "P20")
        self.assertEqual("GROUNDED", row["result"])

    def test_the_pointer_names_the_real_nonconsolidated_context(self):
        """**別名を張らない。**pointer が名乗る枠と値の出どころを一致させる。"""

        row = self.rows(_NC_FACT, "P20")
        self.assertEqual("xbrl:jppfs_cor:Assets@CurrentYearInstant_NonConsolidatedMember",
                         row["pointer"])

    def test_p20_does_not_take_the_matching_nonconsolidated_value_when_consolidated_exists(self):
        """**この試験がこの直しの本体。**

        連結の枠に 9,999 百万円が在り、本文は 1,234 百万円(= 単体の額)と書いてある。
        落とし込みが連結の在る書類でも起きるなら、単体の 1,234 を掴んで ``GROUNDED``
        になる ― つまり**違う対象の数値を正しい根拠として扱う**(2026-10-14 の人間の
        指示が禁じたもの)。P16 と P20 は**どちらも連結を指して食い違いと言う**のが正。
        """

        both = _NC_FACT + "\n " + _CONS_FACT
        for profile in ("P16", "P20"):
            row = self.rows(both, profile)
            self.assertEqual("VALUE_MISMATCH", row["result"], profile)
            self.assertEqual("xbrl:jppfs_cor:Assets@CurrentYearInstant", row["pointer"], profile)

    def test_the_two_profiles_agree_when_a_consolidated_statement_exists(self):
        both = _NC_FACT + "\n " + _CONS_FACT
        a, b = self.rows(both, "P16"), self.rows(both, "P20")
        self.assertEqual(a, b)


class ProfileShapeTest(unittest.TestCase):
    def test_p20_is_p16_plus_one_flag(self):
        p16, p20 = V.P16, V.P20
        self.assertFalse(p16.nonconsolidated_fallback)
        self.assertTrue(p20.nonconsolidated_fallback)
        self.assertEqual(dataclasses.replace(p20, name="P16", nonconsolidated_fallback=False), p16)
        self.assertIs(V.PROFILES["P20"], p20)

    def test_every_other_profile_keeps_the_flag_off(self):
        for name, p in V.PROFILES.items():
            if name == "P20":
                continue
            self.assertFalse(p.nonconsolidated_fallback, name)

    def test_default_profile_is_still_p16(self):
        """既定を変えるのは人間の決定(CLAUDE.md の委任されないもの)。"""

        self.assertEqual("P16", V.DEFAULT_PROFILE)


class WiringTest(unittest.TestCase):
    """**本番の経路から呼ばれているか。**試験が通るだけでは効いている証拠にならない
    (2026-10-09 の記録「変異が赤くなっても本番で効いているとは限らない」)。"""

    def _source(self, rel):
        with io.open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            return fh.read()

    def test_build_raw_claims_decides_once(self):
        src = self._source("adapters/xbrl/recipes.py")
        self.assertEqual(1, src.count("with_nonconsolidated_fallback"),
                         "書類レベルの判定は 1 か所だけ(2 か所に増えたら「1 度だけ」が崩れる)")

    def test_the_decision_comes_before_the_vocabulary_is_built(self):
        """語彙の組み立ても素の枠で足切りするので、**その前**に決めないと半分しか効かない。"""

        body = self._source("adapters/xbrl/recipes.py")
        body = body[body.index("def build_raw_claims("):]
        # ``def _label_subjects`` そのものではなく、**build_raw_claims の中の呼び出し**で比べる。
        self.assertLess(body.index("with_nonconsolidated_fallback"),
                        body.index("hand_rows, added, overrides = _label_subjects("))
        self.assertLess(body.index("with_nonconsolidated_fallback"),
                        body.index("flow_base = _flow_items_by_base("))

    def test_the_flag_is_read_from_the_profile(self):
        src = self._source("adapters/xbrl/recipes.py")
        self.assertIn("profile.nonconsolidated_fallback", src)


class MeasuredResultTest(unittest.TestCase):
    """封 §3 の 4 つの合格線に対する**実測**を字で留める。"""

    @classmethod
    def setUpClass(cls):
        with io.open(RESULT, encoding="utf-8") as fh:
            cls.r = json.load(fh)

    def test_measured_on_the_sealed_development_documents(self):
        with io.open(SPLIT, encoding="utf-8") as fh:
            split = json.load(fh)
        self.assertEqual(split["development"], self.r["docs"])
        self.assertEqual(8, len(self.r["docs"]))
        for doc in split["final_eval_sealed"]:
            self.assertNotIn(doc, self.r["docs"], "最終評価用の書類を開いていない")

    def test_c1_zero_rows_changed_on_consolidated_documents(self):
        self.assertEqual(6, self.r["consolidated_docs"])
        self.assertEqual(0, self.r["C1_changed_rows_on_consolidated"])
        self.assertTrue(self.r["C1_pass"])

    def test_c2_grounded_on_the_two_nonconsolidated_documents(self):
        self.assertEqual(2, self.r["nonconsolidated_docs"])
        self.assertEqual(150, self.r["C2_grounded_on_nonconsolidated"])
        self.assertEqual(231, self.r["C2_claims_on_nonconsolidated"])
        self.assertEqual(64.9, self.r["C2_rate"])
        self.assertTrue(self.r["C2_pass"])

    def test_c2_landed_inside_the_sealed_prediction(self):
        """予測 94〜165 件。**外れていたら外れたと記録する**(直してはいけない)。"""

        self.assertGreaterEqual(self.r["C2_grounded_on_nonconsolidated"], 94)
        self.assertLessEqual(self.r["C2_grounded_on_nonconsolidated"], 165)

    def test_c3_both_documents_lifted(self):
        self.assertEqual([69, 81], [x["grounded_new"] for x in self.r["C3"]])
        self.assertTrue(all(x["lifted"] for x in self.r["C3"]))

    def test_c4_overall_rate(self):
        self.assertEqual(41.8, self.r["C4_rate_base"])
        self.assertEqual(58.2, self.r["C4_rate_new"])
        self.assertTrue(self.r["C4_pass"])

    def test_the_two_zero_documents_are_the_ones_the_seal_names(self):
        zero = [r["doc"] for r in self.r["per_document"] if not r["consolidated"]]
        self.assertEqual(["S100YXGH", "S100Z5CH"], zero)
        for r in self.r["per_document"]:
            self.assertEqual(r["consolidated"], r["consolidated_elements"] > 0, r["doc"])

    def test_no_document_sits_between_zero_and_a_hundred(self):
        """封 §1 の「中間の書類が 1 件も無い」を、直し用 8 書類で留める。"""

        for r in self.r["per_document"]:
            n = r["consolidated_elements"]
            self.assertTrue(n == 0 or n >= 100, (r["doc"], n))


if __name__ == "__main__":
    unittest.main()
