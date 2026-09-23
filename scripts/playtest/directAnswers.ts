// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。「浅い読みで見えた分かれ道」
// (§9.1 の 2.)の一覧 JSON(`direct_answers.json`)を作る CLI。**エンジンは呼ばない**(whatif-v2・read.ts の
// 出力(jsonl)を読むだけ)。
//
// 使い方:
//   npx tsx scripts/playtest/directAnswers.ts \
//     --whatif-v2-dir <whatif-v2 jsonl のフォルダ> --read-dir <read.ts の jsonl のフォルダ> \
//     [--whatif-v2-dir <フォルダ> --read-dir <フォルダ> …](組をまたいで合算。複数可) \
//     [--group <ラベル> …|--time-limit-sec <秒> …](--whatif-v2-dir・--read-dir のペアと同じ順・同じ数。
//       どちらか一方だけ。省略時は「組の順の番号」) \
//     --out <direct_answers.json>
//
// 【この CLI は薄くしてある】結合・選別・並び順・印の数は lib/directAnswers.ts にあり、そちらに試験がある。
// ここでやるのは、--whatif-v2-dir・--read-dir のペアごとに *.jsonl を読む・局ごとに結合する・書く、だけ。
//
// 【gameNo の決め方(計画に無い判断。実装担当の判断)】1 対の --whatif-v2-dir・--read-dir を「1 つの組」として、
// その組の中で kifuId の昇順に 1, 2, 3, … を振る(`lib/reportData.ts` の `buildGames` と同じ考え方 ―
// kifuId でソートしてから index + 1)。組をまたいで gameNo を通し番号にはしない(patient_report_data.json の
// games[].no は組ごとに 1 から始まる番号であり、この CLI の gameNo もそれに合わせる)。
//
// 【group(組のラベル)の決め方(司令塔の仕様追記 1、2026-09-24。実装担当の判断)】「局」の番号が組をまたいで
// 重なる(3 分の組・10 分の組の両方に 1〜10 がある)ため、表で区別できるよう組のラベルを持たせる。
// - `--group <ラベル>`(--whatif-v2-dir・--read-dir のペアと同じ順・同じ数)を渡せば、そのままラベルにする。
// - `--time-limit-sec <秒>`(同じ順・同じ数)を渡せば、`report-pdf/check_answer.py` の `tag_of_time_limit_sec`
//   と同じ対応(180 → 3 分の組、600 → 10 分の組)でラベルにする。この CLI は `--patient` の中身を読まなくても
//   ラベルを決められるため、`--patient <path>` そのものは受け付けない(`--time-limit-sec` だけで足りる ―
//   計画に無い簡略化)。
// - どちらも渡さなければ、組の順の番号(1, 2, 3, …)をラベルにする(「組の順の番号」)。
// - 両方渡す・数が合わない・`--time-limit-sec` が 180/600 以外は exit 1。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。名前・/Users/ を含む絶対パスを出力へ書くこと。
// 新しい閾値を置くこと(TYPE_VALUES を import して使うだけ。180/600 は check_answer.py と同じ値の再利用)。

import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readGitState } from "./lib/gitState.js";
import type { ReadMoveMarks } from "./lib/read.js";
import type { WhatifSideRaw } from "./lib/type.js";
import {
  buildDirectAnswersFile,
  joinDirectAnswersGame,
  type DirectAnswersGameJoinResult,
  type DirectAnswersReadPositionInput,
  type DirectAnswersWhatifPositionInput,
} from "./lib/directAnswers.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE =
  "使い方: npx tsx scripts/playtest/directAnswers.ts --whatif-v2-dir <フォルダ> --read-dir <フォルダ> [--whatif-v2-dir <フォルダ> --read-dir <フォルダ> …] --out <direct_answers.json>";

function collectAllValues(args: readonly string[], name: string): string[] {
  const values: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === name) {
      const value = args[i + 1];
      if (value === undefined) throw new Error(`${name} に値が無い`);
      values.push(value);
    }
  }
  return values;
}

function argValue(args: readonly string[], name: string): string | undefined {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
}

function readJsonLines(filePath: string): Record<string, unknown>[] {
  const text = readFileSync(filePath, "utf-8");
  return text
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

// ---- whatif-v2 の position 行 ----

interface WhatifCandidateRow {
  move: string;
  pv: string[];
  side: WhatifSideRaw;
}

interface WhatifLossRow {
  cpValue: number | null;
  isLowerBound: boolean;
}

interface WhatifPositionRow {
  kind: "position";
  ply: number;
  displayPly: number;
  sfen: string;
  candidates: WhatifCandidateRow[];
  actualMove: string;
  actualSide: WhatifSideRaw;
  topGapCp: number | null;
  loss: WhatifLossRow | null;
  scenes: { fork: boolean };
}

interface WhatifMetaRow {
  kind: "meta";
  kifuId: string;
}

function readWhatifPositions(whatifPath: string): { kifuId: string; positions: DirectAnswersWhatifPositionInput[] } {
  const rows = readJsonLines(whatifPath);
  const meta = rows.find((row) => row.kind === "meta") as unknown as WhatifMetaRow | undefined;
  if (meta === undefined) throw new Error(`whatif-v2 の記録に meta 行がありません: ${whatifPath}`);
  const positionRows = rows.filter((row) => row.kind === "position") as unknown as WhatifPositionRow[];
  const positions: DirectAnswersWhatifPositionInput[] = [];
  for (const row of positionRows) {
    const top1 = row.candidates[0];
    if (top1 === undefined) continue; // 候補 0 件の局面(計画に無い理論上の状態。read.ts・type.ts と同じ扱い)
    positions.push({
      ply: row.ply,
      displayPly: row.displayPly,
      sfen: row.sfen,
      top1Move: top1.move,
      pv: top1.pv,
      top1Side: top1.side,
      actualMove: row.actualMove,
      actualSide: row.actualSide,
      topGapCp: row.topGapCp,
      loss: row.loss === null ? null : { cpValue: row.loss.cpValue, isLowerBound: row.loss.isLowerBound },
      fork: row.scenes.fork,
    });
  }
  return { kifuId: meta.kifuId, positions };
}

// ---- read.ts の分かれ道の行 ----

interface ReadPositionRow {
  kind: "position";
  ply: number;
  firstVisibleNodes: number | null;
  top1Tags: ReadMoveMarks;
  actualTags: ReadMoveMarks;
}

interface ReadMetaRow {
  kind: "meta";
  kifuId: string;
}

function readReadPositions(readPath: string): { kifuId: string; positions: DirectAnswersReadPositionInput[] } {
  const rows = readJsonLines(readPath);
  const meta = rows.find((row) => row.kind === "meta") as unknown as ReadMetaRow | undefined;
  if (meta === undefined) throw new Error(`read の記録に meta 行がありません: ${readPath}`);
  const positionRows = rows.filter((row) => row.kind === "position") as unknown as ReadPositionRow[];
  const positions = positionRows.map((row) => ({
    ply: row.ply,
    firstVisibleNodes: row.firstVisibleNodes,
    top1Tags: row.top1Tags,
    actualTags: row.actualTags,
  }));
  return { kifuId: meta.kifuId, positions };
}

// ---- 1 組(--whatif-v2-dir・--read-dir のペア)ぶんの処理 ----

function jsonlFilesOf(dirPath: string): string[] {
  return readdirSync(dirPath)
    .filter((name) => name.endsWith(".jsonl"))
    .sort();
}

/** `report-pdf/check_answer.py` の `tag_of_time_limit_sec` と同じ対応(司令塔の仕様追記 1)。 */
function groupLabelOfTimeLimitSec(sec: number): string {
  if (sec === 180) return "3 分";
  if (sec === 600) return "10 分";
  throw new Error(`--time-limit-sec は 180 か 600 です(${sec})`);
}

function processGroup(whatifDir: string, readDir: string, group: string): DirectAnswersGameJoinResult[] {
  const whatifDirPath = path.resolve(whatifDir);
  const readDirPath = path.resolve(readDir);
  const files = jsonlFilesOf(whatifDirPath);
  if (files.length === 0) throw new Error(`whatif-v2 のフォルダに *.jsonl が無い: ${whatifDirPath}`);

  const results: DirectAnswersGameJoinResult[] = [];
  files.forEach((name, index) => {
    const gameNo = index + 1; // 組の中で kifuId の昇順に 1, 2, 3, …(実装担当の判断。ファイル冒頭コメント参照)
    const whatifPath = path.join(whatifDirPath, name);
    const readPath = path.join(readDirPath, name);
    const { kifuId: whatifKifuId, positions: whatifPositions } = readWhatifPositions(whatifPath);
    const { kifuId: readKifuId, positions: readPositions } = readReadPositions(readPath);
    if (whatifKifuId !== readKifuId) {
      throw new Error(`--whatif-v2-dir(kifuId=${whatifKifuId})・--read-dir(kifuId=${readKifuId})が対応していません(${name})`);
    }
    results.push(joinDirectAnswersGame(whatifKifuId, gameNo, group, whatifPositions, readPositions));
  });
  return results;
}

/** ペアの数に合わせて組のラベルを決める(司令塔の仕様追記 1。ファイル冒頭コメント参照)。 */
function groupLabelsOf(args: readonly string[], pairCount: number): string[] {
  const groupArgs = collectAllValues(args, "--group");
  const timeLimitArgs = collectAllValues(args, "--time-limit-sec");
  if (groupArgs.length > 0 && timeLimitArgs.length > 0) {
    throw new Error("--group と --time-limit-sec は同時に指定できません");
  }
  if (groupArgs.length > 0) {
    if (groupArgs.length !== pairCount) throw new Error(`--group(${groupArgs.length} 個)と --whatif-v2-dir(${pairCount} 個)の数が対応していません`);
    return groupArgs;
  }
  if (timeLimitArgs.length > 0) {
    if (timeLimitArgs.length !== pairCount) {
      throw new Error(`--time-limit-sec(${timeLimitArgs.length} 個)と --whatif-v2-dir(${pairCount} 個)の数が対応していません`);
    }
    return timeLimitArgs.map((sec) => groupLabelOfTimeLimitSec(Number(sec)));
  }
  return Array.from({ length: pairCount }, (_, index) => String(index + 1)); // 組の順の番号
}

function main(): number {
  const args = process.argv.slice(2);
  const whatifDirs = collectAllValues(args, "--whatif-v2-dir");
  const readDirs = collectAllValues(args, "--read-dir");
  const outArg = argValue(args, "--out");
  if (whatifDirs.length === 0 || readDirs.length === 0 || outArg === undefined) {
    console.error(USAGE);
    return 1;
  }
  if (whatifDirs.length !== readDirs.length) {
    console.error(`--whatif-v2-dir(${whatifDirs.length} 個)と --read-dir(${readDirs.length} 個)の数が対応していません`);
    return 1;
  }
  const groupLabels = groupLabelsOf(args, whatifDirs.length);

  const games: DirectAnswersGameJoinResult[] = [];
  for (let i = 0; i < whatifDirs.length; i++) {
    games.push(...processGroup(whatifDirs[i]!, readDirs[i]!, groupLabels[i]!));
  }

  const file = buildDirectAnswersFile(games);
  const gitState = readGitState(REPO_ROOT);
  const out = { kind: "direct_answers", gitHead: gitState.gitHead, dirty: gitState.dirty, ...file };

  const outPath = path.resolve(outArg);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(out, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(局 ${file.counts.gamesCount} / 分かれ道 ${file.counts.totalForkCount} / 浅い読み ${file.counts.totalCount})`);
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
