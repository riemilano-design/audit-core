# -*- coding: utf-8 -*-
u"""(d) の実測(docs/XBRL_DIM_HOLD_RESULT_2026-10-17.md)の門。

**本文の数は `dim_hold_2026-10-17.json` を正本に突き合わせる。**
**「精度が上がった」「6 行は誤りだった」へ結論が滑らないことを固定する。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_DIM_HOLD_RESULT_2026-10-17.md")
SEAL = os.path.join(ROOT, "docs", "XBRL_DIM_HOLD_SEAL_2026-10-17.md")
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "dim_hold_2026-10-17.json")
DIAG = os.path.join(FX, "dim_diag_2026-10-17.json")
V1 = os.path.join(FX, "contract_v1_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p=REC):
    return json.load(io.open(p, encoding="utf-8"))


def pct(v):
    return u"%s%%(%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])


class StateTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        self.p1 = self.r[u"**第 1 部 規則の適用**"]

    def test_1_only_grounded_moved(self):
        a, b = self.p1[u"状態(前)"], self.p1[u"状態(後)"]
        for k in ("VALUE_MISMATCH", "POINTER_NOT_FOUND"):
            self.assertEqual(a.get(k, 0), b.get(k, 0), k)
            self.assertIn(u"| `%s` | %d | %d(**変わらない**) |"
                          % (k, a.get(k, 0), b.get(k, 0)), self.t, k)
        self.assertLess(b.get("GROUNDED", 0), a.get("GROUNDED", 0))
        self.assertEqual(a.get("GROUNDED", 0) - b.get("GROUNDED", 0),
                         b.get("UNPROVABLE", 0) - a.get("UNPROVABLE", 0))

    def test_2_the_pass_count_matches_the_record_and_contract_v1(self):
        p = self.p1[u"**検査通過**"]
        self.assertEqual(p[u"前"], rec(V1)[u"検査通過"][u"**B′**"])
        self.assertIn(u"| **検査通過(最終判定)** | **%d** | **%d** |"
                      % (p[u"前"], p[u"後"]), self.t)
        self.assertIn(u"**検査通過が %d → %d 行に減った。**"
                      % (p[u"前"], p[u"後"]), self.t)

    def test_3_the_fired_rows_are_the_diagnosis_rows(self):
        fired = [(x[u"doc"], x[u"id"]) for x in self.p1[u"**発火した行**"]]
        self.assertEqual(sorted(fired),
                         sorted((x[u"doc"], x[u"id"])
                                for x in rec(DIAG)["rows"]))
        self.assertIn(u"**発火 %d 行 = %s。**"
                      % (self.p1[u"**発火**"][u"分子"], pct(self.p1[u"**発火**"])),
                      self.t)
        for x in self.p1[u"**発火した行**"]:
            self.assertIn(u"| `%s` %s | %d | `%s` | %s |"
                          % (x[u"doc"], x[u"id"], x[u"兄弟の件数"], x[u"理由"],
                             x[u"**比較器も受ける兄弟(別の数え方)**"]), self.t)

    def test_4_the_reason_carries_the_sibling_count(self):
        for x in self.p1[u"**発火した行**"]:
            self.assertEqual(x[u"理由"],
                             "ambiguous_dimension:%d" % x[u"兄弟の件数"])


class ControlTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.c = rec()[u"**対照(故障を作って当てる)**"]

    def test_5_the_positive_control_fires_on_everything_tried(self):
        self.assertEqual(self.c[u"C-次元(陽性対照)/**発火**"],
                         self.c[u"C-次元(陽性対照)/試せた"])
        self.assertGreater(self.c[u"C-次元(陽性対照)/試せた"], 0)
        self.assertIn(u"**陽性対照が %d/%d で発火した**"
                      % (self.c[u"C-次元(陽性対照)/**発火**"],
                         self.c[u"C-次元(陽性対照)/試せた"]), self.t)

    def test_6_the_excluded_controls_do_not_fire(self):
        for k in (u"C-期間", u"C-単位"):
            self.assertEqual(self.c[k + u"/**発火**"], 0, k)
            self.assertGreater(self.c[k + u"/試せた"], 0, k)
        self.assertIn(u"「規則が繋がっていない」ではなく「除外条件が効いた」である。**",
                      self.t)
        self.assertIn(u"guard-that-only-fires-on-failure", self.t)

    def test_7_the_control_table_matches_the_record(self):
        u"""**表の 3 行を記録の数で字のまま当てる。**"""
        self.assertIn(u"| C-期間(期間だけ違う同額の兄弟を注入) | %d | %d | **%d** |"
                      % (self.c[u"C-期間/試せた"], self.c[u"C-期間/作れなかった"],
                         self.c[u"C-期間/**発火**"]), self.t)
        self.assertIn(u"| C-単位(単位だけ違う同額の兄弟を注入) | %d | 0 | **%d** |"
                      % (self.c[u"C-単位/試せた"], self.c[u"C-単位/**発火**"]),
                      self.t)
        self.assertIn(u"| **C-次元(陽性対照。次元だけ違う同額の兄弟を注入)** | "
                      u"%d | 0 | **%d** |"
                      % (self.c[u"C-次元(陽性対照)/試せた"],
                         self.c[u"C-次元(陽性対照)/**発火**"]), self.t)


class ExposureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.p2 = rec()[u"**第 2 部 露出の帯(状態は変えない)**"]

    def test_8_the_three_bands_match_the_record(self):
        for k in (u"D2 席が名指した 85 行", u"D3 無改変で名指した 42 行",
                  u"D4 正解(T5)の参照先 50 件"):
            self.assertIn(u"**%s**" % pct(self.p2[k]), self.t, k)

    def test_9_the_gold_band_zero_is_shown_to_be_resolved(self):
        self.assertEqual(self.p2[u"D4 正解(T5)の参照先 50 件"][u"分子"], 0)
        self.assertEqual(self.p2[u"D4 正解(T5)の参照先 50 件"][u"分母"], 50)
        self.assertEqual(set(self.p2[u"**参照先が解けなかった件数**"].values()),
                         {0})
        self.assertIn(u"**この 0 は私の引き方が作った 0 ではない。**", self.t)
        self.assertIn(u"**49/50 は同じ要素の別の枠を持っていた**", self.t)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.p = rec()[u"**予測との照合**"]
        self.b = self.t[self.t.index(u"## §5"):self.t.index(u"## §6")]

    def test_10_all_fourteen_fields_are_tallied_with_the_seals_symbols(self):
        ids = re.findall(r"(?m)^\| \*\*(D-\d+)\*\* \|", self.b)
        self.assertEqual(ids, [x[u"記号"] for x in self.p[u"欄ごと"]])
        self.assertEqual(len(ids), 14)
        s = text(SEAL)
        for i in ids:
            self.assertIn(u"| **%s** |" % i, s, i)

    def test_11_the_tally_is_the_records_three_way_split(self):
        self.assertIn(u"**当たり %d / 外れ %d / 未測定 %d。**"
                      % (self.p[u"当たり"], self.p[u"外れ"], self.p[u"**未測定**"]),
                      self.b)
        self.assertEqual(self.p[u"当たり"] + self.p[u"外れ"]
                         + self.p[u"**未測定**"], 14)

    def test_12_each_row_shows_the_records_verdict(self):
        for x in self.p[u"欄ごと"]:
            word = (u"**当たり**" if x[u"当たり"] is True
                    else (u"**未測定**" if x[u"当たり"] is None else u"**外れ**"))
            self.assertIn(u"| **%s** | %s | %s | %s |"
                          % (x[u"記号"], x[u"予測"], x[u"実測"], word),
                          self.b, x[u"記号"])

    def test_13_the_misses_are_kept_as_misses(self):
        missed = [x[u"記号"] for x in self.p[u"欄ごと"] if x[u"当たり"] is False]
        self.assertEqual(missed, ["D-5", "D-7"])
        for m in missed:
            self.assertIn(u"- **%s 外れ**" % m, self.b)
        self.assertIn(u"外れた向きは**規則にとって有利な向き**である", self.b)
        self.assertIn(u"**当たったと読み替えない。**", self.b)
        self.assertIn(u"**D-14 未測定**", self.b)


class LimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_14_no_accuracy_claim_survives(self):
        b = self.t[self.t.index(u"## §6"):self.t.index(u"## §7")]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 9)])
        self.assertIn(u"**この規則は精度を上げない。**", b)
        self.assertIn(u"**保留は誤りの指摘ではない。**", b)
        self.assertIn(u"**保留した 6 行が誤りだったとは言えない。**", b)
        self.assertIn(u"**要素そのものを取り違える問題(T5)は残る。**", b)
        self.assertIn(u"**製品の経路には入っていない。**", b)
        self.assertIn(u"**本番の拒否規則ではない。**", b)
        self.assertNotIn(u"誤りを 6 件見つけた", self.t)

    def test_14b_every_mention_of_accuracy_gain_is_negated(self):
        u"""**字で禁句を並べると自分の否定文に当たる**(記憶
        `source-text-tests-hit-own-prose`。この便で 2 回目)。**否定を見る。**"""
        #: **主張の形**だけを拾う(「改善」の字そのものは拾わない ―
        #: 「改善に数えない」「改善を示すには」は主張ではない)
        CLAIMS = (u"精度が上がった", u"精度が上がる", u"改善した",
                  u"改善が見られ", u"精度の向上")
        NEG = (u"とは言えない", u"上げない", u"示せない", u"数えない",
               u"ではない", u"余地が無かった")
        hits = [ln for ln in self.t.splitlines()
                if any(c in ln for c in CLAIMS)]
        self.assertGreaterEqual(len(hits), 1, u"精度への言及が消えている")
        for ln in hits:
            self.assertTrue(any(n in ln for n in NEG),
                            u"否定のない精度の主張: %s" % ln)

    def test_15_the_cost_section_states_zero_false_rejections(self):
        b = self.t[self.t.index(u"## §2"):self.t.index(u"## §3")]
        self.assertIn(u"**正しい参照先を `不一致` にした件数の増加は 0 件**", b)
        self.assertIn(u"**この規則は誤拒否を作らない。**", b)
        self.assertIn(u"**数としては 6 行すべて正しい。**", b)

    def test_16_the_next_steps_are_three_and_left_to_the_human(self):
        b = self.t[self.t.index(u"## §7"):]
        self.assertEqual(re.findall(r"(?m)^(\d)\. \*\*", b), ["1", "2", "3"])
        self.assertIn(u"**改善を示すには、誤った参照先が通る標本が要る。**", b)
        self.assertIn(u"**engine の変更になる。**", b)

    def test_17_the_engine_is_declared_untouched(self):
        self.assertIn(u"**engine は 1 行も変えていない。規則は封じた 1 つだけ。"
                      u"0 USD・席は呼んでいない。**", self.t)
        self.assertIn(u"XBRL_DIM_HOLD_SEAL_2026-10-17.md", self.t)


class VerdictWordTest(unittest.TestCase):
    u"""判定の語(measure/xbrl_dim_hold_2026-10-17.py: verdict_word)。

    **`None`(未測定)を偽として「外れ」と書いた欠陥**を、記憶ではなく門にする
    (2026-10-19 の再実行の印字で見つけた。記録と文書は正しかった)。
    """

    def setUp(self):
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "dim_hold_for_word",
            os.path.join(ROOT, "measure", "xbrl_dim_hold_2026-10-17.py"))
        self.M = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.M)

    def test_18_none_is_unmeasured_not_a_miss(self):
        self.assertEqual(self.M.verdict_word(None), u"**未測定**")

    def test_19_true_and_false_keep_their_words(self):
        self.assertEqual(self.M.verdict_word(True), u"**当たり**")
        self.assertEqual(self.M.verdict_word(False), u"**外れ**")

    def test_20_the_three_words_are_distinct(self):
        words = [self.M.verdict_word(v) for v in (True, None, False)]
        self.assertEqual(len(set(words)), 3)
        #: **記録の 3 つの数と同じ語を使っていること**
        p = rec()[u"**予測との照合**"]
        self.assertEqual(
            [sum(1 for x in p[u"欄ごと"]
                 if self.M.verdict_word(x[u"当たり"]) == w) for w in words],
            [p[u"当たり"], p[u"**未測定**"], p[u"外れ"]])

    def test_21_values_outside_the_three_states_are_refused(self):
        u"""**真偽値として緩めると `1` が静かに「当たり」になる。**

        三値以外を拒否することで、`is True` を `if v:` に緩める変異が赤くなる
        (記憶 `mutations-miss-degenerate-inputs`)。
        """
        for bad in (1, 0, "", u"x", [], [1], 1.0):
            self.assertRaises(ValueError, self.M.verdict_word, bad)


if __name__ == "__main__":
    unittest.main()
