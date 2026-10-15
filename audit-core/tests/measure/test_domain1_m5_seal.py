# -*- coding: utf-8 -*-
"""段 5 の封(docs/DOMAIN1_M5_SEAL_2026-10-15.md)を門にする。

人間の 3 つの決定と**補足条件**が、後から緩まないことを見る。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DOC = os.path.join(ROOT, "docs", "DOMAIN1_M5_SEAL_2026-10-15.md")
M4SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M4_SEAL_2026-10-15.md")
DIAG = os.path.join(ROOT, "fixtures", "sheet", "m4_fix_diagnostic_2026-10-15.json")
SCORE = os.path.join(ROOT, "fixtures", "sheet", "m4_score_2026-10-15.json")

# §5 の検出条件で「壊したら止める」と名前を挙げた行
MUST_KEEP = ("R004", "R008", "R009", "R013", "R015",
             "R017", "R018", "R019", "R020", "R021", "R022")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def section(doc, start, end=None):
    a = doc.index(start)
    b = doc.index(end) if end else len(doc)
    return doc[a:b]


class HumanDecisionsTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_three_decisions_are_quoted(self):
        self.assertIn("①親の欄を足す、②階層の手がかりを修正する、", self.doc)
        self.assertIn("③別名の裏づけは 3 本以上・食い違い 0 件を要求する", self.doc)

    def test_the_independence_caveat_is_quoted(self):
        self.assertIn("同じ表の同じ情報を 3 回参照しただけなら、独立した 3 本とは数えない",
                      self.doc)
        self.assertIn("根拠の独立性", self.doc)

    def test_definitions_come_before_code(self):
        self.assertIn("正解の定義と検証条件を先に固める段階", self.doc)
        self.assertIn("engine はこの封の後に直す", self.doc)


class AnswerShapeTest(unittest.TestCase):
    """§1 新しい答えの形。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_the_six_fields(self):
        sec = section(self.doc, "### 1-1.", "### 1-2.")
        for f in ("会計", "階層", "**親**", "科目名", "列", "値"):
            self.assertIn(f, sec, f)

    def test_the_parent_is_defined_per_level(self):
        sec = section(self.doc, "### 1-1.", "### 1-2.")
        self.assertIn("`項` なら款名", sec)
        self.assertIn("`目` なら「款名 > 項名」", sec)

    def test_the_total_row_question_is_defined(self):
        sec = section(self.doc, "### 1-2.", "### 1-3.")
        self.assertIn("会計 = `合計` / 階層 = `合計` / 親 = 空欄 / 科目名 = 空欄", sec)
        self.assertIn("**空欄にしない。**", sec)
        self.assertIn("例つきで", sec)

    def test_a_value_match_without_a_parent_is_not_a_correct_connection(self):
        self.assertIn("**値が一致しても正しい接続としない。**", self.doc)

    def test_the_uniqueness_requirement_is_measured_before_the_report(self):
        sec = section(self.doc, "### 1-3.", "### 1-4.")
        self.assertIn("1 より大きい組が残る階層は、採点の対象から外す", sec)
        self.assertIn("**値で候補を絞ってはならない。**", sec)
        self.assertIn("生成の前に数えて", sec)

    def test_old_and_new_forms_are_recorded_separately(self):
        sec = section(self.doc, "### 1-4.", "### 1-5.")
        for f in ("`agree_4`", "`agree_6`", "`only_4`"):
            self.assertIn(f, sec, f)
        self.assertIn("合否はこちらだけで出す", sec)
        self.assertIn("**`only_4` の件数を必ず報告する。**", sec)

    def test_disagreeing_seats_stay_in_the_denominator(self):
        self.assertIn("2 席が食い違った行は判定不能として分母に残す", self.doc)


class LevelCueTest(unittest.TestCase):
    """§2 C-8 の仕様と、**両方を同時に**満たす回帰条件。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_the_level_cue_narrows_instead_of_the_value(self):
        self.assertIn("値の一致を使って候補を絞るのではなく", self.doc)
        self.assertIn("文章の階層指定と資料の階層が一致する候補だけを残す", self.doc)

    def test_it_still_holds_when_several_candidates_remain(self):
        self.assertIn("階層情報があっても候補が複数残るなら保留です", self.doc)

    def test_the_five_regression_conditions_exist(self):
        sec = section(self.doc, "### 2-2.", "## 3.")
        for k in ("K-1", "K-2", "K-3", "K-4", "K-5"):
            self.assertIn(k, sec, k)
        self.assertIn("同じ試験ファイルの中で", sec)

    def test_saving_r007_and_not_mislinking_are_verified_together(self):
        self.assertIn("同時に検証する必要があります", self.doc)


class AliasIndependenceTest(unittest.TestCase):
    """§4 独立性の定義と、**先に数えた件数**。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_the_six_conditions(self):
        sec = section(self.doc, "### 4-1.", "### 4-2.")
        for s in ("独立した 3 本以上", "食い違いが 0 件", "会計の層と階層が整合",
                  "**前方一致は認めない。**",
                  "値が一致するという理由だけで、別名の同一性を認めない",
                  "未確認として保留"):
            self.assertIn(s, sec, s)

    def test_the_four_independence_requirements(self):
        sec = section(self.doc, "### 4-2.", "### 4-3.")
        for k in ("I-1", "I-2", "I-3", "I-4"):
            self.assertIn(k, sec, k)
        self.assertIn("同じ行を別の列で 2 回数えない", sec)
        self.assertIn("款とその唯一の項は 1 本と数える", sec)
        self.assertIn("同じ数が 3 か所に出ても 1 本", sec)

    def test_the_measured_counts_are_sealed(self):
        sec = section(self.doc, "### 4-3.", "### 4-4.")
        self.assertIn("**18**", sec)
        self.assertIn("**2**", sec)
        self.assertIn("**各 1**", sec)
        self.assertIn("**19 候補のうち通るのは 1 件だけである。**", sec)

    def test_it_admits_the_previous_implementation_was_wrong(self):
        sec = section(self.doc, "### 4-3.", "### 4-4.")
        self.assertIn("17 件を 2 本で通していた", sec)
        self.assertIn("同じ行を 2 つの列で 2 回数えていた", sec)

    def test_the_shrinking_denominator_is_declared_in_advance(self):
        sec = section(self.doc, "### 4-4.", "## 5.")
        self.assertIn("性能をよく見せるための除外ではない", sec)
        self.assertIn("**G-5(母数 ≥ 20)は緩めない。**", sec)
        self.assertIn("判定不能(母数不足)", sec)


class BreakDetectionTest(unittest.TestCase):
    """§5 既存の正しい接続が壊れたときの検出条件。"""

    def setUp(self):
        self.doc = text(DOC)

    def test_the_rows_that_must_keep_working_are_named(self):
        hit = [l for l in self.doc.splitlines() if "agree_6` で一致しなくなったら" in l]
        self.assertEqual(len(hit), 1, hit)
        row = hit[0]
        for cid in MUST_KEEP:
            if cid in ("R018", "R019", "R020", "R021"):
                continue   # R017〜R022 の範囲表記
            self.assertIn(cid, row, cid)
        self.assertIn("R017〜R022", row)
        self.assertIn("原因を 1 件ずつ書いて止める", row)
        self.assertIn("数を直さない", row)

    def test_r007_is_not_in_the_must_keep_list(self):
        """R007 は診断で保留に落ちた行。**壊れていない行の一覧に入れない。**"""
        hit = [l for l in self.doc.splitlines() if "agree_6` で一致しなくなったら" in l][0]
        self.assertNotIn("R007", hit)

    def test_the_must_keep_rows_were_actually_correct_in_the_diagnostic(self):
        """一覧が実測と合っていること(名前を思い出しで書いていないこと)。"""
        d = json.load(io.open(DIAG, encoding="utf-8"))
        ok = {r["id"] for r in d["rows"] if r["after"] == "正しい接続"}
        self.assertEqual(set(MUST_KEEP) - ok, set(), sorted(set(MUST_KEEP) - ok))

    def test_binding_to_an_unconfirmed_account_is_a_failure(self):
        self.assertIn("未確認の 18 件に属する行へ結んだら**失敗**", self.doc)

    def test_the_old_form_may_not_decide_the_verdict(self):
        self.assertIn("`agree_4` を使ったら門が赤くなる", self.doc)
        self.assertIn("**`agree_4` で合否を出さない。**", self.doc)


class LinesAndPredictionsTest(unittest.TestCase):
    SECTION = ("### 7-1", "### 7-2")
    ROWS = (("G-1 接続の正確さ", "≥ 50%"), ("G-2 誤接続", "= 0 件"),
            ("G-3 根拠なしの接続", "= 0 件"), ("G-4 保留の適切さ", "≥ 80%"),
            ("G-5 母数", "≥ 20 件"))

    def setUp(self):
        self.doc = text(DOC)

    def test_the_carried_lines_are_a_table_of_exactly_five_rows(self):
        sec = section(self.doc, *self.SECTION)
        prev = text(M4SEAL)
        for name, line in self.ROWS:
            self.assertIn("| %s | %s |" % (name, line), sec, name)
            self.assertIn(line.replace(" 件", ""), prev, line)
        self.assertEqual(len([l for l in sec.splitlines() if l.startswith("| G-")]), 5)

    def test_the_lines_are_counted_on_the_new_form(self):
        self.assertIn("G-1・G-2 は `agree_6`(新形式)で数える", self.doc)

    def test_the_primary_metric_is_a_count(self):
        sec = section(self.doc, "### 7-2.", "### 7-3.")
        self.assertIn("**E2 = 誤受理の件数。**", sec)
        self.assertIn("線は 0 件。率ではなく件数で報告する", sec)
        self.assertIn("誤接続 0 件を母数なしで誇らない", sec)
        self.assertIn("入っていなければ「試していない」と書く", sec)

    def test_ten_predictions_each_have_a_row(self):
        sec = section(self.doc, "### 7-4.", "### 7-5.")
        for i in range(1, 11):
            self.assertIn("| Q-%d |" % i, sec, "Q-%d" % i)

    def test_a_prediction_that_means_failure_is_named(self):
        self.assertIn("Q-2 が外れて 3 件以上なら段 5 は失敗", self.doc)
        self.assertIn("0 件とは予測しない", self.doc)

    def test_the_failure_conditions_forbid_adjusting_afterwards(self):
        sec = section(self.doc, "### 7-5.", "## 8.")
        self.assertIn("E2 ≥ 1 件", sec)
        self.assertIn("同じ標本で閾値・採点規則・分母を調整して合格扱いにしない", sec)


class GenerationTest(unittest.TestCase):
    def setUp(self):
        self.doc = text(DOC)

    def test_the_cost_and_run_cap(self):
        self.assertIn("**1 モデル・1 回**", self.doc)
        self.assertIn("上限 **4 USD**", self.doc)
        self.assertIn("やり直さない", self.doc)

    def test_the_engine_output_is_not_handed_to_the_writer(self):
        self.assertIn("engine の出力・ラベル・採点規則は渡さない", self.doc)

    def test_the_overlap_with_the_previous_report_is_measured(self):
        self.assertIn("前回の報告文との重なりを測る", self.doc)
        self.assertIn("`新規` が 10 件未満なら、「別の報告文で確かめた」とは書かない",
                      self.doc)


class FrozenTest(unittest.TestCase):
    def test_the_previous_failure_is_still_the_record(self):
        s = json.load(io.open(SCORE, encoding="utf-8"))
        self.assertEqual(s["overall"], "失敗")
        self.assertEqual(s["lines"]["G-2 誤接続"]["count"], 5)

    def test_the_diagnostic_is_still_not_evidence(self):
        d = json.load(io.open(DIAG, encoding="utf-8"))
        self.assertTrue(d["not_performance_evidence"])
        self.assertEqual(d["applied_times"], 1)

    def test_the_seal_refuses_to_reuse_the_24(self):
        doc = text(DOC)
        self.assertIn("今回の 24 件を合格判定に使わない", doc)
        self.assertIn("再採点しない", doc)


if __name__ == "__main__":
    unittest.main()
