// data/shapes の日本語駒名 ⇔ shogiopsのRole識別子の変換のみを担当する。
// prototypes/shape-matcher/piece-mapping.mjs のロジックをapps/server側の本実装へ移植したもの。
// 表記のゆらぎ吸収であり、将棋の事実判断(この駒がどこにあるべきか等)は行わない。
//
// data/schemas/shapes.schema.json の required_pieces.piece が例示している表記
// (玉・金・銀など、成る前の基本駒)のみを対象とする。成駒(と金など)の表記は
// 現時点のdata/shapes/*.jsonに登場しないため未対応とし、未知の表記は例外にする。

import type { Role } from "shogiops/types";

const JAPANESE_TO_ROLE: Record<string, Role> = {
  玉: "king",
  王: "king", // 王将表記のゆらぎに備えた別名。データは現状「玉」に統一されている。
  金: "gold",
  銀: "silver",
  桂: "knight",
  香: "lance",
  飛: "rook",
  角: "bishop",
  歩: "pawn",
};

export class UnknownPieceNameError extends Error {
  constructor(public readonly pieceName: string) {
    super(`未知の駒種表記です: "${pieceName}"`);
    this.name = "UnknownPieceNameError";
  }
}

export function japaneseToRole(pieceName: string): Role {
  const role = JAPANESE_TO_ROLE[pieceName];
  if (!role) throw new UnknownPieceNameError(pieceName);
  return role;
}
