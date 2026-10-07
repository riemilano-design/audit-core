// 束 R4 の試験(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §6)。**網に出ない** ― fetch は全部差し替え。
//
// 【要点 1】3 社の応答の形(公開 API の応答を手で写した fixture)から text/json/usage/finishReason を取り出せること。
// 【要点 2】鍵が URL・戻り値・例外の文・投げた error のどこにも出ないこと(鍵を sk-test-… にして全部の字を grep)。
// 【要点 3】429・5xx・接続の失敗は 1・4・16 秒で再送し、4 回目で諦めること(sleep は差し替えて待たない)。
import { describe, expect, it } from "vitest";
import { redactSecrets } from "./env.js";
import { HTTP_ATTEMPT_TIMEOUT_MS, LlmHttpError, LlmTimeoutError, SENDS_TEMPERATURE, callStructured, countTokens, parseStructuredResponse, type ClientDeps, type StructuredRequest } from "./llmClient.js";

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
  it("OpenAI: /v1/responses・Bearer・json_schema strict・seed(temperature は送らない)", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: OPENAI_OK }]);
    await callStructured(req("openai"), deps(f));
    expect(calls[0]!.url).toBe("https://api.openai.com/v1/responses");
    const headers = calls[0]!.init.headers as Record<string, string>;
    expect(headers.authorization).toBe(`Bearer ${KEY}`);
    const body = JSON.parse(String(calls[0]!.init.body)) as Record<string, any>;
    expect(body.text.format).toMatchObject({ type: "json_schema", name: "submit_seat_output", strict: true });
    expect(body.text.format.schema).toEqual(SCHEMA);
    expect("temperature" in body).toBe(false); // gpt-5.5 は temperature を受け付けない(2026-09-30 の実測)
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
    expect("temperature" in body.generationConfig).toBe(false); // 受け付けるが送らない(席の条件をそろえる)
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
  it("3 社とも temperature を送らない(値を渡されても。2026-09-30 の実測と席の対称性)", async () => {
    // claude-opus-5 は `temperature is deprecated`、gpt-5.5 は `Unsupported parameter: 'temperature'` で 400。
    // 受け付ける Gemini だけに送ると席の条件が非対称になるので、そろえて送らない(司令塔の対称性の線)。
    for (const [provider, ok] of [["openai", OPENAI_OK], ["gemini", GEMINI_OK], ["anthropic", ANTHROPIC_OK]] as const) {
      const { fetch: f, calls } = fakeFetch([{ status: 200, body: ok }]);
      await callStructured(req(provider), deps(f)); // req() は temperature: 0 を渡している
      const text = String(calls[0]!.init.body);
      expect(text.includes('"temperature"'), provider).toBe(false);
    }
    expect(SENDS_TEMPERATURE).toEqual({ openai: false, gemini: false, anthropic: false });
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

// ---------------------------------------------------------------------------
// S-5 §2.1(f)(audit-core/docs/CORE_CONNECTION_S5_PLAN_2026-10-07.md): 1 試行に所要の上限(5 分)を字で置き、
// 時間切れは「接続の失敗」と同じ扱い(1・4・16 秒の後に再送、最大 3 回)。**実際に 5 分待つ試験は書かない**
// ― attemptTimeoutMs を試験用に上書きして、AbortSignal.timeout の実物の挙動を小さい時間で確かめる。
// ---------------------------------------------------------------------------
describe("所要の上限(S-5 §2.1(f))", () => {
  it("上限の数は字で 300_000(5 分)", () => {
    expect(HTTP_ATTEMPT_TIMEOUT_MS).toBe(300_000);
  });

  it("各 fetch に AbortSignal.timeout(既定は HTTP_ATTEMPT_TIMEOUT_MS)を渡す", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: OPENAI_OK }]);
    await callStructured(req("openai"), deps(f));
    expect(calls[0]!.init.signal).toBeInstanceOf(AbortSignal);
    expect((calls[0]!.init.signal as AbortSignal).aborted).toBe(false);
  });

  // 【契約の更新】この試験が守っていた S-5 §2.1(f) の契約(「中断は接続の失敗と同じ扱いで再送し、
  // 4 回目で諦める」)は、2026-10-08 の人間の決定(audit-core/docs/CLAIM_DECOMPOSITION_D2B1_PLAN_2026-10-08.md
  // §3(b))で更新された ― 中断の時点で生成はおそらく完了して課金された可能性が高いので、再送すると
  // 同じ仕事に 2 回払うことになる。消さずに、新しい契約(「中断は再送せず 1 回で LlmTimeoutError を
  // 投げる」)を主張する形に書き換える(消すと挙動が変わった理由が読めなくなる)。
  it("時間切れ(AbortSignal の中断)は再送せず、1 回で LlmTimeoutError を投げる(旧契約 S-5 §2.1(f) は D-2b-1 §3(b) で更新された)", async () => {
    // attemptTimeoutMs を 0 に上書き(実物の AbortSignal.timeout をそのまま使い、5 分は待たない)。
    const sleeps: number[] = [];
    const calls: Array<{ signal: AbortSignal }> = [];
    const fetchImpl = (async (_url: string, init: RequestInit) => {
      const signal = init.signal as AbortSignal;
      calls.push({ signal });
      // 実物の fetch も、signal が中断されたら中断の例外を投げる(待つのは abort イベントだけ)。
      return await new Promise<Response>((_resolve, reject) => {
        signal.addEventListener("abort", () => reject(new DOMException("The operation was aborted due to timeout", "TimeoutError")));
      });
    }) as unknown as typeof fetch;
    const d: ClientDeps = { fetch: fetchImpl, apiKey: KEY, sleep: async (ms: number) => { sleeps.push(ms); }, attemptTimeoutMs: 0 };
    let caught: unknown;
    try {
      await callStructured(req("openai"), d);
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(LlmTimeoutError);
    expect(caught).not.toBeInstanceOf(LlmHttpError);
    expect(calls.length).toBe(1); // 旧契約は 4(再送していた)。新契約は再送しないので 1。
    expect(sleeps).toEqual([]); // 旧契約は [1000, 4000, 16000]。新契約はどれも待たない。
    for (const c of calls) expect(c.signal).toBeInstanceOf(AbortSignal);
  });

  it("attemptTimeoutMs を上書きしないときは既定(HTTP_ATTEMPT_TIMEOUT_MS)のまま時間切れにならない(短いやりとりは通る)", async () => {
    const { fetch: f, calls } = fakeFetch([{ status: 200, body: ANTHROPIC_OK }]);
    const r = await callStructured(req("anthropic"), deps(f));
    expect(r.httpStatus).toBe(200);
    expect((calls[0]!.init.signal as AbortSignal).aborted).toBe(false);
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

// ---------------------------------------------------------------------------
// D-2b-1(audit-core/docs/CLAIM_DECOMPOSITION_D2B1_PLAN_2026-10-08.md §3(b)): 中断(タイムアウト)は
// 他の失敗(429/5xx/接続エラー)と見分け、**再送しない**。中断の時点で生成はおそらく完了して課金された
// 可能性が高いので、再送は同じ仕事に 2 回払うことになる。429/5xx/接続エラーは今のまま再送する(別の describe で確認済み)。
// 実測(2026-10-08): Node の `AbortSignal.timeout` による中断は `err.name === "TimeoutError"`(`DOMException`)で、
// `"AbortError"` ではない(封じた予測 H-2 どおり)。
// 【重なりの整理(司令塔の決-1)】「TimeoutError の中断は再送せず 1 回で LlmTimeoutError を投げる」ことは、
// 上の「所要の上限(S-5 §2.1(f))」の書き換えた試験がすでに守っている。ここでは**別の角度**だけを見る ―
// (i) TimeoutError 以外の名前の中断を誤って広く拾っていないか、(ii) maxRetries の転送(中断とは無関係の軸)。
// ---------------------------------------------------------------------------
describe("中断(タイムアウト)は再送しない(D-2b-1 §3(b))", () => {
  /** 実物の AbortSignal.timeout と同じ形(DOMException, name)で中断する fetch 差し替え */
  function abortingFetch(name: "TimeoutError" | "AbortError"): { fetch: typeof fetch; calls: Array<{ signal: AbortSignal }> } {
    const calls: Array<{ signal: AbortSignal }> = [];
    const fetchImpl = (async (_url: string, init: RequestInit) => {
      const signal = init.signal as AbortSignal;
      calls.push({ signal });
      return await new Promise<Response>((_resolve, reject) => {
        signal.addEventListener("abort", () => reject(new DOMException("aborted", name)));
      });
    }) as unknown as typeof fetch;
    return { fetch: fetchImpl, calls };
  }

  it("AbortError という名前の中断(TimeoutError ではない)は、この区別に当たらず接続の失敗として再送する", async () => {
    // 他のどこかが AbortController.abort() を呼んだ場合などを想定 ― 今の配線では起きないが、
    // 「名前で中断を見分ける」実装が TimeoutError 以外まで広げて中断扱いしていないかを確かめる。
    // **実物の `err.name` が本当に "TimeoutError"(`"AbortError"` ではない)かは、鍵もネットワークも使わない
    // ローカルの確認で別途実測した(H-2。この試験は「AbortError という名前なら中断扱いしない」ことだけを守る)。
    const sleeps: number[] = [];
    const { fetch: f, calls } = abortingFetch("AbortError");
    const d: ClientDeps = { fetch: f, apiKey: KEY, sleep: async (ms: number) => { sleeps.push(ms); }, attemptTimeoutMs: 0 };
    let caught: unknown;
    try {
      await callStructured(req("openai"), d);
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(LlmHttpError);
    expect(caught).not.toBeInstanceOf(LlmTimeoutError);
    expect(calls.length).toBe(4); // 再送している(1・4・16 秒の後、4 回目で諦める ― 既存の接続失敗と同じ扱い)
    expect(sleeps).toEqual([1000, 4000, 16000]);
  });

  it("maxRetries を 0 に渡すと、429 でも再送せず 1 回で諦める(ClientDeps の maxRetries が効く)", async () => {
    const sleeps: number[] = [];
    const { fetch: f, calls } = fakeFetch([{ status: 429, body: { error: "rate" } }]);
    const d: ClientDeps = { fetch: f, apiKey: KEY, sleep: async (ms: number) => { sleeps.push(ms); }, maxRetries: 0 };
    await expect(callStructured(req("openai"), d)).rejects.toThrow(LlmHttpError);
    expect(calls.length).toBe(1);
    expect(sleeps).toEqual([]);
  });
});
