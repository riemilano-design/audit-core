// pathPlanner.ts(⑦候補手の前半)+ candidateMoveSafetyCheck.ts(MultiPVとの対応付け)の
// 結果から、⑧「その手の目的」の説明(Explanation, stage: "candidate_move")への接続を
// 準備するモジュール。
//
// 【現時点でこのモジュールが実際に行うこと(重要)】
// 事前調査の結果、CLAUDE.md/docs/PHASES.md/docs/ROLES.mdのいずれにも「エンジン評価上
// 何が"明らかな悪手"か」という具体的な閾値(cp差・mate距離・MultiPV順位等)の定義が
// 存在しないことを確認した。そのため本モジュールは、そのような閾値による判定を
// 一切行わない。candidateMoveSafetyCheck.tsのengineReferenceAvailableは
// 「エンジンによる参考評価を取得でき、candidateMovesとの対応付けが確認できた」
// という機械的事実だけを表し、「安全」「悪手ではない」という判定を意味しない。
// 本モジュールはこの機械的事実だけを根拠に、候補手の説明を出す/出さないを決める:
//   - safetyCheck.engineReferenceAvailable が false の場合、候補手の説明
//     (Explanation)は1件も生成しない(= 呼び出し側のUI表示対象に一切乗らない)。
//   - engineReferenceAvailable が true でも、個々の候補手についてscoreつきの
//     MultiPV行が1件も得られなかった場合(エンジンの中断・タイムアウト等で
//     評価が不十分だった場合を含む)は、その候補**だけ**を説明対象から除外する
//     (他の候補に評価データがあれば、それらは引き続き説明される)。
//   - 「安全です」「おすすめです」「この手が正解です」といった断定は行わない。
//     生成される文言は常に以下の範囲に留める(ユーザー指示で明示された言い回し。
//     新しい将棋知識・断定は追加しない):
//       「この形を目指す進め方の一例です」
//       「この手には、○○の形を作るという目的があります」
//       「この形へ近づける手の候補の一つです」
//   - typical_build_orderは唯一の正解手順として扱わない
//     (pathPlanner.tsのファイル冒頭コメントと同じ方針)。
//   - エンジンのscore(cp/mate)そのものは説明文に含めない(「安全性の参考情報」を
//     初心者向けの断定ラベルへ変換しない)。
//
// 【スキーマについて】
// data/schemas/explanations.schema.json のstage enumには元々"candidate_move"が
// 含まれており、moveフィールドも用意されている。したがってスキーマ変更は不要。
// TypeScript側のExplanationStage型のみ、スキーマに合わせてexplanationGenerator.tsで
// 追加済み(本ファイルでは変更しない)。
//
// 【既存モジュールとの関係】
// pathPlanner.ts / candidateMoveSafetyCheck.ts / explanationGenerator.tsの
// 公開インターフェースはいずれも変更していない(explanationGenerator.tsは
// ExplanationStage型の追加値とPURPOSE_TEMPLATES/capConfidenceのexportのみ)。

import {
  capConfidence,
  PURPOSE_TEMPLATES,
  type ConfidenceLevel,
  type Explanation,
} from "./explanationGenerator.js";
import type { CandidateMoveSafetyCheckResult } from "./candidateMoveSafetyCheck.js";
import type { PathPlanCandidateMove, PathPlanResult } from "./pathPlanner.js";
import type { RouteCandidateMove, ShapeRoutePlanResult } from "./routePlanner.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { toJapaneseSquare, toJapaneseSquarePath } from "../notation/japaneseSquare.js";

export type CandidateMoveExplanationStatus = "not_ready" | "ready";

export type CandidateMoveExplanationNotReadyReason =
  /** pathPlanner.tsが候補手を1つも返していない(PathPlanResult.candidateMovesが空)。 */
  | "no_candidate_moves"
  /** pathPlanResult.shapeIdに対応するShapeFormationResultが見つからない。 */
  | "shape_result_not_found"
  /**
   * candidateMoveSafetyCheck.tsのengineReferenceAvailableがfalse
   * (=エンジンによる参考評価を取得・対応付けできなかった)。
   */
  | "engine_reference_unavailable"
  /**
   * engineReferenceAvailableはtrueだったが、候補手全件についてscoreつきの
   * MultiPV行が1件も得られず(エンジンの中断・タイムアウト等)、
   * 説明できる候補が1件も残らなかった。
   */
  | "insufficient_engine_data";

export interface CandidateMoveExplanationResult {
  status: CandidateMoveExplanationStatus;
  /** status: "ready"の場合はnull。 */
  notReadyReason: CandidateMoveExplanationNotReadyReason | null;
  /**
   * ユーザーに提示してよい候補手の説明(stage: "candidate_move")。
   * status: "not_ready"の場合は常に空配列(=UI表示対象から除外される)。
   */
  explanations: Explanation[];
}

function notReady(reason: CandidateMoveExplanationNotReadyReason): CandidateMoveExplanationResult {
  return { status: "not_ready", notReadyReason: reason, explanations: [] };
}

/** ⑦の候補手1件を、⑧「その手の目的」の説明(Explanation)へ変換する。 */
export function buildCandidateMoveExplanation(
  pathPlanResult: Pick<PathPlanResult, "shapeId" | "targetSquare" | "targetPiece">,
  shapeResult: Pick<ShapeFormationResult, "name" | "dataConfidenceLevel">,
  candidate: PathPlanCandidateMove,
): Explanation {
  const shapeName = shapeResult.name;
  const targetPiece = pathPlanResult.targetPiece;
  const targetSquare = pathPlanResult.targetSquare;

  // このモジュールは常にpathPlanner.tsが候補を返した(=targetSquare/targetPieceが
  // 確定している)状態でのみ呼ばれる(explainCandidateMoves側でno_candidate_movesを
  // 先に弾いているため)。それでも型上nullがあり得るため、文言は安全側に倒す。
  const targetDescription =
    targetPiece && targetSquare ? `${targetPiece}を${targetSquare}へ動かして` : "";

  // ユーザー指示で明示された言い回し(「この形を目指す進め方の一例です」
  // 「この手には、○○の形を作るという目的があります」「この形へ近づける手の
  // 候補の一つです」)の範囲に留める。「正解」「最善」「おすすめ」等は使わない。
  const reason =
    `${shapeName}へ近づける手の候補の一つです。この手には、${targetDescription}` +
    `${shapeName}の形を作るという目的があります。` +
    `(これは${shapeName}を目指す進め方の一例であり、唯一の正解ではありません。)`;

  // 確信度は他ステージと同じ考え方(データ側の確信度を、検知状態に応じた上限で抑える)
  // を踏襲する。「候補」段階であり断定ではないため上限はmediumとする。
  const confidenceLevel: ConfidenceLevel = capConfidence(shapeResult.dataConfidenceLevel, "medium");

  return {
    id: `runtime_candidate_move_${pathPlanResult.shapeId}_${sanitizeForId(candidate.moveUsi)}`,
    stage: "candidate_move",
    purpose: PURPOSE_TEMPLATES.candidate_move,
    move: candidate.moveUsi,
    reason,
    refers_to_shape_id: pathPlanResult.shapeId,
    refers_to_intent_id: null,
    confidence_level: confidenceLevel,
    glossary_terms: [pathPlanResult.shapeId],
    template_id: "candidate_move_example",
  };
}

// Explanation.idはdata/schemas/explanations.schema.jsonのpattern "^[a-z0-9_]+$"に
// 従う必要がある。USI形式の指し手は"+"(成り)や"*"(打つ手、例: "P*5e")を含み得るため、
// idとして安全な文字列に変換する(move自体の値は変換しない。あくまでid生成用)。
function sanitizeForId(moveUsi: string): string {
  return moveUsi.toLowerCase().replace(/[^a-z0-9]/g, "_");
}

/** 候補手にscoreつきのMultiPV行が1件でもあれば「評価データが得られた」とみなす。
 * scoreの値そのものの良し悪しは一切見ない(=閾値判定ではなく、データの有無だけの
 * 機械的な判定)。stopによる早期終了でinfo行が1つも来なかった場合もここでfalseになる。 */
function hasUsableEvaluation(evaluation: { multiPv: { score: unknown }[] } | undefined): boolean {
  return evaluation !== undefined && evaluation.multiPv.some((line) => line.score !== undefined);
}

/**
 * pathPlanner.tsの候補手 + candidateMoveSafetyCheck.tsの参考評価結果から、
 * ユーザーに提示してよい候補手の説明(Explanation, stage: "candidate_move")を組み立てる。
 *
 * 【返り値の読み方】
 * - status: "not_ready" の場合、explanationsは常に空配列。呼び出し側(API/UI)は
 *   この場合、候補手を一切表示してはならない(CLAUDE.mdルール3番: 安全確認を経ていない
 *   候補手をユーザーに見せない)。
 * - status: "ready" の場合、evaluationsにscoreつきのMultiPV行が1件以上あった候補手
 *   だけがexplanationsに入る(評価データが得られなかった候補は個別に除外される。
 *   全て除外された場合はnot_ready/insufficient_engine_dataになる)。
 *
 * いずれの場合も、生成される説明はエンジンのscore自体を含まない
 * (「安全」「おすすめ」等の断定はしない。buildCandidateMoveExplanation参照)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function explainCandidateMoves(
  pathPlanResult: PathPlanResult,
  shapeResults: ShapeFormationResult[],
  safetyCheck: CandidateMoveSafetyCheckResult,
): CandidateMoveExplanationResult {
  if (pathPlanResult.candidateMoves.length === 0) {
    return notReady("no_candidate_moves");
  }

  const shapeResult = shapeResults.find((r) => r.shapeId === pathPlanResult.shapeId);
  if (!shapeResult) {
    return notReady("shape_result_not_found");
  }

  if (!safetyCheck.engineReferenceAvailable) {
    return notReady("engine_reference_unavailable");
  }

  // candidateMoves と safetyCheck.evaluations は同じ順序で1:1対応する
  // (candidateMoveSafetyCheck.tsの既存契約。新しい対応付けロジックは作らない)。
  const explanations = pathPlanResult.candidateMoves
    .map((candidate, index) => ({ candidate, evaluation: safetyCheck.evaluations[index] }))
    .filter(({ evaluation }) => hasUsableEvaluation(evaluation))
    .map(({ candidate }) => buildCandidateMoveExplanation(pathPlanResult, shapeResult, candidate));

  if (explanations.length === 0) {
    return notReady("insufficient_engine_data");
  }

  return { status: "ready", notReadyReason: null, explanations };
}

// ============================================================================
// Phase6 Unit1: routePlanner.ts(複数の未達成マス・複数手の経路)版の説明生成。
//
// 上のexplainCandidateMoves/buildCandidateMoveExplanation(Phase2、単一目標マス前提)は
// 一切変更していない。routePlanner.tsは1回の結果に複数の目標マスの候補手を含むため、
// 「どの目標マスへ向かう経路の何手目か」を候補手ごとに文章へ反映する必要がある。
//
// 【文言の方針(Phase2から変更なし)】
// 「安全です」「おすすめです」「この手が正解です」といった断定は行わない。
// エンジンのscore(cp/mate)そのものは説明文に含めない。
// typical_build_orderは唯一の正解手順として扱わない。
// 準備手については、退避先の良し悪しを判断していないことを文章で明示する
// (「どこへ動かすかは、この形の観点だけでは決まりません」)。
//
// 【座標表記】
// docs/DATA_MODEL.md「座標表記の規約」に従い、説明文中のマス目は
// notation/japaneseSquare.tsで日本語表記へ変換する(Explanation.moveの値自体は
// USI形式のまま。内部データの正規形式は変えない)。
// ============================================================================

/** 候補手の種類ごとのtemplate_id(explanations.schema.jsonのidパターンと同じ規約)。 */
const ROUTE_TEMPLATE_IDS = {
  route_step: "candidate_move_route_step",
  route_arrival: "candidate_move_route_arrival",
  preparation: "candidate_move_preparation",
} as const;

/** 「この形を目指す進め方の一例であり唯一の正解ではない」という共通の但し書き。 */
function exampleDisclaimer(shapeName: string): string {
  return `これは${shapeName}を目指す進め方の一例であり、唯一の正解ではありません。`;
}

/** ⑦の候補手1件(経路つき)を、⑧「その手の目的」の説明(Explanation)へ変換する。 */
export function buildRouteCandidateMoveExplanation(
  shapeId: string,
  shapeResult: Pick<ShapeFormationResult, "name" | "dataConfidenceLevel">,
  candidate: RouteCandidateMove,
): Explanation {
  const shapeName = shapeResult.name;
  const targetSquare = toJapaneseSquare(candidate.targetSquare);
  const routePath = toJapaneseSquarePath(candidate.routeSquares);

  let reason: string;
  let templateId: string;

  if (candidate.kind === "preparation") {
    const clearingSquare = toJapaneseSquare(candidate.clearingSquare ?? candidate.targetSquare);
    reason =
      `${clearingSquare}には今、自分の駒があります。` +
      `「${shapeName}」の${candidate.targetPiece}を${targetSquare}へ進めるには、` +
      `先にこの駒を動かす必要があります。この手はそのための候補の一つです。` +
      `(どこへ動かすかは、この形の観点だけでは決まりません。${exampleDisclaimer(shapeName)})`;
    templateId = ROUTE_TEMPLATE_IDS.preparation;
  } else if (candidate.remainingStepsAfter === 0) {
    reason =
      `この手で${candidate.targetPiece}が${targetSquare}に入り、` +
      `「${shapeName}」に必要な配置の一つができます。(${exampleDisclaimer(shapeName)})`;
    templateId = ROUTE_TEMPLATE_IDS.route_arrival;
  } else {
    reason =
      `「${shapeName}」の${candidate.targetPiece}を${targetSquare}へ運ぶ経路(${routePath})の1手目です。` +
      `この手のあと、${targetSquare}まで残り${candidate.remainingStepsAfter}手です。` +
      `(${exampleDisclaimer(shapeName)})`;
    templateId = ROUTE_TEMPLATE_IDS.route_step;
  }

  return {
    id: `runtime_candidate_move_${shapeId}_${sanitizeForId(candidate.moveUsi)}`,
    stage: "candidate_move",
    purpose: PURPOSE_TEMPLATES.candidate_move,
    move: candidate.moveUsi,
    reason,
    refers_to_shape_id: shapeId,
    refers_to_intent_id: null,
    // 確信度の考え方はPhase2版と同じ(データ側の確信度を、断定を避けるため
    // mediumで頭打ちにする)。
    confidence_level: capConfidence(shapeResult.dataConfidenceLevel, "medium"),
    glossary_terms: [shapeId],
    template_id: templateId,
  };
}

/**
 * routePlanner.tsの経路計画 + candidateMoveSafetyCheck.tsの参考評価結果から、
 * ユーザーに提示してよい候補手の説明を組み立てる。
 *
 * 返り値の読み方・エンジン参考評価の扱いは explainCandidateMoves と全く同じ
 * (status: "not_ready" のときは explanations が常に空で、UIは候補手を一切表示しない。
 * CLAUDE.mdルール3番)。
 *
 * routePlanResult.candidateMoves と safetyCheck.evaluations は同じ順序で1:1対応する
 * (呼び出し側が candidateMoves をそのまま checkCandidateMovesSafety へ渡す前提。
 * Phase2版と同じ契約であり、新しい対応付けロジックは作らない)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function explainRouteCandidateMoves(
  routePlanResult: ShapeRoutePlanResult,
  shapeResults: ShapeFormationResult[],
  safetyCheck: CandidateMoveSafetyCheckResult,
): CandidateMoveExplanationResult {
  if (routePlanResult.candidateMoves.length === 0) {
    return notReady("no_candidate_moves");
  }

  const shapeResult = shapeResults.find((r) => r.shapeId === routePlanResult.shapeId);
  if (!shapeResult) {
    return notReady("shape_result_not_found");
  }

  if (!safetyCheck.engineReferenceAvailable) {
    return notReady("engine_reference_unavailable");
  }

  const explanations = routePlanResult.candidateMoves
    .map((candidate, index) => ({ candidate, evaluation: safetyCheck.evaluations[index] }))
    .filter(({ evaluation }) => hasUsableEvaluation(evaluation))
    .map(({ candidate }) =>
      buildRouteCandidateMoveExplanation(routePlanResult.shapeId, shapeResult, candidate),
    );

  if (explanations.length === 0) {
    return notReady("insufficient_engine_data");
  }

  return { status: "ready", notReadyReason: null, explanations };
}
