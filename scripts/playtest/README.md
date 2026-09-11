# scripts/playtest/

対局ハーネス(docs/PLAYTEST_LOOP_PROPOSAL.md の外側のループ)。**開発補助であり、本番導線(apps/)には含めない。**

現在実装済みなのは STEP T-1(固定棋譜モード)・STEP T-2(不変条件 I-1〜I-5・draft と集約報告)・STEP T-3(探索モードと対局者の多様化)・STEP T-5(比較の道具 `compare.ts`・分母の報告・表記の更新)・STEP T-6(回帰モードのエンジン条件の固定・不変条件の型「結果」・I-6(draft))・STEP T-7(エンジンの参考評価 `engineReference` の記録・I-7(draft))。

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

T-1 が保存した JSONL(1件以上)に対して、不変条件 I-1〜I-7(`scripts/playtest/invariants/`。**I-1・I-2 は 2026-09-11 に人間承認で `status: "approved"`、他(I-3〜I-7)は `status: "draft"`**)を適用し、検出を「型 × 発生条件」で束ねた報告を標準出力(Markdown)へ書く。常に exit 0(`approved` を含め、検出は何もブロックしない。exit code の扱い自体は人間承認事項)。

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

## typecheck

```
npx tsc --noEmit -p scripts/playtest/tsconfig.json
```

## 不変条件のテスト

```
npx vitest run scripts/playtest
```
