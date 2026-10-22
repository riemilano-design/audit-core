# -*- coding: utf-8 -*-
"""採点器の**両側の正規化が対称か**を確かめる器を固定する(人間の指示 2026-10-16)。

> 両側の正規化が対称であることを確認する対象に含めるべきです。
> これは閾値の変更ではなく、**測定器が比較するものを正しく比較できているか**という問題。

守るのは 6 つ。
  1. S-1〜S-5 が**全部通る**(落ちた本数 0)
  2. **S-1 の「生の norm」は崩れなければならない** ― 崩れないならこの試験は
     段 8 の型を検出できていない。崩れた数が**段 8 で開示した X-1 11 / X-2 8**と
     一致すること(あの誤りをそのまま再現している証拠)
  3. S-3 恒等 ― 正解ラベルを engine の答えに入れたら満点(24 件 / 保留 1 件)
  4. S-4 の揺れが**実際に字を変えている**こと(揺れが無ければ S-4 は無意味)
  5. S-5 が**欄ごとに外れる**こと(照合器が緩くないこと)。親だけ 16 件で、
     残る 8 件は**空欄の款の行**(空欄は壊せない)
  6. `flip_blanks` は**空欄だけ**を替え、値の在る欄を触らないこと
  7. **閾値を 1 つも触っていない**こと
"""
import copy
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
SRC = os.path.join(MEASURE, "sheet_symmetry_audit_2026-10-16.py")
OUT = os.path.join(ROOT, "fixtures", "sheet", "symmetry_audit_2026-10-16.json")
SCORER = os.path.join(MEASURE, "sheet_m8_score_2026-10-16.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def mod():
    sp = importlib.util.spec_from_file_location("symmetry_audit_t", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class RecordTest(unittest.TestCase):
    def test_1_no_failure(self):
        r = load(OUT)
        self.assertEqual(r["failures"], [], "落ちた本が在る")
        self.assertEqual(len(r["checks"]), 5)

    def test_2_raw_norm_must_break(self):
        """**歯が在ることの証拠。**生の norm は片側だけ替えると崩れる。"""
        r = load(OUT)["checks"]["S-1 空欄の不変性(X)"]
        raw, folded = r["生の norm"], r["空欄を畳む"]
        self.assertEqual(raw["そのまま"], {"X-1": 19, "X-2": 0})
        # 段 8 の結果 §7 で開示した誤りの数そのもの
        self.assertEqual(raw["engine 側を空文字"], {"X-1": 11, "X-2": 8})
        self.assertEqual(raw["抜粋側を空文字"], {"X-1": 11, "X-2": 8})
        self.assertEqual(raw["両側を空文字"], {"X-1": 19, "X-2": 0})
        self.assertEqual(len({json.dumps(v, sort_keys=True)
                              for v in folded.values()}), 1)
        self.assertNotEqual(len({json.dumps(v, sort_keys=True)
                                 for v in raw.values()}), 1)

    def test_3_identity(self):
        r = load(OUT)["checks"]["S-3 恒等"]
        self.assertEqual(r["ラベルが答えの行"], 24)
        self.assertEqual(r["ラベルが保留の行"], 1)
        self.assertEqual(r["G-1"], 24)
        self.assertEqual(r["G-2"], 0)
        self.assertEqual(r["G-3"], 0)
        self.assertEqual(r["正しく保留"], 1)

    def test_4_score_invariance(self):
        r = load(OUT)["checks"]["S-2 空欄の不変性(採点)"]
        self.assertEqual(len({json.dumps(v, sort_keys=True)
                              for v in r.values()}), 1)
        self.assertEqual(r["そのまま"]["e2"], 0)

    def test_5_inverse_per_field(self):
        r = load(OUT)["checks"]["S-5 逆(緩すぎない)"]
        self.assertEqual(sorted(r), sorted(["会計", "階層", "親", "科目名", "列", "値"]))
        for k, v in r.items():
            self.assertEqual(v["G-1"], v["期待 G-1"], k)
            self.assertEqual(v["G-2"], v["期待 G-2"], k)
        # 親は**空欄の款が 8 件在るので 16 件しか壊せない**
        self.assertEqual(r["親"]["壊した行"], 16)
        self.assertEqual(r["親"]["G-1"], 8)
        for k in ("会計", "階層", "科目名", "列", "値"):
            self.assertEqual(r[k]["壊した行"], 24, k)
            self.assertEqual(r[k]["G-1"], 0, k)


class BehaviourTest(unittest.TestCase):
    def test_6_flip_blanks_touches_only_blanks(self):
        m = mod()
        src = {"scope": "一般会計", "parent": None, "name": "", "column": "  "}
        out = m.flip_blanks(src, ("scope", "parent", "name", "column"), "")
        self.assertEqual(out["scope"], "一般会計", "値の在る欄を触った")
        for k in ("parent", "name", "column"):
            self.assertEqual(out[k], "")
        back = m.flip_blanks(src, ("parent",), None)
        self.assertIsNone(back["parent"])
        self.assertEqual(src["parent"], None, "入力を書き換えた")

    def test_7_wobble_really_changes_the_text(self):
        """揺れが字を変えていなければ S-4 は無意味。"""
        m = mod()
        ev = {"scope": u"一般会計", "parent": u"福祉費>子供費", "name": u"児童費",
              "column": u"支出済額", "value": u"1234567"}
        w = m.wobble(ev)
        for k in ev:
            self.assertNotEqual(w[k], ev[k], k)
        self.assertIn(u",", w["value"])
        self.assertIn(u"円", w["value"])
        self.assertIn(u"＞", w["parent"])

    def test_8_folded_key_folds_both_blank_forms(self):
        m = mod()
        a = m.folded_key({"scope": "一般会計", "level": "款", "parent": None,
                          "name": "福祉費"})
        b = m.folded_key({"scope": "一般会計", "level": "款", "parent": "",
                          "name": "福祉費"})
        self.assertEqual(a, b)
        # **生の鍵は畳まない**(だから段 8 で崩れた)
        self.assertNotEqual(m.raw_key({"parent": None}), m.raw_key({"parent": ""}))

    def test_9_runs_green_now(self):
        """**一回限りの記録ではなく、いま走らせて通ること。**"""
        m = mod()
        m.set_alias()
        rec, mat, s1, s2 = m.load()
        r1 = m.s1_blank_invariance(rec, mat)
        self.assertEqual(len({json.dumps(v, sort_keys=True)
                              for v in r1["空欄を畳む"].values()}), 1)
        b, claims, scorable, n_lab, n_ver, _ = m.binds_from_labels(rec, s1, s2)
        t = m.S.tally(b, claims, scorable, s1, s2)
        self.assertEqual(t["g1"], n_lab)
        self.assertEqual(t["g2"] + t["g3"], 0)
        self.assertEqual(t["hold_ok"], n_ver)


class JudgeTest(unittest.TestCase):
    """**判定そのものに歯が在るか。**壊した報告を食わせて赤になることを確かめる
    (記憶 `guard-that-only-fires-on-failure.md`: 正常な入力では発火しない守りは、
    故障を作って当てないと測れない)。
    """

    def setUp(self):
        self.m = mod()
        self.rep = load(OUT)["checks"]

    def judge(self, mutate):
        rep = copy.deepcopy(self.rep)
        mutate(rep)
        return self.m.judge(rep)

    def test_20_real_record_passes(self):
        self.assertEqual(self.m.judge(copy.deepcopy(self.rep)), [])

    def test_21_shrinking_the_x_tags_is_red(self):
        def f(r):
            del r["S-1 空欄の不変性(X)"]["空欄を畳む"]["抜粋側を空文字"]
        self.assertTrue(self.judge(f))

    def test_22_shrinking_the_score_tags_is_red(self):
        def f(r):
            del r["S-2 空欄の不変性(採点)"]["席側を空文字"]
        self.assertTrue(self.judge(f))

    def test_23_folded_not_invariant_is_red(self):
        def f(r):
            r["S-1 空欄の不変性(X)"]["空欄を畳む"]["両側を空文字"] = {"X-1": 1, "X-2": 1}
        self.assertTrue(self.judge(f))

    def test_24_raw_invariant_is_red(self):
        """生の norm が崩れないなら、この試験は段 8 の型を検出できていない。"""
        def f(r):
            raw = r["S-1 空欄の不変性(X)"]["生の norm"]
            for k in raw:
                raw[k] = {"X-1": 19, "X-2": 0}
        self.assertTrue(self.judge(f))

    def test_25_identity_with_e2_is_red(self):
        def f(r):
            r["S-3 恒等"]["G-2"] = 1
        self.assertTrue(self.judge(f))
        def g(r):
            r["S-3 恒等"]["G-3"] = 1
        self.assertTrue(self.judge(g))

    def test_26_empty_wobble_is_red(self):
        def f(r):
            r["S-4 退化値"]["揺れが字を変えた欄"] = []
        self.assertTrue(self.judge(f))

    def test_27_inverse_without_damage_is_red(self):
        def f(r):
            r["S-5 逆(緩すぎない)"]["値"]["壊した行"] = 0
        self.assertTrue(self.judge(f))

    def test_28_inverse_mismatch_is_red(self):
        def f(r):
            r["S-5 逆(緩すぎない)"]["列"]["G-1"] = 24
        self.assertTrue(self.judge(f))

    def test_29_missing_field_in_inverse_is_red(self):
        def f(r):
            del r["S-5 逆(緩すぎない)"]["値"]
        self.assertTrue(self.judge(f))

    def test_31_score_not_invariant_is_red(self):
        """採点の数が入れ替えで動いたら赤(M8 が黙った穴)。"""
        def f(r):
            r["S-2 空欄の不変性(採点)"]["席側を空文字"]["g1"] = 18
        self.assertTrue(self.judge(f))

    def test_30_wobble_changed_lists_every_field(self):
        self.assertEqual(self.m.wobble_changed(),
                         ["column", "name", "parent", "scope", "value"])
        self.assertEqual(self.rep["S-4 退化値"]["揺れが字を変えた欄"],
                         ["column", "name", "parent", "scope", "value"])


class NoThresholdChangeTest(unittest.TestCase):
    def test_10_thresholds_untouched(self):
        """**閾値を触っていない。**採点器の線は封のまま。"""
        t = text(SCORER)
        self.assertIn(u'"pass": "≥ 50%"', t)
        self.assertIn(u'"pass": "≥ 80%"', t)
        self.assertIn(u'"pass": "= 0 件"', t)
        self.assertIn(u'"pass": "≥ 20"', t)
        self.assertIn(u'"pass": "≥ 1 件"', t)

    def test_11_audit_does_not_import_thresholds(self):
        """この器は**採点の線を読み替えない**(tally を呼ぶだけ)。"""
        t = text(SRC)
        self.assertNotIn(u"0.50", t)
        self.assertNotIn(u"0.80", t)
        self.assertIn(u"**閾値ではなく測定器の検査**", t)

    def test_12_s5_is_declared_necessary(self):
        t = text(SRC)
        self.assertIn(u"**S-5 が無いと S-3 は無意味である。**", t)


if __name__ == "__main__":
    unittest.main()
