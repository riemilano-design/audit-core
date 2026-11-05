# -*- coding: utf-8 -*-
"""J(封 docs/XBRL_INJECT_TYPES_SEAL_2026-11-05.md)の測定 script ``measure/xbrl_jtypes_2026-11-05.py`` の**行の欄**の試験(J の第 1 便の独立監査の宿題。T9 の封 §2-1)。

J の便では、行の欄 ``round-trip``・``読み直し``・``先頭の位が減った`` を固定値にする変異が、標本の行(標本の記録に手で書いた行)では黙った
(標本の行は欄を script から作らないので、script の欄の組み立てを壊しても標本の記録は変わらない)。この file は script の ``inject_text_j`` を小さい入力(zip・判定は偽。lib は本物)で通し、
欄を**壊した差し替え(文を変える・値を変える・位を落とす)で True ↔ False が替わる例**で固定する。J の script・J の門 2 本は 1 byte も変えない。

  1. ``reread_j``: 同じ start・指定の単位・意図した値の token が在るときだけ True。値・単位・start のどれが違っても False。
  2. ``NS.groups_in``(先頭の位の数): 兆・億・万の数 + 1。
  3. round-trip の欄: ``IJ.revert`` が元の文を返さない差し替えで False(全部の型)。
  4. 読み直しの欄: ``IJ.apply_edits`` が別の値・別の単位を書く差し替えで False(全部の型)。round-trip の欄は動かない。
  5. 先頭の位が減った欄: T6・T7 の複合で位が減る行だけ True。減らない行・T2 の行・既存の行は False。固定値(常に False / 常に True)の変異で赤。
"""
import collections
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "core", "py"))
sys.path.insert(0, os.path.join(ROOT, "measure"))


def load_module(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


JR = load_module("tests/measure/test_xbrl_jtypes_result.py", "jtypes_result_gate_for_rows")        # fake_verify_for・run_procedure・Patch・TEXT_P・REFS_P の部品。門としては走らせない
JT = JR.JT
NS = JT.NS
IJ, N, TUNE = JT.IJ, JT.N, JT.TUNE
Patch = JR.Patch
run_procedure = JR.run_procedure
TEXT_P, REFS_P = JR.TEXT_P, JR.REFS_P

#: 位が落ちる複合: 現在の値が 1億500万円(億 + 万の 2 組)、前期の値が 9,700万円(1 組)。T6 の複合の写しはこの形を site にする
TEXT_L = u"売上高は1億500万円でした。粗利益は1,234百万円でした。費用は5,000千円でした。"
REFS_L = [{"key": "jppfs:NetSales@CurrentYearDuration", "value": 105000000.0, "unit": u"円", "label": u"売上高"},
          {"key": "jppfs:NetSales@Prior1YearDuration", "value": 97000000.0, "unit": u"円", "label": u"売上高"}] + REFS_P[2:]


def tok_of(text, unit):
    with JT.yen_scan_on():
        return [t for t in N.scan(text) if t.unit == unit][0]


class RereadTest(unittest.TestCase):
    def test_1_reread_needs_the_same_start_unit_and_value(self):
        text = u"売上高は12億3,456万円でした。"
        with JT.yen_scan_on():
            tok = tok_of(text, u"万円")
            self.assertEqual(123456.0, tok.value)
            self.assertTrue(JT.reread_j(text, tok, 123456.0, u"万円"))
            self.assertFalse(JT.reread_j(text, tok, 123457.0, u"万円"))                     # 値が違う
            self.assertFalse(JT.reread_j(text, tok, 123456.0, u"千円"))                     # 単位が違う
            self.assertFalse(JT.reread_j(text, tok, 123456.0, None))
            moved = u"総売上高は12億3,456万円でした。"                                       # start が 1 字ずれる
            self.assertFalse(JT.reread_j(moved, tok, 123456.0, u"万円"))
            self.assertTrue(JT.reread_j(moved, tok_of(moved, u"万円"), 123456.0, u"万円"))
            broken = text.replace(u"万円", u"")                                              # 単位が消えた文
            self.assertFalse(JT.reread_j(broken, tok, 123456.0, u"万円"))
            other = text.replace(u"12億3,456", u"12億3,457")                                # 値が書き換わった文
            self.assertFalse(JT.reread_j(other, tok, 123456.0, u"万円"))
            self.assertTrue(JT.reread_j(other, tok, 123457.0, u"万円"))
            self.assertTrue(JT.reread_j(text, tok, 123456.0 + 1e-10, u"万円"))              # 許容(1e-9)の内
            self.assertFalse(JT.reread_j(text, tok, 123456.0 + 1e-6, u"万円"))

    def test_2_groups_in_counts_the_big_unit_marks_plus_one(self):
        self.assertEqual(1, NS.groups_in(u"9,700"))
        self.assertEqual(2, NS.groups_in(u"1億500"))
        self.assertEqual(2, NS.groups_in(u"12億3,456"))
        self.assertEqual(2, NS.groups_in(u"5万"))
        self.assertEqual(3, NS.groups_in(u"1兆2億3,456"))
        self.assertEqual(4, NS.groups_in(u"1兆2億3万4"))
        self.assertEqual(1, NS.groups_in(u""))


class RoundTripAndRereadColumnTest(unittest.TestCase):
    TYPES = ("T2_UNIT", "T6_PRIOR", "T7_ROUND")

    def rows(self, patches=(), text=TEXT_P, refs=REFS_P):
        rows, _c = run_procedure(text=text, refs=refs, patches=patches)
        return rows

    def test_3_the_honest_rows_have_true_in_both_columns_for_every_type(self):
        rows = self.rows()
        self.assertEqual(set(self.TYPES), set(r[u"型"] for r in rows))
        self.assertTrue(rows)
        for r in rows:
            self.assertIs(True, r[u"round-trip"], r)
            self.assertIs(True, r[u"読み直し"], r)

    def test_4_round_trip_is_false_when_revert_does_not_give_the_original_back(self):
        real = IJ.revert
        for broken in (lambda tampered, chosen, placements, original: tampered,                                       # 戻さない
                       lambda tampered, chosen, placements, original: real(tampered, chosen, placements, original) + u"。",     # 余分な字
                       lambda tampered, chosen, placements, original: real(tampered, chosen, placements, original)[1:]):      # 字が欠ける
            rows = self.rows(patches=((IJ, "revert", broken),))
            self.assertTrue(rows)
            self.assertEqual(set(self.TYPES), set(r[u"型"] for r in rows))
            self.assertTrue(all(r[u"round-trip"] is False for r in rows), [r[u"round-trip"] for r in rows])
            self.assertTrue(all(r[u"読み直し"] is True for r in rows))                  # 読み直しの欄は動かない(別の欄)
        self.assertTrue(all(r[u"round-trip"] is True for r in self.rows()))

    def test_5_reread_is_false_when_apply_edits_writes_another_value_or_unit(self):
        real = IJ.apply_edits

        def other_value(text, chosen):
            return real(text, [dict(c, replacement=u"9" + c["replacement"]) for c in chosen])            # 先頭に 1 字足して値を変える

        def drop_the_unit(text, chosen):
            out, pl = real(text, chosen)
            for u in (u"百万円", u"万円", u"千円"):
                out = out.replace(u, u"", 1)
            return out, pl
        for broken in (other_value, drop_the_unit):
            rows = self.rows(patches=((IJ, "apply_edits", broken),))
            self.assertTrue(rows)
            self.assertTrue(any(r[u"読み直し"] is False for r in rows), broken.__name__)
            if broken is other_value:
                self.assertTrue(all(r[u"round-trip"] is True for r in rows), broken.__name__)   # round-trip は revert が元の字を持つので別の欄
        rows = self.rows(patches=((IJ, "apply_edits", other_value),))
        self.assertTrue(all(r[u"読み直し"] is False for r in rows))                               # 先頭に 1 字足せば全部の型で値が変わる
        self.assertTrue(all(r[u"読み直し"] is True for r in self.rows()))

    def test_5b_reread_follows_the_unit_after_for_t2(self):
        rows = self.rows()
        t2 = [r for r in rows if r[u"型"] == "T2_UNIT"]
        self.assertTrue(t2)
        for r in t2:
            self.assertIsNotNone(r[u"単位の後"])
            self.assertTrue(r[u"読み直し"])                                                       # T2 は後の単位で読み直す(元の単位では読めない)


class LeadingGroupColumnTest(unittest.TestCase):
    def rows(self, text, refs, patches=()):
        rows, _c = run_procedure(text=text, refs=refs, patches=patches)
        return rows

    def test_6_only_a_compound_that_loses_its_leading_group_is_true(self):
        rows = self.rows(TEXT_L, REFS_L)
        by_type = collections.defaultdict(list)
        for r in rows:
            by_type[r[u"型"]].append(r)
        t6 = by_type["T6_PRIOR"]
        self.assertEqual(1, len(t6))
        self.assertEqual((u"複合", True, True), (t6[0][u"形"], t6[0][u"先頭の位が減った"], t6[0][u"読み直し"]))        # 1億500万円 → 9,700万円
        for r in by_type["T7_ROUND"] + by_type["T2_UNIT"]:
            self.assertIs(False, r[u"先頭の位が減った"], r)                                     # 値 ±1・単位替えは位を落とさない
        self.assertTrue(by_type["T7_ROUND"] and by_type["T2_UNIT"])

    def test_7_rows_that_keep_their_groups_are_false(self):
        rows = self.rows(JR.TEXT_P, JR.REFS_P)
        self.assertTrue(rows)
        self.assertEqual([False] * len(rows), [r[u"先頭の位が減った"] for r in rows])

    def test_8_a_constant_column_is_caught_by_the_two_populations(self):
        u"""固定値の変異(常に False / 常に True)は、位が落ちる複合の行(True)と落ちない行(False)の両方を持つ入力で必ず赤になる。"""
        rows = self.rows(TEXT_L, REFS_L)
        values = set(r[u"先頭の位が減った"] for r in rows)
        self.assertEqual({True, False}, values)

    def test_9_the_column_reads_the_group_count_of_the_replacement_not_of_the_original(self):
        u"""置換の字の位の数が元より少ないときだけ True。groups_in を差し替えた(常に 1 / 常に元と同じ)変異で行が動く。"""
        for fake in (lambda s: 1, lambda s: 9):
            rows = self.rows(TEXT_L, REFS_L, patches=((NS, "groups_in", fake),))
            t6 = [r for r in rows if r[u"型"] == "T6_PRIOR"]
            self.assertEqual(1, len(t6))
            self.assertEqual(fake(u"x") < 2, t6[0][u"先頭の位が減った"])
        rows = self.rows(TEXT_L, REFS_L)
        self.assertEqual([True], [r[u"先頭の位が減った"] for r in rows if r[u"型"] == "T6_PRIOR"])


if __name__ == "__main__":
    unittest.main()
