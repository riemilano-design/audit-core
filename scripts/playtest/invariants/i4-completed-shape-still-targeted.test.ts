import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, ReferenceShapeBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i4CompletedShapeStillTargeted } from "./i4-completed-shape-still-targeted.js";
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

function referenceShape(shapeId: string, status: ReferenceShapeBody["status"]): ReferenceShapeBody {
  return {
    shapeId,
    name: shapeId,
    pendingReviewNote: null,
    characteristics: "",
    status,
    matchedSquareLabels: [],
    missingSquareLabels: [],
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

function makeRecord(ply: number, planOverrides: Partial<ReachablePlanBody>): RecordLine {
  const response = baseResponse(planOverrides);
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

describe("I-4 completed shape still targeted", () => {
  // data/shapes: mino_honmino(root) <- mino_takamino <- mino_ginkanmuri

  it("発火する: 目標形(本美濃)が、既に完成している形(高美濃)の祖先になっている", () => {
    const record = makeRecord(20, {
      resolvedTargetShapeId: "mino_honmino",
      referenceShapes: [referenceShape("mino_takamino", "completed")],
    });

    const findings = i4CompletedShapeStillTargeted.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("mino_honmino<-mino_takamino");
  });

  it("発火する: 同じrunの以前のready行でcompletedになった形(履歴)についても検出する", () => {
    const earlier = makeRecord(14, {
      resolvedTargetShapeId: "mino_takamino",
      referenceShapes: [referenceShape("mino_ginkanmuri", "completed")],
    });
    const later = makeRecord(16, {
      resolvedTargetShapeId: "mino_honmino",
      referenceShapes: [],
    });

    const findings = i4CompletedShapeStillTargeted.check([earlier, later]);

    // earlier行自体はmino_takamino(target)がmino_ginkanmuriの祖先なので発火、
    // later行はmino_honminoがmino_ginkanmuri(履歴)の祖先なので発火。
    expect(findings).toHaveLength(2);
    expect(findings.map((f) => f.ply)).toEqual([14, 16]);
  });

  it("発火しない: 目標形が完成形の子(通常の進行)の場合", () => {
    const record = makeRecord(20, {
      resolvedTargetShapeId: "mino_takamino",
      referenceShapes: [referenceShape("mino_honmino", "completed")],
    });

    expect(i4CompletedShapeStillTargeted.check([record])).toEqual([]);
  });

  it("発火しない: 目標形が未選択(null)の場合", () => {
    const record = makeRecord(20, {
      resolvedTargetShapeId: null,
      referenceShapes: [referenceShape("mino_honmino", "completed")],
    });

    expect(i4CompletedShapeStillTargeted.check([record])).toEqual([]);
  });
});
