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
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_answer as CA  # noqa: E402

# 側の語の試験(P-185)が同じフォルダの他のファイルを原文で読むために使う。
HERE = os.path.dirname(os.path.abspath(__file__))


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


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


class CheckLineBannedEmptyTest(unittest.TestCase):
    """禁止語が無いことの固定(2026-09-25 の人間の決定、凍結の例外 14 件目)。`check_line_banned` と
    検査 3 の枠は残っているが、`BANNED_WORDS` が空なので 1 行も落とさない。"""

    def test_line_with_former_banned_words_passes(self):
        line = "悪手や癖について、あなたの将棋を書きます。"
        problems = []
        CA.check_line_banned(line, problems, 1)
        self.assertEqual(problems, [])


class MenuFractionsTest(unittest.TestCase):
    """**判定が見る分数と、冊子に印字する分数が同じであること。**

    2026-09-29 まではずれていた ― `M4` の行が `forkTotal`(分かれ道の総数)を「いまの値」として
    出していたが、**判定 `m4_holds` はその数で割っていない**(攻め・自玉側それぞれの分母で割る)。P-152。
    """

    @staticmethod
    def materials(attack=(65, 107), defense=(76, 132), fork_total=404,
                  sacrifice=(50, 137), quick=(7, 41), zero_to_one=(22, 531)):
        class G(object):
            pass
        g = G()
        g.after_long_think_quick = {"collapsed": quick[0], "n": quick[1]}
        g.by_spent = [{"collapsed": zero_to_one[0], "n": zero_to_one[1]}]
        return {
            "sideMatch": {"attack": {"collapsed": attack[0], "n": attack[1]},
                          "defense": {"collapsed": defense[0], "n": defense[1]},
                          "forkTotal": fork_total},
            "readCombined": {"sacrificeDiagonal": sacrifice[0], "sacrificeRowTotal": sacrifice[1]},
            "groups": {"min3": g},
        }

    def test_f0_every_fraction_says_what_it_counted(self):
        """**分数は「何を数えたか」を必ず持つ**(`unit`)。分母の出どころの表の単位になる。"""
        m = self.materials()
        for item_id in CA.MENU_FRACTIONS:
            for f in CA.menu_fractions(item_id, m):
                self.assertTrue(f.get("unit"), (item_id, f))

    def test_f0b_the_sacrifice_fraction_is_marked_as_a_unit_mismatch(self):
        """**M6 の分母は局面の数ではない**(P-165。2026-09-29 に `read` の局面行から数え直した)。

        `sacrificeRowTotal` は `tagCrossTable["sacrifice"]` の**行の合計**で、実物では 137。
        第 1 候補が捨て駒だった**局面は 107** で、137 はその 107 局面の
        「実戦の手に付いた印」の総数である(印が 2 つ以上の局面は何度も数えられ、
        印が 1 つも無い 18 局面は分母に入っていない)。**分子 50 は局面の数。**
        **分子と分母の単位が違う。**

        判定 `m6_holds` は動かさない(判断的知識 ― 人間の承認事項)。
        **この印が外れると、単位の違う数が分母の出どころの表に「局面」として並ぶ。**
        """
        m = self.materials()
        (f,) = CA.menu_fractions("M6", m)
        self.assertTrue(f.get("unitMismatch"), f)
        self.assertIn("印の組", f["unitMismatch"])
        # **既知事項の番号をこの文に書かない。**この文は候補の md の書き手への注に入るので、
        # 「P-165」の `165` が「データに無い数」として検査 1 に当たる(実測 2026-09-29)。
        # **消せば消える苦情を書き手の一覧に混ぜない。**
        self.assertFalse(re.search(r"\d", f["unitMismatch"]), f["unitMismatch"])
        # **単位が違うのは M6 だけ**(M4 は局面・M5 は手で、分子と分母がそろっている)。
        for item_id in ("M4", "M5"):
            for other in CA.menu_fractions(item_id, m):
                self.assertIsNone(other.get("unitMismatch"), (item_id, other))

    def test_f1_the_printed_fraction_is_the_one_the_judgment_divides_by(self):
        """**印字する分子 / 分母から作った割合が、判定が閾値に当てる割合と同じ。**"""
        m = self.materials()
        sm = m["sideMatch"]
        got = {f["label"]: (f["numerator"], f["denominator"]) for f in CA.menu_fractions("M4", m)}
        self.assertEqual(got["攻め"], (sm["attack"]["collapsed"], sm["attack"]["n"]))
        self.assertEqual(got["自玉側"], (sm["defense"]["collapsed"], sm["defense"]["n"]))
        for label, bucket in (("攻め", sm["attack"]), ("自玉側", sm["defense"])):
            num, den = got[label]
            self.assertEqual(num / den, CA.rate_of(bucket), label)

    def test_f2_the_fork_total_is_not_printed(self):
        """**`forkTotal` は分数に出てこない。**判定が割っていない数だから。"""
        m = self.materials(fork_total=999)
        numbers = []
        for f in CA.menu_fractions("M4", m):
            numbers += [f["numerator"], f["denominator"]]
        self.assertNotIn(999, numbers)

    def test_f3_m6_is_the_diagonal_over_the_row(self):
        m = self.materials()
        f = CA.menu_fractions("M6", m)[0]
        r = m["readCombined"]
        self.assertEqual((f["numerator"], f["denominator"]),
                         (r["sacrificeDiagonal"], r["sacrificeRowTotal"]))
        self.assertEqual(f["numerator"] / f["denominator"],
                         r["sacrificeDiagonal"] / r["sacrificeRowTotal"])

    def test_f4_m5_is_the_quick_move_after_a_long_think(self):
        m = self.materials()
        f = CA.menu_fractions("M5", m)[0]
        q = m["groups"]["min3"].after_long_think_quick
        self.assertEqual((f["numerator"], f["denominator"]), (q["collapsed"], q["n"]))
        self.assertEqual(f["numerator"] / f["denominator"], CA.rate_of(q))

    def test_f5_missing_material_gives_none_not_a_wrong_number(self):
        m = self.materials()
        m["sideMatch"] = None
        m["readCombined"] = None
        self.assertIsNone(CA.menu_fractions("M4", m))
        self.assertIsNone(CA.menu_fractions("M6", m))

    def test_f6_items_without_a_fraction_are_none(self):
        """**分数を持たない項目は `None`** ― 呼ぶ側が承認済みの表の文に落ちる。"""
        m = self.materials()
        for item_id in ("M1", "M2", "M3", "M7", "M8", "M9"):
            self.assertIsNone(CA.menu_fractions(item_id, m), item_id)

    def test_f7_the_names_say_what_is_counted(self):
        """**名前は判定関数が数えている中身。**将棋の言葉を足していないことを、語で固定する。"""
        m = self.materials()
        names = {f["label"]: f["name"] for f in CA.menu_fractions("M4", m)}
        self.assertIn("第 1 候補が攻めの手だった分かれ道のうち", names["攻め"])
        self.assertIn("実戦も攻めの手だった局面", names["攻め"])
        self.assertIn("自玉側", names["自玉側"])
        # M5 は `answer_facts.bullet_8` の承認済みの言い方から取った
        m5 = CA.menu_fractions("M5", m)[0]["name"]
        self.assertIn("10 秒以上", m5)
        self.assertIn("4 秒以内", m5)
        self.assertIn("崩れた手", m5)

    def test_f8_every_registered_fraction_is_allowed_by_check_1(self):
        """**印字する組は検査 1 の登録済みの組に在る**(無いと門が冊子を落とす)。

        `registered_pairs_of` は材料から組を作るので、**同じ材料で照合する**。
        """
        m = self.materials()
        pairs = set()

        def add(a, b):
            pairs.add((a, b)); pairs.add((b, a))

        sm = m["sideMatch"]
        add(sm["attack"]["n"], sm["attack"]["collapsed"])
        add(sm["defense"]["n"], sm["defense"]["collapsed"])
        r = m["readCombined"]
        add(r["sacrificeRowTotal"], r["sacrificeDiagonal"])
        q = m["groups"]["min3"].after_long_think_quick
        add(q["n"], q["collapsed"])
        for item_id in ("M4", "M5", "M6"):
            for f in CA.menu_fractions(item_id, m):
                self.assertIn((f["numerator"], f["denominator"]), pairs, f"{item_id} / {f['name']}")


class MenuThresholdsTest(unittest.TestCase):
    """**判定の線を名前つきの表に出した**(2026-09-29。人間の決定「7 割の線を出す・道具上の仮置きと明記」)。

    **値は 1 バイトも変えていない** ― リテラルを 1 か所へ移しただけ(P-152 と同じ型:
    「判定だけが知っている数」を無くす)。この試験が見張るのは **(1) 値が元のリテラルと同じこと**、
    **(2) 判定が表を読んでいること**(値を変えると判定が変わる = 陽性対照)、
    **(3) 冊子に出せる形であること**(検査 1 が線の値を「材料に無い数」と言わないこと)。
    """

    materials = staticmethod(MenuFractionsTest.materials)

    def test_t1_the_values_are_the_original_literals(self):
        """**元のリテラルと同一。**`0.7`(M4 の線)と `2`(M5 の倍率)。

        **この 2 つは承認済みの表の側(判断的知識)なので、道具の側では変えない。**
        変えたくなったら人間の承認を経る ― この試験が落ちることでそれが分かる。
        """
        self.assertEqual(CA.MENU_THRESHOLDS["M4"]["line"], 0.7)
        self.assertEqual(CA.MENU_THRESHOLDS["M5"]["times"], 2)

    def test_t2_m4_reads_the_table(self):
        """**陽性対照**: 線を下げると同じ材料で判定が変わる(判定が表を読んでいる証拠)。"""
        m = self.materials()  # 攻め 65/107 = 0.607・自玉側 76/132 = 0.576
        self.assertTrue(CA.m4_holds(m))
        saved = CA.MENU_THRESHOLDS["M4"]["line"]
        try:
            CA.MENU_THRESHOLDS["M4"]["line"] = 0.5
            self.assertFalse(CA.m4_holds(m), "線を 0.5 にしても成り立つ = 判定が表を読んでいない")
        finally:
            CA.MENU_THRESHOLDS["M4"]["line"] = saved
        self.assertTrue(CA.m4_holds(m))

    def test_t3_m5_reads_the_table(self):
        """**陽性対照**: 倍率を上げると同じ材料で判定が変わる。"""
        m = self.materials()  # 長考直後 7/41 = 0.171・0〜1 秒 22/531 = 0.041
        self.assertTrue(CA.m5_holds(m))
        saved = CA.MENU_THRESHOLDS["M5"]["times"]
        try:
            CA.MENU_THRESHOLDS["M5"]["times"] = 10
            self.assertFalse(CA.m5_holds(m), "倍率を 10 にしても成り立つ = 判定が表を読んでいない")
        finally:
            CA.MENU_THRESHOLDS["M5"]["times"] = saved

    def test_t4_the_line_can_be_printed_without_tripping_check_1(self):
        """**線の値を冊子に出せる形か**(P-177 の歯止め)。

        検査 1 は小数の**小数点以下を整数として読む**(`0.61` → 61)。**`0.7` は両方の桁が
        `SMALL_NUMBER_MAX` 以下なので数として拾われない** ― だから材料に無くても落ちない。
        **`0.75` のような線に変えると、検査 1 が「75 が材料に無い」と言って冊子が組めなくなる。**
        そのときこの試験が落ちるので、**線を変える人がその場で気づく。**
        """
        for item_id, spec in CA.MENU_THRESHOLDS.items():
            for key in ("line", "times"):
                if key not in spec:
                    continue
                ratio, fractions, percents, plains = CA.scan_numbers(f"線は {spec[key]} です")
                self.assertFalse(ratio, (item_id, key))
                self.assertEqual((fractions, percents, plains), ([], [], []),
                                 f"{item_id} の {key} = {spec[key]} は検査 1 が数として拾う"
                                 "(材料に無い数として冊子が落ちる)")

    def test_t4b_the_words_of_the_line_avoid_the_banned_ratio_words(self):
        """**「倍」「割」を使わない**(検査 1 が「使わない」で落とす語)。

        人間の決定の語は「7 割」だが、**検査 1 は数字 + 「割」を落とす**(2026-09-29 に実測)。
        だから冊子に出る語は `0.7` と「2 つぶん」である。
        """
        for item_id, spec in CA.MENU_THRESHOLDS.items():
            ratio, _f, _p, _pl = CA.scan_numbers(spec["what"])
            self.assertFalse(ratio, f"{item_id} の線の説明に「倍」「割」が入っている: {spec['what']}")

    def test_t5_the_comparison_pair_comes_from_the_materials(self):
        """**M5 の「比べる相手」は判定が見ている `by_spent[0]` そのもの。**

        批評席 (a) は 3 周続けて「長考直後でない手の崩れ率が無いので前提が数から出ているか分からない」
        と書いた。**その数は判定の中に在った** ― 印字するだけで閉じる。
        """
        got = CA.menu_threshold_of("M5", self.materials())
        self.assertEqual(got["other"]["numerator"], 22)
        self.assertEqual(got["other"]["denominator"], 531)
        self.assertEqual(got["other"]["unit"], "手")
        self.assertEqual(got["times"], 2)

    def test_t6_an_item_without_a_line_says_so(self):
        """線を持たない項目は `None`(勝手に線を作らない)。"""
        self.assertIsNone(CA.menu_threshold_of("M8", self.materials()))

    def test_t7_no_materials_means_no_line(self):
        """材料が無ければ線も出さない(0 除算も推測もしない)。"""
        self.assertIsNone(CA.menu_threshold_of("M5", self.materials(zero_to_one=(0, 0))))


class SideMatchRowsTest(unittest.TestCase):
    """**局面ごとの側**(P-164 の項目 3。2026-09-29)。

    実物で測った ― `whatif-v2` の fork 局面は 404 行で、**`(kifuId, displayPly)` は 404 個で一意**。
    **`sfen` では結合しない**(一意は 403 で、重複した 1 件は第 1 候補の側が
    `defense` と `none` で食い違う ― `sfen` で結合すると印が 2 通りになる局面ができる)。
    """

    @staticmethod
    def write(dir_path, kifu_id, positions):
        path = os.path.join(dir_path, f"{kifu_id}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for ply, display_ply, top1, actual in positions:
                f.write(json.dumps({
                    "kind": "position", "scenes": {"fork": True},
                    "ply": ply, "displayPly": display_ply, "sfen": f"sfen-{kifu_id}-{ply}",
                    "candidates": [{"side": top1}], "actualSide": actual,
                }, ensure_ascii=False) + "\n")

    def test_r0_the_opposite_side_count_and_its_denominator(self):
        """**側が逆だった分かれ道(長考で絞らない)**(2026-09-29。③ の比べる相手)。

        **分母は「第 1 候補の側が 1 つだった分かれ道」(攻め + 自玉側)で、`forkTotal` ではない。**
        「両方」「どちらでもない」は**逆になりえない**ので分母にも入れない ―
        `forkTotal` を分母にすると、**逆になりえない局面を分母に入れた率**になる。
        **合成材料で両者をわざと違う数にして測る**(同じ数なら取り違えが測れない)。
        """
        with tempfile.TemporaryDirectory() as d:
            # 逆 2 件(攻め→自玉側・自玉側→攻め)、同じ側 2 件、both 1 件、none 1 件。
            # 攻め + 自玉側 = 4、forkTotal = 6 ― **わざと違う数にする。**
            self.write(d, "g01", [(1, 1, "attack", "defense"),
                                  (2, 2, "defense", "attack"),
                                  (3, 3, "attack", "attack"),
                                  (4, 4, "defense", "both"),
                                  (5, 5, "both", "attack"),
                                  (6, 6, "none", "defense")])
            sm = CA.side_match_of([d])
            self.assertEqual(sm["forkTotal"], 6)
            self.assertEqual(sm["attack"]["n"] + sm["defense"]["n"], 4)
            self.assertEqual(sm["opposite"], {"numerator": 2, "denominator": 4},
                             "分母が forkTotal になっている(逆になりえない局面を分母に入れている)")

    def test_r1_the_key_is_the_kifu_id_and_the_display_ply(self):
        """**鍵は `(kifuId, displayPly)`。**`ply` で引くと、先後で番号が違う局面を取り違える。"""
        with tempfile.TemporaryDirectory() as d:
            # `ply` と `displayPly` を**わざと違う値**にする(同じ値なら取り違えが測れない)。
            self.write(d, "g01", [(9, 10, "attack", "attack"), (19, 20, "defense", "attack")])
            sm = CA.side_match_of([d])
            self.assertEqual(sorted(sm["rows"]), [("g01", 10), ("g01", 20)])
            self.assertEqual(CA.side_match_mark_of(sm, "g01", 10),
                             {"label": "攻め", "inNumerator": True})
            self.assertEqual(CA.side_match_mark_of(sm, "g01", 20),
                             {"label": "自玉側", "inNumerator": False})
            # `ply` の値では引けない。
            self.assertIsNone(CA.side_match_mark_of(sm, "g01", 9))

    def test_r2_a_duplicate_key_is_dropped(self):
        """**同じ鍵が 2 度来たら、その鍵の印を捨てる**(黙って片方を採らない)。

        実物では起きないが、**起きたときに断定しない**ことが要る ―
        実物の `sfen` の重複 1 件は側が食い違っていた。
        """
        with tempfile.TemporaryDirectory() as d:
            self.write(d, "g01", [(9, 10, "attack", "attack"), (11, 10, "defense", "attack")])
            sm = CA.side_match_of([d])
            self.assertIsNone(sm["rows"][("g01", 10)])
            self.assertIsNone(CA.side_match_mark_of(sm, "g01", 10))
            # **合算は捨てない**(分数は 2 局面とも数える ― 判定は動かさない)。
            self.assertEqual(sm["attack"]["n"], 1)
            self.assertEqual(sm["defense"]["n"], 1)

    def test_r3_the_rows_agree_with_the_totals(self):
        """**局面ごとと合算が同じ走査から来る。**別に数え直せば、同じ言葉に 2 つの分母が付く。"""
        with tempfile.TemporaryDirectory() as d:
            self.write(d, "g01", [(1, 1, "attack", "attack"), (2, 2, "attack", "defense"),
                                  (3, 3, "defense", "both"), (4, 4, "both", "attack")])
            self.write(d, "g02", [(1, 1, "defense", "defense")])
            sm = CA.side_match_of([d])
            rows = [v for v in sm["rows"].values() if v]
            attack = [r for r in rows if r["top1Side"] == "attack"]
            defense = [r for r in rows if r["top1Side"] == "defense"]
            self.assertEqual(len(attack), sm["attack"]["n"])
            self.assertEqual(len(defense), sm["defense"]["n"])
            self.assertEqual(sum(1 for r in attack if r["actualSide"] in ("attack", "both")),
                             sm["attack"]["collapsed"])
            self.assertEqual(sum(1 for r in defense if r["actualSide"] in ("defense", "both")),
                             sm["defense"]["collapsed"])
            self.assertEqual(sm["forkTotal"], 5)
            # 側が「両方」の局面は分母に入らない ― 印も付かない。
            self.assertIsNone(CA.side_match_mark_of(sm, "g01", 4))



class SideWordIsOnePlaceTest(unittest.TestCase):
    """**側の語は 1 か所**(P-185。2026-09-29。司令塔の決定「自玉側」に統一)。

    実測で **2 通り**が同じ顧客の手元に出ていた: 本編「自玉側」20 件・付録 3「守り」3 件
    (批評席 (a) が 6 周目に実物で挙げ、私が封をした PDF で数え直した)。
    語の表は顧客に出る道に **4 つ**あった ― `check_answer.SIDE_JP`(本編)・
    `render_direct.SIDE_JP`(付録 3)・`render_time_cause.VALUE_LABELS` の 2 つ(付録 4)・
    `fig1.SIDE_SHORT`(本編の図)。**ここを 1 か所にして、他は束縛する。**

    **字面では見ない。**「守り」を消した説明のコメント自体に当たるため(2026-09-29 に 4 回踏んだ型)。
    **他のファイルは import できない**(`sys.argv` を読んで走る)ので、
    **該当の代入だけを `ast` で取り出し、偽の `check_answer` を渡して動かす** ―
    写しに戻したら、偽の目印が出てこないので落ちる。
    """

    # 側の語の表を持つ(= 束縛すべき)ファイルと、その中の代入の名前。
    BOUND = (("render_direct.py", "SIDE_JP"), ("fig1.py", "SIDE_SHORT"))
    MARK = {"attack": "＜攻＞", "defense": "＜自＞", "both": "＜両＞", "none": "＜無＞"}

    def _exec_assign(self, name, target, ns):
        import ast
        src = read_text(os.path.join(HERE, name))
        tree = ast.parse(src)
        found = [n for n in tree.body
                 if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", "") == target for t in n.targets)]
        self.assertEqual(len(found), 1,
                         f"{name} の {target} の代入が {len(found)} 個(1 個のはず)")
        ns = dict(ns)
        exec(compile(ast.Module(found, []), f"<{name}>", "exec"), ns)  # noqa: S102
        return ns[target]

    def test_s1_the_word_is_the_one_the_commander_chose(self):
        self.assertEqual(CA.SIDE_JP["defense"], "自玉側")
        self.assertEqual(CA.SIDE_JP["attack"], "攻め")
        self.assertEqual(sorted(CA.SIDE_JP), ["attack", "both", "defense", "none"])

    def test_s2_the_two_key_view_is_derived_from_the_four_key_table(self):
        """**2 鍵の表は写しではなく view。**

        値の一致だけを見ると**写しでも通る**(同じ語を書けば等しい)ので、
        `check_answer.py` の代入を取り出し、**偽の 4 鍵の表**を渡して動かす ―
        写しに書き換えたら、偽の語が出てこないので落ちる。
        """
        self.assertEqual(sorted(CA.SIDE_LABEL_JP), ["attack", "defense"])
        got = self._exec_assign("check_answer.py", "SIDE_LABEL_JP", {"SIDE_JP": self.MARK})
        self.assertEqual(got, {"attack": "＜攻＞", "defense": "＜自＞"},
                         "SIDE_LABEL_JP が 4 鍵の表から作られていない(写しになっている)")

    def test_s3_no_side_table_says_mamori(self):
        """**どの表にも「守り」が無い**(振る舞いで見る ― 表を動かして中身を見る)。"""
        for name, target in self.BOUND:
            table = self._exec_assign(name, target, {"check_answer": CA})
            for key, word in table.items():
                self.assertNotIn("守り", word, f"{name} の {target}[{key!r}] = {word}")

    def test_s4_the_other_files_bind_instead_of_copying(self):
        """**偽の表を渡すと、偽の語が出てくる**(= 束縛している)。写しなら出てこない。"""
        import types
        fake = types.SimpleNamespace(SIDE_JP=self.MARK)
        rd = self._exec_assign("render_direct.py", "SIDE_JP", {"check_answer": fake})
        self.assertEqual(rd, self.MARK, "render_direct が側の語を自分で持っている")
        f1 = self._exec_assign("fig1.py", "SIDE_SHORT", {"check_answer": fake})
        self.assertEqual(f1, {"attack": "＜攻＞側", "defense": "＜自＞"},
                         "fig1 が側の語を自分で持っている")

    def test_s5_the_time_cause_table_binds_the_same_one_place(self):
        """付録 4 の 2 つの欄も同じ 1 か所を引く(`ast` で**値の形**を見る)。

        `render_time_cause.py` は冒頭で材料を読むので import できない。
        `VALUE_LABELS` の中の `top1Side`・`actualSide` が**辞書の literal ではなく名前**であること、
        その名前が `check_answer` から束縛されていることを見る。
        """
        import ast
        tree = ast.parse(read_text(os.path.join(HERE, "render_time_cause.py")))
        # **どの名前から束縛したかを見る**(独立監査 2026-09-29 の REVISE (a))。
        # `as` の名前だけを見ていたので、**`SIDE_LABEL_JP`(2 鍵の view)に差し替えても 5 本とも緑**だった。
        # 2 鍵の表を渡すと、`both`・`none` の値が来たときに `KeyError` になる
        # (付録 3 の実物では「攻め・自玉側両方」が 38 件出ている = 実際に来る値)。
        pairs = {(a.name, a.asname or a.name) for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) and (n.module or "") == "check_answer"
                 for a in n.names}
        self.assertIn(("SIDE_JP", "CA_SIDE_JP"), pairs,
                      f"render_time_cause が 4 鍵の SIDE_JP を束縛していない(束縛は {sorted(pairs)})")
        self.assertNotIn("SIDE_LABEL_JP", {name for name, _ in pairs},
                         "付録 4 が 2 鍵の view を引いている(both・none が来ると KeyError)")
        labels = [n for n in tree.body if isinstance(n, ast.Assign)
                  and any(getattr(t, "id", "") == "VALUE_LABELS" for t in n.targets)]
        self.assertEqual(len(labels), 1)
        got = {}
        for k, v in zip(labels[0].value.keys, labels[0].value.values):
            if getattr(k, "value", None) in ("top1Side", "actualSide"):
                got[k.value] = ast.unparse(v)
        self.assertEqual(got, {"top1Side": "CA_SIDE_JP", "actualSide": "CA_SIDE_JP"})

class MarkFamilyTest(unittest.TestCase):
    """**本編の印の家族の一覧 `MARK_TAG_RES` と `strip_marks`**(門の数え方の束。2026-10-05。裁定 Q2)。"""

    # **実物の印の字**(封じた本編 2026-09-29 の 20・28 行目、⑥ 束 2 の出力、answer_facts の優先順位の印)。
    REAL = {
        "pos": "<!-- pos: 11/48 付録3 3 分 -->",
        "menu": "<!-- menu: M4 -->",
        "priority": "<!-- priority: M4 -->",
        "agg": "<!-- agg: sideMatch.attack -->",
        "ans": "<!-- ans: q1 unanswerable -->",
    }
    BY_NAME = {"menu": CA.MENU_TAG_RE, "priority": CA.PRIORITY_TAG_RE, "pos": CA.POS_TAG_RE,
               "agg": CA.AGG_TAG_RE, "ans": CA.ANS_TAG_RE}

    def test_m1_the_family_is_the_five_kinds_that_can_appear_in_the_counted_lines(self):
        """**5 種で足りることは測った**(2026-10-05): コードが書く印の種類は 8(TODO・agg・ans・appendix・menu・pos・priority・sec)。
        問いの節に出るのは `ans` だけ、(xi) の行に出るのは `agg` だけ(合成の顧客フォルダの本編で実測)。
        `sec`・`appendix` は数え方の節にだけ出る(付録へ回す印)、`TODO` は門の前に消える。だから 5。"""
        self.assertEqual(len(CA.MARK_TAG_RES), 5)
        self.assertEqual(set(CA.MARK_TAG_RES), set(self.BY_NAME.values()))
        kinds = set()
        for name in os.listdir(HERE):
            if name.endswith(".py") and not name.endswith("_test.py"):
                kinds |= set(re.findall(r"<!--\s*([a-zA-Z]+):", open(os.path.join(HERE, name), encoding="utf-8").read()))
        self.assertEqual(kinds, {"TODO", "agg", "ans", "appendix", "menu", "pos", "priority", "sec"})
        self.assertEqual(kinds - set(self.REAL), {"TODO", "appendix", "sec"})

    def test_m2_each_regex_matches_its_own_real_mark_and_no_other(self):
        for name, mark in self.REAL.items():
            for other, tag_re in self.BY_NAME.items():
                hit = tag_re.search(mark) is not None
                self.assertEqual(hit, name == other, (name, other))

    def test_m3_strip_marks_removes_the_whole_family_and_nothing_else(self):
        line = "文" + "".join(self.REAL.values()) + "。"
        self.assertEqual(CA.strip_marks(line), "文。")
        self.assertEqual(CA.strip_marks("印の無い行 25 局"), "印の無い行 25 局")
        # 家族の外(数え方の節の印)は剥かない ― 数える節には出ないことを測って 5 にした。
        self.assertEqual(CA.strip_marks("- 題<!-- sec: 付録1/形勢の流れ -->"), "- 題<!-- sec: 付録1/形勢の流れ -->")
        for name, mark in self.REAL.items():
            self.assertNotIn(mark, CA.strip_marks("a" + mark + "b"), name)
            self.assertEqual(CA.strip_marks("a" + mark + "b"), "ab", name)


# **`__main__` の塊はファイルの末尾に 1 つだけ**(P-181。2026-09-29)。
# 途中に置くと `unittest.main()` の `sys.exit` で**後ろのクラスが定義されず、直接実行で 1 本も走らない**
# (門の `discover` では走るので赤にならない ―「手元で回して OK だった」が嘘になる)。
if __name__ == "__main__":
    unittest.main()
