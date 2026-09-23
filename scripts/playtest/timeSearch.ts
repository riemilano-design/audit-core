// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.2〜§7.5)。「1 手ごとの特徴の表」を発見用・
// 検証用に分けて組み、単独・2・3 条件の組を探索する CLI。**エンジンは呼ばない**(固定棋譜の
// `moveSeconds`・段 2 の記録(replay.ts → rescreen.ts の JSONL)・whatif-v2(STEP WHATIF 作業 4)の jsonl を
// 読むだけ)。
//
// 使い方(--role の直後の --kifu-dir で 1 つの組が始まる。組は役割ごとに複数渡せる):
//   npx tsx scripts/playtest/timeSearch.ts \
//     --role discover --kifu-dir <固定棋譜のフォルダ> --records-dir <段 2 の JSONL のフォルダ> \
//       --time-limit-sec <秒> [--whatif-v2-dir <whatif-v2 jsonl のフォルダ>] \
//     [--role discover|validate --kifu-dir <フォルダ> --records-dir <フォルダ> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] …] \
//     [--outcomes longThink,collapse,decisionGap] \
//     --out <time_cause_search.json>
//
// 【この CLI は薄くしてある】特徴の表は lib/timeFeatures.ts、探索は lib/timeSearch.ts にあり、そちらに試験がある。
// ここでやるのは、引数の解釈・ファイルを読む・局ごとに呼ぶ・書く、だけ。
//
// 【STEP CAUSE-SEARCH-1(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §11.1 の 5.)が足したこと】`--outcomes`
// (既定は 3 つ全部)。`lib/timeSearch.ts` の `searchOf` は常に 3 つのアウトカムを計算するが、この CLI は
// `--outcomes` で指定した鍵だけを出力 JSON の `searches` に残す(指定外の鍵は `searches` に入れない)。
//
// 【組(--kifu-dir で始まるブロック)の決め方】scripts/playtest/timeCause.ts と同じ形式
// (「--kifu-dir が出るたびに新しい組を始め、次の --kifu-dir〈または --out〉までの間のフラグをその組のものとして
// 読む」)に、役割(--role discover|validate)を足しただけ。同じ役割の組は複数渡せる(行を合算する)。
//
// 【局の選び方】`--kifu-dir` の `*.fixed.json` をすべて対象にする(timeCause.ts と違い `--patient` を
// 取らない ― この CLI は gameNo・timeUpLoss を使わないため。実装担当の判断)。`gameNo` はソート順の連番
// (1 始まり)。`--records-dir` の `<id>.jsonl` が無ければ止める(記録が要る前提。timeCause.ts の
// `--whatif-v2-dir` と同じ考え方)。
//
// 【このファイルが絶対にやらないこと】将棋の判断・評価・閾値・文言。名前・/Users/ を含む絶対パスを出力へ書くこと。
// 新しい閾値を置くこと(すべて lib/timeFeatures.ts・lib/timeSearch.ts・lib/reportData.ts の既存の値を使い回す)。

import { existsSync, readdirSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readGitState } from "./lib/gitState.js";
import { buildGameMoveFeatureRows, type MoveFeatureRow, type MoveFeatureWhatifPosition } from "./lib/timeFeatures.js";
import { OUTCOMES, searchOf, type OutcomeKey } from "./lib/timeSearch.js";
import type { RecordLine } from "./invariants/types.js";
import type { TimeCauseFixedKifu } from "./lib/timeCause.js";
import type { WhatifSideRaw } from "./lib/type.js";

const REPO_ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const USAGE =
  "使い方: npx tsx scripts/playtest/timeSearch.ts --role <discover|validate> --kifu-dir <フォルダ> --records-dir <フォルダ> --time-limit-sec <秒> [--whatif-v2-dir <フォルダ>] [--role … …] [--outcomes longThink,collapse,decisionGap] --out <time_cause_search.json>";

// ---- 引数の解釈(--kifu-dir で組が始まる。--role はその組の役割) ----

type Role = "discover" | "validate";

interface GroupArgs {
  kifuDir: string;
  role?: Role;
  recordsDir?: string;
  timeLimitSec?: number;
  whatifV2Dir?: string;
}

function parseArgs(args: readonly string[]): { groups: GroupArgs[]; out?: string; outcomes?: string } {
  const groups: GroupArgs[] = [];
  let current: GroupArgs | null = null;
  let pendingRole: Role | undefined;
  let out: string | undefined;
  let outcomes: string | undefined;
  let i = 0;
  while (i < args.length) {
    const flag = args[i];
    const value = args[i + 1];
    if (flag === "--role") {
      if (value !== "discover" && value !== "validate") throw new Error(`--role は discover か validate(${String(value)})`);
      pendingRole = value;
      i += 2;
      continue;
    }
    if (flag === "--kifu-dir") {
      if (value === undefined) throw new Error("--kifu-dir に値が無い");
      if (pendingRole === undefined) throw new Error("--kifu-dir の前に --role が要る");
      current = { kifuDir: value, role: pendingRole };
      groups.push(current);
      i += 2;
      continue;
    }
    if (flag === "--records-dir") {
      if (current === null) throw new Error("--records-dir の前に --kifu-dir が要る");
      if (value === undefined) throw new Error("--records-dir に値が無い");
      current.recordsDir = value;
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
    if (flag === "--outcomes") {
      if (value === undefined) throw new Error("--outcomes に値が無い");
      outcomes = value;
      i += 2;
      continue;
    }
    throw new Error(`知らない引数: ${flag}`);
  }
  return { groups, out, outcomes };
}

/** STEP CAUSE-SEARCH-1(計画 §11.1 の 5.)。`--outcomes` をアウトカムの鍵の配列にする(既定は 3 つ全部)。 */
function parseOutcomes(raw: string | undefined): OutcomeKey[] {
  if (raw === undefined) return [...OUTCOMES];
  const parts = raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
  if (parts.length === 0) throw new Error("--outcomes に値が無い");
  for (const part of parts) {
    if (!(OUTCOMES as readonly string[]).includes(part)) throw new Error(`--outcomes に知らないアウトカム: ${part}(${OUTCOMES.join("|")} のどれか)`);
  }
  return parts as OutcomeKey[];
}

// ---- 段 2 の記録(meta 行 + record 行) ----

function readJsonLines(filePath: string): Array<Record<string, unknown>> {
  return readFileSync(filePath, "utf-8")
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as Record<string, unknown>);
}

function readRecords(recordsPath: string): RecordLine[] {
  return readJsonLines(recordsPath).filter((line) => line["kind"] === "record") as unknown as RecordLine[];
}

// ---- whatif-v2 の position 行 ----

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
  const rows = readJsonLines(whatifPath).filter((row) => row["kind"] === "position") as unknown as WhatifPositionRow[];
  const positions: MoveFeatureWhatifPosition[] = [];
  for (const row of rows) {
    const top1 = row.candidates[0];
    if (top1 === undefined) continue; // 候補 0 件の局面(timeCause.ts と同じ、計画に無い理論上の状態)
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

// ---- 1 組ぶんの処理 ----

function processGroup(groupArgs: GroupArgs): MoveFeatureRow[] {
  const { kifuDir, role, recordsDir, timeLimitSec, whatifV2Dir } = groupArgs;
  if (role === undefined) throw new Error(`--kifu-dir ${kifuDir} の組に --role が無い`);
  if (recordsDir === undefined) throw new Error(`--kifu-dir ${kifuDir} の組に --records-dir が無い`);

  const kifuDirPath = path.resolve(kifuDir);
  const fixedFiles = readdirSync(kifuDirPath)
    .filter((name) => name.endsWith(".fixed.json"))
    .sort();
  if (fixedFiles.length === 0) throw new Error(`--kifu-dir に *.fixed.json が無い: ${kifuDirPath}`);

  const rows: MoveFeatureRow[] = [];
  fixedFiles.forEach((name, index) => {
    const fixed = JSON.parse(readFileSync(path.join(kifuDirPath, name), "utf-8")) as TimeCauseFixedKifu;
    const gameNo = index + 1;

    const recordsPath = path.join(path.resolve(recordsDir), `${fixed.id}.jsonl`);
    if (!existsSync(recordsPath)) throw new Error(`--records-dir に ${fixed.id}.jsonl が無い: ${recordsPath}`);
    const records = readRecords(recordsPath);

    let whatifPositions: MoveFeatureWhatifPosition[] | null = null;
    if (whatifV2Dir !== undefined) {
      const whatifPath = path.join(path.resolve(whatifV2Dir), `${fixed.id}.jsonl`);
      if (!existsSync(whatifPath)) throw new Error(`--whatif-v2-dir に ${fixed.id}.jsonl が無い: ${whatifPath}`);
      whatifPositions = readWhatifPositions(whatifPath);
    }

    rows.push(...buildGameMoveFeatureRows(fixed, gameNo, role, timeLimitSec, records, whatifPositions));
  });
  return rows;
}

function main(): number {
  const args = process.argv.slice(2);
  let parsed: { groups: GroupArgs[]; out?: string; outcomes?: string };
  let outcomes: OutcomeKey[];
  try {
    parsed = parseArgs(args);
    outcomes = parseOutcomes(parsed.outcomes);
  } catch (err) {
    console.error(err instanceof Error ? err.message : String(err));
    console.error(USAGE);
    return 1;
  }
  if (parsed.groups.length === 0 || parsed.out === undefined) {
    console.error(USAGE);
    return 1;
  }

  const discoverRows: MoveFeatureRow[] = [];
  const validateRows: MoveFeatureRow[] = [];
  for (const groupArgs of parsed.groups) {
    const rows = processGroup(groupArgs);
    (groupArgs.role === "discover" ? discoverRows : validateRows).push(...rows);
  }
  if (discoverRows.length === 0) throw new Error("--role discover の組が無い(発見用の手が 0 件)");
  if (validateRows.length === 0) throw new Error("--role validate の組が無い(検証用の手が 0 件)");

  const result = searchOf(discoverRows, validateRows);
  // STEP CAUSE-SEARCH-1(計画 §11.1 の 5.)。`--outcomes` で指定した鍵だけを出力の `searches` に残す
  // (`searchOf` 自体は常に 3 つとも計算する ― lib の役目を増やさない)。
  const searches: Partial<Record<OutcomeKey, unknown>> = {};
  for (const key of outcomes) searches[key] = result.searches[key];

  const gitState = readGitState(REPO_ROOT);
  const out = { kind: "time_cause_search", gitHead: gitState.gitHead, dirty: gitState.dirty, ...result, searches };

  const outPath = path.resolve(parsed.out);
  mkdirSync(path.dirname(outPath), { recursive: true });
  writeFileSync(outPath, `${JSON.stringify(out, null, 2)}\n`, "utf-8");
  console.log(
    `書き込み: ${outPath}(発見用 ${discoverRows.length} 手・検証用 ${validateRows.length} 手・深さごとの再現: ${result.depths.map((d) => `${d.depth}=${d.reproduced}/${d.adopted}`).join(" ")}・アウトカム: ${outcomes.join(",")})`,
  );
  return 0;
}

try {
  process.exit(main());
} catch (err) {
  console.error(err instanceof Error ? `${err.name}: ${err.message}` : String(err));
  process.exit(1);
}
