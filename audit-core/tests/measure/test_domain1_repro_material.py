# -*- coding: utf-8 -*-
"""別資料(令和５年度)の取得・プロファイル・抜粋を固定する(**費用 0 の段**)。

**凍結した令和６年度の側を汚していないこと**と、
**下見の費用が人間の目安を超えていること**を門で見る。
"""
import hashlib
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
OPENED = os.path.join(FX, "repro_opened_2026-10-17.json")
TOC = os.path.join(FX, "repro_toc_2026-10-17.json")
MAT = os.path.join(FX, "repro_material_2026-10-17.json")
MAT11 = os.path.join(FX, "m11_material_2026-10-16.json")


def _mod(name, rel):
    sp = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "measure", rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


F = _mod("fetch5_for_test", "sheet_repro_fetch_2026-10-17.py")
PR = _mod("profile5_for_test", "sheet_repro_profile_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.r = load(OPENED)

    def test_1_five_files_all_present_with_the_sealed_bytes(self):
        self.assertEqual(len(self.r["files"]), 5)
        self.assertTrue(self.r["全部そろった"])
        self.assertTrue(self.r["バイト数が封と一致"])
        for x in self.r["files"]:
            self.assertEqual(x["bytes"], x["expected_bytes"], x["name"])
            self.assertEqual(len(x["sha256"]), 64, x["name"])
            self.assertIn("05kessan", x["name"], "令和５年度の file")

    def test_2_the_derived_file_was_not_fetched(self):
        skipped = self.r["**取らなかったもの**"]
        self.assertEqual(len(skipped), 1)
        self.assertIn("jissitusyuusi", skipped[0]["name"])
        names = {x["name"] for x in self.r["files"]}
        self.assertNotIn(skipped[0]["name"], names)

    def test_3_raw_files_live_outside_the_repo(self):
        self.assertTrue(self.r["**生ファイルは repo に置かない**"])
        self.assertNotIn(ROOT, self.r["cache"])
        for x in self.r["files"]:
            self.assertFalse(os.path.exists(os.path.join(FX, x["name"])),
                             "生ファイルが repo に在る: %s" % x["name"])


class ProfileTest(unittest.TestCase):
    def test_4_the_profile_switches_and_restores(self):
        self.assertFalse(PR.is_year5(), "既定は令和６年度")
        before = (PR.M2.SOUKATU, PR.M2.KESSAN, PR.M2.MEISAI,
                  PR.P1M.SAINYUU, PR.P1M.MEISAI_SAINYUU, PR.SE.P1REC)
        with PR.year5():
            self.assertTrue(PR.is_year5())
            self.assertEqual(PR.M2.KESSAN, F.KESSAN)
            self.assertEqual(PR.P1M.SAINYUU, F.SAINYUU)
            self.assertEqual(PR.SE.P1REC, PR.TOC_OUT)
        self.assertEqual((PR.M2.SOUKATU, PR.M2.KESSAN, PR.M2.MEISAI,
                          PR.P1M.SAINYUU, PR.P1M.MEISAI_SAINYUU, PR.SE.P1REC),
                         before, "**凍結した側を汚した**")
        self.assertFalse(PR.is_year5())

    def test_5_it_restores_even_when_the_body_raises(self):
        before = PR.M2.KESSAN
        try:
            with PR.year5():
                raise RuntimeError("わざと落とす")
        except RuntimeError:
            pass
        self.assertEqual(PR.M2.KESSAN, before)

    def test_6_the_toc_was_rebuilt_by_the_frozen_rule(self):
        r = load(TOC)
        self.assertIn("meisai_sainyuu()", r["rule"])
        self.assertIn("規則は変えていない", r["rule"])
        self.assertEqual(r["source"], F.MEISAI_SAINYUU)
        self.assertEqual(r["toc_entries"], len(r["meisai_sainyuu"]["toc"]))
        self.assertGreater(r["toc_entries"], 0)


class MaterialStoppedTest(unittest.TestCase):
    """**封 §1-1 で止まったこと**を固定する(parser を直して通していない)。"""

    def setUp(self):
        self.r = load(MAT)

    def test_7_nothing_but_the_file_changed(self):
        for v in self.r["別資料"].values():
            self.assertIn("05kessan", v, v)

    def test_8_it_stopped_and_nothing_was_generated(self):
        self.assertTrue(self.r["**止めた**"])
        self.assertIn("決算書 歳出の行が 0(表 2 が 0 行)", self.r["止めた理由"])
        self.assertIn("生成していない", self.r["step"])
        self.assertIn("parser を直して通すことはしない", self.r["規則"])

    def test_9_the_prompt_is_not_in_the_record(self):
        """**止めたら指示文を記録に入れない。**入れると生成できてしまう。"""
        self.assertNotIn("prompt", self.r)
        self.assertIn("**指示文は記録に入れていない**", self.r)

    def test_10_the_diagnosis_names_the_three_deciding_sites(self):
        d = self.r["診断: 年度の字で動いている所"]
        decides = d["判定に使っている"]
        self.assertEqual(len(decides), 3, decides)
        files = sorted(s["file"] for s in decides)
        self.assertEqual(files, ["measure/sheet_m2_structure_2026-10-15.py",
                                 "measure/sheet_m2_structure_2026-10-15.py",
                                 "measure/sheet_sainyuu_p1_2026-10-16.py"])
        self.assertGreater(d["字(説明・指示文)の数"], 0)
        self.assertIn("指示文も年度の字を持っている",
                      " ".join(k for k in self.r))

    def test_11_the_material_really_was_the_other_year(self):
        """**これが module 実体の取り違えを捕まえた門である。**

        最初の実行は令和６年度のままで、抜粋が段 11 と byte 一致していた。
        **別資料を読めば数が違う**ことを固定する。
        """
        old = load(MAT11)
        self.assertNotEqual(self.r["value_cells"], old["value_cells"])
        self.assertEqual(self.r["value_cells"], 716)
        self.assertEqual(self.r["counts"]["表2_行"], 0)
        self.assertEqual(old["counts"]["表2_行"], 24)
        self.assertEqual(old["value_cells"], 176, "**段 11 の記録が動いた**")

    def test_12_the_estimate_is_recorded_but_unused(self):
        e = self.r["下見の費用"]
        self.assertEqual(e["費-1 報告文 + 2 席"], 3.1071)
        self.assertEqual(e["費-2 報告文 + 1 席(sonnet)"], 2.7546)
        self.assertFalse(e["費-1 は目安の中か"])
        self.assertIn("生成しない", self.r["次の段"])


class StructureCheckTest(unittest.TestCase):
    """**止める判定は 1 か所**。壊した数で 1 本ずつ当てる。"""

    def setUp(self):
        self.M = _mod("repro_mat_for_test",
                      "sheet_repro_material_2026-10-17.py")

    def test_13_each_zero_stops_it(self):
        ok = {"表1_行": 20, "表2_行": 24, "表3_行": 52}
        self.assertEqual(self.M.structure_check(ok), (False, []))
        for k, word in (("表1_行", "会計の集合が取れない"),
                        ("表2_行", "決算書 歳出の行が 0"),
                        ("表3_行", "事項別明細 歳出の行が 0")):
            bad = dict(ok)
            bad[k] = 0
            stopped, why = self.M.structure_check(bad)
            self.assertTrue(stopped, k)
            self.assertTrue(any(word in w for w in why), (k, why))

    def test_14_the_year_scan_finds_the_deciding_sites(self):
        sites = self.M.year_coupled_sites()
        decides = [s for s in sites if s["種類"] == "判定に使っている"]
        self.assertEqual(len(decides), 3)
        for s in sites:
            self.assertNotIn("sheet_repro_", s["file"],
                             "自分の file は数えない")


if __name__ == "__main__":
    unittest.main()
