// STEP WHATIF 作業 2(docs/STEP_WHATIF_PLAN_2026-09-22.md §2.3・§7.3)。`--whatif` かつ `--until pdf` のときに
// 本編 PDF の後で作る付録 2(分かれ道)の段の試験。**既存の scripts/playtest/lib/pipeline.test.ts・
// lib/pipelineReport.test.ts・lib/pipelineWhatif.test.ts・lib/pipelineAbsolutePath.test.ts は 1 行も変えない**
// (別ファイルに分けた)。エンジンも子プロセスも起こさない(fs・道具の実行は注入した偽物)。
//
// 見張ること: `--whatif` かつ `--until pdf` のときだけこの段に入ること、本編 PDF(main.pdf)が無ければ
// whatif-report-data・report-pdf-render-whatif を一切呼ばずに失敗にすること、局ごとの whatif.jsonl が
// 1 つでも欠けていれば失敗にすること、whatif-report-data → report-pdf-render-whatif → report-pdf-check-fonts の順、
// 済みの飛ばし(whatif_report_data.json があれば呼ばない・whatif.pdf が新しければ render・check-fonts を呼ばない)、
// **`--whatif` を付けない実行は、この段の道具を一切呼ばないこと**。

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  gamePaths,
  gateOutPath,
  parsePipelineArgs,
  personWorkDir,
  reportPaths,
  runPipeline,
  whatifPath,
  whatifPdfDone,
  whatifReportDataCommand,
  whatifReportDataDone,
  type GameJob,
  type PipelineArgs,
  type PipelineFs,
  type ToolResult,
  type ToolRunner,
} from "./pipeline.js";

// ---- 偽の fs(既存の pipeline 試験ファイルと同じ作り) ----

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
    ensureDir: () => {
      /* このファイルの試験は呼び出し自体を見ない */
    },
    listFiles: (dirPath) => {
      const names = new Set<string>();
      for (const key of store.keys()) {
        if (path.dirname(key) === dirPath) names.add(path.basename(key));
      }
      return [...names];
    },
  };
}

const metaLine = (extra: Record<string, unknown> = {}): string => JSON.stringify({ kind: "meta", kifuId: "x", startedAt: "t", gitHead: null, enginePath: "/e", ...extra });
const validStage2 = (): string => `${metaLine()}\n${JSON.stringify({ kind: "record", ply: 0 })}\n`;
const validFixed = (id: string): string => JSON.stringify({ id, source: "s", moves: ["7g7f"] });
const validWhatifJsonl = (): string => `${metaLine()}\n${JSON.stringify({ kind: "position", ply: 17 })}\n${JSON.stringify({ kind: "summary", positionsRead: 1 })}\n`;

const senteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });

const report = { name: "たろうさん", title: "対局後診断", today: "2026-09-21" };

const baseArgs = (overrides: Partial<PipelineArgs> = {}): PipelineArgs =>
  ({
    person: "p1",
    kifuDir: "/k",
    work: "/w",
    me: undefined,
    parallel: 5,
    compareDirs: [],
    comparePerson: undefined,
    until: "pdf" as const,
    evaluator: undefined,
    dryRun: false,
    report,
    ...overrides,
  }) as PipelineArgs;

/** g1 が本編 PDF(main.pdf)まで済んでいる状態の偽 fs(このファイルの主眼は付録 2 なので、それより前は「済み」にする)。 */
function makeDoneThroughMainPdfFs(extra: Record<string, string> = {}): ReturnType<typeof makeFakeFs> {
  const personDir = personWorkDir("/w", "p1");
  const gp = gamePaths(personDir, "g1");
  const rp = reportPaths("/w");
  return makeFakeFs({
    [gp.fixedKifuPath]: validFixed("g1"),
    [gp.stage1Path]: `${metaLine()}\n${JSON.stringify({ kind: "summary" })}\n`,
    [gp.stage2Path]: validStage2(),
    [path.join(personDir, "diagnose", "events.jsonl")]: "e",
    [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
    [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
    [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
    [gateOutPath(personDir)]: `${JSON.stringify({ contract: "diagnosis-gate" })}\n`,
    [rp.patient]: "{}",
    [rp.audit]: "{}",
    [rp.sfens]: "{}",
    [rp.prose]: "{}",
    [rp.mainPdf]: "%PDF-1.4 main",
    [whatifPath(personDir, "g1")]: validWhatifJsonl(),
    ...extra,
  });
}

function makeRunner(handlers: Partial<Record<string, (args: readonly string[]) => ToolResult>>, calls: Array<{ tool: string; args: string[] }>): ToolRunner {
  return async (tool, args): Promise<ToolResult> => {
    calls.push({ tool, args: [...args] });
    const handler = handlers[tool];
    if (handler !== undefined) return handler(args);
    // report-pdf-build・report-pdf-render-main・report-pdf-check-fonts(本編)は常に成功させ、付録 2 だけに焦点を絞る
    return { code: 0, stdout: "", stderr: "" };
  };
}

// ---- whatifReportDataCommand(純粋関数) ----

describe("whatifReportDataCommand", () => {
  it("--whatif <files…> --patient <path> --out <path>", () => {
    expect(whatifReportDataCommand(["/w/p1/whatif/g1.jsonl", "/w/p1/whatif/g2.jsonl"], "/w/report/patient_report_data.json", "/w/report/whatif_report_data.json")).toStrictEqual([
      "--whatif",
      "/w/p1/whatif/g1.jsonl",
      "/w/p1/whatif/g2.jsonl",
      "--patient",
      "/w/report/patient_report_data.json",
      "--out",
      "/w/report/whatif_report_data.json",
    ]);
  });
});

// ---- whatifReportDataDone・whatifPdfDone(済みの判定) ----

describe("whatifReportDataDone・whatifPdfDone", () => {
  it("whatifReportDataDone: 無い・空白だけは false", () => {
    expect(whatifReportDataDone(undefined)).toBe(false);
    expect(whatifReportDataDone("  \n")).toBe(false);
    expect(whatifReportDataDone("{}")).toBe(true);
  });

  it("whatifPdfDone: PDF が whatif_report_data.json より新しいときだけ true", () => {
    const mtimes: Record<string, number> = { "/pdf": 300, "/data": 100 };
    const mtimeMs = (p: string): number | undefined => mtimes[p];
    expect(whatifPdfDone(mtimeMs, "/pdf", "/data")).toBe(true);
    expect(whatifPdfDone((p) => (p === "/pdf" ? 50 : mtimes[p]), "/pdf", "/data")).toBe(false);
    expect(whatifPdfDone((p) => (p === "/pdf" ? undefined : mtimes[p]), "/pdf", "/data")).toBe(false);
  });
});

// ---- runPipeline: --whatif かつ --until pdf ----

describe("runPipeline: --whatif かつ --until pdf(本編の後に付録 2)", () => {
  it("whatif-report-data → report-pdf-render-whatif → report-pdf-check-fonts の順に呼ぶ", async () => {
    const fs = makeDoneThroughMainPdfFs();
    const rp = reportPaths("/w");
    const personDir = personWorkDir("/w", "p1");
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner(
      {
        "whatif-report-data": (args) => {
          const outIndex = args.indexOf("--out");
          fs.writeText(args[outIndex + 1]!, "{}");
          return { code: 0, stdout: "", stderr: "" };
        },
      },
      calls,
    );
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runner);
    const whatifCalls = calls.filter((c) => c.tool === "whatif-report-data" || c.tool === "report-pdf-render-whatif" || c.tool === "report-pdf-check-fonts");
    // report-pdf-check-fonts は本編(main.pdf)向けにも 1 回呼ばれるので、付録向け呼び出しは末尾の 1 回
    expect(whatifCalls.map((c) => c.tool)).toStrictEqual(["report-pdf-check-fonts", "whatif-report-data", "report-pdf-render-whatif", "report-pdf-check-fonts"]);
    expect(whatifCalls[1]!.args).toStrictEqual(["--whatif", whatifPath(personDir, "g1"), "--patient", rp.patient, "--out", rp.whatifData]);
    expect(whatifCalls[2]!.args).toStrictEqual([rp.dir, rp.whatifData, rp.whatifPdf]);
    expect(whatifCalls[3]!.args).toStrictEqual([rp.whatifPdf]);
    expect(result.failures).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });

  it("whatif_report_data.json がすでにあれば whatif-report-data を呼ばない(済みの飛ばし)", async () => {
    const rp = reportPaths("/w");
    const fs = makeDoneThroughMainPdfFs({ [rp.whatifData]: "{}" });
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "whatif-report-data")).toBe(false);
    expect(calls.some((c) => c.tool === "report-pdf-render-whatif")).toBe(true);
  });

  it("whatif.pdf が whatif_report_data.json より新しければ、render・check-fonts(付録向け)を呼ばない", async () => {
    const rp = reportPaths("/w");
    const fs = makeDoneThroughMainPdfFs({ [rp.whatifData]: "{}" }) as PipelineFs;
    fs.mtimeMs = (filePath: string): number | undefined => {
      if (filePath === rp.whatifPdf) return 300;
      if (filePath === rp.whatifData) return 100;
      return undefined;
    };
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "whatif-report-data")).toBe(false);
    expect(calls.some((c) => c.tool === "report-pdf-render-whatif")).toBe(false);
    expect(result.exitCode).toBe(0);
  });

  it("本編 PDF(main.pdf)が無ければ、付録 2 の道具を一切呼ばずに失敗にする", async () => {
    const personDir = personWorkDir("/w", "p1");
    const rp = reportPaths("/w");
    const gp = gamePaths(personDir, "g1");
    const fs = makeFakeFs({
      [gp.fixedKifuPath]: validFixed("g1"),
      [gp.stage1Path]: `${metaLine()}\n${JSON.stringify({ kind: "summary" })}\n`,
      [gp.stage2Path]: validStage2(),
      [path.join(personDir, "diagnose", "events.jsonl")]: "e",
      [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
      [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
      [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
      [gateOutPath(personDir)]: `${JSON.stringify({ contract: "diagnosis-gate" })}\n`,
      [rp.patient]: "{}",
      [rp.audit]: "{}",
      [rp.sfens]: "{}",
      [rp.prose]: "{}",
      // main.pdf を書かないランナー(render-main が失敗する体)
      [whatifPath(personDir, "g1")]: validWhatifJsonl(),
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner({ "report-pdf-render-main": () => ({ code: 1, stdout: "", stderr: "boom" }) }, calls);
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runner);
    expect(calls.some((c) => c.tool === "whatif-report-data" || c.tool === "report-pdf-render-whatif")).toBe(false);
    expect(result.failures.some((f) => f.stage === "whatif-pdf" && f.message.includes("main.pdf"))).toBe(true);
  });

  it("局ごとの whatif.jsonl が欠けていれば、付録 2 の道具を呼ばずに失敗にする", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = makeDoneThroughMainPdfFs();
    fs.store.delete(whatifPath(personDir, "g1")); // whatif.jsonl を消す
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "whatif-report-data" || c.tool === "report-pdf-render-whatif")).toBe(false);
    expect(result.failures.some((f) => f.stage === "whatif-pdf" && f.message.includes("g1"))).toBe(true);
  });

  it("render_whatif.py が失敗(rc≠0)すれば check-fonts(付録向け)を呼ばず、失敗にする", async () => {
    const fs = makeDoneThroughMainPdfFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner(
      {
        "whatif-report-data": (args) => {
          fs.writeText(args[args.indexOf("--out") + 1]!, "{}");
          return { code: 0, stdout: "", stderr: "" };
        },
        "report-pdf-render-whatif": () => ({ code: 1, stdout: "", stderr: "KeyError" }),
      },
      calls,
    );
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runner);
    const whatifCalls = calls.filter((c) => c.tool === "whatif-report-data" || c.tool === "report-pdf-render-whatif" || c.tool === "report-pdf-check-fonts");
    expect(whatifCalls.filter((c) => c.tool === "report-pdf-check-fonts")).toHaveLength(1); // 本編向けの 1 回だけ(付録向けは呼ばれない)
    expect(result.failures.some((f) => f.stage === "whatif-pdf")).toBe(true);
    expect(result.exitCode).toBe(1);
  });
});

// ---- --whatif を付けない実行は変わらない ----

describe("runPipeline: --whatif を付けない実行は、付録 2 の道具を一切呼ばない", () => {
  it("--until pdf でも whatif-report-data・report-pdf-render-whatif は 0 回", async () => {
    const fs = makeDoneThroughMainPdfFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs(), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "whatif-report-data" || c.tool === "report-pdf-render-whatif")).toBe(false);
    expect(result.failures.some((f) => f.stage === "whatif-pdf")).toBe(false);
  });
});
