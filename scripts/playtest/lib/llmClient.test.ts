// 束 R4 の試験(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §6)。**網に出ない** ― fetch は全部差し替え。
//
// 【要点 1】3 社の応答の形(公開 API の応答を手で写した fixture)から text/json/usage/finishReason を取り出せること。
// 【要点 2】鍵が URL・戻り値・例外の文・投げた error のどこにも出ないこと(鍵を sk-test-… にして全部の字を grep)。
// 【要点 3】429・5xx・接続の失敗は 1・4・16 秒で再送し、4 回目で諦めること(sleep は差し替えて待たない)。
import { describe, expect, it } from "vitest";
import { redactSecrets } from "./env.js";
import { LlmHttpError, callStructured, countTokens, parseStructuredResponse, type ClientDeps, type StructuredRequest } from "./llmClient.js";

const KEY = "sk-test-0123456789abcdefKEYVALUE";
const SCHEMA = { type: "object", properties: { a: { type: "number" } }, required: ["a"], additionalProperties: false } as const;

function req(provider: StructuredRequest["provider"], model = "m-1"): StructuredRequest {
  return { provider, model, system: "指示文", user: "束", schema: { ...SCHEMA }, schemaName: "submit_seat_output", maxOutputTokens: 30000, temperature: 0, seed: 7 };
}

interface Call { url: string; init: RequestInit }
function fakeFetch(responses: Array<{ status: number; body: unknown } | "network">): { fetch: typeof fetch; calls: Call[] } {
  const calls: Call[] = [];
  let i = 0;
  const fetchImpl = (async (url: string, init: RequestInit) => {
    calls.push({ url: String(url), init });
    const r = responses[Math.min(i++, responses.length - 1)]!;
    if (r === "network") throw new Error(`connect ECONNREFUSED (key ${KEY})`);
    const text = typeof r.body === "string" ? r.body : JSON.stringify(r.body);
    return { status: r.status, ok: r.status < 400, text: async () => text } as unknown as Response;
  }) as unknown as typeof fetch;
  return { fetch: fetchImpl, calls };
}
function deps(fetchImpl: typeof fetch, sleeps: number[] = []): ClientDeps {
  return { fetch: fetchImpl, apiKey: KEY, sleep: async (ms: number) => { sleeps.push(ms); } };
}

// ---- 3 社の応答の fixture(公開 API の応答の形を手で写した) ----
const OPENAI_OK = { id: "resp_abc123", model: "gpt-x-2026-09", status: "completed", system_fingerprint: "fp_44", output: [{ type: "reasoning", summary: [] }, { type: "message", content: [{ type: "output_text", text: '{"a":1}' }] }], usage: { input_tokens: 70649, output_tokens: 4210 } };
const OPENAI_CUT = { id: "resp_cut", model: "gpt-x-2026-09", status: "incomplete", incomplete_details: { reason: "max_output_tokens" }, output: [{ type: "message", content: [{ type: "output_text", text: '{"a":1' }] }], usage: { input_tokens: 70649, output_tokens: 30000 } };
const GEMINI_OK = { candidates: [{ content: { parts: [{ text: '{"a":2}' }], role: "model" }, finishReason: "STOP" }], usageMetadata: { promptTokenCount: 70000, candidatesTokenCount: 3000, totalTokenCount: 73000 }, modelVersion: "gemini-x-2026", responseId: "resp_g1" };
const GEMINI_CUT = { candidates: [{ content: { parts: [{ text: '{"a":2' }] }, finishReason: "MAX_TOKENS" }], usageMetadata: { promptTokenCount: 70000, candidatesTokenCount: 30000 }, modelVersion: "gemini-x-2026" };
const ANTHROPIC_OK = { id: "msg_01xyz", model: "claude-opus-5-2026", stop_reason: "tool_use", content: [{ type: "text", text: "考えました" }, { type: "tool_use", id: "toolu_1", name: "submit_seat_output", input: { a: 3 } }], usage: { input_tokens: 71000, output_tokens: 5000 } };
const ANTHROPIC_CUT = { id: "msg_cut", model: "claude-opus-5-2026", stop_reason: "max_tokens", content: [{ type: "text", text: "途中" }], usage: { input_tokens: 71000, output_tokens: 30000 } };

describe("3 社の応答の取り出し", () => {
  it("OpenAI: 本文・JSON・usage・model・fingerprint", () => {
    const r = parseStructuredResponse("openai", "submit_seat_output", OPENAI_OK);
    expect(r.text).toBe('{"a":1}');
    expect(r.json).toEqual({ a: 1 });
    expect(r.usage).toEqual({ inputTokens: 70649, outputTokens: 4210 });
    expect(r.finishReason).toBe("stop");
    expect(r.modelVersion).toBe("gpt-x-2026-09");
    expect(r.requestId).toBe("resp_abc123");
    expect(r.fingerprint).toBe("fp_44");
  });
  it("Gemini: parts の text・usageMetadata・modelVersion", () => {
    const r = parseStructuredResponse("gemini", "submit_seat_output", GEMINI_OK);
    expect(r.json).toEqual({ a: 2 });
    expect(r.usage).toEqual({ inputTokens: 70000, outputTokens: 3000 });
    expect(r.finishReason).toBe("stop");
    expect(r.modelVersion).toBe("gemini-x-2026");
  });
  it("Anthropic: tool_use の input をそのまま JSON にする(text の節は混ぜない)", () => {
    const r = parseStructuredResponse("anthropic", "submit_seat_output", ANTHROPIC_OK);
    expect(r.json).toEqual({ a: 3 });
    expect(r.text).toBe('{"a":3}');
    expect(r.usage).toEqual({ inputTokens: 71000, outputTokens: 5000 });
    expect(r.finishReason).toBe("stop");
    expect(r.modelVersion).toBe("claude-opus-5-2026");
  });
  it("途中で切れたら 3 社とも length(取り置きを増やす合図)", () => {
    expect(parseStructuredResponse("openai", "s", OPENAI_CUT).finishReason).toBe("length");
    expect(parseStructuredResponse("openai", "s", OPENAI_CUT).finishReasonRaw).toBe("max_output_tokens");
    expect(parseStructuredResponse("gemini", "s", GEMINI_CUT).finishReason).toBe("length");
    expect(parseStructuredResponse("anthropic", "s", ANTHROPIC_CUT).finishReason).toBe("length");
    // 切れた JSON は json を作らない(呼び出し側が取り置きを増やして再試行する)
    expect(parseStructuredResponse("openai", "s", OPENAI_CUT).json).toBeUndefined();
  });
  it("知らない終わり方は other(黙って stop にしない)", () => {
    expect(parseStructuredResponse("gemini", "s", { candidates: [{ finishReason: "SAFETY" }] }).finishReason).toBe("other");
    expect(parseStructuredResponse("anthropic", "s", { stop_reason: "refusal", content: [] }).finishReason).toBe("other");
  });
});

describe("入口・ヘッダ・本体", () => {
  it("OpenAI: /v1/responses・Bearer・json_schema strict・temperature と seed", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: OPENAI_OK }]);
    await callStructured(req("openai"), deps(f));
    expect(calls[0]!.url).toBe("https://api.openai.com/v1/responses");
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers.authorization).toBe(`Bearer ${KEY}`);
    const body = JSON.parse(String(calls[0]!.init.body)) as Record<string, any>;
    expect(body.text.format).toMatchObject({ type: "json_schema", name: "submit_seat_output", strict: true });
    expect(body.text.format.schema).toEqual(SCHEMA);
    expect(body.temperature).toBe(0);
    expect(body.seed).toBe(7);
    expect(body.max_output_tokens).toBe(30000);
  });
  it("Gemini: 鍵は URL でなくヘッダ(x-goog-api-key)・responseSchema と responseMimeType", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: GEMINI_OK }]);
    await callStructured(req("gemini", "gemini-x"), deps(f));
    expect(calls[0]!.url).toBe("https://generativelanguage.googleapis.com/v1beta/models/gemini-x:generateContent");
    expect(calls[0]!.url).not.toContain(KEY);
    expect(calls[0]!.url).not.toContain("key=");
    expect((calls[0]!.init.headers as Record<string, string>)["x-goog-api-key"]).toBe(KEY);
    const body = JSON.parse(String(calls[0]!.init.body)) as Record<string, any>;
    expect(body.generationConfig.responseMimeType).toBe("application/json");
    expect(body.generationConfig.responseSchema).toEqual(SCHEMA);
    expect(body.systemInstruction.parts[0].text).toBe("指示文");
  });
  it("Anthropic: x-api-key と版・tool_choice で形を強制", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: ANTHROPIC_OK }]);
    await callStructured(req("anthropic", "claude-opus-5"), deps(f));
    expect(calls[0]!.url).toBe("https://api.anthropic.com/v1/messages");
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers["x-api-key"]).toBe(KEY);
    expect(headers["anthropic-version"]).toBe("2023-06-01");
    const body = JSON.parse(String(calls[0]!.init.body)) as Record<string, any>;
    expect(body.tool_choice).toEqual({ type: "tool", name: "submit_seat_output" });
    expect(body.tools[0].input_schema).toEqual(SCHEMA);
    expect(body.max_tokens).toBe(30000);
  });
  it("temperature を渡さない席には送らない(推論モデルが受け付けないとき)", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: OPENAI_OK }]);
    const r = { ...req("openai") };
    delete r.temperature;
    delete r.seed;
    await callStructured(r, deps(f));
    const body = JSON.parse(String(calls[0]!.init.body)) as Record<string, unknown>;
    expect("temperature" in body).toBe(false);
    expect("seed" in body).toBe(false);
  });
});

describe("再送(1・4・16 秒)", () => {
  it("429 の後に成功 ― 1 秒だけ待ち、attempts は 2", async () => {
    const sleeps: number[] = [];
    const { fetch: f, calls } = fakeFetch([{ status: 429, body: { error: "rate" } }, { status: 200, body: ANTHROPIC_OK }]);
    const r = await callStructured(req("anthropic"), deps(f, sleeps));
    expect(sleeps).toEqual([1000]);
    expect(calls.length).toBe(2);
    expect(r.attempts).toBe(2);
    expect(r.httpStatus).toBe(200);
  });
  it("5xx が続けば 4 回送って諦める(待ちは 1・4・16 秒)", async () => {
    const sleeps: number[] = [];
    const { fetch: f, calls } = fakeFetch([{ status: 503, body: { error: "unavailable" } }]);
    await expect(callStructured(req("gemini"), deps(f, sleeps))).rejects.toThrow(LlmHttpError);
    expect(sleeps).toEqual([1000, 4000, 16000]);
    expect(calls.length).toBe(4);
  });
  it("接続の失敗も再送する", async () => {
    const sleeps: number[] = [];
    const { fetch: f, calls } = fakeFetch(["network", { status: 200, body: OPENAI_OK }]);
    const r = await callStructured(req("openai"), deps(f, sleeps));
    expect(calls.length).toBe(2);
    expect(r.attempts).toBe(2);
  });
  it("400 は再送しない(入力が悪いので同じ入力を送り直さない)", async () => {
    const sleeps: number[] = [];
    const { fetch: f, calls } = fakeFetch([{ status: 400, body: { error: "bad schema" } }]);
    await expect(callStructured(req("openai"), deps(f, sleeps))).rejects.toThrow(/HTTP 400/);
    expect(calls.length).toBe(1);
    expect(sleeps).toEqual([]);
  });
});

describe("鍵が漏れない", () => {
  it("応答の本文に鍵が echo されても、例外の文には出ない", async () => {
    const { fetch: f } = fakeFetch([{ status: 401, body: { error: { message: `invalid api key: ${KEY}` } } }]);
    let caught = "";
    try {
      await callStructured(req("openai"), deps(f));
    } catch (err) {
      caught = `${(err as Error).name} ${(err as Error).message} ${(err as LlmHttpError).bodyText}`;
    }
    expect(caught).toContain("HTTP 401");
    expect(caught).toContain("[redacted]");
    expect(caught).not.toContain(KEY);
  });
  it("接続の失敗の文からも消える", async () => {
    const sleeps: number[] = [];
    const { fetch: f } = fakeFetch(["network"]);
    let caught = "";
    try {
      await callStructured(req("anthropic"), deps(f, sleeps));
    } catch (err) {
      caught = `${(err as Error).message} ${(err as LlmHttpError).bodyText}`;
    }
    expect(caught).not.toContain(KEY);
    expect(caught).toContain("[redacted]");
  });
  it("成功したときの戻り値(raw を含む全文)に鍵が無い", async () => {
    const { fetch: f } = fakeFetch([{ status: 200, body: ANTHROPIC_OK }]);
    const r = await callStructured(req("anthropic"), deps(f));
    expect(JSON.stringify(r)).not.toContain(KEY);
  });
  it("redactSecrets は短すぎる値を消さない(普通の字を壊さない)", () => {
    expect(redactSecrets(`a ${KEY} b`, [KEY])).toBe("a [redacted] b");
    expect(redactSecrets("a 1 b", ["1"])).toBe("a 1 b");
    expect(redactSecrets("そのまま", [undefined])).toBe("そのまま");
  });
});

describe("送る前の数え", () => {
  it("Anthropic は count_tokens の入口を叩いて input_tokens を返す", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: { input_tokens: 71234 } }]);
    const n = await countTokens({ provider: "anthropic", model: "claude-opus-5", system: "指示文", user: "束" }, deps(f));
    expect(n).toBe(71234);
    expect(calls[0]!.url).toBe("https://api.anthropic.com/v1/messages/count_tokens");
  });
  it("Gemini は countTokens の入口で totalTokens", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: { totalTokens: 70650 } }]);
    const n = await countTokens({ provider: "gemini", model: "gemini-x", system: "指示文", user: "束" }, deps(f));
    expect(n).toBe(70650);
    expect(calls[0]!.url).toContain(":countTokens");
    expect(calls[0]!.url).not.toContain(KEY);
  });
  it("OpenAI は入口が無いので undefined を返し、1 回も送らない(呼び出し側が chars/3 にする)", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: {} }]);
    const n = await countTokens({ provider: "openai", model: "m", system: "s", user: "u" }, deps(f));
    expect(n).toBeUndefined();
    expect(calls.length).toBe(0);
  });
});
