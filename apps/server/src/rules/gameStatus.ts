// 局面(SFEN)が終局しているかどうか・終局理由をshogiopsに判定させる。
// legalMoves.tsと同じ方針(純粋関数、SFEN入力)に従う。

import type { Color, Outcome } from "shogiops/types";
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

/**
 * Phase6 Unit4: colorの側の玉に、現在王手がかかっているかを返す。
 * 判定はshogiopsのPosition.isCheck(color)にそのまま委ね、独自の王手判定は持たない
 * (isGameOver/getGameOutcomeと同じ、SFENを受け取る薄いラッパー)。
 *
 * 「王手を受けている側は、王手を解消する手しか指せない」という将棋のルール上の事実を
 * 述べるためだけに使う。手の良し悪しの評価には一切関与しない。
 */
export function isInCheck(sfen: string, color: Color): boolean {
  return parsePosition(sfen).isCheck(color);
}
