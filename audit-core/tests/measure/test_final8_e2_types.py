"""E2 の型の分類(measure/final8_e2_types_2026-10-14.py)を固定する。

結果文書 §1-2 の内訳が、commit された code から再現できることを門にする
(独立監査 2026-10-14 の指摘: 当初は使い捨ての script で出していた)。
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


T = _load("final8_e2_types_2026-10-14.py")
RESULT = os.path.join(ROOT, "docs", "FINAL_EVAL_8_RESULT_2026-10-14.md")
TYPES = os.path.join(ROOT, "fixtures", "xbrl", "final8", "e2_types_2026-10-14.json")

CTX = {
    "plain_cur": {"members": []},
    "plain_pri": {"members": []},
    "seg_cur": {"members": ["x:SegAMember"]},
    "seg_pri": {"members": ["x:SegAMember"]},
}


def row(arm, label):
    return {"id": "D:H-001", "state": "GROUNDED", "strict": False, "arm": arm, "label": label}


class ClassifyTest(unittest.TestCase):
    def test_alias_only_difference_is_A(self):
        r = row([("TotalAssetsSummaryOfBusinessResults", "plain_cur")], [("Assets", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("A"))

    def test_same_element_different_member_is_B(self):
        r = row([("NetSales", "plain_cur")], [("NetSales", "seg_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("B"))

    def test_same_element_different_period_same_member_is_C(self):
        r = row([("NetSales", "plain_cur")], [("NetSales", "plain_pri")])
        self.assertTrue(T.classify(r, CTX).startswith("C"))

    def test_same_context_different_element_is_D(self):
        r = row([("OperatingIncome", "plain_cur")], [("NetSales", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("D"))

    def test_same_element_fewer_facts_is_C_not_E(self):
        # 要素が同じで context の集合が違えば、件数が違っても C が先に当たる。
        # (実データでは C は 0 件だった ― この形は 1 件も出ていない)
        r = row([("NetSales", "plain_cur"), ("NetSales", "plain_pri")], [("NetSales", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("C"))

    def test_different_element_and_different_count_is_E(self):
        # E は「要素も context も違い、かつ結んだ件数が違う」行。
        r = row([("NetSales", "plain_cur"), ("NetSales", "plain_pri")], [("OperatingIncome", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("E"))

    def test_different_element_same_context_is_D_even_with_extra_fact(self):
        r = row([("NetSales", "plain_cur"), ("OperatingIncome", "plain_cur")], [("NetSales", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("D"))

    def test_element_and_period_both_differ_is_F(self):
        r = row([("OperatingIncome", "plain_cur")], [("NetSales", "seg_pri")])
        self.assertTrue(T.classify(r, CTX).startswith("F"))

    def test_the_order_puts_alias_before_member(self):
        # 別名でもあり member も違う行は A に入る(順が逆だと B に落ちる)
        r = row([("TotalAssetsSummaryOfBusinessResults", "plain_cur")], [("Assets", "plain_cur")])
        self.assertTrue(T.classify(r, CTX).startswith("A"))


class WrittenTypesMatchTheDocumentTest(unittest.TestCase):
    """記録した json の内訳が、結果文書の表の数と字で合っていること。"""

    def setUp(self):
        with io.open(TYPES, encoding="utf-8") as fh:
            self.types = json.load(fh)
        with io.open(RESULT, encoding="utf-8") as fh:
            self.doc = fh.read()

    def test_the_total_is_the_sum_of_the_kinds(self):
        self.assertEqual(self.types["total"], sum(self.types["counts"].values()))
        self.assertEqual(self.types["total"], len(self.types["rows"]))

    def test_every_kind_count_appears_in_the_document_table(self):
        # 表の行だけを見る(自分の説明文に当たらないように)。強調の * は落として比べる。
        rows = [l.replace("*", "") for l in self.doc.splitlines() if l.strip().startswith("|")]
        found = 0
        for kind, n in self.types["counts"].items():
            if n == 0:
                continue
            letter = kind[0]
            hit = [l for l in rows if l.lstrip("| ").startswith(letter) and ("| %d |" % n) in l]
            self.assertTrue(hit, "型 %s の %d 件が §1-2 の表に無い" % (letter, n))
            found += 1
        self.assertEqual(5, found, "0 件でない型は 5 つ(A B D E F)")

    def test_the_direction_split_is_recorded_per_row(self):
        d = sum(1 for r in self.types["rows"] if r["direction"])
        self.assertEqual(20, d, "方向の形の E2 は 20 件(結果文書 §1-3)")
        self.assertEqual(18, self.types["total"] - d)
