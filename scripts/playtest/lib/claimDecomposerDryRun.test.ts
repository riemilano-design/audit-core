// D-2b §2(b)。lib/claimDecomposerDryRun.ts を見る。**実際の HTTP は 1 回も出ない(fetch は差し替え)。実費 0 円。**
// 試験の正解は実装の表・定数から作らない(手で書いた原文・4 本の実在する gold fixture)。
// 退化値(原文が空・user の本文が壊れていて復元できない)も当てる。

import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { decomposeOriginalText, type DecomposeConfig } from "./claimDecomposer.js";
import { buildDryRunFetch } from "./claimDecomposerDryRun.js";
import { checkClaimDecomposition } from "./claimDecomposition.js";
import { baselineDecompose } from "./decompositionBaseline.js";
import { callStructured, countTokens, type Provider } from "./llmClient.js";
import type { SlotDeps } from "./seatRun.js";

const GOLD_DIR = new URL("../fixtures/decomposition/", import.meta.url);

function loadGoldTexts(): Array<{ id: string; original_text: string }> {
  const dir = path.resolve(GOLD_DIR.pathname);
  return readdirSync(dir).filter((f) => f.endsWith(".json")).sort().map((f) => {
    const json = JSON.parse(readFileSync(path.join(dir, f), "utf-8")) as { original_text: string };
    return { id: f, original_text: json.original_text };
  });
}

describe("buildDryRunFetch ― llmClient.callStructured を通した 3 社の応答の読み", () => {
  const PROVIDERS: Provider[] = ["openai", "gemini", "anthropic"];
  for (const provider of PROVIDERS) {
    it(`${provider}: callStructured が原文から復元した baselineDecompose の doc を json として返す`, async () => {
      const { fetch } = buildDryRunFetch();
      const text = "直近20局のうち、先に有利になった局は9局でした。";
      const user = `分解してほしい原文(original_text)は次のとおりです。これを 1 文字も変えずに \`original_text\` へ書き写し、\`claims[]\` を作ってください。\n\n---\n${text}\n---\n`;
      const res = await callStructured(
        { provider, model: "dry-run-model", system: "指示文", user, schema: { type: "object" }, schemaName: "submit_claim_decomposition", maxOutputTokens: 1_000 },
        { fetch, apiKey: "dry-run-key" },
      );
      expect(res.httpStatus).toBe(200);
      expect(res.json).toEqual(baselineDecompose(text));
      expect(checkClaimDecomposition(res.json).problems).toEqual([]);
    });
  }

  it("gemini / anthropic: countTokens も(ネットワークに出ずに)数を返す", async () => {
    const { fetch } = buildDryRunFetch();
    const gemini = await countTokens({ provider: "gemini", model: "dry-run-model", system: "s", user: "u" }, { fetch, apiKey: "k" });
    const anthropic = await countTokens({ provider: "anthropic", model: "dry-run-model", system: "s", user: "u" }, { fetch, apiKey: "k" });
    expect(gemini).toBe(500);
    expect(anthropic).toBe(500);
  });

  it("退化値: user の本文が decomposerUserText の形でなければ、空の claims(baselineDecompose(''))を返す", async () => {
    const { fetch } = buildDryRunFetch();
    const res = await callStructured(
      { provider: "openai", model: "dry-run-model", system: "s", user: "まったく無関係な文字列", schema: { type: "object" }, schemaName: "submit_claim_decomposition", maxOutputTokens: 1_000 },
      { fetch, apiKey: "k" },
    );
    expect(res.json).toEqual(baselineDecompose(""));
  });

  it("呼んだ入口を log に残す(生成の入口と数えの入口を区別する)", async () => {
    const log = { calls: [] as Array<{ url: string; provider: Provider; kind: "generate" | "count" }> };
    const { fetch } = buildDryRunFetch(log);
    await callStructured(
      { provider: "anthropic", model: "m", system: "s", user: "u", schema: { type: "object" }, schemaName: "submit_claim_decomposition", maxOutputTokens: 10 },
      { fetch, apiKey: "k" },
    );
    await countTokens({ provider: "anthropic", model: "m", system: "s", user: "u" }, { fetch, apiKey: "k" });
    expect(log.calls.map((c) => c.kind)).toEqual(["generate", "count"]);
    expect(log.calls.every((c) => c.provider === "anthropic")).toBe(true);
  });
});

describe("下見: decomposeOriginalText を buildDryRunFetch に通して、実在する gold 4 本すべてが present:true になる(本番と同じ配線)", () => {
  const PROVIDERS: Provider[] = ["openai", "gemini", "anthropic"];
  const golds = loadGoldTexts();
  it("gold fixture が実際に 4 本ある(このファイル自身の前提を確かめる)", () => {
    expect(golds.length).toBe(4);
  });
  for (const provider of PROVIDERS) {
    it(`${provider}: 4 本すべて present:true・checkClaimDecomposition の問題 0 件`, async () => {
      const { fetch } = buildDryRunFetch();
      const deps: SlotDeps = { fetch, sleep: async () => {} };
      const cfg: DecomposeConfig = { provider, model: "dry-run-model", apiKey: "dry-run-key", prices: { inPerMillion: 1, outPerMillion: 1 }, reserveOutputTokens: 2_000, temperature: 0, capUsd: 1_000 };
      let cumulative = 0;
      for (const gold of golds) {
        const slot = await decomposeOriginalText(gold.original_text, "指示文", { ...cfg, cumulativeCostUsd: cumulative }, deps);
        expect(slot.present, `${provider} / ${gold.id}: ${slot.absentReason ?? ""} ${slot.absentNote ?? ""}`).toBe(true);
        expect(checkClaimDecomposition(slot.llm).problems).toEqual([]);
        expect(slot.actualCostUsd).toBeGreaterThan(0); // 費用の記録に 0.00 が入っていない
        cumulative = slot.cumulativeCostUsd;
      }
    });
  }
});
