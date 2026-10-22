# -*- coding: utf-8 -*-
"""方式 C の直しの記録と結果の文書を固定する。

**数は記録から読み、文書の数と突き合わせる。**
**「上回った」と書いていないこと**と、**外れ(P-10)が外れとして残っていること**も門で見る。
"""
import hashlib
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "errdet_cprime_2026-10-19.json")
OLD = os.path.join(FX, "errdet_score_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_ERRDET_CPRIME_RESULT_2026-10-19.md")


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


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)
        self.K = self.r["**判定(封 §3 の K-1〜K-4)**"]
        self.T = self.r["方式ごとの内訳"]

    def test_1_inputs_are_the_frozen_answers(self):
        for seat, inp in self.r["入力(凍結済みの席の答え)"].items():
            p = os.path.join(ROOT, inp["file"])
            with io.open(p, "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), inp["sha256"], seat)
        self.assertEqual(self.r["費用"], "0 USD(生成なし)")

    def test_2_k1_k2_k4_hold_for_both_seats(self):
        for seat in ("seat1", "seat2"):
            k = self.K[seat]
            self.assertTrue(k["K-1 退化なし"]["満たした"], seat)
            self.assertTrue(k["K-2 上書き 0"]["満たした"], seat)
            self.assertEqual(k["K-2 上書き 0"]["件数"], 0, seat)
            self.assertTrue(k["K-4 C″ ≧ C′"]["満たした"], seat)
            self.assertIn("直った", k["判定"])

    def test_3_detection_counts_equal_a(self):
        for seat in ("seat1", "seat2"):
            a, c = self.T[seat]["A"], self.T[seat]["C′"]
            self.assertEqual(len(a["検出"]), len(c["検出"]), seat)
            self.assertEqual(a["見落とし"], c["見落とし"], seat)
        self.assertEqual(self.T["seat1"]["C′"]["見落とし"], [])
        self.assertEqual(self.T["seat2"]["C′"]["見落とし"], ["R024"])

    def test_4_the_old_cs_four_losses_came_back(self):
        x = self.r["旧 C(2026-10-17)との突き合わせ"]
        old = load(OLD)["A / C の内訳"]
        for seat in ("seat1", "seat2"):
            self.assertEqual(x[seat]["旧 C の見落とし"], old["C %s" % seat]["見落とし"])
            self.assertEqual(x[seat]["旧 C の見落とし"], ["R001", "R004", "R009", "R024"])
        self.assertEqual(x["seat1"]["旧 C の見落としのうち C′ で検出に戻った"],
                         ["R001", "R004", "R009", "R024"])
        self.assertEqual(x["seat2"]["旧 C の見落としのうち C′ で検出に戻った"],
                         ["R001", "R004", "R009"])

    def test_5_unaltered_26_and_added_information(self):
        for seat in ("seat1", "seat2"):
            c = self.T[seat]["C′"]
            self.assertEqual(c["無改変 26"], {"確認済み": 26}, seat)
            self.assertEqual(c["偽警報の id"], [], seat)
            self.assertEqual(self.K[seat]["K-3 足した情報(数)"]["機械確認済み(行 6)"], 26, seat)
        self.assertEqual(self.T["seat1"]["C′"]["出どころ確認済み(行 1)"],
                         ["R001", "R004", "R009", "R024"])
        self.assertEqual(len(self.T["seat2"]["C′"]["出どころ確認済み(行 1)"]), 3)

    def test_6_trap_is_stopped_on_both_seats_and_recorded_separately(self):
        rows = {s: {x["id"]: x for x in self.r["件ごとの記録(35 件 × 2 席)"][s]}
                for s in ("seat1", "seat2")}
        self.assertEqual((rows["seat1"]["R035"]["席"], rows["seat1"]["R035"]["C′"],
                          rows["seat1"]["R035"]["行"]), ("確認済み", "検出", 7))
        self.assertEqual((rows["seat2"]["R035"]["席"], rows["seat2"]["R035"]["C′"],
                          rows["seat2"]["R035"]["行"]), ("検出", "検出", 2))
        for s in ("seat1", "seat2"):
            self.assertNotIn("R035", self.T[s]["C′"]["偽警報の id"], "罠は別記")

    def test_7_c_double_prime_changes_no_state_and_adds_the_core_row(self):
        self.assertEqual(self.r["C′ と C″ が違う id"], {"seat1": [], "seat2": []})
        for s in ("seat1", "seat2"):
            self.assertEqual(self.T[s]["C″"]["検出-2 正しい行(Core の行)"],
                             ["R004", "R009", "R010", "R012"], s)
            self.assertEqual(self.T[s]["C′"]["検出-2 正しい行(席の住所)"], [], s)

    def test_8_predictions_nine_hits_one_miss_and_p10_is_the_miss(self):
        self.assertEqual(self.r["予測の集計"], {"当たり": 9, "外れ": 1})
        miss = [p["id"] for p in self.r["予測(封 §4)"] if p["判定"] == "外れ"]
        self.assertEqual(miss, ["P-10"])
        self.assertEqual(self.r["封の M-3 での無改変の保留"], {"seat1": 22, "seat2": 22})
        self.assertEqual(self.T["seat2"]["C′(封の M-3)"]["見落とし"], [])
        self.assertEqual(self.T["seat2"]["C′(封の M-3)"]["保留"], ["R024"])

    def test_9_the_seat_answers_were_not_rewritten_by_the_run(self):
        # 記録の件ごとの住所は、凍結済みの答えの 6 欄そのもの
        for s in ("seat1", "seat2"):
            ans = {x["id"]: x for x in load(os.path.join(
                FX, "errdet_answers_%s_2026-10-17.json" % s))["answers"]}
            for row in self.r["件ごとの記録(35 件 × 2 席)"][s]:
                a = ans[row["id"]]
                if row["出どころの行(席)"] is not None:
                    for k in ("会計", "階層", "親", "科目名", "列", "値"):
                        self.assertEqual(row["出どころの行(席)"][k], a.get(k), (s, row["id"], k))


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = load(REC)

    def test_10_the_doc_numbers_match_the_record(self):
        b = sec(self.t, "## §1", "## §2")
        K = self.r["**判定(封 §3 の K-1〜K-4)**"]
        self.assertIn("機械確認済み **%d**・出どころ確認済み **%d**"
                      % (K["seat1"]["K-3 足した情報(数)"]["機械確認済み(行 6)"],
                         K["seat1"]["K-3 足した情報(数)"]["出どころ確認済み(行 1)"]), b)
        self.assertIn("機械確認済み **%d**・出どころ確認済み **%d**"
                      % (K["seat2"]["K-3 足した情報(数)"]["機械確認済み(行 6)"],
                         K["seat2"]["K-3 足した情報(数)"]["出どころ確認済み(行 1)"]), b)
        self.assertIn("| seat1 | **C′** | **8** | 0 | **0** | **0** | 確認済み 26 |", b)
        self.assertIn("| seat2 | **C′** | **7** | 0 | **1** | **0** | 確認済み 26 |", b)
        self.assertIn("**保留 22**・確認済み 4", b)

    def test_11_prediction_tally_and_the_miss_are_in_the_doc(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertIn("**当たり 9 / 外れ 1。**", b)
        self.assertRegex(b, r"\| \*\*P-10\*\* \|.*\| \*\*外れ\*\* \|")
        self.assertEqual(len(re.findall(r"\| \*\*当たり\*\* \|", b)), 9)
        self.assertIn("**「M-3′ と同じ」と書いた私の予測は", b)

    def test_12_it_does_not_claim_c_beat_a(self):
        # 「上回った」は否定の形(〜とは書かない)でしか出ない
        for m in re.finditer(r"上回った", self.t):
            ctx = self.t[max(0, m.start() - 20):m.end() + 12]
            self.assertTrue("とは書かない" in ctx or "と書かない" in ctx, ctx)
        self.assertIn("**検出数は増えていない。**", self.t)

    def test_13_limits_name_the_reuse_and_the_trap_cost(self):
        b = sec(self.t, "## §4", "## §5")
        self.assertIn("**同じ材料・同じ答えの再利用である。**", b)
        self.assertIn("**別資料で同じ数が出るかは測っていない**", b)
        self.assertIn("偽警報が 1 件増えた", b)
        self.assertIn("**どちらの定義を製品にするかは決めていない。**", b)

    def test_14_the_seal_commit_named_in_the_doc_is_the_one_that_added_the_seal(self):
        import subprocess
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h", "--",
                              "docs/DOMAIN1_ERRDET_CPRIME_SEAL_2026-10-19.md"],
                             cwd=ROOT, capture_output=True, text=True).stdout.split()
        if not out:
            self.skipTest("封が未 commit")
        self.assertIn("commit `%s`" % out[-1][:7], self.t)


if __name__ == "__main__":
    unittest.main()
