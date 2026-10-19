# -*- coding: utf-8 -*-
u"""P・U の実測(docs/XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md)の門。

**本文の数は `period_unit_hold_2026-10-19.json` を正本に突き合わせる。**
**「精度が上がった」へ結論が滑らないこと、外れ 2 欄が外れとして残ることを固定する。**
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "XBRL_PERIOD_UNIT_HOLD_RESULT_2026-10-19.md")
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
REC = os.path.join(FX, "period_unit_hold_2026-10-19.json")
DH = os.path.join(FX, "dim_hold_2026-10-17.json")
DIAG = os.path.join(FX, "dim_diag_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p=REC):
    return json.load(io.open(p, encoding="utf-8"))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = rec()
        self.p1 = self.r[u"**第 1 部 規則の適用**"]
        self.c = self.r[u"**対照(故障を作って当てる。GROUNDED の 24 行)**"]
        self.e = self.r[u"**第 2 部 露出の帯(状態は変えない)**"]

    def test_1_only_grounded_moved_and_only_by_d(self):
        a, b = self.p1[u"状態(前)"], self.p1[u"状態(後)"]
        self.assertEqual((a["GROUNDED"], b["GROUNDED"]), (24, 18))
        for k in ("VALUE_MISMATCH", "POINTER_NOT_FOUND"):
            self.assertEqual(a.get(k, 0), b.get(k, 0), k)
        f = self.p1[u"**発火(規則ごと)**"]
        self.assertEqual((len(f["d"]), len(f["P"]), len(f["U"])), (6, 0, 0))
        self.assertTrue(self.p1[u"**(d) の発火が 10-17 の記録と同じ**"])
        diag6 = sorted((x["doc"], x["id"]) for x in rec(DIAG)["rows"])
        self.assertEqual(sorted((x["doc"], x["id"]) for x in f["d"]), diag6)

    def test_2_the_injected_holes_are_closed(self):
        self.assertEqual(self.c[u"C-期間(注入)/作れた"], 18)
        self.assertEqual(self.c[u"C-期間(注入)/作れなかった"], 6)
        self.assertEqual(self.c[u"C-期間(注入)/v1 が通した"], 18)
        self.assertEqual(self.c[u"C-期間(注入)/**発火 P**"], 18)
        self.assertEqual(self.c[u"C-期間(注入)/**発火 U**"], 0)
        self.assertEqual(self.c[u"C-単位/作れた"], 24)
        self.assertEqual(self.c[u"C-単位/v1 が通した"], 24)
        self.assertEqual(self.c[u"C-単位/**発火 U**"], 24)
        self.assertEqual(self.c[u"C-単位/**発火 P**"], 0)
        self.assertEqual(self.c[u"C-単位/**発火 d**"], 0)
        self.assertEqual(self.c[u"C-次元/**発火 P**"], 0)
        self.assertEqual(self.c[u"C-次元/**発火 U**"], 0)
        self.assertEqual(self.c[u"C-次元/**発火 d**"], 24)

    def test_3_gold_pointers_are_never_held(self):
        self.assertEqual(self.e[u"D4 正解(T5)の参照先 50 件/P"][u"分子"], 0)
        self.assertEqual(self.e[u"D4 正解(T5)の参照先 50 件/U"][u"分子"], 0)
        self.assertEqual(self.e[u"D4 正解(T5)の参照先 50 件/P"][u"分母"], 50)

    def test_4_period_exposure_is_zero_and_unit_exposure_is_the_rate_claim_shape(self):
        self.assertEqual(self.e[u"D2 席が名指した 85 行/P"][u"分子"], 0)
        self.assertEqual(self.e[u"D2 席が名指した 85 行/U"][u"分子"], 17)
        self.assertEqual(self.e[u"D3 無改変で名指した 42 行/U"][u"分子"], 17)
        rows = {(x["doc"], x["id"]): x for x in self.r["rows"]}
        for d in self.e[u"D2 の U の明細"]:
            self.assertEqual((d["claim"], d["fact"]), ("pure", "JPY"))
            row = rows[(d["doc"], d["id"])]
            self.assertEqual(row[u"単位"], u"％")
            self.assertEqual(row[u"v1 の state"], "UNPROVABLE", u"既に実証不能のはず")
            self.assertFalse(row[u"注入か"])

    def test_5_predictions_twelve_hits_two_misses(self):
        p = self.r[u"**予測との照合**"]
        self.assertEqual((p[u"当たり"], p[u"外れ"]), (12, 2))
        miss = [x[u"記号"] for x in p[u"欄ごと"] if x[u"当たり"] is False]
        self.assertEqual(miss, ["E-6", "E-12"])
        for x in p[u"欄ごと"]:
            self.assertIn(x[u"当たり"], (True, False), x[u"記号"])

    def test_6_no_pointer_changed_and_no_dangerous_pass(self):
        pass_after = [x for x in self.r["rows"] if x[u"**最終判定(後)**"] == u"検査通過"]
        self.assertEqual(len(pass_after), 18)
        self.assertEqual(sum(1 for x in pass_after if x[u"注入か"]), 0)
        e5 = [x for x in self.r[u"**予測との照合**"][u"欄ごと"] if x[u"記号"] == "E-5"][0]
        self.assertEqual(e5[u"実測"], 0)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_7_state_table_matches_the_record(self):
        a = self.r[u"**第 1 部 規則の適用**"][u"状態(前)"]
        b = self.r[u"**第 1 部 規則の適用**"][u"状態(後)"]
        self.assertIn(u"| `GROUNDED` | %d | **%d** |" % (a["GROUNDED"], b["GROUNDED"]), self.t)
        self.assertIn(u"| `VALUE_MISMATCH` | %d | %d(**変わらない**) |"
                      % (a["VALUE_MISMATCH"], b["VALUE_MISMATCH"]), self.t)
        self.assertIn(u"| `UNPROVABLE` | %d | %d |" % (a["UNPROVABLE"], b["UNPROVABLE"]), self.t)

    def test_8_control_table_matches_the_record(self):
        c = self.r[u"**対照(故障を作って当てる。GROUNDED の 24 行)**"]
        b = sec(self.t, "### §1-1", "## §2")
        self.assertIn(u"| 期間(注入) | %d(作れなかった %d) | **%d / %d** | **%d / %d** | %d | %d |"
                      % (c[u"C-期間(注入)/作れた"], c[u"C-期間(注入)/作れなかった"],
                         c[u"C-期間(注入)/v1 が通した"], c[u"C-期間(注入)/作れた"],
                         c[u"C-期間(注入)/**発火 P**"], c[u"C-期間(注入)/作れた"],
                         c[u"C-期間(注入)/**発火 U**"], c[u"C-期間(注入)/**発火 d**"]), b)
        self.assertIn(u"| 単位(USD) | %d | **%d / %d** | %d | **%d / %d** | %d |"
                      % (c[u"C-単位/作れた"], c[u"C-単位/v1 が通した"], c[u"C-単位/作れた"],
                         c[u"C-単位/**発火 P**"], c[u"C-単位/**発火 U**"], c[u"C-単位/作れた"],
                         c[u"C-単位/**発火 d**"]), b)

    def test_9_exposure_table_matches_the_record(self):
        e = self.r[u"**第 2 部 露出の帯(状態は変えない)**"]
        b = sec(self.t, "## §2", "## §3")
        self.assertIn(u"| D2 席が名指した 85 行 | **%d / 85** | **%d / 85**"
                      % (e[u"D2 席が名指した 85 行/P"][u"分子"], e[u"D2 席が名指した 85 行/U"][u"分子"]), b)
        self.assertIn(u"| **D4 正解(T5)の参照先 50 件** | **%d / 50** | **%d / 50** |"
                      % (e[u"D4 正解(T5)の参照先 50 件/P"][u"分子"], e[u"D4 正解(T5)の参照先 50 件/U"][u"分子"]), b)
        self.assertIn(u"17 行は **全部 `％` の主張**", b)
        self.assertIn(u"**17 行とも既に `UNPROVABLE`**", b)

    def test_10_prediction_tally_and_both_misses(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"**当たり 12 / 外れ 2。**", b)
        self.assertEqual(len(re.findall(r"\| \*\*当たり\*\* \|", b)), 12)
        self.assertRegex(b, r"\| \*\*E-6\*\* \|.*\| \*\*外れ\*\* \|")
        self.assertRegex(b, r"\| \*\*E-12\*\* \|.*\| \*\*外れ\*\* \|")
        self.assertIn(u"**予測の書き方の誤り**", b)
        self.assertIn(u"**封は直さない。**", b)

    def test_11_no_claim_of_accuracy_gain(self):
        for m in re.finditer(u"精度は上が", self.t):
            ctx = self.t[m.start():m.end() + 12]
            self.assertTrue(u"上がらない" in ctx or u"上がっていない" in ctx, ctx)
        self.assertIn(u"**精度は上がらない。**", self.t)
        self.assertIn(u"**同じ 8 書類である。**", self.t)

    def test_12_the_seal_commit_is_the_one_that_added_the_seal(self):
        import subprocess
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%h", "--",
                              "docs/XBRL_PERIOD_UNIT_HOLD_SEAL_2026-10-19.md"],
                             cwd=ROOT, capture_output=True, text=True).stdout.split()
        if not out:
            self.skipTest(u"封が未 commit")
        self.assertIn(u"commit `%s`" % out[-1][:7], self.t)


if __name__ == "__main__":
    unittest.main()
