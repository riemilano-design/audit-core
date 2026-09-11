// STEP T-1(対局ハーネス・固定棋譜モード)。
// docs/PLAYTEST_LOOP_PROPOSAL.md 4.1・4.6・6. の T-1 に従う。
//
// 一度記録した棋譜(自分側・相手側とも既知のUSI列)を、server.tsが行うのと同じ
// 本番関数の呼び出し順で再生し、一手ごとに web が受け取るのと同じ API レスポンス
// (buildStateResponseWithPlan の戻り値)を JSONL に保存する。
//
// 本番関数(apps/server/src 配下)は import して呼ぶだけで、複製・改変はしない。
// 将棋の判断・評価・閾値・文言はここでは一切書かない。
//
// 使い方: npx tsx scripts/playtest/replay.ts <kifu.json> [--out <file.jsonl>]
//         [--nodes <N>] [--threads <N>] [--reference-nodes <N>]
//
// 位置づけの詳細は scripts/playtest/README.md を参照。開発補助であり本番導線には
// 含めない(apps/・data/・docs/・.claude/ は変更しない)。

import { execSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  safeComputePlanChangeAfterMove,
  safeComputePlanChangeReasonAfterMove,
  safeComputeMoveOutcomeAfterMove,
  safeComputeBoardEventsAfterMove,
  type CachedReachablePlan,
} from "../../apps/server/src/api/stateResponse.js";
import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { getApprovedScenarioVariants } from "../../apps/server/src/engine/scenarioRepository.js";
import { UsiEngine, type GoResult } from "../../apps/server/src/engine/usiEngine.js";
import {
  createInitialGameState,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
  type OpponentEngine,
} from "../../apps/server/src/game/gameSession.js";
import {
  buildErrorLine,
  buildImmediateRecord,
  buildReadyRecord,
  buildSummaryLine,
} from "./lib/recorder.js";
import { withFixedSearch } from "./lib/fixedSearchEngine.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT_DIR = __dirname;
const REPO_ROOT = path.join(__dirname, "..", "..");

// STEP T-6(A-3)。docs/STEP_T-6_PLAN_2026-09-11.md 2. A-3、人間の決定
// (2026-09-11。提案書7.1、設問1 = (b))に従う。回帰モード(replay.ts)だけ
// 探索量を固定ノード数(既定4,000,000)・Threads=1にする(本番の既定値
// movetime 2000・Threadsの既定は変えない。探索モード(explore.ts)は本番条件の
// まま)。この既定値はハーネスの引数であって、将棋の判断・本番の閾値ではない
// (README参照)。
const DEFAULT_NODES = 4_000_000;
const DEFAULT_THREADS = 1;

interface FixedKifu {
  id: string;
  source: string;
  moves: string[];
}

/** ある特定の手(記録済みのUSI)をそのまま返す偽エンジン。
 * gameSession.ts の OpponentEngine(Pick<UsiEngine, "position" | "go">)を満たす。
 * 経路1(承認済みvariant)・経路2(scenario)を構造的に通さず、経路3(エンジン)で
 * 記録手を確定させるための意図的な差分(T-1計画書参照。playOpponentMoveへは
 * 承認済みvariantを渡さず、空配列[]を渡す)。 */
function makeFixedOpponentEngine(moveUsi: string): OpponentEngine {
  return {
    position: () => {
      // 記録済みの手をそのまま返すため、局面は参照しない。
    },
    go: async (): Promise<GoResult> => ({
      bestmove: moveUsi,
      ponder: undefined,
      scoreCp: undefined,
      infoLines: [],
    }),
  };
}

/** playHumanMove/playOpponentMoveの想定内エラーで再生を打ち切るための内部マーカー。
 * 呼び出し元がJSONLへ"kind":"error"行を書いた直後にthrowし、外側のtry/finallyで
 * エンジンのquit/closeを確実に行ってからexit 1する。 */
class ReplayHaltError extends Error {}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const kifuArg = args[0];
  if (!kifuArg || kifuArg.startsWith("--")) {
    console.error(
      "使い方: npx tsx scripts/playtest/replay.ts <kifu.json> [--out <file.jsonl>] [--nodes <N>] [--threads <N>] [--reference-nodes <N>]",
    );
    process.exit(1);
  }

  const outIndex = args.indexOf("--out");
  const outArg = outIndex !== -1 ? args[outIndex + 1] : undefined;

  const nodesIndex = args.indexOf("--nodes");
  const nodes = nodesIndex !== -1 ? Number(args[nodesIndex + 1]) : DEFAULT_NODES;

  const threadsIndex = args.indexOf("--threads");
  const threads = threadsIndex !== -1 ? Number(args[threadsIndex + 1]) : DEFAULT_THREADS;

  const searchMode: "nodes" | "movetime" = nodes > 0 ? "nodes" : "movetime";

  // STEP T-7(A-2)。docs/STEP_T-7_PLAN_2026-09-11.md 2. A-2に従う。既定は
  // --nodes と同じ値(--nodes 0のときはDEFAULT_NODES)。エンジンの参考評価
  // (engineReference。ハーネスの観測)を測るためのノード数で、候補手計算(⑧)の
  // 探索量固定(--nodes)とは独立の値として扱う(lib/recorder.tsのreferenceEngine参照)。
  const referenceNodesIndex = args.indexOf("--reference-nodes");
  const referenceNodes =
    referenceNodesIndex !== -1 ? Number(args[referenceNodesIndex + 1]) : nodes > 0 ? nodes : DEFAULT_NODES;

  const kifu = JSON.parse(readFileSync(path.resolve(kifuArg), "utf-8")) as FixedKifu;
  const kifuId = kifu.id;
  const moves = kifu.moves;

  const lines: string[] = [];
  const startedAt = new Date().toISOString();

  let gitHead: string | null;
  try {
    gitHead = execSync("git rev-parse HEAD", { cwd: REPO_ROOT }).toString().trim();
  } catch {
    gitHead = null;
  }

  const enginePath = resolveEnginePath();
  lines.push(
    JSON.stringify({
      kind: "meta",
      kifuId,
      startedAt,
      gitHead,
      enginePath,
      searchMode,
      nodes,
      threads,
      referenceNodes,
    }),
  );

  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  await rawEngine.usiHandshake();
  await rawEngine.isReady();
  // STEP T-6(A-3): setMultiPvと同じ運用(呼び出しタイミングの管理は呼び出し側の
  // 責務。usiEngine.ts参照)で、ハンドシェイク後にThreadsを固定する。
  rawEngine.setThreads(threads);
  const engine = new PrioritizedEngine(rawEngine);

  let exitCode = 0;
  let readyMsPerPly: number[] = [];
  let pliesCompleted = 0;
  const totalStart = Date.now();

  try {
    let state: GameState = createInitialGameState(undefined, { variants: getApprovedScenarioVariants() });
    // STEP 5-1(B-3、人間承認済み。LP-2): server.tsのbackgroundPlanと同じ役割の変数。
    // stateBeforeMoveの局面で実際にキャッシュされていた計画(直前のready行のもの)を
    // safeComputeMoveOutcomeAfterMoveの新引数(displayedPlan)へ渡すために保持する。
    let latestReadyCachedPlan: CachedReachablePlan | undefined;

    // 初期局面(POST /api/game/new相当)。
    {
      const { line } = buildImmediateRecord(state, 0, null, null, false, null, null, []);
      lines.push(line);
    }
    {
      const { line, elapsedMs, cachedPlan } = await buildReadyRecord(
        state,
        0,
        null,
        null,
        withFixedSearch(engine.asLowPriority(), nodes),
        false,
        null,
        null,
        [],
        engine.asLowPriority(),
        referenceNodes,
      );
      readyMsPerPly.push(elapsedMs);
      lines.push(line);
      latestReadyCachedPlan = cachedPlan;
    }

    for (let i = 0; i < moves.length; i += 2) {
      const m = moves[i];
      const g = moves[i + 1];
      if (m === undefined || g === undefined) {
        lines.push(
          buildErrorLine({
            reason: "odd_move_count",
            message: "棋譜の手数が偶数(先後交互)ではありません",
          }),
        );
        throw new ReplayHaltError();
      }

      const stateBeforeMove = state;

      try {
        state = playHumanMove(state, m);
      } catch (err) {
        if (err instanceof HumanMoveError) {
          lines.push(
            buildErrorLine({
              ply: stateBeforeMove.moveHistory.length,
              move: m,
              reason: "human_move_error",
              message: err.message,
            }),
          );
          throw new ReplayHaltError();
        }
        throw err;
      }

      const fakeEngine = makeFixedOpponentEngine(g);
      state = await playOpponentMove(state, fakeEngine, []);

      if (state.moveHistory[state.moveHistory.length - 1] !== g) {
        lines.push(
          buildErrorLine({
            ply: state.moveHistory.length,
            move: g,
            reason: "opponent_move_mismatch",
            message: "相手の手が記録した棋譜の手と一致しませんでした",
          }),
        );
        throw new ReplayHaltError();
      }

      const planChanged = safeComputePlanChangeAfterMove(stateBeforeMove, state, m, {}, undefined);
      const planChangeReason = planChanged
        ? safeComputePlanChangeReasonAfterMove(stateBeforeMove, state, m, {}, undefined)
        : null;
      const opponentMoveUsi =
        state.moveHistory.length === stateBeforeMove.moveHistory.length + 2
          ? (state.moveHistory[state.moveHistory.length - 1] ?? null)
          : null;
      const boardEvents = safeComputeBoardEventsAfterMove(stateBeforeMove, m, opponentMoveUsi);
      const moveOutcome = safeComputeMoveOutcomeAfterMove(
        stateBeforeMove,
        state,
        m,
        opponentMoveUsi,
        {},
        undefined,
        planChangeReason,
        // STEP 5-1(B-3、人間承認済み。LP-2): server.tsと同じ呼び出し順を保つため、
        // stateBeforeMoveの局面のready行(直前ply)で実際にキャッシュされていた計画を渡す。
        latestReadyCachedPlan ?? null,
      );

      const ply = state.moveHistory.length;

      {
        const { line } = buildImmediateRecord(state, ply, m, g, planChanged, planChangeReason, moveOutcome, boardEvents);
        lines.push(line);
      }
      {
        const { line, elapsedMs, cachedPlan } = await buildReadyRecord(
          state,
          ply,
          m,
          g,
          withFixedSearch(engine.asLowPriority(), nodes),
          planChanged,
          planChangeReason,
          moveOutcome,
          boardEvents,
          engine.asLowPriority(),
          referenceNodes,
        );
        readyMsPerPly.push(elapsedMs);
        lines.push(line);
        latestReadyCachedPlan = cachedPlan;
      }

      pliesCompleted = ply;
    }

    const totalMs = Date.now() - totalStart;
    lines.push(buildSummaryLine({ plies: pliesCompleted, totalMs, readyMsPerPly }));
  } catch (err) {
    if (err instanceof ReplayHaltError) {
      exitCode = 1;
    } else {
      throw err;
    }
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }

  const outPath = outArg
    ? path.resolve(outArg)
    : path.join(SCRIPT_DIR, "out", `${kifuId}-${startedAt.replace(/[:.]/g, "-")}.jsonl`);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${lines.join("\n")}\n`, "utf-8");
  console.log(`書き込み: ${outPath}`);

  process.exit(exitCode);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
