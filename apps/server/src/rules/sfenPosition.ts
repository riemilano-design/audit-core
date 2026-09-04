// SFEN文字列をshogiopsの局面オブジェクトへ変換する共通ヘルパー。
// このモジュール配下の各ファイル(legalMoves/applyMove/gameStatus等)が同じ
// InvalidSfenError・同じ解析ロジックを共有するために切り出した
// (別々に定義すると、あるモジュールが投げたエラーを別モジュールの
// catch節(instanceof判定)で捕捉できなくなるため)。

import { parseSfen } from "shogiops/sfen";
import type { Position } from "shogiops/variant/position";

export class InvalidSfenError extends Error {}

export function parsePosition(sfen: string): Position {
  const parsed = parseSfen("standard", sfen);
  if (parsed.isErr) {
    throw new InvalidSfenError(
      `SFENの解析に失敗しました: "${sfen}" (${parsed.error?.message ?? "unknown error"})`,
    );
  }
  return parsed.value;
}
