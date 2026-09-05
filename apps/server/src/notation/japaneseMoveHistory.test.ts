import { Board } from "shogiops/board";
import { Hand, Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import { toJapaneseMoveHistory } from "./japaneseMoveHistory.js";

// 任意の駒配置からSFENを組み立てる(stateResponse.test.tsのcustomSfenと同じ方式)。
function customSfen(pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }>, hands?: Hands): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: hands ?? Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("toJapaneseMoveHistory", () => {
  it("通常の指し手(初手)をshogiopsの日本語棋譜表記へ変換する", () => {
    expect(toJapaneseMoveHistory(["7g7f"])).toEqual(["７六歩"]);
  });

  it("複数手を1手ずつ、直前の局面から順に変換する", () => {
    // 7g7f, 3c3d, 8h2b+(角が銀を取って成る), 3a2b(直前の手と同じマスへ動く=「同」表記)
    expect(toJapaneseMoveHistory(["7g7f", "3c3d", "8h2b+", "3a2b"])).toEqual([
      "７六歩",
      "３四歩",
      "２二角成",
      "同　銀",
    ]);
  });

  it("成り/不成りを、生成されたUSIの+の有無どおりにshogiops自身が判定した表記で返す(このモジュールでは判定しない)", () => {
    const sfen = customSfen([
      { square: "5i", color: "sente", role: "king" },
      { square: "2b", color: "sente", role: "silver" },
      { square: "5a", color: "gote", role: "king" },
    ]);
    expect(toJapaneseMoveHistory(["2b1a"], sfen)).toEqual(["１一銀不成"]);
    expect(toJapaneseMoveHistory(["2b1a+"], sfen)).toEqual(["１一銀成"]);
  });

  it("持ち駒を打つ手も変換する", () => {
    const hands = Hands.from(Hand.from([["pawn", 1]]), Hand.empty());
    const sfen = customSfen(
      [
        { square: "5i", color: "sente", role: "king" },
        { square: "5a", color: "gote", role: "king" },
      ],
      hands,
    );
    expect(toJapaneseMoveHistory(["P*5e"], sfen)).toEqual(["５五歩"]);
  });

  it("直前の手と移動先が同じ場合、「同」表記になる(呼び出し側がlastDestを正しく引き継ぐことの確認)", () => {
    const sfen = customSfen([
      { square: "5i", color: "sente", role: "king" },
      { square: "4d", color: "sente", role: "silver" },
      { square: "5a", color: "gote", role: "king" },
      { square: "5e", color: "gote", role: "pawn" },
      { square: "6d", color: "gote", role: "silver" },
    ]);
    expect(toJapaneseMoveHistory(["4d5e", "6d5e"], sfen)).toEqual(["５五銀", "同　銀"]);
  });

  it("空の指し手履歴に対しては空配列を返す", () => {
    expect(toJapaneseMoveHistory([])).toEqual([]);
  });

  it("非合法な指し手が含まれる場合、applyMove.ts(既存)のIllegalMoveErrorがそのまま伝播する", () => {
    // 初期局面でこの筋の歩は既に7fに動けるが、いきなり2マス先(7e)へは動けない(非合法)。
    expect(() => toJapaneseMoveHistory(["7g7e"])).toThrow();
  });
});
