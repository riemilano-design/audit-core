# -*- coding: utf-8 -*-
"""席の答えの凍結(封 docs/DOMAIN1_M11_SEAL_2026-10-16.md §7)を固定する。

**やり直しをしない**ので、**落ちた答えの扱い**が採点の一部になる。
守るのは 8 つ。
  1. 正しい答えはそのまま通る
  2. **欄が欠けた答えは「判定不能」に倒れ、落ちた件として記録される**
  3. **答えが無い id は「判定不能」に倒れる**(黙って減らさない)
  4. 一覧に無い id・同じ id の 2 回目は落とす
  5. **値が文字列(カンマつき)なら整数に直し、直したことを記録する**
  6. 値が整数に直せなければ「判定不能」に倒す
  7. 記録に「**再生成しない**」が在ること
  8. 記録の答えの数が**一覧の数と必ず同じ**になること(倒した分を含む)
"""
import importlib.util
import io
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


GOOD = {"id": "R001", "会計": "一般会計", "階層": "項", "親": "総務費",
        "科目名": "子供政策連携費", "列": "予算現額", "値": 10169000000}


class CheckHasTeethTest(unittest.TestCase):
    def setUp(self):
        self.m = _mod("m11ans_t", "sheet_m11_freeze_answers_2026-10-16.py")

    def test_1_a_good_answer_passes(self):
        ok, bad = self.m.check([GOOD], {"R001"})
        self.assertEqual(bad, [])
        self.assertEqual(ok, [dict(GOOD)])

    def test_2_a_missing_field_falls_to_unknown(self):
        a = dict(GOOD)
        del a["列"]
        ok, bad = self.m.check([a], {"R001"})
        self.assertEqual(ok, [{"id": "R001", "verdict": "判定不能"}])
        self.assertEqual(len(bad), 1)
        self.assertIn("欄が欠けている: 列", bad[0]["理由"])

    def test_3_a_missing_id_falls_to_unknown(self):
        ok, bad = self.m.check([GOOD], {"R001", "R002"})
        self.assertEqual(len(ok), 2)
        self.assertIn({"id": "R002", "verdict": "判定不能"}, ok)
        self.assertTrue(any("**答えが無い**" in b["理由"] for b in bad))

    def test_4_unknown_and_duplicate_ids_are_dropped(self):
        ok, bad = self.m.check([GOOD, dict(GOOD), dict(GOOD, id="R999")], {"R001"})
        self.assertEqual(len(ok), 1)
        reasons = [b["理由"] for b in bad]
        self.assertIn("同じ id が 2 回", reasons)
        self.assertIn("一覧に無い id", reasons)

    def test_5_a_string_value_is_converted_and_recorded(self):
        ok, bad = self.m.check([dict(GOOD, 値="10,169,000,000円")], {"R001"})
        self.assertEqual(ok[0]["値"], 10169000000)
        self.assertEqual(len(bad), 1)
        self.assertIn("整数に直した", bad[0]["理由"])

    def test_6_an_unparsable_value_falls_to_unknown(self):
        ok, bad = self.m.check([dict(GOOD, 値="およそ百億")], {"R001"})
        self.assertEqual(ok, [{"id": "R001", "verdict": "判定不能"}])
        self.assertIn("値が整数でない", bad[0]["理由"])

    def test_7_a_verdict_answer_passes_through(self):
        ok, bad = self.m.check([{"id": "R001", "verdict": "判定不能"}], {"R001"})
        self.assertEqual(ok, [{"id": "R001", "verdict": "判定不能"}])
        self.assertEqual(bad, [])

    def test_8_the_count_always_matches_the_list(self):
        want = {"R001", "R002", "R003"}
        ok, _ = self.m.check([GOOD, {"id": "R002", "verdict": "根拠なし"}], want)
        self.assertEqual(len(ok), len(want), "倒した分を含めて数が合わない")
        self.assertEqual({a["id"] for a in ok}, want)


class FrozenRecordTest(unittest.TestCase):
    """答えの記録が在れば、**再生成していないこと**と数を固定する。"""

    def _recs(self):
        out = []
        for seat in ("seat1", "seat2"):
            p = os.path.join(FX, "m11_answers_%s_2026-10-16.json" % seat)
            if os.path.exists(p):
                out.append((seat, load(p)))
        return out

    def test_9_no_regeneration_and_blind(self):
        recs = self._recs()
        if not recs:
            self.skipTest("答えがまだ無い")
        want = {c["id"] for c in load(os.path.join(FX, "m11_binds_2026-10-16.json"))
                ["claims"] if not c.get("skipped")}
        for seat, r in recs:
            self.assertTrue(r["blind"], seat)
            self.assertEqual(r["runs"], 1, seat)
            self.assertFalse(r["regenerated"], seat)
            self.assertIn("再生成しない", r["落ちた件の扱い"])
            self.assertEqual({a["id"] for a in r["answers"]}, want, seat)
        if len(recs) == 2:
            self.assertNotEqual(recs[0][1]["model"], recs[1][1]["model"],
                                "2 席が同じ model になっている")


if __name__ == "__main__":
    unittest.main()
