// STEP D-COST。scan-compare.ts の配線を見張る(docs/STEP_D-COST_PLAN_2026-09-15.md 7.1。diagnose.test.ts と同じ形)。
//
// - ソース照合 … 深い記録と軽い記録を取り違えずに渡し、規則と幅を渡して組み立て、描いた行を出していることを見る
//   (照合は片側にしか壊れない。文字列を残して意味を変える書き換えは捕まらない)
// - 子プロセス … scan-compare.ts を実際に走らせ、標準出力が、同じ記録をこの試験のプロセスで lib に掛けて描いたものと
//   全文一致することを確かめる。**エンジンは起動しない**(記録を読むだけ)
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(無視されるファイルも 1 本ずつ。node_modules だけを除く)が同じ。

import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import { DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./lib/failureEventFixtures.js";
import { buildScanReport, renderScanReport, type ScanPairInput } from "./lib/scanCompare.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const SCAN_COMPARE_TS = join(PLAYTEST_DIR, "scan-compare.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    [
      "status",
      "--porcelain",
      "-z",
      "--untracked-files=all",
      "--ignored",
      "--",
      ".",
      ":(exclude,glob)**/node_modules",
      ":(exclude,glob)**/node_modules/**",
    ],
    { cwd: REPO_ROOT },
  ).toString();

function recordsAt(plant: Record<number, PlantedEvaluation>, nodes: number, moves: readonly string[]): RecordLine[] {
  return plantedRecords(moves, plant).map((record): RecordLine =>
    record.engineReference ? { ...record, engineReference: { ...record.engineReference, nodes } } : record,
  );
}

describe("scan-compare.ts(計画 7.1)", () => {
  it("ソース照合: 深い記録を deep に、軽い記録を light に入れ、規則と幅を渡して組み立て、描いた行を出している", () => {
    const source = readFileSync(SCAN_COMPARE_TS, "utf8");
    expect(source).toContain("        deep: { ...deep, expectedNodes: deepNodes },\n");
    expect(source).toContain("        light: { ...readRecord(path.join(lightDir, name)), expectedNodes: lightNodes },\n");
    expect(source).toContain("      const deep = readRecord(path.join(deepDir, name));\n");
    expect(source).toContain("  const report = buildScanReport(inputs, DRAFT_RULE_1, NEAR_BAND_CP);\n");
    expect(source).toContain('  console.log(renderScanReport(report, { onlyDeep, onlyLight }).join("\\n"));\n');
    expect(source).toContain("const NEAR_BAND_CP = 100;\n");
  });

  it(
    "子プロセス: 深い・軽いのフォルダに掛けると exit 0 で、出力が同じ記録を lib に掛けて描いたものと一致する",
    () => {
      const moves = GAME01_MOVES.slice(0, 24);
      const meta = (kifuId: string, nodes: number) =>
        ({ kind: "meta", kifuId, startedAt: "t", gitHead: null, enginePath: "/e/nnue/YaneuraOu-by-gcc", nodes }) as MetaLine;
      const files = [
        {
          name: "g1.jsonl",
          deep: { meta: meta("g1", 4_000_000), records: recordsAt({ 4: engineRef(-500), 8: engineRef(-500) }, 4_000_000, moves) },
          light: { meta: meta("g1", 100_000), records: recordsAt({ 4: engineRef(-450), 8: engineRef(-300) }, 100_000, moves) },
        },
        {
          name: "g2.jsonl",
          deep: { meta: meta("g2", 4_000_000), records: recordsAt({ 12: engineRef(-500) }, 4_000_000, moves) },
          light: { meta: meta("g2", 100_000), records: recordsAt({ 12: null }, 100_000, moves) },
        },
      ];
      const dir = mkdtempSync(join(tmpdir(), "d-cost-scan-"));
      try {
        const deepDir = join(dir, "deep");
        const lightDir = join(dir, "light");
        mkdirSync(deepDir);
        mkdirSync(lightDir);
        const write = (filePath: string, side: { meta: MetaLine; records: RecordLine[] }) =>
          writeFileSync(filePath, `${[side.meta, ...side.records].map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
        for (const file of files) {
          write(join(deepDir, file.name), file.deep);
          write(join(lightDir, file.name), file.light);
        }
        write(join(deepDir, "only-deep.jsonl"), files[0]!.deep);

        const before = gitStatus();
        const stdout = execFileSync(
          "npx",
          ["tsx", SCAN_COMPARE_TS, "--deep", deepDir, "--deep-nodes", "4000000", "--light", lightDir, "--light-nodes", "100000"],
          { cwd: REPO_ROOT, encoding: "utf-8" },
        );
        expect(gitStatus()).toBe(before);

        // 同じ記録を、ファイルを経由した形(JSON に書いて読み直した形)でこのプロセスの lib に掛ける
        const inputs: ScanPairInput[] = files.map((file) => ({
          kifuId: file.deep.meta.kifuId,
          deep: { ...(JSON.parse(JSON.stringify(file.deep)) as { meta: MetaLine; records: RecordLine[] }), expectedNodes: 4_000_000 },
          light: { ...(JSON.parse(JSON.stringify(file.light)) as { meta: MetaLine; records: RecordLine[] }), expectedNodes: 100_000 },
        }));
        const report = buildScanReport(inputs, DRAFT_RULE_1, 100);
        expect(report.every((row) => row.kind === "counted")).toBe(true);
        expect(stdout).toBe(`${renderScanReport(report, { onlyDeep: ["only-deep.jsonl"], onlyLight: [] }).join("\n")}\n`);
        // 取り違えていないことを数でも見る(g1: 深い 2 件のうち 1 件拾えて 1 件取りこぼし / g2: 比べられなかった 1)
        expect(stdout).toContain("| 合計 | 3 | 1 | 1 | 1(notMeasurable 1) | 0 | 1/2(50.0%) | 0 |");
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    60_000,
  );
});
