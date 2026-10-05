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
  - `phaseSpent`: 序盤・中盤・終盤(既存の `phaseOf`)ごとの本人の消費の合計を局ごとに出し、「`timeUpLoss`(本人が時間で負けた局。`ending.kind === "timeUp"` かつ本人の結果が「負け」。相手が切れ負けた勝ちの局は入らない)」と「`otherGames`(それ以外)」で中央値。**ANSWER-M1(`docs/STEP_ANSWER_PLAN_2026-09-23.md` §7.1)**: `perGame`(局ごとの `{ gameNo, total, midMoves, midSec, midSecPerMove, timeUpLoss }`。`midSecPerMove` は `midSec / midMoves`、`midMoves` が 0 なら `null`)と `midOver`(`{ thresholdSec: TIME_VALUES.quickSec(4), games, over, overAndTimeUpLoss }`。`games` は `perGame` のうち `midSecPerMove` が取れた局の数、`over` はそのうち閾値を超えた局の数、`overAndTimeUpLoss` はそのうち本人が時間で負けた局の数)
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
  `EVAL_JITTER_NOTE`(評価の揺れの注記)、`FORBIDDEN_FINDING_TEXT_WORDS`(TS 側の固定文だけを見張る試験用の一覧。python 側の禁止語は 2026-09-25 の人間の決定で機械の禁止語は無し(凍結の例外 14 件目) ― この一覧は対象外で 20 語のまま。§5.1 の 18 語 + 「すべき」
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

## 伝わる形(STEP TIME 作業 4。`docs/STEP_TIME_PLAN_2026-09-22.md` §6.10)

判定・数・設計思想は変えず、`front.pdf` を読んで分かる順と言葉にする。**文の正本は docs §5.5。コードは写しであり、
試験が文字列一致を確かめる**(`lib/findingTexts.test.ts`)。

- **`lib/findingTexts.ts`**: `FindingTextSet` に `oneLine`(1 通りの種類 `timeSpent`・`aheadLoss`・`none`)・
  `oneLineVariants`(3 通りの種類 `timeUpLoss`・`phase`。docs のプレースホルダ `{序盤|中盤|終盤}`・`{X}と{Y}` を
  含んだままの文字列で持ち、埋め込みは `reportData.ts` の役目)を足した。`READING_GUIDE`(読み方の枠)・
  `TRYABLE_SUMMARY_HEADING`・`TRYABLE_SUMMARY_TAIL`(試せることのまとめ)・`GLOSSARY`(言葉の意味、4 項目)も
  新規。`buildFindingTextsFile()` に `readingGuide`・`tryableSummaryHeading`・`tryableSummaryTail`・`glossary`
  を足した(`findings[].oneLine` は個々の発見ごとに解決済みの値を `Finding.oneLine` が持つので、ここには含めない)
- **`lib/findingTexts.test.ts`**: §5.5 の「ひとことで」(5 つの箇条書き行の中の「」をすべて `matchAll` で出現順に
  取り出す)・「読み方」・「試せることのまとめ」(見出し・末尾の文)・「言葉の意味」(4 項目)の一致試験を足した。
  禁止語 0 の対象にも新しい文をすべて足した
- **`lib/reportData.ts`**: `Finding` に `oneLine: string` を足し、5 つの発見の作る関数すべてで設定する。
  `timeUpLossOneLine(n, m)`(m = n / 0 < m < n / m = 0 の順で判定。`m === n` は `null === null` も真になるので、
  `time.available: false` のとき(`shown: false` で画面に出ない)は保守的に `mEqualsN` 側へ落ちる)・
  `phaseOneLine(fell, early, mid, late)`(`fell === 0` → 崩れ 0、最大の段が 1 つ → その段名を `{序盤|中盤|終盤}`
  へ埋め込み、3 つ同数 → `{X}と{Y}で` を `tieAllPhases`(「序盤と中盤と終盤で」)へ丸ごと置き換え、2 つ同数 →
  `{X}と{Y}` を実際の 2 つの段名へ置き換え)。`FINDING_NUMBER_LABELS.timeSpent` の名を「組」→「手」に直した
  (§5.5「言い換え」。お客さん向けの文では「組」を使わない)
- **`report-pdf/render_front.py`**: 1 ページ目の冒頭に読み方の枠(`fdata["readingGuide"]`)、発見ごとに
  「ひとことで」(`findings[].oneLine`。太字、数の文の上)、末尾に「次の 20 局までに試せること(まとめ)」
  (shown の発見の `tryable` を出た順に番号で再掲 + 末尾の 1 文。`tryable` が 1 つも無ければ何も出さない ―
  実装担当の判断)。3 ページ目の表の名を「(崩れた手 / 手)」に。4 ページ目の頭に「言葉の意味」(`fdata["glossary"]`、
  4 項目)。**すべて `fdata`(`finding_texts.json`)があるときだけ足す**(無ければ今の形のまま)。検査に
  「お客さん向けの文に『組』が残っていれば rc=1」を足した(`emit()` に組み込み、テンプレの文・`finding_texts.json`
  経由の文の両方が対象)。`GLOBAL_ALLOWED_NUMBERS` に `600`(「言葉の意味」の「分かれ道」の定義。
  `lib/whatif.ts` の `WHATIF_VALUES.minLossCp` と同じ値)を追加
- 実測(3 分 14 局・10 分 10 局・3 分 20 局の 3 組。`out/tatsunami3`・`out/tatsunami-long`・`out/tatsunami20`、
  gitignore): `reportData.ts` の CLI を直接呼び(エンジン・pipeline は回さない)、`patient_report_data.json`・
  `finding_texts.json` を作り直し、`render_front.py` で `front.pdf` を作り直した。ページ数は 5・4・5、「組」は
  3 組とも 0 件、`main.pdf`(触っていない)は無変更のまま

## 文だけの直し(STEP TIME 作業 4b。`docs/STEP_TIME_PLAN_2026-09-22.md` §6.12)

判定・数は変えない。§5.2 の「試せること」3 本(T1・T4・T3)を、まとめ(1 ページ目末尾)で単独でも読める文に直し
(「(c) が残るか」のような裸の参照をやめて内容を書き下す)、「同じ物差し」→「同じ数え方」に揃えた。§5.5 の
読み方を 5 段に(「次の 20 局で見分けがつくこと」の説明を足し、「4 ページ目」→「最後のページ」)、`phase` の
数の文の下に付ける 1 文(`PHASE_NOTE`)を新設、言葉の意味に「秒読み」を足して 5 項目にした。

- **`lib/findingTexts.ts`**: `FINDING_TEXTS.timeSpent/aheadLoss/none` の `tryable` を docs §5.2 の新しい文字列に
  更新。`READING_GUIDE` を 5 段の文字列に更新。`PHASE_NOTE`(新規 export)。`GLOSSARY` に 5 項目目「秒読み」を追加
  (4 項目 → 5 項目)。`FindingTextsFile`・`buildFindingTextsFile()` に `phaseNote` を足した
- **`lib/findingTexts.test.ts`**: 既存の docs 一致試験(tryable・READING_GUIDE・GLOSSARY)がそのまま新しい文字列を
  検知する(切り出しの正規表現は変えていないが、`READING_GUIDE` の行末に docs 側の注記が付いたため、抽出の
  正規表現だけ「」の直後に `(` が続く箇所までを取るように直した)。`PHASE_NOTE` の一致試験を新規に足した
- **`report-pdf/render_front.py`**: `append_considerations_block` に、`phase`(considerations が null)のときだけ
  `fdata["phaseNote"]` を数の文の下に足す分岐を追加。4 ページ目の「言葉の意味」は `fdata["glossary"]` をそのまま
  並べるだけなのでコード側は無変更(5 項目になるのはデータ側の変更のみ)。検査を追加:
  「次の 20 局までに試せること(まとめ)」の各項目に `(a)`/`(b)`/`(c)` の裸の参照、または「同じ物差し」が残って
  いれば rc=1(`check_summary_item()`。`_BARE_LETTER_REF`・`_SAME_YARDSTICK`)
- 実測(3 分 14 局・10 分 10 局・3 分 20 局の 3 組。作業 3・4 と同じ `out/tatsunami3`・`out/tatsunami-long`・
  `out/tatsunami20`、gitignore): `reportData.ts` の CLI を直接呼び直して `finding_texts.json`・`front.pdf` を作り
  直した。まとめの各項目に `(a)`〜`(c)` の裸の参照なし・「同じ物差し」0 件・「組」0 件、`phase` の下に 1 文、
  言葉の意味 5 項目、ページ数 4〜6、`main.pdf`(触っていない)は無変更のまま

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

## 分かれ道の「タイプ」を数える(`type.ts`。STEP TYPE)

`scripts/playtest/type.ts` は、docs/STEP_TYPE_PLAN_2026-09-23.md の**測る段だけ**を行う道具(冊子に出す形は別の作業)。`whatif.ts`(STEP WHATIF 作業 4。攻めの側の決め方 v2)・`read.ts`(STEP READ)の出力(jsonl)と、同じ局の固定棋譜 JSON の `moveSeconds` だけを読む。**エンジンは呼ばない**。

タイプは **大きさ(A)× 側(B)× 性質(C)** の 3 軸の組(印の組み合わせ。名前は付けない)で定義する(計画 §3)。対象は `whatif.ts` の `scenes.fork` が true の分かれ道(`read.ts` と同じ集合)。

- **軸 A(大きさ)**: `read.ts` の `firstVisibleNodes` から `none`(null = 100 万ノードでも 600 未満)/ `shallow`(2000・10000)/ `deep`(50000 以上)。`TYPE_VALUES.nodeShallowMaxNodes`(10000)・`nodeDeepMinNodes`(50000)の間(計画が定義していない区間)に落ちる値は、現在の `READ_VALUES.nodeLadder` では起こらないが、黙って寄せず例外にする(計画にない判断: 保守的側)
- **軸 B(側)**: `whatif.ts` の第 1 候補(`candidates[0].side`)と実戦の手(`actualSide`)の side(`attack`/`defense`/`both`/`none`)から、`top1AttackActualDefense`(第 1 候補が攻め・実戦が守り)/ `top1DefenseActualAttack`(その逆)/ `same`(同じ側)/ `eitherNone`(どちらかが `none`)。**「両方(`both`)」の扱いは計画に無いため、司令塔の指示どおり「集合が交わるか」で判定する**(計画にない判断): `both` を「攻めでも守りでもある」集合として開き、第 1 候補・実戦の side の集合が 1 つでも重なれば `same`(片方が `both` でも、もう片方の側と重なれば同じ側)。重ならないときだけ `top1AttackActualDefense`/`top1DefenseActualAttack` になる
- **軸 C(性質)**: `read.ts` の実戦の手の印(`actualTags`)と `actualMaterialLook` から、優先順 `retreat`(自陣の側へ動く)→ `materialGain`(`actualMaterialLook > 0` かつ `sacrifice` でない駒得の見た目)→ `drop`(打つ)→ `other`(それ以外)
- **繰り返し**: 同じ (A, B, C) の組が `TYPE_VALUES.repeatMinGames`(= 3)局以上に出ること(1 局 1 回で数える)

```
生成(1 局ぶん): npx tsx scripts/playtest/type.ts --whatif <whatif-v2.jsonl> --read <read.jsonl> --kifu <固定棋譜 JSON> --out <type/<id>.jsonl>
集計(複数局・複数 work をまとめる): npx tsx scripts/playtest/type.ts --summarize <type ディレクトリ …> --out <summary.json>
```

- **生成**: `--whatif`(`scenes.fork` が true の position 行)と `--read`(position 行)を `ply` で結合する(`whatif` の meta の `kifuId`・`read` の meta の `kifuId`・`--kifu` の `id` が食い違えば exit 1)。`read.ts` 側で候補 0 件のため除外された分かれ道(計画に無い理論上の状態。`read.ts` の `skippedForkCount` と同じ考え方)は `readByPly` に無いため同じく除外し、件数だけ `skippedForkCount` に数える(24 局の実行ではこの状態は 1 件も無かった ― `read.ts` の既知の限界と同じ)。その手にかけた秒は、固定棋譍の `moveSeconds`(`originalMoves` と同じ並び・長さ。KIF の手数 = 添字 + 1)を **`displayPly - 1`**(`lib/reportData.ts` の `buildBySpent` 等と同じ添字合わせ ― `whatif.ts`/`read.ts` の `displayPly` はすでに `plyOffset` を足した「本人が指した向きの手数」)で読む(`lib/type.ts` の `spentSecOfDisplayPly`)。**局の結果(勝敗)は、この STEP の集計(T1〜T5)のどれにも使わないため出力に含めない**(計画にない判断: `入力に「局の結果」` とあるが、`resultOf`(`lib/reportData.ts`)は一部の終局の種類で例外を投げるため、使わない値のために失敗しうる経路を増やさない保守的な選択)。出力(JSONL): 1 行目 `{"kind":"meta", kifuId, gitHead, dirty, values}`(**名前・`/Users/` を含む絶対パスは書かない**)、分かれ道ごとに `{"kind":"fork", ply, displayPly, size, side, nature, key, spentSec}`(**手・SFEN・評価値は書かない**)、最後に `{"kind":"summary", kifuId, forkCount, skippedForkCount}`
- **集計**: `--summarize` に渡した各ディレクトリの `*.jsonl`(生成の出力。`summary.json` 自身は `.json` なので対象に含まれない)をすべて読み、`TypeGame` の列にしてから `lib/type.ts` の `typeGroupCountsOf`(組ごとの局数・回数)・`repeatedGroupsOf`(3 局以上の組)・`medianSecondsBySideOf`(T4 用: 側ごとの秒の中央値)・`retreatGameCountOf`(T5 用: 実戦が retreat の分かれ道が出る局数)を呼ぶ。**複数の work をまたいでまとめられる**(ディレクトリを複数渡すだけ。24 局 = `out/tatsunami3` の 14 局 + `out/tatsunami-long` の 10 局を合わせた集計は、両方の `type/` ディレクトリを渡して 1 回の `--summarize` で出す)。読み込んだファイルの `TYPE_VALUES`(meta の `values`)がそろわなければ exit 1。出力(JSON): `{"kind":"summary", gitHead, dirty, values, gamesCount, forksCount, counts, repeatMinGames, repeatedGroups, sideSecondsMedian, retreatGameCount}`
- 純粋関数は `lib/type.ts`(`sizeBucketOf`・`sideBucketOf`・`natureBucketOf`・`typeForkOf`・`typeGroupCountsOf`・`repeatedGroupsOf`・`medianSecondsBySideOf`・`retreatGameCountOf`・`spentSecOfDisplayPly`)。試験は `lib/type.test.ts`(合成の局・秒の添字合わせ・「両方」の扱い・軸 C の優先順・3 局以上の判定を含む)
- **`pipeline.ts` への配線はしない**(`read.ts` と同じ。この段だけ CLI 単体)。**タイプに名前は付けない**(組は `key`(`size|side|nature`)の文字列のまま。冊子に出すときの命名は別の判断)

## 「どうしたら」の冊子の行動のメニュー(`answerMenu.ts`。STEP ANSWER)

`scripts/playtest/answerMenu.ts`(CLI)+ `lib/answerMenu.ts`(純粋関数)は、docs/STEP_ANSWER_PLAN_2026-09-23.md §3 の
「行動のメニュー(条件 → 行動)」を TS の定数 `ANSWER_MENU` にし、`answer_menu.json` へ書き出す道具(判断的知識。
文言の正本は docs §3)。B(「どうしたら」の冊子)の検査(`report-pdf/check_answer.py`)がこの JSON を読む。

```
npx tsx scripts/playtest/answerMenu.ts --out <answer_menu.json>
```

- `ANSWER_MENU` の 1 件: `id`(M1〜M9)・`stage`(段階)・`actionCore`(行動の文の芯)・`evidenceName`(根拠の数の名)・
  `minN`(検査 5 で見る下限)・`verifyName`(答え合わせの数の名)・`verifyGate`(答え合わせの下限。null または
  `{ fraction, min }`)・`foundInSameData`(今回の対局から見つけた読みか)。
- `menuConditionHoldsOf(id, materials)`: id の「出す条件」(§3・§8.2)が、道具が計算した事実(`AnswerMenuMaterials`。
  patient_report_data.json・READ の合算・whatif-v2 の側の一致から作る)で成り立つかを判定する純粋関数。
  `answerMenuDenominatorOf(id, materials)`: 検査 5 の「根拠の数の分母」。
  `menuVerifyGateHoldsOf(id, materials)`: id の答え合わせの下限(`verifyGate`。§8.1)が成り立つかを判定する
  純粋関数。`verifyGate` が null の項目(M1 以外)は常に true。
- **司令塔の事前監査 REVISE(2026-09-23・2026-09-24)を反映**(`lib/answerMenu.ts` 冒頭のコメントに詳細):
  M4 は whatif-v2 の `candidates[0].side`・`actualSide`
  から非対称に数えた 2 分数(第 1 候補が「両方」の局面は分母に入れない)で AND 判定、M6 は
  `tagCrossTable.sacrifice` の行合計/対角(B v3 の実例「57 のうち 17」で確認)、M2/M8 は `--time-limit-sec` で
  タグ付けした patient を組ごとに合算(分子・分母を別々に足す)してから判定する。
- **ANSWER-M1(2026-09-24、`docs/STEP_ANSWER_PLAN_2026-09-23.md` §7)**: M1 の分母(中盤 1 手あたり 4 秒超の局)を
  `lib/reportData.ts` の `PatientPhaseSpent.midOver` として足し、`needsData` を解消した。3 分の組(min3)で
  `timeUpLosses.n ≥ 2` かつ `midOverOver ≥ 5` が条件、分母は `midOverOver`(minN 5)。
- **ANSWER-MENU2(2026-09-24、`docs/STEP_ANSWER_PLAN_2026-09-23.md` §8)**: 答え合わせの下限(`verifyGate`。§8.1)を
  M1 に足した(`midOver.overAndTimeUpLoss / midOver.over ≥ 1/2`。§7.6 で司令塔が手で下した「条件が成立しても、
  答え合わせの数が処方の向きを支えないので出さない」判断を機械が再現する)。M9(§8.2、時間・「中盤の消費が
  自分のふだんの中央値を超えたら、次の手の前に残り時間を見る」)を足した: 3 分の組(min3)で
  `timeUpLosses.n ≥ 2` かつ、時間負けの局の `phaseSpent.perGame[i].midSec` が**すべて**`phaseSpent.otherGames.mid`
  を超える(`AnswerMenuPatientGroup` に足した `timeUpLossMidSecs`(時間負けの局の midSec の配列)・
  `otherGamesMidMedian`(比較相手)から判定)。minN は「時間負け 2」。M9 は `foundInSameData: true`(今回の
  対局から見つけた読み。§7.6)なので、B の印の行に「今回の対局から見つけた読みです」の句が要る(検査は
  `report-pdf/check_answer.py`)。**§8 が決めていない点(実装担当の判断)**: 同じタグ(min3)の patient が
  複数(前回 20 局 + 今回 14 局)あるときの中央値の扱い。`otherGamesMidMedian` は既存の
  `phaseSpentOtherMidMedian`(`primaryGroupOf`。games が最小のファイルの中央値)と同じ代表値を使い、
  `timeUpLossMidSecs`(連結した配列)の**全部**がその代表値を超えるかで見る(詳細は `lib/answerMenu.ts` 冒頭の
  コメント)。
- **計画にない判断**: M3・M5 が使う「既定の組」は、渡された patient の中で `min3` タグがあればそれ、無ければ
  先頭の組(`primaryGroupOf`)。`min3`/`min10` のタグは `--time-limit-sec`(180 秒/600 秒)を渡す側
  (`report-pdf/check_answer.py`)が付ける。
- 試験(`lib/answerMenu.test.ts`): docs §3・§8.2 の表との一致(id・段階・minN。**行動の文の芯は今回は比べない**
  ― docs §3 の表はこの REVISE に合わせて書き直す途中のため。M8 の minN は docs 由来ではなく単独の試験
  ― 「未照合」と明記してある。M1 は ANSWER-M1 で docs 一致試験に戻した)、`menuConditionHoldsOf`/
  `answerMenuDenominatorOf`/`menuVerifyGateHoldsOf` の境界(各 id ごと。M1 の gate 3 ケース、M9 の条件 3 ケースを含む)。

## 局面つきの「この局面では、この手」(`directAnswers.ts`・`finalPositions.ts`。STEP ANSWER 追加作業 ANSWER-DIRECT)

docs/STEP_ANSWER_PLAN_2026-09-23.md §9 の道具。CLAUDE.md ルール 5 の拡張 (4)(2026-09-23 の人間の決定 ― エンジンで
答え合わせした指し手を局面つきで示してよい)の実物。B の手順のメニュー(`answerMenu.ts`)とは別に、**道具が局面と
手を選び**、付録 3(`report-pdf/render_direct.py`)として PDF にする。

### `directAnswers.ts`(問題 2「浅い読みで見えた分かれ道」の材料)

`scripts/playtest/directAnswers.ts`(CLI)+ `lib/directAnswers.ts`(純粋関数)は、`whatif.ts`(STEP WHATIF 作業 4)の
`scenes.fork` が true の position 行と、`read.ts` の分かれ道の行を `ply` で結合し(`lib/type.ts` の生成モードと
同じやり方)、`firstVisibleNodes` が null でなく `TYPE_VALUES.nodeShallowMaxNodes`(1 万。1 万ちょうどは含む)以下の
分かれ道だけを選ぶ。**新しい閾値は置かない**(`TYPE_VALUES` を import するだけ)。

```
npx tsx scripts/playtest/directAnswers.ts \
  --whatif-v2-dir <whatif-v2 jsonl のフォルダ> --read-dir <read.ts の jsonl のフォルダ> \
  --whatif-v2-dir <フォルダ> --read-dir <フォルダ> …(組をまたいで合算。複数可) \
  --group <ラベル> …または --time-limit-sec <秒> …(ペアと同じ順・同じ数。省略時は組の順の番号) \
  --out <direct_answers.json>
```

- 局ごとの結合は `lib/directAnswers.ts` の `joinDirectAnswersGame`(read 側に無い行 ― read.ts 側で候補 0 件等の
  理由で除外された分かれ道 ― は `forkCount` に数えず読み飛ばす。`lib/type.ts` の既知の限界と同じ)。局をまたいだ
  並び順(`sortDirectAnswers`。実戦との差 = `actualGapCp` の大きい順、null は最後)と印の数
  (`directAnswersCountsOf`)は `buildDirectAnswersFile` がまとめる。
- **「性質(tags)」の出どころ(実装担当の判断)**: docs §9.1 の「第 1 候補の性質(READ の印: 取る/打つ/王手/
  捨て駒/引く、と whatif-v2 の側)」という書き分けに合わせ、出力の `top1Tags`/`actualTags` は **read.ts の
  `ReadMoveMarks`**(whatif-v2 自身の `WhatifMoveTags` には打つ・捨て駒・引くに当たる印が無いため)、
  `top1Side`/`actualSide` は **whatif-v2 の side** とした。理由は `lib/directAnswers.ts` 冒頭のコメントに書いた。
- **gameNo の決め方(実装担当の判断)**: 1 対の `--whatif-v2-dir`・`--read-dir` を「1 つの組」とし、その組の中で
  kifuId の昇順に 1, 2, 3, … を振る(`lib/reportData.ts` の `buildGames` と同じ考え方)。組をまたいで通し番号には
  しない(patient_report_data.json の `games[].no` と同じ、組ごとに 1 から始まる番号にそろえるため)。
- **group(組のラベル)の決め方(司令塔の仕様追記 1、2026-09-24。実装担当の判断)**: 「局」の番号が組(3 分の組・
  10 分の組)をまたいで重なる(1〜10 が両方にある)ため、表で区別できるよう `group` を持たせた。
  `--group <ラベル>`(ペアと同じ順・同じ数)をそのままラベルにするか、`--time-limit-sec <秒>`(同じ順・同じ数。
  `report-pdf/check_answer.py` の `tag_of_time_limit_sec` と同じ対応 ― 180 → 3 分、600 → 10 分)でラベルにする。
  どちらも渡さなければ組の順の番号(1, 2, 3, …)。`--patient` そのものは受け付けない(ラベルを決めるのに中身を
  読む必要が無いため。詳しくは `directAnswers.ts` 冒頭のコメント)。
- **「実戦との差」(`actualGapCp`)の決め方(司令塔の仕様追記 2、2026-09-24)**: 実戦の手が第 1 候補からどれだけ
  下がったか(whatif-v2 の `loss`。第 1 候補の評価 − 実戦の手の評価)。実戦の手が候補 5 つに無いとき
  (`loss.isLowerBound`)は「少なくともこれだけ」という下限の値であり実戦の手そのものの正確な差ではないため、
  `actualGapCp` は null にする(`lib/directAnswers.ts` の `actualGapCpOf`)。並び順もこれの大きい順(null は最後)
  にした。`topGapCp`(第 1 候補と第 2 候補の差)は出力の JSON には残すが、表には出さない。
- 出力(JSON): `{"kind":"direct_answers", gitHead, dirty, values, answers, counts}`。`answers` の 1 件:
  `group`・`kifuId`・`gameNo`・`displayPly`・`sfen`・`actualMove`・`top1Move`・`pv`・`top1Tags`・`top1Side`・
  `actualTags`・`actualSide`・`topGapCp`・`actualGapCp`・`firstVisibleNodes`(sfen・USI は測る段〈whatif-v2〉の
  「本人 = 先手」にそろえた向きのまま)。`counts`: `top1TagCounts`・`top1SideCounts`・`actualTagCounts`
  (印ごとの n)・`gamesCount`・`totalCount`(= `answers.length`)・`totalForkCount`(局をまたいだ分かれ道の総数。
  選別をする前)。
- 試験(`lib/directAnswers.test.ts`): 合成の whatif-v2 3 行 + read 3 行での結合・選別(1 万ちょうどは含む、null は
  除く、read に無い行は forkCount に数えない、group を通す)・並び順(`actualGapCp` の大きい順、null は最後、
  `topGapCp` は並び順に使わない)・印の数(局をまたいだ合算)・`actualGapCpOf`(`loss` が null・`isLowerBound`・
  `cpValue` が null の境界)。

### `finalPositions.ts`(問題 1「盤上はこう勝てた」の材料)

`scripts/playtest/finalPositions.ts`(CLI)+ `lib/finalPosition.ts`(純粋関数)は、固定棋譜 JSON の**最後の局面**を
エンジン 1 本(素の `UsiEngine`。`read.ts` の `readEval` と同じ形)で読む。ノードは `READ_VALUES.nodeLadder` の
最大値(100 万)、MultiPV 1、Threads は既存の既定(1)。**新しい値は置かない**。

```
npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --game-nos <n,n,…> [--group <ラベル>|--time-limit-sec <秒>] --out <final_positions.json>
npx tsx scripts/playtest/finalPositions.ts --kifu <固定棋譜 JSON …> --patient <patient_report_data.json> [--group <ラベル>|--time-limit-sec <秒>] --out <final_positions.json>
```

- `lib/finalPosition.ts` の `finalPositionOf` は、`lib/sideAlignment.ts` の `readSideAlignment`(既存・確定済み。
  D0-SIDE 段 2)で固定棋譜が mirrored(本人が後手の局を回して畳んだもの)かどうかを読み、mirrored なら
  `startSfen` から、そうでなければ `lib/kifuImport.ts` の `STANDARD_START_SFEN` から `moves` を `applyMove`
  (apps/server の既存の道具)で最後まで進める(手数が奇数でも最後の手を落とさない ― `lib/replayPlan.ts` の
  2 手ずつの診断ループのための決め事はここには要らない。ファイル冒頭コメント参照)。
- `--game-nos`(カンマ区切り。`--kifu` に渡した順と対応)か `--patient`(`time.timeUpLosses[*].gameNo` の集合と
  `games[].no`/`games[].id` から対象の kifuId を決め、`--kifu` の中からその id を持つファイルだけを選ぶ)の
  どちらか一方を渡す。
- **group(組のラベル)の決め方(司令塔の仕様追記 1、2026-09-24。実装担当の判断)**: `directAnswers.ts` と同じ
  考え方だが、**この CLI は 1 回の実行で 1 つの組しか扱わない**ため、`--group`/`--time-limit-sec` は 1 個だけ
  渡す(`--time-limit-sec` は 180 → 3 分・600 → 10 分。`directAnswers.ts` と同じ対応)。どちらも渡さなければ
  `"1"`(1 回の実行に 1 つの組しか無いため、複数回の実行にまたがる「組の順の番号」はこの CLI 単体では決められ
  ない。詳しくは `finalPositions.ts` 冒頭のコメント)。
- 出力(JSON): `{"kind":"final_positions", startedAt, gitHead, dirty, nodes, threads, entries}`。`entries` の 1 件:
  `group`・`kifuId`・`gameNo`・`moves`(= 固定棋譜の `moves.length`)・`sfen`(最後の局面。mirrored の局は
  「本人 = 先手」にそろえた向きのまま)・`mirrored`・`top1Move`・`pv`・`scoreCp`・`mate`。
- 試験(`lib/finalPosition.test.ts`): 合成の局(mirrored: false・mirrored が無い古い記録・mirrored: true ―
  `lib/sideAlignment.ts` の `alignMovesToSente` で畳んで作る・moves が 0 手)で、`applyMove` を直接呼んだ結果との
  一致を確かめる。**エンジンを使う CLI 自体は vitest の対象外**(`report-pdf/` の python の道具と同じ理由。
  守りは実データでの実行時確認)。

### `report-pdf/render_direct.py`(付録 3「直接の答え」の PDF)

上の 2 つの JSON(+ `sfens.json`)から付録 3 を作る。詳しくは `report-pdf/README.md` を参照。

## 時間負けの要因を、機械で測れる候補に分解する(`timeCause.ts`・`lib/timeCause.ts`。STEP TIME-CAUSE、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)

人間の指摘(2026-09-24): 「時間が無い → 10 分で指す」は条件変更であって対策ではない。「なぜ無いのかを機械的に
分解する」。原因候補(C1〜C10)を最初から処方にせず、**全部を候補として測り、数字が出たものだけを B に上げる**。

`lib/timeCause.ts`(純粋関数)は、固定棋譜の `moveSeconds`・whatif-v2 の position 行(`ply`・`scenes.fork`・
`candidates[0].side`・`actualSide`)・patient の局の対応(`gameNo`↔`kifuId`・`timeUpLoss`)から、局ごとに
C1〜C9・`remainingSec`(C10 の材料)・`midMoveSeconds`(付録 4 の帯用)を組み、組ごとに時間切れで負けた局と
それ以外の局を分けて集計する(`buildGroupTimeCause`)。**新しい閾値は置かない**(`lib/reportData.ts` の
`TIME_VALUES`・`phaseOf`・`ownParityOf`・`spentBucketIndexOf` と `lib/type.ts` の `sideBucketOf` を import
して使い回すだけ)。

```
npx tsx scripts/playtest/timeCause.ts \
  --kifu-dir <固定棋譜〈*.fixed.json〉のフォルダ> --patient <patient_report_data.json> --time-limit-sec <秒> \
    [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] \
  [--kifu-dir <フォルダ> --patient <path> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] …]（組をまたいで合算） \
  --out <time_cause.json>
```

- **組(`--kifu-dir` で始まるブロック)の決め方(実装担当の判断)**: `directAnswers.ts`・`finalPositions.ts` は
  フラグの「対」を同じ回数だけ並べる形式だが、`--whatif-v2-dir` は組ごとに有る・無いの両方が起こる(実データ:
  `tatsunami20` に `whatif-v2` が無い)。そのため「`--kifu-dir` が出るたびに新しい組を始め、次の
  `--kifu-dir`(または `--out`)までの間のフラグをその組のものとして読む」形式にした。`--time-limit-sec` は必須
  (C10 の「終局時の残り秒」に持ち時間の秒が要る)。組のラベルは `directAnswers.ts` と同じ対応(180 → 3 分、
  600 → 10 分)。
- **局の選び方**: `--kifu-dir` の `*.fixed.json` のうち、`--patient` の `games[].id` に対応があるものだけを
  対象にする。`timeUpLoss` は `time.timeUpLosses[*].gameNo` の集合に、対応する `games[].no` が含まれるかで
  決める(`finalPositions.ts` と同じ考え方)。**`--time-limit-sec` が同じ複数の `--kifu-dir` を 1 つの組に
  合算すると、局番号(`gameNo`)は元の `--patient` ごとに 1 から始まるため、同じ組・同じ局番号が別の対局を
  指すことがある**(実データで実際に起きる。`tatsunami20` の 1〜14 局目と `tatsunami3` の 1〜14 局目が両方
  「3 分」組に入る)。`kifuId` で一意に見分けられる(JSON の各局の行に必ず入る。付録 4 の PDF にも列を足した)。
- **C1〜C9 の測り方(`lib/timeCause.ts` の `buildGameTimeCause`)**:
  - C1・C2(+ 終盤): `phaseOf`(既存)で本人の手を早・中・遅に分け、消費秒(`spentSec`)を合計する。
  - C3・C4・C5: 長考(`TIME_VALUES.longThinkSec` 以上)の時期ごとの回数、最長の 1 手とその手目、本人の連続する
    2 手(間に他の手を挟まない)がともに長考だった回数。
  - C6: 中考(`spentBucketIndexOf` が 2、= 4 超〜9 秒)の時期ごとの回数・合計秒。
  - C7・C8: 長考の手を whatif-v2 の position 行と `recordPly`(= `kifPly − plyOffset`。whatif-v2 の `ply` と
    同じ数え方 ― 実データで確認済み)で結合し、結合できたものの中で分かれ道(`scenes.fork`)に当たる数 /
    結合できた長考の総数(C7)、そのうち側が逆(`lib/type.ts` の `sideBucketOf` が
    `top1AttackActualDefense`/`top1DefenseActualAttack`。「両方」「なし」は逆に数えない)だった数 / 長考かつ
    分かれ道の総数(C8)。whatif-v2 が無い組はどちらも null。
  - C9: 序盤の終わり(`phaseOf` が mid になる最初の本人の手の直前の局面)で、本人・相手の飛車が初期の筋
    (先手 2 筋・後手 8 筋)に居るか(`rookOnInitialFileOf`)。局面は本人が指した向き(`originalMoves`・
    `DEFAULT_INITIAL_SFEN`・`applyMove`)で作る(`lib/finalPosition.ts` は mirrored な局を「本人 = 先手」に
    そろえた向きへ進めるため、絶対筋を見るこの用途にはそのまま使えない ― 実装担当の判断。ファイル冒頭コメント
    参照)。
  - C10 の材料(`remainingSec`): `timeLimitSec` − 最後に読めた本人の手の累積消費(`totalSec`)。
- 組ごとの集計(`buildGroupTimeCause`): 時間切れで負けた局とそれ以外の局に分け、C1〜C6 の中央値、C7・C8 の
  分数(局をまたいで合算)、C9 の 2×2(own×opponent)ごとの局数・序/中の消費の中央値、C10 の表(局ごとの
  early・mid・remaining。**相関の値は出さない。並べるだけ**)を組む。
- 出力(`time_cause.json`): `{"kind":"time_cause", gitHead, dirty, games, groups}`。`games` は局ごとの行(上の
  C1〜C10 の生の値 + `midMoveSeconds`)、`groups` は組ごとの集計。
- 試験(`lib/timeCause.test.ts`): 合成 2 局(先手・mirrored: false と後手・mirrored: true。実在の 30 手の対局の
  最初の 24 手を使い、7 手目の飛車の動きで C9 の両方の分岐を作る)で C1〜C9・`remainingSec`・`midMoveSeconds`
  を手で計算した値と突き合わせる。`phaseOf` の境界(early/mid・mid/late)が `lib/reportData.ts` の
  `phaseSpentOfGame`(同じ既存関数。試験のため export した)と同じ側に落ちることも確かめる。組ごとの集計は
  合成の `GameTimeCause`(盤面を伴わない)で `medianOf`・分数の合算・2×2 の内訳を確かめる。
- 実データでの確認(2026-09-24、実装担当): `tatsunami20`(3 分・`whatif-v2` 無し)・`tatsunami3`(3 分・
  `whatif-v2` あり)・`tatsunami-long`(10 分・`whatif-v2` あり)の 3 組(局 44)で rc=0。局ごとの `mid`
  (中盤の消費)が `patient_report_data.json` の `time.phaseSpent.perGame.midSec` と 44 局全部で一致(3 分の組
  34 局・10 分の組 10 局とも)。付録 4 の PDF も rc=0・全書体埋め込み・fitz で PNG 化して目視確認(3 分の組の
  時間切れ 3 局の帯を含む)。

### `report-pdf/render_time_cause.py`(付録 4「時間の使い方」の PDF)

`time_cause.json` から付録 4 を作る。詳しくは `report-pdf/README.md` を参照。

## 時間を使った手に共通する条件を、機械に探索させる(`timeSearch.ts`・`lib/timeFeatures.ts`・`lib/timeSearch.ts`。STEP TIME-CAUSE-2、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7)

人間の指摘(2026-09-24、「まさにここを知りたい」): 人が仮説を挙げる(C1〜C10、上の STEP TIME-CAUSE)のではなく、
**仮説を大量生成できる探索空間を作り、機械に「長考した手に何が共通しているか」を探させる**。見つかったものは
「一緒に起きている条件」(レベル 1)であって「原因」ではない(禁止語)。

### `lib/timeFeatures.ts`(1 手ごとの特徴の表)

`buildGameMoveFeatureRows` は、`lib/timeCause.ts` の局ごとの計算(`ownMoveTimesOf`・`rookOnInitialFileOf`・
`sfenBeforeOriginalKifPly`)を、本人の手ごとの 1 行に広げる。値はすべて既存の道具の出力から作り、**新しい
閾値は置かない**。1 行 = 本人の 1 手で、次の列を持つ(値はすべて離散。`null` は「この手では条件に使えない」
という意味で、探索(`lib/timeSearch.ts`)はそのまま素通りする)。

- **時間**: `spentBucket`(その手の秒の段。`≤1`/`≤4`/`≤9`/`>9`)、`prevOwnSpentBucket`・`prev3SumBucket`・
  `prev5SumBucket`(直前 1・3・5 手の合計を同じ段で。3・5 手のどれか 1 つでも「2 手前・4 手前・…」の kifPly が
  ずれていれば〈間に秒の読めない本人の手が挟まっている〉`null`)、`afterLongThink`(直前の自分の手が長考)、
  `remainingBucket`(`TIME_VALUES.leftBucketsSec` の段。`--time-limit-sec` が無ければ `null`)。
- **局面**: `phase`(`phaseOf`)、`evalBand`(この手を指す前の評価の段。`ahead`/`level`/`behind`。
  `STANDING_BOUNDS` そのまま)、`evalChangePrev`(直前の自分の手番からの評価の向き。`up`/`same`/`down`。
  「同」の境も `STANDING_BOUNDS` の使い回し)、`inCheck`(この手を指す前に王手を受けているか)。
- **選択**(whatif-v2 の position 行がある手だけ): `fork`・`top1Side`・`actualSide`(攻め/守り/両方/なし、
  whatif-v2 の生の値)、`lossBand`(`loss.cpValue` を `STANDING_BOUNDS.aheadCp`〈300〉で 2 値。`isLowerBound`
  〈実戦の手が候補に無い〉は `outOfCandidates`)、`inTop5`(`actualRank` が `null` でない)、READ の印
  (`lib/read.ts` の `moveMarksOf`。取る/打つ/王手/捨て駒/引く の 5 つを、実戦の手・第 1 候補それぞれに)。
- **相手**: 直前の相手の手の印(取る/打つ/王手/成る。`moveMarksOf` + USI の末尾 `+`)。
- **形**: `ownRookMoved`・`oppRookMoved`(局の C9〈`lib/timeCause.ts` と同じ求め方〉の印を全行に付ける。
  `rookOnInitialFileOf` の否定 ― 「初期の筋のまま」ではなく「動いた」の向きにそろえた)。
- **目的変数**: `longThink`(`spentSec` ≥ `TIME_VALUES.longThinkSec`。主)・`spentSec`(副)。

段 2 の記録(replay.ts → rescreen.ts の JSONL)の ready 行は**すべて「本人の手番」の局面**であり(実データで
確認: `ply` は常に偶数)、相手の手を指す前(相手の手番)の局面は記録に無い。そのため相手の直前の手の印は、
1 つ前の ready 行の `sfen` に同じ行の `senteMove`(本人の直前の手)を `applyMove` で 1 手重ねて作る。

whatif-v2 自身の `candidates[].tags`/`actualTags`(`WhatifMoveTags`)は攻め・守りの側の印であって、この段が
要る「取る/打つ/王手/捨て駒/引く」とは別物なので、`lib/read.ts` の `moveMarksOf` を別に呼ぶ(実装担当の判断)。

### `lib/timeSearch.ts`(探索)

`SEARCH_COLUMNS`(30 列。`kifuId`・`group`・`gameNo`・`kifPly` の識別子と、`spentSec`・`spentBucket`・
`longThink`〈目的変数そのもの、またはその生の形の離散化 ― `spentBucket` は `longThink` とほぼ同義になり、
条件に使うとトートロジーになる〉を除いたすべて)から、単独 → 2 条件 → 3 条件の組を全列挙する
(`enumerateCandidatesOf`。同じ列を 2 回使わない。**列の値域の直積ではなく、実際に手に出会った〈n ≥ 1 の〉
値の組だけを数える** ― 実装担当の判断)。

各組の該当する手の数 n と長考率 p を、全体の長考率 p0 と比べる。**採用候補**: n ≥ `FINDING_VALUES.minPairs`
(20)かつ p ≥ p0 × `FINDING_VALUES.ratio`(2)(`isAdoptedOf`)。発見用で採用候補になった組を検証用でも数え直し、
n ≥ `TIME_SEARCH_VALUES.validateMinN`(= 10。この計画で唯一の新しい値)かつ p ≥ p0(検証用) × 2 なら
「再現した」(`isReproducedOf`)。

#### STEP TIME-CAUSE-3(2026-09-25、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §9)。探索の結果を圧縮し、時間 × 崩れで照合する

- **崩れの列**(`lib/timeFeatures.ts` の `MoveFeatureRow.collapse: boolean | null`): この手の前の評価(`evalBand`
  の元)と、次の本人の手番の前の評価(次の ready 行)から、既存の崩れの定義(`lib/gate.ts` の `collapseOf`)で
  求める。前が behind・どちらかが未定・次の ready 行が無ければ(最後の手)`null`(分母に入らない)。`collapse`
  自身は `SEARCH_COLUMNS` から除く(目的変数そのものなので、条件に使うとトートロジーになる ― `longThink` と
  同じ理由)。
- **`ConditionStats` に崩れの 2 つ目の数**(`lib/timeSearch.ts`): `collapseCounted`(`collapse` が `null` でない
  手の数)・`collapsed`(そのうち `true` の数)・`q`(= `collapsed / collapseCounted`。分母 0 なら `null`。`p` は
  既定が `0` なのに対し `q` は `null` にした ― 計画どおり)。`SearchResult.discover`/`validate` にも全体の
  `collapseCounted`・`collapsed`・`collapseRate` を足した。
- **`kind`**(`ReproducedCandidate.kind: "A" | "B" | "C" | null`。`kindOf`): 発見用・検証用の**両方**で「時間」
  (`isAdoptedOf`/`isReproducedOf`)・「崩れ」(`isCollapseAdoptedOf`/`isCollapseReproducedOf`。同じ値の使い回し)
  を判定し、両方が一致したときだけ付く(一致しなければ `null`)。**A** = 時間だけ/**B** = 時間 + 崩れ/
  **C** = 時間でない + 崩れ。
- **崩れを目的変数にした 2 回目の探索**(`SearchResult.collapseSearch: {depths, reproduced, notReproduced}`):
  `runSearchOf` を目的変数(`TIME_OBJECTIVE`/`COLLAPSE_OBJECTIVE`)で一般化し、同じ列挙(`enumerateCandidatesOf`)
  を崩れの採用候補(`collapseCounted` ≥ minPairs かつ q ≥ q0 × ratio)・再現(同じ線、`validateMinN`)で回す。
  **C はこの探索からしか出ない**(長考の探索は時間で候補を選ぶため、時間を満たさない条件〈C の前提〉は
  `adopted` に入らない)。
- **偶然の目安**(`DepthSummary.chanceReproduced`・`chanceLineProbabilityOf`): 深さごとに、採用候補の数 ×
  二項分布の裾(検証用の基準率〈p0 または q0〉のもとで、n = `validateMinN` の手が線〈基準率 × ratio〉を
  越える確率)。長考の探索・崩れの探索のどちらの `depths[]` にも付く。
- **共通因子の表**(`FactorEntry[]`・`factorSummaryOf`): 部品(単独条件)ごとに、(a) 長考の探索で再現した組に
  入る数(深さ別・合計。`inReproduced`)、(b) 部品 1 つだけの条件の `ConditionStats`(発見用・検証用。採用候補
  でなくても出す。`single`)、(c) 部品 1 つで時間の線を越えるか(`singleOverLine`)、(d) その部品を含む長考の
  再現した組のうち B 型の数(`inKindB`)、(e) 崩れの探索で再現した組に入る数(`inCollapseReproduced`)とその
  うち C 型の数(`inKindC`)を出す。**(2026-09-25 の人間の修正、最重要)**: 「よく登場する部品」を答えにしない。
  3 つのアウトカム(長考・時間 + 崩れ・速く指して崩れ)それぞれに `explains.longThink`・
  `explains.timeAndCollapse`・`explains.quickCollapse`(`"single" | "combo" | null`)を付ける。`single` = 部品
  1 つの条件が発見用・検証用の両方でそのアウトカムの線を越える/`combo` = 単独では越えないが、そのアウトカムの
  再現した組(型が一致するもの)に 1 つ以上入る/どちらでもなければ `null`。並びは `single` の数 → `combo` の数
  → `inReproduced.total` の多い順。

```
npx tsx scripts/playtest/timeSearch.ts \
  --role discover --kifu-dir <固定棋譜のフォルダ> --records-dir <段 2 の JSONL のフォルダ> \
    --time-limit-sec <秒> [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] \
  [--role discover|validate --kifu-dir <フォルダ> --records-dir <フォルダ> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] …] \
  --out <time_cause_search.json>
```

- `--kifu-dir` で組が始まる(`timeCause.ts` と同じ形式)。`--role` はその組の役割で、`--kifu-dir` の前に要る。
  `--patient` は取らない(`gameNo`・`timeUpLoss` を使わないため ― 実装担当の判断。`gameNo` はソート順の連番)。
  `--records-dir` は必須(`<kifuId>.jsonl`)。
- 出力(`time_cause_search.json`): `{"kind":"time_cause_search", gitHead, dirty, discover: {moves, longThinkRate,
  collapseCounted, collapsed, collapseRate}, validate: {...}, depths: [{depth, tried, adopted, reproduced,
  chanceReproduced}, …], reproduced: [{depth, condition, discover: {n, longThink, p, collapseCounted, collapsed,
  q}, validate: {...}, kind}, …], notReproduced: [...同じ形...], collapseSearch: {depths, reproduced,
  notReproduced}(崩れを目的変数にした 2 回目の探索。同じ形), factors: [{column, value, inReproduced,
  single, singleOverLine, inKindB, inCollapseReproduced, inKindC, explains}, …]}`(`collapseSearch`・`factors`・
  `kind`・`chanceReproduced`・崩れの数は STEP TIME-CAUSE-3 で足した。既存の鍵は変えていない)。
- 実データ(2026-09-24、実装担当): 発見用 = `tatsunami20`(`whatif-v2` 無し → 選択の列は発見用側で条件に
  出てこない。材料の事実であり、直していない)、検証用 = `tatsunami3`(`whatif-v2` あり)で rc=0。数そのもの
  (試した数・採用候補・再現の数・p0・再現した条件)は司令塔が予測(F1〜F7)と照合するため、ここには書かない
  (盲検)。

### `report-pdf/render_time_cause.py` への追加(「探索の結果」のページ)

`--search <time_cause_search.json>` を任意で受け取る(渡さなければ従来どおり)。見出しは「時間と一緒に
起きている条件(探索)」。**STEP TIME-CAUSE-3 で差し替え**(226 組の一覧はやめた): 深さごとの表を 2 つ
(長考・崩れ、それぞれ試した組の数・採用候補の数・再現の数・偶然の目安)→ 共通因子の表(上位 15。部品ごとに
3 つのアウトカムを「単独で再現」「組で再現」「―」で分類)→ 時間と崩れの両方を説明する条件の一覧 →
速く指して崩れの条件の一覧(上位 10)。A/B/C は文中で「型」と呼ばず「時間だけ」「時間と崩れ」「速く指して
崩れ」と書く。機械の禁止語は無い(2026-09-25 の人間の決定で機械の禁止語は無し(凍結の例外 14 件目)。`render_front.py` の `BANNED` は空)。固定文は今も
「原因」「傾向」「型」「クセ」「パターン」を使っていない(文そのものの書き直しは別の作業)。詳しくは `report-pdf/README.md` の同じ見出しを参照。

### 試験

- `lib/timeFeatures.test.ts`: 合成 1 局(先手・GAME01_MOVES の最初の 16 手)で、`moveSeconds`・植えた評価
  (`plantedRecords`/`engineRef`)・whatif-v2 の入力から手で計算した列の値と突き合わせる。`collapse` 列は、
  同じ合成局の評価から「前が ahead/level で段が下がる(true)」「下がらない(false)」「前が behind(null)」を
  確かめ、別の合成局(評価を `null`〈未定〉にした行を含む)で「前・次のどちらかが未定なら null」を、
  15 手で終わる合成局で「最後の本人の手(次の ready 行が無い)は null」を確かめる(STEP TIME-CAUSE-3)。
- `lib/timeSearch.test.ts`: 合成の表(60 行、列 4 つ: `phase`・`fork`・`inCheck`・`afterLongThink`)で、
  列挙の数(深さ 1〜3 それぞれ組合せの数と合う)・`statsOf` の n/p・`isAdoptedOf`/`isReproducedOf` の判定・
  `TIME_SEARCH_VALUES.validateMinN` の境界を確かめる。STEP TIME-CAUSE-3 で足した試験: `statsOf` の
  `collapseCounted`/`collapsed`/`q`、`isCollapseAdoptedOf`/`isCollapseReproducedOf`、`kindOf`(A/B/C/null の
  4 通りと、発見用・検証用が不一致なら `null` になること)、`chanceLineProbabilityOf`(既知の値 `p0=0.058,
  n=10, ratio=2 → 約 0.111` と、境界の 2 例)、崩れが実際に動く合成の表(`phase` だけを動かし、深さ 2・3 は
  候補 0 になるよう設計)で `kind` が B/C になること・`collapseSearch`・`factors`(`explains`・`inReproduced`・
  `inCollapseReproduced`・`inKindB`・`inKindC`・並び順)を確かめる。

### CAUSE-SEARCH-1(2026-09-25、docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §11)。探索器を「アウトカムを 1 つ指定する道具」に一般化

人間の整理: このアルゴリズムを時間だけでなく普遍的なものにしたい。`lib/timeSearch.ts` に `OUTCOMES`
(`"longThink" | "collapse" | "decisionGap"`)を公開し、アウトカムごとに探索を 1 回ぶん取り直せるようにした。

- **`decisionGap`(新しいアウトカム)**: 分かれ道で実戦の手がエンジンの評価で `STANDING_BOUNDS.aheadCp`(300)
  以上損していたこと(`fork && lossBand === "over300"`)。`fork` が `null`(whatif-v2 の無い手)は `null`
  (集計に入らない)。
- **アウトカムごとの除外列**: `longThink` は `spentBucket`・`spentSec`(もともと `SEARCH_COLUMNS` に無い、
  既存の除外)。`collapse`・`decisionGap` は `fork`・`lossBand`・`inTop5`・`evalChangePrev`(実戦の手の評価差
  そのもの)を新しく除く。除外は `enumerateCandidatesOf`・`runSearchOf` に足した任意の `columns` 引数
  (既定は `SEARCH_COLUMNS`。省略すれば以前と同じ)で行う。
- **`SearchResult.searches: { longThink, collapse, decisionGap }`**(渡す `columns` が違うだけの各 1 探索)。
  `searches.longThink` は既存の `depths`・`reproduced`・`notReproduced`(トップレベル)と同じ中身(同じ
  オブジェクト)。`searches.collapse` は既存の `collapseSearch` とは**列が違う**(新しい除外)ため中身も違う
  ― 既存の `collapseSearch` は変えていない(同一性の試験を優先)。`searches.collapse` の各条件には崩れの
  内訳(`collapsedLong`: `spentBucket === ">9"` の崩れ、`collapsedQuick`: `"≤1"` の崩れ)を足した。
  `decisionGap` は `ConditionStats` を広げず、専用の `OutcomeStats`(`n`・`matched`・`rate`)で持つ
  (`ConditionStats` を広げると既存の鍵の JSON が変わってしまうため)。
- **`FactorEntry.byOutcome: { longThink, collapse, decisionGap }`**(`"single" | "combo" | null`。`single` =
  部品 1 つが両組でそのアウトカムの線を越える、`combo` = そのアウトカムの再現した組〈`searches.<outcome>.
  reproduced`〉に入る)。`byOutcome.longThink` は既存の `explains.longThink` と同じ判定(そのまま複製)。
  `byOutcome.decisionGap` の判定に使った部品単独の分数は `FactorEntry.singleDecisionGap`(発見用・検証用の
  `OutcomeStats`)として新しく JSON に出す(`longThink`・`collapse` の単独の分数は既存の `single` に入っている)。
- **同一性の試験(§11.1 の 7.)**: 一般化の前(feature HEAD `ac1c35c`)と後で、実データ(発見 = `tatsunami20`
  〈whatif-v2 なし〉・検証 = `tatsunami3`〈whatif-v2 あり〉、ともに 180 秒)に対し `depths`・`reproduced`・
  `notReproduced`・`collapseSearch`・`factors[].explains`・`factors[].inReproduced` が JSON として完全に一致
  することを確かめた(実装担当、スクラッチで python 比較)。
- CLI(`timeSearch.ts`)に `--outcomes longThink,collapse,decisionGap`(既定 3 つ全部。指定した鍵だけを出力の
  `searches` に残す。`searchOf` 自体は常に 3 つとも計算する)。
- `report-pdf/render_time_cause.py` の「探索の結果」ページを `TS["searches"]` を使って書き直した(渡された
  `--outcomes` の分だけアウトカムごとの深さの表・上位 10 の一覧を出す)。共通因子の表は既存の 5 列に
  「判断のずれとの関係」(`byOutcome.decisionGap`)を足した 6 列。旧来の「時間と崩れの両方を説明する条件」
  「速く指した手が崩れと一緒に起きている条件」(kind A/B/C の一覧)は、アウトカムごとの上位 10 の一覧に
  置き換えた。実データ(実装担当、発見用に whatif-v2 が無いため `decisionGap` は 0 件): rc=0・10 ページ。
- `check_answer.py --time-search` の登録に `searches.*`(viii〜ix)・`singleDecisionGap`(x)を足した(別コミット)。
  詳しくは `report-pdf/README.md` の同じ見出しを参照。

## 納品までを 1 コマンドで通す(`deliver.ts`・`lib/deliver.ts`。STEP DELIVER-1、docs/STEP_DELIVER1_PLAN_2026-09-25.md)

**分析ロジックは 1 バイトも変えていない。** この道具は既存の道具を規定順に**子プロセスで呼ぶだけ**で、
判断・値・文言を持たない(`pipeline.ts` と同じ流儀)。引数の組み立て・段の順・済みの判定は
`lib/deliver.ts`(純粋。`lib/deliver.test.ts` に試験)にあり、`deliver.ts` は子プロセスの起動と fs だけ。

```
npx tsx scripts/playtest/deliver.ts \
  --person <id> --kifu-dir <dir> --work <dir> --time-limit-sec <秒> \
  --name <表示名> --title <タイトル> --today <YYYY-MM-DD> --out <顧客フォルダ> \
  [--previous-work <前回の work>] [--parallel <N>] \
  [--compare-dir <段 2 の記録のフォルダ …> --compare-person <p記号>] \
  [--group-work <work> --group-time-limit-sec <秒>]… \
  [--forbid <語>]… [--dry-run] [--from <段の名前>]
```

**これ 1 本で新規顧客から納品まで通る**(2026-09-23 の人間の決定。それまでは `pipeline.ts --until gate` を
先に手で回す必要があった)。手順は 1 本だけで、上のコマンド以外に覚えるものは無い。**空の work(= 初めての
顧客)でも同じ 1 コマンドで通る**(2026-09-23 に再確認)。段の直前に引数を読み直すため、後の段が作る材料
(`read/`・`whatif-v2/`・固定棋譜)を使う段は、その材料ができてから正しい引数で動く。

**ただし「1 本」は組が 1 つのときの話である(2026-09-25 に 4 人目の顧客で分かった)。** この道具が材料を作るのは
`--work` に渡した**今回の組 1 つ分**だけで、`--group-work` は**すでに材料がある組を順序つきで並べる旗**である
(下記)。したがって**持ち時間が 2 種類ある初回の顧客**(4 人目は 3 分切れ負け 18 局 + 10 分 + 30 秒 2 局)は、
**`deliver.ts` を 2 回走らせる**。

1. 先に**前の組**を「今回の組」として走らせ、材料だけ作る(`--kifu-dir`・`--work` をその組にする。人間の確認点
   `prose-gate` で自然に止まるので、そこで捨ててよい ― `read/`・`whatif-v2/`・固定棋譜・`patient_report_data.json`
   は段 `pipeline-data` までに揃う)。
2. 次に**主たる組**を「今回の組」として本番を走らせ、`--group-work`/`--group-time-limit-sec` に**両方の組**を
   持ち時間の昇順で並べる(`--work` は一覧にちょうど 1 回)。

**棋譜は組ごとのフォルダに分ける**(混ぜると 1 手あたりの秒が意味を失う)。**組ごとに局番号が 1 から振り直される**
ので、ファイル名の数字も 1 から付ける(入口の名前検査が「局番号以外の数字」を落とすため。下記の `--kifu-dir` の
規約)。どのファイルがどの組の何局目になったかは、**自分で記録に残す**(冊子の対応表はファイル名から作られる)。

**止まる 2 か所(`prose-gate`・`answer-gate`)で何をどう書くかは [../../docs/DELIVER_GATES.md](../../docs/DELIVER_GATES.md)**
(書く前の 4 原則・`_mid.py` と `check_answer.py` が機械で見る規則・行動のメニュー M1〜M9・PDF 目視の観点)。

- **`--kifu-dir` のファイル名の規約(2026-09-23 に実測で分かった)**: ファイル名には**局番号以外の数字を
  入れない**(`g01-sente.kif` … `g20-gote.kif` のように付ける)。理由は 2 つで、どちらも付録 4 に出る。
  (1) 局の `kifuId` は**ファイル名から作られる**(`lib/pipeline.ts` ― 末尾の `-sente`/`-gote` を外した残り)。
  付録 4 の見出し(`render_time_cause.py:437`)はその `kifuId` を**数の照合にかける**ので、許す数
  (その局の `gameNo`・総手数と `{1,2,3,4,5,9,10,300}`)に無い数字 ― 日付や外部サービスの対局 ID ―
  が入っていると必ず「データに無い数」で落ちる(数の取り出しは `[0-9]+` なので、`a0kABJIn` のような
  ID からも `0` が出る)。(2) 付録 4 は `kifuId` を**冊子に印字する**(表の欄 `render_time_cause.py:234`
  と上の見出し)。**`kifuId` を印字するのは付録 4 だけ**(ほかの `render_*.py` は印字しない ―
  `render_direct.py` は `sfens.json` の鍵に使うだけ)。対局 ID や日付を冊子に出さない約束の顧客では、
  ファイル名にそれが入っている限り検査を通しても不適合になる。**直すときはファイル名を付け替えて
  段 2 から作り直す**(記録の中の ID だけ手で書き換えると、使われなかった ID の記録が残って
  `meta.gitHead` が事実と食い違う)。**`deliver.ts` はこの規約を入口で機械に見る**(引数を読んだ直後・
  `--out` の安全装置より前。`--dry-run` でも `--from …` でも同じように止まる ― 飛ばせない)。
  問題があれば何も実行・書き込みせずに rc=1 で止まり、どのファイル名のどの数字が悪いかを出す。
- `--compare-dir`/`--compare-person`: 段 `pipeline-gate` が `pipeline.ts --until gate` へ**中継するだけ**の引数
  (`--compare-dir` は値を連続していくつでも取れる。2 つは必ず一緒に渡す)。新しい work には判定の出力
  (`<work>/<person>/gate.jsonl`)が無いため、これが無いと段 `pipeline-data` が材料不足で止まる。
  **`gate.jsonl` が既にあれば段 `pipeline-gate` は飛ぶ**(既存の work はこの 2 つを渡さなくてもそのまま通る)。
  この 2 つは段 `pipeline-data`・`pipeline-pdf` には渡らない(既存の段の引数は変わらない)。
- `--group-work`/`--group-time-limit-sec`: 付録 3・付録 4・B の検査で**組をまたいで合算する組の一覧を、
  順序つきで明示する**(対で同じ回数並べる)。組の順が、付録 3・付録 4・検査の引数の並びを決める。
  渡さないときの既定は `[--previous-work(あれば), --work]` の順。`--work` は一覧にちょうど 1 回含めること。
- `--from <段の名前>`: 人間の確認点で止まった後、その段から再開する。各段に済みの判定があるので、
  既定(最初から)でも再実行は無駄にならない。

  **流した席以外が再開するとき(P-168。2026-09-29 に実測して書いた)**: `deliver_log.jsonl` には
  段ごとの `stage`・`rc`・時刻しか書かれておらず、**引数が残らない**。`--from` には `--person`・
  `--kifu-dir`・`--work`・`--time-limit-sec`・`--out` 等が全部要るので、**`--dry-run` で復元する**:

  ```bash
  npx tsx deliver.ts --person <p番号> --kifu-dir <棋譜> --work <work> \
    --time-limit-sec <秒> --name X --title X --today <YYYY-MM-DD> --out <納品先> --dry-run
  ```

  印字された JSON の `steps[].args` が、その段をそのまま手で流せる引数一式である。
  **`--name`・`--title` は何を渡してもよい**(2026-09-29 の P-170 の直しで、顧客向け出口 30p 形の
  どの冊子にも届かなくなった。届くのは却下済みの 6 冊形の 2 つの段だけ)。
  **`--today` だけは復元できない**が、本編の 1 ページ目に印字されているので実物から読める。
  **校正済み**: この手順で本編を scratchpad に組み直し、封(`direct/exit_seal.json`)の 3 つの数と
  一致することを確かめた(2026-09-29)。
- `--dry-run`: 何も実行・書き込みせず、段ごとの `{stage, tool, cmd, args, action, reason}` を JSON で出す。
  **段 `pipeline-data` が作る材料(`read/`・`whatif-v2/`・固定棋譜)がまだ無いとき、`--dry-run` の引数は
  「その時点の見え方」でしかない**(それを使う段の引数は実行時に読み直して決まる)。そのときは JSON の
  最上位に `note` が付く。材料が揃っているときは `note` は付かない(既存の出力は 1 バイトも変わらない)。
- `--out` の安全装置: `--out` に `deliver.ts` 自身が書く名前以外のファイルがあれば、何もせず止まる。

### 工程ごとの表(入力 / 出力 / 所要 / 人間の操作 / 停止条件)

所要は固定材料 44 局(3 組)での実測(`deliver_log.jsonl`。局ごとの材料が済みだったため、
S1〜S4・whatif・READ は済みの判定で飛んでいる。**エンジンを実際に回したのは段 7 だけ**)。
段 1 の所要だけは別の実測(`gate.jsonl` を消した 14 局の複製で走らせたときの `deliver_log.jsonl`)。

**表の所要は「材料が済みだったとき」の数字である。初めての顧客(空の work)の実測は別にある**
(2026-09-23、別セッションの 20 局 + 比べの 30 局。`deliver_log.jsonl`):
**機械の時間の合計 5781 秒 = 96.4 分**で、うち段 `pipeline-gate` が 3816 秒・段 `pipeline-data` が
1954 秒、**残る 16 段の合計は 11 秒**。ほぼ全部がエンジンの評価と READ である。局数・比べの材料が違うので
表の数字と直接は比べられないが、**初めての顧客では 1 時間半ほどかかる**ことの目安になる。
人の確認点で止まっていた時間は含まない(それは原価③。docs/STEP_DELIVER1_PLAN_2026-09-25.md §11.5.5)。

**エンジンの本数の数え方(2026-09-23 に実際に使った形。宣言した本数を超えていないことの記録に使う)**

```
while pgrep -f "<回している道具>" >/dev/null 2>&1; do
  echo "$(date -u +%H:%M:%S) $(ps -Ao comm | grep -c 'YaneuraOu-by-gcc$')" >> <作業用>/engine-samples.txt
  sleep 10
done
```

- **`pgrep -c -f YaneuraOu` で数えない。** 数えているシェル自身のコマンド行にも文字列が入るので水増しする
  (実際に 8 本と出て、本当は 5 本だった)。`ps -Ao comm` に `$` 付きで当て、**実行ファイル名だけ**を数える。
- **10 秒ごとに取る。** 1 回だけ見ると起動の谷間に当たって 0 本と出る(実際に起きた)。
- **最大と平均の両方を出す。** 最大は「宣言を超えていない」ことを言い、平均は「宣言した本数を実際に
  使い切ったか」を言う(20 局の実測は最大 5・平均 4.4〜4.6)。
- **開始前と終了後を別に数えて残す。** どちらも 0 本であることが、他のセッションと重なっていないことの裏になる。

| # | 段 | 入力 | 出力 | 所要 | 人間の操作 | 停止条件 |
|---|---|---|---|---|---|---|
| 1 | `pipeline-gate` | `--kifu-dir` の棋譜、`--compare-dir` の段 2 の記録 | `<work>/<person>/gate.jsonl`(判定の出力) | 47.7 秒(14 局 + 試す側 30 局。**`gate.jsonl` があれば 0.0 秒で飛ぶ**) | なし | `pipeline.ts --until gate` rc≠0 / `gate.jsonl` が無いのに `--compare-dir`・`--compare-person` が渡されていない |
| 2 | `pipeline-data` | `--kifu-dir` の棋譜、段 1 の `gate.jsonl`、前回の `patient_report_data.json` | `<work>/p2/…`(S1〜S4・whatif-v2・read)、`<work>/report/patient_report_data.json` 他 | 24.9 秒 | なし | `pipeline.ts` rc≠0 |
| 3 | `prose-gate` | `<work>/report/prose.json` | — | 0.0 秒 | **言い換えを書く**(`prose-request.md` を基に) | `prose.json` が無ければ止まる(`humanGate`) |
| 4 | `pipeline-pdf` | 同 2 + `prose.json` | `<work>/report/front.pdf`・`main.pdf`・`whatif.pdf`・`whatif_report_data.json` | 2.2 秒 | なし | `pipeline.ts` rc≠0 |
| 5 | `deliverables-pdf` | 段 4 の 3 冊 | `<out>/1_まとめ.pdf`・`2_付録1_…`・`3_付録2_…` | 0.0 秒 | なし | 複製元が無い |
| 6 | `appendix3-answers` | `read/` がある組の `whatif-v2/`・`read/` | `<out>/direct/direct_answers.json` | 0.5 秒 | なし | `directAnswers.ts` rc≠0 |
| 7 | `appendix3-final` | 組ごとの固定棋譜・`patient_report_data.json` | `<out>/direct/final_positions_<i>.json` → 連結して `final_positions.json` | 1.4 秒(**エンジン 1 本**) | なし | `finalPositions.ts` rc≠0 / 全組 0 局 |
| 8 | `appendix3-pdf` | 段 6・7 の JSON、`REPORT_DATA_DIR`(組の report を組の順) | `<out>/5_付録3_直接の答え.pdf` | 0.4 秒 | なし | `render_direct.py` rc≠0 |
| 9 | `appendix4-cause` | 全組の固定棋譜・patient・(あれば)`whatif-v2/` | `<out>/direct/time_cause.json` | 0.6 秒 | なし | `timeCause.ts` rc≠0 |
| 10 | `appendix4-search` | 前回の組(発見用)・今回の組(検証用)の固定棋譜・段 2 の記録 | `<out>/direct/time_cause_search.json` | 6.9 秒 | なし | `timeSearch.ts` rc≠0 |
| 11 | `appendix4-pdf` | 段 9・10 の JSON | `<out>/6_付録4_時間の使い方.pdf` | 0.6 秒 | なし | `render_time_cause.py` rc≠0 |
| 12 | `answer-menu` | `lib/answerMenu.ts` の表 | `<out>/direct/answer_menu.json` | 0.4 秒 | なし | `answerMenu.ts` rc≠0 |
| 13 | `answer-draft` | 組ごとの patient、段 6・7・9・10 の JSON、`read/`・`whatif-v2/` | `<out>/8_B_どうしたら_下書き.md`(事実の箇条書きだけ) | 0.1 秒 | なし | `answer_facts.py` rc≠0 |
| 14 | `answer-gate` | 段 13 の下書き | — | 0.0 秒 | **「読み」を書く**(`<!-- TODO: 読み -->` を埋める) | 印が残っていれば止まる(`humanGate`) |
| 15 | `answer-check` | 下書き + 材料の旗 20 個 | — | 0.5 秒 | なし | `check_answer.py` rc≠0(落ちた文の一覧) |
| 16 | `answer-pdf` | 同 15 | `<out>/8_B_どうしたら.pdf` | 0.8 秒 | なし | `render_answer.py` rc≠0 |
| 17 | `exit-candidates` | 段 15 と同じ材料の旗 + 固定棋譜のフォルダ | `<out>/9_本編.md`(下書き)・`<out>/direct/exit_candidates.json` | 1 秒 | なし | `exit_candidates.py` rc≠0 |
| 18 | `exit-fill` | ⑤ の採用(`<顧客>/exit/answer_selection.json`)・① の packet(`<顧客>/packet/observation-packet.json`)・request・段 17 の 2 本・言い換えの文(`<顧客>/exit/fill_texts.json`)・統合の周(`<顧客>/llm-seats/<runId>/integration.json`)+ 材料の旗 + 環境変数 `REPORT_DATA_DIR`(`sfens.json`。見出しの指し手の字。段 7・20 と同じ) | `<out>/9_本編.md`(スロットを埋めた本編)・`<out>/direct/slot_map.json` | 1 秒 | なし(packet が無ければ飛ぶ = 書き手が書く。`TODO` の無い本編は触らない) | `exit_fill.py` rc≠0(言い換えが statement を越える・候補に無い局面・表に無い行動・`check_answer` 不通過) |
| 19 | `exit-gate` | 段 17 の 2 本 + 材料の旗 | — | 0.3 秒 | **数 3 つ・盤 2 つ・行動を選ぶ** | `exit_gate.py` rc≠0(落ちた項目の一覧。`humanGate`) |
| 20 | `exit-render` | 本編の md・組版が書いた索引 2 本(付録 1 は `<work>/report/main_page_index.json`、付録 3 は `<out>/5_付録3_直接の答え_page_index.json`) | `<out>/10_付録_表紙.md`・`.pdf`・`<out>/9_本編_本人用.pdf`・`_見本用.pdf`・`9_本編_本人用_page_index.json`・`10_付録_数の出どころ.pdf`・`10_付録_page_index.json` | 3 秒 | なし | 3 本のどれかが rc≠0(表紙 → 本編 → 束ねの順) |
| 21 | `exit-check` | 段 19 の成果物 + 索引 + 材料の旗 | — | 3 秒 | なし | `check_structure.py` rc≠0(器の 8 項目) |
| 22 | `check-delivery` | `<out>` の PDF 全冊と md | — | 0.2 秒 | **PDF の目視** | 禁止語・`@`・`/Users/`・「水匠」・`None`・`--forbid` の語があれば rc≠0 |

段 17〜21 は**顧客向け出口**(18 の `exit-fill` は ⑥ Slot filling。2026-10-05)(承認済みの 30 ページの形。`docs/GOLDEN_MASTER_CUSTOMER_EXIT.md`)。
**既存の 6 冊は材料として残り**、ここで本編 1 冊 + 付録 1 冊に束ね直す。
段 `exit-render` だけは 1 段で 3 本回す(`exit_cover.py` → `exit_body.py` → `exit_render.py`。段 6 と同じ形)。

段の前後に `<out>/deliver_log.jsonl` へ 1 行追記する(`{stage, startedAt, finishedAt, rc, humanGate}`。
`rc` は数か `"skip"`)。人間の確認点で止まった段は、**止まった時刻の行と、`--from` で再開したときの行の
2 行**が残る(原価③の測り方)。段が rc≠0 ならそこで止まり、以降の段は実行しない。

**人の席の時間(原価③)は `seatSeconds` として記録の行に入る**(2026-09-29。仕様 §5)。
**通した実行にだけ付き、その段の「最後の記録」が止まった記録のときだけ測る** ―
一度通した後の再実行で同じ待ち時間を二度書かないため。止まった記録が無ければ**鍵自体を付けない**
(0 と書くと「席に 0 秒かかった」と読めるため。**測っていないものを数にしない**)。
`prose-gate`・`answer-gate`・`exit-gate` の 3 つとも同じ形で測れる。

### B の「分かっている事実」を機械で組む(`report-pdf/answer_facts.py`)

**数を自分で計算しない。** 同じフォルダの `check_answer.py` を import して、その `PatientFile`・
`combined_groups_of`・`read_combined_of`・`side_match_of`・`direct_materials_of`・
`time_cause_materials_of`・`tag_of_time_limit_sec` が既に作っている材料から数を**引くだけ**である
(`check_answer.py` は 1 バイトも変えていない)。文の形は基準版(v7)の箇条書きをテンプレートにし、
差し替えるのは数だけ。数が引けない箇条書きはその行だけ `<!-- TODO: 読み -->` に落とし、
**どの数が出せなかったかを標準エラーへ出す**(黙って省かない)。

- 表示名は `--name` で受け取る(この道具は名前を自分の中に持たない)。
- 「読み」の文・「こうしてみては」の行・「例」の節・「取り下げたこと」・「やらなくていいこと」・
  「次の 20 局」の表は `<!-- TODO: 読み -->` のプレースホルダで空ける(人と LLM の仕事)。
  「この冊子の約束」は数を含まないので固定文。
- 実測(固定材料 44 局、基準版と同じ材料): 事実の箇条書き **14 / 14** を生成し、基準版の同じ 4 ブロックと
  **数の一覧が順序つきで完全一致**(118 個)、かつ**文字まで同一**。生成物は `check_answer.py` rc=0。

### 伏せ字・個人情報の検査(`report-pdf/check_delivery.py`)

`<out>` 直下の `*.pdf`(`fitz` でテキスト抽出)と `*.md` に、`--forbid` の語・`@`・`/Users/`・「水匠」・`None`(python の None が印字された跡。凍結の例外 12 件目)・
が無いことを確かめる。**禁止語は無し**(2026-09-25 の人間の決定で機械の禁止語は無し(凍結の例外 14 件目)。`check_answer.py` の `BANNED_WORDS` を import する形は
そのままで、一覧が空)。`direct/` の JSON は対象外。

- 実測(例外 14 より前。固定材料の納品フォルダ 7 本 = PDF 5 冊 + md 2 本): 禁止語 18 語・`@`・`/Users/`・「水匠」は **0 件**(rc=0)。
- **注意**: `--forbid` に**お客さま自身の表示名**を渡すと必ず落ちる(本人の冊子には本人の名前が出るのが正しい)。
  実測では `--forbid <表示名>` で 42 件(本編・付録 1・B の本文)。`--forbid` は「出てはいけない語」
  (相手の名前など)に使う。

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```

## 不変条件のテスト

```
npx vitest run scripts/playtest
```
