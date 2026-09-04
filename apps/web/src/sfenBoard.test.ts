import { describe, expect, it } from "vitest";
import { parseSfenBoardPart, parseSfenHands, parseSfenTurn } from "./sfenBoard.js";

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

describe("parseSfenBoardPart", () => {
  it("初期局面を9x9の駒配置に変換する", () => {
    const board = parseSfenBoardPart(STARTPOS_SFEN);
    expect(board).toHaveLength(9);
    for (const rank of board) expect(rank).toHaveLength(9);

    // 1段目(gote側)の左端は香(L)
    expect(board[0]?.[0]).toEqual({ piece: "L", color: "gote" });
    // 9段目(sente側)の右端は香
    expect(board[8]?.[8]).toEqual({ piece: "L", color: "sente" });
    // 3段目はgoteの歩が9枚並ぶ
    for (const square of board[2] ?? []) {
      expect(square).toEqual({ piece: "P", color: "gote" });
    }
    // 空きマスはnull
    expect(board[3]?.[0]).toBeNull();
  });

  it("成り駒(+付き)を正しく解釈する", () => {
    // 5五の位置に後手のと金(+p)、それ以外は空きマスの架空の1段。
    const board = parseSfenBoardPart("9/9/9/9/4+p4/9/9/9/9 b - 1");
    expect(board[4]?.[4]).toEqual({ piece: "+P", color: "gote" });
  });

  it("段数が9でないSFENでエラーを投げる", () => {
    expect(() => parseSfenBoardPart("9/9 b - 1")).toThrow();
  });
});

describe("parseSfenTurn", () => {
  it("bを先手、wを後手と判定する", () => {
    expect(parseSfenTurn(STARTPOS_SFEN)).toBe("sente");
    expect(parseSfenTurn(STARTPOS_SFEN.replace(" b ", " w "))).toBe("gote");
  });
});

describe("parseSfenHands", () => {
  it("持ち駒なし('-')は空を返す", () => {
    expect(parseSfenHands(STARTPOS_SFEN)).toEqual({ sente: {}, gote: {} });
  });

  it("複数種類・複数枚の持ち駒を解釈する", () => {
    const sfen = "9/9/9/9/9/9/9/9/9 b S2Pb 1";
    expect(parseSfenHands(sfen)).toEqual({
      sente: { S: 1, P: 2 },
      gote: { B: 1 },
    });
  });
});
