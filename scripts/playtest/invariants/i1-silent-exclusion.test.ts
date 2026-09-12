import { describe, expect, it } from "vitest";
import type { StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { ReachablePlanBody } from "../../../apps/server/src/api/stateResponse.js";
import { i1SilentExclusion } from "./i1-silent-exclusion.js";
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
    // STEP 5-F(A-3): ③の背景解析の状態。この土台は③について何も言わないため
    // "pending"(まだ計算していない)を既定にする。
    focusTextState: "pending",
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

function baseResponse(planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

function makeRecord(ply: number, planOverrides: Partial<ReachablePlanBody>, isEnd = false): RecordLine {
  const response = baseResponse(planOverrides);
  response.status = { isEnd, outcome: undefined };
  return {
    kind: "record",
    ply,
    sfen: response.sfen,
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

describe("I-1 silent exclusion", () => {
  it("発火する: 候補手が全件除外されているのに、道のりが残っている", () => {
    const record = makeRecord(16, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "not_ready",
        notReadyReason: "excluded_by_reference_evaluation",
        explanations: [],
        sharedNotes: [],
      },
      routes: [
        {
          targetSquare: "2h",
          targetPiece: "玉",
          targetSquareLabel: "２八",
          routeLabel: "３九→２八",
          remainingSteps: 1,
          hasPlayableFirstMove: true,
          blockingSquareLabel: null,
          blockingPieceName: null,
          blockingSquareHasLegalMove: null,
        },
      ],
    });

    const findings = i1SilentExclusion.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("excluded_by_reference_evaluation");
    expect(findings[0]?.ply).toBe(16);
  });

  it("発火する: routesが空でも、除外を伝えるメッセージ(candidate_moves_excluded)が無ければ発火する(STEP 5-1 C-1)", () => {
    const record = makeRecord(16, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "not_ready",
        notReadyReason: "excluded_by_reference_evaluation",
        explanations: [],
        sharedNotes: [],
      },
      routes: [],
      nextConsiderations: [],
    });

    const findings = i1SilentExclusion.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("excluded_by_reference_evaluation");
  });

  it("発火しない: 除外を伝えるメッセージがあり、routesも空なら発火しない(STEP 5-1 C-1)", () => {
    const record = makeRecord(16, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "not_ready",
        notReadyReason: "excluded_by_reference_evaluation",
        explanations: [],
        sharedNotes: [],
      },
      routes: [],
      nextConsiderations: [{ kind: "candidate_moves_excluded", text: "候補手は、指した後の局面を確かめた結果、今は表示していません。" }],
    });

    expect(i1SilentExclusion.check([record])).toEqual([]);
  });

  it("発火しない: 候補手がreadyのとき", () => {
    const record = makeRecord(14, {
      candidateMoveState: "ready",
      candidateMove: { status: "ready", notReadyReason: null, explanations: [], sharedNotes: [] },
      routes: [
        {
          targetSquare: "2h",
          targetPiece: "玉",
          targetSquareLabel: "２八",
          routeLabel: "３九→２八",
          remainingSteps: 1,
          hasPlayableFirstMove: true,
          blockingSquareLabel: null,
          blockingPieceName: null,
          blockingSquareHasLegalMove: null,
        },
      ],
    });

    expect(i1SilentExclusion.check([record])).toEqual([]);
  });
});
