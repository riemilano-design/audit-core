# -*- coding: utf-8 -*-
# check_delivery.py の試験。凍結の例外 12 件目(2026-09-25、`ALWAYS_FORBIDDEN` に `"None"` を足した)の
# 再発防止。check_answer_test.py・answer_facts_test.py と同じ流儀: pytest 等の外部ライブラリは使わず
# 標準ライブラリ unittest だけを使う。gitignore の実データは読まず、材料は一時フォルダに書く合成の
# md・PDF(fitz で作る)。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/check_delivery_test.py`
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_delivery as CD  # noqa: E402


class WordsOfTest(unittest.TestCase):
    # (a) `words_of([])` に `"None"` が入り、個数が 22(`--forbid` なし)。
    def test_none_included_and_count_is_22(self):
        words = CD.words_of([])
        self.assertIn("None", words)
        self.assertEqual(len(words), 22)

    # (e) `--forbid None` を渡しても語の個数は 22 のまま(重複は 1 つ)。
    def test_forbid_none_does_not_duplicate(self):
        words = CD.words_of(["None"])
        self.assertEqual(len(words), 22)
        self.assertEqual(words.count("None"), 1)


class MainOnMdTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def write_md(self, name, text):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    # (b) 一時フォルダに「…None 手目…」を含む md を 1 本置いて `main([dir])` → rc=1、
    # 標準エラーに `「None」` を含む行。
    def test_md_with_none_fails(self):
        self.write_md("a.md", "一度は悪くなったが、None 手目に戻して勝った将棋")
        old_stderr = sys.stderr
        sys.stderr = captured = __import__("io").StringIO()
        try:
            rc = CD.main([self._tmp.name])
        finally:
            sys.stderr = old_stderr
        self.assertEqual(rc, 1)
        self.assertIn("「None」", captured.getvalue())

    # (c) 同じフォルダで `None` の無い md → rc=0。
    def test_md_without_none_passes(self):
        self.write_md("a.md", "一度は悪くなったが、10 手目に戻して勝った将棋")
        rc = CD.main([self._tmp.name])
        self.assertEqual(rc, 0)


class MainOnPdfTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def write_pdf(self, name, page_texts):
        """fitz で `page_texts`(1 ページ 1 文字列)を持つ PDF を作る。"""
        import fitz  # pymupdf

        doc = fitz.open()
        try:
            for text in page_texts:
                page = doc.new_page()
                page.insert_text((72, 72), text)
            path = os.path.join(self._tmp.name, name)
            doc.save(path)
            return path
        finally:
            doc.close()

    # (d) fitz でページを 2 枚作り、2 枚目にだけ `None 手目` を書いた PDF → rc=1 で `p.2` を指す。
    def test_pdf_second_page_only_fails_with_p2(self):
        self.write_pdf("a.pdf", ["1 手目に指した局面", "一度は悪くなったが、None 手目に戻して勝った将棋"])
        old_stderr = sys.stderr
        sys.stderr = captured = __import__("io").StringIO()
        try:
            rc = CD.main([self._tmp.name])
        finally:
            sys.stderr = old_stderr
        self.assertEqual(rc, 1)
        out = captured.getvalue()
        self.assertIn("「None」", out)
        self.assertIn("p.2", out)
        self.assertNotIn("p.1", out)


if __name__ == "__main__":
    unittest.main()
