# -*- coding: utf-8 -*-
u"""10 分の再現の儀式の封 docs/XBRL_RITUAL_SEAL_2026-10-20.md を固定する。
人間の方針の引用・§0-1 の先に測った数(同梱 zip を道具の既定で 1 回走らせて再現する)・
予測 R-1〜R-8 と外れ方・§2 の HUMAN 2 点・§3 の file 一覧・封が実装より先であること(順序)を縛る。"""
import hashlib
import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from adapters.xbrl import vocabulary as V  # noqa: E402
from adapters.xbrl.verify_document import verify_document  # noqa: E402

SEAL_REL = "docs/XBRL_RITUAL_SEAL_2026-10-20.md"
SEAL = os.path.join(ROOT, SEAL_REL)
ZIP_REL = "fixtures/xbrl/ai_prose_instance_2026-10-09.zip"
ZIP = os.path.join(ROOT, ZIP_REL)
# §3 の file 一覧(この順で書かれている)
FILES = ("measure/ritual_2026-10-20.py",
         "fixtures/xbrl/ritual_2026-10-20.json",
         "docs/XBRL_RITUAL_RESULT_2026-10-20.md",
         "README.md",
         "README.en.md",
         "tests/measure/test_xbrl_ritual_result.py")
# 封より後でなければ git 履歴に現れてはならない新規 file(README は既存なので除く)
AFTER = ("measure/ritual_2026-10-20.py",
         "fixtures/xbrl/ritual_2026-10-20.json",
         "docs/XBRL_RITUAL_RESULT_2026-10-20.md",
         "tests/measure/test_xbrl_ritual_result.py")


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def sec(t, start, end=None):
    i = t.index("\n" + start)
    j = t.index("\n" + end, i + 1) if end else len(t)
    return t[i:j]


def predictions(block, tag):
    ids = re.findall(r"(?m)^\| \*\*%s-(\d+)\*\* \|" % tag, block)
    lines = re.findall(r"(?m)^\| \*\*%s-\d+\*\* \|.*$" % tag, block)
    return ids, lines


class SealTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = text(SEAL)
        # zip は git に入っていない(.gitignore の *.zip。同梱は HUMAN の判断待ち)。無い機械では zip を読む門は skip する。
        cls.zb = None
        if os.path.exists(ZIP):
            with open(ZIP, "rb") as fh:
                cls.zb = fh.read()

    def need_zip(self):
        if self.zb is None:
            self.skipTest(u"同梱 zip が無い(未追跡。HUMAN の判断待ち)")

    def test_1_human_policy_is_quoted(self):
        head = self.t[:self.t.index("\n## §0")]
        self.assertIn(u"**人間の方針(2026-10-20)**: 上げる手 4 つのうち「2 = 誤りを通さない再現の儀式を包装に」を 3 群の後に(「1・4 は後回し、順番は任せる」)。", head)
        self.assertIn(u"戦略 第 1 版 芯 (5)「完成の定義 = 買い手が 1 日で再現でき、穴が全部文書に在る」。", head)
        self.assertIn(u"**数を見てから封・予測を直さない。外れは外れとして残す。**", head)

    def test_2_target_command_input_and_zero_cost(self):
        b = sec(self.t, "## §0 ", "## §0-1")
        for s in (u"`python3 measure/ritual_2026-10-20.py --out <dir>`", u"`vocabulary.DEFAULT_PROFILE`",
                  u"`fixtures/xbrl/ai_prose_instance_2026-10-09.zip`",
                  u"**外部との通信なし・API 鍵なし・0 USD**", u"**この zip 以外の入力を読まない**",
                  u"`<dir>/ritual.json`", u"`<dir>/ritual.md`", u"engine 0 行"):
            self.assertIn(s, b, s)

    def test_3_pre_measured_numbers_are_pinned_as_written(self):
        b = sec(self.t, "## §0-1", "## §1")
        for s in (u"claim 412、GROUNDED 330・POINTER_NOT_FOUND 16・UNVERIFIABLE 41・VALUE_MISMATCH 25",
                  u"site 304、土台の不一致 8、注入の対象(GROUNDED の site)241、**止めた 224・通した 17**",
                  u"V2(±1 最小単位)16・V1 1",
                  u"`0百万円 → 00百万円`"):
            self.assertIn(s, b, s)
        # 数の内部整合(字で留めた数同士)
        self.assertEqual(224 + 17, 241)
        self.assertEqual(16 + 1, 17)
        self.assertEqual(330 + 16 + 41 + 25, 412)
        # §1 の R-2 が §0-1 と同じ数を言っていること
        r2 = [l for l in sec(self.t, "## §1", "## §2").splitlines() if l.startswith("| **R-2**")][0]
        for s in (u"**241**", u"**224**", u"**17**"):
            self.assertIn(s, r2, s)

    def test_4_eight_predictions_each_with_a_way_to_fail(self):
        b = sec(self.t, "## §1", "## §2")
        ids, lines = predictions(b, "R")
        self.assertEqual(ids, [str(i) for i in range(1, 9)])
        self.assertEqual(len(lines), 8)
        for line in lines:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            self.assertEqual(len(cells), 3, line)
            self.assertTrue(cells[1], u"予測が空: " + line)
            self.assertTrue(cells[2], u"外れ方が空: " + line)
        for s in (u"**60 秒以内**", u"60 秒超", u"が 1 件**", u"0 件 / 2 件以上", u"**16 件が帯の中**", u"**0 件**",
                  u"通した 17 / 241 = 7.1%", u"止めた 224 / 241 = 92.9%", u"**30 秒以内**", u"**150 秒以内**",
                  u"engine(`core/`・`adapters/`)0 行"):
            self.assertIn(s, b, s)
        self.assertEqual(round(100.0 * 17 / 241, 1), 7.1)
        self.assertEqual(round(100.0 * 224 / 241, 1), 92.9)

    def test_5_cannot_say_has_two_human_points(self):
        b = sec(self.t, "## §2", "## §3")
        self.assertEqual(b.count("HUMAN"), 2)
        self.assertIn(u"**EDINET の書類を売却の包装に同梱してよいかは人間の判断(HUMAN)**", b)
        self.assertIn(u"**HUMAN**: 1 行の docstring の直しの承認。", b)
        self.assertIn(u"`adapters/xbrl/verify_document.py` の docstring", b)
        self.assertIn(u"買い手が自分の書類で回すには鍵と `~/.cache` が要る", b)

    def test_6_closed_file_list(self):
        b = sec(self.t, "## §3")
        first = b[:b.index(u"**これ以外に触らない。")]
        pos = []
        for rel in FILES:
            tok = "`%s`" % rel
            self.assertEqual(first.count(tok), 1, rel)
            pos.append(first.index(tok))
        self.assertEqual(pos, sorted(pos), u"file 一覧の順が変わった")
        self.assertIn(u"**これ以外に触らない。engine 0 行。0 USD。**", b)
        self.assertIn(u"`tests/measure/test_xbrl_ritual_seal.py`", b)

    def test_7_input_zip_sha256_and_bytes_match_the_seal(self):
        self.need_zip()
        b = sec(self.t, "## §0 ", "## §0-1")
        m = re.search(r"sha256 `([0-9a-f]{64})`、([\d,]+) bytes", b)
        self.assertIsNotNone(m)
        self.assertEqual(hashlib.sha256(self.zb).hexdigest(), m.group(1))
        self.assertEqual(len(self.zb), int(m.group(2).replace(",", "")))
        self.assertEqual(len(self.zb), 580260)

    def test_8_p21_run_on_the_bundled_zip_reproduces_section_0_1(self):
        # 封 §0-1 の数は P21 で測った数。2026-10-20 の期を縛る P22 の段 2 で既定は P22 になった(素の書類で GROUNDED 1 行が
        # VALUE_MISMATCH になる)ので、測った当時の P21 を**明示**して再現する(字で留める)。P22 の数は結果の門 test_xbrl_ritual_result.py が記録で縛る。
        self.need_zip()
        b = sec(self.t, "## §0-1", "## §1")
        m = re.search(r"claim (\d+)、GROUNDED (\d+)・POINTER_NOT_FOUND (\d+)・UNVERIFIABLE (\d+)・VALUE_MISMATCH (\d+)", b)
        self.assertIsNotNone(m)
        want = {"GROUNDED": int(m.group(2)), "POINTER_NOT_FOUND": int(m.group(3)),
                "UNVERIFIABLE": int(m.group(4)), "VALUE_MISMATCH": int(m.group(5))}
        out = verify_document(self.zb, "P21", None)  # 封 §0-1 を測った当時の profile(2026-10-20 段 2 より前の既定)
        self.assertEqual(out["profile"], "P21")
        self.assertEqual(out["document"]["claims"], int(m.group(1)))
        self.assertEqual(out["document"]["states"], want)
        self.assertEqual(sum(want.values()), int(m.group(1)))

    def test_10_seal_states_the_zip_is_not_in_git_and_waits_for_human(self):
        # 同梱が決まったら封の追記でこの門を更新する(いまは「git には入っていない」が事実)
        b = sec(self.t, "## §0 ", "## §0-1")
        self.assertIn(u"git には入っていない", b)
        self.assertIn(u"HUMAN", b)
        self.assertIn(u"承認されるまで儀式は実装しない", b)
        self.assertIn(u"人間の同梱の承認 →", sec(self.t, "## §3"))
        self.assertIn(u"git には入っていない(2026-10-20 に封の門の実装席が発見)", sec(self.t, "## §2", "## §3"))
        # 追記(同梱の承認)。本文は変えず、日付つきの追記だけ
        a = sec(self.t, "## 追記(2026-10-20)同梱の承認", "## 追記(2026-10-20)ラベル 2 file への依存の見落とし")
        for s in (u"「任せる進めて」", u"同梱の承認", u"`!fixtures/xbrl/ai_prose_instance_2026-10-09.zip`",
                  u"`S100Z4Q1`", u"E36539", u"**済み**", u"R-1〜R-8 は変えない"):
            self.assertIn(s, a, s)
        # 追記(ラベル 2 file への依存の見落とし)。本文・上の追記は変えず、日付つきの追記だけ
        a2 = sec(self.t, "## 追記(2026-10-20)ラベル 2 file への依存の見落とし")
        for s in (u"ラベル 2 file", u"`TAXONOMY_DIR_DEFAULT`", u"`EDINET_TAXONOMY_DIR`", u"選択肢 2", u"選択肢 1(8 MB の同梱)は人間が望めば後から",
                  u"2026-10-08 の人間の決定", u"`fixtures/xbrl/TAXONOMY_LABELS_README.md`", u"rc=2", u"R-1 は条件つき",
                  u"164〜168 秒", u"`AUDIT_CORE_RITUAL=1`", u"R-7 の判定は外れ", u"**予測 R-1〜R-8 は変えない。**"):
            self.assertIn(s, a2, s)

    def test_12_the_zip_is_tracked_in_git(self):
        # 同梱の承認(封の追記)後の門。司令塔が `git add -f` するまでは赤(index に無い)。
        run = lambda *a: subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run("ls-files", "--error-unmatch", ZIP_REL).returncode, 0, u"zip が git に追跡されていない")

    def test_13_gitignore_exception_exists_and_the_zip_is_not_ignored(self):
        run = lambda *a: subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True, text=True)
        gi = text(os.path.join(ROOT, ".gitignore")).splitlines()
        self.assertIn("*.zip", gi)
        self.assertIn("!" + ZIP_REL, gi)
        self.assertLess(gi.index("*.zip"), gi.index("!" + ZIP_REL), u"例外は *.zip の後ろ")
        self.assertEqual(run("check-ignore", "-q", ZIP_REL).returncode, 1, u"zip がまだ無視される")
        self.assertEqual(run("check-ignore", "-q", "fixtures/xbrl/some_other_file.zip").returncode, 0, u"他の zip は無視されたまま")


class OrderTest(unittest.TestCase):
    @staticmethod
    def _added(rel):
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel],
                             cwd=ROOT, capture_output=True, text=True)
        shas = [s for s in out.stdout.split() if s]
        return shas[-1] if shas else None

    def test_11_the_seal_precedes_every_later_file(self):
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", SEAL_REL],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            # 封が履歴に無い間に、後の file が履歴に現れていたら赤(順序の逆転)。何も無いことは pass と言わず skip で残す。
            for rel in AFTER:
                self.assertIsNone(self._added(rel), u"封より先に履歴に現れた: " + rel)
            self.skipTest(u"封がまだ commit されていない")
        seal = self._added(SEAL_REL)
        for rel in AFTER:
            other = self._added(rel)
            if other is None:
                continue
            self.assertNotEqual(seal, other, rel)
            self.assertTrue(subprocess.run(["git", "merge-base", "--is-ancestor", seal, other],
                                           cwd=ROOT, capture_output=True).returncode == 0, rel)


if __name__ == "__main__":
    unittest.main()
