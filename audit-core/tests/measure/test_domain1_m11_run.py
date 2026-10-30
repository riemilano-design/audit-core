# -*- coding: utf-8 -*-
"""段 11 の接続の結果(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §3・§4)を固定する。

守るのは 12 つ。
  1. **engine の sha が封と一致**し、違えば止まること(歯)
  2. **1 回だけ当てた**こと・`MIN_INDEPENDENT = 3`
  3. 記録の接続数・保留数が**その場で当て直した数と一致する**
  4. **A-1(旧)≥ 1**(③の発火機会が材料に在った)
  5. **A-1(新)= 0・A-3(新)= 0・未確認 0 件**(封 §3 の構造の事実が実測と一致)
  6. `a_counts` は**壊した bind で A-1 / A-2 / A-3 がそれぞれ動く**(歯)
  7. **X-2 は 3 通りとも 0 件**で、判定が合格であること
  8. **増分が 0 件であることが、そのまま記録に在る**(成功に読み替えない)
  9. 旧と新で**結んだ行が 1 件も違わない**こと(記録と一致)
 10. 新 engine で**候補の数が減った主張**が在ること(歳入側の裏づけが効いた跡)
 11. **R035 が VALUE_MISMATCH** で、engine が**正しい行**を指していること
 12. 採点対象が **20 件以上**(G-5 の線)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "m11_binds_2026-10-16.json")
MAT = os.path.join(FX, "m11_material_2026-10-16.json")
REP = os.path.join(FX, "m11_report_2026-10-16.json")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class EngineIsFrozenTest(unittest.TestCase):
    def setUp(self):
        self.m = _mod("m11run_t", "sheet_m11_run_2026-10-16.py")
        self.rec = load(REC)

    def test_1_shas_match_the_seal(self):
        self.assertEqual(self.m.check_shas(), self.rec["engine_sha"])
        self.assertEqual(len(self.m.ENGINE_SHA), 6)

    def test_2_a_moved_engine_stops_the_run(self):
        """**歯**: sha が 1 文字違えば結果を無効にする。"""
        old = dict(self.m.ENGINE_SHA)
        self.m.ENGINE_SHA["sheet_sainyuu_engine_2026-10-16.py"] = "0" * 16
        try:
            with self.assertRaises(SystemExit) as cm:
                self.m.check_shas()
            self.assertIn("結果は無効", str(cm.exception))
        finally:
            self.m.ENGINE_SHA.clear()
            self.m.ENGINE_SHA.update(old)

    def test_3_applied_once_and_threshold_untouched(self):
        self.assertEqual(self.rec["applied_times"], 1)
        self.assertTrue(self.rec["engine_unchanged"])
        self.assertEqual(self.rec["min_independent"], 3,
                         "**MIN_INDEPENDENT が 3 でない**")
        self.assertEqual(self.rec["old_engine"],
                         "measure/sheet_m7_engine_2026-10-15.py")
        self.assertEqual(self.rec["new_engine"],
                         "measure/sheet_sainyuu_engine_2026-10-16.py")


class ReproducedByRerunningTest(unittest.TestCase):
    """**記録を読むだけにしない。**engine をその場で当て直して突き合わせる。"""

    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11run_t2", "sheet_m11_run_2026-10-16.py")
        cls.rec = load(REC)
        m, M2 = cls.m, cls.m.M2
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        args = (M2.parse_soukatu(books[M2.SOUKATU]),
                M2.parse_kessan(books[M2.KESSAN]),
                M2.parse_meisai(books[M2.MEISAI]))
        report = load(REP)["report"]
        cls.o = m.OLD.run(report, *args)
        cls.n = m.NEW.run(report, *args)

    def test_4_splits_match(self):
        def grounded(r):
            return sum(1 for b in r["binds"] if b["state"] == "GROUNDED")
        self.assertEqual(grounded(self.o), self.rec["counts"]["old_split"]["接続数"])
        self.assertEqual(grounded(self.n), self.rec["counts"]["new_split"]["接続数"])
        self.assertEqual(len(self.n["claims"]), self.rec["counts"]["claims"])

    def test_5_alias_counts_match(self):
        self.assertEqual(len(self.o["alias"]["unconfirmed"]),
                         self.rec["alias_old"]["未確認"])
        self.assertEqual(len(self.n["alias"]["unconfirmed"]),
                         self.rec["alias_new"]["未確認"])
        self.assertEqual(len(self.n["alias"]["promoted_by_sainyuu"]),
                         len(self.rec["alias_new"]["歳入で昇格"]))


class StructuralFactsHoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)
        cls.c = cls.rec["claim_level_counts"]

    def test_6_the_opportunity_existed_in_the_old_engine(self):
        self.assertGreaterEqual(self.c["A-1 ③が発火した主張(旧 engine)"], 1,
                                "**③が旧 engine でも発火していない ― 未測定**")
        self.assertEqual(self.rec["alias_old"]["未確認"], 18)

    def test_7_the_new_engine_is_structurally_zero(self):
        self.assertEqual(self.c["A-1 ③が発火した主張(新 engine)"], 0)
        self.assertEqual(self.c["A-3 未確認の別名の行に結んだ主張(旧 / 新)"][1], 0)
        self.assertEqual(self.c["未確認の別名の数(旧 / 新)"], [18, 0])
        self.assertIn("構造的に 0", self.rec["note"])
        self.assertIn("生成より先に書いた", self.rec["note"])

    def test_8_scorable_meets_the_g5_line(self):
        self.assertGreaterEqual(self.rec["counts"]["scorable"], 20)


class ACountsHaveTeethTest(unittest.TestCase):
    """新 engine では未確認が 0 件なので、**壊した bind で当てないと黙る。**"""

    def setUp(self):
        self.m = _mod("m11run_t3", "sheet_m11_run_2026-10-16.py")
        self.alias = {"unconfirmed": [{"name": "東京都と場会計"}]}

    def test_9_each_branch_fires(self):
        a1 = self.m.a_counts(
            {"X": {"state": "UNVERIFIABLE",
                   "hold_reason": "会計が未確認の別名(独立した裏づけ 3 本未満)"}},
            self.alias, ["X"])
        self.assertEqual(len(a1["A-1"]), 1)
        self.assertEqual(len(a1["A-2"]), 0)
        a2 = self.m.a_counts(
            {"X": {"state": "UNVERIFIABLE", "hold_reason": "6 欄が一意でない(3 通り)"}},
            self.alias, ["X"])
        self.assertEqual(len(a2["A-1"]), 0)
        self.assertEqual(len(a2["A-2"]), 1, "③以外の保留を A-2 に数えていない")
        a3 = self.m.a_counts(
            {"X": {"state": "GROUNDED", "evidence": {"scope": "東京都と場会計",
                                                     "name": "運営費",
                                                     "column": "支出済額"}}},
            self.alias, ["X"])
        self.assertEqual(len(a3["A-3"]), 1,
                         "**未確認の別名の行に結んだのに数えていない**")
        skip = self.m.a_counts({"X": {"state": "POINTER_NOT_FOUND"}},
                               self.alias, ["X"])
        self.assertEqual([len(skip[k]) for k in ("A-1", "A-2", "A-3")], [0, 0, 0])


class X2AndIncrementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = load(REC)
        cls.c = cls.rec["claim_level_counts"]

    def test_10_x2_is_zero_in_all_three_ways(self):
        self.assertEqual(self.c["X-2対称(新。**合否**)"], 0)
        self.assertEqual(self.c["X-2三欄(新。**裏取り**)"], 0)
        self.assertEqual(self.c["X-2非対称(新。**開示だけ**)"], 0)
        v = self.rec["X-2 の判定(新)"]
        self.assertTrue(v["合格"], v)
        self.assertIn("開示だけ", v["理由"])
        self.assertGreater(self.rec["X-2(新 engine)"]["結んだ主張"], 0,
                           "結んだ主張が 0 件なら X-2 は未測定である")

    def test_11_the_increment_is_recorded_as_it_is(self):
        """**増分 0 を成功に読み替えない。**記録の数をそのまま固定する。"""
        self.assertEqual(self.c["C-4 旧では保留・新では接続になった主張"], 0,
                         "増分が 0 件でなくなったら結果の文も直すこと")
        self.assertEqual(self.rec["counts"]["old_split"]["接続数"],
                         self.rec["counts"]["new_split"]["接続数"])

    def test_12_no_connected_row_changed_but_candidates_shrank(self):
        bo = {b["claim_id"]: b for b in self.rec["binds_old"]}
        bn = {b["claim_id"]: b for b in self.rec["binds_new"]}
        moved = [k for k in bn if bo[k]["state"] == "GROUNDED"
                 and bn[k]["state"] == "GROUNDED"
                 and (bo[k].get("evidence") or {}) != (bn[k].get("evidence") or {})]
        self.assertEqual(moved, [], "結んだ行が動いた")
        # 減るのは `distinct_keys`(**6 欄の鍵の通り数**)である。
        # `candidates` は区間の候補の数で、別名を畳んでも減らない ― **測って確かめた**
        shrank = [k for k in bn
                  if (bo[k].get("distinct_keys") or 0) > (bn[k].get("distinct_keys") or 0)]
        self.assertGreater(len(shrank), 0,
                           "**鍵の通り数が 1 件も減っていない ― 歳入側の裏づけが効いた跡が無い**")
        self.assertEqual(
            [k for k in bn
             if (bo[k].get("distinct_keys") or 0) < (bn[k].get("distinct_keys") or 0)],
            [], "別名を畳んで鍵の通り数が**増えた**主張が在る")
        self.assertEqual(len(shrank), 7, "減った主張の数が記録と違う")

    def test_13_the_promoted_alias_found_the_right_row(self):
        """**R035**: ③が止めていた行を、新 engine は同定して値の食い違いを出した。"""
        bn = {b["claim_id"]: b for b in self.rec["binds_new"]}
        bo = {b["claim_id"]: b for b in self.rec["binds_old"]}
        self.assertIn("会計が未確認の別名", bo["R035"].get("hold_reason") or "")
        self.assertEqual(bn["R035"]["state"], "VALUE_MISMATCH")
        self.assertTrue(bn["R035"]["range_identified"])
        self.assertEqual(bn["R035"]["candidates"], 1)
        self.assertEqual(bn["R035"]["recomputed"], -48327000)
        mat = load(MAT)
        self.assertIn("運営費\t3,129,389,173\t-48,327,000", mat["prompt"],
                      "抜粋の行が変わった")


if __name__ == "__main__":
    unittest.main()
