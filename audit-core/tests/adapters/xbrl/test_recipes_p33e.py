# -*- coding: utf-8 -*-
"""P33E(表の見出しの「前期」の列の数を前期の手がかりがある数として扱う T)の試験。封 docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md §1。

P33E = P32E + 旗 ``table_period_2026_11_09``。既定 P27 は不変(``DEFAULT_PROFILE`` = P27)。

* 表: 文の列で、``strip()`` が ``|`` で始まる文の連なり(途中に ``|`` で始まらない文が来たら切れる)。連なりの最初の文が見出し。
* 見出しのセルの種類 ``_table_head_kind_2026_11_09``: 「比・増減・率・差」の字があれば None。前期の語だけなら "prior"、当期の語だけなら "current"、他は None。
  見出しが使えるのは「前期」がちょうど 1 列・「当期」が 1 列以下のときだけ。
* 前期の列の数 ``_table_prior_keys_2026_11_09``: セルの数が見出しと同じ行で、``s[:a].count("|") - 1`` が前期の列の番号の数の (文の字, a) の集合。
* 効き方: ``_prior_cue`` と ``_prior_cue_window_2026_11_06`` の先頭で、(s, a) が集合(``_TABLE_PRIOR_SET_2026_11_09``)にあれば真。
  集合は ``_build_raw_num_claims`` の入口で毎回空にし、旗が真のときだけ埋める。

**各挙動について「P33E で効く」と「P32E では従来どおり」を対にして留める。** 合成の instance(同じ要素の CurrentYear と Prior1Year)で
``_build_raw_num_claims`` を呼ぶ。通信しない。
"""
import dataclasses
import inspect
import unittest

from adapters.xbrl import extract as E
from adapters.xbrl import recipes as R
from adapters.xbrl import vocabulary as V

CUR = "CurrentYearDuration"
PRI = "Prior1YearDuration"
SEAL = "docs/XBRL_TABLE_PERIOD_ENGINE_SEAL_2026-11-09.md"
FLAG = "table_period_2026_11_09"
SET = R._TABLE_PRIOR_SET_2026_11_09
HEAD = "| 項目 | 当期 | 前期 | 増減 |"
ROW = "| 売上高 | 120億円 | 100億円 | +20.0% |"
ROW_SWAP = "| 売上高 | 120億円 | 120億円 | +20.0% |"


def fact(name, ctx, value):
    return {"name": "jppfs_cor:" + name, "context": ctx, "unit": "JPY", "value": float(value)}


#: 当期 120 億円・前期 100 億円の売上高。
FACTS = [fact("NetSales", CUR, 12000000000), fact("NetSales", PRI, 10000000000)]
CTXS = {f["context"]: {"members": []} for f in FACTS}


def claims(profile_name, text):
    """``text``(``\\n`` で区切った表)を本番の文の切り方で割り、``_build_raw_num_claims`` の claim の列を返す。"""
    sents = E.split_sentences(text, True)
    return R._build_raw_num_claims(sents, FACTS, CTXS, V.PROFILES[profile_name], lambda si, pos: (None, "t"))


def pick(cl, sentence_index, value):
    """文の番号と値で claim を 1 つだけ選ぶ(0 個・2 個以上なら赤)。"""
    got = [c for c in cl if c["sentence"] == sentence_index and c["value"] == float(value)]
    assert len(got) == 1, (sentence_index, value, [(c["sentence"], c["value"]) for c in cl])
    return got[0]


def view(c):
    return (c["result"], c["pointer"], c["recomputed"], c["reason"], c["bound"], c["form"])


def ptr(ctx):
    return "xbrl:jppfs_cor:NetSales@" + ctx


def keys_of(profile_name, text):
    return R._table_prior_keys_2026_11_09(E.split_sentences(text, True), V.PROFILES[profile_name])


def a_of(sentence, number):
    """エンジンの数の読み(``_numbers_of``)が返す、``number`` で始まる数の位置 a(直前の空白を含む)。"""
    got = [a for (a, b, *_rest) in R._numbers_of(V.P33E, sentence) if sentence[a:b].strip().startswith(number)]
    assert len(got) == 1, (sentence, number, got)
    return got[0]


class ProfileTest(unittest.TestCase):
    def test_p33e_is_p32e_plus_exactly_the_one_flag(self):
        self.assertEqual(dataclasses.replace(V.P32E, name="P33E", **{FLAG: True}), V.P33E)
        self.assertIs(V.PROFILES["P33E"], V.P33E)
        self.assertEqual("P33E", V.P33E.name)

    def test_the_flag_is_true_only_in_p33e(self):
        self.assertTrue(getattr(V.P33E, FLAG))
        self.assertEqual(["P33E"], sorted(n for n, p in V.PROFILES.items() if getattr(p, FLAG)))
        for n in ("P32E", "P30E", "P29E", "P29", "P28E", "P28", "P27E", "P27C", "P27", "P26", "P24", "P22", "P1"):
            self.assertFalse(getattr(V.PROFILES[n], FLAG), n)

    def test_the_flag_defaults_to_false(self):
        names = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertFalse(dataclasses.fields(V.Profile)[names.index(FLAG)].default)

    def test_p31_p31e_and_p33_are_not_made(self):
        for n in ("P31", "P31E", "P33"):
            self.assertNotIn(n, V.PROFILES)

    def test_the_default_profile_is_still_p27(self):
        self.assertEqual("P27", V.DEFAULT_PROFILE)

    def test_the_flag_field_sits_right_after_prior_cue_bind(self):
        names = [f.name for f in dataclasses.fields(V.Profile)]
        self.assertEqual(names.index("prior_cue_bind_2026_11_06") + 1, names.index(FLAG))

    def test_p33e_keeps_the_p32e_flags(self):
        self.assertTrue(V.P33E.prior_cue_bind_2026_11_06)
        self.assertTrue(V.P33E.rounding_mixed_2026_11_04)

    def test_the_seal_is_named_in_the_engine(self):
        for f in (R._table_head_kind_2026_11_09, R._table_prior_keys_2026_11_09):
            self.assertIn(SEAL, inspect.getsource(f))
        self.assertEqual(1, inspect.getsource(R._prior_cue).count(SEAL))
        self.assertEqual(1, inspect.getsource(R._prior_cue_window_2026_11_06).count(SEAL))
        self.assertEqual(1, inspect.getsource(R._build_raw_num_claims).count(SEAL))


class HeadKindTest(unittest.TestCase):
    """見出しのセルの種類。"""

    k = staticmethod(R._table_head_kind_2026_11_09)

    def test_prior_words(self):
        for c in (" 前期 ", "前連結会計年度", "前事業年度", "前年度", "前年同期", "前年", "前期(2025年3月期)"):
            self.assertEqual("prior", self.k(c), c)

    def test_current_words(self):
        for c in (" 当期 ", "当連結会計年度", "当事業年度", "当年度", "当中間", "今期", "当期(2026年3月期)"):
            self.assertEqual("current", self.k(c), c)

    def test_cells_with_ratio_or_change_words_have_no_kind(self):
        for c in ("前年同期比", "前期比", "前期増減", "前期差", "前期増減率", "当期比", "当期の増減", "当期率", "当期差額", "前年比"):
            self.assertIsNone(self.k(c), c)

    def test_other_cells_have_no_kind(self):
        for c in ("項目", " ", "", "2026年3月期", "2025年3月期", "金額"):
            self.assertIsNone(self.k(c), c)

    def test_a_cell_with_both_a_prior_and_a_current_word_has_no_kind(self):
        self.assertIsNone(self.k("当期・前期"))


class KeysTest(unittest.TestCase):
    """前期の列の数の (文の字, 位置) の集合。"""

    def test_the_prior_column_number_only(self):
        want = {(ROW, a_of(ROW, "100億円"))}
        self.assertEqual(want, keys_of("P33E", HEAD + "\n" + ROW))

    def test_the_column_number_is_not_shifted(self):
        # 前期が最初の列(番号 0)・真ん中・最後の列の 3 つ。
        t1 = "| 前期 | 当期 |\n| 100億円 | 120億円 |"
        s = E.split_sentences(t1, True)[1]
        self.assertEqual({(s, a_of(s, "100億円"))}, keys_of("P33E", t1))
        t2 = "| 項目 | 前期 | 当期 |\n| 売上高 | 100億円 | 120億円 |"
        s = E.split_sentences(t2, True)[1]
        self.assertEqual({(s, a_of(s, "100億円"))}, keys_of("P33E", t2))
        t3 = "| 項目 | 増減 | 当期 | 前期 |\n| 売上高 | +20億円 | 120億円 | 100億円 |"
        s = E.split_sentences(t3, True)[1]
        self.assertEqual({(s, a_of(s, "100億円"))}, keys_of("P33E", t3))

    def test_a_table_without_a_current_column_is_used(self):
        # 「当期」は 1 列以下(0 列でもよい)。
        t = "| 項目 | 前期 |\n| 売上高 | 100億円 |"
        s = E.split_sentences(t, True)[1]
        self.assertEqual({(s, a_of(s, "100億円"))}, keys_of("P33E", t))

    def test_every_following_row_is_used(self):
        r2 = "| 営業利益 | 12億円 | 10億円 | +20.0% |"
        t = HEAD + "\n" + ROW + "\n" + r2
        self.assertEqual({(ROW, a_of(ROW, "100億円")), (r2, a_of(r2, "10億円"))}, keys_of("P33E", t))

    def test_two_prior_columns_make_the_table_unusable(self):
        t = "| 項目 | 当期 | 前期 | 前々期は前年 |\n" + "| 売上高 | 120億円 | 100億円 | 90億円 |"
        self.assertEqual(set(), keys_of("P33E", t))

    def test_zero_prior_columns_make_the_table_unusable(self):
        self.assertEqual(set(), keys_of("P33E", "| 項目 | 当期 | 増減 |\n| 売上高 | 120億円 | +20億円 |"))

    def test_two_current_columns_make_the_table_unusable(self):
        t = "| 項目 | 当期 | 当中間 | 前期 |\n| 売上高 | 120億円 | 60億円 | 100億円 |"
        self.assertEqual(set(), keys_of("P33E", t))

    def test_year_only_head_is_unusable(self):
        t = "| 項目 | 2026年3月期 | 2025年3月期 |\n| 売上高 | 120億円 | 100億円 |"
        self.assertEqual(set(), keys_of("P33E", t))

    def test_year_over_year_head_is_unusable(self):
        t = "| 項目 | 当期 | 前年同期比 |\n| 売上高 | 120億円 | 120.0% |"
        self.assertEqual(set(), keys_of("P33E", t))

    def test_a_row_with_a_different_cell_count_is_not_used(self):
        short = "| 売上高 | 120億円 | 100億円 |"
        long_ = "| 売上高 | 120億円 | 100億円 | +20.0% | 備考 |"
        self.assertEqual(set(), keys_of("P33E", HEAD + "\n" + short))
        self.assertEqual(set(), keys_of("P33E", HEAD + "\n" + long_))
        # 他の行は使われる。
        self.assertEqual({(ROW, a_of(ROW, "100億円"))}, keys_of("P33E", HEAD + "\n" + short + "\n" + ROW + "\n" + long_))

    def test_sentences_that_are_not_a_table_are_not_used(self):
        self.assertEqual(set(), keys_of("P33E", "売上高は前期の100億円でした。"))
        self.assertEqual(set(), keys_of("P33E", ROW.replace("|", "／")))

    def test_a_sentence_without_a_pipe_cuts_the_table(self):
        # 切れた後の最初の | の行が新しい見出し(この行は期の語を持たないので使えない)。
        t = HEAD + "\n説明の文です。\n" + ROW
        self.assertEqual(set(), keys_of("P33E", t))
        # 切れた後に新しい見出しが来れば、その表が使われる。
        t2 = HEAD + "\n説明の文です。\n| 項目 | 前期 | 当期 |\n| 売上高 | 100億円 | 120億円 |"
        s = E.split_sentences(t2, True)[3]
        self.assertEqual({(s, a_of(s, "100億円"))}, keys_of("P33E", t2))

    def test_the_head_row_itself_is_not_used(self):
        # 見出しの「前期」のセルに数(100億円)を持たせる。見出しも走査する変異(最初の文の後の continue を外す)では、この数が集合に入って赤になる
        # (測定の便 2026-11-09 の監査の指摘 2: 以前の入力は見出しの数が年(2025年)で、見出しを走査しても数が読まれず変異が黙った)。
        t = "| 項目 | 当期 | 前期(100億円) |\n| 売上高 | 120億円 | 100億円 |"
        head, row = E.split_sentences(t, True)
        self.assertGreaterEqual(len(R._numbers_of(V.P33E, head)), 1)                      # 前提: 見出しの数が読まれる(走査すれば拾える入力)
        got = keys_of("P33E", t)
        self.assertEqual({(row, a_of(row, "100億円"))}, got)
        for s, a in got:
            self.assertNotIn("項目", s)

    def test_only_the_prior_column_not_the_current_or_the_diff(self):
        got = keys_of("P33E", HEAD + "\n" + ROW)
        self.assertNotIn((ROW, a_of(ROW, "120億円")), got)
        self.assertNotIn((ROW, a_of(ROW, "20.0%")), got)

    def test_two_separate_tables_are_both_read(self):
        t = HEAD + "\n" + ROW + "\n本文です。\n| 項目 | 前期 | 当期 |\n| 利益 | 10億円 | 12億円 |"
        got = keys_of("P33E", t)
        self.assertEqual(2, len(got))

    def test_a_leading_double_bar_and_a_trailing_empty_cell_shift_the_column_by_one(self):
        """**いまの振る舞いを字で留める(直さない)。** engine のセルの割り方は ``strip().strip("|").split("|")``(``s.strip("|")`` は連なった ``|`` を全部除く)で、
        封 §1 の 1 の字「``strip()`` の両端の ``|`` を除いて ``|`` で割った字」(両端の ``|`` を 1 つずつ除く読み)より広い。先頭が ``||``(先頭の空セル)で、末尾にも空セルがある行
        (例 ``|| 売上高 | 120億円 | 120億円 | |``)は、先頭の ``||`` が丸ごと除かれて末尾の空セルが残り、セルの数は見出しと同じ 4 になるが、列の番号は 1 つずれる
        (``s[:a].count("|") - 1`` は先頭の ``||`` を 2 つ数える)。このとき**当期の列(見出しから見て 2 番目のセル)の数が前期の列の番号に当たり、前期の fact に結ばれる**。
        封の字どおり(両端の ``|`` を 1 つずつ除く読み)なら先頭の空セル・末尾の空セルを含めて 5 セルで見出しの 4 と合わず、行は使われない。
        この読みの違いは測定の便の監査(2026-11-09)の指摘 1。200 本の AI の文に ``||`` は 0 件・97 書類に表は 0 なので記録の数には届かない。**次の改訂で直す候補**
        (直すときはこの試験を新しい振る舞いに書き替える)。"""
        row = "|| 売上高 | 120億円 | 120億円 | |"
        t = HEAD + "\n" + row
        sents = E.split_sentences(t, True)
        self.assertEqual(row, sents[1])
        pos = sorted(a for (a, _b, *_rest) in R._numbers_of(V.P33E, row))
        self.assertEqual(2, len(pos))
        self.assertEqual(4, len(row.strip("|").split("|")))                                  # セルの数は見出し(4)と同じ
        # いまの振る舞い: 1 つ目の数(真の当期の列)だけが前期の列として集合に入る。2 つ目(真の前期の列)は入らない。
        self.assertEqual({(row, pos[0])}, keys_of("P33E", t))
        # 効き方: 1 つ目の数は、P32E は当期の fact に GROUNDED、P33E は前期の fact を名指して VALUE_MISMATCH。2 つ目は両方とも当期の fact に GROUNDED で同じ。
        got32 = sorted((c for c in claims("P32E", t) if c["sentence"] == 1 and c["value"] == 120e8), key=lambda c: c["pos"])
        got33 = sorted((c for c in claims("P33E", t) if c["sentence"] == 1 and c["value"] == 120e8), key=lambda c: c["pos"])
        self.assertEqual(2, len(got32))
        self.assertEqual(2, len(got33))
        self.assertEqual(("GROUNDED", ptr(CUR)), (got32[0]["result"], got32[0]["pointer"]))
        self.assertEqual(("VALUE_MISMATCH", ptr(PRI)), (got33[0]["result"], got33[0]["pointer"]))
        self.assertEqual(view(got32[1]), view(got33[1]))
        self.assertEqual(("GROUNDED", ptr(CUR)), (got33[1]["result"], got33[1]["pointer"]))


class BehaviorTest(unittest.TestCase):
    """表の前期の列の数は、前期の手がかりがある数と同じに扱う。"""

    def setUp(self):
        SET.clear()

    def tearDown(self):
        SET.clear()

    def test_a_prior_value_in_the_prior_column(self):
        t = HEAD + "\n" + ROW
        p32 = pick(claims("P32E", t), 1, 100e8)
        p33 = pick(claims("P33E", t), 1, 100e8)
        # P32E: 当期の fact を名指して VALUE_MISMATCH(前期の正しい数を「値が違う」と言う)。
        self.assertEqual(("VALUE_MISMATCH", ptr(CUR), 12000000000.0), (p32["result"], p32["pointer"], p32["recomputed"]))
        # P33E: 前期の fact に GROUNDED。
        self.assertEqual(("GROUNDED", ptr(PRI), 10000000000.0), (p33["result"], p33["pointer"], p33["recomputed"]))

    def test_the_current_value_in_the_prior_column(self):
        t = HEAD + "\n" + ROW_SWAP
        got33 = [c for c in claims("P33E", t) if c["sentence"] == 1 and c["value"] == 120e8]
        got32 = [c for c in claims("P32E", t) if c["sentence"] == 1 and c["value"] == 120e8]
        self.assertEqual(2, len(got32))
        self.assertEqual(2, len(got33))
        # 前期の列(2 つ目)の「120億円」: P32E は当期の fact に GROUNDED(通す)、P33E は前期の fact を名指して VALUE_MISMATCH。
        self.assertEqual(("GROUNDED", ptr(CUR), 12000000000.0), (got32[1]["result"], got32[1]["pointer"], got32[1]["recomputed"]))
        self.assertEqual(("VALUE_MISMATCH", ptr(PRI), 10000000000.0), (got33[1]["result"], got33[1]["pointer"], got33[1]["recomputed"]))
        # 当期の列(1 つ目)は同じ。
        self.assertEqual(view(got32[0]), view(got33[0]))

    def test_the_current_and_the_diff_columns_are_the_same(self):
        t = HEAD + "\n" + ROW
        c32, c33 = claims("P32E", t), claims("P33E", t)
        self.assertEqual(len(c32), len(c33))
        for x, y in zip(c32, c33):
            if x["sentence"] == 1 and x["value"] == 100e8:
                continue          # 前期の列の数だけは動く
            self.assertEqual(x, y)

    def test_only_the_prior_column_claim_moves(self):
        t = HEAD + "\n" + ROW + "\n| 営業利益 | 12億円 | 10億円 | +20.0% |"
        c32, c33 = claims("P32E", t), claims("P33E", t)
        moved = [(x["sentence"], x["value"]) for x, y in zip(c32, c33) if x != y]
        self.assertEqual([(1, 100e8)], moved)       # 営業利益の行の数は、売上高の fact と合わず UNVERIFIABLE 等のまま(動かない)

    def test_unused_heads_are_the_same(self):
        for t in ("| 項目 | 2026年3月期 | 2025年3月期 |\n" + ROW,
                  "| 項目 | 当期 | 前年同期比 |\n| 売上高 | 120億円 | 100億円 |",
                  "| 項目 | 当期 | 前期 | 前々期は前年 |\n| 売上高 | 120億円 | 100億円 | 90億円 |",
                  "| 項目 | 前期 | 前年度 | 当期 |\n| 売上高 | 100億円 | 100億円 | 120億円 |"):
            self.assertEqual(claims("P32E", t), claims("P33E", t), t)

    def test_a_row_with_a_different_cell_count_is_the_same(self):
        t = HEAD + "\n| 売上高 | 120億円 | 100億円 |"
        self.assertEqual(claims("P32E", t), claims("P33E", t))

    def test_a_sentence_that_is_not_a_table_is_the_same(self):
        for t in ("売上高は120億円で、前期の100億円から増加しました。", "売上高は100億円でした。", "売上高は前期は100億円でした。"):
            self.assertEqual(claims("P32E", t), claims("P33E", t), t)

    def test_the_head_alone_changes_nothing(self):
        self.assertEqual(claims("P32E", HEAD), claims("P33E", HEAD))

    def test_the_flag_false_profiles_keep_the_old_behavior(self):
        t = HEAD + "\n" + ROW
        for n in ("P32E", "P30E", "P29E", "P28E", "P27E", "P27"):
            c = pick(claims(n, t), 1, 100e8)
            self.assertEqual(ptr(CUR), c["pointer"], n)         # 当期の fact を名指す(今までどおり)
            self.assertEqual("VALUE_MISMATCH", c["result"], n)
            self.assertEqual(set(), SET, n)                      # 旗が偽なら集合は埋まらない
        t2 = HEAD + "\n" + ROW_SWAP
        for n in ("P32E", "P30E"):
            got = [c for c in claims(n, t2) if c["sentence"] == 1 and c["value"] == 120e8]
            self.assertEqual("GROUNDED", got[1]["result"], n)
            self.assertEqual(ptr(CUR), got[1]["pointer"], n)

    def test_the_set_does_not_remain_between_calls(self):
        t = HEAD + "\n" + ROW
        before = claims("P32E", t)
        claims("P33E", t)
        self.assertNotEqual(set(), SET)                # P33E の後は、その呼び出しの分が残っている(次の呼び出しの入口で空にする)
        after = claims("P32E", t)
        self.assertEqual(set(), SET)                   # P32E の入口で空になった
        self.assertEqual(before, after)                # P33E の後に P32E を呼んだ出力が、P33E を呼ぶ前と同じ
        # 別の文でも残らない(同じ字の文だけでなく、(文の字, 位置)が違えば効かない)。
        c = pick(claims("P32E", "売上高は100億円でした。"), 0, 100e8)
        self.assertEqual("VALUE_MISMATCH", c["result"])

    def test_a_second_p33e_call_with_other_sentences_replaces_the_set(self):
        claims("P33E", HEAD + "\n" + ROW)
        c = claims("P33E", "売上高は100億円でした。")
        self.assertEqual(set(), SET)
        self.assertEqual(ptr(CUR), pick(c, 0, 100e8)["pointer"])


class CueWiringTest(unittest.TestCase):
    """集合にある (s, a) は、``_prior_cue`` と ``_prior_cue_window_2026_11_06`` の両方が真を返す(封 §1 の 4)。"""

    S = "| 売上高 | 120億円 | 100億円 |"

    def setUp(self):
        SET.clear()

    def tearDown(self):
        SET.clear()

    def test_without_the_set_neither_function_is_true(self):
        a = a_of(self.S, "100億円")
        self.assertFalse(R._prior_cue(self.S, a))
        self.assertFalse(R._prior_cue_window_2026_11_06(self.S, a))

    def test_prior_cue_is_true_for_a_key_in_the_set(self):
        a = a_of(self.S, "100億円")
        SET.add((self.S, a))
        self.assertTrue(R._prior_cue(self.S, a))
        self.assertTrue(R._prior_cue(self.S, a, a + 5))
        self.assertFalse(R._prior_cue(self.S, a_of(self.S, "120億円")))
        self.assertFalse(R._prior_cue(self.S + " ", a))                   # 文の字が違えば効かない

    def test_the_window_function_is_true_for_a_key_in_the_set(self):
        a = a_of(self.S, "100億円")
        SET.add((self.S, a))
        self.assertTrue(R._prior_cue_window_2026_11_06(self.S, a))
        self.assertFalse(R._prior_cue_window_2026_11_06(self.S, a_of(self.S, "120億円")))
        self.assertFalse(R._prior_cue_window_2026_11_06(self.S + " ", a))

    def test_the_old_windows_are_kept(self):
        s = "売上高は前期の5,000千円です"
        self.assertTrue(R._prior_cue(s, s.index("5,000")))
        self.assertTrue(R._prior_cue_window_2026_11_06(s, s.index("5,000")))
        s2 = "売上高は5,000千円から999千円へ"
        self.assertTrue(R._prior_cue(s2, 4, 4 + len("5,000千円")))
        self.assertFalse(R._prior_cue_window_2026_11_06(s2, 4))


class PbBindingTest(unittest.TestCase):
    """PB の縛り(前期の fact を名指して VALUE_MISMATCH)も表の前期の列の数に効く。"""

    def test_a_value_matching_no_prior_fact_names_the_prior_fact(self):
        t = HEAD + "\n| 売上高 | 120億円 | 999億円 | +20.0% |"
        p32 = pick(claims("P32E", t), 1, 999e8)
        p33 = pick(claims("P33E", t), 1, 999e8)
        self.assertEqual("VALUE_MISMATCH", p33["result"])
        self.assertEqual(ptr(PRI), p33["pointer"])
        self.assertEqual(10000000000.0, p33["recomputed"])
        self.assertTrue(p33["bound"])
        self.assertIsNone(p32["result"])                         # P32E は何にも結ばない(当期の fact にも前期の fact にも)
        self.assertIsNone(p32["pointer"])


if __name__ == "__main__":
    unittest.main()
