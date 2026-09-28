# -*- coding: utf-8 -*-
# `board_spec.py`(盤に渡す値の判断)の試験。
#
# 【なぜこの試験が要るか】**判断を写すと 1 手ずれ、ずれても試験は通ってしまう** ―
# 材料と PDF の両方が同じ写し間違いで揃うため。だから**判断そのものを試験で固定**し、
# **写しが戻っていないこと**も機械で見る(下の `NoCopyTest`)。
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import board_spec as BS

HERE = os.path.dirname(os.path.abspath(__file__))
SFENS = ["s0", "s1", "s2", "s3", "s4"]     # 0 件目が初期局面
MOVES = ["m1", "m2", "m3", "m4"]           # moves[i] が sfens[i] → sfens[i+1]


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

    def test_12_mid_has_no_copy_of_the_index_arithmetic(self):
        """`k["sfens"][ply]` / `k["sfens"][ply - 1]` の直書きが戻っていないこと。

        戻ると、**片方だけ直したときに本編の盤と付録の盤が 1 手ずれる。**
        """
        src = open(os.path.join(HERE, "_mid.py"), encoding="utf-8").read()
        hits = re.findall(r'k\["sfens"\]\s*\[\s*ply', src)
        self.assertEqual(hits, [], f"添字の直書きが戻っている: {hits}")
        hits2 = re.findall(r'min\(\s*s_\["ply"\]\s*,', src)
        self.assertEqual(hits2, [], f"切り詰めの直書きが戻っている: {hits2}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
