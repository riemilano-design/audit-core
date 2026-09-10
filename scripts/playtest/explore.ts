// STEP T-3(探索モードと対局者の多様化)。
// docs/PLAYTEST_LOOP_PROPOSAL.md 4.2・4.5・4.6・6. の T-3、STEP T-3計画書に従う。
//
// 固定棋譜モード(replay.ts、T-1)は「回帰」用(一度記録した局面列を再生し、
// 変更前後の検出数を比べる)。本モジュールは「発見」用であり、相手を本番と同じ
// (素のエンジン)に戻し、自分側は5プロファイル(lib/players.ts)で指させることで
// 未知の局面列を作る。
//
// 【探索の出力は"観測"であることについて(4.5の境界)】
// 出力(JSONL・kifu JSON)は観測にすぎず、何も拘束しない。末尾で行うcheck.tsの
// 実行結果(候補事象)も、既知事項・仕様・kifu/への登録に自動では昇格しない。
// この境界を越える操作(既知事項への追加・kifu/への登録・不変条件のapproved化)は
// 一切行わない(人間の判断)。
//
// 本番関数(apps/server/src配下)はimportして呼ぶだけで、複製・改変はしない。
// 将棋の判断・評価・閾値・文言はここでは一切書かない。相手AIの手加減・強さ調整も
// しない(相手は本番と同一: playOpponentMove(state, engine.asHighPriority(),
// getApprovedScenarioVariants())、movetime 1000ms)。
//
// 使い方: npx tsx scripts/playtest/explore.ts --games 10 --seed 1 [--plies 60] [--out-dir <dir>]

import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  safeComputePlanChangeAfterMove,
  safeComputePlanChangeReasonAfterMove,
  safeComputeMoveOutcomeAfterMove,
  safeComputeBoardEventsAfterMove,
} from "../../apps/server/src/api/stateResponse.js";
import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { getApprovedScenarioVariants } from "../../apps/server/src/engine/scenarioRepository.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import {
  createInitialGameState,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
} from "../../apps/server/src/game/gameSession.js";
import { isGameOver } from "../../apps/server/src/rules/gameStatus.js";
import { buildErrorLine, buildImmediateRecord, buildReadyRecord, buildSummaryLine } from "./lib/recorder.js";
import {
  DEFAULT_PROFILE_ORDER,
  DEFAULT_RANDOM_RATE,
  pickMove,
  type PlayerProfileId,
  type S3ScriptState,
} from "./lib/players.js";
import { Prng } from "./lib/prng.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT_DIR = __dirname;
const REPO_ROOT = path.join(__dirname, "..", "..");
const CHECK_TS_PATH = path.join(SCRIPT_DIR, "check.ts");

const DEFAULT_GAMES = 10;
const DEFAULT_SEED = 1;
const DEFAULT_PLIES_CAP = 60;

/** 終了理由。将棋の良し悪しの判断は含まず、いずれも機械的な事実だけを表す。 */
type EndReason = "game_over" | "opponent_no_move" | "self_no_move" | "plies_cap" | "human_move_error";

interface CliOptions {
  games: number;
  seed: number;
  pliesCap: number;
  outDir: string;
}

function parseArgs(argv: string[], runStartedAt: string): CliOptions {
  const getFlag = (name: string): string | undefined => {
    const index = argv.indexOf(name);
    return index !== -1 ? argv[index + 1] : undefined;
  };

  const games = Number(getFlag("--games") ?? DEFAULT_GAMES);
  const seed = Number(getFlag("--seed") ?? DEFAULT_SEED);
  const pliesCap = Number(getFlag("--plies") ?? DEFAULT_PLIES_CAP);
  const outDirArg = getFlag("--out-dir");
  const outDir = outDirArg
    ? path.resolve(outDirArg)
    : path.join(SCRIPT_DIR, "out", `explore-${runStartedAt.replace(/[:.]/g, "-")}`);

  return { games, seed, pliesCap, outDir };
}

/** --games に対して既定の10局構成(S1×2、S2×2、S3×2、E×2、R×2)を繰り返し割り当てる。 */
function profileForGameIndex(gameIndex1Based: number): PlayerProfileId {
  const order = DEFAULT_PROFILE_ORDER;
  const zeroBased = (gameIndex1Based - 1) % order.length;
  // order.length > 0 であることは定数配列から自明。
  return order[zeroBased] as PlayerProfileId;
}

interface GameRunResult {
  gameNumber: number;
  profile: PlayerProfileId;
  seed: number;
  kifuId: string;
  plies: number;
  endReason: EndReason;
  totalMs: number;
  moves: string[];
  jsonlPath: string;
  kifuJsonPath: string;
}

async function runOneGame(params: {
  gameNumber: number;
  profile: PlayerProfileId;
  seed: number;
  pliesCap: number;
  runStartedAt: string;
  outDir: string;
  engine: PrioritizedEngine;
}): Promise<GameRunResult> {
  const { gameNumber, profile, seed, pliesCap, runStartedAt, outDir, engine } = params;
  const nn = String(gameNumber).padStart(2, "0");
  const kifuId = `explore-${runStartedAt}-${nn}-${profile}`;
  const gameStartedAt = new Date().toISOString();

  const lines: string[] = [];
  const moves: string[] = [];
  const readyMsPerPly: number[] = [];
  const prng = new Prng(seed);
  const s3: S3ScriptState = { cursor: 0 };
  const randomRate = profile === "R" ? DEFAULT_RANDOM_RATE : 0;

  let gitHead: string | null;
  try {
    gitHead = execFileSync("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT }).toString().trim();
  } catch {
    gitHead = null;
  }

  const enginePath = resolveEnginePath();
  lines.push(
    JSON.stringify({
      kind: "meta",
      kifuId,
      startedAt: gameStartedAt,
      gitHead,
      enginePath,
      mode: "explore",
      profile,
      seed,
      randomRate,
      pliesCap,
    }),
  );

  const jsonlPath = path.join(outDir, `game-${nn}.jsonl`);
  const kifuJsonPath = path.join(outDir, `game-${nn}.kifu.json`);

  const totalStart = Date.now();
  let state: GameState = createInitialGameState(undefined, { variants: getApprovedScenarioVariants() });
  let endReason: EndReason = "plies_cap";
  let pliesCompleted = 0;
  let totalMs = 0;

  // 初期局面(POST /api/game/new相当)。
  {
    const { line } = buildImmediateRecord(state, 0, null, null, false, null, null, []);
    lines.push(line);
  }
  let latestReady = await buildReadyRecord(
    state,
    0,
    null,
    null,
    engine.asLowPriority(),
    false,
    null,
    null,
    [],
  );
  readyMsPerPly.push(latestReady.elapsedMs);
  lines.push(latestReady.line);

  try {
    while (true) {
      if (isGameOver(state.sfen)) {
        endReason = "game_over";
        break;
      }
      if (state.moveHistory.length >= pliesCap) {
        endReason = "plies_cap";
        break;
      }

      const stateBeforeMove = state;
      const senteMove = await pickMove(profile, state.sfen, latestReady.response, {
        prng,
        randomRate,
        engine: engine.asHighPriority(),
        s3,
      });

      if (senteMove === undefined) {
        endReason = "self_no_move";
        break;
      }

      try {
        state = playHumanMove(state, senteMove);
      } catch (err) {
        if (err instanceof HumanMoveError) {
          lines.push(
            buildErrorLine({
              ply: stateBeforeMove.moveHistory.length,
              move: senteMove,
              reason: "human_move_error",
              message: err.message,
            }),
          );
          endReason = "human_move_error";
          break;
        }
        throw err;
      }
      moves.push(senteMove);

      state = await playOpponentMove(state, engine.asHighPriority(), getApprovedScenarioVariants());

      const goteMove =
        state.moveHistory.length === stateBeforeMove.moveHistory.length + 2
          ? (state.moveHistory[state.moveHistory.length - 1] ?? null)
          : null;
      if (goteMove !== null) moves.push(goteMove);

      const planChanged = safeComputePlanChangeAfterMove(stateBeforeMove, state, senteMove, {}, undefined);
      const planChangeReason = planChanged
        ? safeComputePlanChangeReasonAfterMove(stateBeforeMove, state, senteMove, {}, undefined)
        : null;
      const boardEvents = safeComputeBoardEventsAfterMove(stateBeforeMove, senteMove, goteMove);
      const moveOutcome = safeComputeMoveOutcomeAfterMove(
        stateBeforeMove,
        state,
        senteMove,
        goteMove,
        {},
        undefined,
        planChangeReason,
      );

      const ply = state.moveHistory.length;

      {
        const { line } = buildImmediateRecord(
          state,
          ply,
          senteMove,
          goteMove,
          planChanged,
          planChangeReason,
          moveOutcome,
          boardEvents,
        );
        lines.push(line);
      }
      latestReady = await buildReadyRecord(
        state,
        ply,
        senteMove,
        goteMove,
        engine.asLowPriority(),
        planChanged,
        planChangeReason,
        moveOutcome,
        boardEvents,
      );
      readyMsPerPly.push(latestReady.elapsedMs);
      lines.push(latestReady.line);

      pliesCompleted = ply;

      if (goteMove === null) {
        // 相手が指さなかった(既にisGameOverだった、またはエンジンがbestmoveを
        // 返さなかった)。次のループ先頭のisGameOverチェックに委ねず、ここで
        // 確定的に判定する(playOpponentMoveはどちらの場合もstateを不変で返すため、
        // isGameOverの真偽だけで区別できる)。
        endReason = isGameOver(state.sfen) ? "game_over" : "opponent_no_move";
        break;
      }
    }
  } finally {
    totalMs = Date.now() - totalStart;
    lines.push(buildSummaryLine({ plies: pliesCompleted, totalMs, readyMsPerPly }));
    lines.push(JSON.stringify({ kind: "end", reason: endReason, ply: pliesCompleted }));

    writeFileSync(jsonlPath, `${lines.join("\n")}\n`, "utf-8");
    writeFileSync(
      kifuJsonPath,
      `${JSON.stringify({ id: kifuId, source: "explore", profile, seed, moves }, null, 2)}\n`,
      "utf-8",
    );
  }

  return {
    gameNumber,
    profile,
    seed,
    kifuId,
    plies: pliesCompleted,
    endReason,
    totalMs,
    moves,
    jsonlPath,
    kifuJsonPath,
  };
}

async function main(): Promise<void> {
  const runStartedAt = new Date().toISOString();
  const options = parseArgs(process.argv.slice(2), runStartedAt);

  mkdirSync(options.outDir, { recursive: true });

  const enginePath = resolveEnginePath();
  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  await rawEngine.usiHandshake();
  await rawEngine.isReady();
  const engine = new PrioritizedEngine(rawEngine);

  const results: GameRunResult[] = [];
  try {
    for (let gameNumber = 1; gameNumber <= options.games; gameNumber++) {
      const profile = profileForGameIndex(gameNumber);
      const gameSeed = options.seed + gameNumber;
      console.log(`[explore] 局 ${gameNumber}/${options.games}(profile: ${profile}, seed: ${gameSeed}) 開始`);
      const result = await runOneGame({
        gameNumber,
        profile,
        seed: gameSeed,
        pliesCap: options.pliesCap,
        runStartedAt,
        outDir: options.outDir,
        engine,
      });
      results.push(result);
      console.log(
        `[explore] 局 ${gameNumber}/${options.games} 終了: 手数=${result.plies}, 理由=${result.endReason}, ${result.totalMs}ms`,
      );
    }
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }

  // check.ts(T-2、変更不可)を子プロセスとして呼び、候補事象の報告を
  // report.md(標準出力そのまま)・report.json(--json)として同じディレクトリへ書く。
  const jsonlPaths = results.map((r) => r.jsonlPath);
  const reportJsonPath = path.join(options.outDir, "report.json");
  const checkStdout = execFileSync(
    "npx",
    ["tsx", CHECK_TS_PATH, ...jsonlPaths, "--json", reportJsonPath],
    { cwd: REPO_ROOT, encoding: "utf-8" },
  );
  writeFileSync(path.join(options.outDir, "report.md"), checkStdout, "utf-8");

  console.log("");
  console.log(`[explore] 完了。出力先: ${options.outDir}`);
  for (const result of results) {
    console.log(
      `  game-${String(result.gameNumber).padStart(2, "0")}: profile=${result.profile} seed=${result.seed} plies=${result.plies} endReason=${result.endReason} totalMs=${result.totalMs}`,
    );
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
