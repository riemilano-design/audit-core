// STEP T-3(探索モードと対局者の多様化)。
// docs/PLAYTEST_LOOP_PROPOSAL.md 4.2・4.5・4.6・6. の T-3、STEP T-3計画書に従う。
//
// 固定棋譜モード(replay.ts、T-1)は「回帰」用(一度記録した局面列を再生し、
// 変更前後の検出数を比べる)。本モジュールは「発見」用であり、相手を本番と同じ
// (素のエンジン)に戻し、自分側はプロファイル(lib/players.ts の S1〜R の 5 つと、STEP D3 の B・B2 =
// lib/beginnerProfile.ts)で指させることで
// 未知の局面列を作る。
//
// 【探索の出力は"観測"であることについて(4.5の境界)】
// 出力(JSONL・kifu JSON)は観測にすぎず、何も拘束しない。末尾で行うcheck.tsの
// 実行結果(候補事象)も、既知事項・仕様・kifu/への登録に自動では昇格しない。
// この境界を越える操作(既知事項への追加・kifu/への登録・不変条件のapproved化)は
// 一切行わない(人間の判断)。
//
// 本番関数(apps/server/src配下)はimportして呼ぶだけで、複製・改変はしない。
// 将棋の判断・評価・閾値・文言はここでは一切書かない。
// **既定では相手は本番と同一**(playOpponentMove(state, 相手のハンドル, getApprovedScenarioVariants())、movetime 1000ms)。
// **--opponent-nodes N は開発・検証専用の設定**で、相手の go にだけ nodes を渡して相手を弱くする
// (STEP D3b。本番の gameSession.ts は変えない。先手の E 読み・候補手・③・engineReference には渡らない。
// 包みとハンドルの作り方は lib/opponentEngine.ts にあり、そちらに試験がある)。
//
// 使い方: npx tsx scripts/playtest/explore.ts --games 10 --seed 1 [--plies 60] [--out-dir <dir>] [--profile <S1|S2|S3|E|R|B|B2>] [--opponent-nodes <N>]
//
// STEP D3: --profile を付けると全局をそのプロファイルで指す(無ければ既定の10局構成。分からない値はエラー)。
// B・B2 の局は、棋譜 JSON に tiers(先手の手ごとに、どの段で決めたか)を足す。振り分けと棋譜 JSON の組み立ては
// lib/players.ts の関数にあり、そちらに試験がある(ここに判断を残さない)。

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
import { buildErrorLine, buildImmediateRecord, buildReadyRecord, buildSummaryLine, buildMetaLine } from "./lib/recorder.js";
import { buildHighPriorityHandles, parseOpponentNodesOption } from "./lib/opponentEngine.js";
import type { BeginnerTier } from "./lib/beginnerProfile.js";
import {
  buildKifuJsonText,
  DEFAULT_RANDOM_RATE,
  parseProfileOption,
  pickMoveWithTier,
  profileForGame,
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

// STEP T-7(A-2)。docs/STEP_T-7_PLAN_2026-09-11.md 2. A-2に従う。探索モードは
// 相手の手・自分側プロファイルの条件を一切変えない(既存のとおり。STEP D3b の --opponent-nodes を付けたときだけ相手の探索量が変わる)。engineReference
// (参考評価。ハーネスの観測)だけは固定ノード数で測る(replay.tsの既定と同じ値)。
const DEFAULT_REFERENCE_NODES = 4_000_000;

/** 終了理由。将棋の良し悪しの判断は含まず、いずれも機械的な事実だけを表す。 */
type EndReason = "game_over" | "opponent_no_move" | "self_no_move" | "plies_cap" | "human_move_error";

interface CliOptions {
  games: number;
  seed: number;
  pliesCap: number;
  outDir: string;
  /** STEP D3: --profile。undefined なら既定の10局構成。 */
  profile: PlayerProfileId | undefined;
  /** STEP D3b: --opponent-nodes。undefined なら相手は本番どおり(movetime 1000ms)。 */
  opponentNodes: number | undefined;
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

  return { games, seed, pliesCap, outDir, profile: parseProfileOption(argv), opponentNodes: parseOpponentNodesOption(argv) };
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
  /** STEP D3b: 相手の go に nodes を付けて渡した回数(--opponent-nodes が無ければ 0)。 */
  opponentNodesGoCalls: number;
}

async function runOneGame(params: {
  gameNumber: number;
  profile: PlayerProfileId;
  seed: number;
  pliesCap: number;
  runStartedAt: string;
  outDir: string;
  engine: PrioritizedEngine;
  /** STEP D3b: 相手の go に渡す nodes。undefined なら本番どおり。 */
  opponentNodes: number | undefined;
}): Promise<GameRunResult> {
  const { gameNumber, profile, seed, pliesCap, runStartedAt, outDir, engine, opponentNodes } = params;
  const nn = String(gameNumber).padStart(2, "0");
  const kifuId = `explore-${runStartedAt}-${nn}-${profile}`;
  const gameStartedAt = new Date().toISOString();

  const lines: string[] = [];
  const moves: string[] = [];
  // STEP D3: 先手の手ごとの段(B・B2 だけ。S1〜R は null が並ぶが棋譜 JSON には書かない)。
  const tiers: (BeginnerTier | null)[] = [];
  const readyMsPerPly: number[] = [];
  const prng = new Prng(seed);
  const s3: S3ScriptState = { cursor: 0 };
  const randomRate = profile === "R" ? DEFAULT_RANDOM_RATE : 0;
  // STEP D3b: 相手と先手(E 読み)のハンドルを別々に作り、相手のハンドルだけに --opponent-nodes を渡す。
  const handles = buildHighPriorityHandles(engine, opponentNodes);


  const enginePath = resolveEnginePath();
  lines.push(
    buildMetaLine({
      kifuId,
      startedAt: gameStartedAt,
      // STEP U6-R: git の状態は渡さない。buildMetaLine が repoRoot から自分で読む(値を偽れないように)。
      repoRoot: REPO_ROOT,
      enginePath,
      extra: {
        mode: "explore",
        profile,
        seed,
        randomRate,
        pliesCap,
        referenceNodes: DEFAULT_REFERENCE_NODES,
        // STEP D3b: 相手の探索量(指定なしは null = 本番どおり movetime 1000ms)。記録から対局の条件を読めるようにする。
        opponentNodes: opponentNodes ?? null,
      },
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
    engine.asLowPriority(),
    DEFAULT_REFERENCE_NODES,
    // STEP 5-F(A-4): ③用の別ハンドル(H-9。asLowPriority()は呼ぶたびに独立した
    // クロージャを返すので、MultiPVの設定が候補手側へ持ち越されない)。
    // explore.tsは探索であって回帰ではなく、compare.tsの3回一致の対象ではない。
    // そのためreplay.tsと違いwithFixedSearchで包まず、本番と同じmovetimeで測る。
    engine.asLowPriority(),
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
      const { move: senteMove, tier } = await pickMoveWithTier(profile, state.sfen, latestReady.response, {
        prng,
        randomRate,
        engine: handles.sente,
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
      tiers.push(tier);

      state = await playOpponentMove(state, handles.opponent, getApprovedScenarioVariants());

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
        // STEP 5-1(B-3、人間承認済み。LP-2): server.tsと同じ呼び出し順を保つため、
        // stateBeforeMoveの局面のready行(latestReady)で実際にキャッシュされていた
        // 計画を渡す。
        latestReady.cachedPlan ?? null,
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
        engine.asLowPriority(),
        DEFAULT_REFERENCE_NODES,
        // STEP 5-F(A-4): ③用の別ハンドル(H-9。asLowPriority()は呼ぶたびに独立した
        // クロージャを返すので、MultiPVの設定が候補手側へ持ち越されない)。
        // explore.tsは探索であって回帰ではなく、compare.tsの3回一致の対象ではない。
        // そのためreplay.tsと違いwithFixedSearchで包まず、本番と同じmovetimeで測る。
        engine.asLowPriority(),
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
      buildKifuJsonText({ id: kifuId, profile, seed, moves, tiers }),
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
    opponentNodesGoCalls: handles.opponentNodesGoCalls(),
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
      const profile = profileForGame(gameNumber, options.profile);
      const gameSeed = options.seed + gameNumber;
      console.log(`[explore] 局 ${gameNumber}/${options.games}(profile: ${profile}, seed: ${gameSeed}, opponentNodes: ${options.opponentNodes ?? "本番どおり"}) 開始`);
      const result = await runOneGame({
        gameNumber,
        profile,
        seed: gameSeed,
        pliesCap: options.pliesCap,
        runStartedAt,
        outDir: options.outDir,
        engine,
        opponentNodes: options.opponentNodes,
      });
      results.push(result);
      console.log(
        `[explore] 局 ${gameNumber}/${options.games} 終了: 手数=${result.plies}, 理由=${result.endReason}, ${result.totalMs}ms, 相手の go(nodes 付き)=${result.opponentNodesGoCalls}`,
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
