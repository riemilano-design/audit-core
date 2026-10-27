# -*- coding: utf-8 -*-
"""役割を替える実験の結果(docs/XBRL_ROLE_SWAP_RESULT_2026-10-17.md)の門。

**数は記録を正本に突き合わせる。合成規則は壊した入力で確かめる。**
"""
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DOC = os.path.join(ROOT, "docs", "XBRL_ROLE_SWAP_RESULT_2026-10-17.md")
REC = os.path.join(FX, "role_swap_2026-10-17.json")
SEAL_REL = "docs/XBRL_ROLE_SWAP_SEAL_2026-10-17.md"
ENGINE_SHA = {"core/py/audit_core/verify.py": "d29b21dccec8af24",
              "adapters/xbrl/comparators.py": "d8706338325e725b",
              "adapters/xbrl/resolve.py": "a41043763c1d4073",
              "adapters/xbrl/recipes.py": "e2bda6aee13880ff",
              "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad"}

# 2026-10-20 追記(上の ENGINE_SHA は、その記録を測った時点の sha で、消さない)。**宣言された遷移**: 封
# docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md(名指しの直し P21。engine を変える)で変わった sha。その封が履歴に在り、
# 値がその封の後の値のときだけ受け入れる(tests/measure/test_xbrl_cd_seal.py の FROZEN_LATER と同じ型)。
SEAL_NAMING_FIX = "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md"
SEAL_PERIOD_BIND = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"    # 2026-10-20 追記: 期を縛る P22 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"    # 2026-10-21 追記: 丸めの帯 P23 の段 1(下の ENGINE_LATER の vocabulary.py・recipes.py の遷移)
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
# recipes.py の 3461c3f8b7af6675(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
ENGINE_LATER = {
    # 2026-10-20(期を縛る P22 の段 1): 封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md(engine を変える。人間の承認 2026-10-20「君に任せる」)で
    # recipes.py の _direct_value_claim の最初の枝に旗 period_bind の塊(+4 行)を足した。sha は 名指しの直し 段 1 5eb80a2 のとき 2f692bca1eac3cd3(残す。測った時点の値)、
    # P22 の段 1 で 65a37869f053a60e(独立監査の指摘で subj and を足した後。足す前の中間値 58178740921eaa04 は commit していない)。受け入れるのは、その封が履歴に在り、値が P22 の段 1 の後の値のときだけ。
    # 2026-10-21(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に _mag_trunc(profile, rounding)(旗 truncate_abs_band を、書類の丸め方が切り捨てと決まった 2 周目だけ帯に渡す)を足し、3 か所の呼び出しを置き換えた。
    # 65a37869f053a60e(P22 の段 1)は残す(測った時点の値)、P23 の段 1 で d5308700eae78c10。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
    # 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に旗 vocab_2026_10_21・frame_rebind の塊(+224 行・既存の行は 1 つも書き換えない)を足した(DEFAULT_PROFILE は P22 のまま)。
    # d5308700eae78c10(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 3461c3f8b7af6675。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
    # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に G1〜G5 の塊(+251 行・-1 行。既存の行の書き換えは数の読み取りの for 文 1 行だけ) を足した。
    # bff243f13429b553(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 181b370420ab751b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
    # 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
    "adapters/xbrl/recipes.py": ("52d645e713c53c1c", SEAL_P27),
}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


def pct(v):
    return u"%s%%(%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])


def _mod():
    sp = importlib.util.spec_from_file_location(
        "role_swap", os.path.join(ROOT, "measure",
                                  "xbrl_role_swap_2026-10-17.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class VerdictTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()
        r4 = self.r[u"R-4 最終判定の正確性"]
        self.inj = r4[[k for k in r4 if k.startswith(u"注入")][0]]
        self.cl = r4[[k for k in r4 if k.startswith(u"無改変")][0]]

    def test_1_b_does_not_beat_a(self):
        self.assertEqual(self.inj[u"検出(誤りが在る)"]["A"][u"分子"],
                         self.inj[u"検出(誤りが在る)"]["B"][u"分子"])
        self.assertEqual(self.cl[u"偽警報"]["A"][u"分子"],
                         self.cl[u"偽警報"]["B"][u"分子"])
        self.assertIn(u"**B(LLM が特定し現行 Core が実証)は A(LLM 単独)を"
                      u"上回らない。**", self.t)
        self.assertIn(u"**等しいなら上回っていない。**", self.t)

    def test_2_the_four_rows_of_the_headline_table_match_the_record(self):
        for label, v in ((u"検出(注入 64 行)", self.inj[u"検出(誤りが在る)"]),
                         (u"**危険な誤通過**(注入を通した)",
                          self.inj[u"**危険な誤通過**"]),
                         (u"偽警報(無改変 128 行)", self.cl[u"偽警報"]),
                         (u"無改変で通した", self.cl[u"正しく通した"])):
            self.assertIn(u"| %s | %s | **%s** |"
                          % (label, pct(v["A"]), pct(v["B"])), self.t, label)

    def test_3_no_dangerous_pass_and_no_false_rejection(self):
        r1 = self.r[u"R-1 誤った参照先を検査通過にした"]
        self.assertEqual(r1[u"(a) 検査通過のうち注入の行"][u"分子"], 0)
        self.assertEqual(r1[u"(b) 注入の行のうち検査通過"][u"分子"], 0)
        self.assertEqual(
            self.r[u"R-2 正しい主張を不一致にした(無改変)"][u"率"][u"分子"], 0)
        self.assertEqual(self.inj[u"**危険な誤通過**"]["B"][u"分子"], 0)

    def test_4_the_only_change_is_refusing_to_vouch(self):
        a = self.cl[u"正しく通した"]["A"][u"分子"]
        b = self.cl[u"正しく通した"]["B"][u"分子"]
        self.assertGreater(a, b)
        self.assertIn(u"残り **%d 行を `実証不能` に落とした。**" % (a - b), self.t)
        self.assertIn(u"**保証しないものを保証しない、という変化である。**"
                      u"精度は上がっていない。", self.t)

    def test_5_unprovable_breakdown_is_printed(self):
        r3 = self.r[u"R-3 実証不能"]
        self.assertIn(u"| 実証不能 | **%s** |" % pct(r3[u"件数"]), self.t)
        for k, v in r3[u"内訳"].items():
            self.assertIn(u"| %s | %d |" % (k, v), self.t, k)
        self.assertEqual(sum(r3[u"内訳"].values()), r3[u"件数"][u"分子"])

    def test_6_separate_tallies_are_kept_separate(self):
        r6 = self.r[u"R-6 差分・率の行(別集計)"]
        r7 = self.r[u"R-7 contract が無い行(別集計)"]
        self.assertEqual(r6[u"件数"], 7)
        self.assertEqual(r7[u"件数"], 24)
        self.assertNotIn(u"検査通過", r6[u"B の判定"])
        self.assertNotIn(u"検査通過", r7[u"B の判定"])
        self.assertIn(u"**その場で contract を足していない。**", self.t)
        self.assertIn(u"**Core がそれを実証したのではない。**", self.t)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_7_six_hits_two_misses_and_the_misses_are_mine(self):
        p = self.r[u"**予測との照合**"]
        self.assertEqual((p[u"当たり"], p[u"外れ"]), (6, 2))
        missed = [x[u"記号"] for x in p[u"欄ごと"] if not x[u"当たり"]]
        self.assertEqual(sorted(missed), ["P-5", "P-8"])
        self.assertIn(u"**当たり 6 / 外れ 2。**", self.t)
        self.assertIn(u"**外れた 2 つは、どちらも私の予測の計算間違いである**", self.t)
        self.assertIn(u"**予測を直さない。**外れは外れとして残す。", self.t)

    def test_8_the_seal_predictions_are_untouched(self):
        out = subprocess.run(["git", "show", "b396d9b:./" + SEAL_REL],
                             cwd=ROOT, capture_output=True)
        self.assertEqual(out.returncode, 0)
        now = io.open(os.path.join(ROOT, SEAL_REL), "rb").read()
        self.assertEqual(hashlib.sha256(out.stdout).hexdigest(),
                         hashlib.sha256(now).hexdigest(),
                         u"**封が動いている**")


class CompositionTest(unittest.TestCase):
    """**合成規則を壊した入力で確かめる**(字の写しではなく振る舞いで)。"""

    def setUp(self):
        self.M = _mod()

    def test_9_the_llm_finding_is_never_overwritten(self):
        for st in ("GROUNDED", "VALUE_MISMATCH", None):
            self.assertEqual(
                self.M.compose(u"誤りが在る", st, None), u"誤りが在る", st)
            self.assertEqual(
                self.M.compose(u"誤りが在る", st, u"contract が無い"),
                u"誤りが在る", st)

    def test_10_grounded_alone_is_the_only_pass(self):
        self.assertEqual(self.M.compose(u"確認済み", "GROUNDED", None),
                         u"検査通過")
        self.assertEqual(self.M.compose(u"確認済み", "VALUE_MISMATCH", None),
                         u"不一致")
        self.assertEqual(self.M.compose(u"確認済み", "POINTER_NOT_FOUND", None),
                         u"実証不能")
        self.assertEqual(self.M.compose(u"確認済み", "GROUNDED",
                                        u"contract が無い"), u"実証不能")
        self.assertEqual(self.M.compose(u"判定できない", "GROUNDED", None),
                         u"実証不能")
        self.assertEqual(self.M.compose(u"欠け", "GROUNDED", None), u"実証不能")


class DisciplineTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec()

    def test_11_engine_untouched(self):
        for rel, want in ENGINE_SHA.items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            if got != want and rel in ENGINE_LATER:
                later, seal_rel = ENGINE_LATER[rel]
                added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal_rel],
                                       cwd=ROOT, capture_output=True, text=True).stdout.split()
                self.assertTrue(added, u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている**" % rel)
        self.assertIn(u"**engine は 1 行も変えていない。contract を足していない。"
                      u"0 USD・席は呼んでいない。**", self.t)

    def test_12_pass_is_not_called_correct(self):
        self.assertIn(u"**`検査通過` は「現行 Core の検査を通過した」という意味であり、"
                      u"「正しい」ではない。**", self.t)
        self.assertIn(u"**未検査属性: 単位・期間・次元(連結区分)・重複。**", self.t)
        for x in self.r["rows"]:
            self.assertEqual(len(x[u"**未検査属性**"]), 4, x[u"id"])

    def test_13_the_cause_is_classified_in_three(self):
        b = self.t[self.t.index(u"## §5"):self.t.index(u"## §6")]
        for k in (u"**contract 不足**", u"**未検査属性**", u"**意味的裏づけの不足**"):
            self.assertIn(k, b, k)
        self.assertIn(u"**だから「単位の穴が危険だ」も「安全だ」も、"
                      u"この材料では言えない。**", b)

    def test_14_limits_and_the_next_step_is_the_humans(self):
        b = self.t[self.t.index(u"## §6"):]
        self.assertIn(u"**B は A を上回っていない。**「同じ」である。", b)
        self.assertIn(u"**LLM の特定能力の差は測っていない。**", b)
        self.assertIn(u"**動く量は測るまで分からない。**", b)
        self.assertIn(u"それだけで Core に価値が無いとは言わない", b)


if __name__ == "__main__":
    unittest.main()
