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
  type CachedReachablePlan,
} from "./api/stateResponse.js";
import { resolveEnginePath } from "./engine/enginePath.js";
import { PrioritizedEngine } from "./engine/prioritizedEngine.js";
import { isScenarioId } from "./engine/scenarioOpponentOpening.js";
import { UsiEngine } from "./engine/usiEngine.js";
import {
  createInitialGameState,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
} from "./game/gameSession.js";

const PORT = Number(process.env.PORT ?? 3000);

let state: GameState = createInitialGameState();
let prioritizedEngine: PrioritizedEngine | undefined;
let prioritizedEngineReady: Promise<PrioritizedEngine> | undefined;

// ⑧のバックグラウンド解析結果のキャッシュ(完了した局面のsfen付き)。
let backgroundPlan: CachedReachablePlan | undefined;
// 現在バックグラウンド解析が進行中の局面(sfen)。同一局面への二重起動を防ぐ。
let backgroundPlanSfen: string | undefined;

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
 * という既存方針をこの関数全体にも適用する)。backgroundPlanSfenの解除は
 * 従来どおりfinallyで行う(成功・失敗いずれの経路でも確実に解除される)。
 */
async function runBackgroundPlanAnalysis(current: GameState): Promise<void> {
  if (backgroundPlanSfen === current.sfen) return; // 同一局面の解析が既に進行中

  backgroundPlanSfen = current.sfen;
  try {
    const engine = await getPrioritizedEngine();
    const result = await safeComputeReachablePlan(current, engine.asLowPriority());
    if (!result) return; // 計算失敗(safeComputeReachablePlan側でconsole.error済み)

    // 世代チェック: 解析完了時点で現在の対局状態が進んでいたら、この結果は
    // 古い局面に対するものなので破棄する(ユーザーが解析完了前に次の手を指した場合)。
    if (state.sfen !== current.sfen) return;

    backgroundPlan = { sfen: current.sfen, plan: result };
  } catch (err) {
    // getPrioritizedEngine()の失敗(エンジン起動・ハンドシェイク失敗等)を含め、
    // バックグラウンド解析のあらゆる失敗が未処理のPromise rejectionとして
    // 外へ漏れないようにする(対局そのものには影響させない)。
    console.error("バックグラウンド候補手解析(runBackgroundPlanAnalysis)でエラーが発生しました:", err);
  } finally {
    if (backgroundPlanSfen === current.sfen) backgroundPlanSfen = undefined;
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

async function handleMove(req: IncomingMessage, res: ServerResponse): Promise<void> {
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
  state = await playOpponentMove(state, engine.asHighPriority());

  // ⑤⑥⑦(エンジン不要)までを含めた状態を即座に返す。⑧(MultiPV参考評価)は
  // まだ完了していなければcandidateMoveState: "pending"になる(レスポンスをブロックしない)。
  sendJson(res, 200, buildStateResponseWithPlan(state, backgroundPlan));

  // レスポンス送出後、バックグラウンドで⑧を計算する(fire-and-forget)。
  void runBackgroundPlanAnalysis(state);
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
    // GET /api/gameは新規のエンジン解析を開始しない。既にバックグラウンドで
    // 完了・キャッシュされている⑧があれば返すだけ(buildStateResponseWithPlan内で
    // sfenが一致するかを確認する)。
    sendJson(res, 200, buildStateResponseWithPlan(state, backgroundPlan));
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/game/new") {
    // ?scenario=boh_gin | hayajikake を指定すると、検証用シナリオ対局として開始する
    // (docs/SCENARIOS.mdの本格的な対局シナリオ機能とは別の、Phase1検証専用の仕組み。
    // 詳細はscenarioOpponentOpening.tsを参照)。未指定・不明な値は従来どおりの通常対局。
    const scenarioParam = url.searchParams.get("scenario");
    state = createInitialGameState(isScenarioId(scenarioParam) ? scenarioParam : undefined);
    // 新しい対局を開始したので、前の対局のバックグラウンド解析結果は破棄する。
    // POST /api/game/new自体はMultiPVを実行しない(従来どおり軽量なレスポンス)。
    backgroundPlan = undefined;
    backgroundPlanSfen = undefined;
    sendJson(res, 200, buildStateResponseWithPlan(state, backgroundPlan));
    return;
  }

  if (req.method === "POST" && url.pathname === "/api/game/move") {
    handleMove(req, res).catch((err) => {
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
