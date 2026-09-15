// STEP D3-COND(docs/STEP_D3-COND_PLAN_2026-09-15.md §6)。--events-cond の行・--cond-summary・条件式の節・定義と §7.2 の材料の読み込み・契約 diagnosis-condition v0.1 のスキーマ。
// **エンジンは起動しない。**
//
// 【正解の置き方】行は植えた記録(lib/failureEventFixtures.ts)を本番の関数に掛けて作る。期待の件数・並び・表の行は、植えた評価の並びから手で数えた。
// 【この試験が確かめないこと】判定と集計の中身(lib/condition.test.ts)。diagnose.ts の配線(diagnose.test.ts)。

import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { POSITION_FACTS_RULES } from "./counterfactual.js";
import { checkCondition, conditionTallyOf, type ConditionDefinition, type ConditionView, type LoadedCondition } from "./condition.js";
import {
  assertDistinctConditionIds,
  assertPersonLabel,
  conditionGameOf,
  conditionInputsOf,
  conditionLinesOf,
  conditionSummaryOf,
  loadConditionsFromDir,
  loadDiagnosisConditionSchema,
  readKifuEndings,
  readListedResults,
  renderConditionSection,
  validateDiagnosisConditionLine,
} from "./conditionReport.js";
import { diagnosisMomentsOf } from "./diagnosisMoment.js";
import { diagnoseRecords, DRAFT_RULE_1, NOT_EVALUATION_CP, STANDING_BOUNDS } from "./failureEvent.js";
import { engineRef, GAME01_MOVES, plantedRecords } from "./failureEventFixtures.js";
import { buildProvenance, loadFailureEventSchema } from "./failureEventSchema.js";

const PROVENANCE = buildProvenance({
  recordPath: "fixture.jsonl",
  recordSha256: "0".repeat(64),
  meta: undefined,
  evaluator: null,
  analysisGit: { gitHead: null, dirty: null },
  rule: DRAFT_RULE_1,
  notEvaluationCp: NOT_EVALUATION_CP,
  standingBounds: STANDING_BOUNDS,
  positionFactsRules: POSITION_FACTS_RULES,
  repoRoot: "/nonexistent-repo-root",
});
const CONDITION_FIXTURES = fileURLToPath(new URL("./conditionFixtures/", import.meta.url));
const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const at = (view: ConditionView, path: string): unknown => path.split(".").reduce<unknown>((current, key) => (current as Record<string, unknown> | undefined)?.[key], view);

const definition = (id: string, patch: Partial<ConditionDefinition>): LoadedCondition =>
  checkCondition(
    { id, label: `試験 ${id}(仮)`, status: "draft", definitionText: "試験だけ", uses: [], thresholds: {}, appliesTo: ["failureEvent", "rise", "maxDropPair"], approval: null, evaluate: () => true, ...patch },
    new TextEncoder().encode(id),
  );
/** A: いつも真 / B: 反事実の手数(compared の門)/ C: 上がりだけ、直前の評価が +300 以上 */
const A = definition("test_only_a", { uses: ["counterfactual.state"] });
const B = definition("test_only_b", { uses: ["counterfactual.comparedPlies"] });
const C = definition("test_only_c", { uses: ["trigger.evaluationBefore.scoreCp"], appliesTo: ["rise"], evaluate: (v) => (at(v, "trigger.evaluationBefore.scoreCp") as number) >= 300 });

/** ply 0・2・4・6 に +500・0・+600・+600 → 組 1(差 −500 = 急落、Event と最大の下がりの組)・組 3(差 +600 = 上がり)・組 5(差 0) */
function plantedGame() {
  const records = plantedRecords(GAME01_MOVES.slice(0, 6), { 0: engineRef(500), 2: engineRef(0), 4: engineRef(600), 6: engineRef(600) });
  const { events } = diagnoseRecords("k", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
  const moments = diagnosisMomentsOf("k", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events);
  return { events, moments };
}

describe("conditionLinesOf(計画 §6 の --events-cond)", () => {
  it("入力(Event → 上がり → 最大の下がり)ごとに定義を並びの順に当て、判定しない行は書かない。行は契約 diagnosis-condition v0.1 のスキーマを通る", () => {
    const { events, moments } = plantedGame();
    expect([events.map((event) => [event.branchPly, event.branch.kinds]), moments.rises.map((rise) => rise.branchPly), "branchPly" in moments.maxDrop ? moments.maxDrop.branchPly : null]).toStrictEqual([[[1, ["cpDrop"]]], [3], 1]);
    const lines = conditionLinesOf(conditionInputsOf(events, moments), [A, B, C], PROVENANCE);
    // B は compared の門で読む(植えた記録の counterfactual の状態をこの行から読み、lib を通さずに期待を決める)
    const bState = (compared: boolean) => (compared ? "match" : "undecidable");
    const eventCompared = events[0]!.counterfactual.state === "compared";
    const riseCompared = moments.rises[0]!.counterfactual.state === "compared";
    expect(lines.map((line) => [line.eventClass, line.branchPly, line.condition.id, line.result.state])).toStrictEqual([
      ["failureEvent", 1, "test_only_a", "match"],
      ["failureEvent", 1, "test_only_b", bState(eventCompared)],
      ["rise", 3, "test_only_a", "match"],
      ["rise", 3, "test_only_b", bState(riseCompared)],
      ["rise", 3, "test_only_c", "noMatch"],
      ["maxDrop", 1, "test_only_a", "match"],
      ["maxDrop", 1, "test_only_b", bState(eventCompared)],
    ]);
    const schema = loadDiagnosisConditionSchema();
    for (const line of lines) {
      expect(Object.keys(line)).toStrictEqual(["contract", "schemaVersion", "kifuId", "eventClass", "branchPly", "condition", "result", "provenance"]);
      expect([line.contract, line.schemaVersion, line.kifuId, line.condition.label, line.condition.status]).toStrictEqual(["diagnosis-condition", "0.1", "k", `試験 ${line.condition.id}(仮)`, "draft"]);
      expect(validateDiagnosisConditionLine(clone(line), schema)).toStrictEqual([]);
    }
  });

  it("最大の下がりの状態の行(noDrop)と appliesTo の外の入力からは行を作らない", () => {
    const records = plantedRecords(GAME01_MOVES.slice(0, 2), { 0: engineRef(100), 2: engineRef(200) });
    const { events } = diagnoseRecords("q", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN);
    const moments = diagnosisMomentsOf("q", records, DRAFT_RULE_1, DEFAULT_INITIAL_SFEN, events);
    expect([events.length, moments.rises.length, "state" in moments.maxDrop ? moments.maxDrop.state : null]).toStrictEqual([0, 0, "noDrop"]);
    expect(conditionLinesOf(conditionInputsOf(events, moments), [A, C], PROVENANCE)).toStrictEqual([]);
  });

  it("全ての手の組の行は書かない(D4 計画 Q-1)", () => {
    const { moments } = plantedGame();
    const pairRow = { kifuId: "k", pairKind: "compared" as const, ...(moments.rises[0]! as object) } as never;
    expect(() => conditionLinesOf([{ kind: "pair", row: pairRow }], [definition("test_only_p", { uses: ["counterfactual.state"], appliesTo: ["pair"] })], PROVENANCE)).toThrow("全ての手の組の行は --events-cond に書かない");
  });
});

describe("契約 diagnosis-condition v0.1 のスキーマ", () => {
  it("出どころは Failure Event の今の版(v0.6)と同じ定義。契約と版は const", () => {
    const schema = loadDiagnosisConditionSchema() as { properties: Record<string, unknown>; required: string[] };
    const failureEvent = loadFailureEventSchema() as { properties: Record<string, unknown> };
    expect(schema.properties.provenance).toStrictEqual(failureEvent.properties.provenance);
    expect([schema.properties.contract, (schema.properties.schemaVersion as { const: string }).const, schema.required]).toStrictEqual([
      { const: "diagnosis-condition" },
      "0.1",
      ["contract", "schemaVersion", "kifuId", "eventClass", "branchPly", "condition", "result", "provenance"],
    ]);
  });

  it("境目: 行の種類 pair・(仮)の無い名前・空の missing・知らない欄・64 桁でない sha・notJudged の状態・理由の形の違い は通らない。3 つの理由の形は通る", () => {
    const { events, moments } = plantedGame();
    const [line] = conditionLinesOf(conditionInputsOf(events, moments), [A], PROVENANCE);
    const base = clone(line!) as unknown as Record<string, any>;
    const schema = loadDiagnosisConditionSchema();
    expect(validateDiagnosisConditionLine(base, schema)).toStrictEqual([]);
    const variants: Array<[string, (value: Record<string, any>) => void]> = [
      ["pair", (value) => (value.eventClass = "pair")],
      ["(仮)なし", (value) => (value.condition.label = "試験 test_only_a")],
      ["空の missing", (value) => (value.result = { state: "undecidable", missing: [] })],
      ["知らない欄", (value) => (value.person = "p1")],
      ["sha", (value) => (value.condition.definitionSha256 = "abc")],
      ["notJudged", (value) => (value.result = { state: "notJudged", reason: "kindNotApplied" })],
      ["理由の形", (value) => (value.result = { state: "undecidable", missing: [{ path: "consequences.mate", reason: { kind: "gate", gatePath: "consequences.windowShort" } }] })],
      ["契約", (value) => (value.contract = "diagnosis-moment")],
    ];
    for (const [name, mutate] of variants) {
      const value = clone(base);
      mutate(value);
      expect(validateDiagnosisConditionLine(value, schema), name).not.toStrictEqual([]);
    }
    const reasons = [
      { kind: "gate", gatePath: "consequences.windowShort", actual: true },
      { kind: "gate", gatePath: "trigger.focus.state", actual: "pending" },
      { kind: "null" },
      { kind: "undetermined", undetermined: "unrecorded" },
    ];
    for (const reason of reasons) {
      const value = clone(base);
      value.result = { state: "undecidable", missing: [{ path: "consequences.mate", reason }] };
      expect(validateDiagnosisConditionLine(value, schema), JSON.stringify(reason)).toStrictEqual([]);
    }
  });
});

describe("renderConditionSection・conditionSummaryOf(計画 §6 の S-3・S-5)", () => {
  const { events, moments } = plantedGame();
  const game = conditionGameOf({ kifuId: "k", meta: undefined, events, moments, endings: new Map([["k", { kind: "resign", ply: 51 }]]), listedResults: new Map([["k", "loss"]]) });
  const tallies = [A, C].map((loaded) => conditionTallyOf("p9", [game], loaded));
  const sources = { kifuDir: "kifu", listedResults: "listed.json" };

  it("見出しに label(仮)と status を出し、表の行は手で数えた値(A: Event 1・上がり 1 が該当、最大の下がりの組は Event と同じ組で数えない / C: 上がりだけ)", () => {
    const lines = renderConditionSection("p9", tallies, sources);
    expect(lines).toContain(`### 試験 test_only_a(仮)(id: test_only_a・status: draft・definitionSha256: ${A.definitionSha256.slice(0, 12)})`);
    expect(lines).toContain(`### 試験 test_only_c(仮)(id: test_only_c・status: draft・definitionSha256: ${C.definitionSha256.slice(0, 12)})`);
    expect(lines).toContain("| Failure Event・上がり・最大の下がりの組 | 2 | 0 | 2 | 0 | 0 | 0 | 1 | 1 |");
    expect(lines).toContain("| 上がり | 0 | 1 | 1 | 0 | 2 | 0 | 0 | 0 |");
    expect(lines).toContain("- 人: p9(--person の記号)。数えた局: 1(先手 1・後手 0)。error 行の記録・数えられなかった記録は入れていない");
    expect(lines).toContain("- §7.2 用の列(kinds に cpDrop か mateDrop がある Failure Event だけ): 該当 1・非該当 0・判定不能 0・該当があった局 1");
    expect(lines.some((line) => line.startsWith("| k | 1 | cpDrop | ") && line.endsWith(" | 落とした | 負け | 一致 |"))).toBe(true);
    expect(lines).toContain("- §7.2 用の列: この定義は Failure Event に当てない");
  });

  it("集計の JSON は契約 diagnosis-condition-summary と版を先頭に持つ", () => {
    const summary = conditionSummaryOf({ person: "p9", inputs: [{ path: "k.jsonl", sha256: "0".repeat(64), kifuId: "k", counted: true }], sources, analysisGit: { gitHead: null, dirty: null }, tallies });
    expect(Object.keys(summary)).toStrictEqual(["contract", "schemaVersion", "person", "inputs", "sources", "analysis", "conditions"]);
    expect([summary.contract, summary.schemaVersion, summary.person, summary.conditions.map((tally) => tally.condition.id)]).toStrictEqual(["diagnosis-condition-summary", "0.1", "p9", ["test_only_a", "test_only_c"]]);
  });
});

describe("読み込み(定義のディレクトリ・§7.2 の材料・--person)", () => {
  it("定義のディレクトリはファイル名の順に読み、同じ id が 2 つあれば止める", async () => {
    const loaded = await loadConditionsFromDir(CONDITION_FIXTURES);
    expect(loaded.map((entry) => entry.definition.id)).toStrictEqual(["test_only_always", "test_only_focus_stated", "test_only_loadable"]);
    expect(() => assertDistinctConditionIds([A, A])).toThrow("同じ id の条件式の定義が 2 つある: test_only_a");
  });

  it("固定棋譜 JSON から id → ending(キーが無い棋譜は undefined・null は null)。同じ id・形の違う ending は止める", () => {
    const dir = mkdtempSync(join(tmpdir(), "d3-cond-kifu-"));
    try {
      writeFileSync(join(dir, "a.json"), JSON.stringify({ id: "k-1", source: "試験", ending: { kind: "resign", ply: 51 }, moves: [] }));
      writeFileSync(join(dir, "b.json"), JSON.stringify({ id: "k-2", source: "試験", moves: [] }));
      writeFileSync(join(dir, "c.json"), JSON.stringify({ id: "k-3", source: "試験", ending: null, moves: [] }));
      writeFileSync(join(dir, "d.json"), JSON.stringify({ id: "k-4", source: "試験", ending: { kind: "unreadable", reason: "ply_mismatch", ply: null }, moves: [] }));
      expect([...readKifuEndings(dir)]).toStrictEqual([
        ["k-1", { kind: "resign", ply: 51 }],
        ["k-2", undefined],
        ["k-3", null],
        ["k-4", { kind: "unreadable", reason: "ply_mismatch", ply: null }],
      ]);
      writeFileSync(join(dir, "e.json"), JSON.stringify({ id: "k-1", source: "試験", moves: [] }));
      expect(() => readKifuEndings(dir)).toThrow("同じ id の棋譜が 2 つある: k-1");
      rmSync(join(dir, "e.json"));
      writeFileSync(join(dir, "f.json"), JSON.stringify({ id: "k-5", ending: { kind: 3 } }));
      expect(() => readKifuEndings(dir)).toThrow("f.json の ending が固定棋譜 JSON の形でない");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("README の表の JSON は win・loss だけ。--person は p と数字の記号だけ", () => {
    const dir = mkdtempSync(join(tmpdir(), "d3-cond-listed-"));
    try {
      writeFileSync(join(dir, "ok.json"), JSON.stringify({ "k-1": "win", "k-2": "loss" }));
      writeFileSync(join(dir, "bad.json"), JSON.stringify({ "k-1": "draw" }));
      expect([...readListedResults(join(dir, "ok.json"))]).toStrictEqual([
        ["k-1", "win"],
        ["k-2", "loss"],
      ]);
      expect(() => readListedResults(join(dir, "bad.json"))).toThrow("k-1 の値が win・loss でない");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
    expect(() => {
      assertPersonLabel("p1");
      assertPersonLabel("p20");
    }).not.toThrow();
    for (const label of ["yamada", "", "P1", "p", "p1 "]) expect(() => assertPersonLabel(label), label).toThrow("--person は名前でない記号");
  });

  it("1 局ぶんの集計の入力: 本人の側は meta から、終局と README の表は kifuId で引く(表が無い・載っていなければ undefined と null)", () => {
    const { events, moments } = plantedGame();
    const mirrored = { kind: "meta", kifuId: "k", mirrored: true, originalUserSide: "gote" } as never;
    const withTables = conditionGameOf({ kifuId: "k", meta: mirrored, events, moments, endings: new Map([["k", { kind: "timeUp", ply: 80 }]]), listedResults: new Map([["x", "win"]]) });
    const withoutTables = conditionGameOf({ kifuId: "k", meta: undefined, events, moments, endings: undefined, listedResults: undefined });
    expect([withTables.userSide, withTables.ending, withTables.listedResult, withoutTables.userSide, withoutTables.ending, withoutTables.listedResult]).toStrictEqual(["gote", { kind: "timeUp", ply: 80 }, null, "sente", undefined, null]);
  });
});
