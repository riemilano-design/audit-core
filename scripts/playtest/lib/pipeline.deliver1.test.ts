// STEP DELIVER-1(docs/STEP_DELIVER1_PLAN_2026-09-25.md §3 の 1・2)。lib/pipeline.ts に足した 2 つだけの試験。
// - §3 の 1: `--time-limit-sec`・`--previous` を S5(reportData.ts)へ**中継するだけ**
// - §3 の 2: READ 工程(`read.ts`)を `--whatif` の後ろに繋ぐ
//
// **既存の試験(pipeline.test.ts)は 1 行も触らない**(足した分だけをここで見張る)。
// エンジンも子プロセスも起こさない(fs・道具の実行はすべて注入した偽物)。

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  parsePipelineArgs,
  personWorkDir,
  readCommand,
  readPath,
  reportDataCommand,
  runPipeline,
  whatifPath,
  type GameJob,
  type PipelineArgs,
  type PipelineFs,
  type ToolName,
  type ToolResult,
} from "./pipeline.js";

// ---- 偽の fs / 道具(pipeline.test.ts と同じ流儀) ----

function makeFakeFs(initial: Record<string, string> = {}): PipelineFs & { store: Map<string, string>; ensureDirCalls: string[] } {
  const store = new Map<string, string>(Object.entries(initial));
  const ensureDirCalls: string[] = [];
  return {
    store,
    ensureDirCalls,
    readText: (filePath) => store.get(filePath),
    writeText: (filePath, content) => {
      store.set(filePath, content);
    },
    appendText: (filePath, content) => {
      store.set(filePath, (store.get(filePath) ?? "") + content);
    },
    ensureDir: (dirPath) => {
      ensureDirCalls.push(dirPath);
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

const validFixed = (id: string): string => JSON.stringify({ id, source: "s", moves: ["7g7f", "3c3d"] });
const metaLine = JSON.stringify({ kind: "meta", kifuId: "x", startedAt: "t", gitHead: null, enginePath: "/e" });
const withSummary = `${metaLine}\n${JSON.stringify({ kind: "summary", plies: 1 })}\n`;
const senteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });

const BASE: PipelineArgs = {
  person: "p1",
  kifuDir: "/k",
  work: "/w",
  me: undefined,
  parallel: 5,
  compareDirs: [],
  comparePerson: undefined,
  until: "diagnose",
  evaluator: undefined,
  dryRun: false,
};

/** 局ごとに、段 1・段 2・whatif-v2 まで済んでいる状態の fs(READ だけが残る)。 */
function fsWithWhatifDone(ids: readonly string[]): ReturnType<typeof makeFakeFs> {
  const personDir = personWorkDir("/w", "p1");
  const initial: Record<string, string> = {
    [path.join(personDir, "diagnose", "events.jsonl")]: "x",
    [path.join(personDir, "diagnose", "rise.jsonl")]: "x",
    [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "x",
    [path.join(personDir, "diagnose", "diagnose.md")]: "x",
  };
  for (const id of ids) {
    initial[path.join(personDir, "kifu", `${id}.fixed.json`)] = validFixed(id);
    initial[path.join(personDir, "stage1", `${id}.jsonl`)] = withSummary;
    initial[path.join(personDir, "stage2", `${id}.jsonl`)] = `${metaLine}\n`;
    initial[whatifPath(personDir, id, 2)] = withSummary;
  }
  return makeFakeFs(initial);
}

/** read.ts が呼ばれたら出力を書く道具(それ以外は何もしない)。 */
function runnerWritingRead(fs: PipelineFs, calls: { tool: ToolName; args: string[] }[]): (tool: ToolName, args: readonly string[]) => Promise<ToolResult> {
  return async (tool, args) => {
    calls.push({ tool, args: [...args] });
    if (tool === "read") {
      const outIndex = args.indexOf("--out");
      fs.writeText(args[outIndex + 1]!, withSummary);
    }
    return { code: 0, stdout: "", stderr: "" };
  };
}

// ---- §3 の 1: --time-limit-sec・--previous の中継 ----

describe("parsePipelineArgs: --time-limit-sec・--previous(STEP DELIVER-1)", () => {
  it("渡さなければキー自体が付かない(既存の toStrictEqual の試験を壊さないため)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect("timeLimitSec" in args).toBe(false);
    expect("previous" in args).toBe(false);
  });

  it("渡せば読める(--previous は絶対パスになる)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--time-limit-sec", "180", "--previous", "/p/report/patient_report_data.json"]);
    expect(args.timeLimitSec).toBe(180);
    expect(args.previous).toBe("/p/report/patient_report_data.json");
    expect(path.isAbsolute(args.previous!)).toBe(true);
  });

  it("--time-limit-sec は正の整数だけ(新しい既定値は作らない)", () => {
    for (const bad of ["0", "-1", "abc", "1.5"]) {
      expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--time-limit-sec", bad])).toThrow();
    }
  });
});

describe("reportDataCommand: 中継は末尾に、渡されたときだけ(STEP DELIVER-1)", () => {
  const call = (relay?: { timeLimitSec?: number; previous?: string }): string[] =>
    reportDataCommand("p1", { name: "名", title: "題", today: "2026-09-24" }, ["/s2.jsonl"], ["/k.fixed.json"], "/g.jsonl", "/patient.json", "/audit.json", "/sfens.json", "/pr.md", relay);

  it("渡さなければ今までと 1 バイトも変わらない(末尾は --out-prose-request)", () => {
    const flags = call();
    expect(flags.slice(-2)).toStrictEqual(["--out-prose-request", "/pr.md"]);
    expect(flags).not.toContain("--time-limit-sec");
    expect(flags).not.toContain("--previous");
    // 既定(relay を省略)と空の relay で同じ
    expect(call({})).toStrictEqual(flags);
  });

  it("渡せば末尾に --time-limit-sec → --previous の順で足す", () => {
    expect(call({ timeLimitSec: 600, previous: "/prev.json" }).slice(-4)).toStrictEqual(["--time-limit-sec", "600", "--previous", "/prev.json"]);
  });

  it("片方だけでも足せる", () => {
    expect(call({ timeLimitSec: 180 }).slice(-2)).toStrictEqual(["--time-limit-sec", "180"]);
    expect(call({ previous: "/prev.json" }).slice(-2)).toStrictEqual(["--previous", "/prev.json"]);
  });
});

// ---- §3 の 2: READ 工程 ----

describe("readPath・readCommand(STEP DELIVER-1)", () => {
  it("出力先は <personDir>/read/<id>.jsonl", () => {
    expect(readPath("/w/p1", "g1")).toBe("/w/p1/read/g1.jsonl");
  });

  it("引数は --whatif → --kifu → --out(--threads は渡さない)", () => {
    expect(readCommand("/w/p1/whatif-v2/g1.jsonl", "/w/p1/kifu/g1.fixed.json", "/w/p1/read/g1.jsonl")).toStrictEqual([
      "--whatif",
      "/w/p1/whatif-v2/g1.jsonl",
      "--kifu",
      "/w/p1/kifu/g1.fixed.json",
      "--out",
      "/w/p1/read/g1.jsonl",
    ]);
  });
});

describe("runPipeline: READ 工程(STEP DELIVER-1)", () => {
  it("--whatif が無ければ read は 1 度も呼ばれない", async () => {
    const fs = fsWithWhatifDone(["g1"]);
    const calls: { tool: ToolName; args: string[] }[] = [];
    await runPipeline(BASE, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    expect(calls.map((c) => c.tool)).not.toContain("read");
  });

  it("--whatif(v2)なら whatif の後ろに局ごとに read を呼ぶ", async () => {
    const fs = fsWithWhatifDone(["g1", "g2"]);
    const calls: { tool: ToolName; args: string[] }[] = [];
    const result = await runPipeline({ ...BASE, whatif: true }, [senteJob("g1"), senteJob("g2")], fs, runnerWritingRead(fs, calls));
    expect(result.failures).toStrictEqual([]);
    const readCalls = calls.filter((c) => c.tool === "read");
    expect(readCalls).toHaveLength(2);
    const personDir = personWorkDir("/w", "p1");
    expect(readCalls[0]!.args).toStrictEqual(readCommand(whatifPath(personDir, "g1", 2), path.join(personDir, "kifu", "g1.fixed.json"), readPath(personDir, "g1")));
    expect(fs.store.has(readPath(personDir, "g1"))).toBe(true);
    expect(fs.store.has(readPath(personDir, "g2"))).toBe(true);
  });

  it("whatif の段より後ろに来る(順序)", async () => {
    const personDir = personWorkDir("/w", "p1");
    // whatif-v2 をまだ作っていない状態にして、whatif → read の順を見る
    const fs = fsWithWhatifDone(["g1"]);
    fs.store.delete(whatifPath(personDir, "g1", 2));
    const calls: { tool: ToolName; args: string[] }[] = [];
    const runner = async (tool: ToolName, args: readonly string[]): Promise<ToolResult> => {
      calls.push({ tool, args: [...args] });
      const outIndex = args.indexOf("--out");
      if (tool === "whatif" || tool === "read") fs.writeText(args[outIndex + 1]!, withSummary);
      return { code: 0, stdout: "", stderr: "" };
    };
    await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runner);
    const tools = calls.map((c) => c.tool);
    expect(tools.indexOf("whatif")).toBeGreaterThanOrEqual(0);
    expect(tools.indexOf("read")).toBeGreaterThan(tools.indexOf("whatif"));
  });

  it("read が済んでいれば飛ばす(最後の行が summary)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = fsWithWhatifDone(["g1"]);
    fs.store.set(readPath(personDir, "g1"), withSummary);
    const calls: { tool: ToolName; args: string[] }[] = [];
    await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    expect(calls.filter((c) => c.tool === "read")).toHaveLength(0);
  });

  it("summary で終わっていない read は済みとみなさない(やり直す)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = fsWithWhatifDone(["g1"]);
    fs.store.set(readPath(personDir, "g1"), `${metaLine}\n`);
    const calls: { tool: ToolName; args: string[] }[] = [];
    await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    expect(calls.filter((c) => c.tool === "read")).toHaveLength(1);
  });

  it("--side-version 1(v1)では read を回さない(whatif-v2 が無いため)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = fsWithWhatifDone(["g1"]);
    fs.store.set(whatifPath(personDir, "g1", 1), withSummary);
    const calls: { tool: ToolName; args: string[] }[] = [];
    await runPipeline({ ...BASE, whatif: true, whatifSideVersion: 1 }, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    expect(calls.filter((c) => c.tool === "read")).toHaveLength(0);
  });

  it("timing.jsonl の行に stage: \"read\" が付く", async () => {
    const fs = fsWithWhatifDone(["g1"]);
    const calls: { tool: ToolName; args: string[] }[] = [];
    const result = await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    const stages = result.timingLines.map((line) => (JSON.parse(line) as { stage?: string }).stage);
    expect(stages).toContain("read");
    expect(stages).toContain("whatif");
  });

  it("read.ts が出力を書かなければ失敗として記録する", async () => {
    const fs = fsWithWhatifDone(["g1"]);
    const calls: { tool: ToolName; args: string[] }[] = [];
    const runner = async (tool: ToolName, args: readonly string[]): Promise<ToolResult> => {
      calls.push({ tool, args: [...args] });
      return { code: 3, stdout: "", stderr: "" }; // 何も書かない
    };
    const result = await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runner);
    expect(result.failures.some((f) => f.stage === "read")).toBe(true);
    expect(result.exitCode).not.toBe(0);
  });

  it("read/ のフォルダを作る", async () => {
    const fs = fsWithWhatifDone(["g1"]);
    const calls: { tool: ToolName; args: string[] }[] = [];
    await runPipeline({ ...BASE, whatif: true }, [senteJob("g1")], fs, runnerWritingRead(fs, calls));
    expect(fs.ensureDirCalls).toContain(path.join(personWorkDir("/w", "p1"), "read"));
  });
});
