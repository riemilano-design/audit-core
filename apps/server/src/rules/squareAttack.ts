// 盤上のマス目1つについて、「指定した色の駒の利きが届いているか」だけを答える、
// rules/attackedPieces.ts の squareAttackers 呼び出しをさらに薄くラップした純粋関数。
//
// rules/attackedPieces.ts の listAttackedPieces は「盤上の自分の駒(玉を除く)」を
// 列挙する関数であり、玉が置かれているマスや、まだ駒が無い(移動先の)マスについては
// 答えられない。STEP 5-E(escapeSquareThreat.ts)が「指した後の移動先に相手の駒が
// 届くか」を求めるには、駒の有無に関係なく「そのマスに利きが届いているか」を直接
// 答える関数が要るため、ここに追加する。
//
// listAttackedPieces・isGameOver/isInCheck(gameStatus.ts)と同じ方針(SFENを受け取り、
// shogiopsの判定にそのまま委ねるだけの薄いラッパー。独自の利き計算は一切持たない)に従う。

import type { Color } from "shogiops/types";
import { parseSquareName } from "shogiops/util";
import { parsePosition } from "./sfenPosition.js";

export { InvalidSfenError } from "./sfenPosition.js";

export class InvalidSquareError extends Error {}

/**
 * squareに、attackerColor側の駒の利きが届いているかどうかを判定する。
 * shogiopsのPosition.squareAttackers(幾何のみ)への薄いラッパーであり、判断
 * (取れるか・守られているか等)は一切行わない。
 *
 * 決定的な純粋関数(SFENのみに依存し、エンジン・LLMには依存しない)。
 */
export function isSquareAttacked(sfen: string, square: string, attackerColor: Color): boolean {
  const pos = parsePosition(sfen);
  const target = parseSquareName(square);
  if (target === undefined) {
    throw new InvalidSquareError(`マス目の表記が不正です: "${square}"`);
  }
  return !pos.squareAttackers(target, attackerColor, pos.board.occupied).isEmpty();
}
