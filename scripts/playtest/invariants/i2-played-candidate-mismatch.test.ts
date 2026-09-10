import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i2PlayedCandidateMismatch } from "./i2-played-candidate-mismatch.js";
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

function makeRecord(ply: number, senteMove: string | null, planOverrides: Partial<ReachablePlanBody>): RecordLine {
  const response = baseResponse(planOverrides);
  return {
    kind: "record",
    ply,
    sfen: response.sfen,
    senteMove,
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

describe("I-2 played candidate mismatch", () => {
  it("発火する: played_candidateが出ているが、直前行で候補手として表示していなかった", () => {
    const previous = makeRecord(14, null, {
      candidateMoveState: "ready",
      candidateMove: { status: "not_ready", notReadyReason: "excluded_by_reference_evaluation", explanations: [], sharedNotes: [] },
    });
    const current = makeRecord(16, "4h3i", {
      lastMoveOutcome: {
        playedMoveLabel: "３九玉",
        opponentMoveLabel: null,
        messages: [{ kind: "played_candidate", text: "この手は、直前に表示していた候補手の一つです。" }],
      } as ReachablePlanBody["lastMoveOutcome"],
    });

    const findings = i2PlayedCandidateMismatch.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.ply).toBe(16);
    expect(findings[0]?.condition).toBe("played_candidate:not_ready");
  });

  it("発火しない: 直前行で実際にその手を候補手として表示していた", () => {
    const previous = makeRecord(14, null, {
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "p",
            move: "4h3i",
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
    const current = makeRecord(16, "4h3i", {
      lastMoveOutcome: {
        playedMoveLabel: "３九玉",
        opponentMoveLabel: null,
        messages: [{ kind: "played_candidate", text: "この手は、直前に表示していた候補手の一つです。" }],
      } as ReachablePlanBody["lastMoveOutcome"],
    });

    expect(i2PlayedCandidateMismatch.check([previous, current])).toEqual([]);
  });
});
