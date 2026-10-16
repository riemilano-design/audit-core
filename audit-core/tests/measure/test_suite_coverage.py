# -*- coding: utf-8 -*-
"""**試験 file が 1 本も標準の検証から漏れていないこと**を固定する。

人間の指示 2026-10-16:

> 重要なのはコマンドの数ではなく、**新しい門を追加したのに標準の検証から漏れる事故**を
> 防ぐことです。

守るのは 8 つ。
  1. ディスク上の試験 file を**数え上げ直して**記録と一致すること
  2. **全部を覆う約束をしたコマンドが在り、実際に 1 本も漏らしていない**こと
  3. どの標準コマンドにも収集されない file が **0 本**であること
  4. **判定に歯が在る**こと(壊した入力を食わせて赤になる)
  5. `run_tests.sh` が `COMMANDS` の字をそのまま走らせること
  6. `measure/__init__.py` を**足していない**こと、その理由が記録に在ること
  7. `measure/tests/test_inject.py` の `sys.path.insert` が実在すること
     (案 B を却下した根拠。消えたら却下の理由も変わる)
  8. 私が「全体 1,065 OK」と報告していた誤りが記録に在ること
"""
import importlib.util
import io
import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(ROOT, "measure", "suite_coverage_2026-10-16.py")
OUT = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
SH = os.path.join(ROOT, "run_tests.sh")
DOC = os.path.join(ROOT, "docs", "SUITE_COVERAGE_2026-10-16.md")


def load(p):
    with io.open(p, encoding="utf-8") as fh:
        return json.load(fh)


def text(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def mod():
    sp = importlib.util.spec_from_file_location("suite_cov_t", SRC)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class CountTest(unittest.TestCase):
    def setUp(self):
        self.m = mod()
        self.rec = load(OUT)

    def test_1_recount_the_files_on_disk(self):
        """**記録ではなく、いま数え上げ直して一致すること。**

        試験 file を足したらこの門が赤くなる ― **それが狙いである。**
        `python3 measure/suite_coverage_2026-10-16.py` を走らせ直すこと。
        """
        files = self.m.test_files()
        self.assertEqual(len(files), self.rec["test_files_on_disk"],
                         "試験 file の数が記録と違う。覆いの検査を走らせ直すこと")
        self.assertEqual(self.m._by_dir(set(files)), self.rec["by_directory"])
        # この門の file 自身が数に入っていること(数え上げが届いている証拠)
        self.assertIn("tests/measure/test_suite_coverage.py", files)

    def test_2_pytest_covers_everything(self):
        p = self.rec["commands"]["pytest"]
        self.assertTrue(p["must_cover_everything"])
        self.assertEqual(p["missed_files"], [])
        self.assertEqual(p["collected_files"], self.rec["test_files_on_disk"])
        self.assertEqual(p["collect_rc"], 0)

    def test_3_nothing_is_uncovered(self):
        self.assertEqual(self.rec["uncovered_files"], [])
        self.assertEqual(self.rec["failures"], [])

    def test_4_discover_is_declared_partial(self):
        """**discover は全部を覆わない。**覆うふりをしないこと。"""
        d = self.rec["commands"]["discover"]
        self.assertFalse(d["must_cover_everything"])
        self.assertGreater(len(d["missed_files"]), 0,
                           "discover が全部覆っているなら約束を書き換えるべき")
        self.assertIn("package でない下位", d["note"])


class LiveCoverageTest(unittest.TestCase):
    """**記録に依らず、いま測って「漏れが 0 本」であること。**

    記録は古くなり得る。この門は毎回**ディスクと収集を両方その場で測る**ので、
    記録を更新し忘れても漏れを見逃さない。
    """

    def test_19_pytest_collects_every_file_right_now(self):
        m = mod()
        files = set(m.test_files())
        full = [c for c in m.COMMANDS if c["must_cover_everything"]]
        self.assertTrue(full, "全部を覆う約束をしたコマンドが無い")
        for c in full:
            got, n, rc = m.collected_by_pytest(c["collect"])
            self.assertEqual(rc, 0, "%s の収集が落ちた" % c["id"])
            missed = sorted(files - got)
            self.assertEqual(missed, [],
                             "**%s が収集していない試験 file が在る**: %s"
                             % (c["id"], missed[:5]))
            self.assertGreaterEqual(n, len(files),
                                    "収集した本数が file 数より少ない")

    def test_20_unittest_collection_is_a_subset_and_measured(self):
        m = mod()
        files = set(m.test_files())
        uni, mods, n = m.collected_by_unittest()
        self.assertTrue(uni <= files, "discover が試験 file 以外を収集している")
        self.assertGreater(len(uni), 0)
        self.assertEqual(len(uni), mods)


class EnumerationIsIndependentlyCheckedTest(unittest.TestCase):
    """**数え上げを狭めて file を隠す**緩め方を止める(変異 W3 が黙った穴)。

    `test_files()` を信じず、**別の道具(glob)で独立に数え直して**突き合わせる。
    """

    def test_21_glob_agrees_with_the_walk(self):
        import glob
        m = mod()
        want = set()
        for pat in ("test_*.py", "*/test_*.py", "*/*/test_*.py",
                    "*/*/*/test_*.py", "*/*/*/*/test_*.py"):
            for f in glob.glob(os.path.join(ROOT, pat)):
                if "__pycache__" in f or "/.git/" in f:
                    continue
                want.add(os.path.relpath(f, ROOT))
        got = set(m.test_files())
        self.assertEqual(got, want,
                         "walk と glob が食い違う(数え上げが狭められていないか)")

    def test_22_every_directory_with_tests_is_counted(self):
        """**試験 file を持つディレクトリが 1 つも落ちていないこと。**"""
        m = mod()
        dirs = set(m._by_dir(set(m.test_files())))
        # `measure/tests` は `tests/` の外に在る ― ここが W3 で消えた
        for d in ("tests/measure", "tests/adapters/xbrl", "tests/core",
                  "tests/golden", "tests/fixtures/xbrl", "measure/tests"):
            self.assertIn(d, dirs, "%s が数え上げから落ちている" % d)
        self.assertTrue(any(not d.startswith("tests/") for d in dirs),
                        "`tests/` の外の試験 file を 1 つも数えていない")

    def test_23_the_walk_starts_at_the_repo_root(self):
        m = mod()
        src = text(SRC)
        self.assertIn("for base, dirs, files in os.walk(ROOT):", src,
                      "数え上げの起点が repo の根でない")


class CollectorHasTeethTest(unittest.TestCase):
    """**収集器が本当に出力を読んでいるか**(変異 W4 が黙った穴)。

    `collected_by_pytest` が「全部在る」と嘘をついても気づかない門では意味が無い。
    **範囲を狭めたコマンドを食わせて、結果が真部分集合になること**を要求する。
    """

    def test_24_narrowing_the_command_narrows_the_result(self):
        m = mod()
        full = [c for c in m.COMMANDS if c["must_cover_everything"]][0]
        got_all, n_all, rc = m.collected_by_pytest(full["collect"])
        self.assertEqual(rc, 0)
        narrowed = list(full["collect"]) + ["tests/core"]
        got_one, n_one, rc2 = m.collected_by_pytest(narrowed)
        self.assertEqual(rc2, 0)
        self.assertTrue(got_one, "狭めたら 0 file になった(読めていない)")
        self.assertLess(len(got_one), len(got_all),
                        "**範囲を狭めても結果が同じ ― 出力を読んでいない**")
        self.assertLess(n_one, n_all)
        for f in got_one:
            self.assertTrue(f.startswith("tests/core/"), f)

    def test_25_a_broken_command_is_reported(self):
        m = mod()
        got, n, rc = m.collected_by_pytest(
            ["python3", "-B", "-m", "pytest", "--collect-only", "-q",
             "tests/does_not_exist_zz"])
        self.assertNotEqual(rc, 0, "在らない道を指しても rc=0 ― 読めていない")


class JudgeHasTeethTest(unittest.TestCase):
    """**壊した入力を食わせて赤になるか**(記憶 `guard-that-only-fires-on-failure`)。"""

    def setUp(self):
        self.m = mod()
        self.rec = load(OUT)
        self.per = {k: dict(v) for k, v in self.rec["commands"].items()}

    def test_5_real_record_passes(self):
        self.assertEqual(self.m.judge(self.per, []), [])

    def test_6_a_file_missed_by_the_full_command_is_red(self):
        per = {k: dict(v) for k, v in self.per.items()}
        per["pytest"]["missed_files"] = ["tests/measure/test_new_gate.py"]
        self.assertTrue(self.m.judge(per, []))

    def test_7_an_uncovered_file_is_red(self):
        self.assertTrue(self.m.judge(self.per, {"measure/tests/test_x.py": []}))

    def test_8_a_failed_collection_is_red(self):
        per = {k: dict(v) for k, v in self.per.items()}
        per["pytest"]["collect_rc"] = 2
        self.assertTrue(self.m.judge(per, []))

    def test_9_an_unmeasured_command_is_red(self):
        per = {k: dict(v) for k, v in self.per.items()}
        per.pop("pytest")
        self.assertTrue(self.m.judge(per, []))

    def test_10_no_full_coverage_promise_is_red(self):
        m = self.m
        keep = [dict(c) for c in m.COMMANDS]
        try:
            for c in m.COMMANDS:
                c["must_cover_everything"] = False
            self.assertTrue(m.judge(self.per, []))
        finally:
            m.COMMANDS[:] = keep


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.m = mod()
        self.sh = text(SH)

    def test_11_runner_exists_and_is_executable(self):
        self.assertTrue(os.access(SH, os.X_OK), "run_tests.sh に実行権が無い")
        self.assertTrue(self.sh.startswith("#!/bin/sh"))
        self.assertIn("set -e", [l.strip() for l in self.sh.split("\n")],
                      "set -e の行が無い(コメントアウトされていないか)")

    def test_12_runner_runs_every_declared_command(self):
        """**COMMANDS に書いたコマンドが runner に字で在ること。**"""
        for c in self.m.COMMANDS:
            self.assertIn(" ".join(c["cmd"]), self.sh,
                          "runner が %s を走らせていない" % c["id"])
        self.assertIn("measure/suite_coverage_2026-10-16.py", self.sh)

    def test_13_runner_names_the_full_command(self):
        self.assertIn("**全部を覆うのは `pytest` だけ**", self.sh)


class RejectedOptionTest(unittest.TestCase):
    """案 B(`measure/` を package にする)を**却下した根拠**を留める。"""

    def test_14_measure_is_not_a_package(self):
        self.assertFalse(os.path.exists(os.path.join(ROOT, "measure", "__init__.py")),
                         "measure/__init__.py が在る ― 収集が崩れる")

    def test_15_the_reason_is_recorded(self):
        why = load(OUT)["why_measure_cannot_be_a_package"]
        self.assertIn("sys.path.insert(0, MEASURE)", why)
        self.assertIn("2,087 本から 101 本に崩れた", why)
        self.assertIn("**だから足さない**", why)

    def test_16_the_sys_path_insert_still_exists(self):
        """却下の根拠が消えていないこと(消えたら案 B を測り直す)。"""
        t = text(os.path.join(ROOT, "measure", "tests", "test_inject.py"))
        self.assertIn("sys.path.insert(0, MEASURE)", t)

    def test_17_why_discover_misses_is_recorded(self):
        why = load(OUT)["why_discover_misses"]
        self.assertIn("package でない下位ディレクトリを飛ばす", why)
        self.assertIn("`measure/` も package でない", why)


class DocTest(unittest.TestCase):
    """記録(docs/SUITE_COVERAGE_2026-10-16.md)を固定する。"""

    def setUp(self):
        self.t = text(DOC)
        self.rec = load(OUT)

    def test_26_my_error_is_stated(self):
        self.assertIn("**「全体 1,065 OK」は全体ではなかった**", self.t)
        self.assertIn("**`measure/tests/test_inject.py` の 96 本は、", self.t)
        self.assertIn("どちらにも入っていなかった。**", self.t)
        self.assertIn("**私はその記録を読まずに同じ型を繰り返した。**", self.t)
        self.assertIn("CONSOLIDATION_P20_RESULT_2026-10-14.md", self.t)

    def test_27_counts_match_the_record(self):
        self.assertIn("ディスク上の試験 file: **%d 本**"
                      % self.rec["test_files_on_disk"], self.t,
                      "文書の file 数が記録と違う。覆いの検査を走らせ直して "
                      "文書も直すこと")
        for d, n in self.rec["by_directory"].items():
            self.assertIn("| `%s` | %d |" % (d, n), self.t, d)
        # §2-2 は変更前の歴史的な実測。**いまの数は §3-2 と突き合わせる**
        p = self.rec["commands"]["pytest"]
        d2 = self.rec["commands"]["discover"]
        self.assertIn("| `pytest -q`(path 指定なし) | **%s** | **%d / %d** |"
                      % ("{:,}".format(p["tests"]), p["collected_files"],
                         self.rec["test_files_on_disk"]), self.t)
        self.assertIn("| `unittest discover`(ルートから) | **%s** | **%d / %d** |"
                      % ("{:,}".format(d2["tests"]), d2["collected_files"],
                         self.rec["test_files_on_disk"]), self.t)
        self.assertIn("**この節は変更前の実測で、後の記録と結び付けない**", self.t)

    def test_28_option_b_is_recorded_as_rejected(self):
        self.assertIn("### 案 B `measure/__init__.py` も足す → **却下**", self.t)
        self.assertIn("**101 本 / 2 モジュール**", self.t)
        self.assertIn("`sys.path.insert(0, MEASURE)`", self.t)
        self.assertIn("だから `measure/__init__.py` は足さない。**", self.t)

    def test_29_option_a_is_recorded_as_adopted(self):
        self.assertIn("### 案 A `tests/measure/__init__.py` を足す → **採用**", self.t)
        self.assertIn("**2,087 本 / 98 モジュール**", self.t)

    def test_30_shadowing_recheck_is_recorded(self):
        self.assertIn("**既知の影は健在である。**", self.t)
        self.assertIn("**42 件の読み込み失敗**", self.t)
        self.assertIn("`-t .` を付ければ 0 件に戻る。", self.t)

    def test_32_my_measurement_was_contaminated_once(self):
        """**却下した案の残骸が次の測定を汚した**ことを開示している。"""
        self.assertIn("### §3-1 **一度測り間違えた(自分の後片付け漏れ)**", self.t)
        self.assertIn("**98 件の収集エラー**", self.t)
        self.assertIn("injected-errors-contaminate-each-other", self.t)
        self.assertIn("**却下した案の残骸が次の測定を汚した。**", self.t)
        self.assertIn("**2,087 OK**", self.t)

    def test_33_full_runs_are_recorded(self):
        """**完走の数が記録に在ること。**収集が通っただけで緑と書かない。"""
        self.assertIn("**2,182 passed / 1 skipped**(rc=0・21 分 00 秒)", self.t)
        self.assertIn("**2,087 OK**(skip 1・20 分 56 秒)", self.t)
        self.assertIn("## §3-2 共有ツリーに入れた後の実測", self.t)

    def test_34_option_a_is_applied_with_its_reason(self):
        init = os.path.join(ROOT, "tests", "measure", "__init__.py")
        self.assertTrue(os.path.exists(init), "案 A が入っていない")
        s = text(init)
        self.assertIn("package でない下位ディレクトリを飛ばす", s)
        self.assertIn("**`measure/__init__.py` は置かない。**", s)
        self.assertIn("2,087 本から 101 本に崩れる", s)

    def test_31_limits(self):
        self.assertIn("**「収集された」と「緑だった」は別である。**", self.t)
        self.assertIn("**1 つのコマンドで全部走るわけではない。**", self.t)
        self.assertIn("この整備は**試験の数を増やしていない。**", self.t)
        self.assertIn("**試験 file を 1 本足すと覆いの記録が古くなって門が赤くなる "
                      "― それが狙いである。**", self.t)


class MyErrorTest(unittest.TestCase):
    def test_18_the_misreport_is_recorded(self):
        """**「全体 1,065 OK」は全体ではなかった**という私の誤りを留める。"""
        t = text(SRC)
        self.assertIn("「全体 1,065 OK」と報告していたが", t)
        self.assertIn("tests/measure", t)
        self.assertIn("measure/tests", t)


class RecordIsStableAndReadOnlyTest(unittest.TestCase):
    """**標準の検証が記録を書き換えないこと。**

    2026-10-16 実測。共有ツリーでの初回の完走が落ちた ―
    `run_tests.sh` の 1 段目が記録を**書き換え**、2 段目の `pytest` が
    「記録と文書が合わない」で赤くなった。**検証を走らせた事自体で緑の木が赤くなる。**
    だから既定は**読むだけ**にし、更新は `--write` のときだけにした。

    あわせて、記録の鍵の順が実行ごとに変わっていた(`main` が set を渡しており
    文字列の hash が実行ごとに違う)。中身が同じでも git の差分が出るので
    **差分が意味を失う。**`_by_dir` が鍵を並べて返すことを固定する。
    """

    def test_35_by_directory_keys_are_sorted(self):
        m = mod()
        d = m._by_dir(set(m.test_files()))
        self.assertEqual(list(d), sorted(d), "鍵が並んでいない")
        rec = load(OUT)["by_directory"]
        self.assertEqual(list(rec), sorted(rec),
                         "記録の鍵が並んでいない。--write で更新すること")

    def test_36_two_builds_agree_on_order(self):
        """**順まで同じ**(dict の等号は順を見ないので、別に見る)。"""
        m = mod()
        a = list(m._by_dir(set(m.test_files())))
        b = list(m._by_dir(set(m.test_files())))
        self.assertEqual(a, b)

    def test_37_the_default_run_does_not_write_the_record(self):
        before = io.open(OUT, "rb").read()
        r = subprocess.run(["python3", "-B", SRC], capture_output=True, text=True)
        self.assertEqual(io.open(OUT, "rb").read(), before,
                         "**既定の実行が記録を書き換えた**")
        self.assertIn("読むだけ", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout[-400:])

    def test_38_a_stale_record_fails_and_write_fixes_it(self):
        """**歯。**記録を 1 か所壊すと落ち、`--write` で直ること。"""
        before = io.open(OUT, "rb").read()
        rec = json.loads(before.decode("utf-8"))
        rec["commands"]["pytest"]["tests"] = -1
        io.open(OUT, "w", encoding="utf-8").write(
            json.dumps(rec, ensure_ascii=False, indent=1))
        try:
            r = subprocess.run(["python3", "-B", SRC],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, "古い記録で落ちていない")
            self.assertIn("**記録が古い**", r.stdout)
            w = subprocess.run(["python3", "-B", SRC, "--write"],
                               capture_output=True, text=True)
            self.assertEqual(w.returncode, 0, w.stdout[-400:])
            self.assertNotEqual(io.open(OUT, "rb").read(),
                                json.dumps(rec, ensure_ascii=False,
                                           indent=1).encode("utf-8"))
        finally:
            io.open(OUT, "wb").write(before)

    def test_39_the_runner_does_not_pass_write(self):
        """`run_tests.sh` が `--write` を渡さないこと(渡したら 37 の意味が消える)。"""
        self.assertNotIn("--write", text(SH))
        self.assertIn("python3 -B measure/suite_coverage_2026-10-16.py", text(SH))


if __name__ == "__main__":
    unittest.main()
