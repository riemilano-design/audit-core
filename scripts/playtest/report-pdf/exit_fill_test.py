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


# ==================== 束 2(F-4〜F-7)====================
#
# 【土台は合成】packet・候補の JSON・統合・下書きの md は全部ここで組む(`out/` は読まない)。
# **数と字だけ封じた最終版(2026-09-29、`9_本編_最終版.md`)に合わせる** ― 期待値は実物の行の字。
# 「表から作った出力を同じ表と比べない」: 期待値は ⑥ の定数からではなく、**送った冊子の行をそのまま**書く。
import exit_candidates as EC  # noqa: E402
import exit_gate as EG  # noqa: E402
import exit_groups as EGR  # noqa: E402

M4_ATTACK_NAME = "第 1 候補が攻めの手だった分かれ道のうち、実戦も攻めの手だった局面"
M4_DEFENSE_NAME = "第 1 候補が自玉側の手だった分かれ道のうち、実戦も自玉側の手だった局面"
M5_NAME = "直前の自分の手が 10 秒以上で、この手は 4 秒以内だった手のうち、崩れた手"
M4_CORE = "10 秒以上考える局面では、攻めの候補と自玉側の候補を 1 つずつ思い浮かべてから比べる"
M5_CORE = "長考した次の 1 手は、相手の返しを見てからひと呼吸"

# 封じた最終版の 12〜14 行目(事実の部分)と 20・22 行目(盤)。**字をそのまま**。
SEALED_FACT_1 = ("第 1 候補が攻めの手だった分かれ道 107 局面のうち、実戦も攻めの手だった局面が 65。"
                 "第 1 候補が自玉側の手だった分かれ道 132 局面のうち、実戦も自玉側の手だった局面が 76。")
SEALED_FACT_2 = "直前の自分の手が 10 秒以上で、この手は 4 秒以内だった 37 手のうち、崩れた手が 9。"
SEALED_FACT_3 = "一度は優勢(+300 以上)になった対局が 18 局。そのうち負けた対局が 6 局。"
SEALED_ACTION_1 = (f"1. {M4_CORE}<!-- menu: M4 -->　― 根拠は{M4_ATTACK_NAME}が 65 / 107、"
                   f"{M4_DEFENSE_NAME}が 76 / 132 です")
SEALED_ACTION_2 = f"2. {M5_CORE}<!-- menu: M5 -->　― 根拠は{M5_NAME}が 9 / 37 です"


def packet():
    return {
        "packetId": "22aee8fe696d0262",
        "facts": {
            "games": [{"gameId": "g11", "no": 11}, {"gameId": "g12", "no": 12}, {"gameId": "g13", "no": 13}],
            # 添字 0 と 1 を盤に使う。**engine の ply は表示の手数**(`displayPly`)で、分かれ道の行の
            # `ply`(本人の手の鍵)とはわざと違う値にする(実物は 404 行のうち 263 行で違う)。
            "engine": [{"gameId": "g11", "ply": 48, "sfen": "(合成)", "src": "e1"},
                       {"gameId": "g12", "ply": 70, "sfen": "(合成)", "src": "e1"},
                       {"gameId": "g13", "ply": 110, "sfen": "(合成)", "src": "e1"}],
            "branches": [{"gameId": "g11", "ply": 47, "displayPly": 48, "top1Side": "attack",
                          "actualSide": "defense", "src": "e2"},
                         {"gameId": "g12", "ply": 69, "displayPly": 70, "top1Side": "defense",
                          "actualSide": "attack", "src": "e2"},
                         {"gameId": "g13", "ply": 109, "displayPly": 110, "src": "e2"}],
        },
        "aggregates": [
            {"id": "sideMatch.attack", "numerator": 65, "denominator": 107},
            {"id": "sideMatch.defense", "numerator": 76, "denominator": 132},
            {"id": "time.quickAfterLongThink", "numerator": 9, "denominator": 37},
            {"id": "time.bySpent0to1", "numerator": 22, "denominator": 531},
            {"id": "aheadThenLost", "numerator": 6, "denominator": 18},
        ],
    }


def fraction(menu_id, label, name, unit, numerator, denominator):
    return {"id": menu_id, "label": label, "name": name, "unit": unit,
            "numerator": numerator, "denominator": denominator}


def candidates():
    return {
        "actionFractions": [fraction("M4", "攻め", M4_ATTACK_NAME, "局面", 65, 107),
                            fraction("M4", "自玉側", M4_DEFENSE_NAME, "局面", 76, 132),
                            fraction("M5", "", M5_NAME, "手", 9, 37)],
        "boards": ["13/110 付録3 3 分", "11/48 付録3 3 分", "12/70 付録3 3 分"],
        "menuPassed": ["M4", "M5", "M6"],
        # 実物の候補の p1Numbers(deliver1、2026-10-05 に読んだ)は 1・4・7・10・300 も持つ
        # (閾値と「第 1 候補」の 1、「0.7」が割れた 7)。門 (ii) はそれで通っている。同じ数を置く。
        "p1Numbers": [{"number": n, "unit": "x", "from": "合成"}
                      for n in (3, 25, 65, 107, 76, 132, 9, 37, 18, 6, 22, 531, 1, 4, 7, 10, 300)],
        "unitMismatchFractions": [],
    }


def passed_rows():
    def row(menu_id, core, fractions):
        return {"id": menu_id, "minN": 5, "denominator": fractions[0]["denominator"],
                "item": {"actionCore": core, "evidenceName": "x", "verifyName": "y"},
                "fractions": fractions}
    return [row("M4", M4_CORE, [f for f in candidates()["actionFractions"] if f["id"] == "M4"]),
            row("M5", M5_CORE, [f for f in candidates()["actionFractions"] if f["id"] == "M5"]),
            row("M6", "(合成の M6)", [fraction("M6", "", "x のうち、y", "局面", 1, 2)])]


def ref(seat, hid):
    return {"seatIndex": seat, "hypothesisId": hid}


STATEMENTS = {
    "0:lead": "攻めも自玉側も第 1 候補と違う側が残り(65 / 107、76 / 132)、長考の直後の 1 手は 9 / 37 で崩れ、優勢 18 局のうち 6 局を落とした",
    "0:h1": "一致率は 0.7 を下回り、65 / 107 と 76 / 132 で両方の側に残った",
    "1:h2": "0〜1 秒の 531 手で崩れは 22 手、長考直後は 9 / 37",
    "2:h3": "一度優勢になった 18 局のうち 6 局を落とした",
    "0:q1": "問いの読み(合成)",
}


def integration():
    def cluster(key, statement):
        seat, hid = key.split(":")
        return {"itemRefs": [ref(int(seat), hid)],
                "representative": {"statement": statement,
                                   # **`internal` は読まれない**(schema に無い欄。写しても参照されないことを f52 が見る)
                                   "internal": {"reasoning": "普段と違う型を試していた(内部の推測)"}}}
    return {"clusters": [cluster(k, v) for k, v in STATEMENTS.items()]}


def texts():
    return {
        "lead": "攻めか自玉側かの分かれ道で第 1 候補と違う側が両方に残り、長考の直後の 1 手は崩れやすく、一度良くなった局を落としていた",
        "p1.1": "どちらの一致率も、道具が仮に置いている線(0.7)を下回りました。",
        "p1.2": "0〜1 秒で指した 531 手では崩れが 22 手でした。長考の直後の 1 手は、それより崩れる割合が高かった、という数です。",
        "p1.3": "負けた局の多くは、一度は良くなってからのものでした。",
    }


def selection2():
    return selection(
        runId="558b8a81-20261001-2",
        lead={"itemRef": ref(0, "lead"), "statementSource": "integration.representative"},
        p1=[{"slot": "p1.1", "aggregateIds": ["sideMatch.attack", "sideMatch.defense"],
             "itemRef": ref(0, "h1"), "readingRequired": True},
            {"slot": "p1.2", "aggregateIds": ["time.quickAfterLongThink", "time.bySpent0to1"],
             "itemRef": ref(1, "h2"), "readingRequired": True},
            {"slot": "p1.3", "aggregateIds": ["aheadThenLost"],
             "itemRef": ref(2, "h3"), "readingRequired": True}],
        answers=[{"questionId": "q1", "status": "unanswerable", "machineSummary": "partial",
                  "itemRefs": [ref(0, "q1")], "aggregateIds": []}],
        boards=[{"slot": "p2.1", "gameId": "g11", "ply": 48, "packetRef": "facts.engine[0].top1Usi"},
                {"slot": "p2.2", "gameId": "g12", "ply": 70, "packetRef": "facts.engine[1].top1Usi"}],
        actions=[{"slot": "act.2", "menuId": "M5", "itemRef": ref(1, "h2")},
                 {"slot": "act.1", "menuId": "M4", "itemRef": ref(0, "h1")}],
    )


def draft_md():
    """段 `exit-candidates` の下書きの**形**(節の並び・TODO・注・下書きだけの節)。中身は合成。"""
    L = ["# 本編(合成)", "", "3 分切れ負け 25 局を、1 手ずつ将棋エンジンで調べました(2026-09-28)。", "",
         "## ひとことで", "", EC.TODO, EC.note("数 3 つを選ぶ"), "",
         EC.DRAFT_ONLY_HEADINGS[0], "", "- **発見(合成)**", "  - 数: 999 局面", "",
         EC.DRAFT_ONLY_HEADINGS[1], "", "- 行動の根拠(行動 M4・攻め): x が 65 / 107。", "",
         "## 局面で見る", "", EC.TODO, EC.note("ここに残すのは盤 2 つ分の行だけ"), "",
         "- 3 分 の 13 局目 110 手目<!-- pos: 13/110 付録3 3 分 -->",
         "- 3 分 の 11 局目 48 手目<!-- pos: 11/48 付録3 3 分 -->",
         "- 3 分 の 12 局目 70 手目<!-- pos: 12/70 付録3 3 分 -->", "",
         "## 試せること", "", EC.TODO, EC.note("下から本数を決める"), "",
         EC.DRAFT_ONLY_HEADINGS[2], "", SEALED_ACTION_1, SEALED_ACTION_2,
         "3. (合成の M6)<!-- menu: M6 -->　― 根拠は x のうち、y が 1 / 2 です", "",
         EC.DRAFT_ONLY_HEADINGS[3], "", "| 項目 | 下限 | いまの分母 | 届かなかった理由 |", "|---|---|---|---|", "",
         EC.DRAFT_ONLY_HEADINGS[4], "", f"- {EI.NOTHING_TO_HIDE_SENTENCE}", "",
         "## 次の 25 局で、何で答え合わせをするか", "", EC.note("残した行動の行だけにする"), "",
         EC.VERIFY_TABLE_HEADER, "|---|---|---|",
         f"| {M4_CORE}<!-- menu: M4 --> | 「{M4_ATTACK_NAME}」と「{M4_DEFENSE_NAME}」 | 攻め 65 / 107、自玉側 76 / 132 |",
         f"| {M5_CORE}<!-- menu: M5 --> | 「{M5_NAME}」 | 9 / 37 |",
         "| (合成の M6)<!-- menu: M6 --> | 「x のうち、y」 | 1 / 2 |", "",
         "## 数え方", "", "- 数え方の固定文(合成)。", "",
         "<!-- appendix: 数の出どころ -->", EC.note("この節の下の表は付録へ"), "",
         "### 数の分母がどこから来たか", "", "| 数 | 数えたもの | どの集計から出たか |", "|---|---|---|",
         "| 107 | 局面 | (合成) |", "",
         "## 対応表 ― 何局目が、どのファイルか(本人用)", "", "| 局 | ファイル名 | 先後 | 手数 | 結果 |",
         "|---|---|---|---|---|", "| 1 | g01-sente.kif | 先手 | 123 | 勝ち |", ""]
    return "\n".join(L)


QUESTIONS2 = QuestionSectionTest.QUESTIONS


def build(**over):
    kw = dict(draft_md=draft_md(), selection=selection2(), packet=packet(), candidates=candidates(),
              questions=QUESTIONS2, texts=texts(), statements=EF.statements_of(integration()),
              passed=passed_rows(), games=25)
    kw.update(over)
    return EF.build_document(**kw)


class ParaphraseCheckTest(unittest.TestCase):
    """**§3 の 1 番。言い換えは `statement` だけに掛ける ― 数・手の字は部分集合で、字も同じ。**"""

    def test_f37_same_value_in_another_form_falls(self):
        """**「値が同じなら通す」に緩めた変異がここで赤くなる**(計画 §7.3 の 1 行目)。"""
        statement = "一致率は 3 / 4 で、▲７六歩が第 1 候補"
        self.assertEqual(EF.paraphrase_problems("3 / 4 でした", statement, "x"), [])
        for output in ("75% でした", "３ / ４ でした", "0.75 でした"):
            got = EF.paraphrase_problems(output, statement, "x")
            self.assertTrue(got, output)
        # 漢数字は数の字として拾えないので**部分集合の検査では通る** ― 測って書く(限界。
        # 漢数字の「三」は数の主張として検査 1 も拾わない。ここで新しい拾い方を作らない)。
        self.assertEqual(EF.paraphrase_problems("三 / 四 でした", statement, "x"), [])

    def test_f38_moves_must_be_the_same_characters(self):
        statement = "▲７六歩が第 1 候補で、実戦は ▲２六歩"
        self.assertEqual(EF.paraphrase_problems("▲７六歩と ▲２六歩", statement, "x"), [])
        got = EF.paraphrase_problems("▲７六歩と ▲３四歩", statement, "x")
        self.assertEqual(len(got), 1, got)
        self.assertIn("▲３四歩", got[0])
        # 統合の statement に無い手を言い換えが足したら落ちる(文法は `check_answer.MOVE_RE`)。
        self.assertTrue(EF.paraphrase_problems("△３四歩", "手の無い文", "x"))

    def test_f39_the_forbidden_word_falls_in_every_supplied_text(self):
        """**§7.3 の 5 行目: 「普段」は太字の 1 文にも読みの文にも出ない。**語の表は 1 か所。"""
        self.assertEqual(EGR.LABEL_FORBIDDEN_WORDS, ("普段",))
        got = EF.paraphrase_problems("普段と違う型でした", "普段と違う型でした", "x")
        self.assertEqual(len(got), 1, got)
        self.assertIn("普段", got[0])
        with self.assertRaises(EF.ExitFillError):
            EF.check_supplied_words("普段の型", "x")
        for slot in ("lead", "p1.1"):
            t = texts()
            t[slot] = t[slot] + " 普段の型より多い"
            with self.assertRaises(EF.ExitFillError) as cm:
                build(texts=t)
            self.assertIn("普段", str(cm.exception))
            self.assertIn(slot, str(cm.exception))

    def test_f40_a_number_the_statement_does_not_have_falls_with_its_place(self):
        t = texts()
        t["p1.1"] = "一致率は 0.7 を下回り、108 局面でした"
        with self.assertRaises(EF.ExitFillError) as cm:
            build(texts=t)
        self.assertIn("108", str(cm.exception))
        self.assertIn("p1.1", str(cm.exception))
        self.assertNotIn("0.7", str(cm.exception).split("statement の数")[0])

    def test_f41_a_missing_text_stops_and_names_the_slot(self):
        """**⑥ は書かない。**渡されなければ止まる(既定の文を入れない)。"""
        for slot in ("lead", "p1.2"):
            t = texts()
            del t[slot]
            with self.assertRaises(EF.ExitFillError) as cm:
                build(texts=t)
            self.assertIn(slot, str(cm.exception))
            self.assertIn("渡されていない", str(cm.exception))

    def test_f42_the_statement_is_the_representative_and_internal_is_not_read(self):
        """統合から読むのは `representative.statement` だけ。`internal` は参照しない
        (人間の決定: 内部の推測は下流から参照できない)。"""
        statements = EF.statements_of(integration())
        self.assertEqual(statements["0:h1"], STATEMENTS["0:h1"])
        self.assertNotIn("普段", json.dumps(statements, ensure_ascii=False))
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.statement_for(statements, ref(9, "zz"), "x")
        self.assertIn("9:zz", str(cm.exception))
        self.assertIn("統合の clusters に無い", str(cm.exception))


class TermMaskTest(unittest.TestCase):
    def test_f70_the_term_first_candidate_is_not_a_number_claim(self):
        """「第 1 候補」の 1 は用語の一部(`check_structure.TERM_LINES`)。席の statement が「第一候補」と
        書いていても、言い換えが「第 1 候補」と書いてよい(用語の 4 行に合わせる)。"""
        self.assertEqual(CS.TERM_LINES[0][0], "第 1 候補")
        self.assertEqual(EF.number_tokens("第 1 候補が 65 / 107"), ["65", "107"])
        self.assertEqual(EF.paraphrase_problems("第 1 候補と違う側が 51 / 239", "第一候補と逆の側は 51・239", "x"), [])
        # 用語の外の 1 は数の主張のまま(「1 手」)。
        self.assertTrue(EF.paraphrase_problems("長考の直後の 1 手", "長考の直後の手", "x"))
        self.assertEqual(EF.paraphrase_problems("長考の直後の 1 手", "直後の 1 手", "x"), [])


class LeadAndFactsTest(unittest.TestCase):
    """**F-5 の尾と F-4 の 3 本。**期待値は封じた最終版の字。"""

    def test_f43_the_tail_and_the_count_are_pinned(self):
        self.assertEqual(EF.LEAD_TAIL_TEMPLATE, " ― という読みです。数は {n} つ。")
        self.assertEqual(EF.lead_line("読み", 3), "**読み** ― という読みです。数は 3 つ。")
        self.assertEqual(CS.HONBUN_P1_FACT_COUNT, 3)
        for n in (2, 4, 0):
            with self.assertRaises(EF.ExitFillError):
                EF.lead_line("読み", n)

    def test_f44_the_connective_type_reproduces_the_sealed_three(self):
        """**2 規則で 3 本が字まで再現する**(司令塔の判断 (D)。名前は `check_answer` の `name`)。"""
        self.assertEqual(EF.FACT_CONNECTIVE, "のうち、")
        self.assertEqual(EF.connective_fact(M4_ATTACK_NAME, 65, 107, "局面"),
                         "第 1 候補が攻めの手だった分かれ道 107 局面のうち、実戦も攻めの手だった局面が 65。")
        self.assertEqual(EF.connective_fact(M4_DEFENSE_NAME, 76, 132, "局面"),
                         "第 1 候補が自玉側の手だった分かれ道 132 局面のうち、実戦も自玉側の手だった局面が 76。")
        # **A の末尾が単位の語なら落とす**(「…4 秒以内だった手」+「37 手」→「…4 秒以内だった 37 手」)。
        self.assertEqual(EF.connective_fact(M5_NAME, 9, 37, "手"), SEALED_FACT_2)
        with self.assertRaises(EF.ExitFillError):
            EF.connective_fact("のうち、が 2 回のうち、ある", 1, 2, "局")
        with self.assertRaises(EF.ExitFillError):
            EF.connective_fact("接続が無い", 1, 2, "局")

    def test_f45_the_ahead_then_lost_type_is_pinned_with_two_holes(self):
        """**司令塔の判断 (ii)**: 封じた 2 文を型に。穴 2 つ。局数も閾値も値として焼かない
        (`+300` は字の一部 = P-188 の 3 か所目)。「のうち、」の型に乗せない。"""
        self.assertEqual(EF.AHEAD_THEN_LOST_TEMPLATE,
                         "一度は優勢(+300 以上)になった対局が {denominator} 局。そのうち負けた対局が {numerator} 局。")
        self.assertEqual(EF.AHEAD_THEN_LOST_HOLES, 2)
        self.assertEqual(EF.AHEAD_THEN_LOST_TEMPLATE.count("{"), EF.AHEAD_THEN_LOST_HOLES)
        self.assertEqual(EF.ahead_then_lost_fact(6, 18), SEALED_FACT_3)
        self.assertNotEqual(EF.ahead_then_lost_fact(3, 12), SEALED_FACT_3)
        self.assertNotIn(EF.FACT_CONNECTIVE, EF.AHEAD_THEN_LOST_TEMPLATE)
        self.assertNotIn("18", EF.AHEAD_THEN_LOST_TEMPLATE)
        self.assertIn("+300", EF.AHEAD_THEN_LOST_TEMPLATE)
        # 局の語は `exit_index.COUNTING_NOTES` の「優勢から負けた対局」と同じ「対局」(司令塔の理由 (2))。
        self.assertTrue(any("優勢から負けた対局" in s for s in EI.COUNTING_NOTES))

    def test_f46_two_aggregates_make_one_fact_in_the_sealed_order(self):
        fact, reaches = EF.fact_text(["sideMatch.attack", "sideMatch.defense"],
                                     EF.aggregate_rows_of(packet()), candidates())
        self.assertEqual(fact, SEALED_FACT_1)
        self.assertTrue(reaches)
        fact3, reaches3 = EF.fact_text(["aheadThenLost"], EF.aggregate_rows_of(packet()), candidates())
        self.assertEqual(fact3, SEALED_FACT_3)
        self.assertFalse(reaches3)
        # **印だけの id**(読みの数の裏づけ)は文を作らない。
        fact2, _ = EF.fact_text(["time.quickAfterLongThink", "time.bySpent0to1"],
                                EF.aggregate_rows_of(packet()), candidates())
        self.assertEqual(fact2, SEALED_FACT_2)
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.fact_text(["time.bySpent0to1"], EF.aggregate_rows_of(packet()), candidates())
        self.assertIn("組める型が無い", str(cm.exception))

    def test_f47_the_numbers_come_from_the_packet_and_must_agree_with_the_candidates(self):
        """**数は packet から**(⑤ は id だけ)。候補の分数と食い違えば止まる ― どちらが正しいかを決めない。"""
        p = packet()
        p["aggregates"][0]["numerator"] = 66
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.fact_text(["sideMatch.attack"], EF.aggregate_rows_of(p), candidates())
        self.assertIn("66 / 107", str(cm.exception))
        self.assertIn("65 / 107", str(cm.exception))
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.fact_text(["sideMatch.nowhere"], EF.aggregate_rows_of(packet()), candidates())
        self.assertIn("packet に無い", str(cm.exception))
        # 分母を落とした packet の行は整数でないので止まる。
        p = packet()
        del p["aggregates"][2]["denominator"]
        with self.assertRaises(EF.ExitFillError):
            EF.fact_text(["time.quickAfterLongThink"], EF.aggregate_rows_of(p), candidates())
        # 候補に同じ (行動, ラベル) の分数が 2 件なら止まる。
        c = candidates()
        c["actionFractions"].append(dict(c["actionFractions"][0]))
        with self.assertRaises(EF.ExitFillError):
            EF.fact_text(["sideMatch.attack"], EF.aggregate_rows_of(packet()), c)

    def test_f48_the_id_table_is_pinned_and_the_marks_use_the_one_grammar(self):
        self.assertEqual(EF.AGGREGATE_FRACTION_OF, {
            "sideMatch.attack": ("M4", "攻め"),
            "sideMatch.defense": ("M4", "自玉側"),
            "time.quickAfterLongThink": ("M5", ""),
        })
        self.assertEqual(EF.AHEAD_THEN_LOST_ID, "aheadThenLost")
        mark = EF.agg_mark("sideMatch.attack")
        self.assertEqual(CA.AGG_TAG_RE.fullmatch(mark).group(1), "sideMatch.attack")
        with self.assertRaises(EF.ExitFillError):
            EF.agg_mark("")
        with self.assertRaises(EF.ExitFillError):
            EF.agg_mark("a -->")
        self.assertEqual(EF.READING_PREFIX, "― 読み: ")
        bullet = EF.fact_bullet("事実。", "読み。", [EF.agg_mark("a"), EF.agg_mark("b")])
        self.assertEqual(bullet, "- 事実。― 読み: 読み。<!-- agg: a --><!-- agg: b -->")
        self.assertEqual(EF.fact_bullet("事実。", "読み。"), "- 事実。― 読み: 読み。")
        with self.assertRaises(EF.ExitFillError):
            EF.agg_mark("a b")


class AggMarksTest(unittest.TestCase):
    def test_f69_marks_are_written_when_every_number_of_the_line_is_in_the_aggregate_rows(self):
        """印が付く道も測る: 行の数が全部集計行の数なら 2 つの印が付く。1 つ外れた数で付かない。"""
        rows = EF.aggregate_rows_of(packet())
        line = "- 攻めの分かれ道 107 局面のうち、実戦も攻めの局面が 65。― 読み: 両方の側に残った。"
        marks, why = EF.agg_marks_for(line, ["sideMatch.attack"], rows)
        self.assertEqual(marks, ["<!-- agg: sideMatch.attack -->"])
        self.assertIsNone(why)
        marks, why = EF.agg_marks_for(line + " 第 1 候補は", ["sideMatch.attack"], rows)
        self.assertEqual(marks, [])
        self.assertIn("[1]", why)
        self.assertIn("(xi)", why)


class BoardsTest(unittest.TestCase):
    """**F-6。候補に無い局面を出さない。**"""

    def test_f49_a_board_comes_out_with_the_candidate_mark_and_the_sides(self):
        line, inner = EF.board_line(selection2()["boards"][0], packet(), candidates())
        self.assertEqual(inner, "11/48 付録3 3 分")
        self.assertEqual(line, "**11 局目 48 手目 ― 実戦は自玉側の手、第 1 候補は攻めの手**<!-- pos: 11/48 付録3 3 分 -->")
        # **印の鍵は engine の ply(= 表示の手数 48)**。分かれ道の行の ply(47)は出ない。
        self.assertNotIn("47", line)
        self.assertEqual(CA.POS_TAG_RE.search(line).group(1), inner)
        # 側の語は `check_answer.SIDE_JP` の 1 か所から(「守り」は出ない。P-185)。
        self.assertNotIn("守り", line)
        self.assertEqual((CA.SIDE_JP["attack"], CA.SIDE_JP["defense"]), ("攻め", "自玉側"))
        self.assertEqual(EF.BOARD_LINE_TEMPLATE,
                         "**{game_no} 局目 {display_ply} 手目 ― 実戦は{actual}の手、第 1 候補は{top1}の手**")

    def test_f50_only_facts_engine_is_accepted(self):
        """**`facts.engine` 以外の場所を受けない**(計画 §7.2 の F-6 の変異)。"""
        for bad in ("aggregates.sideMatch.attack.numerator", "facts.moves[0].usi",
                    "facts.branches[0].top1Usi", "facts.engine", "engine[0].top1Usi", None, 3):
            b = dict(selection2()["boards"][0], packetRef=bad)
            with self.assertRaises(EF.ExitFillError, msg=bad) as cm:
                EF.board_line(b, packet(), candidates())
            self.assertIn("facts.engine", str(cm.exception))

    def test_f51_the_row_must_agree_with_the_selection_and_be_a_candidate(self):
        # 添字の行と ⑤ の (gameId, ply) が違う(⑤ が分かれ道の行の ply 47 を書いた形)。
        b = dict(selection2()["boards"][0], ply=47)
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.board_line(b, packet(), candidates())
        self.assertIn("違う", str(cm.exception))
        # 添字が範囲の外。
        b = dict(selection2()["boards"][0], packetRef="facts.engine[9].top1Usi")
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.board_line(b, packet(), candidates())
        self.assertIn("facts.engine[9]", str(cm.exception))
        # **候補の boards に無い局面**(下書きに印字されていない)。
        c = candidates()
        c["boards"] = [m for m in c["boards"] if not m.startswith("11/48")]
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.board_line(selection2()["boards"][0], packet(), c)
        self.assertIn("候補の boards に 0 件", str(cm.exception))
        # 分かれ道でない局面(branches に無い)。
        p = packet()
        p["facts"]["branches"] = p["facts"]["branches"][1:]
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.board_line(selection2()["boards"][0], p, candidates())
        self.assertIn("分かれ道", str(cm.exception))

    def test_f52_without_sides_the_heading_is_only_the_place(self):
        b = {"slot": "p2.1", "gameId": "g13", "ply": 110, "packetRef": "facts.engine[2].sfen"}
        line, inner = EF.board_line(b, packet(), candidates())
        self.assertEqual(line, "**13 局目 110 手目**<!-- pos: 13/110 付録3 3 分 -->")

    def test_f53_exactly_two_boards(self):
        s = selection2()
        s["boards"] = s["boards"][:1]
        with self.assertRaises(EF.ExitFillError) as cm:
            build(selection=s)
        self.assertIn("1 件", str(cm.exception))


class ActionsTest(unittest.TestCase):
    """**F-7。文は承認済みの表の passed 行から。表に無い・届かない行動は出ない。**"""

    def test_f54_the_action_lines_are_the_draft_s_lines_in_slot_order(self):
        adopted = EF.adopted_action_rows(selection2()["actions"], passed_rows())
        self.assertEqual([slot for slot, _ in adopted], ["act.1", "act.2"])
        self.assertEqual(EF.action_line(1, adopted[0][1]), SEALED_ACTION_1)
        self.assertEqual(EF.action_line(2, adopted[1][1]), SEALED_ACTION_2)
        self.assertEqual(EF.verify_table_row(adopted[1][1]),
                         f"| {M5_CORE}<!-- menu: M5 --> | 「{M5_NAME}」 | 9 / 37 |")

    def test_f55_an_action_outside_the_passed_rows_falls(self):
        actions = [{"slot": "act.1", "menuId": "M6", "itemRef": ref(0, "h1")}]
        passed = [r for r in passed_rows() if r["id"] != "M6"]
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.adopted_action_rows(actions, passed)
        self.assertIn("M6", str(cm.exception))
        self.assertIn("下限を通った候補に無い", str(cm.exception))
        with self.assertRaises(EF.ExitFillError):
            EF.adopted_action_rows([{"slot": "act.1", "menuId": "M9", "itemRef": ref(0, "h1")}], passed_rows())

    def test_f56_slot_numbers_must_run_from_one(self):
        for slots in (("act.2",), ("act.1", "act.3"), ("act.0",), ("p3.1",)):
            actions = [{"slot": s, "menuId": "M4", "itemRef": ref(0, "h1")} for s in slots]
            with self.assertRaises(EF.ExitFillError, msg=slots):
                EF.adopted_action_rows(actions, passed_rows())

    def test_f57_no_action_adopted_prints_the_approved_sentence(self):
        s = selection2()
        s["actions"] = []
        md, rows, _notes = build(selection=s)
        self.assertIn(EI.NO_ACTION_SENTENCE, md)
        self.assertEqual([r for r in rows if r["slot"].startswith("act.")], [])
        self.assertNotIn("<!-- menu:", md)


class BuildDocumentTest(unittest.TestCase):
    """**器を埋めた本編。**封じた最終版の行がそのまま出て、下書きの印・注・候補の節は残らない。"""

    def test_f58_the_sealed_lines_come_out(self):
        md, rows, _notes = build()
        for line in (SEALED_FACT_1, SEALED_FACT_2, SEALED_FACT_3, SEALED_ACTION_1, SEALED_ACTION_2,
                     "**11 局目 48 手目 ― 実戦は自玉側の手、第 1 候補は攻めの手**<!-- pos: 11/48 付録3 3 分 -->",
                     "**12 局目 70 手目 ― 実戦は攻めの手、第 1 候補は自玉側の手**<!-- pos: 12/70 付録3 3 分 -->",
                     "**" + texts()["lead"] + "** ― という読みです。数は 3 つ。",
                     "- " + SEALED_FACT_1 + "― 読み: " + texts()["p1.1"],
                     EI.unanswerable_past_games(25) + " <!-- ans: q1 unanswerable -->"):
            self.assertIn(line, md, line)
        # 下書きの印・注・候補の節は 1 つも残らない。(印 `agg` は f60 ― 3 本とも付けられない)
        self.assertNotIn(EC.TODO, md)
        self.assertNotIn(EC.NOTE_PREFIX, md)
        for heading in EC.DRAFT_ONLY_HEADINGS:
            self.assertNotIn(heading, md)
        self.assertNotIn("999", md)
        # 下書きの他の節は**そのまま**(冒頭・数え方・対応表)。
        for kept in ("3 分切れ負け 25 局を、1 手ずつ将棋エンジンで調べました(2026-09-28)。",
                     "- 数え方の固定文(合成)。", "<!-- appendix: 数の出どころ -->",
                     "| 1 | g01-sente.kif | 先手 | 123 | 勝ち |", "| 107 | 局面 | (合成) |"):
            self.assertIn(kept, md, kept)
        # 答え合わせの表は採った 2 行だけ(M6 の行は落ちる)。
        self.assertNotIn("(合成の M6)", md)
        self.assertEqual(md.count("<!-- menu: M4 -->"), 2)  # 行動の行 + 表の行
        self.assertEqual(md.count("<!-- menu: M5 -->"), 2)
        self.assertTrue(md.endswith("\n"))

    def test_f59_the_question_section_sits_right_after_the_lead_section(self):
        md, _, _ = build()
        heads = [t for _, t in CS.heading_lines(md)]
        self.assertEqual(heads[:3], ["ひとことで", CS.QUESTION_HEADING, "局面で見る"])
        # 問いが 0 件なら節が無い。
        md0, rows0, _ = build(questions=[], selection=dict(selection2(), answers=[]))
        self.assertNotIn(CS.QUESTION_HEADING, md0)
        self.assertEqual([r for r in rows0 if r["slot"].startswith("ans.")], [])

    def test_f60_the_slot_map_covers_every_slot_and_seals_the_body(self):
        md, rows, _notes = build()
        self.assertEqual([r["slot"] for r in rows],
                         ["lead", "p1.1", "p1.2", "p1.3", "ans.q1", "p2.1", "p2.2", "act.1", "act.2"])
        self.assertEqual(EF.slot_map_problems(rows), [])
        for row in rows:
            self.assertIn(row["text"], md)
            self.assertEqual(row["textSha256"], EF.text_sha256(row["text"]))
        by_slot = {r["slot"]: r for r in rows}
        self.assertEqual(by_slot["p1.1"]["aggregateIds"], ["sideMatch.attack", "sideMatch.defense"])
        # **印は 3 本とも付かない**(測った: 第 1 候補 → 1、(0.7) → 7、10 秒・4 秒、+300 が門 (xi) の
        # 「行の数は全部集計行に在る」に当たる)。対応は aggregateIds に残り、理由は注記に出る。
        self.assertEqual(by_slot["p1.1"]["marks"], [])
        self.assertEqual(by_slot["p1.2"]["marks"], [])
        self.assertEqual(by_slot["p1.3"]["marks"], [])
        self.assertEqual(len(_notes), 3, _notes)
        self.assertIn("[1, 7]", _notes[0])
        self.assertIn("[1, 4, 10]", _notes[1])
        self.assertIn("[300]", _notes[2])
        self.assertNotIn("<!-- agg:", md)
        self.assertEqual(by_slot["p1.1"]["itemRef"], ref(0, "h1"))
        self.assertEqual(by_slot["lead"]["itemRef"], ref(0, "lead"))
        self.assertEqual(by_slot["p2.1"]["marks"], ["<!-- pos: 11/48 付録3 3 分 -->"])
        self.assertEqual(by_slot["act.1"]["marks"], ["<!-- menu: M4 -->"])
        self.assertEqual(by_slot["ans.q1"]["marks"], ["<!-- ans: q1 unanswerable -->"])
        self.assertNotIn("page", by_slot["lead"])

    def test_f61_the_built_body_passes_the_gate_s_checks_that_need_no_materials(self):
        """**同じ `exit_gate.py` を通る**(書き手の道と同じ門)。材料の要らない検査を全部回す。"""
        md, _, _ = build()
        problems, notes = [], []
        sections = EG.sections_of(CA.strip_dev_section(md))
        EG.check_todo(md, problems)
        EG.check_p1(sections, candidates(), problems)
        EG.check_p1_reaches_the_actions(sections, candidates(), problems)
        EG.check_no_unit_mismatch(md, candidates(), problems)
        EG.check_p2(sections, candidates(), problems)
        EG.check_draft_leftovers(md, problems)
        EG.check_agg_tags(md, packet(), problems, notes)
        request = {"customerQuestions": QUESTIONS2}
        EG.check_ans_tags(CA.strip_dev_section(md), request, selection2(), problems, notes)
        self.assertEqual(problems, [])
        # 器の門(⑧)の節の有無・位置・長さ。
        CS.check_question_section(md, 1, problems)
        self.assertEqual(problems, [])

    def test_f62_the_forbidden_word_is_only_in_the_human_sentence(self):
        """**§7.3 の 5 行目を本編の全部で見る。**人間が承認した 1 文を除くと「普段」は 0 か所。"""
        md, _, _ = build()
        rest = md.replace(EI.unanswerable_past_games(25), "")
        self.assertNotIn("普段", rest)
        self.assertEqual(md.count("普段"), EI.unanswerable_past_games(25).count("普段"))

    def test_f63_an_unreached_fact_adds_the_approved_sentence_once(self):
        """優勢後敗は行動の根拠に届かない事実 → 節に「無いものは無いと書きます。」を 1 回。"""
        md, _, _ = build()
        self.assertEqual(md.count(EI.NOTHING_TO_HIDE_SENTENCE), 1)
        s = selection2()
        s["p1"][2] = dict(s["p1"][2], aggregateIds=["time.quickAfterLongThink"], itemRef=ref(1, "h2"))
        t = dict(texts(), **{"p1.3": "長考直後は 9 / 37 でした。"})
        md2, _, _ = build(selection=s, texts=t)
        self.assertNotIn(EI.NOTHING_TO_HIDE_SENTENCE, md2)

    def test_f64_a_draft_without_a_slot_section_falls(self):
        for role_head in ("## ひとことで", "## 局面で見る", "## 試せること", "## 次の 25 局で、何で答え合わせをするか"):
            d = draft_md().replace(role_head, "## べつの節")
            with self.assertRaises(EF.ExitFillError) as cm:
                build(draft_md=d)
            self.assertIn("ちょうど 1 つ", str(cm.exception))

    def test_f65_the_constants_it_adds_are_pinned(self):
        """**⑥ が新しく持つ字は定数に全部ある**(§3 の 3 番。固定文を足す変異はここに現れる)。"""
        self.assertEqual(EF.SLOT_ROLES, ("ひとことで", "局面で見る", "試せること", "答え合わせ"))
        self.assertEqual(EF.VERIFY_TABLE_SEPARATOR, "|---|---|---|")
        self.assertEqual(EF.BOARD_LINE_TEMPLATE_WITHOUT_SIDES, "**{game_no} 局目 {display_ply} 手目**")
        self.assertEqual(EF.INTEGRATION_NAME, "integration.json")
        self.assertEqual(EF.OWN_FLAGS, ("--selection", "--packet", "--request", "--candidates", "--md",
                                        "--out-slot-map", "--seats-dir", "--texts"))


class RunTest(unittest.TestCase):
    """**段としての振る舞い。**書き手の道を消さない。"""

    def test_f66_a_body_without_todo_is_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            md_path = os.path.join(d, "9_本編.md")
            with io.open(md_path, "w", encoding="utf-8") as f:
                f.write("## ひとことで\n\n書き手が書いた本編\n")
            own = {k[2:]: os.path.join(d, k[2:]) for k in EF.OWN_FLAGS}
            own["md"] = md_path
            out = io.StringIO()
            self.assertEqual(EF.run(own, [], out=out), 0)
            self.assertIn("触らずに退く", out.getvalue())
            with io.open(md_path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "## ひとことで\n\n書き手が書いた本編\n")
            self.assertFalse(os.path.exists(own["out-slot-map"]))

    def test_f67_missing_flags_are_named(self):
        with self.assertRaises(EF.ExitFillError) as cm:
            EF.parse_own_args(["--selection", "a", "--md", "b"])
        for flag in ("--packet", "--request", "--candidates", "--out-slot-map", "--seats-dir", "--texts"):
            self.assertIn(flag, str(cm.exception))
        self.assertNotIn("--selection", str(cm.exception))
        own, rest = EF.parse_own_args(["--selection", "a", "--packet", "b", "--request", "c", "--candidates", "d",
                                       "--md", "e", "--out-slot-map", "f", "--seats-dir", "g", "--texts", "h",
                                       "--patient", "p.json"])
        self.assertEqual(rest, ["--patient", "p.json"])
        self.assertEqual(own["seats-dir"], "g")

    def test_f68_a_packet_of_another_id_stops(self):
        """⑤ の `packetId` と packet の封が違えば組まない(違う材料の数を入れない)。"""
        with tempfile.TemporaryDirectory() as d:
            paths = {k[2:]: os.path.join(d, k[2:] + ".json") for k in EF.OWN_FLAGS}
            paths["md"] = os.path.join(d, "9_本編.md")
            with io.open(paths["md"], "w", encoding="utf-8") as f:
                f.write(draft_md())
            for key, value in (("selection", selection2()), ("packet", dict(packet(), packetId="0000000000000000")),
                               ("request", {"customerQuestions": QUESTIONS2}), ("candidates", candidates()),
                               ("texts", texts())):
                with io.open(paths[key], "w", encoding="utf-8") as f:
                    json.dump(value, f, ensure_ascii=False)
            with self.assertRaises(EF.ExitFillError) as cm:
                EF.run(paths, [], out=io.StringIO())
            self.assertIn("packetId", str(cm.exception))
