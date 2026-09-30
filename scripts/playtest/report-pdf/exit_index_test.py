# -*- coding: utf-8 -*-
# `exit_index.py` の試験。いまは**付録へ回す節の印**(器の単独束 C-4。2026-09-30)だけを見る。
#
# 【この印の危ない所】**片側だけ効くこと。**本編から外れたのに付録に組まれなければ、
# 顧客が読む表が**どこにも出ない**。だから印の切り出しは「本編から消える」と「節が返る」の
# **両方**を見る(組版の両側は `check_structure` の検査が見る)。
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import exit_index as EI  # noqa: E402


def md_of(tag_line="<!-- appendix: 数の出どころ -->"):
    return "\n".join([
        "# 25 局で起きていたこと",
        "",
        "## ひとことで",
        "",
        "- 崩れは 79 回でした。",
        "",
        "## 数え方",
        "",
        "- 固定の注。",
        "",
        tag_line,
        "",
        "### 数の分母がどこから来たか",
        "",
        "| 数 | 数えたもの | どの集計から出たか |",
        "|---|---|---|",
        "| 79 | 回 | 崩れの合計 |",
        "",
        "## 対応表 ― 何局目が、どのファイルか(本人用)",
        "",
        "| 局 | ファイル名 |",
        "|---|---|",
        "| 1 | g01 |",
    ])


class SplitAppendixSectionsTest(unittest.TestCase):
    def test_a_section_moves_out_of_the_body(self):
        keep, moved = EI.split_appendix_sections(md_of())
        # **本編から消える**
        self.assertNotIn("数の分母がどこから来たか", keep)
        self.assertNotIn("崩れの合計", keep)
        # **印そのものもどちらにも残らない**(顧客の PDF に `<!--` が出ない)
        self.assertNotIn("<!-- appendix", keep)
        # **節が返る**(消えただけにならない)
        self.assertEqual(len(moved), 1)
        title, section = moved[0]
        self.assertEqual(title, "数の出どころ")
        self.assertIn("数の分母がどこから来たか", section)
        self.assertIn("崩れの合計", section)
        self.assertNotIn("<!-- appendix", section)

    def test_the_rest_of_the_body_is_untouched(self):
        keep, _ = EI.split_appendix_sections(md_of())
        for must in ("# 25 局で起きていたこと", "## ひとことで", "- 崩れは 79 回でした。",
                     "## 数え方", "- 固定の注。", "## 対応表 ― 何局目が、どのファイルか(本人用)", "| 1 | g01 |"):
            self.assertIn(must, keep)
        # **次の節を巻き込まない**(対応表が付録へ行ってしまわない)
        _, moved = EI.split_appendix_sections(md_of())
        self.assertNotIn("対応表", moved[0][1])
        self.assertNotIn("g01", moved[0][1])

    def test_no_tag_means_no_change(self):
        md = md_of().replace("<!-- appendix: 数の出どころ -->", "")
        keep, moved = EI.split_appendix_sections(md)
        self.assertEqual(moved, [])
        self.assertIn("数の分母がどこから来たか", keep)

    def test_tag_without_a_next_heading_takes_the_rest(self):
        """**黙って落とさない** ― 印の後に `## ` が無ければ文末までを節にする。"""
        md = "## 数え方\n\n<!-- appendix: 数の出どころ -->\n\n### 表\n\n| a |\n|---|\n| 1 |"
        keep, moved = EI.split_appendix_sections(md)
        self.assertEqual(len(moved), 1)
        self.assertIn("### 表", moved[0][1])
        self.assertNotIn("### 表", keep)

    def test_two_tags_move_two_sections(self):
        md = ("## 数え方\n\n<!-- appendix: 一つ目 -->\n\n### A\n\n## 次\n\n"
              "<!-- appendix: 二つ目 -->\n\n### B\n")
        keep, moved = EI.split_appendix_sections(md)
        self.assertEqual([t for t, _ in moved], ["一つ目", "二つ目"])
        self.assertNotIn("### A", keep)
        self.assertNotIn("### B", keep)
        # **節の見出しは本編に残る**(印は節の中身だけを移す)
        self.assertIn("## 数え方", keep)
        self.assertIn("## 次", keep)

    def test_the_note_for_the_writer_has_no_number(self):
        """書き手への注に**数字を書かない**(検査 1 と門が偽の苦情を出す。既知の型)。"""
        self.assertNotRegex(EI.APPENDIX_TAG_NOTE, r"\d")


if __name__ == "__main__":
    unittest.main(verbosity=2)
