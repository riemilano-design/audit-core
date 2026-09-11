// I-1(沈黙、approved): 候補手が安全確認で全件除外されているのに、除外を伝える
// メッセージが存在せず、道のり([4])だけがそのまま表示され続けている状態を検出する。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md 付録A C-1、STEP 4-2 完了記録(Unit 5の論点として
// 持ち越し)。plan.candidateMoveState/candidateMove/notReadyReason/routes/
// nextConsiderationsはいずれもapps/server/src/api/stateResponse.ts の既存フィールドを
// そのまま読むだけで、このファイルでは新しい判定・文言を作らない。
//
// 検査対象はphase:"ready"の行のみ(計画書の原則どおり)。
//
// 【STEP 5-1(C-1、人間承認済み)】発火条件を「routes.length > 0」または
// 「nextConsiderationsにkind: "candidate_moves_excluded"が無い」のORへ厳しくした
// (条件を緩めていない。除外の事実を伝えるメッセージがあり、かつroutesも空の場合
// だけ発火しなくなる)。除外の事実をnextConsiderationsへ足す側(A-3)は
// api/stateResponse.tsの責務で、ここでは既に確定した値を読むだけ。

import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-1";
const EXCLUSION_NOTICE_KIND = "candidate_moves_excluded";

function checkRecord(record: RecordLine): Finding | null {
  if (record.phase !== "ready") return null;
  const { response } = record;
  if (response.status.isEnd) return null;

  const { plan } = response;
  if (plan.candidateMoveState !== "ready") return null;
  const candidateMove = plan.candidateMove;
  if (!candidateMove || candidateMove.status !== "not_ready") return null;
  if (candidateMove.notReadyReason !== "excluded_by_reference_evaluation") return null;

  const hasExclusionNotice = plan.nextConsiderations.some((m) => m.kind === EXCLUSION_NOTICE_KIND);
  if (plan.routes.length === 0 && hasExclusionNotice) return null;

  return {
    invariantId: ID,
    kifuId: "",
    ply: record.ply,
    phase: record.phase,
    condition: candidateMove.notReadyReason,
    detail: `候補手が全件除外(notReadyReason: ${candidateMove.notReadyReason})されているが、道のりは ${plan.routes.length} 件表示されたままで、除外を伝えるメッセージ(${EXCLUSION_NOTICE_KIND})は${hasExclusionNotice ? "あります" : "ありません"}。`,
    sfen: record.sfen,
    senteMove: record.senteMove,
    goteMove: record.goteMove,
  };
}

export const i1SilentExclusion: Invariant = {
  id: ID,
  title: "候補手が全件除外されても、道のりが沈黙したまま表示され続ける",
  type: "沈黙",
  // STEP 5-1(H-3、2026-09-11人間承認): このファイル冒頭の「このファイル自体には
  // approvedの値を一切書かない」(types.tsコメント)はT-2時点の記述であり、
  // I-1はC-1(条件を厳しくする)の後、2026-09-11の人間承認でapprovedになった。
  status: "approved",
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
