// STEP D1b(docs/STEP_D1b_PLAN_2026-09-15.md 3.)。上がり(rise)と最大の下がり(maxDrop)の固定例 G-1〜G-15(G-9・G-16 は diagnose.test.ts)、
// 不変条件(S-1)、契約 diagnosis-moment v0.1 のスキーマ。**エンジンは起動しない。**
//
// 【正解の置き方】G-1〜G-14 の期待は計画書 3. の表のまま手で書いた(実装の出力から写さない)。G-15 の trigger・consequences は、
// Failure Event と同じ関数(triggerOf・actualContinuation)の値と等しいことを見る(計画 2. の「そのまま」)。
// 【コミット済みの記録】不変条件とスキーマは records/ の d-cost・d0-nnue・d3-nnue・d3b-nnue-n2000・real-01 でも見る。**real-02 は読まない**
// (D1b の予測の盲検 ― 計画 5.。司令塔の指示)。件数は固定しない(P-20)。

import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import {
  diagnosisMomentsOf,
  loadDiagnosisMomentSchema,
  toMomentLine,
  type DiagnosisMoment,
  type DiagnosisMoments,
  type MaxDropMoment,
} from "./diagnosisMoment.js";
import { validate } from "./eventSchema.js";
import { actualContinuation, diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, readEvaluations, triggerOf, type FailureEvent } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { buildProvenance, loadFailureEventSchema, toEventLine } from "./failureEventSchema.js";
import { initialSfenOf } from "./sideAlignment.js";

type Json = Record<string, unknown>;
const schema = loadDiagnosisMomentSchema();
const PROVENANCE = buildProvenance({
  recordPath: "fixture.jsonl",
  recordSha256: "0".repeat(64),
  meta: undefined,
  evaluator: null,
  analysisGit: { gitHead: null, dirty: null },
  rule: DRAFT_RULE_1,
  notEvaluationCp: NOT_EVALUATION_CP,
  repoRoot: "/nonexistent-repo-root",
});
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const lineOf = (moment: DiagnosisMoment): Json => clone(toMomentLine(moment, PROVENANCE)) as unknown as Json;
const cp = (value: number, options: Parameters<typeof engineRef>[1] = {}) => engineRef(value, options);
const mate = (value: number) => engineRef(null, { mate: value });

/** 本人視点の評価の並びを ply 0・2・4… の行に植える(手順は GAME01 の先頭。この範囲に先手が王手中の行・終局は無い) */
function game(values: PlantedEvaluation[]): RecordLine[] {
  const plant: Record<number, PlantedEvaluation> = {};
  values.forEach((value, index) => (plant[index * 2] = value));
  return plantedRecords(GAME01_MOVES.slice(0, (values.length - 1) * 2), plant);
}

function momentsOf(records: RecordLine[]): { moments: DiagnosisMoments; events: FailureEvent[] } {
  const { events } = diagnoseRecords("g", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
  return { moments: diagnosisMomentsOf("g", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events), events };
}

const risesOf = (moments: DiagnosisMoments) => moments.rises.map((rise) => ({ branchPly: rise.branchPly, change: rise.change, failureEventBranchPly: rise.failureEventBranchPly }));

function pairRow(maxDrop: MaxDropMoment): Exclude<MaxDropMoment, { state: string }> {
  if ("state" in maxDrop) throw new Error(`組の行でない: ${maxDrop.state}`);
  return maxDrop;
}
const dropOf = (maxDrop: MaxDropMoment) =>
  "state" in maxDrop
    ? maxDrop
    : { branchPly: maxDrop.branchPly, change: maxDrop.change, failureEventBranchPly: maxDrop.failureEventBranchPly, excludedPairs: maxDrop.excludedPairs };

const NONE = { mateDrop: 0, mateRise: 0, notCompared: 0 };

function focusBaseline(sfen: string, pv: string[]): SearchPvObservation {
  return { source: "focus_baseline", sfen, moveUsi: null, multipv: 1, scoreCp: 0, mate: null, pv, lowerbound: false, upperbound: false };
}
function withFocus(records: RecordLine[], ply: number, pv: string[]): RecordLine[] {
  const row = records.find((record) => record.ply === ply)!;
  row.searchPvs = [focusBaseline(row.sfen, pv)];
  return records;
}

// ---- G-1〜G-14 ----
describe("STEP D1b の固定例(計画 3.)", () => {
  it("G-1 上がりの境目: 0 → +399 → +799 は 2→4(branchPly 3、+400)の 1 行。maxDrop は noDrop・minDiffCp 399", () => {
    const { moments } = momentsOf(game([cp(0), cp(399), cp(799)]));
    expect(risesOf(moments)).toEqual([{ branchPly: 3, change: { kind: "cp", diffCp: 400 }, failureEventBranchPly: null }]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noDrop", minDiffCp: 399, excludedPairs: NONE });
  });

  it("G-2 詰みの上がり: +200 → mate +3 は 0→2 の mateAfter の 1 行。maxDrop は noComparedPair・mateRise 1", () => {
    const { moments } = momentsOf(game([cp(200), mate(3)]));
    expect(risesOf(moments)).toEqual([{ branchPly: 1, change: { kind: "mateAfter", mateAfter: 3 }, failureEventBranchPly: null }]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noComparedPair", excludedPairs: { mateDrop: 0, mateRise: 1, notCompared: 0 } });
  });

  it("G-2′ 詰みの下がり: +200 → mate −3 は上がり無し(mateDrop の Failure Event がある)。maxDrop は noComparedPair・mateDrop 1", () => {
    const { moments, events } = momentsOf(game([cp(200), mate(-3)]));
    expect(moments.rises).toEqual([]);
    expect(events.map((event) => [event.branchPly, event.branch.kinds])).toEqual([[1, ["mateDrop"]]]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noComparedPair", excludedPairs: { mateDrop: 1, mateRise: 0, notCompared: 0 } });
  });

  it("G-3 最大の下がり(閾値未満): +100 → +50 → −100 → −30 は上がり無し。maxDrop は 2→4(−150)・failureEventBranchPly null、Failure Event 0 件", () => {
    const { moments, events } = momentsOf(game([cp(100), cp(50), cp(-100), cp(-30)]));
    expect(moments.rises).toEqual([]);
    expect(events).toEqual([]);
    expect(dropOf(moments.maxDrop)).toEqual({ branchPly: 3, change: { kind: "cp", diffCp: -150 }, failureEventBranchPly: null, excludedPairs: NONE });
  });

  it("G-4 急落と重なる: +300 → −300 → −250 は上がり無し。maxDrop は 0→2(−600)・failureEventBranchPly 1。Failure Event の値は変わらない", () => {
    const records = game([cp(300), cp(-300), cp(-250)]);
    const { events } = diagnoseRecords("g", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const before = clone(events);
    const moments = diagnosisMomentsOf("g", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events);
    expect(moments.rises).toEqual([]);
    expect(dropOf(moments.maxDrop)).toEqual({ branchPly: 1, change: { kind: "cp", diffCp: -600 }, failureEventBranchPly: 1, excludedPairs: NONE });
    expect(clone(events)).toEqual(before);
    expect(clone(diagnoseRecords("g", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).events)).toEqual(before);
    expect(events.map((event) => [event.branchPly, event.branch.kinds])).toEqual([[1, ["cpDrop"]]]);
  });

  it("G-5 同じ最小値: 0 → −100 → −200 → −300 は 3 組とも −100 で、早い組(0→2)", () => {
    const { moments } = momentsOf(game([cp(0), cp(-100), cp(-200), cp(-300)]));
    expect(dropOf(moments.maxDrop)).toEqual({ branchPly: 1, change: { kind: "cp", diffCp: -100 }, failureEventBranchPly: null, excludedPairs: NONE });
  });

  it("G-6 下がりが無い: 0 → +10 → +20 は noDrop・minDiffCp 10", () => {
    const { moments } = momentsOf(game([cp(0), cp(10), cp(20)]));
    expect(moments.rises).toEqual([]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noDrop", minDiffCp: 10, excludedPairs: NONE });
  });

  it("G-7 比べられる組が無い: 1 行目 engineReference null・2 行目だけ測った は noComparedPair・notCompared 1", () => {
    const { moments } = momentsOf(game([null, cp(0)]));
    expect(moments.rises).toEqual([]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noComparedPair", excludedPairs: { mateDrop: 0, mateRise: 0, notCompared: 1 } });
  });

  it("G-8 afterPass の値が無い: G-1 の 2 行目だけ afterPass.scoreCp が null でも、判定は baseline だけで G-1 と同じ", () => {
    const withAfterPass = momentsOf(game([cp(0, { afterPassScoreCp: 50 }), cp(399, { afterPassScoreCp: 50 }), cp(799, { afterPassScoreCp: 50 })])).moments;
    const secondNull = momentsOf(game([cp(0, { afterPassScoreCp: 50 }), cp(399, { afterPassScoreCp: null }), cp(799, { afterPassScoreCp: 50 })])).moments;
    expect(risesOf(secondNull)).toEqual([{ branchPly: 3, change: { kind: "cp", diffCp: 400 }, failureEventBranchPly: null }]);
    expect(risesOf(secondNull)).toEqual(risesOf(withAfterPass));
    expect(secondNull.maxDrop).toEqual(withAfterPass.maxDrop);
    expect(secondNull.maxDrop).toMatchObject({ state: "noDrop", minDiffCp: 399 });
  });

  it("G-10 上がりと matedIfPass が重なる: 0 → +500(2 行目に afterPassMate +3)は 0→2 の 1 行・failureEventBranchPly 1。maxDrop は noDrop・500", () => {
    const { moments, events } = momentsOf(game([cp(0), cp(500, { afterPassMate: 3 })]));
    expect(events.map((event) => [event.branchPly, event.branch.kinds])).toEqual([[1, ["matedIfPass"]]]);
    expect(risesOf(moments)).toEqual([{ branchPly: 1, change: { kind: "cp", diffCp: 500 }, failureEventBranchPly: 1 }]);
    expect(moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noDrop", minDiffCp: 500, excludedPairs: NONE });
  });

  it("G-11 afterPass に最善手がある: G-1 の 2 行目の afterPass.bestmove に手を植えても、opponentBestmove は notInRecord のまま", () => {
    const records = game([cp(0), cp(399, { afterPassBestmove: "8c8d" }), cp(799)]);
    expect(records.find((record) => record.ply === 2)!.engineReference!.afterPass.bestmove).toBe("8c8d");
    const { moments } = momentsOf(records);
    expect(risesOf(moments)).toEqual([{ branchPly: 3, change: { kind: "cp", diffCp: 400 }, failureEventBranchPly: null }]);
    expect(moments.rises[0]!.opponentBestmove).toEqual({ state: "notInRecord" });
    expect(moments.maxDrop).toMatchObject({ state: "noDrop", minDiffCp: 399 });
  });

  it("G-12 読み筋の 1 手目: 上がりの直前の行に focus_baseline を植えると、(i) 1 手目 = 本人の手なら pvFirstMoveIsPlayedMove true (ii) 違う手なら false。G-4 の組の行の counterfactual は Failure Event と等しい", () => {
    // G-1 の上がりは ply 2 → 4。本人の手は GAME01 の 3 手目 7g7f
    expect(GAME01_MOVES[2]).toBe("7g7f");
    const same = momentsOf(withFocus(game([cp(0), cp(399), cp(799)]), 2, ["7g7f", "8c8d"])).moments.rises[0]!;
    const other = momentsOf(withFocus(game([cp(0), cp(399), cp(799)]), 2, ["3g3f", "8c8d"])).moments.rises[0]!;
    expect(same.counterfactual).toMatchObject({ state: "compared", pvFirstMove: "7g7f", pvFirstMoveIsPlayedMove: true });
    expect(other.counterfactual).toMatchObject({ state: "compared", pvFirstMove: "3g3f", pvFirstMoveIsPlayedMove: false });

    const drop = momentsOf(withFocus(game([cp(300), cp(-300), cp(-250)]), 0, ["2g2f", "1c1d"]));
    const row = pairRow(drop.moments.maxDrop);
    expect(row.counterfactual.state).toBe("compared");
    expect(row.counterfactual).toEqual(drop.events.find((event) => event.branchPly === 1)!.counterfactual);
    expect(row.consequences).toEqual(drop.events.find((event) => event.branchPly === 1)!.consequences);
  });

  it("G-13 noDrop の境目: (a) 0 → 0 は noDrop・minDiffCp 0 (b) 0 → −1 は組の行・−1", () => {
    expect(momentsOf(game([cp(0), cp(0)])).moments.maxDrop).toEqual({ eventClass: "maxDrop", kifuId: "g", state: "noDrop", minDiffCp: 0, excludedPairs: NONE });
    expect(dropOf(momentsOf(game([cp(0), cp(-1)])).moments.maxDrop)).toEqual({ branchPly: 1, change: { kind: "cp", diffCp: -1 }, failureEventBranchPly: null, excludedPairs: NONE });
  });

  it("G-14 詰みの下がりのある局: +100 → +80 → mate −3 は 0→2(−20)・failureEventBranchPly null・mateDrop 1(最大は詰みの組の外)", () => {
    const { moments, events } = momentsOf(game([cp(100), cp(80), mate(-3)]));
    expect(events.map((event) => [event.branchPly, event.branch.kinds])).toEqual([[3, ["mateDrop"]]]);
    expect(moments.rises).toEqual([]);
    expect(dropOf(moments.maxDrop)).toEqual({ branchPly: 1, change: { kind: "cp", diffCp: -20 }, failureEventBranchPly: null, excludedPairs: { mateDrop: 1, mateRise: 0, notCompared: 0 } });
  });
});

// ---- G-15 ----
describe("STEP D1b の行の全体(計画 G-15)", () => {
  // GAME01 の ply 20 に +100(bestmove を植える)、ply 22 に +600。ほかは 0(先手が王手中の 34・36・38・40・52・54 と終局の 56 は null)
  const records = plantedRecords(GAME01_MOVES, { 20: cp(100, { bestmove: "3g2h" }), 22: cp(600) });
  const { moments, events } = momentsOf(records);
  const rowAt = (ply: number) => readEvaluations(records).find((row) => row.ply === ply)!;

  it("rise の 1 行(20→22、+500)を全部の欄で書き、v0.1 のスキーマを通る", () => {
    expect(moments.rises).toHaveLength(1);
    const line = lineOf(moments.rises[0]!);
    expect(line).toEqual(
      clone({
        contract: "diagnosis-moment",
        schemaVersion: "0.1",
        eventClass: "rise",
        kifuId: "g",
        branchPly: 21,
        fromReadyPly: 20,
        toReadyPly: 22,
        trigger: triggerOf(rowAt(20), DEFAULT_INITIAL_SFEN),
        change: { kind: "cp", diffCp: 500 },
        moves: { userMove: "3g2h", opponentMove: "6e5g" },
        userBestmoveAtBefore: "3g2h",
        opponentBestmove: { state: "notInRecord" },
        evaluationAfter: { state: "measured", scoreCp: 600, mate: null, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null },
        failureEventBranchPly: null,
        consequences: actualContinuation(GAME01_MOVES, 21, DRAFT_RULE_1.windowPlies, DEFAULT_INITIAL_SFEN),
        counterfactual: { state: "unrecorded" },
        provenance: PROVENANCE,
      }),
    );
    expect(Object.keys(line).slice(0, 3)).toEqual(["contract", "schemaVersion", "eventClass"]);
    expect(validate(line, schema)).toEqual([]);
  });

  it("maxDrop の組の行(22→24、−600、Failure Event 23)を excludedPairs を含めて全部の欄で書き、v0.1 のスキーマを通る", () => {
    expect(events.map((event) => [event.branchPly, event.branch.kinds])).toEqual([[23, ["cpDrop"]]]);
    const line = lineOf(moments.maxDrop);
    expect(line).toEqual(
      clone({
        contract: "diagnosis-moment",
        schemaVersion: "0.1",
        eventClass: "maxDrop",
        kifuId: "g",
        branchPly: 23,
        fromReadyPly: 22,
        toReadyPly: 24,
        trigger: triggerOf(rowAt(22), DEFAULT_INITIAL_SFEN),
        change: { kind: "cp", diffCp: -600 },
        moves: { userMove: "6i5h", opponentMove: "5g4i+" },
        userBestmoveAtBefore: null,
        opponentBestmove: { state: "notInRecord" },
        evaluationAfter: { state: "measured", scoreCp: 0, mate: null, bestmove: null, afterPassScoreCp: null, afterPassMate: null, dropCp: null },
        failureEventBranchPly: 23,
        consequences: actualContinuation(GAME01_MOVES, 23, DRAFT_RULE_1.windowPlies, DEFAULT_INITIAL_SFEN),
        counterfactual: { state: "unrecorded" },
        // 王手中の行 6 と終局の行 1 に触れる組: 32→34・34→36・36→38・38→40・40→42・50→52・52→54・54→56
        excludedPairs: { mateDrop: 0, mateRise: 0, notCompared: 8 },
        provenance: PROVENANCE,
      }),
    );
    expect(validate(line, schema)).toEqual([]);
  });
});

// ---- 監査 A の必須 R-1: 窓に王手が入る組 ----
describe("STEP D1b の窓に王手が入る組(監査 A の必須 R-1)", () => {
  it("R-1: GAME01 の 28 → 30 に +500 を植えると、rise(29)の consequences は checks [34]、maxDrop(31、−500)の consequences は checks [34, 36] で同じ組の Failure Event と等しく、trigger も直前の行・Event と等しい", () => {
    // GAME01 で後手の手の後に先手が王手中になるのは ply 34・36・38・40(ほかの 0 の行は既定)。窓は branchPly から 5 手
    const records = plantedRecords(GAME01_MOVES, { 28: cp(0), 30: cp(500) });
    const { moments, events } = momentsOf(records);
    expect(moments.rises.map((rise) => [rise.branchPly, rise.change])).toEqual([[29, { kind: "cp", diffCp: 500 }]]);
    const rise = moments.rises[0]!;
    expect(rise.consequences).toEqual({ checks: [34], mate: null, windowPlies: 5, windowShort: false });
    expect(rise.trigger).toEqual(triggerOf(readEvaluations(records).find((row) => row.ply === 28)!, DEFAULT_INITIAL_SFEN));

    const row = pairRow(moments.maxDrop);
    expect([row.branchPly, row.change, row.failureEventBranchPly]).toEqual([31, { kind: "cp", diffCp: -500 }, 31]);
    const event = events.find((candidate) => candidate.branchPly === 31)!;
    expect(event.branch.kinds).toEqual(["cpDrop"]);
    expect(row.consequences).toEqual({ checks: [34, 36], mate: null, windowPlies: 5, windowShort: false });
    expect(row.consequences).toEqual(event.consequences);
    expect(row.trigger).toEqual(event.trigger);
  });
});

// ---- 不変条件(S-1)とスキーマ(コミット済みの記録を含む)----
interface Committed {
  label: string;
  records: RecordLine[];
  meta: MetaLine | undefined;
}
const COMMITTED_DIRS = ["d-cost/c4m", "d-cost/l100k", "d-cost/l400k", "d0-nnue", "d3-nnue", "d3b-nnue-n2000", "real-01"];
function committed(): Committed[] {
  return COMMITTED_DIRS.flatMap((dir) => {
    const url = new URL(`../records/${dir}/`, import.meta.url);
    return readdirSync(url)
      .filter((name) => name.endsWith(".jsonl"))
      .sort()
      .map((name) => {
        const lines = readFileSync(new URL(name, url), "utf-8")
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line) => JSON.parse(line) as { kind: string });
        return { label: `${dir}/${name}`, meta: lines.find((line) => line.kind === "meta") as MetaLine | undefined, records: lines.filter((line): line is RecordLine => line.kind === "record") };
      });
  });
}

const FIXTURES: Array<[string, RecordLine[]]> = [
  ["G-1", game([cp(0), cp(399), cp(799)])],
  ["G-2", game([cp(200), mate(3)])],
  ["G-2′", game([cp(200), mate(-3)])],
  ["G-3", game([cp(100), cp(50), cp(-100), cp(-30)])],
  ["G-4", game([cp(300), cp(-300), cp(-250)])],
  ["G-6", game([cp(0), cp(10), cp(20)])],
  ["G-7", game([null, cp(0)])],
  ["G-10", game([cp(0), cp(500, { afterPassMate: 3 })])],
  ["G-14", game([cp(100), cp(80), mate(-3)])],
  ["G-15", plantedRecords(GAME01_MOVES, { 20: cp(100, { bestmove: "3g2h" }), 22: cp(600) })],
];

/** 不変条件: 局に cpDrop の Failure Event がある ⇒ maxDrop は組の行で、failureEventBranchPly が指す Event の kinds に cpDrop がある(「⇐」は書かない ― f2 の再読みの条件 1) */
function expectInvariant(label: string, events: readonly FailureEvent[], maxDrop: MaxDropMoment): boolean {
  const hasCpDrop = events.some((event) => event.branch.kinds.includes("cpDrop"));
  if (!hasCpDrop) return false;
  expect("state" in maxDrop, `${label}: 状態の行になった`).toBe(false);
  const row = pairRow(maxDrop);
  expect(row.failureEventBranchPly, label).not.toBeNull();
  expect(events.find((event) => event.branchPly === row.failureEventBranchPly)?.branch.kinds, label).toContain("cpDrop");
  return true;
}

describe("STEP D1b の不変条件とスキーマ(計画 3.・S-1・Q-1)", () => {
  it("不変条件(固定例): cpDrop の Failure Event がある局では、maxDrop の組の行がその Event を指す", () => {
    let applied = 0;
    for (const [label, records] of FIXTURES) {
      const { moments, events } = momentsOf(records);
      if (expectInvariant(label, events, moments.maxDrop)) applied += 1;
    }
    expect(applied).toBe(2); // G-4・G-15
  });

  it("不変条件とスキーマ(コミット済みの記録。real-02 は読まない): 上がりと最大の下がりの行はすべて v0.1 を通り、cpDrop のある局では maxDrop がその Event を指す", () => {
    const records = committed();
    expect(records.length).toBeGreaterThan(0);
    let lines = 0;
    for (const record of records) {
      const initialSfen = initialSfenOf(record.meta);
      const { events } = diagnoseRecords(record.label, record.records, DRAFT_RULE_1, initialSfen);
      const moments = diagnosisMomentsOf(record.label, record.records, DRAFT_RULE_1, initialSfen, events);
      expectInvariant(record.label, events, moments.maxDrop);
      for (const moment of [...moments.rises, moments.maxDrop]) {
        expect(validate(lineOf(moment), schema), `${record.label} ${moment.eventClass}`).toEqual([]);
        lines += 1;
      }
    }
    expect(lines).toBeGreaterThanOrEqual(records.length);
  }, 120_000);

  it("5 つの変種(上がりの cp・上がりの詰み・最大の下がりの組・noDrop・noComparedPair)が固定例から出て、すべてスキーマを通る", () => {
    const seen = new Set<string>();
    for (const [label, records] of FIXTURES) {
      const { moments } = momentsOf(records);
      for (const moment of [...moments.rises, moments.maxDrop]) {
        const line = lineOf(moment);
        expect(validate(line, schema), label).toEqual([]);
        seen.add(`${moment.eventClass}.${"state" in moment ? moment.state : moment.change.kind}`);
      }
    }
    expect([...seen].sort()).toEqual(["maxDrop.cp", "maxDrop.noComparedPair", "maxDrop.noDrop", "rise.cp", "rise.mateAfter"]);
  });

  it("共通部(kifuId・branchPly・fromReadyPly・toReadyPly・trigger・consequences・provenance・evaluationAfter)は Failure Event v0.4 のスキーマと同じ定義で、counterfactual は説明の文のほかは同じ", () => {
    const fe = loadFailureEventSchema("0.4") as unknown as { properties: Record<string, Json> };
    const variants = (schema as unknown as { oneOf: Array<{ properties: Record<string, Json> }> }).oneOf;
    expect(variants).toHaveLength(5);
    for (const variant of variants) {
      expect(variant.properties.kifuId).toEqual(fe.properties.kifuId);
      expect(variant.properties.provenance).toEqual(fe.properties.provenance);
      if (variant.properties.trigger === undefined) continue;
      for (const key of ["fromReadyPly", "toReadyPly", "trigger", "consequences"]) expect(variant.properties[key], key).toEqual(fe.properties[key]);
      expect(variant.properties.evaluationAfter).toEqual((fe.properties.branch!.properties as Record<string, Json>).evaluationAfter);
      const { description: _a, ...counterfactual } = variant.properties.counterfactual!;
      const { description: _b, ...feCounterfactual } = fe.properties.counterfactual!;
      expect(counterfactual).toEqual(feCounterfactual);
    }
  });

  it("契約と版(Y-17): contract が無い・版が Failure Event の 0.4・eventClass が無い行は落ち、Failure Event の行は v0.1 を通らず、この契約の行は Failure Event v0.4 を通らない", () => {
    const records = FIXTURES.find(([label]) => label === "G-15")![1];
    const { moments, events } = momentsOf(records);
    const line = lineOf(moments.rises[0]!);
    const without = (key: string): Json => {
      const copy = clone(line);
      delete copy[key];
      return copy;
    };
    expect(validate(without("contract"), schema)).not.toEqual([]);
    expect(validate(without("eventClass"), schema)).not.toEqual([]);
    expect(validate({ ...line, schemaVersion: "0.4" }, schema)).not.toEqual([]);
    expect(validate({ ...line, contract: "failure-event" }, schema)).not.toEqual([]);
    expect(validate(clone(toEventLine(events[0]!, PROVENANCE)), schema)).not.toEqual([]);
    expect(validate(line, loadFailureEventSchema("0.4"))).not.toEqual([]);
  });

  it("境目(手で書き換えた 1 行): 上がりの差 0・最大の下がりの組の差 0・noDrop の minDiffCp −1・opponentBestmove に手・状態の行に branchPly・組の行に excludedPairs が無い・上がりの行に excludedPairs は落ちる", () => {
    const g15 = momentsOf(FIXTURES.find(([label]) => label === "G-15")![1]).moments;
    const rise = lineOf(g15.rises[0]!);
    const drop = lineOf(g15.maxDrop);
    const noDrop = lineOf(momentsOf(game([cp(0), cp(10), cp(20)])).moments.maxDrop);
    const changed = (line: Json, change: (copy: Json) => void): Json => {
      const copy = clone(line);
      change(copy);
      return copy;
    };
    const failing: Array<[string, Json]> = [
      ["上がりの差 0", changed(rise, (c) => ((c.change as Json).diffCp = 0))],
      ["最大の下がりの組の差 0", changed(drop, (c) => ((c.change as Json).diffCp = 0))],
      ["noDrop の minDiffCp −1", changed(noDrop, (c) => (c.minDiffCp = -1))],
      ["opponentBestmove に手", changed(rise, (c) => (c.opponentBestmove = { state: "notInRecord", bestmove: "8c8d" }))],
      ["状態の行に branchPly", changed(noDrop, (c) => (c.branchPly = 1))],
      ["組の行に excludedPairs が無い", changed(drop, (c) => delete c.excludedPairs)],
      ["上がりの行に excludedPairs", changed(rise, (c) => (c.excludedPairs = NONE))],
      ["上がりの詰みの手数が負", changed(rise, (c) => (c.change = { kind: "mateAfter", mateAfter: -3 }))],
    ];
    for (const [name, line] of failing) expect(validate(line, schema), name).not.toEqual([]);
    expect(validate(changed(rise, (c) => (c.change = { kind: "mateAfter", mateAfter: 3 })), schema), "上がりの詰み").toEqual([]);
  });
});
