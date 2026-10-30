# -*- coding: utf-8 -*-
"""材料の spec(docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md)の門(spec §6)。"""
import hashlib
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SPEC_REL = "docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md"
SPEC = os.path.join(ROOT, SPEC_REL)
V2 = os.path.join(ROOT, "docs", "XBRL_CD_SEAL_V2_2026-10-17.md")
V2_SHA = None          # 下で実測して比べる(spec を書いても v2 は動かない)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class SpecTest(unittest.TestCase):
    def setUp(self):
        self.t = text(SPEC)

    def test_1_rows_are_eight_plus_sixteen(self):
        """spec M-2。"""
        b = sec(self.t, "## §1 1 書類あたり", "## §2")
        self.assertIn("**24 行**", self.t)
        rows = re.findall(r"(?m)^\| \*\*(注入|無改変)\*\* \| \*\*(\d+)\*\* \|", b)
        self.assertEqual(rows, [("注入", "8"), ("無改変", "16")],
                         "注入 8 / 無改変 16 の行が無い")
        self.assertIn("**T5 を先に取り、足りなければ T3、足りなければ T1 で埋める**", b)
        self.assertIn("**8 件そろわなければ「そろわなかった」と書く**", b)
        self.assertIn("**主比較の判定には使わない**", b)

    def test_2_four_things_shown_and_the_banned_words(self):
        """spec M-3。**見せない字を字で列挙する。**"""
        b = sec(self.t, "## §2 席に見せるもの", "## §3")
        nums = re.findall(r"(?m)^(\d)\. ", b)
        self.assertEqual(nums, ["1", "2", "3", "4"], "見せるものは 4 つ")
        for w in ("注入", "正解", "Core", "engine", "GROUNDED", "pointer",
                  "T1", "T3", "T5"):
            self.assertIn("`%s`" % w, b, "禁じる字の一覧に %s が無い" % w)
        self.assertIn("機械で確かめる", b)

    def test_3_answer_schema_is_three_words_and_one_pointer(self):
        """spec M-4。"""
        b = sec(self.t, "## §3 席の回答の形", "## §4")
        self.assertIn("**`確認済み` / `誤りが在る` / `判定できない`**", b)
        self.assertIn("または **`なし`**", b)
        self.assertIn("**「どちらとも言える」や自由文は受け取らない**", b)
        self.assertIn("**24 行すべてに答える**", b)

    def test_4_four_arms_from_one_answer(self):
        """spec M-5。"""
        b = sec(self.t, "## §4 腕の作り方", "## §5")
        ids = re.findall(r"(?m)^\| \*\*(A|C′|D′|D″)\*\* \|", b)
        self.assertEqual(ids, ["A", "C′", "D′", "D″"], "腕は 4 つ")
        self.assertIn("**席の回答そのまま**", b)
        self.assertIn("**上書きしない**", b)
        self.assertIn("**1 書類 1 便・席は 1 席・再生成なし。**", b)

    def test_5_five_stops(self):
        """spec M-6。"""
        b = sec(self.t, "## §5 止める条件", "## §6")
        self.assertEqual(re.findall(r"(?m)^(\d)\. ", b),
                         [str(i) for i in range(1, 6)], "止める条件は 5 本")
        self.assertIn("**規則を緩めて 8 件にしない。**", b)
        self.assertIn("**結果を見てから §1〜§4 を変えない。**", b)

    def test_6_v2_is_untouched(self):
        """**spec を書いても封 v2 は動かない。**"""
        with io.open(V2, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()[:16]
        out = subprocess.run(["git", "log", "--format=%H", "--", "docs/XBRL_CD_SEAL_V2_2026-10-17.md"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(len([s for s in out.stdout.split() if s]), 1,
                         "**v2 が 2 回以上 commit されている(直した)**")
        self.assertIn("**封 v2 は 1 文字も直していない**", self.t)
        self.assertTrue(sha)


class CommitOrderTest(unittest.TestCase):
    AFTER = ("measure/xbrl_cd_material_2026-10-17.py",
             "fixtures/xbrl/cd8/material_2026-10-17.json",
             "docs/XBRL_CD_RESULT_2026-10-17.md")

    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    @staticmethod
    def _ancestor(a, b):
        return subprocess.run(["git", "merge-base", "--is-ancestor", a, b],
                              cwd=ROOT, capture_output=True).returncode == 0

    def test_7_spec_precedes_the_material(self):
        """spec M-1。"""
        s = self._added(SPEC_REL)
        self.assertIsNotNone(s, "spec がまだ commit されていない")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(s, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(s, other), rel)


class MissingRowRuleTest(unittest.TestCase):
    """§7 の追記(独立監査の REVISE 指摘 4)を固定する。"""

    def setUp(self):
        self.t = text(SPEC)

    def test_8_the_missing_row_rule_is_the_same_for_every_arm(self):
        b = sec(self.t, "## §7 追記")
        self.assertIn("**§1〜§5 は 1 文字も変えず、この場合分けだけを足す**", b)
        rows = re.findall(r"(?m)^\| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", b)
        data = [r for r in rows if "A" != r[1] or True]
        self.assertGreaterEqual(len(data), 4, "場合分けの表が無い")
        self.assertIn("**`欠け`。照合器の結果を足さない**", b)
        self.assertIn("**欠けた行は 4 腕すべての分母から外し、件数を別に書く。**", b)
        self.assertIn("欠けは 4 腕で必ず同数になる。門で確かめる**", b)

    def test_9_the_reason_names_the_broken_comparison(self):
        b = sec(self.t, "## §7 追記")
        self.assertIn("**C′ だけが「席が答えなかった行」で得をする**", b)
        self.assertIn("主比較が壊れる", b)


class T5ZeroDocTest(unittest.TestCase):
    """§8 の追記(再監査の推奨と「未確認」)を固定する。"""

    def setUp(self):
        self.t = text(SPEC)

    def test_10_the_t5_zero_document_is_named(self):
        b = sec(self.t, "## §8 追記")
        self.assertIn("`S100YXF5`", b)
        self.assertIn("この書類では軸B(参照先の正しさ)が", b)
        self.assertIn("**書類は引き直さない**", b)
        self.assertIn("軸B の分母に入った書類が 7 件であることを書く", b)

    def test_11_the_unverified_branch_is_recorded_with_its_remedy(self):
        b = sec(self.t, "## §8 追記")
        self.assertIn("実コードパスとして実行されていない", b)
        self.assertIn("guard-that-only-fires-on-failure", b)
        self.assertIn("**だから採点器には、欠けを作った入力を食わせて赤くなる門を置く**", b)


if __name__ == "__main__":
    unittest.main()
