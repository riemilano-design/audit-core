// STEP T-3。docs/PLAYTEST_LOOP_PROPOSAL.md 4.1・6. の T-3、STEP T-3計画書
// 「実装してよい範囲」に従い、replay.ts が行っていた「一手ぶんの記録
// (immediate/ready の2行の組み立て)」「toCachedPlan」「エラー行」「summary行」の
// 組み立てを関数として切り出したもの。
//
// 【この切り出しについて】
// replay.ts(T-1)の出力(JSONLの各行のキー・値・出現順)は一切変えない。
// 呼び出し順・引数もreplay.tsの既存コードと同じにする(server.tsが行うのと同じ
// 本番関数の呼び出し順という前提を崩さないため)。explore.ts(T-3)もこれらの
// 関数を共有して使う。
//
// 本番関数(apps/server/src配下)はimportして呼ぶだけで、複製・改変はしない。
// 将棋の判断・評価・閾値・文言はここでは一切書かない。

import {
  buildStateResponseWithPlan,
  safeComputeReachablePlan,
  type BoardEvent,
  type CachedReachablePlan,
  type MoveOutcome,
  type PlanChangeReason,
  type StateResponseBodyWithPlan,
  type StateResponseOptions,
} from "../../../apps/server/src/api/stateResponse.js";
import type { GameState } from "../../../apps/server/src/game/gameSession.js";
import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import { measureEngineReference, type EngineReference } from "./engineReference.js";

/** server.tsのrunBackgroundPlanAnalysisと同じ組み立てでCachedReachablePlanを作る。
 * safeComputeReachablePlanが失敗(undefined)を返した場合はundefinedのまま
 * (buildStateResponseWithPlan側でcandidateMoveStateがpending扱いになる)。
 * replay.ts(T-1)のtoCachedPlanをそのまま移設したもの(挙動は変えていない)。 */
export function toCachedPlan(
  sfen: string,
  result: Awaited<ReturnType<typeof safeComputeReachablePlan>>,
): CachedReachablePlan | undefined {
  if (!result) return undefined;
  return {
    sfen,
    targetShapeId: result.targetShapeId,
    plan: {
      reachableShapes: result.reachableShapes,
      candidateMove: result.candidateMove,
      // STEP 5-F(A-4): ③(focusText)を詰め替える。ここを写し忘れると、
      // safeComputeReachablePlanが計算していても記録には null で載る
      // (buildStateResponseWithPlan が cachedPlan.plan.focusText を読むため)。
      // 2026-09-12 の A-4 で実際に踏んだ ― 引数を渡す側だけを直して、
      // 受け取った結果を詰め替える側を数えていなかった(計画書 14.13)。
      focusText: result.focusText,
    },
  };
}

/** 1行分の記録("kind":"record")の組み立て結果。 */
export interface RecordLineResult {
  line: string;
  response: StateResponseBodyWithPlan;
}

function buildRecordLine(params: {
  ply: number;
  sfen: string;
  senteMove: string | null;
  goteMove: string | null;
  phase: "immediate" | "ready";
  elapsedMs: number;
  response: StateResponseBodyWithPlan;
  /** STEP T-7(A-2)。ready行のみ渡す(immediate行はundefinedのまま渡し、
   * JSON.stringifyがキー自体を出力しない挙動を利用する)。 */
  engineReference?: EngineReference | null;
}): string {
  return JSON.stringify({
    kind: "record",
    ply: params.ply,
    sfen: params.sfen,
    senteMove: params.senteMove,
    goteMove: params.goteMove,
    phase: params.phase,
    elapsedMs: params.elapsedMs,
    response: params.response,
    engineReference: params.engineReference,
  });
}

/**
 * immediate行(cachedPlanを渡さない=バックグラウンド解析前の状態)の組み立て。
 * replay.tsの元のインライン処理と同じ引数の並びでbuildStateResponseWithPlanを呼ぶ。
 */
export function buildImmediateRecord(
  state: GameState,
  ply: number,
  senteMove: string | null,
  goteMove: string | null,
  planChanged: boolean,
  planChangeReason: PlanChangeReason | null,
  moveOutcome: MoveOutcome | null,
  boardEvents: BoardEvent[],
  // STEP U6-F(docs/STEP_UNIT6_PLAN_2026-09-12.md 10.7 D-4)。既定{}なので、
  // これを渡さない既存の呼び出し(explore.ts)は無変更で動く。
  options: StateResponseOptions = {},
): RecordLineResult {
  const t0 = Date.now();
  const response = buildStateResponseWithPlan(
    state,
    undefined,
    options,
    undefined,
    planChanged,
    planChangeReason,
    moveOutcome,
    boardEvents,
  );
  const elapsedMs = Date.now() - t0;
  const line = buildRecordLine({
    ply,
    sfen: state.sfen,
    senteMove,
    goteMove,
    phase: "immediate",
    elapsedMs,
    response,
  });
  return { line, response };
}

/** ready行の組み立て結果(readyMsPerPlyの集計に使うelapsedMsも含む)。
 * STEP 5-1(B-3、人間承認済み。LP-2): cachedPlanを併せて返す。この行が表す局面で
 * 実際にキャッシュされていた計画(バックグラウンド解析が未完了ならundefined)を、
 * replay.ts/explore.tsがserver.tsのbackgroundPlanと同じ役割で
 * safeComputeMoveOutcomeAfterMoveの新引数(displayedPlan)へ渡すためのもの。 */
export interface ReadyRecordLineResult extends RecordLineResult {
  elapsedMs: number;
  cachedPlan: CachedReachablePlan | undefined;
}

/**
 * ready行(safeComputeReachablePlanでバックグラウンド解析を実行した後の状態)の組み立て。
 * replay.tsの元のインライン処理と同じ引数の並びでsafeComputeReachablePlan →
 * toCachedPlan → buildStateResponseWithPlanを呼ぶ。
 */
export async function buildReadyRecord(
  state: GameState,
  ply: number,
  senteMove: string | null,
  goteMove: string | null,
  engine: LowPriorityEngine,
  planChanged: boolean,
  planChangeReason: PlanChangeReason | null,
  moveOutcome: MoveOutcome | null,
  boardEvents: BoardEvent[],
  // STEP T-7(A-2): engineReference(参考評価。ハーネスの観測)を測るための
  // engine/ノード数。呼び出し側の候補手計算用engine(nodes固定でラップ済みの
  // こともある)とは別に、raw(未ラップ)のLowPriorityEngineを渡すことで、
  // withFixedSearch(lib/fixedSearchEngine.ts)がgoMultiPvのnodesを常に自分の
  // 固定値へ上書きする挙動と衝突せず、referenceNodesがそのまま使われるようにする
  // (呼び出し側のnodes固定と独立に指定できる)。0なら測らない(engineReferenceは
  // null。referenceEngineは呼ばれない)。
  referenceEngine: LowPriorityEngine,
  referenceNodes: number,
  // STEP 5-F(A-4、人間承認済み): ③(相手の次の狙い)を記録へ載せるためのengine。
  // これを渡さないと computeFocusText が undefined を返し(stateResponse.ts の
  // `if (!focusEngine) return undefined;`)、記録の plan.focusText は**欄ごと消える**。
  // 2026-09-12 の実測では、記録44ファイル・ready 589行のすべてでこの欄が無かった。
  //
  // 【optionalにしない】省略可能な位置引数は、渡し忘れても呼び出しが成立し、
  // 型エラーにもテストの失敗にもならず、**記録だけが本番と違う姿になる**
  // (2026-09-12 に同じことが3回起きている。既知事項。docs/STEP_5-F_PLAN 14.12)。
  // 必須にして、次に呼び出しを増やす人が tsc で止まるようにする。
  //
  // 【呼び出し側は withFixedSearch で包むこと】computeFocusText は
  // measureEngineReference を nodes 無しで呼ぶため、素のハンドルを渡すと
  // movetime(時間で打ち切る探索)になり、compare.ts の3回一致が壊れる。
  // 本番は movetime・ハーネスは固定ノードで**同じものを測っていない**が、これは
  // engineReference(referenceNodes)と候補手(withFixedSearch)が既に受け入れて
  // いる取り引きと同じである(人間決定H-19)。
  //
  // 【engineとは別ハンドルにすること】asLowPriority()は呼ぶたびに独立した
  // クロージャを返すため、別ハンドルにすると③のMultiPV設定が候補手側へ
  // 持ち越されない(H-9・計画書9.6)。
  focusEngine: LowPriorityEngine,
  // STEP U6-F(docs/STEP_UNIT6_PLAN_2026-09-12.md 10.7 D-4)。既定{}なので、
  // これを渡さない既存の呼び出し(explore.ts)は無変更で動く。
  // safeComputeReachablePlanとbuildStateResponseWithPlanの両方へ同じoptionsを渡すこと
  // (片方だけ"current"のままだと、規則が効いた局面でcandidateMoveStateが
  // 必ずpendingへ落ちる。計画10.7 D-4の指摘)。
  options: StateResponseOptions = {},
): Promise<ReadyRecordLineResult> {
  const t0 = Date.now();
  const result = await safeComputeReachablePlan(state, engine, options, undefined, focusEngine);
  const cachedPlan = toCachedPlan(state.sfen, result);
  const response = buildStateResponseWithPlan(
    state,
    cachedPlan,
    options,
    undefined,
    planChanged,
    planChangeReason,
    moveOutcome,
    boardEvents,
  );
  const engineReference =
    referenceNodes > 0 ? await measureEngineReference(state.sfen, referenceEngine, referenceNodes) : null;
  const elapsedMs = Date.now() - t0;
  const line = buildRecordLine({
    ply,
    sfen: state.sfen,
    senteMove,
    goteMove,
    phase: "ready",
    elapsedMs,
    response,
    engineReference,
  });
  return { line, response, elapsedMs, cachedPlan };
}

/**
 * 想定内エラー("kind":"error")の1行を組み立てる。ply・moveは該当する場合のみ
 * 渡す(渡さなければキー自体を出力しない。replay.tsの元のodd_move_count行が
 * ply/moveを持たなかったのと同じ形を保つ)。
 */
export function buildErrorLine(fields: {
  ply?: number;
  move?: string;
  reason: string;
  message: string;
}): string {
  const obj: Record<string, unknown> = { kind: "error" };
  if (fields.ply !== undefined) obj.ply = fields.ply;
  if (fields.move !== undefined) obj.move = fields.move;
  obj.reason = fields.reason;
  obj.message = fields.message;
  return JSON.stringify(obj);
}

/** 正常終了時の末尾行("kind":"summary")を組み立てる。replay.tsの元の形のまま。 */
export function buildSummaryLine(fields: {
  plies: number;
  totalMs: number;
  readyMsPerPly: number[];
}): string {
  return JSON.stringify({
    kind: "summary",
    plies: fields.plies,
    totalMs: fields.totalMs,
    readyMsPerPly: fields.readyMsPerPly,
  });
}
