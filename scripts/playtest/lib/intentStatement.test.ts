// STEP U6-I4。lib/intentStatement.ts のテスト。docs/STEP_U6-I3_PLAN_2026-09-12.md 19.4。
//
// - F-1〜F-10・F-12 … 純粋関数 classifyIntentStatementRow に、合成した検出結果を直接渡す
//   (実データに依存しない ― P-20)
// - F-11 … 薄い呼び出し summarizeIntentStatements に、sfen と履歴が食い違う記録を渡す
//   (本物の detectIntents が例外を投げる経路を通る)
// - T-1 … 固定棋譜 7 局から記録を組み、summarizeIntentStatements に通す(エンジン不要)。
//   **件数は固定しない**(data/intents/ を増やすたびに落ちる ― P-20。19.4.3 の決定)。
//   固定するのは data に依存しない期待値だけ。

import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import {
  explainPositionWithStatus,
  type CoachExplanation,
} from "../../../apps/server/src/analysis/explanationGenerator.js";
import type { IntentDetectionResult } from "../../../apps/server/src/analysis/intentDetector.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../../../apps/server/src/analysis/moveHistory.js";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { RecordLine } from "../invariants/types.js";
import {
  classifyIntentStatementRow,
  summarizeIntentStatements,
  UNDETERMINED_REASONS,
  type IntentDetection,
  type IntentStatementClass,
  type UndeterminedReason,
} from "./intentStatement.js";

// ---- 記録の土台(denominators.test.ts と同じ形) ----

function basePlan(): ReachablePlanBody {
  return {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
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

function makeRecord(sfen: string, moveHistory: string[], coach: CoachExplanation[] | undefined): RecordLine {
  const response: StateResponseBodyWithPlan = {
    sfen,
    moveHistory,
    status: { isEnd: false, outcome: undefined },
    coach,
    legalMoves: [],
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: basePlan(),
  };
  return {
    kind: "record",
    ply: moveHistory.length,
    sfen,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response,
  };
}

function stage(
  stageName: "opponent_intent" | "opponent_next_aim",
  status: CoachExplanation["status"],
  templateId: string,
  refersToIntentId: string | null,
): CoachExplanation {
  return {
    id: `runtime_${stageName}`,
    stage: stageName,
    purpose: "purpose",
    move: null,
    reason: "reason",
    refers_to_shape_id: null,
    refers_to_intent_id: refersToIntentId,
    confidence_level: "low",
    glossary_terms: [],
    template_id: templateId,
    status,
  };
}

/** [2] が狙いを名指しし、[3] がその status を出している記録(本番の forming/matched の段の形)。 */
function spokeRecord(namedIntentId: string, status: "forming" | "matched"): RecordLine {
  return makeRecord(DEFAULT_INITIAL_SFEN, [], [
    stage("opponent_intent", status, `opponent_intent_${status}`, namedIntentId),
    stage(
      "opponent_next_aim",
      status,
      status === "forming" ? "opponent_next_aim_unclassified" : `opponent_next_aim_${status}`,
      status === "forming" ? null : namedIntentId,
    ),
  ]);
}

// ---- 合成の検出結果 ----

/** 狙い 1 件の検出結果。署名の ply を並べて渡す(matchScore は matched / total)。 */
function intentResult(
  intentId: string,
  signaturePlies: number[],
  totalSignatures: number,
  reviewStatus: "draft" | "human_reviewed",
): IntentDetectionResult {
  const matchedCount = signaturePlies.length;
  const unmatchedCount = totalSignatures - matchedCount;
  return {
    intentId,
    name: `テスト${intentId}`,
    openingId: "ibisha",
    dataConfidenceLevel: "medium",
    reviewStatus,
    matchStatus: matchedCount === 0 ? "none" : unmatchedCount === 0 ? "matched" : "forming",
    matchScore: totalSignatures === 0 ? 0 : matchedCount / totalSignatures,
    matchedSignatures: signaturePlies.map((ply) => ({ piece: "歩", to: "8d", evidence: { ply, moveUsi: "8c8d" } })),
    unmatchedSignatures: Array.from({ length: unmatchedCount }, () => ({ piece: "歩", to: "9d" })),
    currentAimExplanation: `${intentId}の今の狙い`,
    nextAimExplanation: `${intentId}の次の狙い`,
  };
}

const detected = (...results: IntentDetectionResult[]): IntentDetection => ({ ok: true, results });
const reason = (r: UndeterminedReason): IntentStatementClass => ({ column: "undetermined", reason: r });

// ---- 固定例(19.4.1) ----

describe("classifyIntentStatementRow の固定例(19.4.1)", () => {
  it("F-1: 名指しした狙いの根拠が、出せる他の候補より古ければ「より古い根拠」", () => {
    const record = spokeRecord("a", "forming");
    const result = classifyIntentStatementRow(
      record,
      detected(intentResult("a", [4], 2, "draft"), intentResult("b", [18], 2, "draft")),
    );
    expect(result).toEqual({ column: "spokeOlder" });
  });

  it("F-2: 名指しした intentId が検出結果に無ければ U-5(黙って飛ばさない)", () => {
    const record = spokeRecord("gone", "forming");
    const result = classifyIntentStatementRow(record, detected(intentResult("a", [4], 2, "draft")));
    expect(result).toEqual(reason("U-5"));
  });

  it("F-3: 候補が 1 件だけなら「最も新しい根拠」(等しい側を最新に数える)", () => {
    const record = spokeRecord("a", "forming");
    const result = classifyIntentStatementRow(record, detected(intentResult("a", [6], 2, "draft")));
    expect(result).toEqual({ column: "spokeLatest" });
  });

  it("F-4: [3] が none なら「候補が 1 件も無い」", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_intent", "none", "opponent_intent_unclassified", null),
      stage("opponent_next_aim", "none", "opponent_next_aim_unclassified", null),
    ]);
    expect(classifyIntentStatementRow(record, detected())).toEqual({ column: "noCandidate" });
  });

  it("F-5: 名指しした狙いの根拠が 2 手にまたがるときは、その最大で比べる", () => {
    const record = spokeRecord("a", "forming");
    const result = classifyIntentStatementRow(
      record,
      detected(intentResult("a", [4, 18], 3, "draft"), intentResult("b", [10], 2, "draft")),
    );
    expect(result).toEqual({ column: "spokeLatest" });
  });

  it("F-6: 出せない候補(matched かつ draft)は、根拠が新しくても比べる相手に入れない", () => {
    const record = spokeRecord("a", "forming");
    const result = classifyIntentStatementRow(
      record,
      detected(intentResult("a", [10], 2, "draft"), intentResult("b", [20], 1, "draft")),
    );
    expect(result).toEqual({ column: "spokeLatest" });
  });

  it("F-7: forming の狙いの名指しは「判定できない」に落ちない", () => {
    const record = spokeRecord("a", "forming");
    const result = classifyIntentStatementRow(record, detected(intentResult("a", [12], 2, "draft")));
    expect(result).toEqual({ column: "spokeLatest" });
  });

  it("F-8: coach に [2] が無ければ U-1", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_next_aim", "none", "opponent_next_aim_unclassified", null),
    ]);
    expect(classifyIntentStatementRow(record, detected())).toEqual(reason("U-1"));
  });

  it("F-13: coach に [2] が無く、検出も失敗した行は U-1(理由は上から順に、最初に当たったものを採る)", () => {
    // U-1 と U-2 の両方に当たる入力。判定の順(19.3)を入れ替える変異(K3)を鳴らすために置く。
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_next_aim", "none", "opponent_next_aim_unclassified", null),
    ]);
    expect(classifyIntentStatementRow(record, { ok: false })).toEqual(reason("U-1"));
  });

  it("F-9: 候補が matched かつ draft だけで [2] が unclassified に落ちたら「候補があるのに黙った」", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_intent", "none", "opponent_intent_unclassified", null),
      stage("opponent_next_aim", "matched", "opponent_next_aim_matched", "a"),
    ]);
    const result = classifyIntentStatementRow(record, detected(intentResult("a", [8, 10], 2, "draft")));
    expect(result).toEqual({ column: "muted" });
  });

  it("F-10: どの列にも当たらない整合しない記録は U-4(受け皿)", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_intent", "forming", "opponent_intent_forming", null),
      stage("opponent_next_aim", "forming", "opponent_next_aim_unclassified", null),
    ]);
    expect(classifyIntentStatementRow(record, detected())).toEqual(reason("U-4"));
  });

  it("F-12: 2 つの列に当たる整合しない記録は U-3([3] が none なのに [2] が名指し)", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_intent", "forming", "opponent_intent_forming", "a"),
      stage("opponent_next_aim", "none", "opponent_next_aim_unclassified", null),
    ]);
    const result = classifyIntentStatementRow(record, detected(intentResult("a", [4], 2, "draft")));
    expect(result).toEqual(reason("U-3"));
  });
});

// ---- 薄い呼び出しの固定例と T-1(19.4.3) ----

const ZERO_UNDETERMINED = Object.fromEntries(Object.keys(UNDETERMINED_REASONS).map((r) => [r, 0]));

describe("summarizeIntentStatements(薄い呼び出し。19.4.3)", () => {
  it("F-11: sfen と履歴が食い違う記録は、行を消さずに U-2 に数える", () => {
    const record = makeRecord(DEFAULT_INITIAL_SFEN, ["7g7f"], [
      stage("opponent_intent", "none", "opponent_intent_unclassified", null),
      stage("opponent_next_aim", "none", "opponent_next_aim_unclassified", null),
    ]);
    const counts = summarizeIntentStatements([record]);
    expect(counts.totalPlies).toBe(1);
    expect(counts.undetermined["U-2"]).toBe(1);
  });

  it("F-10(薄い呼び出し経由): どの列にも当たらない行も全手数に数え、U-4 に入れて assert が通る", () => {
    // 純粋関数の F-10 と同じ記録。受け皿を外す変異(M-6)は summarizeIntentStatements の中を
    // 壊すので、純粋関数の固定例だけでは鳴らない。ここで assert が鳴ることを見張る。
    const record = makeRecord(DEFAULT_INITIAL_SFEN, [], [
      stage("opponent_intent", "forming", "opponent_intent_forming", null),
      stage("opponent_next_aim", "forming", "opponent_next_aim_unclassified", null),
    ]);
    const counts = summarizeIntentStatements([record]);
    expect(counts.totalPlies).toBe(1);
    expect(counts.undetermined["U-4"]).toBe(1);
  });

  it("T-1: 固定棋譜 7 局を通すと、107 行すべてがどれかの列に入り、判定できない行は 0 件", () => {
    const kifuDir = join(dirname(fileURLToPath(import.meta.url)), "..", "kifu");
    const kifuFiles = readdirSync(kifuDir).filter((name) => name.endsWith(".json")).sort();
    expect(kifuFiles).toHaveLength(7);

    const records: RecordLine[] = [];
    for (const file of kifuFiles) {
      const moves: string[] = JSON.parse(readFileSync(join(kifuDir, file), "utf8")).moves;
      for (let ply = 0; ply <= moves.length; ply += 2) {
        const moveHistory = moves.slice(0, ply);
        const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
        records.push(makeRecord(finalSfen, moveHistory, explainPositionWithStatus(finalSfen, moveHistory)));
      }
    }

    const counts = summarizeIntentStatements(records);
    // data に依存しない期待値だけを固定する(19.4.3)。
    expect(counts.totalPlies).toBe(107);
    expect(counts.undetermined).toEqual(ZERO_UNDETERMINED);
    // ply 0 は後手が 1 手も指していないので、どの data でも候補は 0 件。
    expect(counts.noCandidate).toBeGreaterThanOrEqual(1);
  });
});
