# -*- coding: utf-8 -*-
"""封 v2(docs/XBRL_CD_SEAL_V2_2026-10-17.md)の門(封 §5)。

**v1 を直していないことを sha で確かめる。**
**差分が 5 本・軸が 2 つ・数が 4 つ・予測が 2 本であることを字で固定する。**
"""
import hashlib
import io
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
V1_REL = "docs/XBRL_CD_SEAL_2026-10-17.md"
V2_REL = "docs/XBRL_CD_SEAL_V2_2026-10-17.md"
V1 = os.path.join(ROOT, V1_REL)
V2 = os.path.join(ROOT, V2_REL)
V1_SHA = "5fe8f59c09a2a51e"       # 封 V-1。**動いたら赤くなる**


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i) if end else len(t)
    return t[i:j]


class V1FrozenTest(unittest.TestCase):
    def test_1_v1_has_not_moved(self):
        """封 V-1。**差分の封を書いても v1 は動かない。**"""
        with io.open(V1, "rb") as fh:
            self.assertEqual(hashlib.sha256(fh.read()).hexdigest()[:16], V1_SHA,
                             "**v1 が動いている**")
        t = text(V2)
        self.assertIn("**v1 を直さず、差分だけをここに書く。**", t)
        self.assertIn("**v1 の封は 1 文字も直していない**", t)

    def test_2_v2_names_what_it_inherits(self):
        t = text(V2)
        head = t[:t.index("## §1")]
        self.assertIn("**継ぐ封**", head)
        self.assertIn(V1_REL.split("/")[-1], head)
        for k in ("§1(対象 8 書類と引く規則)", "§4-3(合成)",
                  "§5-2(正解の基準)", "§6(対称性)", "§8(止める条件)"):
            self.assertIn(k, head, k)


class DeltaTest(unittest.TestCase):
    def setUp(self):
        self.t = text(V2)

    def test_3_five_deltas_and_no_new_metric(self):
        """封 V-2。"""
        b = sec(self.t, "## §1 変える 5 つ", "### §1-1")
        ids = re.findall(r"(?m)^\| \*\*(Δ\d)\*\*", b)
        self.assertEqual(ids, ["Δ%d" % i for i in range(1, 6)], "差分は 5 本")
        self.assertIn("**主比較は A 対 C′。D′・D″ は副比較。B(Core 単体)は参考**", b)
        self.assertIn("**C′ は席の申告を上書きせず、Core の照合を足すだけ**", b)
        self.assertIn("**新しい指標は 1 つも足さない。**", b)
        self.assertIn("**費用の上限は判定条件にしない**", b)

    def test_4_two_axes_and_four_numbers_with_denominators(self):
        """封 V-3。**分母の無い行を作らない。**"""
        a = sec(self.t, "### §1-1", "### §1-2")
        ids = re.findall(r"(?m)^\| \*\*(軸A 停止判定|軸B 参照先)\*\*", a)
        self.assertEqual(len(ids), 2, "軸は 2 つ")
        self.assertIn("**「止めた」ことを軸B の正解に数えない。**", a)
        self.assertIn("**軸A × 軸B の表を必ず出す**", a)
        n = sec(self.t, "### §1-2", "## §2")
        rows = re.findall(r"(?m)^\| \*\*(誤認定|見逃し|正しい参照先の特定|保留)\*\* \| "
                          r"(.+?) \| (.+?) \|$", n)
        self.assertEqual(len(rows), 4, "数は 4 つ")
        for name, _d, den in rows:
            self.assertTrue(den.strip(), "%s の分母が空" % name)
        self.assertIn("**主比較は A 対 C′ の 4 つの数の差**", n)

    def test_5_two_predictions_with_fail_modes_and_the_and_rule(self):
        """封 V-4・V-5。**片方だけで「上回った」と書けない。**"""
        b = sec(self.t, "## §2 予測", "## §3")
        rows = re.findall(r"(?m)^\| \*\*(Z-\d)\*\* \| (.+?) \| (.+?) \|$", b)
        self.assertEqual([r[0] for r in rows], ["Z-1", "Z-2"])
        for num, _p, how in rows:
            self.assertTrue(len(how.strip()) >= 5, "%s の外れ方が薄い" % num)
        self.assertIn("**Z-1 と Z-2 の両方を満たしたときだけ「LLM + Core は "
                      "LLM 単体を上回った」と書く。**", b)
        self.assertIn("**片方だけなら「片方だけ」と書く。**", b)
        self.assertIn("v1 の X-1〜X-10 は生きている", self.t)

    def test_6_five_stages_with_the_audit_before_the_seat(self):
        """封 V-6。**監査が席より前に在る。**"""
        b = sec(self.t, "## §3 実行の順", "## §4")
        ids = re.findall(r"(?m)^\| \*\*(\d)\*\* \| (.+?) \|$", b)
        self.assertEqual([i[0] for i in ids], ["1", "2", "3", "4", "5"])
        audit = [n for n, body in ids if "独立監査" in body]
        seat = [n for n, body in ids if "席を 1 回だけ呼ぶ" in body]
        self.assertEqual(audit, ["4"])
        self.assertEqual(seat, ["5"])
        self.assertIn("**実行環境の制約は無視しない**", b)
        self.assertIn("鍵の値は記録しない", self.t)

    def test_7_six_things_kept_and_seven_gates(self):
        """封 V-7。"""
        b = sec(self.t, "## §4 変えないもの", "## §5")
        items = re.findall(r"(?m)^- ", b)
        self.assertEqual(len(items), 7, "変えないものは 7 本")
        self.assertIn("**T2 は入れない。**", b)
        self.assertIn("**値の一致は正解にしない。**", b)
        g = sec(self.t, "## §5 門")
        self.assertEqual(re.findall(r"(?m)^\| \*\*(V-\d)\*\*", g),
                         ["V-%d" % i for i in range(1, 8)])


class CommitOrderTest(unittest.TestCase):
    AFTER = ("measure/xbrl_cd_material_2026-10-17.py",
             "fixtures/xbrl/cd8/fetched_2026-10-17.json",
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

    def test_8_v2_precedes_the_material_and_the_result(self):
        v2 = self._added(V2_REL)
        self.assertIsNotNone(v2, "v2 がまだ commit されていない")
        v1 = self._added(V1_REL)
        self.assertTrue(self._ancestor(v1, v2), "v1 が v2 より後に在る")
        for rel in self.AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(v2, other, "同じ commit に在る: %s" % rel)
            self.assertTrue(self._ancestor(v2, other), rel)


if __name__ == "__main__":
    unittest.main()
