// STEP PIPE 作業 A(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1)。S1(読み込み)〜S4(判定)を順に呼ぶ道具。
//
// 使い方:
//   npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir>
//     [--me <名前>] [--parallel <N=5>]
//     [--compare-dir <段 2 の記録のフォルダ …> --compare-person <p記号>]
//     [--until import|evaluate|diagnose|gate] [--evaluator "<評価関数の識別>"] [--dry-run]
//
// S4(gate.ts)の向き: --person・--kifu-dir の局(このお客さん)が材料の側(gate.ts の --person・--material)、
// --compare-dir の記録が試す側(gate.ts の --test-person・--test-sente/--test-gote)。2 人目 20 局(材料)を
// 1 人目 10 局(試す側)で確かめた C-1・C-5 の正式な実行と同じ向き(docs/STEP_D3-COND_PLAN_2026-09-15.md §14・§15.2)。
//
// 【このファイルがやること】
// - 引数を読み、--kifu-dir の中の棋譜ファイルから局の一覧を作り(lib/pipeline.ts の listGames)、
//   lib/pipeline.ts の runPipeline(実行)/ planPipeline(--dry-run のプレビュー)を呼ぶ。
// - 既存の道具(kifu-import-check.ts・replay.ts・rescreen.ts・diagnose.ts・gate.ts)を **子プロセスで呼ぶだけ**
//   (import して中身を複製しない)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。records/ への書き込み。--records-append を足すこと(lib/pipeline.ts の
//   gateCommand が決して付けない。棄却の記録へ書くのは、予測を先にコミットした正式な実行だけ ― 司令塔が手で回す)。

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync, appendFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  listGames,
  parsePipelineArgs,
  planPipeline,
  runPipeline,
  PipelineArgError,
  PipelineConfigError,
  type PipelineFs,
  type ToolName,
  type ToolResult,
} from "./lib/pipeline.js";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(SCRIPT_DIR, "..", "..");

const TOOL_PATHS: Record<ToolName, string> = {
  "kifu-import-check": path.join(SCRIPT_DIR, "kifu-import-check.ts"),
  replay: path.join(SCRIPT_DIR, "replay.ts"),
  rescreen: path.join(SCRIPT_DIR, "rescreen.ts"),
  diagnose: path.join(SCRIPT_DIR, "diagnose.ts"),
  gate: path.join(SCRIPT_DIR, "gate.ts"),
};

/** 既存の道具を `npx tsx <道具>.ts <引数>` で起こすだけ(呼ぶ順・引数の組み立ては lib/pipeline.ts が決める)。 */
function spawnTool(tool: ToolName, args: readonly string[]): Promise<ToolResult> {
  return new Promise((resolve, reject) => {
    const child = spawn("npx", ["tsx", TOOL_PATHS[tool], ...args], { cwd: REPO_ROOT });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf-8");
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf-8");
    });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code: code ?? 1, stdout, stderr }));
  });
}

const realFs: PipelineFs = {
  readText: (filePath) => (existsSync(filePath) ? readFileSync(filePath, "utf-8") : undefined),
  writeText: (filePath, content) => {
    mkdirSync(path.dirname(filePath), { recursive: true });
    writeFileSync(filePath, content, "utf-8");
  },
  appendText: (filePath, content) => {
    mkdirSync(path.dirname(filePath), { recursive: true });
    appendFileSync(filePath, content, "utf-8");
  },
  ensureDir: (dirPath) => {
    mkdirSync(dirPath, { recursive: true });
  },
  listFiles: (dirPath) => (existsSync(dirPath) ? readdirSync(dirPath) : []),
};

async function main(): Promise<void> {
  const argv = process.argv.slice(2);
  let args;
  try {
    args = parsePipelineArgs(argv);
  } catch (error) {
    if (error instanceof PipelineArgError) {
      console.error(error.message);
      process.exitCode = 2;
      return;
    }
    throw error;
  }

  const fileNames = existsSync(args.kifuDir) ? readdirSync(args.kifuDir) : [];
  let games;
  try {
    games = listGames(args.kifuDir, fileNames, args.me);
  } catch (error) {
    if (error instanceof PipelineConfigError) {
      console.error(error.message);
      process.exitCode = 2;
      return;
    }
    throw error;
  }

  if (args.dryRun) {
    const steps = planPipeline(args, games, realFs);
    console.log(JSON.stringify({ person: args.person, games: games.length, parallel: args.parallel, until: args.until, steps }, null, 2));
    process.exitCode = 0;
    return;
  }

  console.log(`並行: ${args.parallel} 本(局 ${games.length})`);
  const result = await runPipeline(args, games, realFs, spawnTool);
  if (result.failures.length > 0) {
    console.error(`失敗 ${result.failures.length} 件:`);
    for (const failure of result.failures) console.error(`- ${failure.gameId} ${failure.stage}: ${failure.message}`);
  } else {
    console.log("失敗 0 件");
  }
  process.exitCode = result.exitCode;
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
