// D-2b(audit-core/docs/CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §2(b))。
// 下見(dry-run)― API を呼ばずに、**本番とまったく同じ配線**(`lib/claimDecomposer.ts` の
// `decomposeOriginalText` → `lib/seatRun.ts` の `runSlot` → `lib/llmClient.ts` の
// `callStructured`/`countTokens`)をそのまま通し、**ネットワークへ出る層(`deps.fetch`)だけ**を
// 差し替える。相対の道・cwd・費用の記録の器(`runSlot` が返す `estimatedCostUsd`/`actualCostUsd`)は
// 本番と同じものを使う ― ここで作り直さない。
//
// 【ダミーの答えの作り方】送られてきた HTTP 要求の本文(各社の形式)から、その回で聞かれた user の
// 本文を取り出し、`originalTextFromDecomposerUserText`(`lib/claimDecomposer.ts`)で元の `original_text`
// を復元する。復元できたら `baselineDecompose`(既存・無変更。D-2b-0)に通した結果を、
// 「LLM が書いたことにする」ダミーの答えとして各社の応答の形(`parseStructuredResponse` が読む形)で返す。
// `baselineDecompose` の出力は `checkClaimDecomposition` を通ることが分かっている
// (`decompositionBaseline.test.ts`)ので、下見は「本番の配線が最後まで通るか」を確かめるものであり、
// **分解の精度を測るものではない**(精度は実 run で初めて測れる。計画 §2(c) は本番の実行)。
//
// 【このファイルが絶対にやらないこと】
// - 実際の HTTP 呼び出し(global fetch を呼ばない。`fetch` という名を持つが中身はローカルの関数)。
// - 分解の精度の測定(それは `decompositionCompare` の役割)。
// - `baselineDecompose`・`checkClaimDecomposition`・`runSlot` の挙動を変えること(呼ぶだけ)。

import { originalTextFromDecomposerUserText } from "./claimDecomposer.js";
import { baselineDecompose, type BaselineDoc } from "./decompositionBaseline.js";
import type { Provider } from "./llmClient.js";

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** URL から「数えの入口」か「生成の入口」か、どの社かを見分ける(`lib/llmClient.ts` の `urlOf` が作る URL の形)。 */
function routeOf(url: string): { provider: Provider; kind: "generate" | "count" } {
  if (url.includes("generativelanguage.googleapis.com")) {
    return { provider: "gemini", kind: url.includes(":countTokens") ? "count" : "generate" };
  }
  if (url.includes("api.anthropic.com")) {
    return { provider: "anthropic", kind: url.endsWith("/count_tokens") ? "count" : "generate" };
  }
  return { provider: "openai", kind: "generate" }; // OpenAI は countTokens を呼ばない(lib/llmClient.ts countTokens 参照)
}

/** HTTP 要求の本文(各社の形式)から user の本文を取り出す(`lib/llmClient.ts` の `bodyOf` の逆読み)。 */
function userTextOfRequestBody(provider: Provider, body: Rec): string {
  if (provider === "openai" && Array.isArray(body.input)) {
    const userMsg = (body.input as Rec[]).find((m) => m.role === "user");
    return typeof userMsg?.content === "string" ? userMsg.content : "";
  }
  if (provider === "gemini" && Array.isArray(body.contents)) {
    const first = body.contents[0] as Rec | undefined;
    const parts = Array.isArray(first?.parts) ? (first!.parts as Rec[]) : [];
    return typeof parts[0]?.text === "string" ? (parts[0]!.text as string) : "";
  }
  if (provider === "anthropic" && Array.isArray(body.messages)) {
    const first = body.messages[0] as Rec | undefined;
    return typeof first?.content === "string" ? (first.content as string) : "";
  }
  return "";
}

/** `schemaName`(ツール名)を本文から取り出す(Anthropic の tool_use 応答に name として積む)。 */
function schemaNameOfRequestBody(provider: Provider, body: Rec): string {
  if (provider === "anthropic" && Array.isArray(body.tools)) {
    const tool = (body.tools as Rec[])[0];
    return typeof tool?.name === "string" ? tool.name : "submit_claim_decomposition";
  }
  if (provider === "openai" && isRecord(body.text) && isRecord((body.text as Rec).format)) {
    const name = ((body.text as Rec).format as Rec).name;
    return typeof name === "string" ? name : "submit_claim_decomposition";
  }
  return "submit_claim_decomposition";
}

/** ダミーの answer(doc)。復元できなければ最小の空 doc(claims 0 件)にする ― 本番では起きない経路。 */
function dummyDocOf(userText: string): BaselineDoc {
  const originalText = originalTextFromDecomposerUserText(userText);
  return baselineDecompose(originalText ?? "");
}

/** 社ごとの「生成の入口」の応答の形(`lib/llmClient.ts` の `parseStructuredResponse` が読む形)。 */
function generateResponseBodyOf(provider: Provider, schemaName: string, doc: BaselineDoc): Rec {
  const usage = { inputTokens: 500, outputTokens: 200 };
  switch (provider) {
    case "openai":
      return {
        id: "dryrun_resp_1", model: "dry-run-model", status: "completed",
        output: [{ type: "message", content: [{ type: "output_text", text: JSON.stringify(doc) }] }],
        usage: { input_tokens: usage.inputTokens, output_tokens: usage.outputTokens },
      };
    case "gemini":
      return {
        candidates: [{ content: { parts: [{ text: JSON.stringify(doc) }] }, finishReason: "STOP" }],
        usageMetadata: { promptTokenCount: usage.inputTokens, candidatesTokenCount: usage.outputTokens },
        modelVersion: "dry-run-model",
      };
    case "anthropic":
      return {
        id: "dryrun_msg_1", model: "dry-run-model", stop_reason: "tool_use",
        content: [{ type: "tool_use", name: schemaName, input: doc }],
        usage: { input_tokens: usage.inputTokens, output_tokens: usage.outputTokens },
      };
  }
}

/** 社ごとの「数えの入口」の応答の形(Gemini・Anthropic だけが呼ばれる。`lib/llmClient.ts` の `countTokens`)。 */
function countResponseBodyOf(provider: Provider): Rec {
  return provider === "anthropic" ? { input_tokens: 500 } : { totalTokens: 500 };
}

export interface DryRunFetchLog {
  calls: Array<{ url: string; provider: Provider; kind: "generate" | "count" }>;
}

/**
 * 下見用の `fetch`(`SlotDeps.fetch` にそのまま渡せる形)。実際の HTTP は一切出さない。
 * `log` を渡すと、どの入口が何回叩かれたかを記録する(試験・下見の報告用)。
 */
export function buildDryRunFetch(log: DryRunFetchLog = { calls: [] }): { fetch: typeof fetch; log: DryRunFetchLog } {
  const fetchImpl = (async (url: string | URL, init?: RequestInit) => {
    const urlStr = String(url);
    const { provider, kind } = routeOf(urlStr);
    log.calls.push({ url: urlStr, provider, kind });
    const bodyText = typeof init?.body === "string" ? init.body : "{}";
    const body = (JSON.parse(bodyText) as Rec) ?? {};
    const responseBody = kind === "count"
      ? countResponseBodyOf(provider)
      : generateResponseBodyOf(provider, schemaNameOfRequestBody(provider, body), dummyDocOf(userTextOfRequestBody(provider, body)));
    return new Response(JSON.stringify(responseBody), { status: 200, headers: { "content-type": "application/json" } });
  }) as unknown as typeof fetch;
  return { fetch: fetchImpl, log };
}
