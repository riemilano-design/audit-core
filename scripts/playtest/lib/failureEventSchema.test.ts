// STEP JSON v0 の T-2〜T-5(docs/STEP_JSON-V0_PLAN_2026-09-15.md 6.2)と、STEP JSON v0.2 の P-2〜P-5・P-7
// (docs/STEP_JSON-V0.2_PLAN_2026-09-15.md 5.・6.2)。Failure Event の 1 行が今の版(0.2)のスキーマを通ることと、
// スキーマが型とずれたら落ちることを見る。**エンジンは起動しない。**
//
// 【実記録だけでは足りない】実記録が通っても、スキーマの半分は試されない(v0 計画 5.2 の P-3)。
// 変種ごとに固定例を 1 件ずつ置き(T-3)、試した変種の一覧を試験で突き合わせる。lib から出ない変種
// (evaluationBefore の notMeasuredGameEnd・action.playedMove の null・evaluationAfter の measured 以外・kingSurroundings の null)は、
// 実際の 1 行を手で書き換えた値で試す。出どころ(provenance)の変種は、組み立ての関数に違う入力を渡して作る。
// 【ファイルと同じ形で試す】JSON.stringify → JSON.parse を通した値を検証する(undefined の欄は落ちる)。
// 【件数は固定しない】P-1(131 件)と P-6(玉の周りの中央値)は実記録の値なので、試験でなく実装の記録で数える(P-20)。

import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { validate } from "./eventSchema.js";
import { diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, readEvaluations, type DiagnosisRule, type FailureEvent } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import {
  buildProvenance,
  FAILURE_EVENT_SCHEMA_VERSION,
  loadFailureEventSchema,
  pathForProvenance,
  provenanceMetaOf,
  recordSha256,
  toEventLine,
  type Provenance,
  type ProvenanceInput,
} from "./failureEventSchema.js";

const schema = loadFailureEventSchema();
const schemaV01 = loadFailureEventSchema("0.1");
type Json = Record<string, unknown>;
const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));

const FIXTURE_META = {
  kind: "meta",
  kifuId: "fixture",
  startedAt: "t",
  gitHead: "0cce0c3",
  dirty: false,
  enginePath: `${REPO_ROOT}apps/server/engine/nnue/YaneuraOu-by-gcc`,
  searchMode: "nodes",
  nodes: 4_000_000,
  threads: 1,
} as MetaLine;
const provenanceInput = (overrides: Partial<ProvenanceInput> = {}): ProvenanceInput => ({
  recordPath: `${REPO_ROOT}scripts/playtest/records/fixture.jsonl`,
  recordSha256: "0".repeat(64),
  meta: FIXTURE_META,
  evaluator: "試験の評価関数",
  analysisGit: { gitHead: "1dfbaa7", dirty: false },
  rule: DRAFT_RULE_1,
  notEvaluationCp: NOT_EVALUATION_CP,
  repoRoot: REPO_ROOT,
  ...overrides,
});
const FIXTURE_PROVENANCE = buildProvenance(provenanceInput());

const lineOf = (event: FailureEvent, provenance: Provenance = FIXTURE_PROVENANCE): Json =>
  JSON.parse(JSON.stringify(toEventLine(event, provenance))) as Json;
const eventsOf = (kifuId: string, records: readonly RecordLine[], rule: DiagnosisRule = DRAFT_RULE_1) => diagnoseRecords(kifuId, records, rule).events;
const at = (events: FailureEvent[], branchPly: number): FailureEvent => {
  const event = events.find((e) => e.branchPly === branchPly);
  if (event === undefined) throw new Error(`分岐点 ${branchPly} の Failure Event が無い`);
  return event;
};
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const withAfterPassMate = engineRef(0, { afterPassMate: 3 });

// ---- 固定例(D1 の植え方 ― T-2)----
const F1 = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }), 50: engineRef(-300) });
const T2_EVENTS: Array<[string, FailureEvent[]]> = [
  ["F-1", eventsOf("F-1", F1)],
  ["F-2", eventsOf("F-2", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }))],
  ["F-3", eventsOf("F-3", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(-300) }))],
  ["F-4", eventsOf("F-4", plantedRecords(GAME01_MOVES.slice(0, 30), { 26: engineRef(500), 28: engineRef(-300) }))],
  ["F-6i", eventsOf("F-6i", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(null, { mate: -3 }) }))],
  ["F-6ii", eventsOf("F-6ii", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(350, { afterPassMate: 5 }) }))],
  ["mateAfterOnly", eventsOf("m1", plantedRecords(GAME01_MOVES.slice(0, 4), { 0: "absent", 2: engineRef(500), 4: engineRef(null, { mate: -3 }) }))],
];

// ---- 変種を埋める固定例(T-3)。**変種ごとに 1 件**。GAME01 で先手が王手中の ready 行は 34・36・38・40・52・54(56 で詰み)----
const removeStages = (records: RecordLine[], ply: number, stages: string[]): RecordLine[] =>
  records.map((record) =>
    record.ply === ply ? { ...record, response: { ...record.response, coach: (record.response.coach ?? []).filter((c) => !stages.includes(c.stage)) } } : record,
  );
const T3: Record<string, FailureEvent> = {
  beforeInCheck: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 42: withAfterPassMate })), 41),
  beforeNotMeasurable: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: null, 22: withAfterPassMate })), 21),
  beforeNotEvaluation: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(-4824, { afterPassScoreCp: 35281 }), 22: withAfterPassMate })), 21),
  beforeUnrecorded: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: "absent", 22: withAfterPassMate })), 21),
  shapeUnrecordedAndUndetermined: at(
    eventsOf("t3", removeStages(plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(-300) }), 20, ["current_shape", "opponent_next_aim"])),
    21,
  ),
  focusStated: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }, { 20: { focusTextState: "ready", focusText: "テストの文" } })), 21),
  focusPending: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }, { 20: { focusTextState: "pending", focusText: null } })), 21),
  focusUnrecorded: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }, { 20: "absent" })), 21),
  mateInWindow: at(eventsOf("t3", F1, { ...DRAFT_RULE_1, windowPlies: 7 }), 49),
  // measured の中の値の枝(規則 11.8。監査 B の必須 2): 実記録に baseline.mate は 0 件、afterPass.mate は正だけ。
  // どれも直後の行の afterPass.mate で matedIfPass として当てる
  beforeMatePositive: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(null, { mate: 5 }), 22: withAfterPassMate })), 21),
  beforeMateNegative: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(null, { mate: -5 }), 22: withAfterPassMate })), 21),
  beforeAfterPassMateNegative: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(100, { afterPassMate: -3 }), 22: withAfterPassMate })), 21),
  mateAfterPositive: at(eventsOf("t3", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(null, { mate: 3, afterPassMate: 5 }) })), 21),
};

// ---- コミット済みの記録(T-4・P-2〜P-5)。out/ は gitignore の対象なので使わない ----
interface CommittedRecord {
  dir: string;
  name: string;
  bytes: Buffer;
  meta: MetaLine | undefined;
  records: RecordLine[];
  events: FailureEvent[];
}
const RECORD_DIRS = ["d0-nnue", "d3-nnue"];
function committedRecords(): CommittedRecord[] {
  return RECORD_DIRS.flatMap((dirName) => {
    const dir = new URL(`../records/${dirName}/`, import.meta.url);
    return readdirSync(dir)
      .filter((name) => name.endsWith(".jsonl"))
      .sort()
      .map((name) => {
        const bytes = readFileSync(new URL(name, dir));
        const lines = bytes
          .toString("utf-8")
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line) => JSON.parse(line) as { kind: string });
        const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
        const records = lines.filter((line): line is RecordLine => line.kind === "record");
        return { dir: dirName, name, bytes, meta, records, events: eventsOf(meta?.kifuId ?? name, records) };
      });
  });
}
const COMMITTED = committedRecords();
const provenanceOfCommitted = (record: CommittedRecord): Provenance =>
  buildProvenance(
    provenanceInput({
      recordPath: `${REPO_ROOT}scripts/playtest/records/${record.dir}/${record.name}`,
      recordSha256: recordSha256(record.bytes),
      meta: record.meta,
    }),
  );
const RECORD_LINES: Json[] = COMMITTED.flatMap((record) => record.events.map((event) => lineOf(event, provenanceOfCommitted(record))));
const RECORD_EVENTS: FailureEvent[] = COMMITTED.flatMap((record) => record.events);

/** lib から出ない変種(手で書き換えた 1 行) */
const HAND_MADE: Record<string, Json> = (() => {
  const base = lineOf(at(T2_EVENTS[0]![1], 49));
  const withChange = (change: (line: Json) => void): Json => {
    const line = clone(base);
    change(line);
    return line;
  };
  const lines: Record<string, Json> = {
    beforeGameEnd: withChange((line) => ((line.trigger as Json).evaluationBefore = { state: "notMeasuredGameEnd" })),
    playedMoveNull: withChange((line) => ((line.action as Json).playedMove = null)),
    kingSurroundingsNull: withChange((line) => ((line.trigger as Json).kingSurroundings = null)),
  };
  for (const state of ["notMeasuredGameEnd", "notMeasuredInCheck", "notMeasurable", "unrecorded", "notEvaluation"]) {
    lines[`after_${state}`] = withChange((line) => ((line.branch as Json).evaluationAfter = { state }));
  }
  return lines;
})();

/** 出どころの変種(組み立ての関数に違う入力を渡す。行は F-1 の分岐点 49) */
const PROVENANCE_VARIANTS: Record<string, Provenance> = {
  metaAbsent: buildProvenance(provenanceInput({ meta: undefined })),
  metaOldRecord: buildProvenance(provenanceInput({ meta: { kind: "meta", kifuId: "old", startedAt: "t", gitHead: null } as unknown as MetaLine })),
  metaDirty: buildProvenance(provenanceInput({ meta: { ...FIXTURE_META, dirty: true } })),
  metaUnmeasured: buildProvenance(provenanceInput({ meta: { ...FIXTURE_META, dirty: null } as unknown as MetaLine })),
  evaluatorAbsent: buildProvenance(provenanceInput({ evaluator: null })),
  analysisDirty: buildProvenance(provenanceInput({ analysisGit: { gitHead: "1dfbaa7", dirty: true } })),
  analysisUnmeasured: buildProvenance(provenanceInput({ analysisGit: { gitHead: null, dirty: null } })),
  recordOutsideRepo: buildProvenance(provenanceInput({ recordPath: "/tmp/elsewhere/game.jsonl" })),
  // replay.ts --nodes 0(時間で打ち切る探索)の meta と同じ形(B が実際に回して確かめた形)。nodes の 0 は null にしない
  metaMovetime: buildProvenance(provenanceInput({ meta: { ...FIXTURE_META, searchMode: "movetime", nodes: 0, referenceNodes: 4_000_000 } as MetaLine })),
};
const PROVENANCE_LINES: Record<string, Json> = Object.fromEntries(
  Object.entries(PROVENANCE_VARIANTS).map(([name, provenance]) => [name, lineOf(at(T2_EVENTS[0]![1], 49), provenance)]),
);

describe("T-2: D1 の固定例から作った Failure Event は、版つきで今の版のスキーマを通る", () => {
  it.each(T2_EVENTS)("%s", (_name, events) => {
    expect(events.length).toBeGreaterThan(0);
    for (const event of events) {
      const line = lineOf(event);
      expect(Object.keys(line)[0]).toBe("schemaVersion");
      expect(line.schemaVersion).toBe(FAILURE_EVENT_SCHEMA_VERSION);
      expect(validate(line, schema), `分岐点 ${event.branchPly}`).toEqual([]);
    }
  });
});

describe("T-3: 変種ごとの固定例(実記録に出ない変種を埋める)", () => {
  it("lib から出る変種は、それぞれ期待した変種になり、スキーマを通る", () => {
    expect(T3.beforeInCheck!.trigger.evaluationBefore).toEqual({ state: "notMeasuredInCheck" });
    expect(T3.beforeNotMeasurable!.trigger.evaluationBefore).toEqual({ state: "notMeasurable" });
    expect(T3.beforeNotEvaluation!.trigger.evaluationBefore).toEqual({ state: "notEvaluation" });
    expect(T3.beforeUnrecorded!.trigger.evaluationBefore).toEqual({ state: "unrecorded" });
    expect(T3.shapeUnrecordedAndUndetermined!.trigger.shape).toEqual({ state: "unrecorded" });
    expect(T3.shapeUnrecordedAndUndetermined!.trigger.opponentIntent.classification).toEqual({ column: "undetermined", reason: "U-1" });
    expect(T3.focusStated!.trigger.focus).toEqual({ state: "stated", text: "テストの文" });
    expect(T3.focusPending!.trigger.focus).toEqual({ state: "pending" });
    expect(T3.focusUnrecorded!.trigger.focus).toEqual({ state: "unrecorded" });
    expect(T3.mateInWindow!.consequences).toEqual({ checks: [52, 54, 56], mate: 56, windowPlies: 7, windowShort: false });
    expect(T3.beforeMatePositive!.trigger.evaluationBefore).toMatchObject({ state: "measured", scoreCp: null, mate: 5 });
    expect(T3.beforeMateNegative!.trigger.evaluationBefore).toMatchObject({ state: "measured", scoreCp: null, mate: -5 });
    expect(T3.beforeAfterPassMateNegative!.trigger.evaluationBefore).toMatchObject({ state: "measured", afterPassMate: -3 });
    expect(T3.mateAfterPositive!.branch).toMatchObject({ kinds: ["matedIfPass"], mateAfter: 3 });
    expect(T3.mateAfterPositive!.branch.evaluationAfter).toMatchObject({ state: "measured", scoreCp: null, mate: 3, afterPassMate: 5 });
    for (const [name, event] of Object.entries(T3)) expect(validate(lineOf(event), schema), name).toEqual([]);
  });

  it("lib から出ない変種(終局の evaluationBefore・playedMove の null・evaluationAfter の measured 以外・kingSurroundings の null)は、手で書き換えた 1 行で通る", () => {
    for (const [name, line] of Object.entries(HAND_MADE)) expect(validate(line, schema), name).toEqual([]);
  });

  it("出どころの変種(meta 行なし・古い記録・汚れの 4 値・自己申告なし・根の外の記録・時間で打ち切る探索の記録)は、組み立てた 1 行で通る", () => {
    expect(PROVENANCE_VARIANTS.metaAbsent!.record.meta).toBeNull();
    expect(PROVENANCE_VARIANTS.metaOldRecord!.record.meta).toEqual({
      gitHead: null,
      dirty: "unrecorded",
      enginePath: null,
      searchMode: null,
      nodes: null,
      threads: null,
      unrecordedKeys: ["dirty", "enginePath", "searchMode", "nodes", "threads"],
    });
    expect(PROVENANCE_VARIANTS.metaDirty!.record.meta?.dirty).toBe("dirty");
    expect(PROVENANCE_VARIANTS.metaUnmeasured!.record.meta?.dirty).toBe("unmeasured");
    expect(FIXTURE_PROVENANCE.record.meta?.dirty).toBe("clean");
    expect(PROVENANCE_VARIANTS.evaluatorAbsent!.evaluator).toEqual({ declared: null });
    expect(PROVENANCE_VARIANTS.analysisDirty!.analysis.dirty).toBe("dirty");
    expect(PROVENANCE_VARIANTS.analysisUnmeasured!.analysis).toMatchObject({ gitHead: null, dirty: "unmeasured" });
    expect(PROVENANCE_VARIANTS.recordOutsideRepo!.record.path).toBe("game.jsonl");
    expect(PROVENANCE_VARIANTS.metaMovetime!.record.meta).toMatchObject({ searchMode: "movetime", nodes: 0, threads: 1, unrecordedKeys: [] });
    for (const [name, line] of Object.entries(PROVENANCE_LINES)) expect(validate(line, schema), name).toEqual([]);
  });

  it("値域の境目は手で書いた 1 行で試す: cp は ±29999 まで通り ±30000 は落ちる(lib は notEvaluation にする)、mate は 0 を通さない", () => {
    const base = lineOf(at(T2_EVENTS[0]![1], 49));
    expect(((base.trigger as Json).evaluationBefore as Json).state).toBe("measured");
    const withBefore = (patch: Json): Json => {
      const line = clone(base);
      Object.assign((line.trigger as Json).evaluationBefore as Json, patch);
      return line;
    };
    const withBranch = (patch: Json): Json => {
      const line = clone(base);
      Object.assign(line.branch as Json, patch);
      return line;
    };
    for (const cp of [29999, -29999]) {
      expect(validate(withBefore({ scoreCp: cp }), schema), `scoreCp ${cp}`).toEqual([]);
      expect(validate(withBefore({ afterPassScoreCp: cp }), schema), `afterPassScoreCp ${cp}`).toEqual([]);
    }
    for (const cp of [30000, -30000]) {
      expect(validate(withBefore({ scoreCp: cp }), schema), `scoreCp ${cp}`).not.toEqual([]);
      expect(validate(withBefore({ afterPassScoreCp: cp }), schema), `afterPassScoreCp ${cp}`).not.toEqual([]);
    }
    expect(validate(withBefore({ mate: 0 }), schema), "mate 0").not.toEqual([]);
    expect(validate(withBefore({ afterPassMate: 0 }), schema), "afterPassMate 0").not.toEqual([]);
    expect(validate(withBranch({ mateAfter: 0 }), schema), "mateAfter 0").not.toEqual([]);
  });

  it("v0.2 の欄の境目: 玉の周りのマスは 3・5・8、駒は 0〜8。出どころは sha256 が 64 桁の小文字、パスは絶対パスでない、自己申告は空でない、探索の節は 0 以上", () => {
    const base = lineOf(at(T2_EVENTS[0]![1], 49));
    const withKing = (value: unknown): Json => {
      const line = clone(base);
      (line.trigger as Json).kingSurroundings = value;
      return line;
    };
    for (const ok of [{ squares: 3, own: 0 }, { squares: 5, own: 5 }, { squares: 8, own: 8 }]) expect(validate(withKing(ok), schema), JSON.stringify(ok)).toEqual([]);
    for (const ng of [{ squares: 4, own: 0 }, { squares: 8, own: 9 }, { squares: 8, own: -1 }]) expect(validate(withKing(ng), schema), JSON.stringify(ng)).not.toEqual([]);
    const withProvenance = (change: (provenance: Json) => void): Json => {
      const line = clone(base);
      change(line.provenance as Json);
      return line;
    };
    expect(validate(withProvenance((p) => ((p.record as Json).sha256 = "A".repeat(64))), schema), "大文字の sha256").not.toEqual([]);
    expect(validate(withProvenance((p) => ((p.record as Json).sha256 = "0".repeat(63))), schema), "63 桁の sha256").not.toEqual([]);
    expect(validate(withProvenance((p) => ((p.record as Json).path = "/Users/someone/game.jsonl")), schema), "絶対パス").not.toEqual([]);
    expect(validate(withProvenance((p) => (((p.record as Json).meta as Json).enginePath = "/Users/someone/engine")), schema), "エンジンの絶対パス").not.toEqual([]);
    expect(validate(withProvenance((p) => ((p.evaluator as Json).declared = "")), schema), "空の自己申告").not.toEqual([]);
    expect(validate(withProvenance((p) => (((p.record as Json).meta as Json).nodes = 0)), schema), "nodes 0(時間で打ち切る探索)").toEqual([]);
    expect(validate(withProvenance((p) => (((p.record as Json).meta as Json).nodes = -1)), schema), "nodes -1").not.toEqual([]);
    expect(validate(withProvenance((p) => ((p.analysis as Json).dirty = "unrecorded")), schema), "解析の汚れに記録していない").not.toEqual([]);
  });

  it("T-2・T-3・T-4 と手で書き換えた値で、スキーマの変種と「無い」の形をすべて試している", () => {
    const lines = [...T2_EVENTS.flatMap(([, events]) => events), ...Object.values(T3)]
      .map((event) => lineOf(event))
      .concat(RECORD_LINES, Object.values(HAND_MADE), Object.values(PROVENANCE_LINES));
    const seen = new Set<string>();
    const sign = (value: number | null): string => (value === null ? "null" : value > 0 ? "pos" : "neg");
    const nullOr = (value: unknown, kind: string): string => (value === null ? "null" : kind);
    for (const line of lines) {
      const event = line as unknown as FailureEvent & { provenance: Provenance };
      seen.add(`evaluationBefore.${event.trigger.evaluationBefore.state}`);
      seen.add(`evaluationAfter.${event.branch.evaluationAfter.state}`);
      seen.add(`classification.${event.trigger.opponentIntent.classification.column}`);
      seen.add(`shape.${event.trigger.shape.state}`);
      seen.add(`focus.${event.trigger.focus.state}`);
      seen.add(`kingSurroundings.${nullOr(event.trigger.kingSurroundings, "object")}`);
      for (const kind of event.branch.kinds) seen.add(`kinds.${kind}`);
      seen.add(`candidateModes.${event.candidateModes.length > 0 ? "some" : "empty"}`);
      seen.add(`checks.${event.consequences.checks.length > 0 ? "some" : "empty"}`);
      seen.add(`consequences.mate.${nullOr(event.consequences.mate, "number")}`);
      seen.add(`windowShort.${event.consequences.windowShort}`);
      seen.add(`diffCp.${nullOr(event.branch.diffCp, "number")}`);
      seen.add(`mateAfter.${sign(event.branch.mateAfter)}`);
      seen.add(`playedMove.${nullOr(event.action.playedMove, "string")}`);
      seen.add(`bestmoveAtBefore.${nullOr(event.action.bestmoveAtBefore, "string")}`);
      seen.add(`refersToIntentId.${nullOr(event.trigger.opponentIntent.refersToIntentId, "string")}`);
      if (event.trigger.shape.state === "recorded") seen.add(`refersToShapeId.${nullOr(event.trigger.shape.refersToShapeId, "string")}`);
      const before = event.trigger.evaluationBefore;
      if (before.state === "measured") {
        seen.add(`dropCp.${nullOr(before.dropCp, "number")}`);
        seen.add(`scoreCp.${nullOr(before.scoreCp, "number")}`);
        seen.add(`afterPassScoreCp.${nullOr(before.afterPassScoreCp, "number")}`);
        seen.add(`mate.${sign(before.mate)}`);
        seen.add(`afterPassMate.${sign(before.afterPassMate)}`);
      }
      const provenance = event.provenance;
      seen.add(`provenance.meta.${nullOr(provenance.record.meta, "object")}`);
      const meta = provenance.record.meta;
      if (meta !== null) {
        seen.add(`provenance.meta.dirty.${meta.dirty}`);
        seen.add(`provenance.meta.gitHead.${nullOr(meta.gitHead, "string")}`);
        seen.add(`provenance.meta.enginePath.${nullOr(meta.enginePath, "string")}`);
        seen.add(`provenance.meta.nodes.${meta.nodes === 0 ? "zero" : nullOr(meta.nodes, "number")}`);
        seen.add(`provenance.meta.unrecordedKeys.${meta.unrecordedKeys.length > 0 ? "some" : "empty"}`);
      }
      seen.add(`provenance.evaluator.${nullOr(provenance.evaluator.declared, "string")}`);
      seen.add(`provenance.analysis.gitHead.${nullOr(provenance.analysis.gitHead, "string")}`);
      seen.add(`provenance.analysis.dirty.${provenance.analysis.dirty}`);
    }
    const states = ["measured", "notMeasuredGameEnd", "notMeasuredInCheck", "notMeasurable", "unrecorded", "notEvaluation"];
    const expected = [
      ...states.map((s) => `evaluationBefore.${s}`),
      ...states.map((s) => `evaluationAfter.${s}`),
      ...["noCandidate", "muted", "spokeLatest", "spokeOlder", "undetermined"].map((c) => `classification.${c}`),
      "shape.recorded",
      "shape.unrecorded",
      ...["stated", "nothingToSay", "pending", "unrecorded"].map((s) => `focus.${s}`),
      "kingSurroundings.null",
      "kingSurroundings.object",
      "kinds.cpDrop",
      "kinds.mateDrop",
      "kinds.matedIfPass",
      "candidateModes.some",
      "candidateModes.empty",
      "checks.some",
      "checks.empty",
      "consequences.mate.null",
      "consequences.mate.number",
      "windowShort.true",
      "windowShort.false",
      "diffCp.null",
      "diffCp.number",
      ...["null", "pos", "neg"].map((s) => `mateAfter.${s}`),
      "playedMove.null",
      "playedMove.string",
      "bestmoveAtBefore.null",
      "bestmoveAtBefore.string",
      "refersToIntentId.null",
      "refersToIntentId.string",
      "refersToShapeId.null",
      "refersToShapeId.string",
      "dropCp.null",
      "dropCp.number",
      "scoreCp.null",
      "scoreCp.number",
      "afterPassScoreCp.null",
      "afterPassScoreCp.number",
      ...["null", "pos", "neg"].map((s) => `mate.${s}`),
      ...["null", "pos", "neg"].map((s) => `afterPassMate.${s}`),
      "provenance.meta.null",
      "provenance.meta.object",
      ...["dirty", "clean", "unrecorded", "unmeasured"].map((s) => `provenance.meta.dirty.${s}`),
      "provenance.meta.gitHead.null",
      "provenance.meta.gitHead.string",
      "provenance.meta.enginePath.null",
      "provenance.meta.enginePath.string",
      "provenance.meta.nodes.null",
      "provenance.meta.nodes.number",
      "provenance.meta.nodes.zero",
      "provenance.meta.unrecordedKeys.empty",
      "provenance.meta.unrecordedKeys.some",
      "provenance.evaluator.null",
      "provenance.evaluator.string",
      "provenance.analysis.gitHead.null",
      "provenance.analysis.gitHead.string",
      ...["dirty", "clean", "unmeasured"].map((s) => `provenance.analysis.dirty.${s}`),
    ];
    expect([...expected].filter((tag) => !seen.has(tag))).toEqual([]);
  });
});

describe("T-4: コミット済みの記録 records/d0-nnue・records/d3-nnue の Failure Event が、すべて今の版のスキーマを通る", () => {
  it("27 本から作った Failure Event(件数は固定しない)", () => {
    expect(COMMITTED.map((record) => record.dir)).toEqual(expect.arrayContaining(RECORD_DIRS));
    expect(RECORD_LINES.length).toBeGreaterThan(0);
    for (const line of RECORD_LINES) expect(validate(line, schema), `${String(line.kifuId)}#${String(line.branchPly)}`).toEqual([]);
  });
});

describe("T-5: 型とスキーマのずれ(欄を消す・知らない欄を足すと落ちる)", () => {
  // 候補の型まで入った 1 行(F-1 の分岐点 49: candidateModes が 1 件)を元にする
  const base = lineOf(at(T2_EVENTS[0]![1], 49));

  const objectPaths = (value: unknown, path: Array<string | number> = []): Array<Array<string | number>> => {
    if (Array.isArray(value)) return value.flatMap((item, index) => objectPaths(item, [...path, index]));
    if (typeof value !== "object" || value === null) return [];
    return [path, ...Object.entries(value).flatMap(([key, child]) => objectPaths(child, [...path, key]))];
  };
  const parentAt = (root: Json, path: Array<string | number>): Json =>
    path.reduce<unknown>((node, key) => (node as Record<string | number, unknown>)[key], root) as Json;

  it("元の 1 行は通る(前提)", () => {
    expect(validate(base, schema)).toEqual([]);
    expect((base.candidateModes as unknown[]).length).toBe(1);
  });

  it("どの欄を 1 つ消しても落ちる", () => {
    let tried = 0;
    for (const path of objectPaths(base)) {
      for (const key of Object.keys(parentAt(base, path))) {
        const broken = clone(base);
        delete parentAt(broken, path)[key];
        expect(validate(broken, schema), [...path, key].join(".")).not.toEqual([]);
        tried += 1;
      }
    }
    // 元の 1 行が持つキーの数(数えた: 最上位 11・trigger 5・evaluationBefore 7・opponentIntent 2・classification 1・shape 3・
    // focus 1・kingSurroundings 2・action 2・branch 5・evaluationAfter 7・consequences 4・candidateModes[0] 3・
    // provenance 3・record 3・meta 7・evaluator 1・analysis 3・rule 5)。道筋の辿り損ねで、消す試しが減っていないことを見る
    expect(tried).toBe(75);
  });

  it("どの入れ物に知らない欄を足しても落ちる", () => {
    for (const path of objectPaths(base)) {
      const broken = clone(base);
      parentAt(broken, path).unexpectedField = 1;
      expect(validate(broken, schema), [...path, "unexpectedField"].join(".")).not.toEqual([]);
    }
  });

  it("版が違えば落ちる", () => {
    expect(validate({ ...base, schemaVersion: "0.1" }, schema)).not.toEqual([]);
  });
});

describe("STEP JSON v0.2 の約束(計画 5. の P-2〜P-5・P-7)", () => {
  it("P-2: evaluationAfter は直後の行(toReadyPly)の評価そのもので、コミット済みの記録ではすべて measured", () => {
    for (const record of COMMITTED) {
      const rows = readEvaluations(record.records);
      for (const event of record.events) {
        const to = rows.find((row) => row.ply === event.toReadyPly);
        expect(event.branch.evaluationAfter, `${record.name}#${event.branchPly}`).toEqual(to?.evaluation);
        expect(event.branch.evaluationAfter.state).toBe("measured");
      }
    }
  });

  it("P-3: bestmoveAtBefore は「evaluationBefore が measured ならその bestmove、でなければ null」と等しい(2 つの理由は同じ行で読める ― K-6 (a))", () => {
    const events = [...T2_EVENTS.flatMap(([, list]) => list), ...Object.values(T3), ...RECORD_EVENTS];
    for (const event of events) {
      const before = event.trigger.evaluationBefore;
      expect(event.action.bestmoveAtBefore, `${event.kifuId}#${event.branchPly}`).toBe(before.state === "measured" ? before.bestmove : null);
    }
  });

  it("P-4: 記録のファイルの sha256 は、各フォルダの SHA256SUMS と一致する", () => {
    for (const dir of RECORD_DIRS) {
      const sums = new Map(
        readFileSync(new URL(`../records/${dir}/SHA256SUMS`, import.meta.url), "utf-8")
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line) => {
            const [sha, name] = line.trim().split(/\s+/);
            return [name!, sha!] as const;
          }),
      );
      const records = COMMITTED.filter((record) => record.dir === dir);
      expect(records.length).toBe(sums.size);
      for (const record of records) expect(recordSha256(record.bytes), `${dir}/${record.name}`).toBe(sums.get(record.name));
    }
  });

  it("P-5: コミット済みの記録の meta は欠けなし(unrecordedKeys が空)で、エンジンのパスは根からの相対になる", () => {
    for (const record of COMMITTED) {
      const meta = provenanceMetaOf(record.meta, REPO_ROOT);
      expect(meta?.unrecordedKeys, record.name).toEqual([]);
      expect(meta?.enginePath, record.name).toMatch(/^apps\/server\/engine\//);
    }
  });

  it("P-7: 0.2 の行は v0.2 のスキーマを通り v0.1 のスキーマでは落ちる。0.2 で足した欄を外して版を 0.1 にした行は v0.1 を通る", () => {
    const lines = [...T2_EVENTS.flatMap(([, events]) => events).map((event) => lineOf(event)), ...RECORD_LINES];
    for (const line of lines) {
      expect(validate(line, schema)).toEqual([]);
      expect(validate(line, schemaV01)).not.toEqual([]);
      const old = clone(line);
      old.schemaVersion = "0.1";
      delete old.provenance;
      delete (old.branch as Json).evaluationAfter;
      delete (old.trigger as Json).kingSurroundings;
      expect(validate(old, schemaV01), `${String(line.kifuId)}#${String(line.branchPly)}`).toEqual([]);
    }
  });

  it("パスは根の中なら相対(区切りは /)、外ならエンジンの置き場所から後ろ、それも無ければファイル名だけ。絶対パスは返さない", () => {
    expect(pathForProvenance(`${REPO_ROOT}scripts/playtest/records/d0-nnue/a.jsonl`, REPO_ROOT)).toBe("scripts/playtest/records/d0-nnue/a.jsonl");
    expect(pathForProvenance("/Users/someone/Desktop/sgogi-coach/apps/server/engine/nnue/YaneuraOu-by-gcc", "/private/tmp/wt")).toBe(
      "apps/server/engine/nnue/YaneuraOu-by-gcc",
    );
    expect(pathForProvenance("/tmp/elsewhere/game.jsonl", REPO_ROOT)).toBe("game.jsonl");
    expect(pathForProvenance(`${REPO_ROOT}../sibling/x.jsonl`, REPO_ROOT)).toBe("x.jsonl");
  });

  it("規則の値は、渡した規則をそのまま写す(固定の値にしない)", () => {
    const rule = { advantageCp: 123, dropCp: -456, windowPlies: 7, focusDropCp: 89 };
    expect(buildProvenance(provenanceInput({ rule, notEvaluationCp: 31000 })).analysis.rule).toEqual({ ...rule, notEvaluationCp: 31000 });
  });
});
