// STEP TIME-CAUSE(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)。時間負けの要因を、機械で測れる候補
// (C1〜C10)に分解する段の純粋関数。**測る段だけ**(CLI は scripts/playtest/timeCause.ts、PDF は
// report-pdf/render_time_cause.py)。
//
// 【このファイルがやること】
// - 固定棋譜(`*.fixed.json`)の `moveSeconds`・whatif-v2 の position 行(`ply`・`scenes.fork`・
//   `candidates[0].side`・`actualSide`)・patient の局の対応(`gameNo`↔`kifuId`・`timeUpLoss`)から、
//   局ごとに C1〜C9 を数える(`buildGameTimeCause`)。
// - 「時期」は既存の `phaseOf`(局の総手数の 1/3・2/3)をそのまま使う。**新しい閾値は置かない**
//   (`TIME_VALUES`・`spentBucketIndexOf`・`phaseOf`・`sideBucketOf` を import して使うだけ)。
// - 本人の手は `lib/reportData.ts` の `ownParityOf`・`sideOf`・`plyOffsetOf`・`originalMovesOf`・
//   `moveSecondsOf` をそのまま呼ぶ(自前で定義し直さない)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンを起動すること(CLI の役目)
// - 将棋の判断・戦法の名前を付けること(C9 は「飛車が初期の筋に居るか」という盤上の事実の印だけを返す)
// - 新しい判定的知識(閾値)を置くこと

import type { MoveTime } from "./kifuImport.js";
import { originalMovesOf, ownParityOf, phaseOf, plyOffsetOf, sideOf, spentBucketIndexOf, TIME_VALUES, type FixedKifu, moveSecondsOf } from "./reportData.js";
import { sideBucketOf, type WhatifSideRaw } from "./type.js";

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { parseSquareName } from "shogiops/util";

export class TimeCauseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TimeCauseError";
  }
}

type Side = "先手" | "後手";
type Phase = "early" | "mid" | "late";

// ---- 入力の形 ----

/**
 * 固定棋譜 JSON(`*.fixed.json`)から、この段が使う分だけ。`lib/reportData.ts` の `FixedKifu` を土台にし、
 * `plyOffset`(mirrored な局が持つ、元の手数との差)だけ足す(実装担当の判断: `sideOf`・`plyOffsetOf` は
 * 本来 records の meta 行の形〈`Pick<MetaLine, "mirrored"|"plyOffset">`〉を受け取る関数だが、固定棋譜
 * JSON 自身も `mirrored`・`plyOffset` の欄を同じ意味で持つため〈`lib/sideAlignment.ts` の
 * `alignedFixedKifu`〉、そのまま渡せる。`reportData.ts` の `FixedKifu` 型は変えていない)。
 */
export interface TimeCauseFixedKifu extends FixedKifu {
  plyOffset?: number;
}

/** whatif-v2 の position 行から、この段が使う分だけ。`ply` は本人の手の recordPly(kifPly − plyOffset)と同じ数え方。 */
export interface TimeCauseWhatifPositionInput {
  ply: number;
  fork: boolean;
  top1Side: WhatifSideRaw;
  actualSide: WhatifSideRaw;
}

// ---- C1〜C9(局ごと) ----

export interface TimeCausePhaseTriple {
  early: number;
  mid: number;
  late: number;
}

export interface TimeCauseMidThinkCell {
  count: number;
  sec: number;
}

export interface TimeCauseMidThinkByPhase {
  early: TimeCauseMidThinkCell;
  mid: TimeCauseMidThinkCell;
  late: TimeCauseMidThinkCell;
}

export interface TimeCauseFraction {
  numerator: number;
  denominator: number;
}

export interface TimeCauseRookMark {
  /** 本人の飛車が初期の筋(先手 2 筋・後手 8 筋)に居るか。 */
  own: boolean;
  /** 相手の飛車が初期の筋に居るか。 */
  opponent: boolean;
}

export interface TimeCauseMidMoveSecond {
  /** KIF の手数(「◯手目」の◯と同じ)。 */
  kifPly: number;
  sec: number;
  /** whatif-v2 が無い組では null。 */
  fork: boolean | null;
}

export interface GameTimeCause {
  gameNo: number;
  kifuId: string;
  group: string;
  timeLimitSec: number;
  timeUpLoss: boolean;
  total: number;
  /** C1(early)・C2(mid)・late の消費秒(本人の手だけの合計)。 */
  phaseSpentSec: TimeCausePhaseTriple;
  /** C3: 時期ごとの長考(TIME_VALUES.longThinkSec 以上)の回数。 */
  longThinkCountByPhase: TimeCausePhaseTriple;
  longThinkTotal: number;
  /** C4: 最長の 1 手。本人の手の秒が 1 つも無ければ null(起きないはずだが念のため)。 */
  longestMove: { sec: number; kifPly: number } | null;
  /** C5: 本人の連続する 2 手(間に他の手が挟まらない)がともに長考だった回数。 */
  longThinkStreakCount: number;
  /** C6: 時期ごとの中考(4 超〜9 秒。TIME_VALUES.spentBucketsSec の段 2)の回数と合計秒。 */
  midThinkByPhase: TimeCauseMidThinkByPhase;
  midThinkTotal: TimeCauseMidThinkCell;
  /**
   * C7: 長考の手のうち、whatif-v2 の position 行と結合できたものの中で分かれ道(`scenes.fork`)に当たる数 /
   * 結合できた長考の総数。whatif-v2 がこの組に無ければ null(結合できない手 ― 長考が startPly より前にある等 ―
   * は分母に数えない。`lib/directAnswers.ts` の join と同じ考え方)。
   */
  forkAmongLongThink: TimeCauseFraction | null;
  /**
   * C8: 「長考かつ分かれ道」のうち、側が逆(`sideBucketOf` が `top1AttackActualDefense`/
   * `top1DefenseActualAttack`。「両方」「なし」は逆に数えない)だった数 / 「長考かつ分かれ道」の総数。
   * whatif-v2 が無ければ null。
   */
  oppositeSideAmongForkLongThink: TimeCauseFraction | null;
  /** C9: 序盤の終わり(phaseOf が mid になる最初の本人の手の直前の局面)での飛車の筋の印。その手が無ければ null。 */
  rookMark: TimeCauseRookMark | null;
  /** C10 の材料: 終局時の残り秒(timeLimitSec − 最後に読めた本人の手の累積消費)。本人の手の秒が 1 つも無ければ null。 */
  remainingSec: number | null;
  /** 付録 4 の帯用。中盤(phaseOf が mid)の本人の手の秒の列。 */
  midMoveSeconds: TimeCauseMidMoveSecond[];
}

interface OwnMoveTime {
  kifPly: number;
  sec: number;
  totalSec: number;
  recordPly: number;
  phase: Phase;
}

function ownMoveTimesOf(side: Side, plyOffset: number, total: number, seconds: readonly (MoveTime | null)[]): OwnMoveTime[] {
  const parity = ownParityOf(side);
  const out: OwnMoveTime[] = [];
  for (let kifPly = parity === 1 ? 1 : 2; kifPly <= seconds.length; kifPly += 2) {
    const time = seconds[kifPly - 1];
    if (time === null || time === undefined) continue;
    const recordPly = kifPly - plyOffset;
    out.push({ kifPly, sec: time.spentSec, totalSec: time.totalSec, recordPly, phase: phaseOf(recordPly, total) });
  }
  return out;
}

function isOppositeSide(top1Side: WhatifSideRaw, actualSide: WhatifSideRaw): boolean {
  const bucket = sideBucketOf(top1Side, actualSide);
  return bucket === "top1AttackActualDefense" || bucket === "top1DefenseActualAttack";
}

const BOARD_RANKS = "abcdefghi";
/** 先手 2 筋・後手 8 筋(初期の飛車の筋)。将棋の判断ではなく、初期配置の事実。 */
const ROOK_INITIAL_FILE: Record<Side, number> = { 先手: 2, 後手: 8 };

/** `sfen` の局面で、`side` の飛車(未成・成りとも rook/dragon)が初期の筋に 1 枚でも居るか。 */
export function rookOnInitialFileOf(sfen: string, side: Side): boolean {
  const board = parsePosition(sfen).board;
  const color = side === "先手" ? "sente" : "gote";
  const file = ROOK_INITIAL_FILE[side];
  for (let rank = 0; rank < BOARD_RANKS.length; rank++) {
    const square = parseSquareName(`${file}${BOARD_RANKS[rank]}`);
    if (square === undefined) continue;
    const piece = board.get(square);
    if (piece?.color === color && (piece.role === "rook" || piece.role === "dragon")) return true;
  }
  return false;
}

/**
 * 本人が指した向き(`originalMoves`・`DEFAULT_INITIAL_SFEN`)で `kifPly` 手目の直前の局面を作る
 * (`lib/reportData.ts` の `buildPatientEvents` の `sfensBefore` と同じ道具〈`applyMove`〉の使い方。
 * `lib/finalPosition.ts` は mirrored な局を「本人 = 先手」にそろえた向きへ進めるため、絶対筋
 * 〈先手 2 筋・後手 8 筋〉を見る C9 にはそのままでは使えない ― 実装担当の判断)。
 */
export function sfenBeforeOriginalKifPly(originalMoves: readonly string[], kifPly: number): string {
  let sfen = DEFAULT_INITIAL_SFEN;
  for (let i = 0; i < kifPly - 1; i++) sfen = applyMove(sfen, originalMoves[i]!);
  return sfen;
}

/** 局ごとに C1〜C9・remainingSec・midMoveSeconds を組む(計画「作るもの」1.)。 */
export function buildGameTimeCause(
  fixed: TimeCauseFixedKifu,
  gameNo: number,
  group: string,
  timeLimitSec: number,
  timeUpLoss: boolean,
  whatifPositions: readonly TimeCauseWhatifPositionInput[] | null,
): GameTimeCause {
  const side = sideOf(fixed);
  const plyOffset = plyOffsetOf(fixed);
  const originalMoves = originalMovesOf(fixed);
  const total = originalMoves.length;
  const seconds = moveSecondsOf(fixed);
  if (seconds === null) throw new TimeCauseError(`${fixed.id} に moveSeconds が無い(この道具は秒の読めた固定棋譜だけを扱う)`);

  const own = ownMoveTimesOf(side, plyOffset, total, seconds);

  const phaseSpentSec: TimeCausePhaseTriple = { early: 0, mid: 0, late: 0 };
  const longThinkCountByPhase: TimeCausePhaseTriple = { early: 0, mid: 0, late: 0 };
  const midThinkByPhase: TimeCauseMidThinkByPhase = { early: { count: 0, sec: 0 }, mid: { count: 0, sec: 0 }, late: { count: 0, sec: 0 } };
  let longestMove: { sec: number; kifPly: number } | null = null;
  for (const move of own) {
    phaseSpentSec[move.phase] += move.sec;
    if (move.sec >= TIME_VALUES.longThinkSec) longThinkCountByPhase[move.phase] += 1;
    if (spentBucketIndexOf(move.sec) === 2) {
      midThinkByPhase[move.phase].count += 1;
      midThinkByPhase[move.phase].sec += move.sec;
    }
    if (longestMove === null || move.sec > longestMove.sec) longestMove = { sec: move.sec, kifPly: move.kifPly };
  }
  const longThinkTotal = longThinkCountByPhase.early + longThinkCountByPhase.mid + longThinkCountByPhase.late;
  const midThinkTotal: TimeCauseMidThinkCell = {
    count: midThinkByPhase.early.count + midThinkByPhase.mid.count + midThinkByPhase.late.count,
    sec: midThinkByPhase.early.sec + midThinkByPhase.mid.sec + midThinkByPhase.late.sec,
  };

  let longThinkStreakCount = 0;
  for (let i = 0; i + 1 < own.length; i++) {
    const a = own[i]!;
    const b = own[i + 1]!;
    if (b.kifPly - a.kifPly !== 2) continue; // 間に(秒の読めない)手が挟まり、真に連続する本人の 2 手ではない
    if (a.sec >= TIME_VALUES.longThinkSec && b.sec >= TIME_VALUES.longThinkSec) longThinkStreakCount += 1;
  }

  const whatifByPly = new Map<number, TimeCauseWhatifPositionInput>();
  if (whatifPositions !== null) for (const position of whatifPositions) whatifByPly.set(position.ply, position);

  let forkAmongLongThink: TimeCauseFraction | null = null;
  let oppositeSideAmongForkLongThink: TimeCauseFraction | null = null;
  if (whatifPositions !== null) {
    const longThinkMoves = own.filter((m) => m.sec >= TIME_VALUES.longThinkSec);
    const matched = longThinkMoves.map((m) => whatifByPly.get(m.recordPly)).filter((p): p is TimeCauseWhatifPositionInput => p !== undefined);
    const forkMatched = matched.filter((p) => p.fork);
    const opposite = forkMatched.filter((p) => isOppositeSide(p.top1Side, p.actualSide));
    forkAmongLongThink = { numerator: forkMatched.length, denominator: matched.length };
    oppositeSideAmongForkLongThink = { numerator: opposite.length, denominator: forkMatched.length };
  }

  const midMoveSeconds: TimeCauseMidMoveSecond[] = own
    .filter((m) => m.phase === "mid")
    .map((m) => ({ kifPly: m.kifPly, sec: m.sec, fork: whatifPositions === null ? null : (whatifByPly.get(m.recordPly)?.fork ?? null) }));

  const firstMid = own.find((m) => m.phase === "mid");
  let rookMark: TimeCauseRookMark | null = null;
  if (firstMid !== undefined) {
    const sfen = sfenBeforeOriginalKifPly(originalMoves, firstMid.kifPly);
    const opponentSide: Side = side === "先手" ? "後手" : "先手";
    rookMark = { own: rookOnInitialFileOf(sfen, side), opponent: rookOnInitialFileOf(sfen, opponentSide) };
  }

  const lastOwn = own[own.length - 1];
  const remainingSec = lastOwn === undefined ? null : timeLimitSec - lastOwn.totalSec;

  return {
    gameNo,
    kifuId: fixed.id,
    group,
    timeLimitSec,
    timeUpLoss,
    total,
    phaseSpentSec,
    longThinkCountByPhase,
    longThinkTotal,
    longestMove,
    longThinkStreakCount,
    midThinkByPhase,
    midThinkTotal,
    forkAmongLongThink,
    oppositeSideAmongForkLongThink,
    rookMark,
    remainingSec,
    midMoveSeconds,
  };
}

// ---- 組ごとの集計(計画「出すもの」) ----

/** 中央値(件数が偶数なら中央 2 件の平均)。空配列は null(`lib/reportData.ts` の私有の `medianOf` と同じ算法だが、
 * このファイルは `reportData.ts` を変えずに済むよう自分で持つ)。 */
export function medianOf(values: readonly number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1]! + sorted[mid]!) / 2 : sorted[mid]!;
}

export interface TimeCauseSubgroupSummary {
  games: number;
  /** C1 */
  medianEarlySec: number | null;
  /** C2 */
  medianMidSec: number | null;
  medianLateSec: number | null;
  /** C3 */
  medianLongThinkTotal: number | null;
  /** C4 */
  medianLongestMoveSec: number | null;
  /** C5 */
  medianStreakCount: number | null;
  /** C6 */
  medianMidThinkCount: number | null;
  medianMidThinkSec: number | null;
  /** C7 */
  forkFraction: TimeCauseFraction | null;
  /** C8 */
  oppositeSideFraction: TimeCauseFraction | null;
}

function sumFractions(fractions: ReadonlyArray<TimeCauseFraction | null>): TimeCauseFraction | null {
  const present = fractions.filter((f): f is TimeCauseFraction => f !== null);
  if (present.length === 0) return null;
  return { numerator: present.reduce((sum, f) => sum + f.numerator, 0), denominator: present.reduce((sum, f) => sum + f.denominator, 0) };
}

export function subgroupSummaryOf(games: readonly GameTimeCause[]): TimeCauseSubgroupSummary {
  return {
    games: games.length,
    medianEarlySec: medianOf(games.map((g) => g.phaseSpentSec.early)),
    medianMidSec: medianOf(games.map((g) => g.phaseSpentSec.mid)),
    medianLateSec: medianOf(games.map((g) => g.phaseSpentSec.late)),
    medianLongThinkTotal: medianOf(games.map((g) => g.longThinkTotal)),
    medianLongestMoveSec: medianOf(games.filter((g) => g.longestMove !== null).map((g) => g.longestMove!.sec)),
    medianStreakCount: medianOf(games.map((g) => g.longThinkStreakCount)),
    medianMidThinkCount: medianOf(games.map((g) => g.midThinkTotal.count)),
    medianMidThinkSec: medianOf(games.map((g) => g.midThinkTotal.sec)),
    forkFraction: sumFractions(games.map((g) => g.forkAmongLongThink)),
    oppositeSideFraction: sumFractions(games.map((g) => g.oppositeSideAmongForkLongThink)),
  };
}

export interface TimeCauseRookBreakdownCell {
  own: boolean;
  opponent: boolean;
  games: number;
  medianEarlySec: number | null;
  medianMidSec: number | null;
}

/** C9: own×opponent の 2×2(実装担当の判断: 順は own=true→false、その中で opponent=true→false)。 */
const ROOK_CELLS: ReadonlyArray<{ own: boolean; opponent: boolean }> = [
  { own: true, opponent: true },
  { own: true, opponent: false },
  { own: false, opponent: true },
  { own: false, opponent: false },
];

function rookMarkBreakdownOf(games: readonly GameTimeCause[]): TimeCauseRookBreakdownCell[] {
  return ROOK_CELLS.map((cell) => {
    const cellGames = games.filter((g) => g.rookMark !== null && g.rookMark.own === cell.own && g.rookMark.opponent === cell.opponent);
    return {
      ...cell,
      games: cellGames.length,
      medianEarlySec: medianOf(cellGames.map((g) => g.phaseSpentSec.early)),
      medianMidSec: medianOf(cellGames.map((g) => g.phaseSpentSec.mid)),
    };
  });
}

export interface TimeCauseC10Row {
  gameNo: number;
  earlySec: number;
  midSec: number;
  remainingSec: number | null;
}

export interface GroupTimeCause {
  group: string;
  timeLimitSec: number;
  games: number;
  timeUpLoss: TimeCauseSubgroupSummary;
  other: TimeCauseSubgroupSummary;
  /** C9: 2×2(own×opponent)ごとの局数・序/中の消費の中央値。 */
  rookMarkBreakdown: TimeCauseRookBreakdownCell[];
  /** C10: 局ごとの (early, mid, 終局時の残り秒)。相関の値は出さない(並べるだけ)。 */
  c10Table: TimeCauseC10Row[];
}

export function buildGroupTimeCause(group: string, timeLimitSec: number, games: readonly GameTimeCause[]): GroupTimeCause {
  const timeUpLossGames = games.filter((g) => g.timeUpLoss);
  const otherGames = games.filter((g) => !g.timeUpLoss);
  return {
    group,
    timeLimitSec,
    games: games.length,
    timeUpLoss: subgroupSummaryOf(timeUpLossGames),
    other: subgroupSummaryOf(otherGames),
    rookMarkBreakdown: rookMarkBreakdownOf(games),
    c10Table: games.map((g) => ({ gameNo: g.gameNo, earlySec: g.phaseSpentSec.early, midSec: g.phaseSpentSec.mid, remainingSec: g.remainingSec })),
  };
}

// ---- ファイル全体 ----

export interface TimeCauseFile {
  games: GameTimeCause[];
  groups: GroupTimeCause[];
}

/** `games`(組をまたいだ全局)から、`group`(+ `timeLimitSec`)ごとにまとめて `time_cause.json` の中身を組む。 */
export function buildTimeCauseFile(games: readonly GameTimeCause[]): TimeCauseFile {
  const order: string[] = [];
  const byGroup = new Map<string, { timeLimitSec: number; games: GameTimeCause[] }>();
  for (const game of games) {
    let entry = byGroup.get(game.group);
    if (entry === undefined) {
      entry = { timeLimitSec: game.timeLimitSec, games: [] };
      byGroup.set(game.group, entry);
      order.push(game.group);
    }
    entry.games.push(game);
  }
  const groups = order.map((group) => {
    const entry = byGroup.get(group)!;
    return buildGroupTimeCause(group, entry.timeLimitSec, entry.games);
  });
  return { games: [...games], groups };
}
