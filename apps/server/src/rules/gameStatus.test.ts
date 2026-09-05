// gameStatus.ts の isInCheck(Phase6 Unit4で追加)のテスト。
// 王手判定そのものはshogiopsの責務のため、ここで確認するのは「配線が正しいこと」
// (指定した色の玉について判定していること)。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import { isInCheck } from "./gameStatus.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

describe("isInCheck", () => {
  it("初期局面では、どちらの玉にも王手はかかっていない", () => {
    expect(isInCheck(INITIAL_SFEN, "sente")).toBe(false);
    expect(isInCheck(INITIAL_SFEN, "gote")).toBe(false);
  });

  it("指定した色の玉について判定する(手番ではなく色で判定する)", () => {
    // 5七の後手の飛車が、5九の先手玉に王手をかけている局面。
    const senteInCheck = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

    expect(isInCheck(senteInCheck, "sente")).toBe(true);
    expect(isInCheck(senteInCheck, "gote")).toBe(false);
  });
});
