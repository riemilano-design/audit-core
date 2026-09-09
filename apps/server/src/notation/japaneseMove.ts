// まだ指していない1手(候補手など)を、その手を指す前の局面つきで日本語の棋譜表記
// (例: "７八銀")へ変換する。
//
// 【既存モジュールとの関係】
// notation/japaneseMoveHistory.ts は「指し終えた手の履歴(配列)」を1手ずつ再生しながら
// 変換するモジュールで、単独の1手を変換する入口を持たない。本モジュールはその入口だけを
// 提供する(japaneseMoveHistory.ts は変更しない)。
//
// 【棋譜表記の生成について】
// 「成」「不成」「右」「左」「打」等の表記ロジックは一切自作せず、既存ライブラリ
// shogiops の notation/japanese.ts (makeJapaneseMoveOrDrop) にすべて委ねる。
// 本モジュールの責務は、SFEN文字列からPositionを作って渡すという配線だけである。
//
// 【合法性を検証しないことについて】
// shogiops の makeJapaneseMoveOrDrop は手の合法性を検証しない(USIとして解釈できれば
// 表記を返す)。本モジュールも合法手判定を独自に持たない(rules/legalMoves.ts の責務を
// 複製しない)。合法な手だけを渡すのは呼び出し側の責務である。
//
// 【「同」表記を出さないことについて】
// makeJapaneseMoveOrDrop は直前の手の移動先(lastDest)を渡すと「同銀」のような表記を
// 生成するが、ここで扱うのは「これから指せる手」であり、単独で読めることが必要なため
// lastDest は渡さない(常にマス目を明示した表記になる)。

import { makeJapaneseMoveOrDrop } from "shogiops/notation/japanese";
import { isDrop, parseUsi } from "shogiops/util";
import { parsePosition } from "../rules/sfenPosition.js";
import { roleToJapanese } from "../analysis/pieceMapping.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";

/**
 * sfen の局面で moveUsi を指した場合の日本語棋譜表記を返す。
 *
 * 変換できなかった場合(USIとして解釈できない、shogiops側がundefinedを返した、
 * 想定外の例外が起きた)は null を返す。呼び出し側が別の表記へフォールバックする想定で、
 * このモジュールでは推測した表記を組み立てない。
 *
 * sfen 自体が不正な場合は parsePosition の InvalidSfenError がそのまま伝播する
 * (既存の notation/japaneseMoveHistory.ts と同じ前提)。
 */
/**
 * sfen の局面で moveUsi を指すときに「動かす駒」の日本語の駒名(例: "金")を返す。
 *
 * Phase 7 Unit 3(初心者向けの表記): 候補手を「６七→６六」ではなく
 * 「歩：６七→６六」と表示するために使う。盤上の移動元マスにある駒を読むだけで、
 * 将棋の判断は一切しない。打つ手(drop)の場合は打つ駒の名前を返す。
 *
 * 変換できなかった場合(USIとして解釈できない、移動元に駒が無い、対応表に無い駒種)は
 * null を返す。呼び出し側は駒名なしの表記へフォールバックする。
 */
export function toMovingPieceName(sfen: string, moveUsi: string): string | null {
  const move = parseUsi(moveUsi);
  if (!move) return null;

  try {
    if (isDrop(move)) return roleToJapanese(move.role);
    const piece = parsePosition(sfen).board.get(move.from);
    return piece ? roleToJapanese(piece.role) : null;
  } catch {
    return null;
  }
}

export function toJapaneseMove(sfen: string, moveUsi: string): string | null {
  const move = parseUsi(moveUsi);
  if (!move) return null;

  try {
    return makeJapaneseMoveOrDrop(parsePosition(sfen), move, undefined) ?? null;
  } catch {
    // shogiops側の想定外の例外時も、表記を推測せずnullを返す(呼び出し側でフォールバック)。
    return null;
  }
}
