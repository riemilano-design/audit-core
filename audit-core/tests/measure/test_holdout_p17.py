# -*- coding: utf-8 -*-
"""封じた引きと測定の数を**追跡されているファイルだけ**で留める。

2026-10-14 の独立監査は GO だったが、申し送りが 1 つあった: **この 2 本の道具に試験が
無い**。原則「一回限りの手の実測は門ではない」。この測定は別の母集団で回し直す見込みが
あるので(単体決算の落とし込みを直した後)、ここで試験にする。

``~/.cache`` の ZIP は追跡されていないので読まない([[test-must-not-read-ignored-material]]
と同じ理由)。留めるのは (1) 引きが封の算法で再現すること、(2) 行の対応づけの道具の
振る舞い、(3) 結果の数が字で固定されていること。
"""

import importlib.util
import io
import json
import os
import random
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIX = os.path.join(ROOT, "fixtures", "xbrl", "holdout_p17")
MEASURE = os.path.join(ROOT, "measure")

_spec = importlib.util.spec_from_file_location(
    "holdout_p17_pair", os.path.join(MEASURE, "holdout_p17_pair_2026-10-14.py"))
PAIR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PAIR)

SEED_HEX = "6a24d72"      # 封 §2。**字で留める**(定数から作ると変異が黙る)
DRAWN = ("S100YYQX", "S100Z3LJ", "S100Z3IZ", "S100Z3H2", "S100YXLE", "S100Z3L6")
LABELED = ("S100YYQX", "S100Z3LJ", "S100Z3IZ")


def _load(name):
    with io.open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return json.load(fh)


class DrawReproducibilityTest(unittest.TestCase):
    """**封 §9-2 の算法で、誰でも同じ 6 件に辿り着く。**"""

    def test_six_documents_reproduce_from_the_sealed_algorithm(self):
        pool = sorted(_load("pool2_clean_2026-10-14.json")["pool_clean"])
        self.assertEqual(len(pool), 256, "母集団の件数が封 §9-1 と違う")
        rng = random.Random(int(SEED_HEX, 16))
        order = list(pool)
        rng.shuffle(order)
        self.assertEqual(tuple(order[:6]), DRAWN)

    def test_the_committed_draw_matches(self):
        drawn = _load("drawn2_2026-10-14.json")
        self.assertEqual(tuple(d["docID"] for d in drawn["drawn"]), DRAWN)
        self.assertEqual(tuple(drawn["labeled"]), LABELED)
        self.assertEqual(drawn["seed_hex"], SEED_HEX)
        self.assertEqual(drawn["skipped"], [], "繰り上げが 0 件でなくなっている")

    def test_a_different_seed_gives_a_different_draw(self):
        """種が結果を決めていること(算法が種を無視していたら落ちる)。"""

        pool = sorted(_load("pool2_clean_2026-10-14.json")["pool_clean"])
        other = list(pool)
        random.Random(int("deadbee", 16)).shuffle(other)
        self.assertNotEqual(tuple(other[:6]), DRAWN)


class PairingToolTest(unittest.TestCase):
    """行の対応づけ ― **id ではなく中身の鍵**。重複は数える。"""

    def test_key_uses_content_not_id(self):
        a = {"id": "N001", "kind": "num", "form": "point", "subject": "売上高",
             "value": 1.0, "unit": "円", "word": None, "span": "x"}
        b = dict(a, id="N999")
        self.assertEqual(PAIR.key_of(a), PAIR.key_of(b), "id が鍵に入っている")
        c = dict(a, value=2.0)
        self.assertNotEqual(PAIR.key_of(a), PAIR.key_of(c))

    def test_duplicate_keys_are_counted_not_hidden(self):
        rows = [{"id": "N1", "kind": "num", "form": "point", "subject": "s",
                 "value": 1.0, "unit": "円", "word": None, "span": "x", "state": "GROUNDED"}]
        rows.append(dict(rows[0], id="N2", state="VALUE_MISMATCH"))
        idx, dup = PAIR.index_claims(rows)
        self.assertEqual(len(idx), 1)
        self.assertEqual(dup, 1, "後勝ちで潰れた件数が報告されていない")

    def test_rate_does_not_divide_by_zero(self):
        self.assertIsNone(PAIR.rate(0, 0))
        self.assertAlmostEqual(PAIR.rate(1, 4), 25.0)


class SealedNumbersTest(unittest.TestCase):
    """**結果の数を字で留める。**(docs/HOLDOUT_P17_RESULT_2026-10-14.md §2)"""

    def setUp(self):
        self.r = _load("pair_P16_P17_2026-10-14.json")

    def test_claims_and_grounded(self):
        a = self.r["all_rows"]
        self.assertEqual((a["P16"]["claims"], a["P17"]["claims"]), (742, 742))
        self.assertEqual((a["P16"]["grounded"], a["P17"]["grounded"]), (287, 293))

    def test_common_rows_and_the_three_gates(self):
        self.assertEqual(self.r["common_rows"]["n"], 712)
        self.assertEqual(self.r["A1_broke"], 0)                    # A-1 合格線 5 以下
        self.assertEqual(self.r["A2_grounded_diff_all"], 6)        # A-2 合格線 減らない
        self.assertEqual(self.r["A2_grounded_diff_common"], 2)
        self.assertAlmostEqual(self.r["A3_stopped_pct_drop_all"], 0.0, places=6)
        self.assertAlmostEqual(self.r["A3_stopped_pct_drop_common"], 0.0, places=6)

    def test_two_documents_grounded_nothing(self):
        """§4 の限界 ― 連結を作っていない会社で 0 件。**件数を留める。**"""

        zero = [d for d in self.r["per_doc"] if d["states_P16_all"].get("GROUNDED", 0) == 0]
        self.assertEqual(len(zero), 2)
        self.assertEqual(sorted(d["doc"] for d in zero), ["S100YXLE", "S100Z3LJ"])
        self.assertEqual(sum(d["claims_P16"] for d in zero), 249)


if __name__ == "__main__":
    unittest.main()
