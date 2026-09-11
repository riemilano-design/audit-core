// I-7(沈黙、draft): 「先に言うべき事実があるのに、別の話をしている」を検出する
// (提案書4.4の述語案。2026-09-11人間決定。閾値300cpはdraftの初期値)。
//
// 出典: docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.4、
// docs/STEP_T-7_PLAN_2026-09-11.md 2. B-1(人間決定: 閾値300cpはdraftの初期値。
// 完了条件は「固定棋譜のply 16で発火」かつ「探索10局で毎手発火しない」)。
//
// 【この不変条件の意味の範囲について(必ず読むこと)】
// - I7_DROP_THRESHOLD_CP = 300 は、本アプリ内のdraftの初期値であり、将棋一般の
//   閾値ではない。approved化の前に人間が再判断する(本ファイル・本STEPの完了条件
//   以外で、この数値を根拠に良し悪しを断定しない)。
// - これは「最善手を言え」ではない。「先に言うべき事実(相手が捕獲を含む手を
//   選ぶと評価が大きく落ちる局面であること)があるのに、画面が道のり・候補手の
//   進捗など別の話をしている」ことを、盤の事実とエンジンの参考評価から拾う
//   ものであり、候補手そのものの良し悪し(最善手かどうか)は判断しない。
//
// 判定:
// - 緊急事態(エンジンの事実): engineReferenceがあり、dropCp !== null かつ
//   dropCp >= I7_DROP_THRESHOLD_CP、かつ afterPass.captureSquare !== null
//   (パスすると相手の最善手が捕獲を含む)、かつ captureSquareの駒が
//   listAttackedPieces(record.sfen, "sente") → detectPieceThreats(...)の
//   結果に含まれる(square一致。[0]「今すぐ対処が必要なこと」の対象駒種
//   (飛・角・金・銀・桂・香)と同じ集合に限る。2026-09-11人間決定)。
// - 別の話(画面の事実、いずれか。conditionに種別を残す):
//   - urgent_empty: plan.urgentMessagesが空
//   - route_shown: plan.routes.length > 0、または candidateMove.status ===
//     "ready" かつ explanationsが1件以上、または lastMoveOutcome.messagesに
//     kind: "route_advanced"/"route_completed"/"route_first_move_available"/
//     "played_candidate" のいずれかがある
// - 検出しない: engineReferenceがnull(測っていない)、終局。captureSquareの
//   駒が[0]の対象駒種でない(歩・成駒等)。urgentMessagesにcaptureSquareの
//   マスを述べるpiece_attackedがあっても、route_shownに該当すれば検出する
//   ([0]が当たりを述べていても道のりの進捗を並べればC-1の事故は起きる。
//   docs/STEP_T-7_PLAN_2026-09-11.md F-2・F-5)。
//
// 2026-09-11人間決定(docs/OBSERVATION_I6_I7_2026-09-11.md 4.): 緊急事態の対象
// 駒種を[0]と同じ集合(飛・角・金・銀・桂・香)に狭めた(urgent_emptyの7件は
// 歩6・と金1で、[0]の対象外の駒だった)。

import { listAttackedPieces } from "../../../apps/server/src/rules/attackedPieces.js";
import { detectPieceThreats } from "../../../apps/server/src/analysis/pieceThreatDetector.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-7";

/** draftの初期値(2026-09-11人間決定)。将棋一般の閾値ではない。 */
export const I7_DROP_THRESHOLD_CP = 300;

const ROUTE_PROGRESS_KINDS = new Set([
  "route_advanced",
  "route_completed",
  "route_first_move_available",
  "played_candidate",
]);

function isUrgentEmpty(record: RecordLine): boolean {
  return record.response.plan.urgentMessages.length === 0;
}

/** route_shownに該当する場合、detailに残す種別(routes/candidate_move_ready/
 * lastMoveOutcomeのkind)を返す。該当しなければnull。 */
function routeShownReason(record: RecordLine): string | null {
  const { plan } = record.response;
  if (plan.routes.length > 0) return "routes";

  const candidateMove = plan.candidateMove;
  if (candidateMove?.status === "ready" && candidateMove.explanations.length > 0) {
    return "candidate_move_ready";
  }

  const messages = plan.lastMoveOutcome?.messages ?? [];
  const found = messages.find((m) => ROUTE_PROGRESS_KINDS.has(m.kind));
  return found?.kind ?? null;
}

export const i7UrgentButOtherTalk: Invariant = {
  id: ID,
  title: "パスすると評価が大きく落ち相手の最善が捕獲を含む局面([0] の対象駒が取られる局面)で、[0] が空、または画面が道のり・候補手の進捗を示している",
  type: "沈黙",
  status: "draft",
  source: "docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.4(閾値300cpは2026-09-11人間決定のdraft初期値)",
  check(records: RecordLine[]): Finding[] {
    const findings: Finding[] = [];

    for (const record of records) {
      if (record.phase !== "ready") continue;
      if (record.response.status.isEnd) continue;

      const engineReference = record.engineReference;
      if (!engineReference) continue;

      const { dropCp, afterPass } = engineReference;
      if (dropCp === null || dropCp < I7_DROP_THRESHOLD_CP) continue;
      if (afterPass.captureSquare === null) continue;

      const facts = detectPieceThreats(listAttackedPieces(record.sfen, "sente"));
      const isTargetedPiece = facts.some((f) => f.square === afterPass.captureSquare);
      if (!isTargetedPiece) continue;

      let condition: "urgent_empty" | "route_shown" | null = null;
      let conditionText = "";
      if (isUrgentEmpty(record)) {
        condition = "urgent_empty";
        conditionText = "[0] が空です。";
      } else {
        const reason = routeShownReason(record);
        if (reason !== null) {
          condition = "route_shown";
          conditionText = `画面が道のり・候補手を示しています(${reason})。`;
        }
      }
      if (condition === null) continue;

      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition,
        detail: `パスすると先手視点で約 ${dropCp}cp 落ち、相手の最善 ${afterPass.bestmove ?? "不明"} が ${afterPass.captureSquare} の駒を取る局面で、${conditionText}`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
