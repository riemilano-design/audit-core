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
        # 付録 3(positions[3])は 2026-09-25(凍結の例外 7b)から `direct_positions_of` が
        # `{"<組>": {(gameNo, ply), …}, …}` を返すため、ここも組の辞書にする(材料が 1 組だけのときの
        # 従来の動作 ― 組の宣言が無ければ (G, P) だけで照合 ― は変わらない。既存のテスト本体・期待値は
        # 1 つも変えていない)。
        self.positions = {
            1: {(1, 10), (2, 20)},  # 付録 1: prose.json の scenes[]
            2: {(3, 33)},  # 付録 2: whatif の representative
            3: {"組": {(5, 59), (9, 77)}},  # 付録 3: direct_answers の局面と final_positions の最終局面(1 組)
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


class WhatifPositionsOfTest(unittest.TestCase):
    """`whatif_positions_of`(検査 7・付録 2 の材料)。2026-09-25 の直し(凍結の例外 7a): 付録 2 の材料は
    `--whatif-data-now`(今回の組の 1 本)だけから作る。`--whatif-data`(全組。検査 1 の数の照合の材料)とは
    別で、`ProsePositionsOfTest` と同じ流儀(実ファイルを一時フォルダに書き、パスを渡す)。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def write_whatif_data(self, name, games):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"games": games}, f)
        return path

    def test_representative_position_included(self):
        path = self.write_whatif_data("w1.json", [{"gameNo": 1, "representative": {"displayPly": 10}}])
        positions = CA.whatif_positions_of([path])
        self.assertEqual(positions, {(1, 10)})

    def test_game_without_representative_skipped(self):
        path = self.write_whatif_data("w2.json", [{"gameNo": 1, "representative": None}, {"gameNo": 2, "representative": {"displayPly": 20}}])
        positions = CA.whatif_positions_of([path])
        self.assertEqual(positions, {(2, 20)})

    def test_no_paths_returns_none(self):
        self.assertIsNone(CA.whatif_positions_of([]))

    def test_two_whatif_data_now_paths_rejected_by_parse_args(self):
        """局番号は組ごとに 1 から振られる(組をまたいで衝突しうる)ため、`--whatif-data-now` は今回の組の
        1 本だけ(`--prose` と同じ流儀)。`parse_args` が 2 本以上を `CheckAnswerError` で拒むことを確かめる。"""
        path1 = self.write_whatif_data("a.json", [{"gameNo": 1, "representative": {"displayPly": 10}}])
        path2 = self.write_whatif_data("b.json", [{"gameNo": 1, "representative": {"displayPly": 30}}])
        argv = ["b.md", "--whatif-data-now", path1, "--whatif-data-now", path2, "--menu", "menu.json"]
        with self.assertRaises(CA.CheckAnswerError) as ctx:
            CA.parse_args(argv)
        self.assertIn("--whatif-data-now", str(ctx.exception))

    def test_missing_whatif_data_now_file_raises_check_answer_error(self):
        """ファイルが無いとき、traceback ではなく `CheckAnswerError` で理由を出す(`--prose` と同じ流儀)。"""
        missing_path = os.path.join(self._tmp.name, "does-not-exist.json")
        with self.assertRaises(CA.CheckAnswerError) as ctx:
            CA.whatif_positions_of([missing_path])
        self.assertIn("--whatif-data-now のファイルが無い", str(ctx.exception))
        self.assertIn(missing_path, str(ctx.exception))

    def test_position_not_in_whatif_data_now_fails_check_pos_tags(self):
        path = self.write_whatif_data("d.json", [{"gameNo": 1, "representative": {"displayPly": 10}}])
        positions_2 = CA.whatif_positions_of([path])
        ctx = make_ctx({1: set(), 2: positions_2, 3: set()})
        problems = []
        CA.check_pos_tags("<!-- pos: 2/20 付録2 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("材料に無い", reason)
        self.assertIn("2/20", reason)
        # 対照: 材料にある方は通る。
        problems2 = []
        CA.check_pos_tags("<!-- pos: 1/10 付録2 -->", ctx, problems2, 1)
        self.assertEqual(problems2, [])


class WhatifDataNowExcludesOtherGroupsTest(unittest.TestCase):
    """`--whatif-data`(全組。検査 1 の数の照合だけの材料)に他の組の `whatif_report_data.json` を渡しても、
    検査 7(付録 2)の材料には入らない ― `build_materials` の配線(`positions[2]` は `whatif_positions_of` に
    `args.whatif_data_now_paths` だけを渡す)を、実際に `parse_args` → `build_materials` を通して確かめる。
    2026-09-25 の直し(凍結の例外 7a。以前は `positions[2]` に `args.whatif_data_paths`〈全組の和集合〉を渡して
    いたため、他の組の局面が「付録 2 にある」と誤って通っていた)。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # `build_materials` は `data/{shapes,openings,intents}` を glob するだけ(検査 6 の材料)なので、
        # 実際のリポジトリルート(このファイルの 3 つ上)を渡す ― 読むだけで書き込みはしない。
        self._repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    def tearDown(self):
        self._tmp.cleanup()

    def write_json(self, name, data):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_leak_excluded_but_number_still_allowed(self):
        now_path = self.write_json("now.json", {"games": [{"gameNo": 1, "representative": {"displayPly": 10}}]})
        # 「もう一方の組」の材料(`--whatif-data` の一部としてのみ渡す。`--whatif-data-now` には渡さない)。
        other_path = self.write_json("other.json", {"games": [{"gameNo": 2, "representative": {"displayPly": 20}}]})
        menu_path = self.write_json("menu.json", {"items": []})
        argv = [
            "b.md",
            "--whatif-data", now_path,
            "--whatif-data", other_path,  # 検査 1(数の照合)の材料には両方入る
            "--whatif-data-now", now_path,  # 検査 7(付録 2)の材料はこれだけ
            "--menu", menu_path,
        ]
        args = CA.parse_args(argv)
        ctx = CA.build_materials(args, self._repo_root)
        # 検査 7: 「もう一方の組」の局面(2, 20)は付録 2 の材料に無い。今回の組の局面(1, 10)はある。
        self.assertEqual(ctx["positions"][2], {(1, 10)})
        self.assertNotIn((2, 20), ctx["positions"][2])
        # 検査 1: 数の照合の材料(allowedNumbers)は `--whatif-data` の全部から作るので、「もう一方の組」だけに
        # ある数(20 = other.json の displayPly)も引き続き許される(この直しで検査 1 の材料は変えていない)。
        self.assertIn(20, ctx["allowedNumbers"])


class RealBaselineWhatifGroupBoundaryTest(unittest.TestCase):
    """指示系統からの固定試験(2026-09-25、凍結の例外 7a。実装担当が 44 局の基準〈3 組〉の実物から読み取った
    値をここに書き写す ― ファイルは読まない〈gitignore の実データには依存させない〉)。

    今回の組(`scripts/playtest/out/tatsunami3/pipe/report/whatif_report_data.json`。`docs/STEP_DELIVER1_PLAN_
    2026-09-25.md` §3.7(a) の「今回の 14 局」)の `games[].representative`(gameNo, displayPly):
    (1, 93)・(2, 71)・(3, 77)(実装担当が読み取り済み)。

    もう一方の組(`scripts/playtest/out/tatsunami-long/pipe/report/whatif_report_data.json`。同じ §3.7(a) の
    「10 分の組」)の `games[].representative`: (2, 97)・(3, 82)・(4, 106)(実装担当が読み取り済み ― いずれも
    今回の組の gameNo 2〜4 の displayPly とは値が異なるため衝突しない)。

    `docs/STEP_DELIVER1_PLAN_2026-09-25.md` §11.7 は、この 2 組(44 局・3 組の基準)で「もう一方の組の 10 件の
    うち 9 件が、今回の組の材料に無いのに検査 7 を通る」と記録している ― この試験は、直した後は通らない
    (材料に無いので落ちる)ことを、今回の組の材料(上の 3 件)だけを `positions[2]` として合成して確かめる。"""

    def setUp(self):
        # `whatif_positions_of(["…/tatsunami3/pipe/report/whatif_report_data.json"])` を実際に読んだ結果と
        # 同じ集合(実装担当が実物を読んで書き写した。gameNo 1〜3 分。他の局は省略)。
        self.now_group_positions = {(1, 93), (2, 71), (3, 77)}

    def check(self, tag):
        ctx = make_ctx({1: set(), 2: self.now_group_positions, 3: set()})
        problems = []
        CA.check_pos_tags(f"<!-- pos: {tag} 付録2 -->", ctx, problems, 1)
        return problems

    def test_now_group_positions_pass(self):
        for g, p in ((1, 93), (2, 71), (3, 77)):
            self.assertEqual(self.check(f"{g}/{p}"), [], f"({g},{p}) は今回の組(tatsunami3)の材料にあるので通るはず")

    def test_other_group_only_positions_fail(self):
        # tatsunami-long(もう一方の組)にしかない局面。旧版(`--whatif-data` の和集合)なら通ってしまっていた。
        for g, p in ((2, 97), (3, 82), (4, 106)):
            problems = self.check(f"{g}/{p}")
            self.assertEqual(len(problems), 1, f"({g},{p}) はもう一方の組(tatsunami-long)にしか無いので落ちるはず")
            _, reason, _ = problems[0]
            self.assertIn("検査 7", reason)
            self.assertIn("材料に無い", reason)


class DirectPositionsOfGroupTest(unittest.TestCase):
    """`direct_positions_of`(検査 7・付録 3 の材料。2026-09-25 の直し、凍結の例外 7b)を、合成 ctx だけでなく
    `direct_materials_of` を実際に通した結果に対して確かめる(合成 ctx だけで材料構築関数を一度も通さない、
    という過去の監査指摘と同じ形を避ける。`ProsePositionsOfTest` と同じ流儀)。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def write_json(self, name, data):
        path = os.path.join(self._tmp.name, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_groups_from_direct_answers_and_final_positions_combined(self):
        answers_path = self.write_json(
            "direct_answers.json",
            {
                "kind": "direct_answers",
                "counts": {
                    "totalCount": 0,
                    "totalForkCount": 0,
                    "top1TagCounts": {},
                    "actualTagCounts": {},
                    "top1SideCounts": {},
                },
                "answers": [
                    {"group": "3 分", "gameNo": 1, "displayPly": 10},
                    {"group": "10 分", "gameNo": 1, "displayPly": 10},
                ],
            },
        )
        final_path = self.write_json(
            "final_positions.json",
            {"kind": "final_positions", "entries": [{"group": "3 分", "gameNo": 5, "moves": 59}]},
        )
        direct = CA.direct_materials_of([answers_path, final_path])
        positions = CA.direct_positions_of(direct)
        # 「局」の番号は組ごとに 1 から振られる(gameNo=1・ply=10 が 2 組それぞれにある)ので、組ごとに
        # 別の集合になっていることを確かめる(単一の集合に混ぜていない)。
        self.assertEqual(positions["3 分"], {(1, 10), (5, 59)})
        self.assertEqual(positions["10 分"], {(1, 10)})

    def test_no_direct_paths_returns_none(self):
        self.assertIsNone(CA.direct_positions_of(None))


class CheckPosTagsAppendix3GroupTest(unittest.TestCase):
    """検査 7・付録 3 の組の照合(2026-09-25、凍結の例外 7b)。`direct_positions_of` が返す
    `{"<組>": {(gameNo, ply), …}, …}` の形の合成材料を `check_pos_tags` に渡して確かめる(`CheckPosTagsTest`
    と同じ流儀)。"""

    def check(self, line, positions3):
        ctx = make_ctx({1: set(), 2: set(), 3: positions3})
        problems = []
        CA.check_pos_tags(line, ctx, problems, 1)
        return problems

    def two_group_positions(self):
        return {"3 分": {(1, 10)}, "10 分": {(2, 20)}}

    # 材料の組が 2 種類以上のとき。

    def test_two_groups_no_group_declared_fails_and_lists_usable_groups(self):
        problems = self.check("<!-- pos: 1/10 付録3 -->", self.two_group_positions())
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組が無い", reason)
        self.assertIn("3 分", reason)
        self.assertIn("10 分", reason)

    def test_two_groups_correct_group_passes(self):
        self.assertEqual(self.check("<!-- pos: 1/10 付録3 3 分 -->", self.two_group_positions()), [])
        self.assertEqual(self.check("<!-- pos: 2/20 付録3 10 分 -->", self.two_group_positions()), [])

    def test_two_groups_wrong_group_for_same_gp_fails(self):
        # (1, 10) は「3 分」の組の材料。「10 分」と書く(4 人目で実際に起きた組の取り違えと同じ型)と落ちる。
        problems = self.check("<!-- pos: 1/10 付録3 10 分 -->", self.two_group_positions())
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組 10 分 の材料に無い", reason)

    def test_two_groups_unknown_group_fails(self):
        problems = self.check("<!-- pos: 1/10 付録3 30 分 -->", self.two_group_positions())
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組 30 分 の材料に無い", reason)

    # 材料の組が 1 種類だけのとき(従来の顧客の形。組が 1 つなら宣言に組を書かなくてよい)。

    def one_group_positions(self):
        return {"3 分": {(1, 10)}}

    def test_one_group_no_group_declared_passes_as_before(self):
        self.assertEqual(self.check("<!-- pos: 1/10 付録3 -->", self.one_group_positions()), [])

    def test_one_group_no_group_declared_missing_position_fails(self):
        problems = self.check("<!-- pos: 9/99 付録3 -->", self.one_group_positions())
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("材料に無い", reason)

    def test_one_group_wrong_group_declared_fails(self):
        problems = self.check("<!-- pos: 1/10 付録3 10 分 -->", self.one_group_positions())
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組 10 分 の材料に無い", reason)

    def test_one_group_correct_group_declared_passes(self):
        self.assertEqual(self.check("<!-- pos: 1/10 付録3 3 分 -->", self.one_group_positions()), [])

    # 付録 1・2・4 の宣言に組を書くと落ちる(付録 3 だけが組を持つ)。

    def test_appendix1_with_group_fails(self):
        ctx = make_ctx({1: {(1, 10)}, 2: set(), 3: {}})
        problems = []
        CA.check_pos_tags("<!-- pos: 1/10 付録1 3 分 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組は書かない", reason)

    def test_appendix2_with_group_fails(self):
        ctx = make_ctx({1: set(), 2: {(1, 10)}, 3: {}})
        problems = []
        CA.check_pos_tags("<!-- pos: 1/10 付録2 3 分 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組は書かない", reason)

    def test_appendix4_with_group_fails_with_group_message_not_no_board_message(self):
        ctx = make_ctx({1: set(), 2: set(), 3: {}})
        problems = []
        CA.check_pos_tags("<!-- pos: 1/10 付録4 3 分 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組は書かない", reason)
        self.assertNotIn("盤が無い", reason)  # 組が書かれているときは「組は書かない」を先に返す


class RealBaselineDirectGroupTest(unittest.TestCase):
    """指示系統からの固定試験(2026-09-25、凍結の例外 7b。実装担当が 44 局の基準〈3 組〉の実物から読み取った
    値をここに書き写す ― ファイルは読まない〈gitignore の実データには依存させない〉)。

    出どころ: `scripts/playtest/out/_deliver1_verify/deliver1/direct/direct_answers.json`(gitignore)を
    `json.load` し、`answers[]` の各要素の `group`・`gameNo`・`displayPly` を読んだ(実装担当が読み取り済み)。
    3 分の組(`answers[].group == "3 分"`、21 件のうち先頭 2 件): (10, 50)・(10, 94)。
    10 分の組(`answers[].group == "10 分"`、9 件のうち先頭 2 件): (4, 72)・(2, 83)。
    この基準は §11.7 の背景が記録する「3 分 21 件・10 分 9 件、重なりは 0 件」と一致する(実装担当が同じ
    ファイルの `answers[].group` の内訳を数えて確認済み)。"""

    def setUp(self):
        self.positions3 = {
            "3 分": {(10, 50), (10, 94)},
            "10 分": {(4, 72), (2, 83)},
        }

    def check(self, tag):
        ctx = make_ctx({1: set(), 2: set(), 3: self.positions3})
        problems = []
        CA.check_pos_tags(f"<!-- pos: {tag} -->", ctx, problems, 1)
        return problems

    def test_correct_group_passes(self):
        for g, p, group in ((10, 50, "3 分"), (10, 94, "3 分"), (4, 72, "10 分"), (2, 83, "10 分")):
            self.assertEqual(self.check(f"{g}/{p} 付録3 {group}"), [], f"({g},{p},{group}) は基準の材料にあるので通るはず")

    def test_no_group_fails_with_two_groups(self):
        problems = self.check("10/50 付録3")
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組が無い", reason)

    def test_swapped_group_fails(self):
        # (10, 50) は 3 分の組の材料。10 分と書く(4 人目で実際に起きた組の取り違えと同じ型)と落ちる。
        problems = self.check("10/50 付録3 10 分")
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("組 10 分 の材料に無い", reason)


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
