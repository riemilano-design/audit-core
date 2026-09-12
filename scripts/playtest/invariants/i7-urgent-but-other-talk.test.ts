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

function baseResponse(sfen: string, isEnd: boolean, planOverrides: Partial<ReachablePlanBody> = {}): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
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

// apps/server/src/rules/attackedPieces.test.ts と同じ実戦局面(A局30手目・８七金の
// 直後)。7gの銀・9gの歩・8hの角に金8gの利きが届いている(2026-09-11 STEP T-7b:
// 緊急事態の対象駒種を[0]と同じ集合に狭めたため、captureSquareが実際に攻撃されて
// いる駒でなければfactsに現れず発火しない。以前は初期局面のSFENに歩しか無い7gを
// captureSquareに使っていたが、[0]の対象駒種フィルタ導入後は発火しなくなるため、
// 対象駒種(銀)が実際に当たっている局面へ差し替えた)。
const SFEN = "ln1gk1snl/1r5b1/p2p1p1pp/1pps2p2/4p4/5PP2/PgS1PGNPP/1B1R2SK1/LN3G2L b 3p 31";

// apps/server/src/rules/attackedPieces.test.ts と同じ実戦局面(C局30手目・３六歩打の
// 直後)。3gの桂に歩3fの利きが届いている。
const KNIGHT_ATTACKED_SFEN = "lnsgk2nl/4r2b1/pp1p2gpp/2p2s3/4p1P2/2PP1pp2/PP1SPPNPP/1B1RG1SK1/LN3G2L b - 31";

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

  it("発火しない: captureSquareの駒が[0]の対象駒種でない(歩)", () => {
    // SFENの9gは歩(9g・8gの金から利きが届いている)であり、[0]の対象駒種
    // (飛・角・金・銀・桂・香)に含まれないため、緊急事態そのものが成立しない。
    const record = makeRecord(
      16,
      SFEN,
      false,
      { urgentMessages: [] },
      makeEngineReference({ afterPass: { scoreCp: 1410, mate: null, bestmove: "8g9g", captureSquare: "9g" } }),
    );

    expect(i7UrgentButOtherTalk.check([record])).toEqual([]);
  });

  it("発火する: captureSquareの駒が[0]の対象駒種(桂)", () => {
    // KNIGHT_ATTACKED_SFENの3gは桂であり、歩3fから利きが届いている
    // ([0]の対象駒種に含まれるため緊急事態が成立する)。
    const record = makeRecord(
      31,
      KNIGHT_ATTACKED_SFEN,
      false,
      { urgentMessages: [] },
      makeEngineReference({ afterPass: { scoreCp: 1410, mate: null, bestmove: "3f3g", captureSquare: "3g" } }),
    );

    const findings = i7UrgentButOtherTalk.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("urgent_empty");
  });
});
