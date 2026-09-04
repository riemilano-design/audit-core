import { describe, expect, it, vi } from "vitest";
import { DEFAULT_MAX_FORCED_OPPONENT_PLIES } from "../engine/forcedOpponentOpening.js";
import {
  createInitialGameState,
  getStatus,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  type GameState,
} from "./gameSession.js";

// 先手が7g7fと指した後の局面(後手番)。forcedOpponentOpening.test.tsと同じ局面を使う。
const GOTE_TURN_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL w - 2";

function unusedEngineMock() {
  return {
    position: vi.fn(() => {
      throw new Error("engineは呼ばれないはずです");
    }),
    go: vi.fn(async () => {
      throw new Error("engineは呼ばれないはずです");
    }),
  };
}

describe("createInitialGameState / getStatus", () => {
  it("初期状態は指し手履歴が空で、終局していない", () => {
    const state = createInitialGameState();
    expect(state.moveHistory).toEqual([]);
    expect(state.forcedPliesUsed).toBe(0);
    expect(getStatus(state)).toEqual({ isEnd: false, outcome: undefined });
  });
});

describe("playHumanMove", () => {
  it("合法手を適用し、履歴に追加する", () => {
    const state = createInitialGameState();
    const next = playHumanMove(state, "7g7f");
    expect(next.moveHistory).toEqual(["7g7f"]);
    expect(next.sfen).not.toBe(state.sfen);
  });

  it("非合法な手にHumanMoveErrorを投げる(元のstateは変更しない)", () => {
    const state = createInitialGameState();
    expect(() => playHumanMove(state, "5e5d")).toThrow(HumanMoveError);
    expect(state.moveHistory).toEqual([]);
  });
});

describe("playOpponentMove", () => {
  it("強制進行の範囲内では、エンジンを呼ばずに指し手を選ぶ", async () => {
    const state: GameState = { sfen: GOTE_TURN_SFEN, moveHistory: ["7g7f"], forcedPliesUsed: 0 };
    const engine = unusedEngineMock();
    const next = await playOpponentMove(state, engine);
    expect(next.moveHistory).toEqual(["7g7f", expect.any(String)]);
    expect(next.forcedPliesUsed).toBe(1);
    expect(engine.position).not.toHaveBeenCalled();
    expect(engine.go).not.toHaveBeenCalled();
  });

  it("強制進行の手数を使い切った後は、エンジンのbestmoveを使う", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: DEFAULT_MAX_FORCED_OPPONENT_PLIES,
    };
    const engine = {
      position: vi.fn(),
      go: vi.fn(async () => ({
        bestmove: "3c3d",
        ponder: undefined,
        scoreCp: undefined,
        infoLines: [],
      })),
    };
    const next = await playOpponentMove(state, engine);
    expect(engine.position).toHaveBeenCalledWith(GOTE_TURN_SFEN);
    expect(engine.go).toHaveBeenCalled();
    expect(next.moveHistory).toEqual(["3c3d"]);
    expect(next.forcedPliesUsed).toBe(DEFAULT_MAX_FORCED_OPPONENT_PLIES);
  });

  it("エンジンがresignを返した場合、局面を変えずそのまま返す", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: DEFAULT_MAX_FORCED_OPPONENT_PLIES,
    };
    const engine = {
      position: vi.fn(),
      go: vi.fn(async () => ({
        bestmove: "resign",
        ponder: undefined,
        scoreCp: undefined,
        infoLines: [],
      })),
    };
    const next = await playOpponentMove(state, engine);
    expect(next).toEqual(state);
  });
});
