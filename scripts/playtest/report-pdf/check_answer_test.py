# -*- coding: utf-8 -*-
# check_answer.py の検査 7(局面の参照)の試験。2026-09-24 の人間の委任(docs/STEP_DELIVER1_PLAN_2026-09-25.md
# §11.7)。「本文が指した局面が、指した付録に実在するか」を確かめる `<!-- pos: G/P 付録N -->` の印を検査する。
#
# answer_facts_test.py と同じ流儀: pytest 等の外部ライブラリは使わない(標準ライブラリ unittest)。gitignore の
# 実データは読まない。材料は、この試験の中に持つ小さな合成 `ctx`(`check_pos_tags`・`check_line_numbers` が
# 読む欄だけを持つ辞書)か、`prose_positions_of` が読む合成の `prose.json`(`tempfile` で一時フォルダに書く。
# `answer_facts_test.py` と同じ流儀)。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/check_answer_test.py`
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402


def make_ctx(positions, pairs=None, allowed_numbers=None):
    """`check_pos_tags`・`check_line_numbers` が読む欄だけを持つ、最小の合成 `ctx`。"""
    return {
        "positions": positions,
        "pairs": pairs if pairs is not None else set(),
        "allowedNumbers": allowed_numbers if allowed_numbers is not None else set(),
    }


class CheckPosTagsTest(unittest.TestCase):
    def setUp(self):
        # 付録 1〜3 は局面あり(付録 4 は render_time_cause.py に盤が無いため、材料の鍵を持たない ―
        # `check_pos_tags` は N==4 を材料の有無より前に特別扱いする)。
        self.positions = {
            1: {(1, 10), (2, 20)},  # 付録 1: prose.json の scenes[]
            2: {(3, 33)},  # 付録 2: whatif の representative
            3: {(5, 59), (9, 77)},  # 付録 3: direct_answers の局面と final_positions の最終局面
        }

    def check(self, line, positions=None):
        ctx = make_ctx(positions if positions is not None else self.positions)
        problems = []
        CA.check_pos_tags(line, ctx, problems, 1)
        return problems

    # 1. 存在する (G,P) の宣言は通る(付録 1・2・3 それぞれ 1 件、final_positions の最終局面 1 件)。
    def test_existing_positions_pass(self):
        self.assertEqual(self.check("参考: <!-- pos: 1/10 付録1 -->"), [])
        self.assertEqual(self.check("参考: <!-- pos: 3/33 付録2 -->"), [])
        self.assertEqual(self.check("参考: <!-- pos: 5/59 付録3 -->"), [])  # direct_answers 側
        self.assertEqual(self.check("参考: <!-- pos: 9/77 付録3 -->"), [])  # final_positions(最終局面)側

    # 2. 存在しない (G,P) は落ち、メッセージに「検査 7」と「G/P」と付録番号が入る。
    def test_missing_position_fails_with_message(self):
        problems = self.check("参考: <!-- pos: 9/99 付録1 -->")
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("9/99", reason)
        self.assertIn("付録 1", reason)

    # 3. 付録 4(render_time_cause.py)には盤が 1 枚も無いため、`<!-- pos: … 付録4 -->` は材料の有無に
    # かかわらず常に「付録 4 には盤が無い」で落ちる(司令塔の指示、2026-09-24)。
    def test_appendix4_always_fails_no_board_message(self):
        for positions in (
            self.positions,  # 付録 4 の鍵自体が無い(--time-cause の材料は付録 4 の検査 7 には使わない)
            {**self.positions, 4: set()},  # 鍵があっても局面が無くても
            {**self.positions, 4: {(5, 59)}},  # 局面があっても関係ない
        ):
            problems = self.check("参考: <!-- pos: 5/59 付録4 -->", positions=positions)
            self.assertEqual(len(problems), 1, positions)
            _, reason, _ = problems[0]
            self.assertIn("検査 7", reason)
            self.assertIn("付録 4 には盤が無い", reason)

    # 4. 形の崩れ(スラッシュが無い、知らない付録番号)は落ちる。
    def test_malformed_tag_fails(self):
        problems = self.check("参考: <!-- pos: 5 付録3 -->")
        self.assertEqual(len(problems), 1)
        self.assertIn("検査 7", problems[0][1])

    def test_unknown_appendix_number_fails(self):
        problems = self.check("参考: <!-- pos: 5/59 付録9 -->")
        self.assertEqual(len(problems), 1)
        self.assertIn("検査 7", problems[0][1])

    # 6. 1 行に印が 2 つあるとき両方見る(1 つは存在する局面、1 つは存在しない局面)。
    def test_two_tags_in_one_line_both_checked(self):
        line = "<!-- pos: 1/10 付録1 --> と <!-- pos: 9/99 付録1 -->"
        problems = self.check(line)
        self.assertEqual(len(problems), 1)
        self.assertIn("9/99", problems[0][1])


class ProsePositionsOfTest(unittest.TestCase):
    """司令塔の指示(付録 1 の材料が、納品されない別冊〈`_tail.py`〉の `events[]`/`escapeScenes[]` から
    作られていた件。2026-09-24)。納品される付録 1(`render_main.py`〈`_head.py + _util.py + _mid.py`〉)が
    実際に盤を描くのは `prose.json` の `scenes[]` だけ(`_mid.py` 133〜143 行、`type` を問わない)なので、
    `prose_positions_of` を直接呼んで確かめる。実ファイルを一時フォルダに書き、パスを渡す
    (`prose_positions_of` は `--prose` のパスから `load_json` で読むため。`answer_facts_test.py` と同じ流儀)。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def write_prose(self, name, data):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_scene_position_included(self):
        path = self.write_prose(
            "prose1.json",
            {"1": {"summary": "s", "takeaway": "t", "scenes": [{"type": "move", "ply": 10, "text": "x"}]}},
        )
        positions = CA.prose_positions_of([path])
        self.assertIn((1, 10), positions)

    def test_non_move_type_scene_included(self):
        # `_mid.py` の 133〜143 行は `type == "move"` の分岐(135〜140 行)でも、それ以外の分岐(141〜143 行)
        # でも盤(`Board(...)`)を描く。
        path = self.write_prose(
            "prose2.json",
            {"2": {"summary": "s", "takeaway": "t", "scenes": [{"type": "opponent", "ply": 20, "text": "x"}]}},
        )
        positions = CA.prose_positions_of([path])
        self.assertIn((2, 20), positions)

    def test_no_prose_paths_returns_none(self):
        self.assertIsNone(CA.prose_positions_of([]))

    def test_two_prose_paths_rejected_by_parse_args(self):
        """局番号は組ごとに 1 から振られる(組をまたいで衝突しうる)ため、`--prose` は今回の組の 1 本だけ
        (2026-09-25 の直し。以前は組ごとに渡し、複数渡すと衝突する局面まで検査 7 を通してしまっていた)。
        `parse_args` が 2 本以上を `CheckAnswerError` で拒むことを確かめる。"""
        path1 = self.write_prose("a.json", {"1": {"scenes": [{"type": "move", "ply": 10, "text": "x"}]}})
        path2 = self.write_prose("b.json", {"3": {"scenes": [{"type": "move", "ply": 30, "text": "y"}]}})
        argv = ["b.md", "--prose", path1, "--prose", path2, "--menu", "menu.json"]
        with self.assertRaises(CA.CheckAnswerError) as ctx:
            CA.parse_args(argv)
        self.assertIn("--prose", str(ctx.exception))

    def test_missing_prose_file_raises_check_answer_error(self):
        """`prose.json` が無いとき(前の組の材料が今回の納品に無い等)、traceback ではなく
        `CheckAnswerError` で「--prose のファイルが無い」と落ちる(2026-09-25 の直し)。"""
        missing_path = os.path.join(self._tmp.name, "does-not-exist.json")
        with self.assertRaises(CA.CheckAnswerError) as ctx:
            CA.prose_positions_of([missing_path])
        self.assertIn("--prose のファイルが無い", str(ctx.exception))
        self.assertIn(missing_path, str(ctx.exception))

    def test_group_boundary_no_leak_from_other_group_prose(self):
        """指示系統からの固定試験(2026-09-25、納品レーンが 4 人目の実物で数えた衝突)。局番号は組ごとに
        1 から振られるため、3 分の組の第 2 局と 10 分の組の第 2 局は別の局面である。今回の組(3 分)の
        1 本だけを渡すと、3 分の組の第 2 局の場面(43・75・81 手目)は通り、10 分の組の第 2 局の場面
        (60・64・68 手目。今回は渡さない ― 納品されるのは今回の組の付録 1 だけ)は材料に無いので落ちる。"""
        min3_path = self.write_prose(
            "min3.json",
            {
                "2": {
                    "scenes": [
                        {"type": "move", "ply": 43, "text": "x"},
                        {"type": "move", "ply": 75, "text": "y"},
                        {"type": "move", "ply": 81, "text": "z"},
                    ]
                }
            },
        )
        # 10 分の組の prose.json(今回は渡さない。局番号が組ごとに 1 から振られることを示すためだけに作る)。
        self.write_prose(
            "min10.json",
            {
                "2": {
                    "scenes": [
                        {"type": "move", "ply": 60, "text": "x"},
                        {"type": "move", "ply": 64, "text": "y"},
                        {"type": "move", "ply": 68, "text": "z"},
                    ]
                }
            },
        )
        positions = CA.prose_positions_of([min3_path])
        ctx = make_ctx({1: positions, 2: set(), 3: set()})
        for ply in (43, 75, 81):
            problems = []
            CA.check_pos_tags(f"<!-- pos: 2/{ply} 付録1 -->", ctx, problems, 1)
            self.assertEqual(problems, [], f"ply={ply} は 3 分の組の材料にあるので通るはず")
        for ply in (60, 64, 68):
            problems = []
            CA.check_pos_tags(f"<!-- pos: 2/{ply} 付録1 -->", ctx, problems, 1)
            self.assertEqual(len(problems), 1, f"ply={ply} は 10 分の組の材料なので落ちるはず")
            self.assertIn("検査 7", problems[0][1])

    def test_string_key_converted_to_int(self):
        path = self.write_prose("c.json", {"7": {"scenes": [{"type": "move", "ply": 70, "text": "z"}]}})
        positions = CA.prose_positions_of([path])
        self.assertIn((7, 70), positions)
        for game_no, _ in positions:
            self.assertIsInstance(game_no, int)

    def test_position_not_in_prose_scenes_fails_check_pos_tags(self):
        """材料構築関数(`prose_positions_of`)を通した結果を `check_pos_tags` に渡し、`scenes[]` に無い
        (gameNo, ply) を指す `<!-- pos: 2/20 付録1 -->` が「材料に無い(検査 7)」で落ちることを確かめる
        (合成 ctx だけで材料構築関数を一度も通さない、という過去の監査指摘と同じ形を避ける)。"""
        path = self.write_prose(
            "d.json",
            {"1": {"scenes": [{"type": "move", "ply": 10, "text": "x"}]}, "2": {"scenes": []}},
        )
        positions_1 = CA.prose_positions_of([path])
        ctx = make_ctx({1: positions_1, 2: set(), 3: set()})
        problems = []
        CA.check_pos_tags("<!-- pos: 2/20 付録1 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("材料に無い", reason)
        self.assertIn("2/20", reason)
        # 対照: scenes[] にある方(材料にある)は通る。
        problems2 = []
        CA.check_pos_tags("<!-- pos: 1/10 付録1 -->", ctx, problems2, 1)
        self.assertEqual(problems2, [])


class CheckLineNumbersPosMaskTest(unittest.TestCase):
    """5. 印の中の数字が検査 1 で落ちない(宣言の数が「登録済みの組」に無くても、`pos` の印だけの行は
    数の照合で落ちない)。"""

    def test_pos_tag_numbers_not_counted_as_bare_numbers(self):
        # 345・12 は allowedNumbers に無く、9 局のうち 59 局のような組でもないので、マスクされなければ
        # 「データに無い数」・「数の組み合わせが登録済みの組に無い」のどちらかで必ず落ちる数を選ぶ。
        ctx = make_ctx(positions={1: set(), 2: set(), 3: set(), 4: set()}, pairs=set(), allowed_numbers=set())
        line = "この手は <!-- pos: 12/345 付録3 --> にあります。"
        problems = []
        CA.check_line_numbers(line, ctx, problems, 1)
        self.assertEqual(problems, [])

    def test_pos_tag_numbers_still_counted_outside_tag(self):
        # マスクが印の外まで壊していないことの対照(印の外の裸の数 12345 は変わらず検査 1 で落ちる)。
        ctx = make_ctx(positions={1: set(), 2: set(), 3: set(), 4: set()}, pairs=set(), allowed_numbers=set())
        line = "この局面は 12345 手目です。<!-- pos: 12/345 付録3 -->"
        problems = []
        CA.check_line_numbers(line, ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        self.assertIn("12345", problems[0][1])


if __name__ == "__main__":
    unittest.main()
