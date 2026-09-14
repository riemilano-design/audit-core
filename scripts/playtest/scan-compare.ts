// STEP D-COST(docs/STEP_D-COST_PLAN_2026-09-15.md 7.1)。同じ棋譜を深い走査と軽い走査で再生した記録の
// フォルダを 2 つ受け取り、ファイル名が同じ記録どうしを突き合わせて Markdown の表を標準出力へ書く。**エンジンは回さない。**
//
// 使い方: npx tsx scripts/playtest/scan-compare.ts --deep <dir> --deep-nodes <N> --light <dir> --light-nodes <N>
//
// 【このファイルは薄くしてある】突き合わせ・率・表の組み立てはすべて lib/scanCompare.ts にあり、そちらに試験がある。
// ここでやるのは、記録を読む・lib を呼ぶ・書き出す、だけである。
//
// 【exit code】lib の例外は外へ出さず「数えられなかった」行にして exit 0。**入力が読めないとき・引数が足りないときは
// 0 でない**(`diagnose.ts` と同じ)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { buildScanReport, renderScanReport, type ScanPairInput } from "./lib/scanCompare.js";

// 閾値の近くとみなす幅(計画 2.2 の「−400 ± 100」)。**表示の幅であり、急落の判定には使わない**
const NEAR_BAND_CP = 100;

const USAGE = "使い方: npx tsx scripts/playtest/scan-compare.ts --deep <dir> --deep-nodes <N> --light <dir> --light-nodes <N>";

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

function positiveInteger(value: string | undefined): number | undefined {
  const n = Number(value);
  return value !== undefined && Number.isInteger(n) && n > 0 ? n : undefined;
}

function readRecord(filePath: string): { meta: MetaLine | undefined; records: RecordLine[] } {
  const lines = readFileSync(filePath, "utf-8")
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
  const deepDir = argValue(args, "--deep");
  const lightDir = argValue(args, "--light");
  const deepNodes = positiveInteger(argValue(args, "--deep-nodes"));
  const lightNodes = positiveInteger(argValue(args, "--light-nodes"));
  if (deepDir === undefined || lightDir === undefined || deepNodes === undefined || lightNodes === undefined) {
    console.error(USAGE);
    process.exit(1);
    return;
  }

  const deepNames = jsonlNames(deepDir);
  const lightNames = jsonlNames(lightDir);
  const onlyDeep = deepNames.filter((name) => !lightNames.includes(name));
  const onlyLight = lightNames.filter((name) => !deepNames.includes(name));
  const inputs: ScanPairInput[] = deepNames
    .filter((name) => lightNames.includes(name))
    .map((name) => {
      const deep = readRecord(path.join(deepDir, name));
      return {
        kifuId: deep.meta?.kifuId ?? name,
        deep: { ...deep, expectedNodes: deepNodes },
        light: { ...readRecord(path.join(lightDir, name)), expectedNodes: lightNodes },
      };
    });

  const report = buildScanReport(inputs, DRAFT_RULE_1, NEAR_BAND_CP);
  console.log(renderScanReport(report, { onlyDeep, onlyLight }).join("\n"));
  process.exit(0);
}

main();
