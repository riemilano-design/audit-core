import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Role } from "shogiops/types";
import { describe, expect, it, vi } from "vitest";
import type { CoachExplanation } from "../analysis/explanationGenerator.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../analysis/moveHistory.js";
import type { GameState } from "../game/gameSession.js";
import type { MultiPvGoResult } from "../engine/usiEngine.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";
import {
  buildStateResponse,
  buildStateResponseWithPlan,
  computeReachablePlan,
  safeComputeReachablePlan,
  type CachedReachablePlan,
} from "./stateResponse.js";

const SENTE_FILLERS = ["1g1f", "2g2f", "3g3f", "4g4f", "5g5f", "6g6f", "9g9f", "8g8f"];

function interleaveWithSenteFillers(goteMoves: string[]): string[] {
  const moves: string[] = [];
  goteMoves.forEach((goteMove, i) => {
    const filler = SENTE_FILLERS[i];
    if (!filler) throw new Error("SENTE_FILLERSが不足しています");
    moves.push(filler, goteMove);
  });
  return moves;
}

function gameStateAfter(moveHistory: string[]): GameState {
  const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
  return { sfen: finalSfen, moveHistory, forcedPliesUsed: 0 };
}

function findStage(coach: CoachExplanation[], stage: CoachExplanation["stage"]): CoachExplanation {
  const found = coach.find((c) => c.stage === stage);
  if (!found) throw new Error(`stage not found: ${stage}`);
  return found;
}

// data/intents/hayajikake.json: 歩 6d(1) -> 6e(2)
const HAYAJIKAKE_GOTE_MOVES_FULL = ["6c6d", "6d6e"];

// 本美濃囲い(mino_honmino)の必須駒配置(8h玉・7h銀・6i金・5h金)がそのまま揃った局面。
// (data/shapes/mino_honmino.jsonの座標をそのまま使用。将棋知識としては既存データそのもの)
function honminoCompletedSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "8h", role: "king" },
    { square: "7h", role: "silver" },
    { square: "6i", role: "gold" },
    { square: "5h", role: "gold" },
  ];
  for (const { square, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color: "sente", role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("buildStateResponse", () => {
  it("初期局面: current_shape/opponent_intent/opponent_next_aimの3件がcoachに含まれる", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponse(state);

    expect(response.coach).toBeDefined();
    const coach = response.coach!;
    expect(coach.map((c) => c.stage)).toEqual(["current_shape", "opponent_intent", "opponent_next_aim"]);
    for (const c of coach) {
      expect(["high", "medium", "low"]).toContain(c.confidence_level);
      expect(["none", "forming", "matched", "completed"]).toContain(c.status);
      expect(c.purpose.length).toBeGreaterThan(0);
      expect(c.reason.length).toBeGreaterThan(0);
    }
    // 既存の対局機能(status/sfen/moveHistory)が壊れていないこと
    expect(response.status.isEnd).toBe(false);
    expect(response.sfen).toBe(state.sfen);
    expect(response.moveHistory).toEqual([]);
  });

  it("none状態: 相手の意図はまだ判断できないため、特定の戦法名を出さない", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponse(state);
    const opponentIntent = findStage(response.coach!, "opponent_intent");

    expect(opponentIntent.status).toBe("none");
    expect(opponentIntent.refers_to_intent_id).toBeNull();
    expect(opponentIntent.confidence_level).toBe("low");
    for (const name of ["棒銀", "斜め棒銀", "早仕掛け"]) {
      expect(opponentIntent.reason).not.toContain(name);
    }
  });

  it("forming状態: 途中段階のIntentを断定表現にしない", () => {
    const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
    const state = gameStateAfter(moveHistory);
    const response = buildStateResponse(state);
    const opponentIntent = findStage(response.coach!, "opponent_intent");

    expect(opponentIntent.status).toBe("forming");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    expect(opponentIntent.reason).toContain("可能性があります");
    expect(opponentIntent.reason).toContain("断定はできません");
    expect(opponentIntent.reason).not.toContain("早仕掛けの形になっています");

    const nextAim = findStage(response.coach!, "opponent_next_aim");
    expect(nextAim.status).toBe("forming");
    expect(nextAim.reason).toContain("断定はできません");
  });

  it("matched状態: Intentが完全一致した場合は確信度の高い言い回しになる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const state = gameStateAfter(moveHistory);
    const response = buildStateResponse(state);
    const opponentIntent = findStage(response.coach!, "opponent_intent");

    expect(opponentIntent.status).toBe("matched");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    expect(opponentIntent.reason).toContain("早仕掛けの形になっています");
    expect(opponentIntent.confidence_level).not.toBe("low");
  });

  it("completed状態: Shapeが完成した局面は名指しで表示される", () => {
    // 本美濃(king8h)は初期配置の角(8h)を動かしてから組む必要があり、実対局の
    // 指し手列で再現すると長くなるため、ここではmoveHistory=[]・initialSfenを
    // この局面自体に上書きして(analysis/intentDetector.tsのsfen/moveHistory整合性
    // チェックを満たしたうえで)直接検証する。
    const sfen = honminoCompletedSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponse(state, { initialSfen: sfen });
    const currentShape = findStage(response.coach!, "current_shape");

    expect(currentShape.status).toBe("completed");
    expect(currentShape.refers_to_shape_id).toBe("mino_honmino");
    expect(currentShape.reason).toContain("本美濃囲いの形ができています");
  });

  it("不正な局面(sfenとmoveHistoryの不整合)でもcoach生成の失敗だけに留まり、既存のstatus等は壊れない", () => {
    // わざと矛盾したGameStateを作る(実運用では起こらないが、安全側の防御を確認する)。
    const inconsistentState: GameState = {
      sfen: DEFAULT_INITIAL_SFEN,
      moveHistory: ["7g7f"], // このsfenはこの履歴の結果ではない
      forcedPliesUsed: 0,
    };

    const response = buildStateResponse(inconsistentState);

    expect(response.coach).toBeUndefined();
    // 対局そのもの(status判定)は説明生成の失敗と無関係に動き続ける
    expect(response.status.isEnd).toBe(false);
    expect(response.sfen).toBe(DEFAULT_INITIAL_SFEN);
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const state = gameStateAfter(moveHistory);
    const first = buildStateResponse(state);
    const second = buildStateResponse(state);
    expect(second).toEqual(first);
  });
});

// 以下、Phase2 ⑤〜⑧(buildStateResponseWithPlan / computeReachablePlan)のテスト。
// 実エンジンは使わず、LowPriorityEngine(Pick<UsiEngine,"position"|"setMultiPv"|"goMultiPv">)
// と構造的に一致するモックで決定的に検証する(candidateMoveSafetyCheck.test.tsと同じ方式)。

function multiPvResult(lines: MultiPvGoResult["lines"], bestmove = "7i8h"): MultiPvGoResult {
  return { bestmove, ponder: undefined, lines, infoLines: [] };
}

function makeMockLowPriorityEngine(
  responses: MultiPvGoResult[] | (() => MultiPvGoResult),
): LowPriorityEngine {
  let call = 0;
  return {
    position: vi.fn(),
    setMultiPv: vi.fn(),
    goMultiPv: vi.fn(async () => {
      if (typeof responses === "function") return responses();
      const result = responses[call];
      call += 1;
      if (!result) throw new Error("モックエンジンへの想定外の呼び出し(レスポンス不足)");
      return result;
    }),
  };
}

function makeThrowingLowPriorityEngine(): LowPriorityEngine {
  return {
    position: vi.fn(),
    setMultiPv: vi.fn(),
    goMultiPv: vi.fn(async () => {
      throw new Error("エンジンがタイムアウトした、という想定");
    }),
  };
}

/** 任意の駒配置からSFENを組み立てる(honminoCompletedSfen()と同じ方式の一般化)。
 * shogiopsのShogi.from(..., false)は相手玉の不在等を許容するため、
 * テストに必要な駒だけを配置すればよい。 */
function customSfen(pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }>): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

// 本美濃囲い(mino_honmino)のうち、玉だけが7iにあり(8hへ1手で届く)、
// 銀7h・金6i・金5hは既に揃っている局面。missingSquares=["8h"]、
// typical_build_order上の対象マスは"8h"(玉)になり、7i8hという合法な候補手が1件だけ存在する。
function honminoOneMoveFromCompleteSfen(): string {
  return customSfen([
    { square: "7i", color: "sente", role: "king" },
    { square: "7h", color: "sente", role: "silver" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
  ]);
}

// 玉8h・金6i・金5hは既に揃い、対象マスは7h(銀)。6g・8gの2枚の銀からそれぞれ
// 1手(斜め後退)で7hへ到達できる(複数候補の検証用。将棋の実戦性は問わない、
// 合法手抽出ロジックの検証が目的)。6iの金も物理的には7hへ動けるが、対象マスの
// 駒種(銀)と一致しないためpathPlanner.tsの駒種フィルタで候補から除外される。
function honminoMultipleCandidatesSfen(): string {
  return customSfen([
    { square: "8h", color: "sente", role: "king" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "6g", color: "sente", role: "silver" },
    { square: "8g", color: "sente", role: "silver" },
  ]);
}

function customGameState(sfen: string): GameState {
  return { sfen, moveHistory: [], forcedPliesUsed: 0 };
}

describe("buildStateResponseWithPlan", () => {
  it("candidate moveが空: 初期局面(玉が8hへ1手で届かない)ではcandidateMoveState: unavailableになる", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined);

    expect(response.plan.reachableShapes.length).toBeGreaterThan(0);
    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.candidateMove).toBeUndefined();
    // Phase1の既存coach(shapeDetector/shapeFormationAnalyzer/intentDetector/explanationGenerator)は
    // buildStateResponseと完全に同じ内容のまま壊れていないこと。
    expect(response.coach).toEqual(buildStateResponse(state).coach);
  });

  it("候補手はあるが、まだバックグラウンド解析が完了していない(cachedPlanなし)場合はpendingになる", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.plan.candidateMoveState).toBe("pending");
    expect(response.plan.candidateMove).toBeUndefined();
  });

  it("cachedPlanのsfenが現在の局面と一致する場合、readyになりcandidateMoveをそのまま使う", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    // checkCandidateMovesSafetyはbaseline局面+各候補手の1:baseline, 2:候補 の順でgoMultiPvを呼ぶ。
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }]), // 候補7i8h
    ]);

    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen });
    const cachedPlan: CachedReachablePlan = { sfen, targetShapeId: computed.targetShapeId, plan: computed };

    const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen });

    expect(response.plan.candidateMoveState).toBe("ready");
    expect(response.plan.candidateMove?.status).toBe("ready");
    expect(response.plan.candidateMove?.explanations.map((e) => e.move)).toEqual(["7i8h"]);
  });

  it("cachedPlanのsfenが現在の局面と一致しない(stale)場合は無視し、pending/unavailableとして扱う", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const staleCachedPlan: CachedReachablePlan = {
      sfen: DEFAULT_INITIAL_SFEN, // 別の局面(古い解析結果)
      targetShapeId: undefined,
      plan: {
        reachableShapes: [],
        candidateMove: { status: "ready", notReadyReason: null, explanations: [] },
      },
    };

    const response = buildStateResponseWithPlan(state, staleCachedPlan, { initialSfen: sfen });

    // staleな結果がそのまま混入していないこと(pendingとして扱われる)。
    expect(response.plan.candidateMoveState).toBe("pending");
    expect(response.plan.candidateMove).toBeUndefined();
  });

  it("複数候補: 対象マスへ複数の合法手がある場合、reachableShapes/candidateMoveの両方に反映される", async () => {
    const sfen = honminoMultipleCandidatesSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine(() =>
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 0 }, pv: [] }], "6g7h"),
    );

    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen });
    expect(computed.candidateMove?.explanations.map((e) => e.move).sort()).toEqual(["6g7h", "8g7h"]);

    const response = buildStateResponseWithPlan(
      state,
      { sfen, targetShapeId: computed.targetShapeId, plan: computed },
      { initialSfen: sfen },
    );
    expect(response.plan.candidateMove?.explanations).toHaveLength(2);
  });

  it("通常対局(scenario未指定)・scenario対局のどちらでもエラーにならない", () => {
    const normalState: GameState = { ...gameStateAfter([]), scenario: undefined };
    const scenarioState: GameState = { ...gameStateAfter([]), scenario: "hayajikake" };

    expect(() => buildStateResponseWithPlan(normalState, undefined)).not.toThrow();
    expect(() => buildStateResponseWithPlan(scenarioState, undefined)).not.toThrow();
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const first = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });
    const second = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });
    expect(second).toEqual(first);
  });
});

// 目標形選択UI(docs/PHASES.md Phase2完了条件「ユーザーが2〜3個の候補から目標形を
// 選べるUI」)向けのselectedTargetShapeId対応(computeRankedPlanContext内の分岐)の検証。
// honminoOneMoveFromCompleteSfen()は、reachableShapesの上位3件が
// ["mino_honmino", "mino_takamino", "mino_ginkanmuri"](matchScore降順)になり、
// mino_honmino/mino_takaminoはどちらも次の対象マスが8h(玉)で、同じ候補手
// (7i8h)を持つ(pathPlanner.tsの独自ロジックではなく、たまたま両shapeのdataが
// この局面では同じ対象マスを指しているため)。候補手のUSI自体は同じでも、
// どちらのshapeを対象にしたかはcandidateMove.explanations[0].refers_to_shape_idと
// resolvedTargetShapeIdで判別できる。
describe("目標形選択(selectedTargetShapeId)", () => {
  it("未選択時は従来通りranked[0](mino_honmino)が採用される", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.plan.resolvedTargetShapeId).toBe("mino_honmino");
    expect(response.plan.reachableShapes.map((s) => s.shapeId)).toEqual([
      "mino_honmino",
      "mino_takamino",
      "mino_ginkanmuri",
    ]);
  });

  it("有効なselectedTargetShapeId(reachableShapes内)を指定すると、そのshapeが採用される", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }]), // 候補7i8h
    ]);

    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_takamino");

    expect(computed.targetShapeId).toBe("mino_takamino");
    expect(computed.candidateMove?.status).toBe("ready");
    expect(computed.candidateMove?.explanations[0]?.refers_to_shape_id).toBe("mino_takamino");
    // reachableShapesの一覧(⑥の表示)自体はランキングそのままで、選択によって
    // 並び替えたり除外したりしない(⑦⑧の対象だけが変わる)。
    expect(computed.reachableShapes.map((s) => s.shapeId)).toEqual([
      "mino_honmino",
      "mino_takamino",
      "mino_ginkanmuri",
    ]);

    const response = buildStateResponseWithPlan(
      state,
      { sfen, targetShapeId: computed.targetShapeId, plan: computed },
      { initialSfen: sfen },
      "mino_takamino",
    );
    expect(response.plan.resolvedTargetShapeId).toBe("mino_takamino");
    expect(response.plan.candidateMoveState).toBe("ready");
  });

  it("reachableShapesに存在しないselectedTargetShapeIdはranked[0]へフォールバックする", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(
      state,
      undefined,
      { initialSfen: sfen },
      "shape_that_does_not_exist",
    );

    expect(response.plan.resolvedTargetShapeId).toBe("mino_honmino");
    expect(response.plan.candidateMoveState).toBe("pending");
  });

  it("同一SFENでtargetShapeIdだけ変更した場合、古いcachedPlanを再利用しない(stale扱い)", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }]), // 候補7i8h
    ]);

    // mino_honmino(未選択時のranked[0]相当)を対象に計算し、それをキャッシュとする。
    const computedForHonmino = await computeReachablePlan(state, engine, { initialSfen: sfen });
    const cachedPlan: CachedReachablePlan = {
      sfen,
      targetShapeId: computedForHonmino.targetShapeId,
      plan: computedForHonmino,
    };
    expect(cachedPlan.targetShapeId).toBe("mino_honmino");

    // 同じsfenのまま、選択をmino_takaminoに変更してレスポンスを組み立てる。
    // sfenは一致するが、cachedPlanはmino_honmino向けの結果なので使ってはならない。
    const response = buildStateResponseWithPlan(
      state,
      cachedPlan,
      { initialSfen: sfen },
      "mino_takamino",
    );

    expect(response.plan.resolvedTargetShapeId).toBe("mino_takamino");
    // "ready"のまま古い(mino_honmino向けの)candidateMoveを返してはいけない。
    expect(response.plan.candidateMoveState).toBe("pending");
    expect(response.plan.candidateMove).toBeUndefined();
  });
});

describe("computeReachablePlan / safeComputeReachablePlan", () => {
  it("MultiPV参考評価が取得できる場合、candidateMove.statusがreadyになる", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 25 }, pv: [] }]), // 候補7i8h
    ]);

    const result = await computeReachablePlan(state, engine, { initialSfen: sfen });

    expect(result.candidateMove?.status).toBe("ready");
    expect(result.candidateMove?.explanations).toHaveLength(1);
    expect(result.reachableShapes.length).toBeGreaterThan(0);
  });

  it("MultiPV取得失敗(エンジン例外)の場合、safeComputeReachablePlanはundefinedを返し例外を外へ漏らさない", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeThrowingLowPriorityEngine();

    const result = await safeComputeReachablePlan(state, engine, { initialSfen: sfen });
    expect(result).toBeUndefined();

    // computeReachablePlan自体は(安全側ラッパーではないため)例外を伝播する。
    await expect(computeReachablePlan(state, engine, { initialSfen: sfen })).rejects.toThrow();
  });

  it("候補手との対応付け(評価データ)が不十分な場合、candidateMove.statusはnot_ready(insufficient_engine_data)になる", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    // scoreを含まないMultiPV結果(=評価データが得られなかった、という想定)。
    // baseline自体は何でもよく、候補手側(2件目)をscore無しにする。
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]),
      multiPvResult([]),
    ]);

    const result = await computeReachablePlan(state, engine, { initialSfen: sfen });

    expect(result.candidateMove?.status).toBe("not_ready");
    expect(result.candidateMove?.notReadyReason).toBe("insufficient_engine_data");
  });

  it("shapeが見つからない/候補手が空(初期局面)の場合、engineに一切問い合わせずcandidateMove: undefinedを返す", async () => {
    const state = gameStateAfter([]);
    const engine = makeMockLowPriorityEngine([]);

    const result = await computeReachablePlan(state, engine);

    expect(result.candidateMove).toBeUndefined();
    expect(engine.goMultiPv).not.toHaveBeenCalled();
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const makeEngine = () =>
      makeMockLowPriorityEngine([
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 1 }, pv: [] }]), // baseline
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 1 }, pv: [] }]), // 候補7i8h
      ]);

    const first = await computeReachablePlan(state, makeEngine(), { initialSfen: sfen });
    const second = await computeReachablePlan(state, makeEngine(), { initialSfen: sfen });
    expect(second).toEqual(first);
  });
});
