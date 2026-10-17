# -*- coding: utf-8 -*-
"""本番の材料(封 v2 段 3)の門。**独立監査の REVISE 指摘 2・3 に対応する。**

- 指摘 2: **採点の関数は (ア) の実物を使う**(書き直していないことを束縛で確かめる)
- 指摘 3: **見せない字の検査がコードで在り、壊した入力で赤くなる**
"""
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT_REL = "measure/xbrl_cd_material_2026-10-17.py"
SCRIPT = os.path.join(ROOT, SCRIPT_REL)
A1_REL = "measure/xbrl_a_core_vs_grep_2026-10-17.py"
REC = os.path.join(ROOT, "fixtures", "xbrl", "cd8", "material_2026-10-17.json")
SPEC_REL = "docs/XBRL_CD_MATERIAL_SPEC_2026-10-17.md"


def _mod():
    sp = importlib.util.spec_from_file_location("cd_material", SCRIPT)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def rec():
    return json.load(io.open(REC, encoding="utf-8"))


class ReuseTest(unittest.TestCase):
    """指摘 2。**(ア) の関数をそのまま使っているか**を束縛で見る。"""

    def setUp(self):
        self.M = _mod()

    def test_1_the_scoring_functions_come_from_the_a_script(self):
        for name in ("norm_pointer", "core_say", "core_pointer_say", "d_prime",
                     "d_double", "gold_of", "judge", "value_index", "material"):
            f = getattr(self.M.A1, name)
            self.assertTrue(f.__code__.co_filename.endswith(A1_REL.split("/")[-1]),
                            "%s が (ア) の file から来ていない" % name)

    def test_2_the_production_script_does_not_redefine_them(self):
        """**書き直すと正規化の掛け忘れが再発する**(6 回目と記録されている型)。"""
        src = io.open(SCRIPT, encoding="utf-8").read()
        for name in ("norm_pointer", "core_say", "core_pointer_say",
                     "d_prime", "d_double", "judge"):
            self.assertNotIn("def %s(" % name, src,
                             "**%s を書き直している**" % name)
        self.assertIn("A1 = importlib.util.module_from_spec", src)

    def test_3_pointers_in_the_record_are_normalised(self):
        """記録に出た参照先が**正規化された字**であること(生の鍵が混ざらない)。"""
        for p in rec()["書類ごと"]:
            for row in p["席の前に出せる分"].values():
                for arm in ("Core", "D′", "D″"):
                    ptr = row[arm]["参照先"]
                    if ptr is None:
                        continue
                    self.assertEqual(ptr, ptr.lower(), "生の鍵が混ざっている: %s" % ptr)
                    self.assertIn("@", ptr)


class BannedWordsTest(unittest.TestCase):
    """指摘 3。**検査がコードで在り、壊した入力で赤くなる。**"""

    def setUp(self):
        self.M = _mod()

    def test_4_the_guard_fires_on_a_banned_word(self):
        self.assertEqual(self.M.check_banned(u"ふつうの文章です。"), {})
        for w in ("注入", "GROUNDED", "T5", "Core"):
            self.assertIn(w, self.M.check_banned(u"これは %s を含む" % w),
                          "%s を見逃した" % w)

    def test_5_the_record_says_zero_for_every_document(self):
        for p in rec()["書類ごと"]:
            b = p["**見せない字**"]
            self.assertTrue(b["**0 件か**"], "%s で見せない字が在る" % p["docID"])
            self.assertEqual(b["見つかった"], {})
            self.assertGreaterEqual(len(b["検査した語"]), 9)

    def test_6_the_prompt_has_the_three_words_and_no_banned_word(self):
        p = self.M.PROMPT
        for w in (u"確認済み", u"誤りが在る", u"判定できない"):
            self.assertIn(w, p, w)
        self.assertEqual(self.M.check_banned(p), {}, "問いに見せない字が在る")
        self.assertEqual(hashlib.sha256(p.encode("utf-8")).hexdigest(),
                         rec()["問いの sha256"], "問いが記録と違う")


class RowsTest(unittest.TestCase):
    def setUp(self):
        self.r = rec()

    def test_7_every_document_has_eight_injections_and_24_rows(self):
        self.assertEqual(len(self.r["書類ごと"]), 8)
        for p in self.r["書類ごと"]:
            self.assertTrue(p["注入"]["**8 件そろったか**"], p["docID"])
            self.assertEqual(p["注入"]["件数"], 8)
            self.assertTrue(p["行"]["**24 行そろったか**"], p["docID"])
            self.assertEqual(p["行"]["注入の行"], 8)
            self.assertEqual(p["行"]["無改変の行"], 16)
            self.assertNotIn("T2_UNIT", p["注入"]["型の内訳"], "T2 が入っている")
        self.assertEqual(self.r["合計"]["注入"], 64)
        self.assertEqual(self.r["合計"]["行"], 192)

    def test_8_contamination_is_measured_and_reported(self):
        for p in self.r["書類ごと"]:
            c = p["**他の行への影響の検査**"]
            self.assertIn("**判定が動いた**", c)
            self.assertGreaterEqual(c["一意に対になった主張"], 1)
            self.assertFalse(c["書類単位の決定"]["**変わったか**"], p["docID"])

    def test_9_the_material_itself_is_not_in_the_repo(self):
        out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                             capture_output=True, text=True).stdout
        self.assertNotIn("_task.txt", out, "**席に渡す字が repo に入っている**")
        for p in self.r["書類ごと"]:
            self.assertIn("scratchpad", p["材料"]["path"])
            self.assertEqual(len(p["材料"]["sha256"]), 64)

    def test_10_no_seat_was_called(self):
        self.assertIn("席を 1 回も呼んでいない", self.r["step"])
        self.assertIn("**席は 1 回も呼んでいない。**A と C′ の数はまだ 1 つも無い",
                      self.r["limits"][0])
        src = io.open(SCRIPT, encoding="utf-8").read()
        for bad in ("anthropic", "Task(", "subagent", "messages.create"):
            self.assertNotIn(bad, src, bad)


class CommitOrderTest(unittest.TestCase):
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

    def test_11_spec_precedes_this_material(self):
        spec = self._added(SPEC_REL)
        self.assertIsNotNone(spec, "spec が commit されていない")
        mine = self._added("fixtures/xbrl/cd8/material_2026-10-17.json")
        if mine is None:
            return
        self.assertTrue(self._ancestor(spec, mine), "spec が材料より後に在る")


if __name__ == "__main__":
    unittest.main()
