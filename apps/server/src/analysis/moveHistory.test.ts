import { describe, expect, it } from "vitest";
import { InvalidSfenError, MoveHistoryError, replayMoveHistory } from "./moveHistory.js";

describe("replayMoveHistory", () => {
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
