# -*- coding: utf-8 -*-
"""段 7 の engine(封 §2 の P-1〜P-7)を固定する。

材料は**手で書いた文と手で作った索引**。実際の報告文での診断は別の script。
守るのは 7 つ。
  1. P-1 答えの親は**索引の欄**から来る(文の字をそのまま使わない)
  2. P-3 手がかりは区間の中だけ。**引き継がない**
  3. P-4 成分が**全部**揃わなければ支持しない
  4. P-5 **支持が無ければ絞らない**(款と項の双子は保留のまま)
  5. P-6 絞った後も 6 欄が 1 通りでなければ保留。**値で選ばない**
  6. P-7 保留でも親の記録が付く
  7. 旧 engine と**親以外の欄が同値**(新しい差を作っていない)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NEW = os.path.join(ROOT, "measure", "sheet_m7_engine_2026-10-15.py")
OLDP = os.path.join(ROOT, "measure", "sheet_m5_engine_2026-10-15.py")
REPORT = os.path.join(ROOT, "fixtures", "sheet", "m6_report_2026-10-15.json")


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = _mod("m7e", NEW)
O = _mod("m5e_for_t7", OLDP)


def entry(name, scope, column, value, level="目", parent=None, ref="D10", file="事項別明細"):
    return {"scope": scope, "level": level, "name": name, "code": "01", "column": column,
            "value": value, "file": file, "children": None, "parent": parent,
            "evidence": {"scope_from": "表題行", "code_ref": "A10", "name_ref": "B10",
                         "value_ref": ref, "header_ref": "D7"}}


VOCAB = sorted({"一般会計": "一般会計", "保健医療費": "保健医療費",
                "都立病院支援費": "都立病院支援費", "管理費": "管理費",
                "総務費": "総務費", "総務管理費": "総務管理費",
                "都営住宅等事業会計": "都営住宅等事業会計",
                "都営住宅等事業費": "都営住宅等事業費"}.items(),
               key=lambda kv: -len(kv[0]))
CUES = {"支出済額": "支出済額", "不用額": "不用額", "予算現額": "予算現額"}


def claims_of(text):
    return E.extract_claims(text, VOCAB, CUES)


class ComponentTest(unittest.TestCase):
    def test_a_row_without_a_parent_has_no_components(self):
        self.assertEqual(E.parent_components(None), [])
        self.assertEqual(E.parent_components(""), [])

    def test_a_kou_parent_has_one_component_and_a_moku_parent_two(self):
        self.assertEqual(E.parent_components("保健医療費"), ["保健医療費"])
        self.assertEqual(E.parent_components("保健医療費 > 都立病院支援費"),
                         ["保健医療費", "都立病院支援費"])


class CueSpanTest(unittest.TestCase):
    def test_the_cue_is_taken_from_the_span_before_the_subject(self):
        c = claims_of("一般会計では、保健医療費「都立病院支援費」(管理費)の"
                      "支出済額が100円でした。")
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["subject"], "管理費")
        self.assertEqual(c[0]["parent_cues"],
                         ["一般会計", "保健医療費", "都立病院支援費"])

    def test_the_cue_is_not_carried_over_to_the_next_amount(self):
        """**P-3。**②(引き継ぎ)へ侵入していないことの門。"""
        c = claims_of("保健医療費「都立病院支援費」(管理費)の支出済額は100円、"
                      "不用額は200円です。")
        self.assertEqual(len(c), 2)
        self.assertEqual(c[0]["parent_cues"], ["保健医療費", "都立病院支援費"])
        self.assertEqual(c[1]["parent_cues"], [], "2 つ目の金額に手がかりが残っている")

    def test_a_name_after_the_subject_is_not_a_cue(self):
        c = claims_of("管理費は、保健医療費より100円多い")
        self.assertEqual(c[0]["subject"], "保健医療費")
        self.assertEqual(c[0]["parent_cues"], ["管理費"])

    def test_no_names_means_no_cue(self):
        c = claims_of("支出済額は100円です")
        self.assertEqual(c[0]["parent_cues"], [])


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.ents = [
            entry("管理費", "一般会計", "支出済額", 100,
                  parent="保健医療費 > 都立病院支援費", ref="D10"),
            entry("管理費", "一般会計", "支出済額", 900,
                  parent="総務費 > 総務管理費", ref="D20"),
            entry("管理費", "一般会計", "支出済額", 700,
                  parent="教育費 > 教育管理費", ref="D30"),
        ]

    def test_p4_needs_every_component(self):
        """款だけ名指しても絞らない(**目の親は 2 成分**)。"""
        c = claims_of("保健医療費の管理費の支出済額は100円")
        kept, info = E.narrow_by_parent(c[0], self.ents)
        self.assertFalse(info["parent_filtered"])
        self.assertEqual(len(kept), 3)

    def test_p4_filters_when_both_components_are_named(self):
        c = claims_of("保健医療費「都立病院支援費」(管理費)の支出済額は100円")
        kept, info = E.narrow_by_parent(c[0], self.ents)
        self.assertTrue(info["parent_filtered"])
        self.assertEqual(info["parent_kept"], ["保健医療費 > 都立病院支援費"])
        self.assertEqual([e["evidence"]["value_ref"] for e in kept], ["D10"])

    def test_the_filter_binds_and_the_answer_comes_from_the_index(self):
        """**P-1。**答えの親は索引の字(` > ` つき)で、文の書き方に依らない。"""
        c = claims_of("保健医療費「都立病院支援費」(管理費)の支出済額は100円")
        b = E.bind(c[0], self.ents)
        self.assertEqual((b["state"], b["route"]), ("GROUNDED", "R-1"))
        self.assertEqual(b["evidence"]["parent"], "保健医療費 > 都立病院支援費")
        self.assertEqual(b["pointer"], "sheet:事項別明細!D10")

    def test_p6_holds_when_the_parent_leaves_two_keys(self):
        """封 §1 の 262 行の型。**正しい親でも一意にならないなら保留。**"""
        ents = [entry("管理費", "一般会計", "支出済額", 100,
                      parent="保健医療費 > 都立病院支援費", ref="D10"),
                entry("管理費", "一般会計", "支出済額", 100, level="項",
                      parent="保健医療費", ref="D11")]
        c = claims_of("保健医療費「都立病院支援費」(管理費)の支出済額は100円")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("6 欄が一意でない", b["hold_reason"])
        self.assertTrue(b["parent_filtered"])

    def test_the_value_never_breaks_a_tie_after_filtering(self):
        """2 つ残ったとき、**片方だけ値が一致していても結ばない。**"""
        ents = [entry("管理費", "一般会計", "支出済額", 100,
                      parent="保健医療費 > 都立病院支援費", ref="D10"),
                entry("管理費", "一般会計", "支出済額", 555, level="項",
                      parent="保健医療費", ref="D11")]
        c = claims_of("保健医療費「都立病院支援費」(管理費)の支出済額は100円")
        self.assertEqual(E.bind(c[0], ents)["state"], "UNVERIFIABLE")


class P5Test(unittest.TestCase):
    """**P-5 = ① と ② を分ける線。**ここが緩むと款に結んでしまう。"""

    def setUp(self):
        self.ents = [
            entry("都営住宅等事業費", "都営住宅等事業会計", "支出済額", 100,
                  level="款", parent=None, ref="D10", file="決算書 歳出"),
            entry("都営住宅等事業費", "都営住宅等事業会計", "支出済額", 100,
                  level="項", parent="都営住宅等事業費", ref="D11", file="決算書 歳出"),
        ]

    def test_a_parentless_row_does_not_become_the_default(self):
        c = claims_of("都営住宅等事業会計の都営住宅等事業費の支出済額は100円")
        self.assertEqual(c[0]["parent_cues"], ["都営住宅等事業会計"])
        kept, info = E.narrow_by_parent(c[0], self.ents)
        self.assertFalse(info["parent_filtered"], "支持が無いのに絞っている")
        self.assertEqual(len(kept), 2)

    def test_the_kan_kou_twin_still_holds(self):
        c = claims_of("都営住宅等事業会計の都営住宅等事業費の支出済額は100円")
        b = E.bind(c[0], self.ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("6 欄が一意でない", b["hold_reason"])

    def test_the_new_engine_does_not_differ_from_the_old_one_here(self):
        """②の領域では**旧と同じ**であること。"""
        c_old = O.extract_claims("都営住宅等事業会計の都営住宅等事業費の支出済額は100円",
                                 VOCAB, CUES)
        b_old = O.bind(c_old[0], self.ents)
        c_new = claims_of("都営住宅等事業会計の都営住宅等事業費の支出済額は100円")
        b_new = E.bind(c_new[0], self.ents)
        self.assertEqual((b_old["state"], b_old["hold_reason"]),
                         (b_new["state"], b_new["hold_reason"]))


class InheritedGuardTest(unittest.TestCase):
    """旧が持っていた守りを、新が**落としていない**こと(変異 E8 が黙った穴)。"""

    def setUp(self):
        self.ents = [entry("管理費", "一般会計", "支出済額", 100,
                           parent="保健医療費 > 都立病院支援費")]

    def test_it_does_not_escape_to_another_level(self):
        """K-3。階層の手がかりが在り、その階層に候補が 0 件なら**保留**。"""
        c = claims_of("項別の管理費の支出済額は100円")
        self.assertEqual(c[0]["level"], "項")
        b = E.bind(c[0], self.ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("階層 項 に候補が 0 件", b["hold_reason"])
        self.assertIn("他の階層へ落ちない", b["hold_reason"])

    def test_the_same_guard_fires_in_the_old_engine_too(self):
        c = O.extract_claims("項別の管理費の支出済額は100円", VOCAB, CUES)
        b = O.bind(c[0], self.ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("階層 項 に候補が 0 件", b["hold_reason"])

    def test_a_value_only_hit_is_still_never_grounded(self):
        c = claims_of("この事業には100円を支出しました")
        b = E.bind(c[0], self.ents)
        self.assertFalse(b["range_identified"])
        self.assertEqual(b["state"], "UNVERIFIABLE")
        self.assertIn("値だけでは結ばない", b["hold_reason"])


class P7RecordTest(unittest.TestCase):
    def test_the_parent_record_is_present_even_when_held(self):
        ents = [entry("管理費", "一般会計", "支出済額", 100,
                      parent="保健医療費 > 都立病院支援費"),
                entry("管理費", "一般会計", "不用額", 200,
                      parent="保健医療費 > 都立病院支援費", ref="E10")]
        c = claims_of("保健医療費「都立病院支援費」(管理費)は100円")
        b = E.bind(c[0], ents)
        self.assertEqual(b["state"], "UNVERIFIABLE")
        for k in ("parent_cues", "parent_filtered", "parent_kept",
                  "parent_before", "parent_after"):
            self.assertIn(k, b, k)
        self.assertEqual((b["parent_before"], b["parent_after"]), (2, 2))
        self.assertTrue(b["parent_filtered"])

    def test_the_record_is_present_on_a_skipped_claim_too(self):
        c = claims_of("■ 会計別決算(表１)")
        b = E.bind(c[0], [])
        self.assertIn("parent_cues", b)
        self.assertEqual(b["state"], "UNVERIFIABLE")


class ParityTest(unittest.TestCase):
    """**親以外は旧と同値。**新しい差を黙って作っていないことの門。"""

    def setUp(self):
        with io.open(REPORT, encoding="utf-8") as fh:
            self.text = json.load(fh)["report"]

    def test_extract_is_identical_except_for_the_new_field(self):
        a = O.extract_claims(self.text, VOCAB, CUES)
        b = E.extract_claims(self.text, VOCAB, CUES)
        self.assertEqual(len(a), len(b))
        seen_new = 0
        for x, y in zip(a, b):
            extra = set(y) - set(x)
            if x.get("skipped"):
                self.assertEqual(extra, set(), "飛ばした行に欄が増えている")
            else:
                self.assertEqual(extra, {"parent_cues"})
                seen_new += 1
            for k in x:
                self.assertEqual(x[k], y[k], "%s の %s が違う" % (x["id"], k))
        self.assertEqual(seen_new, 25, "parent_cues が付いた主張の数")

    def test_the_old_engine_file_is_not_imported_as_a_copy(self):
        """新は旧を**import して使う**(写しを作らない)。"""
        src = io.open(NEW, encoding="utf-8").read()
        self.assertIn('OLD = _mod("m5_for_m7", "sheet_m5_engine_2026-10-15.py")', src)
        self.assertIn("**旧 engine(`sheet_m5_engine_2026-10-15.py`)は 1 byte も変えない。**",
                      src)

    def test_the_constants_are_taken_from_the_old_engine_not_redefined(self):
        """字で書き直していないこと(値の一致 + `OLD.` から取っている字)。"""
        src = io.open(NEW, encoding="utf-8").read()
        for k in ("LEVEL_CUES", "MASK_WORDS", "FIELDS6", "MIN_INDEPENDENT"):
            self.assertEqual(getattr(E, k), getattr(O, k), k)
            self.assertIn("OLD.%s" % k, src, "%s を旧から取っていない" % k)
        for k in ("LEVEL_CUES =", "MASK_WORDS =", "FIELDS6 ="):
            self.assertNotIn("\n%s (" % k, src, "%s を字で書き直している" % k)


if __name__ == "__main__":
    unittest.main()
