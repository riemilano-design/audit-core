// STEP PIPE 作業 C(docs/STEP_PIPE_PLAN_2026-09-21.md §2.2 の最後・§3 (a))。lib/pipeline.ts に足した
// report-data・prose・pdf の 3 段の試験。**エンジンも python も起こさない**(fs・道具の実行はすべて注入した偽物)。
//
// 既存の lib/pipeline.test.ts(S1〜S4)は一切変えていない(このファイルは別ファイルとして追加)。
//
// 見張ること: --until に report-data・prose・pdf が増えたこと(既定の "gate" は変わらない)、--name・--title・--today が
// report-data 以降でだけ必須なこと、report-data 段の向き(材料 = このお客さんの段 2・--kifu・--gate)、gate.jsonl が
// 無ければ「判定の出力が要る」とはっきり失敗にすること、prose.json が無ければ pdf 段(python)を一切起こさないこと、
// pdf 段が build → render-main → check-fonts の順で呼ばれ、render-main が失敗すれば check-fonts を呼ばないこと、
// pdf の「済み」が mtimeMs で判定されること。

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  frontPdfDone,
  PipelineArgError,
  REPORT_STAGES,
  UNTIL_STAGES,
  gamePaths,
  gateOutPath,
  parsePipelineArgs,
  pdfDone,
  personWorkDir,
  proseDone,
  reportDataCommand,
  reportDataDone,
  reportPaths,
  runPipeline,
  type GameJob,
  type PipelineFs,
  type ReportInfo,
  type ToolResult,
  type ToolRunner,
} from "./pipeline.js";

// ---- 偽の fs(lib/pipeline.test.ts の makeFakeFs と同じ作り) ----

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
      /* 何もしない(このファイルでは呼ばれたかどうかを見ない) */
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

const senteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });

/** g1 が段 2(gate まで)を済ませた状態の偽 fs を作る(このファイルの主眼は report-data・prose・pdf なので、
 * それより前の段はあらかじめ「済み」にして焦点を絞る)。 */
function makeDoneThroughGateFs(extra: Record<string, string> = {}): ReturnType<typeof makeFakeFs> {
  const personDir = personWorkDir("/w", "p1");
  const gp = gamePaths(personDir, "g1");
  return makeFakeFs({
    [gp.fixedKifuPath]: validFixed("g1"),
    [gp.stage1Path]: `${metaLine()}\n${JSON.stringify({ kind: "summary" })}\n`,
    [gp.stage2Path]: validStage2(),
    [path.join(personDir, "diagnose", "events.jsonl")]: "e",
    [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
    [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
    [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
    [gateOutPath(personDir)]: `${JSON.stringify({ contract: "diagnosis-gate" })}\n`,
    ...extra,
  });
}

const report: ReportInfo = { name: "たろうさん", title: "対局後診断", today: "2026-09-21" };

const baseArgs = (overrides: Partial<Parameters<typeof runPipeline>[0]> = {}) =>
  ({
    person: "p1",
    kifuDir: "/k",
    work: "/w",
    me: undefined,
    parallel: 5,
    compareDirs: [],
    comparePerson: undefined,
    until: "gate" as const,
    evaluator: undefined,
    dryRun: false,
    ...overrides,
  }) satisfies Parameters<typeof runPipeline>[0];

function makeRunner(handlers: Partial<Record<string, (args: readonly string[]) => ToolResult>>, calls: Array<{ tool: string; args: string[] }>): ToolRunner {
  return async (tool, args): Promise<ToolResult> => {
    calls.push({ tool, args: [...args] });
    const handler = handlers[tool];
    if (handler !== undefined) return handler(args);
    return { code: 0, stdout: "", stderr: "" };
  };
}

// ---- --until・--name/--title/--today ----

describe("parsePipelineArgs: --until に report-data・prose・pdf を足す", () => {
  it("UNTIL_STAGES は STAGES の後ろに report-data・prose・pdf(この順)", () => {
    expect(UNTIL_STAGES).toStrictEqual(["import", "evaluate", "diagnose", "gate", "report-data", "prose", "pdf"]);
    expect(REPORT_STAGES).toStrictEqual(["report-data", "prose", "pdf"]);
  });

  it("--until report-data・prose・pdf を受け付ける(既存の 4 段に加えて)", () => {
    for (const until of REPORT_STAGES) {
      const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", until, "--name", "N", "--title", "T", "--today", "2026-09-21"]);
      expect(args.until).toBe(until);
    }
  });

  it("--until が report-data・prose・pdf のとき、--name・--title・--today が無ければ止まる(推測しない)", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", "report-data"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", "prose", "--name", "N"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", "pdf", "--name", "N", "--title", "T"])).toThrow(PipelineArgError);
  });

  it("--until が gate(既定)のときは --name・--title・--today が無くても止まらない(既存の動きのまま)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect(args.until).toBe("gate");
    expect(args.report).toBeUndefined();
  });

  it("--name・--title・--today を 3 つとも渡せば report が付く(--until に関わらず)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--name", "たろうさん", "--title", "対局後診断", "--today", "2026-09-21"]);
    expect(args.report).toStrictEqual({ name: "たろうさん", title: "対局後診断", today: "2026-09-21" });
    expect(args.until).toBe("gate");
  });

  it("--until は依然として知らない値なら止まる", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", "report"])).toThrow(PipelineArgError);
  });
});

// ---- reportDataCommand ----

describe("reportDataCommand", () => {
  it("reportData.ts の使い方どおりの並び", () => {
    expect(reportDataCommand("p1", report, ["/w/p1/stage2/g1.jsonl"], ["/w/p1/kifu/g1.fixed.json"], "/w/p1/gate.jsonl", "/w/report/patient_report_data.json", "/w/report/audit_metrics.json", "/w/report/sfens.json", "/w/report/prose-request.md")).toStrictEqual([
      "--person",
      "p1",
      "--name",
      "たろうさん",
      "--title",
      "対局後診断",
      "--today",
      "2026-09-21",
      "--records",
      "/w/p1/stage2/g1.jsonl",
      "--kifu",
      "/w/p1/kifu/g1.fixed.json",
      "--gate",
      "/w/p1/gate.jsonl",
      "--out-patient",
      "/w/report/patient_report_data.json",
      "--out-audit",
      "/w/report/audit_metrics.json",
      "--out-sfens",
      "/w/report/sfens.json",
      "--out-prose-request",
      "/w/report/prose-request.md",
    ]);
  });
});

// ---- 段ごとの「済み」の判定 ----

describe("reportDataDone / proseDone / pdfDone", () => {
  it("reportDataDone: 3 つとも非空でなければ false", () => {
    expect(reportDataDone(undefined, "a", "b")).toBe(false);
    expect(reportDataDone("a", "", "b")).toBe(false);
    expect(reportDataDone("a", "b", "c")).toBe(true);
  });

  it("proseDone: 無い・空白だけは false", () => {
    expect(proseDone(undefined)).toBe(false);
    expect(proseDone("  \n")).toBe(false);
    expect(proseDone("{}")).toBe(true);
  });

  it("pdfDone: PDF が prose・patient の両方より新しいときだけ true", () => {
    const mtimes: Record<string, number> = { "/pdf": 300, "/prose": 100, "/patient": 200 };
    const mtimeMs = (p: string): number | undefined => mtimes[p];
    expect(pdfDone(mtimeMs, "/pdf", "/prose", "/patient")).toBe(true);
    expect(pdfDone(mtimeMs, "/pdf", "/patient", "/prose")).toBe(true); // 引数の順を変えても中身は同じ3値
    expect(pdfDone((p) => (p === "/pdf" ? 50 : mtimes[p]), "/pdf", "/prose", "/patient")).toBe(false); // pdf の方が古い
    expect(pdfDone((p) => (p === "/pdf" ? undefined : mtimes[p]), "/pdf", "/prose", "/patient")).toBe(false); // pdf が無い
  });
});

// ---- runPipeline: report-data 段 ----

describe("runPipeline: report-data 段", () => {
  it("gate.jsonl・段2・--name/--title/--today が揃っていれば report-data を呼び、材料=このお客さんの段2・--kifu・--gate を渡す", async () => {
    const fs = makeDoneThroughGateFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const rp = reportPaths("/w");
    const runner = makeRunner(
      {
        "report-data": (args) => {
          const patientOut = args[args.indexOf("--out-patient") + 1]!;
          const auditOut = args[args.indexOf("--out-audit") + 1]!;
          const sfensOut = args[args.indexOf("--out-sfens") + 1]!;
          fs.writeText(patientOut, "{}");
          fs.writeText(auditOut, "{}");
          fs.writeText(sfensOut, "{}");
          return { code: 0, stdout: "", stderr: "" };
        },
      },
      calls,
    );
    const result = await runPipeline(baseArgs({ until: "report-data", report }), [senteJob("g1")], fs, runner);
    expect(calls.map((c) => c.tool)).toStrictEqual(["report-data"]);
    const call = calls[0]!;
    const gp = gamePaths(personWorkDir("/w", "p1"), "g1");
    expect(call.args.slice(0, 8)).toStrictEqual(["--person", "p1", "--name", "たろうさん", "--title", "対局後診断", "--today", "2026-09-21"]);
    expect(call.args.slice(call.args.indexOf("--records") + 1, call.args.indexOf("--kifu"))).toStrictEqual([gp.stage2Path]);
    expect(call.args.slice(call.args.indexOf("--kifu") + 1, call.args.indexOf("--gate"))).toStrictEqual([gp.fixedKifuPath]);
    expect(call.args[call.args.indexOf("--gate") + 1]).toBe(gateOutPath(personWorkDir("/w", "p1")));
    expect(call.args[call.args.indexOf("--out-patient") + 1]).toBe(rp.patient);
    expect(call.args[call.args.indexOf("--out-audit") + 1]).toBe(rp.audit);
    expect(call.args[call.args.indexOf("--out-sfens") + 1]).toBe(rp.sfens);
    expect(call.args[call.args.indexOf("--out-prose-request") + 1]).toBe(rp.proseRequest);
    expect(result.exitCode).toBe(0);
  });

  it("すでに patient/audit/sfens が揃っていれば report-data を呼ばない(済みの飛ばし)", async () => {
    const rp = reportPaths("/w");
    const fs = makeDoneThroughGateFs({ [rp.patient]: "{}", [rp.audit]: "{}", [rp.sfens]: "{}" });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "report-data", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });

  it("gate.jsonl が無ければ(--compare-dir 無し)、report-data を呼ばずに『判定の出力が要る』とはっきり失敗にする", async () => {
    const personDir = personWorkDir("/w", "p1");
    const gp = gamePaths(personDir, "g1");
    const fs = makeFakeFs({
      [gp.fixedKifuPath]: validFixed("g1"),
      [gp.stage1Path]: `${metaLine()}\n${JSON.stringify({ kind: "summary" })}\n`,
      [gp.stage2Path]: validStage2(),
      [path.join(personDir, "diagnose", "events.jsonl")]: "e",
      [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
      [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
      [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
      // gate.jsonl は置かない
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "report-data", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "report-data")).toBe(false);
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.stage === "report-data" && f.message.includes("gate.jsonl") && f.message.includes("判定の出力"))).toBe(true);
  });
});

// ---- runPipeline: prose 段(言い換えの自動化はしない) ----

describe("runPipeline: prose 段", () => {
  it("prose.json が無ければ、prose-request.md の場所を示して失敗にし、pdf 段(python)は一切起こさない", async () => {
    const rp = reportPaths("/w");
    const fs = makeDoneThroughGateFs({ [rp.patient]: "{}", [rp.audit]: "{}", [rp.sfens]: "{}" });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool.startsWith("report-pdf"))).toBe(false);
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.stage === "prose" && f.message.includes("prose-request.md") && f.message.includes("言い換え"))).toBe(true);
  });

  it("prose.json があれば失敗にしない(pdf 段へ進む)", async () => {
    const rp = reportPaths("/w");
    const fs = makeDoneThroughGateFs({ [rp.patient]: "{}", [rp.audit]: "{}", [rp.sfens]: "{}", [rp.prose]: "{}" });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(result.failures.some((f) => f.stage === "prose")).toBe(false);
    expect(calls.some((c) => c.tool === "report-pdf-build")).toBe(true);
  });
});

// ---- runPipeline: pdf 段(build → render-main → check-fonts の順、python) ----

describe("runPipeline: pdf 段", () => {
  function proseReadyFs(extra: Record<string, string> = {}): ReturnType<typeof makeFakeFs> {
    const rp = reportPaths("/w");
    return makeDoneThroughGateFs({ [rp.patient]: "{}", [rp.audit]: "{}", [rp.sfens]: "{}", [rp.prose]: "{}", ...extra });
  }

  it("front(render-front → check-fonts)の後、build → render-main → check-fonts の順に呼ぶ。render-main の引数は [REPORT_DATA_DIR, patient, 出力PDF]、check-fonts は [出力PDF]", async () => {
    const fs = proseReadyFs();
    const rp = reportPaths("/w");
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual([
      "report-pdf-render-front",
      "report-pdf-check-fonts",
      "report-pdf-build",
      "report-pdf-render-main",
      "report-pdf-check-fonts",
    ]);
    expect(calls[0]!.args).toStrictEqual([rp.patient, rp.frontPdf]);
    expect(calls[1]!.args).toStrictEqual([rp.frontPdf]);
    expect(calls[3]!.args).toStrictEqual([rp.dir, rp.patient, rp.mainPdf]);
    expect(calls[4]!.args).toStrictEqual([rp.mainPdf]);
    expect(result.exitCode).toBe(0);
  });

  it("render_main.py が失敗(rc≠0)すれば check_fonts_embedded.py を呼ばず、失敗にする(front.pdf は main.pdf と独立に作られる)", async () => {
    const fs = proseReadyFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner({ "report-pdf-render-main": () => ({ code: 1, stdout: "", stderr: "KeyError" }) }, calls);
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, runner);
    expect(calls.map((c) => c.tool)).toStrictEqual(["report-pdf-render-front", "report-pdf-check-fonts", "report-pdf-build", "report-pdf-render-main"]);
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.stage === "pdf")).toBe(true);
    expect(result.failures.some((f) => f.stage === "front-pdf")).toBe(false);
  });

  it("check_fonts_embedded.py が失敗(rc≠0)すれば失敗にする(埋め込まれていない書体)", async () => {
    const fs = proseReadyFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner({ "report-pdf-check-fonts": () => ({ code: 1, stdout: "", stderr: "not embedded" }) }, calls);
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, runner);
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.stage === "pdf" && f.message.includes("埋め込まれていない"))).toBe(true);
  });

  it("PDF が prose.json・patient_report_data.json より新しければ(mtimeMs)、build・render-main・check-fonts を一切呼ばない", async () => {
    const rp = reportPaths("/w");
    const fs = proseReadyFs() as PipelineFs;
    (fs as PipelineFs).mtimeMs = (filePath: string): number | undefined => {
      if (filePath === rp.mainPdf) return 300;
      if (filePath === rp.frontPdf) return 300;
      if (filePath === rp.prose) return 100;
      if (filePath === rp.patient) return 200;
      return undefined;
    };
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool.startsWith("report-pdf"))).toBe(false);
    expect(result.exitCode).toBe(0);
  });
});

// ---- runPipeline: front-pdf(本編 4 ページ。STEP TIME 作業 2、docs/STEP_TIME_PLAN_2026-09-22.md §6.4 の 3) ----

describe("runPipeline: front-pdf(main.pdf の前に描く。prose.json に依存しない)", () => {
  function proseReadyFs(extra: Record<string, string> = {}): ReturnType<typeof makeFakeFs> {
    const rp = reportPaths("/w");
    return makeDoneThroughGateFs({ [rp.patient]: "{}", [rp.audit]: "{}", [rp.sfens]: "{}", [rp.prose]: "{}", ...extra });
  }

  it("render_front.py の引数は [patient, 出力PDF]。render_front.py が失敗(rc≠0)すれば check-fonts を front.pdf には呼ばない(main.pdf の生成は続ける)", async () => {
    const fs = proseReadyFs();
    const rp = reportPaths("/w");
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner({ "report-pdf-render-front": () => ({ code: 1, stdout: "", stderr: "数の照合エラー" }) }, calls);
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, runner);
    expect(calls[0]).toStrictEqual({ tool: "report-pdf-render-front", args: [rp.patient, rp.frontPdf] });
    expect(calls.some((c) => c.tool === "report-pdf-build")).toBe(true); // main.pdf は front.pdf の失敗と独立に作られる
    expect(result.failures.some((f) => f.stage === "front-pdf" && f.message.includes("render_front.py"))).toBe(true);
    expect(result.exitCode).toBe(1);
  });

  it("front.pdf の check-fonts が失敗(rc≠0)すれば front-pdf 段の失敗にする", async () => {
    const fs = proseReadyFs();
    const rp = reportPaths("/w");
    const calls: Array<{ tool: string; args: string[] }> = [];
    const runner = makeRunner(
      {
        "report-pdf-check-fonts": (args) => (args[0] === rp.frontPdf ? { code: 1, stdout: "", stderr: "not embedded" } : { code: 0, stdout: "", stderr: "" }),
      },
      calls,
    );
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, runner);
    expect(result.failures.some((f) => f.stage === "front-pdf" && f.message.includes("埋め込まれていない"))).toBe(true);
    expect(result.exitCode).toBe(1);
  });

  it("frontPdfDone: front.pdf が patient_report_data.json より新しいときだけ true(prose.json は見ない)", () => {
    const mtimes: Record<string, number> = { "/front.pdf": 300, "/patient": 200 };
    const mtimeMs = (p: string): number | undefined => mtimes[p];
    expect(frontPdfDone(mtimeMs, "/front.pdf", "/patient")).toBe(true);
    expect(frontPdfDone((p) => (p === "/front.pdf" ? 50 : mtimes[p]), "/front.pdf", "/patient")).toBe(false);
    expect(frontPdfDone((p) => (p === "/front.pdf" ? undefined : mtimes[p]), "/front.pdf", "/patient")).toBe(false);
  });

  it("STEP TIME 作業 3: finding_texts.json があれば render_front.py の第 3 引数として渡す", async () => {
    const rp = reportPaths("/w");
    const fs = proseReadyFs({ [rp.findingTexts]: "{}" });
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls[0]).toStrictEqual({ tool: "report-pdf-render-front", args: [rp.patient, rp.frontPdf, rp.findingTexts] });
  });

  it("STEP TIME 作業 3: finding_texts.json が無ければ、従来どおり 2 引数のまま(古い work フォルダ等)", async () => {
    const rp = reportPaths("/w");
    const fs = proseReadyFs(); // rp.findingTexts を置かない
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls[0]).toStrictEqual({ tool: "report-pdf-render-front", args: [rp.patient, rp.frontPdf] });
  });

  it("front.pdf が patient_report_data.json より新しければ(mtimeMs)、render-front・その check-fonts を一切呼ばない(main.pdf の判定とは独立)", async () => {
    const rp = reportPaths("/w");
    const fs = proseReadyFs() as PipelineFs;
    (fs as PipelineFs).mtimeMs = (filePath: string): number | undefined => {
      if (filePath === rp.frontPdf) return 300;
      if (filePath === rp.patient) return 200;
      return undefined; // mainPdf・prose は無い(mtime 不明)ので main.pdf 側は動く
    };
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "pdf", report }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls.some((c) => c.tool === "report-pdf-render-front")).toBe(false);
    expect(calls.some((c) => c.tool === "report-pdf-build")).toBe(true); // main.pdf は別判定で動く
    expect(result.exitCode).toBe(0);
  });
});

// ---- --until gate(既定)は新しい道具を一切呼ばない(既存の動きのまま) ----

describe("runPipeline: --until gate(既定)は report-data・prose・pdf の道具を一切呼ばない", () => {
  it("gate まで済んでいても、report-data・report-pdf-* は 1 度も呼ばれない", async () => {
    const fs = makeDoneThroughGateFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "gate" }), [senteJob("g1")], fs, makeRunner({}, calls));
    expect(calls).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });
});
