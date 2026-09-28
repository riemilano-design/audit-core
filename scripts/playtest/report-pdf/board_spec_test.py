# -*- coding: utf-8 -*-
# `board_spec.py`(盤に渡す値の判断)の試験。
#
# 【なぜこの試験が要るか】**判断を写すと 1 手ずれ、ずれても試験は通ってしまう** ―
# 材料と PDF の両方が同じ写し間違いで揃うため。だから**判断そのものを試験で固定**し、
# **写しが戻っていないこと**も機械で見る(下の `NoCopyTest`)。
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ast

import board_spec as BS

HERE = os.path.dirname(os.path.abspath(__file__))


def read_text(path):
    """**開いたファイルを閉じる**(`open(...).read()` は `ResourceWarning` を出す ― P-127)。"""
    with open(path, encoding="utf-8") as f:
        return f.read()
SFENS = ["s0", "s1", "s2", "s3", "s4"]     # 0 件目が初期局面
MOVES = ["m1", "m2", "m3", "m4"]           # moves[i] が sfens[i] → sfens[i+1]

# **付録 1 の判断を共有するファイル。**ここに挙げたものは `sfens` を自分で引いてはいけない。
# `render_direct.py`・`render_whatif.py` は付録 2・3 の**別の判断**なので入れない。
SHARE_JUDGMENT = ("_mid.py", "render_direct.py", "exit_body.py")


def board_spec_names(tree):
    """そのファイルが `board_spec` に付けた名前を **import 文から**集める。

    返り値: (モジュールに付いた名前の集合, `board_spec` から直に持ってきた名前の集合)。
    **列挙ではなく解決** ― `as` の別名を手で並べると、次の別名で黙って漏れる。
    """
    module_names, direct_names = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "board_spec":
                    module_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "board_spec":
                for alias in node.names:
                    direct_names.add(alias.asname or alias.name)
    return module_names, direct_names


def sfens_reaches(source):
    """**`sfens` に手を伸ばしている式**の行番号を AST で拾う。

    【方式を反転させた理由(独立監査の REVISE・2026-09-29)】
    はじめは「危ない形を数え上げる」書き方にしていた。独立監査が**6 つの抜け道**を実測で見つけた:
    関数の引数で渡して中で引く / `.get("sfens")` / タプル代入 / セイウチ / 属性代入 / 内包表記の束縛。
    **どれも悪意ではなく普通のリファクタで再発する**(このリポジトリはローカルのヘルパー関数を多用する)。
    **数え上げは必ず漏れる** ― §40 の家族(手で並べた一覧は代表だけになる)。

    だから**反転した**: **`sfens` に手を伸ばす式はすべて拾い、
    `board_spec.<なにか>(…)` の引数として直接渡しているものだけを許す。**
    いま正当な出現は `_mid.py` の `board_spec.scene_spec(s_, k["sfens"], k["moves"])` 1 か所だけ。

    拾う形: `X["sfens"]`(添字)と `X.get("sfens")`(呼び出し)。
    **`.get` も拾う** ― 監査は「この方式でも捕まらない」と書いたが、
    **拾う側に足せば閉じる**ので、対象外にせず閉じた。

    【別名の import を、そのファイルの import 文から解く(P-124 の残余 b)】
    `import board_spec as BS` と書いたファイルは、許可の側が名前 `board_spec` しか見ていなかったため
    **正しい受け渡しまで赤になっていた**(`exit_body.py` を書いて実際に赤を見た。2026-09-29)。
    直し方は **`as` の別名を列挙しない** ― 列挙は必ず漏れる(§40 の家族)。
    **そのファイルの `import` 文を AST で読み、`board_spec` を指す名前を集める。**
    - `import board_spec` / `import board_spec as BS` → その名前の**属性呼び出し**を許す
    - `from board_spec import fork_spec` / `… as fs` → その名前の**素の呼び出し**を許す
    `board_spec` を import していないファイルでは、集合が空になり**何も許されない**(いままで通り)。
    """
    tree = ast.parse(source)
    allowed, reaches = set(), []
    module_names, direct_names = board_spec_names(tree)

    def is_board_spec_call(node):
        f = node.func
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            return f.value.id in module_names
        return isinstance(f, ast.Name) and f.id in direct_names

    def reaches_sfens(node):
        if isinstance(node, ast.Subscript):
            sl = node.slice
            return isinstance(sl, ast.Constant) and sl.value == "sfens"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get" and node.args:
            a = node.args[0]
            return isinstance(a, ast.Constant) and a.value == "sfens"
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and is_board_spec_call(node):
            for arg in node.args + [kw.value for kw in node.keywords]:
                if reaches_sfens(arg):
                    allowed.add(id(arg))
        if reaches_sfens(node):
            reaches.append(node)
    return sorted({n.lineno for n in reaches if id(n) not in allowed})


class MoveSceneTest(unittest.TestCase):
    def test_00_move_scene_is_the_position_before_the_move(self):
        """本人が指した場面は**指す前**の局面(`sfens[ply - 1]`)。

        `sfens[ply]` にすると **1 手先**を見せることになり、
        「この手を指す前にどう見えていたか」という本編の文と盤が食い違う。
        """
        spec = BS.scene_spec({"type": "move", "ply": 3}, SFENS, MOVES)
        self.assertEqual(spec["sfen"], "s2")
        self.assertEqual(spec["kind"], "move")

    def test_01_move_scene_passes_no_usi(self):
        """指す前の局面なので、動かした升の色づけ(`usi`)は渡さない ― 矢印で示す。"""
        spec = BS.scene_spec({"type": "move", "ply": 3}, SFENS, MOVES)
        self.assertIsNone(spec["usi"])
        self.assertTrue(spec["wants_arrows"])


class OpponentSceneTest(unittest.TestCase):
    def test_02_other_scene_is_the_position_after_the_move(self):
        """それ以外の場面は**相手が指した後**の局面(`sfens[ply]`)。"""
        spec = BS.scene_spec({"type": "eval", "ply": 3}, SFENS, MOVES)
        self.assertEqual(spec["sfen"], "s3")
        self.assertEqual(spec["kind"], "opponent")

    def test_03_other_scene_passes_the_move_that_led_there(self):
        """`usi = moves[ply - 1]`(その局面に至った手)。赤い升が相手の手になる。"""
        spec = BS.scene_spec({"type": "eval", "ply": 3}, SFENS, MOVES)
        self.assertEqual(spec["usi"], "m3")
        self.assertFalse(spec["wants_arrows"])


class ClampTest(unittest.TestCase):
    def test_04_ply_is_clamped_to_the_last_position(self):
        """**`ply` は `len(sfens) - 1` で切り詰める**(既存の `min(...)`)。

        切り詰めを外すと、終局の直後を指す場面で添字が範囲外になる。
        """
        spec = BS.scene_spec({"type": "eval", "ply": 99}, SFENS, MOVES)
        self.assertEqual(spec["ply"], len(SFENS) - 1)
        self.assertEqual(spec["sfen"], SFENS[-1])


class FallsTest(unittest.TestCase):
    """**材料が足りないときは落ちる。黙って飛ばさない。**"""

    def test_05_empty_sfens(self):
        with self.assertRaises(BS.BoardSpecError):
            BS.scene_spec({"type": "move", "ply": 1}, [], MOVES)

    def test_06_scene_without_ply(self):
        with self.assertRaises(BS.BoardSpecError):
            BS.scene_spec({"type": "move"}, SFENS, MOVES)

    def test_07_ply_below_one(self):
        with self.assertRaises(BS.BoardSpecError):
            BS.scene_spec({"type": "move", "ply": 0}, SFENS, MOVES)

    def test_08_moves_too_short(self):
        with self.assertRaises(BS.BoardSpecError):
            BS.scene_spec({"type": "eval", "ply": 3}, SFENS, ["m1"])


class SideTest(unittest.TestCase):
    def test_09_user_sente_from_patient_data(self):
        """`_mid.py` と同じ判定(`games[].side`)。"""
        self.assertTrue(BS.user_sente("先手"))
        self.assertFalse(BS.user_sente("後手"))

    def test_10_user_sente_from_sfens_record(self):
        """付録 3 側と同じ判定(`sfens.json` の `side`。`"gote"` なら本人が後手)。"""
        self.assertFalse(BS.user_sente_from_sfens({"side": "gote"}))
        self.assertTrue(BS.user_sente_from_sfens({"side": "sente"}))


class Appendix3Test(unittest.TestCase):
    """付録 3 の盤の判断。**材料の `sfen` は使わない。`sfens.json` から引く。**

    理由は `render_direct.py` 22〜26 行 ― 材料の `sfen` は「本人 = 先手」に正規化された記録で、
    **そのまま描くと後手の局で盤が逆になる。**
    私は最初「材料が SFEN を持つので `sfens.json` は要らない」と書いて間違えた(2026-09-29)。
    """

    REC = {"side": "sente", "sfens": ["s0", "s1", "s2", "s3"], "moves": ["m1", "m2", "m3"]}
    GOTE = {"side": "gote", "sfens": ["s0", "s1", "s2", "s3"], "moves": ["m1", "m2", "m3"]}

    def test_17_fork_is_the_position_before_the_move(self):
        """分かれ道は **`sfens[dply - 1]`**(指す前)。`dply` にすると 1 手先になる。"""
        spec = BS.fork_spec({"displayPly": 3}, self.REC)
        self.assertEqual(spec["sfen"], "s2")
        self.assertEqual(spec["ply"], 3)

    def test_18_final_is_the_last_position(self):
        """最終局面は **`sfens[-1]`**。**手数は `entries[].moves`**(`displayPly` ではない)。"""
        spec = BS.final_spec({"moves": 119}, self.REC)
        self.assertEqual(spec["sfen"], "s3")
        self.assertEqual(spec["ply"], 119)

    def test_19_orientation_comes_from_the_sfens_record(self):
        """向きは **`sfens.json` の `side`**(付録 1 の `games[].side` とは別の材料・別の規則)。"""
        self.assertFalse(BS.fork_spec({"displayPly": 3}, self.REC)["mirrored"])
        self.assertTrue(BS.fork_spec({"displayPly": 3}, self.GOTE)["mirrored"])
        self.assertTrue(BS.fork_spec({"displayPly": 3}, self.REC)["user_sente"])
        self.assertFalse(BS.fork_spec({"displayPly": 3}, self.GOTE)["user_sente"])

    def test_19b_a_ply_out_of_range_falls(self):
        """**範囲の外なら落ちる。**前は `sfens[dply - 1]` を直に引いていたので、
        `dply` が 0 なら python の負の添字で**黙って最終局面に回り込んでいた**
        (2026-09-29 に `board_spec` へ寄せたときに閉じた振る舞いの変化)。
        """
        rec = {"sfens": ["s0", "s1", "s2"], "side": "sente"}
        with self.assertRaises(BS.BoardSpecError):
            BS.fork_spec({"kifuId": "g1", "displayPly": 0}, rec)
        with self.assertRaises(BS.BoardSpecError):
            BS.fork_spec({"kifuId": "g1", "displayPly": 99}, rec)

    def test_20_material_sfen_is_never_used(self):
        """**材料が `sfen` を持っていても使わない。**持っていても `sfens.json` の値が出ること。"""
        answer = {"displayPly": 3, "sfen": "正規化されたので使ってはいけない"}
        self.assertEqual(BS.fork_spec(answer, self.REC)["sfen"], "s2")
        entry = {"moves": 119, "sfen": "正規化されたので使ってはいけない"}
        self.assertEqual(BS.final_spec(entry, self.REC)["sfen"], "s3")

    def test_21_missing_material_falls(self):
        """材料が足りなければ落ちる。黙って飛ばさない。"""
        for bad in ({}, {"side": "sente", "sfens": []}):
            with self.assertRaises(BS.BoardSpecError):
                BS.fork_spec({"displayPly": 1}, bad)
        with self.assertRaises(BS.BoardSpecError):
            BS.fork_spec({}, self.REC)
        with self.assertRaises(BS.BoardSpecError):
            BS.final_spec({}, self.REC)
        with self.assertRaises(BS.BoardSpecError):
            BS.fork_spec({"displayPly": 99}, self.REC)


class NoCopyTest(unittest.TestCase):
    """**判断の写しが戻っていないか**を機械で見る(写しは片方だけ直る)。"""

    def test_11_mid_calls_the_shared_judgment(self):
        src = open(os.path.join(HERE, "_mid.py"), encoding="utf-8").read()
        self.assertIn("board_spec.scene_spec(", src, "_mid.py が共通の判断を呼んでいない")

    def test_12_no_sfens_subscript_outside_the_shared_judgment(self):
        """**`sfens` を添字で引く式が、判断を共有する側に無いこと**を AST で見る。

        文字列一致では**変数名を変えた再導入**(`idx = k["sfens"]; idx[ply]`)を捕まえられない
        ― 独立監査が設計の弱さとして挙げた(2026-09-29、P-124)。
        **同型は既にある**: `exit_index.py` が「reportlab・fitz・pypdf を import しない」を
        AST で固定している。新しい仕組みではなく、その型を 1 本増やしたもの。

        **範囲は `SHARE_JUDGMENT` の 3 本**(`_mid.py`・`render_direct.py`・後半の `exit_body.py`)。
        **`render_direct.py` は 2026-09-29 に範囲へ入れた** ― 司令塔の判断で、付録 3 の
        「どの局面を盤に渡すか」も `board_spec.py` の 1 か所にした(P-111 は「どう描くか」の話で、
        こちらは「どの局面を渡すか」なので別物、という理由)。入れる前に赤を見ている(旧 499・562・639 行)。
        `render_whatif.py` は範囲外 ― **付録 2 は正本の束に入っていない**(P-129・P-130)。
        """
        for base in SHARE_JUDGMENT:
            path = os.path.join(HERE, base)
            if not os.path.exists(path):
                continue    # 後半が来る前は exit_body.py が無い(下の test_13 が「来たら見る」を保つ)
            found = sfens_reaches(read_text(path))
            self.assertEqual(found, [],
                             f"{base} が sfens を自分で添字で引いている(行 {found})"
                             f" ― 判断は board_spec.scene_spec() だけが持つ")

    def test_13_the_share_list_is_not_empty_and_names_exist(self):
        """**範囲の一覧が空にならないこと。**空にすれば test_12 は黙って通る。

        `_mid.py`・`render_direct.py` は必ず在るので、一覧から外れたら赤になる
        (`exit_body.py` は後半が来るまで無いので、ここでは押さえない ― test_12 が「来たら見る」を保つ)。
        """
        for base in ("_mid.py", "render_direct.py"):
            self.assertIn(base, SHARE_JUDGMENT)
            self.assertTrue(os.path.exists(os.path.join(HERE, base)), base)

    def test_14_the_check_catches_every_bypass_the_audit_found(self):
        """**校正**: 独立監査が実測で見つけた**6 つの抜け道**を、いまの検査が捕まえるか。

        はじめの書き方(危ない形を数え上げる)はこの 6 つを全部素通りしていた。
        **数え上げは必ず漏れる**ので許可一覧に反転した ― §40 の家族。
        **検査そのものを既知の正解で測る。**
        """
        bypasses = {
            "関数の引数で渡して中で引く":
                'def h(seq, p):\n    return seq[p]\ndef f(k, ply):\n    return h(k["sfens"], ply)\n',
            "`.get` 経由": 'def f(k, ply):\n    return k.get("sfens")[ply]\n',
            "タプル代入": 'def f(k, ply):\n    idx, other = k["sfens"], 1\n    return idx[ply]\n',
            "セイウチ": 'def f(k, ply):\n    return (idx := k["sfens"])[ply]\n',
            "属性代入": 'class C:\n    def f(self, k, ply):\n        self.idx = k["sfens"]\n        return self.idx[ply]\n',
            "内包表記の束縛":
                'def f(k, plys):\n    return [idx[p] for idx in [k["sfens"]] for p in plys]\n',
            "素の二重添字": 'def f(k, ply):\n    return k["sfens"][ply]\n',
            "変数名を変えた単純代入": 'def f(k, ply):\n    idx = k["sfens"]\n    return idx[ply - 1]\n',
        }
        for name, src in bypasses.items():
            self.assertTrue(sfens_reaches(src), f"抜け道を捕まえられていない: {name}")

    def test_15_the_check_allows_only_passing_it_to_the_shared_judgment(self):
        """**誤検出しないこと。**`board_spec.…(…)` に直接渡す形だけが許される。

        これが通らないと `_mid.py` の正当な 1 か所が赤になり、**門を外す圧力になる。**
        """
        # **見本は import から書く** ― 許可は「そのファイルが board_spec に付けた名前」で決まるので、
        # import の無い断片は実物の形ではない(この直しで test_15 が実際に赤になり、書き直した)。
        ok = ('import board_spec\n'
              'def f(s_, k):\n    return board_spec.scene_spec(s_, k["sfens"], k["moves"])\n')
        self.assertEqual(sfens_reaches(ok), [], "正当な受け渡しを誤って捕まえている")
        unrelated = 'def f(spec, d):\n    return spec["sfen"] + d["moves"][0]\n'
        self.assertEqual(sfens_reaches(unrelated), [], "無関係な添字を捕まえている")

    def test_15b_the_alias_is_resolved_from_the_import(self):
        """**別名 import を許す(P-124 の残余 b)。**`as` の別名は列挙せず、import 文から解く。

        **`board_spec` 以外のモジュールに同じ別名を付けた場合は許さない** ―
        ここを試験しないと、直しが「どんな別名でも通る」穴になる。
        """
        alias = ('import board_spec as BS\n'
                 'def f(s_, k):\n    return BS.scene_spec(s_, k["sfens"], k["moves"])\n')
        self.assertEqual(sfens_reaches(alias), [], "別名 import の正当な受け渡しが赤になっている")
        direct = ('from board_spec import scene_spec\n'
                  'def f(s_, k):\n    return scene_spec(s_, k["sfens"], k["moves"])\n')
        self.assertEqual(sfens_reaches(direct), [], "from import の正当な受け渡しが赤になっている")
        # **同じ別名を別のモジュールに付けた場合**(穴になっていないこと)
        impostor = ('import helper as BS\n'
                    'def f(s_, k):\n    return BS.scene_spec(s_, k["sfens"], k["moves"])\n')
        self.assertTrue(sfens_reaches(impostor), "board_spec 以外の別名が許されている")
        no_import = 'def f(s_, k):\n    return board_spec.scene_spec(s_, k["sfens"])\n'
        self.assertTrue(sfens_reaches(no_import), "import の無い board_spec 宛てが許されている")
        # **`from 別のモジュール import 同じ名前` も許されないこと。**
        # ここを試験していなかったため、「from import の出どころを見ない」変異が赤にならなかった
        # (校正で実測 2026-09-29)。**許可の条件は 1 つずつ試験で押さえる。**
        other_from = ('from helper import scene_spec\n'
                      'def f(s_, k):\n    return scene_spec(s_, k["sfens"])\n')
        self.assertTrue(sfens_reaches(other_from), "board_spec 以外からの from import が許されている")

    def test_16_passing_to_something_else_is_not_allowed(self):
        """**他の関数に渡すのは許さない。**許可は `board_spec` 宛てだけ。

        これを許すと、間に何を挟んでも通る道が開く(監査が見つけた 1 つ目の抜け道)。
        """
        # (a) 素の関数へ渡す
        plain = 'def f(s_, k):\n    return helper(s_, k["sfens"], k["moves"])\n'
        self.assertTrue(sfens_reaches(plain), "素の関数への受け渡しが許されている")
        # (b) **別のオブジェクトのメソッドへ渡す。**
        # ここを試験していなかったため、「board_spec の名前の照合を外す」変異が
        # 赤にならなかった(校正で実測 2026-09-29)。**許可の条件は 1 つずつ試験で押さえる。**
        other_obj = 'def f(s_, k):\n    return helper.pick(s_, k["sfens"])\n'
        self.assertTrue(sfens_reaches(other_obj),
                        "board_spec 以外のオブジェクトへの受け渡しが許されている")


class RotateTest(unittest.TestCase):
    """**`render_direct.py` から移した向きの道具**(2026-09-29。司令塔の条件 4)。

    **校正値は「移す前」の関数から取った** ― 移した後のコードから期待値を書くと、
    写し間違いをそのまま正解にしてしまう。移す前の定義を `ast` で取り出し、
    c5 の材料の USI 856 件に当てて得た値がこれ(往復 856/856・全件の写像の指紋
    sha256 = 3eae09155296e667cfd8752f9b5e030f8f233e7ff4a4bd886c84b4d2349231a3)。
    """

    # 移す前の関数が実際に返した値(材料の先頭から。打つ手・成る手・素の手を 1 つずつ)
    BEFORE_MOVE = [("3a1c+", "7i9g+"), ("B*8a", "B*2i"), ("6a7b", "4i3h")]

    def test_21_rotate_matches_the_values_measured_before_the_move(self):
        for src, want in self.BEFORE_MOVE:
            self.assertEqual(BS.rotate_usi(src), want, src)

    def test_22_rotating_twice_returns_the_original(self):
        """**往復**(2 回回すと元に戻る)。移す前は材料の 856 件すべてで戻った。"""
        for src, _ in self.BEFORE_MOVE:
            self.assertEqual(BS.rotate_usi(BS.rotate_usi(src)), src, src)

    def test_23_genuine_move_only_rotates_when_mirrored(self):
        """`mirrored` が真のときだけ回す。偽なら素通り、`None` はどちらでも `None`。"""
        self.assertEqual(BS.genuine_move("3a1c+", True), "7i9g+")
        self.assertEqual(BS.genuine_move("3a1c+", False), "3a1c+")
        self.assertIsNone(BS.genuine_move(None, True))
        self.assertIsNone(BS.genuine_move(None, False))

    def test_24_the_definition_left_render_direct(self):
        """**写しではなく移動であること。**`render_direct.py` に定義が残っていたら、
        直しが片方だけに入る道が開く(P-111 の病気)。**束縛(import)は在ってよい。**
        """
        src = read_text(os.path.join(HERE, "render_direct.py"))
        for name in ("def rotate_usi", "def rotate_square", "def genuine_move"):
            self.assertNotIn(name, src, f"{name} の定義が render_direct.py に残っている")
        self.assertIn("from board_spec import", src, "board_spec からの束縛が無い")


if __name__ == "__main__":
    unittest.main(verbosity=2)
