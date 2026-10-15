"""段 4 の engine を**報告文が存在する前に**固定する(封 §0 の ⑤)。

材料は手で書いた文だけ。実際の報告文はまだ生成していない。
守るのは 4 つ。
  1. 金額の表記から円の値と**書かれた桁**が出ること
  2. 切り出しの規則(主語の手がかり・重複の畳み込み・判定不能)
  3. ルートの順(**下位が上位を置き換えない**)
  4. **範囲の証拠が無い一致を `GROUNDED` にしないこと**
"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "sheet_m4_engine_2026-10-15.py")

spec = importlib.util.spec_from_file_location("m4e", SCRIPT)
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def entry(name, scope, column, value, level="款", children=None, ref="D10"):
    return {"scope": scope, "level": level, "name": name, "code": "01", "column": column,
            "value": value, "file": "決算書 歳出", "children": children,
            "evidence": {"scope_from": "表題行", "code_ref": "A10", "name_ref": "B10",
                         "value_ref": ref, "header_ref": "D7"}}


VOCAB = [("一般会計", "一般会計"), ("議会費", "議会費"), ("都議会費", "都議会費"),
         ("総務費", "総務費")]
VOCAB.sort(key=lambda kv: -len(kv[0]))


class AmountTest(unittest.TestCase):
    def test_plain_yen(self):
        self.assertEqual(E.amount_value("8,962,754,865,176", None), (8962754865176, 1))

    def test_unit_suffix(self):
        self.assertEqual(E.amount_value("1,234", "百万"), (1234000000, 10 ** 6))
        self.assertEqual(E.amount_value("500", "千"), (500000, 10 ** 3))

    def test_concatenated_units(self):
        v, scale = E.amount_value("2兆1,234億", None)
        self.assertEqual(v, 2 * 10 ** 12 + 1234 * 10 ** 8)
        self.assertEqual(scale, 10 ** 8)

    def test_the_written_scale_is_the_smallest_written_place(self):
        """帯の単位は**書かれた桁**。末尾の 0 から作らない(XBRL で踏んだ型)。"""
        self.assertEqual(E.amount_value("100", "百万")[1], 10 ** 6)


class ExtractTest(unittest.TestCase):
    def test_a_claim_gets_its_nearest_preceding_name(self):
        c = E.extract_claims("一般会計の歳出決算額は8,724,585,235,292円でした。", VOCAB)
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["subject"], "一般会計")
        self.assertEqual(c[0]["column"], "歳出決算額")
        self.assertEqual(c[0]["value"], 8724585235292)
        self.assertTrue(c[0]["scorable"])

    def test_a_number_without_any_name_is_not_scorable(self):
        c = E.extract_claims("合計で1,000円の増加がありました。", VOCAB)
        self.assertEqual(len(c), 1)
        self.assertFalse(c[0]["scorable"])

    def test_duplicates_of_the_same_triple_collapse(self):
        c = E.extract_claims("議会費は100円。議会費は100円。", VOCAB)
        self.assertEqual(len(c), 1)

    def test_two_names_in_one_sentence_are_marked_undecidable(self):
        c = E.extract_claims("議会費と都議会費は5,314,472,000円です。", VOCAB)
        self.assertTrue(c[0]["undecidable"])

    def test_a_number_that_is_not_money_is_ignored(self):
        self.assertEqual(E.extract_claims("一般会計の款は37件あります。", VOCAB), [])


class RouteTest(unittest.TestCase):
    def test_r1_binds_an_exact_cell(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4802993869)]
        c = E.extract_claims("議会費の支出済額は4,802,993,869円です。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertEqual((b["route"], b["state"]), ("R-1", "GROUNDED"))
        self.assertTrue(b["range_identified"] and b["value_match"])
        self.assertEqual(b["pointer"], "sheet:決算書 歳出!D10")

    def test_r3_binds_a_sum_only_when_no_cell_matches(self):
        kids = [{"name": "a", "value": 3, "value_ref": "D12"},
                {"name": "b", "value": 4, "value_ref": "D15"}]
        ents = [entry("議会費", "一般会計", "支出済額", 99, children=kids)]
        c = E.extract_claims("議会費の支出済額は7円です。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertEqual((b["route"], b["state"]), ("R-3", "GROUNDED"))
        self.assertEqual(b["evidence"]["included"], ["D12", "D15"])
        self.assertEqual(b["evidence"]["excluded"][0]["why"], "親自身の値(二重計上の防止)")

    def test_r1_wins_over_r3(self):
        """**下位のルートが上位を置き換えない**(欠陥 A で踏んだ型)。"""
        kids = [{"name": "a", "value": 5, "value_ref": "D12"},
                {"name": "b", "value": 5, "value_ref": "D15"}]
        ents = [entry("議会費", "一般会計", "支出済額", 10, children=kids)]
        c = E.extract_claims("議会費の支出済額は10円です。", VOCAB)[0]
        self.assertEqual(E.bind(c, ents)["route"], "R-1")

    def test_r4_needs_a_written_place_and_stays_within_one_unit(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4802993869)]
        c = E.extract_claims("議会費の支出済額は48億円です。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertEqual((b["route"], b["state"]), ("R-4", "GROUNDED"))
        far = E.extract_claims("議会費の支出済額は60億円です。", VOCAB)[0]
        self.assertEqual(E.bind(far, ents)["state"], "VALUE_MISMATCH")

    def test_r4_stops_at_one_written_unit(self):
        """帯は**1 単位**。2 倍に広げると通る値を、ここで止める。

        「48億円」に対し 4,950,000,000 は丸めで 1.5 単位ずれ、切り捨てでも 1.5 単位。
        帯を 2 倍にすると通ってしまう(欠陥 A で踏んだ型)。
        """
        ents = [entry("議会費", "一般会計", "支出済額", 4950000000)]
        c = E.extract_claims("議会費の支出済額は48億円です。", VOCAB)[0]
        self.assertEqual(E.bind(c, ents)["state"], "VALUE_MISMATCH")

    def test_r4_accepts_inside_the_truncate_band(self):
        ents = [entry("議会費", "一般会計", "支出済額", 4890000000)]
        c = E.extract_claims("議会費の支出済額は48億円です。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertEqual((b["route"], b["state"]), ("R-4", "GROUNDED"))

    def test_r4_never_fires_for_a_plain_yen_amount(self):
        """円まで書かれた数に帯は無い(1 円の帯で近いだけの一致を作らない)。"""
        ents = [entry("議会費", "一般会計", "支出済額", 4802993869)]
        c = E.extract_claims("議会費の支出済額は4,802,993,870円です。", VOCAB)[0]
        self.assertEqual(E.bind(c, ents)["state"], "VALUE_MISMATCH")


class EvidenceTest(unittest.TestCase):
    def test_a_value_only_hit_is_never_grounded(self):
        """封 §3・仕様 §4 / 人間の指示 3。値が合っても範囲の証拠が無ければ結ばない。"""
        ents = [entry("総務費", "一般会計", "支出済額", 1234)]
        c = E.extract_claims("この事業には1,234円を支出しました。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertFalse(b["range_identified"])
        self.assertTrue(b["value_match"])
        self.assertEqual(b["state"], "UNVERIFIABLE")

    def test_no_name_and_no_value_is_pointer_not_found(self):
        ents = [entry("総務費", "一般会計", "支出済額", 1234)]
        c = E.extract_claims("この事業には9,999円を支出しました。", VOCAB)[0]
        self.assertEqual(E.bind(c, ents)["state"], "POINTER_NOT_FOUND")

    def test_a_grounded_bind_carries_the_full_evidence(self):
        ents = [entry("議会費", "一般会計", "支出済額", 7)]
        c = E.extract_claims("議会費の支出済額は7円です。", VOCAB)[0]
        ev = E.bind(c, ents)["evidence"]
        for k in ("scope", "level", "name", "column", "name_ref", "value_ref", "header_ref"):
            self.assertIn(k, ev)

    def test_the_column_cue_narrows_the_candidates(self):
        ents = [entry("議会費", "一般会計", "支出済額", 10),
                entry("議会費", "一般会計", "不用額", 20, ref="G10")]
        c = E.extract_claims("議会費の不用額は20円です。", VOCAB)[0]
        b = E.bind(c, ents)
        self.assertEqual(b["evidence"]["column"], "不用額")
        self.assertEqual(b["pointer"], "sheet:決算書 歳出!G10")

    def test_r2_is_not_implemented_because_this_material_has_no_formula(self):
        src = open(SCRIPT, encoding="utf-8").read()
        self.assertIn("R-2 式が示す範囲        … この材料には式が無いので**走らない**", src)


if __name__ == "__main__":
    unittest.main()
