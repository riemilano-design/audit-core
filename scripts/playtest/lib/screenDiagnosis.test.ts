// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §3・§6・§11)。段 2 の記録(meta に screen を持つ記録)を診断で読むときの規則を見張る。
// 記録は GAME01 の実際の手順に、段 1 の軽い値(40 万ノード)と読み直しの深い値(400 万ノード)を植えたもの。**エンジンは使わない。**
// meta の screen は、不変条件(計画 §2・§11)を満たすように組む(読み直す行の選び方は D-SCREEN-1 の lib/rescreen.test.ts が見る)。

import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { EngineReference } from "../../../apps/server/src/analysis/engineReference.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { counterfactualLines, POSITION_FACTS_RULES, type Counterfactual } from "./counterfactual.js";
import { diagnosisMomentsOf, loadDiagnosisMomentSchema, toMomentLine } from "./diagnosisMoment.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import {
  buildDiagnosisReport,
  diagnoseRecords,
  DRAFT_RULE_1,
  NOT_EVALUATION_CP,
  pairEvaluations,
  readEvaluations,
  renderDiagnosisReport,
  STANDING_BOUNDS,
  type DiagnosisInput,
  type FailureEvent,
} from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { buildProvenance, loadFailureEventSchema, toEventLine } from "./failureEventSchema.js";
import { DRAFT_SCREEN_RULE_1, type ScreenMeta } from "./rescreen.js";
import { DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION, FAILURE_EVENT_SCHEMA_VERSION, FAILURE_EVENT_SCREEN_BASE_VERSION } from "./schemaVersions.js";
import { choosePairSources, screenInputConflicts } from "./screenDiagnosis.js";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const ENGINE_PATH = join(REPO_ROOT, "apps", "server", "engine", "nnue", "YaneuraOu-by-gcc");
const LIGHT = 400_000;
const DEEP = 4_000_000;
type Json = Record<string, unknown>;
const clone = (value: unknown): Json => JSON.parse(JSON.stringify(value)) as Json;

function focus(sfen: string, pv: readonly string[], bounds: { lowerbound?: boolean; upperbound?: boolean } = {}): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: 0, mate: null, pv: [...pv], lowerbound: bounds.lowerbound ?? false, upperbound: bounds.upperbound ?? false };
}

const deepRef = (scoreCp: number | null, options: Parameters<typeof engineRef>[1] = {}): EngineReference => ({ ...engineRef(scoreCp, options), nodes: DEEP });

interface DeepPlant {
  reference: EngineReference | null;
  pvs?: (sfen: string) => SearchPvObservation[];
}

interface Stage2 {
  kifuId: string;
  meta: MetaLine;
  records: RecordLine[];
  screen: ScreenMeta;
}

/**
 * 段 2 の記録を植える。`light` は段 1 の値(plantedRecords の形。ノード数は 40 万にする)、`deep` は読み直した行の値と読み筋。
 * 段 1 の③の読み筋は、`lightPvs` に無い行は `[]`(測ったが 0 本)。
 */
function stage2(
  light: Record<number, PlantedEvaluation>,
  deep: Record<number, DeepPlant>,
  lightPvs: Record<number, (sfen: string) => SearchPvObservation[]> = {},
  options: { kifuId?: string; moves?: readonly string[] } = {},
): Stage2 {
  const kifuId = options.kifuId ?? "s2";
  const deepPlies = Object.keys(deep)
    .map(Number)
    .sort((a, b) => a - b);
  const records = plantedRecords(options.moves ?? GAME01_MOVES, light).map((record): RecordLine => {
    const out: RecordLine = {
      ...record,
      ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: LIGHT } } : {}),
      searchPvs: lightPvs[record.ply]?.(record.sfen) ?? [],
    };
    const plant = deep[record.ply];
    if (plant !== undefined) {
      out.engineReferenceDeep = plant.reference;
      out.searchPvsDeep = plant.pvs?.(record.sfen) ?? [];
    }
    return out;
  });
  const screen: ScreenMeta = {
    lightNodes: LIGHT,
    deepNodes: DEEP,
    rule: DRAFT_SCREEN_RULE_1,
    deepPlies,
    sourceSha256: "a".repeat(64),
    deepRun: { gitHead: "deephead", dirty: false, enginePath: ENGINE_PATH, threads: 1, startedAt: "deep-start", order: "plyAscending", measuredOrder: deepPlies },
  };
  const meta = {
    kind: "meta",
    kifuId,
    startedAt: "t",
    gitHead: "stage1head",
    dirty: false,
    dirtyPaths: [],
    dirtyCount: 0,
    enginePath: ENGINE_PATH,
    searchMode: "nodes",
    nodes: LIGHT,
    threads: 1,
    referenceNodes: LIGHT,
    screen,
  } as unknown as MetaLine;
  return { kifuId, meta, records, screen };
}

const diagnosed = (s: Stage2) => diagnoseRecords(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, s.screen);
const eventAt = (events: readonly FailureEvent[], branchPly: number): FailureEvent => {
  const event = events.find((candidate) => candidate.branchPly === branchPly);
  if (event === undefined) throw new Error(`分岐点 ${branchPly} の Event が無い(${events.map((e) => e.branchPly).join(",")})`);
  return event;
};
const compared = (counterfactual: Counterfactual) => {
  if (counterfactual.state !== "compared") throw new Error(`compared でない: ${counterfactual.state}`);
  return counterfactual;
};
const inputOf = (s: Pick<Stage2, "kifuId" | "meta" | "records">): DiagnosisInput => ({ kifuId: s.kifuId, meta: s.meta, records: s.records, errorLines: [] });
const pairCount = (s: Stage2): number => readEvaluations(s.records).length - 1;

// ---- 組ごとの出どころ(計画 §3)----

describe("STEP D-SCREEN-2 の組ごとの出どころ(計画 §3)", () => {
  it("S-10: 軽い −396・深い −508 の組は、深い値で cpDrop になり evaluationSource は deep。直前の評価も深い行の値。軽い値だけなら急落候補にならない", () => {
    const s = stage2({ 20: engineRef(0), 22: engineRef(-396) }, { 20: { reference: deepRef(8) }, 22: { reference: deepRef(-508) } });
    const { events, screen } = diagnosed(s);
    expect(events.map((event) => event.branchPly)).toEqual([21]);
    const event = eventAt(events, 21);
    expect([event.branch.kinds, event.branch.diffCp, event.branch.evaluationSource]).toEqual([["cpDrop"], -516, "deep"]);
    expect(event.trigger.evaluationBefore).toMatchObject({ state: "measured", scoreCp: 8 });
    expect(event.branch.evaluationAfter).toMatchObject({ state: "measured", scoreCp: -508 });
    expect(diagnoseRecords(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).events).toEqual([]);
    expect(screen).toEqual({ lightNodes: LIGHT, deepNodes: DEEP, deepPlies: 2, deepPairs: 1, lightPairs: pairCount(s) - 1, deepUnavailable: 0 });
  });

  it("S-6: 深い行と軽いだけの行の組は、2 行とも軽い値(組の中で混ぜない)。evaluationSource は light", () => {
    const s = stage2({ 20: engineRef(0), 22: engineRef(-500) }, { 22: { reference: deepRef(-50) } });
    const pair = choosePairSources(readEvaluations(s.records)).find((candidate) => candidate.pair.fromPly === 20)!;
    expect([pair.source, pair.pair.kind === "compared" ? pair.pair.diffCp : null, pair.deepUnavailable]).toEqual(["light", -500, false]);
    const event = eventAt(diagnosed(s).events, 21);
    expect([event.branch.diffCp, event.branch.evaluationSource]).toEqual([-500, "light"]);
    expect(event.branch.evaluationAfter).toMatchObject({ state: "measured", scoreCp: -500 });
  });

  it("S-7: 深く測れなかった行(直前の組の直後の行)を含む組は、軽い値で比べ deepUnavailable 1。王手中で測らなかった行は deepUnavailable に数えない", () => {
    const s = stage2({ 18: engineRef(0), 20: engineRef(-500) }, { 18: { reference: deepRef(0) }, 20: { reference: null } }, {}, { moves: GAME01_MOVES.slice(0, 20) });
    const { events, screen } = diagnosed(s);
    expect([eventAt(events, 19).branch.diffCp, eventAt(events, 19).branch.evaluationSource]).toEqual([-500, "light"]);
    expect(screen).toMatchObject({ deepPairs: 0, deepUnavailable: 1 });

    // GAME01 の ply 34 は先手が王手中。読み直しても null(測らないと決めた)なので、深く測れなかった数に入れない
    const inCheck = stage2({}, { 32: { reference: deepRef(0) }, 34: { reference: null } });
    expect(choosePairSources(readEvaluations(inCheck.records)).filter((pair) => pair.deepUnavailable)).toEqual([]);
    expect(diagnosed(inCheck).screen).toMatchObject({ deepPairs: 0, deepUnavailable: 0 });
  });

  it("S-7b(X-2): 読み直した行が評価値でない(notEvaluation)組も、軽い値で比べ deepUnavailable 1", () => {
    const s = stage2({ 18: engineRef(0), 20: engineRef(-500) }, { 18: { reference: deepRef(0) }, 20: { reference: deepRef(40_000) } }, {}, { moves: GAME01_MOVES.slice(0, 20) });
    const { events, screen } = diagnosed(s);
    expect([eventAt(events, 19).branch.diffCp, eventAt(events, 19).branch.evaluationSource]).toEqual([-500, "light"]);
    expect(screen).toMatchObject({ deepPairs: 0, deepUnavailable: 1 });
  });

  it("行の状態の件数は段 1 の値、組の件数は組ごとの出どころで数える(設計 X-3)", () => {
    // 段 1 の ply 24 は評価値でない(40000)が、読み直すと測れた → 組 22→24 は深い値で比べる
    const s = stage2({ 24: engineRef(40_000) }, { 22: { reference: deepRef(0) }, 24: { reference: deepRef(-10) } });
    const { counts } = diagnosed(s);
    const lightOnly = diagnoseRecords(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).counts;
    expect([counts.notEvaluation, lightOnly.notEvaluation]).toEqual([1, 1]);
    expect(counts.comparedPairs).toBe(lightOnly.comparedPairs + 1);
    expect(counts.notComparedPairs).toBe(lightOnly.notComparedPairs - 1);
  });
});

// ---- 読み筋の出どころ(計画 §11)----

describe("STEP D-SCREEN-2 の読み筋の出どころ(計画 §11)", () => {
  const PV20 = GAME01_MOVES.slice(20, 40);
  const dropAt21 = (deep20: DeepPlant, lightPvs: Record<number, (sfen: string) => SearchPvObservation[]> = {}) =>
    stage2({ 20: engineRef(0, { bestmove: "9g9f" }), 22: engineRef(-500) }, { 20: deep20, 22: { reference: deepRef(-500) } }, lightPvs);

  it("S-15: 深い組は searchPvsDeep の focus_baseline(20 手)を使い、N = 6・pvLength 20・pvSource deep・1 手目は深い bestmove と同じ。pvSource は state の直後", () => {
    const s = dropAt21(
      { reference: deepRef(0, { bestmove: PV20[0]! }), pvs: (sfen) => [focus(sfen, PV20)] },
      { 20: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 22), { upperbound: true })] },
    );
    const counterfactual = compared(eventAt(diagnosed(s).events, 21).counterfactual);
    expect([counterfactual.pvSource, counterfactual.comparedPlies, counterfactual.pvLength, counterfactual.pvFirstMoveIsBestmoveAtBefore, counterfactual.pvBounded]).toEqual([
      "deep",
      6,
      20,
      true,
      { lowerbound: false, upperbound: false },
    ]);
    expect(Object.keys(counterfactual).slice(0, 2)).toEqual(["state", "pvSource"]);
  });

  it("S-15b: 深い組で、深い bestmove と searchPvsDeep の 1 手目が違えば pvFirstMoveIsBestmoveAtBefore は false(比べてから書く)", () => {
    const s = dropAt21({ reference: deepRef(0, { bestmove: "9g9f" }), pvs: (sfen) => [focus(sfen, PV20)] });
    const counterfactual = compared(eventAt(diagnosed(s).events, 21).counterfactual);
    expect([counterfactual.pvSource, counterfactual.pvFirstMoveIsBestmoveAtBefore]).toEqual(["deep", false]);
  });

  it("S-16: screen のある記録の軽い組(読み直していない行・深く測れなかった行を含む組)は searchPvs を使い、pvSource は light", () => {
    const notRemeasured = stage2(
      { 20: engineRef(0), 22: engineRef(-500) },
      { 22: { reference: deepRef(-500), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(22, 42))] } },
      { 20: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 26), { lowerbound: true })] },
    );
    const a = compared(eventAt(diagnosed(notRemeasured).events, 21).counterfactual);
    expect([a.pvSource, a.pvLength, a.pvBounded.lowerbound]).toEqual(["light", 6, true]);

    const failed = stage2(
      { 18: engineRef(0), 20: engineRef(-500) },
      { 18: { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(18, 38))] }, 20: { reference: null } },
      { 18: (sfen) => [focus(sfen, GAME01_MOVES.slice(18, 20), { upperbound: true })] },
    );
    const b = compared(eventAt(diagnosed(failed).events, 19).counterfactual);
    expect([b.pvSource, b.pvLength, b.pvBounded.upperbound]).toEqual(["light", 2, true]);
  });

  it("S-17: 深い組で searchPvsDeep も 2 手・upperbound なら N = 2・pvSource deep・pvBounded.upperbound true(軽いほうへ戻らない)", () => {
    const s = dropAt21(
      { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 22), { upperbound: true })] },
      { 20: (sfen) => [focus(sfen, PV20)] },
    );
    const counterfactual = compared(eventAt(diagnosed(s).events, 21).counterfactual);
    expect([counterfactual.pvSource, counterfactual.comparedPlies, counterfactual.pvBounded.upperbound]).toEqual(["deep", 2, true]);
  });

  it("S-18: 深い組で searchPvsDeep が [] なら noFocusBaseline・pvSource deep(軽い読み筋があっても戻らない)", () => {
    const s = dropAt21({ reference: deepRef(0) }, { 20: (sfen) => [focus(sfen, PV20)] });
    expect(eventAt(diagnosed(s).events, 21).counterfactual).toEqual({ state: "noFocusBaseline", pvSource: "deep" });
  });
});

// ---- diagnosis-moment(計画 §3・§11)----

describe("STEP D-SCREEN-2 の最大の下がりと上がり(計画 §3・§11)", () => {
  const momentsOf = (s: Stage2) => diagnosisMomentsOf(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, diagnosed(s).events, s.screen);

  it("S-13: 比べた組に深い組と軽い組が混ざる局は、全部の組を軽い値で選ぶ(深い −700 ではなく軽い −300)", () => {
    const s = stage2({ 10: engineRef(0), 12: engineRef(-100), 16: engineRef(0), 18: engineRef(-300) }, { 10: { reference: deepRef(0) }, 12: { reference: deepRef(-700) } });
    const { maxDrop } = momentsOf(s);
    if (!("change" in maxDrop)) throw new Error("組の行でない");
    expect([maxDrop.branchPly, maxDrop.change, maxDrop.evaluationSource]).toEqual([17, { kind: "cp", diffCp: -300 }, "light"]);
  });

  it("N-1(X-7): 混ざる局の excludedPairs は、全部の組を軽い値で作り直した組で数える(組ごとの出どころの組では数えない)", () => {
    // 組 20→22: 軽い値は直後が詰まされる読み(mateAfter −3 = mateDrop)、深い値は比べられる(−50)。16→18 は軽い組の compared → 出どころが混ざる
    const s = stage2(
      { 10: engineRef(0), 12: engineRef(-100), 16: engineRef(0), 18: engineRef(-300), 22: engineRef(null, { mate: -3 }) },
      { 20: { reference: deepRef(0) }, 22: { reference: deepRef(-50) } },
    );
    const light = pairEvaluations(readEvaluations(s.records));
    expect(choosePairSources(readEvaluations(s.records)).filter((chosen) => chosen.pair.kind === "mateAfter")).toEqual([]);
    const { maxDrop } = momentsOf(s);
    if (!("change" in maxDrop)) throw new Error("組の行でない");
    expect([maxDrop.branchPly, maxDrop.change, maxDrop.evaluationSource]).toEqual([17, { kind: "cp", diffCp: -300 }, "light"]);
    expect(maxDrop.excludedPairs).toEqual({ mateDrop: 1, mateRise: 0, notCompared: light.filter((pair) => pair.kind === "notCompared").length });
  });

  it("比べた組の出どころが 1 種類なら、その値で選ぶ(全部の行を読み直した局は深い値、読み直した行が無い局は軽い値)", () => {
    const allDeep: Record<number, DeepPlant> = {};
    for (const record of plantedRecords(GAME01_MOVES, {})) allDeep[record.ply] = { reference: record.engineReference === null ? null : deepRef(record.ply === 22 ? -800 : 0) };
    const deep = momentsOf(stage2({ 22: engineRef(-100) }, allDeep)).maxDrop;
    if (!("change" in deep)) throw new Error("組の行でない");
    expect([deep.branchPly, deep.change, deep.evaluationSource]).toEqual([21, { kind: "cp", diffCp: -800 }, "deep"]);

    const none = momentsOf(stage2({ 22: engineRef(-100) }, {})).maxDrop;
    if (!("change" in none)) throw new Error("組の行でない");
    expect([none.branchPly, none.change, none.evaluationSource]).toEqual([21, { kind: "cp", diffCp: -100 }, "light"]);
  });

  it("S-20: 混ざる局で選んだ maxDrop の組の 2 行が深く測れていても、evaluationSource は light なので searchPvs を使い pvSource は light", () => {
    const s = stage2(
      { 10: engineRef(0), 12: engineRef(-600), 16: engineRef(0), 18: engineRef(-300) },
      { 10: { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(10, 30))] }, 12: { reference: deepRef(-100) } },
      { 10: (sfen) => [focus(sfen, GAME01_MOVES.slice(10, 12), { lowerbound: true })] },
    );
    const { maxDrop } = momentsOf(s);
    if (!("change" in maxDrop)) throw new Error("組の行でない");
    expect([maxDrop.branchPly, maxDrop.change, maxDrop.evaluationSource]).toEqual([11, { kind: "cp", diffCp: -600 }, "light"]);
    const counterfactual = compared(maxDrop.counterfactual);
    expect([counterfactual.pvSource, counterfactual.pvLength, counterfactual.pvBounded.lowerbound]).toEqual(["light", 2, true]);
  });

  it("S-21: 深い組の rise は searchPvsDeep を使い、evaluationSource・pvSource とも deep。軽い値だけなら rise にならない", () => {
    const s = stage2(
      { 10: engineRef(0), 12: engineRef(0) },
      { 10: { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(10, 16))] }, 12: { reference: deepRef(500) } },
    );
    const { rises } = momentsOf(s);
    expect(rises.map((rise) => [rise.branchPly, rise.change, rise.evaluationSource])).toEqual([[11, { kind: "cp", diffCp: 500 }, "deep"]]);
    const counterfactual = compared(rises[0]!.counterfactual);
    expect([counterfactual.pvSource, counterfactual.pvLength]).toEqual(["deep", 6]);
    expect(diagnosisMomentsOf(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, []).rises).toEqual([]);
  });
});

// ---- 数えない記録(計画 §2・§11、S-8・S-23)----

describe("STEP D-SCREEN-2 の数えない記録(S-8・S-23)", () => {
  const base = () => stage2({ 20: engineRef(0), 22: engineRef(-500) }, { 20: { reference: deepRef(0) }, 22: { reference: deepRef(-500) } });
  const screenOf = (s: Stage2) => (s.meta as unknown as { screen: Json }).screen;
  const recordAt = (s: Stage2, ply: number) => s.records.find((record) => record.phase === "ready" && record.ply === ply)!;
  const cases: Array<[string, (s: Stage2) => void, string]> = [
    ["deepPlies と深い欄のある行が違う", (s) => (screenOf(s).deepPlies = [20]), "深い欄を持つ ready 行(20,22)が screen.deepPlies(20)と違う"],
    ["measuredOrder が deepPlies と違う", (s) => ((screenOf(s).deepRun as Json).measuredOrder = [20]), "screen.deepRun.measuredOrder(20)が screen.deepPlies と同じ行の集まりでない"],
    ["engineReference.nodes が lightNodes と違う", (s) => (recordAt(s, 24).engineReference = { ...recordAt(s, 24).engineReference!, nodes: DEEP }), "ply 24 の engineReference.nodes が 4000000(screen.lightNodes は 400000)"],
    ["engineReferenceDeep.nodes が deepNodes と違う", (s) => (recordAt(s, 22).engineReferenceDeep = { ...recordAt(s, 22).engineReferenceDeep!, nodes: LIGHT }), "ply 22 の engineReferenceDeep.nodes が 400000(screen.deepNodes は 4000000)"],
    ["S-23: engineReferenceDeep があり searchPvsDeep が無い", (s) => delete recordAt(s, 22).searchPvsDeep, "ply 22 の engineReferenceDeep と searchPvsDeep の欄の有無が食い違う"],
    ["S-23: searchPvsDeep があり engineReferenceDeep が無い", (s) => (recordAt(s, 26).searchPvsDeep = []), "ply 26 の engineReferenceDeep と searchPvsDeep の欄の有無が食い違う"],
    ["screen が無いのに深い欄がある", (s) => delete (s.meta as unknown as Json).screen, "meta に screen が無いのに、深い欄を持つ行がある(ply 20,22)"],
    ["screen の形が違う", (s) => (screenOf(s).sourceSha256 = "XYZ"), "screen.sourceSha256 が 64 桁の小文字の 16 進でない"],
    ["ready でない行に深い欄がある", (s) => s.records.push({ ...recordAt(s, 24), phase: "immediate", engineReferenceDeep: null, searchPvsDeep: [] }), "ready でない行(ply 24)に深い欄がある"],
    ["screen.allPlies が true でない", (s) => (screenOf(s).allPlies = false), "screen.allPlies が true でない"],
  ];

  it("前提: 形の揃った段 2 の記録は数え、screen の件数を持つ", () => {
    const result = buildDiagnosisReport([inputOf(base())], DRAFT_RULE_1)[0]!.result;
    expect(result.kind).toBe("counted");
    expect(result.kind === "counted" && result.screen).toMatchObject({ deepPlies: 2, deepPairs: 1 });
  });

  it("床の段 2(screen.allPlies が true)は数える", () => {
    const s = base();
    screenOf(s).allPlies = true;
    expect(buildDiagnosisReport([inputOf(s)], DRAFT_RULE_1)[0]!.result.kind).toBe("counted");
  });

  for (const [name, change, message] of cases) {
    it(`${name}: InvalidScreenRecordError で「数えられなかった」にする`, () => {
      const s = base();
      change(s);
      const result = buildDiagnosisReport([inputOf(s)], DRAFT_RULE_1)[0]!.result;
      expect(result.kind).toBe("notCounted");
      if (result.kind !== "notCounted") return;
      expect(result.errorName).toBe("InvalidScreenRecordError");
      expect(result.message).toContain(`記録 s2 は段 2 の記録の不変条件(計画 §2・§11)を満たさない: `);
      expect(result.message).toContain(message);
    });
  }
});

// ---- Markdown(計画 §11・S-22・K-8)----

describe("STEP D-SCREEN-2 の Markdown(S-22・K-8)", () => {
  const OLD_HEADING = "## 実戦の続きと読み筋(STEP D2。事実の並びだけ。読み筋は③の探索で、急落を見つけた評価とは別の探索)";
  const withDeepAndLight = (kifuId = "s2") =>
    stage2(
      { 20: engineRef(0), 22: engineRef(-500), 44: engineRef(0), 46: engineRef(-500) },
      { 20: { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 40))] }, 22: { reference: deepRef(-500) } },
      {},
      { kifuId },
    );

  it("S-22: 深い Event と軽い Event が 1 件ずつの記録は、見出しに light 1・deep 1、深い行は「読み直しの探索(評価値と同じ探索)」で「③の探索」を含まず、軽い行は③の探索。読み直しの節に件数", () => {
    const s = withDeepAndLight();
    const lines = renderDiagnosisReport(buildDiagnosisReport([inputOf(s)], DRAFT_RULE_1));
    expect(lines).toContain("## 実戦の続きと読み筋(STEP D2・D-SCREEN。事実の並びだけ。軽い組の読み筋は③の探索、深い組の読み筋は読み直しの探索(評価値と同じ探索)。light 1 件・deep 1 件)");
    expect(lines).not.toContain(OLD_HEADING);
    const deepLines = lines.filter((line) => line.startsWith("- s2 分岐点 21 "));
    expect(deepLines).toHaveLength(2);
    expect(deepLines[1]).toContain("読み筋(読み直しの探索(評価値と同じ探索)・6 手 = 分岐の手 + 5 手・");
    expect(deepLines.join("\n")).not.toContain("③の探索");
    expect(lines.filter((line) => line.startsWith("- s2 分岐点 45 "))).toEqual(["- s2 分岐点 45 読み筋: ③の現局面の読み筋が無い"]);
    expect(lines).toContain("## 読み直し(STEP D-SCREEN。meta に screen のある記録だけ)");
    expect(lines).toContain(`| s2 | 400000 | 4000000 | 2 | 1 | ${pairCount(s) - 1} | 0 |`);
  });

  it("N-4: screen のある記録の軽い組の compared は、読み筋の行頭が「③の探索」(pvSource light)", () => {
    const s = stage2(
      { 20: engineRef(0), 22: engineRef(-500), 44: engineRef(0), 46: engineRef(-500) },
      { 20: { reference: deepRef(0) }, 22: { reference: deepRef(-500) } },
      { 44: (sfen) => [focus(sfen, GAME01_MOVES.slice(44, 46))] },
    );
    const counterfactual = eventAt(diagnosed(s).events, 45).counterfactual;
    expect([counterfactual.state, counterfactual.pvSource]).toEqual(["compared", "light"]);
    const lines = counterfactualLines("s2", 45, counterfactual);
    expect(lines).toHaveLength(2);
    expect(lines[1]).toContain("- s2 分岐点 45 読み筋(③の探索・");
    expect(lines.join("\n")).not.toContain("読み直しの探索");
  });

  it("深い組の compared でない状態は、読み直しの探索と書き、noFocusBaseline の文から「③の」を外す", () => {
    expect(counterfactualLines("k", 1, { state: "noFocusBaseline", pvSource: "deep" })).toEqual(["- k 分岐点 1 読み筋(読み直しの探索(評価値と同じ探索)): 現局面の読み筋が無い"]);
    expect(counterfactualLines("k", 1, { state: "noFocusBaseline", pvSource: "light" })).toEqual(["- k 分岐点 1 読み筋: ③の現局面の読み筋が無い"]);
  });

  it("K-8: screen のある記録と無い記録を混ぜると、見出しの light・deep は screen のある記録だけを数え、無い記録の件数を分けて足す。読み直しの節に無い記録の名前と、2 本以上なら合計", () => {
    const plain = plantedRecords(GAME01_MOVES, { 30: engineRef(0), 32: engineRef(-500) });
    const a = withDeepAndLight("s2a");
    const b = withDeepAndLight("s2b");
    const lines = renderDiagnosisReport(
      buildDiagnosisReport([inputOf(a), inputOf(b), { kifuId: "plain", meta: undefined, records: plain, errorLines: [] }], DRAFT_RULE_1),
    );
    expect(lines).toContain(
      "## 実戦の続きと読み筋(STEP D2・D-SCREEN。事実の並びだけ。軽い組の読み筋は③の探索、深い組の読み筋は読み直しの探索(評価値と同じ探索)。light 2 件・deep 2 件・screen の無い記録 1 件)",
    );
    expect(lines).toContain("- screen の無い記録(読み直していない): plain");
    expect(lines).toContain(`| 合計 | - | - | 4 | 2 | ${2 * (pairCount(a) - 1)} | 0 |`);
  });

  it("S-9 の Markdown: screen の無い記録だけなら、見出しは今の文で、読み直しの節は出ない", () => {
    const plain = plantedRecords(GAME01_MOVES, { 30: engineRef(0), 32: engineRef(-500) });
    const lines = renderDiagnosisReport(buildDiagnosisReport([{ kifuId: "plain", meta: undefined, records: plain, errorLines: [] }], DRAFT_RULE_1));
    expect(lines).toContain(OLD_HEADING);
    expect(lines.some((line) => line.startsWith("## 読み直し"))).toBe(false);
  });
});

// ---- 行(JSON)とスキーマ(計画 §3 の版)----

describe("STEP D-SCREEN-2 の行とスキーマ(Failure Event v0.6・diagnosis-moment v0.3 として書く)", () => {
  const feSchema = loadFailureEventSchema();
  const momentSchema = loadDiagnosisMomentSchema();
  const provenanceOf = (meta: MetaLine | undefined) =>
    buildProvenance({
      recordPath: join(REPO_ROOT, "scripts", "playtest", "records", "s2.jsonl"),
      recordSha256: "0".repeat(64),
      meta,
      evaluator: null,
      analysisGit: { gitHead: null, dirty: null },
      rule: DRAFT_RULE_1,
      notEvaluationCp: NOT_EVALUATION_CP,
      standingBounds: STANDING_BOUNDS,
      positionFactsRules: POSITION_FACTS_RULES,
      repoRoot: REPO_ROOT,
    });

  it("段 2 の Event の 1 行は、branch.evaluationSource・counterfactual.pvSource・provenance.record.meta.screen(deepPlies・measuredOrder を除く、エンジンは根からの相対、dirty は 4 値)を持ち、今の版のスキーマを通る", () => {
    const s = stage2(
      { 20: engineRef(0), 22: engineRef(-500), 44: engineRef(0), 46: engineRef(-500) },
      { 20: { reference: deepRef(0), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 40))] }, 22: { reference: deepRef(-500) } },
    );
    const provenance = provenanceOf(s.meta);
    const meta = provenance.record.meta!;
    expect(Object.keys(meta)).toEqual(["gitHead", "dirty", "enginePath", "searchMode", "nodes", "threads", "screen", "unrecordedKeys"]);
    expect(meta.screen).toEqual({
      lightNodes: LIGHT,
      deepNodes: DEEP,
      rule: DRAFT_SCREEN_RULE_1,
      sourceSha256: "a".repeat(64),
      deepRun: { gitHead: "deephead", dirty: "clean", enginePath: "apps/server/engine/nnue/YaneuraOu-by-gcc", threads: 1, startedAt: "deep-start", order: "plyAscending" },
    });
    const { events } = diagnosed(s);
    expect(events.map((event) => [event.branchPly, event.branch.evaluationSource, event.counterfactual.pvSource])).toEqual([
      [21, "deep", "deep"],
      [45, "light", "light"],
    ]);
    for (const event of events) {
      const line = clone(toEventLine(event, provenance));
      expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
      expect(validate(line, feSchema), String(event.branchPly)).toEqual([]);
    }
    const moments = diagnosisMomentsOf(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events, s.screen);
    for (const moment of [...moments.rises, moments.maxDrop]) expect(validate(clone(toMomentLine(moment, provenance)), momentSchema)).toEqual([]);
  });

  it("N-5(X-8): Event の branch では evaluationSource が最後、moment の組の行では standingPair の直後", () => {
    const s = stage2({ 10: engineRef(0), 12: engineRef(0), 20: engineRef(0), 22: engineRef(-500) }, { 10: { reference: deepRef(0) }, 12: { reference: deepRef(500) } });
    const { events } = diagnosed(s);
    const branchKeys = Object.keys(eventAt(events, 21).branch);
    expect(branchKeys[branchKeys.length - 1]).toBe("evaluationSource");
    const { rises, maxDrop } = diagnosisMomentsOf(s.kifuId, s.records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events, s.screen);
    expect(rises.map((rise) => rise.evaluationSource)).toEqual(["deep", "light"]);
    for (const moment of [...rises, maxDrop]) {
      const keys = Object.keys(moment);
      expect(keys.indexOf("standingPair")).toBeGreaterThan(-1);
      expect(keys[keys.indexOf("standingPair") + 1]).toBe("evaluationSource");
    }
  });

  it("S-9 の行: screen の無い記録の Event と moment は evaluationSource・pvSource を持たず、出どころの meta に screen が無い", () => {
    const records = plantedRecords(GAME01_MOVES, { 30: engineRef(0), 32: engineRef(-500) });
    const { events } = diagnoseRecords("plain", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const meta = { kind: "meta", kifuId: "plain", startedAt: "t", gitHead: "g", dirty: false, enginePath: ENGINE_PATH, searchMode: "nodes", nodes: DEEP, threads: 1 } as MetaLine;
    const provenance = provenanceOf(meta);
    expect(Object.keys(provenance.record.meta!)).not.toContain("screen");
    const moments = diagnosisMomentsOf("plain", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events);
    const lines = [...events.map((event) => JSON.stringify(toEventLine(event, provenance))), ...[...moments.rises, moments.maxDrop].map((moment) => JSON.stringify(toMomentLine(moment, provenance)))];
    expect(lines.length).toBeGreaterThan(1);
    for (const line of lines) {
      expect(line).not.toContain('"evaluationSource"');
      expect(line).not.toContain('"pvSource"');
      expect(line).not.toContain('"screen"');
    }
  });

  it("今の版の Failure Event のスキーマは、基の版に D-SCREEN の任意の欄を足しただけ(版の値・$id・title・description のほかは同じ)", () => {
    const current = clone(feSchema);
    const baseSchema = clone(loadFailureEventSchema(FAILURE_EVENT_SCREEN_BASE_VERSION));
    const properties = current.properties as Json;
    delete ((properties.branch as Json).properties as Json).evaluationSource;
    for (const branch of (properties.counterfactual as { oneOf: Json[] }).oneOf) delete (branch.properties as Json).pvSource;
    for (const variant of (((((properties.provenance as Json).properties as Json).record as Json).properties as Json).meta as { oneOf: Json[] }).oneOf) {
      if (variant.properties) delete (variant.properties as Json).screen;
    }
    expect(properties.schemaVersion).toEqual({ const: FAILURE_EVENT_SCHEMA_VERSION });
    properties.schemaVersion = { const: FAILURE_EVENT_SCREEN_BASE_VERSION };
    for (const key of ["$id", "title", "description"]) current[key] = baseSchema[key];
    expect(current).toEqual(baseSchema);
  });

  it("今の版の diagnosis-moment のスキーマは、基の版の組の行に evaluationSource と pvSource を足し、provenance を今の版の Failure Event から写しただけ", () => {
    const current = clone(momentSchema);
    const baseSchema = clone(loadDiagnosisMomentSchema(DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION));
    const baseProvenance = (clone(loadFailureEventSchema(FAILURE_EVENT_SCREEN_BASE_VERSION)).properties as Json).provenance;
    const currentProvenance = (clone(feSchema).properties as Json).provenance;
    for (const variant of current.oneOf as Json[]) {
      const properties = variant.properties as Json;
      expect(properties.provenance).toEqual(currentProvenance);
      properties.provenance = baseProvenance;
      properties.schemaVersion = { ...(properties.schemaVersion as Json), const: DIAGNOSIS_MOMENT_SCREEN_BASE_VERSION };
      delete properties.evaluationSource;
      if (properties.counterfactual) for (const branch of (properties.counterfactual as { oneOf: Json[] }).oneOf) delete (branch.properties as Json).pvSource;
    }
    for (const key of ["$id", "title", "description"]) current[key] = baseSchema[key];
    expect(current).toEqual(baseSchema);
  });

  it("スキーマの境目(手で書き換えた 1 行): evaluationSource・pvSource の知らない値、screen の欄の欠け・写さない欄(deepPlies)・大文字の sha・dirty の boolean は落ちる", () => {
    const s = stage2({ 20: engineRef(0), 22: engineRef(-500) }, { 20: { reference: deepRef(0) }, 22: { reference: deepRef(-500) } });
    const line = clone(toEventLine(eventAt(diagnosed(s).events, 21), provenanceOf(s.meta)));
    expect(validate(line, feSchema)).toEqual([]);
    const changed = (change: (copy: Json) => void): Json => {
      const copy = clone(line);
      change(copy);
      return copy;
    };
    const screenIn = (copy: Json) => (((copy.provenance as Json).record as Json).meta as Json).screen as Json;
    const failing: Array<[string, Json]> = [
      ["evaluationSource が medium", changed((c) => ((c.branch as Json).evaluationSource = "medium"))],
      ["pvSource が both", changed((c) => ((c.counterfactual as Json).pvSource = "both"))],
      ["screen に deepRun が無い", changed((c) => delete screenIn(c).deepRun)],
      ["screen に deepPlies", changed((c) => (screenIn(c).deepPlies = [20, 22]))],
      ["screen の sha が大文字", changed((c) => (screenIn(c).sourceSha256 = "A".repeat(64)))],
      ["deepRun.dirty が boolean", changed((c) => ((screenIn(c).deepRun as Json).dirty = false))],
      ["deepRun.order が別の値", changed((c) => ((screenIn(c).deepRun as Json).order = "measured"))],
    ];
    for (const [name, broken] of failing) expect(validate(broken, feSchema as JsonSchema), name).not.toEqual([]);
  });
});

// ---- 段 2 とその段 1(計画 §3・S-14 の lib)----

describe("STEP D-SCREEN-2 の段 2 とその段 1(S-14)", () => {
  const plainMeta = { kind: "meta", kifuId: "k", startedAt: "t", gitHead: null, enginePath: "/e" } as MetaLine;
  const screenMeta = (sourceSha256: string, kifuId = "k") => ({ ...plainMeta, kifuId, screen: { sourceSha256 } }) as unknown as MetaLine;
  const B = "b".repeat(64);
  const C = "c".repeat(64);
  const D = "d".repeat(64);

  it("(i) 段 2 の sourceSha256 と同じ sha の入力 (ii) 同じ kifuId に screen のある入力と無い入力、をそれぞれ 1 文で返す", () => {
    expect(
      screenInputConflicts([
        { name: "stage1.jsonl", kifuId: "k", sha256: B, meta: plainMeta },
        { name: "stage2.jsonl", kifuId: "k", sha256: C, meta: screenMeta(B) },
      ]),
    ).toEqual([
      "段 2 の記録 stage2.jsonl と、その段 1 の記録 stage1.jsonl を一緒に渡している(screen.sourceSha256 が一致)",
      "同じ kifuId k に、screen のある記録(stage2.jsonl)と無い記録(stage1.jsonl)を一緒に渡している",
    ]);
    expect(
      screenInputConflicts([
        { name: "other-id.jsonl", kifuId: "x", sha256: B, meta: plainMeta },
        { name: "stage2.jsonl", kifuId: "k", sha256: C, meta: screenMeta(B) },
      ]),
    ).toEqual(["段 2 の記録 stage2.jsonl と、その段 1 の記録 other-id.jsonl を一緒に渡している(screen.sourceSha256 が一致)"]);
    expect(
      screenInputConflicts([
        { name: "a.jsonl", kifuId: "k", sha256: B, meta: plainMeta },
        { name: "b.jsonl", kifuId: "k", sha256: C, meta: screenMeta(D) },
      ]),
    ).toEqual(["同じ kifuId k に、screen のある記録(b.jsonl)と無い記録(a.jsonl)を一緒に渡している"]);
  });

  it("(iii) screen の無い同じ kifuId の 3 本、screen のある同じ kifuId の 2 本(段 1 が別)は止めない", () => {
    expect(screenInputConflicts(["c4m", "l100k", "l400k"].map((dir, i) => ({ name: `${dir}.jsonl`, kifuId: "k", sha256: String(i).repeat(64), meta: plainMeta })))).toEqual([]);
    expect(
      screenInputConflicts([
        { name: "a.jsonl", kifuId: "k", sha256: B, meta: screenMeta(D) },
        { name: "b.jsonl", kifuId: "k", sha256: C, meta: screenMeta("e".repeat(64)) },
      ]),
    ).toEqual([]);
  });
});
