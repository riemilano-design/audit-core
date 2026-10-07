// D-2b-0 §2(b)。lib/decompositionCompare.ts を見る。**LLM は 1 回も呼ばない。費用 0 円。**
// 試験の正解は実装の表・定数から作らない(手で書いた原文 + 手で数えた期待値)。退化値(claim 0 件・
// original_text が空・数字の無い文書・span が全部外れる場合)も当てる。

import { describe, expect, it } from "vitest";
import { compareClaimDecomposition } from "./decompositionCompare.js";

function baseClaim(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    claim_id: "c1",
    span: [0, 1],
    form: "direct_value",
    subject: "s",
    value: 1,
    unit: null,
    modifiers: { population: null, time_range: null, normalization: null },
    evidence_pointer: null,
    ...overrides,
  };
}

describe("compareClaimDecomposition", () => {
  it("退化値: 実測・正解とも claim 0 件、original_text も空(span も uncovered も全部空)", () => {
    const actualDoc = { schemaVersion: "0.1", original_text: "", claims: [] };
    const gold = { original_text: "", expected_claims: [], expected_uncovered_number_sentences: [] };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.span).toEqual({ intersection: [], expectedOnly: [], actualOnly: [] });
    expect(result.spanMatchedCount).toBe(0);
    expect(result.valueMatchCount).toBe(0);
    expect(result.formMatchCount).toBe(0);
    expect(result.formBreakdown).toEqual({});
    expect(result.uncovered).toEqual({ intersection: [], expectedOnly: [], actualOnly: [] });
  });

  it("退化値: 正解に claim が無く実測だけに claim がある(数字の無い文書にもかかわらず実測が claim を出す異常系)", () => {
    const text = "晴れだった。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [0, 2] })] };
    const gold = { original_text: text, expected_claims: [], expected_uncovered_number_sentences: [] };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.span.intersection).toEqual([]);
    expect(result.span.expectedOnly).toEqual([]);
    expect(result.span.actualOnly).toEqual([[0, 2]]);
  });

  it("退化値: 正解に claim があり実測に無い(全部 expectedOnly)", () => {
    const text = "売上は100億円だった。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [] };
    const gold = {
      original_text: text,
      expected_claims: [baseClaim({ span: [3, 6], value: 100 })],
      expected_uncovered_number_sentences: [text],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.span.intersection).toEqual([]);
    expect(result.span.expectedOnly).toEqual([[3, 6]]);
    expect(result.span.actualOnly).toEqual([]);
    expect(result.uncovered).toEqual({ intersection: [text], expectedOnly: [], actualOnly: [] });
  });

  it("span は一致するが value が違う場合、spanMatchedCount=1 だが valueMatchCount=0", () => {
    const text = "売上は100億円だった。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [3, 6], value: 999 })] };
    const gold = {
      original_text: text,
      expected_claims: [baseClaim({ span: [3, 6], value: 100 })],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.spanMatchedCount).toBe(1);
    expect(result.valueMatchCount).toBe(0);
    expect(result.formMatchCount).toBe(1); // form は両方 direct_value なので一致
  });

  it("span も value も一致するが form が違う場合、valueMatchCount=1 だが formMatchCount=0", () => {
    const text = "売上は100億円だった。";
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ span: [3, 6], value: 100, form: "aggregate" })],
    };
    const gold = {
      original_text: text,
      expected_claims: [baseClaim({ span: [3, 6], value: 100, form: "direct_value" })],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.spanMatchedCount).toBe(1);
    expect(result.valueMatchCount).toBe(1);
    expect(result.formMatchCount).toBe(0);
    expect(result.formBreakdown).toEqual({ direct_value: { total: 1, matched: 0 } });
  });

  it("span・value・form が全部一致すれば formBreakdown は正解の form をキーに matched=total", () => {
    const text = "売上は100億円だった。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [3, 6], value: 100 })] };
    const gold = {
      original_text: text,
      expected_claims: [baseClaim({ span: [3, 6], value: 100 })],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.formBreakdown).toEqual({ direct_value: { total: 1, matched: 1 } });
  });

  it("同じ span を 2 件の claim が共有する場合(多重集合)、正解 2 件・実測 1 件なら交わり 1・正解のみ 1", () => {
    const text = "abc";
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ claim_id: "a1", span: [0, 1], value: 1 })],
    };
    const gold = {
      original_text: text,
      expected_claims: [
        baseClaim({ claim_id: "g1", span: [0, 1], value: 1 }),
        baseClaim({ claim_id: "g2", span: [0, 1], value: 2 }),
      ],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.span.intersection).toEqual([[0, 1]]);
    expect(result.span.expectedOnly).toEqual([[0, 1]]);
    expect(result.span.actualOnly).toEqual([]);
    // 組になったのは最初に登録された方(g1, value=1)なので value は一致する。
    expect(result.spanMatchedCount).toBe(1);
    expect(result.valueMatchCount).toBe(1);
  });

  it("uncovered の交わり・正解のみ・実測のみが集合として出る(重複は数えない)", () => {
    const text = "晴れだった。雨も降った。";
    // 実測側の claim は 0 件なので、coverageReport(actualDoc) は数字の無い文を uncovered にしない
    // (数字が無い文は numberSentences に入らず uncovered にもならない)。ここでは代わりに数字入りの
    // 文を手で作る。
    const textWithNumbers = "1 手目。2 手目。3 手目。";
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: textWithNumbers,
      claims: [baseClaim({ span: [0, 1], value: 1 })], // "1 手目。" の "1" だけ覆う
    };
    const gold = {
      original_text: textWithNumbers,
      expected_claims: [],
      // 正解は「1 手目。」を覆った想定(=claim があるはず)なので uncovered には入れない。
      // 代わりに他の 2 文 + 正解のみが想定する架空の文を 1 つ混ぜる。
      expected_uncovered_number_sentences: ["2 手目。", "3 手目。", "4 手目。"],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    // 実測の uncovered は coverageReport が計算する: "1 手目。" は覆われるので入らない。"2 手目。"
    // "3 手目。" は claim が無いので uncovered。
    expect(result.uncovered.intersection).toEqual(["2 手目。", "3 手目。"]);
    expect(result.uncovered.expectedOnly).toEqual(["4 手目。"]);
    expect(result.uncovered.actualOnly).toEqual([]);
  });

  it("実測側だけに uncovered な文がある場合(正解は expected_uncovered を空と書いているが実測は覆っていない)", () => {
    const text = "1 手目。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [] }; // 覆っていない
    const gold = {
      original_text: text,
      expected_claims: [baseClaim({ span: [0, 1], value: 1 })], // 正解では「1」が claim で覆われている想定
      expected_uncovered_number_sentences: [], // したがって正解は uncovered を空と書く
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.uncovered.actualOnly).toEqual([text]);
    expect(result.uncovered.expectedOnly).toEqual([]);
    expect(result.uncovered.intersection).toEqual([]);
  });

  it("実測の claims が配列でない・original_text が無い等の壊れた doc でも落ちない(防御的に空扱い)", () => {
    const gold = { original_text: "x", expected_claims: [], expected_uncovered_number_sentences: [] };
    const result = compareClaimDecomposition({ not_a_valid: "doc" }, gold);
    expect(result.span).toEqual({ intersection: [], expectedOnly: [], actualOnly: [] });
    expect(result.uncovered.actualOnly).toEqual([]); // original_text が無い実測は coverageReport 的に空の母集団
  });
});
