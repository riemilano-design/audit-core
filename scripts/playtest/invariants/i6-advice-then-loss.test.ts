// I-6(結果、draft)のテスト。docs/STEP_T-6_PLAN_2026-09-11.md 2. B-3
// 「発火する/発火しない(取り返す手がある)/発火しない(adviceSource none)/
// 成りの手でも移動先が正しく取れる、の4件以上」に従う。
// sfen・手はdetectBoardEventsが実際に動く合法な局面を使う(境目付きの
// apps/server/src/analysis/boardEventDetector.test.ts「2.」と同じ局面・手)。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i6AdviceThenLoss } from "./i6-advice-then-loss.js";
import type { RecordLine } from "./types.js";

/** boardEventDetector.test.tsと同じ組み立て方(両玉を置いたうえで指定した駒を並べる)。 */
function buildSfen(
  pieces: Array<{ square: string; color: Color; role: Role }>,
  kings: { sente: string; gote: string } = { sente: "9i", gote: "1a" },
): string {
  let board = Board.empty();
  const place = (square: string, color: Color, role: Role): void => {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  };
  place(kings.sente, "sente", "king");
  place(kings.gote, "gote", "king");
  for (const { square, color, role } of pieces) place(square, color, role);

  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

/** captured_by_opponentを起こす局面(boardEventDetector.test.ts「2.」と同じ)。
 * 先手が9i8i(無関係な手)を指し、後手が5d5eで5eの先手歩を取る。 */
function buildCaptureSfen(): string {
  return buildSfen([
    { square: "5e", color: "sente", role: "pawn" },
    { square: "5d", color: "gote", role: "pawn" },
  ]);
}

function basePlan(): ReachablePlanBody {
  return {
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
  };
}

function baseResponse(
  sfen: string,
  legalMoves: string[],
  planOverrides: Partial<ReachablePlanBody>,
): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves,
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

/** 直前のready行(ply t-2)。senteMove/goteMoveはこの時点ではまだ無い(null)。 */
function makePreviousRecord(ply: number, sfen: string, planOverrides: Partial<ReachablePlanBody>): RecordLine {
  const response = baseResponse(sfen, [], planOverrides);
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

/** 対象のready行(ply t)。senteMove/goteMoveが指された後の行。 */
function makeCurrentRecord(
  ply: number,
  sfen: string,
  senteMove: string,
  goteMove: string,
  legalMoves: string[],
): RecordLine {
  const response = baseResponse(sfen, legalMoves, {});
  return {
    kind: "record",
    ply,
    sfen,
    senteMove,
    goteMove,
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

/** 直前行の候補手(status: ready)にmoveが含まれるプラン(adviceSource: candidate)。 */
function candidateReadyPlan(move: string): Partial<ReachablePlanBody> {
  return {
    candidateMoveState: "ready",
    candidateMove: {
      status: "ready",
      notReadyReason: null,
      explanations: [
        {
          id: "e1",
          stage: "candidate_move",
          purpose: "p",
          move,
          reason: "r",
          refers_to_shape_id: null,
          refers_to_intent_id: null,
          confidence_level: "low",
          glossary_terms: [],
          template_id: "t",
        },
      ],
      sharedNotes: [],
    },
  };
}

describe("I-6 advice then loss", () => {
  it("発火する: 候補手と一致する手を指した直後に取られ、取り返す手が合法手に無い", () => {
    const sfen = buildCaptureSfen();
    const previous = makePreviousRecord(14, sfen, candidateReadyPlan("9i8i"));
    const current = makeCurrentRecord(16, sfen, "9i8i", "5d5e", ["1a2a"]);

    const findings = i6AdviceThenLoss.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.ply).toBe(16);
    expect(findings[0]?.condition).toBe("candidate");
    expect(findings[0]?.detail).not.toContain("従った");
  });

  it("発火しない: 取り返す手が合法手にある", () => {
    const sfen = buildCaptureSfen();
    const previous = makePreviousRecord(14, sfen, candidateReadyPlan("9i8i"));
    const current = makeCurrentRecord(16, sfen, "9i8i", "5d5e", ["6f5e"]);

    expect(i6AdviceThenLoss.check([previous, current])).toEqual([]);
  });

  it("発火しない: adviceSourceがnone(直前の候補手・道のりのどちらとも一致しない)", () => {
    const sfen = buildCaptureSfen();
    const previous = makePreviousRecord(14, sfen, candidateReadyPlan("2g2f"));
    const current = makeCurrentRecord(16, sfen, "9i8i", "5d5e", ["1a2a"]);

    expect(i6AdviceThenLoss.check([previous, current])).toEqual([]);
  });

  it("成りの手でも移動先が正しく取れる(取り返す手が成りの手でも検出しない)", () => {
    const sfen = buildCaptureSfen();
    const previous = makePreviousRecord(14, sfen, candidateReadyPlan("9i8i"));
    const current = makeCurrentRecord(16, sfen, "9i8i", "5d5e", ["5b5e+"]);

    expect(i6AdviceThenLoss.check([previous, current])).toEqual([]);
  });

  it("発火しない: 直前のready行(t-2)が無い", () => {
    const sfen = buildCaptureSfen();
    const current = makeCurrentRecord(2, sfen, "9i8i", "5d5e", ["1a2a"]);

    expect(i6AdviceThenLoss.check([current])).toEqual([]);
  });
});
