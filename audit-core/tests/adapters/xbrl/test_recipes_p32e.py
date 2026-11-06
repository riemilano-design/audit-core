# -*- coding: utf-8 -*-
"""P32E(前期の手がかりがある数を当期の fact に落とさない PB)の試験。封 docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md §1。

P32E = P30E + 旗 ``prior_cue_bind_2026_11_06``。既定 P27 は不変(``DEFAULT_PROFILE`` = P27)。旗が真のとき ``recipes._direct_value_claim`` に 2 つの block が通る。

* 窓の関数 ``_prior_cue_window_2026_11_06(s, a)``: 数の直前 12 字が 前期・前期末・前連結会計年度・前事業年度・前年同期(+ は・には・の・、)か「(同」で終わるか。
  ``_prior_cue`` の窓の枝と同じ語・同じ窓で、「から」の枝は持たない(「A から B を」の A に当たる偽陽性を避ける)。
* block A(最初の枝の前): 窓の手がかりが真・hits が空でない・hits に ``Prior1Year`` の fact が無いとき、``CurrentYear`` の hit を外す(``Prior2Year`` 以前は残す)。
  外した後は従来の枝(導出 a-b → 最後の枝)に落ちる。
* block B(最後の枝。§1b の止めの後・``last_branch_cues`` の block の前): 窓の手がかりが真なら、増減の語(is_diff)があっても ``Prior1Year`` の fact を名指して
  VALUE_MISMATCH(F1′ と同じ 5 つの欄の字)。``Prior1Year`` の fact が無ければ何もしない。

**各挙動について「P32E で効く」と「P30E では従来どおり」を対にして留める。** 合成の instance(facts と contexts を直接組む)で ``_direct_value_claim`` を呼ぶ。通信しない。
"""
import dataclasses
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
PRI2 = "Prior2YearDuration"
NAME = "NetSales"
PTR = "jppfs_cor:NetSales"
SEAL = "docs/XBRL_PRIOR_CUE_BIND_ENGINE_SEAL_2026-11-06.md"
REASON_VM = "value differs(segment/other period?)"
FLAG = "prior_cue_bind_2026_11_06"


def fact(name, ctx, value):
    return {"name": "jppfs_cor:" + name, "context": ctx, "unit": "JPY", "value": float(value)}


def contexts_for(facts):
    return {f["context"]: {"members": []} for f in facts}


def call(profile_name, sentence, number, unit, subj, elems, facts, member=None):
    """``sentence`` の中の ``number``(数の字面。最初に出る位置)について ``_direct_value_claim`` を呼ぶ。``b`` は本番の ``extract.iter_numbers`` と同じく単位を含む数の終わり。"""
    a = sentence.index(number)
    b = a + len(number) + len(unit)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None,
             "result": None, "recomputed": None}
    R._direct_value_claim(claim, sentence, a, b, 1, float(number.replace(",", "")), unit, None, subj, elems, member,
                          facts, contexts_for(facts), V.PROFILES[profile_name])
    return claim


def key(c):
    """P30E と P32E を比べる欄(結果・pointer・recomputed・reason・bound・form)。"""
    return (c["result"], c["pointer"], c["recomputed"], c["reason"], c["bound"], c["form"])


def ptr(ctx):
    return "xbrl:%s@%s" % (PTR, ctx)


#: 当期 5,000 千円・前期 999 千円の売上高。
F2 = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000)]


class ProfileTest(unittest.TestCase):
    def test_p32e_is_p30e_plus_exactly_the_one_flag(self):
        self.assertEqual(dataclasses.replace(V.P30E, name="P32E", **{FLAG: True}), V.P32E)
        self.assertIs(V.PROFILES["P32E"], V.P32E)
        self.assertEqual("P32E", V.P32E.name)

    def test_the_flag_is_true_only_in_p32e(self):
        self.assertTrue(getattr(V.P32E, FLAG))
        self.assertEqual(["P32E"], sorted(n for n, p in V.PROFILES.items() if getattr(p, FLAG)))
        for n in ("P30E", "P29E", "P29", "P28E", "P28", "P27E", "P27C", "P27", "P26", "P24", "P22", "P1"):
            self.assertFalse(getattr(V.PROFILES[n], FLAG), n)

    def test_the_flag_defaults_to_false(self):
        self.assertFalse(dataclasses.fields(V.Profile)[[f.name for f in dataclasses.fields(V.Profile)].index(FLAG)].default)

    def test_p31_and_p32_are_not_made(self):
        # P31 は規則 T の下書き(docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-03.md)に取り置く。P32 は作らない(封 §0-2 の 1)。
        self.assertNotIn("P31", V.PROFILES)
        self.assertNotIn("P31E", V.PROFILES)
        self.assertNotIn("P32", V.PROFILES)

    def test_the_default_profile_is_still_p27(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)

    def test_the_flag_field_sits_right_after_rounding_mixed(self):
        names = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(names.index("rounding_mixed_2026_11_04") + 1, names.index(FLAG))

    def test_the_flag_and_the_seal_are_named_in_the_engine(self):
        import inspect
        src = inspect.getsource(R._direct_value_claim)
        self.assertEqual(2, src.count(FLAG))
        self.assertEqual(2, src.count(SEAL))
        self.assertIn(SEAL, inspect.getsource(R._prior_cue_window_2026_11_06))


class WindowTest(unittest.TestCase):
    """窓の関数の字。「から」の枝を持たない。"""

    def w(self, s, number):
        return R._prior_cue_window_2026_11_06(s, s.index(number))

    def test_the_words_of_the_window(self):
        for head in ("前期", "前期は", "前期には", "前期の", "前期、", "前期末", "前連結会計年度", "前連結会計年度末の", "前事業年度は", "前事業年度末", "前年同期の"):
            self.assertTrue(self.w("売上高は" + head + "5,000千円", "5,000"), head)

    def test_the_paren_dou(self):
        s = "売上高は3,000千円(同5,000千円)です"
        self.assertTrue(R._prior_cue_window_2026_11_06(s, s.index("5,000")))
        s2 = "売上高は3,000千円(同 5,000千円)です"
        self.assertTrue(R._prior_cue_window_2026_11_06(s2, s2.index("5,000")))       # 「(同」の後の空白は許す(_PRIOR_PAREN_RE は \s*)
        s3 = "売上高は3,000千円(同じ5,000千円)です"
        self.assertFalse(R._prior_cue_window_2026_11_06(s3, s3.index("5,000")))

    def test_a_word_that_does_not_end_the_window_is_false(self):
        for head in ("前期比", "前期比2.9%増の", "前期より", "前期と比べ", ""):
            self.assertFalse(self.w("売上高は" + head + "5,000千円", "5,000"), head)

    def test_the_kara_branch_of_prior_cue_is_not_in_the_window(self):
        s = "売上高は5,000千円から999千円へ"
        a = s.index("5,000")
        b = a + len("5,000千円")       # b は単位を含む数の終わり(直後の 2 字が「から」)
        self.assertTrue(R._prior_cue(s, a, b))                         # C2 の _prior_cue は「から」の枝で真
        self.assertFalse(R._prior_cue_window_2026_11_06(s, a))         # PB の窓は偽

    def test_the_window_is_12_chars(self):
        s = "前期" + "あ" * 10 + "5,000千円"       # 「前期」が 12 字より前
        self.assertFalse(R._prior_cue_window_2026_11_06(s, s.index("5,000")))
        s = "前期の" + "5,000千円"
        self.assertTrue(R._prior_cue_window_2026_11_06(s, s.index("5,000")))
        s = "あ" * 20 + "前期の" + "5,000千円"
        self.assertTrue(R._prior_cue_window_2026_11_06(s, s.index("5,000")))


class BlockATest(unittest.TestCase):
    """最初の枝の前の block A。前期の手がかりがある数は、Prior1Year の hit が無ければ CurrentYear の hit を外す。"""

    S = "売上高は前期の5,000千円です"

    def test_p30e_grounds_the_current_fact_but_p32e_names_the_prior_fact(self):
        """当たる例(封 §1 の 4): 「前期の」と書かれた数に当期の値が入っている。P30E は当期の fact に GROUNDED、P32E は前期の fact を名指して VALUE_MISMATCH。"""
        c30 = call("P30E", self.S, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual("GROUNDED", c30["result"])
        self.assertEqual(ptr(CUR), c30["pointer"])
        c32 = call("P32E", self.S, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual("VALUE_MISMATCH", c32["result"])
        self.assertEqual(ptr(PRI), c32["pointer"])
        self.assertEqual(999000.0, c32["recomputed"])
        self.assertEqual(REASON_VM, c32["reason"])
        self.assertTrue(c32["bound"])

    def test_a_value_that_matches_the_prior_fact_is_grounded_in_the_prior_fact_in_both(self):
        """当たらない例: 前期の fact に値が合う「前期 999」は今までどおり前期の fact に GROUNDED(旗が真でも)。"""
        for p in ("P30E", "P32E"):
            c = call(p, "売上高は前期の999千円です", "999", "千円", "売上高", [NAME], F2)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual(ptr(PRI), c["pointer"], p)
            self.assertEqual(999000.0, c["recomputed"], p)

    def test_prior2year_hits_are_kept(self):
        """CurrentYear だけを外す。Prior2Year(経営指標の要約の 2 期前)の hit は残るので、そこに GROUNDED になる。"""
        facts = [fact("NetSales", CUR, 5000000), fact("NetSales", PRI, 999000), fact("NetSales", PRI2, 5000000)]
        c30 = call("P30E", self.S, "5,000", "千円", "売上高", [NAME], facts)
        c32 = call("P32E", self.S, "5,000", "千円", "売上高", [NAME], facts)
        self.assertEqual(ptr(CUR), c30["pointer"])
        self.assertEqual("GROUNDED", c32["result"])
        self.assertEqual(ptr(PRI2), c32["pointer"])

    def test_prior2year_only_hits_are_the_same_in_both(self):
        facts = [fact("NetSales", PRI, 999000), fact("NetSales", PRI2, 5000000)]
        self.assertEqual(key(call("P30E", self.S, "5,000", "千円", "売上高", [NAME], facts)),
                         key(call("P32E", self.S, "5,000", "千円", "売上高", [NAME], facts)))

    def test_the_prior_condition_is_about_hits_not_about_the_facts(self):
        """hits に Prior1Year が在れば CurrentYear は外さない。別の要素の Prior1Year の hit が在れば、要素が 2 つに分かれて ambiguous のまま
        (外すと 1 つに絞れて no_subject になる)。主語が無く、要素が 2 つ(NetSales の当期・OperatingIncome の前期が同じ値)。"""
        facts = [fact("NetSales", CUR, 5000000), fact("OperatingIncome", PRI, 5000000)]
        for p in ("P30E", "P32E"):
            c = call(p, "前期の5,000千円です", "5,000", "千円", None, [NAME, "OperatingIncome"], facts)
            self.assertEqual("ambiguous(elements)", c["reason"], p)
            self.assertIsNone(c["result"], p)

    def test_no_prior_fact_at_all_falls_through_to_the_last_branch(self):
        """前期の fact が無い要素の「前期の 5,000」: A が当期の hit を外し、B は前期の fact が無いので何もしない。従来の最後の枝(当期の fact を名指して VALUE_MISMATCH)に落ちる。
        P30E は当期の fact に GROUNDED だった行なので、旗が真のとき出力が変わる(封 §1 の字どおり。brief の「P30E と同じ」とは違う)。"""
        facts = [fact("NetSales", CUR, 5000000)]
        c30 = call("P30E", self.S, "5,000", "千円", "売上高", [NAME], facts)
        c32 = call("P32E", self.S, "5,000", "千円", "売上高", [NAME], facts)
        self.assertEqual(("GROUNDED", ptr(CUR)), (c30["result"], c30["pointer"]))
        self.assertEqual(("VALUE_MISMATCH", ptr(CUR), 5000000.0, REASON_VM), (c32["result"], c32["pointer"], c32["recomputed"], c32["reason"]))

    def test_without_a_subject_the_dropped_hit_ends_as_no_element(self):
        """主語が無い数: P30E は no_subject(結ばない)、P32E は当期の hit を外して no_element。どちらも結ばない(pointer なし)。"""
        c30 = call("P30E", "前期の5,000千円です", "5,000", "千円", None, [NAME], F2)
        c32 = call("P32E", "前期の5,000千円です", "5,000", "千円", None, [NAME], F2)
        self.assertEqual("no_subject", c30["reason"])
        self.assertEqual("no_element", c32["reason"])
        self.assertIsNone(c30["pointer"])
        self.assertIsNone(c32["pointer"])
        self.assertFalse(c32["bound"])


class BlockBTest(unittest.TestCase):
    """最後の枝の block B。増減の語(is_diff)があっても前期の fact を名指して VALUE_MISMATCH。"""

    S = "売上高は4,000千円(前期5,000千円)と減少"

    def test_a_diff_phrase_number_with_the_current_value_names_the_prior_fact(self):
        """当たる例(封 §1 の 4): 「…(前期50億円)と減少」の 50億 に当期の値。P30E は(導出の後の diff phrase の枝で)当期の fact に GROUNDED、P32E は前期の fact を名指す。"""
        c30 = call("P30E", self.S, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual(("GROUNDED", ptr(CUR)), (c30["result"], c30["pointer"]))
        c32 = call("P32E", self.S, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual("VALUE_MISMATCH", c32["result"])
        self.assertEqual(ptr(PRI), c32["pointer"])
        self.assertEqual(999000.0, c32["recomputed"])
        self.assertEqual(REASON_VM, c32["reason"])
        self.assertTrue(c32["bound"])
        self.assertEqual("direct_value", c32["form"])

    def test_the_prior_value_inside_the_parentheses_is_still_grounded(self):
        """当たらない例: 前期の fact に値が合う「(前期 999)」は、増減の語があっても前期の fact に GROUNDED(P30E と同じ)。"""
        s = "売上高は5,000千円(前期999千円)と減少"
        self.assertEqual(key(call("P30E", s, "999", "千円", "売上高", [NAME], F2)), key(call("P32E", s, "999", "千円", "売上高", [NAME], F2)))
        self.assertEqual(ptr(PRI), call("P32E", s, "999", "千円", "売上高", [NAME], F2)["pointer"])

    def test_a_number_that_matches_no_fact_is_named_to_the_prior_fact_in_p32e(self):
        """どの fact にも合わない「(前期 1,500)」: P30E は結ばない(reason no_same_value・pointer なし)。P32E は前期の fact を名指して VALUE_MISMATCH(窓の手がかりが真・増減の語つき)。"""
        s = "売上高は5,000千円(前期1,500千円)と減少"
        c30 = call("P30E", s, "1,500", "千円", "売上高", [NAME], F2)
        c32 = call("P32E", s, "1,500", "千円", "売上高", [NAME], F2)
        self.assertEqual(("no_same_value", None, None), (c30["reason"], c30["pointer"], c30["result"]))
        self.assertEqual(("VALUE_MISMATCH", ptr(PRI), 999000.0, REASON_VM), (c32["result"], c32["pointer"], c32["recomputed"], c32["reason"]))

    def test_b_works_before_the_segment_profit_stop(self):
        """B は F2′(枠が取れていないセグメント利益は全社の fact を名指さない)より前に効く(封 §2-2 の 4)。P30E は当期の fact に GROUNDED(F2′ まで行かない)、P32E は前期の fact を名指す。
        増減の語が無い数でも B が名指す(F1′ ではなく B)。"""
        c32 = call("P32E", "セグメント利益は前期の5,000千円です", "5,000", "千円", "セグメント利益", [NAME], F2)
        self.assertEqual(("VALUE_MISMATCH", ptr(PRI), 999000.0), (c32["result"], c32["pointer"], c32["recomputed"]))
        # 前期の手がかりが無ければ、旗が真でも F2′ が止める(当期の fact に落とさず no_element)
        c = call("P32E", "セグメント利益は5,000千円です", "5,000", "千円", "セグメント利益", [NAME], [fact("NetSales", CUR, 5000)])
        self.assertEqual("no_element", c["reason"])

    def test_b_comes_after_the_prior2_stop(self):
        """§1b の止め(前々期が無い「前連結会計年度は…」)は人間の決定で、B より先に効く(止めた行を名指しに戻さない)。P32E でも止まる。"""
        s = "売上高は前連結会計年度は5,000千円です"
        c30 = call("P30E", s, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual(ptr(CUR), c30["pointer"])       # P30E は当期の fact に GROUNDED(hits)
        c32 = call("P32E", s, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c32["reason"])
        self.assertIsNone(c32["pointer"])
        self.assertIsNone(c32["result"])

    def test_b_does_nothing_without_a_prior_fact(self):
        """Prior1Year の fact が無ければ B は何もしない(下へ)。当期の fact だけの要素では、最後の枝が当期の fact を名指す(上の A の試験と同じ)。"""
        c = call("P32E", self.S, "5,000", "千円", "売上高", [NAME], [fact("NetSales", CUR, 5000000)])
        self.assertEqual(ptr(CUR), c["pointer"])
        self.assertEqual("VALUE_MISMATCH", c["result"])

    def test_the_other_element_prior_fact_is_not_used(self):
        """B の fs は主語の要素の fact。別の要素の Prior1Year があっても、主語の要素に Prior1Year が無ければ名指さない。"""
        facts = [fact("NetSales", CUR, 5000000), fact("OperatingIncome", PRI, 5000000)]
        c = call("P32E", "売上高は前期の5,000千円です", "5,000", "千円", "売上高", [NAME], facts)
        self.assertEqual(ptr(CUR), c["pointer"])


class NotTouchedTest(unittest.TestCase):
    """当たらない例: 窓の手がかりが偽(「から」の枝だけ・前期比)の数は P30E と同じ出力。"""

    def test_a_kara_only_number_is_the_same_as_p30e(self):
        """「5,000 千円から売上高 999 千円を」の 5,000(「から」の枝だけ)。P32E は手がかり偽なので P30E と同じ(当期の fact に GROUNDED)。"""
        s = "売上高は5,000千円から売上高999千円を引く"
        c30 = call("P30E", s, "5,000", "千円", "売上高", [NAME], F2)
        c32 = call("P32E", s, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual(key(c30), key(c32))
        self.assertEqual(("GROUNDED", ptr(CUR)), (c32["result"], c32["pointer"]))

    def test_a_prior_ratio_number_is_the_same_as_p30e(self):
        """「前期比 2.9% 増の 5,000 千円」(窓の末尾が 比 でも 増の でも手がかりに当たらない)。"""
        s = "売上高は前期比2.9%増の5,000千円です"
        c30 = call("P30E", s, "5,000", "千円", "売上高", [NAME], F2)
        c32 = call("P32E", s, "5,000", "千円", "売上高", [NAME], F2)
        self.assertEqual(key(c30), key(c32))
        self.assertEqual(("GROUNDED", ptr(CUR)), (c32["result"], c32["pointer"]))

    def test_a_plain_current_number_is_the_same_as_p30e(self):
        for s in ("売上高は5,000千円となった", "売上高は5,000千円(前期999千円)となった"):
            self.assertEqual(key(call("P30E", s, "5,000", "千円", "売上高", [NAME], F2)), key(call("P32E", s, "5,000", "千円", "売上高", [NAME], F2)), s)


class FlagOffTest(unittest.TestCase):
    """旗が偽の profile(P30E 以前)は今までどおり。前期の手がかりがある数に当期の値が入っても当期の fact に GROUNDED。"""

    def test_p30e_and_before_are_unchanged_for_both_examples(self):
        for p in ("P30E", "P29E", "P29", "P28E", "P28", "P27E", "P27", "P26", "P25", "P24", "P23", "P22"):
            a = call(p, "売上高は前期の5,000千円です", "5,000", "千円", "売上高", [NAME], F2)
            self.assertEqual(("GROUNDED", ptr(CUR)), (a["result"], a["pointer"]), p)
            b = call(p, "売上高は4,000千円(前期5,000千円)と減少", "5,000", "千円", "売上高", [NAME], F2)
            self.assertEqual(("GROUNDED", ptr(CUR)), (b["result"], b["pointer"]), p)

    def test_a_p32e_with_the_flag_turned_off_is_p30e(self):
        off = dataclasses.replace(V.P32E, name="P32E_OFF", **{FLAG: False})
        V.PROFILES["P32E_OFF"] = off
        try:
            for s, n in (("売上高は前期の5,000千円です", "5,000"), ("売上高は4,000千円(前期5,000千円)と減少", "5,000"), ("売上高は前連結会計年度は5,000千円です", "5,000")):
                self.assertEqual(key(call("P30E", s, n, "千円", "売上高", [NAME], F2)), key(call("P32E_OFF", s, n, "千円", "売上高", [NAME], F2)), s)
        finally:
            del V.PROFILES["P32E_OFF"]

    def test_p32e_reads_the_flag_only_through_the_profile(self):
        """profile が None のとき(旗の getattr の既定)は従来どおり。"""
        a = "売上高は前期の5,000千円です".index("5,000")
        claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
        R._direct_value_claim(claim, "売上高は前期の5,000千円です", a, a + 7, 1, 5000.0, "千円", None, "売上高", [NAME], None, F2, contexts_for(F2), None)
        self.assertEqual(ptr(CUR), claim["pointer"])


if __name__ == "__main__":
    unittest.main()
