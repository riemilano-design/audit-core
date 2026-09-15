// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の 4.・Q-3)。USI の手を盤ごと 180 度回す純粋関数。
//
// 【このファイルがやること】
// - マス `(筋, 段) → (10 − 筋, 10 − 段)`(段 a〜i を 1〜9 として)。例: `7g → 3c`、`5e → 5e`
// - 盤上の手 `<from><to>[+]` は from・to を回し、成りの `+` はそのまま残す
// - 駒打ち `<駒>*<to>` は駒の文字をそのまま残し(色を持たない)、打つマスを回す
//
// 【このファイルが絶対にやらないこと】
// - 局面を読むこと・合法かどうかを確かめること(回した手順を並べて確かめるのは呼び出し側と試験)
// - 読めない手を推測して回すこと(例外を投げる)
//
// `scripts/lib/usi-coordinates.mjs` の `rotateSquare180` と同じ変換を TS で書き直した(その試験は node:test の形で
// vitest の全件実行では走らない ― P-27)。81 マスで結果が同じことは usiRotation.test.ts が突き合わせる。

const RANKS = "abcdefghi";
const SQUARE = /^([1-9])([a-i])$/;
const BOARD_MOVE = /^([1-9][a-i])([1-9][a-i])(\+?)$/;
const DROP_MOVE = /^([PLNSGBR])\*([1-9][a-i])$/;

export class UsiRotationError extends Error {}

/** マスを 180 度回す(`7g` → `3c`)。 */
export function rotateSquare(square: string): string {
  const match = SQUARE.exec(square);
  if (!match) throw new UsiRotationError(`USI のマスとして読めない: "${square}"`);
  return `${10 - Number(match[1])}${RANKS[RANKS.length - 1 - RANKS.indexOf(match[2]!)]}`;
}

/** USI の手を 180 度回す(`7g7f` → `3c3d`、`8h2b+` → `2b8h+`、`P*2d` → `P*8f`)。 */
export function rotateUsiMove(move: string): string {
  const drop = DROP_MOVE.exec(move);
  if (drop) return `${drop[1]}*${rotateSquare(drop[2]!)}`;
  const board = BOARD_MOVE.exec(move);
  if (board) return `${rotateSquare(board[1]!)}${rotateSquare(board[2]!)}${board[3]}`;
  throw new UsiRotationError(`USI の手として読めない: "${move}"`);
}
