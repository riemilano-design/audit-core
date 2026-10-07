// D-1(audit-core/docs/CLAIM_DECOMPOSITION_D1_PLAN_2026-10-07.md §4)。lib/claimDecomposition.ts を見る。
// **LLM は 1 回も呼ばない。費用 0 円。** 試験の正解は実装が使う表・定数から作らない(手で書いた原文 + 手で
// 数えた期待値)。退化値(空の claims・空の original_text・空の span)も当てる。

import { readdirSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { validate } from "./eventSchema.js";
import { checkClaimDecomposition, coverageReport, decompositionProblems, loadClaimDecompositionSchema } from "./claimDecomposition.js";

describe("claim-decomposition schema v0.1", () => {
  it("この検証器(lib/eventSchema.ts)が扱えるキーワードだけで書かれている(読み込みと照合が例外を投げない)", () => {
    const schema = loadClaimDecompositionSchema();
    const doc = {
      schemaVersion: "0.1",
      original_text: "売上は100億円だった。",
      claims: [
        {
          claim_id: "c1",
          span: [3, 7],
          form: "direct_value",
          subject: "売上",
          value: 100,
          unit: "億円",
          modifiers: { population: null, time_range: null, normalization: null },
          evidence_pointer: null,
        },
      ],
    };
    expect(validate(doc, schema)).toEqual([]);
  });

  it("claim_id が空のとき schema で落ちる(必須の欄は全部埋まっているが minLength で落ちる例)", () => {
    const schema = loadClaimDecompositionSchema();
    const doc = {
      schemaVersion: "0.1",
      original_text: "x",
      claims: [
        {
          claim_id: "",
          span: [0, 1],
          form: "direct_value",
          subject: "s",
          value: "v",
          unit: null,
          modifiers: { population: null, time_range: null, normalization: null },
          evidence_pointer: null,
        },
      ],
    };
    expect(validate(doc, schema).length).toBeGreaterThan(0);
  });

  it("知らない欄が 1 つでもあると落ちる(additionalProperties: false)", () => {
    const schema = loadClaimDecompositionSchema();
    const doc = {
      schemaVersion: "0.1",
      original_text: "x",
      claims: [],
      extra: 1,
    };
    expect(validate(doc, schema).length).toBeGreaterThan(0);
  });

  it("form は CLAIM_CONTRACT_SPEC_v0.2 §2.1 の 4 語(direct_value・derived_value・aggregate・threshold)を全部許す", () => {
    const schema = loadClaimDecompositionSchema();
    for (const form of ["direct_value", "derived_value", "aggregate", "threshold"]) {
      const doc = {
        schemaVersion: "0.1",
        original_text: "x",
        claims: [
          {
            claim_id: "c1",
            span: [0, 1],
            form,
            subject: "s",
            value: 1,
            unit: null,
            modifiers: { population: null, time_range: null, normalization: null },
            evidence_pointer: null,
          },
        ],
      };
      expect(validate(doc, schema)).toEqual([]);
    }
  });

  it("form が 4 語以外(5 番目の語)だと落ちる", () => {
    const schema = loadClaimDecompositionSchema();
    const doc = {
      schemaVersion: "0.1",
      original_text: "x",
      claims: [
        {
          claim_id: "c1",
          span: [0, 1],
          form: "not_a_real_form",
          subject: "s",
          value: 1,
          unit: null,
          modifiers: { population: null, time_range: null, normalization: null },
          evidence_pointer: null,
        },
      ],
    };
    expect(validate(doc, schema).length).toBeGreaterThan(0);
  });
});

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

describe("decompositionProblems", () => {
  it("正しい span は問題無し(0 件)", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "売上は100億円だった。",
      claims: [baseClaim({ span: [3, 6] })], // "100" の 3 文字
    };
    expect(decompositionProblems(doc)).toEqual([]);
  });

  it("退化値: claims が空配列でも問題無し(0 件。空は失敗ではない)", () => {
    const doc = { schemaVersion: "0.1", original_text: "売上は100億円だった。", claims: [] };
    expect(decompositionProblems(doc)).toEqual([]);
  });

  it("退化値: original_text が空文字列で、claims も空なら問題無し", () => {
    const doc = { schemaVersion: "0.1", original_text: "", claims: [] };
    expect(decompositionProblems(doc)).toEqual([]);
  });

  it("退化値: span が [0, 0](空区間)は end<=start で落ちる(original_text は空でも非空でも)", () => {
    const doc1 = { schemaVersion: "0.1", original_text: "", claims: [baseClaim({ span: [0, 0] })] };
    const doc2 = { schemaVersion: "0.1", original_text: "abc", claims: [baseClaim({ span: [0, 0] })] };
    expect(decompositionProblems(doc1).some((m) => m.includes("空か逆転している"))).toBe(true);
    expect(decompositionProblems(doc2).some((m) => m.includes("空か逆転している"))).toBe(true);
  });

  it("span の end が start を下回る(逆転)は問題として出る", () => {
    const doc = { schemaVersion: "0.1", original_text: "abcdef", claims: [baseClaim({ span: [4, 2] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("逆転している"))).toBe(true);
  });

  it("span の end が original_text の長さを超えると問題として出る(索引だけの比較で見つかる)", () => {
    const doc = { schemaVersion: "0.1", original_text: "abc", claims: [baseClaim({ span: [0, 10] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("長さ") && m.includes("超えている"))).toBe(true);
  });

  it("span の start が負だと問題として出る", () => {
    const doc = { schemaVersion: "0.1", original_text: "abc", claims: [baseClaim({ span: [-1, 2] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("start が負"))).toBe(true);
  });

  it("span の要素が整数でない(小数)と問題として出る(型だけの検査では見逃す例)", () => {
    const doc = { schemaVersion: "0.1", original_text: "abcdef", claims: [baseClaim({ span: [1.5, 3] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("整数ではない"))).toBe(true);
  });

  it("span が長さ 2 でない配列は問題として出る(長さ 1)", () => {
    const doc = { schemaVersion: "0.1", original_text: "abc", claims: [baseClaim({ span: [1] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("長さ 2 の配列ではない"))).toBe(true);
  });

  it("span が長さ 2 でない配列は問題として出る(長さ 3)", () => {
    const doc = { schemaVersion: "0.1", original_text: "abcdef", claims: [baseClaim({ span: [1, 2, 3] })] };
    expect(decompositionProblems(doc).some((m) => m.includes("長さ 2 の配列ではない"))).toBe(true);
  });

  it("サロゲートペア(絵文字など)の内側を start/end が指すと問題として出る(索引の数字は範囲内でも内容が割れる例)", () => {
    // "🙂" は UTF-16 で 2 コード単位(サロゲートペア)。"a🙂b" は長さ 4([a][high][low][b])。
    const text = "a🙂b";
    expect(text.length).toBe(4);
    // start=1 はサロゲートペアの内側(high と low の間)を指す ― end=3 なら文字自体は壊れていないが、
    // start=2 なら low サロゲート単体を切り出すことになり壊れる。
    const docStart = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [2, 4] })] };
    expect(decompositionProblems(docStart).some((m) => m.includes("サロゲートペアの中"))).toBe(true);
    const docEnd = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [0, 2] })] };
    expect(decompositionProblems(docEnd).some((m) => m.includes("サロゲートペアの中"))).toBe(true);
    // 境界を割らない span(絵文字を含めて丸ごと、または含めない)は問題無し。
    const docWhole = { schemaVersion: "0.1", original_text: text, claims: [baseClaim({ span: [1, 3] })] };
    expect(decompositionProblems(docWhole)).toEqual([]);
  });

  it("claim_id の重複は問題として出る", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "abcdef",
      claims: [baseClaim({ claim_id: "dup", span: [0, 1] }), baseClaim({ claim_id: "dup", span: [1, 2] })],
    };
    expect(decompositionProblems(doc).some((m) => m.includes('"dup"') && m.includes("重複"))).toBe(true);
  });

  it("claim_id が空文字列は問題として出る", () => {
    const doc = { schemaVersion: "0.1", original_text: "abc", claims: [baseClaim({ claim_id: "" })] };
    expect(decompositionProblems(doc).some((m) => m.includes("claim_id が無い"))).toBe(true);
  });

  it("短絡しない: 2 件の claim がそれぞれ別の問題を持つとき、両方が報告される", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "abcdef",
      claims: [baseClaim({ claim_id: "a", span: [-1, 1] }), baseClaim({ claim_id: "b", span: [0, 100] })],
    };
    const problems = decompositionProblems(doc);
    expect(problems.some((m) => m.startsWith("claims[0]:") && m.includes("start が負"))).toBe(true);
    expect(problems.some((m) => m.startsWith("claims[1]:") && m.includes("超えている"))).toBe(true);
    expect(problems.length).toBe(2);
  });

  it("doc がオブジェクトでないときは問題として出る(落ちない)", () => {
    expect(decompositionProblems(null)).toEqual(["doc がオブジェクトではない"]);
    expect(decompositionProblems("x")).toEqual(["doc がオブジェクトではない"]);
    expect(decompositionProblems([])).toEqual(["doc がオブジェクトではない"]);
  });

  it("original_text が文字列でないときは問題として出る", () => {
    expect(decompositionProblems({ original_text: 1, claims: [] })).toEqual(["original_text が文字列ではない"]);
  });

  it("claims が配列でないときは問題として出る", () => {
    expect(decompositionProblems({ original_text: "x", claims: "not-array" })).toEqual(["claims が配列ではない"]);
  });

  it("claim がオブジェクトでないときは問題として出る(落ちない)", () => {
    const doc = { original_text: "x", claims: [null, 1, "x"] };
    const problems = decompositionProblems(doc);
    expect(problems.length).toBe(3);
    expect(problems.every((m) => m.includes("claim がオブジェクトではない"))).toBe(true);
  });
});

describe("coverageReport", () => {
  it("退化値: original_text が空文字列なら numberSentences は空、bindingRate は 1(空の母集団は失敗ではない)", () => {
    const report = coverageReport({ schemaVersion: "0.1", original_text: "", claims: [] });
    expect(report.numberSentences).toEqual([]);
    expect(report.uncovered).toEqual([]);
    expect(report.bindingRate).toBe(1);
  });

  it("数字の無い文は numberSentences に入らない", () => {
    const report = coverageReport({ schemaVersion: "0.1", original_text: "晴れだった。", claims: [] });
    expect(report.numberSentences).toEqual([]);
  });

  it("数字入りの文が claim で覆われていれば uncovered に入らない(bindingRate 1)", () => {
    const text = "売上は100億円だった。";
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ span: [3, 6] })], // "100" をちょうど覆う
    };
    const report = coverageReport(doc);
    expect(report.numberSentences).toEqual([text]);
    expect(report.uncovered).toEqual([]);
    expect(report.bindingRate).toBe(1);
  });

  it("数字入りの文が claim を 1 つも持たないと uncovered に入る(bindingRate 0)", () => {
    const text = "売上は100億円だった。";
    const doc = { schemaVersion: "0.1", original_text: text, claims: [] };
    const report = coverageReport(doc);
    expect(report.numberSentences).toEqual([text]);
    expect(report.uncovered).toEqual([text]);
    expect(report.bindingRate).toBe(0);
  });

  it("1 文の中に 2 つの数があり、片方だけ覆われている場合もその文は uncovered(部分的な被覆では済まさない)", () => {
    const text = "売上は100億円で、利益は20億円だった。";
    // "100" の位置だけ覆い、"20" は覆わない claim を用意する。
    const idx100 = text.indexOf("100");
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ span: [idx100, idx100 + 3] })],
    };
    const report = coverageReport(doc);
    expect(report.numberSentences).toEqual([text]);
    expect(report.uncovered).toEqual([text]);
    expect(report.bindingRate).toBe(0);
  });

  it("2 文のうち 1 文だけ覆われているとき bindingRate は 0.5", () => {
    const text = "売上は100億円だった。利益は20億円だった。";
    const idx100 = text.indexOf("100");
    const idx20 = text.indexOf("20");
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      // 1 文目の "100" だけ覆う claim を 1 つだけ用意する(2 文目の "20" は覆わない)。
      claims: [baseClaim({ span: [idx100, idx100 + 3] })],
    };
    const report = coverageReport(doc);
    expect(report.numberSentences.length).toBe(2);
    expect(report.uncovered.length).toBe(1);
    expect(report.uncovered[0]).toContain("利益は20億円だった。");
    expect(report.bindingRate).toBe(0.5);
    // 参考までに座標が重ならないことを明示しておく(自明な前提の崩れを検出するため)。
    expect(idx20).toBeGreaterThan(idx100);
  });

  it("全角数字(０-９)の文も numberSentences として検出され、位置が一致していれば覆われる", () => {
    const text = "売上は１００億円だった。";
    const idx = text.indexOf("１");
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [baseClaim({ span: [idx, idx + 3] })],
    };
    const report = coverageReport(doc);
    expect(report.numberSentences).toEqual([text]);
    expect(report.uncovered).toEqual([]);
  });

  it("小数(12.5)を 2 つの別々の claim が整数部・小数部に分けて覆っても、どちらの claim 単独も「12.5」全体を覆っていなければ uncovered(独立監査 REVISE M3 への対応 ― 数の正規表現が小数点を跨いで 1 つの数として扱うことを確かめる試験。これが無いと、数の正規表現を `\\d+(?:\\.\\d+)?` から `\\d+` に壊して小数点を扱えなくしても、既存の 46 本がすべて緑のまま可視化されなかった)", () => {
    const text = "売上は12.5億円だった。";
    const idx = text.indexOf("1");
    expect(text.slice(idx, idx + 4)).toBe("12.5");
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      claims: [
        baseClaim({ claim_id: "c1", span: [idx, idx + 2] }), // "12" だけ(整数部のみ)
        baseClaim({ claim_id: "c2", span: [idx + 3, idx + 4] }), // "5" だけ(小数点を挟んだ別の claim の小数部のみ)
      ],
    };
    const report = coverageReport(doc);
    expect(report.numberSentences).toEqual([text]);
    // "12.5" は 1 つの数として扱われるべきで、整数部と小数部を 2 つの別々の claim が分け合っても、
    // どちらの claim も単独で "12.5" 全体を覆っていない以上、uncovered のまま。
    expect(report.uncovered).toEqual([text]);
    expect(report.bindingRate).toBe(0);
  });

  it("門を通らない span(範囲外)は覆っている扱いにしない(被覆の測定は門を通った span だけを信用する)", () => {
    const text = "売上は100億円だった。";
    const doc = {
      schemaVersion: "0.1",
      original_text: text,
      // end が original_text の長さを超えている(decompositionProblems で問題になる)不正な span。
      claims: [baseClaim({ span: [3, 999] })],
    };
    expect(decompositionProblems(doc).length).toBeGreaterThan(0); // 前提: この span は門で落ちる
    const report = coverageReport(doc);
    expect(report.uncovered).toEqual([text]); // 門を通らない span は被覆として数えない
  });

  it("original_text が文字列でない doc を渡しても落ちない(空の母集団として扱う)", () => {
    const report = coverageReport({ original_text: 123, claims: [] });
    expect(report.numberSentences).toEqual([]);
    expect(report.bindingRate).toBe(1);
  });

  it("claims が配列でない doc を渡しても落ちない(span 無しとして扱う)", () => {
    const text = "売上は100億円だった。";
    const report = coverageReport({ original_text: text, claims: "not-array" });
    expect(report.uncovered).toEqual([text]);
  });
});

describe("checkClaimDecomposition(唯一の入口。schema 照合と decompositionProblems の両方を必ず呼ぶ)", () => {
  it("両方が問題無しのとき、schemaErrors・decompositionProblems・problems が全部空", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "売上は100億円だった。",
      claims: [baseClaim({ span: [3, 6] })], // "100" をちょうど覆う
    };
    const result = checkClaimDecomposition(doc);
    expect(result.schemaErrors).toEqual([]);
    expect(result.decompositionProblems).toEqual([]);
    expect(result.problems).toEqual([]);
  });

  it("schema だけが落とす誤り(form が不正な語)でも、呼び出し元は schema 照合を省略できない ― schemaErrors に出る", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "abc",
      claims: [baseClaim({ form: "not_a_real_form" })],
    };
    const result = checkClaimDecomposition(doc);
    expect(result.schemaErrors.length).toBeGreaterThan(0);
    // decompositionProblems は form を見ないので、ここは問題無し(この doc の span は正しいため)。
    expect(result.decompositionProblems).toEqual([]);
    expect(result.problems.length).toBe(result.schemaErrors.length);
  });

  it("decompositionProblems だけが落とす誤り(span が原文の長さを超える)でも、必ず呼ばれて problems に出る", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "abc",
      claims: [baseClaim({ span: [0, 10] })],
    };
    const result = checkClaimDecomposition(doc);
    // schema は span を「整数 2 個の配列」までしか見ないので、ここは schema だけでは落ちない。
    expect(result.schemaErrors).toEqual([]);
    expect(result.decompositionProblems.length).toBeGreaterThan(0);
    expect(result.problems).toEqual(result.decompositionProblems);
  });

  it("両方に問題があるとき、problems は両方を含む(どちらか一方だけで止めない)", () => {
    const doc = {
      schemaVersion: "0.1",
      original_text: "abc",
      claims: [baseClaim({ form: "not_a_real_form", span: [0, 10] })],
    };
    const result = checkClaimDecomposition(doc);
    expect(result.schemaErrors.length).toBeGreaterThan(0);
    expect(result.decompositionProblems.length).toBeGreaterThan(0);
    expect(result.problems.length).toBe(result.schemaErrors.length + result.decompositionProblems.length);
  });
});

describe("gold_*.json fixtures(独立作成の正解集合。実装側に合わせて書き換えない。glob で全部拾う ― D-2a §1(d))", () => {
  // D-2a 計画(audit-core/docs/CLAIM_DECOMPOSITION_D2A_PLAN_2026-10-07.md §1(d))。
  // gold_02/gold_03/gold_04 を別の独立した席が同時に書いているため、ここでは glob で拾う仕組みだけを作る
  // (1 本も無くても gold_01 だけで動く)。新しい fixture がこの試験に対して落ちるなら、それは発見であり、
  // 試験側を緩めて通す対象ではない。
  const FIXTURES_DIR = new URL("../fixtures/decomposition/", import.meta.url);

  function goldFixtureNames(): string[] {
    return readdirSync(FIXTURES_DIR)
      .filter((name) => /^gold_.*\.json$/.test(name))
      .sort();
  }

  function loadGold(name: string): Record<string, unknown> {
    return JSON.parse(readFileSync(new URL(name, FIXTURES_DIR), "utf-8")) as Record<string, unknown>;
  }

  it("gold_*.json が少なくとも 1 本見つかる(glob が空を拾って静かに 0 件通過しない)", () => {
    expect(goldFixtureNames().length).toBeGreaterThan(0);
  });

  it.each(goldFixtureNames())("%s: expected_claims は schema v0.1 に通り、decompositionProblems も 0 件", (name) => {
    const gold = loadGold(name);
    const doc = {
      schemaVersion: "0.1",
      original_text: gold["original_text"],
      claims: gold["expected_claims"],
    };
    const result = checkClaimDecomposition(doc);
    expect(result.schemaErrors).toEqual([]);
    expect(result.decompositionProblems).toEqual([]);
  });

  it.each(goldFixtureNames())("%s: coverageReport(expected_claims) の uncovered は expected_uncovered_number_sentences と集合として一致する", (name) => {
    const gold = loadGold(name);
    const doc = {
      schemaVersion: "0.1",
      original_text: gold["original_text"],
      claims: gold["expected_claims"],
    };
    const report = coverageReport(doc);

    // splitIntoSentences が句点に続く改行を次の文に含めないよう本番側で直したため、ここでは文字列を
    // 加工しない(trim などで吸収しない)。両辺をそのまま集合として比べる。
    const actual = [...new Set(report.uncovered)].sort();
    const expectedList = gold["expected_uncovered_number_sentences"] as string[];
    const expected = [...new Set(expectedList)].sort();

    // 件数だけでなく中身そのものを比べる(集合として一致するか)。
    expect(actual).toEqual(expected);
    // 重複の同一視で件数が減っていないことの確認(退化防止)。
    expect(actual.length).toBe(expectedList.length);
  });
});
