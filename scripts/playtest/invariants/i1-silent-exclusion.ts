// I-1(沈黙、draft): 候補手が安全確認で全件除外されているのに、除外を伝えるメッセージが
// 存在せず、道のり([4])だけがそのまま表示され続けている状態を検出する。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md 付録A C-1、STEP 4-2 完了記録(Unit 5の論点として
// 持ち越し)。plan.candidateMoveState/candidateMove/notReadyReason/routesはいずれも
// apps/server/src/api/stateResponse.ts の既存フィールドをそのまま読むだけで、
// このファイルでは新しい判定・文言を作らない。
//
// 検査対象はphase:"ready"の行のみ(計画書の原則どおり)。

import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-1";

function checkRecord(record: RecordLine): Finding | null {
  if (record.phase !== "ready") return null;
  const { response } = record;
  if (response.status.isEnd) return null;

  const { plan } = response;
  if (plan.candidateMoveState !== "ready") return null;
  const candidateMove = plan.candidateMove;
  if (!candidateMove || candidateMove.status !== "not_ready") return null;
  if (candidateMove.notReadyReason !== "excluded_by_reference_evaluation") return null;
  if (plan.routes.length === 0) return null;

  return {
    invariantId: ID,
    kifuId: "",
    ply: record.ply,
    phase: record.phase,
    condition: candidateMove.notReadyReason,
    detail: `候補手が全件除外(notReadyReason: ${candidateMove.notReadyReason})されているが、道のりは ${plan.routes.length} 件表示されたままです。除外を伝えるメッセージはありません。`,
    sfen: record.sfen,
    senteMove: record.senteMove,
    goteMove: record.goteMove,
  };
}

export const i1SilentExclusion: Invariant = {
  id: ID,
  title: "候補手が全件除外されても、道のりが沈黙したまま表示され続ける",
  type: "沈黙",
  status: "draft",
  source: "docs/PLAYTEST_LOOP_PROPOSAL.md 付録A C-1、STEP 4-2 完了記録",
  check(records: RecordLine[]): Finding[] {
    const findings: Finding[] = [];
    for (const record of records) {
      const finding = checkRecord(record);
      if (finding) findings.push(finding);
    }
    return findings;
  },
};
