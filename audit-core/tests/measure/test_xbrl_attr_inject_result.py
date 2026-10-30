# -*- coding: utf-8 -*-
u"""属性注入の結果(docs/XBRL_ATTR_INJECT_RESULT_2026-10-17.md)の門。

**本文の数は記録 `attr_inject_2026-10-17.json` を正本に突き合わせる。**
**外れた予測が当たりに書き換えられないこと、**
**「期間は安全」「第 1 層を直すべき」へ結論が滑らないことを固定する。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_ATTR_INJECT_RESULT_2026-10-17.md")
SEAL = os.path.join(ROOT, "docs", "XBRL_ATTR_INJECT_SEAL_2026-10-17.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8",
                   "attr_inject_2026-10-17.json")
BRANCHES = (u"単位", u"期間(注入)", u"期間(実在の枠を指す)", u"次元")
EXPOSURE = (u"別の期間", u"別の次元", u"別の単位")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


def pct(v):
    return u"%s%%(%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])


class BodyMatchesRecordTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_1_control_fired(self):
        n = self.r[u"行"][u"**対照が通った(有効)**"]
        self.assertEqual(n, self.r[u"行"][u"基準"])
        self.assertEqual(self.r[u"行"][u"無効"], [])
        self.assertIn(u"**対照は %d/%d が `GROUNDED`**" % (n, n), self.t)

    def test_2_injection_table_matches(self):
        p1 = self.r[u"**第 1 部 注入**"]
        self.assertEqual(sorted(p1), sorted(BRANCHES))
        for k in BRANCHES:
            v = p1[k]
            self.assertIn(u"| %s | %d | %d | **%s** |"
                          % (k, v[u"試せた"], v[u"作れなかった"],
                             pct(v[u"**誤って通した**"])), self.t, k)

    def test_3_exposure_table_matches(self):
        p2 = self.r[u"**第 2 部 露出(注入なし)**"]
        self.assertEqual(sorted(p2), sorted(EXPOSURE))
        for k in EXPOSURE:
            self.assertIn(u"| %s | **%s** |" % (k, pct(p2[k])), self.t, k)

    def test_4_the_three_holes_are_reported_as_open(self):
        p1 = self.r[u"**第 1 部 注入**"]
        for k in (u"単位", u"期間(注入)", u"次元"):
            self.assertEqual(p1[k][u"**誤って通した**"][u"率"], 100.0, k)
        self.assertIn(u"**単位・次元・期間(注入)はどれも 100% 通る。**", self.t)

    def test_5_the_zero_column_is_not_credited_to_core(self):
        v = self.r[u"**第 1 部 注入**"][u"期間(実在の枠を指す)"]
        self.assertEqual(v[u"**誤って通した**"][u"分子"], 0)
        self.assertIn(u"**「期間(実在の枠を指す)」の 0/%d は Core の功績ではない。**"
                      % v[u"試せた"], self.t)
        self.assertIn(u"**期間を見たからではない。**", self.t)

    def test_6_dimension_is_named_the_measured_risk(self):
        d = self.r[u"**第 2 部 露出(注入なし)**"][u"別の次元"]
        self.assertGreater(d[u"分子"], 0)
        self.assertIn(u"**実データで危ないのは「次元」である**", self.t)
        self.assertIn(u"**%d 行のうち %d 行(%s%%)**"
                      % (d[u"分母"], d[u"分子"], d[u"率"]), self.t)


class PredictionsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        self.b = self.t[self.t.index(u"## §2"):self.t.index(u"## §3")]

    def test_7_every_sealed_field_is_tallied(self):
        ids = re.findall(r"(?m)^\| (Q-\d) \|", self.b)
        self.assertEqual(ids, [x[u"記号"] for x in
                               self.r[u"**予測との照合**"][u"欄ごと"]])
        self.assertEqual(len(ids), 8)

    def test_8_hits_and_misses_are_the_records(self):
        v = self.r[u"**予測との照合**"]
        self.assertIn(u"**当たり %d / 外れ %d。**" % (v[u"当たり"], v[u"外れ"]),
                      self.b)
        for x in v[u"欄ごと"]:
            word = u"**当たり**" if x[u"当たり"] else u"**外れ**"
            self.assertIn(u"| %s | %s | %s | %s |"
                          % (x[u"記号"], x[u"予測"], x[u"実測"], word),
                          self.b, x[u"記号"])

    def test_9_the_two_misses_are_explained_as_misses(self):
        missed = [x[u"記号"] for x in self.r[u"**予測との照合**"][u"欄ごと"]
                  if not x[u"当たり"]]
        self.assertEqual(missed, ["Q-3", "Q-5"])
        for q in missed:
            self.assertIn(u"- **%s 外れ**" % q, self.b)
        self.assertIn(u"予測の時点でこれを数えていなかった。", self.b)
        self.assertIn(u"私の見立てが外れた。", self.b)

    def test_10_the_predictions_still_read_as_the_seal_wrote_them(self):
        s = text(SEAL)
        for x in self.r[u"**予測との照合**"][u"欄ごと"]:
            self.assertIn(x[u"記号"], s, x[u"記号"])


class DisclosureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_11_both_harness_defects_are_disclosed(self):
        b = self.t[self.t.index(u"## §3"):self.t.index(u"## §4")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. \*\*", b), ["1", "2"])
        self.assertIn(u"**期間の枝が 2 つの別物を 1 つの欄に混ぜていた。**", b)
        self.assertIn(u"**Q-8 の数え方が `VALUE_MISMATCH` まで数えていた。**", b)
        self.assertIn(u"**3 行が通り、21 行が `VALUE_MISMATCH` で止まった。**", b)
        self.assertIn(u"**この 2 つを足して「21/24 止めた」と書いてはいけない。**", b)

    def test_12_limits_are_the_records_and_do_not_prescribe_a_fix(self):
        b = self.t[self.t.index(u"## §4"):self.t.index(u"## §5")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 7)])
        self.assertIn(u"**「第 1 層を直すべき」とは書かない**", b)
        self.assertIn(u"**0 件でも「放置してよい」とは書かない。**", b)
        self.assertIn(u"**誤通過の件数は注入を作った私の手で決まる。**", b)
        self.assertNotIn(u"第 1 層を直すべきである", self.t)

    def test_12b_every_mention_of_safety_is_negated(self):
        u"""**字で禁句を並べると自分の否定文に当たる**(記憶
        `source-text-tests-hit-own-prose`)。**否定されているかを見る。**"""
        NEG = (u"ではない", u"別である", u"わけではない", u"書かない")
        hits = [ln for ln in self.t.splitlines() if u"安全" in ln]
        self.assertGreaterEqual(len(hits), 2, u"安全への言及が消えている")
        for ln in hits:
            self.assertTrue(any(n in ln for n in NEG),
                            u"否定のない『安全』: %s" % ln)

    def test_13_the_decision_is_left_to_the_human(self):
        b = self.t[self.t.index(u"## §5"):]
        self.assertIn(u"## §5 次に人間が決めること", self.t)
        self.assertEqual(re.findall(r"(?m)^(\d)\. \*\*", b), ["1", "2", "3"])
        self.assertIn(u"**増え方は測るまで分からない。**", b)
        self.assertIn(u"**席を呼ぶので 0 USD ではない。**", b)

    def test_14_the_engine_is_declared_untouched(self):
        self.assertIn(u"**engine は 1 行も変えていない。規則も増やしていない。"
                      u"0 USD・席は呼んでいない。**", self.t)
        self.assertIn(u"XBRL_ATTR_INJECT_SEAL_2026-10-17.md", self.t)


if __name__ == "__main__":
    unittest.main()
