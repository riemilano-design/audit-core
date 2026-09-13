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
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import { measureEngineReference, type EngineReference } from "./engineReference.js";
import { readGitState, type GitRunner } from "./gitState.js";

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
      // 【searchPvs は**意図的に写さない**(STEP U6-L。忘れたのではない)】
      // CachedReachablePlan は**本番の型**であり、本番が持つキャッシュの形そのもの
      // である。ここへ読み筋を入れると、**本番が読み筋を保持することになり、
      // 「本番の挙動を変えない」という U6-L の前提が崩れる。**
      // 記録へ運ぶ経路は buildReadyRecord → buildRecordLine の searchPvs だけで、
      // この器は通さない(docs/STEP_U6-L_PLAN_2026-09-13.md 1.3)。
      // **良かれと思って写さないこと。**
    },
  };
}

/** 1行分の記録("kind":"record")の組み立て結果。 */
export interface RecordLineResult {
  line: string;
  response: StateResponseBodyWithPlan;
}

/** 記録1行ぶんの組み立てに要る値。
 *
 * 【STEP U6-L(計画書 1.3 決定3): phaseで判別する直和型にした理由】
 * 以前は engineReference が optional だった。immediate行には無い欄だからだが、
 * そのせいで**ready行で渡し忘れても型検査が通る**状態になっていた。省略可能な欄は、
 * 渡し忘れても呼び出しが成立し、型エラーにもテストの失敗にもならず、
 * **記録だけが本番と違う姿になる**(2026-09-12に同じ型を4回踏んでいる)。
 * phaseで判別することで、ready行では engineReference と searchPvs の**両方が必須**に
 * なり、増やした人がtscで止まる。JSONLの形は変えていない
 * (immediate行はキー自体を出力しない既存の挙動をそのまま使う)。 */
type RecordLineParams =
  | {
      phase: "immediate";
      ply: number;
      sfen: string;
      senteMove: string | null;
      goteMove: string | null;
      elapsedMs: number;
      response: StateResponseBodyWithPlan;
    }
  | {
      phase: "ready";
      ply: number;
      sfen: string;
      senteMove: string | null;
      goteMove: string | null;
      elapsedMs: number;
      response: StateResponseBodyWithPlan;
      /** STEP T-7(A-2)。**ハーネスが自分で別に測った**参考評価。
       * ③が使ったものとは別の探索である(だから読み筋は入っていない。
       * apps/server/src/analysis/engineReference.ts の EngineReferenceMeasurement 参照)。 */
      engineReference: EngineReference | null;
      /** STEP U6-L。**本番が③⑤を作るのに実際に使った探索**の読み筋。
       *
       * 【3つの状態を3つの値で表す(2026-09-13 の独立監査の指摘、必須3)】
       * - **欄が無い** … U6-L より前に取った古い記録(ready行では必ず出力するので、
       *   このハーネスが書いた記録には起きない)
       * - **null** … 本番の解析そのものが失敗した(safeComputeReachablePlanが
       *   undefinedを返した)。**測れなかったのであって、0本だったのではない**
       * - **[]** … 測ったが読み筋が1本も取れなかった
       *
       * 当初は失敗も `[]` にしていた。**「失敗した」と「測って0本」が同じ値になり、
       * 一つの値に二つの意味を持たせていた**(既知事項 P-23 と同じ型)。実データでは
       * 起きていなかったが、**起きていないことは設計が正しいことの根拠にならない。** */
      searchPvs: SearchPvObservation[] | null;
    };

function buildRecordLine(params: RecordLineParams): string {
  return JSON.stringify({
    kind: "record",
    ply: params.ply,
    sfen: params.sfen,
    senteMove: params.senteMove,
    goteMove: params.goteMove,
    phase: params.phase,
    elapsedMs: params.elapsedMs,
    response: params.response,
    engineReference: params.phase === "ready" ? params.engineReference : undefined,
    searchPvs: params.phase === "ready" ? params.searchPvs : undefined,
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
  // STEP U6-L: measureEngineReference は読み筋も返すようになったが、**ここでは捨てる。**
  // これはハーネスが自分で別に測った探索であり、③が見た読み筋ではない。
  // 記録へ入れると「読み筋がある」という事実だけが残り、それが③の見たものかどうかを
  // 後から誰も区別できなくなる(2026-09-12に engineReference 自体で3行やられている)。
  // 記録へ載せる読み筋は、下の result.searchPvs(本番が③⑤を作った探索)だけである。
  const engineReference =
    referenceNodes > 0
      ? (await measureEngineReference(state.sfen, referenceEngine, referenceNodes)).reference
      : null;
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
    // STEP U6-L: 本番(safeComputeReachablePlan)が実際に行った探索の読み筋を、
    // 同じ戻り値からそのまま写す(再探索しない。計画書 1.1 決定1)。
    // **解析が失敗した(result === undefined)ときは null。**空配列にしない ―
    // 空配列は「測ったが1本も取れなかった」の意味であり、**測れなかったことと
    // 混ぜない**(2026-09-13 の独立監査の指摘、必須3)。
    searchPvs: result ? result.searchPvs : null,
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

/**
 * STEP U6-R。JSONL の先頭の `meta` 行を組み立てる。**replay.ts と explore.ts の両方がこれを使う。**
 *
 * 【経緯(2026-09-13 の独立監査 2 回)】
 * - 1 回目: `meta` 行を replay.ts と explore.ts がそれぞれ手で組み立てており、
 *   **`dirty` 等を落としても 161 件の試験が 1 件も落ちなかった。** そこでこの関数へ集めた。
 * - 2 回目: 集めたあとも、呼び出し側が `{ ...readGitState(REPO_ROOT), dirty: false }` や
 *   手で作った値を渡せば、**欄は揃ったまま値だけ偽れた**(変異 X03・X04・X10 が沈黙)。
 *   **見張っていたのは「どの関数を呼ぶか」で、「何を渡すか」ではなかった。**
 *
 * 【この形で何が止まるか】
 * **git の状態は呼び出し側から受け取らない。`repoRoot` を受け取り、ここで `readGitState` を呼ぶ。**
 * 呼び出し側が値を偽るには `repoRoot` か `runGit` を変えるしかなく、それはソース照合で
 * 見張る(recorder.test.ts)。**照合は片側にしか壊れない** ― 整形を変えると緑でも落ち、
 * 照合する文字列を残したまま意味を変える書き換えは捕まらない。
 *
 * `runGit` は試験のためだけにある。**replay.ts / explore.ts は渡さない**(照合で見張る)。
 *
 * 【固定の欄が必ず勝つ(非必須 c)】
 * `extra` の型は固定の欄を `never` にしてあるが、`Record<string, unknown>` 型の変数で
 * 渡すと tsc を通って上書きできた。**そこで固定の欄を `extra` の後にもう一度展開する。**
 * 並びは最初の展開で決まるので、出力の欄の順は変わらない。
 *
 * 前半 8 欄の並び(kind / kifuId / startedAt / gitHead / dirty / dirtyPaths /
 * dirtyCount / enginePath)は両モードで同じであり、ここで固定する。
 */
export function buildMetaLine(fields: {
  kifuId: string;
  startedAt: string;
  repoRoot: string;
  enginePath: string;
  extra: Record<string, unknown> & {
    kind?: never;
    kifuId?: never;
    startedAt?: never;
    gitHead?: never;
    dirty?: never;
    dirtyPaths?: never;
    dirtyCount?: never;
    enginePath?: never;
  };
  /** 試験専用。本番の呼び出し側は渡さない。 */
  runGit?: GitRunner;
}): string {
  const gitState = readGitState(fields.repoRoot, fields.runGit);
  const fixed = {
    kind: "meta",
    kifuId: fields.kifuId,
    startedAt: fields.startedAt,
    gitHead: gitState.gitHead,
    dirty: gitState.dirty,
    dirtyPaths: gitState.dirtyPaths,
    dirtyCount: gitState.dirtyCount,
    enginePath: fields.enginePath,
  };
  return JSON.stringify({ ...fixed, ...fields.extra, ...fixed });
}
