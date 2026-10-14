"""方向の主張の原因分け(measure/final8_direction_causes_2026-10-14.py)を固定する。

docs/DIRECTION_CAUSES_2026-10-14.md の数が commit された code から再現できることを門にする。
分類の順・金額の照合・読みの記録の縛りを変えたら、ここが赤くなる。
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _load(name):
    p = os.path.join(ROOT, "measure", name)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_")[:-3], p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


T = _load("final8_direction_causes_2026-10-14.py")
BASE = os.path.join(ROOT, "fixtures", "xbrl", "final8")
CAUSES = os.path.join(BASE, "direction_causes_2026-10-14.json")
READING = os.path.join(BASE, "direction_reading_2026-10-14.json")
DOC = os.path.join(ROOT, "docs", "DIRECTION_CAUSES_2026-10-14.md")

CTX = {
    "plain_cur": {"members": []},
    "plain_pri": {"members": []},
    "seg_cur": {"members": ["x:SegAMember"]},
    "seg_pri": {"members": ["x:SegAMember"]},
}


def row(arm, label):
    return {"id": "D:H-001", "state": "GROUNDED", "strict": False, "direction": True,
            "arm": arm, "label": label}


class MachineBucketTest(unittest.TestCase):
    """段 1(文を読まずに決まる分け方)の順を固定する。"""

    def test_alias_is_taken_before_anything_else(self):
        r = row([("NetSalesSummaryOfBusinessResults", "plain_cur")], [("NetSales", "plain_cur")])
        self.assertEqual(T.machine_bucket(r, CTX), "alias")

    def test_same_element_different_member_is_member_not_disjoint(self):
        r = row([("NetSales", "plain_cur"), ("NetSales", "plain_pri")],
                [("NetSales", "seg_cur"), ("NetSales", "seg_pri")])
        self.assertEqual(T.machine_bucket(r, CTX), "member")

    def test_sharing_one_fact_is_overlap(self):
        r = row([("GrossProfit", "plain_cur")],
                [("GrossProfit", "plain_cur"), ("SGA", "plain_cur")])
        self.assertEqual(T.machine_bucket(r, CTX), "overlap")

    def test_sharing_nothing_is_disjoint(self):
        r = row([("Inventories", "plain_cur")], [("AdvancePayments", "plain_cur")])
        self.assertEqual(T.machine_bucket(r, CTX), "disjoint")

    def test_same_element_same_context_but_only_alias_differs_is_not_member(self):
        """member の判定が alias より前に来たら赤くなる。"""
        r = row([("NetSalesSummaryOfBusinessResults", "seg_cur")], [("NetSales", "seg_cur")])
        self.assertEqual(T.machine_bucket(r, CTX), "alias")


class AmountTest(unittest.TestCase):
    """軸 2 の金額照合。切り捨ての許容を外したら赤くなる。"""

    def test_parses_scales_and_commas(self):
        self.assertEqual(T.amounts("売上高は53,021百万円、費用は1,234千円、端数は56円"),
                         {(53021.0, 10 ** 6), (1234.0, 10 ** 3), (56.0, 1)})

    def test_percentages_are_not_amounts(self):
        self.assertEqual(T.amounts("前期比22.9%減少"), set())

    def test_truncated_notation_matches(self):
        """53,021,694,000 円は書類では 53,021百万円 と切り捨てて書かれる。"""
        self.assertTrue(T.in_sentence(53021694000.0, {(53021.0, 10 ** 6)}))

    def test_rounded_notation_also_matches(self):
        self.assertTrue(T.in_sentence(385846000.0, {(386.0, 10 ** 6)}))

    def test_a_different_amount_does_not_match(self):
        self.assertFalse(T.in_sentence(382286000.0, {(385.0, 10 ** 6)}))

    def test_sign_is_ignored(self):
        self.assertTrue(T.in_sentence(-135504000.0, {(135.0, 10 ** 6)}))

    def test_missing_value_is_not_present(self):
        self.assertFalse(T.in_sentence(None, {(135.0, 10 ** 6)}))


class NumberAxisTest(unittest.TestCase):
    def setUp(self):
        self.vals = {("D", "A", "c1"): 100.0, ("D", "B", "c1"): 200.0}

    def _row(self, arm, label):
        r = row(arm, label)
        r["docID"] = "D"
        return r

    def test_label_only_means_the_number_would_have_caught_it(self):
        r = self._row([("A", "c1")], [("B", "c1")])
        self.assertTrue(T.number_axis(r, self.vals, "200円の増加").startswith("ラベルの数だけ"))

    def test_both_present_needs_a_choice(self):
        r = self._row([("A", "c1")], [("B", "c1")])
        self.assertTrue(T.number_axis(r, self.vals, "100円と200円").startswith("両方の数"))

    def test_no_amount_in_the_sentence(self):
        r = self._row([("A", "c1")], [("B", "c1")])
        self.assertEqual(T.number_axis(r, self.vals, "増加によるものです"), "文に金額が無い")

    def test_amounts_exist_but_neither_side_matches(self):
        r = self._row([("A", "c1")], [("B", "c1")])
        self.assertEqual(T.number_axis(r, self.vals, "999円"), "どちらの数も文に無い")


class SameQuantityTest(unittest.TestCase):
    def _row(self, arm, label):
        r = row(arm, label)
        r["docID"] = "D"
        return r

    def test_self_made_delta_equal_to_a_single_change_fact(self):
        vals = {("D", "Cash", "cur"): 5738810000.0, ("D", "Cash", "pri"): 5503718000.0,
                ("D", "NetChange", "dur"): 235092000.0}
        r = self._row([("Cash", "cur"), ("Cash", "pri")], [("NetChange", "dur")])
        self.assertIs(T.same_quantity(r, vals), True)

    def test_self_made_delta_different_from_the_change_fact(self):
        vals = {("D", "CapitalSurplus", "cur"): 270367000.0, ("D", "CapitalSurplus", "pri"): 417417000.0,
                ("D", "Retirement", "dur"): -135504000.0}
        r = self._row([("CapitalSurplus", "cur"), ("CapitalSurplus", "pri")], [("Retirement", "dur")])
        self.assertIs(T.same_quantity(r, vals), False)

    def test_shape_without_a_pair_is_not_comparable(self):
        vals = {("D", "A", "c1"): 1.0, ("D", "B", "c1"): 2.0}
        r = self._row([("A", "c1")], [("B", "c1")])
        self.assertIsNone(T.same_quantity(r, vals))


class ReadingRecordTest(unittest.TestCase):
    """読みの記録の縛り: 引いた語は文に実在しなければならない。"""

    def setUp(self):
        self.docs, self.labels, self.dump, self.ctx, self.sent = T.load()
        self.rows = T.direction_e2(self.dump, self.labels, self.ctx)
        self.reading = json.load(io.open(READING, encoding="utf-8"))["rows"]

    def test_the_twenty_rows_reproduce(self):
        self.assertEqual(len(self.rows), 20)

    def test_the_reading_covers_exactly_the_rows_the_machine_cannot_decide(self):
        need = {r["id"] for r in self.rows if r["bucket"] in ("overlap", "disjoint")}
        self.assertEqual(need, set(self.reading))

    def test_every_quoted_word_is_really_in_the_sentence(self):
        for rid, rd in self.reading.items():
            for fld in ("arm_word", "label_word"):
                w = rd.get(fld) or ""
                if w:
                    self.assertIn(w, self.sent[rid], "%s %s" % (rid, fld))

    def test_build_refuses_a_word_that_is_not_in_the_sentence(self):
        bad = json.load(io.open(READING, encoding="utf-8"))
        rid = sorted(bad["rows"])[0]
        bad["rows"][rid]["label_word"] = "文に無いはずの語XYZ"
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
            json.dump(bad, fh, ensure_ascii=False)
            p = fh.name
        keep = T.READING
        try:
            T.READING = p
            with self.assertRaises(AssertionError):
                T.stage_build()
        finally:
            T.READING = keep
            os.unlink(p)
            T.stage_build()  # fixture を元に戻す

    def test_every_verdict_is_in_the_enum(self):
        for rid, rd in self.reading.items():
            self.assertIn(rd["verdict"], T.VERDICTS + ("",), rid)


class RecordedCountsTest(unittest.TestCase):
    """文書に書いた数を固定する。分類の順や照合を変えたら赤くなる。"""

    def setUp(self):
        self.rec = json.load(io.open(CAUSES, encoding="utf-8"))

    def test_bucket_counts(self):
        self.assertEqual(self.rec["bucket_counts"],
                         {"alias": 1, "member": 4, "overlap": 7, "disjoint": 8})

    def test_primary_cause_counts(self):
        self.assertEqual(self.rec["cause_counts"],
                         {"(a) 対の取り方": 7, "(c) 語の掛かり先": 5, "(b) member の選び方": 4,
                          "判定不能": 2, "3 候補の外(同値類の表記違い)": 1,
                          "3 候補の外(要素の同定の誤り)": 1})
        self.assertEqual(sum(self.rec["cause_counts"].values()), 20)

    def test_co_cause_counts(self):
        """併存の可能性(disjoint で結んだ fact の数も違う行)を数えるのをやめたら赤くなる。"""
        self.assertEqual(self.rec["co_cause_counts"],
                         {"(a) 対の取り方(結んだ fact の数が違う)": 5})

    def test_number_axis_counts(self):
        self.assertEqual(self.rec["number_axis_counts"],
                         {"ラベルの数だけ文に在る(数を付ければ落ちた)": 6,
                          "両方の数が文に在る(どちらの数かを決める必要)": 5,
                          "文に金額が無い": 5,
                          "どちらの数も文に無い": 4})

    def test_same_quantity_counts(self):
        self.assertEqual(self.rec["same_quantity_counts"], {"None": 10, "False": 8, "True": 2})

    def test_axis1_number_presence_over_all_grounded_rows(self):
        a = self.rec["axis1_counts"]
        self.assertEqual(a["値の形 | 数あり | E1'"], 246)
        self.assertEqual(a["値の形 | 数あり | E2"], 13)
        self.assertEqual(a["値の形 | 数なし | E1'"], 13)
        self.assertEqual(a["値の形 | 数なし | E2"], 5)
        self.assertEqual(a["方向 | 数なし | E1'"], 32)
        self.assertEqual(a["方向 | 数なし | E2"], 20)
        self.assertEqual(sum(a.values()), 329)

    def test_no_direction_claim_carried_a_number(self):
        """方向の形はすべて「数なし」。この 0 が崩れたら軸 1 の読みが変わる。"""
        self.assertFalse([k for k in self.rec["axis1_counts"] if k.startswith("方向 | 数あり")])

    def test_stop_cost_counts(self):
        self.assertEqual(self.rec["stop_cost_counts"],
                         {"結んだ fact の値が文に在る(通る)": 22,
                          "結んだ fact の値が文に無い(止まる恐れ)": 8,
                          "文に金額が無い(影響なし)": 2})

    def test_seat2_sensitivity_is_recorded(self):
        self.assertEqual(self.rec["seat2_direction_rows"], 11)

    def test_the_fixture_is_what_the_script_builds_now(self):
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = T.stage_build()
        self.assertEqual(json.loads(json.dumps(out, ensure_ascii=False)), self.rec)


class DocumentTest(unittest.TestCase):
    """文書の表の数が fixture と離れたら赤くなる。"""

    def setUp(self):
        self.rec = json.load(io.open(CAUSES, encoding="utf-8"))
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        # 表の行を**欄に割って**見る(説明文や隣の表の数に当たらないように)。強調の * は落とす。
        self.rows = []
        for line in self.doc.splitlines():
            t = line.strip()
            if not t.startswith("|"):
                continue
            cells = [c.strip().replace("*", "") for c in t.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            self.rows.append(cells)

    def _row_with(self, label):
        """先頭の欄がその名前そのものである行を返す。部分一致では採らない。"""
        return [r for r in self.rows if r and r[0] == label]

    def test_every_primary_cause_count_is_in_its_own_table_row(self):
        for cause, n in self.rec["cause_counts"].items():
            hit = self._row_with(cause)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (cause, len(hit)))
            self.assertIn(str(n), hit[0][1:], "%s の件数が %d でない: %s" % (cause, n, hit[0]))

    def test_the_cause_counts_in_the_document_add_up_to_twenty(self):
        got = {}
        for cause, n in self.rec["cause_counts"].items():
            got[cause] = int(self._row_with(cause)[0][1])
        self.assertEqual(sum(got.values()), 20)
        self.assertEqual(got, self.rec["cause_counts"])

    def test_the_number_axis_counts_are_in_their_own_table_rows(self):
        for label, n in self.rec["number_axis_counts"].items():
            hit = self._row_with(label)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (label, len(hit)))
            self.assertEqual(hit[0][1], str(n), "%s: %s" % (label, hit[0]))

    def test_the_two_axis_rates_are_in_table_cells_not_only_in_prose(self):
        cells = {c for r in self.rows for c in r}
        for rate in ("5.0%", "35.7%", "27.8%", "38.5%"):
            self.assertIn(rate, cells, "%s が表の欄に無い" % rate)

    def test_the_stop_cost_is_in_its_own_table_rows(self):
        self.assertIn("8 / 32", self.doc)
        for label, n in self.rec["stop_cost_counts"].items():
            hit = self._row_with(label)
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (label, len(hit)))
            self.assertEqual(hit[0][1], str(n), "%s: %s" % (label, hit[0]))

    def test_the_seat2_sensitivity_is_in_the_document(self):
        self.assertIn("%d / 20" % self.rec["seat2_direction_rows"], self.doc)

    def test_the_denominator_is_stated(self):
        self.assertIn("20", self.doc)
        self.assertEqual(self.rec["total"], 20)


if __name__ == "__main__":
    unittest.main()
