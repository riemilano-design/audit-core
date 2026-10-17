# -*- coding: utf-8 -*-
"""封 v2 の採点器の門。**欠けの分岐を故障入力で当てる**(再監査の「未確認」に応える)。"""
import importlib.util
import io
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "measure", "xbrl_cd_score_2026-10-17.py")
PRE = {"Core": {u"言うこと": u"確認済み", u"参照先": u"a@c1"},
       u"D′": {u"言うこと": u"確認済み", u"参照先": u"b@c2"},
       u"D″": {u"言うこと": u"確認済み", u"参照先": u"b@c2"}}


def _mod():
    sp = importlib.util.spec_from_file_location("cd_score", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class MissingBranchTest(unittest.TestCase):
    """spec §7。**正常な入力では発火しない守りなので、故障を作って当てる。**"""

    def setUp(self):
        self.S = _mod()

    def test_1_four_failure_modes_all_become_missing_in_every_arm(self):
        for bad in (None, {"id": "R001"},
                    {"id": "R001", u"判定": u"たぶん誤り"},
                    {"id": "R001", u"判定": u"確認済み", u"参照先": u"へんな形"},
                    {"id": "R001", u"判定": u"確認済み", u"参照先": 12345}):
            seat = self.S.seat_row(bad)
            arms = self.S.arms_of(seat, PRE)
            for name, arm in arms.items():
                self.assertEqual(arm[u"判定"], self.S.MISSING,
                                 "%s が欠けになっていない: %r" % (name, bad))
                self.assertIsNone(arm[u"参照先"], name)
                self.assertFalse(arm[u"足した"],
                                 "**欠けに照合器を足している: %s**" % name)

    def test_2_a_missing_row_is_out_of_every_denominator(self):
        v = self.S.verdict({u"判定": self.S.MISSING, u"参照先": None}, None, True)
        self.assertTrue(v[u"欠け"])
        self.assertNotIn(u"見逃し", v, "欠けの行に見逃しを数えている")
        self.assertNotIn(u"参照先を出した", v)


class ComposeTest(unittest.TestCase):
    def setUp(self):
        self.S = _mod()

    def test_3_the_seat_is_never_overwritten(self):
        for word in (u"確認済み", u"誤りが在る"):
            seat = {u"判定": word, u"参照先": None}
            c = self.S.compose(seat, PRE["Core"])
            self.assertEqual(c[u"判定"], word, "**席を上書きした**")
            self.assertIsNone(c[u"参照先"], "**席が `なし` の行に参照先を足した**")
            self.assertFalse(c[u"足した"])

    def test_4_the_checker_is_added_only_when_the_seat_abstains(self):
        seat = {u"判定": u"判定できない", u"参照先": None}
        c = self.S.compose(seat, PRE["Core"])
        self.assertEqual(c[u"判定"], u"確認済み")
        self.assertEqual(c[u"参照先"], u"a@c1")
        self.assertTrue(c[u"足した"])
        d = self.S.compose(seat, {u"言うこと": u"原資料と一致しない", u"参照先": None})
        self.assertEqual(d[u"判定"], u"誤りが在る")
        e = self.S.compose(seat, {u"言うこと": u"一意でない", u"参照先": None})
        self.assertEqual(e[u"判定"], u"判定できない")

    def test_5_the_same_function_serves_every_arm(self):
        """**腕ごとの分岐を作らない**(C′ だけを得にする道を消す)。"""
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertNotIn('arm == "C', src)
        self.assertNotIn("if name ==", src)
        self.assertEqual(src.count("def compose("), 1)
        S = self.S
        seat = {u"判定": u"判定できない", u"参照先": None}
        arms = S.arms_of(seat, PRE)
        self.assertEqual(arms["C′"][u"参照先"], u"a@c1")
        self.assertEqual(arms[u"D′"][u"参照先"], u"b@c2")


class VerdictTest(unittest.TestCase):
    def setUp(self):
        self.S = _mod()

    def test_6_t5_t3_t1_golds(self):
        S = self.S
        g5 = {u"種類": u"参照先が在る", u"正解": u"a@c1", u"偶然一致する側": u"b@c2"}
        hit = S.verdict({u"判定": u"確認済み", u"参照先": u"a@c1"}, g5, True)
        self.assertTrue(hit[u"特定"])
        self.assertFalse(hit[u"誤認定"])
        self.assertTrue(hit[u"見逃し"], "T5 を確認済みと言ったら見逃し")
        own = S.verdict({u"判定": u"確認済み", u"参照先": u"b@c2"}, g5, True)
        self.assertTrue(own[u"誤認定"])
        self.assertTrue(own[u"値の持ち主だった"])
        g3 = {u"種類": u"参照先は無い", u"正解": None, u"偶然一致する側": None}
        self.assertTrue(S.verdict({u"判定": u"確認済み", u"参照先": u"x@y"}, g3,
                                  True)[u"誤認定"])
        g1 = {u"種類": u"値がどこにも無い", u"正解": None, u"偶然一致する側": None}
        self.assertTrue(S.verdict({u"判定": u"確認済み", u"参照先": None}, g1,
                                  True)[u"誤認定"])
        self.assertFalse(S.verdict({u"判定": u"誤りが在る", u"参照先": None}, g1,
                                   True)[u"誤認定"])

    def test_7_false_alarm_only_on_unmodified_rows(self):
        S = self.S
        self.assertTrue(S.verdict({u"判定": u"誤りが在る", u"参照先": None},
                                  None, False)[u"偽警報"])
        self.assertFalse(S.verdict({u"判定": u"誤りが在る", u"参照先": None},
                                   None, True)[u"偽警報"])


class ZVerdictTest(unittest.TestCase):
    def setUp(self):
        self.S = _mod()

    def _t(self, a_wrong, a_ident, c_wrong, c_ident):
        return {"A": {u"誤認定": {u"分子": a_wrong},
                      u"正しい参照先の特定": {u"分子": a_ident}},
                "C′": {u"誤認定": {u"分子": c_wrong},
                       u"正しい参照先の特定": {u"分子": c_ident}}}

    def test_8_three_branches(self):
        S = self.S
        both = S.judge_z(self._t(5, 2, 3, 4))
        self.assertIn(u"上回った", both[u"判定"])
        one = S.judge_z(self._t(5, 2, 3, 2))
        self.assertIn(u"片方だけ", one[u"判定"])
        none = S.judge_z(self._t(5, 2, 5, 2))
        self.assertIn(u"支持されない", none[u"判定"])

    def test_9_equal_counts_are_not_an_improvement(self):
        """**同じ数を「上回った」に数えない**(封 v2 §2 の外れ方の字)。"""
        v = self.S.judge_z(self._t(3, 3, 3, 3))
        self.assertFalse(v[u"Z-1 誤認定が減った"])
        self.assertFalse(v[u"Z-2 正しい特定が増えた"])


class ReuseTest(unittest.TestCase):
    def test_10_norm_pointer_comes_from_the_a_script(self):
        S = _mod()
        self.assertTrue(S.A1.norm_pointer.__code__.co_filename.endswith(
            "xbrl_a_core_vs_grep_2026-10-17.py"))
        src = io.open(SCRIPT, encoding="utf-8").read()
        self.assertNotIn("def norm_pointer(", src)
        self.assertIn(u"**欠けが腕で違う", src, "欠けの同数検査が無い")


if __name__ == "__main__":
    unittest.main()
