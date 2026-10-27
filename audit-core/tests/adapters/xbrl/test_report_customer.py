# -*- coding: utf-8 -*-
"""顧客向け報告(``adapters/xbrl/report_customer.py``)の試験。封 ``docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md``。

留めるもの: (1) golden ― 手で書いた小さな入力の報告をバイト列で字のまま(全節・other_frame・no_same_value・表に無い reason を含む)と、
実出力 2 件の報告の sha256、(2) 網羅(C-3)― 理由の日本語表は登録簿の理由の全部(16)と同じ集合で、1 つ消すと網羅の検査が赤になる、
(3) 単位 ― 百万円の文は百万円、千円の文は千円、率は率、語の主張は円、(4) 節の順と各節の中身、(5) other_frame と no_same_value の 1 行は
封の字のまま「要確認」に在る、(6) 同じ入力から同じバイト列(C-4)・CLI も同じ、(7) 判定を足さず変えない(全 claim が 1 回ずつ、state・reason で決まる節にだけ)、
(8) LLM・通信を import しない。

**段 2(封 ``docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md``、2026-10-21)で足したもの**: (9) 名簿 ― 名簿に在る file 名だけを sha256 が合うときだけ読む、名簿の外の file を置いても本文が同じ、
(10) 単位・桁・符号 ― 文の字の単位で出す、丸めた字 + 括弧に生の値、負は △、(11) 指紋は本文に無く ``.provenance.json`` に在る、(12) 表題(DEI)、(13) 抜粋は数の途中で切らない、
(14) 書類自身のラベル(``--zip``)。**golden の遷移**: 段 1(c13a746)の golden は「文の値」が claim の単位・出典の値が丸め無し・末尾に指紋の 5 行・「違う」の意味の欄に但し書き無し。
段 2 はそれらが変わるので ``SMALL_GOLDEN`` と ``GOLDEN_SHA256`` を新しい値にした(段 1 の値は ``GOLDEN_SHA256_C13A746`` に残す)。
"""

import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import zipfile

from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import report_customer as RC

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIX = os.path.join(_ROOT, "fixtures", "xbrl")
CASES = ("entry_output_S100Z4N9_original_2026-10-13.json", "entry_output_S100Z4Q1_ai_prose_2026-10-13.json")
# 実出力 2 件の報告(ラベル無し)の sha256。記法を変えたら必ず赤くなる。(既定 = 行なし / --full = 一致の行も)
# **段 2(封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md)の値**。測った当時の段 1(c13a746)の値は GOLDEN_SHA256_C13A746 に残す(消さない)。
GOLDEN_SHA256 = {
    (CASES[0], False): "62b94cbe2b19ae9e6ceec5afd76e1291153be9b64cc3cdd5119c03bdb0d31f4c",
    (CASES[0], True): "908b206d8171dd7107b9e512585d75da55780076c11d8b6b1762e1fa5f3247fe",
    (CASES[1], False): "917afc01d18a77b709e8bde08eec83c213f5b0c38b2bffae784b6c2287060a4c",
    (CASES[1], True): "2c7ccc60ed9137b0615b5f101a2de896c8ba4835938f631b0e766af725a0552e",
}
# 段 1(c13a746)の値。末尾の指紋の行(<sub>…</sub> 5 行。入力 JSON の engine・input が空でない実出力ではそれが入る)を含む形の sha256。段 2 の module では再現しない(測った当時の値として残す)。
GOLDEN_SHA256_C13A746 = {
    (CASES[0], False): "0ea0fdea5234066ac63fd312de133bc7c48f5d1b0882d8532fbcfaec7393de4c",
    (CASES[0], True): "3f7ad3a6e56b739c6795aab7000e3eaa9a81960c8896375ce12f04509b318a68",
    (CASES[1], False): "0a0aeb4a01956715c18e57b19164fc8a17a5fd3269eed3f57d9440bf34dac458",
    (CASES[1], True): "72e05152c491f7d39cc19f8cfb4238089bd28ae1af45e74370142fe427992fee",
}
_ROW = re.compile(r"^\| ([NT]\d{3}) \|", re.M)
_BULLET = re.compile(r"^- ([NT]\d{3}): ", re.M)

LABELS = {"jppfs_cor_NetSales": "売上高", "jppfs_cor_Assets": "資産"}


def _load(name):
    with io.open(os.path.join(_FIX, name), "r", encoding="utf-8") as f:
        return json.load(f)


def _claim(i, span, value, unit, state, reason, pointers, recomputed, word=None):
    return {"id": i, "span": span, "value": value, "unit": unit, "word": word, "state": state, "reason": reason,
            "pointers": pointers, "recomputed": recomputed}


def _small():
    """手で書いた 9 claim: 違う 3(百万円・率・千円)/ 要確認 3(no_same_value・other_frame・表に無い reason)/ 対象外 1 / 判断しない 1 / 一致 1。"""
    cl = [
        _claim("N001", "売上高は40,539百万円", 40539.0, "百万円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], 40480000000.0),
        _claim("N002", "前期比26.2%増", 26.2, "%", "VALUE_MISMATCH", None,
               ["xbrl:jppfs_cor:NetSales@CurrentYearDuration", "xbrl:jppfs_cor:NetSales@Prior1YearDuration"], 36.22),
        _claim("N003", "総資産は53,812千円", 53812.0, "千円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:Assets@CurrentYearInstant"], 53812000000.0),
        _claim("N004", "売上高は100百万円", 100.0, "百万円", "GROUNDED", None, ["xbrl:jppfs_cor:NetSales@Prior1YearDuration"], 100000000.0),
        _claim("N005", "営業利益は3百万円", 3.0, "百万円", "POINTER_NOT_FOUND", "no_same_value", [], None),
        _claim("N006", "売上高は7百万円", 7.0, "百万円", "UNVERIFIABLE", "other_frame", [], None),
        _claim("N007", "従業員は10名", 10.0, "名", "POINTER_NOT_FOUND", "no_element(unit not in XBRL)", [], None),
        _claim("T001", "増加した", None, None, "UNVERIFIABLE", "no_subject", [], None, word="増加"),
        _claim("T002", "減少した", None, None, "UNVERIFIABLE", "something(new)", [], None, word="減少"),
    ]
    return {"document": {"claims": len(cl)}, "input": {}, "engine": {}, "claims": cl}


SMALL_GOLDEN = u"""# 文章と出典(XBRL)の照合 ― (書類)

文章の中の数と増減の語を、同じ書類の XBRL の値と突き合わせた。判定は道具が出したまま並べ替えている(足していない)。

| 区分 | 件数 | 意味 |
|---|---|---|
| 違う | 3 | 出典に当たる値があり、文の値と**違う**。文の誤りか、当てた出典の誤りかは決めない |
| 要確認 | 3 | 道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる |
| 対象外 | 1 | 出典(XBRL)にその数は無い(株数・人数など) |
| 判断しない | 1 | 主語が無い・目標や計画・区分が決まらない。道具は判断しない |
| 一致 | 1 | 出典の値と一致した |
| 合計 | 9 | |

## 1. 違う ― 3 件

出典に当たる値は見つかったが、文の値と違う。文の誤りか、当てた出典の誤りかは、この表では決めない。「出典の値」は文と同じ単位に直してある。

出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)

| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |
|---|---|---|---|---|
| N001 | 売上高は40,539百万円 | 40,539百万円 | 40,480 百万円 | 売上高 当期 |
| N002 | 前期比26.2%増 | 26.2 % | 36.2 %(36.22) | 売上高 当期 / 売上高 前期(前期比(当期 ÷ 前期 − 1)) |
| N003 | 総資産は53,812千円 | 53,812千円 | 53,812,000 千円 | 資産 当期末 |

## 2. 要確認 ― 3 件

道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる。

| # | 文の抜粋 | 文の値 | 理由 |
|---|---|---|---|
| N005 | 営業利益は3百万円 | 3百万円 | 出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる |
| N006 | 売上高は7百万円 | 7百万円 | 同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる |
| T002 | 減少した | 減少 | something(new) |

## 3. 対象外 ― 1 件 / 判断しない ― 1 件

対象外: 出典(XBRL)にその数は無い(株数・人数・区分ごとの前期の数など)。判断しない: 主語が無い・目標や計画の数・区分が 1 つに決まらない文。道具は判断しない。

### 対象外 ― 1 件

- N007: 従業員は10名(文の単位(株・名・件 など)の数は出典(XBRL)に無い)

### 判断しない ― 1 件

- T001: 増加した(文に主語(どの項目の数か)が無い)

## 4. 一致 ― 1 件

文の値と出典の値が一致した。出典の内訳: 当期 0 件 / 前期 1 件 / 計算 0 件。

出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)

(行は `--full` で出す)

---

<sub>書類の指紋・道具の版・照合した文章の指紋は、同じ名前の `.provenance.json`(機械用)に置いた。</sub>
"""


def _units():
    """段 2 の golden 用に手で書いた入力。claim の単位は円だが文は百万円(a)・負(△)・桁(括弧)・兆億の複合と繰り上がり・語の主張(文の単位 / 書類の単位)・読み取れない行・数の途中で切れた抜粋。"""
    cl = [
        _claim("N001", "有形・無形固定資産の取得による支出112百万円及びその他", 112000000.0, "円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:Assets@CurrentYearDuration"], -111150000.0),
        _claim("N002", "営業収益は26億23百万円となり", 2623000000.0, "円", "GROUNDED", None, ["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], 2623000000.0),
        _claim("N003", "営業収益は26億99百万円となり", 2699000000.0, "円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], 2699600000.0),
        _claim("N004", "売上高は1,234.5百万円", 1234500000.0, "円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], 1234512000.0),
        _claim("N005", "利益は100百万円", 100.0, "百万円", "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:Assets@CurrentYearDuration"], 100400000.0),
        _claim("N006", "売上高は7百万円", 7000000.0, "円", "UNVERIFIABLE", "other_frame", [], None),
        _claim("N007", "従業員は1,195名", 1195.0, "名", "POINTER_NOT_FOUND", "no_element(unit not in XBRL)", [], None),
        _claim("T001", "前連結会計年度末に比べ569百万円増加しました", None, None, "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:Assets@CurrentYearInstant", "xbrl:jppfs_cor:Assets@Prior1YearInstant", "builtin:sign(cur-prior)"], -569000000.0, word="増加"),
        _claim("T002", "利益は増加しました", None, None, "VALUE_MISMATCH", None, ["xbrl:jppfs_cor:Assets@CurrentYearInstant", "xbrl:jppfs_cor:Assets@Prior1YearInstant", "builtin:sign(cur-prior)"], -123456789.0, word="増加"),
        _claim("T003", "この結果、1株当たり当期純利益は6", None, None, "UNVERIFIABLE", "no_subject", [], None, word="増加"),
        _claim("N008", "る支出32,110百万円、取得による支出が6", 6.0, "名", "UNVERIFIABLE", "no_subject", [], None),
    ]
    return {"document": {"claims": len(cl)}, "input": {}, "engine": {}, "claims": cl}


UNITS_GOLDEN = u"""# 文章と出典(XBRL)の照合 ― (書類)

文章の中の数と増減の語を、同じ書類の XBRL の値と突き合わせた。判定は道具が出したまま並べ替えている(足していない)。

| 区分 | 件数 | 意味 |
|---|---|---|
| 違う | 6 | 出典に当たる値があり、文の値と**違う**。文の誤りか、当てた出典の誤りかは決めない |
| 要確認 | 1 | 道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる |
| 対象外 | 1 | 出典(XBRL)にその数は無い(株数・人数など) |
| 判断しない | 2 | 主語が無い・目標や計画・区分が決まらない。道具は判断しない |
| 一致 | 1 | 出典の値と一致した |
| 合計 | 11 | |

## 1. 違う ― 6 件

出典に当たる値は見つかったが、文の値と違う。文の誤りか、当てた出典の誤りかは、この表では決めない。「出典の値」は文と同じ単位に直してある。

出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)

| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |
|---|---|---|---|---|
| N001 | 有形・無形固定資産の取得による支出112百万円及びその他 | 112百万円 | △111 百万円(△111.15) | 資産 当期 |
| N003 | 営業収益は26億99百万円となり | 26億99百万円 | 27億円(26億99.6百万円) | 売上高 当期 |
| N004 | 売上高は1,234.5百万円 | 1,234.5百万円 | 1,234.5 百万円(1,234.512) | 売上高 当期 |
| N005 | 利益は100百万円 | 100百万円 | 100 百万円(100.4) | 資産 当期 |
| T001 | 前連結会計年度末に比べ569百万円増加しました | 増加 | △569 百万円 | 資産 当期末 / 資産 前期末(当期末 − 前期末 の符号) |
| T002 | 利益は増加しました | 増加 | △123 百万円(△123.4568) | 資産 当期末 / 資産 前期末(当期末 − 前期末 の符号) |

## 2. 要確認 ― 1 件

道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる。

| # | 文の抜粋 | 文の値 | 理由 |
|---|---|---|---|
| N006 | 売上高は7百万円 | 7百万円 | 同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる |

## 3. 対象外 ― 1 件 / 判断しない ― 2 件

対象外: 出典(XBRL)にその数は無い(株数・人数・区分ごとの前期の数など)。判断しない: 主語が無い・目標や計画の数・区分が 1 つに決まらない文。道具は判断しない。

### 対象外 ― 1 件

- N007: 従業員は1,195名(文の単位(株・名・件 など)の数は出典(XBRL)に無い)

### 判断しない ― 2 件

- T003: この結果、1株当たり当期純利益は(文に主語(どの項目の数か)が無い)
- N008: る支出32,110百万円、取得による支出が(文に主語(どの項目の数か)が無い)

## 4. 一致 ― 1 件

文の値と出典の値が一致した。出典の内訳: 当期 1 件 / 前期 0 件 / 計算 0 件。

出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)

| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |
|---|---|---|---|---|
| N002 | 営業収益は26億23百万円となり | 26億23百万円 | 26億23百万円 | 売上高 当期 |

---

<sub>書類の指紋・道具の版・照合した文章の指紋は、同じ名前の `.provenance.json`(機械用)に置いた。</sub>
"""


def registry_reasons():
    """登録簿の理由の全部(POINTER_NOT_FOUND 9 + UNVERIFIABLE 7 = 16)。"""
    return set(RS._POINTER_NOT_FOUND_REASONS) | set(RS._UNVERIFIABLE_REASONS)


def uncovered(table):
    """登録簿の理由のうち、日本語の表に無いもの(網羅の検査)。"""
    return sorted(registry_reasons() - set(table))


class GoldenTest(unittest.TestCase):
    def test_small_input_matches_golden_bytes(self):
        self.assertEqual(RC.render_markdown(_small(), LABELS, False), SMALL_GOLDEN)

    def test_real_outputs_match_pinned_sha256(self):
        for (js, full), want in sorted(GOLDEN_SHA256.items()):
            md = RC.render_markdown(_load(js), None, full)
            self.assertEqual(hashlib.sha256(md.encode("utf-8")).hexdigest(), want, (js, full))


class ReasonTableTest(unittest.TestCase):
    def test_registry_has_sixteen_reasons_and_is_unbound_reason_state_plus_two(self):
        # 2026-10-22 P26 の段 1(封 XBRL_P26_SEAL_2026-10-21 §2 Q-7「登録簿の理由 16 → 19」): 理由を 3 つ足した。名前の sixteen は 16 のときの名(測った当時)
        reg = registry_reasons()
        # 2026-10-27 P27 の段 2(封 XBRL_P27_SEAL_2026-10-27): 理由 per_unit_counter を足して 20。19 は P26 の段 1 のときの数
        self.assertEqual(len(reg), 20)
        self.assertEqual(reg, set(R.UNBOUND_REASON_STATE) | {"other_frame", "no_same_value", "other_concept", "direction_on_cause_item", "rounded_diff_within_double_band", "per_unit_counter"})

    def test_reason_table_is_exactly_the_registry(self):
        self.assertEqual(uncovered(RC.REASON_JA), [])
        self.assertEqual(sorted(set(RC.REASON_JA) - registry_reasons()), [])
        self.assertEqual(len(RC.REASON_JA), 20)         # 2026-10-22 P26 の段 1: 16 → 19、2026-10-27 P27 の段 2: 19 → 20(per_unit_counter)

    def test_removing_any_one_reason_turns_the_coverage_check_red(self):
        for k in sorted(RC.REASON_JA):
            t = dict(RC.REASON_JA)
            del t[k]
            self.assertEqual(uncovered(t), [k], k)

    def test_each_japanese_line_is_one_line_and_not_the_key(self):
        for k, v in RC.REASON_JA.items():
            self.assertNotIn("\n", v)
            self.assertNotEqual(k, v)
            self.assertTrue(v)

    def test_out_of_scope_and_not_judged_are_subsets_of_the_table(self):
        for k in RC.OUT_OF_SCOPE_REASONS + RC.NOT_JUDGED_REASONS:
            self.assertIn(k, RC.REASON_JA)
        self.assertFalse(set(RC.OUT_OF_SCOPE_REASONS) & set(RC.NOT_JUDGED_REASONS))

    def test_unknown_reason_is_rendered_verbatim_and_does_not_fail(self):
        self.assertEqual(RC.reason_ja("something(new)"), "something(new)")
        self.assertEqual(RC.reason_ja(None), "―")
        md = RC.render_markdown(_small(), LABELS, False)
        self.assertIn("| T002 | 減少した | 減少 | something(new) |", md)

    def test_the_two_sealed_lines_are_written_as_sealed(self):
        self.assertEqual(RC.REASON_JA["other_frame"], "同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる")
        self.assertEqual(RC.REASON_JA["no_same_value"], "出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる")


class SectionOrderTest(unittest.TestCase):
    def test_sections_come_in_the_sealed_order(self):
        md = RC.render_markdown(_small(), LABELS, False)
        heads = re.findall(r"(?m)^## \d\. (違う|要確認|対象外|一致)", md)
        self.assertEqual(heads, ["違う", "要確認", "対象外", "一致"])
        pos = [md.index(s) for s in ("## 1. 違う", "## 2. 要確認", "## 3. 対象外", "### 対象外", "### 判断しない", "## 4. 一致", "\n---\n")]
        self.assertEqual(pos, sorted(pos))

    def test_other_frame_and_no_same_value_are_in_the_check_section_only(self):
        md = RC.render_markdown(_small(), LABELS, False)
        a, b = md.index("## 2. 要確認"), md.index("## 3. 対象外")
        check = md[a:b]
        for rid in ("N005", "N006"):
            self.assertIn("| %s |" % rid, check)
            self.assertNotIn("| %s |" % rid, md[:a])
            self.assertNotIn("%s" % rid, md[b:])
        self.assertIn(RC.REASON_JA["no_same_value"], check)
        self.assertIn(RC.REASON_JA["other_frame"], check)

    def test_section_of_is_decided_by_state_and_reason_only(self):
        S = RC.section_of
        self.assertEqual(S({"state": "VALUE_MISMATCH"}), RC.SECTION_MISMATCH)
        self.assertEqual(S({"state": "GROUNDED"}), RC.SECTION_MATCH)
        self.assertEqual(S({"state": "POINTER_NOT_FOUND", "reason": "no_element"}), RC.SECTION_CHECK)
        self.assertEqual(S({"state": "POINTER_NOT_FOUND", "reason": "no_same_value"}), RC.SECTION_CHECK)
        self.assertEqual(S({"state": "UNVERIFIABLE", "reason": "other_frame"}), RC.SECTION_CHECK)
        self.assertEqual(S({"state": "POINTER_NOT_FOUND", "reason": "no_element(unit not in XBRL)"}), RC.SECTION_OUT)
        self.assertEqual(S({"state": "POINTER_NOT_FOUND", "reason": "no_prior_member_context"}), RC.SECTION_OUT)
        self.assertEqual(S({"state": "UNVERIFIABLE", "reason": "no_subject"}), RC.SECTION_NOT_JUDGED)
        self.assertEqual(S({"state": "UNVERIFIABLE", "reason": "target_or_plan"}), RC.SECTION_NOT_JUDGED)
        self.assertEqual(S({"state": "UNVERIFIABLE", "reason": "ambiguous(member)"}), RC.SECTION_NOT_JUDGED)
        self.assertEqual(S({"state": "UNVERIFIABLE", "reason": "ambiguous(elements)"}), RC.SECTION_CHECK)
        self.assertEqual(S({"state": "GROUNDED", "reason": "no_subject"}), RC.SECTION_MATCH)
        self.assertEqual(S({"state": "VALUE_MISMATCH", "reason": "no_subject"}), RC.SECTION_MISMATCH)

    def test_every_registry_reason_lands_in_a_section_and_only_the_five_known_leave_the_check_section(self):
        out_of_check = set()
        for k in registry_reasons():
            st = "POINTER_NOT_FOUND" if k in RS._POINTER_NOT_FOUND_REASONS else "UNVERIFIABLE"
            if RC.section_of({"state": st, "reason": k}) != RC.SECTION_CHECK:
                out_of_check.add(k)
        self.assertEqual(out_of_check, {"no_element(unit not in XBRL)", "no_prior_member_context", "no_subject", "target_or_plan", "ambiguous(member)"})


class DeterminismTest(unittest.TestCase):
    def test_same_input_twice_gives_same_bytes(self):
        for js in CASES:
            out = _load(js)
            for full in (False, True):
                a = RC.render_markdown(out, None, full)
                b = RC.render_markdown(json.loads(json.dumps(out)), None, full)
                self.assertEqual(a, b, js)

    def test_cli_twice_gives_same_bytes_and_same_as_the_function(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in.json")
            out = _load(CASES[0])
            with io.open(src, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False)
            shas = []
            for i in (1, 2):
                dst = os.path.join(d, "r%d.md" % i)
                r = subprocess.run([sys.executable, "-m", "adapters.xbrl.report_customer", "--in", src, "--out", dst],
                                   cwd=_ROOT, capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                with open(dst, "rb") as f:
                    shas.append(hashlib.sha256(f.read()).hexdigest())
            self.assertEqual(shas[0], shas[1])
            self.assertEqual(shas[0], hashlib.sha256(RC.render_markdown(out, None, False).encode("utf-8")).hexdigest())
            self.assertTrue(os.path.exists(os.path.join(d, "r1.provenance.json")))

    def test_full_flag_adds_only_the_match_rows(self):
        out = _load(CASES[0])
        a = RC.render_markdown(out, None, False)
        b = RC.render_markdown(out, None, True)
        self.assertNotEqual(a, b)
        n_match = sum(1 for c in out["claims"] if c["state"] == "GROUNDED")
        self.assertEqual(len(_ROW.findall(b)) - len(_ROW.findall(a)), n_match)


class NoReclassificationTest(unittest.TestCase):
    def test_every_claim_appears_once_in_full_mode(self):
        for js in CASES:
            out = _load(js)
            md = RC.render_markdown(out, None, True)
            ids = _ROW.findall(md) + _BULLET.findall(md)
            self.assertEqual(sorted(ids), sorted(c["id"] for c in out["claims"]), js)

    def test_section_counts_match_section_of(self):
        for js in CASES:
            out = _load(js)
            md = RC.render_markdown(out, None, False)
            want = {}
            for c in out["claims"]:
                s = RC.section_of(c)
                want[s] = want.get(s, 0) + 1
            for name in (RC.SECTION_MISMATCH, RC.SECTION_CHECK, RC.SECTION_MATCH):
                m = re.search(r"^## \d\. %s ― ([\d,]+) 件" % re.escape(name), md, re.M)
                self.assertIsNotNone(m, name)
                self.assertEqual(int(m.group(1).replace(",", "")), want.get(name, 0), (js, name))
            for name in (RC.SECTION_OUT, RC.SECTION_NOT_JUDGED):
                m = re.search(r"^### %s ― ([\d,]+) 件" % re.escape(name), md, re.M)
                self.assertIsNotNone(m, name)
                self.assertEqual(int(m.group(1).replace(",", "")), want.get(name, 0), (js, name))

    def test_report_does_not_mutate_its_input(self):
        out = _load(CASES[1])
        before = json.dumps(out, sort_keys=True)
        RC.render_markdown(out, None, True)
        self.assertEqual(json.dumps(out, sort_keys=True), before)


class UnitTest(unittest.TestCase):
    def test_direct_value_in_million_yen_stays_million_yen(self):
        self.assertEqual(RC.source_value_ja({"value": 40539.0, "unit": "百万円", "recomputed": 40480000000.0}), "40,480 百万円")

    def test_direct_value_in_thousand_yen_stays_thousand_yen(self):
        self.assertEqual(RC.source_value_ja({"value": 53812.0, "unit": "千円", "recomputed": 53812000000.0}), "53,812,000 千円")

    def test_other_money_units(self):
        self.assertEqual(RC.source_value_ja({"value": 1.0, "unit": "億円", "recomputed": 250000000.0}), "2.5 億円")
        self.assertEqual(RC.source_value_ja({"value": 1.0, "unit": "円", "recomputed": 12345.0}), "12,345 円")

    def test_rate_is_kept(self):
        self.assertEqual(RC.source_value_ja({"value": 26.2, "unit": "%", "recomputed": 36.22}), "36.22 %")
        self.assertEqual(RC.source_value_ja({"value": 1.0, "unit": "ポイント", "recomputed": 0.5}), "0.5 ポイント")

    def test_word_claim_is_yen(self):
        self.assertEqual(RC.source_value_ja({"value": None, "unit": None, "word": "増加", "recomputed": -569000000.0}), "-569,000,000 円")

    def test_none_is_dash(self):
        self.assertEqual(RC.source_value_ja({"recomputed": None}), "―")

    def test_difference_claim_in_million_yen_is_divided_too(self):
        # 差(formula:a-b)も engine は円で返す。文が百万円なら百万円に直る
        self.assertEqual(RC.source_value_ja({"value": 2624.0, "unit": "百万円", "recomputed": -2624000000.0}), "-2,624 百万円")

    def test_real_output_values_follow_the_claim_unit(self):
        out = _load(CASES[0])
        for c in out["claims"]:
            if c["state"] == "VALUE_MISMATCH" and c.get("unit") in RC.UNIT_SCALE and c.get("recomputed") is not None:
                s = RC.source_value_ja(c)
                self.assertTrue(s.endswith(" " + c["unit"]), (c["id"], s))


class SourceTest(unittest.TestCase):
    def test_period_words(self):
        self.assertEqual(RC.period_ja("CurrentYearDuration"), "当期")
        self.assertEqual(RC.period_ja("Prior1YearInstant"), "前期末")
        self.assertEqual(RC.period_ja("Prior1YearDuration_FooMember"), "前期")
        self.assertEqual(RC.split_context("Prior1YearDuration_FooMember"), ("前期", "FooMember"))
        self.assertEqual(RC.period_ja("Weird"), "Weird")

    def test_member_is_written_once_at_the_end(self):
        lab = {"jppfs_cor_Assets": "資産"}
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:Assets@CurrentYearInstant_NonConsolidatedMember",
                                       "xbrl:jppfs_cor:Assets@Prior1YearInstant_NonConsolidatedMember", "formula:a-b"], lab),
                         "資産 当期末 / 資産 前期末(当期末 − 前期末)[区分: 単体]")
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:Assets@CurrentYearInstant_FooMember"], lab), "資産 当期末[区分: FooMember]")

    def test_element_label_or_name(self):
        self.assertEqual(RC.element_ja("jppfs_cor:NetSales", {"jppfs_cor_NetSales": "売上高"}), "売上高")
        self.assertEqual(RC.element_ja("jppfs_cor:NetSales", {}), "jppfs_cor:NetSales")

    def test_formula_and_builtin(self):
        lab = {"jppfs_cor_Assets": "資産"}
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:Assets@CurrentYearInstant", "xbrl:jppfs_cor:Assets@Prior1YearInstant", "formula:a-b"], lab),
                         "資産 当期末 / 資産 前期末(当期末 − 前期末)")
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:Assets@CurrentYearInstant", "xbrl:jppfs_cor:Assets@Prior1YearInstant"], lab),
                         "資産 当期末 / 資産 前期末(前期比(当期末 ÷ 前期末 − 1))")
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:Assets@CurrentYearInstant", "builtin:unknown"], lab),
                         "資産 当期末(builtin:unknown)")
        self.assertEqual(RC.source_ja([], lab), "")

    def test_without_labels_the_element_name_stays(self):
        self.assertEqual(RC.source_ja(["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], {}), "jppfs_cor:NetSales 当期")

    def test_label_linkbase_is_parsed_from_bytes(self):
        xml = (u'<?xml version="1.0" encoding="UTF-8"?>'
               u'<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">'
               u'<link:labelLink>'
               u'<link:loc xlink:type="locator" xlink:href="x.xsd#jppfs_cor_NetSales" xlink:label="loc1"/>'
               u'<link:label xlink:label="lab1" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="ja">売上高</link:label>'
               u'<link:label xlink:label="lab2" xlink:role="http://www.xbrl.org/2003/role/verboseLabel" xml:lang="ja">長い売上高</link:label>'
               u'<link:labelArc xlink:from="loc1" xlink:to="lab1"/>'
               u'</link:labelLink></link:linkbase>').encode("utf-8")
        self.assertEqual(RC.parse_label_linkbase(xml), {"jppfs_cor_NetSales": "売上高"})
        self.assertEqual(RC.load_labels(None), {})


class MatchKindTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(RC.match_kind({"pointers": ["xbrl:a:B@CurrentYearDuration"]}), "当期")
        self.assertEqual(RC.match_kind({"pointers": ["xbrl:a:B@Prior1YearDuration"]}), "前期")
        self.assertEqual(RC.match_kind({"pointers": ["xbrl:a:B@CurrentYearDuration", "xbrl:a:B@Prior1YearDuration", "formula:a-b"]}), "計算")
        self.assertEqual(RC.match_kind({"pointers": []}), "その他")


class ImportBoundaryTest(unittest.TestCase):
    def test_module_imports_no_llm_no_network_no_engine(self):
        with io.open(os.path.join(_ROOT, "adapters", "xbrl", "report_customer.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                names.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom):
                names.add(("." * n.level) + (n.module or ""))
        # 段 2 で hashlib(sha256)・zipfile(書類自身のラベルと DEI)・decimal(桁の丸め)を足した。いずれも標準ライブラリで、通信・LLM・engine ではない。
        self.assertEqual(names, {"argparse", "hashlib", "io", "json", "os", "re", "sys", "unicodedata", "xml", "zipfile", "decimal", ".report"})
        for bad in ("urllib", "socket", "http", "requests", "anthropic", "openai", "subprocess"):
            self.assertNotIn(bad, names)


# ---------------------------------------------------------------------------------------------------------------
# 段 2(封 docs/XBRL_CUSTOMER_REPORT_FIX_SEAL_2026-10-21.md)
# ---------------------------------------------------------------------------------------------------------------

_HEX64 = re.compile(r"\b[0-9a-f]{64}\b")
JPIGP_LINE = "d45c95cc634202973557f5ed935d747ba25e751b7386c5269fe3e7bdb2c82d09  jpigp_2025-11-01_lab.xml"


def _linkbase(pairs):
    """``{loc の id: 日本語の標準ラベル}`` → ラベル linkbase の bytes。"""
    body = []
    for i, (k, v) in enumerate(sorted(pairs.items())):
        body.append(u'<link:loc xlink:type="locator" xlink:href="x.xsd#%s" xlink:label="loc%d"/>'
                    u'<link:label xlink:label="lab%d" xlink:role="http://www.xbrl.org/2003/role/label" xml:lang="ja">%s</link:label>'
                    u'<link:labelArc xlink:from="loc%d" xlink:to="lab%d"/>' % (k, i, i, v, i, i))
    return (u'<?xml version="1.0" encoding="UTF-8"?><link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" '
            u'xmlns:xlink="http://www.w3.org/1999/xlink"><link:labelLink>' + u"".join(body) + u'</link:labelLink></link:linkbase>').encode("utf-8")


def _sha(b):
    return hashlib.sha256(b).hexdigest()


class LegendTest(unittest.TestCase):
    LEGEND = u"出典の値は文の桁に丸めた数。括弧は丸める前の値。△ は負の数(財務諸表の書き方)"

    def test_the_approved_legend_is_in_the_differs_and_the_matches_sections_only(self):
        self.assertEqual(RC.LEGEND, self.LEGEND)
        for full in (False, True):
            md = RC.render_markdown(_units(), LABELS, full)
            self.assertEqual(md.count(self.LEGEND), 2)
            i1, i2, i3, i4 = md.index("## 1. 違う"), md.index("## 2. 要確認"), md.index("## 4. 一致"), md.index("\n---\n")
            self.assertEqual([md[i1:i2].count(self.LEGEND), md[i2:i3].count(self.LEGEND), md[i3:i4].count(self.LEGEND)], [1, 0, 1])

    def test_the_legend_is_there_even_when_the_section_is_empty(self):
        out = {"document": {"claims": 0}, "input": {}, "engine": {}, "claims": []}
        self.assertEqual(RC.render_markdown(out, None, False).count(self.LEGEND), 2)


class UnitsGoldenTest(unittest.TestCase):
    def test_units_input_matches_golden_bytes(self):
        self.assertEqual(RC.render_markdown(_units(), LABELS, True), UNITS_GOLDEN)

    def test_unit_of_the_sentence_is_kept_even_if_the_claim_unit_is_yen(self):
        md = RC.render_markdown(_units(), LABELS, False)
        self.assertIn("| N001 | 有形・無形固定資産の取得による支出112百万円及びその他 | 112百万円 | △111 百万円(△111.15) |", md)
        self.assertNotIn("112,000,000", md)

    def test_every_row_is_in_the_same_section_as_before(self):
        # 判定と節の割り当ては変えない(封 §1): section_of は state・reason だけで決まる(段 1 の試験 SectionOrderTest が表を縛る)
        got = {c["id"]: RC.section_of(c) for c in _units()["claims"]}
        self.assertEqual(got["N001"], "違う")
        self.assertEqual(got["N002"], "一致")
        self.assertEqual(got["N006"], "要確認")
        self.assertEqual(got["N007"], "対象外")
        self.assertEqual(got["T003"], "判断しない")


class FormatSourceTest(unittest.TestCase):
    def test_rounding_to_the_written_digits_with_the_raw_value_in_brackets(self):
        self.assertEqual(RC.format_source(61274000.0, "百万円", False, 0), "61 百万円(61.274)")
        self.assertEqual(RC.format_source(61274000.0, "百万円", False, 1), "61.3 百万円(61.274)")
        self.assertEqual(RC.format_source(61000000.0, "百万円", False, 0), "61 百万円")          # 丸めても同じなら括弧は付けない
        self.assertEqual(RC.format_source(40480000000.0, "百万円", False, 0), "40,480 百万円")

    def test_half_rounds_up_not_to_even(self):
        self.assertEqual(RC.format_source(2500000.0, "百万円", False, 0), "3 百万円(2.5)")
        self.assertEqual(RC.format_source(3500000.0, "百万円", False, 0), "4 百万円(3.5)")

    def test_negative_is_written_with_the_triangle(self):
        self.assertEqual(RC.format_source(-111150000.0, "百万円", False, 0), "△111 百万円(△111.15)")
        self.assertEqual(RC.format_source(-569000000.0, "円", False, 0), "△569,000,000 円")
        # 丸めて 0 になる負の数: 丸めた字には △ を付けず、括弧の生の値は負のまま
        self.assertEqual(RC.format_source(-300000.0, "百万円", False, 0), "0 百万円(△0.3)")

    def test_rate_is_rounded_to_the_digits_of_the_sentence(self):
        self.assertEqual(RC.format_source(36.22, "%", False, 1), "36.2 %(36.22)")
        self.assertEqual(RC.format_source(0.5, "ポイント", False, 1), "0.5 ポイント")

    def test_compound_written_form_and_carry(self):
        self.assertEqual(RC.format_source(2623000000.0, "百万円", True, 0), "26億23百万円")
        self.assertEqual(RC.format_source(2624123456.0, "百万円", True, 0), "26億24百万円(26億24.1235百万円)")
        self.assertEqual(RC.format_source(2699600000.0, "百万円", True, 0), "27億円(26億99.6百万円)")    # 百万円の位が繰り上がって億に

    def test_decimals_of_the_claim_value(self):
        self.assertEqual(RC.decimals_of(26.2), 1)
        self.assertEqual(RC.decimals_of(40539.0), 0)
        self.assertEqual(RC.decimals_of(0.05), 2)
        self.assertEqual(RC.decimals_of(1e22), 0)


class WrittenAmountTest(unittest.TestCase):
    def test_amounts_and_digits_in_the_sentence(self):
        a = RC.written_amounts("売上は26億23百万円で、1,234.5百万円、5千円")
        self.assertEqual([(x.text, x.unit, x.compound, x.decimals) for x in a],
                         [("26億23百万円", "百万円", True, 0), ("1,234.5百万円", "百万円", False, 1), ("5千円", "千円", False, 0)])
        self.assertEqual(a[0].yen, 2623000000.0)

    def test_bare_thousands_are_thousand_yen_not_a_kanji_form(self):
        # 監査の指摘: 「805千円」を漢数字形(805,000 円・単位 円)と読んでいた。N千円だけ(兆・億・万・百を伴わない)は千円。
        a = RC.written_amounts("支払は805千円、381千円")
        self.assertEqual([(x.text, x.unit, x.yen) for x in a], [("805千円", "千円", 805000.0), ("381千円", "千円", 381000.0)])
        # 従来どおり: 千・百の組み合わせは漢数字形
        a = RC.written_amounts("3千5百円と2千万円")
        self.assertEqual([(x.text, x.unit, x.yen) for x in a], [("3千5百円", "円", 3500.0), ("2千万円", "百万円", 20000000.0)])
        c = _claim("N", "売上高は381千円", 381.0, "千円", "VALUE_MISMATCH", None, [], 382000.0)
        self.assertEqual(RC.claim_value_written(c), "381千円")
        self.assertEqual(RC.source_value_report(c)[0], "382 千円")
        c = dict(c, value=381000.0, unit="円")
        self.assertEqual(RC.source_value_report(c)[0], "382 千円")

    def test_the_amount_equal_to_the_claim_value_is_chosen(self):
        c = _claim("N", "前年度比1,086百万円増の1,721百万円", 1721.0, "百万円", "GROUNDED", None, [], 1721000000.0)
        self.assertEqual(RC.written_amount_of(c).text, "1,721百万円")
        c2 = dict(c, value=1721000000.0, unit="円")
        self.assertEqual(RC.written_amount_of(c2).text, "1,721百万円")

    def test_no_matching_amount_is_unread_and_keeps_the_claim_unit(self):
        c = _claim("N", "利益が増えた", 100.0, "百万円", "VALUE_MISMATCH", None, [], 100400000.0)
        self.assertIsNone(RC.written_amount_of(c))
        self.assertEqual(RC.source_value_report(c), ("100 百万円(100.4)", "unread"))
        self.assertEqual(RC.claim_value_written(c), "100 百万円")

    def test_word_claim_takes_the_unit_of_the_nearest_amount_else_the_most_common_unit_of_the_document(self):
        c = _claim("T", "前年度末に比べ569百万円増加しました", None, None, "VALUE_MISMATCH", None, [], -569000000.0, word="増加")
        self.assertEqual(RC.source_value_report(c, "円"), ("△569 百万円", "word_span"))
        c = _claim("T", "売上高は増加しました", None, None, "VALUE_MISMATCH", None, [], -569000000.0, word="増加")
        self.assertEqual(RC.source_value_report(c, "円"), ("△569,000,000 円", "word_doc"))
        self.assertEqual(RC.source_value_report(c, "百万円"), ("△569 百万円", "word_doc"))

    def test_the_most_common_unit_with_ties_by_the_fixed_order(self):
        cl = [_claim("a", "10百万円", 10.0, "百万円", "GROUNDED", None, [], 1.0), _claim("b", "5千円", 5.0, "千円", "GROUNDED", None, [], 1.0)]
        self.assertEqual(RC.doc_unit_of(cl), "百万円")
        self.assertEqual(RC.doc_unit_of([]), "円")

    def test_non_numeric_or_missing_recomputed(self):
        self.assertEqual(RC.source_value_report({"recomputed": None})[0], "―")
        self.assertEqual(RC.source_value_report({"recomputed": None})[1], "none")

    def test_real_outputs_have_no_unit_mismatch_between_sentence_and_the_value_columns(self):
        for js in CASES:
            out = _load(js)
            du = RC.doc_unit_of(out["claims"])
            for c in out["claims"]:
                a = RC.written_amount_of(c)
                if a is None or c.get("recomputed") is None:
                    continue
                shown = RC.source_value_report(c, du)[0].split("(", 1)[0].strip()
                self.assertTrue(shown.endswith(a.unit) or (a.compound and shown.endswith("円")), (js, c["id"], shown, a.text))
                self.assertIn(RC.claim_value_written(c), unicodedata.normalize("NFKC", c["span"]))


class SignAndPreferTest(unittest.TestCase):
    def test_rate_sign_in_the_sentence_column_is_the_sentences_own_character(self):
        mk = lambda span, v: _claim("N", span, v, "%", "VALUE_MISMATCH", None, [], -66.0)
        self.assertEqual(RC.claim_value_written(mk("前期比△66.7%の減少", -66.7)), "△66.7 %")
        self.assertEqual(RC.claim_value_written(mk("前期比-66.7%の減少", -66.7)), "-66.7 %")
        self.assertEqual(RC.claim_value_written(mk("前期比▲66.7%の減少", -66.7)), "▲66.7 %")
        self.assertEqual(RC.claim_value_written(mk("前期比66.7%の減少", -66.7)), "66.7 %")        # 文に符号の字が無ければ付けない(エンジンの向きは文の字ではない)
        self.assertEqual(RC.claim_value_written(mk("前期比26.2%増", 26.2)), "26.2 %")
        self.assertEqual(RC.claim_value_written(mk("全く別の文", -66.7)), "-66.7 %")               # 同じ数の字が無ければ今までの字
        c = dict(mk("前期比△66.7%の減少", -66.7), recomputed=-66.74)
        self.assertEqual(RC.source_value_report(c), ("△66.7 %(△66.74)", "other"))

    def test_prefer_sentence_picks_half_up_or_truncation_whichever_equals_the_sentence(self):
        from decimal import Decimal
        F = RC.format_source
        self.assertEqual(F(40539600000.0, "百万円", False, 0), "40,540 百万円(40,539.6)")                       # 既定は四捨五入
        self.assertEqual(F(40539600000.0, "百万円", False, 0, Decimal(40539)), "40,539 百万円(40,539.6)")      # 切り捨てが文と同じ
        self.assertEqual(F(40539600000.0, "百万円", False, 0, Decimal(40540)), "40,540 百万円(40,539.6)")      # 四捨五入が文と同じ
        self.assertEqual(F(40539600000.0, "百万円", False, 0, Decimal(40000)), "40,540 百万円(40,539.6)")      # どちらも違えば四捨五入
        self.assertEqual(F(36.29, "%", False, 1, Decimal("36.2")), "36.2 %(36.29)")
        self.assertEqual(F(2699600000.0, "百万円", True, 0, Decimal(2699)), "26億99百万円(26億99.6百万円)")      # 複合の字でも切り捨て
        self.assertEqual(F(-40539600000.0, "百万円", False, 0, Decimal(40539)), "△40,539 百万円(△40,539.6)")

    def test_the_match_section_uses_the_sentence_side_rounding_and_the_differs_section_does_not(self):
        mk = lambda i, st: _claim(i, "売上高は40,539百万円", 40539.0, "百万円", st, None, ["xbrl:jppfs_cor:NetSales@CurrentYearDuration"], 40539600000.0)
        out = {"document": {"claims": 2}, "input": {}, "engine": {}, "claims": [mk("N001", "GROUNDED"), mk("N002", "VALUE_MISMATCH")]}
        md = RC.render_markdown(out, LABELS, True)
        self.assertIn("| N001 | 売上高は40,539百万円 | 40,539百万円 | 40,539 百万円(40,539.6) |", md)
        self.assertIn("| N002 | 売上高は40,539百万円 | 40,539百万円 | 40,540 百万円(40,539.6) |", md)
        self.assertEqual([c["state"] for c in out["claims"]], ["GROUNDED", "VALUE_MISMATCH"])        # 判定は変えない


class ExcerptTest(unittest.TestCase):
    def test_trailing_partial_number_is_dropped(self):
        T = RC.trim_partial_number
        self.assertEqual(T("る支出32,110百万円、有形・無形固定資産の取得による支出112百万円及びその他の支出が6"),
                         "る支出32,110百万円、有形・無形固定資産の取得による支出112百万円及びその他の支出が")
        self.assertEqual(T("貸与制度では2.9万件増加し、112"), "貸与制度では2.9万件増加し、")
        self.assertEqual(T("この結果、1株当たり当期純利益は6"), "この結果、1株当たり当期純利益は")

    def test_leading_partial_number_is_dropped_only_when_it_starts_with_a_point(self):
        T = RC.trim_partial_number
        self.assertEqual(T(".2ポイント増、中期経営計画の目標値であった8.6%と比べて1.3ポイン"), "ポイント増、中期経営計画の目標値であった8.6%と比べて1.3ポイン")
        self.assertEqual(T("2026年3月時点で"), "2026年3月時点で")        # 先頭の数は桁の途中かどうか見分けられないので落とさない(限界)
        self.assertEqual(T("180店舗"), "180店舗")

    def test_a_complete_number_is_kept_and_an_empty_result_falls_back(self):
        T = RC.trim_partial_number
        self.assertEqual(T("営業収益は26億23百万円"), "営業収益は26億23百万円")
        self.assertEqual(T("123"), "123")
        self.assertEqual(T(""), "")
        self.assertEqual(T(None), "")

    def test_only_the_not_judged_and_out_of_scope_bullets_are_trimmed(self):
        md = RC.render_markdown(_units(), LABELS, False)
        self.assertIn("- N008: る支出32,110百万円、取得による支出が(", md)
        self.assertNotIn("支出が6", md)
        # 「違う」「要確認」の抜粋は engine の出したまま
        out = _units()
        out["claims"][5]["span"] = "売上高は7百万円のうち6"
        self.assertIn("| N006 | 売上高は7百万円のうち6 |", RC.render_markdown(out, LABELS, False))


class RosterTest(unittest.TestCase):
    """名簿(``taxonomy_labels_sha256.txt``)に在る file 名だけを、sha256 が合うときだけ読む(封 §1-1・R2-5)。"""

    def _dir(self):
        d = tempfile.mkdtemp(prefix="roster_")
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        return d

    def _put(self, d, name, data):
        with open(os.path.join(d, name), "wb") as f:
            f.write(data)

    def test_the_repo_roster_lists_the_three_files_with_the_sealed_jpigp_line(self):
        self.assertTrue(os.path.exists(RC.ROSTER_PATH))
        r = RC.load_roster()
        self.assertEqual(sorted(r), ["jpcrp_2025-11-01_lab.xml", "jpigp_2025-11-01_lab.xml", "jppfs_2025-11-01_lab.xml"])
        self.assertEqual("%s  %s" % (r["jpigp_2025-11-01_lab.xml"], "jpigp_2025-11-01_lab.xml"), JPIGP_LINE)
        with io.open(RC.ROSTER_PATH, encoding="utf-8") as f:
            self.assertIn(JPIGP_LINE, f.read().splitlines())

    def test_roster_parser_skips_comments_and_blank_lines_and_a_missing_file_is_empty(self):
        d = self._dir()
        p = os.path.join(d, "r.txt")
        with io.open(p, "w", encoding="utf-8") as f:
            f.write("# c\n\n%s  a_lab.xml\n" % ("A" * 64))
        self.assertEqual(RC.load_roster(p), {"a_lab.xml": "a" * 64})
        self.assertEqual(RC.load_roster(os.path.join(d, "nope.txt")), {})

    def test_only_roster_files_are_read_and_a_file_outside_the_roster_changes_nothing(self):
        d = self._dir()
        good = _linkbase({"jppfs_cor_NetSales": u"売上高"})
        self._put(d, "a_lab.xml", good)
        roster = {"a_lab.xml": _sha(good)}
        base_labels, base_meta = RC.load_labels_with_meta(d, None, roster)
        self.assertEqual(base_labels, {"jppfs_cor_NetSales": u"売上高"})
        self.assertEqual(base_meta, [{"file": "a_lab.xml", "sha256": _sha(good), "status": "used"}])
        # 名簿の外の file(別の label を持つ)を置く
        self._put(d, "zz_extra_lab.xml", _linkbase({"jppfs_cor_NetSales": u"名簿の外", "jppfs_cor_Assets": u"資産"}))
        self._put(d, "a_lab.xml.orig", b"not xml")
        labels, meta = RC.load_labels_with_meta(d, None, roster)
        self.assertEqual((labels, meta), (base_labels, base_meta))
        out = _small()
        self.assertEqual(RC.render_markdown(out, labels, True), RC.render_markdown(out, base_labels, True))
        self.assertEqual(RC.load_labels(d, roster), base_labels)

    def test_a_file_with_a_wrong_sha256_is_not_used_and_is_recorded(self):
        d = self._dir()
        good = _linkbase({"jppfs_cor_NetSales": u"売上高"})
        self._put(d, "a_lab.xml", good + b" ")           # 1 byte 違う
        labels, meta = RC.load_labels_with_meta(d, None, {"a_lab.xml": _sha(good)})
        self.assertEqual(labels, {})
        self.assertEqual(meta, [{"file": "a_lab.xml", "sha256": _sha(good + b" "), "status": "sha256_mismatch"}])

    def test_a_missing_roster_file_is_recorded_as_missing(self):
        d = self._dir()
        labels, meta = RC.load_labels_with_meta(d, None, {"a_lab.xml": "0" * 64})
        self.assertEqual((labels, meta), ({}, [{"file": "a_lab.xml", "sha256": None, "status": "missing"}]))

    def test_no_directory_means_no_labels_and_no_meta(self):
        self.assertEqual(RC.load_labels_with_meta(None, None, {"a": "0" * 64}), ({}, []))
        self.assertEqual(RC.load_labels(os.path.join(self._dir(), "nope")), {})

    def test_the_real_cache_folder_gives_three_used_files(self):
        d = os.path.join(os.path.expanduser("~"), ".cache", "audit-core", "edinet-taxonomy", "2025-11-01")
        if not all(os.path.exists(os.path.join(d, n)) for n in RC.load_roster()):
            self.skipTest(u"標準ラベルの 3 file がこの機械に無い(fixtures/xbrl/TAXONOMY_LABELS_README.md)")
        labels, meta = RC.load_labels_with_meta(d, None)
        self.assertEqual([m["status"] for m in meta], ["used", "used", "used"])
        self.assertEqual(labels["jppfs_cor_NetSales"], "売上高")
        self.assertTrue(any(k.startswith("jpigp_cor_") for k in labels))


def _make_zip(path, dei=None, lab=None, extra_pub=None, title=None):
    """書類の ZIP に見立てた小さな ZIP。``dei`` は DEI の要素(局所名 → 値)、``lab`` は書類自身のラベル。"""
    inst = [u'<?xml version="1.0" encoding="UTF-8"?><xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:jpdei_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jpdei/2025-11-01/jpdei_cor">']
    for k, v in sorted((dei or {}).items()):
        inst.append(u'<jpdei_cor:%s contextRef="FilingDateInstant">%s</jpdei_cor:%s>' % (k, v, k))
    if title is not None:
        inst.append(u'<jpcrp_cor:DocumentTitleCoverPage xmlns:jpcrp_cor="http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/2025-11-01/jpcrp_cor" contextRef="FilingDateInstant">%s</jpcrp_cor:DocumentTitleCoverPage>' % title)
    inst.append(u"</xbrli:xbrl>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E00000-000_2026-03-31.xbrl", u"".join(inst).encode("utf-8"))
        if lab is not None:
            z.writestr("XBRL/PublicDoc/jpcrp030000-asr-001_E00000-000_2026-03-31_lab.xml", _linkbase(lab))
        for name, data in (extra_pub or {}).items():
            z.writestr(name, data)


DEI_OK = {"FilerNameInJapaneseDEI": u"テスト株式会社", "DocumentTypeDEI": u"第三号様式", "CurrentPeriodEndDateDEI": "2026-03-31", "CurrentFiscalYearEndDateDEI": "2026-03-31"}


class ZipLabelsAndTitleTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="zip_")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.d, ignore_errors=True))

    def test_company_element_and_member_are_read_from_the_documents_own_labels(self):
        z = os.path.join(self.d, "d.zip")
        _make_zip(z, DEI_OK, {"jpcrp030000-asr_E00000-000_FooProfit": u"ファーム利益", "jpcrp030000-asr_E00000-000_BarSegmentMember": u"介護事業 [メンバー]"})
        labels, meta = RC.load_labels_with_meta(None, z)
        self.assertEqual(labels["jpcrp030000-asr_E00000-000_FooProfit"], u"ファーム利益")
        self.assertEqual(labels["member:jpcrp030000-asr_E00000-000BarSegmentMember"], u"介護事業")      # 「 [メンバー]」は落とす
        self.assertEqual([m["file"] for m in meta], ["zip:jpcrp030000-asr-001_E00000-000_2026-03-31_lab.xml"])
        txt = RC.source_ja(["xbrl:jpcrp030000-asr_E00000-000:FooProfit@CurrentYearDuration_jpcrp030000-asr_E00000-000BarSegmentMember"], labels)
        self.assertEqual(txt, u"ファーム利益 当期[区分: 介護事業]")
        self.assertEqual(RC.unresolved_names(["xbrl:jpcrp030000-asr_E00000-000:FooProfit@CurrentYearDuration_jpcrp030000-asr_E00000-000BarSegmentMember"], labels), [])

    def test_unresolved_names_lists_the_names_that_stay_in_roman_letters(self):
        ptr = ["xbrl:jpcrp030000-asr_E00000-000:FooProfit@CurrentYearDuration_jpcrp030000-asr_E00000-000BarSegmentMember", "formula:a-b"]
        self.assertEqual(RC.unresolved_names(ptr, {}), ["jpcrp030000-asr_E00000-000:FooProfit", "jpcrp030000-asr_E00000-000BarSegmentMember"])
        self.assertEqual(RC.unresolved_names(["xbrl:jppfs_cor:Assets@CurrentYearInstant_NonConsolidatedMember"], {"jppfs_cor_Assets": u"資産"}), [])
        self.assertEqual(RC.unresolved_names(None, {}), [])

    def test_standard_label_wins_over_the_documents_label_for_the_same_key(self):
        z = os.path.join(self.d, "d.zip")
        _make_zip(z, DEI_OK, {"jppfs_cor_NetSales": u"書類の売上"})
        std = os.path.join(self.d, "std")
        os.makedirs(std)
        good = _linkbase({"jppfs_cor_NetSales": u"売上高"})
        with open(os.path.join(std, "a_lab.xml"), "wb") as f:
            f.write(good)
        labels, _meta = RC.load_labels_with_meta(std, z, {"a_lab.xml": _sha(good)})
        self.assertEqual(labels["jppfs_cor_NetSales"], u"売上高")

    def test_dei_gives_filer_doctype_and_period_end_and_the_title(self):
        z = os.path.join(self.d, "d.zip")
        _make_zip(z, DEI_OK)
        dei = RC.dei_from_zip(z)
        self.assertEqual(dei, {"filer": u"テスト株式会社", "doctype": u"第三号様式", "period_end": "2026-03-31"})
        md = RC.render_markdown(_small(), LABELS, False, dei)
        self.assertEqual(md.split("\n", 1)[0], u"# テスト株式会社 第三号様式(2026-03-31)の数の点検")

    def test_doctype_is_the_document_title_and_falls_back_to_the_dei_form_name(self):
        z = os.path.join(self.d, "t.zip")
        _make_zip(z, DEI_OK, title=u"有価証券報告書")
        dei = RC.dei_from_zip(z)
        self.assertEqual(dei["doctype"], u"有価証券報告書")
        md = RC.render_markdown(_small(), LABELS, False, dei)
        self.assertEqual(md.split("\n", 1)[0], u"# テスト株式会社 有価証券報告書(2026-03-31)の数の点検")
        # 題名が空の要素のあとに本物が在っても、空でない最初のものを取る
        z2 = os.path.join(self.d, "t2.zip")
        _make_zip(z2, DEI_OK, title=u"有価証券報告書")
        with zipfile.ZipFile(z2) as zz:
            name = [n for n in zz.namelist() if n.endswith(".xbrl")][0]
            data = zz.read(name).decode("utf-8").replace(u"<jpcrp_cor:DocumentTitleCoverPage", u'<jpcrp_cor:DocumentTitleCoverPage xmlns:jpcrp_cor="http://x/jpcrp_cor"> </jpcrp_cor:DocumentTitleCoverPage><jpcrp_cor:DocumentTitleCoverPage', 1)
        z3 = os.path.join(self.d, "t3.zip")
        with zipfile.ZipFile(z3, "w") as zo:
            zo.writestr(name, data.encode("utf-8"))
        self.assertEqual(RC.dei_from_zip(z3)["doctype"], u"有価証券報告書")
        # 題名が無ければ DEI の様式名
        z4 = os.path.join(self.d, "t4.zip")
        _make_zip(z4, DEI_OK)
        self.assertEqual(RC.dei_from_zip(z4)["doctype"], u"第三号様式")

    def test_period_end_falls_back_to_the_fiscal_year_end(self):
        z = os.path.join(self.d, "d.zip")
        _make_zip(z, {"FilerNameInJapaneseDEI": u"甲", "DocumentTypeDEI": u"第三号様式", "CurrentFiscalYearEndDateDEI": "2026-06-30"})
        self.assertEqual(RC.dei_from_zip(z)["period_end"], "2026-06-30")

    def test_without_dei_or_with_a_partial_dei_the_title_is_the_old_one(self):
        old = u"# 文章と出典(XBRL)の照合 ― (書類)"
        self.assertEqual(RC.render_markdown(_small(), LABELS, False).split("\n", 1)[0], old)
        self.assertEqual(RC.render_markdown(_small(), LABELS, False, None).split("\n", 1)[0], old)
        for dei in ({"filer": u"甲", "doctype": None, "period_end": "2026-03-31"}, {"filer": None, "doctype": u"x", "period_end": "2026-03-31"},
                    {"filer": u"甲", "doctype": u"x", "period_end": None}, {}):
            self.assertEqual(RC.render_markdown(_small(), LABELS, False, dei).split("\n", 1)[0], old)
        z = os.path.join(self.d, "e.zip")
        _make_zip(z, {})
        self.assertEqual(RC.dei_from_zip(z), {"filer": None, "doctype": None, "period_end": None})


class ProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prov_")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.d, ignore_errors=True))

    def test_the_body_has_no_sha256_and_no_fingerprint_and_ends_with_the_one_line(self):
        for js in CASES:
            out = _load(js)
            self.assertTrue(out["input"]["zip_sha256"] and out["engine"])             # 入力に指紋は在る(本文に出ないことを見る)
            for full in (False, True):
                md = RC.render_markdown(out, None, full)
                self.assertEqual(_HEX64.findall(md), [], js)
                for w in (out["input"]["zip_sha256"], out["engine"].get("git_commit") or "x" * 8, "engine の指紋", "profile:"):
                    self.assertNotIn(w, md)
                tail = md.split("\n---\n", 1)[1]
                self.assertEqual(tail, u"\n<sub>書類の指紋・道具の版・照合した文章の指紋は、同じ名前の `.provenance.json`(機械用)に置いた。</sub>\n")

    def test_provenance_carries_the_fingerprints_and_the_body_sha256(self):
        out = _load(CASES[0])
        md = RC.render_markdown(out, None, False)
        meta = [{"file": "b", "sha256": "1" * 64, "status": "used"}, {"file": "a", "sha256": None, "status": "missing"}]
        pv = RC.render_provenance(out, md, meta, {"filer": u"甲"}, "2" * 64)
        rec = json.loads(pv)
        self.assertEqual(rec["report"]["body_sha256"], hashlib.sha256(md.encode("utf-8")).hexdigest())
        self.assertEqual(rec["input"]["zip_sha256"], out["input"]["zip_sha256"])
        self.assertEqual(rec["engine"], out["engine"])
        self.assertEqual((rec["profile"], rec["tool"]), (out["profile"], out["tool"]))
        self.assertEqual([m["file"] for m in rec["labels"]], ["a", "b"])                 # file 名順
        self.assertEqual(rec["zip_given"], {"sha256": "2" * 64, "same_as_input": False})
        self.assertTrue(pv.endswith("\n"))
        # key は並ぶ(sort_keys)・時刻を入れない
        self.assertEqual(pv, json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        self.assertNotIn("time", json.dumps(rec).lower())

    def test_same_input_gives_the_same_bytes_for_the_body_and_the_json(self):
        out = _load(CASES[1])
        a = RC.render_markdown(out, None, False)
        b = RC.render_markdown(json.loads(json.dumps(out)), None, False)
        self.assertEqual(RC.render_provenance(out, a, [], None, None), RC.render_provenance(json.loads(json.dumps(out)), b, [], None, None))
        # 本文が変われば json の body_sha256 も変わる
        out3 = json.loads(json.dumps(out))
        out3["claims"][0]["state"] = "VALUE_MISMATCH" if out3["claims"][0]["state"] != "VALUE_MISMATCH" else "GROUNDED"
        c = RC.render_markdown(out3, None, False)
        self.assertNotEqual(json.loads(RC.render_provenance(out3, c, [], None, None))["report"]["body_sha256"],
                            json.loads(RC.render_provenance(out, a, [], None, None))["report"]["body_sha256"])

    def test_cli_writes_the_body_and_the_provenance_next_to_it_with_the_same_bytes_twice(self):
        src = os.path.join(self.d, "in.json")
        out = _load(CASES[0])
        with io.open(src, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        z = os.path.join(self.d, "d.zip")
        _make_zip(z, DEI_OK, {"jpcrp030000-asr_E00000-000_Foo": u"ふー"})
        got = []
        for i in (1, 2):
            dst = os.path.join(self.d, "r%d.report.md" % i)
            r = subprocess.run([sys.executable, "-m", "adapters.xbrl.report_customer", "--in", src, "--out", dst, "--zip", z, "--full"],
                               cwd=_ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            pvp = os.path.join(self.d, "r%d.report.provenance.json" % i)           # 拡張子 .md を除いた名前 + .provenance.json
            self.assertTrue(os.path.exists(pvp), os.listdir(self.d))
            with open(dst, "rb") as f1, open(pvp, "rb") as f2:
                got.append((f1.read(), f2.read()))
        self.assertEqual(got[0], got[1])
        body, pv = got[0]
        md = body.decode("utf-8")
        rec = json.loads(pv.decode("utf-8"))
        self.assertEqual(rec["report"]["body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(md.split("\n", 1)[0], u"# テスト株式会社 第三号様式(2026-03-31)の数の点検")
        self.assertEqual(_HEX64.findall(md), [])
        self.assertEqual(rec["zip_given"]["sha256"], hashlib.sha256(open(z, "rb").read()).hexdigest())
        self.assertEqual(rec["title"]["filer"], u"テスト株式会社")
        self.assertTrue(any(m["file"].startswith("zip:") for m in rec["labels"]))
        # 関数と同じ字
        self.assertEqual(md, RC.render_markdown(out, RC.load_labels_with_meta(None, z)[0], True, RC.dei_from_zip(z)))

    def test_provenance_path_drops_the_extension(self):
        self.assertEqual(RC.provenance_path("/a/b/report.md"), "/a/b/report.provenance.json")
        self.assertEqual(RC.provenance_path("/a/b/report"), "/a/b/report.provenance.json")

    def test_label_files_outside_the_roster_do_not_enter_the_provenance(self):
        d = tempfile.mkdtemp(prefix="provlab_")
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        good = _linkbase({"jppfs_cor_NetSales": u"売上高"})
        for n, data in (("a_lab.xml", good), ("zz_lab.xml", b"x")):
            with open(os.path.join(d, n), "wb") as f:
                f.write(data)
        _labels, meta = RC.load_labels_with_meta(d, None, {"a_lab.xml": _sha(good)})
        self.assertEqual([m["file"] for m in meta], ["a_lab.xml"])


if __name__ == "__main__":
    unittest.main()
