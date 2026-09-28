// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。固定棋譜 JSON から
// 「最後の局面の SFEN」を作る純粋関数。「盤上はこう勝てた」(§9.1 の 1.)の終局の局面を、呼び出し側(CLI)が
// エンジンで読むための下ごしらえ。
//
// 【このファイルがやること】
// - `lib/sideAlignment.ts` の `readSideAlignment`(既存・確定済み。D0-SIDE 段 2)で、固定棋譜が
//   「本人が後手の局を回して畳んだもの」(mirrored: true)かどうかを読む(二重に実装しない)
// - mirrored なら `startSfen` から、そうでなければ標準の初期局面(`lib/kifuImport.ts` の
//   `STANDARD_START_SFEN`)から、`moves` を `applyMove`(apps/server の既存の道具)で 1 手ずつ進める
// - 進めた最後の SFEN と、進めた手数(= moves.length)を返す
//
// 【このファイルが絶対にやらないこと】
// - エンジンを起動すること・ファイルの読み書き(CLI(scripts/playtest/finalPositions.ts)の役目)
// - 手数が奇数のときに最後の手を落とすこと(`lib/replayPlan.ts` の役目。あれは replay.ts の
//   2 手ずつの診断ループのための決め事で、「本当の最後の局面」を作るこの関数には要らない ―
//   ここでは `moves` を最後まですべて進める)
// - 局面の意味からの判断。将棋の判断的知識

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { STANDARD_START_SFEN } from "./kifuImport.js";
import { readSideAlignment } from "./sideAlignment.js";

export interface FinalPositionKifu {
  moves: readonly string[];
  [field: string]: unknown;
}

export interface FinalPosition {
  /** 最後の局面の SFEN(mirrored の局は「本人 = 先手」にそろえた向きのまま ― whatif-v2・read.ts と同じ座標)。 */
  sfen: string;
  /** 進めた手数(= moves.length)。 */
  moves: number;
}

/** 固定棋譜 JSON(`*.fixed.json`)から、最後の局面の SFEN を作る(計画 §9.2)。 */
export function finalPositionOf(kifu: FinalPositionKifu): FinalPosition {
  const { alignment } = readSideAlignment(kifu);
  let sfen = alignment.mirrored ? alignment.startSfen : STANDARD_START_SFEN;
  for (const move of kifu.moves) sfen = applyMove(sfen, move);
  return { sfen, moves: kifu.moves.length };
}

/**
 * 元の棋譜の手数(= 進めた手数 + plyOffset)。**顧客の紙に出す手数はこちら。**
 *
 * STEP ENDING_CLOCK §4 の 24(2026-09-28、独立監査 REVISE R6 の直し込み)。
 * `finalPositionOf` が返す `moves` は**進めた手数**で、その約束は正しい。ただし本人が後手だった局
 * (`mirrored: true`)は、固定棋譜が相手の初手を開始局面に畳んでいる(`plyOffset: 1`)ので、
 * **進めた手数は元の手数より 1 少ない**。規約は前からある ― `lib/reportData.ts` の `displayPlyOf`
 * (displayPly = 記録の ply + plyOffset)・`invariants/types.ts`(「元の ply = 記録の ply + plyOffset」)。
 * **付録 3 の最後の局面だけがこの規約に乗っていなかった**(付録 1・付録 4 は `patient_report_data.json` の
 * `total` を使うので正しかった。同じ 1 局の手数が冊子の間で違う、と文脈ゼロの批評席が指摘した)。
 *
 * **`mirrored: true` なのに `plyOffset` の欄が無い固定棋譜は例外にする。** 黙って 1 を足さない ―
 * 「欄が無い」と「1 だった」を同じ値にすると、入口が壊れていることに誰も気づけない(「無い」の 3 種類を分ける)。
 */
export function originalMovesOf(final: FinalPosition, meta: Readonly<Record<string, unknown>>): number {
  if (meta.mirrored !== true) return final.moves;
  if (typeof meta.plyOffset !== "number") {
    throw new Error(
      `mirrored: true なのに plyOffset の欄が無い(${JSON.stringify(meta.plyOffset)})。元の手数へ戻せない`,
    );
  }
  return final.moves + meta.plyOffset;
}
