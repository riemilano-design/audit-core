// D-2b-0(audit-core/docs/CLAIM_DECOMPOSITION_D2B0_PLAN_2026-10-07.md §2(b))。
// 分解器(基準線でも LLM でも)が出した doc と、正解集合(`gold_*.json` の `expected_claims` /
// `expected_uncovered_number_sentences`)を比べる純粋関数。
//
// 【このファイルがやること】
// - span の一致を**多重集合**として比べる(交わり / 正解のみ / 実測のみ)。同じ span を 2 件の claim が
//   共有する場合がある(`gold_03` の c1/c2。D-2a 結果 §5)ため、集合ではなく多重集合で数える。
// - span が一致した claim の組について、`value` の一致件数・`form` の一致件数(正解の form ごとの内訳つき)を数える。
// - 被覆されない数字入りの文の集合を比べる(交わり / 正解のみ / 実測のみ)。実測側は
//   `lib/claimDecomposition.ts` の `coverageReport`(既存・挙動不変)を使う。正解側は
//   gold fixture の `expected_uncovered_number_sentences` をそのまま使う。
//
// 【このファイルが絶対にやらないこと】
// - 件数だけを返すこと(計画 §2(b)「件数だけでなく集合で返す」)。
// - 「どちらが正しいか」の判定・良し悪しの評価(これは純粋な集合演算であり、将棋の判断ではない)。
// - `coverageReport`・`decompositionProblems`・`spanRealityProblem` の挙動を変えること(呼ぶだけ)。

import { coverageReport } from "./claimDecomposition.js";

export type Span = readonly [number, number];

interface RawClaimLike {
  span: Span;
  value: unknown;
  form: unknown;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** `doc.claims[]` から span/value/form だけを取り出す(防御的 ― schema 未検査の値も受け付ける)。 */
function extractClaims(doc: unknown): RawClaimLike[] {
  const rawClaims = isRecord(doc) && Array.isArray(doc["claims"]) ? (doc["claims"] as unknown[]) : [];
  const out: RawClaimLike[] = [];
  for (const claim of rawClaims) {
    if (!isRecord(claim)) continue;
    const span = claim["span"];
    if (!Array.isArray(span) || span.length !== 2) continue;
    const [start, end] = span as [unknown, unknown];
    if (typeof start !== "number" || typeof end !== "number") continue;
    out.push({ span: [start, end], value: claim["value"], form: claim["form"] });
  }
  return out;
}

function spanKey(span: Span): string {
  return `${span[0]},${span[1]}`;
}

interface SpanBucket {
  span: Span;
  claims: RawClaimLike[];
}

function bySpan(claims: RawClaimLike[]): Map<string, SpanBucket> {
  const map = new Map<string, SpanBucket>();
  for (const claim of claims) {
    const key = spanKey(claim.span);
    const bucket = map.get(key);
    if (bucket) bucket.claims.push(claim);
    else map.set(key, { span: claim.span, claims: [claim] });
  }
  return map;
}

function compareSpansBySort(a: Span, b: Span): number {
  return a[0] - b[0] || a[1] - b[1];
}

export interface SpanMultisetComparison {
  /** 正解と実測の両方に(多重集合として)現れた span。重複があれば重複ぶん入る。 */
  intersection: Span[];
  /** 正解にしか現れなかった span(重複を含む)。 */
  expectedOnly: Span[];
  /** 実測にしか現れなかった span(重複を含む)。 */
  actualOnly: Span[];
}

export interface FormBreakdownEntry {
  /** span が一致した claim のうち、正解の form がこの値だった件数。 */
  total: number;
  /** そのうち実測の form も一致した件数。 */
  matched: number;
}

export interface UncoveredSetComparison {
  intersection: string[];
  expectedOnly: string[];
  actualOnly: string[];
}

export interface DecompositionCompareResult {
  span: SpanMultisetComparison;
  /** span が一致した claim の組の総数(= span.intersection.length)。 */
  spanMatchedCount: number;
  /** span が一致した組のうち、value も一致した件数。 */
  valueMatchCount: number;
  /** span が一致した組のうち、form も一致した件数。 */
  formMatchCount: number;
  /** 正解の form ごとの一致件数の内訳。span が一致した組だけを数える。 */
  formBreakdown: Record<string, FormBreakdownEntry>;
  uncovered: UncoveredSetComparison;
}

export interface GoldFixtureLike {
  original_text: string;
  expected_claims: unknown;
  expected_uncovered_number_sentences: readonly string[];
}

/**
 * 分解器が出した `actualDoc`(claim-decomposition v0.1 の形。schema 未検査でも落ちない)を、
 * 正解集合 `gold`(`gold_*.json` をそのまま渡せる形)と比べる。
 */
export function compareClaimDecomposition(actualDoc: unknown, gold: GoldFixtureLike): DecompositionCompareResult {
  const expectedClaims = extractClaims({ claims: gold.expected_claims });
  const actualClaims = extractClaims(actualDoc);

  const expectedBySpan = bySpan(expectedClaims);
  const actualBySpan = bySpan(actualClaims);

  const intersection: Span[] = [];
  const expectedOnly: Span[] = [];
  const actualOnly: Span[] = [];
  const pairs: Array<{ expected: RawClaimLike; actual: RawClaimLike }> = [];

  const allKeys = new Set<string>([...expectedBySpan.keys(), ...actualBySpan.keys()]);
  for (const key of allKeys) {
    const expBucket = expectedBySpan.get(key);
    const actBucket = actualBySpan.get(key);
    const exp = expBucket?.claims ?? [];
    const act = actBucket?.claims ?? [];
    const span = expBucket?.span ?? actBucket?.span;
    if (span === undefined) continue; // allKeys は両方の Map の鍵の和なので、片方には必ず存在する
    const matchedCount = Math.min(exp.length, act.length);
    for (let i = 0; i < matchedCount; i++) {
      intersection.push(span);
      const expectedClaim = exp[i];
      const actualClaim = act[i];
      if (expectedClaim !== undefined && actualClaim !== undefined) {
        pairs.push({ expected: expectedClaim, actual: actualClaim });
      }
    }
    for (let i = matchedCount; i < exp.length; i++) expectedOnly.push(span);
    for (let i = matchedCount; i < act.length; i++) actualOnly.push(span);
  }

  intersection.sort(compareSpansBySort);
  expectedOnly.sort(compareSpansBySort);
  actualOnly.sort(compareSpansBySort);

  let valueMatchCount = 0;
  let formMatchCount = 0;
  const formBreakdown: Record<string, FormBreakdownEntry> = {};
  for (const { expected, actual } of pairs) {
    if (Object.is(expected.value, actual.value) || expected.value === actual.value) valueMatchCount += 1;
    const expectedFormKey = typeof expected.form === "string" ? expected.form : String(expected.form);
    const entry = formBreakdown[expectedFormKey] ?? { total: 0, matched: 0 };
    entry.total += 1;
    const formMatches = expected.form === actual.form;
    if (formMatches) {
      entry.matched += 1;
      formMatchCount += 1;
    }
    formBreakdown[expectedFormKey] = entry;
  }

  const actualUncovered = new Set(coverageReport(actualDoc).uncovered);
  const expectedUncovered = new Set(gold.expected_uncovered_number_sentences);
  const uncoveredIntersection: string[] = [];
  const uncoveredExpectedOnly: string[] = [];
  const uncoveredActualOnly: string[] = [];
  for (const s of expectedUncovered) {
    if (actualUncovered.has(s)) uncoveredIntersection.push(s);
    else uncoveredExpectedOnly.push(s);
  }
  for (const s of actualUncovered) {
    if (!expectedUncovered.has(s)) uncoveredActualOnly.push(s);
  }

  return {
    span: { intersection, expectedOnly, actualOnly },
    spanMatchedCount: intersection.length,
    valueMatchCount,
    formMatchCount,
    formBreakdown,
    uncovered: {
      intersection: uncoveredIntersection.sort(),
      expectedOnly: uncoveredExpectedOnly.sort(),
      actualOnly: uncoveredActualOnly.sort(),
    },
  };
}
