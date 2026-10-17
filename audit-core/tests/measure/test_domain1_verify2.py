# -*- coding: utf-8 -*-
"""検証層の直しの測定と結果を固定する(封 docs/DOMAIN1_VERIFY2_SEAL_2026-10-17.md)。

**合成の規則は壊した入力で 1 本ずつ当てる**(正常な材料では分岐が全部通らない)。
"""
import importlib.util
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX = os.path.join(ROOT, "fixtures", "sheet")
REC = os.path.join(FX, "verify2_2026-10-17.json")
DOC = os.path.join(ROOT, "docs", "DOMAIN1_VERIFY2_RESULT_2026-10-17.md")
A1 = "A 席そのまま / seat1"
C1 = "C′ 席 + Core / seat1"
D1 = "D 席 + grep(申告を使わない) / seat1"
DP1 = "D′ 席 + grep(申告を残す) / seat1"


def _mod(name, rel):
    sp = importlib.util.spec_from_file_location(
        name, os.path.join(ROOT, "measure", rel))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


V = _mod("verify2_for_test", "sheet_verify2_2026-10-17.py")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class CompositionTest(unittest.TestCase):
    """**席が言ったときは消さない**を、4 つの入り口すべてで当てる。"""

    SIX = {"会計": "一般会計", "階層": "項", "親": "総務費", "科目名": "x",
           "列": "支出済額", "値": 100}

    def test_1_seat_says_is_exhaustive(self):
        self.assertEqual(V.seat_says({"verdict": "根拠なし"}),
                         ("誤りが在る", "値が原資料に無い"))
        self.assertEqual(V.seat_says({"verdict": "根拠なし",
                                      "不一致の種類": "列の取り違え"}),
                         ("誤りが在る", "列の取り違え"))
        self.assertEqual(V.seat_says({"verdict": "判定不能"})[0], "判定できない")
        self.assertEqual(V.seat_says(dict(self.SIX,
                                          **{"不一致の種類": "別の科目の値"})),
                         ("誤りが在る", "別の科目の値"))
        self.assertEqual(V.seat_says(dict(self.SIX, **{"不一致の種類": "不明"})),
                         ("黙っている", "不明"))

    def test_2_the_verifier_never_overwrites_the_seat(self):
        """**席が「誤りが在る」と言ったら、検証器が何を返しても消えない。**"""
        for chk in ("確認済み", "原資料と一致しない",
                    "確認できない(参照先が無い)", "確認できない(値が一意でない)"):
            self.assertEqual(V.compose("誤りが在る", chk), "誤りが在る", chk)
            self.assertEqual(V.compose("判定できない", chk), "判定できない", chk)

    def test_3_the_verifier_decides_only_when_the_seat_is_silent(self):
        self.assertEqual(V.compose("黙っている", "原資料と一致しない"), "誤りが在る")
        self.assertEqual(V.compose("黙っている", "確認済み"), "確認済み")
        self.assertEqual(V.compose("黙っている", "確認できない(参照先が無い)"),
                         "判定できない")
        self.assertEqual(V.compose("黙っている", "確認できない(値が一意でない)"),
                         "判定できない")

    def test_4_axis2_never_invents_a_kind_the_verifier_cannot_say(self):
        self.assertEqual(V.axis2("列の取り違え", "誤りが在る"), "列の取り違え")
        self.assertEqual(V.axis2("不明", "誤りが在る"), "値が原資料に無い")
        self.assertEqual(V.axis2("不明", "確認済み"), "不明")
        self.assertEqual(V.axis2("不明", "判定できない"), "不明")

    def test_5_grep_only_counts_values(self):
        vals = {100: 1, 200: 2}
        self.assertEqual(V.grep_check(100, vals), "確認済み")
        self.assertEqual(V.grep_check(200, vals), "確認できない(値が一意でない)")
        self.assertEqual(V.grep_check(999, vals), "原資料と一致しない")


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.r = load(REC)
        self.m = self.r["方式ごと"]

    def test_6_nothing_but_the_composition_changed(self):
        self.assertEqual(self.r["変えたもの"],
                         "**合成の規則 1 か所だけ**(封 §1)")
        for k in ("engine", "席の答え", "正解ラベル", "6 欄の鍵"):
            self.assertIn(k, self.r["変えていないもの"], k)
        self.assertTrue(
            self.r["**この便の数のほとんどは算術で決まる。性能ではない**"])

    def test_7_the_four_lost_detections_came_back(self):
        self.assertEqual(len(self.m[C1]["検出"]), 8)
        self.assertEqual(self.m[C1]["見落とし"], [])
        for cid in ("R001", "R004", "R009", "R024"):
            self.assertIn(cid, self.m[C1]["検出"], cid)

    def test_8_core_adds_only_axis_three_over_grep(self):
        """**C′ と D′ の差は軸 3 だけ。**ここが売却判断の数である。"""
        c, d = self.m[C1], self.m[DP1]
        self.assertEqual(c["検出"], d["検出"])
        self.assertEqual(c["見落とし"], d["見落とし"])
        self.assertEqual(c["軸 2 種類を当てた"], d["軸 2 種類を当てた"])
        self.assertEqual(c["軸 3 本来の参照先が正しい"]["件数"], 4)
        self.assertEqual(d["軸 3 本来の参照先が正しい"]["件数"], 0)

    def test_9_dropping_the_declaration_costs_four(self):
        self.assertEqual(len(self.m[D1]["検出"]), 4)
        self.assertEqual(len(self.m[D1]["見落とし"]), 4)
        self.assertEqual(len(self.m[DP1]["検出"]), 8)

    def test_10_the_cost_of_the_or_is_the_trap(self):
        k = "罠(R035)"
        self.assertFalse(self.m[A1][k]["**文書は正しいのに誤りが在ると言ったか**"])
        self.assertTrue(self.m[C1][k]["**文書は正しいのに誤りが在ると言ったか**"])

    def test_11_no_false_alarms_on_the_unaltered_26(self):
        for key, v in self.m.items():
            self.assertEqual(v["偽警報(無改変 26 件)"]["件数"], 0, key)

    def test_12_all_ten_predictions_and_the_arithmetic_ones_are_marked(self):
        ch = self.r["予測の照合(H-1〜H-10)"]
        self.assertEqual(len(ch), 10)
        self.assertTrue(all(ch.values()), [k for k, v in ch.items() if not v])
        self.assertEqual(self.r["**算術で決まる予測(手柄にしない)**"],
                         ["H-1", "H-4", "H-8"])
        self.assertEqual(self.r["**測る意味が在った予測**"],
                         ["H-3", "H-5", "H-7", "H-10"])

    def test_13_limits_name_what_was_not_compared(self):
        j = " ".join(self.r["limits"])
        self.assertIn("既存製品は手元で測れない", j)
        self.assertIn("素朴な値一致照合", j)
        self.assertIn("設計の確認であって性能ではない", j)


class DocTest(unittest.TestCase):
    def setUp(self):
        self.t = text(DOC)
        self.r = load(REC)

    def test_14_the_heading_says_same_material(self):
        self.assertIn("同じ材料での修正結果", self.t.split("\n")[0])
        head = self.t[:self.t.index("\n## §1")]
        self.assertIn("**未使用の別資料の結果ではない。**", head)
        self.assertIn("**だからこの文書では「性能」という語を使わない。**", head)

    def test_15_the_word_performance_is_not_used_as_a_claim(self):
        """**「性能」は「性能ではない」の形でしか出てこない。**"""
        for m in re.finditer("性能", self.t):
            around = self.t[max(0, m.start() - 30):m.start() + 30]
            self.assertTrue(
                ("ではない" in around) or ("使わない" in around)
                or ("測れない" in around) or ("性能は未使用" in around),
                around)

    def test_16_the_three_measured_things(self):
        b = sec(self.t, "### §2-1", "## §3")
        self.assertIn("**測る意味が在った数は 3 つだけ**", b)
        self.assertIn("**Core の機械部分が grep に足したのはここだけ**", b)
        self.assertIn("**文書の層の偽警報が 0 → 1 に増えた**", b)

    def test_17_the_grep_comparison_is_the_headline(self):
        b = sec(self.t, "### §3-3", "## §4")
        self.assertIn("**軸 3 本来の参照先** | **4** | **0** | **+4** |", b)
        self.assertIn("**だからこの材料では、買い手が"
                      "「LLM + 値の出現回数の照合」を自分で組めば、\n"
                      "検出と種類の数は同じになる。**", b)

    def test_18_predictions_table_marks_the_arithmetic_ones(self):
        b = sec(self.t, "## §4", "## §5")
        ids = re.findall(r"(?m)^\| \*?\*?H-(\d+)", b)
        self.assertEqual(ids, [str(i) for i in range(1, 11)], "H-1〜H-10")
        self.assertEqual(b.count("**手柄にしない**"), 3)
        self.assertIn("**意味が在ったのは H-3・H-5・H-7・H-10 の 4 本で、"
                      "4 本とも当たった。**", b)

    def test_19_ten_limits_including_the_two_new_ones(self):
        b = sec(self.t, "## §5 示せないこと", "## §6")
        nums = re.findall(r"(?m)^(\d+)\. ", b)
        self.assertEqual(nums, [str(i) for i in range(1, 11)], "限界は 10 本")
        self.assertIn("**「既存製品と比べた」とは書かない。**", b)
        self.assertIn("軸 3 の 4 件が顧客にとってどれだけの値打ちかは"
                      "測っていない。**", b)

    def test_20_the_next_step_names_the_right_main_comparison(self):
        b = sec(self.t, "## §6")
        self.assertIn("**だから (2) で測るべき主比較は「C′ 対 D′」である**", b)
        self.assertIn("**「C′ 対 A」だけを測ると、grep で足りることを見落とす。**", b)
        self.assertIn("**(2) の条件はこの封では決めない**", b)
        self.assertIn("**これは見込みであって保証値ではない。**", b)
        self.assertIn("**既存製品の席は手元で測れない。**", b)


if __name__ == "__main__":
    unittest.main()
