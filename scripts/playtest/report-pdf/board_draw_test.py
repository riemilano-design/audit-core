# -*- coding: utf-8 -*-
# `board_draw.py`(盤を描く道具)の試験。
#
# 【この試験が守るもの】**様式を `_head.py` から借りないこと。**
# もとの `Board.draw` は `INK`・`RED`・`BG`・`LINE`・`MUTED`・`FONT` を連結の前の名前で借りていて、
# そのまま切り出すと `NameError: INK` で落ちた(実測 2026-09-29)。
# 借りる形に戻ると、**import できるはずのモジュールが import で落ちる**か、
# **連結されたときだけ動く**という分かりにくい状態に戻る。
#
# 【数え上げにしない】借りうる名前を列挙するのではなく、
# **モジュールの外から来る名前を全部挙げて、許した集合に入っているかを見る。**
# 数え上げは必ず漏れる(§40 の家族。P-124 で AST でも同じ間違いをした)。
import ast
import builtins
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import board_draw as BD

HERE = os.path.dirname(os.path.abspath(__file__))


def read_text(path):
    """**開いたファイルを閉じる**(`open(...).read()` は `ResourceWarning` を出す ― P-127)。"""
    with open(path, encoding="utf-8") as f:
        return f.read()
STYLE = BD.BoardStyle(ink="#000000", red="#ff0000", bg="#ffffff",
                      line="#cccccc", muted="#888888", font="Helvetica")
# 初期局面(本人が先手)
SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"


def external_names(path):
    """モジュールが外から借りている名前を全部挙げる(import と組み込みは除く)。"""
    src = read_text(path)
    tree = ast.parse(src)
    defined = set(dir(builtins))
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(n.name)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            defined.add(n.id)
        elif isinstance(n, ast.arg):
            defined.add(n.arg)
        elif isinstance(n, ast.alias):
            defined.add((n.asname or n.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name:
            defined.add(n.name)
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return sorted(used - defined)


class DoesNotBorrowStyleTest(unittest.TestCase):
    def test_00_board_draw_borrows_no_name_from_outside(self):
        """**外から借りている名前が 1 つも無いこと。**

        様式(`INK` など)を借りると、この一覧に現れる。
        **借りうる名前を列挙するのではなく、外から来る名前を全部見る** ― 数え上げは漏れる。
        """
        self.assertEqual(external_names(os.path.join(HERE, "board_draw.py")), [],
                         "board_draw.py が外の名前を借りている(様式は BoardStyle で受ける)")

    def test_01_the_checker_catches_a_borrowed_name(self):
        """**校正**: 借りた名前を、この検査が本当に見つけるか。"""
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("def g():\n    return INK\n")
            path = f.name
        self.addCleanup(os.unlink, path)
        self.assertEqual(external_names(path), ["INK"])

    def test_02_style_is_required(self):
        """様式は**引数**。渡さなければ落ちる(既定値でこっそり描かない)。"""
        with self.assertRaises(TypeError):
            BD.Board(SFEN, True)


class DrawsTest(unittest.TestCase):
    def test_03_board_draws_with_the_given_style(self):
        """渡した様式で実際に描けること(PDF が 1 ページできる)。"""
        import tempfile
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate
        out = os.path.join(tempfile.mkdtemp(), "b.pdf")
        SimpleDocTemplate(out, pagesize=A4).build([BD.Board(SFEN, True, STYLE)])
        self.assertTrue(os.path.getsize(out) > 0)

    def test_04_parse_sfen_reads_the_initial_position(self):
        """`parse_sfen` が初期局面を読めること(移した先でも同じ)。

        返るのは **`(筋, 段) → (駒の名, 先手か)` の辞書**と、持ち駒
        (`{True: [先手], False: [後手]}`)。**成りは旗ではなく駒の名に入る**(`PROM` が別名を持つ)。

        **私はこの形を 2 回思い込みで書き、2 回落ちた**(2026-09-29): 1 回目は 9×9 の入れ子だと思い、
        2 回目は 2 つ目の要素を「成っているか」だと思った。**実物を印字してから書き直した。**
        """
        cells, hands = BD.parse_sfen(SFEN)
        self.assertEqual(len(cells), 40, "初期局面の駒は 40 枚")
        self.assertEqual(cells[(5, 9)], ("玉", True), "先手(本人)の玉が 5 九")
        self.assertEqual(cells[(5, 1)], ("玉", False), "後手の玉が 5 一")
        self.assertEqual(hands, {True: [], False: []}, "初期局面に持ち駒は無い")

    def test_05_usi_squares_reads_a_drop(self):
        """打つ手は「元の升」を持たない(`None`)。"""
        frm, to = BD.usi_squares("P*5e")
        self.assertIsNone(frm)
        self.assertEqual(to, (5, 5))


class UtilIsAThinWrapperTest(unittest.TestCase):
    def test_06_util_does_not_define_its_own_board(self):
        """`_util.py` は**薄い包み**で、盤の描き方を自分で持たないこと。

        持つと **P-111 が 4 実装に戻る**(いま 3 ― `fig1`・`render_direct`・`render_whatif`)。
        """
        src = open(os.path.join(HERE, "_util.py"), encoding="utf-8").read()
        tree = ast.parse("\n".join(src.split("\n")[1:]))   # 1 行目は `_data_dir` を要る読み込み
        boards = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "Board"]
        self.assertEqual(len(boards), 1, "_util.py の Board が 1 つでない")
        bases = [ast.unparse(b) for b in boards[0].bases]
        self.assertEqual(bases, ["board_draw.Board"],
                         f"_util.py の Board が board_draw を継いでいない: {bases}")
        self.assertNotIn("def draw", ast.unparse(boards[0]),
                         "_util.py の Board が自分で描いている(薄い包みでない)")

    def test_07_util_does_not_redefine_the_arrow_colours(self):
        """矢印の 2 色は `board_draw.py` の 1 か所。**`_util.py` が定義し直していないこと。**

        2026-09-29 に `_util.py` から移した(あちらは `build.sh` の断片で import できないため、
        写せば `Board` を移した意味が薄れる)。**定義し直すと、直しが片方だけに入る。**
        `Legend` は `_util.py` に残っているので、**束縛(import)は在ってよい。**
        """
        src = read_text(os.path.join(HERE, "_util.py"))
        tree = ast.parse("\n".join(src.split("\n")[1:]))
        assigned = [t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name)]
        for name in ("COL_PLAYED", "COL_CAND"):
            self.assertNotIn(name, assigned, f"_util.py が {name} を定義し直している")
        self.assertIn("from board_draw import COL_CAND, COL_PLAYED", src,
                      "board_draw からの束縛が無い")


if __name__ == "__main__":
    unittest.main(verbosity=2)
