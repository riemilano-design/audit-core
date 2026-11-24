# 試験の時間の内訳 ― tests/measure(2026-11-24 実測)

CLAUDE.md の「遅い試験の内訳」の置き場。数は 1 回の実測(`python3 -m pytest -q tests/measure --durations=0 -p no:cacheprovider`、この worktree、他の席の作業と並べて走らせた)。

## 1. 全体

- 7742 passed・49 skipped・5 warnings、**2 時間 2 分 53 秒(7373.88 秒)**。2026-11-15 の実測(約 1 時間 12 分)より長い。並べて走らせた負荷か、その後に足した試験かは分けていない。
- 時間を記録した試験の file は 250(tests/measure の .py は 292)。10 秒以上かかった段(call・setup・teardown)は 218。

## 2. 遅い所

- **1 つの試験が全体の 4 割**: `test_xbrl_tanshin_self_inject_seal.py` の `MutantTest::test_k_1_every_check_is_green_on_the_real_code_and_red_on_each_mutant` が 2847.54 秒。この file 全体で 2949.06 秒。
- **変異の試験が全体の 7 割弱**: class の名が `Mutant…Test`・`Mutation…Test` の試験の合計が 5017.58 秒(記録した段の合計 7329.03 秒のうち)。
- 次に遅い file(合計秒): input_type_v1_seal 305.68・suite_coverage 302.77・fresh_seal 241.93・input_type_v1_result 241.69・company_excel_seal 220.06・vocab_result 153.54・scope_cond_seal 149.78・plan_attr_seal 146.81。

## 3. 速い束の案(まだ走らせていない)

- ふだんの束: `python3 -m pytest -q tests/measure -k "not Mutant and not Mutation"`。差し引きの見込みは 7329 − 5018 ≈ 2311 秒(約 39 分)だが、**この束はまだ実測していない**。`-k` が class の名で外れることも、走らせて確かめてから使う。
- 変異の試験は「門が変異で赤くなる」を確かめる試験なので、枝を寄せる前と外に出す数を作る時(CLAUDE.md の「全部の門」の時)には全部走らせる。
- 遅い 1 本(inject_seal の k_1)は、変異の数を減らすか分けるかで短くなりうるが、試験の中身を変えるのは動きを変える変更なので、人間の決めと監査が要る。
