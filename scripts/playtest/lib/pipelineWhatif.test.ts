// STEP WHATIF 作業 1(docs/STEP_WHATIF_PLAN_2026-09-22.md)。`--whatif`(新しい任意の段)の試験。
// **既存の scripts/playtest/lib/pipeline.test.ts は 1 行も変えない**(別ファイルに分けた)。
// エンジンも子プロセスも起こさない(fs・道具の実行は注入した偽物。既存の pipeline.test.ts と同じ流儀)。
//
// 見張ること: `--whatif` を付けたときだけ diagnose の後に局ごとに whatif.ts を呼ぶこと、済みの飛ばし
// (最後の行が summary)、1 局の失敗で他を止めないこと、timing.jsonl に stage: "whatif" が残ること、
// **`--whatif` を付けない実行は、道具の呼び出し・timing.jsonl・失敗・exitCode のいずれも変わらないこと**。

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  gamePaths,
  gateOutPath,
  listGames,
  parsePipelineArgs,
  personWorkDir,
  PipelineArgError,
  runPipeline,
  timingPath,
  whatifCommand,
  whatifPath,
  type GameJob,
  type PipelineArgs,
  type PipelineFs,
  type ToolResult,
  type ToolRunner,
} from "./pipeline.js";

// ---- 偽の fs(pipeline.test.ts の makeFakeFs と同じ形。パス文字列をキーにした Map) ----

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
      // このファイルの試験は ensureDir の呼び出し自体を見張らない
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

const senteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });
const validFixed = (id: string): string => JSON.stringify({ id, source: "s", moves: ["7g7f", "3c3d"] });
const metaLine = (extra: Record<string, unknown> = {}): string => JSON.stringify({ kind: "meta", kifuId: "x", startedAt: "t", gitHead: null, enginePath: "/e", ...extra });
const validStage1 = (): string => `${metaLine()}\n${JSON.stringify({ kind: "summary", plies: 1, totalMs: 1, readyMsPerPly: [1] })}\n`;
const validStage2 = (): string => `${metaLine()}\n${JSON.stringify({ kind: "record", ply: 0 })}\n`;
const validDiagnose = (fs: ReturnType<typeof makeFakeFs>, personDir: string): void => {
  fs.writeText(path.join(personDir, "diagnose", "events.jsonl"), "e");
  fs.writeText(path.join(personDir, "diagnose", "rise.jsonl"), "r");
  fs.writeText(path.join(personDir, "diagnose", "maxdrop.jsonl"), "m");
  fs.writeText(path.join(personDir, "diagnose", "diagnose.md"), "# md");
};
/** whatif.ts の出力の形(最後の行が summary。他の段(replay.ts 等)と同じ済みの判定)。 */
const validWhatif = (): string => `${metaLine()}\n${JSON.stringify({ kind: "position", ply: 17 })}\n${JSON.stringify({ kind: "summary", positionsRead: 1 })}\n`;

const baseArgs = (overrides: Partial<PipelineArgs> = {}): PipelineArgs => ({
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
  ...overrides,
});

/** 段 1・段 2・診断がすべて済んでいる状態を作る(このファイルの試験は whatif の段だけを見るため)。 */
function readyFs(personDir: string, ids: readonly string[]): ReturnType<typeof makeFakeFs> {
  const initial: Record<string, string> = {};
  for (const id of ids) {
    const gp = gamePaths(personDir, id);
    initial[gp.fixedKifuPath] = validFixed(id);
    initial[gp.stage1Path] = validStage1();
    initial[gp.stage2Path] = validStage2();
  }
  const fs = makeFakeFs(initial);
  validDiagnose(fs, personDir);
  return fs;
}

function runnerOf(fs: ReturnType<typeof makeFakeFs>, calls: Array<{ tool: string; args: string[] }>, options: { failWhatifFor?: string } = {}): ToolRunner {
  return async (tool, args): Promise<ToolResult> => {
    calls.push({ tool, args: [...args] });
    if (tool === "diagnose") {
      const eventsIndex = args.indexOf("--events");
      const riseIndex = args.indexOf("--events-rise");
      const maxdropIndex = args.indexOf("--events-maxdrop");
      fs.writeText(args[eventsIndex + 1]!, "{}\n");
      fs.writeText(args[riseIndex + 1]!, "{}\n");
      fs.writeText(args[maxdropIndex + 1]!, "{}\n");
      return { code: 0, stdout: "# diagnose\n", stderr: "" };
    }
    if (tool === "whatif") {
      const outIndex = args.indexOf("--out");
      const outPath = args[outIndex + 1]!;
      const kifuPath = args[args.indexOf("--kifu") + 1]!;
      const id = (JSON.parse(fs.readText(kifuPath) ?? "{}") as { id?: string }).id;
      if (options.failWhatifFor !== undefined && id === options.failWhatifFor) {
        return { code: 1, stdout: "", stderr: "boom" };
      }
      fs.writeText(outPath, validWhatif());
      return { code: 0, stdout: "", stderr: "" };
    }
    return { code: 0, stdout: "", stderr: "" };
  };
}

// ---- parsePipelineArgs ----

describe("parsePipelineArgs: --whatif", () => {
  it("--whatif を渡すと args.whatif が true", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--whatif"]);
    expect(args.whatif).toBe(true);
  });

  it("--whatif を渡さなければ、whatif キー自体が無い(既存の toStrictEqual を壊さないため)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect(Object.hasOwn(args, "whatif")).toBe(false);
  });
});

describe("parsePipelineArgs: --side-version(STEP WHATIF 作業 4、計画 §9.3)", () => {
  it("--side-version 1 を渡すと args.whatifSideVersion が 1", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--whatif", "--side-version", "1"]);
    expect(args.whatifSideVersion).toBe(1);
  });

  it("--side-version 2 を渡すと args.whatifSideVersion が 2", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--whatif", "--side-version", "2"]);
    expect(args.whatifSideVersion).toBe(2);
  });

  it("--side-version を渡さなければ、whatifSideVersion キー自体が無い(既存の toStrictEqual を壊さないため)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect(Object.hasOwn(args, "whatifSideVersion")).toBe(false);
  });

  it("1・2 以外は止める(推測しない)", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--side-version", "3"])).toThrow(PipelineArgError);
  });
});

// ---- whatifCommand・whatifPath(純粋関数) ----

// STEP WHATIF 作業 4(計画 §9.3): sideVersion の既定は 2(v2)。既定では --side-version を渡さない
// (whatif.ts 自身の既定も v2 なので値を固定しない旗は渡さない)。フォルダも既定は whatif-v2/、
// sideVersion: 1 のときだけ従来どおり whatif/(v1 のフォルダ名は変えない)。
describe("whatifCommand・whatifPath", () => {
  it("whatifCommand は既定(v2)で --kifu と --out だけ(値を固定しない旗は渡さない)", () => {
    expect(whatifCommand("/f/g1.fixed.json", "/w/p1/whatif-v2/g1.jsonl")).toStrictEqual(["--kifu", "/f/g1.fixed.json", "--out", "/w/p1/whatif-v2/g1.jsonl"]);
  });

  it("whatifCommand は sideVersion: 1 のとき --side-version 1 を足す", () => {
    expect(whatifCommand("/f/g1.fixed.json", "/w/p1/whatif/g1.jsonl", 1)).toStrictEqual(["--kifu", "/f/g1.fixed.json", "--out", "/w/p1/whatif/g1.jsonl", "--side-version", "1"]);
  });

  it("whatifPath は既定(v2)で <person>/whatif-v2/<id>.jsonl", () => {
    expect(whatifPath("/w/p1", "g1")).toBe(path.join("/w/p1", "whatif-v2", "g1.jsonl"));
  });

  it("whatifPath は sideVersion: 1 のとき <person>/whatif/<id>.jsonl(v1 のフォルダ名は変えない)", () => {
    expect(whatifPath("/w/p1", "g1", 1)).toBe(path.join("/w/p1", "whatif", "g1.jsonl"));
  });
});

// ---- runPipeline: --whatif あり ----

describe("runPipeline: --whatif(diagnose の後に局ごとに呼ぶ)", () => {
  it("段が全部済んでいても、--whatif を付ければ局ごとに whatif.ts を呼ぶ", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1", "g2"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1"), senteJob("g2")];
    const result = await runPipeline(baseArgs({ whatif: true }), games, fs, runnerOf(fs, calls));
    expect(calls.filter((c) => c.tool === "whatif").map((c) => c.args[1])).toStrictEqual(
      [gamePaths(personDir, "g1").fixedKifuPath, gamePaths(personDir, "g2").fixedKifuPath].sort(),
    );
    expect(fs.readText(whatifPath(personDir, "g1"))).toBe(validWhatif());
    expect(fs.readText(whatifPath(personDir, "g2"))).toBe(validWhatif());
    expect(result.failures).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });

  it("STEP WHATIF 作業 4: 既定(whatifSideVersion 省略)は whatif-v2/ フォルダに書き、--side-version は渡さない", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runnerOf(fs, calls));
    const whatifCall = calls.find((c) => c.tool === "whatif")!;
    expect(whatifCall.args).toStrictEqual(["--kifu", gamePaths(personDir, "g1").fixedKifuPath, "--out", whatifPath(personDir, "g1", 2)]);
    expect(fs.readText(whatifPath(personDir, "g1", 2))).toBe(validWhatif());
    expect(fs.readText(whatifPath(personDir, "g1", 1))).toBeUndefined(); // v1 のフォルダには書かない
  });

  it("STEP WHATIF 作業 4: --side-version 1 は whatif/ フォルダに書き、whatif.ts へ --side-version 1 を渡す", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true, whatifSideVersion: 1 }), [senteJob("g1")], fs, runnerOf(fs, calls));
    const whatifCall = calls.find((c) => c.tool === "whatif")!;
    expect(whatifCall.args).toStrictEqual(["--kifu", gamePaths(personDir, "g1").fixedKifuPath, "--out", whatifPath(personDir, "g1", 1), "--side-version", "1"]);
    expect(fs.readText(whatifPath(personDir, "g1", 1))).toBe(validWhatif());
    expect(fs.readText(whatifPath(personDir, "g1", 2))).toBeUndefined(); // v2 のフォルダには書かない
  });

  it("すでに whatif の記録(最後の行が summary)があれば呼ばない(済みの飛ばし)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1"]);
    fs.writeText(whatifPath(personDir, "g1"), validWhatif());
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runnerOf(fs, calls));
    expect(calls.filter((c) => c.tool === "whatif")).toStrictEqual([]);
  });

  it("fixed 棋譜が無ければ、whatif.ts を呼ばずに失敗を記録する", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = makeFakeFs(); // fixed 棋譜すら無い
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ whatif: true, until: "import" }), [senteJob("g1")], fs, runnerOf(fs, calls));
    // import 自体は道具を呼ばない設定にしていないため、まず import の失敗が残る。whatif は呼ばれない。
    expect(calls.filter((c) => c.tool === "whatif")).toStrictEqual([]);
    expect(result.failures.some((f) => f.stage === "whatif")).toBe(true);
  });

  it("1 局の whatif が失敗しても他の局を止めず、失敗の一覧と exitCode ≠ 0 に残る", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1", "g2"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1"), senteJob("g2")], fs, runnerOf(fs, calls, { failWhatifFor: "g1" }));
    expect(calls.filter((c) => c.tool === "whatif")).toHaveLength(2);
    expect(fs.readText(whatifPath(personDir, "g2"))).toBe(validWhatif());
    expect(result.failures).toEqual([{ gameId: "g1", stage: "whatif", message: expect.stringContaining("whatif.ts rc=1") }]);
    expect(result.exitCode).toBe(1);
  });

  it("timing.jsonl に stage: \"whatif\" つきで残る", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fs, runnerOf(fs, calls));
    const lines = (fs.readText(timingPath("/w")) ?? "")
      .split("\n")
      .filter((l) => l.trim().length > 0)
      .map((l) => JSON.parse(l) as { gameId: string; stage?: string });
    expect(lines.some((l) => l.gameId === "g1" && l.stage === "whatif")).toBe(true);
  });

  it("--until が import(=段 1 未満)でも、fixed 棋譜さえ済んでいれば whatif は呼ぶ(段の進み具合に関係しない)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = makeFakeFs({ [gamePaths(personDir, "g1").fixedKifuPath]: validFixed("g1") });
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ whatif: true, until: "import" }), [senteJob("g1")], fs, runnerOf(fs, calls));
    expect(calls.some((c) => c.tool === "whatif")).toBe(true);
  });
});

// ---- runPipeline: --whatif 無し(動き・出力を 1 バイトも変えないことの確認) ----

describe("runPipeline: --whatif を付けない実行は変わらない", () => {
  it("whatif.ts を一切呼ばない・失敗を足さない・timing.jsonl に stage が付かない", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fs = readyFs(personDir, ["g1"]);
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs(), [senteJob("g1")], fs, runnerOf(fs, calls));
    expect(calls.filter((c) => c.tool === "whatif")).toStrictEqual([]);
    expect(result.failures).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
    const lines = (fs.readText(timingPath("/w")) ?? "")
      .split("\n")
      .filter((l) => l.trim().length > 0)
      .map((l) => JSON.parse(l) as Record<string, unknown>);
    for (const line of lines) expect(Object.hasOwn(line, "stage")).toBe(false);
  });

  it("2 つの実行(--whatif あり・無し)で、道具の呼び出し(whatif 以外)・gate.jsonl の有無・exitCode が同じ", async () => {
    const personDir = personWorkDir("/w", "p1");
    const fsA = readyFs(personDir, ["g1"]);
    const fsB = readyFs(personDir, ["g1"]);
    const callsA: Array<{ tool: string; args: string[] }> = [];
    const callsB: Array<{ tool: string; args: string[] }> = [];
    const resultA = await runPipeline(baseArgs({ whatif: true }), [senteJob("g1")], fsA, runnerOf(fsA, callsA));
    const resultB = await runPipeline(baseArgs(), [senteJob("g1")], fsB, runnerOf(fsB, callsB));
    expect(callsA.filter((c) => c.tool !== "whatif").map((c) => c.tool)).toStrictEqual(callsB.map((c) => c.tool));
    expect(fsA.readText(gateOutPath(personDir))).toBe(fsB.readText(gateOutPath(personDir)));
    expect(resultA.exitCode).toBe(resultB.exitCode);
  });
});
