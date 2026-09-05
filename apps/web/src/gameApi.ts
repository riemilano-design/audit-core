// apps/serverの最小HTTP APIへのフェッチラッパー。
// 開発時はvite.config.tsのプロキシ設定により、相対パス"/api/..."がapps/serverへ転送される。

export interface GameOutcome {
  result: string;
  winner: "sente" | "gote" | undefined;
}

export interface GameStatus {
  isEnd: boolean;
  outcome: GameOutcome | undefined;
}

// apps/server/src/analysis/explanationGenerator.ts の CoachExplanation に対応する型。
// data/schemas/explanations.schema.json 準拠のフィールド(purpose/reason等)に、
// UI側でforming/matched/completed/noneを出し分けるためのstatusを加えたもの。
export type CoachStage = "current_shape" | "opponent_intent" | "opponent_next_aim";
export type CoachStatus = "none" | "forming" | "matched" | "completed";
export type ConfidenceLevel = "high" | "medium" | "low";

export interface CoachExplanation {
  id: string;
  stage: CoachStage;
  purpose: string;
  reason: string;
  refers_to_shape_id: string | null;
  refers_to_intent_id: string | null;
  confidence_level: ConfidenceLevel;
  glossary_terms: string[];
  template_id: string;
  status: CoachStatus;
}

// apps/server/src/analysis/shapeGraphRanking.ts の RankedReachableShape に対応する型
// (⑥目指せる形のランキング。上位3件、1位を唯一の正解として強調しない)。
export interface RankedReachableShape {
  shapeId: string;
  name: string;
  family: string;
  parentShapeId: string | null;
  status: "none" | "forming" | "completed";
  matchScore: number;
  adjustment: "prioritize" | "deprioritize" | null;
  reason: string | null;
  sourceIntentId: string | null;
}

// apps/server/src/analysis/candidateMoveExplanation.ts の CandidateMoveExplanationResult に
// 対応する型(⑧その手の目的。エンジンのMultiPV参考評価と対応付けできた候補手だけが入る)。
export type CandidateMoveExplanationStatus = "not_ready" | "ready";
export type CandidateMoveExplanationNotReadyReason =
  | "no_candidate_moves"
  | "shape_result_not_found"
  | "engine_reference_unavailable"
  | "insufficient_engine_data";

export interface CandidateMoveExplanation {
  id: string;
  purpose: string;
  move: string | null;
  reason: string;
  refers_to_shape_id: string | null;
  confidence_level: ConfidenceLevel;
}

export interface CandidateMoveExplanationResult {
  status: CandidateMoveExplanationStatus;
  notReadyReason: CandidateMoveExplanationNotReadyReason | null;
  explanations: CandidateMoveExplanation[];
}

// apps/server/src/api/stateResponse.ts の CandidateMoveState / ReachablePlanBody に対応する型。
// candidateMoveStateが"ready"であっても、candidateMove.statusが"not_ready"のことがある
// (エンジンの参考評価が取れても、評価データが不十分だった場合等)。
export type CandidateMoveState = "unavailable" | "pending" | "ready";

export interface ReachablePlanBody {
  reachableShapes: RankedReachableShape[];
  candidateMoveState: CandidateMoveState;
  candidateMove: CandidateMoveExplanationResult | undefined;
  /** ⑦⑧の計算に実際に使われたshapeId(ユーザーが選択したもの、または未選択/無効時の
   * フォールバックとしてranked[0]が採用されたもの)。reachableShapesの表示で
   * どれが現在の対象かを示すために使う。目指せる形が1件も無い場合はnull。 */
  resolvedTargetShapeId: string | null;
  /** Phase3 Unit1(計画崩れの検知のみ): 相手の手によって、ユーザーが着手する直前の
   * 計画の前提が機械的に崩れたかどうか。 */
  planChanged: boolean;
  /** Phase3 Unit2(崩れた理由の分類のみ): planChanged===falseの場合は常にnull。
   * 事実として断定できない場合は"unknown"になる(候補手が非合法になったことを
   * 無条件に「相手が原因」と断定しないため)。 */
  planChangeReason: PlanChangeReason | null;
}

// apps/server/src/analysis/planChangeReason.ts の PlanChangeReason に対応する型。
export type PlanChangeReason =
  | "candidate_piece_captured"
  | "candidate_move_illegal_due_to_check"
  | "candidate_piece_pinned"
  | "unknown";

/**
 * planChanged/planChangeReasonから、ユーザーに表示してよい理由文言を導く純粋関数
 * (DOM非依存、テスト容易性のためgameApi.ts側に置く)。
 *
 * - planChanged===falseの場合は常にnull(理由文言を絶対に表示しない)。
 *   plan.planChangeReasonの値だけでは判定せず、必ずplanChangedとの組み合わせで
 *   判定する(人間指示のとおり)。
 * - "unknown"、および既知の3種以外の値(サーバー側が将来追加する未知の理由を含む)は
 *   すべてnullを返す(=理由を断定しない安全側の既定動作)。新しい将棋ロジックは
 *   一切追加しない、既存の3分類をそのまま日本語文言へ変換するだけの対応表。
 */
export function getPlanChangeReasonMessage(
  plan: Pick<ReachablePlanBody, "planChanged" | "planChangeReason">,
): string | null {
  if (!plan.planChanged) return null;

  switch (plan.planChangeReason) {
    case "candidate_piece_captured":
      return "予定していた駒が、相手の手によって取られました。";
    case "candidate_move_illegal_due_to_check":
      return "相手の手によって、予定していた玉の移動ができなくなりました。";
    case "candidate_piece_pinned":
      return "相手の手によって、予定していた駒が動かせなくなりました。";
    default:
      // "unknown"・null・将来サーバー側が追加する未知の値は、理由を断定せず
      // 文言を表示しない(従来通り「前回の計画が使えなくなりました。」のみ)。
      return null;
  }
}

export interface GameStateResponse {
  sfen: string;
  moveHistory: string[];
  forcedPliesUsed: number;
  status: GameStatus;
  // 説明生成に失敗した場合(想定外の不整合等)はundefined(対局自体は継続する)。
  coach: CoachExplanation[] | undefined;
  // ⑤〜⑧(自分の目的・目指せる形・候補手・その手の目的)。エンジンのMultiPV参考評価は
  // POST /api/game/moveのレスポンスをブロックしないバックグラウンド処理のため、
  // candidateMoveState: "pending"の間はcandidateMoveがまだ無いことがある。
  plan: ReachablePlanBody;
  /**
   * Phase5: 現在の局面における、現在の手番の合法手一覧(USI形式)。
   * apps/server/src/rules/legalMoves.ts の判定結果をそのまま返すもので、
   * 合法手判定ロジック自体はサーバー側にある(ここでは再実装しない)。
   * 盤面クリックUIは、この一覧をfrom/drop種でフィルタして移動先を求める。
   */
  legalMoves: string[];
}

export interface MoveErrorResponse {
  error: string;
}

export function isMoveError(body: GameStateResponse | MoveErrorResponse): body is MoveErrorResponse {
  return "error" in body;
}

async function parseJson<T>(res: Response): Promise<T> {
  return (await res.json()) as T;
}

export async function fetchGameState(): Promise<GameStateResponse> {
  const res = await fetch("/api/game");
  return parseJson<GameStateResponse>(res);
}

export async function startNewGame(): Promise<GameStateResponse> {
  const res = await fetch("/api/game/new", { method: "POST" });
  return parseJson<GameStateResponse>(res);
}

export async function submitMove(move: string): Promise<GameStateResponse | MoveErrorResponse> {
  const res = await fetch("/api/game/move", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ move }),
  });
  return parseJson<GameStateResponse | MoveErrorResponse>(res);
}

/** 目標形選択UI(docs/PHASES.md Phase2完了条件)から、目指せる形の1つを選ぶ。
 * 選択したshapeIdが実際に採用されるかはサーバー側(stateResponse.ts)が判断する
 * (reachableShapesに含まれない場合は既存動作のranked[0]へ安全にフォールバックする)。 */
export async function selectTargetShape(shapeId: string): Promise<GameStateResponse | MoveErrorResponse> {
  const res = await fetch("/api/game/target-shape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ shapeId }),
  });
  return parseJson<GameStateResponse | MoveErrorResponse>(res);
}
