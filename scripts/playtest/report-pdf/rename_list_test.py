# -*- coding: utf-8 -*-
# `rename_list.py`(改名の一覧)の試験。**合成の git リポジトリだけ**を使う。
#
# 【なぜ合成材料だけか】① の制約(仕様 §4):**実物での確認は門にできない** ―
# 顧客の棋譜と診断データをリポジトリに置けないため。実物での確認は記録にする。
#
# 【この試験が守っているもの】道具を作るときに踏んだ 3 つの穴が戻らないこと。
# どれも「黙って落ちる」型だったので、**止めたら赤になる**ことを 1 本ずつ測る。
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rename_list as RL


class Repo:
    """合成の git リポジトリ。コミットを順に積んで、日付も指定する。"""

    def __init__(self, path):
        self.path = path
        self.run("init", "-q", "-b", "main")
        self.run("config", "user.email", "t@example.com")
        self.run("config", "user.name", "t")

    def run(self, *args):
        r = subprocess.run(["git", *args], cwd=self.path, capture_output=True, text=True)
        if r.returncode != 0:
            raise AssertionError(f"git {args[0]} が失敗: {r.stderr}")
        return r.stdout

    def write(self, rel, text):
        full = os.path.join(self.path, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(text)

    def commit(self, message, when):
        self.run("add", "-A")
        env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
        r = subprocess.run(["git", "commit", "-q", "-m", message], cwd=self.path,
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            raise AssertionError(f"git commit が失敗: {r.stderr}")


class RenameListTestBase(unittest.TestCase):
    PATHS = ["scripts/playtest/report-pdf", ":(glob)scripts/playtest/*.ts"]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(self.tmp.name)

    def scan(self, since="2026-01-01 00:00", since_newer=None):
        return RL.Scanner(self.tmp.name, self.PATHS).scan(since, since_newer)

    def render_py(self, title):
        return (f'# -*- coding: utf-8 -*-\n'
                f'# ==================== 「{title}」の節 ====================\n'
                f'story.append(P("{title}", S_H2))\n')


class FindsRenamesTest(RenameListTestBase):
    def test_00_rename_in_a_heading_style_line(self):
        """`S_H2)` の行の改名を見つける(md の `## ` だけ見ていたら落ちる形)。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("古い題"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("新しい題"))
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        self.assertEqual([(r["old"], r["new"]) for r in got["renamed"]], [("古い題", "新しい題")])

    def test_01_rename_into_a_constant_is_found(self):
        """**穴 1**: 定数に置き換えた改名。新しい側に日本語の文字列が無くても見つける。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("古い題"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\nTITLE = "新しい題"\n'
                        'story.append(P(TITLE, S_H2))\n')
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        pairs = [(r["old"], r["new"]) for r in got["renamed"]]
        self.assertIn(("古い題", "新しい題"), pairs,
                      f"定数の値に直せていない(要目視: {got['eyeball']})")

    def test_02_md_heading_rename_is_found(self):
        """md は `#` の行を見る。"""
        self.repo.write("scripts/playtest/report-pdf/a.md", "# 古い見出し\n\n本文\n")
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/a.md", "# 新しい見出し\n\n本文\n")
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        self.assertEqual([(r["old"], r["new"]) for r in got["renamed"]],
                         [("古い見出し", "新しい見出し")])

    def test_03_python_comment_bar_is_not_a_heading(self):
        """python の `# ==== …` は見出しではない(md 見出しは .md に限る)。

        限らないと、コメントの書き換えが改名として大量に出て**本物が埋まる**。
        """
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\n# ==================== 古いコメント ====================\nx = 1\n')
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\n# ==================== 新しいコメント ====================\nx = 1\n')
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        # **3 つのバケツすべてで 0 件。**A と C だけを見ると、制限を外したときに
        # コメントの書き換えが **B(包み替え)に落ちて**見逃せる(校正で実測 2026-09-29)。
        self.assertEqual(got["renamed"], [])
        self.assertEqual(got["eyeball"], [])
        self.assertEqual(got["wrapped"], [], "コメントの書き換えがどのバケツにも出てはいけない")


class NeverSilentTest(RenameListTestBase):
    def test_04_one_sided_hunk_goes_to_eyeball_not_to_nowhere(self):
        """**穴 2**: 片側だけの hunk を捨てない。**黙って 0 にしない。**"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        # 題は同じままで、包む関数だけを足す(足された側にだけ別の日本語が出る)
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\n'
                        '# ==================== 「題」の節 ====================\n'
                        'story.append(mark(P("題", S_H2), "索引の鍵"))\n')
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        self.assertEqual(got["renamed"], [], "改名ではない")
        self.assertEqual(len(got["eyeball"]), 1, f"要目視に出ていない: {got}")
        self.assertEqual(got["eyeball"][0]["gone"], [])
        self.assertIn("索引の鍵", got["eyeball"][0]["came"])

    def test_04b_a_title_moved_into_a_call_is_not_a_rename(self):
        """**独立監査が見つけた偽陽性**(2026-09-29)。

        見出しの行が `X_TITLE = tool.title("種別", "節")` の形になると、
        **呼び出しの引数の日本語まで拾う**。旧題の対になる文字列が新旧に共通して消えると、
        **無関係な引数が「新名」として 1:1 に組まれ、いまの正しい題を「写してはいけない旧名」として警告する。**
        道具の目的と正反対なので、**A に落とさず C に出す。**
        """
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\n'
                        'story.append(mark(P("現行の題そのまま", S_H2), "節キー"))\n')
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py",
                        '# -*- coding: utf-8 -*-\n'
                        'X_TITLE = tool.title("種別X", "節キー")\n'
                        'story.append(mark(P(X_TITLE, S_H2), "節キー"))\n')
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        self.assertEqual(got["renamed"], [],
                         "改名していない現行の題を『旧名』として確定させてはいけない")
        self.assertTrue(got["eyeball"], "拾えなかったものが C に出ていない")

    def test_04c_a_deleted_file_is_not_silent(self):
        """**独立監査が見つけた無音**(2026-09-29)。

        `+++ /dev/null` は `+++ b/` で始まらないので、直さないと
        **path が前のファイルのままか None になり、A・B・C のどこにも出ない。**
        自分のコメントに書いた「黙って 0 にしない」に反していた。
        """
        self.repo.write("scripts/playtest/report-pdf/keep.py", 'x = 1\n')
        self.repo.write("scripts/playtest/report-pdf/gone.py", self.render_py("消える題"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.run("rm", "-q", "scripts/playtest/report-pdf/gone.py")
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        notes = [r for r in got["eyeball"] if r.get("note") == "ファイルごと消えた"]
        self.assertTrue(notes, f"ファイル全削除が黙って消えている: {got}")
        self.assertEqual(notes[0]["file"], "gone.py")
        self.assertIn("消える題", notes[0]["gone"])

    def test_05_new_file_is_not_a_rename(self):
        """**穴 3**: 新規ファイルは全行が「足された」になる。改名として出さない。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", 'x = 1\n')
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/new.md", "# 見出し 1\n\n## 見出し 2\n\n本文\n")
        self.repo.commit("2", "2026-02-02 10:00:00")
        got = self.scan()
        self.assertEqual(got["renamed"], [])
        self.assertEqual(got["eyeball"], [], f"新規ファイルが雑音になっている: {got['eyeball']}")

    def test_06_empty_range_is_an_error_not_an_empty_list(self):
        """**範囲が空なら落とす。**0 件を「改名なし」と読むと、写しが安全に見えてしまう。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", 'x = 1\n')
        self.repo.commit("1", "2026-02-01 10:00:00")
        with self.assertRaises(RL.RenameListError) as e:
            self.scan(since="2027-01-01 00:00")
        self.assertIn("コミットが無い", str(e.exception))

    def test_07_wrong_path_is_an_error_not_an_empty_list(self):
        """見る経路が違っても同じ ― 0 件で通さない。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", 'x = 1\n')
        self.repo.commit("1", "2026-02-01 10:00:00")
        with self.assertRaises(RL.RenameListError):
            RL.Scanner(self.tmp.name, ["no/such/path"]).scan("2026-01-01 00:00")


class RangeTest(RenameListTestBase):
    def test_08_commits_before_since_are_excluded(self):
        """範囲より前の改名は出ない(**範囲を狭めると落ちる** ― 実物の mtime を使う理由)。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 A"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 B"))
        self.repo.commit("2", "2026-02-02 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 C"))
        self.repo.commit("3", "2026-03-10 10:00:00")
        wide = self.scan(since="2026-01-01 00:00")
        narrow = self.scan(since="2026-03-01 00:00")
        self.assertEqual([(r["old"], r["new"]) for r in wide["renamed"]],
                         [("題 B", "題 C"), ("題 A", "題 B")])
        self.assertEqual([(r["old"], r["new"]) for r in narrow["renamed"]],
                         [("題 B", "題 C")])

    def test_09_since_newer_marks_which_real_booklet_is_affected(self):
        """2 つの実物があるので、**どちらに効く改名か**を行ごとに分ける。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 A"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 B"))
        self.repo.commit("2", "2026-02-02 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("題 C"))
        self.repo.commit("3", "2026-03-10 10:00:00")
        got = self.scan(since="2026-01-01 00:00", since_newer="2026-03-01 00:00")
        which = {(r["old"], r["new"]): r["which"] for r in got["renamed"]}
        self.assertEqual(which[("題 B", "題 C")], "両方")
        self.assertEqual(which[("題 A", "題 B")], "古い実物のみ")


class RenderTest(RenameListTestBase):
    def test_10_the_report_names_all_three_buckets(self):
        """A・B・C の 3 つを必ず出す(C を出さないと、拾えなかったものが見えない)。"""
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("古い題"))
        self.repo.commit("1", "2026-02-01 10:00:00")
        self.repo.write("scripts/playtest/report-pdf/r.py", self.render_py("新しい題"))
        self.repo.commit("2", "2026-02-02 10:00:00")
        text = RL.render(self.scan(), "2026-01-01 00:00", None)
        self.assertIn("## A. 改名", text)
        self.assertIn("## B. 改名なし", text)
        self.assertIn("## C. 要目視", text)
        self.assertIn("古い題", text)
        self.assertIn("新しい題", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
