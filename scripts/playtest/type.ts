// STEP TYPE(docs/STEP_TYPE_PLAN_2026-09-23.md)。分かれ道の「タイプ」(大きさ×側×性質の組)を測る段の CLI。
// **エンジンは呼ばない**(whatif-v2・read.ts の出力と fixed 棋譜の moveSeconds を読むだけ)。
//
// 2 つのモードを持つ:
//
// 生成(1 局ぶん): npx tsx scripts/playtest/type.ts --whatif <whatif-v2.jsonl> --read <read.jsonl>
//                    --kifu <固定棋譜 JSON> --out <type/<id>.jsonl>
//
// 集計(複数局・複数 work をまとめる): npx tsx scripts/playtest/type.ts --summarize <type ディレクトリ …>
//                    --out <summary.json>
//
// 【この CLI は薄くしてある】組の付け方・集計は lib/type.ts にあり、そちらに試験がある。
// ここでやるのは、whatif-v2・read.ts・固定棋譜を読む・id で結合する・行を書く(生成)、
// または複数の type ディレクトリの *.jsonl を読み集計する(集計)、だけである。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。タイプへの命名。
// 名前・/Users/ を含む絶対パスを出力へ書くこと。手・SFEN・評価値を書くこと。

import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readGitState } from "./lib/gitState.js";
import {
  TYPE_VALUES,
  medianSecondsBySideOf,
  repeatedGroupsOf,
  retreatGameCountOf,
  spentSecOfDisplayPly,
  typeForkOf,
  typeGroupCountsOf,
  type TypeFork,
  type TypeGame,
  type TypeNatureTags,
  type WhatifSideRaw,
} from "./lib/type.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE = [
  "使い方:",
  "  生成: npx tsx scripts/playtest/type.ts --whatif <whatif-v2.jsonl> --read <read.jsonl> --kifu <固定棋譜 JSON> --out <type/<id>.jsonl>",
  "  集計: npx tsx scripts/playtest/type.ts --summarize <type ディレクトリ …> --out <summary.json>",
].join("\n");

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

/** `--summarize` の直後から、次の `--` で始まるトークンの手前までを集める。 */
function collectUntilFlag(args: readonly string[], startIndex: number): string[] {
  const values: string[] = [];
  let i = startIndex;
  while (i < args.length && !args[i]!.startsWith("--")) {
    values.push(args[i]!);
    i++;
  }
  return values;
}

function readJsonLines(filePath: string): Record<string, unknown>[] {
  const text = readFileSync(filePath, "utf-8");
  return text
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

// ---- 生成モード ----

interface WhatifCandidateRow {
  side: WhatifSideRaw;
}

interface WhatifPositionRow {
  kind: "position";
  ply: number;
  displayPly: number;
  candidates: WhatifCandidateRow[];
  actualSide: WhatifSideRaw;
  scenes: { fork: boolean };
}

interface WhatifMetaRow {
  kind: "meta";
  kifuId: string;
}

interface ReadPositionRow {
  kind: "position";
  ply: number;
  displayPly: number;
  firstVisibleNodes: number | null;
  actualTags: TypeNatureTags;
  actualMaterialLook: number;
}

interface ReadMetaRow {
  kind: "meta";
  kifuId: string;
}

interface FixedKifuLike {
  id: string;
  moveSeconds?: readonly ({ spentSec: number; totalSec: number } | null)[];
}

function readWhatifForkPositions(whatifPath: string): { kifuId: string; positions: WhatifPositionRow[] } {
  const rows = readJsonLines(whatifPath);
  const meta = rows.find((row) => row.kind === "meta") as unknown as WhatifMetaRow | undefined;
  if (meta === undefined) throw new Error(`whatif の記録に meta 行がありません: ${whatifPath}`);
  const positions = rows.filter((row) => row.kind === "position" && (row as unknown as WhatifPositionRow).scenes.fork === true) as unknown as WhatifPositionRow[];
  return { kifuId: meta.kifuId, positions };
}

function readReadPositions(readPath: string): { kifuId: string; positions: ReadPositionRow[] } {
  const rows = readJsonLines(readPath);
  const meta = rows.find((row) => row.kind === "meta") as unknown as ReadMetaRow | undefined;
  if (meta === undefined) throw new Error(`read の記録に meta 行がありません: ${readPath}`);
  const positions = rows.filter((row) => row.kind === "position") as unknown as ReadPositionRow[];
  return { kifuId: meta.kifuId, positions };
}

function runGenerate(args: readonly string[]): number {
  const whatifArg = argValue(args, "--whatif");
  const readArg = argValue(args, "--read");
  const kifuArg = argValue(args, "--kifu");
  const outArg = argValue(args, "--out");
  if (whatifArg === undefined || readArg === undefined || kifuArg === undefined || outArg === undefined) {
    console.error(USAGE);
    return 1;
  }

  const whatifPath = path.resolve(whatifArg);
  const readPath = path.resolve(readArg);
  const kifuPath = path.resolve(kifuArg);

  const { kifuId: whatifKifuId, positions: forkPositions } = readWhatifForkPositions(whatifPath);
  const { kifuId: readKifuId, positions: readPositions } = readReadPositions(readPath);
  const kifu = JSON.parse(readFileSync(kifuPath, "utf-8")) as FixedKifuLike;

  if (whatifKifuId !== readKifuId || whatifKifuId !== kifu.id) {
    console.error(`--whatif(kifuId=${whatifKifuId})・--read(kifuId=${readKifuId})・--kifu(id=${kifu.id})が対応していません`);
    return 1;
  }
  const kifuId = whatifKifuId;

  const readByPly = new Map<number, ReadPositionRow>();
  for (const position of readPositions) readByPly.set(position.ply, position);

  const forks: TypeFork[] = [];
  // read.ts 側で候補が 0 件のため除外された分かれ道(計画に無い理論上の状態。read.ts の skippedForkCount と同じ考え方)。
  // 24 局の実測ではこの状態は起きていない(read.ts の既知の限界と同じ)。
  let skippedForkCount = 0;
  for (const position of forkPositions) {
    const readPosition = readByPly.get(position.ply);
    if (readPosition === undefined) {
      skippedForkCount++;
      continue;
    }
    if (readPosition.displayPly !== position.displayPly) {
      throw new Error(`whatif と read の displayPly が食い違う(kifuId=${kifuId}, ply=${position.ply})`);
    }
    const top1 = position.candidates[0];
    if (top1 === undefined) {
      // read.ts 側もここでは skippedForkCount に数えているはずなので、通常は readByPly に無く上の分岐で弾かれる。
      // 念のための歯止め(理論上の状態)。
      skippedForkCount++;
      continue;
    }
    const spentSec = spentSecOfDisplayPly(kifu.moveSeconds, position.displayPly);
    const fork = typeForkOf({
      ply: position.ply,
      displayPly: position.displayPly,
      firstVisibleNodes: readPosition.firstVisibleNodes,
      top1Side: top1.side,
      actualSide: position.actualSide,
      actualTags: readPosition.actualTags,
      actualMaterialLook: readPosition.actualMaterialLook,
      spentSec,
    });
    forks.push(fork);
  }

  const gitState = readGitState(REPO_ROOT);
  const lines: string[] = [
    JSON.stringify({ kind: "meta", kifuId, gitHead: gitState.gitHead, dirty: gitState.dirty, values: TYPE_VALUES }),
    ...forks.map((fork) => JSON.stringify({ kind: "fork", ...fork })),
    JSON.stringify({ kind: "summary", kifuId, forkCount: forks.length, skippedForkCount }),
  ];

  const outPath = path.resolve(outArg);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${lines.join("\n")}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(分かれ道 ${forks.length} / 除外 ${skippedForkCount})`);
  return 0;
}

// ---- 集計モード ----

interface TypeMetaRow {
  kind: "meta";
  kifuId: string;
  values: unknown;
}

interface TypeForkRow extends TypeFork {
  kind: "fork";
}

function readTypeGameFile(filePath: string): { game: TypeGame; values: unknown } {
  const rows = readJsonLines(filePath);
  const meta = rows.find((row) => row.kind === "meta") as unknown as TypeMetaRow | undefined;
  if (meta === undefined) throw new Error(`type の記録に meta 行がありません: ${filePath}`);
  const forks = rows.filter((row) => row.kind === "fork") as unknown as TypeForkRow[];
  return { game: { id: meta.kifuId, forks }, values: meta.values };
}

function runSummarize(args: readonly string[]): number {
  const summarizeIndex = args.indexOf("--summarize");
  const dirs = collectUntilFlag(args, summarizeIndex + 1);
  const outArg = argValue(args, "--out");
  if (dirs.length === 0 || outArg === undefined) {
    console.error(USAGE);
    return 1;
  }

  const games: TypeGame[] = [];
  let firstValues: unknown;
  let firstValuesSource: string | undefined;
  for (const dir of dirs) {
    const dirPath = path.resolve(dir);
    const files = readdirSync(dirPath)
      .filter((name) => name.endsWith(".jsonl"))
      .sort();
    if (files.length === 0) {
      console.error(`型のディレクトリに *.jsonl が無い: ${dirPath}`);
      return 1;
    }
    for (const name of files) {
      const filePath = path.join(dirPath, name);
      const { game, values } = readTypeGameFile(filePath);
      if (firstValuesSource === undefined) {
        firstValues = values;
        firstValuesSource = filePath;
      } else if (JSON.stringify(values) !== JSON.stringify(firstValues)) {
        console.error(`TYPE_VALUES が記録の間でそろわない(${firstValuesSource} と ${filePath})`);
        return 1;
      }
      games.push(game);
    }
  }

  const counts = typeGroupCountsOf(games);
  const repeatedGroups = repeatedGroupsOf(counts);
  const sideSecondsMedian = medianSecondsBySideOf(games);
  const retreatGameCount = retreatGameCountOf(games);
  const forksCount = games.reduce((sum, game) => sum + game.forks.length, 0);

  const gitState = readGitState(REPO_ROOT);
  const summary = {
    kind: "summary",
    gitHead: gitState.gitHead,
    dirty: gitState.dirty,
    values: TYPE_VALUES,
    gamesCount: games.length,
    forksCount,
    counts,
    repeatMinGames: TYPE_VALUES.repeatMinGames,
    repeatedGroups,
    sideSecondsMedian,
    retreatGameCount,
  };

  const outPath = path.resolve(outArg);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(summary, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(局 ${games.length} / 分かれ道 ${forksCount} / 組 ${counts.length} / 3局以上の組 ${repeatedGroups.length})`);
  return 0;
}

function main(): number {
  const args = process.argv.slice(2);
  if (args.includes("--summarize")) return runSummarize(args);
  return runGenerate(args);
}

try {
  process.exit(main());
} catch (err) {
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
