// I-2(矛盾、draft): 「この手は、直前に表示していた候補手の一つです」
// (lastMoveOutcome.messages の kind: "played_candidate")が出ているのに、
// 直前のready行では実際にはその手を表示していなかった状態を検出する。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md 付録A C-2、P-9。
//
// 判定: ply tのready行にplayed_candidateが出ているとき、同じrunの直前のready行
// (ply t-2)を見て、candidateMove.status === "ready" かつ
// explanations.some(e => e.move === senteMove(t)) が成り立たなければ検出する
// (直前行が無い・candidateMoveが無い・not_readyの場合もすべて「表示していない」)。
//
// このファイルは既存フィールドの突き合わせのみを行い、新しい判定・文言は作らない。

import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-2";
const PLAYED_CANDIDATE_KIND = "played_candidate";

/** records(1run分、ply昇順とは限らないため事前にready行だけをply順に並べたもの)の中から
 * targetPlyのちょうど1つ前(t-2)のready行を探す。 */
function findPreviousReadyRecord(readyRecords: RecordLine[], targetPly: number): RecordLine | undefined {
  return readyRecords.find((r) => r.ply === targetPly - 2);
}

export const i2PlayedCandidateMismatch: Invariant = {
  id: ID,
  title: "「直前に表示していた候補手の一つです」と述べるが、直前は表示していなかった",
  type: "矛盾",
  // STEP 5-1(H-3、2026-09-11人間承認): このファイル冒頭の「このファイル自体には
  // approvedの値を一切書かない」(types.tsコメント)はT-2時点の記述であり、I-2は
  // 2026-09-11の人間承認でapprovedになった(判定条件自体は変えていない、C-2)。
  status: "approved",
  source: "docs/PLAYTEST_LOOP_PROPOSAL.md 付録A C-2、P-9",
  check(records: RecordLine[]): Finding[] {
    const readyRecords = records.filter((r) => r.phase === "ready");
    const findings: Finding[] = [];

    for (const record of readyRecords) {
      const messages = record.response.plan.lastMoveOutcome?.messages ?? [];
      const hasPlayedCandidateMessage = messages.some((m) => m.kind === PLAYED_CANDIDATE_KIND);
      if (!hasPlayedCandidateMessage) continue;
      if (record.senteMove === null) continue;

      const previous = findPreviousReadyRecord(readyRecords, record.ply);
      const previousCandidateMove = previous?.response.plan.candidateMove;
      const previousStatus = previousCandidateMove?.status ?? "none";

      const wasDisplayed =
        previous !== undefined &&
        previousCandidateMove !== undefined &&
        previousCandidateMove.status === "ready" &&
        previousCandidateMove.explanations.some((e) => e.move === record.senteMove);

      if (wasDisplayed) continue;

      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: `${PLAYED_CANDIDATE_KIND}:${previousStatus}`,
        detail: `指し手 ${record.senteMove} について「直前に表示していた候補手の一つです」と述べていますが、直前のready行(ply ${record.ply - 2})の候補手状態は "${previousStatus}" で、この手を含んでいませんでした。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
