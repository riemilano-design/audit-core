// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.2・§7.5)。「1 手ごとの特徴の表」を組む段の
// 純粋関数。**測る段だけ**(探索は lib/timeSearch.ts、CLI は scripts/playtest/timeSearch.ts、PDF は
// report-pdf/render_time_cause.py の追加ページ)。
//
// 【このファイルがやること】
// - `lib/timeCause.ts` の局ごとの計算(`ownMoveTimesOf`・`rookOnInitialFileOf`・`sfenBeforeOriginalKifPly`)を、
//   本人の手ごとの 1 行に広げる(`buildGameMoveFeatureRows`)。値はすべて既存の道具の出力から作り、
//   **新しい閾値は置かない**(`TIME_VALUES`・`spentBucketIndexOf`・`leftBucketIndexOf`・`STANDING_BOUNDS` を
//   import して使うだけ)。
// - 段 2 の記録(replay.ts → rescreen.ts の JSONL、`RecordLine[]`)から、`lib/failureEvent.ts` の
//   `readEvaluations`・`pairEvaluations` をそのまま呼び、本人の手の直前の行(ready 行。ply = recordPly − 1)の
//   評価・局面を読む(記録の `sfen` をそのまま使う。P-77 と同じ、記録が既に本人 = 先手にそろえてある前提)。
//   **記録の ready 行はすべて「本人の手番」の局面**であり、相手の手を指す前(相手の手番)の局面は記録に無いため、
//   1 つ前の ready 行の `sfen` に同じ行の `senteMove`(本人の直前の手)を 1 手重ねて作る(既存の `applyMove` を
//   1 回呼ぶだけ ― 実装担当の判断。実データ〈tatsunami20〉で確かめた: record.ply は常に偶数で、奇数手番
//   〈相手の手番〉の局面は記録されていない)。
// - whatif-v2(STEP WHATIF 作業 4)の position 行がある手だけ、`lib/read.ts` の `moveMarksOf`(既存)を
//   実戦の手・第 1 候補の手に当てて印を作る(whatif-v2 自身の `actualTags`/`candidates[].tags` は
//   側〈攻め・守り〉の印であって、この段が要る「取る/打つ/王手/捨て駒/引く」とは別物 ― 実装担当の判断)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンを起動すること(CLI の役目)
// - 将棋の判断・戦法の名前を付けること。閾値を新しく置くこと(すべて既存の値の使い回し)
// - 探索(単独・2・3 条件の列挙、採用候補・再現の判定)をすること(lib/timeSearch.ts の役目)

import type { RecordLine } from "../invariants/types.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { pairEvaluations, readEvaluations, STANDING_BOUNDS, type Evaluation } from "./failureEvent.js";
import { moveMarksOf } from "./read.js";
import { standingOf } from "./standing.js";
import { originalMovesOf, plyOffsetOf, leftBucketIndexOf, sideOf, spentBucketIndexOf, TIME_VALUES, moveSecondsOf } from "./reportData.js";
import { ownMoveTimesOf, rookOnInitialFileOf, sfenBeforeOriginalKifPly, TimeCauseError, type OwnMoveTime, type Side, type TimeCauseFixedKifu } from "./timeCause.js";
import type { WhatifSideRaw } from "./type.js";

// ---- 段の値(離散化の段だけ。既存の TIME_VALUES・STANDING_BOUNDS の使い回し) ----

/** `TIME_VALUES.spentBucketsSec`([1, 4, 9])の 4 段のラベル(計画「作るもの」1.)。 */
export const FEATURE_SPENT_BUCKET_LABELS = ["≤1", "≤4", "≤9", ">9"] as const;
export type FeatureSpentBucket = (typeof FEATURE_SPENT_BUCKET_LABELS)[number];

function spentBucketLabelOf(spentSec: number): FeatureSpentBucket {
  return FEATURE_SPENT_BUCKET_LABELS[spentBucketIndexOf(spentSec)]!;
}

/** `TIME_VALUES.leftBucketsSec`([60, 120])の 3 段のラベル。 */
export const FEATURE_LEFT_BUCKET_LABELS = ["<60", "60-119", ">=120"] as const;
export type FeatureLeftBucket = (typeof FEATURE_LEFT_BUCKET_LABELS)[number];

function leftBucketLabelOf(leftSec: number): FeatureLeftBucket {
  return FEATURE_LEFT_BUCKET_LABELS[leftBucketIndexOf(leftSec)]!;
}

/** 直前の自分の手からの評価の向き。「同」は既存の崩れの境(`STANDING_BOUNDS`、±300)を使い回す。 */
export type FeatureEvalChange = "up" | "same" | "down";

function evalChangeOf(diffCp: number): FeatureEvalChange {
  if (diffCp >= STANDING_BOUNDS.aheadCp) return "up";
  if (diffCp <= STANDING_BOUNDS.behindCp) return "down";
  return "same";
}

/** `standingOf` の戻り値のうち、文字列(ahead/level/behind)だけを読む(undetermined は null)。 */
function evalBandOf(evaluation: Evaluation): "ahead" | "level" | "behind" | null {
  const standing = standingOf(evaluation, STANDING_BOUNDS);
  return typeof standing === "string" ? standing : null;
}

/**
 * `loss.cpValue` を崩れの境(`STANDING_BOUNDS.aheadCp` = 300)で 2 値にする。`isLowerBound`(実戦の手が
 * 候補に無い)は「候補外」を優先する(計画「作るもの」1. の指示どおり)。`cpValue` が null(詰みが絡む等、
 * `isLowerBound` でもない)は判定できないので null。
 */
export type FeatureLossBand = "over300" | "under300" | "outOfCandidates";

function lossBandOf(cpValue: number | null, isLowerBound: boolean): FeatureLossBand | null {
  if (isLowerBound) return "outOfCandidates";
  if (cpValue === null) return null;
  return cpValue >= STANDING_BOUNDS.aheadCp ? "over300" : "under300";
}

// ---- whatif-v2 の入力(この段が使う分だけ) ----

/**
 * whatif-v2 の position 行から、この段が使う分だけ(`lib/timeCause.ts` の `TimeCauseWhatifPositionInput` を
 * 選択の列ぶん広げたもの ― 実装担当の判断: 同じ型を拡張せず新しく持つ。C7・C8〈timeCause.ts〉は fork・side しか
 * 使わないため、そちらの型は変えない)。`ply` は本人の手の recordPly と同じ数え方(timeCause.ts と同じ前提)。
 */
export interface MoveFeatureWhatifPosition {
  ply: number;
  /** 本人の手番の局面(whatif-v2 が読んだ向き。`sfen` と `actualMove`/`top1Move` は同じ座標系)。 */
  sfen: string;
  fork: boolean;
  top1Side: WhatifSideRaw;
  actualSide: WhatifSideRaw;
  /** 第 1 候補(candidates[0])の手。 */
  top1Move: string;
  actualMove: string;
  actualRank: number | null;
  lossCpValue: number | null;
  lossIsLowerBound: boolean;
}

// ---- 1 行(MoveFeatureRow) ----

export interface MoveFeatureRow {
  kifuId: string;
  group: string;
  gameNo: number;
  /** KIF の手数(「◯手目」の◯と同じ)。 */
  kifPly: number;

  // 時間
  spentSec: number;
  spentBucket: FeatureSpentBucket;
  prevOwnSpentBucket: FeatureSpentBucket | null;
  prev3SumBucket: FeatureSpentBucket | null;
  prev5SumBucket: FeatureSpentBucket | null;
  /** 直前の自分の手が長考(`TIME_VALUES.longThinkSec` 以上)だったか。直前の自分の手が無ければ null。 */
  afterLongThink: boolean | null;
  /** `--time-limit-sec` が無ければ null。 */
  remainingBucket: FeatureLeftBucket | null;

  // 局面
  phase: "early" | "mid" | "late";
  evalBand: "ahead" | "level" | "behind" | null;
  evalChangePrev: FeatureEvalChange | null;
  /** 王手を受けているか(この手を指す前)。評価行が無ければ null。 */
  inCheck: boolean | null;

  // 選択(whatif-v2 の position 行がある手だけ)
  fork: boolean | null;
  top1Side: WhatifSideRaw | null;
  actualSide: WhatifSideRaw | null;
  lossBand: FeatureLossBand | null;
  inTop5: boolean | null;
  actualCapture: boolean | null;
  actualDrop: boolean | null;
  actualGivesCheck: boolean | null;
  actualSacrifice: boolean | null;
  actualRetreat: boolean | null;
  top1Capture: boolean | null;
  top1Drop: boolean | null;
  top1GivesCheck: boolean | null;
  top1Sacrifice: boolean | null;
  top1Retreat: boolean | null;

  // 相手(直前の手。取る/打つ/王手/成る)
  oppPrevCapture: boolean | null;
  oppPrevDrop: boolean | null;
  oppPrevGivesCheck: boolean | null;
  oppPrevPromotion: boolean | null;

  // 形(局の C9 の印。全行に同じ値)
  ownRookMoved: boolean | null;
  oppRookMoved: boolean | null;

  // 目的変数
  longThink: boolean;
}

// ---- 直前 n 手(本人。kifPly が 2 ずつ連続している場合だけ) ----

/**
 * `own`(kifPly 昇順)の `index` 番目の手から見て、直前の `n` 手が「2 ずつ連続する本人の手」であれば返す
 * (間に秒の読めない本人の手が挟まっていれば null。`lib/reportData.ts` の `buildAfterLongThink` の
 * 「2 手前」〈秒が無ければ数えない〉と同じ考え方を、3 手・5 手にも広げた ― 実装担当の判断)。
 */
function prevContiguousOwnMovesOf(own: readonly OwnMoveTime[], index: number, n: number): OwnMoveTime[] | null {
  if (index < n) return null;
  const out: OwnMoveTime[] = [];
  for (let step = 1; step <= n; step++) {
    const candidate = own[index - step]!;
    if (candidate.kifPly !== own[index]!.kifPly - 2 * step) return null;
    out.push(candidate);
  }
  return out;
}

function sumSecOf(moves: readonly OwnMoveTime[]): number {
  return moves.reduce((sum, m) => sum + m.sec, 0);
}

// ---- 1 局ぶん ----

/** 局ごとに `MoveFeatureRow` の列を組む(計画「作るもの」1.)。 */
export function buildGameMoveFeatureRows(
  fixed: TimeCauseFixedKifu,
  gameNo: number,
  group: string,
  timeLimitSec: number | undefined,
  records: readonly RecordLine[],
  whatifPositions: readonly MoveFeatureWhatifPosition[] | null,
): MoveFeatureRow[] {
  const side: Side = sideOf(fixed);
  const plyOffset = plyOffsetOf(fixed);
  const originalMoves = originalMovesOf(fixed);
  const total = originalMoves.length;
  const seconds = moveSecondsOf(fixed);
  if (seconds === null) throw new TimeCauseError(`${fixed.id} に moveSeconds が無い(この道具は秒の読めた固定棋譜だけを扱う)`);
  const own = ownMoveTimesOf(side, plyOffset, total, seconds);

  // 形(C9。timeCause.ts の buildGameTimeCause と同じ求め方 ― 既存の関数だけを呼ぶ。全行に同じ値を付ける)
  const firstMid = own.find((m) => m.phase === "mid");
  let ownRookMoved: boolean | null = null;
  let oppRookMoved: boolean | null = null;
  if (firstMid !== undefined) {
    const sfenAtFirstMid = sfenBeforeOriginalKifPly(originalMoves, firstMid.kifPly);
    const opponentSide: Side = side === "先手" ? "後手" : "先手";
    ownRookMoved = !rookOnInitialFileOf(sfenAtFirstMid, side);
    oppRookMoved = !rookOnInitialFileOf(sfenAtFirstMid, opponentSide);
  }

  // 段 2 の記録(ready 行だけ、ply 昇順)。row.ply + 1 = 本人の手の recordPly(triggerOf の branchPly と同じ規約)。
  const evalRows = readEvaluations(records);
  const evalPairs = pairEvaluations(evalRows);
  const evalIndexByPly = new Map<number, number>(evalRows.map((row, index) => [row.ply, index]));

  const whatifByPly = new Map<number, MoveFeatureWhatifPosition>();
  if (whatifPositions !== null) for (const position of whatifPositions) whatifByPly.set(position.ply, position);

  const rows: MoveFeatureRow[] = [];
  let usedBefore = 0;
  for (let index = 0; index < own.length; index++) {
    const move = own[index]!;
    const thisUsedBefore = usedBefore;
    usedBefore += move.sec;

    const prevOwn = prevContiguousOwnMovesOf(own, index, 1);
    const prev3 = prevContiguousOwnMovesOf(own, index, 3);
    const prev5 = prevContiguousOwnMovesOf(own, index, 5);

    const evalRowIndex = evalIndexByPly.get(move.recordPly - 1);
    const evalRow = evalRowIndex === undefined ? undefined : evalRows[evalRowIndex]!;
    const prevEvalRow = evalRowIndex === undefined || evalRowIndex === 0 ? undefined : evalRows[evalRowIndex - 1]!;
    const evalPair = evalRowIndex === undefined || evalRowIndex === 0 ? undefined : evalPairs[evalRowIndex - 1]!;

    const evalBand = evalRow === undefined ? null : evalBandOf(evalRow.evaluation);
    const evalChangePrev = evalPair !== undefined && evalPair.kind === "compared" ? evalChangeOf(evalPair.diffCp) : null;
    const inCheck = evalRow === undefined ? null : isSenteInCheck(evalRow.record.sfen);

    // 相手の直前の手(この行の直前の評価行の goteMove)。評価行の sfen はどれも「本人〈= sente〉の手番」の
    // 局面なので(§7.2 の実測で確かめた。record.ply は常に偶数)、相手の手を指す前の局面(相手の手番)は
    // 直前の評価行の sfen に本人の手〈同じ行の senteMove〉を当てて作る(既存の applyMove を 1 手ぶん重ねるだけ)。
    let oppPrevCapture: boolean | null = null;
    let oppPrevDrop: boolean | null = null;
    let oppPrevGivesCheck: boolean | null = null;
    let oppPrevPromotion: boolean | null = null;
    if (
      evalRow !== undefined &&
      prevEvalRow !== undefined &&
      evalRow.record.senteMove !== null &&
      evalRow.record.senteMove !== undefined &&
      evalRow.record.goteMove !== null &&
      evalRow.record.goteMove !== undefined
    ) {
      const oppMove = evalRow.record.goteMove;
      const sfenBeforeOppMove = applyMove(prevEvalRow.record.sfen, evalRow.record.senteMove);
      const marks = moveMarksOf(sfenBeforeOppMove, oppMove);
      oppPrevCapture = marks.capture;
      oppPrevDrop = marks.drop;
      oppPrevGivesCheck = marks.givesCheck;
      // 成った手か(USI の末尾 +。lib/moveFacts.ts の promotion〈U-4〉と同じ定義)。moveMarksOf は
      // 「成れるのに成らない」しか持たないため、ここだけ USI の末尾を直接読む(新しい判断ではない)。
      oppPrevPromotion = oppMove.endsWith("+");
    }

    const whatif = whatifByPly.get(move.recordPly) ?? null;
    let fork: boolean | null = null;
    let top1Side: WhatifSideRaw | null = null;
    let actualSide: WhatifSideRaw | null = null;
    let lossBand: FeatureLossBand | null = null;
    let inTop5: boolean | null = null;
    let actualCapture: boolean | null = null;
    let actualDrop: boolean | null = null;
    let actualGivesCheck: boolean | null = null;
    let actualSacrifice: boolean | null = null;
    let actualRetreat: boolean | null = null;
    let top1Capture: boolean | null = null;
    let top1Drop: boolean | null = null;
    let top1GivesCheck: boolean | null = null;
    let top1Sacrifice: boolean | null = null;
    let top1Retreat: boolean | null = null;
    if (whatif !== null) {
      fork = whatif.fork;
      top1Side = whatif.top1Side;
      actualSide = whatif.actualSide;
      lossBand = lossBandOf(whatif.lossCpValue, whatif.lossIsLowerBound);
      inTop5 = whatif.actualRank !== null;
      const actualMarks = moveMarksOf(whatif.sfen, whatif.actualMove);
      const top1Marks = moveMarksOf(whatif.sfen, whatif.top1Move);
      actualCapture = actualMarks.capture;
      actualDrop = actualMarks.drop;
      actualGivesCheck = actualMarks.givesCheck;
      actualSacrifice = actualMarks.sacrifice;
      actualRetreat = actualMarks.retreat;
      top1Capture = top1Marks.capture;
      top1Drop = top1Marks.drop;
      top1GivesCheck = top1Marks.givesCheck;
      top1Sacrifice = top1Marks.sacrifice;
      top1Retreat = top1Marks.retreat;
    }

    rows.push({
      kifuId: fixed.id,
      group,
      gameNo,
      kifPly: move.kifPly,
      spentSec: move.sec,
      spentBucket: spentBucketLabelOf(move.sec),
      prevOwnSpentBucket: prevOwn === null ? null : spentBucketLabelOf(prevOwn[0]!.sec),
      prev3SumBucket: prev3 === null ? null : spentBucketLabelOf(sumSecOf(prev3)),
      prev5SumBucket: prev5 === null ? null : spentBucketLabelOf(sumSecOf(prev5)),
      afterLongThink: prevOwn === null ? null : prevOwn[0]!.sec >= TIME_VALUES.longThinkSec,
      remainingBucket: timeLimitSec === undefined ? null : leftBucketLabelOf(timeLimitSec - thisUsedBefore),
      phase: move.phase,
      evalBand,
      evalChangePrev,
      inCheck,
      fork,
      top1Side,
      actualSide,
      lossBand,
      inTop5,
      actualCapture,
      actualDrop,
      actualGivesCheck,
      actualSacrifice,
      actualRetreat,
      top1Capture,
      top1Drop,
      top1GivesCheck,
      top1Sacrifice,
      top1Retreat,
      oppPrevCapture,
      oppPrevDrop,
      oppPrevGivesCheck,
      oppPrevPromotion,
      ownRookMoved,
      oppRookMoved,
      longThink: move.sec >= TIME_VALUES.longThinkSec,
    });
  }
  return rows;
}

/** 記録は本人 = 先手にそろえてある(`lib/failureEvent.ts` の `evaluationOf` と同じ前提。「王手を受けている」= sente が王手中)。 */
function isSenteInCheck(sfen: string): boolean {
  return isInCheck(sfen, "sente");
}
