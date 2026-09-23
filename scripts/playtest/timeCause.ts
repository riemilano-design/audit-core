// STEP TIME-CAUSE(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)。時間負けの要因を、機械で測れる候補
// (C1〜C10)に分解する CLI。**エンジンは呼ばない**(固定棋譜の `moveSeconds`・whatif-v2(STEP WHATIF 作業 4)の
// jsonl・`patient_report_data.json` を読むだけ)。
//
// 使い方(--kifu-dir で 1 つの組が始まる。組は複数渡せる):
//   npx tsx scripts/playtest/timeCause.ts \
//     --kifu-dir <固定棋譜〈*.fixed.json〉のフォルダ> --patient <patient_report_data.json> --time-limit-sec <秒> \
//       [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] \
//     [--kifu-dir <フォルダ> --patient <path> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] …]（組をまたいで合算） \
//     --out <time_cause.json>
//
// 【この CLI は薄くしてある】局ごとの C1〜C9・組ごとの集計は lib/timeCause.ts にあり、そちらに試験がある。
// ここでやるのは、引数の解釈・ファイルを読む・局ごとに呼ぶ・書く、だけ。
//
// 【組(--kifu-dir で始まるブロック)の決め方(実装担当の判断)】`directAnswers.ts`・`finalPositions.ts` は
// フラグの「対」を同じ回数だけ並べる形式だが、この CLI は `--whatif-v2-dir` が組ごとに有る・無いの両方が
// 起こる(計画の実データ: tatsunami20 に `whatif-v2` が無い)。そのため「`--kifu-dir` が出るたびに新しい組を
// 始め、次の `--kifu-dir`(または `--out`)までの間のフラグをその組のものとして読む」形式にした。
//
// 【group(組のラベル)の決め方】`directAnswers.ts`・`finalPositions.ts` と同じ対応
// (`report-pdf/check_answer.py` の `tag_of_time_limit_sec`。180 → 3 分の組、600 → 10 分の組)。
// この CLI は `--time-limit-sec` を必須にする(C10 の「終局時の残り秒」に持ち時間の秒が要るため。計画 §2 の C10)。
//
// 【局の選び方(実装担当の判断)】`--kifu-dir` の `*.fixed.json` のうち、`--patient` の `games[].id` に
// 対応があるものだけを対象にする(対応が無ければ対象外 ― 比較用の別データ等)。`timeUpLoss` は
// `time.timeUpLosses[*].gameNo` の集合に、対応する `games[].no` が含まれるかで決める(`finalPositions.ts` と
// 同じ考え方)。`--patient` の `time.available` が false の組は `timeUpLosses` が無いため、全局 `timeUpLoss: false`
// として扱う(実データでは起きない。念のための歯止め)。
//
// 【whatif-v2 の結び方】`--whatif-v2-dir` を渡した組では、`--kifu-dir` の各 `*.fixed.json` の `id` と同じ名前
// (`<id>.jsonl`)のファイルを読む(`directAnswers.ts` と同じ命名の前提)。ファイルが無ければ止める
// (`--whatif-v2-dir` を渡した以上、全局ぶん揃っている前提。揃っていないのはデータの食い違いとして検出する)。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。名前・/Users/ を含む絶対パスを出力へ書くこと。
// 新しい閾値を置くこと(すべて lib/timeCause.ts・lib/reportData.ts の既存の値を使い回す)。

import { existsSync, readdirSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readGitState } from "./lib/gitState.js";
import { buildGameTimeCause, buildTimeCauseFile, type GameTimeCause, type TimeCauseFixedKifu, type TimeCauseWhatifPositionInput } from "./lib/timeCause.js";
import type { WhatifSideRaw } from "./lib/type.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE =
  "使い方: npx tsx scripts/playtest/timeCause.ts --kifu-dir <フォルダ> --patient <patient_report_data.json> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] [--kifu-dir … …] --out <time_cause.json>";

/** `report-pdf/check_answer.py` の `tag_of_time_limit_sec`・`directAnswers.ts`・`finalPositions.ts` と同じ対応。 */
function groupLabelOfTimeLimitSec(sec: number): string {
  if (sec === 180) return "3 分";
  if (sec === 600) return "10 分";
  throw new Error(`--time-limit-sec は 180 か 600 です(${sec})`);
}

// ---- 引数の解釈(--kifu-dir で組が始まる) ----

interface GroupArgs {
  kifuDir: string;
  patient?: string;
  timeLimitSec?: number;
  whatifV2Dir?: string;
}

function parseArgs(args: readonly string[]): { groups: GroupArgs[]; out?: string } {
  const groups: GroupArgs[] = [];
  let current: GroupArgs | null = null;
  let out: string | undefined;
  let i = 0;
  while (i < args.length) {
    const flag = args[i];
    const value = args[i + 1];
    if (flag === "--kifu-dir") {
      if (value === undefined) throw new Error("--kifu-dir に値が無い");
      current = { kifuDir: value };
      groups.push(current);
      i += 2;
      continue;
    }
    if (flag === "--patient") {
      if (current === null) throw new Error("--patient の前に --kifu-dir が要る");
      if (value === undefined) throw new Error("--patient に値が無い");
      current.patient = value;
      i += 2;
      continue;
    }
    if (flag === "--time-limit-sec") {
      if (current === null) throw new Error("--time-limit-sec の前に --kifu-dir が要る");
      if (value === undefined) throw new Error("--time-limit-sec に値が無い");
      current.timeLimitSec = Number(value);
      i += 2;
      continue;
    }
    if (flag === "--whatif-v2-dir") {
      if (current === null) throw new Error("--whatif-v2-dir の前に --kifu-dir が要る");
      if (value === undefined) throw new Error("--whatif-v2-dir に値が無い");
      current.whatifV2Dir = value;
      i += 2;
      continue;
    }
    if (flag === "--out") {
      if (value === undefined) throw new Error("--out に値が無い");
      out = value;
      i += 2;
      continue;
    }
    throw new Error(`知らない引数: ${flag}`);
  }
  return { groups, out };
}

// ---- patient JSON ----

interface PatientGameLike {
  no: number;
  id: string;
}

interface PatientLike {
  games: PatientGameLike[];
  time: { available: boolean; timeUpLosses: { gameNo: number }[] | null };
}

function readPatient(patientPath: string): PatientLike {
  return JSON.parse(readFileSync(path.resolve(patientPath), "utf-8")) as PatientLike;
}

// ---- whatif-v2 の position 行 ----

interface WhatifCandidateRow {
  side: WhatifSideRaw;
}

interface WhatifPositionRow {
  kind: "position";
  ply: number;
  candidates: WhatifCandidateRow[];
  actualSide: WhatifSideRaw;
  scenes: { fork: boolean };
}

function readJsonLines(filePath: string): Record<string, unknown>[] {
  const text = readFileSync(filePath, "utf-8");
  return text
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

function readWhatifPositions(whatifPath: string): TimeCauseWhatifPositionInput[] {
  const rows = readJsonLines(whatifPath);
  const positionRows = rows.filter((row) => row.kind === "position") as unknown as WhatifPositionRow[];
  const positions: TimeCauseWhatifPositionInput[] = [];
  for (const row of positionRows) {
    const top1 = row.candidates[0];
    if (top1 === undefined) continue; // 候補 0 件の局面(directAnswers.ts と同じ、計画に無い理論上の状態)
    positions.push({ ply: row.ply, fork: row.scenes.fork, top1Side: top1.side, actualSide: row.actualSide });
  }
  return positions;
}

// ---- 1 組ぶんの処理 ----

function processGroup(groupArgs: GroupArgs): GameTimeCause[] {
  const { kifuDir, patient: patientPath, timeLimitSec, whatifV2Dir } = groupArgs;
  if (patientPath === undefined) throw new Error(`--kifu-dir ${kifuDir} の組に --patient が無い`);
  if (timeLimitSec === undefined) throw new Error(`--kifu-dir ${kifuDir} の組に --time-limit-sec が無い`);

  const group = groupLabelOfTimeLimitSec(timeLimitSec);
  const patient = readPatient(patientPath);
  const gameNoById = new Map(patient.games.map((g) => [g.id, g.no]));
  const timeUpLossGameNos = new Set((patient.time.timeUpLosses ?? []).map((loss) => loss.gameNo));

  const kifuDirPath = path.resolve(kifuDir);
  const fixedFiles = readdirSync(kifuDirPath)
    .filter((name) => name.endsWith(".fixed.json"))
    .sort();
  if (fixedFiles.length === 0) throw new Error(`--kifu-dir に *.fixed.json が無い: ${kifuDirPath}`);

  const games: GameTimeCause[] = [];
  for (const name of fixedFiles) {
    const fixed = JSON.parse(readFileSync(path.join(kifuDirPath, name), "utf-8")) as TimeCauseFixedKifu;
    const gameNo = gameNoById.get(fixed.id);
    if (gameNo === undefined) continue; // --patient の games に無い局(この組の対象外)

    let whatifPositions: TimeCauseWhatifPositionInput[] | null = null;
    if (whatifV2Dir !== undefined) {
      const whatifPath = path.join(path.resolve(whatifV2Dir), `${fixed.id}.jsonl`);
      if (!existsSync(whatifPath)) throw new Error(`--whatif-v2-dir に ${fixed.id}.jsonl が無い: ${whatifPath}`);
      whatifPositions = readWhatifPositions(whatifPath);
    }

    games.push(buildGameTimeCause(fixed, gameNo, group, timeLimitSec, timeUpLossGameNos.has(gameNo), whatifPositions));
  }
  return games;
}

function main(): number {
  const args = process.argv.slice(2);
  let parsed: { groups: GroupArgs[]; out?: string };
  try {
    parsed = parseArgs(args);
  } catch (err) {
    console.error(err instanceof Error ? err.message : String(err));
    console.error(USAGE);
    return 1;
  }
  if (parsed.groups.length === 0 || parsed.out === undefined) {
    console.error(USAGE);
    return 1;
  }

  const games: GameTimeCause[] = [];
  for (const groupArgs of parsed.groups) games.push(...processGroup(groupArgs));

  const file = buildTimeCauseFile(games);
  const gitState = readGitState(REPO_ROOT);
  const out = { kind: "time_cause", gitHead: gitState.gitHead, dirty: gitState.dirty, ...file };

  const outPath = path.resolve(parsed.out);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(out, null, 2)}\n`, "utf-8");
  console.log(`書き込み: ${outPath}(組 ${file.groups.length} / 局 ${file.games.length})`);
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
