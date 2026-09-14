// STEP D1(docs/STEP_D1_PLAN_2026-09-14.md 3.2)。replay.ts の JSONL を読み、Failure Event を
// Markdown の表で標準出力へ書く。**エンジンは回さない**(check.ts と同じ形)。
//
// 使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>]
//
// 【このファイルは薄くしてある】判定・集計・表の組み立てはすべて lib/failureEvent.ts にあり、そちらに試験がある。
// ここでやるのは、記録を読む・lib を呼ぶ・書き出す、だけである。
//
// 【exit code】lib の例外は外へ出さず「数えられなかった」行にして exit 0。**入力が読めないとき(ENOENT・壊れた JSONL)は
// 例外がこのファイルから外へ出て 0 でない**(check.ts と同じ。計画 D-1 の読み替え ― 2026-09-15、監査 B の非必須 d)。
//
// 【このファイルが絶対にやらないこと】
// - 死因のタグを approved にすること・閾値を確定すること
// - **この件数を診断に使うこと**(今の記録は駒得だけの評価。計画 0.)

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { buildDiagnosisReport, DRAFT_RULE_1, renderDiagnosisReport, type DiagnosisInput } from "./lib/failureEvent.js";

function parseArgs(argv: string[]): { files: string[]; eventsOut: string | undefined } {
  const eventsIndex = argv.indexOf("--events");
  const eventsOut = eventsIndex !== -1 ? argv[eventsIndex + 1] : undefined;
  const files = argv.filter((arg, index) => eventsIndex === -1 || (index !== eventsIndex && index !== eventsIndex + 1));
  return { files: files.filter((file) => file.length > 0), eventsOut };
}

function readInput(filePath: string): DiagnosisInput {
  const lines = readFileSync(path.resolve(filePath), "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
  const records = lines.filter((line): line is RecordLine => line.kind === "record");
  return { kifuId: meta?.kifuId ?? path.basename(filePath), meta, records };
}

function main(): void {
  const { files, eventsOut } = parseArgs(process.argv.slice(2));
  if (files.length === 0) {
    console.error("使い方: npx tsx scripts/playtest/diagnose.ts <a.jsonl> [<b.jsonl> ...] [--events <out.jsonl>]");
    process.exit(0);
    return;
  }

  const inputs = files.map(readInput);
  const report = buildDiagnosisReport(inputs, DRAFT_RULE_1);
  console.log(renderDiagnosisReport(report).join("\n"));

  if (eventsOut) {
    const eventLines = report.flatMap((row) => (row.result.kind === "counted" ? row.result.events.map((event) => JSON.stringify(event)) : []));
    writeFileSync(path.resolve(eventsOut), eventLines.length > 0 ? `${eventLines.join("\n")}\n` : "", "utf-8");
  }

  process.exit(0);
}

main();
