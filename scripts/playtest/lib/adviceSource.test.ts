// STEP T-6(B-2)のテスト。docs/STEP_T-6_PLAN_2026-09-11.md 2. B-2に従う。

import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { deriveAdviceSource } from "./adviceSource.js";
import type { RecordLine } from "../invariants/types.js";

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

function baseResponse(planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

function makeReadyRecord(ply: number, planOverrides: Partial<ReachablePlanBody>): RecordLine {
  const response = baseResponse(planOverrides);
  return {
    kind: "record",
    ply,
    sfen: response.sfen,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

describe("deriveAdviceSource", () => {
  it("直前行が無ければ none", () => {
    expect(deriveAdviceSource(undefined, "7g7f")).toBe("none");
  });

  it("直前行の候補手(status: ready)にsenteMoveが含まれていれば candidate", () => {
    const previous = makeReadyRecord(14, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "p",
            move: "7g7f",
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
    });

    expect(deriveAdviceSource(previous, "7g7f")).toBe("candidate");
  });

  it("候補手にsenteMoveが含まれず、道のり(candidateMoveLabels)に含まれていれば route", () => {
    const previous = makeReadyRecord(14, {
      candidateMoveState: "ready",
      candidateMove: { status: "not_ready", notReadyReason: "excluded_by_reference_evaluation", explanations: [], sharedNotes: [] },
      candidateMoveLabels: { "6g6f": "四間飛車" },
    });

    expect(deriveAdviceSource(previous, "6g6f")).toBe("route");
  });

  it("候補手・道のりのどちらにも含まれなければ none", () => {
    const previous = makeReadyRecord(14, {
      candidateMoveState: "ready",
      candidateMove: { status: "not_ready", notReadyReason: "excluded_by_reference_evaluation", explanations: [], sharedNotes: [] },
      candidateMoveLabels: { "6g6f": "四間飛車" },
    });

    expect(deriveAdviceSource(previous, "2g2f")).toBe("none");
  });

  it("候補手のstatusがreadyでも、explanationsにsenteMoveが無ければ candidateMoveLabelsを見る", () => {
    const previous = makeReadyRecord(14, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "p",
            move: "7g7f",
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
      candidateMoveLabels: { "6g6f": "四間飛車" },
    });

    expect(deriveAdviceSource(previous, "6g6f")).toBe("route");
  });
});
