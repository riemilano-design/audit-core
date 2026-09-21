// STEP PIPE 作業 A(docs/STEP_PIPE_PLAN_2026-09-21.md §2.1)。lib/pipeline.ts の試験。
// **エンジンも子プロセスも起こさない**(fs・道具の実行はすべて注入した偽物)。
//
// 見張ること(計画・依頼の指示・司令塔 e3 の直しから): 段の順序、済みの飛ばし、並行の上限を超えないこと、
// 1 局の失敗で他が止まらず最後に rc ≠ 0、引数が §1 の表の値と一致、--records-append を決して付けないこと、
// records/ へ書かないこと、--until と --dry-run。
//
// **S4(gate)の向き(2026-09-21 の直し)**: 材料の側 = このお客さん(--person・--kifu-dir の局)、
// 試す側 = --compare-dir の記録(先後は各記録の meta 行から読む。ファイル名には頼らない)。

import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  CONDITIONS_DIR,
  KIF_EXTENSIONS,
  PipelineArgError,
  PipelineConfigError,
  STAGE1_DIRECTION_RULE,
  STAGE1_NODES,
  STAGE1_REFERENCE_NODES,
  STAGE1_THREADS,
  STAGE2_DEEP_NODES,
  STAGES,
  diagnoseCommand,
  diagnoseDone,
  fixedKifuDone,
  gamePaths,
  gateCommand,
  gateDone,
  gateOutPath,
  importCommand,
  listGames,
  parsePipelineArgs,
  personWorkDir,
  planPipeline,
  readMetaLine,
  replayCommand,
  rescreenCommand,
  runPipeline,
  runWithLimit,
  sideOfStage2,
  stage1Done,
  stage2Done,
  timingLineOf,
  timingPath,
  type GameJob,
  type PipelineFs,
  type ToolResult,
  type ToolRunner,
} from "./pipeline.js";

// ---- 偽の fs(メモリ上。パス文字列をキーにした Map) ----

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

/** 何もファイルへ書かない fs(planPipeline が読み取り専用であることを確かめるための地雷) */
function makeThrowingWriteFs(initial: Record<string, string> = {}): PipelineFs {
  const store = new Map<string, string>(Object.entries(initial));
  return {
    readText: (filePath) => store.get(filePath),
    writeText: () => {
      throw new Error("writeText は呼ばれないはず(planPipeline は読み取り専用)");
    },
    appendText: () => {
      throw new Error("appendText は呼ばれないはず(planPipeline は読み取り専用)");
    },
    ensureDir: () => {
      throw new Error("ensureDir は呼ばれないはず(planPipeline は読み取り専用)");
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
const metaLine = (extra: Record<string, unknown> = {}): string => JSON.stringify({ kind: "meta", kifuId: "x", startedAt: "t", gitHead: null, enginePath: "/e", ...extra });
const validStage1 = (extra: Record<string, unknown> = {}): string => `${metaLine(extra)}\n${JSON.stringify({ kind: "summary", plies: 1, totalMs: 1, readyMsPerPly: [1] })}\n`;
const validStage2 = (extra: Record<string, unknown> = {}): string => `${metaLine(extra)}\n${JSON.stringify({ kind: "record", ply: 0 })}\n`;

const senteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-sente.kif`, kifName: `${id}-sente.kif`, sideMode: { kind: "filenameSuffix", side: "sente" } });
const goteJob = (id: string): GameJob => ({ id, kifPath: `/k/${id}-gote.kif`, kifName: `${id}-gote.kif`, sideMode: { kind: "filenameSuffix", side: "gote" } });

// ---- 引数の解釈 ----

describe("parsePipelineArgs", () => {
  it("必須の3つ(--person --kifu-dir --work)と既定値(--parallel 5・--until gate)", () => {
    const args = parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w"]);
    expect(args).toStrictEqual({
      person: "p1",
      kifuDir: "/k",
      work: "/w",
      me: undefined,
      parallel: 5,
      compareDirs: [],
      comparePerson: undefined,
      until: "gate",
      evaluator: undefined,
      dryRun: false,
    });
  });

  it("--compare-dir は複数値を取り、--compare-person と一緒に渡せる", () => {
    const args = parsePipelineArgs([
      "--person",
      "p1",
      "--kifu-dir",
      "/k",
      "--work",
      "/w",
      "--compare-dir",
      "/c1",
      "/c2",
      "--compare-person",
      "p2",
      "--until",
      "diagnose",
      "--me",
      "太郎",
      "--parallel",
      "3",
      "--evaluator",
      "NNUE test",
      "--dry-run",
    ]);
    expect(args.compareDirs).toStrictEqual(["/c1", "/c2"]);
    expect(args.comparePerson).toBe("p2");
    expect(args.until).toBe("diagnose");
    expect(args.me).toBe("太郎");
    expect(args.parallel).toBe(3);
    expect(args.evaluator).toBe("NNUE test");
    expect(args.dryRun).toBe(true);
  });

  it("--person・--kifu-dir・--work が無ければ止まる", () => {
    expect(() => parsePipelineArgs(["--kifu-dir", "/k", "--work", "/w"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--work", "/w"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k"])).toThrow(PipelineArgError);
  });

  it("--parallel は正の整数でなければ止まる", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--parallel", "0"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--parallel", "abc"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--parallel", "1.5"])).toThrow(PipelineArgError);
  });

  it("--until は import|evaluate|diagnose|gate のいずれかでなければ止まる", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--until", "report"])).toThrow(PipelineArgError);
  });

  it("--compare-dir と --compare-person は必ず一緒(片方だけは止まる)", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--compare-dir", "/c1"])).toThrow(PipelineArgError);
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--compare-person", "p2"])).toThrow(PipelineArgError);
  });

  it("知らない引数は止まる", () => {
    expect(() => parsePipelineArgs(["--person", "p1", "--kifu-dir", "/k", "--work", "/w", "--nodes", "1"])).toThrow(PipelineArgError);
  });
});

// ---- 局の一覧づくり ----

describe("listGames", () => {
  it("--me があれば、id はファイル名(拡張子を除く)そのもの。kifName は --kifu-dir からの相対(ファイル名そのもの)", () => {
    const games = listGames("/k", ["b.kif", "a.csa"], "太郎");
    expect(games).toStrictEqual([
      { id: "a", kifPath: path.join("/k", "a.csa"), kifName: "a.csa", sideMode: { kind: "me", me: "太郎" } },
      { id: "b", kifPath: path.join("/k", "b.kif"), kifName: "b.kif", sideMode: { kind: "me", me: "太郎" } },
    ]);
  });

  it("--me が無ければ、ファイル名の末尾 -sente / -gote を読む(id はそれを除いた部分。並びは id 昇順)", () => {
    const games = listGames("/k", ["p3-02-sente.kif", "p3-01-gote.kif"], undefined);
    expect(games).toStrictEqual([
      { id: "p3-01", kifPath: path.join("/k", "p3-01-gote.kif"), kifName: "p3-01-gote.kif", sideMode: { kind: "filenameSuffix", side: "gote" } },
      { id: "p3-02", kifPath: path.join("/k", "p3-02-sente.kif"), kifName: "p3-02-sente.kif", sideMode: { kind: "filenameSuffix", side: "sente" } },
    ]);
  });

  it("拡張子が対象外のファイルは無視する", () => {
    expect(listGames("/k", ["readme.md", "a-sente.kif"], undefined)).toHaveLength(1);
  });

  it("KIF_EXTENSIONS に .ki2 を含む(取り込めるかは kifu-import-check.ts の側の話で、一覧づくりでは弾かない)", () => {
    expect(KIF_EXTENSIONS).toContain(".ki2");
    expect(listGames("/k", ["a-sente.ki2"], undefined)).toHaveLength(1);
  });

  it("--me が無く、ファイル名の末尾が -sente / -gote でもなければ止まる(推測しない)", () => {
    expect(() => listGames("/k", ["mystery.kif"], undefined)).toThrow(PipelineConfigError);
  });
});

// ---- 既存の道具へ渡す引数(計画 §1 の表の値に固定) ----

describe("道具へ渡す引数(表の値に固定)", () => {
  const job: GameJob = { id: "g1", kifPath: "/k/g1-sente.kif", kifName: "g1-sente.kif", sideMode: { kind: "filenameSuffix", side: "sente" } };

  it("importCommand: --as 経路(ファイル名の末尾)。--source は --kifu-dir からの相対(ファイル名。絶対パスを固定棋譜に残さない)", () => {
    expect(importCommand(job, "/w/kifu/g1.fixed.json")).toStrictEqual(["/k/g1-sente.kif", "--fixed", "/w/kifu/g1.fixed.json", "--id", "g1", "--source", "g1-sente.kif", "--as", "sente"]);
  });

  it("importCommand: --me 経路", () => {
    const meJob: GameJob = { id: "g2", kifPath: "/k/g2.kif", kifName: "g2.kif", sideMode: { kind: "me", me: "太郎" } };
    expect(importCommand(meJob, "/w/kifu/g2.fixed.json")).toStrictEqual(["/k/g2.kif", "--fixed", "/w/kifu/g2.fixed.json", "--id", "g2", "--source", "g2.kif", "--me", "太郎"]);
  });

  it("replayCommand: nodes 400000・reference-nodes 400000・threads 1・direction-rule current(表のとおり)", () => {
    expect(STAGE1_NODES).toBe(400_000);
    expect(STAGE1_REFERENCE_NODES).toBe(400_000);
    expect(STAGE1_THREADS).toBe(1);
    expect(STAGE1_DIRECTION_RULE).toBe("current");
    expect(replayCommand("/w/kifu/g1.fixed.json", "/w/stage1/g1.jsonl")).toStrictEqual([
      "/w/kifu/g1.fixed.json",
      "--nodes",
      "400000",
      "--reference-nodes",
      "400000",
      "--threads",
      "1",
      "--direction-rule",
      "current",
      "--out",
      "/w/stage1/g1.jsonl",
    ]);
  });

  it("rescreenCommand: deep-nodes 4000000(表のとおり)", () => {
    expect(STAGE2_DEEP_NODES).toBe(4_000_000);
    expect(rescreenCommand("/w/stage1/g1.jsonl", "/w/stage2/g1.jsonl")).toStrictEqual(["/w/stage1/g1.jsonl", "--out", "/w/stage2/g1.jsonl", "--deep-nodes", "4000000"]);
  });

  it("diagnoseCommand: --evaluator は渡されたときだけ付く", () => {
    expect(diagnoseCommand(["/a.jsonl", "/b.jsonl"], "/e.jsonl", "/r.jsonl", "/m.jsonl", undefined)).toStrictEqual([
      "/a.jsonl",
      "/b.jsonl",
      "--events",
      "/e.jsonl",
      "--events-rise",
      "/r.jsonl",
      "--events-maxdrop",
      "/m.jsonl",
    ]);
    expect(diagnoseCommand(["/a.jsonl"], "/e.jsonl", "/r.jsonl", "/m.jsonl", "NNUE")).toStrictEqual([
      "/a.jsonl",
      "--events",
      "/e.jsonl",
      "--events-rise",
      "/r.jsonl",
      "--events-maxdrop",
      "/m.jsonl",
      "--evaluator",
      "NNUE",
    ]);
  });

  it("gateCommand: 第1引数が --person(材料)、第2引数が --test-person(試す側)。--records-append を絶対に足さない。--test-gote は 1 件以上のときだけ付く", () => {
    const withoutGote = gateCommand("p1", "p2", ["/m1.jsonl"], ["/s1.jsonl"], [], "/conditions", "/gate.jsonl");
    expect(withoutGote).toStrictEqual(["--person", "p1", "--test-person", "p2", "--material", "/m1.jsonl", "--test-sente", "/s1.jsonl", "--conditions", "/conditions", "--out", "/gate.jsonl"]);
    expect(withoutGote).not.toContain("--records-append");

    const withGote = gateCommand("p1", "p2", ["/m1.jsonl"], ["/s1.jsonl"], ["/g1.jsonl"], "/conditions", "/gate.jsonl");
    expect(withGote).toContain("--test-gote");
    expect(withGote).not.toContain("--records-append");
  });

  it("CONDITIONS_DIR は scripts/playtest/lib/conditions を指す", () => {
    expect(CONDITIONS_DIR.endsWith(path.join("lib", "conditions"))).toBe(true);
  });
});

// ---- 段ごとの「済み」の判定 ----

describe("fixedKifuDone", () => {
  it("無い・壊れた JSON・id 不一致・moves が配列でない、はすべて false", () => {
    expect(fixedKifuDone(undefined, "g1")).toBe(false);
    expect(fixedKifuDone("{not json", "g1")).toBe(false);
    expect(fixedKifuDone(validFixed("other"), "g1")).toBe(false);
    expect(fixedKifuDone(JSON.stringify({ id: "g1", moves: "x" }), "g1")).toBe(false);
  });
  it("id が一致し moves が配列なら true", () => {
    expect(fixedKifuDone(validFixed("g1"), "g1")).toBe(true);
  });
});

describe("stage1Done", () => {
  it("無い・空・最後の行が summary でない、はすべて false", () => {
    expect(stage1Done(undefined)).toBe(false);
    expect(stage1Done("")).toBe(false);
    expect(stage1Done(`${metaLine()}\n`)).toBe(false);
  });
  it("最後の行が summary なら true(末尾の空行・空白は無視)", () => {
    expect(stage1Done(validStage1())).toBe(true);
    expect(stage1Done(`${validStage1()}\n\n  \n`)).toBe(true);
  });
});

describe("stage2Done", () => {
  it("無い・空(空白だけ)は false、それ以外は true", () => {
    expect(stage2Done(undefined)).toBe(false);
    expect(stage2Done("")).toBe(false);
    expect(stage2Done("   \n")).toBe(false);
    expect(stage2Done(validStage2())).toBe(true);
  });
});

describe("diagnoseDone", () => {
  it("4 つすべてが無ければ false・1 つでも欠けても false・4 つ揃えば true", () => {
    expect(diagnoseDone(undefined, undefined, undefined, undefined)).toBe(false);
    expect(diagnoseDone("a", "b", "c", undefined)).toBe(false);
    expect(diagnoseDone("a", "b", "", "d")).toBe(false);
    expect(diagnoseDone("a", "b", "c", "d")).toBe(true);
  });
});

describe("gateDone", () => {
  it("存在の有無をそのまま返す", () => {
    expect(gateDone(true)).toBe(true);
    expect(gateDone(false)).toBe(false);
  });
});

// ---- meta 行 / 本人の側 ----

describe("readMetaLine / sideOfStage2", () => {
  it("meta 行を先頭から探して返す", () => {
    expect(readMetaLine(validStage2())).toMatchObject({ kind: "meta", kifuId: "x" });
    expect(readMetaLine("not json\n")).toBeUndefined();
    expect(readMetaLine("")).toBeUndefined();
  });

  it("mirrored の無い記録は sente、mirrored: true + originalUserSide: gote は gote", () => {
    expect(sideOfStage2(validStage2())).toBe("sente");
    expect(sideOfStage2(validStage2({ mirrored: true, originalUserSide: "gote" }))).toBe("gote");
  });

  it("形が壊れていれば null(userSideOf が投げる例外を吸収する)", () => {
    expect(sideOfStage2(validStage2({ mirrored: true }))).toBeNull();
  });
});

// ---- 上限つきの並行実行 ----

describe("runWithLimit", () => {
  it("結果は入力の順のまま返す", async () => {
    const results = await runWithLimit([1, 2, 3], 2, async (n) => {
      // 何もしない
      void n;
    });
    expect(results.map((r) => r.job)).toStrictEqual([1, 2, 3]);
    expect(results.every((r) => r.ok)).toBe(true);
  });

  it("同時実行が limit を超えない", async () => {
    let active = 0;
    let maxActive = 0;
    const jobs = Array.from({ length: 8 }, (_, i) => i);
    await runWithLimit(jobs, 3, async () => {
      active += 1;
      maxActive = Math.max(maxActive, active);
      await new Promise((resolve) => setTimeout(resolve, 5));
      active -= 1;
    });
    expect(maxActive).toBeLessThanOrEqual(3);
    expect(maxActive).toBe(3);
  });

  it("1 件の失敗で他が止まらない。失敗した件だけ ok: false", async () => {
    const results = await runWithLimit([1, 2, 3], 3, async (n) => {
      if (n === 2) throw new Error("boom");
    });
    expect(results.map((r) => r.ok)).toStrictEqual([true, false, true]);
    expect(results[1]!.error).toBeInstanceOf(Error);
  });
});

// ---- runPipeline(実行) ----

function successfulRunner(fs: ReturnType<typeof makeFakeFs>, calls: Array<{ tool: string; args: string[] }>, options: { failImportFor?: string } = {}): ToolRunner {
  return async (tool, args): Promise<ToolResult> => {
    calls.push({ tool, args: [...args] });
    if (tool === "kifu-import-check") {
      const idIndex = args.indexOf("--id");
      const id = args[idIndex + 1]!;
      if (options.failImportFor === id) return { code: 1, stdout: "", stderr: "boom" };
      const fixedIndex = args.indexOf("--fixed");
      fs.writeText(args[fixedIndex + 1]!, validFixed(id));
      return { code: 0, stdout: "", stderr: "" };
    }
    if (tool === "replay") {
      const outIndex = args.indexOf("--out");
      fs.writeText(args[outIndex + 1]!, validStage1());
      return { code: 0, stdout: "", stderr: "" };
    }
    if (tool === "rescreen") {
      const outIndex = args.indexOf("--out");
      fs.writeText(args[outIndex + 1]!, validStage2());
      return { code: 0, stdout: "", stderr: "" };
    }
    if (tool === "diagnose") {
      const eventsIndex = args.indexOf("--events");
      const riseIndex = args.indexOf("--events-rise");
      const maxdropIndex = args.indexOf("--events-maxdrop");
      fs.writeText(args[eventsIndex + 1]!, "{}\n");
      fs.writeText(args[riseIndex + 1]!, "{}\n");
      fs.writeText(args[maxdropIndex + 1]!, "{}\n");
      return { code: 0, stdout: "# diagnose\n", stderr: "" };
    }
    if (tool === "gate") {
      const outIndex = args.indexOf("--out");
      fs.writeText(args[outIndex + 1]!, "{}\n");
      return { code: 0, stdout: "", stderr: "" };
    }
    return { code: 0, stdout: "", stderr: "" };
  };
}

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

describe("runPipeline: 段の順序", () => {
  it("新しい局は import → replay → rescreen の順に呼ぶ(until=evaluate)", async () => {
    const fs = makeFakeFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    const result = await runPipeline(baseArgs({ until: "evaluate" }), games, fs, successfulRunner(fs, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual(["kifu-import-check", "replay", "rescreen"]);
    expect(result.exitCode).toBe(0);
    expect(result.failures).toStrictEqual([]);
  });
});

describe("runPipeline: 済みの飛ばし", () => {
  it("段 1・段 2 とも済んでいれば kifu-import-check・replay・rescreen を一切呼ばない(until=evaluate)", async () => {
    const personDir = personWorkDir("/w", "p1");
    const gp = gamePaths(personDir, "g1");
    const fs = makeFakeFs({
      [gp.fixedKifuPath]: validFixed("g1"),
      [gp.stage1Path]: validStage1(),
      [gp.stage2Path]: validStage2(),
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    const result = await runPipeline(baseArgs({ until: "evaluate" }), games, fs, successfulRunner(fs, calls));
    expect(calls).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });

  it("段 1 だけ済んでいれば import は呼ばず、replay と rescreen だけ呼ぶ", async () => {
    const personDir = personWorkDir("/w", "p1");
    const gp = gamePaths(personDir, "g1");
    const fs = makeFakeFs({ [gp.fixedKifuPath]: validFixed("g1"), [gp.stage1Path]: validStage1() });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    await runPipeline(baseArgs({ until: "evaluate" }), games, fs, successfulRunner(fs, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual(["rescreen"]);
  });

  it("診断(S3)がすでに揃っていれば diagnose.ts を呼ばない", async () => {
    const personDir = personWorkDir("/w", "p1");
    const gp = gamePaths(personDir, "g1");
    const fs = makeFakeFs({
      [gp.fixedKifuPath]: validFixed("g1"),
      [gp.stage1Path]: validStage1(),
      [gp.stage2Path]: validStage2(),
      [path.join(personDir, "diagnose", "events.jsonl")]: "e",
      [path.join(personDir, "diagnose", "rise.jsonl")]: "r",
      [path.join(personDir, "diagnose", "maxdrop.jsonl")]: "m",
      [path.join(personDir, "diagnose", "diagnose.md")]: "# md",
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    const result = await runPipeline(baseArgs({ until: "diagnose" }), games, fs, successfulRunner(fs, calls));
    expect(calls).toStrictEqual([]);
    expect(result.exitCode).toBe(0);
  });
});

describe("runPipeline: 並行の上限", () => {
  it("--parallel を超えて同時に呼ばない", async () => {
    const fs = makeFakeFs();
    let active = 0;
    let maxActive = 0;
    const games: GameJob[] = Array.from({ length: 6 }, (_, i) => senteJob(`g${i}`));
    const run: ToolRunner = async (tool, args) => {
      if (tool === "kifu-import-check") {
        active += 1;
        maxActive = Math.max(maxActive, active);
        await new Promise((resolve) => setTimeout(resolve, 5));
        active -= 1;
        const idIndex = args.indexOf("--id");
        const fixedIndex = args.indexOf("--fixed");
        fs.writeText(args[fixedIndex + 1]!, validFixed(args[idIndex + 1]!));
        return { code: 0, stdout: "", stderr: "" };
      }
      return { code: 0, stdout: "", stderr: "" };
    };
    await runPipeline(baseArgs({ until: "import", parallel: 2 }), games, fs, run);
    expect(maxActive).toBeLessThanOrEqual(2);
    expect(maxActive).toBe(2);
  });
});

describe("runPipeline: 1局の失敗で他を止めない", () => {
  it("1 局が import で失敗しても、他の局は最後まで進み、最後に失敗の一覧と rc ≠ 0", async () => {
    const fs = makeFakeFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("bad"), senteJob("good")];
    const result = await runPipeline(baseArgs({ until: "evaluate" }), games, fs, successfulRunner(fs, calls, { failImportFor: "bad" }));
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.gameId === "bad")).toBe(true);
    // good 側は最後まで進んでいる(段2の成果物がある)
    const goodPaths = gamePaths(personWorkDir("/w", "p1"), "good");
    expect(fs.readText(goodPaths.stage2Path)).toBeDefined();
    // bad 側は成果物が無い
    const badPaths = gamePaths(personWorkDir("/w", "p1"), "bad");
    expect(fs.readText(badPaths.fixedKifuPath)).toBeUndefined();
  });
});

describe("runPipeline: --until", () => {
  const games: GameJob[] = [senteJob("g1")];

  it("--until import なら kifu-import-check だけ", async () => {
    const fs = makeFakeFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ until: "import" }), games, fs, successfulRunner(fs, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual(["kifu-import-check"]);
  });

  it("--until diagnose は diagnose まで呼び、gate は呼ばない(--compare-dir があっても)", async () => {
    const fs = makeFakeFs({ "/material/a.jsonl": validStage2() });
    const calls: Array<{ tool: string; args: string[] }> = [];
    await runPipeline(baseArgs({ until: "diagnose", compareDirs: ["/material"], comparePerson: "p2" }), games, fs, successfulRunner(fs, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual(["kifu-import-check", "replay", "rescreen", "diagnose"]);
  });

  it("--until gate でも --compare-dir が無ければ gate は呼ばず、失敗にもしない", async () => {
    const fs = makeFakeFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const result = await runPipeline(baseArgs({ until: "gate" }), games, fs, successfulRunner(fs, calls));
    expect(calls.map((c) => c.tool)).toStrictEqual(["kifu-import-check", "replay", "rescreen", "diagnose"]);
    expect(result.exitCode).toBe(0);
  });
});

describe("runPipeline: gate の向き(材料 = このお客さん、試す側 = --compare-dir)", () => {
  it("材料は必ずこのお客さんの段 2、試す側は --compare-dir の *.jsonl を各記録の meta の本人の側で振り分ける", async () => {
    const fs = makeFakeFs({
      "/material/sente-rec.jsonl": validStage2(),
      "/material/gote-rec.jsonl": validStage2({ mirrored: true, originalUserSide: "gote" }),
      "/material/readme.md": "z",
    });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("s1"), senteJob("s2")];
    const result = await runPipeline(baseArgs({ compareDirs: ["/material"], comparePerson: "p2" }), games, fs, successfulRunner(fs, calls));
    const gateCall = calls.find((c) => c.tool === "gate")!;
    // --person(材料)= このお客さん、--test-person(試す側)= --compare-person
    expect(gateCall.args[gateCall.args.indexOf("--person") + 1]).toBe("p1");
    expect(gateCall.args[gateCall.args.indexOf("--test-person") + 1]).toBe("p2");
    // 材料 = このお客さんの段 2(s1・s2)
    const materialArgs = gateCall.args.slice(gateCall.args.indexOf("--material") + 1, gateCall.args.indexOf("--test-sente"));
    expect(materialArgs.sort()).toStrictEqual([gamePaths(personWorkDir("/w", "p1"), "s1").stage2Path, gamePaths(personWorkDir("/w", "p1"), "s2").stage2Path].sort());
    // 試す側 = --compare-dir の記録(meta の本人の側で振り分け。ファイル名に "gote"/"sente" は使っていない)
    expect(gateCall.args).toContain("--test-sente");
    expect(gateCall.args).toContain("--test-gote");
    const testSenteIndex = gateCall.args.indexOf("--test-sente");
    const testGoteIndex = gateCall.args.indexOf("--test-gote");
    expect(gateCall.args.slice(testSenteIndex + 1, testGoteIndex)).toStrictEqual(["/material/sente-rec.jsonl"]);
    expect(gateCall.args.slice(testGoteIndex + 1, gateCall.args.indexOf("--conditions"))).toStrictEqual(["/material/gote-rec.jsonl"]);
    expect(gateCall.args).not.toContain("--records-append");
    expect(result.exitCode).toBe(0);
  });

  it("--compare-dir の記録の本人の側が meta から決められなければ、推測せずこの段を失敗にする(ファイル名には頼らない)", async () => {
    // meta 行自体が無い記録は sente とみなす(D0-SIDE より前の記録との後方互換。README・userSideOf の規約どおり)ので、
    // ここでは mirrored: true なのに originalUserSide が無い(形が決まりと食い違う)記録を置き、決められないことを確かめる。
    // ファイル名には gote 等を含めない(--compare-dir のフォルダには命名の規約が無いことを確かめる意図)。
    const fs = makeFakeFs({ "/material/broken.jsonl": `${metaLine({ mirrored: true })}\n` });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("s1")];
    const result = await runPipeline(baseArgs({ compareDirs: ["/material"], comparePerson: "p2" }), games, fs, successfulRunner(fs, calls));
    expect(calls.some((c) => c.tool === "gate")).toBe(false);
    expect(result.exitCode).toBe(1);
    expect(result.failures.some((f) => f.stage === "gate" && f.message.includes("broken.jsonl") && f.message.includes("推測しない"))).toBe(true);
  });
});

describe("runPipeline: records/ には一切書かない", () => {
  it("fs.writeText / fs.appendText / fs.ensureDir の対象パスに 'records' を含むものが無い", async () => {
    const fs = makeFakeFs({ "/material/a.jsonl": validStage2() });
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    await runPipeline(baseArgs({ compareDirs: ["/material"], comparePerson: "p2" }), games, fs, successfulRunner(fs, calls));
    for (const key of fs.store.keys()) expect(key).not.toContain("records");
    for (const dir of fs.ensureDirCalls) expect(dir).not.toContain("records");
    for (const call of calls) for (const a of call.args) expect(a).not.toContain("records/");
  });
});

describe("runPipeline: timing.jsonl", () => {
  it("局ごとに開始・終了・rc の行を書く", async () => {
    const fs = makeFakeFs();
    const calls: Array<{ tool: string; args: string[] }> = [];
    const games: GameJob[] = [senteJob("g1")];
    await runPipeline(baseArgs({ until: "evaluate" }), games, fs, successfulRunner(fs, calls));
    const lines = (fs.readText(timingPath("/w")) ?? "")
      .split("\n")
      .filter((line) => line.trim().length > 0)
      .map((line) => JSON.parse(line) as { gameId: string; startedAt: string; finishedAt: string; rc: number | "skip" });
    expect(lines).toHaveLength(1);
    expect(lines[0]!.gameId).toBe("g1");
    expect(typeof lines[0]!.startedAt).toBe("string");
    expect(typeof lines[0]!.finishedAt).toBe("string");
  });

  it("timingLineOf は改行付きの1行 JSON", () => {
    const line = timingLineOf({ gameId: "g1", startedAt: "a", finishedAt: "b", rc: "skip" });
    expect(line).toBe(`${JSON.stringify({ gameId: "g1", startedAt: "a", finishedAt: "b", rc: "skip" })}\n`);
  });
});

// ---- --dry-run(planPipeline) ----

describe("planPipeline(--dry-run)", () => {
  it("fs へは書かない(writeText/appendText/ensureDir を呼べば例外になる fs でも通る)", () => {
    const games: GameJob[] = [senteJob("g1")];
    const fs = makeThrowingWriteFs();
    expect(() => planPipeline(baseArgs(), games, fs)).not.toThrow();
  });

  it("済みの局は action: skip、未実施は action: run", () => {
    const personDir = personWorkDir("/w", "p1");
    const gpDone = gamePaths(personDir, "done");
    const fs = makeThrowingWriteFs({ [gpDone.fixedKifuPath]: validFixed("done"), [gpDone.stage1Path]: validStage1(), [gpDone.stage2Path]: validStage2() });
    const games: GameJob[] = [senteJob("done"), senteJob("todo")];
    const steps = planPipeline(baseArgs({ until: "evaluate" }), games, fs);
    const doneSteps = steps.filter((s) => s.gameId === "done");
    const todoSteps = steps.filter((s) => s.gameId === "todo");
    expect(doneSteps.every((s) => s.action === "skip")).toBe(true);
    expect(todoSteps.every((s) => s.action === "run")).toBe(true);
  });

  it("diagnose のプレビューは、今すでに段2が済んでいる局だけを対象にする。gate のプレビューは材料=お客さん・試す側=--compare-dir(meta 由来)", () => {
    const personDir = personWorkDir("/w", "p1");
    const gpDone = gamePaths(personDir, "done");
    const fs = makeThrowingWriteFs({
      [gpDone.fixedKifuPath]: validFixed("done"),
      [gpDone.stage1Path]: validStage1(),
      [gpDone.stage2Path]: validStage2(),
      "/material/a.jsonl": validStage2({ mirrored: true, originalUserSide: "gote" }),
    });
    const games: GameJob[] = [senteJob("done"), senteJob("todo")];
    const steps = planPipeline(baseArgs({ compareDirs: ["/material"], comparePerson: "p2" }), games, fs);
    const diagnoseStep = steps.find((s) => s.stage === "diagnose")!;
    expect(diagnoseStep.args).toContain(gpDone.stage2Path);
    expect(diagnoseStep.args).not.toContain(gamePaths(personDir, "todo").stage2Path);
    const gateStep = steps.find((s) => s.stage === "gate")!;
    expect(gateStep.args).not.toContain("--records-append");
    expect(gateStep.args[gateStep.args.indexOf("--person") + 1]).toBe("p1");
    expect(gateStep.args[gateStep.args.indexOf("--test-person") + 1]).toBe("p2");
    // 材料 = お客さんの段 2 済みの局だけ
    expect(gateStep.args.slice(gateStep.args.indexOf("--material") + 1, gateStep.args.indexOf("--test-sente"))).toStrictEqual([gpDone.stage2Path]);
    // 試す側(gote) = --compare-dir の記録(meta が mirrored: true なので --test-gote 側)。--test-sente 自体は旗として残るが値は無い
    const tsIndex = gateStep.args.indexOf("--test-sente");
    const tgIndex = gateStep.args.indexOf("--test-gote");
    expect(gateStep.args.slice(tsIndex + 1, tgIndex)).toStrictEqual([]);
    expect(gateStep.args.slice(tgIndex + 1)).toStrictEqual(["/material/a.jsonl", "--conditions", CONDITIONS_DIR, "--out", gateOutPath(personDir)]);
  });

  it("--until を越える段のプレビューは出さない", () => {
    const games: GameJob[] = [senteJob("g1")];
    const fs = makeThrowingWriteFs();
    const steps = planPipeline(baseArgs({ until: "import" }), games, fs);
    expect(steps.map((s) => s.stage)).toStrictEqual(["import"]);
  });
});

// ---- 段の一覧は配列で足せる形(--until の値はここから出す) ----

describe("STAGES", () => {
  it("import・evaluate・diagnose・gate の 4 段(この順)", () => {
    expect(STAGES).toStrictEqual(["import", "evaluate", "diagnose", "gate"]);
  });
});
