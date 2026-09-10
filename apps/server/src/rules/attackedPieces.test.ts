// listAttackedPieces(Phase 7 Unit 4 STEP 4-3)のテスト。
// 利きの計算そのものはshogiops(squareAttackers)の責務のため、ここで確認するのは
// 「配線が正しいこと」(自分の駒のうち、玉を除いて相手の利きが届いているものを
// 正しく列挙すること)。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import { InvalidSfenError, listAttackedPieces } from "./attackedPieces.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

describe("listAttackedPieces", () => {
  it("初期局面では、どちらの色にも当たっている駒は無い", () => {
    expect(listAttackedPieces(INITIAL_SFEN, "sente")).toEqual([]);
    expect(listAttackedPieces(INITIAL_SFEN, "gote")).toEqual([]);
  });

  it("実戦局面(A局30手目・８七金の直後)で、角８八・銀７七・歩９七の3件が金８七から当たっている", () => {
    const sfen = "ln1gk1snl/1r5b1/p2p1p1pp/1pps2p2/4p4/5PP2/PgS1PGNPP/1B1R2SK1/LN3G2L b 3p 31";

    expect(listAttackedPieces(sfen, "sente")).toEqual([
      { square: "7g", role: "silver", attackers: [{ square: "8g", role: "gold" }] },
      { square: "9g", role: "pawn", attackers: [{ square: "8g", role: "gold" }] },
      { square: "8h", role: "bishop", attackers: [{ square: "8g", role: "gold" }] },
    ]);
  });

  it("実戦局面(C局30手目・３六歩打の直後)で、桂３七が歩３六から当たっている", () => {
    const sfen = "lnsgk2nl/4r2b1/pp1p2gpp/2p2s3/4p1P2/2PP1pp2/PP1SPPNPP/1B1RG1SK1/LN3G2L b - 31";

    const result = listAttackedPieces(sfen, "sente");
    expect(result).toContainEqual({
      square: "3g",
      role: "knight",
      attackers: [{ square: "3f", role: "pawn" }],
    });
  });

  it("玉は含めない(玉に王手がかかっていても列挙しない)", () => {
    // 5七の後手の飛車が、5九の先手玉に王手をかけている局面(gameStatus.test.tsと同じ)。
    // 先手の盤上の駒は玉だけなので、返り値は0件になる。
    const senteInCheck = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

    expect(listAttackedPieces(senteInCheck, "sente")).toEqual([]);
  });

  it("成駒(龍・と金)の役職をそのまま返す(正規化しない)", () => {
    // 先手の龍(3e)が後手の角(5c)から当たっており、先手の銀(2g)が後手のと金(2f)から
    // 当たっている。玉はどちらも王手を受けていない。
    const sfen = "8k/9/4b4/9/6+R2/7+p1/7S1/9/8K b - 1";

    expect(listAttackedPieces(sfen, "sente")).toEqual([
      { square: "3e", role: "dragon", attackers: [{ square: "5c", role: "bishop" }] },
      { square: "2g", role: "silver", attackers: [{ square: "2f", role: "tokin" }] },
    ]);
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => listAttackedPieces("not-a-valid-sfen", "sente")).toThrow(InvalidSfenError);
  });
});
