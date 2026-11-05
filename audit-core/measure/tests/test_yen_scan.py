# -*- coding: utf-8 -*-
"""規則 H(封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md §1・追記 1)の試験。

注入の仕掛けの数の読み(``measure/lib/numbers.py``)に「万円」と「億+万などの複合の数」を
足す切り替え ``yen_scan_2026_11_05``(既定 偽)の試験。偽のとき既存の出力が 1 byte も変わらないこと、
真のとき複合 token・万円 の単位・描き・読み直しが封の字どおりであること、倍率表の 万円 の行。

置き場: 封の追記 1 の 2。``test_inject.py`` は名前で仕掛けの file に数えられ、封の木に在る file の
変更が宣言できないので、H の試験は新しい file にある。切り替えを真にする試験は必ず偽に戻す。
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
MEASURE = os.path.dirname(HERE)
sys.path.insert(0, MEASURE)

from lib import numbers as N  # noqa: E402
from lib import scales as SC  # noqa: E402


class TestMoneyScaleTableYenScan(unittest.TestCase):
    """``test_inject.TestMoneyScaleTable`` の表と同じ仕組み(scan -> scaled_value)に、万円 の行を足した表。
    万円 を単位として読むのは切り替えが真のときだけなので、真で走らせる(既存の表の試験は偽で走る)。"""

    _DIGITS_RE = re.compile(r"[0-9,]+(?:\.[0-9]+)?")

    # 封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md §1(規則 H)で足した行。万円 を単位として
    # 読むのは切り替え ``N.yen_scan_2026_11_05`` が真のときだけなので、test_inject の ``REQUIRED_ROWS`` の
    # 試験(切り替え 偽 で走る)には混ぜず、真で走る別の試験で同じ仕組み(scan -> scaled_value)に乗せる。
    YEN_SCAN_ROWS = [
        ("1,234万円", 12340000.0,
         "AI の文の代表例。material/xbrl の 3 書類には実在しない(grep \"[0-9,]万円\" は 3 書類とも 0 件。"
         "S100YMFV に 25 件・S100Z4Q1 に 8 件ある「万円」は全部「4億1千9百万円」型の漢数字の百万円)"),
        ("568万円", 5680000.0, "AI の文の代表例(コンマ無し)。3 書類には実在しない(同じ grep で 0 件)"),
    ]

    def test_man_yen_scale_table_rows_under_yen_scan(self):
        self.assertFalse(N.yen_scan_2026_11_05)
        N.yen_scan_2026_11_05 = True
        try:
            for digits, expected, why in self.YEN_SCAN_ROWS:
                text = N.normalize_digits("%sの額である。" % digits)
                digits_literal = self._DIGITS_RE.search(digits).group(0)
                tok = next(x for x in N.scan(text) if x.text == digits_literal)
                self.assertEqual(tok.unit, "万円")
                got = SC.scaled_value(tok.value, tok.unit)
                self.assertEqual(got, expected, "%r (%s) -> %r (expected %r)" % (digits, why, got, expected))
        finally:
            N.yen_scan_2026_11_05 = False


def _tok_fields(t):
    return (t.text, t.start, t.end, t.value, t.unit, t.unit_end, t.sentence_index, t.has_comma, t.has_frac)


class _YenScanOn(object):
    """切り替え ``N.yen_scan_2026_11_05`` を with の中だけ真にする。出るときは必ず偽に戻す
    (試験の順序で他の試験が汚れない)。"""

    def __enter__(self):
        N.yen_scan_2026_11_05 = True
        return self

    def __exit__(self, *exc):
        N.yen_scan_2026_11_05 = False
        return False


class TestYenScan2026_11_05(unittest.TestCase):
    """規則 H(封 docs/XBRL_INJECT_SCAN_FIX_SEAL_2026-11-05.md §1): 注入の仕掛けの数の読みに
    「万円」と「億+万などの複合の数」を足す。切り替え ``N.yen_scan_2026_11_05``(既定 偽)。

    偽のときの期待値は、この直しの前の ``numbers.py``(89afc79)で同じ文を ``scan`` して
    取った token の全欄を字で写したもの(今の ``numbers.py`` から作った表ではない)。
    """

    # (文, 偽のときの token の全欄 = (text, start, end, value, unit, unit_end, sentence_index, has_comma, has_frac))
    FALSE_CASES = [
        ("売上高は12億3,456万円。", [
            ("12", 4, 6, 12.0, None, 6, 0, False, False),
            ("3,456", 7, 12, 3456.0, None, 12, 0, True, False)]),
        ("1,234万円", [("1,234", 0, 5, 1234.0, None, 5, 0, True, False)]),
        ("5兆1,234億円", [
            ("5", 0, 1, 5.0, None, 1, 0, False, False),
            ("1,234", 2, 7, 1234.0, "億円", 9, 0, True, False)]),
        ("10億円", [("10", 0, 2, 10.0, "億円", 4, 0, False, False)]),
        ("1,234億円", [("1,234", 0, 5, 1234.0, "億円", 7, 0, True, False)]),
        ("1,234百万円", [("1,234", 0, 5, 1234.0, "百万円", 8, 0, True, False)]),
        ("105,873千円", [("105,873", 0, 7, 105873.0, "千円", 9, 0, True, False)]),
        ("1,234万人", [("1,234", 0, 5, 1234.0, None, 5, 0, True, False)]),
        ("3万株", [("3", 0, 1, 3.0, None, 1, 0, False, False)]),
        ("2026年", [("2026", 0, 4, 2026.0, None, 4, 0, False, False)]),
        ("売上は1億500万円でした。次は1,234万円。", [
            ("1", 3, 4, 1.0, None, 4, 0, False, False),
            ("500", 5, 8, 500.0, None, 8, 0, False, False),
            ("1,234", 16, 21, 1234.0, None, 21, 1, True, False)]),
    ]

    # 真のときに複合 token にならない文(億だけ・百万円・千円・万人・万株・年)。
    NO_HIT = ["10億円", "1,234億円", "1,234百万円", "105,873千円", "1,234万人", "3万株", "2026年"]

    # ---- (a) 切り替え 偽 = 既存どおり -------------------------------------------------

    def test_switch_default_is_false(self):
        self.assertIs(N.yen_scan_2026_11_05, False)

    def test_false_scan_is_exactly_the_old_output(self):
        self.assertFalse(N.yen_scan_2026_11_05)
        for text, expected in self.FALSE_CASES:
            got = N.scan(text)
            self.assertEqual([_tok_fields(t) for t in got], expected, text)
            for t in got:
                self.assertIsNone(t.groups, text)

    def test_false_unit_family_and_unit_after_do_not_know_man_yen(self):
        self.assertFalse(N.yen_scan_2026_11_05)
        self.assertIsNone(N.unit_family("万円"))
        self.assertEqual(N._unit_after("1万円", 1), (None, 1))
        self.assertEqual(N._unit_after("1 万円", 1), (None, 1))

    def test_false_render_value_is_the_old_one(self):
        self.assertFalse(N.yen_scan_2026_11_05)
        tok = N.scan("1,234万円")[0]
        self.assertEqual(N.render_value(5678.0, tok), "5,678")
        tok = N.scan("売上高は12億3,456万円。")[0]
        self.assertEqual(N.render_value(13.0, tok), "13")

    def test_as_dict_does_not_carry_groups(self):
        with _YenScanOn():
            tok = N.scan("12億3,456万円")[0]
        self.assertIsNotNone(tok.groups)
        self.assertEqual(
            sorted(tok.as_dict()),
            sorted(["start", "end", "text", "value", "unit", "unit_end", "sentence_index"]),
        )

    # ---- (b) 真 = 複合 token の当たる例 / 当たらない例 --------------------------------

    def test_true_compound_examples_every_field(self):
        cases = [
            ("売上高は12億3,456万円", dict(text="12億3,456", unit="万円", value=123456.0,
                                       groups=(("億", False), ("万", True)),
                                       start=4, end=12, unit_end=14, has_comma=True)),
            ("1,234万円", dict(text="1,234", unit="万円", value=1234.0,
                              groups=(("万", True),), start=0, end=5, unit_end=7, has_comma=True)),
            ("5兆1,234億円", dict(text="5兆1,234", unit="億円", value=51234.0,
                                groups=(("兆", False), ("億", True)),
                                start=0, end=7, unit_end=9, has_comma=True)),
        ]
        with _YenScanOn():
            for text, want in cases:
                toks = N.scan(text)
                self.assertEqual(len(toks), 1, text)
                t = toks[0]
                for k, v in want.items():
                    self.assertEqual(getattr(t, k), v, "%s: %s" % (text, k))
                self.assertIs(t.has_frac, False)
                self.assertEqual(t.sentence_index, 0)
                self.assertIsInstance(t.value, float)

    def test_true_value_is_the_numeral_system_not_a_guess(self):
        with _YenScanOn():
            self.assertEqual(N.scan("1億500万円")[0].value, 10500.0)            # 万円 の数
            self.assertEqual(N.scan("1億500万円")[0].unit, "万円")
            self.assertEqual(N.scan("12億円と3万円")[0].value, 12.0)             # 億だけ = 既存
            self.assertEqual(N.scan("5兆1,234万円")[0].value, 500001234.0)     # 兆 + 万: 兆 = 10^8 万
            self.assertEqual(N.scan("5兆1,234万円")[0].unit, "万円")
            self.assertEqual(N.scan("2億3万円")[0].value, 20003.0)

    def test_true_sentence_index_follows_the_start(self):
        with _YenScanOn():
            toks = N.scan("売上は1億500万円でした。次は1,234万円。")
        self.assertEqual([(t.text, t.sentence_index) for t in toks], [("1億500", 0), ("1,234", 1)])

    def test_true_non_hits_are_the_old_tokens_with_no_groups(self):
        for text in self.NO_HIT:
            self.assertFalse(N.yen_scan_2026_11_05)
            old = [_tok_fields(t) for t in N.scan(text)]
            with _YenScanOn():
                new = N.scan(text)
            self.assertEqual([_tok_fields(t) for t in new], old, text)
            for t in new:
                self.assertIsNone(t.groups, text)

    def test_true_single_oku_stays_the_existing_token(self):
        with _YenScanOn():
            t = N.scan("10億円")[0]
        self.assertIsNone(t.groups)
        self.assertEqual((t.text, t.unit, t.value), ("10", "億円", 10.0))

    def test_true_unit_family_and_unit_after_know_man_yen(self):
        with _YenScanOn():
            self.assertEqual(N.unit_family("万円"), "money")
            self.assertEqual(N._unit_after("1万円", 1), ("万円", 3))
            self.assertEqual(N._unit_after("1 万円", 1), ("万円", 4))
            # 元の単位は変わらない(長い順: 百万円 が 万円 に食われない)
            self.assertEqual(N._unit_after("1百万円", 1), ("百万円", 4))
            self.assertEqual(N._unit_after("1千円", 1), ("千円", 3))
            self.assertEqual(N._unit_after("1円", 1), ("円", 2))
            self.assertEqual(N._unit_after("1万人", 1), (None, 1))
        self.assertIsNone(N.unit_family("万円"))

    def test_true_spaced_man_yen_is_a_plain_token_with_man_yen_unit(self):
        with _YenScanOn():
            t = N.scan("利益は 5 万円でした。")[0]
        self.assertEqual((t.text, t.unit, t.value, t.unit_end), ("5", "万円", 5.0, 8))
        self.assertIsNone(t.groups)

    def test_the_sealed_pattern_text(self):
        # 封 §1 の 1 の正規表現の字。(?=\d) を外しても振る舞いは変わらない(等価)ので、字で留める。
        x = r"(\d{1,3}(?:,\d{3})+|\d+)"
        self.assertEqual(
            N.YEN_SCAN_RE.pattern,
            r"(?<![0-9.,])(?=\d)(?:" + x + r"兆)?(?:" + x + r"億)?(?:" + x + r"万)?円",
        )

    # ---- (c) 覆われた既存の token が消え、位置順 -----------------------------------

    def test_true_covered_tokens_are_replaced_and_order_is_by_position(self):
        text = "前期は3万株、売上高は12億3,456万円、利益は1,234万円で、10億円を超えた。"
        with _YenScanOn():
            new = N.scan(text)
        old = N.scan(text)
        self.assertEqual([t.text for t in old], ["3", "12", "3,456", "1,234", "10"])
        self.assertEqual([t.text for t in new], ["3", "12億3,456", "1,234", "10"])
        self.assertEqual([t.start for t in new], sorted(t.start for t in new))
        # 覆われた span の中に既存の token が残っていない
        for c in [t for t in new if t.groups is not None]:
            self.assertEqual([t for t in new if t is not c and c.start <= t.start < c.unit_end], [])

    def test_true_a_man_only_token_replaces_the_same_span(self):
        text = "利益は1,234万円。"
        old = N.scan(text)
        with _YenScanOn():
            new = N.scan(text)
        self.assertEqual(len(old), 1)
        self.assertEqual(len(new), 1)
        self.assertEqual((old[0].start, old[0].end), (new[0].start, new[0].end))
        self.assertIsNone(old[0].unit)
        self.assertEqual(new[0].unit, "万円")

    # ---- (d) render_groups ---------------------------------------------------------

    def test_render_groups_examples(self):
        with _YenScanOn():
            comma = N.scan("12億3,456万円")[0]
            self.assertEqual(N.render_value(123458.0, comma), "12億3,458")
            self.assertEqual(N.render_value(123458, comma), "12億3,458")
            like_plain = N.scan("1億500万円")[0]             # 万 の group にコンマ無し
            self.assertEqual(N.render_value(9700.0, like_plain), "9700")
            self.assertEqual(N.render_value(10000.0, like_plain), "1億0")
            self.assertEqual(N.render_value(10500.0, like_plain), "1億500")
            like_comma = N.scan("1億5,000万円")[0]           # 万 の group にコンマ有り
            self.assertEqual(N.render_value(9700.0, like_comma), "9,700")
            self.assertEqual(N.render_value(123456789.0, like_comma), "12345億6,789")
            # 3 桁区切り: コンマありの group だけ
            self.assertEqual(N.render_value(5000.0, N.scan("1,234万円")[0]), "5,000")
            self.assertEqual(N.render_value(1234567.0, N.scan("1,234万円")[0]), "1,234,567")
            self.assertEqual(N.render_value(1234567.0, N.scan("568万円")[0]), "1234567")
            tri = N.scan("5兆1,234億円")[0]
            self.assertEqual(N.render_value(51235.0, tri), "5兆1,235")
            self.assertEqual(N.render_value(1234.0, tri), "1,234")      # 先頭の 兆 の group が 0 → 落とす
            self.assertEqual(N.render_value(50000.0, tri), "5兆0")

    def test_render_groups_rounds_to_an_integer(self):
        with _YenScanOn():
            comma = N.scan("12億3,456万円")[0]
            self.assertEqual(N.render_value(123457.6, comma), "12億3,458")

    def test_render_value_of_a_plain_token_is_untouched_while_true(self):
        with _YenScanOn():
            self.assertEqual(N.render_value(5678.0, N.scan("1,234 百万円")[0]), "5,678")
            self.assertEqual(N.render_value(16.0, N.scan("15.0 %")[0]), "16.0")

    # ---- (e) 描いた字を置いて読み直す(round-trip) -----------------------------------

    def test_rendered_text_rescans_to_the_intended_value_with_groups(self):
        cases = [
            ("売上高は12億3,456万円でした。", 123458.0),
            ("売上は1億500万円でした。", 9700.0),
            ("売上は1億500万円でした。", 10000.0),
            ("売上は1億5,000万円でした。", 9700.0),
            ("利益は1,234万円でした。", 5678.0),
            ("利益は568万円でした。", 569.0),
            ("規模は5兆1,234億円でした。", 51235.0),
            ("規模は5兆1,234億円でした。", 50000.0),
        ]
        for text, value in cases:
            with _YenScanOn():
                like = next(t for t in N.scan(text) if t.groups is not None)
                drawn = N.render_value(value, like)
                new_text = text[:like.start] + drawn + text[like.end:]
                again = N.scan(new_text)
            hit = [t for t in again if t.start == like.start]
            self.assertEqual(len(hit), 1, (text, value, drawn))
            t = hit[0]
            self.assertIsNotNone(t.groups, (text, value, drawn))
            self.assertEqual(t.unit, like.unit, (text, value, drawn))
            # 読み直した値 = 意図した値(位が減った形は groups が減るが value の単位は同じ)
            self.assertEqual(t.value, value, (text, value, drawn))
            self.assertEqual(t.unit_end, like.start + len(drawn) + (like.unit_end - like.end))

    # ---- (f) 倍率表 -----------------------------------------------------------------

    def test_scaled_value_of_man_yen(self):
        self.assertEqual(SC.scaled_value(1234, "万円"), 12340000.0)
        self.assertEqual(SC.scale_of("万円"), 10000)
        self.assertEqual(SC.MONEY_SCALE["百万円"], 1000000)         # 隣の行は変わらない

    # ---- (g) is_quantity は複合 token にも既存の規則 --------------------------------

    def test_is_quantity_applies_the_existing_rules_to_compound_tokens(self):
        def verdicts(text):
            with _YenScanOn():
                return [(t.text, N.is_quantity(text, t)) for t in N.scan(text)]

        self.assertEqual(verdicts("売上高は12億3,456万円でした。"), [("12億3,456", True)])
        self.assertEqual(verdicts("売上は1億500万円でした。次は1,234万円。"), [("1億500", True), ("1,234", True)])
        self.assertEqual(verdicts("5兆1,234億円"), [("5兆1,234", True)])
        # 日付の文脈
        self.assertEqual(
            verdicts("2025年3月期の売上高は1,234万円でした。"),
            [("2025", False), ("3", False), ("1,234", False)],
        )
        # 範囲の後ろの端
        self.assertEqual(verdicts("1,000万円〜2,000万円"), [("1,000", True), ("2,000", False)])
        # 識別子に溶けた数
        self.assertEqual(verdicts("g02-5万円"), [("02", False), ("5", False)])

    # ---- (h) 切り替えを真にした試験は偽に戻す -----------------------------------------

    def test_with_block_restores_false_even_on_error(self):
        try:
            with _YenScanOn():
                self.assertTrue(N.yen_scan_2026_11_05)
                raise RuntimeError("x")
        except RuntimeError:
            pass
        self.assertIs(N.yen_scan_2026_11_05, False)


if __name__ == "__main__":
    unittest.main()
