// 3 席 LLM API の束 R2 ― CLI: 席の出力の封筒(seat-output.v0.1)を、seat_input.meta.json と request に照らす
// (計画 docs/STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md §1。lib は lib/seatOutput.ts)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。【packet を読まない】packetRef の実在は自動化レーンの検証器(H-9)。
// 使い方: npx tsx scripts/playtest/seatOutputCheck.ts --seat-output <json> --meta <seat_input.meta.json> --request <request.json> --today YYYY-MM-DD [--obs-items <path>]
// 出口: 問題を 1 件 1 行で出し、1 本でも落ちれば終了コード 1(hypothesisCheck.ts の流儀)。--today は必須(日付を機械が決めない)。
import { readFileSync } from "node:fs";
import { seatOutputProblems } from "./lib/seatOutput.js";
import type { SeatInputMeta } from "./lib/seatInput.js";

function argOf(name: string): string | undefined {
  const index = process.argv.indexOf(`--${name}`);
  if (index < 0) return undefined;
  const value = process.argv[index + 1];
  return value === undefined || value.startsWith("--") ? undefined : value;
}
function requiredArg(name: string): string {
  const value = argOf(name);
  if (value === undefined) throw new Error(`--${name} が要る`);
  return value;
}

function main(): void {
  const envelope = JSON.parse(readFileSync(requiredArg("seat-output"), "utf-8")) as unknown;
  const meta = JSON.parse(readFileSync(requiredArg("meta"), "utf-8")) as SeatInputMeta;
  const request = JSON.parse(readFileSync(requiredArg("request"), "utf-8")) as unknown;
  const today = requiredArg("today");
  const obsItemsPath = argOf("obs-items");
  const problems = seatOutputProblems(envelope, { meta, request, today, ...(obsItemsPath === undefined ? {} : { obsItemsPath }) });
  const env = envelope as { run?: { seat?: string; model?: string }; items?: unknown[]; answers?: unknown[] };
  console.log(`席 ${String(env.run?.seat)}(${String(env.run?.model)}) 項目 ${env.items?.length ?? 0} 本・答え ${env.answers?.length ?? 0} 行`);
  if (problems.length > 0) {
    console.log(`問題 ${problems.length} 件:`);
    for (const p of problems) console.log(`  - ${p}`);
    process.exitCode = 1;
    return;
  }
  console.log("問題なし(封筒の schema・E-1〜E-7・各行の H-1〜H-8。packet の実在は見ていない = H-9)");
}

main();
