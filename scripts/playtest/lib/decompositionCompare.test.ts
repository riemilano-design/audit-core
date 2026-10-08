// D-2b-0 §2(b)。lib/decompositionCompare.ts を見る。**LLM は 1 回も呼ばない。費用 0 円。**
// 試験の正解は実装の表・定数から作らない(手で書いた原文 + 手で数えた期待値)。退化値(claim 0 件・
// original_text が空・数字の無い文書・span が全部外れる場合)も当てる。

import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  compareClaimDecomposition,
  compareClaimDecompositionBySentence,
  extractWeightedClaims,
  hostSentenceOf,
  matchClaimsBySentence,
  maxWeightBipartiteMatch,
  type ClaimMatchResult,
  type GoldFixtureLike,
  type WeightedClaim,
} from "./decompositionCompare.js";
// S-C 用: `claimDecomposition.ts` の `splitIntoSentences` を直接 import して使う(決-B の契約どおり、
// 文の一覧の作り方は本体実装と完全に同じ関数を使う。別の分割ロジックを試験側で作らない)。
import { splitIntoSentences as splitSentencesForTest } from "./claimDecomposition.js";

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

  // 独立監査(D-2b-0 GO、推奨 2 件)への対応。audit-core/docs/CLAIM_DECOMPOSITION_D2B0_RESULT_2026-10-07.md §4。
  // 監査が当てた 14 本の変異のうち 3 本が黙った(span 側 .sort() 除去・uncovered 側 .sort() 除去・spanKey の
  // 区切り文字除去)。記録済みの数値は汚染していないが、「黙る」=「測っていない」ので試験で留める。
  //
  // 並び順の根拠(コードを読んで確かめた。文書化された契約が無いため、ここで実際の挙動を固定する):
  // - `span.*`(intersection/expectedOnly/actualOnly)は `compareSpansBySort`(span[0] 昇順 → tie は
  //   span[1] 昇順)で明示的に `.sort()` される(decompositionCompare.ts の `intersection.sort(...)` 等)。
  // - `uncovered.*` は引数無しの `.sort()`(文字列の既定の辞書順 = UTF-16 コード単位の昇順)で返る
  //   (`uncoveredIntersection.sort()` 等)。
  it("span の多重集合(intersection/expectedOnly/actualOnly)は、入力順を乱しても span[0] 昇順(tie は span[1] 昇順)で返る", () => {
    // 交わり(両方にある): [1,2] [5,6] [10,11] / 正解のみ: [3,4] [8,9] / 実測のみ: [13,14] [20,21]
    // 入力配列はどれも昇順ではない順番で書く(入力順のまま返しても緑になる試験にしない)。
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: "x",
      claims: [
        baseClaim({ claim_id: "a-f", span: [20, 21], value: "F" }), // 実測のみ
        baseClaim({ claim_id: "a-c", span: [10, 11], value: 1 }), // 交わり
        baseClaim({ claim_id: "a-g", span: [13, 14], value: "G" }), // 実測のみ
        baseClaim({ claim_id: "a-a", span: [1, 2], value: 1 }), // 交わり
        baseClaim({ claim_id: "a-b", span: [5, 6], value: 1 }), // 交わり
      ],
    };
    const gold = {
      original_text: "x",
      expected_claims: [
        baseClaim({ claim_id: "g-c", span: [10, 11], value: 1 }), // 交わり
        baseClaim({ claim_id: "g-a", span: [1, 2], value: 1 }), // 交わり
        baseClaim({ claim_id: "g-e", span: [8, 9], value: "E" }), // 正解のみ
        baseClaim({ claim_id: "g-b", span: [5, 6], value: 1 }), // 交わり
        baseClaim({ claim_id: "g-d", span: [3, 4], value: "D" }), // 正解のみ
      ],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    // 入力順のまま(.sort() 無し)だと [[10,11],[1,2],[5,6]] のような未整列の並びになるはず
    // ―このテストは昇順そのものを固定するので、.sort() が外れれば必ず赤くなる。
    expect(result.span.intersection).toEqual([
      [1, 2],
      [5, 6],
      [10, 11],
    ]);
    expect(result.span.expectedOnly).toEqual([
      [3, 4],
      [8, 9],
    ]);
    expect(result.span.actualOnly).toEqual([
      [13, 14],
      [20, 21],
    ]);
  });

  it("uncovered の集合(intersection/expectedOnly/actualOnly)は、入力順(= 文の出現順)を乱しても文字列の昇順で返る", () => {
    // 原文の文の出現順をあえて数の昇順と不一致にする: 3,1,2,9,0(claims は空なので全部 uncovered)。
    const text = "3 手目。1 手目。2 手目。9 手目。0 手目。";
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [] };
    const gold = {
      original_text: text,
      expected_claims: [],
      // 正解側の配列順も数の昇順と不一致にする: 3,8,1,4(「8 手目。」「4 手目。」は実測に無い正解のみ)。
      expected_uncovered_number_sentences: ["3 手目。", "8 手目。", "1 手目。", "4 手目。"],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    // 交わり: "1 手目。"/"3 手目。" が両方にある → 昇順なら ["1 手目。","3 手目。"]
    // 正解のみ: "4 手目。"/"8 手目。" → 昇順なら ["4 手目。","8 手目。"]
    // 実測のみ: "0 手目。"/"2 手目。"/"9 手目。" → 昇順なら ["0 手目。","2 手目。","9 手目。"]
    // 入力順のまま(.sort() 無し)だとどの配列も上記の昇順とは一致しない並びになる。
    expect(result.uncovered.intersection).toEqual(["1 手目。", "3 手目。"]);
    expect(result.uncovered.expectedOnly).toEqual(["4 手目。", "8 手目。"]);
    expect(result.uncovered.actualOnly).toEqual(["0 手目。", "2 手目。", "9 手目。"]);
  });

  it("spanKey の区切り文字(カンマ)が無いと [1,23] と [12,3] が衝突する ― 区切り文字は別の span として扱うために在る", () => {
    // 区切り文字(カンマ)が無いと `${span[0]}${span[1]}` は両方 \"123\" になり同一の span と誤認される。
    // 区切り文字がある現在の実装では、[1,23] と [12,3] は別の span として扱われる ―
    // すなわち value・form が一致していても「交わり」にはならず、それぞれ expectedOnly / actualOnly になる。
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: "x",
      claims: [baseClaim({ span: [12, 3], value: 1, form: "direct_value" })],
    };
    const gold = {
      original_text: "x",
      expected_claims: [baseClaim({ span: [1, 23], value: 1, form: "direct_value" })],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecomposition(actualDoc, gold);
    expect(result.span.intersection).toEqual([]);
    expect(result.span.expectedOnly).toEqual([[1, 23]]);
    expect(result.span.actualOnly).toEqual([[12, 3]]);
    expect(result.spanMatchedCount).toBe(0);
    expect(result.valueMatchCount).toBe(0);
  });
});

// 封 ③-1(audit-core/docs/COMPARATOR_FIX_PLAN_2026-10-08.md)。決-B/決-C/決-D の新しい関数と、
// 決-E の自己試験 3 本(S-A/S-B/S-C)。既存の `compareClaimDecomposition` には触れない(決-A)。

const FIXTURES_DIR = new URL("../fixtures/decomposition/", import.meta.url);

function goldFixtureNames(): string[] {
  return readdirSync(FIXTURES_DIR)
    .filter((name) => /^gold_.*\.json$/.test(name))
    .sort();
}

function loadGoldFixture(name: string): GoldFixtureLike & { expected_claims: Array<Record<string, unknown>> } {
  const raw = JSON.parse(readFileSync(new URL(name, FIXTURES_DIR), "utf-8")) as Record<string, unknown>;
  return {
    original_text: raw["original_text"] as string,
    expected_claims: raw["expected_claims"] as Array<Record<string, unknown>>,
    expected_uncovered_number_sentences: raw["expected_uncovered_number_sentences"] as string[],
  };
}

/** 固定種の決定的な疑似乱数(Fisher-Yates のためだけに使う。暗号用途ではない)。 */
function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function seededShuffle<T>(arr: readonly T[], seed: number): T[] {
  const out = [...arr];
  const rand = seededRandom(seed);
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    const tmp = out[i] as T;
    out[i] = out[j] as T;
    out[j] = tmp;
  }
  return out;
}

const SHUFFLE_SEED = 20261008;

describe("hostSentenceOf(決-B)", () => {
  const sentences = [
    { start: 0, end: 10 },
    { start: 10, end: 25 },
    { start: 25, end: 40 },
  ];

  it("span が 1 つの文に完全に収まるとき、その文を返す", () => {
    expect(hostSentenceOf(sentences, [12, 20])).toEqual({ start: 10, end: 25 });
  });

  it("span が 2 つの文にまたがるとき、重なりが大きい方の文を返す", () => {
    // [8,16): 文0との重なり=2([8,10))、文1との重なり=6([10,16)) → 文1が勝つ
    expect(hostSentenceOf(sentences, [8, 16])).toEqual({ start: 10, end: 25 });
  });

  it("重なりが同点のとき、start が小さい文を返す", () => {
    // [5,20): 文0との重なり=5([5,10))、文1との重なり=10([10,20))。わざと同点を作るため文を変える。
    const tiedSentences = [
      { start: 0, end: 10 },
      { start: 10, end: 20 },
    ];
    // [5,15): 文0との重なり=5([5,10))、文1との重なり=5([10,15)) → 同点。start が小さい文0を返す。
    expect(hostSentenceOf(tiedSentences, [5, 15])).toEqual({ start: 0, end: 10 });
  });

  it("重なりが 0 以下しか無いとき undefined を返す(span が文の外側・隙間)", () => {
    expect(hostSentenceOf(sentences, [40, 50])).toBeUndefined();
    expect(hostSentenceOf(sentences, [-10, 0])).toBeUndefined();
  });

  it("文の一覧が空のとき undefined を返す", () => {
    expect(hostSentenceOf([], [0, 5])).toBeUndefined();
  });

  it("span の端点が文の端点にちょうど接する(重なり0)場合は undefined", () => {
    // [10,10) は空区間なので全ての文との重なりが 0 以下
    expect(hostSentenceOf(sentences, [10, 10])).toBeUndefined();
  });
});

describe("compareClaimDecompositionBySentence(決-C/決-D) ― 単体試験(退化値を含む)", () => {
  function baseClaim2(overrides: Record<string, unknown> = {}): Record<string, unknown> {
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

  it("退化値: 正解・実測とも claims 0 件(original_text も空)", () => {
    const gold: GoldFixtureLike = { original_text: "", expected_claims: [], expected_uncovered_number_sentences: [] };
    const actualDoc = { schemaVersion: "0.1", original_text: "", claims: [] };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toEqual([]);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.sentenceCorrect).toBe(0);
  });

  it("退化値: claims が 1 件のみ、文も 1 つだけの原文(value・form 一致)", () => {
    const text = "100 円でした。";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ span: [0, 3], value: 100 })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim2({ span: [0, 3], value: 100 })] };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toEqual([{ goldIndex: 0, actualIndex: 0, sameSentence: true, valueMatch: true, formMatch: true }]);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.sentenceCorrect).toBe(1);
  });

  it("退化値: span が原文の全ての文の外側にある claim は、host が無くても value/form が一致すれば対になる(決-F: 文書全体でマッチングする。host 無しは「同じ文」ボーナスが付かないだけ)", () => {
    const text = "1 文目。2 文目。";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ claim_id: "g1", span: [100, 103], value: 1 })], // 文の外
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim2({ claim_id: "a1", span: [200, 203], value: 1 })], // 文の外(別の位置)。value・form は g1 と一致
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    // value(8)+form(4)=12 > 0 なので対になる。host が両方無いので「同じ文」ボーナスは付かず、
    // sameSentence も false(決-I: 双方とも導出文が無い場合は同一と数えない)。
    expect(result.pairs).toEqual([{ goldIndex: 0, actualIndex: 0, sameSentence: false, valueMatch: true, formMatch: true }]);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.sentenceCorrect).toBe(0);
  });

  it("退化値: span が原文の全ての文の外側にある claim どうしで、value も form も不一致なら対にならない(重み 0 の対は作らない ― 決-G)", () => {
    const text = "1 文目。2 文目。";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ claim_id: "g1", span: [100, 103], value: 1, form: "direct_value" })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim2({ claim_id: "a1", span: [200, 203], value: 999, form: "aggregate" })],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toEqual([]);
    expect(result.goldUnmatched).toEqual([0]);
    expect(result.actualUnmatched).toEqual([0]);
    expect(result.sentenceCorrect).toBe(0);
  });

  it("退化値: 同じ span を持つ claim が 3 件以上ある(多重)場合でも、最大マッチングで全件対応が付く", () => {
    const text = "abc";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [
        baseClaim2({ claim_id: "g1", span: [0, 1], value: 1, form: "a" }),
        baseClaim2({ claim_id: "g2", span: [0, 1], value: 2, form: "b" }),
        baseClaim2({ claim_id: "g3", span: [0, 1], value: 3, form: "c" }),
      ],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [
        baseClaim2({ claim_id: "a1", span: [0, 1], value: 2, form: "b" }),
        baseClaim2({ claim_id: "a2", span: [0, 1], value: 1, form: "a" }),
        baseClaim2({ claim_id: "a3", span: [0, 1], value: 3, form: "c" }),
      ],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs.length).toBe(3);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.pairs.every((p) => p.valueMatch && p.formMatch)).toBe(true);
    expect(result.sentenceCorrect).toBe(3);
  });

  it("value が null 同士は一致、null と 0 は不一致(=== による比較を使っている)", () => {
    const text = "x";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ span: [0, 1], value: null, form: "threshold" })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim2({ span: [0, 1], value: 0, form: "threshold" })] };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(1);
    expect(result.pairs[0]?.valueMatch).toBe(false); // null !== 0
    expect(result.pairs[0]?.formMatch).toBe(true);
  });

  it("value が数値 100 と文字列 \"100\" は不一致(=== は型も見る。正規化を足さない)", () => {
    const text = "x";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ span: [0, 1], value: 100, form: "direct_value" })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim2({ span: [0, 1], value: "100", form: "direct_value" })] };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(1);
    expect(result.pairs[0]?.valueMatch).toBe(false);
  });

  it("正解の claim が実測より多い場合、余った正解は goldUnmatched に入る", () => {
    const text = "1 文のみ。";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [
        baseClaim2({ claim_id: "g1", span: [0, 1], value: 1 }),
        baseClaim2({ claim_id: "g2", span: [0, 1], value: 2 }),
      ],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: [baseClaim2({ claim_id: "a1", span: [0, 1], value: 1 })] };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(1);
    expect(result.goldUnmatched).toHaveLength(1);
    expect(result.actualUnmatched).toEqual([]);
  });

  it("実測の claim が正解より多い場合、余った実測は actualUnmatched に入る", () => {
    const text = "1 文のみ。";
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim2({ claim_id: "g1", span: [0, 1], value: 1 })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [
        baseClaim2({ claim_id: "a1", span: [0, 1], value: 1 }),
        baseClaim2({ claim_id: "a2", span: [0, 1], value: 2 }),
      ],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(1);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toHaveLength(1);
  });

  it("pairs は goldIndex 昇順で返る(文の処理順と正準順序がずれる場合がある ― span が長く後の文へ大きく重なる claim と、短い span で先の文に収まる claim を混ぜて作る)", () => {
    // 文A = [0,11)(句点を含む)、文B = [11,52)(句点を含む)。
    const text = "A".repeat(10) + "。" + "B".repeat(40) + "。";
    // m: span[0]=2 なので正準順序では先(goldIndex=0)になるが、span が長く文Bへの重なりの方が大きいため
    // hostSentenceOf は文Bを選ぶ(文Bは処理順では後)。
    // n: span[0]=8 なので正準順序では後(goldIndex=1)になるが、span が短く文Aに完全に収まるため
    // hostSentenceOf は文Aを選ぶ(文Aは処理順では先)。
    // 文の処理順(A→B)でそのまま push すると [goldIndex=1(文Aで作られる), goldIndex=0(文Bで作られる)] の
    // 順になり、goldIndex 昇順にならない ― 最後の並び替えが無いとここで崩れる。
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [
        baseClaim2({ claim_id: "m", span: [2, 47], value: "m-value" }),
        baseClaim2({ claim_id: "n", span: [8, 9], value: "n-value" }),
      ],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [
        baseClaim2({ claim_id: "m-actual", span: [2, 47], value: "m-value" }),
        baseClaim2({ claim_id: "n-actual", span: [8, 9], value: "n-value" }),
      ],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(2);
    expect(result.pairs.map((p) => p.goldIndex)).toEqual([0, 1]);
  });

  it("決-H: 片側 9 件(全探索と貪欲の切り替えが在った旧い閾値 8/9 の境界)でも最適解が求まる(greedyFallbackSentences は削除済み ― 欄が無いことは import 時の型で保証される)", () => {
    const text = "たくさんの数字がある 1 つの文。";
    const goldClaims = [];
    const actualClaims = [];
    for (let i = 0; i < 9; i++) {
      goldClaims.push(baseClaim2({ claim_id: `g${i}`, span: [0, 1], value: i, form: "direct_value" }));
      actualClaims.push(baseClaim2({ claim_id: `a${i}`, span: [0, 1], value: i, form: "direct_value" }));
    }
    const gold: GoldFixtureLike = { original_text: text, expected_claims: goldClaims, expected_uncovered_number_sentences: [] };
    const actualDoc = { schemaVersion: "0.1", original_text: text, claims: actualClaims };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    // value が重複無くそれぞれ一意に一致する組は全部見つかる(切り替えが無くなった今も最適解は変わらない)。
    expect(result.pairs).toHaveLength(9);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.sentenceCorrect).toBe(9);
  });

  it("実測の claims が配列でない壊れた doc でも落ちない(防御的に空扱い)", () => {
    const gold: GoldFixtureLike = {
      original_text: "x",
      expected_claims: [baseClaim2({ span: [0, 1], value: 1 })],
      expected_uncovered_number_sentences: [],
    };
    const result = compareClaimDecompositionBySentence({ not_a_valid: "doc" }, gold);
    expect(result.pairs).toEqual([]);
    expect(result.goldUnmatched).toEqual([0]);
    expect(result.actualUnmatched).toEqual([]);
  });
});

describe("決-E 自己試験の基礎(gold_01..04 を実物として使う。1 回目の差し戻しで S-A/S-B は決-J の新しい材料へ置き換えた)", () => {
  it("gold_*.json が少なくとも 4 本見つかる(glob が空を拾って静かに通過しない)", () => {
    expect(goldFixtureNames().length).toBeGreaterThanOrEqual(4);
  });

  it.each(goldFixtureNames())(
    "恒等(自己比較)の基本性質 %s: expected_claims をそのまま実測として渡すと 1 対 1 完全対応・sentenceCorrect=正解件数・value 全件一致・actualUnmatched が空",
    (name) => {
      const gold = loadGoldFixture(name);
      const actualDoc = { schemaVersion: "0.1", original_text: gold.original_text, claims: gold.expected_claims };
      const result = compareClaimDecompositionBySentence(actualDoc, gold);
      const expectedCount = gold.expected_claims.length;

      expect(result.pairs).toHaveLength(expectedCount);
      expect(result.goldUnmatched).toEqual([]);
      expect(result.actualUnmatched).toEqual([]);
      expect(result.sentenceCorrect).toBe(expectedCount);
      expect(result.pairs.every((p) => p.valueMatch)).toBe(true);
      expect(result.pairs.every((p) => p.sameSentence)).toBe(true);
    },
  );

  it("gold_03 は同じ文に 2 件以上の claim がある本であることの確認(c1/c2 が span [0,50] を共有。S-B の材料として使う前提)", () => {
    const gold = loadGoldFixture("gold_03.json");
    const c1 = gold.expected_claims.find((c) => c["claim_id"] === "c1");
    const c2 = gold.expected_claims.find((c) => c["claim_id"] === "c2");
    expect(c1?.["span"]).toEqual([0, 50]);
    expect(c2?.["span"]).toEqual([0, 50]);
  });

  it.each(goldFixtureNames())(
    "S-C(ずらしても文が変わらない) %s: span を -4/-1/+1/+4 字ずらしても、長さ 8 字以上の claim について選ばれた文が変わらない",
    (name) => {
      const gold = loadGoldFixture(name);
      const sentenceList = splitSentencesForTest(gold.original_text);

      const longClaims = gold.expected_claims.filter((c) => {
        const span = c["span"] as [number, number];
        return span[1] - span[0] >= 8;
      });
      expect(longClaims.length).toBeGreaterThan(0); // この前提が崩れたら試験が何も確かめていないことになる

      for (const claim of longClaims) {
        const span = claim["span"] as [number, number];
        const original = hostSentenceOf(sentenceList, span);
        expect(original).toBeDefined(); // 正解の span は原文の文の中にあるはず
        for (const shift of [-4, -1, 1, 4]) {
          const shifted: [number, number] = [span[0] + shift, span[1] + shift];
          const shiftedHost = hostSentenceOf(sentenceList, shifted);
          expect(shiftedHost?.start).toBe(original?.start);
          expect(shiftedHost?.end).toBe(original?.end);
        }
      }
    },
  );
});

// 決-J(1 回目の差し戻し): S-A は「開始位置が前の文にあり、大部分が次の文にある範囲」を含む
// 合成材料で試す(gold_01..04 には無い。fixture ファイルは 1 バイトも触らない ― ここでコード内に書く)。
//
// 設計メモ(なぜ恒等(self-identity)のまま span も完全に同じにしないか): gold と actual の span が
// 完全に同じだと、`hostSentenceOf(gold.span)` と `hostSentenceOf(actual.span)` は「同じ関数を同じ
// 入力に適用する」だけになり、その関数の定義が壊れていても(壊れていても同じ壊れ方を 2 回するので)
// 両者は常に一致してしまう ― 壊れを検出できない。そこで実測側の span を「正解とは異なるが、真に
// 同じ文(文B)に属する」位置へ少しずらして作る。これにより `sameSentence` の判定が
// `hostSentenceOf` の**具体的な戻り値**(どの文を指すか)に本当に依存するようになり、
// BREAK-1(開始位置で文を決める誤り)を踏むと確実に不一致になる(U-6)。
describe("S-A(決-J): 開始位置が前の文・大部分が次の文にまたがる span を含む合成材料", () => {
  // 文A = [0,20)(「あ」19 字 + 句点)。文B = [20,60)(「い」39 字 + 句点)。
  const sentenceAText = "あ".repeat(19) + "。";
  const sentenceBText = "い".repeat(39) + "。";
  const text = sentenceAText + sentenceBText;

  it("前提: splitIntoSentences がちょうど文A=[0,20)・文B=[20,60)を作る", () => {
    const sentences = splitSentencesForTest(text);
    expect(sentences).toEqual([
      { text: sentenceAText, start: 0, end: 20 },
      { text: sentenceBText, start: 20, end: 60 },
    ]);
  });

  it("正解の claim(span=[17,55), 開始位置は文Aの中・重なりは文Bの方が大きい)の真の host は文B", () => {
    const sentences = splitSentencesForTest(text);
    expect(hostSentenceOf(sentences, [17, 55])).toEqual({ text: sentenceBText, start: 20, end: 60 });
  });

  it("正しい hostSentenceOf のもとでは、ずらした実測 span([25,50), 文Bに完全に収まる)が正解と同じ文に対応付けられ sameSentence=true・sentenceCorrect=1", () => {
    const gold: GoldFixtureLike = {
      original_text: text,
      expected_claims: [baseClaim({ claim_id: "g1", span: [17, 55], value: 42, form: "direct_value" })],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ claim_id: "a1", span: [25, 50], value: 42, form: "direct_value" })],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toEqual([{ goldIndex: 0, actualIndex: 0, sameSentence: true, valueMatch: true, formMatch: true }]);
    expect(result.goldUnmatched).toEqual([]);
    expect(result.actualUnmatched).toEqual([]);
    expect(result.sentenceCorrect).toBe(1);
  });
});

// 決-J: S-B は「並べ直し(正準順序付け)を通さず、対を作る関数(`matchClaimsBySentence`)を直接」試す。
// `compareClaimDecompositionBySentence` を経由しない ― その関数が行う `compareWeightedClaims` による
// 事前の並べ替えに結果の不変性を頼っていないかを確かめる。gold_03(c1/c2 が同じ文 [0,50] を共有)を使う。
describe("S-B(決-J): matchClaimsBySentence を正準順序付けを経ずに直接呼ぶ ― 実測配列の並び順が結果(claim_id の組)を変えない", () => {
  function pairsByClaimId(result: ClaimMatchResult) {
    return result.pairs
      .map((p) => ({ goldClaimId: p.gold.claimId, actualClaimId: p.actual.claimId, valueMatch: p.valueMatch, formMatch: p.formMatch }))
      .sort((a, b) => (a.goldClaimId !== b.goldClaimId ? (a.goldClaimId < b.goldClaimId ? -1 : 1) : a.actualClaimId < b.actualClaimId ? -1 : 1));
  }
  function unmatchedIds(claims: readonly WeightedClaim[]): string[] {
    return claims.map((c) => c.claimId).sort();
  }

  it.each(goldFixtureNames())("%s: 実測配列を種 20261008 でシャッフルして matchClaimsBySentence に直接渡しても、選ばれる対(claim_id の組)・未対応の集合が同一", (name) => {
    const gold = loadGoldFixture(name);
    const sentences = splitSentencesForTest(gold.original_text);
    const goldClaims = extractWeightedClaims({ claims: gold.expected_claims }); // 並べ替えていない、ファイル順そのまま
    const actualUnshuffled = extractWeightedClaims({ claims: gold.expected_claims });
    const actualShuffled = extractWeightedClaims({ claims: seededShuffle(gold.expected_claims, SHUFFLE_SEED) });

    const resultUnshuffled = matchClaimsBySentence(goldClaims, actualUnshuffled, sentences);
    const resultShuffled = matchClaimsBySentence(goldClaims, actualShuffled, sentences);

    expect(pairsByClaimId(resultShuffled)).toEqual(pairsByClaimId(resultUnshuffled));
    expect(unmatchedIds(resultShuffled.goldUnmatched)).toEqual(unmatchedIds(resultUnshuffled.goldUnmatched));
    expect(unmatchedIds(resultShuffled.actualUnmatched)).toEqual(unmatchedIds(resultUnshuffled.actualUnmatched));
  });

  it("同じ文に 2 件以上 claim がある材料(gold_03 の c1/c2)が、少なくとも 1 本の S-B 対象に含まれていることの確認", () => {
    const gold = loadGoldFixture("gold_03.json");
    expect(goldFixtureNames()).toContain("gold_03.json");
    const c1 = gold.expected_claims.find((c) => c["claim_id"] === "c1");
    const c2 = gold.expected_claims.find((c) => c["claim_id"] === "c2");
    expect(c1?.["span"]).toEqual([0, 50]);
    expect(c2?.["span"]).toEqual([0, 50]);
  });

  it("matchClaimsBySentence に渡す実測配列の並び順(ソートしていない生の配列)を素朴に入れ替えた 2 パターンで、総重みが変わらない(退化値: 配列の先頭・末尾を入れ替える)", () => {
    const text = "abc";
    const sentences = splitSentencesForTest("abc。");
    const g1: WeightedClaim = { claimId: "g1", span: [0, 1], value: 1, form: "a" };
    const g2: WeightedClaim = { claimId: "g2", span: [0, 1], value: 2, form: "b" };
    const a1: WeightedClaim = { claimId: "a1", span: [0, 1], value: 1, form: "a" };
    const a2: WeightedClaim = { claimId: "a2", span: [0, 1], value: 2, form: "b" };
    const r1 = matchClaimsBySentence([g1, g2], [a1, a2], sentences);
    const r2 = matchClaimsBySentence([g2, g1], [a2, a1], sentences); // 両方を逆順に
    expect(pairsByClaimId(r1)).toEqual(pairsByClaimId(r2));
    void text;
  });
});

// 決-J: S-D(新規)。ハンガリー法(`maxWeightBipartiteMatch`)の結果が、小さな無作為の例で
// 全探索(この試験の中だけに置く参照実装。本体には置かない)と一致することを 200 例で確かめる。
describe("S-D(決-J): maxWeightBipartiteMatch は小さな例(片側 6 件以下)で全探索と一致する", () => {
  /** S-D 専用の全探索(本体には置かない ― 決-H の指示「全探索は試験の中だけ」)。
   * 重み行列から、総重みが最大になる(部分マッチングも許す)対応付けの総重みを返す。 */
  function exhaustiveMaxWeightMatchTotal(weights: ReadonlyArray<ReadonlyArray<number>>, n: number, m: number): number {
    let best = 0;
    function recurse(i: number, usedMask: number, total: number): void {
      if (total > best) best = total;
      if (i === n) return;
      recurse(i + 1, usedMask, total); // i 行目のgold claimを組ませない
      for (let j = 0; j < m; j++) {
        if ((usedMask & (1 << j)) !== 0) continue;
        const row = weights[i];
        const w = row === undefined ? undefined : row[j];
        if (w === undefined || w <= 0) continue;
        recurse(i + 1, usedMask | (1 << j), total + w);
      }
    }
    recurse(0, 0, 0);
    return best;
  }

  function matchTotalWeight(weights: ReadonlyArray<ReadonlyArray<number>>, n: number, m: number): number {
    const pairs = maxWeightBipartiteMatch(weights, n, m);
    let total = 0;
    for (const [i, j] of pairs) {
      const row = weights[i];
      const w = row === undefined ? undefined : row[j];
      if (w === undefined) throw new Error("S-D: 範囲外の対が返った");
      total += w;
    }
    return total;
  }

  it("種 20261008・200 例・片側 1〜6 件の無作為な重み行列(値は決-G で現れうる 0/1/4/5/8/9/12/13)で、maxWeightBipartiteMatch の合計重みが全探索と一致する", () => {
    const rand = seededRandom(20261008);
    const possibleWeights = [0, 1, 4, 5, 8, 9, 12, 13];
    let checked = 0;
    for (let trial = 0; trial < 200; trial++) {
      const n = 1 + Math.floor(rand() * 6);
      const m = 1 + Math.floor(rand() * 6);
      const weights: number[][] = [];
      for (let i = 0; i < n; i++) {
        const row: number[] = [];
        for (let j = 0; j < m; j++) {
          const idx = Math.floor(rand() * possibleWeights.length);
          row.push(possibleWeights[idx] as number);
        }
        weights.push(row);
      }
      const exhaustive = exhaustiveMaxWeightMatchTotal(weights, n, m);
      const actual = matchTotalWeight(weights, n, m);
      expect(actual).toBe(exhaustive);
      checked += 1;
    }
    expect(checked).toBe(200); // 200 例すべてを確かに回したことの確認(early returnで数が減っていないか)
  });
});

// 独立監査の REVISE(audit-core/docs/COMPARATOR_FIX_PLAN_2026-10-08.md、1 回目の差し戻し後の追記)。
// 監査が当てた 9 本の変異のうち 3 本(M7/M8・M6・M2)が、既存の 51 本の試験を 1 本も赤くせずに
// 通った。原因は共通: 試験が出力の欄(valueMatch/formMatch/pairs の並び)しか見ておらず、
// 「どの対が選ばれたか」を見ていなかったこと。ここから下の 3 本は、選ばれた対そのものが
// 変わることを捕まえる(本体(decompositionCompare.ts)の挙動は変えない。試験を足すだけ)。
describe("封 ③-1 REVISE 対応: 選ばれた対そのものを見る試験(直し1/2/3)", () => {
  it("直し1: pairWeight の value/form の比較が === のままであることを、選ばれた対で確かめる(M7・M8 を捕まえる)", () => {
    // M7(pairWeight 内の g.value === a.value を == に緩める)を捕まえる材料
    // ― 監査の再現材料をそのまま使う: 正解の value は数値 100。
    // A(actualLooseValue): value が文字列 "100"(== なら一致、=== なら不一致)。form は gold と同じ
    //   ("direct_value")なので form 一致(4点)のみ ― === のままなら weight=4。
    // C(actualStrictValue): value が数値 100(=== でも一致、8点)だが form が不一致 ― weight=8。
    // === のままなら C(8点)が選ばれる。== に緩めると A が 4+8=12点になり C(8点)を上回って
    // しまう(選ばれる対が入れ替わる)。
    const goldForValue: WeightedClaim = { claimId: "g-value", span: [0, 1], value: 100, form: "direct_value" };
    const actualLooseValue: WeightedClaim = { claimId: "a-loose-value", span: [0, 1], value: "100", form: "direct_value" };
    const actualStrictValue: WeightedClaim = { claimId: "a-strict-value", span: [0, 1], value: 100, form: "aggregate" };
    const resultValue = matchClaimsBySentence([goldForValue], [actualLooseValue, actualStrictValue], []);
    expect(resultValue.pairs).toHaveLength(1);
    expect(resultValue.pairs[0]?.actual.claimId).toBe("a-strict-value");

    // M8(pairWeight 内の g.form === a.form を == に緩める)を捕まえる材料。
    // 正解の form は文字列 "1"。value はどちらの実測も不一致にして form だけで競わせる。
    // a-loose-form: form が数値 1(== なら "1" と一致、=== なら不一致)。gold と重ならない文
    //   (span=[10,11]、sentenceA の外)にあるため「同じ文」加点も付かない ― === のままなら weight=0。
    // a-no-match: value も form も不一致だが、gold と同じ文(sentenceA、span=[0,1])にあるため
    //   「同じ文」加点(+1)だけ付く ― === のままなら weight=1 でこちらが選ばれる。
    // == に緩めると a-loose-form が 4点になり a-no-match(1点)を上回ってしまう(選ばれる対が入れ替わる)。
    const goldForForm: WeightedClaim = { claimId: "g-form", span: [0, 1], value: "v-gold", form: "1" };
    const actualLooseForm: WeightedClaim = { claimId: "a-loose-form", span: [10, 11], value: "v-other", form: 1 };
    const actualNoMatch: WeightedClaim = { claimId: "a-no-match", span: [0, 1], value: "v-other2", form: "other" };
    const sentenceA = { start: 0, end: 5 };
    const resultForm = matchClaimsBySentence([goldForForm], [actualLooseForm, actualNoMatch], [sentenceA]);
    expect(resultForm.pairs).toHaveLength(1);
    expect(resultForm.pairs[0]?.actual.claimId).toBe("a-no-match");
  });

  it("直し2: pairs は goldIndex 昇順で返る ― 価値が入れ替わって一致する材料(ハンガリー法の列順の出力は goldIndex 降順になる)で並べ替えを確かめる(M6 を捕まえる)", () => {
    // g-low(span[0,1])・g-high(span[5,6])の value を、a-low(span[0,1])・a-high(span[5,6])の
    // value と「入れ替えて」一致させる(g-low は a-high と、g-high は a-low と value が一致する)。
    // 最大重みマッチングは交差した対応(g-low↔a-high, g-high↔a-low)を選ぶ。
    // ハンガリー法の出力は列(actualIndex)昇順なので、内部の対応は
    // (goldIndex=1,actualIndex=0) → (goldIndex=0,actualIndex=1) の順になり、並べ替えが無いと
    // goldIndex は [1,0](降順)のまま返ってしまう。
    const gold: GoldFixtureLike = {
      original_text: "",
      expected_claims: [
        baseClaim({ claim_id: "g-low", span: [0, 1], value: "valB", form: "direct_value" }),
        baseClaim({ claim_id: "g-high", span: [5, 6], value: "valA", form: "direct_value" }),
      ],
      expected_uncovered_number_sentences: [],
    };
    const actualDoc = {
      schemaVersion: "0.1",
      original_text: "",
      claims: [
        baseClaim({ claim_id: "a-low", span: [0, 1], value: "valA", form: "direct_value" }),
        baseClaim({ claim_id: "a-high", span: [5, 6], value: "valB", form: "direct_value" }),
      ],
    };
    const result = compareClaimDecompositionBySentence(actualDoc, gold);
    expect(result.pairs).toHaveLength(2);
    // 並べ替えが働いているので goldIndex は昇順(今回の材料では内部の計算順と逆になる)。
    // 並べ替えを外すと [1, 0] になる(このため actualIndex は昇順ではなく [1, 0] になる)。
    expect(result.pairs.map((p) => p.goldIndex)).toEqual([0, 1]);
    expect(result.pairs.map((p) => p.actualIndex)).toEqual([1, 0]);
  });

  it("直し3: 「同じ文」の加点は value の重みと form の重みの差より必ず小さい ― value 一致・別の文にある対は、form 一致のみ・同じ文にある対に必ず負けない(M2 を捕まえる)", () => {
    // 決-G の人間の条件: 加点(同じ文)は、value と form の重みの差(最小4)より必ず小さい。
    // 数の字面(SAME_SENTENCE_BONUS === 1)ではなく、この条件が実際に効いているかを振る舞いで見る:
    // value だけ一致・別の文にある対(valueMatchOtherSentence)と、form だけ一致・gold と同じ文に
    // ある対(formMatchSameSentence)を同じ gold と競わせ、常に前者が選ばれることを確かめる。
    const sentenceA = { start: 0, end: 5 };
    const sentenceB = { start: 10, end: 15 };
    const gold: WeightedClaim = { claimId: "g", span: [0, 1], value: "valX", form: "formA" };
    const valueMatchOtherSentence: WeightedClaim = { claimId: "v", span: [10, 11], value: "valX", form: "formZ" };
    const formMatchSameSentence: WeightedClaim = { claimId: "f", span: [0, 2], value: "valY", form: "formA" };
    const result = matchClaimsBySentence([gold], [valueMatchOtherSentence, formMatchSameSentence], [sentenceA, sentenceB]);
    expect(result.pairs).toHaveLength(1);
    expect(result.pairs[0]?.actual.claimId).toBe("v");
  });
});
