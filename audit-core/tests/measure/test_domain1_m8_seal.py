# -*- coding: utf-8 -*-
"""段 8 の封(docs/DOMAIN1_M8_SEAL_2026-10-16.md)を固定する。**材料より先に赤くなる門。**

守るのは 7 つ。
  1. 段 7 を失敗として固定し、再採点しないこと
  2. 款名の裏づけ B-1〜B-3 と、**推測で補完しない**こと
  3. **表 3 の裏づけは 2 本しか作れない**ことを先に書いてあること
  4. 人間が新しく求めた予測 ― **評価者が根拠を確認できないとき engine が何をするか**(X-1〜X-4)
  5. 合格線が段 7 と同じで、**E2 = 0 件**と増分の 2 本が在ること
  6. 席の一致率を成果として書かないこと
  7. engine と問いを変えないこと・②③に触らないこと
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
FX = os.path.join(ROOT, "fixtures", "sheet")
SEAL = os.path.join(ROOT, "docs", "DOMAIN1_M8_SEAL_2026-10-16.md")
M7S = os.path.join(FX, "m7_score_2026-10-15.json")
M6MAT = os.path.join(FX, "m6_label_material_2026-10-15.json")
ENGINE = os.path.join(ROOT, "measure", "sheet_m5_engine_2026-10-15.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def section(name):
    t = text(SEAL)
    i = t.index(name)
    j = t.find("\n## ", i + 1)
    return t[i:(j if j > 0 else len(t))]


class Stage7FrozenTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 1. 段 7 は失敗として固定する")

    def test_the_seal_quotes_stage_7_numbers_as_they_are(self):
        sc = load(M7S)
        self.assertEqual(sc["overall"], "失敗")
        self.assertEqual(sc["E2_誤受理"], 6)
        head = text(SEAL)
        self.assertIn("**失敗**・\nE2 **6 件**・G-1 **51.3%**・G-7 **+3 件**・G-8 **0 件**",
                      head)
        self.assertIn("**この数は動かさない。**", head)

    def test_the_seal_refuses_to_rescore_stage_7(self):
        self.assertIn("**段 7 の報告文を新しい材料で再採点しない。**", self.s)
        self.assertIn("段 8 は**別の標本・別の報告文**で測る。", self.s)

    def test_the_decisive_correspondence_is_recorded(self):
        """段 7 の 20/20・6/6 が封の予測の土台であること。"""
        self.assertIn("| **20 件** | **20 件すべて正しい接続** |", self.s)
        self.assertIn("| **6 件** | **6 件すべて誤受理** |", self.s)
        self.assertIn("**20/20・6/6 で対応している。**", self.s)

    def test_the_numbers_match_the_stage_7_record(self):
        sc = load(M7S)
        self.assertEqual(sc["lines"]["G-1 接続の正確さ"]["num"], 20)
        self.assertEqual(sum(1 for r in sc["rows"]
                             if r["verdict"] == "根拠なし/判定不能なのに接続した"), 6)


class BackingTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 2. 材料の仕様")

    def test_the_three_backings_for_a_kou_parent_are_named(self):
        for k in ("**B-1**", "**B-2**", "**B-3**"):
            self.assertIn(k, self.s, k)
        self.assertIn("`01` から始まる 1..n の連番", self.s)
        self.assertIn("**1 通りだけ**", self.s)

    def test_a_row_without_all_three_is_excluded_not_guessed(self):
        self.assertIn("**3 本のうち 1 本でも欠けるか食い違えば、その項の行は表 2 に入れない。**",
                      self.s)
        self.assertIn("**款名を空欄にして載せることもしない。推測で補完しない。**", self.s)

    def test_the_measured_counts_are_in_the_seal(self):
        self.assertIn("| **3 本そろう(B-1 = B-3、候補 1 通り)** | **72** |", self.s)
        self.assertIn("| 食い違う(明細に複数の款の候補が在る) | **2**", self.s)
        self.assertIn("| 明細に対応する項が無い | **20** |", self.s)

    def test_table_3_has_only_two_backings_and_says_so(self):
        self.assertIn("**2 本**しか作れない", self.s)
        self.assertIn("**決算書に目の行は無いので、表 3 に B-3 のような"
                      "「別の file での裏づけ」は作れない。**", self.s)
        self.assertIn("**この差を「同じ強さの根拠」として扱わない。**", self.s)

    def test_the_question_hash_is_pinned(self):
        mat = load(M6MAT)
        sha = hashlib.sha256(mat["question"].encode("utf-8")).hexdigest()
        self.assertIn(sha[:16], self.s)
        self.assertIn(mat["spec_version"], self.s)
        self.assertIn("**正解の定義を動かさずに材料だけを直す。**", self.s)

    def test_the_engine_is_not_changed(self):
        self.assertIn("**P-1〜P-7 を変更しない。**", self.s)
        self.assertIn("sheet_m7_engine_2026-10-15.py", self.s)


class UnverifiablePredictionTest(unittest.TestCase):
    """**人間が新しく求めた予測の型。**ここが消えたら赤。"""

    def setUp(self):
        self.s = section("## 4. **評価者が根拠を確認できない場合")

    def test_the_human_instruction_is_quoted(self):
        self.assertIn("**評価者が根拠を確認できないケースで\n> エンジンが何をするかも、"
                      "予測対象に含めるべきです。**", self.s)

    def test_my_stage_7_miss_is_named_here(self):
        self.assertIn("段 7 で私が外したのはここである。", self.s)
        self.assertIn("**「評価できない」と「安全側に落ちる」は別である。**", self.s)

    def test_the_four_x_indicators_exist(self):
        for k in ("**X-1**", "**X-2**", "**X-3**", "**X-4**"):
            self.assertIn(k, self.s, k)
        self.assertIn("段 7 の実測は X-1 **20**・X-2 **6**・X-3 **6**・X-4 **0** だった。",
                      self.s)

    def test_the_seal_admits_this_type_may_not_close(self):
        self.assertIn("**この型は段 8 では閉じない**", self.s)
        self.assertIn("**款名を足しても X-2 は 0 にならない可能性が在る。**", self.s)

    def test_the_seal_refuses_to_add_an_extract_scoped_engine_rule(self):
        self.assertIn("**X-2 を 0 にするために engine に「抜粋の外に結ばない」規則を"
                      "足すことはしない**", self.s)
        self.assertIn("材料に合わせた規則は実験用の細工になる", self.s)


class GateLineTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 5. 合格線")

    def test_the_lines_are_the_same_as_stage_7(self):
        for line in ("| G-1 接続の正確さ | ≥ 50% |", "| G-2 誤接続 | = 0 件 |",
                     "| G-3 根拠なしの接続 | = 0 件 |", "| G-5 母数 | ≥ 20 件 |",
                     "| G-7 正しい接続の増分(新 − 旧) | ≥ 1 件 |",
                     "| G-8 誤受理の増分(新 − 旧) | = 0 件 |"):
            self.assertIn(line, self.s, line)

    def test_the_main_metric_is_e2_zero_and_the_verdict_is_the_new_engine(self):
        self.assertIn("**主指標は E2 = 0 件。**", self.s)
        self.assertIn("**新 engine の数で出す。**", self.s)
        self.assertIn("**良い方を選ばない。**", self.s)

    def test_the_failure_conditions_name_every_line(self):
        for k in ("G-1 < 50%", "**E2 ≥ 1 件**", "G-3 ≥ 1 件",
                  "**G-7 < 1 件**", "**G-8 ≥ 1 件**"):
            self.assertIn(k, self.s, k)

    def test_seat_agreement_is_not_a_result(self):
        self.assertIn("**「2 席の回答が一致しやすくなっても、それだけで engine の接続が"
                      "正しいと証明されたことには\nならない。」**", self.s)
        self.assertIn("**席の一致率が上がったことを成果として書かない。**", self.s)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 6. 予測")

    def test_all_ten_predictions_exist_with_counts(self):
        for i in range(1, 11):
            self.assertRegex(self.s, r"\| T-%d \| " % i)
        self.assertIn("**E2 は 0〜1 件。1 件でも出れば失敗**", self.s)
        self.assertIn("**X-2(抜粋の外に結ぶ)は 0〜2 件。"
                      "X-2 に入った主張は全部 X-3(誤受理)になる**", self.s)
        self.assertIn("**X-4(抜粋に在る行に結んで誤受理)は 0 件**", self.s)

    def test_the_seal_learns_from_stage_7(self):
        self.assertIn("**段 7 で件数の予測を書かなかった反省から、"
                      "今回は T-1〜T-10 を件数で書いた。**", self.s)

    def test_the_seat_agreement_prediction_is_marked_as_not_a_result(self):
        self.assertIn("**ただしこれは成果ではない**(§5)", self.s)

    def test_the_verdict_is_not_by_how_many_predictions_hit(self):
        self.assertIn("**10 本のうち 1 本でも外れたら、外れたと書く。**", self.s)
        self.assertIn("当たった本数で合否を言わない。", self.s)


class ScopeTest(unittest.TestCase):
    def setUp(self):
        self.s = section("## 7. やらないこと")

    def test_nine_things_not_to_do(self):
        self.assertEqual(len(re.findall(r"^\d+\. ", self.s, re.M)), 9)

    def test_it_keeps_2_and_3_out(self):
        self.assertIn("②(階層の手がかりの引き継ぎ)と③(未確認の別名)には手を付けない。",
                      self.s)

    def test_it_refuses_generalisation_and_guessing(self):
        self.assertIn("**款名を推測で補完しない。**", self.s)
        self.assertIn("他の自治体・他の年度・一般の会計資料に通じるとは結論しない。", self.s)

    def test_the_order_puts_the_seal_first(self):
        s = section("## 8. 順序")
        self.assertIn("**この封を commit する(材料より先・生成より先)。**", s)
        self.assertIn("**生成の前に機会の件数を記録する**", s)
        self.assertIn("**同じ報告文に旧・新 2 本の engine を当てて凍結**", s)

    def test_the_old_engine_is_still_the_stage_5_file(self):
        import subprocess
        out = subprocess.check_output(
            ["git", "-C", ROOT, "log", "--oneline", "-1", "--",
             "measure/sheet_m5_engine_2026-10-15.py"]).decode()
        self.assertIn("段 5", out, "旧 engine が変更されている: %s" % out)


class MeasuredFactsTest(unittest.TestCase):
    """§2 の数は**元資料から測ったもの**。資料が変わったら赤くする。"""

    def setUp(self):
        spec = importlib.util.spec_from_file_location("m5_for_seal8", ENGINE)
        self.E = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.E)
        M2 = self.E.M2
        self.M2 = M2
        self.books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            self.books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        self.ks = M2.parse_kessan(self.books[M2.KESSAN])
        self.ms = M2.parse_meisai(self.books[M2.MEISAI])
        raw = self.E.fix_total_level(self.E.build_index(
            M2.parse_soukatu(self.books[M2.SOUKATU]), self.ks, self.ms))
        self.ents = self.E.canonicalize(raw, self.E.alias_table(raw))

    def test_b2_the_kou_codes_restart_at_01_under_every_kan(self):
        import collections
        norm = self.M2.norm
        b0 = [b for b in self.ks["blocks"]
              if norm(b["account"]) == norm("一般会計")][0]
        g = collections.defaultdict(list)
        for it in b0["items"]:
            g[it.get("parent_row")].append(it["code"])
        self.assertEqual(len(g), 18)
        self.assertEqual(sum(1 for v in g.values() if v[0] == "01"), 18)
        self.assertEqual(
            sum(1 for v in g.values()
                if [int(x) for x in v] == list(range(1, len(v) + 1))), 18)
        self.assertIn("一般会計で **18 束 / 18 束**が成立", section("## 2. 材料の仕様"))

    def test_b5_the_moku_codes_restart_at_01_under_every_kou(self):
        import collections
        bundles = restart = seq = 0
        for s in self.ms["sheets"]:
            item_rows = sorted((x["row"], x.get("name")) for x in s["items"])
            g = collections.defaultdict(list)
            for mk in s["moku"]:
                hit = [rr for rr, n in item_rows if rr < mk["row"]]
                g[hit[-1] if hit else None].append(mk.get("code"))
            for k, v in g.items():
                if k is None or not all(v):
                    continue
                bundles += 1
                restart += 1 if v[0] == "01" else 0
                try:
                    if [int(x) for x in v] == list(range(1, len(v) + 1)):
                        seq += 1
                except ValueError:
                    pass
        self.assertEqual((bundles, restart, seq), (101, 101, 101))
        self.assertIn("**101 束 / 101 束**が成立", section("## 2. 材料の仕様"))

    def test_b3_the_two_files_agree_on_72_kou_parents(self):
        import collections
        norm = self.M2.norm
        kessan, meisai = {}, collections.defaultdict(set)
        for e in self.ents:
            if e["file"] == "決算書 歳出" and e["level"] == "項" and e["name"]:
                kessan[(norm(e["scope"]), norm(e["name"]))] = e["parent"]
            if e["file"] == "事項別明細" and e["level"] == "項" and e["name"] and e["parent"]:
                meisai[(norm(e["scope"]), norm(e["name"]))].add(e["parent"])
        agree = dis = only_k = 0
        for k, kan in kessan.items():
            m = meisai.get(k)
            if not m:
                only_k += 1
            elif len(m) == 1 and norm(list(m)[0]) == norm(kan or ""):
                agree += 1
            else:
                dis += 1
        self.assertEqual((len(kessan), agree, dis, only_k), (94, 72, 2, 20))


if __name__ == "__main__":
    unittest.main()
