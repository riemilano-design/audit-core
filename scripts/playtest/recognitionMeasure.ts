// STEP OPEN-2(docs/LANE_DIAG_LOG_2026-09.md §12.8)。認識(形・狙い・戦型)を数える CLI。
// 数え方は lib/recognitionMeasure.ts(純粋関数)が持つ。ここはファイルを読み、git の状態を測り、
// 書き出すだけ。
//
// 使い方:
//   npx tsx scripts/playtest/recognitionMeasure.ts \
//     --games <list.json> [--shapes <dir>]… [--intents <dir>]… [--openings <dir>]… \
//     --maxply <N|0> --out <json>
//
// - 同じ旗を複数回渡すと、そのディレクトリを合わせて読む(id が重なったら例外で止まる)。
// - `--games` は `{"games":[{"group":"…","id":"…","path":"…"}]}`。`path` は cwd 相対か絶対。
// - `--maxply` 0 は全手。
//
// 【このファイルが絶対にやらないこと】
// - 数の計算(合計・割合・判定)。lib 側がすべて持つ。
// - 人の名前・ファイル名・棋譜の中身を出力に書くこと。出るのは固定棋譜の id と数だけで、
//   入力ディレクトリの一覧も **cwd 相対に直してから** 書く(絶対パスを残さない)。
// - `scripts/playtest/out/` の下に既定で書くこと(`--out` は呼び出し側が決める)。

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadIntents } from "../../apps/server/src/analysis/intentRepository.js";
import { loadOpeningsFromDir, type OpeningDefinition } from "../../apps/server/src/analysis/openingDetector.js";
import { loadShapes } from "../../apps/server/src/analysis/shapeRepository.js";
import { readGitState } from "./lib/gitState.js";
import { measureRecognition, type MeasuredGame } from "./lib/recognitionMeasure.js";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

const USAGE =
  "使い方: npx tsx scripts/playtest/recognitionMeasure.ts --games <list.json> [--shapes <dir>]… [--intents <dir>]… [--openings <dir>]… --maxply <N|0> --out <json>";

/** 入力の読み込み・中身の誤りで終わるとき(exit 1)。 */
export class RecognitionMeasureCliError extends Error {}
/** 必須の引数が足りない・知らない引数(exit 2)。 */
export class RecognitionMeasureCliArgError extends Error {}

export interface CliArgs {
  games: string;
  shapes: string[];
  intents: string[];
  openings: string[];
  maxPly: number;
  out: string;
}

const SINGLE = ["--games", "--maxply", "--out"] as const;
const MULTI = ["--shapes", "--intents", "--openings"] as const;

export function parseArgs(argv: readonly string[]): CliArgs {
  const single = new Map<string, string>();
  const multi = new Map<string, string[]>(MULTI.map((flag) => [flag, []]));
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]!;
    if ((SINGLE as readonly string[]).includes(flag)) {
      const value = argv[index + 1];
      if (value === undefined || value.startsWith("--")) throw new RecognitionMeasureCliArgError(`${flag} に値が無い`);
      if (single.has(flag)) throw new RecognitionMeasureCliArgError(`${flag} が 2 回ある`);
      single.set(flag, value);
      index += 1;
    } else if ((MULTI as readonly string[]).includes(flag)) {
      // 同じ旗を複数回渡せる(ディレクトリを合わせて読む)。1 回で複数の値も受ける。
      while (argv[index + 1] !== undefined && !argv[index + 1]!.startsWith("--")) {
        multi.get(flag)!.push(argv[index + 1]!);
        index += 1;
      }
    } else {
      throw new RecognitionMeasureCliArgError(`知らない引数: ${flag}`);
    }
  }
  if (!single.has("--games")) throw new RecognitionMeasureCliArgError(`--games が無い。${USAGE}`);
  if (!single.has("--maxply")) throw new RecognitionMeasureCliArgError(`--maxply が無い。${USAGE}`);
  if (!single.has("--out")) throw new RecognitionMeasureCliArgError(`--out が無い。${USAGE}`);
  const maxPlyText = single.get("--maxply")!;
  const maxPly = Number(maxPlyText);
  if (!Number.isInteger(maxPly) || maxPly < 0) {
    throw new RecognitionMeasureCliArgError(`--maxply は 0 以上の整数(0 = 全手): "${maxPlyText}"`);
  }
  return {
    games: single.get("--games")!,
    shapes: multi.get("--shapes")!,
    intents: multi.get("--intents")!,
    openings: multi.get("--openings")!,
    maxPly,
    out: single.get("--out")!,
  };
}

interface GameListEntry {
  group: string;
  id: string;
  path: string;
}

/** `--games` の一覧を読む。path は cwd 相対か絶対。 */
export function readGameList(listPath: string): GameListEntry[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(readFileSync(listPath, "utf-8"));
  } catch (err) {
    throw new RecognitionMeasureCliError(`--games を読めません: "${listPath}"(${(err as Error).message})`);
  }
  const games = (parsed as { games?: unknown }).games;
  if (!Array.isArray(games) || games.length === 0) {
    throw new RecognitionMeasureCliError(`--games の中身が {"games":[…]} ではありません: "${listPath}"`);
  }
  return games.map((entry, index) => {
    const e = entry as Partial<GameListEntry>;
    if (typeof e.group !== "string" || typeof e.id !== "string" || typeof e.path !== "string") {
      throw new RecognitionMeasureCliError(`--games の ${index + 1} 件目に group/id/path が揃っていません`);
    }
    return { group: e.group, id: e.id, path: e.path };
  });
}

/** 固定棋譜を読む。`rows[].id` は固定棋譜の id(無いときだけ一覧の id を使う)。 */
function readFixedKifu(entry: GameListEntry): MeasuredGame {
  const fullPath = path.resolve(entry.path);
  let parsed: { id?: unknown; moves?: unknown; startSfen?: unknown };
  try {
    parsed = JSON.parse(readFileSync(fullPath, "utf-8")) as typeof parsed;
  } catch (err) {
    // メッセージにファイル名は出さない(人・棋譜の名前が混ざりうる)。一覧での位置だけを言う。
    throw new RecognitionMeasureCliError(`固定棋譜を読めません(group=${entry.group} id=${entry.id}): ${(err as Error).message}`);
  }
  if (!Array.isArray(parsed.moves) || parsed.moves.some((m) => typeof m !== "string")) {
    throw new RecognitionMeasureCliError(`固定棋譜に moves(文字列の配列)がありません(group=${entry.group} id=${entry.id})`);
  }
  const id = typeof parsed.id === "string" && parsed.id.length > 0 ? parsed.id : entry.id;
  const startSfen = typeof parsed.startSfen === "string" ? parsed.startSfen : undefined;
  return { group: entry.group, id, moves: parsed.moves as string[], startSfen };
}

/** 複数のディレクトリを合わせて読む。id が重なったら例外(どちらを採るかを黙って決めない)。 */
export function mergeById<T extends { id: string }>(groups: readonly T[][], what: string): T[] {
  const byId = new Map<string, T>();
  for (const group of groups) {
    for (const item of group) {
      if (byId.has(item.id)) throw new RecognitionMeasureCliError(`${what} の id が重複しています: "${item.id}"`);
      byId.set(item.id, item);
    }
  }
  return [...byId.values()];
}

/** 出力に残すパス。cwd 相対に直し、cwd の外なら basename だけにする(絶対パスを書かない)。 */
export function relativeForOutput(target: string, cwd: string = process.cwd()): string {
  const rel = path.relative(cwd, path.resolve(cwd, target));
  if (rel === "") return ".";
  if (rel.startsWith("..") || path.isAbsolute(rel)) return path.basename(path.resolve(cwd, target));
  return rel;
}

function main(): number {
  const args = parseArgs(process.argv.slice(2));

  const shapes = mergeById(args.shapes.map((dir) => loadShapes(dir)), "shapes");
  const intents = mergeById(args.intents.map((dir) => loadIntents(dir)), "intents");
  const openings = mergeById<OpeningDefinition>(
    args.openings.map((dir) => loadOpeningsFromDir(dir)),
    "openings",
  );

  const games = readGameList(args.games).map(readFixedKifu);
  const { byGroup, rows } = measureRecognition(games, { shapes, intents, openings, maxPly: args.maxPly });

  const gitState = readGitState(REPO_ROOT);
  const output = {
    kind: "recognition_measure",
    schemaVersion: "0.1",
    gitHead: gitState.gitHead,
    dirty: gitState.dirty,
    maxPly: args.maxPly,
    shapesDirs: args.shapes.map((dir) => relativeForOutput(dir)),
    intentsDirs: args.intents.map((dir) => relativeForOutput(dir)),
    openingsDirs: args.openings.map((dir) => relativeForOutput(dir)),
    shapeIds: shapes.map((s) => s.id),
    intentIds: intents.map((i) => i.id),
    openingIds: openings.map((o) => o.id),
    byGroup,
    rows,
  };

  const outPath = path.resolve(args.out);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(output, null, 2)}\n`, "utf-8");
  console.log(
    `書き込み: ${outPath}(${rows.length} 局・組 ${Object.keys(byGroup).length}・形 ${shapes.length}・狙い ${intents.length}・戦型 ${openings.length})`,
  );
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  if (err instanceof RecognitionMeasureCliArgError) {
    console.error(`${err.message}\n${USAGE}`);
    process.exit(2);
  }
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
