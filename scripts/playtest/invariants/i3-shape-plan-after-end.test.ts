import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i3ShapePlanAfterEnd } from "./i3-shape-plan-after-end.js";
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

function baseResponse(isEnd: boolean, planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
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
  phase: "immediate" | "ready",
  isEnd: boolean,
  planOverrides: Partial<ReachablePlanBody> = {},
): RecordLine {
  const response = baseResponse(isEnd, planOverrides);
  return {
    kind: "record",
    ply,
    sfen: response.sfen,
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase,
    elapsedMs: 0,
    response,
  };
}

describe("I-3 shape/plan after end", () => {
  it("発火する: 終局後(ready)にroutesが残っている", () => {
    const record = makeRecord(20, "ready", true, {
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

    const findings = i3ShapePlanAfterEnd.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("routes");
  });

  it("発火する: 終局後(immediate)にresolvedTargetShapeIdが残っている(I-3はimmediateも検査対象)", () => {
    const record = makeRecord(20, "immediate", true, { resolvedTargetShapeId: "mino_honmino" });

    const findings = i3ShapePlanAfterEnd.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("resolvedTargetShapeId");
    expect(findings[0]?.phase).toBe("immediate");
  });

  it("発火しない: 終局前(isEnd:false)は対象外", () => {
    const record = makeRecord(10, "ready", false, {
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

    expect(i3ShapePlanAfterEnd.check([record])).toEqual([]);
  });

  it("発火しない: 終局後、すべてnull/空である", () => {
    const record = makeRecord(20, "ready", true, {});

    expect(i3ShapePlanAfterEnd.check([record])).toEqual([]);
  });
});
