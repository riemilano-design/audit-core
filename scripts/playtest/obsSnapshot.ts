// STEP OBS-3a(docs/LANE_DIAG_LOG_2026-09.md §12.4)。観測の写し(obs_snapshot.json)を、道具の出力から
// 機械で作る CLI。純粋な組み立ては `lib/obsSnapshot.ts`(`buildObsSnapshot`)が行う。ここはファイルを読み、
// git の状態を測り、書き出すだけ。
//
// 使い方:
//   npx tsx scripts/playtest/obsSnapshot.ts --customer <p番号> --group <ラベル> \
//     --patient <patient_report_data.json> --time-cause <time_cause.json> \
//     [--whatif-data <whatif_report_data.json>] [--direct <direct_answers.json>] \
//     [--final-positions <final_positions.json>] [--menu <answer_menu.json>] \
//     [--obs-items <OBSERVATION_ITEMS.md>(既定は docs/OBSERVATION_ITEMS.md)] \
//     --out <obs_snapshot.json>
//
// 【このファイルが絶対にやらないこと】
// - 合計・割合・新しい数を作ること(`lib/obsSnapshot.ts` の `SNAPSHOT_ITEMS`・`numbersOnly` が、
//   道具の出力をそのまま写すだけにする)。
// - 文字列(名前・盤・文)を出力へ残すこと。
// - 将棋の判断・評価・閾値・文言。
// - `scripts/playtest/out/` の下に書くこと(`--out` は呼び出し側が決める。この CLI 自身は既定を持たない)。

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { recordSha256 } from "./lib/failureEventSchema.js";
import { readGitState } from "./lib/gitState.js";
import { loadObsRegistry } from "./lib/hypothesis.js";
import { buildObsSnapshot, type ObsSnapshotInputFile, type ObsSnapshotInputs } from "./lib/obsSnapshot.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const DEFAULT_OBS_ITEMS_PATH = path.join(REPO_ROOT, "docs", "OBSERVATION_ITEMS.md");

const USAGE = [
  "使い方:",
  "  npx tsx scripts/playtest/obsSnapshot.ts --customer <p番号> --group <ラベル> \\",
  "    --patient <patient_report_data.json> --time-cause <time_cause.json> \\",
  "    [--whatif-data <whatif_report_data.json>] [--direct <direct_answers.json>] \\",
  "    [--final-positions <final_positions.json>] [--menu <answer_menu.json>] \\",
  "    [--obs-items <OBSERVATION_ITEMS.md>] --out <obs_snapshot.json>",
].join("\n");

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

function readInputFile(filePath: string): ObsSnapshotInputFile {
  const resolved = path.resolve(filePath);
  const bytes = readFileSync(resolved);
  return { name: path.basename(resolved), sha256: recordSha256(bytes), data: JSON.parse(bytes.toString("utf-8")) as unknown };
}

function main(): number {
  const args = process.argv.slice(2);
  const customer = argValue(args, "--customer");
  const group = argValue(args, "--group");
  const patientPath = argValue(args, "--patient");
  const timeCausePath = argValue(args, "--time-cause");
  const outArg = argValue(args, "--out");
  if (customer === undefined || group === undefined || patientPath === undefined || timeCausePath === undefined || outArg === undefined) {
    console.error(USAGE);
    return 2;
  }

  const whatifDataPath = argValue(args, "--whatif-data");
  const directPath = argValue(args, "--direct");
  const finalPositionsPath = argValue(args, "--final-positions");
  const menuPath = argValue(args, "--menu");
  const obsItemsPath = argValue(args, "--obs-items") ?? DEFAULT_OBS_ITEMS_PATH;

  const registry = loadObsRegistry(obsItemsPath);
  const gitState = readGitState(REPO_ROOT);

  const inputs: ObsSnapshotInputs = {
    patient: readInputFile(patientPath),
    timeCause: readInputFile(timeCausePath),
    whatifData: whatifDataPath === undefined ? undefined : readInputFile(whatifDataPath),
    direct: directPath === undefined ? undefined : readInputFile(directPath),
    finalPositions: finalPositionsPath === undefined ? undefined : readInputFile(finalPositionsPath),
    menu: menuPath === undefined ? undefined : readInputFile(menuPath),
  };

  const snapshot = buildObsSnapshot(inputs, { customer, group, registry, gitHead: gitState.gitHead, dirty: gitState.dirty });

  const outPath = path.resolve(outArg);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(snapshot, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(${snapshot.items.length} 件)`);
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
