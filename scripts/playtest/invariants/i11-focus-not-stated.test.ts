// I-11(沈黙、draft)のテスト。docs/STEP_5-F_PLAN_2026-09-12.md 14.5 の 1 に従う。
//
// 3段階(緊急事態 / (A)でない / ③が名指していない)それぞれについて、
// **発火する・発火しない**の両方を確かめる。判定ロジックを写経せず、
// 記録の形だけを作って i11FocusNotStated.check() に渡す。
//
// 閾値は本番(DROP_THRESHOLD_CP)を import する。このテストが数値を持たないのは
// I-11 本体と同じ理由である(本番の閾値を変えたときにテストだけ古い値で残らない)。

import { describe, expect, it } from "vitest";
import { DROP_THRESHOLD_CP } from "../../../apps/server/src/analysis/pieceThreatFocusExplanation.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { EngineReference } from "../lib/engineReference.js";
import { i11FocusNotStated } from "./i11-focus-not-stated.js";
import type { RecordLine } from "./types.js";

const SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** 8h = ８八。本番の文言と同じ表記(toJapaneseSquare)になる。 */
const CAPTURE_SQUARE = "8h";
const CAPTURE_SQUARE_JA = "８八";

function basePlan(): ReachablePlanBody {
  return {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
    focusTextState: "ready",
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

function engineReference(overrides: Partial<EngineReference> = {}): EngineReference {
  return {
    nodes: 1000,
    baseline: { scoreCp: 0, mate: null, bestmove: "2g2f" },
    afterPass: { scoreCp: -DROP_THRESHOLD_CP, mate: null, bestmove: "2b8h+", captureSquare: CAPTURE_SQUARE },
    dropCp: DROP_THRESHOLD_CP,
    ...overrides,
  };
}

/** 帯([0])の「当たり」1件。squareは実体(PieceThreatMessage)には載るが応答の型には無い。 */
function bandMessage(square: string): { kind: string; text: string } {
  return { kind: "piece_attacked", text: `あなたの駒に当たっています。`, square } as {
    kind: string;
    text: string;
  };
}

function record(
  planOverrides: Partial<ReachablePlanBody>,
  referenceOverrides: Partial<EngineReference> | null = {},
): RecordLine {
  const response: StateResponseBodyWithPlan = {
    sfen: SFEN,
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
  return {
    kind: "record",
    ply: 16,
    sfen: SFEN,
    senteMove: "2g2f",
    goteMove: "8c8d",
    phase: "ready",
    elapsedMs: 0,
    response,
    engineReference: referenceOverrides === null ? null : engineReference(referenceOverrides),
  };
}

describe("I-11 ③が急ぐ駒を名指していない", () => {
  // --- 3段階目: ③が名指しているか ---
  it("発火する: 緊急事態なのに③に文が無い(帯は0件)", () => {
    const findings = i11FocusNotStated.check([record({ focusText: null })]);
    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("focus_absent");
    expect(findings[0]?.ply).toBe(16);
  });

  it("発火する: ③に文はあるが、別のマスを述べている", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: "このまま何もしないと、あなたの７七の桂が取られる可能性があります。" }),
    ]);
    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("focus_other_square");
  });

  it("発火しない: ③がそのマスを名指している", () => {
    const findings = i11FocusNotStated.check([
      record({
        focusText: `このまま何もしないと、あなたの${CAPTURE_SQUARE_JA}の角が取られる可能性があります。`,
      }),
    ]);
    expect(findings).toEqual([]);
  });

  // --- 2段階目: (A)の除外 ---
  it("発火しない: (A) 帯がちょうど1件で、そのマスがcaptureSquareと同じ(本番が③を黙ると決めた局面)", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null, urgentMessages: [bandMessage(CAPTURE_SQUARE)] }),
    ]);
    expect(findings).toEqual([]);
  });

  it("発火する: 帯が1件でも、マスが違えば(A)ではない", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null, urgentMessages: [bandMessage("7g")] }),
    ]);
    expect(findings).toHaveLength(1);
  });

  it("発火する: 帯が2件なら(A)ではない(同じマスを含んでいても)", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null, urgentMessages: [bandMessage(CAPTURE_SQUARE), bandMessage("7g")] }),
    ]);
    expect(findings).toHaveLength(1);
  });

  it("発火する: 帯のsquareが欠けている古い世代の記録では(A)を確かめられないので除外しない", () => {
    const withoutSquare = { kind: "piece_attacked", text: "あなたの駒に当たっています。" };
    const findings = i11FocusNotStated.check([
      record({ focusText: null, urgentMessages: [withoutSquare] }),
    ]);
    expect(findings).toHaveLength(1);
    expect(findings[0]?.detail).toContain("マス情報が欠けている");
  });

  // --- 1段階目: 緊急事態か ---
  it("発火しない: engineReferenceがnull(測っていない)", () => {
    expect(i11FocusNotStated.check([record({ focusText: null }, null)])).toEqual([]);
  });

  it("発火しない: dropCpが閾値未満", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null }, { dropCp: DROP_THRESHOLD_CP - 1 }),
    ]);
    expect(findings).toEqual([]);
  });

  it("発火する: dropCpがちょうど閾値(境目は採用側)", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null }, { dropCp: DROP_THRESHOLD_CP }),
    ]);
    expect(findings).toHaveLength(1);
  });

  it("発火しない: captureSquareがnull(相手の最善が捕獲を含まない)", () => {
    const findings = i11FocusNotStated.check([
      record(
        { focusText: null },
        { afterPass: { scoreCp: -400, mate: null, bestmove: "8c8d", captureSquare: null } },
      ),
    ]);
    expect(findings).toEqual([]);
  });

  it("発火しない: dropCpがnull(mateが絡む。H-2で③を出さないと決めた)", () => {
    expect(i11FocusNotStated.check([record({ focusText: null }, { dropCp: null })])).toEqual([]);
  });

  // --- 対象外の行 ---
  it("発火しない: focusTextStateが\"pending\"(まだ計算していない。言っていないのとは違う)", () => {
    const findings = i11FocusNotStated.check([
      record({ focusText: null, focusTextState: "pending" }),
    ]);
    expect(findings).toEqual([]);
  });

  it("発火しない: 終局", () => {
    const r = record({ focusText: null });
    r.response.status = { isEnd: true, outcome: undefined };
    expect(i11FocusNotStated.check([r])).toEqual([]);
  });

  it("発火しない: immediate行(readyではない)", () => {
    const r = record({ focusText: null });
    r.phase = "immediate";
    expect(i11FocusNotStated.check([r])).toEqual([]);
  });
});
