import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i5AttackedWithoutUrgent } from "./i5-attacked-without-urgent.js";
import type { RecordLine } from "./types.js";

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

function baseResponse(sfen: string, isEnd: boolean, planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

function makeRecord(
  ply: number,
  sfen: string,
  isEnd: boolean,
  planOverrides: Partial<ReachablePlanBody> = {},
): RecordLine {
  const response = baseResponse(sfen, isEnd, planOverrides);
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

// STEP 4-3のテスト(apps/server/src/rules/attackedPieces.test.ts)で使われている実戦局面。
// 金８七から銀７七・歩９七・角８八の3件に利きが届いているが、detectPieceThreatsの
// 対象駒種フィルタ(B-1: 飛・角・金・銀・桂・香のみ、歩は対象外)により歩は除かれ、
// 角・銀の2件がfactsになる(実測で確認済み)。並び順はdetectPieceThreatsに委ね、
// ここでは新しい規則を作らない。
const ATTACKED_SFEN = "ln1gk1snl/1r5b1/p2p1p1pp/1pps2p2/4p4/5PP2/PgS1PGNPP/1B1R2SK1/LN3G2L b 3p 31";
const INITIAL_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

describe("I-5 attacked without urgent", () => {
  it("発火する: 駒が当たっているのに urgentMessages に piece_attacked が無い", () => {
    const record = makeRecord(30, ATTACKED_SFEN, false, { urgentMessages: [] });

    const findings = i5AttackedWithoutUrgent.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("角銀");
  });

  it("発火しない: urgentMessages に piece_attacked がある", () => {
    const record = makeRecord(30, ATTACKED_SFEN, false, {
      urgentMessages: [{ kind: "piece_attacked", text: "角・銀に相手の駒の利きが届いています。" }],
    });

    expect(i5AttackedWithoutUrgent.check([record])).toEqual([]);
  });

  it("発火しない: 当たっている駒が無い(初期局面)", () => {
    const record = makeRecord(0, INITIAL_SFEN, false, { urgentMessages: [] });

    expect(i5AttackedWithoutUrgent.check([record])).toEqual([]);
  });
});
