# STEP D2.5 計画: 物差しを増やす ― 玉の区域に届く駒と升・N 手の間の変化・形勢の状態と遷移(2026-09-15)

**状態**: 計画(下書き。司令塔 e3 の依頼)。**司令塔の決定(版 `8b5b00f2`): Q-1〜Q-6 は推奨どおり**(6.)。**事前読み B の REVISE(版 `8b5b00f2`、必須 R-1・R-2、推奨 S-1〜S-6)を司令塔 e3 の決定で取り込み、版 `b28c69cf` に B の再読み GO(任意なし)**(往復 1 回)。**その後、司令塔 e3 が Q-8 を決定して M-1・M-2 の欄名だけ書き換えた(6.)。計画は確定。実装 1e、監査 C。**実装者 1e の下見(D-1〜D-4・S-1〜S-5)も取り込んだ。**実装しない。定義の値と語はすべて draft で、人間の承認が要る(印 【承認】)。** **2026-09-15 に人間が承認: 玉の区域(玉 + 8 近傍のうち盤上の升)・玉自身の利きを数えない・形勢の境 +300/−300(詰みは符号、詰み 0 は undetermined)。残りの【承認】の点(持ち駒・届くか置かれたか・延べ数・M-4 の代替・遷移の順序)は推奨どおりに実装し、結果の表と一緒に人間に確認する。**
**書いた人**: A(sgogi-coach-64)。**エンジンは使っていない。**基点 HEAD `d3cbdc9`(上位構想 §15 は `67482d8`、15.5 の組の数の訂正は `567a0f0`)。根拠は `docs/DIAGNOSIS_CONCEPT_2026-09-14.md` §15.2・15.4・15.5・15.11 と §7.3 の 1.「今後追加」。
**前提**: D2 の道具(取った駒・王手・詰み・玉の周り・逃げ道)は評価語なしで動いている(`8ee0839`、20 局で照合 §12.7 `cbb985f`)。この STEP はその隣に数を足すだけで、D2 の欄の意味は変えない。

## 0. 実物から分かった前提

| # | 事実 | 場所 |
|---|---|---|
| E-1 | 利きの幾何は shogiops 0.21.0 の `attacks(piece, square, occupied)`。成駒(と・成香・成桂・成銀)は金の形、馬・竜は線 + 玉の形、香桂銀金歩は色で向きが変わる。**線の駒は `occupied` で止まり、止めた駒の升は色を問わず利きに含む**。`pos.squareAttackers`(Position のメソッド)は**玉の利きも含む**(`kingAttacks ∩ roles('king','dragon','horse')`)。ピン・取り返し・守りは見ない(`attackedPieces.ts` と同じ方針、STEP 4-3 の人間承認) | `apps/server/src/rules/squareAttack.ts:28-35`・`apps/server/src/rules/attackedPieces.ts:42-70`・`apps/server/src/analysis/pvMaterials.ts:29`・`:230-266`・shogiops `dist/variant/shogi.js:28-38`(B・A) |
| E-2 | 既にある玉の周りの数: `kingSurroundingsOf` = 先手玉の 8 近傍の升数(中央 8・端 5・隅 3)と、**そこに置かれた**先手の駒の数(利きではない)。`pvMaterials` の材料 5 = 8 近傍の自分の駒の数の差、材料 12 = 飛角香竜馬の**盤全体**の利き升数の差(盤の外の升は `BOARD_SQUARES` と交わらせて除く) | `scripts/playtest/lib/kingSurroundings.ts:12-49`・`apps/server/src/analysis/pvMaterials.ts` の `countKingNeighbors` :230-248・`countSlidingReach` :251-266 |
| E-3 | 逃げ道 = 手番を先手にした局面で先手玉を動かす合法手の数(draft、D2 Q-3) | `lib/counterfactual.ts:130-142` |
| E-4 | D2 の 1 本ぶんの事実 `SequenceFacts` は N 手目の後の局面から `kingSurroundingsEnd`・`kingEscapesEnd` を作る。差は `pvMinusActual`(読み筋 − 実戦、数の欄だけ)。counterfactual の根 = 直前の ready 行の sfen = `trigger` の局面 | `lib/counterfactual.ts:58-86`・`:149-192`・`lib/failureEvent.ts:390` |
| E-5 | **Failure Event は直前の状態を問わない**: `cpDrop` は `diffCp ≤ dropCp`(−400)だけ、`mateDrop` は `mateAfter < 0`、`matedIfPass` は直後の行だけで決まる。直前 `scoreCp ≥ +300`(`advantageCp`)を使うのは `candidateModes`(死因①)の付与だけ。**「互角 → 劣勢」の急落も Failure Event に入る**。diagnosis-moment の `rise` は `diffCp ≥ +400` か `mateAfter > 0`、`maxDrop` は局ごとに最も下がった組 | `lib/failureEvent.ts:363-374`・`:385-388`・`:408`・`lib/diagnosisMoment.ts:38-80`(B の R-1 で直した。版 `8b5b00f2` は :386 を読み違えていた) |
| E-6 | 評価の状態は `measured`(`scoreCp`・`mate`・`afterPassMate` など)ほか。`|scoreCp| ≥ 30000` は評価値でない(P-45)。記録は回して先手 = 本人、`scoreCp` は先手視点。スキーマは `mate` 0 を通さない | `lib/failureEvent.ts:57-111`・JSON v0 の T-3 |
| E-7 | 版の規則: 任意の欄を足す = MINOR / 列挙の値を足す = MAJOR / 閾値を変える = 版は上げず出どころに規則の値を書く。古い版のスキーマは消さない。**D-SCREEN 計画が Failure Event v0.5・diagnosis-moment v0.2 を予約**(`d3cbdc9` でコミット済み。v0.5 のスキーマは D-SCREEN-2 で入る)。D-SCREEN の「`screen` の無い記録はバイト一致」の基点は v0.4 の出力 | `docs/STEP_JSON-V0_PLAN_2026-09-15.md` §3.2・`docs/STEP_D-SCREEN_PLAN_2026-09-15.md` §3・§11 |
| E-8 | **全ての手の組(§15.5 の定義、`567a0f0`)= 本人の手 1 つ → 相手の手 1 つ = 連続する ready 行の組**。2 人目 20 局で 734 組(ready 行 754。連続する行の ply の差はすべて 2、最初の行を除く 734 行が本人の手と相手の手を 1 つずつ持つ) | 上位構想 15.5・A が `kifu2-*.jsonl` の ply と手の欄だけを数えた |

## 1. 足す物差しの定義(**すべて事実の数。欄にも文にも「良い・悪い」「速い・遅い」を入れない**)

**玉の区域(zone)**: 玉の升と、その 8 近傍のうち盤の中の升(中央 9・端 6・隅 4)。【人間承認 2026-09-15】。欄の名前は `zoneSquares`(**`kingSurroundings.squares` は玉の升を含まない 8・5・3 で、1 違う**)。玉が盤に無ければその側は null。
**「利きが届く升」**: 盤上の**玉以外の**駒 1 枚ずつに `attacks(piece, square, occupied)` を当てた升(**味方の駒・相手の駒のいる升も含む** ― E-1)。**M-1・M-2・M-3 とも玉自身の利きは数えない【承認】**(自玉の区域では玉の利きが常に 8 近傍に届き、升数 − 1 に張り付くため。司令塔 e3 の決定)。`pos.squareAttackers` は玉の利きを含むので使わない(R-2)。**持ち駒は数えない。**

| # | 欄(案) | 定義(局面 1 つから数える) | 【承認】で決める点 |
|---|---|---|---|
| M-1 区域に届く相手の駒 | `zonePieces.opponentKingZone.bySente`・`zonePieces.ownKingZone.byGote`(Q-8 の決定で中立の名前。形は M-3 と同じ) | 後手玉の区域の升に利きが 1 升以上届く先手の駒(玉を除く)の枚数 / 先手玉の区域に利きが届く後手の駒(玉を除く)の枚数 | 区域の形・持ち駒を入れるか |
| M-2 区域に届く味方の駒 | `zonePieces.ownKingZone.bySente`・`zonePieces.opponentKingZone.byGote`(同上) | 先手玉の区域に利きが届く先手の駒(玉を除く)の枚数 / 後手玉の区域に利きが届く後手の駒(玉を除く)の枚数。**`kingSurroundings.own`(区域に置かれた駒)とは別の量** | 「届く」か「置かれた」か |
| M-3 区域の升に届く利き | `zoneControl.ownKingZone: { bySente, byGote }`・`zoneControl.opponentKingZone: { bySente, byGote }` | 各玉の区域の升のうち、先手の(玉以外の)駒の利きが届く升の数・後手の(玉以外の)駒の利きが届く升の数(**升数**。1 升に何枚届いても 1) | 玉の利きを入れない(上の定義。司令塔 e3 の決定 → **人間承認 2026-09-15**)・升数か延べ数か |
| M-4 利きと攻撃駒数の N 手の変化(§15.4 の「攻めの速度」「相手の攻撃速度」に代わる事実の量) | **新しい欄を作らない** | 読む側が `counterfactual.actual.positionFactsEnd − trigger.positionFacts`(と読み筋の側)で作る(根が同じ ― E-4)。相手側は同じ量を逆の玉で読む。既にある欄: 王手の ply(`checks`)・パスすると詰まされる読み(`afterPassMate > 0`)・詰みまでの手数(エンジンが詰みを見つけたときの `mate` だけ) | 代わりの量として採るか |
| — | **測らないと明記** | 「王手までの最短手数」「詰めろまでの手数」は探索が要り、局面の純粋関数では測れない。エンジンの読みは急落の根の 1 本だけで、全ての手の組には無い | — |
| M-5 形勢の状態 | `standing: "ahead" \| "level" \| "behind" \| { undetermined: 理由 }` | 1 つの評価について: `mate > 0` → ahead、`mate < 0` → behind、**`mate === 0` → undetermined**、`scoreCp ≥ +300` → ahead、`scoreCp ≤ −300` → behind、ほかの cp → level。評価の状態が `notMeasuredGameEnd`・`notMeasuredInCheck`・`notMeasurable`・`unrecorded`・`notEvaluation` の 5 つ → undetermined(理由は状態の名前をそのまま。`measured` で `scoreCp` も `mate` も null の行は `evaluationOf` が `notMeasurable` にするので来ない ― `lib/failureEvent.ts:62-99`) | 境 +300(5.3・`advantageCp` の借用)と −300(新しい値)・境を含むか・mate の扱い |
| M-6 遷移 | `standingPair: { before, after }` | 組の直前の行と直後の行の M-5 を並べるだけ。**「越えた」「崩れた」の語は欄にしない**(順序 ahead > level > behind で下がったかは読む側が数える) | 状態の順序を決めてよいか |

**欄の語**: `ahead / level / behind` は M-5 の境の値の名前であって評価ではない。画面・レポートの文(優勢・互角・劣勢)は D6 で言い換えるときに、draft であることと一緒に出す(CLAUDE.md 6 番)。`attackers`・`defenders` は役割の語で評価語ではないが、「区域に届く先手の駒 / 後手の駒」のような中立の名前も選べる(Q-8)。

## 2. どこに足すか(**局面 → 事実の純粋関数。全ての手の組(E-8)にもそのまま当てられる形**)

- **新しい lib `scripts/playtest/lib/positionFacts.ts`**: `positionFactsOf(sfen, rules): PositionFacts`(M-1〜M-3 を 1 回で。玉以外の駒ごとに `attacks` を当て、区域と交わらせる。`apps/` は変えない)。`rules` は `PvMaterialRules` と同じく**既定値を置かず**呼び出し側が選ぶ(`zone: "king_and_eight_neighbors"`・`reach: "non_king_pieces"`・`control: "squares"`)。区域の升の数も返す(端・隅で分母が変わるため)。利きは手番に依らないので、後手番の局面にもそのまま当てる
- **`lib/standing.ts`**: `standingOf(evaluation, bounds)`(M-5)・`standingPairOf(before, after, bounds)`(M-6)。`bounds = { aheadCp: 300, behindCp: -300 }` は draft の定数を 1 か所に置く(`DRAFT_RULE_1` の隣)。`evaluationOf(record)` の結果にそのまま当てる
- **Failure Event**: `trigger.positionFacts`(直前の行の局面)・`branch.standingPair`。`counterfactual`(compared)の `actual`・`pv` に `positionFactsEnd`(`sequenceFacts` の `kingSurroundingsEnd` の隣に足す。N で切るのは `counterfactualOf` の既存の切り方 ― `lib/counterfactual.ts:189`・`:253-255`)、`pvMinusActual.positionFacts`(M-1〜M-3 の差。どちらかが null なら null)
- **diagnosis-moment**: `MomentPairFields` が `trigger`・`counterfactual` を共有するので同じ欄が入る。組の行に `standingPair`。maxDrop の `noDrop`・`noComparedPair` の行には足さない
- **全ての手の組(D4)**: この STEP では出力を作らない。D4 が ready 行ごとに `positionFactsOf` と `standingOf` を呼べば足りる形にしておく
- `kingSurroundings`・逃げ道・`pvMaterials` の既存の欄は変えない(重なる量は §1 に書いた差のとおり別の欄)

## 3. 契約と版

- **任意の欄を足すだけ = MINOR**(E-7。`standing` の値の列挙は**新しい欄**の列挙で、既存の列挙に値を足すのではない)。閾値(±300)と `rules` の値は出どころの規則の欄に書く
- **版の番号(Q-3、司令塔 e3 の決定)**: **先にスキーマ(`failure-event.v0.5.schema.json`)をコミットした方が v0.5・moment v0.2 を取り、後の方が v0.6・v0.3**。**後の方は、先の方のそのコミットを基点にバイト一致を確かめる**(D2.5 が先なら、D-SCREEN-2 の「`screen` の無い記録はバイト一致」の基点は v0.4 でなく D2.5 のコミットの出力になる)
- **旧版の JSON**: 新しい欄のキーが無い = その版では出していない(読む側は `unrecorded` と扱う)。**記録(JSONL)の側は測り直し不要**(局面と評価から計算するので、古い記録からも作れる)。旧版の出力と比べると、新しい欄以外は `schemaVersion`・`provenance.analysis` を除いてバイト一致、Markdown は D2.5 の列を足した分だけ変わる

## 4. 固定例と変異(規則 11.3・11.8。期待は手で導いた。実装のときに盤の図を計画の実装の節に残し、図で確かめ直す)

盤の升は USI(筋 1〜9・段 a〜i)。区域は E-1・§1 の定義。

| # | 固定例 | 期待 |
|---|---|---|
| P-1 | 平手の初期局面 | 区域の升数 6 と 6。M-1 両側 0。**M-2 先手 5**(金 4i・6i、銀 3i・7i、飛 2h)・後手 5。**M-3 `ownKingZone.bySente` 4**(4h・5h・6h・5i)・`byGote` 0、`opponentKingZone.byGote` 4・`bySente` 0 |
| P-2 | 先手玉 9i・後手玉 5e だけ | 区域の升数 4 と 9。M-1〜M-3 すべて 0(玉の利きは数えない) |
| P-3 | 先手玉 9i・後手玉 5a・先手飛 5e・後手金 5b だけ(先手番) | 飛は 5d・5c・5b で止まる(5b を含む)。M-1 `onOpponentKingZone` 1。M-3 `opponentKingZone.bySente` 1(5b)・`byGote` 3(金の利き 4b・6b・5a)。M-2 `opponentKingZone` 1。先手の区域は 0 |
| P-4 | P-3 の後手金を 5c に | 飛は 5d・5c で止まる。`opponentKingZone.bySente` 0・`byGote` 1(5b)・M-1 0・M-2 `opponentKingZone` 1 |
| P-5 | 先手玉が盤に無い | 先手玉の側は null、差も null |
| P-6 | P-3 に先手の持ち駒の金を足す | P-3 と同じ(持ち駒は数えない) |
| P-7 | 同じ 2 枚が後手玉の区域の同じ升に届く(先手玉 9i・後手玉 5a・先手と 4c・先手と 6c だけ) | M-1 2・`opponentKingZone.bySente` **3**(と 4c は 3b・4b・5b・3c・5c・4d、と 6c は 5b・6b・7b・5c・7c・6d に届き、区域に入るのは 4b・5b・6b。5b には 2 枚届くが 1 升)。**延べ数で数えると 4** |
| P-8 | 先手玉 9i・後手玉 5a・先手馬 6c だけ | `opponentKingZone.bySente` 3(6b = 玉の形、5b・4a = 線)。**線だけと取り違えると 2** |
| P-9 | 先手玉 9i・後手玉 5a・先手と金 4c だけ | `opponentKingZone.bySente` 2(4b・5b = 金の形)。**歩の形と取り違えると 1** |
| P-10 | `scoreCp` +300 / +299 / −299 / −300 / `mate` +3 / `mate` −1 / `mate` 0 / 状態 `notMeasuredGameEnd`・`notMeasuredInCheck`・`notMeasurable`・`unrecorded`・`notEvaluation` | ahead / level / level / behind / ahead / behind / undetermined / undetermined(理由 = 状態の名前)×5 |
| P-11 | Failure Event の組(直前 +700・直後 +200)/(直前 +100・直後 −350)と、counterfactual N = 2 の組 | `standingPair` ahead → level / level → behind・`positionFactsEnd` は 2 手目の後の局面 |
| P-12 | 旧版と同じ入力(GAME01・d0-nnue) | 新しい欄以外は 3. の一致 |

変異(中心): **W-1a** 区域に玉の升を入れない(P-1・P-2 の升数)/ **W-1b** 区域を 5×5 にする(P-2・P-3)/ **W-2** M-3 を延べ数で数える(P-7)/ **W-3** 遮りを見ない・止めた駒の升を含めない(P-3・P-4)/ **W-4** 玉の利きを入れる(`pos.squareAttackers` で数える。P-1 の `ownKingZone.bySente` が 6、P-2 の M-3 が 0 でなくなる。M-1・M-2 は玉を駒の枚数に足す形でも当てる)/ **W-5** M-2 を区域に置かれた駒で数える(P-1 の M-2 が 2)/ **W-6** 先手と後手を入れ替える(P-3)/ **W-7** 馬・竜の玉の形を落とす(P-8)/ **W-8** 成駒を元の駒の形で数える(P-9)/ **W-9** 境の `≥` を `>` に(P-10 の +300)/ **W-10** mate の符号を逆に(P-10)/ **W-11** undetermined を level に畳む(P-10)/ **W-12** `positionFactsEnd` を N 手で切らず読み筋の最後で取る(`counterfactualOf` 側の変異。P-11)。周辺: W-13 持ち駒を数える(P-6)・W-14 null を 0 に(P-5)・W-15 旧版にも欄を書く(P-12)。**予測は実装の後、当てる前に試験の単位で書く。**

## 5. 予測(**測る前に書く。書いた人 A。見たもの: §12.7 の表と、D2 照合の監査で読んだ 2 人目 20 局の events の `counterfactual` の欄・kifuId・分岐点・N。`trigger`・`branch` の評価の値・盤・moment の jsonl の中身は見ていない。g3 は見ていない**)

**書き直しの記録**: 版 `8b5b00f2` の予測(予-1「39 件のうち ahead → level か behind が 12〜24、残りは ahead → ahead」・予-2「直後 behind 3〜10」・予-3「moment の level → behind が局の 20〜50%」)は、E-5 の読み違い(Failure Event は直前 ahead だけ)を前提にしていた。**B の R-1 を受け、測る前の 2026-09-15T13:45:24Z に次の表へ書き直した**(元の値はこの段落に残す)。

**入力**: Failure Event = C の scratchpad の `p2-20-all-events.jsonl`(sha256 `7e63d3fc…`、39 件、うち compared 37)。maxDrop = 同じ場所の `p2-20-all-maxdrop.jsonl`(sha256 `fce9b847…`、中身は見ていない)。境は M-5 の draft の値。

| # | 予測 | 外れたと言える条件 |
|---|---|---|
| 予-1 | 39 件のうち直前が ahead は **18〜32 件** | 17 件以下か 33 件以上 |
| 予-2 | 39 件のうち状態が下がった件(ahead → level・ahead → behind・level → behind)は **14〜28 件** | 13 件以下か 29 件以上 |
| 予-3 | 39 件のうち直後が behind は **6〜18 件** | 5 件以下か 19 件以上 |
| 予-4 | 20 局の maxDrop の組の行(`noDrop`・`noComparedPair` を除く)のうち、level → behind は **2〜8 局**(rise は定義上 level → behind になれないので数えない ― E-5) | 1 局以下か 9 局以上 |

**物差しごとに差が出た件数の予測**(§12.7 と同じ形。分母 compared 37。N = 2 が 16 件あるので差は出にくい側に置く。M-3 は玉の利きを除く定義で。版 `8b5b00f2` から値は変えていない)

| 物差し | 予測 | 外れ |
|---|---|---|
| M-1 後手玉の区域に届く先手の駒の枚数が違う | 14〜26 | 範囲外 |
| M-1 先手玉の区域に届く後手の駒の枚数が違う | 12〜24 | 範囲外 |
| M-2 先手玉の区域に届く先手の駒の枚数が違う | 10〜22 | 範囲外 |
| M-3 先手玉の区域で後手の利きが届く升の数が違う | 10〜22 | 範囲外 |
| M-3 後手玉の区域で先手の利きが届く升の数が違う | 12〜24 | 範囲外 |
| M-1〜M-3 のどれにも差が無い | 3〜10 | 範囲外 |

## 6. 決定が要る点

**決定(司令塔 e3、版 `8b5b00f2`): Q-1〜Q-6 は推奨どおり**(区域 = 玉 + 8 近傍、升数と枚数は別の欄、版は先に入れた方が v0.5・moment v0.2、速さは新しい欄を作らない、境 ±300 は人間の承認待ちの仮置き、Event と moment の両方)。**B の事前読みの後の決定(司令塔 e3): Q-3 は「先にスキーマをコミットした方。後の方はそのコミットを基点にバイト一致を確かめる」、Q-7 は玉の利きを M-1〜M-3 とも数えない(【承認】)。Q-8 は B の再読み GO(版 `b28c69cf`)の後に司令塔 e3 が決定: **中立の名前** `zonePieces.{ownKingZone,opponentKingZone}.{bySente,byGote}`(枚数。M-3 の `zoneControl` と同じ形)。理由: 「攻め駒・守り駒」は役割の解釈で、区域に利きが届く駒がその役割を持つとは限らない(§15.4 の 1. は解釈を持たない)。同じ形にすると読む側の分岐が 1 つで済む。M-1・M-2 の欄名だけ書き換え、定義は変えていない。**

| # | 点 | 推奨 | ほかの案 |
|---|---|---|---|
| Q-1 | 区域の形 | 玉の升 + 8 近傍 | 8 近傍だけ / 5×5 |
| Q-2 | 利きの数え方 | 升数(M-3)と、届く駒の枚数(M-1・M-2)を別の欄 | 延べ数 1 つ / 盤全体の利き升数(選ぶなら盤の外の升を除く ― E-2) |
| Q-3 | 版の番号 | 先にスキーマのファイルをコミットした方が v0.5・moment v0.2。後の方がバイト一致の基点を名前で書く | D2.5 を v0.6 に固定 |
| Q-4 | 速さ | 新しい欄を作らず、M-1・M-3 の N 手の変化と既存の欄で代える | 「王手までの最短手数」を探索で測る(エンジンが要る・全ての手の組に当てられない) |
| Q-5 | 形勢の境 | +300 / −300(**人間承認 2026-09-15**)、境を含む、mate は符号で、`mate` 0 は undetermined | ±200 / ±500、mate を undetermined |
| Q-6 | 足す場所 | Failure Event と moment の両方(同じ関数) | moment だけ / D4 の出力だけ |
| Q-7 | 玉の利きを入れるか | **M-1〜M-3 とも入れない**(決定。入れると自分の区域が張り付く ― R-2) | 入れる(`pos.squareAttackers` のまま) |
| Q-8 | 欄の名前 | `attackers`・`defenders`(役割の語) | 「区域に届く先手の駒 / 後手の駒」の中立の名前 |

## 7. やらないこと・限界

- 条件式(D3-COND)・Gate と全ての手の組の出力(D4)・LLM の言い換え(D6)・`apps/` の変更・エンジンを回すこと。既存の欄(D2・`kingSurroundings`・`pvMaterials`)の意味を変えること。g3 を開くこと(D3 の定義承認まで)
- **限界**: 利きは幾何だけ(ピン・取り返しを見ない ― E-1)。持ち駒は数えない。攻めの速さは代わりの量で、手数では測らない。形勢の状態は記録の `engineReference` の 1 つの探索の値で、別の探索とは食い違いうる(P-33)。counterfactual の N = 2 の件は 2 手分の比べ(PV-INFO が入れば変わる)

**既知事項の候補(登録と番号は司令塔)**
- **K-3** D-SCREEN が入ると、`standing` の元の評価が軽い / 深いで変わりうる(`evaluationSource`)。**読み筋の側も深い探索から取るので(D-SCREEN §11 の `pvSource`)、`pv.positionFactsEnd`・`pvMinusActual.positionFacts` も出どころで変わる**。同じ出どころの値で取る規則を、後に入れる方の計画で書く(1e の D-4)
- (版 `8b5b00f2` の K-1 は上位構想の訂正 `567a0f0` で閉じたので消し、E-8 の定義に置き換えた。K-2 は E-5 の読み違いから出たもので、消した)

**事前読み B(版 `8b5b00f2` の REVISE)の取り込み**: R-1 → E-5・5. の書き直しの記録と予-1〜予-4・入力・K-2 を消す / R-2 → E-1・§1 の「利きが届く升」・M-3 の【承認】・Q-7・P-2・P-3・P-4(升の名前)・W-3・W-4 / S-1 → 題・M-4 の見出し・Q-8 / S-2 → M-5 の `mate` 0・P-10・M-4 の作り方・§2 の後手番 / S-3 → 3. の版・Q-3 / S-4 → P-1 の M-2・M-3、P-8・P-9、W-1a・W-1b・W-5・W-7・W-8 / S-5 → 5. の書き直しの記録 / S-6 → E-8・Q-2

**実装者 1e の下見(版 `8b5b00f2`)の取り込み**: D-1 → E-5(B の R-1 と同じ)/ D-2 → §1 の定義・Q-7(B の R-2 と同じ)/ D-3 → E-8 / D-4 → K-3 / S-1 → §1 の「利きが届く升」/ S-2 → E-1・E-2 の場所 / S-3 → §1 の `zoneSquares` / S-4 → M-5・P-10 / S-5 → §2 の Failure Event・W-12
