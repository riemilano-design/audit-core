import { describe, expect, it } from "vitest";
import { getLegalMoves, InvalidSfenError, isLegalMove } from "./legalMoves.js";

describe("getLegalMoves", () => {
  it("初期局面(先手番)の合法手数を返す", () => {
    const moves = getLegalMoves("startpos");
    // 初期局面の先手合法手は30通り(全て歩・香・桂・銀・角の移動。成り/打つ手は存在しない)。
    expect(moves).toHaveLength(30);
    expect(moves).toContain("7g7f");
    expect(moves).toContain("2g2f");
  });

  it("重複のないUSI文字列の一覧を返す", () => {
    const moves = getLegalMoves("startpos");
    expect(new Set(moves).size).toBe(moves.length);
  });

  it("壊れたSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => getLegalMoves("not-a-valid-sfen")).toThrow(InvalidSfenError);
  });
});

describe("isLegalMove", () => {
  it("初期局面での合法な指し手をtrueと判定する", () => {
    expect(isLegalMove("startpos", "7g7f")).toBe(true);
  });

  it("初期局面での非合法な指し手(自分の駒がない場所からの移動)をfalseと判定する", () => {
    expect(isLegalMove("startpos", "5e5d")).toBe(false);
  });

  it("USIとして解析できない文字列をfalseと判定する", () => {
    expect(isLegalMove("startpos", "not-a-move")).toBe(false);
  });

  it("壊れたSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => isLegalMove("not-a-valid-sfen", "7g7f")).toThrow(InvalidSfenError);
  });
});
