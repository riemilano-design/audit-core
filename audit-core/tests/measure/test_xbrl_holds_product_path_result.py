# -*- coding: utf-8 -*-
u"""(d)・P・U を製品の経路へ + 軸の保持 (e) の実測(docs/XBRL_HOLDS_PRODUCT_PATH_RESULT_2026-10-19.md)の門。

**本文の数は `holds_product_path_2026-10-19.json` を正本に突き合わせる。**
**外れ 4 欄(F-2・F-10・F-11・F-12)が外れとして残ること、「精度が上がった」へ滑らないことを固定する。**
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_HOLDS_PRODUCT_PATH_RESULT_2026-10-19.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "holds_product_path_2026-10-19.json")
FROZEN = os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")
MISSES = ["F-2", "F-10", "F-11", "F-12"]
RED_IN_FIRST_RUN = [
    "tests/measure/test_verify_external_v1.py::ReviseRecordTest::test_25_the_allowed_list_was_not_edited",
    "tests/measure/test_verify_external_v1.py::ReviseRecordTest::test_26_the_entry_point_is_not_in_the_adapters_directory",
    "tests/measure/test_xbrl_cd_seal.py::FrozenToolsTest::test_12_engine_and_tools_have_not_moved",
]


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = rec()
        self.F = self.r[u"**実測**"]

    def test_1_core_untouched_and_instance_only_lost_its_docstring_line(self):
        self.assertEqual(self.F["F-1"], 0)
        n = self.F["F-2"][u"instance.py の numstat"]
        self.assertEqual(n["deleted"], 1)
        self.assertEqual(n[u"消したコード行"], 0)
        self.assertEqual(len(n[u"消した行の中身"]), 1)
        self.assertIn('"""', n[u"消した行の中身"][0])
        pt = self.F["F-2"][u"engine 側の試験(変異を除く)"]
        self.assertTrue(pt["ran"])
        self.assertEqual((pt["rc"], pt["failed"]), (0, 0))
        self.assertGreaterEqual(pt["passed"], 786)

    def test_2_axes_one_to_one_on_all_contexts(self):
        a = self.F["F-3"]
        self.assertEqual((a[u"書類"], a[u"**違反**"]), (8, 0))
        self.assertGreater(a[u"members を持つ枠"], 0)
        self.assertLessEqual(a[u"members を持つ枠"], a[u"枠"])

    def test_3_the_192_rows_and_the_six_reasons_reproduce(self):
        f4 = self.F["F-4"]
        self.assertEqual((f4[u"行"], f4[u"**一致**"]), (192, 192))
        self.assertEqual(f4[u"不一致の明細"], [])
        self.assertEqual((f4[u"(d) の理由を照合した行"], f4[u"理由も一致"]), (6, 6))
        self.assertEqual(f4[u"state の分布(入口)"],
                         {"GROUNDED": 18, "None": 107, "UNPROVABLE": 23, "VALUE_MISMATCH": 44})

    def test_4_axes_classes_and_controls(self):
        self.assertEqual(self.F["F-5"][u"分類"], {"ConsolidatedOrNonConsolidatedAxis": 2,
                                                   "OperatingSegmentsAxis": 2, "ComponentsOfEquityAxis": 2})
        self.assertEqual(len(self.F["F-5"][u"明細"]), 6)
        c = self.F["F-6"]
        for k, n in ((u"期間(注入)", 18), (u"単位", 24), (u"次元", 24)):
            self.assertEqual((c[k][u"作れた"], c[k][u"**保留**"]), (n, n), k)

    def test_5_existing_path_only_moved_in_the_engine_field(self):
        f7 = self.F["F-7"]
        self.assertTrue(f7["ran"] and f7[u"基準の sha256 の頭が封のとおり"])
        self.assertEqual(f7[u"**動いた欄**"], ["engine"])
        self.assertEqual(f7[u"engine の中で動いた欄"],
                         ["adapter_xbrl_py_files", "adapter_xbrl_py_sha256", "git_commit"])
        self.assertEqual(f7[u"claims の本数"], 119)
        self.assertEqual(f7[u"claims の state"],
                         {"GROUNDED": 60, "POINTER_NOT_FOUND": 17, "UNVERIFIABLE": 18, "VALUE_MISMATCH": 24})
        self.assertTrue(self.F["F-8"][u"**同じ**"])

    def test_6_three_new_mutations_red_and_89_old_rows_untouched(self):
        m = self.F["F-9"]
        self.assertTrue(m[u"走らせた"])
        self.assertEqual((m[u"封の commit の行数"], m[u"いまの行数"], m[u"**既存の行で字が同じ**"]), (89, 92, 89))
        self.assertEqual(m[u"**赤の本数**"], 3)
        self.assertEqual(sorted(x["id"] for x in m[u"結果"]),
                         ["HOLD-R1-holds-move-non-grounded", "HOLD-R2-period-ignores-dimension",
                          "HOLD-R3-axes-not-kept"])
        for x in m[u"結果"]:
            self.assertEqual((x[u"色"], x[u"予測"]), ("red", "red"), x["id"])

    def test_7_frozen_surface_is_34_to_36_not_22_to_24(self):
        fz = self.F["F-10"]
        self.assertEqual(fz[u"封の commit の実測(git ls-tree)"], 34)
        self.assertEqual(fz[u"封の commit の字(FROZEN_COUNT)"], 22)
        self.assertEqual((fz[u"いまの実測(git ls-files)"], fz[u"いまの字(FROZEN_COUNT)"], fz[u"束ねた本数"]), (36, 36, 36))
        self.assertEqual(fz[u"世代の行(封の commit → いま)"], [2, 3])
        self.assertTrue(fz[u"字で留めた世代の値と一致"])
        self.assertEqual(fz[u"足した file"], ["audit-core/adapters/xbrl/holds.py",
                                               "audit-core/adapters/xbrl/verify_external.py"])
        self.assertEqual(fz[u"消えた file"], [])
        src = text(FROZEN)
        # 2026-10-21 追記(pin の遷移): 顧客向けの日本語の報告形(封 docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md)が新しい module report_customer.py を足して 36 → 37 本。
        # この門が測った当時の値(上の 36)は消さない。いまの字は、測った当時の 36 か、宣言された遷移の 37(report_customer.py が追跡されているとき)だけを受け入れる。
        n_now = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src).group(1))
        # 2026-10-21 追記(commit c13a746 の後、独立監査の推奨): report_customer.py が commit されたので 37 に締める。
        self.assertEqual(n_now, 37)
        if n_now == 37:
            self.assertIn(u"audit-core/adapters/xbrl/report_customer.py", subprocess.run(["git", "ls-files", "audit-core/adapters"], cwd=os.path.dirname(ROOT), capture_output=True, text=True).stdout.split())
        self.assertIn(fz[u"いまの束ねた sha"], src)

    def test_8_run_tests_red_once_then_green_and_audit_go_without_revise(self):
        f11 = self.F["F-11"]
        self.assertEqual((f11[u"回数"], f11[u"1 回目の rc"], f11[u"最後の rc"]), (2, None, 0))
        self.assertTrue(f11[u"**全部通った**"])
        self.assertEqual(f11[u"走らせた順"][0][u"赤の試験"], RED_IN_FIRST_RUN)
        self.assertEqual(f11[u"走らせた順"][1][u"赤の試験"], [])
        self.assertEqual((self.F["F-12"][u"判定"], self.F["F-12"][u"REVISE の回数"]), ("GO", 0))
        self.assertTrue(self.F["F-12"][u"出どころ"])

    def test_9_predictions_nine_hits_three_misses(self):
        p = self.r[u"**予測との照合**"]
        self.assertEqual((p[u"当たり"], p[u"外れ"]), (8, 4))
        self.assertEqual([x[u"記号"] for x in p[u"欄ごと"]], ["F-%d" % i for i in range(1, 13)])
        self.assertEqual([x[u"記号"] for x in p[u"欄ごと"] if not x[u"当たり"]], MISSES)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        self.F = self.r[u"**実測**"]

    def test_10_headline_and_result_table_match_the_record(self):
        p = self.r[u"**予測との照合**"]
        self.assertIn(u"予測 当たり %d / 外れ %d**" % (p[u"当たり"], p[u"外れ"]), self.t.splitlines()[0])
        b = sec(self.t, "## §1", "## §2")
        a, f4, c, f7 = self.F["F-3"], self.F["F-4"], self.F["F-6"], self.F["F-7"]
        self.assertIn(u"| F-3 軸の 1:1 | %d 書類・%d 枠(members あり %d)| **違反 %d** |"
                      % (a[u"書類"], a[u"枠"], a[u"members を持つ枠"], a[u"**違反**"]), b)
        self.assertIn(u"| F-4 192 行の再現 | 記録 `period_unit_hold_2026-10-19.json` の「合成の後」| **%d / %d** 一致・(d) の理由 %d / %d |"
                      % (f4[u"**一致**"], f4[u"行"], f4[u"理由も一致"], f4[u"(d) の理由を照合した行"]), b)
        self.assertIn(u"| F-6 対照 | 注入 1 件ずつ(GROUNDED の 24 行)| 期間(注入)**%d / %d**・単位 **%d / %d**・次元 **%d / %d** |"
                      % (c[u"期間(注入)"][u"**保留**"], c[u"期間(注入)"][u"作れた"], c[u"単位"][u"**保留**"],
                         c[u"単位"][u"作れた"], c[u"次元"][u"**保留**"], c[u"次元"][u"作れた"]), b)
        st = f7[u"claims の state"]
        self.assertIn(u"claims %d: G %d / PNF %d / UNV %d / VM %d"
                      % (f7[u"claims の本数"], st["GROUNDED"], st["POINTER_NOT_FOUND"], st["UNVERIFIABLE"],
                         st["VALUE_MISMATCH"]), b)
        self.assertIn(u"動いた欄は **`engine` だけ**", b)
        self.assertIn(u"**%d 本とも red**" % self.F["F-9"][u"**赤の本数**"], b)

    def test_11_prediction_tally_and_the_three_misses_each_with_a_cause(self):
        b = sec(self.t, "## §3", "## §4")
        p = self.r[u"**予測との照合**"]
        self.assertIn(u"**当たり %d / 外れ %d。**" % (p[u"当たり"], p[u"外れ"]), b)
        self.assertEqual(len(re.findall(r"\| \*\*当たり\*\* \|", b)), p[u"当たり"])
        self.assertEqual(len(re.findall(r"\| \*\*外れ\*\* \|", b)), p[u"外れ"])
        for sym in MISSES:
            self.assertRegex(b, r"\| \*\*%s\*\* \|.*\| \*\*外れ\*\* \|" % re.escape(sym))
            self.assertRegex(b, r"(?m)^- \*\*%s 外れ\*\*: " % re.escape(sym))
        n = self.F["F-2"][u"instance.py の numstat"]
        self.assertIn(u"numstat は足した %d・消した %d" % (n["added"], n["deleted"]), b)
        fz = self.F["F-10"]
        self.assertIn(u"実測は %d → %d" % (fz[u"封の commit の実測(git ls-tree)"], fz[u"いまの実測(git ls-files)"]), b)
        f11 = self.F["F-11"]
        first = f11[u"走らせた順"][0][u"要約の行"][-1]
        m = re.search(r"(\d+) failed", first)
        self.assertIsNotNone(m, first)
        self.assertIsNone(f11[u"1 回目の rc"])
        self.assertIn(u"**1 回目はログに `rc=` の行が無い**(pytest %s failed・赤 %d 本)"
                      % (m.group(1), len(f11[u"走らせた順"][0][u"赤の試験"])), b)
        self.assertIn(u"2 回目 rc=%d" % f11[u"最後の rc"], b)
        self.assertIn(u"**封は直さない。**", b)

    def test_12_no_claim_of_accuracy_gain_and_limits(self):
        for m in re.finditer(u"精度は上が", self.t):
            ctx = self.t[m.start():m.end() + 12]
            self.assertTrue(u"上がらない" in ctx or u"上がっていない" in ctx, ctx)
        b = sec(self.t, "## §4")
        self.assertIn(u"**精度は上がらない。**", b)
        self.assertIn(u"**同じ 8 書類である。**", b)
        self.assertIn(u"「どの軸の違いなら不一致か」は決めない", b)

    def test_13_the_seal_commit_is_the_one_that_added_the_seal(self):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h", "--",
                              "docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md"],
                             cwd=ROOT, capture_output=True, text=True).stdout.split()
        if not out:
            self.skipTest(u"封が未 commit")
        self.assertIn(u"commit `%s`" % out[-1][:7], self.t)
        self.assertEqual(self.r["seal_commit"], out[-1][:7])


if __name__ == "__main__":
    unittest.main()
