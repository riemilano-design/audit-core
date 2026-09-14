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
| `….meta.searchMode`・`nodes`・`threads` | string / integer | 探索の条件 | `null` = meta にその欄が無い(**`unrecordedKeys` に名前を並べる**) | meta |
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
| **K-2** | パスの形 | **リポジトリの根からの相対パス**(外ならファイル名だけ)**+ `record.sha256`**。`enginePath` も同じ形に直す。**絶対パスはホームのユーザー名を含む**(F-1)。企業に見せるかは人間が決めるが、見せる前提の形にしておく | 絶対パスのまま写す(誰の機械かが出る) |
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
