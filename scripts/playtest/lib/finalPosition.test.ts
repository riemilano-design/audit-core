// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。lib/finalPosition.ts の単体試験。
// **エンジンは起動しない**(合成の入力だけを使う)。実データ(t3-01.fixed.json)での確認は、実装担当の報告に
// 書く一回限りの手作業(このファイルには含めない ― out/ は gitignore で、このリポジトリのほかの試験も
// gitignore の実データには依存していない)。

import { describe, expect, it } from "vitest";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { finalPositionOf } from "./finalPosition.js";
import { STANDARD_START_SFEN } from "./kifuImport.js";
import { alignMovesToSente } from "./sideAlignment.js";

describe("finalPositionOf", () => {
  it("mirrored: false(先手の局)は標準の初期局面から moves をすべて進める", () => {
    const moves = ["7g7f", "3c3d", "2g2f"];
    let expected = STANDARD_START_SFEN;
    for (const move of moves) expected = applyMove(expected, move);

    const result = finalPositionOf({ moves, mirrored: false });

    expect(result.sfen).toBe(expected);
    expect(result.moves).toBe(3);
  });

  it("mirrored が無い(古い記録)ときも標準の初期局面から進める(readSideAlignment の既定)", () => {
    const moves = ["7g7f", "3c3d"];
    let expected = STANDARD_START_SFEN;
    for (const move of moves) expected = applyMove(expected, move);

    const result = finalPositionOf({ moves });

    expect(result.sfen).toBe(expected);
    expect(result.moves).toBe(2);
  });

  it("mirrored: true(後手の局を畳んだもの)は startSfen から畳んだ moves を進める", () => {
    // 本人が後手で指した実際の手順(先手から数えて 4 手)を alignMovesToSente で畳む
    // (lib/sideAlignment.ts の既存の道具。二重に実装しない)。
    const originalMoves = ["7g7f", "3c3d", "2g2f", "8c8d"];
    const { alignment, moves } = alignMovesToSente(originalMoves, "gote");
    if (!alignment.mirrored) throw new Error("テストの前提が崩れている(mirrored になるはず)");

    let expected = alignment.startSfen;
    for (const move of moves) expected = applyMove(expected, move);

    const result = finalPositionOf({
      mirrored: true,
      originalUserSide: "gote",
      plyOffset: 1,
      startSfen: alignment.startSfen,
      moves,
    });

    expect(result.sfen).toBe(expected);
    expect(result.moves).toBe(moves.length);
  });

  it("moves が 0 手(mirrored: false)なら、最後の局面 = 標準の初期局面", () => {
    const result = finalPositionOf({ moves: [], mirrored: false });
    expect(result.sfen).toBe(STANDARD_START_SFEN);
    expect(result.moves).toBe(0);
  });
});
