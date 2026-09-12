// I-10(結果、draft): I-8 が検出する手について、直前の ready 行の応答に
// 「その移動先に相手の駒が届く」という情報が無かった場合を検出する。
//
// 出典: docs/STEP_5-E_PLAN_2026-09-12.md A-4・6.1(2026-09-12人間決定 H-5 = (i))。
//
// 【なぜ I-8 ではなく新しい不変条件なのか】
// 固定棋譜は指し手が記録済みのため、表示を直しても I-8 は動かない
// (帯の名指し・指し手・取られた事実はどれも変わらない。計画書6.1)。
// 一方、再生では応答がサーバーで作り直されるため、「画面がその移動先に相手の駒が
// 届くと示していたか」は同じ4局から測れる。これが I-10 を足す理由である。
//
// 【判定(I-8 とまったく同じ条件に1つ足すだけ)】
// 1. I-8 と同じ条件で対象行を選ぶ: 直前の ready 行(t-2)の帯に piece_attacked の
//    名指しがあり、movesBandNamedPiece(previous, record.senteMove) が真で、
//    detectBoardEvents(previous.sfen, senteMove, goteMove) に captured_by_opponent
//    かつ square === senteMove の移動先 の事象がある。
// 2. そのうえで、直前の ready 行の応答の escapeSquareThreats(USI文字列の配列)に
//    record.senteMove が含まれていないときだけ検出する。
//    このフィールドが存在しない古い記録は「情報が無かった」として検出する
//    (undefined は空配列と同じ扱い。これは意図した挙動。基準値を測った
//    2026-09-12の記録にはこのフィールドがまだ無いため、I-10は1件になるはず)。
// 3. detectBoardEvents が例外を投げた行は検出しない(推測しない)。
// 4. condition には I-8 と同じく deriveAdviceSource(previous, record.senteMove) の
//    値を入れる。
//
// 【この不変条件が言うこと・言わないこと(必ず読むこと)】
// - 因果は主張しない。「画面が示していれば取られなかった」とは言わない。
//   言えるのは「直前の画面がこの移動先に相手の駒が届くことを示していなかった」
//   という事実だけである。
// - 閾値・将棋の良し悪しの判断は一切持たない。
// - I-8 の定義は一切変えない(人間決定。I-8 は分母と観測としてそのまま残す)。
//   このファイルは I-8 の検出結果・件数に影響を与えない。

import { detectBoardEvents } from "../../../apps/server/src/analysis/boardEventDetector.js";
import { deriveAdviceSource, movesBandNamedPiece } from "../lib/adviceSource.js";
import { toSquareOf } from "../lib/players.js";
import type { Finding, Invariant, RecordLine } from "./types.js";

const ID = "I-10";

/** records(1run分)の中から、対象のready行のちょうど1つ前(t-2)のready行を探す。
 * i8-band-piece-then-captured.ts と同じ探し方(t-2 のみを対象、I-8 の定義を変えない)。 */
function findPreviousReadyRecord(readyRecords: RecordLine[], targetPly: number): RecordLine | undefined {
  return readyRecords.find((r) => r.ply === targetPly - 2);
}

export const i10EscapeSquareNotShown: Invariant = {
  id: ID,
  title: "I-8が検出した手について、直前の画面はその移動先に相手の駒が届くことを示していなかった",
  type: "結果",
  status: "draft",
  source: "docs/STEP_5-E_PLAN_2026-09-12.md A-4・6.1(2026-09-12人間決定 H-5=(i))",
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

      // I-10 だけの条件: 直前の画面が、この移動先に相手の駒が届くことを
      // 示していたか(escapeSquareThreatsに含まれるか)。フィールドが無い
      // 古い記録はundefinedになり、空配列と同じ扱いにする(意図した挙動)。
      const escapeSquareThreats = previous.response.escapeSquareThreats ?? [];
      if (escapeSquareThreats.includes(record.senteMove)) continue;

      const pieceClause = capture.piece ? `${capture.piece}が` : "";
      findings.push({
        invariantId: ID,
        kifuId: "",
        ply: record.ply,
        phase: record.phase,
        condition: deriveAdviceSource(previous, record.senteMove),
        detail: `帯が名指しした駒(${record.senteMove.slice(0, 2)})を動かす手 ${record.senteMove} を指した直後、相手の応手 ${record.goteMove} で${pieceClause}移動先の${destination}で取られましたが、直前の画面はこの移動先に相手の駒が届くことを示していませんでした。`,
        sfen: record.sfen,
        senteMove: record.senteMove,
        goteMove: record.goteMove,
      });
    }

    return findings;
  },
};
