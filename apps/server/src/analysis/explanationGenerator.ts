// Shape判定結果(Unit1) + Intent判定結果(Unit2) -> 初心者向け説明(Explanation) への変換。
// docs/DATA_MODEL.md の教育用データパイプライン⑨(初心者向け説明)のうち、
// ②(現在の形)・③(相手の意図)・④(相手の次の狙い)に対応する部分を扱う
// (⑤〜⑧はPhase2、candidate_moveステージは対象外)。
//
// 【将棋知識について】このモジュールは新しい将棋知識を一切作らない。
// 説明文の実質的な内容(「この形が何なのか」「相手が何をしているのか」)は、
// 常に data/shapes/*.json の characteristics と data/intents/*.json の
// current_aim_explanation / next_aim_explanation という、既に人間がレビュー済みの
// 文章をそのまま使う(shapeDetector.ts / intentDetector.ts がそれぞれの結果に
// そのまま引き継いでいるフィールド)。本モジュールが追加するのは以下の2つだけ:
//   1. data/explanations/*.jsonサンプルに既に存在する、ステージ共通の定型purpose文
//      (shape/intentの内容に関わらず同じ文言。「なぜこの説明を見せるか」という
//      アプリ側の目的説明であり、将棋の事実ではない)
//   2. Unit1/Unit2のstatus(none/forming/matched/completed)に応じた、断定を避ける
//      ための定型的な前置き文(「〜の可能性があります」等。これも将棋の事実ではなく、
//      日本語の言い回しテンプレート)
// 上記いずれも「新しい将棋知識の確定」ではないため、確認なしに実装している。
//
// 【glossary_termsについて】将棋用語集(glossary)はdata/配下にまだ実体がない
// (docs/DATA_MODEL.md「用語集データについて」参照。v0.1設計時に構想されたのみで、
// 用語キーの正式な一覧は未確認)。そのため、安全に導出できるshape_id/intent_id自体
// のみを入れるに留める(例: ["boh_gin"])。将来、用語集データが追加された時点で拡張する。

import type { ShapeDetectionResult } from "./shapeDetector.js";
import { detectShapes } from "./shapeDetector.js";
import type { IntentDetectionResult } from "./intentDetector.js";
import { detectIntents, type DetectIntentsOptions } from "./intentDetector.js";

export type ExplanationStage = "current_shape" | "opponent_intent" | "opponent_next_aim";
export type ConfidenceLevel = "high" | "medium" | "low";

// data/schemas/explanations.schema.json に対応する型(スキーマ自体は変更していない)。
export interface Explanation {
  id: string;
  stage: ExplanationStage;
  purpose: string;
  move: null;
  reason: string;
  refers_to_shape_id: string | null;
  refers_to_intent_id: string | null;
  confidence_level: ConfidenceLevel;
  glossary_terms: string[];
  template_id: string;
}

const CONFIDENCE_ORDER: Record<ConfidenceLevel, number> = { low: 0, medium: 1, high: 2 };

/** dataの確信度(shapes/intentsのconfidence_level)を、検知状態に応じた上限で抑える。 */
function capConfidence(dataLevel: ConfidenceLevel, cap: ConfidenceLevel): ConfidenceLevel {
  return CONFIDENCE_ORDER[dataLevel] <= CONFIDENCE_ORDER[cap] ? dataLevel : cap;
}

// data/explanations/*.jsonサンプルにある、各ステージの定型purpose文をそのまま踏襲する
// (shape/intentの内容に依存しない、アプリ側の「なぜこの説明を見せるか」という目的文)。
const PURPOSE_TEMPLATES: Record<ExplanationStage, string> = {
  current_shape:
    "今、自分の陣形がどんな形になっているかを知り、この先どんな囲いを目指せるかを考えるための土台にします。",
  opponent_intent: "相手が今どんな作戦で攻めようとしているかを把握し、慌てずに対応を考えるためです。",
  opponent_next_aim: "相手が次に何を狙ってきそうかを先読みし、今のうちに備えておくためです。",
};

/** ソート済み(matchScore降順)結果配列から、matchScore>0の最有力候補だけを返す。 */
function pickBest<T extends { matchScore: number }>(results: T[]): T | undefined {
  const [best] = results;
  return best && best.matchScore > 0 ? best : undefined;
}

// Explanationはdata/schemas/explanations.schema.json準拠のフィールドのみを持つ
// (additionalProperties: falseのスキーマにそのまま流用できる状態を保つため)。
// 一方、Web API層はバッジ表示等のために「forming/matched/completed/none」という
// 生の判定状態(Unit1のShapeStatus / Unit2のIntentMatchStatus)も必要とするため、
// 内部的にはExplanationと状態をペアで持ち回り、schema純粋なExplanation[]が欲しい
// 呼び出し元(generateExplanations)と、状態つきが欲しい呼び出し元
// (generateCoachExplanations)の両方に対応する。
type RawStatus = ShapeDetectionResult["status"] | IntentDetectionResult["matchStatus"];

interface StageResult {
  explanation: Explanation;
  status: RawStatus;
}

function buildCurrentShapeStage(shapeResults: ShapeDetectionResult[]): StageResult {
  const best = pickBest(shapeResults);

  if (!best) {
    // docs/PHASES.md Phase1完了条件: 「定跡から外れた局面でも、無言・エラーにならず
    // 『未分類』等の穏当な表示に落ちる」に対応する。特定の形を断定しない。
    return {
      status: "none",
      explanation: {
        id: "runtime_current_shape_unclassified",
        stage: "current_shape",
        purpose: PURPOSE_TEMPLATES.current_shape,
        move: null,
        reason:
          "今の陣形は、あらかじめ用意されている形のどれともまだはっきり一致していません。駒がどう組み合わさっていくかを、これから一緒に見ていきましょう。",
        refers_to_shape_id: null,
        refers_to_intent_id: null,
        confidence_level: "low",
        glossary_terms: [],
        template_id: "current_shape_unclassified",
      },
    };
  }

  const lead =
    best.status === "completed"
      ? `今、${best.name}の形ができています。`
      : `${best.name}を作ろうとしている可能性があります(まだ完成はしていません)。`;

  const reason = best.characteristics ? `${lead} ${best.characteristics}` : lead;

  return {
    status: best.status,
    explanation: {
      id: `runtime_current_shape_${best.shapeId}`,
      stage: "current_shape",
      purpose: PURPOSE_TEMPLATES.current_shape,
      move: null,
      reason,
      refers_to_shape_id: best.shapeId,
      refers_to_intent_id: null,
      confidence_level: capConfidence(best.dataConfidenceLevel, best.status === "completed" ? "high" : "medium"),
      glossary_terms: [best.shapeId],
      template_id: `current_shape_${best.status}`,
    },
  };
}

function buildOpponentIntentStage(intentResults: IntentDetectionResult[]): StageResult {
  const best = pickBest(intentResults);

  if (!best) {
    return {
      status: "none",
      explanation: {
        id: "runtime_opponent_intent_unclassified",
        stage: "opponent_intent",
        purpose: PURPOSE_TEMPLATES.opponent_intent,
        move: null,
        reason:
          "相手の狙いは、まだはっきりとは分かりません。特定の作戦を決めつけず、もう少し様子を見てみましょう。",
        refers_to_shape_id: null,
        refers_to_intent_id: null,
        confidence_level: "low",
        glossary_terms: [],
        template_id: "opponent_intent_unclassified",
      },
    };
  }

  const lead =
    best.matchStatus === "matched"
      ? `相手は${best.name}の形になっています。`
      : `相手は${best.name}を狙っている可能性があります(まだ断定はできません)。`;

  return {
    status: best.matchStatus,
    explanation: {
      id: `runtime_opponent_intent_${best.intentId}`,
      stage: "opponent_intent",
      purpose: PURPOSE_TEMPLATES.opponent_intent,
      move: null,
      reason: `${lead} ${best.currentAimExplanation}`,
      refers_to_shape_id: null,
      refers_to_intent_id: best.intentId,
      confidence_level: capConfidence(best.dataConfidenceLevel, best.matchStatus === "matched" ? "high" : "medium"),
      glossary_terms: [best.intentId],
      template_id: `opponent_intent_${best.matchStatus}`,
    },
  };
}

function buildOpponentNextAimStage(intentResults: IntentDetectionResult[]): StageResult {
  const best = pickBest(intentResults);

  if (!best) {
    return {
      status: "none",
      explanation: {
        id: "runtime_opponent_next_aim_unclassified",
        stage: "opponent_next_aim",
        purpose: PURPOSE_TEMPLATES.opponent_next_aim,
        move: null,
        reason: "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
        refers_to_shape_id: null,
        refers_to_intent_id: null,
        confidence_level: "low",
        glossary_terms: [],
        template_id: "opponent_next_aim_unclassified",
      },
    };
  }

  const hedge = best.matchStatus === "matched" ? "" : "まだ断定はできませんが、";

  return {
    status: best.matchStatus,
    explanation: {
      id: `runtime_opponent_next_aim_${best.intentId}`,
      stage: "opponent_next_aim",
      purpose: PURPOSE_TEMPLATES.opponent_next_aim,
      move: null,
      reason: `${hedge}${best.nextAimExplanation}`,
      refers_to_shape_id: null,
      refers_to_intent_id: best.intentId,
      confidence_level: capConfidence(best.dataConfidenceLevel, best.matchStatus === "matched" ? "high" : "medium"),
      glossary_terms: [best.intentId],
      template_id: `opponent_next_aim_${best.matchStatus}`,
    },
  };
}

function buildStages(shapeResults: ShapeDetectionResult[], intentResults: IntentDetectionResult[]): StageResult[] {
  return [
    buildCurrentShapeStage(shapeResults),
    buildOpponentIntentStage(intentResults),
    buildOpponentNextAimStage(intentResults),
  ];
}

/**
 * Unit1(detectShapes)・Unit2(detectIntents)の判定結果から、
 * 「現在の形 -> 相手の意図 -> 相手の次の狙い」の順で3件の説明(Explanation)を組み立てる。
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function generateExplanations(
  shapeResults: ShapeDetectionResult[],
  intentResults: IntentDetectionResult[],
): Explanation[] {
  return buildStages(shapeResults, intentResults).map((s) => s.explanation);
}

/** generateExplanationsのExplanationに、Web API/UI向けの生の判定状態(status)を添えたもの。 */
export interface CoachExplanation extends Explanation {
  status: RawStatus;
}

/**
 * generateExplanationsと同じ材料から、UI側が「forming/matched/completed/none」を
 * そのままバッジ等に表示できるよう、判定状態(status)つきの説明を返す。
 * Explanation自体(スキーマ準拠フィールドのみ)はgenerateExplanationsと完全に同じ内容。
 */
export function generateCoachExplanations(
  shapeResults: ShapeDetectionResult[],
  intentResults: IntentDetectionResult[],
): CoachExplanation[] {
  return buildStages(shapeResults, intentResults).map((s) => ({ ...s.explanation, status: s.status }));
}

export interface ExplainPositionOptions extends DetectIntentsOptions {
  shapes?: Parameters<typeof detectShapes>[1];
}

/**
 * SFEN + 指し手履歴から、Unit1/Unit2を呼び出したうえで説明を組み立てる統合用の入口。
 * (Web API層など、判定結果を個別に扱う必要がない呼び出し元向けの利便関数)
 */
export function explainPosition(
  sfen: string,
  moveHistory: string[],
  options: ExplainPositionOptions = {},
): Explanation[] {
  const shapeResults = detectShapes(sfen, options.shapes);
  const intentResults = detectIntents(sfen, moveHistory, options);
  return generateExplanations(shapeResults, intentResults);
}

/**
 * explainPositionのstatus付き版。apps/server/src/server.ts(HTTP API)が、
 * UI側でforming/matched/completed/noneのバッジ表示を出し分けるために使う。
 */
export function explainPositionWithStatus(
  sfen: string,
  moveHistory: string[],
  options: ExplainPositionOptions = {},
): CoachExplanation[] {
  const shapeResults = detectShapes(sfen, options.shapes);
  const intentResults = detectIntents(sfen, moveHistory, options);
  return generateCoachExplanations(shapeResults, intentResults);
}
