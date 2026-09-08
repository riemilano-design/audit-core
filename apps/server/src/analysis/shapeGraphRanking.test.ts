import { describe, expect, it } from "vitest";
import { rankReachableShapes } from "./shapeGraphRanking.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import type { TargetPurposeAdjustment } from "./targetPurposeSelector.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";
import { detectIntents } from "./intentDetector.js";
import { selectTargetPurpose } from "./targetPurposeSelector.js";
import { DEFAULT_INITIAL_SFEN } from "./moveHistory.js";

// 単体テスト用の最小フィクスチャ。rankReachableShapesが参照するフィールド
// (shapeId, name, family, parentShapeId, side, status, matchScore)以外は
// 判定に無関係なため、型を満たすためのダミー値を入れる。
function makeShapeResult(overrides: Partial<ShapeFormationResult> & { shapeId: string }): ShapeFormationResult {
  return {
    shapeId: overrides.shapeId,
    name: overrides.name ?? overrides.shapeId,
    side: overrides.side ?? "self",
    family: overrides.family ?? "美濃系",
    parentShapeId: overrides.parentShapeId ?? null,
    perspectiveColor: overrides.perspectiveColor ?? "sente",
    status: overrides.status ?? "none",
    matchScore: overrides.matchScore ?? 0,
    matchedSquares: overrides.matchedSquares ?? [],
    missingSquares: overrides.missingSquares ?? [],
    optionalMatchedSquares: overrides.optionalMatchedSquares ?? [],
    dataConfidenceLevel: overrides.dataConfidenceLevel ?? "medium",
    reviewStatus: overrides.reviewStatus ?? "human_reviewed",
    characteristics: overrides.characteristics ?? "",
    formationEvidence: overrides.formationEvidence ?? [],
  };
}

function makePurpose(overrides: Partial<TargetPurposeAdjustment> & { shapeId: string }): TargetPurposeAdjustment {
  return {
    shapeId: overrides.shapeId,
    adjustment: overrides.adjustment ?? "prioritize",
    reason: overrides.reason ?? "",
    sourceIntentId: overrides.sourceIntentId ?? "boh_gin",
  };
}

describe("rankReachableShapes", () => {
  it("intentなし(targetPurposeが空) -> matchScore降順・shapeId昇順で全候補が中立扱いで並ぶ", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.2, status: "none" }),
      makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.6, status: "forming" }),
    ];

    const ranked = rankReachableShapes(shapeResults, []);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_takamino", "mino_ginkanmuri"]);
    for (const r of ranked) {
      expect(r.adjustment).toBeNull();
      expect(r.reason).toBeNull();
      expect(r.sourceIntentId).toBeNull();
    }
  });

  it("prioritizeされた形は、より高いmatchScoreの中立な形より上位に来る", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.9, status: "forming" }),
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.1, status: "forming" }),
    ];
    const targetPurpose = [makePurpose({ shapeId: "mino_honmino", adjustment: "prioritize" })];

    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_honmino", "mino_ginkanmuri"]);
    expect(ranked[0]!.adjustment).toBe("prioritize");
  });

  it("deprioritizeされた形は、より低いmatchScoreの中立な形より下位に来る", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.9, status: "forming" }),
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.1, status: "forming" }),
    ];
    const targetPurpose = [makePurpose({ shapeId: "mino_ginkanmuri", adjustment: "deprioritize" })];

    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_honmino", "mino_ginkanmuri"]);
    expect(ranked[1]!.adjustment).toBe("deprioritize");
  });

  it("prioritize/deprioritize混在 -> prioritize群 < 中立群 < deprioritize群の順で並ぶ", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.9, status: "forming" }), // deprioritize
      makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.5, status: "forming" }), // 中立
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.1, status: "forming" }), // prioritize
    ];
    const targetPurpose = [
      makePurpose({ shapeId: "mino_honmino", adjustment: "prioritize" }),
      makePurpose({ shapeId: "mino_ginkanmuri", adjustment: "deprioritize" }),
    ];

    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_honmino", "mino_takamino", "mino_ginkanmuri"]);
    expect(ranked.map((r) => r.adjustment)).toEqual(["prioritize", null, "deprioritize"]);
  });

  it("status: completedの形は候補から除外される", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 1, status: "completed" }),
      makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.5, status: "forming" }),
    ];

    const ranked = rankReachableShapes(shapeResults, []);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_takamino"]);
  });

  it("side: opponentの形は候補から除外される(自分が目指す形にはなり得ないため)", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "some_opponent_shape", side: "opponent", matchScore: 1, status: "forming" }),
      makeShapeResult({ shapeId: "mino_honmino", side: "self", matchScore: 0.1, status: "forming" }),
    ];

    const ranked = rankReachableShapes(shapeResults, []);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_honmino"]);
  });

  it("複数候補(3件以上)を正しくランキングする", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.3, status: "none" }),
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.75, status: "forming" }),
      makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.5, status: "forming" }),
    ];

    const ranked = rankReachableShapes(shapeResults, []);

    expect(ranked.map((r) => r.shapeId)).toEqual(["mino_honmino", "mino_takamino", "mino_ginkanmuri"]);
  });

  it("同点(同tier・同matchScore)時はshapeId昇順で決定的にタイブレークする(入力順に依存しない)", () => {
    const a = makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.5, status: "forming" });
    const b = makeShapeResult({ shapeId: "mino_ginkanmuri", matchScore: 0.5, status: "forming" });

    const rankedAB = rankReachableShapes([a, b], []);
    const rankedBA = rankReachableShapes([b, a], []);

    expect(rankedAB.map((r) => r.shapeId)).toEqual(["mino_ginkanmuri", "mino_takamino"]);
    expect(rankedBA.map((r) => r.shapeId)).toEqual(["mino_ginkanmuri", "mino_takamino"]);
  });

  it("targetPurposeがshapeResultsに存在しないshapeIdを参照していても安全に無視される", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.5, status: "forming" })];
    const targetPurpose = [makePurpose({ shapeId: "nonexistent_shape", adjustment: "prioritize" })];

    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked).toHaveLength(1);
    expect(ranked[0]!.shapeId).toBe("mino_honmino");
    expect(ranked[0]!.adjustment).toBeNull();
  });

  it("同一shapeIdに対して複数件のtargetPurposeが渡された場合、最初の1件を決定的に採用する", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.5, status: "forming" })];
    const targetPurpose = [
      makePurpose({ shapeId: "mino_honmino", adjustment: "prioritize", sourceIntentId: "boh_gin" }),
      makePurpose({ shapeId: "mino_honmino", adjustment: "deprioritize", sourceIntentId: "hayajikake" }),
    ];

    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked[0]!.adjustment).toBe("prioritize");
    expect(ranked[0]!.sourceIntentId).toBe("boh_gin");
  });

  it("shapeResultsが空配列 -> 空配列を返す", () => {
    expect(rankReachableShapes([], [])).toEqual([]);
  });

  it("全候補がcompleted -> 空配列を返す", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", matchScore: 1, status: "completed" })];
    expect(rankReachableShapes(shapeResults, [])).toEqual([]);
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_honmino", matchScore: 0.5, status: "forming" }),
      makeShapeResult({ shapeId: "mino_takamino", matchScore: 0.5, status: "forming" }),
    ];
    const targetPurpose = [makePurpose({ shapeId: "mino_honmino", adjustment: "prioritize" })];

    expect(rankReachableShapes(shapeResults, targetPurpose)).toEqual(rankReachableShapes(shapeResults, targetPurpose));
  });

  describe("Phase1データとの統合(回帰確認)", () => {
    it("初期局面: Phase1のanalyzeShapeFormation/detectIntents/selectTargetPurposeをそのまま通して実行してもエラーにならず、除外規則が働く", () => {
      const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
      const intentResults = detectIntents(DEFAULT_INITIAL_SFEN, []);
      const targetPurpose = selectTargetPurpose(intentResults);

      // 初期局面ではintentは全てmatchScore: 0(matchStatus: none)のため、⑤は空。
      expect(targetPurpose).toEqual([]);

      const ranked = rankReachableShapes(shapeResults, targetPurpose);

      // data/shapes/の3件はすべてside: selfであり、初期局面では誰もcompletedではないため、
      // 3件とも候補に残る(除外規則自体がPhase1の実データに対しても安全に働くことの確認)。
      expect(ranked.map((r) => r.shapeId).sort()).toEqual(["mino_ginkanmuri", "mino_honmino", "mino_takamino"]);
      for (const r of ranked) {
        expect(r.adjustment).toBeNull();
      }
    });
  });
});
