// 束 R4 ― 送る前の概算と費用の上限(計画 §1「数え・費用」・§3)。
// 【上限を越える見込みなら送らない】概算トークン × 単価(.env の PRICE_*)が SEAT_COST_CAP_USD を越えたら送らない(司令塔の先決め 1)。
// 【概算の方法を記録する】OpenAI は count-tokens が無いので chars/3。Anthropic・Gemini は API(llmClient.countTokens)。越えたら送らない側に倒れる。

export type EstimateMethod = "chars/3" | "api";

export interface TokenEstimate {
  inputTokens: number;
  method: EstimateMethod;
}

export function estimateTokensByChars(text: string): TokenEstimate {
  return { inputTokens: Math.ceil([...text].length / 3), method: "chars/3" };
}

/**
 * 入力が或る大きさを超えると上がる段(2026-09-30 司令塔の規則)。
 * 例: Gemini は入力 200k 超で単価が上がる。**1 つの値では表せないので、超える組では高い段で見積もる(安い方に倒さない)。**
 */
export interface PriceTier {
  /** この入力トークン数を**超えたら**この段 */
  aboveInputTokens: number;
  inPerMillion: number;
  outPerMillion: number;
}

export interface Prices {
  /** USD per 1M tokens(下の段) */
  inPerMillion: number;
  outPerMillion: number;
  /** 上の段(あれば)。複数あれば、当たる段のうち**いちばん高い**ものを使う */
  tiers?: readonly PriceTier[];
}

/** その入力の大きさに当たる単価。段の境目は「超えたら上の段」。当たる段が複数なら高い方に倒す */
export function pricesFor(prices: Prices, inputTokens: number): { inPerMillion: number; outPerMillion: number } {
  let chosen = { inPerMillion: prices.inPerMillion, outPerMillion: prices.outPerMillion };
  for (const tier of prices.tiers ?? []) {
    if (inputTokens <= tier.aboveInputTokens) continue;
    if (tier.inPerMillion >= chosen.inPerMillion || tier.outPerMillion >= chosen.outPerMillion) {
      chosen = { inPerMillion: Math.max(chosen.inPerMillion, tier.inPerMillion), outPerMillion: Math.max(chosen.outPerMillion, tier.outPerMillion) };
    }
  }
  return chosen;
}

/** 費用。段のある社は入力の大きさで単価が変わる(pricesFor) */
export function costUsd(inputTokens: number, outputTokens: number, prices: Prices): number {
  const p = pricesFor(prices, inputTokens);
  return (inputTokens * p.inPerMillion + outputTokens * p.outPerMillion) / 1_000_000;
}

export interface BudgetDecision {
  ok: boolean;
  reason?: "cost_cap" | "input_limit";
  estimatedCostUsd: number;
  cumulativeCostUsd: number;
}

/**
 * 送ってよいか。累計(この実行でここまでに見込んだ費用)+ この席の見込みが上限を越えるなら cost_cap、
 * 入力トークン + 出力の取り置きが入力上限を越えるなら input_limit。
 */
export function budgetDecision(args: { inputTokens: number; reserveOutputTokens: number; prices: Prices; capUsd: number; cumulativeCostUsd: number; inputLimit?: number }): BudgetDecision {
  const estimatedCostUsd = costUsd(args.inputTokens, args.reserveOutputTokens, args.prices);
  const cumulativeCostUsd = args.cumulativeCostUsd + estimatedCostUsd;
  if (args.inputLimit !== undefined && args.inputTokens + args.reserveOutputTokens > args.inputLimit) return { ok: false, reason: "input_limit", estimatedCostUsd, cumulativeCostUsd: args.cumulativeCostUsd };
  if (cumulativeCostUsd > args.capUsd) return { ok: false, reason: "cost_cap", estimatedCostUsd, cumulativeCostUsd: args.cumulativeCostUsd };
  return { ok: true, estimatedCostUsd, cumulativeCostUsd };
}
