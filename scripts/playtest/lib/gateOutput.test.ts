// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §5・§7・§8)。契約 diagnosis-gate v0.1 の行・入力の確かめ・棄却の記録の追記(G-F10)。**エンジンは起動しない。**
//
// 【正解の置き方】期待は計画書の表と司令塔の決定 T-3・T-7・T-8 から手で書いた(実装の出力から写さない)。棄却の記録は一時ディレクトリにだけ書く。

import { mkdtempSync, readFileSync, rmSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import type { MetaLine } from "../invariants/types.js";
import { checkCondition, type ConditionDefinition, type LoadedCondition, type PairRow } from "./condition.js";
import { GATE_VALUES, gateOf, gateTallyOf, type GatePairsGame, type GateTally, type JudgedPair } from "./gate.js";
import {
  appendGateRecords,
  gateInputProblems,
  gateLineOf,
  gateRecordsSummary,
  renderGateMarkdown,
  testGoteProblems,
  testSetOf,
  validateDiagnosisGateLine,
  type GateInputEntry,
  type GateRunContext,
} from "./gateOutput.js";
import { baselineTallyOf } from "./gate.js";

const SHA = (c: string) => c.repeat(64);
const definition = (patch: Partial<ConditionDefinition> = {}): ConditionDefinition => ({
  id: "test_only_out",
  label: "試験だけの定義(仮)",
  status: "draft",
  definitionText: "試験だけ",
  uses: ["standingPair.before"],
  thresholds: {},
  appliesTo: ["pair"],
  approval: null,
  evaluate: () => true,
  ...patch,
});
const loaded = (d: ConditionDefinition, bytes = d.id): LoadedCondition => checkCondition(d, new TextEncoder().encode(bytes));
const APPROVED = { approvedBy: "test", date: "2026-09-16", record: "test" };

const stub = (kifuId: string, from: number, before: "ahead" | "level", after: "ahead" | "level" | "behind"): PairRow =>
  ({ kifuId, pairKind: "compared", branchPly: from + 1, fromReadyPly: from, toReadyPly: from + 2, standingPair: { before, after }, counterfactual: { state: "compared" } }) as unknown as PairRow;
const J = (actual: "match" | "noMatch"): JudgedPair => ({ actual: { state: actual, usedValues: {} }, pv: { state: "noMatch", usedValues: {} } });

/** 真 20 組(崩れ 10)・偽 100 組(崩れ 10)を 3 局ずつ(lib/gate.test.ts の MATERIAL_OK と同じ件数) */
function tally(trueN: number, trueC: number, falseN: number, falseC: number, games = 3): GateTally {
  const build = (prefix: string, n: number, c: number, judged: JudgedPair) => {
    const perGame: PairRow[][] = Array.from({ length: games }, () => []);
    for (let k = 0; k < n; k += 1) perGame[k % games]!.push(stub(`${prefix}${k % games}`, perGame[k % games]!.length * 100, "ahead", k < c ? "level" : "ahead"));
    const kept = perGame.map((pairs, g) => ({ pairs, g })).filter(({ pairs }) => pairs.length > 0);
    return { games: kept.map(({ pairs, g }): GatePairsGame => ({ kifuId: `${prefix}${g}`, pairs, movesMissing: 0, rowStandings: [] })), judged: kept.map(({ pairs }) => pairs.map(() => judged)) };
  };
  const t = build("t", trueN, trueC, J("match"));
  const f = build("f", falseN, falseC, J("noMatch"));
  return gateTallyOf([...t.games, ...f.games], [...t.judged, ...f.judged]);
}

const CONTEXT: GateRunContext = {
  person: "p2",
  testPerson: "p1",
  referenceNodes: 4_000_000,
  materialInputs: [{ path: "scripts/playtest/records/x/a.jsonl", sha256: SHA("a") }],
  test: { ...testSetOf(6, 0), inputs: [{ path: "scripts/playtest/records/x/b.jsonl", sha256: SHA("b") }] },
  gateValues: GATE_VALUES,
  conditionsInRun: 1,
  provenance: { gitHead: null, dirty: null },
};
const plain = (value: unknown): unknown => JSON.parse(JSON.stringify(value));

describe("契約 diagnosis-gate v0.1 の行(計画 §7・T-3)", () => {
  it("approved の定義: meets の行がスキーマに合う。draft: notJudged draft で集計つき。pair を含まない定義: notJudged pairNotApplied で集計なし", () => {
    const material = tally(20, 10, 100, 10);
    const test = tally(3, 2, 10, 1, 1);
    const approved = loaded(definition({ status: "approved", approval: APPROVED }));
    const meets = gateLineOf(CONTEXT, approved, { material, test, gate: gateOf("approved", material, test) });
    expect(validateDiagnosisGateLine(plain(meets))).toEqual([]);
    expect(meets.gate).toMatchObject({ verdict: "meets", text: "追加検証する価値のある個人パターン候補" });
    expect(Object.keys(meets)).toEqual(["contract", "schemaVersion", "person", "testPerson", "condition", "source", "material", "test", "gate", "gateValues", "conditionsInRun", "provenance"]);

    const draft = gateLineOf(CONTEXT, loaded(definition()), { material, test, gate: gateOf("draft", material, test) });
    expect(validateDiagnosisGateLine(plain(draft))).toEqual([]);
    expect(draft.gate).toEqual({ notJudged: "draft" });

    const notApplied = gateLineOf(CONTEXT, loaded(definition({ appliesTo: ["failureEvent"], uses: ["trigger.focus.state"] })), null);
    expect(validateDiagnosisGateLine(plain(notApplied))).toEqual([]);
    expect(notApplied.gate).toEqual({ notJudged: "pairNotApplied" });
    expect(Object.hasOwn(notApplied.material, "tally")).toBe(false);
  });

  it("スキーマは食い違った形を通さない: pairNotApplied に集計がある / draft に文がある / 人のラベルが名前 / ほかの verdict の語", () => {
    const material = tally(20, 10, 100, 10);
    const test = tally(3, 2, 10, 1, 1);
    const draft = plain(gateLineOf(CONTEXT, loaded(definition()), { material, test, gate: gateOf("draft", material, test) })) as Record<string, any>;
    const notApplied = plain(gateLineOf(CONTEXT, loaded(definition({ appliesTo: ["failureEvent"], uses: ["trigger.focus.state"] })), null)) as Record<string, any>;
    const meets = plain(gateLineOf(CONTEXT, loaded(definition({ status: "approved", approval: APPROVED })), { material, test, gate: gateOf("approved", material, test) })) as Record<string, any>;
    expect(validateDiagnosisGateLine({ ...notApplied, material: { ...notApplied.material, tally: material } })).not.toEqual([]);
    expect(validateDiagnosisGateLine({ ...draft, gate: { notJudged: "draft", text: "現データでは個人パターンとして採用する根拠が不足" } })).not.toEqual([]);
    expect(validateDiagnosisGateLine({ ...draft, person: "tatsunami" })).not.toEqual([]);
    expect(validateDiagnosisGateLine({ ...meets, gate: { ...meets.gate, verdict: "promising" } })).not.toEqual([]);
    // S-2: gateValues は人間の確定値だけ / G-3 を当てた(applicable)行の values は n・actualTrue・pvTrue が必須
    expect(validateDiagnosisGateLine({ ...meets, gateValues: { ...meets.gateValues, minTruePairs: 9 } })).not.toEqual([]);
    const items = meets.gate.items.map((entry: Record<string, unknown>) => (entry.item === "G-3" ? { ...entry, values: {} } : entry));
    expect(validateDiagnosisGateLine({ ...meets, gate: { ...meets.gate, items } })).not.toEqual([]);
  });

  it("試す側の集合の名前(Q-10): 後手 0 局は sente<n> で仮、後手があれば sente<n>+gote<m>", () => {
    expect(testSetOf(6, 0)).toEqual({ set: "sente6", provisional: true });
    expect(testSetOf(6, 4)).toEqual({ set: "sente6+gote4", provisional: false });
  });
});

// ---- 入力の確かめ ----

const meta = (kifuId: string, patch: Record<string, unknown> = {}): MetaLine => ({ kind: "meta", kifuId, startedAt: "t", gitHead: null, enginePath: "/e", referenceNodes: 4_000_000, ...patch }) as unknown as MetaLine;
const entry = (name: string, patch: Partial<GateInputEntry> = {}): GateInputEntry => ({ name, path: `scripts/playtest/records/x/${name}.jsonl`, kifuId: name, sha256: SHA(name.slice(-1)), meta: meta(name), errorLines: 0, ...patch });

describe("gateInputProblems(計画 §2 の Q-2・§6・T-8)", () => {
  it("通る: ラベルが記号で違い、referenceNodes がそろい、重なりが無い", () => {
    expect(gateInputProblems({ person: "p2", testPerson: "p1", material: [entry("m1"), entry("m2")], testSente: [entry("s3")], testGote: [] })).toEqual({ problems: [], referenceNodes: 4_000_000 });
  });

  it("G-F8 材料と試す側で referenceNodes が違う → 止める", () => {
    const result = gateInputProblems({ person: "p2", testPerson: "p1", material: [entry("m1")], testSente: [entry("s2", { meta: meta("s2", { referenceNodes: 400_000 }) })], testGote: [] });
    expect(result.referenceNodes).toBeNull();
    expect(result.problems.join("\n")).toMatch(/referenceNodes がそろわない/);
  });

  it("止める: 同じラベル・名前のラベル・材料と試す側に同じ記録(sha256・kifuId)・error 行・先手の列に後手の記録", () => {
    const problems = (input: Parameters<typeof gateInputProblems>[0]) => gateInputProblems(input).problems.join("\n");
    expect(problems({ person: "p1", testPerson: "p1", material: [entry("m1")], testSente: [entry("s2")], testGote: [] })).toMatch(/同じ人のラベル/);
    expect(problems({ person: "someone", testPerson: "p1", material: [entry("m1")], testSente: [entry("s2")], testGote: [] })).toMatch(/--person は p1・p2 の形/);
    expect(problems({ person: "p2", testPerson: "p1", material: [entry("m1")], testSente: [entry("s2", { sha256: SHA("1"), kifuId: "m1" })], testGote: [] })).toMatch(/同じ sha256[\s\S]*同じ kifuId/);
    expect(problems({ person: "p2", testPerson: "p1", material: [entry("m1", { errorLines: 1 })], testSente: [entry("s2")], testGote: [] })).toMatch(/error 行/);
    expect(problems({ person: "p2", testPerson: "p1", material: [entry("m1")], testSente: [entry("s2", { meta: meta("s2", { mirrored: true, originalUserSide: "gote" }) })], testGote: [] })).toMatch(/本人が gote/);
  });

  it("R-1 根の外の入力(.. で始まる・絶対パス)→ 止める。根の中と .. で始まる名前のディレクトリは通す", () => {
    const problems = (path: string) => gateInputProblems({ person: "p2", testPerson: "p1", material: [entry("m1", { path })], testSente: [entry("s2")], testGote: [] }).problems;
    expect(problems("../../../Users/someone/sgogi-coach/scripts/playtest/records/real-02/kifu2-01.jsonl").join("")).toContain("根の外");
    expect(problems("/Users/someone/a.jsonl").join("")).toContain("根の外");
    expect(problems("..").join("")).toContain("根の外");
    expect(problems("scripts/playtest/records/real-02/kifu2-01.jsonl")).toEqual([]);
    expect(problems("..hidden/a.jsonl")).toEqual([]);
  });

  it("S-1 --test-person が記号の形でない → 止める(名前のラベルを受けない)", () => {
    const result = gateInputProblems({ person: "p2", testPerson: "someone", material: [entry("m1")], testSente: [entry("s2")], testGote: [] });
    expect(result.problems.join("\n")).toContain("--test-person は p1・p2 の形");
    expect(gateInputProblems({ person: "p2", testPerson: "p1x", material: [entry("m1")], testSente: [entry("s2")], testGote: [] }).problems.join("\n")).toContain("--test-person は p1・p2 の形");
  });

  it("T-7 --test-gote: 定義が 0 本・draft を含む → 止める / すべて approved → 通る / 後手なし → 何も言わない", () => {
    const approved = loaded(definition({ status: "approved", approval: APPROVED }));
    expect(testGoteProblems(4, [])).toHaveLength(1);
    expect(testGoteProblems(4, [approved, loaded(definition({ id: "test_only_draft" }))]).join("")).toMatch(/draft: test_only_draft/);
    expect(testGoteProblems(4, [approved])).toEqual([]);
    expect(testGoteProblems(0, [loaded(definition())])).toEqual([]);
  });
});

// ---- 棄却の記録(G-F10)----

describe("棄却の記録(計画 §5 の Q-8、G-F10)", () => {
  it("G-F10 2 回追記(定義を 1 バイト変える)→ 2 行とも残り definitionSha256 が違う。pair を含まない定義の行は追記しない。0 行ならファイルを作らない", () => {
    const dir = join(mkdtempSync(join(tmpdir(), "gate-records-")), "gate");
    try {
      const material = tally(20, 10, 100, 10);
      const test = tally(3, 2, 10, 1, 1);
      const first = loaded(definition(), "test_only_out v1");
      const second = loaded(definition(), "test_only_out v2");
      const notApplied = gateLineOf(CONTEXT, loaded(definition({ id: "test_only_event", appliesTo: ["failureEvent"], uses: ["trigger.focus.state"] })), null);

      expect(appendGateRecords(dir, "p2", [notApplied])).toBe(0);
      expect(existsSync(dir)).toBe(false);
      expect(gateRecordsSummary(dir, "p2")).toEqual({ rows: 0, conditions: 0 });

      expect(appendGateRecords(dir, "p2", [gateLineOf(CONTEXT, first, { material, test, gate: gateOf("draft", material, test) }), notApplied])).toBe(1);
      expect(appendGateRecords(dir, "p2", [gateLineOf(CONTEXT, second, { material, test, gate: gateOf("draft", material, test) })])).toBe(1);
      const rows = readFileSync(join(dir, "p2.jsonl"), "utf-8").trim().split("\n").map((line) => JSON.parse(line) as { condition: { definitionSha256: string } });
      expect(rows).toHaveLength(2);
      expect(rows[0]!.condition.definitionSha256).not.toBe(rows[1]!.condition.definitionSha256);
      expect(rows.map((row) => row.condition.definitionSha256)).toEqual([first.definitionSha256, second.definitionSha256]);
      expect(gateRecordsSummary(dir, "p2")).toEqual({ rows: 2, conditions: 2 });
      expect(() => appendGateRecords(dir, "../p2", [])).toThrow(/p1・p2 の形/);
    } finally {
      rmSync(join(dir, ".."), { recursive: true, force: true });
    }
  });
});

describe("renderGateMarkdown(計画 §7)", () => {
  it("基準値の表・pair を含まない定義の id・draft は判定を出さない文・approved は項目の表と verdict の文だけ", () => {
    const material = tally(20, 10, 100, 10);
    const test = tally(3, 2, 10, 1, 1);
    const games: GatePairsGame[] = [{ kifuId: "g", pairs: [stub("g", 0, "ahead", "level")], movesMissing: 0, rowStandings: [] }];
    const lines = [
      gateLineOf(CONTEXT, loaded(definition({ status: "approved", approval: APPROVED })), { material, test, gate: gateOf("approved", material, test) }),
      gateLineOf(CONTEXT, loaded(definition({ id: "test_only_d" })), { material, test, gate: gateOf("draft", material, test) }),
      gateLineOf(CONTEXT, loaded(definition({ id: "test_only_event", appliesTo: ["failureEvent"], uses: ["trigger.focus.state"] })), null),
    ];
    const text = renderGateMarkdown({
      person: "p2",
      testPerson: "p1",
      referenceNodes: 4_000_000,
      material: { files: 1, baseline: baselineTallyOf(games) },
      test: { ...testSetOf(6, 0), files: 1, baseline: baselineTallyOf(games) },
      lines,
      recordsBefore: { rows: 0, conditions: 0 },
    }).join("\n");
    expect(text).toContain("## 全ての組の崩れ(条件式なし)");
    expect(text).toContain("| 材料 | 1 | 1 / 1(100.0%)");
    expect(text).toContain("- test_only_event(draft)");
    expect(text).toMatch(/この実行で Gate に当てた条件式: 2 本/);
    expect(text).toMatch(/draft の定義なので Gate の判定を出さない/);
    expect(text).toMatch(/\| G-2 \| trueCollapsed 10・trueDenominator 20・falseCollapsed 10・falseDenominator 100 \|/);
    expect(text.match(/追加検証する価値のある個人パターン候補/g)).toHaveLength(1);
    expect(text).not.toMatch(/根拠が不足/);
  });
});
