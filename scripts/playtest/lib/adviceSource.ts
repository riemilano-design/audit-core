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

export type AdviceSource = "candidate" | "route" | "band" | "none";

/**
 * [0]「今すぐ対処が必要なこと」(帯)の piece_attacked が名指しした、自分の駒のマス。
 *
 * 【なぜ型を広げて読むか】
 * 本番の宣言型 ReachablePlanBody.urgentMessages は { kind: string; text: string }[] で、
 * square を持たない。しかし [0] の piece_attacked は PieceThreatMessage
 * (analysis/pieceThreatDetector.ts)がそのまま連結されたもの
 * (api/stateResponse.ts partitionUrgentMessages)であり、実データには square がある
 * (本作業の固定棋譜4局では piece_attacked 66件すべてに string の square があった)。
 * apps/ の型を広げるのは本STEPの範囲外(scripts/playtest/ のみ)なので、ここでは
 * ハーネス側の局所的な型で読み、typeof の実行時ガードを置く。square が無い行は
 * 「名指ししていない」として静かに落とす(推測しない)。
 */
interface BandMessageLike {
  kind: string;
  square?: unknown;
}

const BAND_PIECE_ATTACKED_KIND = "piece_attacked";

/** 直前のready行の帯が名指しした自分の駒のマスの一覧(順序は画面の並びのまま)。 */
export function listBandNamedSquares(previousReady: RecordLine | undefined): string[] {
  if (!previousReady) return [];
  const messages = previousReady.response.plan.urgentMessages as unknown as BandMessageLike[];
  return messages
    .filter((m) => m.kind === BAND_PIECE_ATTACKED_KIND && typeof m.square === "string")
    .map((m) => m.square as string);
}

/**
 * senteMove が「帯が名指しした駒を動かす手」かどうか。
 * ドロップ(打つ手)は盤上の駒を動かさないため常に false。
 *
 * I-8 はこの述語を直接使い、deriveAdviceSource の戻り値("band")には依存しない。
 * 理由: deriveAdviceSource は1つの値しか返さないため、候補手にも載っていて
 * かつ帯の駒でもある手は "candidate" になる。"band" だけを見ると、その重なりを
 * 取りこぼす。重なりは I-8 の finding の condition に残して見えるようにする。
 */
export function movesBandNamedPiece(previousReady: RecordLine | undefined, senteMove: string): boolean {
  if (senteMove.includes("*")) return false;
  return listBandNamedSquares(previousReady).includes(senteMove.slice(0, 2));
}

/**
 * 直前のready行(previousReady。無ければ"none")と、その次に指された手
 * (senteMove)から、adviceSourceを導く。
 * ① previousReady.response.plan.candidateMove.status === "ready" かつ
 *    explanations.some(e => e.move === senteMove) なら "candidate"。
 * ② そうでなく candidateMoveLabels のキーに senteMove が含まれれば "route"。
 * ③ そうでなく、帯([0]の piece_attacked)が名指しした駒を動かす手なら "band"
 *    (STEP T-8 で追加)。
 * ④ それ以外(previousReadyが無い場合を含む)は "none"。
 *
 * 【STEP T-8 で "band" を足したときの順序について】
 * "band" は必ず ①② の後に判定する。こうすることで、既存の I-6
 * (adviceSource が candidate/route の行だけを見る)の挙動は一切変わらない
 * (以前 "none" だった一部の手が "band" になるだけで、candidate/route の
 * 判定結果は同じ)。
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

  if (movesBandNamedPiece(previousReady, senteMove)) {
    return "band";
  }

  return "none";
}
