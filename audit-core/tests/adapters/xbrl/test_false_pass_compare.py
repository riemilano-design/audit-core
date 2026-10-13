# -*- coding: utf-8 -*-
"""``measure/false_pass_compare_2026-10-15.py`` ― **比較可能かの検査そのもの**を留める。

人間の指摘(2026-10-14)「P16 と P18 の分母・誤りの種類・評価条件が比較可能である
ことが前提」。道具は 3 つを機械で確かめる。ここで留めるのは「**崩れている入力を
本当に落とすか**」。落とさない検査は、在っても守りにならない
(記憶「正常な入力では発火しない守りは、故障を作って当てないと測れない」)。
"""

import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # tests/adapters/xbrl -> repo
TOOL = os.path.join(ROOT, "measure", "false_pass_compare_2026-10-15.py")

_spec = importlib.util.spec_from_file_location("false_pass_compare_tool", TOOL)
CMP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CMP)


def _row(cid, new, outcome):
    return {"id": cid, "new": new, "outcome": outcome}


def _run(doc, profile, kind, rows, batch=1):
    return {"doc": doc, "profile": profile, "kind": kind, "batch": batch, "rows": list(rows)}


def _report(a_ids, b_ids, a_pass=(), b_pass=(), batch=1, newmap=None):
    """``a_ids`` ⊆ ``b_ids`` の 1 書類ぶんの合成入力。"""

    newmap = newmap or {}
    rep = []
    for kind in ("V1", "V2"):
        rep.append(_run("D1", "P16", kind,
                        [_row(i, newmap.get((i, kind, "P16"), i + kind),
                              "PASSED" if (i, kind) in a_pass else "detected:VALUE_MISMATCH")
                         for i in a_ids], batch))
        rep.append(_run("D1", "P18", kind,
                        [_row(i, newmap.get((i, kind, "P18"), i + kind),
                              "PASSED" if (i, kind) in b_pass else "detected:VALUE_MISMATCH")
                         for i in b_ids], batch))
    return rep


class ComparableTest(unittest.TestCase):
    def test_accepts_a_well_formed_pair(self):
        by = CMP.index(_report(["N1", "N2"], ["N1", "N2", "N3"]))
        ok, problems, detail = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertTrue(ok, problems)
        self.assertEqual(problems, [])
        self.assertEqual(detail["D1"]["common"], 2)
        self.assertTrue(detail["D1"]["a_subset_of_b"])

    def test_refuses_when_batch_is_not_one(self):
        """**まとめて変えた run は比べない。**(丸めの判定が動いて互いを汚す)"""

        by = CMP.index(_report(["N1"], ["N1"], batch=25))
        ok, problems, _ = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("batch" in p for p in problems), problems)

    def test_refuses_when_the_mutated_text_differs(self):
        """**同じ行に同じ字を当てていなければ件数は比べられない。**"""

        by = CMP.index(_report(["N1"], ["N1"], newmap={("N1", "V1", "P18"): "ちがう字"}))
        ok, problems, _ = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("変えた字" in p for p in problems), problems)

    def test_refuses_when_v1_and_v2_cover_different_rows(self):
        """**1 行に 1 通りだけ当てた版は比べない。**(限界の型が標本から外れる)"""

        rep = _report(["N1", "N2"], ["N1", "N2"])
        for r in rep:
            if r["profile"] == "P16" and r["kind"] == "V2":
                r["rows"] = r["rows"][:1]
        ok, problems, _ = CMP.check_comparable(CMP.index(rep), ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("両方当てた版でない" in p for p in problems), problems)

    def test_broken_row_sets_do_not_raise(self):
        """**崩れた入力で例外を投げない。**（投げる道具は「比較できない」と言えない。
        2026-10-15 に実測: 行の集合が崩れた合成の入力で KeyError になった）"""

        rep = _report(["N1", "N2"], ["N1", "N2"])
        for r in rep:
            if r["profile"] == "P16" and r["kind"] == "V2":
                r["rows"] = r["rows"][:1]
        ok, problems, _ = CMP.check_comparable(CMP.index(rep), ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("この行が無い" in p for p in problems), problems)

    def test_refuses_when_a_run_is_missing(self):
        rep = [r for r in _report(["N1"], ["N1"]) if not (r["profile"] == "P18" and r["kind"] == "V2")]
        ok, problems, _ = CMP.check_comparable(CMP.index(rep), ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("run が無い" in p for p in problems), problems)


    def test_missing_kind_field_does_not_raise(self):
        """**欄が欠けた古い出力で例外を投げない。**（``--kinds`` を足す前の版には ``kind`` が無い。2026-10-15 に実物で KeyError）"""

        rep = _report(["N1"], ["N1"])
        for r in rep:
            del r["kind"]
        by = CMP.index(rep)   # ここで落ちない
        ok, problems, _ = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertFalse(ok)
        self.assertTrue(any("run が無い" in p for p in problems), problems)

class TallyTest(unittest.TestCase):
    def test_counts_common_and_extra_separately(self):
        """**増えた行で通した件数を、揃えた分母の中に混ぜない。**"""

        rep = _report(["N1", "N2"], ["N1", "N2", "N3"],
                      a_pass=[("N1", "V2"), ("N2", "V2")],
                      b_pass=[("N1", "V2"), ("N3", "V1")])
        by = CMP.index(rep)
        ok, _problems, detail = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertTrue(ok)
        acc = CMP.tally(by, ["D1"], "P16", "P18", detail)
        self.assertEqual(acc["common_n"], 4)        # 共通 2 行 × 2 通り
        self.assertEqual(acc["a_all_n"], 4)
        self.assertEqual(acc["b_all_n"], 6)         # 3 行 × 2 通り
        self.assertEqual(acc["b_extra_n"], 2)       # 増えた 1 行 × 2 通り
        self.assertEqual(acc["a_common"], 2)
        self.assertEqual(acc["b_common"], 1)        # N3 の 1 件は共通に数えない
        self.assertEqual(acc["b_all"], 2)
        self.assertEqual(acc["b_extra"], 1)

    def test_extra_rows_passing_is_visible(self):
        """増えた行だけで通した場合、揃えた分母の率は 0 でも ``b_extra`` が立つ。"""

        rep = _report(["N1"], ["N1", "N9"], b_pass=[("N9", "V1"), ("N9", "V2")])
        by = CMP.index(rep)
        ok, _p, detail = CMP.check_comparable(by, ["D1"], "P16", "P18")
        self.assertTrue(ok)
        acc = CMP.tally(by, ["D1"], "P16", "P18", detail)
        self.assertEqual(acc["b_common"], 0)
        self.assertEqual(acc["b_extra"], 2)


class RealInputTest(unittest.TestCase):
    """**実物の測定(batch=1)で、人間が前提にした 3 点が通ること。**"""

    def setUp(self):
        if not os.path.exists(CMP.DEFAULT_IN):
            self.skipTest("測定の出力が無い: %s" % CMP.DEFAULT_IN)
        self.rep = CMP.load(CMP.DEFAULT_IN)
        self.by = CMP.index(self.rep)
        self.docs = sorted(set(r["doc"] for r in self.rep))

    def test_p16_and_p18_are_comparable_on_the_real_measurement(self):
        ok, problems, detail = CMP.check_comparable(self.by, self.docs, "P16", "P18")
        self.assertTrue(ok, problems)
        for doc in self.docs:
            self.assertTrue(detail[doc]["a_subset_of_b"], doc)

    def test_the_published_numbers(self):
        """**公表する数を字で留める。**(21/340 と 4/340、増えた 66 回で 0 件)"""

        ok, _p, detail = CMP.check_comparable(self.by, self.docs, "P16", "P18")
        self.assertTrue(ok)
        acc = CMP.tally(self.by, self.docs, "P16", "P18", detail)
        self.assertEqual(acc["common_n"], 340)
        self.assertEqual(acc["a_common"], 21)
        self.assertEqual(acc["b_common"], 4)
        self.assertEqual(acc["b_all_n"], 406)
        self.assertEqual(acc["b_extra_n"], 66)
        self.assertEqual(acc["b_extra"], 0)


if __name__ == "__main__":
    unittest.main()
