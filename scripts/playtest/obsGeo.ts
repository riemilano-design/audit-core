// STEP OBS-5(docs/LANE_DIAG_LOG_2026-09.md §12.10 (A))。観測の写し `obs_geo.json` を作る CLI。
// 純粋な組み立ては `lib/obsGeo.ts`(`buildObsGeo`)が行う。ここはファイルを読み、git の状態を測り、
// 書き出すだけ(`obsExtra.ts` と同じ読み方をそのまま使う)。
//
// 使い方:
//   npx tsx scripts/playtest/obsGeo.ts --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> \
//     [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] --out <obs_geo.json>
//
// 【このファイルが絶対にやらないこと】
// - 盤の計算・幾何の判定(`lib/obsGeo.ts` が既存の道具を呼ぶだけで行う)。
// - `scripts/playtest/out/` の下に書くこと(`--out` は呼び出し側が決める。この CLI 自身は既定を持たない)。

import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { MetaLine, RecordLine } from "./invariants/types.js";
import { readGitState } from "./lib/gitState.js";
import { buildObsGeo } from "./lib/obsGeo.js";
import type { GameSource } from "./lib/reportData.js";
import type { MoveFeatureWhatifPosition } from "./lib/timeFeatures.js";
import type { WhatifSideRaw } from "./lib/type.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

const USAGE =
  "使い方: npx tsx scripts/playtest/obsGeo.ts --records <段 2 の JSONL …> --kifu <固定棋譜 JSON …> [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] --out <obs_geo.json>";

export class ObsGeoCliError extends Error {}
/** 必須の引数が足りない(使い方を出して exit 2 にする側。データの読み込みエラー〈ObsGeoCliError〉とは exit code を分ける)。 */
export class ObsGeoCliArgError extends Error {}

interface CliArgs {
  records: string[];
  kifu: string[];
  whatifV2Dir?: string;
  out: string;
}

const SINGLE = ["--out", "--whatif-v2-dir"] as const;
const MULTI = ["--records", "--kifu"] as const;

export function parseArgs(argv: readonly string[]): CliArgs {
  const single = new Map<string, string>();
  const multi = new Map<string, string[]>(MULTI.map((flag) => [flag, []]));
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if ((SINGLE as readonly string[]).includes(flag)) {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new ObsGeoCliArgError(`${flag} に値が無い`);
      if (single.has(flag)) throw new ObsGeoCliArgError(`${flag} が 2 回ある`);
      single.set(flag, value);
      index += 1;
    } else if ((MULTI as readonly string[]).includes(flag)) {
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        multi.get(flag)!.push(argv[index + 1]!);
        index += 1;
      }
    } else {
      throw new ObsGeoCliArgError(`知らない引数: ${flag}`);
    }
  }
  if (!single.has("--out")) throw new ObsGeoCliArgError(`--out が無い。${USAGE}`);
  if (multi.get("--records")!.length === 0) throw new ObsGeoCliArgError(`--records が無い。${USAGE}`);
  if (multi.get("--kifu")!.length === 0) throw new ObsGeoCliArgError(`--kifu が無い。${USAGE}`);
  return { records: multi.get("--records")!, kifu: multi.get("--kifu")!, whatifV2Dir: single.get("--whatif-v2-dir"), out: single.get("--out")! };
}

function readJsonlLines(filePath: string): Array<Record<string, unknown>> {
  return readFileSync(filePath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

/** `reportData.ts` の `readGameSource`・`obsExtra.ts` と同じ読み方(動きを変えない。この CLI が独立して持つ最小の複製)。 */
function readGameSource(recordsPath: string, kifuFiles: readonly string[]): GameSource {
  const lines = readJsonlLines(recordsPath);
  const meta = lines.find((line) => line["kind"] === "meta") as unknown as MetaLine | undefined;
  if (meta === undefined) throw new ObsGeoCliError(`${recordsPath} に meta 行が無い`);
  const records = lines.filter((line) => line["kind"] === "record") as unknown as RecordLine[];
  const kifuPath = kifuFiles.find((file) => path.basename(file) === `${meta.kifuId}.fixed.json` || path.basename(file, ".fixed.json") === meta.kifuId);
  if (kifuPath === undefined) throw new ObsGeoCliError(`${meta.kifuId} の固定棋譜(--kifu)が見つからない`);
  const fixed = JSON.parse(readFileSync(kifuPath, "utf-8")) as GameSource["fixed"];
  return { kifuId: meta.kifuId, meta, records, fixed };
}

// ---- --whatif-v2-dir(scripts/playtest/timeSearch.ts の readWhatifPositions と同じ読み方の複製) ----

interface WhatifCandidateRow {
  move: string;
  side: WhatifSideRaw;
}

interface WhatifLossRow {
  cpValue: number | null;
  isLowerBound: boolean;
}

interface WhatifPositionRow {
  kind: "position";
  ply: number;
  sfen: string;
  candidates: WhatifCandidateRow[];
  actualMove: string;
  actualSide: WhatifSideRaw;
  actualRank: number | null;
  loss: WhatifLossRow | null;
  scenes: { fork: boolean };
}

function readWhatifPositions(whatifPath: string): MoveFeatureWhatifPosition[] {
  const rows = readJsonlLines(whatifPath).filter((row) => row["kind"] === "position") as unknown as WhatifPositionRow[];
  const positions: MoveFeatureWhatifPosition[] = [];
  for (const row of rows) {
    const top1 = row.candidates[0];
    if (top1 === undefined) continue; // 候補 0 件の局面(timeSearch.ts と同じ、計画に無い理論上の状態)
    positions.push({
      ply: row.ply,
      sfen: row.sfen,
      fork: row.scenes.fork,
      top1Side: top1.side,
      actualSide: row.actualSide,
      top1Move: top1.move,
      actualMove: row.actualMove,
      actualRank: row.actualRank,
      lossCpValue: row.loss?.cpValue ?? null,
      lossIsLowerBound: row.loss?.isLowerBound ?? false,
    });
  }
  return positions;
}

/** `--whatif-v2-dir` を渡した以上、全局ぶん `<kifuId>.jsonl` が揃っている前提(`timeCause.ts`・`timeSearch.ts` と同じ)。 */
function readWhatifPositionsByKifuId(sources: readonly GameSource[], whatifV2Dir: string): Map<string, MoveFeatureWhatifPosition[]> {
  const dirPath = path.resolve(whatifV2Dir);
  const out = new Map<string, MoveFeatureWhatifPosition[]>();
  for (const source of sources) {
    const whatifPath = path.join(dirPath, `${source.kifuId}.jsonl`);
    if (!existsSync(whatifPath)) throw new ObsGeoCliError(`--whatif-v2-dir に ${source.kifuId}.jsonl が無い: ${whatifPath}`);
    out.set(source.kifuId, readWhatifPositions(whatifPath));
  }
  return out;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));
  const sources = args.records.map((recordsPath) => readGameSource(recordsPath, args.kifu));
  const gitState = readGitState(REPO_ROOT);

  const whatifPositionsByKifuId = args.whatifV2Dir === undefined ? null : readWhatifPositionsByKifuId(sources, args.whatifV2Dir);

  const geo = buildObsGeo(sources, whatifPositionsByKifuId, gitState.gitHead, gitState.dirty);

  const outPath = path.resolve(args.out);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(geo, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(moves ${geo.moves.length} 手・decisionContext ${geo.decisionContext.length} 行)`);
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  if (err instanceof ObsGeoCliArgError) {
    console.error(`${err.message}\n${USAGE}`);
    process.exit(2);
  }
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
