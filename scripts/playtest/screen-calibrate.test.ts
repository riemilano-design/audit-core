// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §5)。screen-calibrate.ts と measure-twice.ts の配線を見張る(scan-compare.test.ts と同じ形)。
//
// - ソース照合 … 相手と段 2 を取り違えずに lib に渡し、描いた行を出していること。measure-twice.ts は測る行をエンジンを起こす前に決め、
//   1 行につき同じエンジンで 2 回続けて測り、Threads 1 であること(照合は片側にしか壊れない)
// - 子プロセス … screen-calibrate.ts を実際に走らせ、標準出力が、同じ記録をこの試験のプロセスで lib に掛けて描いたものと全文一致すること。
//   measure-twice.ts は**エンジンを起こさずに止まる経路だけ**(引数の誤り・無い ply・--out が入力と同じ)
//
// 【静かにスキップしない】npx・tsx・git が無ければ execFileSync が例外を投げて赤になる。
// 【一時ディレクトリ以外に書かない】走らせる前と後で git status(node_modules だけを除く)が同じ。

import { execFileSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { MetaLine, RecordLine } from "./invariants/types.js";
import { DRAFT_RULE_1 } from "./lib/failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./lib/failureEventFixtures.js";
import { compareDeepRows, compareRescreenRuns, compareWithStage2, renderScreenCalibration } from "./lib/screenCalibration.js";

const PLAYTEST_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(PLAYTEST_DIR, "..", "..");
const SCREEN_CALIBRATE_TS = join(PLAYTEST_DIR, "screen-calibrate.ts");
const MEASURE_TWICE_TS = join(PLAYTEST_DIR, "measure-twice.ts");

const gitStatus = (): string =>
  execFileSync(
    "git",
    ["status", "--porcelain", "-z", "--untracked-files=all", "--ignored", "--", ".", ":(exclude,glob)**/node_modules", ":(exclude,glob)**/node_modules/**"],
    { cwd: REPO_ROOT },
  ).toString();

function run(script: string, args: string[]): { status: number; stdout: string; stderr: string } {
  try {
    const stdout = execFileSync("npx", ["tsx", script, ...args], { cwd: REPO_ROOT, encoding: "utf-8", stdio: ["ignore", "pipe", "pipe"] });
    return { status: 0, stdout, stderr: "" };
  } catch (error) {
    const failure = error as { status: number | null; stdout: string; stderr: string };
    return { status: failure.status ?? -1, stdout: String(failure.stdout), stderr: String(failure.stderr) };
  }
}

const jsonl = (lines: unknown[]): string => `${lines.map((line) => JSON.stringify(line)).join("\n")}\n`;

describe("screen-calibrate.ts・measure-twice.ts(計画 §5・§11)", () => {
  it("ソース照合: screen-calibrate.ts は相手を base、段 2 を stage2 として lib に渡し、描いた行を出す", () => {
    const source = readFileSync(SCREEN_CALIBRATE_TS, "utf8");
    expect(source).toContain("        return { kind: \"counted\", comparison: compareWithStage2(kifuId, base, stage2, DRAFT_RULE_1), deepRows: compareDeepRows(stage2.records, base.records) };\n");
    expect(source).toContain('      const base = parseRecord(readFileSync(path.join(baseDir, name), "utf-8"));\n');
    expect(source).toContain('      const stage2 = parseRecord(readFileSync(path.join(stage2Dir, name), "utf-8"));\n');
    expect(source).toContain('      return { kifuId: parseRecord(first).meta?.kifuId ?? name, comparison: compareRescreenRuns(first, readFileSync(path.join(repeatDir!, name), "utf-8")) };\n');
    expect(source).toContain("    renderScreenCalibration(rows, runs, {\n");
  });

  it("ソース照合: measure-twice.ts はエンジンを起こす前に測る行を決め、1 行につき同じエンジンで続けて 2 回測り、Threads 1 で比べを書く", () => {
    const source = readFileSync(MEASURE_TWICE_TS, "utf8");
    expect(source).toContain("  const plan = planMeasureTwice(kifuId, { meta, records }, DRAFT_RULE_1, plies);\n");
    expect(source.indexOf("planMeasureTwice(kifuId")).toBeLessThan(source.indexOf("rawEngine.start();"));
    expect(source).toContain(
      "      const first = await measureEngineReference(sfen, engine, nodes);\n      const second = await measureEngineReference(sfen, engine, nodes);\n      const comparison = compareMeasurementPair(first, second);\n",
    );
    expect(source).toContain("const THREADS = 1;\n");
    expect(source).toContain("    rawEngine.setThreads(THREADS);\n");
    expect(source).toContain('    writeFileSync(outPath, `${out.join("\\n")}\\n`, "utf-8");\n');
    expect(source).toContain("  if (inputPath === outPath) throw new Error(");
  });

  it(
    "子プロセス: screen-calibrate.ts の標準出力は、同じ記録を lib に掛けて描いたものと全文一致し、片方にしか無い記録と 2 回の rescreen の節を出す。引数が足りなければ exit 1",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d-screen-2-calibrate-"));
      try {
        const before = gitStatus();
        const baseDir = join(dir, "base");
        const stage2Dir = join(dir, "stage2");
        const repeatDir = join(dir, "repeat");
        for (const d of [baseDir, stage2Dir, repeatDir]) mkdirSync(d);
        const meta = { kind: "meta", kifuId: "cal-cli", startedAt: "t", gitHead: null, enginePath: "/e", searchMode: "nodes", nodes: 4_000_000, threads: 1 };
        const baseRecords = plantedRecords(GAME01_MOVES, { 20: engineRef(0), 22: engineRef(-500) }).map((record): RecordLine => ({ ...record, searchPvs: [] }));
        const stage2Records = plantedRecords(GAME01_MOVES, { 20: engineRef(0), 22: engineRef(-396) }).map((record): RecordLine => {
          const out: RecordLine = { ...record, ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: 400_000 } } : {}), searchPvs: [] };
          if (record.ply === 20 || record.ply === 22) {
            out.engineReferenceDeep = { ...engineRef(record.ply === 22 ? -508 : 0), nodes: 4_000_000 };
            out.searchPvsDeep = [];
          }
          return out;
        });
        const screen = {
          lightNodes: 400_000,
          deepNodes: 4_000_000,
          rule: { dropCp: -300, advantageCp: 300, advantageDropCp: -200, before: 1, after: 2 },
          deepPlies: [20, 22],
          sourceSha256: "a".repeat(64),
          deepRun: { gitHead: null, dirty: null, enginePath: "/e", threads: 1, startedAt: "t2", order: "plyAscending", measuredOrder: [20, 22] },
        };
        const stage2Meta = { ...meta, nodes: 400_000, referenceNodes: 400_000, screen };
        writeFileSync(join(baseDir, "k.jsonl"), jsonl([meta, ...baseRecords]), "utf-8");
        writeFileSync(join(baseDir, "only-base.jsonl"), jsonl([meta]), "utf-8");
        writeFileSync(join(stage2Dir, "k.jsonl"), jsonl([stage2Meta, ...stage2Records]), "utf-8");
        cpSync(join(stage2Dir, "k.jsonl"), join(repeatDir, "k.jsonl"));

        const result = run(SCREEN_CALIBRATE_TS, ["--base", baseDir, "--stage2", stage2Dir, "--stage2-repeat", repeatDir]);
        expect(result.status).toBe(0);
        const base = { meta: meta as unknown as MetaLine, records: baseRecords };
        const stage2 = { meta: stage2Meta as unknown as MetaLine, records: stage2Records };
        const stage2Text = readFileSync(join(stage2Dir, "k.jsonl"), "utf-8");
        const expected = renderScreenCalibration(
          [{ kind: "counted", comparison: compareWithStage2("cal-cli", base, stage2, DRAFT_RULE_1), deepRows: compareDeepRows(stage2.records, base.records) }],
          [{ kifuId: "cal-cli", comparison: compareRescreenRuns(stage2Text, stage2Text) }],
          { onlyBase: ["only-base.jsonl"], onlyStage2: [] },
        );
        expect(result.stdout).toBe(`${expected.join("\n")}\n`);
        expect(result.stdout).toContain("| cal-cli | 1 | 1 | 1 | 0 | 0 | 0/1 | 0 | 0 | 0/1 | 0 | 0 | 0 | 0 |");
        expect(result.stdout).toContain("- 相手にしか無い(段 2 は回していない): only-base.jsonl");

        const usage = run(SCREEN_CALIBRATE_TS, ["--base", baseDir]);
        expect(usage.status).toBe(1);
        expect(usage.stderr).toContain("使い方: npx tsx scripts/playtest/screen-calibrate.ts --base <dir> --stage2 <dir> [--stage2-repeat <dir>]");
        expect(gitStatus()).toBe(before);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );

  it(
    "子プロセス: measure-twice.ts は、引数の誤り・ready 行に無い ply・--out が入力と同じ、でエンジンを起こさずに exit 1 で止まり、書かない",
    () => {
      const dir = mkdtempSync(join(tmpdir(), "d-screen-2-measure-twice-"));
      try {
        const before = gitStatus();
        const record = join(dir, "k.jsonl");
        const text = jsonl([{ kind: "meta", kifuId: "twice", startedAt: "t", gitHead: null, enginePath: "/e" }, ...plantedRecords(GAME01_MOVES.slice(0, 4), {})]);
        writeFileSync(record, text, "utf-8");
        const out = join(dir, "out.jsonl");

        const usage = run(MEASURE_TWICE_TS, [record, "--out", out]);
        expect(usage.status).toBe(1);
        expect(usage.stderr).toContain("使い方: npx tsx scripts/playtest/measure-twice.ts <記録.jsonl> --nodes <N> --out <出力.jsonl> [--plies <ply,ply,...>]");

        const missing = run(MEASURE_TWICE_TS, [record, "--nodes", "4000000", "--out", out, "--plies", "2,99"]);
        expect(missing.status).toBe(1);
        expect(missing.stderr).toContain("Error: 記録 twice に ply 99 の ready 行が無い");
        expect(missing.stderr).not.toContain("測る行");

        const same = run(MEASURE_TWICE_TS, [record, "--nodes", "4000000", "--out", record]);
        expect(same.status).toBe(1);
        expect(same.stderr).toContain("Error: --out が入力と同じパス(記録のファイルは変えない)");
        expect(readFileSync(record, "utf-8")).toBe(text);
        expect(existsSync(out)).toBe(false);
        expect(gitStatus()).toBe(before);
      } finally {
        rmSync(dir, { recursive: true, force: true });
      }
    },
    120_000,
  );
});
