# -*- coding: utf-8 -*-
"""仮説 A の分岐(docs/XBRL_BRANCH_A_2026-10-17.md)の門。

**数は 3 つの記録を正本に突き合わせる。**
**engine を触っていないことは sha で確かめる。**
**予測は「測る前に commit した」ことを git の順で確かめる。**
"""
import hashlib
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DOC = os.path.join(ROOT, "docs", "XBRL_BRANCH_A_2026-10-17.md")
BR = os.path.join(FX, "branch_a_2026-10-17.json")
MAP = os.path.join(FX, "rowclaim_map_2026-10-17.json")
PRED = os.path.join(FX, "branch_a_predictions_2026-10-17.json")
ENGINE_SHA = {"adapters/xbrl/recipes.py": "e2bda6aee13880ff",
              "adapters/xbrl/instance.py": None,
              "adapters/xbrl/resolve.py": "a41043763c1d4073",
              "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
              "adapters/xbrl/vocabulary.py": "bcf559308bda0cc6"}
NOT_YET_MEASURED = "fixtures/xbrl/cd8/p20_rerun_2026-10-17.json"  # 実測の記録


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p):
    return json.load(io.open(p, encoding="utf-8"))


class BranchTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.b = rec(BR)

    def test_1_the_executed_line_is_one_place(self):
        hits = [h for hs in self.b[u"**実行された行**"].values() for h in hs]
        self.assertEqual(len(hits), 6, u"10 行 = 6 主張")
        self.assertEqual({h[u"行"] for h in hits}, {330})
        self.assertEqual({h[u"関数"] for h in hits}, {"_direct_value_claim"})
        for h in hits:
            self.assertEqual(h[u"**候補 fact の数 fs**"], 0, h[u"主張 id"])
            self.assertEqual(h[u"member"], "None", h[u"主張 id"])
            self.assertTrue(h[u"選ばれた要素"], u"**要素は選べている**")
        self.assertIn(u"`recipes.py:330`", self.t)
        self.assertIn(u"**落ちているのは候補 fact が 0 件だから**である。", self.t)

    def test_2_the_dropping_function_and_its_two_conditions(self):
        b = self.b[u"**分岐の場所**"]
        self.assertEqual(b[u"落とす関数"][u"関数"], "ctx_ok / plain_context")
        self.assertEqual(b[u"条件を立てる場所"][u"関数"],
                         "with_nonconsolidated_fallback")
        self.assertEqual(len(b[u"条件を立てる場所"][u"2 つの条件"]), 2)
        self.assertIn(u"`with_nonconsolidated_fallback`", self.t)
        self.assertIn(u"`ctx_ok`", self.t)

    def test_3_the_profile_flags_are_read_from_the_code(self):
        import sys
        sys.path.insert(0, ROOT)
        from adapters.xbrl import vocabulary as V
        p = self.b[u"**分岐の場所**"][u"**profile**"]
        self.assertIs(p[u"`P16.nonconsolidated_fallback`"],
                      V.PROFILES["P16"].nonconsolidated_fallback)
        self.assertIs(p[u"`P20.nonconsolidated_fallback`"],
                      V.PROFILES["P20"].nonconsolidated_fallback)
        self.assertEqual(p[u"**Core の既定**"], V.DEFAULT_PROFILE)
        self.assertEqual(p[u"今回の測定で使った"], "P16")
        self.assertFalse(V.PROFILES["P16"].nonconsolidated_fallback)
        self.assertTrue(V.PROFILES["P20"].nonconsolidated_fallback)
        self.assertIn(u"**コードの既定は P20 である。封の字は直さない**", self.t)

    def test_4_the_minimal_repro_is_a_two_by_two(self):
        cs = self.b[u"**最小の再現入力**"][u"場合ごと"]
        self.assertEqual(len(cs), 4)
        plain = next(c for c in cs if c[u"場合"].startswith(u"素の枠"))
        self.assertTrue(plain[u"ctx_ok(member=None)"], u"**対照**")
        self.assertEqual(plain[u"**facts_for の件数**"], 1, u"**対照**")
        off = next(c for c in cs if u"fallback 無効" in c[u"場合"])
        on = next(c for c in cs if c[u"場合"].endswith(u"(P20)"))
        cons = next(c for c in cs if u"連結の要素が在る" in c[u"場合"])
        self.assertFalse(off[u"ctx_ok(member=None)"])
        self.assertEqual(off[u"**facts_for の件数**"], 0)
        self.assertTrue(on[u"ctx_ok(member=None)"])
        self.assertEqual(on[u"**facts_for の件数**"], 1)
        self.assertFalse(cons[u"ctx_ok(member=None)"], u"**2 つ目の条件**")
        self.assertEqual(cons[u"**facts_for の件数**"], 0)

    def test_5_only_the_two_failing_documents_meet_the_condition(self):
        mat = self.b[u"材料の性質(8 書類)"]
        self.assertEqual(len(mat), 8)
        meet = {d for d, v in mat.items() if v[u"**fallback の条件を満たす**"]}
        self.assertEqual(meet, {"S100YZ7E", "S100YZEV"})
        for d, v in mat.items():
            self.assertEqual(v[u"連結の財務要素の数"] == 0,
                             v[u"**fallback の条件を満たす**"], d)


class HarnessDefectTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.m = rec(MAP)

    def test_6_the_mapping_is_not_one_to_one(self):
        t = self.m[u"合計"]
        self.assertEqual(t[u"行"], 192)
        self.assertGreater(t[u"共有された行"], 0)
        self.assertEqual(t[u"T5"], t[u"T5 のうち 1 対 1"] + t[u"T5 のうち共有"]
                         + t[u"T5 のうち対応が付かない"])
        for k in (u"行", u"対応が付かない行", u"共有された主張", u"共有された行",
                  u"T5"):
            self.assertIn(u"| %d |" % t[k], self.t, k)
        self.assertIn(u"| **%d** |" % t[u"T5 のうち 1 対 1"], self.t)

    def test_7_both_denominators_are_printed(self):
        r = self.m[u"**Core 自身の特定率を分母で分ける**"]
        for k in (u"全部の T5 行(封の記録と同じ数)", u"**1 対 1 の行だけ**"):
            v = r[k]
            self.assertIn(u"**%s%%(%s/%s)**" % (v[u"率"], v[u"分子"], v[u"分母"]),
                          self.t, k)
        # **封の記録の数を書き換えていない**
        self.assertEqual(r[u"全部の T5 行(封の記録と同じ数)"][u"分子"], 15)
        self.assertEqual(r[u"全部の T5 行(封の記録と同じ数)"][u"分母"], 50)
        score = rec(os.path.join(FX, "score_2026-10-17.json"))
        self.assertEqual(
            score[u"採点"]["A"][u"正しい参照先の特定"][u"分母(T5 の件)"], 50)
        self.assertEqual(
            score[u"採点"]["A"][u"正しい参照先の特定"][u"分子"], 35)

    def test_8_the_seven_rows_are_four_claims(self):
        w = self.m[u"席が外した行(α の天井の分母)"]
        self.assertEqual(w[u"行"], 7)
        self.assertEqual(w[u"**異なる主張の数**"], 4)
        self.assertIn(u"**α の天井 0 は「0/7 行 = 0/%d 主張」である。**"
                      % w[u"**異なる主張の数**"], self.t)

    def test_9_the_defect_scope_is_stated(self):
        lim = self.m["limits"]
        self.assertTrue(any(u"席の答え・D′・D″ はこの欄の欠陥の影響を受けない" in x
                            or u"影響するのは Core 欄だけ" in x for x in lim))
        self.assertIn(u"**A 対 C′ の判定も変わらない**", self.t)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.p = rec(PRED)

    def test_10_every_claim_has_a_falsifiable_prediction(self):
        rows = self.p[u"主張ごとの予測(10 行 = 6 主張)"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(len(x[u"行"]) for x in rows), 10)
        for x in rows:
            self.assertTrue(x[u"外れる条件"], x[u"主張 id"])
            self.assertIn(u"`%s`" % x[u"主張 id"], self.t, x[u"主張 id"])

    def test_11_the_six_documents_must_not_move(self):
        d = self.p[u"書類ごとの予測"][u"**変わってはいけない 6 書類**"]
        self.assertEqual(len(d[u"書類"]), 6)
        self.assertNotIn("S100YZ7E", d[u"書類"])
        self.assertNotIn("S100YZEV", d[u"書類"])
        self.assertIn(u"**1 行でも動いたら、この予測は外れ**", self.t)

    def test_12_the_prediction_includes_a_cost_not_only_a_gain(self):
        n = self.p[u"数の予測"]
        self.assertIn(u"7 行増える",
                      n[u"Core-P が参照先を名指して正解でなかった行"][u"**P20 の予測**"])
        self.assertIn(u"**7 行増える**", self.t)
        self.assertIn(u"0/7", n[u"**α の天井(席が外した 7 行で Core が正解を持つ)**"]
                      [u"**P20 の予測**"])
        self.assertIn(u"**当たっても「Core が良くなった」とは書かない。**", self.t)

    def test_13_the_prediction_is_committed_before_the_measurement(self):
        """**予測より後に測る。**

        **file の有無では書かない**(測った瞬間に赤くなる門は、正しい手順を
        罰する。記憶 `order-gate-by-commit-not-file-absence`)。
        **commit の順**で書く ― 実測の記録が commit されているなら、
        予測の commit がその**祖先**であることを要求する。
        """
        def added(rel):
            out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H",
                                  "--", rel], cwd=ROOT, capture_output=True,
                                 text=True)
            shas = [s for s in out.stdout.split() if s]
            return shas[-1] if shas else None

        pred = added("fixtures/xbrl/cd8/branch_a_predictions_2026-10-17.json")
        if pred is None:
            self.skipTest(u"予測がまだ commit されていない(この便で commit する)")
        run = added(NOT_YET_MEASURED)
        if run is None:
            return                      # まだ測っていない。順序は破れていない
        self.assertNotEqual(pred, run, u"**同じ commit に在る**")
        self.assertTrue(
            subprocess.run(["git", "merge-base", "--is-ancestor", pred, run],
                           cwd=ROOT, capture_output=True).returncode == 0,
            u"**予測が実測より後に commit されている**")
        self.assertFalse(
            subprocess.run(["git", "merge-base", "--is-ancestor", run, pred],
                           cwd=ROOT, capture_output=True).returncode == 0)

    def test_14_engine_files_are_untouched(self):
        for rel, want in ENGINE_SHA.items():
            if want is None:
                continue
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            self.assertEqual(got, want, u"**%s が動いている**" % rel)
        self.assertIn(u"**engine は 1 行も変えていない。修正には入っていない。"
                      u"0 USD・席は呼んでいない。**", self.t)

    def test_15_it_stops_here(self):
        b = self.t[self.t.index(u"## §7"):]
        self.assertIn(u"**修正案も改善率も書かない。**", b)
        self.assertIn(u"**新しい封**であり、人間の判断が要る", self.t)


if __name__ == "__main__":
    unittest.main()
