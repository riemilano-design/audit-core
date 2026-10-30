# -*- coding: utf-8 -*-
"""P20 の結果(docs/XBRL_P20_RESULT_2026-10-17.md)の門。

**数は 2 つの記録を正本に突き合わせる。**
**予測の file が動いていないこと**と**engine が動いていないこと**を固定する。
"""
import hashlib
import io
import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
DOC = os.path.join(ROOT, "docs", "XBRL_P20_RESULT_2026-10-17.md")
RUN = os.path.join(FX, "p20_rerun_2026-10-17.json")
RECHECK = os.path.join(FX, "p20_pred_recheck_2026-10-17.json")
PRED_REL = "fixtures/xbrl/cd8/branch_a_predictions_2026-10-17.json"
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
SEAL_VOCAB = "docs/XBRL_VOCAB_SEAL_2026-10-21.md"    # 2026-10-21 追記: 語彙の登録と枠の取り直し P24 の段 1(下の ENGINE_LATER の recipes.py・vocabulary.py の遷移)
SEAL_LASTBRANCH = "docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md"    # 2026-10-21 追記: 最後の枝 P25 の段 1(下の ENGINE_LATER の遷移)
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"    # 2026-10-22 追記: P26 の段 1(下の ENGINE_LATER の遷移)
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
SEAL_P27 = "docs/XBRL_P27_SEAL_2026-10-27.md"    # 2026-10-27 追記: P27 の段 2(下の遷移)
SEAL_DEFAULT_P27 = "docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md"    # 2026-10-28 追記: 既定を P26 -> P27 に切り替える 段 2(下の遷移。vocabulary.py の DEFAULT_PROFILE の 1 行と注記 +5 行・-1 行、verify_document.py の docstring の 1 行 +1 行・-1 行だけ)
SEAL_CAND = "docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md"    # 2026-10-30 追記: 候補の欄を足す(下の遷移)
# 2026-10-21(最後の枝 P25 の段 1): 封 docs/XBRL_LASTBRANCH_SEAL_2026-10-21.md(engine を変える。人間の事前承認 2026-10-21)で recipes.py に最後の枝の証拠の判定の塊(+72 行・-0 行。既存の行は 1 つも書き換えない)、vocabulary.py に旗 last_branch_names_only_if_evidence・P25・PROFILES の登録(+7 行・-0 行)を足した(DEFAULT_PROFILE は P22 のまま)。
# recipes.py の 3461c3f8b7af6675・vocabulary.py の 83498c04a7b70396(P24 の段 1)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が P25 の段 1 の後の値のときだけ。
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
    # 85896a67913ce1e7(P27 の段 2) は残す(測った時点の値。vocabulary.py の sha16)、既定を P26 -> P27 に切り替える 段 2(封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md)で 514ebb8104451c07。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
    "adapters/xbrl/vocabulary.py": ("7fbcfbf0e472f366", SEAL_CAND),
    # 2026-10-28(既定を P26 -> P27 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P27_SEAL_2026-10-28.md §1-1 が宣言した遷移。verify_document.py の docstring の 1 行(+1 行・-1 行)。上の表の 67e7639de3f5f2ad は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
    # 2026-10-30(候補の欄を足す): 封 docs/XBRL_UNNAMED_CANDIDATE_SEAL_2026-10-29.md §2-3 が宣言した遷移(人間の承認 2026-10-30)。vocabulary.py に旗 1 つ・P27C・PROFILES の登録、verify_document.py に Claim の欄 candidate(CLAIM_FIELDS の末尾)、report_customer.py に candidate_ja(案 A)を足した。直前の値(vocabulary.py 514ebb8104451c07・verify_document.py c3791080ab5aef2f・report_customer.py 6679138d350ec382・束ねた指紋 92326a0f4dcefd21・frozen_bundle 030455282c89661b)は残す(測った時点の値)。受け入れるのは、その封が履歴に在り、値が候補の欄の後の値のときだけ。
    "adapters/xbrl/verify_document.py": ("6c76c8ade6c7b1c8", SEAL_CAND),
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


def rec(p):
    return json.load(io.open(p, encoding="utf-8"))


def pct(v):
    return u"%s%%(%s/%s)" % (v[u"率"], v[u"分子"], v[u"分母"])


class ResultTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = rec(RUN)

    def test_1_all_six_fields_hit_and_the_doc_says_so(self):
        ch = self.r[u"**予測との照合**"]
        self.assertEqual(len(ch[u"欄ごと"]), 6)
        self.assertEqual(ch[u"外れ"], 0)
        self.assertEqual(ch[u"当たり"], 6)
        self.assertIn(u"**当たり %d / 外れ %d。**" % (ch[u"当たり"], ch[u"外れ"]),
                      self.t)
        for c in ch[u"欄ごと"]:
            self.assertIn(c[u"欄"], self.t, c[u"欄"])

    def test_2_the_identification_numbers_are_from_the_record(self):
        m2 = self.r[u"M-2 特定"]
        self.assertIn(u"| Core 自身の特定(T5 全部の行) | %s | **%s** |"
                      % (pct(m2[u"全部の行"]["P16"]), pct(m2[u"全部の行"]["P20"])),
                      self.t)
        self.assertIn(u"| Core 自身の特定(1 対 1 の行だけ) | %s | **%s** |"
                      % (pct(m2[u"1 対 1 の行だけ"]["P16"]),
                         pct(m2[u"1 対 1 の行だけ"]["P20"])), self.t)
        self.assertEqual(m2[u"全部の行"]["P20"][u"分子"], 18)
        self.assertEqual(m2[u"1 対 1 の行だけ"]["P20"][u"分子"], 15)

    def test_3_the_cost_is_printed_next_to_the_gain(self):
        m3 = self.r[u"M-3 名指して正解でない行"]
        self.assertIn(u"| **うち正解でなかった行** | %d | **%d** |"
                      % (m3["P16"][u"分子"], m3["P20"][u"分子"]), self.t)
        self.assertEqual(m3["P20"][u"分子"] - m3["P16"][u"分子"], 7)
        self.assertIn(u"**特定は 3 行増え、誤認定は 7 行増えた。**", self.t)
        self.assertIn(u"**これを「改善」と書かない。**", self.t)

    def test_4_the_six_documents_did_not_move(self):
        six = self.r[u"M-4 6 書類の動き"]
        self.assertEqual(len(six), 6)
        self.assertTrue(all(v == 0 for v in six.values()), six)
        self.assertIn(u"| 連結ありの 6 書類で動いた主張 | ― | **0 件** |", self.t)

    def test_5_the_alpha_ceiling_did_not_move(self):
        self.assertEqual(self.r[u"M-5 α の天井"]["P16"], "0/7")
        self.assertEqual(self.r[u"M-5 α の天井"]["P20"], "0/7")
        self.assertIn(u"**α の天井は 0/7 のまま。**", self.t)
        self.assertIn(u"**製品価値の側は、この設定変更では動かない。**", self.t)

    def test_6_every_one_of_the_ten_rows_is_in_the_table(self):
        ten = self.r[u"M-1 10 行の state"][u"明細"]
        self.assertEqual(len(ten), 10)
        for x in ten:
            self.assertNotEqual(x["P20"][u"state"], "POINTER_NOT_FOUND", x[u"id"])
            self.assertIn(u"| `%s` | %s |" % (x[u"doc"], x[u"id"]),
                          self.t.split(u"### §2-2")[1], x[u"id"])
        self.assertEqual(self.r[u"M-1 10 行の state"][u"POINTER_NOT_FOUND の数"],
                         {"P16": 10, "P20": 0})


class ComparatorDefectTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.k = rec(RECHECK)

    def test_7_both_tallies_are_kept(self):
        a = self.k[u"照合 1(先の記録・そのまま残す)"][u"当たり"]
        b = self.k[u"**照合 2(字で書いた参照先で比べる)**"][u"当たり"]
        self.assertEqual((a, b), (9, 10))
        self.assertIn(u"| 照合 1(先の記録。そのまま残す) | **%d/10** |" % a, self.t)
        self.assertIn(u"| **照合 2(字で書いた参照先で比べる)** | **%d/10** |" % b,
                      self.t)
        self.assertIn(u"**両方を残す。**", self.t)
        self.assertIn(u"**実測の数(M-1〜M-6)は 1 つも変えていない。**", self.t)

    def test_8_the_one_differing_row_is_named(self):
        d = self.k[u"**2 つの数え方で違った行**"]
        self.assertEqual(len(d), 1)
        self.assertEqual((d[0][u"doc"], d[0][u"行"]), ("S100YZEV", "R011"))
        self.assertEqual(d[0][u"実測の参照先"], d[0][u"正解"])
        self.assertIn(u"`R011`", self.t)

    def test_9_the_first_record_was_not_rewritten(self):
        """**先の記録の主張ごとの数が 9/10 のまま**であること。"""
        run = rec(RUN)
        ch = run[u"**予測との照合**"]
        self.assertEqual(ch[u"主張ごとの当たり"], 9)
        self.assertEqual(ch[u"主張ごとの外れ"], 1)


class DisciplineTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)

    def test_10_prediction_file_is_unchanged_since_its_commit(self):
        out = subprocess.run(["git", "show", "cf4f5c9:./" + PRED_REL],
                             cwd=ROOT, capture_output=True)
        self.assertEqual(out.returncode, 0)
        now = io.open(os.path.join(ROOT, PRED_REL), "rb").read()
        self.assertEqual(hashlib.sha256(out.stdout).hexdigest(),
                         hashlib.sha256(now).hexdigest(),
                         u"**予測の file が動いている**")

    def test_11_engine_is_untouched(self):
        for rel, want in ENGINE_SHA.items():
            with io.open(os.path.join(ROOT, rel), "rb") as fh:
                got = hashlib.sha256(fh.read()).hexdigest()[:16]
            assert_pinned_or_declared(self, rel, got, want)
        self.assertIn(u"**profile を P16 → P20 にしただけ。"
                      u"engine のコードは 1 行も変えていない。0 USD・席は呼んでいない。**",
                      self.t)

    def test_12_it_does_not_claim_product_value(self):
        b = self.t[self.t.index(u"## §5"):]
        self.assertIn(u"**性能の証明ではない**", b)
        self.assertIn(u"**A 対 C′(LLM + Core が LLM 単体より正確か)"
                      u"はこの封では測っていない。**", b)
        self.assertIn(u"**「P20 にすべき」とは書かない。**", b)
        self.assertIn(u"**測っていない。**", b)

    def test_13_next_steps_are_the_humans(self):
        b = self.t[self.t.index(u"## §6"):]
        self.assertIn(u"独立監査の GO が要る", b)
        self.assertIn(u"**先に Core 側の特定を上げないと α は 0 のままである。**", b)


if __name__ == "__main__":
    unittest.main()
