// isSquareAttacked(STEP 5-E)のテスト。
// 利きの計算そのものはshogiops(squareAttackers)の責務のため、ここで確認するのは
// 「配線が正しいこと」(指定したマスに、指定した色の駒の利きが届いているかどうか)。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import { InvalidSfenError, InvalidSquareError, isSquareAttacked } from "./squareAttack.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

describe("isSquareAttacked", () => {
  it("初期局面では、どちらの色の駒からも利きが届いていないマスがある(5e)", () => {
    expect(isSquareAttacked(INITIAL_SFEN, "5e", "sente")).toBe(false);
    expect(isSquareAttacked(INITIAL_SFEN, "5e", "gote")).toBe(false);
  });

  it("玉のマスでも判定できる(listAttackedPiecesは玉を除外するが、これは除外しない)", () => {
    // 5七の後手飛車が、5九の先手玉に利きが届いている(rules/gameStatus.test.tsと同じ局面)。
    const senteInCheck = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

    expect(isSquareAttacked(senteInCheck, "5i", "gote")).toBe(true);
    // 後手玉(5一)には、先手側(玉だけ)の利きは届いていない。
    expect(isSquareAttacked(senteInCheck, "5a", "sente")).toBe(false);
  });

  it("利きが届いていないマスは false", () => {
    const senteInCheck = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

    expect(isSquareAttacked(senteInCheck, "1a", "sente")).toBe(false);
  });

  it("駒が置かれていないマスでも、玉に利きが届いている駒種を問わず判定できる", () => {
    // 実戦局面(rules/attackedPieces.test.tsと同じA局30手目)。後手の8g金は
    // 縦横に利きを持ち、玉のマス(7h)にも利きが届いている。listAttackedPiecesは
    // 玉を除外するため、この事実はlistAttackedPiecesでは確認できない。
    const sfen = "ln1gk1snl/1r5b1/p2p1p1pp/1pps2p2/4p4/5PP2/PgS1PGNPP/1B1R2SK1/LN3G2L b 3p 31";

    expect(isSquareAttacked(sfen, "7h", "gote")).toBe(true);
  });

  it("打つ手の移動先(まだ駒が無いマス)でも判定できる", () => {
    // 5七の後手飛車が5筋に利きを持つので、5五(空マス)にも利きが届いている。
    const sfen = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

    expect(isSquareAttacked(sfen, "5e", "gote")).toBe(true);
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => isSquareAttacked("not-a-valid-sfen", "5e", "sente")).toThrow(InvalidSfenError);
  });

  it("不正なマス目表記に対してInvalidSquareErrorを投げる", () => {
    expect(() => isSquareAttacked(INITIAL_SFEN, "not-a-square", "sente")).toThrow(InvalidSquareError);
  });
});
