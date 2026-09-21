// STEP FILL 作業 X(docs/STEP_FILL_PLAN_2026-09-22.md §2)。rescreenRecords が run.checkMeasure を使って
// checkBaselineDeep を書く配線を見張る。**エンジンは使わない**(偽の measure・偽の checkMeasure・偽の git)。
// 記録は GAME01 の実際の手順に評価を植えたもの(lib/failureEventFixtures.ts。rescreen.test.ts と同じ土台)。
//
// GAME01 で先手が王手中の ready 行は 34・36・38・40・52・54(56 で終局)。この試験は 30→32 に急落を植えて
// 候補の組を作り、読み直す行(28・30・32・34。DRAFT_SCREEN_RULE_1 の before=1・after=2)に王手中の行 34 を含める。

import { describe, expect, it } from "vitest";
import type { EngineReferenceMeasurement } from "../../../apps/server/src/analysis/engineReference.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import { isGameOver, isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import type { RecordLine } from "../invariants/types.js";
import { evaluationOf } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { readGitState, type GitRunner } from "./gitState.js";
import { choosePairSources } from "./screenDiagnosis.js";
import { DRAFT_SCREEN_RULE_1, deepPliesOf, rescreenRecords, type DeepRunInput } from "./rescreen.js";

const rule = DRAFT_SCREEN_RULE_1;
const LIGHT = 400_000;
const DEEP = 4_000_000;
// 34・36・38・40 手目が王手中(GAME01)。ここまでを含める
const MOVES40 = GAME01_MOVES.slice(0, 40);

function observation(tag: string, sfen: string): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: null, mate: null, pv: [tag], lowerbound: false, upperbound: false };
}

function stage1Records(plant: Record<number, PlantedEvaluation>): RecordLine[] {
  return plantedRecords(MOVES40, plant).map((record): RecordLine => ({
    ...record,
    ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: LIGHT } } : {}),
    searchPvs: [observation(`light-${record.ply}`, record.sfen)],
  }));
}

const META = {
  kind: "meta",
  kifuId: "rescreen-checkbaseline-fixture",
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

function stage1Source(records: readonly RecordLine[]): Buffer {
  const lines: unknown[] = [META, ...records];
  return Buffer.from(`${lines.map((line) => JSON.stringify(line)).join("\n")}\n`, "utf-8");
}

const fakeGit: GitRunner = (args) => (args[0] === "rev-parse" ? "deephead\n" : " M scripts/playtest/lib/rescreen.ts\0");

function run(overrides: Partial<DeepRunInput> = {}): DeepRunInput {
  return { deepNodes: DEEP, enginePath: "/deep/engine", threads: 1, startedAt: "deep-start", repoRoot: "/repo", runGit: fakeGit, ...overrides };
}

/** 30→32 に急落(-300)を植えた記録。読み直す行は 28・30・32・34(34 が王手中)。 */
function recordsWithDropBeforeCheck(): RecordLine[] {
  return stage1Records({ 30: engineRef(0), 32: engineRef(-300) });
}

/** measureEngineReference と同じ形: 終局・王手中(パスが成立しない)は engine を触らず null を返す。
 * checkBaselineDeep の入力(deepPlies に王手中の行が混ざる)を、本物の measure と同じ挙動で再現するため。 */
function fakeMeasure(): { calls: string[]; measure: (sfen: string) => Promise<EngineReferenceMeasurement> } {
  const calls: string[] = [];
  return {
    calls,
    measure: async (sfen) => {
      calls.push(sfen);
      if (isGameOver(sfen) || isInCheck(sfen, "sente")) return { reference: null, searchPvs: [] };
      return { reference: { ...engineRef(-1000 - calls.length), nodes: DEEP }, searchPvs: [observation(`deep-${calls.length}`, sfen)] };
    },
  };
}

describe("STEP FILL 作業 X: rescreenRecords と checkBaselineDeep(計画 §2)", () => {
  it("前提: DRAFT_SCREEN_RULE_1 で読み直す行は 28・30・32・34(34 は王手中)", () => {
    expect(deepPliesOf(recordsWithDropBeforeCheck(), rule)).toEqual([28, 30, 32, 34]);
  });

  it("王手中の行(34)にだけ checkBaselineDeep を足す。他の読み直した行(28・30・32)には出さない", async () => {
    const source = stage1Source(recordsWithDropBeforeCheck());
    const { measure } = fakeMeasure();
    const checkCalls: string[] = [];
    const text = await rescreenRecords(source, rule, measure, run({
      checkMeasure: async (sfen) => {
        checkCalls.push(sfen);
        return { scoreCp: -900, mate: null, bestmove: "5i5h", nodes: DEEP };
      },
    }));

    const lines = text.split("\n").filter((line) => line.length > 0).map((line) => JSON.parse(line) as Record<string, unknown> & { ply?: number; kind?: string; phase?: string });
    const byPly = new Map(lines.filter((line) => line.kind === "record" && line.phase === "ready").map((line) => [line.ply, line]));

    expect(byPly.get(34)!.checkBaselineDeep).toEqual({ scoreCp: -900, mate: null, bestmove: "5i5h", nodes: DEEP });
    for (const ply of [28, 30, 32]) {
      expect(Object.keys(byPly.get(ply)!)).not.toContain("checkBaselineDeep");
    }
    // checkMeasure は王手中の行(34)だけ呼ぶ
    expect(checkCalls).toHaveLength(1);
  });

  it("checkMeasure を渡さない(既存の呼び出し)場合、checkBaselineDeep はどの行にも出ない", async () => {
    const source = stage1Source(recordsWithDropBeforeCheck());
    const { measure } = fakeMeasure();
    const text = await rescreenRecords(source, rule, measure, run());
    expect(text).not.toContain("checkBaselineDeep");
  });

  it("checkMeasure が null を返した(測ろうとして測れなかった)場合、checkBaselineDeep は null(キーは残す)", async () => {
    const source = stage1Source(recordsWithDropBeforeCheck());
    const { measure } = fakeMeasure();
    const text = await rescreenRecords(source, rule, measure, run({ checkMeasure: async () => null }));
    const line = text.split("\n").map((l) => (l ? (JSON.parse(l) as { ply?: number; checkBaselineDeep?: unknown }) : null)).find((l) => l?.ply === 34);
    expect(line).toBeDefined();
    expect(line!.checkBaselineDeep).toBeNull();
  });

  it("読み取り側: deepRowOf(choosePairSources 経由)が checkBaselineDeep を measured として読む(深い側の同じ役の関数)", async () => {
    const source = stage1Source(recordsWithDropBeforeCheck());
    const { measure } = fakeMeasure();
    const text = await rescreenRecords(source, rule, measure, run({
      checkMeasure: async () => ({ scoreCp: -900, mate: null, bestmove: "5i5h", nodes: DEEP }),
    }));
    const records = text
      .split("\n")
      .filter((line) => line.length > 0)
      .map((line) => JSON.parse(line) as RecordLine & { kind: string })
      .filter((line) => line.kind === "record") as RecordLine[];

    const rows = records.filter((record) => record.phase === "ready").map((record) => ({ ply: record.ply, record, evaluation: evaluationOf(record) }));
    const chosen = choosePairSources(rows);
    // 32→34 の組は、34 が王手中で checkBaselineDeep から measured を得るので deep(2 行とも深く測れた)
    const pair = chosen.find((c) => c.from.ply === 32 && c.to.ply === 34)!;
    expect(pair.source).toBe("deep");
    expect(pair.to.evaluation).toEqual({
      state: "measured",
      scoreCp: -900,
      mate: null,
      bestmove: "5i5h",
      afterPassScoreCp: null,
      afterPassMate: null,
      dropCp: null,
    });
  });

  it("読み直す行に王手中の行が無い局は、checkMeasure を渡しても呼ばれない", async () => {
    const source = stage1Source(stage1Records({ 4: engineRef(0), 6: engineRef(-300) }));
    const { measure } = fakeMeasure();
    const checkCalls: string[] = [];
    await rescreenRecords(source, rule, measure, run({
      checkMeasure: async (sfen) => {
        checkCalls.push(sfen);
        return null;
      },
    }));
    expect(checkCalls).toEqual([]);
  });
});
