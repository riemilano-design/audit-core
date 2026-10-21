# -*- coding: utf-8 -*-
"""顧客向け報告(``adapters/xbrl/report_customer.py``)の試験。封 ``docs/XBRL_CUSTOMER_REPORT_SEAL_2026-10-21.md``。

留めるもの: (1) golden ― 手で書いた小さな入力の報告をバイト列で字のまま(全節・other_frame・no_same_value・表に無い reason を含む)と、
実出力 2 件の報告の sha256、(2) 網羅(C-3)― 理由の日本語表は登録簿の理由の全部(16)と同じ集合で、1 つ消すと網羅の検査が赤になる、
(3) 単位 ― 百万円の文は百万円、千円の文は千円、率は率、語の主張は円、(4) 節の順と各節の中身、(5) other_frame と no_same_value の 1 行は
封の字のまま「要確認」に在る、(6) 同じ入力から同じバイト列(C-4)・CLI も同じ、(7) 判定を足さず変えない(全 claim が 1 回ずつ、state・reason で決まる節にだけ)、
(8) LLM・通信を import しない。
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
import unittest

from adapters.xbrl import recipes as R
from adapters.xbrl import registry_setup as RS
from adapters.xbrl import report_customer as RC

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FIX = os.path.join(_ROOT, "fixtures", "xbrl")
CASES = ("entry_output_S100Z4N9_original_2026-10-13.json", "entry_output_S100Z4Q1_ai_prose_2026-10-13.json")
# 実出力 2 件の報告(ラベル無し)の sha256。記法を変えたら必ず赤くなる。(既定 = 行なし / --full = 一致の行も)
GOLDEN_SHA256 = {
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
| 違う | 3 | 出典に当たる値があり、文の値と**違う** |
| 要確認 | 3 | 道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる |
| 対象外 | 1 | 出典(XBRL)にその数は無い(株数・人数など) |
| 判断しない | 1 | 主語が無い・目標や計画・区分が決まらない。道具は判断しない |
| 一致 | 1 | 出典の値と一致した |
| 合計 | 9 | |

## 1. 違う ― 3 件

出典に当たる値は見つかったが、文の値と違う。文の誤りか、当てた出典の誤りかは、この表では決めない。「出典の値」は文と同じ単位に直してある。

| # | 文の抜粋 | 文の値 | 出典の値 | 出典 |
|---|---|---|---|---|
| N001 | 売上高は40,539百万円 | 40,539 百万円 | 40,480 百万円 | 売上高 当期 |
| N002 | 前期比26.2%増 | 26.2 % | 36.22 % | 売上高 当期 / 売上高 前期(前期比(当期 ÷ 前期 − 1)) |
| N003 | 総資産は53,812千円 | 53,812 千円 | 53,812,000 千円 | 資産 当期末 |

## 2. 要確認 ― 3 件

道具が文を出典の 1 つの値に結べなかった。理由の列を見て人が確かめる。

| # | 文の抜粋 | 文の値 | 理由 |
|---|---|---|---|
| N005 | 営業利益は3百万円 | 3 百万円 | 出典の当期の数と合わず、同じ数も桁違いの数もこの項目に無い。参照先を確かめる |
| N006 | 売上高は7百万円 | 7 百万円 | 同じ項目の別の区分(セグメント・単体等)の数と合う。どの区分の数かを確かめる |
| T002 | 減少した | 減少 | something(new) |

## 3. 対象外 ― 1 件 / 判断しない ― 1 件

対象外: 出典(XBRL)にその数は無い(株数・人数・区分ごとの前期の数など)。判断しない: 主語が無い・目標や計画の数・区分が 1 つに決まらない文。道具は判断しない。

### 対象外 ― 1 件

- N007: 従業員は10名(文の単位(株・名・件 など)の数は出典(XBRL)に無い)

### 判断しない ― 1 件

- T001: 増加した(文に主語(どの項目の数か)が無い)

## 4. 一致 ― 1 件

文の値と出典の値が一致した。出典の内訳: 当期 0 件 / 前期 1 件 / 計算 0 件。

(行は `--full` で出す)

---

<sub>書類: </sub>  
<sub>入力 ZIP の sha256: ( bytes)</sub>  
<sub>照合した文章: 書類の原文</sub>  
<sub>engine の指紋: adapters  / core  / git </sub>  
<sub>profile:  / 道具: </sub>
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
        reg = registry_reasons()
        self.assertEqual(len(reg), 16)
        self.assertEqual(reg, set(R.UNBOUND_REASON_STATE) | {"other_frame", "no_same_value"})

    def test_reason_table_is_exactly_the_registry(self):
        self.assertEqual(uncovered(RC.REASON_JA), [])
        self.assertEqual(sorted(set(RC.REASON_JA) - registry_reasons()), [])
        self.assertEqual(len(RC.REASON_JA), 16)

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
        self.assertEqual(names, {"argparse", "io", "json", "os", "re", "sys", "unicodedata", "xml", ".report"})
        for bad in ("urllib", "socket", "http", "requests", "anthropic", "openai", "subprocess"):
            self.assertNotIn(bad, names)


if __name__ == "__main__":
    unittest.main()
