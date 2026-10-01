// STEP JSON v0 の T-1(docs/STEP_JSON-V0_PLAN_2026-09-15.md 6.2)。検証器そのものの試験。
// **赤を先に確かめる**: 各キーワードで、通る値と通らない値の両方を並べる(通るだけの試験は、何も見ない検証器でも緑になる)。

import { describe, expect, it } from "vitest";
import { SchemaKeywordError, validate, type JsonSchema } from "./eventSchema.js";

const ok = (value: unknown, schema: JsonSchema) => expect(validate(value, schema), JSON.stringify(value)).toEqual([]);
const ng = (value: unknown, schema: JsonSchema) => expect(validate(value, schema), JSON.stringify(value)).not.toEqual([]);

describe("T-1: 検証器(外部ライブラリ無し。計画 J-7)", () => {
  it("type: integer は整数だけ、配列で書けば null も許す", () => {
    ok(1, { type: "integer" });
    ng(1.5, { type: "integer" });
    ng("1", { type: "integer" });
    ng(null, { type: "integer" });
    ok(null, { type: ["integer", "null"] });
    ok(-3, { type: ["integer", "null"] });
    ok(1.5, { type: "number" });
    ng([], { type: "object" });
    ng(null, { type: "object" });
    ok([], { type: "array" });
    ok(false, { type: "boolean" });
    ng(0, { type: "boolean" });
  });

  it("const と enum: 値がちょうど同じときだけ通る", () => {
    ok("measured", { const: "measured" });
    ng("unrecorded", { const: "measured" });
    ok("U-3", { enum: ["U-1", "U-2", "U-3"] });
    ng("U-9", { enum: ["U-1", "U-2", "U-3"] });
  });

  it("pattern・minimum・maximum", () => {
    ok("7g7f", { type: "string", pattern: "^[1-9][a-i][1-9][a-i]$" });
    ng("7g7", { type: "string", pattern: "^[1-9][a-i][1-9][a-i]$" });
    ok(0, { type: "integer", minimum: 0, maximum: 2 });
    ng(-1, { type: "integer", minimum: 0 });
    ng(3, { type: "integer", maximum: 2 });
    ok(null, { type: ["integer", "null"], minimum: 2 }); // null には minimum を当てない
  });

  it("required と additionalProperties: false", () => {
    const schema: JsonSchema = { type: "object", required: ["a"], additionalProperties: false, properties: { a: { type: "integer" }, b: { type: "string" } } };
    ok({ a: 1 }, schema);
    ok({ a: 1, b: "x" }, schema);
    ng({ b: "x" }, schema);
    ng({ a: 1, c: true }, schema);
    ng({ a: "1" }, schema);
  });

  it("プロトタイプの名前の欄も、知らない欄・無い必須の欄として扱う(Object.prototype を辿らない。監査 B の必須 1)", () => {
    const schema: JsonSchema = { type: "object", required: ["a"], additionalProperties: false, properties: { a: { type: "integer" } } };
    for (const name of ["constructor", "toString", "hasOwnProperty", "__proto__"]) {
      // __proto__ はオブジェクトのリテラルで書くと欄にならない(プロトタイプを差し替える)ので、ファイルと同じく JSON.parse で作る
      const value = JSON.parse(`{"a":1,"${name}":1}`) as object;
      expect(Object.keys(value)).toContain(name);
      expect(validate(value, schema), name).toEqual([`$: 知らない欄「${name}」`]);
    }
    expect(validate({}, { type: "object", required: ["toString"] })).toEqual(["$: 必須の欄「toString」が無い"]);
  });

  it("minItems と items(要素ごとに見て、何番目かを書く)", () => {
    const schema: JsonSchema = { type: "array", minItems: 1, items: { type: "integer" } };
    ok([1, 2], schema);
    ng([], schema);
    expect(validate([1, "x"], schema)).toEqual(['$[1]: 型が integer ではない(string)']);
  });

  it("oneOf は「ちょうど 1 つ」: 0 個も 2 個も通らない", () => {
    const overlapping: JsonSchema = { oneOf: [{ type: "integer" }, { type: "integer", minimum: 0 }] };
    ok(-1, overlapping); // 1 つ目だけに合う
    ng(5, overlapping); // 2 つに合う
    ng("x", overlapping); // どれにも合わない
    const variants: JsonSchema = {
      oneOf: [
        { type: "object", required: ["state", "text"], additionalProperties: false, properties: { state: { const: "stated" }, text: { type: "string" } } },
        { type: "object", required: ["state"], additionalProperties: false, properties: { state: { const: "pending" } } },
      ],
    };
    ok({ state: "stated", text: "文" }, variants);
    ok({ state: "pending" }, variants);
    ng({ state: "pending", text: "" }, variants); // 変種に無い欄
    ng({ state: "stated" }, variants); // 変種に要る欄が無い
  });

  it("入れ子の誤りは、欄の道筋つきで出す", () => {
    const schema: JsonSchema = { type: "object", properties: { a: { type: "object", properties: { b: { const: 1 } } } } };
    expect(validate({ a: { b: 2 } }, schema)).toEqual(["$.a.b: 2 は 1 ではない"]);
  });

  it("知らないキーワード・扱わない形はスキーマの誤りとして例外にする(黙って何も見ないにしない)", () => {
    expect(() => validate({}, { requried: ["a"] })).toThrow(SchemaKeywordError);
    expect(() => validate({ a: 1 }, { properties: { a: { multipleOf: 2 } } })).toThrow(SchemaKeywordError);
    expect(() => validate(1, { type: "int" })).toThrow(SchemaKeywordError);
    expect(() => validate({}, { type: "object", additionalProperties: true })).toThrow(SchemaKeywordError);
    expect(() => validate("a", { const: { x: 1 } })).toThrow(SchemaKeywordError);
    expect(() => validate(1, { oneOf: { type: "integer" } })).toThrow(SchemaKeywordError);
    // キーワードの値の形が違うもの(監査 B の任意 d。以前は黙って飛ばす・1 文字ずつ見る、だった)
    expect(() => validate(1, { type: "integer", minimum: "0" })).toThrow(SchemaKeywordError);
    expect(() => validate(1, { type: "integer", maximum: "2" })).toThrow(SchemaKeywordError);
    expect(() => validate([], { type: "array", minItems: "1" })).toThrow(SchemaKeywordError);
    expect(() => validate("a", { type: "string", pattern: 1 })).toThrow(SchemaKeywordError);
    expect(() => validate({}, { type: "object", required: "a" })).toThrow(SchemaKeywordError);
    expect(() => validate({ a: 1 }, { type: "object", properties: [] })).toThrow(SchemaKeywordError);
    expect(() => validate([1], { type: "array", items: [] })).toThrow(SchemaKeywordError);
    // 注記は検証に使わず、例外にもしない
    ok(1, { $schema: "x", $id: "y", $comment: "z", title: "t", description: "d", type: "integer" });
  });
  it("minLength は短い文字列を落とす(退化した文字を入口で止める)", () => {
    // **1 字の `:` が packet の provenance のパスとして通っていた**(2026-10-01。実験席が実物で再現)。
    // その束を組むと本文に `- :` の行ができ、席の到達の照合がその節を素通りしていた。
    const schema = { type: "string", minLength: 3 };
    expect(validate(":", schema)).toHaveLength(1);
    expect(validate(":", schema)[0]).toContain("3 文字より短い");
    expect(validate("ab", schema)).toHaveLength(1);
    // **ちょうど 3 文字は通る**(境目を数で固定する ― `<` と `<=` の取り違えが黙らない)。
    expect(validate("a.b", schema)).toEqual([]);
    expect(validate("docs/README.md", schema)).toEqual([]);
  });

  it("minLength は文字列でないものには当てない(pattern と同じ扱い)", () => {
    // 数や配列に長さを当てると、**型の誤りと長さの誤りが 2 行出る**(同じ 1 つの誤りを 2 回言う)。
    expect(validate(1, { minLength: 3 })).toEqual([]);
    expect(validate([1, 2], { minLength: 3 })).toEqual([]);
    expect(validate(null, { minLength: 3 })).toEqual([]);
  });

  it("minLength が数でなければスキーマの誤り(黙って何も見ないにしない)", () => {
    expect(() => validate("x", { minLength: "3" })).toThrow(SchemaKeywordError);
  });
});
