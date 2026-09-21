// STEP D-SCREEN-1(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §1)。段 1 の記録(全行を軽いノード数で測った replay.ts の JSONL)を読み、
// 急落の候補の前後の ready 行だけを深いノード数で測り直した段 2 の記録を書く。
//
// 使い方: npx tsx scripts/playtest/rescreen.ts <段1.jsonl> --out <段2.jsonl> --deep-nodes <N> [--all-plies]
//   --all-plies(STEP D-SCREEN-2)は校正の床(計画 §5 の 0.)だけで使う: 候補を選ばず、全 ready 行を読み直す
//
// 【このファイルは薄くしてある】候補の選び方・読み直す行・記録の組み立ては lib/rescreen.ts にあり、そちらに試験がある。
// ここでやるのは、記録を読む・書く前の確かめ(エンジンを起こす前)・エンジンを 1 本(Threads 1)起こして
// measureEngineReference を measure として渡す・書く、だけである。
//
// 【段 1 のファイルは変えない】--out が入力と同じパスなら止める。
// 【exit code】引数の誤り・段 1 として受け付けない入力・例外は 1(書かない)。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import { measureCheckBaseline } from "./lib/checkBaseline.js";
import { measureEngineReference } from "./lib/engineReference.js";
import { DRAFT_SCREEN_RULE_1, planRescreen, rescreenRecords } from "./lib/rescreen.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
// 深い回は 1 プロセス・Threads 1(計画 §1)
const DEEP_THREADS = 1;
const USAGE = "使い方: npx tsx scripts/playtest/rescreen.ts <段1.jsonl> --out <段2.jsonl> --deep-nodes <N> [--all-plies]";

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const inputArg = args[0];
  const outArg = argValue(args, "--out");
  const deepNodes = Number(argValue(args, "--deep-nodes"));
  const options = { allPlies: args.includes("--all-plies") };
  if (inputArg === undefined || inputArg.startsWith("--") || outArg === undefined || !Number.isInteger(deepNodes) || deepNodes <= 0) {
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }
  const inputPath = path.resolve(inputArg);
  const outPath = path.resolve(outArg);
  if (inputPath === outPath) throw new Error("--out が入力と同じパス(段 1 のファイルは変えない)");

  const source = readFileSync(inputPath);
  // エンジンを起こす前に、段 1 として受け付けるかを確かめる
  const { deepPlies } = planRescreen(source, DRAFT_SCREEN_RULE_1, options);
  console.error(`読み直す行: ${deepPlies.length}`);

  const enginePath = resolveEnginePath();
  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  try {
    await rawEngine.usiHandshake();
    await rawEngine.isReady();
    rawEngine.setThreads(DEEP_THREADS);
    const engine = new PrioritizedEngine(rawEngine).asLowPriority();
    const startedAt = new Date().toISOString();
    const text = await rescreenRecords(source, DRAFT_SCREEN_RULE_1, (sfen) => measureEngineReference(sfen, engine, deepNodes), {
      deepNodes,
      enginePath,
      threads: DEEP_THREADS,
      startedAt,
      repoRoot: REPO_ROOT,
      checkMeasure: (sfen) => measureCheckBaseline(sfen, engine, deepNodes),
    }, options);
    writeFileSync(outPath, text, "utf-8");
    console.error(`書き込み: ${outPath}`);
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
