# -*- coding: utf-8 -*-
"""P-1 出どころの確認(docs/DOMAIN1_SAIIRU_P1_2026-10-16.md)を固定する。

守るのは 8 つ。
  1. 記録の数が**その場の実測と一致**する(表題 19・2 行にまたがる 16・目次 19)
  2. **会計の集合が歳出側と完全に一致**すること(実測)
  3. **列の集合がほぼ交わらない**こと ― 共通の名前は `予算現額` だけ(実測)
  4. 明細 歳入の階層が **款・項・目・節**(歳出より 1 段深い)
  5. **6e の 0 件は「除いた形」つきで記録されている**(表題 19+19 を除いた上での 0)
  6. 文書が**数を出さない段**であると宣言していること(P-2 以降と混ぜない)
  7. **`予算現額` は 6a で落ちる見込み**が先に書かれていること
  8. 私の 3 つの誤り(`['v']`・表題 1 行・見出し 2 行丸ごと)が記録に在ること
"""
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
REC = os.path.join(ROOT, "fixtures", "sheet", "sainyuu_p1_2026-10-16.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SAIIRU_P1_2026-10-16.md")
SRC = os.path.join(MEASURE, "sheet_sainyuu_p1_2026-10-16.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


_C = {}


def live():
    """**記録ではなく、いま実物を読んで作り直す。**"""
    if "r" in _C:
        return _C["r"]
    sp = importlib.util.spec_from_file_location("p1_live", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    sk, _ = m.read(m.SAINYUU)
    sm, _ = m.read(m.MEISAI_SAINYUU)
    _C["r"] = (m, m.kessan_sainyuu(sk), m.meisai_sainyuu(sm))
    return _C["r"]


class LiveStructureTest(unittest.TestCase):
    def setUp(self):
        self.m, self.k, self.me = live()
        self.rec = load(REC)

    def test_1_titles_and_accounts(self):
        self.assertEqual(self.k["title_rows_loose"], 19)
        self.assertEqual(self.k["title_rows_identified"], 19)
        self.assertEqual(self.k["titles_spanning_two_rows"], 16)
        self.assertEqual(self.k["titles_not_identified"], [])
        self.assertEqual(self.rec["kessan_sainyuu"]["title_rows_identified"], 19)
        self.assertEqual(self.rec["kessan_sainyuu"]["titles_spanning_two_rows"], 16)

    def test_2_account_sets_match_saisyutu(self):
        """**その場で比べる。**記録の `same_set` を読むだけでは、比較を
        `True` に固定する変異が黙る(2026-10-16 の変異 P6 で実測)。"""
        a = self.m.account_sets(self.k)
        self.assertEqual(a, self.rec["account_sets"], "記録が実測と違う")
        self.assertTrue(a["same_set"], "会計の集合が歳出と違う")
        self.assertEqual(a["only_in_sainyuu"], [])
        self.assertEqual(a["only_in_saisyutu"], [])
        self.assertEqual(len(a["sainyuu"]), 19)
        self.assertEqual(sorted(self.k["accounts"]and
                                [self.m.norm(x) for x in self.k["accounts"]]),
                         a["sainyuu"])

    def test_3_only_one_shared_column_name(self):
        c = self.m.column_sets(self.k)
        self.assertEqual(c, self.rec["column_sets"], "記録が実測と違う")
        self.assertEqual(c["shared_names"], ["予算現額"],
                         "共通の列名が `予算現額` だけではない")
        for want in ("調定額", "収入済額", "不納欠損額", "収入未済額"):
            self.assertIn(want, c["sainyuu(決算書 歳入)"], want)
            self.assertNotIn(want, c["saisyutu(決算書 歳出)"], want)
        for want in ("支出済額", "不用額", "翌年度繰越額"):
            self.assertNotIn(want, c["sainyuu(決算書 歳入)"], want)

    def test_4_meisai_has_one_more_level(self):
        self.assertEqual(self.me["levels_in_header"], ["款", "項", "目", "節"])
        self.assertEqual(self.me["toc_entries"], 19)
        self.assertEqual(self.me["sheet_count"], 20)

    def test_5_the_header_extraction_drops_row_content(self):
        """**見出しに行の中身を混ぜない。**最初に書いた版は `01`・`都税` を拾った。

        **その場で測る** ― 記録を読むだけでは、階層の列を外す枝を消す変異が黙る。
        """
        cols = self.m.value_columns(self.k)
        for bad in ("01", "都税", "円", "款", "項"):
            self.assertNotIn(bad, cols, bad)
        self.assertEqual(cols, self.rec["column_sets"]["sainyuu(決算書 歳入)"])


class RestatementZeroIsAccountableTest(unittest.TestCase):
    """**0 件には除いた形を添える。**でないと自分の絞り込みが作った 0 になる。"""

    def setUp(self):
        self.rec = load(REC)
        self.r6 = self.rec["restatement_6e"]

    def test_6_zero_hits_with_excluded_titles_counted(self):
        self.assertEqual(self.r6["hits_kessan"], 0)
        self.assertEqual(self.r6["hits_meisai"], 0)
        self.assertEqual(self.r6["excluded_kessan"], 19)
        self.assertEqual(self.r6["excluded_meisai"], 19)
        self.assertEqual(self.r6["excluded_form"],
                         ["歳入歳出決算書", "歳入歳出決算事項別明細書"])

    def test_7_the_scan_would_find_a_real_reference(self):
        """**歯。**作った「再掲」のセルを食わせたら拾うこと。"""
        m, _, _ = live()
        fake = {"A1": {"value": "款の額は歳出に同じ(再掲)"},
                "A2": {"value": "令和６年度東京都一般会計歳入歳出決算書"}}
        hit, excluded = m.cross_references(fake)
        self.assertEqual(len(hit), 1, hit)
        self.assertEqual(len(excluded), 1, excluded)

    def test_8_notes_do_not_reference_saisyutu(self):
        """**その場で拾う。**記録を読むだけでは、注記を拾わない変異が黙る。"""
        m, k_live, _ = live()
        k = k_live["notes"]
        self.assertEqual(k, self.rec["kessan_sainyuu"]["notes"],
                         "記録の注記が実測と違う")
        self.assertTrue(k, "注記が 1 件も取れていない(読み方の欠陥かもしれない)")
        self.assertTrue(any("還付未済金" in n["text"] for n in k))
        for n in k:
            self.assertNotIn("再掲", n["text"])


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.rec = load(REC)

    def test_9_the_doc_declares_it_produces_no_counts(self):
        self.assertIn("**この段では数を出さない。**", self.t)
        self.assertIn("「P-1 を飛ばして数を数えた」は失敗条件", self.t)
        self.assertIn("**独立した裏づけの本数・3 本に達する会計の数は出さない。**",
                      self.rec["what_this_step_does_not_do"])

    def test_10_numbers_in_the_doc_match_the_record(self):
        k = self.rec["kessan_sainyuu"]
        self.assertIn("**会計の表題を %d 件同定した。**" % k["title_rows_identified"],
                      self.t)
        self.assertIn("**ただし %d 件のうち %d 件は表題が 2 行にまたがっていた。**"
                      % (k["title_rows_identified"], k["titles_spanning_two_rows"]),
                      self.t)
        self.assertIn("| 再掲・参照(**書類の表題を除く**) | 決算書 **%d 件** / 明細 **%d 件** |"
                      % (self.rec["restatement_6e"]["hits_kessan"],
                         self.rec["restatement_6e"]["hits_meisai"]), self.t)
        self.assertIn("| **除いた「書類の表題」** | 決算書 **%d 件** / 明細 **%d 件** |"
                      % (self.rec["restatement_6e"]["excluded_kessan"],
                         self.rec["restatement_6e"]["excluded_meisai"]), self.t)

    def test_11_the_shared_column_is_flagged_for_6a(self):
        self.assertIn("**名前が共通の列** | **`予算現額` だけ**", self.t)
        self.assertIn("**歳入の予算現額が歳出の予算現額と等しい可能性が高い。**", self.t)
        self.assertIn("等しければ **6a で落ちる**", self.t)
        self.assertIn("**これは P-2 で測る。**", self.t)

    def test_12_the_verdict_is_not_overstated(self):
        self.assertIn("**歳入側の 2 冊は、歳出側の 2 冊の再掲ではない。**", self.t)
        self.assertIn("**ただしこれは「独立した証拠になる」という結論ではない。**", self.t)
        self.assertIn("**まだ測っていない。**", self.t)

    def test_13_my_three_errors_are_recorded(self):
        block = self.t.split("## §4")[1].split("## §5")[0]
        self.assertIn("`['v']`", block)
        self.assertIn("**19 件のうち 3 件しか同定できず", block)
        self.assertIn("zero-count-may-be-my-own-bug", block)
        rows = re.findall(r"^\| .+ \| .+ \| .+ \|$", block, re.M)
        # 見出しの 1 行 + 誤り 3 件(`|---|` の区切りはこの正規表現に当たらない)
        self.assertEqual(len(rows), 4, rows)


class TeethTest(unittest.TestCase):
    """**判定に歯が在ること。**変異が黙った 2 本を調べて足した門。"""

    def setUp(self):
        self.m, self.k, self.me = live()

    def test_14_header_cols_does_not_look_past_the_next_row(self):
        """**見出しは `科目` の行とその次の行だけ。**2 つ先は行の中身である。

        最初に書いた版は 2 行先まで拾い、列の集合に `01`・`都税` が混ざった。
        壊した入力を食わせて、**2 つ先が入らないこと**を確かめる。
        """
        rows = {5: {"A": "科目", "D": "予算現額"},
                6: {"A": "款", "B": "項"},
                7: {"A": "01", "B": "都税"}}      # ここは行の中身
        head, cols = self.m.header_cols(rows)
        self.assertEqual(head, 5)
        got = {c["text"] for c in cols}
        self.assertIn("予算現額", got)
        self.assertNotIn("都税", got, "**2 つ先の行の中身を見出しに拾っている**")
        self.assertEqual(self.m.value_columns({"header_cells": cols}), ["予算現額"])

    def test_15_the_level_col_skip_is_equivalent_on_this_material(self):
        """**階層の列を外す枝は、この材料では結果を変えない**(測って確かめた)。

        外さないと `款`・`項` が余分に入るが、`value_columns` が名前で落とすので
        **値の列の集合は同じ**になる。だから変異 P2 が黙るのは**同値**であり穴ではない。
        **2 つ先の行まで広げたら同値でなくなる**ので、そちらは `test_14` が守る。
        """
        rows = self.m.cells_by_row(
            self.m.read(self.m.SAINYUU)[0]["歳入"]["cells"])
        _, with_skip = self.m.header_cols(rows)
        _, without = self.m.header_cols(rows, level_cols=())
        extra = {c["text"] for c in without} - {c["text"] for c in with_skip}
        self.assertEqual(sorted(extra), ["款", "項"], sorted(extra))
        self.assertEqual(self.m.value_columns({"header_cells": with_skip}),
                         self.m.value_columns({"header_cells": without}))

    def test_16_account_sets_can_say_no(self):
        """**歯。**会計の集合がずれたら `same_set` が偽になること。

        記録と突き合わせるだけでは、`same_set` を `True` に固定する変異が黙る
        (2026-10-16 の変異 P6 で実測)。
        """
        real = self.m.account_sets(self.k)
        self.assertTrue(real["same_set"])
        short = self.m.account_sets({"accounts": self.k["accounts"][:-1]})
        self.assertFalse(short["same_set"], "1 件落としても真になっている")
        self.assertEqual(len(short["only_in_saisyutu"]), 1)
        extra = self.m.account_sets(
            {"accounts": list(self.k["accounts"]) + ["にせの会計"]})
        self.assertFalse(extra["same_set"])
        self.assertEqual(extra["only_in_sainyuu"], ["にせの会計"])


if __name__ == "__main__":
    unittest.main()
