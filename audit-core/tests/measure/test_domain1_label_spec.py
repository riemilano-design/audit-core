# -*- coding: utf-8 -*-
"""正解の定義が**ただ 1 か所**に在り、問いがそこから作られていることを門にする。

段 5 の失敗の直接の対策(人間の指示 2026-10-15 の ①):
> 規則と問いの対応が一つでも不一致なら、**ラベル材料を生成できない。**
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
M = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")


def mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


L = mod("label_spec", os.path.join(M, "sheet_label_spec_2026-10-15.py"))


class SingleSourceTest(unittest.TestCase):
    """問いは `SPEC` から作る。**手書きの問いが残っていないこと。**"""

    def test_the_question_is_generated_and_checks_out(self):
        self.assertTrue(L.check_question(L.question_text()))

    def test_the_builder_does_not_contain_a_hand_written_question(self):
        src = io.open(os.path.join(M, "sheet_m6_label_material_2026-10-15.py"),
                      encoding="utf-8").read()
        self.assertNotIn("QUESTION = ", src)
        self.assertIn("L.question_text()", src)
        self.assertIn("L.check_question(question)", src)

    def test_the_six_fields_and_their_blank_levels(self):
        got = {f["key"]: tuple(f["blank_at"]) for f in L.SPEC["fields"]}
        self.assertEqual(got, {"会計": (), "階層": (), "親": ("会計", "合計", "款"),
                               "科目名": ("会計", "合計"), "列": (), "値": ()})

    def test_the_account_rule_that_段5_was_missing(self):
        """段 5 で問いに写していなかった規則が、**問いの字に在ること。**"""
        q = L.question_text()
        self.assertIn("表 1(総括)に書かれている名前", q)
        self.assertIn("`東京都` を外した表 1 の名前", q)
        self.assertIn("`東京都一般会計` なら `一般会計`", q)


class QuestionGateTest(unittest.TestCase):
    """問いを 1 か所でも崩したら材料を作れないこと。"""

    def _broken(self, q):
        with self.assertRaises(AssertionError):
            L.check_question(q)

    def test_removing_a_rule_body_is_refused(self):
        q = L.question_text()
        self._broken(q.replace(L.SPEC["rules"]["R-会計-2"], "表の名前で。"))

    def test_removing_a_rule_id_is_refused(self):
        self._broken(L.question_text().replace("[R-列-2] ", ""))

    def test_removing_a_field_line_is_refused(self):
        q = L.question_text()
        self._broken(q.replace(L.field_line(L.SPEC["fields"][5]) + "\n", ""))

    def test_changing_a_field_description_is_refused(self):
        q = L.question_text()
        self._broken(q.replace(L.field_line(L.SPEC["fields"][2]), "  親 … 適当に"))

    def test_dropping_a_blank_level_is_refused(self):
        q = L.question_text()
        self._broken(q.replace("(会計 ・ 合計 ・ 款 の行は空欄)", "(会計 の行は空欄)"))

    def test_removing_a_verdict_option_is_refused(self):
        q = L.question_text()
        self._broken(q.replace("  判定不能 … ", "  (消した) … "))

    def test_changing_the_field_count_is_refused(self):
        q = L.question_text()
        self._broken(q.replace("答える欄は 6 つです。", "答える欄は 5 つです。"))

    def test_removing_an_example_is_refused(self):
        q = L.question_text()
        self._broken(q.replace('{"id": "R003"', '{"id": "X003"'))


class NormalizeTest(unittest.TestCase):
    """席の回答を同じ形に揃える。**文字列が似ているだけで同一と決めない。**"""

    ALIAS = {"東京都一般会計": {"canonical": "一般会計"}}

    def test_a_confirmed_alias_is_normalized(self):
        a = L.normalize_answer({"会計": "東京都一般会計", "階層": "目",
                                "親": "福祉費 > 子供・子育て支援費",
                                "科目名": "児童福祉施設費", "列": "支出済額",
                                "値": 219337467055}, self.ALIAS)
        self.assertEqual(a["会計"], L.norm("一般会計"))

    def test_an_unconfirmed_name_is_left_as_written(self):
        """裏づけの無い `東京都公債費会計` を**直さない**(直したら文字列で同一と決めたことになる)。"""
        a = L.normalize_answer({"会計": "東京都公債費会計", "階層": "目", "親": "a > b",
                                "科目名": "x", "列": "支出済額", "値": 1}, self.ALIAS)
        self.assertEqual(a["会計"], L.norm("東京都公債費会計"))

    def test_the_parent_separator_is_normalized_but_not_the_names(self):
        a = L.normalize_answer({"会計": "一般会計", "階層": "目", "親": "福祉費>子育て費",
                                "科目名": "x", "列": "支出済額", "値": 1})
        b = L.normalize_answer({"会計": "一般会計", "階層": "目", "親": "福祉費 > 子育て費",
                                "科目名": "x", "列": "支出済額", "値": 1})
        self.assertEqual(a["親"], b["親"])
        self.assertNotEqual(a["親"], L.norm("福祉費 > こそだて費"))

    def test_the_value_is_an_integer_string(self):
        for v in (1066495914576, "1,066,495,914,576", "1066495914576円"):
            a = L.normalize_answer({"会計": "x", "階層": "款", "親": "", "科目名": "y",
                                    "列": "支出済額", "値": v})
            self.assertEqual(a["値"], "1066495914576", v)

    def test_a_verdict_answer_stays_a_verdict(self):
        self.assertEqual(L.normalize_answer({"verdict": "判定不能"}),
                         {"verdict": L.norm("判定不能")})

    def test_the_column_alias_is_applied_both_sides(self):
        a = L.normalize_answer({"会計": "x", "階層": "款", "親": "", "科目名": "y",
                                "列": "計", "値": 1})
        self.assertEqual(a["列"], L.norm("予算現額"))


class ColumnAliasTest(unittest.TestCase):
    """列の別名は**表の構造の証拠**が在る組だけ。値の一致では足さない。"""

    def test_the_spec_alias_matches_the_structural_evidence(self):
        R = mod("rep", os.path.join(M, "sheet_representations_2026-10-15.py"))
        M2 = L.M2
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            if not os.path.exists(os.path.join(M2.CACHE, f)):
                self.skipTest("材料が ~/.cache に無い")
        books = {}
        for f in (M2.SOUKATU, M2.KESSAN, M2.MEISAI):
            books[f], _ = M2.M1.read(os.path.join(M2.CACHE, f))
        got = R.column_alias(M2.parse_meisai(books[M2.MEISAI]))
        self.assertEqual({L.norm(k): L.norm(v) for k, v in got.items()},
                         {L.norm(k): L.norm(v) for k, v in L.COLUMN_ALIAS.items()})

    def test_the_rule_text_names_the_pair(self):
        rule = L.SPEC["rules"]["R-列-2"]
        for k, v in L.COLUMN_ALIAS.items():
            self.assertIn(k, rule, k)
            self.assertIn(v, rule, v)
        self.assertIn("同じ列として採点します", rule)


class RepresentationsTest(unittest.TestCase):
    """6 欄すべてについて、表記の割れを材料を作る前に調べた記録。"""

    REC = os.path.join(FX, "representations_2026-10-15.json")

    def setUp(self):
        if not os.path.exists(self.REC):
            self.skipTest("まだ調べていない")
        self.r = json.load(io.open(self.REC, encoding="utf-8"))["fields"]

    def test_all_six_fields_were_surveyed(self):
        self.assertEqual(sorted(self.r), sorted(["会計", "階層", "親", "科目名",
                                                 "列", "値"]))

    def test_each_field_has_a_canonical_and_a_normalization_condition(self):
        for k, v in self.r.items():
            self.assertTrue(v["正本"], k)
            self.assertTrue(v["正規化できる条件"], k)
            self.assertTrue(v["決め方"], k)

    def test_the_account_field_normalizes_only_the_confirmed_one(self):
        a = self.r["会計"]
        self.assertEqual(a["正規化する"], {"東京都一般会計": "一般会計"})
        self.assertEqual(len(a["未確認(保留にする)"]), 18)
        self.assertIn("値の一致だけでは認めない", a["決め方"])

    def test_a_column_pair_with_only_value_agreement_is_refused(self):
        """**値が一致するだけで同一と決めない**(人間の指示)。"""
        cands = self.r["列"]["候補"]
        self.assertTrue(cands)
        decided = [c for c in cands if c["同一と決めたか"]]
        refused = [c for c in cands if not c["同一と決めたか"]]
        self.assertEqual([(c["決算書"], c["明細"]) for c in decided],
                         [("予算現額", "計")])
        self.assertTrue(refused)
        for c in refused:
            self.assertIn("値が一致しただけ", c["理由"])
            self.assertIsNone(c["明細の見出しの入れ子"])

    def test_the_decided_pair_has_structural_evidence(self):
        d = [c for c in self.r["列"]["候補"] if c["同一と決めたか"]][0]
        self.assertEqual(d["明細の見出しの入れ子"], "予算現額")
        self.assertIn("構造の証拠", d["理由"])


class SampleTest(unittest.TestCase):
    """段 6 の標本が、前回**一度も発火しなかった 3 条件**を満たすこと。"""

    MAT = os.path.join(FX, "m6_material_2026-10-15.json")

    def setUp(self):
        if not os.path.exists(self.MAT):
            self.skipTest("まだ材料を作っていない")
        self.m = json.load(io.open(self.MAT, encoding="utf-8"))

    def test_condition_1_unconfirmed_accounts_are_present(self):
        c = self.m["conditions"]["条件1 未確認の会計を含む"]
        self.assertTrue(c["満たす"])
        self.assertGreaterEqual(len(c["会計"]), 5)

    def test_condition_2_the_parent_is_load_bearing(self):
        c = self.m["conditions"]["条件2 親が効く行を含む"]
        self.assertTrue(c["満たす"])
        dup = c["同名で親が違う目"]
        self.assertTrue(dup)
        self.assertGreaterEqual(max(dup.values()), 2)

    def test_condition_3_novelty_is_guaranteed_structurally(self):
        c = self.m["conditions"]["条件3 新規主張 10 件以上"]
        self.assertTrue(c["満たす(構造として)"])
        self.assertIn("1 行も入れていない", c["どう満たすか"])
        self.assertIn("10 件未満なら、そのまま報告して作り直さない", c["ただし"])

    def test_no_previously_claimed_value_is_in_the_extract(self):
        """**構造で保証する**: 段 4・段 5 で主張された値が抜粋に 1 つも無いこと。

        **0 だけは除く。**段 5 が「差額は 0 円」と書いたので 0 は既出だが、
        0 は行を特定せず(不用額などに大量に在る)、落とすと抜粋が空になる。
        行の選別から外したことは材料の `rule` に書いてある。
        **主張の新規・再出の印は変えていない**(0 の主張は `再出` のまま)。
        """
        used = set()
        for f in ("m4_binds_2026-10-15.json", "m5_binds_2026-10-15.json"):
            for cl in json.load(io.open(os.path.join(FX, f),
                                        encoding="utf-8"))["claims"]:
                v = cl.get("value")
                if v is not None and v != 0:
                    used.add(v)
        extract = (self.m["prompt"].split("----- 表(ここから) -----")[1]
                   .split("----- 表(ここまで) -----")[0])
        hit = [v for v in used if "{:,}".format(v) in extract]
        self.assertEqual(hit, [], hit)

    def test_the_rule_is_mechanical(self):
        for s in ("1 行も入れない", "文書の順で先頭から", "0 を除く"):
            self.assertIn(s, self.m["rule"], s)

    def test_the_instruction_text_is_unchanged(self):
        prev = json.load(io.open(os.path.join(FX, "m4_material_2026-10-15.json"),
                                 encoding="utf-8"))
        mark = "----- 表(ここから) -----"
        self.assertEqual(self.m["prompt"].split(mark)[0], prev["prompt"].split(mark)[0])
        self.assertTrue(self.m["prompt_identical_to_stage4"])

    def test_the_limits_are_unchanged(self):
        self.assertEqual(self.m["limits"], {"extract_chars": 24000,
                                            "report_chars": 1200})
        self.assertLessEqual(self.m["extract_chars"], 24000)
        self.assertEqual(self.m["runs"], 1)


if __name__ == "__main__":
    unittest.main()
