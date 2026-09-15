// STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §1 の M-5・M-6)。1 つの評価を形勢の状態(ahead / level / behind / undetermined)に分け、
// 組の直前と直後の状態を並べる純粋関数。
//
// 【このファイルがやること】評価の状態が measured でなければ undetermined(理由は状態の名前をそのまま)、mate は符号で、cp は境の値で分ける
//
// 【このファイルが絶対にやらないこと】
// - 「越えた」「崩れた」などの判定語を欄にすること(順序で下がったかは読む側が数える ― M-6)。優勢・互角・劣勢の文を作ること(D6)
// - 境の値を置くこと(呼び出し側が渡す。値は lib/failureEvent.ts の STANDING_BOUNDS)
// - measured でない評価・mate 0 を level に畳むこと
//
// 【判断的知識】境 +300 / −300・mate は符号で・mate 0 は undetermined は人間の承認済み(2026-09-15、2fe81c3)。境を含むのは計画 Q-5 の推奨どおり。
// 状態の順序(ahead > level > behind)で下がったかを読む側が数えることは、推奨どおりの仮置き(draft。結果の表と一緒に人間に確認する)

import type { Evaluation, EvaluationState } from "./failureEvent.js";

export interface StandingBounds {
  /** これ以上の scoreCp は ahead(境を含む) */
  aheadCp: number;
  /** これ以下の scoreCp は behind(境を含む) */
  behindCp: number;
}

/** undetermined の理由。評価の状態の名前をそのまま使い、mate 0 だけ `mateZero`(スキーマは mate 0 を通さないので、行には出ない) */
export type UndeterminedReason = Exclude<EvaluationState, "measured"> | "mateZero";

/** `ahead`・`level`・`behind` は境の値の名前であって評価ではない */
export type Standing = "ahead" | "level" | "behind" | { undetermined: UndeterminedReason };

export interface StandingPair {
  before: Standing;
  after: Standing;
}

export function standingOf(evaluation: Evaluation, bounds: StandingBounds): Standing {
  if (evaluation.state !== "measured") return { undetermined: evaluation.state };
  if (evaluation.mate !== null) {
    if (evaluation.mate > 0) return "ahead";
    if (evaluation.mate < 0) return "behind";
    return { undetermined: "mateZero" };
  }
  if (evaluation.scoreCp === null) {
    // evaluationOf は scoreCp も mate も null の行を notMeasurable にするので、ここには来ない(来たら黙って level にしない)
    throw new Error("measured の評価に scoreCp も mate も無い");
  }
  if (evaluation.scoreCp >= bounds.aheadCp) return "ahead";
  if (evaluation.scoreCp <= bounds.behindCp) return "behind";
  return "level";
}

/** 組の直前の行と直後の行の状態を並べるだけ */
export function standingPairOf(before: Evaluation, after: Evaluation, bounds: StandingBounds): StandingPair {
  return { before: standingOf(before, bounds), after: standingOf(after, bounds) };
}
