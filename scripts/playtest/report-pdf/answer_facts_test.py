# -*- coding: utf-8 -*-
# answer_facts.py の試験(2026-09-24 の人間の決定「同じミスがおきないようにしといて」の再発防止)。
#
# 2 人目の顧客の納品で、数の照合は通るのに読み(解釈)の文が数に合わなかった事故が起きた
# (`bullet_4` の「『選択肢が多い局面で長考している』とは、分かれ道の印からは言えません」が
# 27/47 = 57% に対して結論が逆だった)。数の照合(`check_answer.py`)はこの種の間違いを見つけられない。
# この試験は、`render()` が返す 14 個の箇条書きの本文に、比較・解釈・因果・程度を述べる語
# (「読みの語」)が混ざっていないことを機械で検査する。
#
# pytest 等の外部ライブラリは使わない(このリポジトリに python の試験の前例が無いため、新しい依存を
# 増やさない)。材料は本物の JSON ファイル・gitignore の実データを読まず、この試験の中に持つ小さな
# 合成データ(`build_materials` 関数。`check_answer.py` の `CombinedGroup` 等と同じ形の属性だけを
# `types.SimpleNamespace` で用意する)。
#
# 実行: `python3 -X utf8 scripts/playtest/report-pdf/answer_facts_test.py`
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import answer_facts as AF  # noqa: E402

# 読みの語(機械が書かない。2026-09-24 の人間の決定の指示書に列挙されたもの)。比較・解釈・因果・程度を
# 述べる語で、数の箇条書きには出てはいけない。
READING_WORDS = [
    "言えません",
    "ことが多い",
    "ゆっくり",
    "ずっと",
    "消えています",
    "勝っていました",
    "共通しません",
    "返してきません",
    "より多い",
    "割合が高い",
    "多くは",
]


def build_materials(read_dir):
    """14 個の箇条書きすべてが `<!-- TODO: 読み -->` に落ちずに本文を返せる、最小の合成材料。
    数そのものは何でもよい(この試験は数の正しさではなく、文に読みの語が残っていないかだけを見る)。"""
    patient_min3 = SimpleNamespace(tag="min3", raw={"games": [{"id": "k1"}, {"id": "k2"}]})
    g3 = SimpleNamespace(
        games=5,
        time_up_losses={"n": 2, "m": 2},
        by_spent=[
            {"n": 30, "collapsed": 5},
            {"n": 0, "collapsed": 0},
            {"n": 0, "collapsed": 0},
            {"n": 6, "collapsed": 4},
        ],
        after_long_think_quick={"n": 4, "collapsed": 2},
    )
    g10 = SimpleNamespace(games=8, time_up_losses={"n": 1, "m": 1})

    tul_games = [
        {
            "group": "3分",
            "timeUpLoss": True,
            "phaseSpentSec": {"mid": 95, "early": 20},
            "remainingSec": 30,
            "longThinkCountByPhase": {"mid": 3},
            "longThinkStreakCount": 0,
            "longestMove": {"sec": 25},
            "midThinkTotal": {"sec": 40},
        },
        {
            "group": "3分",
            "timeUpLoss": True,
            "phaseSpentSec": {"mid": 88, "early": 18},
            "remainingSec": 15,
            "longThinkCountByPhase": {"mid": 3},
            "longThinkStreakCount": 0,
            "longestMove": {"sec": 22},
            "midThinkTotal": {"sec": 35},
        },
    ]
    tc_data = {
        "groups": [
            {
                "timeLimitSec": 180,
                "group": "3分",
                "other": {"games": 10, "medianMidSec": 40, "medianMidThinkSec": 18, "medianEarlySec": 25},
                "timeUpLoss": {"medianMidSec": 91.5, "medianEarlySec": 19},
            }
        ],
        "games": tul_games,
    }
    time_cause = {
        "raw": [tc_data],
        "groups": {
            "3分": SimpleNamespace(
                fork_fraction={"numerator": 9, "denominator": 16},
                opposite_side_fraction={"numerator": 3, "denominator": 9},
            )
        },
    }

    direct_entries = [
        {"kifuId": "k1", "gameNo": 3, "moves": 91, "scoreCp": 82},
        {"kifuId": "k3", "gameNo": 7, "moves": 64, "scoreCp": -50},
    ]
    direct = {
        "raw": [{"kind": "final_positions", "entries": direct_entries}],
        "totalCount": 12,
        "top1TagCounts": {"drop": 3, "sacrifice": 2, "capture": 5, "givesCheck": 2},
        "actualTagCounts": {"drop": 1, "sacrifice": 1},
        "top1SideCounts": {"attack": 7, "defense": 5},
    }

    read_combined = {
        "forkPositionsRead": 47,
        "firstVisibleNodesNoneCount": 10,
        "sacrificeRowTotal": 22,
        "sacrificeDiagonal": 9,
        "opponentReplyMatchesPv": {"matched": 30, "measured": 40},
    }

    side_match = {"attack": {"n": 10, "collapsed": 6}, "defense": {"n": 8, "collapsed": 5}}

    return {
        "patientFiles": [patient_min3],
        "groups": {"min3": g3, "min10": g10},
        "readCombined": read_combined,
        "sideMatch": side_match,
        "direct": direct,
        "timeCause": time_cause,
        "readDirs": [read_dir],
    }


class AnswerFactsRenderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        # `read_game_count` は `--read-dir` の *.jsonl の**ファイル数**を数えるだけ(中身は読まない)。
        for i in range(3):
            open(os.path.join(self._tmp.name, f"g{i}.jsonl"), "w", encoding="utf-8").close()

    def tearDown(self):
        self._tmp.cleanup()

    def render(self, has_time_search):
        materials = build_materials(self._tmp.name)
        md, missing = AF.render(materials, "テスト名", has_time_search)
        self.assertEqual(missing, [], f"材料が足りず TODO に落ちた箇条書きがある(試験の材料を直す): {missing}")
        return md

    def bullet_lines(self, md):
        return [line for line in md.split("\n") if line.startswith("- ")]

    def test_no_reading_words_in_bullets_without_time_search(self):
        bullets = self.bullet_lines(self.render(False))
        self.assertEqual(len(bullets), 14, "箇条書きが 14 本ではない(試験の材料を直す)")
        for line in bullets:
            for word in READING_WORDS:
                self.assertNotIn(word, line, f"読みの語「{word}」が箇条書きに残っている: {line}")

    def test_no_reading_words_in_bullets_with_time_search(self):
        # `--time-search` ありのときも bullet_9 に読みの文が付け足されないことを確かめる。
        bullets = self.bullet_lines(self.render(True))
        for line in bullets:
            for word in READING_WORDS:
                self.assertNotIn(word, line, f"読みの語「{word}」が箇条書きに残っている: {line}")

    def test_score_cp_sign_only_for_positive(self):
        # bullet_1: scoreCp の印字は正のときだけ + を付ける(負のとき「+-」にならない)。
        md = self.render(False)
        self.assertNotIn("+-", md)
        self.assertIn("+82", md)
        self.assertIn(" -50", md)


if __name__ == "__main__":
    unittest.main()
