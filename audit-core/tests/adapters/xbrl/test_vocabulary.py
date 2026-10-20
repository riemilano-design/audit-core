# -*- coding: utf-8 -*-
import ast
import glob
import io
import os
import unittest

from adapters.xbrl import vocabulary as V


_TESTS_XBRL_DIR = os.path.dirname(os.path.abspath(__file__))


def _literal_names(node):
    """``["P1", "P2"]`` のような**文字列だけの並び**なら名前の list、でなければ None。"""

    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return None
    names = []
    for element in node.elts:
        if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
            return None
        names.append(element.value)
    return names


def _is_registry_expr(node):
    """``sorted(V.PROFILES)`` / ``sorted(V.PROFILES.keys())`` か。"""

    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "sorted" and len(node.args) == 1):
        return False
    arg = node.args[0]
    if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "keys":
        arg = arg.func.value
    return (isinstance(arg, ast.Attribute) and arg.attr == "PROFILES"
            and isinstance(arg.value, ast.Name) and arg.value.id == "V")


def registry_pins(source):
    """``assertEqual`` で ``sorted(V.PROFILES)`` と**字で並べた一覧**を比べている所。

    返すのは ``(行番号, 名前の並び)``。

    **「P1 を含むか」のような推測では判定しない。** 最初そう書いて、意図的な抜き取り
    6 件(``test_concept_binding.ProfileFlagsTest``)を誤って捕まえた。ここで見るのは
    **「登録表そのものと比べている」という構造**だけなので、抜き取りの並びには当たらない。
    """

    out = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "assertEqual" and len(node.args) >= 2):
            continue
        sides = node.args[:2]
        if not any(_is_registry_expr(side) for side in sides):
            continue
        for side in sides:
            names = _literal_names(side)
            if names is not None:
                out.append((getattr(side, "lineno", getattr(node, "lineno", 0)), names))
    return out


class ProfileListPinsAreSelfCheckedTest(unittest.TestCase):
    """**登録表に 1 件足したときに、一覧を字で固定した所が黙って食い違わないようにする。**

    2026-10-14 に実際にこれで事故った: ``PROFILES`` に ``P20`` を足したのに、一覧を
    字で並べている試験 2 本を直し忘れた。**新しく書いた試験 39 本は全部緑**で、
    変異 89 本を回して初めて出た ― しかも等価変異 8 本が同じ理由で赤くなり、
    **変異の測定そのものが汚染された**(run を 1 本捨てた)。

    対策を記憶ではなく**実行前に赤くなる試験**にする(2026-10-08 の人間の指示)。

    判定は**構造で**行う: ``assertEqual`` の片側が ``sorted(V.PROFILES)`` で、もう片側が
    字で並べた一覧なら、それは**登録表の全部についての主張**なので一致を要求する。
    個別の旗を見るための抜き取りの並びには当たらない。
    """

    def test_every_registry_pin_matches_the_registry(self):
        expected = sorted(V.PROFILES)
        found = 0
        for path in sorted(glob.glob(os.path.join(_TESTS_XBRL_DIR, "test_*.py"))):
            with io.open(path, encoding="utf-8") as fh:
                source = fh.read()
            for lineno, names in registry_pins(source):
                found += 1
                self.assertEqual(
                    expected, sorted(names),
                    "%s:%d の一覧が PROFILES と食い違っている(登録表に足したらここも直す)"
                    % (os.path.basename(path), lineno))
        # **0 件だったら「通った」ではなく「届いていない」**(2026-10-07 の記録)。
        self.assertGreaterEqual(found, 2, "登録表と比べている一覧が見つからない(走査が壊れている)")

    def test_the_scanner_finds_a_diverging_pin(self):
        """**試験そのものが効くことを当てる。**1 件足りない一覧を検出するか。"""

        short = [n for n in sorted(V.PROFILES) if n != "P20"]
        source = ("class T:\n    def t(self):\n"
                  "        self.assertEqual(sorted(V.PROFILES), %r)\n" % (short,))
        found = registry_pins(source)
        self.assertEqual(1, len(found))
        self.assertNotEqual(sorted(V.PROFILES), sorted(found[0][1]))

    def test_the_scanner_finds_the_pin_on_either_side(self):
        source = ("class T:\n    def t(self):\n"
                  '        self.assertEqual(["P1"], sorted(V.PROFILES.keys()))\n')
        self.assertEqual([["P1"]], [names for _, names in registry_pins(source)])

    def test_the_scanner_ignores_a_sampled_list(self):
        """個別の旗を見るための抜き取り(登録表と比べていない)には当たらない。

        最初の版は「P1 を含むなら全部の一覧」という**推測の規則**で判定し、
        ``test_concept_binding`` の抜き取り 6 件を誤って捕まえた。
        """

        source = ("class T:\n    def t(self):\n"
                  '        for name in ("P1", "P5F", "P6", "P7", "P13", "P15"):\n'
                  "            self.assertFalse(V.PROFILES[name].x, name)\n")
        self.assertEqual([], registry_pins(source))

    def test_the_scanner_ignores_other_assert_equals(self):
        source = ("class T:\n    def t(self):\n"
                  '        self.assertEqual(["P1", "P2"], something_else)\n'
                  "        self.assertEqual(sorted(V.SUBJECTS), [1, 2])\n")
        self.assertEqual([], registry_pins(source))

    def test_the_scanner_reads_the_tree_not_the_text(self):
        """説明文の中の一覧には当たらない(字面の試験の失敗の型)。"""

        source = '"""説明: self.assertEqual(sorted(V.PROFILES), [\'P1\'])"""\nX = 1\n'
        self.assertEqual([], registry_pins(source))


class SubjectsTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(V.SUBJECTS_BASE_39), 39)
        self.assertEqual(len(V.SUBJECTS_RUN_B_EXTRA_34), 34)
        self.assertEqual(len(V.SUBJECTS_73), 73)
        self.assertEqual(len(V.SUBJECTS_74), 74)

    def test_order_extra_before_base(self):
        self.assertEqual(V.SUBJECTS_73[:34], V.SUBJECTS_RUN_B_EXTRA_34)
        self.assertEqual(V.SUBJECTS_73[34:], V.SUBJECTS_BASE_39)

    def test_vocab4_is_first_in_74(self):
        self.assertEqual(V.SUBJECTS_74[0], V.VOCAB4)
        self.assertEqual(V.SUBJECTS_74[1:], list(V.SUBJECTS_73))

    def test_elements_are_lists_of_str(self):
        for word, elems in V.SUBJECTS_74:
            self.assertIsInstance(word, str)
            self.assertIsInstance(elems, list)
            self.assertTrue(all(isinstance(e, str) for e in elems))


class MatchValueTest(unittest.TestCase):
    def test_round_exact(self):
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")

    def test_round_within_half_unit(self):
        self.assertEqual(V.match_value(100.4, 100.0, 1.0), "round")

    def test_truncate(self):
        # fact slightly above target, within one full unit -> truncate
        self.assertEqual(V.match_value(100.9, 100.0, 1.0), "truncate")

    def test_abs_round(self):
        self.assertEqual(V.match_value(-100.0, 100.0, 1.0), "abs+round")

    def test_no_match(self):
        self.assertIsNone(V.match_value(50.0, 100.0, 1.0))

    def test_sign_mode_order_prefers_plain_over_abs(self):
        # fact already matches without abs; must not report "abs+round".
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")


class TolOfTest(unittest.TestCase):
    def test_decimals_drives_tolerance(self):
        self.assertEqual(V.tol_of({"decimals": "-6"}, 1e3), 0.5e6)

    def test_claim_scale_floor(self):
        self.assertEqual(V.tol_of({"decimals": "0"}, 1e6), 0.5e6)

    def test_missing_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({}, 1e3), 0.5e3)

    def test_inf_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({"decimals": "INF"}, 1e3), 0.5e3)

    def test_bad_decimals_falls_back_to_claim_scale(self):
        self.assertEqual(V.tol_of({"decimals": "not-a-number"}, 1e3), 0.5e3)


class ProfileTest(unittest.TestCase):
    def test_p1_is_member_off(self):
        self.assertFalse(V.P1.member_on)
        self.assertFalse(V.P1.claim_level_member)
        self.assertIsNone(V.P1.run3)
        self.assertEqual(len(V.P1.subjects), 73)

    def test_p5f_is_member_on_claim_level(self):
        self.assertTrue(V.P5F.member_on)
        self.assertTrue(V.P5F.claim_level_member)
        self.assertEqual(V.P5F.run3, "L")
        self.assertEqual(len(V.P5F.subjects), 74)

    def test_profiles_registry(self):
        self.assertEqual(V.PROFILES["P1"], V.P1)
        self.assertEqual(V.PROFILES["P5F"], V.P5F)

    def test_p1_and_p5f_flags_are_all_off(self):
        # Core 接続 C-1g §1: P1・P5F の定義は不変(3 つの新フラグは既定 False)。
        for profile in (V.P1, V.P5F):
            self.assertFalse(profile.flow_sign)
            self.assertFalse(profile.point_diff)
            self.assertFalse(profile.segment_denominator)

    def test_p1_p5f_p6_c1h_flags_are_all_off(self):
        # Core 接続 C-1h §1: P1・P5F・P6 の定義は不変(3 つの新フラグは既定
        # False のまま)。
        for profile in (V.P1, V.P5F, V.P6):
            self.assertFalse(profile.expenditure_sign)
            self.assertFalse(profile.target_word)
            self.assertFalse(profile.text_reason_split)


class P6ProfileTest(unittest.TestCase):
    """Core 接続 C-1g §1(人間の承認、2026-10-06): profile P6 の語彙 7 行と
    3 つのフラグ。P1/P5F はこれらに触れない。
    """

    def test_p6_flags_all_on(self):
        self.assertTrue(V.P6.flow_sign)
        self.assertTrue(V.P6.point_diff)
        self.assertTrue(V.P6.segment_denominator)
        self.assertTrue(V.P6.member_on)
        self.assertTrue(V.P6.claim_level_member)
        self.assertEqual(V.P6.run3, "L")

    def test_p6_in_profiles_registry(self):
        self.assertEqual(V.PROFILES["P6"], V.P6)
        # Core 接続 C-1h: PROFILES は P7 を足して 4 件になった(この行は
        # C-1h の実装担当が更新。P6 自体の登録は不変)。
        self.assertIn("P6", V.PROFILES)

    def test_subjects_p6_extra_7_count(self):
        self.assertEqual(len(V.SUBJECTS_P6_EXTRA_7), 7)

    def test_subjects_p6_extra_7_words(self):
        words = [w for w, _elems in V.SUBJECTS_P6_EXTRA_7]
        self.assertEqual(
            words,
            [
                "流動負債", "固定負債", "投資有価証券の取得による支出",
                "1年内返済予定の長期借入金", "持分法による投資利益", "ROE", "退職給付に係る負債",
            ],
        )

    def test_subjects_p6_is_extra_7_plus_74_in_order(self):
        self.assertEqual(len(V.SUBJECTS_P6), 81)
        self.assertEqual(V.SUBJECTS_P6[:7], tuple(V.SUBJECTS_P6_EXTRA_7))
        self.assertEqual(V.SUBJECTS_P6[7:], tuple(V.SUBJECTS_74))
        self.assertEqual(V.P6.subjects, V.SUBJECTS_P6)

    def test_extra_7_words_absent_from_p1_and_p5f(self):
        p1_words = {w for w, _e in V.P1.subjects}
        p5f_words = {w for w, _e in V.P5F.subjects}
        for word, _elems in V.SUBJECTS_P6_EXTRA_7:
            self.assertNotIn(word, p1_words)
            self.assertNotIn(word, p5f_words)


class FlowConventionTest(unittest.TestCase):
    """Core 接続 C-1g §1-2: CF 流量項目の符号の規約(b、人間の決定、
    2026-10-06)。
    """

    def test_decrease_increase_prefix_is_minus_one(self):
        self.assertEqual(V.flow_convention("DecreaseIncreaseInNotesAndAccountsReceivableTrade"), -1)

    def test_increase_decrease_prefix_is_plus_one(self):
        self.assertEqual(V.flow_convention("IncreaseDecreaseInNotesAndAccountsPayableTrade"), 1)

    def test_net_increase_decrease_prefix_is_plus_one(self):
        self.assertEqual(V.flow_convention("NetIncreaseDecreaseInCashAndCashEquivalents"), 1)

    def test_net_decrease_increase_prefix_is_minus_one(self):
        self.assertEqual(V.flow_convention("NetDecreaseIncreaseInSomething"), -1)

    def test_company_extension_prefix_uses_local_name_only(self):
        self.assertEqual(V.flow_convention("e01234-asr_E00001-000:IncreaseDecreaseInProvisionForWarranties"), 1)
        self.assertEqual(V.flow_convention("e01234-asr_E00001-000:DecreaseIncreaseInTradeReceivables"), -1)

    def test_non_flow_element_is_none(self):
        self.assertIsNone(V.flow_convention("NetSales"))
        self.assertIsNone(V.flow_convention("jppfs_cor:CurrentLiabilities"))


class P7ProfileTest(unittest.TestCase):
    """Core 接続 C-1h §1(人間の決定、2026-10-06): profile P7 = P6 + 3 つの
    フラグ。P7 の語彙は P6 と同じ(``SUBJECTS_P6``)。
    """

    def test_p7_flags_all_on(self):
        self.assertTrue(V.P7.expenditure_sign)
        self.assertTrue(V.P7.target_word)
        self.assertTrue(V.P7.text_reason_split)
        # P6 の 3 フラグも引き続き真(P7 は P6 の全部を引き継ぐ)。
        self.assertTrue(V.P7.flow_sign)
        self.assertTrue(V.P7.point_diff)
        self.assertTrue(V.P7.segment_denominator)
        self.assertTrue(V.P7.member_on)
        self.assertTrue(V.P7.claim_level_member)
        self.assertEqual(V.P7.run3, "L")

    def test_p7_in_profiles_registry(self):
        self.assertEqual(V.PROFILES["P7"], V.P7)
        # XBRL 直し(2026-10-08)で P8 を足した。P1/P5F/P6/P7 の 4 つが在ること
        # と、P8 がこの 4 つに加わっていることを両方見る。
        self.assertEqual(sorted(V.PROFILES.keys()),
                         ["P1", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21", "P22", "P23", "P5F", "P6", "P7", "P8", "P9"])

    def test_p7_subjects_same_as_p6(self):
        self.assertEqual(V.P7.subjects, V.P6.subjects)
        self.assertEqual(len(V.P7.subjects), 81)


class ExpenditureConventionTest(unittest.TestCase):
    """Core 接続 C-1h §1-1(人間の決定、2026-10-06): CF の「支出」系項目。"""

    def test_purchase_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PurchaseOfPropertyPlantAndEquipment"))

    def test_payments_for_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PaymentsForRetirementBenefits"))

    def test_payments_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("PaymentsOfSomething"))

    def test_repayments_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RepaymentsOfLongTermLoansPayable"))

    def test_repayment_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RepaymentOfLoansPayable"))

    def test_redemption_of_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("RedemptionOfBonds"))

    def test_dividends_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("DividendsPaid"))

    def test_income_taxes_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("IncomeTaxesPaid"))

    def test_interest_paid_prefix_is_expenditure(self):
        self.assertTrue(V.expenditure_convention("InterestPaid"))

    def test_proceeds_from_prefix_is_not_expenditure(self):
        self.assertFalse(V.expenditure_convention("ProceedsFromLongTermLoansPayable"))

    def test_increase_decrease_prefix_is_not_expenditure(self):
        # flow_convention(DecreaseIncreaseIn…/IncreaseDecreaseIn…) が先に
        # 効く対象で、expenditure_convention はここでは False。
        self.assertFalse(V.expenditure_convention("IncreaseDecreaseInNotesAndAccountsPayableTrade"))
        self.assertFalse(V.expenditure_convention("DecreaseIncreaseInNotesAndAccountsReceivableTrade"))

    def test_company_extension_prefix_uses_local_name_only(self):
        self.assertTrue(V.expenditure_convention("e01234-asr_E00001-000:PurchaseOfInvestmentSecurities"))

    def test_non_expenditure_element_is_false(self):
        self.assertFalse(V.expenditure_convention("NetSales"))
        self.assertFalse(V.expenditure_convention("Assets"))


if __name__ == "__main__":
    unittest.main()


class MatchValueModeTest(unittest.TestCase):
    """XBRL 直し §2(2026-10-08): ``match_value`` の ``mode``。

    桁 ``unit`` を 1.0、目標を 100.0 に固定して、3 つの帯を両側から当てる。
    ``-0.4`` は round だけ・``+0.9`` は truncate だけが通る帯であり、
    ``mode=None``(既存)は**両方**通す = 許容幅が実質 1.5 倍であることを数で残す。
    """

    def test_mode_none_accepts_both_sides(self):
        self.assertEqual(V.match_value(99.6, 100.0, 1.0), "round")
        self.assertEqual(V.match_value(100.9, 100.0, 1.0), "truncate")

    def test_round_only_rejects_the_truncate_side(self):
        self.assertEqual(V.match_value(99.6, 100.0, 1.0, "round"), "round")
        self.assertIsNone(V.match_value(100.9, 100.0, 1.0, "round"))

    def test_truncate_only_rejects_the_negative_side(self):
        self.assertEqual(V.match_value(100.9, 100.0, 1.0, "truncate"), "truncate")
        self.assertIsNone(V.match_value(99.6, 100.0, 1.0, "truncate"))

    def test_truncate_only_still_labels_the_overlap_as_truncate(self):
        # 差が 0 以上 unit/2 以下の重なりの帯は、梯子では round の札が付くが、
        # 書類の丸め方を truncate に決めたら truncate の札になる。
        self.assertEqual(V.match_value(100.0, 100.0, 1.0), "round")
        self.assertEqual(V.match_value(100.0, 100.0, 1.0, "truncate"), "truncate")

    def test_abs_prefix_survives_each_mode(self):
        self.assertEqual(V.match_value(-100.9, 100.0, 1.0, "truncate"), "abs+truncate")
        self.assertEqual(V.match_value(-99.6, 100.0, 1.0, "round"), "abs+round")

    def test_mode_none_is_identical_to_the_frozen_ladder(self):
        # 恒等: mode を渡さないことと None を渡すことが同じ。
        for fv in (99.4, 99.6, 100.0, 100.4, 100.9, 101.2, -100.0, 0.0):
            self.assertEqual(V.match_value(fv, 100.0, 1.0), V.match_value(fv, 100.0, 1.0, None))


class DecideRoundingTest(unittest.TestCase):
    """XBRL 直し §2: 書類単位の丸め方の決め方。``(差, 桁)`` の列から決める。"""

    def test_truncate_when_truncate_only_evidence_wins(self):
        self.assertEqual(V.decide_rounding([(0.9, 1.0), (0.8, 1.0), (-0.3, 1.0)]), ("truncate", 1, 2))

    def test_round_when_round_only_evidence_wins(self):
        self.assertEqual(V.decide_rounding([(-0.3, 1.0), (-0.2, 1.0), (0.9, 1.0)]), ("round", 2, 1))

    def test_tie_falls_back_to_the_written_default(self):
        self.assertEqual(V.DOC_ROUNDING_DEFAULT, "round")
        self.assertEqual(V.decide_rounding([(0.9, 1.0), (-0.3, 1.0)]), ("round", 1, 1))

    def test_no_evidence_falls_back_to_the_written_default(self):
        self.assertEqual(V.decide_rounding([]), ("round", 0, 0))

    def test_overlap_band_is_evidence_for_neither(self):
        # 差が 0..unit/2 の重なりの帯は、どちらの丸め方でも説明できるので
        # R にも T にも数えない。
        self.assertEqual(V.decide_rounding([(0.0, 1.0), (0.4, 1.0), (0.5, 1.0)]), ("round", 0, 0))

    def test_unit_is_read_per_row(self):
        # 桁は行ごと。0.9 は桁 1.0 なら truncate だけの帯だが、桁 10.0 なら重なり。
        self.assertEqual(V.decide_rounding([(0.9, 1.0)]), ("truncate", 0, 1))
        self.assertEqual(V.decide_rounding([(0.9, 10.0)]), ("round", 0, 0))


class SubjectsP8Test(unittest.TestCase):
    """XBRL 直し §1a(2026-10-08): 「資産合計」に ``TotalAssets`` を足す。
    主語の数は増やしていない・P6 の語彙は不変。
    """

    def test_same_number_of_subjects_as_p6(self):
        self.assertEqual(len(V.SUBJECTS_P8), len(V.SUBJECTS_P6))

    def test_only_the_total_assets_rows_differ_from_p6(self):
        differ = [(a, b) for a, b in zip(V.SUBJECTS_P6, V.SUBJECTS_P8) if a != b]
        self.assertTrue(differ)
        for a, b in differ:
            self.assertEqual(a[0], "資産合計")
            self.assertEqual(b, ("資産合計", ["Assets", "TotalAssets"]))

    def test_p6_total_assets_is_still_assets_only_somewhere(self):
        # 直す前の非対称(「純資産合計」は Summary が引けるのに「資産合計」は
        # 引けない)が P6 に残っていることを固定する。
        self.assertIn(("資産合計", ["Assets"]), list(V.SUBJECTS_P6))
        self.assertIn(("純資産合計", ["NetAssets"]), list(V.SUBJECTS_P6))

    def test_p8_total_assets_can_reach_the_summary_element(self):
        # 語彙には「資産合計」の行が 2 つある(RUN=="B" の 34 語と基礎の 39 語)。
        # ``subject_of`` は同じ語・同じ長さなら**先に来た行**を採るので、
        # ``dict()`` で引くと(後の行が勝って)実際とは違う答えになる。
        # そこで実際に主語を引く経路で見る。
        # ``facts_for`` は 要素名 + "SummaryOfBusinessResults" を完全一致に数える。
        from adapters.xbrl import extract as X
        s = "当連結会計年度末における資産合計は、278億円となりました。"
        pos = s.index("278")
        _w8, elems8 = X.subject_of(s, pos, V.SUBJECTS_P8)
        _w6, elems6 = X.subject_of(s, pos, V.SUBJECTS_P6)
        self.assertEqual(elems8, ["Assets", "TotalAssets"])
        self.assertEqual(elems6, ["Assets"])
        self.assertIn("TotalAssetsSummaryOfBusinessResults", [e + "SummaryOfBusinessResults" for e in elems8])
        self.assertNotIn("TotalAssetsSummaryOfBusinessResults", [e + "SummaryOfBusinessResults" for e in elems6])


class P8ProfileTest(unittest.TestCase):
    """XBRL 直し(2026-10-08): P8 = P7 + 5 つのフラグ。既存 profile は不変。"""

    FLAGS = ("prior2_required", "doc_rounding", "target_both", "paren_sentence", "drop_qualitative")

    def test_p8_turns_all_five_on(self):
        for f in self.FLAGS:
            self.assertTrue(getattr(V.P8, f), f)

    def test_existing_profiles_keep_all_five_off(self):
        for p in (V.P1, V.P5F, V.P6, V.P7):
            for f in self.FLAGS:
                self.assertFalse(getattr(p, f), "%s.%s" % (p.name, f))

    def test_p8_keeps_every_p7_flag(self):
        for f in ("member_on", "claim_level_member", "flow_sign", "point_diff", "segment_denominator",
                  "expenditure_sign", "target_word", "text_reason_split"):
            self.assertEqual(getattr(V.P8, f), getattr(V.P7, f), f)
        self.assertEqual(V.P8.run3, V.P7.run3)

    def test_p8_uses_the_p8_subjects(self):
        self.assertEqual(V.P8.subjects, V.SUBJECTS_P8)
        self.assertEqual(V.P7.subjects, V.SUBJECTS_P6)


class SubjectsP12Test(unittest.TestCase):
    """XBRL 直し §7c(人間の判断、2026-10-08): 手書きの語彙そのものを直す。

    直すのは 2 語だけ。標準タクソノミ(jppfs 2025-11-01)で機械確認した結果、
    「要素が実在しない + 同じ日本語ラベルの実在の要素が在る + 3 書類とも fact 0」
    の 3 つを同時に満たすのがこの 2 語しかなかった。
    """

    def test_the_two_words_gain_the_element_that_actually_exists(self):
        d = dict(V.SUBJECTS_P12)
        self.assertEqual(d["退職給付に係る資産"], ["RetirementBenefitAsset", "NetDefinedBenefitAsset"])
        self.assertEqual(d["退職給付に係る負債"], ["RetirementBenefitLiability", "NetDefinedBenefitLiability"])

    def test_the_old_name_is_kept_not_replaced(self):
        # 会社拡張が古い名前を使っている書類がありうるので**消さずに足す**。
        for word, elems in V.SUBJECTS_P12_FIXES.items():
            self.assertEqual(elems[0], dict(V.SUBJECTS_P8)[word][0], word)
            self.assertGreater(len(elems), len(dict(V.SUBJECTS_P8)[word]))

    def test_p6_and_p8_are_not_touched(self):
        """**ここが動くと P7(「直す前」)と P10 の既に測った数が黙って動く。**

        ``dict(...)`` は使わない ― 一覧には同じ語が 2 行在ることがあり
        (``資産合計`` は P6 で 2 行)、``dict`` は**最後**を返すのに
        ``subject_of`` は**先**を採る。前にこの取り違えで試験を 1 本間違えた。
        """

        def first(subjects, word):
            return next(e for w, e in subjects if w == word)

        self.assertEqual(first(V.SUBJECTS_P8, "退職給付に係る負債"), ["RetirementBenefitLiability"])
        self.assertEqual(first(V.SUBJECTS_P6, "退職給付に係る負債"), ["RetirementBenefitLiability"])
        self.assertEqual(first(V.SUBJECTS_P8, "退職給付に係る資産"), ["RetirementBenefitAsset"])
        self.assertEqual(first(V.SUBJECTS_P6, "退職給付に係る資産"), ["RetirementBenefitAsset"])
        # §1a で足した 資産合計 の 1 行目は P6 では ["Assets"] のまま。
        self.assertEqual(first(V.SUBJECTS_P6, "資産合計"), ["Assets"])

    def test_only_the_two_words_differ_from_p8(self):
        self.assertEqual(len(V.SUBJECTS_P12), len(V.SUBJECTS_P8))
        differ = [a[0] for a, b in zip(V.SUBJECTS_P12, V.SUBJECTS_P8) if a != b]
        self.assertEqual(sorted(set(differ)), ["退職給付に係る負債", "退職給付に係る資産"])

    def test_the_word_order_is_unchanged(self):
        self.assertEqual([w for w, _e in V.SUBJECTS_P12], [w for w, _e in V.SUBJECTS_P8])


class P12P13P14ProfileTest(unittest.TestCase):
    """XBRL 直し §7a/§7b/§7c/§8 の profile。既存の定義は 1 行も書き換えない。"""

    def test_p13_is_p12_plus_only_the_taxonomy_flag(self):
        import dataclasses
        a = dataclasses.replace(V.P12, name="x", taxonomy_labels=True)
        self.assertEqual(a, dataclasses.replace(V.P13, name="x"))

    def test_p14_is_p13_plus_only_the_namespace_flag(self):
        import dataclasses
        a = dataclasses.replace(V.P13, name="x", taxonomy_labels_all_ns=True)
        self.assertEqual(a, dataclasses.replace(V.P14, name="x"))

    def test_p12_to_p14_use_the_fixed_hand_vocabulary(self):
        for p in (V.P12, V.P13, V.P14):
            self.assertIs(p.subjects, V.SUBJECTS_P12, p.name)
        for p in (V.P8, V.P9, V.P10, V.P11):
            self.assertIs(p.subjects, V.SUBJECTS_P8, p.name)

    def test_profiles_registry_lists_every_profile(self):
        self.assertEqual(sorted(V.PROFILES),
                         ["P1", "P10", "P11", "P12", "P13", "P14", "P15", "P16", "P17", "P18", "P19", "P20", "P21", "P22", "P23", "P5F", "P6", "P7", "P8", "P9"])
        for name, p in V.PROFILES.items():
            self.assertEqual(p.name, name)


# ---------------------------------------------------------------------------
# 主語の規則の直し S4(人間の判断 1、2026-10-08)。
# ---------------------------------------------------------------------------

SENT_T006 = ("一方で利益面におきましては、当社連結子会社である大日本ダイヤコンサルタント株式会社が"
             "実施した複数の橋梁耐震補強設計業務において、期末に設計の一部に誤りが判明し、"
             "完成業務補償引当金繰入額を計上したため、営業利益は14億6千5百万円(同54.0%)、"
             "経常利益は14億5千7百万円(同53.8%)、最終の親会社株主に帰属する当期純利益は"
             "9億4千5百万円(同49.2%)となり、前連結会計年度に比べ増収減益となりました。")
SENT_T015 = ("当連結会計年度の業績につきましては、売上高は堅調に推移したものの、"
             "原材料価格の高騰や人件費の増加の影響、新店舗出店及びアカデミー開設に係る"
             "費用の発生等により前期に比べ増収減益となりました。")
SENT_T042 = ("また、特別損失として減損損失3,758千円を計上したことにより、"
             "親会社株主に帰属する当期純損失105,873千円と前連結会計年度に比べ"
             "88,251千円(前連結会計年度は親会社株主に帰属する当期純損失17,621千円)の"
             "減益となりました。")
SENT_T040 = ("営業損益につきましては、営業損失52,196千円と前連結会計年度に比べ"
             "42,487千円(前連結会計年度は営業損失9,709千円)の減益となりました。")


class DirectionFamilyWordsTest(unittest.TestCase):
    def test_the_two_families_are_written_out_literally(self):
        # **部分一致で作っていない**こと(「利益」「損失」から作ると
        # 「減損損失」が入ってしまう)。
        self.assertEqual(V.REVENUE_WORDS, ("売上高", "営業収益", "売上収益"))
        self.assertEqual(len(V.PROFIT_WORDS), 10)
        self.assertIn("親会社株主に帰属する当期純損失", V.PROFIT_WORDS)
        self.assertNotIn("減損損失", V.PROFIT_WORDS)

    def test_a_direction_word_without_a_family_is_not_touched(self):
        # 「当てない」と「0 件」を言い分ける ― ここが None でないと
        # 「増加」の主張まで S4 が触ってしまう。
        for w in ("増加", "減少", "拡大", "上回", "改善"):
            self.assertIsNone(V.direction_family_words("売上高は100円増加しました。", w), w)

    def test_zero_candidates_is_an_empty_list_not_none(self):
        self.assertEqual(V.direction_family_words("前期に比べ増収となりました。", "増収"), [])

    def test_t006_three_profit_words_in_one_sentence(self):
        got = V.direction_family_words(SENT_T006, "減益")
        self.assertEqual([w for w, _i in got], ["営業利益", "経常利益", "親会社株主に帰属する当期純利益"])

    def test_t006_has_no_revenue_word_although_it_says_zoshu(self):
        self.assertEqual(V.direction_family_words(SENT_T006, "増収"), [])

    def test_t015_has_one_revenue_word_and_no_profit_word(self):
        self.assertEqual([w for w, _i in V.direction_family_words(SENT_T015, "増収")], ["売上高"])
        self.assertEqual(V.direction_family_words(SENT_T015, "減益"), [])

    def test_a_nested_occurrence_counts_once_as_the_longer_word(self):
        # 「当期純損失」は「親会社株主に帰属する当期純損失」の中に在る。
        # 2 件と数えると「決められない」になってしまうので 1 件に畳む。
        got = V.direction_family_words(SENT_T042, "減益")
        self.assertEqual([w for w, _i in got], ["親会社株主に帰属する当期純損失"])

    def test_the_same_word_twice_counts_once(self):
        got = V.direction_family_words(SENT_T040, "減益")
        self.assertEqual([w for w, _i in got], ["営業損失"])

    def test_eigyogai_shueki_is_not_a_revenue_word(self):
        # 「営業外収益」は「営業収益」を含まない(字が違う)。
        self.assertEqual(V.direction_family_words("営業外収益4,171千円を計上し増収となりました。", "増収"), [])


class P15ProfileTest(unittest.TestCase):
    FLAGS = ("subject_skip_coordinated_cause", "subject_direction_object",
             "subject_not_part_of_aggregate", "direction_word_lexicon",
             "direction_amount_check")

    def test_p15_turns_on_all_five(self):
        for f in self.FLAGS:
            self.assertTrue(getattr(V.P15, f), f)

    def test_every_earlier_profile_has_all_five_off(self):
        # **P13 の定義を 1 行も書き換えていない**ことの錠。
        for name, p in V.PROFILES.items():
            if name == "P15":
                continue
            for f in self.FLAGS:
                self.assertFalse(getattr(p, f), (name, f))

    def test_p15_differs_from_p13_in_exactly_those_five_fields(self):
        import dataclasses
        a, b = dataclasses.asdict(V.P13), dataclasses.asdict(V.P15)
        differ = sorted(k for k in a if a[k] != b[k])
        self.assertEqual(differ, sorted(("name",) + self.FLAGS))

    def test_p15_is_in_the_registry_and_names_itself(self):
        self.assertIs(V.PROFILES["P15"], V.P15)
        self.assertEqual(V.P15.name, "P15")

    def test_p15_uses_the_same_hand_vocabulary_as_p13(self):
        self.assertEqual(V.P15.subjects, V.P13.subjects)
