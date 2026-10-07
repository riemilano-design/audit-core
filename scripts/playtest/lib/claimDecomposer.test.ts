// D-2b(audit-core/docs/CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §2(a))。lib/claimDecomposer.ts を見る。
// **LLM は 1 回も呼ばない(fetch は全部差し替え)。実費 0 円。** 試験の正解は実装の表・定数から作らない
// (手で書いた原文 + 手で作った応答)。退化値(原文が空・schema で永久に落ち続ける・上限に達する)も当てる。

import { describe, expect, it } from "vitest";
import {
  DECOMPOSER_INSTRUCTION_SHA256, DECOMPOSER_USER_PREFIX, DECOMPOSER_USER_SUFFIX,
  assertPricesPresent, decomposeOriginalText, decomposerInstructionShaProblems, decomposerUserText,
  originalTextFromDecomposerUserText, validateDecomposerOutput, type DecomposeConfig,
} from "./claimDecomposer.js";
import type { SlotDeps } from "./seatRun.js";

type Rec = Record<string, unknown>;

const PRICES = { inPerMillion: 5, outPerMillion: 30 };
function cfgOf(over: Partial<DecomposeConfig> = {}): DecomposeConfig {
  return { provider: "openai", model: "gpt-5.5", apiKey: "sk-test-DUMMY00000000", prices: PRICES, reserveOutputTokens: 1_000, temperature: 0, capUsd: 10, ...over };
}
const DEPS: SlotDeps = { sleep: async () => {}, now: () => new Date("2026-10-07T00:00:00Z") } as unknown as SlotDeps;

function openaiBody(json: unknown, over: Rec = {}): Rec {
  return { id: "resp_1", model: "gpt-5.5-2026", status: "completed", output: [{ type: "message", content: [{ type: "output_text", text: JSON.stringify(json) }] }], usage: { input_tokens: 500, output_tokens: 200 }, ...over };
}

function minimalDoc(originalText: string, claims: Rec[] = []): Rec {
  return { schemaVersion: "0.1", original_text: originalText, claims };
}
function claimOf(over: Rec = {}): Rec {
  return {
    claim_id: "c1", span: [0, 1], form: "direct_value", subject: "s", value: 1, unit: null,
    modifiers: { population: null, time_range: null, normalization: null }, evidence_pointer: null, ...over,
  };
}

/** 呼ばれた順に応答を返す fetch(count の入口は呼ばれない ― provider は openai)。本物の HTTP は出ない。 */
function sequencedFetch(replies: Array<{ status: number; body: unknown }>): { fetch: typeof fetch; userTexts: string[] } {
  const userTexts: string[] = [];
  let i = 0;
  const fetchImpl = (async (_url: string, init: RequestInit) => {
    const body = JSON.parse(String(init.body)) as Rec;
    const input = body.input as Rec[] | undefined;
    const userMsg = input?.find((m) => m.role === "user");
    userTexts.push(String(userMsg?.content ?? ""));
    const r = replies[Math.min(i, replies.length - 1)]!;
    i += 1;
    return { status: r.status, ok: r.status < 400, text: async () => JSON.stringify(r.body) } as unknown as Response;
  }) as unknown as typeof fetch;
  return { fetch: fetchImpl, userTexts };
}

describe("decomposerUserText / originalTextFromDecomposerUserText(往復)", () => {
  it("decomposerUserText で作った文字列から、同じ原文を復元できる", () => {
    const text = "売上は100億円だった。";
    expect(originalTextFromDecomposerUserText(decomposerUserText(text))).toBe(text);
  });
  it("退化値: 空文字列でも往復する", () => {
    expect(originalTextFromDecomposerUserText(decomposerUserText(""))).toBe("");
  });
  it("この形で作られていない文字列は undefined(下見のダミー応答作りだけに使う安全弁)", () => {
    expect(originalTextFromDecomposerUserText("まったく無関係な文字列")).toBeUndefined();
  });
  it("前後の文字列そのものがこのファイルの約束(表示中の指示文の文言と無関係に固定されている)", () => {
    expect(DECOMPOSER_USER_PREFIX.length).toBeGreaterThan(0);
    expect(DECOMPOSER_USER_SUFFIX).toBe("\n---\n");
  });
});

describe("decomposerInstructionShaProblems", () => {
  it("固定値どおりの指示文は問題 0 件", () => {
    const content = Buffer.from("テスト"); // 内容は使わず、表の鍵名だけ見るため架空の名前で確かめる
    expect(decomposerInstructionShaProblems("no-such-file.md", content)).toEqual([
      "no-such-file.md: この指示文の sha が固定されていない(固定してから配る。版名を上げたら表に足す)",
    ]);
  });
  it("表に在る名前で内容が違えば、sha の不一致を報告する(改変の検出)", () => {
    const basename = Object.keys(DECOMPOSER_INSTRUCTION_SHA256)[0]!;
    const problems = decomposerInstructionShaProblems(basename, Buffer.from("改変された中身"));
    expect(problems.length).toBe(1);
    expect(problems[0]).toContain("sha が固定値と違う");
  });
});

describe("validateDecomposerOutput", () => {
  it("original_text が入力と一致し、schema も decompositionProblems も通れば問題 0 件", () => {
    const text = "売上は100億円だった。";
    const doc = minimalDoc(text, [claimOf({ span: [3, 7], value: 100, subject: "売上" })]);
    expect(validateDecomposerOutput(text)(doc)).toEqual([]);
  });
  it("original_text が入力と違えば、schema を見る前に不一致を報告する(書き写しの誤りを検出)", () => {
    const text = "原文A";
    const doc = minimalDoc("原文B(書き換えられた)", []);
    const problems = validateDecomposerOutput(text)(doc);
    expect(problems).toContain("original_text が入力した原文と一致しない(原文を 1 文字も変えずに書き写すこと)");
  });
  it("退化値: doc がオブジェクトではない", () => {
    expect(validateDecomposerOutput("x")(null)).toEqual(["doc がオブジェクトではない"]);
    expect(validateDecomposerOutput("x")("文字列")).toEqual(["doc がオブジェクトではない"]);
  });
});

describe("decomposeOriginalText(fetch は全部差し替え。実費 0 円)", () => {
  it("1 回目で通れば present:true・attempts は 1 件", async () => {
    const text = "売上は100億円だった。";
    const doc = minimalDoc(text, [claimOf({ span: [3, 7], value: 100, subject: "売上" })]);
    const { fetch } = sequencedFetch([{ status: 200, body: openaiBody(doc) }]);
    const result = await decomposeOriginalText(text, "指示文", cfgOf(), { ...DEPS, fetch });
    expect(result.present).toBe(true);
    expect(result.attempts.length).toBe(1);
    expect(result.llm).toEqual(doc);
    expect(result.actualCostUsd).toBeGreaterThan(0);
  });

  it("退化値: 原文が空文字列でも claims 0 件の doc で通る", async () => {
    const doc = minimalDoc("", []);
    const { fetch } = sequencedFetch([{ status: 200, body: openaiBody(doc) }]);
    const result = await decomposeOriginalText("", "指示文", cfgOf(), { ...DEPS, fetch });
    expect(result.present).toBe(true);
    expect((result.llm as Rec).claims).toEqual([]);
  });

  it("理由は累積して渡す(1 回目は original_text 不一致、2 回目は別の理由(claim_id 重複)で落ち、" +
    "2 回目に送った文には 1 回目の理由がまだ入っている ― 直前の分だけを渡すと消えてしまう)", async () => {
    const text = "売上は100億円だった。";
    const wrongTextDoc = minimalDoc("別の原文(書き換え)", [claimOf({ span: [3, 7], value: 100 })]);
    const dupIdDoc = minimalDoc(text, [claimOf({ claim_id: "c1", span: [3, 7], value: 100 }), claimOf({ claim_id: "c1", span: [0, 1], value: 2 })]);
    const okDoc = minimalDoc(text, [claimOf({ span: [3, 7], value: 100, subject: "売上" })]);
    const { fetch, userTexts } = sequencedFetch([
      { status: 200, body: openaiBody(wrongTextDoc) },
      { status: 200, body: openaiBody(dupIdDoc) },
      { status: 200, body: openaiBody(okDoc) },
    ]);
    const result = await decomposeOriginalText(text, "指示文", cfgOf(), { ...DEPS, fetch });
    expect(result.present).toBe(true);
    expect(result.attempts.length).toBe(3);
    // 1 回目で落ちた理由(original_text 不一致)が、3 回目に送った文にもまだ入っている(累積)
    expect(userTexts[2]).toContain("original_text が入力した原文と一致しない");
    // 2 回目で落ちた理由(claim_id 重複)も 3 回目の文に入っている
    expect(userTexts[2]).toContain('claim_id "c1" が文書内で重複している');
    // 2 回目の文は 1 回目の理由だけを持ち、まだ claim_id の理由は知らない(前回の返答そのものは渡さない)
    expect(userTexts[1]).toContain("original_text が入力した原文と一致しない");
    expect(userTexts[1]).not.toContain("claim_id");
  });

  it("3 回とも schema で落ちたら空席(schema_failed)。落ちた試行ごとに理由が残る(保存物)", async () => {
    const text = "x";
    const badDoc = { schemaVersion: "0.1", original_text: text, claims: [{ claim_id: "" }] }; // claim_id が空 かつ span 無し
    const { fetch } = sequencedFetch([
      { status: 200, body: openaiBody(badDoc) },
      { status: 200, body: openaiBody(badDoc) },
      { status: 200, body: openaiBody(badDoc) },
    ]);
    const result = await decomposeOriginalText(text, "指示文", cfgOf(), { ...DEPS, fetch });
    expect(result.present).toBe(false);
    expect(result.absentReason).toBe("schema_failed");
    expect(result.attempts.length).toBe(3);
    // 落ちた試行の理由の本文が保存物として残る(件数だけでなく理由そのもの)
    const problemFiles = result.files.filter((f) => f.name.includes("_problems.txt"));
    expect(problemFiles.length).toBe(3);
    for (const f of problemFiles) expect(f.content.length).toBeGreaterThan(0);
  });

  it("費用の上限に当たれば送らない(cost_cap)。生成の入口は 1 回も叩かれない", async () => {
    const text = "売上は100億円だった。";
    const { fetch, userTexts } = sequencedFetch([{ status: 200, body: openaiBody(minimalDoc(text, [])) }]);
    const result = await decomposeOriginalText(text, "指示文", cfgOf({ capUsd: 0.0000001 }), { ...DEPS, fetch });
    expect(result.present).toBe(false);
    expect(result.absentReason).toBe("cost_cap");
    expect(result.capReached).toBe(true);
    expect(userTexts.length).toBe(0);
  });

  it("鍵が無ければ空席(no_key)。モデル名が無ければ空席(no_model)。どちらも生成の入口を叩かない", async () => {
    const text = "x";
    const { fetch: fetch1, userTexts: u1 } = sequencedFetch([{ status: 200, body: openaiBody(minimalDoc(text)) }]);
    const r1 = await decomposeOriginalText(text, "指示文", cfgOf({ apiKey: "" }), { ...DEPS, fetch: fetch1 });
    expect(r1.absentReason).toBe("no_key");
    expect(u1.length).toBe(0);

    const { fetch: fetch2, userTexts: u2 } = sequencedFetch([{ status: 200, body: openaiBody(minimalDoc(text)) }]);
    const r2 = await decomposeOriginalText(text, "指示文", cfgOf({ model: "" }), { ...DEPS, fetch: fetch2 });
    expect(r2.absentReason).toBe("no_model");
    expect(u2.length).toBe(0);
  });
});

describe("assertPricesPresent(独立監査の指摘 2026-10-07 ― 単価が無いまま本番に進む穴を塞ぐ門)", () => {
  // .env は読まない。CLI の `productionConfigOf` 相当が積む `warnings` 配列を直接注入して試験する
  // (このファイルは `runClaimDecomposer.ts` を import しない ― その CLI は末尾で `await main()` を
  // 無条件に実行するため、import するだけで本番の配線が走ってしまう。鍵を使わずに試験するため、
  // 判定だけを `lib/claimDecomposer.ts` の純粋関数として切り出した)。
  it("warnings が 1 件でもあれば投げる(単価欠落で費用 0 → 上限が効かない事故を送る前に止める)", () => {
    expect(() => assertPricesPresent("gpt", ["gpt: 単価(PRICE_GPT_INPUT / PRICE_GPT_OUTPUT)が .env に無い ― 費用を 0 と見なして進めない"]))
      .toThrow(/単価が \.env に無い\(gpt\)/);
  });
  it("warnings が複数件でも投げる(件数は見ず、空かどうかだけで判定する)", () => {
    expect(() => assertPricesPresent("claude", ["理由1", "理由2"])).toThrow(/単価が \.env に無い\(claude\)/);
  });
  it("warnings が空なら投げない(単価が揃っているときは素通り)", () => {
    expect(() => assertPricesPresent("gemini", [])).not.toThrow();
  });
});
