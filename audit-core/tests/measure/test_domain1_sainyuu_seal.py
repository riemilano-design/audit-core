# -*- coding: utf-8 -*-
"""歳入側の取得の封(docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md)を固定する。

**封は取得より先・測定より先に commit する。**
守るのは 10 つ。
  1. §1 の 2 件の file 名・URL・期待バイト数が**取得の道具の字と一致**する
  2. **実質収支 file を取得していない**(記録にも cache にも無い)。理由が記録に在る
  3. §3 の R-独立-6 が **6a〜6f の 6 項目**在ること
  4. **6f(別の file だから独立とは書かない)**が在ること
  5. §4 の P-1〜P-6 が在り、**P-1 を飛ばさない**と書いてあること
  6. §5 の停止規則(**`MIN_INDEPENDENT` を 2 にしない**)
  7. §6 の予測が **10 本**・**「材料をまだ見ていない」**と書いてあること
  8. §8 の限界、特に **1(安全性が改善したとは書かない)**・**2(実物の文に対しては未検証)**
  9. 段 10 の封の停止規則と**同じ条件**を引いていること
 10. **封が取得の道具・記録より先に commit されたこと**(commit の順)
"""
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_SAIIRU_SEAL_2026-10-16.md")
M10 = os.path.join(ROOT, "docs", "DOMAIN1_M10_SEAL_2026-10-16.md")
TOOL = os.path.join(MEASURE, "sheet_fetch_sainyuu_2026-10-16.py")
REC = os.path.join(FX, "opened_sainyuu_2026-10-16.json")
CACHE = os.path.expanduser("~/.cache/audit-core/sheet")
# **取ってはいけない file**(封 §1)
JISSITU = "op20251218_06kessan_06_jissitusyuusi.xlsx"

# 封 §1 の表(道具と封の両方に同じ字で在ること)
WANT = (("決算書 歳入", "op20251218_06kessan_02_sainyuu.xlsx", 96925),
        ("事項別明細 歳入", "op20251218_06kessan_04_jikoubetu_sainyuu.xlsx", 706250))


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def tool():
    sp = importlib.util.spec_from_file_location("fetch_sainyuu_t", TOOL)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class SealAndToolAgreeTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.m = tool()

    def test_1_two_files_only(self):
        self.assertEqual(len(self.m.FILES), 2, "取るのは 2 件だけ")
        self.assertEqual(tuple(self.m.FILES), WANT)

    def test_2_names_bytes_and_urls_are_in_the_seal(self):
        for label, name, want in WANT:
            self.assertIn("`%s`" % name, self.t, name)
            self.assertIn("**{:,}**".format(want), self.t, "期待バイト数 %d" % want)
        self.assertIn("https://www.opendata.metro.tokyo.lg.jp/kaikeikanri/",
                      self.m.BASE)
        self.assertEqual(self.m.BASE,
                         "https://www.opendata.metro.tokyo.lg.jp/kaikeikanri/")

    def test_3_the_tool_refuses_to_run_twice(self):
        self.assertIn("記録が既に在る", text(TOOL))
        self.assertIn("一度だけ", text(TOOL))

    def test_4_failures_are_not_filled_with_another_file(self):
        self.assertIn("**失敗は失敗として記録する**", text(TOOL))
        self.assertIn("別の file で埋めない", text(TOOL))

    def test_5_license_and_source_are_recorded(self):
        self.assertIn("CC BY 4.0", self.m.DATASET)
        self.assertIn("CC BY 4.0", self.t)
        self.assertIn("東京都会計管理局", self.t)


class JissitusyuusiIsNotFetchedTest(unittest.TestCase):
    """**実質収支は取らない。**歳入と歳出から導出される数なので独立にならない。"""

    def test_6_the_tool_lists_it_as_not_fetched_with_a_reason(self):
        m = tool()
        names = [n for _, n, _ in m.NOT_FETCHED]
        self.assertIn(JISSITU, names)
        why = [w for _, n, w in m.NOT_FETCHED if n == JISSITU][0]
        self.assertIn("導出", why)
        self.assertNotIn(JISSITU, [n for _, n, _ in m.FILES])

    def test_7_it_is_not_in_the_cache(self):
        self.assertFalse(os.path.exists(os.path.join(CACHE, JISSITU)),
                         "**取ってはいけない file が cache に在る**")

    def test_8_it_is_not_in_the_record(self):
        if not os.path.exists(REC):
            self.skipTest("まだ取得していない")
        rec = json.load(io.open(REC, encoding="utf-8"))
        self.assertNotIn(JISSITU, rec["files"])
        self.assertIn(JISSITU, [x["name"] for x in rec["not_fetched"]])

    def test_9_the_record_matches_the_seal_once_fetched(self):
        if not os.path.exists(REC):
            self.skipTest("まだ取得していない")
        rec = json.load(io.open(REC, encoding="utf-8"))
        self.assertEqual(sorted(rec["files"]), sorted(n for _, n, _ in WANT))
        for _, name, want in WANT:
            f = rec["files"][name]
            self.assertEqual(f["expected_bytes"], want)
            self.assertEqual(f["bytes"], want,
                             "**取れたバイト数が HEAD と違う**: %s" % name)
            self.assertEqual(len(f["sha256"]), 64)

    def test_10_no_xlsx_was_put_in_the_repo(self):
        hits = []
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
            hits += [os.path.join(base, f) for f in files if f.endswith(".xlsx")]
        self.assertEqual(hits, [], "**生ファイルを repo に置いた**")


class IndependenceConditionsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_11_six_conditions_6a_to_6f(self):
        ids = re.findall(r"\*\*6([a-f]) ", self.t)
        self.assertEqual(ids, ["a", "b", "c", "d", "e", "f"], ids)

    def test_12_a_different_file_is_not_evidence_of_independence(self):
        self.assertIn("**file が別であること・sha が別であることは、独立の証拠にしない。**",
                      self.t)
        self.assertIn("**6f 「別の file だから独立」とは書かない。**", self.t)

    def test_13_restatement_condition_requires_reading_the_structure(self):
        self.assertIn("**6e 出どころの重複(この封で新しく足す条件)。**", self.t)
        self.assertIn("**資料の構造と注記を読んで確かめる**", self.t)
        self.assertIn("字面の一致だけで判断しない。", self.t)


class WhatWillBeMeasuredTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_14_p1_to_p6(self):
        ids = re.findall(r"^\| \*\*P-(\d)\*\* \|", self.t, re.M)
        self.assertEqual([int(x) for x in ids], [1, 2, 3, 4, 5, 6], ids)

    def test_15_p1_must_not_be_skipped(self):
        self.assertIn("**P-1 を飛ばして P-2 以降に進まない。**", self.t)

    def test_16_the_stop_rule_is_kept_and_not_loosened(self):
        self.assertIn("**`MIN_INDEPENDENT` を 2 にする選択肢は取らない。**", self.t)
        self.assertIn("**P-4 が 0 件でも、R-独立-6 を緩めて数え直さない。**", self.t)
        self.assertIn("**P-5 で新しく正しく接続した主張が 0 件なら、この経路は打ち切る。**", self.t)

    def test_17_it_quotes_the_m10_stop_rule(self):
        """段 10 の封と**同じ条件**を引いていること(別の条件に置き換えていない)。"""
        self.assertIn("新しく正しく接続した主張が 1 件以上生まれた場合", self.t)
        self.assertIn("新しく正しく接続した主張が 1 件以上生まれた場合", text(M10))
        self.assertIn("docs/DOMAIN1_M10_SEAL_2026-10-16.md", self.t)


class PredictionsAndLimitsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_18_ten_blind_predictions(self):
        block = self.t.split("## §6")[1].split("## §7")[0]
        ids = re.findall(r"^\| T-(\d+) \|", block, re.M)
        self.assertEqual([int(x) for x in ids], list(range(1, 11)), ids)
        self.assertIn("**この予測は中身を知らないまま書いている。**", block)
        self.assertIn("**測ったあとに編集しない。追記は日付つきで足すだけ。外れは外れとして残す。**",
                      block)

    def test_19_predictions_are_ranges_that_can_fail(self):
        """**0 でも 18 でもない**と言い切っている予測が在ること(外れうる粒度)。"""
        self.assertIn("**0 件でも 18 件でもないと予測する**", self.t)

    def test_20_four_limits_with_the_two_that_matter(self):
        block = self.t.split("## §8")[1].split("## §9")[0]
        ids = re.findall(r"^(\d+)\. ", block, re.M)
        self.assertEqual([int(x) for x in ids], [1, 2, 3, 4], ids)
        self.assertIn("**「別名規則の安全性が改善した」とは書かない**", block)
        self.assertIn("**③の実物の文に対する安全性は、この封でも未検証のまま残る。**", block)
        self.assertIn("**測れた否定的結果**である", block)

    def test_21_failure_conditions_include_loosening_after_seeing_the_result(self):
        block = self.t.split("## §7")[1].split("## §8")[0]
        self.assertIn("**P-4 = 0 を見てから R-独立-6 を緩めた**", block)
        self.assertIn("生ファイルを repo に置いた", block)
        self.assertIn("**P-1 を飛ばして数を数えた**", block)


class CommitOrderTest(unittest.TestCase):
    """**封が取得の道具・記録より先に commit されたこと。**

    道は `cwd=ROOT`(= audit-core/)からの相対で書く ― repo ルートからの道を渡すと
    pathspec が当たらず、空振りを「未 commit」と読み違える(2026-10-16 に踏んだ)。
    """

    SEAL_REL = "docs/DOMAIN1_SAIIRU_SEAL_2026-10-16.md"
    TOOL_REL = "measure/sheet_fetch_sainyuu_2026-10-16.py"
    REC_REL = "fixtures/sheet/opened_sainyuu_2026-10-16.json"

    @staticmethod
    def _added(rel):
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
            cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _tracked(rel):
        return subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                              cwd=ROOT, capture_output=True).returncode == 0

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_22_seal_is_committed(self):
        self.assertTrue(self._tracked(self.SEAL_REL),
                        "道が git に当たっていない(pathspec の誤り)")
        self.assertIsNotNone(self._added(self.SEAL_REL), "封がまだ commit されていない")

    def test_23_seal_precedes_the_tool_and_the_record(self):
        seal = self._added(self.SEAL_REL)
        for rel in (self.TOOL_REL, self.REC_REL):
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other,
                                "封と %s が同じ commit に入っている(順を測れない)" % rel)
            self.assertTrue(self._ancestor(seal, other),
                            "封が %s より後に commit されている" % rel)
            self.assertFalse(self._ancestor(other, seal))   # 歯: 逆向きは偽

    def test_24_a_wrong_pathspec_is_detected(self):
        wrong = "audit-core/" + self.SEAL_REL
        self.assertIsNone(self._added(wrong))
        self.assertFalse(self._tracked(wrong))


if __name__ == "__main__":
    unittest.main()
