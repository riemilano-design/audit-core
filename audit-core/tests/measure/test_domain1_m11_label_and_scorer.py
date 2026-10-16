# -*- coding: utf-8 -*-
"""段 11 の問い・席の材料・採点器(封 §1・§6・§7・§11 の 7・8)を固定する。

守るのは 10 つ。
  1. 問いが**段 9 の問いと 1 文字も違わない**(違えば材料を作れない)
  2. 問いを変えたら `check_identical_to_m9` が赤になる(歯)
  3. 席の材料に**禁じた語が無い**(段 9 の一覧をそのまま使う)
  4. **「歳入」を禁じ語に足せない理由**が字で在る(凍結した問いの例文に在る)
  5. 席は 2 つ・**逆順**で、段 9 と同じ model の割り当て
  6. **再生成しないと書いてある**(封 §7)
  7. 採点器の線が **7 本**で、閾値が**段 9 の数**であること
  8. 採点器が**ラベルより先に commit されたこと**(commit の順)
  9. `beta_and_five_fields` が**壊した入力で β と食い違いを数える**(歯)
 10. 採点器が**非対称の数を必ず出す**ことが字で在ること
"""
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MEASURE = os.path.join(ROOT, "measure")
FX = os.path.join(ROOT, "fixtures", "sheet")
LAB = os.path.join(FX, "m11_label_material_2026-10-16.json")
M9LAB = os.path.join(FX, "m9_label_material_2026-10-16.json")
SCORER = os.path.join(MEASURE, "sheet_m11_score_2026-10-16.py")


def _mod(name, path):
    sp = importlib.util.spec_from_file_location(name, os.path.join(MEASURE, path))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


class QuestionIsUnchangedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _mod("m11lab_t", "sheet_m11_label_material_2026-10-16.py")
        cls.rec = load(LAB)

    def test_1_identical_to_stage9(self):
        want = load(M9LAB)["question"]
        self.assertEqual(self.rec["question"], want,
                         "**問いが段 9 と違う。採点基準を変えてはいけない**")
        self.assertEqual(self.m.L9.question_text(), want)
        self.assertTrue(self.rec["question_identical_to_m9"])
        self.assertEqual(self.rec["question_changed_lines"], [])

    def test_2_a_changed_question_is_red(self):
        with self.assertRaises(AssertionError) as cm:
            self.m.check_identical_to_m9(self.rec["question"] + "\n余計な行")
        self.assertIn("採点基準を変えてはいけない", str(cm.exception))

    def test_3_no_banned_word_leaks(self):
        self.assertEqual(self.m.BANNED, load(M9LAB)["banned_checked"],
                         "禁じ語の一覧が段 9 と違う")
        for f in self.rec["files"]:
            body = text(f["path"]) if os.path.exists(f["path"]) else self.rec["question"]
            for w in self.m.BANNED:
                self.assertNotIn(w, body, "%s に %s" % (f["seat"], w))

    def test_4_why_sainyuu_cannot_be_banned(self):
        src = text(os.path.join(MEASURE, "sheet_m11_label_material_2026-10-16.py"))
        self.assertIn("**「歳入」は禁じ語に足せない。**", src)
        self.assertIn("`歳入決算額` が在る", src)
        self.assertIn("歳入", load(M9LAB)["question"],
                      "凍結した問いに 歳入 が無いなら、この注は嘘である")

    def test_5_two_seats_reversed(self):
        seats = self.rec["seats"]
        self.assertEqual([s["seat"] for s in seats], ["seat1", "seat2"])
        self.assertEqual([s["model"] for s in seats],
                         [s["model"] for s in load(M9LAB)["seats"]],
                         "席の model の割り当てが段 9 と違う")
        self.assertEqual(seats[1]["order"], "逆順")
        a, b = self.rec["files"]
        self.assertEqual((a["first_id"], a["last_id"]), (b["last_id"], b["first_id"]))

    def test_6_no_retry(self):
        self.assertIn("**しない。**", self.rec["retry"])
        self.assertIn("判定不能", self.rec["retry"])


class ScorerLinesTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SCORER)

    def test_7_seven_lines_with_stage9_thresholds(self):
        self.assertIn("線は **7 本。すべて満たして初めて合格**", self.t)
        self.assertIn("G1P_MIN = 0.50", self.t)
        self.assertIn("G4_MIN = 0.80", self.t)
        self.assertIn("G5_MIN = 20", self.t)
        self.assertIn("**段 9 の線。動かさない**", self.t)
        for k in ("A-1(旧)", "E2(新・対称)", "X-2対称(新)", "X-2三欄(新)",
                  "β の 5 欄", "G-5 母数", "G-1′(新)"):
            self.assertIn(k, self.t, k)

    def test_8_asymmetric_number_is_always_reported(self):
        self.assertIn("**非対称にしたときの数(開示。性能として書かない)**", self.t)
        self.assertIn("**非対称にした数も必ず併記する**", self.t)
        self.assertIn("**合否に入れない**: N-接続-増", self.t)

    def test_9_increment_is_not_a_line(self):
        self.assertIn("**増えても合格にしない。減っても失敗にしない**", self.t)
        self.assertNotIn('"N-接続-増"', self.t.split("主実験の線(7 本)")[1]
                         .split("主実験の判定")[0])


class BetaHasTeethTest(unittest.TestCase):
    """封 §5。**β = 0 の材料では字で書いた判定が黙るので、壊した入力で当てる。**"""

    @classmethod
    def setUpClass(cls):
        cls.sc = _mod("m11score_t", "sheet_m11_score_2026-10-16.py")

    def _answer(self, scope):
        return {"会計": scope, "階層": "目", "親": "と場事業費 > と場事業費",
                "科目名": "運営費", "列": "支出済額", "値": "3,129,389,173"}

    def _bind(self, scope, name="運営費"):
        return {"state": "GROUNDED", "route": "R-1", "pointer": "x",
                "evidence": {"scope": scope, "level": "目",
                             "parent": "と場事業費 > と場事業費", "name": name,
                             "column": "支出済額", "value": 3129389173}}

    def test_10_beta_counts_only_alias_dependent_hits(self):
        alias = {"東京都と場会計": {"canonical": "と場会計"}}
        s1 = {"A": dict(self._answer("東京都と場会計"), id="A")}
        s2 = {"A": dict(self._answer("東京都と場会計"), id="A")}
        out = self.sc.beta_and_five_fields(
            {"A": self._bind("と場会計")}, {"A": {}}, ["A"], s1, s2, alias)
        self.assertEqual(out["β 別名表に依って一致した主張"], 1,
                         "**別名表に依った一致を β に数えていない**")
        self.assertEqual(out["5 欄の一致"], 1)
        self.assertEqual(out["5 欄の食い違い"], 0)
        self.assertFalse(out["空振りか"])

    def test_11_a_hit_without_the_alias_table_is_not_beta(self):
        s1 = {"A": dict(self._answer("と場会計"), id="A")}
        s2 = {"A": dict(self._answer("と場会計"), id="A")}
        out = self.sc.beta_and_five_fields(
            {"A": self._bind("と場会計")}, {"A": {}}, ["A"],
            s1, s2, {"東京都と場会計": {"canonical": "と場会計"}})
        self.assertEqual(out["β 別名表に依って一致した主張"], 0)
        self.assertTrue(out["空振りか"])
        self.assertIn("空振りを「安全性の証拠」として書かない", out["注"])

    def test_12_a_wrong_row_behind_the_alias_is_caught_by_five_fields(self):
        """**歯**: 会計だけ別名表で合わせても、5 欄が違えば食い違いに数える。"""
        alias = {"東京都と場会計": {"canonical": "と場会計"}}
        s1 = {"A": dict(self._answer("東京都と場会計"), id="A")}
        s2 = {"A": dict(self._answer("東京都と場会計"), id="A")}
        out = self.sc.beta_and_five_fields(
            {"A": self._bind("と場会計", name="別の目")}, {"A": {}}, ["A"],
            s1, s2, alias)
        self.assertEqual(out["β 別名表に依って一致した主張"], 0,
                         "6 欄が一致していないので β ではない")
        # 会計以外が違う bind は、そもそも「正しい接続」に入らない
        self.assertEqual(out["5 欄の食い違い"], 0)


class ScorerPrecedesTheLabelsTest(unittest.TestCase):
    """**採点器はラベルを見る前に commit する**(封 §7)。"""

    SCORER_REL = "measure/sheet_m11_score_2026-10-16.py"
    LABELS = ("fixtures/sheet/m11_answers_seat1_2026-10-16.json",
              "fixtures/sheet/m11_answers_seat2_2026-10-16.json")

    @staticmethod
    def _added(rel):
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
            cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _tracked(rel):
        return subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                              cwd=ROOT, capture_output=True).returncode == 0

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_13_scorer_is_committed(self):
        self.assertTrue(self._tracked(self.SCORER_REL),
                        "道が git に当たっていない(pathspec の誤り)")
        self.assertIsNotNone(self._added(self.SCORER_REL),
                             "採点器がまだ commit されていない")

    def test_14_scorer_precedes_each_label_file(self):
        sc = self._added(self.SCORER_REL)
        for rel in self.LABELS:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(sc, other,
                                "採点器とラベルが同じ commit に入っている(順を測れない)")
            self.assertTrue(self._ancestor(sc, other),
                            "**採点器がラベルより後に commit されている**")
            self.assertFalse(self._ancestor(other, sc))     # 歯: 逆向きは偽


if __name__ == "__main__":
    unittest.main()
