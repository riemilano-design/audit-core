// STEP FILL 計画(docs/STEP_FILL_PLAN_2026-09-22.md §3)作業 Y、H3。
//
// `--work`・`--kifu-dir`・`--compare-dir` を相対パスで渡すと、S7(python・cwd = report-pdf/)へ
// REPORT_DATA_DIR として渡したときに report-pdf/ からの相対として解決され、正しいパスにならない
// (docs/STEP_PIPE_PLAN_2026-09-21.md §5.5 の 1)。受け取った時点(parsePipelineArgs)で絶対パスにする直し。
//
// **エンジンも python も起こさない**(既存の lib/pipeline.test.ts・lib/pipelineReport.test.ts と同じ流儀。
// fs・道具の実行はすべて注入した偽物)。既存の 2 ファイルは 1 文字も変えていない(別ファイルとして追加)。

import path from "node:path";
import { describe, expect, it } from "vitest";

import { gamePaths, parsePipelineArgs, personWorkDir, reportPaths, runPipeline, type GameJob, type PipelineFs, type ReportInfo, type ToolResult } from "./pipeline.js";

// ---- 偽の fs(既存の 2 ファイルと同じ作り) ----

function makeFakeFs(initial: Record<string, string> = {}): PipelineFs & { store: Map<string, string> } {
  const store = new Map<string, string>(Object.entries(initial));
  return {
    store,
    readText: (filePath) => store.get(filePath),
    writeText: (filePath, content) => {
      store.set(filePath, content);
    },
    appendText: (filePath, content) => {
      store.set(filePath, (store.get(filePath) ?? "") + content);
    },
    ensureDir: () => {},
    listFiles: (dirPath) => {
      const names = new Set<string>();
      for (const key of store.keys()) {
        if (path.dirname(key) === dirPath) names.add(path.basename(key));
      }
      return [...names];
    },
  };
}

const metaLine = (): string => JSON.stringify({ kind: "meta", kifuId: "x", startedAt: "t", gitHead: null, enginePath: "/e" });
const validStage2 = (): string => `${metaLine()}\n${JSON.stringify({ kind: "record", ply: 0 })}\n`;
const validFixed = (id: string): string => JSON.stringify({ id, source: "s", moves: ["7g7f"] });
const senteJob = (id: string, kifuDir: string): GameJob => ({ id, kifPath: `${kifuDir}/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });
const report: ReportInfo = { name: "たろうさん", title: "対局後診断", today: "2026-09-21" };

// ---- parsePipelineArgs: 相対パスを絶対パスにする ----

describe("parsePipelineArgs: --work・--kifu-dir・--compare-dir を受け取った時点で絶対パスにする(H3)", () => {
  it("相対パスは path.resolve(process.cwd() 基準) で絶対パスになる", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "rel/kifu", "--work", "rel/work"]);
    expect(path.isAbsolute(args.kifuDir)).toBe(true);
    expect(path.isAbsolute(args.work)).toBe(true);
    expect(args.kifuDir).toBe(path.resolve("rel/kifu"));
    expect(args.work).toBe(path.resolve("rel/work"));
  });

  it("すでに絶対パスなら値は変わらない(既存の試験がすべて絶対パスを渡している前提を壊さない)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect(args.kifuDir).toBe("/k");
    expect(args.work).toBe("/w");
  });

  it("--compare-dir も同じく絶対パスにする(複数値とも)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--compare-dir", "rel/c1", "rel/c2", "--compare-person", "p2"]);
    expect(args.compareDirs).toStrictEqual([path.resolve("rel/c1"), path.resolve("rel/c2")]);
  });

  it("--work の相対パスの違い(例: 末尾のスラッシュの有無)は、path.resolve で正規化された同じ絶対パスになる", () => {
    const a = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "rel/work"]);
    const b = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "rel/work/"]);
    expect(a.work).toBe(b.work);
  });
});

// ---- runPipeline: 相対パスの --work で S7(pdf 段)が正しい絶対パスで呼ばれる ----

describe("runPipeline: 相対パスの --work でも pdf 段(REPORT_DATA_DIR)が絶対パスで呼ばれる(H3)", () => {
  it("--work を相対パスで渡しても、report-pdf-render-main へ渡す REPORT_DATA_DIR(rp.dir)は絶対パス", async () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "rel/kifu", "--work", "rel/work", "--until", "pdf", "--name", "たろうさん", "--title", "対局後診断", "--today", "2026-09-21"]);
    // 相対パスのまま渡していれば、ここで絶対パスになっていることが直しの前提(直しが効いていなければこの assert 自体が落ちる)
    expect(path.isAbsolute(args.work)).toBe(true);

    const personDir = personWorkDir(args.work, "p1");
    const gp = gamePaths(personDir, "g1");
    const rp = reportPaths(args.work);
    const fs = makeFakeFs({
      [gp.fixedKifuPath]: validFixed("g1"),
      [gp.stage1Path]: `${metaLine()}\n${JSON.stringify({ kind: "summary" })}\n`,
      [gp.stage2Path]: validStage2(),
      [path.join(personDir, "diagnose", "events.jsonl")]: "e",
      [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
      [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
      [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
      [path.join(personDir, "gate.jsonl")]: `${JSON.stringify({ contract: "diagnosis-gate" })}\n`,
      [rp.patient]: "{}",
      [rp.audit]: "{}",
      [rp.sfens]: "{}",
      [rp.prose]: "{}",
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const run = async (tool: string, toolArgs: readonly string[]): Promise<ToolResult> => {
      calls.push({ tool, args: [...toolArgs] });
      return { code: 0, stdout: "", stderr: "" };
    };
    const result = await runPipeline(args, [senteJob("g1", args.kifuDir)], fs, run);
    expect(result.exitCode).toBe(0);
    const renderCall = calls.find((c) => c.tool === "report-pdf-render-main");
    expect(renderCall).toBeDefined();
    const [reportDataDir, patientPath, outPdfPath] = renderCall!.args;
    expect(path.isAbsolute(reportDataDir!)).toBe(true);
    expect(path.isAbsolute(patientPath!)).toBe(true);
    expect(path.isAbsolute(outPdfPath!)).toBe(true);
    expect(reportDataDir).toBe(rp.dir);
  });
});
