// 指し手履歴(USI形式の文字列配列)を、初期局面から実際に再生しながら
// 「何手目に・どちらの手番が・どの駒種を・どのマスへ動かしたか」という
// Intent判定に必要な情報へ分解する。
//
// 将棋の合法性判定・局面遷移は既存のrules/配下(applyMove.ts, 内部でlegalMoves.tsを使用)に
// 完全に委ね、本モジュールはその結果(遷移前後の局面)から駒種を読み取るだけに責務を限定する
// (CLAUDE.mdルール3番の前段と同じく、安全確認を経た局面遷移のみを前提にする)。

import { makeSfen, parseSfen } from "shogiops/sfen";
import type { Color, Role } from "shogiops/types";
import { isDrop, makeSquareName, parseUsi } from "shogiops/util";
import { applyMove } from "../rules/applyMove.js";
import { parsePosition } from "../rules/sfenPosition.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";
export { IllegalMoveError } from "../rules/applyMove.js";

export const DEFAULT_INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

export class MoveHistoryError extends Error {}

export interface MoveEvent {
  /** 1手目を1とする手数 */
  ply: number;
  moveUsi: string;
  /** この手を指した手番。MVP確定仕様ではsente=自分(四間飛車)、gote=相手(居飛車)。 */
  color: Color;
  /** 動いた(または打たれた)駒の種類 */
  role: Role;
  /** 移動先のマス目(USI形式、例: 7c) */
  toSquare: string;
}

export interface MoveHistoryReplay {
  events: MoveEvent[];
  /** moveHistoryをすべて適用した後の局面のSFEN */
  finalSfen: string;
  /**
   * Phase 7 Unit 2(認識の時系列): 各手を適用した**後**の局面のSFEN。
   * `sfens[0]` は initialSfen、`sfens[i]` は i手目まで適用した局面で、
   * 要素数は `moveHistory.length + 1`。末尾は `finalSfen` と等しい。
   *
   * 履歴を途中まで切り詰めて認識を再計算する際、対応する中間局面が必要になる
   * (docs/PHASES.md Phase 7 Unit 2)。再生の途中で既に計算しているものを
   * 捨てずに返すだけであり、新しい計算・判定は行っていない。
   */
  sfens: string[];
}

/**
 * initialSfenからmoveHistoryを1手ずつ適用しながら、各手のMoveEventを組み立てる。
 * moveHistoryの中に非合法な手・解析できない手が含まれる場合は例外を投げる
 * (applyMove.ts / sfenPosition.ts が投げるIllegalMoveError / InvalidSfenErrorをそのまま伝播する)。
 */
export function replayMoveHistory(
  moveHistory: string[],
  initialSfen: string = DEFAULT_INITIAL_SFEN,
): MoveHistoryReplay {
  let sfen = initialSfen;
  const events: MoveEvent[] = [];
  const sfens: string[] = [initialSfen];

  moveHistory.forEach((moveUsi, index) => {
    const pos = parsePosition(sfen);
    const move = parseUsi(moveUsi);
    if (!move) {
      throw new MoveHistoryError(`指し手の解析に失敗しました: "${moveUsi}"(${index + 1}手目)`);
    }

    const color = pos.turn;
    const role: Role = isDrop(move)
      ? move.role
      : (() => {
          const piece = pos.board.get(move.from);
          if (!piece) {
            throw new MoveHistoryError(`移動元に駒がありません: "${moveUsi}"(${index + 1}手目)`);
          }
          return piece.role;
        })();
    const toSquare = makeSquareName(move.to);

    events.push({ ply: index + 1, moveUsi, color, role, toSquare });

    // 合法性の確認・局面遷移そのものはapplyMove.tsに委ねる(非合法ならIllegalMoveErrorが伝播する)。
    sfen = applyMove(sfen, moveUsi);
    sfens.push(sfen);
  });

  return { events, finalSfen: sfen, sfens };
}
