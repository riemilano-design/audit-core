// STEP T-5(T5-B)。lib/denominators.tsの純粋関数のテスト。

import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { CoachExplanation } from "../../../apps/server/src/analysis/explanationGenerator.js";
import type { RecordLine } from "../invariants/types.js";
import { buildDenominatorReport, countDenominators, type DenominatorInput } from "./denominators.js";

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

function coachOf(status: CoachExplanation["status"]): CoachExplanation[] {
  return [
    {
      id: "runtime_current_shape_x",
      stage: "current_shape",
      purpose: "purpose",
      move: null,
      reason: "reason",
      refers_to_shape_id: null,
      refers_to_intent_id: null,
      confidence_level: "low",
      glossary_terms: [],
      template_id: "template",
      status,
    },
  ];
}

function baseResponse(
  planOverrides: Partial<ReachablePlanBody> = {},
  coach: CoachExplanation[] | undefined = coachOf("none"),
): StateResponseBodyWithPlan {
  return {
    sfen: "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1",
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

function makeRecord(
  ply: number,
  phase: "immediate" | "ready",
  planOverrides: Partial<ReachablePlanBody> = {},
  coach: CoachExplanation[] | undefined = coachOf("none"),
): RecordLine {
  const response = baseResponse(planOverrides, coach);
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

describe("countDenominators", () => {
  it("phase:immediateの行は数えない", () => {
    const records = [makeRecord(2, "immediate")];
    expect(countDenominators(records).totalPlies).toBe(0);
  });

  it("coachがundefinedの行は認識なし(沈黙側)として数える", () => {
    const records = [makeRecord(2, "ready", {}, undefined)];
    const counts = countDenominators(records);
    expect(counts.totalPlies).toBe(1);
    expect(counts.hasRecognition).toBe(0);
    expect(counts.silent).toBe(1);
  });

  it("coachにforming以上のstatusがあれば認識ありと数える", () => {
    const records = [makeRecord(2, "ready", {}, coachOf("forming"))];
    expect(countDenominators(records).hasRecognition).toBe(1);
  });

  it("candidateMoveLabelsが空でなければ道のりありと数える", () => {
    const records = [makeRecord(2, "ready", { candidateMoveLabels: { "7g7f": "７六" } })];
    expect(countDenominators(records).hasRoute).toBe(1);
  });

  it("candidateMoveState:readyかつcandidateMove.status:readyなら候補手ありと数える", () => {
    const records = [
      makeRecord(2, "ready", {
        candidateMoveState: "ready",
        candidateMove: { status: "ready", notReadyReason: null, explanations: [], sharedNotes: [] },
      }),
    ];
    expect(countDenominators(records).hasCandidateMove).toBe(1);
  });

  it("除外理由がexcluded_by_reference_evaluationなら候補手が全件除外と数える", () => {
    const records = [
      makeRecord(2, "ready", {
        candidateMoveState: "ready",
        candidateMove: {
          status: "not_ready",
          notReadyReason: "excluded_by_reference_evaluation",
          explanations: [],
          sharedNotes: [],
        },
      }),
    ];
    const counts = countDenominators(records);
    expect(counts.candidateExcluded).toBe(1);
    expect(counts.hasCandidateMove).toBe(0);
  });

  it("認識・道のり・候補手のいずれも無ければ沈黙と数える", () => {
    const records = [makeRecord(2, "ready", {}, coachOf("none"))];
    const counts = countDenominators(records);
    expect(counts.silent).toBe(1);
  });

  it("認識ありなら沈黙には数えない", () => {
    const records = [makeRecord(2, "ready", {}, coachOf("matched"))];
    expect(countDenominators(records).silent).toBe(0);
  });
});

describe("buildDenominatorReport", () => {
  it("探索の記録が無ければperProfileはundefined", () => {
    const inputs: DenominatorInput[] = [
      { kifuId: "k1", mode: undefined, profile: undefined, records: [makeRecord(2, "ready")] },
    ];
    const report = buildDenominatorReport(inputs);
    expect(report.perInput).toHaveLength(1);
    expect(report.perInput[0]?.label).toBe("k1");
    expect(report.perProfile).toBeUndefined();
  });

  it("探索の記録があればprofileごとの小計をあわせて返す", () => {
    const inputs: DenominatorInput[] = [
      {
        kifuId: "explore-01",
        mode: "explore",
        profile: "S1",
        records: [makeRecord(2, "ready", {}, coachOf("matched"))],
      },
      {
        kifuId: "explore-02",
        mode: "explore",
        profile: "S1",
        records: [makeRecord(4, "ready", {}, coachOf("matched"))],
      },
      {
        kifuId: "explore-03",
        mode: "explore",
        profile: "E",
        records: [makeRecord(2, "ready", {}, undefined)],
      },
    ];
    const report = buildDenominatorReport(inputs);
    expect(report.perInput).toHaveLength(3);
    expect(report.perProfile).toBeDefined();
    const s1 = report.perProfile?.find((r) => r.label === "S1");
    const e = report.perProfile?.find((r) => r.label === "E");
    expect(s1?.counts.totalPlies).toBe(2);
    expect(s1?.counts.hasRecognition).toBe(2);
    expect(e?.counts.totalPlies).toBe(1);
    expect(e?.counts.silent).toBe(1);
  });

  it("profile未指定の探索記録はunknownとして集計する", () => {
    const inputs: DenominatorInput[] = [
      { kifuId: "explore-01", mode: "explore", profile: undefined, records: [makeRecord(2, "ready")] },
    ];
    const report = buildDenominatorReport(inputs);
    expect(report.perProfile?.[0]?.label).toBe("unknown");
  });
});
