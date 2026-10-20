# -*- coding: utf-8 -*-
"""診断(docs/XBRL_PNF_DIAG_2026-10-17.md)の門。

**数は `fixtures/xbrl/cd8/pnf_diag_2026-10-17.json` を正本に突き合わせる。**
**「engine を触っていない」は sha で確かめる**(文を信じない)。
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
DOC = os.path.join(ROOT, "docs", "XBRL_PNF_DIAG_2026-10-17.md")
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "pnf_diag_2026-10-17.json")
# 診断の前後で動いていないこと(封 v2 の段 5 の時点の engine)
ENGINE_SHA = {"adapters/xbrl/recipes.py": "e2bda6aee13880ff",
              "adapters/xbrl/resolve.py": "a41043763c1d4073",
              "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
              "adapters/xbrl/vocabulary.py": "bcf559308bda0cc6"}

# 2026-10-20 追記(上の ENGINE_SHA は、その記録を測った時点の sha で、消さない)。**宣言された遷移**: 封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md
# (名指しの直し P21。engine を変える)で変わった sha。その封が履歴に在り、値がその封の後の値のときだけ受け入れる
# (tests/measure/test_xbrl_cd_seal.py の FROZEN_LATER と同じ型: 「ずれ」と「宣言された遷移」を言い分ける)。
SEAL_NAMING_FIX = "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md"
SEAL_PERIOD_BIND = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"    # 2026-10-20 追記: 期を縛る P22 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"    # 2026-10-21 追記: 丸めの帯 P23 の段 1(下の ENGINE_LATER の vocabulary.py・recipes.py の遷移)
ENGINE_LATER = {
    # 2026-10-20(期を縛る P22 の段 1): 封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md(engine を変える。人間の承認 2026-10-20「君に任せる」)で
    # recipes.py の _direct_value_claim の最初の枝に旗 period_bind の塊(+4 行)を足した。sha は 名指しの直し 段 1 5eb80a2 のとき 2f692bca1eac3cd3(残す。測った時点の値)、
    # P22 の段 1 で 65a37869f053a60e(独立監査の指摘で subj and を足した後。足す前の中間値 58178740921eaa04 は commit していない)。受け入れるのは、その封が履歴に在り、値が P22 の段 1 の後の値のときだけ。
    # 2026-10-21(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に _mag_trunc(profile, rounding)(旗 truncate_abs_band を、書類の丸め方が切り捨てと決まった 2 周目だけ帯に渡す)を足し、3 か所の呼び出しを置き換えた。
    # 65a37869f053a60e(P22 の段 1)は残す(測った時点の値)、P23 の段 1 で d5308700eae78c10。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
    "adapters/xbrl/recipes.py": ("d5308700eae78c10", SEAL_ROUNDING),
    # 2026-10-20(段 2): 既定を P20 -> P21 にした(vocabulary.py の DEFAULT_PROFILE と決定の注記。同じ封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2)。
    # vocabulary.py の sha は 段 1 5eb80a2 のとき 6c6db4c75e571a6c(残す。段 1 の結果の記録が測った時点の値)、段 2 で 1205b30b496090ef。
    # 受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-20(期を縛る P22 の段 1): 同じ封で vocabulary.py に旗 period_bind と P22 を足した(DEFAULT_PROFILE は P21 のまま)。
    # sha は 段 1 5eb80a2 で 6c6db4c75e571a6c・名指しの直し 段 2 で 1205b30b496090ef(どちらも残す。測った時点の値)、P22 の段 1 で 1fdb48e7e3ba58ce。
    # 2026-10-20(期を縛る P22 の段 2): 既定を P21 -> P22 にした(vocabulary.py の DEFAULT_PROFILE と決定の注記だけ。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2・E-8。人間の承認 2026-10-20「任せる」)。
    # 段 1 3320c8c の 1fdb48e7e3ba58ce は残す(測った時点の値)、段 2 で 25a3c0992e10daaa。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-21(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 truncate_abs_band・P23(= P22 + 率の旗 + truncate_abs_band)・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
    # 25a3c0992e10daaa(P22 の段 2)は残す(測った時点の値)、P23 の段 1 で f7b8d925eb6787ec。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
    "adapters/xbrl/vocabulary.py": ("f7b8d925eb6787ec", SEAL_ROUNDING),
}


def assert_pinned_or_declared(test, rel, got, want):
    if got != want and rel in ENGINE_LATER:
        later, seal_rel = ENGINE_LATER[rel]
        added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel],
                               cwd=ROOT, capture_output=True, text=True).stdout.split()
        test.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
        test.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
        return
    test.assertEqual(got, want, u"**%s が動いている**" % rel)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


def name_of(key):
    return key.split("@", 1)[0]


class ObservationTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_1_every_row_tried_zero_keys(self):
        rows = self.r["rows"]
        self.assertEqual(len(rows), 10)
        for x in rows:
            self.assertEqual(x[u"**試した key**"], [], x[u"id"])
            self.assertEqual(x[u"結果の参照先"], [], x[u"id"])
            self.assertEqual(x[u"Core の reason"], "no_element", x[u"id"])
            self.assertEqual(x[u"Core の state"], "POINTER_NOT_FOUND", x[u"id"])
        self.assertIn(u"**10 行すべてで、試した key は 0 本である。**", self.t)

    def test_2_the_gold_fact_is_in_the_instance(self):
        rows = self.r["rows"]
        n = sum(1 for x in rows
                if x[u"正解の (要素名, context) が instance に在る"])
        self.assertEqual(n, 10, u"**Core は正解の fact を読み込んでいる**")
        self.assertIn(u"| 正解の `(要素名, context)` が instance に在った行 "
                      u"| **%d / 10** |" % n, self.t)

    def test_3_gold_elements_live_only_in_dimensioned_contexts(self):
        rows = self.r["rows"]
        for x in rows:
            self.assertFalse(x[u"**正解の要素名に次元なしの context が在るか**"],
                             x[u"id"])
            ctxs = x[u"**正解の要素名が在る context**"]
            self.assertTrue(ctxs, x[u"id"])
            for _c, mem in ctxs:
                self.assertNotEqual(mem, u"次元なし", x[u"id"])

    def test_4_the_two_places_are_both_printed_with_the_records_counts(self):
        k = self.r[u"**観測**"][u"候補 0 の内訳ごと"]
        self.assertEqual(sum(k.values()), 10)
        self.assertIn(u"**%d 行**は語彙も subject も正解の要素名そのものを持っていた"
                      % k[u"語彙は正解の要素を持っていた(落ちたのは後段)"], self.t)
        self.assertIn(u"残る **%d 行**は、subject に当たった要素の中に正解が無い"
                      % k[u"subject に当たった要素に正解が無い"], self.t)

    def test_5_the_three_rows_had_the_gold_element_in_the_vocabulary(self):
        """**後段で落ちた行は、要素を選べていた**(これが仮説 A の根拠)。"""
        after = [x for x in self.r["rows"]
                 if x[u"**候補 0 の内訳**"][u"どこで落ちたか"]
                 == u"語彙は正解の要素を持っていた(落ちたのは後段)"]
        self.assertTrue(after)
        for x in after:
            hit = [h.lower() for h in
                   x[u"**候補 0 の内訳**"][u"その語に当たった要素"] or []]
            self.assertIn(name_of(x[u"正解の key"]), hit, x[u"id"])

    def test_6_the_wiring_gate_is_recorded_for_both_documents(self):
        for doc, v in self.r[u"書類ごと"].items():
            self.assertTrue(v[u"**配線が verify_document と一致**"], doc)
            self.assertTrue(v[u"材料の sha256 が封の記録と一致"], doc)
            self.assertGreater(v[u"次元つきの context を持つ fact"],
                               0.9 * v[u"instance の fact 数"], doc)
        self.assertIn(u"一致しなければ止める", self.t)


class DisciplineTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_7_engine_files_are_untouched(self):
        for rel, want in ENGINE_SHA.items():
            if want is None:
                continue
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            assert_pinned_or_declared(self, rel, got, want)
        self.assertIn(u"**Core の関数・正規化・探索挙動は 1 行も変えていない。"
                      u"費用 0 USD・席は呼んでいない。**", self.t)

    def test_8_interpretation_is_marked_as_hypothesis(self):
        b = self.t[self.t.index(u"## §4 解釈"):self.t.index(u"## §5")]
        self.assertIn(u"**仮説。測るまで断定しない**", self.t)
        self.assertIn(u"**これは仮説である。**", b)
        self.assertIn(u"**2 つは別の直しである。**", b)

    def test_9_my_two_measurement_defects_are_recorded(self):
        b = self.t[self.t.index(u"## §5 言えないこと"):]
        self.assertIn(u"**誤った記録を作り、作り直した**", b)
        self.assertIn(u"normalize-both-sides-of-a-comparison", b)
        self.assertIn(u"**数の主張では `word` は `None` である。**", b)

    def test_10_the_record_keeps_its_limits(self):
        lim = self.r["limits"]
        self.assertGreaterEqual(len(lim), 4)
        self.assertTrue(any(u"直していない" in x for x in lim))
        self.assertTrue(any(u"両側に同じ関数" in x for x in lim))

    def test_11_alpha_comes_after_this(self):
        b = self.t[self.t.index(u"## §6"):]
        self.assertIn(u"**α はこの後である。**", b)
        self.assertIn(u"独立監査の GO が要る", b)


if __name__ == "__main__":
    unittest.main()
