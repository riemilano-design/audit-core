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
