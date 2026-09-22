// STEP WHATIF 作業 2(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)。「見せる段」の材料(付録 2)を書く道具。
// **測る段(whatif.ts)の出力(whatif.jsonl)を読むだけ**(エンジンは起こさない)。
//
// 使い方:
//   npx tsx scripts/playtest/whatifReport.ts --whatif <whatif.jsonl …> --patient <patient_report_data.json>
//     --out <whatif_report_data.json>
//
// 組み立ては純粋関数(lib/whatifReport.ts)に任せ、ここは読み書きと配線だけ。
//
// 【この CLI が絶対にやらないこと】エンジンを回すこと・records/ へ書くこと・将棋の判断・文言。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { buildWhatifReportData, WhatifReportError, type PatientGameLike, type WhatifReportInput } from "./lib/whatifReport.js";

const USAGE = "使い方: npx tsx scripts/playtest/whatifReport.ts --whatif <whatif.jsonl …> --patient <patient_report_data.json> --out <whatif_report_data.json>";

export class WhatifReportCliError extends Error {}

interface CliArgs {
  whatifFiles: string[];
  patient: string;
  out: string;
}

export function parseArgs(argv: readonly string[]): CliArgs {
  const whatifFiles: string[] = [];
  let patient: string | undefined;
  let out: string | undefined;
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if (flag === "--whatif") {
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        whatifFiles.push(argv[index + 1]!);
        index += 1;
      }
    } else if (flag === "--patient") {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new WhatifReportCliError(`--patient に値が無い。${USAGE}`);
      patient = value;
      index += 1;
    } else if (flag === "--out") {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new WhatifReportCliError(`--out に値が無い。${USAGE}`);
      out = value;
      index += 1;
    } else {
      throw new WhatifReportCliError(`知らない引数: ${flag}。${USAGE}`);
    }
  }
  if (whatifFiles.length === 0) throw new WhatifReportCliError(`--whatif が無い。${USAGE}`);
  if (patient === undefined) throw new WhatifReportCliError(`--patient が無い。${USAGE}`);
  if (out === undefined) throw new WhatifReportCliError(`--out が無い。${USAGE}`);
  return { whatifFiles, patient, out };
}

interface PatientReportDataMinimal {
  games: PatientGameLike[];
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  const patientData = JSON.parse(readFileSync(path.resolve(args.patient), "utf-8")) as PatientReportDataMinimal;
  const patientById = new Map(patientData.games.map((game) => [game.id, game]));

  const inputs: WhatifReportInput[] = args.whatifFiles.map((filePath) => {
    const jsonl = readFileSync(path.resolve(filePath), "utf-8");
    // patient 側と突き合わせるための id を、先頭行(meta 行のはず)から読む。中身の検証(kind === "meta" か等)は
    // lib 側の parseWhatifJsonl(buildWhatifReportData の中)が改めてやるので、ここでは id を知るためだけに読む。
    const firstLine = jsonl.split("\n").find((line) => line.trim().length > 0);
    const kifuId = firstLine === undefined ? undefined : (JSON.parse(firstLine) as { kifuId?: string }).kifuId;
    if (kifuId === undefined) throw new WhatifReportCliError(`${filePath} の先頭行(meta 行のはず)から kifuId を読めない`);
    const patient = patientById.get(kifuId);
    if (patient === undefined) throw new WhatifReportCliError(`${filePath}(kifuId=${kifuId})が patient_report_data.json の games に無い`);
    return { id: kifuId, jsonl, patient };
  });

  const report = buildWhatifReportData(inputs);
  writeFileSync(path.resolve(args.out), `${JSON.stringify(report, null, 2)}\n`, "utf-8");
  console.log(`whatif_report_data.json: ${report.gamesCount} 局`);
  process.exitCode = 0;
}

try {
  main();
} catch (error) {
  if (error instanceof WhatifReportCliError || error instanceof WhatifReportError) {
    console.error(error.message);
    process.exitCode = 1;
  } else {
    throw error;
  }
}
