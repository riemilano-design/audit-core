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
import type { ShapeStatus } from "../analysis/shapeDetector.js";
import { toMovingPieceName } from "../notation/japaneseMove.js";
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
import { exposeName } from "../analysis/nameExposure.js";
import { getLegalMoves } from "../rules/legalMoves.js";
import { isInCheck } from "../rules/gameStatus.js";
import { toJapaneseMoveHistory } from "../notation/japaneseMoveHistory.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";

export type { PlanSnapshot } from "../analysis/planChangeDetector.js";
export type { PlanChangeReason } from "../analysis/planChangeReason.js";
export type { MoveOutcome } from "../analysis/moveOutcomeDetector.js";
export type { BoardEvent } from "../analysis/boardEventDetector.js";
export type { NextConsiderationMessage } from "../analysis/nextConsiderationExplanation.js";

/**
 * ブラウザへ公開してよい対局状態だけを明示列挙した型(許可リスト方式)。
 *
 * GameState(game/gameSession.ts)はサーバー内部の対局状態であり、相手AIの制御に
 * 関わる情報(scenario / wasLastOpponentMoveForced など)を含む。Phase 7 Unit 1 では
 * 相手AIが選んだ狙いをユーザーに開示しないため(docs/PHASES.md Phase 4「その後の変更」・
 * docs/SCENARIOS.md)、内部状態をそのまま公開できない。
 *
 * ここで公開してよいものだけを列挙し、toPublicGameState()を唯一の変換境界にすることで、
 * GameStateへフィールドを追加しても既定では公開されない(除外リスト方式にしない)。
 *
 * forcedPliesUsed について: STEP ζ-4c-1(C-6、人間承認済み)により非公開へ移した。
 * 強制進行の手数は、選ばれた狙いの手順長を通じて狙いの間接的な手がかりになりうるため、
 * 非公開とする(人間承認済み)。
 */
export interface PublicGameState {
  sfen: string;
  moveHistory: string[];
}

/**
 * サーバー内部の対局状態から、公開してよい情報だけを取り出す唯一の変換境界。
 * この関数を通らない公開経路を作らないこと(docs/ARCHITECTURE.md 8.)。
 */
function toPublicGameState(current: GameState): PublicGameState {
  return {
    sfen: current.sfen,
    moveHistory: current.moveHistory,
  };
}

export interface StateResponseBody extends PublicGameState {
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
/**
 * [5]「参考になる囲い」の1件。学習用の参考資料であり、選択肢ではない。
 * 完成形の駒配置は、座標の根拠が人間に確認されるまで返さない(toReferenceShapes参照)。
 */
export interface ReferenceShapeBody {
  shapeId: string;
  name: string;
  pendingReviewNote: string | null;
  characteristics: string;
  /** 現在の局面についての認識状態(none / forming / completed)。 */
  status: ShapeStatus;
  /** 既に成立しているマス(日本語表記)。現在の形との関係を示すために使う。 */
  matchedSquareLabels: string[];
  /** まだ埋まっていないマス(日本語表記)。 */
  missingSquareLabels: string[];
}

/** [3]「なぜそれが重要か」に出す、完成した自分の形の弱点。data/shapes/*.json の
 * weak_against をそのまま運ぶだけで、新しい文言は作らない。 */
export interface ShapeWeaknessBody {
  shapeId: string;
  name: string;
  /** review_statusが"draft"の場合にだけ入る注記。それ以外はnull。 */
  pendingReviewNote: string | null;
  text: string;
}

export interface TargetShapeProgress {
  shapeId: string;
  name: string;
  /** data/shapes/*.json の characteristics をそのまま運んだもの(新しい文言ではない)。
   * ユーザーが選んだ目標形が「どういう形なのか」を [4] で一度だけ説明するために使う。 */
  description: string;
  /** 既にその形の一部として成立しているマス(日本語表記、例: "６九") */
  matchedSquareLabels: string[];
  /** まだ埋まっていないマス(日本語表記) */
  missingSquareLabels: string[];
  /**
   * STEP ζ-5: この形のreview_statusが"draft"の場合にだけ入る注記
   * (analysis/nameExposure.tsのsite="shape")。それ以外はnull。
   * review_status自体(生の値)は公開しない(analysis/nameExposure.tsに判断を集約する)。
   */
  pendingReviewNote: string | null;
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
   * 表示するメッセージ。Phase6 Unit3で、盤面の出来事(捕獲・成り)のメッセージが先頭に
   * 加わる(起きた順。形・経路についての説明はその後ろ)。
   *
   * 【Unit 3(情報構造の整理)で契約が変わった】**空配列になり得る。**
   * - 目標形が未選択のときは「特に変化なし」("no_notable_change")を返さない
   *   (filterLastMoveMessagesForTargetShape。既知事項 U0-1)
   * - 王手("check_received")は [0] の urgentMessages へ移し、ここには残さない
   *   (partitionUrgentMessages)
   * 利用側(apps/web/src/gameApi.ts の LastMoveOutcomeBody)にも同じ契約を書いてある。
   */
  messages: (BoardEventMessage | MoveOutcomeMessage)[];
}

/**
 * STEP ζ-5: analysis/shapeGraphRanking.tsのRankedReachableShapeのうち、
 * ブラウザへ公開してよいフィールドだけを明示列挙した型(許可リスト方式)。
 * PublicGameStateと同じ理由(docs/ARCHITECTURE.md 8.)で、reviewStatusの生値は
 * 列挙しない(名前を出してよいかの判断はanalysis/nameExposure.tsに集約する)。
 */
export interface ReachableShapeBody {
  shapeId: string;
  name: string;
  family: string;
  parentShapeId: string | null;
  status: RankedReachableShape["status"];
  matchScore: number;
  adjustment: RankedReachableShape["adjustment"];
  reason: string | null;
  sourceIntentId: string | null;
  /** review_statusが"draft"の場合にだけ入る注記(analysis/nameExposure.tsのsite="shape")。 */
  pendingReviewNote: string | null;
}

export interface ReachablePlanBody {
  /** shapeGraphRankingの上位(最大3件)の「目指せる形」。1位を唯一の正解として
   * 強調しない前提で、呼び出し側(UI)は並列表示する。 */
  reachableShapes: ReachableShapeBody[];
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
   * 表示すべき事実が無い場合・目標形が決まっていない場合・対局終了時は空配列。
   * 【Unit 3 で契約が変わった】王手("in_check")は [0] の urgentMessages へ移す
   * (partitionUrgentMessages)。候補手が1件でもある局面では
   * "no_playable_route_first_move" を除く(filterContradictoryConsiderations)
   * (呼び出し側はブロックごと描画しない)。
   */
  nextConsiderations: NextConsiderationMessage[];
  candidateMoveState: CandidateMoveState;
  /** candidateMoveState: "ready"の場合のみ値を持つ。それ以外はundefined。 */
  candidateMove: CandidateMoveExplanationResult | undefined;
  /**
   * STEP ζ-5(経路6): 候補手セクションに添える注意書き。選択中の形のreview_statusが
   * "draft"の場合にだけ入る(analysis/nameExposure.tsのsite="section")。
   * 個々の候補手の説明文自体(candidateMoveExplanation.tsの文言)は変更しない。
   * 候補手見出しの名前表示(TargetShapeProgress.pendingReviewNote)がフォールバック
   * しても、この注意書きは独立に出る。選択中の形が無い場合はnull。
   */
  pendingReviewNote: string | null;
  /**
   * ⑦⑧の計算に実際に使われたshapeId。ユーザーが選択したshapeIdがreachableShapes
   * に含まれる場合のみ値を持つ。未選択・無効値の場合はnull(Phase 7 Unit 0で
   * ranked[0]への自動フォールバックを廃止した。目標形は選ぶまで存在しない)。
   * reachableShapesのどれが現在の「目標」かをUI側でハイライトするために使う。
   */
  resolvedTargetShapeId: string | null;
  /** [3]「なぜそれが重要か」に出す、完成した自分の形の弱点。該当が無ければnull。 */
  shapeWeakness: ShapeWeaknessBody | null;
  /** [0]「今すぐ対処が必要なこと」に出すメッセージ。該当が無ければ空配列
   * (partitionUrgentMessages参照。文言はすべて既存のもの)。 */
  urgentMessages: { kind: string; text: string }[];
  /** [5]「参考になる囲い」。学習用の参考資料で、選択肢ではない。 */
  referenceShapes: ReferenceShapeBody[];
  /** 方向が1つに定まらないときに [4] へ出す一文。定まっている場合はnull。 */
  directionNote: string | null;
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
 * ユーザーが指定した生の値そのものではない。未選択・無効値の場合はundefined
 * (Phase 7 Unit 0でranked[0]への自動フォールバックを廃止した)。同じsfenでも
 * 目標形が変わればcandidateMovesの中身は変わり得るため、sfenだけを世代識別子に
 * すると古い目標形の結果を新しい目標形の結果として誤って返しかねない
 * (このバグを避けるためのフィールド追加)。
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
  /** 実際にroutePlanner.tsへ渡されたshapeId。ユーザーが選択したshapeId
   * (selectedTargetShapeId)がreachableShapesに含まれていればそれ、
   * 含まれない(未選択・無効値)場合はundefined(Phase 7 Unit 0。
   * 目標形は選ぶまで存在しないものとして扱う)。 */
  resolvedTargetShapeId: string | undefined;
  /** Phase 7 Unit 3: 局面から認識できた方向性(1件に定まったか、定まらなかったか)。 */
  direction: RecognizedDirection;
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
 * 含まれない場合(未指定・無効なshapeId・対局が進んで候補から外れた等)は
 * undefinedのままにする(Phase 7 Unit 0)。目標形は「対局開始時に自動選択される
 * もの」ではなく「ユーザーが選ぶまで存在しないもの」として扱う
 * ([../../../../CLAUDE.md](../../../../CLAUDE.md) の「絶対的な上位原則」)。
 * その結果、resolvedTargetShapeId / routePlanResult(ひいてはtargetShapeProgress /
 * routes / candidateMove)は未選択の間undefinedになる。reachableShapes(目指せる形の
 * 候補)自体は、選ぶ手段を残すためこれまでどおり計算・提供する。
 */
/**
 * Phase 7 Unit 3: 道のり・候補手の対象を「局面から認識できた方向性」から決める。
 *
 * 【ranked[0] フォールバックを復活させないこと(人間の確定した制約)】
 * `rankReachableShapes` の順位は matchScore と intent 由来の調整を含む「望ましさ」の
 * 並びであり、Unit 0 で「1位を自動的に目標形にする」ことを人間が廃止した。ここでは
 * 順位を一切使わない。使うのは `shapeFormationAnalyzer` の `status` だけで、これは
 * `formationEvidence`(実際にその駒がそのマスへ動いた証拠)を要求する認識結果である。
 *
 * 【1つに定まらない場合は何も返さない】
 * forming がちょうど1件のときだけ、その形を対象とする。0件(まだ何も認識できていない)
 * でも、2件以上(方向が1つに定まらない)でも undefined を返し、候補手を生成しない。
 * 同点を裁く規則をここで発明しない(CLAUDE.mdルール4番: 判定結果・優先度を人間の
 * 承認なしに確定しない)。
 */
export type RecognizedDirectionReason = "single" | "none" | "ambiguous";

export interface RecognizedDirection {
  shapeId: string | undefined;
  reason: RecognizedDirectionReason;
  /** 認識されていた(forming の)形の件数。報告・テスト用。 */
  formingCount: number;
}

/** shapeId から parent_shape_id をたどった祖先の一覧。循環していても止まる(安全側)。 */
function ancestorIdsOf(
  shapeId: string,
  parentById: Map<string, string | null>,
): string[] {
  const ancestors: string[] = [];
  const seen = new Set<string>([shapeId]);
  let current = parentById.get(shapeId) ?? null;
  while (current !== null && !seen.has(current)) {
    ancestors.push(current);
    seen.add(current);
    current = parentById.get(current) ?? null;
  }
  return ancestors;
}

/**
 * 認識できた形が複数あるときに、道のり・候補手の対象を1件へ絞る規則(人間の承認済み)。
 *
 * 【根拠は parent_shape_id だけである】
 * data/shapes/*.json の parent_shape_id は 本美濃囲い → 高美濃囲い → 銀冠 という
 * 「基本の形から発展させた形」の関係を表す既存の記述的データである。forming が複数
 * あるとき、**そのうち他のすべての祖先になっている形(= 最も基本となる、一番近い
 * 到達点)** を対象とする。
 *
 *   本美濃 + 高美濃 + 銀冠 → 本美濃
 *   高美濃 + 銀冠         → 高美濃
 *   本美濃 + 銀冠         → 本美濃(祖先はたどって判定する)
 *   1件のみ               → その形
 *   0件                   → 対象を決めない(候補手を出さない)
 *
 * 【使わないもの(人間が明示した禁止事項)】
 * - rankReachableShapes の順位(ranked[0] フォールバックの復活にあたる)
 * - matchScore による並べ替え
 * - 新しい閾値・将棋知識にもとづく判定
 * これらを構造として排除するため、**入力は shapeResults(全形)であり、
 * ranked.slice(0, 3) ではない。** ranked を入力にすると、対象になりうる形の集合を
 * matchScore が決めることになる(形が3件の現状では同じ結果だが、形が増えた時点で
 * 効き始める)。
 *
 * 【一意に決まらない場合】
 * forming が複数あり、そのうちのどれも他すべての祖先でない場合(例: 将来、別系統の
 * 囲いが追加されて兄弟関係になった場合)は、対象を決めずに "ambiguous" を返す。
 * ここで順位付けを発明しない([../../../../CLAUDE.md](../../../../CLAUDE.md)
 * 「絶対に守るルール」4番)。この状態は人間へ報告する対象である。
 */
export function resolveRecognizedDirection(
  shapes: Pick<ShapeFormationResult, "shapeId" | "status" | "parentShapeId">[],
): RecognizedDirection {
  const forming = shapes.filter((shape) => shape.status === "forming");
  if (forming.length === 0) {
    return { shapeId: undefined, reason: "none", formingCount: 0 };
  }
  if (forming.length === 1) {
    return { shapeId: forming[0]!.shapeId, reason: "single", formingCount: 1 };
  }

  const parentById = new Map(shapes.map((shape) => [shape.shapeId, shape.parentShapeId]));
  const ancestorsById = new Map(
    forming.map((shape) => [shape.shapeId, ancestorIdsOf(shape.shapeId, parentById)]),
  );

  // 他のすべての forming の祖先(または自分自身)になっている形を探す。
  const rootMost = forming.filter((candidate) =>
    forming.every(
      (other) =>
        other.shapeId === candidate.shapeId ||
        (ancestorsById.get(other.shapeId) ?? []).includes(candidate.shapeId),
    ),
  );

  if (rootMost.length === 1) {
    return { shapeId: rootMost[0]!.shapeId, reason: "single", formingCount: forming.length };
  }
  return { shapeId: undefined, reason: "ambiguous", formingCount: forming.length };
}

/** 方向が1つに定まらないときに [4] へ出す一文(人間が指定した文言)。 */
export const DIRECTION_UNDECIDED_TEXT =
  "この局面では、まだ特定の囲いへの方向は決まっていません。";

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
  // Phase 7 Unit 3: ユーザーに目標形を選ばせるUIは廃止した。本番導線では、道のり・
  // 候補手の対象を「局面から認識できた方向性」から決める(resolveRecognizedDirection)。
  // selectedTargetShapeId は開発・検証用の POST /api/game/target-shape のためだけに残す
  // (Unit 0 で forcedOpponentOpening を残したのと同じ扱い)。明示された場合はそれを優先する。
  // 入力は shapeResults(全形)。ranked.slice(0, 3) を渡すと、対象になりうる形の集合を
  // matchScore が決めることになるため、渡さない(resolveRecognizedDirection のコメント参照)。
  const direction = resolveRecognizedDirection(shapeResults);
  const explicit =
    selectedTargetShapeId !== undefined
      ? reachableShapes.find((s) => s.shapeId === selectedTargetShapeId)
      : undefined;
  const top =
    explicit ?? (direction.shapeId !== undefined ? shapeResults.find((s) => s.shapeId === direction.shapeId) : undefined);
  const resolvedTargetShapeId = top?.shapeId;
  const routePlanResult = top ? planRoutesToShape(current.sfen, shapeResults, top.shapeId) : undefined;
  return { shapeResults, reachableShapes, resolvedTargetShapeId, routePlanResult, direction };
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
/**
 * 候補手の表示ラベル。Phase 7 Unit 3 から「駒名：移動元→移動先」の形にする
 * (例: "金：６七→６六")。駒名は現在局面のSFENの移動元マスを読むだけで決まり、
 * 将棋の判断は入れない。駒名が取れない場合は従来どおりマス目だけの表記に落とす。
 */
function toCandidateMoveLabels(
  routePlanResult: ShapeRoutePlanResult | undefined,
  sfen: string,
): Record<string, string> {
  const labels: Record<string, string> = {};
  for (const candidate of routePlanResult?.candidateMoves ?? []) {
    const squares = toJapaneseMoveSquares(candidate.moveUsi);
    const piece = safeToMovingPieceName(sfen, candidate.moveUsi);
    labels[candidate.moveUsi] = piece ? `${piece}：${squares}` : squares;
  }
  return labels;
}

/** 駒名の取得は表示上の都合であり、失敗しても対局・解析を止めない。 */
function safeToMovingPieceName(sfen: string, moveUsi: string): string | null {
  try {
    return toMovingPieceName(sfen, moveUsi);
  } catch (err) {
    console.error("候補手の駒名の解決(notation/japaneseMove.ts)でエラーが発生しました:", err);
    return null;
  }
}

/**
 * [5]「参考になる囲い」に出す一覧。ユーザーが選ぶための候補ではなく、
 * 「将棋にはこういう完成形がある」という学習用の参考資料である。
 *
 * 【完成形の駒配置(required_pieces)をここで返さないこと】
 * data/shapes/*.json の座標は、各ファイルの source 自身が「一次資料による確認を
 * 行っていない」と記しており、特に mino_takamino は source が記す先手視点の記述と
 * 保存座標の左右が一致していない。人間による座標の確定を待つため、完成形の盤も
 * 駒名+座標の一覧も出さない(人間の指示)。ここで返すのは名前と特徴だけである。
 */
function toReferenceShapes(context: RankedPlanContext | undefined): ReferenceShapeBody[] {
  if (!context) return [];
  return context.shapeResults.map((shape) => {
    const exposed = exposeName(shape.name, shape.reviewStatus, "shape");
    return {
      shapeId: shape.shapeId,
      name: exposed.name,
      pendingReviewNote: exposed.pendingNote,
      characteristics: shape.characteristics,
      status: shape.status,
      matchedSquareLabels: shape.matchedSquares.map((square) => toJapaneseSquare(square)),
      missingSquareLabels: shape.missingSquares.map((square) => toJapaneseSquare(square)),
    };
  });
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
      shapeReviewStatus: shapeResult.reviewStatus,
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

/** 選択中の形の「今どこまで出来ているか」を、既存の判定結果からそのまま組み立てる。
 *
 * 【description について(Unit 3 情報構造の整理)】
 * ユーザーが自分で選んだ目標形の名前は [4]「どう指すか」に必ず出るが、その形が
 * どういう形なのかの説明はどこにも出ていなかった。ここで返す description は
 * data/shapes/*.json の characteristics をそのまま運ぶだけで、新しい文言は作らない。
 * これは「盤面がその形である」という断定ではなく、ユーザーが選んだ目標の説明である
 * (formingでcharacteristicsを連結しないexplanationGenerator.tsの制約は、
 * 「今の形が何か」を断定しないための制約であり、ここには当たらない)。
 * review_status が draft の場合は既存の pendingReviewNote が併記される。
 */
function toTargetShapeProgress(context: RankedPlanContext | undefined): TargetShapeProgress | null {
  if (!context?.resolvedTargetShapeId) return null;
  const shapeResult = context.shapeResults.find((r) => r.shapeId === context.resolvedTargetShapeId);
  if (!shapeResult) return null;
  return {
    shapeId: shapeResult.shapeId,
    name: shapeResult.name,
    description: shapeResult.characteristics,
    matchedSquareLabels: shapeResult.matchedSquares.map((square) => toJapaneseSquare(square)),
    missingSquareLabels: shapeResult.missingSquares.map((square) => toJapaneseSquare(square)),
    pendingReviewNote: exposeName(shapeResult.name, shapeResult.reviewStatus, "shape").pendingNote,
  };
}

/**
 * [3]「なぜそれが重要か」に出す、自分の形の弱点(data/shapes/*.json の weak_against)。
 *
 * 【表示条件(人間の承認済み仕様)】
 * 実際にその形が認定された場合(status === "completed")だけ返す。ShapeStatus は
 * none / forming / completed の3値で "matched" は存在しないため、条件は completed のみ。
 * forming・none では返さない(形を断定していない段階で、その形の弱点を述べないため)。
 *
 * 本文に他の戦法名が直書きされている点(既知事項 Z-1)は、人間が次Phaseへ持ち越しと
 * 処遇済みである。ここでは data/ の本文を書き換えず、表示条件だけを決める。
 */
function toShapeWeakness(shapeResults: ShapeFormationResult[] | undefined): ShapeWeaknessBody | null {
  if (!shapeResults) return null;
  const completed = shapeResults.filter((r) => r.status === "completed" && r.weakAgainst);
  if (completed.length === 0) return null;
  // 複数が同時に completed になり得るため、必須マスが多い(=より具体的な)ものを1件だけ選ぶ。
  // 「どれが優れているか」の判断ではなく、重複表示を避けるための機械的な選択である。
  const best = completed.reduce((a, b) => (b.matchedSquares.length > a.matchedSquares.length ? b : a));
  const exposed = exposeName(best.name, best.reviewStatus, "shape");
  return {
    shapeId: best.shapeId,
    name: exposed.name,
    pendingReviewNote: exposed.pendingNote,
    text: best.weakAgainst as string,
  };
}

/**
 * STEP ζ-5(経路6): 候補手セクションに添える注意書き。選択中の形(resolvedTargetShapeId)の
 * review_statusが"draft"の場合にだけ注記(site="section")を返す。候補手が実際に
 * 表示されているか(candidateMoveState)には依存せず、選択中の形自体から独立に決まる
 * (候補手見出しの名前表示がフォールバックしても、この注意書きは漏れないようにするため)。
 */
function toPlanPendingReviewNote(context: RankedPlanContext | undefined): string | null {
  if (!context?.resolvedTargetShapeId) return null;
  const shapeResult = context.shapeResults.find((r) => r.shapeId === context.resolvedTargetShapeId);
  if (!shapeResult) return null;
  return exposeName(shapeResult.name, shapeResult.reviewStatus, "section").pendingNote;
}

/**
 * RankedPlanContextのreachableShapes(内部型RankedReachableShape[])を、
 * 公開してよいフィールドだけを明示列挙したReachableShapeBody[]へ変換する
 * (toPublicGameState()と同じ許可リスト方式)。reviewStatusの生値は列挙しないため、
 * フィールドを追加しても既定では公開されない。
 */
function toReachableShapeBodies(reachableShapes: RankedReachableShape[]): ReachableShapeBody[] {
  return reachableShapes.map((shape) => ({
    shapeId: shape.shapeId,
    name: shape.name,
    family: shape.family,
    parentShapeId: shape.parentShapeId,
    status: shape.status,
    matchScore: shape.matchScore,
    adjustment: shape.adjustment,
    reason: shape.reason,
    sourceIntentId: shape.sourceIntentId,
    pendingReviewNote: exposeName(shape.name, shape.reviewStatus, "shape").pendingNote,
  }));
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
    ...toPublicGameState(current),
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
 * computeRankedPlanContext側でundefinedのままになる(Phase 7 Unit 0で
 * ranked[0]への自動フォールバックを廃止した。目標形は選ぶまで存在しない)。
 *
 * planChanged・planChangeReasonは、Phase3 Unit1/Unit2の結果を呼び出し元
 * (server.ts)からそのまま受け取って埋め込むだけの値(このモジュール自身は
 * 検知・分類ロジックを持たない。検知はcomputePlanChangeAfterMove/
 * safeComputePlanChangeAfterMoveが、理由分類はcomputePlanChangeReasonAfterMove/
 * safeComputePlanChangeReasonAfterMoveが行う)。省略時はそれぞれfalse/null
 * (検知対象外の呼び出し、例: 新規対局直後・目標形変更直後)。
 */
/**
 * 既知事項 U0-1 の解消(人間の承認済み仕様)。
 * 目標形が選ばれていないのに「選んだ形」「目標にしている形」を指す説明は返さない。
 * 代替の文言は新規に作らず、該当する説明そのものを落とす。
 *
 * 落とすのは stage: "current_shape" かつ status が "forming" のものだけである。
 * - "completed": 「今、◯◯の形ができています」は目標形の選択と無関係に成立する事実
 * - "none": 「どの形ともまだ一致していません」も目標形と無関係
 * - "forming": 文言が「今の陣形は、選んだ形に近づいてきていますが…」であり、
 *   目標形が未選択のときは指す対象が存在しない
 */
export function filterCoachForTargetShape(
  coach: CoachExplanation[] | undefined,
  hasTargetShape: boolean,
): CoachExplanation[] | undefined {
  if (coach === undefined || hasTargetShape) return coach;
  return coach.filter((item) => !(item.stage === "current_shape" && item.status === "forming"));
}

/**
 * 既知事項 U0-1 の解消(人間の承認済み仕様)。
 * 目標形が選ばれていない間は「この手のあと、目標にしている形について特に大きな
 * 変化はありませんでした。」(kind: "no_notable_change")を返さない。
 * 盤面で実際に起きたこと(捕獲・成り・王手)はそのまま残す。
 */
export function filterLastMoveMessagesForTargetShape(
  messages: (BoardEventMessage | MoveOutcomeMessage)[],
  hasTargetShape: boolean,
): (BoardEventMessage | MoveOutcomeMessage)[] {
  if (hasTargetShape) return messages;
  return messages.filter((message) => message.kind !== "no_notable_change");
}

/**
 * [0]「今すぐ対処が必要なこと」に出すメッセージ(Unit 3 情報構造の整理)。
 *
 * 【なぜサーバー側で振り分けるか】
 * 既存の方針(gameApi.tsのコメント)どおり、メッセージ種別(kind)の一覧はサーバー側だけが
 * 持ち、web側に同じ列挙を重複させない。どのメッセージが「今すぐ対処が必要」かの判断も
 * 将棋の判断であり、web側に持たせない([../../../../CLAUDE.md](../../../../CLAUDE.md)
 * 「絶対に守るルール」5番)。
 *
 * 【重複の解消】
 * 王手は2つの経路から同じ内容が届く。
 * - 盤面で起きたこと: "check_received"(相手の手であなたの玉に王手がかかっています。)
 * - 今の局面の事実: "in_check"(今、あなたの玉に王手がかかっています。ルール上…)
 * 両方出すと同じ事実を2箇所で述べることになるため、"in_check" があるときはそちらだけを
 * 使い、"check_received" は落とす。"in_check" は目標形が選ばれていないと生成されない
 * (toNextConsiderationsが目標形の無い局面では空を返す)ため、その場合だけ
 * "check_received" を [0] に回す。文言はどちらもサーバー側の既存のもので、新しい文言は
 * 作らない。
 */
const URGENT_BOARD_EVENT_KIND = "check_received";
const URGENT_NEXT_CONSIDERATION_KIND = "in_check";

export interface UrgentPartition {
  urgent: { kind: string; text: string }[];
  lastMoveMessages: (BoardEventMessage | MoveOutcomeMessage)[];
  nextConsiderations: NextConsiderationMessage[];
}

export function partitionUrgentMessages(
  lastMoveMessages: (BoardEventMessage | MoveOutcomeMessage)[],
  nextConsiderations: NextConsiderationMessage[],
): UrgentPartition {
  const inCheckNotices = nextConsiderations.filter((m) => m.kind === URGENT_NEXT_CONSIDERATION_KIND);
  const checkReceived = lastMoveMessages.filter((m) => m.kind === URGENT_BOARD_EVENT_KIND);

  // "in_check" があればそれだけを使う(同じ王手を2度述べない)。
  const urgent = inCheckNotices.length > 0 ? [...inCheckNotices] : [...checkReceived];

  return {
    urgent,
    lastMoveMessages: lastMoveMessages.filter((m) => m.kind !== URGENT_BOARD_EVENT_KIND),
    nextConsiderations: nextConsiderations.filter((m) => m.kind !== URGENT_NEXT_CONSIDERATION_KIND),
  };
}

/**
 * 「今の局面では、選んだ形へ向かう道のりの一手目を、どれも指すことができません。」
 * (kind: "no_playable_route_first_move")は、同じ画面の下に候補手が並ぶと初心者には
 * 矛盾して読める(Unit 1 の実測で2回再現)。候補手が1件でもある局面では、この一文を
 * 出さない。厳密には「道のりの一手目」と「準備手」は別のものだが、その区別を画面で
 * 説明せずに両方出すことが混乱の原因だったため、表示側で出し分ける。
 * 判定は候補手の有無という機械的な事実だけで行い、将棋の判断はしない。
 */
const CONTRADICTORY_WITH_CANDIDATES_KIND = "no_playable_route_first_move";

export function filterContradictoryConsiderations(
  nextConsiderations: NextConsiderationMessage[],
  hasCandidateMoves: boolean,
): NextConsiderationMessage[] {
  if (!hasCandidateMoves) return nextConsiderations;
  return nextConsiderations.filter((m) => m.kind !== CONTRADICTORY_WITH_CANDIDATES_KIND);
}

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
  const reachableShapes = toReachableShapeBodies(context?.reachableShapes ?? []);
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

  const partition = partitionUrgentMessages(
    lastMoveOutcome
      ? filterLastMoveMessagesForTargetShape(
          // 盤面で実際に起きたこと(捕獲・王手・成り)を先に述べ、そのあとで
          // 形・経路についての説明を述べる。
          [...explainBoardEvents(lastBoardEvents), ...explainMoveOutcome(lastMoveOutcome)],
          resolvedTargetShapeId !== null,
        )
      : [],
    toNextConsiderations(current, context, base.status.isEnd),
  );

  return {
    ...base,
    coach: filterCoachForTargetShape(base.coach, resolvedTargetShapeId !== null),
    plan: {
      reachableShapes,
      routes: toRouteSummaries(context?.routePlanResult),
      targetShapeProgress: toTargetShapeProgress(context),
      candidateMoveLabels: toCandidateMoveLabels(context?.routePlanResult, current.sfen),
      referenceShapes: toReferenceShapes(context),
      directionNote:
        context && context.direction.reason !== "single" && context.resolvedTargetShapeId === undefined
          ? DIRECTION_UNDECIDED_TEXT
          : null,
      urgentMessages: partition.urgent,
      lastMoveOutcome: lastMoveOutcome
        ? {
            ...resolveMoveLabels(current.moveHistory, base.moveHistoryJapanese, lastMoveOutcome),
            messages: partition.lastMoveMessages,
          }
        : null,
      nextConsiderations: filterContradictoryConsiderations(partition.nextConsiderations, hasCandidateMoves),
      candidateMoveState,
      candidateMove,
      pendingReviewNote: toPlanPendingReviewNote(context),
      resolvedTargetShapeId,
      shapeWeakness: toShapeWeakness(context?.shapeResults),
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
 * shapeId(選択されていなければundefined。Phase 7 Unit 0でranked[0]への
 * 自動フォールバックを廃止した。目標形は選ぶまで存在しない)であり、
 * 呼び出し元(server.ts)がCachedReachablePlanの世代識別子として保持する。
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
