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


if __name__ == "__main__":
    unittest.main()
