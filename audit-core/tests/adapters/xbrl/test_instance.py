# -*- coding: utf-8 -*-
import unittest

from . import _material as M
from adapters.xbrl import instance as I


class StripHtmlTest(unittest.TestCase):
    # Stripper emits its tag marker on handle_starttag, i.e. *before* the
    # tag's text, and collapses runs of spaces/tabs (not newlines).
    def test_strips_tags_and_keeps_text(self):
        self.assertEqual(I.strip_html("<p>a</p><p>b</p>"), "\na\nb")

    def test_td_becomes_space_not_newline(self):
        self.assertEqual(I.strip_html("<td>a</td><td>b</td>"), " a b")

    def test_unescapes_entities(self):
        self.assertEqual(I.strip_html("a&amp;b"), "")


class PlainContextAndCtxOkTest(unittest.TestCase):
    def test_plain_context_true_without_members(self):
        contexts = {"CurrentYearDuration": {"members": []}}
        self.assertTrue(I.plain_context("CurrentYearDuration", contexts))

    def test_plain_context_false_with_members(self):
        contexts = {"CurrentYearDuration_FooMember": {"members": ["x:FooMember"]}}
        self.assertFalse(I.plain_context("CurrentYearDuration_FooMember", contexts))

    def test_plain_context_false_for_non_consolidated(self):
        contexts = {"CurrentYearDuration_NonConsolidatedMember": {"members": []}}
        self.assertFalse(I.plain_context("CurrentYearDuration_NonConsolidatedMember", contexts))

    def test_ctx_ok_member_none_matches_plain(self):
        contexts = {"CurrentYearDuration": {"members": []}}
        self.assertTrue(I.ctx_ok("CurrentYearDuration", contexts, None))

    def test_ctx_ok_member_requires_exact_single_member(self):
        contexts = {
            "CurrentYearDuration_FooMember": {"members": ["x:FooMember"]},
            "CurrentYearDuration_FooBarMember": {"members": ["x:FooMember", "x:BarMember"]},
        }
        self.assertTrue(I.ctx_ok("CurrentYearDuration_FooMember", contexts, "x:FooMember"))
        self.assertFalse(I.ctx_ok("CurrentYearDuration_FooBarMember", contexts, "x:FooMember"))


class FactsForTest(unittest.TestCase):
    def test_exact_match_preferred_over_loose(self):
        contexts = {"CurrentYearDuration": {"members": []}}
        facts = [
            {"name": "jppfs_cor:NetSalesExtra", "context": "CurrentYearDuration", "unit": "JPY", "value": 1.0},
            {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration", "unit": "JPY", "value": 2.0},
        ]
        got = I.facts_for(["NetSales"], facts, contexts)
        self.assertEqual([f["name"] for f in got], ["jppfs_cor:NetSales"])

    def test_summary_of_business_results_suffix(self):
        contexts = {"CurrentYearDuration": {"members": []}}
        facts = [{"name": "jpcrp_cor:NetSalesSummaryOfBusinessResults", "context": "CurrentYearDuration", "unit": "JPY", "value": 3.0}]
        got = I.facts_for(["NetSales"], facts, contexts)
        self.assertEqual(len(got), 1)

    def test_member_filters_context(self):
        contexts = {
            "CurrentYearDuration_FooMember": {"members": ["x:FooMember"]},
            "CurrentYearDuration": {"members": []},
        }
        facts = [
            {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration_FooMember", "unit": "JPY", "value": 1.0},
            {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration", "unit": "JPY", "value": 2.0},
        ]
        got = I.facts_for(["NetSales"], facts, contexts, member="x:FooMember")
        self.assertEqual([f["value"] for f in got], [1.0])

    def test_no_match_returns_empty(self):
        contexts = {"CurrentYearDuration": {"members": []}}
        facts = [{"name": "jppfs_cor:Assets", "context": "CurrentYearDuration", "unit": "JPY", "value": 1.0}]
        self.assertEqual(I.facts_for(["NetSales"], facts, contexts), [])


class SegmentMemberDenominatorTest(unittest.TestCase):
    """Core 接続 C-1g §1-4(人間の承認、2026-10-06): 事業 member だけを数える
    分母。凍結の ``member_denominator``(全部数える)との対照で、標準の
    名前空間の member(株主資本等変動計算書の member・役員区分など)を除く。
    """

    def test_standard_namespace_members_are_excluded(self):
        contexts = {
            "CurrentYearDuration_CapitalStockMember": {
                "start": "2025-04-01", "end": "2026-03-31",
                "members": ["jppfs_cor:CapitalStockMember"],
            },
        }
        self.assertEqual(I.segment_member_denominator(contexts), [])
        # The frozen member_denominator still counts it (contrast).
        self.assertEqual(I.member_denominator(contexts), ["jppfs_cor:CapitalStockMember"])

    def test_company_extension_members_are_included(self):
        contexts = {
            "CurrentYearDuration_FooSegmentMember": {
                "start": "2025-04-01", "end": "2026-03-31",
                "members": ["jpcrp030000-asr_E05055-000:FooReportableSegmentMember"],
            },
        }
        self.assertEqual(
            I.segment_member_denominator(contexts),
            ["jpcrp030000-asr_E05055-000:FooReportableSegmentMember"],
        )

    def test_mixed_standard_and_extension_members(self):
        contexts = {
            "CurrentYearDuration_CapitalStockMember": {
                "start": "2025-04-01", "end": "2026-03-31",
                "members": ["jppfs_cor:CapitalStockMember"],
            },
            "CurrentYearDuration_FooSegmentMember": {
                "start": "2025-04-01", "end": "2026-03-31",
                "members": ["jpcrp030000-asr_E05055-000:FooReportableSegmentMember"],
            },
            "Prior1YearDuration_BarSegmentMember": {
                "start": "2024-04-01", "end": "2025-03-31",
                "members": ["jpcrp030000-asr_E05055-000:BarReportableSegmentMember"],
            },
        }
        self.assertEqual(
            I.segment_member_denominator(contexts),
            [
                "jpcrp030000-asr_E05055-000:BarReportableSegmentMember",
                "jpcrp030000-asr_E05055-000:FooReportableSegmentMember",
            ],
        )
        self.assertEqual(len(I.member_denominator(contexts)), 3)

    def test_non_consolidated_and_instant_only_contexts_excluded(self):
        contexts = {
            "CurrentYearDuration_NonConsolidatedMember_FooSegmentMember": {
                "start": "2025-04-01", "end": "2026-03-31",
                "members": ["jpcrp030000-asr_E05055-000:FooReportableSegmentMember"],
            },
            "CurrentYearInstant_FooSegmentMember": {
                "instant": "2026-03-31",
                "members": ["jpcrp030000-asr_E05055-000:FooReportableSegmentMember"],
            },
        }
        self.assertEqual(I.segment_member_denominator(contexts), [])

    def test_no_members_is_empty(self):
        self.assertEqual(I.segment_member_denominator({}), [])


class SelectMdnaTest(unittest.TestCase):
    def test_prefers_management_analysis_text_block(self):
        tbs = {
            "jpcrp_cor:OverviewOfBusinessResultsTextBlock": "x",
            "jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock": "y",
        }
        self.assertEqual(I.select_mdna(tbs), "jpcrp_cor:ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock")

    def test_falls_back_to_overview(self):
        tbs = {"jpcrp_cor:OverviewOfBusinessResultsTextBlock": "x"}
        self.assertEqual(I.select_mdna(tbs), "jpcrp_cor:OverviewOfBusinessResultsTextBlock")

    def test_none_when_nothing_matches(self):
        self.assertIsNone(I.select_mdna({"jpcrp_cor:SomeOtherTextBlock": "x"}))


class LoadInstanceOnRealMaterialTest(unittest.TestCase):
    def test_loads_both_documents(self):
        for doc in (M.DOC_1, M.DOC_5):
            zb = M.load_zip_bytes(doc["docID"], doc["sha256"])
            inst = I.load_instance(zb)
            self.assertGreater(len(inst["facts"]), 0)
            self.assertGreater(len(inst["contexts"]), 0)
            self.assertIsNotNone(I.select_mdna(inst["textblocks"]))


if __name__ == "__main__":
    unittest.main()


class InlineLabelsTest(unittest.TestCase):
    """XBRL 直し §7(2026-10-08): 書類自身のインライン XBRL から
    「日本語の勘定科目名 → 要素の局所名」を取る。
    """

    ROW = ('<tr><td><p>%s</p></td>'
           '<td><p>%s</p></td>'
           '<td><p><ix:nonFraction contextRef="CurrentYearInstant" name="%s">1,234</ix:nonFraction></p></td>'
           '</tr>')

    class _Zip(object):
        """``zipfile.ZipFile`` の代わり(``read(name)`` だけ使う)。"""

        def __init__(self, files):
            self._files = files

        def read(self, name):
            return self._files[name].encode("utf-8")

    def _labels(self, rows, name="x_ixbrl.htm"):
        html = "<html><body><table>" + "".join(rows) + "</table></body></html>"
        return I.inline_labels(self._Zip({name: html}), [name])

    def test_label_and_element_are_paired_from_the_same_row(self):
        got = self._labels([self.ROW % ("&#160;", "資産合計", "jppfs_cor:Assets")])
        self.assertEqual(got, {"資産合計": ["Assets"]})

    def test_numeric_entity_for_an_empty_cell_is_decoded_not_taken_as_a_name(self):
        # 最初の実装は ``&#160;`` を実体参照のまま 6 文字の名前として拾い、
        # 1 社目の取れた名前を 226 → 105 に落としていた。
        # 2 社目・3 社目は本物の nbsp 文字なので落ちず、**1 書類だけで測って
        # いたら気づかない型の誤り**だった。字面で留める。
        got = self._labels([self.ROW % ("&#160;", "売上原価", "jppfs_cor:CostOfSales")])
        self.assertNotIn("&#160;", got)
        self.assertEqual(got, {"売上原価": ["CostOfSales"]})

    def test_real_nbsp_character_is_also_skipped(self):
        got = self._labels([self.ROW % (" ", "売上原価", "jppfs_cor:CostOfSales")])
        self.assertEqual(got, {"売上原価": ["CostOfSales"]})

    def test_numeric_only_cell_is_not_a_name(self):
        got = self._labels([self.ROW % ("1,234", "△5.8", "jppfs_cor:Assets")])
        self.assertEqual(got, {})

    def test_rows_without_a_fact_are_ignored(self):
        html = "<table><tr><td><p>資産合計</p></td></tr></table>"
        self.assertEqual(I.inline_labels(self._Zip({"a_ixbrl.htm": html}), ["a_ixbrl.htm"]), {})

    def test_two_elements_in_one_row_both_attach_to_the_name(self):
        row = ('<tr><td><p>&#160;</p></td><td><p>売上高</p></td>'
               '<td><p><ix:nonFraction name="jppfs_cor:NetSales">1</ix:nonFraction></p></td>'
               '<td><p><ix:nonFraction name="jpcrp_cor:NetSalesSummaryOfBusinessResults">1</ix:nonFraction></p></td>'
               '</tr>')
        self.assertEqual(self._labels([row]), {"売上高": ["NetSales", "NetSalesSummaryOfBusinessResults"]})

    def test_short_names_are_dropped_at_the_written_threshold(self):
        self.assertEqual(I.LABEL_MIN_LEN, 3)
        self.assertEqual(self._labels([self.ROW % ("&#160;", "資産", "jppfs_cor:Assets")]), {})
        self.assertEqual(self._labels([self.ROW % ("&#160;", "資産合計", "jppfs_cor:Assets")]),
                         {"資産合計": ["Assets"]})

    def test_denied_names_are_dropped(self):
        for word in ("その他", "合計", "前連結会計年度"):
            self.assertIn(word, I.LABEL_DENY)
            self.assertEqual(self._labels([self.ROW % ("&#160;", word, "jppfs_cor:OtherCA")]), {}, word)

    def test_cover_page_items_in_brackets_are_dropped(self):
        got = self._labels([self.ROW % ("&#160;", "【電話番号】", "jpcrp_cor:TelephoneNumberCoverPage")])
        self.assertEqual(got, {})

    def test_only_ixbrl_files_are_read(self):
        html = "<table>" + (self.ROW % ("&#160;", "資産合計", "jppfs_cor:Assets")) + "</table>"
        self.assertEqual(I.inline_labels(self._Zip({"a.htm": html}), ["a.htm"]), {})
