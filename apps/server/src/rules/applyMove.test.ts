import { parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import { applyMove, IllegalMoveError, InvalidSfenError } from "./applyMove.js";

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

describe("applyMove", () => {
  it("合法手を適用し、次の局面のSFENを返す", () => {
    const next = applyMove(STARTPOS_SFEN, "7g7f");
    expect(next).not.toBe(STARTPOS_SFEN);
    // 適用後のSFENが再度shogiopsで解釈できる(壊れていない)ことを確認する。
    expect(parseSfen("standard", next).isOk).toBe(true);
    expect(next).toContain(" w "); // 手番が後手に移っている
  });

  it("非合法な指し手に対してIllegalMoveErrorを投げる", () => {
    expect(() => applyMove(STARTPOS_SFEN, "5e5d")).toThrow(IllegalMoveError);
  });

  it("壊れたSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => applyMove("not-a-valid-sfen", "7g7f")).toThrow(InvalidSfenError);
  });
});
