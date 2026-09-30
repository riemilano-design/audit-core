// 3 席 LLM API の束 R4 ― `.env` を読む場所は**ここ 1 か所**(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §8)。
//
// 【鍵の流れ】`.env`(gitignore、人間が置く)→ process.env → 名前で 1 つずつ読む → 引数で渡す。
//   dump しない・ログに出さない・戻り値に鍵を含めない(hasKey の真偽だけ)。dotenv を足さない(依存 0)。
import { existsSync, readFileSync } from "node:fs";

/** R4 が読む変数の名前(司令塔了承 2026-09-30)。値は人間が .env に置く。ここに値は無い */
export const ENV_NAMES = {
  keys: { openai: "OPENAI_API_KEY", gemini: "GEMINI_API_KEY", anthropic: "ANTHROPIC_API_KEY" },
  models: { gpt: "SEAT_GPT_MODEL", gemini: "SEAT_GEMINI_MODEL", claude: "SEAT_CLAUDE_MODEL" },
  integrator: { provider: "INTEGRATOR_PROVIDER", model: "INTEGRATOR_MODEL" },
  // 単価の名前は**人間・司令塔が置いた .env の実物に合わせた**(2026-09-30 に実測。こちらの案は IN / OUT だったが、置かれていたのは INPUT / OUTPUT)
  prices: { gpt: ["PRICE_GPT_INPUT", "PRICE_GPT_OUTPUT"], gemini: ["PRICE_GEMINI_INPUT", "PRICE_GEMINI_OUTPUT"], claude: ["PRICE_CLAUDE_INPUT", "PRICE_CLAUDE_OUTPUT"] },
  /**
   * 入力が大きいと単価が上がる社の上の段(2026-09-30 司令塔): 閾値を**超えたら**高い単価で見積もる。
   * 置かれていなければ段なし(1 つの単価)として扱う ― 安い方に倒さないため、段が在る社は必ず 3 つ揃えて置く。
   */
  priceTiers: { gemini: ["PRICE_GEMINI_TIER_ABOVE_TOKENS", "PRICE_GEMINI_INPUT_HIGH", "PRICE_GEMINI_OUTPUT_HIGH"] },
  inputLimits: { gpt: "SEAT_GPT_INPUT_LIMIT", gemini: "SEAT_GEMINI_INPUT_LIMIT", claude: "SEAT_CLAUDE_INPUT_LIMIT" },
  costCap: "SEAT_COST_CAP_USD",
} as const;

/**
 * 最小の .env 読み(`KEY=VALUE`、`#` の行は無視、両端の引用符は外す)。**既に process.env に在る名前は上書きしない**。
 * 読んだ名前の一覧だけ返す(値は返さない)。
 */
export function loadDotEnv(path: string, env: NodeJS.ProcessEnv = process.env): string[] {
  if (!existsSync(path)) return [];
  const loaded: string[] = [];
  for (const rawLine of readFileSync(path, "utf-8").split("\n")) {
    const line = rawLine.trim();
    if (line.length === 0 || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq <= 0) continue;
    const name = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    if (env[name] === undefined) {
      env[name] = value;
      loaded.push(name);
    }
  }
  return loaded;
}

/** 名前で 1 つ読む(無ければ undefined。値をログに出す口は持たない) */
export function readEnv(name: string, env: NodeJS.ProcessEnv = process.env): string | undefined {
  const value = env[name];
  return value === undefined || value.length === 0 ? undefined : value;
}

export function readEnvNumber(name: string, env: NodeJS.ProcessEnv = process.env): number | undefined {
  const value = readEnv(name, env);
  if (value === undefined) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

/** 鍵の有無だけ(値は返さない) */
export function hasEnv(name: string, env: NodeJS.ProcessEnv = process.env): boolean {
  return readEnv(name, env) !== undefined;
}

/** 文字列から鍵の値を消す(例外の文・ログに鍵が乗らないための最後の網) */
export function redactSecrets(text: string, secrets: readonly (string | undefined)[]): string {
  let out = text;
  for (const s of secrets) if (s !== undefined && s.length >= 8) out = out.split(s).join("[redacted]");
  return out;
}
