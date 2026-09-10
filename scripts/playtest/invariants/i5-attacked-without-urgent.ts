// I-5(沈黙、draft): 自分の駒に相手の利きが届いている事実(detectPieceThreats)が
// あるのに、[0]「今すぐ対処が必要なこと」(urgentMessages)に kind: "piece_attacked" が
// 1件も無い状態を検出する。個々の駒への対応までは見ない、粗いdraft。
//
// 出典: docs/PLAYTEST_LOOP_PROPOSAL.md P-3、STEP 4-3 完了記録(回帰確認)。
//
// facts(利きの事実)は listAttackedPieces(rules/attackedPieces.ts)と
// detectPieceThreats(analysis/pieceThreatDetector.ts)を import してそのまま使う。
// 駒種のフィルタ・正規化・並び順は detectPieceThreats が本番と同じ規則で行うため、
// このファイルではフィルタ・正規化を一切書かない。

import { listAttackedPieces } from "../../../apps/server/src/rules/attackedPieces.js";
import { detectPieceThreats, normalizeRole } from "../../../apps/server/src/analysis/pieceThreatDetector.js";
import { roleToJapanese } from "../../../apps/server/src/analysis/pieceMapping.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-5";
const PIECE_ATTACKED_KIND = "piece_attacked";

/** factsの各roleを正規化後の駒名にし、facts の順のまま連結した文字列を作る
 * (束ねるためのcondition。新しい語は作らない)。 */
function factsToCondition(facts: ReturnType<typeof detectPieceThreats>): string {
  return facts.map((f) => roleToJapanese(normalizeRole(f.role)) ?? f.role).join("");
}

export const i5AttackedWithoutUrgent: Invariant = {
  id: ID,
  title: "駒に利きが届いているのに、[0] に当たりの行が無い",
  type: "沈黙",
  status: "draft",
  source: "docs/PLAYTEST_LOOP_PROPOSAL.md P-3、STEP 4-3 完了記録",
  check(records: RecordLine[]): Finding[] {
    const findings: Finding[] = [];

    for (const record of records) {
      if (record.phase !== "ready") continue;
      if (record.response.status.isEnd) continue;

      const facts = detectPieceThreats(listAttackedPieces(record.sfen, "sente"));
      if (facts.length === 0) continue;

      const hasUrgentPieceAttackedMessage = record.response.plan.urgentMessages.some(
        (m) => m.kind === PIECE_ATTACKED_KIND,
      );
      if (hasUrgentPieceAttackedMessage) continue;

      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: factsToCondition(facts),
        detail: `自分の駒 ${facts.length} 件に相手の利きが届いていますが、urgentMessages に "${PIECE_ATTACKED_KIND}" がありません。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
