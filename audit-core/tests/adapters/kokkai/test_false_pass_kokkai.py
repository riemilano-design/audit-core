# -*- coding: utf-8 -*-
"""``measure/kokkai_false_pass_2026-10-15.py`` の**桁の決め方**を留める。

なぜ試験が要るか: 2026-10-15 の監査が、使い捨ての script の桁の決め方が 49 件のうち
26 件で粗すぎたことを見つけた(十百千だけで書かれた数で**先頭の位**を採っていた ―
「四十五隻」に +10)。原則「一回限りの手の実測は門ではない」。道具にして試験を付ける。
"""

import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TOOL = os.path.join(ROOT, "measure", "kokkai_false_pass_2026-10-15.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_CORE = os.path.join(ROOT, "core", "py")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

_spec = importlib.util.spec_from_file_location("kokkai_false_pass_tool", TOOL)
FP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FP)


class MinWrittenStepTest(unittest.TestCase):
    """**書かれた表記の最小の桁**を返す。位取りの字の先頭ではない。"""

    CASES = (
        # 十百千だけの数 ― 一の位まで書かれていれば 1(監査が見つけた 26 件の型)
        ("四十五隻", 1.0),
        ("八十三名", 1.0),
        ("二百八十六円", 1.0),
        ("十年", 10.0),            # 一の位が書かれていない
        ("千五百円", 100.0),       # 百の位が最小
        # 大きい単位つき ― その単位の中で最小の位
        ("三百億円", 1e10),
        ("八兆五千六百四十一億円", 1e8),
        ("二兆円", 1e12),
        ("十億円", 1e9),
        ("約八千億円", 1e11),
        # 小数 ― 大きい単位の前に来る形も含む
        ("一・一兆円", 1e11),
        ("二・五兆円", 1e11),
        ("二七・七％", 0.1),
        ("1.25%", 0.01),
        # **複合単位**(``UNITS`` の 万人・億人)― 単位に含まれる位の字は桁として残す
        # (2026-10-15 の監査が実データ K-034「三十四万人」で見つけた誤り)
        ("三十四万人", 1e4),
        ("二億人", 1e8),
        ("百二十三万人", 1e4),
        # 接頭辞つき(剥がさなくても位の字でない字は読み飛ばされる)
        ("約三十四万人", 1e4),
        ("およそ二七・七％", 0.1),
        # 位取りの字を使わない並び
        ("一五％", 1.0),
        ("15%", 1.0),
        ("一九九一年", 1.0),
    )

    def test_cases(self):
        for text, want in self.CASES:
            got = FP.min_written_step(text)
            self.assertIsNotNone(got, text)
            self.assertAlmostEqual(got, want, delta=1e-9 * max(1.0, want), msg=text)

    def test_leading_place_is_not_the_step(self):
        """**先頭の位を採る実装では落ちる。**(監査が見つけた誤りそのもの)"""

        self.assertEqual(FP.min_written_step("四十五隻"), 1.0)
        self.assertNotEqual(FP.min_written_step("四十五隻"), 10.0)
        self.assertEqual(FP.min_written_step("八兆五千六百四十一億円"), 1e8)
        self.assertNotEqual(FP.min_written_step("八兆五千六百四十一億円"), 1e12)

    def test_unreadable_returns_none(self):
        self.assertIsNone(FP.min_written_step("数十"[0:0]))
        self.assertIsNone(FP.min_written_step(None))
        self.assertIsNone(FP.min_written_step("円"))

    def test_every_unit_containing_a_place_char_keeps_that_place(self):
        """**不変条件**: ``UNITS`` の単位に位の字(十百千万億兆)が含まれていたら、
        その字は桁として残る。字で 2 件を並べるのではなく、単位の一覧を全部当てる
        (``UNITS`` が増えたときに同じ誤りが戻らないように)。"""

        from adapters.kokkai import numerals as N
        place = {"十": 10.0, "百": 100.0, "千": 1000.0, "万": 1e4, "億": 1e8, "兆": 1e12}
        checked = 0
        for u in sorted(N.UNITS):
            chars = [ch for ch in u if ch in place]
            if not chars:
                continue
            checked += 1
            want = min(place[ch] for ch in chars)
            got = FP.min_written_step("三" + u)
            self.assertIsNotNone(got, u)
            self.assertAlmostEqual(got, want, delta=1e-9 * want, msg=u)
        self.assertGreaterEqual(checked, 2, "複合単位が 1 件も無い ― 一覧の読み方が違う")

    def test_the_real_row_that_the_audit_found(self):
        """**実データの 1 行を字で留める。**(記憶でなく試験で縛る)"""

        self.assertAlmostEqual(FP.min_written_step("三十四万人"), 1e4, delta=1e-6)
        self.assertNotEqual(FP.min_written_step("三十四万人"), 1.0)

    def test_unit_is_stripped_longest_first(self):
        """単位は長いものから剥がす(``numerals`` と同じ向き)。"""

        self.assertEqual(FP.min_written_step("三か月"), 1.0)
        self.assertEqual(FP.min_written_step("五十パーセント"), 10.0)


def _tool_source():
    with open(TOOL, encoding="utf-8") as fh:
        return fh.read()


class ToolShapeTest(unittest.TestCase):
    def test_measures_both_meetings(self):
        self.assertEqual(len(FP.CASES), 2)
        for mt, sm in FP.CASES:
            self.assertTrue(os.path.exists(os.path.join(FP.FIX, mt)), mt)
            self.assertTrue(os.path.exists(os.path.join(FP.FIX, sm)), sm)

    def test_one_mutation_per_verification(self):
        """**1 件ずつ別の検証にかける。**(XBRL 側で束ねると互いを汚した ―
        束ねた版は書類の丸めの決定を動かし、22 件の誤りを通した)"""

        src = _tool_source()
        self.assertIn("for cc in s2[\"claims\"]:", src)
        self.assertIn("if cc[\"id\"] == c[\"id\"]:", src)
        self.assertNotIn("batch", src)

    def test_no_network(self):
        src = _tool_source()
        for word in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(word, src)


if __name__ == "__main__":
    unittest.main()
