// STEP D6(docs/STEP_D6_PLAN_2026-09-16.md §6)。D4 の Gate の記録(契約 diagnosis-gate v0.1 の JSONL)と条件式の定義の置き場を読み、
// audience(dev / person)の報告(契約 diagnosis-report v0.1 の JSONL と Markdown)を書く。**エンジンは回さない。LLM を呼ばない。**
//
// 使い方: npx tsx scripts/playtest/report.ts --gate <gate.jsonl> --conditions <dir> --audience <dev|person> [--include-insufficient] --out <report.jsonl> --md <report.md>
//
// 【このファイルは薄くしてある】確かめ・採る行・文・出力の確かめは lib/diagnosisReport.ts にあり、そちらに試験がある。
// ここでやるのは、ファイルを読む・定義を読み込む・lib を呼ぶ・書く、だけである。
// 【exit code】引数の誤り・読めない入力・定義の読み込みの誤り・lib の確かめに当たったときは 1(何も書かない)。

import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadCondition } from "./lib/condition.js";
import { buildDiagnosisReport, ReportInputError, ReportOutputError, type Audience, type ReportDefinition } from "./lib/diagnosisReport.js";
import { STANDING_BOUNDS } from "./lib/failureEvent.js";
import { pathForProvenance, recordSha256 } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = "使い方: npx tsx scripts/playtest/report.ts --gate <gate.jsonl> --conditions <dir> --audience <dev|person> [--include-insufficient] --out <report.jsonl> --md <report.md>";

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  const value = index === -1 ? undefined : args[index + 1];
  return value === undefined || value.startsWith("--") ? undefined : value;
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const gateArg = argValue(args, "--gate");
  const conditionsArg = argValue(args, "--conditions");
  const audienceArg = argValue(args, "--audience");
  const outArg = argValue(args, "--out");
  const mdArg = argValue(args, "--md");
  if (gateArg === undefined || conditionsArg === undefined || outArg === undefined || mdArg === undefined || (audienceArg !== "dev" && audienceArg !== "person")) {
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }
  const gatePath = path.resolve(gateArg);
  const outPath = path.resolve(outArg);
  const mdPath = path.resolve(mdArg);
  if (outPath === gatePath || mdPath === gatePath || outPath === mdPath) throw new Error("--out・--md が --gate か互いと同じパス(記録のファイルは変えない)");

  const bytes = readFileSync(gatePath);
  const entries = bytes
    .toString("utf-8")
    .split("\n")
    .map((text, index) => ({ text: text.trim(), line: index + 1 }))
    .filter(({ text }) => text.length > 0)
    .map(({ text, line }) => ({ line, value: JSON.parse(text) as unknown }));

  const definitions: ReportDefinition[] = [];
  for (const name of readdirSync(conditionsArg).filter((file) => file.endsWith(".ts") && !file.endsWith(".test.ts")).sort()) {
    const loaded = await loadCondition(path.join(conditionsArg, name));
    const { id, label, status, readableText } = loaded.definition;
    definitions.push({ id, label, status, ...(readableText === undefined ? {} : { readableText }), definitionSha256: loaded.definitionSha256 });
  }

  const git = readGitState(REPO_ROOT);
  const report = buildDiagnosisReport(
    entries,
    { definitions, standingBounds: STANDING_BOUNDS, input: { path: pathForProvenance(gatePath, REPO_ROOT), sha256: recordSha256(bytes) }, provenance: { gitHead: git.gitHead, dirty: git.dirty } },
    { audience: audienceArg as Audience, includeInsufficient: args.includes("--include-insufficient") },
  );
  writeFileSync(outPath, `${report.lines.map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
  writeFileSync(mdPath, `${report.markdown.join("\n")}\n`, "utf-8");
  console.log(`書いた行 ${report.lines.length}(audience ${audienceArg})`);
}

main().catch((error: unknown) => {
  if (error instanceof ReportInputError || error instanceof ReportOutputError) {
    console.error(error.name);
    for (const problem of error.problems) console.error(`- ${problem}`);
  } else console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
});
