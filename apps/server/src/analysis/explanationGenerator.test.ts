import { describe, expect, it } from "vitest";
import { detectIntents } from "./intentDetector.js";
import { detectShapes, type ShapeDetectionResult } from "./shapeDetector.js";
import { getShapes } from "./shapeRepository.js";
import { getIntents, type IntentDefinition } from "./intentRepository.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import { explainPosition, generateExplanations, type Explanation } from "./explanationGenerator.js";

const SENTE_FILLERS = ["1g1f", "2g2f", "3g3f", "4g4f", "5g5f", "6g6f", "9g9f", "8g8f"];

function interleaveWithSenteFillers(goteMoves: string[]): string[] {
  const moves: string[] = [];
  goteMoves.forEach((goteMove, i) => {
    const filler = SENTE_FILLERS[i];
    if (!filler) throw new Error("SENTE_FILLERSが不足しています");
    moves.push(filler, goteMove);
  });
  return moves;
}

function sfenAfter(moveHistory: string[]): string {
  return replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN).finalSfen;
}

function findStage(explanations: Explanation[], stage: Explanation["stage"]): Explanation {
  const found = explanations.find((e) => e.stage === stage);
  if (!found) throw new Error(`stage not found: ${stage}`);
  return found;
}

// data/intents/hayajikake.json: 歩 6d(1) -> 6e(2)
const HAYAJIKAKE_GOTE_MOVES_FULL = ["6c6d", "6d6e"];

// 本美濃(mino_honmino)の必須駒配置(8h玉・7h銀・6i金・5h金)そのもの。
const TEST_HONMINO: ShapeDetectionResult = {
  shapeId: "mino_honmino",
  name: "本美濃囲い",
  side: "self",
  family: "美濃系",
  parentShapeId: null,
  perspectiveColor: "sente",
  status: "completed",
  matchScore: 1,
  matchedSquares: ["8h", "7h", "6i", "5h"],
  missingSquares: [],
  optionalMatchedSquares: [],
  dataConfidenceLevel: "medium",
  characteristics: "四間飛車でよく使われる、完成が早くバランスの良い囲い。",
};

const NO_SHAPE_RESULTS: ShapeDetectionResult[] = getShapes().map((shape) => ({
  shapeId: shape.id,
  name: shape.name,
  side: shape.side,
  family: shape.family,
  parentShapeId: shape.parent_shape_id ?? null,
  perspectiveColor: "sente",
  status: "none",
  matchScore: 0,
  matchedSquares: [],
  missingSquares: shape.required_pieces.filter((p) => !p.optional).map((p) => p.square),
  optionalMatchedSquares: [],
  dataConfidenceLevel: shape.confidence_level,
  characteristics: shape.characteristics,
}));

const NO_INTENT_RESULTS = getIntents().map((intent) => ({
  intentId: intent.id,
  name: intent.name,
  openingId: intent.opening_id,
  dataConfidenceLevel: intent.confidence_level,
  matchStatus: "none" as const,
  matchScore: 0,
  matchedSignatures: [],
  unmatchedSignatures: intent.recognition_pattern,
  currentAimExplanation: intent.current_aim_explanation,
  nextAimExplanation: intent.next_aim_explanation,
  affectsTargetShapes: intent.affects_target_shapes,
}));

describe("generateExplanations", () => {
  it("常に3件(current_shape/opponent_intent/opponent_next_aim)を、その順序で返す", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    expect(explanations.map((e) => e.stage)).toEqual(["current_shape", "opponent_intent", "opponent_next_aim"]);
  });

  it("current_shape: Shapeがcompletedの場合、名称と根拠(shapes.characteristics由来)を含む説明を返す", () => {
    const explanations = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.refers_to_shape_id).toBe("mino_honmino");
    expect(currentShape.reason).toContain("本美濃囲い");
    expect(currentShape.reason).toContain(TEST_HONMINO.characteristics);
    expect(currentShape.confidence_level).not.toBe("low");
    expect(currentShape.purpose).toBeTruthy();
    expect(currentShape.move).toBeNull();
  });

  it("current_shape: Shapeがforming(全shapeがmatchScore<1)の場合、断定しない言い回しになる", () => {
    const forming: ShapeDetectionResult = { ...TEST_HONMINO, status: "forming", matchScore: 0.5, missingSquares: ["5h"] };
    const explanations = generateExplanations([forming], NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.reason).toContain("可能性があります");
    expect(currentShape.reason).not.toContain("完成しています");
  });

  it("current_shape: 全shapeがnone(matchScore 0)の場合、特定の形を断定せず『未分類』の説明になる", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    const currentShape = findStage(explanations, "current_shape");

    expect(currentShape.refers_to_shape_id).toBeNull();
    expect(currentShape.confidence_level).toBe("low");
    // data/shapes/に存在する形の名称を、根拠なく断定的に名指ししていないこと
    for (const shape of getShapes()) {
      expect(currentShape.reason).not.toContain(shape.name);
    }
  });

  it("opponent_intent / opponent_next_aim: Unit1/Unit2と統合し、早仕掛けmatched局面で一貫した説明になる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = detectShapes(sfen);
    const intentResults = detectIntents(sfen, moveHistory);
    const explanations = generateExplanations(shapeResults, intentResults);

    const opponentIntent = findStage(explanations, "opponent_intent");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    expect(opponentIntent.reason).toContain("早仕掛け");
    // intents.current_aim_explanation(既存の人間レビュー済みテキスト)がそのまま含まれること
    const hayajikake = getIntents().find((i) => i.id === "hayajikake")!;
    expect(opponentIntent.reason).toContain(hayajikake.current_aim_explanation);
    expect(opponentIntent.confidence_level).not.toBe("low");

    const nextAim = findStage(explanations, "opponent_next_aim");
    expect(nextAim.refers_to_intent_id).toBe("hayajikake");
    expect(nextAim.reason).toContain(hayajikake.next_aim_explanation);
  });

  it("opponent_intent: Intentがforming(途中段階)の場合、断定しない言い回しになる", () => {
    const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
    const sfen = sfenAfter(moveHistory);
    const shapeResults = detectShapes(sfen);
    const intentResults = detectIntents(sfen, moveHistory);
    const explanations = generateExplanations(shapeResults, intentResults);

    const opponentIntent = findStage(explanations, "opponent_intent");
    expect(opponentIntent.reason).toContain("可能性があります");
    expect(opponentIntent.reason).toContain("断定はできません");

    const nextAim = findStage(explanations, "opponent_next_aim");
    expect(nextAim.reason).toContain("断定はできません");
  });

  it("opponent_intent / opponent_next_aim: 全intentがnoneの場合、特定の意図を断定しない", () => {
    const explanations = generateExplanations(NO_SHAPE_RESULTS, NO_INTENT_RESULTS);
    const opponentIntent = findStage(explanations, "opponent_intent");
    const nextAim = findStage(explanations, "opponent_next_aim");

    expect(opponentIntent.refers_to_intent_id).toBeNull();
    expect(opponentIntent.confidence_level).toBe("low");
    expect(nextAim.refers_to_intent_id).toBeNull();
    expect(nextAim.confidence_level).toBe("low");
    for (const intent of getIntents()) {
      expect(opponentIntent.reason).not.toContain(intent.name);
    }
  });

  it("同じ入力に対して常に同じ結果を返す(決定的。LLM等の非決定的な作文をしない)", () => {
    const first = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    const second = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    expect(second).toEqual(first);
  });

  it("すべてのExplanationがdata/schemas/explanations.schema.jsonの必須フィールドを満たす", () => {
    const explanations = generateExplanations([TEST_HONMINO], NO_INTENT_RESULTS);
    for (const explanation of explanations) {
      expect(explanation.id).toMatch(/^[a-z0-9_]+$/);
      expect(["current_shape", "opponent_intent", "opponent_next_aim"]).toContain(explanation.stage);
      expect(explanation.purpose.length).toBeGreaterThan(0);
      expect(explanation.reason.length).toBeGreaterThan(0);
      expect(["high", "medium", "low"]).toContain(explanation.confidence_level);
    }
  });
});

describe("explainPosition (Unit1/Unit2との統合)", () => {
  it("SFEN+moveHistoryから直接、Unit1(detectShapes)・Unit2(detectIntents)を経由して説明を生成する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const sfen = sfenAfter(moveHistory);

    const viaIntegration = explainPosition(sfen, moveHistory);
    const viaManual = generateExplanations(detectShapes(sfen), detectIntents(sfen, moveHistory));

    expect(viaIntegration).toEqual(viaManual);
  });

  it("不正な入力(sfenとmoveHistoryの不整合)はdetectIntents由来のエラーがそのまま伝播する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    expect(() => explainPosition(DEFAULT_INITIAL_SFEN, moveHistory)).toThrow();
  });

  it("不正なSFENに対してエラーを投げる", () => {
    expect(() => explainPosition("not-a-valid-sfen", [])).toThrow();
  });
});
