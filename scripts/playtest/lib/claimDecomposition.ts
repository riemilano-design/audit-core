// D-1(audit-core/docs/CLAIM_DECOMPOSITION_D1_PLAN_2026-10-07.md §4)。原文(LLM の席が出した文字列)を
// Claim(契約 claim-decomposition v0.1。schemas/claim-decomposition.v0.1.schema.json)へ分解した結果を、
// schema が確かめられない 2 点について機械で検査する。
//
// 【このファイルがやること】
// - `decompositionProblems(doc)`: span の門。claim_id の重複・span の範囲・span が original_text の
//   実在する文字(サロゲートペアを分断しない)を指しているかを確かめる(§4(b)「部分一致で通さない」の規律)。
//   1 件見つけても止めない ― 全 claim を見て、見つかった問題を全部返す(短絡しない)。
// - `coverageReport(doc)`: 被覆の測定(§4(d))。原文のうち「数が書いてあるのに、どの claim の span にも
//   覆われていない文」を数える。
// - `checkClaimDecomposition(doc)`: schema 照合(`loadClaimDecompositionSchema` + `validate`)と
//   `decompositionProblems` の両方を必ず呼ぶ唯一の入口(独立監査 REVISE への対応)。呼び出し側がどちらか
//   一方だけを呼んで schema 照合を省略できる経路を残さないため、将来この文書を検査するコードは
//   `decompositionProblems` を直接呼ぶのではなくこちらを呼ぶ。
//
// 【このファイルが絶対にやらないこと】
// - Claim が「正しいか」の判断(§3「正しさの判定は Core が行い、分解の正しさは独立に測る」)。
// - 席の呼び出し・実 run(D-1 は LLM を 1 回も呼ばない。計画 §4)。
//
// 【span の検査の規律】`lib/hypothesis.ts` の `verifiedSpans` / `isFullyCoveredBySpan` と同じ規律
// (部分的な重なりは通さない)を使う(計画 §5 設計判断 5)。ただし分解層の claim は自分の span を
// 自己申告するため、ここでの検査は「申告された span が、原文に対して索引としても内容としても
// 実在するか」(decompositionProblems)と、「数の入った文が、申告された span のどれかに
// 完全に覆われているか」(coverageReport)の 2 つに分けている。

import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";

export const CLAIM_DECOMPOSITION_SCHEMA_VERSION = "0.1" as const;

/** スキーマのファイル(scripts/playtest/schemas/claim-decomposition.v<version>.schema.json)を読む。 */
export function loadClaimDecompositionSchema(version: string = CLAIM_DECOMPOSITION_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/claim-decomposition.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isHighSurrogate(code: number): boolean {
  return code >= 0xd800 && code <= 0xdbff;
}

function isLowSurrogate(code: number): boolean {
  return code >= 0xdc00 && code <= 0xdfff;
}

/**
 * span `[start, end)` が、`text` の実在する文字をちょうど指しているかを確かめる。
 * 索引の範囲(0 <= start < end <= text.length)だけでなく、**その位置の文字列**(`text.slice(start, end)`)が
 * 申告された長さと一致すること(JS の `slice` は範囲外を例外にせず黙って切り詰める ― 索引の数の比較だけでは
 * 見つからない)、かつ境界がサロゲートペアの内側(UTF-16 のコード単位 1 つが「半分の文字」になる位置)を
 * 割っていないことまで確かめる。問題が無ければ `null`。
 */
function spanRealityProblem(span: readonly [number, number], text: string): string | null {
  const [start, end] = span;
  if (!Number.isInteger(start) || !Number.isInteger(end)) return `span の要素が整数ではない([${start}, ${end}])`;
  if (start < 0) return `span の start が負(${start})`;
  if (end <= start) return `span が空か逆転している(start=${start}, end=${end})`;
  if (end > text.length) return `span の end(${end})が original_text の長さ(${text.length})を超えている`;
  const sliced = text.slice(start, end);
  if (sliced.length !== end - start) {
    return `span の位置の文字列の長さ(${sliced.length})が申告された長さ(${end - start})と一致しない`;
  }
  if (isHighSurrogate(text.charCodeAt(start - 1)) && isLowSurrogate(text.charCodeAt(start))) {
    return `span の start(${start})がサロゲートペアの中を指している`;
  }
  if (isHighSurrogate(text.charCodeAt(end - 1)) && isLowSurrogate(text.charCodeAt(end))) {
    return `span の end(${end})がサロゲートペアの中を指している`;
  }
  return null;
}

/**
 * span の門(計画 §4(b))。`doc` の `claims[]` を全部見て、見つかった問題を全部返す(1 件で止めない)。
 * `doc` は schema 照合を経ていない可能性がある値として扱う(防御的に型を確かめる)。
 */
export function decompositionProblems(doc: unknown): string[] {
  const problems: string[] = [];
  if (!isRecord(doc)) {
    problems.push("doc がオブジェクトではない");
    return problems;
  }
  const originalText = doc["original_text"];
  if (typeof originalText !== "string") {
    problems.push("original_text が文字列ではない");
    return problems;
  }
  const claims = doc["claims"];
  if (!Array.isArray(claims)) {
    problems.push("claims が配列ではない");
    return problems;
  }

  const seenIds = new Set<string>();
  claims.forEach((claim, index) => {
    const label = `claims[${index}]`;
    if (!isRecord(claim)) {
      problems.push(`${label}: claim がオブジェクトではない`);
      return;
    }

    const claimId = claim["claim_id"];
    if (typeof claimId !== "string" || claimId === "") {
      problems.push(`${label}: claim_id が無い`);
    } else {
      if (seenIds.has(claimId)) problems.push(`${label}: claim_id "${claimId}" が文書内で重複している`);
      seenIds.add(claimId);
    }

    const span = claim["span"];
    if (!Array.isArray(span) || span.length !== 2) {
      problems.push(`${label}: span が長さ 2 の配列ではない(${Array.isArray(span) ? span.length : typeof span})`);
      return;
    }
    const [start, end] = span as [unknown, unknown];
    if (typeof start !== "number" || typeof end !== "number") {
      problems.push(`${label}: span の要素が数ではない`);
      return;
    }
    const problem = spanRealityProblem([start, end], originalText);
    if (problem !== null) problems.push(`${label}: ${problem}`);
  });

  return problems;
}

export interface ClaimDecompositionCheckResult {
  /** schema 照合(`form`・`subject`・`value`・`modifiers`・`evidence_pointer` など、schema が扱うキーワードで確かめられる誤り)。 */
  schemaErrors: string[];
  /** `decompositionProblems` が返す、schema では確かめられない誤り(span が原文に実在するか・claim_id の重複)。 */
  decompositionProblems: string[];
  /** `schemaErrors` と `decompositionProblems` を連結した全問題(呼び出し側が「問題が 1 件もないか」だけを見たいとき用)。 */
  problems: string[];
}

/**
 * Claim Decomposition 文書を検査する唯一の入口(監査 REVISE (2) への対応)。
 * schema 照合(`loadClaimDecompositionSchema` + `validate`)と `decompositionProblems` の
 * **両方を必ず呼ぶ** ― どちらか一方だけを呼んで他方を省略できる経路を作らない。
 * 呼び出し側(将来の統合層)は、この関数だけを呼べば両方の検査を受けたことになる。
 */
export function checkClaimDecomposition(
  doc: unknown,
  version: string = CLAIM_DECOMPOSITION_SCHEMA_VERSION,
): ClaimDecompositionCheckResult {
  const schema = loadClaimDecompositionSchema(version);
  const schemaErrors = validate(doc, schema);
  const problems = decompositionProblems(doc);
  return { schemaErrors, decompositionProblems: problems, problems: [...schemaErrors, ...problems] };
}

/** 全角数字を同じ位置の半角数字に置き換える(1 文字 → 1 文字。`lib/hypothesis.ts` の `normalizeFullWidthDigits` と同じ規律)。 */
function normalizeFullWidthDigits(text: string): string {
  return text.replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xff10 + 0x30));
}

interface NumberToken {
  start: number;
  end: number;
}

/** `text` の中の数字の並び(半角・全角どちらも)の位置を、半開区間 `[start, end)` の配列で返す。 */
function extractNumberTokens(text: string): NumberToken[] {
  const normalized = normalizeFullWidthDigits(text);
  const out: NumberToken[] = [];
  const re = /\d+(?:\.\d+)?/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(normalized)) !== null) {
    out.push({ start: match.index, end: match.index + match[0].length });
  }
  return out;
}

interface SentenceSpan {
  text: string;
  start: number;
  end: number;
}

/**
 * 原文を文に切る。**句点「。」を文の切れ目とし、「。」自身は直前の文に含める**(句点が無い末尾の断片も
 * 1 文として扱う)。読点「、」・改行では切らない ― 被覆判定の単位(「1 文の中に数があるか」)を、
 * 読点でこまぎれにして過剰に `uncovered` を出さないため、句点だけを切れ目にする(このファイルの決定。
 * 計画 §4(d) は切り方を指定していない)。
 *
 * **直前の句点に続く改行は、次の文の一部にしない。** 原文は段落の区切りに改行(1 個または連続した複数個)を
 * 使うが、改行そのものは文の内容ではなく空白の区切りである。句点を見つけて次の文の開始位置を定めるとき、
 * そこに続く「\n」を読み飛ばしてから次の文の `start` を確定する(「改行で文を切らない」=「改行を区切り文字
 * として扱わない」ことと、「改行を次の文の文字列に含めない」ことは別の決定であり、ここでは後者も行う)。
 * これは境界そのものの決定であり、呼び出し側で出力文字列を `.trim()` して吸収する話ではない ―
 * gold fixture(`fixtures/decomposition/gold_01.json` の note)は「span は文そのものの区間(句点を含み、
 * 改行は含まない)」という取り決めで claim の span を書いており、この関数が返す `sentence.start`/`text` も
 * 同じ取り決めに合わせる必要がある(そうしないと、この関数が返す sentence の境界と、独立に作られた正解
 * 集合の span の境界が食い違ったままになる)。
 */
function splitIntoSentences(text: string): SentenceSpan[] {
  const sentences: SentenceSpan[] = [];
  let start = 0;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === "。") {
      sentences.push({ text: text.slice(start, i + 1), start, end: i + 1 });
      start = i + 1;
      while (text[start] === "\n") start++;
    }
  }
  if (start < text.length) sentences.push({ text: text.slice(start), start, end: text.length });
  return sentences;
}

const HAS_DIGIT = /[0-9０-９]/;

/** `num`(絶対位置)が、`spans` のどれか 1 つに**完全に**入っているか(部分的な重なりは見逃さない)。`lib/hypothesis.ts` の `isFullyCoveredBySpan` と同じ規律。 */
function isFullyCoveredBySpan(token: NumberToken, spans: ReadonlyArray<readonly [number, number]>): boolean {
  return spans.some(([s, e]) => s <= token.start && token.end <= e);
}

export interface CoverageReport {
  /** 原文の文のうち、数字(半角・全角)を含む文(出現順・重複を含む、同じ文字列が複数回出ても複数回入れる)。 */
  numberSentences: string[];
  /** `numberSentences` のうち、文中の数の少なくとも 1 つが、どの claim の span にも完全に覆われていない文。 */
  uncovered: string[];
  /** `(numberSentences.length - uncovered.length) / numberSentences.length`。数字入りの文が 0 件のときは 1(空の母集団は被覆の失敗ではない)。 */
  bindingRate: number;
}

/**
 * 被覆の測定(計画 §4(d))。`doc.original_text` のうち「数が書いてあるのに、どの claim の span にも
 * ならなかった文」を数える。`doc` が壊れている(claims が配列でない等)場合は、健全化した
 * (claims を空扱いにした)状態で測る ― decompositionProblems が構造の誤りを別に報告する。
 */
export function coverageReport(doc: unknown): CoverageReport {
  const originalText = isRecord(doc) && typeof doc["original_text"] === "string" ? (doc["original_text"] as string) : "";
  const rawClaims = isRecord(doc) && Array.isArray(doc["claims"]) ? (doc["claims"] as unknown[]) : [];

  const spans: Array<[number, number]> = [];
  for (const claim of rawClaims) {
    if (!isRecord(claim)) continue;
    const span = claim["span"];
    if (!Array.isArray(span) || span.length !== 2) continue;
    const [start, end] = span as [unknown, unknown];
    if (typeof start !== "number" || typeof end !== "number") continue;
    // 被覆の測定は「門を通った span だけ」を信用する(範囲外・分断された span を覆っている扱いにしない)。
    if (spanRealityProblem([start, end], originalText) !== null) continue;
    spans.push([start, end]);
  }

  const allTokens = extractNumberTokens(originalText);
  const numberSentences: string[] = [];
  const uncovered: string[] = [];
  for (const sentence of splitIntoSentences(originalText)) {
    if (!HAS_DIGIT.test(sentence.text)) continue;
    numberSentences.push(sentence.text);
    const tokens = allTokens.filter((t) => t.start >= sentence.start && t.end <= sentence.end);
    const allCovered = tokens.length > 0 && tokens.every((t) => isFullyCoveredBySpan(t, spans));
    if (!allCovered) uncovered.push(sentence.text);
  }

  const bindingRate = numberSentences.length === 0 ? 1 : (numberSentences.length - uncovered.length) / numberSentences.length;
  return { numberSentences, uncovered, bindingRate };
}
