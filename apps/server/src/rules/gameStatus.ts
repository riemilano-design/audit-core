// 局面(SFEN)が終局しているかどうか・終局理由をshogiopsに判定させる。
// legalMoves.tsと同じ方針(純粋関数、SFEN入力)に従う。

import type { Outcome } from "shogiops/types";
import { parsePosition } from "./sfenPosition.js";

export { InvalidSfenError } from "./sfenPosition.js";

export function isGameOver(sfen: string): boolean {
  return parsePosition(sfen).isEnd();
}

/**
 * 終局している場合、その結果(勝者・種別)を返す。終局していなければundefined。
 */
export function getGameOutcome(sfen: string): Outcome | undefined {
  return parsePosition(sfen).outcome();
}
