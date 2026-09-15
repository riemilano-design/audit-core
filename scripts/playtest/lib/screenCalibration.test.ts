// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §5・§11 の床)。校正で数える純粋関数を見張る。**エンジンは使わない。**
// 記録は GAME01 の実際の手順に評価を植えたもの。比べる相手(4M 一律)は screen の無い記録、段 2 は meta に screen を持つ記録。

import { describe, expect, it } from "vitest";
import type { EngineReference, EngineReferenceMeasurement } from "../../../apps/server/src/analysis/engineReference.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { DRAFT_RULE_1, type EvaluationPair, type FailureEvent, type NotComparedReason } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { DRAFT_SCREEN_RULE_1, type ScreenMeta } from "./rescreen.js";
import {
  compareDeepRows,
  compareEventSets,
  compareMeasurementPair,
  compareRescreenRuns,
  compareWithStage2,
  planMeasureTwice,
  renderScreenCalibration,
  type StageRow,
} from "./screenCalibration.js";

const LIGHT = 400_000;
const DEEP = 4_000_000;

function focus(sfen: string, pv: readonly string[], bounds: { lowerbound?: boolean; upperbound?: boolean } = {}): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: 0, mate: null, pv: [...pv], lowerbound: bounds.lowerbound ?? false, upperbound: bounds.upperbound ?? false };
}
const at = (nodes: number) => (scoreCp: number | null, options: Parameters<typeof engineRef>[1] = {}): EngineReference => ({ ...engineRef(scoreCp, options), nodes });

/** 比べる相手(4M 一律): 全 ready 行に searchPvs [] を持たせる(counterfactual は noFocusBaseline になる) */
function uniform(plant: Record<number, PlantedEvaluation>, pvs: Record<number, (sfen: string) => SearchPvObservation[]> = {}): { meta: MetaLine; records: RecordLine[] } {
  const records = plantedRecords(GAME01_MOVES, plant).map((record): RecordLine => ({ ...record, searchPvs: pvs[record.ply]?.(record.sfen) ?? [] }));
  return { meta: { kind: "meta", kifuId: "cal", startedAt: "t", gitHead: null, enginePath: "/e", searchMode: "nodes", nodes: DEEP, threads: 1 } as MetaLine, records };
}

function stage2(
  light: Record<number, PlantedEvaluation>,
  deep: Record<number, { reference: EngineReference | null; pvs?: (sfen: string) => SearchPvObservation[] }>,
): { meta: MetaLine; records: RecordLine[] } {
  const deepPlies = Object.keys(deep)
    .map(Number)
    .sort((a, b) => a - b);
  const records = plantedRecords(GAME01_MOVES, light).map((record): RecordLine => {
    const out: RecordLine = { ...record, ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: LIGHT } } : {}), searchPvs: [] };
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
    deepRun: { gitHead: "g", dirty: false, enginePath: "/e", threads: 1, startedAt: "t", order: "plyAscending", measuredOrder: deepPlies },
  };
  return { meta: { kind: "meta", kifuId: "cal", startedAt: "t", gitHead: null, enginePath: "/e", referenceNodes: LIGHT, screen } as unknown as MetaLine, records };
}

describe("STEP D-SCREEN-2 の校正: Failure Event の集合と読み筋(§5 の 1.・§11 の (vii))", () => {
  // 相手(4M 一律): 21 に急落(−500)、45 に急落(−500)
  // 段 2: 21 は深い組(−508、読み筋は標識付きで 1 手目が深い bestmove と違う)、45 は軽い −300 で急落にならない(取りこぼし)、
  //       11 は深い組で −600(相手に無い = 余計)
  const base = uniform({ 20: engineRef(0), 22: engineRef(-500), 44: engineRef(0), 46: engineRef(-500) });
  const s2 = stage2(
    { 20: engineRef(0), 22: engineRef(-396), 44: engineRef(0), 46: engineRef(-300) },
    {
      10: { reference: at(DEEP)(0) },
      12: { reference: at(DEEP)(-600) },
      20: { reference: at(DEEP)(0, { bestmove: "9g9f" }), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(20, 40), { upperbound: true })] },
      22: { reference: at(DEEP)(-508) },
    },
  );

  it("(branchPly, kinds) で一致・取りこぼし・余計を数え、counterfactual の状態の一致を pvSource ごとに、深い組の 1 手目を標識で分けて数える", () => {
    const c = compareWithStage2("cal", base, s2, DRAFT_RULE_1);
    // 45: 段 2 の同じ組 44→46 は軽い値で比べた(−300)→ 取りこぼし。11: 相手の同じ組 10→12 は比べた(0)→ 余計
    expect(c.events).toEqual({
      base: 2,
      stage2: 2,
      common: 1,
      kindsDiffer: [],
      missed: ["45:cpDrop"],
      missedUncomparable: [],
      extra: ["11:cpDrop"],
      extraUncomparable: [],
      missRate: { numerator: 1, denominator: 2 },
      extraRate: { numerator: 1, denominator: 2 },
    });
    // 21: 相手は noFocusBaseline、段 2 は compared → 一致 0 / 比べた 1(deep)。11 は相手に無いので分母に入れない
    expect(c.counterfactualState).toEqual({ light: { numerator: 0, denominator: 0 }, deep: { numerator: 0, denominator: 1 } });
    // 深い組の compared は 21 だけ(11 は読み筋 [] で noFocusBaseline)。1 手目 ≠ 深い bestmove・標識付き
    expect(c.deepFirstMove).toEqual({ notBestmove: { numerator: 1, denominator: 1 }, boundedNotBestmove: { numerator: 1, denominator: 1 }, unboundedNotBestmove: { numerator: 0, denominator: 0 } });
    expect(c.screen).toMatchObject({ deepPlies: 4, deepPairs: 2, deepUnavailable: 0 });
  });

  it("相手と段 2 で counterfactual の状態が同じなら一致に数える(light の組)", () => {
    const light = stage2({ 20: engineRef(0), 22: engineRef(-500) }, {});
    expect(compareWithStage2("cal", uniform({ 20: engineRef(0), 22: engineRef(-500) }), light, DRAFT_RULE_1).counterfactualState).toEqual({
      light: { numerator: 1, denominator: 1 },
      deep: { numerator: 0, denominator: 0 },
    });
  });

  it("段 2 に screen が無い・相手に screen がある、は数えずに止める", () => {
    expect(() => compareWithStage2("cal", base, base, DRAFT_RULE_1)).toThrow("段 2 の記録 cal の meta に screen が無い");
    expect(() => compareWithStage2("cal", s2, s2, DRAFT_RULE_1)).toThrow("比べる相手の記録 cal の meta に screen がある");
  });

  it("compareEventSets は同じ組で突き合わせ、当たり方の並びの違いは一致、当たり方だけ違うは別に数え、片側にだけある Event をもう片方の同じ組の状態で取りこぼし・余計と比べられない(理由つき)に分ける", () => {
    const event = (from: number, kinds: FailureEvent["branch"]["kinds"]) => ({ branchPly: from + 1, fromReadyPly: from, toReadyPly: from + 2, branch: { kinds } }) as unknown as FailureEvent;
    const cmp = (from: number): EvaluationPair => ({ kind: "compared", fromPly: from, toPly: from + 2, diffCp: 0 });
    const mateAfter = (from: number): EvaluationPair => ({ kind: "mateAfter", fromPly: from, toPly: from + 2, scoreCpBefore: 0, mateAfter: 3 });
    const notCompared = (from: number, reason: NotComparedReason): EvaluationPair => ({ kind: "notCompared", fromPly: from, toPly: from + 2, reason, side: "to" });
    const baseSide = {
      events: [event(2, ["cpDrop", "matedIfPass"]), event(4, ["cpDrop"]), event(6, ["cpDrop"]), event(8, ["cpDrop"]), event(10, ["cpDrop"]), event(12, ["mateDrop"])],
      pairs: [cmp(2), cmp(4), cmp(6), cmp(8), cmp(10), cmp(12), cmp(14), notCompared(16, "mateBefore")],
    };
    // 段 2 には組 10→12 が無い(記録が途中で終わった等)
    const stage2Side = {
      events: [event(2, ["matedIfPass", "cpDrop"]), event(4, ["mateDrop"]), event(14, ["cpDrop"]), event(16, ["cpDrop"])],
      pairs: [cmp(2), cmp(4), cmp(6), notCompared(8, "notEvaluation"), mateAfter(12), cmp(14), cmp(16)],
    };
    expect(compareEventSets(baseSide, stage2Side)).toEqual({
      base: 6,
      stage2: 4,
      common: 1,
      kindsDiffer: ["5:cpDrop→mateDrop"],
      missed: ["7:cpDrop", "13:mateDrop"],
      missedUncomparable: [
        { key: "9:cpDrop", reason: "notEvaluation" },
        { key: "11:cpDrop", reason: "noPair" },
      ],
      extra: ["15:cpDrop"],
      extraUncomparable: [{ key: "17:cpDrop", reason: "mateBefore" }],
      missRate: { numerator: 2, denominator: 4 },
      extraRate: { numerator: 1, denominator: 3 },
    });
  });

  it("R-1: 段 2 の同じ組が評価値でない・記録が途中で終わり組が無い Event は、取りこぼしに入れず理由つきで比べられないに数え、率の分母に入れない。表に理由と合計を書く", () => {
    // 段 2: ply 22 は読み直しても評価値でない(notEvaluation)。記録は ply 40 で終わる(組 44→46 が無い)
    const truncated = stage2({ 20: engineRef(0), 22: engineRef(40_000) }, { 20: { reference: at(DEEP)(0) }, 22: { reference: at(DEEP)(40_000) } });
    truncated.records = truncated.records.filter((record) => record.ply <= 40);
    const c = compareWithStage2("cal", base, truncated, DRAFT_RULE_1);
    expect(c.events).toEqual({
      base: 2,
      stage2: 0,
      common: 0,
      kindsDiffer: [],
      missed: [],
      missedUncomparable: [
        { key: "21:cpDrop", reason: "notEvaluation" },
        { key: "45:cpDrop", reason: "noPair" },
      ],
      extra: [],
      extraUncomparable: [],
      missRate: { numerator: 0, denominator: 0 },
      extraRate: { numerator: 0, denominator: 0 },
    });
    const row = (kifuId: string): StageRow => ({ kind: "counted", comparison: { ...c, kifuId }, deepRows: compareDeepRows(truncated.records, base.records) });
    const lines = renderScreenCalibration([row("p"), row("q")], [], { onlyBase: [], onlyStage2: [] });
    expect(lines).toContain("| p | 2 | 0 | 0 | 0 | 0 | 分母 0 | 2(21:cpDrop 評価値でない・45:cpDrop 組が無い) | 0 | 分母 0 | 0 | 0 | 0 | 0 |");
    expect(lines).toContain("| 合計 | 4 | 0 | 0 | 0 | 0 | 分母 0 | 4(評価値でない 2・組が無い 2) | 0 | 分母 0 | 0 | 0 | 0 | 0 |");
  });
});

describe("STEP D-SCREEN-2 の校正: 読み直した行と相手の同じ行(床の (i)・(vi))", () => {
  it("参考評価の一致、読み筋の長さ・標識・1 手目の一致、相手に行が無い、を数える", () => {
    const pv20 = GAME01_MOVES.slice(20, 30);
    const base = uniform({ 20: engineRef(0), 22: engineRef(-100) }, { 20: (sfen) => [focus(sfen, pv20)], 22: (sfen) => [focus(sfen, GAME01_MOVES.slice(22, 24), { upperbound: true })] });
    const s2 = stage2(
      { 20: engineRef(0), 22: engineRef(-100) },
      {
        20: { reference: at(DEEP)(0), pvs: (sfen) => [focus(sfen, pv20)] },
        22: { reference: at(DEEP)(-120), pvs: (sfen) => [focus(sfen, GAME01_MOVES.slice(22, 32))] },
        24: { reference: at(DEEP)(0) },
      },
    );
    const withoutPly24 = base.records.filter((record) => record.ply !== 24);
    expect(compareDeepRows(s2.records, withoutPly24)).toEqual({ deepRows: 3, noCounterpart: 1, referenceEqual: 1, pvCompared: 2, pvLengthEqual: 1, pvBoundsEqual: 1, pvFirstMoveEqual: 2 });
  });
});

describe("STEP D-SCREEN-2 の校正: 同じ入力で 2 回回した rescreen(床の (iii)・(iv))", () => {
  const meta = (startedAt: string, gitHead: string, deepNodes = DEEP) => JSON.stringify({ kind: "meta", kifuId: "cal", screen: { deepNodes, deepRun: { startedAt, gitHead, dirty: false, order: "plyAscending" } } });
  const row = (ply: number, deep?: unknown) => JSON.stringify({ kind: "record", ply, phase: "ready", ...(deep === undefined ? {} : { engineReferenceDeep: null, searchPvsDeep: deep }) });

  it("deepRun の startedAt・gitHead だけが違う 2 回は meta が同じ。record 行のバイト一致と searchPvsDeep の一致を数える", () => {
    const first = [meta("t1", "g1"), row(0), row(2, [["7g7f"]]), row(4, [["2g2f"]]), ""].join("\n");
    const same = [meta("t2", "g2"), row(0), row(2, [["7g7f"]]), row(4, [["2g2f"]]), ""].join("\n");
    expect(compareRescreenRuns(first, same)).toEqual({ metaEqual: true, recordLines: 3, recordLinesEqual: 3, deepRows: 2, searchPvsDeepEqual: 2 });
    const differs = [meta("t2", "g2", LIGHT), row(0), row(2, [["7g7f"]]), row(4, [["8c8d"]]), ""].join("\n");
    expect(compareRescreenRuns(first, differs)).toEqual({ metaEqual: false, recordLines: 3, recordLinesEqual: 2, deepRows: 2, searchPvsDeepEqual: 1 });
  });
});

describe("STEP D-SCREEN-2 の校正: 同じ局面を続けて 2 回測る(床の (v))", () => {
  const measurement = (scoreCp: number, pv: string[], bounds: { upperbound?: boolean } = {}): EngineReferenceMeasurement => ({
    reference: at(DEEP)(scoreCp),
    searchPvs: [focus("s", pv, bounds), { ...focus("s", ["x"]), source: "focus_after_pass" }],
  });

  it("参考評価・focus_baseline の pv・標識の一致を分けて返す。focus_baseline が片方に無ければ比べない", () => {
    expect(compareMeasurementPair(measurement(10, ["7g7f", "3c3d"]), measurement(10, ["7g7f", "3c3d"]))).toEqual({ referenceEqual: true, focusCompared: true, focusPvEqual: true, focusBoundsEqual: true });
    expect(compareMeasurementPair(measurement(10, ["7g7f", "3c3d"]), measurement(12, ["7g7f"], { upperbound: true }))).toEqual({ referenceEqual: false, focusCompared: true, focusPvEqual: false, focusBoundsEqual: false });
    expect(compareMeasurementPair(measurement(10, ["7g7f"]), { reference: null, searchPvs: [] })).toEqual({ referenceEqual: false, focusCompared: false, focusPvEqual: false, focusBoundsEqual: false });
  });

  it("planMeasureTwice: 渡さなければ Failure Event の根、渡せば昇順・重なりなし。ready 行に無い ply は止める", () => {
    const record = uniform({ 20: engineRef(0), 22: engineRef(-500), 44: engineRef(0), 46: engineRef(-500) });
    const plan = planMeasureTwice("cal", record, DRAFT_RULE_1);
    expect(plan.plies).toEqual([20, 44]);
    expect(plan.sfenByPly.get(20)).toBe(record.records.find((r) => r.ply === 20)!.sfen);
    expect(planMeasureTwice("cal", record, DRAFT_RULE_1, [6, 2, 6]).plies).toEqual([2, 6]);
    expect(() => planMeasureTwice("cal", record, DRAFT_RULE_1, [2, 99, 101])).toThrow("記録 cal に ply 99,101 の ready 行が無い");
  });
});

describe("STEP D-SCREEN-2 の校正: 報告", () => {
  it("数えた記録の表・合計・数えなかった記録・片方にしか無い記録を描き、2 回の rescreen の節は渡したときだけ出す", () => {
    const base = uniform({ 20: engineRef(0), 22: engineRef(-500) });
    const s2 = stage2({ 20: engineRef(0), 22: engineRef(-500) }, {});
    const counted = (kifuId: string): StageRow => ({ kind: "counted", comparison: { ...compareWithStage2("cal", base, s2, DRAFT_RULE_1), kifuId }, deepRows: compareDeepRows(s2.records, base.records) });
    const rows: StageRow[] = [counted("a"), counted("b"), { kind: "notCounted", kifuId: "broken", detail: "InvalidScreenRecordError: 何か" }];
    const lines = renderScreenCalibration(rows, [], { onlyBase: ["x.jsonl"], onlyStage2: ["y.jsonl"] });
    expect(lines).toContain("| a | 1 | 1 | 1 | 0 | 0 | 0/1 | 0 | 0 | 0/1 | 0 | 0 | 0 | 0 |");
    expect(lines).toContain("| 合計 | 2 | 2 | 2 | 0 | 0 | 0/2 | 0 | 0 | 0/2 | 0 | 0 | 0 | 0 |");
    expect(lines).toContain("| a | 1/1 | 分母 0 | 分母 0 | 分母 0 | 分母 0 | 0 | 28 | 0 |");
    expect(lines).toContain("- 数えられなかった: broken(InvalidScreenRecordError: 何か)");
    expect(lines).toContain("- 相手にしか無い(段 2 は回していない): x.jsonl");
    expect(lines).toContain("- 段 2 にしか無い(相手は回していない): y.jsonl");
    expect(lines.some((line) => line.startsWith("## 同じ入力で 2 回回した rescreen"))).toBe(false);
    const withRuns = renderScreenCalibration(rows, [{ kifuId: "a", comparison: { metaEqual: true, recordLines: 3, recordLinesEqual: 3, deepRows: 1, searchPvsDeepEqual: 1 } }], { onlyBase: [], onlyStage2: [] });
    expect(withRuns).toContain("| a | 同じ | 3 | 3 | 1 | 1 |");
  });
});
