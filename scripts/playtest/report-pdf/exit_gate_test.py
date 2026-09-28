# -*- coding: utf-8 -*-
# 段 `exit-gate` の検査(`exit_gate.py`)の試験。
#
# 【この門の危ない所】**見落とす側に倒れること。**
# 「3 つ選べた」と言って 4 つ目の数を通す・候補に無い盤を通す・下限に届かなかった行動を通す・
# 下書きの注が付いたまま顧客の PDF を作る。**どれも黙って進む**ので、ここで赤にする。
#
# 【組版を回さない】この道具は md の文字と候補の JSON だけを見るので、
# **reportlab も材料の JSON も要らない**(`check_sentences` だけが `check_answer.py` に委ね、
# あちらは `check_answer.py` 側の試験で測っている)。
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
import exit_gate as EG  # noqa: E402


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


# ---- 合成の本編(実物は使わない ― 門は合成で測る) ----
BOARDS = ("13/110 付録3 3 分", "16/93 付録3 3 分", "21/57 付録3 3 分")
CANDS = {
    "p1Numbers": [{"number": n, "unit": "局", "from": "校正用"} for n in (79, 41, 6, 25)],
    "boards": list(BOARDS),
    "menuPassed": ["M3", "M4", "M5"],
}


def md_of(p1=None, p2=None, p3=None, extra=""):
    """通る本編を組み、渡された節だけ差し替える。**節の見出しは `check_structure.SECTIONS` から作る。**"""
    def head(role):
        h, c = next((h, c) for r, h, c in CS.SECTIONS if r == role)
        return h if c is None else f"{h} 20 局で、何で{c}をするか"

    p1 = ["- 崩れ 79 回のうち、中盤が 41 回でした。", "- 優勢から負けた対局が 6 局ありました。"] if p1 is None else p1
    p2 = [f"- この局面です<!-- pos: {BOARDS[0]} -->", f"- この局面です<!-- pos: {BOARDS[1]} -->"] if p2 is None else p2
    p3 = ["1. 試せることがあります<!-- menu: M3 -->"] if p3 is None else p3
    lines = ["# 20 局で起きていたこと", "", CS.SCOPE_SENTENCE, ""]
    for role, body in (("ひとことで", p1), ("局面で見る", p2), ("試せること", p3)):
        lines += [f"## {head(role)}", ""] + list(body) + [""]
    for role in ("答え合わせ", "数え方", "対応表"):
        lines += [f"## {head(role)}", "", "本文です。", ""]
    return "\n".join(lines) + extra


def problems_of(md_text, cands=None):
    """`check_sentences` 以外の 5 つを回す(あちらは `check_answer.py` の材料が要る)。"""
    cands = CANDS if cands is None else cands
    sections = EG.sections_of(CA.strip_dev_section(md_text))
    problems = []
    EG.check_todo(md_text, problems)
    EG.check_p1(sections, cands, problems)
    EG.check_p2(sections, cands, problems)
    EG.check_p3(sections, cands, problems)
    EG.check_draft_leftovers(md_text, problems)
    return problems


class PassesTest(unittest.TestCase):
    def test_01_a_finished_honbun_passes(self):
        """**選び終わった本編は通る。**通らなければ門が書き手を止め続ける(道具の不具合)。"""
        self.assertEqual(problems_of(md_of()), [])

    def test_02_the_scope_sentence_number_is_not_counted(self):
        """**商品の範囲の 1 段落の「20 局」は数に入らない。**

        あの段落は最初の `## ` より前にあり、**書き手が選んだ数ではない**(正本 §1 の固定文)。
        節の中だけを数える作りでここが守られる ― 入ってしまうと、まともな本編が必ず 4 つになる。
        """
        self.assertIn("20 局", CS.SCOPE_SENTENCE)
        self.assertEqual(problems_of(md_of()), [])


class SectionsTest(unittest.TestCase):
    def test_02b_the_preamble_belongs_to_no_section(self):
        """**最初の `## ` より前の行は、どの節にも入らない。**

        表題(`# `)と商品の範囲の 1 段落がそこに在る。`# ` でも割る作りにすると
        **その段落が節の中身になり、まともな本編の数が必ず 1 つ増える。**
        「通る本編が通る」では測れなかった(校正で実測 2026-09-29 ― 順序に救われて緑だった)ので、
        **割り方そのものを測る。**
        """
        sections = EG.sections_of(md_of())
        for _heading, lines in sections:
            self.assertNotIn(CS.SCOPE_SENTENCE, lines)
            self.assertNotIn("# 20 局で起きていたこと", lines)
        # 節の数は `## ` の数(6)。
        self.assertEqual(len(sections), len(CS.SECTIONS))


class P1Test(unittest.TestCase):
    def test_03_four_numbers_fall(self):
        """**4 つ目の数は落ちる。**「ちょうど 3 つ」を通す門でないと器が崩れる。"""
        md = md_of(p1=["- 79 回・41 回・6 局・25 局の 4 つを書きました。"])
        self.assertTrue(any("ちょうど 3 個" in p for p in problems_of(md)))

    def test_04_two_numbers_fall(self):
        """**3 つ未満も落ちる。**足りないまま進むと p1 が承認済みの形にならない。"""
        md = md_of(p1=["- 79 回と 41 回でした。"])
        self.assertTrue(any("ちょうど 3 個" in p for p in problems_of(md)))

    def test_05_a_number_not_in_the_candidates_falls(self):
        """**候補に無い数は落ちる。**書き手が材料に無い数を作った場合。"""
        md = md_of(p1=["- 79 回・41 回・4321 回でした。"])
        found = problems_of(md)
        self.assertTrue(any("4321" in p and "候補に無い" in p for p in found), found)

    def test_06_a_single_digit_number_is_counted(self):
        """**1 桁の数も数える。**実物の p1 は「6 局」を含む ―
        `check_answer.py` の既定(9 以下は単独では見ない)をそのまま使うと、
        **1 桁の 4 つ目が黙って通る。**`small_max=0` を渡している理由がこれ。
        """
        md = md_of(p1=["- 79 回・41 回・6 局・7 局の 4 つ。"])
        found = problems_of(md)
        self.assertTrue(any("ちょうど 3 個" in p for p in found), found)
        self.assertTrue(any("7" in p and "候補に無い" in p for p in found), found)

    def test_07_repeating_a_number_is_allowed(self):
        """**同じ数を 2 回書いても 1 つと数える。**

        「ひとことで」の 1 文が上の数をもう一度使うのは自然な書き方で、
        **出た回数で数えるとまともな文が落ちる。**異なる値で数える理由がこれ。
        """
        md = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 優勢から負けた対局が 6 局ありました。",
                       "- 79 回のうち中盤が多いという読みです。"])
        self.assertEqual(problems_of(md), [])

    def test_08_the_ordered_item_marker_is_not_a_number(self):
        """**番号つき箇条書きの頭は数ではない。**「1. 」を数えると本数が狂う。"""
        md = md_of(p1=["1. 崩れ 79 回のうち、中盤が 41 回でした。",
                       "2. 優勢から負けた対局が 6 局ありました。"])
        self.assertEqual(problems_of(md), [])

    def test_09_the_menu_mark_number_is_not_a_number(self):
        """**行動の印の中の数(`M3` の 3)は数ではない。**

        `check_answer.py` 側はこれを 9 以下として見ていないだけなので、
        上限 0 で数えるこちらは**自分で外す**(あちらは触っていない)。

        **`number_claims` に直接当てる。**「P3 に印がある本編が通る」で測ろうとしたが、
        `number_claims` は P1 の節にしか当たらないので**外す処理を消しても緑だった**
        (校正で実測 2026-09-29)。**関数の約束を直接測る。**
        """
        self.assertEqual(EG.number_claims(["1. 試せます<!-- menu: M3 -->"]), [])
        self.assertEqual(EG.number_claims(["- 12 回<!-- menu: M10 -->"]), [12])
        md = md_of(p3=["1. 試せることがあります<!-- menu: M3 -->"])
        self.assertEqual(problems_of(md), [])

    def test_10_the_count_falls_without_p1_numbers_in_the_json(self):
        """**候補の JSON に `p1Numbers` が無ければ落ちる。**

        古い JSON(候補の段を回し直していない)で門が黙る道を閉じる。
        """
        cands = {k: v for k, v in CANDS.items() if k != "p1Numbers"}
        self.assertTrue(any("p1Numbers" in p for p in problems_of(md_of(), cands)))

    def test_11_a_missing_section_falls(self):
        """**節が無ければ落ちる。**器の門より先に、書き手の席で気づける。"""
        md = md_of().replace("## ひとことで", "## 見出しを消した")
        self.assertTrue(any("「ひとことで」の節が無い" in p for p in problems_of(md)))


class P2Test(unittest.TestCase):
    def test_12_three_boards_fall(self):
        """**盤はちょうど 2 つ**(正本 §1。本数は `check_structure.BOARD_COUNT` が正本)。"""
        md = md_of(p2=[f"- 盤<!-- pos: {b} -->" for b in BOARDS])
        found = problems_of(md)
        self.assertEqual(CS.BOARD_COUNT, 2)
        self.assertTrue(any(f"ちょうど {CS.BOARD_COUNT} 個" in p for p in found), found)

    def test_13_a_board_not_in_the_candidates_falls(self):
        """**候補に無い盤は落ちる。**候補の一覧は md に印字したものと同じなので、
        「下書きに出ていなかった局面」を書き手が作った状態。
        """
        md = md_of(p2=[f"- 盤<!-- pos: {BOARDS[0]} -->", "- 盤<!-- pos: 99/1 付録3 3 分 -->"])
        found = problems_of(md)
        self.assertTrue(any("99/1" in p and "候補に無い" in p for p in found), found)

    def test_14_spacing_in_the_mark_does_not_matter(self):
        """**印の中の空白の詰め方で落ちない。**組のラベルに空白が入る(「3 分」)ので、
        空白を消すのではなく 1 つに詰めて比べる。書き手が空白を増やしただけで落ちるのは道具の不具合。

        **印の「中」の空白で測る。**最初は `<!-- pos:  13/110 … -->` のように**外側**を空けて書いたが、
        あれは `POS_TAG_RE` 自身が落としていて、**詰める処理を外しても緑だった**(校正で実測 2026-09-29)。
        """
        inner = BOARDS[0].replace(" 付録3", "  付録3")
        self.assertNotEqual(inner, BOARDS[0])
        md = md_of(p2=[f"- 盤<!-- pos: {inner} -->", f"- 盤<!-- pos: {BOARDS[1]} -->"])
        self.assertEqual(problems_of(md), [])

    def test_15_a_board_outside_the_section_is_not_counted(self):
        """**他の節の印は P2 の数に入らない。**

        本編は付録 1 の局面も指しうる(別の節で)。そこまで数えると「ちょうど 2 つ」が崩れる。
        """
        md = md_of() + "\n## 追加の節\n\n- 別の節の盤<!-- pos: 21/57 付録3 3 分 -->\n"
        self.assertEqual(problems_of(md), [])


class P3Test(unittest.TestCase):
    def test_16_an_action_that_did_not_pass_the_minimum_falls(self):
        """**下限に届かなかった行動は落ちる。**

        承認済みの表の「条件 → 行動」の下限を通っていない行動を顧客に出す道を閉じる。
        """
        md = md_of(p3=["1. 試せます<!-- menu: M1 -->"])
        found = problems_of(md)
        self.assertTrue(any("M1" in p and "下限を通っていない" in p for p in found), found)

    def test_17_no_action_at_all_falls(self):
        """**行動が 0 本は落ちる。**「試せること」の節が空のまま進む道を閉じる。"""
        md = md_of(p3=["本文だけ書いて印を付けていません。"])
        self.assertTrue(any("1 つも無い" in p for p in problems_of(md)))

    def test_18_several_passing_actions_are_allowed(self):
        """**本数は書き手が決める。**下限を通った候補の中であれば何本でもよい(仕様 §1)。"""
        md = md_of(p3=[f"{i}. 試せます<!-- menu: {m} -->" for i, m in enumerate(CANDS["menuPassed"], 1)])
        self.assertEqual(problems_of(md), [])


class LeftoverTest(unittest.TestCase):
    def test_19_a_todo_falls(self):
        """**選ぶ場所が残っていれば止まる**(`prose-gate`・`answer-gate` と同型)。"""
        md = md_of(p1=[EC.TODO])
        self.assertTrue(any("選ぶ場所が" in p for p in problems_of(md)))

    def test_20_a_todo_in_the_dev_section_also_falls(self):
        """**書いた側の記録の節に残った `TODO` でも止まる。**

        顧客には見えないが「まだ選んでいない」ことは変わらない。
        `strip_dev_section` を通した側で見ると、**ここが黙る。**
        """
        md = md_of() + f"\n## 書いた側の記録(顧客には見せない)\n\n{EC.TODO}\n"
        self.assertNotIn(EC.TODO, CA.strip_dev_section(md))
        self.assertTrue(any("選ぶ場所が" in p for p in problems_of(md)))

    def test_21_each_draft_only_heading_falls(self):
        """**下書きだけの節が 1 つでも残れば落ちる**(4 つとも別々に確かめる)。"""
        self.assertEqual(len(EC.DRAFT_ONLY_HEADINGS), 4)
        for heading in EC.DRAFT_ONLY_HEADINGS:
            md = md_of() + f"\n{heading}\n\n中身\n"
            found = problems_of(md)
            self.assertTrue(any(heading in p for p in found), (heading, found))

    def test_22_a_note_to_the_writer_falls(self):
        """**書き手への注が残れば落ちる。**注は顧客の PDF には出ないが、
        **出ないから良い話ではない** ― 残っているのは選び終えていない印である。
        """
        md = md_of() + "\n" + EC.note("ここに残すのは 3 つだけ") + "\n"
        self.assertTrue(any("書き手への注" in p for p in problems_of(md)))


class NoOwnRulesTest(unittest.TestCase):
    """**門が自分で判定・文言・本数を作っていないこと。**"""

    def test_23_the_counts_come_from_check_structure(self):
        """本数は `check_structure.py` の定数を**呼んで**いること(数字を書いていない)。

        ソースに裸の「3」「2」があるかを見るのではなく、**`CS.` 経由で読んでいる行**を見る
        (説明文の中の数字を捕まえないため ― 2026-09-29 に 5 回踏んだ型)。
        """
        tree = ast.parse(read_text(os.path.join(HERE, "exit_gate.py")))
        used = set()
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "CS"):
                used.add(node.attr)
        self.assertIn("HONBUN_P1_NUMBER_COUNT", used)
        self.assertIn("BOARD_COUNT", used)
        self.assertIn("heading_matches", used)

    def test_24_the_number_rule_is_check_answers(self):
        """数の拾い方は `check_answer.scan_numbers` を呼んでいること。

        **自分で `re.finditer(r"\\d+")` を書いていたら、規則が 2 か所になる。**
        `exit_gate.py` の関数の本文だけを見る(説明文は除く)。
        """
        tree = ast.parse(read_text(os.path.join(HERE, "exit_gate.py")))
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                value = node.func.value
                if isinstance(value, ast.Name):
                    calls.add(f"{value.id}.{node.func.attr}")
        self.assertIn("CA.scan_numbers", calls)
        digit_res = [n.args[0].value for n in ast.walk(tree)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "compile" and n.args
                     and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)]
        # 番号つき箇条書きの頭を外す 1 本だけは自前(数を拾う規則ではない)。
        self.assertEqual(digit_res, [EG.ORDERED_ITEM_RE.pattern], digit_res)

    def test_25_the_draft_headings_come_from_the_writer_side(self):
        """下書きだけの見出しは `exit_candidates.py` から読んでいること(写していない)。"""
        src = read_text(os.path.join(HERE, "exit_gate.py"))
        for heading in EC.DRAFT_ONLY_HEADINGS:
            self.assertNotIn(heading, src, f"見出しを写している: {heading}")
        self.assertIn("EC.DRAFT_ONLY_HEADINGS", src)


class SameLimitOnBothSidesTest(unittest.TestCase):
    def test_28_the_candidate_list_uses_the_same_limit_as_the_gate(self):
        """**候補を作る側と数える側が同じ上限を使っていること。**

        実測で踏んだ(2026-09-29): 候補の側が既定(9 以下は単独では見ない)で拾い、
        門が上限 0 で数えていたため、**「6 局が候補に無い」でまともな選択が止まった**
        (3 人目の実物の p1 は aheadLossGames = 6 を使っている)。
         が  を渡していることを AST で見る。
        """
        tree = ast.parse(read_text(os.path.join(HERE, "exit_candidates.py")))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "p1_numbers")
        limits = [kw.value.value for n in ast.walk(fn)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                  and n.func.attr == "scan_numbers"
                  for kw in n.keywords if kw.arg == "small_max"]
        self.assertEqual(limits, [0], f"候補の側の上限が門と違う: {limits}")

    def test_29_a_single_digit_finding_number_is_a_candidate(self):
        """**1 桁の数が候補に入ること**(実物の 6 局が通ること)。"""
        patient = {"games": [{}] * 20,
                   "findings": [{"kind": "aheadLoss",
                                 "text": "一度は優勢(+300 以上)になった後に負けた対局が 6 局ありました"}]}
        repro = {"totalPositions": 100, "totalGames": 20, "rows": []}
        numbers = {x["number"] for x in EC.p1_numbers(patient, repro)}
        self.assertIn(6, numbers, sorted(numbers))


class ScanNumbersTest(unittest.TestCase):
    def test_26_the_default_limit_is_unchanged(self):
        """**`check_answer.py` の既定は動かしていない。**

        引数を足しただけで、渡さなければ検査 1 と同じ(9 以下は単独では拾わない)。
        ここが動くと、既に納品した冊子を検査した結果が変わる。
        """
        _ratio, _fr, _pc, plains = CA.scan_numbers("7 と 12 があります")
        self.assertEqual(plains, [12])
        _ratio, _fr, _pc, plains0 = CA.scan_numbers("7 と 12 があります", small_max=0)
        self.assertEqual(plains0, [7, 12])

    def test_27_a_fraction_gives_both_sides(self):
        """分数は**左右の両方**を数に入れる(片方だけ照合すると、もう片方に何でも書ける)。"""
        claims = EG.number_claims(["- 68 局のうち 5 局でした。"])
        self.assertEqual(set(claims), {68, 5})


if __name__ == "__main__":
    unittest.main(verbosity=2)
