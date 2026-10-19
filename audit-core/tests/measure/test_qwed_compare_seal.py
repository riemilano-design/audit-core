# -*- coding: utf-8 -*-
u"""QWED 比較の封(docs/QWED_COMPARE_SEAL_2026-10-19.md)を固定する。

封は「取り込まない・並べて測る」。QWED は import しない(この門は 3.9 で走る)。
"""
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SEAL_REL = "docs/QWED_COMPARE_SEAL_2026-10-19.md"
SEAL = os.path.join(ROOT, SEAL_REL)
AFTER = ("measure/qwed_compare_2026-10-19.py",
         "fixtures/xbrl/cd8/qwed_compare_2026-10-19.json",
         "docs/QWED_COMPARE_RESULT_2026-10-19.md",
         "tests/measure/test_qwed_compare_result.py",
         # 追記 2(E′)。§6 でなく追記の節に在る
         "fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json",
         "docs/QWED_COMPARE_EPRIME_RESULT_2026-10-20.md",
         "tests/measure/test_qwed_compare_eprime_result.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class SealTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SEAL)

    def test_1_head_names_the_instruction_and_the_zero_usd_no_integration_rule(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"**QWED という既存システムを見つけた。競合にも思えるが取り込めるかも**", head)
        self.assertIn(u"**同じ材料で測った数は 1 つも無い**", head)
        self.assertIn(u"**0 USD・LLM は呼ばない・engine(`core/`・`adapters/`)は変えない・QWED を依存に足さない。**", head)

    def test_2_the_entry_and_the_three_classes_are_literal(self):
        b = sec(self.t, "## §0", "## §1")
        self.assertIn(u"qwed **7.3.0**", b)
        self.assertIn(u"Python **3.11.17**", b)
        self.assertIn(u"FactVerifier(use_llm_fallback=False).verify_fact(claim, context, provider=None)", b)
        for k in (u"**QWED が違うと言う**", u"**QWED が通す**", u"**判定なし**"):
            self.assertIn(k, b, k)
        self.assertIn(u'`scores.entity_match < 1.0`', b)
        self.assertIn(u'`scores.entity_match == 1.0` **かつ** `deterministic_verdict == "SUPPORTED"`', b)
        self.assertIn(u"**Audit Core 側は記録から写す。再実行しない。**", b)
        self.assertIn(u"**QWED のコードは変えない。QWED の答えを Audit Core の state に写さない。engine は触らない。**", b)

    def test_3_denominators_are_literal_and_measured(self):
        b = sec(self.t, "## §1", "## §2")
        for k in (u"| 行 | **192** |", u"**64**(型: T5_COINCIDENT **50**・T3_ABSENT **12**・T1_VALUE **2**",
                  u"VALUE_MISMATCH **43**・参照先なし **21**・GROUNDED **0**",
                  u"誤りが在る **51**・実証不能 13・**検査通過 0**",
                  u"**Audit Core が注入 64 件のうち検査通過(誤りを通す)にした行は 0。**",
                  u"| S100YXMA | 1,223 | 116,712 |", u"| S100YZEV | 397 | 41,062 |",
                  u"**95,000 字以下の塊(chunk)に行の境で割る**",
                  u"**割れる数は S100YWGX・S100YXMA・S100YZCT が 2、他 5 書類が 1、合計 11**",
                  u"| 主張(id) | **35**", u"| 文(重複なし。`rows[].文` の字) | **11** |",
                  u"**8**(I-1 2・I-2 2・II-1 2・II-2 2", u"**8 通りの文に 1 件ずつ**",
                  u"| 誤りの無い文 | **3**", u"**4,194 字**",
                  u"検出 **4**(R004・R009・R010・R012)・保留 4(R001・R021・R024・R030)・見落とし 0・偽警報 0"):
            self.assertIn(k, b, k)
        self.assertIn(u"**字で留める。全部いま測った**", b)

    def test_4_three_runs_each_with_one_way_to_build_the_input(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertEqual(re.findall(r"(?m)^### (W1|E|S) ―", b), ["W1", "E", "S"])
        self.assertIn(u"`Fact <局所名> in <context id> equals <値の字>.`", b)
        self.assertIn(u"`Fact equals <換算した値>.`", b)
        self.assertIn(u"`UNIT_SCALE[単位]`(`adapters/xbrl/vocabulary.py`", b)
        self.assertIn(u"**95,000 字以下の chunk に行の境で割る**", b)
        self.assertIn(u"`entity_match` が最大の chunk の結果**(同点は前の chunk)", b)
        self.assertIn(u"**1 回だけ**置き換える(置き換えた回数が 1 でなければ止める)", b)
        self.assertIn(u"**文と id は 1 対多**", b)
        self.assertIn(u"**途中で封を書き換えない。**", b)

    def test_5_three_controls_one_change_each(self):
        b = sec(self.t, "## §3", "## §4")
        self.assertIn(u"**測る道具の故障を作って当てる。1 回に 1 件**", b)
        self.assertEqual(re.findall(r"(?m)^\| \*\*C-(\d)", b), ["1", "2", "3"])
        self.assertIn(u"S100YXMA R004", b)
        self.assertIn(u"**その数から抜けるのは `385`・`483` の 2 つだけ**", b)

    def test_6_seventeen_predictions_each_with_a_failure_mode(self):
        b = sec(self.t, "## §4", "## §5")
        ids = re.findall(r"(?m)^\| \*\*Q-(\d+)\*\* \|", b)
        self.assertEqual(ids, [str(i) for i in range(1, 18)])
        for line in re.findall(r"(?m)^\| \*\*Q-\d+\*\* \|.*$", b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        for k in (u"**注入 64 / 64**", u"**QWED が違うと言う: 注入 0 / 64。QWED が通す: 0 / 192**",
                  u"**QWED が通す: 注入 35 以上 / 64**", u"**60〜100**", u"**14 以上** / 18",
                  u"**QWED が違うと言う ≦ 2 / 8**", u"**300 秒未満**",
                  u"**本当に測っているのは Q-4・Q-5・Q-8〜Q-11・Q-14 である。**"):
            self.assertIn(k, b, k)

    def test_7_limits_are_written_first(self):
        b = sec(self.t, "## §5", "## §6")
        for k in (u"**QWED の LLM の経路は測らない**", u"**入力の形はこちらが決めた。**",
                  u"**Math engine(`verify_math`)は測らない。**", u"**同じ 8 書類・同じ 35 件である。**",
                  u"**qwed 7.3.0 の数である。**", u"**誤りを通す率(偽陰性)だけを並べる。**"):
            self.assertIn(k, b, k)

    def test_8_the_file_list_is_closed_and_engine_is_untouched(self):
        b = sec(self.t, "## §6", "## §7")
        for rel in AFTER[:4]:
            self.assertIn("`%s`" % rel, b, rel)
        for rel in AFTER[4:]:          # 追記 2(E′)の file は追記の節に在る
            self.assertIn("`%s`" % rel, self.t, rel)
        self.assertIn(u"**これ以外に触らない。**", b)
        self.assertIn(u"`core/py/` は 0 行、`adapters/` は 0 行", b)
        self.assertIn(u"**変異 3 通り**", b)
        self.assertIn(u"**測ってから封を直さない。**", b)

    def test_9_not_doing(self):
        b = sec(self.t, "## §7")
        self.assertIn(u"依存に足さない", b)
        self.assertIn(u"**作らない**", b)


class Addendum2Test(unittest.TestCase):
    u"""追記 2(2026-10-20): E′ の描き方と予測 Q-18〜Q-24。本文 §0〜§7 は書き換えない。"""
    def setUp(self):
        self.t = text(SEAL)
        self.b = self.t[self.t.index(u"\n## 追記 2"):]

    def test_12_addendum_does_not_rewrite_the_body(self):
        body = self.t[:self.t.index(u"\n## 追記 2")]
        for k in (u"**QWED が通す: 注入 35 以上 / 64**", u"**60〜100**", u"値は instance の字そのまま"):
            self.assertIn(k, body, k)

    def test_13_eprime_is_defined_with_one_real_line(self):
        self.assertEqual(re.findall(r"(?m)^\| \*\*E′(a|b)\*\* \|", self.b), ["a", "b"])
        self.assertIn(u"`Fact OrdinaryIncome in CurrentYearDuration equals 12497000000.`", self.b)
        self.assertIn(u"`Fact OrdinaryIncome in CurrentYearDuration equals 12497.`", self.b)
        self.assertIn(u"**換算しない**", self.b)

    def test_14_seven_more_predictions_each_with_a_failure_mode(self):
        ids = re.findall(r"(?m)^\| \*\*Q-(\d+)\*\* \|", self.b)
        self.assertEqual(ids, [str(i) for i in range(18, 25)])
        for line in re.findall(r"(?m)^\| \*\*Q-\d+\*\* \|.*$", self.b):
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        self.assertIn(u"**34〜38**", self.b)
        self.assertIn(u"注入は 0〜5 / 64**", self.b)
        self.assertIn(u"`fixtures/xbrl/cd8/qwed_compare_eprime_2026-10-20.json`", self.b)


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_10_the_seal_precedes_the_measurement(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)

    def test_11_qwed_is_not_a_dependency_of_the_tree(self):
        # 字面を 2 つに割る: この file 自身が pattern に当たらないように(memory: source-text-tests-hit-own-prose)
        pats = ["import " + "qwed", "from " + "qwed"]
        args = ["git", "grep", "-l", "-i"]
        for pat in pats:
            args += ["-e", pat]
        out = subprocess.run(args + ["--", "core", "adapters", "tests", "measure"],
                             cwd=ROOT, capture_output=True, text=True)
        hits = [h for h in out.stdout.split() if h != "measure/qwed_compare_2026-10-19.py"]
        self.assertEqual(hits, [], out.stdout)


if __name__ == "__main__":
    unittest.main()
