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


# 冒頭の段落に入る日付(P-162)。**試験の中で 1 か所**にする。
TODAY = "2026-09-29"


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
    return EC.build_md(direct, patient, repro, [], [], mapping, denoms, None,
                       EC.opening_lines(patient, direct, TODAY))


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
        md = EC.build_md(direct, patient, repro, passed, [], [], EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
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
        # 冒頭の段落は `CS.opening_paragraph` から作る(2026-09-29。P-162 で 1 文 → 4 文になった)。
        self.assertIn("CS.opening_paragraph", SRC)
        self.assertIn("CS.SECTIONS", SRC)
        # 固定文の 1 つ目の頭 10 文字が道具に直接書かれていないこと
        self.assertNotIn(EI.COUNTING_NOTES[0][:10], SRC, "数え方の固定文を写している")
        self.assertNotIn(CS.SCOPE_SENTENCE_TEMPLATE[:10], SRC, "商品の範囲の段落を写している")
        # **冒頭の断り書きも写さない**(P-162)。ここに写しが入ると、
        # **器の門が数える文と、道具が印字する文が別々に直る**道ができる。
        for sentence in (CS.OPENING_NOT_A_JUDGE, CS.OPENING_APPENDIX, CS.OPENING_ENGINE_TEMPLATE):
            self.assertNotIn(sentence[:10], SRC, f"冒頭の固定文を写している: {sentence[:10]}")

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
        md = EC.build_md(direct, patient, repro, [], [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY), featured=2)
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


TWO = [{"label": "攻め", "unit": "局面",
        "name": "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面",
        "numerator": 65, "denominator": 107},
       {"label": "自玉側", "unit": "局面",
        "name": "第 1 候補が自玉側の手だった分かれ道のうち、実戦も自玉側の手だった局面",
        "numerator": 76, "denominator": 132}]
ONE = [{"label": "", "unit": "局面",
        "name": "第 1 候補が駒を捨てる手だった分かれ道のうち、実戦も駒を捨てる手だった局面",
        "numerator": 50, "denominator": 137}]
# **単位が違う分数**(P-165。実物の M6 がこれ ― 分子は局面・分母は印の組)。
MISMATCH = [dict(ONE[0], unit="印の組",
                 unitMismatch="分子は局面の数・分母は印の組の数(P-165。人間の承認待ち)")]


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
                         EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
        self.assertIn(EC.VERIFY_TABLE_HEADER, md)
        self.assertEqual(EC.VERIFY_TABLE_HEADER.count("|"), 4)  # 3 列
        rows = [l for l in md.split("\n") if l.startswith("| ") and "<!-- menu:" in l]
        for r in rows:
            # **1 列目は行動の文。**`M4` のような道具の中の名前が 1 列目に来ない。
            first = r.split("|")[1]
            self.assertNotIn("M4", first.replace("<!-- menu: M4 -->", ""))
            self.assertNotIn("M6", first.replace("<!-- menu: M6 -->", ""))


class FixedSentenceCandidatesTest(unittest.TestCase):
    """**使ってよい固定文が下書きに出ている**(2026-09-29。項目 2)。

    候補に無い文を書き手が使えば門が止める ― **印字していないものは選べない。**
    """

    def test_25_the_selection_sentence_is_offered_with_the_game_count(self):
        """「なぜこの N つだけなのか」の 1 文が、**この冊子の局数**で出ている。"""
        md = emitted_md()
        self.assertIn(EI.selection_sentence(2), md)
        # 別の局数の文は出ない(直書きしていないこと)。
        self.assertNotIn(EI.selection_sentence(25), md)

    def test_25b_the_nothing_to_hide_sentence_is_offered(self):
        """「無いものは無いと書きます。」が出ている(4 人目の実物の型の尾)。"""
        self.assertIn(EI.NOTHING_TO_HIDE_SENTENCE, emitted_md())

    def test_25c_the_tool_does_not_write_the_subject(self):
        """**「〜という形は出ていません」の主語を道具が作らない。**

        4 人目のあの主語(「長く考えた手で崩れる」)は書き手が数から書いたもので、
        材料のどこにも文として無い。道具が埋めれば**私が将棋の言い方を決める**ことになる。
        """
        md = emitted_md()
        self.assertNotIn("という形はこの", md)
        self.assertNotIn("長く考えた手で崩れる", md)

    def test_25d_the_approved_negative_statements_are_offered(self):
        """**否定の型の文は承認済みの表からそのまま出す**(道具が言い換えない)。"""
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}], "findings": []}
        core = "序盤を急ぐ必要は数からは出ていない"
        dropped = [{"id": "M3", "minN": 10, "denominator": 20,
                    "why": EC.NEGATIVE_TYPE_REASON,
                    "item": {"actionCore": core, "evidenceName": "根拠", "verifyName": ""}}]
        md = EC.build_md(direct, patient, repro, [], dropped, [],
                         EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
        self.assertIn(f"- {core}", md)

    def test_25e_only_negative_types_are_offered_that_way(self):
        """**下限に届かなかっただけの項目は固定文の一覧に出さない。**

        出すと「条件が成り立たなかった行動」を否定の事実として書ける道ができる。
        """
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}], "findings": []}
        core = "これは条件が成り立たなかった行動"
        dropped = [{"id": "M9", "minN": 10, "denominator": 3,
                    "why": "根拠の数が下限 10 に届かない(いまの分母 3)",
                    "item": {"actionCore": core, "evidenceName": "根拠", "verifyName": "答え"}}]
        md = EC.build_md(direct, patient, repro, [], dropped, [],
                         EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
        # 落ちた一覧の表には出るが、固定文の一覧(`- ` の行)には出ない。
        self.assertIn(f"| M9 |", md)
        self.assertNotIn(f"- {core}", md)


class ActionFractionsInP1Test(unittest.TestCase):
    """**行動の根拠の分数が p1 の候補に出ている**(P-164。2026-09-29)。

    4 人目(18 局版)の p1 は 3 本のうち **2 本が行動の「根拠:」と同じ数・ほぼ同じ文**だった。
    5 人目(25 局版)は 0 本 ― 道具が `MENU_FRACTIONS` を **p3 の行動の下にしか出していなかった**ため、
    **書き手が p1 に根拠の数を選べなかった。**
    """

    def fixture(self, fractions):
        answers = [answer(1, 10, top1=("drop",), actual=("drop",)),
                   answer(2, 20, top1=("drop",), actual=("capture",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 2}, "games": [], "findings": []}
        repro = EC.repro_rows(direct)
        row = passed_row(fractions=fractions)
        denoms = EC.denominators(direct, patient, repro, [row])
        md = EC.build_md(direct, patient, repro, [row], [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY))
        return direct, patient, repro, row, md

    def test_27_the_fraction_lines_are_printed_in_the_draft(self):
        """**文と数の両方が p1 の候補に出る**(書き手が文ごと選べるように)。"""
        _direct, _patient, _repro, _row, md = self.fixture(TWO)
        for f in TWO:
            self.assertIn(f"{f['name']}が {f['numerator']} / {f['denominator']}。", md)
        self.assertIn("行動の根拠(行動 M4・攻め)", md)
        self.assertIn("行動の根拠(行動 M4・自玉側)", md)

    def test_27b_the_numbers_are_in_the_gate_allow_list(self):
        """**印字する側と数える側は同じ集合。**候補に無ければ門が書き手を止める(P-139 の 3 度目)。"""
        direct, patient, repro, row, _md = self.fixture(TWO)
        got = {int(x["number"]) for x in EC.p1_numbers(patient, repro, direct, [row])}
        for f in TWO:
            self.assertIn(f["numerator"], got, f)
            self.assertIn(f["denominator"], got, f)
        # 渡さなければ入らない(勝手に増えていないこと)。
        plain = {int(x["number"]) for x in EC.p1_numbers(patient, repro, direct)}
        self.assertNotIn(107, plain)
        self.assertNotIn(132, plain)

    def test_27c_the_json_the_gate_reads_carries_them(self):
        """**門が読む JSON まで届いていること**(関数だけでは `build()` の渡し忘れが黙る)。"""
        direct, patient, repro, row, _md = self.fixture(TWO)
        payload = EC.candidates_json(direct, patient, repro, [], [row], [],
                                     EC.opening_lines(patient, direct, TODAY))
        pairs = {(f["numerator"], f["denominator"]) for f in payload["actionFractions"]}
        self.assertEqual(pairs, {(65, 107), (76, 132)})
        got = {int(x["number"]) for x in payload["p1Numbers"]}
        self.assertTrue({65, 107, 76, 132} <= got, sorted(got))

    def test_27d_a_unit_mismatch_is_not_offered(self):
        """**単位が違う分数は p1 に出さない**(P-165)。出せば穴が 1 か所から 2 か所になる。"""
        direct, patient, repro, row, md = self.fixture(MISMATCH)
        self.assertEqual(EC.action_fractions([row]), [])
        # **p1 の候補の節にだけ出ない。**行動の「根拠:」と答え合わせの表には残る ―
        # あちらは判定が見た分数をそのまま出す場所で、**判定は動かさない**(P-165 は人間の承認待ち)。
        # 落とすのは書き手(司令塔の判断「3 周目は (ウ)」)で、下の門 (ix) がそれを機械で確かめる。
        p1 = md.split("## 局面で見る")[0]
        self.assertNotIn("行動の根拠(", p1)
        self.assertNotIn("50 / 137", p1)
        self.assertIn("50 / 137", md)  # p3 の根拠と表には在る
        # 門の一覧(p1 の許可)にも入らない。
        got = {int(x["number"]) for x in EC.p1_numbers(patient, repro, direct, [row])}
        self.assertNotIn(137, got)


class BoardFractionMarkTest(unittest.TestCase):
    """**盤の候補に「どの行動の根拠の分数に入るか」の印**(P-164 の項目 3。2026-09-29)。

    実物で測った ― `(kifuId, displayPly)` は 404 行 → 404 個の鍵で一意、盤の候補 103 が 103 とも当たり、
    **M4 の分母に入るのは 68・分子は 49・入らないのは 35**。
    `sfen` では結合しない(一意は 403 で、重複した 1 件は側が `defense` と `none` で食い違う)。
    """

    @staticmethod
    def side_match(top1="attack", actual="attack"):
        return {"attack": {"n": 107, "collapsed": 65},
                "defense": {"n": 132, "collapsed": 76},
                "forkTotal": 404,
                "rows": {("g01", 10): {"top1Side": top1, "actualSide": actual}}}

    def test_28_a_numerator_position_says_so(self):
        a = answer(1, 10, top1=("drop",))
        got = EC.board_fraction_note(self.side_match("attack", "attack"),
                                     [passed_row(fractions=TWO)], a)
        self.assertIn("行動 M4・攻め", got)
        self.assertIn("65 / 107", got)
        self.assertIn("分子にも入る", got)
        # **書き手への注の形**(残っていれば門 (vi) が落とす)。
        self.assertTrue(got.startswith(EC.NOTE_PREFIX), got)

    def test_28b_a_denominator_only_position_says_so(self):
        a = answer(1, 10, top1=("drop",))
        got = EC.board_fraction_note(self.side_match("defense", "attack"),
                                     [passed_row(fractions=TWO)], a)
        self.assertIn("自玉側", got)
        self.assertIn("76 / 132", got)
        self.assertIn("分母に入るが分子ではない", got)

    def test_28c_both_sides_get_no_mark(self):
        """**分母に入らない局面には印を付けない**(側が「両方」「どちらでもない」もの ― 実物で 35 件)。

        「分母に入らない」と書くと読者は「関係が無い」と読むが、その局面は分かれ道としては在る。
        """
        a = answer(1, 10, top1=("drop",))
        for top1 in ("both", "none", None):
            self.assertIsNone(EC.board_fraction_note(self.side_match(top1, "attack"),
                                                     [passed_row(fractions=TWO)], a))

    def test_28d_an_unknown_position_gets_no_mark(self):
        """**結合できない局面には印を付けない**(材料が足りないときに断定しない)。"""
        a = answer(2, 99, top1=("drop",))  # rows に無い鍵
        self.assertIsNone(EC.board_fraction_note(self.side_match(), [passed_row(fractions=TWO)], a))
        self.assertIsNone(EC.board_fraction_note(None, [passed_row(fractions=TWO)], a))

    def test_28e_a_duplicate_key_gets_no_mark(self):
        """**同じ鍵が 2 度来た局面には印を付けない**(どちらの側かを断定しない)。

        実物では起きない(404 行 → 404 個の鍵)が、起きたときに黙って片方を採らない。
        """
        sm = self.side_match()
        sm["rows"][("g01", 10)] = None
        a = answer(1, 10, top1=("drop",))
        self.assertIsNone(EC.board_fraction_note(sm, [passed_row(fractions=TWO)], a))

    def test_28f_no_action_means_no_mark(self):
        """**行動が無ければ印も無い**(「どの行動の根拠か」が言えない)。"""
        a = answer(1, 10, top1=("drop",))
        self.assertIsNone(EC.board_fraction_note(self.side_match(), [], a))
        # 単位が違う分数だけのときも印を付けない(P-165)。
        self.assertIsNone(EC.board_fraction_note(self.side_match(),
                                                 [passed_row(fractions=MISMATCH)], a))

    def test_28g_the_mark_reaches_the_draft(self):
        """印が**下書きの本文まで**届く(関数だけ直っていても書き手には見えない)。"""
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 1}, "games": [], "findings": []}
        repro = EC.repro_rows(direct)
        row = passed_row(fractions=TWO)
        md = EC.build_md(direct, patient, repro, [row], [], [],
                         EC.denominators(direct, patient, repro, [row]), None,
                         EC.opening_lines(patient, direct, TODAY), 0,
                         self.side_match("attack", "attack"))
        self.assertIn("分子にも入る", md)
        # 印が無い形でも下書きは組める(印は足すもので、要るものではない)。
        md2 = EC.build_md(direct, patient, repro, [row], [], [],
                          EC.denominators(direct, patient, repro, [row]), None,
                          EC.opening_lines(patient, direct, TODAY))
        self.assertNotIn("分子にも入る", md2)

    def test_28h_the_side_label_is_not_copied(self):
        """**側の語は `check_answer` の 1 か所から来る**(「攻め」「自玉側」を写さない)。"""
        self.assertEqual(set(CA.SIDE_LABEL_JP.values()),
                         {f["label"] for f in TWO})


class DenominatorTableTest(unittest.TestCase):
    """**冊子に出る分母は全部表に行がある**(P-161。2026-09-29)。

    2 周目の表は 3 行(103・24・25)だけで、**行動の根拠の分母と観測の分母が引けなかった**。
    「数の出どころを引ける」と約束しているのに、**行動の根拠の数だけが引けない**形だった。
    """

    def fixture(self):
        answers = [answer(1, 10, top1=("drop",), actual=("drop",)),
                   answer(2, 20, top1=("drop",), actual=("capture",)),
                   answer(2, 30, top1=("capture",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 2}, "games": [], "findings": []}
        return direct, patient, EC.repro_rows(direct)

    def test_26_the_action_denominators_are_rows(self):
        """**行動の根拠の分母が行になる**(分数の 1 本ごとに 1 行)。"""
        direct, patient, repro = self.fixture()
        rows = EC.denominators(direct, patient, repro, [passed_row(fractions=TWO)])
        got = {(r["number"], r["unit"]) for r in rows}
        self.assertIn((107, "局面"), got)
        self.assertIn((132, "局面"), got)
        # 渡さなければ出ない(前の形に戻せることを測る ― 行が勝手に増えない)。
        plain = {(r["number"], r["unit"]) for r in EC.denominators(direct, patient, repro)}
        self.assertNotIn((107, "局面"), plain)
        self.assertNotIn((132, "局面"), plain)

    def test_26b_the_observation_denominators_are_rows(self):
        """**観測の分母も行になる**(局面と局の両方)。行動ではないが冊子に出る。"""
        direct, patient, repro = self.fixture()
        rows = EC.denominators(direct, patient, repro)
        c = CA.top1_actual_cross(direct, "drop")
        got = {(r["number"], r["unit"]) for r in rows}
        self.assertIn((c["positions"], "局面"), got)
        self.assertIn((c["games"], "局"), got)

    def test_26c_a_unit_mismatch_is_not_a_row(self):
        """**単位が違う分数は表に出さない**(P-165)。出せば表そのものが嘘になる。"""
        direct, patient, repro = self.fixture()
        rows = EC.denominators(direct, patient, repro, [passed_row(fractions=MISMATCH)])
        self.assertNotIn(137, {r["number"] for r in rows})
        # **黙って落とさない** ― 理由が書き手への注に出る。
        notes = EC.unit_mismatch_notes([passed_row(fractions=MISMATCH)])
        self.assertEqual(len(notes), 1)
        self.assertIn("P-165", notes[0])

    def test_26d_the_note_reaches_the_draft(self):
        """注が**下書きの本文まで**届く(関数だけ直っていても書き手には見えない)。"""
        direct, patient, repro = self.fixture()
        row = passed_row(fractions=MISMATCH)
        denoms = EC.denominators(direct, patient, repro, [row])
        md = EC.build_md(direct, patient, repro, [row], [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY))
        self.assertIn("分母の表に出していません", md)
        self.assertNotIn("| 137 |", md)

    def test_26e_group_denominators_are_anticipated(self):
        """**群ごとの分母を最初から受ける**(戦型の再集計。後から足すと表が追いつかない)。"""
        direct, patient, repro = self.fixture()
        rows = EC.denominators(direct, patient, repro, [],
                              [("多数の核を共有", 18), ("それ以外", 4), ("署名なし", 3)])
        got = {(r["number"], r["unit"]) for r in rows}
        for n in (18, 4, 3):
            self.assertIn((n, "局"), got)
        self.assertTrue(any("署名なし" in r["from"] for r in rows))

    def test_26f_the_same_row_is_not_repeated(self):
        """同じ数・同じ出どころの行は 1 つ(同じ分数を 2 本の行動が使っても表が二重にならない)。"""
        direct, patient, repro = self.fixture()
        two = [passed_row(item_id="M4", fractions=TWO), passed_row(item_id="M4", fractions=TWO)]
        rows = EC.denominators(direct, patient, repro, two)
        keys = [(r["number"], r["unit"], r["from"]) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))


    # ---- 顧客の語(P-172。2026-09-29)----
    # 4 周目の実物は、この列に「行動 M4 の根拠」「観測」「direct_answers.json」
    # 「patient_report_data.json」「opening_recognition.json の署名」を顧客に見せていた。
    # **表の「数」と「数えたもの」は変えない。「どの集計から出たか」の列だけを顧客の語にする。**
    def all_from(self):
        direct, patient, repro = self.fixture()
        rows = EC.denominators(direct, patient, repro, [passed_row(fractions=TWO)],
                               groups=[("群 A", 2)])
        return [r["from"] for r in rows]

    def test_26g_no_machine_file_name_reaches_the_table(self):
        """**機械のファイル名を顧客に見せない。**

        席 (a) は内部の名札を挙げた。**JSON のファイル名は席も挙げていない**(集計のときに
        私が測って見つけた)。**どちらも顧客の冊子に出す理由が無い。**
        """
        for text in self.all_from():
            for bad in (".json", "direct_answers", "patient_report_data", "opening_recognition"):
                self.assertNotIn(bad, text, f"分母の表に機械の名前が出ている: {text}")

    def test_26h_no_internal_action_number_reaches_the_table(self):
        """**行動の番号(M4・M5…)を出さない。**

        席 (a): 「『行動 M4』『M5』という番号から M1〜M3 が存在して落とされたことがうかがえるが、
        それが何でなぜ落ちたかは本文のどこにも無い」 ― **番号を消せば、落ちた候補の存在が
        表から漏れることも無くなる。**
        """
        for text in self.all_from():
            self.assertNotRegex(text, r"\bM\d\b", f"分母の表に行動の番号が出ている: {text}")
            self.assertNotIn("観測", text, f"分母の表に内部の区分が出ている: {text}")

    def test_26i_the_action_rows_say_what_was_counted(self):
        """**番号を消しても「何を数えた分母か」は残る**(分数の名前で言う)。

        行動の文そのものは道具に無い(`answer_menu.json` は `verifyName` と `minN` だけ)。
        だから分数の名前で言う ― 名前は判定関数が数えている中身をそのまま日本語にしたもの。
        """
        texts = [t for t in self.all_from() if "分かれ道のうち" in t]
        self.assertEqual(len(texts), 2, texts)
        for text in texts:
            self.assertIn(EC.DENOM_SECTION_ACTION, text)

    def test_26j_the_section_name_is_not_a_copy(self):
        """**節の名は正本(`check_structure.SECTIONS`)と同じ語**(写しが片方だけ古くならない)。"""
        import check_structure as CS
        roles = [role for role, _head, _contains in CS.SECTIONS]
        self.assertIn(EC.DENOM_SECTION_ACTION, roles,
                      "分母の表が使う節の名が、門の正本の役割名に無い")


class ThresholdInTheBookletTest(unittest.TestCase):
    """**判定の線を冊子に出す**(2026-09-29。人間の決定「7 割の線を出す・道具上の仮置きと明記」)。

    批評席 (a) が **3 周続けて**「一致率が高いのか低いのか、**比べる相手が無い**」と書いた。
    **比べる相手は道具の中に在った** ― `m4_holds` の `0.7`、`m5_holds` の「0〜1 秒の崩れ率の 2 つぶん」。
    冊子に出ていなかったのは、値が関数の中のリテラルだったからである。
    """

    @staticmethod
    def materials(zero_to_one=(22, 531)):
        class G(object):
            pass
        g = G()
        g.after_long_think_quick = {"collapsed": 9, "n": 37}
        g.by_spent = [{"collapsed": zero_to_one[0], "n": zero_to_one[1]}]
        return {"groups": {"min3": g},
                "sideMatch": {"attack": {"collapsed": 65, "n": 107},
                              "defense": {"collapsed": 76, "n": 132}, "forkTotal": 404}}

    M5_ROW = [{"label": "", "unit": "手",
               "name": "直前の自分の手が 10 秒以上で、この手は 4 秒以内だった手のうち、崩れた手",
               "numerator": 9, "denominator": 37}]

    def thresholds(self):
        return EC.thresholds_of([passed_row(item_id="M4", fractions=TWO),
                                 passed_row(item_id="M5", fractions=self.M5_ROW)],
                                self.materials())

    def test_30_the_line_becomes_a_row_in_the_table(self):
        """**線そのものが分母の表の行になる**(顧客が線を引けるように)。"""
        rows = EC.threshold_denominator_rows(self.thresholds())
        numbers = [(r["number"], r["unit"]) for r in rows]
        self.assertIn((0.7, EC.THRESHOLD_UNIT), numbers)
        for r in rows:
            if r["number"] == 0.7:
                self.assertIn("道具上の仮置き", r["from"])

    def test_30b_the_comparison_pair_becomes_a_row(self):
        """**M5 の線の「比べる相手」の分母も行になる**(席 (a) が 3 周求めた数)。"""
        rows = EC.threshold_denominator_rows(self.thresholds())
        got = [(r["number"], r["unit"], r["from"]) for r in rows if r["number"] == 531]
        self.assertEqual(len(got), 1, rows)
        self.assertIn("比べる相手", got[0][2])

    def test_30c_the_sentences_say_the_line_and_this_time(self):
        """**線の値と「今回の値」を並べるだけ。**「下回った」は書かない(それは書き手の文)。"""
        sentences = EC.threshold_sentences(self.thresholds())
        self.assertEqual(len(sentences), 2, sentences)
        joined = "".join(sentences)
        self.assertIn("0.7", joined)
        self.assertIn("65 / 107", joined)
        self.assertIn("76 / 132", joined)
        self.assertIn("22 / 531", joined)
        self.assertIn("9 / 37", joined)
        for word in ("下回", "上回", "低い", "高い", "問題"):
            self.assertNotIn(word, joined, f"道具が判断の語を書いている: {word}")

    def test_30d_the_sentences_pass_the_ratio_word_rule_of_check_1(self):
        """**「倍」「割」を使わない。**検査 1 は数字 + 倍|割 を「使わない」で落とす(実測 2026-09-29)。

        人間の決定の語は「7 割」だが、**そのままでは冊子に出せない** ― だから `0.7` と「2 つぶん」。
        **この試験が無いと、語を戻した人が組版の最後まで気づかない。**
        """
        for sentence in EC.threshold_sentences(self.thresholds()):
            ratio, _f, _p, _pl = CA.scan_numbers(sentence)
            self.assertFalse(ratio, f"検査 1 が落とす語が入っている: {sentence}")

    def test_30e_the_comparison_numbers_are_candidates_but_the_line_is_not(self):
        """**印字する数は候補に入れる**(P-139 の型)。**線の値は入れない** ―

        `0.7` は検査 1 も門も数として拾わない(両方の桁が `SMALL_NUMBER_MAX` 以下)。
        **拾われない数を候補に入れると、候補の一覧が嘘になる。**
        """
        rows = EC.threshold_numbers(self.thresholds())
        numbers = [r["number"] for r in rows]
        self.assertIn(22, numbers)
        self.assertIn(531, numbers)
        self.assertNotIn(0.7, numbers)

    def test_30f_an_action_without_a_line_adds_nothing(self):
        """**線を持たない行動では、行も文も増えない**(勝手に線を作らない)。"""
        thresholds = EC.thresholds_of([passed_row(item_id="M8", fractions=TWO)], self.materials())
        self.assertEqual(thresholds, [])
        self.assertEqual(EC.threshold_denominator_rows(thresholds), [])
        self.assertEqual(EC.threshold_sentences(thresholds), [])
        self.assertEqual(EC.threshold_numbers(thresholds), [])

    # ---- 配線(**関数を書いても呼ばれなければ冊子に出ない**)----
    # 先に `check_no_real_name` で踏んだ型: **関数の試験だけでは、呼び出しを消す変異が黙る。**
    def wired_fixture(self):
        answers = [answer(1, 10, top1=("drop",), actual=("drop",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 1}, "games": [], "findings": []}
        repro = EC.repro_rows(direct)
        passed = [passed_row(item_id="M4", fractions=TWO),
                  passed_row(item_id="M5", fractions=self.M5_ROW)]
        thresholds = EC.thresholds_of(passed, self.materials())
        denoms = EC.denominators(direct, patient, repro, passed, None, thresholds)
        md = EC.build_md(direct, patient, repro, passed, [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY), 0, None, (), thresholds)
        p1 = EC.p1_numbers(patient, repro, direct, passed, thresholds)
        return denoms, md, p1

    def test_30h_the_table_really_carries_the_line(self):
        """**`denominators` が線の行を持つ**(呼び出しを消したら落ちる)。"""
        denoms, _md, _p1 = self.wired_fixture()
        self.assertIn((0.7, EC.THRESHOLD_UNIT), [(r["number"], r["unit"]) for r in denoms])
        self.assertIn(531, [r["number"] for r in denoms])

    def test_30i_the_draft_really_carries_the_sentences(self):
        """**下書きの「使ってよい固定文」に線の文が在る**(呼び出しを消したら落ちる)。"""
        _denoms, md, _p1 = self.wired_fixture()
        section = md.split(EC.DRAFT_ONLY_HEADINGS[4])[1]
        for sentence in EC.threshold_sentences(EC.thresholds_of(
                [passed_row(item_id="M4", fractions=TWO),
                 passed_row(item_id="M5", fractions=self.M5_ROW)], self.materials())):
            self.assertIn(sentence, section)

    def test_30j_the_candidate_numbers_really_carry_the_pair(self):
        """**候補の数に比べる相手が在る**(呼び出しを消すと、書き手が書いた瞬間に門が止める)。"""
        _denoms, _md, p1 = self.wired_fixture()
        numbers = [r["number"] for r in p1]
        self.assertIn(22, numbers)
        self.assertIn(531, numbers)

    def test_30g_the_values_come_from_the_judgment_table(self):
        """**線の値の出どころは `check_answer.MENU_THRESHOLDS` の 1 か所**(写しを持たない)。

        **字面では見ない。**`assertNotIn("0.7", src)` と書いたら**自分の説明の文に当たって落ちた**
        (このリポジトリで繰り返している型)。**コードの中の数のリテラルだけ**を AST で見る。
        """
        import ast
        path = os.path.join(os.path.dirname(os.path.abspath(EC.__file__)), "exit_candidates.py")
        with io.open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        floats = [n.value for n in ast.walk(tree)
                  if isinstance(n, ast.Constant) and isinstance(n.value, float)]
        self.assertEqual(floats, [], f"線の値が候補の段に写されている: {floats}")
        self.assertIn("CA.menu_threshold_of", io.open(path, encoding="utf-8").read())


class LongThinkForkObservationTest(unittest.TestCase):
    """**10 秒以上考えた手のうち分かれ道だった数**(2026-09-29。③)。行動 1 の条件との橋。

    批評席は **2・3・4 周目と 3 周続けて**「行動 1 の条件『10 秒以上』と根拠の分数(全部の分かれ道)が
    つながらない」と書いた。**その橋にあたる数は材料に在った** ― `time_cause.json` の per-game。
    **観測として出すだけ**(行動にしない)。**判定も割合も作らない。**
    """

    COUNTS = {"longThink": 61, "fork": 33, "oppositeSide": 5}

    def test_31_the_line_says_all_three_numbers(self):
        line = EC.long_think_fork_line(self.COUNTS)
        for n in ("61", "33", "5"):
            self.assertIn(n, line)
        self.assertIn("観測(行動ではありません)", line)

    def test_31b_the_line_says_which_of_the_two_counts_it_is(self):
        """**「10 秒以上考えた手」は 2 通りある**(全部の手 / 崩れを判定できた手)。

        名前でどちらかを言わないと、**分母の出どころが違う数を同じ言い方で並べる**ことになる
        (2026-09-24 の教訓「一致率を 2 つ並べて比べない」)。
        """
        line = EC.long_think_fork_line(self.COUNTS)
        self.assertIn("全部", line)

    def test_31c_no_judgment_and_no_rate(self):
        """**判定の語も割合も作らない**(規則 8 (3)・人間の決定)。"""
        line = EC.long_think_fork_line(self.COUNTS)
        for word in ("%", "率", "多い", "少ない", "傾向", "見落と", "べき"):
            self.assertNotIn(word, line, f"観測に判定の語が入っている: {word}")
        ratio, _f, _p, _pl = CA.scan_numbers(line)
        self.assertFalse(ratio, "「倍」「割」が入っている(検査 1 が落とす)")

    def test_31d_no_material_means_no_line(self):
        """材料が無ければ何も出さない(推測しない)。"""
        self.assertIsNone(EC.long_think_fork_line(None))
        self.assertEqual(EC.long_think_fork_rows(None), [])
        self.assertEqual(EC.long_think_fork_numbers(None), [])

    def test_31e_the_denominators_and_the_candidates_carry_the_numbers(self):
        """**分母の表に 2 つの分母・候補の数に 3 つ全部**(印字する側と数える側は同じ集合。P-139)。"""
        rows = [(r["number"], r["unit"]) for r in EC.long_think_fork_rows(self.COUNTS)]
        self.assertEqual(rows, [(61, "手"), (33, "手")])
        numbers = [r["number"] for r in EC.long_think_fork_numbers(self.COUNTS)]
        self.assertEqual(numbers, [61, 33, 5])

    def test_31f_the_totals_are_guarded(self):
        """**足した数どうしの筋が通らなければ落とす**(`exit_groups` の総和の見張りと同じ形)。

        材料の作りが変わったときに**黙って別の数を出さない**ため。
        """
        def tc(long_think, fork_d, fork_n, opp_d, opp_n):
            return {"raw": [{"games": [{"group": "3 分", "longThinkTotal": long_think,
                                        "forkAmongLongThink": {"numerator": fork_n,
                                                               "denominator": fork_d},
                                        "oppositeSideAmongForkLongThink": {"numerator": opp_n,
                                                                           "denominator": opp_d}}]}]}
        got = CA.long_think_fork_of(tc(61, 61, 33, 33, 5), "3 分")
        self.assertEqual(got, {"longThink": 61, "fork": 33, "oppositeSide": 5})
        with self.assertRaises(CA.CheckAnswerError):
            CA.long_think_fork_of(tc(61, 60, 33, 33, 5), "3 分")   # 10 秒以上の数が合わない
        with self.assertRaises(CA.CheckAnswerError):
            CA.long_think_fork_of(tc(61, 61, 33, 32, 5), "3 分")   # 分かれ道の数が合わない

    def test_31g_the_group_is_the_material_tag_not_the_display_label(self):
        """**組は材料の `group` で引く。**CLI の呼び名(「3 分切れ負け」)では当たらない。

        当たらないと**黙って `None`** になり、観測が丸ごと消える(顧客には「無かった」ように見える)。
        """
        tc = {"raw": [{"games": [{"group": "3 分", "longThinkTotal": 1,
                                  "forkAmongLongThink": {"numerator": 1, "denominator": 1},
                                  "oppositeSideAmongForkLongThink": {"numerator": 0,
                                                                     "denominator": 1}}]}]}
        self.assertIsNotNone(CA.long_think_fork_of(tc, "3 分"))
        self.assertIsNone(CA.long_think_fork_of(tc, "3 分切れ負け"))
        # **字面では見ない。**`assertIn("group_label_of(direct, None)", src)` と書いたら
        # **すぐ上の説明のコメントに当たって**、呼び名で引く変異が黙った(実測。この型は今日 4 度目)。
        # **AST で呼び出しの引数を見る。**
        import ast
        path = os.path.join(os.path.dirname(os.path.abspath(EC.__file__)), "exit_candidates.py")
        with io.open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "long_think_fork_of"]
        self.assertEqual(len(calls), 1, "long_think_fork_of の呼び出しが 1 か所でない")
        group_arg = calls[0].args[1]
        self.assertIsInstance(group_arg, ast.Call, f"組の引数が呼び出しでない: {ast.dump(group_arg)}")
        self.assertEqual(group_arg.func.id, "group_label_of")
        self.assertIsInstance(group_arg.args[1], ast.Constant)
        self.assertIsNone(group_arg.args[1].value,
                          "組を CLI の呼び名で引いている(材料の group に当たらず、観測が黙って消える)")

    # ---- 長考で絞らない「側が逆」(③ の比べる相手。司令塔の依頼 2026-09-29)----
    OPPOSITE_ALL = {"numerator": 51, "denominator": 239}

    def test_31j_the_comparison_line_names_its_own_denominator(self):
        """**5 / 33 と 51 / 239 は分母の出どころが違う** ― だから**別の文**にし、名前で言う。

        1 文に混ぜると「そのうち」で繋がって読め、**比べられない 2 つの率を比べたことになる**
        (2026-09-24 の教訓)。
        """
        line = EC.opposite_all_line(self.OPPOSITE_ALL)
        self.assertIn("239", line)
        self.assertIn("51", line)
        self.assertIn("長考で絞らない", line)
        # **長考の行とは別の文**(同じ行に入れない)。
        self.assertNotIn("10 秒以上", line)
        ratio, _f, _p, _pl = CA.scan_numbers(line)
        self.assertFalse(ratio)

    def test_31k_the_definition_is_the_same_as_the_typescript_one(self):
        """**「側が逆」の定義は `lib/type.ts` の `sideBucketOf` と同じ**(真になる組はちょうど 2 通り)。

        `both` は必ず交わるので逆にならない。`none` も逆にならない。
        **ここがずれると、冊子の数と `time_cause` の数が別の定義になる。**
        """
        self.assertTrue(CA.is_opposite_side("attack", "defense"))
        self.assertTrue(CA.is_opposite_side("defense", "attack"))
        for pair in (("attack", "attack"), ("defense", "defense"),
                     ("attack", "both"), ("both", "attack"), ("both", "both"),
                     ("attack", "none"), ("none", "defense"), ("none", "none")):
            self.assertFalse(CA.is_opposite_side(*pair), pair)
        self.assertEqual(len(CA.OPPOSITE_SIDE_PAIRS), 2)

    def test_31l_the_comparison_rows_and_numbers(self):
        rows = [(r["number"], r["unit"]) for r in EC.opposite_all_rows(self.OPPOSITE_ALL)]
        self.assertEqual(rows, [(239, CA.OPPOSITE_ALL_UNIT)])
        numbers = [r["number"] for r in EC.opposite_all_numbers(self.OPPOSITE_ALL)]
        self.assertEqual(numbers, [239, 51])
        self.assertEqual(EC.opposite_all_line(None), None)
        self.assertEqual(EC.opposite_all_rows(None), [])
        self.assertEqual(EC.opposite_all_numbers(None), [])

    def test_31h_the_draft_and_the_table_really_carry_it(self):
        """**配線**(関数を書いても呼ばれなければ冊子に出ない)。"""
        answers = [answer(1, 10, top1=("drop",), actual=("drop",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 1}, "games": [], "findings": []}
        repro = EC.repro_rows(direct)
        sm = {"attack": {"n": 107, "collapsed": 65}, "defense": {"n": 132, "collapsed": 76},
              "forkTotal": 404, "opposite": self.OPPOSITE_ALL, "rows": {}}
        denoms = EC.denominators(direct, patient, repro, [], None, (), self.COUNTS, sm)
        md = EC.build_md(direct, patient, repro, [], [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY), 0, sm, (), (), self.COUNTS)
        self.assertIn(EC.long_think_fork_line(self.COUNTS), md)
        self.assertIn(EC.opposite_all_line(self.OPPOSITE_ALL), md)
        self.assertIn(EC.LONG_THINK_TWO_COUNTS_NOTE, md)
        numbers = [(r["number"], r["unit"]) for r in denoms]
        self.assertIn((61, "手"), numbers)
        self.assertIn((239, CA.OPPOSITE_ALL_UNIT), numbers)
        p1 = [r["number"] for r in EC.p1_numbers(patient, repro, direct, [], (), self.COUNTS, sm)]
        self.assertIn(5, p1)
        self.assertIn(51, p1)

    def test_31i_the_note_has_no_digits(self):
        """**書き手への注に数を書かない**(検査 1 と門 (ii) が偽の苦情を出す。`c6c8b5b`)。"""
        self.assertNotRegex(EC.LONG_THINK_TWO_COUNTS_NOTE, r"\d")


class OpeningGroupsInTheDraftTest(unittest.TestCase):
    """**戦型の群ごとの再集計が観測の欄に出る**(2026-09-29)。数だけ・戦型名なし。

    群ごとの数の作りは `exit_groups_test.py` が測る。ここは**下書きと候補の JSON まで届くか**。
    """

    GROUPS = [{"key": "core", "label": "群 A", "games": 18, "gameNos": [1, 2],
               "gameIds": ["g01", "g02"], "aheadGames": 12, "aheadLossGames": 3,
               "collapses": 56},
              {"key": "other", "label": "群 B", "games": 4, "gameNos": [4],
               "gameIds": ["g04"], "aheadGames": 4, "aheadLossGames": 3, "collapses": 18},
              {"key": "noSignature", "label": "群 C", "games": 3, "gameNos": [9],
               "gameIds": ["g09"], "aheadGames": 2, "aheadLossGames": 0, "collapses": 5}]

    def fixture(self, groups):
        answers = [answer(1, 10, top1=("drop",), actual=("drop",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 1}, "games": [], "findings": []}
        repro = EC.repro_rows(direct)
        denoms = EC.denominators(direct, patient, repro, [],
                                 EC.group_denominator_rows(groups))
        md = EC.build_md(direct, patient, repro, [], [], [], denoms, None,
                         EC.opening_lines(patient, direct, TODAY), 0, None, groups)
        return direct, patient, repro, denoms, md

    def test_29_the_group_lines_are_in_the_observation_part(self):
        """**観測の欄に 1 群 1 行。**「ひとことで」の節の中(候補の節)に在る。"""
        _d, _p, _r, _den, md = self.fixture(self.GROUPS)
        p1 = md.split("## 局面で見る")[0]
        for label in ("群 A", "群 B", "群 C"):
            self.assertIn(f"- {label}: ", p1)
        self.assertIn("18 局", p1)
        self.assertIn("崩れ 56 回", p1)

    def test_29b_the_group_rows_are_in_the_denominator_table(self):
        """**群の分母が表の行になる**(3 行)。"""
        _d, _p, _r, denoms, md = self.fixture(self.GROUPS)
        got = {(r["number"], r["unit"]) for r in denoms}
        for n in (18, 4, 3):
            self.assertIn((n, "局"), got)
        for label in ("群 A", "群 B", "群 C"):
            self.assertTrue(any(label in r["from"] for r in denoms), label)
        self.assertIn("| 18 | 局 |", md)

    def test_29c_nothing_appears_when_no_groups_are_given(self):
        """**渡さなければ何も変わらない**(認識の JSON が無い顧客でも通る)。"""
        _d, _p, _r, denoms, md = self.fixture([])
        self.assertNotIn("群 A", md)
        self.assertNotIn("戦型", md)
        self.assertFalse(any("群" in r["from"] for r in denoms))

    def test_29d_the_note_tells_the_writer_not_to_name_the_opening(self):
        """**書き手への注で「戦型の名前は書かない」と伝える**(未承認の分類なので)。"""
        _d, _p, _r, _den, md = self.fixture(self.GROUPS)
        self.assertIn("戦型の名前は書かない", md)
        self.assertIn("割合を出さない", md)

    def test_29e_the_json_the_gate_reads_carries_the_groups(self):
        """**候補の JSON まで届く**(書き手と門が同じものを見る)。"""
        direct, patient, repro, denoms, _md = self.fixture(self.GROUPS)
        payload = EC.candidates_json(direct, patient, repro, denoms, [], [],
                                     EC.opening_lines(patient, direct, TODAY), self.GROUPS)
        self.assertEqual([r["key"] for r in payload["openingGroups"]],
                         ["core", "other", "noSignature"])
        self.assertEqual(payload["openingGroups"][1]["gameIds"], ["g04"])

    def test_29g_the_rows_the_table_gets_are_built_by_the_function(self):
        """**`build()` は自分で対を組まない**(組むと `[]` を渡す変異が黙る)。"""
        got = EC.group_denominator_rows(self.GROUPS)
        self.assertEqual(got, [("群 A", 18), ("群 B", 4), ("群 C", 3)])
        self.assertEqual(EC.group_denominator_rows(()), [])
        self.assertEqual(EC.group_denominator_rows(None), [])
        self.assertIn("group_denominator_rows(groups)", SRC)
        # **対を作る式が 1 か所だけ**(写しが戻ったら落ちる)。
        self.assertEqual(SRC.count('for r in groups or ()'), 1)

    def test_29f_the_lines_come_from_exit_groups(self):
        """**行の文は `exit_groups.lines_of` が正本**(候補の段に写しを持たない)。"""
        self.assertIn("EGR.lines_of", SRC)
        self.assertNotIn("一度は優勢になった局", SRC)


class GroupLabelTest(unittest.TestCase):
    """**組の名の出どころは 1 か所**(仕様 §4d・P-162)。

    2026-09-29 の校正で、**「組の名を『3 分』に固定する」変異が緑のまま通った** ―
    合成材料の `group` がたまたま「3 分」だったので、
    **材料から取っているのか固定値なのかを区別する試験が 1 本も無かった。**
    """

    def test_24_the_default_comes_from_the_material(self):
        """渡されなければ**材料の `group`**(「N 分」)。固定値ではない。"""
        answers = [answer(1, 10, top1=("drop",))]
        for label in ("3 分", "10 分 + 30 秒"):
            for a in answers:
                a["group"] = label
            self.assertEqual(EC.group_label_of(direct_of(answers), None), label)

    def test_24b_the_given_label_wins(self):
        """**人間が渡したラベルが勝つ**(持ち時間の形は秒数から決まらない)。"""
        answers = [answer(1, 10, top1=("drop",))]
        got = EC.group_label_of(direct_of(answers), "3 分切れ負け")
        self.assertEqual(got, "3 分切れ負け")
        self.assertNotEqual(got, answers[0]["group"])

    def test_24c_two_groups_fall(self):
        """**2 組以上は落ちる。**黙って 1 組として書くと、冒頭の局数と本文の分母が食い違う。"""
        answers = [answer(1, 10, top1=("drop",)), answer(2, 20, top1=("drop",))]
        answers[1]["group"] = "10 分 + 30 秒"
        with self.assertRaises(EC.ExitCandidatesError):
            EC.group_label_of(direct_of(answers), None)

    def test_24d_the_label_reaches_the_opening(self):
        """**渡したラベルが冒頭の 1 文目に出る**(関数の戻り値だけでなく md まで届く)。"""
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}], "findings": []}
        got = EC.opening_lines(patient, direct, TODAY, "3 分切れ負け")
        self.assertIn("3 分切れ負け 1 局を、", got[0])
        self.assertIn(TODAY, got[0])
        # 渡さなければ材料の語のまま(出力不変)。
        self.assertIn("3 分 1 局を、", EC.opening_lines(patient, direct, TODAY)[0])


class NoActionTest(unittest.TestCase):
    def test_20_zero_actions_prints_the_fixed_sentence(self):
        """**差が無ければ行動にしない。**0 本なら固定文が出る(2026-09-29 の司令塔の判断)。"""
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, [], [], [],
                         EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
        self.assertIn(EI.NO_ACTION_SENTENCE, md)

    def test_20b_the_sentence_is_not_printed_when_there_are_actions(self):
        answers = [answer(1, 10, top1=("drop",))]
        direct = direct_of(answers)
        repro = EC.repro_rows(direct)
        patient = {"summary": {"games": 1}, "games": [{"no": 1}],
                   "findings": [{"kind": "phase", "oneLine": "一言", "text": "崩れ 79 回でした", "shown": True}]}
        md = EC.build_md(direct, patient, repro, [passed_row(fractions=TWO)], [], [],
                         EC.denominators(direct, patient, repro), None,
                         EC.opening_lines(patient, direct, TODAY))
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
        payload = EC.candidates_json(direct, patient, repro, [], [], [],
                                     EC.opening_lines(patient, direct, TODAY))
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

class ForkNestingTest(unittest.TestCase):
    """**分かれ道の数の入れ子**(P-183。2026-09-29。5 周目の批評席 (a))。

    席は「404・239・103・51 の関係(どれがどれの部分集合か)が本編・付録のどちらにも無い」と書いた。
    **404 は本編に 0 件**で、付録の前文にしか無い(実測)。

    **実測した関係**(`whatif-v2` の 404 行と `direct_answers` の 103 件を突き合わせた):
    239 ⊆ 404・103 ⊆ 404・51 ⊆ 239、**103 ⊄ 239 かつ 239 ⊄ 103**(別の絞り方。両方に当たるのは 68)。
    """

    SIDE_MATCH = {"forkTotal": 404, "opposite": {"numerator": 51, "denominator": 239}}
    # **103 件**。他の試験と同じ `answer()` で組む(材料の形を 2 通り持たない)。
    DIRECT = direct_of([answer(1, i + 1) for i in range(103)])
    PATIENT = {"summary": {"games": 25}, "games": [], "findings": []}

    def nesting(self):
        return EC.fork_nesting_of(self.DIRECT, self.SIDE_MATCH)

    def test_32_the_four_numbers_come_from_the_materials(self):
        self.assertEqual(self.nesting(),
                         {"all": 404, "oneSide": 239, "shallow": 103, "opposite": 51})

    def test_32b_no_material_means_no_sentence(self):
        """**材料が無ければ数を作らない。**"""
        self.assertIsNone(EC.fork_nesting_of(self.DIRECT, None))
        self.assertIsNone(EC.fork_nesting_of(self.DIRECT, {"forkTotal": 404}))
        self.assertIsNone(EC.fork_nesting_line(None))
        self.assertEqual(EC.fork_nesting_rows(None), [])
        self.assertEqual(EC.fork_nesting_numbers(None), [])

    def test_32c_the_sentence_carries_all_four(self):
        line = EC.fork_nesting_line(self.nesting())
        for n in ("404", "239", "103", "51"):
            self.assertIn(n, line)

    def test_32d_the_sentence_does_not_nest_the_two_cuts(self):
        """**239 と 103 の間に「そのうち」を掛けない**(実測では部分集合ではない)。

        「そのうち」は **404 に 1 回だけ**掛かる。そのうえで「別の絞り方」と明言する ―
        この 1 節が、席が挙げた「どれがどれの部分集合か」への答えである。
        """
        line = EC.fork_nesting_line(self.nesting())
        self.assertEqual(line.count("そのうち"), 1, f"「そのうち」が 1 回でない: {line}")
        self.assertIn("別の絞り方", line)
        self.assertIn("片方がもう片方に含まれるわけではありません", line)

    def test_32e_the_sentence_has_no_number_outside_the_four(self):
        """**文に出る数は 4 つだけ**(検査 1 と門 (ii) が拾う)。「この二つ」は漢数字。"""
        import re as _re
        # **10 以上の数だけを見る。**「第 1 候補」の 1 は冊子じゅうに在る言い方で、
        # 検査 1 も 9 以下を落とす(`SMALL_NUMBER_MAX`)。
        found = {int(x) for x in _re.findall(r"[0-9]+", EC.fork_nesting_line(self.nesting()))}
        self.assertEqual({n for n in found if n >= 10}, {404, 239, 103, 51})

    def test_32f_the_numbers_are_in_the_candidate_list(self):
        """**門 (ii) を通る**(印字する側と数える側は同じ集合。P-139)。"""
        repro = EC.repro_rows(self.DIRECT)
        numbers = EC.p1_numbers(self.PATIENT, repro, direct=self.DIRECT, side_match=self.SIDE_MATCH)
        got = {n["number"] for n in numbers}
        for want in (404, 239, 103, 51):
            self.assertIn(want, got, f"{want} が候補の数に無い")

    def test_32g_only_the_new_denominator_is_added_to_the_table(self):
        """分母の表に足すのは **404 だけ**(239・103・51 は既に行がある / 分子)。

        器の余裕は 0 なので、**行を増やすのは 1 行まで**(司令塔の条件)。
        """
        rows = EC.fork_nesting_rows(self.nesting())
        self.assertEqual([r["number"] for r in rows], [404])

    def test_32h_the_sentence_is_offered_in_the_draft(self):
        """**md の「使ってよい固定文」に出ること**(書き手が選ぶ)。

        **`build_md` を通して見る** ― 関数だけを見ると、`build_md` が呼んでいなくても緑になる。
        """
        repro = EC.repro_rows(self.DIRECT)
        denoms = EC.denominators(self.DIRECT, self.PATIENT, repro, side_match=self.SIDE_MATCH)
        md = EC.build_md(self.DIRECT, self.PATIENT, repro, [], [], [], denoms, None,
                         EC.opening_lines(self.PATIENT, self.DIRECT, TODAY), 0, self.SIDE_MATCH)
        self.assertIn("分かれ道は全部で 404 局面", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
