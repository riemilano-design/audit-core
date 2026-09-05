import { describe, expect, it } from "vitest";
import { toJapaneseMoveSquares, toJapaneseSquare, toJapaneseSquarePath } from "./japaneseSquare.js";

describe("toJapaneseSquare", () => {
  it("1. USI形式のマス目を日本語表記に変換する", () => {
    expect(toJapaneseSquare("8h")).toBe("８八");
    expect(toJapaneseSquare("5i")).toBe("５九");
    expect(toJapaneseSquare("1a")).toBe("１一");
    expect(toJapaneseSquare("9i")).toBe("９九");
  });

  it("2. docs/DATA_MODEL.mdの段の対応表(a〜i = 一〜九)どおりに変換する", () => {
    const ranks = ["a", "b", "c", "d", "e", "f", "g", "h", "i"];
    const expected = ["一", "二", "三", "四", "五", "六", "七", "八", "九"];
    expect(ranks.map((rank) => toJapaneseSquare(`5${rank}`))).toEqual(expected.map((r) => `５${r}`));
  });

  it("3. 解釈できない文字列は例外を投げず、そのまま返す", () => {
    expect(toJapaneseSquare("")).toBe("");
    expect(toJapaneseSquare("zz")).toBe("zz");
    expect(toJapaneseSquare("5i6h")).toBe("5i6h");
    expect(toJapaneseSquare("0a")).toBe("0a");
  });

  it("4. 経路(マス目の並び)を矢印でつないだ1つの文字列にする", () => {
    expect(toJapaneseSquarePath(["5i", "6h", "7h", "8h"])).toBe("５九→６八→７八→８八");
    expect(toJapaneseSquarePath(["7i", "7h"])).toBe("７九→７八");
    expect(toJapaneseSquarePath([])).toBe("");
  });
});

describe("toJapaneseMoveSquares", () => {
  it("1. USI形式の指し手を、移動元→移動先のマス目表記に変換する", () => {
    expect(toJapaneseMoveSquares("5i6h")).toBe("５九→６八");
    expect(toJapaneseMoveSquares("7g7f")).toBe("７七→７六");
  });

  it("2. 成りを表す'+'が付いていてもマス目部分だけを変換する", () => {
    expect(toJapaneseMoveSquares("5d5c+")).toBe("５四→５三");
  });

  it("3. ドロップ・解釈できない文字列は例外を投げずそのまま返す", () => {
    expect(toJapaneseMoveSquares("P*5e")).toBe("P*5e");
    expect(toJapaneseMoveSquares("")).toBe("");
    expect(toJapaneseMoveSquares("zzzz")).toBe("zzzz");
  });
});
