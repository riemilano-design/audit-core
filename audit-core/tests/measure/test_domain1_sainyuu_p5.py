# -*- coding: utf-8 -*-
"""P-5 診断(docs/DOMAIN1_SAIIRU_P5_2026-10-16.md)を固定する。

守るのは 8 つ。
  1. 凍結した engine の sha が動いていないこと・`MIN_INDEPENDENT = 3`
  2. **その場で当て直して**段 9 の再現 6 / 新 18 / E2 0 / A-1 12 -> 0 が出ること
  3. **段 9 で正しかった 6 件が 1 件も壊れていない**こと
  4. **非対称にすると誤接続 12 件になる**こと(片側正規化の作り物を数で残す)
  5. **会計の欄を除いた 5 欄が、別名表を切った状態で 12/12 一致**すること(循環を切る)
  6. **席が 12 件とも `東京都○○会計` と書いている**こと(問いの指示どおり)
  7. 停止規則の判定が記録と文書で一致すること
  8. 文書が X-2 を**未測定**と書き、「安全性が改善した」と書かないこと
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "sainyuu_p5_2026-10-16.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_SAIIRU_P5_2026-10-16.md")
SRC = os.path.join(MEASURE, "sheet_sainyuu_p5_2026-10-16.py")
ENGINE = os.path.join(MEASURE, "sheet_m5_engine_2026-10-15.py")
NEWENG = os.path.join(MEASURE, "sheet_sainyuu_engine_2026-10-16.py")

NEW_IDS = ["R009", "R010", "R011", "R012", "R013", "R014", "R015",
           "R017", "R019", "R020", "R021", "R022"]


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class PinnedTest(unittest.TestCase):
    def test_1_shas_and_threshold(self):
        rec = load(REC)
        self.assertEqual(rec["min_independent"], 3)
        self.assertIn("MIN_INDEPENDENT = 3", text(ENGINE))
        # 新しい engine は閾値を定義し直さない
        t = text(NEWENG)
        self.assertIn("MIN_INDEPENDENT = M7.MIN_INDEPENDENT", t)
        self.assertNotIn("MIN_INDEPENDENT = 1", t)
        self.assertNotIn("MIN_INDEPENDENT = 2", t)
        self.assertTrue(rec["engine_shas_unchanged"])


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.rec = load(REC)

    def test_2_counts(self):
        old = self.rec["対称(段 9 の再現)"]
        new = self.rec["対称(新。**これが答え**)"]
        self.assertEqual(old["g1"], 6)
        self.assertEqual(new["g1"], 18)
        self.assertEqual(new["e2"], 0)
        self.assertEqual(new["g2"], 0)
        self.assertEqual(self.rec["N-接続-正の増分"], 12)
        self.assertEqual(self.rec["新しく正しく接続した主張"], NEW_IDS)

    def test_3_nothing_broke(self):
        self.assertEqual(
            self.rec["壊れた主張(段 9 で正しかったのに新で正しくない)"], [])

    def test_4_alias_hold_went_to_zero(self):
        self.assertEqual(self.rec["A の数え(段 9 の engine)"]["A-1"], 12)
        self.assertEqual(self.rec["A の数え(新 engine)"]["A-1"], 0)
        self.assertEqual(self.rec["A の数え(新 engine)"]["A-3"], 0)
        self.assertEqual(self.rec["別名"]["新で通った"], 19)
        self.assertEqual(self.rec["別名"]["未確認のまま"], 0)

    def test_5_the_asymmetric_variant_is_recorded(self):
        """**片側だけ正規化すると同じ 12 件が誤接続になる。**数で残す。"""
        a = self.rec["非対称(開示用。採点器だけ段 9 の別名表)"]
        self.assertEqual(a["g1"], 6)
        self.assertEqual(a["g2"], 12)
        self.assertEqual(a["e2"], 12)

    def test_6_five_fields_agree_without_the_alias_table(self):
        """**循環を切る測定。**会計を除いた 5 欄が別名表なしで一致すること。"""
        f = self.rec["会計の欄を除いた 5 欄の一致(別名表を使わない)"]
        self.assertEqual(f["一致"], 12)
        self.assertEqual(f["食い違い"], 0)
        self.assertEqual(f["判定不能"], 0)
        self.assertNotIn("会計", f["欄"])
        self.assertEqual(len(f["欄"]), 5)

    def test_7_stop_rule(self):
        self.assertEqual(self.rec["停止規則の判定"], "本実験に進める")
        self.assertIn("0 件ならこの経路を打ち切る", self.rec["停止規則"])


class SeatFormTest(unittest.TestCase):
    """**席は問いの指示どおり抜粋の字で書いた。**ここを取り違えると §2 の読みが壊れる。"""

    def test_8_both_seats_wrote_the_printed_alias(self):
        for seat in ("seat1", "seat2"):
            d = load(os.path.join(FX, "m9_answers_%s_2026-10-16.json" % seat))
            ans = {a["id"]: a for a in d["answers"]}
            n = sum(1 for i in NEW_IDS
                    if str((ans.get(i) or {}).get("会計") or "").startswith("東京都"))
            self.assertEqual(n, 12, seat)

    def test_9_the_question_asks_for_the_printed_spelling(self):
        q = load(os.path.join(FX, "m9_label_material_2026-10-16.json"))["question"]
        self.assertIn("指している行の「会計」欄に書かれている字をそのまま", q)
        self.assertIn("`東京都` を付けたり外したりしないでください", q)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.rec = load(REC)

    def test_10_numbers_match(self):
        self.assertIn("| **正しい接続** | **6** | **18** |", self.t)
        self.assertIn("**N-接続-正 の増分: +12 件**", self.t)
        self.assertIn("| **段 9 のまま(非対称)** | 6 | **12** | **12** |", self.t)
        self.assertIn("| **5 欄の一致** | **12 件** |", self.t)

    def test_11_the_asymmetry_warning_is_present(self):
        self.assertIn("**片側だけ正規化を掛けるのは段 8 の欠陥そのものである**", self.t)
        self.assertIn("**2026-10-16 に 5 回目**", self.t)
        self.assertIn("**席は 12 件とも指示どおり `東京都○○会計` と書いた**", self.t)

    def test_12_x2_is_declared_unmeasured(self):
        self.assertIn("**X-2 は P-5 では測っていない。**", self.t)
        self.assertIn("X-2 は**未測定**", self.t)

    def test_13_limits_and_no_safety_claim(self):
        block = self.t.split("## §5")[1]
        self.assertIn("**既知の標本に対する診断であり、性能の証明ではない。**", block)
        self.assertIn("**③の実物の文に対する安全性は、依然として未検証である。**", block)
        self.assertIn("**「別名規則の安全性が改善した」とは書かない。**", block)
        self.assertNotIn("安全性を確認できた", self.t)

    def test_14_the_miss_is_recorded(self):
        self.assertIn("| T-6 | P-5 の新しい正しい接続は **0〜6 件** | **+12 件** | **外れ** |",
                      self.t)
        self.assertIn("**5 本中 5 本が「低く見る」向きに外れた**", self.t)

    def test_15_cost_is_zero_and_report_before_spending(self):
        self.assertIn("**生成していない(費用 0 USD)", self.t)
        self.assertIn("**ただし本実験は生成に費用が掛かるので、走らせる前に人間へ報告する。**",
                      self.t)


class LiveReMeasureTest(unittest.TestCase):
    """**その場で測り直して記録と一致すること。**

    記録を読むだけの門は、採点器の別名表の差し替えや 5 欄の比較を壊す変異に黙る。
    実物の 5 冊を読むので数十秒かかるが、**ここが本体である。**
    """

    @classmethod
    def setUpClass(cls):
        sp = importlib.util.spec_from_file_location("p5_live", SRC)
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        cls.live = m.measure()
        cls.rec = load(REC)

    def test_16_the_whole_record_is_reproduced(self):
        for k in ("対称(段 9 の再現)", "対称(新。**これが答え**)",
                  "非対称(開示用。採点器だけ段 9 の別名表)",
                  "A の数え(段 9 の engine)", "A の数え(新 engine)",
                  "会計の欄を除いた 5 欄の一致(別名表を使わない)",
                  "N-接続-正の増分", "新しく正しく接続した主張",
                  "壊れた主張(段 9 で正しかったのに新で正しくない)",
                  "別名", "採点対象", "停止規則の判定"):
            self.assertEqual(self.live[k], self.rec[k], k)

    def test_17_the_symmetric_and_asymmetric_runs_really_differ(self):
        """**歯。**対称と非対称が同じ数なら、この区別は何も測っていない。"""
        sym = self.live["対称(新。**これが答え**)"]
        asym = self.live["非対称(開示用。採点器だけ段 9 の別名表)"]
        self.assertNotEqual(sym["g1"], asym["g1"])
        self.assertNotEqual(sym["g2"], asym["g2"])
        self.assertEqual(sym["g1"] - asym["g1"], asym["g2"])

    def test_18_the_stop_rule_follows_the_increment(self):
        """判定が増分から決まっていること(字で固定していない)。"""
        inc = self.live["N-接続-正の増分"]
        self.assertEqual(self.live["停止規則の判定"],
                         "本実験に進める" if inc >= 1 else "**打ち切る**")
        self.assertGreaterEqual(inc, 1)


class DecisionTeethTest(unittest.TestCase):
    """**壊した入力で判定を当てる。**この材料は「食い違い 0・全部 3 本以上」なので、
    実物だけでは判定を壊す変異が黙る(2026-10-16 の変異 S2・S4・S8 で実測)。"""

    @classmethod
    def setUpClass(cls):
        sp = importlib.util.spec_from_file_location("eng_t", NEWENG)
        cls.eng = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(cls.eng)
        sp2 = importlib.util.spec_from_file_location("p5_t", SRC)
        cls.p5 = importlib.util.module_from_spec(sp2)
        sp2.loader.exec_module(cls.p5)

    def test_19_a_mismatch_is_never_promoted(self):
        """**A-規則-4。**食い違いが 1 件でもあれば、裏づけが何本あっても通さない。"""
        ok, why = self.eng.promote(1, {1, 2, 3, 4, 5})
        self.assertFalse(ok)
        self.assertIn("食い違い", why)

    def test_20_short_backing_is_never_promoted(self):
        ok, why = self.eng.promote(0, {1, 2})
        self.assertFalse(ok)
        self.assertIn("独立した裏づけが 2 本", why)
        ok3, why3 = self.eng.promote(0, {1, 2, 3})
        self.assertTrue(ok3, why3)
        self.assertIsNone(why3)

    def test_21_the_threshold_used_is_three(self):
        self.assertEqual(self.eng.MIN_INDEPENDENT, 3)
        self.assertFalse(self.eng.promote(0, {1, 2})[0])
        self.assertTrue(self.eng.promote(0, {1, 2, 3})[0])

    def test_22_the_stop_rule_has_both_branches(self):
        self.assertEqual(self.p5.stop_verdict(1), "本実験に進める")
        self.assertEqual(self.p5.stop_verdict(12), "本実験に進める")
        self.assertEqual(self.p5.stop_verdict(0), "**打ち切る**")

    def test_23_the_five_field_check_cannot_depend_on_the_alias_table(self):
        """**S6 は同値である**と測って確かめる(門を足すのではなく証明する)。

        5 欄は会計を含まないので、別名表を入れても結果は変わらない。
        **会計を含めたら変わる**ので、そこは `test_7`(欄の中身)が守る。
        """
        rec = load(REC)
        f = rec["会計の欄を除いた 5 欄の一致(別名表を使わない)"]
        self.assertNotIn("会計", f["欄"])
        # 会計を外した 5 欄に別名表が効く余地が無いことを、欄の集合で示す
        import importlib.util as iu
        sp = iu.spec_from_file_location("s8_t", os.path.join(MEASURE,
                                        "sheet_m8_score_2026-10-16.py"))
        s8 = iu.module_from_spec(sp)
        sp.loader.exec_module(s8)
        self.assertEqual(set(s8.F6) - set(f["欄"]), {"会計"})
        self.assertIn("### §2-2 この 5 欄の測定は**別名表に依らない**(測って確かめた)",
                      text(DOC))
        self.assertIn("**12 件のラベルを別名表あり/なしで作り直して、食い違い 0 件**",
                      text(DOC))


if __name__ == "__main__":
    unittest.main()
