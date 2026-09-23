// STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 3)。納品までを 1 コマンドで通す道具。
//
// 使い方:
//   npx tsx scripts/playtest/deliver.ts \
//     --person <id> --kifu-dir <dir> --work <dir> --time-limit-sec <秒> \
//     --name <表示名> --title <タイトル> --today <YYYY-MM-DD> --out <顧客フォルダ> \
//     [--previous-work <前回の work>] [--parallel <N>] \
//     [--compare-dir <段 2 の記録のフォルダ …> --compare-person <p記号>] \
//     [--group-work <work> --group-time-limit-sec <秒>]… \
//     [--forbid <語>]… [--dry-run] [--from <段の名前>]
//
// `--compare-dir`/`--compare-person` は段 `pipeline-gate` で `pipeline.ts --until gate` へ中継するだけ
// (新しい work に `gate.jsonl` が無いときに要る。既にあればその段は飛ぶ)。
//
// 【この道具がやること】既存の道具を規定順に**子プロセスで呼ぶだけ**(pipeline.ts と同じ流儀)。
// 引数の組み立て・段の順・済みの判定は lib/deliver.ts(純粋。vitest の試験つき)にあり、ここでやるのは
// 子プロセスの起動と fs だけである。
//
// 【この道具が絶対にやらないこと】将棋の判断・評価・閾値・文言。新しい分析指標・新しい集計。
// 既存の道具(lib/ の純粋関数・report-pdf/ の python)の中身の複製・改変。
// 人間の確認点(S6 の言い換え・B の「読み」)を自動で埋めること。

import { spawn } from "node:child_process";
import { appendFileSync, copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  DeliverArgError,
  TODO_MARK,
  deliverLogLineOf,
  deliverOutPaths,
  finalPositionsPartPath,
  finalPositionsCommand,
  groupListOf,
  mergeFinalPositions,
  parseDeliverArgs,
  planDeliver,
  unexpectedOutFiles,
  type DeliverArgs,
  type DeliverProbe,
  type DeliverTool,
  type PlannedDeliverStep,
} from "./lib/deliver.js";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(SCRIPT_DIR, "..", "..");
const REPORT_PDF_DIR = path.join(SCRIPT_DIR, "report-pdf");

/** `npx tsx <道具>.ts` で起こすもの。 */
const TSX_TOOLS: Partial<Record<DeliverTool, string>> = {
  pipeline: path.join(SCRIPT_DIR, "pipeline.ts"),
  "direct-answers": path.join(SCRIPT_DIR, "directAnswers.ts"),
  "final-positions": path.join(SCRIPT_DIR, "finalPositions.ts"),
  "time-cause": path.join(SCRIPT_DIR, "timeCause.ts"),
  "time-search": path.join(SCRIPT_DIR, "timeSearch.ts"),
  "answer-menu": path.join(SCRIPT_DIR, "answerMenu.ts"),
};

/** `python3 -X utf8 <道具>.py`(cwd = report-pdf/。report-pdf/README.md の手順どおり)。 */
const PY_TOOLS: Partial<Record<DeliverTool, string>> = {
  "render-direct": "render_direct.py",
  "render-time-cause": "render_time_cause.py",
  "answer-facts": "answer_facts.py",
  "check-answer": "check_answer.py",
  "render-answer": "render_answer.py",
  "check-delivery": "check_delivery.py",
};

function cmdOf(tool: DeliverTool): string {
  const tsx = TSX_TOOLS[tool];
  if (tsx !== undefined) return `npx tsx ${path.relative(REPO_ROOT, tsx)}`;
  const py = PY_TOOLS[tool];
  if (py !== undefined) return `python3 -X utf8 ${path.relative(REPO_ROOT, path.join(REPORT_PDF_DIR, py))}`;
  return tool;
}

interface RunResult {
  code: number;
  stdout: string;
  stderr: string;
}

function spawnProcess(cmd: string, args: readonly string[], cwd: string, env: NodeJS.ProcessEnv): Promise<RunResult> {
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

function runTool(tool: DeliverTool, args: readonly string[], env: Record<string, string> | undefined): Promise<RunResult> {
  const tsx = TSX_TOOLS[tool];
  if (tsx !== undefined) return spawnProcess("npx", ["tsx", tsx, ...args], REPO_ROOT, { ...process.env, ...env });
  const py = PY_TOOLS[tool];
  if (py !== undefined) return spawnProcess("python3", ["-X", "utf8", py, ...args], REPORT_PDF_DIR, { ...process.env, ...env });
  throw new Error(`子プロセスを起こさない道具: ${tool}`);
}

const probe: DeliverProbe = {
  exists: (filePath) => existsSync(filePath),
  hasJsonl: (dirPath) => existsSync(dirPath) && readdirSync(dirPath).some((name) => name.endsWith(".jsonl")),
  fixedKifuFiles: (dirPath) =>
    existsSync(dirPath)
      ? readdirSync(dirPath)
          .filter((name) => name.endsWith(".fixed.json"))
          .sort()
          .map((name) => path.join(dirPath, name))
      : [],
  timeUpLossCount: (patientPath) => {
    if (!existsSync(patientPath)) return 0;
    try {
      const data = JSON.parse(readFileSync(patientPath, "utf-8")) as { time?: { timeUpLosses?: unknown[] | null } };
      const losses = data.time?.timeUpLosses;
      return Array.isArray(losses) ? losses.length : 0;
    } catch {
      return 0;
    }
  },
};

/** 段 4(複製)。`args` は [src, dst, src, dst, …]。 */
function copyPairs(args: readonly string[]): number {
  for (let i = 0; i < args.length; i += 2) {
    const src = args[i]!;
    const dst = args[i + 1]!;
    if (!existsSync(src)) {
      console.error(`複製元が無い: ${src}`);
      return 1;
    }
    mkdirSync(path.dirname(dst), { recursive: true });
    copyFileSync(src, dst);
  }
  return 0;
}

/**
 * 段 6。組の順に `finalPositions.ts` を 1 組ずつ回し(エンジンは常に 1 本)、**先頭のメタ + entries 連結**で
 * `final_positions.json` を書く。時間切れ負けが 0 局の組は飛ばす(道具が対象 0 件で rc=1 になるため)。
 */
async function runFinalPositions(args: DeliverArgs): Promise<number> {
  const out = deliverOutPaths(args.out);
  const groups = groupListOf(args);
  const partPaths: string[] = [];

  mkdirSync(out.directDir, { recursive: true });
  // **組の順のまま**、1 組ずつ順に回す(エンジンは常に 1 本)。引数の組み立ては lib/deliver.ts の
  // `finalPositionsCommand`(試験つき)。材料(patient・固定棋譜)は**この時点で**見る ― 今回の組の
  // patient・固定棋譜は段 1 が作るため、計画を組んだ時点では無いことがある。
  for (const [index, group] of groups.entries()) {
    const partPath = finalPositionsPartPath(args.out, index);
    if (!existsSync(partPath)) {
      const losses = probe.timeUpLossCount(group.patient);
      if (losses === 0) {
        // `finalPositions.ts` は対象 0 件で rc=1 になるので回さない(実装担当の判断)。
        console.log(`[appendix3-final] 組 ${index + 1}: 時間切れ負け 0 局なので回さない`);
        continue;
      }
      const kifuFiles = probe.fixedKifuFiles(group.fixedKifuDir);
      if (kifuFiles.length === 0) {
        console.error(`[appendix3-final] 組 ${index + 1}: 固定棋譜(*.fixed.json)が無い: ${group.fixedKifuDir}`);
        return 1;
      }
      const result = await runTool("final-positions", finalPositionsCommand(group, kifuFiles, partPath), undefined);
      process.stdout.write(result.stdout);
      if (result.code !== 0 || !existsSync(partPath)) {
        console.error(result.stderr.trim().slice(0, 2000));
        return result.code === 0 ? 1 : result.code;
      }
    }
    partPaths.push(partPath);
  }
  if (partPaths.length === 0) {
    console.error("[appendix3-final] どの組にも時間切れ負けが無いので final_positions.json を作れない");
    return 1;
  }
  const parts = partPaths.map((partPath) => JSON.parse(readFileSync(partPath, "utf-8")) as Record<string, unknown>);
  writeFileSync(out.finalPositions, `${JSON.stringify(mergeFinalPositions(parts), null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${out.finalPositions}(${partPaths.length} 組を連結)`);
  return 0;
}

/** 人間の確認点。止まるべきかを見て、止まるなら理由を出す。 */
function gateBlocked(step: PlannedDeliverStep): string | null {
  const target = step.args[0]!;
  if (step.stage === "prose-gate") {
    if (existsSync(target) && readFileSync(target, "utf-8").trim().length > 0) return null;
    return step.reason;
  }
  // answer-gate: 下書きに「読み」の印が残っていれば止まる。
  if (!existsSync(target)) return `B の下書きが無い: ${target}`;
  return readFileSync(target, "utf-8").includes(TODO_MARK) ? `B の「読み」が未記入: ${target}(${TODO_MARK} が残っている)` : null;
}

async function main(): Promise<number> {
  let args: DeliverArgs;
  try {
    args = parseDeliverArgs(process.argv.slice(2));
  } catch (error) {
    if (error instanceof DeliverArgError) {
      console.error(error.message);
      return 2;
    }
    throw error;
  }

  const out = deliverOutPaths(args.out);

  // --out の安全装置(司令塔の判断)。deliver.ts 自身が書く名前以外のファイルがあれば、何もせず止まる。
  if (existsSync(args.out)) {
    const topNames = readdirSync(args.out);
    const directNames = existsSync(out.directDir) ? readdirSync(out.directDir) : [];
    const unexpected = unexpectedOutFiles(topNames, directNames);
    if (unexpected.length > 0) {
      console.error(`--out に deliver.ts が書かない名前のファイルがある(取り違えを避けるため何もしない):\n- ${unexpected.join("\n- ")}`);
      return 2;
    }
  }

  const steps = planDeliver(args, probe, cmdOf);

  if (args.dryRun) {
    console.log(JSON.stringify({ person: args.person, out: args.out, groups: args.groups, steps }, null, 2));
    return 0;
  }

  mkdirSync(out.directDir, { recursive: true });

  for (const step of steps) {
    const startedAt = new Date().toISOString();
    let rc: number | "skip" = "skip";
    let humanGate = false;

    if (step.action === "skip") {
      console.log(`[${step.stage}] skip: ${step.reason}`);
    } else if (step.action === "fail") {
      // 引数が足りない段(段 pipeline-gate だけ)。人間の確認点ではないので humanGate は付けない。
      rc = 1;
      console.error(`[${step.stage}] ${step.reason}`);
    } else if (step.action === "gate") {
      const blocked = gateBlocked(step);
      if (blocked === null) {
        console.log(`[${step.stage}] 確認点は済んでいる`);
      } else {
        humanGate = true;
        rc = 1;
        console.error(`[${step.stage}] 人間の確認点で止まります: ${blocked}`);
      }
    } else if (step.stage === "deliverables-pdf") {
      rc = copyPairs(step.args);
    } else if (step.stage === "appendix3-final") {
      rc = await runFinalPositions(args);
    } else {
      console.log(`[${step.stage}] ${step.cmd}`);
      const result = await runTool(step.tool, step.args, step.env);
      rc = result.code;
      process.stdout.write(result.stdout);
      if (result.code !== 0) console.error(result.stderr.trim().slice(0, 4000));
    }

    const finishedAt = new Date().toISOString();
    appendFileSync(out.log, deliverLogLineOf({ stage: step.stage, startedAt, finishedAt, rc, humanGate }), "utf-8");

    if (rc !== "skip" && rc !== 0) {
      console.error(`段 ${step.stage} で止まりました(rc=${rc})。直したら --from ${step.stage} で再開できます。`);
      return typeof rc === "number" ? rc : 1;
    }
  }

  console.log(`納品フォルダ: ${args.out}`);
  return 0;
}

main().then(
  (code) => {
    process.exitCode = code;
  },
  (error: unknown) => {
    console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
    process.exitCode = 1;
  },
);
