"""欠陥 A の評価の結果(封 docs/DEFECT_A_EVAL_SEAL_2026-10-14.md)を固定する。

合格線・母数・予測の照合・盲検の約束が後から動かないことを門にする。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "fixtures", "xbrl", "defect_a")
SCORE = os.path.join(BASE, "score_2026-10-14.json")
BA = os.path.join(BASE, "before_after_2026-10-14.json")
MAT = os.path.join(BASE, "seat", "material_2026-10-14.json")
KEY = os.path.join(BASE, "commander_only", "key_2026-10-14.json")
REG = os.path.join(BASE, "regression_final8_after_2026-10-14.json")
DOC = os.path.join(ROOT, "docs", "DEFECT_A_EVAL_RESULT_2026-10-14.md")
SEATS = [os.path.join(BASE, "answers_seat%d" % i, "answer_2026-10-14.json") for i in (1, 2)]


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.s = json.load(io.open(SCORE, encoding="utf-8"))

    def test_the_four_pass_lines(self):
        self.assertEqual(self.s["L_A"], 34)
        self.assertEqual(self.s["F1"], 1.0)
        self.assertEqual(self.s["F2"], 0)
        self.assertEqual(self.s["F3"], 0)
        self.assertEqual(self.s["overall"], "合格")

    def test_each_line_is_recorded_with_its_verdict(self):
        for name in ("F-1 >= 90%", "F-2 = 0", "F-3 = 0", "F-4 >= 20"):
            self.assertEqual(self.s["verdict"][name]["合否"], "合格", name)

    def test_the_numerator_and_denominator_are_consistent(self):
        self.assertEqual(self.s["F1_num"], self.s["agree_counts"]["差"])
        self.assertAlmostEqual(self.s["F1"], self.s["F1_num"] / float(self.s["L_A"]))
        self.assertEqual(sum(self.s["pair_counts"].values()), self.s["L_A"])

    def test_disagreements_would_count_against_f1(self):
        """食い違い・判定不能は分子に入らない(分母には入る)。"""
        self.assertEqual(sum(self.s["agree_counts"].values()), self.s["L_A"])
        self.assertNotIn("食い違い", self.s["agree_counts"])

    def test_the_mixed_rows_split(self):
        """混ぜた行が全部『差』なら席は当てずっぽうを言っている。分かれていること。"""
        self.assertEqual(self.s["mixed_n"], 34)
        self.assertEqual(self.s["mixed_agree_counts"], {"水準": 27, "差": 7})

    def test_the_offsets_are_all_one_written_unit(self):
        self.assertEqual(self.s["offset_units"], {"1.0": 34})

    def test_no_two_unit_offset_appeared(self):
        """予測 P-5。出たら帯 2 倍では足りない。"""
        self.assertNotIn("2.0", self.s["offset_units"])

    def test_the_three_untested_conditions_are_still_untested(self):
        """期間・集計範囲・単位 は この標本でも 1 件も落としていない(封 §7 の報告事項)。"""
        self.assertEqual(self.s["condition_counts"], {"4 つの条件はすべて満たす": 102})

    def test_the_profiles_differ(self):
        self.assertEqual(self.s["profile_L_A"], {"P20": 34, "P16": 28})

    def test_both_seats_read_only_the_material(self):
        for who in ("席1", "席2"):
            self.assertEqual(self.s["seats"]["読んだファイル"][who],
                             ["fixtures/xbrl/defect_a/seat/material_2026-10-14.json"], who)


class BeforeAfterTest(unittest.TestCase):
    def setUp(self):
        self.ba = json.load(io.open(BA, encoding="utf-8"))

    def test_the_moved_rows_and_f3(self):
        for prof, la in (("P20", 34), ("P16", 28)):
            r = self.ba["result"][prof]
            self.assertEqual(r["L_A"], la)
            self.assertEqual(len(r["moved"]), la)
            self.assertEqual(r["F3"], 0)
            self.assertEqual(r["other"], [])

    def test_every_moved_row_went_mismatch_to_grounded(self):
        for prof in ("P20", "P16"):
            for m in self.ba["result"][prof]["moved"]:
                self.assertEqual(m["before"]["result"], "VALUE_MISMATCH", m["id"])
                self.assertEqual(m["after"]["result"], "GROUNDED", m["id"])

    def test_only_money_numeric_claims_moved(self):
        for prof in ("P20", "P16"):
            for m in self.ba["result"][prof]["moved"]:
                self.assertEqual(m["kind"], "num", m["id"])
                self.assertIn(m["unit"], ("百万円", "千円", "円", "億円"), m["id"])

    def test_the_eight_documents_are_the_drawn_ones(self):
        drawn = json.load(io.open(os.path.join(BASE, "draw_2026-10-14.json"), encoding="utf-8"))["docs"]
        self.assertEqual(self.ba["docs"], drawn)


class BlindingTest(unittest.TestCase):
    """材料に engine の内部が漏れていないことを門にする。"""

    FORBIDDEN = ("要素", "context", "member", "pointer", "recomputed", "result",
                 "GROUNDED", "VALUE_MISMATCH", "jppfs", "jpcrp", "xbrl:")

    def setUp(self):
        with io.open(MAT, encoding="utf-8") as fh:
            self.text = fh.read()
        self.mat = json.loads(self.text)

    def test_the_rows_carry_only_the_sealed_fields(self):
        allowed = {"行の鍵", "docID", "文", "対象の数(文中の表記)", "単位",
                   "数の前後(文中の位置を示すための抜粋)"}
        for r in self.mat["行"]:
            self.assertEqual(set(r), allowed, r.get("行の鍵"))

    def test_nothing_in_the_material_names_the_engines_internals(self):
        for w in self.FORBIDDEN:
            self.assertNotIn(w, self.text, "材料に %r が在る" % w)

    def test_the_material_mixes_scored_and_unscored_rows(self):
        key = json.load(io.open(KEY, encoding="utf-8"))
        self.assertEqual(len(self.mat["行"]), 68)
        self.assertEqual(sum(1 for r in key["rows_map"] if r["採点対象"]), 34)
        self.assertEqual(sum(1 for r in key["rows_map"] if not r["採点対象"]), 34)

    def test_the_seats_answered_every_row_with_an_enum_value(self):
        keys = [r["行の鍵"] for r in self.mat["行"]]
        for p in SEATS:
            d = json.load(io.open(p, encoding="utf-8"))
            self.assertEqual([r["行の鍵"] for r in d["行"]], keys, p)
            for r in d["行"]:
                self.assertIn(r["判定"], ("差", "水準", "判定不能"), r["行の鍵"])


class RegressionTest(unittest.TestCase):
    """予測 P-1 / P-2 の照合(最終評価用 8 書類。合否の証拠には使わない)。"""

    def setUp(self):
        self.reg = json.load(io.open(REG, encoding="utf-8"))

    def test_p1_the_false_stops_fell_from_twelve_to_four(self):
        k = self.reg["bad_sibling_kinds"]
        self.assertEqual(sum(v for kk, v in k.items() if kk.startswith("E1'")), 4)

    def test_p2_the_wrong_grounds_side_is_unchanged(self):
        k = self.reg["bad_sibling_kinds"]
        self.assertEqual(sum(v for kk, v in k.items() if kk.startswith("E2")), 7)

    def test_the_a_class_is_gone(self):
        for kk in self.reg["bad_sibling_kinds"]:
            self.assertNotIn("A 文の数は『差』", kk)

    def test_it_is_marked_as_worktree_output(self):
        self.assertIn("worktree", self.reg["note"])
        self.assertIn("合否の証拠には使わない", self.reg["purpose"])


class DocumentTest(unittest.TestCase):
    def setUp(self):
        self.s = json.load(io.open(SCORE, encoding="utf-8"))
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip().replace("*", "").replace("`", "") for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]

    def _row(self, label):
        return [r for r in self.rows if r and r[0] == label]

    def test_each_pass_line_has_its_own_row_with_the_measured_value(self):
        for sym, got in (("F-1", "100.0%"), ("F-2", "0 件"), ("F-3", "0 件"), ("F-4", "34 件")):
            hit = self._row(sym)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (sym, len(hit)))
            self.assertTrue(any(got in c for c in hit[0]), "%s: %s" % (sym, hit[0]))

    def test_each_prediction_has_its_own_row(self):
        for sym in ("P-1", "P-2", "P-3", "P-4", "P-5"):
            self.assertEqual(len(self._row(sym)), 1, sym)

    def test_the_document_says_what_the_result_does_not_prove(self):
        self.assertIn("あらゆる書類で安全だという証明ではありません", self.doc)

    def test_the_document_discloses_the_identical_seat_agreement(self):
        self.assertIn("68 行すべてで一致", self.doc)


if __name__ == "__main__":
    unittest.main()
