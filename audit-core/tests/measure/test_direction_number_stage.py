"""方向の主張に数が付かなかった理由の処理段分け(measure/direction_number_stage_2026-10-14.py)を固定する。

``classify`` 段は commit 済みの fixture と facts だけで回る(ZIP は要らない)ので、
ここで門にできる。``extract`` 段は取得済み ZIP が要るため門にしない。
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


T = _load("direction_number_stage_2026-10-14.py")
BASE = os.path.join(ROOT, "fixtures", "xbrl", "final8")
SIB = os.path.join(BASE, "direction_siblings_2026-10-14.json")
OUT = os.path.join(BASE, "direction_number_stage_2026-10-14.json")
DOC = os.path.join(ROOT, "docs", "DIRECTION_CAUSES_2026-10-14.md")


class PrecisionTest(unittest.TestCase):
    """許容は「書かれた数の桁」から取る。単位の記号から取ると取りこぼす。"""

    def test_a_number_written_to_the_million_place(self):
        self.assertEqual(T.precision(257000000.0), 10 ** 6)

    def test_a_number_written_to_the_thousand_place(self):
        self.assertEqual(T.precision(14816000.0), 10 ** 3)

    def test_an_exact_number_has_no_slack(self):
        self.assertEqual(T.precision(214611001.0), 1)

    def test_zero_does_not_divide_forever(self):
        self.assertEqual(T.precision(0.0), 1)


class ClassifySiblingTest(unittest.TestCase):
    """A → B → C → D の順を固定する。順を変えたら赤くなる。"""

    FACTS = [{"要素": "jppfs_cor:NetSales", "context": "CurrentYearDuration_SegBMember", "値": 9648249000.0},
             {"要素": "jppfs_cor:OperatingIncome", "context": "CurrentYearDuration", "値": 640909000.0}]

    def _row(self, stated, delta, elements):
        return {"stated": stated, "direction_delta": delta, "direction_elements": elements}

    def test_a_difference_is_A_even_though_another_fact_would_match(self):
        r = self._row(640909000.0, 640909000.0, ["NetSales"])
        self.assertEqual(T.classify_sibling(r, self.FACTS), "A")

    def test_the_same_element_in_another_frame_is_B(self):
        r = self._row(9648000000.0, None, ["NetSales"])
        self.assertEqual(T.classify_sibling(r, self.FACTS), "B")

    def test_another_element_is_C(self):
        r = self._row(640909000.0, None, ["GrossProfit"])
        self.assertEqual(T.classify_sibling(r, self.FACTS), "C")

    def test_no_matching_fact_is_D(self):
        r = self._row(777000000.0, None, ["GrossProfit"])
        self.assertEqual(T.classify_sibling(r, self.FACTS), "D")

    def test_A_is_taken_before_B_when_both_would_match(self):
        """差でもあり、同じ要素の別の枠の値でもある数。順を入れ替えたら赤くなる。
        この標本には両方に当たる行が 1 件も無いので、実物では順を測れない。"""
        facts = [{"要素": "jppfs_cor:NetSales", "context": "Prior1YearDuration", "値": 500000000.0}]
        r = self._row(500000000.0, 500000000.0, ["NetSales"])
        self.assertEqual(T.classify_sibling(r, facts), "A")

    def test_B_is_taken_before_C_when_both_would_match(self):
        facts = self.FACTS + [{"要素": "jppfs_cor:Other", "context": "CurrentYearInstant", "値": 9648100000.0}]
        r = self._row(9648000000.0, None, ["NetSales"])
        self.assertEqual(T.classify_sibling(r, facts), "B")

    def test_the_tolerance_comes_from_the_written_digits(self):
        """2億57百万円(百万円の桁)は差 258,000,000 に当たる。円の桁で比べたら当たらない。"""
        r = self._row(257000000.0, 258000000.0, ["NetAssets"])
        self.assertEqual(T.classify_sibling(r, []), "A")


class RecordedCountsTest(unittest.TestCase):
    def setUp(self):
        self.rec = json.load(io.open(OUT, encoding="utf-8"))
        self.sib = json.load(io.open(SIB, encoding="utf-8"))

    def test_the_fifty_two_direction_rows_are_covered(self):
        self.assertEqual(len(self.sib["rows"]), 52)
        self.assertEqual(sum(self.rec["sibling_presence"].values()), 52)
        self.assertEqual(sum(1 for r in self.sib["rows"] if r["e2"]), 20)

    def test_sibling_presence(self):
        p = self.rec["sibling_presence"]
        self.assertEqual(p["E2 | 在る → VALUE_MISMATCH(engine 自身が落としていた)"], 7)
        self.assertEqual(p["E1' | 在る → VALUE_MISMATCH(engine 自身が落としていた)"], 12)
        self.assertEqual(p["E2 | 同じ文・同じ fact の金額の主張が無い"], 9)
        self.assertEqual(p["E1' | 同じ文・同じ fact の金額の主張が無い"], 3)

    def test_the_bad_sibling_kinds_separate_the_stages(self):
        k = self.rec["bad_sibling_kinds"]
        self.assertEqual(k["E1' | " + T.KINDS["A"]], 8)
        self.assertEqual(k["E2 | " + T.KINDS["B"]], 3)
        self.assertEqual(k["E2 | " + T.KINDS["C"]], 4)
        self.assertEqual(k["E1' | " + T.KINDS["C"]], 4)
        self.assertEqual(sum(k.values()), 19)

    def test_defect_A_never_appears_on_a_wrong_row(self):
        """A は engine 自身の止めすぎの誤りなので、E2(通してしまった行)には出ない。"""
        self.assertNotIn("E2 | " + T.KINDS["A"], self.rec["bad_sibling_kinds"])

    def test_defect_B_never_appears_on_a_correct_row(self):
        """B だけが E2 に偏る(この標本では費用 0)。偏りが崩れたら赤くなる。"""
        self.assertNotIn("E1' | " + T.KINDS["B"], self.rec["bad_sibling_kinds"])

    def test_the_money_claim_census(self):
        c = self.rec["money_claim_census"]
        self.assertEqual(c["全体 | VALUE_MISMATCH"], 110)
        self.assertEqual(c["全体 | GROUNDED"], 295)
        self.assertEqual(c["VALUE_MISMATCH の中身 | 文の数は『差』だった(欠陥 A)"], 30)
        self.assertEqual(c["VALUE_MISMATCH の中身 | 差でもない"], 74)
        self.assertEqual(c["VALUE_MISMATCH の中身 | 対になる期間の fact が無い"], 6)
        self.assertEqual(sum(v for k, v in c.items() if k.startswith("VALUE_MISMATCH")), 110)

    def test_the_fixture_is_what_the_script_builds_now(self):
        """**本物の fixture には書かせない。**変異を回したときに記録が上書きされるため
        (2026-10-14 に実際に汚した)。出力先を一時ファイルへ向けて比べる。"""
        import contextlib
        import tempfile
        keep = T.OUT
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            tmp = fh.name
        try:
            T.OUT = tmp
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                out = T.stage_classify()
        finally:
            T.OUT = keep
            os.unlink(tmp)
        self.assertEqual(json.loads(json.dumps(out, ensure_ascii=False)), self.rec)

    def test_the_document_states_the_stage_numbers(self):
        with io.open(DOC, encoding="utf-8") as fh:
            doc = fh.read()
        rows = [[c.strip().replace("*", "") for c in l.strip().strip("|").split("|")]
                for l in doc.splitlines() if l.strip().startswith("|")]
        for label, e2, e1 in ((T.KINDS["A"], "0", "8"), (T.KINDS["B"], "3", "0"), (T.KINDS["C"], "4", "4")):
            hit = [r for r in rows if r and r[0] == label]
            self.assertEqual(len(hit), 1, "%s の行が %d 本" % (label, len(hit)))
            self.assertEqual(hit[0][1:3], [e2, e1], "%s: %s" % (label, hit[0]))
        self.assertIn("30", doc)


if __name__ == "__main__":
    unittest.main()
