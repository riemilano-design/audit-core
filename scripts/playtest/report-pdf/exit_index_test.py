# -*- coding: utf-8 -*-
# `exit_index.py` の試験。いまは**付録へ回す節の印**(器の単独束 C-4。2026-09-30)だけを見る。
#
# 【この印の危ない所】**片側だけ効くこと。**本編から外れたのに付録に組まれなければ、
# 顧客が読む表が**どこにも出ない**。だから印の切り出しは「本編から消える」と「節が返る」の
# **両方**を見る(組版の両側は `check_structure` の検査が見る)。
import io
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


class UnanswerablePastGamesTest(unittest.TestCase):
    """**F-2。答えられなかった問いの文**(人間が書いた。2026-10-01)。

    【顧客の PDF にどう出るか】節「お預かりした問い」の中に**この 1 文がそのまま**出る。
    【ここで字で留める理由】**人間が書いた文**なので、言い換え・要約・語の差し替えが
    起きたら赤にする。長さも人間が数えた値(80)で留める。
    """

    # **人間が書いた文そのまま**(25 局)。docs/AUTOMATION_STATUS_2026-09-26.md に写しが在る。
    WANT_AT_25 = ("今回お預かりした 25 局だけでは、「普段と異なる戦略だった場合の効果」は"
                  "確認できませんでした。「普段」を判定するには、"
                  "今回とは別の過去棋譜との比較が必要です。")

    def test_u1_the_sentence_is_pinned_character_by_character(self):
        """**字で留める。**替えるには人間の判断が要る。"""
        self.assertEqual(EI.unanswerable_past_games(25), self.WANT_AT_25)

    def test_u2_the_length_is_counted_with_the_spaces_in(self):
        """**空白を含めて 80 文字**(人間が数えた側)。空白を落とすと 78 ―
        門は空白を含めて数えるので、**78 では比べられなくなる。**"""
        got = EI.unanswerable_past_games(25)
        self.assertEqual(len(got), 80)
        self.assertEqual(len(got.replace(" ", "")), 78)
        # **数え方を取り違えた変異が落ちる**(78 を 80 と書いた側)。
        self.assertNotEqual(len(got), 78)

    def test_u3_the_pinned_length_is_the_number_the_human_wrote(self):
        """定数も字で留める。**近くの数と同じにしない**(78・門の 200・見込みの 156 と
        取り違えない)。"""
        self.assertEqual(EI.UNANSWERABLE_PAST_GAMES_CHARS, 80)
        self.assertEqual(EI.UNANSWERABLE_PAST_GAMES_MEASURED_AT_GAMES, 25)
        for near in (4, 5, 25, 78, 156, 200, 240):
            self.assertNotEqual(EI.UNANSWERABLE_PAST_GAMES_CHARS, near)
        # **定数と実物が一致**(どちらかだけ動かした変異が落ちる)。
        self.assertEqual(
            len(EI.unanswerable_past_games(EI.UNANSWERABLE_PAST_GAMES_MEASURED_AT_GAMES)),
            EI.UNANSWERABLE_PAST_GAMES_CHARS)

    def test_u4_the_game_count_comes_from_the_material(self):
        """**局数は渡した値が入る**(値で焼く変異が落ちる)。"""
        self.assertIn("今回お預かりした 20 局だけでは", EI.unanswerable_past_games(20))
        self.assertNotIn("25", EI.unanswerable_past_games(20))
        # 局数が 1 桁変われば長さも変わる(型が効いていることの裏)。
        self.assertEqual(len(EI.unanswerable_past_games(100)), 81)

    def test_u5_the_word_the_human_chose_is_not_swapped(self):
        """**「戦略」のまま**(顧客の字の「戦型」に替えない ― 人間の決定 2026-10-01)。"""
        got = EI.unanswerable_past_games(25)
        self.assertIn("普段と異なる戦略だった場合の効果", got)
        self.assertNotIn("戦型", got)

    def test_u6_the_held_word_appears_here_on_purpose(self):
        """**「普段」がこの文に出るのは正しい** ― 人間が**判定できないものとして**使っている。
        「普段」を文書全体の黒名簿にした変異が、ここで赤くなる。"""
        got = EI.unanswerable_past_games(25)
        self.assertEqual(got.count("普段"), 2)
        self.assertIn("「普段」を判定するには", got)

    def test_u7_the_sentence_says_what_is_missing(self):
        """**答えられない理由と、要るものを書く**(「答えなかった」で終わらせない)。"""
        got = EI.unanswerable_past_games(25)
        self.assertIn("確認できませんでした", got)
        self.assertIn("今回とは別の過去棋譜との比較が必要です", got)

    def test_u8_a_missing_game_count_falls_instead_of_printing_a_default(self):
        """**局数が数でなければ落ちる**(既定値を入れない・「None 局」と印字しない)。"""
        for bad in (None, 0, -1, True, "25", 25.0):
            with self.assertRaises(ValueError, msg=repr(bad)):
                EI.unanswerable_past_games(bad)

    def test_u9_the_sentence_fits_the_gate(self):
        """**⑧ の門(G-7)に収まる。**節の持ち分は 200 文字で、この文は 80 文字。"""
        import check_structure as CS
        got = EI.unanswerable_past_games(25)
        self.assertLessEqual(len(got), CS.MAX_QUESTION_SECTION_CHARS)
        # **門が数えるのと同じ側で測る**(節に置いて数え直す)。
        md_text = "\n".join(["# 対局後診断", "", "## ひとことで", "", "- 数。", "",
                             "## お預かりした問い", "", got, "", "## 数え方", "", "(注)"])
        body = CS.question_section_body(md_text)
        self.assertEqual(body, got)
        self.assertEqual(len(body), 80)

    def test_u10_the_sentence_lives_in_one_place(self):
        """**文はリポジトリで 1 か所。**`report-pdf` の道具(試験を除く)を見て、
        型が**1 回だけ**在ることを確かめる ― 写しを置いたら落ちる。"""
        # **型のうち、局数の穴を含まない後半**で探す(前半は型なので字が違う)。
        fragment = "「普段と異なる戦略だった場合の効果」は"
        found = []
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py") or name.endswith("_test.py"):
                continue
            text = io.open(os.path.join(HERE, name), encoding="utf-8").read()
            n = text.count(fragment)
            if n:
                found.append((name, n))
        self.assertEqual(found, [("exit_index.py", 1)], found)


if __name__ == "__main__":
    unittest.main(verbosity=2)
