#!/bin/sh
# STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)。凍結した第 6 版テンプレートの 6 本を連結して、
# render_main.py(本編)・render_appendix.py(別冊)を作るだけの小さなスクリプト。
# 中身(_head.py・_util.py・_mid.py・_app_head.py・_app.py・_tail.py)は変えない(パスの受け取り方だけ変えてある。README.md 参照)。
set -eu
cd "$(dirname "$0")"
cat _head.py _util.py _mid.py > render_main.py
cat _head.py _util.py _app_head.py _app.py _tail.py > render_appendix.py
echo "render_main.py・render_appendix.py を作った"
