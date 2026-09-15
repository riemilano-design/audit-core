# STEP JSON v0.2 計画: Failure Event に出どころ・直後の評価・玉の周りの数を足す(2026-09-15。**計画のみ**。**実装 A、監査 B(D-COST の計測の後)**)

## 0. この STEP の位置づけ

- **司令塔の依頼(2026-09-15)**: D3 の 20 局(`2e5f9f0`)で、Failure Event を**記録をまたいで集める段**に入る。v0.1 計画([STEP_JSON-V0_PLAN_2026-09-15.md](STEP_JSON-V0_PLAN_2026-09-15.md))3.3 の候補を計画にする
  - `provenance`(記録のパス・記録の `gitHead`・評価関数の識別。評価関数の識別は **P-43 が直るまでの暫定として、`enginePath` と `nn.bin` の sha256 を README から手で渡す形**)
  - `evaluationAfter`
  - `bestmoveAtBefore` の `null` の 2 つの理由を分ける
  - **A 層の数の候補**「分岐点の直前の、自玉の隣の自分の駒の数」(D3 で植えた答えが形の欄で見えなかった件 ― D3 計画 L-8・Q-7)。**数を出すだけで閾値は置かない。**司令塔の決定で **v0.2 に入れる**(K-7。判断的知識かどうかの整理は 2.4)
- **版は `0.2`**(欄を足すだけ = MINOR。v0.1 計画 3.2)
- **実装 A(sgogi-coach-64)、監査 B(sgogi-coach-ed。D-COST の計測の後)**(司令塔、2026-09-15)
- **決定(司令塔、2026-09-15)**: 4. の K-1〜K-9 は**すべて推奨どおり**
- **基準は HEAD `2e5f9f0`。エンジンは使っていない。**1. の数は、コミット済みの記録(`records/d0-nnue` 7 本・`records/d3-nnue` 20 本)に今の lib を掛けた使い捨ての道具(`scratchpad/v02-probe.ts`、sha256 `e8f61f25…`)で数えた。**校正**: 初期局面の「玉の隣の自分の駒」= 2(4i・6i の金)、D3 の Failure Event の数 = B 50・B′ 59(D3 計画 §9.4 と一致)

---

## 1. 実物から分かった前提(**場所か数で書く**)

| # | 事実 | 場所・数 |
|---|---|---|
| F-1 | 27 本の記録の `meta` は、どれも `gitHead`・`dirty`・`enginePath`・`searchMode`・`nodes`・`threads` を持つ(欠け 0)。**`enginePath` はホームディレクトリのユーザー名を含む絶対パス**(`/Users/…/apps/server/engine/nnue/YaneuraOu-by-gcc`) | `records/d0-nnue`(gitHead `a9da0589`)・`records/d3-nnue`(`258f3749`)の meta 行 |
| F-2 | **`records/d3-nnue` の `meta.enginePath` は評価(再生)のエンジンで、対局の相手のエンジン(駒得版)は meta に残らない**。README が正本 | `records/d3-nnue/README.md` |
| F-3 | 記録のファイルの sha256 は、どちらのフォルダにも `SHA256SUMS` がある。評価関数(水匠 5)の `nn.bin` の sha256 `768068f0…` は README にだけある(P-43) | `records/*/SHA256SUMS`・`README.md` |
| F-4 | **lib は記録のファイルのパスを知らない**。`DiagnosisInput` は `kifuId`・`meta`・`records` だけで、パスは `diagnose.ts` の `readInput` の中にしか無い | `diagnose.ts:33-42`、`lib/failureEvent.ts:434-438` の `DiagnosisInput` |
| F-5 | **`action.bestmoveAtBefore` は `evaluationBefore.state === "measured" ? evaluationBefore.bestmove : null`**。`measured` のときは `evaluationBefore.bestmove` と同じ値の写し | `lib/failureEvent.ts` の `diagnoseRecords` |
| F-6 | **27 本の Failure Event 131 件(d0 22・B 50・B′ 59)で、`bestmoveAtBefore` の `null` は 12 件(B 3・B′ 9)。12 件とも「直前が `measured` でない」で、「`measured` なのに最善手が無い」は 0 件** | 使い捨ての道具 |
| F-7 | **Failure Event の直後の行は、131 件すべて `measured`**。組み立てで決まる: `cpDrop` は両方 `measured` の組、`mateDrop` は直後が `measured` の mate、`matedIfPass` は直後が `measured` で `afterPassMate > 0` | `lib/failureEvent.ts` の `pairEvaluations`・`diagnoseRecords`。道具で 131/131 |
| F-8 | `branch.diffCp` が `null` の Failure Event は 18 件(B 3・B′ 15)。直後は `measured` の mate が 12 件、`measured` の cp が 6 件(直前が `measured` でない・直前が mate の `matedIfPass`)。**v0.1 ではこの 6 件の直後の cp が 1 行から分からない**(v0.1 計画 E-10 の導出は `diffCp` が数のときだけ) | 使い捨ての道具 |
| F-9 | **玉の隣(8 近傍)の先手の駒の数**。Failure Event の直前の行: d0 は中央値 4(分布 2:9・3:1・4:8・5:1・6:1・7:2)、**B は中央値 4(4 が 47/50)、B′ は中央値 2(2 が 35/59)**。ready 行すべてでは d0 中央値 3・B 4(151/199)・B′ 2(132/210)。金銀だけに絞っても同じ傾向(B 4・B′ 2) | 使い捨ての道具 |
| F-10 | 同じ 85 件の急落候補で、形の欄(`trigger.shape.status`)は **85 件すべて `none`**(D3 計画 §9.5 予-D9) | D3 計画 §9.5 |
| F-11 | Failure Event の型を読むもの: `diagnose.ts`(書き出し)・`lib/failureEventSchema.ts`(版と検証)・その試験・`diagnose.test.ts`(子プロセスの `--events` を lib の結果と `toEqual` で比べる)。`diagnosisTotals.ts` は数だけを読む | `git grep FailureEvent`(校正: `export interface FailureEvent` が 1 件当たることを先に確かめた) |

---

## 2. v0.2 に足す欄(**決定は 4.**)

「無い」の規約は v0.1 と同じ 3 種(キーが無い = その変種に無い / `null` = 欄はあるが値が無い / `[]` = 見た範囲で 0 件)。

### 2.1 `provenance`(最上位。**各行に置く** ― K-1)

| 欄 | 型 | 意味 | `null` のとき | 元 |
|---|---|---|---|---|
| `provenance.record.path` | string | 記録のファイル。**リポジトリの根からの相対パス**、リポジトリの外ならファイル名だけ(K-2) | 無いことは無い | `diagnose.ts` に渡された引数(F-4) |
| `provenance.record.sha256` | string | 記録のファイルのバイト列の sha256(`diagnose.ts` が読んだバイト) | 無いことは無い | `diagnose.ts` が計算。`SHA256SUMS` と照らせる(F-3) |
| `provenance.record.meta` | object \| null | 記録の meta の写し(下の 6 欄) | `null` = **meta 行が無い** | meta 行 |
| `….meta.gitHead` | string \| null | 記録を取ったときのコード | `null` = 記録時に取れなかった | `meta.gitHead` |
| `….meta.dirty` | string | 記録を取ったときの作業ツリーの汚れ。`lib/gitState.ts:148` の `DirtyState` の 4 値(`dirty`・`clean`・`unrecorded`・`unmeasured`)をそのまま | 無いことは無い(4 値の中に「記録していない」がある) | `lib/gitState.ts:167` の `readDirtyState(meta)` |
| `….meta.enginePath` | string | **評価(再生)に使ったエンジン**。K-2 の形に直す | 無いことは無い | `meta.enginePath` |
| `….meta.searchMode`・`nodes`・`threads` | string / integer | 探索の条件。**`nodes` の `0` = 時間で打ち切る探索(`searchMode` が `"movetime"`。`replay.ts --nodes 0`)。`searchMode` と組で読む**(→ 司令塔の決定、2026-09-15。10.6) | `null` = meta にその欄が無い(**`unrecordedKeys` に名前を並べる**)。**`nodes` の `0` を `null` にしない**(欄は meta にある) | meta |
| `….meta.unrecordedKeys` | string[] | meta に無かった欄の名前 | `[]` = 欠けなし | meta |
| `provenance.evaluator.declared` | string \| null | **人が `diagnose.ts --evaluator "<文>"` で渡した評価関数の識別**(例: `YaneuraOu NNUE 水匠5 nn.bin sha256 768068f0…`)。**確かめていない自己申告の文**(K-4。**スキーマの欄の説明にもこの言葉を書く**) | `null` = 渡されていない。**`enginePath` から推測しない**(P-43) | CLI |
| `provenance.analysis.gitHead`・`dirty` | string \| null / string | **`diagnose.ts` を回したときのコード**(Failure Event を組み立てたコード。記録を取ったコードとは別) | `gitHead` の `null` = 取れなかった | `lib/gitState.ts:106` の `readGitState(cwd)`(recorder と同じ読み方) |
| `provenance.analysis.rule` | object | 規則の値 `advantageCp`・`dropCp`・`windowPlies`・`focusDropCp`・`notEvaluationCp`(K-8) | 無いことは無い | `DRAFT_RULE_1`・`NOT_EVALUATION_CP` |

- **なぜ要るか**: `kifuId` は評価関数・再生をまたいで一意ではない(P-46)。規則を変えると同じ版でも別の Failure Event が出る(v0.1 計画 3.2 の約束)。企業に出す Evidence には「どの記録・どの条件で出た値か」が要る
- **対局の相手のエンジンは載せない**(F-2。記録に無いものは写せない。README を正本として `evaluator.declared` の文に書いてもらう)

### 2.2 `branch.evaluationAfter`

- **形は `trigger.evaluationBefore` と同じ 6 変種の判別ユニオン**(K-5)。直後の行(`toReadyPly`)の評価を状態 + 値で写す
- **今の lib からは `measured` しか出ない**(F-7)。それでも 6 変種で持つ理由と、`measured` だけにする案は K-5
- **これで F-8 の 6 件の直後の cp が 1 行で読める**。v0.1 の導出(`evaluationBefore.scoreCp + branch.diffCp`)は残るが、読む側が導出しなくてよくなる
- v0.1 計画 E-9 の **EvaluationAfter** はこの欄になる

### 2.3 `action.bestmoveAtBefore` の `null` の 2 つの理由(K-6)

**実物(F-5・F-6)**: 2 つの理由は、どちらも**同じ 1 行の中の `trigger.evaluationBefore` で決まる**。

| `bestmoveAtBefore` | `evaluationBefore.state` | 理由 | 27 本で |
|---|---|---|---|
| `null` | `measured` 以外 | 直前を測っていない・測れなかった | 12 件 |
| `null` | `measured`(`bestmove` も `null`) | エンジンが最善手を返さなかった | **0 件** |

| 案 | 中身 | 版 | 評価 |
|---|---|---|---|
| **(a) 決定** | **欄を足さない。**スキーマの説明に上の表を書き、試験で「`bestmoveAtBefore` は `evaluationBefore.state === "measured" ? evaluationBefore.bestmove : null` と等しい」を全固定例・全実記録で見る | 変わらない | 2 つの理由は今も 1 行で読める。足すと同じ事実を 2 か所に持ち、食い違いうる |
| (b) | `action.bestmoveAtBeforeAbsence: "notMeasured" \| "engineReturnedNone" \| null` を足す | MINOR | 1 欄で読める。**列挙なので、理由を足すたびに MAJOR**(J-5)。`evaluationBefore.state` と食い違う形が作れる |
| (c) | `action.bestmoveAtBefore` を消し、`evaluationBefore.bestmove` だけにする | **MAJOR** | 重複は消えるが 0.2 ではできない |

### 2.4 A 層の数: 玉の周り(K-7。**決定: v0.2 に入れる**)

**形(決定)**: `trigger.kingSurroundings: { squares: integer, own: integer } | null`

- `squares` = **直前の行の局面で、先手玉の 8 近傍のうち盤の中にあるマスの数**(盤の中央 8、端 5、隅 3)
- `own` = そのマスにある**先手の駒の数(駒の種類を問わない。成り駒も含む)**
- `null` = 先手玉が盤上に無い(今の組み立てでは起きない)
- **`squares` を並べる理由**: 玉が端にいると `own` の上限が 5 になる。`own` だけでは「端にいる」と「周りに駒が無い」を分けられない(Evidence 例の 5i の玉は `squares` 5)

**判断的知識かどうかの整理**(CLAUDE.md ルール 4・DATA_MODEL の Kind 1〜3)

| 何をするか | 種類 | この案での扱い |
|---|---|---|
| 8 近傍のマスを数え、先手の駒を**種類を問わず**数える | **盤面の事実(A 層)**。判定・優先度・閾値・挙動を変えない。Failure Event は解析の出力で、知識の 3 種のどれでもない(v0.1 計画 J-3) | **置く(決定)** |
| 数える駒を**金・銀だけ**にする | 「守りの駒はどれか」という将棋の判断が入る。値を出すだけでも、どの駒を選ぶかに判断がある | **置かない**(F-9 で傾向は同じだった) |
| 「2 以下なら囲っていない」などの**閾値・名前**を付ける | **Kind 3 相当**(判定を変える) | **置かない**。`candidateModes`・死因の規則にも使わない |
| 画面・コーチの文に出す | 上位原則・ルール 4・6 の対象 | **この STEP の範囲外** |

**実物(F-9・F-10)。「植えた癖が数には見える」の材料として置く**: 形の欄は 85 件すべて `none` で B と B′ を分けなかったが、この数は **B の直前の行で中央値 4、B′ で中央値 2** と分かれた。**「診断に役立つ」とは書かない**(司令塔、2026-09-15)。

**ただし読み方に限りがある**:

- **植えた癖そのものを数えている**。B の 5-iii は「金か銀を玉の隣へ」なので、B で数が大きいのは作りどおり。**この欄が植えた癖を「見える」ことは示すが、診断に役立つことは示さない**(D3 計画 L-7)
- B と B′ は 10 局ずつで対になっていない(L-7)

**入れる時期(決定: (i))**:

| 案 | 中身 | 評価 |
|---|---|---|
| **(i) 決定** | **v0.2 に入れる** | 欄を足すたびに MINOR が 1 つ上がる。provenance・evaluationAfter と同じ STEP で lib の Failure Event の型を 1 回だけ変え、監査も 1 回にできる |
| (ii) | v0.2 には入れず、D 系の別 STEP で 0.3 として入れる | v0.2 の監査の範囲は狭くなる。版が 1 つ増える |

---

## 3. 版

- **`schemaVersion: "0.2"`**。**スキーマのファイルを 1 つ増やす**(`scripts/playtest/schemas/failure-event.v0.2.schema.json`)。**`failure-event.v0.1.schema.json` は消さない**(v0.1 計画 3.2)
- **MINOR の根拠**: 足すのは `provenance`・`branch.evaluationAfter`・`trigger.kingSurroundings`(K-7)だけで、**既存の欄の意味・単位・視点を変えない**。K-6 の推奨 (a) なら `action` は変わらない
- v0.1 のスキーマは `additionalProperties: false` なので、**0.2 の行は v0.1 のスキーマでは落ちる**(意図どおり。読む側は `schemaVersion` でスキーマを選ぶ)

---

## 4. 決定(司令塔、2026-09-15。**K-1〜K-9 はすべて推奨どおり**)

| # | 判断 | 決定 | 選ばなかった案 |
|---|---|---|---|
| **K-1** | `provenance` を置く場所 | **各行**(v0.1 の J-1 と同じ理由: 1 行だけ切り出しても出どころが分かる) | ファイルの先頭に 1 行(行を切り出すと消える) |
| **K-2** | パスの形 | **リポジトリの根からの相対パス**(外ならファイル名だけ。**→ 実装で「根の外なら `apps/server/engine/` から後ろ、それも無ければファイル名だけ」と読み替えた ― 司令塔の決定、2026-09-15。10.2**)**+ `record.sha256`**。`enginePath` も同じ形に直す。**絶対パスはホームのユーザー名を含む**(F-1)。企業に見せるかは人間が決めるが、見せる前提の形にしておく | 絶対パスのまま写す(誰の機械かが出る) |
| **K-3** | meta が無い・meta の欄が無いとき | **meta 行が無ければ `record.meta: null`。欄が無ければその欄は `null` にし、`unrecordedKeys` に名前を並べる**。`dirty` は `DirtyState` の 4 値で写す(「記録していない」が値の中にある) | 欄ごとに判別ユニオン(読む側が重い) |
| **K-4** | 評価関数の識別の渡し方 | **`diagnose.ts --evaluator "<文>"` を 1 つ**(その回のすべての入力に同じ文)。**渡されなければ `null`。`enginePath` から推測しない**。**欄の説明に「確かめていない自己申告」と書く**。評価関数が違う記録は分けて回す | 入力ごとに渡す(引数が長くなる)/ README を読む(README の形に依存する) |
| **K-5** | `evaluationAfter` の形 | **`evaluationBefore` と同じ 6 変種**(今は `measured` しか出ないが、同じ型を使えば読む側の分岐が 1 つで済み、lib の組み立てを変えても契約が変わらない)。**出ない 5 変種は、v0.1 の `HAND_MADE` と同じく手で書いた 1 行で試す** | `measured` だけ(組み立ての今の性質を契約に焼き込む。lib が変われば MAJOR) |
| **K-6** | `bestmoveAtBefore` の `null` | **(a) 欄を足さず、説明と等しさの試験で約束する**(2.3) | (b) 理由の欄を足す / (c) 欄を消す(MAJOR) |
| **K-7** | 玉の周りの数 | **(i) v0.2 に入れる。形は `{ squares, own }`、種類を問わず数える。閾値・名前は置かない**(2.4) | (ii) 別 STEP で 0.3 / 金銀だけを数える |
| **K-8** | 規則の値を行に写すか | **写す**(`provenance.analysis.rule`。v0.1 計画 3.2 の「閾値を変えても版は上げず、出どころに規則の値を書く」の実装) | 写さない(同じ版で規則が違う行を見分けられない) |
| **K-9** | 解析のコードの版を写すか | **写す**(`provenance.analysis.gitHead`・`dirty`。記録を取ったコードと、Failure Event を組み立てたコードは別) | 記録の `gitHead` だけ |

---

## 5. 期待値(**実装の STEP が測る前に置く値**。1. の使い捨ての道具で数えた値なので、「再現すべき値」として置く)

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| P-1 | 27 本の Failure Event は **131 件**(d0 22・B 50・B′ 59)。v0.2 の欄を足しても件数と既存の欄の値は変わらない | 件数か、既存の欄の値が 1 つでも変わる |
| P-2 | `branch.evaluationAfter.state` は **131/131 が `measured`** | `measured` 以外が 1 件でも出る |
| P-3 | `bestmoveAtBefore` が `null` の 12 件は、**12 件とも `evaluationBefore.state` が `measured` でない**。等しさの試験は 131/131 で通る(K-6 (a)) | 等しくない行が出る |
| P-4 | `provenance.record.sha256` は、27 本とも各フォルダの `SHA256SUMS` と一致する | 1 本でも違う |
| P-5 | `provenance.record.meta.unrecordedKeys` は 27 本とも `[]` | 欠けが出る |
| P-6 | Failure Event の `trigger.kingSurroundings.own` の中央値は **d0 4・B 4・B′ 2** | 値が違う |
| P-7 | 0.2 の行はすべて v0.2 のスキーマを通り、**v0.1 のスキーマでは落ちる** | どちらかが逆 |

---

## 6. 実装の STEP でやること(**この計画書のコミットの後、A が実装する**。v0.2 のスキーマのファイルを増やし v0.1 は残す、検証器の変更が要れば最小、P-1〜P-7 の再現、変異)

### 6.1 変えるもの

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/failureEvent.ts` | `FailureEvent.branch.evaluationAfter`(直後の行の `evaluation`)。`trigger.kingSurroundings`(K-7)(本番の `parsePosition` で盤を読む。数えるだけ) |
| `scripts/playtest/lib/failureEventSchema.ts` | 版を `"0.2"` に。`provenance` の型と、Failure Event に `provenance` を付ける関数。版ごとにスキーマを選んで読む |
| `scripts/playtest/schemas/failure-event.v0.2.schema.json`(新規) | v0.1 のスキーマ + 2. の欄。**v0.1 のファイルは変えない** |
| `scripts/playtest/diagnose.ts` | 入力ごとに記録のパス(K-2)と sha256 を持ち、`--evaluator` を読み、解析の `gitHead`・`dirty` と規則の値を添えて `--events` の行を書く |

### 6.2 試験

- 検証器は v0.1 の J-7 のまま(変えない)
- **P-1〜P-7 を固定例と実記録で**。`provenance` の変種(meta 行なし・meta の欄なし・`dirty` の 4 値・`--evaluator` なし)を固定例で埋め、v0.1 の T-3 と同じく**札の突き合わせ**で覚えさせる
- `evaluationAfter` の `measured` 以外の 5 変種は手で書いた 1 行(K-5)
- **子プロセス**(`diagnose.test.ts`): `--events` の行が v0.2 を通り、`provenance.record.sha256` が書いたファイルの sha256 と一致し、`--evaluator` の文がそのまま入る。**今の `toEqual(expectedEvents.map(toEventLine))` は `provenance` の分だけ直す**(F-11)
- K-6 (a) なら、等しさの試験を全固定例・全実記録で

### 6.3 変異(**中心を壊すもの ― 規則 11.8**)

- `evaluationAfter` を直前の行から取る
- `record.sha256` を記録でなく別のバイト(例: 書き出し先)から計算する
- `evaluator.declared` を `enginePath` から推測して埋める(P-43 に反する)
- `provenance.analysis.rule` を定数の写しでなく固定の値にする(規則を変えても行が変わらない)
- パスを絶対パスのまま書く(K-2)
- (K-7)数える駒に後手の駒を含める・玉自身を含める・8 近傍を 4 近傍にする・`squares` を常に 8 にする
- スキーマの `provenance` から `additionalProperties: false` を消す
- `toEventLine` が `"0.1"` を書く

---

## 7. やらないこと・限界

### 7.1 やらないこと

- **P-43 を直すこと**(`recorder.ts`・`usiEngine.ts` で meta に評価関数を残す)。この STEP は README から手で渡す暫定
- 玉の周りの数に**閾値・名前**を付けること、`candidateModes`・死因の規則・画面・コーチの文に使うこと(2.4)
- 企業へ出すかどうか・`1.0`(人間が決める。v0.1 の J-4)
- ajv などの外部ライブラリ(v0.1 の J-7)
- 既存の欄の意味を変えること(MAJOR になる)

### 7.2 限界

- **L-1 `evaluator.declared` は自己申告の文で、確かめていない**。記録の値がその評価関数で取られたことは、行からは確かめられない(P-43 が直るまで)
- **L-2 `record.sha256` はバイト列を指すだけ**で、評価関数・対局の相手を指さない(F-2)
- **L-3 玉の周りの数は、B と B′ の差を「作りどおり」に写す**(2.4)。診断に役立つかは別に測る
- **L-4 `evaluationAfter` の `measured` 以外の変種は、今の lib からは出ない**(F-7)。契約にはあるが実物では試されない
- **L-5 1. の数は使い捨ての道具で数えた**(型検査を通していない。校正は 2 つだけ ― 初期局面の 2 と D3 の Failure Event の数)。実装の STEP の試験で数え直す

---

## 8. Evidence の例(**v0.2 の欄で。例 1 件、切り出し**)

**元**: v0.1 計画 8. と同じ NNUE 版の記録 `records/d0-nnue/2026-09-12-live-30moves-claude-2-round2.jsonl` の分岐点 19。値は記録の実物(ply 18・20 の `engineReference`)と `SHA256SUMS` から写した。**v0.2 の実装の出力ではない**(実装はまだ)。

```json
{
  "schemaVersion": "0.2",
  "kifuId": "2026-09-12-live-30moves-claude-2-round2",
  "branchPly": 19,
  "provenance": {
    "record": { "path": "scripts/playtest/records/d0-nnue/2026-09-12-live-30moves-claude-2-round2.jsonl", "sha256": "08bc484691ec3c89792f67d23f19524f7f1a5047a597bcd013bfe8978ce17b4f" },
    "evaluator": { "declared": "YaneuraOu NNUE 9.80 / 水匠5 nn.bin sha256 768068f0d534a060… / FV_SCALE 24" }
  },
  "trigger": {
    "evaluationBefore": { "state": "measured", "scoreCp": -3517, "mate": null },
    "kingSurroundings": { "squares": 5, "own": 2 }
  },
  "branch": {
    "kinds": ["cpDrop"],
    "diffCp": -410,
    "evaluationAfter": { "state": "measured", "scoreCp": -3927, "mate": null, "bestmove": "2d2e", "afterPassScoreCp": 4725, "afterPassMate": null, "dropCp": 798 }
  },
  "consequences": { "checks": [22], "mate": null, "windowPlies": 5, "windowShort": false }
}
```

- **この切り出しは v0.2 のスキーマを通らない**(`required` の欄を落としている)。見せ方の例
- **EvaluationAfter は −3927 を欄で読める**(v0.1 では −3517 + (−410) の導出)
- `evaluator.declared` は **人が渡した文**(L-1)。この例の文は `records/d0-nnue/README.md` の値から作った
- `kingSurroundings` は K-7 の決定の形(ply 18 の局面で先手玉は 5i、盤の中の近傍 5 マスに先手の駒 2 枚)

---

## 10. 実装の記録(2026-09-15、実装担当 A。**予測の節 5. は書き換えていない**)

**基準は HEAD `1dfbaa7`。エンジンは使っていない。**C(D3b)に、D3b が `diagnose.ts`・`lib/failureEvent.ts`・`lib/failureEventSchema.ts`・`schemas/` とその試験に触らないことを先に確かめた(司令塔の指示)。

### 10.1 変えたもの

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/failureEvent.ts` | `KingSurroundings` と `kingSurroundingsOf(sfen)`(本番の `parsePosition` と shogiops の `parseSquareName` で盤を読み、先手玉の 8 近傍の盤の中のマスと先手の駒を数える)。`Trigger.kingSurroundings`(直前の行の局面)、`FailureEvent.branch.evaluationAfter`(直後の行の `evaluation` をそのまま)。**既存の欄の値は変えていない** |
| `scripts/playtest/lib/failureEvent.test.ts` | `branch` を `toEqual` で比べる 4 か所は、`evaluationAfter` を外して v0.1 までの 4 欄のまま比べる(`branchOf`)。v0.2 の lib の試験 3 件(evaluationAfter が直後の行の評価・kingSurroundingsOf の端・中央・隅・後手の駒・成り駒・Failure Event は直前の行から数える) |
| `scripts/playtest/lib/failureEventSchema.ts` | 版 `"0.2"`・`KNOWN_SCHEMA_VERSIONS`。`Provenance` の型、`recordSha256`・`pathForProvenance`・`provenanceMetaOf`・`buildProvenance`。`toEventLine(event, provenance)`(版は先頭、出どころは末尾)。`loadFailureEventSchema(version)` |
| `scripts/playtest/schemas/failure-event.v0.2.schema.json`(新規) | v0.1 のスキーマから生成し、2. の欄を足した(`evaluationAfter` は `evaluationBefore` の 6 変種の写し)。**`failure-event.v0.1.schema.json` は 1 バイトも変えていない** |
| `scripts/playtest/lib/failureEventSchema.test.ts` | 今の版(0.2)で T-2〜T-5 を回し直し、T-4 を `records/d0-nnue`・`records/d3-nnue` の 27 本に広げた。lib から出ない変種(`evaluationAfter` の `measured` 以外 5 つ・`kingSurroundings` の null)を手で書いた 1 行で、出どころの変種 8 つを組み立ての関数で作り、札の突き合わせに足した。T-5 のキーは 41 → 75。P-2〜P-5・P-7、パスの形、規則の写しの試験 |
| `scripts/playtest/diagnose.ts` | `--evaluator "<文>"`(空の文は誤りとして止める)。入力ごとにバイト列の sha256 を取り、`readGitState` とこのリポジトリの根で `buildProvenance` を組み、`--events` の各行に付ける |
| `scripts/playtest/diagnose.test.ts` | ソース照合の文字列。子プロセスに `--evaluator` を渡し、出どころを**組み立ての関数を通さずに**見る(ファイル名・そのバイトの sha256・`--evaluator` の文・`git rev-parse HEAD`・規則の値)。版の値を `"0.2"` に |

**検証器(`lib/eventSchema.ts`)は変えていない**(`enum` に数・`pattern` の先読み `^(?!/)` と `\S` は今の検証器で扱える)。

### 10.2 計画との違い

- **K-2 の読み替え(司令塔の決定、2026-09-15: 実装どおり)**: `pathForProvenance` は、根の中なら相対、**根の外なら、パスの中の `apps/server/engine/` から後ろを残し**、それも無ければファイル名だけにした。**理由 = K-2 の目的(絶対パス・ホームのユーザー名を出さない)は満たしたまま、`engine/` と `engine/nnue/` の区別(D1-FIX の注記・P-43 が頼る)を保つため。**決定の文言どおり「外ならファイル名だけ」にすると、記録を共有ツリーで取り `diagnose.ts` を worktree で回したとき、`enginePath` が `YaneuraOu-by-gcc` だけになり区別が消える。**4. の K-2 の表の文言は「根の外なら `apps/server/engine/` から後ろ、それも無ければファイル名だけ」と読み替える。**実記録 27 本はどれも `apps/server/engine/nnue/YaneuraOu-by-gcc`(10.5 の P-5)
- **`provenance` の位置**: 行の末尾(8. の例は `kifuId` の後に置いていたが、例は切り出し。スキーマは位置を約束しない。版の欄だけが先頭 ― v0 の J-1)
- **`record.meta.enginePath` を `string | null` にした**(2.1 の表は「無いことは無い」)。meta に欄が無い古い記録を「空の文字列」で埋めないため。無いときは `unrecordedKeys` に名前が入る
- **`analysis.dirty` は 3 値**(`dirty`・`clean`・`unmeasured`)。回したときの `readGitState` から「記録していない」は出ないので、スキーマの列挙から外した
- **P-1(131 件)と P-6(中央値)は試験に書かず、実測で照合した**(実記録の件数を試験に固定しない ― P-20)。P-2〜P-5・P-7 は試験に書いた
- **`kingSurroundings` を直前の行から数えることは見張られている**: B の監査の変異 X-1(直後の行から数える)が、lib の試験「Failure Event の kingSurroundings は直前の行から数える」で鳴った(A はこの変異を当てておらず、実装の記録に「見張っていない」と誤って書いていた ― 監査で直した)
- **限界**: `meta.enginePath` が相対パスの文字列なら、`diagnose.ts` を回した cwd を基準に直す(記録を取ったときの cwd は記録に無い)。今の `replay.ts` は絶対パスを書くので、コミット済みの記録には出ない

### 10.3 件数

- `tsc --noEmit -p scripts/playtest/tsconfig.json` exit 0・`typecheck:scripts` exit 0
- 変えた lib を読む 4 ファイル(`lib/failureEvent.test.ts`・`lib/failureEventSchema.test.ts`・`lib/eventSchema.test.ts`・`diagnose.test.ts`)は **72 件すべて通過**
- vitest の全件は **1 回だけ**回し、**35 ファイル 401 件すべて通過**(基準 389 + 12 = `failureEvent.test.ts` +3・`failureEventSchema.test.ts` +9)。`--testTimeout=60000`、load average 5.6〜8.1

### 10.4 変異(道具 `json-v02-mutate.py`、sha256 `b5afe0ff…`。**予測は当てる前に道具に試験名で書き、道具の sha を同じ逐次コマンドで残した**。4 ファイルと型検査だけを回した)

**適用 18 / 鳴った 18 / 沈黙 0 / 適用できなかった 0。予測(鳴るはず・鳴らないはずの両方)17 / 18。**全ファイルが元のバイト列に戻った。**別の理由の赤は 0 件。**中心 6 / 6。

| # | 壊し方 | 鳴った試験 |
|---|---|---|
| W-1 [中心] | `evaluationAfter` を直前の行から取る | lib の evaluationAfter・P-2・T-3 の lib から出る変種 |
| W-2 [中心] | `diagnose.ts` が記録のバイトでなくパスの文字列の sha256 を書く | 子プロセスだけ |
| W-3 | `evaluator.declared` を `enginePath` から推測して埋める | 出どころの変種・札の突き合わせ |
| W-4 | 規則の値を固定の値にする | 規則の写し |
| W-5 [中心] | 根の中のパスを絶対パスのまま書く | 17 件(パス・T-2・T-4・子プロセスほか)。**予測は外れた**(下) |
| W-6 | 根の外のエンジンのパスをファイル名だけにする | P-5・パスの形 |
| W-7 | 玉の周りに後手の駒も数える | kingSurroundingsOf |
| W-8 [中心] | 玉自身のマスも数える | 16 件(kingSurroundingsOf・T-2・子プロセスほか。squares が 9・6・4 になりスキーマで落ちる) |
| W-9 | 8 近傍を縦横の 4 近傍にする | 15 件(kingSurroundingsOf・T-2・子プロセスほか) |
| W-10 | `squares` を常に 8 にする | kingSurroundingsOf |
| W-11 | スキーマの `provenance` から `additionalProperties: false` を消す | T-5 の知らない欄を足す |
| W-12 [中心] | `toEventLine` が版 0.1 を書く | 16 件(T-2・T-4・子プロセス・P-7 ほか) |
| W-13 | `diagnose.ts` が `--evaluator` の文を渡さない | 子プロセスだけ |
| W-14 | 解析の `gitHead` を記録の meta から取る | 子プロセス・出どころの変種 |
| W-15 | `unrecordedKeys` を常に空にする | 出どころの変種・札の突き合わせ |
| W-16 | スキーマの `squares` に 4・9 を許す | v0.2 の欄の境目 |
| W-17 | スキーマの sha256 の形を緩める | v0.2 の欄の境目 |
| W-18 [中心] | `diagnose.ts` がすべての入力に 1 本目の記録の出どころを付ける | 子プロセスだけ |

**W-5 の予測の外れ(読みの誤り)**: 子プロセスは「鳴らない」と予測した(記録は根の外の一時ディレクトリなのでファイル名だけになり、変異の経路を通らないと読んだ)。実際は、子プロセスの固定例の meta の `enginePath` が `"-"` で、`path.resolve` が**根の中のパス**にするため変異の経路を通り、絶対パスになってスキーマの `^(?!/)` で落ちた。見張りの穴ではない。

### 10.5 予測との照合(5. を書き換えていない。実測は `diagnose.ts --events` を `records/d0-nnue`・`records/d3-nnue` に掛けた出力)

| # | 予測 | 実測 | 判定 |
|---|---|---|---|
| P-1 | 131 件(d0 22・B 50・B′ 59) | d0 22・B 50・B′ 59 = 131 | 的中 |
| P-2 | `evaluationAfter.state` は 131/131 が `measured` | d0 22/22・B 50/50・B′ 59/59(試験でも全件で直後の行の評価と等しい) | 的中 |
| P-3 | `bestmoveAtBefore` の `null` 12 件はすべて直前が `measured` でない | B 3/3・B′ 9/9(d0 は 0)。試験で全固定例・全実記録の等しさが通る | 的中 |
| P-4 | `record.sha256` は 27 本とも `SHA256SUMS` と一致 | 試験で d0 7/7・d3 20/20 | 的中 |
| P-5 | `unrecordedKeys` は 27 本とも `[]` | 27 本とも `[]`。`enginePath` は 27 本とも `apps/server/engine/nnue/YaneuraOu-by-gcc` | 的中 |
| P-6 | `kingSurroundings.own` の中央値 d0 4・B 4・B′ 2 | d0 4・B 4・B′ 2 | 的中 |
| P-7 | 0.2 の行は v0.2 を通り v0.1 で落ちる | 試験で全固定例・全実記録。0.2 で足した欄を外して版を 0.1 にした行は v0.1 を通る | 的中 |

- **既存の欄の名前は変えていない**(C の D3b の予測照合の道具が読む `branch.kinds`・`consequences.checks`・`candidateModes`・`trigger.shape` ほか)。C に伝えた

### 10.6 監査 B の REVISE への対応(書いたのは実装担当 A、2026-09-15。指摘は B の監査の必須 1・任意 3、変異 X-1・X-5・Z-1 は B のもの。**司令塔の決定: 必須 1 は nodes の 0 をそのまま写す、任意 a〜c も直す**)

| 指摘 | 直したこと |
|---|---|
| **必須 1**: `replay.ts --nodes 0`(時間で打ち切る探索)の記録は meta に `nodes: 0` を書くが、v0.2 のスキーマの `record.meta.nodes` は `minimum 1` で、`diagnose.ts` が契約を破る行を書く(コミット済みの記録には無いので試験は通っていた) | **`nodes` の `0` を `null` にしない**(`null` は「meta にその欄が無い」= `unrecordedKeys` に名前が並ぶ意味。0 の記録は欄がある)。v0.2 のスキーマを `minimum 0` にし、説明に「0 = 時間で打ち切る探索(`searchMode` が `"movetime"`)。`searchMode` と組で読む」。**v0.1 のスキーマは触らない**。4. の表の `searchMode`・`nodes`・`threads` の行に同じ一言。固定例 `metaMovetime`(`replay.ts --nodes 0` と同じ meta: `searchMode "movetime"`・`nodes 0`・`threads 1`・`referenceNodes`)を出どころの変種に足し、`nodes` が 0・`searchMode` が `"movetime"` のまま・`unrecordedKeys` が空であることを見る。札に `provenance.meta.nodes.zero`。欄の境目に「`nodes` 0 は通る・-1 は落ちる」 |
| **任意 a**: `--evaluator` を値なしで末尾に渡すと exit 0 で `declared` が null(「渡されない」と畳まれる)。空の文を止める行を見張る試験が無い(B の X-5 が沈黙) | `diagnose.ts` は `--evaluator` があるのに、値が無い・空・空白だけ・次の旗(`--` で始まる)なら誤りとして止める(`--evaluator --events <out>` は、直す前は `"--events"` を自己申告の文として受け取っていた)。子プロセスの試験を 1 つ足し、4 通りとも exit 0 以外・止めた文が標準エラーにある(別の理由の失敗と区別する)・`--events` を書かないことを見る |
| **任意 b**: 子プロセスの試験の固定例の `enginePath` が相対の `"-"` で、試験のプロセスと子プロセスで cwd が違うと別のパスに直り、`scripts/playtest` から回すと変異なしでも落ちる | 固定例の `enginePath` を、試験のファイルの位置から取った根からの絶対パス(`<根>/apps/server/engine/YaneuraOu-by-gcc`)にした。`scripts/playtest` から回しても通ることを確かめた。限界は 10.2 に 1 行(相対の `enginePath` は `diagnose.ts` の cwd を基準に直る) |
| **任意 c**: 10.2 の「`kingSurroundings` を直前の行から数えることは見張っていない」は実物と違う(B の X-1 が鳴った) | 10.2 を「見張られている」に直した |

**変えたファイル**: `schemas/failure-event.v0.2.schema.json`・`lib/failureEventSchema.ts`(コメント 1 行。動きは変えていない)・`lib/failureEventSchema.test.ts`・`diagnose.ts`・`diagnose.test.ts`・この計画書。`lib/failureEvent.ts`・`lib/failureEvent.test.ts` は変えていない。

**件数**: `tsc --noEmit -p scripts/playtest/tsconfig.json` exit 0・`typecheck:scripts` exit 0。4 ファイル **73 件すべて通過**(72 + `diagnose.test.ts` の 1)。`diagnose.test.ts` を `scripts/playtest` から回して 3 件通過。vitest の全件は **1 回だけ**、根から `--root scripts/playtest --testTimeout=60000` で **35 ファイル 402 件すべて通過**(load average 13.5〜17.9)。

**変異**(道具 `json-v02-revise-mutate.py`、sha256 `23e5fa30…`。**予測は当てる前に道具に試験名で書き、道具の sha を同じ逐次コマンドで残した**。足した試験の分だけ。Y-8 だけは `scripts/playtest` を cwd にして `diagnose.test.ts` を回した)

**適用 8 / 鳴った 8 / 沈黙 0 / 適用できなかった 0。予測(鳴るはず・鳴らないはずの両方)8 / 8。**全ファイルが元のバイト列に戻った。**別の理由の赤は 0 件。**中心 4 / 4。

| # | 壊し方 | 鳴った試験 |
|---|---|---|
| Y-1 [中心] | スキーマの `meta.nodes` を `minimum 1` に戻す | 出どころの変種・v0.2 の欄の境目 |
| Y-2 [中心] | `provenanceMetaOf` が `nodes` の 0 を null にする | 出どころの変種・札の突き合わせ |
| Y-3 [中心] | `diagnose.ts` の止め方を直す前(空の文だけ)に戻す | `--evaluator` を値なし…の試験だけ |
| Y-4 | 次の旗(`--events`)を自己申告の文として受け取る | 同上 |
| Y-5 | 空の文を止めない(B の X-5 と同じ) | 同上 |
| Y-6 | スキーマの `meta.nodes` から `minimum` を消す | v0.2 の欄の境目(-1 が通る) |
| Y-7 [中心] | 試験から movetime の固定例を外す | 出どころの変種・札の突き合わせ |
| Y-8 | 子プロセスの試験の固定例の `enginePath` を `"-"` に戻し、`scripts/playtest` から回す | 子プロセスだけ |

**再監査の後の直し(B の GO の任意 1、司令塔の決定)**: B の変異 Z-1(値なしの `--evaluator` を `undefined` として見ない。末尾の `--evaluator` で `trim` の TypeError になり、exit 1・`--events` なしは同じ)が沈黙した。試験は止めた文だけを見ており、tsx が標準エラーに出す code frame(`throw new Error("--evaluator …` のソースの行)にも一致したため。**`diagnose.test.ts` の 1 行を、例外の名前つきの `Error: --evaluator に評価関数の識別の文を渡してください` を見る形に直した**(`diagnose.ts` は変えていない)。道具 `json-v02-z1-mutate.py`(sha256 `647f551e…`、予測は当てる前に記入): 直す前は Z-1 が沈黙(B の結果を再現、予測 1/1)、直した後は **Z-1・Y-3・Y-4・Y-5 = 適用 4 / 鳴った 4 / 沈黙 0 / 適用できなかった 0、予測 4/4**(Z-1 は末尾の `--evaluator` の止めた文の確かめで落ちた)。`tsc` exit 0、`diagnose.test.ts` は根からも `scripts/playtest` からも 3 件通過、全件 1 回 35 ファイル 402 件通過(load average 7.5〜10.9)。
