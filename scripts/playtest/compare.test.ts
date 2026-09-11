// STEP T-5(T5-A)。compare.tsの純粋関数(正規化・比較)のテスト。
// docs/STEP_T-5_PLAN_2026-09-11.md 2. T5-A「一致するケース、record行の値が違う
// ケース、行数が違うケース、除外フィールドだけ違うケース」を満たす。

import { describe, expect, it } from "vitest";
import { compareNormalizedLines, diffPaths, normalizeJsonl, normalizeLine, type JsonlLine } from "./compare.js";

function metaLine(overrides: Partial<JsonlLine> = {}): JsonlLine {
  return {
    kind: "meta",
    kifuId: "k1",
    startedAt: "2026-09-11T00:00:00.000Z",
    gitHead: "abc123",
    enginePath: "/path/to/engine",
    ...overrides,
  };
}

function recordLine(overrides: Partial<JsonlLine> = {}): JsonlLine {
  return {
    kind: "record",
    ply: 4,
    sfen: "some-sfen",
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 123,
    response: { coach: [], plan: { candidateMoveLabels: {} } },
    ...overrides,
  };
}

function summaryLine(overrides: Partial<JsonlLine> = {}): JsonlLine {
  return {
    kind: "summary",
    plies: 10,
    totalMs: 25000,
    readyMsPerPly: [100, 200, 300],
    ...overrides,
  };
}

describe("normalizeLine", () => {
  it("record行からelapsedMsを除く", () => {
    const normalized = normalizeLine(recordLine({ elapsedMs: 999 }));
    expect(normalized.elapsedMs).toBeUndefined();
    expect(normalized.ply).toBe(4);
  });

  it("meta行からstartedAt/gitHead/enginePathを除く", () => {
    const normalized = normalizeLine(metaLine());
    expect(normalized.startedAt).toBeUndefined();
    expect(normalized.gitHead).toBeUndefined();
    expect(normalized.enginePath).toBeUndefined();
    expect(normalized.kifuId).toBe("k1");
  });

  it("summary行からtotalMs/readyMsPerPlyを除く", () => {
    const normalized = normalizeLine(summaryLine());
    expect(normalized.totalMs).toBeUndefined();
    expect(normalized.readyMsPerPly).toBeUndefined();
    expect(normalized.plies).toBe(10);
  });

  it("record/meta/summary以外(例: error)はそのまま返す", () => {
    const line: JsonlLine = { kind: "error", reason: "human_move_error", message: "x" };
    expect(normalizeLine(line)).toEqual(line);
  });
});

describe("diffPaths", () => {
  it("完全に一致する値は差分なし", () => {
    expect(diffPaths({ a: 1, b: { c: 2 } }, { a: 1, b: { c: 2 } })).toEqual([]);
  });

  it("ネストしたオブジェクトの不一致をドット表記で報告する", () => {
    expect(diffPaths({ a: { b: 1 } }, { a: { b: 2 } })).toEqual(["a.b"]);
  });

  it("配列要素の不一致を角括弧表記で報告する", () => {
    expect(diffPaths({ list: [1, 2] }, { list: [1, 3] })).toEqual(["list[1]"]);
  });

  it("limitを超える差分は切り詰める", () => {
    const a = { a: 1, b: 1, c: 1, d: 1 };
    const b = { a: 2, b: 2, c: 2, d: 2 };
    expect(diffPaths(a, b, 2)).toHaveLength(2);
  });
});

describe("normalizeJsonl", () => {
  it("複数行をパースして正規化する", () => {
    const raw = `${JSON.stringify(metaLine())}\n${JSON.stringify(recordLine())}\n`;
    const lines = normalizeJsonl(raw);
    expect(lines).toHaveLength(2);
    expect(lines[0]?.startedAt).toBeUndefined();
    expect(lines[1]?.elapsedMs).toBeUndefined();
  });

  it("空行を無視する", () => {
    const raw = `${JSON.stringify(recordLine())}\n\n\n`;
    expect(normalizeJsonl(raw)).toHaveLength(1);
  });
});

describe("compareNormalizedLines", () => {
  it("一致するケース: 同じ内容の2本は完全一致する", () => {
    const baseline = [metaLine(), recordLine()];
    const target = [metaLine(), recordLine()];
    const result = compareNormalizedLines(baseline, target, "b.jsonl");
    expect(result.matches).toBe(true);
    expect(result.diffs).toEqual([]);
  });

  it("除外フィールドだけ違うケース: startedAt/gitHead/elapsedMsだけが違えば一致扱いになる", () => {
    const baseline = normalizeJsonl(`${JSON.stringify(metaLine())}\n${JSON.stringify(recordLine())}\n`);
    const target = normalizeJsonl(
      `${JSON.stringify(metaLine({ startedAt: "2026-09-11T01:00:00.000Z", gitHead: "def456" }))}\n${JSON.stringify(recordLine({ elapsedMs: 42 }))}\n`,
    );
    const result = compareNormalizedLines(baseline, target, "b.jsonl");
    expect(result.matches).toBe(true);
  });

  it("record行の値が違うケース: 差分のply/phase/パスを報告する", () => {
    const baseline = [recordLine({ ply: 4, phase: "ready", response: { plan: { candidateMoveLabels: {} } } })];
    const target = [recordLine({ ply: 4, phase: "ready", response: { plan: { candidateMoveLabels: { "7g7f": "７六" } } } })];
    const result = compareNormalizedLines(baseline, target, "b.jsonl");
    expect(result.matches).toBe(false);
    expect(result.diffs).toHaveLength(1);
    expect(result.diffs[0]?.ply).toBe(4);
    expect(result.diffs[0]?.phase).toBe("ready");
    expect(result.diffs[0]?.paths).toContain("response.plan.candidateMoveLabels.7g7f");
  });

  it("行数が違うケース: matchesがfalseになり、行数がそれぞれ報告される", () => {
    const baseline = [metaLine(), recordLine(), recordLine({ ply: 6 })];
    const target = [metaLine(), recordLine()];
    const result = compareNormalizedLines(baseline, target, "b.jsonl");
    expect(result.matches).toBe(false);
    expect(result.baselineLineCount).toBe(3);
    expect(result.fileLineCount).toBe(2);
  });

  // STEP T-6(A-3): meta行のsearchMode/nodes/threadsは正規化の除外一覧に含めない
  // (=条件が違う記録は一致しない)。
  it("searchModeが違う2本は一致しない", () => {
    const baseline = normalizeJsonl(
      `${JSON.stringify(metaLine({ searchMode: "nodes", nodes: 4_000_000, threads: 1 }))}\n`,
    );
    const target = normalizeJsonl(
      `${JSON.stringify(metaLine({ searchMode: "movetime", nodes: 0, threads: 1 }))}\n`,
    );
    const result = compareNormalizedLines(baseline, target, "b.jsonl");
    expect(result.matches).toBe(false);
    expect(result.diffs[0]?.paths).toContain("searchMode");
  });
});
