// 先手玉の周りを数える(STEP JSON v0.2 で failureEvent.ts に置いた関数を、STEP D2 で lib/counterfactual.ts からも使うために
// このファイルへ移した。中身は変えていない。failureEvent.ts が同じ名前で export し直す)。

import { parseSquareName } from "shogiops/util";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";

/**
 * STEP JSON v0.2(docs/STEP_JSON-V0.2_PLAN_2026-09-15.md 2.4・K-7)。局面の先手玉の 8 近傍のうち盤の中にあるマスの数(`squares`。
 * 中央 8・端 5・隅 3)と、そこにある先手の駒の数(`own`。駒の種類を問わず、成り駒も含む)。
 * **数えるだけ(A 層の数)。閾値も名前も置かず、死因の規則・candidateModes・画面には使わない。**先手玉が盤上に無ければ null。
 */
export interface KingSurroundings {
  squares: number;
  own: number;
}

const BOARD_RANKS = "abcdefghi";

export function kingSurroundingsOf(sfen: string): KingSurroundings | null {
  const board = parsePosition(sfen).board;
  const pieceAt = (file: number, rank: number) => {
    const square = parseSquareName(`${file}${BOARD_RANKS[rank]}`);
    return square === undefined ? undefined : board.get(square);
  };
  let king: { file: number; rank: number } | undefined;
  for (let file = 1; file <= 9 && !king; file++) {
    for (let rank = 0; rank < 9; rank++) {
      const piece = pieceAt(file, rank);
      if (piece?.color === "sente" && piece.role === "king") {
        king = { file, rank };
        break;
      }
    }
  }
  if (!king) return null;
  let squares = 0;
  let own = 0;
  for (let df = -1; df <= 1; df++) {
    for (let dr = -1; dr <= 1; dr++) {
      if (df === 0 && dr === 0) continue;
      const file = king.file + df;
      const rank = king.rank + dr;
      if (file < 1 || file > 9 || rank < 0 || rank > 8) continue;
      squares += 1;
      if (pieceAt(file, rank)?.color === "sente") own += 1;
    }
  }
  return { squares, own };
}
