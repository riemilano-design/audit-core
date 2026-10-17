# -*- coding: utf-8 -*-
u"""次元の診断(docs/XBRL_DIM_DIAG_2026-10-17.md)の門。

**本文の数は `dim_diag_2026-10-17.json` を正本に突き合わせる。**
**「個別を拒否してよい」「次元つきを拒否してよい」へ結論が滑らないことを固定する。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_DIM_DIAG_2026-10-17.md")
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "dim_diag_2026-10-17.json")
CEIL = os.path.join(FX, "ceiling_2026-10-17.json")
SRC = os.path.join(FX, "attr_inject_2026-10-17.json")
POP = (u"基準 24 行", u"席が参照先を出した全部の行", u"正解(T5)の参照先")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p=REC):
    return json.load(io.open(p, encoding="utf-8"))


class RowsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_1_the_six_rows_are_the_ones_the_injection_record_named(self):
        src = rec(SRC)
        want = [(x[u"doc"], x[u"id"]) for x in src["rows"]
                if x[u"露出(注入なし)"][u"別の次元"][u"件数"]]
        got = [(x[u"doc"], x[u"id"]) for x in self.r["rows"]]
        self.assertEqual(got, want)
        self.assertEqual(len(got), 6)

    def test_2_every_row_line_matches_the_record(self):
        for x in self.r["rows"]:
            g = x[u"**競合**"]
            line = u"| `%s` %s | %s %s | **%s** | `%s` | %s | %s |" % (
                x[u"doc"], x[u"id"], u"{:,.0f}".format(x[u"値"]), x[u"単位"],
                g[0][u"分類"], g[0][u"軸と枠"][0][0].split(":")[-1],
                u" / ".join(a[u"軸と枠"][0][1].split(":")[-1] for a in g),
                u"・".join(x[u"**文に在った字**"]) or u"**無し**")
            self.assertIn(line, self.t, (x[u"doc"], x[u"id"]))

    def test_3_the_three_mechanisms_are_two_rows_each(self):
        c = self.r[u"**行の分類**"]
        self.assertEqual(sorted(c), sorted([u"連結・個別の区分", u"セグメント",
                                            u"株主資本の内訳"]))
        self.assertEqual(set(c.values()), {2})
        for k in c:
            self.assertIn(u"| %s | %s%d%s |"
                          % (u"**連結・個別の区分**" if k == u"連結・個別の区分"
                             else k,
                             u"**" if k == u"連結・個別の区分" else u"",
                             c[k], u"**" if k == u"連結・個別の区分" else u""),
                          self.t, k)

    def test_4_all_six_pointers_are_undimensioned(self):
        self.assertEqual([x[u"席の参照先は明示次元つきか"]
                          for x in self.r["rows"]], [False] * 6)
        self.assertIn(u"**露出した 6 行の参照先は 6/6 すべて明示次元なし**", self.t)

    def test_5_no_row_has_a_gold_pointer(self):
        self.assertTrue(all(x[u"正解"] is None for x in self.r["rows"]))
        self.assertTrue(all(x[u"注入か"] is False for x in self.r["rows"]))
        self.assertIn(u"**6 行はいずれも無改変の行で、正解(T5)の参照先が無い。**",
                      self.t)


class PopulationTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        self.p = self.r[u"**参照先に明示次元が付いていたか**"]

    def test_6_populations_total_to_the_known_counts(self):
        self.assertEqual(sorted(self.p), sorted(POP))
        tot = {k: sum(v.values()) for k, v in self.p.items()}
        self.assertEqual(tot[u"基準 24 行"], 24)
        self.assertEqual(tot[u"席が参照先を出した全部の行"], 85)
        self.assertEqual(tot[u"正解(T5)の参照先"], 50)

    def test_7_the_table_numbers_come_from_the_record(self):
        for k in POP:
            v = self.p[k]
            self.assertIn(u"**%d** | %d |" % (v[u"明示次元つき"],
                                              v[u"明示次元なし"]), self.t, k)

    def test_8_a_blanket_rejection_is_reported_as_unusable(self):
        d = self.p[u"正解(T5)の参照先"][u"明示次元つき"]
        self.assertGreater(d, 0)
        self.assertIn(u"**正解そのものが 50 件中 %d 件は明示次元つきである。**" % d,
                      self.t)
        self.assertIn(u"**正解 %d/50 件を落とす。使えない**" % d, self.t)

    def test_9_the_independent_cross_check_holds(self):
        u"""**字で分けた層別**と**軸で分けた数**が同じであること。"""
        st = rec(CEIL)[u"層別"][u"本番(未使用 8)"]
        self.assertEqual(st[u"次元つき"][u"分母"],
                         self.p[u"正解(T5)の参照先"][u"明示次元つき"])
        self.assertEqual(st[u"次元なし"][u"分母"],
                         self.p[u"正解(T5)の参照先"][u"明示次元なし"])
        self.assertIn(u"**別の見方で 13 と 37 が同じになった。**", self.t)


class NonConsolidatedTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        self.b = self.r[u"**候補規則 (b) の帯(規則にはしない)**"]

    def test_10_the_band_is_all_in_nonconsolidated_filers(self):
        n = self.b[u"参照先が個別(NonConsolidated)の枠"]
        self.assertEqual(self.b[u"**うち書類に連結の fact が 0 件(個別しか無い)**"],
                         n)
        self.assertEqual(self.b[u"**うち同じ要素の「次元なし」の枠が無い**"], n)
        self.assertIn(u"| 参照先が個別の枠 | **%d** |" % n, self.t)
        self.assertIn(u"**%d/%d が、連結の fact を 1 件も持たない 2 書類" % (n, n),
                      self.t)

    def test_11_the_two_filers_are_the_records(self):
        nc = sorted(d for d, v in self.r[u"**書類ごとの連結・個別**"].items()
                    if v[u"**個別しか無い書類**"])
        self.assertEqual(len(nc), 2)
        self.assertIn(u"・".join(u"`%s`" % d for d in nc), self.t)
        for d, v in self.r[u"**書類ごとの連結・個別**"].items():
            self.assertEqual(v[u"**個別しか無い書類**"], v[u"連結の要素数"] == 0, d)

    def test_12_rejecting_nonconsolidated_is_reported_as_false_rejection(self):
        n = self.b[u"参照先が個別(NonConsolidated)の枠"]
        self.assertIn(u"**つまり「個別の枠を指したら怪しい」は成り立たない。**", self.t)
        self.assertIn(u"拒否すれば %d 件すべてが誤拒否になる。" % n, self.t)
        self.assertIn(u"**%d 件すべて誤拒否**" % n, self.t)

    def test_13_the_text_rule_is_reported_as_inert(self):
        self.assertEqual(self.b.get(u"**うち文に「連結」が在る(規則 b が当たる)**", 0),
                         0)
        self.assertIn(u"| うち文に「連結」が在る | **0** |", self.t)
        self.assertIn(u"**この標本では 0 件に当たる**", self.t)


class DisclosureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_14_the_dimension_check_is_not_sold_as_closing_the_main_hole(self):
        co = self.r[u"**偶然一致する側の次元(T5 の注入が借りた fact)**"]
        for k, v in co.items():
            self.assertIn(u"| %s | %d |" % (k, v), self.t, k)
        self.assertIn(u"**次元を検査しても、**", self.t.replace("\n", ""))
        self.assertIn(u"要素が違う取り違えは止まらない。**", self.t)

    def test_15_own_defects_are_disclosed_including_the_word_list(self):
        b = self.t[self.t.index(u"## §4"):self.t.index(u"## §5")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. \*\*", b), ["1", "2"])
        self.assertIn(u"`正解[参照先]`", b)
        self.assertIn(u"**第 1 便は「正解の参照先 0 件」になった。**", b)
        self.assertIn(u"**静かに 85 → 70 に落ちていた。**", b)
        self.assertIn(u"**「当事業年度」対「当連結会計年度」**", b)

    def test_16_limits_and_options_are_complete_and_undecided(self):
        lim = self.t[self.t.index(u"## §5"):self.t.index(u"## §6")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", lim),
                         [str(i) for i in range(1, 7)])
        self.assertIn(u"**どの次元差を不一致にするかは決めない。**", lim)
        opt = self.t[self.t.index(u"## §6"):]
        self.assertEqual(re.findall(r"(?m)^\| \((\w)\)", opt),
                         ["a", "b", "c", "d", "e"])
        self.assertIn(u"**どれを採るかは人間が決める。**", opt)
        for bad in (u"採用する", u"を採ることにする", u"直すべきである"):
            self.assertNotIn(bad, self.t, bad)

    def test_17_the_engine_is_declared_untouched(self):
        self.assertIn(u"**読むだけ。engine を変えていない。規則を増やしていない。"
                      u"注入もしていない。0 USD・席は呼んでいない。**", self.t)
        self.assertIn(u"dim_diag_2026-10-17.json", self.t)


if __name__ == "__main__":
    unittest.main()
