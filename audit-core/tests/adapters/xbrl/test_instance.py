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


class RowElementsStatementOnlyTest(unittest.TestCase):
    """XBRL 直し §7a(人間の判断、2026-10-08): 計算書の行から来たラベルだけ使う。

    採る条件は 2 つ ― 行の ix の context に member が 1 つも付いていないこと、
    かつ要素が財務諸表タクソノミ(``jppfs_cor``)のものであること。
    """

    def _row(self, pairs):
        cells = "".join(
            '<td><p><ix:nonFraction contextRef="%s" name="%s">1</ix:nonFraction></p></td>' % (c, n)
            for n, c in pairs)
        return "<tr><td><p>甲勘定</p></td>" + cells + "</tr>"

    CTX = {"CurrentYearInstant": {"members": []},
           "CurrentYearInstant_SegMember": {"members": ["SegMember"]}}

    def test_without_the_flag_every_element_in_the_row_is_taken(self):
        row = self._row([("jppfs_cor:Assets", "CurrentYearInstant"),
                         ("jpcrp_cor:NetSalesSummaryOfBusinessResults", "CurrentYearInstant")])
        self.assertEqual(I._row_elements(row, False, self.CTX),
                         ["jppfs_cor:Assets", "jpcrp_cor:NetSalesSummaryOfBusinessResults"])

    def test_a_member_on_any_fact_in_the_row_drops_the_whole_row(self):
        row = self._row([("jppfs_cor:NetSales", "CurrentYearInstant_SegMember")])
        self.assertEqual(I._row_elements(row, True, self.CTX), [])

    def test_a_member_on_one_of_two_facts_still_drops_the_whole_row(self):
        row = self._row([("jppfs_cor:NetSales", "CurrentYearInstant"),
                         ("jppfs_cor:NetSales", "CurrentYearInstant_SegMember")])
        self.assertEqual(I._row_elements(row, True, self.CTX), [])

    def test_only_the_statement_taxonomy_elements_are_taken(self):
        row = self._row([("jppfs_cor:Assets", "CurrentYearInstant"),
                         ("jpcrp_cor:AuditFeesConsolidatedSubsidiaries", "CurrentYearInstant")])
        self.assertEqual(I.STATEMENT_PREFIX, "jppfs_cor")
        self.assertEqual(I._row_elements(row, True, self.CTX), ["jppfs_cor:Assets"])

    def test_a_row_with_no_statement_element_becomes_empty(self):
        row = self._row([("jpcrp_cor:AuditFeesConsolidatedSubsidiaries", "CurrentYearInstant")])
        self.assertEqual(I._row_elements(row, True, self.CTX), [])

    def test_an_unknown_context_is_treated_as_having_no_member(self):
        row = self._row([("jppfs_cor:Assets", "NoSuchContext")])
        self.assertEqual(I._row_elements(row, True, self.CTX), ["jppfs_cor:Assets"])

    def test_inline_labels_refuses_the_flag_without_contexts(self):
        with self.assertRaises(ValueError):
            I.inline_labels(None, [], statement_only=True)


class ParseLabelLinkbaseTest(unittest.TestCase):
    """XBRL 直し §8: 標準タクソノミのラベル linkbase を読む。

    ``loc`` -> ``labelArc`` -> ``label`` の 3 つを辿る(``label_XXX`` という
    名前から要素名を推測しない)。
    """

    HEAD = ('<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
            'xmlns:xlink="http://www.w3.org/1999/xlink">')

    def _xml(self, locs, labels, arcs):
        parts = [self.HEAD]
        for label, href in locs:
            parts.append('<link:loc xlink:href="%s" xlink:label="%s"/>' % (href, label))
        for label, role, lang, text in labels:
            parts.append('<link:label xlink:label="%s" xlink:role="%s" xml:lang="%s">%s</link:label>'
                         % (label, role, lang, text))
        for a, b in arcs:
            parts.append('<link:labelArc xlink:from="%s" xlink:to="%s"/>' % (a, b))
        parts.append("</link:linkbase>")
        return "".join(parts).encode("utf-8")

    STD = "http://www.xbrl.org/2003/role/label"
    TOTAL = "http://www.xbrl.org/2003/role/totalLabel"

    def test_the_arc_decides_the_pair_not_the_name(self):
        # ``label_B`` の字面は ``CurrentAssets`` を連想させるが、arc は
        # ``NoncurrentAssets`` に繋がっている。**arc に従う。**
        xml = self._xml([("A", "../x.xsd#jppfs_cor_NoncurrentAssets")],
                        [("label_CurrentAssets", self.STD, "ja", "固定資産")],
                        [("A", "label_CurrentAssets")])
        self.assertEqual(I.parse_label_linkbase(xml), {"jppfs_cor_NoncurrentAssets": "固定資産"})

    def test_only_the_standard_label_role_is_taken(self):
        xml = self._xml([("A", "../x.xsd#jppfs_cor_CurrentAssets")],
                        [("l1", self.STD, "ja", "流動資産"), ("l2", self.TOTAL, "ja", "流動資産合計")],
                        [("A", "l1"), ("A", "l2")])
        self.assertEqual(I.STANDARD_LABEL_ROLE, self.STD)
        self.assertEqual(I.parse_label_linkbase(xml), {"jppfs_cor_CurrentAssets": "流動資産"})

    def test_the_total_label_can_be_asked_for_explicitly(self):
        xml = self._xml([("A", "../x.xsd#jppfs_cor_CurrentAssets")],
                        [("l1", self.STD, "ja", "流動資産"), ("l2", self.TOTAL, "ja", "流動資産合計")],
                        [("A", "l1"), ("A", "l2")])
        self.assertEqual(I.parse_label_linkbase(xml, role=self.TOTAL),
                         {"jppfs_cor_CurrentAssets": "流動資産合計"})

    def test_english_labels_are_not_taken(self):
        xml = self._xml([("A", "../x.xsd#jppfs_cor_CurrentAssets")],
                        [("l1", self.STD, "en", "Current assets")], [("A", "l1")])
        self.assertEqual(I.parse_label_linkbase(xml), {})

    def test_the_text_is_nfkc_normalized(self):
        xml = self._xml([("A", "../x.xsd#jppfs_cor_X")],
                        [("l1", self.STD, "ja", " １株当たり純資産 ")], [("A", "l1")])
        self.assertEqual(I.parse_label_linkbase(xml), {"jppfs_cor_X": "1株当たり純資産"})

    def test_a_label_without_an_arc_is_not_taken(self):
        xml = self._xml([("A", "../x.xsd#jppfs_cor_X")], [("l1", self.STD, "ja", "甲")], [])
        self.assertEqual(I.parse_label_linkbase(xml), {})


class TaxonomyLabelFilesTest(unittest.TestCase):
    """XBRL 直し §8: ラベルの本体は**リポジトリの外**。読む前に sha256 を照合する。"""

    def test_a_missing_file_raises_instead_of_returning_nothing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                I._read_taxonomy_file(d, "nope.xml", "0" * 64)

    def test_a_wrong_sha256_raises(self):
        import hashlib
        import os as _os
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = _os.path.join(d, "a.xml")
            open(path, "wb").write(b"hello")
            with self.assertRaises(ValueError):
                I._read_taxonomy_file(d, "a.xml", "0" * 64)
            good = hashlib.sha256(b"hello").hexdigest()
            data, actual = I._read_taxonomy_file(d, "a.xml", good)
            self.assertEqual((data, actual), (b"hello", good))

    def test_the_recorded_sha256_file_matches_the_literals_in_the_code(self):
        """``fixtures/xbrl/taxonomy_labels_sha256.txt``(人に見せる記録)と
        コードの字面が食い違わないように、**両方**を読んで突き合わせる。
        """

        import os as _os
        here = _os.path.dirname(_os.path.abspath(__file__))
        # tests/adapters/xbrl -> audit-core(変異の砂場でも同じ形に写される)
        root = _os.path.dirname(_os.path.dirname(_os.path.dirname(here)))
        path = _os.path.join(root, "fixtures", "xbrl", "taxonomy_labels_sha256.txt")
        recorded = {}
        for line in open(path, encoding="utf-8"):
            sha, name = line.split()
            recorded[name] = sha
        self.assertEqual(recorded, {name: sha for _ns, name, sha in I.TAXONOMY_LABEL_FILES})

    def test_the_version_matches_what_the_documents_reference(self):
        """人間の指示「書類が参照する版と一致させる」を機械で留める。"""

        import io as _io
        import re as _re
        import zipfile as _zipfile
        from adapters.xbrl import edinet as _E
        self.assertEqual(I.TAXONOMY_VERSION, "2025-11-01")
        for doc in ("S100Z4Q1", "S100Z4B6", "S100YMFV"):
            z = _zipfile.ZipFile(_io.BytesIO(open(_E.cache_path(doc), "rb").read()))
            refs = set()
            for n in z.namelist():
                if n.endswith(".xsd"):
                    text = z.read(n).decode("utf-8", "replace")
                    refs |= set(_re.findall(r'xlink:href="(http[^"]*/(?:jppfs|jpcrp)/[^"]*_lab\.xml)"', text))
            self.assertTrue(refs, doc)
            for _ns, name, _sha in I.TAXONOMY_LABEL_FILES:
                self.assertTrue(any(r.endswith("/" + name) for r in refs), (doc, name, sorted(refs)))


class TaxonomyLabelsTest(unittest.TestCase):
    """XBRL 直し §8: 語にするのは「この書類に fact が在る要素」だけ。"""

    MAP = {"CurrentAssets": "流動資産", "Assets": "資産", "OtherCA": "その他",
           "NetSales": "売上高", "Unused": "受注高"}

    def _labels(self, fact_locals):
        orig = I.taxonomy_label_map
        I.taxonomy_label_map = lambda namespaces=("jppfs",), directory=None: dict(self.MAP)
        try:
            return I.taxonomy_labels(fact_locals)
        finally:
            I.taxonomy_label_map = orig

    def test_only_elements_with_a_fact_become_words(self):
        got = self._labels({"CurrentAssets", "NetSales"})
        self.assertEqual(got, {"流動資産": ["CurrentAssets"], "売上高": ["NetSales"]})
        self.assertNotIn("受注高", got)

    def test_short_and_denied_words_are_dropped_the_same_way_as_the_document_labels(self):
        got = self._labels({"Assets", "OtherCA"})
        self.assertEqual(got, {})

    def test_two_elements_with_the_same_label_are_kept_in_a_decided_order(self):
        orig = I.taxonomy_label_map
        I.taxonomy_label_map = lambda namespaces=("jppfs",), directory=None: {
            "BAmortization": "のれん償却額", "AAmortization": "のれん償却額"}
        try:
            got = I.taxonomy_labels({"AAmortization", "BAmortization"})
        finally:
            I.taxonomy_label_map = orig
        self.assertEqual(got, {"のれん償却額": ["AAmortization", "BAmortization"]})

    def test_the_namespace_filter_keeps_jpcrp_out(self):
        """``jppfs`` に限る規則を**仕組みとして**留める。

        3 書類では `P13` と `P14`(限定なし)が 1 行も違わなかった ―
        **実物では差が出ない**ので、ここで字面と仕組みを留めておかないと
        この分岐は黙って壊れる。
        """

        only = I.taxonomy_label_map(("jppfs",))
        both = I.taxonomy_label_map(None)
        self.assertIn("CurrentAssets", only)
        self.assertNotIn("AuditFeesConsolidatedSubsidiaries", only)
        self.assertIn("AuditFeesConsolidatedSubsidiaries", both)
        self.assertGreater(len(both), len(only))

    def test_the_real_files_give_the_two_words_the_document_labels_could_not(self):
        """§1.4 の肝 ― 計算書の**見出しの行**は書類のラベルでは引けないが、
        標準タクソノミの**標準ラベル**なら引ける。
        """

        from adapters.xbrl import edinet as _E
        inst = I.load_instance(open(_E.cache_path("S100YMFV"), "rb").read())
        locals_ = {f["name"].split(":")[-1] for f in inst["facts"]}
        got = I.taxonomy_labels(locals_)
        self.assertEqual(got.get("流動資産"), ["CurrentAssets"])
        self.assertEqual(got.get("固定資産"), ["NoncurrentAssets"])
        self.assertEqual(got.get("長期借入金の返済による支出"), ["RepaymentOfLongTermLoansPayableFinCF"])
