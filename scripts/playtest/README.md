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
- 欄の並び: 側を決めない `{ id, source, ending, moves }` / 本人が先手 `{ id, source, mirrored, ending, moves }` / 本人が後手 `{ id, source, mirrored, originalUserSide, plyOffset, startSfen, ending, moves, originalMoves }`

## JSONL の形式

- 先頭行: `{"kind":"meta", "kifuId", "startedAt", "gitHead", "enginePath"}`(固定棋譜モードは STEP T-6 で `searchMode`・`nodes`・`threads`、STEP T-7 で `referenceNodes` を追加。探索モードは `mode: "explore"`・`profile` 等、STEP T-7 で `referenceNodes` を追加。上記参照)
- 各記録行: `{"kind":"record", "ply", "sfen", "senteMove", "goteMove", "phase":"immediate"|"ready", "elapsedMs", "response", "engineReference"}`(`response` は `buildStateResponseWithPlan` の戻り値そのまま。web が受け取るのと同じ形。`engineReference` は STEP T-7 で追加した ready 行のみのフィールド。下記「エンジンの参考評価(STEP T-7)」参照。immediate 行にはキー自体が無い)
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

## 一本の流れ(`pipeline.ts`。STEP PIPE 作業 A)

`scripts/playtest/pipeline.ts` は、S1(読み込み)〜S4(判定)の 4 段を**既存の道具を子プロセスで呼ぶ順に並べるだけ**の道具である(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1)。**S1〜S4 のどの道具の中身も複製・改変しない**。将棋の判断・閾値・文言はここでは一切書かない。

```
npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir>
  [--me <名前>] [--parallel <N=5>]
  [--compare-dir <段2の記録のフォルダ …> --compare-person <p記号>]
  [--until import|evaluate|diagnose|gate] [--evaluator "<評価関数の識別>"] [--dry-run]
```

- **段**: S1 `kifu-import-check.ts`(読み込み)→ S2 `replay.ts`(軽い値。nodes/reference-nodes 400,000・threads 1・direction-rule current)→ `rescreen.ts`(深い値。deep-nodes 4,000,000)→ S3 `diagnose.ts`(1 人ぶんまとめて)→ S4 `gate.ts`(`--compare-dir` があるときだけ)。引数の値は固定(表と違う値を渡す旗は無い)
- **先後**: `--me <名前>` を全局へ渡すか、`--me` を渡さなければ局ごとにファイル名の末尾 `-sente`/`-gote` を読む(id はそれを除いた部分)。どちらも無ければ**推測せずに止まる**
- **途中から再開できる**: 段ごと・局ごとに、出力があって完結していれば(段 1 は最後の行が `summary`、段 2 は空でない、fixed 棋譜は `id`・`moves` がある、診断は 4 つの出力がすべてある、gate は出力がある)飛ばす
- **並行**: `--parallel`(既定 5)を上限にした局ごとのジョブの列。1 局の失敗で他は止めず、最後に失敗の一覧と `exitCode ≠ 0`
- **所要**: 局ごとの開始・終了・rc を `<work>/timing.jsonl` に書く
- **`--source` は絶対パスにしない**: `kifu-import-check.ts --source` には `--kifu-dir` からの相対パス(ファイル名そのもの)を渡す(絶対パスを固定棋譜に残さないため)。第一引数(道具が実際に読む場所)は指定どおりのパスのまま
- **S4(`gate.ts`)の向き(2026-09-21 の直し)**: **材料の側 = このお客さん**(`--person`・`--kifu-dir` の局。`gate.ts` の `--person`・`--material`)、**試す側 = `--compare-dir` の記録**(`gate.ts` の `--test-person`・`--test-sente`/`--test-gote`)。2 人目 20 局(材料)を 1 人目 10 局(試す側)で確かめた C-1・C-5 の正式な実行と同じ向き(docs/STEP_D3-COND_PLAN_2026-09-15.md §14・§15.2)。`--compare-dir` の記録の先後は**各記録の meta 行(`mirrored`・`originalUserSide`。`replay.ts` が書く。`lib/sideAlignment.ts` の `sideMetaFields`)から読む**。ファイル名には頼らない(比較対象のフォルダに命名の規約は無い)。meta から決められない記録が 1 件でもあれば、推測せずこの段を失敗にして理由(ファイル名)を出す
- **`--compare-person`**: 計画の CLI には試す側の人のラベルを渡す旗が無かったため、`gate.ts` が要求する「試す側の人のラベル(p1・p2 の記号)」を渡すための `--compare-person` を新設した(`--compare-dir` と必ず一緒に渡す)。`--person`(材料)には `--person` の値をそのまま使う
- **`--records-append` は決して付けない**。`records/` へは一切書かない(棄却の記録へ書くのは、予測を先にコミットした正式な実行だけで、司令塔が手で回す)
- **試験はエンジンも子プロセスも起こさない**: fs・道具の実行(`ToolRunner`)を注入できる形にし、段の順序・済みの飛ばし・並行の上限・1 局の失敗が他を止めないこと・引数の固定・`--until`・`--dry-run`・gate の材料/試す側の向き・meta から本人の側が決められない記録の扱いを `scripts/playtest/lib/pipeline.test.ts` で見張る

`--dry-run` は何も書かず・何も実行せず、段ごとの `run`/`skip` とその引数を表示するだけ(`diagnose`/`gate` のプレビューは、その時点ですでに段 2 まで済んでいる局だけを対象にする。これから実行して済むはずの局は、実行するまで成否が分からないため含めない)。

S5(レポートの材料)以降は別 STEP(作業 B)で、`pipeline.ts` にはまだつながっていない。段の一覧(`STAGES`、`lib/pipeline.ts`)は配列なので、後で司令塔が足せる。

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```

## 不変条件のテスト

```
npx vitest run scripts/playtest
```
