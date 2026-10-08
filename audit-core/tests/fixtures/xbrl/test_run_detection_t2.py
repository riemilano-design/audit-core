# -*- coding: utf-8 -*-
"""``fixtures/xbrl/run_detection_t2.py`` の純粋な判定・抽選ロジックの単体
試験。合成データだけを使う(本物の EDINET ZIP も Core の実行も要らない)。

Core/Adapter を実際に回す統合動作(段 1〜7 一式)は、本物の 3 書類に対して
``python3 fixtures/xbrl/run_detection_t2.py`` を実行した結果として
SubagentHandback の報告に書く(費用 0 円・ここでは再現しない)。
"""

import collections
import io
import os
import sys
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
if _FIXTURES_XBRL not in sys.path:
    sys.path.insert(0, _FIXTURES_XBRL)

import run_detection_t2 as D  # noqa: E402
from adapters.xbrl import extract as Ex  # noqa: E402

_MDNA_LOCAL = "ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"


def make_zip(mdna_text):
    """最小の合成 ZIP(``tests/fixtures/xbrl/test_tamper_unit.py`` の
    ``make_zip`` と同じ形。この試験ファイル単独で読めるよう、小さいので
    重複して持つ ― prepare_material.py が instance.py と strip_html を
    独立に持つのと同じ理由)。"""

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:jpcrp_cor="http://example.com/jpcrp_cor">\n'
        '<jpcrp_cor:%s contextRef="CurrentYearDuration">%s</jpcrp_cor:%s>\n'
        '</xbrli:xbrl>\n'
    ) % (_MDNA_LOCAL, mdna_text, _MDNA_LOCAL)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("XBRL/PublicDoc/test-001_2026-01-01.xbrl", xml.encode("utf-8"))
    return buf.getvalue()


class IsDetectedTest(unittest.TestCase):
    """試験 6・7: Claim が 1 件も作られなかった場合は検出に数えない(「止め
    なかった」側)。検出の判定は GROUNDED だけを通す(4 状態の表)。"""

    def test_no_claim_after_tamper_is_not_detected(self):
        self.assertFalse(D.is_detected(False, None))

    def test_four_states_table(self):
        table = [
            ("GROUNDED", False),
            ("VALUE_MISMATCH", True),
            ("POINTER_NOT_FOUND", True),
            ("UNVERIFIABLE", True),
        ]
        for state, expected in table:
            with self.subTest(state=state):
                self.assertEqual(D.is_detected(True, state), expected)

    def test_claim_present_false_wins_even_if_state_looks_grounded(self):
        """claim_present_after=False のとき、post_state の値が何であって
        も(呼び出し側のバグで GROUNDED 以外の文字列が紛れ込んだとしても)
        検出に数えてはいけない ― 作られなかった Claim の「状態」は意味を
        持たない。"""

        for bogus_state in (None, "GROUNDED", "VALUE_MISMATCH", "anything"):
            with self.subTest(bogus_state=bogus_state):
                self.assertFalse(D.is_detected(False, bogus_state))


class DrawSitesTest(unittest.TestCase):
    """試験 4・5: 抽選が決定的・種を変えると抽選が変わる。"""

    def _eligible(self, n):
        return [
            {"id": "site-%02d" % i, "siblings": ["百万円", "億円", "千円"]}
            for i in range(n)
        ]

    def test_deterministic_same_seed_same_doc(self):
        eligible = self._eligible(20)
        drawn1, units1, k1 = D.draw_sites(eligible, "seed-A", "docX", 5)
        drawn2, units2, k2 = D.draw_sites(eligible, "seed-A", "docX", 5)
        self.assertEqual(k1, k2)
        self.assertEqual([d["id"] for d in drawn1], [d["id"] for d in drawn2])
        self.assertEqual(units1, units2)

    def test_different_seed_changes_the_draw(self):
        eligible = self._eligible(20)
        drawn1, units1, _k1 = D.draw_sites(eligible, "seed-A", "docX", 5)
        drawn2, units2, _k2 = D.draw_sites(eligible, "seed-B", "docX", 5)
        ids1 = [d["id"] for d in drawn1]
        ids2 = [d["id"] for d in drawn2]
        self.assertTrue(ids1 != ids2 or units1 != units2, "changing the seed string must change something")

    def test_different_doc_changes_the_draw(self):
        """種の文字列はそのまま使う(seed + ":" + doc_id)。doc を変えても
        結果が変わることを確かめる ― 3 書類が同じ抽選を共有しない。"""

        eligible = self._eligible(20)
        drawn1, units1, _k1 = D.draw_sites(eligible, "seed-A", "doc1", 5)
        drawn2, units2, _k2 = D.draw_sites(eligible, "seed-A", "doc2", 5)
        ids1 = [d["id"] for d in drawn1]
        ids2 = [d["id"] for d in drawn2]
        self.assertTrue(ids1 != ids2 or units1 != units2)

    def test_shortfall_when_pool_smaller_than_count(self):
        eligible = self._eligible(3)
        drawn, units, k = D.draw_sites(eligible, "seed-A", "docX", 12)
        self.assertEqual(k, 3)
        self.assertEqual(len(drawn), 3)
        self.assertEqual(len(units), 3)
        self.assertEqual(sorted(d["id"] for d in drawn), sorted(e["id"] for e in eligible))

    def test_empty_pool_draws_nothing(self):
        drawn, units, k = D.draw_sites([], "seed-A", "docX", 12)
        self.assertEqual((drawn, units, k), ([], [], 0))

    def test_sibling_chosen_is_always_from_its_own_list(self):
        eligible = [
            {"id": "a", "siblings": ["百万円"]},
            {"id": "b", "siblings": ["億円", "千円"]},
            {"id": "c", "siblings": ["％"]},
        ]
        drawn, units, k = D.draw_sites(eligible, "seed-A", "docX", 3)
        self.assertEqual(k, 3)
        for d, u in zip(drawn, units):
            self.assertIn(u, d["siblings"])


class UnitTextVariantsTest(unittest.TestCase):
    def test_full_width_percent_has_half_width_variant(self):
        self.assertEqual(D._unit_text_variants("％"), sorted({"％", "%"}))

    def test_unit_with_no_nfkc_change_has_one_variant(self):
        self.assertEqual(D._unit_text_variants("千円"), ["千円"])


class FindClaimSitesByDigitsTest(unittest.TestCase):
    """対応づけが「全文一致」であること(窓の部分一致に戻っていないか)の
    回帰。書類が実際に持っていた型(密な文で隣の数の単位が窓に紛れ込む)を
    模して、exact-match だけがこれを避けられることを確かめる。"""

    def _sites(self):
        return [
            {"id": "N002", "digits": "106.0%"},
            {"id": "N003", "digits": "214億2千2百万円"},
            {"id": "N004", "digits": "106.8%"},
        ]

    def test_exact_digit_and_unit_resolves_uniquely(self):
        sites = self._sites()
        hits = D.find_claim_sites_by_digits(sites, "106.0", "％")
        self.assertEqual([h["id"] for h in hits], ["N002"])

    def test_substring_of_a_longer_digits_field_is_not_a_match(self):
        """N003 の digits は「214億2千2百万円」で、どこにも「106.8」という
        部分文字列は含まれない。だが、もし対応づけが『span の部分一致』の
        ままだったら(直した前のやり方)、窓が隣の文を含むせいで誤って
        当たってしまう型のバグだった。ここでは digits フィールド自体には
        紐がない(窓を持たない)ので、与えた入力に対して正しく 0 件になる
        ことだけを確かめる。"""

        sites = [{"id": "N003", "digits": "214億2千2百万円(同106.8%)"}]
        hits = D.find_claim_sites_by_digits(sites, "106.8", "％")
        self.assertEqual(hits, [], "digits が数字+単位ちょうどではない行を一致させてはいけない")

    def test_no_match_returns_empty(self):
        sites = self._sites()
        self.assertEqual(D.find_claim_sites_by_digits(sites, "999", "千円"), [])

    def test_true_duplicate_digits_is_reported_as_two_matches(self):
        sites = [
            {"id": "N010", "digits": "35億円"},
            {"id": "N011", "digits": "35億円"},
        ]
        hits = D.find_claim_sites_by_digits(sites, "35", "億円")
        self.assertEqual(len(hits), 2)


class NumClaimSitesExclusionTest(unittest.TestCase):
    """REVISE 2026-10-08(独立監査、1 回目): ``num_claim_sites`` が
    ``adapters.xbrl.extract.EXCLUDE_AFTER``/``EXCLUDE_CONTEXT`` の判定を
    ``recipes._build_raw_num_claims`` と同じ窓のリテラル(``s[b:b+3]``・
    ``s[max(0,a-12):b+4]``)で複製しているが、本物の 3 書類ではどちらも
    1 回も発火していなかった(監査の変異 2 本が黙った)。合成の文で両方の
    枝を実際に通し、窓を 1 文字でも変えたら赤になる(数字側の境界試験と
    同じ型)ことを確かめる。窓の長さは「ちょうど境界」になるように文を
    作ってある(詳しい計算は本文のコメントに書く)。"""

    def test_exclude_after_branch_is_exercised(self):
        """「四半期」は 3 字で ``s[b:b+3]`` の全長ちょうどを使う。数の直後に
        「四半期」が来る文を 1 つ、普通の文を 1 つ混ぜ、前者だけ Claim の
        候補から消えること(= 除外が実際に発火したこと)を確かめる。"""

        zb = make_zip("当期は3百万円四半期ごとに計上しました。当期は149百万円となりました。")
        sites = D.num_claim_sites(zb)
        self.assertEqual([s["digits"] for s in sites], ["149百万円"])

    def test_exclude_context_branch_left_boundary_is_exercised(self):
        """``注1`` の直後に「あ」を 10 字挟むと、``a-12`` の窓はちょうど
        「注1」の先頭 1 字手前まで届く(``s[a-12:...]`` が「注1あああ…」に
        なる)。1 文字でも窓を削ると「注」が落ちて発火しなくなる境界。"""

        zb = make_zip("注1" + "あ" * 10 + "3百万円を計上しました。当期は149百万円となりました。")
        sites = D.num_claim_sites(zb)
        self.assertEqual([s["digits"] for s in sites], ["149百万円"])

    def test_exclude_context_branch_right_boundary_is_exercised(self):
        """数の直後に「あ」を 2 字挟んで「注1」を置くと、``b+4`` の窓は
        ちょうど「注1」の末尾まで届く。1 文字でも窓を削ると「1」が落ちて
        発火しなくなる境界。"""

        zb = make_zip("当期は3百万円" + "あ" * 2 + "注1のとおりでした。当期は149百万円となりました。")
        sites = D.num_claim_sites(zb)
        self.assertEqual([s["digits"] for s in sites], ["149百万円"])

    def test_exclude_after_window_widening_is_a_true_equivalent_mutant(self):
        """独立監査が当てた変異のうち ``after = s[b:b+3]`` を ``s[b:b+4]``
        へ広げるものは、**数学的に真の等価変異**であることをここに書き残す
        (作り話で押し切らない)。``EXCLUDE_AFTER`` は ``re.match`` で先頭
        だけを見る(終端アンカー ``$`` が無い)ので、選択肢の最大長が 3
        である限り、窓を 3 文字より広げても ``.match()`` の真偽は入力に
        関わらず変わらない(逆に 3 未満へ縮めると「四半期」等の長い選択肢
        が切れて変わる ― それは
        ``test_exclude_after_branch_is_exercised`` で別に確かめている)。

        触れない ``adapters.xbrl.extract.EXCLUDE_AFTER`` 側で選択肢がもし
        4 文字以上に増えたら、この等価性は崩れて窓=3 は不足になる。振る舞
        いで直接ピン止めできないので、代わりに「選択肢は全部 3 文字以下」
        という前提そのものを検査する。この前提が崩れたら(=この試験が
        赤くなったら)、num_claim_sites の窓を extract.py に合わせて直す
        必要があるという合図になる。"""

        inner = Ex.EXCLUDE_AFTER.pattern
        m = __import__("re").match(r"^\^\((.*)\)$", inner)
        self.assertIsNotNone(m, "EXCLUDE_AFTER のパターンの形が想定と違う: %r" % (inner,))
        alternatives = m.group(1).split("|")
        self.assertTrue(len(alternatives) >= 1)
        too_long = [a for a in alternatives if len(a) > 3]
        self.assertEqual(
            too_long, [],
            "EXCLUDE_AFTER に 4 文字以上の選択肢が増えた: %r ― "
            "num_claim_sites の s[b:b+3] の窓を広げる必要がある" % (too_long,),
        )


class _FakeToken(object):
    """``classify_site`` は ``tok.text``/``tok.unit`` しか見ないので、本物の
    ``measure.lib.numbers.NumberToken`` を作らず最小の二属性だけ持つ。"""

    def __init__(self, text, unit):
        self.text = text
        self.unit = unit


class ClassifySiteTest(unittest.TestCase):
    """人間の指示(2026-10-08、2 回目の REVISE)§A: ①〜④ の分類順 ―
    (a) HTML の一意性より先に (b) 対応づけを見る。5 つの出口(①②③④a④b)
    を 1 つずつ合成データで確かめる。"""

    def test_bucket1_not_picked_up_when_zero_claims(self):
        tok = _FakeToken("149", "百万円")
        cls = D.classify_site(tok, ["円", "千円", "億円"], [], {}, "どこにも出てこない文字列")
        self.assertEqual(cls["bucket"], "1_not_picked_up")
        self.assertEqual(cls["claim_candidates"], 0)

    def test_bucket2_ambiguous_correspondence_when_two_or_more_claims(self):
        tok = _FakeToken("149", "百万円")
        num_sites = [
            {"id": "N001", "digits": "149百万円"},
            {"id": "N002", "digits": "149百万円"},
        ]
        cls = D.classify_site(tok, ["円"], num_sites, {}, "irrelevant")
        self.assertEqual(cls["bucket"], "2_ambiguous_correspondence")
        self.assertEqual(cls["claim_candidates"], 2)

    def test_bucket3_not_grounded_before_mixing(self):
        tok = _FakeToken("149", "百万円")
        num_sites = [{"id": "N001", "digits": "149百万円"}]
        by_id = {"N001": {"id": "N001", "state": "VALUE_MISMATCH"}}
        cls = D.classify_site(tok, ["円"], num_sites, by_id, "irrelevant")
        self.assertEqual(cls["bucket"], "3_not_grounded_before_mixing")
        self.assertEqual(cls["baseline_state"], "VALUE_MISMATCH")

    def test_bucket4a_html_ambiguous_because_two_occurrences(self):
        tok = _FakeToken("149", "百万円")
        num_sites = [{"id": "N001", "digits": "149百万円"}]
        by_id = {"N001": {"id": "N001", "state": "GROUNDED"}}
        inner = "149百万円でした。もう一度149百万円という数字が出ます。"
        cls = D.classify_site(tok, ["円"], num_sites, by_id, inner)
        self.assertEqual(cls["bucket"], "4a_html_ambiguous")
        self.assertEqual(cls["html_match_count"], 2)

    def test_bucket4a_html_ambiguous_when_inner_is_none(self):
        """MD&A の raw 位置が取れない(``locate_mdna_raw`` が失敗した)場合も
        ④a(道具の限界)に落ちる ― ①〜③ の判定とは独立。"""

        tok = _FakeToken("149", "百万円")
        num_sites = [{"id": "N001", "digits": "149百万円"}]
        by_id = {"N001": {"id": "N001", "state": "GROUNDED"}}
        cls = D.classify_site(tok, ["円"], num_sites, by_id, None)
        self.assertEqual(cls["bucket"], "4a_html_ambiguous")
        self.assertIsNone(cls["html_match_count"])

    def test_bucket4b_eligible_when_grounded_and_html_unique(self):
        tok = _FakeToken("149", "百万円")
        num_sites = [{"id": "N001", "digits": "149百万円"}]
        by_id = {"N001": {"id": "N001", "state": "GROUNDED"}}
        inner = "149百万円でした。"
        cls = D.classify_site(tok, ["円"], num_sites, by_id, inner)
        self.assertEqual(cls["bucket"], "4b_eligible")
        self.assertEqual(cls["html_match_count"], 1)

    def test_order_is_correspondence_before_html(self):
        """(a) HTML の一意性を先に見ていたら、この入力(claim 対応は 0 件=①
        だが HTML には 2 回出る)は「HTML が曖昧」に落ちてしまう。正しい順
        (b) 先なら①になることを確かめる ― 今回の REVISE の核心。"""

        tok = _FakeToken("149", "百万円")
        inner = "149百万円でした。もう一度149百万円という数字が出ます。"
        cls = D.classify_site(tok, ["円"], [], {}, inner)  # num_sites が空 = ①
        self.assertEqual(cls["bucket"], "1_not_picked_up")

    def test_five_buckets_partition_a_synthetic_population_exactly(self):
        """5 つの出口の合計が、与えた現場の総数にちょうど一致することを
        小さな合成集団で確かめる(本物の 175 件での一致は実行結果で確認済
        み。ここは unittest から再現できる最小版)。"""

        by_id = {
            "N010": {"id": "N010", "state": "GROUNDED"},
            "N011": {"id": "N011", "state": "VALUE_MISMATCH"},
        }
        cases = [
            (_FakeToken("1", "件"), [], "irrelevant"),                                   # ①
            (_FakeToken("2", "件"), [
                {"id": "Na", "digits": "2件"}, {"id": "Nb", "digits": "2件"},
            ], "irrelevant"),                                                            # ②
            (_FakeToken("3", "件"), [{"id": "N011", "digits": "3件"}], "irrelevant"),     # ③
            (_FakeToken("4", "件"), [{"id": "N010", "digits": "4件"}],
             "4件でした。もう一度4件という数字が出ます。"),                                  # ④a
            (_FakeToken("5", "件"), [{"id": "N010", "digits": "5件"}], "5件でした。"),     # ④b
        ]
        buckets = []
        for tok, num_sites, inner in cases:
            local_by_id = dict(by_id)
            if num_sites and num_sites[0]["id"] not in local_by_id:
                local_by_id[num_sites[0]["id"]] = {"id": num_sites[0]["id"], "state": "GROUNDED"}
            cls = D.classify_site(tok, ["回"], num_sites, local_by_id, inner)
            buckets.append(cls["bucket"])
        self.assertEqual(
            sorted(buckets),
            sorted(["1_not_picked_up", "2_ambiguous_correspondence", "3_not_grounded_before_mixing",
                    "4a_html_ambiguous", "4b_eligible"]),
        )
        self.assertEqual(len(buckets), 5)


class ClopperPearsonTest(unittest.TestCase):
    """人間の指示(2026-10-08、2 回目の REVISE)§B: Clopper-Pearson(正確法)
    の幅。人間自身の裏取り(30/30・片側・alpha=0.05 -> 下限=0.05**(1/30)=
    0.904966...)と、教科書の参照値(n=10,k=5,両側 -> [0.1871, 0.8129])の
    両方で合わせる。"""

    def test_matches_human_worked_check_30_of_30_one_sided(self):
        lo, hi = D.clopper_pearson(30, 30, alpha=0.05, two_sided=False)
        self.assertAlmostEqual(lo, 0.05 ** (1.0 / 30), places=12)
        self.assertEqual(hi, 1.0)

    def test_two_sided_textbook_reference_5_of_10(self):
        lo, hi = D.clopper_pearson(5, 10, alpha=0.05, two_sided=True)
        self.assertAlmostEqual(lo, 0.1871, places=3)
        self.assertAlmostEqual(hi, 0.8129, places=3)

    def test_k_zero_lower_bound_is_zero(self):
        lo, hi = D.clopper_pearson(0, 10, alpha=0.05, two_sided=True)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.0)

    def test_k_equals_n_upper_bound_is_one(self):
        lo, hi = D.clopper_pearson(10, 10, alpha=0.05, two_sided=True)
        self.assertEqual(hi, 1.0)
        self.assertGreater(lo, 0.0)

    def test_n_zero_returns_none(self):
        lo, hi = D.clopper_pearson(0, 0, alpha=0.05)
        self.assertIsNone(lo)
        self.assertIsNone(hi)

    def test_interval_widens_as_k_moves_away_from_the_edges(self):
        """k=10/n=20(中央)の方が k=19/n=20(端)より幅が広いはず(端に近い
        ほど片方の境界が 0 か 1 に近づいて幅が狭くなる、という向きの回帰)。"""

        lo_mid, hi_mid = D.clopper_pearson(10, 20, two_sided=True)
        lo_edge, hi_edge = D.clopper_pearson(19, 20, two_sided=True)
        self.assertGreater(hi_mid - lo_mid, hi_edge - lo_edge)

    def test_one_sided_lower_is_at_least_two_sided_lower(self):
        """同じ (k, n) なら、片側(全 alpha を下だけに使う)の下限は、両側
        (alpha/2 を下に使う)の下限以上になる(片側の方が条件が緩い)。"""

        lo_two, _ = D.clopper_pearson(12, 20, alpha=0.05, two_sided=True)
        lo_one, hi_one = D.clopper_pearson(12, 20, alpha=0.05, two_sided=False)
        self.assertGreaterEqual(lo_one, lo_two)
        self.assertEqual(hi_one, 1.0)


class StructuralCheckForBucket1Test(unittest.TestCase):
    """人間の指示(2026-10-08、2 回目の REVISE)§「0 件に理由を測る」:
    ``structural_check_for_bucket1`` が、本当に構造的に①=0だと言える状況
    と、除外が発火して言えない状況を言い分けることを確かめる。"""

    def test_structural_zero_true_when_no_exclusion_fires(self):
        zb = make_zip("当期は149百万円となりました。")
        raw_sites = [{"token": _FakeToken("149", "百万円"), "siblings": ["円"]}]
        result = D.structural_check_for_bucket1(zb, raw_sites)
        self.assertTrue(result["is_structural_zero"])
        self.assertEqual(result["sites_not_subset_of_iter_numbers"], 0)
        self.assertEqual(result["exclude_after_or_context_fired_for_sites"], 0)

    def test_structural_zero_false_when_site_is_not_a_subset_of_iter_numbers(self):
        """t2_sites が「現場」と見なす (number_text, unit) が、Adapter の
        ``iter_numbers`` には(除外をかけない状態でも)1 回も出てこない場合
        ― そもそも Adapter の数スキャナが認識しない単位(例: 「局」は
        extract.NUM_RE の単位リストに無い)。部分集合でないと報告される
        ことを確かめる(黙る変異の回帰: 監査が ``in_all`` を常に True にす
        る変異を当てたら黙った)。"""

        zb = make_zip("当期は149百万円となりました。")
        raw_sites = [{"token": _FakeToken("5", "局"), "siblings": ["手"]}]
        result = D.structural_check_for_bucket1(zb, raw_sites)
        self.assertFalse(result["is_structural_zero"])
        self.assertEqual(result["sites_not_subset_of_iter_numbers"], 1)
        self.assertEqual(result["not_subset_examples"][0]["number_text"], "5")

    def test_structural_zero_false_when_exclusion_fires_for_the_site(self):
        """「四半期」で EXCLUDE_AFTER が発火する現場を 1 つ混ぜると、その
        現場自身について構造的とは言えなくなる(①=0 が偶然になりうる)。"""

        zb = make_zip("当期は3百万円四半期ごとに計上しました。当期は149百万円となりました。")
        raw_sites = [
            {"token": _FakeToken("3", "百万円"), "siblings": ["円"]},
            {"token": _FakeToken("149", "百万円"), "siblings": ["円"]},
        ]
        result = D.structural_check_for_bucket1(zb, raw_sites)
        self.assertFalse(result["is_structural_zero"])
        self.assertEqual(result["exclude_after_or_context_fired_for_sites"], 1)
        self.assertEqual(result["exclude_fired_examples"][0]["number_text"], "3")


class BuildDetectionRatesTest(unittest.TestCase):
    """人間の指示(2026-10-08、3 回目の REVISE)1・2: ``build_detection_rates``
    は ``main()`` の外のモジュールレベルの純粋関数で、``defn_n = 混入数 +
    ①の件数`` の足し算はこの関数の中にある。②: ①>0 のとき、条件付きの率
    は変わらず、定義どおりの率だけが分母の増加で下がることを固定する。

    わざと 100% にならない値を使う(人間の指示: 100% を維持するために試験
    入力を選ばない)。"""

    def test_not_picked_up_zero_means_both_rates_equal(self):
        """①=0 のとき、2 つの率は(たまたま)一致する。"""

        rates = D.build_detection_rates(detected_total=9, drawn_total=10, not_picked_up_n=0)
        cond = rates["conditional_on_traceable_before_mixing"]
        defn = rates["per_definition_including_not_picked_up"]
        self.assertEqual(cond["n"], 10)
        self.assertEqual(defn["n"], 10)
        self.assertEqual(cond["rate"], defn["rate"])
        self.assertAlmostEqual(cond["rate"], 0.9)

    def test_not_picked_up_positive_lowers_only_the_per_definition_rate(self):
        """核心: 混入 10 件・検出 10 件・① 5 件 ->
        条件付き = 10/10 = 100%、定義どおり = 10/15 = 66.7%。
        条件付きの n は①の影響を受けず、定義どおりの n だけ増える。"""

        rates = D.build_detection_rates(detected_total=10, drawn_total=10, not_picked_up_n=5)
        cond = rates["conditional_on_traceable_before_mixing"]
        defn = rates["per_definition_including_not_picked_up"]

        self.assertEqual(cond["n"], 10)
        self.assertEqual(cond["k"], 10)
        self.assertAlmostEqual(cond["rate"], 1.0)

        self.assertEqual(defn["n"], 15)
        self.assertEqual(defn["k"], 10)
        self.assertAlmostEqual(defn["rate"], 10.0 / 15.0)
        self.assertAlmostEqual(defn["rate"], 0.6666666666666666, places=12)

        # 率そのものが下がった以上、幅(特に下限)も下がっているはず。
        self.assertLess(defn["rate"], cond["rate"])
        self.assertLess(defn["ci_two_sided_95"][0], cond["ci_two_sided_95"][0])
        self.assertLess(defn["ci_one_sided_lower_95"][0], cond["ci_one_sided_lower_95"][0])
        # 上限も、k=n でなくなった定義どおり側は 1.0 未満になる(条件付きは
        # k=n=10 なので両側上限は 1.0 のまま)。
        self.assertEqual(cond["ci_two_sided_95"][1], 1.0)
        self.assertLess(defn["ci_two_sided_95"][1], 1.0)

    def test_broken_implementation_without_the_addition_is_caught(self):
        """元の誤実装(``defn_n = cond_n``、① を足さない)を自分で当てて、
        上の核心の試験が実際に赤くなることを確かめる(このテストは「壊れて
        いたら落ちるはずの入力」を使って、壊れていない本物の関数が正しく
        振る舞うことをもう一度確認する形で残す ― 広い意味でのピン止め)。"""

        def broken_build_detection_rates(detected_total, drawn_total, not_picked_up_n):
            cond_n, cond_k = drawn_total, detected_total
            defn_n, defn_k = cond_n, detected_total  # MUTATION: ① を足さない
            return collections.OrderedDict([
                ("conditional_on_traceable_before_mixing", D._rate_block(cond_k, cond_n)),
                ("per_definition_including_not_picked_up", D._rate_block(defn_k, defn_n)),
            ])

        broken = broken_build_detection_rates(detected_total=10, drawn_total=10, not_picked_up_n=5)
        # 壊れた実装では両方 n=10 のまま(①が反映されない)。
        self.assertEqual(broken["per_definition_including_not_picked_up"]["n"], 10)
        # 本物の関数はそうならないことを、ここで対比して示す。
        real = D.build_detection_rates(detected_total=10, drawn_total=10, not_picked_up_n=5)
        self.assertNotEqual(
            real["per_definition_including_not_picked_up"]["n"],
            broken["per_definition_including_not_picked_up"]["n"],
        )
        self.assertEqual(real["per_definition_including_not_picked_up"]["n"], 15)


class AggregateInjectionsTest(unittest.TestCase):
    """人間の指示(2026-10-08、3 回目の REVISE)1・3: ``aggregate_injections``
    は ``main()`` の外のモジュールレベルの純粋関数で、``if detected: ...
    else: ...`` の分岐はこの関数の中にある。③: ``detected=False`` を含む
    合成入力で、未検出が検出率を正しく下げることを固定する。

    わざと 100% にならない値を使う(10 件のうち 3 件が ``detected=False``)。
    族ごとの ``not_stopped`` も見る(実物では 3 書類とも 0 で未検証だった)。"""

    def _row(self, unit_family, detected):
        return {"unit_family": unit_family, "detected": detected}

    def test_mixed_detected_lowers_the_rate_and_splits_not_stopped_by_family(self):
        """核心: 混入 10 件、うち detected=False が 3 件 ->
        detected_total=7・not_stopped_total=3・条件付き = 7/10 = 70%。
        族は 2 つ(money 6 件・ratio 4 件)に分け、not_stopped が族ごとに
        正しく割れることも見る(money に 2 件、ratio に 1 件)。"""

        rows = (
            [self._row("money", True)] * 4
            + [self._row("money", False)] * 2
            + [self._row("ratio", True)] * 3
            + [self._row("ratio", False)] * 1
        )
        self.assertEqual(len(rows), 10)
        detected_total, not_stopped_total, family_tally = D.aggregate_injections(rows)

        self.assertEqual(detected_total, 7)
        self.assertEqual(not_stopped_total, 3)
        self.assertAlmostEqual(detected_total / len(rows), 0.7)

        self.assertEqual(family_tally["money"]["n"], 6)
        self.assertEqual(family_tally["money"]["detected"], 4)
        self.assertEqual(family_tally["money"]["not_stopped"], 2)
        self.assertAlmostEqual(family_tally["money"]["detection_rate"], 4 / 6)

        self.assertEqual(family_tally["ratio"]["n"], 4)
        self.assertEqual(family_tally["ratio"]["detected"], 3)
        self.assertEqual(family_tally["ratio"]["not_stopped"], 1)
        self.assertAlmostEqual(family_tally["ratio"]["detection_rate"], 3 / 4)

    def test_error_row_with_detected_none_counts_toward_family_n_only(self):
        """混入そのものが失敗した行(``detected=None``)は、族の ``n`` だけ
        増え、``detected``/``not_stopped`` のどちらにも数えない(元の
        ``main()`` の挙動のまま)。"""

        rows = [self._row("money", True), self._row("money", None), self._row("money", False)]
        detected_total, not_stopped_total, family_tally = D.aggregate_injections(rows)
        self.assertEqual(detected_total, 1)
        self.assertEqual(not_stopped_total, 1)
        self.assertEqual(family_tally["money"]["n"], 3)
        self.assertEqual(family_tally["money"]["detected"], 1)
        self.assertEqual(family_tally["money"]["not_stopped"], 1)

    def test_broken_implementation_that_ignores_detected_is_caught(self):
        """元の誤実装(``detected`` を無視して常に検出に数える)を当てたら、
        上の核心の試験(7/10)が崩れることを対比で示す。"""

        def broken_aggregate(rows):
            detected_total = len(rows)  # MUTATION: detected を見ない
            not_stopped_total = 0
            return detected_total, not_stopped_total, {}

        rows = (
            [self._row("money", True)] * 4
            + [self._row("money", False)] * 2
            + [self._row("ratio", True)] * 3
            + [self._row("ratio", False)] * 1
        )
        broken_detected, broken_not_stopped, _ = broken_aggregate(rows)
        self.assertEqual(broken_detected, 10)  # 壊れた実装は 10/10 になる
        real_detected, real_not_stopped, _ = D.aggregate_injections(rows)
        self.assertEqual(real_detected, 7)
        self.assertNotEqual(real_detected, broken_detected)


if __name__ == "__main__":
    unittest.main()
