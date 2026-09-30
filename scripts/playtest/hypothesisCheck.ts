// STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2)。仮説の記録(契約 hypothesis)を、スキーマ + 機械検査
// H-1〜H-8(lib/hypothesis.ts)に照らす CLI。照合する版は行の `schemaVersion` が決める(v0.1 / v0.2)。
//
// 使い方: npx tsx scripts/playtest/hypothesisCheck.ts <hypothesis.json>… --today YYYY-MM-DD [--obs-items <path>]
//
// - `--today` は必須(照合の日付を機械が「今日」から決めない。H-4 が測る前に書かれた予測かを見るための基準)。
// - `--obs-items` の既定は repo の `docs/OBSERVATION_ITEMS.md`。
// - ファイルごとに 9 行(check/ok/messages)を標準出力へ書く。1 本でも落ちれば `process.exitCode = 1`
//   (`lib/gate.ts` の流儀)。引数が無い・`--today` が無いときは使い方を出して `process.exitCode = 2`。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・仮説の妥当性の判断(機械で検査できる「形式」だけを見る)。
// - 渡されたファイルを書き換えること。エンジンを起動すること。
// - `--today` を省略して今日の日付を機械が決めること。

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkResultLines, loadObsRegistry, validateHypothesisLine } from "./lib/hypothesis.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = "使い方: npx tsx scripts/playtest/hypothesisCheck.ts <hypothesis.json>… --today YYYY-MM-DD [--obs-items <path>]";

interface Args {
  files: string[];
  today: string;
  obsItems: string;
}

class UsageError extends Error {}

function parseArgs(argv: readonly string[]): Args {
  const files: string[] = [];
  let today: string | undefined;
  let obsItems: string | undefined;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]!;
    if (arg === "--today") {
      today = argv[index + 1];
      index += 1;
    } else if (arg === "--obs-items") {
      obsItems = argv[index + 1];
      index += 1;
    } else if (arg.startsWith("--")) {
      throw new UsageError(`知らない引数: ${arg}`);
    } else {
      files.push(arg);
    }
  }
  if (today === undefined) throw new UsageError("--today が無い");
  return { files, today, obsItems: obsItems ?? path.join(REPO_ROOT, "docs", "OBSERVATION_ITEMS.md") };
}

function main(): void {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.error(USAGE);
    process.exitCode = 2;
    return;
  }
  let args: Args;
  try {
    args = parseArgs(argv);
  } catch (error) {
    console.error(error instanceof UsageError ? error.message : String(error));
    console.error(USAGE);
    process.exitCode = 2;
    return;
  }

  const registry = loadObsRegistry(path.resolve(args.obsItems));

  let anyFailed = false;
  for (const file of args.files) {
    const line: unknown = JSON.parse(readFileSync(path.resolve(file), "utf-8"));
    console.log(`# ${file}`);
    // スキーマはここで固定しない。行の schemaVersion に対応する版を lib 側が選ぶ(STEP EXPO-1)。
    for (const result of validateHypothesisLine(line, { today: args.today, registry })) {
      // 状態の語は lib の 1 か所で決める(`skip` を `ok` と書かないため)
      for (const text of checkResultLines(result)) console.log(text);
      if (!result.ok) anyFailed = true;
    }
  }
  if (anyFailed) process.exitCode = 1;
}

main();
