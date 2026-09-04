import { parseSfen } from "shogiops/sfen";
import { parseUsi } from "shogiops/util";
import { describe, expect, it } from "vitest";
import { isLegalMove } from "../rules/legalMoves.js";
import {
  DEFAULT_MAX_FORCED_OPPONENT_PLIES,
  InvalidSfenError,
  pickForcedOpponentMove,
} from "./forcedOpponentOpening.js";

// 先手が7g7fと指した後の局面(後手番)。強制進行の対象は常に「その局面の手番側」。
const GOTE_TURN_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";

describe("pickForcedOpponentMove", () => {
  it("返す手は合法手である", () => {
    const move = pickForcedOpponentMove(GOTE_TURN_SFEN, 0);
    expect(move).toBeDefined();
    expect(isLegalMove(GOTE_TURN_SFEN, move as string)).toBe(true);
  });

  it("飛車を動かす手を選ばない", () => {
    const move = pickForcedOpponentMove(GOTE_TURN_SFEN, 0);
    const md = parseUsi(move as string);
    expect(md).toBeDefined();
    if (md && "from" in md) {
      const pos = parseSfen("standard", GOTE_TURN_SFEN).unwrap();
      expect(pos.board.get(md.from)?.role).not.toBe("rook");
    }
  });

  it("同じ局面・同じforcedPliesSoFarに対して同じ手を決定的に返す", () => {
    const first = pickForcedOpponentMove(GOTE_TURN_SFEN, 0);
    const second = pickForcedOpponentMove(GOTE_TURN_SFEN, 0);
    expect(first).toBe(second);
  });

  it("maxForcedPlies以降はundefinedを返す(呼び出し側がエンジンに委ねる合図)", () => {
    expect(pickForcedOpponentMove(GOTE_TURN_SFEN, DEFAULT_MAX_FORCED_OPPONENT_PLIES)).toBeUndefined();
    expect(pickForcedOpponentMove(GOTE_TURN_SFEN, DEFAULT_MAX_FORCED_OPPONENT_PLIES + 1)).toBeUndefined();
  });

  it("maxForcedPliesを明示的に指定できる", () => {
    expect(pickForcedOpponentMove(GOTE_TURN_SFEN, 1, { maxForcedPlies: 1 })).toBeUndefined();
    expect(pickForcedOpponentMove(GOTE_TURN_SFEN, 0, { maxForcedPlies: 1 })).toBeDefined();
  });

  it("壊れたSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => pickForcedOpponentMove("not-a-valid-sfen", 0)).toThrow(InvalidSfenError);
  });
});
