// 現在の局面(sfen)における、現在の手番の合法手すべてについて、
// 「その手を指した後、移動先のマスに相手の駒が届くか」を機械的に求める
// (STEP 5-E・H-1・2026-09-12人間承認)。
//
// 判定方法: rules/applyMove.ts で局面を実際に進め、進んだ局面に対して
// rules/squareAttack.ts(shogiopsのsquareAttackersへ委ねる薄いラッパー)で
// 移動先マスへの相手の利きを調べるだけ。新しい利き計算は一切実装しない。
// 将棋エンジン・LLMのいずれにも依存しない、決定的な純粋関数。
//
// 【成り・不成について】
// 利きは盤上の駒の占有だけで決まり、動いた駒が成ったかどうかには依存しない。
// そのため、同じ移動先への成り・不成りの2手は必ず同じ判定結果になる。この関数は
// getLegalMoves が返す指し手をすべて独立に(成り・不成りをまとめる最適化をせずに)
// 判定するが、結果はこの事実により常に一致する。
//
// 【打つ手について】
// ドロップ(例 "P*5e")も対象に含める。H-4d「選んだ駒すべてを対象にする」の理由
// (名指しされていない駒だけが安全という誤った含みを作らない)は、ドロップにも
// 同じく当てはまるため。
//
// 【このモジュールが絶対にやらないこと】
// - 「逃げるべきマス」の示唆・推奨は一切しない(結果を使う側の責務でもない。
//   CLAUDE.md「絶対に守るルール」3番)。
// - 「取れるか」「守れるか」といった判断は一切しない(H-3。範囲外)。

import type { Color } from "shogiops/types";
import { makeSquareName, parseUsi } from "shogiops/util";
import { getLegalMoves } from "../rules/legalMoves.js";
import { applyMove } from "../rules/applyMove.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { isSquareAttacked } from "../rules/squareAttack.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError } from "../rules/applyMove.js";

export class InvalidMoveUsiError extends Error {}

export interface EscapeSquareThreat {
  /** 判定した指し手(USI形式)。getLegalMovesの要素をそのまま使う。 */
  move: string;
  /** 移動先のマス目(USI形式)。moveから取り出したものと同じ。 */
  toSquare: string;
  /** その手を指した後、移動先のマスに相手の駒の利きが届くかどうか。 */
  attacked: boolean;
}

/**
 * 現在の局面(sfen)における、現在の手番の合法手すべてについて、
 * 「その手を指した後、移動先に相手の駒が届くか」を判定する。
 * 合法手が無い(盤上に指せる駒が無い等)場合は空配列を返す。
 *
 * 決定的な純粋関数(SFENのみに依存し、エンジン・LLMには依存しない)。
 */
export function detectEscapeSquareThreats(sfen: string): EscapeSquareThreat[] {
  const moverColor: Color = parsePosition(sfen).turn;
  const attackerColor: Color = moverColor === "sente" ? "gote" : "sente";

  return getLegalMoves(sfen).map((move) => {
    const parsed = parseUsi(move);
    if (!parsed) {
      // getLegalMovesはmakeUsiで生成した文字列をそのまま返すため、通常は
      // ここに到達しない。到達した場合は呼び出し側の前提が崩れているため、
      // 推測で処理を続けずエラーにする。
      throw new InvalidMoveUsiError(`合法手の指し手表記が不正です: "${move}"`);
    }
    const toSquare = makeSquareName(parsed.to);
    const afterSfen = applyMove(sfen, move);
    const attacked = isSquareAttacked(afterSfen, toSquare, attackerColor);
    return { move, toSquare, attacked };
  });
}

/**
 * ある1駒(square)について、その駒から指せる合法手だけをthreatsから選び、
 * 「合法手が1つも無いか」「合法手はあるが移動先すべてに相手の駒が届くか」を
 * 集計するだけの関数(STEP 5-E・H-2)。新しい利き判定は行わない
 * (detectEscapeSquareThreatsが既に計算した結果を選び・数えるだけ)。
 *
 * 打つ手(ドロップ、例 "P*5e")は移動元となる盤上マスを持たないため、対象にしない
 * (このマスに元々あった駒の合法手だけを見るという趣旨に合わせる)。
 */
export interface PieceEscapeSquareStatus {
  /** squareにある駒の合法手が1つも無い。 */
  hasNoLegalMoves: boolean;
  /** squareにある駒の合法手はあるが、移動先すべてに相手の駒が届く。 */
  allDestinationsAttacked: boolean;
}

export function summarizeEscapeSquareThreatsForSquare(
  threats: EscapeSquareThreat[],
  square: string,
): PieceEscapeSquareStatus {
  const movesFromSquare = threats.filter((threat) => threat.move.slice(0, 2) === square);
  return {
    hasNoLegalMoves: movesFromSquare.length === 0,
    allDestinationsAttacked: movesFromSquare.length > 0 && movesFromSquare.every((threat) => threat.attacked),
  };
}
