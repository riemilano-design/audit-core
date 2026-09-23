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

`scripts/playtest/out/_deliver1_handoff/` に、司令塔 e3 が 44 局で使ったスクリプトの写し: `run_check.sh`(`check_answer.py` の引数 20 個: patient ×3 と `--time-limit-sec`、whatif-data ×2、whatif-v2-dir ×2、read-dir ×2、type-summary ×2、whatif-pdf ×3(付録 2 ×2 + 付録 3)、direct ×2、time-cause、time-search、menu)、`run_render.sh`(同じ引数で `render_answer.py`)、`rerun_s5_direct.sh`(S5 を旗つきで呼び直した形)、`make_direct.sh`(付録 3 の 3 コマンド)。`answer_menu.json` は `lib/answerMenu.ts` の表から `npx tsx scripts/playtest/answerMenu.ts`(README の「行動のメニュー」の節)で作るか、写しをそのまま使う(`_deliver1_handoff/answer_menu.json`)。**`--whatif-pdf` に付録 3 の PDF を渡す**のは、B の読み筋の手(付録 3 の印字)を検査 2 で照合するため(STEP TIME-CAUSE §6.3・§8.5)。

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

## 10. 実装の記録(2026-09-23。担当セッション「DELIVER-1 原価削減・納品パイプライン」)

コミット: `59c46b9`(基点 `44f0296`)。独立監査 GO。0 worktrees。

### 10.1 §3 の 1〜6 の実装

| 計画 | 実装 |
|---|---|
| 1. `--time-limit-sec`・`--previous` の中継 | `lib/pipeline.ts`・`pipeline.ts`。どちらも**任意のキー**(渡さなければ `reportDataCommand` は末尾に何も足さない = 今までと同じ引数・同じ出力) |
| 2. READ 工程の接続 | `lib/pipeline.ts` の `--whatif` のブロックの後ろ。**v2 のときだけ**(`read.ts` の入力は whatif-v2)。済みの判定は他の段と同じ(最後の行が `summary`)。`timing.jsonl` に `stage: "read"`。TYPE は繋いでいない |
| 3. `deliver.ts` | 16 段。純粋な部分は `lib/deliver.ts`(試験 46 本)、CLI の殻は子プロセスの起動と fs だけ。段ごとの表は `scripts/playtest/README.md` |
| 4. `answer_facts.py` | B の「分かっている事実」14 本。数は `check_answer.py` の材料から**引くだけ**(同ファイルを import。1 バイトも変えていない) |
| 5. `deliver_log.jsonl` | 段ごとに `{stage, startedAt, finishedAt, rc, humanGate}`。人間の確認点は止まった行と再開の行の 2 行 |
| 6. `check_delivery.py` | `<out>` の PDF 全冊と md。禁止語 18 語は `check_answer.py` の `BANNED_WORDS` の先頭 18 語を import(二重に持たない) |

### 10.2 §3 の 7 の結果(固定材料 44 局・3 組。独立監査が自分で再測した数)

- **6 つのうち 5 つが JSON として同一**(`gitHead`・`dirty`・`startedAt` を除く): `patient_report_data.json`・`whatif_report_data.json`・`direct_answers.json`・`final_positions.json`・`time_cause_search.json`。
- **`time_cause.json` だけ相違**。相違は 44 局のうち 20 局(前回の組)の `forkAmongLongThink`・`oppositeSideAmongForkLongThink`・`midMoveSeconds[].fork` が null → 値つきになったこと、およびそれに伴う 3 分の組の `forkFraction`・`oppositeSideFraction`(C7 が 9/35 → 25/68、C8 が 1/9 → 2/25)。10 分の組は完全一致。**理由は材料の違いで、道具の判定は変わっていない**。対照 2 本を測って切り分けた: (i) 前回の組の `--whatif-v2-dir` を**渡して**手回しした出力 = `deliver.ts` の出力、(ii) **渡さずに**手回しした出力 = 既存の顧客フォルダのファイル。**どちらも同一**。既存ファイルは前回の組に `whatif-v2` が無かった時期に作られている。
- (b) `answer_facts.py`: 事実の箇条書き **14 / 14** を生成し、基準版の同じ 4 ブロックと**数の一覧(118 個)が順序つきで一致、かつ文字まで同一**。落とした箇条書きは 0。生成物は `check_answer.py` rc=0(校正: 数を 1 つ変えると rc=1)。
- (c) `check_answer.py`・`render_answer.py` の引数: 手回しの写し(`run_check.sh`・`run_render.sh`)と**旗の種類・回数・組の順が完全一致**(各 22 旗)。正規化は役割だけ(work → 組の番号、出力フォルダ → `OUT`)。
- 回帰: vitest **1516 → 1579 passed・0 failed**(88 files)。worktree で `typecheck-scripts` rc=0・`check-docs` rc=0。本体ツリーの `typecheck-scripts` は rc=1 だが、10 件すべて gitignore の `out/` の古い草稿で、**`out/` の外は 0 件**(§8 に書いた既知の状態のまま)。
- 変異 4 本(組の順序を逆・`read/` の無い組に `--read-dir`・中継を消す・連結の順を逆)は予測どおり検知(6・2・2・2 本)。監査は別の 1 本(`read/` のフィルタ)を抜き取りで回し 3 本の失敗を確認。
- 所要(`deliver_log.jsonl`、24 行): `pipeline-data` 24.9 秒・`pipeline-pdf` 2.2 秒・`appendix4-search` 6.9 秒・`appendix3-final` 1.4 秒(**エンジンを回したのはここだけ**・3 局面)・他は 0.6 秒以下。初回通しで約 37.5 秒(S1〜S4・whatif・READ は済みの判定で飛んでいる)。
- 固定材料(前回の組・今回の組・10 分の組・顧客フォルダ・手回しの写し)は**無変更**を実測で確認。書き込みは gitignore の `out/_deliver1_verify/` だけ。

### 10.3 計画に無い判断(記録として残す)

- **司令塔**: `deliver.ts` に `--group-work`/`--group-time-limit-sec`(任意・繰り返し)を足した。**理由**: §3.7(a) の固定材料 44 局は 3 つの work にまたがるが、§3.3 の引数は `--work` と `--previous-work` の 2 つしか名前を持たず、3 つ目の組を渡す道が無いと一致確認ができない。通常の顧客(前回 + 今回)では渡さない。既定は `[前回, 今回]` の順。
- **司令塔**: 「事実の箇条書き」の範囲を、基準版が自分で `**分かっている事実**` と見出しを付けた 4 ブロック(14 本)に定めた。`**機械に探させた結果**`・`**こうしてみては**`・`## 例`・`## 数を見て取り下げたこと`・`## やらなくていいこと`・`## 次の 20 局…` は「読み」なので `<!-- TODO: 読み -->` で空ける。**基準版自身の見出しを境目にした**(こちらで都合よく線を引かないため)。
- **司令塔**: `<out>` のファイル名を固定(`1_まとめ.pdf`・`2_付録1_形勢が動いた対局.pdf`・`3_付録2_分かれ道.pdf`・`5_付録3_直接の答え.pdf`・`6_付録4_時間の使い方.pdf`・`8_B_どうしたら_下書き.md`・`8_B_どうしたら.pdf`)。`--out` に `deliver.ts` 自身が書く名前以外のファイルがあれば何もせず止まる(既存の顧客フォルダの取り違え防止。実測: 顧客フォルダを渡すと rc=2・書き込み 0)。
- **実装担当**: (i) その実行自身が作るファイルについては引数の選び方をファイルの存在に依らせない(`--dry-run` と実行が食い違うため)。(ii) `finalPositions.ts` は選ばれた局が 0 のとき rc=1 なので、時間切れ負け 0 局の組は飛ばす(判定は実行時)。(iii) `answer_facts.py` は `--read-dir`/`--whatif-v2-dir` も受ける(`check_answer.py` が同じ材料を作るのに要る)。(iv) `--name` を引数で受け、表示名をソースに持たない。(v) 「今回の組」= そのタグの最後の `--patient`、「24 局」= `read/` の `*.jsonl` のファイル数。(vi) `--parallel` は渡されたときだけ中継。
- **実装担当が見つけた材料の誤り**: 手回しの写し `make_direct.sh` の連結 python は鍵の名前が古い(`positions` を見るが実際は `entries`)。あのファイルは手で結合されたものと読める。`deliver.ts` は「先頭のメタ + `entries` を組の順に連結」を実装しており、既存ファイルと一致する。
- **基準版の文から引き継いだ主張が 1 つある**: 6 本目の箇条書きの「飛車の筋 … 共通しません」は基準版の文言のままで、コードが差し替えるのは局数だけ。**新しい顧客では人間が確かめる必要がある**(道具はこの主張を作り直さない)。

### 10.4 残っている人間の作業と、次に測るもの

- 人間の確認点は 3 つのまま: `prose-gate`(言い換え)・`answer-gate`(「読み」を書く)・`check-delivery`(PDF の目視)。
- `--forbid` に何を渡すかは人間が決める。**実測: 顧客自身の表示名を渡すと必ず落ちる**(本人の冊子に本人の名前が出るのは正しい。42 件)。渡さなければ rc=0(7 ファイル・禁止語 0)。
- **人間の判断が要る 1 件**: 次の納品で `time_cause.json` を作り直した側(C7 25/68)で出すか、基準版の材料(9/35)を保つか。作り直すと基準版 B の 4 本目の箇条書きの数が動く。
- 次に測るべき原価: **③ 人間の確認時間**。上の所要は道具の時間だけで、`prose-gate`・`answer-gate` は「止まった時刻 / 再開の時刻」の欄を用意しただけで、まだ人間の実作業では測っていない(この STEP の検証では下書きの中身を書いていない)。**2 人目の納品で実測する。**
