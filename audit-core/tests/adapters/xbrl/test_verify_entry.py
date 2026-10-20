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
# 2026-10-14 の実測: 既定を P16 -> P20 にして止めた件数が動いた書類と、その P20 の止めた件数。
# 14 書類のうちこの 2 書類だけが動く(どちらも連結の要素が 0 件 = 連結財務諸表を作っていない会社)。
ROBUSTNESS_P20_MOVED = {"S100Z3HP": 19, "S100Z433": 30}
# 2026-10-20(段 2): 既定を P20 -> P21 にして、未使用 2 書類の P16 の記録(dump_P16)から**動いた行**。
# 5 行だけ(書類 -> 行 id -> P21 での state と参照先)。全部 VALUE_MISMATCH の参照先の移動で、
# GROUNDED は 1 行も動かない。F1′(前期の手がかり: 当期の fact から前期の fact へ)が S100Z4N9 の 4 行、
# F3b(増減の文は残高の対)が S100Z39P の 1 行。reason・subject は P16 の記録のまま。
# 封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md §1・N-12。それ以外の行は P16 の記録と byte 単位に同一。
HOLDOUT_P21_MOVED = {
    "S100Z39P": {
        "H-075": ("VALUE_MISMATCH", ["xbrl:jppfs_cor:NetDefinedBenefitLiability@CurrentYearInstant",
                                     "xbrl:jppfs_cor:NetDefinedBenefitLiability@Prior1YearInstant",
                                     "formula:a-b"]),
    },
    "S100Z4N9": {
        "H-067": ("VALUE_MISMATCH", ["xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration"]),
        "H-120": ("VALUE_MISMATCH", ["xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration"]),
        "H-122": ("VALUE_MISMATCH", ["xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration"]),
        "H-124": ("VALUE_MISMATCH", ["xbrl:jppfs_cor:OrdinaryIncome@Prior1YearDuration"]),
    },
}
# 出力の byte を字で留める値(engine の指紋を除いた本体の sha256)。
# 下の test_one_documents_output_sha256_is_pinned_literally が使う。
# 2026-10-14: 既定が P16 -> P20 になり、この値が動いた。**動いたのは profile 欄の字だけ**で、
# profile 欄を除いた本体は P16 と P20 で byte 単位に同一・行の差 0 件(S100Z4B6 は連結要素 147 の
# 連結あり書類なので P20 の落とし込みは発火しない)。古い値は P16 のときの
# dbc1da2a504f346766297800b1056509fdf3a9b4c0809260bd6b85d5b92dfbd5。
# 2026-10-20(段 2): 既定が P20 -> P21 になり、既定の値が動いた。**動いたのは profile 欄の字だけ**
# (S100Z4B6 の 147 の連結要素の書類で、P20 と P21 の claims は 1 行も違わない。profile 欄を除いた本体は同一)。
# 上の P20 の値は P20 を明示して回した結果として残す(測った時点の字。消さない)。
# 封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2。
# 2026-10-20(期を縛る P22 の段 2): 既定が P21 -> P22 になり、既定の値がもう一度動いた。**動いたのは profile 欄の字だけ**
# (S100Z4B6 は P21 と P22 で claims が 1 行も違わない。profile 欄を除いた本体は同一)。P21 の値は P21 を明示して回した結果として残す
# (測った時点の字。消さない)。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2。
_PINNED_BODY_SHA256_S100Z4B6_P20 = "413aaeab69b472ebdc60d9a4291d6845a62f457635ac56747e739b8c5696aa54"
_PINNED_BODY_SHA256_S100Z4B6_P21 = "540a60b75559eab62694a9c690892a8f36e4636de425024912f654112b7fa943"
_PINNED_BODY_SHA256_S100Z4B6 = "b0f5b32496a745526ba5b9107f1cc6856fef0a811c46f4e69679a57887288758"


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
    def test_the_two_structurally_failing_documents_are_flagged_under_p16(self):
        """**P16 のときの事実。**記録を書き換えず、profile を明示して留める
        (2026-10-14 に既定が P20 になり、既定で回すと旗が立たなくなった)。"""

        for doc in DOC_UNVERIFIABLE_DOCS:
            out = VD.verify_document(_read(doc), profile_name="P16")
            self.assertTrue(out["document"]["unverifiable"], doc)
            self.assertEqual(out["document"]["states"].get("GROUNDED", 0), 0, doc)
            self.assertEqual(out["document"]["rule"], VD.DOC_UNVERIFIABLE_RULE)
            # Claim 個別の state は旗で変わらない
            self.assertEqual(sum(out["document"]["states"].values()), out["document"]["claims"])

    def test_the_two_documents_are_no_longer_flagged_under_p20(self):
        """**2026-10-14 の既定(P20)の事実。**この 2 書類は連結財務諸表を作っていない会社で、
        P16 は 1 件も結べず書類ごと UNVERIFIABLE にしていた。P20 はこれを直す。
        2026-10-20 に既定が P21 になったので、測った時点の P20 を**明示して**留める(字は消さない)。"""

        for doc in DOC_UNVERIFIABLE_DOCS:
            out = VD.verify_document(_read(doc), profile_name="P20")
            self.assertEqual(out["profile"], "P20", doc)
            self.assertFalse(out["document"]["unverifiable"], doc)
            self.assertGreater(out["document"]["states"].get("GROUNDED", 0), 0, doc)
            self.assertEqual(sum(out["document"]["states"].values()), out["document"]["claims"], doc)

    def test_the_two_documents_are_no_longer_flagged_under_p21(self):
        """**P21 のときの事実(2026-10-20 の段 2 から P22 の段 2 の前まで既定だった)。**P21 を明示して、
        この 2 書類は書類ごと UNVERIFIABLE にならない。P21 は P20 の GROUNDED を動かさない(封の N-4)。"""

        for doc in DOC_UNVERIFIABLE_DOCS:
            out = VD.verify_document(_read(doc), profile_name="P21")
            self.assertEqual(out["profile"], "P21", doc)
            self.assertFalse(out["document"]["unverifiable"], doc)
            self.assertGreater(out["document"]["states"].get("GROUNDED", 0), 0, doc)
            self.assertEqual(sum(out["document"]["states"].values()), out["document"]["claims"], doc)

    def test_the_two_documents_are_no_longer_flagged_under_the_default(self):
        """**既定(2026-10-20 の期を縛る P22 の段 2 から P22)の事実。**既定の経路でも、この 2 書類は書類ごと
        UNVERIFIABLE にならない(字の試験ではなく振る舞いで)。"""

        for doc in DOC_UNVERIFIABLE_DOCS:
            out = VD.verify_document(_read(doc))
            self.assertEqual(out["profile"], "P22", doc)
            self.assertFalse(out["document"]["unverifiable"], doc)
            self.assertGreater(out["document"]["states"].get("GROUNDED", 0), 0, doc)
            # 旗が外れても Claim 個別の state の合計は全件のまま
            self.assertEqual(sum(out["document"]["states"].values()), out["document"]["claims"], doc)

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
        self.assertEqual(out["profile"], "P22")
        self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(),
                         "%s" % _PINNED_BODY_SHA256_S100Z4B6)

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_one_documents_output_sha256_is_pinned_literally_under_p21(self):
        """2026-10-20 の名指しの直し 段 2 から期を縛る P22 の段 2 の前までの既定(P21)のときの値を、P21 を**明示して**残す
        (測った時点の字。消さない)。S100Z4B6 は profile 欄を除いて P21 と P22 で同一。"""

        out = VD.verify_document(_read("S100Z4B6"), profile_name="P21")
        del out["engine"]
        body = VD.dumps(out)
        self.assertEqual(out["profile"], "P21")
        self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(),
                         "%s" % _PINNED_BODY_SHA256_S100Z4B6_P21)

    @unittest.skipUnless(_have("S100Z4B6"), "材料が無い")
    def test_one_documents_output_sha256_is_pinned_literally_under_p20(self):
        """2026-10-14 の既定(P20)のときの値を、P20 を**明示して**残す(測った時点の字。消さない)。
        2026-10-20 に既定が P21 になったが、S100Z4B6 は profile 欄を除いて P20 と P21 で同一。"""

        out = VD.verify_document(_read("S100Z4B6"), profile_name="P20")
        del out["engine"]
        body = VD.dumps(out)
        self.assertEqual(out["profile"], "P20")
        self.assertEqual(hashlib.sha256(body.encode("utf-8")).hexdigest(),
                         "%s" % _PINNED_BODY_SHA256_S100Z4B6_P20)

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
            self.assertEqual(data["profile"], "P22")     # 2026-10-14 は P20、2026-10-20(段 2)から P21、同日の期を縛る P22 の段 2 から P22


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

    def _dump_and_rows(self, doc):
        with io.open(os.path.join(_HOLDOUT, "commander_only", "dump_P16_%s.json" % doc),
                     encoding="utf-8") as fh:
            dump = json.load(fh)
        with io.open(os.path.join(_HOLDOUT, "commander_only", "key_%s.json" % doc),
                     encoding="utf-8") as fh:
            key = json.load(fh)
        return dump, {r["行の鍵"]: r["claim_id"] for r in key["rows_map"]}

    def test_p16_matches_the_holdout_dumps(self):
        """**P16 のときの事実。**2026-10-20(段 2)に既定が P21 になったので、P16 を明示して回す
        (それまでは既定 = P16 と P20 が未使用 2 書類で同じだった)。数も記録も書き換えない。"""

        for doc in HOLDOUT_DOCS:
            dump, by_row = self._dump_and_rows(doc)
            out = VD.verify_document(_read(doc), profile_name="P16")
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

    def test_p21_moves_only_the_five_recorded_holdout_rows(self):
        """**P21(2026-10-20 の名指しの直し 段 2 から期を縛る P22 の段 2 の前まで既定だった。いまは P21 を明示)で P16 の記録と違う行は、
        HOLDOUT_P21_MOVED の 5 行だけ。**
        動いた行は新しい state・参照先を字で留め(全部 VALUE_MISMATCH で、元も VALUE_MISMATCH)、
        reason・subject は P16 の記録のまま。それ以外の行は 4 つの欄とも P16 の記録と同一。
        GROUNDED の数も P16 の記録(HOLDOUT_EXPECTED)のまま。封の N-12。"""

        moved_seen = {}
        for doc in HOLDOUT_DOCS:
            dump, by_row = self._dump_and_rows(doc)
            out = VD.verify_document(_read(doc), profile_name="P21")
            self.assertEqual(out["profile"], "P21", doc)
            got = {c["id"]: c for c in out["claims"]}
            self.assertEqual(len(out["claims"]), HOLDOUT_EXPECTED[doc]["claims"], doc)
            self.assertEqual(out["document"]["states"]["GROUNDED"],
                             HOLDOUT_EXPECTED[doc]["grounded"], doc)
            expect_moved = HOLDOUT_P21_MOVED.get(doc, {})
            checked = 0
            for row_key, want in dump.items():
                rid = row_key.split(":", 1)[1]
                g = got[by_row[rid]]
                if rid in expect_moved:
                    state, pointers = expect_moved[rid]
                    self.assertEqual(want["state"], "VALUE_MISMATCH", (doc, rid))   # 元も VALUE_MISMATCH
                    self.assertEqual(g["state"], state, (doc, rid))
                    self.assertEqual(g["pointers"], pointers, (doc, rid))
                    self.assertNotEqual(g["pointers"], want["pointers"], (doc, rid))   # 本当に動いた行
                    self.assertEqual(g["reason"], want["reason"], (doc, rid))
                    self.assertEqual(g["subject"], want["subject"], (doc, rid))
                    moved_seen.setdefault(doc, []).append(rid)
                else:
                    for f in ("state", "pointers", "reason", "subject"):
                        self.assertEqual(g[f], want[f], (doc, rid, f))
                checked += 1
            self.assertGreaterEqual(checked, 100, doc)
        self.assertEqual({d: sorted(v) for d, v in moved_seen.items()},
                         {d: sorted(v) for d, v in HOLDOUT_P21_MOVED.items()})
        self.assertEqual(sum(len(v) for v in moved_seen.values()), 5)

    # 2026-10-20(期を縛る P22 の段 2): 既定が P22 になって、未使用 2 書類の P16 の記録(dump_P16)の中で P21 の 5 行のほかに動く行。
    # 1 行だけ: S100Z39P の H-042(増減の文『1年内返済予定の長期借入金が100百万円減少』の 100 が前期残高と一致する型 = 結果文書の型 A)が
    # GROUNDED -> POINTER_NOT_FOUND(no_element。参照先なし)。dump に無い行でもう 1 行 GROUNDED が減る(S100Z4N9 の N056『1年内償還予定の社債の減少300,000千円』、型 A)ので、
    # GROUNDED の数は 80 -> 79(S100Z39P)・99 -> 98(S100Z4N9)。全部 E-2(67 書類)の GROUNDED を離れた 25 行に入る行で、新しく GROUNDED になる行は 0。
    HOLDOUT_P22_MOVED_FROM_GROUNDED = {"S100Z39P": {"H-042": ("POINTER_NOT_FOUND", [], "no_element")}}
    HOLDOUT_P22_GROUNDED = {"S100Z39P": 79, "S100Z4N9": 98}

    def test_the_default_p22_moves_the_five_p21_rows_and_leaves_grounded_on_two_rows(self):
        """**既定(2026-10-20 の期を縛る P22 の段 2 から P22)で P16 の記録と違う行は、P21 の 5 行(HOLDOUT_P21_MOVED。P21 と同じ state・参照先)に
        H-042 の 1 行(GROUNDED -> POINTER_NOT_FOUND)を足した 6 行だけ。**それ以外の行は 4 つの欄とも P16 の記録と同一。
        GROUNDED の数は S100Z39P 80 -> 79・S100Z4N9 99 -> 98(後者は dump に無い行)。新しく GROUNDED になる行は無い。"""

        moved_seen = {}
        for doc in HOLDOUT_DOCS:
            dump, by_row = self._dump_and_rows(doc)
            out = VD.verify_document(_read(doc))
            self.assertEqual(out["profile"], "P22", doc)
            got = {c["id"]: c for c in out["claims"]}
            self.assertEqual(len(out["claims"]), HOLDOUT_EXPECTED[doc]["claims"], doc)
            self.assertEqual(out["document"]["states"]["GROUNDED"], self.HOLDOUT_P22_GROUNDED[doc], doc)
            self.assertLess(out["document"]["states"]["GROUNDED"], HOLDOUT_EXPECTED[doc]["grounded"], doc)
            expect_moved = HOLDOUT_P21_MOVED.get(doc, {})
            expect_left = self.HOLDOUT_P22_MOVED_FROM_GROUNDED.get(doc, {})
            checked = 0
            for row_key, want in dump.items():
                rid = row_key.split(":", 1)[1]
                g = got[by_row[rid]]
                if rid in expect_moved:
                    state, pointers = expect_moved[rid]
                    self.assertEqual(want["state"], "VALUE_MISMATCH", (doc, rid))
                    self.assertEqual(g["state"], state, (doc, rid))
                    self.assertEqual(g["pointers"], pointers, (doc, rid))
                    self.assertNotEqual(g["pointers"], want["pointers"], (doc, rid))
                    self.assertEqual(g["reason"], want["reason"], (doc, rid))
                    self.assertEqual(g["subject"], want["subject"], (doc, rid))
                    moved_seen.setdefault(doc, []).append(rid)
                elif rid in expect_left:
                    state, pointers, reason = expect_left[rid]
                    self.assertEqual(want["state"], "GROUNDED", (doc, rid))             # 元は GROUNDED
                    self.assertEqual((g["state"], g["pointers"], g["reason"]), (state, pointers, reason), (doc, rid))
                    self.assertEqual(g["subject"], want["subject"], (doc, rid))
                    moved_seen.setdefault(doc, []).append(rid)
                else:
                    for f in ("state", "pointers", "reason", "subject"):
                        self.assertEqual(g[f], want[f], (doc, rid, f))
                checked += 1
            self.assertGreaterEqual(checked, 100, doc)
        want_moved = {}
        for d, v in HOLDOUT_P21_MOVED.items():
            want_moved.setdefault(d, []).extend(v)
        for d, v in self.HOLDOUT_P22_MOVED_FROM_GROUNDED.items():
            want_moved.setdefault(d, []).extend(v)
        self.assertEqual({d: sorted(v) for d, v in moved_seen.items()}, {d: sorted(v) for d, v in want_moved.items()})
        self.assertEqual(sum(len(v) for v in moved_seen.values()), 6)


class RobustnessTableTest(unittest.TestCase):
    """14 書類の止めた件数が、記録した表(§2-3 の P16 の列)と同じ。

    2026-10-14 に既定が P20 になったが、**この表は P16 の測定の記録なので数は書き換えない。**
    profile を明示して回す。既定(P20)で動く 2 書類は下の ROBUSTNESS_P20_MOVED で別に留める。"""

    def test_the_recorded_stop_counts_are_reproduced(self):
        docs = [d for d in sorted(ROBUSTNESS_P16) if _have(d)]
        if len(docs) < 10:
            raise unittest.SkipTest("材料が足りない(%d 書類)" % len(docs))
        for doc in docs:
            want_stopped, want_total = ROBUSTNESS_P16[doc]
            out = VD.verify_document(_read(doc), profile_name="P16")
            total = out["document"]["claims"]
            grounded = out["document"]["states"].get("GROUNDED", 0)
            self.assertEqual(total, want_total, doc)
            self.assertEqual(total - grounded, want_stopped, doc)

    def test_only_the_two_nonconsolidated_documents_move_under_p20(self):
        """**既定を P16 -> P20 にして動いたのは、連結財務諸表の無い 2 書類だけ**
        (2026-10-14 の実測。14 書類中 12 書類は 1 件も動かない)。
        動いた 2 書類の P20 の止めた件数も字で留める。2026-10-20 に既定が P21 になったので P20 を明示する。"""

        docs = [d for d in sorted(ROBUSTNESS_P16) if _have(d)]
        if len(docs) < 10:
            raise unittest.SkipTest("材料が足りない(%d 書類)" % len(docs))
        moved = []
        for doc in docs:
            want_stopped, want_total = ROBUSTNESS_P16[doc]
            out = VD.verify_document(_read(doc), profile_name="P20")     # 2026-10-14 の既定 = P20(2026-10-20 から明示)
            total = out["document"]["claims"]
            stopped = total - out["document"]["states"].get("GROUNDED", 0)
            self.assertEqual(total, want_total, doc)      # Claim の切り方は profile で変わらない
            if stopped != want_stopped:
                moved.append(doc)
                self.assertEqual(stopped, ROBUSTNESS_P20_MOVED[doc], doc)
        self.assertEqual(sorted(moved), sorted(ROBUSTNESS_P20_MOVED),
                         "既定で動く書類の集合が記録と違う")

    def test_p21_gives_the_same_stop_counts_as_p20(self):
        """**2026-10-20(名指しの直し 段 2)。P21(その時の既定。いまは P21 を明示)でも、14 書類の止めた件数(= 全件 - GROUNDED)は
        P20 のときと同じ**(P21 は GROUNDED を動かさない。封の N-4)。P16 の表(ROBUSTNESS_P16)から
        動く書類は ROBUSTNESS_P20_MOVED の 2 書類だけで、その数も P20 のまま。"""

        docs = [d for d in sorted(ROBUSTNESS_P16) if _have(d)]
        if len(docs) < 10:
            raise unittest.SkipTest("材料が足りない(%d 書類)" % len(docs))
        moved = []
        for doc in docs:
            want_stopped, want_total = ROBUSTNESS_P16[doc]
            out = VD.verify_document(_read(doc), profile_name="P21")          # 2026-10-20 の名指しの直し 段 2 の既定 = P21(いまは明示)
            self.assertEqual(out["profile"], "P21", doc)
            total = out["document"]["claims"]
            stopped = total - out["document"]["states"].get("GROUNDED", 0)
            self.assertEqual(total, want_total, doc)
            if stopped != want_stopped:
                moved.append(doc)
                self.assertEqual(stopped, ROBUSTNESS_P20_MOVED[doc], doc)
        self.assertEqual(sorted(moved), sorted(ROBUSTNESS_P20_MOVED))

    # 2026-10-20(期を縛る P22 の段 2): 既定が P22 になって、14 書類の止めた件数(= 全件 - GROUNDED)が P20 のときから増える書類と、その P22 の止めた件数。
    # 5 書類で合計 +11(E-2 の GROUNDED を離れた 25 行のうち、この 14 書類に入る行)。残りの 9 書類は P16 の表のまま、
    # P20 で動く 2 書類のうち S100Z3HP は P22 でも P20 のまま(19)、S100Z433 は 30 -> 31。
    ROBUSTNESS_P22_STOPPED = {"S100Z3CO": 62, "S100Z3JY": 52, "S100Z433": 31, "S100Z4DE": 47, "S100Z4PA": 64}

    def test_the_default_p22_stops_more_on_five_of_the_fourteen_documents(self):
        """**2026-10-20(期を縛る P22 の段 2)。既定が P22 になって、14 書類の止めた件数が P20・P21 のときより増えるのは
        ROBUSTNESS_P22_STOPPED の 5 書類だけ**(合計 +11。増えた行は GROUNDED -> 非 GROUNDED で、止めた件数が減る書類は 0)。
        残りの書類は P16 の表(ROBUSTNESS_P16)か P20 の表(ROBUSTNESS_P20_MOVED)のまま。claim の数は profile で変わらない。"""

        docs = [d for d in sorted(ROBUSTNESS_P16) if _have(d)]
        if len(docs) < 10:
            raise unittest.SkipTest("材料が足りない(%d 書類)" % len(docs))
        more = {}
        for doc in docs:
            want_stopped, want_total = ROBUSTNESS_P16[doc]
            out = VD.verify_document(_read(doc))          # 既定 = P22
            self.assertEqual(out["profile"], "P22", doc)
            total = out["document"]["claims"]
            stopped = total - out["document"]["states"].get("GROUNDED", 0)
            self.assertEqual(total, want_total, doc)
            base = ROBUSTNESS_P20_MOVED.get(doc, want_stopped)        # P20・P21 のときの止めた件数
            self.assertGreaterEqual(stopped, base, doc)
            if stopped != base:
                more[doc] = stopped
        self.assertEqual(more, self.ROBUSTNESS_P22_STOPPED)
        self.assertEqual(sum(v - ROBUSTNESS_P20_MOVED.get(d, ROBUSTNESS_P16[d][0]) for d, v in more.items()), 11)


if __name__ == "__main__":
    unittest.main()
