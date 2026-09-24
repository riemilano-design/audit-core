# -*- coding: utf-8 -*-
# check_answer.py の検査 7(局面の参照)の試験。2026-09-24 の人間の委任(docs/STEP_DELIVER1_PLAN_2026-09-25.md
# §11.7)。「本文が指した局面が、指した付録に実在するか」を確かめる `<!-- pos: G/P 付録N -->` の印を検査する。
#
# answer_facts_test.py と同じ流儀: pytest 等の外部ライブラリは使わない(標準ライブラリ unittest)。材料は
# 本物の JSON ファイル・gitignore の実データを読まず、この試験の中に持つ小さな合成 `ctx`(`check_pos_tags`・
# `check_line_numbers` が読む欄だけを持つ辞書)。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/check_answer_test.py`
import os
import sys
import unittest
from types import SimpleNamespace

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
        # 付録 1〜3 は局面あり、付録 4 は「材料はあるが局面が無い」場合を既定にする(検査 3 の試験用)。
        # 個々の試験で必要に応じて作り直す。
        self.positions = {
            1: {(1, 10), (2, 20)},  # 付録 1: patient の events[]・escapeScenes[]
            2: {(3, 33)},  # 付録 2: whatif の representative
            3: {(5, 59), (9, 77)},  # 付録 3: direct_answers の局面と final_positions の最終局面
            4: None,  # 付録 4: --time-cause が渡されていない(試験ごとに上書きする)
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

    # 3. 材料が渡されていない付録の宣言は落ちる(付録 4。--time-cause が無い = positions[4] is None)。
    def test_material_not_provided_fails(self):
        problems = self.check("参考: <!-- pos: 5/59 付録4 -->")
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("材料が渡されていない", reason)

    # 3b. 付録 4 は材料が渡されているが局面の印字が 1 つも無い(--time-cause はあるが longestMove が無い)場合、
    # 「材料が渡されていない」とは別の理由(「局面の材料を持たない」)で落ちる。
    def test_appendix4_empty_positions_fails_with_distinct_message(self):
        positions = dict(self.positions)
        positions[4] = set()  # --time-cause は渡されたが longestMove が 1 件も無い
        problems = self.check("参考: <!-- pos: 5/59 付録4 -->", positions=positions)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("局面の材料を持たない", reason)

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


class PatientPositionsOfTest(unittest.TestCase):
    """司令塔の監査 REVISE(付録 1 の材料が過大許可だった件)。`patient_positions_of`(材料構築関数そのもの)を
    直接呼び、`kind == "matedIfPass"` の events は材料から除かれることを確かめる(`kind == "drop"` の行だけが
    `render_appendix.py`〈`_tail.py` の付録 6〉で印字されるため)。`escapeScenes` は絞り込みが無いので
    全件材料になる。`PatientFile.__init__` は `summary`・`time` 等の全欄を要求するため、ここでは
    `patient_positions_of` が読む `.raw` 欄だけを持つ `SimpleNamespace`(`answer_facts_test.py` と同じ流儀)を使う。"""

    def make_patient_file(self, events, escape_scenes):
        return SimpleNamespace(raw={"events": events, "escapeScenes": escape_scenes})

    def test_mated_if_pass_events_excluded_from_positions(self):
        events = [
            {"gameNo": 1, "ply": 10, "kind": "drop"},
            {"gameNo": 2, "ply": 20, "kind": "matedIfPass"},
        ]
        positions = CA.patient_positions_of([self.make_patient_file(events, [])])
        self.assertIn((1, 10), positions)
        self.assertNotIn((2, 20), positions)

    def test_escape_scenes_not_filtered_by_kind(self):
        escape_scenes = [{"gameNo": 3, "displayPly": 30}]
        positions = CA.patient_positions_of([self.make_patient_file([], escape_scenes)])
        self.assertIn((3, 30), positions)

    def test_no_patient_files_returns_none(self):
        self.assertIsNone(CA.patient_positions_of([]))

    def test_matedIfPass_position_fails_check_pos_tags_as_not_in_material(self):
        """材料構築関数(`patient_positions_of`)を通した結果を `check_pos_tags` に渡し、`matedIfPass` の
        (gameNo, ply) を指す `<!-- pos: 2/20 付録1 -->` が「材料に無い(検査 7)」で落ちることを確かめる
        (今までの試験は合成 ctx だけで材料構築関数を一度も通していなかった、という監査指摘への対応)。"""
        events = [
            {"gameNo": 1, "ply": 10, "kind": "drop"},
            {"gameNo": 2, "ply": 20, "kind": "matedIfPass"},
        ]
        positions_1 = CA.patient_positions_of([self.make_patient_file(events, [])])
        ctx = make_ctx({1: positions_1, 2: set(), 3: set(), 4: set()})
        problems = []
        CA.check_pos_tags("<!-- pos: 2/20 付録1 -->", ctx, problems, 1)
        self.assertEqual(len(problems), 1)
        _, reason, _ = problems[0]
        self.assertIn("検査 7", reason)
        self.assertIn("材料に無い", reason)
        self.assertIn("2/20", reason)
        # 対照: drop の方(材料にある)は通る。
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
