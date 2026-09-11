// I-6(結果、draft): 直前に画面へ出ていた助言(候補手/道のりの一手)と一致する手を
// 指した直後、相手の応手で駒を取られ、取り返す手が合法手に無い場合を検出する
// (提案書4.3の最小案。2026-09-11人間決定)。
//
// 出典: docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.3(最小案。2026-09-11人間決定)。
//
// 【この検出の意味の範囲について(必ず読むこと。lib/adviceSource.tsと同じ注記)】
// この検出が対象にするのは「直前に画面へ出ていた助言(候補手または道のりの一手)と
// 一致する手」であり、「助言に従った」手ではない。「従った」と言えるのは、選択
// 規則がその助言を実際に参照しているS1(および②③でS1規則へフォールバックした
// S2・S3の手)だけで、E・Rの手は助言を参照せずに決まるため一致は偶然でありうる。
// 固定棋譜(人間の対局)は選択の由来が記録に無いため「一致」として扱う。
// この区別はdetail文でも「従った」と書かず「一致する」と書くことで示す
// (STEP T-6計画書2. B-2)。
//
// 判定(最小案。取り返し以外の損得・単純案(得喪の合計)は扱わない):
// ready行tについて、adviceSource(直前のready行t-2から導く)がcandidate/route
// のとき、本番関数detectBoardEvents(prev.sfen, senteMove, goteMove)の結果に
// captured_by_opponentかつsquareが非nullの事象があり、そのsquareを移動先とする手
// (players.tsのtoSquareOfで判定)がrecord(ply tのready行)のresponse.legalMoves
// に1つも無ければ検出する。将棋の知識(良し悪しの判断)は使わない。
//
// detectBoardEventsが例外を投げた場合は、その行を検出しない(try/catch。
// 推測しない)。
//
// 2026-09-11人間決定(docs/OBSERVATION_I6_I7_2026-09-11.md 4.): 持ち越し。
// 定義を狭める候補として注記のみ残す:「取られた駒が、助言の手(候補手・道のりの
// 一手)の移動元・移動先・利きの線上にある」に限る。実装は別STEPで判断する
// (この注記の追加時点では判定を変えていない)。

import { detectBoardEvents } from "../../../apps/server/src/analysis/boardEventDetector.js";
import { deriveAdviceSource } from "../lib/adviceSource.js";
import { toSquareOf } from "../lib/players.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-6";

/** records(1run分)の中から、対象のready行のちょうど1つ前(t-2)のready行を探す。 */
function findPreviousReadyRecord(readyRecords: RecordLine[], targetPly: number): RecordLine | undefined {
  return readyRecords.find((r) => r.ply === targetPly - 2);
}

export const i6AdviceThenLoss: Invariant = {
  id: ID,
  title: "直前に表示していた候補手/道のりの一手と一致する手を指した直後、駒を取られ、取り返す手が無い",
  type: "結果",
  status: "draft",
  source: "docs/COVERAGE_AND_OUTCOME_PROPOSAL.md 4.3(最小案。2026-09-11人間決定)",
  check(records: RecordLine[]): Finding[] {
    const readyRecords = records.filter((r) => r.phase === "ready").sort((a, b) => a.ply - b.ply);
    const findings: Finding[] = [];

    for (const record of readyRecords) {
      if (record.senteMove === null || record.goteMove === null) continue;

      const previous = findPreviousReadyRecord(readyRecords, record.ply);
      if (!previous) continue;

      const adviceSource = deriveAdviceSource(previous, record.senteMove);
      if (adviceSource !== "candidate" && adviceSource !== "route") continue;

      let events;
      try {
        events = detectBoardEvents(previous.sfen, record.senteMove, record.goteMove);
      } catch {
        continue;
      }

      const capture = events.find((e) => e.kind === "captured_by_opponent" && e.square !== null);
      if (!capture || capture.square === null) continue;

      const canRecapture = record.response.legalMoves.some((move) => toSquareOf(move) === capture.square);
      if (canRecapture) continue;

      const pieceClause = capture.piece ? `${capture.piece}が` : "";
      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: adviceSource,
        detail: `直前に表示していた候補手/道のりの一手と一致する手 ${record.senteMove} を指した直後、相手の応手 ${record.goteMove} で${pieceClause}${capture.square}で取られ、${capture.square}へ動く手が合法手にありません。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
