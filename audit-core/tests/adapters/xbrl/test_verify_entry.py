# -*- coding: utf-8 -*-
"""入口(``adapters/xbrl/verify_document.py``)の試験。

人間の決定(2026-10-13)の完成条件を、3 つに**分けて**留める:

1. **判定の一致**: Claim id ごとの ``(state, pointers, reason, subject)`` が、
   既存の測定と同じ。期待値は 2 つの独立な出どころから取る ―
   (a) ``fixtures/xbrl/entry_golden_ai_prose_2026-10-13.json``(開発書類の AI 文、
   P7・P13・P16。``tests/golden/_instrument`` で作った。入口の出力からは作っていない)、
   (b) ``fixtures/xbrl/holdout_p16/commander_only/dump_P16_<doc>.json``(未使用 2 書類。
   限定確認のときに作り、commit 済み。行の鍵 -> claim id の対応表を経由する)。
2. **入力の一致**: 文章を差し替えた ZIP の sha256 が封じた値と同じ。
3. **出力の安定**: 同じ入力を 2 回処理して JSON の byte が同じ。1 書類は sha256 を字で留める。

さらに、人間が承認した**書類レベルの旗**を、真になる 2 書類・偽になる書類・
Claim 0 件の合成の入力で留める。

材料が無い環境では skip する(``_material`` と同じ姿勢)。通信しない。
"""

import hashlib
import io
import json
import os
import tempfile
import unittest

from adapters.xbrl import prose as PR
from adapters.xbrl import verify_document as VD
from adapters.xbrl import vocabulary as V

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
_FIX = os.path.join(_ROOT, "fixtures", "xbrl")
_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
_GOLDEN = os.path.join(_FIX, "entry_golden_ai_prose_2026-10-13.json")
_HOLDOUT = os.path.join(_FIX, "holdout_p16")
_PROSE = os.path.join(_FIX, "ai_prose_2026-10-09.txt")

DEV_DOC = "S100Z4Q1"
HOLDOUT_DOCS = ("S100Z39P", "S100Z4N9")
# 結果文書 docs/HOLDOUT_P16_RESULT_2026-10-13.md §2 の数(字で留める)
HOLDOUT_EXPECTED = {"S100Z39P": {"claims": 103, "grounded": 80},
                    "S100Z4N9": {"claims": 186, "grounded": 99}}
# docs/CONCEPT_BINDING_P16_2026-10-13.md §2-3 の表(P16 の列。止めた件数/全件)
ROBUSTNESS_P16 = {
    "S100YMFV": (48, 133), "S100Z1WR": (35, 91), "S100Z35K": (109, 133),
    "S100Z37J": (48, 129), "S100Z3BW": (51, 145), "S100Z3CO": (61, 143),
    "S100Z3HP": (62, 62), "S100Z3JY": (51, 135), "S100Z3V1": (59, 109),
    "S100Z433": (87, 87), "S100Z4B6": (58, 123), "S100Z4DE": (42, 117),
    "S100Z4PA": (61, 125), "S100Z4Q1": (11, 88),
}
# 書類レベルの旗が真になる書類(3 profile とも GROUNDED 0 件・PNF が大半)
DOC_UNVERIFIABLE_DOCS = ("S100Z3HP", "S100Z433")
# 出力の byte を字で留める値(engine の指紋を除いた本体の sha256)。
# 下の test_one_documents_output_sha256_is_pinned_literally が使う。
_PINNED_BODY_SHA256_S100Z4B6 = "dbc1da2a504f346766297800b1056509fdf3a9b4c0809260bd6b85d5b92dfbd5"


def _zip(doc):
    return os.path.join(_CACHE, "%s.zip" % doc)


def _have(doc):
    return os.path.exists(_zip(doc))


def _read(doc):
    with open(_zip(doc), "rb") as fh:
        return fh.read()


class ProseReplacementTest(unittest.TestCase):
    """2. 入力の一致 ― 差し替えは日付つき道具と同じ(封じた sha256)。"""

    @unittest.skipUnless(_have(DEV_DOC) and os.path.exists(_PROSE), "材料が無い")
    def test_modified_zip_matches_the_sealed_sha256(self):
        text = io.open(_PROSE, encoding="utf-8").read()
        zb2, element, member = PR.build_modified_zip(_read(DEV_DOC), text)
        self.assertEqual(hashlib.sha256(zb2).hexdigest(), PR.AI_PROSE_ZIP_SHA256)
        self.assertTrue(element.endswith("ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"))
        self.assertTrue(member.endswith(".xbrl"))

    def test_one_line_is_one_paragraph_and_text_is_not_changed(self):
        html = PR.prose_to_html(u"売上高は 100 百万円。\n\n営業利益は 10 百万円。")
        self.assertEqual(html, u"<p>売上高は 100 百万円。</p>\n<p>営業利益は 10 百万円。</p>")

    def test_special_characters_are_escaped(self):
        self.assertEqual(PR.prose_to_html(u"a<b&c"), u"<p>a&lt;b&amp;c</p>")

    def test_a_zip_without_the_section_raises_instead_of_exiting(self):
        import io as _io
        import zipfile
        buf = _io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("XBRL/PublicDoc/x.xbrl", "<xbrl></xbrl>")
        with self.assertRaises(PR.ProseReplacementError):
            PR.build_modified_zip(buf.getvalue(), u"文")


class DocumentLevelRuleTest(unittest.TestCase):
    """人間が承認した書類レベルの旗。**規則の字そのもの**を留める。"""

    def test_the_rule_text_is_pinned(self):
        r = VD.DOC_UNVERIFIABLE_RULE
        self.assertIn(u"Claim 件数が 0 件の場合、書類レベルを UNVERIFIABLE とする。", r)
        self.assertIn(u"GROUNDED 件数が 0 件", r)
        self.assertIn(u"POINTER_NOT_FOUND 件数 ÷ 全 Claim 件数が 0.5 を超える", r)
        self.assertIn(u"Claim 個別の state は変更しない。", r)
        self.assertEqual(VD.DOC_UNVERIFIABLE_PNF_THRESHOLD, 0.5)

    def test_zero_claims_is_unverifiable(self):
        self.assertEqual(VD.document_level({}, 0)[0], True)

    def test_grounded_zero_and_pnf_over_half(self):
        self.assertEqual(VD.document_level({"POINTER_NOT_FOUND": 6, "UNVERIFIABLE": 4}, 10)[0], True)

    def test_exactly_half_is_not_unverifiable(self):
        # 「0.5 を超える」= 等号では立たない
        self.assertEqual(VD.document_level({"POINTER_NOT_FOUND": 5, "UNVERIFIABLE": 5}, 10)[0], False)

    def test_one_grounded_keeps_the_document_verifiable(self):
        self.assertEqual(VD.document_level({"GROUNDED": 1, "POINTER_NOT_FOUND": 99}, 100)[0], False)

    def test_many_stops_without_pnf_is_not_unverifiable(self):
        self.assertEqual(VD.document_level({"VALUE_MISMATCH": 9, "POINTER_NOT_FOUND": 1}, 10)[0], False)

    @unittest.skipUnless(all(_have(d) for d in DOC_UNVERIFIABLE_DOCS), "材料が無い")
    def test_the_two_structurally_failing_documents_are_flagged(self):
        for doc in DOC_UNVERIFIABLE_DOCS:
            out = VD.verify_document(_read(doc))
            self.assertTrue(out["document"]["unverifiable"], doc)
            self.assertEqual(out["document"]["states"].get("GROUNDED", 0), 0, doc)
            self.assertEqual(out["document"]["rule"], VD.DOC_UNVERIFIABLE_RULE)
            # Claim 個別の state は旗で変わらない
            self.assertEqual(sum(out["document"]["states"].values()), out["document"]["claims"])

    @unittest.skipUnless(all(_have(d) for d in HOLDOUT_DOCS), "材料が無い")
    def test_the_holdout_documents_are_not_flagged(self):
        for doc in HOLDOUT_DOCS:
            out = VD.verify_document(_read(doc))
            self.assertFalse(out["document"]["unverifiable"], doc)
            self.assertIsNone(out["document"]["unverifiable_why"], doc)


class OutputStabilityTest(unittest.TestCase):
    """3. 出力の安定 ― 同じ入力なら byte が同じ。"""

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_the_same_input_gives_the_same_bytes(self):
        zb = _read("S100Z4B6")
        a = VD.dumps(VD.verify_document(zb))
        b = VD.dumps(VD.verify_document(zb))
        self.assertEqual(hashlib.sha256(a.encode("utf-8")).hexdigest(),
                         hashlib.sha256(b.encode("utf-8")).hexdigest())

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_one_documents_output_sha256_is_pinned_literally(self):
        """**形式を変えたら赤くなる。** 2 回比べるだけでは、字下げや並びを
        変えても両方同じになるので黙る(人間の決定の「出力の安定」の 2 つ目)。
        engine の指紋は adapters/xbrl の .py が変わるたびに動くので除いて留める
        (指紋自体は別の試験で見ている)。"""

        out = VD.verify_document(_read("S100Z4B6"))
        del out["engine"]
        body = VD.dumps(out)
        self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(),
                         "%s" % _PINNED_BODY_SHA256_S100Z4B6)

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_the_claim_rows_have_exactly_the_pinned_fields_in_order(self):
        out = VD.verify_document(_read("S100Z4B6"))
        self.assertTrue(out["claims"])
        for row in out["claims"]:
            self.assertEqual(tuple(row.keys()), VD.CLAIM_FIELDS)

    def test_the_fingerprint_does_not_depend_on_git(self):
        fp = VD.engine_fingerprint()
        for key in ("adapter_xbrl_py_sha256", "core_py_sha256"):
            self.assertEqual(len(fp[key]), 64, key)
        self.assertGreater(fp["adapter_xbrl_py_files"], 5)
        # git が無い環境では None(出力は壊れない)
        self.assertTrue(fp["git_commit"] is None or len(fp["git_commit"]) == 40)

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_cli_writes_the_same_bytes_as_the_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            rc = VD.main(["--doc", "S100Z4B6", "--out", path])
            self.assertEqual(rc, 0)
            with io.open(path, encoding="utf-8") as fh:
                on_disk = fh.read()
            self.assertEqual(on_disk, VD.dumps(VD.verify_document(_read("S100Z4B6"))))
            data = json.loads(on_disk)
            self.assertEqual(data["profile"], V.DEFAULT_PROFILE)
            self.assertEqual(data["profile"], "P20")


class SemanticMatchAgainstTheDevelopmentMeasurementTest(unittest.TestCase):
    """1(a). 判定の一致 ― 開発書類の AI 文、P7・P13・P16。"""

    @classmethod
    def setUpClass(cls):
        if not (_have(DEV_DOC) and os.path.exists(_GOLDEN) and os.path.exists(_PROSE)):
            raise unittest.SkipTest("材料が無い")
        with io.open(_GOLDEN, encoding="utf-8") as fh:
            cls.golden = json.load(fh)
        cls.text = io.open(_PROSE, encoding="utf-8").read()
        cls.zb = _read(DEV_DOC)

    def _compare(self, profile):
        out = VD.verify_document(self.zb, profile, self.text)
        want = self.golden["profiles"][profile]
        self.assertEqual(out["input"]["text_replaced"]["element"], self.golden["replaced_element"])
        self.assertEqual(len(out["claims"]), want["claims"])
        got = {c["id"]: c for c in out["claims"]}
        self.assertEqual(sorted(got), sorted(want["rows"]))
        for cid, w in want["rows"].items():
            g = got[cid]
            self.assertEqual(g["state"], w["state"], cid)
            self.assertEqual(g["pointers"], w["pointers"], cid)
            self.assertEqual(g["reason"], w["reason"], cid)
            self.assertEqual(g["subject"], w["subject"], cid)

    def test_p16_matches_the_golden(self):
        self._compare("P16")

    def test_p13_matches_the_golden(self):
        self._compare("P13")

    def test_p7_matches_the_golden(self):
        self._compare("P7")

    def test_p16_state_counts_are_the_recorded_ones(self):
        # docs/CONCEPT_BINDING_P16_2026-10-13.md §2: G 330 / VM 25 / PNF 16 / UV 41
        out = VD.verify_document(self.zb, "P16", self.text)
        self.assertEqual(out["document"]["states"],
                         {"GROUNDED": 330, "POINTER_NOT_FOUND": 16,
                          "UNVERIFIABLE": 41, "VALUE_MISMATCH": 25})


class SemanticMatchAgainstTheHoldoutMeasurementTest(unittest.TestCase):
    """1(b). 判定の一致 ― 未使用 2 書類(限定確認の dump。commit 済み)。"""

    @classmethod
    def setUpClass(cls):
        if not all(_have(d) for d in HOLDOUT_DOCS):
            raise unittest.SkipTest("材料が無い")
        if not os.path.isdir(os.path.join(_HOLDOUT, "commander_only")):
            raise unittest.SkipTest("限定確認の記録が無い")

    def test_p16_matches_the_holdout_dumps(self):
        for doc in HOLDOUT_DOCS:
            with io.open(os.path.join(_HOLDOUT, "commander_only", "dump_P16_%s.json" % doc),
                         encoding="utf-8") as fh:
                dump = json.load(fh)
            with io.open(os.path.join(_HOLDOUT, "commander_only", "key_%s.json" % doc),
                         encoding="utf-8") as fh:
                key = json.load(fh)
            by_row = {r["行の鍵"]: r["claim_id"] for r in key["rows_map"]}
            out = VD.verify_document(_read(doc))
            got = {c["id"]: c for c in out["claims"]}
            self.assertEqual(len(out["claims"]), HOLDOUT_EXPECTED[doc]["claims"], doc)
            self.assertEqual(out["document"]["states"]["GROUNDED"],
                             HOLDOUT_EXPECTED[doc]["grounded"], doc)
            checked = 0
            for row_key, want in dump.items():
                cid = by_row[row_key.split(":", 1)[1]]
                g = got[cid]
                self.assertEqual(g["state"], want["state"], (doc, row_key))
                self.assertEqual(g["pointers"], want["pointers"], (doc, row_key))
                self.assertEqual(g["reason"], want["reason"], (doc, row_key))
                self.assertEqual(g["subject"], want["subject"], (doc, row_key))
                checked += 1
            self.assertGreaterEqual(checked, 100, doc)


class RobustnessTableTest(unittest.TestCase):
    """14 書類の止めた件数が、記録した表(§2-3 の P16 の列)と同じ。"""

    def test_the_recorded_stop_counts_are_reproduced(self):
        docs = [d for d in sorted(ROBUSTNESS_P16) if _have(d)]
        if len(docs) < 10:
            raise unittest.SkipTest("材料が足りない(%d 書類)" % len(docs))
        for doc in docs:
            want_stopped, want_total = ROBUSTNESS_P16[doc]
            out = VD.verify_document(_read(doc))
            total = out["document"]["claims"]
            grounded = out["document"]["states"].get("GROUNDED", 0)
            self.assertEqual(total, want_total, doc)
            self.assertEqual(total - grounded, want_stopped, doc)


if __name__ == "__main__":
    unittest.main()
