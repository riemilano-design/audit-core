# -*- coding: utf-8 -*-
# `exit_groups.py`(戦型の群ごとの再集計)の試験。
#
# 【この道具の危ない所】**群に割った数が材料の合計と合わないまま顧客に出ること。**
# 群が 4 局・3 局しかないので、割合を出す・群どうしを比べる・「差がある」と言う、も越権になる。
# **材料は合成**(実物での確認は門にできない)。
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_answer as CA  # noqa: E402
import exit_candidates as EC  # noqa: E402
import exit_groups as EGR  # noqa: E402


def recognition(classes):
    """`gNN` → 群 の対応だけを持つ最小の認識。"""
    return {"rows": {gid: {"proposalSignatureClass": cls} for gid, cls in classes.items()}}


def game(no, gid, result="勝ち", scores=(0,), ahead=False):
    """合成の 1 局。`ahead` が真なら +300 を 1 つ挟む(優勢になった局)。"""
    series = list(scores)
    if ahead:
        series = [0, 400] + series
    return {"no": no, "id": gid, "result": result, "scores": series, "events": 99}


def patient(games, ahead_games=None, ahead_loss=None, fell=None):
    """`findings` と `overview` は**番人が突き合わせる合計**を持つ(実物と同じ形)。"""
    n_ahead = sum(1 for g in games if EGR.is_ahead(g)) if ahead_games is None else ahead_games
    n_loss = (sum(1 for g in games if EGR.is_ahead(g) and g["result"] == "負け")
              if ahead_loss is None else ahead_loss)
    n_fell = sum(EGR.collapses_of(g) for g in games) if fell is None else fell
    return {"summary": {"games": len(games)}, "games": games,
            "overview": {"fell": n_fell},
            "findings": [{"kind": "aheadLoss",
                          "numbers": {"aheadGames": n_ahead, "aheadLossGames": n_loss}}]}


BASE_GAMES = [game(1, "g01", ahead=True), game(2, "g02", result="負け", ahead=True),
              game(3, "g03"), game(4, "g04", result="負け", ahead=True)]
BASE_CLASSES = {"g01": "多数の核", "g02": "多数の核", "g03": "それ以外", "g04": "署名なし"}


class GroupsTest(unittest.TestCase):
    def test_01_the_groups_come_out_in_order_with_machine_keys(self):
        """**機械の名は局数を含まない**(材料が変われば鍵が変わってしまう)。"""
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        self.assertEqual([r["key"] for r in rows], ["core", "other", "noSignature"])
        self.assertEqual([r["games"] for r in rows], [2, 1, 1])
        self.assertEqual([r["gameNos"] for r in rows], [[1, 2], [3], [4]])
        for r in rows:
            self.assertNotIn(str(r["games"]), r["key"])

    def test_02_the_headings_are_provisional_and_name_no_opening(self):
        """**戦型の名前も「普段指さない戦型」も出さない**(顧客向けの分類として未承認)。"""
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        self.assertEqual([r["label"] for r in rows], ["群 A", "群 B", "群 C"])
        text = "\n".join(EGR.lines_of(rows, EC.CROSS_PHRASE_JP))
        for banned in ("矢倉", "戦型", "普段", "居飛車", "振り飛車", "のような形"):
            self.assertNotIn(banned, text, banned)

    def test_03_no_rates_and_no_comparison(self):
        """**割合・%・群どうしを比べる語・「差」の判定を出さない。**"""
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        text = "\n".join(EGR.lines_of(rows, EC.CROSS_PHRASE_JP))
        for banned in ("%", "割合", "率", "より多い", "より少ない", "差が", "傾向", "比べ", "倍"):
            self.assertNotIn(banned, text, banned)
        # 「/」も出さない(分数に見える形で並べない)。
        self.assertNotIn("/", text)

    def test_04_an_unknown_class_falls(self):
        """**知らない群は落ちる。**呼び方を人が決める前に顧客へ出さない。"""
        classes = dict(BASE_CLASSES, g03="新しい群")
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(classes), patient(BASE_GAMES))
        self.assertIn("知らない群", str(cm.exception))

    def test_05_a_game_set_mismatch_falls(self):
        """**局の集合が違えば落ちる**(別の 25 局を見た認識を黙って使わない)。"""
        classes = {k: v for k, v in BASE_CLASSES.items() if k != "g04"}
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(classes), patient(BASE_GAMES))
        self.assertIn("局の集合が合わない", str(cm.exception))

    def test_06_a_total_mismatch_falls(self):
        """**群に割った合計が材料の合計と違えば落ちる。**黙って違う数を出さない。"""
        for field, want in (("aheadGames", 99), ("aheadLossGames", 99)):
            p = patient(BASE_GAMES)
            p["findings"][0]["numbers"][field] = want
            with self.assertRaises(EGR.ExitGroupsError) as cm:
                EGR.group_rows(recognition(BASE_CLASSES), p)
            self.assertIn("違う", str(cm.exception))
        p = patient(BASE_GAMES)
        p["overview"]["fell"] = 12345
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(BASE_CLASSES), p)
        self.assertIn("崩れ", str(cm.exception))
        p = patient(BASE_GAMES)
        p["summary"]["games"] = 99
        with self.assertRaises(EGR.ExitGroupsError):
            EGR.group_rows(recognition(BASE_CLASSES), p)

    def test_07_ahead_uses_the_printed_threshold(self):
        """**優勢は +300 以上。**`None` が混じっても落ちない(実物に 4 件ある)。"""
        self.assertTrue(EGR.is_ahead({"scores": [0, None, 300]}))
        self.assertFalse(EGR.is_ahead({"scores": [0, None, 299]}))
        self.assertFalse(EGR.is_ahead({"scores": []}))

    def test_08_collapses_come_from_the_score_series(self):
        """**崩れは `scores` の隣り合う組**。区分が 1 段以上下がった回数。

        **`games[].events` は崩れではない** ― 実物で 133 で、冊子の 79 と合わなかった
        (合計の番人が捕まえた)。`events` の一覧に規則を当てても 53 で合わない。
        """
        # 互角 → 劣勢(1 回)、劣勢 → 劣勢(0 回)、優勢 → 互角(1 回)
        self.assertEqual(EGR.collapses_of({"scores": [0, -400, -500, 400, 0]}), 2)
        # 上がる側は数えない。
        self.assertEqual(EGR.collapses_of({"scores": [-400, 0, 400]}), 0)
        # `None` は飛ばす(前後どちらでも落ちない)。
        self.assertEqual(EGR.collapses_of({"scores": [0, None, -400]}), 0)
        # **`events` の欄を見ていないこと**(合成の局は events=99 を持っている)。
        self.assertEqual(EGR.collapses_of(game(1, "g01")), 0)

    def test_09_side_match_is_split_not_recounted(self):
        """**側の一致は `side_match_of` の局面ごとの欄を振り分けるだけ。**"""
        sm = {"attack": {"n": 2, "collapsed": 1}, "defense": {"n": 1, "collapsed": 1},
              "forkTotal": 9,
              "rows": {("g01", 10): {"top1Side": "attack", "actualSide": "attack"},
                       ("g01", 20): {"top1Side": "attack", "actualSide": "defense"},
                       ("g03", 30): {"top1Side": "defense", "actualSide": "both"},
                       ("g04", 40): {"top1Side": "both", "actualSide": "attack"},
                       ("g02", 50): None}}
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES), None, sm)
        by = {r["key"]: r["sideMatch"] for r in rows}
        self.assertEqual(by["core"]["attack"], {"n": 2, "collapsed": 1})
        self.assertEqual(by["other"]["defense"], {"n": 1, "collapsed": 1})
        # 側が「両方」の局面と、重複で捨てた局面は分母に入らない。
        self.assertEqual(by["noSignature"]["attack"], {"n": 0, "collapsed": 0})

    def test_10_a_side_total_mismatch_falls(self):
        """**側の合計が合わなければ落ちる。**"""
        sm = {"attack": {"n": 99, "collapsed": 1}, "defense": {"n": 1, "collapsed": 1},
              "forkTotal": 9,
              "rows": {("g01", 10): {"top1Side": "attack", "actualSide": "attack"}}}
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES), None, sm)
        self.assertIn("側の一致", str(cm.exception))

    def test_11_the_cross_uses_only_the_registered_tags(self):
        """**`sacrifice` は入れない**(`CROSS_TAGS` が `drop` だけ = P-156 の決定を広げない)。"""
        answers = [{"gameNo": 1, "kifuId": "g01", "top1Tags": {"drop": True, "sacrifice": True},
                    "actualTags": {"drop": True, "sacrifice": True}},
                   {"gameNo": 3, "kifuId": "g03", "top1Tags": {"drop": True, "sacrifice": True},
                    "actualTags": {"drop": False, "sacrifice": False}}]
        direct = {"raw": [{"kind": "direct_answers", "answers": answers}]}
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES), direct)
        for r in rows:
            self.assertEqual(set(r["cross"]), set(CA.CROSS_TAGS))
            self.assertNotIn("sacrifice", r["cross"])
        by = {r["key"]: r["cross"]["drop"] for r in rows}
        self.assertEqual(by["core"]["positions"], 1)
        self.assertEqual(by["core"]["bothPositions"], 1)
        self.assertEqual(by["other"]["bothPositions"], 0)

    def test_12_a_cross_total_mismatch_falls(self):
        """**観測の合計が合わなければ落ちる。**群に入らない局の局面があるとここで止まる。"""
        answers = [{"gameNo": 9, "kifuId": "g99", "top1Tags": {"drop": True},
                    "actualTags": {"drop": True}}]
        direct = {"raw": [{"kind": "direct_answers", "answers": answers}]}
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES), direct)
        self.assertIn("観測", str(cm.exception))

    def test_13_the_words_come_from_one_place(self):
        """**側の語と「駒を打つ手」を写さない。**"""
        src = io.open(os.path.join(HERE, "exit_groups.py"), encoding="utf-8").read()
        self.assertIn("CA.SIDE_LABEL_JP", src)
        for word in ("攻め", "自玉側", "駒を打つ手"):
            self.assertNotIn(f'"{word}"', src, f"語を写している: {word}")

    def test_14_an_empty_recognition_falls(self):
        """`rows` が無い認識は落ちる(空の群を黙って出さない)。"""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.json")
            with io.open(path, "w", encoding="utf-8") as f:
                json.dump({"rows": {}}, f)
            with self.assertRaises(EGR.ExitGroupsError):
                EGR.load(path)


if __name__ == "__main__":
    unittest.main()
