// STEP T-6(B-2)。docs/STEP_T-6_PLAN_2026-09-11.md 2. B-2に従う。
//
// 提案書(docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.3)は「recorder.tsに1項目足す」
// としているが、S1の選択規則(scripts/playtest/lib/players.ts pickByS1Rule)は
// 直前のready行の既存フィールドだけで決まる(STEP T-6計画書1. F-9)ため、記録には
// 何も足さず、この純粋関数で直前のready行から事後に導く。JSONLの形式は変えない。
//
// 【この値の意味の範囲について(必ず読むこと。計画レビューのREVISEを受けた論点)】
// この関数が返す値は「その手が、直前に画面へ出ていた助言(候補手または道のりの
// 一手)と一致した」ことを意味するのであり、「助言に従った」ことを意味しない。
// 「従った」と言えるのは、選択規則がその助言を実際に参照しているS1
// (および②③でS1規則へフォールバックした手を選んだS2・S3)だけであり、E・Rの手は
// 助言を参照せずに決まるため、一致は偶然でありうる。固定棋譜(人間の対局。C-1の
// 事故を含む)は選択の由来(どの規則で選ばれたか)が記録に無いため、区別せず
// 「一致」として扱う。この区別は invariants/i6-advice-then-loss.ts の detail文・
// scripts/playtest/README.md にも明示する。

import type { RecordLine } from "../invariants/types.js";

export type AdviceSource = "candidate" | "route" | "none";

/**
 * 直前のready行(previousReady。無ければ"none")と、その次に指された手
 * (senteMove)から、adviceSourceを導く。
 * ① previousReady.response.plan.candidateMove.status === "ready" かつ
 *    explanations.some(e => e.move === senteMove) なら "candidate"。
 * ② そうでなく candidateMoveLabels のキーに senteMove が含まれれば "route"。
 * ③ それ以外(previousReadyが無い場合を含む)は "none"。
 */
export function deriveAdviceSource(
  previousReady: RecordLine | undefined,
  senteMove: string,
): AdviceSource {
  if (!previousReady) return "none";

  const { plan } = previousReady.response;
  const candidateMove = plan.candidateMove;
  if (candidateMove?.status === "ready" && candidateMove.explanations.some((e) => e.move === senteMove)) {
    return "candidate";
  }

  if (Object.keys(plan.candidateMoveLabels).includes(senteMove)) {
    return "route";
  }

  return "none";
}
