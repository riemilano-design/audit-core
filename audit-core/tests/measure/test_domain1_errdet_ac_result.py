# -*- coding: utf-8 -*-
"""A 対 C の採点・追記・結果の文書を固定する。

**数は記録から読み、文書の数と突き合わせる。**
**「上回った」と書いていないこと**と、**私の設計が負けたと書いてあること**も門で見る。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
SCORE = os.path.join(FX, "errdet_score_2026-10-17.json")
ADD = os.path.join(FX, "errdet_addendum_2026-10-17.json")
MATREC = os.path.join(FX, "errdet_material_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_ERRDET_AC_RESULT_2026-10-17.md")
A1, A2, C1, C2 = "A seat1", "A seat2", "C seat1", "C seat2"


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


class AnswersAndCostTest(unittest.TestCase):
    def setUp(self):
        self.recs = {s: load(os.path.join(
            FX, "errdet_answers_%s_2026-10-17.json" % s))
            for s in ("seat1", "seat2")}

    def test_1_one_run_no_retry_nothing_failed(self):
        for s, r in self.recs.items():
            self.assertEqual(r["runs"], 1, s)
            self.assertFalse(r["regenerated"], s)
            self.assertEqual(r["機械検査に落ちた件"], [], s)
            self.assertEqual(r["足した欄で落ちた件"], [], s)
            self.assertEqual(len(r["answers"]), 35, s)

    def test_2_the_task_is_the_sealed_material(self):
        want = {f["seat"]: f["sha256"] for f in load(MATREC)["files"]}
        for s, r in self.recs.items():
            self.assertEqual(r["task_sha256"], want[s], s)

    def test_3_cost_inside_the_cap(self):
        total = round(sum(r["費用"]["費用の上限(全部が出力だと仮定)"]
                          for r in self.recs.values()), 4)
        self.assertEqual(total, 1.8692)
        self.assertLessEqual(total, 4.0)
        self.assertTrue(self.recs["seat2"]["費用の累計"]["上限の中か"])


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.r = load(SCORE)
        self.v = {x["席"]: x for x in self.r["**判定(封 §5-4 の G-1・G-2)**"]}
        self.d = self.r["A / C の内訳"]

    def test_4_input_difference_is_zero(self):
        self.assertTrue(self.r["**A と C は同じ生成を共有する(入力差ゼロ)**"])
        self.assertTrue(self.r["**主比較は A 対 C。B は参考群**"])

    def test_5_g1_failed_and_g2_passed_for_both_seats(self):
        for seat in ("seat1", "seat2"):
            j = self.v[seat]
            self.assertFalse(j["G-1 見落としが減る"]["満たした"], seat)
            self.assertTrue(j["G-2 偽警報が増えない"]["満たした"], seat)
            self.assertEqual(j["判定"], "**G-2 のみ**", seat)

    def test_6_a_detected_more_than_c(self):
        self.assertEqual(len(self.d[A1]["検出"]), 8)
        self.assertEqual(len(self.d[A2]["検出"]), 7)
        self.assertEqual(len(self.d[C1]["検出"]), 4)
        self.assertEqual(len(self.d[C2]["検出"]), 4)
        self.assertEqual(self.d[A1]["見落とし"], [])
        self.assertEqual(self.d[A2]["見落とし"], ["R024"])
        self.assertEqual(self.d[C1]["見落とし"],
                         ["R001", "R004", "R009", "R024"])

    def test_7_the_four_losses_are_the_group_two_errors(self):
        """**検証が席の申告を捨てた 4 件は、全部群 II である。**"""
        err = {e["id"]: e for e in self.r["誤りの件ごと"][C1]}
        for cid in ("R001", "R004", "R009", "R024"):
            self.assertEqual(err[cid]["群"], "群 II", cid)
            self.assertTrue(err[cid]["見落とし"], cid)
        a = {e["id"]: e for e in self.r["誤りの件ごと"][A1]}
        for cid in ("R001", "R004", "R009", "R024"):
            self.assertTrue(a[cid]["検出-1 誤りだと言えた"], cid)
            self.assertTrue(a[cid]["検出-3 一致"], cid)

    def test_8_no_false_alarms_anywhere_on_the_unaltered_26(self):
        for arm in (A1, A2, C1, C2):
            self.assertEqual(self.d[arm]["偽警報の id"], [], arm)
            self.assertEqual(self.d[arm]["無改変(26 件。罠は別記)"],
                             {"確認済み": 26}, arm)

    def test_9_kind_identification(self):
        self.assertEqual(len(self.d[A1]["検出-3 種類を特定"]), 8)
        self.assertEqual(len(self.d[A2]["検出-3 種類を特定"]), 7)
        self.assertEqual(len(self.d[C1]["検出-3 種類を特定"]), 4)
        self.assertEqual(len(self.r["B(参考群)"]["検出-3 種類を特定"]), 2)

    def test_10_both_m3_definitions_are_recorded(self):
        self.assertEqual(self.d[C1]["封の M-3 での見落とし"], ["R009"])
        self.assertEqual(self.d[C2]["封の M-3 での見落とし"], ["R009"])
        self.assertEqual(self.d[A1]["封の M-3 での見落とし"], [])

    def test_11_the_trap_is_recorded_separately(self):
        k = "罠(R035)"
        self.assertFalse(self.d[A1][k]["**文書は正しいのに一致しないと言ったか**"])
        self.assertTrue(self.d[A2][k]["**文書は正しいのに一致しないと言ったか**"])
        self.assertEqual(self.d[A2][k]["種類の申告"], "単位・符号の表記")
        self.assertTrue(self.d[C1][k]["**文書は正しいのに一致しないと言ったか**"])

    def test_12_the_two_gaps_were_fixed_before_seeing_the_answers(self):
        got = self.r["封が書いていなかった 2 点をここで決めた(答えを見る前に commit した)"]
        self.assertEqual(len(got), 2)
        self.assertIn("不一致の申告", got[0])
        self.assertIn("席の答えをそのまま引き継ぐ", got[1])


class AddendumTest(unittest.TestCase):
    def setUp(self):
        self.r = load(ADD)

    def test_13_the_two_arms_point_at_different_rows(self):
        m = self.r["方式ごと"]
        self.assertEqual(m[A1]["追-1 改変前の正しい行を指した"]["件数"], 0)
        self.assertEqual(m[A1]["追-2 植えた値の出どころを指した"]["ids"],
                         ["R001", "R004", "R009", "R024"])
        b = m["B(参考群)"]
        self.assertEqual(b["追-1 改変前の正しい行を指した"]["件数"], 4)
        self.assertEqual(b["追-2 植えた値の出どころを指した"]["件数"], 0)

    def test_14_the_addendum_is_not_used_for_the_verdict(self):
        self.assertIn("合否にこの数を使わない", self.r["step"])
        self.assertIn("**合否(G-1・G-2)にこの数を使っていない。**",
                      " ".join(self.r["limits"]))

    def test_15_core_holds_14_of_the_unaltered_26(self):
        b = self.r["方式ごと"]["B(参考群)"]["無改変 26 件"]
        self.assertEqual(b["保留"], 14)
        self.assertEqual(b["確認済み"], 12)
        self.assertEqual(b["偽警報"], 0)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_16_the_order_follows_the_human_instruction(self):
        i = self.t.index("# 第 1 部 封印済みの基準に対する合否")
        j = self.t.index("# 第 2 部 誤りの種類別の内訳")
        k = self.t.index("# 第 3 部 次の投資判断")
        self.assertLess(i, j)
        self.assertLess(j, k)
        self.assertIn("**① 封印済みの基準に対する合否 → ② 誤りの種類別の内訳 → "
                      "③ 次の投資判断。**", self.t[:i])

    def test_17_it_does_not_claim_c_won(self):
        b = sec(self.t, "## §1-1", "## §1-2")
        self.assertIn("**G-2 のみ合格**", b)
        self.assertIn("**だから上回っていない。**", b)
        self.assertIn("**偽警報を増やさずに見落としを減らす効果は未確認**", b)

    def test_18_my_design_is_named_as_the_cause(self):
        b = sec(self.t, "## §1-3", "## §1-4")
        self.assertIn("**これは実装の都合ではない。2 手前に私が提案した"
                      "設計そのものの欠陥である。**", b)
        self.assertIn("**しかし測っていない。だから値打ちを主張しない。**", b)
        rows = re.findall(r"(?m)^\| `R0(\d\d)` ", b)
        self.assertEqual(rows, ["01", "04", "09", "24"], "4 件を字で並べる")

    def test_19_the_seal_gap_is_disclosed(self):
        b = sec(self.t, "## §1-7", "# 第 2 部")
        self.assertIn("**A 対 C の予測を 1 本も書いていない。**", b)
        self.assertIn("**これは私の封の穴である。", b)

    def test_20_the_type_breakdown_is_there(self):
        b = sec(self.t, "## §2-1", "## §2-2")
        for k in ("**I-1 桁の入れ替え**", "**I-2 末尾 1 桁の差**",
                  "**II-1 列の取り違え**", "**II-2 別の科目の値**"):
            self.assertIn(k, b, k)
        self.assertIn("**群 I(原資料に無い値)は全方式が得意だった。**", b)
        self.assertIn("**群 II(値は在るが参照先が違う)で方式が割れた。**", b)
        d = sec(self.t, "## §2-2", "## §2-3")
        self.assertIn("**顧客に渡せる説明の粒度では、LLM が明確に上だった。**", d)
        self.assertIn("**通常の報告文を自然に読む場面での検出性能とは区別する**", d)

    def test_21_the_addendum_is_marked_as_not_part_of_the_verdict(self):
        b = sec(self.t, "## §2-3", "# 第 3 部")
        self.assertIn("追記(合否には使わない)", b)
        self.assertIn("**2 つの方式は別の行を指している。**", b)
        self.assertIn("**ただしこれは測っていない。**", b)

    def test_22_the_investment_options_are_separated_and_not_a_proof(self):
        b = sec(self.t, "# 第 3 部")
        self.assertIn("**人工の誤りでの合格を、顧客価値や売却価値の証明にしない**", b)
        self.assertIn("**以下は投資の選択肢であって、価値の証明ではない。**", b)
        opts = re.findall(r"(?m)^\| \*\*\((\d)\)\*\*", b)
        self.assertEqual(opts, ["1", "2", "3"], "選択肢は 3 つ")
        self.assertIn("**どれを選ぶかは人間の判断である。**", b)
        limits = sec(self.t, "## §3-2", "## §3-3")
        nums = re.findall(r"(?m)^(\d)\. ", limits)
        self.assertEqual(nums, [str(i) for i in range(1, 8)], "限界は 7 本")


if __name__ == "__main__":
    unittest.main()
