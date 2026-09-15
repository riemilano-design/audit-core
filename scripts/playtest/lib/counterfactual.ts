// STEP D2(docs/STEP_D2_PLAN_2026-09-15.md)。Failure Event 1 件ごとに、分岐点の局面(直前の ready 行の sfen)から
// 実戦の続きとエンジンの読み筋(直前の行の searchPvs の focus_baseline)を同じ手数だけ進め、観測できる事実だけを並べる。
//
// 【このファイルがやること】
// - 状態を 8 つに分ける(計画 2.2。判定の順は actualRootMismatch → unrecorded → notMeasurable → noFocusBaseline → emptyPv
//   → rootMismatch → pvUnplayable → compared。最初に当たった 1 つだけ)
// - 2 本を N = min(windowPlies + 1, 実戦, 読み筋) 手で切り、取った駒の駒種ごとの枚数・王手・詰み・詰みでない終局・
//   先手玉の周り・先手玉の逃げ道を数える(計画 2.1・2.3。上限は D1 の actualContinuation の窓と同じ)
// - STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §2): N 手目の後の局面の、両方の玉の区域に利きが届く駒と升の数(positionFactsEnd)と、その差
// - 数の欄だけ「読み筋 − 実戦」の差を取る(計画 2.4)。どちらかが数えられなければ差は null
//
// 【このファイルが絶対にやらないこと】
// - エンジンを回すこと。読み筋の取り直し(読み筋は③の探索で、急落を見つけた engineReference とは別の探索 ― 計画 0.1)
// - 評価語・駒の価値・差の合計(pvMaterials.ts・captureSummary.ts の人間承認済みの制約。計画 0.5)
// - どちらの続きが良いかの判断・死因の推定(計画 7.)
// - 「無い」を 0 や空で埋めること(規則 11.6)
// - 例外を握りつぶすこと(実戦の手順が initialSfen から非合法なら、D1 の actualContinuation と同じく例外になる ― 計画 4. の限界)
//
// 【判断的知識の仮置き(draft)】逃げ道の定義(計画 Q-3。人間には 20 局版の結果と一緒に承認を取る)。窓(windowPlies)は呼び出し側が渡す。

import type { Role } from "shogiops/types";
import { makeSquareName } from "shogiops/util";
import { detectBoardEvents } from "../../../apps/server/src/analysis/boardEventDetector.js";
import { passSfen } from "../../../apps/server/src/analysis/engineReference.js";
import { roleToJapanese } from "../../../apps/server/src/analysis/pieceMapping.js";
import { computePvMaterials, type PvMaterialRules } from "../../../apps/server/src/analysis/pvMaterials.js";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { getGameOutcome, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { getLegalMoves } from "../../../apps/server/src/rules/legalMoves.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import type { RecordLine } from "../invariants/types.js";
import { kingSurroundingsOf, type KingSurroundings } from "./kingSurroundings.js";
import { positionFactsDiff, positionFactsOf, type PositionFacts, type PositionFactsDiff, type PositionFactsRules } from "./positionFacts.js";

/**
 * computePvMaterials に渡す規則。**D2 が読むのは `capturedRoles` だけ**で、ほかの材料の規則は結果に使わないが、
 * 型が必須にしているので 1 か所に固定値を置く(計画 2.3)。
 */
const PV_MATERIAL_RULES: PvMaterialRules = {
  contact: "capture_available",
  kingNeighborhood: "eight_neighbors",
  advance: "rank_delta",
  reach: "sliding_attack_count",
};

/**
 * STEP D2.5 の positionFactsOf に渡す規則(計画 §2。選べる値は今 1 つずつ。lib は既定値を置かないので、使う側がここで選ぶ)。
 * Failure Event の trigger(lib/failureEvent.ts)も同じ値を使い、出どころ(provenance.analysis.rule.positionFacts)にも写す。
 */
export const POSITION_FACTS_RULES: PositionFactsRules = {
  zone: "king_and_eight_neighbors",
  reach: "non_king_pieces",
  control: "squares",
};

/** 駒種ごとの枚数(成駒は元の駒種。0 の駒種は持たない) */
export type RoleCounts = Partial<Record<Role, number>>;

/**
 * 先手玉の逃げ道の数。**定義(draft、計画 Q-3): 局面で手番を先手にし、先手玉を動かす合法手の数(駒を取る手を含む)。**
 * 合法手の玉は相手の利きのあるマスへ行けないので、利きで絞っても値は変わらない(計画 2.3・事前読み A の M-3)。
 */
export type KingEscapes =
  | { state: "counted"; count: number }
  /** 先手玉が盤上に無い */
  | { state: "noKing" }
  /** 後手番で後手玉に王手が掛かっていて、手番を先手にした局面を作れない(計画 2.3・事前読み A の M-2) */
  | { state: "opponentInCheck" };

export interface SequenceFacts {
  /** N 手の中でそれぞれが取った駒(`us` = 根の手番 = 先手) */
  capturedRoles: { us: RoleCounts; opponent: RoleCounts };
  /** 先手の手の後に後手玉が王手を受けた ply / 後手の手の後に先手玉が王手を受けた ply(記録の手数) */
  checks: { byUs: number[]; byOpponent: number[] };
  /** N 手の中で詰みになった ply と勝った側(詰みのときだけ。どちらの勝ちも持つ ― D1 の consequences.mate は後手の勝ちだけ) */
  mate: { ply: number; winner: "sente" | "gote" } | null;
  /** 詰みでない終局の ply と種類 */
  gameEnd: { ply: number; result: string } | null;
  /** N 手目の後の局面の先手玉の周り。先手玉が無ければ null */
  kingSurroundingsEnd: KingSurroundings | null;
  /** STEP D2.5: N 手目の後の局面の、両方の玉の区域に利きが届く駒と升の数(玉が無い側は null) */
  positionFactsEnd: PositionFacts;
  /** N 手目の後の局面の先手玉の逃げ道 */
  kingEscapesEnd: KingEscapes;
}

export interface CounterfactualDiff {
  capturedRoles: { us: RoleCounts; opponent: RoleCounts };
  /** `kingSurroundingsEnd.own` の差。どちらかが null なら null */
  kingSurroundingsOwn: number | null;
  /** STEP D2.5: `positionFactsEnd` の zonePieces・zoneControl の差。玉がどちらかの局面で無い側は null */
  positionFacts: PositionFactsDiff;
  /** `kingEscapesEnd` の差(`count` 同士)。どちらかが数えられなければ null */
  kingEscapes: number | null;
}

export type CounterfactualComparison = {
  state: "compared";
  /** N */
  comparedPlies: number;
  windowPlies: number;
  /** 実戦で根から進めた手数(上限 windowPlies + 1。棋譜の終わりか終局で止まる) */
  actualPlies: number;
  pvLength: number;
  pvUsablePlies: number;
  /** 読み筋を非合法手で打ち切った位置(1 始まり)。最後まで並べられたら null */
  pvTruncatedAtPly: number | null;
  pvBounded: { lowerbound: boolean; upperbound: boolean };
  pvFirstMove: string;
  /** 読み筋の 1 手目が action.bestmoveAtBefore と同じか(別の探索なので食い違いうる ― 計画 0.1) */
  pvFirstMoveIsBestmoveAtBefore: boolean;
  pvFirstMoveIsPlayedMove: boolean;
  /** 根の局面の先手玉の逃げ道(根は先手番なので手番を変えない) */
  kingEscapesRoot: KingEscapes;
  actual: SequenceFacts;
  pv: SequenceFacts;
  /** 読み筋 − 実戦(計画 2.4。向きを名前に書く) */
  pvMinusActual: CounterfactualDiff;
  /** それぞれの `kingEscapesEnd − kingEscapesRoot`。数えられなければ null */
  kingEscapesChangeFromRoot: { actual: number | null; pv: number | null };
};

export type CounterfactualUnavailableState =
  /** 記録の手順を initialSfen から branchPly − 1 手並べた局面が、直前の行の sfen と違う */
  | "actualRootMismatch"
  /** 直前の行に searchPvs の欄が無い(測っていない) */
  | "unrecorded"
  /** searchPvs が null(本番の解析が失敗した = 測れなかった) */
  | "notMeasurable"
  /** focus_baseline の 1 本目が無い */
  | "noFocusBaseline"
  /** focus_baseline の pv が 0 手 */
  | "emptyPv"
  /** 読み筋の sfen が直前の行の sfen と違う */
  | "rootMismatch"
  /** 読み筋の 1 手目が根で非合法 */
  | "pvUnplayable";

export type Counterfactual = CounterfactualComparison | { state: CounterfactualUnavailableState };

/** 盤・手番・持ち駒(SFEN の先頭 3 欄)。手数の欄は比べない。 */
function positionPart(sfen: string): string {
  return sfen.split(" ").slice(0, 3).join(" ");
}

export function kingEscapesOf(sfen: string): KingEscapes {
  const position = parsePosition(sfen);
  const king = position.board.pieces("sente", "king").first();
  if (king === undefined) return { state: "noKing" };
  let senteToMove = sfen;
  if (position.turn === "gote") {
    if (isInCheck(sfen, "gote")) return { state: "opponentInCheck" };
    senteToMove = passSfen(sfen);
  }
  const from = makeSquareName(king);
  // 打つ手は駒の名前の文字から始まるので、移動元の升で始まる手だけが玉を動かす手
  return { state: "counted", count: getLegalMoves(senteToMove).filter((move) => move.startsWith(from)).length };
}

function roleCountsOf(counts: ReadonlyMap<Role, number>): RoleCounts {
  return Object.fromEntries([...counts].sort(([a], [b]) => a.localeCompare(b))) as RoleCounts;
}

/** 根(先手番)から `moves` をすべて並べ、事実を数える。`branchPly` は 1 手目の記録の手数。 */
export function sequenceFacts(rootSfen: string, moves: readonly string[], branchPly: number): SequenceFacts {
  const materials = computePvMaterials(rootSfen, [...moves], PV_MATERIAL_RULES, 0);
  if (materials.kind !== "measured" || materials.usablePlies !== moves.length) {
    throw new Error(`手順を ${moves.length} 手とも並べられない(並べられたのは ${materials.usablePlies} 手)`);
  }
  const checks = { byUs: [] as number[], byOpponent: [] as number[] };
  let mate: SequenceFacts["mate"] = null;
  let gameEnd: SequenceFacts["gameEnd"] = null;
  const noteEnd = (afterSfen: string, ply: number) => {
    const outcome = getGameOutcome(afterSfen);
    if (outcome === undefined) return;
    if (outcome.result === "checkmate") {
      if (outcome.winner === undefined) throw new Error(`詰みなのに勝った側が無い: ${afterSfen}`);
      mate = { ply, winner: outcome.winner };
    } else {
      gameEnd = { ply, result: outcome.result };
    }
  };

  let sfen = rootSfen;
  for (let index = 0; index < moves.length; index += 2) {
    const usMove = moves[index]!;
    const opponentMove = moves[index + 1] ?? null;
    const usPly = branchPly + index;
    for (const event of detectBoardEvents(sfen, usMove, opponentMove)) {
      if (event.kind === "check_given") checks.byUs.push(usPly);
      if (event.kind === "check_received") checks.byOpponent.push(usPly + 1);
    }
    sfen = applyMove(sfen, usMove);
    noteEnd(sfen, usPly);
    if (opponentMove === null) break;
    sfen = applyMove(sfen, opponentMove);
    noteEnd(sfen, usPly + 1);
  }

  return {
    capturedRoles: { us: roleCountsOf(materials.materials.capturedRoles.us), opponent: roleCountsOf(materials.materials.capturedRoles.opponent) },
    checks,
    mate,
    gameEnd,
    kingSurroundingsEnd: kingSurroundingsOf(sfen),
    positionFactsEnd: positionFactsOf(sfen, POSITION_FACTS_RULES),
    kingEscapesEnd: kingEscapesOf(sfen),
  };
}

function roleDiff(pv: RoleCounts, actual: RoleCounts): RoleCounts {
  const roles = [...new Set([...Object.keys(pv), ...Object.keys(actual)])].sort() as Role[];
  const diff: RoleCounts = {};
  for (const role of roles) {
    const value = (pv[role] ?? 0) - (actual[role] ?? 0);
    if (value !== 0) diff[role] = value;
  }
  return diff;
}

function escapesDiff(minuend: KingEscapes, subtrahend: KingEscapes): number | null {
  return minuend.state === "counted" && subtrahend.state === "counted" ? minuend.count - subtrahend.count : null;
}

export interface CounterfactualInput {
  /** 直前の ready 行(fromReadyPly)。`sfen` が根 */
  record: Pick<RecordLine, "sfen" | "searchPvs">;
  /** 記録の全手順(initialSfen から) */
  moves: readonly string[];
  /** 分岐点の手の記録の手数 */
  branchPly: number;
  windowPlies: number;
  initialSfen: string;
  /** action.bestmoveAtBefore */
  bestmoveAtBefore: string | null;
}

export function counterfactualOf(input: CounterfactualInput): Counterfactual {
  const { record, moves, branchPly, windowPlies, initialSfen } = input;

  // 1. 実戦の根の照合(記録そのものの食い違いなので先に見る。計画 2.2・事前読み A の N-5)
  let replayed = initialSfen;
  for (let index = 0; index < branchPly - 1; index++) replayed = applyMove(replayed, moves[index]!);
  if (positionPart(replayed) !== positionPart(record.sfen)) return { state: "actualRootMismatch" };

  // 2. 読み筋の有無
  if (record.searchPvs === undefined) return { state: "unrecorded" };
  if (record.searchPvs === null) return { state: "notMeasurable" };
  const observation = record.searchPvs.find((pv) => pv.source === "focus_baseline" && pv.multipv === 1);
  if (observation === undefined) return { state: "noFocusBaseline" };
  if (observation.pv.length === 0) return { state: "emptyPv" };
  if (positionPart(observation.sfen) !== positionPart(record.sfen)) return { state: "rootMismatch" };

  const rootSfen = record.sfen;
  const pvReplay = computePvMaterials(rootSfen, observation.pv, PV_MATERIAL_RULES, 0);
  if (pvReplay.usablePlies === 0) return { state: "pvUnplayable" };

  // 3. 実戦で根から進められる手数(上限 windowPlies + 1。終局で止まる)
  const limit = windowPlies + 1;
  let actualPlies = 0;
  let sfen = rootSfen;
  while (actualPlies < limit) {
    const move = moves[branchPly - 1 + actualPlies];
    if (move === undefined) break;
    sfen = applyMove(sfen, move);
    actualPlies += 1;
    if (getGameOutcome(sfen) !== undefined) break;
  }

  const comparedPlies = Math.min(limit, actualPlies, pvReplay.usablePlies);
  const actual = sequenceFacts(rootSfen, moves.slice(branchPly - 1, branchPly - 1 + comparedPlies), branchPly);
  const pv = sequenceFacts(rootSfen, observation.pv.slice(0, comparedPlies), branchPly);
  const kingEscapesRoot = kingEscapesOf(rootSfen);
  const pvFirstMove = observation.pv[0]!;

  return {
    state: "compared",
    comparedPlies,
    windowPlies,
    actualPlies,
    pvLength: observation.pv.length,
    pvUsablePlies: pvReplay.usablePlies,
    pvTruncatedAtPly: pvReplay.kind === "measured" ? pvReplay.truncatedAtPly : null,
    pvBounded: { lowerbound: observation.lowerbound, upperbound: observation.upperbound },
    pvFirstMove,
    pvFirstMoveIsBestmoveAtBefore: pvFirstMove === input.bestmoveAtBefore,
    pvFirstMoveIsPlayedMove: pvFirstMove === moves[branchPly - 1],
    kingEscapesRoot,
    actual,
    pv,
    pvMinusActual: {
      capturedRoles: {
        us: roleDiff(pv.capturedRoles.us, actual.capturedRoles.us),
        opponent: roleDiff(pv.capturedRoles.opponent, actual.capturedRoles.opponent),
      },
      kingSurroundingsOwn:
        pv.kingSurroundingsEnd !== null && actual.kingSurroundingsEnd !== null ? pv.kingSurroundingsEnd.own - actual.kingSurroundingsEnd.own : null,
      positionFacts: positionFactsDiff(pv.positionFactsEnd, actual.positionFactsEnd),
      kingEscapes: escapesDiff(pv.kingEscapesEnd, actual.kingEscapesEnd),
    },
    kingEscapesChangeFromRoot: {
      actual: escapesDiff(actual.kingEscapesEnd, kingEscapesRoot),
      pv: escapesDiff(pv.kingEscapesEnd, kingEscapesRoot),
    },
  };
}

// ---- Markdown(計画 2.5。事実の並びだけ。評価語を使わない)----

const ROLE_ORDER: Role[] = ["king", "rook", "bishop", "gold", "silver", "knight", "lance", "pawn"];

function rolesText(counts: RoleCounts): string {
  const roles = [...ROLE_ORDER.filter((role) => role in counts), ...(Object.keys(counts) as Role[]).filter((role) => !ROLE_ORDER.includes(role))];
  return roles.map((role) => `${roleToJapanese(role) ?? role} ${counts[role]}`).join("・") || "なし";
}

function pliesText(plies: readonly number[]): string {
  return plies.length === 0 ? "なし" : plies.map((ply) => `${ply} 手目`).join("・");
}

function escapesText(escapes: KingEscapes): string {
  switch (escapes.state) {
    case "counted":
      return String(escapes.count);
    case "noKing":
      return "数えられない(先手玉が無い)";
    case "opponentInCheck":
      return "数えられない(後手玉に王手が掛かっている局面)";
  }
}

function factsText(facts: SequenceFacts): string {
  const mate = facts.mate === null ? "なし" : `${facts.mate.ply} 手目(${facts.mate.winner === "sente" ? "先手" : "後手"}の勝ち)`;
  const gameEnd = facts.gameEnd === null ? "" : `、詰みでない終局 ${facts.gameEnd.ply} 手目(${facts.gameEnd.result})`;
  const surroundings =
    facts.kingSurroundingsEnd === null ? "数えられない(先手玉が無い)" : `${facts.kingSurroundingsEnd.own} / ${facts.kingSurroundingsEnd.squares} マス`;
  return [
    `先手が取った駒 ${rolesText(facts.capturedRoles.us)} / 後手が取った駒 ${rolesText(facts.capturedRoles.opponent)}`,
    `先手の手による王手 ${pliesText(facts.checks.byUs)}`,
    `後手の手による王手 ${pliesText(facts.checks.byOpponent)}`,
    `詰み ${mate}${gameEnd}`,
    `先手玉の周りの味方 ${surroundings}`,
    `先手玉の逃げ道 ${escapesText(facts.kingEscapesEnd)}`,
  ].join("、");
}

const UNAVAILABLE_LABELS: Record<CounterfactualUnavailableState, string> = {
  actualRootMismatch: "実戦の手順を開始局面から並べた局面が、直前の行の局面と違う(比べない)",
  unrecorded: "記録に読み筋が無い(測っていない)",
  notMeasurable: "読み筋が null(測れなかった)",
  noFocusBaseline: "③の現局面の読み筋が無い",
  emptyPv: "読み筋が 0 手",
  rootMismatch: "読み筋の局面が直前の行の局面と違う(比べない)",
  pvUnplayable: "読み筋の 1 手目が直前の行の局面で指せない(比べない)",
};

/** Event 1 件の行。`compared` なら 2 行(実戦の続き・読み筋)、それ以外は状態の 1 行。 */
export function counterfactualLines(kifuId: string, branchPly: number, counterfactual: Counterfactual): string[] {
  const head = `- ${kifuId} 分岐点 ${branchPly}`;
  if (counterfactual.state !== "compared") return [`${head} 読み筋: ${UNAVAILABLE_LABELS[counterfactual.state]}`];
  const { comparedPlies, windowPlies } = counterfactual;
  const plies =
    comparedPlies === windowPlies + 1
      ? `${comparedPlies} 手 = 分岐の手 + ${windowPlies} 手`
      : `${comparedPlies} 手。上限は ${windowPlies + 1} 手 = 分岐の手 + ${windowPlies} 手`;
  const bounded = [counterfactual.pvBounded.lowerbound ? "lowerbound" : null, counterfactual.pvBounded.upperbound ? "upperbound" : null].filter(Boolean);
  const boundedText = bounded.length === 0 ? "標識なし" : `標識 ${bounded.join("・")}`;
  const firstMove = `1 手目は直前の bestmove と${counterfactual.pvFirstMoveIsBestmoveAtBefore ? "同じ" : "違う"}`;
  return [
    `${head} 実戦の続き(${plies}): ${factsText(counterfactual.actual)}`,
    `${head} 読み筋(③の探索・${plies}・${boundedText}・${firstMove}): ${factsText(counterfactual.pv)}`,
  ];
}
