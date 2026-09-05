// 指し手履歴(USI形式)を、初心者にも読める日本語の棋譜表記(例: "７六歩")へ変換する。
// docs/PHASES.md Phase5「指し手履歴がUSI形式で分かりにくい問題」への対応。
//
// 【重要】将棋の棋譜表記(「同」「成」「不成」「打」等)の生成ロジックは一切自作せず、
// 既存ライブラリshogiopsの notation/japanese.ts (makeJapaneseMoveOrDrop) にすべて委ねる。
// このモジュールの責務は、apps/server/src/analysis/moveHistory.ts の replayMoveHistory と
// 同じ「1手ずつ局面を再生しながら、各手の直前の局面を渡す」という配線だけであり、
// replayMoveHistory自体(Intent判定等が依存する既存の分析ロジック)は変更しない
// (別モジュールとして新規に追加するのみ)。
//
// makeJapaneseMoveOrDropは、SFENから再生成した(=それ単体では「直前の一手」を
// 記憶していない)Positionを渡す前提だと「同」表記を出せないため、前の手の
// 移動先(lastDest)を呼び出し側であるここで明示的に渡す。

import { makeJapaneseMoveOrDrop } from "shogiops/notation/japanese";
import { parseUsi } from "shogiops/util";
import type { Square } from "shogiops/types";
import { applyMove } from "../rules/applyMove.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { DEFAULT_INITIAL_SFEN } from "../analysis/moveHistory.js";

/**
 * moveHistory(USI形式、初手から順)を、1手ずつ日本語棋譜表記へ変換する。
 * 変換できなかった手(USIの解析に失敗した、またはshogiops側がundefinedを返した場合)は
 * nullを返す。呼び出し側(UI)は、nullの手についてはUSI表記へフォールバックする想定
 * (このモジュールでは推測表記を生成しない)。
 *
 * moveHistoryの中に非合法な手が含まれる場合は、rules/applyMove.tsのIllegalMoveErrorが
 * そのまま伝播する(既存のreplayMoveHistoryと同じ前提: moveHistoryは常に合法な手の列である)。
 */
export function toJapaneseMoveHistory(
  moveHistory: string[],
  initialSfen: string = DEFAULT_INITIAL_SFEN,
): (string | null)[] {
  let sfen = initialSfen;
  let previousTo: Square | undefined;
  const result: (string | null)[] = [];

  for (const moveUsi of moveHistory) {
    const move = parseUsi(moveUsi);
    let japanese: string | null = null;

    if (move) {
      try {
        japanese = makeJapaneseMoveOrDrop(parsePosition(sfen), move, previousTo) ?? null;
      } catch {
        // shogiops側の想定外の例外時も、この1手だけnull(USIへフォールバック)にし、
        // 履歴全体の変換を止めない。
        japanese = null;
      }
      previousTo = move.to;
    }

    result.push(japanese);
    // 局面の進行(合法性確認込み)は既存のapplyMove.tsにそのまま委ねる。
    sfen = applyMove(sfen, moveUsi);
  }

  return result;
}
