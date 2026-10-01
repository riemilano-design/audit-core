// STEP JSON v0(docs/STEP_JSON-V0_PLAN_2026-09-15.md 4. の J-7)。JSON Schema の小さな部分集合の検証器。
//
// 【外部ライブラリを使わない】scripts/validate-data.mjs と同じ方針(docs/TESTING_STRATEGY.md)。validate-data.mjs が
// 扱うキーワード(type・enum・pattern・minimum・maximum・properties・required・additionalProperties・minItems・items)に、
// 判別ユニオンを書くための oneOf と const だけを足した。ajv は 1.0 のときに改めて判断する(計画 9.)。
//
// 【知らないキーワードは例外にする】スキーマの綴り違い(requried など)や、この検証器が扱わないキーワード
// ($ref・anyOf・multipleOf など)が、黙って「何も見ない」にならないようにする。
// 【oneOf は「ちょうど 1 つ」】1 つ以上に合えばよい、にすると変種の取り違えを見逃す。
// 【additionalProperties は false だけ】true やスキーマを渡したら例外(使う予定が無い形を黙って受けない)。
// 【プロトタイプを辿らない】properties の引き当てと required は Object.hasOwn で見る。`properties[key]` や `key in instance` だと、
// constructor・toString・__proto__ などの名前の欄が Object.prototype の値に当たり、知らない欄・無い必須の欄を黙って通す(監査 B の必須 1)。
// 【スキーマの形も見る】数でない minimum・文字列の required・配列の properties などを、黙って「何も見ない」「1 文字ずつ見る」にしない(監査 B の任意 d)。

export type JsonSchema = { readonly [keyword: string]: unknown };

/** 検証に使わない注記のキーワード */
const ANNOTATIONS = new Set(["$schema", "$id", "$comment", "title", "description"]);
const KEYWORDS = new Set([
  "type",
  "enum",
  "const",
  "pattern",
  "minimum",
  "maximum",
  "properties",
  "required",
  "additionalProperties",
  "minItems",
  // **文字列の最小の長さ**(2026-10-01)。退化した文字(1 字の `:` など)を入口で落とすために足した
  // ― packet の `provenance` のパスが 1 字でも通り、その束を組むと本文に `- :` の行ができていた
  // (実験席が実物で再現)。**`pattern` だけでは長さを縛れない**(長さを正規表現に混ぜると読めなくなる)。
  "minLength",
  "items",
  "oneOf",
]);

/** スキーマそのものの誤り(知らないキーワード・扱わない形)。値の誤りとは分ける */
export class SchemaKeywordError extends Error {
  override name = "SchemaKeywordError";
}

function typeName(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number" && Number.isInteger(value)) return "integer";
  return typeof value;
}

function matchesType(value: unknown, expected: string, path: string): boolean {
  switch (expected) {
    case "null":
      return value === null;
    case "array":
      return Array.isArray(value);
    case "object":
      return typeof value === "object" && value !== null && !Array.isArray(value);
    case "integer":
      return typeof value === "number" && Number.isInteger(value);
    case "number":
      return typeof value === "number" && Number.isFinite(value);
    case "string":
      return typeof value === "string";
    case "boolean":
      return typeof value === "boolean";
    default:
      throw new SchemaKeywordError(`${path}: 知らない type「${expected}」`);
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 値をスキーマに照らし、誤りを 1 件 1 行で返す(空なら通った)。スキーマの誤りは SchemaKeywordError を投げる。 */
export function validate(instance: unknown, schema: JsonSchema, path = "$"): string[] {
  const errors: string[] = [];
  validateInto(instance, schema, path, errors);
  return errors;
}

function validateInto(instance: unknown, schema: JsonSchema, path: string, errors: string[]): void {
  for (const keyword of Object.keys(schema)) {
    if (!KEYWORDS.has(keyword) && !ANNOTATIONS.has(keyword)) {
      throw new SchemaKeywordError(`${path}: この検証器が扱わないキーワード「${keyword}」`);
    }
  }
  for (const keyword of ["minimum", "maximum", "minItems", "minLength"]) {
    if (schema[keyword] !== undefined && typeof schema[keyword] !== "number") throw new SchemaKeywordError(`${path}: ${keyword} は数でなければならない`);
  }
  if (schema.pattern !== undefined && typeof schema.pattern !== "string") throw new SchemaKeywordError(`${path}: pattern は文字列でなければならない`);
  if (schema.required !== undefined && !(Array.isArray(schema.required) && schema.required.every((key) => typeof key === "string"))) {
    throw new SchemaKeywordError(`${path}: required は文字列の配列でなければならない`);
  }
  if (schema.properties !== undefined && !isPlainObject(schema.properties)) throw new SchemaKeywordError(`${path}: properties はオブジェクトでなければならない`);
  if (schema.items !== undefined && !isPlainObject(schema.items)) throw new SchemaKeywordError(`${path}: items は 1 つのスキーマ(オブジェクト)だけを扱う`);

  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => matchesType(instance, String(type), path))) {
      errors.push(`${path}: 型が ${types.join(" | ")} ではない(${typeName(instance)})`);
      return;
    }
  }

  if (schema.const !== undefined) {
    if (typeof schema.const === "object" && schema.const !== null) {
      throw new SchemaKeywordError(`${path}: const はプリミティブの値だけを扱う`);
    }
    if (instance !== schema.const) errors.push(`${path}: ${JSON.stringify(instance)} は ${JSON.stringify(schema.const)} ではない`);
  }

  if (schema.enum !== undefined) {
    if (!Array.isArray(schema.enum)) throw new SchemaKeywordError(`${path}: enum は配列でなければならない`);
    if (!schema.enum.includes(instance)) errors.push(`${path}: ${JSON.stringify(instance)} は [${schema.enum.join(", ")}] のどれでもない`);
  }

  if (schema.pattern !== undefined && typeof instance === "string") {
    if (!new RegExp(String(schema.pattern)).test(instance)) errors.push(`${path}: "${instance}" は ${String(schema.pattern)} に合わない`);
  }

  // **文字列の長さ**(`pattern` と同じ扱い ― 文字列でないものには当てない)。
  if (typeof schema.minLength === "number" && typeof instance === "string" && instance.length < schema.minLength) {
    errors.push(`${path}: "${instance}" は ${schema.minLength} 文字より短い(${instance.length} 文字)`);
  }

  if (typeof instance === "number") {
    if (typeof schema.minimum === "number" && instance < schema.minimum) errors.push(`${path}: ${instance} は ${schema.minimum} より小さい`);
    if (typeof schema.maximum === "number" && instance > schema.maximum) errors.push(`${path}: ${instance} は ${schema.maximum} より大きい`);
  }

  if (isPlainObject(instance)) {
    const properties = (schema.properties ?? {}) as Record<string, JsonSchema>;
    for (const key of (schema.required ?? []) as string[]) {
      if (!Object.hasOwn(instance, key)) errors.push(`${path}: 必須の欄「${key}」が無い`);
    }
    if (schema.additionalProperties !== undefined && schema.additionalProperties !== false) {
      throw new SchemaKeywordError(`${path}: additionalProperties は false だけを扱う`);
    }
    for (const [key, value] of Object.entries(instance)) {
      const propertySchema = Object.hasOwn(properties, key) ? properties[key] : undefined;
      if (propertySchema !== undefined) validateInto(value, propertySchema, `${path}.${key}`, errors);
      else if (schema.additionalProperties === false) errors.push(`${path}: 知らない欄「${key}」`);
    }
  }

  if (Array.isArray(instance)) {
    if (typeof schema.minItems === "number" && instance.length < schema.minItems) {
      errors.push(`${path}: 要素が ${instance.length} 個で、${schema.minItems} 個に足りない`);
    }
    if (schema.items !== undefined) {
      instance.forEach((item, index) => validateInto(item, schema.items as JsonSchema, `${path}[${index}]`, errors));
    }
  }

  if (schema.oneOf !== undefined) {
    if (!Array.isArray(schema.oneOf)) throw new SchemaKeywordError(`${path}: oneOf は配列でなければならない`);
    const matched = schema.oneOf.filter((branch) => validate(instance, branch as JsonSchema, path).length === 0).length;
    if (matched !== 1) errors.push(`${path}: oneOf の ${matched} 個に合った(ちょうど 1 個でなければならない)`);
  }
}
