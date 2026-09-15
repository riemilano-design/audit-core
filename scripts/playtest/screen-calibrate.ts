// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §5・§11 の床)。比べる相手(4M 一律。床では段 1)の記録のフォルダと、段 2 の記録のフォルダを受け取り、
// ファイル名が同じ記録どうしを突き合わせて Markdown の表を標準出力へ書く。**エンジンは回さない。**
//
// 使い方: npx tsx scripts/playtest/screen-calibrate.ts --base <dir> --stage2 <dir> [--stage2-repeat <dir>]
//   --stage2-repeat: 同じ入力でもう 1 回回した rescreen の出力のフォルダ(床の (iii)・(iv))
//
// 【このファイルは薄くしてある】数える・表を組み立てるのは lib/screenCalibration.ts にあり、そちらに試験がある。
// ここでやるのは、記録を読む・lib を呼ぶ・書き出す、だけである。
//
// 【exit code】lib の例外は外へ出さず「数えられなかった」行にして exit 0。**引数が足りない・フォルダが読めないときは 1**(diagnose.ts と同じ)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { compareDeepRows, compareRescreenRuns, compareWithStage2, renderScreenCalibration, type StageRow } from "./lib/screenCalibration.js";

const USAGE = "使い方: npx tsx scripts/playtest/screen-calibrate.ts --base <dir> --stage2 <dir> [--stage2-repeat <dir>]";

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

function parseRecord(text: string): { meta: MetaLine | undefined; records: RecordLine[] } {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as { kind: string });
  const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
  const records = lines.filter((line): line is RecordLine => line.kind === "record");
  return { meta, records };
}

function jsonlNames(dir: string): string[] {
  return readdirSync(dir).filter((name) => name.endsWith(".jsonl")).sort();
}

function main(): void {
  const args = process.argv.slice(2);
  const baseDir = argValue(args, "--base");
  const stage2Dir = argValue(args, "--stage2");
  const repeatDir = argValue(args, "--stage2-repeat");
  if (baseDir === undefined || stage2Dir === undefined || baseDir.startsWith("--") || stage2Dir.startsWith("--") || (args.includes("--stage2-repeat") && (repeatDir === undefined || repeatDir.startsWith("--")))) {
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }

  const baseNames = jsonlNames(baseDir);
  const stage2Names = jsonlNames(stage2Dir);
  const rows: StageRow[] = stage2Names
    .filter((name) => baseNames.includes(name))
    .map((name): StageRow => {
      const base = parseRecord(readFileSync(path.join(baseDir, name), "utf-8"));
      const stage2 = parseRecord(readFileSync(path.join(stage2Dir, name), "utf-8"));
      const kifuId = stage2.meta?.kifuId ?? name;
      try {
        return { kind: "counted", comparison: compareWithStage2(kifuId, base, stage2, DRAFT_RULE_1), deepRows: compareDeepRows(stage2.records, base.records) };
      } catch (error) {
        return { kind: "notCounted", kifuId, detail: error instanceof Error ? `${error.name}: ${error.message}` : String(error) };
      }
    });
  const repeatNames = repeatDir === undefined ? [] : jsonlNames(repeatDir);
  const runs = stage2Names
    .filter((name) => repeatNames.includes(name))
    .map((name) => {
      const first = readFileSync(path.join(stage2Dir, name), "utf-8");
      return { kifuId: parseRecord(first).meta?.kifuId ?? name, comparison: compareRescreenRuns(first, readFileSync(path.join(repeatDir!, name), "utf-8")) };
    });

  console.log(
    renderScreenCalibration(rows, runs, {
      onlyBase: baseNames.filter((name) => !stage2Names.includes(name)),
      onlyStage2: stage2Names.filter((name) => !baseNames.includes(name)),
    }).join("\n"),
  );
  process.exitCode = 0;
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
  process.exitCode = 1;
}
