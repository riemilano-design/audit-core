// STEP P-47(docs/STEP_P-47_PLAN_2026-09-15.md): scripts/validate-data.mjs の検証器が、プロトタイプの名前
// (constructor・toString・hasOwnProperty・__proto__)の欄を、知らない欄・無い必須の欄として扱うことの試験。
// 手本は scripts/playtest/lib/eventSchema.test.ts の T-1。
//
// validate-data.mjs は関数を export せず、自分の 1 つ上の階層から data/ を探す。そこで一時ディレクトリの根に
// scripts/validate-data.mjs を写し、最小のスキーマと例だけを置いて node で実行する。**共有ツリーの data/ は読まない・書かない。**
// **赤を先に確かめる**: プロトタイプの名前と並べて、ふつうの名前(zzz・name)でも赤になることを見る
// (何も見ない検証器でも緑になる試験にしない)。vitest の形で書く(node:test の形は vitest が拾わない。P-27)。

import { spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const SCRIPT = fileURLToPath(new URL("./validate-data.mjs", import.meta.url));
const NAMES = ["constructor", "toString", "hasOwnProperty", "__proto__"] as const;

/** 例のファイル名に使う(validate-data.mjs は `<type>(.[a-z0-9_]+)*.example.json` だけを拾う)。 */
const fileTag = (name: string) => name.toLowerCase();

/** 一時ディレクトリの根に validate-data.mjs と data/ を作って実行し、終了コード・エラーの行・標準出力を返す。 */
function runValidator(
  schemas: Record<string, object>,
  examples: Record<string, string>,
): { status: number | null; errorLines: string[]; stdout: string } {
  const root = mkdtempSync(path.join(tmpdir(), "p47-validate-data-"));
  try {
    mkdirSync(path.join(root, "scripts"));
    mkdirSync(path.join(root, "data", "schemas"), { recursive: true });
    mkdirSync(path.join(root, "data", "examples"));
    copyFileSync(SCRIPT, path.join(root, "scripts", "validate-data.mjs"));
    for (const [type, schema] of Object.entries(schemas)) {
      writeFileSync(path.join(root, "data", "schemas", `${type}.schema.json`), JSON.stringify(schema));
    }
    // 例は JSON の文字列のまま書く(__proto__ はオブジェクトのリテラルで書くと欄にならず、ファイルと同じ入力にならない)
    for (const [file, text] of Object.entries(examples)) {
      writeFileSync(path.join(root, "data", "examples", file), text);
    }
    const result = spawnSync(process.execPath, [path.join(root, "scripts", "validate-data.mjs")], { encoding: "utf-8" });
    const errorLines = result.stderr
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.startsWith("- "));
    return { status: result.status, errorLines, stdout: result.stdout };
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

const UNKNOWN_FIELD_SCHEMA = {
  type: "object",
  required: ["a"],
  additionalProperties: false,
  properties: { a: { type: "integer" } },
};

describe("validate-data.mjs ― プロトタイプの名前の欄(P-47)", () => {
  it("対照: 正しい例だけなら exit 0(一時ディレクトリの根で検証器が動いていること)", () => {
    const r = runValidator({ unk: UNKNOWN_FIELD_SCHEMA }, { "unk.example.json": '{"a":1}' });
    expect([r.status, r.errorLines]).toEqual([0, []]);
    expect(r.stdout).toContain("検証したファイル: 1件");
  });

  it("知らない欄: ふつうの名前(zzz)と同じく、プロトタイプの名前の欄も赤にする", () => {
    const examples: Record<string, string> = { "unk.zzz.example.json": '{"a":1,"zzz":1}' };
    for (const name of NAMES) examples[`unk.${fileTag(name)}.example.json`] = `{"a":1,"${name}":1}`;
    const r = runValidator({ unk: UNKNOWN_FIELD_SCHEMA }, examples);
    expect(r.status).toBe(1);
    expect(r.errorLines).toContain('- examples/unk.zzz.example.json: unexpected field "zzz" (additionalProperties: false)');
    for (const name of NAMES) {
      expect(r.errorLines, name).toContain(
        `- examples/unk.${fileTag(name)}.example.json: unexpected field "${name}" (additionalProperties: false)`,
      );
    }
    expect(r.errorLines).toHaveLength(1 + NAMES.length); // ほかの誤りを混ぜていない
  });

  it("必須の欄: ふつうの名前(name)と同じく、プロトタイプの名前の必須の欄が無ければ赤にする", () => {
    const schema = { type: "object", required: ["name", ...NAMES], properties: { a: { type: "integer" } } };
    const r = runValidator({ req: schema }, { "req.example.json": '{"a":1}' });
    expect(r.status).toBe(1);
    expect(r.errorLines).toEqual(
      ["name", ...NAMES].map((key) => `- examples/req.example.json: missing required field "${key}"`),
    );
  });
});
