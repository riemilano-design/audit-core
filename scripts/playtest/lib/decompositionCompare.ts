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

import { coverageReport, splitIntoSentences } from "./claimDecomposition.js";

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

// ============================================================================
// 封 ③-1(audit-core/docs/COMPARATOR_FIX_PLAN_2026-10-08.md §1、および 1 回目の差し戻し後の
// 追記 ― 決-F/決-G/決-H/決-I/決-J)。
//
// 【ここから下が新しい関数】既存の `compareClaimDecomposition` とその出力(既存の 6 欄)は
// 1 行も変えていない(決-A)。ここから下は、claim の「同一性」(どの実測がどの正解に当たるか)を
// 判定する、新しい・独立した計算である。既存の補助関数(`isRecord` のみ例外的に共有。
// 副作用の無い純粋な型ガードであり、挙動を変える余地が無い)は再利用しない ― 既存の挙動が
// 新しい関数の変更に引き込まれないようにするため。
//
// 【設計(1 回目の差し戻し後)】
// - 決-F: 対は**文書全体**で作る。文ごとのバケツに閉じない(バケツ制限は `sameSentence` を
//   構造上つねに真にしてしまい、封 ③-1 が消そうとした欠陥(BREAK-7)をそのまま残すため)。
// - 決-B: `hostSentenceOf` は「span が最も重なる文」を返す純粋関数(変更なし)。
// - 決-G: 辺の重みは整数で固定する ― value 一致 = 8 / form 一致 = 4 /
//   同じ文(`hostSentenceOf` が一致) = 1。重み 0(どれも一致しない)の対は作らない
//   (= 最終的な `pairs` に含めない)。
// - 決-H: 割り当て問題の最適解(ハンガリー法)で解く。全探索と貪欲の切り替えは行わない
//   (`greedyFallbackSentences` は削除済み)。矩形(正解・実測の件数が異なる)を扱える。
//   決定的(同じ入力には常に同じ結果)。
// - 決-I: 文の正しさ(`sameSentence`/`sentenceCorrect`)は、**対を作った後に**別に判定する。
//   対を作る重み(決-G の +1)には `hostSentenceOf` の一致を使うが、`pairs[].sameSentence` は
//   そこから流用せず、対が決まった後にもう一度 `hostSentenceOf` を呼んで判定する
//   (対の作り方の中ではこの判定結果を使わない)。
// - claim の同一性は `claim_id` ではなく、入力配列の順番に依存しない「正準順序」
//   (span 昇順 → claim_id 昇順)を割り当てた添字で表す(`compareClaimDecompositionBySentence`
//   の公開する `goldIndex`/`actualIndex` のためだけの割り付けであり、対を作る内部の計算
//   (`matchClaimsBySentence`)はこれに依存しない ― 決-J の S-B が直接確かめる)。
// ============================================================================

export interface SentenceLike {
  readonly start: number;
  readonly end: number;
}

/**
 * 決-B。`span` に対して「重なりが最大の文」を返す。
 * 重なり = `min(span[1], s.end) - max(span[0], s.start)`。同点のときは `start` が小さい文。
 * 重なりが 0 以下しか無ければ `undefined`。
 */
export function hostSentenceOf<S extends SentenceLike>(sentences: readonly S[], span: Span): S | undefined {
  let best: S | undefined;
  let bestOverlap = 0;
  for (const s of sentences) {
    const overlap = Math.min(span[1], s.end) - Math.max(span[0], s.start);
    if (overlap <= 0) continue;
    if (best === undefined || overlap > bestOverlap || (overlap === bestOverlap && s.start < best.start)) {
      best = s;
      bestOverlap = overlap;
    }
  }
  return best;
}

export interface WeightedClaim {
  claimId: string;
  span: Span;
  value: unknown;
  form: unknown;
}

/** `doc.claims[]` から span/value/form/claim_id を取り出す(`extractClaims` と同じ防御的な作り。意図的に重複させる ― 既存の `extractClaims`・`RawClaimLike` は変えない)。 */
export function extractWeightedClaims(doc: unknown): WeightedClaim[] {
  const rawClaims = isRecord(doc) && Array.isArray(doc["claims"]) ? (doc["claims"] as unknown[]) : [];
  const out: WeightedClaim[] = [];
  for (const claim of rawClaims) {
    if (!isRecord(claim)) continue;
    const span = claim["span"];
    if (!Array.isArray(span) || span.length !== 2) continue;
    const [start, end] = span as [unknown, unknown];
    if (typeof start !== "number" || typeof end !== "number") continue;
    const claimId = typeof claim["claim_id"] === "string" ? (claim["claim_id"] as string) : "";
    out.push({ claimId, span: [start, end], value: claim["value"], form: claim["form"] });
  }
  return out;
}

/**
 * 正準順序: span[0] 昇順 → span[1] 昇順 → claim_id 昇順(文字列比較)。
 * **入力配列の並び順(= 添字)に依存しない**。`compareClaimDecompositionBySentence` が公開する
 * `goldIndex`/`actualIndex` の添字を決めるためだけに使う(対を作る計算そのものはこれに依存しない。
 * 決-J の S-B が、この並べ替えを経ない `matchClaimsBySentence` を直接呼んで確かめる)。
 * 既知の限界: span と claim_id の両方が完全に同じ claim が 2 件以上あると順序は定まらない
 * (`decompositionProblems` の claim_id 重複検査が別に守る領域であり、ここでは扱わない)。
 */
function compareWeightedClaims(a: WeightedClaim, b: WeightedClaim): number {
  if (a.span[0] !== b.span[0]) return a.span[0] - b.span[0];
  if (a.span[1] !== b.span[1]) return a.span[1] - b.span[1];
  if (a.claimId < b.claimId) return -1;
  if (a.claimId > b.claimId) return 1;
  return 0;
}

/** 決-G: 辺の重み。value 一致 = 8 / form 一致 = 4 / 同じ文(host が一致) = 1。整数固定・浮動小数を使わない。 */
const VALUE_WEIGHT = 8;
const FORM_WEIGHT = 4;
const SAME_SENTENCE_BONUS = 1;
/** 1 対がとりうる重みの最大値(= 8 + 4 + 1)。ハンガリー法を「最小コスト」の形に変換するための定数。 */
const MAX_PAIR_WEIGHT = VALUE_WEIGHT + FORM_WEIGHT + SAME_SENTENCE_BONUS;

/**
 * 決-G。host(`hostSentenceOf` の結果、無ければ `undefined`)はあらかじめ計算済みのものを受け取る
 * (呼び出し側が重み行列を作るときに 1 回だけ計算してキャッシュする ― O(n*m) 回 `hostSentenceOf` を
 * 呼び直さないため)。**この重みの計算自体は「対を作る」ために使うスコアであり、決-I が言う
 * 「対の作り方の中では使わない」対象(`sentenceCorrect`/`pairs[].sameSentence` の最終判定)とは別**
 * ― 決-I の判定は対が決まった後に `hostSentenceOf` を呼び直して行う(下記 `compareClaimDecompositionBySentence`)。
 */
function pairWeight(g: WeightedClaim, a: WeightedClaim, hostG: SentenceLike | undefined, hostA: SentenceLike | undefined): number {
  let weight = 0;
  if (g.value === a.value) weight += VALUE_WEIGHT;
  if (g.form === a.form) weight += FORM_WEIGHT;
  if (hostG !== undefined && hostA !== undefined && hostG.start === hostA.start) weight += SAME_SENTENCE_BONUS;
  return weight;
}

/** `arr[index]` を安全に読む(`noUncheckedIndexedAccess` 対応)。範囲内であることを呼び出し元が
 * 構造上保証している箇所でだけ使う ― 保証が破れたら(本来起きないはずの)例外で止める(黙って
 * 既定値を返して誤りを隠さない)。 */
function requireAt<T>(arr: readonly T[], index: number): T {
  const value = arr[index];
  if (value === undefined) throw new Error(`decompositionCompare: index ${index} が範囲外(長さ ${arr.length})`);
  return value;
}

/**
 * 決-H。n 行 <= m 列の最小コスト完全割り当て(ハンガリー法。O(n^2 m))。1-indexed の添字で
 * `p[j]` = 列 j に割り当てられた行(1-indexed、0 は未割り当て)を求める古典的な実装(e-maxx 系)。
 * `n <= m` を呼び出し元が保証する(大きい方に合わせて転置するのは `maxWeightBipartiteMatch` の責務)。
 * 決定的: 同じ `cost` には常に同じ結果を返す(同点の扱いは `cur < minv[j]` の厳密な不等号・
 * 列を小さい番号から走査する順序で固定される。乱択を使わない)。
 */
function hungarianMinCostAssignment(cost: ReadonlyArray<ReadonlyArray<number>>, n: number, m: number): Array<[number, number]> {
  const INF = Number.POSITIVE_INFINITY;
  const u = new Array<number>(n + 1).fill(0);
  const v = new Array<number>(m + 1).fill(0);
  const p = new Array<number>(m + 1).fill(0);
  const way = new Array<number>(m + 1).fill(0);

  for (let i = 1; i <= n; i++) {
    p[0] = i;
    let j0 = 0;
    const minv = new Array<number>(m + 1).fill(INF);
    const used = new Array<boolean>(m + 1).fill(false);
    do {
      used[j0] = true;
      const i0 = requireAt(p, j0);
      const costRow = requireAt(cost, i0 - 1);
      let delta = INF;
      let j1 = -1;
      for (let j = 1; j <= m; j++) {
        if (requireAt(used, j)) continue;
        const cur = requireAt(costRow, j - 1) - requireAt(u, i0) - requireAt(v, j);
        if (cur < requireAt(minv, j)) {
          minv[j] = cur;
          way[j] = j0;
        }
        if (requireAt(minv, j) < delta) {
          delta = requireAt(minv, j);
          j1 = j;
        }
      }
      for (let j = 0; j <= m; j++) {
        if (requireAt(used, j)) {
          const pj = requireAt(p, j);
          u[pj] = requireAt(u, pj) + delta;
          v[j] = requireAt(v, j) - delta;
        } else {
          minv[j] = requireAt(minv, j) - delta;
        }
      }
      j0 = j1;
    } while (requireAt(p, j0) !== 0);
    do {
      const j1 = requireAt(way, j0);
      p[j0] = requireAt(p, j1);
      j0 = j1;
    } while (j0 !== 0);
  }

  const pairs: Array<[number, number]> = [];
  for (let j = 1; j <= m; j++) {
    const i = requireAt(p, j);
    if (i !== 0) pairs.push([i - 1, j - 1]);
  }
  return pairs;
}

/**
 * 決-H。`weights`(n 行 × m 列、各要素は 0 以上の整数)から、総重みが最大になる対応付けを解く
 * (割り当て問題の最適解。全探索と貪欲の切り替えは行わない)。
 * 矩形(n ≠ m)を扱う ― 小さい方の辺が尽きるまで全行(または全列)を使い切る完全割り当てを
 * ハンガリー法で求め(`MAX_PAIR_WEIGHT - weight` のコストに変換して最小化)、**重み 0 の対は
 * 結果から除く**(決-G「重み 0 の対は作らない」)。重みはすべて 0 以上なので、完全割り当てに
 * 重み 0 の対が混ざっても総重みは変わらない(= 残りをどう詰めても損にならない)。したがって
 * これは「一部が未割り当てでよい」最大重みマッチングと同じ値を与える。
 */
export function maxWeightBipartiteMatch(weights: ReadonlyArray<ReadonlyArray<number>>, n: number, m: number): Array<[number, number]> {
  if (n === 0 || m === 0) return [];
  const transpose = n > m;
  const rows = transpose ? m : n;
  const cols = transpose ? n : m;
  const cost: number[][] = [];
  for (let i = 0; i < rows; i++) {
    const row: number[] = [];
    for (let j = 0; j < cols; j++) {
      const w = transpose ? requireAt(requireAt(weights, j), i) : requireAt(requireAt(weights, i), j);
      row.push(MAX_PAIR_WEIGHT - w);
    }
    cost.push(row);
  }
  const rawPairs = hungarianMinCostAssignment(cost, rows, cols);
  const result: Array<[number, number]> = [];
  for (const [r, c] of rawPairs) {
    const [gi, aj] = transpose ? [c, r] : [r, c];
    const w = requireAt(requireAt(weights, gi), aj);
    if (w > 0) result.push([gi, aj]);
  }
  return result;
}

export interface ClaimMatchPair {
  gold: WeightedClaim;
  actual: WeightedClaim;
  valueMatch: boolean;
  formMatch: boolean;
}

export interface ClaimMatchResult {
  pairs: ClaimMatchPair[];
  goldUnmatched: WeightedClaim[];
  actualUnmatched: WeightedClaim[];
}

/**
 * 決-F/決-G/決-H。正解・実測の claim 配列(どんな順番で渡されてもよい)と文の一覧から、
 * **文書全体で**重みが最大になる対応付けを解く(文ごとのバケツに閉じない ― 決-F)。
 *
 * **入力配列の並び順に依存しない**(決-J の S-B が、この関数を正準順序付けの手前から直接
 * 呼んで確かめる)。これを保証するため、内部で claim の**内容**(span → claim_id。
 * `compareWeightedClaims` と同じ比べ方)に基づく順序へいったん並べ替えてから重み行列を作る。
 * この並べ替えは `compareClaimDecompositionBySentence` が出力の添字(`goldIndex`/`actualIndex`)を
 * 決めるために行う「正準順序付け」とは**独立**の、この関数内部だけの実装詳細である
 * ― ハンガリー法の同点の崩し方を入力配列の見た目の並び(呼び出し側の都合)に委ねず、claim の
 * 内容という決定的な基準に委ねるために必要であり、出力の意味には現れない(出力は常に claim の
 * オブジェクトそのもの(参照)で返すので、呼び出し側は自分の添字に自分で対応づけられる)。
 *
 * 決-I: ここでは value/form の一致と `hostSentenceOf` の一致(決-G の +1 ボーナス)を**重みの計算**
 * だけに使う。対が決まった後の「文が合っているか」の判定(`sameSentence`/`sentenceCorrect`)は、
 * ここでは一切返さない ― それは呼び出し側が対の後にもう一度判定する(決-I「対の作り方の中では
 * この判定を使わない」)。
 */
export function matchClaimsBySentence(
  goldClaims: readonly WeightedClaim[],
  actualClaims: readonly WeightedClaim[],
  sentences: readonly SentenceLike[],
): ClaimMatchResult {
  const sortedGold = [...goldClaims].sort(compareWeightedClaims);
  const sortedActual = [...actualClaims].sort(compareWeightedClaims);
  const n = sortedGold.length;
  const m = sortedActual.length;
  if (n === 0 || m === 0) {
    return { pairs: [], goldUnmatched: sortedGold, actualUnmatched: sortedActual };
  }

  const hostGold = sortedGold.map((g) => hostSentenceOf(sentences, g.span));
  const hostActual = sortedActual.map((a) => hostSentenceOf(sentences, a.span));

  // `hostGold[i]`/`hostActual[j]` は「host が無い(= undefined)」を正当な値として持つので
  // `requireAt`(undefined を内部不整合として例外にする)は使わない。添字 i・j は
  // `sortedGold`/`sortedActual` と同じ長さの配列を `.map` で作っているため構造上つねに範囲内。
  const weights: number[][] = sortedGold.map((g, i) => sortedActual.map((a, j) => pairWeight(g, a, hostGold[i], hostActual[j])));

  const matched = maxWeightBipartiteMatch(weights, n, m);

  const pairs: ClaimMatchPair[] = [];
  const matchedGoldIdx = new Set<number>();
  const matchedActualIdx = new Set<number>();
  for (const [gi, aj] of matched) {
    const g = requireAt(sortedGold, gi);
    const a = requireAt(sortedActual, aj);
    matchedGoldIdx.add(gi);
    matchedActualIdx.add(aj);
    pairs.push({ gold: g, actual: a, valueMatch: g.value === a.value, formMatch: g.form === a.form });
  }

  const goldUnmatched = sortedGold.filter((_, i) => !matchedGoldIdx.has(i));
  const actualUnmatched = sortedActual.filter((_, i) => !matchedActualIdx.has(i));

  return { pairs, goldUnmatched, actualUnmatched };
}

export interface SentenceAwareClaimPair {
  /** 正準順序(span 昇順 → claim_id 昇順)における正解 claim の添字。 */
  goldIndex: number;
  /** 正準順序における実測 claim の添字。 */
  actualIndex: number;
  /** この対の正解・実測それぞれの導出文(`hostSentenceOf`)が同一か。決-I: 対が決まった後に
   * `hostSentenceOf` を呼び直して判定する(対を作るときに使った決-G の +1 ボーナスの値を
   * そのまま流用しない)。双方とも導出文が無い(`undefined`)場合は同一と数えない。 */
  sameSentence: boolean;
  valueMatch: boolean;
  formMatch: boolean;
}

export interface SentenceAwareCompareResult {
  pairs: SentenceAwareClaimPair[];
  /** 対応が付かなかった正解の添字(正準順序)。 */
  goldUnmatched: number[];
  /** 対応が付かなかった実測の添字(正準順序)。 */
  actualUnmatched: number[];
  /** 正解の導出文と実測の導出文が同一の対の件数(別の正解の文に当たったものは数えない)。 */
  sentenceCorrect: number;
}

/** オブジェクト参照をキーにした `Map` から値を読む(無ければ内部不整合として例外を投げる)。 */
function requireFromRefMap<K extends object, V>(map: ReadonlyMap<K, V>, key: K): V {
  const value = map.get(key);
  if (value === undefined) throw new Error("decompositionCompare: 対応する添字が見つからない(内部不整合)");
  return value;
}

/**
 * 決-F/決-G/決-H/決-I。`actualDoc` と `gold` を、文書全体の最大重みマッチングで claim ごとに
 * 対応付ける。既存の `compareClaimDecomposition` の出力・挙動には一切影響しない(決-A。補助関数も
 * 共有しない)。
 *
 * ここでは「正準順序」(span 昇順 → claim_id 昇順)で `goldIndex`/`actualIndex` の添字を割り付ける
 * ためだけに `compareWeightedClaims` でいったん並べ替え、実際の対応付けは `matchClaimsBySentence`
 * (この並べ替えに依存しない、決-J の S-B が直接確かめる関数)へ委譲する。
 */
export function compareClaimDecompositionBySentence(actualDoc: unknown, gold: GoldFixtureLike): SentenceAwareCompareResult {
  const sentences = splitIntoSentences(gold.original_text);
  const canonicalGold = extractWeightedClaims({ claims: gold.expected_claims }).sort(compareWeightedClaims);
  const canonicalActual = extractWeightedClaims(actualDoc).sort(compareWeightedClaims);

  const goldIndexOf = new Map<WeightedClaim, number>();
  canonicalGold.forEach((c, i) => goldIndexOf.set(c, i));
  const actualIndexOf = new Map<WeightedClaim, number>();
  canonicalActual.forEach((c, i) => actualIndexOf.set(c, i));

  const matchResult = matchClaimsBySentence(canonicalGold, canonicalActual, sentences);

  const pairs: SentenceAwareClaimPair[] = matchResult.pairs.map(({ gold: g, actual: a, valueMatch, formMatch }) => {
    // 決-I: 文の正しさは対を作った後に別に判定する(対を作るときの重みのボーナスを流用しない)。
    const hostG = hostSentenceOf(sentences, g.span);
    const hostA = hostSentenceOf(sentences, a.span);
    const sameSentence = hostG !== undefined && hostA !== undefined && hostG.start === hostA.start;
    return {
      goldIndex: requireFromRefMap(goldIndexOf, g),
      actualIndex: requireFromRefMap(actualIndexOf, a),
      sameSentence,
      valueMatch,
      formMatch,
    };
  });
  pairs.sort((x, y) => x.goldIndex - y.goldIndex);

  const goldUnmatched = matchResult.goldUnmatched.map((g) => requireFromRefMap(goldIndexOf, g)).sort((a, b) => a - b);
  const actualUnmatched = matchResult.actualUnmatched.map((a) => requireFromRefMap(actualIndexOf, a)).sort((a, b) => a - b);

  const sentenceCorrect = pairs.filter((p) => p.sameSentence).length;

  return { pairs, goldUnmatched, actualUnmatched, sentenceCorrect };
}
