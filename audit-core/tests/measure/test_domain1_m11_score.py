# -*- coding: utf-8 -*-
"""段 11 の採点の結果(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §6・§8)を固定する。

守るのは 12 つ。
  1. 線が **7 本**在り、**6 本通って G-1′ が落ちた**こと(数をそのまま固定)
  2. **総合は失敗**であること(**成功に読み替えない**)
  3. **E2 = 0・誤接続 0 件**(安全の側は通った)
  4. **X-2 は 3 通りとも 0 件**で、**結んだ主張が 0 件でない**(= 未測定ではない)
  5. **β = 0 の「空振り」が空振りと書かれている**(安全性の証拠にしない)
  6. **対称と非対称の数が同じ**であること(この標本では別名表が効かなかった)
  7. **N-接続-増 = 0** が合否に入っていないこと
  8. **止めた主張が半分を超えたので G-1′ を成果として書かない**と記録に在ること
  9. G-4 が**分母 0 で未測定**(6 段続けて)
 10. `MIN_INDEPENDENT = 3`・sha が封と一致
 11. 採点が**ラベルと採点器から作り直せる**こと(記録を読むだけにしない)
 12. **閾値が段 9 の数のまま**であること
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
REC = os.path.join(FX, "m11_score_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class LinesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)
        cls.lines = cls.rec["主実験の線(7 本)"]

    def test_1_seven_lines_six_passed(self):
        self.assertEqual(len(self.lines), 7)
        ok = [k for k, v in self.lines.items() if v["ok"]]
        bad = [k for k, v in self.lines.items() if not v["ok"]]
        self.assertEqual(len(ok), 6, ok)
        self.assertEqual(bad, ["G-1′(新)③で止めた主張を除いた接続の正確さ"], bad)

    def test_2_the_overall_verdict_is_failure(self):
        self.assertIn("失敗", self.rec["主実験の判定"],
                      "**失敗を成功に読み替えてはいけない**")
        self.assertNotIn("合格", self.rec["主実験の判定"])

    def test_3_the_safety_lines_passed(self):
        e2 = self.lines["E2(新・対称)誤受理"]
        self.assertEqual(e2["count"], 0)
        self.assertEqual(e2["G-2 誤接続"], 0)
        self.assertEqual(e2["G-3 根拠なし"], 0)
        self.assertEqual([r["id"] for r in self.rec["rows"]
                          if r["verdict"] == "誤接続"], [])

    def test_4_x2_is_measured_not_vacuous(self):
        x = self.rec["X-2 の 3 通り(封 §4)"]
        self.assertEqual([x["X-2対称(合否)"], x["X-2非対称(開示だけ)"],
                          x["X-2三欄(裏取り)"]], [0, 0, 0])
        self.assertGreater(x["結んだ主張"], 0,
                           "結んだ主張が 0 件なら X-2 は未測定である")
        self.assertEqual(x["X-1対称"], x["結んだ主張"])
        self.assertTrue(x["判定"]["合格"])
        self.assertIn("人工材料", x["計数器の歯"])

    def test_5_beta_is_recorded_as_vacuous(self):
        b = self.rec["β と 5 欄(封 §5。循環を切る)"]
        self.assertEqual(b["β 別名表に依って一致した主張"], 0)
        self.assertTrue(b["空振りか"])
        self.assertIn("空振りを「安全性の証拠」として書かない", b["注"])
        self.assertTrue(self.lines["β の 5 欄の食い違い"]["空振りか"],
                        "空振りを線の中でも開示すること")

    def test_6_symmetric_and_asymmetric_agree_on_this_sample(self):
        asym = self.rec["**非対称にしたときの数(開示。性能として書かない)**"]
        self.assertEqual(asym["正しい接続"],
                         self.rec["5 つを分けて数える(封 §6-1)"]["N-接続-正"]["新"])
        self.assertEqual(asym["誤接続"], 0)
        self.assertIn("合否には使わない", asym["注"])

    def test_7_increment_is_zero_and_not_a_line(self):
        inc = self.rec["記録のみ(線にしない)"]["N-接続-増(合否に入れない)"]
        self.assertEqual(inc["count"], 0)
        self.assertEqual(inc["旧"], inc["新"])
        self.assertIn("増えても合格にしない", inc["注"])
        self.assertNotIn("N-接続-増", self.lines)

    def test_8_g1p_is_not_a_performance_claim(self):
        u = self.rec["G-1′ を成果として書けるか"]
        self.assertFalse(u["usable"])
        self.assertEqual(u["止めた主張(A-1 + A-2)"], 19)
        self.assertEqual(u["採点対象"], 35)
        self.assertIn("分母が偏っている", u["注"])

    def test_9_g4_is_unmeasured_again(self):
        g4 = self.rec["併測 G-4(合否に入れない)"]
        self.assertEqual(g4["den"], 0)
        self.assertEqual(g4["status"], "未測定")

    def test_10_threshold_and_shas(self):
        self.assertEqual(self.rec["min_independent"], 3)
        run = _mod("run11_for_score_t", "sheet_m11_run_2026-10-16.py")
        self.assertEqual(self.rec["engine_sha"], run.check_shas())

    def test_11_thresholds_are_stage9_numbers(self):
        sc = _mod("m11score_t2", "sheet_m11_score_2026-10-16.py")
        self.assertEqual(sc.G1P_MIN, 0.50)
        self.assertEqual(sc.G4_MIN, 0.80)
        self.assertEqual(sc.G5_MIN, 20)
        self.assertAlmostEqual(
            self.lines["G-1′(新)③で止めた主張を除いた接続の正確さ"]["rate"],
            16.0 / 35, places=6)


class ReproducibleTest(unittest.TestCase):
    """**記録を読むだけにしない。**ラベルと bind から数え直して突き合わせる。"""

    def test_12_tally_reproduces_the_numbers(self):
        sc = _mod("m11score_t3", "sheet_m11_score_2026-10-16.py")
        rec = load(REC)
        binds = load(os.path.join(FX, "m11_binds_2026-10-16.json"))
        claims = {c["id"]: c for c in binds["claims"]}
        bn = {b["claim_id"]: b for b in binds["binds_new"]}
        s1 = {a["id"]: a for a in
              load(os.path.join(FX, "m11_answers_seat1_2026-10-16.json"))["answers"]}
        s2 = {a["id"]: a for a in
              load(os.path.join(FX, "m11_answers_seat2_2026-10-16.json"))["answers"]}
        scorable = sorted(cid for cid, c in claims.items() if c.get("scorable"))
        books = {}
        for f in (sc.RUN.M2.SOUKATU, sc.RUN.M2.KESSAN, sc.RUN.M2.MEISAI):
            books[f], _ = sc.RUN.M2.M1.read(os.path.join(sc.RUN.M2.CACHE, f))
        raw = sc.RUN.OLD.fix_total_level(sc.RUN.OLD.build_index(
            sc.RUN.M2.parse_soukatu(books[sc.RUN.M2.SOUKATU]),
            sc.RUN.M2.parse_kessan(books[sc.RUN.M2.KESSAN]),
            sc.RUN.M2.parse_meisai(books[sc.RUN.M2.MEISAI])))
        sc.S8.ALIAS = sc.RUN.NEW.alias_table(raw)["table"]
        t = sc.tally(bn, claims, scorable, s1, s2)
        self.assertEqual(t["g1"], 16)
        self.assertEqual(t["e2"], 0)
        self.assertEqual(len(scorable), rec["scored_claims"])
        self.assertEqual(t["seats_agree_6"],
                         rec["記録のみ(線にしない)"]
                         ["席の一致率(成果として書かない)"]["num"])


if __name__ == "__main__":
    unittest.main()
