# -*- coding: utf-8 -*-
"""概念で結ぶ直し(profile P16、2026-10-13)の試験。

2 層ある。

1. 規則の単体試験 ― C1〜C5 の各規則に「当たる例」と「当たらない例」の両方を置く
   (規則を 1 つ外すと、その規則の試験だけが赤くなる)。
2. 材料での試験 ― AI 文の材料(``S100Z4Q1`` の MD&A を ``ai_prose_2026-10-09.txt`` に
   差し替えた ZIP)を P7(いまの main の挙動)と P16 で回し、**独立ラベル**
   (``fixtures/xbrl/independent_grounds_labels_2026-10-13.json``、2 席一致の確定 183 件)
   に対する根拠レベルの指標で、P7 の値を字で留め、P16 がそれを上回ることを留める。
   期待値は**実装の出力ではなく独立ラベル**から来る。キャッシュの ZIP が無ければ落ちる
   (skip にしない)。
"""

import hashlib
import importlib.util
import io
import os
import sys
import unittest

from adapters.xbrl import edinet
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
_GOLDEN = os.path.join(_AUDIT_CORE, "tests", "golden")
_MEASURE = os.path.join(_AUDIT_CORE, "measure")

DOC = "S100Z4Q1"
DOC_ZIP_SHA256 = "0731a291f10af5dd207e05d54df8e2b5dc34e79a84de94af1c1a5d4e207228f6"
MODIFIED_ZIP_SHA256 = "03521437be23c8e2a02d85b4bc29a215646803582e9101fdf185521041174799"
LABELS_SHA256 = "1aa397f8c841c49e5b90de495062117eb17655c2d67b7887493ca517c91c7f79"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. 規則の単体試験
# ---------------------------------------------------------------------------

class PriorCueTest(unittest.TestCase):
    """C2: 数の直前の「前期」「前期末」「(同」、数の直後の「から」。"""

    def _at(self, s, num):
        a = s.index(num)
        return a, a + len(num)

    def test_prior_word_right_before_number(self):
        s = "ROEは5.8%(前期13.3%)となり"
        a, b = self._at(s, "13.3")
        self.assertTrue(R._prior_cue(s, a, b))
        s = "自己資本比率は61.7%(前期末60.6%)と"
        a, b = self._at(s, "60.6")
        self.assertTrue(R._prior_cue(s, a, b))
        s = "不動産賃貸料15百万円(同15百万円)、"
        a = s.index("(同15") + 2
        self.assertTrue(R._prior_cue(s, a, a + 2))
        a, b = self._at(s, "15")  # 最初の 15(当期)
        self.assertFalse(R._prior_cue(s, a, b))

    def test_hikaku_is_not_a_prior_cue(self):
        s = "売上高は38,064百万円(前期比2.9%増)となり"
        a, b = self._at(s, "2.9")
        self.assertFalse(R._prior_cue(s, a, b))

    def test_kara_marks_the_earlier_number(self):
        # 本番の b は数と単位の終わり(NUM_RE は単位まで取る)。
        s = "売上総利益率は32.5%から29.8%へと低下"
        a, b = self._at(s, "32.5%")
        self.assertTrue(R._prior_cue(s, a, b))
        a, b = self._at(s, "29.8%")
        self.assertFalse(R._prior_cue(s, a, b))

    def test_clause_cue_for_direction_word(self):
        s = "938百万円拡大したこと、3前期は売上債権が209百万円減少したのに対し"
        self.assertTrue(R._prior_cue_clause(s, s.index("減少")))
        s = "前期は増加した、当期は売上債権が減少した"
        self.assertFalse(R._prior_cue_clause(s, s.index("減少")))  # 読点で節が切れる
        s = "前期比で売上債権が減少した"
        self.assertFalse(R._prior_cue_clause(s, s.index("減少")))
        s = "営業損失42,487千円(前連結会計年度は営業損失9,709千円)の減益となりました"
        self.assertFalse(R._prior_cue_clause(s, s.index("減益")))  # 閉じた括弧の中は別の節


class RatioWordTest(unittest.TestCase):
    """C5: 率の語(RATIO_TABLE)と数の間に助詞・「前期の」・「NN%から」だけを許す。"""

    def test_ratio_word_before_number(self):
        s = "売上総利益率は32.5%から29.8%へと低下しております"
        self.assertEqual(R._ratio_word_before(s, s.index("32.5")), "売上総利益率")
        self.assertEqual(R._ratio_word_before(s, s.index("29.8")), "売上総利益率")
        s = "売上原価率は前期の67.5%から70.2%へと2.7ポイント上昇し"
        self.assertEqual(R._ratio_word_before(s, s.index("67.5")), "売上原価率")
        self.assertEqual(R._ratio_word_before(s, s.index("70.2")), "売上原価率")

    def test_longest_word_wins_and_non_ratio_is_none(self):
        s = "売上高営業利益率は5.0%でした"
        self.assertEqual(R._ratio_word_before(s, s.index("5.0")), "売上高営業利益率")
        s = "売上総利益は1,000百万円でした"
        self.assertIsNone(R._ratio_word_before(s, s.index("1,000")))
        s = "売上総利益率が高い水準で、営業利益は1,465百万円"
        self.assertIsNone(R._ratio_word_before(s, s.index("1,465")))

    def test_formula_token_maps_to_ratio_comparator(self):
        raw = {
            "id": "N036", "sentence": 0, "span": "x", "value": 32.5, "unit": "%",
            "subject": "売上総利益率", "form": "derived_value",
            "pointer": ["xbrl:jppfs_cor:GrossProfit@Prior1YearDuration",
                        "xbrl:jppfs_cor:NetSales@Prior1YearDuration", "formula:a/b*100"],
            "bound": True, "reason": None, "result": "GROUNDED", "recomputed": 32.51,
        }
        recipe = R.claim_to_recipe(raw, "num")
        self.assertEqual(recipe.contract.comparator, "ratio*100")


class PctPhraseTest(unittest.TestCase):
    """C4: 「46.0%の大幅減益」の形。"""

    def test_phrase_forms(self):
        for text, word in (("46.0%の大幅減益となりました", "減益"),
                           ("20.7%の大幅増加となりました", "増加"),
                           ("8.9%増加しました", "増加"),
                           ("2.9%増", "増")):
            m = R._PCT_PHRASE_RE.search(text)
            self.assertIsNotNone(m, text)
            self.assertEqual(m.group(3), word)
        self.assertIsNone(R._PCT_PHRASE_RE.search("自己資本比率は61.7%でした"))


class FlowItemTest(unittest.TestCase):
    """C3: 「Xの増加/減少(額)」を X の CF 増減項目に結ぶ。符号はラベルの括弧が正本。"""

    FLOW = {"base": {"契約資産": ["DecreaseIncreaseInContractAssetsOpeCF"]},
            "sign": {"IncreaseDecreaseInNetDefinedBenefitAssetOpeCF": -1}}

    def test_direction_word_right_after_subject(self):
        s = "営業活動の結果獲得した資金の主な内容は、完成業務補償引当金の増加786百万円、契約資産の減少161百万円"
        pos = s.index("減少")
        self.assertEqual(R._flow_elems_for(s, "契約資産", pos, self.FLOW),
                         ["DecreaseIncreaseInContractAssetsOpeCF"])

    def test_amount_after_increase_word(self):
        s = "営業キャッシュ・フローの減少は、契約資産の増加額が前期890百万円から当期1,828百万円へ"
        pos = s.index("890")
        self.assertEqual(R._flow_elems_for(s, "契約資産", pos, self.FLOW),
                         ["DecreaseIncreaseInContractAssetsOpeCF"])

    def test_not_a_flow_phrase(self):
        s = "契約資産は11,267百万円"
        self.assertIsNone(R._flow_elems_for(s, "契約資産", s.index("11,267"), self.FLOW))
        s = "総資産の減少161百万円"
        self.assertIsNone(R._flow_elems_for(s, "総資産", s.index("減少"), self.FLOW))
        self.assertIsNone(R._flow_elems_for(s, "契約資産", 3, None))
        # 貸借対照表の説明(キャッシュ・フローの手がかり語が無い)では掛けない。
        s = "資産の増加は、契約資産の減少161百万円によるものです"
        self.assertIsNone(R._flow_elems_for(s, "契約資産", s.index("減少"), self.FLOW))

    def test_context_window_looks_back_two_sentences(self):
        # 手がかり語がこの文に無くても直前 2 文に在れば True。3 文前だけなら False。
        sents = ["営業活動によるキャッシュ・フローは減少した。", "主な要因は次のとおり。",
                 "契約資産の減少161百万円。", "次の段落。", "さらに次。"]
        self.assertEqual(R._cf_context_flags(sents), [True, True, True, False, False])
        self.assertEqual(R._cf_context_flags(["純資産の増加。", "契約資産の減少。"]), [False, False])

    def test_sign_from_label_overrides_name(self):
        # 名前は IncreaseDecrease(= 正が増加)だが、ラベル「(△は増加)」は負が増加。
        self.assertEqual(R._flow_sign_of("jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF", self.FLOW), -1)
        self.assertEqual(R._flow_sign_of("jppfs_cor:IncreaseDecreaseInContractLiabilitiesOpeCF", self.FLOW), 1)
        self.assertEqual(R._flow_sign_of("jppfs_cor:DecreaseIncreaseInTradeReceivables", None), -1)
        self.assertIsNone(R._flow_sign_of("jppfs_cor:NetSales", self.FLOW))


class StatementFirstTest(unittest.TestCase):
    """C1: 計算書(jppfs_cor)の fact を先に置く。並べ替えは安定で、中身は同じ。"""

    def test_statement_facts_come_first_and_order_is_stable(self):
        facts = [
            {"name": "jpcrp_cor:NetSalesSummaryOfBusinessResults", "context": "CurrentYearDuration", "value": 1.0},
            {"name": "jpcrp030000-asr_E00000-000:Foo", "context": "CurrentYearDuration", "value": 2.0},
            {"name": "jppfs_cor:NetSales", "context": "CurrentYearDuration", "value": 3.0},
            {"name": "jpcrp_cor:AssetsSummaryOfBusinessResults", "context": "CurrentYearInstant", "value": 4.0},
            {"name": "jppfs_cor:Assets", "context": "CurrentYearInstant", "value": 5.0},
        ]
        out = R.statement_facts_first(facts)
        self.assertEqual([f["value"] for f in out], [3.0, 5.0, 1.0, 2.0, 4.0])
        self.assertEqual(sorted(map(id, out)), sorted(map(id, facts)))  # 同じ辞書、複製しない


class ProfileFlagsTest(unittest.TestCase):
    def test_only_p16_has_the_new_flags(self):
        for name in ("P1", "P5F", "P6", "P7", "P13", "P15"):
            p = V.PROFILES[name]
            self.assertFalse(p.statement_facts_first or p.period_cue or p.flow_item_from_label
                             or p.pct_change_phrase or p.ratio_table, name)
        p = V.P16
        self.assertTrue(p.statement_facts_first and p.period_cue and p.flow_item_from_label
                        and p.pct_change_phrase and p.ratio_table and p.taxonomy_labels)
        self.assertIs(V.PROFILES["P16"], V.P16)


# ---------------------------------------------------------------------------
# 2. 材料での試験(独立ラベルに対する根拠レベルの指標)
# ---------------------------------------------------------------------------

class ConceptBindingMaterialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for p in (_AUDIT_CORE, _GOLDEN):
            if p not in sys.path:
                sys.path.insert(0, p)
        INS = _load("_instrument", os.path.join(_GOLDEN, "_instrument.py"))
        builder = _load("ai_prose_claims", os.path.join(_FIXTURES, "ai_prose_claims_2026-10-09.py"))
        GE = _load("grounds_eval", os.path.join(_MEASURE, "grounds_eval.py"))

        zb = edinet.read_cached(DOC, expected_sha256=DOC_ZIP_SHA256)  # 無ければ落ちる
        with io.open(os.path.join(_FIXTURES, "ai_prose_2026-10-09.txt"), encoding="utf-8") as fh:
            prose = fh.read()
        mod_zb, _mdna, _src = builder.build_modified_zip(zb, prose)
        assert hashlib.sha256(mod_zb).hexdigest() == MODIFIED_ZIP_SHA256, "AI 文の ZIP が封じた sha と違う"

        with open(GE.LABELS_PATH, "rb") as fh:
            assert hashlib.sha256(fh.read()).hexdigest() == LABELS_SHA256, "独立ラベルが封じた sha と違う"
        cls.labels = GE.load_labels()
        cls.GE = GE
        cls.rows = {}
        cls.dump = {}
        for name in ("P7", "P16"):
            recs, res, _metas = INS.run_verification(DOC, V.PROFILES[name], lambda: mod_zb)
            dump = {}
            for r in recs:
                q = res[r.claim.id]
                dump[r.claim.id] = {"state": q.state.value, "pointers": [str(p) for p in r.pointers],
                                    "subject": r.claim.subject}
            cls.dump[name] = dump
            cls.rows[name] = GE.score(dump, cls.labels)

    def _m(self, name, select=None):
        return self.GE.summarize(self.rows[name], select)

    def test_labels_are_the_sealed_183(self):
        self.assertEqual(len(self.labels), 183)
        self.assertEqual(self._m("P7")["MISSING"], 0)
        self.assertEqual(self._m("P16")["MISSING"], 0)

    def test_p7_baseline_pinned(self):
        # いまの main の挙動(P7)を独立ラベルで測った値。動いたら「何が動いたか」を読む。
        m = self._m("P7")
        self.assertEqual((m["L"], m["G"], m["E1_strict"], m["E2_strict"], m["E2_v0"], m["E3"]),
                         (183, 90, 66, 24, 12, 93))

    def test_p16_beats_p7_on_every_axis(self):
        m7, m16 = self._m("P7"), self._m("P16")
        self.assertGreater(m16["E1_strict"], m7["E1_strict"])
        self.assertLess(m16["E2_strict"], m7["E2_strict"])
        self.assertLess(m16["E3"], m7["E3"])

    def test_p16_floor(self):
        # 2026-10-13 の実測 E1' 146 / E2 厳密 8 / E3 29。下げる変更はここで赤くなる。
        m = self._m("P16")
        self.assertGreaterEqual(m["E1_strict"], 146)
        self.assertLessEqual(m["E2_strict"], 8)
        self.assertLessEqual(m["E3"], 29)
        mv = self._m("P16", lambda r: not r["direction"])
        self.assertLessEqual(mv["E2_strict"], 2)

    def _ptr(self, name, cid):
        return self.dump[name][cid]["pointers"]

    def test_c1_statement_table_beats_summary(self):
        self.assertEqual(self._ptr("P7", "N010"), ["xbrl:jpcrp_cor:NetAssetsSummaryOfBusinessResults@CurrentYearInstant"])
        self.assertEqual(self._ptr("P16", "N010"), ["xbrl:jppfs_cor:NetAssets@CurrentYearInstant"])

    def test_c2_prior_period_from_cue(self):
        self.assertEqual(self._ptr("P16", "N113"), ["xbrl:jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults@Prior1YearDuration"])
        self.assertEqual(self.dump["P16"]["N113"]["state"], "GROUNDED")
        self.assertEqual(self._ptr("P16", "T103")[0], "xbrl:jppfs_cor:DecreaseIncreaseInNotesAndAccountsReceivableTradeOpeCF@Prior1YearDuration")

    def test_c3_flow_item_from_label(self):
        self.assertEqual(self._ptr("P16", "T095")[0],
                         "xbrl:jpcrp030000-asr_E36539-000:DecreaseIncreaseInContractAssetsOpeCF@CurrentYearDuration")
        self.assertEqual(self._ptr("P16", "N279"), ["xbrl:jppfs_cor:IncreaseDecreaseInNetDefinedBenefitAssetOpeCF@Prior1YearDuration"])
        self.assertEqual(self.dump["P16"]["N279"]["state"], "GROUNDED")
        # P7 は残高の 2 時点に結んでいた(ラベルは CF 項目)。
        self.assertTrue(self._ptr("P7", "T095")[0].startswith("xbrl:jppfs_cor:ContractAssets@"))

    def test_c4_pct_change_phrase(self):
        self.assertEqual(self._ptr("P16", "N067"),
                         ["xbrl:jppfs_cor:OperatingIncome@CurrentYearDuration", "xbrl:jppfs_cor:OperatingIncome@Prior1YearDuration"])
        self.assertEqual(self.dump["P16"]["N067"]["state"], "GROUNDED")
        self.assertEqual(self.dump["P7"]["N067"]["state"], "POINTER_NOT_FOUND")

    def test_c3_gate_keeps_balance_sheet_context_on_the_original_document(self):
        # 原文 S100Z4Q1 の純資産の説明(キャッシュ・フローの手がかり語が無い段落)の
        # 「退職給付に係る調整累計額の増加」「退職給付に係る資産の増加」は残高の 2 時点のまま。
        # 文脈の門を外す変異(常に True)では CF 増減項目に変わる(state は同じ GROUNDED なので
        # pointer で留める)。
        zb = edinet.read_cached(DOC, expected_sha256=DOC_ZIP_SHA256)
        INS = _load("_instrument", os.path.join(_GOLDEN, "_instrument.py"))
        recs, res, _metas = INS.run_verification(DOC, V.P16, lambda: zb)
        ptr = {r.claim.id: [str(p) for p in r.pointers] for r in recs}
        self.assertEqual(ptr["T024"], ["xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlans@CurrentYearInstant",
                                       "xbrl:jppfs_cor:RemeasurementsOfDefinedBenefitPlans@Prior1YearInstant",
                                       "builtin:sign(cur-prior)"])
        self.assertEqual(ptr["T011"][0], "xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant")
        self.assertEqual(ptr["N021"][0], "xbrl:jppfs_cor:NetDefinedBenefitAsset@CurrentYearInstant")
        # 同じ書類のキャッシュ・フローの説明では CF 項目に結ぶ。
        self.assertEqual(ptr["T027"][0], "xbrl:jpcrp030000-asr_E36539-000:DecreaseIncreaseInContractAssetsOpeCF@CurrentYearDuration")
        self.assertEqual(ptr["T029"][0], "xbrl:jppfs_cor:IncreaseDecreaseInContractLiabilitiesOpeCF@CurrentYearDuration")

    def test_c5_ratio_from_two_facts(self):
        self.assertEqual(self._ptr("P16", "N036"),
                         ["xbrl:jppfs_cor:GrossProfit@Prior1YearDuration", "xbrl:jppfs_cor:NetSales@Prior1YearDuration", "formula:a/b*100"])
        self.assertEqual(self._ptr("P16", "N037"),
                         ["xbrl:jppfs_cor:GrossProfit@CurrentYearDuration", "xbrl:jppfs_cor:NetSales@CurrentYearDuration", "formula:a/b*100"])
        self.assertEqual(self.dump["P16"]["N036"]["state"], "GROUNDED")


if __name__ == "__main__":
    unittest.main()
