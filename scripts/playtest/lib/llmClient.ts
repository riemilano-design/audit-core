// 束 R4 ― 3 社の REST を Node の fetch で薄く呼ぶ(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §1・§2・§4)。
//
// 【SDK を足さない】依存 0・鍵の流れが 1 か所・試験で fetch を差し替えて網に出ない。
// 【鍵】引数 deps.apiKey で受け取り、戻り値・例外・ログに含めない(例外の文は redactSecrets を通す)。Gemini は query でなくヘッダで渡す(URL に鍵を載せない)。
// 【構造化】OpenAI = text.format json_schema(strict)/ Gemini = responseSchema / Anthropic = tool_use の input_schema で強制。
//   返った JSON は**必ず正本の検証器で見直す**(呼び出し側)。ここは取り出すだけ。
// 【再試行】429 / 5xx / 接続の失敗は 1・4・16 秒の後に同じ入力で最大 3 回(sleep は差し替え可)。schema 不通過・途中切れの再試行は seatRun の側。
// 【D-2b-1(audit-core/docs/CLAIM_DECOMPOSITION_D2B1_PLAN_2026-10-08.md §3(b))】`AbortSignal.timeout` による
//   中断(`err.name === "TimeoutError"`)は**再送しない**(`LlmTimeoutError` を投げる)。中断の時点で生成は
//   おそらく完了しており課金された可能性が高いので、同じ入力を再送すると同じ仕事に 2 回払うことになる。
//   2026-10-07 の実測では 1 本につき最大 4 回ぶんがこちら側の費用の数え上げに乗らないまま課金され得た。
//   429 / 5xx / それ以外の接続エラーは今のまま再送する(挙動は変えない)。
import { redactSecrets } from "./env.js";

export type Provider = "openai" | "gemini" | "anthropic";
/**
 * その社に `temperature` を送るか。**いまは 3 社とも送らない**(2026-09-30 の初回の実行で実測):
 * claude-opus-5 は `temperature is deprecated for this model`、gpt-5.5 は `Unsupported parameter: 'temperature'` で 400。
 * 受け付ける Gemini だけに送ると**席の条件が非対称になり、一致・不一致を実力差として読めなくなる**
 * (司令塔の対称性の線 2026-09-30。value の形をそろえるのと同じ理由)。
 * 送らなかったことは記録に残す(`run_summary` の `temperatureSent`)― 「温度 0 で回した」と読ませない。
 */
export const SENDS_TEMPERATURE: Readonly<Record<Provider, boolean>> = { openai: false, gemini: false, anthropic: false };
export type FinishReason = "stop" | "length" | "other";

export interface StructuredRequest {
  provider: Provider;
  model: string;
  system: string;
  user: string;
  /** 正本の schema をその社向けに写したもの(schemaAdapters) */
  schema: Record<string, unknown>;
  schemaName: string;
  maxOutputTokens: number;
  temperature?: number;
  seed?: number;
}

export interface StructuredResponse {
  text: string;
  json: unknown;
  /** 応答の全 JSON(原文として保存する) */
  raw: unknown;
  usage: { inputTokens: number; outputTokens: number };
  finishReason: FinishReason;
  finishReasonRaw: string;
  modelVersion?: string;
  requestId?: string;
  fingerprint?: string;
  httpStatus: number;
  attempts: number;
}

export interface ClientDeps {
  fetch: typeof fetch;
  apiKey: string;
  baseUrl?: string;
  sleep?: (ms: number) => Promise<void>;
  maxRetries?: number;
  /** 試験用の上書き(既定は HTTP_ATTEMPT_TIMEOUT_MS)。S-5 §2.1(f) */
  attemptTimeoutMs?: number;
}

/**
 * `AbortSignal.timeout` による中断(D-2b-1 §3(b))。**再送しない** ― 中断の時点で生成はおそらく完了して
 * 課金された可能性が高く、再送は同じ仕事に 2 回払うことになる。429/5xx/それ以外の接続エラー(`LlmHttpError`
 * や通常の network error)とは別の型にして、呼び出し側(`seatRun.ts`)が中断だったことを区別できるようにする。
 */
export class LlmTimeoutError extends Error {
  readonly attemptTimeoutMs: number;
  constructor(attemptTimeoutMs: number) {
    super(`fetch が ${attemptTimeoutMs}ms で中断した(AbortSignal.timeout ― TimeoutError)。生成はおそらく完了して課金された可能性が高いので、同じ入力を再送しない`);
    this.name = "LlmTimeoutError";
    this.attemptTimeoutMs = attemptTimeoutMs;
  }
}

export class LlmHttpError extends Error {
  readonly status: number;
  readonly bodyText: string;
  /** 何回 HTTP を叩いた後の失敗か(再送を含む。記録に残す) */
  readonly attempts: number;
  constructor(status: number, bodyText: string, attempts = 1) {
    super(`HTTP ${status}: ${bodyText.slice(0, 300)}`);
    this.name = "LlmHttpError";
    this.status = status;
    this.bodyText = bodyText;
    this.attempts = attempts;
  }
}

const BACKOFF_MS = [1000, 4000, 16000] as const;
/** S-5 §2.1(f)。1 試行(1 回の fetch)にかける所要の上限 = 5 分。時間切れは「接続の失敗」と同じ扱い(再送)。 */
export const HTTP_ATTEMPT_TIMEOUT_MS = 300_000;
const DEFAULT_BASE: Record<Provider, string> = {
  openai: "https://api.openai.com",
  gemini: "https://generativelanguage.googleapis.com",
  anthropic: "https://api.anthropic.com",
};

function isRetryable(status: number): boolean {
  return status === 429 || status >= 500;
}

/** 同じ入力での再送(429 / 5xx / 接続)。それ以外の HTTP の失敗はそのまま投げる */
async function fetchWithRetry(deps: ClientDeps, url: string, init: RequestInit): Promise<{ status: number; body: unknown; attempts: number }> {
  const sleep = deps.sleep ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
  const maxRetries = deps.maxRetries ?? BACKOFF_MS.length;
  const attemptTimeoutMs = deps.attemptTimeoutMs ?? HTTP_ATTEMPT_TIMEOUT_MS;
  let attempt = 0;
  for (;;) {
    attempt += 1;
    let res: Response | undefined;
    let networkError: string | undefined;
    try {
      res = await deps.fetch(url, { ...init, signal: AbortSignal.timeout(attemptTimeoutMs) });
    } catch (err) {
      // 中断(タイムアウト)は他の接続失敗と見分け、再送せずに投げる(D-2b-1 §3(b)。上のファイル冒頭コメント参照)。
      // 実測(2026-10-08): Node の `AbortSignal.timeout` による中断は `err.name === "TimeoutError"`
      // (`DOMException`)で、`"AbortError"` ではない ― それ以外の中断・接続失敗は今のまま再送する。
      if ((err as Error).name === "TimeoutError") throw new LlmTimeoutError(attemptTimeoutMs);
      networkError = redactSecrets((err as Error).message, [deps.apiKey]);
    }
    if (res !== undefined && !isRetryable(res.status)) {
      const text = await res.text();
      if (!res.ok) throw new LlmHttpError(res.status, redactSecrets(text, [deps.apiKey]), attempt);
      return { status: res.status, body: JSON.parse(text) as unknown, attempts: attempt };
    }
    const status = res?.status ?? 0;
    const bodyText = res === undefined ? (networkError ?? "network") : redactSecrets(await res.text(), [deps.apiKey]);
    if (attempt > maxRetries) throw new LlmHttpError(status, `再送 ${maxRetries} 回の後も失敗: ${bodyText}`, attempt);
    await sleep(BACKOFF_MS[Math.min(attempt - 1, BACKOFF_MS.length - 1)]!);
  }
}

function headersOf(provider: Provider, apiKey: string): Record<string, string> {
  switch (provider) {
    case "openai":
      return { "content-type": "application/json", authorization: `Bearer ${apiKey}` };
    case "gemini":
      return { "content-type": "application/json", "x-goog-api-key": apiKey };
    case "anthropic":
      return { "content-type": "application/json", "x-api-key": apiKey, "anthropic-version": "2023-06-01" };
  }
}

function urlOf(provider: Provider, base: string, model: string, kind: "generate" | "count"): string {
  switch (provider) {
    case "openai":
      return `${base}/v1/responses`;
    case "gemini":
      return `${base}/v1beta/models/${encodeURIComponent(model)}:${kind === "generate" ? "generateContent" : "countTokens"}`;
    case "anthropic":
      return `${base}/v1/messages${kind === "generate" ? "" : "/count_tokens"}`;
  }
}

function bodyOf(req: StructuredRequest): Record<string, unknown> {
  switch (req.provider) {
    case "openai": {
      const body: Record<string, unknown> = {
        model: req.model,
        input: [{ role: "system", content: req.system }, { role: "user", content: req.user }],
        text: { format: { type: "json_schema", name: req.schemaName, schema: req.schema, strict: true } },
        max_output_tokens: req.maxOutputTokens,
      };
      if (req.temperature !== undefined && SENDS_TEMPERATURE.openai) body.temperature = req.temperature;
      if (req.seed !== undefined) body.seed = req.seed;
      return body;
    }
    case "gemini": {
      const generationConfig: Record<string, unknown> = { maxOutputTokens: req.maxOutputTokens, responseMimeType: "application/json", responseSchema: req.schema };
      if (req.temperature !== undefined && SENDS_TEMPERATURE.gemini) generationConfig.temperature = req.temperature;
      return { systemInstruction: { parts: [{ text: req.system }] }, contents: [{ role: "user", parts: [{ text: req.user }] }], generationConfig };
    }
    case "anthropic": {
      const body: Record<string, unknown> = {
        model: req.model,
        max_tokens: req.maxOutputTokens,
        system: req.system,
        messages: [{ role: "user", content: req.user }],
        tools: [{ name: req.schemaName, description: "この形で答えを出す(欄の意味は指示文)", input_schema: req.schema }],
        tool_choice: { type: "tool", name: req.schemaName },
      };
      // temperature は送らない(SENDS_TEMPERATURE.anthropic = false)
      return body;
    }
  }
}

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}
function asArray(x: unknown): unknown[] {
  return Array.isArray(x) ? x : [];
}

/** 3 社の応答から本文・JSON・usage・終わり方を取り出す(形は各社の公開 API の応答) */
export function parseStructuredResponse(provider: Provider, schemaName: string, body: unknown): Omit<StructuredResponse, "httpStatus" | "attempts"> {
  const b = isRecord(body) ? body : {};
  switch (provider) {
    case "openai": {
      let text = "";
      for (const item of asArray(b.output) as Rec[]) {
        if (item.type !== "message") continue;
        for (const part of asArray(item.content) as Rec[]) if (part.type === "output_text" && typeof part.text === "string") text += part.text;
      }
      const usage = isRecord(b.usage) ? b.usage : {};
      const incomplete = isRecord(b.incomplete_details) ? String(b.incomplete_details.reason ?? "") : "";
      const finishRaw = b.status === "incomplete" ? incomplete || "incomplete" : String(b.status ?? "completed");
      return {
        text, json: tryParse(text), raw: body,
        usage: { inputTokens: Number(usage.input_tokens ?? 0), outputTokens: Number(usage.output_tokens ?? 0) },
        finishReason: finishRaw === "max_output_tokens" ? "length" : finishRaw === "completed" ? "stop" : "other",
        finishReasonRaw: finishRaw,
        ...(typeof b.model === "string" ? { modelVersion: b.model } : {}),
        ...(typeof b.id === "string" ? { requestId: b.id } : {}),
        ...(typeof b.system_fingerprint === "string" ? { fingerprint: b.system_fingerprint } : {}),
      };
    }
    case "gemini": {
      const cand = (asArray(b.candidates)[0] ?? {}) as Rec;
      const content = isRecord(cand.content) ? cand.content : {};
      let text = "";
      for (const part of asArray(content.parts) as Rec[]) if (typeof part.text === "string") text += part.text;
      const usage = isRecord(b.usageMetadata) ? b.usageMetadata : {};
      const finishRaw = String(cand.finishReason ?? "");
      return {
        text, json: tryParse(text), raw: body,
        usage: { inputTokens: Number(usage.promptTokenCount ?? 0), outputTokens: Number(usage.candidatesTokenCount ?? 0) },
        finishReason: finishRaw === "MAX_TOKENS" ? "length" : finishRaw === "STOP" ? "stop" : "other",
        finishReasonRaw: finishRaw,
        ...(typeof b.modelVersion === "string" ? { modelVersion: b.modelVersion } : {}),
        ...(typeof b.responseId === "string" ? { requestId: b.responseId } : {}),
      };
    }
    case "anthropic": {
      let json: unknown;
      let text = "";
      for (const block of asArray(b.content) as Rec[]) {
        if (block.type === "tool_use" && block.name === schemaName) { json = block.input; text = JSON.stringify(block.input); }
        else if (block.type === "text" && typeof block.text === "string" && json === undefined) text += block.text;
      }
      if (json === undefined) json = tryParse(text);
      const usage = isRecord(b.usage) ? b.usage : {};
      const finishRaw = String(b.stop_reason ?? "");
      return {
        text, json, raw: body,
        usage: { inputTokens: Number(usage.input_tokens ?? 0), outputTokens: Number(usage.output_tokens ?? 0) },
        finishReason: finishRaw === "max_tokens" ? "length" : finishRaw === "tool_use" || finishRaw === "end_turn" ? "stop" : "other",
        finishReasonRaw: finishRaw,
        ...(typeof b.model === "string" ? { modelVersion: b.model } : {}),
        ...(typeof b.id === "string" ? { requestId: b.id } : {}),
      };
    }
  }
}

function tryParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

export async function callStructured(req: StructuredRequest, deps: ClientDeps): Promise<StructuredResponse> {
  const base = deps.baseUrl ?? DEFAULT_BASE[req.provider];
  const { status, body, attempts } = await fetchWithRetry(deps, urlOf(req.provider, base, req.model, "generate"), {
    method: "POST", headers: headersOf(req.provider, deps.apiKey), body: JSON.stringify(bodyOf(req)),
  });
  return { ...parseStructuredResponse(req.provider, req.schemaName, body), httpStatus: status, attempts };
}

/** 送る前の数え(Anthropic・Gemini は API。OpenAI は API が無いので undefined を返し、呼び出し側が chars/3 にする) */
export async function countTokens(req: Pick<StructuredRequest, "provider" | "model" | "system" | "user">, deps: ClientDeps): Promise<number | undefined> {
  if (req.provider === "openai") return undefined;
  const base = deps.baseUrl ?? DEFAULT_BASE[req.provider];
  const body = req.provider === "anthropic"
    ? { model: req.model, system: req.system, messages: [{ role: "user", content: req.user }] }
    : { contents: [{ role: "user", parts: [{ text: `${req.system}\n\n${req.user}` }] }] };
  const { body: res } = await fetchWithRetry(deps, urlOf(req.provider, base, req.model, "count"), { method: "POST", headers: headersOf(req.provider, deps.apiKey), body: JSON.stringify(body) });
  const r = isRecord(res) ? res : {};
  const n = req.provider === "anthropic" ? r.input_tokens : r.totalTokens;
  return typeof n === "number" ? n : undefined;
}
