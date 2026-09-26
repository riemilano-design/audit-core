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

### 8.5 司令塔の確認と追加(2026-09-26)

司令塔が実物で確かめ、**§8.1 の訂正 2 点はどちらも正しい**と認めた(`shapeRepository.ts` の冒頭コメントも
「`data/shapes/*.json`(将棋知識としての唯一のソース)」)。**意味の確認**: 下書きを候補に入れるのは自動ではなく
**この道具が明示して渡す行為**なので、注に書くのは必須(規則 4 の範囲内だが、こちらが選んでやること)。

**P3 は予測ではなく道具の性質**(司令塔の指摘): `rankReachableShapes` が `completed`/`matched` を候補から外すため、
露出の R4(named)には**構造上当たりようがない**。つまり**この図は形の名前を断定できない作りになっている**。
「断定しないよう気をつけている」ではなく「**断定できない作り**」として記録し、**試験と変異で示す**
(試験: どんな入力でも `label.level` に `"named"` が現れない。変異: 候補から completed を外す扱いを無効にすると
その試験が落ちる)。実装の指示に追加した。

**切れ目を決めなかった判断は正しい**(司令塔)。`matchScore` の分布を出し、**「何件見せるか」は (b) で司令塔が決める**
(分布を見る前に数を決めると「2〜3 個と決め打ちしない」に戻るため)。

**P1 が 167/167 だった場合の報告のしかた**(司令塔): 全件で図が出るなら、**「図を出すかどうか」の出口が一度も
使われていない**ということでもある(人間の指定「十分な候補がなければ図自体を出さない」)。悪いという話ではないが、
**「この材料では `figure: false` の出口が使われなかった」と明記する** ― 使われていない出口は次の顧客で初めて動く。

### 8.6 段取り 1 で止まった件の決定 ― (B) を採る(納品レーン長、2026-09-26)

**実装担当が段取り 1(P5 の往復)で止めて返した**(指示どおり。推測で埋めなかった)。実測: 計画 §2 の式
`moveHistory = moves.slice(0, displayPly - 1)`(平手から再生)は **55 / 167 局面でしか合わない**。残り 112 局面
(= `mirrored: true` の 11 局ぶん)は `IllegalMoveError`。`displayPly` 自体は 167/167 で `sfen` の手数欄と一致しており、
**誤っていたのは計画 §2 の式だけ**(私の書き落とし ― 回した局は平手から始まらない)。

**私も実物で確かめた**: `g03.fixed.json` は `mirrored: true`・`plyOffset: 1`・`startSfen`(後手番の平手に 1 手目を当てた
先手番の局面)を持ち、`lib/sideAlignment.ts:125` の `initialSfenOf` と `lib/finalPosition.ts:38` が**既に同じ読み方**
(`mirrored` なら `startSfen`、そうでなければ平手)を採っている。**新しい設計ではなく既存の前例に合わせるだけ。**

**決定: (B)** ― `ShapeCandidateInput` に開始局面の欄(既定は平手)を 1 つ足し、進める手数を
**`displayPly -(開始局面の SFEN の手数欄)`** にする。`analyzeShapeFormation` の `options.initialSfen` に渡す。
理由: 計画 §2 の安全策(再生結果と `sfen` が合わなければ例外)を保ったまま、材料を 100%(18 局・167 局面)使える
唯一の形だから。(A)(7 局・55 局面に限る)は材料を 3 分の 1 に落とすだけで、図が「先手の局にしか出ない」という
説明のつかない偏りを生む。(C)(CLI で切り出す)は計画 §2 の「切り出しを道具に確かめさせる」から外れる。

**新しい閾値・新しい判定は 1 つも足さない**(読むのは棋譜に既にある欄と SFEN の手数欄だけ)。
**校正**: この式で **167 / 167 が一致**することを実装の最初に測り、報告に書く(合わなければまた止める)。

**測っていないこととして報告に残すこと**: 回した局で畳まれている 1 手は `sideAlignment.ts` の作りから相手の手なので
自玉側の証拠(`formationEvidence`)は落ちない ― これは**コードの作りから言える範囲**で、局ごとには測っていない。

## 9. 実装のコミット `ab6ac85` と独立監査 GO(2026-09-26)

**独立監査 GO**(opus、判定書 scratchpad `FIG2A_AUDIT.md` 208 行。**省いた項目なし**)。監査が自分で回した根拠:
- **範囲**: 追跡ファイルは無変更、`apps/server/**`・`lib/**`・`data/`・`docs/`・納品の経路は不動、`NAME_EXPOSURE_VALUES` の既定も不動。**新しい道具はどこからも呼ばれていない**(参照は自分の 3 本だけ)。
- **新しい閾値が無い**: 数値リテラルを全部洗い、値と言えるのは `FIG2A_EXPOSURE_VALUES` の 5 欄だけ。`recognitionMeasure.ts:131-136` の D'' と**5 欄すべて同値**であることを突き合わせ。候補は 1 件も捨てていない(毎局面 47 の定数)。
- **`named` が返らないことは型でも閉じている**: `ShapeStatus` に `"matched"` が無く、`rankReachableShapes` が `completed` を除外し、R4 は `isComplete` だけ。**変異 2 本を自分で当てて戻した**(駒数の検査を外す → 14 の 1 本だけ / `completed` を混ぜる → 5 本。どちらも予測どおり、戻した後 `shasum` 一致)。
- **校正 167/167 を実装を import せず `shogiops` だけで再現**(回した局 112/112)。1 手ずらすと不一致 = 空振りでない。**盤が左右逆のまま出る間違いは出ていない。**
- **駒数の検査**: 期待値は平手から数えて引いている。`parsePosition` は歩 16 枚・19 枚を通すが `findShapeCandidates` は両方で例外 = 空振りでない。**`g05` 17 手目(先手に角 2 枚)は通る**(27 手目の `+B`+`B` も)。
- **出力の突き合わせ**: 監査が CLI を自分で回し、実装担当の `run1.json` と **`cmp` で 1 バイト一致**。数え直した値はすべて報告と一致。`hedged` 240 件すべて末尾が「のような形」・すべて `pendingNote` 付き。
- 回帰 1,754 通過、typecheck の rc=1 は `out/` の他席の下書き 10 件だけ(`tsc --listFiles` に新しい 3 本が出ることまで確認)。

**コミット `ab6ac85`**(パス指定で `scripts/playtest/fig/` と `scripts/playtest/figShapeCandidates.ts` の 2 つだけ。924 行追加)。**同じツリーで FIG-1 の差分が 6 本増えていたが触っていない。**

**監査が記録に残せと言ったこと**:
1. **`hedged` の `label` には下書きの名前が出る**(240 件すべて `draft`・`pendingNote` 付き。例「無敵囲いのような形」)。顧客経路はまだ 1 本も無いが、**(b) がこの `label` を冊子に出すなら、D'' の採用と下書き名の `hedged` 表示について人間/司令塔の承認が要る**(`nameExposure.ts` 自身が「この値は案であり統括の承認を経ていない/本体へつなぐのは EXPO-2」と書いている)。**司令塔は「図に名前を出さない(マスと駒だけ)」と決めているので、その形なら承認は不要。**
2. **既知事項の候補 2 件**(どちらも「ユーザーに見えるか = はい」): `figure: false` の出口が 1 度も通っていない(未検証の経路が 1 本残る)/ `hedged` は 1 局面で最大 8 件(紙面に直接効く)。
3. **駒落ちの棋譜が材料に入ると駒数の検査は必ず例外**になる(平手 18 局では 167/167 通過)。止まるのは正しい振る舞いだが覚えておく。
