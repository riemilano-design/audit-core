# STEP JSON v0.3-META 計画: Failure Event の出どころに、D0-SIDE の meta の欄を写す(2026-09-15。**計画のみ**。**実装 1e の見込み、事前読み f2**。**K-1〜K-7 は司令塔の決定済み(K-6 は f2 の事前読み R-1 を受けて MINOR、K-7 は S-2 を受けて変種 7)**)

## 0. この STEP の位置づけ

- **司令塔の依頼(2026-09-15)**: D0-SIDE 段 1(`5a2dc84`)・段 2(`e3b0a17`)が `replay.ts` の meta に書く欄を、Failure Event JSON の `provenance.record.meta` に写す。D0-SIDE 計画 §11.4 の「人に見せる出力(D4)の前に行う」を果たす
  - 写す欄は 7 つ(司令塔の数え方では 6 欄 ― `trailingMoveTruncated` と `truncatedTrailingMove` を 1 組と数える): `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`sideAlignmentChecked`・`trailingMoveTruncated`・`truncatedTrailingMove`
  - §11.4 は `sideAlignmentChecked` を挙げていない(§11.4 を書いた後に司令塔の決定で足された欄 ― D0-SIDE §12.7)。この STEP では 7 つとも写す
- **版は `0.3`**(欄を足すだけ = MINOR。v0.1 計画 3.2)
- **D2 の `counterfactual` はこの後の v0.4**(D2 計画 6. の Q-1 の決定。B の D2 計画は共有ツリーで未コミット)
- **基準は HEAD `e020b33`。エンジンは使っていない。**1. の数は、`e020b33` の使い捨ての worktree で、コミット済みの記録 74 本に今の `diagnose.ts --events` を掛けた出力と、meta 行を数える使い捨ての道具(`scratchpad/json03-probe/run.py`・`scratchpad/meta-count.py`)で数えた。**校正**: `d0-nnue` 22 件・`d3-nnue` 109 件は、v0.2 計画 10.5 の P-1(d0 22・B 50 + B′ 59 = 131)と一致し、`real-01` 5 件は REAL-01 計画 6. の表の「Failure Event 5」と一致した。worktree は数えた後に消した

### 0.1 司令塔が決めたこと(この計画の前提。**決定 D-1〜D-4**)

| # | 決定 |
|---|---|
| **D-1** | **古い記録(欄が meta に無い)では、その欄を出さず、既存の `unrecordedKeys` に名前を並べる。`false` は書かない**(「記録していない」を「回していない」「落としていない」に畳まない。D0-SIDE の null 禁止と同じ向き) |
| **D-2** | **条件つきの欄**(`startSfen`・`originalUserSide`・`plyOffset` は `mirrored` が `true` のときだけ / `truncatedTrailingMove` は `trailingMoveTruncated` が `true` のときだけ)は、**手書きの検証器(`lib/eventSchema.ts`)を広げず、`oneOf` と `const` の変種で縛る**(B が確かめた) |
| **D-3** | **試験で「meta に無い欄は必ず `unrecordedKeys` にある」「ある欄は `unrecordedKeys` に無い」を固定例で確かめる。**固定例は 3 つ以上: D0-SIDE 段 2 の回した記録(`mirrored: true`)・real-01 の 1 局(打ち切りの欄だけ)・古い meta の 1 局(欄なし)。中心を壊す変異(`false` を書く・`unrecordedKeys` に並べない・条件つきの欄を無条件にする など)を入れる。**文の読み方は下の読み替えで確定(K-1 の決定、司令塔 2026-09-15)** |
| **D-4** | 実装は計画 GO の後に司令塔が指示する(担当は 1e の見込み)。事前読みは f2(2026-09-15 に司令塔が依頼。real-02 の監査が来たらそちらが優先で、事前読みは中断してよい) |

**D-3 の文言と D-1 の間に 1 つ隙間がある(→ 4. の K-1)**: `mirrored: false` の局では `startSfen` は meta に無いが、「記録していない」のではなく「その変種に無い」。D-3 を文字どおり読むと、この `startSfen` も `unrecordedKeys` に並ぶことになり、D-1 の向き(「回していない」と「記録していない」を分ける)と逆になる。D-3 は **「meta に無い欄は、変種に無い(門の欄が `false`)か、`unrecordedKeys` にあるかの、ちょうど一方」** と読む。**この読み替えで確定(K-1 の決定、司令塔 2026-09-15)**。

---

## 1. 実物から分かった前提(**場所か数で書く**)

| # | 事実 | 場所・数 |
|---|---|---|
| F-1 | **コミット済みの記録は 74 本で、meta 行はどれも 1 行(計 74 行)。**`d0-nnue` 7・`d3-nnue` 20・`d3b-nnue-n2000` 20・`d-cost` 21(`c4m`・`l100k`・`l400k` の下)・`real-01` 6 | `git ls-files scripts/playtest/records` の `.jsonl`。道具で数えた |
| F-2 | **7 欄が 1 つも無い meta は 68 行**(`real-01` 以外のすべて)。**`real-01` の 6 行は `trailingMoveTruncated: true` と `truncatedTrailingMove` の 2 欄だけ**(`kifu-02` `8c8b+`・`03` `3i6f`・`05` `7a8b`・`06` `S*7a`・`08` `G*4b`・`10` `4c5b`。記録の `gitHead` は `5a2dc84`)。**`mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`sideAlignmentChecked` を持つ行は 0。`trailingMoveTruncated: false` の行も 0**(監査 A の数えと一致) | 道具で数えた |
| F-3 | `replay.ts` は meta の `extra` に `...sideMetaFields(sideAlignment), sideAlignmentChecked, ...truncationMetaFields(replayPlan)` を書く。**`sideMetaFields` と `sideAlignmentChecked` は同じコミット `e3b0a17` で入り、`truncationMetaFields` は `5a2dc84` で入った**(`git log -S`)。**`mirrored` があって `sideAlignmentChecked` が無い meta を書く `replay.ts` はコミットされていない**。打ち切りの欄だけがある meta は `5a2dc84`〜`b87b2f2` の `replay.ts` が書く(real-01 がそれ) | `replay.ts:209-211`(HEAD)、`lib/sideAlignment.ts:112-116`、`lib/replayPlan.ts:45-49` |
| F-4 | meta の型(`invariants/types.ts` の `MetaLine`)は 7 欄とも省略可能で、**値は 3 つ(`true`・`false`・欄が無い)**。`startSfen`・`plyOffset`(値は 1)・`originalUserSide`(値は `"gote"`)は `mirrored` が `true` のときだけ、`truncatedTrailingMove` は `trailingMoveTruncated` が `true` のときだけ書く。`sideAlignmentChecked` の `true` は照合して一致した回した局だけ、`false` は回していない局と `originalMoves` の無い回した局 | `invariants/types.ts:140-170` |
| F-5 | **v0.2 の `provenanceMetaOf` は 6 欄(`gitHead`・`dirty`・`enginePath`・`searchMode`・`nodes`・`threads`)だけを読み、無い欄も `null` で出し、`unrecordedKeys` に `Object.hasOwn` で名前を並べる。**スキーマの `record.meta` は `additionalProperties: false` で、`unrecordedKeys` の要素は 6 つの名前の `enum`。**だから今は、real-01 の「最後の手を落とした」ことが Failure Event の行から読めない**(meta にはあるが写していない) | `lib/failureEventSchema.ts:25`・`:81-96`、`schemas/failure-event.v0.2.schema.json` の `provenance.record.meta` |
| F-6 | **検証器が扱うキーワードは `type`・`enum`・`const`・`pattern`・`minimum`・`maximum`・`properties`・`required`・`additionalProperties`(false だけ)・`minItems`・`items`・`oneOf`(ちょうど 1 つ)だけ**。`not`・`allOf`・`anyOf`・`dependentRequired`・`contains` は無く、知らないキーワードは例外。`const` はプリミティブだけ。**「この欄が無い」を縛る方法は、その変種で `additionalProperties: false` にして欄を `properties` に書かないことだけ。配列の中身と変種の対応(`unrecordedKeys` にこの名前がある)は縛れない** | `lib/eventSchema.ts:19-32`・`:102-107`・`:128-135`・`:147-151` |
| F-7 | **74 本に HEAD の `diagnose.ts --events` を掛けると、Failure Event は 335 件**: `d0-nnue` 22・`d3-nnue` 109・`d3b-nnue-n2000` 133・`d-cost` 66・`real-01` 5(`kifu-02` 1・`05` 2(分岐点 17・77)・`06` 1・`10` 1。`03`・`08` は 0)。5 群とも exit 0。**335 件とも `unrecordedKeys` は `[]`** | 使い捨ての道具(出力は `scratchpad/json03-probe/*.events.jsonl`) |
| F-8 | **形の食い違う meta が Failure Event まで届く道がある**。`buildDiagnosisReport` は `initialSfenOf(meta)` を呼び、`mirrored: true` で `startSfen` が無ければ例外 →「数えられなかった」行(Event を出さない)。**しかし `mirrored: true`・`startSfen` あり・`plyOffset` が無い(や `originalUserSide` が違う)meta、`trailingMoveTruncated: true` で `truncatedTrailingMove` が無い meta は、そのまま数えられて Event を出す。**`replay.ts` はその形を書かない(`readSideAlignment` が固定棋譜の形を確かめてから meta を書く) | `lib/sideAlignment.ts:124-130`、`lib/failureEvent.ts:527-529` |
| F-9 | **回した記録(`mirrored: true`)はコミット済みに 0 本。**最初に来るのは C の real-03(後手の fixed 15 本。C の worktree `wt-real-03` の基点は `e3b0a17`)。real-02 の記録はまだ届いていない(記録を取った `gitHead` が分からないので、どの欄を持つかは実物で数える) | `git worktree list`、F-2 |
| F-10 | **版を読むもの**: `lib/failureEventSchema.ts:19`(`"0.2"`)・`:21`(`KNOWN_SCHEMA_VERSIONS`)・`diagnose.test.ts:161`(**文字列 `"0.2"` を直に見る**)・`lib/failureEventSchema.test.ts`(定数で見る。P-7 は v0.1 と比べる)・`diagnose.ts:9`(注記)。`provenanceMetaOf` を読むのは `failureEventSchema.ts:115` と試験の P-5(`:498`) | `git grep` |
| F-11 | 回した局の固定例: `FOLD_START`(平手・後手番に `3c3d` を当てた局面)と `FOLD_MOVES`(6 手)が、`lib/failureEvent.test.ts:408-409`・`lib/intentStatement.test.ts:373-374`・`check.test.ts:173`・`invariants/i9…test.ts:169`・`lib/scanCompare.test.ts:212-213` の **5 か所にそれぞれ手で書いてあり、`failureEventFixtures.ts` からは出していない** | `git grep` |
| F-12 | `records/real-01` には `SHA256SUMS` がある(`d3b-nnue-n2000`・`d-cost/{c4m,l100k,l400k}` にもある)。v0.2 の T-4・P-4 の `RECORD_DIRS` は `d0-nnue`・`d3-nnue` の 2 つだけ | `git ls-files`、`lib/failureEventSchema.test.ts` の `RECORD_DIRS` |

---

## 2. v0.3 に足す欄(**決定は 0.1 の D-1〜D-4 と 4. の K-1〜K-5**)

「無い」の規約は v0.1 と同じ 3 種(キーが無い = その変種に無い / `null` = 欄はあるが値が無い / `[]` = 見た範囲で 0 件)。**7 欄は `null` を使わない**(D0-SIDE と同じ)。

### 2.1 欄(すべて `provenance.record.meta` の中)

| 欄 | 型 | 出るとき | 変種に無い(キーが無く、`unrecordedKeys` にも無い) | 記録していない(キーが無く、`unrecordedKeys` にある) |
|---|---|---|---|---|
| `mirrored` | boolean | meta にあるとき(`e3b0a17` 以降の `replay.ts` は常に書く) | ― | meta に無い(段 2 より前の記録)。**`sideAlignmentChecked` も無いときに限る**(片方だけがあるのは K-3 で止まる) |
| `originalUserSide` | `"gote"`(const) | `mirrored` が `true` | `mirrored` が `false` | `mirrored` が meta に無い(K-1) |
| `plyOffset` | `1`(const) | 同上 | 同上 | 同上 |
| `startSfen` | string | 同上 | 同上 | 同上 |
| `sideAlignmentChecked` | boolean | meta にあるとき(`e3b0a17` 以降は常に書く)。**`true` は `mirrored` が `true` のときだけ**(K-2)。**門を持たない欄として扱う** | ― | meta に無い。**`mirrored` も無いときに限る**(片方だけがあるのは K-3 で止まる) |
| `trailingMoveTruncated` | boolean | meta にあるとき(`5a2dc84` 以降は常に書く) | ― | meta に無い(段 1 より前の記録)。**そろえの組も無いときに限る**(そろえの組があって打ち切りの組が無いのは K-3 で止まる ― K-7) |
| `truncatedTrailingMove` | string(USI) | `trailingMoveTruncated` が `true` | `trailingMoveTruncated` が `false` | `trailingMoveTruncated` が meta に無い(K-1)。**そろえの組も無いときに限る**(K-7) |

- **値は meta をそのまま写す**(`startSfen` を直さない・`truncatedTrailingMove` を回し戻さない)。どの座標系で読むかは `mirrored` で決まる(D0-SIDE Q-7。回した局の手は、本人を先手にそろえた座標)
- **v0.2 の 6 欄の書き方は変えない**(無い欄は `null` + `unrecordedKeys`)。**新しい 7 欄だけが「キーを出さない + `unrecordedKeys`」**になり、1 つの object の中で 2 つの書き方が並ぶ。6 欄を「キーを出さない」に揃えると、v0.2 の読み手が頼る欄の意味が変わり **MAJOR** になるので揃えない(3.)
- **`unrecordedKeys` の意味**(スキーマの説明も直す): v0.2 は「meta に無かった欄の名前」。v0.3 は **「meta に無く、その変種に無いとも言えない欄の名前」**。v0.2 の 6 欄については同じ意味(6 欄には変種が無い)

### 2.2 3 つの形(見本。**v0.3 の実装の出力ではない**)

```jsonc
// 古い記録(F-2 の 68 本)。K-1 の決定 (b)
"meta": { "gitHead": "…", "dirty": "clean", "enginePath": "apps/server/engine/nnue/YaneuraOu-by-gcc", "searchMode": "nodes", "nodes": 4000000, "threads": 1,
          "unrecordedKeys": ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"] }

// real-01 の kifu-02(打ち切りの欄だけ)
"meta": { "gitHead": "5a2dc84…", …, "trailingMoveTruncated": true, "truncatedTrailingMove": "8c8b+",
          "unrecordedKeys": ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked"] }

// 回して照合した局(e3b0a17 以降の replay.ts。手数が偶数で落としていない)
"meta": { "gitHead": "…", …, "mirrored": true, "originalUserSide": "gote", "plyOffset": 1, "startSfen": "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2",
          "sideAlignmentChecked": true, "trailingMoveTruncated": false, "unrecordedKeys": [] }
```

### 2.3 スキーマの形(D-2)

`record.meta` を **`oneOf: [null, 変種 7 つ]`** にする。7 つ = **そろえの組が無い × 打ち切りの組 3 状態(無い・落としていない・落とした)の 3 つ + そろえの組 2 状態(回していない・回した)× 打ち切りの組 2 状態(落としていない・落とした)の 4 つ**(K-2・K-7 の決定 (a))。**そろえの組があって打ち切りの組が無い 2 つは置かない**(どの `replay.ts` も書かない ― F-3)。

| そろえの組 | 欄 |
|---|---|
| 無い | `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`sideAlignmentChecked` を `properties` に書かない |
| 回していない | `mirrored: const false`・`sideAlignmentChecked: const false`(どちらも required)。`originalUserSide`・`plyOffset`・`startSfen` は書かない |
| 回した | `mirrored: const true`・`originalUserSide: const "gote"`・`plyOffset: const 1`・`startSfen: string`・`sideAlignmentChecked: boolean`(すべて required) |

| 打ち切りの組 | 欄 |
|---|---|
| 無い | `trailingMoveTruncated`・`truncatedTrailingMove` を書かない |
| 落としていない | `trailingMoveTruncated: const false`(required)。`truncatedTrailingMove` は書かない |
| 落とした | `trailingMoveTruncated: const true`・`truncatedTrailingMove: string`(USI の `pattern`)(どちらも required) |

- 7 つの変種は、v0.2 の 6 欄 + `unrecordedKeys` を同じ形で持ち、`additionalProperties: false`。**変種どうしは `const` と欄の有無で排他になる**(`oneOf` はちょうど 1 つ ― F-6)
- **スキーマのファイルは v0.2 のファイルから道具で生成する**(v0.2 も v0.1 から生成した ― v0.2 計画 10.1)。手で 7 つ書き写さない
- `unrecordedKeys` の `items.enum` を 13 の名前に広げる(**版の読み方は K-6**)。**中身と変種の対応はスキーマでは縛れない**(F-6)→ 試験で見る(6.2・L-1)
- **lib(`provenanceMetaOf`)も同じ縛りを、食い違った欄の名前つきで確かめる**(K-3。`const` と 2 つの `pattern` まで)。`pattern` の文字列は lib の定数とスキーマで同じであることを試験で見る
- **変種は 7 つ(K-7 の決定)**。「そろえの組あり × 打ち切りの組なし」の meta は、lib が K-3 の食い違いとして止める

---

## 3. 版

- **`schemaVersion: "0.3"`**。**スキーマのファイルを 1 つ増やす**(`scripts/playtest/schemas/failure-event.v0.3.schema.json`)。**`v0.1`・`v0.2` のファイルは 1 バイトも変えない**
- **MINOR の根拠**: 足すのは `record.meta` の 7 欄と `unrecordedKeys` の名前だけで、v0.2 の 6 欄の値と `null` の規約は変えない(2.1)。v0.1 計画 3.2 の MAJOR の 2 行に字面で当たる点(f2 の事前読み R-1: (1) `unrecordedKeys` の `items.enum` を 6 から 13 に広げる = 列挙の値を足す(J-5)/ (2) `unrecordedKeys` の説明を変える = 既存の欄の意味を変える)は、**司令塔の決定(2026-09-15。K-6)で次のとおり読む**:
  - **(1) J-5 の読み方**: J-5「列挙の値を足す = MAJOR」の根拠は、読む側が列挙の値で分岐し、知らない値を黙って落とすと「無い」を 0 に畳むことにある(v0.1 計画 4. の J-5 の理由)。`unrecordedKeys` の `items.enum` は**欄の名前の集合**で、読む側は自分が読む欄の名前を引くだけ。v0.2 の読み手が知らない名前(新しい 7 欄)は、その読み手が読まない欄の名前なので、落としても意味が畳まれない。したがって **同じ版で足した任意の欄の名前を `unrecordedKeys` の列挙に足すことは「任意の欄を足す」の一部で MINOR**
  - **(2) 意味**: **v0.2 の 6 欄については `unrecordedKeys` の意味(meta に欄が無い)を変えない。新しい 7 欄では「meta に無く、門の欄が `false` でない欄」に限る(§2.1・K-1)。この限定は v0.2 の読み手が読まない欄にしか掛からないので、J-5 の読み方(欄の名前の列挙に、同じ版で足した任意の欄の名前を足すのは MINOR)と同じ理由で MINOR。J-5 の変更ではない。**
  - **これは J-5 の読み方の確定であり、J-5 の変更ではない(v0.1 計画は直さない)**。MAJOR と読むと `1.0` = Gate 3 以降の人間の判断(J-4)になり、今は当たらない
- v0.2 のスキーマは `record.meta` が `additionalProperties: false` で `schemaVersion` が `const "0.2"` なので、**0.3 の行は v0.2 のスキーマでは落ちる**(意図どおり。読む側は `schemaVersion` でスキーマを選ぶ)

---

## 4. 決定(司令塔、2026-09-15。**K-1〜K-5 はすべて推奨どおり**。**K-6(f2 の事前読み R-1)・K-7(S-2)も決定**)

| # | 判断 | 決定(推奨どおり) | 選ばなかった案とその理由 |
|---|---|---|---|
| **K-1** | 門の欄(`mirrored`・`trailingMoveTruncated`)が meta に無いとき、**従う欄**(`originalUserSide`・`plyOffset`・`startSfen` / `truncatedTrailingMove`)の名前も `unrecordedKeys` に並べるか | **(b) 並べる。**規則は「meta に無い欄は、変種に無い(門が `false`)か `unrecordedKeys` にあるかの、ちょうど一方」。読む側は欄ごとに `unrecordedKeys` を引けば「記録していない」が分かる。D-3 の文言にいちばん近い | (a) 門の名前だけを並べる: 従う欄が「記録していない」ことを、門の名前から推し量らせる。D-3 の「meta に無い欄は必ず `unrecordedKeys` にある」から外れる欄が、門が `false` のときに加えて、門が無いときにも出る |
| **K-2** | `sideAlignmentChecked` を、スキーマで `mirrored` と結びつけるか | **(a) 結びつける**(そろえの組: 無い / `mirrored: false` なら `false` だけ / `mirrored: true` なら boolean)。変種は 3 × 3 = **9**(→ K-7 の決定で、書かれない 2 組を外して **7**)。F-3 のとおり、2 つを別々に書いた `replay.ts` はコミットされていない。「照合したのに回していない」(`mirrored: false` で `true`)をスキーマで落とせる | (b) 独立にする: 変種は 3 × 3 × 2 = 18。書かれない組(`mirrored` だけ・`sideAlignmentChecked` だけ・回していないのに `true`)を契約が通す |
| **K-3** | 1. の F-8 の、**どの変種にも合わない meta**(門が boolean でない・`mirrored: true` なのに従う欄が欠ける/値が違う・`mirrored: false` に従う欄がある・`sideAlignmentChecked` と `mirrored` の組が 2.3 に無い・`trailingMoveTruncated: true` で `truncatedTrailingMove` が無いか文字列でない・`false` なのにある・門が無いのに従う欄だけある・**そろえの組があるのに打ち切りの組が無い(K-7)**・**`startSfen` が K-5 の `pattern` に合わない(空・空白で区切った 4 つの部分でない)・`truncatedTrailingMove` が USI の `pattern` に合わない(`"8c8"` など)**)を `--events` に写すとき。**判定は「2.3 のどの変種にも合わない」で、`const` と 2 つの `pattern` まで含む**(f2 の事前読み R-2: 値の形を見ないと、スキーマを通らない行を黙って書く (b) と同じになる) | **(a) 写さずに止める。**`provenanceMetaOf`(か、そこから呼ぶ読み取りの関数)が名前つきの例外を投げ、`diagnose.ts` は **`--events` のファイルを書かずに 0 でない exit**(Markdown の表は既に出ている)。`replay.ts` が meta を書く前に止まる・`check.ts` が形の食い違う meta で止まる(D0-SIDE §12.8)と同じ向き | (b) そのまま写す: スキーマを通らない行を黙って書く(書くときに誰も照らさない)/ (c) 欄を `unrecordedKeys` に並べる: 「形が壊れている」を「記録していない」に畳む(D-1 の向きに反する)/ (d) `diagnose.ts` が書く前に各行をスキーマに照らす: 同じ効果だが、何が食い違ったかが「oneOf の 0 個に合った」になり読めない |
| **K-4** | 欄の順(試験の `toEqual` と見本のため。**スキーマは順を約束しない**) | **v0.2 の 6 欄 → `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`sideAlignmentChecked`・`trailingMoveTruncated`・`truncatedTrailingMove` → `unrecordedKeys`。**`unrecordedKeys` の中も同じ順(6 欄の後に 7 欄) | meta の欄の順をそのまま使う(記録ごとに順が変わり、試験の期待値が記録に依存する) |
| **K-5** | 値の縛りの強さ | **`plyOffset: const 1`・`originalUserSide: const "gote"`**(D0-SIDE の案 1 と `MetaLine` の型のとおり)。**`startSfen` は `type: string` と空白で区切った 4 つの部分の `pattern` だけ**(盤の正しさは `replay.ts`・`initialSfenOf` の役目)。**`truncatedTrailingMove` は USI の `pattern`**(盤上の手 `^[1-9][a-i][1-9][a-i]\+?$` か打つ手 `^[PLNSGBR]\*[1-9][a-i]$`。`lib/usiRotation.ts` と同じ形) | `plyOffset: integer ≥ 1`・`originalUserSide: enum` にしておく: 先手を後手にそろえる・畳む手数を変える日が来たら、`replay.ts` の意味も変わる。そのとき版を上げて広げる(列挙を足すのは MAJOR ― v0.1 の J-5) |
| **K-6** | `unrecordedKeys` の名前を 13 に広げること(列挙の値を足す)と、その説明を変えることが、v0.1 計画 3.2 の MAJOR の 2 行(J-5・「既存の欄の意味を変える」)に当たるか(f2 の事前読み R-1。3.) | **決定(司令塔、2026-09-15): (a) MINOR。読み方の文は 3. に書いた**(J-5 の変更ではなく読み方の確定。`kinds`・`state` など、読む側が値で分岐する列挙に値を足すのは MAJOR のまま) | (b) 字面どおり守る: 7 欄の名前を別の配列(例: `unrecordedSideKeys`)に並べ、`unrecordedKeys` の `enum` と説明を変えない。字面どおり MINOR になるが、D-1 の「既存の `unrecordedKeys` に並べる」を変えることになり、読む側は 2 つの配列を合わせて引く / (c) MAJOR にする: 次は `1.0` で、J-4 により人間の判断(Gate 3 以降)。この STEP が止まる |
| **K-7** | 当初の 2.3 の変種 9 のうち、**そろえの組がある(回していない・回した)× 打ち切りの組が無い**の 2 つは、どの `replay.ts` も書かない(F-3: そろえの欄を書く `e3b0a17` 以降の `replay.ts` は、打ち切りの欄も必ず書く)。これを契約が通すか(f2 の事前読み S-2) | **決定(司令塔、2026-09-15): (a) 7 つにする**(そろえの組が無い × 打ち切りの組 3 状態 = 3、そろえの組 2 状態 × 打ち切りの組 2 状態(落としていない・落とした)= 4)。K-2 と同じ理由(書かれない組を契約が通さない)。K-3 の食い違いに「そろえの組があるのに打ち切りの組が無い」を足す | (b) 9 つのまま、「通すが書かれない」と 7.2 に書く: 書かれない形の meta が来ても、lib とスキーマが黙って通す |

---

## 5. 期待値(**実装の STEP が測る前に置く値**。1. の使い捨ての道具で数えた値なので「再現すべき値」として置く。K-1 は決定 (b))

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| P-1 | 74 本の Failure Event は **335 件**(d0 22・d3 109・d3b 133・d-cost 66・real-01 5)。v0.3 にしても件数と、`schemaVersion`・`provenance.record.meta` 以外の欄の値は変わらない | 件数か、それ以外の欄の値が 1 つでも変わる |
| P-2 | **68 本(330 件)の `unrecordedKeys` は 7 欄の名前 7 つ**(K-4 の順)。7 欄のキーはどれも出ない | 名前が欠ける・キーが出る・`false` が出る |
| P-3 | **real-01 の 5 件の `unrecordedKeys` は `mirrored`・`originalUserSide`・`plyOffset`・`startSfen`・`sideAlignmentChecked` の 5 つ**で、`trailingMoveTruncated: true`・`truncatedTrailingMove` は記録の meta と同じ(`kifu-02` `8c8b+`・`05` `7a8b` ×2・`06` `S*7a`・`10` `4c5b`) | どれか 1 つでも違う |
| P-4 | 335 件で `mirrored`・`sideAlignmentChecked` のキーが出る行は **0**、`trailingMoveTruncated: false` の行も **0**(F-2) | 1 件でも出る |
| P-5 | 335 件と全固定例で、7 欄のそれぞれが、**元の meta を基準に**次の 3 つを満たす: **キーがある ⇔ meta にある** / **名前が `unrecordedKeys` にある ⇔ meta に無く、門が `false` でない**(門の欄そのものと、門を持たない `sideAlignmentChecked` は「meta に無い」だけ。門が `true` で従う欄が欠ける・`mirrored` と `sideAlignmentChecked` の片方だけがある・そろえの組があって打ち切りの組が無い(K-7)は、どれも K-3 で止まるので行にならない)/ **変種に無い ⇔ meta に無く、門が `false`**(D-3・K-1。f2 の事前読み S-1: 「ちょうど 1 つ」だけでは、meta に無い欄のキーを出して名前を並べない行が通る) | 1 つでも成り立たない |
| P-6 | 335 件の行から 7 欄と 7 つの名前を取り除き、版を `"0.2"` にすると、**v0.2 のスキーマを通り、HEAD `e020b33` の `diagnose.ts` の出力(`scratchpad/json03-probe/*.events.jsonl`。sha256 と作り直す手順は L-6)と、`provenance.analysis`(回したときの `gitHead`・`dirty`)を除いて一致する** | 通らない・一致しない |
| P-7 | 0.3 の行はすべて v0.3 のスキーマを通り、v0.2 のスキーマでは落ちる | どちらかが逆 |

---

## 6. 実装の STEP でやること(**この計画の GO とコミットの後、司令塔の指示で**)

### 6.1 変えるもの

| ファイル | 中身 |
|---|---|
| `scripts/playtest/lib/failureEventSchema.ts` | 版を `"0.3"` に、`KNOWN_SCHEMA_VERSIONS` に `"0.3"`。`ProvenanceMeta` に 7 欄(2.3 の組の型で)。`provenanceMetaOf` が 7 欄を K-1・K-4 のとおり写し、K-3 の食い違いで例外 |
| `scripts/playtest/schemas/failure-event.v0.3.schema.json`(新規) | v0.2 のファイルから道具で生成(2.3)。`$id`・`title`・`description`・`schemaVersion` の `const`・`record.meta` の `oneOf`・`unrecordedKeys` の `enum` と説明。**v0.1・v0.2 のファイルは変えない** |
| `scripts/playtest/lib/failureEventSchema.test.ts` | 6.2 |
| `scripts/playtest/diagnose.test.ts` | `"0.2"` を `"0.3"` に(F-10)。子プロセスに回した記録を足す(6.2) |
| `scripts/playtest/diagnose.ts` | 冒頭の注記の版(`:9`)。K-3 (a) の止まり方は lib の例外がそのまま外へ出る形で、**動きの変更は要らない見込み**(実装で確かめる) |

**変えないもの**: `lib/failureEvent.ts`(Event の値)・`invariants/types.ts`(`MetaLine`)・`replay.ts`・`lib/sideAlignment.ts`・`lib/replayPlan.ts`・`check.ts`・`lib/eventSchema.ts`(D-2)。

### 6.2 試験

- **D-3 の固定例(3 つ以上。すべて `provenanceMetaOf` / `buildProvenance` を通して 1 行に付け、スキーマに照らす)**
  - **回した記録**: meta の 7 欄を**本番の関数で作る**(`sideMetaFields(alignMovesToSente(…, "gote"))`・`sideAlignmentChecked`・`truncationMetaFields(planReplayMoves(…))`)。`sideAlignmentChecked` の `true` と `false`(`originalMoves` の無い回した局)、打ち切りの `true` と `false` を埋める。**手で書いた 1 つ(2.2 の 3 つ目)と本番の関数の出力が一致することも見る**(校正)
  - **real-01 の 1 局**: `RECORD_DIRS` に `real-01` を足す(T-4・P-4 の `SHA256SUMS` も掛かる ― F-12)。P-3 の値を `kifu-02` で見る
  - **古い meta の 1 局**: 既存の `FIXTURE_META`(7 欄なし)と、コミット済みの `d0-nnue`・`d3-nnue`
  - `mirrored: false` の局(従う欄が「変種に無い」ことの境目)
- **D-3 の対応の試験**(P-5): すべての固定例と実記録の行で、7 欄ごとに **元の meta を基準に** P-5 の 3 つの ⇔ を見る。**門の分類(どの欄がどの門に従うか)は lib から import せず、試験の中で書く。固定例ごとに、期待する `unrecordedKeys` を手で書いて `toEqual` で比べる**(同じ分類を lib と試験で共有すると、M-4・M-5 が両側で揃って沈黙する ― f2 の事前読み S-1)。**v0.2 の 6 欄は「`unrecordedKeys` にある ⇔ 元の meta に無い」**(今の P-5 は「空」しか見ていない)
- **札の突き合わせ**(v0.2 の T-3 と同じ形)に足す: `provenance.meta.side.{absent,notMirrored,mirroredChecked,mirroredUnchecked}`・`provenance.meta.truncation.{absent,notTruncated,truncated}`、および 7 変種それぞれ
- **スキーマの境目**(手で書き換えた 1 行): `mirrored: false` に `startSfen` → 落ちる / `mirrored: true` で `plyOffset` が無い → 落ちる / `plyOffset: 2`・`originalUserSide: "sente"` → 落ちる / `mirrored: false` で `sideAlignmentChecked: true` → 落ちる / `mirrored` が無いのに `sideAlignmentChecked` → 落ちる / `trailingMoveTruncated: false` に `truncatedTrailingMove` → 落ちる / `truncatedTrailingMove: "8c8"` → 落ちる / そろえの組があって打ち切りの組が無い(`mirrored: false`・`sideAlignmentChecked: false` だけ、`mirrored: true` の 5 欄だけ)→ 落ちる(K-7) / 7 欄のどれかが `null` → 落ちる / 知らない欄 → 落ちる
- **K-3**: 食い違いの形ごとに `provenanceMetaOf` が例外を投げ、例外の文に食い違った欄の名前がある。**値の形の食い違い(`truncatedTrailingMove: "8c8"`・`startSfen` が空・4 つの部分でない)も入れる**(R-2)。lib の `pattern` の定数とスキーマの `pattern` の文字列が同じであることを見る。子プロセスで 1 つ(`--events` を書かず exit 0 以外、止めた文が標準エラーにある ― v0.2 の Z-1 の教訓で、例外の名前つきの文を見る)。**子プロセスでは `--events` のパスに前もってファイルを置き、止まった後もバイト列が変わらない(前の回のファイルが残る)ことを見る**(f2 の事前読み S-5。L-4)
- **子プロセス**(`diagnose.test.ts`): 回した記録を 1 本足す。**`FOLD_START`・`FOLD_MOVES` に評価を植え、Failure Event が 1 件以上出ることを先に確かめる**(0 件なら何も見ない試験になる。出なければ別の手順を探す)。書かれた行の `provenance.record.meta` の 7 欄を、**組み立ての関数を通さずに**記録の meta と比べる。`FOLD_START` を `failureEventFixtures.ts` から出すかは実装で決める(F-11。5 か所の手書きはこの STEP では触らない)
- P-6・P-7 を試験に書く(P-1 の件数は試験に固定しない ― P-20。実装の記録で数える)

### 6.3 変異(**中心を壊すもの ― 規則 11.8**。予測は実装の後、当てる前に書く)

| # | 壊し方 | 見張る試験 |
|---|---|---|
| M-1 [中心] | 古い記録で 7 欄に `false` を書く(`mirrored`・`trailingMoveTruncated`・`sideAlignmentChecked` のどれか 1 つずつ) | 対応の試験・P-2・T-4 |
| M-2 [中心] | 新しい 7 欄の名前を `unrecordedKeys` に並べない | 対応の試験・P-2・P-3 |
| M-3 [中心] | 従う欄を無条件に写す(`mirrored: false` でも `startSfen` のキーを出す / `trailingMoveTruncated: false` でも `truncatedTrailingMove` のキーを出す) | スキーマ・対応の試験 |
| M-4 [中心] | 門が `false` のときも従う欄の名前を `unrecordedKeys` に並べる | 対応の試験 |
| M-5 | 門が無いとき従う欄の名前を並べない(K-1 を (a) にする) | 対応の試験・P-2 |
| M-6 [中心] | K-3 の食い違いを例外にせず写す | K-3 の試験(lib・子プロセス) |
| M-7 | スキーマの `plyOffset` の `const` を外す / `originalUserSide` の `const` を外す | 境目 |
| M-8 | スキーマで `sideAlignmentChecked` を `mirrored` と独立にする(K-2 を (b) にする) | 境目 |
| M-9 | 無い欄を `null` で出す | スキーマ・対応の試験 |
| M-10 [中心] | `toEventLine` が `"0.2"` を書く | T-2・P-7・子プロセス |
| M-11 | `truncatedTrailingMove` を meta でなく別の値(空文字・`trailingMoveTruncated` の文字列)にする | P-3・子プロセス |
| M-12 | v0.2 の 6 欄の書き方を変える(6 欄も「キーを出さない」にする) | 出どころの変種・P-6 |
| M-13 | `diagnose.ts` の子プロセスで、回した記録の meta でなく 1 本目の記録の meta を付ける | 子プロセスだけ |
| M-14 | スキーマの `record.meta` の変種を 1 つ消す(例: 回した × 落とした) | 札の突き合わせ・境目 |
| M-15 [中心] | lib が値の形を確かめない(`truncatedTrailingMove` の USI の `pattern` / `startSfen` の `pattern` を見ずに写す) | K-3 の試験(値の形)(f2 の事前読み R-2) |
| M-16 [中心] | スキーマに「そろえの組あり × 打ち切りの組なし」の変種を足す(9 つに戻す)/ lib がその組を止めない(K-7) | 境目・K-3 の試験 |

---

## 7. やらないこと・限界

### 7.1 やらないこと

- **D2 の `counterfactual`**(v0.4。D2 計画 6. の Q-1)
- `replay.ts`・`MetaLine`・`check.ts`・`scan-compare` の変更(meta の欄を足す・読み方を変える)
- **v0.2 の 6 欄の `null` の規約を変えること**(MAJOR。2.1)
- Markdown の表(`diagnose.ts` の標準出力)に 7 欄を出すこと(人に見せる出力は D4)
- `lib/eventSchema.ts` にキーワードを足すこと(D-2)
- `FOLD_START` の 5 か所の手書きをまとめること(F-11)

### 7.2 限界

- **L-1 スキーマは `unrecordedKeys` の中身と欄の有無の対応を縛れない**(F-6)。見張りは 6.2 の対応の試験だけで、**スキーマを通っても「欄が無いのに名前が無い」行はありうる**
- **L-2 回した記録はコミット済みに 0 本**(F-9)。`mirrored: true` の変種は、C の real-03 がコミットされるまで固定例でしか試されない。**real-03 のコミットの後に、その回した記録の固定例を 1 本足す**(`RECORD_DIRS` に `real-03` を足す)
- **L-3 `sideAlignmentChecked: false` は 2 つの意味を持つ**(回していない / `originalMoves` の無い回した局)。行では `mirrored` と組で読む(D0-SIDE §12.8)
- **L-4 K-3 (a) は入力 1 本の食い違いで、その回の `--events` を全部書かない**。どの入力で止まったかは例外の文に書く。**止まったとき、前の回に同じパスへ書いた `--events` のファイルは消えずに残る**(`writeFileSync` は最後の 1 回だけ ― `diagnose.ts:101`。f2 の事前読み S-5)。読む側は exit code で見分ける(6.2 の子プロセスで見る)
- **L-5 1. の数は使い捨ての道具で数えた**。校正は 3 つ: v0.2 の P-1 の 131 件(d0 + d3)・REAL-01 計画 6. の 5 件・**D3b 計画 §11.5 の B 60 + B′ 73 = 133 件**(d3b)。`d-cost` 66 件は照らす先の数を持たない。**f2 が事前読みで `e020b33` の worktree から独立に再現した**(meta 74 行・7 欄なし 68・Event 335 件、5 群とも exit 0、`d-cost` は群に分けて 22 + 23 + 21 = 66)。実装の STEP の試験と実測で数え直す
- **L-6 P-6 が頼る道具の出力**(`scratchpad/json03-probe/`。HEAD `e020b33` の `diagnose.ts --events`。**`provenance.analysis` は回したときの値**): `d0-nnue.events.jsonl` 22 行 `e57553b2198283b9e745f736581cb9172b45530a5e6cb3f19c6f7ee0c6f07b76`・`d3-nnue.events.jsonl` 109 行 `dd10b9a9ed07c6d483a4e28ca33f41e52a784a5866fb06e8d9a6f9c7bc10c300`・`d3b-nnue-n2000.events.jsonl` 133 行 `751e2223167ba9e7f243ad1d6917c9fa6d1e06c9438a51cf15d085428b610a6f`・`d-cost.events.jsonl` 66 行 `6920237fb429683b52e59dbf3121c9a5ec9bc73e3d72a769ecb877a4d1f6bf75`・`real-01.events.jsonl` 5 行 `9e6d1cc8418ea36c92d22da17b77151f82736ff3256a411bc613ec8e446f4bf1`。**作り直す手順**: `e020b33` の worktree の根で、群ごとに `npx tsx scripts/playtest/diagnose.ts <その群の .jsonl をパスの昇順で。d-cost は下のフォルダまで> --events <出力>`。scratchpad が消えていても、この手順で作り直せる(`analysis` 以外は同じになるはず)
- **L-7 P-52 の処遇は V0.3-META の後に決める**(`a84689b` で登録。回した記録の手順を `startSfen` を使わずに平手から並べると、D1 の `actualContinuation` が `IllegalMoveError` で止まり「数えられなかった」になる。K-3 と同じ向きの限界 ― 司令塔、2026-09-15)
