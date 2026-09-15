// STEP D1(docs/STEP_D1_PLAN_2026-09-14.md 5.1)。**試験専用**の記録の組み立て。本番・CLI からは使わない。
//
// 実際の指し手に、合成の評価(engineReference)を植える。**評価の急落と、窓の中の王手・詰みの両方を
// 持つ実記録は手元に 1 本も無い**(計画 1.1)ため、死因①の規則を端から端まで通す確認にはこれが要る。
// ②③(coach)は本番の explainPositionWithStatus で作る(エンジン不要。T-1 と同じ)。

import type { EngineReference } from "../../../apps/server/src/analysis/engineReference.js";
import { explainPositionWithStatus, type CoachExplanation } from "../../../apps/server/src/analysis/explanationGenerator.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import type { RecordLine } from "../invariants/types.js";

/**
 * 探索モード `explore-2026-09-10T23-01-21-685Z/game-01`(`37174b9`)の実際の指し手 56 手。
 * **後手の勝ちの詰みで終わる**(56 手目)。後手の手の後に先手が王手中になるのは ply 34・36・38・40・52・54・56
 * (本番の isInCheck / getGameOutcome を当てて確かめた。計画 1.1)。
 */
export const GAME01_MOVES: readonly string[] = [
  "2g2f", "1c1d", "7g7f", "8c8d", "7i7h", "3c3d", "7h7g", "4a3b", "2f2e", "3b3c",
  "3g3f", "8d8e", "3i3h", "7a6b", "5i4h", "7c7d", "4h3g", "8a7c", "2h1h", "7c6e",
  "3g2h", "6e5g", "6i5h", "5g4i+", "5h4h", "4i4h", "2i3g", "G*7h", "1g1f", "7h8i",
  "2h2g", "8i8h", "2g2h", "4h3h", "2h2g", "3h3g", "2g3g", "B*5i", "3g4f", "2b1c",
  "N*2d", "5i7g+", "1h2h", "2c2d", "3f3e", "8h9i", "2h5h", "G*2f", "5h5c+", "6b5c",
  "1f1e", "S*3g", "4f5g", "R*5i", "P*5h", "L*5d",
];

export function engineRef(
  scoreCp: number | null,
  options: {
    mate?: number | null;
    bestmove?: string | null;
    afterPassScoreCp?: number | null;
    afterPassMate?: number | null;
    /** STEP D1b(計画 E-9・G-11): afterPass の最善手。既定は null(本番の記録は文字列を持つことが多い) */
    afterPassBestmove?: string | null;
    dropCp?: number | null;
  } = {},
): EngineReference {
  return {
    baseline: { scoreCp, mate: options.mate ?? null, bestmove: options.bestmove ?? null },
    afterPass: { scoreCp: options.afterPassScoreCp ?? null, mate: options.afterPassMate ?? null, bestmove: options.afterPassBestmove ?? null, captureSquare: null },
    dropCp: options.dropCp ?? null,
    nodes: 4_000_000,
  };
}

interface BaseRow {
  ply: number;
  sfen: string;
  moveHistory: string[];
  coach: CoachExplanation[];
}

const baseRowsCache = new Map<string, BaseRow[]>();

/** ply 0, 2, 4, … の ready 行の土台(局面と②③)。同じ手順は 1 回だけ組み立てる。 */
export function baseRowsOf(moves: readonly string[], initialSfen: string = DEFAULT_INITIAL_SFEN): BaseRow[] {
  const key = `${initialSfen}|${moves.join(" ")}`;
  const cached = baseRowsCache.get(key);
  if (cached) return cached;
  const rows: BaseRow[] = [];
  for (let ply = 0; ply <= moves.length; ply += 2) {
    const moveHistory = moves.slice(0, ply);
    const { finalSfen } = replayMoveHistory(moveHistory, initialSfen);
    rows.push({ ply, sfen: finalSfen, moveHistory, coach: explainPositionWithStatus(finalSfen, moveHistory, { initialSfen }) });
  }
  baseRowsCache.set(key, rows);
  return rows;
}

/** 植える評価。`"absent"` は欄そのものを置かない(「測っていない」)。 */
export type PlantedEvaluation = EngineReference | null | "absent";
/** 植える③。`"absent"` は `focusTextState` の欄を置かない(「記録していない」)。 */
export type PlantedFocus = Pick<ReachablePlanBody, "focusTextState" | "focusText"> | "absent";

function basePlan(focus: PlantedFocus): ReachablePlanBody {
  const plan = {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
    candidateMove: undefined,
    pendingReviewNote: null,
    resolvedTargetShapeId: null,
    shapeWeakness: null,
    urgentMessages: [],
    referenceShapes: [],
    directionNote: null,
    planChanged: false,
    planChangeReason: null,
    ...(focus === "absent" ? {} : focus),
  };
  return plan as ReachablePlanBody;
}

/**
 * 実際の手順の ready 行に、評価と③を植えた記録を作る。
 * `initialSfen` は開始局面(STEP D0-SIDE 段 2。回して畳んだ記録の固定例を作るため。既定は平手)。
 * `plant` の既定: 指定の無い行は、終局・先手が王手中なら null(本番の measureEngineReference と同じ)、それ以外は 0。
 */
export function plantedRecords(
  moves: readonly string[],
  plant: Record<number, PlantedEvaluation>,
  focus: Record<number, PlantedFocus> = {},
  initialSfen: string = DEFAULT_INITIAL_SFEN,
): RecordLine[] {
  return baseRowsOf(moves, initialSfen).map((row) => {
    const planted: PlantedEvaluation =
      row.ply in plant ? plant[row.ply]! : isGameOver(row.sfen) || isInCheck(row.sfen, "sente") ? null : engineRef(0);
    const response: StateResponseBodyWithPlan = {
      sfen: row.sfen,
      moveHistory: row.moveHistory,
      status: { isEnd: isGameOver(row.sfen), outcome: undefined },
      coach: row.coach,
      legalMoves: [],
      escapeSquareThreats: [],
      moveHistoryJapanese: [],
      plan: basePlan(row.ply in focus ? focus[row.ply]! : { focusTextState: "ready", focusText: null }),
    };
    const record: RecordLine = {
      kind: "record",
      ply: row.ply,
      sfen: row.sfen,
      senteMove: row.ply > 0 ? moves[row.ply - 2]! : null,
      goteMove: row.ply > 0 ? moves[row.ply - 1]! : null,
      phase: "ready",
      elapsedMs: 0,
      response,
    };
    if (planted !== "absent") record.engineReference = planted;
    return record;
  });
}

/**
 * STEP JSON V0.3-META。回して畳んだ記録の固定例(D0-SIDE 段 2 の R-5 と同じ手順): 平手・後手番の初期局面に 3c3d を当てた開始局面から 6 手。
 * `plantedRecords(FOLD_MOVES, { 0: engineRef(500), 2: engineRef(-500) }, {}, FOLD_START)` で分岐点 1 に Failure Event が出る(lib/failureEvent.test.ts の R-5)。
 * lib/failureEvent.test.ts ほか 5 か所にある手書きの写しは、この STEP では置き換えない(計画 F-11・7.1)。
 */
export const FOLD_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";
export const FOLD_MOVES: readonly string[] = ["7g7f", "4c4d", "5i6h", "9c9d", "6h7g", "4d4e"];
