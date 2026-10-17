# -*- coding: utf-8 -*-
"""0 USD の事前確認(docs/XBRL_CD_DRYRUN_2026-10-17.md)の門。

**数は記録 `fixtures/xbrl/cd8/dryrun_2026-10-17.json` を正本にし、
文書に書いた数が記録と食い違ったら赤くする**(記憶 `count-lines-not-guesses`)。
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_CD_DRYRUN_2026-10-17.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "dryrun_2026-10-17.json")
DRAW = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "draw_2026-10-17.json")
SCRIPT = os.path.join(ROOT, "measure", "xbrl_cd_dryrun_2026-10-17.py")
STRUCT_KEY = "構造(**使用済みの書類で測った。新しい 8 件は開いていない**)"


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


class NoGenerationTest(unittest.TestCase):
    def test_1_the_run_called_no_seat_and_opened_no_new_doc(self):
        t = text(DOC)
        self.assertIn("**費用 0 USD。席を 1 回も呼んでいない。"
                      "新しい 8 書類を 1 件も開いていない。**", t)
        r = rec()
        self.assertIn("**費用 0 USD・生成なし**", r["step"])
        used = r[STRUCT_KEY]["参考にした書類"]
        self.assertEqual(len(used), 8)
        self.assertFalse(set(used) & set(r["引いた 8 件"]),
                         "**参考書類と引いた書類が重なっている**")

    def test_2_the_key_value_is_never_recorded(self):
        """鍵の値は記録に出ない。**名前だけ。**"""
        blob = json.dumps(rec(), ensure_ascii=False) + text(DOC)
        self.assertIn("EDINET_API_KEY", blob)
        self.assertIn("**値は読まない・書かない**", text(DOC))
        self.assertNotIn("Subscription-Key", blob)
        # 32 桁以上の英数の連なり(鍵の形)が無いこと
        self.assertEqual([], [s for s in re.findall(r"[A-Za-z0-9]{32,}", blob)
                              if not re.fullmatch(r"[0-9a-f]{32,}", s)],
                         "**鍵らしい字が記録に在る**")


class NumbersMatchTheRecordTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_3_cost_band_in_the_doc_equals_the_record(self):
        b = self.r["費用の実測見積もり"]["見積もりの帯"]
        lo = b["8 便 1 席の上限 USD(低い側)"]
        hi = b["8 便 1 席の上限 USD(高い側)"]
        self.assertIn("**%.2f 〜 %.2f USD**" % (lo, hi), self.t)
        self.assertFalse(self.r["費用の実測見積もり"]["**目安の中か**"])
        self.assertIn("**いいえ(5〜6 倍)**", self.t)
        self.assertEqual(self.r["費用の実測見積もり"]["人間の目安"], 3.0)

    def test_4_t5_zero_docs_are_named(self):
        per = self.r[STRUCT_KEY]["書類ごと"]
        zero = [p["docID"] for p in per
                if p["注入できる site の数"]["T5_COINCIDENT"] == 0]
        self.assertEqual(len(zero), 3, "T5 が 0 件の書類は 3 件")
        for d in zero:
            self.assertIn("**`%s`**" % d, self.t, "%s が太字で挙がっていない" % d)
        self.assertIn("3 書類で 0 件", self.t)

    def test_5_material_sizes_match(self):
        per = self.r[STRUCT_KEY]["書類ごと"]
        avg_t = int(sum(p["本文の字数"] for p in per) / float(len(per)))
        avg_r = int(sum(p["refs を 1 行にした字数"] for p in per) / float(len(per)))
        self.assertIn("**{:,}**".format(avg_t), self.t)
        self.assertIn("**{:,}**".format(avg_r), self.t)
        share = 100 * avg_r / float(self.r["費用の実測見積もり"]["見積もりの帯"]
                                   ["1 便の材料の字数(平均の見込み)"])
        self.assertIn("その %d%% が `refs` である" % round(share), self.t)

    def test_6_collision_histogram_matches(self):
        per = self.r[STRUCT_KEY]["書類ごと"]
        tot = {}
        for p in per:
            for k, v in p["同じ値を持つ fact の数 n"].items():
                tot[k] = tot.get(k, 0) + v
        for key, label in (("n=1", "n = 1(値が一意)"), ("n=2〜5", "n = 2〜5"),
                           ("n>=6", "n ≥ 6")):
            self.assertIn("| {} | **{:,}** |".format(label, tot[key]), self.t)
        s = sum(tot.values())
        self.assertIn("8 書類の合計 {:,} 件".format(s), self.t)
        pct = round(100.0 * (tot["n=2〜5"] + tot["n>=6"]) / s)
        self.assertIn("**値が一意でない fact は %d%%** ある" % pct, self.t)

    def test_7_draw_record_matches_the_doc(self):
        d = json.load(io.open(DRAW, encoding="utf-8"))
        for doc in d["引いた 8 件"]:
            self.assertIn("`%s`" % doc, self.t)
        self.assertIn("**飛ばした件: %d 件**" % len(d["飛ばした件"]), self.t)
        self.assertIn("**規則を満たす書類は %d 件**" % d["規則を満たす書類"], self.t)
        self.assertEqual(d["**キャッシュに在るか**"]["在った"], [])


class OptionsAndLimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_8_four_options_and_i_do_not_decide(self):
        i = self.t.index("## §3-2")
        b = self.t[i:self.t.index("## §4", i)]
        ids = re.findall(r"(?m)^\| \*\*\((ア|イ|ウ|エ)\)\*\*", b)
        self.assertEqual(ids, ["ア", "イ", "ウ", "エ"], "選択肢は 4 つ")
        self.assertIn("**私は決めない**", b)
        self.assertIn("**私は (ア) → 結果を見て (ウ) を推す。**", b)
        self.assertIn("**ただし (ア) は未使用データの主張にはならない。**", b)
        self.assertIn("失うもの", b, "**選択肢に代価の欄が無い**")

    def test_9_six_limits_including_opportunity_vs_firing(self):
        b = self.t[self.t.index("## §4 示せないこと"):]
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 7)], "限界は 6 本")
        self.assertIn("`opportunity-in-material-does-not-mean-it-fires`", b)
        self.assertIn("**どの方式が勝つかは 1 つも測っていない。**", b)

    def test_10_the_stop_quotes_the_seal(self):
        self.assertIn("**止めた。規模を削っていない。封の条件も変えていない。**", self.t)
        self.assertIn("規模を自分で勝手に削らない", self.t)

    def test_11_the_script_does_not_call_any_seat(self):
        """**配線で確かめる** ― 下見の script に席を呼ぶ道が無い。"""
        s = text(SCRIPT)
        for bad in ("anthropic", "Task(", "subagent", "messages.create"):
            self.assertNotIn(bad, s, bad)
        self.assertIn("**席を 1 回も呼ばない。生成しない。", s)


if __name__ == "__main__":
    unittest.main()
