// STEP D-SCREEN-1(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §2・§6・§11)。候補の組の選び方・読み直す行・段 2 の記録の形を見張る。
// エンジンは使わない(偽の measure・偽の git)。記録は GAME01 の実際の手順に評価を植えたもの(lib/failureEventFixtures.ts)。

import { describe, expect, it } from "vitest";
import type { EngineReferenceMeasurement } from "../../../apps/server/src/analysis/engineReference.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { RecordLine } from "../invariants/types.js";
import { pairEvaluations, readEvaluations } from "./failureEvent.js";
import { recordSha256 } from "./failureEventSchema.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { readGitState, type GitRunner } from "./gitState.js";
import {
  deepPliesOf,
  DRAFT_SCREEN_RULE_1,
  planRescreen,
  RescreenInputError,
  rescreenRecords,
  screenCandidatesOf,
  type DeepRunInput,
  type ScreenMeasure,
} from "./rescreen.js";

const rule = DRAFT_SCREEN_RULE_1;
const LIGHT = 400_000;
const DEEP = 4_000_000;
// ready 行は ply 0〜20 の 11 行。王手中の行は無い(GAME01 で最初に先手が王手中になるのは ply 34)
const MOVES20 = GAME01_MOVES.slice(0, 20);

function observation(tag: string, sfen: string): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: null, mate: null, pv: [tag], lowerbound: false, upperbound: false };
}

/** 段 1 の記録: 植えた評価を軽いノード数にし、ready 行ごとに③の探索の読み筋(軽い)を持たせる */
function stage1Records(plant: Record<number, PlantedEvaluation>, moves: readonly string[] = MOVES20): RecordLine[] {
  return plantedRecords(moves, plant).map((record): RecordLine => ({
    ...record,
    ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: LIGHT } } : {}),
    searchPvs: [observation(`light-${record.ply}`, record.sfen)],
  }));
}

const META = {
  kind: "meta",
  kifuId: "rescreen-fixture",
  startedAt: "stage1-start",
  gitHead: "stage1head",
  dirty: false,
  dirtyPaths: [],
  dirtyCount: 0,
  enginePath: "/stage1/engine",
  searchMode: "nodes",
  nodes: LIGHT,
  threads: 1,
  referenceNodes: LIGHT,
};

/** 段 1 のファイルのバイト列。本物の replay.ts と同じく、ready 行の前に immediate 行がある(ply 6 だけ置く) */
function stage1Source(records: readonly RecordLine[], meta: Record<string, unknown> = META): Buffer {
  const lines: unknown[] = [meta];
  for (const record of records) {
    if (record.ply === 6) lines.push({ kind: "record", ply: 6, sfen: record.sfen, senteMove: record.senteMove, goteMove: record.goteMove, phase: "immediate", elapsedMs: 0, response: record.response });
    lines.push(record);
  }
  return Buffer.from(`${lines.map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
}

// 深い回の作業ツリーは汚れていた、とする。段 1 の META(gitHead stage1head・dirty false)と違う値にして、gitHead と dirty の両方を
// 道具が自分で読むことを見張る(監査 f2 の N-1。dirty が同じ false だと、段 1 の meta から写す変異が沈黙した)
const fakeGit: GitRunner = (args) => (args[0] === "rev-parse" ? "deephead\n" : " M scripts/playtest/lib/rescreen.ts\0");

function run(overrides: Partial<DeepRunInput> = {}): DeepRunInput {
  return { deepNodes: DEEP, enginePath: "/deep/engine", threads: 1, startedAt: "deep-start", repoRoot: "/repo", runGit: fakeGit, ...overrides };
}

/** 呼ばれるたびに違う値を返す偽の measure(何回目の呼び出しの値かを、評価・最善手・読み筋に書く) */
function fakeMeasure(result?: (sfen: string, call: number) => EngineReferenceMeasurement) {
  const calls: string[] = [];
  const measure: ScreenMeasure = async (sfen) => {
    calls.push(sfen);
    const call = calls.length;
    return result
      ? result(sfen, call)
      : { reference: { ...engineRef(-1000 - call, { bestmove: `deep-best-${call}` }), nodes: DEEP }, searchPvs: [observation(`deep-call-${call}`, sfen)] };
  };
  return { calls, measure };
}

// ---- 候補の組(計画 §2 の (a)〜(d))----

describe("STEP D-SCREEN-1 の候補の組(計画 §2)", () => {
  it("S-1: 直前 0 で差 −299 は候補にならず、差 −300 は候補になる((b) に当たらない直前)", () => {
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(0), 12: engineRef(-299) }), rule)).toEqual([]);
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(0), 12: engineRef(-300) }), rule)).toEqual([{ fromPly: 10, toPly: 12, reasons: ["drop"] }]);
  });

  it("S-2: 直前 +300・差 −200 は候補になり、直前 +299・差 −200 は候補にならない", () => {
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(300), 12: engineRef(100) }), rule)).toEqual([{ fromPly: 10, toPly: 12, reasons: ["advantageDrop"] }]);
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(299), 12: engineRef(99) }), rule)).toEqual([]);
  });

  it("(a) と (b) の両方に当たる組は、理由を両方持つ", () => {
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(300), 12: engineRef(-100) }), rule)).toEqual([{ fromPly: 10, toPly: 12, reasons: ["drop", "advantageDrop"] }]);
  });

  it("S-5: notEvaluation の組と notMeasurable の組は候補になり、王手中・終局の組は候補にならない", () => {
    expect(screenCandidatesOf(stage1Records({ 6: engineRef(40_000) }), rule)).toEqual([
      { fromPly: 4, toPly: 6, reasons: ["notEvaluation"] },
      { fromPly: 6, toPly: 8, reasons: ["notEvaluation"] },
    ]);
    expect(screenCandidatesOf(stage1Records({ 6: null }), rule)).toEqual([
      { fromPly: 4, toPly: 6, reasons: ["notMeasurable"] },
      { fromPly: 6, toPly: 8, reasons: ["notMeasurable"] },
    ]);
    // GAME01 の全手: ply 34・36・38・40・52・54 は王手中、56 は終局で null(plantedRecords の既定)。ほかの行は 0 で差も 0
    const whole = stage1Records({}, GAME01_MOVES);
    expect(whole.filter((record) => record.engineReference === null).map((record) => record.ply)).toEqual([34, 36, 38, 40, 52, 54, 56]);
    expect(screenCandidatesOf(whole, rule)).toEqual([]);
    // 終局の組(監査 f2 の N-2): GAME01 は終局の行(56)の前が王手中(54)なので、直前の行 54 に測れた値を植えて、
    // 直前が測れて直後が終局の組を作る(本物の記録では王手中の行は null。ここは reason を notMeasuredGameEnd にするための植え方)
    const gameEnd = stage1Records({ 54: engineRef(0) }, GAME01_MOVES);
    const gameEndPairs = pairEvaluations(readEvaluations(gameEnd));
    expect(gameEndPairs[gameEndPairs.length - 1]).toEqual({ fromPly: 54, toPly: 56, kind: "notCompared", reason: "notMeasuredGameEnd", side: "to" });
    expect(screenCandidatesOf(gameEnd, rule)).toEqual([]);
  });

  it("S-11: 直後が詰まされる読み(mate −3)の組と、直後の行の afterPassMate +3 の組は、どちらも候補になる", () => {
    expect(screenCandidatesOf(stage1Records({ 10: engineRef(0), 12: engineRef(null, { mate: -3 }) }), rule)).toEqual([{ fromPly: 10, toPly: 12, reasons: ["mateAfter"] }]);
    expect(screenCandidatesOf(stage1Records({ 12: engineRef(0, { afterPassMate: 3 }) }), rule)).toEqual([{ fromPly: 10, toPly: 12, reasons: ["matedIfPass"] }]);
  });
});

// ---- 読み直す行(計画 §2・Q-2)----

describe("STEP D-SCREEN-1 の読み直す行(計画 §2)", () => {
  it("S-3: 候補が最初の組なら行 i−1 が、最後の組なら行 i+2 が端で切れる", () => {
    expect(deepPliesOf(stage1Records({ 2: engineRef(-300) }), rule)).toEqual([0, 2, 4]);
    expect(deepPliesOf(stage1Records({ 20: engineRef(-300) }), rule)).toEqual([16, 18, 20]);
    // 端でない組は 4 行
    expect(deepPliesOf(stage1Records({ 10: engineRef(-300) }), rule)).toEqual([6, 8, 10, 12]);
  });

  it("S-4: 隣り合う 2 つの候補の読み直す行は、重なりを 1 回にして昇順に並ぶ", () => {
    const records = stage1Records({ 6: engineRef(-300), 8: engineRef(-600) });
    expect(screenCandidatesOf(records, rule).map((candidate) => [candidate.fromPly, candidate.toPly])).toEqual([
      [4, 6],
      [6, 8],
    ]);
    expect(deepPliesOf(records, rule)).toEqual([2, 4, 6, 8, 10]);
  });

  it("候補が無ければ読み直す行も無い", () => {
    expect(deepPliesOf(stage1Records({}), rule)).toEqual([]);
  });
});

// ---- 段 2 の記録(計画 §2・§11)----

describe("STEP D-SCREEN-1 の段 2 の記録(計画 §2・§11)", () => {
  const records = stage1Records({ 6: engineRef(-300), 8: engineRef(-600) });
  const DEEP_PLIES = [2, 4, 6, 8, 10];
  const plyOfSfen = new Map(records.map((record) => [record.sfen, record.ply]));

  it("S-12: 段 1 のバイト列と engineReference を変えず、読み直していない行はそのまま、meta に screen を足し、deepRun の git は道具が読み、measuredOrder は measure を呼んだ順", async () => {
    const source = stage1Source(records);
    const sourceCopy = Buffer.from(source);
    const { calls, measure } = fakeMeasure();
    const text = await rescreenRecords(source, rule, measure, run());

    expect(Buffer.compare(source, sourceCopy)).toBe(0);
    const inLines = source.toString("utf-8").split("\n");
    const outLines = text.split("\n");
    expect(outLines).toHaveLength(inLines.length);
    expect(outLines[outLines.length - 1]).toBe("");

    // meta: 段 1 の欄はそのままの値と並び、後ろに screen
    const inMeta = JSON.parse(inLines[0]!) as Record<string, unknown>;
    const outMeta = JSON.parse(outLines[0]!) as Record<string, unknown>;
    expect(Object.keys(outMeta)).toEqual([...Object.keys(inMeta), "screen"]);
    const { screen, ...restMeta } = outMeta;
    expect(restMeta).toEqual(inMeta);
    const git = readGitState("/repo", fakeGit);
    expect(git.gitHead).toBe("deephead");
    expect(git.dirty).toBe(true);
    expect(inMeta.gitHead).toBe("stage1head");
    expect(inMeta.dirty).toBe(false);
    expect(screen).toEqual({
      lightNodes: LIGHT,
      deepNodes: DEEP,
      rule: DRAFT_SCREEN_RULE_1,
      deepPlies: DEEP_PLIES,
      sourceSha256: recordSha256(source),
      deepRun: {
        gitHead: git.gitHead,
        dirty: git.dirty,
        enginePath: "/deep/engine",
        threads: 1,
        startedAt: "deep-start",
        order: "plyAscending",
        measuredOrder: calls.map((sfen) => plyOfSfen.get(sfen)),
      },
    });
    // measure は ply の昇順に 1 行 1 回
    expect(calls.map((sfen) => plyOfSfen.get(sfen))).toEqual(DEEP_PLIES);

    // record 行: 読み直していない行(immediate 行を含む)は段 1 のバイト列のまま。読み直した行は欄を後ろに足すだけ
    let deepRows = 0;
    for (let index = 1; index < inLines.length; index++) {
      const inLine = inLines[index]!;
      if (inLine === "") continue;
      const inRecord = JSON.parse(inLine) as RecordLine;
      const deep = inRecord.phase === "ready" && DEEP_PLIES.includes(inRecord.ply);
      if (!deep) {
        expect(outLines[index]).toBe(inLine);
        continue;
      }
      deepRows += 1;
      const outRecord = JSON.parse(outLines[index]!) as Record<string, unknown>;
      expect(Object.keys(outRecord)).toEqual([...Object.keys(inRecord), "engineReferenceDeep", "searchPvsDeep"]);
      const { engineReferenceDeep: _deep, searchPvsDeep: _pvs, ...rest } = outRecord;
      expect(rest).toEqual(inRecord);
      expect(outRecord.engineReference).toEqual(inRecord.engineReference);
    }
    expect(deepRows).toBe(DEEP_PLIES.length);
  });

  it("S-19: 読み直した行の searchPvsDeep と engineReferenceDeep は同じ measure 呼び出しの戻り値、measure の回数 = deepPlies の数、searchPvs は段 1 のまま", async () => {
    const source = stage1Source(records);
    const { calls, measure } = fakeMeasure();
    const outRecords = (await rescreenRecords(source, rule, measure, run()))
      .split("\n")
      .filter((line) => line.length > 0)
      .map((line) => JSON.parse(line) as RecordLine & { engineReferenceDeep?: unknown; searchPvsDeep?: unknown })
      .filter((line) => line.kind === "record" && line.phase === "ready");

    expect(calls).toHaveLength(DEEP_PLIES.length);
    for (const outRecord of outRecords) {
      const inRecord = records.find((record) => record.ply === outRecord.ply)!;
      expect(outRecord.searchPvs).toEqual(inRecord.searchPvs);
      const call = calls.indexOf(outRecord.sfen) + 1;
      if (!DEEP_PLIES.includes(outRecord.ply)) {
        expect(call).toBe(0);
        expect(Object.keys(outRecord)).not.toContain("engineReferenceDeep");
        expect(Object.keys(outRecord)).not.toContain("searchPvsDeep");
        continue;
      }
      expect(outRecord.engineReferenceDeep).toEqual({ ...engineRef(-1000 - call, { bestmove: `deep-best-${call}` }), nodes: DEEP });
      expect(outRecord.searchPvsDeep).toEqual([observation(`deep-call-${call}`, outRecord.sfen)]);
    }
  });

  it("測れなかった行は engineReferenceDeep が null(キーは残す)、searchPvsDeep は測った分(0 本なら [])", async () => {
    const source = stage1Source(stage1Records({ 10: engineRef(-300) }));
    const { measure } = fakeMeasure((sfen) => ({ reference: null, searchPvs: [] }));
    const text = await rescreenRecords(source, rule, measure, run());
    const deepLines = text.split("\n").filter((line) => line.includes('"engineReferenceDeep"'));
    expect(deepLines).toHaveLength(4);
    for (const line of deepLines) {
      const record = JSON.parse(line) as { engineReferenceDeep?: unknown; searchPvsDeep?: unknown };
      expect(record.engineReferenceDeep).toBeNull();
      expect(record.searchPvsDeep).toEqual([]);
    }
  });

  it("候補が無ければ measure を呼ばず、record 行はすべて段 1 のまま、screen の deepPlies と measuredOrder は空", async () => {
    const source = stage1Source(stage1Records({}));
    const { calls, measure } = fakeMeasure();
    const outLines = (await rescreenRecords(source, rule, measure, run())).split("\n");
    const inLines = source.toString("utf-8").split("\n");
    expect(calls).toEqual([]);
    expect(outLines.slice(1)).toEqual(inLines.slice(1));
    const screen = (JSON.parse(outLines[0]!) as { screen: { deepPlies: number[]; deepRun: { measuredOrder: number[] } } }).screen;
    expect(screen.deepPlies).toEqual([]);
    expect(screen.deepRun.measuredOrder).toEqual([]);
  });
});

// ---- 段 1 として受け付けない入力 ----

describe("STEP D-SCREEN-1 の入力の確かめ(書く前に止める)", () => {
  const records = stage1Records({ 10: engineRef(-300) });
  const cases: Array<[string, Buffer, string]> = [
    ["meta 行が無い", Buffer.from(`${records.map((record) => JSON.stringify(record)).join("\n")}\n`), "meta 行がちょうど 1 つではない(0 行)"],
    ["meta 行が 2 つ", Buffer.from(`${JSON.stringify(META)}\n${stage1Source(records).toString("utf-8")}`), "meta 行がちょうど 1 つではない(2 行)"],
    ["段 2 の記録(meta に screen)", stage1Source(records, { ...META, screen: { deepPlies: [] } }), "meta に screen がある"],
    ["meta に referenceNodes が無い", stage1Source(records, { ...META, referenceNodes: undefined }), "meta の referenceNodes が正の整数でない"],
    ["同じ ply の ready 行が 2 つ", stage1Source([...records, records[3]!]), "同じ ply の ready 行が 2 つ以上ある"],
  ];

  for (const [name, source, message] of cases) {
    it(`${name}: planRescreen も rescreenRecords も RescreenInputError で止まり、measure を呼ばない`, async () => {
      expect(() => planRescreen(source, rule)).toThrow(RescreenInputError);
      expect(() => planRescreen(source, rule)).toThrow(message);
      const { calls, measure } = fakeMeasure();
      await expect(rescreenRecords(source, rule, measure, run())).rejects.toThrow(message);
      expect(calls).toEqual([]);
    });
  }

  it("planRescreen は読み直す行と lightNodes を返す", () => {
    expect(planRescreen(stage1Source(records), rule)).toEqual({ deepPlies: [6, 8, 10, 12], lightNodes: LIGHT });
  });

  // STEP D-SCREEN-2(計画 §5 の 0. の床)
  it("allPlies: 候補を選ばず全 ready 行を ply の昇順に読み直し、measure は ready 行の数だけ呼ぶ(screen の rule はそのまま写し、rule の直後に allPlies: true を書く。床でなければキーを出さない)", async () => {
    const allPlies = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20];
    expect(planRescreen(stage1Source(records), rule, { allPlies: true })).toEqual({ deepPlies: allPlies, lightNodes: LIGHT });
    const { calls, measure } = fakeMeasure();
    const text = await rescreenRecords(stage1Source(records), rule, measure, run(), { allPlies: true });
    expect(calls).toHaveLength(allPlies.length);
    const screen = (JSON.parse(text.split("\n")[0]!) as { screen: { deepPlies: number[]; rule: unknown; allPlies?: boolean; deepRun: { measuredOrder: number[] } } }).screen;
    expect([screen.deepPlies, screen.deepRun.measuredOrder, screen.rule, screen.allPlies]).toEqual([allPlies, allPlies, DRAFT_SCREEN_RULE_1, true]);
    expect(Object.keys(screen).slice(0, 4)).toEqual(["lightNodes", "deepNodes", "rule", "allPlies"]);
    const plain = await rescreenRecords(stage1Source(records), rule, fakeMeasure().measure, run());
    expect(Object.hasOwn((JSON.parse(plain.split("\n")[0]!) as { screen: object }).screen, "allPlies")).toBe(false);
  });
});
