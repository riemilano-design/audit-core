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
//
// 位置づけの詳細は scripts/playtest/README.md を参照。開発補助であり本番導線には
// 含めない(apps/・data/・docs/・.claude/ は変更しない)。

import { execSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildStateResponseWithPlan,
  safeComputeReachablePlan,
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT_DIR = __dirname;
const REPO_ROOT = path.join(__dirname, "..", "..");

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

/** server.ts の runBackgroundPlanAnalysis と同じ組み立てで CachedReachablePlan を作る。
 * safeComputeReachablePlan が失敗(undefined)を返した場合は undefined のまま
 * (buildStateResponseWithPlan 側でcandidateMoveStateが pending 扱いになる)。 */
function toCachedPlan(
  sfen: string,
  result: Awaited<ReturnType<typeof safeComputeReachablePlan>>,
): CachedReachablePlan | undefined {
  if (!result) return undefined;
  return {
    sfen,
    targetShapeId: result.targetShapeId,
    plan: { reachableShapes: result.reachableShapes, candidateMove: result.candidateMove },
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
    console.error("使い方: npx tsx scripts/playtest/replay.ts <kifu.json> [--out <file.jsonl>]");
    process.exit(1);
  }

  const outIndex = args.indexOf("--out");
  const outArg = outIndex !== -1 ? args[outIndex + 1] : undefined;

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
  lines.push(JSON.stringify({ kind: "meta", kifuId, startedAt, gitHead, enginePath }));

  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  await rawEngine.usiHandshake();
  await rawEngine.isReady();
  const engine = new PrioritizedEngine(rawEngine);

  let exitCode = 0;
  let readyMsPerPly: number[] = [];
  let pliesCompleted = 0;
  const totalStart = Date.now();

  try {
    let state: GameState = createInitialGameState(undefined, { variants: getApprovedScenarioVariants() });

    // 初期局面(POST /api/game/new相当)。
    {
      const t0 = Date.now();
      const response = buildStateResponseWithPlan(state, undefined, {}, undefined, false, null, null, []);
      lines.push(
        JSON.stringify({
          kind: "record",
          ply: 0,
          sfen: state.sfen,
          senteMove: null,
          goteMove: null,
          phase: "immediate",
          elapsedMs: Date.now() - t0,
          response,
        }),
      );
    }
    {
      const t0 = Date.now();
      const result = await safeComputeReachablePlan(state, engine.asLowPriority(), {}, undefined);
      const cachedPlan = toCachedPlan(state.sfen, result);
      const response = buildStateResponseWithPlan(state, cachedPlan, {}, undefined, false, null, null, []);
      const elapsedMs = Date.now() - t0;
      readyMsPerPly.push(elapsedMs);
      lines.push(
        JSON.stringify({
          kind: "record",
          ply: 0,
          sfen: state.sfen,
          senteMove: null,
          goteMove: null,
          phase: "ready",
          elapsedMs,
          response,
        }),
      );
    }

    for (let i = 0; i < moves.length; i += 2) {
      const m = moves[i];
      const g = moves[i + 1];
      if (m === undefined || g === undefined) {
        lines.push(
          JSON.stringify({
            kind: "error",
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
            JSON.stringify({
              kind: "error",
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
          JSON.stringify({
            kind: "error",
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
      );

      const ply = state.moveHistory.length;

      {
        const t0 = Date.now();
        const response = buildStateResponseWithPlan(
          state,
          undefined,
          {},
          undefined,
          planChanged,
          planChangeReason,
          moveOutcome,
          boardEvents,
        );
        lines.push(
          JSON.stringify({
            kind: "record",
            ply,
            sfen: state.sfen,
            senteMove: m,
            goteMove: g,
            phase: "immediate",
            elapsedMs: Date.now() - t0,
            response,
          }),
        );
      }
      {
        const t0 = Date.now();
        const result = await safeComputeReachablePlan(state, engine.asLowPriority(), {}, undefined);
        const cachedPlan = toCachedPlan(state.sfen, result);
        const response = buildStateResponseWithPlan(
          state,
          cachedPlan,
          {},
          undefined,
          planChanged,
          planChangeReason,
          moveOutcome,
          boardEvents,
        );
        const elapsedMs = Date.now() - t0;
        readyMsPerPly.push(elapsedMs);
        lines.push(
          JSON.stringify({
            kind: "record",
            ply,
            sfen: state.sfen,
            senteMove: m,
            goteMove: g,
            phase: "ready",
            elapsedMs,
            response,
          }),
        );
      }

      pliesCompleted = ply;
    }

    const totalMs = Date.now() - totalStart;
    lines.push(JSON.stringify({ kind: "summary", plies: pliesCompleted, totalMs, readyMsPerPly }));
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
