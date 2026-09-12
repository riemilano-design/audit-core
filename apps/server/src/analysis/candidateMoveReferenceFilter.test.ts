import { describe, expect, it } from "vitest";
import {
  filterCandidateMovesByReferenceEvaluation,
  REFERENCE_DROP_THRESHOLD_CP,
} from "./candidateMoveReferenceFilter.js";
import type { CandidateMoveSafetyCheckResult } from "./candidateMoveSafetyCheck.js";

// filterCandidateMovesByReferenceEvaluationが実際に受け取るのはbaselineMultiPvと
// evaluationsだけ(Pick<CandidateMoveSafetyCheckResult, ...>)なので、テストでも
// その2フィールドだけを組み立てる。
function makeInput(
  baselineMultiPv: CandidateMoveSafetyCheckResult["baselineMultiPv"],
  evaluations: CandidateMoveSafetyCheckResult["evaluations"],
): Pick<CandidateMoveSafetyCheckResult, "baselineMultiPv" | "evaluations"> {
  return { baselineMultiPv, evaluations };
}

function evaluation(
  score: CandidateMoveSafetyCheckResult["evaluations"][number]["multiPv"][number]["score"],
): CandidateMoveSafetyCheckResult["evaluations"][number] {
  return { moveUsi: "dummy", resultingSfen: "startpos", multiPv: score === undefined ? [] : [{ multipv: 1, score, pv: [], lowerbound: false, upperbound: false }] };
}

describe("filterCandidateMovesByReferenceEvaluation", () => {
  it("低下がREFERENCE_DROP_THRESHOLD_CP(300cp)以上なら除外する", () => {
    const input = makeInput(
      [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "cp", value: REFERENCE_DROP_THRESHOLD_CP })],
    );

    const result = filterCandidateMovesByReferenceEvaluation(input);

    expect(result.baselineUnavailable).toBe(false);
    expect(result.excluded).toEqual([true]);
  });

  it("低下が閾値未満なら除外しない", () => {
    const input = makeInput(
      [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "cp", value: REFERENCE_DROP_THRESHOLD_CP - 1 })],
    );

    const result = filterCandidateMovesByReferenceEvaluation(input);

    expect(result.excluded).toEqual([false]);
  });

  it("候補手後(相手視点)がmateで正の値(自分が詰まされる)なら、基準局面の状態に関わらず除外する", () => {
    const inputWithCpBaseline = makeInput(
      [{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "mate", value: 1 })],
    );
    const inputWithMateBaseline = makeInput(
      [{ multipv: 1, score: { type: "mate", value: 5 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "mate", value: 1 })],
    );

    expect(filterCandidateMovesByReferenceEvaluation(inputWithCpBaseline).excluded).toEqual([true]);
    expect(filterCandidateMovesByReferenceEvaluation(inputWithMateBaseline).excluded).toEqual([true]);
  });

  it("基準局面がmateの場合、低下比較は行わない(mateで負=自分が詰ますなら除外しない)", () => {
    const input = makeInput(
      [{ multipv: 1, score: { type: "mate", value: 3 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "mate", value: -1 })],
    );

    const result = filterCandidateMovesByReferenceEvaluation(input);

    expect(result.baselineUnavailable).toBe(false);
    expect(result.excluded).toEqual([false]);
  });

  it("基準局面の評価値が取得できない場合(baselineMultiPvが空)、候補手を全件除外する(決定5)", () => {
    const input = makeInput(
      [],
      [evaluation({ type: "cp", value: 0 }), evaluation({ type: "cp", value: 0 })],
    );

    const result = filterCandidateMovesByReferenceEvaluation(input);

    expect(result.baselineUnavailable).toBe(true);
    expect(result.excluded).toEqual([true, true]);
  });

  it("基準局面の評価値が取得できない場合(先頭行にscoreが無い)も、候補手を全件除外する(決定5)", () => {
    const input = makeInput(
      [{ multipv: 1, score: undefined, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "cp", value: 0 })],
    );

    const result = filterCandidateMovesByReferenceEvaluation(input);

    expect(result.baselineUnavailable).toBe(true);
    expect(result.excluded).toEqual([true]);
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    const input = makeInput(
      [{ multipv: 1, score: { type: "cp", value: 10 }, pv: [], lowerbound: false, upperbound: false }],
      [evaluation({ type: "cp", value: 50 }), evaluation({ type: "cp", value: 500 })],
    );

    expect(filterCandidateMovesByReferenceEvaluation(input)).toEqual(filterCandidateMovesByReferenceEvaluation(input));
  });
});
