// shogiopsを使った合法手判定。
// [CLAUDE.md](../../../../CLAUDE.md) ルール3番(将棋エンジンによる安全確認を経ていない候補手を
// ユーザーに見せない)の前段として、まず「合法手かどうか」をshogiopsに判定させる。
// 局面(SFEN)を入力として結果を返す純粋関数として実装する
// (docs/TESTING_STRATEGY.md「ロジック単体テスト」の方針に従う)。

import { parseSfen } from "shogiops/sfen";
import { makeUsi, parsePieceName, parseUsi } from "shogiops/util";
import type { MoveOrDrop } from "shogiops/types";
import type { Position } from "shogiops/variant/position";

export class InvalidSfenError extends Error {}

function parsePosition(sfen: string): Position {
  const parsed = parseSfen("standard", sfen);
  if (parsed.isErr) {
    throw new InvalidSfenError(
      `SFENの解析に失敗しました: "${sfen}" (${parsed.error?.message ?? "unknown error"})`,
    );
  }
  return parsed.value;
}

/**
 * 局面(SFEN)における、現在の手番の合法手をすべてUSI形式で返す。
 * 通常の指し手は成り/不成りの両方を、legalかどうかで別々に判定する
 * (成れるかどうか・成りが強制かどうかはshogiops側のルールに委ねる)。
 */
export function getLegalMoves(sfen: string): string[] {
  const pos = parsePosition(sfen);
  const ctx = pos.ctx();
  const usiMoves: string[] = [];

  for (const [from, toSquares] of pos.allMoveDests(ctx)) {
    for (const to of toSquares) {
      for (const promotion of [false, true]) {
        const move: MoveOrDrop = { from, to, promotion };
        if (pos.isLegal(move, ctx)) {
          usiMoves.push(makeUsi(move));
        }
      }
    }
  }

  for (const [pieceName, toSquares] of pos.allDropDests(ctx)) {
    const { role } = parsePieceName(pieceName);
    for (const to of toSquares) {
      const drop: MoveOrDrop = { role, to };
      if (pos.isLegal(drop, ctx)) {
        usiMoves.push(makeUsi(drop));
      }
    }
  }

  return usiMoves;
}

/**
 * 局面(SFEN)に対して、指定した指し手(USI形式)が合法手かどうかを判定する。
 */
export function isLegalMove(sfen: string, moveUsi: string): boolean {
  const pos = parsePosition(sfen);
  const move = parseUsi(moveUsi);
  if (!move) return false;
  return pos.isLegal(move);
}
