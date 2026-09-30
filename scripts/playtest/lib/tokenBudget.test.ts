// 束 R4 の試験 ― 送る前の概算と上限(計画 §1「数え・費用」・§3)。**越える見込みなら送らない側に倒れる**。
import { describe, expect, it } from "vitest";
import { budgetDecision, costUsd, estimateTokensByChars, pricesFor } from "./tokenBudget.js";

const PRICES = { inPerMillion: 3, outPerMillion: 15 };

describe("概算", () => {
  it("chars/3 で切り上げ、方法を記録する(OpenAI は count-tokens が無い)", () => {
    expect(estimateTokensByChars("abcd")).toEqual({ inputTokens: 2, method: "chars/3" });
    expect(estimateTokensByChars("あいうえお").inputTokens).toBe(2);
    expect(estimateTokensByChars("").inputTokens).toBe(0);
  });
  it("費用は 100 万トークンあたりの単価から", () => {
    expect(costUsd(1_000_000, 0, PRICES)).toBe(3);
    expect(costUsd(70_000, 30_000, PRICES)).toBeCloseTo(0.21 + 0.45, 10);
  });
});

describe("上限で止める", () => {
  const base = { inputTokens: 70_000, reserveOutputTokens: 30_000, prices: PRICES, capUsd: 1, cumulativeCostUsd: 0 };
  it("収まれば ok。累計に見込みを足して返す", () => {
    const d = budgetDecision(base);
    expect(d.ok).toBe(true);
    expect(d.estimatedCostUsd).toBeCloseTo(0.66, 10);
    expect(d.cumulativeCostUsd).toBeCloseTo(0.66, 10);
  });
  it("累計が上限を越えるなら cost_cap(累計は増やさない ― 送っていないので)", () => {
    const d = budgetDecision({ ...base, cumulativeCostUsd: 0.5 });
    expect(d).toMatchObject({ ok: false, reason: "cost_cap", cumulativeCostUsd: 0.5 });
    expect(d.estimatedCostUsd).toBeCloseTo(0.66, 10);
  });
  it("ちょうど上限は通す(越えたときだけ止める)", () => {
    expect(budgetDecision({ ...base, capUsd: 0.66 }).ok).toBe(true);
    expect(budgetDecision({ ...base, capUsd: 0.65 }).ok).toBe(false);
  });
  it("入力 + 取り置きが社の上限を越えるなら input_limit(費用より先に見る)", () => {
    const d = budgetDecision({ ...base, inputLimit: 99_999 });
    expect(d).toMatchObject({ ok: false, reason: "input_limit" });
    expect(budgetDecision({ ...base, inputLimit: 100_000 }).ok).toBe(true);
  });
  it("入力上限が無い社(.env に置かれていない)は費用だけで見る", () => {
    expect(budgetDecision({ ...base, inputLimit: undefined }).ok).toBe(true);
  });
});

describe("入力が大きいと上がる段(2026-09-30 司令塔の規則: 安い方に倒さない)", () => {
  // Gemini の形: 下の段 2/12、入力 200k 超で 4/18
  const GEMINI = { inPerMillion: 2, outPerMillion: 12, tiers: [{ aboveInputTokens: 200_000, inPerMillion: 4, outPerMillion: 18 }] };
  it("境目までは下の段、超えたら上の段(境目そのものは下の段)", () => {
    expect(pricesFor(GEMINI, 70_649)).toEqual({ inPerMillion: 2, outPerMillion: 12 });
    expect(pricesFor(GEMINI, 200_000)).toEqual({ inPerMillion: 2, outPerMillion: 12 });
    expect(pricesFor(GEMINI, 200_001)).toEqual({ inPerMillion: 4, outPerMillion: 18 });
  });
  it("費用も段で変わる(いまの束 約 7 万トークンは下の段)", () => {
    expect(costUsd(70_000, 10_000, GEMINI)).toBeCloseTo(0.14 + 0.12, 10);
    expect(costUsd(250_000, 10_000, GEMINI)).toBeCloseTo(1 + 0.18, 10);
  });
  it("段が無い社はそのまま 1 つの単価", () => {
    expect(pricesFor(PRICES, 9_999_999)).toEqual({ inPerMillion: 3, outPerMillion: 15 });
  });
  it("上限の判定も上の段で見る(下の段なら通る額で止まる)", () => {
    const args = { inputTokens: 250_000, reserveOutputTokens: 10_000, prices: GEMINI, capUsd: 0.8, cumulativeCostUsd: 0 };
    expect(budgetDecision(args)).toMatchObject({ ok: false, reason: "cost_cap" });
    // 下の段の単価で見ていれば 0.5 + 0.12 = 0.62 ドルで通ってしまう
    expect(costUsd(250_000, 10_000, { inPerMillion: 2, outPerMillion: 12 })).toBeLessThan(0.8);
  });
  it("段の並びが逆でも高い方に倒れる", () => {
    const flipped = { inPerMillion: 2, outPerMillion: 12, tiers: [{ aboveInputTokens: 200_000, inPerMillion: 4, outPerMillion: 18 }, { aboveInputTokens: 100_000, inPerMillion: 3, outPerMillion: 14 }] };
    expect(pricesFor(flipped, 150_000)).toEqual({ inPerMillion: 3, outPerMillion: 14 });
    expect(pricesFor(flipped, 250_000)).toEqual({ inPerMillion: 4, outPerMillion: 18 });
  });
});
