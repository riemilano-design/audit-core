// Phase 0時点での最小HTTPサーバー。
// apps/web(仮の盤面UI)から、対局状態の取得・指し手の送信を受け付ける。
// 対局は同時に1つだけ(Phase0の検証目的には十分。複数対局の管理は将来必要になれば設計する)。

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { resolveEnginePath } from "./engine/enginePath.js";
import { UsiEngine } from "./engine/usiEngine.js";
import {
  createInitialGameState,
  getStatus,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
} from "./game/gameSession.js";

const PORT = Number(process.env.PORT ?? 3000);

let state: GameState = createInitialGameState();
let engine: UsiEngine | undefined;
let engineReady: Promise<UsiEngine> | undefined;

// エンジンはUSIハンドシェイク(usi->usiok, isready->readyok)が完了するまで
// position/goを受け付けられない。初回呼び出し時に1度だけハンドシェイクし、以後使い回す。
function getEngine(): Promise<UsiEngine> {
  if (!engineReady) {
    engineReady = (async () => {
      const e = new UsiEngine(resolveEnginePath());
      e.start();
      await e.usiHandshake();
      await e.isReady();
      engine = e;
      return e;
    })();
  }
  return engineReady;
}

function stateResponse(current: GameState) {
  return { ...current, status: getStatus(current) };
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

  state = await playOpponentMove(state, await getEngine());
  sendJson(res, 200, stateResponse(state));
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

  if (req.method === "GET" && req.url === "/api/game") {
    sendJson(res, 200, stateResponse(state));
    return;
  }

  if (req.method === "POST" && req.url === "/api/game/new") {
    state = createInitialGameState();
    sendJson(res, 200, stateResponse(state));
    return;
  }

  if (req.method === "POST" && req.url === "/api/game/move") {
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
  engine?.quit();
  engine?.close();
  server.close(() => process.exit(0));
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
