# -*- coding: utf-8 -*-
"""P22(期を縛る直し)の試験。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md §1。

P22 = P21 + 旗 ``period_bind``。旗が真のとき、``recipes._direct_value_claim`` の最初の枝は、前期の手がかり
(``_prior_cue`` = 数の直前 12 字・``_prior_cue_clause`` = 同じ節の「前期は」等)が**無い**数について、
値が合っても ``Prior1Year`` の fact を候補(hits)から外す。当期の hit が残ればそれに結ぶ(従来どおり)。残らなければ
値の一致なしとして後続の枝(導出 a-b → 最後の枝)に落ちる。**各挙動について「P22 で効く」と「P21 では従来どおり」を対にして留める。**

合成の instance(facts と contexts を直接組む)で ``_direct_value_claim`` を呼ぶ。通信しない。
"""
import dataclasses
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
NAME = "NetSales"
PTR = "jppfs_cor:NetSales"


def fact(name, ctx, value):
    return {"name": "jppfs_cor:" + name, "context": ctx, "unit": "JPY", "value": float(value)}


def contexts_for(facts):
    return {f["context"]: {"members": []} for f in facts}


def call(profile_name, sentence, number, unit, subj, elems, facts, member=None):
    """``sentence`` の中の ``number``(数の字面)について ``_direct_value_claim`` を呼ぶ。"""
    a = sentence.index(number)
    b = a + len(number)
    claim = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None,
             "result": None, "recomputed": None}
    R._direct_value_claim(claim, sentence, a, b, 1, float(number.replace(",", "")), unit, None, subj, elems, member,
                          facts, contexts_for(facts), V.PROFILES[profile_name])
    return claim


def sales(cur, prior):
    return [fact("NetSales", CUR, cur), fact("NetSales", PRI, prior)]


class FlagShapeTest(unittest.TestCase):
    def test_p22_is_p21_plus_exactly_the_one_flag(self):
        self.assertEqual(dataclasses.replace(V.P21, name="P22", period_bind=True), V.P22)
        self.assertIs(V.PROFILES["P22"], V.P22)
        self.assertFalse(V.P21.period_bind)

    def test_only_p22_has_the_flag_on(self):
        self.assertEqual(["P22"], sorted(n for n, p in V.PROFILES.items() if p.period_bind))

    def test_the_default_profile_stays_p21_in_step_1(self):
        """段 1 では既定にしない(封 §1)。段 2(人間の承認の後)で P22 にする。"""
        self.assertEqual("P21", V.DEFAULT_PROFILE)


class WithoutCueTest(unittest.TestCase):
    """手がかりが無い数は、前期の fact にだけ値が合っても GROUNDED にしない。"""

    S = "売上高は999千円となった。"

    def test_a_prior_only_match_is_not_grounded_in_p22(self):
        c = call("P22", self.S, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
        self.assertNotEqual("GROUNDED", c["result"])
        self.assertEqual("VALUE_MISMATCH", c["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, CUR), c["pointer"])       # 当期の fact を名指して値が違うと言う
        self.assertEqual(5000000.0, c["recomputed"])

    def test_p21_still_grounds_the_prior_year_fact(self):
        """旗が効くのは P22 だけ。P21 は従来どおり前期の fact で GROUNDED(穴 B の原因)。"""
        c = call("P21", self.S, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"])

    def test_every_profile_before_p22_keeps_grounding_the_prior_fact(self):
        for name, p in V.PROFILES.items():
            if name == "P22":
                continue
            c = call(name, self.S, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
            self.assertEqual("GROUNDED", c["result"], name)
            self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"], name)

    def test_the_current_year_match_is_kept_when_both_periods_match(self):
        """当期にも合うなら当期に結ぶ。前期の fact を先に並べても(P21 は先頭 = 前期になる)P22 は当期。"""
        facts = [fact("NetSales", PRI, 999000), fact("NetSales", CUR, 999000)]
        c21 = call("P21", self.S, "999", "千円", "売上高", [NAME], facts)
        c22 = call("P22", self.S, "999", "千円", "売上高", [NAME], facts)
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c21["pointer"])
        self.assertEqual("GROUNDED", c22["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, CUR), c22["pointer"])

    def test_a_current_only_match_is_unchanged(self):
        for p in ("P21", "P22"):
            c = call(p, "売上高は5,000千円となった。", "5,000", "千円", "売上高", [NAME], sales(5000000, 7000000))
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:%s@%s" % (PTR, CUR), c["pointer"], p)

    def test_a_prior_only_match_falls_to_the_derived_difference(self):
        """前期の hit を外すと、後続の枝(導出 a-b)に落ちる。当期 2,000 - 前期 1,000 = 1,000 が言いたい数なら GROUNDED(導出)。"""
        facts = sales(2000000, 1000000)
        c21 = call("P21", "売上高は1,000千円となった。", "1,000", "千円", "売上高", [NAME], facts)
        c22 = call("P22", "売上高は1,000千円となった。", "1,000", "千円", "売上高", [NAME], facts)
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c21["pointer"])
        self.assertEqual("direct_value", c21["form"])
        self.assertEqual("GROUNDED", c22["result"])
        self.assertEqual("derived_value", c22["form"])
        self.assertEqual(["xbrl:%s@%s" % (PTR, CUR), "xbrl:%s@%s" % (PTR, PRI), "formula:a-b"], c22["pointer"])


class WithCueTest(unittest.TestCase):
    """前期の手がかりがあれば C2 のまま(Prior1Year の fact に結ぶ)。"""

    def test_cue_right_before_the_number(self):
        for p in ("P21", "P22"):
            c = call(p, "売上高は、前期は999千円となった。", "999", "千円", "売上高", [NAME], sales(5000000, 999000))
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"], p)

    def test_paren_dou_cue(self):
        for p in ("P21", "P22"):
            c = call(p, "売上高は5,000千円(同999千円)となった。", "999", "千円", "売上高", [NAME], sales(5000000, 999000))
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"], p)

    def test_cue_in_the_same_clause(self):
        """数の直前 12 字には無いが、同じ節に「前期は」が在る(_prior_cue_clause)。"""
        s = "前期は売上高が999千円となった。"
        a = s.index("999")
        self.assertFalse(R._prior_cue(s, a, a + 3))
        self.assertTrue(R._prior_cue_clause(s, a))
        c22 = call("P22", s, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
        self.assertEqual("GROUNDED", c22["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c22["pointer"])

    def test_after_a_comma_the_clause_cue_does_not_reach(self):
        """読点より前の「前期は」は別の節。手がかりなし = P22 は前期の fact に結ばない。"""
        s = "前期は減収となったが、売上高が999千円となった。"
        a = s.index("999")
        self.assertFalse(R._prior_cue_clause(s, a))
        c22 = call("P22", s, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
        self.assertEqual("VALUE_MISMATCH", c22["result"])
        self.assertEqual("xbrl:%s@%s" % (PTR, CUR), c22["pointer"])

    def test_the_ratio_to_prior_period_is_a_current_period_claim(self):
        """「前期比」は当期の主張(末尾が 比)。手がかりにならない = P22 は前期の fact に結ばない。"""
        s = "売上高は前期比999千円となった。"
        a = s.index("999")
        self.assertFalse(R._prior_cue(s, a, a + 3))
        c22 = call("P22", s, "999", "千円", "売上高", [NAME], sales(5000000, 999000))
        self.assertNotEqual("GROUNDED", c22["result"])

    def test_cue_with_only_the_prior_fact_matching_keeps_c2_order(self):
        """手がかりあり + 当期にも合う: C2 の並べ替えで前期が先(P22 でも不変)。"""
        facts = [fact("NetSales", CUR, 999000), fact("NetSales", PRI, 999000)]
        c = call("P22", "売上高は、前期は999千円となった。", "999", "千円", "売上高", [NAME], facts)
        self.assertEqual("xbrl:%s@%s" % (PTR, PRI), c["pointer"])


class NoSubjectKeptTest(unittest.TestCase):
    """案ア(2026-10-08 の人間の決定): 主語が取れない数は束縛しない。P22 でも no_subject のまま。"""

    def test_no_subject_stays_unbound_when_the_current_year_matches(self):
        facts = sales(999000, 7000000)
        for p in ("P21", "P22"):
            c = call(p, "999千円となった。", "999", "千円", None, [], facts)
            self.assertEqual("no_subject", c["reason"], p)
            self.assertIsNone(c["pointer"], p)
            self.assertFalse(c["bound"], p)
            self.assertEqual("UNVERIFIABLE", R._state_of(c["reason"], c["result"]), p)

    def test_no_subject_never_binds_a_prior_year_fact_in_p22(self):
        c = call("P22", "999千円となった。", "999", "千円", None, [], sales(5000000, 999000))
        self.assertIsNone(c["pointer"])
        self.assertFalse(c["bound"])
        self.assertNotEqual("GROUNDED", c["result"])


    def test_no_subject_prior_only_match_keeps_reason_and_state_of_p21(self):
        """2026-10-20 独立監査の指摘: 主語なし + Prior1Year の fact にだけ合う数は、P22 でも P21 と reason・state まで同一
        (単一の家族 -> no_subject、複数の家族 -> ambiguous(elements)。どちらも UNVERIFIABLE)。"""
        one = sales(5000000, 999000)
        two = one + [fact("OperatingIncome", "Prior1YearDuration", 999000)]
        for facts, want in ((one, "no_subject"), (two, "ambiguous(elements)")):
            c21 = call("P21", "999千円となった。", "999", "千円", None, [], facts)
            c22 = call("P22", "999千円となった。", "999", "千円", None, [], facts)
            self.assertEqual(want, c21["reason"])
            self.assertEqual(c21, c22)
            self.assertEqual("UNVERIFIABLE", R._state_of(c22["reason"], c22["result"]))

    def test_no_subject_without_any_match_is_also_the_same(self):
        facts = sales(5000000, 7000000)
        c21 = call("P21", "999千円となった。", "999", "千円", None, [], facts)
        c22 = call("P22", "999千円となった。", "999", "千円", None, [], facts)
        self.assertEqual(c21, c22)


class PriorTwoYearsTest(unittest.TestCase):
    """前々期(Prior2Year)の fact は外さない。P22 が外すのは Prior1Year だけ(未測定の穴: 前々期の値への置き換えは P22 でも通る)。"""

    def test_a_prior2_only_match_stays_grounded_in_p22(self):
        facts = sales(5000000, 7000000) + [fact("NetSales", "Prior2YearDuration", 999000)]
        for p in ("P21", "P22"):
            c = call(p, "売上高は999千円となった。", "999", "千円", "売上高", [NAME], facts)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("xbrl:%s@Prior2YearDuration" % PTR, c["pointer"], p)

    def test_prior1_is_dropped_but_prior2_is_kept_when_both_match(self):
        facts = [fact("NetSales", "Prior1YearDuration", 999000), fact("NetSales", "Prior2YearDuration", 999000), fact("NetSales", CUR, 5000000)]
        c = call("P22", "売上高は999千円となった。", "999", "千円", "売上高", [NAME], facts)
        self.assertEqual("xbrl:%s@Prior2YearDuration" % PTR, c["pointer"])


class PriorYearStopIsKeptTest(unittest.TestCase):
    """§1b の止め(前々期が無い「前連結会計年度は…」)は人間の決定。P22 でも同じ 2 行(test_recipes_p21 と同じ標本)。"""

    def test_p22_keeps_the_stop_for_a_prior_year_phrase_with_a_prior_fact(self):
        facts = [fact("NetSales", "CurrentYearDuration", 5000000), fact("NetSales", "Prior1YearDuration", 7000000)]
        c = call("P22", "売上高は、前連結会計年度は999千円となった。", "999", "千円", "売上高", ["NetSales"], facts)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(c["reason"], c["result"]))

    def test_p22_keeps_the_stop_for_a_prior_year_difference_on_a_balance(self):
        facts = [fact("CashAndDeposits", "CurrentYearInstant", 10000000), fact("CashAndDeposits", "Prior1YearInstant", 8000000)]
        c = call("P22", "現金及び預金は、前連結会計年度は500千円増加した。", "500", "千円", "現金及び預金", ["CashAndDeposits"], facts)
        self.assertEqual("no_element(no prior2 for prior-year diff)", c["reason"])
        self.assertIsNone(c["pointer"])
        self.assertEqual("direct_value", c["form"])


class CommaAfterPriorYearPhraseTest(unittest.TestCase):
    """既知の端(2026-10-20 独立監査): 「前連結会計年度は、9,709千円」(語と数の間に読点)は手がかりの規則の外。
    P21 は前期の fact に GROUNDED、P22 は前期の fact を外して §1b の止め(no_element(no prior2 for prior-year diff))に落ちる
    = 今回の直しが §1b の止めへ新しい行を送る。ここは挙動の記録で、良し悪しの判断ではない。"""

    def test_p21_grounds_it_and_p22_sends_it_to_the_stop(self):
        facts = [fact("OperatingIncome", CUR, 5000000), fact("OperatingIncome", PRI, -9709000)]
        s = "営業利益は、前連結会計年度は、9,709千円となった。"
        a = s.index("9,709")
        self.assertFalse(R._prior_cue(s, a, a + 5))
        self.assertFalse(R._prior_cue_clause(s, a))
        out = {}
        for p in ("P21", "P22"):
            c = {"reason": None, "bound": False, "form": "direct_value", "pointer": None, "value": None, "result": None, "recomputed": None}
            R._direct_value_claim(c, s, a, a + 5, -1, 9709.0, "千円", None, "営業利益", ["OperatingIncome"], None, facts, contexts_for(facts), V.PROFILES[p])
            out[p] = c
        self.assertEqual("GROUNDED", out["P21"]["result"])
        self.assertEqual("xbrl:jppfs_cor:OperatingIncome@%s" % PRI, out["P21"]["pointer"])
        self.assertEqual("no_element(no prior2 for prior-year diff)", out["P22"]["reason"])
        self.assertIsNone(out["P22"]["pointer"])


class LastBranchKeptTest(unittest.TestCase):
    """P21 の最後の枝(F1′・F2′・F3b)は P22 でも効く(P22 は P21 の上)。"""

    def test_f3b_balance_pair_still_applies(self):
        facts = [fact("CashAndDeposits", "CurrentYearInstant", 10000000), fact("CashAndDeposits", "Prior1YearInstant", 8000000)]
        c = call("P22", "現金及び預金は、前期末に比べて500千円増加した。", "500", "千円", "現金及び預金", ["CashAndDeposits"], facts)
        self.assertEqual("derived_value", c["form"])
        self.assertEqual(["xbrl:jppfs_cor:CashAndDeposits@CurrentYearInstant",
                          "xbrl:jppfs_cor:CashAndDeposits@Prior1YearInstant", "formula:a-b"], c["pointer"])

    def test_a_decrease_equal_to_the_prior_balance_is_no_longer_grounded(self):
        """代価の型: 「短期借入金が 200 千円減少」(前期残高 200 → 当期は fact 無し)。減少額が前期の残高と偶然一致する。
        P21 は「増減の語はあるが値が一致する fact に結ぶ」枝で前期の残高に GROUNDED、P22 はその前期の hit を外して止める
        (当期の fact が無いので最後の枝は no_element = POINTER_NOT_FOUND)。"""
        facts = [fact("ShortTermLoans", "Prior1YearInstant", 200000)]
        s = "短期借入金が200千円減少した。"
        c21 = call("P21", s, "200", "千円", "短期借入金", ["ShortTermLoans"], facts)
        c22 = call("P22", s, "200", "千円", "短期借入金", ["ShortTermLoans"], facts)
        self.assertEqual("GROUNDED", c21["result"])
        self.assertEqual("xbrl:jppfs_cor:ShortTermLoans@Prior1YearInstant", c21["pointer"])
        self.assertEqual("diff phrase but value matched a fact", c21["reason"])
        self.assertIsNone(c22["result"])
        self.assertIsNone(c22["pointer"])
        self.assertEqual("no_element", c22["reason"])
        self.assertEqual("POINTER_NOT_FOUND", R._state_of(c22["reason"], c22["result"]))

    def test_a_decrease_with_the_pair_is_still_grounded_by_the_derived_difference(self):
        """当期の fact も在れば、減少額は残高の対(当期 - 前期)に GROUNDED で結ぶ(P21 も P22 も同じ。止めない)。"""
        facts = [fact("ShortTermLoans", "CurrentYearInstant", 0), fact("ShortTermLoans", "Prior1YearInstant", 200000)]
        for p in ("P21", "P22"):
            c = call(p, "短期借入金が200千円減少した。", "200", "千円", "短期借入金", ["ShortTermLoans"], facts)
            self.assertEqual("GROUNDED", c["result"], p)
            self.assertEqual("derived_value", c["form"], p)


if __name__ == "__main__":
    unittest.main()
