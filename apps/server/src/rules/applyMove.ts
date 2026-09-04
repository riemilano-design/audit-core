// 局面(SFEN)に指し手(USI形式)を適用し、適用後のSFENを返す純粋関数。
// legalMoves.tsの合法手判定を経由しない指し手適用を防ぐため、必ずisLegalMoveで確認してから適用する
// (CLAUDE.mdルール3番「安全確認を経ていない候補手をユーザーに見せない」の前段にあたる、
// 「非合法な手をそもそも局面に適用しない」という最低限の防御)。

import { makeSfen } from "shogiops/sfen";
import { parseUsi } from "shogiops/util";
import { isLegalMove } from "./legalMoves.js";
import { parsePosition } from "./sfenPosition.js";

export { InvalidSfenError } from "./sfenPosition.js";
export class IllegalMoveError extends Error {}

export function applyMove(sfen: string, moveUsi: string): string {
  if (!isLegalMove(sfen, moveUsi)) {
    throw new IllegalMoveError(`非合法な指し手です: "${moveUsi}"(局面: "${sfen}")`);
  }
  const pos = parsePosition(sfen);
  const move = parseUsi(moveUsi);
  if (!move) {
    // isLegalMoveがtrueを返した時点でパース済みのはずだが、型上の安全のため確認する。
    throw new IllegalMoveError(`指し手の解析に失敗しました: "${moveUsi}"`);
  }
  pos.play(move);
  return makeSfen(pos);
}
