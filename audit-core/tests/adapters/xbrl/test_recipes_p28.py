# -*- coding: utf-8 -*-
"""P28(= P27 + O。「その他」の主語の結び直し)の試験。封 docs/XBRL_OTHER_SUBJECT_ENGINE_SEAL_2026-11-02.md §1・§2-1。

旗 ``other_subject_2026_11_02`` が真の profile は P28 だけ。直前が「その他」「その他の○○」の円族の数で、engine が GROUNDED にしなかった行について、
書類の全部の ``Other…`` 要素(同じ期・member なし・JPY)のうち engine の帯の中の fact がちょうど 1 つならそれに結ぶ(R0)。
**この file の例の字と数は全部作り物**(封 §1 の例のとおり)。各条件について「当たる例」「当たらない例」(と代価の「当たってしまう例」)を置く。
変異(正規表現の {0,8}・TRAIL の読点・hops・候補の条件 (a)〜(d)・ちょうど 1 つ・GROUNDED を触らない条件・旗の既定)で赤くなることは、
便の結果の文書(docs/XBRL_OTHER_SUBJECT_ENGINE_RESULT_2026-11-02.md)の変異の節に書いた。通信しない。
"""
import dataclasses
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

from .test_recipes_p24 import contexts_for, fact, num_claims

CUR = "CurrentYearDuration"
CUR_I = "CurrentYearInstant"
PRI = "Prior1YearDuration"
KEY = "other_subject_2026_11_02"
P28_OFF = dataclasses.replace(V.P28, name="P28_OFF", other_subject_2026_11_02=False)
NS = fact("NetSales", CUR, 820000000)


def claims(p, sentence, facts):
    return num_claims(p, sentence, facts, contexts_for(facts))


def pick(cs, value):
    got = [c for c in cs if abs(c["value"] - value) < 1e-6 * max(1.0, abs(value)) or abs(c["value"] * (c.get("unit_scale") or 1.0) - value) < 1e-6 * max(1.0, abs(value))]
    assert len(got) == 1, [(c["id"], c["value"], c["unit"]) for c in cs]
    return got[0]


def shape_at(sentence, needle, nth=0):
    """文の中の ``needle`` の開始位置で形を求める(nth 番目の出現)。"""
    i = -1
    for _ in range(nth + 1):
        i = sentence.index(needle, i + 1)
    return R._other_subject_shape_2026_11_02(V.P28, sentence, i)


# ====================================================================================================
class ProfileShapeTest(unittest.TestCase):
    def test_p28_is_p27_plus_exactly_the_other_flag(self):
        self.assertEqual(dataclasses.replace(V.P27, name="P28", other_subject_2026_11_02=True), V.P28)
        self.assertIs(V.PROFILES["P28"], V.P28)

    def test_only_p28_has_the_flag(self):
        # 2026-11-03: 旗が真の profile は P28 と P28E(= P27E + O。封 docs/XBRL_P28E_SEAL_2026-11-03.md §1)の 2 つ。ほかは偽。
        self.assertEqual(["P28", "P28E"], sorted(n for n, p in V.PROFILES.items() if p.other_subject_2026_11_02))
        self.assertFalse(V.P27.other_subject_2026_11_02)
        self.assertFalse(V.P27E.other_subject_2026_11_02)
        self.assertFalse(V.P27C.other_subject_2026_11_02)

    def test_default_is_still_p27_and_flag_defaults_false(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)
        fields = {f.name: f for f in dataclasses.fields(V.Profile)}
        self.assertIs(False, fields[KEY].default)

    def test_flag_position_after_p27_flags_before_unnamed_candidate(self):
        order = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(order.index("future_period_2026_10_27") + 1, order.index(KEY))
        self.assertEqual(order.index(KEY) + 1, order.index("unnamed_candidate_2026_10_29"))
        self.assertEqual("unnamed_candidate_2026_10_29", order[-1])

    def test_flag_off_p28_equals_p27_except_name(self):
        self.assertEqual(dataclasses.replace(V.P27, name="P28"), dataclasses.replace(P28_OFF, name="P28"))

    def test_constants_are_the_sealed_strings(self):
        self.assertEqual(":" + ":" + "、はがをでに " + "　", R.OTHER_SUBJECT_TRAIL_2026_11_02)
        self.assertEqual("その他(の[^、。::()()\\s]{0,8})?$", R.OTHER_SUBJECT_RE_2026_11_02.pattern)
        self.assertEqual(5, R.OTHER_SUBJECT_HOPS_2026_11_02)
        for ch in R.OTHER_SUBJECT_TRAIL_2026_11_02[:2] + R.OTHER_SUBJECT_RE_2026_11_02.pattern:
            if ch in ":()":
                self.assertLess(ord(ch), 128)


# ====================================================================================================
class ShapeTest(unittest.TestCase):
    def test_hit_other_after_comma(self):
        self.assertEqual((True, False), shape_at("受取配当金12百万円、その他3百万円", "3百万円"))

    def test_hit_other_noun_and_dou_chain(self):
        s = "その他の流動資産45百万円(同41百万円)"
        self.assertEqual((True, False), shape_at(s, "45百万円"))
        self.assertEqual((True, True), shape_at(s, "41百万円"))

    def test_hit_leading_dash(self):
        self.assertEqual((True, False), shape_at("- その他の包括利益7百万円", "7百万円"))

    def test_hit_with_particle_before_number(self):
        self.assertEqual((True, False), shape_at("営業外収益のその他は3百万円", "3百万円"))

    def test_miss_plain_subject(self):
        self.assertEqual((False, False), shape_at("売上高123百万円", "123百万円"))

    def test_miss_other_noun_too_long(self):
        # 「その他」の後に「の」が無く 9 字以上 → 偽(限界。measure と同じ)
        self.assertEqual((False, False), shape_at("その他有価証券評価差額金9百万円", "9百万円"))

    def test_miss_quoted_other(self):
        self.assertEqual((False, False), shape_at("『その他』の販管費5百万円", "5百万円"))

    def test_miss_prior_parenthesis_not_dou(self):
        # 「(前期」は「(同」でない(限界)
        self.assertEqual((False, False), shape_at("その他の資産10百万円(前期3百万円)", "3百万円"))

    def test_limit_noun_eight_chars_ok_nine_not(self):
        self.assertTrue(shape_at("その他の" + "あ" * 8 + "5百万円", "5百万円")[0])
        self.assertFalse(shape_at("その他の" + "あ" * 9 + "5百万円", "5百万円")[0])

    def test_trailing_chars_are_skipped(self):
        for t in ("、", "は", "が", "を", "で", "に", " ", "　", ":"):
            self.assertTrue(shape_at("その他" + t + "5百万円", "5百万円")[0], repr(t))

    def test_dou_chain_without_previous_number_is_false_prior(self):
        self.assertEqual((False, True), shape_at("(同5百万円", "5百万円"))

    def test_dou_chain_hops_limit(self):
        s = "その他の資産10百万円" + "".join("(同%d百万円)" % n for n in (9, 8, 7, 6, 5, 4))
        # 5 番目の「(同」(5)は 5 回で先頭の 10 に届く。6 番目(4)は 6 回要るので届かず偽。
        self.assertEqual((True, True), shape_at(s, "5百万円"))
        self.assertEqual((False, True), shape_at(s, "4百万円"))

    def test_dou_chain_skips_to_last_number_before(self):
        s = "売上高820百万円、その他の資産3百万円(同2百万円)"
        self.assertEqual((True, True), shape_at(s, "2百万円"))


# ====================================================================================================
class DecideTest(unittest.TestCase):
    def test_hit_binds_current_period_other_element(self):
        fs = [NS, fact("OtherNOI", CUR, 3000000)]
        s = "売上高は820百万円、その他は3百万円でした。"
        c27 = pick(claims("P27", s, fs), 3000000)
        self.assertNotEqual("GROUNDED", c27["result"])
        c = pick(claims("P28", s, fs), 3000000)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c["pointer"])
        self.assertTrue(c["bound"])
        self.assertEqual(3000000.0, c["recomputed"])
        self.assertTrue(c.get("match"))
        self.assertIsNone(c["reason"])
        self.assertEqual({"前期": False, "候補": 1, "決まった": True}, c[KEY])

    def test_hit_prior_period_for_dou(self):
        fs = [NS, fact("OtherNOI", CUR, 3000000), fact("OtherNOI", PRI, 2000000)]
        cs = claims("P28", "売上高は820百万円、その他の流動資産は3百万円(同2百万円)でした。", fs)
        c2 = pick(cs, 2000000)
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + PRI, c2["pointer"])
        self.assertEqual({"前期": True, "候補": 1, "決まった": True}, c2[KEY])
        c3 = pick(cs, 3000000)
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c3["pointer"])

    def test_pointer_str_form_same_as_direct_value_claim(self):
        fs = [NS, fact("OtherCA", CUR_I, 4000000)]
        c = pick(claims("P28", "売上高は820百万円、その他は4百万円でした。", fs), 4000000)
        self.assertEqual("xbrl:jppfs_cor:OtherCA@" + CUR_I, c["pointer"])

    def test_two_candidates_keep_engine_verdict(self):
        fs = [NS, fact("OtherNOI", CUR, 3000000), fact("OtherNOE", CUR, 3000000)]
        s = "売上高は820百万円、その他は3百万円でした。"
        c27 = pick(claims("P27", s, fs), 3000000)
        c = pick(claims("P28", s, fs), 3000000)
        self.assertEqual({"前期": False, "候補": 2, "決まった": False}, c[KEY])
        self.assertEqual(self.engine_fields(c27), self.engine_fields(c))

    def test_zero_candidates_keep_engine_verdict(self):
        fs = [NS, fact("OtherNOI", CUR, 9000000)]
        s = "売上高は820百万円、投資その他の資産は88百万円でした。"
        c27 = pick(claims("P27", s, fs), 88000000)
        c = pick(claims("P28", s, fs), 88000000)
        self.assertEqual({"前期": False, "候補": 0, "決まった": False}, c[KEY])
        self.assertEqual(self.engine_fields(c27), self.engine_fields(c))

    def test_engine_grounded_row_is_not_touched(self):
        # 売上高の 820 百万円は engine 自身が NetSales で GROUNDED にする。Other… に同じ値が在っても結び直さない。
        fs = [NS, fact("OtherNOI", CUR, 820000000)]
        s = "売上高は820百万円、その他は820百万円でした。"
        cs27 = claims("P27", s, fs)
        cs = claims("P28", s, fs)
        self.assertEqual(3, len(cs27) + 1)   # 数は 2 つ
        for a, b in zip(cs27, cs):
            self.assertEqual("GROUNDED", b["result"])
            self.assertEqual(self.engine_fields(a), self.engine_fields(b))
        other_row = cs[1]
        self.assertEqual("xbrl:jppfs_cor:NetSales@" + CUR, other_row["pointer"])
        self.assertEqual({"前期": False, "候補": 1, "決まった": False}, other_row[KEY])   # 候補の数は engine が GROUNDED にした行にも数える。決まったは偽

    def test_costly_false_hit_is_documented(self):
        # 代価: 「その他の包括利益累計額」(正しい要素は別)の値が偶然 OtherCA の fact と一致し、他に無いと OtherCA に結ぶ。
        fs = [NS, fact("OtherCA", CUR_I, 15000000)]
        c = pick(claims("P28", "売上高は820百万円、その他の包括利益累計額は15百万円でした。", fs), 15000000)
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:jppfs_cor:OtherCA@" + CUR_I, c["pointer"])

    def test_no_subject_row_is_also_bound_per_seal_text(self):
        # 封 §2-2 の 1: subj を条件に入れない(封の字)。主語なしの行にも当たりうる。数は記録に書く。
        fs = [fact("OtherNOI", CUR, 3000000)]
        s = "その他は3百万円でした。"
        c27 = pick(claims("P27", s, fs), 3000000)
        self.assertIsNone(c27["subject"])
        self.assertNotEqual("GROUNDED", c27["result"])
        c = pick(claims("P28", s, fs), 3000000)
        self.assertEqual("GROUNDED", c["result"])

    # --- 候補の条件 (a)〜(d)。各条件を外すと候補が 2 になって結べなくなる、を 1 つずつ。
    def decided_only_noi(self, extra):
        fs = [NS, fact("OtherNOI", CUR, 3000000)] + extra
        c = pick(claims("P28", "売上高は820百万円、その他は3百万円でした。", fs), 3000000)
        self.assertEqual("GROUNDED", c["result"], c[KEY])
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c["pointer"])
        self.assertEqual(1, c[KEY]["候補"])

    def test_cond_a_name_must_start_with_other(self):
        self.decided_only_noi([fact("ProfitOtherNet", CUR, 3000000)])

    def test_cond_b_unit_must_be_jpy(self):
        self.decided_only_noi([fact("OtherNOE", CUR, 3000000, unit="USD")])
        self.decided_only_noi([fact("OtherNOE", CUR, 3000000, unit="pure")])

    def test_cond_c_period_must_match(self):
        self.decided_only_noi([fact("OtherNOE", PRI, 3000000)])
        self.decided_only_noi([fact("OtherNOE", "Prior2YearDuration", 3000000)])

    def test_cond_c_member_context_excluded(self):
        self.decided_only_noi([fact("OtherNOE", CUR + "_ConsolidatedMember", 3000000)])

    def test_cond_c_prior_uses_prior_only(self):
        fs = [NS, fact("OtherNOI", CUR, 2000000)]
        c = pick(claims("P28", "売上高は820百万円、その他の資産は3百万円(同2百万円)でした。", fs), 2000000)
        self.assertEqual({"前期": True, "候補": 0, "決まった": False}, c[KEY])
        self.assertNotEqual("GROUNDED", c["result"])

    def test_cond_d_value_must_match_in_band(self):
        self.decided_only_noi([fact("OtherNOE", CUR, 4500000), fact("OtherCA", CUR, 30000000)])

    def test_cond_d_band_is_engine_band(self):
        # 3.2 百万円 は 0.1 百万円の桁。0.05 以内は合う、0.2 離れたら合わない。
        s = "売上高は820百万円、その他は3.2百万円でした。"
        near = pick(claims("P28", s, [NS, fact("OtherNOI", CUR, 3230000)]), 3200000)
        self.assertEqual("GROUNDED", near["result"])
        far = pick(claims("P28", s, [NS, fact("OtherNOI", CUR, 3400000)]), 3200000)
        self.assertNotEqual("GROUNDED", far["result"])
        self.assertEqual(0, far[KEY]["候補"])

    def test_non_money_unit_is_not_handled(self):
        cs = claims("P28", "その他は3%でした。", [fact("OtherNOI", CUR, 3)])
        for c in cs:
            self.assertNotIn(KEY, c)

    # --- 作りから: 形が偽の行は P27 と同じ。旗が偽なら P27 と同じ。
    SENTENCES = ["売上高は820百万円、営業利益は90百万円でした。", "売上高は820百万円(前期800百万円)。", "その他有価証券評価差額金は9百万円でした。",
                 "売上高は820百万円、その他は3百万円(同2百万円)でした。"]
    FACTS = [NS, fact("OperatingIncome", CUR, 90000000), fact("OtherNOI", CUR, 3000000), fact("OtherNOI", PRI, 2000000)]

    def test_flag_off_is_identical_to_p27(self):
        for s in self.SENTENCES:
            self.assertEqual(claims("P27", s, self.FACTS), claims(P28_OFF, s, self.FACTS), s)

    def test_no_shape_rows_are_identical_to_p27_and_have_no_key(self):
        for s in self.SENTENCES[:3]:
            a, b = claims("P27", s, self.FACTS), claims("P28", s, self.FACTS)
            self.assertEqual(a, b, s)
            for c in b:
                self.assertNotIn(KEY, c)

    @staticmethod
    def engine_fields(c):
        return dict((k, v) for k, v in c.items() if k != KEY)

    def test_provenance_carries_the_key(self):
        fs = [NS, fact("OtherNOI", CUR, 3000000)]
        raw = pick(claims("P28", "売上高は820百万円、その他は3百万円でした。", fs), 3000000)
        r = R.claim_to_recipe(raw, "num")
        self.assertEqual({"前期": False, "候補": 1, "決まった": True}, r.claim.provenance[KEY])
        raw2 = pick(claims("P27", "売上高は820百万円、営業利益は3百万円でした。", fs), 3000000)
        self.assertNotIn(KEY, R.claim_to_recipe(raw2, "num").claim.provenance)


# ====================================================================================================
# P28E(= P27E + O)。封 docs/XBRL_P28E_SEAL_2026-11-03.md §1・§2-1。engine は変えない(旗は新しくない)。独立監査の注意 3 本(符号・stale keys・mag_trunc)の振る舞いの試験。
# 作り物の facts。変異: 符号に敏感にする / 消去(_P27_STALE_KEYS の pop)を外す / mag_trunc を偽に固定する、で赤くなる(便の結果の文書の変異の節)。
EXPECT_STALE = ("match", "no_same_value", "other_frame", "rounded_diff_hold", "last_branch_evidence", "last_branch_digit_floor", "ambiguous_count")


def claims_rounding(p, sentence, facts, rounding):
    """``rounding``(書類の丸め方の 2 周目)を渡して数の主張を作る(test_recipes_p24.num_claims は渡せない)。"""
    return R._build_raw_num_claims([sentence], facts, contexts_for(facts), V.PROFILES[p], lambda si, pos: (None, "test"), rounding=rounding)


def direct_claim(**extra):
    """``_other_subject_2026_11_02`` を直接呼ぶための、engine が GROUNDED にしなかった行の形(unit_scale 1.0・claim_scale 百万円)。"""
    c = {"unit_scale": 1.0, "claim_scale": 1000000.0, "result": None, "reason": "no_same_value", "pointer": None, "bound": False, "recomputed": None}
    c.update(extra)
    return c


class P28EProfileTest(unittest.TestCase):
    def test_p28e_is_p27e_plus_exactly_the_other_flag(self):
        self.assertEqual(dataclasses.replace(V.P27E, name="P28E", other_subject_2026_11_02=True), V.P28E)
        self.assertIs(V.PROFILES["P28E"], V.P28E)

    def test_p28e_has_the_flag_set_of_p27e_plus_the_other_flag(self):
        names = [f.name for f in dataclasses.fields(V.Profile) if f.type in (bool, "bool")]
        on = lambda p: set(n for n in names if getattr(p, n))
        self.assertEqual(on(V.P27E) | {KEY}, on(V.P28E))
        self.assertEqual(on(V.P28) | {"last_branch_relative_2026_10_27"}, on(V.P28E))
        self.assertTrue(V.P28E.last_branch_relative_2026_10_27)
        self.assertFalse(V.P28.last_branch_relative_2026_10_27)

    def test_p28e_flag_off_is_p27e_except_name(self):
        off = dataclasses.replace(V.P28E, other_subject_2026_11_02=False)
        self.assertEqual(dataclasses.replace(V.P27E, name="P28E"), off)

    def test_default_is_still_p27(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)
        self.assertNotEqual("P28E", V.DEFAULT_PROFILE)


class P28ESignTest(unittest.TestCase):
    """符号: O は ``V.match_value`` の既存の帯(符号を見ない ― 同じ符号か絶対値で当たる)で候補を引く。符号つきの数でも決まる fact は +1 と -1 の入力で同じ。"""

    def decided(self, fact_value, sentence, value):
        fs = [NS, fact("OtherNOI", CUR, fact_value), fact("OtherNOE", CUR, 999000000)]
        return pick(claims("P28E", sentence, fs), value)

    def test_signed_sentence_binds_the_same_fact_as_the_unsigned_one_for_both_fact_signs(self):
        for fv in (146000000, -146000000):
            plus = self.decided(fv, "売上高は820百万円、その他は146百万円でした。", 146000000)
            minus = self.decided(fv, "売上高は820百万円、その他は△146百万円でした。", -146000000)
            for c in (plus, minus):
                self.assertEqual("GROUNDED", c["result"], (fv, c[KEY]))
                self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c["pointer"])
                self.assertEqual(float(fv), c["recomputed"])
                self.assertEqual({"前期": False, "候補": 1, "決まった": True}, c[KEY])
            self.assertEqual(plus["pointer"], minus["pointer"])
            self.assertEqual(-146000000.0, minus["value"])
            self.assertEqual(146000000.0, plus["value"])

    def test_direct_call_sign_minus_one_and_plus_one_pick_the_same_fact(self):
        s = "その他は146百万円でした。"
        a = s.index("146")
        b = a + len("146百万円")
        for fv in (146000000.0, -146000000.0):
            facts = [fact("OtherNOI", CUR, fv), fact("OtherNOE", CUR, 5000000)]
            got = []
            for sign in (1, -1):
                c = direct_claim()
                R._other_subject_2026_11_02(c, s, a, b, sign, 146000000.0, "円", facts, contexts_for(facts), V.P28E, None)
                got.append((c["result"], c["pointer"], c["recomputed"], c[KEY]["候補"], c[KEY]["決まった"]))
            self.assertEqual(got[0], got[1], fv)
            self.assertEqual(("GROUNDED", "xbrl:jppfs_cor:OtherNOI@" + CUR, fv, 1, True), got[0])

    def test_sign_is_not_a_condition_a_wrong_sign_fact_of_another_size_is_not_picked(self):
        # 絶対値が合わなければ、符号が合っても結ばない(符号が条件になったのでも、符号を落としただけでもない)
        facts = [fact("OtherNOI", CUR, -147000000)]
        s = "その他は146百万円でした。"
        a = s.index("146")
        for sign in (1, -1):
            c = direct_claim()
            R._other_subject_2026_11_02(c, s, a, a + 6, sign, 146000000.0, "円", facts, contexts_for(facts), V.P28E, None)
            self.assertNotEqual("GROUNDED", c["result"], sign)
            self.assertEqual(0, c[KEY]["候補"])


class P28EStaleKeysTest(unittest.TestCase):
    """stale keys: 最後の枝の欄を置いた claim に O が当たって決まったら、その欄と reason が消え、GROUNDED の形になる。"""

    def test_pipeline_row_loses_the_last_branch_fields_when_o_decides(self):
        fs = [NS, fact("OtherNOI", CUR, 3000000)]
        s = "売上高は820百万円、その他は3百万円でした。"
        before = pick(claims("P27E", s, fs), 3000000)
        self.assertIn("no_same_value", before)             # O を当てる前は最後の枝の欄が在る(試験が空振りでないこと)
        self.assertIn("last_branch_evidence", before)
        self.assertEqual("no_same_value", before["reason"])
        c = pick(claims("P28E", s, fs), 3000000)
        for k in R._P27_STALE_KEYS:
            if k != "match":                                  # match は消してから O の一致の仕方で置き直す
                self.assertNotIn(k, c, k)
        self.assertEqual("GROUNDED", c["result"])
        self.assertIsNone(c["reason"])
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c["pointer"])
        self.assertIs(True, c["bound"])
        self.assertEqual(3000000.0, c["recomputed"])
        self.assertTrue(c["match"])
        self.assertEqual({"前期": False, "候補": 1, "決まった": True}, c[KEY])

    def test_the_stale_key_list_is_the_seven_fields_of_the_last_branch(self):
        self.assertEqual(EXPECT_STALE, tuple(R._P27_STALE_KEYS))

    def test_direct_call_removes_every_stale_key_and_the_reason(self):
        fs = [fact("OtherNOI", CUR, 3000000)]
        s = "その他は3百万円でした。"
        a = s.index("3")
        stale = dict((k, {"x": 1}) for k in EXPECT_STALE)
        stale["match"] = "round"
        stale["ambiguous_count"] = 2
        c = direct_claim(**stale)
        self.assertEqual(set(EXPECT_STALE), set(c) & set(EXPECT_STALE))
        R._other_subject_2026_11_02(c, s, a, a + 5, 1, 3000000.0, "円", fs, contexts_for(fs), V.P28E, None)
        for k in EXPECT_STALE:
            if k != "match":
                self.assertNotIn(k, c, k)
        self.assertIsNone(c["reason"])
        self.assertEqual("GROUNDED", c["result"])
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, c["pointer"])
        self.assertIs(True, c["bound"])
        self.assertEqual(3000000.0, c["recomputed"])
        self.assertEqual("round", c["match"])             # match は消してから O の一致の仕方で置き直す(古い値が残るのでなく、新しい値)

    def test_direct_call_with_stale_keys_but_no_decision_leaves_them_alone(self):
        # 決まらない(候補 0)ときは claim を変えない(欄の消去は決まったときだけ)
        fs = [fact("OtherNOI", CUR, 9000000)]
        s = "その他は3百万円でした。"
        a = s.index("3")
        c = direct_claim(no_same_value={"x": 1}, last_branch_evidence=None)
        R._other_subject_2026_11_02(c, s, a, a + 5, 1, 3000000.0, "円", fs, contexts_for(fs), V.P28E, None)
        self.assertIn("no_same_value", c)
        self.assertIn("last_branch_evidence", c)
        self.assertEqual("no_same_value", c["reason"])
        self.assertNotEqual("GROUNDED", c["result"])


class P28EMagTruncTest(unittest.TestCase):
    """mag_trunc: 書類の丸めが切り捨てのとき(rounding = truncate・claim の magnitude_truncate 真)の帯を O が使う。"""

    S = "売上高は820百万円、その他は146百万円でした。"

    def test_truncate_band_value_is_decided_only_under_truncate(self):
        fs = [NS, fact("OtherNOI", CUR, 146999999)]
        trunc = pick(claims_rounding("P28E", self.S, fs, "truncate"), 146000000)
        self.assertIs(True, trunc.get("magnitude_truncate"))                 # rounding = truncate で claim が絶対値の帯の札を持つ
        self.assertEqual("GROUNDED", trunc["result"], trunc[KEY])
        self.assertEqual("xbrl:jppfs_cor:OtherNOI@" + CUR, trunc["pointer"])
        self.assertEqual(146999999.0, trunc["recomputed"])
        self.assertIn("truncate", trunc["match"])
        rnd = pick(claims_rounding("P28E", self.S, fs, "round"), 146000000)
        self.assertNotIn("magnitude_truncate", rnd)
        self.assertNotEqual("GROUNDED", rnd["result"])                        # 四捨五入の書類なら 146,999,999 は帯の外
        self.assertEqual({"前期": False, "候補": 0, "決まった": False}, rnd[KEY])

    def test_negative_fact_outside_the_magnitude_band_is_not_decided_under_truncate(self):
        # fact -300,297,000 を「△4億円」(-400,000,000)の切り捨ての帯に符号つきのまま当てると 99,703,000 < 1 億で通ってしまう(P19 の実測)。
        # 絶対値で当てれば 300,297,000 < 4 億で帯の外。claim の札(magnitude_truncate)を O が使うことを字で留める。
        fs = [NS, fact("OtherNOI", CUR, -300297000)]
        s = "売上高は820百万円、その他は△4億円でした。"
        cs = claims_rounding("P28E", s, fs, "truncate")
        c = pick(cs, -400000000)
        self.assertIs(True, c.get("magnitude_truncate"))
        self.assertNotEqual("GROUNDED", c["result"], c.get(KEY))
        self.assertEqual({"前期": False, "候補": 0, "決まった": False}, c[KEY])

    def test_direct_call_uses_the_magnitude_flag_of_the_claim_not_the_profile(self):
        fs = [fact("OtherNOI", CUR, -300297000)]
        s = "その他は△4億円でした。"
        a = s.index("△")
        b = len(s) - len("でした。")
        for flag, want in ((True, 0), (False, 1)):
            c = direct_claim(claim_scale=100000000.0, **({"magnitude_truncate": True} if flag else {}))
            R._other_subject_2026_11_02(c, s, a, b, 1, -400000000.0, "円", fs, contexts_for(fs), V.P28E, "truncate")
            self.assertEqual(want, c[KEY]["候補"], flag)
            self.assertEqual(bool(want), c[KEY]["決まった"], flag)


if __name__ == "__main__":
    unittest.main()
