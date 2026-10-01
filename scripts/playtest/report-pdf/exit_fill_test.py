# -*- coding: utf-8 -*-
# `exit_fill.py`(⑥ Slot filling)の試験。束 1 = F-1・F-2・F-3 + F-8(司令塔の判断 2026-10-01)。
#
# 【この道具の危ない所】**⑥ は顧客の文を作る最初の段**である。危ないのは 3 つ ―
# (1) **採用の印が無い候補を組んでしまう**(⑤ の下書きは `adoptedBy: null` を書くので、
#     段を飛ばして手で走らせると下書きがそのまま冊子になる)。
# (2) **契約の写しを python に作る**(表が 2 か所になり、黙ってずれる)。
# (3) **⑥ が自分の言葉を書く**(人間が承認していない文が顧客に出る)。
#
# 【土台は合成】実物の `answer_selection.json` はまだ無い(採用は司令塔か人間がする)。
# 問いの字と人間の文だけは**実物の道具から引く**(写さない)。
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_answer as CA  # noqa: E402
import check_structure as CS  # noqa: E402
import exit_fill as EF  # noqa: E402
import exit_index as EI  # noqa: E402

SRC = io.open(os.path.join(HERE, "exit_fill.py"), encoding="utf-8").read()


def item_ref():
    """**毎回あたらしい object を返す。**1 つを使い回すと、1 か所の守りを外す変異が
    別の場所の誤りで緑になる(2026-10-01 に ⑤ の契約で実際に踏んだ)。"""
    return {"seatIndex": 0, "hypothesisId": "h01"}


def selection(**over):
    """**⑥ が読む欄だけ**を持つ最小の選択。契約に合っているかは見ない側。"""
    base = {
        "customerRef": "c5",
        "packetId": "22aee8fe696d0262",
        "lead": {"itemRef": item_ref(), "statementSource": "integration.representative"},
        "p1": [{"slot": f"p1.{i}", "aggregateIds": ["a1"], "itemRef": item_ref(),
                "readingRequired": True} for i in (1, 2, 3)],
        "answers": [{"questionId": "q1", "status": "unanswerable",
                     "machineSummary": "partial", "itemRefs": [item_ref()],
                     "aggregateIds": ["a1"]}],
        "boards": [{"slot": f"p2.{i}", "gameId": "g01", "ply": 48,
                    "packetRef": "facts.engine[0].top1"} for i in (1, 2)],
        "actions": [{"slot": "act.1", "menuId": "M4", "itemRef": item_ref()}],
        "humanQueue": [],
        "adoptedBy": {"who": "commander", "at": "2026-10-01",
                      "basis": "検証を通った読みのうち問いに合うものを採った"},
    }
    base.update(over)
    return base


class SelectionReadTest(unittest.TestCase):
    """**F-8 の前半。⑤ の出力のうち、⑥ が読む欄だけを見る。**"""

    def test_f1_a_minimal_selection_passes(self):
        self.assertEqual(EF.selection_problems(selection()), [])

    def test_f2_the_fields_it_reads_are_pinned(self):
        """**読む欄の表を字で留める。**欄を外す変異がここで赤くなる。"""
        self.assertEqual(EF.SELECTION_TOP_FIELDS,
                         ("customerRef", "packetId", "lead", "p1", "answers", "boards",
                          "actions", "adoptedBy"))
        self.assertEqual(EF.ADOPTED_FIELDS, ("who", "at", "basis"))
        self.assertEqual(EF.SELECTION_ITEM_FIELDS, {
            "p1": ("slot", "aggregateIds", "itemRef", "readingRequired"),
            "answers": ("questionId", "status", "itemRefs", "aggregateIds"),
            "boards": ("slot", "gameId", "ply", "packetRef"),
            "actions": ("slot", "menuId", "itemRef"),
        })

    def test_f3_each_missing_top_field_is_named(self):
        """**1 つ外すと 1 件、しかも名前が出る。**まとめて数えるだけだと、
        別の欄を見る変異が黙る。"""
        for field in EF.SELECTION_TOP_FIELDS:
            s = selection()
            del s[field]
            got = EF.selection_problems(s)
            if field == "adoptedBy":
                # 採用の印は不在と「印が無い」の 2 件が出る(どちらも正しい)。
                self.assertTrue(any(field in g for g in got), got)
                continue
            self.assertEqual(len(got), 1, (field, got))
            self.assertIn(field, got[0])

    def test_f4_a_null_adopted_mark_stops(self):
        """**⑤ の下書きがここで止まる。**`exitSelect.ts --draft` は `adoptedBy: null`
        を書くので、段を飛ばすとこの形が入ってくる。"""
        got = EF.selection_problems(selection(adoptedBy=None))
        self.assertEqual(len(got), 1, got)
        self.assertIn("採用の印", got[0])

    def test_f5_a_blank_adopted_field_stops(self):
        """**空白だけの根拠で通さない**(委任の条件 2「承認には根拠を書く」)。
        全角空白・タブ・`None`・数も落ちる。"""
        for field in EF.ADOPTED_FIELDS:
            for bad in ("", " ", "　", "\t", None, 0, ["x"]):
                s = selection()
                s["adoptedBy"] = dict(s["adoptedBy"])
                s["adoptedBy"][field] = bad
                got = EF.selection_problems(s)
                self.assertEqual(len(got), 1, (field, bad, got))
                self.assertIn(field, got[0])

    def test_f6_each_missing_item_field_is_named_with_its_place(self):
        """**並びの中の欄も 1 つずつ。**場所(並びの名と番号)が出る。"""
        for name, fields in EF.SELECTION_ITEM_FIELDS.items():
            for field in fields:
                s = selection()
                s[name] = [dict(row) for row in s[name]]
                del s[name][0][field]
                got = EF.selection_problems(s)
                self.assertEqual(len(got), 1, (name, field, got))
                self.assertIn(f"{name}[0].{field}", got[0])

    def test_f7_lead_without_an_item_ref_is_named(self):
        s = selection(lead={"statementSource": "integration.representative"})
        got = EF.selection_problems(s)
        self.assertEqual(len(got), 1, got)
        self.assertIn("lead.itemRef", got[0])

    def test_f8_broken_shapes_are_named_not_crashed(self):
        """**object でない・並びでないものは落とす**(例外で落ちるのではなく苦情で返す)。"""
        self.assertIn("object でない", EF.selection_problems(["x"])[0])
        got = EF.selection_problems(selection(p1={"slot": "p1.1"}))
        self.assertTrue(any("p1 が並びでない" in g for g in got), got)
        got = EF.selection_problems(selection(answers=["x"]))
        self.assertTrue(any("answers[0] が object でない" in g for g in got), got)

    def test_f9_it_does_not_copy_the_contract(self):
        """**契約の写しを作らない**(司令塔の条件)。型・列挙・字の形は 1 つも見ない ―
        それは ⑤ の門の仕事で、ここに写せば**表が 2 か所になる。**

        **だから、契約に合わない値でもこの検査は通る。**
        契約の検査を足した変異がここで赤くなる。
        """
        s = selection()
        s["packetId"] = "ぜんぜん封ではない"
        s["customerRef"] = "x"
        s["answers"] = [dict(s["answers"][0], questionId="Q-9", status="なんでも",
                             machineSummary="なんでも")]
        s["actions"] = [dict(s["actions"][0], menuId="M99")]
        s["boards"] = [dict(r, ply=-1) for r in s["boards"]]
        s["p1"] = s["p1"][:1]  # 3 本でなくても、**件数は ⑤ の門が見る**
        s["adoptedBy"] = dict(s["adoptedBy"], who="だれか")
        self.assertEqual(EF.selection_problems(s), [])

    def test_f10_read_selection_stops_on_a_bad_file(self):
        with tempfile.TemporaryDirectory() as d:
            good = os.path.join(d, "good.json")
            bad = os.path.join(d, "bad.json")
            with io.open(good, "w", encoding="utf-8") as f:
                json.dump(selection(), f, ensure_ascii=False)
            with io.open(bad, "w", encoding="utf-8") as f:
                json.dump(selection(adoptedBy=None), f, ensure_ascii=False)
            self.assertEqual(EF.read_selection(good)["customerRef"], "c5")
            with self.assertRaises(EF.ExitFillError) as cm:
                EF.read_selection(bad)
            self.assertIn("採用の印", str(cm.exception))


class SlotMapShapeTest(unittest.TestCase):
    """**F-8 の後半。`slot_map.json` の形。**まだ契約(schema)にしない ―
    **記録が 3 件を超えるまで**(1 件で形を決めると 2 件目で変わる)。"""

    def test_f11_the_columns_are_pinned(self):
        """**7 欄・⑥ が 6 欄・⑦ が 1 欄**を字で留める。"""
        self.assertEqual(EF.SLOT_MAP_COLUMNS,
                         ("slot", "marks", "itemRef", "aggregateIds", "text",
                          "textSha256", "page"))
        self.assertEqual(EF.SLOT_MAP_COLUMNS_FROM_FILL,
                         ("slot", "marks", "itemRef", "aggregateIds", "text", "textSha256"))
        self.assertEqual(EF.SLOT_MAP_COLUMNS_FROM_RENDER, ("page",))
        self.assertEqual(len(EF.SLOT_MAP_COLUMNS), 7)
        self.assertEqual(len(EF.SLOT_MAP_COLUMNS_FROM_FILL), 6)
        # **2 つに割った欄が、ちょうど全部**(どちらかに寄せた変異が落ちる)。
        self.assertEqual(EF.SLOT_MAP_COLUMNS_FROM_FILL + EF.SLOT_MAP_COLUMNS_FROM_RENDER,
                         EF.SLOT_MAP_COLUMNS)
        # **`page` は ⑥ が書かない**(組んだ後にしか分からない)。
        self.assertNotIn("page", EF.SLOT_MAP_COLUMNS_FROM_FILL)

    def test_f12_a_row_has_exactly_the_six_columns(self):
        row = EF.fill_row("p1.1", "あ", marks=["<!-- agg: x -->"], aggregate_ids=["x"])
        self.assertEqual(set(row), set(EF.SLOT_MAP_COLUMNS_FROM_FILL))
        self.assertEqual(EF.slot_map_problems([row]), [])
        self.assertIsNone(row["itemRef"])

    def test_f13_the_seal_is_taken_from_the_body(self):
        """**封は本文から**(別の字から取る変異が落ちる)。"""
        row = EF.fill_row("p1.1", "あいうえお")
        self.assertEqual(row["textSha256"], EF.text_sha256("あいうえお"))
        self.assertNotEqual(row["textSha256"], EF.text_sha256("p1.1"))
        self.assertNotEqual(row["textSha256"], EF.text_sha256(""))
        self.assertEqual(len(row["textSha256"]), 64)

    def test_f14_a_seal_that_does_not_match_the_body_is_named(self):
        """**文が後で変わったら落ちる**(組版が文を変えていないことを測る道具)。"""
        row = EF.fill_row("p1.1", "あ")
        row["text"] = "い"
        got = EF.slot_map_problems([row])
        self.assertEqual(len(got), 1, got)
        self.assertIn("封が本文と合わない", got[0])
        self.assertIn("p1.1", got[0])

    def test_f15_a_blank_slot_or_body_falls(self):
        for slot, text in (("", "あ"), ("  ", "あ"), ("p1.1", ""), ("p1.1", "　")):
            with self.assertRaises(EF.ExitFillError, msg=(slot, text)):
                EF.fill_row(slot, text)

    def test_f16_a_repeated_slot_is_named_with_both_places(self):
        rows = [EF.fill_row("p1.1", "あ"), EF.fill_row("p1.1", "い")]
        got = EF.slot_map_problems(rows)
        self.assertEqual(len(got), 1, got)
        self.assertIn("p1.1", got[0])
        self.assertIn("0", got[0])
        self.assertIn("1", got[0])

    def test_f17_a_missing_or_unknown_column_is_named(self):
        for field in EF.SLOT_MAP_COLUMNS_FROM_FILL:
            row = EF.fill_row("p1.1", "あ")
            del row[field]
            got = EF.slot_map_problems([row])
            self.assertTrue(any(field in g for g in got), (field, got))
        row = dict(EF.fill_row("p1.1", "あ"), よけいな欄="x")
        got = EF.slot_map_problems([row])
        self.assertEqual(len(got), 1, got)
        self.assertIn("知らない欄", got[0])

    def test_f18_the_page_column_belongs_to_the_render_step(self):
        """**⑥ の出力に `page` が在ってはいけない**(⑦ が足す)。
        ⑦ の後は逆に**無ければ落ちる。**"""
        six = EF.fill_row("p1.1", "あ")
        got = EF.slot_map_problems([dict(six, page=3)])
        self.assertEqual(len(got), 1, got)
        self.assertIn("page", got[0])
        got = EF.slot_map_problems([six], with_page=True)
        self.assertEqual(len(got), 1, got)
        self.assertIn("page", got[0])
        self.assertEqual(EF.slot_map_problems([dict(six, page=1)], with_page=True), [])

    def test_f19_a_page_that_is_not_a_number_is_named(self):
        six = EF.fill_row("p1.1", "あ")
        for bad in (0, -1, True, "3", 1.5, None):
            got = EF.slot_map_problems([dict(six, page=bad)], with_page=True)
            self.assertEqual(len(got), 1, (bad, got))
            self.assertIn("ページが数でない", got[0])

    def test_f20_broken_shapes_are_named(self):
        self.assertIn("並びでない", EF.slot_map_problems({"slot": "x"})[0])
        self.assertIn("object でない", EF.slot_map_problems(["x"])[0])
        row = dict(EF.fill_row("p1.1", "あ"), marks="x")
        self.assertTrue(any("marks が並びでない" in g for g in EF.slot_map_problems([row])))
        row = dict(EF.fill_row("p1.1", "あ"), aggregateIds="x")
        self.assertTrue(any("aggregateIds が並びでない" in g
                            for g in EF.slot_map_problems([row])))

    def test_f21_the_slot_names_it_invents_are_pinned(self):
        """⑤ がスロットの名を持たない 2 か所。**字で留める。**"""
        self.assertEqual(EF.LEAD_SLOT, "lead")
        self.assertEqual(EF.ANSWER_SLOT_PREFIX, "ans.")
        self.assertEqual(EF.answer_slot("q1"), "ans.q1")
        self.assertEqual(EF.answer_slot("q12"), "ans.q12")
        with self.assertRaises(EF.ExitFillError):
            EF.answer_slot("  ")


class QuestionSectionTest(unittest.TestCase):
    """**F-3 節「お預かりした問い」。**⑤ の `status` で文の出どころが決まる。"""

    # **土台は合成。**`out/` は gitignore なので**実データを試験で読まない**
    # (この族の決まり ― `check_structure_test.py` の冒頭。読むと新しい作業場で落ちる。
    # 実際に worktree で `ERROR: exit_fill_test` になって気づいた 2026-10-01)。
    #
    # **長さだけ実物に合わせる。**実物の q1 は**53 文字**(2026-10-01 に実測。
    # `out/c5/packet/observation-request.json`)。合成の字も 53 文字にして、
    # 下の f25 が留める 163 が**実物と同じ数**になるようにしてある。
    QUESTION_TEXT = "三分切れは練習対局のつもりで指しており、何局かは自分があまり選ばない駒組みを試している。影響を知りたいです"
    QUESTIONS = [{"id": "q1", "text": QUESTION_TEXT, "askedAt": "2026-09-29",
                  "via": "relayed"}]

    def answers(self, status="unanswerable", qid="q1"):
        return [{"questionId": qid, "status": status}]

    def test_f22_no_question_means_no_section(self):
        """**問いが 0 件なら節ごと出さない**(⑧ の G-4。「問いは無かった」とも書かない)。"""
        self.assertEqual(EF.question_section_lines("c5", [], [], 25), [])
        self.assertEqual(EF.question_section_lines("c5", None, [], 25), [])

    def test_f23_the_real_question_comes_out_with_the_human_sentence(self):
        """**実物の形。**見出し → 問いの字 → 人間が書いた文 + 印。"""
        lines = EF.question_section_lines("c5", self.QUESTIONS, self.answers(), 25)
        self.assertEqual(lines[0], "## " + CS.QUESTION_HEADING)
        self.assertIn(self.QUESTIONS[0]["text"], lines)
        body = [l for l in lines if "ans:" in l]
        self.assertEqual(len(body), 1, lines)
        self.assertIn(EI.unanswerable_past_games(25), body[0])
        self.assertIn("<!-- ans: q1 unanswerable -->", body[0])

    def test_f24_the_question_is_not_presented_as_a_quotation(self):
        """**「」で囲まない。**材料は「人間が中継した本人の言葉。本人が書いた文字列
        そのものではない」と書いている ― 囲むと**本人の字だと主張する。**"""
        text = self.QUESTIONS[0]["text"]
        lines = EF.question_section_lines("c5", self.QUESTIONS, self.answers(), 25)
        self.assertIn(text, lines)
        self.assertNotIn("「" + text + "」", "\n".join(lines))
        # **問いの行は字そのまま**(何も足さない)。囲む変異がここで赤くなる ―
        # 「人間が書いた文には鉤括弧が在る」ので、本編ぜんたいから鉤括弧を探すのでは測れない。
        qline = [l for l in lines if text in l]
        self.assertEqual(qline, [text], lines)
        # 判断の根拠は材料の `requestedScope.note`(「人間が中継した本人の言葉。
        # **本人が書いた文字列そのものではない**」)― `out/` は gitignore なので
        # 試験では読まず、**道具の注**に出どころを書いてある。
        self.assertIn("本人が書いた文字列そのものではない", SRC)

    def test_f25_the_section_passes_the_gate(self):
        """**⑧ の門を通る。**長さは**門が数える道**で測る(印も数に入る)。"""
        lines = EF.question_section_lines("c5", self.QUESTIONS, self.answers(), 25)
        md = "\n".join(["# 対局後診断", "", "## ひとことで", "", "- 数。", ""]
                       + lines + ["## 数え方", "", "(注)"])
        problems = []
        CS.check_question_section(md, len(self.QUESTIONS), problems)
        self.assertEqual(problems, [])
        body = CS.question_section_body(md)
        # **字で留める**(実測 2026-10-01)。問いの字 53 + 人間の文 80 + 印 29 + 空白 1。
        self.assertEqual(len(self.QUESTION_TEXT), 53)
        self.assertEqual(len(body), 163)
        # **足し算を留める**(どれか 1 つが変わったら 163 も変わる)。
        self.assertEqual(len(body),
                         len(self.QUESTION_TEXT) + len(EI.unanswerable_past_games(25))
                         + len("<!-- ans: q1 unanswerable -->") + 1)
        self.assertLessEqual(len(body), CS.MAX_QUESTION_SECTION_CHARS)
        # **印が 29 文字ぶん持ち分を食う**(門は機械の印も数える)。正直な限界。
        self.assertEqual(len("<!-- ans: q1 unanswerable -->"), 29)

    def test_f26_the_approved_table_is_pinned(self):
        """**承認済みの文の表を字で留める。**鍵は(顧客の符号, 問いの id)で、
        **status ごとの固定文ではない。**"""
        self.assertEqual(list(EF.APPROVED_ANSWER_TEXTS), [("c5", "q1")])
        status, build = EF.APPROVED_ANSWER_TEXTS[("c5", "q1")]
        self.assertEqual(status, "unanswerable")
        self.assertIs(build, EI.unanswerable_past_games)

    def test_f36_another_customer_does_not_get_this_customer_s_approved_text(self):
        """**鍵は(顧客の符号, 問いの id)の組**で、**問いの id だけではない。**

        **独立監査が見つけた沈黙(2026-10-01)**: 鍵を `question_id` だけに緩める変異が
        **690 本中 1 本も赤くならなかった。**実装は正しく組で引いていたが、
        **組にした理由として明記した退行(別の顧客に c5 の文が漏れる)を測る試験が無かった。**
        `test_f26` は**表の鍵の値そのもの**を字で留めるだけで、
        `answer_text_of` が**その鍵をどう使っているか**(顧客の符号を本当に見ているか)は見ていない。

        **落ちる側は「緩めたら通ってしまう側」から選ぶ** ― 顧客の符号だけを変え、
        問いの id・status は c5 と同じにする(緩めると c5 の文がそのまま出る組み合わせ)。
        """
        q = [{"id": "q1", "text": "べつの顧客の問い"}]
        a = self.answers("unanswerable", "q1")
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.question_section_lines("c6", q, a, 25)
        # **c5 の文が出るのではなく、人間が書く文が無いことで止まる。**
        self.assertIn("人間が書く", str(cm.exception))
        # 直に呼んでも同じ(節を組む側だけで守っていない)。
        with self.assertRaises(EF.ExitFillError):
            EF.answer_text_of("c6", "q1", "unanswerable", 25)
        # **c5 なら出る**(逆の向き ― 組を無視して「いつも落とす」変異も赤になる)。
        self.assertEqual(EF.answer_text_of("c5", "q1", "unanswerable", 25),
                         EI.unanswerable_past_games(25))
        # **顧客が違えば、渡された文が使える**(問いの id が c5 と同じでも承認済みに当たらない)。
        self.assertEqual(
            EF.answer_text_of("c6", "q1", "answered", 25, "こういう読みです。"),
            "こういう読みです。")

    def test_f27_a_status_that_does_not_match_the_approval_falls(self):
        """**人が承認した状態と合わない文を出さない。**"""
        for status in ("answered", "partial"):
            with self.assertRaises(EF.ExitFillError, msg=status) as cm:
                EF.question_section_lines("c5", self.QUESTIONS, self.answers(status), 25)
            self.assertIn("承認済みの文", str(cm.exception))

    def test_f28_a_supplied_text_does_not_override_the_human(self):
        """**人間が書いた文を上書きしない。**"""
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.question_section_lines("c5", self.QUESTIONS, self.answers(), 25,
                                      {"q1": "べつの文"})
        self.assertIn("上書き", str(cm.exception))

    def test_f29_an_unanswerable_question_without_an_approved_text_falls(self):
        """**なぜ答えられないかは人間が書く文**であって、席の読みの言い換えではない。
        ⑥ は書かない ― 渡されても使わない。"""
        q = [{"id": "q2", "text": "べつの問い"}]
        a = self.answers("unanswerable", "q2")
        for supplied in (None, {"q2": "答えられません"}):
            with self.assertRaises(EF.ExitFillError, msg=repr(supplied)) as cm:
                EF.question_section_lines("c5", q, a, 25, supplied)
            self.assertIn("人間が書く", str(cm.exception))

    def test_f30_an_answered_question_needs_a_supplied_text(self):
        """**⑥ は固定文を新しく作らない。**渡されれば使う。"""
        q = [{"id": "q2", "text": "べつの問い"}]
        a = self.answers("answered", "q2")
        for supplied in (None, {}, {"q2": "  "}):
            with self.assertRaises(EF.ExitFillError, msg=repr(supplied)) as cm:
                EF.question_section_lines("c5", q, a, 25, supplied)
            self.assertIn("固定文を新しく作らない", str(cm.exception))
        lines = EF.question_section_lines("c5", q, a, 25, {"q2": "こういう読みです。"})
        self.assertTrue(any("こういう読みです。" in l and "ans: q2 answered" in l
                            for l in lines), lines)

    def test_f31_a_question_without_an_answer_falls(self):
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.question_section_lines("c5", self.QUESTIONS, [], 25)
        self.assertIn("⑤ の答えが無い", str(cm.exception))

    def test_f32_two_answers_for_one_question_fall(self):
        a = self.answers() + self.answers()
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.question_section_lines("c5", self.QUESTIONS, a, 25)
        self.assertIn("2 行", str(cm.exception))

    def test_f33_a_blank_question_falls(self):
        for q in ([{"id": "", "text": "あ"}], [{"id": "q1", "text": "  "}],
                  [{"id": "q1"}], [{"text": "あ"}]):
            with self.assertRaises(EF.ExitFillError, msg=repr(q)):
                EF.question_section_lines("c5", q, self.answers(), 25)

    def test_f34_the_mark_is_checked_against_the_one_grammar(self):
        """**印の文法は `check_answer.ANS_TAG_RE` の 1 か所**(写しを作らない)。
        読めない形になったら**組んだ所で止まる。**"""
        self.assertEqual(EF.ans_mark("q1", "unanswerable"),
                         "<!-- ans: q1 unanswerable -->")
        self.assertEqual(EF.ans_mark("q12", "answered"), "<!-- ans: q12 answered -->")
        for qid, status in (("Q1", "answered"), ("1", "answered"), ("q1", "un answerable"),
                            ("q1", "  "), ("", "answered"), ("q1", "answered -->")):
            with self.assertRaises(EF.ExitFillError, msg=(qid, status)):
                EF.ans_mark(qid, status)
        # **文法を写していない**(正規表現が 2 か所になっていない)。
        self.assertIn("CA.ANS_TAG_RE", SRC)
        self.assertNotIn("ans:\\s*", SRC)

    def test_f35_the_heading_is_not_copied(self):
        """**見出しの字は `check_structure` の 1 か所から。**写すと、門と組版がずれる。"""
        self.assertIn("CS.QUESTION_HEADING", SRC)
        self.assertNotIn('"お預かりした問い"', SRC)
        self.assertNotIn("## お預かりした問い", SRC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
