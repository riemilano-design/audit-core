# -*- coding: utf-8 -*-
# compare_render.py の変異試験。**道具が「変わった」を本当に捕まえるか**を 1 つずつ変異させて測る。
# **格上げの条件**(司令塔の判断 2026-09-28): scratchpad の使い捨てを `report-pdf/` に上げるなら変異つきで。
#
# check_answer_test.py・check_delivery_test.py・check_structure_test.py と同じ流儀
# (外部ライブラリなし・unittest だけ・材料は一時フォルダの合成・PDF は fitz)。
#
# **この道具が生まれた理由を試験に残す**: 最初は `get_images()`(埋め込み画像の数と長さ)で比べる
# つもりだった。実測すると**盤はベクタ描画なので画像は 0 個**で、**盤が変わっても何も言わない道具**だった。
# `test_05_images_are_zero_so_they_cannot_be_the_measure` がその事実を固定する
# ― **同じ間違いをもう一度しないため。**
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/compare_render_test.py`
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compare_render as CR  # noqa: E402


def write_pdf(path, pages, shift=0.0, text_suffix=""):
    """fitz で「文字 + ベクタ(枠と線)」のページを作る。`shift` は枠の原点をずらす量(pt)。"""
    import fitz

    doc = fitz.open()
    try:
        for lines in pages:
            page = doc.new_page()
            y = 72
            for line in lines:
                page.insert_text((72, y), line + text_suffix, fontname="japan", fontsize=11)
                y += 24
            # 盤に相当するベクタ(枠 + 格子)。**埋め込み画像は 1 つも置かない**(実物と同じ形)。
            page.draw_rect(fitz.Rect(72 + shift, 200, 272 + shift, 400), width=1)
            for i in range(1, 5):
                page.draw_line(fitz.Point(72 + shift, 200 + i * 40), fitz.Point(272 + shift, 200 + i * 40), width=0.4)
        doc.save(path)
    finally:
        doc.close()


PAGES = [["1 ページ目", "盤があります"], ["2 ページ目", "もう 1 つの盤"], ["3 ページ目", "最後"]]


class CompareRenderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.a = os.path.join(self._tmp.name, "a.pdf")
        write_pdf(self.a, PAGES)

    def tearDown(self):
        self._tmp.cleanup()

    def other(self, name, **kwargs):
        path = os.path.join(self._tmp.name, name)
        write_pdf(path, kwargs.pop("pages", PAGES), **kwargs)
        return path

    # ---- 土台: 同じ中身なら「変わっていない」と言う ----
    def test_00_same_content_is_unchanged(self):
        b = self.other("b.pdf")
        self.assertEqual(CR.differences(self.a, b), [])

    # **バイトが違っても「変わった」と言わない**(これが言えないと、日時の差で毎回赤になる)。
    def test_01_byte_difference_alone_is_not_a_change(self):
        b = self.other("b.pdf")
        self.assertNotEqual(open(self.a, "rb").read(), open(b, "rb").read(),
                            "2 回作って同じバイトになってしまうと、この試験は何も確かめていない")
        self.assertEqual(CR.differences(self.a, b), [])

    # ---- 変異(1 つずつ) ----
    def test_02_half_point_shift_is_caught(self):
        # **0.5pt のずれ**。丸めの桁(ROUND_DIGITS)を上げすぎると、ここが落ちなくなる。
        b = self.other("b.pdf", shift=0.5)
        diffs = CR.differences(self.a, b)
        self.assertTrue(any("ベクタ描画が違うページ" in d for d in diffs), diffs)

    def test_03_text_change_is_caught(self):
        b = self.other("b.pdf", text_suffix="(直した)")
        diffs = CR.differences(self.a, b)
        self.assertTrue(any("文字が違うページ" in d for d in diffs), diffs)

    def test_04_page_count_change_is_caught(self):
        b = self.other("b.pdf", pages=PAGES + [["4 ページ目"]])
        diffs = CR.differences(self.a, b)
        self.assertTrue(any("ページ数が違う" in d for d in diffs), diffs)

    # ---- この道具が生まれた理由を固定する ----
    def test_05_images_are_zero_so_they_cannot_be_the_measure(self):
        """**この試験は実装の写しではなく、道具の側の仮定を固定するものである**(司令塔の注記の指示 2026-09-28)。

        固定している仮定: **「盤はベクタ描画であり、埋め込み画像ではない」**。
        だから `get_images()`(画像の数と長さ)で比べる道具は、**盤が変わっても何も言わない**
        (2026-09-28 に実物で実測: 付録 1 の 21 ページで画像 0 個 ― 最初の私の比べ方がこれだった)。

        **この試験が落ちたら、道具を見直す合図である**(組版が画像を埋め込む作りに変わった、ということ)。
        比べ方をどう変えるかは、そのときに測って決める。"""
        import fitz

        doc = fitz.open(self.a)
        try:
            self.assertEqual(sum(len(p.get_images(full=True)) for p in doc), 0)
            self.assertGreater(sum(CR.drawing_signature(p)[0] for p in doc), 0,
                               "ベクタが 0 本なら、この道具は何も見ていない")
        finally:
            doc.close()

    # ---- 端(丸めの桁が効いているか) ----
    def test_06_tiny_shift_below_rounding_is_not_caught(self):
        """**丸めの桁より小さいずれは捕まえない**(0.001pt)。**これは穴ではなく、決めた分解能である** ―
        測れる下限を試験に書いておく(0.5pt は捕まえる = test_02)。"""
        b = self.other("b.pdf", shift=0.001)
        self.assertEqual(CR.differences(self.a, b), [])


if __name__ == "__main__":
    unittest.main()
