import { describe, expect, it, vi } from "vitest";
import { DEFAULT_MAX_FORCED_OPPONENT_PLIES } from "../engine/forcedOpponentOpening.js";
import type { ApprovedScenarioVariant } from "../engine/scenarioRepository.js";
import {
  createInitialGameState,
  getStatus,
  HumanMoveError,
  playHumanMove,
  playOpponentMove,
  toHumanMoveErrorMessage,
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

  it("scenarioを指定すると、GameStateにそのまま保持される(通常対局は従来どおりundefined)", () => {
    expect(createInitialGameState().scenario).toBeUndefined();
    expect(createInitialGameState("hayajikake").scenario).toBe("hayajikake");
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

  // STEP 4-7B(P-11。人間承認 H-1): ユーザー向けのHumanMoveError.messageから
  // SFENを除去する。
  it("非合法な手のHumanMoveError.messageがSFENを含まず、既存文からSFEN部分だけを除いた文になる", () => {
    const state = createInitialGameState();
    let thrown: unknown;
    try {
      playHumanMove(state, "5e5d");
    } catch (err) {
      thrown = err;
    }
    expect(thrown).toBeInstanceOf(HumanMoveError);
    expect((thrown as HumanMoveError).message).toBe('非合法な指し手です: "5e5d"');
    expect((thrown as HumanMoveError).message).not.toContain("局面:");
    expect((thrown as HumanMoveError).message).not.toContain(state.sfen);
  });
});

describe("toHumanMoveErrorMessage", () => {
  it("末尾の「(局面: \"…\")」を取り除く", () => {
    expect(
      toHumanMoveErrorMessage('非合法な指し手です: "7g7f"(局面: "lnsgkgsnl/9/ppppppppp/9/9/9/PPPPPPPPP/9/LNSGKGSNL b - 1")'),
    ).toBe('非合法な指し手です: "7g7f"');
  });

  it("該当する末尾が無ければそのまま返す(applyMove.tsの解析失敗メッセージ)", () => {
    expect(toHumanMoveErrorMessage('指し手の解析に失敗しました: "xyz"')).toBe(
      '指し手の解析に失敗しました: "xyz"',
    );
  });
});

describe("playOpponentMove", () => {
  // Phase 7 Unit 0: forcedOpponentOpening(居飛車強制)は本番導線から外れた
  // ([../../../../CLAUDE.md](../../../../CLAUDE.md) の「絶対的な上位原則」)。
  // 旧テスト「強制進行の範囲内では、エンジンを呼ばずに指し手を選ぶ」が固定していた
  // 仕様(通常対局でforcedOpponentOpeningを使う)は撤回されたため、「通常対局
  // (scenario未指定)では、forcedPliesUsedの範囲内でもエンジンのbestmoveへ落ちる」
  // ことを検証する形へ書き換える。
  it("通常対局(scenario未指定)では、forcedPliesUsedの範囲内でもエンジンのbestmoveを使う", async () => {
    const state: GameState = { sfen: GOTE_TURN_SFEN, moveHistory: ["7g7f"], forcedPliesUsed: 0 };
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
    expect(next.moveHistory).toEqual(["7g7f", "3c3d"]);
    // forcedOpponentOpeningの経路を通らないため、forcedPliesUsedは増えないまま。
    expect(next.forcedPliesUsed).toBe(0);
  });

  // Phase 7 Unit 0: 旧テスト「強制進行の手が採用された場合、wasLastOpponentMoveForcedは
  // trueになる」(scenario未指定)が固定していた仕様も撤回されたため、
  // 「通常対局ではwasLastOpponentMoveForcedがfalseになる(エンジンの手が採用される)」
  // ことを検証する形へ書き換える。
  it("通常対局(scenario未指定)でエンジンのbestmoveが採用された場合、wasLastOpponentMoveForcedはfalseになる", async () => {
    const state: GameState = { sfen: GOTE_TURN_SFEN, moveHistory: ["7g7f"], forcedPliesUsed: 0 };
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
    expect(next.wasLastOpponentMoveForced).toBe(false);
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

  // Phase4 B: engineのbestmoveが採用された場合、wasLastOpponentMoveForcedはfalseになる。
  it("エンジンのbestmoveが採用された場合、wasLastOpponentMoveForcedはfalseになる", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: DEFAULT_MAX_FORCED_OPPONENT_PLIES,
      wasLastOpponentMoveForced: true,
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
    expect(next.wasLastOpponentMoveForced).toBe(false);
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

  // Phase4 C: 実際に着手が行われないケース(resign等)では、既存のwasLastOpponentMoveForced
  // をそのまま維持する(推測で書き換えない)。
  it("エンジンがresignを返した場合、wasLastOpponentMoveForcedは変化しない(既存値を維持)", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: DEFAULT_MAX_FORCED_OPPONENT_PLIES,
      wasLastOpponentMoveForced: true,
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
    expect(next.wasLastOpponentMoveForced).toBe(true);
  });

  it("scenario指定時は、エンジンのbestmoveではなくscenarioOpponentOpeningの手を使う", async () => {
    // scenarioOpponentOpening.test.tsと揃えた検証用の局面であり、
    // hayajikakeシナリオでは1手目として6c6dを選ぶはず(scenarioOpponentOpening.test.ts参照)。
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      scenario: "hayajikake",
    };
    const engine = unusedEngineMock();
    const next = await playOpponentMove(state, engine);
    expect(next.moveHistory).toEqual(["7g7f", "6c6d"]);
    expect(next.forcedPliesUsed).toBe(1);
    expect(next.scenario).toBe("hayajikake");
    expect(engine.position).not.toHaveBeenCalled();
  });

  // Phase4 D: scenario対局でもforced moveが採用された場合はtrueになる。
  it("scenario対局でforced moveが採用された場合、wasLastOpponentMoveForcedはtrueになる", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      scenario: "hayajikake",
    };
    const engine = unusedEngineMock();
    const next = await playOpponentMove(state, engine);
    expect(next.wasLastOpponentMoveForced).toBe(true);
  });

  it("scenarioの手を使い切った後は、エンジンのbestmoveにフォールバックする", async () => {
    // hayajikakeは2手しか無いため、forcedPliesUsed=2の時点で既に尽きている。
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: 2,
      scenario: "hayajikake",
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
    expect(engine.go).toHaveBeenCalled();
    expect(next.moveHistory).toEqual(["3c3d"]);
    expect(next.scenario).toBe("hayajikake");
  });

  // Phase4 E: scenarioの手を使い切ってengine fallbackになった場合はfalseになる。
  it("scenarioの手を使い切ってengineにフォールバックした場合、wasLastOpponentMoveForcedはfalseになる", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: [],
      forcedPliesUsed: 2,
      scenario: "hayajikake",
      wasLastOpponentMoveForced: true,
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
    expect(next.wasLastOpponentMoveForced).toBe(false);
  });
});

// STEP ζ-4c-1: createInitialGameStateの第2引数(相手AI制御の候補・seed)。
describe("createInitialGameState (相手AI制御, STEP ζ-4c-1)", () => {
  it("controlを渡さない場合、opponentControlはundefinedのまま(既存の呼び出し・挙動を変えない)", () => {
    expect(createInitialGameState().opponentControl).toBeUndefined();
    expect(createInitialGameState("hayajikake").opponentControl).toBeUndefined();
  });

  it("control.variantsが空配列の場合、opponentControlは作られるがselectedVariantIdはundefined(承認済み候補0件)", () => {
    const state = createInitialGameState(undefined, { variants: [], seed: 1 });
    expect(state.opponentControl).toEqual({ seed: 1, selectedVariantId: undefined, movesUsed: 0 });
  });

  it("control.variantsに1件だけあれば、それが必ず選ばれる", () => {
    const variant: ApprovedScenarioVariant = {
      openingId: "test_opening",
      variantId: "test_variant",
      targetIntentId: "hayajikake",
      moves: ["6c6d"],
    };
    const state = createInitialGameState(undefined, { variants: [variant], seed: 1 });
    expect(state.opponentControl?.selectedVariantId).toBe("test_opening/test_variant");
    expect(state.opponentControl?.movesUsed).toBe(0);
    expect(state.opponentControl?.seed).toBe(1);
  });
});

// STEP ζ-4c-1: playOpponentMoveの経路1(相手AI制御, opponentControl)。
// 経路の優先順位は 1.opponentControl -> 2.scenario(開発モード専用) -> 3.エンジン。
// Phase 7 Unit 0: forcedOpponentOpening(旧・経路3)は本番導線から外れ、
// scenario未指定の場合は経路2を飛ばして直接エンジンへ落ちる。
describe("playOpponentMove (相手AI制御, STEP ζ-4c-1)", () => {
  const variant: ApprovedScenarioVariant = {
    openingId: "test_opening",
    variantId: "test_variant",
    targetIntentId: "hayajikake",
    // gameSession.playOpponentMoveのテスト内で既に合法性が確認されている手順
    // (scenarioOpponentOpening.tsのHAYAJIKAKE_SCRIPTと同じ手。新しい将棋知識ではない)。
    moves: ["6c6d", "6d6e"],
  };

  // Phase 7 Unit 0: 旧テスト「承認済みvariantが0件のとき、既存のforcedOpponentOpeningの
  // 経路が変わらず使われる」が固定していた仕様(通常対局でforcedOpponentOpeningを使う)は
  // 撤回されたため、「通常対局(scenario未指定)ではエンジンへ落ちる」ことを検証する
  // 形へ書き換える。
  it("承認済みvariantが0件(selectedVariantIdがundefined)かつscenario未指定のとき、通常対局ではエンジンへ落ちる", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      opponentControl: { seed: 1, selectedVariantId: undefined, movesUsed: 0 },
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
    const next = await playOpponentMove(state, engine, []);
    expect(engine.position).toHaveBeenCalledWith(GOTE_TURN_SFEN);
    expect(engine.go).toHaveBeenCalled();
    expect(next.moveHistory).toEqual(["7g7f", "3c3d"]);
    expect(next.forcedPliesUsed).toBe(0);
    expect(next.wasLastOpponentMoveForced).toBe(false);
  });

  it("scenario指定時、承認済みvariantが0件でも既存のscenarioOpponentOpeningの経路が変わらず使われる", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      scenario: "hayajikake",
      opponentControl: { seed: 1, selectedVariantId: undefined, movesUsed: 0 },
    };
    const engine = unusedEngineMock();
    const next = await playOpponentMove(state, engine, []);
    expect(next.moveHistory).toEqual(["7g7f", "6c6d"]);
    expect(engine.position).not.toHaveBeenCalled();
  });

  it("承認済みvariantの1手目が現局面で合法なら、それを採用しmovesUsedを1増やす", async () => {
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      opponentControl: { seed: 1, selectedVariantId: "test_opening/test_variant", movesUsed: 0 },
    };
    const engine = unusedEngineMock();
    const next = await playOpponentMove(state, engine, [variant]);
    expect(next.moveHistory).toEqual(["7g7f", "6c6d"]);
    expect(next.opponentControl).toEqual({ seed: 1, selectedVariantId: "test_opening/test_variant", movesUsed: 1 });
    expect(next.wasLastOpponentMoveForced).toBe(true);
    expect(engine.position).not.toHaveBeenCalled();
  });

  // Phase 7 Unit 0: 旧テストは非合法時のフォールバック先をforcedOpponentOpening
  // (経路3、当時)としていたが、この経路は本番導線から外れた。scenario未指定の
  // 通常対局では、経路1が発動しない場合エンジン(経路3)へ直接フォールバックする
  // ことを検証する形へ書き換える。
  it("次の手がその場の局面で非合法な場合、経路1は発動せず(movesUsedは増えない)、通常対局ではエンジンへフォールバックする", async () => {
    // moves[1]("6d6e")は、まだ1手目("6c6d")が適用されておらず(GOTE_TURN_SFENのまま)、
    // gote歩は6cのままなので非合法(scenarioOpponentOpening.test.tsの
    // 「人間の手でシナリオの想定局面が崩れ、次の手が非合法になった場合はundefinedを返す」と同じ考え方)。
    const state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      opponentControl: { seed: 1, selectedVariantId: "test_opening/test_variant", movesUsed: 1 },
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
    const next = await playOpponentMove(state, engine, [variant]);
    expect(next.opponentControl?.movesUsed).toBe(1);
    expect(next.wasLastOpponentMoveForced).toBe(false);
    expect(engine.position).toHaveBeenCalledWith(GOTE_TURN_SFEN);
    expect(engine.go).toHaveBeenCalled();
    expect(next.moveHistory).toEqual(["7g7f", "3c3d"]);
  });

  // Phase 7 Unit 0: 旧テストは、variantを使い切った後のフォールバック先を
  // forcedOpponentOpening(当時の経路3)としていたが、この経路は本番導線から
  // 外れた。scenario未指定の通常対局では、variantを使い切るとエンジンへ
  // フォールバックすることを検証する形へ書き換える。
  it("複数手にわたって、承認済みvariantの手が順に指され、使い切ると通常対局ではエンジンへフォールバックする。playHumanMoveを挟んでもopponentControlは引き継がれる", async () => {
    let state: GameState = {
      sfen: GOTE_TURN_SFEN,
      moveHistory: ["7g7f"],
      forcedPliesUsed: 0,
      opponentControl: { seed: 1, selectedVariantId: "test_opening/test_variant", movesUsed: 0 },
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

    // 1手目: variantの手(6c6d)が採用される(経路1。エンジンは呼ばれない)。
    state = await playOpponentMove(state, engine, [variant]);
    expect(state.moveHistory.at(-1)).toBe("6c6d");
    expect(state.opponentControl?.movesUsed).toBe(1);
    expect(engine.position).not.toHaveBeenCalled();

    // 人間側の一手(playHumanMoveを挟んでもopponentControlが消えないことの確認)。
    state = playHumanMove(state, "1g1f");
    expect(state.opponentControl).toEqual({ seed: 1, selectedVariantId: "test_opening/test_variant", movesUsed: 1 });

    // 2手目: variantの手(6d6e)が採用される(経路1。エンジンは呼ばれない)。
    state = await playOpponentMove(state, engine, [variant]);
    expect(state.moveHistory.at(-1)).toBe("6d6e");
    expect(state.opponentControl?.movesUsed).toBe(2);
    expect(engine.position).not.toHaveBeenCalled();

    // 人間側の一手。
    state = playHumanMove(state, "2g2f");
    expect(state.opponentControl?.movesUsed).toBe(2);

    // 3手目: variantのmovesを使い切った(moves[2]は存在しない)ため、
    // scenario未指定の通常対局ではエンジンへフォールバックする(Phase 7 Unit 0)。
    state = await playOpponentMove(state, engine, [variant]);
    expect(state.opponentControl?.movesUsed).toBe(2);
    expect(state.forcedPliesUsed).toBe(0);
    expect(state.wasLastOpponentMoveForced).toBe(false);
    expect(engine.position).toHaveBeenCalledTimes(1);
    expect(engine.go).toHaveBeenCalledTimes(1);
    expect(state.moveHistory.at(-1)).toBe("3c3d");
  });
});
