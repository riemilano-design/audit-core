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
import exit_index as EI  # noqa: E402


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

    def test_02_the_headings_name_no_opening(self):
        """**戦型の名前も「普段指さない戦型」も出さない**(顧客向けの分類として未承認)。"""
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        # 合成の材料は 4 局なので、ラベルの局数も 4 になる(**値で焼いていない**)。
        self.assertEqual([r["label"] for r in rows],
                         ["この 4 局で多かった分類", "この 4 局でそれ以外だった分類",
                          "分類が取れない局"])
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


class GroupLabelTableTest(unittest.TestCase):
    """**F-1。packet の群 ↔ 冊子のラベルの対応表**(人間の決定 2026-10-01)。

    【顧客の PDF にどう出るか】本編の群の表の**行の見出し**と、観測の欄の**行の頭**に出る。
    封じた最終版はここに「普段の型」「普段と違う型」と書いていた ―
    **「25 局内で多かった」は「本人が普段指している」ではない**ので、言い換える(人間)。

    【ここで字で留める理由】**人が決めた中身を、試験の土台を表から作って測ると黙る**
    (2026-10-01 に 3 回踏んだ家族)。だからラベルの文字列は**字で**置く。
    """

    # 対応表の全部。**packet の鍵 → 冊子のラベルの型**(局数は型のまま)。
    WANT = {
        "core": "この {games} 局で多かった分類",
        "other": "この {games} 局でそれ以外だった分類",
        "noSignature": "分類が取れない局",
    }

    def test_l1_the_table_is_pinned_character_by_character(self):
        """**人間が決めたラベルを字で留める。**替えるには人間の判断が要る。"""
        self.assertEqual(EGR.GROUP_LABELS, self.WANT)

    def test_l2_the_table_covers_exactly_the_groups_that_are_printed(self):
        """**出す群と表の鍵が同じ集合。**片方の群だけ足した変異がここで落ちる。"""
        self.assertEqual(set(EGR.GROUP_LABELS), set(EGR.GROUP_ORDER))
        self.assertEqual(set(EGR.GROUP_LABELS), set(EGR.CLASS_KEYS.values()))
        self.assertEqual(len(EGR.GROUP_LABELS), 3)

    def test_l3_the_game_count_comes_from_the_material(self):
        """**局数は渡した値が入る**(値で焼く変異が落ちる)。**25 と 20 で違う文**になる。"""
        self.assertEqual(EGR.label_of("core", 25), "この 25 局で多かった分類")
        self.assertEqual(EGR.label_of("core", 20), "この 20 局で多かった分類")
        self.assertEqual(EGR.label_of("other", 25), "この 25 局でそれ以外だった分類")
        self.assertEqual(EGR.label_of("other", 20), "この 20 局でそれ以外だった分類")
        # **25 が別の顧客の冊子に出ない**(2026-09-30 に顧客に見える名前で実際に起きた型)。
        self.assertNotIn("25", EGR.label_of("core", 20))

    def test_l4_the_third_label_carries_no_game_count(self):
        """**「分類が取れない局」には局数が入らない**(3 つ目だけ型が違うことを留める)。"""
        self.assertNotIn("{games}", EGR.GROUP_LABELS["noSignature"])
        self.assertEqual(EGR.label_of("noSignature", 25), "分類が取れない局")
        self.assertEqual(EGR.label_of("noSignature", 20), "分類が取れない局")
        # 局数が無くても落ちない(型に穴が無いので材料を要求しない)。
        self.assertEqual(EGR.label_of("noSignature", None), "分類が取れない局")

    def test_l5_the_third_label_says_classification_not_formation(self):
        """**3 つ揃えて「分類」**(司令塔の判断)。3 つ目だけ「型」だと、
        **最初の 2 つが型であることを含意してしまう。**"""
        for key in EGR.GROUP_ORDER:
            self.assertIn("分類", EGR.GROUP_LABELS[key], key)
            self.assertNotIn("型", EGR.GROUP_LABELS[key], key)

    def test_l6_the_label_constants_carry_no_held_word(self):
        """**守りの 1 本目: ラベルの定数に「普段」が入っていない。**"""
        for key, template in EGR.GROUP_LABELS.items():
            for word in EGR.LABEL_FORBIDDEN_WORDS:
                self.assertNotIn(word, template, f"{key} に {word}")

    def test_l7_a_label_with_the_held_word_falls(self):
        """**黒名簿を空にする変異がここで赤くなる。**
        土台はラベルの定数から作らない ― **却下された字そのもの**を置く。"""
        for bad in ("普段の型", "普段と違う型", "この 25 局で普段指していた分類"):
            with self.assertRaises(EGR.ExitGroupsError, msg=bad) as cm:
                EGR.check_label_words(bad)
            self.assertIn("普段", str(cm.exception))
        # **正しいラベルは通る**(黒名簿を広げすぎた変異が落ちる)。
        for key in EGR.GROUP_ORDER:
            self.assertEqual(EGR.check_label_words(EGR.label_of(key, 25)),
                             EGR.label_of(key, 25))

    def test_l7b_label_of_passes_its_result_through_the_check(self):
        """**`label_of` が検査を通す。**表に却下された字が入ったら、
        **ラベルを作る所で止まる**(`check_label_words` の呼びを外す変異がここで赤くなる)。"""
        saved = dict(EGR.GROUP_LABELS)
        try:
            EGR.GROUP_LABELS["core"] = "普段の型 {games} 局"
            with self.assertRaises(EGR.ExitGroupsError) as cm:
                EGR.label_of("core", 25)
            self.assertIn("普段", str(cm.exception))
        finally:
            EGR.GROUP_LABELS.clear()
            EGR.GROUP_LABELS.update(saved)
        # **戻したことを確かめる**(土台が次の試験を汚さない)。
        self.assertEqual(EGR.GROUP_LABELS, self.WANT)

    def test_l8_the_held_word_is_not_a_document_wide_blacklist(self):
        """**黒名簿は 1 語だけ・的はラベルだけ。**
        顧客の問いの字と、人間が書いた 80 文字の文には「普段」が**正しく**出る ―
        文書全体の黒名簿にすると**その 2 か所が壊れる**(司令塔が実物で確かめた)。"""
        self.assertEqual(EGR.LABEL_FORBIDDEN_WORDS, ("普段",))
        human = EI.unanswerable_past_games(25)
        self.assertIn("普段", human)
        # **その文はラベルの検査に通さない**(通すと人間の文が出せなくなる)。
        with self.assertRaises(EGR.ExitGroupsError):
            EGR.check_label_words(human)

    def test_l9_the_printed_row_heading_is_checked_too(self):
        """**守りの 2 本目: 群の表の行の見出し。**ラベルを別の道で入れた行が、
        **印字の手前で止まる**(`lines_of` の検査を外す変異がここで赤くなる)。"""
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        text = "\n".join(EGR.lines_of(rows, EC.CROSS_PHRASE_JP))
        self.assertNotIn("普段", text)
        for r in rows:
            self.assertIn(f"- {r['label']}: ", text)
        # **ラベルを差し替えた行は印字されない。**
        bad = [dict(rows[0], label="普段の型")]
        with self.assertRaises(EGR.ExitGroupsError):
            EGR.lines_of(bad, EC.CROSS_PHRASE_JP)

    def test_l10_an_unknown_group_key_falls(self):
        """**表に無い鍵は落ちる。**呼び方を人が決める前に顧客へ出さない。"""
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.label_of("newGroup", 25)
        self.assertIn("newGroup", str(cm.exception))

    def test_l11_a_missing_game_count_falls_instead_of_printing_a_default(self):
        """**局数が数でなければ落ちる**(既定値を入れない・「None 局」と印字しない)。"""
        for bad in (None, 0, -1, True, "25", 25.0):
            with self.assertRaises(EGR.ExitGroupsError, msg=repr(bad)):
                EGR.label_of("core", bad)

    def test_l12_the_group_rows_use_the_table_and_the_material_total(self):
        """**`group_rows` はラベルを自分で組まない**(写しを持てば表が 2 か所になる)。
        局数は**材料の合計**(`summary.games`)― 群ごとの局数ではない。"""
        games = BASE_GAMES
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(games))
        for r in rows:
            self.assertEqual(r["label"], EGR.label_of(r["key"], len(games)))
        # **群ごとの局数ではない**(core は 2 局だが、ラベルは 4 局)。
        core = next(r for r in rows if r["key"] == "core")
        self.assertEqual(core["games"], 2)
        self.assertIn("4 局", core["label"])
        self.assertNotIn("2 局", core["label"])

    def test_l13_a_material_without_a_total_falls(self):
        """**合計が無い材料は落ちる**(ラベルに既定値を入れて進まない)。"""
        p = patient(BASE_GAMES)
        del p["summary"]["games"]
        with self.assertRaises(EGR.ExitGroupsError) as cm:
            EGR.group_rows(recognition(BASE_CLASSES), p)
        self.assertIn("局数", str(cm.exception))

    def test_l14_the_packet_side_name_is_not_the_booklet_label(self):
        """**packet の内部の名(「群 A」)を冊子に写さない。**
        packet は封がしてあって直せない(ラベルを変えると `packetId` が変わる)ので、
        **翻訳はこちら側の仕事**である ― 写した変異がここで赤くなる。"""
        for key, template in EGR.GROUP_LABELS.items():
            self.assertNotIn("群 ", template, key)
        rows = EGR.group_rows(recognition(BASE_CLASSES), patient(BASE_GAMES))
        text = "\n".join(EGR.lines_of(rows, EC.CROSS_PHRASE_JP))
        for internal in ("群 A", "群 B", "群 C"):
            self.assertNotIn(internal, text, internal)

    def test_l15_the_table_lives_in_one_place(self):
        """**対応表はリポジトリで 1 か所。**`report-pdf` の道具(試験を除く)を見て、
        ラベルの型が**それぞれ 1 回だけ**在ることを確かめる ― 写しを置いたら落ちる。"""
        counts = {t: 0 for t in EGR.GROUP_LABELS.values()}
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py") or name.endswith("_test.py"):
                continue
            text = io.open(os.path.join(HERE, name), encoding="utf-8").read()
            for template in counts:
                counts[template] += text.count(template)
        for template, n in counts.items():
            self.assertEqual(n, 1, f"{template} が {n} か所")


if __name__ == "__main__":
    unittest.main()
