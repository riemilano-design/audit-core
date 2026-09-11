import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { EngineReference } from "../lib/engineReference.js";
import { I7_DROP_THRESHOLD_CP, i7UrgentButOtherTalk } from "./i7-urgent-but-other-talk.js";
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

function makeEngineReference(overrides: Partial<EngineReference> = {}): EngineReference {
  return {
    baseline: { scoreCp: -324, mate: null, bestmove: "6i7h" },
    afterPass: { scoreCp: 1410, mate: null, bestmove: "7f7g", captureSquare: "7g" },
    dropCp: 1086,
    nodes: 4_000_000,
    ...overrides,
  };
}

function makeRecord(
  ply: number,
  sfen: string,
  isEnd: boolean,
  planOverrides: Partial<ReachablePlanBody> = {},
  engineReference: EngineReference | null = makeEngineReference(),
): RecordLine {
  const response = baseResponse(sfen, isEnd, planOverrides);
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: "4h3h",
    goteMove: "5d7f",
    phase: "ready",
    elapsedMs: 0,
    response,
    engineReference,
  };
}

const SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 16";

describe("I-7 urgent but other talk", () => {
  it("発火する(urgent_empty): urgentMessagesが空", () => {
    const record = makeRecord(16, SFEN, false, { urgentMessages: [] });

    const findings = i7UrgentButOtherTalk.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("urgent_empty");
    expect(findings[0]?.detail).toContain("[0] が空です。");
    expect(findings[0]?.detail).toContain("1086cp");
    expect(findings[0]?.detail).toContain("7f7g");
    expect(findings[0]?.detail).toContain("7g");
  });

  it("発火する(route_shown): lastMoveOutcome.messagesにroute_advancedがある", () => {
    const record = makeRecord(16, SFEN, false, {
      urgentMessages: [{ kind: "piece_attacked", text: "桂に相手の駒の利きが届いています。" }],
      lastMoveOutcome: {
        playedMoveLabel: "４八玉",
        opponentMoveLabel: "５四馬",
        messages: [{ kind: "route_advanced", text: "玉を２八へ運ぶ道のりが、残り2手から残り1手になりました。" }],
      },
    });

    const findings = i7UrgentButOtherTalk.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("route_shown");
    expect(findings[0]?.detail).toContain("route_advanced");
  });

  it("発火しない: dropCpが閾値未満", () => {
    const record = makeRecord(16, SFEN, false, { urgentMessages: [] }, makeEngineReference({ dropCp: I7_DROP_THRESHOLD_CP - 1 }));

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });

  it("発火しない: afterPass.captureSquareがnull(相手の最善が捕獲を含まない)", () => {
    const record = makeRecord(
      16,
      SFEN,
      false,
      { urgentMessages: [] },
      makeEngineReference({ afterPass: { scoreCp: 1410, mate: null, bestmove: "3c3d", captureSquare: null } }),
    );

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });

  it("発火しない: engineReferenceがnull(測っていない)", () => {
    const record = makeRecord(16, SFEN, false, { urgentMessages: [] }, null);

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });

  it("発火しない: 終局", () => {
    const record = makeRecord(16, SFEN, true, { urgentMessages: [] });

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });

  it("発火しない: urgentMessagesが非空かつroute_shownの条件にも該当しない", () => {
    const record = makeRecord(16, SFEN, false, {
      urgentMessages: [{ kind: "piece_attacked", text: "桂に相手の駒の利きが届いています。" }],
    });

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });
});
