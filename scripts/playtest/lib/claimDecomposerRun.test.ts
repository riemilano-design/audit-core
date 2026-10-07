// D-2b §2(c)(d)。lib/claimDecomposerRun.ts を見る。**LLM は 1 回も呼ばない(fetch は全部差し替え)。実費 0 円。**
// 試験の正解は実装の表・定数から作らない(手で書いた gold + 手で数えた期待値)。退化値(gold 0 本・
// 分解器が全部空席・上限に当たって途中で止まる)も当てる。

import { describe, expect, it } from "vitest";
import type { DecomposeConfig } from "./claimDecomposer.js";
import { runDecomposerOverGold, sumDecompositionCompare, type GoldFixtureFile } from "./claimDecomposerRun.js";
import type { DecompositionCompareResult } from "./decompositionCompare.js";
import type { SlotDeps } from "./seatRun.js";

type Rec = Record<string, unknown>;

function cfgOf(over: Partial<DecomposeConfig> = {}): DecomposeConfig {
  return { provider: "openai", model: "gpt-5.5", apiKey: "sk-test-DUMMY", prices: { inPerMillion: 5, outPerMillion: 30 }, reserveOutputTokens: 1_000, temperature: 0, capUsd: 10, ...over };
}
function claimOf(over: Rec = {}): Rec {
  return { claim_id: "c1", span: [0, 1], form: "direct_value", subject: "s", value: 1, unit: null, modifiers: { population: null, time_range: null, normalization: null }, evidence_pointer: null, ...over };
}
function openaiBody(json: unknown): Rec {
  return { id: "resp_1", model: "gpt-5.5-2026", status: "completed", output: [{ type: "message", content: [{ type: "output_text", text: JSON.stringify(json) }] }], usage: { input_tokens: 500, output_tokens: 200 } };
}

/** gold ごとに違う doc を順に返す fetch(gold の順 = decomposeOriginalText を呼ぶ順と一致させる)。 */
function fetchForDocs(docs: unknown[]): typeof fetch {
  let i = 0;
  return (async (_url: string, _init: RequestInit) => {
    const body = openaiBody(docs[Math.min(i, docs.length - 1)]);
    i += 1;
    return { status: 200, ok: true, text: async () => JSON.stringify(body) } as unknown as Response;
  }) as unknown as typeof fetch;
}
const DEPS_BASE: Omit<SlotDeps, "fetch"> = { sleep: async () => {} };

describe("runDecomposerOverGold", () => {
  it("gold 2 本が両方 present になり、compare が各本に付く。費用は gold をまたいで累積する", async () => {
    const goldA: GoldFixtureFile = { id: "a", original_text: "売上は100億円だった。", expected_claims: [claimOf({ span: [3, 7], value: 100, subject: "売上" })], expected_uncovered_number_sentences: [] };
    const goldB: GoldFixtureFile = { id: "b", original_text: "今年は50人だった。", expected_claims: [claimOf({ span: [0, 9], value: 50, subject: "人数" })], expected_uncovered_number_sentences: [] };
    const docA = { schemaVersion: "0.1", original_text: goldA.original_text, claims: [claimOf({ span: [3, 7], value: 100, subject: "売上" })] };
    const docB = { schemaVersion: "0.1", original_text: goldB.original_text, claims: [claimOf({ span: [0, 9], value: 999, subject: "人数" })] }; // value を外して一致しない例を混ぜる
    const fetch = fetchForDocs([docA, docB]);
    const results = await runDecomposerOverGold([goldA, goldB], "指示文", cfgOf(), { ...DEPS_BASE, fetch });
    expect(results.map((r) => r.goldId)).toEqual(["a", "b"]);
    expect(results[0]!.slot.present).toBe(true);
    expect(results[1]!.slot.present).toBe(true);
    expect(results[0]!.compare?.valueMatchCount).toBe(1); // A は value 一致
    expect(results[1]!.compare?.valueMatchCount).toBe(0); // B は value 不一致(999 ≠ 50)
    // 費用は gold をまたいで累積する(2 本目の cumulativeCostUsd は 1 本目より大きい)
    expect(results[1]!.slot.cumulativeCostUsd).toBeGreaterThan(results[0]!.slot.cumulativeCostUsd);
  });

  it("退化値: gold が 0 本なら結果も 0 件", async () => {
    const results = await runDecomposerOverGold([], "指示文", cfgOf(), { ...DEPS_BASE, fetch: fetchForDocs([]) });
    expect(results).toEqual([]);
  });

  it("上限に当たったら、その gold は空席になり残りの gold は送らない(capReached で打ち切る)", async () => {
    const goldA: GoldFixtureFile = { id: "a", original_text: "売上は100億円だった。", expected_claims: [], expected_uncovered_number_sentences: [] };
    const goldB: GoldFixtureFile = { id: "b", original_text: "今年は50人だった。", expected_claims: [], expected_uncovered_number_sentences: [] };
    const docA = { schemaVersion: "0.1", original_text: goldA.original_text, claims: [] };
    const fetch = fetchForDocs([docA]);
    // 1 本目で使う見込みだけで上限を越える極小の capUsd にする
    const results = await runDecomposerOverGold([goldA, goldB], "指示文", cfgOf({ capUsd: 0.0000001 }), { ...DEPS_BASE, fetch });
    expect(results.length).toBe(1);
    expect(results[0]!.slot.present).toBe(false);
    expect(results[0]!.slot.absentReason).toBe("cost_cap");
    expect(results[0]!.compare).toBeUndefined();
  });

  it("空席の gold には compare が付かない(present:false のときは比べる相手の実測が無い)", async () => {
    const goldA: GoldFixtureFile = { id: "a", original_text: "x", expected_claims: [], expected_uncovered_number_sentences: [] };
    // schema で 3 回とも落ちる doc(claim_id が空)
    const badDoc = { schemaVersion: "0.1", original_text: "x", claims: [{ claim_id: "" }] };
    const fetch = fetchForDocs([badDoc, badDoc, badDoc]);
    const results = await runDecomposerOverGold([goldA], "指示文", cfgOf(), { ...DEPS_BASE, fetch });
    expect(results[0]!.slot.present).toBe(false);
    expect(results[0]!.compare).toBeUndefined();
  });
});

function compareOf(over: Partial<DecompositionCompareResult> = {}): DecompositionCompareResult {
  return {
    span: { intersection: [[0, 1]], expectedOnly: [], actualOnly: [] },
    spanMatchedCount: 1, valueMatchCount: 1, formMatchCount: 1,
    formBreakdown: { direct_value: { total: 1, matched: 1 } },
    uncovered: { intersection: [], expectedOnly: [], actualOnly: [] },
    ...over,
  };
}

describe("sumDecompositionCompare(件数の合計だけ。指標の定義は変えない)", () => {
  it("退化値: 空配列は全部 0", () => {
    const totals = sumDecompositionCompare([]);
    expect(totals).toEqual({
      spanIntersection: 0, spanExpectedOnly: 0, spanActualOnly: 0, spanMatchedCount: 0,
      valueMatchCount: 0, formMatchCount: 0, formBreakdown: {},
      uncoveredIntersection: 0, uncoveredExpectedOnly: 0, uncoveredActualOnly: 0,
    });
  });

  it("2 件を合計する(span の各集合・value・form・uncovered の長さの単純な足し算)", () => {
    const a = compareOf();
    const b = compareOf({
      span: { intersection: [[2, 3], [4, 5]], expectedOnly: [[6, 7]], actualOnly: [] },
      spanMatchedCount: 2, valueMatchCount: 0, formMatchCount: 1,
      formBreakdown: { direct_value: { total: 1, matched: 0 }, aggregate: { total: 1, matched: 1 } },
      uncovered: { intersection: ["u1"], expectedOnly: ["u2", "u3"], actualOnly: [] },
    });
    const totals = sumDecompositionCompare([a, b]);
    expect(totals.spanIntersection).toBe(3); // 1 + 2
    expect(totals.spanExpectedOnly).toBe(1); // 0 + 1
    expect(totals.spanMatchedCount).toBe(3);
    expect(totals.valueMatchCount).toBe(1);
    expect(totals.formMatchCount).toBe(2);
    // form ごとの内訳は複数件をまたいで鍵ごとに加算される(direct_value は a と b の両方から来る)
    expect(totals.formBreakdown).toEqual({
      direct_value: { total: 2, matched: 1 },
      aggregate: { total: 1, matched: 1 },
    });
    expect(totals.uncoveredIntersection).toBe(1);
    expect(totals.uncoveredExpectedOnly).toBe(2);
  });
});
