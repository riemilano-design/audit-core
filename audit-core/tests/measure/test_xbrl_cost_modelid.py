# -*- coding: utf-8 -*-
"""① の続き(モデル ID と単価の候補)の門。

**数は記録 JSON を正本に突き合わせる。**
**鍵らしい字が出力と csv に無いことを機械で見る。**
"""
import csv
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "model_rates_2026-10-17.json")
CSV_P = os.path.join(FX, "seat_runs_for_console_2026-10-17.csv")
DOC = os.path.join(ROOT, "docs", "XBRL_COST_MODELID_2026-10-17.md")
SEAL = os.path.join(ROOT, "docs", "XBRL_CD_SEAL_2026-10-17.md")
KEYISH = re.compile(r"[A-Za-z0-9]{32,}")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class ModelIdTest(unittest.TestCase):
    def setUp(self):
        self.r = json.load(io.open(REC, encoding="utf-8"))
        self.t = text(DOC)

    def test_1_every_model_string_in_the_record_is_in_the_doc(self):
        plain = self.t.replace("**", "")
        for row in self.r["1 記録に在るモデルの字"]:
            self.assertIn("| %d |" % row["件数"], plain)
            head = row["字"].split("(")[0]
            self.assertIn("`%s" % head, self.t, "%s が本文に無い" % row["字"])

    def test_2_the_real_ids_are_the_4_5_seats(self):
        ids = {r["字"]: r["件数"] for r in self.r["1 記録に在るモデルの字"]
               if r["**モデル ID の形か**"]}
        self.assertEqual(sorted(ids), ["claude-haiku-4-5", "claude-opus-5",
                                       "claude-sonnet-4-5"])
        for k, v in ids.items():
            self.assertIn("| **`%s`** | **%d** | **はい** |" % (k, v), self.t)

    def test_3_the_harness_route_is_disclosed(self):
        self.assertIn("**席は API を直接叩いていない。**", self.t)
        self.assertIn("**だから「1 便が API 何回に化けたか」は私の記録に無い。**", self.t)
        self.assertIn("Agent(subagent)の harness を通している",
                      self.r["**席を呼んだときの実際の経路**"])


class RateTableTest(unittest.TestCase):
    def setUp(self):
        self.r = json.load(io.open(REC, encoding="utf-8"))
        self.t = text(DOC)

    def test_4_published_rates_are_attributed_to_the_human(self):
        srcs = {e["出どころ"] for e in self.r["2 単価の候補 × 入出力の割れ方"]}
        self.assertTrue(any("人間が公開料金表で確認" in s for s in srcs))
        self.assertIn("**私は確かめていない。**", self.t)
        self.assertIn("opus の記録 1 件から解いた組", self.t)

    def test_5_the_rows_quoted_in_the_doc_match_the_record(self):
        want = [("Claude Sonnet 5", 0.1), ("Claude Sonnet 5", 1.0),
                ("Claude Sonnet 4.6", 0.1), ("Claude Sonnet 4.6", 1.0),
                ("opus の記録から解いた組", 0.1)]
        by = {(e["単価の組"], e["出力の割合(仮定)"]): e
              for e in self.r["2 単価の候補 × 入出力の割れ方"]}
        for key in want:
            e = by[key]
            self.assertIn("%.2f USD" % e["8 便 USD"], self.t,
                          "%s の 8 便が本文に無い" % (key,))

    def test_6_material_only_rows_are_inside_the_guide_for_both_sonnets(self):
        by = {(e["単価の組"], str(e["出力の割合(仮定)"])): e
              for e in self.r["2 単価の候補 × 入出力の割れ方"]}
        for name in ("Claude Sonnet 5", "Claude Sonnet 4.6"):
            e = by[(name, "材料だけ入力 + 出力 6000")]
            self.assertTrue(e["目安 3 USD の中"], name)
        self.assertIn("**どの単価でも「材料だけを入力・出力は上限」なら"
                      "目安の中に入る。**", self.t)


class NoSecretsTest(unittest.TestCase):
    def test_7_the_csv_has_no_keys_and_no_breakdown(self):
        with io.open(CSV_P, encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["file", "model(記録のまま)",
                                   "合計トークン(実測)", "時刻"])
        self.assertGreaterEqual(len(rows) - 1, 1)
        body = "\n".join(",".join(r) for r in rows[1:])
        leaks = [s for s in KEYISH.findall(body)
                 if not re.fullmatch(r"[0-9a-f]{32,}", s)]
        self.assertEqual(leaks, [], "**鍵らしい字が csv に在る**")
        for word in ("api_key", "EDINET_API_KEY", "Authorization", "x-api-key"):
            self.assertNotIn(word, body, word)

    def test_8_the_doc_states_no_credentials_were_emitted(self):
        self.assertIn("**API キー・認証情報は 1 文字も出していません**", text(DOC))


class AmendmentTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_9_four_amendments_and_none_applied_yet(self):
        b = self.t[self.t.index("## §4"):self.t.index("## §5")]
        ids = re.findall(r"(?m)^\| \*\*(改-\d)\*\*", b)
        self.assertEqual(ids, ["改-%d" % i for i in range(1, 5)], "案は 4 本")
        self.assertIn("**上限を USD ではなくトークン数で封じる**", b)
        self.assertIn("**トークンは私が測れる。USD は私から見えない。**", b)
        self.assertIn("**主比較を字で足す ― 「A(LLM 単体)対 C′(LLM + Core)」", b)
        self.assertIn("**この便では封を 1 文字も直していない。**", b)

    def test_10_the_production_seal_is_untouched_and_names_no_main_comparison(self):
        """**封が直っていないことを封そのもので確かめる。**

        併せて**私の言い方の訂正を固定する** ―
        「主比較は C′ 対 D′」は**東京都の封**の字で、XBRL の封には無い。
        """
        s = text(SEAL)
        self.assertNotIn("主比較", s, "**XBRL の封は主比較を字で決めていない**")
        self.assertNotIn("claude-sonnet-5", s)
        self.assertNotIn("300,000 トークン", s)
        repro = text(os.path.join(ROOT, "docs",
                                  "DOMAIN1_REPRO_SEAL_2026-10-17.md"))
        self.assertIn("**主比較は C′ 対 D′。**", repro)
        self.assertIn("**「主比較は C′ 対 D′」と書いてあるのは東京都の封**", self.t)

    def test_11_six_limits_including_the_humans_distinction(self):
        b = self.t[self.t.index("## §5 示せないこと"):]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 7)], "限界は 6 本")
        self.assertIn("**1 本の記録で単価の組を一意に再現できたことと、"
                      "今回の実費を確定できたことは別である**", b)


if __name__ == "__main__":
    unittest.main()
