"""未解決事項の台帳(docs/XBRL_OPEN_ISSUES_2026-10-15.md)が記録と食い違わないことを門にする。

台帳は過去の測定の引き写しである。**引き写しが間に合わなくなる**のがいちばん起きやすい
欠陥なので、台帳の各行の数を**その数が在る fixture**に突き合わせる。
"""
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "xbrl")
DOC = os.path.join(ROOT, "docs", "XBRL_OPEN_ISSUES_2026-10-15.md")


def _j(*p):
    return json.load(io.open(os.path.join(FX, *p), encoding="utf-8"))


class LedgerTest(unittest.TestCase):
    def setUp(self):
        with io.open(DOC, encoding="utf-8") as fh:
            self.doc = fh.read()
        self.rows = [[c.strip() for c in l.strip().strip("|").split("|")]
                     for l in self.doc.splitlines() if l.strip().startswith("|")]
        self.body = [r for r in self.rows if r and r[0].isdigit()]

    def _row(self, n):
        hit = [r for r in self.body if r[0] == str(n)]
        self.assertEqual(len(hit), 1, "# %s の行が %d 本" % (n, len(hit)))
        return hit[0]

    def test_the_ledger_has_eight_numbered_rows(self):
        self.assertEqual([r[0] for r in self.body], [str(i) for i in range(1, 9)])

    def test_every_row_has_one_of_the_three_states(self):
        for r in self.body:
            state = r[2].replace("*", "")
            self.assertIn(state, ("未採用", "未測定", "未解決"), r[:3])

    def test_row1_matches_the_structure_and_impact_fixtures(self):
        st = _j("final8", "defect_a_structure_2026-10-14.json")
        imp = _j("defect_a", "used_docs_impact_2026-10-14.json")["result"]["P20"]
        sc = _j("defect_a", "score_2026-10-14.json")
        cells = " ".join(self._row(1))
        self.assertIn("%d 件" % st["money_mismatch_rows"], cells)
        self.assertIn("**%d 件(27%%)**" % st["diagnostic_count"], cells)
        self.assertIn("%d 件を動かし" % sc["L_A"], cells)
        self.assertIn("%d 件奪った" % imp["other"], cells)

    def test_row3_keeps_the_four_versus_four(self):
        cells = " ".join(self._row(3))
        self.assertIn("E2 4 件 / E1' 4 件", cells)
        self.assertIn("止める信号に使えない", cells)

    def test_row4_matches_the_causes_fixture(self):
        dc = _j("final8", "direction_causes_2026-10-14.json")
        a1 = dc["axis1_counts"]
        e2 = a1["方向 | 数なし | E2"]
        g = e2 + a1["方向 | 数なし | E1'"]
        cells = " ".join(self._row(4))
        self.assertIn("%d / %d = 38.5%%" % (e2, g), cells)
        self.assertIn("%d 件" % (a1["値の形 | 数あり | E1'"] + a1["値の形 | 数あり | E2"]), cells)

    def test_row5_matches_the_score_condition_counts(self):
        sc = _j("defect_a", "score_2026-10-14.json")
        n = sc["condition_counts"]["4 つの条件はすべて満たす"]
        self.assertIn("**%d 件すべてが 4 条件を満たす**" % n, " ".join(self._row(5)))

    def test_row7_matches_the_seat_order_number(self):
        dc = _j("final8", "direction_causes_2026-10-14.json")
        self.assertIn("**%d / 20**" % dc["seat2_direction_rows"], " ".join(self._row(7)))

    def test_the_resolved_item_is_kept_out_of_the_ledger(self):
        st = _j("final8", "defect_a_structure_2026-10-14.json")
        n = st["scale_agreement"]["claim_scale == 書かれた桁"]
        self.assertIn("**%d / 464**" % n, self.doc)
        self.assertNotIn("claim_scale", " ".join(" ".join(r) for r in self.body))

    def test_the_ledger_records_the_reopen_condition_as_a_spec_first(self):
        self.assertIn("優先関係を仕様として定義し直す", self.doc)
        self.assertIn("order[34:]", self.doc)

    def test_the_ledger_does_not_claim_safety(self):
        self.assertIn("どれも「直せば安全になる」とは書いていない", self.doc)


if __name__ == "__main__":
    unittest.main()
