# -*- coding: utf-8 -*-
"""``fixtures/xbrl/tamper_value.py``(型 1)の単体試験。

合成の小さな ZIP だけを使う(本物の EDINET ZIP には触れない)。封
``audit-core/docs/DETECTION_T1_T3_PLAN_2026-10-08.md`` 第 2 部が要求する
最低限の点(数字側の左の境界・全角両形・単位は 1 文字も変わらない・他の
エントリは不変・層の許容の表・(a') は検出率の分母に入らない・漢数字混じ
りは混ぜられない・置換値が参照一覧に在る現場は落ちる)をカバーする。
"""

import io
import os
import sys
import unittest
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_AUDIT_CORE = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIXTURES_XBRL = os.path.join(_AUDIT_CORE, "fixtures", "xbrl")
if _FIXTURES_XBRL not in sys.path:
    sys.path.insert(0, _FIXTURES_XBRL)

import tamper_value as TV  # noqa: E402
import run_detection_t1 as D1  # noqa: E402


_MDNA_LOCAL = "ManagementAnalysisOfFinancialPositionOperatingResultsAndCashFlowsTextBlock"


def make_zip(mdna_text, extra_files=None, local_name=_MDNA_LOCAL, mdna_count=1):
    """最小の合成 ZIP。``tests/fixtures/xbrl/test_tamper_unit.py: make_zip``
    と同じ形(この試験ファイル単独で読めるよう、重複して持つ -- 同ファイル
    の docstring と同じ理由)。"""

    blocks = []
    for i in range(mdna_count):
        blocks.append(
            '<jpcrp_cor:%s contextRef="Ctx%d">%s</jpcrp_cor:%s>' % (local_name, i, mdna_text, local_name)
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" '
        'xmlns:jpcrp_cor="http://example.com/jpcrp_cor">\n'
        + "\n".join(blocks) +
        '\n</xbrli:xbrl>\n'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("XBRL/PublicDoc/test-001_2026-01-01.xbrl", xml.encode("utf-8"))
        for name, data in (extra_files or {}).items():
            z.writestr(name, data)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. 数字の左の境界
# ---------------------------------------------------------------------------

class NumberLeftBoundaryTest(unittest.TestCase):
    def test_short_number_does_not_match_inside_longer_one(self):
        zb = make_zip("当期は1,149百万円となりました。")
        entry, raw, start, end, _local = TV.locate_mdna_raw(zb)
        inner = raw[start:end]
        with self.assertRaises(TV.AmbiguousSite) as ctx:
            TV.find_number_site(inner, "149", "百万円")
        self.assertEqual(ctx.exception.match_count, 0)

    def test_without_the_boundary_it_would_falsely_match(self):
        # 境界を外した素の正規表現なら「149百万円」が「1,149百万円」の末尾に
        # 1 件マッチしてしまう(退化させて確認する ― 守りの効き目を測る)。
        import re
        inner = "当期は1,149百万円となりました。"
        naive = re.compile(re.escape("149") + r"[ 　]*" + re.escape("百万円"))
        self.assertEqual(len(list(naive.finditer(inner))), 1)

    def test_the_longer_number_itself_is_found_uniquely(self):
        zb = make_zip("当期は1,149百万円となりました。")
        entry, raw, start, end, _local = TV.locate_mdna_raw(zb)
        inner = raw[start:end]
        ns, ne, us, ue = TV.find_number_site(inner, "1,149", "百万円")
        self.assertEqual(inner[ns:ne], "1,149")
        self.assertEqual(inner[us:ue], "百万円")


# ---------------------------------------------------------------------------
# 2. 全角の数字
# ---------------------------------------------------------------------------

class FullwidthDigitsTest(unittest.TestCase):
    def test_fullwidth_number_is_found(self):
        zb = make_zip("当期は３億円となりました。")  # ３億円
        entry, raw, start, end, _local = TV.locate_mdna_raw(zb)
        inner = raw[start:end]
        ns, ne, us, ue = TV.find_number_site(inner, "3", "億円")
        self.assertEqual(inner[ns:ne], "３")  # ３ (全角)

    def test_half_width_only_search_would_miss_it(self):
        # 半角だけで探せば見つからない(両形探索が無いと 0 件に退化する)。
        import re
        inner = "当期は３億円となりました。"
        half_only = re.compile(re.escape("3") + r"[ 　]*" + re.escape("億円"))
        self.assertEqual(len(list(half_only.finditer(inner))), 0)


# ---------------------------------------------------------------------------
# 3. 単位が 1 文字も変わらないこと
# ---------------------------------------------------------------------------

class UnitUntouchedTest(unittest.TestCase):
    def test_unit_bytes_identical_before_and_after(self):
        zb = make_zip("当期は129,331千円となりました。")
        new_zb = TV.tamper_value(zb, "129,331", "千円", "129,431")
        _e1, raw1, s1, e1, _l1 = TV.locate_mdna_raw(zb)
        _e2, raw2, s2, e2, _l2 = TV.locate_mdna_raw(new_zb)
        before = raw1[s1:e1]
        after = raw2[s2:e2]
        # 単位の文字列そのものが、前後でちょうど同じ回数・同じ形で現れる。
        self.assertEqual(before.count("千円"), after.count("千円"))
        self.assertNotIn("129,331", after)
        self.assertIn("129,431", after)
        self.assertIn("千円", after)


# ---------------------------------------------------------------------------
# 4. 他の ZIP エントリが不変
# ---------------------------------------------------------------------------

class OtherEntriesUnchangedTest(unittest.TestCase):
    def test_other_entries_untouched(self):
        extra = {"XBRL/PublicDoc/manifest.xml": b"<manifest/>", "meta/other.bin": b"\x00\x01\x02binary"}
        zb = make_zip("当期は129,331千円となりました。", extra_files=extra)
        new_zb = TV.tamper_value(zb, "129,331", "千円", "129,431")
        z1 = zipfile.ZipFile(io.BytesIO(zb))
        z2 = zipfile.ZipFile(io.BytesIO(new_zb))
        self.assertEqual(z1.namelist(), z2.namelist())
        for name in extra:
            self.assertEqual(z1.read(name), z2.read(name))


# ---------------------------------------------------------------------------
# 5. 層の作り方の表形式試験(許容を字で留める)
# ---------------------------------------------------------------------------

class LayerConstructionTableTest(unittest.TestCase):
    def test_money_sen_en_layer_a_adds_one_thousand_yen(self):
        # 千円: claim_scale=1000(許容 500 円)。1,000 円を超えるには +1(千円)。
        params = {"unit_scale": 1000.0, "claim_scale": 1000.0}
        self.assertEqual(TV.tolerance_base_of(params), (500.0, "claim_scale"))
        self.assertEqual(TV.layer_a_delta_doc("129,331", params), 1.0)
        self.assertIsNone(TV.layer_aprime_delta_doc("129,331", params))

    def test_percentage_tolerance_015_layer_a_is_02_points(self):
        params = {"tolerance": 0.15}
        self.assertEqual(TV.tolerance_base_of(params), (0.15, "tolerance"))
        self.assertAlmostEqual(TV.layer_a_delta_doc("5.8", params), 0.2)
        self.assertAlmostEqual(TV.layer_aprime_delta_doc("5.8", params), 0.1)

    def test_breaking_the_table_turns_it_red(self):
        # 表の 1 行を壊すと(許容を間違った式で読む)、この試験が落ちる
        # ことそのものを確かめる -- tolerance_base_of を壊した変異と同じ形。
        params = {"claim_scale": 1000.0, "unit_scale": 1000.0}
        wrong_tolerance = 1.0 * params["claim_scale"]  # 0.5 の代わりに 1.0(壊した式)
        self.assertNotEqual(wrong_tolerance, TV.tolerance_base_of(params)[0])

    def test_degenerate_unreadable_params_builds_no_layer(self):
        # 退化値: 許容が読めない(params が空/None)。層は 1 つも作れない。
        for params in (None, {}, {"something_else": 1}):
            self.assertEqual(TV.tolerance_base_of(params), (None, "unreadable"))
            self.assertIsNone(TV.layer_a_delta_doc("129,331", params))
            self.assertIsNone(TV.layer_aprime_delta_doc("129,331", params))


# ---------------------------------------------------------------------------
# 6. (a') が検出率の分母に入らないこと(合成入力)
# ---------------------------------------------------------------------------

class AprimeExcludedFromRateTest(unittest.TestCase):
    def test_adding_aprime_rows_does_not_move_layer_or_combined_denominators(self):
        rows_by_layer = {
            "a_just_outside": [{"detected": True}, {"detected": False}],
            "b_one_digit": [{"detected": True}],
            "c_order_of_magnitude": [{"detected": True}],
        }
        shortfall = {"a_just_outside": 0, "b_one_digit": 0, "c_order_of_magnitude": 0, "aprime_within_tolerance": 0}
        excluded = {"aprime_within_tolerance": {"cannot_build": 0, "collides_with_reference": 0}}

        base = D1.build_layer_summary(dict(rows_by_layer, aprime_within_tolerance=[]), shortfall, excluded)
        base_n = base["layer_rates"]["a_just_outside"]["rates"]["conditional_on_traceable_before_mixing"]["n"]
        base_combined_n = base["combined_rates"]["conditional_on_traceable_before_mixing"]["n"]

        # (a') に 5 件「足す」。検出結果はわざと混ぜる(全部 100% になる値を
        # 選ばない -- stayed_grounded 3 件・not_grounded 2 件)。
        with_aprime = dict(rows_by_layer, aprime_within_tolerance=[
            {"post_state": "GROUNDED", "claim_present_after": True},
            {"post_state": "GROUNDED", "claim_present_after": True},
            {"post_state": "GROUNDED", "claim_present_after": True},
            {"post_state": "VALUE_MISMATCH", "claim_present_after": True},
            {"post_state": "VALUE_MISMATCH", "claim_present_after": True},
        ])
        after = D1.build_layer_summary(with_aprime, shortfall, excluded)
        after_n = after["layer_rates"]["a_just_outside"]["rates"]["conditional_on_traceable_before_mixing"]["n"]
        after_combined_n = after["combined_rates"]["conditional_on_traceable_before_mixing"]["n"]

        self.assertEqual(base_n, after_n)
        self.assertEqual(base_combined_n, after_combined_n)
        self.assertEqual(after["aprime_box"]["drawn"], 5)
        self.assertEqual(after["aprime_box"]["stayed_grounded"], 3)
        self.assertEqual(after["aprime_box"]["not_grounded"], 2)


# ---------------------------------------------------------------------------
# 7. 漢数字混じりの金額は「混ぜられない書き方」として落ちる
# ---------------------------------------------------------------------------

class KanjiMixedAmountExcludedTest(unittest.TestCase):
    def test_kanji_mixed_amount_is_not_plain(self):
        for digits in ("22億8千1百万円", "9千3百万円", "380億6千4百万円"):
            self.assertFalse(TV.is_plain_number_unit(digits), digits)

    def test_single_segment_is_plain(self):
        # 単一区切り(百万円・億円 がそれ自体 1 つの単位として NUM_RE の
        # 一覧に在る)は混ぜられる -- 漢数字混じりと取り違えない。
        for digits in ("149百万円", "3億円", "6,451百万円"):
            self.assertTrue(TV.is_plain_number_unit(digits), digits)


# ---------------------------------------------------------------------------
# 8. 置換値が参照一覧に在る現場は落ちる
# ---------------------------------------------------------------------------

class CollidesWithReferenceTest(unittest.TestCase):
    def test_exact_match_in_reference_list_is_rejected(self):
        refs = [{"value": 129431000.0, "unit": "円", "label": "x"}]
        self.assertTrue(TV.collides_with_reference(129431.0, "千円", refs))

    def test_non_matching_value_is_not_rejected(self):
        refs = [{"value": 999999999.0, "unit": "円", "label": "x"}]
        self.assertFalse(TV.collides_with_reference(129431.0, "千円", refs))


# ---------------------------------------------------------------------------
# 追加: written_value_of / doc_to_base_scale(漢数字混じりの「百万」1 区切り
# で claim.value が既に base 単位になっている現場で、書かれた文字から正しく
# 値を作れることの回帰 -- 2026-10-08 実測で見つけた癖: S100YMFV N035 等)
# ---------------------------------------------------------------------------

class WrittenValueVsBaseScaleTest(unittest.TestCase):
    def test_written_value_reads_the_text_not_a_prescaled_claim_value(self):
        self.assertEqual(TV.written_value_of("149"), 149.0)
        self.assertEqual(TV.written_value_of("1,850,502"), 1850502.0)

    def test_doc_to_base_scale_uses_claim_scale_not_unit_scale(self):
        # 漢数字混じりの「百万」1 区切り(unit_scale=1.0 のまま、claim_scale
        # だけが正しい倍率を持つ -- tamper_value.doc_to_base_scale の docstring)。
        quirky_params = {"unit_scale": 1.0, "claim_scale": 1000000.0}
        self.assertEqual(TV.doc_to_base_scale(quirky_params), 1000000.0)
        self.assertEqual(TV.step_base_of("149", quirky_params), 1000000.0)
        # 層 (a) は 149 -> 150(+1、書かれた桁の 1 ステップ)であるべき。
        # unit_scale(1.0)を使う壊れた版なら delta_doc は 1.0 のままだが、
        # base 側の意味が壊れる(500000 を直接足して「149500000」のような
        # 桁違いの文字列になる)。ここは delta_doc の値そのものより、
        # 「a' が作れない」(money では m<1)ことで固定する。
        self.assertIsNone(TV.layer_aprime_delta_doc("149", quirky_params))

    def test_regression_aprime_not_buildable_for_quirky_million_yen_claim(self):
        # 2026-10-08 実測で見つけた欠陥の回帰: 直す前は unit_scale(1.0)を
        # 使って a' の delta_doc=500000 を作り、render_like が「149」に
        # そのまま加算して「149500000」という壊れた文字列を書いていた。
        quirky_params = {"unit_scale": 1.0, "claim_scale": 1000000.0}
        self.assertIsNone(TV.layer_aprime_delta_doc("149", quirky_params))


# ---------------------------------------------------------------------------
# 追加: layer_b_new_text(先頭 0 回避・決定性)
# ---------------------------------------------------------------------------

class LayerBNewTextTest(unittest.TestCase):
    def test_deterministic_given_same_seed(self):
        import random
        a = TV.layer_b_new_text("129,331", random.Random("x"))
        b = TV.layer_b_new_text("129,331", random.Random("x"))
        self.assertEqual(a, b)

    def test_different_seed_can_differ(self):
        import random
        results = {TV.layer_b_new_text("129,331", random.Random(str(i))) for i in range(30)}
        self.assertGreater(len(results), 1)

    def test_leading_zero_avoided_for_multi_digit_integer(self):
        import random
        for i in range(200):
            new_text = TV.layer_b_new_text("129,331", random.Random("seed-%d" % i))
            self.assertIsNotNone(new_text)
            int_part = new_text.split(".")[0].replace(",", "")
            self.assertFalse(int_part.startswith("0"), new_text)

    def test_changed_value_differs_from_original(self):
        import random
        new_text = TV.layer_b_new_text("5", random.Random("single-digit"))
        self.assertNotEqual(new_text, "5")


if __name__ == "__main__":
    unittest.main()
