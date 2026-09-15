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
// 【STEP JSON V0.3-META】記録の meta の 7 欄(docs/STEP_JSON-V0.3-META_PLAN_2026-09-15.md 6.2): 7 変種の固定例(meta は本番の関数で作る)・
// 元の meta を基準にした対応の試験(門の分類はこのファイルの中で書く)・K-3 の食い違い(値の形まで)・スキーマの境目。

import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { validate } from "./eventSchema.js";
import { diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, readEvaluations, type DiagnosisRule, type FailureEvent } from "./failureEvent.js";
import { engineRef, FOLD_START, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import {
  buildProvenance,
  FAILURE_EVENT_SCHEMA_VERSION,
  InvalidProvenanceMetaError,
  loadFailureEventSchema,
  pathForProvenance,
  PROVENANCE_META_KEYS,
  provenanceMetaOf,
  recordSha256,
  START_SFEN_PATTERN,
  toEventLine,
  USI_MOVE_PATTERN,
  type Provenance,
  type ProvenanceInput,
} from "./failureEventSchema.js";
import { planReplayMoves, truncationMetaFields } from "./replayPlan.js";
import { alignMovesToSente, sideMetaFields } from "./sideAlignment.js";

const schema = loadFailureEventSchema();
const schemaV01 = loadFailureEventSchema("0.1");
const schemaV02 = loadFailureEventSchema("0.2");
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
const eventsOf = (kifuId: string, records: readonly RecordLine[], rule: DiagnosisRule = DRAFT_RULE_1) => diagnoseRecords(kifuId, records, rule, DEFAULT_INITIAL_SFEN).events;
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
// STEP JSON V0.3-META: real-01(meta に打ち切りの組だけがある記録 ― 計画 F-2・6.2)を足した
const RECORD_DIRS = ["d0-nnue", "d3-nnue", "real-01"];
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

// ---- STEP JSON V0.3-META の 7 変種(計画 2.3・6.2)。meta の 7 欄は、replay.ts と同じ本番の関数で作る ----
/** V0.3-META で足した 7 欄の名前(K-4 の順)。lib の定数を使わず、ここに書く */
const V03_KEYS = ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"];
const FIVE_MOVES = ["7g7f", "3c3d", "2g2f", "8c8d", "2f2e"]; // 本人が先手なら 5 手(奇数)、後手の局として回すと 4 手(偶数)
const FOUR_MOVES = ["7g7f", "3c3d", "2g2f", "8c8d"]; // 本人が先手なら 4 手(偶数)、回すと 3 手(奇数。落とすのは回した 2g2f)
const sideAndTruncationOfKifu = (original: readonly string[], userSide: "sente" | "gote", sideAlignmentChecked: boolean): Record<string, unknown> => {
  const aligned = alignMovesToSente(original, userSide);
  return { ...sideMetaFields(aligned.alignment), sideAlignmentChecked, ...truncationMetaFields(planReplayMoves(aligned.moves)) };
};
const V03_METAS: Record<string, MetaLine> = {
  absent_absent: FIXTURE_META,
  absent_notTruncated: { ...FIXTURE_META, ...truncationMetaFields(planReplayMoves(FOUR_MOVES)) } as MetaLine,
  absent_truncated: { ...FIXTURE_META, ...truncationMetaFields(planReplayMoves(FIVE_MOVES)) } as MetaLine,
  notMirrored_notTruncated: { ...FIXTURE_META, ...sideAndTruncationOfKifu(FOUR_MOVES, "sente", false) } as MetaLine,
  notMirrored_truncated: { ...FIXTURE_META, ...sideAndTruncationOfKifu(FIVE_MOVES, "sente", false) } as MetaLine,
  mirrored_notTruncated: { ...FIXTURE_META, ...sideAndTruncationOfKifu(FIVE_MOVES, "gote", true) } as MetaLine,
  mirrored_truncated: { ...FIXTURE_META, ...sideAndTruncationOfKifu(FOUR_MOVES, "gote", false) } as MetaLine,
};
/** 手で書いた期待値(写る 7 欄の値と unrecordedKeys)。本番の関数の出力と突き合わせる(校正) */
const V03_EXPECTED: Record<string, { fields: Record<string, unknown>; unrecordedKeys: string[] }> = {
  absent_absent: { fields: {}, unrecordedKeys: ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"] },
  absent_notTruncated: { fields: { trailingMoveTruncated: false }, unrecordedKeys: ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked"] },
  absent_truncated: { fields: { trailingMoveTruncated: true, truncatedTrailingMove: "2f2e" }, unrecordedKeys: ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked"] },
  notMirrored_notTruncated: { fields: { mirrored: false, sideAlignmentChecked: false, trailingMoveTruncated: false }, unrecordedKeys: [] },
  notMirrored_truncated: { fields: { mirrored: false, sideAlignmentChecked: false, trailingMoveTruncated: true, truncatedTrailingMove: "2f2e" }, unrecordedKeys: [] },
  mirrored_notTruncated: {
    fields: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FOLD_START, sideAlignmentChecked: true, trailingMoveTruncated: false },
    unrecordedKeys: [],
  },
  mirrored_truncated: {
    fields: { mirrored: true, originalUserSide: "gote", plyOffset: 1, startSfen: FOLD_START, sideAlignmentChecked: false, trailingMoveTruncated: true, truncatedTrailingMove: "2g2f" },
    unrecordedKeys: [],
  },
};

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
  // STEP JSON V0.3-META の 7 変種
  ...Object.fromEntries(Object.entries(V03_METAS).map(([name, meta]) => [`v03_${name}`, buildProvenance(provenanceInput({ meta }))])),
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
      unrecordedKeys: ["dirty", "enginePath", "searchMode", "nodes", "threads", "mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"],
    });
    expect(PROVENANCE_VARIANTS.metaDirty!.record.meta?.dirty).toBe("dirty");
    expect(PROVENANCE_VARIANTS.metaUnmeasured!.record.meta?.dirty).toBe("unmeasured");
    expect(FIXTURE_PROVENANCE.record.meta?.dirty).toBe("clean");
    expect(PROVENANCE_VARIANTS.evaluatorAbsent!.evaluator).toEqual({ declared: null });
    expect(PROVENANCE_VARIANTS.analysisDirty!.analysis.dirty).toBe("dirty");
    expect(PROVENANCE_VARIANTS.analysisUnmeasured!.analysis).toMatchObject({ gitHead: null, dirty: "unmeasured" });
    expect(PROVENANCE_VARIANTS.recordOutsideRepo!.record.path).toBe("game.jsonl");
    expect(PROVENANCE_VARIANTS.metaMovetime!.record.meta).toMatchObject({ searchMode: "movetime", nodes: 0, threads: 1, unrecordedKeys: ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked", "trailingMoveTruncated", "truncatedTrailingMove"] });
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
        // STEP JSON V0.3-META: そろえの組・打ち切りの組と、その 7 変種(計画 2.3)
        const sideTag = !Object.hasOwn(meta, "mirrored") ? "absent" : meta.mirrored === false ? "notMirrored" : meta.sideAlignmentChecked === true ? "mirroredChecked" : "mirroredUnchecked";
        const truncationTag = !Object.hasOwn(meta, "trailingMoveTruncated") ? "absent" : meta.trailingMoveTruncated === true ? "truncated" : "notTruncated";
        seen.add(`provenance.meta.side.${sideTag}`);
        seen.add(`provenance.meta.truncation.${truncationTag}`);
        seen.add(`provenance.meta.variant.${sideTag.startsWith("mirrored") ? "mirrored" : sideTag}_${truncationTag}`);
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
      ...["absent", "notMirrored", "mirroredChecked", "mirroredUnchecked"].map((tag) => `provenance.meta.side.${tag}`),
      ...["absent", "notTruncated", "truncated"].map((tag) => `provenance.meta.truncation.${tag}`),
      ...["absent_absent", "absent_notTruncated", "absent_truncated", "notMirrored_notTruncated", "notMirrored_truncated", "mirrored_notTruncated", "mirrored_truncated"].map(
        (tag) => `provenance.meta.variant.${tag}`,
      ),
      "provenance.evaluator.null",
      "provenance.evaluator.string",
      "provenance.analysis.gitHead.null",
      "provenance.analysis.gitHead.string",
      ...["dirty", "clean", "unmeasured"].map((s) => `provenance.analysis.dirty.${s}`),
    ];
    expect([...expected].filter((tag) => !seen.has(tag))).toEqual([]);
    // V0.3-META: 7 変種の外の形(K-7 で置かない組など)が固定例から出ていない
    expect([...seen].filter((tag) => tag.startsWith("provenance.meta.variant.") && !expected.includes(tag))).toEqual([]);
  });
});

describe("T-4: コミット済みの記録 records/d0-nnue・records/d3-nnue・records/real-01 の Failure Event が、すべて今の版のスキーマを通る", () => {
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

  it("P-5: コミット済みの記録の meta は v0.2 の 6 欄に欠けなし(unrecordedKeys に 6 欄の名前が無い)で、エンジンのパスは根からの相対になる", () => {
    for (const record of COMMITTED) {
      const meta = provenanceMetaOf(record.meta, REPO_ROOT);
      expect(meta?.unrecordedKeys.filter((key) => (PROVENANCE_META_KEYS as readonly string[]).includes(key)), record.name).toEqual([]);
      expect(meta?.enginePath, record.name).toMatch(/^apps\/server\/engine\//);
    }
  });

  it("P-7(V0.3-META の P-6・P-7): 0.3 の行は v0.3 を通り v0.2・v0.1 では落ちる。0.3 で足した 7 欄と名前を外して版を 0.2 にした行は v0.2 を通り、さらに 0.2 で足した欄を外して版を 0.1 にした行は v0.1 を通る", () => {
    const lines = [...T2_EVENTS.flatMap(([, events]) => events).map((event) => lineOf(event)), ...RECORD_LINES, ...Object.values(PROVENANCE_LINES)];
    for (const line of lines) {
      const label = `${String(line.kifuId)}#${String(line.branchPly)}`;
      expect(validate(line, schema), label).toEqual([]);
      expect(validate(line, schemaV02), label).not.toEqual([]);
      expect(validate(line, schemaV01), label).not.toEqual([]);
      const v02 = clone(line);
      v02.schemaVersion = "0.2";
      const meta = ((v02.provenance as Json).record as Json).meta as Json | null;
      if (meta !== null) {
        for (const key of V03_KEYS) delete meta[key];
        meta.unrecordedKeys = (meta.unrecordedKeys as string[]).filter((key) => !V03_KEYS.includes(key));
      }
      expect(validate(v02, schemaV02), label).toEqual([]);
      const old = clone(v02);
      old.schemaVersion = "0.1";
      delete old.provenance;
      delete (old.branch as Json).evaluationAfter;
      delete (old.trigger as Json).kingSurroundings;
      expect(validate(old, schemaV01), label).toEqual([]);
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

// ---- STEP JSON V0.3-META(docs/STEP_JSON-V0.3-META_PLAN_2026-09-15.md 5.・6.2)----
describe("STEP JSON V0.3-META の約束(記録の meta の 7 欄)", () => {
  const V02_KEYS = ["gitHead", "dirty", "enginePath", "searchMode", "nodes", "threads"];
  const SIDE_NAMES = ["mirrored", "originalUserSide", "plyOffset", "startSfen", "sideAlignmentChecked"];
  const TRUNCATION_NAMES = ["trailingMoveTruncated", "truncatedTrailingMove"];
  // 門の分類は lib から import せず、ここで書く(計画 6.2。同じ分類を lib と共有すると、分類の誤りが両側で揃って沈黙する ― f2 の事前読み S-1)
  const GATE_OF: Record<string, string | null> = {
    mirrored: null,
    originalUserSide: "mirrored",
    plyOffset: "mirrored",
    startSfen: "mirrored",
    sideAlignmentChecked: null,
    trailingMoveTruncated: null,
    truncatedTrailingMove: "trailingMoveTruncated",
  };
  const pickSeven = (meta: object): Record<string, unknown> =>
    Object.fromEntries(V03_KEYS.filter((key) => Object.hasOwn(meta, key)).map((key) => [key, (meta as Record<string, unknown>)[key]]));

  /** P-5: 元の meta を基準に、7 欄ごとに 3 つの ⇔ を見る。v0.2 の 6 欄は「名前が並ぶ ⇔ meta に無い」 */
  const expectCorrespondence = (source: MetaLine | undefined, label: string): void => {
    const copied = provenanceMetaOf(source, REPO_ROOT);
    if (source === undefined) {
      expect(copied, label).toBeNull();
      return;
    }
    if (copied === null) throw new Error(`${label}: meta があるのに null になった`);
    const raw = source as unknown as Record<string, unknown>;
    const out = copied as unknown as Record<string, unknown>;
    for (const key of V03_KEYS) {
      const inMeta = Object.hasOwn(raw, key);
      const gate = GATE_OF[key] ?? null;
      const gateFalse = gate !== null && raw[gate] === false;
      expect(Object.hasOwn(out, key), `${label}: ${key} のキー`).toBe(inMeta);
      expect(copied.unrecordedKeys.includes(key), `${label}: ${key} の名前`).toBe(!inMeta && !gateFalse);
      if (inMeta) expect(out[key], `${label}: ${key} の値`).toBe(raw[key]);
    }
    for (const key of V02_KEYS) expect(copied.unrecordedKeys.includes(key), `${label}: ${key} の名前`).toBe(!Object.hasOwn(raw, key));
  };

  it("7 変種の固定例: meta の 7 欄を本番の関数(alignMovesToSente・sideMetaFields・planReplayMoves・truncationMetaFields)で作ると、手で書いた値と unrecordedKeys のとおりに写る", () => {
    expect(Object.keys(V03_METAS).sort()).toEqual(Object.keys(V03_EXPECTED).sort());
    for (const [name, meta] of Object.entries(V03_METAS)) {
      const copied = provenanceMetaOf(meta, REPO_ROOT);
      if (copied === null) throw new Error(`${name}: null`);
      expect(pickSeven(copied), name).toEqual(V03_EXPECTED[name]!.fields);
      expect(copied.unrecordedKeys, name).toEqual(V03_EXPECTED[name]!.unrecordedKeys);
    }
  });

  it("P-5: 元の meta を基準に、キーがある ⇔ meta にある / 名前が並ぶ ⇔ meta に無く門が false でない / 変種に無い ⇔ meta に無く門が false。v0.2 の 6 欄の名前 ⇔ meta に無い(固定例とコミット済みの記録すべて)", () => {
    const fixtures: Array<[string, MetaLine | undefined]> = [
      ...Object.entries(V03_METAS),
      ["meta 行なし", undefined],
      ["古い記録", { kind: "meta", kifuId: "old", startedAt: "t", gitHead: null } as unknown as MetaLine],
      ["時間で打ち切る探索", { ...FIXTURE_META, searchMode: "movetime", nodes: 0 } as MetaLine],
    ];
    for (const [name, meta] of fixtures) expectCorrespondence(meta, name);
    expect(COMMITTED.length).toBeGreaterThan(0);
    for (const record of COMMITTED) expectCorrespondence(record.meta, `${record.dir}/${record.name}`);
  });

  it("P-2・P-3: d0-nnue・d3-nnue の meta は 7 つの名前をすべて並べ、real-01 の kifu-02 は打ち切りの組だけを写してそろえの組の 5 つの名前を並べる", () => {
    const old = COMMITTED.filter((record) => record.dir === "d0-nnue" || record.dir === "d3-nnue");
    expect(old.length).toBeGreaterThan(0);
    for (const record of old) {
      const copied = provenanceMetaOf(record.meta, REPO_ROOT);
      expect(pickSeven(copied ?? {}), record.name).toEqual({});
      expect(copied?.unrecordedKeys, record.name).toEqual([...SIDE_NAMES, ...TRUNCATION_NAMES]);
    }
    const kifu02 = COMMITTED.find((record) => record.dir === "real-01" && record.name === "kifu-02.jsonl");
    if (kifu02 === undefined) throw new Error("real-01/kifu-02.jsonl が無い");
    const copied = provenanceMetaOf(kifu02.meta, REPO_ROOT);
    expect(pickSeven(copied ?? {})).toEqual({ trailingMoveTruncated: true, truncatedTrailingMove: "8c8b+" });
    expect(copied?.unrecordedKeys).toEqual(SIDE_NAMES);
  });

  it("K-3: どの変種にも合わない meta(値の形を含む)は写さず、記録の kifuId と食い違った欄の名前つきで InvalidProvenanceMetaError を投げる", () => {
    const MIRRORED = V03_METAS.mirrored_truncated as unknown as Record<string, unknown>;
    const NOT_MIRRORED = V03_METAS.notMirrored_notTruncated as unknown as Record<string, unknown>;
    const ABSENT = FIXTURE_META as unknown as Record<string, unknown>;
    const without = (meta: Record<string, unknown>, ...keys: string[]): Record<string, unknown> => {
      const copy = { ...meta };
      for (const key of keys) delete copy[key];
      return copy;
    };
    const cases: Array<[string, Record<string, unknown>, string]> = [
      ["mirrored が boolean でない", { ...MIRRORED, mirrored: "true" }, "mirrored"],
      ["回した局に plyOffset が無い", without(MIRRORED, "plyOffset"), "plyOffset"],
      ["plyOffset が 2", { ...MIRRORED, plyOffset: 2 }, "plyOffset"],
      ["originalUserSide が sente", { ...MIRRORED, originalUserSide: "sente" }, "originalUserSide"],
      ["startSfen が空", { ...MIRRORED, startSfen: "" }, "startSfen"],
      ["startSfen が 4 つの部分でない", { ...MIRRORED, startSfen: "lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b -" }, "startSfen"],
      ["sideAlignmentChecked が boolean でない", { ...MIRRORED, sideAlignmentChecked: "false" }, "sideAlignmentChecked"],
      ["回していない局に startSfen", { ...NOT_MIRRORED, startSfen: FOLD_START }, "startSfen"],
      ["回していない局の sideAlignmentChecked が true", { ...NOT_MIRRORED, sideAlignmentChecked: true }, "sideAlignmentChecked"],
      ["mirrored だけで sideAlignmentChecked が無い", without(NOT_MIRRORED, "sideAlignmentChecked"), "sideAlignmentChecked"],
      ["sideAlignmentChecked だけで mirrored が無い", without(NOT_MIRRORED, "mirrored"), "mirrored"],
      ["mirrored が無いのに従う欄がある", { ...ABSENT, startSfen: FOLD_START }, "startSfen"],
      ["K-7: 回していない局に打ち切りの組が無い", without(NOT_MIRRORED, "trailingMoveTruncated"), "trailingMoveTruncated"],
      ["K-7: 回した局に打ち切りの組が無い", without(MIRRORED, "trailingMoveTruncated", "truncatedTrailingMove"), "trailingMoveTruncated"],
      ["trailingMoveTruncated が boolean でない", { ...ABSENT, trailingMoveTruncated: "true" }, "trailingMoveTruncated"],
      ["落としたのに truncatedTrailingMove が無い", without(MIRRORED, "truncatedTrailingMove"), "truncatedTrailingMove"],
      ["truncatedTrailingMove が USI でない", { ...MIRRORED, truncatedTrailingMove: "8c8" }, "truncatedTrailingMove"],
      ["truncatedTrailingMove が文字列でない", { ...MIRRORED, truncatedTrailingMove: 7 }, "truncatedTrailingMove"],
      ["落としていないのに truncatedTrailingMove", { ...NOT_MIRRORED, truncatedTrailingMove: "2g2f" }, "truncatedTrailingMove"],
      ["trailingMoveTruncated が無いのに truncatedTrailingMove", { ...ABSENT, truncatedTrailingMove: "2g2f" }, "truncatedTrailingMove"],
    ];
    for (const [name, meta, key] of cases) {
      let caught: unknown;
      try {
        provenanceMetaOf(meta as unknown as MetaLine, REPO_ROOT);
      } catch (error) {
        caught = error;
      }
      expect(caught, `${name}: 止まらなかった`).toBeInstanceOf(InvalidProvenanceMetaError);
      expect((caught as Error).message, name).toContain(`記録 ${String(meta.kifuId)} の meta が`);
      expect((caught as Error).message, name).toContain(`欄 ${key}:`);
    }
    // 形の合う値は止めない(打つ手・成る手)
    for (const move of ["P*5e", "8c8b+"]) expect(() => provenanceMetaOf({ ...MIRRORED, truncatedTrailingMove: move } as unknown as MetaLine, REPO_ROOT), move).not.toThrow();
  });

  it("K-5・K-7: スキーマ v0.3 の meta は null と 7 変種で、startSfen・truncatedTrailingMove の pattern は lib の定数と同じ文字列", () => {
    const recordProperties = (((schema.properties as Json).provenance as Json).properties as Json).record as Json;
    const oneOf = ((recordProperties.properties as Json).meta as Json).oneOf as Json[];
    expect(oneOf.filter((branch) => branch.type === "null")).toHaveLength(1);
    const objects = oneOf.filter((branch) => branch.type === "object");
    expect(objects).toHaveLength(7);
    const patternsOf = (key: string): string[] => [
      ...new Set(
        objects.flatMap((branch) => {
          const property = (branch.properties as Record<string, Json | undefined>)[key];
          return property === undefined ? [] : [String(property.pattern)];
        }),
      ),
    ];
    expect(patternsOf("startSfen")).toEqual([START_SFEN_PATTERN]);
    expect(patternsOf("truncatedTrailingMove")).toEqual([USI_MOVE_PATTERN]);
  });

  it("スキーマの境目(手で書き換えた 1 行): 変種に無い欄・欠けた欄・値の形・K-7 の組・null は落ち、打つ手・成る手は通る", () => {
    const broken = (name: string, change: (meta: Json) => void): Json => {
      const line = clone(PROVENANCE_LINES[`v03_${name}`]!);
      change(((line.provenance as Json).record as Json).meta as Json);
      return line;
    };
    const failing: Array<[string, Json]> = [
      ["回していない局に startSfen", broken("notMirrored_notTruncated", (m) => (m.startSfen = FOLD_START))],
      ["回した局に plyOffset が無い", broken("mirrored_truncated", (m) => delete m.plyOffset)],
      ["plyOffset が 2", broken("mirrored_truncated", (m) => (m.plyOffset = 2))],
      ["originalUserSide が sente", broken("mirrored_truncated", (m) => (m.originalUserSide = "sente"))],
      ["回していない局の sideAlignmentChecked が true", broken("notMirrored_notTruncated", (m) => (m.sideAlignmentChecked = true))],
      ["mirrored が無いのに sideAlignmentChecked", broken("absent_absent", (m) => (m.sideAlignmentChecked = false))],
      ["落としていないのに truncatedTrailingMove", broken("notMirrored_notTruncated", (m) => (m.truncatedTrailingMove = "2g2f"))],
      ["truncatedTrailingMove が USI でない", broken("mirrored_truncated", (m) => (m.truncatedTrailingMove = "8c8"))],
      ["startSfen が空", broken("mirrored_truncated", (m) => (m.startSfen = ""))],
      ["startSfen が 3 つの部分", broken("mirrored_truncated", (m) => (m.startSfen = "a b c"))],
      ["K-7: 回していない局に打ち切りの組が無い", broken("notMirrored_notTruncated", (m) => delete m.trailingMoveTruncated)],
      ["K-7: 回した局に打ち切りの組が無い", broken("mirrored_truncated", (m) => {
        delete m.trailingMoveTruncated;
        delete m.truncatedTrailingMove;
      })],
      ...V03_KEYS.map((key): [string, Json] => [`${key} が null`, broken("mirrored_truncated", (m) => (m[key] = null))]),
    ];
    for (const [name, line] of failing) expect(validate(line, schema), name).not.toEqual([]);
    for (const move of ["P*5e", "8c8b+"]) expect(validate(broken("mirrored_truncated", (m) => (m.truncatedTrailingMove = move)), schema), move).toEqual([]);
  });
});
