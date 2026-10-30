# -*- coding: utf-8 -*-
u"""汎化 C の封(docs/XBRL_GENERALITY_SEAL_2026-10-20.md)を固定する。C0 は 0 USD、C1 は条件つき。"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_GENERALITY_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
DRAW = os.path.join(ROOT, "fixtures", "xbrl", "gen_c", "draw_2026-10-20.json")
EIGHT = ["S100Z0OS", "S100YYN7", "S100YYT8", "S100Z42X", "S100YYT4", "S100Z4GF", "S100Z4J8", "S100YYUD"]
AFTER = ("fixtures/xbrl/gen_c/fetched_2026-10-20.json",
         "measure/xbrl_gen_c_2026-10-20.py",
         "fixtures/xbrl/gen_c/c0_2026-10-20.json",
         "docs/XBRL_GENERALITY_RESULT_2026-10-20.md",
         "tests/measure/test_xbrl_generality_result.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_head_names_the_human_flow_and_the_no_fix_rule(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"**有料のLLMはいつでも好きな時に使っていい**", head)
        self.assertIn(u"**0 USDで汎化Cを実行し、結果を監査する。**", head)
        self.assertIn(u"**LLM単体とLLM＋Coreの比較がまだ必要な論点に限って、有料試験を行う。**", head)
        self.assertIn(u"**engine(`core/`・`adapters/`)は 1 行も変えない。測ってから直さない。**C0 は席を呼ばない。", head)

    def test_2_stages_reuse_cd8_paths_and_c1_has_a_written_condition(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertEqual(re.findall(r"(?m)^\| \*\*(C0-1|C0-2|C0-3|C1)", b), ["C0-1", "C0-2", "C0-3", "C1"])
        self.assertIn(u"`adapters/xbrl/verify_document.py --doc <id>`", b)
        self.assertIn(u"`measure/xbrl_a_core_vs_grep_2026-10-17.py`", b)
        self.assertIn(u"`verify_external(spec, period_pair=True)`", b)
        self.assertIn(u"sha256 `4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb`、411 字", b)
        self.assertIn(u"**C1 をやる条件(先に書く)**", b)
        self.assertIn(u"**C1 はやらない**", b)
        self.assertIn(u"**別の追記で予測を先に書く**", b)

    def test_3_denominators_and_the_eight_documents_are_literal(self):
        b = sec(self.t, "## §1", "## §2")
        self.assertIn(u"| 母集団 | **256** |", b)
        self.assertIn(u"**位置 59 から**", b)
        for d in EIGHT:
            self.assertIn("`%s`" % d, b, d)
        self.assertIn(u"**8 件とも無い**", b)
        self.assertIn(u"**`EDINET_API_KEY` は人間が環境変数で渡し、値は記録しない**", b)
        self.assertIn(u"**取得後に数える**", b)
        self.assertIn(u"**除外**", b)

    def test_4_cd8_comparison_numbers_point_at_records(self):
        b = sec(self.t, "## §2", "## §3")
        for k in (u"46 / 64 = 71.9%", u"18 / 76 = 23.7%", u"17 / 85 = 20.0%", u"77 / 192 = 40.1%",
                  u"GROUNDED 60 / VALUE_MISMATCH 24 / UNVERIFIABLE 18 / POINTER_NOT_FOUND 17"):
            self.assertIn(k, b, k)
        for rel in ("a_core_vs_grep_2026-10-17.json", "period_unit_hold_2026-10-19.json",
                    "period_pair_stage2_2026-10-19.json", "holds_product_path_2026-10-19.json"):
            self.assertIn(rel, b, rel)

    def test_5_three_controls(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertEqual(re.findall(r"(?m)^\| \*\*C-(\d)", b), ["1", "2", "3"])
        self.assertIn(u"1 回に 1 件**", b)

    def test_6_fourteen_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §4", "## §5")
        ids = re.findall(r"(?m)^\| \*\*G-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 15)])
        for line in re.findall(r"(?m)^\| \*\*G-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**本当に測っているのは G-5〜G-12 である。G-8 が外れたら、直さずに 1 件ずつ読んで記録し、直しは別の封で。**", b)
        self.assertIn(u"**この封の最重要の数**", b)

    def test_7_limits_and_closed_file_list(self):
        self.assertIn(u"**8 書類 1 回である。**", sec(self.t, "## §5", "## §6"))
        b = sec(self.t, "## §6")
        for rel in AFTER:
            self.assertIn("`%s`" % rel, b, rel)
        self.assertIn(u"**これ以外に触らない。**", b)
        self.assertIn(u"**数を見てから封・材料・採点を直さない。**", b)


class DrawTest(unittest.TestCase):
    u"""draw の記録が封の 8 件と一致し、cd8 の規則の続きであること。"""
    def test_8_draw_record_matches_the_seal(self):
        with io.open(DRAW, encoding="utf-8") as fh:
            d = json.load(fh)
        self.assertEqual(d[u"引いた 8 件"], EIGHT)
        self.assertEqual(d[u"位置"], list(range(59, 67)))
        self.assertEqual(d[u"seed_hex"], "6a24d72")
        self.assertEqual(d[u"pool"], 256)
        self.assertEqual(d[u"飛ばした件"], [])
        self.assertEqual(d[u"**キャッシュに在るか**"][u"在った"], [])


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_9_the_seal_precedes_the_measurement(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


class AddendumC1Test(unittest.TestCase):
    u"""追記 1(C1 ― 席つき 8 便)。本文は不変、席の model・回数・上限・下見、予測 K-1〜K-12 が席を呼ぶ前に固定されていること。"""
    AFTER_C1 = ("measure/xbrl_gen_c1_2026-10-20.py",
                "fixtures/xbrl/gen_c/material_2026-10-20.json",
                "fixtures/xbrl/gen_c/seat_answers",
                "fixtures/xbrl/gen_c/c1_2026-10-20.json",
                "docs/XBRL_GENERALITY_C1_RESULT_2026-10-20.md",
                "tests/measure/test_xbrl_generality_c1_result.py")

    def setUp(self):
        t = text(SEAL)
        self.body = t[:t.index(u"\n## 追記 1")]
        self.a = t[t.index(u"\n## 追記 1"):]

    def test_10_body_is_unchanged_by_the_addendum(self):
        # 本文の §0〜§6 の見出しは追記の前に全部在り、追記の中に §0〜§6 の見出しは無い
        for h in ("## §0", "## §1", "## §2", "## §3", "## §4", "## §5", "## §6"):
            self.assertIn("\n" + h, self.body, h)
            self.assertNotIn("\n" + h + " ", self.a, h)
        self.assertIn(u"本文(§0〜§6)は 1 文字も直さない**", self.a)

    def test_11_condition_and_seat_terms_are_literal(self):
        self.assertIn(u"**G-5 が外れた**(Core-P の特定率 13 / 50 = 26.0%。幅 55〜80%)", self.a)
        self.assertIn(u"| model | `sonnet`", self.a)
        self.assertIn(u"| 回数 | **8 便**", self.a)
        self.assertIn(u"**合計 1,600,000 トークン**", self.a)
        self.assertIn(u"1 便が 250,000 を超えたらその便を止めて「欠け」", self.a)
        self.assertIn(u"`4c63022014736bb25de0c3808d227c06bbfcd72856aaf3a2e2dfdf31cb85c0fb`(411 字)", self.a)
        self.assertIn(u"**下見で止まれば席は呼ばない**", self.a)
        self.assertIn(u"**8 + 8 + 4 = 20 行以下**", self.a)

    def test_12_twelve_predictions_each_with_a_failure_mode(self):
        ids = re.findall(r"(?m)^\| \*\*K-(\d+)\*\* \|", self.a)
        self.assertEqual(ids, [str(i) for i in range(1, 13)])
        for line in re.findall(r"(?m)^\| \*\*K-\d+\*\* \|.*$", self.a):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertEqual(re.findall(r"(?m)^\| \*\*K-C(\d)", self.a), ["1", "2", "3"])
        self.assertIn(u"**本当に測っているのは K-3〜K-6 である。**", self.a)
        self.assertIn(u"**これも engine の独立した証拠ではない**", self.a)

    def test_13_closed_file_list_and_order(self):
        for rel in self.AFTER_C1:
            self.assertIn("`%s" % rel, self.a, rel)
        self.assertIn(u"**数を見てから封・材料・採点・予測を直さない。**", self.a)

    def test_14_the_addendum_precedes_c1_files(self):
        # 追記が入った commit より後に C1 の file が足されること(順序の門。cwd 相対)
        out = subprocess.run(["git", "log", "-S", u"## 追記 1(2026-10-20)**C1", "--format=%H", "--", SEAL_REL],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        if not shas:
            self.skipTest(u"追記がまだ commit されていない")
        add = shas[-1]
        for rel in self.AFTER_C1:
            other = OrderTest._added(rel)
            if other is None:
                continue
            self.assertNotEqual(add, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", add, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


class AddendumP20Test(unittest.TestCase):
    u"""追記 2(改善 1 ― (ア)の測定を製品の既定 P20 で測り直す)。本文と追記 1 は不変、予測 R-1〜R-11 が測る前に固定されていること。"""
    AFTER_P20 = ("measure/xbrl_gen_c_p20_2026-10-20.py",
                 "fixtures/xbrl/gen_c/c0_p20_2026-10-20.json",
                 "docs/XBRL_GENERALITY_P20_RESULT_2026-10-20.md",
                 "tests/measure/test_xbrl_generality_p20_result.py")

    def setUp(self):
        t = text(SEAL)
        self.before = t[:t.index(u"\n## 追記 2")]
        self.a = t[t.index(u"\n## 追記 2"):]

    def test_15_body_and_addendum1_precede_and_are_not_repeated(self):
        for h in ("## §0", "## §6", u"## 追記 1"):
            self.assertIn("\n" + h, self.before, h)
            self.assertNotIn("\n" + h, self.a, h)
        self.assertIn(u"本文(§0〜§6)と追記 1 は 1 文字も直さない**", self.a)
        self.assertIn(u"**C0 の結果文書と記録は直さない**", self.a)

    def test_16_facts_and_terms_are_literal(self):
        for s in (u"13 / 50 = 26.0%", u"16 / 20 = 80.0%", u"5 / 20 = 25.0%",
                  u"`DEFAULT_PROFILE = \"P20\"`", u"**`S100Z4GF` と `S100Z4J8` の 2 件だけ**",
                  u"**P20 は P16 と 1 件も違わなかった**", u"`measure/SEED.json`",
                  u"**依ったらその事実を書いて止める**"):
            self.assertIn(s, self.a, s)

    def test_17_eleven_predictions_each_with_a_failure_mode(self):
        ids = re.findall(r"(?m)^\| \*\*R-(\d+)\*\* \|", self.a)
        self.assertEqual(ids, [str(i) for i in range(1, 12)])
        for line in re.findall(r"(?m)^\| \*\*R-\d+\*\* \|.*$", self.a):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertEqual(re.findall(r"(?m)^\| \*\*R-C(\d)", self.a), ["1", "2", "3"])
        self.assertIn(u"**本当に測っているのは R-2〜R-4・R-6 である。**", self.a)
        self.assertIn(u"これも engine の独立した証拠ではない", self.a)

    def test_18_closed_file_list_and_order(self):
        for rel in self.AFTER_P20:
            self.assertIn("`%s`" % rel, self.a, rel)
        self.assertIn(u"**これ以外に触らない。**", self.a)
        self.assertIn(u"**数を見てから封・材料・採点・予測を直さない。**", self.a)
        out = subprocess.run(["git", "log", "-S", u"## 追記 2(2026-10-20)**改善 1", "--format=%H", "--", SEAL_REL],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        if not shas:
            self.skipTest(u"追記 2 がまだ commit されていない")
        add = shas[-1]
        for rel in self.AFTER_P20:
            other = OrderTest._added(rel)
            if other is None:
                continue
            self.assertNotEqual(add, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", add, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


class AddendumAlphaTest(unittest.TestCase):
    u"""追記 3(改善 2 ― α: 席の参照先を Core が検算)。本文・追記 1・2 は不変、予測 S-1〜S-9 が測る前に固定されていること。"""
    AFTER_ALPHA = ("measure/xbrl_gen_c_alpha_2026-10-20.py",
                   "fixtures/xbrl/gen_c/alpha_2026-10-20.json",
                   "docs/XBRL_GENERALITY_ALPHA_RESULT_2026-10-20.md",
                   "tests/measure/test_xbrl_generality_alpha_result.py")

    def setUp(self):
        t = text(SEAL)
        self.before = t[:t.index(u"\n## 追記 3")]
        self.a = t[t.index(u"\n## 追記 3"):]

    def test_19_earlier_parts_precede_and_are_not_repeated(self):
        for h in ("## §0", "## §6", u"## 追記 1", u"## 追記 2"):
            self.assertIn("\n" + h, self.before, h)
            self.assertNotIn("\n" + h, self.a, h)
        self.assertIn(u"本文・追記 1・追記 2 は 1 文字も直さない**", self.a)
        self.assertIn(u"**「教える」は規則として覚え込ませない**", self.a)

    def test_20_facts_and_the_alpha_rule_are_literal(self):
        for s in (u"**席が `確認済み` と言い参照先を出した行 77**", u"`判定できない` 51",
                  u"`誤りが在る` + 参照先 25", u"`判定できない` 39",
                  u"**`判定できない` に下げる(警告。`誤りが在る` に上書きしない)**",
                  u"21 / 50", u"GROUNDED 0 / 25"):
            self.assertIn(s, self.a, s)
        self.assertEqual(re.findall(r"(?m)^\| \*\*α-(\d)", self.a), ["1", "2", "3", "4"])

    def test_21_nine_predictions_each_with_a_failure_mode(self):
        ids = re.findall(r"(?m)^\| \*\*S-(\d+)\*\* \|", self.a)
        self.assertEqual(ids, [str(i) for i in range(1, 10)])
        for line in re.findall(r"(?m)^\| \*\*S-\d+\*\* \|.*$", self.a):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertEqual(re.findall(r"(?m)^\| \*\*S-C(\d)", self.a), ["1", "2", "3"])
        self.assertIn(u"**本当に測っているのは S-1〜S-3 である。**", self.a)
        self.assertIn(u"独立した証拠ではない", self.a)

    def test_22_closed_file_list_and_order(self):
        for rel in self.AFTER_ALPHA:
            self.assertIn("`%s`" % rel, self.a, rel)
        self.assertIn(u"**これ以外に触らない。**", self.a)
        self.assertIn(u"**数を見てから封・材料・採点・予測を直さない。**", self.a)
        out = subprocess.run(["git", "log", "-S", u"## 追記 3(2026-10-20)**改善 2", "--format=%H", "--", SEAL_REL],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        if not shas:
            self.skipTest(u"追記 3 がまだ commit されていない")
        add = shas[-1]
        for rel in self.AFTER_ALPHA:
            other = OrderTest._added(rel)
            if other is None:
                continue
            self.assertNotEqual(add, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", add, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
