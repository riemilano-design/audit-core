// I-8(結果、draft): 帯([0]「今すぐ対処が必要なこと」)が名指しした駒を自分が動かし、
// その直後の相手の手でその駒が取られた場合を検出する。
//
// 出典: docs/BASELINE_2026-09-12.md 3.3(4局の基準値で、人間が「誤らせる型(最優先)」
// と判定した局が I-1〜I-7 のすべてで0件になった。理由は I-6 が adviceSource
// (候補手・道のり)だけを見て帯を対象にしないため)。2026-09-12 人間決定により追加。
//
// 【この不変条件が言うこと・言わないこと(必ず読むこと)】
// - これは「帯の言うとおりに逃がしたら取られた」を数えるものではない。帯は
//   「どこへ逃げれば安全か」を言わないため、帯が名指しした駒を動かす手が
//   逃げる手とは限らない(取りに行く手・別の用事で動かす手も含む)。この検出が
//   言えるのは「帯が名指しした駒を動かし、その駒が直後に取られた」という
//   盤の事実だけである。
// - 因果は主張しない。動かさなくても取られていたかどうかは判定しない
//   (それはエンジンの判断であり、ここでは行わない)。
// - I-6 と違い「取り返す手が合法手に無い」ことは要求しない(2026-09-12の人間の
//   定義そのまま)。したがって I-6 より広い。両方に出る行がありうる。
// - 閾値・文言・将棋の良し悪しの判断は一切持たない。
//
// 判定:
// ready行tについて、直前のready行(t-2)の帯に kind: "piece_attacked" があり、
// senteMove の移動元マスがその名指しマスに含まれ(lib/adviceSource.ts の
// movesBandNamedPiece。ドロップは対象外)、本番関数
// detectBoardEvents(prev.sfen, senteMove, goteMove) の結果に captured_by_opponent
// かつ square === senteMove の移動先 の事象があれば検出する。
// detectBoardEvents が例外を投げた行は検出しない(推測しない)。
//
// condition には deriveAdviceSource の値(band / candidate / route)を入れる。
// 帯が名指しした駒を動かす手が、同時に候補手・道のりにも載っていた場合は
// band ではなく candidate/route になる(重なりを隠さないため。
// lib/adviceSource.ts の movesBandNamedPiece の注記を参照)。

import { detectBoardEvents } from "../../../apps/server/src/analysis/boardEventDetector.js";
import { deriveAdviceSource, movesBandNamedPiece } from "../lib/adviceSource.js";
import { toSquareOf } from "../lib/players.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-8";

/** records(1run分)の中から、対象のready行のちょうど1つ前(t-2)のready行を探す。 */
function findPreviousReadyRecord(readyRecords: RecordLine[], targetPly: number): RecordLine | undefined {
  return readyRecords.find((r) => r.ply === targetPly - 2);
}

export const i8BandPieceThenCaptured: Invariant = {
  id: ID,
  title: "帯が名指しした駒を動かし、その直後の相手の手でその駒が取られた",
  type: "結果",
  status: "draft",
  source: "docs/BASELINE_2026-09-12.md 3.3(2026-09-12人間決定。帯を adviceSource に足す)",
  check(records: RecordLine[]): Finding[] {
    const readyRecords = records.filter((r) => r.phase === "ready").sort((a, b) => a.ply - b.ply);
    const findings: Finding[] = [];

    for (const record of readyRecords) {
      if (record.senteMove === null || record.goteMove === null) continue;

      const previous = findPreviousReadyRecord(readyRecords, record.ply);
      if (!previous) continue;

      if (!movesBandNamedPiece(previous, record.senteMove)) continue;

      let events;
      try {
        events = detectBoardEvents(previous.sfen, record.senteMove, record.goteMove);
      } catch {
        continue;
      }

      const destination = toSquareOf(record.senteMove);
      const capture = events.find((e) => e.kind === "captured_by_opponent" && e.square === destination);
      if (!capture) continue;

      const pieceClause = capture.piece ? `${capture.piece}が` : "";
      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: deriveAdviceSource(previous, record.senteMove),
        detail: `帯が名指しした駒(${record.senteMove.slice(0, 2)})を動かす手 ${record.senteMove} を指した直後、相手の応手 ${record.goteMove} で${pieceClause}移動先の${destination}で取られました。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
