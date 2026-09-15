# STEP D0-SIDE(番号は仮)計画: 本人が後手の棋譜を、本人が先手の形にそろえる(2026-09-15)

**状態**: **計画(確定。司令塔、2026-09-15)**。書いたのは 1e。**二本立て ― 先に案 3、並行して案 1(3.)。** 案 1 は確認 2(3.1)の読み「`apps/` に触らず `scripts/` の R-1〜R-7 で足りる」を採る。この計画書の範囲ではエンジンを使わない。
**段取り(司令塔)**:
- 監査は A(64)。**A が計画を事前に読み、指摘があれば取り込んでから実装に入る**
- 実装は 1e が worktree で行う
- R-5〜R-7 は D1 の lib に触るので、固定例「開始局面を渡すと、渡さないときと違う結果になる」と変異「`meta` の `startSfen` を読まない」を必ず入れる
- 段 R(エンジン)は、実装の GO の後に司令塔の合図で 1 本
- `~/Desktop/kifu-samples/` にファイルが来たら、**実装より先に読み込み検査**(案 3 の先手の局を先に流すため。10.)
- **追加(2026-09-15、`a011c05` の後)**: 司令塔の追加の決定 2 点(名前の `@` の規則・奇数手数の最後の手を落とす R-8)と、監査 A の事前読み(下書き `0af796d6` に対する必須 3・推奨 5)を本文に取り込んだ。取り込み先の対応は 11.。その後の A の追加の事前読み(`@` の突き合わせ・R-8)と、それへの司令塔の決定も取り込んだ(11.3)。**Q-6〜Q-8 は司令塔が決めた。残る決定は Q-9 と、R-8 の `truncatedTrailingMove` を 1 つの欄にまとめた形の確認**(その後、`null` はやめて `trailingMoveTruncated` を常に書く形に決まった。12.6)
**基点**: HEAD `4f5964d`(読んだ実物はこの版)。
**きっかけ**: 司令塔の依頼。人間が実棋譜を集めた。本人が後手の局が半分近くあると見込まれる。
**置き場所**: `docs/STEP_D0-SIDE_PLAN_2026-09-15.md`(司令塔がコミットする。計画は文書なので監査不要)。

---

## 0. 先に書く: 「回すだけ」では、再生に通らない

依頼の案は「本人が後手の局を 180 度回転して先後を入れ替え、本人を常に先手にする」だった。**手を回すことそのものは正しい変換だが、回した棋譜は後手から指し始める。** 平手の初期局面は 180 度回しても同じ形だが、**最初に指すのは元の先手(相手)で、回すと相手の側の手(後手の駒の手)になる。**

- 例: 相手(先手)の 1 手目 `7g7f` → 回すと `3c3d`(**後手の歩を突く手**)。本人(後手)の 1 手目 `3c3d` → 回すと `7g7f`(先手の歩を突く手)
- **回した手順は `[3c3d, 7g7f, …]` で、後手が先に指す**

**いまの道具はどれも「平手の初期局面・先手から指す」を前提にしている**(2. の E-1〜E-4)。`replay.ts` は初期局面(先手番)から `playHumanMove(state, moves[0])` を呼ぶので、**回した棋譜をそのまま渡すと 1 手目の `3c3d`(先手番で後手の歩を動かす)が非合法になり、`human_move_error` で止まる**(予-S1)。

したがって、この STEP で決めるべきことは座標の変換より先に、**「後手から指し始める棋譜」を道具にどう渡すか**である(3.)。

---

## 1. 目的と範囲

- **目的**: 実棋譜のうち本人が後手の局を、既存の道具(`replay.ts` → `diagnose.ts`、先手視点の死因①・JSON v0 の奇数/偶数の ply)で読める形にする
- **範囲**: `scripts/playtest/lib/` の純粋関数(手の変換・本人の側の判定)と、`kifuImport` の出力(固定棋譜 JSON)に足す欄。**`apps/` と `data/` には触れない**(3. の案 1 で `apps/` に触れる必要が出たら、そこで止めて司令塔に上げる)
- **前提**: 開始局面は平手(`kifuImport` が平手以外を `unsupported_start` にする。変えない)
- **固定棋譜 JSON に残すもの**(案): `mirrored: true`、`originalUserSide: "gote"`、`plyOffset`(3. の案 1 のとき 1)、`startSfen`(同)。**元の棋譜の手順は別に残す**(段 2 で `originalMoves` の欄にした。本人が先手の局は `mirrored: false` だけを書く。12.7)(回した手順から戻せるが、戻す計算を報告の根拠にしない)
- **本人の選び方**(案、6. の Q-2): `--me <名前>` でヘッダの先手・後手の名前と突き合わせる。KIF は `先手：` / `後手：` の行、CSA は `N+` / `N-` の行(どちらも `kifuImport` が「読んだが使わない行」の header に入れている)。**一致が 0 か 2 なら取り込まず、理由 `user_side_unknown` を返す(推測しない)**。`--as sente|gote` で明示もできる。**本人の名前は人間が教える。報告・コミットに相手の名前を書かない**
- **名前の比べ方(司令塔の決定、2026-09-15)**: この出どころの書き出しでは、ヘッダの名前の欄が `名前@▲4八銀` のように `@` の後ろに文字が付くことがある(11.1)。**ヘッダの値から最初の `@` 以降を落とした部分と、`--me` を完全一致で比べる**(表記ゆれの吸収はしない。**落とす前の生の文字列は、本人の側だけを取り込みの記録に残す。相手の名前は残さない**(8.。司令塔の決定))。KIF(`先手：` / `後手：`)と CSA(`N+` / `N-`)で同じ規則。**名前そのものに `@` が入っていると、そこで切れる**(決定的な規則の限界として受け入れる)

## 2. 実物から分かった前提(HEAD `4f5964d`)

| # | 事実 | 場所 | 影響 |
|---|---|---|---|
| E-1 | `replay.ts` は `createInitialGameState` から始め、`moves` を 2 手ずつ `(先手 = playHumanMove, 後手 = 固定の応手)` で読む。**ready 行は開始局面(ply 0)に 1 本と、2 手ごとに 1 本。** **手数が奇数なら、最後の組で `odd_move_count` の error 行を書き、それまでの行といっしょにファイルへ書いてから exit 1 で止まる**(監査 A の事前読み。**「読めない」ではなく「最後の組を欠いた記録が残る」**) | `scripts/playtest/replay.ts:193`(開始)・`:205`(ply 0 の ready)・`:228`(2 手ずつ読む)・`:234`(`odd_move_count`)・`:244`(`playHumanMove`)・`:314`(組ごとの ready) | 後手から始まる棋譜はそのままでは読めない。**最後の手を指したのが先手の局は、最後の組を欠いた記録になり、`diagnose.ts` はそれを黙って 1 局として数える**(A の読み: `readInput` は `kind: "record"` だけを読む)。見本の 1 局(37 手・先手の勝ち)はこれに当たる。**R-8 で直す** |
| E-2 | `createInitialGameState` の局面は定数 `INITIAL_SFEN`(平手・先手番)で、開始局面を受ける引数が無い | `apps/server/src/game/gameSession.ts:26`・`:115-124` | 開始局面を変えるには `apps/` を変えるか、`scripts` 側で `GameState` を組む |
| E-3 | D1 と JSON v0 は「**先手の手 = 奇数の ply、ready 行 = 偶数の ply**」で書かれている(`branchPly` 奇数、`fromReadyPly`・`toReadyPly`・`checks`・`consequences.mate` 偶数)。死因①は先手優勢 → 急落 → 後手の手で自玉に王手・詰み | `docs/STEP_JSON-V0_PLAN_2026-09-15.md` 2.2(`:53`・`:59-60`・`:82-83`)、`scripts/playtest/lib/failureEvent.ts:94`・`:196-218` | 本人を先手にそろえるなら、**本人の手が奇数の ply に来る形**にしないと、この前提が崩れる |
| E-4 | **開始局面を差し替える口は、解析の側にはある**: `failureEvent.ts` の `actualContinuation(…, initialSfen = DEFAULT_INITIAL_SFEN)`、`stateResponse.ts:1198` の `options.initialSfen ?? DEFAULT_INITIAL_SFEN`、`recognitionTimeline`・`shapeFormationAnalyzer`・`intentDetector`・`captureSummary`・`japaneseMoveHistory` も `initialSfen` を受ける(「MVP では常に startpos のため通常は指定不要(テスト用の差し替え口)」) | 各ファイル(`git grep DEFAULT_INITIAL_SFEN`) | **`replay.ts`・`recorder.ts` がこの口に値を渡しているかは確かめていない**(3. の案 1 の最初の確かめ) |
| E-5 | 180 度回転のマスの変換は既にある: `scripts/lib/usi-coordinates.mjs` の `rotateSquare180`(筋 n → 10−n、段 a↔i) | `scripts/lib/usi-coordinates.mjs` | **その試験 `usi-coordinates.test.mjs` は node:test の形で、vitest の全件実行では走っていない**(P-27)。使うなら、変換の正しさを vitest の試験で別に確かめる |

## 3. 後手から始まる棋譜をどう渡すか(**決定が要る。6. の Q-1**)

| 案 | やり方 | 良い点 | 要るもの・危うい点 |
|---|---|---|---|
| **案 1: 相手の 1 手目を開始局面に畳む** | 回した手順の 1 手目(相手の手、後手の駒)を、平手・**後手番**の初期局面に適用した局面を `startSfen`(先手番)にし、`moves` は 2 手目から。**本人の手が 1, 3, 5, … 手目(奇数)に来る**。元の棋譜の手数との対応は `plyOffset: 1`(元の ply = 回した ply + 1) | E-3 の奇数/偶数の前提をそのまま使える。死因①の向き(先手 = 本人)も変えない | **`replay.ts` が `startSfen` から始められること**(E-2 のため `scripts` 側で `GameState` を組むか `apps/` を変える)と、**解析の各所に `initialSfen` が渡ること**(E-4。渡らないと、指し手履歴を初期局面から並べ直す解析 ― 形・狙い・棋譜の日本語表記 ― が別の局面を見る)。**`apps/` に触れるかどうかを最初に確かめる** |
| 案 2: 回さず、道具に「本人の側」を持たせる | `diagnose.ts` 等に `userSide` を渡し、評価の符号・王手の向き・玉の色・ready 行の手番を入れ替える | 棋譜を変えない | 変える場所が多い(死因①の規則・JSON v0 の奇数/偶数・`replay.ts` の先後の読み方)。**本番は「自分 = 先手固定」**(CLAUDE.md の現在のスコープ)で、応答の側は先手の前提 |
| 案 3: 本人が先手の局だけを使う | 後手の局は `user_is_gote` として数えるだけで、読まない | 実装が要らない | 局数が半分近くになる(依頼の見込み)。**後手の局に固有の負け方は見えない** |

**推奨(下書き)**: **まず段 0 で、本人が後手の局の件数を数える**(8. の予測の欄)。後手の局が少なければ案 3 で足りる。多ければ案 1。**案 1 に入る前に、E-4 の「`replay.ts`・`recorder.ts` が `initialSfen` を渡しているか」を読んで、`apps/` に触れずに済むかを司令塔に報告する**。

**司令塔の決定(2026-09-15)**:
1. **先に案 3**: ファイルが来たら、本人が先手の局はそのまま既存の道具(`kifu-import-check.ts` → NNUE 版の `replay.ts` → `diagnose.ts`)に通す。実装なし。死因①の規則が実戦で鳴るかの最初の答えを、これで取る
2. **並行して案 1 を作る**。その前に、`replay.ts`・`recorder.ts` が開始局面から始められるかを読んで確かめる(3.1)
3. 固定例 F-S4、F-S6 の別経路の検算、`--me` の完全一致、`rotateSquare180` の TS 化と 81 マスの突き合わせ、Q-5 は下書きのとおり(**Q-5 は、その後の決定 5. で R-8 に変わった**)
4. **(`a011c05` の後)`--me` はヘッダの値から最初の `@` 以降を落とした部分と完全一致で比べる**(1.・F-S7)
5. **(`a011c05` の後)再生に渡す手順の手数が奇数なら、最後の先手の手を落として再生し、`meta` に残す**(R-8・F-S9・Q-5)

### 3.1 確認 2: 開始局面(`startSfen`)から始められるか ― **`apps/` は変えずに済む。変えるのは `scripts/` だけ**(HEAD `4f5964d`。**読んで確かめた。実行はしていない**)

**`apps/server` の側は、開始局面を受ける口が既に通っている**:

| # | 事実 | 場所 |
|---|---|---|
| S-1 | `StateResponseOptions` は `ExplainPositionOptions` を広げたもので、`ExplainPositionOptions` は `DetectIntentsOptions`・`AnalyzeShapeFormationOptions` を広げている。**`initialSfen?: string` は両方にある**(`buildRecognitionTimeline` の options にもある) | `apps/server/src/api/stateResponse.ts:526`、`apps/server/src/analysis/explanationGenerator.ts:528`、`intentDetector.ts:128`、`shapeFormationAnalyzer.ts:75`、`recognitionTimeline.ts:87` |
| S-2 | 応答を組む中で**指し手履歴を初期局面から並べ直す箇所は、どれも `options.initialSfen` を渡している** | `stateResponse.ts:772-773`(形・狙い)・`:795-798`(時系列)・`:1116`(取った駒)・`:1198`(マスを失った判定)・`:1418`(棋譜の日本語) |
| S-3 | `recorder.ts` は `buildImmediateRecord`・`buildReadyRecord` とも、受けた `options` を `buildStateResponseWithPlan` と `safeComputeReachablePlan` の両方にそのまま渡す | `scripts/playtest/lib/recorder.ts:149`・`:236-237` |
| S-4 | `playOpponentMove` は `state.sfen` と `state.moveHistory` しか読まない。`replay.ts` は承認済み variant に `[]` を渡すので、相手 AI の制御の経路は発動しない | `apps/server/src/game/gameSession.ts:202-262`、`scripts/playtest/replay.ts` の `playOpponentMove(state, fakeEngine, [])` |
| S-5 | ほかに `moveHistory` を読む解析(`pathPlanner.ts`・`signatureEvidence.ts`・`pvMaterials.ts`)は、指し手履歴を初期局面から並べ直していない(`git grep moveHistory` で型の import とコメントだけ) | 各ファイル |
| S-6 | `createInitialGameState` は開始局面の引数を持たない(`INITIAL_SFEN` 固定)。**ただし `GameState` は export された型で、`replay.ts` がそれを受け取って `playHumanMove` / `playOpponentMove` を呼んでいるだけ** | `gameSession.ts:26`・`:115-124` |

**したがって `scripts/` 側で足りる。`gameSession.ts` に引数を足す必要は無い**(`replay.ts` で `{ ...createInitialGameState(…), sfen: startSfen }` のように開始局面だけを差し替えた `GameState` を作ればよい)。**`apps/` を変えないので、「本番の挙動は変えない」の固定例は要らない**(もし実装の途中で `apps/` に触る必要が出たら、そこで止めて司令塔に上げ、既定値で同じ挙動になる固定例を入れる)。

**`scripts/` で変える必要がある箇所**(**いまは初期局面を前提に、`initialSfen` を渡さずに呼んでいる**):

| # | 箇所 | いまの形 | 案 1 で要ること |
|---|---|---|---|
| R-1 | `scripts/playtest/replay.ts:193` | `createInitialGameState(…)` の局面(平手・先手番)から始める | 棋譜 JSON に `startSfen` があれば、その局面から始める |
| R-2 | `replay.ts` の `stateResponseOptions`(`{ directionRule, suppressTargetShapeProgress }`) | `initialSfen` を持たない | `initialSfen: startSfen` を足す(S-2・S-3 でそのまま各所へ届く) |
| R-3 | `replay.ts` の `buildMetaLine` の `extra` | 開始局面を記録しない | `startSfen`・`plyOffset`・`mirrored`・`originalUserSide`・`trailingMoveTruncated`(と、落としたときだけ `truncatedTrailingMove`)を記録する(P-43 と同じく、記録から出どころを辿れるように)。**`mirrored: boolean` と `trailingMoveTruncated: boolean` はどの局にも書く。`startSfen`・`plyOffset`・`originalUserSide` は `mirrored` が `true` のときだけ、`truncatedTrailingMove` は `trailingMoveTruncated` が `true` のときだけ書く(false では欄そのものを書かない)**(**null は使わない。司令塔の決定、2026-09-15。12.6・12.7**)(欄が無い = D0-SIDE より前、と区別する。Q-7) |
| R-4 | 固定棋譜の型 `FixedKifu`(`replay.ts:151-153` で `id`・`moves` だけ読む) | 開始局面の欄が無い | 省略可能な `startSfen` を足す(無ければ今と同じ) |
| **R-5** | **`scripts/playtest/lib/failureEvent.ts:303`**(`detectIntents(record.sfen, record.response.moveHistory)`)・**`:415`**(`actualContinuation(moves, branchPly, rule.windowPlies)`) | `initialSfen` を渡さないので、既定の平手から並べ直す | **`meta` の `startSfen` を読んで渡す**。渡さないと、開始局面が違う記録で、狙いの判定と実戦の続きが別の局面を見る(非合法手で例外になるか、黙って違う値になる)。**D1 の lib の変更なので、監査の対象** |
| R-6 | `scripts/playtest/lib/intentStatement.ts:155`(`check.ts` の②の表) | 同上 | 同上 |
| R-7 | `scripts/playtest/invariants/i9-shape-claim-without-evidence.ts:70`(`analyzeShapeFormation(record.sfen, record.response.moveHistory)`) | 同上 | 同上 |
| **R-8** | `replay.ts` の 2 手ずつ読む前(`:228`) | 手数が奇数なら、最後の組を欠いた記録と error 行を残して exit 1(E-1) | **司令塔の決定(2026-09-15)**: **再生に渡す手順(案 1 では畳んだ後)の手数が奇数なら、最後の先手の手を落として再生し、`meta` に `trailingMoveTruncated: true` と `truncatedTrailingMove`(落とした手の USI)を残す**。落とさない局は `trailingMoveTruncated: false` だけを書き、`truncatedTrailingMove` の欄は書かない(**null は使わない。司令塔の決定、12.6**)。**奇数かどうかは畳んだ後の手数で判定し、畳む → 落とす の順に行う**(F-S9a (iii)・V-S22)。落とす先手の手は、案 1 で回した局でも本人の手になる。**負け方の診断に最後の 1 手は要らず、落としたことは記録から辿れる。本人が先手の局にも効くので、案 3 の前に要る**(見本 1 局が 37 手) |
| **R-9** | `diagnose.ts` の入力の読み込み(`readInput`) | `kind: "record"` の行だけを読み、error 行があっても 1 局として数える(A の読み) | **司令塔の決定(2026-09-15)**: **error 行を持つ記録は入力に使わず、「error 行のため使わない」として件数と理由を出す**(Q-6)。**部分の局を黙って 1 局と数えない**ことを R-8 の見張りに含める。**D1 の lib / CLI の変更なので監査の対象**。固定例: error 行を 1 行含む記録 → 局として数えられず、理由が出る。変異 V-S23 |

- **`explore.ts` は変えない**(本人が指す探索であって、外の棋譜を読まない)
- **限界**: 3.1 は読んで確かめただけで、**開始局面の違う棋譜を実際に `replay.ts` に通してはいない**(エンジンを使う段 R)
- **R-5〜R-7 で開始局面を渡し忘れたときの形は、場所ごとに違う**(監査 A の事前読み、必須 1。行番号は A が HEAD `4f5964d` で読んだもの):
  - `detectIntents`(R-5 の `:303`・R-6)と `analyzeShapeFormation`(R-7)は、並べ直した局面を `record.sfen` と文字列で比べ、違えば例外を投げる(`intentDetector.ts:150-157`・`shapeFormationAnalyzer.ts:121-129`)。**ただし例外は外へ出ない**: `triggerOf` と `summarizeIntentStatements` は `{ ok: false }` にして **U-2** に数え(`intentStatement.ts:90`)、**i9 は `catch → continue` で所見が黙って消える**。したがって「数えられなかった」行には現れない
  - `actualContinuation`(R-5 の `:415`)は `record.sfen` と比べない。**畳んだ手順が既定の平手からも合法に並ぶと、別の局面で王手・詰みを数えて黙って違う値を返す**(A の実測: 固定棋譜 7 本の 1 手目を畳んで平手から並べると、6 本は 1〜19 手目で非合法、**`2026-09-12-live-30moves-claude-3` は 29 手すべて合法に並んで別の局面で終わった**)。並ばなければ例外で、`buildDiagnosisReport`(`:511`)が「数えられなかった」にする
- **固定例に足すもの**(変異はどれも「`meta` の `startSfen` を読まない」。V-S15):
  - **R-5 の `:303` と R-6**: 畳んだ記録で **U-2 にならず、決まった列(候補なし・黙った・喋った のどれか)になる**
  - **R-7**: **開始局面を渡すと所見が出る**局面にする(所見が出ない固定例だと、変異が `continue` に飲まれて沈黙する)
  - **R-5 の `:415`**: **claude-3 型(既定の平手からも合法に並ぶ)で、`checks`・`mate` の値そのもの**を見る(例外になる固定例だけだと「数えられなかった」でしか鳴らない)
  - **`replay.ts` で `GameState.sfen` に入れる `startSfen` と、`options.initialSfen` に入れる文字列は同じ文字列にする**。`detectIntents` は手数の欄まで含めて文字列で比べるため、正規化の違い(手数 1 と 2、持ち駒の並び)があると全行が黙って U-2 になる。**`startSfen` は手で書かず、`applyMove` の出力をそのまま使い**、固定例 1 件で文字列の一致を見る(F-S8・V-S16)
  - `failureEventFixtures.ts:57`(`plantedRecords`)は既定の平手から並べるので、畳んだ形の固定例を作るなら開始局面の引数を足す(推奨 3)
- **段 R の確かめ**: 記録を `diagnose.ts`・`check.ts` にかけて、**例外と「数えられなかった」行が 0、U-2 が 0、i9 の `catch` に入った行が 0** であること。i9 に数える口が無ければ足すか、限界と書く(必須 1 (d))
- **限界(R-8。司令塔の決定で、この計画と記録の README の両方に書く)**: **落とした手が本人の詰ませた手だった局は、Event の行では「窓が足りない」に見える。** `actualContinuation` は `windowShort: !ended && reachedPly < lastPly`(A の読み: `failureEvent.ts:221`)で、元の棋譜では終局した局面が、落とした記録では終局していない。**行からは、窓が足りない理由(記録の終わり / 落とした手)を見分けられない**(`meta` の `trailingMoveTruncated`・`truncatedTrailingMove` を辿れば分かる)。**落とす局は、最後の手を指したのが先手の局(本人が先手なら、本人の手で終わる局)に偏る。** その件数を 9. の表に出す

## 4. 変換の定義(純粋関数。案 1・案 3 のどちらでも回す関数は同じ)

- **マス**: `(筋, 段) → (10 − 筋, 10 − 段)`(USI の段 a〜i を 1〜9 として)。例: `7g → 3c`、`2d → 8f`、`5e → 5e`(中央は動かない)
- **通常の手 `<from><to>[+]`**: `from`・`to` を回し、**成りの `+` はそのまま残す**
- **駒打ち `<駒>*<to>`**: **駒の文字はそのまま(`P`・`L` などは色を持たない)、打つマスを回す**
- **盤全体(校正のための別の経路)**: SFEN の盤の文字列を 180 度回し、駒の大文字・小文字を入れ替え、持ち駒の先手・後手を入れ替え、手番を入れ替える。**手を回して並べた局面と、局面を直接回した SFEN が一致することを見る**(5. の F-S6)。**書き方の注意(監査 A の推奨 1)**: (a) 反転は**駒の単位**で行う(文字列を反転すると成り駒の `+b` が `b+` になる。F-S6 の最後の局面は 1 段目に `+b` を持つ)(b) **比べ方は、SFEN の文字列ではなく `parsePosition` で盤・持ち駒・手番を比べる**か、同じ正規化を通す(手で並べた持ち駒の並びが shogiops の正規化と違うと、偽の赤になる)(c) 盤の回転は**マスの変換(`rotateSquare` の TS 版)を使わず**、行と駒の単位の反転で書く(変換器とマスの写し方を共有しないため)
- **やらない**: 駒の種類の変換(将棋の駒は色で区別されるだけで、手の文字列に色が無い)

## 5. 固定例(**既知の正解で校正する**。期待値は試験を回す前に手で書く)

| # | 入力 | 期待 | 手で導いた理由 |
|---|---|---|---|
| F-S1 | `7g7f` | `3c3d` | 7→3、g(7)→c(3)、f(6)→d(4)(依頼の例) |
| F-S2 | `8h2b+` | `2b8h+` | 8h→2b、2b→8h、`+` はそのまま(依頼の例) |
| F-S3 | `P*5e` | `P*5e` | 中央は動かない(依頼の例)。**ただしこれだけでは「打つマスを回さない」誤りを見分けられない** |
| **F-S4** | **`P*2d`** | **`P*8f`** | **2→8、d(4)→f(6)。F-S3 の見分けられない誤りを捕まえるため足した** |
| F-S5 | 81 マスすべてと、F-S1〜S4 の手 | 2 回回すと元に戻る | 変換は自分自身の逆 |
| F-S6 | 既存の固定棋譜 `2026-09-10-claude-10moves` の 20 手を回す | (a) 平手・**後手番**の初期局面から `applyMove` で全手合法 (b) 最後の局面が、元の最後の局面を 4. の「盤全体」で回した SFEN と一致(盤・持ち駒・手番) | **手の変換と局面の変換という別の経路が一致すること**を正解に置く(変換器と検算が同じ誤りを持つのを避ける) |
| F-S7 | ヘッダの名前(**名前はすべて架空**) | `--me` が先手の名前だけに一致 → 回さない / 後手の名前だけ → 回す / どちらにも一致しない・両方に一致 → `user_side_unknown`。**`@` の規則(司令塔の決定)**: ヘッダ `ミサカ@▲4八銀` は `--me ミサカ` に**一致**し、取り込みの記録には**本人の側の**生の文字列 `ミサカ@▲4八銀` だけが残る(相手の側の名前は残らない)。ヘッダ `ミサカ2` は**不一致**。**赤の例(監査 A の推奨 2)**: (i) 前方一致・部分一致(`--me abc` とヘッダ `abc2`)は不一致 (ii) 名前の後ろの空白・CR(CRLF のファイル)は Q-8 で決めた扱いで 1 例 (iii) 先手・後手の行そのものが無いときは、名前が違うときと理由を分ける(Q-8)(iv) 先手の行が 2 本ある (v) 大文字小文字だけ違う → 不一致 (vi) `--me` と `--as` が食い違う → 取り込まない (vii) KIF と CSA で 1 例ずつ。**`@` の赤の例(監査 A の追加。司令塔が採用。KIF・CSA の両方で)**: (a) `@abc` は落とすと空の文字列で、どの `--me` とも一致しない。`--me ""` と空白だけの `--me` は止める (b) `@` の無い `abc` は文字列全体と完全一致 (c) 両方の名前の `@` より前が同じ(`abc@▲…` と `abc@△…`)→ 一致 2 で `user_side_unknown` (d) 片方だけに `@` があり、落とすと同じになる(`abc` と `abc@x`)→ 一致 2 で `user_side_unknown`((c) と経路が違うので別の例)(e) `@` が 2 つ(`a@b@c`)→ 最初の `@` で切って `a` (f) `--me` 自身に `@` がある → **止める** (g) 全角の `＠` は `@` として扱わない (h) `@` の前の空白(`abc @x`)と行末の CR → Q-8 で決めた扱いで 1 例 | 手で書いた KIF・CSA の最小ヘッダで |
| F-S8(案 1 のとき) | F-S6 の回した手順 | `startSfen` = **`lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2`**(平手・後手番の初期局面に、回した 1 手目 `3c3d` を当てた局面。**手数の欄は `2`**)、`moves` = 回した 2 手目以降(19 手)、`plyOffset: 1`。**`GameState.sfen` と `options.initialSfen` がこの文字列と一致する** | 回した 1 手目は、元の 1 手目 `7g7f` を回したもの。期待の SFEN は、監査 A が手で導き、後手番の平手から `replayMoveHistory` で並べた結果と文字列まで一致することを確かめた値(必須 1・推奨 5)。**1e も手で導き、一致を確かめた(11.5)**。**1 手を開始局面に畳むので、元の手数が偶数なら残りは奇数になる**(この例は残り 19 手)。**残りが奇数なら R-8 で最後の先手の手を落とす**(F-S9) |
| **F-S9(R-8)** | 手数が奇数の固定棋譜(手で書く。n 手) | **error 行が無く、ready 行は (n−1)/2 + 1 本**(開始局面の 1 本と組ごと。E-1)、`meta` に `trailingMoveTruncated: true` と `truncatedTrailingMove`(落とした手の USI)。手数が偶数なら `trailingMoveTruncated: false` だけで(`truncatedTrailingMove` の欄は無い)、ready 行は n/2 + 1 本 | 司令塔の決定(2026-09-15)。**依頼の文の「(n−1)/2 本」は、ply 0 の ready 行(`replay.ts:205`)を足すと (n−1)/2 + 1 本になる**(D0-NNUE の 20 手の局で ready 11 本 = 20/2 + 1)。**`replay.ts` を通すとエンジンを使う**ので、推奨: 落とす手順を lib の純粋関数に出してエンジン無しで試験し、`replay.ts` の配線(`meta` の欄と ready 行の本数)は段 R の記録で確かめる |
| F-S9a〜e(R-8。監査 A の追加。司令塔が採用) | (i) 手数が偶数 (ii) 手数が奇数 (iii) **畳む(1 手目)と落とす(最後)を重ねる局**: 元の手数が偶数の後手の局(`claude-10moves` を回すと 20 手 → 畳んで 19 手 → 落として 18 手)(iv) 再生に渡す手順が 0 手になる局 3 通り: (a) 本人が先手・元 1 手 (b) 本人が後手・元 2 手 (c) 本人が後手・元 1 手 (v) 落とした手が本人の詰ませた手の局 | (i) 落とさず `trailingMoveTruncated: false`(`truncatedTrailingMove` の欄は無い)(ii) 最後の 1 手だけを落とし、落とした手の文字列が `meta` と一致 (iii) `plyOffset: 1` と、落とした手(**回した座標**)が両方残る。奇数かどうかは**畳んだ後の手数**で判定する (iv) 3 通りとも再生せず、理由 `no_moves_to_replay`(Q-9)。**段 1 は (a) だけ**((b)(c) は畳む処理が要るので段 2。変異の候補「0 手の判定を落とした後だけで行う」は (c) で鳴る)(v) 元の棋譜では終局だった局面で、`actualContinuation` が `windowShort: true` を返す(**限界を固定例で見る**。3.1) | (iii) を元の手数で判定すると、元 20 手は偶数なので落とさず、畳んだ 19 手が `odd_move_count` で止まる(V-S22) |
| F-S10 | 手で導いた期待値(変換器も検算も通さない正解。監査 A の推奨 1 (d)) | `2026-09-10-claude-10moves` の最後の局面を回したもの = `ln1g2s1+B/1ks1gr3/p1pppp1pp/1p7/9/1GP6/PP1PPPPPP/7R1/LNS1KGSNL w NLPb 21`(成り駒と、両方の持ち駒を含む) | 監査 A が手で回し、後手番の平手から `replayMoveHistory` で並べた結果と文字列まで一致することを確かめた値。**1e も手で導き、一致を確かめた(11.5)** |
| F-S11 | 元の最後の局面と、回した最後の局面 | **一致しない** | 初期局面のように対称な局面だと回転の誤りが見えないので、前提として 1 行置く(推奨 1 (e)) |
| 段 R(エンジンを使う。後で) | 実際の 1 局(本人が後手)を案 1 の形で `replay.ts` に通す | エラー行が無く、ready 行の局面が「元の棋譜の本人の手番の局面を回したもの」と一致する。`meta` に `trailingMoveTruncated` がある(落とした局は `truncatedTrailingMove` も)。`diagnose.ts`・`check.ts` で例外・「数えられなかった」・U-2・i9 の `catch` が 0(3.1) | エンジンを持つセッションが行う。**この計画書の範囲では回さない**。**元の手数の奇数・偶数は選ばなくてよい**(R-8 で最後の手を落とす) |

## 6. 決定が要る点

| # | 判断 | 下書きの推奨 |
|---|---|---|
| **Q-1** | 後手から始まる棋譜の渡し方(3.) | **決定(司令塔、2026-09-15): 先に案 3、並行して案 1。** 案 1 は 3.1 の確認で `apps/` を変えずに済む(`scripts/` の R-1〜R-7) |
| Q-2 | 本人の選び方 | `--me <名前>` を主にし、`--as sente\|gote` で明示もできる。**比べ方は、ヘッダの値から最初の `@` 以降を落とした部分との完全一致(司令塔の決定、2026-09-15)**。一致 0・2 は取り込まない。生の文字列は記録に残す |
| Q-3 | マスの回転を `usi-coordinates.mjs` から使うか、TS の lib に書くか | **TS の lib に書き、`rotateSquare180` と 81 マスで結果が同じことを vitest の試験で突き合わせる**(`.mjs` の試験は vitest で走っていない。P-27) |
| Q-4 | 元の棋譜の手数との対応をどこに残すか | 固定棋譜 JSON の `plyOffset` と、元の手順(回す前)をそのまま残す。レポートでは元の手数に戻して書く |
| Q-5 | 手数が奇数の局の扱い | **決定(司令塔、2026-09-15)**: **R-8 ― 最後の先手の手を落として再生し、`meta` に `trailingMoveTruncated`(常に)と、落としたときだけ `truncatedTrailingMove`(落とした手)を残す(**null は使わない。司令塔の決定、12.6**)**。本人が先手の局にも効くので、案 3 の前に要る(下書きの「変えずに `odd_move_count` の件数として数える」は取り下げ) |
| **Q-6** | `replay.ts` が error 行を書いて exit 1 した記録(R-8 の後も、非合法手などで起きうる)を `diagnose.ts` に掛けるか | **決定(司令塔、2026-09-15)**: **error 行を持つ記録は `diagnose.ts` の入力に使わない**(R-9)。件数と理由は報告に残す。**部分の局を黙って 1 局と数えない**ことを R-8 の見張りに含める(監査 A の必須 2) |
| **Q-7** | Event の 1 行から座標系が分かるようにするか(監査 A の必須 3) | **決定(司令塔、2026-09-15)**: **この STEP では `meta` に書く(R-3。回さない局・落とさない局にも値を書く)。v0.3 は D4 の前(11.4)。** 以下は決定の前に書いた推奨の記録: **いまは `meta` に書き、記録を辿る**(`provenance.record.path`・sha256 から記録の `meta` に届く)。**Evidence として人に見せる前(D4 の出力の前)に、JSON v0.3(MINOR)で `provenance.record.meta` に `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`trailingMoveTruncated`(と `truncatedTrailingMove`) を足す**。いまの v0.2 の `provenance.record.meta` は 6 欄固定で `additionalProperties: false`(A の読み: `failureEventSchema.ts` の `PROVENANCE_META_KEYS`)なので、足さない限り Event の行には写らない。`replay.ts` はどの局にも `mirrored`・`trailingMoveTruncated` を書き、`startSfen`・`plyOffset`・`originalUserSide` は回した局だけ、`truncatedTrailingMove` は落とした局だけに書く(欄が無い = D0-SIDE より前、と区別できる。12.7)。**時期を決めるのは司令塔** |
| **Q-8** | `--me` の細部(監査 A の推奨 2 と、追加の事前読み) | **決定(司令塔、2026-09-15)**: 赤の例 (i)〜(vii)・(a)〜(h) を採る。**`--me` 自身に `@` があれば止める**(推測しない)。**全角の `＠` は `@` として扱わない**。**`--me ""` と空白だけの `--me` は止める**。**生の文字列を記録に残すのは本人の側だけ**(相手の名前は残さない。8.)。**大文字小文字などの表記ゆれは吸収しない**。**推奨(未決。実装の前に司令塔が決める)**: (ii)(h) `@` 以降を落とした後、前後の空白と CR を落としてから比べる(**ファイルの形式の揺れであって、名前の表記ゆれの吸収ではない**)/ (iii) 先手・後手の行が無いときは、`user_side_unknown` と別の理由 `user_side_no_header` にする / (vi) `--me` と `--as` が食い違ったら `user_side_conflict` で取り込まない。**決定(司令塔、2026-09-15、コミット時): 残る推奨(空白と CR を落としてから比べる・`user_side_no_header`・`user_side_conflict`)もそのまま採る** |
| **Q-9** | 再生に渡す手順が 0 手になる局の扱い(監査 A の追加 (iv) と再指摘) | **決定(司令塔、2026-09-15)**: 再生しない。**条件は「畳む・落とすの後に、再生に渡す手順が 0 手」(経路を問わない)、理由の名前は `no_moves_to_replay`**(0 手の記録からは比べる組が作れず、診断の材料にならない。黙って捨てずに件数を出す)。経路は 3 通り: (a) 本人が先手で元が 1 手(落として 0)(b) 本人が後手で元が 2 手(畳んで 1 → 落として 0)(c) 本人が後手で元が 1 手(畳んで 0。奇数でないので落とさない)。**コミット時(`e1ef22b`)の決定は「元が 1 手だけの局」・理由 `no_moves_after_truncation` だったが、(c) は落とした後ではないので、A の再指摘を受けて変えた(12.2)** |

## 7. 変異(**中心を壊す変異を必ず入れる ― 規則 11.8**。予測は実装の後、当てる前に書く)

| # | 壊し方 | 鳴るはずの固定例 |
|---|---|---|
| **V-S1** | **回さない**(手をそのまま返す) | F-S1・F-S2・F-S4・F-S6 |
| **V-S2** | **筋だけ回す** | F-S1・F-S4・F-S6 |
| V-S3 | 段だけ回す | F-S1・F-S4・F-S6 |
| **V-S4** | **打つマスを回さない** | **F-S4**(F-S3 では鳴らない予測) |
| V-S5 | 打つ駒の文字を変える(例: 小文字にする) | F-S3・F-S4 |
| **V-S6** | **成りの `+` を落とす** | F-S2・F-S6(成りを含むので局面が変わる) |
| V-S7 | 本人の側を取り違える(先手の名前に一致したのに回す) | F-S7 |
| V-S8(案 1) | `startSfen` の手番を後手のままにする / `plyOffset` を 0 にする | F-S8 |
| V-S9 | 盤全体の回転(検算の側)で持ち駒の先後を入れ替えない | F-S6(持ち駒のある局面なので鳴る。**検算の側も壊して鳴ることを見る**) |
| V-S10 | `@` 以降を落とさない(生の文字列で比べる) | F-S7(`ミサカ@▲4八銀` が不一致になる) |
| V-S11 | 完全一致を部分一致(`includes`)にする | F-S7 の (i)(`ミサカ2`・`abc2` が一致になる) |
| V-S12 | 空白・CR を落とす処理を、Q-8 の決定と逆にする(外す / 足す) | F-S7 の (ii) |
| **V-S13** | **R-8: 奇数でも最後の手を落とさない** | **F-S9**(`odd_move_count` で止まる) |
| V-S14 | R-8: 落としたことを `meta` に残さない | F-S9 |
| **V-S15** | **R-5〜R-7: `meta` の `startSfen` を読まない**(場所ごとに 1 件ずつ) | 3.1 の固定例(U-2 になる / 所見が消える / `checks`・`mate` が変わる) |
| V-S16 | `GameState.sfen` と `options.initialSfen` に、正規化の違う文字列を渡す(手数の欄を `1` にする) | F-S8(文字列の一致) |
| V-S17 | 最後の `@` で切る | F-S7 の (e) |
| V-S18 | 片側の名前だけ `@` を落とす | F-S7 の (d) |
| V-S19 | 完全一致を前方一致(`startsWith`)にする | F-S7 の (i)・`ミサカ2` |
| V-S20 | R-8: 偶数でも落とす | F-S9a の (i) |
| V-S21 | R-8: 最後でなく最初の手を落とす | F-S9a の (ii) |
| **V-S22** | **R-8: 奇数かどうかを、畳んだ後でなく元の手数で判定する** | **F-S9a の (iii)**(元 20 手は偶数なので落とさず、畳んだ 19 手が `odd_move_count` で止まる) |
| **V-S23** | **R-9: error 行を持つ記録を `diagnose.ts` の入力に使う** | R-9 の固定例 |

## 8. やらないこと

- 駒落ち・途中局面から始まる棋譜(`unsupported_start` のまま)
- 後手視点の文言の変更(①〜④・帯・レポートの言い回し)。本番の「自分 = 先手固定」は変えない
- 名前の推測(表記ゆれの吸収など)。相手の名前を記録・報告すること
- 取った棋譜をリポジトリにコミットすること

## 9. 予測(**測る前に書く**)

**いま書ける予測**:

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-S1 | **回した棋譜をいまの `replay.ts` にそのまま渡すと、本人が後手の局はすべて 1 手目で `human_move_error` になる**(0.) | 1 局でも 1 手目を通る |
| 予-S2 | F-S5 の往復は 81 マスすべてで元に戻る | 1 マスでも戻らない |
| 予-S3 | F-S6 の 2 つの経路は、盤・持ち駒・手番の 3 つとも一致する | どれかが一致しない |

**`~/Desktop/kifu-samples/` の中身が来てから埋める欄**(**件数は見る前に、数える前に書く**。見込みは下の行に先に書き、実数は別の列に書く):

| 項目 | 見込み(見る前) | 実数 |
|---|---|---|
| ファイル数・形式(KIF / CSA / その他) | ― | (空) |
| 読めた / 読めなかった(理由ごと) | 読めなかったが 1 件以上(D0-KIFU の予-K3 と同じ読み) | (空) |
| 本人が先手 / 後手 / 名前で決まらない | 後手が 30〜70%(対局サービスは先後を振り分けるため)。名前で決まらないが 1 件以上 | (空) |
| 手数の分布(最小・中央値・最大) | ― | (空) |
| 元の手数が奇数 / 偶数(監査 A の必須 2 (a)) | ― | (空) |
| 再生に渡す手順(案 1 では畳んだ後)の手数が奇数 = R-8 で最後の手を落とす局 | ― | (空) |
| うち、落とした手で局が終わっていた局(行では「窓が足りない」に見える。3.1 の限界) | ― | (空) |
| 名前の欄に `@` が付く件数(先手の欄 / 後手の欄。11.1) | ― | (空) |
| `replay.ts` が error 行を書いて exit 1 した記録(件数と理由。Q-6) | 0(R-8 の後、非合法手が出なければ) | (空) |

## 10. `kifu-samples` にファイルが置かれたときの手順(司令塔の依頼)

1. `~/Desktop/kifu-samples/` を **scratchpad にコピー**してから作業する(元のフォルダは読むだけ。リポジトリにはコミットしない)
2. 9. の「見込み」の列を、ファイルを開く前に書いたことを確かめる
3. `npx tsx scripts/playtest/kifu-import-check.ts <コピー先>` で全件読む。読めた / 読めなかった(理由ごと)、形式、手数の分布、文字コードを数える
4. 先後の内訳は、**本人の名前を人間から聞いてから**ヘッダの名前と突き合わせる。聞くまでは「ヘッダに先手・後手の名前がある件数」だけを出す
5. **報告に相手のユーザー名を書かない**(ファイル名に含まれていれば、報告では番号に置き換える)

## 11. 追加の決定と、監査 A の事前読みの取り込み(2026-09-15、`a011c05` の後)

**司令塔の確認(コミット時)**: `truncatedTrailingMove` は 1 欄(落とした手の USI、落とさない局は `null`)でよい。Q-8・Q-9 は推奨どおりに決めた。**(その後、`truncatedTrailingMove` の `null` はやめた。12.6)**

### 11.1 見本 1 局(人間の実棋譜。**scratchpad の外へ出さない・コミットしない・相手の名前を書かない**)

| # | 事実 | 誰が確かめたか |
|---|---|---|
| E-6 | KIF 2.0・UTF-8・手合割 平手・棋戦「ランクマッチ」・37 手・投了・先手の勝ち。`kifu-import-check.ts` で読めて、往復は局面一致・表記の食い違い 0 | 司令塔 |
| E-7 | **名前の欄に `@` が付いているのは、この 1 局では先手の欄だけ**(`@` は 1 つ、`@` の後ろは `▲4八銀`)。後手の欄に `@` は無い。37 手目は先手の手で、38 行目が `投了`、まとめの行は「まで37手で先手の勝ち」 | 1e(名前を出力せず、`@` の有無と数・`@` の後ろの文字・指し手の行とまとめの行だけを出した) |

- **`@` の後ろ(`▲4八銀`)が何を表すかは確かめていない**(書き出し形式の説明を読んでいない)。規則は「最初の `@` 以降を落とす」だけにして、その意味には依らない
- **1 局だけなので、`@` がどういうときに付くか(先手の欄だけか、局によるか)は分からない。** kifu-samples が来たら数える(9. の表)

### 11.2 監査 A の事前読み(下書き `0af796d6` に対する必須 3・推奨 5)の取り込み先

| 指摘 | 取り込み先 |
|---|---|
| 必須 1: R-5〜R-7 の「黙って違う値」は場所ごとに形が違う(U-2・i9 の `catch`・claude-3 型)。`startSfen` と `initialSfen` は同じ文字列にする | 3.1 の箇条(固定例・文字列の一致・段 R の確かめ)、F-S8、V-S15・V-S16 |
| 必須 2: 奇数の手数は途中までの記録が残り、`diagnose.ts` が黙って数える | E-1 の書き直し、R-8(司令塔の決定と同じ向き)、9. の表、Q-6 |
| 必須 3: v0.2 の `provenance` にはこの欄を載せられない | Q-7(時期は司令塔) |
| 推奨 1: F-S6 の検算が比べ方を共有しないか、手で導いた期待値 | 4. の盤全体の注意 (a)(b)(c)、F-S10・F-S11 |
| 推奨 2: `--me` の赤の例 | F-S7 の (i)〜(vii)、Q-8、V-S10〜V-S12 |
| 推奨 3: ほかに初期局面を前提にした読み方 | 3.1 の箇条(`failureEventFixtures.ts:57`)。`kingSurroundingsOf`・`pathForProvenance`・`scanCompare` の G-2・`apps` の SFEN の手数の欄を読む箇所は、**A の読みで影響なし**(1e は読み直していない) |
| 推奨 4: E-1 の書き直し | E-1 |
| 推奨 5: F-S8 に手数の欄 `2` を明記 | F-S8 |

### 11.3 監査 A の追加の事前読み(`@` の突き合わせ・R-8)と、司令塔の決定の取り込み先

| 指摘 | 司令塔の決定(2026-09-15) | 取り込み先 |
|---|---|---|
| `@` の赤の例 (a)〜(h) と変異 4 つ | 採る。(f) は止める、(g) は `@` として扱わない | F-S7、V-S10・V-S11・V-S17〜V-S19、Q-8 |
| 生の文字列を記録に残すと、相手の名前も残して 8. とぶつかる | **残すのは本人の側だけ** | 1.、F-S7、Q-8 |
| R-8 は `meta` を辿れば分かるが、Event の 1 行だけでは分からない | この STEP は `meta` に書く。v0.3 は D4 の前 | R-3、Q-7、11.4 |
| 落とした手が詰ませた手なら、行では「窓が足りない」に見える | **計画の限界と、記録の README に書く** | 3.1 の限界、9. の表、F-S9a (v) |
| R-8 の固定例 (i)〜(v) と変異 4 つ | 採る | F-S9a〜e、V-S13・V-S14・V-S20〜V-S22、Q-9 |
| (前回の必須 2)error 行が出た記録を黙って 1 局と数えない | **`diagnose.ts` の入力に使わない** | R-9、Q-6、V-S23 |

### 11.4 後で(この STEP ではやらない)

- **JSON v0.3(MINOR): `provenance.record.meta` に `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`trailingMoveTruncated`(と、落としたときだけ `truncatedTrailingMove`)を足す(`mirrored`・`trailingMoveTruncated` はどの局にも、`originalUserSide`・`plyOffset`・`startSfen` は `mirrored` が `true` のときだけ、`truncatedTrailingMove` は落としたときだけ写す。null は使わない)。人に見せる出力(D4)の前に行う。** 司令塔が PHASES.md に候補として持つ
- **`scan-compare` にも R-9 と同じ扱いを入れる**(error 行のある記録を突き合わせに使わない。いまは黙って比べる ― 12.4)

### 11.5 監査 A の期待値 2 つを、1e も手で導いた(推奨 1 (d)。写すだけにしない)

- **F-S8**: 平手・後手番の初期局面に `3c3d` を当てる。3 段目 `ppppppppp` の 3 筋(左から 7 つ目)が空いて `pppppp1pp`、4 段目 `9` の 3 筋に後手の歩が入って `6p2`。手番は先手、手数の欄は 2 → `lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2`。**A の値と一致した**
- **F-S10**: 元の最後の局面は、コミット済みの `scripts/playtest/records/d0-nnue/2026-09-10-claude-10moves.jsonl` の ply 20 の ready 行の `sfen` = `lnsgk1snl/1r7/pppppp1pp/6pg1/9/7P1/PP1PPPP1P/3RG1SK1/+b1S2G1NL b Bnlp 21`(`applyMove` で並べた局面で、回転の道具は通っていない)。**段の順を逆にし、各段を駒の単位で左右反転し、大文字・小文字を入れ替え、持ち駒の先後を入れ替え、手番を入れ替える**:
  - 1 段目 = 元の 9 段目 `+b1S2G1NL` → 駒の単位で `[+b,_,S,_,_,G,_,N,L]` → 反転 `[L,N,_,G,_,_,S,_,+b]` → 入れ替え `ln1g2s1+B`
  - 2 段目 = 元の 8 段目 `3RG1SK1` → `1ks1gr3`
  - 3 段目 = 元の 7 段目 `PP1PPPP1P` → `p1pppp1pp`
  - 4 段目 = 元の 6 段目 `7P1` → `1p7`
  - 5 段目 = `9`
  - 6 段目 = 元の 4 段目 `6pg1` → `1GP6`
  - 7 段目 = 元の 3 段目 `pppppp1pp` → `PP1PPPPPP`
  - 8 段目 = 元の 2 段目 `1r7` → `7R1`
  - 9 段目 = 元の 1 段目 `lnsgk1snl` → `LNS1KGSNL`
  - 持ち駒: 先手の `B` → 後手の `b`、後手の `n`・`l`・`p` → 先手の `N`・`L`・`P` → `NLPb`(並びは A の値と同じ、先手の駒が先)。手番 `b` → `w`。手数の欄 21 はそのまま
  - → `ln1g2s1+B/1ks1gr3/p1pppp1pp/1p7/9/1GP6/PP1PPPPPP/7R1/LNS1KGSNL w NLPb 21`。**A の値と一致した**
- **限界**: どちらも手の作業で、道具では確かめていない。**道具で確かめるのは実装の試験**(F-S6 の 2 つの経路と、この手で導いた値の 3 つが一致することを見る)

## 12. 実装の記録(`e1ef22b` の後)

### 12.1 段 1 / 段 2 の分け方(司令塔の決定、2026-09-15)

- **理由**: 実棋譜 10 局の読み込み検査で、**本人が先手の 6 局はすべて手数が奇数**だった(本人の手で終わる局)。**案 3(先手の局をいまの道具にそのまま流す)も、R-8 が無いと `replay.ts` の `odd_move_count` で止まる**。R-8 を先に通して、C が先手の 6 局を評価できるようにし、その間に回転の部分を作る
- **段 1(先)**: R-8、R-9、Q-9 の (a)、R-3 のうち `trailingMoveTruncated`・`truncatedTrailingMove` の欄だけ。固定例 F-S9・F-S9a の (i)(ii)(iv-a)(v)。変異 V-S13・V-S14・V-S20・V-S21・V-S23
- **段 2(後)**: 回転・畳み・`--me`・R-1〜R-7・F-S1〜S8・S10・S11・Q-9 の (b)(c)・残りの変異

### 12.2 `e1ef22b` の後に変えた計画書の文言

- **Q-9**: 条件を「元が 1 手だけの局」から「**畳む・落とすの後に、再生に渡す手順が 0 手**」に、理由の名前を `no_moves_after_truncation` から **`no_moves_to_replay`** に変えた(監査 A の再指摘: 本人が後手で元が 1 手の局は、畳んで 0 手になり、落とした後ではない。司令塔の決定)。6. の Q-9 と、5. の F-S9a の (iv) を直した

### 12.3 段 1 で作ったもの

| 対象 | 変更 |
|---|---|
| `scripts/playtest/lib/replayPlan.ts`(新規) | `planReplayMoves(moves)`: 手数が奇数なら最後の 1 手を落とし(`trailingMoveTruncated: true` と、`truncatedTrailingMove` にその USI)、偶数なら何も落とさない(`trailingMoveTruncated: false`)。meta に書く欄は `truncationMetaFields` が返す(落とさないときは `truncatedTrailingMove` の欄を持たない)。落とした後に 0 手なら `noMovesToReplay`(理由 `no_moves_to_replay`)。**手数 0 の棋譜も同じ印になる**(Q-9 の 3 通りのほかの経路。`kifuImport` は指し手の無い棋譜を `no_move_lines` にするので、取り込みからは作られない) |
| `scripts/playtest/replay.ts` | 棋譜の手順を `planReplayMoves` に通してから 2 手ずつ読む。`meta` の `extra` に `truncationMetaFields` の欄を書く。**再生する手が無い局は、エンジンを起こす前に理由の error 行を書いて exit 1**。記録を書く処理を `writeRecordLines` に出して 2 つの経路で共有した(書き方は変えていない)。`odd_move_count` の分岐は残した(もう通らないはずの守り) |
| `scripts/playtest/invariants/types.ts` | `MetaLine.trailingMoveTruncated?: boolean`・`truncatedTrailingMove?: string` と、3 値の欄の表に列(`trailingMoveTruncated`。`dirty` と同じ形)を足した |
| `scripts/playtest/lib/failureEvent.ts` | `DiagnosisInput.errorLines`(**必須**)。1 つでもあれば診断の関数を呼ばず、結果 `excluded`(理由の一覧)にする。入力の一覧に「error 行のため使わなかった入力」、表の欄に「error 行のため使わない」(例外で数えられなかった入力と分ける) |
| `scripts/playtest/lib/diagnosisTotals.ts` | 合計の見出しに「error 行のため使わなかった N 本」を足し、合計に入れない入力として名前で並べる |
| `scripts/playtest/diagnose.ts` | 記録の `kind: "error"` の行を集めて `errorLines` として渡す |
| 試験 | `lib/replayPlan.test.ts`(新規)・`replay.test.ts`(新規。ソース照合)・`lib/failureEvent.test.ts`(R-9)・`lib/diagnosisTotals.test.ts`(F-Q5)・`diagnose.test.ts`(ソース照合と、error 行を持つ 3 本目の入力を子プロセスに足した) |

- **3 値の欄の規約とのずれ(直した)**: 最初は「落とさない局は `null`」で実装したが、`invariants/types.ts` の表の `null`(測れなかった)とぶつかり、v0.3 で `provenance` に写すと `null` が「欄が無い」の意味にもなるので、司令塔の決定で `trailingMoveTruncated: boolean` を常に書き、落とした手は `true` のときだけ書く形に直した(12.6)
- **F-S9a の (v)(限界の固定例)**: 手で作った 1 手詰の局面(`4k3p/9/4P4/9/9/9/9/9/K8 b G 1` から `9i9h`・`1a1b`・`G*5b`)で、元の手順では `windowShort: false`、落とした手順では `windowShort: true` になることを見る。**実棋譜は試験に使っていない**

### 12.4 段 1 の限界

- **`replay.ts` の配線はソース照合だけ**(エンジンを起こすので試験の中で走らせない)。書き出した記録の ready 行の本数((n−1)/2 + 1)と `meta` の値は、エンジンを使う再生(C の先手 6 局)の記録で確かめる
- R-9 は、コミット済みの記録(error 行 0 本。A の数え)の結果を変えない、と読める。**本監査の全件で確かめる**(A の予測)
- **R-9 は `scan-compare` に効かない**(監査 A の指摘、司令塔の決定で範囲外): `scan-compare.ts:41` は `kind: "record"` の行だけを読み、`scanCompare.ts:52` が `diagnoseRecords` を直接呼ぶ。**D-COST の突き合わせでは、error 行のある記録(途中で止まった局)を黙って比べる**

- **監査 A の任意の指摘 2 件(GO のまま。司令塔の決定: 直さず限界として書く、2026-09-15)**: (1) `diagnose.ts` が集める error 行の種類は、ソース照合でしか見張られていない(子プロセスの固定例は `odd_move_count` だけ)。(2) `truncationMetaFields` が `moves` などを `meta` に漏らす誤りは、lib の試験でしか捕まらない(子プロセスは沈黙)。どちらも振る舞いは変わらない。段 2 で子プロセスの固定例を足すときに合わせて見る

### 12.5 段 1 の実測(worktree `wt-d0-side`、基点 `e1ef22b`)

- **予測**: 変異を当てる前に、同じ逐次コマンドの中で `scratchpad/d0-side/stage1-predictions.md`(sha1 `2b1a211f`)に書いた。**変異 10 件の予測は、鳴る試験の名前と件数まで 10/10 的中**
- **足した試験(12 件。`git diff e1ef22b` と新規ファイルの `it(` の行で数えた)**:
  - scripts/playtest/lib/replayPlan.test.ts(新規): 7
  - scripts/playtest/replay.test.ts(新規): 3
  - scripts/playtest/lib/failureEvent.test.ts: 1
  - scripts/playtest/lib/diagnosisTotals.test.ts: 1
  - scripts/playtest/diagnose.test.ts: 0
  - `diagnose.test.ts` は既存の試験の中に、ソース照合の 2 行と、error 行を持つ 3 本目の入力を足した(試験の件数は変わらない)
- **変えた 5 本の試験だけ**: 5 ファイル・55 件すべて通過
- **型検査**(`node scripts/typecheck-scripts.mjs`、2 つの tsconfig): rc=0・出力 0 行
- **変異(`scratchpad/d0-side/stage1-mutate.py`。試験は変えた 5 本、tsc は `scripts/playtest/tsconfig.json`。試験の失敗と tsc の失敗を分けて数える)**: **適用 10 / 鳴った 10(うち試験 10・tsc だけ 0)/ 沈黙 0 / 適用できなかった 0**。変異の前後で 11 ファイルの sha256 が一致した

| # | 壊し方 | 鳴った試験(失敗件数 / 55) | tsc |
|---|---|---|---|
| V-S13 | 手数が奇数でも落とさない | F-S9・(ii)・(iv-a)・(v)(3) | 0 |
| V-S14 | 落とした手を `meta` に書かない | replay.test の `meta`(1) | 0 |
| V-S20 | 偶数でも落とす | (i)(1) | 0 |
| V-S21 | 最初の手を落とす | (ii)・(v)(2)。(iv-a) は 1 手なので同じ結果(予測どおり) | 0 |
| V-S23a | lib が error 行を見ない | failureEvent の R-9・diagnose の子プロセス(2) | 0 |
| V-S23b | `diagnose.ts` が error 行を集めない | diagnose のソース照合・子プロセス(2) | 0 |
| W-1 | `replay.ts` が落とす前の手順を読む | replay.test の手順(1) | 0 |
| W-2 | 再生する手が無い局の分岐を消す | replay.test の分岐(1) | **1**(`replayPlan.reason` の型が絞れない) |
| T-1 | 合計で error 行の入力を「数えられなかった」に畳む | F-Q5(1) | 0 |
| T-2 | 表の欄を「数えられなかった」に畳む | failureEvent の R-9(1)。diagnose の子プロセスは両側が同じ lib なので沈黙(予測どおり) | 0 |

- **vitest の全件(変異の後に 1 回、`--testTimeout=60000`)**: **Test Files 3 failed | 92 passed | 1 skipped (96)、Tests 1270 passed | 1 skipped (1271)**。落ちた 3 ファイルは既存の node:test 形式(`scripts/lib/usi-coordinates.test.mjs`・`prototypes/shape-matcher` の 2 本。P-27)で、予測どおり。**段 1 の前の全件の件数は測っていない**(足した件数は上の静的な数え)

### 12.6 直し版(司令塔の決定と監査 A の事前の指摘、2026-09-15)

**何を変えたか**
- **`truncatedTrailingMove` の `null` をやめた**(司令塔の決定): `invariants/types.ts` の 3 値の表では `null` = 測れなかった で、「落とさなかった」を `null` で表すと規約とぶつかる。**v0.3 で `provenance` に写すと、`null` は「欄が無い(D0-SIDE より前の記録)」の意味にもなり、区別できない**
  - **形**: `meta` に **`trailingMoveTruncated: boolean` を常に書く**(落とした = `true`、落とさない = `false`)。**`truncatedTrailingMove: string`(落とした手の USI)は `true` のときだけ書く**(`false` のときは欄そのものを書かない)。`null` はどこにも使わない。古い記録は `trailingMoveTruncated` の欄が無いことで見分ける
  - `lib/replayPlan.ts`: `TrailingTruncation` 型と、meta に書く欄だけを返す `truncationMetaFields` を足した。`replay.ts` は `...truncationMetaFields(replayPlan)` で書く
  - `invariants/types.ts`: 表の列を `trailingMoveTruncated`(`dirty` と同じ形)に直し、`null` の例外の注記を消した
- **Q-9 の分岐を子プロセスで試す**(監査 A の推奨、司令塔の決定): `replay.test.ts` に、`SHOGI_ENGINE_PATH` に存在しないパスを渡して 1 手の棋譜・0 手の棋譜で `replay.ts` を回す試験を 2 件足した。**exit 1・`meta`・error 行の理由・record 行 0 本・リポジトリに書かないこと**を見る。分岐がエンジンの起動より前で止まらなければ、存在しないエンジンの起動で落ちて記録が書かれない(P-30)ので赤になる
- **偶数の局は `Object.hasOwn` で「`truncatedTrailingMove` の欄が無い」ことを見る**(監査 A、司令塔の決定): lib の試験と、0 手の棋譜の子プロセスの試験で見る(`null` や `undefined` を書く誤りを捕まえる。値だけ比べると `JSON` を通した `null` が沈黙しうる)
- **R-9 は `scan-compare` に効かない**(監査 A、司令塔の決定で範囲外)を 12.4 の限界と 11.4 の「後で」に書いた
- **段 2 への申し送り**: R-3 の `startSfen: null`(回さない局)も、同じ理由で形を決め直す必要がある

**実測(worktree `wt-d0-side`、基点 `e1ef22b`)**
- **予測**: 変異を当てる前に、同じ逐次コマンドの中で `scratchpad/d0-side/stage1c-predictions.md`(sha1 `2d985118`)に書いた。**変異 16 件は、鳴る試験の名前と件数まで 16/16 的中**
- **足した試験(16 件。`git diff e1ef22b` と新規ファイルの `it(` の行で数えた)**: lib/replayPlan.test.ts(新規) 9・replay.test.ts(新規) 5・lib/failureEvent.test.ts 1・lib/diagnosisTotals.test.ts 1・diagnose.test.ts 0。**予測の「14 件増える」は外れ**(`truncationMetaFields` の 2 件を数え忘れた。試験の中身ではなく、予測の書き方の誤り)
- **変えた 5 本の試験だけ**: 5 ファイル・59 件すべて通過。**型検査** rc=0・出力 0 行
- **変異(`scratchpad/d0-side/stage1c-mutate.py`)**: **適用 16 / 鳴った 16(うち試験 16・tsc だけ 0)/ 沈黙 0 / 適用できなかった 0**。変異の前後で 11 ファイルの sha256 が一致した

| # | 壊し方 | 鳴った試験(失敗件数 / 59) | tsc |
|---|---|---|---|
| V-S13 | 奇数でも落とさない | (ii)・(iv-a)・(v)・「落としたとき」の meta・子プロセス 1 手(5) | 0 |
| V-S14 | meta に書かない(`...truncationMetaFields` を消す) | ソース照合の meta・子プロセス 1 手・0 手(3) | 0 |
| V-S20 | 偶数でも落とす | (i)・「落とさなかった」の meta(2) | 0 |
| V-S21 | 最初の手を落とす | (ii)・(v)(2) | 0 |
| V-S23a | lib が error 行を見ない | failureEvent の R-9・diagnose の子プロセス(2) | 0 |
| V-S23b | `diagnose.ts` が error 行を集めない | diagnose のソース照合・子プロセス(2) | 0 |
| W-1 | `replay.ts` が落とす前の手順を読む | ソース照合の手順(1)。子プロセスは分岐で先に止まるので変わらない(予測どおり) | 0 |
| W-2 | 0 手の分岐を消す | ソース照合の分岐・子プロセス 1 手・0 手(3) | **1** |
| T-1 | 合計で error 行の入力を「数えられなかった」に畳む | F-Q5(1) | 0 |
| T-2 | 表の欄を「数えられなかった」に畳む | failureEvent の R-9(1) | 0 |
| **N-1** | **偶数でも `truncatedTrailingMove: null` を書く** | 「落とさなかった」の meta・子プロセス 0 手の `Object.hasOwn`(2) | 0 |
| N-2 | 落としたとき `trailingMoveTruncated` を書かない | 「落としたとき」の meta・子プロセス 1 手(2) | 0 |
| N-2b | 落とさなかったとき `trailingMoveTruncated` を書かない | 「落とさなかった」の meta・子プロセス 0 手(2) | 0 |
| N-3 | `true` なのに落とした手を書かない | 「落としたとき」の meta・子プロセス 1 手(2) | 0 |
| **N-4** | **0 手の分岐の exit を 0 にする** | 子プロセス 1 手・0 手(2) | 0 |
| **N-5** | **0 手の分岐で記録を書かない** | 子プロセス 1 手・0 手(2) | 0 |

- **vitest の全件(変異の後に 1 回、`--testTimeout=60000`)**: **Test Files 3 failed | 92 passed | 1 skipped (96)、Tests 1274 passed | 1 skipped (1275)**。落ちた 3 ファイルは既存の node:test 形式(P-27)で、予測どおり

### 12.7 段 2(worktree `wt-d0-side2`、基点 `5a2dc84`。2026-09-15)

**作ったもの**

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/usiRotation.ts`(新規) | `rotateSquare`・`rotateUsiMove`(4.)。読めない手は例外。`usi-coordinates.mjs` の `rotateSquare180` と 81 マスで突き合わせる(Q-3) |
| `scripts/playtest/lib/userSide.ts`(新規) | `decideUserSide`(1.・F-S7・Q-8)。KIF `先手：`/`後手：`(半角 `:` も)、CSA `N+`/`N-`。最初の半角 `@` 以降を落とし、前後の空白・タブ・CR・全角の空白を落として完全一致。`user_side_no_header`・`user_side_unknown`・`user_side_conflict`。`--me` が空・空白だけ・半角 `@` を含むなら止める。**返す名前は本人の側の生の値だけ** |
| `scripts/playtest/lib/sideAlignment.ts`(新規) | `alignMovesToSente`(回して 1 手目を平手・後手番に当てた局面を `startSfen` に畳む。`applyMove` の出力をそのまま使う)・`readSideAlignment`(固定棋譜の欄の形を確かめる。食い違えば例外)・`sideMetaFields`・`initialSfenOf`(meta を 3 つに分けて読む)・`alignedFixedKifu`(Q-4: 回す前の手順を `originalMoves` に残す) |
| `scripts/playtest/replay.ts` | R-1〜R-4。そろえの欄を meta より前に読み、**同じ文字列**を `GameState.sfen` と `options.initialSfen` に渡す。meta に `...sideMetaFields(sideAlignment)` |
| `scripts/playtest/lib/failureEvent.ts` | R-5。`triggerOf`・`diagnoseRecords`・`actualContinuation` の `initialSfen` を**必須**にし(既定値を外した)、`buildDiagnosisReport` が `initialSfenOf(input.meta)` を渡す(形の食い違う meta は「数えられなかった」) |
| `scripts/playtest/lib/intentStatement.ts` | R-6。`summarizeIntentStatements` は `{ records, initialSfen }` のまとまりを受ける(開始局面の違う入力を混ぜた合計も、それぞれの開始局面から数え直す) |
| `scripts/playtest/invariants/i9-shape-claim-without-evidence.ts`・`invariants/types.ts`・`check.ts` | R-7。`Invariant.check(records, context?)` の文脈で開始局面を渡す(**省略は既存の試験のため。check.ts は必ず渡す**)。`check.ts` は meta から読んだ開始局面を②の表と不変条件の両方に渡す |
| `scripts/playtest/lib/scanCompare.ts` | 計画の R-1〜R-7 の外。`diagnoseRecords` の引数を必須にしたため、深い・軽いそれぞれの meta の開始局面を渡す |
| `scripts/playtest/kifu-import-check.ts` | `--me <名前>` / `--as sente\|gote`(ファイル 1 つのときだけ)。決まれば `--fixed` をそろえた形で書き、決まらなければ理由を出して書かない。**標準出力に出す名前は本人の側の値だけ** |
| `scripts/playtest/lib/failureEventFixtures.ts` | `plantedRecords`・`baseRowsOf` に開始局面の引数(推奨 3。既定は平手) |
| `invariants/types.ts` の `MetaLine` | `mirrored?: boolean`・`startSfen?`・`plyOffset?`・`originalUserSide?: "gote"`。3 値の表に `mirrored` の列を足した(`dirty` と同じ形。null の例外は作らない) |

**実装で決めたこと(計画に書いていなかった細部。監査で見てほしい)**
- 先手・後手の行の**どちらかが無い**局は `user_side_no_header`(両方無いときだけではない)。先手か後手の行が 2 本以上なら `user_side_unknown`
- `--me` そのものは前後の空白を落とさない(空・空白だけなら止める)。`--me` で決まらなかった局を `--as` で決め直さない
- 本人の側のヘッダの生の値は **`kifu-import-check.ts` の標準出力にだけ出し、固定棋譜 JSON には書かない**(records/ に置く JSON に名前を入れない、の人間の承認に合わせた)
- 固定棋譜 JSON: 本人が先手 → `id`・`source`・`mirrored: false`・`moves`。後手 → `id`・`source`・`mirrored: true`・`originalUserSide`・`plyOffset`・`startSfen`・`moves`・`originalMoves`。`--me`/`--as` を渡さなければ今までと同じ 3 欄
- そろえの欄の形が食い違う固定棋譜は、`replay.ts` が **meta を書く前に**例外で止まる(記録を書かない、exit 1)
- 手数が奇数かどうか(R-8)は `replay.ts` が畳んだ後の `moves` で決める。**畳むのは固定棋譜を作るとき、落とすのは再生のとき**なので、V-S22 の形(元の手数で判定)は起きない。同じ種類の誤りは W-R3(`originalMoves` で判定する)で見た
- F-S7 の名前は、計画の例の名前を使わず**すべて架空の名前**にした

**固定例(期待値は回す前に手で書いた)**
- F-S1〜S6・S10・S11 は `usiRotation.test.ts`。F-S6 の検算(盤全体の回転)は、マスの変換を使わず行と駒の単位の反転で書き、shogiops の正規化を通した盤・手番・持ち駒の 3 欄で比べる。**検算を壊す変異 V-S9 も当てた**
- F-S7 は `userSide.test.ts`(赤の例 (i)〜(vii)・(a)〜(h) を KIF と CSA の両方で)と `kifu-import-check.test.ts`(子プロセス)
- F-S8・F-S9a (iii)(iv-b)(iv-c)・Q-4 は `sideAlignment.test.ts`。Q-9 の (b)(c) は `replay.test.ts` の子プロセスでも見る(meta の欄と error 行)
- **R-5 :415 の固定例は手で組んだ**: 3.1 の claude-3 を回して畳むと、平手からも 29 手合法に並ぶが、**どの分岐点でも王手・詰みが 0 で、渡し忘れても値が変わらない**(探りで確かめた。ほかの固定棋譜 6 本と game-01 も同じく値の変わる分岐点が 0)。そこで、平手・後手番に `3c3d` を当てた開始局面(F-S8 と同じ)から `7g7f 4c4d 5i6h 9c9d 6h7g 4d4e` を指す 6 手を作った。**平手からも合法に並び、開始局面の側だけ最後の `4d4e` で角筋 2b-3c-4d-5e-6f が通って 7g の先手玉が王手を受ける**(開始局面から `checks: [6]`、平手から黙って `[]`、畳まずに後手番の平手から並べると 1 手ずれて `[7]`)。R-5 :303・R-6・R-7(I-9 は `6i5h` の局面)・check.ts・scan-compare の固定例も同じ開始局面で作った
- 監査 A の段 1 の任意 2 件: (1) `diagnose.test.ts` の error 行の理由を `human_move_error` にした (2) `replay.test.ts` の子プロセスで、meta に `moves`・`reason`・`originalMoves` の欄が無いことを見る

**実測(worktree `wt-d0-side2`)**
- 足した試験 96 件: `lib/usiRotation.test.ts`(新規)16・`lib/userSide.test.ts`(新規)40・`lib/sideAlignment.test.ts`(新規)19・`kifu-import-check.test.ts`(新規)6・`replay.test.ts` +4・`lib/failureEvent.test.ts` +5・`lib/intentStatement.test.ts` +2・`i9-shape-claim-without-evidence.test.ts` +2・`lib/scanCompare.test.ts` +1・`check.test.ts` +1・`diagnose.test.ts` 0(理由の値だけ変えた)
- 既存の試験の呼び出しは、必須にした `initialSfen` に平手を渡す形に直した(`failureEvent.test.ts`・`failureEventSchema.test.ts`・`intentStatement.test.ts`・`check.test.ts`。見る値は変えていない)
- **型検査**(`node scripts/typecheck-scripts.mjs`、2 つの tsconfig): rc=0
- **scripts/playtest の vitest 全件**: **42 ファイル / 523 件すべて通過**。予測(`scratchpad/d0-side/stage2-full-prediction.md`、回す前に書いた)の 42 / 523 と一致
- 途中の赤 1 回: `userSide.ts` の名前の行の正規表現 `(.*)$` は、`.` が CR に一致しないので、行末に CR が残った行を名前の行として読み落とした(手で書いた (ii) の固定例で見つかった)。`([\s\S]*)$` に直した
- **変異**(`scratchpad/d0-side/stage2-mutate.py`。予測は道具の中に書き、当てる前に `stage2-mut-out/predictions.md`(sha1 `ce480f08`)へ書き出した。試験は変えた 13 本、tsc は `scripts/playtest/tsconfig.json`。変異の前に 13 本が通ることを確かめた): **適用 33 / 鳴った 33 / 沈黙 0 / 適用できなかった 0**。予測: 集合 33/33・tsc 33/33・中心 10/10 鳴った。沈黙: [] | 集合が外れた: [] | tsc が外れた: []。変異の前後で 24 ファイルの sha256 が一致した

| # | 中心 | 壊し方 | 鳴った試験(予測の見出し) | 失敗件数 | tsc | 予測 |
|---|---|---|---|---|---|---|
| V-S1 | **中心** | 回さない(手をそのまま返す) | U1, U2, U4, U12, U13, U14, U15, A2, A3, A4, A6, A7, A8, A13, A19, K1, K4 | 17 | 0 | 的中 |
| V-S2 | **中心** | 筋だけ回す | U1, U2, U4, U5, U7, U9, U12, U13, U14, U15, A2, A3, A4, A6, A7, A8, A13, A19, K1, K4 | 20 | 0 | 的中 |
| V-S4 |  | 打つマスを回さない | U4, U12, U13, U14, U15, A3 | 6 | 0 | 的中 |
| V-S5 |  | 打つ駒の文字を小文字にする | U3, U4, U8, U12, U13, U14, U15, A3 | 8 | 0 | 的中 |
| V-S6 |  | 成りの + を落とす | U2, U8, U12, U13, U14, U15, A3 | 7 | 0 | 的中 |
| V-S8a |  | startSfen の手番を後手のままにする | A2, A3, A7, A8, A13, A19, K1, K4 | 8 | 0 | 的中 |
| V-S8b |  | plyOffset を 0 にする | A2, A6, A7, A8, A13, A19, K1 | 7 | 0 | 的中 |
| V-S9 |  | 検算の側で持ち駒の先後を入れ替えない | U13 | 1 | 0 | 的中 |
| V-S7 | **中心** | 本人の側を取り違える | S1, S2, S4, S7, S11, S13, S16, S17, S22, S23, K1, K2, K3 | 21 | 0 | 的中 |
| V-S10 | **中心** | @ 以降を落とさない | S4, S7, S15, S16, S21, S22, K1, K3 | 12 | 0 | 的中 |
| V-S11 |  | 完全一致を部分一致(includes)にする | S5, S17 | 4 | 0 | 的中 |
| V-S19 |  | 完全一致を前方一致(startsWith)にする | S5, S6, S17 | 6 | 0 | 的中 |
| V-S12 |  | 空白・CR を落とさない | S7, S21 | 3 | 0 | 的中 |
| V-S17 |  | 最後の @ で切る | S16, S21 | 3 | 0 | 的中 |
| V-S18 |  | 後手の名前だけ @ を落とさない | S7, S14, S15, S22, K1, K3 | 9 | 0 | 的中 |
| V-S15a | **中心** | R-5 :415 diagnoseRecords が開始局面を actualContinuation に渡さない | F4, C1 | 2 | 0 | 的中 |
| V-S15b |  | R-5 :303 triggerOf が開始局面を detectIntents に渡さない | F3, F4 | 2 | 0 | 的中 |
| V-S15c | **中心** | R-5 buildDiagnosisReport が meta の startSfen を読まない | F4, F5 | 2 | 0 | 的中 |
| V-S15d | **中心** | R-6 summarizeIntentStatements が開始局面を渡さない | I1, I2, H1 | 3 | 0 | 的中 |
| V-S15e | **中心** | R-7 I-9 が文脈の開始局面を使わない | N1, H1 | 2 | 0 | 的中 |
| W-C1 |  | check.ts が不変条件に文脈を渡さない | H1 | 1 | 0 | 的中 |
| W-C2 |  | check.ts が meta の開始局面を読まない | H1 | 1 | 0 | 的中 |
| W-S1 |  | scanCompare が軽い走査の meta を読まない | C1 | 1 | 0 | 的中 |
| V-S16 |  | GameState.sfen に正規化の違う文字列を渡す(手数の欄を 1) | R4 | 1 | 0 | 的中 |
| W-R1 | **中心** | replay.ts が meta にそろえの欄を書かない | R4, R5, R6, R7, R8 | 5 | 0 | 的中 |
| W-R2 | **中心** | replay.ts が固定棋譜のそろえの欄を読まない | R4, R7, R8, R9 | 4 | 0 | 的中 |
| W-R3 |  | replay.ts が畳む前の手順(originalMoves)で落とすかを決める(V-S22 の段 2 版) | R1, R7, R8 | 3 | 0 | 的中 |
| A-2 |  | truncationMetaFields が受けた値をそのまま返す(監査 A の任意 2) | P1, P2, R5, R6, R7, R8 | 6 | 0 | 的中 |
| A-9 |  | diagnose.ts が理由 odd_move_count の error 行だけを集める(監査 A の任意 1) | D0, D1 | 2 | 0 | 的中 |
| W-K1 |  | kifu-import-check.ts が決まらない局も書く | K3 | 1 | **1** | 的中 |
| W-K2 |  | kifu-import-check.ts が --me を先に確かめない | K6 | 1 | 0 | 的中 |
| W-A1 |  | readSideAlignment が mirrored でない棋譜の余計な欄を見逃す | A11 | 1 | 0 | 的中 |
| W-A2 |  | initialSfenOf が 3 つに分けず ?? で読む | A16, F5 | 2 | 0 | 的中 |

**載せ直し(基点 `b87b2f2`。司令塔の指示、2026-09-15)**: 上の実測は基点 `5a2dc84` の worktree `wt-d0-side2` で取った。その後に D0-KIFU2(`b87b2f2`)が `kifu-import-check.ts` を変えた(1 文字の成り駒を揃え、表に「揃えた手」の列を足す)ので、**worktree `wt-d0-side3` を `b87b2f2` で作り直し**、段 2 の 25 本のうち `b87b2f2` までに変わっていない 24 本はそのまま写し、`kifu-import-check.ts` だけは `git merge-file`(自分の版・`5a2dc84` の版・`b87b2f2` の版)で 3 方向に合わせた(衝突 0。揃えた手の列・詳細行と、`--me` / `--as` の両方が入っていることを確かめた)。載せ直した版で: 型検査 rc=0・check-docs rc=0・**scripts/playtest の vitest 全件 42 ファイル / 532 件すべて通過**(回す前の見込み `stage2r-full-prediction.md`: `b87b2f2` の 436 件 + 段 2 の 96 件 = 532)。変異は、中心・`kifu-import-check.ts` に関わるもの・R-5〜R-7 の各 1 件の 15 件(V-S1・V-S2・V-S8a・V-S8b・V-S7・V-S10・V-S18・V-S15a・V-S15c・V-S15d・V-S15e・W-R1・W-R2・W-K1・W-K2)を当て直した(道具 `scratchpad/d0-side/stage2r-mutate.py`、予測は `5a2dc84` のときと同じで、当てる前に `stage2r-mut-out/predictions.md`(sha1 `cb960b69`)へ書き出した): **適用 15 / 鳴った 15 / 沈黙 0 / 適用できなかった 0**。予測: 集合 15/15・tsc 15/15・中心 10/10 鳴った。変異の前後で 25 ファイルの sha256 が一致した

**監査 A の事前の読みを受けた追加(司令塔の決定、2026-09-15。載せ直し版に入れた)**:
- **■1 回した固定棋譜の欄の照合**: `readSideAlignment` は、`mirrored: true` の固定棋譜に `originalMoves` があれば、`alignMovesToSente(originalMoves, "gote")` で `startSfen`・`moves`・`plyOffset` を作り直し、書かれている値と一致することを確かめる。食い違えば、食い違った欄の名前を理由にして `InvalidSideAlignmentError`(`replay.ts` は meta を書く前に止まり、記録を書かない)。`originalMoves` は**必須にしない**。代わりに **meta に `sideAlignmentChecked: boolean` を常に書く**(照合して一致した局だけ `true`。回していない局と、`originalMoves` の無い回した局は `false`)。**照合せずに通した回した局が、記録から見える**。`mirrored` でない固定棋譜に `originalMoves` があれば形の食い違いとして止める。`invariants/types.ts` の 3 値の表に列を足した(`false` は「照合していない」)
- **■2 固定例の土台の cache**: 同じ手順を平手と開始局面で続けて `plantedRecords` し、ready 行の局面がそれぞれの開始局面から始まることを見る試験を 1 件足した(cache のキーから開始局面を外す誤りを捕まえる)
- 固定例: 照合して一致 → `true` / `originalMoves` 無し → `false` / `moves` を 1 手変える → 止まる / `startSfen` を変える → 止まる / `originalMoves` が配列でない・空・読めない手・非合法な 1 手目 → 止まる / `mirrored` でない局に `originalMoves` → 止まる(lib)。`replay.ts` の子プロセスで、`originalMoves` の無い回した局の meta(`sideAlignmentChecked: false`)と、`moves` を変えた局が記録を書かずに止まることを見る。試験は 7 件増えた(sideAlignment +4・replay +2・failureEvent +1)
- 実測: 型検査 rc=0・**全件 Test Files  42 passed (42)、      Tests  539 passed (539)**(回す前の見込み `stage2x-full-prediction.md`: 532 + 7 = 539)。変異は、足した分(照合を外す `X-1`・`true` を常に書く `X-2`/`X-2b`・cache のキーから開始局面を外す `X-3`)と、この変更で鳴る試験が変わる 4 件(V-S8a・V-S8b・W-R1・W-R2。予測を書き直した)の 8 件(道具 `scratchpad/d0-side/stage2x-mutate.py`、予測は当てる前に `stage2x-mut-out/predictions.md`(sha1 `82c55d8e`)へ書き出した): **適用 8 / 鳴った 8 / 沈黙 0 / 適用できなかった 0**。予測: 集合 8/8・tsc 8/8・中心 3/3 鳴った。変異の前後で 25 ファイルの sha256 が一致した

### 12.8 段 2 の限界
- **`replay.ts` の再生の経路(エンジンを起こす側)は、ソース照合と子プロセスの手前まで**。`GameState.sfen` と `options.initialSfen` が同じ文字列であること(V-S16)はソース照合でしか見ていない。回した局の ready 行の局面・本数は段 R(エンジン)の記録で確かめる
- **開始局面を渡すのは R-5〜R-7 と scan-compare まで**。ほかに記録の指し手履歴を平手から並べ直す読み手が増えたら、同じ扱いが要る(`git grep DEFAULT_INITIAL_SFEN` で探す)
- `check.ts` は、形の食い違う meta(`mirrored: true` で `startSfen` が無い)を読むと例外で止まる(exit 0 の約束から外れる)。`replay.ts` はその形を書かない。壊れた JSON 行で止まるのと同じ扱いにした
- `Invariant.check` の文脈は省略できる(既存の試験の呼び出しを変えないため)。**check.ts が渡し忘れる誤りは型検査では止まらず、check.test.ts の子プロセスでだけ捕まる**(W-C1・W-C2)
- R-9(error 行のある記録を使わない)は、段 1 のとおり scan-compare には効かない(12.4)
- **`originalMoves` の無い回した固定棋譜は照合しない**(司令塔の決定で必須にしない)。その局の記録は `sideAlignmentChecked: false` になるので、使う側が数えて見分ける

- **監査 A の任意の指摘 2 件(GO のまま。司令塔の決定: 段 2 のコミットには入れず、後の小さな追加で塞ぐ、2026-09-15)**: (1) `kifu-import-check.ts` の表の「揃えた手」の列は、どの試験も見ていない(D0-KIFU2 の限界「ソース照合のみ」と同じ。merge で消えても気づけない)。`kifu-import-check.test.ts` の子プロセスに 1 文字の成り駒を含む架空の最小 KIF を 1 件足せば見張れる。(2) 後手の名前の行が 2 本ある固定例が無い(`userSide.test.ts` の (iv) に 1 行)。担当 1e、監査 A。

### 12.9 段 2 の後の小さな追加(基点 `e3b0a17`。監査 A の段 2 の任意 2 件。担当 1e、2026-09-15)

12.8 の最後の段落に書いた 2 つの見張りの穴を、試験を足して塞いだ(振る舞いは変えていない)。
- **任意 1(`kifu-import-check.ts` の表の「揃えた手」の列)**: `kifu-import-check.test.ts` の子プロセスに、1 文字の成り駒「圭」を含む架空の最小 KIF(D0-KIFU2 の計画 3. の T-4 と同じ 9 手)を足した。表の見出しの行と `game.kif` の行を列の名前で突き合わせ、`揃えた手` が `1`・詳細行 `- game.kif 9 手目 揃えて読んだ: 圭→成桂` があること、成り駒を含まない KIF では `揃えた手` が `0` で詳細行が無いことを見る(列が消えると値がずれて赤になる)
- **任意 2(後手の名前の行が 2 本ある例)**: `userSide.test.ts` の (iv) に、後手の行が 2 本ある例を足した(KIF・CSA の両方。`user_side_unknown`)
- **実測**(worktree `wt-d0-side-small`): 型検査 rc=0・scripts/playtest の vitest 全件 **Test Files  42 passed (42)、      Tests  542 passed (542)**(回す前の見込み `stage2y-full-prediction.md`: 539 + 3 = 542)。変異(道具 `scratchpad/d0-side/stage2y-mutate.py`、予測は当てる前に `stage2y-mut-out/predictions.md`(sha1 `00f3a645`)へ書き出した): **適用 3 / 鳴った 3 / 沈黙 0 / 適用できなかった 0**。予測: 集合 3/3・tsc 3/3・中心 2/2 鳴った。変異の前後でファイルの sha256 が一致した
  - Y-1(中心): 読めた行から「揃えた手」の欄を消す(監査 A の B-10 と同じ形)→ 足した子プロセスの試験
  - Y-2: 詳細行「揃えて読んだ」を出さない → 同じ試験
  - Y-3(中心): 名前の行の重なりを先手の側だけ見る(監査 A の B-7 と同じ形)→ 足した (iv) の試験(KIF・CSA)

- **監査 A の任意(GO のまま。限界として残す、司令塔 2026-09-15)**: `not_imported` の行(読めなかった局)の「揃えた手」の欄は、どの試験も見ていない(探り Z-3 が沈黙)。段 2 の振る舞いには関係しない。次に `kifu-import-check.ts` を触る STEP で固定例を足す
