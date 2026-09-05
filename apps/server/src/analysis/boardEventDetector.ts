// 着手の前後の局面から、「将棋のルール上、機械的に確定できる出来事」だけを取り出す
// (Phase6 Unit3)。扱うのは捕獲・王手・成りの3種類のみ。
//
// 【このモジュールがやること】
// 実際に指された手そのものを1手ずつ見て、その手で何が起きたかを確定する。
// 判定に使うのは、指し手(USI)と、その手を指す直前の局面・直後の局面だけであり、
// 将棋の知識データ(shapes/openings/intents)には一切依存しない。
//
// 【このモジュールが絶対にやらないこと】
// - 「良い手/悪い手」「損をした」「危険」「警戒すべき」といった評価・推奨は一切しない
//   (評価に必要な情報を引数として受け取ってすらいない)。
// - エンジンの評価値には一切触れない。LLMも使わない。
// - 「成れる状態だった」「取られそう」といった、実際には起きていないことは述べない。
// - 確定できないことは述べない(捕獲された駒の種類が対応表に無い成駒だった場合など、
//   駒種はnullにして名前を付けない)。
//
// 【原因の帰属について】
// beforeとafterの間には「ユーザーの手」と「相手の手」の2手が入るが、本モジュールは
// 2手を別々の局面遷移として個別に評価するため、どの手による出来事かが常に一意に決まる
// (moveOutcomeDetector.tsのような帰属の曖昧さは構造上発生しない)。
//
// 【局面遷移について】
// 中間局面(ユーザーの手を指した直後)は、既存のrules/applyMove.ts(合法性確認込みの
// 唯一の局面遷移API)で求める。独自の局面遷移ロジックは複製しない。

import { isDrop, makeSquareName, parseUsi } from "shogiops/util";
import type { Color } from "shogiops/types";
import { applyMove } from "../rules/applyMove.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { roleToJapanese } from "./pieceMapping.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError } from "../rules/applyMove.js";

export type BoardEventKind =
  /** あなたの手で相手の駒を取った */
  | "captured_by_you"
  /** 相手の手であなたの駒が取られた */
  | "captured_by_opponent"
  /** あなたの手で相手の玉に王手がかかった */
  | "check_given"
  /** 相手の手であなたの玉に王手がかかった */
  | "check_received"
  /** あなたの手で駒が成った */
  | "promoted_by_you"
  /** 相手の手で駒が成った */
  | "promoted_by_opponent";

export interface BoardEvent {
  kind: BoardEventKind;
  /**
   * 関係する駒の日本語表記。捕獲なら取られた駒、成りなら成った駒。
   * 対応表に無い駒種(成駒など)や、王手のように特定の駒に紐づかない場合はnull
   * (推測して名前を付けない)。
   */
  piece: string | null;
  /**
   * 出来事が起きたマス(USI形式)。捕獲・成りは移動先のマス。
   * 王手は特定のマスに紐づかないためnull。
   */
  square: string | null;
}

/** 1手ぶんの局面遷移。 */
interface MoveTransition {
  moveUsi: string;
  /** この手を指す直前の局面 */
  sfenBefore: string;
  /** この手を指した直後の局面 */
  sfenAfter: string;
  /** この手を指した側 */
  mover: "you" | "opponent";
}

function eventsForTransition(transition: MoveTransition): BoardEvent[] {
  const { moveUsi, sfenBefore, sfenAfter, mover } = transition;
  const events: BoardEvent[] = [];

  const move = parseUsi(moveUsi);
  // 解釈できない指し手について推測はしない(何も報告しない)。
  if (!move) return events;

  const positionBefore = parsePosition(sfenBefore);
  const moverColor: Color = positionBefore.turn;

  // 1. 捕獲: 着手前の局面で、移動先に相手の駒が実際に存在したかどうかだけで確定する。
  //    ドロップ(打つ手)は駒のあるマスへは打てないため対象外。
  if (!isDrop(move)) {
    const captured = positionBefore.board.get(move.to);
    if (captured && captured.color !== moverColor) {
      events.push({
        kind: mover === "you" ? "captured_by_you" : "captured_by_opponent",
        piece: roleToJapanese(captured.role),
        square: makeSquareName(move.to),
      });
    }
  }

  // 2. 成り: 実際に指された手が成りだった場合のみ。「成れた」という未実行の可能性は扱わない。
  if (!isDrop(move) && move.promotion) {
    const promotedPiece = positionBefore.board.get(move.from);
    events.push({
      kind: mover === "you" ? "promoted_by_you" : "promoted_by_opponent",
      piece: promotedPiece ? roleToJapanese(promotedPiece.role) : null,
      square: makeSquareName(move.to),
    });
  }

  // 3. 王手: この手を指した直後の局面で、手番side(=指されなかった側)が王手を
  //    受けているかどうか。1手ずつ評価しているため、どちらの手による王手かが一意に決まる。
  const positionAfter = parsePosition(sfenAfter);
  if (positionAfter.isCheck()) {
    events.push({
      kind: mover === "you" ? "check_given" : "check_received",
      piece: null,
      square: null,
    });
  }

  return events;
}

/**
 * ユーザーの着手と(あれば)相手の応手について、盤面上の出来事を列挙する。
 *
 * sfenBeforeUserMoveは「ユーザーが着手する直前の局面」。中間局面・最終局面は
 * rules/applyMove.tsで求める(呼び出し元が別途保持する必要はない)。
 * opponentMoveUsiがnullの場合(相手が指していない場合)は、ユーザーの手の分だけを返す。
 *
 * 指し手が非合法だった場合はIllegalMoveErrorがそのまま伝播する
 * (呼び出し元の安全側ラッパーが処理する)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。エンジン・LLMには一切依存しない)。
 */
export function detectBoardEvents(
  sfenBeforeUserMove: string,
  userMoveUsi: string,
  opponentMoveUsi: string | null,
): BoardEvent[] {
  const sfenAfterUserMove = applyMove(sfenBeforeUserMove, userMoveUsi);

  const transitions: MoveTransition[] = [
    {
      moveUsi: userMoveUsi,
      sfenBefore: sfenBeforeUserMove,
      sfenAfter: sfenAfterUserMove,
      mover: "you",
    },
  ];

  if (opponentMoveUsi !== null) {
    transitions.push({
      moveUsi: opponentMoveUsi,
      sfenBefore: sfenAfterUserMove,
      sfenAfter: applyMove(sfenAfterUserMove, opponentMoveUsi),
      mover: "opponent",
    });
  }

  return transitions.flatMap((transition) => eventsForTransition(transition));
}
