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
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import board_draw as BD      # noqa: E402
import board_spec as BS      # noqa: E402

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




class CandidateDashIsOnePlaceTest(unittest.TestCase):
    """**第 1 候補の破線の型は 1 か所**(2026-09-29。司令塔の決定 (ア))。

    実測で **3 通り**あった: 本編の盤と凡例が `(3, 2)`・付録 3 の矢印が `(2.2, 1.6)`・
    付録 3 の打つ手の丸が `(2, 1.5)`。**同じ局面を本編と付録の両方に載せる作り**なので、
    同じものが違う書き方で出ると同じものと思えない(P-176 と同じ家族)。
    **凡例も同じ値**でなければ、凡例が盤の説明にならない。
    """

    # 破線を引くファイル。**凡例(`_util.py`)を入れるのが要点** ― 盤だけ直すと凡例が取り残される。
    FILES = ("board_draw.py", "_util.py", "render_direct.py")

    def test_d1_the_pattern_is_the_one_the_commander_chose(self):
        self.assertEqual(BD.DASH_CAND, (1.5, 1))

    def test_d2_every_dash_with_arguments_uses_the_one_place(self):
        """**引数つきの `setDash` は、この 3 本では必ず `*DASH_CAND`。**

        `ast` で呼び出しを見る(字面では、なぜ変えたかを書いたコメントの数字に当たる)。
        引数なしの `setDash()`(破線をやめる)は対象外 ― 値を持たないので写しにならない。
        """
        for name in self.FILES:
            with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
                tree = ast.parse(f.read())
            calls = [n for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "setDash" and n.args]
            self.assertTrue(calls, f"{name} に引数つきの setDash が無い(移し忘れか、対象の取り違え)")
            for call in calls:
                self.assertEqual(
                    [ast.unparse(a) for a in call.args], ["*DASH_CAND"],
                    f"{name} が破線の型を自分で持っている: {ast.unparse(call)}")

    def test_d3_the_two_other_files_bind_the_constant(self):
        """**写すのではなく束縛する**(`from board_draw import DASH_CAND`)。

        写せば、直しが片方だけに入る。**`ast` で import を見る** ―
        字面で探すと、説明のコメントに名前を書いただけで通る。
        `_util.py` は 1 行目に読み込みの細工が在るので、他の試験と同じく 1 行目を外して読む。
        """
        for name in ("_util.py", "render_direct.py"):
            src = read_text(os.path.join(HERE, name))
            if name == "_util.py":
                src = "\n".join(src.split("\n")[1:])
            tree = ast.parse(src)
            bound = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                     and (n.module or "") == "board_draw" for a in n.names}
            self.assertIn("DASH_CAND", bound,
                          f"{name} が board_draw から DASH_CAND を束縛していない(束縛は {sorted(bound)})")

    # **実測した軸の長さ**(pt。矢じるしの外に出ている線の長さ)。2026-09-29 に PDF のベクタから測った。
    # 本編の盤 = 10.8(11 局目 48 手目の第 1 候補)。付録 3 の 20 ページ目の 3 本 = 9.56・27.47・38.54。
    # **同じ手でも冊子によってマスの大きさが違う**ので、いちばん短いものを含めて並べる。
    SHAFTS_PT = (9.56, 10.8, 27.47, 38.54)
    # 直す前に在った 3 通りの破線の型(周期 = 和)。
    OLD_PATTERNS = ((3, 2), (2.2, 1.6), (2, 1.5))

    def test_d4_the_new_pattern_shows_more_dashes_than_every_old_one(self):
        """**どの古い型よりも、どの軸でも破線の周期が増えること。**

        「2 本しか見えない」が直った証拠を数で残す。いちばん短い軸(9.56pt)では
        (2.2, 1.6) の 2.5 周 → (1.5, 1) の 3.8 周、本編の 10.8pt では 2.2 周 → 4.3 周。
        **「4 本以上見えるか」は司令塔が目で確かめる**(この試験は周期の数までしか言えない ―
        見え方は数ではないので、ここで断定しない)。
        """
        new_period = sum(BD.DASH_CAND)
        for shaft in self.SHAFTS_PT:
            for old in self.OLD_PATTERNS:
                self.assertGreater(shaft / new_period, shaft / sum(old),
                                   f"軸 {shaft}pt で {old} より周期が増えていない")

    def test_d5_the_shortest_shaft_gets_at_least_three_cycles(self):
        """**いちばん短い軸(9.56pt)でも 3 周以上**。直す前は 2.5 周だった。

        下限を 3 にしたのは**実測の 3.8 周から少し下**に置いたもので、見え方の基準ではない
        (見え方は司令塔が目で決める)。型を粗く戻したらここが赤くなる。
        """
        self.assertGreaterEqual(min(self.SHAFTS_PT) / sum(BD.DASH_CAND), 3.0)

class HandWordIsOnePlaceTest(unittest.TestCase):
    """**持ち駒の語は 1 か所**(P-176。2026-09-29)。

    批評席 (a)(4 周目)が実物で挙げた: 同じ 12 局目 70 手目の局面で、
    本編「桂二 香 歩二」・付録 3「桂二　香一　歩二」。**1 枚のときに数を付けるかと、
    区切りの空白の幅**の 2 つが違っていた。**P-111 の家族**(4 つの実装が別々に組んでいた)。
    """

    def test_w1_one_piece_has_no_number(self):
        """**1 枚のときは数を付けない**(将棋の持ち駒の書き方)。"""
        self.assertEqual(BS.hand_word("香", 1), "香")
        self.assertEqual(BS.hand_word("香", 2), "香二")
        self.assertEqual(BS.hand_word("歩", 9), "歩九")

    def test_w2_ten_or_more_uses_digits(self):
        """10 枚以上は算用数字(漢数字の表は 1 桁しか持たない。歩は 18 枚まで在りうる)。"""
        self.assertEqual(BS.hand_word("歩", 10), "歩10")
        self.assertEqual(BS.hand_word("歩", 18), "歩18")

    def test_w3_zero_is_not_a_word(self):
        self.assertIsNone(BS.hand_word("香", 0))
        self.assertIsNone(BS.hand_word("香", -1))

    def test_w4_the_phrase_drops_none_and_says_nashi(self):
        self.assertEqual(BS.hands_phrase(["桂二", None, "香"]), "桂二 香")
        self.assertEqual(BS.hands_phrase([]), "なし")
        self.assertEqual(BS.hands_phrase([None]), "なし")

    def test_w5_the_sfen_parse_goes_through_the_one_place(self):
        """**SFEN から作る側も同じ 1 か所を通る**(1 枚は数なし)。"""
        _cells, hs = BD.parse_sfen("9/9/9/9/9/9/9/9/9 b 2NL2P 1")
        self.assertEqual(BS.hands_phrase(hs[True]), "桂二 香 歩二")

    def test_w6_all_four_renderers_call_the_one_place(self):
        """**4 つの実装が同じ 1 か所を呼ぶ**(写しが残っていれば、また書き方が分かれる)。

        **字面ではなく `ast` で呼び出しを見る**(説明のコメントに語を書くと字面の試験は当たる ―
        2026-09-29 に何度も踏んだ型)。
        """
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("board_draw.py", "render_direct.py", "render_whatif.py", "fig1.py"):
            with io.open(os.path.join(here, name), encoding="utf-8") as f:
                tree = ast.parse(f.read())
            calls = [n for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "hand_word"]
            self.assertTrue(calls, f"{name} が board_spec.hand_word を呼んでいない(写しが残っている)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
