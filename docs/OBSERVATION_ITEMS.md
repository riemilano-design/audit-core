# 観測項目の一覧(obs ID の正本)

**書く席**: 開発・診断レーン長(1 ファイル 1 席)。
**位置づけ**: [DESIGN_OBSERVATION_LAYER_2026-09.md](DESIGN_OBSERVATION_LAYER_2026-09.md) §14 の段取り 1。設計案 §1・§2 で案として振った `obs.<列>.<名前>` を、**既存の出力の欄名と 1 対 1 で突き合わせて登録する**。この一覧が仮説の契約 §7 の検査 **H-2**(「`observations[].obsId` は登録済みの ID である。未登録は落ちる」)の**登録簿**になる。
**この文書がしないこと**: 新しい計算・新しい欄・新しい閾値を作らない。コードを変えない。ここに載る ID は、既存の出力にある値に**名前を付けただけ**(状態 `existing`)か、設計案 §2 の項目で**まだ値が無い**もの(状態 `copy` / `new` / `vocab`)。後者は「無い」と書くために載せる(H-2 では `existing` 以外の ID を引いた仮説は落ちる)。

**欄名の確かめ方**: すべて `scripts/playtest/lib/*.ts`(または `apps/server/src/analysis/`)の型定義の実物から写した(2026-09-25、`41f200e` 時点)。JSON のパスは出力ファイルの根からの `a.b[].c` の形。`file:line` は型定義の場所。

---

## 0. 規則

| 規則 | 中身 |
|---|---|
| ID の形 | `obs.<列>.<名前>`。列は `eval fe moment cf cond time timeSearch fork side read direct menu recog report geo vocab`。名前は出力の欄名をそのまま(camelCase)使う。**欄名を言い換えない**(H-2 の照合を機械で行うため) |
| 状態 | `existing` = 既存の出力にある/`copy` = 既存の欄の写し(名前を付け直すだけで作れる。未実装)/`new` = 新しい計算が要る(未実装。**測ってから**)/`vocab` = 語彙の列(値域は知識レーンが供給する `data/` の `id`、§3 供給の規則 5) |
| 契約 | JSON スキーマの有無。`無` = TS 型だけが正本(設計案 §12 #9。`provenance.gitHead` で版を残す) |
| 「無い」の書き方 | 値が無いときに 0・false・空で埋めない欄は、状態の値(`state`)を持つ。ここでは `null` と `state` を欄の説明に明記する |
| 変更 | ID を足す・消す・欄名を変えるのは開発・診断レーン長。既存の出力の欄名が変わったら(コードの変更)、同じコミットでこの一覧を直す |

---

## 1. `existing` ― 既存の出力にある値

### 1.1 `obs.eval.*`(評価。出どころ `patient_report_data.json`・Failure Event)

| obs ID | 出力ファイル/パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.eval.score` | `patient_report_data.json` `games[].scores[]`(同じ添字の `games[].plies[]` が手数) | `PatientGame` `lib/reportData.ts:130` | 各手の評価(本人視点、cp)。`null` = 測っていない | 無 |
| `obs.eval.standing` | Failure Event `branch.standingPair.{before,after}`、diagnosis-moment `standingPair` | `STANDING_BOUNDS {aheadCp: 300, behindCp: −300}` `lib/failureEvent.ts:62`、`Standing` `lib/standing.ts:27` | `ahead/level/behind` または `{undetermined}`(人間承認 2026-09-15) | 有(v0.7 / moment v0.4) |
| `obs.eval.game` | `patient_report_data.json` `games[].{no,id,side,total,result,ending,events,marks}` | `PatientGame` `lib/reportData.ts:130` | 局の事実: 手数・勝ち負け・終局の語(`ending` は `null` あり)・Failure Event の数 | 無 |

### 1.2 `obs.fe.*`(Failure Event v0.7。出どころ `*.jsonl`、契約 `schemas/failure-event.v0.7.schema.json`)

| obs ID | 出力ファイル/パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.fe.event` | 行の必須 12 欄 `schemaVersion kifuId branchPly fromReadyPly toReadyPly trigger action branch consequences counterfactual candidateModes provenance` | `FailureEventLine` `lib/failureEventSchema.ts:100`、`FailureEvent` `lib/failureEvent.ts:328` | 急落 1 件 | **有** |
| `obs.fe.evaluationState` | `trigger.evaluationBefore.state` | `Evaluation` `lib/failureEvent.ts:73` | 6 状態 `measured/notMeasuredGameEnd/notMeasuredInCheck/notMeasurable/unrecorded/notEvaluation`。`measured` のとき `scoreCp mate bestmove afterPassScoreCp afterPassMate dropCp` | 有 |
| `obs.fe.kingSurroundings` | `trigger.kingSurroundings.{squares,own}`(`null` = 先手玉が盤上に無い) | `KingSurroundings` `lib/kingSurroundings.ts:12` | 玉の 8 近傍の升の数と、そこにある味方の駒の数 | 有 |
| `obs.fe.positionFacts` | `trigger.positionFacts.{zoneSquares,zonePieces,zoneControl}.{ownKingZone,opponentKingZone}`(`ZoneCounts {bySente, byGote}`、玉が無い側は `null`) | `PositionFacts` `lib/positionFacts.ts:45` | 両玉の区域(玉 + 8 近傍)に利きが届く駒の枚数(M-1・M-2)と升の数(M-3) | 有 |
| `obs.fe.shape` | `trigger.shape` = `{state:"recorded", status, refersToShapeId}` または `{state:"unrecorded"}` | `ShapeState` `lib/failureEvent.ts:272` | 急落の手前の形の認識(`data/shapes` の id × 状態)。**語彙の列の既存の唯一の実例** | 有 |
| `obs.fe.opponentIntent` | `trigger.opponentIntent.{classification, refersToIntentId}` | `Trigger` `lib/failureEvent.ts:277` | 相手の狙いの認識(`data/intents` の id) | 有 |
| `obs.fe.branch` | `branch.{kinds, diffCp, mateAfter, matedIfPassAfter, evaluationAfter, standingPair, evaluationSource?}` | `FailureEvent` `lib/failureEvent.ts:328`、`BranchKind` `:323` | 急落の種類 `cpDrop/mateDrop/matedIfPass`、差、詰み | 有 |
| `obs.fe.action` | `action.{playedMove, bestmoveAtBefore}` | `lib/failureEvent.ts:328` | 実戦の手と、その手前の局面の最善手(USI) | 有 |

### 1.3 `obs.moment.*`(diagnosis-moment v0.4。契約 `schemas/diagnosis-moment.v0.4.schema.json`)

| obs ID | 出力ファイル/パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.moment.rise` | `rises[]`(`eventClass:"rise"`、`change` = `{kind:"cp", diffCp}` または `{kind:"mateAfter", mateAfter}`) | `RiseMoment` `lib/diagnosisMoment.ts:85` | 上がり(`−dropCp` 以上)の組 | **有** |
| `obs.moment.maxDrop` | `maxDrop`(`eventClass:"maxDrop"` + `change` + `excludedPairs {mateDrop, mateRise, notCompared}`、または `state:"noDrop"` + `minDiffCp`、または `state:"noComparedPair"`) | `MaxDropMoment` `lib/diagnosisMoment.ts:87` | 局ごとの最大の下がり。**出せない局も状態行** | 有 |
| `obs.moment.pair` | `MomentPairFields` = `branchPly fromReadyPly toReadyPly trigger moves{userMove,opponentMove} userBestmoveAtBefore opponentBestmove evaluationAfter standingPair failureEventBranchPly consequences counterfactual` | `lib/diagnosisMoment.ts:48` | 組(本人の手 + 相手の手)の共通の欄 | 有 |

### 1.4 `obs.cf.*`(反事実。Failure Event / moment の `counterfactual` 欄。**契約は v0.7 スキーマの `properties` が空 = TS 型が正本**)

| obs ID | 出力ファイル/パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.cf.state` | `counterfactual.state`(比べられたとき以外は `actualRootMismatch/unrecorded/notMeasurable/noFocusBaseline/emptyPv/rootMismatch/pvUnplayable`) | `CounterfactualUnavailableState` `lib/counterfactual.ts:128`、`Counterfactual` `:144` | 比べられたか/なぜ比べられないか | 穴(空) |
| `obs.cf.window` | `counterfactual.{comparedPlies, windowPlies, actualPlies, pvLength, pvUsablePlies, pvTruncatedAtPly, pvBounded{lowerbound,upperbound}, pvFirstMove, pvFirstMoveIsBestmoveAtBefore, pvFirstMoveIsPlayedMove}` | `CounterfactualComparison` `lib/counterfactual.ts:100` | 比べた手数と読み筋の性質 | 穴 |
| `obs.cf.kingEscapesRoot` | `counterfactual.kingEscapesRoot` = `{state:"counted", count}` / `{state:"noKing"}` / `{state:"opponentInCheck"}` | `KingEscapes` `lib/counterfactual.ts:64` | 分かれ目の局面の自玉の逃げ道の数(C-1 の材料) | 穴 |
| `obs.cf.kingEscapesEnd` | `counterfactual.{actual,pv}.kingEscapesEnd`(同じ 3 状態) | `SequenceFacts` `lib/counterfactual.ts:71` | 実戦の続き/読み筋の続きの終点の逃げ道 | 穴 |
| `obs.cf.sequenceFacts` | `counterfactual.{actual,pv}.{capturedRoles{us,opponent}, checks{byUs,byOpponent}, mate{ply,winner}|null, gameEnd{ply,result}|null, kingSurroundingsEnd, positionFactsEnd}` | `SequenceFacts` `lib/counterfactual.ts:71` | 続きの中で取った駒・王手・詰み・終局・終点の玉まわり | 穴 |
| `obs.cf.userMoveFacts` | `counterfactual.actual.userMoveFacts.{role, drop, capturedRole, promotion, kingMove, fromInOwnKingZone, toInOwnKingZone, toInOpponentKingZone, ownKingZoneReachBeforeMinusAfter}`(U-1〜U-9。`null` の意味は各欄の注釈) | `UserMoveFacts` `lib/moveFacts.ts:28` | 本人の手 1 つの幾何の事実(**設計案 §2 の `obs.geo.moveFacts` の実体**) | 穴 |
| `obs.cf.pvMinusActual` | `counterfactual.pvMinusActual.{capturedRoles, kingSurroundingsOwn, positionFacts, kingEscapes}`、`kingEscapesChangeFromRoot.{actual,pv}` | `CounterfactualDiff` `lib/counterfactual.ts:90` | 読み筋の続き − 実戦の続き | 穴 |

### 1.5 `obs.cond.*`(条件式と門。契約 `schemas/diagnosis-condition.v0.1.schema.json`・`diagnosis-gate.v0.1.schema.json`)

| obs ID | 出力ファイル/パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.cond.king_escapes_decrease_v1` | 条件式 C-1(`uses: counterfactual.kingEscapesRoot.count, counterfactual.actual.kingEscapesEnd.count`、`appliesTo: failureEvent rise maxDropPair pair`) | `lib/conditions/king_escapes_decrease_v1.ts:12`、`ConditionDefinition` `lib/condition.ts:53` | 真/偽/**判定不能**(分母に入れない) | 有 |
| `obs.cond.ahead_move_into_own_king_zone_v1` | 条件式(`uses: standingPair.before, counterfactual.actual.userMoveFacts.toInOwnKingZone`、`appliesTo: rise maxDropPair pair`) | `lib/conditions/ahead_move_into_own_king_zone_v1.ts:12` | 同上 | 有 |
| `obs.cond.readableFields` | 条件式が読んでよいパスの表(`trigger.* action.* branch.* moves.* standingPair.* change.* consequences.* counterfactual.*`) | `READABLE_FIELDS` `lib/condition.ts:154` | 「表に無いパスは読まない」の表そのもの(H-2 の先例) | 有 |
| `obs.cond.gate` | 門の値 `GATE_VALUES {minTruePairs:10, minGames:3, minRateRatio:2, minRateDiffPoints:10, maxPvToActualRatio:0.5, minTestTruePairs:3}` と G-1〜G-4 の判定 | `lib/gate.ts:313` | 条件式を採用してよいかの門(判断的知識、仮置きを含む) | 有 |

### 1.6 `obs.time.*`(時間。出どころ `time_cause.json`(`kind:"time_cause"`)と `patient_report_data.json` の `time`)

`time_cause.json` の `games[]`(局ごと):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.time.phaseSpentSec` | `games[].phaseSpentSec.{early,mid,late}` | `GameTimeCause` `lib/timeCause.ts:102`、`TimeCausePhaseTriple` `:65` | 段ごとの消費(秒) | 無 |
| `obs.time.longThinkCountByPhase` | `games[].longThinkCountByPhase.{early,mid,late}` | 同上 | 段ごとの長考(10 秒以上)の回数 | 無 |
| `obs.time.longThinkTotal` | `games[].longThinkTotal` | 同上 | 局の長考の回数(**設計案 §10.3 の分母**) | 無 |
| `obs.time.longestMove` | `games[].longestMove` = `{sec, kifPly}` または `null` | 同上 | 最長の 1 手 | 無 |
| `obs.time.longThinkStreakCount` | `games[].longThinkStreakCount` | 同上 | 長考の連続の回数 | 無 |
| `obs.time.midThinkByPhase` | `games[].midThinkByPhase.{early,mid,late}.{count,sec}`、`games[].midThinkTotal.{count,sec}` | `TimeCauseMidThinkByPhase` `:76`、`TimeCauseMidThinkCell` `:71` | 中くらいの考慮(4 秒超 10 秒未満)の段ごとの回数と秒 | 無 |
| `obs.time.forkAmongLongThink` | `games[].forkAmongLongThink` = `{numerator, denominator}` または `null` | `TimeCauseFraction` `:82` | 長考した手のうち分かれ道だった割合(C7) | 無 |
| `obs.time.oppositeSideAmongForkLongThink` | `games[].oppositeSideAmongForkLongThink`(同じ形) | 同上 | 分かれ道での長考のうち第 1 候補と側が逆だった割合(C8) | 無 |
| `obs.time.rookMark` | `games[].rookMark` = `{own, opponent}` または `null` | `TimeCauseRookMark` `:87` | 飛車を動かしたか(C9。**設計案 §2 の `obs.geo.rookFile` の元**) | 無 |
| `obs.time.remainingSec` | `games[].remainingSec`、`games[].timeUpLoss`、`games[].timeLimitSec` | `GameTimeCause` `:102` | 残り時間(C10)、時間で負けた局か、持ち時間 | 無 |
| `obs.time.midMoveSeconds` | `games[].midMoveSeconds[].{kifPly, sec, fork}` | `TimeCauseMidMoveSecond` `:94` | 中盤の 1 手ごとの秒と分かれ道か | 無 |

`time_cause.json` の `groups[]`(組ごと):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.time.groupMedians` | `groups[].{timeUpLoss,other}.{games, medianEarlySec, medianMidSec, medianLateSec, medianLongThinkTotal, medianLongestMoveSec, medianStreakCount, medianMidThinkCount, medianMidThinkSec, forkFraction, oppositeSideFraction}` | `GroupTimeCause` `lib/timeCause.ts:384`、`TimeCauseSubgroupSummary` `:305` | 時間負けの局/それ以外の局の中央値(**設計案 §10.3 の「序 27・中 63.5・終 44.5」の実体は `medianEarlySec/medianMidSec/medianLateSec`**) | 無 |
| `obs.time.rookMarkBreakdown` | `groups[].rookMarkBreakdown[].{own, opponent, games, medianEarlySec, medianMidSec}` | `TimeCauseRookBreakdownCell` `:349` | 飛車の印ごとの内訳 | 無 |
| `obs.time.c10Table` | `groups[].c10Table[].{gameNo, earlySec, midSec, remainingSec}` | `TimeCauseC10Row` `:377` | 局ごとの序・中の消費と残り | 無 |

`patient_report_data.json` の `time`(冊子の本編の数。`available:false` なら他は全部 `null`):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.time.bySpent` | `time.bySpent[].{n, collapsed}`(段は `TIME_VALUES.spentBucketsSec [1,4,9]` = 1 秒/2〜4/5〜9/10 秒以上の 4 段) | `TimeBucket` `lib/reportData.ts:540`、`PatientTime` `:837`、`TIME_VALUES` `:469` | 消費の段ごとの組の数と崩れた数(**設計案 §10.3 の「17/10/0」の実体**。分母は崩れの組 `counted` と同じ) | 無 |
| `obs.time.byLeft` | `time.byLeft[].{n, collapsed}`(段は `leftBucketsSec [60,120]`。`--time-limit-sec` が無ければ `null`) | 同上 | 残り時間の段ごと | 無 |
| `obs.time.afterLongThink` | `time.afterLongThink` | `PatientAfterLongThink` `lib/reportData.ts:613` | 長考の直後の手の崩れ | 無 |
| `obs.time.perMove` | `time.perMove` | `PerMoveTimeStats` `lib/reportData.ts:561` | 1 手の消費の統計 | 無 |
| `obs.time.phaseSpentPatient` | `time.phaseSpent` | `PatientPhaseSpent` `lib/reportData.ts:696`(`PhaseSpentGroup` `:688`・`PerGame` `:708`・`MidOver` `:722`) | 本編用の段ごとの消費(組ごと・局ごと・中盤の超え) | 無 |
| `obs.time.timeUpLosses` | `time.timeUpLosses[]`(本人が時間で負けた局だけ。相手の切れ負けは入らない) | `TimeUpGame` `lib/reportData.ts:810` | 時間負けの局の一覧 | 無 |

`obs_extra.json`(STEP OBS-5'。docs/LANE_DIAG_LOG_2026-09.md §12.6。1 周で不足した観測項目 2 つ「組と局・手の対応」「段ごとの手数あたり」を、既存の材料の写しで作った。`kind:"obs_extra"`):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.time.pairSpent` | `pairs[].{gameNo, branchPly, displayPly, phase, spentSec, spentBucket, collapsed}` | `ObsExtraPair` `lib/obsExtra.ts` | 「組」(`countedPairsOf`)1 つずつに局・手数・段・消費・段ごとの区分・崩れたかを付けた写し。`spentSec`/`spentBucket` は取れない組は `null`(落とさない) | 無 |
| `obs.time.phaseMoves` | `phaseMoves[].{gameNo, timeUpLoss, early, mid, late}.{moves, sec}` | `ObsExtraPhaseMoves` `lib/obsExtra.ts` | 局ごとの段別の手数と消費の合計(`phaseSpentOfGame` と同じ数え方に手数を添えた) | 無 |
| `obs.time.phaseSecPerMoveMedians` | `phaseSecPerMoveMedians.{timeUpLoss,other}.{games, early, mid, late}` | `ObsExtraPhaseSecPerMoveMedians` `lib/obsExtra.ts` | 段ごとの手数あたり秒(`sec/moves`)の中央値。**existing(計算あり: 中央値。閾値ではない)**。`moves` が 0 の局はその段の中央値の分母に入れない(段の列からだけ除く。`games` は組の局の総数で段によらない = レーン長の判断、§12.6 の実測に記録)。`moveSeconds` が無い局は `{moves: 0, sec: 0}` になり「秒が無い」と「その段で 0 手」を区別しない(既知。基準の組では発生なし) | 無 |

`obs_geo.json`(STEP OBS-5。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A)。`kind:"obs_geo"`。`moves[]` の 3 本は §1.15 の `obs.geo.*` を参照):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.time.decisionContext` | `decisionContext[].{gameNo, kifPly, spentBucket, collapse, fork, inCheck, oppPrevCapture, oppPrevDrop, oppPrevGivesCheck, oppPrevPromotion, phase, evalBand}` | `ObsGeoDecisionContext` `lib/obsGeo.ts` | `obs.timeSearch.col.*` のうち `fork inCheck oppPrevCapture oppPrevDrop oppPrevGivesCheck oppPrevPromotion phase evalBand` の 8 本を、5〜9 秒・10 秒以上の帯(`MoveFeatureRow.spentBucket` が `"≤9"`/`">9"`。新しい閾値は置かない)の手だけに絞って写した行。`spentBucket`(どちらの帯か)と、既存の崩れの旗 `collapse` を添える(統括経由の人間の決定、2026-09-25。当初計画の「長考〈10 秒以上〉だけ」から範囲を広げた) | 無 |

### 1.7 `obs.timeSearch.*`(探索。出どころ `time_cause_search.json`(`kind:"time_cause_search"`)。契約 無)

30 列は `SEARCH_COLUMNS` `lib/timeSearch.ts:63` の並びをそのまま ID にする(`obs.timeSearch.col.<列名>`)。値域は `MoveFeatureRow` の各欄(`null` = その手では測れない):

| obs ID(30 本) | 列名(`SEARCH_COLUMNS` の並び) |
|---|---|
| `obs.timeSearch.col.prevOwnSpentBucket` / `.prev3SumBucket` / `.prev5SumBucket` / `.afterLongThink` / `.remainingBucket` | 直前の自分の消費の段/直前 3 手・5 手の合計の段/長考の直後か/残り時間の段 |
| `.phase` / `.evalBand` / `.evalChangePrev` / `.inCheck` / `.fork` | 段/評価の帯/直前の評価の変化/王手中か/分かれ道か |
| `.top1Side` / `.actualSide` / `.lossBand` / `.inTop5` | 第 1 候補の側/実戦の側/損の帯/実戦が 5 候補に入るか |
| `.actualCapture` / `.actualDrop` / `.actualGivesCheck` / `.actualSacrifice` / `.actualRetreat` | 実戦の手の性質(取る/打つ/王手/捨て駒/引く = `ReadMoveMarks` の写し) |
| `.top1Capture` / `.top1Drop` / `.top1GivesCheck` / `.top1Sacrifice` / `.top1Retreat` | 第 1 候補の手の性質(同上) |
| `.oppPrevCapture` / `.oppPrevDrop` / `.oppPrevGivesCheck` / `.oppPrevPromotion` | 相手の直前の手の性質(**設計案 §2 の「相手への反応」の既存の材料**) |
| `.ownRookMoved` / `.oppRookMoved` | 自分/相手の飛車が動いたか |

探索の結果(型 `lib/timeSearch.ts`):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.timeSearch.outcome` | アウトカム `OUTCOMES = longThink / collapse / decisionGap` | `:102` | 探索の目的変数(条件には使わない) | 無 |
| `obs.timeSearch.searches` | `searches.{longThink, collapse, decisionGap}.{depths[], reproduced[], notReproduced[]}` | `SearchesResult` `:447`、`RunSearchResult` `:686`、`CollapseOutcomeSearchResult` `:417`、`DecisionGapSearchResult` `:333` | 深さ 1〜3 の条件の組と、検証側で再現したか(`validateMinN: 10` `:53`) | 無 |
| `obs.timeSearch.conditionStats` | 候補ごとの `{n, longThink, p, collapseCounted, collapsed, q}` | `ConditionStats` `:130`、`Condition` `:128` | 条件が成り立つ手の数と、そのうちのアウトカムの率 | 無 |
| `obs.timeSearch.factors` | `factors[].{column, value, inReproduced{depth1,depth2,depth3,total}, single{discover,validate}, singleOverLine, inKindB, inCollapseReproduced, inKindC, explains{longThink,timeAndCollapse,quickCollapse}, byOutcome, singleDecisionGap}` | `FactorEntry` `:199` | 列 × 値ごとの「一緒に現れる」の要約(A/B/C の型 `Kind` `:146`) | 無 |
| `obs.timeSearch.roleSummary` | `discover`・`validate` の `{moves, longThinkRate, collapseCounted, collapsed, collapseRate}` | `SearchRoleSummary` `:175` | 発見側・検証側の分母 | 無 |

### 1.8 `obs.fork.*`(分かれ道。出どころ `whatif_report_data.json`。契約 無)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.fork.values` | `values.{sideZoneRadius, startPly, minLossCp, narrowGapCp, riseCp, sideVersion, hitsDefenderRadius, attackZoneRadius}`(`WHATIF_VALUES` `lib/whatif.ts:55` の写し: `minLossCp: 600, startPly: 17, sideZoneRadius: 2, attackZoneRadius: 3, hitsDefenderRadius: 2, sideVersion: 2, multiPv: 5`) | `WhatifReportValues` `lib/whatifReport.ts:353` | 使った値(判断的知識の写し。**新しい値は置かない**) | 無 |
| `obs.fork.game` | `games[].{gameNo, id, side, result, total, ending, plyOffset, scores, plies, positionsRead, matchesTop1, withinMultiPv}` | `WhatifReportGameOut` `lib/whatifReport.ts:237` | 局ごとの読んだ局面数・第 1 候補と一致した数・5 候補に入った数 | 無 |
| `obs.fork.representative` | `games[].representative.{kind, ply, displayPly, sfen, actualMove, actualRank, actual{found,scoreCp,mate}, topGapCp}`(`null` = 代表局面が無い) | `WhatifRepresentativeOut` `lib/whatifReport.ts:189`、`WhatifSceneKind` `:93`(`fork/narrowHeld/chanceHeld`) | 代表局面(**分かれ道の正本の定義 = 第 1 候補と 600cp 以上離れた実戦の手、または候補 5 つに入らなかった手**。2026-09-26 に統括が正本を確かめた。**「第 1 候補と実戦の手の側が違う」は分かれ道の定義ではない** ― 側が違うかどうかは分かれ道の中で何が起きたかの話)。**検査 7 の付録 2 の局面の元**。**母集団**: 4 人目の納品で分かれ道は **277(20 局ぶん)**、うち差が測れて局面つきで見えるのが 167(`obs.direct.answer`)| 無 |
| `obs.fork.candidates` | `games[].representative.candidates[].{move, scoreCp, mate, pv}`(先頭 3、pv は 5 手まで) | `WhatifCandidateOut` `:128` | エンジンの候補(**検査 2 の「手」の元**) | 無 |
| `obs.fork.scene` | `games[].representative.scene.{attack, defense, sideGapCp}`(各 `WhatifSideReadOut {state: found/noLegalMove/notMeasured, move?, scoreCp?, mate?, pv?}`) | `:139` | 攻め側・守り側それぞれの最善とその差 | 無 |
| `obs.fork.afterCandidate` | `games[].representative.afterCandidate.{candidateIndex, move, scoreCp, mate, sfenAfter, …}` | `WhatifAfterCandidateOut` `:152` | 候補の読み筋どおりに進めた局面(付録の盤) | 無 |
| `obs.fork.summary` | `summary` | `WhatifReportSummaryOut` `:278` | 全局の集計 | 無 |

`obs_geo.json`(STEP OBS-5d。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A3)。`kind:"obs_geo"`。出どころは `obs.geo.*`〈§1.15〉と同じファイルだが、中身が分かれ道の側なので obsId の列は `fork` にした):

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.fork.sideCrossTable` | `sideCrossTable[].{top1Side, actualSide, count}` | `ObsGeoSideCrossCell` `lib/obsGeo.ts` | `whatif-v2` の `kind:"position"` かつ `scenes.fork` が真の行について、第 1 候補の側(`candidates[0]` に `sideOf` を当てた値。既存)× 実戦の側(`actualSide`。既存)の交差表(4×4 = 16 マス、件数のみ。件数 0 のマスも省かない)。**顧客に送付済みの冊子の「エンジンが攻めのとき実戦も攻めた 53/92」が道具の出力と照合できなかったため道具に載せた**(規則 5 (1))。**`both` は他のマスへ足し込まない**(統括の決定 2026-09-26。「一致」「不一致」という合計はこの表を読む側が作る)。新しい盤の計算・新しい閾値は無し | 無 |
| `obs.fork.sideCrossByGame` | `sideCrossByGame.{gamesTotal, cells[].{top1Side, actualSide, positions, gamesWithAtLeastOne, maxPositionsInOneGame}}` | `ObsGeoSideCrossByGame`・`ObsGeoSideCrossByGameCell` `lib/obsGeo.ts` | `sideCrossTable` と同じ交差表(4×4 = 16 マス)を、**「何局に散っているか」でも数え直した版**(STEP OBS-5h。docs/LANE_DIAG_LOG_2026-09.md §12.14)。**単位・分母・範囲**: `gamesTotal` = 分母(`--whatif-v2-dir` で渡した局の数。無ければ 0)。`positions` = このマスだった fork 局面の**延べ数**(= `sideCrossTable` の同じマスの `count` と同じ)。`gamesWithAtLeastOne` = このマスが 1 局面以上あった**局の数**。`maxPositionsInOneGame` = **1 局の中の**このマスの最多件数。件数 0 のマスも省かない。**`both` は他のマスへ足し込まない**(`sideCrossTable` と同じ、統括の決定 2026-09-26)。新しい盤の計算・新しい閾値は無し | 無 |

### 1.9 `obs.side.*`(側。出どころ `whatif.jsonl`(局ごと)、`direct_answers.json`、探索の列。契約 無)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.side.tags` | `WhatifMoveTags {oppKingZone, ownKingZone, givesCheck, kingMove, captures, hitsOppKingZonePiece, oppKingZone3}` | `lib/whatif.ts:94` | 手の行き先だけで決まる 7 つの印(**幾何**) | 無 |
| `obs.side.of` | `sideOf(tags)` = `attack/defense/both/none`(v2: 攻め = `oppKingZone ∪ givesCheck ∪ captures ∪ hitsOppKingZonePiece ∪ oppKingZone3`、守り = `ownKingZone ∪ kingMove`) | `sideOf` `lib/whatif.ts:121`、`WhatifSide` `:112` | 側の分類。**`both/none` は側の分母に入らない**(設計案 §12 #3) | 無 |
| `obs.side.top1` / `obs.side.actual` | `direct_answers.json` `answers[].{top1Side, actualSide}`、探索の列 `top1Side/actualSide` | `DirectAnswer` `lib/directAnswers.ts:97` | 第 1 候補の側/実戦の側 | 無 |

### 1.10 `obs.read.*`(READ。出どころ `read.jsonl`(`kind:"position"` / `kind:"summary"`)。契約 無)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.read.firstVisibleNodes` | `position.firstVisibleNodes` | `ReadForkPosition` `lib/read.ts:238`(欄 `:245`) | 差が初めて見えたノード数(`READ_VALUES.nodeLadder` `:40` の段) | 無 |
| `obs.read.ladder` | `position.ladder[].{nodes, top{scoreCp,mate}|null, actual{scoreCp,mate,pv}|null}` | `ReadLadderLevel` `:179` | ノード数の段ごとの評価 | 無 |
| `obs.read.marks` | `position.{top1Tags, actualTags}` = `ReadMoveMarks {drop, capture, retreat, declinesPromotion, sacrifice, kingMove, givesCheck}` | `lib/read.ts:122` | 手の性質 7 つ(**幾何**。`sacrifice` は「行き先が相手の利きにあり駒の損得が負」) | 無 |
| `obs.read.opponentReplyMatchesPv` | `position.opponentReplyMatchesPv`、`summary.opponentReplyMatchesPv.{matched, measured}` | `:238`、`ReadGameSummary` `:347` | 相手の応手が読み筋どおりだったか | 無 |
| `obs.read.materialLook` | `position.{top1MaterialLook, actualMaterialLook}`、`summary.materialLook` | `ReadMaterialLookSummary` `:324` | 駒の損得の見え方 | 無 |
| `obs.read.summary` | `summary.{forkPositionsRead, firstVisibleNodesBuckets, tagCrossTable}` + `skippedForkCount, timingMs` | `ReadGameSummary` `:347`、`scripts/playtest/read.ts:206` | 局ごとの集計(印 × 印の交差表) | 無 |

### 1.11 `obs.direct.*`(直接の答え。出どころ `direct_answers.json`・`final_positions.json`。契約 無。両方 `group` 必須)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.direct.answer` | `answers[].{group, kifuId, gameNo, displayPly, sfen, actualMove, top1Move, pv, top1Tags, top1Side, actualTags, actualSide, topGapCp, actualGapCp, firstVisibleNodes}` | `DirectAnswer` `lib/directAnswers.ts:97` | 分かれ道 1 つの「その手・第 1 候補・側・印・見えたノード数」を 1 行に(**検査 7 の付録 3 の局面の元**)。**母集団(2026-09-26 に確かめた)**: 分かれ道のうち**差が測れて局面つきで見えるもの**だけ。4 人目の納品では **167 行 = 20 局ぶん**(分かれ道の全体 277 の部分集合)。**写しに入るときは `--group` で絞られる**ので、3 分の組の写しでは **161 行**になる | 無 |
| `obs.direct.counts` | `counts.{top1TagCounts, top1SideCounts, actualTagCounts, gamesCount, totalCount, totalForkCount}` | `DirectAnswersCounts` `:188` | 印と側の集計。**⚠ 母集団が上の行と違う(P-89。2026-09-26)**: この集計は**組で絞られない**(道具が出した数をそのまま写すため)。4 人目では `totalCount` **167**(20 局ぶん = 3 分 161 + 10 分 6)、`gamesCount` **18**(答えの行がある局の数)、`totalForkCount` **277**(局ごとの `forkCount` の総和 = 分かれ道の全体で、答えの行とは**別の数え方**)。**`obs.direct.answer` の行数(組で絞った数)と同じ分母として並べないこと** | 無 |
| `obs.direct.finalPosition` | `final_positions.json` `entries[].{group, kifuId, gameNo, moves, sfen, mirrored, top1Move, pv, scoreCp, mate}`(根の `kind:"final_positions", nodes, threads, gitHead, dirty`) | `scripts/playtest/finalPositions.ts:196`(欄は無名の型)、`FinalPosition` `lib/finalPosition.ts:28` | 時間切れの最後の局面のエンジンの読み(`mate` の符号つき。**設計案 §10.3 の「−6488・+50・…」の実体**) | 無 |

### 1.12 `obs.menu.*`(承認済みの行動の表。出どころ `answer_menu.json`。契約 docs 一致試験だけ)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.menu.item` | `items[].{id, stage, actionCore, evidenceName, minN, verifyName, verifyGate{fraction,min}|null, foundInSameData}`(`id` = M1〜M9、`stage` = 時間/条件/否定/手順) | `AnswerMenuItem` `lib/answerMenu.ts:64`、`ANSWER_MENU` `:89` | 行動の表の**判定**(条件が成り立つか・分母)。行そのものは 3 種類目の判断的知識(設計案 §11.1) | 無(docs 一致試験 `id・stage・minN`) |

### 1.13 `obs.recog.*`(対局中の認識。出どころ `apps/server/src/analysis/recognitionTimeline.ts`。JSON には書かれない = メモリ上)

| obs ID | 値 | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.recog.shape` | `{ply, kind:"shape", targetId, side, from, to, sfen, moveUsi}`(`from/to` = `ShapeStatus`) | `RecognitionTimelineEntry` `apps/server/src/analysis/recognitionTimeline.ts:52` | 形の認識の遷移。**対局中と対局後の結合キー `(targetId, status, ply)`**(設計案 §9) | 型のみ |
| `obs.recog.intent` | `{ply, kind:"intent", targetId, side:"opponent", from, to, sfen, moveUsi}`(`from/to` = `IntentMatchStatus`) | 同 `:68` | 狙いの認識の遷移 | 型のみ |

### 1.14 `obs.report.*`(冊子の本編の数。出どころ `patient_report_data.json`。契約 無。§1 の表に無かった列 ― 本編の数が仮説から引かれるので登録する)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.report.event` | `events[].{gameNo, kind: drop/matedIfPass, ply, before, after, played, best, sameBest, after5, afterPassMate, playedUsi, bestUsi}` | `PatientEvent` `lib/reportData.ts:247` | 付録 1 の急落の行 | 無 |
| `obs.report.escapeScene` | `escapeScenes[].{gameNo, displayPly, userMove, opponentMove, before, after, escRoot, escEnd, pvEscEnd}` | `EscapeScene` `lib/reportData.ts:326` | C-1 が真の場面(逃げ道の数の前後) | 無 |
| `obs.report.overview` | `overview.{fell, early, mid, late, fromAhead, fromAheadLoss, moveCheck{n,fell,games,otherN,otherFell}|null}` | `PatientOverview` `lib/reportData.ts:380`、`MoveCheckOverview` `:372` | 崩れの数と段の内訳(**設計案 §10.3 の「崩れ 30 = 序 11・中 15・終 4」の実体**) | 無 |
| `obs.report.finding` | `findings[].{kind: timeSpent/timeUpLoss/aheadLoss/phase/none, shown, numbers, labels, text, oneLine}`(`FINDING_VALUES {minPairs: 20, ratio: 2}` `:893`) | `Finding` `lib/reportData.ts:883` | 「ひとことで」の発見。文の数はすべて `numbers` から | 無 |
| `obs.report.previous` | `previous` | `PatientPrevious` `lib/reportData.ts:1044`、`PreviousFindingComparison` `:1036` | 前回の冊子との比較(2 回目以降) | 無 |

### 1.15 `obs.geo.*`(幾何の組み合わせの名前。出どころ `obs_geo.json`(`kind:"obs_geo"`)の `moves[]`。STEP OBS-5、docs/LANE_DIAG_LOG_2026-09.md §12.10 (A)。契約 無)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.geo.moveCombination` | `moves[].{gameNo, kifPly, side, facts, combination}` | `ObsGeoMove` `lib/obsGeo.ts` | 本人の手 1 つの、幾何の事実 4 本(取る・打つ・王手・玉を動かす。`obs.cf.userMoveFacts`・`obs.read.marks` と同じ元を `moveFactsOf`/`moveMarksOf` で取り直したもの)× 側(`obs.side.of` と同じ `sideOf(tagsOf(...))`)から作った組み合わせの名前(決-B)。名前の表(将棋の語彙を 1 語も含まない)は `lib/obsGeo.ts` に 1 か所 | 無 |
| `obs.geo.replyToCapture` | `moves[].{gameNo, kifPly, replyToCapture}` | 同上 | 相手の直前の手が取る手だったかどうか × 本人の手が取る手かどうかの組み合わせの名前(「取り返し」「取らない」「相手は取っていない」の 3 値) | 無 |
| `obs.geo.replyToCheck` | `moves[].{gameNo, kifPly, replyToCheck}` | 同上 | 相手の直前の手が王手だったかどうか × 本人の手の印の組み合わせの名前(「玉を動かす」「取る」「それ以外」「王手ではない」の 4 値)。**設計案 §2 の元の案にあった「合駒」は入れていない**(利きの線を新しく計算することになるため。この段の「既存の道具を呼ぶだけ」という制約を越える ― 決-B の元の案からの逸脱) | 無 |

### 1.16 `obs.vocab.*`(語彙。出どころ `recognition_measure.json`(`kind:"recognition_measure"`)の `byGroup[group]`。STEP OBS-5c、docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2)「計画の直し」2026-09-26。契約 無)

| obs ID | パス | 型(file:line) | 中身 | 契約 |
|---|---|---|---|---|
| `obs.vocab.shapeStatus` | `byGroup[group].statusCounts.shape.{self,opponent}.{none,forming,completed,matched}` | `StatusCountsBySide` `lib/recognitionMeasure.ts` | 形の認識の状態(`none`/`forming`/`completed`。`matched` は使わない)の件数(延べ = 局面 × レコードの行。`none` を捨てない)。種類 × 自分側/相手側 | 無 |
| `obs.vocab.intentStatus` | `byGroup[group].statusCounts.intent.{self,opponent}.{none,forming,completed,matched}` | 同上 | 狙いの認識の状態(`none`/`forming`/`matched`。狙いは常に相手側にしか数えない = `self` は 0 のまま)の件数(延べ) | 無 |
| `obs.vocab.openingStatus` | `byGroup[group].statusCounts.opening.{self,opponent}.{none,forming,completed,matched}` | 同上 | 戦型の認識の状態(`none`/`forming`/`completed`)の件数(延べ) | 無 |
| `obs.vocab.exposure` | `byGroup[group].exposure["D''"].{shape,intent,opening}.{self,opponent}.{named,hedged,hidden}` | `ExposureCounts`(`named`・`hedged`・`hidden` の 3 つだけを写す) `lib/recognitionMeasure.ts` | **【顧客の文に使わない】**(既知事項 P-99。この数は**道具の振る舞い**〈名前を出すか控えるか隠すかの規則がどう働いたか〉であって、顧客の指し方ではない。内部の読みには使ってよい) 露出の値の組 `D''`(STEP EXPO-1b の中間案)を当てたときの `named`/`hedged`/`hidden` の件数(延べ)。種類 × 自分側/相手側。`hiddenCompletedNoEvidence`・`weakClaims`・`weakClaimsShown`・`pickedByR5p`・`droppedByR6`・`droppedByR6ById`(id → 数の対)は写さない(統括の追加指示、2026-09-25。**§2 に予約が無かった新規 ID** ― `obs.vocab.shapeStatus/intentStatus/openingStatus` と違い、設計案 §2 の元の表には無い) | 無 |
| `obs.vocab.shapeMissingSummary` | `byGroup[group].{shapeMissingTotal,selfClosestOneAwayGames}` | `GroupTotals` `lib/recognitionMeasure.ts` | 「あと 1 枚」の中身(STEP OBS-5e。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A4))。欠けたマス・駒の延べ件数(forming だった局面だけ)と、自分側の「最も近づいた形」の欠けがちょうど 1 枚だった局の数。**件数だけ**(形 id ごとの内訳〈`shapeMissingCounts`。id → 数の対〉、局ごとの「最も近づいた形」の中身〈`rows[].closestSelfShape`。id・マス・駒の文字列〉は写さない ― §2 に予約が無かった新規 ID) | 無 |
| `obs.vocab.shapeMovedRequiredSummary` | `byGroup[group].shapeMovedRequiredCompleteTotal`、`movedRequiredZeroShapeCounts.{self,opponent}` | 同上、`RecognitionMeasureResult` `lib/recognitionMeasure.ts` | 到達率を「初期位置でない必要駒」だけで数え直した版(STEP OBS-5e)。数え直した到達率が 1.0 に達した局数の延べ(id をまたいだ合計)と、「初期位置でない必要駒」が 0 の形(数え直せない形)の件数(自分側・相手側)。**件数だけ**(形 id ごとの内訳〈`shapeMovedRequiredBest`・`gamesMovedRequiredComplete`〉、id の一覧〈`movedRequiredZeroShapeIds`〉は写さない ― §2 に予約が無かった新規 ID) | 無 |
| `obs.vocab.shapeOneAwayDetail` | `rows[].closestSelfShape`(`missing` がちょうど 1 件の行)→ `{gameNo,shapeId,square,piece}` | `ClosestSelfShape`・`MissingPiece` `lib/recognitionMeasure.ts` | 「止まる場所」(STEP OBS-5f。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A5))。欠けがちょうど 1 枚だった局それぞれの、欠けていた駒の種類・マスと局番号。局番号は固定棋譜の `id` ではなく、`--patient` の `games[].id`↔`no` で数に変換したもの。**白いリスト(`numbersOnly`)に初めて開けた文字列の穴**(形の id・マス・駒の 2 種類だけ) | 無 |
| `obs.vocab.shapeMovedRequiredPerGame` | `rows[].{closestSelfShape.movedRequired,shapeMovedRequiredBestArrived}` → `{gameNo,shapeId,arrivedAtClosest,arrivedBest,total,piecesAtClosest[]}` | 同上 | 局ごとの「**動かして持って来る必要がある必要駒**が何枚来ていたか」(STEP OBS-5g)。**範囲の違う 2 つの数を、名前で分けて持つ**:**`arrivedAtClosest`** = **最も近づいた 1 局面**での到着枚数。**`arrivedBest`** = **局を通して**いちばんそろった時点での到着枚数(**最大が 1 なら、その局では一度も それ以上そろっていない**)。`total` はその形で動かす必要がある枚数、`piecesAtClosest[]` は `{square,piece,arrived}`。**「もう 1 枚が最後まで来ない」は `arrivedBest` で言う**(局全体についての言明なので)。**2 つは実データで食い違う** ― `<p4>` の 3 分 18 局では `arrivedAtClosest` が 1 / 10 / 5、`arrivedBest` が 1 / 12 / 3 で、第 2・第 4 局が動く(**局のどこかでは 1 枚来ていたが、最も近づいた局面では 0 枚**)。**片方だけを見て他方の問いに答えない**(既知事項 P-95。**この規則を出した本人が踏んだ**)。**なぜ枚数で持つか**: 割合の 0.5 を「2 枚のうち 1 枚」と読むには `data/` の形の定義が要り、**その読み替えは導出**になる。冊子の柱の数を**写しから直に読める**ようにするための欄(規則 5 (1)) | 無 |
| `obs.vocab.shapeClosestPerGame` | `rows[].closestSelfShape.shapeId` と `rows[].shapeBest` / `rows[].shapeMovedRequiredBest` → `{gameNo,shapeId,rawBest,movedRequiredBest}` | 同上 | 局ごとの「最も近づいた形」(STEP OBS-5f)。形 id と到達率を、生(`shapeBest`)・「初期位置でない必要駒」だけで数え直した版(`shapeMovedRequiredBest`)の両方で示す。数え直せない形(分母 0)は `movedRequiredBest: null` | 無 |

`statusCounts`(`lib/recognitionMeasure.ts`)は `countExposure` と違い `status`(または `matchStatus`)が `"none"` の行も捨てずに数える(STEP OBS-5c の直し。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A2) の「計画の直し」)。`exposure["D''"]` は既存(STEP EXPO-1b)。

**`obs.vocab.shapeOneAwayDetail`・`obs.vocab.shapeClosestPerGame` が文字列(`shapeId`・`square`・`piece`)を通してよい理由(STEP OBS-5f。docs/LANE_DIAG_LOG_2026-09.md §12.10 (A5) 条件 3)**: `square`・`piece`(駒の種類とマス)は盤の幾何の事実であり、`shapeId` は `data/` の認識(`review_status` を経たもの)である。**道具(`data/` の定義)が既に持つ id をそのまま写すだけ**で、LLM や役がここで新しく将棋の知識で名前を付けるわけではない(名前として顧客に出せるかは、この写しとは別の露出の規則が決める)。固定棋譜の `id`(`g01` 等)は直接は通さず、`--patient` の `games[].id`↔`no` で数(局番号)に変換してから使う ― 通す文字列を「形の id」と「マス + 駒」の 2 種類だけに保つため。

**`obs.vocab.shapeMovedRequiredSummary` の読み方(既知事項 P-90。2026-09-26 の実測で分かった)**: 数え直しは平手の初期配置にある必要駒を分母から外すので、**外した駒がその後に動いてしまった局でも 1.0 になる**。`shapeMovedRequiredCompleteTotal` は **「形が完成した局の数」ではない**(実例: `<p4>` の 3 分の 18 局で、自分側 `mutekigakoi` は生の完成 0 局なのにこの数には 1 局入る)。**この数を「囲いが完成した」と言い換えないこと。** 生の完成は `obs.recog.*` 側の `gamesCompleted`(写していない)ではなく、写しでは `obs.vocab.shapeStatus` の `completed` の件数で見る。

---

### 1.x 顧客の文に使わない観測(**名指しの一覧**。既知事項 P-99。2026-09-26)

**ここに挙げた観測は、数が実在し分母が書かれ禁止語が 0 件でも、顧客が読む文には入れない。** 理由は**その数の主語が顧客の指し手ではなく道具だから**である(「こちらの仕組みがどう働いたか」は顧客が使えない)。**内部の読み・仮説・整合には使ってよい。**

| 観測 | なぜ顧客の文に使わないか |
|---|---|
| `obs.vocab.exposure` | 名前を**出すか・控えるか・隠すか**の規則がどう働いたかの件数。顧客の指し方ではない。実例(2026-09-26、言い換え役 B の初回): 「控えめに言った形が 657 件、出さなかったものが 4703 件」が顧客の表に入り、**機械の検査も語の検査も全部通った** |

**この一覧の使い方**: 役の指示文と監査の観点に「**この一覧の観測を顧客の文に入れない**」を置く。**語の一覧(仕組みの語)とは別の歯止め** ― 語は機械で見られるが、**主語が顧客か道具かは語では見られない**(P-99 の本体)。**新しい観測を §1 に足すときは、顧客の文に使ってよいかを 1 行で決める。**

## 2. `copy` / `new` / `vocab` ― 設計案 §2 の項目(**まだ値は無い**。H-2 では引けない)

| obs ID(設計案 §2) | 状態 | 既存の元(あれば) | 備考 |
|---|---|---|---|
| `obs.geo.kingSquare` | `new` | ―(`kingSurroundingsOf` が内部で玉の升を探すが、出力していない) | 玉の升。新しい出力 |
| `obs.geo.kingNeighbors` | `copy` | `obs.fe.kingSurroundings {squares, own}` | 名前を付け直すだけ。ただし Failure Event の `trigger` にしか無い(急落の手前の局面だけ)。全手で出すなら `new` |
| `obs.geo.kingEscapes` | `copy` | `obs.cf.kingEscapesRoot` / `obs.cf.kingEscapesEnd` | 同上(組の分かれ目と終点だけ) |
| `obs.geo.kingZoneReach` | `copy` | `obs.fe.positionFacts`(`zonePieces`・`zoneControl`) | 同上 |
| `obs.geo.rookFile` | `new` | `obs.time.rookMark {own, opponent}`(動いたか、の真偽だけ。筋は持たない) | 筋の番号は新しい出力 |
| `obs.geo.rookMovedPly` | `new` | 同上(手数を持たない) | |
| `obs.geo.bishopDiagonalOpen` | `new` | ― | |
| `obs.geo.rookSquare` / `obs.geo.kingRookDistance` | `new` | ― | |
| `obs.geo.developedCount` / `obs.geo.piecesInOppHalf` / `obs.geo.handCount` | `new` | ― | |
| `obs.geo.attackersNearOppKing` / `obs.geo.defendersNearOwnKing` | `copy`(半径は既存の値) | `obs.fe.positionFacts.zonePieces`(区域 = 玉 + 8 近傍 = 半径 1)。半径 2・3 の数は `obs.side.tags`(真偽だけ)に元があるが枚数は無い | 半径 1 なら `copy`、半径 2・3 の枚数は `new` |
| `obs.geo.replyToCapture` / `obs.geo.replyToCheck` | **→ §1.15(実体化済み)** | `obs.timeSearch.col.oppPrevCapture/oppPrevGivesCheck`(相手の直前の手の種類)+ `obs.read.marks`(本人の手の種類)。「取り返し/逃げ/無関係」「玉を動かす/合駒/取る」の**組み合わせの名前**は `new` だった | **OBS-5(§12.10 (A))で実体を作った**。値は「取り返し/取らない/相手は取っていない」「玉を動かす/取る/それ以外/王手ではない」の**確定した 3・4 値**(「合駒」は入れていない。§1.15 参照) |
| `obs.geo.moveFacts` | `copy` | `obs.cf.userMoveFacts`(U-1〜U-9)、`obs.read.marks`、`obs.side.tags` | **3 つの既存の型に散っている**。1 つに寄せるのは実装の判断 |
| `obs.geo.moveSide` | `copy` | `obs.side.of` | |
| `obs.geo.moveCombination`(決-B) | **→ §1.15(実体化済み)** | `obs.cf.userMoveFacts` × `obs.side.of` の組み合わせ(例: 「取る・相手玉側」) | **OBS-5(§12.10 (A))で実体を作った**。目的候補の列挙の代わり。名前の表は `lib/obsGeo.ts` に 1 か所(語彙ではなく幾何) |
| `obs.time.decisionContext` | **→ §1.6(実体化済み)** | `obs.timeSearch.col.*` のうち `fork inCheck oppPrevCapture oppPrevDrop oppPrevGivesCheck oppPrevPromotion phase evalBand` を、長考した手(`obs.time.longThinkCountByPhase` の手)に限って写す予定だった | **OBS-5(§12.10 (A))で実体を作った**。30 列は既に全手で出ている。統括経由の人間の決定(2026-09-25)で、対象は当初の「長考(10 秒以上)だけ」から「5〜9 秒・10 秒以上の帯」に広げ、`spentBucket`・`collapse` を添えた(§1.6 の `obs_geo.json` 参照) |
| `obs.geo.moveNumberOfFirstContact` / `obs.geo.promotionCount` | `new` | ― | |
| `obs.vocab.shapeStatus` | **→ §1.16(実体化済み)** | `obs.fe.shape`(急落の手前だけ)、`obs.recog.shape`(対局中、メモリ上) | 値域として想定していたのは `data/shapes/*.json` の `id` × `none/forming/completed`(id の一覧)だったが、**id の一覧は写さない**(白いリストの門)ため、**STEP OBS-5c(§12.10 (A2))で実体化したのは種類 × 側 × 状態の件数**(id ごとの内訳ではない) |
| `obs.vocab.intentStatus` | **→ §1.16(実体化済み)** | `obs.fe.opponentIntent`、`obs.recog.intent` | 同上(狙いは `self` が常に 0) |
| `obs.vocab.openingStatus` | **→ §1.16(実体化済み)** | ―(`data/openings` 3 件は実行時に読まれていない) | **STEP OBS-5c で `recognitionMeasure.ts` が読む戦型(下書きを含む)に実体化**。同上の件数 |
| ~~`obs.vocab.purposeCandidates`~~ | **置かない** | ― | 決-B(2026-09-25)。目的候補の列挙は許さない |

---

## 3. 数(2026-09-26。**この節は人が手で持つ数を置かない** ― 統括の決定)

> **§1 から数えられる数は、ここに書かずに §1 を指す。** 2026-09-26 に、下の「`existing` の ID」の総数と内訳が **OBS-5g(124→125)・OBS-5h(125→126)の 2 周続けて更新漏れ**していたことが分かった(OBS-5h の実装担当が見つけ、独立監査が範囲を確かめた)。**原因は、そこが人が手で持っている数だから** ― 機械が読むのは §1 の表の行だけ(`lib/hypothesis.ts` の `loadObsRegistry` は `## 1.` から `## 2.` の手前まで)で、**この節の数は誰も検査していない。書いておけば 3 周目も漏れる。** そこで**総数と接頭辞ごとの内訳を消し、数え方だけを残した。**
> **残してある数は、同じ文の中に一覧があるもの**(数と一覧が離れていないので、片方だけずれない)。
> **人が持たない数は、ずれない。**「次は忘れずに直す」は構造ではない(統括、2026-09-26)。

| 数えるもの | 数 |
|---|---|
| `existing` の ID(§1) | **数えない(§1 を数えること)**。数え方 = §1 の `## 1.` から `## 2.` の手前までで、`` | `obs. `` で始まる行の先頭欄にある `obs.*` を全部(1 セルに複数ある行は全部)+ `obs.timeSearch.col.` × `SEARCH_COLUMNS`(`lib/timeSearch.ts` の要素数。§1.7 の表は 5〜6 本ずつ束ねて書いてあり、先頭以外は `.name` の略記なので**行から数えられない**のはここだけ)。**機械の正本は `lib/hypothesis.ts` の `loadObsRegistry` で、その数は `lib/hypothesis.test.ts` の「`existing` の大きさは N」が固定している**(この数を直すのは観測項目を足す STEP の仕事) |
| うち既存の欄名と 1 対 1 で対応した ID | **すべて**(ID の名前 = 欄名または型名)。**数は書かない** ― 上と同じ数なので、片方だけずれる |
| うち JSON スキーマ(契約)のある ID | **16** = eval 1(`standing`)+ fe 8 + moment 3 + cond 4。cf 7 は「穴」(スキーマの `properties` が空)で契約あり扱いにしない。recog 2 は型のみ。**残りは契約 無**(数は書かない ― 総数から引いた数なので、総数がずれると一緒にずれる)(OBS-5' の 3 本・OBS-5 の 4 本・OBS-5c の 4 本・OBS-5e の 2 本・OBS-5d の 1 本・OBS-5f の 2 本も契約 無) |
| 設計案 §2 の項目(§2 の表) | **20 行**(`copy` 6・`new` 7・`vocab` 0・置かない 1・**→ §1(実体化済み)6**〈STEP OBS-5 の 3 + STEP OBS-5c の 3〉)。数え方: 行の状態の欄。「`copy` の一部 + `new`」「`copy`(半径 1)/`new`(半径 2・3)」の行はそれぞれ `new`・`copy` に数えた(→ §1 の 6 行は元 `new` 2〈`moveCombination`・`replyToCapture`/`replyToCheck` の対〉+ `copy` 1〈`decisionContext`〉+ `vocab` 3〈`shapeStatus`・`intentStatus`・`openingStatus`〉)。**`obs.vocab.exposure`・`obs.vocab.shapeMissingSummary`・`obs.vocab.shapeMovedRequiredSummary`・`obs.fork.sideCrossTable`(STEP OBS-5d)・`obs.vocab.shapeOneAwayDetail`・`obs.vocab.shapeClosestPerGame`(STEP OBS-5f)は §2 に元の行が無い新規 ID なので、この 20 行には数えない**(§1.16・§1.8 に直接足した) |
| 設計案 §1 の表と欄名が食い違っていたもの(この一覧で直した) | **2**: (1) `TIME_VALUES` の置き場は `lib/timeCause.ts` ではなく `lib/reportData.ts:469`。(2) 設計案 §7 の例のパス `groups[min3].other.phaseSpentMedian.mid` は実在せず、正しくは `groups[].other.medianMidSec`(§7 は案の JSON なので、契約の実装で直す) |
| 対応が取れなかった ID | **0**(取れなかったものは `new` として §2 に置いた) |

**幾何/語彙の内訳**(§1 の `existing` のうち、設計案 §2 の線で「幾何(知識なし)」に当たるもの): `obs.fe.kingSurroundings`・`obs.fe.positionFacts`・`obs.cf.kingEscapesRoot/End`・`obs.cf.userMoveFacts`・`obs.cf.pvMinusActual`・`obs.side.tags`・`obs.side.of`・`obs.read.marks`・`obs.time.rookMark`・探索の列のうち手の性質 14 本(`actual*` 5・`top1*` 5・`oppPrev*` 4)・`obs.geo.moveCombination`・`obs.geo.replyToCapture`・`obs.geo.replyToCheck`(STEP OBS-5 の 3 本) = **27**。「語彙(認識)」に当たるもの: `obs.fe.shape`・`obs.fe.opponentIntent`・`obs.recog.shape`・`obs.recog.intent`・`obs.vocab.shapeStatus`・`obs.vocab.intentStatus`・`obs.vocab.openingStatus`・`obs.vocab.exposure`(STEP OBS-5c の 4 本)・`obs.vocab.shapeMissingSummary`・`obs.vocab.shapeMovedRequiredSummary`(STEP OBS-5e の 2 本)・`obs.vocab.shapeOneAwayDetail`・`obs.vocab.shapeClosestPerGame`(STEP OBS-5f の 2 本) = **12**。**残りは**評価・時間・探索の集計・冊子の数(**数は書かない** ― 総数から引いた数なので)(どちらの列でもない = 数。OBS-5' の 3 本・OBS-5 の `obs.time.decisionContext`・OBS-5d の `obs.fork.sideCrossTable` もここ)。

---

## 4. 設計案との対応

- 設計案 §1 の表の ID は、この一覧で **`obs.fe.*` を 8 本に、`obs.cf.*` を 7 本に、`obs.time.*` を 24 本(OBS-5' の 3 本・OBS-5 の `decisionContext` 1 本を含む)に、`obs.timeSearch.*` を 35 本に分解**した(§1 の表は列の粗さで書いていた)。`obs.report.*` は §1 に無かった列(冊子の本編の数)。`obs.geo.*` は STEP OBS-5 でこの一覧に初めて `existing` が付いた列(3 本)。`obs.vocab.*` は STEP OBS-5c でこの一覧に初めて `existing` が付いた列(8 本。うち `obs.vocab.exposure`〈STEP OBS-5c〉・`obs.vocab.shapeMissingSummary`・`obs.vocab.shapeMovedRequiredSummary`〈STEP OBS-5e〉・`obs.vocab.shapeOneAwayDetail`・`obs.vocab.shapeClosestPerGame`〈STEP OBS-5f〉の 5 本は設計案 §2 に元の行が無い新規 ID。**`obs.vocab.shapeOneAwayDetail`・`obs.vocab.shapeClosestPerGame`は、白いリスト〈`numbersOnly`〉に初めて文字列(形の id・マス・駒)を通した ID でもある**)。`obs.fork.*` は STEP OBS-5d で 8 本目(`obs.fork.sideCrossTable`)が付いたが、出どころは `whatif_report_data.json` ではなく `obs_geo.json`(§1.8 に注記)で、これも設計案 §2 に元の行が無い新規 ID。
- 設計案 §7 の H-2 は、この一覧の **§1(`existing`)だけ**を登録済みとする。§2 の ID を引いた仮説は落ちる(値が無いので)。
- 設計案 §10.3 の実例が引いた数の実体: 崩れの内訳 = `obs.report.overview`、消費の段ごと = `obs.time.bySpent`、中央値 = `obs.time.groupMedians`、長考の分母 = `obs.time.longThinkTotal`、時計で終わった局の最後の評価 = `obs.direct.finalPosition`。**5 つとも `existing`。**
