import { describe, expect, it } from "vitest";
import { InvalidSfenError, MoveHistoryError, replayMoveHistory } from "./moveHistory.js";

describe("replayMoveHistory", () => {
  // Phase 7 Unit 2: 各手を適用した後の局面。再生の途中で既に計算しているものを返すだけで、
  // 新しい計算・判定はしていない。
  it("各手を適用した後の局面を、手数+1件そろえて返す", () => {
    const history = ["7g7f", "3c3d", "2g2f"];
    const { finalSfen, sfens } = replayMoveHistory(history);

    expect(sfens).toHaveLength(history.length + 1);
    // 先頭は初期局面(まだ1手も指していない)、末尾はfinalSfenと一致する。
    expect(sfens[0]).toContain(" b - 1");
    expect(sfens.at(-1)).toBe(finalSfen);
    // 途中の局面は、その手数まで進んだ局面になっている(手数はSFEN末尾の数字)。
    expect(sfens[1]).toContain(" w - 2");
    expect(sfens[2]).toContain(" b - 3");
  });

  it("空の履歴でも、初期局面1件だけを返す", () => {
    const { finalSfen, sfens } = replayMoveHistory([]);

    expect(sfens).toEqual([finalSfen]);
  });

  it("空の履歴の場合、初期局面をそのままfinalSfenとして返す", () => {
    const { events, finalSfen } = replayMoveHistory([]);
    expect(events).toEqual([]);
    expect(finalSfen).toContain(" b - 1");
  });

  it("各手についてply/color/role/toSquareを正しく組み立てる", () => {
    const { events, finalSfen } = replayMoveHistory(["7g7f", "3c3d"]);

    expect(events).toHaveLength(2);
    expect(events[0]).toMatchObject({ ply: 1, moveUsi: "7g7f", color: "sente", role: "pawn", toSquare: "7f" });
    expect(events[1]).toMatchObject({ ply: 2, moveUsi: "3c3d", color: "gote", role: "pawn", toSquare: "3d" });
    expect(finalSfen).toContain(" b - 3");
  });

  it("非合法な手が含まれる場合、IllegalMoveError(applyMove.ts由来)を投げる", () => {
    expect(() => replayMoveHistory(["5e5d"])).toThrow();
  });

  it("不正な初期SFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => replayMoveHistory(["7g7f"], "not-a-valid-sfen")).toThrow(InvalidSfenError);
  });

  it("解析できない指し手文字列に対してMoveHistoryErrorを投げる", () => {
    expect(() => replayMoveHistory(["not-a-move"])).toThrow(MoveHistoryError);
  });
});
