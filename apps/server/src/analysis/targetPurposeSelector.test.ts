import { describe, expect, it } from "vitest";
import { selectTargetPurpose } from "./targetPurposeSelector.js";
import type { IntentDetectionResult } from "./intentDetector.js";

// 単体テスト用の最小フィクスチャ。selectTargetPurposeが参照するフィールド
// (matchScore, intentId, affectsTargetShapes)以外は判定に無関係なため、
// 型を満たすためのダミー値を入れる。
function makeIntentResult(overrides: Partial<IntentDetectionResult> & { intentId: string }): IntentDetectionResult {
  return {
    intentId: overrides.intentId,
    name: overrides.name ?? overrides.intentId,
    openingId: overrides.openingId ?? "ibisha",
    dataConfidenceLevel: overrides.dataConfidenceLevel ?? "medium",
    reviewStatus: overrides.reviewStatus ?? "human_reviewed",
    matchStatus: overrides.matchStatus ?? "forming",
    matchScore: overrides.matchScore ?? 0.5,
    matchedSignatures: overrides.matchedSignatures ?? [],
    unmatchedSignatures: overrides.unmatchedSignatures ?? [],
    currentAimExplanation: overrides.currentAimExplanation ?? "",
    nextAimExplanation: overrides.nextAimExplanation ?? "",
    affectsTargetShapes: overrides.affectsTargetShapes,
  };
}

describe("selectTargetPurpose", () => {
  it("intentResultsが空配列 -> 空配列を返す(安全なフォールバック)", () => {
    expect(selectTargetPurpose([])).toEqual([]);
  });

  it("全intentのmatchScoreが0(=none) -> 空配列を返す", () => {
    const results = [
      makeIntentResult({ intentId: "boh_gin", matchScore: 0, matchStatus: "none" }),
      makeIntentResult({ intentId: "hayajikake", matchScore: 0, matchStatus: "none" }),
    ];
    expect(selectTargetPurpose(results)).toEqual([]);
  });

  it("affectsTargetShapesが未定義のintentのみが最有力 -> 空配列を返す", () => {
    const results = [makeIntentResult({ intentId: "boh_gin", matchScore: 0.5, affectsTargetShapes: undefined })];
    expect(selectTargetPurpose(results)).toEqual([]);
  });

  it("1件のintentがmatchScore>0 -> そのaffects_target_shapesをそのまま反映する", () => {
    const results = [
      makeIntentResult({
        intentId: "boh_gin",
        matchScore: 0.5,
        affectsTargetShapes: [
          { shape_id: "mino_honmino", adjustment: "prioritize", reason: "急戦のため早く完成させたい" },
          { shape_id: "mino_ginkanmuri", adjustment: "deprioritize", reason: "組むのに時間がかかるため" },
        ],
      }),
    ];

    expect(selectTargetPurpose(results)).toEqual([
      {
        shapeId: "mino_honmino",
        adjustment: "prioritize",
        reason: "急戦のため早く完成させたい",
        sourceIntentId: "boh_gin",
      },
      {
        shapeId: "mino_ginkanmuri",
        adjustment: "deprioritize",
        reason: "組むのに時間がかかるため",
        sourceIntentId: "boh_gin",
      },
    ]);
  });

  it("reasonが未定義の場合は空文字にフォールバックする", () => {
    const results = [
      makeIntentResult({
        intentId: "boh_gin",
        matchScore: 0.5,
        affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize" }],
      }),
    ];
    expect(selectTargetPurpose(results)[0]!.reason).toBe("");
  });

  it("複数intentのmatchScoreが異なる -> matchScoreが最大の1件だけを採用する(合算しない)", () => {
    const results = [
      makeIntentResult({
        intentId: "boh_gin",
        matchScore: 0.33,
        affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "boh_gin由来" }],
      }),
      makeIntentResult({
        intentId: "hayajikake",
        matchScore: 1,
        affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "hayajikake由来" }],
      }),
    ];

    const purpose = selectTargetPurpose(results);
    expect(purpose).toHaveLength(1);
    expect(purpose[0]!.sourceIntentId).toBe("hayajikake");
    expect(purpose[0]!.reason).toBe("hayajikake由来");
  });

  it("複数intentのmatchScoreが同点 -> intentId昇順で決定的に1件を選ぶ(入力順に依存しない)", () => {
    const a = makeIntentResult({
      intentId: "hayajikake",
      matchScore: 0.5,
      affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "hayajikake由来" }],
    });
    const b = makeIntentResult({
      intentId: "boh_gin",
      matchScore: 0.5,
      affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "boh_gin由来" }],
    });

    const purposeAB = selectTargetPurpose([a, b]);
    const purposeBA = selectTargetPurpose([b, a]);

    expect(purposeAB[0]!.sourceIntentId).toBe("boh_gin");
    expect(purposeBA[0]!.sourceIntentId).toBe("boh_gin");
    expect(purposeAB).toEqual(purposeBA);
  });

  it("matchScore<=0のintentが最有力候補に混ざっていても除外される", () => {
    const results = [
      makeIntentResult({ intentId: "naname_bogin", matchScore: 0, matchStatus: "none" }),
      makeIntentResult({
        intentId: "boh_gin",
        matchScore: 0.33,
        affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "boh_gin由来" }],
      }),
    ];

    const purpose = selectTargetPurpose(results);
    expect(purpose).toHaveLength(1);
    expect(purpose[0]!.sourceIntentId).toBe("boh_gin");
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const results = [
      makeIntentResult({
        intentId: "boh_gin",
        matchScore: 0.5,
        affectsTargetShapes: [{ shape_id: "mino_honmino", adjustment: "prioritize", reason: "x" }],
      }),
    ];
    expect(selectTargetPurpose(results)).toEqual(selectTargetPurpose(results));
  });
});
