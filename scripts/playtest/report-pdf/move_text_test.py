# -*- coding: utf-8 -*-
"""`move_text.py` ― 指し手の字の 1 か所(⑥ 束 3。2026-10-05)。

**振る舞い**(打・成・同・成駒の名・▲△)と、**写しではなく移動であること**(2 本の renderer が同じ名前を
`from move_text import …` で束縛し、自分では定義しない)を見る。字面ではなく `ast` で見る(説明のコメントに当たらない)。
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import board_spec as BS  # noqa: E402
import move_text as MT  # noqa: E402

MOVED = ("ZEN", "KAN", "PIECE", "PROM", "parse_sfen", "sq", "usi_squares", "piece_kanji", "move_kanji", "mark")
RENDERERS = ("render_direct.py", "render_whatif.py")


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def defined_names(tree):
    out = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            out |= {t.id for t in node.targets if isinstance(t, ast.Name)}
    return out


def bound_from(tree, module):
    return {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and (n.module or "") == module
            for a in n.names}


class MoveKanjiTest(unittest.TestCase):
    SFEN = "9/7b1/6p2/9/9/9/9/1P7/9 b P 1"

    def cells(self):
        cells, turn, hands = MT.parse_sfen(self.SFEN)
        return cells, turn, hands

    def test_m1_parse_sfen_reads_cells_turn_and_hands(self):
        cells, turn, hands = self.cells()
        self.assertEqual(turn, "b")
        self.assertEqual(hands, {"P": 1})
        self.assertEqual(cells, {(2, 2): "b", (3, 3): "p", (8, 8): "P"})

    def test_m2_drop_move_promotion_and_same_square(self):
        cells, _turn, _hands = self.cells()
        self.assertEqual(MT.move_kanji(cells, "P*4d", None), "４四歩打")
        self.assertEqual(MT.move_kanji(cells, "8h8g+", None), "８七歩成")
        self.assertEqual(MT.move_kanji(cells, "8h8g", None), "８七歩")
        self.assertEqual(MT.move_kanji(cells, "3c3d", None), "３四歩")
        # 直前の手と同じ升なら「同」。
        self.assertEqual(MT.move_kanji(cells, "2b2c", (2, 3)), "同　角")

    def test_m3_promoted_piece_names_come_from_the_table(self):
        cells = {(5, 5): "+R", (6, 6): "+p"}
        self.assertEqual(MT.piece_kanji("+R"), "竜")
        self.assertEqual(MT.move_kanji(cells, "5e5d", None), "５四竜")
        self.assertEqual(MT.move_kanji(cells, "6f6g", None), "６七と")
        self.assertEqual(MT.PROM, {"p": "と", "l": "杏", "n": "圭", "s": "全", "b": "馬", "r": "竜"})

    def test_m4_mark_is_the_person_regardless_of_side(self):
        self.assertEqual(MT.mark("b", True), "▲")
        self.assertEqual(MT.mark("w", True), "△")
        self.assertEqual(MT.mark("w", False), "▲")
        self.assertEqual(MT.mark("b", False), "△")

    def test_m5_ranks_are_bound_from_board_spec(self):
        self.assertIs(MT.RANKS, BS.RANKS)
        self.assertEqual(MT.sq("8h"), (8, 8))
        self.assertEqual(MT.usi_squares("P*4d"), (None, (4, 4)))
        self.assertEqual(MT.usi_squares("8h8g+"), ((8, 8), (8, 7)))


class MovedNotCopiedTest(unittest.TestCase):
    """**写しではなく移動。**2 本の renderer は 10 の名前を `move_text` から束縛し、自分では 1 つも定義しない。"""

    def test_m6_renderers_bind_every_moved_name(self):
        for name in RENDERERS:
            tree = ast.parse(read_text(os.path.join(HERE, name)))
            bound = bound_from(tree, "move_text")
            self.assertEqual(set(MOVED) - bound, set(), f"{name} が move_text から束縛していない名前がある")

    def test_m7_renderers_define_none_of_them(self):
        for name in RENDERERS:
            tree = ast.parse(read_text(os.path.join(HERE, name)))
            left = defined_names(tree) & set(MOVED)
            self.assertEqual(left, set(), f"{name} に定義が残っている(写しになる)")

    def test_m8_no_other_file_defines_move_kanji(self):
        """`def move_kanji` は report-pdf の中で `move_text.py` だけ(試験は除く)。"""
        owners = []
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py") or name.endswith("_test.py"):
                continue
            tree = ast.parse(read_text(os.path.join(HERE, name)))
            if "move_kanji" in defined_names(tree):
                owners.append(name)
        self.assertEqual(owners, ["move_text.py"])

    def test_m9_the_module_has_no_side_effects(self):
        """argv・環境変数・ファイルを読まない(⑥ が import する条件)。"""
        tree = ast.parse(read_text(os.path.join(HERE, "move_text.py")))
        src_names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        self.assertNotIn("argv", src_names)
        self.assertNotIn("environ", src_names)
        calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertNotIn("open", calls)
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
                  {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertEqual(imports, {"board_spec"})


if __name__ == "__main__":
    unittest.main()
