# -*- coding: utf-8 -*-
# `exit_candidates.py`(本編の md の下書き = 候補)の試験。
#
# 【この道具の危ない所】組版ではなく、**候補の段で越権すること**:
# 型に名前を付ける・目的を書く・承認済みの表の外から行動を作る・新しい統計を作る・
# 材料に無い言い方を使う。**そこは reportlab を回さずに測れる。**
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_structure as CS  # noqa: E402
import exit_candidates as EC  # noqa: E402
import exit_index as EI  # noqa: E402


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


SRC = read_text(os.path.join(HERE, "exit_candidates.py"))


def tag_words():
    """`render_direct.py` の `TAG_JP`・`SIDE_JP` を **AST で引く**(写さない)。

    `render_direct.py` は冒頭で `sys.argv` を読んで走るので import できない。
    **語の正本はあちら**なので、あちらのコードから引いて突き合わせる。
    """
    tree = ast.parse(read_text(os.path.join(HERE, "render_direct.py")))
    words = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "TAG_JP" for t in node.targets):
            for el in node.value.elts:
                words[el.elts[0].value] = el.elts[1].value
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SIDE_JP" for t in node.targets):
            for k, v in zip(node.value.keys, node.value.values):
                words[k.value] = v.value
    return words


def emitted_md():
    """**道具が実際に出す md**(合成の材料で 1 本組む)。

    **検査は「道具が出す文」に当てる。**ソース全文に `assertNotIn` を当てると、
    **自分の説明文(「『時間切れ』とは書かない」等)を捕まえる** ―
    2026-09-29 にこの型を 4 本続けて踏んだ(同じ日の 3 度目の同型)。
    """
    answers = [answer(1, 10, top1=("drop", "capture"), actual=("capture",)),
               answer(2, 20, top1=("sacrifice",), actual=("drop",), side="defense")]
    direct = direct_of(answers)
    repro = EC.repro_rows(direct)
    patient = {"games": [{"no": 1, "id": "g01", "side": "先手", "total": 99, "result": "勝ち"},
                         {"no": 2, "id": "g02", "side": "後手", "total": 88, "result": "負け"}],
               "findings": [{"kind": "phase", "oneLine": "崩れは中盤に多かった", "shown": True}]}
    mapping = [{"no": 1, "source": "g01-sente.kif", "side": "先手", "total": 99, "result": "勝ち"},
               {"no": 2, "source": "g02-gote.kif", "side": "後手", "total": 88, "result": "負け"}]
    denoms = EC.denominators(direct, patient, repro)
    return EC.build_md(direct, patient, repro, [], [], mapping, denoms, None)


# ---- 合成の材料(実物は使わない ― ① の制約。実物での確認は門にできない) ----
def answer(game_no, ply, top1=(), actual=(), side="attack", actual_side=None):
    """合成の 1 件。

    **`actual_side` を別に取れるようにしてある。**最初は `top1Side` と `actualSide` に同じ値を入れていて、
    そのため「側を `actualSide` から取る」変異が**どの試験でも赤にならなかった**(校正で実測 2026-09-29)。
    **合成材料が 2 つの欄を同じ値にすると、取り違えを区別できない。**
    """
    tags = ("drop", "capture", "retreat", "declinesPromotion", "sacrifice", "kingMove", "givesCheck")
    return {"gameNo": game_no, "displayPly": ply, "group": "3 分", "kifuId": f"g{game_no:02d}",
            "actualGapCp": 100 * ply, "top1Side": side,
            "actualSide": actual_side or ("defense" if side == "attack" else "attack"),
            "top1Tags": {t: t in top1 for t in tags},
            "actualTags": {t: t in actual for t in tags}}


def direct_of(answers):
    """`check_answer.direct_materials_of` が返す形の最小版(`counts` は数え上げて作る)。"""
    tag_keys = ("drop", "capture", "sacrifice", "givesCheck")
    return {
        "raw": [{"kind": "direct_answers", "answers": answers}],
        "totalCount": len(answers),
        "top1TagCounts": {k: sum(1 for a in answers if a["top1Tags"][k]) for k in tag_keys},
        "actualTagCounts": {k: sum(1 for a in answers if a["actualTags"][k]) for k in tag_keys},
        "top1SideCounts": {s: sum(1 for a in answers if a["top1Side"] == s)
                           for s in ("attack", "defense")},
    }


class ReproKindsTest(unittest.TestCase):
    def test_00_there_are_eight_kinds(self):
        """**8 種類。**仕様(36 行目の表)が「再現の 8 種類」と書いている数。"""
        self.assertEqual(len(EC.REPRO_KINDS), 8)

    def test_01_the_eight_are_the_ones_the_booklet_already_prints(self):
        """**8 つの組が `answer_facts.py` の `bullet_11` と同じであること。**

        `bullet_11` は既に顧客の冊子にこの 8 つの数を印字している。
        **候補の段で別の組にすると、同じ材料から違う 8 つが出る**(どちらが正か分からなくなる)。
        `bullet_11` の本文から `t1[…]`・`ac[…]`・`sd[…]` の鍵を AST で拾って突き合わせる
        (**文字列一致ではなく、あちらのコードが実際に引いている鍵**)。
        """
        tree = ast.parse(read_text(os.path.join(HERE, "answer_facts.py")))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "bullet_11")
        var_to_source = {"t1": "top1", "ac": "actual", "sd": "side"}
        found = set()
        for node in ast.walk(fn):
            if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                    and node.value.id in var_to_source
                    and isinstance(node.slice, ast.Constant)):
                found.add((var_to_source[node.value.id], node.slice.value))
        mine = {(source, key) for source, key, _phrase in EC.REPRO_KINDS}
        self.assertEqual(mine, found,
                         f"bullet_11 が引いている鍵と合わない(あちら {sorted(found)} / こちら {sorted(mine)})")

    def test_02_each_phrase_carries_the_word_the_booklet_uses(self):
        """**語の正本は `render_direct.py` の `TAG_JP`・`SIDE_JP`。**

        8 つの言い方が、**その鍵についてあちらが使っている語を含むこと**を見る。
        敷き詰め(許した語を引いて残りが空)は最初に書いたが、**「を」「手」を数え上げ忘れて赤になった** ―
        数え上げは漏れる(§40 の家族)。**含むことを見る**形に変えた。
        `capture` はあちらが「取る」、`sacrifice` は「捨て駒」なので、
        **語幹(「取」「捨」)で見る**(こちらは「駒を取る手」「駒を捨てる手」と書いている)。
        """
        words = tag_words()
        self.assertTrue(words, "render_direct.py から語を引けていない")
        for source, key, phrase in EC.REPRO_KINDS:
            want = words.get(key)
            self.assertIsNotNone(want, f"{key} の語が render_direct.py に無い")
            stem = want[0]
            self.assertIn(stem, phrase, f"{phrase} に {want} の語幹「{stem}」が無い")

    def test_03_a_recount_that_disagrees_with_counts_falls(self):
        """**数え直した局面が `counts` と合わなければ落ちる。**

        合わないのは材料の中で食い違っている状態で、**どちらを出しても嘘になる**。
        黙って片方を採ると、冊子の数と候補の数が違う。
        """
        answers = [answer(1, 10, top1=("drop",)), answer(1, 20, top1=("drop",))]
        d = direct_of(answers)
        d["top1TagCounts"]["drop"] = 1      # 材料の側が古い状態を作る
        with self.assertRaises(EC.ExitCandidatesError):
            EC.repro_rows(d)

    def test_04_games_are_counted_without_duplicates(self):
        """**局数は重複を除いて数える**(同じ局に 2 局面あっても 1 局)。"""
        answers = [answer(1, 10, top1=("drop",)), answer(1, 20, top1=("drop",)),
                   answer(2, 30, top1=("drop",))]
        got = EC.repro_rows(direct_of(answers))
        row = next(r for r in got["rows"] if "打つ" in r["phrase"] and "第 1 候補" in r["phrase"])
        self.assertEqual((row["positions"], row["games"]), (3, 2))
        self.assertEqual((got["totalPositions"], got["totalGames"]), (3, 2))

    def test_04b_the_side_row_follows_the_first_candidate(self):
        """**側は第 1 候補の側**(`top1Side`)。`actualSide` ではない。

        `bullet_11` が印字しているのは `top1SideCounts` なので、こちらが `actualSide` を数えると
        **同じ材料から違う 8 つが出る**。合成材料の 2 つの欄をわざと違う値にして測る。
        """
        answers = [answer(1, 10, side="attack"), answer(2, 20, side="attack")]
        self.assertEqual([a["actualSide"] for a in answers], ["defense", "defense"],
                         "合成材料の 2 つの欄が同じ値になっている(取り違えを区別できない)")
        got = EC.repro_rows(direct_of(answers))
        attack = next(r for r in got["rows"] if "攻め" in r["phrase"])
        defense = next(r for r in got["rows"] if "守り" in r["phrase"])
        self.assertEqual((attack["positions"], defense["positions"]), (2, 0))

    def test_05_empty_material_falls(self):
        with self.assertRaises(EC.ExitCandidatesError):
            EC.repro_rows(direct_of([]))


class NoOverreachTest(unittest.TestCase):
    def test_06_the_draft_never_says_time_ran_out(self):
        """**「時間切れ」と書かない**(2026-09-27 `5bb7ae9` で断定をやめた語)。
        時間の数が出るときは「持ち時間に到達した」の語(`exit_index.COUNTING_NOTES` の中にある)。
        **見るのは出した md** ― ソース全文だと「『時間切れ』とは書かない」という自分の説明文で赤になる。
        """
        self.assertNotIn("時間切れ", emitted_md())
        self.assertTrue(any("持ち時間に到達した" in s for s in EI.COUNTING_NOTES),
                        "固定文に「持ち時間に到達した」が無い(語の出どころが消えた)")

    def test_07_the_179_second_threshold_is_not_in_the_draft(self):
        """**179 秒は自動判定に入れない**(人間の決定)。出した md に数として出さない。"""
        self.assertNotIn("179", emitted_md())

    def test_08_no_sentence_claims_what_the_person_does_not_do(self):
        """**「この人は〜しない」の形を候補にも出さない**(司令塔の指示 1)。

        型に名前を付ける語・癖を断定する語を、**出した md に出さない**。
        """
        md = emitted_md()
        for banned in ("この人は", "癖", "傾向", "苦手", "得意", "しがち", "しない人"):
            self.assertNotIn(banned, md, f"断定の語が下書きに出ている: {banned}")

    def test_08b_the_scope_sentence_appears_exactly_once(self):
        """商品の範囲の 1 段落は**ちょうど 1 か所**(正本 §1)。"""
        self.assertEqual(emitted_md().count(CS.SCOPE_SENTENCE), 1)

    def test_08c_every_place_to_choose_is_marked(self):
        """**選ぶ場所は 3 か所**(数・盤・行動)。印が減ったら書き手が気づけない。"""
        self.assertEqual(emitted_md().count(EC.TODO), 3)

    def test_09_the_menu_judgment_is_not_reimplemented(self):
        """**minN の判定は `check_answer.py` の関数をそのまま呼ぶ。**

        別に作れば「候補には出るのに門が落とす」「門は通るのに候補に出ない」道ができる。
        """
        self.assertIn("CA.MENU_HOLDS", SRC)
        self.assertIn("CA.MENU_DENOMINATOR", SRC)
        self.assertIn("CA.menu_verify_gate_holds", SRC)
        for copied in ("def menu_holds", "def menu_denominator", "MENU_HOLDS = ", "MENU_DENOMINATOR = "):
            self.assertNotIn(copied, SRC, f"検査 4・5 の {copied} を写している")

    def test_10_the_fixed_sentences_are_not_copied(self):
        """数え方の固定文・商品の範囲の 1 段落・節の見出しを**写していないこと**。"""
        self.assertIn("EI.COUNTING_NOTES", SRC)
        self.assertIn("CS.SCOPE_SENTENCE", SRC)
        self.assertIn("CS.SECTIONS", SRC)
        # 固定文の 1 つ目の頭 10 文字が道具に直接書かれていないこと
        self.assertNotIn(EI.COUNTING_NOTES[0][:10], SRC, "数え方の固定文を写している")
        self.assertNotIn(CS.SCOPE_SENTENCE[:10], SRC, "商品の範囲の段落を写している")

    def test_11_the_heading_judgment_holds_no_string_of_its_own(self):
        """見出しを作る関数が、見出しの値を自分の文字列として持たないこと。"""
        tree = ast.parse(SRC)
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "heading_of")
        body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                               and isinstance(fn.body[0].value, ast.Constant)) else fn.body
        strings = [n.value for b in body for n in ast.walk(b)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        for role, head, contains in CS.SECTIONS:
            self.assertNotIn(head, strings, f"{role} の見出しの頭を写している")


class InstructionTest(unittest.TestCase):
    def test_12_instructions_to_the_writer_are_comments(self):
        """**書き手への指示は注釈にする。**顧客の PDF に出てはいけない文だから。"""
        made = EC.note("ここに残すのは 2 行だけ")
        self.assertTrue(made.startswith("<!--") and made.endswith("-->"), made)

    def test_13_the_todo_marker_is_the_one_the_spec_names(self):
        """選ぶ場所の印は仕様の `<!-- TODO: 選ぶ -->` そのまま(新しい印を作らない)。"""
        self.assertEqual(EC.TODO, "<!-- TODO: 選ぶ -->")


class MappingTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.dir = tempfile.mkdtemp(prefix="kifu-")
        self.patient = {"games": [{"no": 1, "id": "g01", "side": "先手", "total": 99,
                                   "result": "勝ち"}]}

    def write_fixed(self, name, payload):
        import json

        with io.open(os.path.join(self.dir, name), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    def test_14_the_file_name_comes_from_the_fixed_kifu(self):
        self.write_fixed("g01.fixed.json", {"id": "g01", "source": "g01-sente.kif"})
        rows = EC.mapping_rows(self.patient, self.dir)
        self.assertEqual(rows, [{"no": 1, "source": "g01-sente.kif", "side": "先手",
                                 "total": 99, "result": "勝ち"}])

    def test_15_a_missing_fixed_kifu_falls(self):
        """**黙って空欄にしない。**対応表は顧客が自分の棋譜を突き合わせる唯一の列。"""
        with self.assertRaises(EC.ExitCandidatesError):
            EC.mapping_rows(self.patient, self.dir)

    def test_16_a_fixed_kifu_without_source_falls(self):
        self.write_fixed("g01.fixed.json", {"id": "g01"})
        with self.assertRaises(EC.ExitCandidatesError):
            EC.mapping_rows(self.patient, self.dir)


class DenominatorTest(unittest.TestCase):
    def test_17_the_denominators_carry_where_they_came_from(self):
        """**分母の出どころは JSON の側に持つ**(文字列に埋めない ― 仕様 §3 の 1)。"""
        answers = [answer(1, 10, top1=("drop",)), answer(2, 20)]
        repro = EC.repro_rows(direct_of(answers))
        patient = {"games": [{"no": i} for i in range(1, 6)]}
        rows = EC.denominators(direct_of(answers), patient, repro)
        self.assertTrue(rows)
        for r in rows:
            self.assertIn("number", r)
            self.assertIn("unit", r)
            self.assertTrue(r["from"], "分母の出どころが空")
        self.assertIn(5, [r["number"] for r in rows], "全部の局数が分母に入っていない")


if __name__ == "__main__":
    unittest.main(verbosity=2)
