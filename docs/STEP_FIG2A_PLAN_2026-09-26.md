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
