# STEP FIG-2 (a) 計画 ― 候補形の検索の道具(納品レーン。2026-09-26)

司令塔の指示(2026-09-26)で着手。**この計画の承認 → 実装 → 独立監査 GO → コミット**の順。見せ方 (b) は司令塔。

## 1. 何を作るか

実戦の局面から、**「この局面では、こういう自玉側の形が選択肢になります」**と言える候補を出す小さな道具。
**「この囲いが正解です」ではない**(人間の指定)。

- 新しいファイル 2 本だけ: `scripts/playtest/fig/shapeCandidates.ts`(純関数の層)と `scripts/playtest/fig/shapeCandidates.test.ts`。
  CLI が要るなら `scripts/playtest/figShapeCandidates.ts`(薄い入口)を足す。
- `apps/server/src/analysis/shapeGraphRanking.ts` は**読むだけ・触らない**(指示)。`scripts/playtest/lib/` と
  `scripts/playtest/records/obs-3/p4-min3-r2/` は開発・診断レーンが FIG-1 で触るので**書かない**(import して読むのは可)。

## 2. 入口と出口

**入口**(1 局面ぶん):
| 欄 | 出どころ |
|---|---|
| `kifuId`・`displayPly`・`sfen` | `direct_answers.json` の `answers[]`(実在する局面だけを使う。指示) |
| `moves`(USI の全手) | 同じ組の `<work>/p2/kifu/<kifuId>.fixed.json` の `moves` |

`moveHistory = moves.slice(0, displayPly - 1)`(SFEN の手数欄が「次に指す手の番号」のため)。
**この切り出しが正しいことは道具に確かめさせる**: `analyzeShapeFormation(sfen, moveHistory)` は再生結果が
`sfen` と一致しなければ例外を投げる。**例外はそのまま出口に返す**(黙って別の局面を評価しない)。

**出口**(JSON。1 局面につき 1 件):
```
{ kifuId, displayPly, sfen,
  figure: boolean,                 // 候補が 0 件なら false(図を出さない)
  candidates: [ { shapeId, family, parentShapeId, status, matchScore, rank,
                  label: { level: "named" | "hedged", text: string },   // hedged は「〜のような形」
                  evidence: { evidenceCount, missingCount, requiredCount, movedRequiredCount },
                  exposureRule: "R1" | "R4" | "R5" | "R5p" | …,          // 内部用
                  pendingNote: string | null } ],
  notes: string[],                 // 下の「劣化の注」。必ず入れる
  internal: { exposureCounts: {...}, droppedByRule: {...} }              // ★顧客版に出さない
}
```
`internal` の欄には **`"customerVisible": false` の印**を付ける(`obs.vocab.exposure` の 0 / 657 / 4703 と同じ型の数
= 道具の振る舞いであって顧客の指し方ではない。P-99)。

## 3. 手順(決め打ちの個数を作らない)

1. `analyzeShapeFormation(sfen, moveHistory)` → `ShapeFormationResult[]`(`apps/server` の既存。判定は足さない)。
2. `rankReachableShapes(results, [])` → 到達できる形の順位。
   **`selectTargetPurpose` を呼ばない劣化版**(指示)。`[]` を渡すので全件が中立の段になり、並びは
   `matchScore` 降順 → `shapeId` 昇順だけで決まる。**注に必ず書く**:
   「**狙い(⑤)で絞っていません。目的で選んだ結果ではありません。**」
3. 各候補に `decideNameExposure(input, D'')` を当てる。`input` は既存の組み立て方をそのまま使う
   (`evidenceCount = formationEvidence.length`、`missingCount = missingSquares.length`、
   `requiredCount = matchedSquares.length + missingSquares.length`、
   `movedRequiredCount = movedRequiredCountOf(非 optional の required_pieces, perspectiveColor)`)。
   **D'' = `{ minEvidenceForHedged: 2, hedgeOneEvidenceIfMissingLe1: true, minEvidenceForCompleted: "movedRequired" }`**
   (`EXPOSURE_VALUE_SETS["D''"]` と同値。**既定の `NAME_EXPOSURE_VALUES` は動かさない** ― 道具が値を明示して渡す)。
4. **`hidden` になった候補は捨てる**(= 「根拠が弱ければ名前を出さない」)。`named` は名前、`hedged` は
   「〜のような形」。**新しい閾値を 1 つも作らない**: 残す/捨てるの線は `decideNameExposure` の判定そのもの。
   個数の上限・下限を置かない(「2〜3 個出す」と決めない ― 指示)。
5. 残りが 0 件なら `figure: false`(**0 個は正常な出口**)。

**v1 でやらないこと(注に明記)**: 「そこへ行く手順があるか」の**経路の判定はしない**。
名前は `data/` の認識(`review_status`)を経たものだけで、道具は名前を作らない(CLAUDE.md 規則 4)。

## 4. 変えないもの

`apps/server/src/analysis/` の中身(`shapeGraphRanking.ts`・`shapeFormationAnalyzer.ts`・`nameExposure.ts`)、
`NAME_EXPOSURE_VALUES` の既定、`data/`、納品の経路(`deliver.ts`・`pipeline.ts`・`report-pdf/`)。

## 5. 試験(`shapeCandidates.test.ts`。合成の局面で、実データを読まない)

1. 候補 0 件のとき `figure: false`・`candidates: []`(0 個が正常な出口)。
2. `hidden` の候補が落ちる(証拠 1 件・欠け 2 以上 → R5 で hidden)。
3. `hedged` が「〜のような形」になる(`draft` の reviewed 済みでない形 → R1)。
4. `named` は `reviewed` かつ completed/matched かつ証拠が `movedRequired` 以上のときだけ。
5. `movedRequiredCount` が 0 のレコードは `named` にならない(D'' の肝)。
6. 並びが `matchScore` 降順 → `shapeId` 昇順で決定的(同じ入力で 2 回呼んで同一)。
7. `notes` に「狙いで絞っていない」「経路を見ていない」の 2 つが必ず入る。
8. `moveHistory` の切り出しが合わないとき(`sfen` と再生結果が違う)は例外が伝わる。
9. `internal` に `customerVisible: false` の印が付く。

## 6. 実測(報告の本体。予測を先にファイルへ書いてから測る)

**材料は 4 人目の 167 局面(`direct_answers.json` の `answers[]`)。読むだけ。**
- (A) 167 局面すべてで道具が例外なく終わること。**`figure: true` の局面数・候補数の分布(0 個が何件か)**を数える。
  **予測を先に書く**: 私の予測は「`figure: true` は 167 のうち **20 件以下**、大半は 0 個」(理由: D'' は証拠 2 件以上を
  求め、`data/shapes/` は美濃囲い系 3 件しかない)。外れたらそのまま報告する。
- (B) `named` と `hedged` の内訳、落ちた規則の内訳(R0/R2/R3/R5/R6)。
- (C) 同じ入力で 2 回回して出力が 1 バイト一致(決定的)。
- (D) 回帰: `npx vitest run --root scripts/playtest --exclude '**/.claude/worktrees/**'`(P-88)、
  `node scripts/typecheck-scripts.mjs`、`apps/server` の試験は触っていないので回さない(触ったら回す)。
- (E) 変異 2 本(予測を先に): D'' を既定値に戻すと試験 5 が落ちる / `hidden` を捨てる行を消すと試験 2 が落ちる。

**測らないと分かっていること**(報告に書く): 出てきた候補が将棋として妥当かは道具では測れない(人の目)。
経路の有無は見ていないので「本当に到達できるか」は言えない。

## 7. 危ないところ(先に書く)

- **`figure: true` が 0 件になる見込み**がある。そのときは「道具が壊れている」のではなく**材料が足りない**
  (`data/shapes/` が 3 件)。0 件だったら**候補を増やすために閾値を下げることはしない** ― 人間・司令塔へ数を出して返す。
- 後手の局は `*.fixed.json` の `mirrored` で本人が先手になるよう正規化済み。**`mirrored: true` の局が材料に
  含まれるかを先に数え、含まれるなら 1 局面で往復を確かめる**(合わなければ v1 は先手の局だけに限り、注に書く)。
- `scripts/playtest/lib/recognitionMeasure.ts` から `movedRequiredCountOf` を import する(読むだけ)。
  FIG-1 が同じファイルを触っているので、**実装中に向こうが変えたら import 先を自前に写す**(写したら報告に書く)。

---

## 8. 司令塔の指摘による直し(2026-09-26。実装に入る前)

### 8.1 形の数 ― 自分で数え直した

| 置き場所 | 数 | `review_status` | `side` |
|---|---|---|---|
| `data/shapes/` | **3** | `human_reviewed` 2(`mino_honmino`・`mino_takamino`)/ **`draft` 1**(`mino_ginkanmuri`) | すべて self |
| `data/drafts/2026-09-25-knowledge/shapes/` | **79** | **全件 `draft`** | self 44 / opponent 35 |

合計 82(self 47・opponent 35)。司令塔の数(82・47・35)と一致。**ただし 2 点、司令塔の言い方を訂正する。**

1. **`analyzeShapeFormation` は下書きを読んでいない。** `getShapes()` の `DEFAULT_SHAPES_DIR` は `data/shapes/` だけで
   (`shapeRepository.ts:13`)、`data/drafts/…` を読む口はリポジトリ内に 1 つも無い(`git grep` 0 件)。
   **下書き 79 件を候補に入れるには、この道具が `options.shapes` に明示して渡すしかない。**そうする(規則 4 が許す範囲)。
   渡したことは注に書く(「下書き 79 件を含む 82 形から探した」)。
2. **「`data/shapes/` の 3 件だけが `named` になりうる」も不正確**: `mino_ginkanmuri` は `data/shapes/` にあるが `draft` なので、
   `named` になりうるのは **`human_reviewed` の 2 件だけ**。

### 8.2 「候補に残すか」と「名前をどう出すか」を分ける(司令塔の直し。採る)

- **候補に残すか = 到達できるか。** `rankReachableShapes`(side=opponent と completed を外し、順位をつける)だけで決める。
  **露出では捨てない。**序盤(まだ何も組めていない局面)で図が必ず空になるのを避けるため。
- **名前をどう出すか = 露出の規則(D'')。** `named` → 名前、`hedged` → 「〜のような形」、**それ以下は名前を出さず盤だけ**。
  候補からは捨てない。
- **`figure: false` は「到達できる候補が 0 件」のときだけ。** 名前が出せないことは図を出さない理由にしない。

**§3 の 4・5 は上書きされる。**出口の `candidates[].label` は `{ level: "named" | "hedged" | "none", text | null }` とし、
`level: "none"` は**盤だけ出す**(名前欄を空にする)。

### 8.3 残す/捨ての線は決められない ― そう報告する(司令塔「決められないなら、決められないと報告してください」)

`rankReachableShapes` が返すのは**順位であって切れ目ではない**。self の 47 形のうち completed を外した全部が「到達できる」側に残る。
既存の道具の中に、**新しい閾値を作らずに「ここから下は候補でない」と言える線は無い**(あるのは
`side`・`completed` の 2 つの除外と、`matchScore` の順位だけ)。`status === "forming"` を線にすることは**できるが採らない** ―
それは形成の証拠による切り方で、司令塔が 8.2 で外した理由(序盤で空になる)にそのまま当たる。

**したがって v1 は切らない**: 到達できる候補を**全件、順位つきで**返し、`matchScore` の分布を報告に出す。
**「何件まで見せるか」は見せ方 (b) の判断**(= 判断的知識。人間・司令塔が決める)。道具は数を出すところまでやる。

### 8.4 予測の書き直し(82 形を入口にしたときの見込み。実測の前に書く)

- **P1**: `figure: true` は **167 局面のうち 167 件**(0 件になる局面は無い)。理由: self 47 形のうち completed になるのは
  ごく一部で、残りはすべて「到達できる」側に入るため。
- **P2**: 1 局面あたりの候補数は **40〜47 件**(中央値 46 前後)。
- **P3**: **`named` は 0 件**(構造上)。`rankReachableShapes` は completed を外すので、候補は forming か none しか無く、
  露出の R4(named)は completed/matched にしか当たらない。**つまりこの図は、名前を断定することが原理的にできない。**
  これは規則 4 の趣旨に沿う(下書きを断定的に見せない)。**外れたら報告する。**
- **P4**: `hedged`(「〜のような形」)が 1 件以上ある局面は **167 のうち 60 件以下**。1 局面あたりの `hedged` は中央値 0〜1 件。
- **P5**: `mirrored: true` の局(材料 18 局のうち 11 局)でも、`moves` と `sfen` の往復は合う(合わなければ先手の局だけに限る)。

§6 の実測は上記 P1〜P5 を当てる形に読み替える。**予測が外れたら、外れたまま報告する**(閾値を足して合わせない)。
