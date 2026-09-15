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
// 【STEP D2 の v0.4】counterfactual(docs/STEP_D2_PLAN_2026-09-15.md 2.2〜2.4): 状態 8 つと compared の中の変種を lib(counterfactualOf)で作って 1 行に差し込み、
// 手で書いた noKing の 1 行と合わせて変種の一覧に入れる。v0.4 = v0.3 + counterfactual・0.4 → 0.3 → 0.2 → 0.1 の鎖・境目・T-5 を見る。
// 【STEP D2.5 の v0.5】trigger.positionFacts・branch.standingPair・counterfactual の positionFactsEnd と差・規則の standing と positionFacts(docs/STEP_D2.5_PLAN_2026-09-15.md §2・§3):
// 玉が盤上に無い側の 3 変種は手で書き換えた 1 行、形勢の状態は lib の固定例と手で書き換えた 1 行で埋める。v0.5 = v0.4 + 6 欄・0.5 → 0.4 の鎖・境目・T-5 の数を見る
// (値の期待は lib/positionFacts.test.ts・lib/standing.test.ts)。

import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { counterfactualOf, POSITION_FACTS_RULES, type Counterfactual } from "./counterfactual.js";
import { validate } from "./eventSchema.js";
import { diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, readEvaluations, STANDING_BOUNDS, type DiagnosisRule, type FailureEvent } from "./failureEvent.js";
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
const schemaV03 = loadFailureEventSchema("0.3");
const schemaV04 = loadFailureEventSchema("0.4");
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
  standingBounds: STANDING_BOUNDS,
  positionFactsRules: POSITION_FACTS_RULES,
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
const focusBaselineOf = (sfen: string, pv: string[], extra: Json = {}): Json => ({
  source: "focus_baseline",
  sfen,
  moveUsi: null,
  multipv: 1,
  scoreCp: 0,
  mate: null,
  pv,
  lowerbound: false,
  upperbound: false,
  ...extra,
});
// STEP D2: F-1 と同じ急落に、直前の行(ply 48)の focus_baseline の読み筋(実戦と同じ 6 手)を植えた記録。分岐点 49 の counterfactual が compared になる
const F11 = (() => {
  const records = plantedRecords(GAME01_MOVES, { 48: engineRef(500, { afterPassMate: 3, dropCp: 350, bestmove: "2h2g" }), 50: engineRef(-300) });
  const row = records.find((record) => record.ply === 48)!;
  row.searchPvs = [focusBaselineOf(row.sfen, GAME01_MOVES.slice(48, 54))] as unknown as RecordLine["searchPvs"];
  return records;
})();
const T2_EVENTS: Array<[string, FailureEvent[]]> = [
  ["F-1", eventsOf("F-1", F1)],
  ["F-2", eventsOf("F-2", plantedRecords(GAME01_MOVES, { 20: engineRef(100), 22: engineRef(-500) }))],
  ["F-3", eventsOf("F-3", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(-300) }))],
  ["F-4", eventsOf("F-4", plantedRecords(GAME01_MOVES.slice(0, 30), { 26: engineRef(500), 28: engineRef(-300) }))],
  ["F-6i", eventsOf("F-6i", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(null, { mate: -3 }) }))],
  ["F-6ii", eventsOf("F-6ii", plantedRecords(GAME01_MOVES, { 20: engineRef(500), 22: engineRef(350, { afterPassMate: 5 }) }))],
  ["mateAfterOnly", eventsOf("m1", plantedRecords(GAME01_MOVES.slice(0, 4), { 0: "absent", 2: engineRef(500), 4: engineRef(null, { mate: -3 }) }))],
  ["F-11(D2)", eventsOf("F-11", F11)],
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

/** STEP D2.5: 玉の区域の数の、玉が盤上に無い側を null にする(positionFacts は 3 欄、差は 2 欄のどちらにも使う) */
const withoutKing = (facts: Json, sides: string[]): void => {
  for (const key of Object.keys(facts)) for (const side of sides) (facts[key] as Json)[side] = null;
};

/** lib から出ない変種(手で書き換えた 1 行) */
const HAND_MADE: Record<string, Json> = (() => {
  const base = lineOf(at(T2_EVENTS[0]![1], 49));
  const withChange = (change: (line: Json) => void): Json => {
    const line = clone(base);
    change(line);
    return line;
  };
  const lines: Record<string, Json> = {
    beforeGameEnd: withChange((line) => {
      (line.trigger as Json).evaluationBefore = { state: "notMeasuredGameEnd" };
      ((line.branch as Json).standingPair as Json).before = { undetermined: "notMeasuredGameEnd" };
    }),
    playedMoveNull: withChange((line) => ((line.action as Json).playedMove = null)),
    kingSurroundingsNull: withChange((line) => ((line.trigger as Json).kingSurroundings = null)),
    // STEP D2.5: 玉が盤上に無い側(lib の固定例は両方の玉がある局面だけ)
    positionFactsOwnKingMissing: withChange((line) => withoutKing((line.trigger as Json).positionFacts as Json, ["ownKingZone"])),
    positionFactsOpponentKingMissing: withChange((line) => withoutKing((line.trigger as Json).positionFacts as Json, ["opponentKingZone"])),
    positionFactsNoKings: withChange((line) => withoutKing((line.trigger as Json).positionFacts as Json, ["ownKingZone", "opponentKingZone"])),
  };
  for (const state of ["notMeasuredGameEnd", "notMeasuredInCheck", "notMeasurable", "unrecorded", "notEvaluation"]) {
    lines[`after_${state}`] = withChange((line) => {
      (line.branch as Json).evaluationAfter = { state };
      ((line.branch as Json).standingPair as Json).after = { undetermined: state };
    });
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

// ---- STEP D2 の counterfactual の変種(docs/STEP_D2_PLAN_2026-09-15.md 2.2〜2.4)。値は lib(counterfactualOf)で作り、F-1 の分岐点 49 の 1 行に差し込む ----
// 盤は lib/counterfactual.test.ts の固定例と同じ(値の期待はそちらで見る。ここではスキーマの変種を埋めることだけを見る)
const CF_F1_ACTUAL = ["7g7f", "3c3d", "8h2b+", "3a2b", "B*4e"];
const CF_F1_PV = ["7g7f", "3c3d", "2g2f", "4a3b", "2f2e"];
const CF_F2_ACTUAL = ["7g7f", "3c3d", "8h3c+", "4a4b", "3c4b"];
const CF_MATE_ROOT = "4k4/9/4P4/9/9/9/9/9/4K4 b G 1";
const CF_STALEMATE_ROOT = "k8/2G6/9/1G7/9/9/9/9/4K4 b - 1";
const CF_GOTE_MATE_ROOT = "4k4/9/9/9/9/9/4p3P/9/4K4 b g 1";
const CF_GOLD_ROOT = "4k4/9/9/9/9/9/9/4G4/4K4 b - 1";
const CF_OTHER_ROOT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";
const cfOf = (
  root: string,
  actual: string[],
  searchPvs: Json[] | null | undefined,
  options: { bestmoveAtBefore?: string | null; recordSfen?: string } = {},
): Counterfactual => {
  const record = { sfen: options.recordSfen ?? root } as Pick<RecordLine, "sfen" | "searchPvs">;
  if (searchPvs !== undefined) record.searchPvs = searchPvs as unknown as RecordLine["searchPvs"];
  return counterfactualOf({ record, moves: actual, branchPly: 1, windowPlies: DRAFT_RULE_1.windowPlies, initialSfen: root, bestmoveAtBefore: options.bestmoveAtBefore ?? null });
};
const CF_VARIANTS: Record<string, Counterfactual> = {
  actualRootMismatch: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, undefined, { recordSfen: CF_GOLD_ROOT }),
  unrecorded: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, undefined),
  notMeasurable: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, null),
  noFocusBaseline: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, CF_F1_PV, { source: "focus_after_pass" })]),
  emptyPv: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, [])]),
  rootMismatch: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(CF_OTHER_ROOT, CF_F1_PV)]),
  pvUnplayable: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, ["7f7e"])]),
  capturedUpperbound: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, CF_F1_PV, { upperbound: true })], { bestmoveAtBefore: "7g7f" }),
  checksLowerbound: cfOf(DEFAULT_INITIAL_SFEN, CF_F2_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, CF_F1_PV, { lowerbound: true })]),
  pvTruncated: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_ACTUAL, [focusBaselineOf(DEFAULT_INITIAL_SFEN, ["7g7f", "3c3d", "7f7e", "7f7e"])]),
  mateBySente: cfOf(CF_MATE_ROOT, ["5i4h", "5a4a"], [focusBaselineOf(CF_MATE_ROOT, ["G*5b"])]),
  mateByGote: cfOf(CF_GOTE_MATE_ROOT, ["1g1f", "G*5h"], [focusBaselineOf(CF_GOTE_MATE_ROOT, ["5i4i", "G*5h"])]),
  gameEndNotMate: cfOf(CF_STALEMATE_ROOT, ["5i4h"], [focusBaselineOf(CF_STALEMATE_ROOT, ["8d8c"])]),
  surroundingsDiff: cfOf(CF_GOLD_ROOT, ["5h4g"], [focusBaselineOf(CF_GOLD_ROOT, ["5h4h"])]),
  // STEP D2.5: 読み筋 = 実戦(区域の数の差がすべて 0 の変種)
  samePv: cfOf(DEFAULT_INITIAL_SFEN, CF_F1_PV, [focusBaselineOf(DEFAULT_INITIAL_SFEN, CF_F1_PV)], { bestmoveAtBefore: "7g7f" }),
};
/** F-1 の分岐点 49 の 1 行の counterfactual を差し替える(キーの位置は consequences の後のまま) */
const withCounterfactual = (counterfactual: unknown): Json => {
  const line = lineOf(at(T2_EVENTS[0]![1], 49));
  line.counterfactual = clone(counterfactual);
  return line;
};
const CF_LINES: Record<string, Json> = Object.fromEntries(Object.entries(CF_VARIANTS).map(([name, counterfactual]) => [name, withCounterfactual(counterfactual)]));
/** lib から出ない counterfactual の変種(先手玉が盤上に無い: 周りは null、逃げ道は noKing、差と根からの変化は null。手で書き換えた 1 行) */
const CF_HAND_MADE: Record<string, Json> = (() => {
  const noKing = clone(CF_VARIANTS.surroundingsDiff!) as unknown as Json;
  noKing.kingEscapesRoot = { state: "noKing" };
  for (const key of ["actual", "pv"]) Object.assign(noKing[key] as Json, { kingSurroundingsEnd: null, kingEscapesEnd: { state: "noKing" } });
  Object.assign(noKing.pvMinusActual as Json, { kingSurroundingsOwn: null, kingEscapes: null });
  noKing.kingEscapesChangeFromRoot = { actual: null, pv: null };
  for (const key of ["actual", "pv"]) withoutKing((noKing[key] as Json).positionFactsEnd as Json, ["ownKingZone"]);
  withoutKing((noKing.pvMinusActual as Json).positionFacts as Json, ["ownKingZone"]);
  // STEP D2.5: 後手玉が盤上に無い・どちらの玉も無い(区域の数だけを書き換える)
  const withoutKings = (base: Json, sides: string[]): Json => {
    const counterfactual = clone(base);
    for (const key of ["actual", "pv"]) withoutKing((counterfactual[key] as Json).positionFactsEnd as Json, sides);
    withoutKing((counterfactual.pvMinusActual as Json).positionFacts as Json, sides);
    return withCounterfactual(counterfactual);
  };
  return {
    noKing: withCounterfactual(noKing),
    positionFactsOpponentKingMissing: withoutKings(clone(CF_VARIANTS.surroundingsDiff!) as unknown as Json, ["opponentKingZone"]),
    positionFactsNoKings: withoutKings(noKing, ["ownKingZone", "opponentKingZone"]),
  };
})();

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
      .concat(RECORD_LINES, Object.values(HAND_MADE), Object.values(PROVENANCE_LINES), Object.values(CF_LINES), Object.values(CF_HAND_MADE));
    const seen = new Set<string>();
    const sign = (value: number | null): string => (value === null ? "null" : value > 0 ? "pos" : "neg");
    const nullOr = (value: unknown, kind: string): string => (value === null ? "null" : kind);
    const standingTag = (standing: unknown): string => (typeof standing === "string" ? standing : `undetermined.${(standing as { undetermined: string }).undetermined}`);
    const kingsTag = (sides: { ownKingZone: unknown; opponentKingZone: unknown }): string =>
      sides.ownKingZone === null ? (sides.opponentKingZone === null ? "noKings" : "ownKingMissing") : sides.opponentKingZone === null ? "opponentKingMissing" : "both";
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
      // STEP D2.5 の v0.5: 形勢の状態と、玉の区域の数の変種(玉が無い側)
      seen.add(`standingPair.before.${standingTag(event.branch.standingPair.before)}`);
      seen.add(`standingPair.after.${standingTag(event.branch.standingPair.after)}`);
      seen.add(`positionFacts.trigger.${kingsTag(event.trigger.positionFacts.zonePieces)}`);
      // STEP D2 の v0.4: counterfactual の状態と、compared の中の変種(計画 2.2〜2.4)
      const counterfactual = event.counterfactual;
      seen.add(`counterfactual.state.${counterfactual.state}`);
      if (counterfactual.state === "compared") {
        const someOrEmpty = (value: readonly number[] | object): string => ((Array.isArray(value) ? value.length : Object.keys(value).length) > 0 ? "some" : "empty");
        const zeroOr = (value: number | null): string => (value === null ? "null" : value === 0 ? "zero" : "nonzero");
        seen.add(`counterfactual.pvTruncatedAtPly.${nullOr(counterfactual.pvTruncatedAtPly, "number")}`);
        seen.add(`counterfactual.pvBounded.lowerbound.${counterfactual.pvBounded.lowerbound}`);
        seen.add(`counterfactual.pvBounded.upperbound.${counterfactual.pvBounded.upperbound}`);
        seen.add(`counterfactual.pvFirstMoveIsBestmoveAtBefore.${counterfactual.pvFirstMoveIsBestmoveAtBefore}`);
        seen.add(`counterfactual.pvFirstMoveIsPlayedMove.${counterfactual.pvFirstMoveIsPlayedMove}`);
        seen.add(`counterfactual.kingEscapesRoot.${counterfactual.kingEscapesRoot.state}`);
        for (const facts of [counterfactual.actual, counterfactual.pv]) {
          seen.add(`counterfactual.facts.capturedRoles.${someOrEmpty({ ...facts.capturedRoles.us, ...facts.capturedRoles.opponent })}`);
          seen.add(`counterfactual.facts.checks.byUs.${someOrEmpty(facts.checks.byUs)}`);
          seen.add(`counterfactual.facts.checks.byOpponent.${someOrEmpty(facts.checks.byOpponent)}`);
          seen.add(`counterfactual.facts.mate.${facts.mate === null ? "null" : facts.mate.winner}`);
          seen.add(`counterfactual.facts.gameEnd.${nullOr(facts.gameEnd, "object")}`);
          seen.add(`counterfactual.facts.kingSurroundingsEnd.${nullOr(facts.kingSurroundingsEnd, "object")}`);
          seen.add(`counterfactual.facts.kingEscapesEnd.${facts.kingEscapesEnd.state}`);
          seen.add(`counterfactual.facts.positionFactsEnd.${kingsTag(facts.positionFactsEnd.zonePieces)}`);
        }
        const diff = counterfactual.pvMinusActual;
        seen.add(`counterfactual.diff.capturedRoles.${someOrEmpty({ ...diff.capturedRoles.us, ...diff.capturedRoles.opponent })}`);
        seen.add(`counterfactual.diff.kingSurroundingsOwn.${zeroOr(diff.kingSurroundingsOwn)}`);
        seen.add(`counterfactual.diff.kingEscapes.${zeroOr(diff.kingEscapes)}`);
        seen.add(`counterfactual.diff.positionFacts.${kingsTag(diff.positionFacts.zonePieces)}`);
        const diffValues = [diff.positionFacts.zonePieces.ownKingZone, diff.positionFacts.zonePieces.opponentKingZone, diff.positionFacts.zoneControl.ownKingZone, diff.positionFacts.zoneControl.opponentKingZone]
          .flatMap((counts) => (counts === null ? [] : [counts.bySente, counts.byGote]));
        seen.add(`counterfactual.diff.positionFacts.values.${diffValues.every((value) => value === 0) ? "zero" : "nonzero"}`);
        for (const change of [counterfactual.kingEscapesChangeFromRoot.actual, counterfactual.kingEscapesChangeFromRoot.pv]) {
          seen.add(`counterfactual.changeFromRoot.${nullOr(change, "number")}`);
        }
      }
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
      // STEP D2 の v0.4
      ...["compared", "actualRootMismatch", "unrecorded", "notMeasurable", "noFocusBaseline", "emptyPv", "rootMismatch", "pvUnplayable"].map((s) => `counterfactual.state.${s}`),
      "counterfactual.pvTruncatedAtPly.null",
      "counterfactual.pvTruncatedAtPly.number",
      ...["lowerbound", "upperbound"].flatMap((key) => [`counterfactual.pvBounded.${key}.true`, `counterfactual.pvBounded.${key}.false`]),
      ...["pvFirstMoveIsBestmoveAtBefore", "pvFirstMoveIsPlayedMove"].flatMap((key) => [`counterfactual.${key}.true`, `counterfactual.${key}.false`]),
      "counterfactual.kingEscapesRoot.counted",
      "counterfactual.kingEscapesRoot.noKing",
      "counterfactual.facts.capturedRoles.some",
      "counterfactual.facts.capturedRoles.empty",
      ...["byUs", "byOpponent"].flatMap((key) => [`counterfactual.facts.checks.${key}.some`, `counterfactual.facts.checks.${key}.empty`]),
      ...["null", "sente", "gote"].map((s) => `counterfactual.facts.mate.${s}`),
      "counterfactual.facts.gameEnd.null",
      "counterfactual.facts.gameEnd.object",
      "counterfactual.facts.kingSurroundingsEnd.null",
      "counterfactual.facts.kingSurroundingsEnd.object",
      ...["counted", "noKing", "opponentInCheck"].map((s) => `counterfactual.facts.kingEscapesEnd.${s}`),
      "counterfactual.diff.capturedRoles.some",
      "counterfactual.diff.capturedRoles.empty",
      ...["kingSurroundingsOwn", "kingEscapes"].flatMap((key) => ["null", "zero", "nonzero"].map((s) => `counterfactual.diff.${key}.${s}`)),
      "counterfactual.changeFromRoot.null",
      "counterfactual.changeFromRoot.number",
      // STEP D2.5 の v0.5
      ...["before", "after"].flatMap((side) =>
        ["ahead", "level", "behind", ...["notMeasuredGameEnd", "notMeasuredInCheck", "notMeasurable", "unrecorded", "notEvaluation"].map((s) => `undetermined.${s}`)].map((tag) => `standingPair.${side}.${tag}`),
      ),
      ...["both", "ownKingMissing", "opponentKingMissing", "noKings"].flatMap((tag) => [`positionFacts.trigger.${tag}`, `counterfactual.facts.positionFactsEnd.${tag}`, `counterfactual.diff.positionFacts.${tag}`]),
      "counterfactual.diff.positionFacts.values.zero",
      "counterfactual.diff.positionFacts.values.nonzero",
    ];
    expect([...expected].filter((tag) => !seen.has(tag))).toEqual([]);
    // V0.3-META: 7 変種の外の形(K-7 で置かない組など)が固定例から出ていない
    expect([...seen].filter((tag) => tag.startsWith("provenance.meta.variant.") && !expected.includes(tag))).toEqual([]);
    // STEP D2: 一覧に無い counterfactual の変種(根の逃げ道の opponentInCheck など、置かない形)が出ていない
    expect([...seen].filter((tag) => tag.startsWith("counterfactual.") && !expected.includes(tag))).toEqual([]);
    // STEP D2.5: 一覧に無い形勢の状態(mateZero など、行に出さない形)が出ていない
    expect([...seen].filter((tag) => (tag.startsWith("standingPair.") || tag.startsWith("positionFacts.")) && !expected.includes(tag))).toEqual([]);
  });
});

describe("T-4: コミット済みの記録 records/d0-nnue・records/d3-nnue・records/real-01 の Failure Event が、すべて今の版のスキーマを通る", () => {
  it("33 本(d0-nnue 7・d3-nnue 20・real-01 6)から作った Failure Event(件数は固定しない)", () => {
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
    // 元の 1 行が持つキーの数(数えた: 最上位 12(STEP D2 の counterfactual を含む)・counterfactual 1(unrecorded の state)・trigger 5・evaluationBefore 7・opponentIntent 2・classification 1・shape 3・
    // focus 1・kingSurroundings 2・action 2・branch 5・evaluationAfter 7・consequences 4・candidateModes[0] 3・
    // provenance 3・record 3・meta 7・evaluator 1・analysis 3・rule 5)。道筋の辿り損ねで、消す試しが減っていないことを見る
    // STEP D2.5 の v0.5 で +28(trigger の positionFacts 1 と中身 17・branch の standingPair 1 と before・after 2・rule の standing 1 と中身 2・positionFacts 1 と中身 3)
    expect(tried).toBe(105);
  });

  it("どの入れ物に知らない欄を足しても落ちる", () => {
    for (const path of objectPaths(base)) {
      const broken = clone(base);
      parentAt(broken, path).unexpectedField = 1;
      expect(validate(broken, schema), [...path, "unexpectedField"].join(".")).not.toEqual([]);
    }
  });

  it("STEP D2: compared の 1 行(取った駒の無い変種。0 の駒種はキーを出さないので、取った駒のある 1 行では消して通る欄ができる)でも、どの欄を 1 つ消しても・どの入れ物に知らない欄を足しても落ちる", () => {
    const compared = CF_LINES.surroundingsDiff!;
    expect(validate(compared, schema)).toEqual([]);
    expect((compared.counterfactual as Json).state).toBe("compared");
    let tried = 0;
    for (const path of objectPaths(compared)) {
      for (const key of Object.keys(parentAt(compared, path))) {
        const broken = clone(compared);
        delete parentAt(broken, path)[key];
        expect(validate(broken, schema), [...path, key].join(".")).not.toEqual([]);
        tried += 1;
      }
      const added = clone(compared);
      parentAt(added, path).unexpectedField = 1;
      expect(validate(added, schema), [...path, "unexpectedField"].join(".")).not.toEqual([]);
    }
    // 上の 1 行の 77 のうち counterfactual の state 1 を、compared の 55 に置き換えた数(数えた: compared 16・pvBounded 2・kingEscapesRoot 2・
    // actual 14・pv 14(それぞれ 6・capturedRoles 2・checks 2・kingSurroundingsEnd 2・kingEscapesEnd 2)・pvMinusActual 5(3・capturedRoles 2)・kingEscapesChangeFromRoot 2)
    // STEP D2.5 の v0.5 で +79(上の 28 と、actual・pv の positionFactsEnd 各 1 と中身 17・pvMinusActual の positionFacts 1 と中身 14)
    expect(tried).toBe(210);
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

  it("P-7(V0.3-META の P-6・P-7、STEP D2 の v0.4・STEP D2.5 の v0.5): 0.5 の行は v0.5 を通り v0.4・v0.3・v0.2・v0.1 では落ちる。D2.5 の欄を外して版を 0.4 にした行は v0.4 を通り、counterfactual を外して版を 0.3 にした行は v0.3 を通り、0.3 で足した 7 欄と名前を外して版を 0.2 にした行は v0.2 を通り、さらに 0.2 で足した欄を外して版を 0.1 にした行は v0.1 を通る", () => {
    const lines = [
      ...T2_EVENTS.flatMap(([, events]) => events).map((event) => lineOf(event)),
      ...RECORD_LINES,
      ...Object.values(PROVENANCE_LINES),
      ...Object.values(CF_LINES),
      ...Object.values(CF_HAND_MADE),
    ];
    for (const line of lines) {
      const label = `${String(line.kifuId)}#${String(line.branchPly)}`;
      expect(validate(line, schema), label).toEqual([]);
      expect(validate(line, schemaV04), label).not.toEqual([]);
      expect(validate(line, schemaV03), label).not.toEqual([]);
      expect(validate(line, schemaV02), label).not.toEqual([]);
      expect(validate(line, schemaV01), label).not.toEqual([]);
      const v04 = clone(line);
      v04.schemaVersion = "0.4";
      delete (v04.trigger as Json).positionFacts;
      delete (v04.branch as Json).standingPair;
      const counterfactual = v04.counterfactual as Json;
      if (counterfactual.state === "compared") {
        for (const key of ["actual", "pv"]) delete (counterfactual[key] as Json).positionFactsEnd;
        delete (counterfactual.pvMinusActual as Json).positionFacts;
      }
      const analysisRule = ((v04.provenance as Json).analysis as Json).rule as Json;
      delete analysisRule.standing;
      delete analysisRule.positionFacts;
      expect(validate(v04, schemaV04), label).toEqual([]);
      const v03 = clone(v04);
      v03.schemaVersion = "0.3";
      delete v03.counterfactual;
      expect(validate(v03, schemaV03), label).toEqual([]);
      const v02 = clone(v03);
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
    // STEP D2.5: 形勢の状態の境も渡した値を写す。区域の数え方は選べる値が 1 つずつなので、その値
    expect(buildProvenance(provenanceInput({ rule, notEvaluationCp: 31000, standingBounds: { aheadCp: 222, behindCp: -333 } })).analysis.rule).toEqual({
      ...rule,
      notEvaluationCp: 31000,
      standing: { aheadCp: 222, behindCp: -333 },
      positionFacts: { zone: "king_and_eight_neighbors", reach: "non_king_pieces", control: "squares" },
    });
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

  it("スキーマの境目(手で書き換えた 1 行): 変種に無い欄・欠けた欄(従う欄が 1 つだけ無い・3 つとも無い回した局を含む)・値の形・K-7 の組・null は落ち、打つ手・成る手は通る", () => {
    const broken = (name: string, change: (meta: Json) => void): Json => {
      const line = clone(PROVENANCE_LINES[`v03_${name}`]!);
      change(((line.provenance as Json).record as Json).meta as Json);
      return line;
    };
    const failing: Array<[string, Json]> = [
      ["回していない局に startSfen", broken("notMirrored_notTruncated", (m) => (m.startSfen = FOLD_START))],
      ["回した局に plyOffset が無い", broken("mirrored_truncated", (m) => delete m.plyOffset)],
      // V0.3-META の監査 A の任意 1(STEP D2 の後の小さな追加): 従う欄 3 つが全部無い回した局。1 つだけ欠けた行では、変種が
      // 「3 つとも有るか、3 つとも無いか」を許す形に崩れても鳴らない。落としていない局・落とした局の 2 つの変種の両方で見る。
      // sideAlignmentChecked は false にする(A の O-1): true のままだと、回していない変種の mirrored が boolean に崩れても、
      // その変種の sideAlignmentChecked の const false で落ちて鳴らない
      ...(["mirrored_notTruncated", "mirrored_truncated"] as const).map((name): [string, Json] => [
        `回した局(${name})に従う欄 3 つが全部無い(sideAlignmentChecked は false)`,
        broken(name, (m) => {
          delete m.originalUserSide;
          delete m.plyOffset;
          delete m.startSfen;
          m.sideAlignmentChecked = false;
        }),
      ]),
      // 司令塔の決定(上の 2 行の限界を足す)と A の O-2: 従う欄が 1 つだけ無い行を、2 つの変種 × 3 欄それぞれ。3 つとも無い行だけでは、
      // 変種が 1 欄だけを任意にする形に崩れても、残りの 2 欄で落ちるので鳴らない(落とした変種の plyOffset は上の既存の行と重なる)
      ...(["mirrored_notTruncated", "mirrored_truncated"] as const).flatMap((name) =>
        (["originalUserSide", "plyOffset", "startSfen"] as const).map((key): [string, Json] => [
          `回した局(${name})に ${key} だけが無い`,
          broken(name, (m) => delete m[key]),
        ]),
      ),
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

// ---- STEP D2 の v0.4(docs/STEP_D2_PLAN_2026-09-15.md 2.2〜2.4)----
describe("STEP D2 の v0.4(counterfactual)", () => {
  it("v0.4 のスキーマは、v0.3 に counterfactual を consequences の後に足しただけ(版の値・$id・title・description のほかは v0.3 と同じ)", () => {
    const v04 = clone(schemaV04) as unknown as Json;
    const v03 = schemaV03 as unknown as Json;
    const required = v04.required as string[];
    const properties = v04.properties as Json;
    expect(required.indexOf("counterfactual")).toBe(required.indexOf("consequences") + 1);
    expect(Object.keys(properties).indexOf("counterfactual")).toBe(Object.keys(properties).indexOf("consequences") + 1);
    expect(properties.schemaVersion).toEqual({ const: "0.4" });
    delete properties.counterfactual;
    v04.required = required.filter((key) => key !== "counterfactual");
    properties.schemaVersion = { const: "0.3" };
    for (const key of ["$id", "title", "description"]) v04[key] = v03[key];
    expect(v04).toEqual(v03);
  });

  it("lib で作った counterfactual の変種は、それぞれ期待した状態になり、差し込んだ 1 行と手で書いた noKing の 1 行はスキーマを通る。F-11 の Event は compared で通る", () => {
    expect(Object.fromEntries(Object.entries(CF_VARIANTS).map(([name, counterfactual]) => [name, counterfactual.state]))).toEqual({
      actualRootMismatch: "actualRootMismatch",
      unrecorded: "unrecorded",
      notMeasurable: "notMeasurable",
      noFocusBaseline: "noFocusBaseline",
      emptyPv: "emptyPv",
      rootMismatch: "rootMismatch",
      pvUnplayable: "pvUnplayable",
      capturedUpperbound: "compared",
      checksLowerbound: "compared",
      pvTruncated: "compared",
      mateBySente: "compared",
      mateByGote: "compared",
      gameEndNotMate: "compared",
      surroundingsDiff: "compared",
      samePv: "compared",
    });
    for (const [name, line] of Object.entries({ ...CF_LINES, ...CF_HAND_MADE })) expect(validate(line, schema), name).toEqual([]);
    const f11 = at(T2_EVENTS.find(([name]) => name === "F-11(D2)")![1], 49);
    expect(f11.counterfactual.state).toBe("compared");
    expect(validate(lineOf(f11), schema)).toEqual([]);
  });

  it("counterfactual の境目(手で書き換えた 1 行): 差の 0・玉や成駒の駒種・0 枚・逃げ道 9・count の無い counted・知らない状態・compared でない状態の欄・勝った側の値・checkmate の終局・N 0・USI でない 1 手目・1 手目の打ち切り・小数・null は落ち、負の差・打つ手の 1 手目は通る", () => {
    const broken = (name: string, change: (counterfactual: Json) => void): Json => {
      const line = clone(CF_LINES[name]!);
      change(line.counterfactual as Json);
      return line;
    };
    const part = (counterfactual: Json, ...keys: string[]): Json => keys.reduce<Json>((node, key) => node[key] as Json, counterfactual);
    const failing: Array<[string, Json]> = [
      ["差の駒種が 0", broken("capturedUpperbound", (c) => (part(c, "pvMinusActual", "capturedRoles", "us").bishop = 0))],
      ["取った駒に玉", broken("capturedUpperbound", (c) => (part(c, "actual", "capturedRoles", "us").king = 1))],
      ["取った駒に成駒の名前", broken("capturedUpperbound", (c) => (part(c, "actual", "capturedRoles", "us").horse = 1))],
      ["取った駒が 0 枚", broken("capturedUpperbound", (c) => (part(c, "actual", "capturedRoles", "us").bishop = 0))],
      ["逃げ道 9", broken("surroundingsDiff", (c) => (c.kingEscapesRoot = { state: "counted", count: 9 }))],
      ["count の無い counted", broken("surroundingsDiff", (c) => (part(c, "actual").kingEscapesEnd = { state: "counted" }))],
      ["noKing に count", broken("surroundingsDiff", (c) => (part(c, "actual").kingEscapesEnd = { state: "noKing", count: 0 }))],
      ["知らない状態", broken("unrecorded", (c) => (c.state = "notRecorded"))],
      ["compared でない状態に comparedPlies", broken("unrecorded", (c) => (c.comparedPlies = 1))],
      ["compared なのに state だけ", withCounterfactual({ state: "compared" })],
      ["詰みの勝った側が null", broken("mateByGote", (c) => (part(c, "actual").mate = { ply: 2, winner: null }))],
      ["詰みでない終局に checkmate", broken("gameEndNotMate", (c) => (part(c, "pv").gameEnd = { ply: 1, result: "checkmate" }))],
      ["N が 0", broken("surroundingsDiff", (c) => (c.comparedPlies = 0))],
      ["1 手目が USI でない", broken("surroundingsDiff", (c) => (c.pvFirstMove = "5h4"))],
      ["打ち切りが 1 手目", broken("pvTruncated", (c) => (c.pvTruncatedAtPly = 1))],
      ["差が小数", broken("surroundingsDiff", (c) => (part(c, "pvMinusActual").kingSurroundingsOwn = 0.5))],
      ["counterfactual が null", withCounterfactual(null)],
    ];
    for (const [name, line] of failing) expect(validate(line, schema), name).not.toEqual([]);
    expect(validate(broken("surroundingsDiff", (c) => (part(c, "pvMinusActual", "capturedRoles", "us").pawn = -2)), schema), "差 −2").toEqual([]);
    expect(validate(broken("surroundingsDiff", (c) => (c.pvFirstMove = "G*5b")), schema), "打つ手の 1 手目").toEqual([]);
  });
});

// ---- STEP D2.5 の v0.5(docs/STEP_D2.5_PLAN_2026-09-15.md §2・§3)----
describe("STEP D2.5 の v0.5(玉の区域の数・形勢の状態)", () => {
  it("v0.5 のスキーマは、v0.4 に 6 つの欄(trigger.positionFacts・branch.standingPair・compared の actual と pv の positionFactsEnd・pvMinusActual.positionFacts・provenance の rule の standing と positionFacts)を足しただけ(版の値・$id・title・description のほかは v0.4 と同じ)", () => {
    const v05 = clone(schema) as unknown as Json;
    const v04 = schemaV04 as unknown as Json;
    const walk = (root: Json, ...keys: Array<string | number>): Json => keys.reduce<Json>((node, key) => (node as Record<string | number, unknown>)[key] as Json, root);
    const removeAfter = (holder: Json, key: string, after: string): void => {
      const properties = holder.properties as Json;
      const required = holder.required as string[];
      expect(Object.keys(properties).indexOf(key), key).toBe(Object.keys(properties).indexOf(after) + 1);
      expect(required.indexOf(key), key).toBe(required.indexOf(after) + 1);
      delete properties[key];
      holder.required = required.filter((name) => name !== key);
    };
    const properties = v05.properties as Json;
    expect(properties.schemaVersion).toEqual({ const: "0.5" });
    removeAfter(walk(properties, "trigger"), "positionFacts", "kingSurroundings");
    removeAfter(walk(properties, "branch"), "standingPair", "evaluationAfter");
    const compared = walk(properties, "counterfactual", "oneOf", 1);
    for (const side of ["actual", "pv"]) removeAfter(walk(compared, "properties", side), "positionFactsEnd", "kingSurroundingsEnd");
    removeAfter(walk(compared, "properties", "pvMinusActual"), "positionFacts", "kingSurroundingsOwn");
    const rule = walk(properties, "provenance", "properties", "analysis", "properties", "rule");
    removeAfter(rule, "positionFacts", "standing");
    removeAfter(rule, "standing", "notEvaluationCp");
    properties.schemaVersion = { const: "0.4" };
    for (const key of ["$id", "title", "description"]) v05[key] = v04[key];
    expect(v05).toEqual(v04);
  });

  it("v0.5 の欄の境目(手で書き換えた 1 行): 区域の升 5・駒 39・升 10・負の駒・片側だけの null・知らない状態・undetermined に measured や mateZero・状態の欄に理由の文字列・差の升 −10・規則の区域に知らない値・境が小数は落ち、差の −9・駒 38 は通る", () => {
    const base = lineOf(at(T2_EVENTS[0]![1], 49));
    const changed = (from: Json, change: (line: Json) => void): Json => {
      const line = clone(from);
      change(line);
      return line;
    };
    const facts = (line: Json, key: string): Json => ((line.trigger as Json).positionFacts as Json)[key] as Json;
    const pair = (line: Json): Json => (line.branch as Json).standingPair as Json;
    const diff = (line: Json, key: string): Json => (((line.counterfactual as Json).pvMinusActual as Json).positionFacts as Json)[key] as Json;
    const rule = (line: Json): Json => ((line.provenance as Json).analysis as Json).rule as Json;
    const compared = CF_LINES.surroundingsDiff!;
    const failing: Array<[string, Json]> = [
      ["区域の升 5", changed(base, (l) => (facts(l, "zoneSquares").opponentKingZone = 5))],
      ["区域に届く駒 39", changed(base, (l) => (facts(l, "zonePieces").opponentKingZone = { bySente: 39, byGote: 0 }))],
      ["区域の升に届く利き 10", changed(base, (l) => (facts(l, "zoneControl").opponentKingZone = { bySente: 10, byGote: 0 }))],
      ["負の駒", changed(base, (l) => (facts(l, "zonePieces").ownKingZone = { bySente: -1, byGote: 0 }))],
      ["升は数えたのに駒だけ null", changed(base, (l) => (facts(l, "zonePieces").ownKingZone = null))],
      ["知らない状態の名前", changed(base, (l) => (pair(l).before = "winning"))],
      ["undetermined に measured", changed(base, (l) => (pair(l).before = { undetermined: "measured" }))],
      ["undetermined に mateZero(mate 0 は行に出ない)", changed(base, (l) => (pair(l).after = { undetermined: "mateZero" }))],
      ["状態の欄に理由の文字列", changed(base, (l) => (pair(l).after = "undetermined"))],
      ["差の升 −10", changed(compared, (l) => (diff(l, "zoneControl").ownKingZone = { bySente: -10, byGote: 0 }))],
      ["規則の区域に知らない値", changed(base, (l) => ((rule(l).positionFacts as Json).zone = "king_only"))],
      ["境が小数", changed(base, (l) => ((rule(l).standing as Json).aheadCp = 300.5))],
    ];
    for (const [name, line] of failing) expect(validate(line, schema), name).not.toEqual([]);
    expect(validate(changed(compared, (l) => (diff(l, "zoneControl").ownKingZone = { bySente: -9, byGote: 9 })), schema), "差の升 −9・+9").toEqual([]);
    expect(validate(changed(base, (l) => (facts(l, "zonePieces").opponentKingZone = { bySente: 38, byGote: 0 })), schema), "駒 38").toEqual([]);
  });
});
