// STEP PIPE 作業 A(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1)+ 作業 C(§2.2 の最後・§3 (a))。
// S1(読み込み)〜S7(PDF)を順に呼ぶ道具。
//
// 使い方:
//   npx tsx scripts/playtest/pipeline.ts --person <id> --kifu-dir <dir> --work <dir>
//     [--me <名前>] [--parallel <N=5>]
//     [--compare-dir <段 2 の記録のフォルダ …> --compare-person <p記号>]
//     [--name <表示名> --title <タイトル> --today <YYYY-MM-DD>]  … --until が report-data・prose・pdf のときだけ必須
//     [--until import|evaluate|diagnose|gate|report-data|prose|pdf] [--evaluator "<評価関数の識別>"] [--dry-run]
//     [--whatif]  … STEP WHATIF 作業 1。付けたときだけ、diagnose の後に局ごとに whatif.ts を回す(--until には無関係)
//
// S4(gate.ts)の向き: --person・--kifu-dir の局(このお客さん)が材料の側(gate.ts の --person・--material)、
// --compare-dir の記録が試す側(gate.ts の --test-person・--test-sente/--test-gote)。2 人目 20 局(材料)を
// 1 人目 10 局(試す側)で確かめた C-1・C-5 の正式な実行と同じ向き(docs/STEP_D3-COND_PLAN_2026-09-15.md §14・§15.2)。
//
// S5(reportData.ts)・S7(report-pdf/)は STEP PIPE 作業 B(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2)で足された道具を
// 同じ流儀(子プロセスで呼ぶだけ)でつなぐ。S6(言い換え)は自動化しない ― prose.json が無ければ止まる。
//
// 【このファイルがやること】
// - 引数を読み、--kifu-dir の中の棋譜ファイルから局の一覧を作り(lib/pipeline.ts の listGames)、
//   lib/pipeline.ts の runPipeline(実行)/ planPipeline(--dry-run のプレビュー)を呼ぶ。
// - 既存の道具(kifu-import-check.ts・replay.ts・rescreen.ts・diagnose.ts・gate.ts・reportData.ts)を
//   **子プロセスで呼ぶだけ**(import して中身を複製しない)。S7(report-pdf/)は python(reportlab・pymupdf)なので
//   `npx tsx` ではなく `sh build.sh`・`python3 -X utf8 render_main.py …`・`python3 -X utf8 check_fonts_embedded.py …`
//   を呼ぶ(report-pdf/README.md の手順どおり。中身は変えない)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。records/ への書き込み。--records-append を足すこと(lib/pipeline.ts の
//   gateCommand が決して付けない。棄却の記録へ書くのは、予測を先にコミットした正式な実行だけ ― 司令塔が手で回す)。
// - 言い換え(S6)の自動化。エンジンを起こすこと。

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync, appendFileSync } from "node:fs";
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
const REPORT_PDF_DIR = path.join(SCRIPT_DIR, "report-pdf");

// npx tsx <道具>.ts <引数> で起こす既存の道具(S1〜S5)。S7(report-pdf-*)はここに無く、下の spawnTool で別に分ける。
const TSX_TOOL_PATHS: Record<Exclude<ToolName, "report-pdf-build" | "report-pdf-render-main" | "report-pdf-check-fonts" | "report-pdf-render-whatif">, string> = {
  "kifu-import-check": path.join(SCRIPT_DIR, "kifu-import-check.ts"),
  replay: path.join(SCRIPT_DIR, "replay.ts"),
  rescreen: path.join(SCRIPT_DIR, "rescreen.ts"),
  diagnose: path.join(SCRIPT_DIR, "diagnose.ts"),
  gate: path.join(SCRIPT_DIR, "gate.ts"),
  "report-data": path.join(SCRIPT_DIR, "reportData.ts"),
  // STEP WHATIF 作業 1。`--whatif` のときだけ呼ぶ(lib/pipeline.ts の runPipeline 参照)。
  whatif: path.join(SCRIPT_DIR, "whatif.ts"),
  // STEP WHATIF 作業 2。`--whatif` かつ `--until pdf` のときだけ呼ぶ(付録 2「分かれ道」の材料)。
  "whatif-report-data": path.join(SCRIPT_DIR, "whatifReport.ts"),
};

/** `cmd <args>` を起こし、標準出力・標準エラー・終了コードを集める(spawnTool の共通部分)。 */
function spawnProcess(cmd: string, args: readonly string[], cwd: string, env: NodeJS.ProcessEnv = process.env): Promise<ToolResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, [...args], { cwd, env });
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

/**
 * 既存の道具を起こすだけ(呼ぶ順・引数の組み立ては lib/pipeline.ts が決める)。
 * S1〜S5 は `npx tsx <道具>.ts <引数>`(cwd はリポジトリの根)。
 * S7(report-pdf-*)は report-pdf/README.md の手順どおり(python の実行ファイルは README のとおり `python3`、cwd は report-pdf/):
 * - `report-pdf-build`(args 無し): `sh build.sh` で render_main.py・render_appendix.py を作る
 * - `report-pdf-render-main`(args = [REPORT_DATA_DIR, patient_report_data.json, 出力 PDF]):
 *   `REPORT_DATA_DIR=<args[0]> python3 -X utf8 render_main.py <args[1]> <args[2]>`
 * - `report-pdf-check-fonts`(args = [PDF …]): `python3 -X utf8 check_fonts_embedded.py <args…>`
 * - `report-pdf-render-whatif`(STEP WHATIF 作業 2。args = [REPORT_DATA_DIR, whatif_report_data.json, 出力 PDF]):
 *   `REPORT_DATA_DIR=<args[0]> python3 -X utf8 render_whatif.py <args[1]> <args[2]>`(新規ファイル。build.sh では作らない ―
 *   既存の 6 本(_head/_util/_mid/_app_head/_app/_tail)の連結とは別の、単体の python ファイルのまま)
 */
function spawnTool(tool: ToolName, args: readonly string[]): Promise<ToolResult> {
  if (tool === "report-pdf-build") return spawnProcess("sh", ["build.sh"], REPORT_PDF_DIR);
  if (tool === "report-pdf-render-main") {
    const [reportDataDir, patientPath, outPdfPath] = args;
    return spawnProcess("python3", ["-X", "utf8", "render_main.py", patientPath!, outPdfPath!], REPORT_PDF_DIR, { ...process.env, REPORT_DATA_DIR: reportDataDir });
  }
  if (tool === "report-pdf-render-whatif") {
    const [reportDataDir, whatifDataPath, outPdfPath] = args;
    return spawnProcess("python3", ["-X", "utf8", "render_whatif.py", whatifDataPath!, outPdfPath!], REPORT_PDF_DIR, { ...process.env, REPORT_DATA_DIR: reportDataDir });
  }
  if (tool === "report-pdf-check-fonts") {
    return spawnProcess("python3", ["-X", "utf8", "check_fonts_embedded.py", ...args], REPORT_PDF_DIR);
  }
  return spawnProcess("npx", ["tsx", TSX_TOOL_PATHS[tool], ...args], REPO_ROOT);
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
  mtimeMs: (filePath) => (existsSync(filePath) ? statSync(filePath).mtimeMs : undefined),
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
