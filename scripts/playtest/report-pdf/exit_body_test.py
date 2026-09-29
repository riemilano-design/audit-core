# -*- coding: utf-8 -*-
# `exit_body.py`(本編の md → 本人用・見本用の PDF)の試験。
#
# 【組版を回さない試験を主にする理由】この道具の危ない所は**組版の見た目ではなく、
# 印と盤の対応が黙ってずれること**(印が 1 つ落ちる・盤が 1 枚足りない・抜くページが別になる)。
# そこは reportlab を回さずに測れる。組版を通す 1 本だけ、実材料で別に測る(記録に残す)。
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_structure as CS  # noqa: E402
import exit_body as EB  # noqa: E402


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def function_strings(path, name):
    """`path` の関数 `name` の**中に書かれた文字列**(docstring は除く)。

    **ファイル全体を `assertNotIn` で見ると、自分の説明文を捕まえる。**
    2026-09-29 に同じ型を 2 回踏んだ(「`"対応表`」はエラーの文・「`"ah2"`」は
    「書き写さない」と書いた docstring)。**狙いは「判定が自分の文字列を持たない」こと**なので、
    見るのは関数の中だけにする。
    """
    tree = ast.parse(read_text(path))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                           and isinstance(fn.body[0].value, ast.Constant)) else fn.body
    return [n.value for b in body for n in ast.walk(b)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


class MarksTest(unittest.TestCase):
    def test_00_marks_come_back_in_order(self):
        md = ("ここ<!-- pos: 5/27 付録3 3 分 -->です。\n"
              "\n"
              "つぎ<!-- pos: 1/75 付録1 -->です。\n")
        marks = EB.marks_of(md)
        self.assertEqual([(m.appendix, m.game_no, m.ply, m.group) for m in marks],
                         [(3, 5, 27, "3 分"), (1, 1, 75, None)])

    def test_01_two_marks_on_one_line_are_both_read(self):
        """1 行に 2 つ ― **片方を落とすと盤が 1 枚足りない PDF が「できた」ことになる。**"""
        md = "A<!-- pos: 2/10 付録3 3 分 -->B<!-- pos: 3/12 付録3 3 分 -->\n"
        self.assertEqual(len(EB.marks_of(md)), 2)

    def test_02_a_broken_mark_falls(self):
        """形が崩れた印は落とす。**検査 7 も同じ形で落とすが、「はず」で通さない。**"""
        with self.assertRaises(EB.ExitBodyError):
            EB.marks_of("<!-- pos: これは壊れている -->\n")


class StripAndInsertTest(unittest.TestCase):
    MD = "ここが盤の場所<!-- pos: 5/27 付録3 3 分 -->です。\n"

    def test_03_the_mark_is_removed_from_the_text(self):
        """**P-123 の歯止め。**印が PDF に出ないのは**偶然**である ―
        `render_answer.inline_markup` は `menu`・`priority` の印だけを外し、`pos` の印は
        reportlab が「知らないタグ」として黙って捨てているだけ。書式が変われば顧客の文に出る。

        **この歯止めは今日の PDF の文字では観測できない**(実測 2026-09-29: 除去を外しても
        reportlab が捨てるので PDF の文字は変わらなかった)。だから門は**渡す文**に置く。
        """
        out = EB.strip_and_insert(self.MD, EB.marks_of(self.MD))
        self.assertNotIn("pos:", out)
        self.assertNotIn("<!--", out)
        self.assertIn("ここが盤の場所です。", out)

    def test_04_the_sentinel_lands_on_its_own_line_right_after(self):
        """目印は**その行の直後の、目印だけの行**。
        そうでないと `build_story` が目印だけの `Paragraph` を作らず、盤に入れ替えられない。
        """
        out = EB.strip_and_insert(self.MD, EB.marks_of(self.MD)).split("\n")
        self.assertEqual(out[0], "ここが盤の場所です。")
        self.assertEqual(out[2], EB.sentinel(0))

    def test_05_a_mark_on_a_table_row_falls(self):
        """**表の行に印があれば落とす。**表は連続する行を 1 つの `Table` にまとめるので、
        間に盤の行を挟むと**表が割れる**(黙って割らない)。
        """
        md = "| 局 | 手 |\n| --- | --- |\n| 5 | 27 |<!-- pos: 5/27 付録3 3 分 -->\n"
        with self.assertRaises(EB.ExitBodyError):
            EB.strip_and_insert(md, EB.marks_of(md))


class _FakeStyle:
    def __init__(self, name):
        self.name = name


class _FakeParagraph:
    """`Paragraph` の代わり。**様式の名前も持つ** ―
    対応表の見分けは「`## ` の行だけが `S_H2` になる」ことに依るので、
    様式を持たない偽物では**本文と見出しの区別が測れない**(変異試験で判明 2026-09-29)。
    """

    def __init__(self, text, style_name=None):
        self.text = text
        import render_answer as RA

        self.style = _FakeStyle(style_name or RA.S_BODY.name)


def heading(text):
    import render_answer as RA

    return _FakeParagraph(text, RA.S_H2.name)


class SwapTest(unittest.TestCase):
    def test_06_the_sentinel_is_replaced_by_the_board(self):
        board = object()
        story = [_FakeParagraph("本文"), _FakeParagraph(EB.sentinel(0)), _FakeParagraph("つづき")]
        out = EB.swap_boards(story, {0: board})
        self.assertIs(out[1], board)
        self.assertEqual(len(out), 3)

    def test_07_a_board_with_no_sentinel_falls(self):
        """**印 1 つに盤 1 つ。**数が合わなければ落ちる(盤を黙って捨てない)。"""
        story = [_FakeParagraph(EB.sentinel(0))]
        with self.assertRaises(EB.ExitBodyError):
            EB.swap_boards(story, {0: object(), 1: object()})

    def test_08_a_sentinel_with_no_board_falls(self):
        """**余分な目印を黙って捨てない。**

        はじめの見本(`[目印3]` と盤 `{0}`)では、数の照合の方が先に鳴るので
        **「盤が無い目印で落ちる」判定を外しても赤にならなかった**(校正で実測 2026-09-29)。
        **数がたまたま揃う形**で測る: 目印が 2 つ・盤は 1 つだが、
        差し替えられた番号の集合は `{0}` で盤と一致してしまう。
        """
        story = [_FakeParagraph(EB.sentinel(0)), _FakeParagraph(EB.sentinel(5))]
        with self.assertRaises(EB.ExitBodyError):
            EB.swap_boards(story, {0: object()})

    def test_09_a_sentinel_mixed_into_other_text_falls(self):
        """目印が他の文と同じ段落に入ったら落とす ― **制御文字が顧客の PDF に出る道**を閉じる。

        **数の照合では捕まらない形で測る**(校正で実測 2026-09-29): 混ざった段落のほかに
        まともな目印もあるので、番号の集合は盤と一致してしまう。
        それでも**制御文字が残った段落**が顧客の PDF に出るので落とす。
        """
        story = [_FakeParagraph("本文 " + EB.sentinel(0) + " つづき"),
                 _FakeParagraph(EB.sentinel(0))]
        with self.assertRaises(EB.ExitBodyError):
            EB.swap_boards(story, {0: object()})


class MappingSectionTest(unittest.TestCase):
    def test_10_the_heading_comes_from_the_gate_constants(self):
        """対応表の見分けは `check_structure.py` の `SECTIONS`・`MAPPING_ROLE` から引く。
        **見出しの文字を写さない** ― 写すと片方だけ直る。

        見本は**実物 2 件の見出し**(正本 §7): 4 人目「対応表 ― 何局目が、どのファイルか(本人用)」・
        3 人目 v3「対応表 ― 何局目が、どの対局か(本人用)」。
        """
        self.assertTrue(EB.mapping_heading_matches("対応表 ― 何局目が、どのファイルか(本人用)"))
        self.assertTrue(EB.mapping_heading_matches("対応表 ― 何局目が、どの対局か(本人用)"))
        self.assertFalse(EB.mapping_heading_matches("数え方"))
        self.assertFalse(EB.mapping_heading_matches("ひとことで"))
        # **語が途中に出るだけの文は見出しではない。**ここを試験していなかったため、
        # 「前方一致を『含む』に緩める」変異が赤にならなかった(校正で実測 2026-09-29)。
        self.assertFalse(EB.mapping_heading_matches("この対応表は本人用だけに入っています。"))

    def test_11_the_judgment_holds_no_string_of_its_own(self):
        """**見分ける関数の中に文字列が 1 つも無いこと。**

        はじめは「ファイル全体に `"対応表` が出ない」で見ようとしたが、**誤検出した** ―
        落ちたのは `"対応表の節が本編に無い(…)"` という**エラーの文**で、見出しの定数ではない。
        **狙いは「判定が自分の文字列を持たない」こと**なので、判定の関数だけを見る
        (エラーの文に語が出るのは構わない)。
        """
        strings = function_strings(os.path.join(HERE, "exit_body.py"), "mapping_heading_matches")
        head, contains = next((h, c) for role, h, c in CS.SECTIONS if role == CS.MAPPING_ROLE)
        self.assertNotIn(head, strings, "見出しの頭を写している")
        if contains is not None:
            self.assertNotIn(contains, strings, "見出しに含まれる語を写している")
        src = read_text(os.path.join(HERE, "exit_body.py"))
        # **判定そのものは `check_structure.heading_matches` に移した**(2026-09-29)。
        # `exit_gate.py` が P1〜P3 の節に同じ判定を要り、ここに残すと 2 か所になるため。
        # こちらが持つのは「どの役割か」だけ。
        self.assertIn("CS.heading_matches", src)
        self.assertIn("CS.MAPPING_ROLE", src)
        # 移した先でも文字列を写していないこと(表から引いていること)。
        moved = function_strings(os.path.join(HERE, "check_structure.py"), "heading_matches")
        self.assertNotIn(head, moved, "移した先で見出しの頭を写している")

    def test_12_the_role_exists_in_the_gate(self):
        """門の側に役割が在ること(消えたらこの道具の見分けが黙って何も一致しなくなる)。"""
        self.assertIn(CS.MAPPING_ROLE, [role for role, _h, _c in CS.SECTIONS])


class _FakeDoc:
    def __init__(self):
        self.page = 1
        self.afterFlowable = None


class RecorderTest(unittest.TestCase):
    def test_13_no_mapping_section_falls(self):
        doc = _FakeDoc()
        rec = EB.MappingPageRecorder(doc)
        rec._record(heading("ひとことで"))
        with self.assertRaises(EB.ExitBodyError):
            rec.pages_to_drop(1)

    def test_14_a_section_spanning_pages_is_allowed_and_all_are_dropped(self):
        """**差は 1 ページに固定しない**(司令塔の判断 2026-09-29・案 1)。

        対応表は分析の中身ではなく**顧客が自分の局を引く索引**で、**行数は局数に比例する**。
        実測(節がページ先頭から始まる場合): **25 行 = 1 ページ・26 行 = 2 ページ**。
        だから**索引が示すページを全部抜く**。
        **はじめは「2 ページにまたがれば落とす」にしていた** ― 25 局の顧客が出せないので、
        司令塔の判断で変えた(P-133)。
        """
        doc = _FakeDoc()
        doc.page = 4
        rec = EB.MappingPageRecorder(doc)
        rec._record(heading("対応表 ― 何局目が、どのファイルか(本人用)"))
        doc.page = 5
        rec._record(_FakeParagraph("つづきの行"))
        self.assertEqual(rec.pages_to_drop(5), [4, 5])

    def test_14b_a_section_that_does_not_reach_the_last_page_falls(self):
        """**節の後ろに本文があれば落とす。**

        固定を外したぶん、ここを見ないと**抜いたページに顧客が読むべき文が混ざる**。
        """
        doc = _FakeDoc()
        doc.page = 3
        rec = EB.MappingPageRecorder(doc)
        rec._record(heading("対応表 ― 何局目が、どのファイルか(本人用)"))
        with self.assertRaises(EB.ExitBodyError):
            rec.pages_to_drop(5)      # 本編は 5 ページあるのに節は 3 ページで終わっている

    def test_15_the_pages_are_the_ones_the_section_landed_on(self):
        """**ページ数では決めない**(「最後の 1 枚」にすると、対応表が最後でなくなった日に別の
        ページを黙って抜く)。節が載ったページを返す。
        """
        doc = _FakeDoc()
        doc.page = 5
        rec = EB.MappingPageRecorder(doc)
        rec._record(heading("対応表 ― 何局目が、どの対局か(本人用)"))
        rec._record(_FakeParagraph("表の中身"))
        self.assertEqual(rec.pages_to_drop(5), [5])

    def test_15b_a_body_paragraph_starting_with_the_word_is_not_the_heading(self):
        """**本文の段落を見出しと間違えない。**

        変異試験で見つけた**道具の穴**(2026-09-29): 記録する側はすべての flowable に
        見出しの判定を当てていたので、「対応表は本人用だけです」のように**始まる本文**があると
        そこから節が始まったことになり、**抜くページが前にずれる**(顧客に対応表が残る)。
        `build_story` は `## ` の行だけを `S_H2` にするので、**様式で絞る**。
        """
        doc = _FakeDoc()
        doc.page = 3
        rec = EB.MappingPageRecorder(doc)
        rec._record(_FakeParagraph("対応表は本人用だけに入っています。"))   # 本文の様式
        with self.assertRaises(EB.ExitBodyError):
            rec.pages_to_drop(5)   # まだ節は始まっていない
        doc.page = 5
        rec._record(heading("対応表 ― 何局目が、どのファイルか(本人用)"))
        self.assertEqual(rec.pages_to_drop(5), [5])

    def test_15c_the_heading_style_name_is_not_copied(self):
        """様式の名前は `render_answer.py` の `S_H2` から引く(`"ah2"` と書き写さない)。"""
        import render_answer as RA

        # **見るのは「様式の値」だけ。**`getattr(flowable, "style", …)` の属性名まで禁じると、
        # 狙い(値を写していないこと)から外れる(最初は空の一覧を求めて赤になった)。
        strings = function_strings(os.path.join(HERE, "exit_body.py"), "is_section_heading")
        self.assertNotIn(RA.S_H2.name, strings, "様式の名前を写している")
        self.assertIn("RA.S_H2.name", read_text(os.path.join(HERE, "exit_body.py")))

    def test_16_the_recorder_adds_no_flowable(self):
        """`exit_index.PageIndexRecorder` と同じ流儀: **flowable を 1 つも足さない**
        (足すと組版が変わる)。`afterFlowable` を差し替えるだけであること。
        """
        src = read_text(os.path.join(HERE, "exit_body.py"))
        tree = ast.parse(src)
        cls = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.ClassDef) and n.name == "MappingPageRecorder")
        # **docstring を落としてから見る。**落とさないと、`pages_to_drop` の説明文にある
        # 「`PageBreak` を差し込む」という**説明そのもの**を捕まえる(2026-09-29 に実際に赤になった)。
        # **検査は「動くコード」に当てる** ― 同日 4 度目の同型。
        def strip_docstrings(node):
            for n in ast.walk(node):
                body = getattr(n, "body", None)
                if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    del body[0]
            return node

        body = ast.dump(strip_docstrings(cls))
        for bad in ("Spacer", "PageBreak", "append(P("):
            self.assertNotIn(bad, body, f"記録する側が {bad} を足している")


class PageBreakTest(unittest.TestCase):
    """**対応表の前で改ページする**(司令塔の判断 2026-09-29・案 1)。

    改ページしないと、対応表の最初のページに**その前の節の文が残り**、
    そのページを抜くと顧客が読むべき文まで消える。
    **実測でもここが効いた**: 改ページ前は 25 行の対応表が 3〜4 ページにまたがり、
    改ページ後は 4 ページ目 1 枚に収まった(本人用 4 / 見本用 3)。
    """

    def test_16b_a_page_break_goes_in_front_of_the_heading(self):
        from reportlab.platypus import PageBreak

        story = [_FakeParagraph("本文"),
                 heading("対応表 ― 何局目が、どのファイルか(本人用)"),
                 _FakeParagraph("表")]
        out = EB.break_before_mapping(story)
        self.assertIsInstance(out[1], PageBreak)
        self.assertIs(out[2], story[1])
        self.assertEqual(len(out), 4)

    def test_16c_no_mapping_heading_falls(self):
        with self.assertRaises(EB.ExitBodyError):
            EB.break_before_mapping([_FakeParagraph("本文")])

    def test_16d_two_mapping_headings_fall(self):
        """**ちょうど 1 つ。**2 つあると、どちらから抜くかが決まらない。"""
        story = [heading("対応表 ― 何局目が、どのファイルか(本人用)"),
                 heading("対応表 ― 何局目が、どの対局か(本人用)")]
        with self.assertRaises(EB.ExitBodyError):
            EB.break_before_mapping(story)


class DropPagesTest(unittest.TestCase):
    def test_16e_dropping_zero_pages_falls(self):
        """**1 枚も抜かない指定は落とす** ― 対応表が付いたまま外へ出る。"""
        with self.assertRaises(EB.ExitBodyError):
            EB.drop_pages("dummy.pdf", "out.pdf", [])


class SharedJudgmentTest(unittest.TestCase):
    def test_17_the_position_check_is_not_reimplemented(self):
        """**印が材料に実在するかの照合は検査 7(`check_answer.check_answer`)がやる。**
        この道具が自分の照合を持つと、片方だけ通る道ができる。
        """
        src = read_text(os.path.join(HERE, "exit_body.py"))
        self.assertIn("CA.check_answer(", src)
        for copied in ("def prose_positions_of", "def direct_positions_of", "def check_pos_tags"):
            self.assertNotIn(copied, src, f"検査 7 の {copied} を写している")

    def test_18_the_mark_grammar_is_not_reimplemented(self):
        """印の文法も写さない(`check_answer.py` の `POS_TAG_RE`・`POS_INNER_RE` を使う)。"""
        src = read_text(os.path.join(HERE, "exit_body.py"))
        self.assertIn("CA.POS_TAG_RE", src)
        self.assertIn("CA.POS_INNER_RE", src)
        self.assertNotIn("re.compile(r\"<!--\\s*pos", src)


class SectionMarkTest(unittest.TestCase):
    """**節の印(`<!-- sec: 付録N/節 -->`)も自分で外す**(P-123 の家族)。"""

    def test_s1_the_section_mark_is_removed_from_the_text(self):
        """印が組版に渡る文から消えていること。

        reportlab が知らないタグとして黙って捨てているだけなので、**書式が変われば顧客の文に出る。**
        本編は `exit-candidates` が `exit_index.COVER_SECTIONS` から 3 つの印を必ず置くので、
        **外さない道が実際に通る**(校正で黙っていた ― 2026-09-29)。
        """
        import exit_render as ER

        body = "## 数え方\n\n- 25 局の形勢の流れ<!-- sec: 付録1/形勢の流れ -->\n"
        self.assertTrue(ER.SEC_TAG_RE.search(body))
        self.assertIsNone(ER.SEC_TAG_RE.search(ER.SEC_TAG_RE.sub("", body)))

    def test_s1b_strip_marks_removes_the_section_mark(self):
        """**組版に渡す文に節の印が残っていない。**

        `build()` の中に置いていたときは**外す行を消しても緑だった**(校正で実測 2026-09-29) ―
        材料が要る `build()` を回す試験が無かったため。番人ごと関数に切ったのでここで測れる。
        """
        body = "## 数え方\n\n- 25 局の形勢の流れ<!-- sec: 付録1/形勢の流れ -->\n"
        out = EB.strip_marks(body, [])
        self.assertNotIn("sec:", out)
        self.assertIn("25 局の形勢の流れ", out)

    def test_s2_the_guard_names_the_section_mark_too(self):
        """**取り除けていないときに落ちる番人**が、節の印も見ていること。

        番人が `POS_TAG_RE` だけを見ていると、節の印が残ったまま PDF になる。
        """
        src = read_text(os.path.join(HERE, "exit_body.py"))
        lines = src.split("\n")
        raise_at = next(i for i, line in enumerate(lines) if "印が取り除けていない" in line)
        # 番人の条件は raise の直前の `if` の行(複数行に折れていれば手前へ遡る)。
        cond = next(lines[i] for i in range(raise_at - 1, -1, -1) if lines[i].lstrip().startswith("if "))
        guard = "".join(lines[lines.index(cond):raise_at])
        self.assertIn("POS_TAG_RE", guard, guard)
        self.assertIn("SEC_TAG_RE", guard, guard)


class KeepsTheHeadingWithTheBoardTest(unittest.TestCase):
    """**見出しと盤を離さない**(D6 = P-150。2026-09-29)。

    1 周目の批評席が「2 つ目の局面は見出しだけで盤が次ページに送られており、
    1 ページ目では途切れています」と挙げた。封は「小さいもの(門にしない)」に置いていた。
    """

    class Para(object):
        def __init__(self, text, style_name="abody"):
            self.text = text
            self.style = type("S", (), {"name": style_name})()

    class Board(object):
        pass

    def test_d1_bold_only_line_is_recognized(self):
        """盤の見出しは `## ` の行ではないので**様式では見分けられない**(実測 2026-09-29)。"""
        self.assertTrue(EB.is_bold_only_line(self.Para("<b>16 局目 93 手目 ― …</b>")))
        self.assertTrue(EB.is_bold_only_line(self.Para("  <b><b>16</b> 局目</b>  ")))
        self.assertFalse(EB.is_bold_only_line(self.Para("盤は付録と同じく、本人を下にしています。")))
        self.assertFalse(EB.is_bold_only_line(self.Para("<b>太字</b>のあとに本文")))
        self.assertFalse(EB.is_bold_only_line(self.Board()))

    def test_d2_the_heading_and_the_board_become_one_flowable(self):
        from reportlab.platypus import KeepTogether
        board = self.Board()
        heading = self.Para("<b>16 局目 93 手目 ― …</b>")
        story = [self.Para("まえがき"), heading, self.Para(EB.sentinel(0))]
        out = EB.swap_boards(story, {0: board})
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[1], KeepTogether)
        self.assertEqual(out[1]._content, [heading, board])

    def test_d3_a_board_without_a_heading_is_left_alone(self):
        from reportlab.platypus import KeepTogether
        board = self.Board()
        story = [self.Para("ふつうの本文です。"), self.Para(EB.sentinel(0))]
        out = EB.swap_boards(story, {0: board})
        self.assertEqual(len(out), 2)
        self.assertNotIsInstance(out[1], KeepTogether)
        self.assertIs(out[1], board)

    def test_d4_the_count_check_still_holds(self):
        """**まとめても数の照合は残る**(印 1 つに盤 1 つ)。"""
        board = self.Board()
        story = [self.Para("<b>見出し</b>"), self.Para(EB.sentinel(0))]
        with self.assertRaises(EB.ExitBodyError):
            EB.swap_boards(story, {0: board, 1: self.Board()})


class LeadSentencesDoNotPromiseAllPagesTest(unittest.TestCase):
    """**束ねられる付録の前文は「全部並べる」と約束しない**(2026-09-29。P-152 の家族)。

    `render_direct.py`・`_mid.py` は `sys.argv` を読んで走るので import できない。**原文で見る。**
    """

    def test_d5_appendix3_does_not_say_it_lists_them_all(self):
        src = read_text(os.path.join(HERE, "render_direct.py"))
        self.assertNotIn("局面)を、実戦との差が大きい順に並べます。", src)
        self.assertIn("局面ありました。", src)
        # 2026-09-29(P-171): **「ここから先は、」も外した** ― 束ねると 6 ページ目の次は
        # 20 ページ目になる(4 周目の実物)ので、続きのページを約束して嘘になる。
        # **無いことは `ast` で見る**(`exit_render_test.NeighbourPromiseTest.test_n8`)―
        # ここで `assertNotIn` にすると、**なぜ外したかを書いたこのコメント自身**に当たる。
        self.assertIn("実戦との差が大きい順に並べています。", src)

    def test_d6_appendix1_does_not_say_from_the_next_page(self):
        src = read_text(os.path.join(HERE, "_mid.py"))
        self.assertNotIn("次のページから、形勢が大きく動いた", src)
        self.assertIn("形勢が大きく動いたのは", src)
        self.assertIn("一覧にまとめています", src)


class SinglePageHasNoPageNumberTest(unittest.TestCase):
    """**1 ページの文書にノンブルを出さない**(P-163。2026-09-29)。

    批評席 (a) が付録の表紙の「ページ 1 / 1」を挙げた。**読者に何も渡さない**どころか、
    「この冊子は 1 ページなのか」と読める(束ねた付録は 4 ページある)。
    **実際に組んで fitz で読む** ― 組版の中だけを見ると、直したつもりで届かない(P-159 の家族)。
    """

    def _render(self, md_text):
        import tempfile

        import fitz

        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "x.pdf")
            pages = EB.render_plain(md_text, out, "校正")
            doc = fitz.open(out)
            try:
                texts = [doc[i].get_text() for i in range(doc.page_count)]
            finally:
                doc.close()
            return pages, texts

    def test_d7_one_page_prints_no_page_number(self):
        pages, texts = self._render("# 表紙\n\n短い 1 段落です。\n")
        self.assertEqual(pages, 1)
        self.assertNotIn("ページ 1 / 1", "".join(texts))
        # **「ページ」の語ごと出ない**(「ページ 1 /」のような半端な形も出ない)。
        self.assertNotRegex("".join(texts), r"ページ\s*\d+\s*/")

    def test_d7b_two_pages_still_print_the_number_but_not_the_total(self):
        """**2 ページ以上では出る。**出なくなったら、顧客が何ページ目を見ているか分からない。

        **ただし総数は出さない**(P-166。2026-09-29)― 見本用は本人用からページを抜いたもので、
        **同じ組版が描いた「/ 5」を 4 ページの冊子が持っていた**(実測)。
        """
        md = "# 題\n\n" + "".join(f"{i} 行目の段落です。\n\n" for i in range(1, 121))
        pages, texts = self._render(md)
        self.assertGreater(pages, 1)
        joined = "".join(texts)
        self.assertIn("ページ 1", joined)
        self.assertIn(f"ページ {pages}", joined)
        # **「/ 総数」の形が 1 つも無いこと**(見本用が嘘の総数を持てなくなる)。
        self.assertNotRegex(joined, r"ページ\s*\d+\s*/")


# **`__main__` の塊はファイルの末尾に 1 つだけ**(P-181。2026-09-29)。
# 途中に置くと `unittest.main()` の `sys.exit` で**後ろのクラスが定義されず、直接実行で 1 本も走らない**
# (門の `discover` では走るので赤にならない ―「手元で回して OK だった」が嘘になる)。

class NoTagWordingTest(unittest.TestCase):
    """**印が 1 つも付かないときの語**(P-184。2026-09-29。5 周目の批評席 (a))。

    直す前は「特になし」で、席は「意味が取れません」と書いた ― **「調べていない」とも読める。**
    直した後は**印の一覧からその場で組む**(「取る・打つ・王手・捨て駒・引くのどれでもない」)ので、
    **印を足し引きしても語がずれない。**

    `render_direct.py` は `sys.argv` を読んで走るので import できない。
    **原文から `TAG_JP` と 3 つの定義だけを取り出して動かす**(字面で見るのではなく、**振る舞いで見る**)。
    """

    def piece(self):
        """`render_direct.py` から、この件に要る定義だけを取り出して動かす。"""
        import ast

        src = read_text(os.path.join(HERE, "render_direct.py"))
        tree = ast.parse(src)
        wanted_names = {"TAG_JP"}
        wanted_defs = {"no_tag_text", "tags_text_of"}
        picked = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and (t.id in wanted_names or t.id == "NO_TAG_TEMPLATE")
                    for t in node.targets):
                picked.append(node)
            elif isinstance(node, ast.FunctionDef) and node.name in wanted_defs:
                picked.append(node)
        self.assertEqual(len(picked), 4, f"取り出せた定義が 4 つでない: {len(picked)}")
        ns = {}
        exec(compile(ast.Module(body=picked, type_ignores=[]), "<render_direct>", "exec"), ns)
        return ns

    def test_t1_no_tag_says_which_marks_were_checked(self):
        ns = self.piece()
        self.assertEqual(ns["no_tag_text"](), "取る・打つ・王手・捨て駒・引くのどれでもない")
        self.assertEqual(ns["tags_text_of"]({}), ns["no_tag_text"]())

    def test_t2_the_wording_is_built_from_the_table(self):
        """**表から組む。**印を 1 つ減らすと語も変わる(語を別に書いていれば変わらない)。"""
        ns = self.piece()
        ns["TAG_JP"] = [("capture", "取る"), ("drop", "打つ")]
        self.assertEqual(ns["no_tag_text"](), "取る・打つのどれでもない")

    def test_t3_a_tagged_move_is_unchanged(self):
        """印が付く手の語は変えていない(直したのは「1 つも無いとき」だけ)。"""
        ns = self.piece()
        self.assertEqual(ns["tags_text_of"]({"capture": True}), "取る")
        self.assertEqual(ns["tags_text_of"]({"capture": True, "retreat": True}), "取る・引く")

    def test_t4_the_old_wording_is_gone(self):
        """**「特になし」が道具の文字定数に残っていないこと。**

        **docstring は除く**(なぜ変えたかを書いた説明文に当たるため ― この日 5 回踏んだ型)。
        """
        import ast

        src = read_text(os.path.join(HERE, "render_direct.py"))
        tree = ast.parse(src)
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                body = getattr(node, "body", None) or []
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                   and isinstance(body[0].value.value, str):
                    docs.add(id(body[0].value))
        hits = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and id(n) not in docs and "特になし" in n.value]
        self.assertEqual(hits, [], f"「特になし」が残っている: {hits}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
