// STEP U6-I4。「本番の canSpeakAtIntentStage を呼ぶ。写さない」(docs/STEP_U6-I3_PLAN_2026-09-12.md
// 19.2 の 2・19.8 の誤り 1)を見張る。
//
// 【なぜ別ファイルか】vi.mock はファイル全体に効く(import より前へ持ち上げられる)。
// intentStatement.test.ts に置くと、T-1 が使う本物の explainPositionWithStatus まで差し替えの
// 影響を受けうるため、このファイルに分けた。
//
// 【なぜ要るか(2026-09-13 の独立監査。必須 1)】
// 今日の本番と同じ意味に写した述語 `!(matched && draft)` に置き換える変異(K2)は、
// intentStatement.test.ts では沈黙した(0/160)。今日の exposeName は draft のときだけ止めるので、
// 同じ意味の変異が沈黙するのは当然である。**しかしこの決定が効くのは、本番の判定が変わった日**
// であり、その日に実装が写した述語に差し替わっていても何も鳴らない。
// **本番を「常に false を返す」ものに差し替え、それが分類に届くことを確かめる。**
// 本番を呼んでいれば鳴り、写していれば鳴らない。文字列に依らない。

import { describe, expect, it, vi } from "vitest";
import type { CoachExplanation } from "../../../apps/server/src/analysis/explanationGenerator.js";
import type { IntentDetectionResult } from "../../../apps/server/src/analysis/intentDetector.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import type { RecordLine } from "../invariants/types.js";
import { classifyIntentStatementRow } from "./intentStatement.js";

vi.mock("../../../apps/server/src/analysis/explanationGenerator.js", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../../apps/server/src/analysis/explanationGenerator.js")>();
  return { ...original, canSpeakAtIntentStage: () => false };
});

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

/** 分類に要る欄だけを持つ記録(classifyIntentStatementRow は response.coach しか読まない)。 */
function recordWithCoach(coach: CoachExplanation[]): RecordLine {
  return {
    kind: "record",
    ply: 0,
    sfen: DEFAULT_INITIAL_SFEN,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response: { coach } as StateResponseBodyWithPlan,
  };
}

function formingResult(intentId: string, ply: number): IntentDetectionResult {
  return {
    intentId,
    name: `テスト${intentId}`,
    openingId: "ibisha",
    dataConfidenceLevel: "medium",
    reviewStatus: "draft",
    matchStatus: "forming",
    matchScore: 0.5,
    matchedSignatures: [{ piece: "歩", to: "8d", evidence: { ply, moveUsi: "8c8d" } }],
    unmatchedSignatures: [{ piece: "歩", to: "9d" }],
    currentAimExplanation: `${intentId}の今の狙い`,
    nextAimExplanation: `${intentId}の次の狙い`,
  };
}

describe("classifyIntentStatementRow は本番の canSpeakAtIntentStage を呼ぶ(写さない)", () => {
  it("本番が「出せない」と言えば、F-7 と同じ forming の名指しが U-7 に変わる", () => {
    // F-7(intentStatement.test.ts)と同じ入力。本物の canSpeakAtIntentStage なら「最も新しい根拠」。
    const record = recordWithCoach([
      stage("opponent_intent", "forming", "opponent_intent_forming", "a"),
      stage("opponent_next_aim", "forming", "opponent_next_aim_unclassified", null),
    ]);
    const result = classifyIntentStatementRow(record, { ok: true, results: [formingResult("a", 12)] });
    expect(result).toEqual({ column: "undetermined", reason: "U-7" });
  });
});
