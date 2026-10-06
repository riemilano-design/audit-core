// 3 席 LLM API の束 R3 ― CLI: 整理役の出力(integration.v0.1)を、その入力の器(integration_input.v0.1)に照らす
// (計画 docs/STEP_LLM_SEATS_R3_INTEGRATION_2026-09-30.md §1。lib は lib/integration.ts)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。【packet を読まない】実在は自動化レーンの検証器(H-9)。
// 使い方: npx tsx scripts/playtest/integrationCheck.ts --integration <json> --input <integration_input.json> --today YYYY-MM-DD [--obs-items <path>] [--packet <path>]
// 出口: 問題を 1 件 1 行で出し、1 本でも落ちれば終了コード 1。--today は必須。
// --packet は任意(STEP S-2)。指定すれば各束の representative の H-9・H-10・H-11 の照合に渡す(無ければ今までどおり未照合)。
import { readFileSync } from "node:fs";
import { integrationProblems } from "./lib/integration.js";

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
  const output = JSON.parse(readFileSync(requiredArg("integration"), "utf-8")) as unknown;
  const input = JSON.parse(readFileSync(requiredArg("input"), "utf-8")) as unknown;
  const today = requiredArg("today");
  const obsItemsPath = argOf("obs-items");
  const packetPath = argOf("packet");
  const packet: unknown = packetPath === undefined ? undefined : JSON.parse(readFileSync(packetPath, "utf-8"));
  const problems = integrationProblems(output, input, { today, packet, ...(obsItemsPath === undefined ? {} : { obsItemsPath }) });
  const out = output as { clusters?: unknown[]; dropped?: unknown[]; heldBack?: unknown[]; forVerification?: unknown[] };
  console.log(`束 ${out.clusters?.length ?? 0}・落とした項目 ${out.dropped?.length ?? 0}・外した束 ${out.heldBack?.length ?? 0}・検証へ ${out.forVerification?.length ?? 0}`);
  if (problems.length > 0) {
    console.log(`問題 ${problems.length} 件:`);
    for (const p of problems) console.log(`  - ${p}`);
    process.exitCode = 1;
    return;
  }
  console.log("問題なし(器の schema・I-1〜I-8・代表の行の H-1〜H-8。packet の実在は見ていない = H-9)");
}

main();
