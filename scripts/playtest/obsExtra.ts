// STEP OBS-5'(docs/LANE_DIAG_LOG_2026-09.md §12.6)。観測の写し `obs_extra.json` を作る CLI。
// 純粋な組み立ては `lib/obsExtra.ts`(`buildObsExtra`)が行う。ここはファイルを読み、git の状態を測り、
// 書き出すだけ(`reportData.ts` と同じ `--records`・`--kifu` の読み方をそのまま使う)。
//
// 使い方:
//   npx tsx scripts/playtest/obsExtra.ts --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> --out <obs_extra.json>
//
// 【このファイルが絶対にやらないこと】
// - 合計・割合・新しい数の計算(`lib/obsExtra.ts` が既存の値を組み合わせるだけ)。
// - `patient_report_data.json`・`time_cause.json` を読み書きすること(この道具は `--records`・`--kifu` だけを読む)。
// - `scripts/playtest/out/` の下に書くこと(`--out` は呼び出し側が決める。この CLI 自身は既定を持たない)。

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { readGitState } from "./lib/gitState.js";
import { buildObsExtra } from "./lib/obsExtra.js";
import type { GameSource } from "./lib/reportData.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

const USAGE = "使い方: npx tsx scripts/playtest/obsExtra.ts --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> --out <obs_extra.json>";

export class ObsExtraCliError extends Error {}
/** 必須の引数が足りない(使い方を出して exit 2 にする側。データの読み込みエラー〈ObsExtraCliError〉とは exit code を分ける)。 */
export class ObsExtraCliArgError extends Error {}

interface CliArgs {
  records: string[];
  kifu: string[];
  out: string;
}

const SINGLE = ["--out"] as const;
const MULTI = ["--records", "--kifu"] as const;

export function parseArgs(argv: readonly string[]): CliArgs {
  const single = new Map<string, string>();
  const multi = new Map<string, string[]>(MULTI.map((flag) => [flag, []]));
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if ((SINGLE as readonly string[]).includes(flag)) {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new ObsExtraCliArgError(`${flag} に値が無い`);
      if (single.has(flag)) throw new ObsExtraCliArgError(`${flag} が 2 回ある`);
      single.set(flag, value);
      index += 1;
    } else if ((MULTI as readonly string[]).includes(flag)) {
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        multi.get(flag)!.push(argv[index + 1]!);
        index += 1;
      }
    } else {
      throw new ObsExtraCliArgError(`知らない引数: ${flag}`);
    }
  }
  if (!single.has("--out")) throw new ObsExtraCliArgError(`--out が無い。${USAGE}`);
  if (multi.get("--records")!.length === 0) throw new ObsExtraCliArgError(`--records が無い。${USAGE}`);
  if (multi.get("--kifu")!.length === 0) throw new ObsExtraCliArgError(`--kifu が無い。${USAGE}`);
  return { records: multi.get("--records")!, kifu: multi.get("--kifu")!, out: single.get("--out")! };
}

function readJsonlLines(filePath: string): Array<Record<string, unknown>> {
  return readFileSync(filePath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

/** `reportData.ts` の `readGameSource` と同じ読み方(動きを変えない。この CLI が独立して持つ最小の複製)。 */
function readGameSource(recordsPath: string, kifuFiles: readonly string[]): GameSource {
  const lines = readJsonlLines(recordsPath);
  const meta = lines.find((line) => line["kind"] === "meta") as unknown as MetaLine | undefined;
  if (meta === undefined) throw new ObsExtraCliError(`${recordsPath} に meta 行が無い`);
  const records = lines.filter((line) => line["kind"] === "record") as unknown as RecordLine[];
  const kifuPath = kifuFiles.find((file) => path.basename(file) === `${meta.kifuId}.fixed.json` || path.basename(file, ".fixed.json") === meta.kifuId);
  if (kifuPath === undefined) throw new ObsExtraCliError(`${meta.kifuId} の固定棋譜(--kifu)が見つからない`);
  const fixed = JSON.parse(readFileSync(kifuPath, "utf-8")) as GameSource["fixed"];
  return { kifuId: meta.kifuId, meta, records, fixed };
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  const sources = args.records.map((recordsPath) => readGameSource(recordsPath, args.kifu));
  const gitState = readGitState(REPO_ROOT);

  const extra = buildObsExtra(sources, gitState.gitHead, gitState.dirty);

  const outPath = path.resolve(args.out);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(extra, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(pairs ${extra.pairs.length} 件・phaseMoves ${extra.phaseMoves.length} 局)`);
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  if (err instanceof ObsExtraCliArgError) {
    console.error(`${err.message}\n${USAGE}`);
    process.exit(2);
  }
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
