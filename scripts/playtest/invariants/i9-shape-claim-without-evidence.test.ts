// I-9(盤との不一致、draft)のテスト。docs/PHASES.md「Unit 6 の再定義と決定」H-5。
// 局面・指し手の作り方は apps/server/src/analysis/shapeFormationAnalyzer.test.ts の
// 本美濃囲い(mino_honmino)の例に合わせる(6i5hだけを指すと、4i金の偶然の一致に
// 5h金の証拠1件が加わり、2h・3hの2件が欠けたままになる)。

import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import type {
  ReachablePlanBody,
  StateResponseBodyWithPlan,
  TargetShapeProgress,
} from "../../../apps/server/src/api/stateResponse.js";
import { i9ShapeClaimWithoutEvidence } from "./i9-shape-claim-without-evidence.js";
import type { RecordLine } from "./types.js";

function baseTargetShapeProgress(overrides: Partial<TargetShapeProgress> = {}): TargetShapeProgress {
  return {
    shapeId: "mino_honmino",
    name: "本美濃囲い",
    description: "",
    matchedSquareLabels: [],
    matchedSquares: [],
    matchedPieceLabels: [],
    missingSquareLabels: [],
    missingSquares: [],
    pendingReviewNote: null,
    ...overrides,
  };
}

function basePlan(overrides: Partial<ReachablePlanBody> = {}): ReachablePlanBody {
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
    ...overrides,
  };
}

function makeRecord(
  ply: number,
  sfen: string,
  moveHistory: string[],
  planOverrides: Partial<ReachablePlanBody>,
  phase: "immediate" | "ready" = "ready",
): RecordLine {
  const response: StateResponseBodyWithPlan = {
    sfen,
    moveHistory,
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: basePlan(planOverrides),
  };
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: null,
    goteMove: null,
    phase,
    elapsedMs: 0,
    response,
  };
}

describe("I-9 shape claim without evidence", () => {
  it("発火する: 6i5hだけを指した局面(証拠1件・欠け2件)", () => {
    const moveHistory = ["6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const record = makeRecord(2, finalSfen, moveHistory, {
      targetShapeProgress: baseTargetShapeProgress({
        missingSquares: ["2h", "3h"],
      }),
    });

    const findings = i9ShapeClaimWithoutEvidence.check([record]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.ply).toBe(2);
    expect(findings[0]?.condition).toBe("forming");
    expect(findings[0]?.detail).toContain("本美濃囲い");
    expect(findings[0]?.detail).toContain("1 件(5h)");
    expect(findings[0]?.detail).toContain("2 件(2h, 3h)");
  });

  it("発火しない: targetShapeProgressがnull(④に組み上がりが出ていない)", () => {
    const record = makeRecord(2, DEFAULT_INITIAL_SFEN, [], { targetShapeProgress: null });

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });

  it("発火しない: 証拠が2件(3i3h・6i5h)ある場合(欠けも1件になり両方の条件を満たさない)", () => {
    const moveHistory = ["3i3h", "3c3d", "6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const record = makeRecord(4, finalSfen, moveHistory, {
      targetShapeProgress: baseTargetShapeProgress({ missingSquares: ["2h"] }),
    });

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });

  it("発火しない: 欠けが1件しかない(閾値未満)", () => {
    const moveHistory = ["6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const record = makeRecord(2, finalSfen, moveHistory, {
      targetShapeProgress: baseTargetShapeProgress({ missingSquares: ["2h"] }),
    });

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });

  it("発火しない: readyでない行(immediate)", () => {
    const moveHistory = ["6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const record = makeRecord(
      2,
      finalSfen,
      moveHistory,
      { targetShapeProgress: baseTargetShapeProgress({ missingSquares: ["2h", "3h"] }) },
      "immediate",
    );

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });

  it("発火しない: shapeIdが結果に無い(存在しない形を指す)", () => {
    const record = makeRecord(2, DEFAULT_INITIAL_SFEN, [], {
      targetShapeProgress: baseTargetShapeProgress({
        shapeId: "no_such_shape",
        missingSquares: ["2h", "3h"],
      }),
    });

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });

  it("発火しない: sfenとmoveHistoryの組み合わせが矛盾している(analyzeShapeFormationが例外)", () => {
    const record = makeRecord(2, DEFAULT_INITIAL_SFEN, ["7g7f"], {
      targetShapeProgress: baseTargetShapeProgress({ missingSquares: ["2h", "3h"] }),
    });

    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
  });
});

// ---- STEP D0-SIDE 段 2(R-7): 開始局面は check.ts が文脈で渡す ----
// 開始局面 FOLD_START は、平手・後手番の初期局面に 3c3d を当てた局面(計画 F-S8。手で導いた値)。後手の歩の位置だけが平手と違う。
const FOLD_START = "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 2";

describe("I-9 と開始局面(STEP D0-SIDE 段 2 の R-7)", () => {
  const moveHistory = ["6i5h"];
  const { finalSfen } = replayMoveHistory(moveHistory, FOLD_START);
  const record = makeRecord(2, finalSfen, moveHistory, {
    targetShapeProgress: baseTargetShapeProgress({ missingSquares: ["2h", "3h"] }),
  });

  it("文脈で開始局面を渡すと、平手の固定例と同じ所見が出る(証拠 1 件・欠け 2 件)", () => {
    const findings = i9ShapeClaimWithoutEvidence.check([record], { initialSfen: FOLD_START });
    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("forming");
    expect(findings[0]?.detail).toContain("1 件(5h)");
    expect(findings[0]?.detail).toContain("2 件(2h, 3h)");
  });

  it("文脈が無い・平手を渡すと、局面と履歴の食い違いで例外になり、所見が黙って消える(渡し忘れの形)", () => {
    expect(i9ShapeClaimWithoutEvidence.check([record])).toEqual([]);
    expect(i9ShapeClaimWithoutEvidence.check([record], { initialSfen: DEFAULT_INITIAL_SFEN })).toEqual([]);
  });
});
