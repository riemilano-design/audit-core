// STEP JSON v0 の T-2〜T-5(docs/STEP_JSON-V0_PLAN_2026-09-15.md 6.2)。Failure Event の 1 行が v0.1 のスキーマを通ることと、
// スキーマが型とずれたら落ちることを見る。**エンジンは起動しない。**
//
// 【実記録だけでは足りない】実記録 41 件が通っても、スキーマの半分は試されない(計画 5.2 の P-3)。
// 変種ごとに固定例を 1 件ずつ置き(T-3)、試した変種の一覧を試験で突き合わせる。lib から出ない変種
// (evaluationBefore の notMeasuredGameEnd・action.playedMove の null)は、実際の 1 行を手で書き換えた値で試す。
// 【ファイルと同じ形で試す】JSON.stringify → JSON.parse を通した値を検証する(undefined の欄は落ちる)。

import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { validate } from "./eventSchema.js";
import { diagnoseRecords, DRAFT_RULE_1, type DiagnosisRule, type FailureEvent } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { FAILURE_EVENT_SCHEMA_VERSION, loadFailureEventSchema, toEventLine } from "./failureEventSchema.js";

const schema = loadFailureEventSchema();
type Json = Record<string, unknown>;
const lineOf = (event: FailureEvent): Json => JSON.parse(JSON.stringify(toEventLine(event))) as Json;
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

// ---- コミット済みの記録(T-4)。out/ は gitignore の対象なので使わない ----
function recordsDirEvents(): FailureEvent[] {
  const dir = new URL("../records/d0-nnue/", import.meta.url);
  return readdirSync(dir)
    .filter((name) => name.endsWith(".jsonl"))
    .sort()
    .flatMap((name) => {
      const lines = readFileSync(new URL(name, dir), "utf-8")
        .split("\n")
        .filter((line) => line.trim().length > 0)
        .map((line) => JSON.parse(line) as { kind: string });
      const meta = lines.find((line) => line.kind === "meta") as MetaLine | undefined;
      const records = lines.filter((line): line is RecordLine => line.kind === "record");
      return eventsOf(meta?.kifuId ?? name, records);
    });
}
const RECORD_EVENTS = recordsDirEvents();

/** lib から出ない変種(手で書き換えた 1 行) */
const HAND_MADE: Record<string, Json> = (() => {
  const base = lineOf(at(T2_EVENTS[0]![1], 49));
  const gameEnd = clone(base);
  (gameEnd.trigger as Json).evaluationBefore = { state: "notMeasuredGameEnd" };
  const noPlayedMove = clone(base);
  (noPlayedMove.action as Json).playedMove = null;
  return { beforeGameEnd: gameEnd, playedMoveNull: noPlayedMove };
})();

describe("T-2: D1 の固定例から作った Failure Event は、版つきで v0.1 のスキーマを通る", () => {
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
    for (const [name, event] of Object.entries(T3)) expect(validate(lineOf(event), schema), name).toEqual([]);
  });

  it("lib から出ない変種(終局の evaluationBefore・playedMove の null)は、手で書き換えた 1 行で通る", () => {
    for (const [name, line] of Object.entries(HAND_MADE)) expect(validate(line, schema), name).toEqual([]);
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

  it("T-2・T-3・T-4 と手で書き換えた値で、スキーマの変種と「無い」の形をすべて試している", () => {
    const lines = [...T2_EVENTS.flatMap(([, events]) => events), ...Object.values(T3), ...RECORD_EVENTS].map(lineOf).concat(Object.values(HAND_MADE));
    const seen = new Set<string>();
    const sign = (value: number | null): string => (value === null ? "null" : value > 0 ? "pos" : "neg");
    for (const line of lines) {
      const event = line as unknown as FailureEvent;
      seen.add(`evaluationBefore.${event.trigger.evaluationBefore.state}`);
      seen.add(`classification.${event.trigger.opponentIntent.classification.column}`);
      seen.add(`shape.${event.trigger.shape.state}`);
      seen.add(`focus.${event.trigger.focus.state}`);
      for (const kind of event.branch.kinds) seen.add(`kinds.${kind}`);
      seen.add(`candidateModes.${event.candidateModes.length > 0 ? "some" : "empty"}`);
      seen.add(`checks.${event.consequences.checks.length > 0 ? "some" : "empty"}`);
      seen.add(`consequences.mate.${event.consequences.mate === null ? "null" : "number"}`);
      seen.add(`windowShort.${event.consequences.windowShort}`);
      seen.add(`diffCp.${event.branch.diffCp === null ? "null" : "number"}`);
      seen.add(`mateAfter.${sign(event.branch.mateAfter)}`);
      seen.add(`playedMove.${event.action.playedMove === null ? "null" : "string"}`);
      seen.add(`bestmoveAtBefore.${event.action.bestmoveAtBefore === null ? "null" : "string"}`);
      seen.add(`refersToIntentId.${event.trigger.opponentIntent.refersToIntentId === null ? "null" : "string"}`);
      if (event.trigger.shape.state === "recorded") seen.add(`refersToShapeId.${event.trigger.shape.refersToShapeId === null ? "null" : "string"}`);
      const before = event.trigger.evaluationBefore;
      if (before.state === "measured") {
        seen.add(`dropCp.${before.dropCp === null ? "null" : "number"}`);
        seen.add(`scoreCp.${before.scoreCp === null ? "null" : "number"}`);
        seen.add(`afterPassScoreCp.${before.afterPassScoreCp === null ? "null" : "number"}`);
        seen.add(`mate.${sign(before.mate)}`);
        seen.add(`afterPassMate.${sign(before.afterPassMate)}`);
      }
    }
    const expected = [
      ...["measured", "notMeasuredGameEnd", "notMeasuredInCheck", "notMeasurable", "unrecorded", "notEvaluation"].map((s) => `evaluationBefore.${s}`),
      ...["noCandidate", "muted", "spokeLatest", "spokeOlder", "undetermined"].map((c) => `classification.${c}`),
      "shape.recorded",
      "shape.unrecorded",
      ...["stated", "nothingToSay", "pending", "unrecorded"].map((s) => `focus.${s}`),
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
    ];
    expect([...expected].filter((tag) => !seen.has(tag))).toEqual([]);
  });
});

describe("T-4: コミット済みの記録 records/d0-nnue の Failure Event が、すべて v0.1 のスキーマを通る", () => {
  it("7 本から作った Failure Event(実測 22 件。件数は固定しない)", () => {
    expect(RECORD_EVENTS.length).toBeGreaterThan(0);
    for (const event of RECORD_EVENTS) expect(validate(lineOf(event), schema), `${event.kifuId}#${event.branchPly}`).toEqual([]);
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
    // 元の 1 行が持つキーの数(数えた: 最上位 10・trigger 4・evaluationBefore 7・opponentIntent 2・classification 1・shape 3・
    // focus 1・action 2・branch 4・consequences 4・candidateModes[0] 3)。道筋の辿り損ねで、消す試しが減っていないことを見る
    expect(tried).toBe(41);
  });

  it("どの入れ物に知らない欄を足しても落ちる", () => {
    for (const path of objectPaths(base)) {
      const broken = clone(base);
      parentAt(broken, path).unexpectedField = 1;
      expect(validate(broken, schema), [...path, "unexpectedField"].join(".")).not.toEqual([]);
    }
  });

  it("版が違えば落ちる", () => {
    expect(validate({ ...base, schemaVersion: "0.2" }, schema)).not.toEqual([]);
  });
});
