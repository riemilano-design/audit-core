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
import { planRoutesToShape, type ShapeRoutePlanResult } from "../analysis/routePlanner.js";
import { checkCandidateMovesSafety } from "../analysis/candidateMoveSafetyCheck.js";
import {
  explainRouteCandidateMoves,
  type CandidateMoveExplanationResult,
} from "../analysis/candidateMoveExplanation.js";
import { toJapaneseMoveSquares, toJapaneseSquare, toJapaneseSquarePath } from "../notation/japaneseSquare.js";
import { detectPlanChange, type PlanSnapshot } from "../analysis/planChangeDetector.js";
import { classifyPlanChangeReason, type PlanChangeReason } from "../analysis/planChangeReason.js";
import {
  detectMoveOutcome,
  type MoveOutcome,
  type MoveOutcomeSnapshot,
} from "../analysis/moveOutcomeDetector.js";
import { explainMoveOutcome, type MoveOutcomeMessage } from "../analysis/moveOutcomeExplanation.js";
import { detectBoardEvents, type BoardEvent } from "../analysis/boardEventDetector.js";
import { detectNextConsiderations } from "../analysis/nextConsiderationDetector.js";
import {
  explainNextConsiderations,
  type NextConsiderationMessage,
} from "../analysis/nextConsiderationExplanation.js";
import { explainBoardEvents, type BoardEventMessage } from "../analysis/boardEventExplanation.js";
import { getLegalMoves } from "../rules/legalMoves.js";
import { isInCheck } from "../rules/gameStatus.js";
import { toJapaneseMoveHistory } from "../notation/japaneseMoveHistory.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";

export type { PlanSnapshot } from "../analysis/planChangeDetector.js";
export type { PlanChangeReason } from "../analysis/planChangeReason.js";
export type { MoveOutcome } from "../analysis/moveOutcomeDetector.js";
export type { BoardEvent } from "../analysis/boardEventDetector.js";
export type { NextConsiderationMessage } from "../analysis/nextConsiderationExplanation.js";

export interface StateResponseBody extends GameState {
  status: GameStatus;
  /**
   * Unit3(analysis/explanationGenerator.ts)による「現在の形・相手の意図・相手の次の狙い」の説明。
   * 説明生成の失敗時(想定外のデータ不整合等)はundefinedになる(対局自体は継続する)。
   */
  coach: CoachExplanation[] | undefined;
  /**
   * Phase5: 現在の局面(current.sfen)における、現在の手番の合法手一覧(USI形式)。
   * rules/legalMoves.ts の getLegalMoves をそのまま呼んだ結果であり、判定ロジックは
   * 一切ここに持たない(盤面クリックUIが移動先/打てるマスを求めるために使う配線のみ)。
   */
  legalMoves: string[];
  /**
   * Phase5: moveHistory(USI形式)の各手を、notation/japaneseMoveHistory.ts(shogiops標準の
   * makeJapaneseMoveOrDropをそのまま利用)で日本語棋譜表記へ変換したもの。
   * moveHistoryと同じ並び・同じ長さ。変換できなかった手はnull(UI側がUSI表記へ
   * フォールバックする)。棋譜表記の生成ロジックはここには一切持たない(配線のみ)。
   */
  moveHistoryJapanese: (string | null)[];
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

/**
 * Phase6 Unit1: 選択中の形について「今どこまで出来ているか」をUIが表示するための情報。
 * shapeFormationAnalyzer.tsの判定結果(matchedSquares/missingSquares)をそのまま
 * 日本語表記へ変換して渡すだけで、新しい判定は一切行わない。
 */
export interface TargetShapeProgress {
  shapeId: string;
  name: string;
  /** 既にその形の一部として成立しているマス(日本語表記、例: "６九") */
  matchedSquareLabels: string[];
  /** まだ埋まっていないマス(日本語表記) */
  missingSquareLabels: string[];
}

/**
 * Phase6 Unit1: 未達成マス1つ分の経路(UI表示用の要約)。
 * routePlanner.tsのShapeSquareRouteから、UIが「選択した形 → 必要なマス →
 * 現在の局面からの経路 → 今指せる最初の一手」という因果を示すために必要な項目だけを
 * 抜き出したもの(判定・計算はここでは一切行わない)。
 */
export interface ShapeRouteSummary {
  /** 目標マス(USI形式。識別用) */
  targetSquare: string;
  /** 目標マスに置く駒種(日本語表記、data/shapes/*.jsonそのまま) */
  targetPiece: string;
  /** 目標マス(日本語表記、例: "８八") */
  targetSquareLabel: string;
  /** 経路(日本語表記、例: "５九→６八→７八→８八") */
  routeLabel: string;
  /** 目標マスまでの残り手数 */
  remainingSteps: number;
  /** 経路の1手目を現在の局面で指せるか */
  hasPlayableFirstMove: boolean;
  /** 経路上で最初に自分の駒が居るマス(日本語表記)。無ければnull。 */
  blockingSquareLabel: string | null;
}

/**
 * Phase6 Unit2: 直前の一手で何が変わったかの表示用データ。
 * 事実の抽出はanalysis/moveOutcomeDetector.ts、文言はanalysis/moveOutcomeExplanation.tsが
 * 担当し、ここでは表示用の入れ物にまとめるだけ(判定・文言生成は持たない)。
 */
export interface LastMoveOutcomeBody {
  /** ユーザーの着手(日本語棋譜表記。変換できない場合はマス目表記へフォールバック) */
  playedMoveLabel: string;
  /** 相手の応手。相手が指していない場合はnull。 */
  opponentMoveLabel: string | null;
  /**
   * 表示するメッセージ。変化が無かった場合も「特に変化なし」の1件が入る(空にはならない)。
   * Phase6 Unit3で、盤面の出来事(捕獲・王手・成り)のメッセージが先頭に加わる
   * (起きた順。形・経路についての説明はその後ろ)。
   */
  messages: (BoardEventMessage | MoveOutcomeMessage)[];
}

export interface ReachablePlanBody {
  /** shapeGraphRankingの上位(最大3件)の「目指せる形」。1位を唯一の正解として
   * 強調しない前提で、呼び出し側(UI)は並列表示する。 */
  reachableShapes: RankedReachableShape[];
  /**
   * Phase6 Unit1: 選択中の形の未達成マスごとの経路。routePlanner.tsの結果をそのまま
   * 要約したもの(候補手が表示される理由をユーザーが追跡できるようにするための情報)。
   * 経路を計算できない場合・選択中の形が無い場合は空配列。
   */
  routes: ShapeRouteSummary[];
  /**
   * Phase6 Unit1: 選択中の形が今どこまで出来ているか。選択中の形が無い場合はnull。
   */
  targetShapeProgress: TargetShapeProgress | null;
  /**
   * Phase6 Unit1: 候補手(USI形式)→ マス目の日本語表記("５九→６八")の対応表。
   * UIが候補手を日本語で表示するためのもの(docs/DATA_MODEL.mdの座標表記の規約に従い、
   * 変換はサーバー側のnotation/japaneseSquare.tsに集約し、web側に重複させない)。
   */
  candidateMoveLabels: Record<string, string>;
  /**
   * Phase6 Unit2: 直前の一手で何が変わったか。新規対局直後・目標形変更直後・
   * 比較できない場合はnull(前の状態についての誤った差分説明を残さないため)。
   */
  lastMoveOutcome: LastMoveOutcomeBody | null;
  /**
   * Phase6 Unit4: 現在の局面について分かっていること(直前の一手による差分ではない)。
   * 事実の抽出はanalysis/nextConsiderationDetector.ts、文言は
   * analysis/nextConsiderationExplanation.tsが担当し、ここでは配線するだけ。
   * 表示すべき事実が無い場合・目標形が決まっていない場合・対局終了時は空配列
   * (呼び出し側はブロックごと描画しない)。
   */
  nextConsiderations: NextConsiderationMessage[];
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
  /**
   * Phase3 Unit1(計画崩れの検知のみ): 相手の手によって、ユーザーが着手する直前に
   * 保持していた計画(PlanSnapshot)の前提が機械的に崩れたかどうか。
   * 判定条件はplanChangeDetector.ts参照(候補Aのみ、人間承認済み)。
   */
  planChanged: boolean;
  /**
   * Phase3 Unit2(崩れた理由の分類のみ、人間承認済み): planChangeReason.ts参照。
   * planChanged===falseの場合は常にnull。事実として断定できない場合は
   * "unknown"になる(「候補手が非合法になった」ことを無条件に「相手が原因」と
   * 断定しないため)。再計画ロジックの新規実装は行わない(Phase2の既存の
   * ⑤⑥⑦⑧再計算がそのまま新しい候補手として使われる)。
   */
  planChangeReason: PlanChangeReason | null;
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
  /** 実際にroutePlanner.tsへ渡されたshapeId。reachableShapesが空ならundefined。
   * ユーザーが選択したshapeId(selectedTargetShapeId)がreachableShapesに含まれて
   * いればそれ、含まれない(未選択・無効値)場合はranked[0]にフォールバックした結果。 */
  resolvedTargetShapeId: string | undefined;
  /** resolvedTargetShapeIdについてのみ計算したroutePlanner結果。対象shapeが無ければundefined。 */
  routePlanResult: ShapeRoutePlanResult | undefined;
}

/**
 * ⑤自分の目的 → ⑥目指せる形のランキング → ⑦候補手生成を計算する。
 * いずれもエンジン不要・高速な純粋関数(targetPurposeSelector.ts / shapeGraphRanking.ts /
 * routePlanner.ts)。例外はそのまま呼び出し元へ伝播する(呼び出し元がそれぞれ安全に扱う)。
 *
 * Phase6 Unit1で、⑦の候補手生成をpathPlanner.ts(単一目標マス・1手先読み)から
 * routePlanner.ts(複数の未達成マス・複数手の経路)へ切り替えた。pathPlanner.ts自体は
 * 温存しており(削除も変更もしていない)、この呼び出し経路から使わなくなっただけである。
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
  const routePlanResult = top ? planRoutesToShape(current.sfen, shapeResults, top.shapeId) : undefined;
  return { shapeResults, reachableShapes, resolvedTargetShapeId, routePlanResult };
}

/** routePlanner.tsの経路を、UI表示用の要約(日本語表記つき)へ変換するだけの関数。 */
function toRouteSummaries(routePlanResult: ShapeRoutePlanResult | undefined): ShapeRouteSummary[] {
  if (!routePlanResult) return [];
  return routePlanResult.routes.map((route) => ({
    targetSquare: route.targetSquare,
    targetPiece: route.targetPiece,
    targetSquareLabel: toJapaneseSquare(route.targetSquare),
    routeLabel: toJapaneseSquarePath(route.routeSquares),
    remainingSteps: route.remainingSteps,
    hasPlayableFirstMove: route.firstMoveUsis.length > 0,
    blockingSquareLabel: route.blockingSquare === null ? null : toJapaneseSquare(route.blockingSquare),
  }));
}

/** RankedPlanContextを、moveOutcomeDetector.tsが比較に使うスナップショットへ変換する。 */
function toMoveOutcomeSnapshot(context: RankedPlanContext): MoveOutcomeSnapshot {
  const shapeResult = context.shapeResults.find((r) => r.shapeId === context.resolvedTargetShapeId);
  return {
    targetShapeId: context.resolvedTargetShapeId,
    matchedSquares: shapeResult?.matchedSquares ?? [],
    routes: context.routePlanResult?.routes ?? [],
    candidateMoves: context.routePlanResult?.candidateMoves ?? [],
  };
}

/**
 * 直前の一手の表示ラベルを決める。
 * 指し手履歴の日本語棋譜表記(notation/japaneseMoveHistory.ts)が使える場合はそれを使い、
 * 使えない場合のみマス目表記へフォールバックする。履歴の末尾がMoveOutcomeの
 * 指し手と一致することを確認してから使う(古い結果に別の手の表記を付けないため)。
 */
function resolveMoveLabels(
  moveHistory: string[],
  moveHistoryJapanese: (string | null)[],
  outcome: MoveOutcome,
): Pick<LastMoveOutcomeBody, "playedMoveLabel" | "opponentMoveLabel"> {
  const last = moveHistory.length - 1;
  const fallbackPlayed = toJapaneseMoveSquares(outcome.playedMoveUsi);
  const fallbackOpponent =
    outcome.opponentMoveUsi === null ? null : toJapaneseMoveSquares(outcome.opponentMoveUsi);

  if (outcome.opponentMoveUsi !== null) {
    const matches =
      moveHistory[last] === outcome.opponentMoveUsi && moveHistory[last - 1] === outcome.playedMoveUsi;
    return {
      playedMoveLabel: (matches ? moveHistoryJapanese[last - 1] : null) ?? fallbackPlayed,
      opponentMoveLabel: (matches ? moveHistoryJapanese[last] : null) ?? fallbackOpponent,
    };
  }

  const matches = moveHistory[last] === outcome.playedMoveUsi;
  return {
    playedMoveLabel: (matches ? moveHistoryJapanese[last] : null) ?? fallbackPlayed,
    opponentMoveLabel: null,
  };
}

/** 候補手のUSI表記を、UI表示用の日本語のマス目表記へ変換した対応表を作る。 */
function toCandidateMoveLabels(routePlanResult: ShapeRoutePlanResult | undefined): Record<string, string> {
  const labels: Record<string, string> = {};
  for (const candidate of routePlanResult?.candidateMoves ?? []) {
    labels[candidate.moveUsi] = toJapaneseMoveSquares(candidate.moveUsi);
  }
  return labels;
}

/**
 * Phase6 Unit4: 現在局面について分かっていることを組み立てる。
 *
 * 判定・文言生成は一切ここに持たない(事実はnextConsiderationDetector.ts、文言は
 * nextConsiderationExplanation.tsの責務)。ここで行うのは、既に計算済みの
 * RankedPlanContext・対局状態・王手(rules/gameStatus.tsのisInCheck)を渡す配線だけ。
 *
 * 自分側の色は、既存のShapeFormationResult.perspectiveColorをそのまま使う
 * (新しい色判定ロジックは作らない)。
 *
 * Phase1のcoachやPhase6 Unit1〜3と同様、ここでの失敗を対局本体へ波及させない
 * (失敗時は空配列=ブロック非表示に落とす)。
 */
function toNextConsiderations(
  current: GameState,
  context: RankedPlanContext | undefined,
  isGameEnd: boolean,
): NextConsiderationMessage[] {
  if (!context?.resolvedTargetShapeId) return [];
  const shapeResult = context.shapeResults.find((r) => r.shapeId === context.resolvedTargetShapeId);
  if (!shapeResult) return [];

  try {
    const facts = detectNextConsiderations({
      targetShapeId: context.resolvedTargetShapeId,
      shapeName: shapeResult.name,
      missingSquares: shapeResult.missingSquares,
      routes: context.routePlanResult?.routes ?? [],
      candidateMoves: context.routePlanResult?.candidateMoves ?? [],
      isGameEnd,
      inCheck: isInCheck(current.sfen, shapeResult.perspectiveColor),
    });
    return explainNextConsiderations(facts, current.sfen);
  } catch (err) {
    console.error("今の局面で分かっていること(Phase6 Unit4)の計算でエラーが発生しました:", err);
    return [];
  }
}

/** 選択中の形の「今どこまで出来ているか」を、既存の判定結果からそのまま組み立てる。 */
function toTargetShapeProgress(context: RankedPlanContext | undefined): TargetShapeProgress | null {
  if (!context?.resolvedTargetShapeId) return null;
  const shapeResult = context.shapeResults.find((r) => r.shapeId === context.resolvedTargetShapeId);
  if (!shapeResult) return null;
  return {
    shapeId: shapeResult.shapeId,
    name: shapeResult.name,
    matchedSquareLabels: shapeResult.matchedSquares.map((square) => toJapaneseSquare(square)),
    missingSquareLabels: shapeResult.missingSquares.map((square) => toJapaneseSquare(square)),
  };
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
    // Phase4: current.wasLastOpponentMoveForced(gameSession.tsが確定させた事実)を
    // そのままexplanationGenerator.tsへ渡す。ここでは真偽の判定・推測は一切行わない。
    return explainPositionWithStatus(
      current.sfen,
      current.moveHistory,
      options,
      current.wasLastOpponentMoveForced ?? false,
    );
  } catch (err) {
    console.error("説明生成(analysis/explanationGenerator.ts)でエラーが発生しました:", err);
    return undefined;
  }
}

// options.initialSfenは実サーバー(server.ts)では常に既定値(標準初期局面)のまま使う
// (対局は常にstartposから始まるため)。テストコードが、実際の対局進行を経ずに
// 特定の局面を直接検証したい場合にのみ上書きする(analysis/intentDetector.tsの
// sfen/moveHistory整合性チェックを、任意の盤面に対しても有効なまま使うため)。
/**
 * moveHistoryの日本語棋譜表記への変換に失敗しても(想定外のデータ不整合等)、
 * 対局そのもの(status/sfen等)には影響させない(safeExplainPositionと同じ安全側の方針)。
 * 失敗時はmoveHistoryと同じ長さのnull配列を返し、UI側が全件USI表記へフォールバックする。
 */
function safeToJapaneseMoveHistory(moveHistory: string[], initialSfen?: string): (string | null)[] {
  try {
    return toJapaneseMoveHistory(moveHistory, initialSfen);
  } catch (err) {
    console.error("指し手履歴の日本語棋譜表記変換(notation/japaneseMoveHistory.ts)でエラーが発生しました:", err);
    return moveHistory.map(() => null);
  }
}

export function buildStateResponse(current: GameState, options: ExplainPositionOptions = {}): StateResponseBody {
  return {
    ...current,
    status: getStatus(current),
    coach: safeExplainPosition(current, options),
    legalMoves: getLegalMoves(current.sfen),
    moveHistoryJapanese: safeToJapaneseMoveHistory(current.moveHistory, options.initialSfen),
  };
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
 *
 * planChanged・planChangeReasonは、Phase3 Unit1/Unit2の結果を呼び出し元
 * (server.ts)からそのまま受け取って埋め込むだけの値(このモジュール自身は
 * 検知・分類ロジックを持たない。検知はcomputePlanChangeAfterMove/
 * safeComputePlanChangeAfterMoveが、理由分類はcomputePlanChangeReasonAfterMove/
 * safeComputePlanChangeReasonAfterMoveが行う)。省略時はそれぞれfalse/null
 * (検知対象外の呼び出し、例: 新規対局直後・目標形変更直後)。
 */
export function buildStateResponseWithPlan(
  current: GameState,
  cachedPlan: CachedReachablePlan | undefined,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
  planChanged = false,
  planChangeReason: PlanChangeReason | null = null,
  lastMoveOutcome: MoveOutcome | null = null,
  lastBoardEvents: BoardEvent[] = [],
): StateResponseBodyWithPlan {
  const base = buildStateResponse(current, options);
  const context = safeComputeRankedPlanContext(current, options, selectedTargetShapeId);
  const reachableShapes = context?.reachableShapes ?? [];
  const resolvedTargetShapeId = context?.resolvedTargetShapeId ?? null;
  const hasCandidateMoves = (context?.routePlanResult?.candidateMoves.length ?? 0) > 0;

  let candidateMoveState: CandidateMoveState;
  let candidateMove: CandidateMoveExplanationResult | undefined;

  if (!hasCandidateMoves) {
    // routePlanner.tsが対象の形について候補手を1つも返せない(=解析する対象が無い)。
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

  return {
    ...base,
    plan: {
      reachableShapes,
      routes: toRouteSummaries(context?.routePlanResult),
      targetShapeProgress: toTargetShapeProgress(context),
      candidateMoveLabels: toCandidateMoveLabels(context?.routePlanResult),
      lastMoveOutcome: lastMoveOutcome
        ? {
            ...resolveMoveLabels(current.moveHistory, base.moveHistoryJapanese, lastMoveOutcome),
            // 盤面で実際に起きたこと(捕獲・王手・成り)を先に述べ、そのあとで
            // 形・経路についての説明を述べる。
            messages: [...explainBoardEvents(lastBoardEvents), ...explainMoveOutcome(lastMoveOutcome)],
          }
        : null,
      nextConsiderations: toNextConsiderations(current, context, base.status.isEnd),
      candidateMoveState,
      candidateMove,
      resolvedTargetShapeId,
      planChanged,
      planChangeReason,
    },
  };
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
  const routePlanResult = context.routePlanResult;

  if (!routePlanResult || routePlanResult.candidateMoves.length === 0) {
    return {
      reachableShapes: context.reachableShapes,
      candidateMove: undefined,
      targetShapeId: context.resolvedTargetShapeId,
    };
  }

  const safetyCheck = await checkCandidateMovesSafety(current.sfen, routePlanResult.candidateMoves, engine);
  const candidateMove = explainRouteCandidateMoves(routePlanResult, context.shapeResults, safetyCheck);
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

/**
 * stateBeforeMove(ユーザーが着手する直前の局面)から⑤⑥⑦を計算してPlanSnapshotを
 * 作る(Phase3 Unit1・Unit2で共通の下準備。判定ロジックそのものは持たない)。
 * 計画(候補手)が1件も無かった場合(candidateMoveState: "unavailable"に相当)は
 * undefinedを返す(=崩すべき計画自体が無い)。
 *
 * computePlanChangeAfterMoveのUnit1時点の挙動を変えないための内部ヘルパー。
 */
function buildPlanSnapshotBeforeMove(
  stateBeforeMove: GameState,
  options: ExplainPositionOptions,
  selectedTargetShapeId: string | undefined,
): PlanSnapshot | undefined {
  const beforeContext = computeRankedPlanContext(stateBeforeMove, options, selectedTargetShapeId);
  const candidateMoves = beforeContext.routePlanResult?.candidateMoves ?? [];
  if (!beforeContext.resolvedTargetShapeId || candidateMoves.length === 0) return undefined;

  return {
    targetShapeId: beforeContext.resolvedTargetShapeId,
    candidateMoveUsis: candidateMoves.map((c) => c.moveUsi),
  };
}

/**
 * Phase3 Unit1(計画崩れの検知のみ、人間承認済み)。
 * stateAfterMove(その後ユーザーの着手・相手の着手を経た局面)における
 * 現在のtargetShapeId・合法手一覧と、buildPlanSnapshotBeforeMoveが作った
 * PlanSnapshotを突き合わせて、計画が崩れたかを判定する。
 *
 * 【判定条件(候補Aのみ)】
 * planChangeDetector.ts参照。targetPieceの消失・typical_build_orderの変化・
 * より良い別ルートの発見・エンジン評価値等は一切判定条件に含めない。
 * detectPlanChange自体はUnit1から一切変更していない。
 *
 * 【エンジン非依存】
 * getLegalMoves(rules/legalMoves.ts、shogiopsベース)のみを使い、
 * PrioritizedEngine/MultiPVには一切触れない。
 *
 * 例外はそのまま伝播する(呼び出し元のsafeComputePlanChangeAfterMoveが処理する)。
 */
export function computePlanChangeAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): boolean {
  const previousSnapshot = buildPlanSnapshotBeforeMove(stateBeforeMove, options, selectedTargetShapeId);
  if (!previousSnapshot) return false;

  const afterContext = computeRankedPlanContext(stateAfterMove, options, selectedTargetShapeId);
  const currentLegalMoveUsis = getLegalMoves(stateAfterMove.sfen);

  return detectPlanChange(previousSnapshot, playedMoveUsi, afterContext.resolvedTargetShapeId, currentLegalMoveUsis);
}

/**
 * computePlanChangeAfterMoveの安全側ラッパー(safeComputeRankedPlanContextと同じパターン)。
 * 失敗時はconsole.errorに留め、falseを返す(対局進行には一切影響させない)。
 */
export function safeComputePlanChangeAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): boolean {
  try {
    return computePlanChangeAfterMove(stateBeforeMove, stateAfterMove, playedMoveUsi, options, selectedTargetShapeId);
  } catch (err) {
    console.error("計画崩れ検知(Phase3 Unit1, planChangeDetector)でエラーが発生しました:", err);
    return false;
  }
}

/**
 * Phase3 Unit2(崩れた理由の分類のみ、人間承認済み)。
 * computePlanChangeAfterMoveと同じ判定(detectPlanChange)を経てplanChangedが
 * trueの場合にのみ、classifyPlanChangeReason(エンジン・LLM非依存)で理由を分類する。
 * falseの場合、または崩すべき計画自体が無かった場合はnullを返す。
 *
 * 呼び出し元(server.ts)がcomputePlanChangeAfterMoveと同じstateBeforeMove/
 * stateAfterMove/playedMoveUsiの組み合わせで呼ぶことを前提とする
 * (両関数は同じ入力から独立に判定するため、二重にengine等を呼ぶことはないが、
 * ⑤⑥⑦の計算(エンジン不要・軽量)は両関数でそれぞれ1回ずつ行われる)。
 *
 * 例外はそのまま伝播する(呼び出し元のsafeComputePlanChangeReasonAfterMoveが処理する)。
 */
export function computePlanChangeReasonAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): PlanChangeReason | null {
  const previousSnapshot = buildPlanSnapshotBeforeMove(stateBeforeMove, options, selectedTargetShapeId);
  if (!previousSnapshot) return null;

  const afterContext = computeRankedPlanContext(stateAfterMove, options, selectedTargetShapeId);
  const currentLegalMoveUsis = getLegalMoves(stateAfterMove.sfen);

  const changed = detectPlanChange(previousSnapshot, playedMoveUsi, afterContext.resolvedTargetShapeId, currentLegalMoveUsis);
  if (!changed) return null;

  return classifyPlanChangeReason(previousSnapshot, playedMoveUsi, stateAfterMove.sfen);
}

/**
 * Phase6 Unit2(直前の一手で何が変わったかの抽出)。
 * ユーザー着手直前(stateBeforeMove)と、相手の応手まで終えた現在(stateAfterMove)の
 * ⑤⑥⑦をそれぞれ計算し、moveOutcomeDetector.tsで差分を取る。
 *
 * planChangeReasonは、呼び出し元が既存のcomputePlanChangeReasonAfterMoveで得た値を
 * そのまま渡す(このモジュールも、moveOutcomeDetector.tsも、理由の判定は自前で行わない)。
 *
 * 【比較できない場合はnullを返す】
 * 相手が応手していない(終局等で手番が自分に戻っていない)局面では、routePlanner.tsが
 * not_self_turnで経路を返さないため、差分を取ると「経路が全て失われた」という誤った
 * 事実になる。この場合は比較自体を行わずnullを返す(推測しない)。
 *
 * 【エンジン非依存】
 * ⑧(MultiPV参考評価)には一切触れない。したがって「良い手だったか」は判定できないし、
 * 判定しない。
 *
 * 例外はそのまま伝播する(呼び出し元のsafeComputeMoveOutcomeAfterMoveが処理する)。
 */
export function computeMoveOutcomeAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  opponentMoveUsi: string | null,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
  planChangeReason: PlanChangeReason | null = null,
): MoveOutcome | null {
  const afterContext = computeRankedPlanContext(stateAfterMove, options, selectedTargetShapeId);
  if (afterContext.routePlanResult?.unresolvedReason === "not_self_turn") return null;

  const beforeContext = computeRankedPlanContext(stateBeforeMove, options, selectedTargetShapeId);

  return detectMoveOutcome(
    toMoveOutcomeSnapshot(beforeContext),
    toMoveOutcomeSnapshot(afterContext),
    playedMoveUsi,
    opponentMoveUsi,
    planChangeReason,
  );
}

/**
 * Phase6 Unit3(盤面で実際に起きたこと)。
 * ユーザーの着手と(あれば)相手の応手について、捕獲・王手・成りだけを抽出する。
 * 判定はanalysis/boardEventDetector.tsが行い、ここは配線のみ。
 *
 * 形・経路(Unit1/Unit2)とは独立した、将棋のルールだけから決まる事実であり、
 * エンジンの評価値には一切依存しない。
 *
 * 例外はそのまま伝播する(呼び出し元のsafeComputeBoardEventsAfterMoveが処理する)。
 */
export function computeBoardEventsAfterMove(
  stateBeforeMove: GameState,
  playedMoveUsi: string,
  opponentMoveUsi: string | null,
): BoardEvent[] {
  return detectBoardEvents(stateBeforeMove.sfen, playedMoveUsi, opponentMoveUsi);
}

/**
 * computeBoardEventsAfterMoveの安全側ラッパー(他のsafe*と同じパターン)。
 * 失敗時はconsole.errorに留め、空配列を返す(対局進行には一切影響させない)。
 */
export function safeComputeBoardEventsAfterMove(
  stateBeforeMove: GameState,
  playedMoveUsi: string,
  opponentMoveUsi: string | null,
): BoardEvent[] {
  try {
    return computeBoardEventsAfterMove(stateBeforeMove, playedMoveUsi, opponentMoveUsi);
  } catch (err) {
    console.error("盤面の出来事の抽出(Phase6 Unit3, boardEventDetector)でエラーが発生しました:", err);
    return [];
  }
}

/**
 * computeMoveOutcomeAfterMoveの安全側ラッパー(他のsafe*と同じパターン)。
 * 失敗時はconsole.errorに留め、nullを返す(対局進行には一切影響させない)。
 */
export function safeComputeMoveOutcomeAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  opponentMoveUsi: string | null,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
  planChangeReason: PlanChangeReason | null = null,
): MoveOutcome | null {
  try {
    return computeMoveOutcomeAfterMove(
      stateBeforeMove,
      stateAfterMove,
      playedMoveUsi,
      opponentMoveUsi,
      options,
      selectedTargetShapeId,
      planChangeReason,
    );
  } catch (err) {
    console.error("直前の一手の変化の抽出(Phase6 Unit2, moveOutcomeDetector)でエラーが発生しました:", err);
    return null;
  }
}

/**
 * computePlanChangeReasonAfterMoveの安全側ラッパー(safeComputePlanChangeAfterMoveと
 * 同じパターン)。失敗時はconsole.errorに留め、nullを返す(対局進行には
 * 一切影響させない)。
 */
export function safeComputePlanChangeReasonAfterMove(
  stateBeforeMove: GameState,
  stateAfterMove: GameState,
  playedMoveUsi: string,
  options: ExplainPositionOptions = {},
  selectedTargetShapeId?: string,
): PlanChangeReason | null {
  try {
    return computePlanChangeReasonAfterMove(stateBeforeMove, stateAfterMove, playedMoveUsi, options, selectedTargetShapeId);
  } catch (err) {
    console.error("計画崩れ理由判定(Phase3 Unit2, planChangeReason)でエラーが発生しました:", err);
    return null;
  }
}
