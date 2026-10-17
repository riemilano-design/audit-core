# -*- coding: utf-8 -*-
"""結果(docs/XBRL_CD_RESULT_2026-10-17.md)の門。

**本文の数は記録 `score_2026-10-17.json` を正本に突き合わせる。**
**判定が「上回った」に書き換えられないことを固定する。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_CD_RESULT_2026-10-17.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "score_2026-10-17.json")
ANS = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "seat_answers")
TOKENS = (110811, 112185, 118752, 140998, 142437, 146289, 156426, 157811)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


class VerdictTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_1_both_z_failed_and_the_doc_says_so(self):
        v = self.r[u"**主比較の判定**"]
        self.assertFalse(v[u"Z-1 誤認定が減った"])
        self.assertFalse(v[u"Z-2 正しい特定が増えた"])
        self.assertIn(u"支持されない", v[u"判定"])
        self.assertIn(u"**Z-1(C′ の誤認定は A より少ない): 外れ。**", self.t)
        self.assertIn(u"**Z-2(C′ の正しい特定は A より多い): 外れ。**", self.t)
        self.assertIn(u"**判定: この標本では、LLM + Core が LLM 単体を上回ることは"
                      u"支持されない。**", self.t)
        self.assertIn(u"**基準は変えない。**", self.t)

    def test_2_the_headline_table_matches_the_record(self):
        plain = self.t.replace("**", "")
        for arm in ("A", "C′", "D′", "D″"):
            v = self.r[u"採点"][arm]
            w, i = v[u"誤認定"], v[u"正しい参照先の特定"]
            self.assertIn(u"%s%%(%d/%d)" % (w[u"率"], w[u"分子"],
                                            w[u"分母(参照先を出した件)"]), plain,
                          u"%s の誤認定が本文と違う" % arm)
            self.assertIn(u"%s%%(%d/%d)" % (i[u"率"], i[u"分子"],
                                            i[u"分母(T5 の件)"]), plain,
                          u"%s の特定が本文と違う" % arm)
            fa = v[u"偽警報(**判定には使わない**)"]
            self.assertIn(u"%s%%(%d/%d)" % (fa[u"率"], fa[u"分子"],
                                            fa[u"分母(無改変の件)"]), plain,
                          u"%s の偽警報が本文と違う" % arm)

    def test_3_no_row_was_missing_and_the_arms_agree(self):
        self.assertEqual(set(self.r[u"**欠けは 4 腕で同数**"].values()), {0})
        self.assertEqual(self.r[u"行の合計"], 192)
        self.assertIn(u"**0 件**(8 書類すべて 24/24 行)", self.t)
        self.assertEqual(len([f for f in os.listdir(ANS)
                             if f.endswith("_answer.json")]), 8)


class WhyTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_4_core_never_got_a_turn_on_t5(self):
        rows = self.r["rows"]
        t5 = [r for r in rows if (r[u"正解"] or {}).get(u"種類") == u"参照先が在る"]
        abstained = [r for r in t5 if r[u"席"][u"判定"] == u"判定できない"]
        self.assertEqual(len(abstained), 0, "T5 で席が迷った行が在る")
        self.assertIn(u"**T5(Core が強い層)50 行のうち、席が `判定できない` だった行** "
                      u"| **0** |", self.t)
        self.assertIn(u"Core には出番が 1 行も無かった。**", self.t)
        added = [r for r in rows if r[u"腕"]["C′"].get(u"足した")]
        self.assertEqual(len(added), 98)
        self.assertIn(u"**C′ が照合器を足した 98 行で Core が言ったこと** | "
                      u"**全部 `判定できない`**", self.t)

    def test_5_value_search_is_reported_as_harmful(self):
        fa = {a: self.r[u"採点"][a][u"偽警報(**判定には使わない**)"][u"分子"]
              for a in ("A", "C′", "D′", "D″")}
        self.assertEqual(fa["A"], fa["C′"], "A と C′ の偽警報が違う")
        self.assertGreater(fa["D′"], fa["A"] * 10)
        self.assertIn(u"**Core を足した C′ は偽警報を 1 件も増やしていない。**", self.t)
        self.assertIn(u"**買い手にとっての差は「改善」ではなく「壊さないこと」だった。**",
                      self.t)

    def test_6_predictions_are_tallied_with_the_bias_named(self):
        b = self.t[self.t.index(u"## §2-3"):self.t.index(u"## §2-4")]
        ids = re.findall(r"(?m)^\| \*{0,2}(Z-\d|X-\d+)\*{0,2} \|", b)
        self.assertEqual(ids[:2], ["Z-1", "Z-2"])
        self.assertEqual(len([i for i in ids if i.startswith("X-")]), 10)
        self.assertIn(u"**当たり 3 / 外れ 8 / 未測定 1。**", b)
        self.assertIn(u"predict-then-tally-my-bias", b)
        self.assertIn(u"**未測定**", b)

    def test_7_cost_is_reported_with_tokens_and_no_single_usd_claim(self):
        b = self.t[self.t.index(u"## §2-4"):]
        self.assertIn(u"**{:,}**".format(sum(TOKENS)), b)
        self.assertIn(u"**再生成 0**", b)
        self.assertIn(u"**USD は私から見えない。**", b)
        for usd in ("16.29", "3.04", "4.56"):
            self.assertIn(usd, b, usd)
        self.assertIn(u"推定を実測として扱わない", b)


class LimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_8_seven_limits_and_the_core_claim_is_not_overreached(self):
        b = self.t[self.t.index(u"## §3-2"):self.t.index(u"## §3-3")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 8)], u"限界は 7 本")
        self.assertIn(u"**Core に価値が無いことの証明ではない。**", b)
        self.assertIn(u"**封はその役を与えていない**", b)
        self.assertIn(u"**その能力が使われる場面が 0 行だった**", b)

    def test_9_next_steps_are_three_and_not_decided_by_me(self):
        b = self.t[self.t.index(u"## §3-3"):]
        ids = re.findall(r"(?m)^\| \*{0,2}\((α|β|γ)\)\*{0,2} \|", b)
        self.assertEqual(ids, ["α", "β", "γ"])
        self.assertIn(u"**この便の結果で封を変えない。**", b)
        self.assertIn(u"**人間の判断**", b)
        self.assertIn(u"測るまで「改善する」と書かない。**", b)


class CeilingAddendumTest(unittest.TestCase):
    """§8 の追記。**数は `ceiling_2026-10-17.json` を正本に突き合わせる。**"""

    def setUp(self):
        self.t = text(DOC)
        self.c = json.load(io.open(
            os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                         "ceiling_2026-10-17.json"), encoding="utf-8"))

    @staticmethod
    def _pct(v):
        return u"%s%%(%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])

    def test_10_the_addendum_is_dated_and_keeps_the_body(self):
        self.assertIn(u"## §8 追記(2026-10-17・α の封を書く前に)", self.t)
        self.assertIn(u"**本文(§1〜§7)は 1 文字も直していない。**", self.t)
        self.assertIn(u"**0 USD。席は呼んでいない。**", self.t)
        self.assertIn(u"ceiling_2026-10-17.json", self.t)

    def test_11_population_numbers_come_from_the_record(self):
        o = self.c[u"α が検査できる母集団"]
        for k in (u"席が参照先を名指した行", u"うち Core に主張が対応した行",
                  u"うち正解が固定できる行(T5)", u"無改変で名指した行"):
            self.assertIn(u"**%d**" % o[k], self.t, k)
        self.assertEqual(o[u"席が参照先を名指した行"], 85)

    def test_12_the_correction_ceiling_is_the_records_number(self):
        c = self.c[u"**α の天井(席が外した行で Core が正解を持っていたか)**"]
        self.assertIn(u"| 席が参照先を外した行 | **%d** |" % c[u"席が外した行"], self.t)
        self.assertIn(u"| **うち Core が正解を持っていた** | **%d** |"
                      % c[u"**Core が正解を持っていた**"], self.t)
        self.assertIn(u"| Core が参照先を出さなかった | %d |"
                      % c[u"Core が参照先を出さなかった"], self.t)
        self.assertIn(u"| Core が席と同じ(誤った)参照先を出した | %d |"
                      % c[u"Core が席と同じ参照先を出した"], self.t)

    def test_13_both_samples_rates_are_printed_with_denominators(self):
        r = self.c[u"Core 自身の特定率"]
        for k in (u"本番(未使用 8 書類)", u"(ア)(別の 8 書類・同じ P16)",
                  u"席(本番)"):
            self.assertIn(self._pct(r[k]), self.t, k)
        # **(ア) の記録の見出しの数は書き換えない**
        self.assertIn(u"**71.9%(46/64)**", self.t)
        self.assertIn(u"**その数は書き換えない**", self.t)

    def test_14_strata_and_per_document_spread(self):
        for s in (u"本番(未使用 8)", u"(ア)(別の 8)"):
            st = self.c[u"層別"][s]
            for k in (u"次元つき", u"次元なし"):
                if st[k][u"率"] is None:
                    continue
                self.assertIn(self._pct(st[k]), self.t, (s, k))
        for d, v in self.c[u"書類ごと(本番)"].items():
            self.assertIn(u"| `%s` | %s |" % (d, self._pct(v)), self.t, d)

    def test_15_the_addendum_does_not_promise_what_it_did_not_measure(self):
        b = self.t[self.t.index(u"### §8-5"):]
        self.assertIn(u"**α の「警告」はまだ測っていない。**", b)
        self.assertIn(u"**値の照合は「参照先の正しさ」を分けられない。**", b)
        self.assertIn(u"**「次元を出せない」は仮説であり、測るまで断定しない。**", b)
        self.assertIn(u"**原因は特定していない。**", b)


if __name__ == "__main__":
    unittest.main()
