# -*- coding: utf-8 -*-
"""`_head.py`・`_mid.py`(`build.sh` が繋ぐ断片)の**顧客に出る語**の試験。

**なぜ断片に試験ファイルを作ったか**: `_head.py`・`_mid.py` は import できない断片なので、
これまで**顧客に出る題の語をどの試験も見ていなかった**(`check_structure_test` が `_mid.py` の
`REPORT_DISPLAY_NAME` を原文で見ているだけ)。題は顧客の冊子の本文なので、変えたときに
気づく場所が要る。**`ast` で読めることは実測した**(断片でも構文は通る)。

**字面ではなく `ast` で見る** ― 説明のコメントに題の語を書くと、字面の試験はそこに当たる
(2026-09-29 に 1 日 4 回踏んだ型)。
"""
import ast
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def title_strings_of(name):
    """その断片で `title = "…"` に代入される文字列を全部返す(`ast` で読む)。"""
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "title"):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out.append(node.value.value)
    return out


class ResignTitleSaysWhoTest(unittest.TestCase):
    """**投了の題は「誰が投了したか」を言う**(P-175。2026-09-29)。

    批評席 (a)(4 周目)が実物で挙げた: 第 1・20・25 局が「盤上は劣勢のまま、投了で終わった将棋」
    なのに結果は**勝ち**、第 16 局は「優勢のまま投了」で**負け**。
    「相手の投了だと推測はできるが説明が無く、グラフの終点と結果が食い違って見える」。

    **結果から決まる** ― 投了で終わって負けたなら本人が、勝ったなら相手が投了した。
    **将棋の判断はしていない**(`ending` の語と `result` の組み合わせだけ)。
    """

    def setUp(self):
        self.titles = title_strings_of("_head.py")

    def test_h1_the_loss_title_says_the_person_resigned(self):
        self.assertIn("盤上は優勢のまま、本人の投了で終わった将棋", self.titles)

    def test_h2_the_win_title_says_the_opponent_resigned(self):
        self.assertIn("盤上は劣勢のまま、相手の投了で終わった将棋", self.titles)

    def test_h3_the_bare_title_remains_only_as_the_fallback(self):
        """**引き分けの受け皿だけが語を足さない題である。**

        勝ちも負けも「誰が」を言うので、語を足さない題は**ちょうど 1 つ**(引き分け用)。
        2 つ以上あれば、どちらかの枝が直っていない。
        """
        bare = [t for t in self.titles if "投了で終わった将棋" in t
                and "本人の投了" not in t and "相手の投了" not in t]
        self.assertEqual(bare, ["盤上は劣勢のまま、投了で終わった将棋"], bare)

    def test_h4_every_resign_title_is_reachable_from_the_result(self):
        """**題の語は結果の語と対になっている**(「本人」は負けの枝・「相手」は勝ちの枝)。

        `ast` で枝を辿るのは重いので、**語の非対称**で見る ―
        「優勢のまま」は負けの側の言い方、「劣勢のまま」は勝ちの側の言い方(鏡写し)。
        """
        person = [t for t in self.titles if "本人の投了" in t]
        opponent = [t for t in self.titles if "相手の投了" in t]
        self.assertEqual(len(person), 1, person)
        self.assertEqual(len(opponent), 1, opponent)
        self.assertIn("優勢のまま", person[0])
        self.assertIn("劣勢のまま", opponent[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
