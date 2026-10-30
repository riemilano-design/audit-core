# -*- coding: utf-8 -*-
"""段 9 の結果(docs/DOMAIN1_M9_RESULT_2026-10-16.md)を固定する。

**失敗した側の歯止めが本体。**守るのは 9 つ。
  1. 数が記録と一致し、**閾値が封のまま**であること
  2. **総合は失敗**(G-1′ 46.2% < 50%)。5 本通って 1 本落ちたと書いてある
  3. **③は初めて発火した(12 件)が、「誤接続を防いだ」ことは示せない**
  4. **③の費用を直接 12 + 間接 3 で書いている**(A-2 を成功に数えない)
  5. **G-4 は 4 段続けて未測定**。機会を確保しても発火は生成に依存する
  6. **生の G-1 を段 8 と比べない**・**席の一致率 100% を成果にしない**
  7. 外れた予測 4 本が残っており、**全部同じ向き**だと書いてある
  8. 目の親が**実質 1 本**だと書いてある
  9. **赤のまま commit した**ことと**封に無い規則を外した**ことを開示している
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "m9_score_2026-10-16.json")
BINDS = os.path.join(FX, "m9_binds_2026-10-16.json")
OPP = os.path.join(FX, "m9_opportunity_2026-10-16.json")
REPORT = os.path.join(FX, "m9_report_2026-10-16.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M9_RESULT_2026-10-16.md")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M9_SEAL_2026-10-16.md")
M8S = os.path.join(FX, "m8_score_2026-10-16.json")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class NumbersTest(unittest.TestCase):
    def setUp(self):
        self.s = load(SCORE)
        self.m = self.s["主実験(③)"]

    def test_1_overall_is_failure(self):
        self.assertEqual(self.s["主実験の判定"], "失敗")
        self.assertIn("**総合判定: 失敗。**", text(DOC))

    def test_2_five_pass_one_fails(self):
        ok = [k for k, v in self.m.items() if v["ok"]]
        bad = [k for k, v in self.m.items() if not v["ok"]]
        self.assertEqual(len(ok), 5)
        self.assertEqual(bad, ["G-1′ ③で止めた主張を除いた接続の正確さ"])
        self.assertIn("**5 本通って 1 本落ちた。**", text(DOC))

    def test_3_each_line(self):
        self.assertEqual(self.m["A-1 ③が発火した主張"]["count"], 12)
        self.assertEqual(self.m["A-3 未確認の別名の行に結んだ主張"]["count"], 0)
        self.assertEqual(self.m["E2 誤受理"]["count"], 0)
        self.assertEqual(self.m["X-2 抜粋に無い行に結んだ主張"]["count"], 0)
        self.assertEqual(self.m["G-5 母数"]["count"], 25)
        g1p = self.m["G-1′ ③で止めた主張を除いた接続の正確さ"]
        self.assertEqual((g1p["num"], g1p["den"]), (6, 13))
        self.assertAlmostEqual(g1p["rate"], 6.0 / 13, places=6)

    def test_4_thresholds_are_the_sealed_ones(self):
        self.assertEqual(self.m["A-1 ③が発火した主張"]["pass"], "≥ 1 件")
        self.assertEqual(self.m["A-3 未確認の別名の行に結んだ主張"]["pass"], "= 0 件")
        self.assertEqual(self.m["E2 誤受理"]["pass"], "= 0 件")
        self.assertEqual(self.m["X-2 抜粋に無い行に結んだ主張"]["pass"], "= 0 件")
        self.assertEqual(self.m["G-5 母数"]["pass"], "≥ 20")
        self.assertEqual(
            self.m["G-1′ ③で止めた主張を除いた接続の正確さ"]["pass"], "≥ 50%")
        seal = text(SEAL)
        self.assertIn("| **G-1′** | **③で止めた主張を分母から除いた**"
                      "接続の正確さ | **≥ 50%** |", seal)

    def test_5_recorded_only(self):
        r = self.s["記録のみ"]
        self.assertEqual(r["生の G-1(線にしない)"]["num"], 6)
        self.assertEqual(r["生の G-1(線にしない)"]["den"], 25)
        self.assertEqual(r["G-7 正しい接続の増分(線にしない)"]["count"], 0)
        self.assertEqual(r["G-8 誤受理の増分"]["count"], 0)
        self.assertEqual(r["A-2 ③以外の理由で保留"]["count"], 7)
        self.assertEqual(r["X-1"], 6)
        self.assertEqual(r["X-3 X-2 のうち誤受理"], 0)
        self.assertEqual(r["N-1 親で絞って親が合った"], 7)
        self.assertEqual(r["N-2 親で絞って親が違った"], 0)
        self.assertEqual(r["席の一致率(成果として書かない)"]["rate"], 1.0)

    def test_6_g1prime_guard_fired(self):
        g = self.s["G-1′ を成果として書けるか"]
        self.assertFalse(g["usable"])
        self.assertEqual(g["止めた主張(A-1 + A-2)"], 19)
        self.assertIn("**G-1′ を成果として書かない。**", text(DOC))

    def test_7_engine_sha_unchanged(self):
        self.assertEqual(self.s["engine_sha"], load(BINDS)["engine_sha"])
        for pre in ("6eb5723ef518e1b4", "4574c3ea013d05a1", "8e387958c69398e8"):
            self.assertIn(pre, self.s["engine_sha"].values())
            self.assertIn(pre, text(DOC))
        self.assertTrue(load(BINDS)["engine_unchanged"])
        self.assertFalse(load(REPORT)["engine_changed_for_m9"])


class ThirdRuleFiredTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_8_fired_for_the_first_time(self):
        self.assertIn("**③は 4 段目で初めて発火した**", self.t)
        self.assertIn("| ③が発火した主張(A-1) | 0 | 0 | 0 | **12** |", self.t)
        for cid in ("R009", "R015", "R019", "R022"):
            self.assertIn(cid, self.t)

    def test_9_cannot_show_it_prevented_a_wrong_link(self):
        self.assertIn("**「止まった」ことは示せた。"
                      "「止めたおかげで誤接続を防いだ」ことは示せない**", self.t)
        self.assertIn("この材料には、別名の推測が誤りになる行が 1 件も無い", self.t)
        self.assertIn("**12 件すべてについて、両席は抜粋から行を特定できていた**",
                      self.t)
        self.assertIn("**「安全に止まった」と「正しく止まった」は別である。**", self.t)

    def test_10_cost_is_direct_plus_indirect(self):
        self.assertIn("**③の保守性の値段を測った ― 直接 12 件 + 間接 3 件**", self.t)
        self.assertIn("**同じ会計が索引に 2 つの名前で並ぶ**", self.t)
        self.assertIn("= 15 件 / 25 件である。**", self.t)
        self.assertIn("**A-2 を③の成功に数えない**", self.t)
        for cid in ("R023", "R024", "R025"):
            self.assertIn(cid, self.t)

    def test_11_a2_breakdown_matches_the_binds(self):
        a2 = [x["id"] for x in load(BINDS)["A-2_詳細"]]
        self.assertEqual(sorted(a2),
                         ["R002", "R003", "R016", "R018", "R023", "R024", "R025"])
        a1 = [x["id"] for x in load(BINDS)["A-1_詳細"]]
        self.assertEqual(len(a1), 12)
        self.assertEqual(load(BINDS)["A-3_詳細"], [])
        self.assertEqual(load(BINDS)["X-2_詳細"], [])


class G4Test(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.g = load(SCORE)["併測 G-4(③の合否に入れない)"]

    def test_12_unmeasured_for_the_fourth_stage(self):
        self.assertEqual(self.g["den"], 0)
        self.assertEqual(self.g["status"], "未測定")
        self.assertFalse(self.g["evaluable"])
        self.assertEqual(self.g["(a) 両席が一致して保留"]["den"], 0)
        self.assertEqual(self.g["(b) 2 席が食い違って保留"]["den"], 0)
        self.assertIn("## §5 G-4 は **4 段続けて未測定**", self.t,
                      "§5 の見出しが『4 段続けて未測定』を言っていない")
        self.assertEqual(self.t.count("**4 段続けて未測定**"), 2,
                         "見出しと §10 の表の 2 か所で言うこと")
        self.assertIn("| G-4 の分母 | 4(うち両席一致 1) | 6 | 1 | **0** |", self.t)

    def test_13_opportunity_was_secured_but_did_not_fire(self):
        o = load(OPP)
        self.assertEqual(
            o["O-4 抜粋の中で親が 2 通り以上に割れるセル(席が決められない)"], 10)
        self.assertIn("**O-4 = 10 セル**", self.t)
        self.assertIn("**それでも分母は 0 だった。"
                      "報告文が 0 円の数を 1 つも引かなかった。**", self.t)
        self.assertIn("**機会(セル)を材料に入れることはできるが、"
                      "主張になるかは生成に依存する。**", self.t)
        self.assertIn("**G-4 は確率的にしか測れない。**", self.t)
        self.assertIn("**合格扱いにしない。**", self.t)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_14_twelve_predictions_scored(self):
        block = self.t.split("## §7")[1].split("## §8")[0]
        ids = re.findall(r"^\| T-(\d+) \|", block, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 13)))
        rows = [l for l in block.split("\n") if l.startswith("| T-")]
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(1 for l in rows if "**外れ" in l), 4)
        self.assertEqual(sum(1 for l in rows if l.rstrip().endswith("| 当たり |")), 8)

    def test_15_misses_are_kept_and_the_bias_is_named(self):
        self.assertIn("**外れは外れとして残す。封は直さない。**", self.t)
        self.assertIn("**外れた 4 本は全部同じ向きである。**", self.t)
        self.assertIn("**③がどれだけ止めるかを過小に見積もっていた。**", self.t)
        self.assertIn("predict-then-tally-my-bias", self.t)
        self.assertIn("**機会の数を数えておいて、その数を予測に反映していなかった。**",
                      self.t)

    def test_16_seal_predictions_untouched(self):
        """**封の予測の字が動いていないこと。**"""
        seal = text(SEAL)
        self.assertIn("| T-1 | **A-1(③の発火)は 1〜6 件**。"
                      "0 件なら「未測定」として報告する |", seal)
        self.assertIn("| T-5 | **生の G-1 は 40〜65%**", seal)
        self.assertIn("| T-6 | **G-1′ は 55〜80%** |", seal)


class RefusalTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_17_no_comparison_with_m8(self):
        self.assertIn("**生の G-1 24.0% を段 8 の 76.0% と比べない。**", self.t)
        self.assertEqual(load(M8S)["lines"]["G-1 接続の正確さ"]["num"], 19)

    def test_18_seat_agreement_is_not_a_result(self):
        self.assertIn("**席の一致率 100% を成果として書かない。**", self.t)

    def test_19_g7_is_neither_pass_nor_fail(self):
        self.assertIn("**G-7 = 0 を失敗とも成功とも書かない。**", self.t)
        self.assertIn("**接続は 1 件も増やしていない**", self.t)

    def test_20_moku_backing_is_really_one(self):
        self.assertIn("**目の親の裏づけは実質 1 本である。**", self.t)
        self.assertIn("2,555 行すべてで", self.t)
        self.assertIn("**「2 本を要求した」ことと「親の欄を信じた」ことは、"
                      "この材料では区別できない。**", self.t)

    def test_21_no_generalisation_and_untouched_items(self):
        self.assertIn("**汎化は示していない。**", self.t)
        self.assertIn("**②(階層の手がかりの引き継ぎ)には手を付けていない。**", self.t)
        self.assertIn("**項(親 1 成分)で接続が増えるか**は段 9 でも測っていない",
                      self.t)


class DisclosureTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_22_red_commit_disclosed(self):
        self.assertIn("**工程が進むと落ちる門を書いていた。"
                      "同じ型を 1 セッションで 2 か所に書いた。**", self.t)
        self.assertIn("**合わせて 4 つの commit を赤のまま出した**", self.t)
        for s in ("e8673a9", "a0d1310", "7f45b15", "e962416", "c587277"):
            self.assertIn(s, self.t, s)
        self.assertIn("**1 つ目を直した時点で 2 つ目を探していなかった**", self.t)
        self.assertIn("two-place-defect-needs-two-checks", self.t)
        self.assertIn("**工程が進むと必ず落ちる門を書いてはいけない**", self.t)

    def test_23_rule_not_in_the_seal_was_removed(self):
        self.assertIn("**封に無い規則を script が足していたので外した。**", self.t)
        self.assertIn("**重複した行の数(表 2 で 17 行・表 3a で 14 行)を記録した。**",
                      self.t)
        self.assertIn("114 個の値", self.t)

    def test_24_symmetry_audit_came_first(self):
        self.assertIn("8819f61", self.t)
        self.assertIn("`X-1 11 / X-2 8`", self.t)

    def test_25_commit_order_is_machine_checked(self):
        order = ["docs/DOMAIN1_M9_SEAL_2026-10-16.md",
                 "measure/sheet_label_spec_m9_2026-10-16.py",
                 "fixtures/sheet/m9_material_2026-10-16.json",
                 "fixtures/sheet/m9_report_2026-10-16.json",
                 "fixtures/sheet/m9_binds_2026-10-16.json",
                 "fixtures/sheet/m9_answers_seat1_2026-10-16.json"]
        shas = []
        for rel in order:
            out = subprocess.check_output(
                ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                cwd=ROOT).decode().split()
            self.assertTrue(out, rel)
            shas.append(out[-1])
        for a, b in zip(shas, shas[1:]):
            if a == b:
                continue
            self.assertEqual(subprocess.call(
                ["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT), 0,
                "工程の順が逆: %s" % rel)
        for s in ("c03c16f", "22d2ac6", "e8673a9", "a0d1310", "7f45b15", "e962416"):
            self.assertIn(s, self.t, s)

    def test_26_report_generated_once(self):
        r = load(REPORT)
        self.assertEqual(r["runs"], 1)
        self.assertFalse(r["regenerated"])
        self.assertEqual(r["report_chars"], 948)
        self.assertTrue(r["within_limit"])
        self.assertTrue(r["prompt_identical_to_stage4"])


class DocTablesMatchMeasurementTest(unittest.TestCase):
    """**文書の表のセルを採点記録と突き合わせる。**

    文章だけを固定していると、表の数や線を書き換える緩め方が通る
    (変異 V2・V4・V5・V10 が黙った)。
    """

    def setUp(self):
        self.t = text(DOC)
        self.s = load(SCORE)

    def _rows(self, head, tail):
        block = self.t.split(head)[1].split(tail)[0]
        out = []
        for line in block.split("\n"):
            if not line.startswith("|") or "---" in line:
                continue
            out.append([c.strip() for c in line.strip().strip("|").split("|")])
        return out

    def test_28_main_table_matches(self):
        rows = self._rows("## §1 採点 ― **総合は失敗**", "### 併測")
        body = [r for r in rows if r and r[0] not in ("記号",)]
        self.assertEqual(len(body), 6, "線の表が 6 行でない")
        m = self.s["主実験(③)"]
        want = [
            ("A-1", "**12 件**", "≥ 1 件", "○"),
            ("A-3", "**0 件**", "= 0 件", "○"),
            ("E2", "**0 件**", "= 0 件", "○"),
            ("X-2", "**0 件**", "= 0 件", "○"),
            ("G-5", "25 件", "≥ 20", "○"),
            ("**G-1′**", "**46.2%(6/13)**", "≥ 50%", "**×**"),
        ]
        got = [(r[0], r[2], r[3], r[4]) for r in body]
        self.assertEqual(got, want, "表のセルが変わっている")
        # 表の数が採点記録と一致すること
        self.assertEqual(m["A-1 ③が発火した主張"]["count"], 12)
        self.assertEqual(m["G-5 母数"]["count"], 25)
        self.assertEqual("%.1f%%(%d/%d)"
                         % (m["G-1′ ③で止めた主張を除いた接続の正確さ"]["rate"] * 100,
                            m["G-1′ ③で止めた主張を除いた接続の正確さ"]["num"],
                            m["G-1′ ③で止めた主張を除いた接続の正確さ"]["den"]),
                         "46.2%(6/13)")
        # **線は封のまま**。表の中の線が封と一致すること
        self.assertIn("| **G-1′** | ③で止めた主張を除いた接続の正確さ "
                      "| **46.2%(6/13)** | ≥ 50% | **×** |", self.t)

    def test_29_g4_table_matches(self):
        rows = self._rows("### 併測(③の合否に入れない)", "### 記録のみ")
        body = [r for r in rows if r and r[0] != "記号"]
        self.assertEqual(body[0][0], "**G-4 保留の適切さ**")
        self.assertEqual(body[0][1], "**未測定(分母 0)**")
        self.assertEqual(body[0][2], "≥ 80%")
        self.assertEqual(body[0][3], "**4 段続けて未確認**")
        g = self.s["併測 G-4(③の合否に入れない)"]
        self.assertEqual(g["status"], "未測定")
        self.assertEqual(g["den"], 0)

    def test_30_recorded_table_has_the_raw_g1(self):
        rows = self._rows("### 記録のみ(線にしない)", "**G-1′ を成果として書かない。**")
        cells = {r[0]: r[1] for r in rows if len(r) == 2}
        self.assertIn("**生の G-1**", cells)
        r = self.s["記録のみ"]["生の G-1(線にしない)"]
        self.assertEqual(cells["**生の G-1**"],
                         "**%.1f%%(%d/%d)**" % (r["rate"] * 100, r["num"], r["den"]))
        self.assertIn("G-7 正しい接続の増分(新 − 旧)", cells)
        self.assertIn("A-2 ③以外の理由で保留", cells)
        self.assertIn("席の一致率", cells)

    def test_31_no_threshold_in_the_doc_differs_from_the_seal(self):
        """**文書の中の線が封の線と 1 つも違わないこと。**"""
        seal = text(SEAL)
        for line in ("≥ 1 件", "= 0 件", "≥ 20", "≥ 50%", "≥ 80%"):
            self.assertIn(line, seal, line)
            self.assertIn(line, self.t, line)
        # 封に無い線が文書に現れていないこと
        for bad in ("≥ 40%", "≥ 30%", "≥ 10", "≤ 1 件"):
            self.assertNotIn(bad, self.t, "封に無い線が文書に在る: %s" % bad)


class RemainingHolesTest(unittest.TestCase):
    def test_27_holes_listed(self):
        t = text(DOC)
        block = t.split("## §10")[1]
        for s in ("**この材料では原理的にできない**", "**4 段続けて未測定**",
                  "**未着手**", "**まだ 1 件も増えていない**", "**実質 1 本**",
                  "**未測定**。段 9 は「止まる側」しか測っていない"):
            self.assertIn(s, block, s)
        self.assertIn("**新しい封を立てる前に人間の判断が要る。**", block)


if __name__ == "__main__":
    unittest.main()
