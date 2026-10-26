# -*- coding: utf-8 -*-
u"""顧客向けの報告形(新しい module `adapters/xbrl/report_customer.py`)の封の門
docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md を固定する。型は P25 の封の門 tests/measure/test_xbrl_lastbranch_seal.py に倣う。
人間の承認の引用と「既存の report.py は 1 字も触らない」宣言(2026-10-13 の人間の決定)・予測 C-1〜C-5 と C-2b と外れ方と幅の算術・
§0 の数の和と記録との突き合わせ・§1 の節の順と理由の日本語 2 行・理由の表の key の数(engine の実物と突き合わせる)・
§3 の限界・§4 の file 一覧と順序・**封が実装より先であること(新しい file がまだ無い)**・
**封の commit 時点の `report.py`・`verify_document.py` の sha16 と engine の束ねた指紋・frozen_bundle の本数**を縛る。

**この門の engine の留め(test_11・test_12)は、実装の便の commit で「宣言された遷移」に更新する前提である。**
`adapters/xbrl/` に module(`report_customer.py`)を足すと、`verify_document.engine_fingerprint()` の `adapter_xbrl_py_sha256`(15 file → 16 file)が
その場で動き、`git add` された時点で `fixtures/frozen_bundle_sha.py` の対象(`git ls-files audit-core/core audit-core/adapters`)が 36 → 37 本になる
(FROZEN_COUNT = 36 の定数と `bundle()` の本数が合わず rc=2)。この門は両方を字で留めるので、実装の便で赤くなる ― それが狙い。そのとき
`FINGERPRINT_LATER` に (後の値, この封の path) を足して宣言する(P25 の封の門の ENGINE_LATER と同じ型)。
`report.py`・`verify_document.py`・`vocabulary.py`・`recipes.py`・`registry_setup.py` の sha16 はこの封が「触らない」と書いたもの(§1 で
profile は入力の JSON のまま、§4 で adapters/xbrl に足すのは report_customer.py だけ)で、宣言の遷移を持たない。動いたら赤のまま。

**封の字と engine の実物の食い違い(この門が見つけて、封は直さずに報告した 1 点。2026-10-21 実装席)**:
封 §2 C-3 の下書きは「`UNBOUND_REASON_STATE` の全 key(**16** = P22 時点の 14 + `other_frame` + `no_same_value`)」と書いていたが(commit 前に司令塔が「登録簿の理由の全部」に直した)、
`recipes.UNBOUND_REASON_STATE` の key は**今 14**で、`other_frame` と `no_same_value` はその辞書に無い。この 2 つは
`recipes._state_of` の別の枝(`other_frame(` の接頭辞・`NO_SAME_VALUE`)と `registry_setup._POINTER_NOT_FOUND_REASONS`(9)・
`_UNVERIFIABLE_REASONS`(7)に在る。**16 は登録簿の理由の数**(9 + 7)で、`UNBOUND_REASON_STATE` の key の数ではない。
封 §0 の「理由の表 14 key = `UNBOUND_REASON_STATE` 14 key」と §1 の「`UNBOUND_REASON_STATE` の全 key を網羅 + 2 行」は実物と合う。
この門は封の字 **16** を字のまま留め(test_2)、実物は「UNBOUND_REASON_STATE 14 + 2 = 登録簿 16」の関係として縛る(test_8)。
実装席が 2 通りに読める点: 網羅の門の対象が「UNBOUND_REASON_STATE の 14 key + 2 行」か「登録簿の 16 理由」か ― 集合としては同じ 16 になる(test_8)。

**§0 の下調べの数(出典に fact が無い (a) の 145 + 6、判断しない (c) の 1,001 + 42 + 38、一致の内訳 1,736 / 180 / 2,326、客 A の 39 claim・5 件)は、
記録(fixtures/)にまだ無い**(司令塔の席の手元の試作、scratchpad、正本でない)。この門は字と内訳の和・既存の記録から引ける数との関係だけを縛り、
記録に無い数を「測った」とは言わない。実物で数え直すのは結果の門(C-1・C-2 の測定)の仕事。
P22 の VALUE_MISMATCH 1,410 と GROUNDED 4,242 は記録 `fixtures/xbrl/rounding_2026-10-21.json`(R2 の集計「VALUE_MISMATCH の合計 P22」「GROUNDED の合計 P22」)と、
P25 の 626・4,382・UNVERIFIABLE 1,397・POINTER_NOT_FOUND 1,394 は記録 `fixtures/xbrl/lastbranch_2026-10-21.json`(L1 の集計)と同じ。
P22 の UNVERIFIABLE + POINTER_NOT_FOUND は記録に欄が無く、7,799 − 4,242 − 1,410 = 2,147 の引き算で出す(封 §0 の 915 + 151 + 1,081 = 2,147 と同じ)。"""
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))

SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md"
SEAL = os.path.join(ROOT, SEAL_REL)
ROUNDING_JSON = os.path.join(ROOT, "fixtures", "xbrl", "rounding_2026-10-21.json")
LASTBRANCH_JSON = os.path.join(ROOT, "fixtures", "xbrl", "lastbranch_2026-10-21.json")

# §4 の file 一覧(この順で書かれている)。新規の 6 本は封の commit 時点で作業木にも履歴にも無い。
NEW_MODULE = "adapters/xbrl/report_customer.py"
FILES = (NEW_MODULE,
         "tests/adapters/xbrl/test_report_customer.py",
         "measure/xbrl_customer_report_2026-10-21.py",
         "fixtures/xbrl/customer_report_2026-10-21.json",
         "docs/XBRL_CUSTOMER_REPORT_RESULT_2026-10-21.md",
         "tests/measure/test_xbrl_customer_report_result.py")
P25_UNIT_TEST = "tests/adapters/xbrl/test_recipes_p25.py"   # 既存。1 本足す(engine は変えない)

# 触らない file の sha256 の先頭 16 桁(封の commit 時点 = P25 段 1 の commit 9577eab・宣言 0db03a4 の後の木)。宣言の遷移を持たない。
UNTOUCHED = {"adapters/xbrl/report.py": "0d2854e659a5d8e0",              # 人間の決定 2026-10-13「判定に手を加えない・golden」
             "adapters/xbrl/verify_document.py": "67e7639de3f5f2ad",
             "adapters/xbrl/vocabulary.py": "27e71e9861fc5aad",           # P25 段 1 の後の値
             "adapters/xbrl/recipes.py": "bff243f13429b553",
             "adapters/xbrl/registry_setup.py": "f42ffe23aaa7673b"}

# 2026-10-22(P26 の段 1): 封 docs/XBRL_P26_SEAL_2026-10-21.md が engine の vocabulary.py(+17)・recipes.py(+251/-1)・registry_setup.py(+6)を書き換えた
# (extract.py・report_customer.py も。この封の UNTOUCHED の外)。上の UNTOUCHED は「この封は触らない」の値(封の commit 時点)で消さない。
# 受け入れるのは、その封が履歴に在り、値が P26 の段 1 の後の値のときだけ。report.py・verify_document.py は遷移を持たない(動いたら赤のまま)。
SEAL_P26 = "docs/XBRL_P26_SEAL_2026-10-21.md"
SEAL_DEFAULT_P26 = "docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md"    # 2026-10-23 追記: 既定を P22 -> P26 に切り替える 段 2(下の遷移)
# 2026-10-23(既定を P22 -> P26 に切り替える 段 2): 封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md(engine の差分は vocabulary.py の DEFAULT_PROFILE の 1 行と決定の注記 +4 行・-1 行だけ。人間の事前承認 2026-10-21)。
# 83025e9c0525d08b(P26 の段 1)は残す(測った時点の値)、段 2 で e28733067b1f17f5。受け入れるのは、その封が履歴に在り、値が段 2 の後の値のときだけ。
UNTOUCHED_LATER = {"adapters/xbrl/vocabulary.py": ("e28733067b1f17f5", SEAL_DEFAULT_P26), "adapters/xbrl/recipes.py": ("181b370420ab751b", SEAL_P26),
                   "adapters/xbrl/registry_setup.py": ("7f2cbded9c830211", SEAL_P26)}
P26_REASONS = ("other_concept", "direction_on_cause_item", "rounded_diff_within_double_band")

# 封の commit 時点の engine の束ねた指紋(verify_document.engine_fingerprint())と frozen_bundle。**宣言された遷移の前の値**で、消さない。
FINGERPRINT_AT_SEAL = {"adapter_xbrl_py_sha256": "8137596dc4eb7aa7d5446c85b46bcbf2cc6c2d458a0b439bd190ee291ac424c4",
                       "adapter_xbrl_py_files": 15,
                       "core_py_sha256": "34e836bb39762d5af831a9aa11d4ea095e73221beb5bd4510d3b234363a2a6e8",
                       "core_py_files": 4}
FROZEN_BUNDLE_AT_SEAL = "8ffdc9177cdc4be7c059e5bd0a6f6e5b8466215918077591eb64371b7c69304a"   # frozen_bundle_sha.FROZEN_BUNDLE_GENERATIONS の最新(P25 段 1)
FROZEN_COUNT_AT_SEAL = 36
# 宣言された遷移(実装の便の commit で足す): {欄: (後の値, 遷移を宣言した封の path)}。封の commit 時点では空。
# 実装で adapter_xbrl_py_sha256 / adapter_xbrl_py_files(15 → 16)が動く。frozen_bundle は FROZEN_COUNT 36 → 37 と新しい世代。
FIX_SEAL_REL = "docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md"
# 段 1(c13a746)の後の値。**測った当時の値として残す**(段 2 で module の中身が動いたので、いまの木はこの値ではない)。
FINGERPRINT_STAGE1 = {"adapter_xbrl_py_sha256": "c556de1cb26e975a172d54a4e39f4971bb5c11a5fd8a02a8404b9a719eb27acb", "adapter_xbrl_py_files": 16}
FINGERPRINT_LATER = {
    # 2026-10-21 実装の便(module report_customer.py を足した。封が宣言した遷移): adapters/xbrl の .py が 15 → 16 file、束ねた指紋が動く。
    # module が動けばここも動く(測り直す)。測った当時の値(FINGERPRINT_AT_SEAL)は残す。
    # 2026-10-21 追記(顧客向けの報告形の直し。封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md が宣言した遷移): module の中身が動き、束ねた指紋が
    # c556de1c…(段 1)から 11840a09… に動いた。file の数 16 は動かない。受け入れるのは、その封が履歴に在り、値が下の値のときだけ。
    # 2026-10-22 追記(P26 の段 1。封 docs/XBRL_P26_SEAL_2026-10-21.md が宣言した遷移): engine の 4 file と module が動き、束ねた指紋が 11840a09…(報告形の直し)から 498993e2… に動いた。
    # 2026-10-23 追記(既定を P22 -> P26 に切り替える 段 2。封 docs/XBRL_DEFAULT_P26_SEAL_2026-10-23.md が宣言した遷移): vocabulary.py の 1 行と注記が動き、束ねた指紋が 498993e2…(P26 の段 1。残す)から 5aba7749… に動いた。
    "adapter_xbrl_py_sha256": ("5aba7749259683563c37e62353717f64b4e4828931998a7c42518aca107f3504", SEAL_DEFAULT_P26),
    "adapter_xbrl_py_files": (16, SEAL_REL),
}
# 実装の便の後の frozen_bundle(FROZEN_COUNT 36 → 37・新しい世代。report_customer.py を git add した状態で測る)。封の commit 時点の値(FROZEN_BUNDLE_AT_SEAL)は残す。
FROZEN_BUNDLE_STAGE1 = "66f906c89205f0ef361e13fe051dbdeaed75a032e0d60ca832f6d605166f3b36"   # 段 1(c13a746)の世代。消さない
# 2026-10-21 追記(顧客向けの報告形の直し): 同じ 37 本のまま module の中身が動き、世代がもう 1 つ増えた。最新の世代はこの値。
FROZEN_BUNDLE_AFTER = "5c4da2e2ff3f30b7dcb6ebcbc84a5c68b074e8dc495f2d260551d7e10a4ce66c"
# 2026-10-22 追記(P26 の段 1): 同じ 37 本のまま engine の 4 file と module が動き、世代がもう 1 つ増えた。最新の世代はこの値。
FROZEN_BUNDLE_P26 = "a97ecf7c44e60c45bf6e6c23439c59955aad8bddf26b1174ee1e0ebabfd59c7c"
# 2026-10-23 追記(既定を P22 -> P26 に切り替える 段 2): 同じ 37 本のまま vocabulary.py が動き、世代がもう 1 つ増えた。最新の世代はこの値。
FROZEN_BUNDLE_DEFAULT_P26 = "26b5270646f2d8d8fcb7ca829f5f36066f9e2e9a1c3d1f0e4cdde1822e5d6fb6"
FROZEN_COUNT_AFTER = 37


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def jload(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def num(s):
    return int(s.replace(",", ""))


def sha16(rel):
    with io.open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True)


def rows(block, tag):
    """予測の表の行を ``{id: 行}`` で返す(C-2b のような英字つきの id も取る)。順序は書かれた順。"""
    out = []
    for m in re.finditer(r"(?m)^\| \*\*%s-(\w+)\*\* \|.*$" % tag, block):
        out.append((m.group(1), m.group(0)))
    return out


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def rng(line, label):
    """``label**lo〜hi**`` の幅を取る(label は幅の直前の字)。"""
    m = re.search(re.escape(label) + r"\*\*([\d,]+)〜([\d,]+)\*\*", line)
    assert m, (label, line)
    return num(m.group(1)), num(m.group(2))


def one(pattern, b, label):
    m = re.search(pattern, b)
    assert m, u"§0 の書き方が変わった: " + label
    return m


def s0_numbers(b):
    """§0 の数を、書かれた字のまま取り出す(書き方が変わったら落ちる)。"""
    m_not = one(r"GROUNDED でない ([\d,]+) のうち、出典に fact が無い \(a\) = `no_element\(unit not in XBRL\)` (\d+)・`no_prior_member_context` (\d+)、"
                r"判断しないが正しい \(c\) = `no_subject` ([\d,]+)・`target_or_plan` (\d+)・`ambiguous\(member\)` (\d+)。"
                r"合わせて ([\d,]+) / ([\d,]+) = ([\d.]+)%", b, "GROUNDED でない 3,557 の内訳")
    m_a = one(r"answer_key の 5 件は 5 / 5 が先頭の節「違う」に在り", b, "5 / 5")
    m_a39 = one(r"客 A の P22 の出力\((\d+) claim\)", b, "客 A の 39 claim")
    m_sec = one(r"67 書類\(既定 P22、([\d,]+) claim\): 違う ([\d,]+) / 要確認 (\d+) / 対象外 (\d+) / 判断しない ([\d,]+) / 一致 ([\d,]+)"
                r"\(当期 ([\d,]+)・前期 (\d+)・計算 ([\d,]+)\)", b, "67 書類の節の件数")
    m_key = one(r"理由の表 (\d+) key = `UNBOUND_REASON_STATE` (\d+) key", b, "理由の表 14 key")
    m_fp = one(r"engine の指紋\(adapter_xbrl_py_sha256、(\d+) file → (\d+) file\)が動き、frozen_bundle の本数 (\d+) → (\d+)", b, "指紋と本数")
    m_gold = one(r"`report.py` の golden (\d+) 本は緑のまま", b, "golden 13 本")
    return {"not_g": num(m_not.group(1)), "a_unit": int(m_not.group(2)), "a_prior": int(m_not.group(3)),
            "c_subject": num(m_not.group(4)), "c_plan": int(m_not.group(5)), "c_member": int(m_not.group(6)),
            "ac_sum": num(m_not.group(7)), "ac_den": num(m_not.group(8)), "ac_pct": m_not.group(9),
            "case_a_claims": int(m_a39.group(1)),
            "claims": num(m_sec.group(1)), "wrong": num(m_sec.group(2)), "check": int(m_sec.group(3)), "out_of": int(m_sec.group(4)),
            "no_judge": num(m_sec.group(5)), "match": num(m_sec.group(6)), "m_cur": num(m_sec.group(7)),
            "m_prior": int(m_sec.group(8)), "m_calc": num(m_sec.group(9)),
            "table_keys": int(m_key.group(1)), "unbound_keys": int(m_key.group(2)),
            "fp_files_from": int(m_fp.group(1)), "fp_files_to": int(m_fp.group(2)),
            "fz_from": int(m_fp.group(3)), "fz_to": int(m_fp.group(4)),
            "golden": int(m_gold.group(1))}


def p22_record():
    r = jload(ROUNDING_JSON)["R2"]["集計"]
    return r["GROUNDED の合計 P22"], r["VALUE_MISMATCH の合計 P22"]


def p25_record():
    return jload(LASTBRANCH_JSON)["L1"]["集計"]


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)

    def test_1_human_approval_is_quoted_and_report_py_is_declared_untouched(self):
        head = self.t[:self.t.index("\n## §0 ")]
        self.assertTrue(head.startswith(u"# 封: 顧客向けの報告形(新しい module。既存の報告は触らない)― 2026-10-21"))
        self.assertIn(u"**engine 側(`adapters/xbrl/` に module を足す)の変更。人間の承認(2026-10-21 深夜)「先に承認しておくので好きに進めて これをもって承認とする」。", head)
        self.assertIn(u"既存の `adapters/xbrl/report.py` は人間の決定(2026-10-13「判定に手を加えない・golden」)のまま 1 字も触らない。", head)
        self.assertIn(u"判定(state・reason・pointer)は足さず変えず、並べ方と字だけを変える。**", head)

    def test_2_six_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §2", "## §3")
        rs = rows(b, "C")
        self.assertEqual([i for i, _ in rs], ["1", "2", "2b", "3", "4", "5"])
        by = dict(rs)
        for i, line in rs:
            cs = cells(line)
            self.assertEqual(len(cs), 3, line)
            self.assertTrue(cs[1], u"予測が空: " + line)
            self.assertTrue(cs[2], u"外れ方が空: " + line)
        # 行ごとに、予測の幅と外れ方の両方を字で縛る(幅を直すと赤くなる)
        for i, ss in (("1", (u"客 A の P22 の出力(誤り入り 39 claim)を新しい報告にすると、答え合わせの 5 件が先頭の節「違う」に **5 / 5** 在り",
                             u"出典の値は文と同じ単位(百万円の文は百万円、千円の文は千円。語の主張は円)", u"5 件が先頭に無い / 単位が文と違う")),
                      ("2", (u"67 書類の無改変(既定 P22)で", u"「違う」**1,410**", u"「要確認」**880〜950**", u"「対象外 + 判断しない」**1,200〜1,260**",
                             u"「一致」4,242", u"足して 7,799", u"幅の外 / 和が合わない")),
                      ("2b", (u"同じ 67 書類を P25 明示で", u"「違う」**626**", u"「一致」**4,382**",
                              u"(P25 段 1 の記録 fixtures/xbrl/lastbranch_2026-10-21.json の VALUE_MISMATCH・GROUNDED)",
                              u"「対象外 + 判断しない」**1,190〜1,250**", u"「要確認」**1,540〜1,600**", u"足して 7,799", u"幅の外 / 和が合わない")),
                      ("3", (u"理由の日本語表は登録簿の理由の全部(**16** = `UNBOUND_REASON_STATE` の 14 key + `other_frame` + `no_same_value`)を網羅し",
                             u"網羅の門が理由を 1 つ消すと赤", u"赤にならない / key の数が違う")),
                      ("4", (u"同じ JSON から 2 回で同じバイト列", u"`report.py` の golden は不変", u"違う / golden が動く")),
                      ("5", (u"既存の `report.py`・`verify_document.py` は 0 行", u"engine の指紋は module を足した分だけ動く(宣言された遷移)",
                             u"1 行でも / 宣言なしに赤が残る"))):
            for s in ss:
                self.assertIn(s, by[i], u"C-%s: %s" % (i, s))

    def test_3_prediction_ranges_are_consistent_with_the_section_0_numbers_and_the_sums(self):
        """幅どうし・幅と §0 の件数・和 7,799 の整合。片方だけ直すと赤くなる。
        C-2(P22): 違う + 要確認 + (対象外 + 判断しない) + 一致 = 7,799 になりうる。幅の端の和が 7,799 を挟み、§0 の件数は幅の中。
        C-2b(P25): 同じ。要確認の幅 1,540〜1,600 は、P25 の PNF + UNV(記録)から (a)(c) 1,232 を引いた 1,559 を含む。"""
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        b = sec(self.t, "## §2", "## §3")
        by = dict(rows(b, "C"))
        total = n["claims"]
        self.assertEqual(total, 7799)
        # C-2
        l2 = by["2"]
        wrong = num(re.search(r"「違う」\*\*([\d,]+)\*\*", l2).group(1))
        match = num(re.search(r"「一致」([\d,]+)", l2).group(1))
        chk_lo, chk_hi = rng(l2, u"「要確認」")
        oj_lo, oj_hi = rng(l2, u"「対象外 + 判断しない」")
        self.assertEqual((wrong, match), (n["wrong"], n["match"]))
        self.assertLessEqual(chk_lo, chk_hi)
        self.assertLessEqual(oj_lo, oj_hi)
        self.assertTrue(chk_lo <= n["check"] <= chk_hi, (chk_lo, n["check"], chk_hi))
        self.assertTrue(oj_lo <= n["out_of"] + n["no_judge"] <= oj_hi, (oj_lo, n["out_of"] + n["no_judge"], oj_hi))
        self.assertTrue(wrong + match + chk_lo + oj_lo <= total <= wrong + match + chk_hi + oj_hi,
                        (wrong + match + chk_lo + oj_lo, total, wrong + match + chk_hi + oj_hi))
        self.assertEqual(num(re.search(r"足して ([\d,]+)", l2).group(1)), total)
        # C-2b
        l2b = by["2b"]
        wrong_b = num(re.search(r"「違う」\*\*([\d,]+)\*\*", l2b).group(1))
        match_b = num(re.search(r"「一致」\*\*([\d,]+)\*\*", l2b).group(1))
        chk_lo_b, chk_hi_b = rng(l2b, u"「要確認」")
        oj_lo_b, oj_hi_b = rng(l2b, u"「対象外 + 判断しない」")
        self.assertLessEqual(chk_lo_b, chk_hi_b)
        self.assertLessEqual(oj_lo_b, oj_hi_b)
        self.assertTrue(wrong_b + match_b + chk_lo_b + oj_lo_b <= total <= wrong_b + match_b + chk_hi_b + oj_hi_b,
                        (wrong_b + match_b + chk_lo_b + oj_lo_b, total, wrong_b + match_b + chk_hi_b + oj_hi_b))
        self.assertEqual(num(re.search(r"足して ([\d,]+)", l2b).group(1)), total)
        # 「対象外 + 判断しない」の理由(a)(c)は P25 で動かない(VALUE_MISMATCH → POINTER_NOT_FOUND no_same_value だけが動く)ので、C-2 と C-2b は同じ 1,232 を含む
        ac = n["a_unit"] + n["a_prior"] + n["c_subject"] + n["c_plan"] + n["c_member"]
        self.assertEqual(ac, 1232)
        self.assertTrue(oj_lo_b <= ac <= oj_hi_b and oj_lo <= ac <= oj_hi)
        # 要確認の幅(P25)は、記録の PNF + UNV から (a)(c) を引いた値を含む
        rec = p25_record()
        unv_pnf_p25 = rec["UNVERIFIABLE の合計 P25"] + rec["POINTER_NOT_FOUND の合計 P25"]
        self.assertEqual(unv_pnf_p25, 2791)
        self.assertTrue(chk_lo_b <= unv_pnf_p25 - ac <= chk_hi_b, (chk_lo_b, unv_pnf_p25 - ac, chk_hi_b))
        # 4 つの節 + 一致は P25 の記録の state の和と整合(違う = VALUE_MISMATCH、一致 = GROUNDED)
        self.assertEqual(rec["VALUE_MISMATCH の合計 P25"] + rec["GROUNDED の合計 P25"] + unv_pnf_p25, total)

    def test_4_section_0_numbers_are_pinned_as_written_and_sum(self):
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        # GROUNDED でない 3,557 のうち (a)(c)。(a) 145 + 6 = 151、(c) 1,001 + 42 + 38 = 1,081、合わせて 1,232 / 3,557 = 34.6%
        self.assertEqual((n["not_g"], n["a_unit"], n["a_prior"], n["c_subject"], n["c_plan"], n["c_member"]), (3557, 145, 6, 1001, 42, 38))
        self.assertEqual((n["ac_sum"], n["ac_den"], n["ac_pct"]), (1232, 3557, "34.6"))
        self.assertEqual(n["a_unit"] + n["a_prior"] + n["c_subject"] + n["c_plan"] + n["c_member"], n["ac_sum"])
        self.assertEqual(n["ac_den"], n["not_g"])
        self.assertEqual(round(100.0 * n["ac_sum"] / n["ac_den"], 1), 34.6)
        # 67 書類(既定 P22、7,799 claim)の節の件数と和
        self.assertEqual((n["claims"], n["wrong"], n["check"], n["out_of"], n["no_judge"], n["match"]), (7799, 1410, 915, 151, 1081, 4242))
        self.assertEqual(n["wrong"] + n["check"] + n["out_of"] + n["no_judge"] + n["match"], n["claims"])
        self.assertEqual((n["m_cur"], n["m_prior"], n["m_calc"]), (1736, 180, 2326))
        self.assertEqual(n["m_cur"] + n["m_prior"] + n["m_calc"], n["match"])
        # 対象外 151 = (a)、判断しない 1,081 = (c)。GROUNDED でない 3,557 = 違う + 要確認 + 対象外 + 判断しない
        self.assertEqual((n["out_of"], n["no_judge"]), (n["a_unit"] + n["a_prior"], n["c_subject"] + n["c_plan"] + n["c_member"]))
        self.assertEqual(n["wrong"] + n["check"] + n["out_of"] + n["no_judge"], n["not_g"])
        # 客 A: 39 claim、答え合わせ 5 件が 5 / 5 先頭の節
        self.assertEqual(n["case_a_claims"], 39)
        # 理由の表 14 key = UNBOUND_REASON_STATE 14 key(C-3 の 16 とは別の数。docstring)
        self.assertEqual((n["table_keys"], n["unbound_keys"]), (14, 14))
        # 指紋 15 → 16 file、frozen_bundle 36 → 37、golden 13 本
        self.assertEqual((n["fp_files_from"], n["fp_files_to"], n["fz_from"], n["fz_to"], n["golden"]), (15, 16, 36, 37, 13))
        self.assertEqual(n["fp_files_to"] - n["fp_files_from"], 1)
        self.assertEqual(n["fz_to"] - n["fz_from"], 1)

    def test_5_section_0_numbers_match_the_records(self):
        """P22 の VALUE_MISMATCH 1,410・GROUNDED 4,242(記録 rounding_2026-10-21.json)、P25 の 626・4,382・UNV 1,397・PNF 1,394(記録 lastbranch_2026-10-21.json)、
        総 claim 7,799・書類 67 が封の字と同じ。P22 の UNV + PNF は記録に欄が無く、引き算で出す(docstring)。"""
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        g22, vm22 = p22_record()
        self.assertEqual((g22, vm22), (n["match"], n["wrong"]))
        self.assertEqual(n["claims"] - g22 - vm22, 2147)
        self.assertEqual(n["check"] + n["out_of"] + n["no_judge"], 2147)
        rec = p25_record()
        r = jload(LASTBRANCH_JSON)
        self.assertEqual(rec["総 claim"], n["claims"])
        self.assertEqual(rec["書類数"], 67)
        b = sec(self.t, "## §2", "## §3")
        l2b = dict(rows(b, "C"))["2b"]
        self.assertEqual((rec["VALUE_MISMATCH の合計 P25"], rec["GROUNDED の合計 P25"]),
                         (num(re.search(r"「違う」\*\*([\d,]+)\*\*", l2b).group(1)), num(re.search(r"「一致」\*\*([\d,]+)\*\*", l2b).group(1))))
        self.assertEqual((rec["VALUE_MISMATCH の合計 P25"], rec["GROUNDED の合計 P25"]), (626, 4382))
        self.assertEqual((rec["UNVERIFIABLE の合計 P25"], rec["POINTER_NOT_FOUND の合計 P25"]), (1397, 1394))
        # P25 は P24 の VALUE_MISMATCH 577 行だけを POINTER_NOT_FOUND に動かす(GROUNDED・UNVERIFIABLE は不動)
        self.assertEqual(rec["POINTER_NOT_FOUND の合計 P25"] - rec["POINTER_NOT_FOUND の合計 P24"], 577)
        self.assertEqual(rec["GROUNDED の合計 P24"], rec["GROUNDED の合計 P25"])
        self.assertEqual(rec["UNVERIFIABLE の合計 P24"], rec["UNVERIFIABLE の合計 P25"])

    def test_6_section_1_order_of_sections_and_the_two_reason_lines(self):
        b = sec(self.t, "## §1", "## §2")
        items = re.findall(r"(?m)^  (\d)\. (.*)$", b)
        self.assertEqual([i for i, _ in items], ["1", "2", "3", "4", "5"])
        starts = [(u"**違う** = VALUE_MISMATCH。", u"文と同じ単位に直す"),
                  (u"**要確認** = POINTER_NOT_FOUND と UNVERIFIABLE のうち (a)(c) 以外。", u"表に無い reason は字のまま出して赤にしない"),
                  (u"**対象外**(出典に無い) = (a) の reason。**判断しない** = (c) の reason。", u"件数と抜粋だけ。"),
                  (u"**一致** = GROUNDED。", u"`--full` で出す"),
                  (u"末尾に小さく: ", u"profile")]
        for (i, line), want in zip(items, starts):
            for s in want:
                self.assertIn(s, line, s)
        self.assertTrue(items[0][1].startswith(starts[0][0]))
        # 節の順を表す字(違う → 要確認 → 対象外 / 判断しない → 一致 → 末尾の指紋)が行の頭に在る
        self.assertIn(u"- 節の順と字(state・reason から決定論で引く。表は字で留める):", b)
        # 理由の日本語表の 2 行(P24 の other_frame・P25 の no_same_value)は「要確認」に置く
        self.assertIn(u"P24 の `other_frame` と P25 の `no_same_value` は「要確認」に置く: ", b)
        self.assertIn(u"`other_frame` =「同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる」", b)
        self.assertIn(u"`no_same_value` =「出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる」", b)
        # 新 module・入口・純粋関数・golden・LLM なし・profile は入力のまま・議事録は別の封
        for s in (u"新 module `adapters/xbrl/report_customer.py`(`python3 -m adapters.xbrl.report_customer --in out.json --out report.md [--labels <dir>]`)。",
                  u"純粋関数、同じ JSON から同じバイト列(golden)。LLM なし。",
                  u"理由の日本語表(reason → 1 行)は登録簿の理由の全部を網羅する(`registry_setup._POINTER_NOT_FOUND_REASONS` 9 + `_UNVERIFIABLE_REASONS` 7 = 16。`recipes.UNBOUND_REASON_STATE` の 14 key + `other_frame` + `no_same_value` と同じ集合。網羅を門で縛る。新しい reason が増えたら赤)。",
                  u"profile は入力の JSON に書かれた profile をそのまま出す(報告は判定をしない)。測定は既定(P22)と P25 明示の 2 通り。",
                  u"議事録(`adapters/kokkai/report_meeting.py`)は別の封(この封は有報だけ)。"):
            self.assertIn(s, b, s)

    def test_7_limits_are_written(self):
        b = sec(self.t, "## §3", "## §4")
        for s in (u"「対象外」「判断しない」の線は reason 単位で、混在の reason(no_element 等)は全部「要確認」に入る(安全側)。",
                  u"標準ラベルは repo の外(2026-10-08 の人間の決定)。無ければ要素名のまま。",
                  u"IFRS(`jpigp_cor`)と会社ごとのセグメント member はラベル file に無く要素名のまま(67 書類で 48 行 + member の字)。",
                  u"語の主張(「増加した」等)の出典の値は単位が無いので円で出る。",
                  u"`report.py` 末尾の「率・差は文と同じ単位」は差については実物と違う(差も円)― `report.py` は触らないので、この封の文書に 1 行書く。",
                  u"「違う」が正しい文に出る率は報告の形では減らない(既定 P22 で 1,410 / 7,799 = 18.1%。",
                  u"P25 明示で減るのは P24・P25 の engine の直しの効き目で、この封の効き目ではない)。",
                  u"`no_same_value` の名指した当期の値は `Claim.provenance` に在るが、`verify_document` の出力 JSON には provenance の欄が無い。",
                  u"この封は `verify_document.py` を触らないので、報告に「当期の値は X」は出さない(理由の 1 行だけ)。出すなら別の封。"):
            self.assertIn(s, b, s)
        # 18.1% は §0 の件数から出る
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        self.assertEqual(round(100.0 * n["wrong"] / n["claims"], 1), 18.1)

    def test_8_reason_table_key_counts_match_the_engine(self):
        """封 §0 の「14 key = UNBOUND_REASON_STATE 14 key」は実物と合う。封 §2 C-3 の「**16**」は UNBOUND_REASON_STATE の key の数ではなく、
        登録簿の理由の数(`registry_setup._POINTER_NOT_FOUND_REASONS` 9 + `_UNVERIFIABLE_REASONS` 7)= UNBOUND_REASON_STATE の 14 + `other_frame` + `no_same_value`。
        封の字は直さず(docstring)、実物の関係を縛る。網羅の門の対象は、どちらで読んでも同じ 16 の集合になる。"""
        from adapters.xbrl import recipes, registry_setup as RS
        n = s0_numbers(sec(self.t, "## §0 ", "## §1"))
        keys = set(recipes.UNBOUND_REASON_STATE)
        self.assertEqual(len(recipes.UNBOUND_REASON_STATE), 14)
        self.assertEqual(len(keys), n["unbound_keys"])
        self.assertEqual(len(keys), n["table_keys"])
        reg = set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS)
        # 2026-10-22(P26 の段 1。封 docs/XBRL_P26_SEAL_2026-10-21.md §2 Q-7「登録簿の理由 16 → 19」): 理由を 3 つ足した(POINTER_NOT_FOUND 9 → 10・UNVERIFIABLE 7 → 9)。
        # この封の commit 時点は (9, 7) と 16(下の c3 の字 16 と n["unbound_keys"] 14 がその事実)。いまは宣言された 19。
        self.assertEqual((len(RS._POINTER_NOT_FOUND_REASONS), len(RS._UNVERIFIABLE_REASONS)), (10, 9))
        self.assertEqual(len(reg), 19)
        # 2 つの理由は UNBOUND_REASON_STATE に無く、_state_of の別の枝と登録簿に在る(+ P26 の 3 つ)
        self.assertEqual(sorted(reg - keys), sorted(["no_same_value", "other_frame"] + list(P26_REASONS)))
        self.assertEqual(keys - reg, set())
        self.assertNotIn("other_frame", keys)
        self.assertNotIn("no_same_value", keys)
        self.assertEqual(recipes._state_of("no_same_value", "POINTER_NOT_FOUND"), "POINTER_NOT_FOUND")
        self.assertEqual(recipes._state_of("other_frame(CurrentYearDuration)", "POINTER_NOT_FOUND"), "UNVERIFIABLE")
        # 登録簿の state は UNBOUND_REASON_STATE の state と全 key で同じ(2 つの理由は封 §1 のとおり POINTER_NOT_FOUND / UNVERIFIABLE)
        for k, st in recipes.UNBOUND_REASON_STATE.items():
            self.assertEqual(st, "POINTER_NOT_FOUND" if k in RS._POINTER_NOT_FOUND_REASONS else "UNVERIFIABLE", k)
        # C-3 の字 16 は登録簿の数と同じ(UNBOUND_REASON_STATE の 14 + 2 の分解も字で在る)
        c3 = dict(rows(sec(self.t, "## §2", "## §3"), "C"))["3"]
        self.assertEqual(int(re.search(r"\*\*(\d+)\*\*", c3).group(1)), len(reg) - len(P26_REASONS))        # 封の字 16 = 測った時点の登録簿。いまは P26 の 3 つを足して 19
        self.assertIn(u"`UNBOUND_REASON_STATE` の 14 key + `other_frame` + `no_same_value`", c3)

    def test_9_closed_file_list_and_order(self):
        b = sec(self.t, "## §4")
        first = b[:b.index(u"\n順序:")]
        # 既存の P25 の試験に 1 本足す(桁の倍数でない値の unit 試験。engine は変えない)。この段落は矢印の列より前
        tok = "`%s`" % P25_UNIT_TEST
        self.assertEqual(first.count(tok), 1)
        self.assertIn(u"`_written_precision` の丸めを切り捨てにする変異が黙る", first)
        self.assertIn(u"桁の倍数でない値の unit 試験を", first)
        chain_at = first.index("`%s` →" % NEW_MODULE)
        self.assertLess(first.index(tok), chain_at)
        pos = []
        for rel in FILES:
            tk = "`%s`" % rel
            self.assertEqual(first.count(tk), 1, rel)
            pos.append(first.index(tk))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertEqual(len(FILES), 6)
        # 矢印の列の字(書かれた順): module → 試験(golden・網羅・単位・C-4)→ measure(C-1・C-2)→ 記録 → 結果文書 → 結果の門 → README → pin → 覆い
        chain = first[chain_at:]
        for s in (u"`tests/adapters/xbrl/test_report_customer.py`(golden・網羅・単位・C-4)",
                  u"`measure/xbrl_customer_report_2026-10-21.py`(C-1・C-2)",
                  u"README の入口(有報: 自分の zip + 文 + 報告の 3 行)",
                  u"pin の遷移の宣言(engine の束ねた sha・frozen_bundle 36 → 37・point_prior の B-5・ritual の R-8・"
                  u"ENGINE_LATER は vocabulary/recipes が不変なら不要、axis3 の LATER_ENGINE_COMMITS は次の便)",
                  u"→ 覆い。"):
            self.assertIn(s, chain, s)
        p = [chain.index(s) for s in (u"README の入口", u"pin の遷移の宣言", u"→ 覆い。")]
        self.assertEqual(p, sorted(p))
        self.assertGreater(chain.index(u"README の入口"), chain.index("`tests/measure/test_xbrl_customer_report_result.py`"))
        # 試作は scratchpad の clone(追跡外)。流用してよいが、other_frame・no_same_value の行と C-2b はこの封で足す
        self.assertIn(u"試作の module は scratchpad の clone(`scratchpad/report/clone/audit-core/adapters/xbrl/report_customer.py`、513 行、試験 18 本)。", first)
        self.assertIn(u"流用してよいが、P24 の `other_frame`・P25 の `no_same_value` の行と C-2b はこの封で足す。", first)
        order = b[b.index(u"\n順序:"):]
        self.assertIn(u"順序: 人間の事前承認(2026-10-21)→ P25 段 1 の commit(9577eab・宣言 0db03a4)→ この封 + 門を commit → 実装 → 凍結 → 独立監査 → commit → "
                      u"axis3 の宣言 → 段 2(既定の切り替え)を人間に。", order)
        # 実在する既存 file は在る
        self.assertTrue(os.path.exists(os.path.join(ROOT, P25_UNIT_TEST)))
        for c in ("9577eab", "0db03a4"):
            self.assertEqual(git("cat-file", "-e", c + "^{commit}").returncode, 0, u"封が名指す commit %s が無い" % c)


class SealedStateTest(unittest.TestCase):
    """封の commit 時点の木を字で留める。実装の便で赤くなるもの(新しい file が在る・指紋が動く)は docstring のとおり、遷移の宣言で直す。"""

    def test_10_new_files_exist_now_the_seal_came_first(self):
        u"""封が実装より先であることは、実装の便で「在る」に直した(2026-10-21。封の commit 時点は §4 の新規 6 本が作業木にも履歴にも無かった = 測った当時の事実。
        P25 の封の門 test_14 と同じ型)。いまは 6 本が作業木に在り、module は import できる。封が先であることは test_13(commit の順)が縛る。"""
        for rel in FILES:
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), u"実装の便で作る file が無い: " + rel)
        r = subprocess.run([sys.executable, "-c", "import adapters.xbrl.report_customer"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_11_untouched_files_keep_their_sha(self):
        """C-5: `report.py`(人間の決定 2026-10-13)・`verify_document.py` は 0 行。engine の他の 3 file(vocabulary・recipes・registry_setup)も
        封は触らない。宣言の遷移を持たない: 動いたら赤のまま。"""
        for rel, want in sorted(UNTOUCHED.items()):
            got = sha16(rel)
            if got != want and rel in UNTOUCHED_LATER:
                later, seal_rel = UNTOUCHED_LATER[rel]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(),
                                u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (rel, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % rel)
                continue
            self.assertEqual(got, want, u"**%s が動いている(この封は触らない)**" % rel)
        for rel in ("report", "verify_document"):
            self.assertNotIn("adapters/xbrl/%s.py" % rel, UNTOUCHED_LATER)
        # report.py の golden の試験が在る(C-4 の「不変」の相手)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_report.py")))
        t = text(os.path.join(ROOT, "tests", "adapters", "xbrl", "test_report.py"))
        self.assertEqual(len(re.findall(r"(?m)^    def test_", t)), 13)

    def test_12_engine_fingerprint_and_frozen_bundle_are_the_ones_at_the_seal_or_a_declared_transition(self):
        """module を足すと `adapter_xbrl_py_sha256` が動く(15 → 16 file)・frozen_bundle の本数が 36 → 37 になる。封の commit 時点の値を字で留め、
        後は `FINGERPRINT_LATER` に宣言された値(と、それを宣言した封が履歴に在ること)だけを受け入れる。"""
        from adapters.xbrl import verify_document as VD
        fp = VD.engine_fingerprint()
        for k, want in sorted(FINGERPRINT_AT_SEAL.items()):
            got = fp[k]
            if got != want and k in FINGERPRINT_LATER:
                later, seal_rel = FINGERPRINT_LATER[k]
                self.assertTrue(git("log", "--diff-filter=A", "--format=%H", "--", seal_rel).stdout.split(),
                                u"**%s が動いているのに、遷移を宣言した封 %s が履歴に無い**" % (k, seal_rel))
                self.assertEqual(got, later, u"**%s が、宣言された遷移の値とも違う**" % k)
                continue
            self.assertEqual(got, want, u"**%s が動いている(実装の便の commit で FINGERPRINT_LATER に遷移を宣言する)**" % k)
        # adapters/xbrl の .py の数は指紋の file 数と同じ(いまは 16。封の commit 時点は 15)。__pycache__ は数えない
        py = [f for f in os.listdir(os.path.join(ROOT, "adapters", "xbrl")) if f.endswith(".py")]
        self.assertEqual(len(py), fp["adapter_xbrl_py_files"])
        # frozen_bundle: 字の本数 36 と git ls-files の本数・束ねた sha(repo の根で測る。frozen_bundle_sha.py は repo 相対の path で git に問う)
        src = text(os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py"))
        count = int(re.search(r"(?m)^FROZEN_COUNT = (\d+)", src).group(1))
        gens = re.findall(r'\("([0-9a-f]{64})",\n', src)
        r = subprocess.run([sys.executable, os.path.join(ROOT, "fixtures", "frozen_bundle_sha.py")], cwd=REPO, capture_output=True, text=True)
        out = r.stdout
        m = re.search(r"対象 (\d+) 本 @ ", out)
        self.assertIsNotNone(m, out)
        n_files = int(m.group(1))
        if count == FROZEN_COUNT_AT_SEAL and n_files == FROZEN_COUNT_AT_SEAL:
            self.assertEqual(r.returncode, 0, out)
            self.assertIn(FROZEN_BUNDLE_AT_SEAL, out)
            self.assertEqual(gens[-1], FROZEN_BUNDLE_AT_SEAL)
        else:
            # 実装の便の後: 37 本・新しい世代。宣言(FINGERPRINT_LATER)が無ければ赤にする
            self.assertTrue(FINGERPRINT_LATER, u"**frozen_bundle の本数が %d(定数 %d)に動いているのに、遷移の宣言が無い**" % (n_files, count))
            self.assertEqual((count, n_files), (FROZEN_COUNT_AFTER, FROZEN_COUNT_AFTER), u"遷移は 36 → 37 本だけ宣言されている")
            self.assertEqual(r.returncode, 0, out)
            self.assertIn(FROZEN_BUNDLE_DEFAULT_P26, out)
            self.assertEqual(gens[-1], FROZEN_BUNDLE_DEFAULT_P26)
            self.assertIn(FROZEN_BUNDLE_AT_SEAL, gens, u"封の commit 時点の世代は消さない")
            self.assertIn(FROZEN_BUNDLE_STAGE1, gens, u"段 1(c13a746)の世代は消さない")
            self.assertEqual(gens.index(FROZEN_BUNDLE_AFTER), gens.index(FROZEN_BUNDLE_STAGE1) + 1, u"段 2 の世代は段 1 の次")
            self.assertEqual(gens.index(FROZEN_BUNDLE_P26), gens.index(FROZEN_BUNDLE_AFTER) + 1, u"P26 の段 1 の世代は報告形の直しの次")
            self.assertEqual(gens.index(FROZEN_BUNDLE_DEFAULT_P26), gens.index(FROZEN_BUNDLE_P26) + 1, u"既定を P26 にした段 2 の世代は P26 の段 1 の次")
        # 字で留めた本数は git が数える本数と同じ(今)
        ls = subprocess.run(["git", "ls-files", "audit-core/core", "audit-core/adapters"], cwd=REPO, capture_output=True, text=True).stdout.split()
        self.assertEqual(len(ls), n_files)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        shas = [s for s in git("log", "--diff-filter=A", "--format=%H", "--", rel).stdout.split() if s]
        return shas[-1] if shas else None

    def test_13_the_seal_precedes_every_later_file(self):
        tracked = git("ls-files", "--error-unmatch", SEAL_REL).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in FILES:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.skipTest(u"封がまだ commit されていない(後の file が履歴に無いことだけ確かめた)")
        seal = self._added(SEAL_REL)
        for rel in FILES:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(git("merge-base", "--is-ancestor", seal, other).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
