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

/** 帯([0])が squares の駒を名指ししているプラン(STEP T-8)。 */
function bandPlan(squares: string[]): Partial<ReachablePlanBody> {
  return {
    urgentMessages: squares.map((square) => ({
      kind: "piece_attacked",
      text: `あなたの${square}の駒に、相手の駒が当たっています(次の相手の手で取られる可能性があります)。`,
      square,
      attackerSquares: [],
    })) as unknown as ReachablePlanBody["urgentMessages"],
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

  // --- STEP T-8 で足した "band" ---

  it("候補手・道のりに無く、帯が名指しした駒を動かす手なら band", () => {
    const previous = makeReadyRecord(28, bandPlan(["7i", "9i"]));
    expect(deriveAdviceSource(previous, "7i7h")).toBe("band");
  });

  it("帯が名指ししていない駒を動かす手は none のまま", () => {
    const previous = makeReadyRecord(28, bandPlan(["7i"]));
    expect(deriveAdviceSource(previous, "2g2f")).toBe("none");
  });

  it("打つ手(ドロップ)は band にならない", () => {
    const previous = makeReadyRecord(28, bandPlan(["P*"]));
    expect(deriveAdviceSource(previous, "P*8h")).toBe("none");
  });

  it("帯に square が無い行は名指ししていない扱い(推測しない)", () => {
    const previous = makeReadyRecord(28, {
      urgentMessages: [{ kind: "piece_attacked", text: "当たっています。" }],
    });
    expect(deriveAdviceSource(previous, "7i7h")).toBe("none");
  });

  // 順序の保証: band は candidate/route の後に判定する(I-6 の挙動を変えないため)。
  it("帯の駒を動かす手でも、候補手に載っていれば candidate が優先される", () => {
    const previous = makeReadyRecord(28, {
      ...bandPlan(["7i"]),
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "p",
            move: "7i7h",
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
    expect(deriveAdviceSource(previous, "7i7h")).toBe("candidate");
  });

  it("帯の駒を動かす手でも、道のりに載っていれば route が優先される", () => {
    const previous = makeReadyRecord(28, {
      ...bandPlan(["7i"]),
      candidateMoveLabels: { "7i7h": "本美濃囲い" },
    });
    expect(deriveAdviceSource(previous, "7i7h")).toBe("route");
  });
});
