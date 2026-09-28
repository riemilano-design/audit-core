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

import check_answer as CA  # noqa: E402
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
    patient = {"summary": {"games": 2},
               "games": [{"no": 1, "id": "g01", "side": "先手", "total": 99, "result": "勝ち"},
                         {"no": 2, "id": "g02", "side": "後手", "total": 88, "result": "負け"}],
               # `text` は**埋まった文**(数が入っている側)。2026-09-29 に候補の段が印字するようになった ―
               # `oneLine` には数が無く、**書き手が選ぶ 3 つの数が下書きに出ていなかった**。
               "findings": [{"kind": "phase", "oneLine": "崩れは中盤に多かった",
                             "text": "崩れ 79 回のうち、序盤 7・中盤 41・終盤 31 でした",
                             "shown": True}]}
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
        # **実物には必ず在る鍵**(検査 1 が「浅い読みで見えた分かれ道 / 分かれ道」の組に使う)。
        # 2026-09-29 に足した ― 合成材料に無かったので、`registered_pairs_of` を呼ぶ試験が
        # `KeyError` で落ちた。**合成は実物の形に合わせる。**
        "totalForkCount": len(answers) * 4,
        "top1TagCounts": {k: sum(1 for a in answers if a["top1Tags"][k]) for k in tag_keys},
        "actualTagCounts": {k: sum(1 for a in answers if a["actualTags"][k]) for k in tag_keys},
        "top1SideCounts": {s: sum(1 for a in answers if a["top1Side"] == s)
                           for s in ("attack", "defense")},
        # **実物には必ず在る鍵**(検査 1 の (v) 組ごとの数 / 総数)。2026-09-29 に足した。
        "groupCounts": {a.get("group", "3 分"): sum(1 for b in answers
                                                    if b.get("group", "3 分") == a.get("group", "3 分"))
                        for a in answers},
    }


class DraftOffersWhatTheWriterMustPickTest(unittest.TestCase):
    """**選ぶ相手が下書きに印字されていること。**印字されていなければ、書き手は材料を開くしかない。"""

    def test_00a_the_filled_sentence_with_the_numbers_is_printed(self):
        """**発見の「埋まった文」(数が入っている側)が出ていること。**

        `oneLine` には数が無い。**`text` を印字するまで、選ぶ 3 つの数が下書きに出ていなかった**
        (2026-09-29 に門を繋いで見つけた穴。校正でも黙っていたのでここで測る)。
        """
        md = emitted_md()
        self.assertIn("崩れ 79 回のうち、序盤 7・中盤 41・終盤 31 でした", md)

    def test_00b_every_verify_row_carries_exactly_one_menu_mark(self):
        """**答え合わせの表の行に、行動の印がちょうど 1 つ。**

        器の門の項目 6 がこれを求める。印が無いと**工程の最後(`exit-check`)で行数ぶん落ちる**
        (実測 2026-09-29: 5 行ぶん + 集合が合わない 1 件)。
        """
        passed = [{"id": "M3", "minN": 5, "denominator": 20,
                   "item": {"actionCore": "やってみる", "evidenceName": "根拠", "verifyName": "答え合わせ"}},
                  {"id": "M4", "minN": 5, "denominator": 20,
                   "item": {"actionCore": "やってみる", "evidenceName": "根拠", "verifyName": "答え合わせ"}}]
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, passed, [], [], EC.denominators(direct, patient, repro), None)
        head, contains = next((h, c) for r, h, c in CS.SECTIONS if r == CS.VERIFY_ROLE)
        rows = []
        inside = False
        for line in md.split("\n"):
            if line.startswith("## "):
                inside = line.startswith(f"## {head}")
                continue
            if inside and line.startswith("| ") and not line.startswith("|---"):
                rows.append(line)
        # 見出しの行を除いた本文行(2 件)。**見出しは道具の定数から引く**(写しを持たない)。
        body_rows = [r for r in rows if r != EC.VERIFY_TABLE_HEADER]
        self.assertEqual(len(body_rows), 2, rows)
        for row in body_rows:
            self.assertEqual(len(CA.MENU_TAG_RE.findall(row)), 1, row)


class DoesNotOverwriteTheWriterTest(unittest.TestCase):
    """**既に在る本編の md を上書きしない**(2026-09-29。実際に書き手の 92 行を消した)。

    経緯: 候補の JSON だけを作り直したくて JSON を消して段を回したら、段の「済みの判定」が
    `md と JSON の両方が在る` だったため段が走り、**書き手が書いた md が素の下書きに戻った。**
    git の追跡外なので戻せなかった。**番人は道具の側に置く** ―
    段の判定を直すだけでは、手で呼んだときに消せる。
    """

    def test_00c_an_existing_md_is_refused(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            md = os.path.join(d, "honbun.md")
            with io.open(md, "w", encoding="utf-8") as f:
                f.write("書き手が書いた本文")
            own = {"out_md": md, "out_json": os.path.join(d, "c.json"), "kifu_dir": d}
            with self.assertRaises(EC.ExitCandidatesError) as e:
                EC.build(own, [])
            self.assertIn("既にある", str(e.exception))
            # **中身が残っていること**(落ちる前に開いていない)。
            with io.open(md, encoding="utf-8") as f:
                self.assertEqual(f.read(), "書き手が書いた本文")


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
        # 合成の材料は 2 局(`emitted_md` の patient)。**局数で作った文**がちょうど 1 か所(D1)。
        self.assertEqual(emitted_md().count(CS.scope_sentence(2)), 1)
        # 別の局数の文は出ない(20 が直書きだった頃はこちらが 1 か所だった)。
        self.assertEqual(emitted_md().count(CS.scope_sentence(20)), 0)

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
        self.assertIn("CS.scope_sentence", SRC)
        self.assertIn("CS.SECTIONS", SRC)
        # 固定文の 1 つ目の頭 10 文字が道具に直接書かれていないこと
        self.assertNotIn(EI.COUNTING_NOTES[0][:10], SRC, "数え方の固定文を写している")
        self.assertNotIn(CS.SCOPE_SENTENCE_TEMPLATE[:10], SRC, "商品の範囲の段落を写している")

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
        patient = {"summary": {"games": 5}, "games": [{"no": i} for i in range(1, 6)]}
        rows = EC.denominators(direct_of(answers), patient, repro)
        self.assertTrue(rows)
        for r in rows:
            self.assertIn("number", r)
            self.assertIn("unit", r)
            self.assertTrue(r["from"], "分母の出どころが空")
        self.assertIn(5, [r["number"] for r in rows], "全部の局数が分母に入っていない")


class RestCountTest(unittest.TestCase):
    """「そのほかの N 局」の引き算。**3 か所で同じ引き算をしていた所を 1 本にした**(2026-09-29)。

    2026-09-29 の独立監査が実測した穴 ― **`exit_candidates` 側の引き算だけを変えても、
    この試験ファイルは 1 本も落ちなかった**(`exit_cover` 側は `test_03b` が守っていた)。
    `_mid.py` の `assert` は**自分が作った一覧と自分の引き算**を比べるだけで、
    別プロセスの 2 つが同じ形で引いていることは確かめられない。
    """

    def test_18_the_number_in_the_md_is_the_subtraction(self):
        # 材料は 2 局・1 局ずつ見た局は 0 → 「そのほかの 2 局」
        self.assertIn("そのほかの 2 局", emitted_md())

    def test_18b_the_number_moves_with_the_featured_count(self):
        answers = [answer(1, 10, top1=("drop",), actual=("capture",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 7}, "games": [], "findings": []}
        denoms = EC.denominators(direct, patient, repro)
        md = EC.build_md(direct, patient, repro, [], [], [], denoms, None, featured=2)
        self.assertIn("そのほかの 5 局", md)
        self.assertNotIn("そのほかの 7 局", md)

    def test_18c_the_subtraction_lives_in_one_place(self):
        """**引き算を持つのは `exit_index.rest_count` だけ。**3 つの書く側は全部そこを呼ぶ。

        写しが戻ったら落ちる ― **これが監査が見つけた穴の再発の歯止め**。
        """
        self.assertEqual(EI.rest_count(25, 6), 19)
        self.assertEqual(EI.rest_count("25", "6"), 19)  # 材料が文字でも数で引く
        for name in ("exit_candidates.py", "exit_cover.py", "_mid.py"):
            src = read_text(os.path.join(HERE, name))
            self.assertIn("rest_count(", src, name + " が共通の引き算を呼んでいない")
        # **`summary.games` から直に引く形が戻っていないか**(3 つのファイルすべて)
        for name in ("exit_candidates.py", "exit_cover.py"):
            src = read_text(os.path.join(HERE, name))
            self.assertNotIn('int(patient["summary"]["games"]) - ', src,
                             name + " に引き算の写しが戻っている")
        mid = read_text(os.path.join(HERE, "_mid.py"))
        # **引用符の形を両方見る**(2026-09-29 の監査が挙げた宿題 ― 二重引用符だけを探していたので、
        # `assert` のエラーの文に残っていた単一引用符の写しが網に入っていなかった)。
        self.assertNotIn('s["games"] - len(PROSE)', mid)
        self.assertNotIn("s['games'] - len(PROSE)", mid)
def passed_row(item_id="M4", fractions=None, action="攻めと自玉側を 1 つずつ比べる",
               verify_name="側の一致率", denominator=404, min_n=30):
    return {"id": item_id, "minN": min_n, "denominator": denominator, "fractions": fractions,
            "item": {"actionCore": action, "evidenceName": "側の分数", "verifyName": verify_name}}


TWO = [{"label": "攻め", "name": "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面",
        "numerator": 65, "denominator": 107},
       {"label": "自玉側", "name": "第 1 候補が自玉側の手だった分かれ道のうち、実戦も自玉側の手だった局面",
        "numerator": 76, "denominator": 132}]
ONE = [{"label": "", "name": "第 1 候補が駒を捨てる手だった分かれ道のうち、実戦も駒を捨てる手だった局面",
        "numerator": 50, "denominator": 137}]


class VerifyTableTest(unittest.TestCase):
    """**答え合わせの表は 3 列で、いまの値に分子 / 分母の両方が入る**(2026-09-29。P-152)。"""

    def test_19_the_value_cell_carries_both_numbers(self):
        self.assertEqual(EC.values_cell(passed_row(fractions=TWO)), "攻め 65 / 107、自玉側 76 / 132")
        self.assertEqual(EC.values_cell(passed_row("M6", ONE)), "50 / 137")

    def test_19b_the_denominator_of_the_gate_is_not_printed(self):
        """**`404` は出ない。**判定が割っていない数だから(いまの値の列に置いていた)。"""
        self.assertNotIn("404", EC.values_cell(passed_row(fractions=TWO)))
        self.assertNotIn("404", EC.facts_cell(passed_row(fractions=TWO)))
        self.assertNotIn("30", EC.evidence_phrase(passed_row(fractions=TWO)))

    def test_19c_the_fact_cell_is_the_spelled_out_fraction(self):
        cell = EC.facts_cell(passed_row(fractions=TWO))
        self.assertIn("第 1 候補が攻めの手だった分かれ道のうち", cell)
        self.assertIn("自玉側", cell)
        self.assertNotIn("側の一致率", cell)

    def test_19d_an_item_without_a_fraction_falls_back_to_the_approved_words(self):
        """**承認済みの表の文には触らない。**分数を持たない項目は `verifyName` のまま。"""
        row = passed_row("M9", None, verify_name="持ち時間に到達した局のうち中央値超え / 持ち時間に到達した局",
                         denominator=5, min_n=2)
        self.assertEqual(EC.facts_cell(row), row["item"]["verifyName"])
        self.assertEqual(EC.values_cell(row), "5")
        self.assertIn("側の分数", EC.evidence_phrase(row))

    def test_19e_the_reason_line_carries_the_same_numbers_as_the_table(self):
        """**根拠の 1 行と表が同じ数を出す**(写しを 2 か所に持たない)。"""
        row = passed_row(fractions=TWO)
        phrase = EC.evidence_phrase(row)
        for f in TWO:
            self.assertIn(f"{f['numerator']} / {f['denominator']}", phrase)
            self.assertIn(f"{f['numerator']} / {f['denominator']}", EC.values_cell(row))

    def test_19f_the_table_has_three_columns_and_no_id_column(self):
        passed = [passed_row(fractions=TWO), passed_row("M6", ONE, action="捨てる手を候補に入れる")]
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, passed, [], [],
                         EC.denominators(direct, patient, repro), None)
        self.assertIn(EC.VERIFY_TABLE_HEADER, md)
        self.assertEqual(EC.VERIFY_TABLE_HEADER.count("|"), 4)  # 3 列
        rows = [l for l in md.split("\n") if l.startswith("| ") and "<!-- menu:" in l]
        for r in rows:
            # **1 列目は行動の文。**`M4` のような道具の中の名前が 1 列目に来ない。
            first = r.split("|")[1]
            self.assertNotIn("M4", first.replace("<!-- menu: M4 -->", ""))
            self.assertNotIn("M6", first.replace("<!-- menu: M6 -->", ""))


class NoActionTest(unittest.TestCase):
    def test_20_zero_actions_prints_the_fixed_sentence(self):
        """**差が無ければ行動にしない。**0 本なら固定文が出る(2026-09-29 の司令塔の判断)。"""
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, [], [], [],
                         EC.denominators(direct, patient, repro), None)
        self.assertIn(EI.NO_ACTION_SENTENCE, md)

    def test_20b_the_sentence_is_not_printed_when_there_are_actions(self):
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, [passed_row(fractions=TWO)], [], [],
                         EC.denominators(direct, patient, repro), None)
        self.assertNotIn(EI.NO_ACTION_SENTENCE, md)
class NegativeTypeTest(unittest.TestCase):
    """**否定の型は本編の行動に入れない**(2026-09-29。`verifyName` が空で分数も無い項目)。"""

    def test_21_the_predicate(self):
        self.assertTrue(EC.is_negative_type({"verifyName": ""}, None))
        self.assertTrue(EC.is_negative_type({"verifyName": ""}, []))
        self.assertFalse(EC.is_negative_type({"verifyName": "側の一致率"}, None))
        self.assertFalse(EC.is_negative_type({"verifyName": ""}, ONE))

    def test_21b_menu_rows_drops_it_with_the_reason(self):
        """**段の中で落ちること**を測る(述語だけでは、呼ばれているかが分からない)。"""
        class G(object):
            pass
        g = G()
        g.time_up_losses = {"n": 3, "m": 3}
        materials = {"groups": {"min3": g}, "sideMatch": None, "readCombined": None}
        items = {"M8": {"actionCore": "やってみる", "evidenceName": "根拠",
                        "verifyName": "", "verifyGate": None}}
        ctx = {"menuItemsById": items, "menuMinN": {"M8": 2}, "materials": materials}
        passed, dropped = EC.menu_rows(ctx)
        self.assertEqual(passed, [])
        self.assertEqual([r["id"] for r in dropped], ["M8"])
        self.assertEqual(dropped[0]["why"], EC.NEGATIVE_TYPE_REASON)
        # **判定・下限・門はどれも通っている**(落ちた理由が否定の型であることの裏)
        self.assertTrue(CA.MENU_HOLDS["M8"](materials))
        self.assertGreaterEqual(CA.MENU_DENOMINATOR["M8"](materials), 2)

    def test_21c_an_item_with_a_verify_name_still_passes(self):
        class G(object):
            pass
        g = G()
        g.time_up_losses = {"n": 3, "m": 3}
        materials = {"groups": {"min3": g}, "sideMatch": None, "readCombined": None}
        items = {"M8": {"actionCore": "やってみる", "evidenceName": "根拠",
                        "verifyName": "時間切れの局数", "verifyGate": None}}
        ctx = {"menuItemsById": items, "menuMinN": {"M8": 2}, "materials": materials}
        passed, dropped = EC.menu_rows(ctx)
        self.assertEqual([r["id"] for r in passed], ["M8"])
        self.assertEqual(dropped, [])
class CrossObservationTest(unittest.TestCase):
    """**観測 1 行(第 1 候補の印 × 実戦の印)。行動ではない。**

    人間が 2026-09-28 に引いた線そのもの。**分母は `direct` から数える** ―
    `read` の `tagCrossTable` から数えると p1 の数と分母が違う(実測: 捨てる手は 41 対 137)。
    """

    def test_22_the_line_carries_both_sides_with_positions_and_games(self):
        answers = [answer(1, 10, top1=("drop",), actual=("drop",)),
                   answer(1, 20, top1=("drop",), actual=("capture",)),
                   answer(2, 30, top1=("drop",), actual=("capture",)),
                   answer(2, 40, top1=("capture",), actual=("drop",))]
        direct = direct_of(answers)
        line = EC.cross_line(direct, "drop")
        # 第 1 候補が打つ手: 3 局面 / 2 局。実戦も打つ手: 1 局面 / 1 局。そうでない: 2 局面 / 2 局。
        self.assertIn("3 局面(2 局)", line)
        self.assertIn("実戦も駒を打つ手だった局面 1(1 局)", line)
        self.assertIn("実戦は駒を打つ手ではなかった局面 2(2 局)", line)

    def test_22b_the_line_says_it_is_not_an_action(self):
        """**行動と混ぜない。**承認済みの表に「打つ」の項目が無いので、行動にすれば表の外から作ることになる。"""
        md = emitted_md()
        cross = [l for l in md.split("\n") if "観測(行動ではありません)" in l]
        self.assertEqual(len(cross), len(CA.CROSS_TAGS), md)

    def test_22c_only_the_drop_tag_is_printed(self):
        """**`sacrifice` は出さない** ― `M6` の答え合わせの分数と分母が違うので並べられない。"""
        self.assertEqual(CA.CROSS_TAGS, ("drop",))
        md = emitted_md()
        self.assertNotIn("第 1 候補が駒を捨てる手だった分かれ道", md)

    def test_22d_the_banned_words_are_not_used(self):
        """**「打たない」「見落とし」「候補に入れない」は使わない**(規則 8 (3)・人間の線)。"""
        answers = [answer(1, 10, top1=("drop",), actual=("capture",))]
        line = EC.cross_line(direct_of(answers), "drop")
        for banned in ("打たない", "見落と", "候補に入れ"):
            self.assertNotIn(banned, line)

    def test_22e_the_words_come_from_the_tag_table(self):
        """**語は `render_direct.py` の `TAG_JP` から**(写していないことを AST で突き合わせる)。"""
        words = tag_words()
        self.assertIn(words["drop"], EC.CROSS_PHRASE_JP["drop"])
        # **出す印と語の集合が一致する**(語だけ残る・印だけ増えるを止める)
        self.assertEqual(set(EC.CROSS_PHRASE_JP), set(CA.CROSS_TAGS))

    def test_22f_check_1_allows_the_printed_pairs(self):
        """**印字する組が検査 1 の登録済みの組に在る**(無いと門が冊子を落とす)。"""
        # **偶然一致を避ける材料。**2026-09-29 に変異で見つけた ― 最初の材料では
        # 「第 1 候補が打つ手」の数が総数と同じで、**実戦の印ごとの組(既に登録済み)が
        # 同じ組を作っていた**ので、新しい登録を外しても試験が黙った。
        # **総数 5・第 1 候補が打つ手 3 局面(2 局)**にして、組が重ならないようにする。
        answers = [answer(1, 10, top1=("drop",), actual=("drop",)),
                   answer(1, 20, top1=("drop",), actual=("capture",)),
                   answer(2, 30, top1=("drop",), actual=("capture",)),
                   answer(2, 40, top1=("capture",), actual=("drop",)),
                   answer(3, 50, top1=("capture",), actual=("drop",))]
        direct = direct_of(answers)
        c = CA.top1_actual_cross(direct, "drop")
        self.assertEqual((c["positions"], c["games"]), (3, 2))
        self.assertNotEqual(c["positions"], direct["totalCount"])
        pairs = CA.registered_pairs_of([], {"direct": direct, "groups": {}, "readCombined": None,
                                            "sideMatch": None, "timeCause": None, "timeSearch": None,
                                            "patientGroups": []})
        for num in ("bothPositions", "otherPositions"):
            self.assertIn((c[num], c["positions"]), pairs, num)
        for num in ("bothGames", "otherGames"):
            self.assertIn((c[num], c["games"]), pairs, num)
class ObservationNumbersAreCandidatesTest(unittest.TestCase):
    """**印字する側と数える側は同じ集合。**観測 1 行の数が `p1Numbers` に在ること(2026-09-29)。

    通して見つけた ― 観測を下書きに印字しているのに候補に無かったので、
    **書き手が観測を p1 に使うと門が「数 32 が候補に無い」と言って止めた**(実物で出た)。
    P-139(門が 1 桁を数え、候補が数えなかった)と**同じ型の 2 度目**。
    """

    @staticmethod
    def fixture():
        answers = [answer(1, 10, top1=("drop",), actual=("drop",)),
                   answer(1, 20, top1=("drop",), actual=("capture",)),
                   answer(2, 30, top1=("drop",), actual=("capture",)),
                   answer(2, 40, top1=("capture",), actual=("drop",)),
                   answer(3, 50, top1=("capture",), actual=("drop",))]
        direct = direct_of(answers)
        return direct, EC.repro_rows(direct), {
            "summary": {"games": 3}, "games": [{"no": 1}, {"no": 2}, {"no": 3}],
            "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}

    def test_23_all_six_numbers_of_the_observation_are_candidates(self):
        direct, repro, patient = self.fixture()
        got = {int(x["number"]) for x in EC.p1_numbers(patient, repro, direct)}
        c = CA.top1_actual_cross(direct, "drop")
        for key in ("positions", "games", "bothPositions", "bothGames", "otherPositions", "otherGames"):
            self.assertIn(c[key], got, key)

    def test_23b_every_number_the_line_prints_is_a_candidate(self):
        """**出す文から数を拾って突き合わせる**(欄の名前ではなく、印字された数で測る)。"""
        direct, repro, patient = self.fixture()
        got = {int(x["number"]) for x in EC.p1_numbers(patient, repro, direct)}
        line = EC.cross_line(direct, "drop")
        _ratio, fractions, percents, plains = CA.scan_numbers(line, small_max=0)
        printed = [n for a, b, _s in fractions for n in (a, b)] + list(percents) + list(plains)
        self.assertTrue(printed)
        for n in printed:
            self.assertIn(n, got, f"{n} が候補に無い(門が止める): {line}")

    def test_23c_the_candidates_carry_where_the_number_came_from(self):
        direct, repro, patient = self.fixture()
        rows = [x for x in EC.p1_numbers(patient, repro, direct) if "観測" in x["from"]]
        self.assertEqual(len(rows), 6)
        for r in rows:
            self.assertIn("direct_answers.json", r["from"])

    def test_23e_the_json_the_gate_reads_carries_them(self):
        """**門が読む JSON まで届いていること。**関数を直接呼ぶ試験だけでは、
        `build()` の中で `direct` を渡し忘れても黙る(2026-09-29 に変異で実測)。"""
        direct, repro, patient = self.fixture()
        payload = EC.candidates_json(direct, patient, repro, [], [], [])
        got = {int(x["number"]) for x in payload["p1Numbers"]}
        c = CA.top1_actual_cross(direct, "drop")
        for key in ("positions", "games", "bothPositions", "bothGames", "otherPositions", "otherGames"):
            self.assertIn(c[key], got, key)

    def test_23f_the_json_is_built_by_the_function(self):
        """**`build()` は自分で辞書を組まない**(組むと測れない所に戻る)。"""
        src = read_text(os.path.join(HERE, "exit_candidates.py"))
        self.assertIn("json.dump(candidates_json(", src)
        self.assertEqual(src.count('"p1Numbers"'), 1)

    def test_23d_without_the_material_the_list_is_unchanged(self):
        """`direct` を渡さなければ**前と同じ**(既存の呼び出しを壊していない)。"""
        direct, repro, patient = self.fixture()
        without = EC.p1_numbers(patient, repro)
        with_direct = EC.p1_numbers(patient, repro, direct)
        self.assertEqual(without, with_direct[:len(without)])
        self.assertEqual(len(with_direct) - len(without), 6)
if __name__ == "__main__":
    unittest.main(verbosity=2)
