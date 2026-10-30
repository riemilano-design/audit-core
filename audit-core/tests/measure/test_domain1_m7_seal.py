# -*- coding: utf-8 -*-
"""段 7 の封(docs/DOMAIN1_M7_SEAL_2026-10-15.md)を固定する。**実装より先に赤くなる門。**

守るのは 6 つ。
  1. 規則 P-1〜P-7 の字(とくに **P-5 = 親の無い行を既定にしない**)
  2. 人間が求めた 5 つの数(N-1〜N-5)が別々に在ること
  3. 合格線が段 6 と同じで、**E2 = 0 件**と**増分の 2 本**が在ること
  4. 問いを変えないこと(`SPEC` version と問いの sha256 を字で留める)
  5. 診断の予測 D-1〜D-7 が**外れうる粒度**で書かれていること
  6. ①と②③を混ぜないこと・汎化を主張しないこと
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M7_SEAL_2026-10-15.md")
M6MAT = os.path.join(ROOT, "fixtures", "sheet", "m6_label_material_2026-10-15.json")
M6BINDS = os.path.join(ROOT, "fixtures", "sheet", "m6_binds_2026-10-15.json")
ENGINE = os.path.join(ROOT, "measure", "sheet_m5_engine_2026-10-15.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def section(name):
    """封の節を切り出す(節の外の文字で門をごまかせないようにする)。"""
    t = text(SEAL)
    i = t.index(name)
    j = t.find("\n## ", i + 1)
    return t[i:(j if j > 0 else len(t))]


class RuleTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 2. 規則")

    def test_all_seven_rules_are_present(self):
        for k in ("P-1", "P-2", "P-3", "P-4", "P-5", "P-6", "P-7"):
            self.assertIn("### %s " % k, self.s, k)

    def test_p1_says_the_parent_is_a_filter_not_an_answer(self):
        self.assertIn("engine は**親の文字列を答えとして採用しない。**", self.s)
        self.assertIn("**文から親の名前を合成しない。**", self.s)

    def test_p3_forbids_carrying_the_cue_over(self):
        self.assertIn("**区間に名前が無ければ `C` は空とし、前の金額の手がかりを"
                      "使い回さない**", self.s)

    def test_p3_refuses_the_whole_sentence_alternative_and_says_why(self):
        self.assertIn("**採らない。**", self.s)
        self.assertIn("**材料に害が無いことを規則の根拠にしない。**", self.s)

    def test_p4_requires_every_component(self):
        self.assertIn("その成分(`款名` または `款名 > 項名`)が**全部** `C` に在る", self.s)
        self.assertIn("**1 つだけ在る候補は支持されていない。**", self.s)

    def test_p5_does_not_make_parentless_rows_the_default(self):
        """**ここが ① と ② を分ける線。**消えたら赤。"""
        self.assertIn("**支持された候補が 1 つも無ければ、絞らない**", self.s)
        self.assertIn("款と項の双子は**保留のまま**にし、②で別に扱う。", self.s)
        self.assertIn("**1 本の報告文の 2 席の答えを規約として採用しない。**", self.s)

    def test_p6_never_picks_by_value(self):
        self.assertIn("**値で 1 件に絞ることは絶対にしない**", self.s)
        self.assertIn("6 欄が 1 通りでなければ保留", self.s)

    def test_p7_records_the_parent_facts_even_when_not_bound(self):
        self.assertIn("**接続できたかに関係なく記録する**", self.s)
        for f in ("parent_cues", "parent_filtered", "parent_kept",
                  "parent_before", "parent_after"):
            self.assertIn("`%s`" % f, self.s)


class FiveCountsTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 3. 数えるもの")

    def test_the_five_counts_the_human_asked_for(self):
        want = ("N-1 親を正しく抽出できた件数", "N-2 親を誤って抽出した件数",
                "N-3 正しく接続できた件数", "N-4 誤接続した件数",
                "N-5 根拠不足として保留した件数")
        for k in want:
            self.assertIn("**%s**" % k, self.s, k)

    def test_extracting_the_parent_is_not_evidence_of_binding(self):
        self.assertIn("**N-1 と N-3 は別の数である。**", self.s)
        self.assertIn("**「親が正しく取れた」ことを「接続できた」ことの証拠にしない。**", self.s)

    def test_an_empty_denominator_is_unmeasured_not_a_pass(self):
        self.assertIn("**分母が 0 のとき `合格` と書かない。`未測定` と書く**", self.s)
        self.assertIn("**報告文が親を 1 度も書かなければ、この段の主目的は `未測定` である。**",
                      self.s)


class GateLineTest(unittest.TestCase):
    def test_the_five_sealed_lines_are_unchanged_from_stage_6(self):
        s = section("## 5. 合格線")
        for line in ("| G-1 接続の正確さ | ≥ 50% |", "| G-2 誤接続 | = 0 件 |",
                     "| G-3 根拠なしの接続 | = 0 件 |", "| G-5 母数 | ≥ 20 件 |"):
            self.assertIn(line, s)
        self.assertIn("| G-4 保留の適切さ | ≥ 80%(分母が 0 なら `未測定`) |", s)

    def test_the_main_metric_is_e2_zero(self):
        s = section("## 5. 合格線")
        self.assertIn("**主指標は E2 = 0 件。**", s)
        self.assertIn("**誤接続ゼロを緩めない。**", section("## 6. やらないこと"))

    def test_the_increment_is_measured_on_one_report_with_two_engines(self):
        s = section("## 4. 増えたかどうか")
        self.assertIn("G-1 を**別の標本の間で比べない**", s)
        self.assertIn("**旧 engine", s)
        self.assertIn("1 byte も変えない", s)
        self.assertIn("| **G-7 正しい接続の増分** | **≥ 1 件**(新 − 旧) |", s)
        self.assertIn("| **G-8 誤受理の増分** | **= 0 件**。新 engine の E2 自体も **0 件** |", s)
        self.assertIn("**良い方を選ばない。**", s)

    def test_the_failure_conditions_name_every_line(self):
        s = section("## 5. 合格線")
        for k in ("G-1 < 50%", "**E2 ≥ 1 件**", "G-3 ≥ 1 件", "**G-7 < 1 件**",
                  "**G-8 ≥ 1 件**"):
            self.assertIn(k, s, k)


class QuestionIsUnchangedTest(unittest.TestCase):
    """**正解の定義を動かさずに engine だけを変える**ことを、字と sha で留める。"""

    def test_the_seal_pins_the_stage_6_question_hash(self):
        mat = json.load(io.open(M6MAT, encoding="utf-8"))
        q = mat["question"]
        sha = hashlib.sha256(q.encode("utf-8")).hexdigest()
        s = section("## 5. 合格線")
        self.assertIn(sha[:16], s, "問いの sha が封に無い")
        self.assertIn(mat["spec_version"], s)
        self.assertIn("{:,} 字".format(len(q)), s)
        self.assertIn("**問いは段 6 と 1 文字も変えない**", s)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 7. 段 6 の 25 件への予測")

    def test_it_is_marked_diagnostic_only(self):
        self.assertIn("**診断用。合否には使わない**", self.s)
        self.assertIn("**ここで当たっても段 6 の合否は動かない。**", self.s)

    def test_all_seven_numbered_predictions_exist(self):
        for k in ("D-1", "D-2", "D-3", "D-4", "D-5", "D-6", "D-7"):
            self.assertRegex(self.s, r"\| %s \| " % k)

    def test_the_prediction_is_specific_enough_to_fail(self):
        self.assertIn("状態が変わる主張は **1 件だけ**", self.s)
        self.assertIn("**14/25(56.0%)**", self.s)
        self.assertIn("親で絞った主張 **4 件**", self.s)

    def test_every_one_of_the_25_rows_is_accounted_for(self):
        """群の件数の合計が **25** であること(読み落とした行を作らない)。"""
        rows = re.findall(r"^\| (?!記号|群|---|D-)[^|]+\| (\d+) \|", self.s, re.M)
        self.assertTrue(rows, "群の表が読めない")
        self.assertEqual(sum(int(x) for x in rows), 25,
                         "群の件数の合計が 25 でない: %s" % rows)

    def test_the_regression_line_is_in_the_prediction(self):
        self.assertIn("**段 6 で接続できた 13 件は 1 件も壊れない**", self.s)
        b = json.load(io.open(M6BINDS, encoding="utf-8"))
        self.assertEqual(b["counts"]["split"]["接続数"], 13)

    def test_the_seal_discloses_that_i_already_read_these_sentences(self):
        self.assertIn("私は段 6 の 25 件の文を既に読んでいる。", self.s)
        self.assertIn("**性能の評価は、新しい報告文だけで行う**", self.s)


class ScopeTest(unittest.TestCase):
    def test_the_seal_keeps_2_and_3_out_of_this_experiment(self):
        s = section("## 6. やらないこと")
        self.assertIn("**階層の手がかりを 1 文の中で引き継がない**(②)", s)
        self.assertIn("**別名の扱いを変えない**(③)", s)

    def test_the_seal_refuses_generalisation(self):
        s = section("## 6. やらないこと")
        self.assertIn("**他の自治体・他の年度・一般の会計資料に通じるとは結論しない**", s)

    def test_the_seal_refuses_to_rescore_stage_6(self):
        s = section("## 6. やらないこと")
        self.assertIn("**段 6 の報告文で再採点して合格にしない。**", s)

    def test_the_order_puts_the_seal_before_the_implementation(self):
        s = section("## 8. 順序")
        self.assertIn("**この封を commit する(実装より先)。**", s)
        self.assertIn("**新しい file に書き、旧 engine は 1 byte も変えない。**", s)
        self.assertIn("ここで**人間の判断を仰ぐ。**", s)

    def test_the_old_engine_is_still_byte_identical_to_stage_5(self):
        """封が「1 byte も変えない」と書いた相手が、まだ段 5 のままであること。"""
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out, "旧 engine が段 6 以降で変更されている: %s" % out)


class IndexFactsTest(unittest.TestCase):
    """§1 の数は**索引から測ったもの**。索引が変わったら赤くする。"""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("m5_for_seal7", ENGINE)
        self.E = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.E)
        M2 = self.E.M2
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        raw = self.E.fix_total_level(self.E.build_index(
            M2.parse_soukatu(books[M2.SOUKATU]), M2.parse_kessan(books[M2.KESSAN]),
            M2.parse_meisai(books[M2.MEISAI])))
        self.ents = self.E.canonicalize(raw, self.E.alias_table(raw))
        self.s = section("## 1. 索引の側で測った事実")

    def _comps(self, p):
        return [self.E.norm(x.strip()) for x in (p or "").split(">") if x.strip()]

    def test_the_parent_component_counts_match_the_seal(self):
        import collections
        c = collections.Counter(len(self._comps(e["parent"])) for e in self.ents)
        self.assertEqual(c[0], 543)
        self.assertEqual(c[1], 1111)
        self.assertEqual(c[2], 2555)
        self.assertIn("| **543** |", self.s)
        self.assertIn("| **1,111** |", self.s)
        self.assertIn("| **2,555** |", self.s)

    def test_the_262_ambiguous_rows_are_measured_not_guessed(self):
        """**正しい親を与えても一意にならない行**の数。規則 P-6 の根拠。"""
        import collections
        by_name = collections.defaultdict(list)
        for e in self.ents:
            by_name[self.E.norm(e["name"])].append(e)
        one = amb = 0
        for e in self.ents:
            cs = set(self._comps(e["parent"]))
            if not cs:
                continue
            kept = [x for x in by_name[self.E.norm(e["name"])]
                    if self._comps(x["parent"])
                    and all(c in cs for c in self._comps(x["parent"]))
                    and self.E.norm(x["column"]) == self.E.norm(e["column"])]
            keys = {self.E.field_key(x) for x in kept}
            if len(keys) == 1:
                one += 1
            else:
                amb += 1
        self.assertEqual((one, amb), (3404, 262))
        self.assertIn("| **3,404** |", self.s)
        self.assertIn("| **262** |", self.s)
        self.assertIn("**262 行は、親が正しく分かっても結んではいけない行である。**", self.s)

    def test_the_names_that_span_levels_are_measured(self):
        import collections
        lv = collections.defaultdict(set)
        for e in self.ents:
            if e["name"]:
                lv[self.E.norm(e["name"])].add(e["level"])
        self.assertEqual(sum(1 for v in lv.values() if len(v) > 1), 27)
        self.assertIn("**27 種**", self.s)

    def test_kanrihi_has_61_parents(self):
        par = {(e["scope"], e["parent"]) for e in self.ents
               if self.E.norm(e["name"]) == self.E.norm("管理費")}
        self.assertEqual(len(par), 61)
        self.assertIn("`管理費` は **61 通り**", self.s)


if __name__ == "__main__":
    unittest.main()
