// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §2・§8)。全ての手の組 allPairsOf の固定例 K-11・G-F8 と、コミット済みの記録(real-01)での
// 「上がり・最大の下がりの組の行と同じ欄」の突き合わせ。**エンジンは起動しない。**
//
// 【正解の置き方】K-11・G-F8 の件数と状態は、植えた評価から手で数えた(実装の出力から写さない)。欄の一致は diagnosisMomentsOf の行と比べる(計画 §2 の「pairFields を関数の外へ出したもの」)。
// 【コミット済みの記録】real-01(1 人目の先手 6 局)だけを読む。件数は固定しない(P-20)。

import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { EngineReference } from "../../../apps/server/src/analysis/engineReference.js";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { allPairsOf, diagnosisMomentsOf, type MomentPairFields } from "./diagnosisMoment.js";
import { diagnoseRecords, DRAFT_RULE_1, readEvaluations, STANDING_BOUNDS } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords, type PlantedEvaluation } from "./failureEventFixtures.js";
import { DRAFT_SCREEN_RULE_1, type ScreenMeta } from "./rescreen.js";
import { choosePairSources, screenOfRecord } from "./screenDiagnosis.js";
import { initialSfenOf } from "./sideAlignment.js";
import { standingPairOf } from "./standing.js";

type Json = Record<string, unknown>;
/** 組の行の欄だけ(行の種類ごとの欄を外す)。JSON の文字列で比べて欄の順も見る */
const fieldsOf = (row: object): string => {
  const { eventClass: _eventClass, kifuId: _kifuId, change: _change, excludedPairs: _excludedPairs, pairKind: _pairKind, ...fields } = row as Json;
  return JSON.stringify(fields);
};

/** 本人視点の評価の並びを ply 0・2・4… の行に植える */
function game(values: PlantedEvaluation[]): RecordLine[] {
  const plant: Record<number, PlantedEvaluation> = {};
  values.forEach((value, index) => (plant[index * 2] = value));
  return plantedRecords(GAME01_MOVES.slice(0, (values.length - 1) * 2), plant);
}

describe("allPairsOf(計画 §2)", () => {
  it("K-11 4 行の記録で 3 組目の相手の手が棋譜に無い → pairs 2 組・movesMissing 1。上がり・最大の下がりに選ばれた組の欄は diagnosisMomentsOf の行と一致", () => {
    // 0 → +500 → 0 → 0: 組 1(branchPly 1)は上がり +500、組 2(branchPly 3)は −500 で最大の下がりかつ急落、組 3(branchPly 5)は差 0
    const records = game([engineRef(0), engineRef(500), engineRef(0), engineRef(0)]);
    const last = records.find((record) => record.ply === 6)!;
    last.response = { ...last.response, moveHistory: last.response.moveHistory.slice(0, 5) }; // 組 3 の相手の手(記録の手数 6)を消す
    const { events } = diagnoseRecords("k11", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const moments = diagnosisMomentsOf("k11", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events);
    const all = allPairsOf("k11", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events, { source: "light" });

    expect(all.movesMissing).toBe(1);
    expect(all.pairs.map((pair) => [pair.kifuId, pair.pairKind, pair.branchPly, pair.failureEventBranchPly])).toEqual([
      ["k11", "compared", 1, null],
      ["k11", "compared", 3, 3],
    ]);
    expect(all.rowStandings).toEqual([
      { ply: 0, standing: "level" },
      { ply: 2, standing: "ahead" },
      { ply: 4, standing: "level" },
      { ply: 6, standing: "level" },
    ]);
    expect(moments.rises.map((rise) => rise.branchPly)).toEqual([1]);
    expect("state" in moments.maxDrop ? moments.maxDrop.state : moments.maxDrop.branchPly).toBe(3);
    expect(fieldsOf(all.pairs[0]!)).toBe(fieldsOf(moments.rises[0]!));
    expect(fieldsOf(all.pairs[1]!)).toBe(fieldsOf(moments.maxDrop));
  });

  it("出どころは light だけを受ける(型の外から別の値を渡したら止める)", () => {
    const records = game([engineRef(0), engineRef(0)]);
    expect(() => allPairsOf("x", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, [], { source: "deep" } as unknown as { source: "light" })).toThrow(/light だけ/);
  });
});

// ---- G-F8(D-SCREEN-2 の実物の形)----

const LIGHT = 400_000;
const DEEP = 4_000_000;

/** 段 2 の記録: 軽い値 ply 20 = 0・22 = −200、読み直した深い値 ply 20 = +8・22 = −508(screenDiagnosis.test.ts の stage2 と同じ組み方) */
function stage2(): { meta: MetaLine; records: RecordLine[]; screen: ScreenMeta } {
  const deep: Record<number, EngineReference> = { 20: { ...engineRef(8), nodes: DEEP }, 22: { ...engineRef(-508), nodes: DEEP } };
  const deepPlies = [20, 22];
  const records = plantedRecords(GAME01_MOVES, { 20: engineRef(0), 22: engineRef(-200) }).map((record): RecordLine => {
    const out: RecordLine = { ...record, ...(record.engineReference ? { engineReference: { ...record.engineReference, nodes: LIGHT } } : {}), searchPvs: [] };
    if (deep[record.ply] !== undefined) {
      out.engineReferenceDeep = deep[record.ply]!;
      out.searchPvsDeep = [];
    }
    return out;
  });
  const screen: ScreenMeta = {
    lightNodes: LIGHT,
    deepNodes: DEEP,
    rule: DRAFT_SCREEN_RULE_1,
    deepPlies,
    sourceSha256: "a".repeat(64),
    deepRun: { gitHead: "deephead", dirty: false, enginePath: "/e", threads: 1, startedAt: "deep-start", order: "plyAscending", measuredOrder: deepPlies },
  };
  const meta = { kind: "meta", kifuId: "gf8", startedAt: "t", gitHead: null, enginePath: "/e", searchMode: "nodes", nodes: LIGHT, threads: 1, referenceNodes: LIGHT, screen } as unknown as MetaLine;
  return { meta, records, screen };
}

describe("G-F8 深い値を持つ記録でも allPairsOf は軽い値を読む(計画 §2 の R-6)", () => {
  it("段 2 の不変条件を満たす記録で、ply 20→22 の組は診断では deep になるが、allPairsOf の組は軽い値(standingPair level→level・直後 −200)で、出どころの欄を書かない", () => {
    const { meta, records, screen } = stage2();
    expect(screenOfRecord("gf8", meta, records)).toEqual(screen);
    const rows = readEvaluations(records);
    const index = rows.findIndex((row) => row.ply === 20);
    const deepPick = choosePairSources(rows)[index]!;
    expect(deepPick.source).toBe("deep");
    // 深い値なら level→behind になる組(軽い値と見分けがつく植え方)
    expect(standingPairOf(deepPick.from.evaluation, deepPick.to.evaluation, STANDING_BOUNDS)).toEqual({ before: "level", after: "behind" });

    const { events } = diagnoseRecords("gf8", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const all = allPairsOf("gf8", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events, { source: "light" });
    const pair = all.pairs.find((candidate) => candidate.fromReadyPly === 20)!;
    expect(pair.standingPair).toEqual({ before: "level", after: "level" });
    expect(pair.trigger.evaluationBefore).toMatchObject({ state: "measured", scoreCp: 0 });
    expect(pair.evaluationAfter).toMatchObject({ state: "measured", scoreCp: -200 });
    expect(all.rowStandings.find((row) => row.ply === 22)!.standing).toBe("level");
    for (const row of all.pairs) {
      expect(Object.hasOwn(row, "evaluationSource")).toBe(false);
      expect(Object.hasOwn(row.counterfactual, "pvSource")).toBe(false);
    }

    // 深い欄を外した記録と、組も行の状態も同じ
    const stripped = records.map(({ engineReferenceDeep: _deep, searchPvsDeep: _pvs, ...record }) => record as RecordLine);
    expect(all).toEqual(allPairsOf("gf8", stripped, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, diagnoseRecords("gf8", stripped, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN).events, { source: "light" }));
  }, 60_000);
});

// ---- コミット済みの記録(real-01)----

describe("real-01 の 6 局で、allPairsOf の組は上がり・最大の下がりの組の行と同じ欄(計画 §2)", () => {
  const dir = new URL("../records/real-01/", import.meta.url);
  const files = readdirSync(dir).filter((name) => /^kifu-\d+\.jsonl$/.test(name));

  it("記録が 1 本以上ある", () => {
    expect(files.length).toBeGreaterThan(0);
  });

  it.each(files)("%s: 組の数 + movesMissing = ready 行 − 1、選ばれた組の欄が一致し、出どころの欄を書かない", (name) => {
    const lines = readFileSync(new URL(name, dir), "utf-8")
      .split("\n")
      .filter((line) => line.trim() !== "")
      .map((line) => JSON.parse(line) as Json);
    const meta = lines.find((line) => line.kind === "meta") as unknown as MetaLine;
    const records = lines.filter((line) => line.kind === "record") as unknown as RecordLine[];
    const initialSfen = initialSfenOf(meta);
    const { events } = diagnoseRecords(meta.kifuId, records, DRAFT_RULE_1, initialSfen);
    const moments = diagnosisMomentsOf(meta.kifuId, records, DRAFT_RULE_1, initialSfen, events);
    const all = allPairsOf(meta.kifuId, records, DRAFT_RULE_1, initialSfen, events, { source: "light" });

    const readyRows = readEvaluations(records).length;
    expect(all.pairs.length + all.movesMissing).toBe(readyRows - 1);
    expect(all.rowStandings).toHaveLength(readyRows);
    const selected: MomentPairFields[] = [...moments.rises, ...("state" in moments.maxDrop ? [] : [moments.maxDrop])];
    for (const moment of selected) {
      const pair = all.pairs.find((candidate) => candidate.branchPly === moment.branchPly);
      expect(pair, `branchPly ${moment.branchPly}`).toBeDefined();
      expect(fieldsOf(pair!)).toBe(fieldsOf(moment));
    }
  }, 60_000);
});
