// Shape判定結果(Unit1) + Intent判定結果(Unit2) -> 初心者向け説明(Explanation) への変換。
// docs/DATA_MODEL.md の教育用データパイプライン⑨(初心者向け説明)のうち、
// ②(現在の形)・③(相手の意図)・④(相手の次の狙い)に対応する部分を扱う。
// candidate_moveステージ(⑦の説明)は、pathPlanner.ts/candidateMoveSafetyCheck.tsの
// 結果を必要とするため、別モジュール(candidateMoveExplanation.ts)が扱う。
// 本ファイルはExplanationStage型・PURPOSE_TEMPLATES・capConfidenceをそちらへ
// export し、重複するテンプレート・型を作らないようにしている。
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

import type { IntentDetectionResult } from "./intentDetector.js";
import { detectIntents, type DetectIntentsOptions } from "./intentDetector.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { analyzeShapeFormation, type AnalyzeShapeFormationOptions } from "./shapeFormationAnalyzer.js";

// "candidate_move"はdata/schemas/explanations.schema.jsonのstage enumに元々含まれていた
// 値(スキーマ変更ではなく、TS側の型をスキーマに追いつかせる追加)。
// candidateMoveExplanation.ts(Phase2)がこの値を使う。既存の3ステージの生成関数
// (buildCurrentShapeStage等)は変更していない。
export type ExplanationStage = "current_shape" | "opponent_intent" | "opponent_next_aim" | "candidate_move";
export type ConfidenceLevel = "high" | "medium" | "low";

// data/schemas/explanations.schema.json に対応する型(スキーマ自体は変更していない)。
// moveはスキーマ上元々["string","null"]("stageがcandidate_moveの場合のみ値を持つ")
// だったが、これまでcandidate_moveステージを生成していなかったためnull固定になっていた。
// candidateMoveExplanation.tsがcandidate_move(move: 実際のUSI文字列)を生成できるよう、
// スキーマに合わせてTS側の型をstring | nullへ広げた(スキーマ自体は変更していない。
// 既存の3ステージは今後もmove: nullを返すので後方互換)。
export interface Explanation {
  id: string;
  stage: ExplanationStage;
  purpose: string;
  move: string | null;
  reason: string;
  refers_to_shape_id: string | null;
  refers_to_intent_id: string | null;
  confidence_level: ConfidenceLevel;
  glossary_terms: string[];
  template_id: string;
}

const CONFIDENCE_ORDER: Record<ConfidenceLevel, number> = { low: 0, medium: 1, high: 2 };

/** dataの確信度(shapes/intentsのconfidence_level)を、検知状態に応じた上限で抑える。
 * candidateMoveExplanation.tsも同じ考え方(検知状態に応じて確信度の言い切りを抑える)を
 * 使うため、export して重複実装を避ける。 */
export function capConfidence(dataLevel: ConfidenceLevel, cap: ConfidenceLevel): ConfidenceLevel {
  return CONFIDENCE_ORDER[dataLevel] <= CONFIDENCE_ORDER[cap] ? dataLevel : cap;
}

// data/explanations/*.jsonサンプルにある、各ステージの定型purpose文をそのまま踏襲する
// (shape/intentの内容に依存しない、アプリ側の「なぜこの説明を見せるか」という目的文)。
// candidate_moveの文言はcandidateMoveExplanation.tsが参照する(将棋知識ではなく、
// アプリ側の目的説明という性格は他の3ステージと同じ)。
export const PURPOSE_TEMPLATES: Record<ExplanationStage, string> = {
  current_shape:
    "今、自分の陣形がどんな形になっているかを知り、この先どんな囲いを目指せるかを考えるための土台にします。",
  opponent_intent: "相手が今どんな作戦で攻めようとしているかを把握し、慌てずに対応を考えるためです。",
  opponent_next_aim: "相手が次に何を狙ってきそうかを先読みし、今のうちに備えておくためです。",
  candidate_move:
    "自分が今目指している形に近づく手の候補を知り、次に何を指すか考えるための材料にするためです。",
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
type RawStatus = ShapeFormationResult["status"] | IntentDetectionResult["matchStatus"];

interface StageResult {
  explanation: Explanation;
  status: RawStatus;
}

function buildCurrentShapeStage(shapeResults: ShapeFormationResult[]): StageResult {
  // status==="none"(shape_formation_evidenceが無い、偶然の一致を含む)は
  // 「報告に値する候補」から除外する。matchScoreだけで選ぶと、初期配置の駒が
  // たまたま必須マスと一致しているだけの形を「作ろうとしている可能性がある」と
  // 誤って断定してしまう(Unit4のブラウザ実地確認で発見された問題への対応)。
  const best = pickBest(shapeResults.filter((r) => r.status !== "none"));

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

// Phase4: forcedOpponentOpening/scenarioOpponentOpeningの強制進行フェーズでは、
// intentDetector.tsの3件が全てnoneになることが構造上ほぼ必ず起きる
// (data/intents/*.jsonのrecognition_patternは、強制進行の機械的な手順とは
// 無関係なため)。この場合に限り、将棋上の意図を推測するのではなく、
// 「直近の相手の手はシステムの決まった手順によるものである」という、
// wasLastOpponentMoveForced(呼び出し元が確定させた事実)だけをそのまま説明する。
// intentが1件でも検出されている場合(best !== undefined)は、この文言は一切使わず
// 既存のintent説明を必ず優先する(呼び出し側の分岐、下記参照)。
const OPPONENT_UNCLASSIFIED_FORCED_OPENING_REASON =
  "相手の今の手は、対局序盤の決まった手順によるものです。そのため、狙いはまだ判定できません。";

function buildOpponentIntentStage(
  intentResults: IntentDetectionResult[],
  wasLastOpponentMoveForced: boolean = false,
): StageResult {
  const best = pickBest(intentResults);

  if (!best) {
    return {
      status: "none",
      explanation: {
        id: "runtime_opponent_intent_unclassified",
        stage: "opponent_intent",
        purpose: PURPOSE_TEMPLATES.opponent_intent,
        move: null,
        reason: wasLastOpponentMoveForced
          ? OPPONENT_UNCLASSIFIED_FORCED_OPENING_REASON
          : "相手の狙いは、まだはっきりとは分かりません。特定の作戦を決めつけず、もう少し様子を見てみましょう。",
        refers_to_shape_id: null,
        refers_to_intent_id: null,
        confidence_level: "low",
        glossary_terms: [],
        template_id: wasLastOpponentMoveForced
          ? "opponent_intent_unclassified_forced_opening"
          : "opponent_intent_unclassified",
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

function buildOpponentNextAimStage(
  intentResults: IntentDetectionResult[],
  wasLastOpponentMoveForced: boolean = false,
): StageResult {
  const best = pickBest(intentResults);

  if (!best) {
    return {
      status: "none",
      explanation: {
        id: "runtime_opponent_next_aim_unclassified",
        stage: "opponent_next_aim",
        purpose: PURPOSE_TEMPLATES.opponent_next_aim,
        move: null,
        reason: wasLastOpponentMoveForced
          ? OPPONENT_UNCLASSIFIED_FORCED_OPENING_REASON
          : "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
        refers_to_shape_id: null,
        refers_to_intent_id: null,
        confidence_level: "low",
        glossary_terms: [],
        template_id: wasLastOpponentMoveForced
          ? "opponent_next_aim_unclassified_forced_opening"
          : "opponent_next_aim_unclassified",
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

function buildStages(
  shapeResults: ShapeFormationResult[],
  intentResults: IntentDetectionResult[],
  wasLastOpponentMoveForced: boolean = false,
): StageResult[] {
  return [
    buildCurrentShapeStage(shapeResults),
    buildOpponentIntentStage(intentResults, wasLastOpponentMoveForced),
    buildOpponentNextAimStage(intentResults, wasLastOpponentMoveForced),
  ];
}

/**
 * Unit5(analyzeShapeFormation)・Unit2(detectIntents)の判定結果から、
 * 「現在の形 -> 相手の意図 -> 相手の次の狙い」の順で3件の説明(Explanation)を組み立てる。
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function generateExplanations(
  shapeResults: ShapeFormationResult[],
  intentResults: IntentDetectionResult[],
  wasLastOpponentMoveForced: boolean = false,
): Explanation[] {
  return buildStages(shapeResults, intentResults, wasLastOpponentMoveForced).map((s) => s.explanation);
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
  shapeResults: ShapeFormationResult[],
  intentResults: IntentDetectionResult[],
  wasLastOpponentMoveForced: boolean = false,
): CoachExplanation[] {
  return buildStages(shapeResults, intentResults, wasLastOpponentMoveForced).map((s) => ({
    ...s.explanation,
    status: s.status,
  }));
}

export interface ExplainPositionOptions extends DetectIntentsOptions, AnalyzeShapeFormationOptions {}

/**
 * SFEN + 指し手履歴から、Unit5(analyzeShapeFormation)/Unit2(detectIntents)を
 * 呼び出したうえで説明を組み立てる統合用の入口。
 * (Web API層など、判定結果を個別に扱う必要がない呼び出し元向けの利便関数)
 */
export function explainPosition(
  sfen: string,
  moveHistory: string[],
  options: ExplainPositionOptions = {},
  wasLastOpponentMoveForced: boolean = false,
): Explanation[] {
  const shapeResults = analyzeShapeFormation(sfen, moveHistory, options);
  const intentResults = detectIntents(sfen, moveHistory, options);
  return generateExplanations(shapeResults, intentResults, wasLastOpponentMoveForced);
}

/**
 * explainPositionのstatus付き版。apps/server/src/server.ts(HTTP API)が、
 * UI側でforming/matched/completed/noneのバッジ表示を出し分けるために使う。
 *
 * wasLastOpponentMoveForced(Phase4): 呼び出し元(api/stateResponse.ts)が
 * GameState.wasLastOpponentMoveForcedをそのまま渡す想定の追加引数。省略時はfalse
 * (既存呼び出し元の挙動を変えない)。
 */
export function explainPositionWithStatus(
  sfen: string,
  moveHistory: string[],
  options: ExplainPositionOptions = {},
  wasLastOpponentMoveForced: boolean = false,
): CoachExplanation[] {
  const shapeResults = analyzeShapeFormation(sfen, moveHistory, options);
  const intentResults = detectIntents(sfen, moveHistory, options);
  return generateCoachExplanations(shapeResults, intentResults, wasLastOpponentMoveForced);
}
