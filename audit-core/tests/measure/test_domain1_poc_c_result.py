# -*- coding: utf-8 -*-
"""方式 C の記録と結果の文書を固定する(封 docs/DOMAIN1_POC_C_SEAL_2026-10-17.md)。

**数は記録から読み、文書の数と突き合わせる。**
**第 1 便の本文が書き換えられていないこと**も門で見る(訂正は追記で足した)。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_POC_C_RESULT_2026-10-17.md")
ABDOC = os.path.join(ROOT, "docs", "DOMAIN1_POC_AB_RESULT_2026-10-17.md")
MAT = os.path.join(FX, "poc_c_material_2026-10-17.json")
SCORE = os.path.join(FX, "poc_c_score_2026-10-17.json")
SIGN = os.path.join(FX, "poc_sign_defect_2026-10-17.json")
DELTA = os.path.join(FX, "poc_c_delta_2026-10-17.json")
A1, A2 = "A1 一般 LLM(sonnet)", "A2 一般 LLM(haiku)"
C1, C2 = "C1 一般 LLM + 証拠(sonnet)", "C2 一般 LLM + 証拠(haiku)"
B = "B Audit Core"


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class AnswersTest(unittest.TestCase):
    def setUp(self):
        self.recs = {s: load(os.path.join(
            FX, "poc_c_answers_%s_2026-10-17.json" % s))
            for s in ("seat1", "seat2")}
        self.mat = load(MAT)

    def test_1_one_run_no_retry_nothing_failed_the_check(self):
        for s, r in self.recs.items():
            self.assertEqual(r["runs"], 1, s)
            self.assertFalse(r["regenerated"], s)
            self.assertEqual(r["機械検査に落ちた件"], [], s)
            self.assertEqual(len(r["answers"]), 35, s)
            self.assertEqual(len({a["id"] for a in r["answers"]}), 35, s)

    def test_2_the_task_is_the_sealed_material(self):
        want = {f["seat"]: f for f in self.mat["files"]}
        for s, r in self.recs.items():
            self.assertEqual(r["task_sha256"], want[s]["C の sha256"], s)
            self.assertTrue(r["A が接頭"], s)
            self.assertEqual(r["model"], want[s]["model"], s)
            self.assertEqual(r["order"], want[s]["order"], s)

    def test_3_cost_is_measured_and_inside_the_cap(self):
        rates = {"seat1": 15.0, "seat2": 5.0}
        total = 0.0
        for s, r in self.recs.items():
            c = r["費用"]
            self.assertEqual(c["単価(出力・USD/1M)"], rates[s])
            self.assertEqual(
                c["費用の上限(全部が出力だと仮定)"],
                round(c["使ったトークン(実測)"] * rates[s] / 1e6, 4), s)
            total += c["費用の上限(全部が出力だと仮定)"]
        self.assertLessEqual(round(total, 4), 4.0, "**上限を超えている**")
        self.assertEqual(round(total, 4), 1.9595)
        self.assertEqual(
            self.recs["seat2"]["費用の累計"]["2 席の合計の上限"], 1.9595)
        self.assertTrue(self.recs["seat2"]["費用の累計"]["上限の中か"])


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.r = load(SCORE)
        self.m = self.r["主採点(寛容な会計)"]

    def test_4_a_was_rescored_and_reproduced(self):
        self.assertTrue(self.r["A を採り直して記録と一致"])
        self.assertIn("import", self.r["採点器"])

    def test_5_c_equals_a_on_every_sealed_metric(self):
        for c, a in ((C1, A1), (C2, A2)):
            for k in ("M-1 誤接続率", "M-2 回収率", "M-3 根拠の再現性"):
                self.assertEqual(self.m[c][k], self.m[a][k], "%s / %s" % (c, k))
            self.assertEqual(self.m[c]["別枠"], self.m[a]["別枠"], c)
        self.assertEqual(self.m[C1]["M-2 回収率"]["num"], 24)
        self.assertEqual(self.m[C1]["M-1 誤接続率"]["num"], 0)
        self.assertEqual(self.m[B]["M-2 回収率"]["num"], 12)

    def test_6_strict_scope_is_reported_too(self):
        st = self.r["**厳格な会計(印字のみ)。埋もれさせない**"]
        for name in (A1, A2, C1, C2):
            self.assertEqual(st[name]["M-2 回収率"]["num"], 24, name)
            self.assertEqual(st[name]["M-1 誤接続率"]["num"], 0, name)
        self.assertEqual(st[B]["M-2 回収率"]["num"], 12)

    def test_7_detection_did_not_improve(self):
        d3 = self.r["D-3 不整合の検出"]
        key = "**根拠のない確認(35 件すべてで)**"
        for name in (A1, A2, C1, C2):
            self.assertEqual(d3[name][key]["ids"], ["R035"], name)
            self.assertEqual(d3[name]["検出できた件数(確認しなかった)"], 0, name)
        self.assertEqual(d3[B][key]["件数"], 0)
        self.assertEqual(d3[B]["検出できた件数(確認しなかった)"], 1)

    def test_8_the_follow_rate_cannot_tell_following_from_agreement(self):
        """**A も 16/16 である**(指標の欠陥。文書で開示する)。"""
        d1 = self.r["D-1 追随率"]
        for name in (A1, A2, C1, C2):
            self.assertEqual(d1[name]["同じ行を答えた"], 16, name)
            self.assertEqual(d1[name]["道具が特定し、この方式も接続した件"], 16)

    def test_9_the_verdict_is_no_difference_for_both_seats(self):
        v = self.r["D-4 と判定(**席はモデルで対にする**)"]
        self.assertEqual(len(v), 2)
        for x in v:
            self.assertIn("差が出なかった", x["判定"])
            self.assertEqual(x["内訳"]["D-4 A から落ちた件"], [])
            self.assertEqual(x["内訳"]["A に無く C で正しくなった件"], [])
            self.assertEqual(x["内訳"]["誤接続の差"], 0)
            self.assertEqual(x["内訳"]["回収の差"], 0)
            self.assertEqual(x["内訳"]["検出の差"], 0)

    def test_10_the_input_was_a_plus_evidence_only(self):
        self.assertTrue(self.r["入力"]["A が接頭"])
        self.assertTrue(self.r["入力"]["**B′ は使っていない**"])


class SignDefectTest(unittest.TestCase):
    def setUp(self):
        self.r = load(SIGN)

    def test_11_one_claim_lost_its_sign_and_it_is_r035(self):
        self.assertEqual(self.r["直前に負の印が在る主張"]["ids"], ["R035"])
        d = self.r["明細"][0]
        self.assertEqual(d["印"], "マイナス")
        self.assertEqual(d["切り出した値"], 48327000)
        self.assertEqual(d["符号を直した値"], -48327000)
        self.assertEqual(d["道具が出した行の値"], -48327000)

    def test_12_fixing_the_sign_would_put_it_in_the_gold_set(self):
        d = self.r["明細"][0]
        self.assertEqual(d["封の第 1 段(変えない)"], "値が不一致")
        self.assertEqual(d["符号を直したときの第 1 段"], "値の候補が一意")
        self.assertTrue(d["符号を直したら正解集合に入るか"])
        self.assertEqual(d["符号を直したときの第 2 段"]["欠けた条件"], [])

    def test_13_every_seat_wrote_the_negative_value(self):
        d = self.r["明細"][0]
        self.assertEqual(sorted(set(d["席が書いた値"].values())), [-48327000])
        self.assertTrue(all(d["席の値が正本の行と一致"].values()))

    def test_14_the_sealed_numbers_were_not_rewritten(self):
        self.assertTrue(self.r["**封の正解基準・正解集合・採点の数は書き換えていない**"])
        gold = load(os.path.join(FX, "poc_gold_2026-10-17.json"))
        self.assertEqual(gold["正解集合"]["件数"], 24, "**封の正解集合が動いた**")
        row = [r for r in gold["rows"] if r["id"] == "R035"][0]
        self.assertEqual(row["第 1 段"], "値が不一致")
        self.assertIsNone(row["正解"])


class DeltaTest(unittest.TestCase):
    def test_15_the_answers_barely_changed(self):
        r = load(DELTA)
        s1, s2 = r["席ごと"]["seat1"], r["席ごと"]["seat2"]
        self.assertEqual((s1["同じ答え"], s1["違った答え"]), (35, 0))
        self.assertEqual((s2["同じ答え"], s2["違った答え"]), (34, 1))
        d = s2["違った件"][0]
        self.assertEqual(d["id"], "R031")
        self.assertEqual(d["違った欄"], ["会計"])
        self.assertEqual(d["A"]["会計"].strip(), d["C"]["会計"].strip(),
                         "違いは末尾の空白だけ")
        self.assertIn("2 つの LLM が一致した", r["注"])


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.s = load(SCORE)

    def test_16_three_layers_and_the_verdict(self):
        for k in ("# 第 1 層 判定", "# 第 2 層 観測", "# 第 3 層 解釈"):
            self.assertIn(k, self.t, k)
        b = sec(self.t, "## §1-1", "## §1-2")
        self.assertIn("**だから「改善した」とは書かない。"
                      "判定は「差が出なかった」である。**", b)
        rows = re.findall(r"(?m)^\| (\d) ", b)
        self.assertEqual(rows, ["1", "2", "3"], "成功条件 3 本")
        self.assertIn("**満たさない**", b)

    def test_17_the_human_branch_is_quoted_and_followed(self):
        b = sec(self.t, "## §1-2", "## §1-3")
        self.assertIn("C の拡張を止める", b)
        self.assertIn("**この分岐に当たる。**", b)
        self.assertIn("**5 件**", b, "候補範囲実験の数を字で")

    def test_18_the_numbers_in_the_doc_match_the_record(self):
        m = self.s["主採点(寛容な会計)"]
        b = sec(self.t, "## §2-1", "## §2-2")
        self.assertIn("**24/24 (100.0%)**", b)
        self.assertIn("12/24 (50.0%)", b)
        self.assertIn("6/35 (17.1%)", b)
        self.assertIn("34/35 (97.1%)", b)
        self.assertIn("**16/16 (100.0%)**", b)
        self.assertEqual(m[C1]["M-2 回収率"]["num"], 24)
        self.assertEqual(m[B]["M-3 根拠の再現性"]["num"], 1)
        cost = sec(self.t, "## §2-6", "## §2-7")
        self.assertIn("103,778", cost)
        self.assertIn("80,562", cost)
        self.assertIn("**1.9595 USD**", cost)
        self.assertIn("**目標 0.5 USD は満たせなかった。"
                      "これは実行前に封 §7 に書いたとおりである。**", cost)

    def test_19_my_two_defects_are_disclosed(self):
        b = sec(self.t, "## §2-3", "## §2-4")
        self.assertIn("**A は証拠を見ていないのに 16/16 である。**", b)
        self.assertIn("**この指標は設計が悪い。**", b)
        s = sec(self.t, "## §2-7", "## §2-8")
        self.assertIn("**つまりこの 1 件では、報告文は正しい。"
                      "誤っていたのは私の切り出しの符号である。**", s)
        self.assertIn("**封の正解基準・正解集合・A / B / C の採点の数は "
                      "1 つも書き換えていない。**", s)
        self.assertIn("**規則は直していない。直しは別の封で切る。**", s)

    def test_20_predictions_are_tallied_with_the_misses_and_their_direction(self):
        b = sec(self.t, "## §2-8", "# 第 3 層")
        xs = re.findall(r"(?m)^\| X-(\d) ", b)
        ys = re.findall(r"(?m)^\| Y-(\d) ", b)
        self.assertEqual(xs, [str(i) for i in range(1, 7)], "盲検 6 本")
        self.assertEqual(ys, [str(i) for i in range(1, 6)], "既知 5 本")
        self.assertEqual(b.count("**外れ**"), 3, "外れは 3 本")
        self.assertIn("**3 本とも同じ向きに外れた。**", b)
        self.assertIn("predict-then-tally-my-bias", b)

    def test_21_the_first_delivery_conclusion_is_corrected(self):
        b = sec(self.t, "## §3-2", "## §3-3")
        self.assertIn("**したがって、この材料で Core が一般 LLM に"
                      "勝っている点は 0 件である。**", b)
        self.assertIn("**第 1 便の結果の文書には、日付つきの追記でこの訂正を足した。"
                      "本文は書き換えていない。**", b)

    def test_22_what_is_not_measured(self):
        b = sec(self.t, "## §4 示せないこと", "## §5")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 11)], "限界は 10 本")
        self.assertIn("**(新)席が証拠を読んだかどうかを測っていない。**", b)
        self.assertIn("**Core の価値を測るには、一般 LLM が誤接続する材料が要る。**",
                      sec(self.t, "## §3-3", "## §3-4"))

    def test_23_the_doc_does_not_claim_improvement(self):
        self.assertNotIn("改善した**", sec(self.t, "# 第 1 層", "# 第 2 層")
                         .replace("「改善した」とは書かない", ""))
        self.assertIn("**差が出なかったことを、差が出なかったと書いた。**", self.t)
        self.assertIn("**開発を続ける理由を、この結果から作らない。**", self.t)


class FirstDeliveryUntouchedTest(unittest.TestCase):
    """**本文は書き換えず、追記で訂正した**ことを門で見る。"""

    def setUp(self):
        self.t = text(ABDOC)

    def test_24_the_body_still_holds_the_original_claim(self):
        self.assertIn("**偽の確認: A 1 件 / B 0 件** ― **Core の唯一の明確な勝ち。**",
                      self.t)
        self.assertIn("**この分岐に当たる。**", self.t)

    def test_25_the_addendum_is_dated_and_corrects_it(self):
        b = sec(self.t, "## §8 追記")
        self.assertIn("2026-10-17", b)
        self.assertIn("本文は書き換えていない**)", b)
        self.assertIn("Core の勝ちではなかった", b)
        self.assertIn("**したがって「保留によって防げた誤り」は 0 件である。**", b)
        self.assertIn("poc_sign_defect_2026-10-17.json", b)


if __name__ == "__main__":
    unittest.main()
