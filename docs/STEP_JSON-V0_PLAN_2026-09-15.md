# STEP JSON v0(番号は仮)計画: `diagnose.ts --events` の Failure Event JSON を版付きのスキーマにする(2026-09-15)

**状態**: 計画。**計画レビュー済み(司令塔、2026-09-15。J-1〜J-8 を推奨どおり決定し、(a)〜(c) を足した ― 9.)。**この計画書では実装しない。

**担当**: 実装 A、監査 B(D-COST の実装の後)。

---

## 0. この STEP の位置づけ(**先に書く**)

- **人間の決定(2026-09-15)**: [BUSINESS_CONCEPT_2026-09-15.md](BUSINESS_CONCEPT_2026-09-15.md) 4. の 6「Failure Event JSON を版付きの契約にする(JSON スキーマ v0。`diagnose.ts --events` の形を固定して版番号を付ける)」、[DIAGNOSIS_CONCEPT_2026-09-14.md](DIAGNOSIS_CONCEPT_2026-09-14.md) 8. の **JSON v0**(「項目を増やすときは版を上げる」)
- **将来の API の契約の下書き**である。**API サーバー・認証・DB は作らない**(6.)
- この STEP で決めるのは「**いまの 1 行が何を持ち、何を約束し、どう壊れたら気づくか**」。**項目の意味や判定は変えない**(D1 の lib の値をそのまま写す)
- **エンジンは使っていない。**下の実物は、コミット済みの記録に HEAD `011087a` の `diagnose.ts` を掛けた出力を読んだだけ

---

## 1. 実物から分かった前提(**読みで書かず、場所で書く**)

| # | 事実 | 場所 |
|---|---|---|
| E-1 | `--events` は **1 行 1 Failure Event の JSONL**。`JSON.stringify(event)` をそのまま書く。**版の欄も出どころの欄も無い** | `scripts/playtest/diagnose.ts:52-54` |
| E-2 | 1 行の型は `FailureEvent` | `scripts/playtest/lib/failureEvent.ts:281-298` |
| E-3 | `trigger.evaluationBefore` は **6 変種の判別ユニオン**(`state` で分かれ、値の 6 欄は `measured` にだけある) | 同 `:58-82` |
| E-4 | `trigger.focus` は 4 変種(`text` は `stated` だけ)、`trigger.shape` は 2 変種(`status`・`refersToShapeId` は `recorded` だけ)、`trigger.opponentIntent.classification` は 5 変種(`reason` は `undetermined` だけ、値は `U-1`〜`U-8`) | 同 `:225-238`、`scripts/playtest/lib/intentStatement.ts:34-52` |
| E-5 | 値の元は `engineReference`(`baseline.scoreCp`/`mate` は**手番側の視点**、`afterPass` は**先手がパスした後の手番 = 後手の視点**、`dropCp` = `baseline.scoreCp − (−afterPass.scoreCp)` で両方 cp のときだけ) | `apps/server/src/analysis/engineReference.ts:36-57` |
| E-6 | **既存の検証器 `scripts/validate-data.mjs` は外部ライブラリを使わない手書き**で、対応するキーワードは `type`・`enum`・`pattern`・`minimum`/`maximum`・`properties`・`required`・`additionalProperties`・`minItems`・`items` だけ。**`oneOf`・`const` が無く、E-3・E-4 の判別ユニオンを書けない** | `scripts/validate-data.mjs:50-104`、[TESTING_STRATEGY.md](TESTING_STRATEGY.md) 13 行(「Node.js 標準機能のみ」) |
| E-7 | リポジトリに JSON Schema の検証ライブラリ(ajv など)は**入っていない** | ルートと `apps/server` の `package.json`・`node_modules` |
| E-8 | **`kifuId` は評価関数をまたいで一意ではない**: MATERIAL 版の `out/obs2/obs2-claude-2.jsonl` と NNUE 版の `records/d0-nnue/…claude-2-round2.jsonl` は、どちらも `kifuId` が `2026-09-12-live-30moves-claude-2-round2` で、**分岐点 19 の Failure Event が両方に出る**(値は違う) | 5. の実測 |
| E-9 | **EvaluationBefore / EvaluationAfter / CheckWithin / Mate** は、**人間の提示(2026-09-15)の 9. の名前**である。[BUSINESS_CONCEPT_2026-09-15.md](BUSINESS_CONCEPT_2026-09-15.md) には本文を写していない(`docs/` を `grep -riE "evaluation.?before\|evaluation.?after\|check.?within"` しても出ない)(司令塔、2026-09-15) | — |
| E-10 | **EvaluationAfter にあたる欄は無い**。`trigger.evaluationBefore.scoreCp + branch.diffCp` で導ける(直後の行の `baseline.scoreCp`) | `failureEvent.ts:151`(`pairEvaluations` で `diffCp` = 直後 − 直前)・`:380`(Failure Event に写す) |

---

## 2. 1 行の項目(**v0.1 の契約にするもの**)

**葉の欄 32 個 + 版の欄 1 個 = 33 個**(入れ物のオブジェクトは 10 個: `trigger`・`evaluationBefore`・`opponentIntent`・`classification`・`shape`・`focus`・`action`・`branch`・`consequences`・`candidateModes` の要素)。

### 2.1 「無い」の規約(**3 種を混ぜない。AGENT_PROTOCOL 11.6**)

JSON には `undefined` が無いので、TypeScript の 3 種は JSON では次の 3 つになる。

| 形 | 意味 | どこで使うか |
|---|---|---|
| **キーが無い** | **その変種にはその欄が無い**(判別ユニオン)。「値が無い」ではない | `evaluationBefore` の値 6 欄(`state` ≠ `measured`)・`focus.text`(≠ `stated`)・`classification.reason`(≠ `undetermined`)・`shape.status` と `shape.refersToShapeId`(≠ `recorded`) |
| **`null`** | **欄はあるが、値が無い**(その理由は欄ごとに下の表) | 数や手の欄 |
| **`[]`** | **見た範囲で 0 件だった**。**見た範囲は `consequences.windowShort` と一緒に読む**(`true` なら「窓の途中までしか見ていない」) | `consequences.checks`・`candidateModes` |

**0 や `false` や空文字で「無い」を埋めない。**`kinds` と `matchedBy` は必ず 1 件以上(`[]` にならない)。

### 2.2 項目の表

単位: **ply** = 開始局面からの手数(1 始まり。先手の手は奇数、後手の手は偶数)。**cp** = センチポーン(整数)。**視点**は各欄に書く。

| 欄 | 型 | 意味・単位 | 取りうる値 | `null` / キーが無いとき | 元 |
|---|---|---|---|---|---|
| `schemaVersion` | string | **この行の版(新設)** | `"0.1"` | 無いことは無い | 3. |
| `kifuId` | string | 記録の識別(meta 行の `kifuId`、無ければファイル名) | 任意の文字列。**評価関数をまたいで一意ではない(E-8)** | 無いことは無い | `diagnose.ts:29-37` |
| `branchPly` | integer | 分岐点の手(先手の手)の ply | 奇数・≥ 1 | 同上 | `failureEvent.ts:283-284` |
| `fromReadyPly` / `toReadyPly` | integer | 比べた 2 つの ready 行の ply(`branchPly − 1` / `branchPly + 1`) | 偶数・≥ 0 | 同上 | 同 `:285-286` |
| `trigger.evaluationBefore.state` | string | 直前の行の評価の状態 | `measured`・`notMeasuredGameEnd`・`notMeasuredInCheck`・`notMeasurable`・`unrecorded`・`notEvaluation` | 無いことは無い | 同 `:58-82` |
| `….scoreCp` | integer \| null | 直前の行の評価(**先手視点**の cp) | 絶対値 < 30000(D-6 で 30000 以上は `notEvaluation`) | `null` = mate で返った。**キーが無い = `measured` でない** | E-5 |
| `….mate` | integer \| null | 直前の行の詰みの手数(**先手視点**。負 = 先手が詰まされる) | 0 以外の整数 | `null` = cp で返った | E-5 |
| `….bestmove` | string \| null | 直前の行のエンジンの最善手(USI) | USI の手 | `null` = エンジンが返さなかった | E-5 |
| `….afterPassScoreCp` | integer \| null | 先手がパスした後の評価(**後手視点**の cp) | 絶対値 < 30000 | `null` = mate で返った・測っていない | E-5 |
| `….afterPassMate` | integer \| null | 先手がパスした後の詰みの手数(**後手視点**。正 = 先手がパスすると後手が詰ませる = 詰めろ相当) | 0 以外の整数 | 同上 | E-5 |
| `….dropCp` | integer \| null | パスしたときの落ち幅(**先手視点**)= `scoreCp − (−afterPassScoreCp)` | 整数 | `null` = **両方 cp ではなかった**(0 ではない) | E-5 |
| `trigger.opponentIntent.classification.column` | string | 直前の行の②の分類(U6-I4) | `noCandidate`・`muted`・`spokeLatest`・`spokeOlder`・`undetermined` | 無いことは無い | `intentStatement.ts:47-52` |
| `….classification.reason` | string | 分類できなかった理由 | `U-1`〜`U-8` | **キーが無い = `undetermined` でない** | 同 `:34-43` |
| `trigger.opponentIntent.refersToIntentId` | string \| null | ②が名指しした狙いの id(`data/intents/`) | 狙いの id | `null` = 名指ししていない | `failureEvent.ts:264-267` |
| `trigger.shape.state` | string | 直前の行の形(coach の `current_shape`)を記録していたか | `recorded`・`unrecorded` | 無いことは無い | 同 `:238` |
| `trigger.shape.status` | string | 形の段階 | `none`・`forming`・`completed` など(**本番の値をそのまま写す。v0.1 では列挙で固定しない** ― 4. の J-6) | **キーが無い = `unrecorded`** | 同 `:268-271` |
| `trigger.shape.refersToShapeId` | string \| null | 形の id(`data/shapes/`) | 形の id | `null` = 名指ししていない。キーが無い = `unrecorded` | 同上 |
| `trigger.focus.state` | string | 直前の行の③の状態 | `stated`・`nothingToSay`・`pending`・`unrecorded` | 無いことは無い | 同 `:225-236` |
| `trigger.focus.text` | string | ③の文(**そのまま写す。中身で分けない**) | 任意の文字列 | **キーが無い = `stated` でない** | 同上 |
| `action.playedMove` | string \| null | 分岐点で実際に指した手(USI) | USI の手 | `null` = 棋譜に無い(**今の組み立てでは起きない**) | 同 `:288`・`:375` |
| `action.bestmoveAtBefore` | string \| null | 直前の行の最善手 | USI の手 | `null` = **直前が `measured` でない、または最善手が無い**(**2 つの理由が 1 つの `null` に畳まれる**。区別は `evaluationBefore.state` で読む ― 7. の L-3。v0.2 の候補 ― 3.3) | 同 `:288` |
| `branch.kinds` | string[] | 分岐点で何に当たったか | 要素は `cpDrop`・`mateDrop`・`matedIfPass`。**1 件以上** | `[]` にならない | 同 `:279` |
| `branch.diffCp` | integer \| null | 直後の行 − 直前の行の評価(**先手視点** cp、**2 手分**) | 整数 | `null` = 組が cp どうしでなかった(直後が mate・比べていない) | 同 `:151`・`:380` |
| `branch.mateAfter` | integer \| null | 直後の行の `baseline.mate`(先手視点) | 0 以外の整数 | `null` = 直後が mate でない | 同 `:292` |
| `branch.matedIfPassAfter` | boolean | 直後の行で `afterPassMate > 0` だった | `true`・`false` | 無いことは無い | 同 `:293-294` |
| `consequences.checks` | integer[] | 窓の中で、後手の手の後に自玉が王手を受けた ply | 偶数の ply の昇順 | `[]` = 見た範囲で無かった(`windowShort` と読む) | 同 `:165-172` |
| `consequences.mate` | integer \| null | 窓の中で自玉が詰んだ ply(後手の勝ちの詰みだけ) | 偶数の ply | `null` = 見た範囲で無かった(`windowShort` と読む) | 同上 |
| `consequences.windowPlies` | integer | 窓の長さ(ply。規則の値 ― 今は 5) | ≥ 0 | 無いことは無い | 同上 |
| `consequences.windowShort` | boolean | 窓が棋譜の終わりを越え、終局もしていない(**「起きなかった」ではない**) | `true`・`false` | 無いことは無い | 同上 |
| `candidateModes[].mode` | string | 死因の型 | `mate_threat` | — | 同 `:297` |
| `candidateModes[].status` | string | 候補の確からしさ | `draft` | — | 同上 |
| `candidateModes[].matchedBy` | string[] | どの当たり方で候補になったか | `branch.kinds` と同じ値。1 件以上 | — | 同上 |

---

## 3. 版番号と、版を上げる規則

### 3.1 版の欄

- **各行に `schemaVersion` を置く**(決定。J-1)。JSONL の行を 1 行だけ切り出して渡しても、版が分かる
- 形は **`"MAJOR.MINOR"` の文字列**。最初の版は **`"0.1"`**
- **v0.1 の中身は、2. の今の欄 + `schemaVersion` だけ**(決定。J-2)。今の出力に 1 欄足すだけで、値は 1 つも変えない

### 3.2 版を上げる規則(**依頼の規則 + 境目の決め方**)

| 変更 | 版 | 理由 |
|---|---|---|
| **任意の欄を足す**(読む側が知らなくても、既存の欄の意味が変わらない) | **MINOR** | 依頼の規則 |
| **欄を消す・名前を変える・型を変える** | **MAJOR** | 依頼の規則 |
| **既存の欄の意味・単位・視点を変える**(例: `diffCp` を後手視点にする、窓を ply から「手の組」にする) | **MAJOR** | 依頼の規則。**値の形が同じでも意味が変われば MAJOR** |
| **列挙の値を足す**(例: `kinds` に死因②、`evaluationBefore.state` に新しい状態) | **MAJOR**(決定。J-5) | 読む側は列挙の値で分岐する(「知らない値」を黙って落とすと、「無い」を 0 にするのと同じ誤りになる) |
| **判断的知識の値(閾値)を変える**(例: −400 → −300、30000 → 32000) | **欄の形は変わらないので版は上げない**。**ただし出どころの欄(0.2 の候補 ― J-3)に規則の値を書く** | 同じ版でも、規則が違えば同じ棋譜から違う Failure Event が出る。版は「形の約束」、規則は「中身の条件」で、分けて持つ |

- **`0.x` の間は外部に互換を約束しない**(決定。J-4)。**`1.0` は Gate 3 以降に人間が決める**(企業に出す約束になるため。CLAUDE.md の「外部へ公開する判断」)
- 版を上げたら、**スキーマのファイルを版ごとに 1 つ増やし、古い版のファイルは消さない**(古い記録を検証できるように)

### 3.3 v0.2 の候補(**この STEP では入れない。D3 の後に計画する**(司令塔、2026-09-15))

| 候補 | 何のため | 版 |
|---|---|---|
| `evaluationAfter`(直後の行の状態 + 値。`evaluationBefore` と同じ形) | EvaluationAfter を導出でなく欄で持つ(E-10)。`diffCp` が `null` のとき直後の状態が分からない | MINOR |
| `provenance`(**記録のパス・`gitHead`・評価関数の識別**。あわせて `dirty`・`nodes`・規則の値 `DRAFT_RULE_1` と `NOT_EVALUATION_CP` を持つかも、そのとき決める) | **E-8**: `kifuId` だけでは MATERIAL と NNUE の同じ分岐点を取り違える。企業に出す Evidence には「どの条件で出た値か」が要る(P-43 のため評価関数の識別は meta から取れない) | MINOR |
| **`bestmoveAtBefore` の `null` の 2 つの理由を分ける**(L-3。例: 理由の欄を足す) | 「直前が `measured` でない」と「最善手が無い」を 1 行で読めるようにする | 欄を足すなら MINOR、`null` の意味を変えるなら MAJOR(そのとき決める) |

---

## 4. 決定(司令塔、2026-09-15。**J-1〜J-8 はすべて推奨どおり**)

| # | 判断 | 決定 | 選ばなかった案 |
|---|---|---|---|
| **J-1** | 版の欄の位置 | **各行に `schemaVersion`** | 先頭に見出しの行を 1 行置く(行を切り出すと版が消える) |
| **J-2** | v0.1 の中身 | **今の欄 + `schemaVersion` だけ**(値は変えない) | v0.1 から `evaluationAfter`・`provenance` を入れる(D1 の lib を変える STEP になり、監査の範囲が広がる) |
| **J-3** | スキーマの置き場所 | **`scripts/playtest/schemas/failure-event.v0.1.schema.json`**(`data/schemas/` と分ける) | `data/schemas/failure-event.schema.json` |
| **J-4** | `0.x` の互換の約束 | **外部に約束しない。`1.0` は Gate 3 以降に人間が決める** | 0.x から MINOR の互換を約束する |
| **J-5** | 列挙の値を足すとき | **MAJOR** | MINOR(0.x の間だけ) |
| **J-6** | `shape.status` の値を列挙で固定するか | **固定しない(`string`)**。本番の `CoachExplanation.status` の値をそのまま写す欄で、値の集合は本番側の型が持つ | 列挙で固定する(本番に値が増えたら MAJOR になる) |
| **J-7** | 検証器 | **外部ライブラリを足さない。`validate-data.mjs` と同じ方針で、`oneOf` と `const` だけを足した小さな検証器を `scripts/playtest/lib/` に置く**(E-6・E-7)。**検証器自身に固定例と変異を付ける**(6.2 の T-1・6.3) | ajv を devDependency に足す(TESTING_STRATEGY の方針を変える判断。**`1.0` のときに改めて判断する**) |
| **J-8** | `additionalProperties` | **版ごとのスキーマは `false`**(知らない欄が出たら赤)。**型に欄を足してスキーマを直し忘れたら、試験が落ちる** | `true`(読む側の寛容さを先取りする。直し忘れに気づけない) |

**J-3 の理由**: `data/schemas/` は将棋の知識(形・戦型・狙い・説明)のスキーマで、`validate-data.mjs` が `data/<type>/` と組にして読み、ID の相互参照も見る(E-6)。Failure Event は**解析の出力**で、知識ではない(CLAUDE.md の知識の 3 種のどれでもない)。同じ場所に置くと、`validate-data.mjs` の対象の型の一覧(`data/examples/<type>.example.json` の前提)にも混ざる。

---

## 5. 期待値(**測る前に書く。項目は数える前に型から書いた**)

### 5.1 実記録の出力(**計画を書くために HEAD `011087a` で実際に回した。エンジン不使用**)

| 対象 | Failure Event | 備考 |
|---|---|---|
| `scripts/playtest/records/d0-nnue/` 7 本(`0cce0c3`) | **22** | exit 0 |
| 既存 6 本(`out/u6l` 4・`out/obs2/obs2-claude-2`・探索 `game-01`) | **19** | exit 0。**`out/` は gitignore の対象で、試験には置けない** |

**41 件で実際に現れた変種**: `evaluationBefore.state` は `measured` だけ(41)/ `focus` は `stated` 29・`nothingToSay` 12 / `shape` は `recorded` だけ(`none` 25・`forming` 9・`completed` 7)/ `classification.column` は `spokeLatest` 18・`spokeOlder` 13・`muted` 5・`noCandidate` 5 / `kinds` は `cpDrop` 40・`matedIfPass` 1 / `checks` が 1 件以上 3 / `windowShort` が `true` 10 / `candidateModes` はすべて `[]` / `mateAfter`・`consequences.mate` はすべて `null`。**2.2 の葉 32 個のうち、41 件に現れたのは 28 個**(現れないのは `classification.reason` と `candidateModes[]` の 3 欄の、計 4 欄)。

### 5.2 予測

| # | 予測 | 根拠 | 外れる条件 |
|---|---|---|---|
| **P-1** | v0.1 の葉の欄は **33 個**(今の 32 個 + `schemaVersion`)、入れ物は 10 個 | 2.2 を型(`failureEvent.ts:58-82`・`:225-298`、`intentStatement.ts:47-52`)から数えた | 実装で型に無い欄が JSON に出る、または型にある欄が JSON に出ない |
| **P-2** | **既存 6 本 + d0-nnue 7 本の 41 件は、すべて v0.1 のスキーマを通る**(`schemaVersion` を足した出力で) | 41 件の変種(5.1)はすべて 2.2 の値域の中 | 1 件でも通らなければ、2.2 の読み違いかスキーマの誤り |
| **P-3** | **ただし 41 件が通っても、スキーマの半分は試されない**(`evaluationBefore` の 5 変種・`focus` の 2 変種・`shape.unrecorded`・`undetermined`・`mateDrop`・`candidateModes` の中身・`consequences.mate` の数) | 5.1 | — |
| **P-4** | D1 の固定例から作る Failure Event で、**P-3 の穴のうち `mateDrop`・`mateAfter` の数・`candidateModes` の中身・`evaluationBefore.unrecorded`・`focus.pending`・`focus.unrecorded`・`windowShort: true` は埋まる。`consequences.mate` の数・`evaluationBefore` の残り 4 変種・`shape.unrecorded`・`muted`/`spokeOlder`/`undetermined` は埋まらない** | 計画を書くために、`lib/failureEventFixtures.ts` の植え方で 6 通りの記録を作り、出る変種を数えた(使い捨ての確認。**判断の根拠ではなく観測**) | 実装の STEP で固定例を足せば埋まる(6.2 の T-3) |

---

## 6. 実装の STEP でやること(**ここでは実装しない**)

### 6.1 足すもの

| ファイル | 中身 |
|---|---|
| `scripts/playtest/schemas/failure-event.v0.1.schema.json`(新規) | 2. の表をそのまま JSON Schema にしたもの。判別ユニオンは `oneOf` + `const`。**`additionalProperties: false`**(J-8) |
| `scripts/playtest/lib/eventSchema.ts`(新規) | 小さな検証器(J-7)。`validate-data.mjs` の対応キーワード + `oneOf`・`const`。**`oneOf` はちょうど 1 つに合うことを見る** |
| `scripts/playtest/lib/failureEvent.ts` | `FAILURE_EVENT_SCHEMA_VERSION = "0.1"` と、書き出す形(`{ schemaVersion, ...event }`)を作る関数 1 つ。**値は変えない** |
| `scripts/playtest/diagnose.ts` | `--events` の 1 行を上の関数で作る(照合の 1 行を差し替える) |

### 6.2 試験(**validate の試験**)

| # | 見るもの | 固定例 |
|---|---|---|
| T-1 | 検証器そのもの: `oneOf` がちょうど 1 つ、`const`・`required`・`additionalProperties: false`・`items`・`minItems` が期待どおりに赤・緑になる | 小さなスキーマと値の組(**先に赤を確かめる**) |
| T-2 | **D1 の固定例から作った Failure Event がすべて通る**(`schemaVersion` 付き) | `failureEvent.test.ts` の植え方(5.2 の P-4 の 6 通り) |
| T-3 | **P-3 の穴を埋める固定例**: `evaluationBefore` が `notMeasuredGameEnd`・`notMeasuredInCheck`・`notMeasurable`・`notEvaluation` で `matedIfPass` だけの Failure Event / `shape.unrecorded` / `classification` が `undetermined` / `consequences.mate` が数 | 植え方を足す(**変種ごとに 1 件**) |
| T-4 | **コミット済みの記録 `records/d0-nnue` 7 本の Failure Event 22 件がすべて通る** | lib で組み立てて検証(`out/` は使えない) |
| T-5 | **型とスキーマのずれ**: 型にある欄を 1 つずつ消した値・知らない欄を足した値が赤になる | T-2 の 1 件を元に作る |
| T-6 | `diagnose.ts` の配線: 子プロセスの `--events` の各行に `schemaVersion: "0.1"` があり、スキーマを通る | 既存の子プロセスの試験を広げる |

### 6.3 変異(**中心を壊すものを入れる ― 規則 11.8**)

- スキーマの `required` から `consequences.windowShort` を消す → T-5 が鳴る
- lib が `evaluationBefore` に欄を 1 つ足す(スキーマは直さない)→ T-2・T-4 が鳴る(J-8)
- 検証器の `oneOf` を「1 つ以上に合えばよい」にする → T-1 が鳴る
- `schemaVersion` を書かない → T-6 が鳴る
- `focus.text` を `stated` 以外にも `""` で出す(「無い」を空文字にする)→ T-2 が鳴る

---

## 7. やらないこと・限界

### 7.1 やらないこと

- **API サーバー・認証・DB**(依頼の (5))
- 項目の意味・判定・閾値を変えること(D1 の lib の値をそのまま写す)
- `evaluationAfter`・`provenance` を v0.1 に入れること(3.3。J-2)
- `data/schemas/` と `validate-data.mjs` を変えること(J-3)
- `1.0` と外部への互換の約束(J-4。人間が決める)
- ajv などの外部ライブラリを足すこと(J-7。`1.0` のときに改めて判断する)

### 7.2 限界

- **L-1 評価関数は 1 行から分からない**(E-8・P-43)。v0.1 の Evidence は「どの記録から出たか」を行の外(記録のファイルと meta)で持つ
- **L-2 `kifuId` は評価関数・再生をまたいで一意ではない**(E-8)。v0.1 の 1 行を集めて数えるときは、記録のファイルと組にする
- **L-3 `action.bestmoveAtBefore` の `null` は 2 つの理由を畳む**(2.2)。`evaluationBefore.state` と組で読む。**分けるのは v0.2 の候補**(3.3)
- **L-4 実記録 41 件が通っても、スキーマの半分は試されない**(5.2 の P-3)。**変種を固定例で埋めるのは実装の STEP の仕事**(T-3)
- **L-5 スキーマは形を約束するが、中身の条件(閾値)は約束しない**(3.2)

### 7.3 既知事項の候補(**番号は司令塔がコミットのときに採る**)

- **`kifuId` は評価関数(と再生)をまたいで一意ではない**(E-8)。MATERIAL 版の `out/obs2/obs2-claude-2.jsonl` と NNUE 版の `records/d0-nnue/2026-09-12-live-30moves-claude-2-round2.jsonl` は、どちらも `kifuId` が `2026-09-12-live-30moves-claude-2-round2` で、分岐点 19 の Failure Event が両方に出る(値は違う: 直前 −3388 / −3517、差 −916 / −410)。**Failure Event を記録をまたいで集めるときは、記録のファイル(と評価関数の識別)と組にしないと取り違える。**v0.2 の `provenance` の候補(3.3)

---

## 8. Evidence として企業に見せる最小の形(**例 1 件。今の項目名で**)

**元**: NNUE 版の記録 `scripts/playtest/records/d0-nnue/2026-09-12-live-30moves-claude-2-round2.jsonl`(`0cce0c3`、記録の gitHead `a9da058`・汚れなし・nodes 4,000,000)の、分岐点 19 の Failure Event(HEAD `011087a` の `diagnose.ts --events` の出力をそのまま切り出し、`schemaVersion` だけ足した)。**死因①(draft)は付いていない例である**(直前が優勢でないため)。

**依頼文の 4 つの名前と、今の項目の対応**

| 依頼文の名前 | 今の項目 | この例の値 | 読み方 |
|---|---|---|---|
| **EvaluationBefore** | `trigger.evaluationBefore.state` と `.scoreCp`(`.mate`) | `measured`・**−3517** | 分岐点の直前の局面の評価(先手視点 cp) |
| **EvaluationAfter** | **欄は無い(E-10)**。`trigger.evaluationBefore.scoreCp + branch.diffCp` | −3517 + (−410) = **−3927** | 直後の局面の評価(先手視点 cp)。**v0.2 の候補(3.3)** |
| **CheckWithin** | `consequences.checks` と `consequences.windowPlies`・`consequences.windowShort` | **`[22]`**・5・`false` | 分岐点の手から 5 手の実戦の続きで、22 手目の後手の手で自玉に王手。窓は最後まで見た |
| **Mate** | `consequences.mate` | **`null`** | 見た窓の中で自玉は詰んでいない(`windowShort: false` なので「見ていない」ではない) |

**最小の形(今の項目名のまま、4 つに要る欄だけを残した切り出し)**

```json
{
  "schemaVersion": "0.1",
  "kifuId": "2026-09-12-live-30moves-claude-2-round2",
  "branchPly": 19,
  "trigger": { "evaluationBefore": { "state": "measured", "scoreCp": -3517, "mate": null } },
  "action": { "playedMove": "1i1h", "bestmoveAtBefore": "P*8e" },
  "branch": { "kinds": ["cpDrop"], "diffCp": -410, "mateAfter": null },
  "consequences": { "checks": [22], "mate": null, "windowPlies": 5, "windowShort": false },
  "candidateModes": []
}
```

- **この切り出しは v0.1 のスキーマを通らない**(`required` の欄を落としている)。**見せ方の例であって、別のスキーマではない**。企業向けに切り出した形を契約にするなら、それは別の版(または別のスキーマ)として決める
- **同じ `kifuId`・分岐点 19 の Failure Event が MATERIAL 版の記録にもある**(E-8)。**この例を見せるときは、記録のファイルと評価関数(nn.bin の sha256 ― U6-T2)を必ず並べる**

---

## 9. 決定(司令塔の計画レビュー、2026-09-15)

| # | 決定 |
|---|---|
| J-1〜J-8 | **すべて 4. の推奨どおり。**J-2: v0.1 は今の欄 + `schemaVersion` だけ(値は変えない)/ J-5: 列挙の値の追加は MAJOR(読む側が値で分岐するため)/ J-7: 外部ライブラリは足さず、`oneOf` と `const` だけの小さな検証器を置く。**検証器自身に固定例と変異を付ける。ajv は `1.0` のときに改めて判断** |
| (a) | v0.2 の候補(`evaluationAfter`、`provenance` = 記録のパス・gitHead・評価関数の識別)は **D3 の後に計画する**(3.3)。E-8 は既知事項の候補として 7.3 に置く(番号はコミットのときに司令塔が採る) |
| (b) | E-9 の名前は「人間の提示(2026-09-15)の 9. の名前。BUSINESS_CONCEPT には本文を写していない」と書く(1. の E-9) |
| (c) | L-3(`bestmoveAtBefore` の `null` が 2 つの理由を畳む)を v0.2 の候補に入れる(3.3) |
| 担当 | 実装 A、監査 B(D-COST の実装の後) |
| 次 | この計画書のコミットの後、A が実装する: スキーマ・検証器・試験 T-1〜T-6・変異、`diagnose.ts` に `schemaVersion` を足す最小の変更 |
