// STEP T-5(T5-A: 比較の道具)。docs/STEP_T-5_PLAN_2026-09-11.md 2. T5-A、
// docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.1(揺れの観測)に従う。
//
// 複数のJSONL(replay.ts/explore.tsが保存したもの)を読み、実行のたびに変わる値
// (record行のelapsedMs、meta行のstartedAt/gitHead/enginePath、summary行の
// totalMs/readyMsPerPly)を除いて正規化し、1本目(baseline)を基準に他のファイルと
// 比較する。出力はMarkdown(標準出力)と--json。
//
// 使い方: npx tsx scripts/playtest/compare.ts <a.jsonl> <b.jsonl> [...] [--json <out.json>]
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・評価・閾値・文言。
// - 一致/不一致の良し悪しを判定すること(観測であり、常にexit 0)。
// - replay.ts/explore.ts/recorder.tsの変更・複製。

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/** JSONLの1行分(kindと任意のフィールド)。中身の型はここでは定義せず、
 * check.tsのように本番のStateResponseBodyWithPlan型へは依存しない
 * (行同士の構造比較だけを行うため)。 */
export type JsonlLine = Record<string, unknown> & { kind: string };

const RECORD_EXCLUDED_KEYS = ["elapsedMs"];
const META_EXCLUDED_KEYS = ["startedAt", "gitHead", "enginePath"];
const SUMMARY_EXCLUDED_KEYS = ["totalMs", "readyMsPerPly"];

function omitKeys(line: JsonlLine, keys: string[]): JsonlLine {
  const result: JsonlLine = { ...line };
  for (const key of keys) delete result[key];
  return result;
}

/** 1行を正規化する(実行のたびに変わる値を除く)。除外するフィールドはkindごとに
 * 決まっている(STEP T-5計画書2. T5-A)。record/meta/summary以外のkind
 * (error/end等)はそのまま返す。 */
export function normalizeLine(line: JsonlLine): JsonlLine {
  switch (line.kind) {
    case "record":
      return omitKeys(line, RECORD_EXCLUDED_KEYS);
    case "meta":
      return omitKeys(line, META_EXCLUDED_KEYS);
    case "summary":
      return omitKeys(line, SUMMARY_EXCLUDED_KEYS);
    default:
      return line;
  }
}

/** JSONL全文を行ごとに読み、正規化した行の配列を返す。 */
export function normalizeJsonl(raw: string): JsonlLine[] {
  return raw
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
    .map((l) => JSON.parse(l) as JsonlLine)
    .map(normalizeLine);
}

/** 差分パスを何件まで報告するかの上限(観測を読みやすい分量に収めるための
 * 実装上の判断であり、将棋の判断・閾値ではない)。 */
export const MAX_DIFF_PATHS_PER_LINE = 5;

/** 2つの値を再帰的に比較し、異なっていた場所をドット/角括弧表記のパスとして
 * 最大limit件まで収集する純粋関数。プリミティブの型・値の不一致、オブジェクトと
 * 配列の食い違いをそれぞれ1件のパスとして数える。 */
export function diffPaths(a: unknown, b: unknown, limit: number = MAX_DIFF_PATHS_PER_LINE, prefix = ""): string[] {
  if (limit <= 0) return [];
  if (a === b) return [];

  const isObjA = a !== null && typeof a === "object";
  const isObjB = b !== null && typeof b === "object";
  if (!isObjA || !isObjB) {
    return [prefix || "(root)"];
  }

  const arrA = Array.isArray(a);
  const arrB = Array.isArray(b);
  if (arrA !== arrB) {
    return [prefix || "(root)"];
  }

  const paths: string[] = [];

  if (arrA && arrB) {
    const len = Math.max(a.length, b.length);
    for (let i = 0; i < len && paths.length < limit; i++) {
      paths.push(...diffPaths(a[i], b[i], limit - paths.length, `${prefix}[${i}]`));
    }
    return paths.slice(0, limit);
  }

  const objA = a as Record<string, unknown>;
  const objB = b as Record<string, unknown>;
  const keys = Array.from(new Set([...Object.keys(objA), ...Object.keys(objB)])).sort();
  for (const key of keys) {
    if (paths.length >= limit) break;
    const nextPrefix = prefix ? `${prefix}.${key}` : key;
    paths.push(...diffPaths(objA[key], objB[key], limit - paths.length, nextPrefix));
  }
  return paths.slice(0, limit);
}

/** 1行分の差分(baselineとの比較結果)。 */
export interface LineDiff {
  index: number;
  ply: number | null;
  phase: string | null;
  paths: string[];
}

/** 差分がある行を何件まで報告するかの上限(実装上の判断)。 */
export const MAX_DIFFERING_LINES = 10;

/** baseline(正規化済み)とtarget(正規化済み)を比較した結果。 */
export interface FileCompareResult {
  filePath: string;
  matches: boolean;
  baselineLineCount: number;
  fileLineCount: number;
  diffs: LineDiff[];
}

/** 正規化済みの2本を比較する純粋関数。行数が異なる場合はmin(件数)まで
 * 突き合わせたうえでmatches: falseとする(一致でも不一致でも判断はしない。観測)。 */
export function compareNormalizedLines(
  baselineLines: JsonlLine[],
  targetLines: JsonlLine[],
  filePath: string,
): FileCompareResult {
  const lineCountMismatch = baselineLines.length !== targetLines.length;
  const len = Math.min(baselineLines.length, targetLines.length);
  const diffs: LineDiff[] = [];

  for (let i = 0; i < len; i++) {
    const a = baselineLines[i] as JsonlLine;
    const b = targetLines[i] as JsonlLine;
    const paths = diffPaths(a, b);
    if (paths.length > 0) {
      const ply = typeof a.ply === "number" ? a.ply : typeof b.ply === "number" ? b.ply : null;
      const phase = typeof a.phase === "string" ? a.phase : typeof b.phase === "string" ? b.phase : null;
      diffs.push({ index: i, ply, phase, paths });
      if (diffs.length >= MAX_DIFFERING_LINES) break;
    }
  }

  return {
    filePath,
    matches: !lineCountMismatch && diffs.length === 0,
    baselineLineCount: baselineLines.length,
    fileLineCount: targetLines.length,
    diffs,
  };
}

export interface CompareReport {
  inputs: string[];
  baseline: string;
  matchedCount: number;
  comparedCount: number;
  results: FileCompareResult[];
}

function buildReport(files: string[]): CompareReport {
  const baselinePath = files[0] as string;
  const baselineLines = normalizeJsonl(readFileSync(path.resolve(baselinePath), "utf-8"));

  const results: FileCompareResult[] = [];
  for (let i = 1; i < files.length; i++) {
    const filePath = files[i] as string;
    const targetLines = normalizeJsonl(readFileSync(path.resolve(filePath), "utf-8"));
    results.push(compareNormalizedLines(baselineLines, targetLines, filePath));
  }

  return {
    inputs: files,
    baseline: baselinePath,
    matchedCount: results.filter((r) => r.matches).length,
    comparedCount: results.length,
    results,
  };
}

function renderMarkdown(report: CompareReport): string {
  const lines: string[] = [];

  lines.push("# 対局記録の比較(揺れの観測)");
  lines.push("");
  lines.push("## 入力");
  for (const f of report.inputs) {
    lines.push(`- ${f}${f === report.baseline ? "(基準)" : ""}`);
  }
  lines.push("");

  lines.push(`## 一致した本数: ${report.matchedCount} / ${report.comparedCount}(基準を除く)`);
  lines.push("");

  if (report.results.length === 0) {
    lines.push("比較対象がありません(入力が1本のみ)。");
    lines.push("");
  } else {
    for (const result of report.results) {
      lines.push(`### ${result.filePath}`);
      lines.push("");
      if (result.matches) {
        lines.push("基準と正規化後に完全一致しました。");
      } else {
        if (result.baselineLineCount !== result.fileLineCount) {
          lines.push(`行数が異なります(基準: ${result.baselineLineCount} 行 / 対象: ${result.fileLineCount} 行)。`);
        }
        if (result.diffs.length > 0) {
          lines.push(`差があった行(最大 ${MAX_DIFFERING_LINES} 件):`);
          for (const diff of result.diffs) {
            lines.push(
              `- index: ${diff.index} / ply: ${diff.ply ?? "不明"} / phase: ${diff.phase ?? "不明"} / 差分パス(最大 ${MAX_DIFF_PATHS_PER_LINE} 件): ${diff.paths.join(", ")}`,
            );
          }
        }
      }
      lines.push("");
    }
  }

  lines.push("---");
  lines.push("");
  lines.push("観測であり、判断はしない。一致でも不一致でも異常とは呼ばない(docs/AGENT_PROTOCOL.md 11.)。");
  lines.push("");

  return lines.join("\n");
}

function main(): void {
  const argv = process.argv.slice(2);
  const jsonIndex = argv.indexOf("--json");
  const jsonOut = jsonIndex !== -1 ? argv[jsonIndex + 1] : undefined;
  const files = (jsonIndex !== -1 ? argv.slice(0, jsonIndex) : argv).filter((a) => a.length > 0);

  if (files.length === 0) {
    console.error(
      "使い方: npx tsx scripts/playtest/compare.ts <a.jsonl> <b.jsonl> [...] [--json <out.json>]",
    );
    process.exit(0);
    return;
  }

  const report = buildReport(files);
  console.log(renderMarkdown(report));

  if (jsonOut) {
    writeFileSync(path.resolve(jsonOut), `${JSON.stringify(report, null, 2)}\n`, "utf-8");
  }

  process.exit(0);
}

// compare.test.tsが純粋関数(normalizeLine/diffPaths/compareNormalizedLines等)を
// importする際にmain()が実行されない(process.exitが呼ばれない)よう、CLIとして
// 直接実行された場合だけmain()を呼ぶ(check.tsには無いテスト由来の追加。
// check.tsは同種のテストを持たないため、ここでのみ必要になったガード)。
const isMainModule = process.argv[1] !== undefined && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isMainModule) {
  main();
}
