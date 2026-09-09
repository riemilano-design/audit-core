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

// apps/server/src/api/stateResponse.ts の ReachableShapeBody に対応する型
// (⑥目指せる形のランキング。上位3件、1位を唯一の正解として強調しない)。
// 【Phase 7 Unit 3】この一覧をユーザーが選ぶUIは廃止した。順位は道のり・候補手の
// 対象決定には使わない(サーバー側 resolveRecognizedDirection が status だけで決める)。
// STEP ζ-5: reviewStatusの生値は公開されない(サーバー側のanalysis/nameExposure.tsに
// 判断を集約するため)。pendingReviewNoteはreview_statusが"draft"の場合にだけ入る注記で、
// それ以外はnull。web側はこの注記の文言を作らず、有無だけを見て表示する。
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
  pendingReviewNote: string | null;
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
  /** Unit 3: 候補手セクション全体に1回だけ添える但し書き。以前は候補手ごとの
   * reason末尾に同じ文が繰り返されていた。文言はサーバー側の既存のもの。 */
  sharedNotes: string[];
}

// apps/server/src/api/stateResponse.ts の CandidateMoveState / ReachablePlanBody に対応する型。
// candidateMoveStateが"ready"であっても、candidateMove.statusが"not_ready"のことがある
// (エンジンの参考評価が取れても、評価データが不十分だった場合等)。
export type CandidateMoveState = "unavailable" | "pending" | "ready";

// apps/server/src/api/stateResponse.ts の TargetShapeProgress に対応する型
// (Phase6 Unit1: 選択中の形が今どこまで出来ているか)。
// マス目は既にサーバー側(notation/japaneseSquare.ts)で日本語表記に変換済み。
export interface TargetShapeProgress {
  shapeId: string;
  name: string;
  /** Unit 3: ユーザーが選んだ目標形が「どういう形なのか」の説明
   * (data/shapes/*.json の characteristics)。web側では表示するだけ。 */
  description: string;
  matchedSquareLabels: string[];
  missingSquareLabels: string[];
  /**
   * STEP ζ-5: この形のreview_statusが"draft"の場合にだけ入る注記
   * (サーバー側analysis/nameExposure.tsのsite="shape")。それ以外はnull。
   * review_status自体(生の値)は公開されない。
   */
  pendingReviewNote: string | null;
}

// apps/server/src/api/stateResponse.ts の ShapeRouteSummary に対応する型
// (Phase6 Unit1: 未達成マスごとの経路)。
// 「選択した形 → 必要なマス → 現在の局面からの経路 → 今指せる最初の一手」という
// 因果をUIが示すための表示用データで、判定・計算はすべてサーバー側にある。
export interface ShapeRouteSummary {
  /** 目標マス(USI形式。識別用) */
  targetSquare: string;
  /** 目標マスに置く駒種(例: "玉") */
  targetPiece: string;
  /** 目標マス(日本語表記、例: "８八") */
  targetSquareLabel: string;
  /** 経路(日本語表記、例: "５九→６八→７八→８八") */
  routeLabel: string;
  remainingSteps: number;
  /** 経路の1手目を現在の局面で指せるか */
  hasPlayableFirstMove: boolean;
  /** 経路上で最初に自分の駒が居るマス(日本語表記)。無ければnull。 */
  blockingSquareLabel: string | null;
}

// apps/server/src/analysis/moveOutcomeExplanation.ts の MoveOutcomeMessage に対応する型
// (Phase6 Unit2: 直前の一手で何が変わったか)。
// kindはサーバー側の事実の種類(route_advanced等)。UI側は表示の出し分け用にしか使わないため、
// 種類の一覧はサーバー側だけが持つ(web側に同じ列挙を重複させない)。
export interface MoveOutcomeMessage {
  kind: string;
  text: string;
}

// apps/server/src/api/stateResponse.ts の LastMoveOutcomeBody に対応する型。
// 文言・マス目の日本語表記はすべてサーバー側で生成済みで、ここでは表示するだけ。
export interface LastMoveOutcomeBody {
  playedMoveLabel: string;
  opponentMoveLabel: string | null;
  /** Unit 3(情報構造の整理)で契約が変わった。**空配列になり得る。**
   * - 目標形が未選択のときは「特に変化なし」(no_notable_change)を返さない(既知事項 U0-1)
   * - 王手(check_received)は [0] の urgentMessages へ移し、ここには残さない
   * いずれもサーバー側(api/stateResponse.ts)で確定済みで、web側は表示するだけ。 */
  messages: MoveOutcomeMessage[];
}

// apps/server/src/analysis/nextConsiderationExplanation.ts の NextConsiderationMessage に
// 対応する型(Phase6 Unit4: 今の局面で分かっていること)。
// kindはサーバー側のメッセージ種別(in_check / route_first_move_playable /
// no_playable_route_first_move / shape_completed / ordering_note)。UI側は表示の
// 出し分けにしか使わないため、種類の一覧はサーバー側だけが持つ
// (MoveOutcomeMessageと同じ方針で、web側に同じ列挙を重複させない)。
export interface NextConsiderationMessage {
  kind: string;
  text: string;
}

// apps/server/src/api/stateResponse.ts の ShapeWeaknessBody に対応する型
// (Unit 3: [3]「なぜそれが重要か」に出す、完成した自分の形の弱点)。
// 文言は data/shapes/*.json の weak_against そのままで、web側は表示するだけ。
export interface ShapeWeaknessBody {
  shapeId: string;
  name: string;
  pendingReviewNote: string | null;
  text: string;
}

// apps/server/src/api/stateResponse.ts の ReferenceShapeBody に対応する型
// (Unit 3: [5]「参考になる囲い」)。完成形の駒配置は、座標の根拠が人間に確認される
// まで返ってこない(サーバー側 toReferenceShapes のコメント参照)。
export interface ReferenceShapeBody {
  shapeId: string;
  name: string;
  pendingReviewNote: string | null;
  characteristics: string;
  status: "none" | "forming" | "completed";
  matchedSquareLabels: string[];
  missingSquareLabels: string[];
}

// apps/server/src/api/stateResponse.ts の partitionUrgentMessages が返すメッセージ。
// どれが「今すぐ対処が必要」かの判断はサーバー側にあり、web側は表示するだけ。
export interface UrgentMessage {
  kind: string;
  text: string;
}

export interface ReachablePlanBody {
  reachableShapes: RankedReachableShape[];
  /** Phase6 Unit1: 選択中の形の未達成マスごとの経路。無い場合は空配列。 */
  routes: ShapeRouteSummary[];
  /** Phase6 Unit1: 選択中の形の進み具合。選択中の形が無い場合はnull。 */
  targetShapeProgress: TargetShapeProgress | null;
  /** Phase6 Unit1: 候補手(USI形式)→ マス目の日本語表記("５九→６八")の対応表。
   * 変換はサーバー側(notation/japaneseSquare.ts)にあり、ここでは表示に使うだけ。 */
  candidateMoveLabels: Record<string, string>;
  /** Phase6 Unit2: 直前の一手で何が変わったか。新規対局直後・目標形変更直後はnull。 */
  lastMoveOutcome: LastMoveOutcomeBody | null;
  /** Unit 3: [0]「今すぐ対処が必要なこと」。該当が無ければ空配列。 */
  urgentMessages: UrgentMessage[];
  /** Unit 3: [5]「参考になる囲い」。学習用の参考資料で、選択肢ではない。 */
  referenceShapes: ReferenceShapeBody[];
  /** Unit 3: 局面から認識できた方向が1つに定まらないときの一文。定まっていればnull。 */
  directionNote: string | null;
  /** Unit 3: [3]「なぜそれが重要か」に出す、完成した自分の形の弱点。無ければnull。 */
  shapeWeakness: ShapeWeaknessBody | null;
  /** Phase6 Unit4: 今の局面で分かっていること(直前の一手による差分ではない)。
   * 事実の抽出も文言生成もサーバー側(nextConsiderationDetector.ts /
   * nextConsiderationExplanation.ts)で完了しており、ここでは表示するだけ。
   * 表示すべき事実が無い場合・目標形が決まっていない場合・対局終了時は空配列。
   * 【Unit 3 で契約が変わった】王手("in_check")は urgentMessages へ移り、ここには来ない。
   * 候補手がある局面では "no_playable_route_first_move" も来ない
   * (どちらもサーバー側で確定済み。web側は表示するだけ)。 */
  nextConsiderations: NextConsiderationMessage[];
  candidateMoveState: CandidateMoveState;
  candidateMove: CandidateMoveExplanationResult | undefined;
  /**
   * STEP ζ-5(経路6): 候補手セクションに添える注意書き。選択中の形のreview_statusが
   * "draft"の場合にだけ入る(サーバー側analysis/nameExposure.tsのsite="section")。
   * 個々の候補手の説明文自体は変更されない。選択中の形が無い場合はnull。
   */
  pendingReviewNote: string | null;
  /** ⑦⑧の計算に実際に使われたshapeId(ユーザーが選択したもの)。未選択・無効値の
   * 場合はnull(Phase 7 Unit 0でranked[0]への自動フォールバックを廃止した。
   * 目標形は選ぶまで存在しない)。reachableShapesの表示でどれが現在の対象かを
   * 示すために使う。目指せる形が1件も無い場合もnull。 */
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

/**
 * Phase6 Unit3 ⑦: Phase3の「前回の計画が使えなくなりました。」を表示してよいかを返す。
 *
 * Unit2の`route_lost`メッセージ(「…道のりが、今の局面では続けられなくなりました。」)は
 * Phase3の通知と同じ事象を述べるため、両方出すと重複する。その場合はPhase3側を出さない。
 *
 * 判定ロジック(planChangeDetector/planChangeReason/moveOutcomeDetector)は一切変更せず、
 * ここで行うのは「どちらを表示するか」という表示上の判断だけ
 * (getPlanChangeReasonMessageと同じく、DOM非依存の純粋関数としてテストするためgameApi.tsに置く)。
 */
export function shouldShowPlanChangedNotice(
  plan: Pick<ReachablePlanBody, "planChanged" | "lastMoveOutcome">,
): boolean {
  if (!plan.planChanged) return false;
  const hasRouteLostMessage = plan.lastMoveOutcome?.messages.some((m) => m.kind === "route_lost") ?? false;
  return !hasRouteLostMessage;
}

/**
 * Phase6 Unit4: 「今の局面で分かっていること」ブロックを表示してよいかを返す。
 *
 * 判定材料はサーバーが返した件数だけで、将棋のルール判定・文言生成・文言の加工・
 * 並び替え・フィルタは一切行わない(それらはすべてサーバー側で確定済み)。
 * shouldShowPlanChangedNoticeと同じく、DOM非依存の純粋関数としてテストするために
 * gameApi.tsに置く。
 */
export function shouldShowNextConsiderations(
  plan: Pick<ReachablePlanBody, "nextConsiderations">,
): boolean {
  return plan.nextConsiderations.length > 0;
}

/**
 * Unit 3(情報構造の整理): 理由文が同一の候補手を1行にまとめる。
 *
 * Unit 1 の実測で、候補手3件のうち2件(７七→３三・７七→４四)の理由文が完全に同一で、
 * 同じ説明が2度並んでいた。ここで行うのは「reasonが文字列として等しいものをまとめ、
 * 指し手のラベルを並記する」だけで、将棋の判断・文言の生成は一切しない。
 * 並び順は入力順を保つ(サーバーが決めた順序を変えない)。
 * shouldShowPlanChangedNoticeと同じく、DOM非依存の純粋関数としてテストするため
 * gameApi.tsに置く。
 */
export interface GroupedCandidateMove {
  /** 同じ理由を持つ候補手の指し手ラベル(表示用。日本語表記が無い場合はUSIのまま)。 */
  moveLabels: string[];
  reason: string;
}

export function groupCandidateExplanationsByReason(
  explanations: Pick<CandidateMoveExplanation, "move" | "reason">[],
  candidateMoveLabels: Record<string, string>,
): GroupedCandidateMove[] {
  const groups: GroupedCandidateMove[] = [];
  for (const explanation of explanations) {
    const moveUsi = explanation.move ?? "";
    const label = candidateMoveLabels[moveUsi] ?? moveUsi;
    const existing = groups.find((group) => group.reason === explanation.reason);
    if (existing) {
      existing.moveLabels.push(label);
    } else {
      groups.push({ moveLabels: [label], reason: explanation.reason });
    }
  }
  return groups;
}

/**
 * STEP ζ-5: pendingReviewNoteの有無だけを見て、括弧書きの注記サフィックス("(注記)")を返す
 * (無ければ空文字)。review_status自体(生の値)はサーバー側から渡ってこないため、ここでは
 * 解釈しようがない。注記の文言はサーバー側(analysis/nameExposure.ts)が決めたものをそのまま
 * 使い、web側で新しい文言を作らない。名前と組み合わせる位置(「」の内側/外側)は呼び出し側に
 * 委ねる(人間承認済みの文言仕様に合わせるため)。shouldShowPlanChangedNoticeと同じく、
 * DOM非依存の純粋関数としてテストするためgameApi.tsに置く。
 */
export function reviewNoteSuffix(pendingReviewNote: string | null): string {
  return pendingReviewNote ? `(${pendingReviewNote})` : "";
}

/**
 * ⑧(MultiPV参考評価)の再取得を、あと何回まで試してよいかの上限。
 * エンジンは基準局面1回＋候補手ごとに1回ずつ直列に探索するため、完了まで数秒〜数十秒かかる。
 * 実機実測では1手あたり18〜19秒かかっている(以前の「約8秒」という前提は実測で否定された)。
 * 1回だけの再取得では間に合わず、サーバー側が"ready"になっているのに画面が「計算中」の
 * まま止まる状態が起きていた。上限を45秒相当(1.5秒×30回)にしているのは、実測18〜19秒に
 * 対して余裕を持たせるため。上限を設けて有限回で必ず止める方針自体は変えていない。
 */
export const PLAN_REFRESH_MAX_ATTEMPTS = 30;

/**
 * ⑧の再取得をもう一度予約してよいかを返す純粋関数
 * (DOM非依存、テスト容易性のためgameApi.ts側に置く)。
 *
 * - "ready"(解析完了)・"unavailable"(そもそも候補手が無い)になったら止める
 * - まだ"pending"でも、上限回数に達したら止める(無限にポーリングしない)
 *
 * 判定材料はサーバーが返した状態と試行回数だけで、将棋の判断は一切行わない。
 */
export function shouldRetryPlanRefresh(
  plan: Pick<ReachablePlanBody, "candidateMoveState">,
  attempt: number,
): boolean {
  if (plan.candidateMoveState !== "pending") return false;
  return attempt < PLAN_REFRESH_MAX_ATTEMPTS;
}

export interface GameStateResponse {
  sfen: string;
  moveHistory: string[];
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
  /**
   * Phase5: moveHistoryと同じ並び・同じ長さの、日本語棋譜表記(例: "７六歩")。
   * apps/server/src/notation/japaneseMoveHistory.ts(shogiops標準のmakeJapaneseMoveOrDrop)が
   * 生成したものをそのまま返す。変換できなかった手はnull(この場合UI側は
   * 対応するmoveHistoryのUSI表記を代わりに表示する)。棋譜表記の変換ロジックは
   * サーバー側にあり、ここでは再実装しない。
   */
  moveHistoryJapanese: (string | null)[];
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
 * (reachableShapesに含まれない場合は目標形は決まらない。Phase 7 Unit 0で
 * ranked[0]への自動フォールバックを廃止した。目標形は選ぶまで存在しない)。 */
export async function selectTargetShape(shapeId: string): Promise<GameStateResponse | MoveErrorResponse> {
  const res = await fetch("/api/game/target-shape", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ shapeId }),
  });
  return parseJson<GameStateResponse | MoveErrorResponse>(res);
}
