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
import exit_index as EI  # noqa: E402
import exit_gate as EG  # noqa: E402


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


# ---- 合成の本編(実物は使わない ― 門は合成で測る) ----
BOARDS = ("13/110 付録3 3 分", "16/93 付録3 3 分", "21/57 付録3 3 分")
# 冒頭の段落(P-162)。**道具と同じ 1 か所から作る**(写さない)。
OPENING = CS.opening_paragraph(20, (("3 分", 20),), "2026-09-29")

# 行動の根拠の分数(P-164 の門が突き合わせる)。**2 本 = 4 人目の実物と同じ本数。**
ACTION_FRACTIONS = [
    {"id": "M4", "label": "攻め", "unit": "局面", "name": "攻めの一致",
     "numerator": 65, "denominator": 107},
    {"id": "M4", "label": "自玉側", "unit": "局面", "name": "自玉側の一致",
     "numerator": 76, "denominator": 132},
]

CANDS = {
    "opening": list(OPENING),
    "actionFractions": list(ACTION_FRACTIONS),
    "p1Numbers": [{"number": n, "unit": "局", "from": "校正用"}
                  for n in (79, 41, 6, 25, 65, 107, 76, 132)],
    "boards": list(BOARDS),
    "menuPassed": ["M3", "M4", "M5"],
}


def md_of(p1=None, p2=None, p3=None, extra=""):
    """通る本編を組み、渡された節だけ差し替える。**節の見出しは `check_structure.SECTIONS` から作る。**"""
    def head(role):
        h, c = next((h, c) for r, h, c in CS.SECTIONS if r == role)
        return h if c is None else f"{h} 20 局で、何で{c}をするか"

    # 既定は**事実 3 本**(正本の形。`HONBUN_P1_FACT_COUNT`)。
    # 既定は**4 人目(18 局版)の型** ― 2 本が行動の根拠の分数、1 本は行動にしないもので、
    # 節に「無いものは無いと書きます。」を置く(P-164 の門が求める形)。
    p1 = ["- 攻めの一致は 65 / 107 でした。",
          "- 自玉側の一致は 76 / 132 でした。",
          "- 崩れ 79 回のうち、中盤が 41 回でした。",
          EI.NOTHING_TO_HIDE_SENTENCE] if p1 is None else p1
    p2 = [f"- この局面です<!-- pos: {BOARDS[0]} -->", f"- この局面です<!-- pos: {BOARDS[1]} -->"] if p2 is None else p2
    p3 = ["1. 試せることがあります<!-- menu: M3 -->"] if p3 is None else p3
    lines = ["# 20 局で起きていたこと", ""] + list(OPENING) + [""]
    for role, body in (("ひとことで", p1), ("局面で見る", p2), ("試せること", p3)):
        lines += [f"## {head(role)}", ""] + list(body) + [""]
    for role in ("答え合わせ", "数え方", "対応表"):
        lines += [f"## {head(role)}", "", "本文です。", ""]
    return "\n".join(lines) + extra


def p1_number_problems(md_text, cands=None):
    """**(ii) の苦情だけ**を返す。

    2026-09-29 に (viii)(p1 が行動に届いているか)を足したので、
    **(ii) の規則を測る試験が (viii) の苦情で落ちるようになった** ―
    片方の門の試験にもう片方の判定を混ぜると、**どちらを測っているのか分からなくなる。**
    """
    return [x for x in problems_of(md_text, cands) if x.startswith("(ii)")]


def problems_of(md_text, cands=None):
    """`check_sentences` 以外の 6 つを回す(あちらは `check_answer.py` の材料が要る)。"""
    cands = CANDS if cands is None else cands
    sections = EG.sections_of(CA.strip_dev_section(md_text))
    problems = []
    EG.check_todo(md_text, problems)
    EG.check_opening(md_text, cands, problems)
    EG.check_p1(sections, cands, problems)
    EG.check_p1_reaches_the_actions(sections, cands, problems)
    EG.check_no_unit_mismatch(md_text, cands, problems)
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
        self.assertIn("20 局", CS.scope_sentence(20))
        self.assertEqual(problems_of(md_of()), [])


class OpeningTest(unittest.TestCase):
    """**(vii) 冒頭の段落の文が 1 文ずつちょうど 1 回**(P-162)。

    2 周目の冊子は冒頭が 1 文だけで、
    **「手の良し悪しを判定するものではありません。」が本編に無いまま顧客に出た。**
    """

    def test_31_every_opening_sentence_is_required(self):
        """**1 文でも消えたら落ちる。**書き手が消せる場所なので、消えたら止まる。"""
        for dropped in OPENING:
            md = md_of().replace(dropped + "\n", "", 1)
            self.assertNotEqual(md, md_of(), f"差し替えが効いていない: {dropped[:20]}")
            problems = problems_of(md)
            hit = [x for x in problems if x.startswith("(vii)")]
            self.assertEqual(len(hit), 1, (dropped[:20], problems))
            self.assertIn("0 か所", hit[0])

    def test_31b_the_heaviest_caveat_is_one_of_them(self):
        """**「手の良し悪しを判定するものではありません。」が段落に在る。**

        これが冒頭の型から落ちると、上の試験は「消したものが落ちる」を測るだけで
        **この 1 文を守らなくなる**(型が正しいことは別に測る)。
        """
        self.assertIn(CS.OPENING_NOT_A_JUDGE, OPENING)
        self.assertIn(CS.OPENING_APPENDIX, OPENING)

    def test_31c_a_doubled_sentence_falls(self):
        """2 回出ても落ちる(古い版と新しい版が混ざるのを防ぐ)。"""
        problems = problems_of(md_of(extra="\n" + CS.OPENING_APPENDIX + "\n"))
        hit = [x for x in problems if x.startswith("(vii)")]
        self.assertEqual(len(hit), 1, problems)
        self.assertIn("2 か所", hit[0])

    def test_31d_a_missing_candidate_list_falls(self):
        """候補の JSON に `opening` が無ければ落ちる(候補の段を回し直す合図)。"""
        cands = {k: v for k, v in CANDS.items() if k != "opening"}
        problems = problems_of(md_of(), cands=cands)
        self.assertTrue(any("opening が無い" in x for x in problems), problems)

    def test_31e_the_gate_reads_the_list_it_is_given(self):
        """**門は自分の一覧を持たない**(候補の JSON が言う文を探す)。

        **ソース全文に `assertNotIn` を当てない** ― この道具の説明文そのものが
        「手の良し悪しを判定するものではありません。」を引いているので、写しの検査は
        **自分の説明文を捕まえる**(同じ日に 4 本続けて踏んだ型)。
        **振る舞いで測る**: 候補の一覧を別の文に替えると、門はその文を探す。
        """
        other = "これは校正用の別の文です。"
        cands = dict(CANDS, opening=[other])
        # 土台の md にはその文が無いので落ちる。
        problems = [x for x in problems_of(md_of(), cands=cands) if x.startswith("(vii)")]
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(other[:20], problems[0])
        # その文を足せば通る ― **門が持っているのは一覧ではなく、突き合わせる手順だけ**。
        problems = [x for x in problems_of(md_of(extra="\n" + other + "\n"), cands=cands)
                    if x.startswith("(vii)")]
        self.assertEqual(problems, [])


class P1ReachesTheActionsTest(unittest.TestCase):
    """**(viii) P1 の事実が行動のページに届いているか**(P-164。2026-09-29)。

    実測: **18 局版は 3 本すべて届いている**(2 本は行動の根拠の分数、1 本は行動にしない理由)。
    **25 局版は 0 本。** 人間の判断「一段上の理由は観測 → 解釈 → 行動のつながり」。
    """

    @staticmethod
    def eight(md):
        return [x for x in problems_of(md) if x.startswith("(viii)")]

    def test_32_the_18_game_shape_passes(self):
        """**2 本が分数・1 本が行動にしないもの + 固定文**は通る(4 人目の型)。"""
        self.assertEqual(self.eight(md_of()), [])

    def test_32b_zero_connected_facts_fall(self):
        """**0 本つながらないと落ちる**(= 2 周目の 25 局版の形)。"""
        md = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 優勢から負けた対局が 6 局ありました。",
                       "- 分かれ道は 25 局にありました。"])
        got = self.eight(md)
        self.assertEqual(len(got), 1, got)
        self.assertIn("3 本", got[0])
        self.assertIn("許されるのは 0 本", got[0])

    def test_32c_one_unconnected_fact_needs_the_sentence(self):
        """**つながらない 1 本は、固定文が節に在るときだけ通る。**"""
        facts = ["- 攻めの一致は 65 / 107 でした。",
                 "- 自玉側の一致は 76 / 132 でした。",
                 "- 崩れ 79 回のうち、中盤が 41 回でした。"]
        # 固定文なし → 落ちる
        got = self.eight(md_of(p1=facts))
        self.assertEqual(len(got), 1, got)
        self.assertIn("1 本", got[0])
        self.assertIn(EI.NOTHING_TO_HIDE_SENTENCE, got[0])
        # 固定文あり → 通る
        self.assertEqual(self.eight(md_of(p1=facts + [EI.NOTHING_TO_HIDE_SENTENCE])), [])

    def test_32d_two_unconnected_facts_fall_even_with_the_sentence(self):
        """**固定文があっても 2 本は通らない**(「行動にしない」は 1 本まで)。"""
        md = md_of(p1=["- 攻めの一致は 65 / 107 でした。",
                       "- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 優勢から負けた対局が 6 局ありました。",
                       EI.NOTHING_TO_HIDE_SENTENCE])
        got = self.eight(md)
        self.assertEqual(len(got), 1, got)
        self.assertIn("2 本", got[0])
        self.assertIn("許されるのは 1 本", got[0])

    def test_32e_both_numbers_of_the_fraction_are_required(self):
        """**分子だけ・分母だけでは「届いた」にしない。**片方だけなら別の話をしている。"""
        for one in ("- 攻めの一致は 65 局面でした。", "- 分かれ道は 107 局面でした。"):
            md = md_of(p1=[one, "- 自玉側の一致は 76 / 132 でした。",
                           "- 崩れ 79 回のうち、中盤が 41 回でした。",
                           EI.NOTHING_TO_HIDE_SENTENCE])
            got = self.eight(md)
            self.assertEqual(len(got), 1, (one, got))
            self.assertIn("2 本", got[0])

    def test_32f_the_gate_reads_the_fractions_it_is_given(self):
        """**門は分数の一覧を持たない**(候補の JSON が言う組を探す)。"""
        cands = dict(CANDS, actionFractions=[
            {"id": "MX", "label": "", "unit": "局面", "name": "別の分数",
             "numerator": 79, "denominator": 41}])
        # 79 / 41 を持つ事実が 1 本あるので、つながらないのは 2 本になる。
        md = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 攻めの一致は 65 / 107 でした。",
                       "- 自玉側の一致は 76 / 132 でした。"])
        got = [x for x in problems_of(md, cands=cands) if x.startswith("(viii)")]
        self.assertEqual(len(got), 1, got)
        self.assertIn("2 本", got[0])

    def test_32g_a_missing_candidate_list_falls(self):
        """候補の JSON に `actionFractions` が無ければ落ちる(候補の段を回し直す合図)。"""
        cands = {k: v for k, v in CANDS.items() if k != "actionFractions"}
        got = [x for x in problems_of(md_of(), cands=cands) if x.startswith("(viii)")]
        self.assertTrue(any("actionFractions が無い" in x for x in got), got)

    def test_32h_zero_actions_means_no_fraction_and_the_sentence_is_the_only_way(self):
        """**行動が 0 本のときは、分数が 1 本も無い** ― 3 本とも落ちる。

        そのときは書き手が `NO_ACTION_SENTENCE` の冊子を作る(行動 0 本の形)。
        **門が「分数が無いから全部通す」形になっていないこと**をここで測る。
        """
        cands = dict(CANDS, actionFractions=[])
        got = [x for x in problems_of(md_of(), cands=cands) if x.startswith("(viii)")]
        self.assertEqual(len(got), 1, got)
        self.assertIn("3 本", got[0])
        self.assertIn("許されるのは 1 本", got[0])


class UnitMismatchTest(unittest.TestCase):
    """**(ix) 単位が違う分数が顧客の本編に残っていないか**(P-165。2026-09-29)。

    顧客に送った 2 周目の冊子に「50 / 137」が出ている ― **分子は局面の数・分母は印の組の数**。
    3 周目は書き手がこの行動を落とすが、**落としを記憶に頼らない。**
    """

    MISMATCH = [{"id": "M6", "numerator": 50, "denominator": 137,
                 "unitMismatch": "分子は局面の数・分母は印の組の数(P-165。人間の承認待ち)"}]

    def test_33_the_pair_left_in_the_honbun_falls(self):
        cands = dict(CANDS, unitMismatchFractions=list(self.MISMATCH))
        md = md_of(p3=["1. 駒を捨てる手を 1 つ入れる<!-- menu: M3 -->　― 根拠は 50 / 137 です"])
        got = [x for x in problems_of(md, cands=cands) if x.startswith("(ix)")]
        self.assertEqual(len(got), 1, got)
        self.assertIn("50 / 137", got[0])
        self.assertIn("P-165", got[0])

    def test_33b_dropping_it_passes(self):
        """**落とせば通る。**門が書き手を止め続ける形になっていないこと。"""
        cands = dict(CANDS, unitMismatchFractions=list(self.MISMATCH))
        self.assertEqual([x for x in problems_of(md_of(), cands=cands) if x.startswith("(ix)")], [])

    def test_33c_no_mismatch_means_nothing_to_check(self):
        """印が付いた分数が無ければ何も言わない(既定の冊子が止まらない)。"""
        self.assertEqual([x for x in problems_of(md_of()) if x.startswith("(ix)")], [])


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
            self.assertNotIn(CS.scope_sentence(20), lines)
            self.assertNotIn("# 20 局で起きていたこと", lines)
        # 節の数は `## ` の数(6)。
        self.assertEqual(len(sections), len(CS.SECTIONS))


class P1Test(unittest.TestCase):
    def test_03_four_facts_fall(self):
        """**4 本目の事実は落ちる。**正本の p1 は事実 3 本(`HONBUN_P1_FACT_COUNT`)。"""
        md = md_of(p1=["- 79 回でした。", "- 41 回でした。", "- 6 局でした。", "- 25 局でした。"])
        found = problems_of(md)
        self.assertTrue(any("ちょうど 3 本" in p for p in found), found)

    def test_04_two_facts_fall(self):
        """**3 本未満も落ちる。**足りないまま進むと p1 が承認済みの形にならない。"""
        md = md_of(p1=["- 79 回でした。", "- 41 回でした。"])
        self.assertTrue(any("ちょうど 3 本" in p for p in problems_of(md)))

    def test_04c_many_values_in_three_facts_pass(self):
        """**1 本の事実が値をいくつ持っていてもよい。**

        これが「異なる値で 3 つ」を撤回した理由(2026-09-29)。人間の線
        「局数で数える・**分母を付ける**」と両立しない ― 「18 局のうち 6 局」だけで既に 2 値。
        **実物 2 件(3 人目の試作・4 人目の本人用 p1)はどちらも値 10 個以上で事実 3 本**だった。
        """
        md = md_of(p1=["- 一度は優勢になった 25 局のうち、負けたのは 6 局でした。",
                       "- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 分かれ道は 41 局面(6 局)ありました。"])
        self.assertEqual(p1_number_problems(md), [])

    def test_04d_a_sentence_outside_the_bullets_is_not_a_fact(self):
        """**箇条書き以外の 1 文は事実として数えない**(実物はどちらも「1 文 + 事実 3 本」)。

        その 1 文の数も候補に在ることは見る ― **部分集合は要求しない。**
        司令塔の提案に入っていたが、**根拠に引かれた実物そのものが落ちる**(3 人目の 1 文は
        「2 局ありました」「97 / 236」を使い、どれも箇条書きに出ていない。実測 2026-09-29)。
        """
        md = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 優勢から負けた対局が 6 局ありました。",
                       "- 分かれ道は 25 局にありました。",
                       "中盤で形勢が動いているという読みです。"])
        self.assertEqual(p1_number_problems(md), [])
        # 1 文の中の数も照合される(候補に無ければ落ちる)。
        md2 = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                        "- 優勢から負けた対局が 6 局ありました。",
                        "- 分かれ道は 25 局にありました。",
                        "4321 回という読みです。"])
        self.assertTrue(any("4321" in p and "候補に無い" in p for p in problems_of(md2)))

    def test_05_a_number_not_in_the_candidates_falls(self):
        """**候補に無い数は落ちる。**書き手が材料に無い数を作った場合。"""
        md = md_of(p1=["- 79 回でした。", "- 41 回でした。", "- 4321 回でした。"])
        found = problems_of(md)
        self.assertTrue(any("4321" in p and "候補に無い" in p for p in found), found)

    def test_06_a_single_digit_number_is_counted(self):
        """**1 桁の数も照合する。**実物の p1 は「6 局」を含む ―
        `check_answer.py` の既定(9 以下は単独では見ない)をそのまま使うと、
        **1 桁の、候補に無い数が黙って通る。**`small_max=0` を渡している理由がこれ。
        """
        md = md_of(p1=["- 79 回でした。", "- 41 回でした。", "- 6 局と 7 局でした。"])
        found = problems_of(md)
        self.assertTrue(any("7" in p and "候補に無い" in p for p in found), found)
        self.assertFalse(any("数 6 が候補に無い" in p for p in found), found)

    def test_07_repeating_a_number_is_allowed(self):
        """**同じ数を何度書いてもよい。**照合は「候補に在るか」だけを見る。"""
        md = md_of(p1=["- 崩れ 79 回のうち、中盤が 41 回でした。",
                       "- 優勢から負けた対局が 6 局ありました。",
                       "- 79 回のうち中盤が多い形でした。"])
        self.assertEqual(p1_number_problems(md), [])

    def test_08_the_ordered_item_marker_is_not_a_number(self):
        """**番号つき箇条書きの頭は数ではない。**「1. 」を照合にかけると候補に無い数として落ちる。"""
        self.assertEqual(EG.number_claims(["11. 崩れ 79 回でした。"]), [79])

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

    def test_10b_three_facts_are_required_even_with_the_right_numbers(self):
        """**数が全部候補に在っても、事実が 3 本でなければ落ちる**(2 つの検査は独立)。"""
        md = md_of(p1=["- 79 回と 41 回と 6 局と 25 局でした。"])
        found = problems_of(md)
        self.assertTrue(any("ちょうど 3 本" in p for p in found), found)
        self.assertFalse(any("候補に無い" in p for p in found), found)

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
        """**下書きだけの節が 1 つでも残れば落ちる**(5 つとも別々に確かめる)。

        本数を固定で書いてある理由: **節を足したときにこの試験を通ることを強制する**
        (足した節が (vi) に入っていなければ、顧客の冊子に下書きの節が残る)。
        """
        self.assertEqual(len(EC.DRAFT_ONLY_HEADINGS), 5)
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
        self.assertIn("HONBUN_P1_FACT_COUNT", used)
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

    def test_28b_the_fact_count_itself_is_a_candidate(self):
        """**「数は 3 つ。」の 3 が候補に在ること。**

        実物(3 人目の試作の「ひとことで」の 1 文)がこの言い方をしている。
        候補に入れない作りにしたら、**実物と同じ言い方をした書き手が門で止まった**
        (実測 2026-09-29: 本番の下書きで残った問題はこの 1 件だけだった)。
        **これは対局の事実ではなく冊子の形の数**なので `from` にそう書いてある。
        """
        patient = {"summary": {"games": 20}, "games": [{}] * 20, "findings": []}
        repro = {"totalPositions": 100, "totalGames": 20, "rows": []}
        rows = EC.p1_numbers(patient, repro)
        shape = [r for r in rows if r["number"] == CS.HONBUN_P1_FACT_COUNT and r["unit"] == "本"]
        self.assertEqual(len(shape), 1, rows)
        self.assertIn("正本", shape[0]["from"])

    def test_29_a_single_digit_finding_number_is_a_candidate(self):
        """**1 桁の数が候補に入ること**(実物の 6 局が通ること)。"""
        patient = {"summary": {"games": 20}, "games": [{}] * 20,
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


class DraftOnlySectionsAreNotCountedTest(unittest.TestCase):
    """**(vi) が削除を求めている節の数に、(ii) が苦情を言わない**(2026-09-29。実物で出た)。

    実物で「数 5 が候補に無い」「数 2 が候補に無い」が出た ― どちらも下書きだけの見出し
    (「候補 1: 発見(材料が出した 5 種類)」「候補 2: 同じ型が何局で起きたか」)の中の数字だった。
    **書き手の一覧に、消せば消える苦情を混ぜない。**
    """

    def test_30_lines_inside_a_draft_only_section_are_dropped(self):
        lines = ["- 一度は優勢になった 18 局のうち 6 局。",
                 EC.DRAFT_ONLY_HEADINGS[0],
                 "- 崩れ 79 回のうち中盤 41 回。",
                 "## 次の節"]
        kept = EG.without_draft_only(lines)
        self.assertIn("- 一度は優勢になった 18 局のうち 6 局。", kept)
        self.assertNotIn("- 崩れ 79 回のうち中盤 41 回。", kept)
        self.assertNotIn(EC.DRAFT_ONLY_HEADINGS[0], kept)
        # **次の見出しで拾い直す**(節の外に出たら落とさない)
        self.assertIn("## 次の節", kept)

    def test_30b_a_number_only_inside_a_draft_only_section_is_not_a_problem(self):
        cands = {"p1Numbers": [{"number": 3}, {"number": 18}, {"number": 6}]}
        # **事実の行に数を入れない**(入れるとその数の苦情が出て、測りたいものが見えない)。
        sections = [("ひとことで", ["- 一度は優勢になった 18 局のうち 6 局。",
                                    "- ふたつ目の事実。", "- みつ目の事実。",
                                    EC.DRAFT_ONLY_HEADINGS[1],
                                    "- 候補の中の 97 / 236。"])]
        problems = []
        EG.check_p1(sections, cands, problems)
        self.assertEqual([p for p in problems if "97" in p or "236" in p], [])
        # **見出しそのものの数にも苦情を言わない**(見出しを落とさないと「数 2」が出る。
        # 2026-09-29 に変異で実測 ― 見出しを残す変異が黙っていた)
        self.assertEqual([p for p in problems if "数 2 " in p], [], problems)

    def test_30c_a_number_outside_is_still_a_problem(self):
        """**外の数は今までどおり止める**(緩めていないことの裏)。"""
        cands = {"p1Numbers": [{"number": 3}, {"number": 18}, {"number": 6}]}
        sections = [("ひとことで", ["- 一度は優勢になった 18 局のうち 6 局。",
                                    "- 97 / 236 でした。", "- 3 本目。"])]
        problems = []
        EG.check_p1(sections, cands, problems)
        self.assertTrue([p for p in problems if "97" in p], problems)

    def test_30d_the_headings_come_from_the_candidates_tool(self):
        """**見出しの一覧は写さない**(`exit_candidates` が正本)。"""
        src = read_text(os.path.join(HERE, "exit_gate.py"))
        self.assertIn("EC.DRAFT_ONLY_HEADINGS", src)
        for h in EC.DRAFT_ONLY_HEADINGS:
            self.assertNotIn(h, src)
if __name__ == "__main__":
    unittest.main(verbosity=2)
