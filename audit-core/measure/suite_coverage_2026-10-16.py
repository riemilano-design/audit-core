# -*- coding: utf-8 -*-
"""**試験 file が 1 本も標準の検証から漏れていないこと**を機械で確かめる。

人間の指示 2026-10-16:

> 重要なのはコマンドの数ではなく、**新しい門を追加したのに標準の検証から漏れる事故**を
> 防ぐことです。

私の誤り(段 6〜段 9 で繰り返した): 「全体 1,065 OK」と報告していたが、
`audit-core/` からの `unittest discover` は **`tests/measure`(43 file・1,022 本)にも
`measure/tests`(1 file・96 本)にも降りていなかった。**
`tests` は package なのに `tests/measure` に `__init__.py` が無いので、
unittest の探索は**package でない下位ディレクトリを飛ばす**。
`measure/` も package でないので丸ごと飛ばされる。

この file は**試験を走らせない。**ディスク上の試験 file を数え上げ、
各コマンドが**収集するか**を調べ、**どのコマンドにも収集されない file を落とす。**

    python3 measure/suite_coverage_2026-10-16.py
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "fixtures", "suite_coverage_2026-10-16.json")
SKIP_DIRS = (".git", "node_modules", "__pycache__", ".pytest_cache")

# **標準のコマンドをここ 1 か所に書く。**run_tests.sh も門もこれを読む
COMMANDS = [
    {"id": "pytest",
     "cmd": ["python3", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"],
     "collect": ["python3", "-B", "-m", "pytest", "--collect-only", "-q",
                 "-p", "no:cacheprovider"],
     "must_cover_everything": True,
     "note": "全部を覆う唯一のコマンド(2026-10-14 の記録のとおり)"},
    {"id": "discover",
     "cmd": ["python3", "-B", "-m", "unittest", "discover"],
     "collect": None,          # unittest は API で数える
     "must_cover_everything": False,
     "note": "`tests/` 以下の package だけ。**package でない下位は飛ばす**"},
]


def test_files():
    """ディスク上の `test_*.py` を全部数え上げる(repo-relative の道)。"""
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                out.append(os.path.relpath(os.path.join(base, f), ROOT))
    return sorted(out)


def collected_by_unittest():
    """`unittest discover` が収集する file の道(module 名から引き直す)。"""
    loader = unittest.TestLoader()
    suite = loader.discover(ROOT, top_level_dir=ROOT)
    mods = set()

    def walk(x):
        if isinstance(x, unittest.TestSuite):
            for y in x:
                walk(y)
        else:
            mods.add(type(x).__module__)

    walk(suite)
    out = set()
    for m in mods:
        p = os.path.join(*m.split(".")) + ".py"
        if os.path.exists(os.path.join(ROOT, p)):
            out.add(p)
    return out, len(mods), suite.countTestCases()


def collected_by_pytest(cmd):
    """`pytest --collect-only -q` が収集する file の道。"""
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    files, n = set(), None
    for line in r.stdout.split("\n"):
        line = line.strip()
        m = re.match(r"^(\S+?\.py)::", line)
        if m:
            files.add(m.group(1))
        m2 = re.match(r"^(\d+) tests? collected", line)
        if m2:
            n = int(m2.group(1))
    return files, n, r.returncode


def judge(per, uncovered):
    """**落ちた本を出す。**正常な入力では発火しない守りなので、試験が壊した入力を
    食わせて赤を確かめられるよう main から切り出してある
    (記憶 `guard-that-only-fires-on-failure.md`)。
    """
    fail = []
    for c in COMMANDS:
        p = per.get(c["id"])
        if p is None:
            fail.append("**標準コマンド %s の収集を測っていない**" % c["id"])
            continue
        if p["collect_rc"] != 0:
            fail.append("%s の収集が落ちた(rc=%d)" % (c["id"], p["collect_rc"]))
        if c["must_cover_everything"] and p["missed_files"]:
            fail.append("**%s が %d 本の試験 file を収集していない**: %s"
                        % (c["id"], len(p["missed_files"]), p["missed_files"][:5]))
    if not any(c["must_cover_everything"] for c in COMMANDS):
        fail.append("**全部を覆う約束をしたコマンドが 1 つも無い**")
    if uncovered:
        fail.append("**どの標準コマンドにも収集されない試験 file が %d 本在る**: %s"
                    % (len(uncovered), sorted(uncovered)[:5]))
    return fail


def main(write=False):
    files = set(test_files())
    uni, uni_mods, uni_n = collected_by_unittest()
    per = {}
    uncovered = dict((f, []) for f in files)
    for c in COMMANDS:
        if c["id"] == "discover":
            got, n, rc = uni, uni_n, 0
        else:
            got, n, rc = collected_by_pytest(c["collect"])
        missed = sorted(files - got)
        extra = sorted(got - files)
        per[c["id"]] = {"collected_files": len(got & files), "tests": n,
                        "missed_files": missed, "extra_files": extra,
                        "collect_rc": rc, "note": c["note"],
                        "must_cover_everything": c["must_cover_everything"]}
        for f in got & files:
            uncovered.pop(f, None)

    fail = judge(per, uncovered)

    rec = {"purpose": ("**試験 file が 1 本も標準の検証から漏れていないこと**。"
                       "人間の指示 2026-10-16。**試験は走らせない。収集だけ数える**"),
           "test_files_on_disk": len(files),
           "by_directory": _by_dir(files),
           "unittest_modules": uni_mods,
           "commands": per,
           "uncovered_files": sorted(uncovered),
           "failures": fail,
           "why_discover_misses": (
               "`tests` は package だが `tests/measure` に `__init__.py` が無いので、"
               "unittest の探索は**package でない下位ディレクトリを飛ばす**。"
               "`measure/` も package でないので丸ごと飛ぶ"),
           "why_measure_cannot_be_a_package": (
               "`measure/__init__.py` を足すと `measure.tests.test_inject` が"
               "`tests.*` より先に読み込まれ、その 39 行目の "
               "`sys.path.insert(0, MEASURE)` が **`import tests` を "
               "`measure/tests/` に解決させる**。実測で `tests.core` など 5 つが "
               "ImportError になり、収集が 2,087 本から 101 本に崩れた。**だから足さない**"),
           }
    # **既定では記録を書かない。**標準の検証(`run_tests.sh`)がこの file を
    # 書き換えてしまうと、**検証を走らせた事自体で緑の木が赤くなる**
    # (2026-10-16 実測。共有ツリーの初回の完走がこれで落ちた)。
    # 記録を更新するのは `--write` を付けたときだけにする。
    stale = _stale(rec)
    if write:
        json.dump(rec, io.open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    elif stale:
        fail = list(fail) + [
            "**記録が古い**(%s)。`python3 measure/suite_coverage_2026-10-16.py "
            "--write` で更新し、文書の数も直すこと" % "・".join(stale)]

    print("=== 試験の覆いの検査(人間の指示 2026-10-16)===")
    print("ディスク上の試験 file: %d 本" % len(files))
    for k, v in sorted(rec["by_directory"].items()):
        print("   %-24s %d" % (k, v))
    for c in COMMANDS:
        p = per[c["id"]]
        print("%-9s 収集 %3d file / %s 本%s"
              % (c["id"], p["collected_files"],
                 p["tests"] if p["tests"] is not None else "?",
                 "" if not p["missed_files"]
                 else "  **漏れ %d 本**" % len(p["missed_files"])))
        for f in p["missed_files"]:
            print("            漏れ: %s" % f)
    print()
    if fail:
        print("**落ちた %d 本:**" % len(fail))
        for f in fail:
            print("  - %s" % f)
    else:
        print("**どの試験 file も標準のコマンドに収集されている。**")
    print("->", OUT if write else "%s(読むだけ)" % OUT)
    if fail:
        sys.exit(1)


def _stale(rec):
    """記録とこの場の実測が食い違っている欄を並べる(**書き換えずに**比べる)。"""
    try:
        old = json.load(io.open(OUT, encoding="utf-8"))
    except Exception as e:                                   # 記録が無い・壊れた
        return ["記録を読めない: %s" % e]
    out = []
    if old.get("test_files_on_disk") != rec["test_files_on_disk"]:
        out.append("試験 file %s -> %s"
                   % (old.get("test_files_on_disk"), rec["test_files_on_disk"]))
    if old.get("by_directory") != rec["by_directory"]:
        out.append("ディレクトリごとの内訳")
    for cid, p in rec["commands"].items():
        o = (old.get("commands") or {}).get(cid) or {}
        if o.get("tests") != p["tests"]:
            out.append("%s の本数 %s -> %s" % (cid, o.get("tests"), p["tests"]))
        if o.get("collected_files") != p["collected_files"]:
            out.append("%s の file 数 %s -> %s"
                       % (cid, o.get("collected_files"), p["collected_files"]))
    return out


def _by_dir(files):
    """**鍵を並べて返す。**`main` が set を渡すので、並べないと記録の鍵の順が
    実行ごとに変わり、**中身が同じでも git の差分が出る**(2026-10-16 実測)。"""
    out = {}
    for f in files:
        d = os.path.dirname(f) or "."
        out[d] = out.get(d, 0) + 1
    return dict(sorted(out.items()))


if __name__ == "__main__":
    main(write="--write" in sys.argv[1:])
