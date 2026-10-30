# -*- coding: utf-8 -*-
u"""(d) の封(docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md)を固定する。

**封は実装・測定より先に commit されること**(commit の順で見る)。
**分母は記録と一致すること。予測は 14 本で、外れ方が書かれていること。**
"""
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/XBRL_DIM_HOLD_SEAL_2026-10-17.md"
SEAL = os.path.join(ROOT, SEAL_REL)
FX = os.path.join(ROOT, "fixtures", "xbrl", "cd8")
#: **この封より後に作られるもの**(順序の門。無い間は飛ばす)
AFTER = ("measure/xbrl_dim_hold_2026-10-17.py",
         "fixtures/xbrl/cd8/dim_hold_2026-10-17.json")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rec(name):
    return json.load(io.open(os.path.join(FX, name), encoding="utf-8"))


def sec(t, start, end=None):
    i = t.index("\n" + start)
    return t[i:t.index("\n" + end, i)] if end else t[i:]


class RuleTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_the_five_firing_conditions_are_numbered(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 6)])
        self.assertIn(u"`GROUNDED`", b)
        self.assertIn(u"**要素が同一**", b)
        self.assertIn(u"`_dim_of(ctx)`", b)
        self.assertIn(u"**比較器が使ったものと同じ値**", b)
        self.assertIn(u"`ambiguous_dimension:<件数>`", b)

    def test_2_the_rule_does_not_look_at_whether_a_dimension_exists(self):
        self.assertIn(u"**次元の有無は条件に入らない。**", self.t)
        self.assertIn(u"**曖昧さは対称である**", self.t)
        self.assertIn(u"この規則は**次元の有無を見ない。**", self.t)

    def test_3_the_six_exclusions_are_numbered(self):
        b = sec(self.t, "### §3-1", "### §3-2")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 7)])
        for k in (u"期間だけ違う兄弟", u"単位だけ違う兄弟", u"要素が違う fact",
                  u"`円` の行"):
            self.assertIn(k, b, k)

    def test_4_the_forbidden_actions_are_sealed(self):
        b = sec(self.t, "### §3-2", "## §4")
        self.assertIn(u"**別の fact を正解として選び直さない。**", b)
        self.assertIn(u"**`検査通過` を増やさない。**", b)
        self.assertIn(u"**減らす方向にしか動かない。**", b)
        g = sec(self.t, "## §9")
        self.assertEqual(len(re.findall(r"(?m)^- \*\*", g)), 5)
        self.assertIn(u"**閾値 `tol` を新しく作ること。**", g)

    def test_5_the_state_table_has_exactly_five_rows(self):
        b = sec(self.t, "## §4", "## §5")
        rows = re.findall(r"(?m)^\| (.+?) \| (.+?) \| (.+?) \|$", b)
        rows = [r for r in rows if not set(r[0]) <= set("- ")]
        self.assertEqual(len(rows), 6, rows)      # 見出し + 5 行
        self.assertEqual(sum(1 for r in rows if u"変えない" in r[2]), 4)
        self.assertEqual(sum(1 for r in rows if u"UNVERIFIABLE" in r[2]), 1)


class DenominatorTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.v1 = rec("contract_v1_2026-10-17.json")
        self.sc = rec("score_2026-10-17.json")

    def test_6_the_four_denominators_match_the_records(self):
        named = [x for x in self.sc["rows"] if x[u"席"][u"参照先"]]
        unmod = [x for x in named if not x[u"注入か"]]
        ok = [x for x in unmod if x[u"席"][u"判定"] == u"確認済み"]
        gold = [x for x in self.sc["rows"]
                if (x[u"正解"] or {}).get(u"正解")]
        want = {"D1": self.v1[u"検査通過"][u"**B′**"], "D2": len(named),
                "D3": len(unmod), "D4": len(gold)}
        self.assertEqual(want, {"D1": 24, "D2": 85, "D3": 42, "D4": 50})
        b = sec(self.t, "## §5", "### §5-1")
        for k, v in want.items():
            self.assertIn(u"**%s " % k, b, k)
            self.assertIn(u"| **%d** |" % v, b, (k, v))
        self.assertIn(u"**41**", b)
        self.assertEqual(len(ok), 41)

    def test_7_the_two_parts_are_kept_apart(self):
        b = sec(self.t, "### §5-1", "## §6")
        self.assertIn(u"**第 1 部 規則の適用(状態が変わる)**: **D1 の 24 行だけ。**",
                      b)
        self.assertIn(u"**第 2 部 露出の帯(状態は変えない)**", b)
        self.assertIn(u"**主張の値ではなく参照先の fact 自身の値**", b)

    def test_8_the_three_cost_terms_come_from_the_records(self):
        b = sec(self.t, "## §6", "## §7")
        self.assertEqual(
            self.v1[u"R-2 正しい主張を不一致にした(無改変)"][u"率"][u"分子"], 1)
        self.assertEqual(
            self.v1[u"R-1 誤った参照先を検査通過にした"][u"(a) 検査通過のうち注入"][u"分子"],
            0)
        self.assertIn(u"**1 件**(`R-2`", b)
        self.assertIn(u"**0 件**(`R-1` 0/24)", b)
        self.assertIn(u"**この規則で精度が上がることは、この標本では示せない。**", b)
        self.assertIn(u"**結果をそう読まない読み方(「改善した」)はこの封で禁じる。**", b)


class PredictionTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)
        self.b = sec(self.t, "## §7", "## §8")

    def test_9_there_are_fourteen_fields_each_with_a_way_to_fail(self):
        rows = re.findall(r"(?m)^\| \*\*(D-\d+)\*\* \| (.+?) \| (.+?) \|$",
                          self.b)
        self.assertEqual([r[0] for r in rows],
                         ["D-%d" % i for i in range(1, 15)],
                         [r[0] for r in rows])
        for sym, pred, how in rows:
            self.assertTrue(pred.strip(), sym)
            self.assertTrue(how.strip() and how.strip() != u"―", sym)

    def test_10_the_numbers_derived_from_committed_records_are_exact(self):
        d = rec("dim_diag_2026-10-17.json")
        n6 = len(d["rows"])
        n18 = d[u"**候補規則 (b) の帯(規則にはしない)**"][
            u"参照先が個別(NonConsolidated)の枠"]
        self.assertIn(u"D1 24 行での発火 = **%d 行**" % n6, self.b)
        self.assertIn(u"**24 → %d 行**" % (24 - n6), self.b)
        self.assertIn(u"**個別の枠を指した %d 行は 0 件発火**" % n18, self.b)

    def test_11_the_bands_can_fail_and_carry_a_point_estimate(self):
        for sym in ("D-5", "D-6", "D-7"):
            line = [l for l in self.b.splitlines() if l.startswith(u"| **%s"
                                                                   % sym)][0]
            self.assertRegex(line, r"\d+〜\d+")
            self.assertIn(u"点推定", line)
            self.assertIn(u"帯の外", line)

    def test_12_the_controls_are_failure_injections(self):
        self.assertIn(u"**D-10・D-11 は故障を作って当てる対照である**", self.b)
        self.assertIn(u"guard-that-only-fires-on-failure", self.b)
        self.assertIn(u"**正常な材料では除外条件は黙るので、", self.b)

    def test_13_no_improvement_is_promised(self):
        b = sec(self.t, "## §8")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 8)])
        self.assertIn(u"**発火した行が誤った参照先だったとは言えない。**", b)
        self.assertIn(u"**この規則は精度を上げない見込みである**", b)
        self.assertIn(u"**保留は誤りの指摘ではない。**", b)
        self.assertIn(u"**要素そのものを取り違える問題(T5)は別の課題として残る。**", b)
        self.assertIn(u"**これは本番の拒否規則ではない。**", b)
        self.assertIn(u"**軸情報の保持((e))はこの封に入らない。**", b)

    def test_14_the_seal_declares_no_implementation(self):
        head = self.t[:self.t.index(u"## §1")]
        self.assertIn(u"**この封は判定仕様と事前予測だけを固定する。**", head)
        self.assertIn(u"**engine を変更しない。実装するかどうかは、"
                      u"この封の commit の後に人間が決める。**", head)
        self.assertIn(u"**0 USD・席は呼ばない。**", head)


class OrderTest(unittest.TestCase):
    u"""**封が実装・測定より先に commit されたこと**を commit の順で見る。"""

    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A",
                              "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True)
        lines = out.stdout.decode().split()
        return lines[-1] if lines else None

    def test_15_the_seal_is_committed_before_what_it_seals(self):
        seal = self._added(SEAL_REL)
        self.assertIsNotNone(seal, u"封が commit されていない")
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertEqual(
                subprocess.run(["git", "merge-base", "--is-ancestor", seal,
                                other], cwd=ROOT,
                               capture_output=True).returncode, 0, rel)


if __name__ == "__main__":
    unittest.main()
