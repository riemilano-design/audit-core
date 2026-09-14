#!/usr/bin/env node
// data/ 配下のJSONファイルを data/schemas/*.schema.json に照らして検証する。
// 外部ライブラリに依存しない(Node.js標準機能のみ)。理由は docs/TESTING_STRATEGY.md を参照。
//
// 使い方: node scripts/validate-data.mjs
//
// 検証対象:
//   - data/examples/<type>.example.json  (常に存在する想定。IDの相互参照は警告のみ)
//   - data/<type>/*.json                 (Phase1以降に作られる本番データ。IDの相互参照はエラー扱い)

import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { join, basename } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const SCHEMAS_DIR = join(ROOT, "data", "schemas");
const EXAMPLES_DIR = join(ROOT, "data", "examples");
const DATA_DIR = join(ROOT, "data");

const REFERENCE_FIELDS = {
  // フィールド名 -> 参照先の type 名。配列フィールドは values を配列として扱う。
  opening_id: "openings",
  refers_to_shape_id: "shapes",
  refers_to_intent_id: "intents",
  parent_shape_id: "shapes",
  leads_to_shape_ids: "shapes", // 配列
};

function loadJson(path) {
  return JSON.parse(readFileSync(path, "utf-8"));
}

function typeOf(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

function matchesType(value, expected) {
  const actual = typeOf(value);
  if (actual === "number" && expected === "integer") {
    return Number.isInteger(value);
  }
  return actual === expected;
}

// 最小限のJSON Schema(draft-07のサブセット)バリデータ。
// 対応: type, enum, pattern, required, properties, additionalProperties, items, minItems, minimum, maximum
function validateAgainstSchema(instance, schema, pathLabel, errors) {
  if (schema.type) {
    const expectedTypes = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!expectedTypes.some((t) => matchesType(instance, t))) {
      errors.push(`${pathLabel}: type mismatch (expected ${expectedTypes.join("|")}, got ${typeOf(instance)})`);
      return; // 型が違う場合、これ以上の検証は意味が薄いので打ち切る
    }
  }

  if (instance === null) return;

  if (schema.enum && !schema.enum.includes(instance)) {
    errors.push(`${pathLabel}: value "${instance}" not in enum [${schema.enum.join(", ")}]`);
  }

  if (schema.pattern && typeof instance === "string") {
    const re = new RegExp(schema.pattern);
    if (!re.test(instance)) {
      errors.push(`${pathLabel}: "${instance}" does not match pattern ${schema.pattern}`);
    }
  }

  if (typeof instance === "number") {
    if (schema.minimum !== undefined && instance < schema.minimum) {
      errors.push(`${pathLabel}: ${instance} is below minimum ${schema.minimum}`);
    }
    if (schema.maximum !== undefined && instance > schema.maximum) {
      errors.push(`${pathLabel}: ${instance} is above maximum ${schema.maximum}`);
    }
  }

  if (typeOf(instance) === "object") {
    const props = schema.properties || {};
    // プロトタイプを辿らない(STEP P-47): `key in instance`・`key in props`・`props[key]` だと、constructor・toString・
    // hasOwnProperty・__proto__ の名前が Object.prototype に当たり、知らない欄・無い必須の欄を黙って通す。
    for (const key of schema.required || []) {
      if (!Object.hasOwn(instance, key)) {
        errors.push(`${pathLabel}: missing required field "${key}"`);
      }
    }
    for (const [key, value] of Object.entries(instance)) {
      if (schema.additionalProperties === false && !Object.hasOwn(props, key)) {
        errors.push(`${pathLabel}: unexpected field "${key}" (additionalProperties: false)`);
        continue;
      }
      if (Object.hasOwn(props, key)) {
        validateAgainstSchema(value, props[key], `${pathLabel}.${key}`, errors);
      }
    }
  }

  if (typeOf(instance) === "array") {
    if (schema.minItems !== undefined && instance.length < schema.minItems) {
      errors.push(`${pathLabel}: array has ${instance.length} items, minItems is ${schema.minItems}`);
    }
    if (schema.items) {
      instance.forEach((item, i) => {
        validateAgainstSchema(item, schema.items, `${pathLabel}[${i}]`, errors);
      });
    }
  }
}

function collectIds(byType) {
  // byType: { shapes: [instance, ...], openings: [...], ... }
  const ids = {};
  for (const [type, instances] of Object.entries(byType)) {
    ids[type] = new Set(instances.map((i) => i.id).filter(Boolean));
  }
  return ids;
}

function checkReferences(instance, ids, pathLabel, warningsOnly, problems) {
  for (const [field, targetType] of Object.entries(REFERENCE_FIELDS)) {
    if (!(field in instance)) continue;
    const raw = instance[field];
    const values = Array.isArray(raw) ? raw : [raw];
    for (const v of values) {
      if (v === null || v === undefined) continue;
      if (!ids[targetType] || !ids[targetType].has(v)) {
        const msg = `${pathLabel}.${field}: "${v}" は ${targetType} の中に見つかりません`;
        problems.push({ msg, warningsOnly });
      }
    }
  }
}

function main() {
  if (!existsSync(SCHEMAS_DIR)) {
    console.error(`スキーマディレクトリが見つかりません: ${SCHEMAS_DIR}`);
    process.exit(1);
  }

  const schemaFiles = readdirSync(SCHEMAS_DIR).filter((f) => f.endsWith(".schema.json"));
  const schemasByType = {};
  for (const file of schemaFiles) {
    const type = basename(file, ".schema.json");
    schemasByType[type] = loadJson(join(SCHEMAS_DIR, file));
  }

  const errors = [];
  const referenceProblems = [];
  const instancesByType = {};

  for (const type of Object.keys(schemasByType)) {
    instancesByType[type] = [];

    // 1) data/examples/<type>.example.json および data/examples/<type>.<なにか>.example.json
    //    (例: openings.example.json と openings.ibisha.example.json の両方を1つのtypeとして拾う)
    if (existsSync(EXAMPLES_DIR)) {
      const pattern = new RegExp(`^${type}(\\.[a-z0-9_]+)*\\.example\\.json$`);
      for (const file of readdirSync(EXAMPLES_DIR).filter((f) => pattern.test(f))) {
        const examplePath = join(EXAMPLES_DIR, file);
        const instance = loadJson(examplePath);
        validateAgainstSchema(instance, schemasByType[type], `examples/${file}`, errors);
        instancesByType[type].push({ instance, label: `examples/${file}`, warningsOnly: true });
      }
    }

    // 2) data/<type>/*.json (Phase1以降の本番データ)
    const typeDataDir = join(DATA_DIR, type);
    if (existsSync(typeDataDir) && statSync(typeDataDir).isDirectory()) {
      for (const file of readdirSync(typeDataDir).filter((f) => f.endsWith(".json"))) {
        const filePath = join(typeDataDir, file);
        const instance = loadJson(filePath);
        validateAgainstSchema(instance, schemasByType[type], `${type}/${file}`, errors);
        instancesByType[type].push({ instance, label: `${type}/${file}`, warningsOnly: false });
      }
    }
  }

  const idsByType = collectIds(
    Object.fromEntries(Object.entries(instancesByType).map(([t, list]) => [t, list.map((x) => x.instance)]))
  );

  for (const list of Object.values(instancesByType)) {
    for (const { instance, label, warningsOnly } of list) {
      checkReferences(instance, idsByType, label, warningsOnly, referenceProblems);
    }
  }

  console.log(`スキーマ: ${Object.keys(schemasByType).length}件 (${Object.keys(schemasByType).join(", ")})`);
  console.log(`検証したファイル: ${Object.values(instancesByType).reduce((n, l) => n + l.length, 0)}件`);

  if (errors.length > 0) {
    console.error("\n[エラー] スキーマ違反:");
    for (const e of errors) console.error(`  - ${e}`);
  }

  const hardRefProblems = referenceProblems.filter((p) => !p.warningsOnly);
  const softRefProblems = referenceProblems.filter((p) => p.warningsOnly);

  if (softRefProblems.length > 0) {
    console.warn("\n[情報] examples内のID参照未解決(単体のサンプルなので想定内。data/README.md参照):");
    for (const p of softRefProblems) console.warn(`  - ${p.msg}`);
  }

  if (hardRefProblems.length > 0) {
    console.error("\n[エラー] 本番データのID参照が解決できません:");
    for (const p of hardRefProblems) console.error(`  - ${p.msg}`);
  }

  if (errors.length > 0 || hardRefProblems.length > 0) {
    console.error("\n検証NG。上記を修正してください。");
    process.exit(1);
  }

  console.log("\n検証OK。");
}

main();
