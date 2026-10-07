// D-2b-0(audit-core/docs/CLAIM_DECOMPOSITION_D2B0_PLAN_2026-10-07.md §2(c))。
// 「基準線の分解器」― LLM を 1 回も呼ばない、規則ベースの素朴な分解器。
//
// 【これが測るもの】LLM の分解器(D-2b)を作る前に、「何もしない規則」がどこまで届くかという下限。
// 分解器としての実用性は求めない。
//
// 【span の定義(司令塔の仕様の誤りの訂正・2026-10-07)】計画 §2(c) の「数のある文を 1 claim として」は
// 文全体を指す。claim の span は「その主張を述べている文そのものの区間」であり、文中で拾った数字の
// 位置(例: "100" の 3 文字)ではない。正解集合 4 本はすべて「span は文そのものの区間(句点を含み、
// 改行は含まない)」という取り決めで書かれており、基準線もこの取り決めに合わせる。
//
// 【やること】`lib/claimDecomposition.ts` の `splitIntoSentences` で原文を文に切り(句点「。」が
// 境界、句点は直前の文に含む、改行は次の文に含めない ― splitIntoSentections 自身の規約)、各文の中で
// 最初に出てくる数字の並び(ASCII の `\d+(?:\.\d+)?` だけ。全角数字は扱わない)を 1 つだけ拾って
// `value` にし、その文の span([sentence.start, sentence.end))を claim の span にする
// (`form: "direct_value"` 固定)。文に数字が無ければ claim を作らない。1 つの文に複数の数字があっても、
// 2 件目以降は無視する(アルゴリズムを賢くしない ― 計画 §2(c)「良くする努力をしない」)。
//
// 【`splitIntoSentences` を共有する理由】測っているのは「どの文が claim になり、value と form が
// 何になるか」であって、文の切り方そのものではない。切り方を基準線だけ別実装にすると、「切り方の違い」
// と「claim の選び方の違い」が混ざって、どちらを測ったのか分からなくなる(司令塔の判断・2026-10-07)。
//
// 【このファイルが絶対にやらないこと】
// - 全角数字・漢数字の認識。
// - 文脈からの `form`(derived_value/aggregate/threshold)の推定 ― 常に `direct_value`。
// - `subject` の内容推定(常に文そのもの)・`unit`・`modifiers` の内容推定(常に null)。
// - `lib/claimDecomposition.ts` の `extractNumberTokens`(数字トークンの抽出)の呼び出し・流用 ―
//   数字を拾う正規表現は基準線が自分で持つ(全角数字を拾わない基準線の既知の限界を保つため)。

import { splitIntoSentences } from "./claimDecomposition.js";

export interface BaselineClaim {
  claim_id: string;
  span: [number, number];
  form: "direct_value";
  subject: string;
  value: number;
  unit: null;
  modifiers: { population: null; time_range: null; normalization: null };
  evidence_pointer: null;
}

export interface BaselineDoc {
  schemaVersion: "0.1";
  original_text: string;
  claims: BaselineClaim[];
}

const FIRST_NUMBER = /\d+(?:\.\d+)?/;

/**
 * `originalText` を `splitIntoSentences` で文に切り、各文の最初の数字だけを 1 claim として当てる。
 * claim の span は、その文そのものの区間(`[sentence.start, sentence.end)`)― 拾った数字の位置ではない
 * (このファイル先頭のコメント「span の定義」を見る)。
 */
export function baselineDecompose(originalText: string): BaselineDoc {
  const claims: BaselineClaim[] = [];

  let claimIndex = 0;
  for (const sentence of splitIntoSentences(originalText)) {
    const match = FIRST_NUMBER.exec(sentence.text);
    if (match !== null) {
      claimIndex += 1;
      claims.push({
        claim_id: `c${claimIndex}`,
        span: [sentence.start, sentence.end],
        form: "direct_value",
        subject: sentence.text,
        value: Number(match[0]),
        unit: null,
        modifiers: { population: null, time_range: null, normalization: null },
        evidence_pointer: null,
      });
    }
  }

  return { schemaVersion: "0.1", original_text: originalText, claims };
}
