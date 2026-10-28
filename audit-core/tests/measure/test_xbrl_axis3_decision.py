# -*- coding: utf-8 -*-
"""①(実費の記録)と ②(軸3 の定義)の門。

**数は記録 JSON を正本に突き合わせる。**
**「engine を触っていない」は git と sha で確かめる**(文を信じない)。
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
DOC = os.path.join(ROOT, "docs", "XBRL_AXIS3_DECISION_2026-10-17.md")
RECS = os.path.join(FX, "cost_records_2026-10-17.json")
SPLIT = os.path.join(FX, "cost_split_2026-10-17.json")
AX = os.path.join(FX, "axis3_decision_2026-10-17.json")
BASE = "2745dd5"          # 今日の便の起点
ENGINE_SHA = {"adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
              "adapters/xbrl/vocabulary.py": "bcf559308bda0cc6"}

# 2026-10-20 追記(上の ENGINE_SHA は、その記録を測った時点の sha で、消さない)。**宣言された遷移**: 封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md
# (名指しの直し P21。engine を変える)で変わった sha。その封が履歴に在り、値がその封の後の値のときだけ受け入れる
# (tests/measure/test_xbrl_cd_seal.py の FROZEN_LATER と同じ型: 「ずれ」と「宣言された遷移」を言い分ける)。
SEAL_NAMING_FIX = "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md"
SEAL_PERIOD_BIND = "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md"    # 2026-10-20 追記: 期を縛る P22 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_ROUNDING = "docs/XBRL_ROUNDING_SEAL_2026-10-21.md"    # 2026-10-21 追記: 丸めの帯 P23 の段 1(下の ENGINE_LATER の vocabulary.py・recipes.py の遷移)
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# vocabulary.py の 83498c04a7b70396(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
ENGINE_LATER = {
    # 2026-10-20(段 2): 既定を P20 -> P21 にした(vocabulary.py の DEFAULT_PROFILE と決定の注記。同じ封 docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md の段 2)。
    # vocabulary.py の sha は 段 1 5eb80a2 のとき 6c6db4c75e571a6c(残す。段 1 の結果の記録が測った時点の値)、段 2 で 1205b30b496090ef。
    # 受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-20(期を縛る P22 の段 1): 同じ封で vocabulary.py に旗 period_bind と P22 を足した(DEFAULT_PROFILE は P21 のまま)。
    # sha は 段 1 5eb80a2 で 6c6db4c75e571a6c・名指しの直し 段 2 で 1205b30b496090ef(どちらも残す。測った時点の値)、P22 の段 1 で 1fdb48e7e3ba58ce。
    # 2026-10-20(期を縛る P22 の段 2): 既定を P21 -> P22 にした(vocabulary.py の DEFAULT_PROFILE と決定の注記だけ。封 docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md の段 2・E-8。人間の承認 2026-10-20「任せる」)。
    # 段 1 3320c8c の 1fdb48e7e3ba58ce は残す(測った時点の値)、段 2 で 25a3c0992e10daaa。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-21(丸めの帯 P23 の段 1): 封 docs/XBRL_ROUNDING_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 truncate_abs_band・P23(= P22 + 率の旗 + truncate_abs_band)・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
    # 25a3c0992e10daaa(P22 の段 2)は残す(測った時点の値)、P23 の段 1 で f7b8d925eb6787ec。受け入れるのは、その封が履歴に在り、値が P23 の段 1 の後の値のときだけ。
    # 2026-10-21(語彙の登録と枠の取り直し P24 の段 1): 封 docs/XBRL_VOCAB_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 2 つ・資金の句の表・P24・PROFILES の登録を足した(DEFAULT_PROFILE は P22 のまま)。
    # f7b8d925eb6787ec(P23 の段 1)は残す(測った時点の値)、P24 の段 1 で 83498c04a7b70396。受け入れるのは、その封が履歴に在り、値が P24 の段 1 の後の値のときだけ。
    # 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で vocabulary.py に旗 5 つ・P26・PROFILES の登録(+17 行・-0 行) を足した。
    # 27e71e9861fc5aad(P25 の段 1)は残す(測った時点の値)、P26 の段 1 で 83025e9c0525d08b。受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。
    # 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
    # 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-27(P27 の段 2): 封 docs/XBRL_P27_SEAL_2026-10-27.md §2-3 が宣言した遷移。engine の 5 file(vocabulary・recipes・extract・registry_setup・report_customer)に挿入だけを足した(既存の行の書き換え 0)。直前の値は残す(測った時点の値)、P27 の段 2 で下の値。受け入れるのは、その封が履歴に在り、値が P27 の段 2 の後の値のときだけ。
    # 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    "adapters/xbrl/vocabulary.py": ("514ebb8104451c07", SEAL_DEFAULT_P27),
    # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1 が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行)。上の表の 67e7639de3f5f2ad は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    "adapters/xbrl/verify_document.py": ("c3791080ab5aef2f", SEAL_DEFAULT_P27),
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

# 2026-10-19 追記(10-14 の封の字・値は消さない)。宣言された遷移: BASE 以後に adapters/・core/ を触った commit のうち、
# 下に名前と封を書いたものだけを受け入れる。封が git 履歴に在ることも要る(fixtures/frozen_bundle_sha.py の世代と同じ型)。
LATER_ENGINE_COMMITS = {
    "295e636": "docs/XBRL_HOLDS_PRODUCT_PATH_SEAL_2026-10-19.md",   # (d)・P・U を製品の経路へ + 軸の保持 (e)
    "ac8c3ff": "docs/XBRL_PERIOD_PAIR_SEAL_2026-10-19.md",          # 期間の対 PP 段 2 ― engine
    "5eb80a2": "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md",           # 名指しの直し P21 段 1 ― engine(既定は P20 のまま)
    "a516288": "docs/XBRL_NAMING_FIX_SEAL_2026-10-20.md",           # 名指しの直し P21 段 2 ― 既定 P20 -> P21
    "3320c8c": "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md",          # 期間を縛る P22 段 1 ― engine(旗だけ、既定は P21 のまま。宣言 2026-10-20)
    "d0b544c": "docs/XBRL_PERIOD_BIND_SEAL_2026-10-20.md",          # 期間を縛る P22 段 2 ― 既定 P21 -> P22(宣言 2026-10-21)
    "7d530cc": "docs/XBRL_ROUNDING_SEAL_2026-10-21.md",             # 丸めの帯 P23 段 1 ― engine(旗だけ、既定は P22 のまま。宣言 2026-10-21)
    "c7ad668": "docs/XBRL_VOCAB_SEAL_2026-10-21.md",                # 語彙の登録と枠の取り直し P24 段 1 ― engine(旗だけ、既定は P22 のまま。宣言 2026-10-21)
    "9577eab": "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md",           # 最後の枝の名指し P25 段 1 ― engine(旗だけ、既定は P22 のまま。宣言 2026-10-21)
    "c13a746": "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md",      # 日本語の報告形 ― 新しい module report_customer.py(判定は不変。宣言 2026-10-21)
    "129ee9d": "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md",  # 報告形の直し ― report_customer.py だけ(判定と節の割り当ては不変。宣言 2026-10-22)
    "b778dd9": "docs/XBRL_P26_SEAL_2026-10-21.md",                 # P26 段 1 ― engine(旗だけ、既定は P22 のまま。宣言 2026-10-22)
    "917157c": "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md",         # P26 段 2 ― 既定 P22 -> P26(vocabulary.py +4/−1。宣言 2026-10-27)
    "b2c3f56": "docs/XBRL_P27_SEAL_2026-10-27.md",                 # P27 段 2 E ― engine(P27・P27E の旗、既定は P26 のまま。宣言 2026-10-27)
}


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(p):
    return json.load(io.open(p, encoding="utf-8"))


class CostRecordsTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec(RECS)

    def test_1_counts_match_the_record(self):
        c = self.r["内訳"]
        self.assertIn("| 数えた json | **%d** |" % self.r["数えた file"], self.t)
        for key, label in (("トークンの記録が在る file", "トークンの記録が在る file"),
                           ("入出力の内訳が在る file", "**入出力の内訳が在る file**"),
                           ("合計だけの file", "合計トークンだけの file"),
                           ("実請求額が在る file", "**実請求額が在る file**")):
            self.assertIn("| %s | **%d** |" % (label, c[key]), self.t,
                          "%s の数が違う" % key)

    def test_2_the_breakdown_is_one_file_only(self):
        self.assertEqual(self.r["内訳"]["入出力の内訳が在る file"], 1)
        self.assertEqual(self.r["内訳"]["実請求額が在る file"], 0)
        self.assertIn("**席の記録(sonnet / haiku の 6 本)は全部「合計トークン」"
                      "だけである。**", self.t)


class CostSplitTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec(SPLIT)

    def test_3_the_rate_pair_is_unique_and_quoted(self):
        s = self.r["2 実費を再現する単価の組"]
        self.assertTrue(s["**解は 1 つか**"], "単価の組が 1 つに決まっていない")
        h = s["候補"][0]
        self.assertIn("**入力 %d USD/1M・出力 %d USD/1M(出力は入力の %d 倍)**"
                      % (h["入力 USD/1M"], h["出力 USD/1M"], h["出力は入力の何倍"]),
                      self.t)

    def test_4_chars_per_input_token_is_measured(self):
        v = self.r["1 1 字あたりの入力トークン(実測)"]
        self.assertIn("**1 字あたりの入力トークン = %s**" % v, self.t)
        m = self.r["**使った記録**"]
        self.assertIn("| prompt | **{:,} 字** |".format(m["prompt_chars"]), self.t)
        self.assertIn("| **入力トークン** | **{:,}** |".format(m["input_tokens"]),
                      self.t)
        self.assertIn("| **実費** | **%s USD** |" % m["cost_usd"], self.t)

    def test_5_three_scenarios_with_their_totals(self):
        for s in self.r["3 8 便 1 席の見積もり(**sonnet の単価は確かめていない**)"]:
            self.assertIn("| **%.2f USD** |" % s["8 便 USD"], self.t,
                          "場合の合計が本文に無い: %s" % s["場合"])
        self.assertIn("推定を実測として扱わない。", self.t)
        self.assertIn("**実請求額**(課金の画面)。記録に 0 件。", self.t)


class Axis3Test(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec(AX)

    def test_6_the_definition_separates_two_axes(self):
        self.assertIn("**「止めた」ことを軸B の正解に数えない。**", self.t)
        self.assertIn("**軸A と軸B を掛け合わせた表も必ず出す**", self.t)
        self.assertIn("**対応が付かない行は軸A の分母から外し、件数を別に書く。**",
                      self.t)
        self.assertIn("軸A(停止判定)と軸B(参照先の正しさ)を別に採る",
                      self.r["決めた読み方"])

    def test_7_the_two_axis_table_matches_the_record(self):
        for arm, label in (("Core-P", "**Core**"), ("D′", "**D′**"), ("D″", "**D″**")):
            v = self.r["腕"][arm]
            a = v["軸A 停止判定"]
            b = v["軸B 参照先(T5。状態に関わらず読む)"]
            plain = self.t.replace("**", "")
            self.assertIn("%s(%d/%d)" % (fmt(a["率"]), a["止めた"],
                                         a["分母(対応が付いた件)"]), plain,
                          "%s の軸A が本文と違う" % arm)
            self.assertIn("| %s | %s | %s | %s |"
                          % (fmt(b["**名指した率**"]),
                             fmt(b["**名指したうち正しい率**"]),
                             fmt(b["**T5 全体での特定率**"]),
                             ("%d 件" % b["うち値の持ち主を採った"])), plain,
                          "%s の軸B の行が本文と違う" % arm)

    def test_8_the_cross_table_shows_stopped_but_wrong(self):
        c = self.r["腕"]["Core-P"]["軸A × 軸B(T5)"]
        self.assertEqual(c.get("通した × 正解と違う", 0), 0, "Core は 1 件も通していない")
        self.assertIn("| **Core** | **%d** | **%d** | %d | **0** | %d |"
                      % (c["止めた × 正解と一致"], c["止めた × 正解と違う"],
                         c["止めた × 名指さない"], c["対応が付かない × 名指さない"]),
                      self.t)
        d = self.r["腕"]["D′"]["軸A × 軸B(T5)"]
        self.assertIn("| **D′** | 0 | 0 | %d | **%d** | 0 |"
                      % (d["止めた × 名指さない"], d["通した × 正解と違う"]), self.t)
        self.assertIn("**誤った参照先も隠れない**", self.t)

    def test_9_the_engine_was_not_touched(self):
        """**文を信じない。**git と sha で確かめる(2026-10-19: 宣言された遷移だけ例外)。"""
        out = subprocess.run(["git", "log", "--format=%h",
                              "%s..HEAD" % BASE, "--", "adapters", "core"],
                             cwd=ROOT, capture_output=True, text=True)
        commits = [c for c in out.stdout.split() if c]
        undeclared = [c for c in commits if c not in LATER_ENGINE_COMMITS]
        self.assertEqual(undeclared, [],
                         "**adapters/ か core/ を触っている(宣言されていない commit: %s)**" % undeclared)
        for c in commits:
            seal = LATER_ENGINE_COMMITS[c]
            added = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", seal],
                                   cwd=ROOT, capture_output=True, text=True).stdout.split()
            self.assertTrue(added, "**commit %s の宣言された遷移の封 %s が履歴に無い**" % (c, seal))
        for rel, want in ENGINE_SHA.items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            assert_pinned_or_declared(self, rel, got, want)
        self.assertIn("**これは指標の作り直しであって、判定ロジックの修正ではない**",
                      self.t)
        self.assertIn("**Core の隣接要素の誤り(12 件)は、指標を変えても消えない。**",
                      self.t)

    def test_10_what_is_not_done_is_listed(self):
        b = self.t[self.t.index("# ③ まだやらないこと"):]
        nums = re.findall(r"(?m)^(\d)\. ", b[:b.index("## §4")])
        self.assertEqual(nums, ["1", "2", "3", "4"], "やらないことは 4 本")
        self.assertIn("**本番の封(`XBRL_CD_SEAL_2026-10-17.md`)はまだ 1 文字も"
                      "直していない。**", b)
        self.assertIn("**Core 単体で差が出たことは、組み合わせの優位性ではない。**", b)
        li = b[b.index("## §4"):]
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", li),
                         [str(i) for i in range(1, 7)], "限界は 6 本")

    def test_11_the_unused_eight_are_still_untouched(self):
        """**この文はこの便の時点の事実である。**封 v2 の段 2 で取得が済んだ後は、
        「まだ取得していない」を現在の事実として要求しない(それは記録の改竄になる)。
        代わりに **取得したのは引いた 8 件そのものである**ことを要求する
        (穴を開けない。§5 の追記で経緯を残す)。
        """
        cache = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet")
        drawn = rec(os.path.join(FX, "draw_2026-10-17.json"))["引いた 8 件"]
        self.assertIn("**まだ 1 件も取得していない。**", self.t)
        fetched = os.path.join(FX, "fetched_2026-10-17.json")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch",
             "fixtures/xbrl/cd8/fetched_2026-10-17.json"],
            cwd=ROOT, capture_output=True).returncode == 0
        if tracked:
            got = [d["docID"] for d in rec(fetched)["取得した書類"]]
            self.assertEqual(sorted(got), sorted(drawn),
                             "**取得したものが引いた 8 件と違う**")
            self.assertIn("この節は封 v2 の段 2 で更新された", self.t,
                          "**取得したのに追記が無い**")
            return
        if os.path.isdir(cache):
            names = "\n".join(os.listdir(cache))
            for d in drawn:
                self.assertNotIn(d, names, "**%s が取得されている**" % d)


def fmt(x):
    return "判定不能" if x is None else "%.1f%%" % x


if __name__ == "__main__":
    unittest.main()
