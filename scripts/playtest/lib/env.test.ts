// 束 R4 の試験 ― `.env` を読む 1 か所(計画 §8)。**値を返す口は名前で 1 つずつだけ**(dump を持たない)。
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ENV_NAMES, hasEnv, loadDotEnv, readEnv, readEnvNumber, redactSecrets } from "./env.js";

function envFile(body: string): string {
  const dir = mkdtempSync(path.join(tmpdir(), "r4env-"));
  const file = path.join(dir, ".env");
  writeFileSync(file, body, "utf-8");
  return file;
}

describe("loadDotEnv", () => {
  it("KEY=VALUE を読み、# の行と空行を飛ばし、引用符を外す", () => {
    const file = envFile('# コメント\n\nOPENAI_API_KEY=sk-test-abc\nSEAT_GPT_MODEL="gpt-x"\nSEAT_COST_CAP_USD=\'12.5\'\n壊れた行\n');
    const env: NodeJS.ProcessEnv = {};
    const loaded = loadDotEnv(file, env);
    expect(loaded.sort()).toEqual(["OPENAI_API_KEY", "SEAT_COST_CAP_USD", "SEAT_GPT_MODEL"]);
    expect(env.SEAT_GPT_MODEL).toBe("gpt-x");
    expect(readEnvNumber("SEAT_COST_CAP_USD", env)).toBe(12.5);
  });
  it("既に在る名前は上書きしない(実行のときの指定が勝つ)", () => {
    const file = envFile("SEAT_GPT_MODEL=from-file\n");
    const env: NodeJS.ProcessEnv = { SEAT_GPT_MODEL: "from-shell" };
    expect(loadDotEnv(file, env)).toEqual([]);
    expect(env.SEAT_GPT_MODEL).toBe("from-shell");
  });
  it("ファイルが無ければ何もしない(鍵の無い環境でも試験が回る)", () => {
    expect(loadDotEnv(path.join(tmpdir(), "no-such-r4-env"), {})).toEqual([]);
  });
  it("戻り値は名前だけ(値を返さない)", () => {
    const file = envFile("ANTHROPIC_API_KEY=sk-ant-SECRETVALUE123\n");
    const env: NodeJS.ProcessEnv = {};
    const loaded = loadDotEnv(file, env);
    expect(JSON.stringify(loaded)).not.toContain("SECRET");
  });
});

describe("読み出し", () => {
  it("空文字は無いものとして扱う(.env.example の空欄をモデル名にしない)", () => {
    const env: NodeJS.ProcessEnv = { SEAT_GPT_MODEL: "", SEAT_CLAUDE_MODEL: "claude-opus-5" };
    expect(readEnv("SEAT_GPT_MODEL", env)).toBeUndefined();
    expect(hasEnv("SEAT_GPT_MODEL", env)).toBe(false);
    expect(readEnv("SEAT_CLAUDE_MODEL", env)).toBe("claude-opus-5");
    expect(hasEnv("SEAT_CLAUDE_MODEL", env)).toBe(true);
  });
  it("数でない値は undefined(壊れた単価で費用を 0 と見なさない)", () => {
    expect(readEnvNumber("PRICE_GPT_INPUT", { PRICE_GPT_INPUT: "たぶん 3 ドル" })).toBeUndefined();
    expect(readEnvNumber("PRICE_GPT_INPUT", { PRICE_GPT_INPUT: "3" })).toBe(3);
  });
  it("変数の名前の一覧に値が混ざっていない(この module は鍵を持たない)", () => {
    const text = JSON.stringify(ENV_NAMES);
    expect(text).not.toMatch(/sk-|AIza/);
    expect(ENV_NAMES.keys.anthropic).toBe("ANTHROPIC_API_KEY");
    expect(ENV_NAMES.costCap).toBe("SEAT_COST_CAP_USD");
    // 名前は .env の実物と同じでなければ「単価が無い」で止まる(2026-09-30 に実測して合わせた)
    expect(ENV_NAMES.prices.claude).toEqual(["PRICE_CLAUDE_INPUT", "PRICE_CLAUDE_OUTPUT"]);
    expect(ENV_NAMES.priceTiers.gemini).toEqual(["PRICE_GEMINI_TIER_ABOVE_TOKENS", "PRICE_GEMINI_INPUT_HIGH", "PRICE_GEMINI_OUTPUT_HIGH"]);
  });
});

describe("redactSecrets", () => {
  it("同じ鍵が何度出ても全部消える", () => {
    const key = "sk-test-0123456789";
    expect(redactSecrets(`${key} と ${key}`, [key])).toBe("[redacted] と [redacted]");
  });
  it("8 字未満は消さない(普通の字を壊さない)", () => {
    expect(redactSecrets("abc の話", ["abc"])).toBe("abc の話");
  });
});
