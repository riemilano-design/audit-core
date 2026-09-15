// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §11 の床 (v))。記録の ready 行の局面を、**同じエンジンのプロセスで続けて 2 回** measureEngineReference に掛け、
// 2 回の結果を JSONL に書く(P-33 の同型。P-48 の残りの対照 ― 同じプロセスで、直前の探索が同じ局面のとき、参考評価と focus_baseline の読み筋・標識が同じになるか)。
//
// 使い方: npx tsx scripts/playtest/measure-twice.ts <記録.jsonl> --nodes <N> --out <出力.jsonl> [--plies <ply,ply,...>]
//   --plies を渡さなければ、記録の Failure Event の根(fromReadyPly。規則は DRAFT_RULE_1)を測る
//
// 【このファイルは薄くしてある】測る行の決め方と 2 回の比べは lib/screenCalibration.ts(planMeasureTwice・compareMeasurementPair)にあり、そちらに試験がある。
// ここでやるのは、記録を読む・エンジンを起こす前に測る行を決める・エンジンを 1 本(Threads 1)起こして 1 行につき 2 回続けて測る・書く、だけである。
// 【エンジンを使う】回すセッションが本数を宣言する(規則 12 番)。**試験はエンジンを起こさない経路だけ**(ソース照合と、引数・入力の誤り)。
// 【exit code】引数の誤り・入力の誤り・例外は 1(書かない)。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveEnginePath } from "../../apps/server/src/engine/enginePath.js";
import { PrioritizedEngine } from "../../apps/server/src/engine/prioritizedEngine.js";
import { UsiEngine } from "../../apps/server/src/engine/usiEngine.js";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import { measureEngineReference } from "./lib/engineReference.js";
import { DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { recordSha256 } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";
import { compareMeasurementPair, planMeasureTwice } from "./lib/screenCalibration.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
// 1 プロセス・Threads 1(所要を根拠にしない測定でも、揺れの条件を D-COST・rescreen と揃える)
const THREADS = 1;
const USAGE = "使い方: npx tsx scripts/playtest/measure-twice.ts <記録.jsonl> --nodes <N> --out <出力.jsonl> [--plies <ply,ply,...>]";

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const inputArg = args[0];
  const outArg = argValue(args, "--out");
  const nodes = Number(argValue(args, "--nodes"));
  const pliesArg = argValue(args, "--plies");
  if (
    inputArg === undefined ||
    inputArg.startsWith("--") ||
    outArg === undefined ||
    !Number.isInteger(nodes) ||
    nodes <= 0 ||
    (args.includes("--plies") && (pliesArg === undefined || pliesArg.startsWith("--")))
  ) {
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }
  const inputPath = path.resolve(inputArg);
  const outPath = path.resolve(outArg);
  if (inputPath === outPath) throw new Error("--out が入力と同じパス(記録のファイルは変えない)");
  const plies = pliesArg?.split(",").map((value) => {
    const ply = Number(value);
    if (!Number.isInteger(ply) || ply < 0) throw new Error(`--plies の値が 0 以上の整数でない: ${value}`);
    return ply;
  });

  const source = readFileSync(inputPath);
  const lines = source
    .toString("utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
  const records = lines.filter((line): line is RecordLine => line.kind === "record");
  const kifuId = meta?.kifuId ?? path.basename(inputPath);
  // エンジンを起こす前に、測る行を決める(無い ply はここで止まる)
  const plan = planMeasureTwice(kifuId, { meta, records }, DRAFT_RULE_1, plies);
  console.error(`測る行: ${plan.plies.length}`);

  const enginePath = resolveEnginePath();
  const rawEngine = new UsiEngine(enginePath);
  rawEngine.start();
  try {
    await rawEngine.usiHandshake();
    await rawEngine.isReady();
    rawEngine.setThreads(THREADS);
    const engine = new PrioritizedEngine(rawEngine).asLowPriority();
    const git = readGitState(REPO_ROOT);
    const out: string[] = [
      JSON.stringify({ kind: "meta", kifuId, sourceSha256: recordSha256(source), startedAt: new Date().toISOString(), gitHead: git.gitHead, dirty: git.dirty, enginePath, threads: THREADS, nodes, plies: plan.plies }),
    ];
    let referenceEqual = 0;
    let focusCompared = 0;
    let focusPvEqual = 0;
    for (const ply of plan.plies) {
      const sfen = plan.sfenByPly.get(ply)!;
      // 同じプロセスで、同じ局面を続けて 2 回(間に別の局面の探索を挟まない)
      const first = await measureEngineReference(sfen, engine, nodes);
      const second = await measureEngineReference(sfen, engine, nodes);
      const comparison = compareMeasurementPair(first, second);
      if (comparison.referenceEqual) referenceEqual += 1;
      if (comparison.focusCompared) focusCompared += 1;
      if (comparison.focusPvEqual) focusPvEqual += 1;
      out.push(JSON.stringify({ kind: "measureTwice", ply, sfen, first, second, comparison }));
    }
    writeFileSync(outPath, `${out.join("\n")}\n`, "utf-8");
    console.log(`測った行 ${plan.plies.length} / 参考評価が同じ ${referenceEqual} / focus_baseline を比べた ${focusCompared} / そのうち pv が同じ ${focusPvEqual}`);
  } finally {
    rawEngine.quit();
    rawEngine.close();
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
