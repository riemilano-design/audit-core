// D-2b-0 §2(c)。lib/decompositionBaseline.ts を見る。**LLM は 1 回も呼ばない。費用 0 円。**
// 試験の正解は実装の表・定数から作らない(手で書いた原文 + 手で数えた期待値)。退化値(空文字列・
// 数字の無い文・句点の無い断片・複数の数字を持つ文)も当てる。
//
// span の定義は「文そのものの区間」(司令塔の仕様の誤りの訂正・2026-10-07。lib/decompositionBaseline.ts
// 先頭のコメントを見る)。数字の位置ではない。

import { describe, expect, it } from "vitest";
import { checkClaimDecomposition } from "./claimDecomposition.js";
import { baselineDecompose } from "./decompositionBaseline.js";

describe("baselineDecompose", () => {
  it("退化値: 空文字列には claim が 0 件", () => {
    const doc = baselineDecompose("");
    expect(doc.original_text).toBe("");
    expect(doc.claims).toEqual([]);
  });

  it("退化値: 数字の無い 1 文には claim が 0 件", () => {
    const doc = baselineDecompose("今日は晴れだった。");
    expect(doc.claims).toEqual([]);
  });

  it("退化値: 句点の無い断片(文末に「。」が無い)でも、数字があれば claim になる(span は断片全体)", () => {
    const text = "売上は100億円";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    expect(doc.claims[0]?.span).toEqual([0, text.length]);
    expect(doc.claims[0]?.subject).toBe(text);
    expect(doc.claims[0]?.value).toBe(100);
    expect(doc.claims[0]?.form).toBe("direct_value");
  });

  it("数字が 1 つだけの 1 文は、文全体を span として claim になる(unit・modifiers・evidence_pointer は null)", () => {
    const text = "売上は100億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    const claim = doc.claims[0];
    expect(claim?.span).toEqual([0, text.length]);
    expect(claim?.subject).toBe(text);
    expect(claim?.value).toBe(100);
    expect(claim?.form).toBe("direct_value");
    expect(claim?.unit).toBeNull();
    expect(claim?.modifiers).toEqual({ population: null, time_range: null, normalization: null });
    expect(claim?.evidence_pointer).toBeNull();
  });

  it("1 文に 2 つの数字があっても、最初の数字だけを value にする(span は文全体のまま。2 件目以降は無視する ― 賢くしない)", () => {
    const text = "売上は100億円で、利益は20億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    expect(doc.claims[0]?.span).toEqual([0, text.length]);
    expect(doc.claims[0]?.subject).toBe(text);
    expect(doc.claims[0]?.value).toBe(100);
  });

  it("2 文(片方は数字が無い)では、数字のある文だけ claim になり件数は 1。span はその文自身(直前の文を含まない)", () => {
    const text = "晴れだった。売上は100億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    const sentenceStart = text.indexOf("売上は100億円だった。");
    expect(doc.claims[0]?.span).toEqual([sentenceStart, text.length]);
    expect(doc.claims[0]?.subject).toBe("売上は100億円だった。");
  });

  it("2 文とも数字があれば claim は 2 件、claim_id は c1・c2 の順。span はそれぞれの文全体で重ならない", () => {
    const text = "売上は100億円だった。利益は20億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(2);
    expect(doc.claims.map((c) => c.claim_id)).toEqual(["c1", "c2"]);
    const boundary = text.indexOf("利益");
    expect(doc.claims[0]?.span).toEqual([0, boundary]);
    expect(doc.claims[0]?.subject).toBe(text.slice(0, boundary));
    expect(doc.claims[1]?.span).toEqual([boundary, text.length]);
    expect(doc.claims[1]?.subject).toBe(text.slice(boundary, text.length));
  });

  it("subject の境界は句点を含み、直前の文の文字(句点)を含まない(off-by-one の検出。D-2b-0 実測 §11 の C4)", () => {
    // 句点を直前の文に含めない off-by-one の変異が入ると、この文の subject/span が 1 文字ずれる
    // (直前の文の末尾の「。」を自分の先頭に含むか、自分の末尾の「。」を失うかのどちらかになる)。
    const text = "晴れだった。売上は100億円だった。利益は20億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(2);
    expect(doc.claims[0]?.subject).toBe("売上は100億円だった。");
    expect(doc.claims[0]?.subject.startsWith("。")).toBe(false);
    expect(doc.claims[0]?.subject.endsWith("。")).toBe(true);
    expect(doc.claims[1]?.subject).toBe("利益は20億円だった。");
    expect(doc.claims[1]?.subject.startsWith("。")).toBe(false);
    expect(doc.claims[1]?.subject.endsWith("。")).toBe(true);
    // span もこの境界と一致する(文字列の比較だけでなく索引の比較も行う)。
    const firstStart = text.indexOf("売上");
    const secondStart = text.indexOf("利益");
    expect(doc.claims[0]?.span).toEqual([firstStart, secondStart]);
    expect(doc.claims[1]?.span).toEqual([secondStart, text.length]);
  });

  it("小数(12.5)は 1 つの数として value に拾う(整数部だけに壊れていない。span は文全体)", () => {
    const text = "差は12.5億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    expect(doc.claims[0]?.span).toEqual([0, text.length]);
    expect(doc.claims[0]?.value).toBe(12.5);
  });

  it("全角数字は拾わない(素朴な基準線の既知の限界。賢くしない決定の確認)", () => {
    const text = "売上は１００億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims).toEqual([]);
  });

  it("出力は checkClaimDecomposition(schema + decompositionProblems)を 0 件で通る", () => {
    const text = "売上は100億円だった。利益は20億円だった。";
    const doc = baselineDecompose(text);
    const result = checkClaimDecomposition(doc);
    expect(result.schemaErrors).toEqual([]);
    expect(result.decompositionProblems).toEqual([]);
  });

  it("claim_id は文書内で重複しない(複数文・複数 claim でも一意)", () => {
    const text = "1 局目は 10 手。2 局目は 20 手。3 局目は 30 手。";
    const doc = baselineDecompose(text);
    const ids = doc.claims.map((c) => c.claim_id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("句点の直後の改行は次の文の span に含めない(splitIntoSentences の規約を継承していることの確認)", () => {
    const text = "晴れだった。\n売上は100億円だった。";
    const doc = baselineDecompose(text);
    expect(doc.claims.length).toBe(1);
    expect(doc.claims[0]?.subject).toBe("売上は100億円だった。");
    expect(doc.claims[0]?.subject.startsWith("\n")).toBe(false);
  });
});
