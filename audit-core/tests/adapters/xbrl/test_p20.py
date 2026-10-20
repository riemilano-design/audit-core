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


class DegenerateInputTest(unittest.TestCase):
    """崩れた入力・端の入力。**変異が全部赤でも退化値の穴は残る**ので、
    変異に頼らず自分で探す(2026-10-01 の記録)。
    """

    def test_contexts_without_a_members_key(self):
        """``members`` の欄が**無い**枠(``get`` が None を返す)。"""

        c = {"CurrentYearInstant": {"instant": "2026-03-31"}}
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertTrue(I.plain_context("CurrentYearInstant", on))
        self.assertFalse(I._nonconsolidated_only("CurrentYearInstant", on))

    def test_contexts_with_members_none(self):
        c = {"X_NonConsolidatedMember": {"members": None}}
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertFalse(I.plain_context("X_NonConsolidatedMember", on))

    def test_contexts_with_an_empty_members_list(self):
        """member が空の枠は、名前に NonConsolidated が入っていなければ素。"""

        c = ctxs(CurrentYearInstant=(), X_NonConsolidatedMember=())
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertTrue(I.plain_context("CurrentYearInstant", on))
        # 名前に NonConsolidated が在るが member が空 ― 単体の member だけではないので落とさない。
        self.assertFalse(I.plain_context("X_NonConsolidatedMember", on))

    def test_empty_contexts_and_empty_facts(self):
        on = I.with_nonconsolidated_fallback({}, [], True)
        self.assertTrue(on.nonconsolidated_ok)
        self.assertEqual({}, dict(on))

    def test_an_undeclared_context_id_is_treated_as_plain(self):
        """**P16 からの既存の緩さを、変えずに留める。**

        ``contexts`` に無い cid は「member が無い」と見えるので素の枠として通る
        (``plain_context`` は P16 のときからこう振る舞う)。**P20 はこれを変えない。**

        実物で発火していないことを測った: 直し用 8 書類の fact **6,555 件すべて**が
        宣言済みの枠を指しており、**宣言の無い枠を指す fact は 0 件**(入口は 8 件とも
        ``.xbrl``。iXBRL の入口では測っていない)。
        **直す対象ではあるが、この封の範囲外**(直すと実物の件数が動きうるので、
        予測と合格線を別に立ててから当てる)。申し送りに記録した。
        """

        on = I.with_nonconsolidated_fallback({}, [], True)
        self.assertTrue(I.plain_context("anything", on))
        self.assertTrue(I.plain_context("anything", {}))
        # 名前に NonConsolidated が在る宣言の無い cid は、落とし込みの側でも通らない。
        self.assertFalse(I.plain_context("NoSuch_NonConsolidatedMember", on))

    def test_a_fact_without_a_name(self):
        """``name`` が無い / None の fact で落ちない。"""

        for bad in ({"context": "CurrentYearInstant"},
                    {"name": None, "context": "CurrentYearInstant"}):
            self.assertEqual(0, I.consolidated_element_count([bad]))

    def test_a_fact_without_a_context(self):
        self.assertEqual(0, I.consolidated_element_count([{"name": "jppfs_cor:Assets"}]))

    def test_wrapping_twice_keeps_one_decision(self):
        """二重に包んでも決定は 1 つ。中身も増えない。"""

        c = ctxs(X_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))
        once = I.with_nonconsolidated_fallback(c, facts(), True)
        twice = I.with_nonconsolidated_fallback(once, facts(), True)
        self.assertTrue(twice.nonconsolidated_ok)
        self.assertEqual(dict(once), dict(twice))
        self.assertEqual(dict(c), dict(twice))

    def test_wrapping_a_decided_document_with_the_flag_off_returns_it_unchanged(self):
        """旗が偽なら、既に決まっている入れ物も**そのまま**返る(決定を消さない)。

        消す側に倒すと「同じ書類の途中で決定が変わる」ので、消さないのが正。
        """

        c = ctxs(X_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))
        once = I.with_nonconsolidated_fallback(c, facts(), True)
        again = I.with_nonconsolidated_fallback(once, facts(), False)
        self.assertIs(once, again)
        self.assertTrue(again.nonconsolidated_ok)

    def test_exactly_one_consolidated_element_blocks_the_fallback(self):
        """**ちょうど 1 種**でも連結在りに分類する(境界)。"""

        c = ctxs(X_NonConsolidatedMember=("jppfs_cor:NonConsolidatedMember",))
        f = facts(("jppfs_cor:Assets", "CurrentYearInstant"))
        self.assertIs(c, I.with_nonconsolidated_fallback(c, f, True))

    def test_a_context_named_nonconsolidated_without_the_member(self):
        """名前に NonConsolidated が在るのに member が別物 ― 落とさない。"""

        c = ctxs(CurrentYearInstant_NonConsolidatedMember=("m:Parking",))
        on = I.with_nonconsolidated_fallback(c, facts(), True)
        self.assertFalse(I.plain_context("CurrentYearInstant_NonConsolidatedMember", on))

    def test_plain_period_contexts_constant_covers_the_four_names(self):
        self.assertEqual(("CurrentYearInstant", "CurrentYearDuration",
                          "Prior1YearInstant", "Prior1YearDuration"),
                         I.PLAIN_PERIOD_CONTEXTS)


class ProfileShapeTest(unittest.TestCase):
    def test_p20_is_p16_plus_one_flag(self):
        p16, p20 = V.P16, V.P20
        self.assertFalse(p16.nonconsolidated_fallback)
        self.assertTrue(p20.nonconsolidated_fallback)
        self.assertEqual(dataclasses.replace(p20, name="P16", nonconsolidated_fallback=False), p16)
        self.assertIs(V.PROFILES["P20"], p20)

    def test_every_other_profile_keeps_the_flag_off(self):
        for name, p in V.PROFILES.items():
            if name in ("P20", "P21"):    # P21 = P20 + last_branch_cues(封 XBRL_NAMING_FIX_SEAL_2026-10-20)
                continue
            self.assertFalse(p.nonconsolidated_fallback, name)

    def test_default_profile_is_p21(self):
        """既定を変えるのは人間の決定(CLAUDE.md の委任されないもの)。

        2026-10-14 に人間が P16 -> P20 を決めた。根拠は Q1・Q2・Q3 の 3 つの測定と独立監査 GO 2 回
        (docs/FINAL_EVAL_8_RESULT_2026-10-14.md・docs/Q2_NONCONSOLIDATED_RESULT_2026-10-14.md)。
        **engine 全体の品質合格ではない**(同じ 8 書類で E2/G = 11.6%、合格線 10% 未達)。
        2026-10-20(段 2)に P20 -> P21(人間の指示「アダプターの問題か。とにかく精度を改善して。何してもいいから」の
        委任のもと、封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2 の条件 N-4・N-5 が当たった)。
        P21 = P20 + last_branch_cues なので、P20 の連結の無い書類の落とし込みの旗は P21 でも真のまま。
        """

        self.assertEqual("P21", V.DEFAULT_PROFILE)
        self.assertTrue(V.PROFILES[V.DEFAULT_PROFILE].nonconsolidated_fallback)


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


class SuiteEvidenceTest(unittest.TestCase):
    """**結果文書に書いた試験の本数が、完走した run の数と一致すること。**

    2026-10-14 に**同じ日に 2 回**、測った数を手で書き写す所で間違えた。
    (1) 監査へ渡した依頼書に古い `pytest 1027` を残した。
    (2) 報告していた `1039` が `tests/` だけの数で、`measure/tests/` の 96 本が抜けていた。
    C-1〜C-4 は json から読んでいるので 1 回も間違えていない。**間違えたのは手で書き写した
    数だけ**なので、同じ仕組みを試験の本数にも掛ける(2026-10-08 の人間の指示
    「対策は記憶でなく実行前に赤くなる試験にする」)。

    数の出どころ: `measure/parse_suite_evidence.py` が完走したログから取り出し、
    `fixtures/xbrl/p20/suite_evidence_2026-10-14.json` に書いたもの。
    """

    @classmethod
    def setUpClass(cls):
        with io.open(os.path.join(ROOT, "fixtures", "xbrl", "p20",
                                  "suite_evidence_2026-10-14.json"), encoding="utf-8") as fh:
            cls.ev = json.load(fh)
        with io.open(os.path.join(ROOT, "docs",
                                  "CONSOLIDATION_P20_RESULT_2026-10-14.md"), encoding="utf-8") as fh:
            cls.doc = fh.read()

    def test_the_document_states_every_measured_number(self):
        for label, value in (("pytest", self.ev["pytest_passed"]),
                             ("discover", self.ev["discover_ran"]),
                             ("変異の予測一致", self.ev["mutation_predicted"])):
            self.assertIn("%d" % (value,), self.doc,
                          "%s の数 %d が結果文書に無い(書き写しが古い)" % (label, value))

    def _results_table(self):
        """結果を**今の数として示している表の行だけ**を返す(``|`` で始まる行)。

        範囲の絞り方を**同じ日に 2 回**間違えた。
        1 回目: 文書の全文を探し、**訂正の経緯を書いた表**に当たって誤って落ちた。
        2 回目: 見出しで節に絞ったが、**その節の中の自分の説明文**(「捨てた run の数
        1027・1039… がこの表に出ていないこと」)に当たった ―
        **字面の試験は自分の説明文に当たる**(2026-09-29 の記録。今日 4 回目)。

        だから**散文を一切含めず、表の行だけ**を見る。
        """

        start = self.doc.index("**完走した 1 本の run の数**")
        end = self.doc.index("### 5-2a.", start)
        return "\n".join(line for line in self.doc[start:end].split("\n")
                          if line.strip().startswith("|"))

    def test_the_results_table_is_not_empty(self):
        """**0 行なら「通った」ではなく「届いていない」。**"""

        rows = [r for r in self._results_table().split("\n") if r.strip()]
        self.assertGreaterEqual(len(rows), 4, "表の行が取れていない(見出しの字が変わった?)")

    def test_the_results_table_states_no_superseded_number(self):
        """**捨てた run の数を、今の数の表に残さない。**

        1027(依頼書に残した古い値)・1039・1030(`tests/` だけの狭い数)・
        1141・1036(1 つ前の run の数)は、訂正の経緯や説明文でだけ使ってよい。
        """

        table = self._results_table()
        for stale in ("1027", "1039", "1030", "1141", "1036"):
            self.assertNotIn(stale, table, "今の数の表に古い数 %s が残っている" % (stale,))

    def test_the_results_table_states_the_measured_numbers(self):
        table = self._results_table()
        for label, value in (("pytest", self.ev["pytest_passed"]),
                             ("discover", self.ev["discover_ran"]),
                             ("変異の予測一致", self.ev["mutation_predicted"])):
            self.assertIn("%d" % (value,), table,
                          "%s の数 %d が今の数の表に無い" % (label, value))

    def test_the_frozen_head_is_the_one_the_document_names(self):
        self.assertIn(self.ev["head"], self.doc,
                      "凍結した HEAD %s が結果文書に無い" % (self.ev["head"],))

    def test_the_run_was_all_green(self):
        self.assertEqual(1, self.ev["mutation_misses"])
        self.assertEqual(89, self.ev["mutation_predicted"] + self.ev["mutation_misses"])
        self.assertEqual(5, self.ev["mutation_test_methods"])


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
