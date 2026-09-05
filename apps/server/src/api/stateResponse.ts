// GameState -> HTTPレスポンス用オブジェクトの組み立て。
// server.tsから対局状態のレスポンス生成ロジックを切り出したもの(テスト容易性のため)。
// server.ts自体はHTTPサーバーの起動処理(server.listen/シグナルハンドラ登録)を
// importした時点で実行してしまうため、テストコードから直接importすると
// 実際にポート待受が発生する。この副作用を避けるため、レスポンス組み立てという
// テスト可能な部分のみをここに分離する(server.tsの既存の外部インターフェース・
// 挙動は変えていない)。

import {
  explainPositionWithStatus,
  type CoachExplanation,
  type ExplainPositionOptions,
} from "../analysis/explanationGenerator.js";
import { getStatus, type GameState, type GameStatus } from "../game/gameSession.js";
import { analyzeShapeFormation, type ShapeFormationResult } from "../analysis/shapeFormationAnalyzer.js";
import { detectIntents } from "../analysis/intentDetector.js";
import { selectTargetPurpose } from "../analysis/targetPurposeSelector.js";
import { rankReachableShapes, type RankedReachableShape } from "../analysis/shapeGraphRanking.js";
import { planPathToShape, type PathPlanResult } from "../analysis/pathPlanner.js";
import { checkCandidateMovesSafety } from "../analysis/candidateMoveSafetyCheck.js";
import {
  explainCandidateMoves,
  type CandidateMoveExplanationResult,
} from "../analysis/candidateMoveExplanation.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";

export interface StateResponseBody extends GameState {
  status: GameStatus;
  /**
   * Unit3(analysis/explanationGenerator.ts)による「現在の形・相手の意図・相手の次の狙い」の説明。
   * 説明生成の失敗時(想定外のデータ不整合等)はundefinedになる(対局自体は継続する)。
   */
  coach: CoachExplanation[] | undefined;
}

/**
 * candidateMoveの計算がどこまで進んでいるかを表す(⑦候補手・⑧説明はエンジンの
 * MultiPV参考評価を伴うため、着手のHTTPレスポンスをブロックせずバックグラウンドで
 * 計算する。docs/PHASES.md Phase2)。
 * - "unavailable": ⑥1位の形について、pathPlanner.tsが候補手を1つも返せない
 *   (=そもそも解析する対象が無い。バックグラウンド解析も行わない)
 * - "pending": 候補手はあるが、現在の局面(sfen)に対するバックグラウンド解析が
 *   まだ完了していない(=まだキャッシュに無い)
 * - "ready": 現在の局面(sfen)に対するバックグラウンド解析が完了し、結果が
 *   キャッシュされている。実際に表示してよい内容は`candidateMove`(その中の
 *   `status`)を見て判断する("ready"であっても`candidateMove.status`が
 *   "not_ready"のことがある。例: 評価データが不十分だった場合)
 */
export type CandidateMoveState = "unavailable" | "pending" | "ready";

export interface ReachablePlanBody {
  /** shapeGraphRankingの上位(最大3件)の「目指せる形」。1位を唯一の正解として
   * 強調しない前提で、呼び出し側(UI)は並列表示する。 */
  reachableShapes: RankedReachableShape[];
  candidateMoveState: CandidateMoveState;
  /** candidateMoveState: "ready"の場合のみ値を持つ。それ以外はundefined。 */
  candidateMove: CandidateMoveExplanationResult | undefined;
  /**
   * ⑦⑧の計算に実際に使われたshapeId(ユーザーが選択したものか、未選択/無効時の
   * フォールバックとしてranked[0]が採用されたものか、いずれか)。reachableShapesの
   * どれが現在の「目標」かをUI側でハイライトするために使う。目指せる形が1件も
   * 無い場合はnull。
   */
  resolvedTargetShapeId: string | null;
}

export interface StateResponseBodyWithPlan extends StateResponseBody {
  plan: ReachablePlanBody;
}

/** バックグラウンド解析の完了結果。どの局面(sfen)・どの目標形(targetShapeId)に
 * 対する結果かをserver.ts側で保持し、現在の対局状態のsfen・選択中の目標形の両方が
 * 一致する場合のみbuildStateResponseWithPlanへ渡す(stale result防止。新しいID体系は
 * 発明せず既存のsfenをそのまま、targetShapeIdは選択機能で新たに生じた次元として、
 * それぞれ世代識別子として使う)。
 *
 * targetShapeIdは「実際に採用された(resolvedTargetShapeId)」値であり、
 * ユーザーが指定した生の値そのものではない(未選択・無効時のranked[0]フォールバックも
 * 含む)。同じsfenでも目標形が変わればcandidateMovesの中身は変わり得るため、
 * sfenだけを世代識別子にすると古い目標形の結果を新しい目標形の結果として
 * 誤って返しかねない(このバグを避けるためのフィールド追加)。
 */
export interface CachedReachablePlan {
  sfen: string;
  targetShapeId: string | undefined;
  plan: {
    reachableShapes: RankedReachableShape[];
    candidateMove: CandidateMoveExplanationResult | undefined;
  };
}

interface RankedPlanContext {
  shapeResults: ShapeFormationResult[];
  /** shapeGraphRankingの上位3件。 */
  reachableShapes: RankedReachableShape[];
  /** 実際にpathPlanner.tsへ渡されたshapeId。reachableShapesが空ならundefined。
   * ユーザーが選択したshapeId(selectedTargetShapeId)がreachableShapesに含まれて
   * いればそれ、含まれない(未選択・無効値)場合はranked[0]にフォールバックした結果。 */
  resolvedTargetShapeId: string | undefined;
  /** resolvedTargetShapeIdについてのみ計算したpathPlanner結果。対象shapeが無ければundefined。 */
  pathPlanResult: PathPlanResult | undefined;
}

/**
 * ⑤自分の目的 → ⑥目指せる形のランキング → ⑦候補手生成を計算する。
 * いずれもエンジン不要・高速な純粋関数(targetPurposeSelector.ts / shapeGraphRanking.ts /
 * pathPlanner.ts、Phase2 Unit1/Unit2。ここでは一切変更しない)。
 * 例外はそのまま呼び出し元へ伝播する(呼び出し元がそれぞれ安全に扱う)。
 *
 * selectedTargetShapeIdは、ユーザーが目標形選択UIで選んだshapeId(任意)。
 * reachableShapes(上位3件)に含まれる場合のみ採用し、⑦の対象として使う。
 * 含まれない場合(未指定・無効なshapeId・対局が進んで候補から外れた等)は、
 * 従来通りranked[0]にフォールバックする(既存動作を変えない安全側の既定値)。
 */
function computeRankedPlanContext(
  current: GameState,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): RankedPlanContext {
  const shapeResults = analyzeShapeFormation(current.sfen, current.moveHistory, options);
  const intentResults = detectIntents(current.sfen, current.moveHistory, options);
  const targetPurpose = selectTargetPurpose(intentResults);
  const ranked = rankReachableShapes(shapeResults, targetPurpose);
  // docs/PHASES.mdが明記する「ユーザーが2〜3個の候補から目標形を選べるUI」に基づく件数。
  const reachableShapes = ranked.slice(0, 3);
  const selected =
    selectedTargetShapeId !== undefined
      ? reachableShapes.find((s) => s.shapeId === selectedTargetShapeId)
      : undefined;
  const top = selected ?? ranked[0];
  const resolvedTargetShapeId = top?.shapeId;
  const pathPlanResult = top ? planPathToShape(current.sfen, shapeResults, top.shapeId) : undefined;
  return { shapeResults, reachableShapes, resolvedTargetShapeId, pathPlanResult };
}

// 説明生成は対局の合法性判定とは独立した機能である。ここで万一例外が起きても
// (想定外のデータ不整合等)、対局そのもの(盤面・指し手)は止めない
// (docs/PHASES.md Phase1完了条件「無言・エラーにならない」を、コーチ機能自体の
// 障害からも守るための最後の防御線)。
export function safeExplainPosition(
  current: GameState,
  options: ExplainPositionOptions = {},
): CoachExplanation[] | undefined {
  try {
    return explainPositionWithStatus(current.sfen, current.moveHistory, options);
  } catch (err) {
    console.error("説明生成(analysis/explanationGenerator.ts)でエラーが発生しました:", err);
    return undefined;
  }
}

// options.initialSfenは実サーバー(server.ts)では常に既定値(標準初期局面)のまま使う
// (対局は常にstartposから始まるため)。テストコードが、実際の対局進行を経ずに
// 特定の局面を直接検証したい場合にのみ上書きする(analysis/intentDetector.tsの
// sfen/moveHistory整合性チェックを、任意の盤面に対しても有効なまま使うため)。
export function buildStateResponse(current: GameState, options: ExplainPositionOptions = {}): StateResponseBody {
  return { ...current, status: getStatus(current), coach: safeExplainPosition(current, options) };
}

/** ⑤⑥⑦の計算(エンジン不要)も、Phase1のcoach同様に失敗を対局本体へ波及させない。 */
function safeComputeRankedPlanContext(
  current: GameState,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): RankedPlanContext | undefined {
  try {
    return computeRankedPlanContext(current, options, selectedTargetShapeId);
  } catch (err) {
    console.error("目指せる形/候補手のランキング計算(⑤⑥⑦)でエラーが発生しました:", err);
    return undefined;
  }
}

/**
 * 既存の同期buildStateResponse()は一切変更しない(GET /api/game・
 * POST /api/game/newはこれを使い続ける)。本関数は、それに加えて⑤⑥⑦(同期・
 * エンジン不要)と、既にバックグラウンドで完了・キャッシュされている⑧候補手説明
 * (cachedPlan、あれば)を合成して返す、新規の同期関数。
 *
 * cachedPlanが現在の局面(current.sfen)・現在採用中の目標形(resolvedTargetShapeId)の
 * いずれかと一致しない場合は使わない(stale result防止。新しいID体系は発明せず、
 * 既存のsfenと、目標形選択機能で新たに生じたtargetShapeIdを、それぞれ世代識別子として
 * 使う。同じsfenでも目標形が変われば候補手の中身は変わるため、sfenだけの比較では
 * 「目標形を変えた直後、古い目標形の候補手が一瞬表示される」不整合が起こり得る)。
 *
 * MultiPVによるエンジン参考評価そのものはここでは一切行わない
 * (POST /api/game/moveのレスポンスをブロックしないため。server.tsが別途
 * バックグラウンドでcomputeReachablePlan/safeComputeReachablePlanを実行し、
 * 完了した結果だけをcachedPlanとして次回以降ここへ渡す)。
 *
 * selectedTargetShapeIdは、目標形選択UI(POST /api/game/target-shape)で
 * ユーザーが選んだshapeId。省略時・reachableShapesに含まれない値の場合は
 * computeRankedPlanContext側でranked[0]にフォールバックする。
 */
export function buildStateResponseWithPlan(
  current: GameState,
  cachedPlan: CachedReachablePlan | undefined,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): StateResponseBodyWithPlan {
  const base = buildStateResponse(current, options);
  const context = safeComputeRankedPlanContext(current, options, selectedTargetShapeId);
  const reachableShapes = context?.reachableShapes ?? [];
  const resolvedTargetShapeId = context?.resolvedTargetShapeId ?? null;
  const hasCandidateMoves = (context?.pathPlanResult?.candidateMoves.length ?? 0) > 0;

  let candidateMoveState: CandidateMoveState;
  let candidateMove: CandidateMoveExplanationResult | undefined;

  if (!hasCandidateMoves) {
    // pathPlanner.tsが対象の形について候補手を1つも返せない(=解析する対象が無い)。
    candidateMoveState = "unavailable";
    candidateMove = undefined;
  } else if (
    cachedPlan &&
    cachedPlan.sfen === current.sfen &&
    cachedPlan.targetShapeId === context?.resolvedTargetShapeId
  ) {
    // 現在の局面・現在の目標形の組み合わせに対するバックグラウンド解析が
    // 既に完了・キャッシュされている。
    candidateMoveState = "ready";
    candidateMove = cachedPlan.plan.candidateMove;
  } else {
    // 候補手はあるが、現在の局面・目標形の組み合わせに対する解析がまだ完了していない
    // (または、目標形が変わった直後で古いキャッシュがstaleになった)。
    candidateMoveState = "pending";
    candidateMove = undefined;
  }

  return { ...base, plan: { reachableShapes, candidateMoveState, candidateMove, resolvedTargetShapeId } };
}

/**
 * ⑤⑥⑦(同期)に続けて、⑦候補手が1件以上あれば⑧(candidateMoveSafetyCheck.tsの
 * MultiPV参考評価 → candidateMoveExplanation.tsの説明生成)まで非同期で計算する。
 * POST /api/game/moveのHTTPレスポンスは待たない、バックグラウンド実行専用の入口
 * (server.tsがfire-and-forgetで呼ぶ)。
 *
 * 例外はそのまま伝播する(呼び出し元のsafeComputeReachablePlanが処理する)。
 *
 * selectedTargetShapeIdの扱いはbuildStateResponseWithPlanと同じ
 * (computeRankedPlanContext参照)。戻り値のtargetShapeIdは、実際に採用された
 * (フォールバック後の)shapeIdであり、呼び出し元(server.ts)がCachedReachablePlanの
 * 世代識別子として保持する。
 */
export async function computeReachablePlan(
  current: GameState,
  engine: LowPriorityEngine,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): Promise<{
  reachableShapes: RankedReachableShape[];
  candidateMove: CandidateMoveExplanationResult | undefined;
  targetShapeId: string | undefined;
}> {
  const context = computeRankedPlanContext(current, options, selectedTargetShapeId);
  const pathPlanResult = context.pathPlanResult;

  if (!pathPlanResult || pathPlanResult.candidateMoves.length === 0) {
    return {
      reachableShapes: context.reachableShapes,
      candidateMove: undefined,
      targetShapeId: context.resolvedTargetShapeId,
    };
  }

  const safetyCheck = await checkCandidateMovesSafety(current.sfen, pathPlanResult.candidateMoves, engine);
  const candidateMove = explainCandidateMoves(pathPlanResult, context.shapeResults, safetyCheck);
  return { reachableShapes: context.reachableShapes, candidateMove, targetShapeId: context.resolvedTargetShapeId };
}

/**
 * computeReachablePlanの安全側ラッパー(safeExplainPositionと同じパターン)。
 * バックグラウンド解析の失敗(エンジンタイムアウト・想定外のデータ不整合等)は
 * console.errorするだけに留め、対局進行には一切影響させない。
 */
export async function safeComputeReachablePlan(
  current: GameState,
  engine: LowPriorityEngine,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): Promise<
  | { reachableShapes: RankedReachableShape[]; candidateMove: CandidateMoveExplanationResult | undefined; targetShapeId: string | undefined }
  | undefined
> {
  try {
    return await computeReachablePlan(current, engine, options, selectedTargetShapeId);
  } catch (err) {
    console.error("候補手プラン計算(⑧, candidateMoveSafetyCheck/candidateMoveExplanation)でエラーが発生しました:", err);
    return undefined;
  }
}
