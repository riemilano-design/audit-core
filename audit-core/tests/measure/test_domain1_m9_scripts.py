# -*- coding: utf-8 -*-
"""段 9 の run / score / ラベル材料の script を固定する(封 §4・§6・§11)。

**ラベルより先・生成より先に commit する。**守るのは 7 つ。
  1. run と score が **engine の sha を封と照合して止まる**
  2. **主実験の線は 6 本**で、閾値が封のまま
  3. **G-7 は線でない**(記録のみ)。**G-8 = 0 は線に残る**
  4. **A-2 を③の成功に数えない**・**A-1 = 0 なら未測定**
  5. G-4 は**別立て**で、分母を (a)(b) に割り、**≤ 2 件なら合格扱いにしない**
  6. ラベル材料は**段 9 の spec から問いを作り**、会計の 2 本以外が動けば止まる
  7. 禁じた語に **③・発火・A-1・A-3・X-2** が入っている(席に漏らさない)
"""
import hashlib
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def text(p):
    with io.open(os.path.join(MEASURE, p), encoding="utf-8") as fh:
        return fh.read()


class ShaGateTest(unittest.TestCase):
    def setUp(self):
        self.R = _mod("run9_s", "sheet_m9_run_2026-10-16.py")

    def test_1_shas_match(self):
        self.assertEqual(sorted(self.R.ENGINE_SHA),
                         ["sheet_m5_engine_2026-10-15.py",
                          "sheet_m7_engine_2026-10-15.py",
                          "sheet_parent_backing_2026-10-16.py"])
        for f, pre in self.R.ENGINE_SHA.items():
            h = hashlib.sha256(
                io.open(os.path.join(MEASURE, f), "rb").read()).hexdigest()
            self.assertTrue(h.startswith(pre), f)
        self.assertEqual(self.R.check_shas(), dict(self.R.ENGINE_SHA))

    def test_2_sha_gate_has_teeth(self):
        """**壊した期待値で止まること**(正常時は発火しない守り)。"""
        R = self.R
        keep = dict(R.ENGINE_SHA)
        try:
            R.ENGINE_SHA["sheet_m7_engine_2026-10-15.py"] = "0000000000000000"
            with self.assertRaises(SystemExit) as cm:
                R.check_shas()
            self.assertIn("結果は無効である", str(cm.exception))
        finally:
            R.ENGINE_SHA.clear()
            R.ENGINE_SHA.update(keep)

    def test_3_score_checks_the_sha_too(self):
        self.assertIn("RUN.check_shas()", text("sheet_m9_score_2026-10-16.py"))


class LinesTest(unittest.TestCase):
    def setUp(self):
        self.S = _mod("score9_s", "sheet_m9_score_2026-10-16.py")
        self.t = text("sheet_m9_score_2026-10-16.py")

    def test_4_thresholds(self):
        self.assertEqual(self.S.G1P_MIN, 0.50)
        self.assertEqual(self.S.G4_MIN, 0.80)
        self.assertEqual(self.S.G5_MIN, 20)

    def test_5_six_main_lines(self):
        for s in ("A-1 ③が発火した主張", "A-3 未確認の別名の行に結んだ主張",
                  "E2 誤受理", "X-2 抜粋に無い行に結んだ主張", "G-5 母数",
                  "G-1′ ③で止めた主張を除いた接続の正確さ"):
            self.assertIn('"%s"' % s, self.t, s)
        self.assertIn("main_ok = all(v[\"ok\"] for v in lines.values())", self.t)

    def test_6_g7_is_not_a_line_and_g8_is(self):
        self.assertIn('"G-7 正しい接続の増分(線にしない)"', self.t)
        self.assertIn('"G-8 誤受理の増分": {"count": g8, "pass": "= 0 件",', self.t)
        # G-7 は `lines`(合否)に入っていない
        block = self.t.split("    lines = {")[1].split("    main_ok")[0]
        self.assertNotIn("G-7", block)
        self.assertNotIn("G-4", block)

    def test_7_a1_zero_is_unmeasured(self):
        self.assertIn('unmeasured = len(a1) == 0 or den_p == 0', self.t)
        self.assertIn('overall = "未測定(③が発火していない)"', self.t)

    def test_8_a2_is_not_success(self):
        self.assertIn('"注": "**③の成功に数えない**"', self.t)

    def test_9_g4_separate_and_split(self):
        self.assertIn("併測 G-4(③の合否に入れない)", self.t)
        self.assertIn('"(a) 両席が一致して保留"', self.t)
        self.assertIn('"(b) 2 席が食い違って保留"', self.t)
        self.assertIn('"evaluable": g4_den > 2', self.t)
        self.assertIn("4 段続けて未確認", self.t)

    def test_10_g1prime_guard(self):
        self.assertIn("g1p_usable = stopped * 2 <= n", self.t)
        self.assertIn("**止めた主張が採点対象の半分を超えたら G-1′ を成果として", self.t)

    def test_11_raw_g1_is_always_written(self):
        self.assertIn('"生の G-1(線にしない)"', self.t)

    def test_12_uses_the_audited_comparator(self):
        """**段 8 の対の作り方をそのまま使う**(対称性を S-1〜S-5 で確かめた器)。"""
        self.assertIn("tally = S8.tally", self.t)
        self.assertIn("confirmed = S8.confirmed", self.t)
        self.assertIn("sheet_symmetry_audit_2026-10-16.py", self.t)

    def test_13_folds_blanks_on_both_sides(self):
        self.assertIn('return tuple(norm(d.get(k)) or ""', self.t)
        self.assertIn('return tuple(norm(d.get(k)) or ""',
                      text("sheet_m9_run_2026-10-16.py"))


class LabelMaterialTest(unittest.TestCase):
    def setUp(self):
        self.M = _mod("lab9_s", "sheet_m9_label_material_2026-10-16.py")

    def test_14_banned_words(self):
        for w in ("③", "発火", "A-1", "A-3", "X-2", "未確認", "別名",
                  "独立した裏づけ", "封", "engine"):
            self.assertIn(w, self.M.BANNED, w)

    def test_15_question_comes_from_the_m9_spec(self):
        self.assertEqual(self.M.L9.SPEC["version"], "2026-10-16/m9")
        q = self.M.L9.question_text()
        self.assertTrue(self.M.L9.check_question(q))
        self.assertEqual(self.M.diff_against_m8(q) != [], True,
                         "段 8 との差が無い(直しが効いていない)")

    def test_16_diff_gate_has_teeth(self):
        """**会計の 2 本以外が動いたら止まること。**"""
        q = self.M.L9.question_text()
        broken = q.replace("[R-値-1]", "[R-値-1改]")
        with self.assertRaises(AssertionError):
            self.M.diff_against_m8(broken)

    def test_17_question_rules_leak_no_banned_word(self):
        q = self.M.L9.question_text()
        for w in self.M.BANNED:
            self.assertNotIn(w, q, "問いに禁じた語が在る: %s" % w)


if __name__ == "__main__":
    unittest.main()
