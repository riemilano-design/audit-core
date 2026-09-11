// Phase 0時点での最小HTTPサーバー。
// apps/web(仮の盤面UI)から、対局状態の取得・指し手の送信を受け付ける。
// 対局は同時に1つだけ(Phase0の検証目的には十分。複数対局の管理は将来必要になれば設計する)。
//
// 【Phase2 ⑤〜⑧の非同期接続について】
// MultiPVによるエンジン参考評価(⑧)は、POST /api/game/moveのHTTPレスポンスを
// ブロックしない。人間の着手→合法性確認→相手の手→Phase1解析→⑤⑥⑦(エンジン不要)
// までを計算してレスポンスを返した後、バックグラウンドで⑧を計算し、完了した結果を
// `backgroundPlan`(モジュール変数、既存のengine/engineReadyと同じ設計方針)へ
// キャッシュする。次回のGET /api/game等で、そのキャッシュが現在の対局局面(sfen)と
// 一致する場合にのみ返す(stale result防止。新しいID体系は発明せず、既存のsfenを
// 世代識別子として使う)。
//
// 【エンジンアクセスの優先度について】
// 対局進行のbestmove探索(playOpponentMove、高優先度)とMultiPV参考評価
// (低優先度・バックグラウンド)が同一エンジンプロセスに同時にgoを送らないよう、
// engine/prioritizedEngine.ts(PrioritizedEngine)でラップして使う。

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import {
  buildStateResponseWithPlan,
  safeComputeReachablePlan,
  safeComputePlanChangeAfterMove,
  safeComputePlanChangeReasonAfterMove,
  safeComputeMoveOutcomeAfterMove,
  safeComputeBoardEventsAfterMove,
  type BoardEvent,
  type CachedReachablePlan,
  type MoveOutcome,
  type PlanChangeReason,
} from "./api/stateResponse.js";
import { resolveEnginePath } from "./engine/enginePath.js";
import { PrioritizedEngine } from "./engine/prioritizedEngine.js";
import { isDevScenarioEnabled, isScenarioId } from "./engine/scenarioOpponentOpening.js";
import { getApprovedScenarioVariants } from "./engine/scenarioRepository.js";
import { UsiEngine } from "./engine/usiEngine.js";
import {
  createInitialGameState,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
} from "./game/gameSession.js";

const PORT = Number(process.env.PORT ?? 3000);

let state: GameState = createInitialGameState(undefined, { variants: getApprovedScenarioVariants() });
let prioritizedEngine: PrioritizedEngine | undefined;
let prioritizedEngineReady: Promise<PrioritizedEngine> | undefined;

// 目標形選択UI(POST /api/game/target-shape)でユーザーが選んだshapeId。
// GameStateには含めない(対局進行そのものとは独立した、コーチ機能側の選択状態のため。
// backgroundPlan/backgroundPlanKeyと同じ「モジュール変数で保持し、新規対局開始時に
// 手動でリセットする」既存の設計方針を踏襲する)。実際に採用されるshapeId
// (resolvedTargetShapeId)は、reachableShapesに含まれるかどうかで
// stateResponse.ts側が決める(未指定・無効値の場合はnull。Phase 7 Unit 0で
// ranked[0]への自動フォールバックを廃止した。目標形は選ぶまで存在しない)。
let selectedTargetShapeId: string | undefined;

// ⑧のバックグラウンド解析結果のキャッシュ(完了した局面のsfen・目標形の組み合わせ付き)。
let backgroundPlan: CachedReachablePlan | undefined;
// 現在バックグラウンド解析が進行中の(局面, 選択中の目標形)の組み合わせ。
// 同一局面かつ同一選択への二重起動を防ぐ(sfenだけでなく選択も変わったら別扱いにする)。
let backgroundPlanKey: string | undefined;

// Phase3 Unit1(計画崩れの検知のみ、人間承認済み)。直近のPOST /api/game/moveで
// safeComputePlanChangeAfterMoveが判定した結果をここに保持し、以後のGET /api/game
// (schedulePlanRefreshによるポーリング等)でも同じ結果を返す(backgroundPlan/
// selectedTargetShapeIdと同じ「モジュール変数で保持し、次の状態変化まで使い回す」
// 既存の設計方針を踏襲する)。新規対局・目標形変更のいずれでもリセットする
// (承認事項5: 目標形変更・ユーザー自身の正常な進行を「計画崩れ」として扱わない)。
let lastPlanChanged = false;
// Phase3 Unit2(崩れた理由の分類のみ、人間承認済み)。lastPlanChangedと必ずペアで
// 更新・リセットする(lastPlanChangedがfalseの間はnullのまま)。
let lastPlanChangeReason: PlanChangeReason | null = null;
// Phase6 Unit2(直前の一手で何が変わったか)。lastPlanChanged/lastPlanChangeReasonと
// 同じ「モジュール変数で保持し、次の状態変化まで使い回す」方針。新規対局・目標形変更の
// いずれでもnullにリセットする(前の形についての差分説明を残さないため)。
let lastMoveOutcome: MoveOutcome | null = null;
// Phase6 Unit3(盤面で実際に起きたこと: 捕獲・王手・成り)。lastMoveOutcomeと同じ
// ライフサイクルで保持・リセットする(表示もlastMoveOutcomeと同じブロック内に出る)。
let lastBoardEvents: BoardEvent[] = [];

/** 局面(sfen)と選択中の目標形(selectedTargetShapeId、未選択ならundefined)から、
 * バックグラウンド解析の進行中判定に使うキーを作る。 */
function planKey(sfen: string, targetShapeId: string | undefined): string {
  return `${sfen}::${targetShapeId ?? ""}`;
}

// エンジンはUSIハンドシェイク(usi->usiok, isready->readyok)が完了するまで
// position/goを受け付けられない。初回呼び出し時に1度だけハンドシェイクし、以後使い回す。
function getPrioritizedEngine(): Promise<PrioritizedEngine> {
  if (!prioritizedEngineReady) {
    prioritizedEngineReady = (async () => {
      const e = new UsiEngine(resolveEnginePath());
      e.start();
      await e.usiHandshake();
      await e.isReady();
      const wrapped = new PrioritizedEngine(e);
      prioritizedEngine = wrapped;
      return wrapped;
    })();
  }
  return prioritizedEngineReady;
}

/**
 * ⑧(MultiPV参考評価 → 候補手説明)を、現在のstateとは独立にバックグラウンドで計算する。
 * fire-and-forgetで呼ばれる(呼び出し元はこのPromiseを待たない。`void runBackgroundPlanAnalysis(...)`)。
 * 完了時点でゲームの局面が進んでいたら(=ユーザーが次の手を指していたら)、
 * その結果は古いものとして破棄する(stale result防止)。
 *
 * 【例外処理について(最終監査で発見・修正)】
 * fire-and-forgetで呼ばれる(呼び出し元が.catch()を付けない)ため、この関数自体が
 * reject するPromiseを返すと、Node.jsの未処理Promise rejectionとなり
 * プロセスが終了しかねない。safeComputeReachablePlan()自体は内部の失敗
 * (エンジンタイムアウト等)を既に安全に捕捉して返す設計だが、その手前の
 * getPrioritizedEngine()(エンジンプロセスの起動・ハンドシェイク)が失敗した場合は
 * 従来ここで捕捉されていなかった。そのため、try全体を囲うcatchを追加し、
 * どの段階の失敗であっても外部へ例外を漏らさず、対局そのものには一切影響させない
 * (safeComputeReachablePlan/safeExplainPositionと同じ「失敗時はconsole.errorのみ」
 * という既存方針をこの関数全体にも適用する)。backgroundPlanKeyの解除は
 * 従来どおりfinallyで行う(成功・失敗いずれの経路でも確実に解除される)。
 */
/**
 * targetShapeIdAtTrigger は、この解析を起動した時点(呼び出し元がstateと共に
 * 同期的に読んだ時点)のselectedTargetShapeIdのスナップショット。
 * 非同期処理の間にモジュール変数selectedTargetShapeIdが変わっても、この関数内では
 * 常にトリガー時点の値を使う(prioritizedEngine.tsのposition()/goMultiPv()引数の
 * スナップショット方針と同じ考え方)。
 */
async function runBackgroundPlanAnalysis(
  current: GameState,
  targetShapeIdAtTrigger: string | undefined,
): Promise<void> {
  const key = planKey(current.sfen, targetShapeIdAtTrigger);
  if (backgroundPlanKey === key) return; // 同一局面・同一選択の解析が既に進行中

  backgroundPlanKey = key;
  try {
    const engine = await getPrioritizedEngine();
    const result = await safeComputeReachablePlan(current, engine.asLowPriority(), {}, targetShapeIdAtTrigger);
    if (!result) return; // 計算失敗(safeComputeReachablePlan側でconsole.error済み)

    // 世代チェック: 解析完了時点で現在の対局状態が進んでいたら、この結果は
    // 古い局面に対するものなので破棄する(ユーザーが解析完了前に次の手を指した場合)。
    if (state.sfen !== current.sfen) return;
    // 世代チェック(目標形選択): 解析完了時点で選択が変わっていたら、この結果は
    // 古い選択に対するものなので破棄する(ユーザーが解析完了前に別の形を選んだ場合)。
    if (selectedTargetShapeId !== targetShapeIdAtTrigger) return;

    backgroundPlan = {
      sfen: current.sfen,
      targetShapeId: result.targetShapeId,
      plan: { reachableShapes: result.reachableShapes, candidateMove: result.candidateMove },
    };
  } catch (err) {
    // getPrioritizedEngine()の失敗(エンジン起動・ハンドシェイク失敗等)を含め、
    // バックグラウンド解析のあらゆる失敗が未処理のPromise rejectionとして
    // 外へ漏れないようにする(対局そのものには影響させない)。
    console.error("バックグラウンド候補手解析(runBackgroundPlanAnalysis)でエラーが発生しました:", err);
  } finally {
    if (backgroundPlanKey === key) backgroundPlanKey = undefined;
  }
}

function sendJson(res: ServerResponse, statusCode: number, body: unknown): void {
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(JSON.stringify(body));
}

function readJsonBody(req: IncomingMessage): Promise<unknown> {
  return new Promise((resolve, reject) => {
    let raw = "";
    req.on("data", (chunk: Buffer) => {
      raw += chunk;
    });
    req.on("end", () => {
      if (!raw) {
        resolve(undefined);
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

/**
 * Phase5: POST /api/game/moveの直列化用キュー。
 *
 * 【背景・原因(人間承認済みの調査結果)】
 * handleMoveInternal は `state = playHumanMove(...)` の後、`await getPrioritizedEngine()` /
 * `await playOpponentMove(...)` という2箇所のawaitを経る。この間にNode.jsのイベントループが
 * 別のリクエストを処理できてしまうため、1件目のリクエストが「人間の着手だけ反映し、
 * 相手の応手がまだ反映されていない中間状態」のときに2件目のリクエストが割り込むと、
 * 2件目は「まだ相手の手番であるはずの局面」に対して人間の着手を試みることになり、
 * UIが直前に合法と判定して見せた手が非合法として拒否される(実際に再現・確認済み)。
 *
 * 【対応方針】
 * 合法手判定(getLegalMoves)・将棋ルール(applyMove等)は一切変更せず、
 * リクエストの処理順序だけを1件ずつに直列化する(既存ロジック上の不具合修正)。
 * moveQueueは常にresolveする(個々のリクエストの成否に関わらず、次のリクエストの
 * 開始を妨げない)。各リクエスト自身の成否・エラーレスポンスは、従来通り
 * handleMoveInternalの戻り値(Promise)がそのまま呼び出し元(server作成部の
 * .catch())へ伝播することで扱う(本キュー自体はエラーハンドリングの経路を変えない)。
 */
let moveQueue: Promise<void> = Promise.resolve();

async function handleMove(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const task = moveQueue.then(() => handleMoveInternal(req, res));
  moveQueue = task.then(
    () => undefined,
    () => undefined,
  );
  return task;
}

async function handleMoveInternal(req: IncomingMessage, res: ServerResponse): Promise<void> {
  let body: unknown;
  try {
    body = await readJsonBody(req);
  } catch {
    sendJson(res, 400, { error: "リクエストボディがJSONとして解析できません" });
    return;
  }

  const move = (body as { move?: unknown } | undefined)?.move;
  if (typeof move !== "string") {
    sendJson(res, 400, { error: "リクエストボディにmove(string)が必要です" });
    return;
  }

  // Phase3 Unit1: ユーザーが着手する直前の局面(=この時点のstate)を、計画崩れ検知の
  // 比較基準として保持しておく(承認事項A「ユーザーが着手する直前」のスナップショット)。
  const stateBeforeMove = state;

  try {
    state = playHumanMove(state, move);
  } catch (err) {
    if (err instanceof HumanMoveError) {
      sendJson(res, 400, { error: err.message });
      return;
    }
    throw err;
  }

  const engine = await getPrioritizedEngine();
  state = await playOpponentMove(state, engine.asHighPriority(), getApprovedScenarioVariants());

  // Phase3 Unit1: 相手の着手を経た現在の局面が、ユーザー着手直前の計画の前提を
  // 崩したかを判定する(エンジン非依存、候補Aのみ。planChangeDetector.ts参照)。
  const planChanged = safeComputePlanChangeAfterMove(stateBeforeMove, state, move, {}, selectedTargetShapeId);
  // Phase3 Unit2: 崩れた場合のみ理由を分類する(エンジン非依存。planChangeReason.ts参照)。
  const planChangeReason = planChanged
    ? safeComputePlanChangeReasonAfterMove(stateBeforeMove, state, move, {}, selectedTargetShapeId)
    : null;
  lastPlanChanged = planChanged;
  lastPlanChangeReason = planChangeReason;

  // Phase6 Unit2: 相手が実際に応手したかどうかは、指し手履歴の増分から確定的に分かる
  // (ユーザーの手だけ増えていれば相手は指していない)。推測はしない。
  const opponentMoveUsi =
    state.moveHistory.length === stateBeforeMove.moveHistory.length + 2
      ? (state.moveHistory[state.moveHistory.length - 1] ?? null)
      : null;
  lastBoardEvents = safeComputeBoardEventsAfterMove(stateBeforeMove, move, opponentMoveUsi);
  lastMoveOutcome = safeComputeMoveOutcomeAfterMove(
    stateBeforeMove,
    state,
    move,
    opponentMoveUsi,
    {},
    selectedTargetShapeId,
    planChangeReason,
    // STEP 5-1(B-2、人間承認済み。LP-2): backgroundPlanはこの時点(playHumanMove/
    // playOpponentMoveの直後)ではstateBeforeMoveのまま(runBackgroundPlanAnalysis完了時
    // にのみ書き換わる)。「実際に表示していた計画」としてそのまま渡す
    // (backgroundPlan未設定ならnull=表示していた計画が無い)。
    backgroundPlan ?? null,
  );

  // ⑤⑥⑦(エンジン不要)までを含めた状態を即座に返す。⑧(MultiPV参考評価)は
  // まだ完了していなければcandidateMoveState: "pending"になる(レスポンスをブロックしない)。
  sendJson(
    res,
    200,
    buildStateResponseWithPlan(state, backgroundPlan, {}, selectedTargetShapeId, planChanged, planChangeReason, lastMoveOutcome, lastBoardEvents),
  );

  // レスポンス送出後、バックグラウンドで⑧を計算する(fire-and-forget)。
  void runBackgroundPlanAnalysis(state, selectedTargetShapeId);
}

/**
 * 目標形選択UI(docs/PHASES.md Phase2完了条件「ユーザーが2〜3個の候補から目標形を
 * 選べるUI」)から呼ばれる。選択されたshapeIdが実際に現在のreachableShapesに
 * 含まれるかどうかの妥当性判定はここでは行わない(stateResponse.ts側の
 * computeRankedPlanContextが、局面が進むたびに変わるreachableShapesと突き合わせて
 * 都度判定する。含まれなければ目標形は決まらない。Phase 7 Unit 0で
 * ranked[0]への自動フォールバックを廃止した。目標形は選ぶまで存在しない)。
 */
async function handleTargetShape(req: IncomingMessage, res: ServerResponse): Promise<void> {
  let body: unknown;
  try {
    body = await readJsonBody(req);
  } catch {
    sendJson(res, 400, { error: "リクエストボディがJSONとして解析できません" });
    return;
  }

  const shapeId = (body as { shapeId?: unknown } | undefined)?.shapeId;
  if (typeof shapeId !== "string") {
    sendJson(res, 400, { error: "リクエストボディにshapeId(string)が必要です" });
    return;
  }

  selectedTargetShapeId = shapeId;
  // 選択が変わった時点で、古い選択に対するバックグラウンド解析結果を破棄する。
  // (buildStateResponseWithPlan側のsfen+targetShapeId一致チェックだけでも古い結果は
  // 弾かれるが、不要になったキャッシュを明示的に破棄して残さないようにする。)
  backgroundPlan = undefined;
  backgroundPlanKey = undefined;
  // Phase3 Unit1/Unit2(承認事項5): 目標形の変更はユーザー自身の操作であり、
  // 「相手の手による計画崩れ」ではないため、計画崩れ状態・理由をリセットする
  // (両者は必ずペアで更新・リセットする)。
  lastPlanChanged = false;
  lastPlanChangeReason = null;
  // 目標形が変わった直後は、前の形についての差分説明を絶対に残さない(Phase6 Unit2)。
  lastMoveOutcome = null;
  lastBoardEvents = [];

  // 局面(sfen)自体は変わらないため、⑤⑥(エンジン不要)は同期的に返しつつ、
  // ⑦⑧はcandidateMoveState: "pending"から始まり、バックグラウンド解析の完了を待つ
  // (POST /api/game/moveと同じ非同期方針)。
  sendJson(
    res,
    200,
    buildStateResponseWithPlan(state, backgroundPlan, {}, selectedTargetShapeId, lastPlanChanged, lastPlanChangeReason, lastMoveOutcome, lastBoardEvents),
  );

  void runBackgroundPlanAnalysis(state, selectedTargetShapeId);
}

const server = createServer((req, res) => {
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    });
    res.end();
    return;
  }

  // req.urlはパス+クエリ文字列(例: "/api/game/new?scenario=hayajikake")なので、
  // ルーティング判定にはpathnameだけを使う(クエリの有無で既存の一致判定を壊さないため)。
  const url = new URL(req.url ?? "/", "http://localhost");

  if (req.method === "GET" && url.pathname === "/api/game") {
    // GET /api/gameは、既にバックグラウンドで完了・キャッシュされている⑧があれば
    // それを返す(buildStateResponseWithPlan内でsfen・選択中の目標形の両方が
    // 一致するかを確認する)。
    // Phase3 Unit1/Unit2: lastPlanChanged/lastPlanChangeReasonは直近の
    // POST /api/game/moveでの判定結果をそのまま返す(このリクエスト自体は
    // 着手を伴わないため、新たな判定は行わない)。
    //
    // ただし、返す予定のcandidateMoveStateが"pending"(まだ解析結果が無い)場合に
    // 限り、runBackgroundPlanAnalysisを起動する。ページを開いただけ(POSTを一度も
    // 経ていない)の経路には解析を起動する呼び出し元が存在せず、候補手が
    // 「計算中」のまま永久に止まっていたため(実機確認で判明)。
    // 既にキャッシュ済み("ready"/"unavailable")なら再起動する必要は無く、
    // 同一局面・同一選択への多重起動はrunBackgroundPlanAnalysis冒頭の
    // backgroundPlanKeyによるガードがPOST側と同様に防ぐ。
    const body = buildStateResponseWithPlan(state, backgroundPlan, {}, selectedTargetShapeId, lastPlanChanged, lastPlanChangeReason, lastMoveOutcome, lastBoardEvents);

    if (body.plan.candidateMoveState === "pending") {
      void runBackgroundPlanAnalysis(state, selectedTargetShapeId);
    }

    sendJson(res, 200, body);
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/game/new") {
    // ?scenario=boh_gin | hayajikake を指定すると、検証用シナリオ対局として開始する
    // (docs/SCENARIOS.mdの本格的な対局シナリオ機能とは別の、Phase1検証専用の仕組み。
    // 詳細はscenarioOpponentOpening.tsを参照)。
    // STEP ζ-4c-1(C-5): この`?scenario=`はSHOGI_DEV_SCENARIO環境変数が設定された
    // 開発モードでのみ有効。未設定の場合は指定があっても無視し、通常対局として開始する
    // (クライアントが相手AIの制御状態を指定できる経路を通常運用では作らないため。
    // docs/ARCHITECTURE.md 6.)。未指定・不明な値も従来どおり通常対局。
    const scenarioParam = url.searchParams.get("scenario");
    const scenario = isDevScenarioEnabled() && isScenarioId(scenarioParam) ? scenarioParam : undefined;
    state = createInitialGameState(scenario, { variants: getApprovedScenarioVariants() });
    // 新しい対局を開始したので、前の対局のバックグラウンド解析結果・目標形選択は破棄する。
    // POST /api/game/new自体はMultiPVを実行しない(従来どおり軽量なレスポンス)。
    backgroundPlan = undefined;
    backgroundPlanKey = undefined;
    selectedTargetShapeId = undefined;
    // Phase3 Unit1/Unit2(承認事項D): 新規対局開始時は計画崩れ状態・理由も
    // リセットする(両者は必ずペアで更新・リセットする)。
    lastPlanChanged = false;
    lastPlanChangeReason = null;
    lastMoveOutcome = null;
    lastBoardEvents = [];
    sendJson(
      res,
      200,
      buildStateResponseWithPlan(state, backgroundPlan, {}, selectedTargetShapeId, lastPlanChanged, lastPlanChangeReason, lastMoveOutcome, lastBoardEvents),
    );

    // レスポンス送出後、バックグラウンドで⑧を計算する(fire-and-forget)。
    // POST /api/game/move・POST /api/game/target-shape と同じ扱い。これが無いと、
    // 新規対局直後は解析が一度も起動せず、候補手が「計算中」のまま止まる
    // (Phase6の通し確認で判明。二重起動防止・stale result防止は
    // runBackgroundPlanAnalysis側のbackgroundPlanKey/planKeyがそのまま効く)。
    void runBackgroundPlanAnalysis(state, selectedTargetShapeId);
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/game/move") {
    handleMove(req, res).catch((err) => {
      console.error(err);
      sendJson(res, 500, { error: "サーバー内部エラー" });
    });
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/game/target-shape") {
    handleTargetShape(req, res).catch((err) => {
      console.error(err);
      sendJson(res, 500, { error: "サーバー内部エラー" });
    });
    return;
  }

  sendJson(res, 404, { error: "not found" });
});

server.listen(PORT, () => {
  console.log(`shogi-coach server listening on http://localhost:${PORT}`);
});

function shutdown(): void {
  prioritizedEngine?.quit();
  prioritizedEngine?.close();
  server.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
