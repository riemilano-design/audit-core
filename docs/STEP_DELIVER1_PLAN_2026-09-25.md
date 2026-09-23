# STEP DELIVER-1 計画(2026-09-25、人間の指示。担当: 新セッション「将棋コーチ｜DELIVER-1原価削減・納品パイプライン」)

棚卸しは [DELIVER_INVENTORY_2026-09-25.md](DELIVER_INVENTORY_2026-09-25.md)(§1 の 17 工程、§4 の作るもの)。この文書はその §4 を、新セッションが単独で実行できる形に書いたもの。基点は feature `0d45055`。

## 1. 目的(人間の言葉)

v7 を基準版として、「**同じ分析結果を、より少ない手作業・確認・AI 処理で納品できる状態**」にする。原則: 「新しいことを考える」のではなく「**今あることを人手なしで同じように出す**」。

## 2. 最重要制約 ― 分析ロジックを変更しない

禁止: 新しい分析指標/新しい探索条件/CAUSE-SEARCH のアルゴリズム変更/閾値変更(`*_VALUES` と `answerMenu.ts` の表)/B の新規ルール/診断内容の高度化/permutation・pattern compression・M10・TYPE-2/v7 の判定結果・文章構造の変更。`lib/` の純粋関数(`reportData.ts`・`whatif.ts`・`read.ts`・`directAnswers.ts`・`finalPosition.ts`・`timeCause.ts`・`timeFeatures.ts`・`timeSearch.ts`・`answerMenu.ts`)と `render_*.py`・`check_answer.py` の判定は触らない(呼び方だけ変える)。

## 3. 実装対象(人間の指定、順に)

1. `pipeline.ts` に `--time-limit-sec`・`--previous` を中継(S5 `reportData.ts` へ。中継するだけ。既定は今のまま = 渡さなければ `byLeft`・`previous` は null)。
2. READ 工程を接続: `pipeline.ts --whatif` の後ろで局ごとに `read.ts --whatif <whatif-v2/<id>.jsonl> --kifu <kifu/<id>.fixed.json> --out <read/<id>.jsonl>`(済みの判定は他の段と同じ流儀: 最後の行が summary)。TYPE(`type.ts`)は繋がない。
3. `scripts/playtest/deliver.ts`(新規): 既存の道具を規定順に**子プロセスで呼ぶだけ**(`pipeline.ts` と同じ流儀。判断・値・文言を持たない)。順: pipeline(S1〜S4 + whatif + READ)→ S5(旗つき)→ S6 の確認点(`prose.json` が無ければ止まる)→ S7 本編 + 付録 1・2 → 付録 3(`directAnswers.ts` → `finalPositions.ts` → `render_direct.py`)→ 付録 4(`timeCause.ts` → `render_time_cause.py`)→(`--previous-work` があるときだけ)探索(`timeSearch.ts` 発見 = 前回・検証 = 今回 → `render_time_cause.py --search`)→ B の下書き(4.)→ 止まる(B の「読み」の確認点)→ `check_answer.py` → `render_answer.py`。引数: `--person --kifu-dir --work --time-limit-sec --name --title --today --out <顧客フォルダ> [--previous-work <前回の work>] [--parallel]`。
4. B の「分かっている事実」を既存 JSON から機械生成: `scripts/playtest/report-pdf/answer_facts.py`(新規)。入力 = `patient_report_data.json`(組ごと)・`direct_answers.json`・`final_positions.json`・`time_cause.json`(・`time_cause_search.json`)。出力 = v7 と同じ見出し構造の md の下書き。**事実の箇条書きは v7 の文をテンプレートにして数だけ差し替える**(文の形を変えない)。「読み」の文・「こうしてみては」の行・「例」の節は `<!-- TODO: 読み -->` のプレースホルダで空け、LLM/人間が埋める。生成した md は必ず `check_answer.py` を通る(生成物が落ちたら生成側の誤り)。
5. 納品ログ `<out>/deliver_log.jsonl`: 段ごとに `{stage, startedAt, finishedAt, rc, humanGate: bool}`。人間の確認点(S6・B の読み・PDF の目視)は「止まった時刻」と「再開の時刻」を残す(= 原価③の測り方)。
6. 伏せ字・個人情報の検査を自動化: `scripts/playtest/report-pdf/check_delivery.py`(新規)。`<out>` の PDF 全冊と md のテキストに、名前(`--forbid <語>` で渡す)・`@`・`/Users/`・「水匠」・禁止語 18 語(悪手・弱点・癖・型・傾向・原因・ミス・見落とし・改善・練習・必ず・明らか・あなた・ご自身・いつも・がち・クセ・パターン。B は既に `check_answer.py` が見るので PDF 側で重複してよい)が無いことを確かめ、あれば rc ≠ 0 で止まる。
7. **既存の出力と DELIVER-1 の出力が一致することの確認**(最重要の試験): 立浪さんの 44 局を固定材料にする。(a) 今回の 14 局(work = `scripts/playtest/out/tatsunami3/pipe`、person `p2`、kifu = `scripts/playtest/out/tatsunami3/kifu`、180 秒、前回 = `scripts/playtest/out/tatsunami20/pipe`)を `deliver.ts` で通し、`patient_report_data.json`・`whatif_report_data.json`・`direct_answers.json`・`final_positions.json`・`time_cause.json`・`time_cause_search.json` が、顧客フォルダ `scripts/playtest/out/立浪さん_2026-09-22/direct/` と `tatsunami3/pipe/report/` の既存のものと **JSON として同一**(`gitHead`・`dirty`・`startedAt` 等の時刻を除く)であること。エンジンの段は済みの判定で飛ぶので再解析は起きない(起きたら済みの判定の誤り)。(b) `answer_facts.py` が v7 の md(`18_B_どうしたら_v7_2026-09-25_送付用.md`)から「事実の箇条書き」の数をすべて再現すること(数の一覧の diff が空)。(c) `check_answer.py`・`render_answer.py` の引数一式が、手で組んでいた `run_check.sh`(下の §5)と同じであること(`--dry-run` で表示して diff)。
8. 監査用テスト 1 回(独立監査 GO)→ コミット。

## 4. 各工程の記録(人間の指定)

`deliver.ts` の README の節に、工程ごとに **入力/出力/所要時間/人間の操作/エラー時の停止条件** を表で書く。所要時間は 7.(a) の実行の `deliver_log.jsonl` から。

## 5. 手で組んでいた引数一式(新セッションが読む。gitignore の `out/` に写しを置いた)

`scripts/playtest/out/_deliver1_handoff/` に、司令塔 e3 が 44 局で使ったスクリプトの写し: `run_check.sh`(`check_answer.py` の引数 20 個: patient ×3 と `--time-limit-sec`、whatif-data ×2、whatif-v2-dir ×2、read-dir ×2、type-summary ×2、whatif-pdf ×3(付録 2 ×2 + 付録 3)、direct ×2、time-cause、time-search、menu)、`run_render.sh`(同じ引数で `render_answer.py`)、`rerun_s5_direct.sh`(S5 を旗つきで呼び直した形)、`make_direct.sh`(付録 3 の 3 コマンド)。`answer_menu.json` は `lib/answerMenu.ts` の表から `npx tsx scripts/playtest/answerMenuJson.ts`(あれば)か、写しをそのまま使う(`_deliver1_handoff/answer_menu.json`)。**`--whatif-pdf` に付録 3 の PDF を渡す**のは、B の読み筋の手(付録 3 の印字)を検査 2 で照合するため(STEP TIME-CAUSE §6.3・§8.5)。

## 6. 完了条件(人間の指定)

- 既存 v7 の分析結果を変更せず納品まで通せる(7.(a)(b)(c))。
- 手作業の箇所が一覧化されている(§4 の表の「人間の操作」列)。
- 自動化された箇所が確認できる(棚卸し §1 の「自動化」の行が `deliver.ts` のどの段に対応するか)。
- 失敗時にどこで止まったか分かる(`deliver_log.jsonl` の最後の行と、非 0 の rc の段の名前)。
- 0 worktrees、vitest・typecheck-scripts・check-docs、独立監査 GO、コミットまで。

## 7. 完了後の報告(人間の指定、4 点)

「何を自動化したか」「何分の作業が削減されたか」(削減は、棚卸し §1 の手回し 4 か所 + B の事実の節、について `deliver_log.jsonl` の所要と、手回しのときの推定(手順の数)を並べて書く。**測っていないものは推定と明記**)「まだ残っている人間作業」「次に測定すべき原価」。

## 8. 進め方の規則(このリポジトリの慣行)

- 1 作業 1 セッション。実装は worktree の使い捨てサブエージェント、独立監査 1 回、往復 1 回まで。**`git stash` を使わない**(共有スタッシュ)。コミットは `git add` を使わずパス指定(新規は `git add -N` → `git commit -F <file> -- <paths>`)、末尾に `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`。エンジンは 5 本まで(この STEP では済みの判定により起きないはず。起きたら止めて確かめる)。
- 相手の名前・元ファイル名・`@`・`/Users/` のパス・「水匠」を、記録・報告・コミット文に書かない。顧客フォルダの既存ファイルを書き換えない(一致の確認は写しとの diff)。
- 動きを変える変更は監査 GO を経てから承認。測っていないものは承認しない。
- vitest は `npx vitest run scripts/playtest --exclude '.claude/**'`(基点 1516)。本体ツリーの typecheck は gitignore の `out/` の古い草稿で落ちる既知の状態(worktree では 0)。

## 9. 記録

- 2026-09-25: 計画(司令塔 e3)。着手は新セッション。
