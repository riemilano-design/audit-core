# scripts/playtest/

対局ハーネス(docs/PLAYTEST_LOOP_PROPOSAL.md の外側のループ)。**開発補助であり、本番導線(apps/)には含めない。**

現在実装済みなのは STEP T-1(固定棋譜モード)・STEP T-2(不変条件 I-1〜I-5・draft と集約報告)・STEP T-3(探索モードと対局者の多様化)・STEP T-5(比較の道具 `compare.ts`・分母の報告・表記の更新)・STEP T-6(回帰モードのエンジン条件の固定・不変条件の型「結果」・I-6(draft))・STEP T-7(エンジンの参考評価 `engineReference` の記録・I-7(draft))・STEP T-8(帯を `adviceSource` に足し、I-8(draft))・STEP U6-0(不変条件 I-9(draft)。誤認を測る)。

## 位置づけ

- 本番関数(`apps/server/src/` の既存export)を import して呼ぶだけで、複製・改変はしない。
- 将棋の判断・評価・閾値・文言はここでは一切書かない。
- 出力(JSONL)は記録用。**コミットするかどうかは人間の指示による**(`scripts/playtest/out/` は `.gitignore` 済み)。

## 使い方

```
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json --out /path/to/out.jsonl
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json --nodes 4000000 --threads 1
npx tsx scripts/playtest/replay.ts scripts/playtest/kifu/2026-09-10-claude-10moves.json --reference-nodes 4000000
```

エンジン(`apps/server/engine/YaneuraOu-by-gcc`、`resolveEnginePath()` が解決)を実際に起動する。`--out` を省略すると `scripts/playtest/out/<kifuId>-<timestamp>.jsonl` に書く。

### 回帰モードのエンジン条件(STEP T-6)

固定棋譜モード(`replay.ts`)は候補手の参考評価(⑧)に実際のエンジンを使うため、探索量が実行のたびに揺れうる(STEP T-5 で観測)。この揺れを抑えるため、`replay.ts` は既定で探索量を固定ノード数(`--nodes`、既定 **4,000,000**)・`Threads`(`--threads`、既定 **1**)にする(人間の決定。2026-09-11、提案書 [COVERAGE_AND_OUTCOME_PROPOSAL.md](../../docs/COVERAGE_AND_OUTCOME_PROPOSAL.md) 7.1 設問1 = (b))。

- この既定値は**ハーネスの引数であって、将棋の判断・本番の閾値ではない**。本番の既定値(`movetime 2000`・`Threads` の既定)は変えていない。
- `--nodes 0` を指定すると、探索量を固定せず本番条件(`movetime`)のまま再生する(比較実験用。既定ではない)。
- 実際に使った条件は `meta` 行の `searchMode`(`"nodes"` または `"movetime"`)・`nodes`・`threads` に残るため、`compare.ts`・`check.ts` で条件の違いを追跡できる。`compare.ts` はこれらのフィールドを正規化の除外対象にしていない(=条件が違う記録は一致しない)。
- **探索モード(`explore.ts`)はこの固定を行わない**(本番条件のまま。相手AIの手加減をしないのと同じ理由で、探索モードは本番に近い条件を保つ)。

## 固定棋譜(kifu.json)の形式

```json
{
  "id": "任意のID",
  "source": "出典(自由記述)",
  "moves": ["先手の手", "後手の手", "先手の手", "後手の手", ...]
}
```

先手(自分)から始まり交互。相手側の手は本物のエンジンに問い合わせず、記録済みの手をそのまま返す偽エンジンで適用する(`playOpponentMove` へは承認済みvariantを渡さず空配列 `[]` を渡す。将来variantが承認されても再生が変わらないための防御)。

外部の棋譜から `kifu-import-check.ts --fixed` で作った固定棋譜は、次の欄も持つ(`replay.ts` はそろえの欄を `lib/sideAlignment.ts` の `readSideAlignment` で読み、`ending` は読まない):

- `ending`(STEP D0-KIFU3、`docs/STEP_D0-KIFU3_PLAN_2026-09-15.md`): 棋譜に書かれていた終局の種類と手数。`{ "kind": "timeUp", "ply": 78 }` の形で、`kind` は `lib/kifuImport.ts` の語の表(KIF は `ENDING_KIF_WORDS` の 12 語、CSA は `CSA_ENDING_KINDS`)の英名。表に無い CSA の語は `"unlisted"`。`ply` は**元の手順**の指し手数 + 1(回した局でも `originalMoves` の手数 + 1)。KIF の行頭の手数が食い違えば `{ "kind": "unreadable", "reason": "ply_mismatch", "ply": null }`。終局の行が無ければ `null`。**キーが無い = 終局の行を見ていない**(この STEP より前に作った固定棋譜・探索の棋譜)。終局の行の文と「まで」の行は写さない
- `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`originalMoves`(STEP D0-SIDE 段 2、`docs/STEP_D0-SIDE_PLAN_2026-09-15.md`): `--me` か `--as` で本人の側を決めたときだけ書く。本人が先手なら `mirrored: false` だけ。本人が後手なら `mirrored: true`・`originalUserSide: "gote"`・`plyOffset: 1`・回した 1 手目を開始局面に畳んだ `startSfen`・畳んだ後の `moves`・回す前の手順 `originalMoves`
- `moveSeconds`(STEP TIME、`docs/STEP_TIME_PLAN_2026-09-22.md` §6.1): KIF の指し手行の末尾 `(m:ss/h:mm:ss)` から読んだ、**元の手順の順のまま**(`originalMoves` と同じ並び・同じ長さ。KIF の手数 = 添字 + 1)の消費時間の配列。各要素は `{ "spentSec": 1, "totalSec": 12 }`(切り捨ての整数)か、その手の秒を読めなければ `null`。回した局(`mirrored: true`)でも回さず・詰めない(`moves` ではなく `originalMoves` と対応する)。**1 手も読めていなければ欄そのものを書かない**(CSA・時間の無い KIF・この STEP より前に作った固定棋譜)。既存の固定棋譜に後から足す小さな道具は `kifu-times.ts <fixed.json> <元の KIF>`(下記)
- 欄の並び: 側を決めない `{ id, source, ending, moves }` / 本人が先手 `{ id, source, mirrored, ending, moves }` / 本人が後手 `{ id, source, mirrored, originalUserSide, plyOffset, startSfen, ending, moves, originalMoves }`(`moveSeconds` を持つときは、いずれも `ending` の後ろ・`moves` の前)

## JSONL の形式

- 先頭行: `{"kind":"meta", "kifuId", "startedAt", "gitHead", "enginePath"}`(固定棋譜モードは STEP T-6 で `searchMode`・`nodes`・`threads`、STEP T-7 で `referenceNodes` を追加。探索モードは `mode: "explore"`・`profile` 等、STEP T-7 で `referenceNodes` を追加。上記参照)
- 各記録行: `{"kind":"record", "ply", "sfen", "senteMove", "goteMove", "phase":"immediate"|"ready", "elapsedMs", "response", "engineReference"}`(`response` は `buildStateResponseWithPlan` の戻り値そのまま。web が受け取るのと同じ形。`engineReference` は STEP T-7 で追加した ready 行のみのフィールド。下記「エンジンの参考評価(STEP T-7)」参照。immediate 行にはキー自体が無い)。**STEP FILL 作業 X** で、`engineReference` が null・終局でなく本人(先手)が王手中の ready 行にだけ `checkBaseline`(現局面だけの参考評価。下記「王手中の局面の参考評価(STEP FILL)」参照)を追加した。それ以外の行にはキー自体が無い
- 想定内エラー(非合法手・相手の手の不一致)の場合: `{"kind":"error", ...}` を書いて exit 1
- 末尾行(正常終了時のみ): `{"kind":"summary", "plies", "totalMs", "readyMsPerPly"}`

## 探索モード(STEP T-3)

固定棋譜モード(replay.ts)は**回帰**用(一度記録した局面列を再生し、変更前後の検出数を比べる)。探索モードは**発見**用で、相手を本番と同一(素のエンジン、`movetime 1000`)に戻し、自分側は5プロファイル(`scripts/playtest/lib/players.ts`)のいずれかで指させることで未知の局面列を作る。

```
npx tsx scripts/playtest/explore.ts --games 10 --seed 1
npx tsx scripts/playtest/explore.ts --games 10 --seed 1 --plies 60 --out-dir /path/to/out
```

- `--games`(既定10)・`--seed`(既定1)・`--plies`(既定60。1局あたりの手数の上限)・`--out-dir`(既定 `scripts/playtest/out/explore-<startedAt>/`)
- 10局の既定の内訳: S1×2、S2×2、S3×2、E×2、R×2(`--games` が10以外の場合はこの順を繰り返す)。局ごとの種は `seed + 局番号` から決定的に導出する
- 対局者(自分側)の5プロファイル(台本はテストの入力であり、ユーザーに見せる知識でも本番の判断でもない。将棋の良し悪しを判断する規則は無い):
  - **S1(文どおり)**: 候補手が `ready` ならその最初の説明の手。無ければ道のりの最初の一手。どちらも無ければ E
  - **S2(逃げる)**: 駒が当たっている(`piece_attacked`)なら、その駒の合法手のうち移動先に相手の利きが無い手。無ければ S1
  - **S3(振り飛車定型)**: 定型序盤列を先頭から合法な手だけ消費。使い切ったら S1
  - **E(浅い読み)**: 同じエンジンプロセスに `movetime 100` で指させる
  - **R(乱択混合)**: 既定 `randomRate 0.3` で合法手から乱択、それ以外は E
- 出力: 局ごとに `game-NN.jsonl`(T-1 と同じ形式。`meta` に `mode: "explore"`・`profile`・`seed`・`randomRate`・`pliesCap` を追加)と `game-NN.kifu.json`(`{ id, source: "explore", profile, seed, moves }`。`replay.ts` でそのまま再生できる形式)。最後に `check.ts`(変更なし)を10局へ実行した結果を `report.md`・`report.json` として同じディレクトリへ書く
- 終了条件: 終局(`isGameOver`)・相手または自分のエンジンが手を返さない・`--plies` 到達。理由は各 `game-NN.jsonl` の末尾付近の `{"kind":"end","reason",...}` 行に書く

**この出力の意味について**: 探索の出力(JSONL・kifu JSON)は**観測**であり、何も拘束しない。`check.ts` の検出(=候補事象)も、既知事項・仕様・`kifu/` への登録に自動では昇格しない(docs/AGENT_PROTOCOL.md 11.)。局面列を固定棋譜として `scripts/playtest/kifu/` へ登録するかどうかは、人間の判断による。

## エンジンの参考評価(STEP T-7)

`scripts/playtest/lib/engineReference.ts` が、ready 行ごとにエンジンの参考評価を測って記録する(`engineReference: EngineReference | null`。**ハーネスの観測であり、本番の判断・表示ではない**。本番側の候補手の参考評価(⑧、`analysis/candidateMoveReferenceFilter.ts` の300cp)とは無関係)。

- `baseline`: 現局面(先手番)を MultiPV1・固定 nodes で読んだ結果(先手視点の `scoreCp`/`mate`/`bestmove`)
- `afterPass`: 手番を入れ替えた局面(`passSfen`。先手がパスしたのと同じ盤面)を同条件で読んだ結果(後手視点)。`captureSquare` は、その `bestmove` の移動先に先手の駒があればそのマス、無ければ `null`
- `dropCp`: `baseline.scoreCp − (−afterPass.scoreCp)`(先手視点の落ち幅)。両方 `cp` のときだけ算出し、それ以外(`mate` が絡む・欠測)は `null`
- 測らない場合(`null` を記録): 終局、先手が王手中(パスが成立しない)、エンジンの例外・タイムアウト(推測しない)
- 探索量は `replay.ts` の `--reference-nodes <N>`(既定は `--nodes` の値。`--nodes 0` のときは 4,000,000)、`explore.ts` は常に 4,000,000 固定(候補手計算に使う自分側/相手側の条件は一切変えない)。実際に使った値は `meta.referenceNodes` に残る
- 候補手計算用の探索量固定(`lib/fixedSearchEngine.ts`)とは独立の値として扱う(呼び出しには raw な `LowPriorityEngine` を使うため、`--nodes` と `--reference-nodes` に異なる値を指定しても、参考評価には `--reference-nodes` の値がそのまま使われる)

## 王手中の局面の参考評価(STEP FILL 作業 X)

`engineReference`(上記)は、本人(先手)が王手中の局面では「パスが成立しない」という理由で `null` のまま返る(本番の `measureEngineReference` はエンジンを一切呼ばない)。そのままでは王手中が続く局面に評価が一切付かず、優勢から自玉の詰みへ変わる過程が診断の組・グラフから抜ける。`scripts/playtest/lib/checkBaseline.ts` の `measureCheckBaseline` が、ハーネスの観測として**現局面だけ**(パスした局面は読まない。王手中はパスが成立しないため)を別に測り、`checkBaseline: { scoreCp, mate, bestmove, nodes } | null` を ready 行に足す。**`engineReference` 自体は変えず `null` のまま残る**(「パスの比べは測っていない」という意味を保つ)。

- 記録する行(段 1、`replay.ts`・`lib/recorder.ts`): `engineReference` が `null`・終局でなく・本人が王手中・`--reference-nodes` が 0 でない ready 行にだけ、`--reference-nodes` と同じノード数で測る。それ以外の行(王手中でない・終局・`--reference-nodes 0`)には `checkBaseline` のキー自体が無い
- 段 2(`rescreen.ts`): 読み直す行に選ばれた行が王手中なら、同じ形で `checkBaselineDeep`(深いノード数版)を足す。深く読み直す行の選び方(`DRAFT_SCREEN_RULE_1`)は変えない
- 読み方(`lib/failureEvent.ts` の `evaluationOf`。深い側は `lib/screenDiagnosis.ts` の `deepRowOf` が `checkBaselineDeep` を `checkBaseline` に差し替えて同じ関数へ渡す): `checkBaseline` に値があれば `state: "measured"`(`afterPassScoreCp`・`afterPassMate`・`dropCp` は `null` ― パスが成立せず比べていないため)。`checkBaseline` が無い(古い記録・王手中でない・終局・`--reference-nodes 0`)・`null`(測ろうとして測れなかった)行は、これまでどおり `notMeasuredInCheck`。`|scoreCp| ≥ NOT_EVALUATION_CP` の扱い(`notEvaluation`)は `engineReference` と同じに当てる
- `records/` の既存の記録(この STEP より前に取ったもの)は `checkBaseline` の欄を持たないため、読み方はこれまでどおり変わらない

## 不変条件チェック(STEP T-2・STEP T-5・STEP T-6・STEP T-7 で表記を更新)

T-1 が保存した JSONL(1件以上)に対して、不変条件 I-1〜I-9(`scripts/playtest/invariants/`。**I-1・I-2 は 2026-09-11 に人間承認で `status: "approved"`、他(I-3〜I-9)は `status: "draft"`**)を適用し、検出を「型 × 発生条件」で束ねた報告を標準出力(Markdown)へ書く。常に exit 0(`approved` を含め、検出は何もブロックしない。exit code の扱い自体は人間承認事項)。

```
npx tsx scripts/playtest/check.ts scripts/playtest/out/run1.jsonl scripts/playtest/out/run2.jsonl
npx tsx scripts/playtest/check.ts scripts/playtest/out/run1.jsonl --json scripts/playtest/out/check.json
```

`--json` を指定すると、機械可読の結果(`{ inputs, invariants, findings, groups, denominators }`)も同じ内容で書き出す。「## 入力」の各行に `profile`(`meta.profile` があればそれ、固定棋譜モードのように無ければ「固定」)を出す。入力の `gitHead` が2種類以上ある場合、または入力の探索条件(`meta.searchMode`/`nodes`/`threads` の組。STEP T-6)が2種類以上ある場合、「## 入力」節の末尾にそれぞれ混在している旨の注意が1行出る。

### 型「結果」と I-6(draft。STEP T-6)

不変条件の型は6型(沈黙・矛盾・断定・未説明用語・盤との不一致・陳腐化)に加え、STEP T-6 で7型目「**結果**」を追加した(人間承認済み。[COVERAGE_AND_OUTCOME_PROPOSAL.md](../../docs/COVERAGE_AND_OUTCOME_PROPOSAL.md) 7.1)。他の6型が「説明の言い方」の不整合を対象にするのに対し、「結果」は実際に盤上で起きたこと(局面・手の事実)を対象にする。

**I-6**(`invariants/i6-advice-then-loss.ts`、`status: "draft"`)は、提案書 4.3 の最小案(2026-09-11 人間決定)を実装したもの: 直前に画面へ出ていた助言(候補手または道のりの一手)と**一致する**手を指した直後、相手の応手で駒を取られ、取り返す手が合法手に無い場合を検出する(得喪の合計のような単純案は扱わない)。`condition` は `adviceSource`(`candidate` または `route`)。

### I-7(draft。STEP T-7)

**I-7**(`invariants/i7-urgent-but-other-talk.ts`、`status: "draft"`、型「沈黙」)は、提案書 4.4 の述語案(2026-09-11 人間決定)を実装したもの: 「先に言うべき事実があるのに、別の話をしている」を検出する。

- **緊急事態**(エンジンの事実): `engineReference` があり、`dropCp !== null && dropCp >= 300` かつ `afterPass.captureSquare !== null`(パスすると相手の最善手が捕獲を含む)、かつその `captureSquare` の駒が `listAttackedPieces` → `detectPieceThreats`(`apps/server/src/analysis/pieceThreatDetector.ts`)の結果に含まれる(square 一致。[0]「今すぐ対処が必要なこと」と同じ対象駒種(飛・角・金・銀・桂・香)に限る。2026-09-11 人間決定、STEP T-7b。歩・成駒(と金等)は対象外)
- **別の話**(画面の事実、`condition` に残す): `urgent_empty`(`plan.urgentMessages` が空)、または `route_shown`(`plan.routes.length > 0`、または `candidateMove.status === "ready"` かつ説明が1件以上、または `lastMoveOutcome.messages` に `route_advanced`/`route_completed`/`route_first_move_available`/`played_candidate` のいずれかがある)
- 検出しない: `engineReference` が `null`(測っていない)、終局。`captureSquare` の駒が [0] の対象駒種でない(歩・成駒等)。`urgentMessages` に当たりの行があっても `route_shown` に該当すれば検出する(「[0] が当たりを述べていても道のりの進捗を並べれば事故は起きる」という意図)

**閾値 300cp は draft の初期値であり、将棋一般の閾値ではない**(2026-09-11 人間決定。`I7_DROP_THRESHOLD_CP`。approved 化の前に人間が再判断する)。**これは「最善手を言え」ではない**。候補手そのものの良し悪し(最善手かどうか)は判断せず、盤の事実とエンジンの参考評価から「先に言うべき事実」の有無だけを拾う。

### I-8(draft。STEP T-8)

**I-8**(`invariants/i8-band-piece-then-captured.ts`、`status: "draft"`、型「結果」)は、`docs/BASELINE_2026-09-12.md` 3.3(2026-09-12 人間決定)を実装したもの: **帯([0]「いま注意する駒」)が名指しした駒を自分が動かし、その直後の相手の手でその駒が取られた**場合を検出する。基準値の 4 局で、人間が「誤らせる型(最優先)」と判定した局が I-1〜I-7 のすべてで 0 件になったため追加された(I-6 は `adviceSource`(候補手・道のり)だけを見て帯を対象にしないため)。

- 判定: 直前の ready 行(t-2)の帯に `piece_attacked` があり、`senteMove` の移動元がその名指しマスに含まれ(`lib/adviceSource.ts` の `movesBandNamedPiece`。打つ手は対象外)、本番関数 `detectBoardEvents` の結果に `captured_by_opponent` かつ移動先のマスの事象があるとき。`detectBoardEvents` が例外を投げた行は検出しない。
- `condition` は `deriveAdviceSource`(`band` / `candidate` / `route`)。帯が名指しした駒を動かす手が同時に候補手・道のりにも載っていた場合は `band` ではなく `candidate`/`route` になる(重なりを隠さないため)。
- **この不変条件が言わないこと**: 「帯の言うとおりに逃がしたら取られた」を数えるものではない(帯は「どこへ逃げれば安全か」を言わないため、名指しされた駒を動かす手が逃げる手とは限らない)。因果も主張しない(動かさなくても取られていたかは判定しない)。I-6 と違い「取り返す手が合法手に無い」ことは要求しないため、**I-6 より広い**(両方に出る行がありうる)。

### I-9(draft。STEP U6-0)

**I-9**(`invariants/i9-shape-claim-without-evidence.ts`、`status: "draft"`、型「盤との不一致」)は、docs/PHASES.md「Unit 6 の再定義と決定」H-5(2026-09-12 人間承認)を実装したもの: ④が特定の形(`plan.targetShapeProgress`)の組み上がりを出しているのに、指し手で作られたことが確認できる証拠(`formationEvidence`)がほとんど無い場合を検出する。背景は縛った初心者の3局目の観測(docs/OBSERVATION_BEGINNER_CLAUDE_2026-09-12.md 3.。玉を初形から一度も動かしていないのに④が「本美濃囲いに近づいている」と言い続けた)。

- 記録(JSONL)には `formationEvidence` が入っていないため、`sfen` と `moveHistory` から本番関数 `analyzeShapeFormation`(`apps/server/src/analysis/shapeFormationAnalyzer.ts`)を**呼び直して**再計算する(判定ロジックは複製しない)。
- 検出条件: `targetShapeProgress` の `shapeId` と一致する結果の `formationEvidence.length <= 1`(`I9_MAX_EVIDENCE`)かつ `targetShapeProgress.missingSquares.length >= 2`(`I9_MIN_MISSING`)。`missingSquares` は応答の値をそのまま使い、再計算しない。
- **証拠1件・欠け2件以上という閾値は draft の初期値であり、将棋一般の閾値ではない**(H-5。approved 化の前に人間が再判断する。H-3 の順序: (i) I-9 で誤認を測る → (ii) 量だけ増やす → (iii) 同じ4局で再測定 → (iv) それから閾値を判断)。
- **この不変条件が言わないこと**: 形の名前が間違っているとは主張しない。ユーザーがその形を目指していたかどうかは判定しない。因果(この一致が原因で誤認した等)も主張しない。言えるのは「④が組み上がりを出している局面で、証拠が n 件・欠けが m 件だった」という記録上の事実だけである。

### `adviceSource`(記録ではなく事後判定)について

「その手が、直前に画面へ出ていた助言と一致していたか」(`adviceSource`。`scripts/playtest/lib/adviceSource.ts`)は、JSONL に新しい項目を記録するのではなく、**直前の ready 行の既存フィールド(候補手の説明・道のりのラベル)から事後に導く**純粋関数として実装した。対局者プロファイル S1(文どおり)の選択規則が、直前の ready 行の同じフィールドだけを見て決まるため、記録を増やさずに判定できる(STEP T-6 計画書 F-9)。

**重要: `adviceSource` が `candidate`/`route` であることは「その手が助言と一致した」ことを意味するのであり、「助言に従った」ことを意味しない。** 選択規則が実際に助言を参照しているのは S1(および S1 規則へフォールバックした S2・S3 の手)だけで、E(浅い読み)・R(乱択混合)の手は助言を参照せずに決まるため、一致は偶然でありうる。固定棋譜(人間の対局)は手の由来が記録に無いため、区別せず「一致」として扱う。I-6 の `detail` 文も「一致する」と書き、「従った」とは書かない。**探索10局などの集計を読むときは、S1 と他のプロファイルを分けて読むこと**(`profile` は `meta.profile` に残っている)。

**この報告の意味について**: 不変条件(`approved` と `draft`)による検出であり、仕様・既知事項・異常の有無を確定するものではない。`approved` の検出は STEP の完了条件に関わる(docs/AGENT_PROTOCOL.md 11.)。0件は「有効な不変条件が捉える範囲では検出されない」ことを意味する(docs/AGENT_PROTOCOL.md 11. 規則5)。有効化(`draft` → `approved`)・既知事項への追加・仕様変更は、この報告からは自動で起きない(人間の判断が要る)。

不変条件を追加する場合は `scripts/playtest/invariants/i*.ts` を1件追加し、`index.ts` の一覧に加える。`status` は draft のまま追加してよいが、`approved` にする操作(=STEP の完了条件に入れる)は人間承認事項(docs/AGENT_PROTOCOL.md 11.)。

### 分母(観測の集計。STEP T-5 T5-B)

`check.ts` の報告に「## 分母(観測の集計)」節が出る。入力(kifuId)ごとに、`phase: "ready"` の record 行を「全手数・認識あり・道のりあり・候補手あり・候補手が全件除外・いずれも無し(沈黙)」の6列で数えたもの(定義は既存フィールドの機械的な読み取りのみ、`scripts/playtest/lib/denominators.ts`)。探索の記録(`meta.mode === "explore"`)は `meta.profile` ごとの小計行もあわせて出る。**観測の集計であり、不変条件ではない。何も異常と呼ばない。**

## 比較の道具(STEP T-5 T5-A)

複数の JSONL を読み、実行のたびに変わる値(record 行の `elapsedMs`、meta 行の `startedAt`/`gitHead`/`enginePath`、summary 行の `totalMs`/`readyMsPerPly`)を除いて正規化し、1本目を基準に他のファイルと比較する。揺れの観測(同じ棋譜を複数回再生した結果を比べる)に使う。常に exit 0(観測であり判断はしない)。

```
npx tsx scripts/playtest/compare.ts run-01.jsonl run-02.jsonl run-03.jsonl
npx tsx scripts/playtest/compare.ts run-01.jsonl run-02.jsonl --json compare.json
```

出力は Markdown(入力一覧、基準と一致した本数、差があった行の `ply`・`phase`・JSON の差分パス(最大数件))と `--json` の機械可読な結果。

## reports/(探索の集約報告の保管)

`scripts/playtest/reports/` は追跡対象(`out/` と異なり `.gitignore` されない)。探索モードの集約報告(`report.md`・`report.json`)のうち、検証材料として保持すると人間が判断したものをコピーして置く。ここに置いた候補事象は仕分け(直す/受容/持ち越す)待ちであり、既知事項・仕様への登録を意味しない。

## 一本の流れ(`pipeline.ts`。STEP PIPE 作業 A・作業 C)

`scripts/playtest/pipeline.ts` は、S1(読み込み)〜S7(PDF)の 7 段を**既存の道具を子プロセスで呼ぶ順に並べるだけ**の道具である(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1・§2.2 の最後・§3 (a))。**S1〜S7 のどの道具の中身も複製・改変しない**。将棋の判断・閾値・文言はここでは一切書かない。

```
npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir>
  [--me <名前>] [--parallel <N=5>]
  [--compare-dir <段2の記録のフォルダ …> --compare-person <p記号>]
  [--name <表示名> --title <タイトル> --today <YYYY-MM-DD>]  … --until が report-data・prose・pdf のときだけ必須
  [--until import|evaluate|diagnose|gate|report-data|prose|pdf] [--evaluator "<評価関数の識別>"] [--dry-run]
```

- **段**: S1 `kifu-import-check.ts`(読み込み)→ S2 `replay.ts`(軽い値。nodes/reference-nodes 400,000・threads 1・direction-rule current)→ `rescreen.ts`(深い値。deep-nodes 4,000,000)→ S3 `diagnose.ts`(1 人ぶんまとめて)→ S4 `gate.ts`(`--compare-dir` があるときだけ)。引数の値は固定(表と違う値を渡す旗は無い)
- **先後**: `--me <名前>` を全局へ渡すか、`--me` を渡さなければ局ごとにファイル名の末尾 `-sente`/`-gote` を読む(id はそれを除いた部分)。どちらも無ければ**推測せずに止まる**
- **途中から再開できる**: 段ごと・局ごとに、出力があって完結していれば(段 1 は最後の行が `summary`、段 2 は空でない、fixed 棋譜は `id`・`moves` がある、診断は 4 つの出力がすべてある、gate は出力がある)飛ばす
- **並行**: `--parallel`(既定 5)を上限にした局ごとのジョブの列。1 局の失敗で他は止めず、最後に失敗の一覧と `exitCode ≠ 0`
- **所要**: 局ごとの開始・終了・rc を `<work>/timing.jsonl` に書く
- **`--source` は絶対パスにしない**: `kifu-import-check.ts --source` には `--kifu-dir` からの相対パス(ファイル名そのもの)を渡す(絶対パスを固定棋譜に残さないため)。第一引数(道具が実際に読む場所)は指定どおりのパスのまま
- **`--work`・`--kifu-dir`・`--compare-dir` は受け取った時点で絶対パスにする**(STEP FILL 作業 Y、H3、docs/STEP_FILL_PLAN_2026-09-22.md §3)。相対パスで `--work` を渡すと、S7(python・cwd = `report-pdf/`)へ `REPORT_DATA_DIR` として渡すときに `report-pdf/` からの相対として解決されてしまい、pdf の段だけ失敗する(S1〜S5 は相対パスのままでも通るため気づきにくい)。`parsePipelineArgs`(`lib/pipeline.ts`)が `path.resolve()` で直す(すでに絶対パスなら値は変わらない)
- **S4(`gate.ts`)の向き(2026-09-21 の直し)**: **材料の側 = このお客さん**(`--person`・`--kifu-dir` の局。`gate.ts` の `--person`・`--material`)、**試す側 = `--compare-dir` の記録**(`gate.ts` の `--test-person`・`--test-sente`/`--test-gote`)。2 人目 20 局(材料)を 1 人目 10 局(試す側)で確かめた C-1・C-5 の正式な実行と同じ向き(docs/STEP_D3-COND_PLAN_2026-09-15.md §14・§15.2)。`--compare-dir` の記録の先後は**各記録の meta 行(`mirrored`・`originalUserSide`。`replay.ts` が書く。`lib/sideAlignment.ts` の `sideMetaFields`)から読む**。ファイル名には頼らない(比較対象のフォルダに命名の規約は無い)。meta から決められない記録が 1 件でもあれば、推測せずこの段を失敗にして理由(ファイル名)を出す
- **`--compare-person`**: 計画の CLI には試す側の人のラベルを渡す旗が無かったため、`gate.ts` が要求する「試す側の人のラベル(p1・p2 の記号)」を渡すための `--compare-person` を新設した(`--compare-dir` と必ず一緒に渡す)。`--person`(材料)には `--person` の値をそのまま使う
- **`--records-append` は決して付けない**。`records/` へは一切書かない(棄却の記録へ書くのは、予測を先にコミットした正式な実行だけで、司令塔が手で回す)
- **試験はエンジンも子プロセスも起こさない**: fs・道具の実行(`ToolRunner`)を注入できる形にし、段の順序・済みの飛ばし・並行の上限・1 局の失敗が他を止めないこと・引数の固定・`--until`・`--dry-run`・gate の材料/試す側の向き・meta から本人の側が決められない記録の扱いを `scripts/playtest/lib/pipeline.test.ts` で見張る

`--dry-run` は何も書かず・何も実行せず、段ごとの `run`/`skip` とその引数を表示するだけ(`diagnose`/`gate` のプレビューは、その時点ですでに段 2 まで済んでいる局だけを対象にする。これから実行して済むはずの局は、実行するまで成否が分からないため含めない)。**`--dry-run` は S1〜S4 までのプレビューのまま**(下の S5〜S7 のプレビューは作業 C では足していない。`--until` に `report-data`/`prose`/`pdf` を渡しても、表示は gate までで止まる)。

### S5〜S7(本人向けの材料・言い換え・PDF。STEP PIPE 作業 C)

作業 B で足された `reportData.ts`(S5)・`report-pdf/`(S7)を、`pipeline.ts` の続きの段としてつなぐ。出力は `<work>/report/` の下(局ごとではなく人ごと 1 か所)。

- **S5**(`reportData.ts`。`--until report-data`): 材料 = **このお客さんの段 2**(`--person`・`--kifu-dir` の局。gate 段と同じ向き)。`--records`(段 2)・`--kifu`(固定棋譜)・`--gate`(`<work>/<person>/gate.jsonl`)を渡し、`patient_report_data.json`・`audit_metrics.json`・`sfens.json`・`prose-request.md`・**`finding_texts.json`**(STEP TIME 作業 3。旗は無い。`patient_report_data.json` と同じフォルダに常に書く)を書く。`--conditions`・`--king-escapes-condition`・`--move-check-condition` は渡さない(reportData.ts の既定 = 金の標本(第 6 版)に合わせた承認済みの定義のまま)。**`--gate` の出力(`gate.jsonl`)が無ければ(`--compare-dir` を渡さず gate 段が飛ばされた等)、reportData.ts を呼ばずに「判定の出力(gate.jsonl)が無い(--compare-dir が要る)」とはっきり失敗にする**。**済みの判定**: `patient_report_data.json`・`audit_metrics.json`・`sfens.json` の 3 つが揃っていれば飛ばす(`finding_texts.json` の有無は済みの判定に使わない。古い work フォルダには無いことがある)。**STEP TIME**: `reportData.ts` に `--time-limit-sec <秒>` を渡すと、`patient_report_data.json` の `time.byLeft`(残り時間の 3 段)を出す(渡さなければ `byLeft` は `null`)。持ち時間は同じ人・同じ回の局ならすべて同じ前提(1 回の実行に 1 つの値)。**STEP TIME 作業 2**: `--previous <前回の patient_report_data.json>` を渡すと `patient_report_data.json` の `previous`(発見の種類ごとの前回・今回の比較)を出す(渡さなければ `null`)。`pipeline.ts` はこれらの旗をまだ中継しない(`--time-limit-sec`・`--previous` を付けて回すときは `reportData.ts` を直接呼ぶ)
- **S6**(言い換え。`--until prose`): 自動化しない(LLM を呼ばない)。`<work>/report/prose.json` が無ければ、`prose-request.md` の場所を示して失敗にする(rc ≠ 0)。あれば次へ進む。照合(使わない語・文の数)はしない ― それは S7 の `_mid.py` の役目のまま
- **S7**(PDF。`--until pdf`): まず本編 4 節(`front.pdf`。STEP TIME 作業 2・作業 3): `python3 -X utf8 render_front.py <patient_report_data.json> <出力 PDF> [<finding_texts.json>]` → `python3 -X utf8 check_fonts_embedded.py <出力 PDF>`(`prose.json` を読まないので `REPORT_DATA_DIR` は渡さない。失敗は `stage: "front-pdf"` で、**下の main.pdf の生成とは独立**(front.pdf が失敗しても main.pdf は作る))。**`finding_texts.json` は、`<work>/report/` にあれば第 3 引数として渡す(`pipeline.ts` が `fs.readText` で有無を確かめる。無ければ 2 引数のまま = 今の形(数の文だけ))**。次に `report-pdf/build.sh`(`render_main.py`・`render_appendix.py` を作る)→ `REPORT_DATA_DIR=<work>/report python3 -X utf8 render_main.py <patient_report_data.json> <出力 PDF>` → `python3 -X utf8 check_fonts_embedded.py <出力 PDF>` の順に呼ぶ(README は `scripts/playtest/report-pdf/README.md`。python の実行ファイルはそこに書かれた `python3` のまま)。**別冊(`render_appendix.py`)は作らない**(`report-pdf/README.md` に明記した既知の欠落。`reportData.ts` の `audit_metrics.json` からは作れない欄があるため)。**済みの判定**: `front.pdf` は `patient_report_data.json` より新しい(mtime)ときだけ飛ばす(`prose.json`・`finding_texts.json` は見ない)。`main.pdf` は `prose.json`・`patient_report_data.json` の両方より新しい(mtime)ときだけ飛ばす。`prose.json` が無い(S6 が失敗している)ときは S7 全体(front.pdf も)を一切起こさない
- **試験はエンジンも python も起こさない**: S1〜S4 と同じ `ToolRunner` の注入で、道具の実行をすべて差し替える(`scripts/playtest/lib/pipelineReport.test.ts`)

段の一覧(`STAGES`・`UNTIL_STAGES`、`lib/pipeline.ts`)は配列なので、後で司令塔が足せる。

## 消費時間(STEP TIME 作業 1。`docs/STEP_TIME_PLAN_2026-09-22.md` §6.1)

- **取り込み**: `kifu-import-check.ts --fixed` は、KIF の指し手行の末尾 `(m:ss/h:mm:ss)` を読んで固定棋譜に `moveSeconds` を書く(形式は上記「固定棋譜(kifu.json)の形式」)。CSA は読まない(今回は対象外)。
- **既存の固定棋譜に後から足す**: `npx tsx scripts/playtest/kifu-times.ts <fixed.json> <元の KIF>`。元の KIF を読み直し、固定棋譜の本人の手順(`originalMoves` があればそれ、無ければ `moves`)と 1 手でも食い違えば書かない(理由を標準エラーへ出して exit 1)。一致すれば `moveSeconds` を足して書き直す(**mtime は変えない**)。1 手も秒を読めなければ、欄を足さずに exit 0。開発補助であり本番導線には含めない。
- **`patient_report_data.json` の `time`**(`lib/reportData.ts` の `buildPatientTime`。判定的な値は `TIME_VALUES` の 1 か所): 1 局でも `moveSeconds` が無ければ `available: false` で他の欄はすべて `null`(比較対象の棋譜など、一部だけ出して比べられるように見せない)。`available: true` のときの欄:
  - `perMove`: 本人の手の秒の件数・中央値・平均・10 秒以上/30 秒以上/0〜1 秒の割合(%)・1 局あたりの消費の中央値
  - `bySpent`: その手にかけた時間で 4 段(0〜1・2〜4・5〜9・10 秒以上)に分けた `{ n, collapsed }`(`n` は既存の崩れの組・`counted` と同じ分母)
  - `afterLongThink`: `quickAfterLongThink`(直前の自分の手が 10 秒以上で、この手は 4 秒以下)・`afterLongThinkAny`(直前の自分の手が 10 秒以上。この手の時間は問わない)。**「直前の自分の手」は 2 手前**(1 手前は相手の手)
  - `byLeft`: `--time-limit-sec` を渡したときだけ(渡さなければ `null`)。残り = 持ち時間 − それまでの本人の消費の合計(この手より前・`spentSec` の和)で 3 段(60 未満・60〜119・120 以上)に分ける。残りが負でも「60 未満」の段に入る
  - `phaseSpent`: 序盤・中盤・終盤(既存の `phaseOf`)ごとの本人の消費の合計を局ごとに出し、「`timeUpLoss`(本人が時間で負けた局。`ending.kind === "timeUp"` かつ本人の結果が「負け」。相手が切れ負けた勝ちの局は入らない)」と「`otherGames`(それ以外)」で中央値
  - `timeUpLosses`: 本人が時間で負けた局(`timeUpLoss` と同じ絞り込み)の局番号・手数・本人の消費の合計(その局で読めた最後の本人の手の `totalSec`)・最後に読んだ局面の評価(`displayScoreOf`)

## 本編 4 ページ(STEP TIME 作業 2。`docs/STEP_TIME_PLAN_2026-09-22.md` §6.4)

2 回目以降の主役になる本編 4 ページを道具で出す。今の本編(凍結した第 6 版、局ごとのページ。`main.pdf`)は**触らず、
資料 1 になる**。発見の判定は `lib/reportData.ts`(TypeScript・試験できる側)で行い、`report-pdf/render_front.py` は
描くだけ。

- **`patient_report_data.json` の `findings`**(`lib/reportData.ts` の `buildFindings`。判定的な値は `FINDING_VALUES` の
  1 か所): 種類は固定の一覧 `timeSpent`(T1: 10 秒以上かけた手の崩れ率が 0〜1 秒の 2 倍以上・10 秒以上の組が 20 組以上)・
  `timeUpLoss`(T2: 持ち時間を使い切って負けた局が 1 局以上)・`aheadLoss`(**局の数**。凍結の `_head.py` の
  `game_facts` と同じ決め方 ― その局の `scores`(表示の向き)が一度でも `STANDING_BOUNDS.aheadCp`(+300)以上になった局を
  `numbers.aheadGames`、そのうち `result` が「負け」の局を `numbers.aheadLossGames`。`aheadLossGames` が 1 局以上で出す。
  司令塔の直し、2026-09-23: 当初は `overview.fromAhead`/`fromAheadLoss`(組の延べ)を使っていたが、文が「対局が n 局」と
  書くのに合わせて局の数へ直した)・
  `phase`(崩れの序中終。つねに出す・判定なし)・`none`(上の 3 つが 1 つも出ないとき)。`shown: false` の発見も JSON には
  書く(数つき。前回との比較に使う)。文の中の数はすべて `numbers` から作る
- **`patient_report_data.json` の `previous`**(`lib/reportData.ts` の `buildPrevious`。CLI の `--previous <前回の
  patient_report_data.json>`): 種類ごとに「前回出た・今回も出た/前回出た・今回は出ない/前回出ない・今回出た」の
  3 通り + 両方の数(`numbersBefore`・`numbersNow`)。渡さなければ `null`(python は「初回のため、前回との比較は
  ありません」の 1 文を出す)
- **`report-pdf/render_front.py`**(新規ファイル。既存の 6 本(`_head.py` 等)は変えない): `patient_report_data.json` の
  `findings`・`previous`・`time`・`overview`・`summary` だけから、A4 縦 4 ページの PDF を作る(1 今回の n 局で分かった
  こと / 2 前回のことは、今回も起きたか / 3 次の n 局で見るもの(名前と今回の値だけ。予測や助言は書かない) / 4 数え方)。
  詳しい設計は `report-pdf/README.md` の「本編 4 ページ」節を参照
- `pipeline.ts` の S7 に `front.pdf` を足した(`main.pdf` の前に描く。上の「S5〜S7」節を参照)

## 固定文の差し込み(STEP TIME 作業 3。`docs/STEP_TIME_PLAN_2026-09-22.md` §6.7)

「じゃあどうしたらいい?」に人を介さずできる限り答える 3 段(考えられること・次の 20 局で見分けがつくこと・
試せること)を `front.pdf` に足す。**文の正本は docs §5.2・§5.3。コードは写しであり、試験が両者の文字列一致を
確かめる**(`lib/findingTexts.test.ts`)。局ごとに LLM が考える文ではない(発見の種類ごとに固定)。

- **`lib/findingTexts.ts`**(新規、純粋データ): `FINDING_TEXTS`(発見の種類ごとの `title`・`considerations`・
  `distinguish`・`tryable`。`phase` は 3 つとも `null` ― §5.2 T5「考えられること・試せることは付けない」)、
  `CONSIDERATIONS_LEAD`(「考えられること」の頭に付ける 1 文)、`PREVIOUS_TEXTS`(§5.3 の 3 通り)、
  `EVAL_JITTER_NOTE`(評価の揺れの注記)、`FORBIDDEN_FINDING_TEXT_WORDS`(§5.1 の禁止語 18 語 + 「すべき」
  「した方がよい」)、`buildFindingTextsFile()`(`finding_texts.json` の形を作る)。
  - **`title` について**: 型には `title: string` があるが、docs §5.2 の見出し行(「T1 \`timeSpent\`: …」)は
    §5.1 の「答えの形」(3 段)には含まれず、1 ページ目の見出しはすでに `render_front.py` の `TITLE_JP`
    (作業 2 で実装担当が決めた、事実だけの題)が担っている。この STEP はそれを変える指示を受けていないため、
    `title` は **新しい文言を作らず、既存の `TITLE_JP` と同じ文字列をそのまま移した**(実装担当の判断。docs との
    一致試験の対象にはしない ― 試験は §5.2・§5.3 の 3 段・3 通りの文だけを見る)
- **`lib/findingTexts.test.ts`**: docs のファイルを実行時に読み、見出し行(`**T1 \`timeSpent\`: …**` 等)から
  節を切り出して `- 考えられること(...): (a) … (b) … (c) …`・`- 次の 20 局で見分けがつくこと: …`・
  `- 試せること: …` の行を正規表現で取り出し、`FINDING_TEXTS` と文字列として一致することを確かめる(切り方は
  試験の中に書く。docs を書き換えたらこの試験が赤くなる)。§5.3 の 3 通り・評価の揺れの注記も同様。禁止語 0 の
  試験も含む
- **`reportData.ts`(CLI)**: `--out-patient` と同じフォルダに `finding_texts.json` を常に書く(旗は無い。
  `buildFindingTextsFile()` の JSON 化。`patient_report_data.json` は数だけのまま ― `Finding` に `texts` は
  入れない)
- **`report-pdf/render_front.py`**: 第 3 引数(`finding_texts.json`)を渡すと、1 ページ目の shown の発見ごとに
  3 段(`phase` は無し)、2 ページ目の種類ごとの 3 通りの文の下に §5.3 の固定文、4 ページ目に評価の揺れの注記を
  足す。**渡さなければ今の形(数の文だけ)のまま動く**。3 段を足すと 1 ページ目が 2 ページ以上になり得るため、
  ページ数の検査は「4 ページ固定」から「4 節・節ごとに改ページ・合計 4〜6 ページ」に緩めた(超えたら rc=1)。
  検査(禁止語・数の照合)は固定文も対象(`GLOBAL_ALLOWED_NUMBERS` に固定文の数(30・40)を追加)
- **`lib/pipeline.ts`**: `reportPaths()` に `findingTexts`(`<work>/report/finding_texts.json`)を足した。S7 の
  front 呼び出しは `fs.readText(rp.findingTexts)` で有無を確かめ、あれば第 3 引数として渡す(無ければ既存どおり
  2 引数)。**既存の試験は変えていない**(偽 fs に `rp.findingTexts` を置かなければ、そのまま今までどおりの
  2 引数を試す試験になる)。有る場合の試験を 2 本追加した
- **感想票**(`out/concierge-prep/08-application-kit.md` の C。gitignore): 司令塔が手で直す(この STEP の実装
  担当は触らない。§6.7 の 4)

## 全員に共通の基準値(`baselineTable.ts`。STEP BASE)

`scripts/playtest/baselineTable.ts` は、1 人の段 2 の記録を「その人(`--person`)」、その人を除いた 1 人以上を「基準値の材料(`--pool`)」にして、あらかじめ決めた 24 の枠(docs/STEP_BASE_PLAN_2026-09-21.md §1.1)ごとに、その人の崩れ率が基準値からどれだけ外れているかを出す道具(下見。断定ではない)。

```
npx tsx scripts/playtest/baselineTable.ts --person <pN> --material <段 2 の記録 …>
  --pool <pM>=<記録 …> [--pool <pK>=<…> …] --out <baseline.json>
```

- `--pool` は 1 人の pool を表す。最初のトークンは `<ラベル>=<1 本目の記録のパス>`(空でもよい)、続く(`--` で始まらない)トークンは同じ pool の記録を追加する。複数人を pool に入れるときは `--pool` を人の数だけ繰り返す
- 標準出力に Markdown の表(枠ごとの その人 / 基準値 の崩れ・分母・率、candidate・lower)。`--out` に、名前・手・局面・SFEN を含まない JSON(枠ごとの内訳・pool の人ごとの内訳・GATE_VALUES)を書く。`records/` へは書かない・エンジンは使わない
- 止める(exit 1): `--person`・`--pool` のラベルが `p1`・`p2` の形でない・`--pool` のラベルが `--person` と同じ・`--pool` 同士で同じラベル・記録が無い・referenceNodes がそろわない・error 行がある・同じ記録(name・sha256・kifuId のいずれか)が `--material` と `--pool` の間、または `--pool` 同士で重なる

### 24 の枠と崩れの数え方

- 崩れ・分母・分母から外す理由は `lib/gate.ts` の `collapseOf`(直前 ahead・level → 直後が 1 段以上下がったら崩れ)をそのまま使う。**この道具は新しい閾値・崩れの定義を作らない**
- 軸 A(直前の形勢・2): `standingPair.before` が `ahead`/`level` のときだけ枠に入る。`behind`・未定はどちらの軸の枠にも入れず、`unclassified.A` に数える
- 軸 B(時期・3): `lib/reportData.ts` の `phaseOf`(組の `branchPly` ÷ その局の総手数。1/3 未満が早い、2/3 未満が中、それ以外が遅い。境を含むのは `phaseOf` の実装のまま)をそのまま呼ぶ。**総手数は、この道具では記録の meta には無く、記録の指し手(`lib/failureEvent.ts` の `fullMovesOf`。最も長い `moveHistory`)から取る**(固定棋譜 JSON はこの CLI の入力に無いため使わない)。0 手以下・取れない局は `unclassified.B.subjectGames`/`poolGames`(局の数)と `subjectPairs`/`poolPairs`(組の数)に別に出す
- 軸 C(手の種類・7、重なってよい): `counterfactual.actual.userMoveFacts` を、承認済みの条件式 `lib/conditions/ahead_move_into_own_king_zone_v1.ts` と同じ門(`counterfactual.state === "compared"`)で読む。打つ手(`drop`)・駒を取る手(`capturedRole ≠ null`)・成る手(`promotion`)・玉を動かす手(`kingMove`)・自玉のそばへ動かす手(`toInOwnKingZone`)・相手玉のそばへ動かす手(`toInOpponentKingZone`)。6 つとも偽なら「どれでもない手」。`counterfactual.state` が `compared` でない、または `toInOwnKingZone`/`toInOpponentKingZone` が null な組は、軸 C 全体(7 枠すべて)を判定できないものとして数えず、`unclassified.C` に数える(欄が null な組は「その軸では数えない」という計画の文どおり、7 枠のどれか 1 つだけを判定不能にはしない)
- A×B(6)・優勢×C(6、「どれでもない」は含まない)は、両方の軸が判定できたときだけ枠に入る

### 既知の限界

- **軸 B の総手数は、固定棋譜 JSON の総手数より 1〜2 手少ない局がある**。上の「軸 B」のとおり、この道具は段 2 の記録(`fullMovesOf`)から総手数を取り、`reportData.ts` が使う固定棋譜 JSON の `originalMoves` は読まない。監査の実測(2 人目 20 局): 20 局のうち 14 局で両者が食い違い、839 組のうち 13 組(約 1.5%)で 早い/中/遅い の区分が変わった。したがって、この道具の軸 B・A×B・candidate/lower の判定は、`reportData.ts`(本人向けレポート)の時期の欄とこの分だけ合わないことがある。

### 外れの印(candidate・lower)

枠ごとに、次の 3 条件を**すべて**満たすときだけ `candidate: true`(値はすべて `GATE_VALUES` を読むだけで、ここに新しい数は置かない)。

1. その人の分母 ≥ `minTruePairs` かつ 崩れのある局 ≥ `minGames`
2. `lib/gate.ts` の `rateRatioMet`/`rateDiffMet`(G-2 と同じ整数の式)で、その人の率が基準値の率より 比 ≥ `minRateRatio`・差 ≥ `minRateDiffPoints` ポイント高い
3. pool の人ごとの率(分母が 0 の人はこの比べから除く。比べる相手が 1 人もいなければ条件 3 は満たしたものとして扱う)と比べて、その人の率がどの人よりも真に高い

`lower`(その人のほうが低い)は同じ 3 条件を向きだけ逆にする: 条件 2 は `rateRatioMet`/`rateDiffMet` の引数を入れ替えて呼ぶ(基準値の率 ÷ その人の率)、条件 3 は「pool のどの人よりも真に低い」。**その人の崩れが 0 のときの比の扱いは `rateRatioMet`/`rateDiffMet` の G-2 と同じ特別扱いをそのまま使う**(偽の側の崩れが 0 なら、真の側の崩れ ≥ 1 で比の条件を満たしたことにする。`lower` では「真の側」が基準値になるので、基準値の崩れが 1 以上あれば、その人の崩れが 0 でも比の条件を満たす)。満たさなかった条件は `reasonsCandidateNotMet`/`reasonsLowerNotMet` に理由の記号で出す(`subjectDenominatorBelowMin`・`subjectGamesWithCollapseBelowMin`・`ratioNotMet`・`diffNotMet`・`poolMemberEqualOrHigher`/`poolMemberEqualOrLower`)。

候補はここでは出すだけで、本人向けの文にする前には docs/STEP_BASE_PLAN_2026-09-21.md §4 の確かめ(同じ人の次の棋譜で再現するか)を通す。

### whatif(重要な局面の分かれ道)の率を足す(`--whatif-material`・`--whatif-pool`。STEP WHATIF 作業 3)

`whatif.ts`(下記)の出力(jsonl)を材料に、5 つの率(第 1 候補と同じ・上位 5 つの中・fork・narrowHeld・chanceHeld。分母は `positionsRead` の合計)+ 攻めの側に合法手が無かった場面の率(分母は `scenesRead` の合計)の 6 行を、Markdown の表の下・`--out` の JSON の `whatif` に足す(docs/STEP_WHATIF_PLAN_2026-09-22.md §8.1-2)。どちらも任意で、**渡さなければ出力は 1 バイトも変わらない**(`--material`・`--pool` の 24 枠の集計・Markdown・JSON はこの機能を足す前と同じ)。

```
npx tsx scripts/playtest/baselineTable.ts --person <pN> --material <段 2 の記録 …> --pool <pM>=<記録 …> …
  --whatif-material <whatif.jsonl …> --whatif-pool <pM>=<whatif.jsonl …> [--whatif-pool <pK>=<…> …] --out <baseline.json>
```

- `--whatif-material`・`--whatif-pool` は片方だけでは受け付けない(exit 1。行を組み立てられないため)。`--whatif-pool` の書き方は `--pool` と同じ(`<ラベル>=<1 本目のファイル>` + 続くファイル)
- **candidate/lower の判定は付けない**(v1)。崩れ率の 3 条件(§8.1-2 参照)とは意味が違う新しい閾値を決めることになるため。出すのは、その人の率・pool 合計の率・**pool の人ごとの率の最小〜最大**だけ
- 止める(exit 1): `--whatif-pool` のラベルの集合が `--pool` のラベルの集合と一致しない(片方にしか無いラベルがある)・記録の最後の行が `summary` でない・`values`(meta 行の `WHATIF_VALUES` の写し)が記録の間でそろわない・同じ記録(name・sha256・kifuId のいずれか)が `--whatif-material` と `--whatif-pool` の間、または `--whatif-pool` 同士で重なる
- 純粋関数は `lib/whatifBaseline.ts`(`whatifInputProblems`・`whatifRateRowsOf`・`renderWhatifRateMarkdown`)。`lib/baselineTable.ts`(24 枠の集計)は変えていない

## 重要な局面の分かれ道を測る(`whatif.ts`。STEP WHATIF 作業 1)

`scripts/playtest/whatif.ts` は、docs/STEP_WHATIF_PLAN_2026-09-22.md の**測る段だけ**を行う道具(見せる段(PDF・Web、計画 §2.3)は別の作業)。固定棋譜(`kifu-import-check.ts --fixed` の JSON)だけを読み、段 2 の記録は読まない。

```
npx tsx scripts/playtest/whatif.ts --kifu <固定棋譜 JSON> --out <whatif.jsonl>
  [--nodes <N>] [--multipv <K>] [--threads <N>] [--side-version 1|2]
```

- エンジン(`resolveEnginePath()` が解決する実行ファイル)を実際に起動する。**1 巡目**(本人の手番の局面ごとに候補 K 個を MultiPV で読む)は replay.ts・rescreen.ts と同じ `LowPriorityEngine`(`PrioritizedEngine.asLowPriority()`)を使う。**2 巡目**(下記)は素の `UsiEngine` を直に使う
- 本人の手番の局面(そろえた記録は先手番。`lib/whatif.ts` の `WHATIF_VALUES.startPly` = 17 手目から)だけを MultiPV で読む。**王手中の局面も読む・終局の局面は読まない**(`lib/whatif.ts` の `evaluableTurns`)
- 値(`WHATIF_VALUES`: `multiPv`・`nodes`・`startPly`・`minLossCp`・`narrowGapCp`・`riseCp`・`pvMoves`・`sideZoneRadius`・`sideNodes`・`sideVersion`・`hitsDefenderRadius`・`attackZoneRadius`)は `lib/whatif.ts` に 1 か所だけ置く**判断的知識の仮置き**(2026-09-22、計画 §2.1・§2.2・§2.5・§9.3)。`--nodes`・`--multipv`・`--threads` はハーネスの探索条件(候補 K 個の読み)だけを、`--side-version` は攻めの側の決め方だけを上書きする(既定は `sideVersion: 2`。`startPly`・`sideZoneRadius` 等ほかの閾値は CLI からは変えない)
- 候補・実戦の手に付ける印(`oppKingZone`・`ownKingZone`・`givesCheck`・`kingMove`・`captures`・`hitsOppKingZonePiece`・`oppKingZone3`)は、**行き先だけ**で決める。王手か・玉を動かす手かは `lib/moveFacts.ts` の `moveFactsOf`(D2.6 で確定済み)・`isInCheck` をそのまま呼ぶ(二重に実装しない)。**玉のそば**(`oppKingZone`・`ownKingZone`)は、この段だけの決め方 ― 玉から `sideZoneRadius`(既定 2)マス以内(縦横斜めの大きいほう、shogiops の `squareDist`)。`moveFactsOf`・`POSITION_FACTS_RULES`(Gate・基準値(`baselineTable.ts` の軸 C)が使う「玉の升 + 8 近傍 = 1 マス以内」の決め方)は変えない ― **この段と Gate・基準値では「玉のそば」の広さが違う**(meta 行の `kingZoneRadius` 参照)。**守りの側**(v1・v2 とも同じ)= `ownKingZone`(玉自身の手を除く)または `kingMove`。**攻めの側**は `sideVersion` で切り替える: v1 = `oppKingZone` または `givesCheck`、**v2(既定)** = v1 ∪ `captures`(相手の駒を取る)∪ `hitsOppKingZonePiece`(動かした駒が、相手玉から `hitsDefenderRadius`(既定 2)マス以内の相手の駒(玉以外)に当たる。shogiops の `attacks(piece, to, occupied)` で数える)∪ `oppKingZone3`(行き先が相手玉から `attackZoneRadius`(既定 3)マス以内)。両方に当たる手は `both`
- **なぜ広げたか(計画 §2.5、2026-09-22)**: 候補 K 個の中から攻め・守りの最上位を拾うやり方は、8 マスの決め方では両方が見つかる局面が実測 4/85(5%)しか無く、成り立たないと分かった。そこで、場面の局面だけ・合法手を全部使い、側ごとに絞って読み直す形(下記 2 巡目)に変え、広さも 2 マスへ広げた
- **攻めの側の決め方 v2(STEP WHATIF 作業 4、計画 §9.3、2026-09-22)**: 2 人目の本人から「玉を攻める前の段階の手(守りの駒を剥がす・陣形を崩す)も攻めだと思う」という感想が届き、24 局の下見で「第 1 候補の 53% が v1 では『なし』に分類される」ことを確かめた。v2 = v1 ∪ 取る ∪ 守り駒に当てる ∪ 3 マス以内(「相手の駒のどれかに当たる」「相手陣へ動く」は序盤の駒組みの手まで大量に拾うため採らなかった ― 計画 §9.3)。v2 が既定。`sideVersion: 1` を渡せば v1 と同じ結果になる
- 拾う場面 3 種類(`fork`・`narrowHeld`・`chanceHeld`、計画 §2.2)と、1 局に 1 つのいちばん大きな分かれ道(`biggestFork`、§2.4-1)は `lib/whatif.ts` の `whatifPositionOf`・`whatifGameSummaryOf` が組む(エンジンは呼ばない純粋関数。試験は `lib/whatif.test.ts`)
- **2 巡目(側ごとの読み。計画 §2.5)**: 1 巡目がすべて終わり `biggestFork` が決まってから、場面(`fork`・`narrowHeld`・`chanceHeld` のどれか、または `biggestFork`)の局面だけ(`lib/whatif.ts` の `sceneReadPlies`)、合法手をすべて出して攻め・守りの側に分け(`sideMovesOf`。候補 K 個に付ける印と同じ決め方)、**側ごとにその側の手だけを** `go nodes <sideNodes> searchmoves <その側の手…>`(MultiPV 1)で読む(`whatifSceneOf`)。**`LowPriorityEngine`(apps/server が公開する型)には searchmoves を渡す口が無いため、apps/ は変えず、CLI 側で素の `UsiEngine`(`send`・`waitForLine`)を直に使う**(lib/checkBaseline.ts と同じ「ハーネスの観測として足す」流儀)。その側に合法手が無ければ `noLegalMove`(呼ばない)。`sideGapCp` は両方 `found`・cp のときだけ
- 出力(JSONL): 1 行目 `{"kind":"meta", kifuId, startedAt, gitHead, dirty, values, threads, kingZoneRadius: { thisStage, gateAndBaseline }, mirrored, plyOffset, startSfen}`(**名前・`/Users/` を含む絶対パスは書かない** ― `enginePath` はここに含めない。`mirrored`・`plyOffset`・`startSfen` は `lib/sideAlignment.ts` の `sideMetaFields`(`replay.ts` の段の meta と同じ形)。`startSfen` は `mirrored` のときだけ持つ)、局面ごとに `{"kind":"position", ...}`(`WhatifPosition` + `displayPly`。候補 K 個・実戦の手の順位・`loss`・拾った場面)、場面の局面だけ `{"kind":"scene", ...}`(`WhatifScene` + `displayPly`。攻め・守りそれぞれの `WhatifSideRead`(`found`/`noLegalMove`/`notMeasured`)と `sideGapCp`)、最後に `{"kind":"summary", ...}`(`WhatifGameSummary` + `sceneReads`(`WhatifSceneReadSummary`: 場面の数・側ごとに合法手が無かった数・両方 `found` の数)+ `timingMs: { pass1, pass2 }`。`biggestFork` も `displayPly` を持つ)
- **`ply` は畳んだ後の記録の手数。人に見せる手数は `displayPly`(= `ply` + `plyOffset`)** ― mirrored の局(元の棋譜が後手番だった局。`plyOffset` = 1)では、この段の `ply` は元の棋譜の手数と 1 ずれる。`position`・`scene` の行と `summary.biggestFork` はどれも `lib/whatif.ts` の `withDisplayPly`(`lib/reportData.ts` の `displayPlyOf` をそのまま呼ぶ。二重に実装しない)で `displayPly` を持つ
- 見せる段(PDF・Web)はここでは作らない。冊子に書ける文言の確定・LLM の言い換えも、この段の範囲外

### 既知の限界(`whatif.ts`)

- **`biggestFork` が同点のときは、早い手数(`ply` が小さいほう)のほうを採る**(`whatifGameSummaryOf` の比べは厳密な `>` のため、後から出た同点の局面には入れ替わらない)
- **`--dry-run` のプレビューに whatif の段は出ない**(`pipeline.ts` の `--dry-run` は S1〜S4 までのプレビューのまま。上の「S5〜S7」の節と同じ既知の限界)

### `pipeline.ts` の `--whatif`(任意の段)

`pipeline.ts` に `--whatif` を付けると、**`--until` の進み具合とは関係なく**、diagnose の段の後に局ごとに `whatif.ts` を回し、`<work>/<person>/whatif-v2/<id>.jsonl`(既定。攻めの側の決め方 v2)を書く(`--parallel` に従う。済みの判定は他の段と同じ流儀 ― 最後の行が `summary` であること)。fixed 棋譜が無い局は、`whatif.ts` を呼ばずに失敗として記録する。所要は `timing.jsonl` に `stage: "whatif"` つきで残る(ほかの段の行には `stage` の欄自体が無い)。`--whatif` を**付けない**実行は、道具の呼び出し・出力・`timing.jsonl` の形が一切変わらない(試験は `lib/pipelineWhatif.test.ts`)。

- **`--side-version 1`(STEP WHATIF 作業 4、計画 §9.3)を付けると、v1(従来の決め方)で読み、`<work>/<person>/whatif/<id>.jsonl`(v1 のフォルダ名は変えない)に書く。**`whatif.ts` へも `--side-version 1` を渡す。`--until pdf` かつ `--whatif` のとき、付録 2 の材料もこの `--side-version` と同じフォルダを読む(v1/v2 を混ぜない)

```
npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir> --whatif [--side-version 1]
```

## 重要な局面の分かれ道を見せる(`whatifReport.ts`・`report-pdf/render_whatif.py`。STEP WHATIF 作業 2)

`whatif.ts`(測る段、上記)の出力を、付録 2(分かれ道)の PDF にする**見せる段**。docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3。

- **`scripts/playtest/lib/whatifReport.ts`**(純粋関数。試験は `lib/whatifReport.test.ts`): 局ごとの `whatif.jsonl` と `patient_report_data.json` の games の欄(id・side・total・result・ending・scores・plies)から、付録 2 の材料 `whatif_report_data.json` の中身を組む。
  - **1 ページ目の集計**(§7.3): 読んだ局面・第 1 候補と同じ・上位 5 つの数、fork/narrowHeld/chanceHeld の延べ数(`scenes.rawTotal`)と重なりを除いた数(`scenes.distinctTotal`。局ごとに fork ∪ narrowHeld ∪ chanceHeld の手数の集合を取り、重なりを除いてから局をまたいで足す)、攻め・守り両方の手が出た場面の数(`sideCompare`)、負けた局のうち narrowHeld があった局の数(`lossesWithNarrowHeld`)。**消費時間の表はここでは作らない**(§7.3 末尾。入力に消費時間が無い。まとめの冊子の側で司令塔が別に扱う)
  - **局ごとの代表の場面 1 つ**(`pickRepresentativePly`。4 つの分岐): 負けた局は `summary.biggestFork` の局面。勝った局は narrowHeld のうち `topGapCp` が最大の局面(同点は早い手数)。無ければ chanceHeld の最初(最も早い手数)。それも無ければ `biggestFork`(fork の最大)。それも無ければ `null`(「載せる局面なし」)
  - **場面の材料**(`buildRepresentative`): displayPly・種類・候補 3 つ(手・評価・読み筋 5 手)・実戦の手と順位・attack/defense の読み(`scene`)・`sideGapCp`・「第 1 候補(実戦が第 1 候補なら第 2 候補)を 5 手進めた局面」(`afterCandidate`。apps/server の `applyMove` で実際に SFEN へ適用する ― 将棋のルールを python 側で二重に実装しない)
  - **手は USI のまま出す**(日本語表記・盤面図は python 側の役目)。**mirrored(本人が後手)の局の sfen・USI は、測る段がそろえた解析用の向き(180 度回した、本人 = 先手の向き)のまま**(回し直さない。既出の `WhatifPositionRow`/`WhatifSceneRow` の `sfen`・`move`・`pv` は全部この向き)
  - `WhatifReportData.values`(`sideZoneRadius`・`startPly`・`minLossCp`・`narrowGapCp`・`riseCp`・`sideVersion`・`hitsDefenderRadius`・`attackZoneRadius`(STEP WHATIF 作業 4)。全局で同じはずの判断的知識の値。違えば止める)を出力に含める ― 冊子の文に出す数は python 側もここ経由でデータから読み、固定で書かない
  - **名前・`/Users/` を含む絶対パスは出力へ含めない**
- **`scripts/playtest/whatifReport.ts`**(CLI。上記の純粋関数への配線だけ): `--whatif <whatif.jsonl …> --patient <patient_report_data.json> --out <whatif_report_data.json>`。各 `whatif.jsonl` の先頭行(meta)の `kifuId` で `patient_report_data.json` の games と突き合わせる。
- **`scripts/playtest/report-pdf/render_whatif.py`**(新規ファイル。**既存の 6 本(`_head.py`・`_util.py`・`_mid.py`・`_app_head.py`・`_app.py`・`_tail.py`)は変えない**): `whatif_report_data.json` と `sfens.json`(`REPORT_DATA_DIR` から読む。既存の `_head.py`・`_util.py` と同じ流儀)から、付録 2 の PDF を作る。1 ページ目(集計)+ 1 局 1 ページ(代表の場面が無い局は表にだけ出し、ページは作らない)。
  - **書体・`REPORT_DATA_DIR`・盤面図(`Board`)・手の表記の考え方は、既存の `_head.py`・`_util.py` の流儀を再利用する**(このファイルの中で新しく書き直したもの。中身を import はしない ― `_head.py`・`_util.py` は `cat` で連結される前提の断片ファイルのため)
  - **mirrored(本人が後手)の局の手の表記**(依頼の指示: 既存の付録 1(本編)・`reportData.ts` と同じ流儀に合わせる。回し方を新しく決めない): 盤面図・実戦の手は `sfens.json`(本人が指した実際の向き)を使う。エンジンの候補・読み筋・攻め/守りの手(実戦では指されていない、解析用の向きのままの手)は、`rotate_usi`(`lib/usiRotation.ts` の `rotateUsiMove` と同じマスの変換を python で書き直したもの)で本人が指した向きへ戻してから、`sfens.json` の実際の局面へ適用する(このファイル内の `apply_move`・`serialize_sfen`)
  - **数の照合**: 文に出す数は、その場面で使ってよい数の集合(局の事実・§2.1 の値・「第 1 候補」等の方式そのものの語彙数)に無ければ `sys.exit(1)`。禁止語(`BANNED`)も同じく確かめる
  - **人間の追加指示(2026-09-22)**: 各局のページで、5 手進めた局面の盤面の上に「エンジンの読み筋で 5 手進めた局面(実戦ではありません)」、実戦の局面の盤面の上に「実戦の局面(指す前)」の帯を置く。1 ページ目の攻め/守りの注記の末尾に「(決め方 v1: 玉から {sideZoneRadius} マス以内)」を足す(値は `values.sideZoneRadius` から。固定で書かない)。分かれ道 × その手にかけた時間の表は、この付録には入れない(まとめの冊子の側で司令塔が扱う)
  - **攻めの側の決め方 v1/v2 の切り替え(STEP WHATIF 作業 4、計画 §9.3)**: 注記の文は `values.sideVersion` で切り替える(v1 = 上記の文、v2(既定)= 「行き先が相手の玉から {attackZoneRadius} マス以内・王手・取る・相手の玉のそばの駒に当てる、のどれか」)。値は `values.attackZoneRadius`・`values.hitsDefenderRadius` から(固定で書かない)。古い `whatif_report_data.json`(`sideVersion` を持たない)は v1 として扱う
  - 使い方: `REPORT_DATA_DIR=<sfens.json のあるフォルダ> python3 -X utf8 render_whatif.py <whatif_report_data.json> <出力 PDF>`
  - **この python の道具は vitest の対象外**(`report-pdf/` 全体と同じ。既存の README の「既知の限界」参照)。守りは、合成データ(先手の負け・後手の勝ち・載せる局面なし)と実データでの実行時の確かめ(rc・禁止語・数の照合・実測の件数)だけ

### `pipeline.ts` の `--whatif` かつ `--until pdf`(本編の後に付録 2)

`--whatif` を付けて `--until pdf` まで実行すると、本編の PDF(`main.pdf`)の後に、`<work>/report/whatif_report_data.json` と `<work>/report/whatif.pdf` を作る(`whatif-report-data` → `report-pdf-render-whatif` → `report-pdf-check-fonts` の順)。

- **材料**: このお客さんの局のうち、段 2 まで済んだ局(`successGames`)それぞれの `<work>/<person>/whatif-v2/<id>.jsonl`(既定。`--side-version 1` なら `<work>/<person>/whatif/<id>.jsonl`。**全部揃っていなければ**、道具を呼ばずに失敗として記録する ― 1 局でも `--whatif` の記録が無ければ付録は作らない)
- **済みの判定**: `whatif_report_data.json` は空でなければ飛ばす。`whatif.pdf` は `whatif_report_data.json` より新しければ(mtime)飛ばす(本編の `pdfDone` と同じ考え方。依存は `whatif_report_data.json` だけ)
- **本編 PDF が無ければ**(`main.pdf` が無い・pdf 段自体が失敗している)、付録 2 の道具を一切呼ばずに失敗として記録する
- `--whatif` を**付けない**実行、または `--until` が `pdf` より前の実行は、この段に一切入らない(道具の呼び出し・出力が 1 バイトも変わらない。試験は `lib/pipelineWhatifReport.test.ts`)

```
npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir> \
  --name <表示名> --title <タイトル> --today <YYYY-MM-DD> --until pdf --whatif
```

## 「読みの間違い」を人を介さずに分解する(`read.ts`。STEP READ)

`scripts/playtest/read.ts` は、docs/STEP_READ_PLAN_2026-09-22.md の**測る段だけ**を行う道具(見せる段は今回作らない。計画 5.)。`whatif.ts`(STEP WHATIF 作業 4。攻めの側の決め方 v2)の出力(jsonl)と、同じ局の固定棋譜 JSON だけを読む。段 2 の記録・`pipeline.ts` への配線はしない(**この段だけ CLI 単体**。ほかの段のような `pipeline.ts` の任意の段は今回作っていない)。

```
npx tsx scripts/playtest/read.ts --whatif <whatif-v2.jsonl> --kifu <固定棋譜 JSON> --out <read.jsonl>
  [--threads <N>]
```

- **対象は `scenes.fork` が true の position 行(分かれ道)だけ**(計画「作るもの」冒頭)。`whatif` の meta 行の `kifuId` と `--kifu` の `id` が一致しなければ止める(exit 1)
- 値(`READ_VALUES`: `nodeLadder`・`minLossCp`・`pieceValues`)は `lib/read.ts` に 1 か所だけ置く**判断的知識の仮置き**(計画「作るもの」1.〜3.)。`minLossCp` は `WHATIF_VALUES.minLossCp` と同じ値を参照する(値の重複を避ける)。CLI からは変えない(`--threads` だけを受け付ける)
- **2.1 浅い探索でも分かる崩れか**: 分かれ道の局面ごとに、`nodeLadder`(2 千・1 万・5 万・20 万・100 万)の各段で (a) `go nodes N`(MultiPV 1、searchmoves 無し)= 第 1 候補の評価と、(b) `go nodes N searchmoves <実戦の手>` = 実戦の手だけを読ませた評価を読み、差(`lib/whatif.ts` の `evalValueOf` で mate を数直線に乗せてから引く。二重に実装しない)が `minLossCp` 以上になる最小の段を `firstVisibleNodes` に記録(どの段でも出なければ `null`)。あわせて、いちばん深い段(100 万ノード)の (b) の読み筋の 2 手目(相手の返し)が、固定棋譍から読んだ次の相手の実際の手と同じかを `opponentReplyMatchesPv` に記録(比べられなければ `null`)
- **2.2 手の性質**: 第 1 候補・実戦の手それぞれに `drop`(打つ)・`capture`(取る)・`retreat`(自陣の側へ動く。本人 = 先手にそろえた記録なので、段が大きくなる方向。打つ手は false)・`declinesPromotion`(成れるのに成らない)・`sacrifice`(捨て駒。動かした先が相手の利きにあり、取り返しの有無を問わず、その升での駒の損得(取った駒の価値 − 動かした駒の価値、成っていれば成った後の価値)が負)・`kingMove`・`givesCheck` を付ける(印は行き先と駒だけで決まる。`kingMove`・`givesCheck` は既存の `lib/moveFacts.ts` の `moveFactsOf`・`apps/server` の `isInCheck` をそのまま呼ぶ)
- **2.3 見た目**: `materialLookOf`(指した直後の見た目の損得 = 取った駒の価値 −(動かした先が相手の利きにあるなら動かした駒の価値、なければ 0))を第 1 候補・実戦の手それぞれについて記録
- **エンジンの呼び方**: `whatif.ts` の 2 巡目(側ごとの読み)と同じく、素の `UsiEngine` を直に使う(`LowPriorityEngine` には searchmoves を渡す口が無いため。lib/checkBaseline.ts と同じ「ハーネスの観測として足す」流儀)
- 出力(JSONL): 1 行目 `{"kind":"meta", kifuId, startedAt, gitHead, dirty, values, threads}`(**名前・`/Users/` を含む絶対パスは書かない**。`enginePath` はここに含めない)、分かれ道ごとに `{"kind":"position", ply, displayPly, sfen, actualMove, top1Move, ladder, firstVisibleNodes, opponentReplyMatchesPv, top1Tags, actualTags, top1MaterialLook, actualMaterialLook}`、最後に `{"kind":"summary", forkPositionsRead, firstVisibleNodesBuckets, opponentReplyMatchesPv, tagCrossTable, materialLook, skippedForkCount, timingMs}`(**summary には手・評価値・SFEN を書かない**。局面ごとの行には書いてよい)
  - `firstVisibleNodesBuckets`: `nodeLadder` の各段(キーはノード数の文字列)+ `"none"`(どの段でも出なかった件数)
  - `opponentReplyMatchesPv`(summary 側): `{ matched, measured }`(`measured` は比べられた件数。対局の最後の手だった等で比べられなければ、その局面は数えない)
  - `tagCrossTable`: 第 1 候補の種類(7)× 実戦の手の種類(7)の件数の表(`READ_TAG_NAMES` の順。複数の印に当たってよいので、1 局面が複数のセルへ数えられる ― 独立した集計であり、確率の合計が 100% になる分割ではない)
  - `materialLook`(summary 側): `actualPositiveCount`(実戦の手が駒得に見える局面の数。対象は分かれ道 = 評価が下がった局面なので、これがそのまま「駒得に見える手を選んで下がった」件数になる)・`top1NegativeCount`(第 1 候補が駒損に見える局面の数)・`bothCount`(両方に当たる局面の数)

### 既知の限界(`read.ts`)

- **候補が 0 件の分かれ道(理論上)は、測れないので `skippedForkCount` に数えるだけで、`position` の行には出さない**(`whatif.ts` の既知の限界「候補が 0 件の局面は fork 扱いだが biggestFork の対象外」と同じ考え方)。24 局の実行ではこの状態は 1 件も無かった
- **`scenes.fork` の判定自体は `whatif.ts`(MultiPV 5)のもの**であり、`read.ts` は「実戦の手が候補 5 つに入らなかった」ことを理由に fork とされた局面もそのまま読む。この段の node ラダーは「第 1 候補」対「実戦の手」だけを比べる(MultiPV 1)ので、`firstVisibleNodes` が `null`(100 万ノードでも 600 以上の差が付かない)になる分かれ道がありうる ― これは fork の定義の違いによるもので、道具の不具合ではない
- **`pipeline.ts` への配線はしない**(計画「作るもの」5.)。`--dry-run` のプレビューにも出ない(そもそも配線が無い)
- **見せる段(数の一覧を文にする・PDF・Web)は無い**。24 局の合計は司令塔がまとめに手で入れる(計画§3)

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```

## 不変条件のテスト

```
npx vitest run scripts/playtest
```
