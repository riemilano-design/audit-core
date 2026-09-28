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
SFENS = ["s0", "s1", "s2", "s3", "s4"]     # 0 件目が初期局面
MOVES = ["m1", "m2", "m3", "m4"]           # moves[i] が sfens[i] → sfens[i+1]

# **付録 1 の判断を共有するファイル。**ここに挙げたものは `sfens` を自分で引いてはいけない。
# `render_direct.py`・`render_whatif.py` は付録 2・3 の**別の判断**なので入れない。
SHARE_JUDGMENT = ("_mid.py", "exit_body.py")


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
    """
    tree = ast.parse(source)
    allowed, reaches = set(), []

    def is_board_spec_call(node):
        f = node.func
        return (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                and f.value.id == "board_spec")

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

        **範囲は付録 1 の判断を共有する組だけ**(`_mid.py` と後半の `exit_body.py`)。
        `render_direct.py`・`render_whatif.py` も `k["sfens"][…]` を引くが、
        **あれは付録 2・3 の別の判断**なので範囲に入れない(P-124 に「他は未適用」と残す)。
        """
        for base in SHARE_JUDGMENT:
            path = os.path.join(HERE, base)
            if not os.path.exists(path):
                continue    # 後半が来る前は exit_body.py が無い(下の test_13 が「来たら見る」を保つ)
            found = sfens_reaches(open(path, encoding="utf-8").read())
            self.assertEqual(found, [],
                             f"{base} が sfens を自分で添字で引いている(行 {found})"
                             f" ― 判断は board_spec.scene_spec() だけが持つ")

    def test_13_the_share_list_is_not_empty_and_names_exist(self):
        """**範囲の一覧が空にならないこと。**空にすれば test_12 は黙って通る。

        `_mid.py` は必ず在るので、一覧から外れたら赤になる。
        """
        self.assertIn("_mid.py", SHARE_JUDGMENT)
        self.assertTrue(os.path.exists(os.path.join(HERE, "_mid.py")))

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
        ok = 'def f(s_, k):\n    return board_spec.scene_spec(s_, k["sfens"], k["moves"])\n'
        self.assertEqual(sfens_reaches(ok), [], "正当な受け渡しを誤って捕まえている")
        unrelated = 'def f(spec, d):\n    return spec["sfen"] + d["moves"][0]\n'
        self.assertEqual(sfens_reaches(unrelated), [], "無関係な添字を捕まえている")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
