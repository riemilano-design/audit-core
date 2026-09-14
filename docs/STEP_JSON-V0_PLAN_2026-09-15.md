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
- **`scripts/validate-data.mjs` の検証器も、プロトタイプの名前の欄を通す形になっている**(JSON v0 の監査 B の必須 1 の参考。**この STEP の範囲外なので直していない** ― 司令塔の決定、2026-09-15)。`:83` の `key in instance`(必須の欄)・`:88` の `key in props`(知らない欄)・`:92` の `props[key]` が Object.prototype を辿るので、`data/` の JSON に `constructor`・`toString` などの名前の知らない欄があっても赤にならず、必須の欄の名前がそれらなら無くても通る、と読める。**読みで同じ形と判断しただけで、実行して確かめていない。**直し方は `eventSchema.ts` と同じ `Object.hasOwn`(10.6)

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

---

## 10. 実装の記録(2026-09-15、実装担当 A。**予測の節 5. は書き換えていない**)

### 10.1 足したもの・変えたもの

| ファイル | 中身 |
|---|---|
| `scripts/playtest/schemas/failure-event.v0.1.schema.json`(新規) | 2.2 の表を写したスキーマ。判別ユニオン(`evaluationBefore` 6 変種・`classification` 5 変種・`shape` 2 変種・`focus` 4 変種)は `oneOf` + `const`。**すべての入れ物で `additionalProperties: false`**(J-8)。USI の手の欄に手の形の `pattern`(実記録 24 本の `bestmove` 424 欄と `moveHistory` はすべてこの形に合った ― `resign`・`win` は無かった) |
| `scripts/playtest/lib/eventSchema.ts`(新規) | 検証器(J-7)。`validate-data.mjs` と同じキーワードに `oneOf`(**ちょうど 1 つ**)と `const` だけを足した。**知らないキーワード・扱わない形(`additionalProperties: true` など)は `SchemaKeywordError` を投げる**(綴り違いが黙って「何も見ない」にならないように) |
| `scripts/playtest/lib/eventSchema.test.ts`(新規) | T-1(9 件。10.6 で 1 件足した) |
| `scripts/playtest/lib/failureEventSchema.ts`(新規) | `FAILURE_EVENT_SCHEMA_VERSION = "0.1"`・`toEventLine`(版の欄を先頭に足すだけ)・スキーマの読み込み・1 行の検証 |
| `scripts/playtest/lib/failureEventSchema.test.ts`(新規) | T-2〜T-5(16 件。10.6 で 1 件足した) |
| `scripts/playtest/diagnose.ts` | `--events` の 1 行を `JSON.stringify(toEventLine(event))` にした(import 1 行・冒頭の説明 2 行)。**標準出力の表は変えていない。**D3 のコミット `258f374` の後に載せた(司令塔の注意。10.5) |
| `scripts/playtest/diagnose.test.ts` | T-6。既存の子プロセスの試験を広げ、ソース照合の文字列を差し替えた(10.5) |

**計画 6.1 との差(司令塔の承認、2026-09-15)**: 版の定数と `toEventLine` を、計画では `lib/failureEvent.ts` に置く予定だった。**D3 が同じファイルを触って監査中なので、衝突を避けて `lib/failureEventSchema.ts` に分けた。**

### 10.2 試験

- **T-3 は「試した変種」を突き合わせる**: T-2・T-3・T-4 の Failure Event と、lib から出ない変種を手で書き換えた 2 行(`evaluationBefore` の `notMeasuredGameEnd`・`action.playedMove` の `null`)から、変種と「無い」の形の札を集め、**一覧の札がすべて現れる**ことを見る(札の数はここに書かない。1 回目に「38 個」と書いたのは数え誤りで、実物は 41 個だった ― 監査 B の任意 a。10.6 で値の枝の札を足した)(5.2 の P-3 の穴を塞いだことを、試験が覚えている)
- 変種を埋める固定例: 直前が王手中(GAME01 の 40 手目 → 42 に `afterPass.mate`)・測れなかった(`null`)・評価値でない(afterPass 35281)・欄なし の 4 つは `matedIfPass` だけで当たる Failure Event、`shape.unrecorded` と `undetermined`(U-1)は直前の行の coach から `current_shape` と `opponent_next_aim` を消した記録、`consequences.mate` の数は F-1 を `windowPlies` 7 で数えたもの(`[52, 54, 56]`・詰み 56)
- **T-4 は `records/d0-nnue` の 7 本**(`out/` は gitignore の対象で使えない)。件数は固定しない(実測 22)
- **T-5**: F-1 の分岐点 49 の 1 行(候補の型が 1 件入る)から、**41 個のキーを 1 つずつ消すとすべて落ちる**・各入れ物に知らない欄を足すとすべて落ちる・版が違えば落ちる
- 件数: HEAD `9f6db06` の worktree で、型検査 exit 0・vitest **31 ファイル 329 件**すべて通過(JSON v0 の 2 本を除くと 29 ファイル 306 件。+23)。`258f374` に載せ直した後の件数は 10.5

### 10.3 既存の揺れ: `intentStatement.test.ts` の T-1 の時間切れ(**原因は負荷。JSON v0 の中身ではない**)

| 回 | 回し方 | 結果 |
|---|---|---|
| 1 | 全体(JSON v0 の 2 本を含む) | 落ちた(8.8 秒。`Test timed out in 5000ms`) |
| 2 | 同上 | 落ちた(8.2 秒) |
| 3 | T-1 のファイルだけ | 通った |
| 4 | 全体(JSON v0 の 2 本を除く) | 通った(306 件) |
| 5 | T-1 のファイルだけ | 落ちた(7.7 秒) |
| 6 | 全体(JSON v0 の 2 本を除く) | 落ちた(10.6 秒) |
| 7 | 全体(JSON v0 の 2 本を含む) | 落ちた(10.4 秒) |

- **負荷**(5〜7 回目の直後): load average **16.6**(8 CPU)。並行していたもの: 別セッションの vitest(`lib/scanCompare.test.ts`・`scan-compare.test.ts`)、Chrome のレンダラー、macOS の更新サービス。エンジンは 0 本
- **最初は「JSON v0 の試験の負荷が既存の試験を押し出した」と読んだが、誤りだった**(4 回目だけを見て決めた。6 回目で 2 本を除いても落ちた)
- **直し(司令塔の決定、2026-09-15。JSON v0 とは別コミット)**: T-1 に明示の時間切れ `60_000`(`diagnose.test.ts` の子プロセスと同じ)。**差分は `}, 60_000);` の 1 行だけ**(理由はコードに書かず、この節に残す ― 司令塔の指示)。直した後、load average **18.4** のもとで全体 329 件すべて通過
- **変異の条件**: 道具の vitest に `--testTimeout=60000` を付けた(司令塔の決定 (2) a。リポジトリの設定は変えない)

### 10.4 変異(**予測は当てる前に道具 `json-v0-mutate.py` に試験名で書いた**。vitest に `--testTimeout=60000` ― 10.3)

**適用 14 / 鳴った 14 / 適用できなかった 0。予測(鳴るはず・鳴らないはずの両方)13 / 14。**全ファイルが元のバイト列に戻った。**別の理由の赤(ファイルごとの失敗・読み込みの失敗)は 0 件。**`diagnose.ts` の変異(S-3: 版の欄を書かない)は、D3 のコミットの後に T-6 と一緒に当てる。

| # | 壊し方 | 鳴った試験 |
|---|---|---|
| V-1 | `oneOf` を「1 つ以上に合えばよい」にする | T-1 の `oneOf` |
| V-2 | `const` を見ない | T-1 の `const`・`oneOf`・入れ子、T-2 の全固定例、T-3、T-4、T-5 の前提(14 件)。**予測は外れた**(下) |
| V-3 | `additionalProperties: false` を見ない | T-1 の required/additionalProperties・`oneOf`、T-5 の「知らない欄を足す」 |
| V-4 | `required` を見ない | T-1 の required/additionalProperties・`oneOf`、T-5 の「欄を 1 つ消す」 |
| V-5 | `minItems` を見ない | T-1 の minItems/items |
| V-6 | `items` の要素を見ない | T-1 の minItems/items、T-5 の「消す」「足す」 |
| V-7 | `integer` に小数も通す | T-1 の type |
| V-8 | 知らないキーワードを例外にせず飛ばす | T-1 の知らないキーワード |
| S-1 | スキーマの `consequences.required` から `windowShort` を消す | T-5 の「欄を 1 つ消す」だけ |
| S-2 | lib が `evaluationBefore`(measured)に欄 `nodes` を足す(スキーマは直さない) | T-2 の全固定例・T-3・T-4・T-5(12 件) |
| S-4 | `focus` の `nothingToSay` に空文字の `text` を足す(「無い」を空文字にする) | D1 の F-7(③の 4 つの状態)・T-2・T-3・T-4・T-5(13 件) |
| S-5 | `toEventLine` が版 `"0.2"` を書く | T-2・T-3・T-4・T-5 の前提(11 件) |
| S-6 | 版の欄を先頭でなく末尾に置く | T-2 の全固定例(「版の欄が先頭」)だけ |
| S-7 | スキーマの measured の変種から `additionalProperties: false` を消す | T-5 の「知らない欄を足す」だけ |

**V-2 の予測の外れ(道具の誤りではなく、読みの誤り)**: 「版が違えば落ちる」(T-5)も鳴ると予測したが、鳴らなかった。`const` を見ないと、`focus` の `nothingToSay`・`pending`・`unrecorded` の 3 変種が同じ形(`state` だけ)になって `oneOf` が 3 つに合い、**元の 1 行そのものが通らなくなる**。版を `"0.2"` にした 1 行も同じ理由で落ちるので、「落ちる」を期待する試験は緑のままだった。**版の `const` そのものは S-5 で見張られている**(`toEventLine` が `"0.2"` を書くと T-2・T-4 が鳴る)ので、見張りの穴ではない。

### 10.5 D3 のコミット(`258f374`)の上に載せ直した後(**2 回目の変異と件数**)

- **載せ直し**: HEAD `258f374` の新しい worktree に、1 回目の新規 5 本・計画書・T-1 の 1 行を写し、`diagnose.ts`・`diagnose.test.ts` を変えた。D3 が変えた `lib/failureEvent.ts` は `dropCountCell` の export だけで、**JSON v0 の新規 5 本は写したまま変えずに通った**
- **T-6**: 既存の子プロセスの試験を広げた。書き出した行が `expectedEvents.map(toEventLine)` と一致し、**各行の先頭の欄が `schemaVersion`・値が `"0.1"`・この版のスキーマを通る**。`toEqual` は欄の順を見ないので、先頭であることは別に見る。版は定数でなく値 `"0.1"` で見る(定数ごと変わる壊し方でも鳴るように)
- **件数**: `typecheck:scripts` exit 0、vitest **35 ファイル 386 件すべて通過**(JSON v0 の 2 本を除くと 33 ファイル 363 件 = 司令塔の D3 の測り直しと同じ。+23)。`--testTimeout=60000`、load average 5.8〜14.0
- **変異**(道具 `json-v0-mutate2.py`。sha256 `67e374dd…` を、当てる前に同じ逐次コマンドで記録): **1 回目の 14 件の予測は変えずに残し**、`diagnose.ts` の変更で増えた見張り(子プロセスの試験・ソース照合)の予測だけを足した。V-2・S-4 は、子プロセスの固定例にどの変種が出るかしだいで読みで決められないので、子プロセスの予測を書かなかった。S-3 を足した

**適用 15 / 鳴った 15 / 沈黙 0 / 適用できなかった 0。予測(鳴るはず・鳴らないはずの両方)14 / 15。**外れは 1 回目と同じ V-2 の T-5「版が違えば落ちる」(理由は 10.4)。全ファイルが元のバイト列に戻った。**別の理由の赤は 0 件。**

| # | 鳴った試験(1 回目との違い) |
|---|---|
| V-1・V-3〜V-8・S-1・S-7 | 1 回目と同じ。**子プロセス・ソース照合は鳴らない**(予測どおり: 正しい行は正しいまま) |
| V-2 | 1 回目の 14 件 + 子プロセス(15 件。子プロセスは予測なし) |
| S-2 | 1 回目の 12 件 + 子プロセス(13 件。予測どおり: 欄が増えた行がスキーマを通らない) |
| S-4 | 1 回目の 13 件 + 子プロセス(14 件。子プロセスは予測なし) |
| S-5 | 1 回目の 11 件 + 子プロセス(12 件。予測どおり: 版が `"0.1"` でない) |
| S-6 | 1 回目の 7 件 + 子プロセス(8 件。予測どおり: 先頭が `schemaVersion` でない) |
| **S-3(新)** | `diagnose.ts` が版の欄を書かない → **ソース照合・子プロセスの 2 件だけ**(予測どおり。lib の試験 T-2〜T-5 は鳴らない) |

### 10.6 監査 B の REVISE(必須 2・任意 5)の後(**3 回目の変異と件数**。司令塔の決定: 7 件すべて直す)

- **必須 1(検証器がプロトタイプを辿る)**: `properties[key]` と `key in instance` が Object.prototype を辿り、`constructor`・`toString`・`hasOwnProperty`・`__proto__` の名前の**知らない欄を通し**、必須の欄 `"toString"` が**無くても通した**(J-8 の「知らない欄が出たら赤」が破れる)。**`Object.hasOwn` に直し、T-1 に固定例を足した**(4 つの名前の欄はファイルと同じく `JSON.parse` で作る。`__proto__` はオブジェクトのリテラルで書くと欄にならない)
- **必須 2(スキーマの値域の枝が試されていない)**: 直前の評価の `mate` の正・負、`scoreCp` の null、`afterPassMate` の負、`branch.mateAfter` の正、`scoreCp` の ±29999 の境目の 6 つを、どの試験も通っていなかった。**実記録(records と out の 99 本。監査 B の数え)に `baseline.mate` は 0 件、`afterPass.mate` は正の 2 件だけ**で、固定例も直後の行にしか mate を植えていなかった
  - lib から出せる 4 つは **T-3 の固定例に足した**: 直前の行に `engineRef(null, { mate: 5 })`・`{ mate: -5 }`、直前の `afterPassMate` −3、直後の行に `mate` 3 と `afterPassMate` 5。どれも直後の行の `afterPass.mate` で matedIfPass として当てる
  - ±30000 は lib が notEvaluation にするので出せない → **手で書いた 1 行**で、`scoreCp`・`afterPassScoreCp` の ±29999 は通り ±30000 は落ちる、`mate`・`afterPassMate`・`mateAfter` の 0 は落ちる、を見る(T-3 に 1 件)
  - T-3 の札に、`scoreCp`・`afterPassScoreCp` の null / 数、`mate`・`afterPassMate`・`mateAfter` の null / 正 / 負、`dropCp` の null を足した。**これらの枝は実記録に無く、固定例と手で書いた 1 行でだけ試している**
- **任意 a**: 10.2 の札の数(上)
- **任意 b(限界)**: 2.2 の「奇数・≥ 1」(`branchPly`)、「偶数」(`fromReadyPly`・`toReadyPly`・`checks` の要素・`consequences.mate`)、「昇順」(`checks`)は**スキーマで表していない**(検証器に `multipleOf` と並びの見張りが無い ― J-7)。スキーマを通っても、これらは確かめていない
- **任意 c(限界)**: `mate` の「0 以外の整数」について、USI の解析(`apps/server/src/engine/usiInfoParser.ts:66` の `(-?\d+)`)は `mate 0` も通す。`engineReference` は王手中・終局の局面を測らないので出ない、と読める(**実行して確かめていない**)。出たらスキーマで赤になる(意図どおり。上の境目の試験が見張る)
- **任意 d**: 検証器が、数でない `minimum`・`maximum`・`minItems`、文字列でない `pattern`、文字列の配列でない `required`、オブジェクトでない `properties`・`items` を `SchemaKeywordError` にする(以前は黙って飛ばす・1 文字ずつ見る、だった)。T-1 に 7 つ足した
- **任意 e**: `failureEventSchema.ts` の冒頭のコメントが、書いた先を「計画書 §10.1」と指す
- **件数**: `typecheck:scripts` exit 0、vitest **35 ファイル 388 件すべて通過**(2 回目の 386 + T-1 の 1 + T-3 の 1)。`--testTimeout=60000`、load average 7.5〜11.9

**A の変異**(道具 `json-v0-mutate3.py`、sha256 `22446aa3…` を当てる前に同じ逐次コマンドで記録): 2 回目の 15 件の予測は変えずに残し、足した試験(プロトタイプの名前の欄・値域の境目)の予測だけを足した。V-4 はアンカーの文字列だけ直した(`key in instance` が `Object.hasOwn` になったため。壊し方は同じ)。

**適用 30 / 鳴った 30 / 沈黙 0 / 適用できなかった 0。予測 29 / 30。**外れは 1・2 回目と同じ V-2 の T-5「版が違えば落ちる」(10.4。足した予測の「値域の境目」は V-2 で鳴った)。全ファイルが元のバイト列に戻った。**別の理由の赤は 0 件。**

| # | 壊し方 | 鳴った試験 |
|---|---|---|
| V-9 | (必須 1 の直しを戻す)`properties` を `properties[key]` で引く | プロトタイプの名前の欄 |
| V-10 | (同)`required` を `key in instance` で見る | プロトタイプの名前の欄 |
| V-11〜V-15 | (任意 d)数でない `minimum` など・文字列の `required`・配列の `properties`・文字列でない `pattern`・配列の `items` を黙って受ける | 知らないキーワード・扱わない形(各 1 件) |
| S-8〜S-12 | (必須 2)直前の `mate` の負・正、`scoreCp` の null、`afterPassMate` の負、`mateAfter` の正の枝を消す | T-3 の lib から出る変種(各 1 件) |
| S-13・S-14 | (必須 2)`scoreCp`・`afterPassScoreCp` の上下限を ±99999 に広げる | 値域の境目(各 1 件) |
| S-15 | (必須 2 の v)直前の `mate` に 0 を許す | 値域の境目 |
| V-3・V-4 | (2 回目との違い) | + プロトタイプの名前の欄 |
| V-2・S-2・S-4・S-5 | (2 回目との違い) | + 値域の境目 |

**監査 B の 20 件の当て直し**(B の `json-audit-mutate.py` の写し `json-audit-mutate-btool.py`、sha256 `6c40f709…`。WT だけを替え、B が沈黙と予測した 6 件の予測を、当てる前に「鳴る」に書き換えた。変異の中身は変えていない): **適用 20 / 鳴った 20 / 沈黙 0 / 適用できなかった 0、予測 20 / 20、中心 18 / 18。**B の実行で沈黙した B-1・B-2・B-3・B-5・B-7 は T-3 の足した固定例で、B-8 は値域の境目で、それぞれ 1 件鳴った
