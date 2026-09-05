import { describe, expect, it } from "vitest";
import {
  buildCandidateMoveExplanation,
  explainCandidateMoves,
  type CandidateMoveExplanationResult,
} from "./candidateMoveExplanation.js";
import type { CandidateMoveSafetyCheckResult } from "./candidateMoveSafetyCheck.js";
import type { PathPlanCandidateMove, PathPlanResult } from "./pathPlanner.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";

function makePathPlanResult(overrides: Partial<PathPlanResult> & { shapeId: string }): PathPlanResult {
  return {
    shapeId: overrides.shapeId,
    targetSquare: overrides.targetSquare ?? "8h",
    targetPiece: overrides.targetPiece ?? "玉",
    candidateMoves: overrides.candidateMoves ?? [{ moveUsi: "5i8h" }],
    unresolvedReason: overrides.unresolvedReason ?? null,
  };
}

function makeShapeResult(overrides: Partial<ShapeFormationResult> & { shapeId: string }): ShapeFormationResult {
  return {
    shapeId: overrides.shapeId,
    name: overrides.name ?? "本美濃囲い",
    side: overrides.side ?? "self",
    family: overrides.family ?? "美濃系",
    parentShapeId: overrides.parentShapeId ?? null,
    perspectiveColor: overrides.perspectiveColor ?? "sente",
    status: overrides.status ?? "forming",
    matchScore: overrides.matchScore ?? 0.5,
    matchedSquares: overrides.matchedSquares ?? [],
    missingSquares: overrides.missingSquares ?? [],
    optionalMatchedSquares: overrides.optionalMatchedSquares ?? [],
    dataConfidenceLevel: overrides.dataConfidenceLevel ?? "medium",
    characteristics: overrides.characteristics ?? "",
    formationEvidence: overrides.formationEvidence ?? [],
  };
}

// candidateMoveSafetyCheck.tsのCandidateMoveSafetyCheckResult.engineReferenceAvailableは
// 「エンジンによる参考評価を取得し対応付けできたか」という機械的事実であり、
// 「安全」を意味しない(ファイル冒頭コメント参照)。
// multiPvPerEvalを指定しない場合、各evaluationはmultiPv: []
// (=scoreが取得できなかった、という状態)になる。
function makeSafetyCheckResult(
  evaluationsCount: number,
  options: { available?: boolean; multiPvPerEval?: CandidateMoveSafetyCheckResult["evaluations"][number]["multiPv"][] } = {},
): CandidateMoveSafetyCheckResult {
  const { available = true, multiPvPerEval } = options;
  return {
    baselineSfen: "startpos",
    baselineMultiPv: [],
    evaluations: Array.from({ length: evaluationsCount }, (_, i) => ({
      moveUsi: `dummy${i}`,
      resultingSfen: "startpos",
      multiPv: multiPvPerEval?.[i] ?? [],
    })),
    engineReferenceAvailable: available,
  };
}

describe("explainCandidateMoves", () => {
  it("候補手が0件の場合、not_ready(no_candidate_moves)で説明を1件も生成しない", () => {
    const pathPlanResult = makePathPlanResult({ shapeId: "mino_honmino", candidateMoves: [] });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];

    const result = explainCandidateMoves(pathPlanResult, shapeResults, makeSafetyCheckResult(0));

    expect(result).toEqual<CandidateMoveExplanationResult>({
      status: "not_ready",
      notReadyReason: "no_candidate_moves",
      explanations: [],
    });
  });

  it("shapeIdに対応するShapeFormationResultが見つからない場合、安全にnot_readyを返す", () => {
    const pathPlanResult = makePathPlanResult({ shapeId: "mino_honmino" });
    const result = explainCandidateMoves(pathPlanResult, [], makeSafetyCheckResult(1));

    expect(result.status).toBe("not_ready");
    expect(result.notReadyReason).toBe("shape_result_not_found");
    expect(result.explanations).toEqual([]);
  });

  it("engineReferenceAvailableがfalseの間は、候補が揃っていても説明を1件も生成しない(UI表示対象から除外される)", () => {
    const pathPlanResult = makePathPlanResult({ shapeId: "mino_honmino" });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];

    const result = explainCandidateMoves(
      pathPlanResult,
      shapeResults,
      makeSafetyCheckResult(1, { available: false }),
    );

    expect(result.status).toBe("not_ready");
    expect(result.notReadyReason).toBe("engine_reference_unavailable");
    expect(result.explanations).toEqual([]);
  });

  it("複数候補があっても、engineReferenceAvailableがfalseなら全て除外される(一部だけ通す、という挙動はしない)", () => {
    const pathPlanResult = makePathPlanResult({
      shapeId: "mino_honmino",
      candidateMoves: [{ moveUsi: "5i8h" }, { moveUsi: "6i8h" }],
    });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];

    const result = explainCandidateMoves(
      pathPlanResult,
      shapeResults,
      makeSafetyCheckResult(2, { available: false }),
    );

    expect(result.explanations).toEqual([]);
  });

  it("engineReferenceAvailableがtrueで、全候補にscoreつきのMultiPV評価がある場合、候補数分のExplanationが生成される", () => {
    const pathPlanResult = makePathPlanResult({
      shapeId: "mino_honmino",
      candidateMoves: [{ moveUsi: "5i8h" }, { moveUsi: "6i8h" }],
    });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];
    const safetyCheck = makeSafetyCheckResult(2, {
      available: true,
      multiPvPerEval: [
        [{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }],
        [{ multipv: 1, score: { type: "cp", value: -5 }, pv: [] }],
      ],
    });

    const result = explainCandidateMoves(pathPlanResult, shapeResults, safetyCheck);

    expect(result.status).toBe("ready");
    expect(result.notReadyReason).toBeNull();
    expect(result.explanations.map((e) => e.move)).toEqual(["5i8h", "6i8h"]);
  });

  it("engineReferenceAvailableがtrueでも、評価データ(score)が無い候補だけを個別に除外する", () => {
    const pathPlanResult = makePathPlanResult({
      shapeId: "mino_honmino",
      candidateMoves: [{ moveUsi: "5i8h" }, { moveUsi: "6i8h" }],
    });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];
    const safetyCheck = makeSafetyCheckResult(2, {
      available: true,
      multiPvPerEval: [
        [{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }],
        [], // stopによる早期終了等でscoreが得られなかった想定
      ],
    });

    const result = explainCandidateMoves(pathPlanResult, shapeResults, safetyCheck);

    expect(result.status).toBe("ready");
    expect(result.explanations).toHaveLength(1);
    expect(result.explanations[0]!.move).toBe("5i8h");
  });

  it("engineReferenceAvailableがtrueでも、全候補が評価データ無しならnot_ready(insufficient_engine_data)になる", () => {
    const pathPlanResult = makePathPlanResult({
      shapeId: "mino_honmino",
      candidateMoves: [{ moveUsi: "5i8h" }, { moveUsi: "6i8h" }],
    });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];
    const safetyCheck = makeSafetyCheckResult(2, { available: true, multiPvPerEval: [[], []] });

    const result = explainCandidateMoves(pathPlanResult, shapeResults, safetyCheck);

    expect(result.status).toBe("not_ready");
    expect(result.notReadyReason).toBe("insufficient_engine_data");
    expect(result.explanations).toEqual([]);
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    const pathPlanResult = makePathPlanResult({ shapeId: "mino_honmino" });
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino" })];
    const safetyCheck = makeSafetyCheckResult(1, {
      multiPvPerEval: [[{ multipv: 1, score: { type: "cp", value: 1 }, pv: [] }]],
    });

    expect(explainCandidateMoves(pathPlanResult, shapeResults, safetyCheck)).toEqual(
      explainCandidateMoves(pathPlanResult, shapeResults, safetyCheck),
    );
  });
});

describe("buildCandidateMoveExplanation", () => {
  const candidate: PathPlanCandidateMove = { moveUsi: "5i8h" };
  const pathPlanResult = makePathPlanResult({ shapeId: "mino_honmino" });
  const shapeResult = makeShapeResult({ shapeId: "mino_honmino", dataConfidenceLevel: "medium" });

  it("stage: candidate_move、move: 候補手のUSI文字列を持つExplanationを組み立てる", () => {
    const explanation = buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate);

    expect(explanation.stage).toBe("candidate_move");
    expect(explanation.move).toBe("5i8h");
    expect(explanation.refers_to_shape_id).toBe("mino_honmino");
    expect(explanation.glossary_terms).toEqual(["mino_honmino"]);
  });

  it("断定的な表現(最善/おすすめ/必ず/正解だと言い切る表現)を一切含まない", () => {
    const explanation = buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate);
    // "唯一の正解ではありません"のような「正解であることの否定」は許容する
    // (むしろ望ましい)ため、"正解"の有無ではなく断定を示す肯定的な言い切り表現の
    // 有無をチェックする。
    for (const banned of ["最善", "おすすめ", "必ず", "べきです", "が正解です", "は正解"]) {
      expect(explanation.reason).not.toContain(banned);
      expect(explanation.purpose).not.toContain(banned);
    }
  });

  it("typical_build_orderを唯一の正解として扱わない旨の文言が含まれる", () => {
    const explanation = buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate);
    expect(explanation.reason).toContain("一例");
    expect(explanation.reason).toContain("唯一の正解ではありません");
  });

  it("idはUSI形式の特殊文字(+/*)を含んでいてもschemaのpattern(^[a-z0-9_]+$)に適合するよう変換する", () => {
    const dropCandidate: PathPlanCandidateMove = { moveUsi: "P*5e" };
    const explanation = buildCandidateMoveExplanation(pathPlanResult, shapeResult, dropCandidate);
    expect(explanation.id).toMatch(/^[a-z0-9_]+$/);
    // move自体(実際の指し手)は変換せずそのまま保持する。
    expect(explanation.move).toBe("P*5e");
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    expect(buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate)).toEqual(
      buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate),
    );
  });
});
