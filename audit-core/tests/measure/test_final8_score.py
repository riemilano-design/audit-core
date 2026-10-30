"""最終評価用 8 書類の採点器(measure/final8_score_2026-10-14.py)のうち、封 §4 の
N-3 を決める 2 つの関数と、材料の漏れ検査を、合成の行で固定する。"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _load(name):
    p = os.path.join(ROOT, "measure", name)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").replace(".py", ""), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = _load("final8_score_2026-10-14.py")
M = _load("final8_material_2026-10-14.py")

CTX = {"D": {
    "CurrentYearInstant_NonConsolidatedMember": {"members": ["jppfs_cor:NonConsolidatedMember"]},
    "CurrentYearInstant_SegAMember": {"members": ["jppfs_cor:NonConsolidatedMember", "x:SegAMember"]},
    "Prior1YearInstant_NonConsolidatedMember": {"members": ["jppfs_cor:NonConsolidatedMember"]},
}}


def row(arm, label, state="GROUNDED", strict=False):
    return {"id": "D:H-001", "state": state, "strict": strict, "arm": arm, "label": label}


class E2MemberTest(unittest.TestCase):
    def test_same_element_different_member_is_counted(self):
        r = row([("Assets", "CurrentYearInstant_NonConsolidatedMember")], [("Assets", "CurrentYearInstant_SegAMember")])
        self.assertEqual(1, len(S.e2_member_rows([r], CTX)))

    def test_same_element_different_period_same_member_is_not_member_mismatch(self):
        r = row([("Assets", "CurrentYearInstant_NonConsolidatedMember")], [("Assets", "Prior1YearInstant_NonConsolidatedMember")])
        self.assertEqual([], S.e2_member_rows([r], CTX))

    def test_different_element_is_not_member_mismatch(self):
        r = row([("Assets", "CurrentYearInstant_NonConsolidatedMember")], [("Liabilities", "CurrentYearInstant_SegAMember")])
        self.assertEqual([], S.e2_member_rows([r], CTX))

    def test_strict_match_or_not_grounded_is_skipped(self):
        a = [("Assets", "CurrentYearInstant_NonConsolidatedMember")]
        self.assertEqual([], S.e2_member_rows([row(a, a, strict=True)], CTX))
        self.assertEqual([], S.e2_member_rows([row(a, [("Assets", "CurrentYearInstant_SegAMember")], state="VALUE_MISMATCH")], CTX))


class UAbsentTest(unittest.TestCase):
    def _labels(self, reasons, cls="判定不能(両側)"):
        return {"labels": [{"id": "D:H-001", "分類": cls, "判定不能の理由": reasons}]}

    def test_both_absent_and_grounded_is_counted(self):
        dump = {"D:H-001": {"state": "GROUNDED", "pointers": ["xbrl:jppfs_cor:Assets@CurrentYearInstant_NonConsolidatedMember"]}}
        self.assertEqual(1, len(S.u_absent_rows(self._labels([S.ABSENT, S.ABSENT]), dump)))

    def test_one_seat_with_another_reason_is_not_counted(self):
        dump = {"D:H-001": {"state": "GROUNDED", "pointers": []}}
        self.assertEqual([], S.u_absent_rows(self._labels([S.ABSENT, "その他"]), dump))

    def test_not_grounded_is_not_counted(self):
        dump = {"D:H-001": {"state": "POINTER_NOT_FOUND", "pointers": []}}
        self.assertEqual([], S.u_absent_rows(self._labels([S.ABSENT, S.ABSENT]), dump))

    def test_confirmed_row_is_never_counted_here(self):
        dump = {"D:H-001": {"state": "GROUNDED", "pointers": []}}
        self.assertEqual([], S.u_absent_rows(self._labels([S.ABSENT, S.ABSENT], cls="確定(同値類v0)"), dump))


class LeakCheckTest(unittest.TestCase):
    def test_banned_word_in_commander_prose_is_found(self):
        self.assertEqual(1, len(M.leaks(["この行は P16 で判定した"])))

    def test_document_text_is_outside_the_check(self):
        mat = {"purpose": "x", "欄の意味": {}, "元データ": {},
               "行": [{"docID": "S1", "文": "連結売上高は単体の GROUNDED"}]}
        self.assertEqual([], M.leaks(M.commander_prose(mat)))

    def test_the_banned_list_names_the_two_profiles_and_the_classification_words(self):
        for w in ("P16", "P20", "連結", "単体", "GROUNDED", "pointer"):
            self.assertIn(w, M.BANNED)


if __name__ == "__main__":
    unittest.main()
