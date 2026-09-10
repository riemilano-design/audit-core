// 自分の駒に相手の駒の利きが届いている、という将棋のルール上の事実だけを列挙する。
// shogiops の Position.squareAttackers(幾何のみ)への薄いラッパーであり、
// isGameOver/isInCheck(gameStatus.ts)と同じ方針(SFENを受け取り、独自の判定を
// 持たない)に従う。
//
// squareAttackers はマスへ利きが届いているかどうかの幾何だけを返す。ピンで
// 実際には動かせない・取り返せる・守られている、といった判断はここでは一切行わない
// (STEP 4-3 人間承認: A「駒が当たっている」の定義)。
//
// 自分の玉は対象に含めない。玉に利きが届いている状態は「王手」であり、
// rules/gameStatus.ts の isInCheck が既に扱っている事実と同じものを重ねて
// 返さないため(STEP 4-3 人間承認: F①)。

import { makeSquareName, opposite } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { parsePosition } from "./sfenPosition.js";

export { InvalidSfenError } from "./sfenPosition.js";

export interface AttackedPieceAttacker {
  /** 攻めている相手の駒があるマス(USI形式)。 */
  square: string;
  /** 攻めている相手の駒の役職(成駒はそのまま。正規化はここでは行わない)。 */
  role: Role;
}

export interface AttackedPiece {
  /** 自分の駒があるマス(USI形式)。 */
  square: string;
  /** 自分の駒の役職(成駒はそのまま。正規化はここでは行わない)。 */
  role: Role;
  /** このマスへ利きが届いている相手の駒。1件以上。 */
  attackers: AttackedPieceAttacker[];
}

/**
 * color側の駒(玉を除く)のうち、相手の駒の利きが届いているものを列挙する。
 * 判定は shogiops の squareAttackers に委ねるだけで、独自の利き計算は行わない。
 *
 * 決定的な純粋関数(SFENのみに依存し、エンジン・LLMには依存しない)。
 */
export function listAttackedPieces(sfen: string, color: Color): AttackedPiece[] {
  const pos = parsePosition(sfen);
  const attackerColor = opposite(color);
  const result: AttackedPiece[] = [];

  for (const square of pos.board.color(color)) {
    const piece = pos.board.get(square);
    if (!piece || piece.role === "king") continue;

    const attackerSquares = pos.squareAttackers(square, attackerColor, pos.board.occupied);
    if (attackerSquares.isEmpty()) continue;

    const attackers: AttackedPieceAttacker[] = [];
    for (const attackerSquare of attackerSquares) {
      const attackerPiece = pos.board.get(attackerSquare);
      if (!attackerPiece) continue;
      attackers.push({ square: makeSquareName(attackerSquare), role: attackerPiece.role });
    }
    if (attackers.length === 0) continue;

    result.push({ square: makeSquareName(square), role: piece.role, attackers });
  }

  return result;
}
