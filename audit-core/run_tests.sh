#!/bin/sh
# 標準の検証。**この 1 本を走らせれば、試験 file が 1 本も漏れていないことまで確かめる。**
#
# 人間の指示 2026-10-16:
#   > 重要なのはコマンドの数ではなく、**新しい門を追加したのに標準の検証から漏れる
#   > 事故**を防ぐことです。
#
# 段 6〜段 9 で私は「全体 1,065 OK」と報告していたが、`unittest discover` は
# `tests/measure`(43 file)にも `measure/tests`(1 file)にも降りていなかった。
# **全部を覆うのは `pytest` だけ**である(2026-10-14 の記録のとおり)。
#
#   1. 覆いの検査 ― ディスク上の試験 file が全部収集されるか(**試験は走らせない**)
#   2. pytest    ― **全数**(99 file)
#   3. unittest discover ― 別の runner でもう一度(`tests/` 以下の package)
#
# どれか 1 つでも落ちたら全体を落とす。
set -e
cd "$(dirname "$0")"
echo "--- 1/3 覆いの検査 ---"
python3 -B measure/suite_coverage_2026-10-16.py
echo "--- 2/3 pytest(全数)---"
python3 -B -m pytest -q -p no:cacheprovider
echo "--- 3/3 unittest discover ---"
python3 -B -m unittest discover
echo "--- 全部通った ---"
