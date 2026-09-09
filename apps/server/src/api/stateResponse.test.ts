import { Board } from "shogiops/board";
import { Hand, Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Role } from "shogiops/types";
import { describe, expect, it, vi } from "vitest";
import type { CoachExplanation } from "../analysis/explanationGenerator.js";
import { getIntents } from "../analysis/intentRepository.js";
import { getShapes } from "../analysis/shapeRepository.js";
import type { BoardEventMessage } from "../analysis/boardEventExplanation.js";
import { toMovingPieceName } from "../notation/japaneseMove.js";
import type { ShapeFormationResult } from "../analysis/shapeFormationAnalyzer.js";
import type { NextConsiderationMessage } from "../analysis/nextConsiderationExplanation.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../analysis/moveHistory.js";
import { applyMove } from "../rules/applyMove.js";
import type { GameState } from "../game/gameSession.js";
import type { MultiPvGoResult } from "../engine/usiEngine.js";
import type { LowPriorityEngine } from "../engine/prioritizedEngine.js";
import {
  buildStateResponse,
  buildStateResponseWithPlan,
  computePlanChangeAfterMove,
  computePlanChangeReasonAfterMove,
  computeReachablePlan,
  computeBoardEventsAfterMove,
  computeMoveOutcomeAfterMove,
  safeComputeBoardEventsAfterMove,
  safeComputeMoveOutcomeAfterMove,
  safeComputePlanChangeAfterMove,
  safeComputePlanChangeReasonAfterMove,
  safeComputeReachablePlan,
  type CachedReachablePlan,
  filterCoachForTargetShape,
  filterLastMoveMessagesForTargetShape,
  partitionUrgentMessages,
  filterContradictoryConsiderations,
  resolveRecognizedDirection,
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

  // Phase4: current.wasLastOpponentMoveForced(gameSession.tsが確定させた事実)が
  // safeExplainPosition経由でexplanationGenerator.tsまで正しく伝播することを確認する。
  it("Phase4: wasLastOpponentMoveForced=true かつ intent全noneの場合、事実ベースの新文言が伝播する", () => {
    const state: GameState = { ...gameStateAfter([]), wasLastOpponentMoveForced: true };
    const response = buildStateResponse(state);
    const opponentIntent = findStage(response.coach!, "opponent_intent");
    const nextAim = findStage(response.coach!, "opponent_next_aim");

    expect(opponentIntent.reason).toBe("相手の今の手は、対局序盤の決まった手順によるものです。");
    expect(nextAim.reason).toBe("相手の今の手は、対局序盤の決まった手順によるものです。");
  });

  it("Phase4: wasLastOpponentMoveForced=false(未指定含む)かつintent全noneの場合、従来文言のまま伝播する", () => {
    const stateWithFalse: GameState = { ...gameStateAfter([]), wasLastOpponentMoveForced: false };
    const stateWithUndefined: GameState = gameStateAfter([]);

    for (const state of [stateWithFalse, stateWithUndefined]) {
      const opponentIntent = findStage(buildStateResponse(state).coach!, "opponent_intent");
      expect(opponentIntent.reason).toBe(
        "相手の狙いは、まだはっきりとは分かりません。特定の作戦を決めつけず、もう少し様子を見てみましょう。",
      );
    }
  });

  it("Phase4: wasLastOpponentMoveForced=trueでも、intentが一致していれば既存のintent説明を優先する", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const forcedState: GameState = { ...gameStateAfter(moveHistory), wasLastOpponentMoveForced: true };
    const notForcedState: GameState = { ...gameStateAfter(moveHistory), wasLastOpponentMoveForced: false };

    const forcedIntent = findStage(buildStateResponse(forcedState).coach!, "opponent_intent");
    const notForcedIntent = findStage(buildStateResponse(notForcedState).coach!, "opponent_intent");

    expect(forcedIntent).toEqual(notForcedIntent);
    expect(forcedIntent.refers_to_intent_id).toBe("hayajikake");
    expect(forcedIntent.reason).toContain("早仕掛けの形になっています");
  });

  it("forming状態: 途中段階のIntentを断定表現にしない", () => {
    const moveHistory = interleaveWithSenteFillers([HAYAJIKAKE_GOTE_MOVES_FULL[0]!]);
    const state = gameStateAfter(moveHistory);
    const response = buildStateResponse(state);
    const opponentIntent = findStage(response.coach!, "opponent_intent");

    expect(opponentIntent.status).toBe("forming");
    expect(opponentIntent.refers_to_intent_id).toBe("hayajikake");
    // 論点1(甲、STEP ζ-5): formingの段階では戦法名・current_aim_explanationを
    // 一切出さず、観測できている事実だけを機械的に述べる。
    expect(opponentIntent.reason).toContain("ように見えます");
    expect(opponentIntent.reason).toContain("まだ決まっていません");
    expect(opponentIntent.reason).not.toContain("早仕掛けの形になっています");
    for (const intent of getIntents()) {
      expect(opponentIntent.reason).not.toContain(intent.name);
    }

    // opponent_next_aim(甲、STEP ζ-5): formingの段階ではステージ自体をレスポンスの
    // 配列に含めない(表示しない)。
    expect(response.coach!.find((e) => e.stage === "opponent_next_aim")).toBeUndefined();
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

// honminoMultipleCandidatesSfen()と同じ駒配置に、相手(gote)が指せる無害な歩(1c)を
// 追加したもの。Phase3の既知課題(兄弟候補の誤検知)の統合テスト専用
// (相手がこの計画と無関係な手(1c1d)を指すシナリオを構成するために必要)。
function honminoMultipleCandidatesWithOpponentPawnSfen(): string {
  return customSfen([
    { square: "8h", color: "sente", role: "king" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "6g", color: "sente", role: "silver" },
    { square: "8g", color: "sente", role: "silver" },
    { square: "1c", color: "gote", role: "pawn" },
  ]);
}

// honminoMultipleCandidatesSfen()と同じ駒配置に、ユーザーが指せる無害な歩(1g)と、
// 6gの銀を直接捕獲できる相手(gote)の桂馬(7e)を追加したもの
// (planChangeCaptureFixtureSfenと同じ考え方だが、兄弟候補(8g7h)が生き残る
// ことを確認するために複数候補の局面を使う)。
function honminoMultipleCandidatesWithCaptureFixtureSfen(): string {
  return customSfen([
    { square: "8h", color: "sente", role: "king" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "6g", color: "sente", role: "silver" },
    { square: "8g", color: "sente", role: "silver" },
    { square: "1g", color: "sente", role: "pawn" },
    { square: "7e", color: "gote", role: "knight" },
  ]);
}

// Phase3 Unit1(計画崩れの検知)専用の局面。honminoOneMoveFromCompleteSfen()と同じ
// 「王が7iにあり8hへ1手(7i8h)で本美濃が完成する」局面に、
// - ユーザーが提案手(7i8h)以外に指せる、無関係な歩(1g)
// - 相手(gote)が打てる飛車1枚(持ち駒)
// を追加したもの。相手が飛車を8筋へ打つと、王が8hへ動けば飛車の利きに入るため
// (王手放置)、候補手7i8hが機械的に非合法になる(=相手の手による崩れの検証に使う)。
function planChangeFixtureSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "7i", role: "king" },
    { square: "7h", role: "silver" },
    { square: "6i", role: "gold" },
    { square: "5h", role: "gold" },
    { square: "1g", role: "pawn" },
  ];
  for (const { square, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color: "sente", role });
  }
  const hands = Hands.from(Hand.empty(), Hand.from([["rook", 1]]));
  const pos = Shogi.from({ board, hands, turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

// Phase3 Unit2(計画崩れの理由分類)専用の局面。玉8h・金6i・金5hは既に揃い、
// 対象マスは7h(銀)。銀は6gの1枚のみ(候補手は"6g7h"の1件)、
// ユーザーが無関係な歩(1g)を指せるようにし、相手(gote)には桂馬を7eに配置する
// (7eの桂馬は6g・8gのどちらにも1手で到達でき、6gの銀を直接取れる)。
function planChangeCaptureFixtureSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }> = [
    { square: "8h", color: "sente", role: "king" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "6g", color: "sente", role: "silver" },
    { square: "1g", color: "sente", role: "pawn" },
    { square: "7e", color: "gote", role: "knight" },
  ];
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("buildStateResponseWithPlan", () => {
  // 【Phase6 Unit1で挙動が変わったテスト】
  // 以前はpathPlanner.ts(単一目標マス・1手先読み)を使っていたため、初期局面では
  // typical_build_order先頭の8h(玉)へ1手で届かず、candidateMoveState: "unavailable"に
  // なっていた(docs/PHASES.md Phase5「実対局確認で判明した設計上の限界」)。
  // routePlanner.ts(複数の未達成マス・複数手の経路)に切り替えたことで、
  // 初期局面でも経路と候補手が計算できるようになった。
  it("初期局面でも経路が計算され、候補手あり(pending)になる(Phase6 Unit1)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    expect(response.plan.reachableShapes.length).toBeGreaterThan(0);
    expect(response.plan.candidateMoveState).toBe("pending");
    // ⑧の説明はエンジン参考評価を伴うため、この時点(バックグラウンド解析前)ではまだ無い。
    expect(response.plan.candidateMove).toBeUndefined();
    // Phase1の既存coach(shapeDetector/shapeFormationAnalyzer/intentDetector/explanationGenerator)は
    // buildStateResponseと完全に同じ内容のまま壊れていないこと。
    expect(response.coach).toEqual(buildStateResponse(state).coach);
  });

  it("選択中の形について、必要なマス・現在の進み具合・経路がレスポンスに含まれる(Phase6 Unit1)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    // 「選択した形 → 必要なマス → 今どこまで出来ているか」をUIが辿れること。
    expect(response.plan.targetShapeProgress?.shapeId).toBe(response.plan.resolvedTargetShapeId);
    expect(response.plan.targetShapeProgress?.matchedSquareLabels).toEqual(["６九"]);
    expect(response.plan.targetShapeProgress?.missingSquareLabels).toEqual(["８八", "７八", "５八"]);

    // 「未達成マス → 現在の局面からの経路 → 今指せる最初の一手があるか」を辿れること。
    const kingRoute = response.plan.routes.find((r) => r.targetSquare === "8h");
    expect(kingRoute?.targetPiece).toBe("玉");
    expect(kingRoute?.targetSquareLabel).toBe("８八");
    expect(kingRoute?.routeLabel).toBe("５九→６八→７八→８八");
    expect(kingRoute?.remainingSteps).toBe(3);
    expect(kingRoute?.hasPlayableFirstMove).toBe(true);
    expect(kingRoute?.blockingSquareLabel).toBe("８八");
  });

  it("候補手を計算できない局面(相手の手番)ではcandidateMoveState: unavailableになる", () => {
    // routePlanner.tsは相手の手番では候補を返さない(not_self_turn)。
    const state = gameStateAfter(["7g7f"]);
    const response = buildStateResponseWithPlan(state, undefined);

    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.candidateMove).toBeUndefined();
    expect(response.plan.routes).toEqual([]);
  });

  it("候補手はあるが、まだバックグラウンド解析が完了していない(cachedPlanなし)場合はpendingになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

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

    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
    const cachedPlan: CachedReachablePlan = { sfen, targetShapeId: computed.targetShapeId, plan: computed };

    const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen }, "mino_honmino");

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
        candidateMove: { status: "ready", notReadyReason: null, explanations: [], sharedNotes: [] },
      },
    };

    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const response = buildStateResponseWithPlan(state, staleCachedPlan, { initialSfen: sfen }, "mino_honmino");

    // staleな結果がそのまま混入していないこと(pendingとして扱われる)。
    expect(response.plan.candidateMoveState).toBe("pending");
    expect(response.plan.candidateMove).toBeUndefined();
  });

  it("複数候補: 対象マスへ複数の合法手がある場合、reachableShapes/candidateMoveの両方に反映される", async () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfen = honminoMultipleCandidatesSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine(() =>
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 0 }, pv: [] }], "6g7h"),
    );

    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
    expect(computed.candidateMove?.explanations.map((e) => e.move).sort()).toEqual(["6g7h", "8g7h"]);

    const response = buildStateResponseWithPlan(
      state,
      { sfen, targetShapeId: computed.targetShapeId, plan: computed },
      { initialSfen: sfen },
      "mino_honmino",
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

  // STEP ζ-5: review_statusによる名前の露出制御。data/shapes/mino_ginkanmuri.jsonは
  // review_status: "draft"(人間承認済みの実データ)。
  describe("review_statusによる名前の露出制御(STEP ζ-5)", () => {
    it("draftの形(銀冠)を選択すると、pendingReviewNoteが注記付きで返る(経路3・4・6・7の材料)", () => {
      const state = gameStateAfter([]);
      const response = buildStateResponseWithPlan(state, undefined, {}, "mino_ginkanmuri");

      expect(response.plan.resolvedTargetShapeId).toBe("mino_ginkanmuri");
      // 経路3・7(組み上がり見出し・候補手見出し、main.tsが名前と組み合わせて表示する)。
      expect(response.plan.targetShapeProgress?.pendingReviewNote).toBe("内容を確認中の形");
      // 経路6(候補手セクションの注意書き。選択中の形から独立に決まる)。
      expect(response.plan.pendingReviewNote).toBe(
        "この形の説明は内容を確認中のため、参考程度に見てください。",
      );
      // 経路4(選択ボタン。reachableShapesの各要素)。
      const ginkanmuriButton = response.plan.reachableShapes.find((s) => s.shapeId === "mino_ginkanmuri");
      expect(ginkanmuriButton?.pendingReviewNote).toBe("内容を確認中の形");
    });

    it("human_reviewedの形(本美濃)を選択すると、pendingReviewNoteはすべてnull", () => {
      const state = gameStateAfter([]);
      const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

      expect(response.plan.resolvedTargetShapeId).toBe("mino_honmino");
      expect(response.plan.targetShapeProgress?.pendingReviewNote).toBeNull();
      expect(response.plan.pendingReviewNote).toBeNull();
      const honminoButton = response.plan.reachableShapes.find((s) => s.shapeId === "mino_honmino");
      expect(honminoButton?.pendingReviewNote).toBeNull();
    });

    it("reviewStatusの生値はレスポンスに出ない(reachableShapes・targetShapeProgressのどちらにも無い)", () => {
      const state = gameStateAfter([]);
      const response = buildStateResponseWithPlan(state, undefined, {}, "mino_ginkanmuri");

      expect(response.plan.reachableShapes.length).toBeGreaterThan(0);
      for (const shape of response.plan.reachableShapes) {
        expect(shape).not.toHaveProperty("reviewStatus");
      }
      expect(response.plan.targetShapeProgress).not.toBeNull();
      expect(response.plan.targetShapeProgress).not.toHaveProperty("reviewStatus");
    });
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
  // Phase 7 Unit 0: 目標形は対局開始時に自動選択されない。ユーザーが選ぶまでは
  // resolvedTargetShapeId / targetShapeProgress / routes / candidateMoveのいずれも
  // 出ないが、reachableShapes(目指せる形の候補、選ぶ手段)は引き続き提供する。
  it("未選択時は目標形が決まらない(resolvedTargetShapeIdはnull、reachableShapesは引き続き出る)", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.reachableShapes.map((s) => s.shapeId)).toEqual([
      "mino_honmino",
      "mino_takamino",
      "mino_ginkanmuri",
    ]);
    expect(response.plan.targetShapeProgress).toBeNull();
    expect(response.plan.routes).toEqual([]);
    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.candidateMove).toBeUndefined();
  });

  it("有効なselectedTargetShapeId(reachableShapes内)を指定すると、そのshapeが採用される", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    // mino_takaminoは本美濃より必要なマスが多く、routePlanner.tsが複数の目標マスに
    // ついて候補手を返すため、エンジンへの問い合わせ回数は局面によって変わる。
    // ここで検証したいのは「どのshapeが対象に採用されたか」なので、回数に依存しない
    // 関数形式のモックを使う。
    const engine = makeMockLowPriorityEngine(() =>
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }]),
    );

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

  // Phase 7 Unit 0: 無効なselectedTargetShapeIdもranked[0]へはフォールバックしない
  // (未選択時と同じく「目標形が決まらない」扱いになる)。
  it("reachableShapesに存在しないselectedTargetShapeIdは目標形が決まらない扱いになる(ranked[0]へはフォールバックしない)", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const response = buildStateResponseWithPlan(
      state,
      undefined,
      { initialSfen: sfen },
      "shape_that_does_not_exist",
    );

    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.candidateMoveState).toBe("unavailable");
  });

  it("同一SFENでtargetShapeIdだけ変更した場合、古いcachedPlanを再利用しない(stale扱い)", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [] }]), // 候補7i8h
    ]);

    // mino_honminoを明示的に選択して計算し、それをキャッシュとする
    // (Phase 7 Unit 0: 未選択時のranked[0]フォールバックは廃止したため、
    // ここでは明示的にmino_honminoを選択する)。
    const computedForHonmino = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
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

    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const result = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");

    expect(result.candidateMove?.status).toBe("ready");
    expect(result.candidateMove?.explanations).toHaveLength(1);
    expect(result.reachableShapes.length).toBeGreaterThan(0);
  });

  it("MultiPV取得失敗(エンジン例外)の場合、safeComputeReachablePlanはundefinedを返し例外を外へ漏らさない", async () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const engine = makeThrowingLowPriorityEngine();

    const result = await safeComputeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
    expect(result).toBeUndefined();

    // computeReachablePlan自体は(安全側ラッパーではないため)例外を伝播する。
    await expect(
      computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino"),
    ).rejects.toThrow();
  });

  it("候補手との対応付け(評価データ)が不十分な場合、candidateMove.statusはnot_ready(insufficient_engine_data)になる", async () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    // scoreを含まないMultiPV結果(=評価データが得られなかった、という想定)。
    // baseline自体は何でもよく、候補手側(2件目)をscore無しにする。
    const engine = makeMockLowPriorityEngine([
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [] }]),
      multiPvResult([]),
    ]);

    const result = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");

    expect(result.candidateMove?.status).toBe("not_ready");
    expect(result.candidateMove?.notReadyReason).toBe("insufficient_engine_data");
  });

  it("候補手が空の場合(相手の手番)、engineに一切問い合わせずcandidateMove: undefinedを返す", async () => {
    // Phase6 Unit1以降、初期局面では候補手が計算できるようになったため、
    // 「候補手が空」の例としてroutePlanner.tsが候補を返さない相手の手番を使う。
    const state = gameStateAfter(["7g7f"]);
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

// Phase3 Unit1(計画崩れの検知のみ、人間承認済み)。判定条件そのもの(候補A)の
// 網羅的なテストはplanChangeDetector.test.tsで行う。ここではGameState/実際の
// pathPlanner.ts結果を経由した統合(computePlanChangeAfterMove)の配線を検証する。
describe("computePlanChangeAfterMove / safeComputePlanChangeAfterMove", () => {
  it("ユーザーが提案手をそのまま指した場合、除外後の残存候補が無くplanChanged: falseになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = honminoOneMoveFromCompleteSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "7i8h");
    const stateAfter: GameState = { sfen: sfenAfterUserMove, moveHistory: ["7i8h"], forcedPliesUsed: 0 };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "7i8h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);
  });

  // 【既知課題の修正確認(人間承認済み)】
  // 複数候補(6g7h/8g7h、いずれも移動先マス7hを共有する兄弟候補)のうち、
  // ユーザーが1つ(6g7h)をそのまま指し、相手はこの計画と完全に無関係な手
  // (1c1d)を指す。修正前はここでplanChanged: trueに誤検知していた
  // (兄弟候補8g7hが、ユーザー自身の着手で7hが埋まったせいで非合法になるため)。
  // 手作りのlegalMoves配列ではなく、実際のapplyMove/getLegalMoves(pathPlanner経由)を
  // 使って検証する。
  it("複数候補(兄弟候補)のうち1つをそのまま指し、相手が無関係な手を指した場合はplanChanged: falseになる(既知課題の修正確認)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = honminoMultipleCandidatesWithOpponentPawnSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "6g7h"); // 複数候補のうち1つをそのまま指す
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "1c1d"); // 相手はこの計画と無関係な手
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["6g7h", "1c1d"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "6g7h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);

    // 【今回追加(既知課題修正後の理由分類との整合性確認)】
    // planChanged: falseの場合、理由分類(computePlanChangeReasonAfterMove)も
    // 呼ばれるべきではなく、nullになる(server.tsの配線と同じ前提)。
    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "6g7h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBeNull();
  });

  // 兄弟候補の一方だけが相手に実際に捕獲され、もう一方は生きている場合。
  // 「候補の一部が使えなくなった」だけでは計画変更と判定しない、という既存方針を維持する。
  it("兄弟候補の一方だけが相手に捕獲されても、もう一方が合法ならplanChanged: falseのまま", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = honminoMultipleCandidatesWithCaptureFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f"); // 提案手以外の無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "7e6g"); // 桂馬が6gの銀を取る(8gの銀は無傷)
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "7e6g"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBeNull();
  });

  it("ユーザーが提案手以外を指し、相手の手が残存候補を機械的に非合法にした場合はplanChanged: trueになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f"); // 提案手(7i8h)とは無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*8a"); // 相手が飛車を8筋へ打つ
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "R*8a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);
  });

  it("ユーザーが提案手以外を指したが、相手の手が計画に無関係な場合はplanChanged: falseのままになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*1a"); // 8筋に利きが無い場所へ打つ
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "R*1a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);
  });

  it("stateBeforeMove時点で候補手が無い(unavailable相当)場合はplanChanged: falseになる", () => {
    const stateBefore = gameStateAfter([]); // 初期局面: 玉が8hへ1手で届かないためcandidateMovesは空
    const stateAfter = gameStateAfter([]);

    const planChanged = computePlanChangeAfterMove(stateBefore, stateAfter, "7g7f");
    expect(planChanged).toBe(false);
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);
    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*8a");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "R*8a"],
      forcedPliesUsed: 0,
    };

    const first = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    const second = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(second).toBe(first);
  });

  it("計算中に例外が起きてもsafeComputePlanChangeAfterMoveはfalseを返し、例外を外へ漏らさない", () => {
    // buildStateResponseの既存テスト(不正な局面)と同じ、わざと矛盾したGameState。
    const inconsistentState: GameState = {
      sfen: DEFAULT_INITIAL_SFEN,
      moveHistory: ["7g7f"], // このsfenはこの履歴の結果ではない
      forcedPliesUsed: 0,
    };

    const result = safeComputePlanChangeAfterMove(inconsistentState, inconsistentState, "7g7f");
    expect(result).toBe(false);

    // computePlanChangeAfterMove自体は(安全側ラッパーではないため)例外を伝播する。
    expect(() => computePlanChangeAfterMove(inconsistentState, inconsistentState, "7g7f")).toThrow();
  });
});

describe("buildStateResponseWithPlan: planChanged", () => {
  it("planChangedを省略した場合はfalseになる(Phase2までの既存呼び出しとの後方互換)", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined);
    expect(response.plan.planChanged).toBe(false);
  });

  it("planChanged=trueを渡すとレスポンスにそのまま反映される", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, undefined, true);
    expect(response.plan.planChanged).toBe(true);
  });

  it("planChangeReasonを省略した場合はnullになる(Unit1までの既存呼び出しとの後方互換)", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined);
    expect(response.plan.planChangeReason).toBeNull();
  });

  it("planChangeReason=\"candidate_piece_captured\"を渡すとレスポンスにそのまま反映される", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, undefined, true, "candidate_piece_captured");
    expect(response.plan.planChangeReason).toBe("candidate_piece_captured");
  });
});

// Phase3 Unit2(崩れた理由の分類のみ、人間承認済み)。分類そのもの(candidate_piece_
// captured/unknown)の網羅的なテストはplanChangeReason.test.tsで行う。ここでは
// GameState/実際のpathPlanner.ts結果を経由した統合(computePlanChangeReasonAfterMove)
// の配線を検証する。
describe("computePlanChangeReasonAfterMove / safeComputePlanChangeReasonAfterMove", () => {
  it("相手の手で残存候補の駒が捕獲された場合、planChangeReason: candidate_piece_capturedになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeCaptureFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f"); // 提案手(6g7h)とは無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "7e6g"); // 桂馬が銀を取る
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "7e6g"],
      forcedPliesUsed: 0,
    };

    // 前提確認: このシナリオでは実際にplanChangedがtrueになる(computePlanChangeAfterMove、
    // Unit1のロジックは今回変更していないため、既存の挙動としてそのまま成立する)。
    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBe("candidate_piece_captured");
  });

  it("王手放置(候補手の玉移動が相手の利きに入る)で崩れた場合、planChangeReason: candidate_move_illegal_due_to_checkになる", () => {
    // Unit1の実機再現テストと同じフィクスチャ(相手が飛車を8筋へ打ち、王の移動先が
    // 利きに入るため候補手が非合法になる。駒は取られていない)。
    // 今回のUnit2追加分類により、unknownではなくcandidate_move_illegal_due_to_checkに
    // 正しく分類されることを確認する(pos.squareAttackers、既存shogiops APIのみ使用)。
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*8a");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "R*8a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBe("candidate_move_illegal_due_to_check");
  });

  it("planChanged: falseの場合、planChangeReasonは常にnullになる", () => {
    // ユーザーが提案手をそのまま指した場合(除外後の残存候補が無くplanChanged: false)。
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = honminoOneMoveFromCompleteSfen();
    const stateBefore = customGameState(sfenBefore);
    const sfenAfterUserMove = applyMove(sfenBefore, "7i8h");
    const stateAfter: GameState = { sfen: sfenAfterUserMove, moveHistory: ["7i8h"], forcedPliesUsed: 0 };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "7i8h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "7i8h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBeNull();
  });

  it("stateBeforeMove時点で候補手が無い場合、planChangeReasonはnullになる", () => {
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter([]);
    const reason = computePlanChangeReasonAfterMove(stateBefore, stateAfter, "7g7f");
    expect(reason).toBeNull();
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", () => {
    const sfenBefore = planChangeCaptureFixtureSfen();
    const stateBefore = customGameState(sfenBefore);
    const sfenAfterUserMove = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "7e6g");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["1g1f", "7e6g"],
      forcedPliesUsed: 0,
    };

    const first = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    const second = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(second).toBe(first);
  });

  it("計算中に例外が起きてもsafeComputePlanChangeReasonAfterMoveはnullを返し、例外を外へ漏らさない", () => {
    const inconsistentState: GameState = {
      sfen: DEFAULT_INITIAL_SFEN,
      moveHistory: ["7g7f"], // このsfenはこの履歴の結果ではない
      forcedPliesUsed: 0,
    };

    const result = safeComputePlanChangeReasonAfterMove(inconsistentState, inconsistentState, "7g7f");
    expect(result).toBeNull();

    // computePlanChangeReasonAfterMove自体は(安全側ラッパーではないため)例外を伝播する。
    expect(() => computePlanChangeReasonAfterMove(inconsistentState, inconsistentState, "7g7f")).toThrow();
  });
});

// Phase6 Unit2(直前の一手で何が変わったか)。事実の抽出そのものの網羅的なテストは
// moveOutcomeDetector.test.ts / moveOutcomeExplanation.test.ts で行う。
// ここではGameStateを経由した配線(スナップショットの作り方・ラベル・null条件)を検証する。
describe("computeMoveOutcomeAfterMove / safeComputeMoveOutcomeAfterMove", () => {
  it("候補手を指して目標マスが完成した場合、その事実が抽出される", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const stateBefore = gameStateAfter([]);
    // 初期局面で7i7h(銀を7hへ)は候補手であり、本美濃の7hが完成する。
    const stateAfter = gameStateAfter(["7i7h", "1c1d"]);

    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7i7h", "1c1d", {}, "mino_honmino");

    expect(outcome?.playedMoveUsi).toBe("7i7h");
    expect(outcome?.opponentMoveUsi).toBe("1c1d");
    expect(outcome?.facts.map((f) => f.kind)).toContain("route_completed");
    expect(outcome?.facts.map((f) => f.kind)).toContain("played_candidate");
  });

  it("相手が応手しておらず手番が自分に戻っていない場合は、差分を取らずnullを返す", () => {
    // 相手の手番の局面ではroutePlanner.tsが経路を返さないため、差分を取ると
    // 「経路が全て失われた」という誤った事実になる。比較自体を行わない。
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter(["7i7h"]);

    expect(
      computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7i7h", null, {}, "mino_honmino"),
    ).toBeNull();
  });

  it("planChangeReasonをそのまま原因として引き継ぐ(自前で理由を判定しない)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeCaptureFixtureSfen();
    const stateBefore = customGameState(sfenBefore);
    const sfenAfterUser = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponent = applyMove(sfenAfterUser, "7e6g");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponent,
      moveHistory: ["1g1f", "7e6g"],
      forcedPliesUsed: 0,
    };

    const outcome = computeMoveOutcomeAfterMove(
      stateBefore,
      stateAfter,
      "1g1f",
      "7e6g",
      { initialSfen: sfenBefore },
      "mino_honmino",
      "candidate_piece_captured",
    );

    const lost = outcome?.facts.find((f) => f.kind === "route_lost");
    expect(lost?.cause).toBe("candidate_piece_captured");
  });

  it("safe版は、局面と履歴が矛盾していても例外を投げずnullを返す", () => {
    const inconsistentState: GameState = { sfen: DEFAULT_INITIAL_SFEN, moveHistory: ["7g7f"], forcedPliesUsed: 0 };

    expect(safeComputeMoveOutcomeAfterMove(inconsistentState, inconsistentState, "7g7f", null)).toBeNull();
  });
});

// Unit 3(情報構造の整理)。既知事項 U0-1 の解消と、[3]「なぜそれが重要か」に出す弱点。
describe("Unit 3: 目標形が未選択のときに、存在しない目標形を指す説明を返さない", () => {
  const coach = (stage: CoachExplanation["stage"], status: CoachExplanation["status"]): CoachExplanation =>
    ({
      id: `runtime_${stage}_${status}`,
      stage,
      purpose: "テスト用",
      move: null,
      reason: "テスト用",
      refers_to_shape_id: null,
      refers_to_intent_id: null,
      confidence_level: "low",
      glossary_terms: [],
      template_id: `${stage}_${status}`,
      status,
    }) as CoachExplanation;

  it("未選択のとき、current_shapeのformingだけを落とす", () => {
    const input = [
      coach("current_shape", "forming"),
      coach("current_shape", "completed"),
      coach("current_shape", "none"),
      coach("opponent_intent", "forming"),
    ];

    const filtered = filterCoachForTargetShape(input, false);

    expect(filtered?.map((c) => `${c.stage}:${c.status}`)).toEqual([
      "current_shape:completed",
      "current_shape:none",
      "opponent_intent:forming",
    ]);
  });

  it("選択済みのときは何も落とさない", () => {
    const input = [coach("current_shape", "forming")];

    expect(filterCoachForTargetShape(input, true)).toEqual(input);
  });

  it("coachがundefinedならundefinedのまま返す", () => {
    expect(filterCoachForTargetShape(undefined, false)).toBeUndefined();
  });

  it("未選択のとき、no_notable_changeだけを落とし盤面の出来事は残す", () => {
    const messages = [
      { kind: "captured_by_opponent" as const, text: "取られました。" },
      { kind: "no_notable_change" as const, text: "特に大きな変化はありませんでした。" },
    ];

    expect(filterLastMoveMessagesForTargetShape(messages, false)).toEqual([messages[0]]);
    expect(filterLastMoveMessagesForTargetShape(messages, true)).toEqual(messages);
  });
});

describe("Unit 3: partitionUrgentMessages([0]「今すぐ対処が必要なこと」)", () => {
  const checkReceived = {
    kind: "check_received",
    text: "相手の手で、あなたの玉に王手がかかっています。",
  } satisfies BoardEventMessage;
  const captured = {
    kind: "captured_by_opponent",
    text: "あなたの角が取られました。",
  } satisfies BoardEventMessage;
  const inCheck = {
    kind: "in_check",
    text: "今、あなたの玉に王手がかかっています。",
  } satisfies NextConsiderationMessage;
  const routeNote = {
    kind: "route_first_move_playable",
    text: "７七桂は、道のりの一手目です。",
  } satisfies NextConsiderationMessage;

  it("in_checkがあるときは、それだけを[0]に出し、check_receivedは落とす", () => {
    const result = partitionUrgentMessages([checkReceived, captured], [inCheck, routeNote]);

    expect(result.urgent).toEqual([inCheck]);
    expect(result.lastMoveMessages).toEqual([captured]);
    expect(result.nextConsiderations).toEqual([routeNote]);
  });

  it("in_checkが無いとき(目標形未選択等)は、check_receivedを[0]に回す", () => {
    const result = partitionUrgentMessages([checkReceived, captured], []);

    expect(result.urgent).toEqual([checkReceived]);
    expect(result.lastMoveMessages).toEqual([captured]);
  });

  it("王手が無ければ[0]は空で、他は素通しする", () => {
    const result = partitionUrgentMessages([captured], [routeNote]);

    expect(result.urgent).toEqual([]);
    expect(result.lastMoveMessages).toEqual([captured]);
    expect(result.nextConsiderations).toEqual([routeNote]);
  });
});

// 人間が承認した規則: forming が複数あるときは parent_shape_id の鎖をたどり、
// 他のすべての祖先になっている形(= 最も基本となる形)を対象にする。
// ranked[0]・matchScore・新しい閾値は一切使わない。
describe("Unit 3: resolveRecognizedDirection(parent_shape_id の鎖で1件へ絞る)", () => {
  type Shape = Pick<ShapeFormationResult, "shapeId" | "status" | "parentShapeId">;
  const shape = (
    shapeId: string,
    status: "none" | "forming" | "completed",
    parentShapeId: string | null,
  ): Shape => ({ shapeId, status, parentShapeId });

  // data/shapes/*.json の実際の鎖: 本美濃(ルート) → 高美濃 → 銀冠
  const honmino = (status: "none" | "forming" | "completed") => shape("mino_honmino", status, null);
  const takamino = (status: "none" | "forming" | "completed") =>
    shape("mino_takamino", status, "mino_honmino");
  const ginkanmuri = (status: "none" | "forming" | "completed") =>
    shape("mino_ginkanmuri", status, "mino_takamino");

  it("forming 3件(本美濃+高美濃+銀冠)なら、最も祖先側の本美濃を対象にする", () => {
    const result = resolveRecognizedDirection([honmino("forming"), takamino("forming"), ginkanmuri("forming")]);

    expect(result).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 3 });
  });

  it("forming 2件(高美濃+銀冠)なら高美濃を対象にする", () => {
    const result = resolveRecognizedDirection([honmino("completed"), takamino("forming"), ginkanmuri("forming")]);

    expect(result).toEqual({ shapeId: "mino_takamino", reason: "single", formingCount: 2 });
  });

  it("forming 2件(本美濃+銀冠、間の高美濃はforming でない)でも祖先をたどって本美濃を対象にする", () => {
    const result = resolveRecognizedDirection([honmino("forming"), takamino("none"), ginkanmuri("forming")]);

    expect(result).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 2 });
  });

  it("forming 1件ならその形を対象にする", () => {
    const result = resolveRecognizedDirection([honmino("forming"), takamino("none"), ginkanmuri("none")]);

    expect(result).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 1 });
  });

  it("forming 0件なら対象を決めない(候補手を出さない)", () => {
    const result = resolveRecognizedDirection([honmino("none"), takamino("completed"), ginkanmuri("none")]);

    expect(result).toEqual({ shapeId: undefined, reason: "none", formingCount: 0 });
  });

  it("鎖でつながらない兄弟同士のときは対象を決めない(順位付けを発明しない)", () => {
    const result = resolveRecognizedDirection([
      shape("family_a_root", "forming", null),
      shape("family_b_root", "forming", null),
    ]);

    expect(result).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });
  });

  it("parent_shape_id が循環していても止まり、対象を決めずに返す", () => {
    const result = resolveRecognizedDirection([
      shape("a", "forming", "b"),
      shape("b", "forming", "a"),
    ]);

    expect(result.reason).toBe("ambiguous");
  });

  it("completedは方向の判断に使わない(ranked[0]フォールバックを復活させない)", () => {
    const result = resolveRecognizedDirection([honmino("completed"), takamino("completed")]);

    expect(result.shapeId).toBeUndefined();
    expect(result.reason).toBe("none");
  });
});

describe("Unit 3: 候補手のラベルに駒名を付ける", () => {
  it("初期局面の7g7fは「歩：７七→７六」になる", () => {
    const response = buildStateResponseWithPlan(gameStateAfter([]), undefined, {});

    // 候補手が出ない局面でもラベル生成そのものは検証できるよう、変換関数の結果を直接見る。
    expect(toMovingPieceName(DEFAULT_INITIAL_SFEN, "7g7f")).toBe("歩");
    expect(response.plan.candidateMoveLabels).toBeDefined();
  });

  it("移動元に駒が無い場合はnullを返し、呼び出し側がマス目だけの表記に落とせる", () => {
    expect(toMovingPieceName(DEFAULT_INITIAL_SFEN, "5e5d")).toBeNull();
  });

  it("USIとして解釈できない文字列はnullを返す", () => {
    expect(toMovingPieceName(DEFAULT_INITIAL_SFEN, "zzzz")).toBeNull();
  });
});

describe("Unit 3: filterContradictoryConsiderations", () => {
  const noPlayable = {
    kind: "no_playable_route_first_move",
    text: "今の局面では、選んだ形へ向かう道のりの一手目を、どれも指すことができません。",
  } satisfies NextConsiderationMessage;
  const completed = { kind: "shape_completed", text: "形ができています。" } satisfies NextConsiderationMessage;

  it("候補手があるときは、矛盾して読める一文を落とす", () => {
    expect(filterContradictoryConsiderations([noPlayable, completed], true)).toEqual([completed]);
  });

  it("候補手が無いときはそのまま残す", () => {
    expect(filterContradictoryConsiderations([noPlayable, completed], false)).toEqual([noPlayable, completed]);
  });
});

describe("Unit 3: shapeWeakness([3]「なぜそれが重要か」)", () => {
  // 先手が 玉8八・銀7八・金6九・金5八 を組み上げ、本美濃囲いがcompletedになる手順。
  // 後手の手は形の判定に関与しない歩突きで埋めている。
  const HONMINO_COMPLETED_MOVES = [
    "7g7f", "1c1d",
    "8h7g", "2c2d",
    "5i6h", "3c3d",
    "6h7h", "4c4d",
    "7h8h", "5c5d",
    "7i7h", "6c6d",
    "4i5h",
  ];

  it("形が完成していない初期局面では返さない", () => {
    const response = buildStateResponseWithPlan(gameStateAfter([]), undefined, {});

    expect(response.plan.shapeWeakness).toBeNull();
  });

  it("形が完成したら、data/shapes/*.json の weak_against をそのまま返す", () => {
    const response = buildStateResponseWithPlan(gameStateAfter(HONMINO_COMPLETED_MOVES), undefined, {});

    expect(response.plan.shapeWeakness?.shapeId).toBe("mino_honmino");
    expect(response.plan.shapeWeakness?.text).toContain("横からの攻め");
    // 新しい文言を作らないこと(data側の本文と完全一致する)。
    expect(response.plan.shapeWeakness?.text).toBe(getShapes().find((s) => s.id === "mino_honmino")?.weak_against);
  });
});

describe("buildStateResponseWithPlan: lastMoveOutcome", () => {
  it("MoveOutcomeを渡すと、日本語棋譜表記のラベルとメッセージがレスポンスに入る", () => {
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter(["7i7h", "1c1d"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7i7h", "1c1d");

    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, undefined, false, null, outcome);

    expect(response.plan.lastMoveOutcome?.playedMoveLabel).toBe("７八銀");
    expect(response.plan.lastMoveOutcome?.opponentMoveLabel).toBe("１四歩");
    // Unit 3(情報構造の整理・既知事項 U0-1): 目標形が未選択(selectedTargetShapeId:
    // undefined)のときは「目標にしている形について特に大きな変化はありませんでした」を
    // 返さない。存在しない目標形を指す文言を出さないための仕様である。
    expect(response.plan.lastMoveOutcome!.messages.some((m) => m.kind === "no_notable_change")).toBe(false);
    // 説明文に評価語が混ざらないこと(moveOutcomeExplanation.tsの方針)。
    for (const message of response.plan.lastMoveOutcome!.messages) {
      for (const forbidden of ["最善", "おすすめ", "安全", "悪手", "形勢"]) {
        expect(message.text).not.toContain(forbidden);
      }
    }
  });

  it("MoveOutcomeを渡さない場合(新規対局直後・目標形変更直後)はnullになる", () => {
    const state = gameStateAfter([]);

    const response = buildStateResponseWithPlan(state, undefined);

    expect(response.plan.lastMoveOutcome).toBeNull();
  });
});

// Phase6 Unit3(盤面で実際に起きたこと: 捕獲・王手・成り)。事実抽出そのものの
// 網羅的なテストはboardEventDetector.test.ts / boardEventExplanation.test.tsで行う。
// ここではGameStateを経由した配線と、Unit2の説明との共存を検証する。
describe("computeBoardEventsAfterMove / buildStateResponseWithPlan: 盤面イベント", () => {
  it("相手が自分の駒を取った場合、その事実が抽出される", () => {
    // 後手の歩を1筋で下ろし、1gに残っている自分の歩を取らせる(同時に成る)。
    const history = ["9g9f", "1c1d", "8g8f", "1d1e", "7g7f", "1e1f"];
    const stateBefore = gameStateAfter(history);
    const stateAfter = gameStateAfter([...history, "5g5f", "1f1g+"]);

    const events = computeBoardEventsAfterMove(stateBefore, "5g5f", "1f1g+");

    expect(events).toEqual([
      { kind: "captured_by_opponent", piece: "歩", square: "1g" },
      { kind: "promoted_by_opponent", piece: "歩", square: "1g" },
    ]);
    expect(stateAfter.moveHistory).toHaveLength(8);
  });

  it("何も起きていない手ではイベントを返さない", () => {
    expect(computeBoardEventsAfterMove(gameStateAfter([]), "7g7f", "1c1d")).toEqual([]);
  });

  it("safe版は、非合法な指し手を渡されても例外を投げず空配列を返す", () => {
    expect(safeComputeBoardEventsAfterMove(gameStateAfter([]), "9a9b", null)).toEqual([]);
  });

  it("盤面イベントのメッセージが、形・経路の説明より前に並ぶ(Unit2と共存する)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const history = ["9g9f", "1c1d", "8g8f", "1d1e", "7g7f", "1e1f"];
    const stateBefore = gameStateAfter(history);
    const stateAfter = gameStateAfter([...history, "7i7h", "1f1g+"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7i7h", "1f1g+", {}, "mino_honmino");
    const events = computeBoardEventsAfterMove(stateBefore, "7i7h", "1f1g+");

    const response = buildStateResponseWithPlan(
      stateAfter,
      undefined,
      {},
      "mino_honmino",
      false,
      null,
      outcome,
      events,
    );

    const kinds = response.plan.lastMoveOutcome!.messages.map((m) => m.kind);
    // 先頭2件が盤面の出来事、そのあとに形・経路の説明(Unit2)が続く。
    expect(kinds.slice(0, 2)).toEqual(["captured_by_opponent", "promoted_by_opponent"]);
    expect(kinds).toContain("route_completed");
  });

  it("盤面イベントを渡さない場合、Unit2の説明だけが返る(既存動作を変えない)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter(["7i7h", "1c1d"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7i7h", "1c1d", {}, "mino_honmino");

    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, "mino_honmino", false, null, outcome);

    expect(response.plan.lastMoveOutcome!.messages.map((m) => m.kind)).toEqual([
      "played_candidate",
      "route_completed",
    ]);
  });
});

// 以下、Phase6 Unit4(今の局面で分かっていること)の配線テスト。
// 事実の抽出・文言生成そのものは nextConsiderationDetector.test.ts /
// nextConsiderationExplanation.test.ts が担当し、ここで確認するのは配線のみ。
describe("buildStateResponseWithPlan: nextConsiderations(Phase6 Unit4)", () => {
  it("現在の局面について分かっていることが、文言としてレスポンスに含まれる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    // 初期局面では、経路の一手目が複数指せる(=対応の文言 + 並び順の注記)。
    const kinds = response.plan.nextConsiderations.map((m) => m.kind);
    expect(kinds.filter((k) => k === "route_first_move_playable").length).toBeGreaterThanOrEqual(2);
    expect(kinds[kinds.length - 1]).toBe("ordering_note");
    expect(response.plan.nextConsiderations[0]?.text).toContain("道のりの一手目です。");
  });

  it("目標形が決まっていない場合は空配列", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, { shapes: [] });

    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.nextConsiderations).toEqual([]);
  });

  it("王手を受けている局面では、ルール上の制約を先頭に述べる", () => {
    // 先手(ユーザー側)の玉に王手がかかっている局面を直接組み立てる。
    const sfen = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    if (response.plan.resolvedTargetShapeId !== null) {
      expect(response.plan.nextConsiderations[0]?.kind).toBe("in_check");
      expect(response.plan.nextConsiderations[0]?.text).toContain("王手を解消する手しか指せません");
    }
  });

  it("同じ局面に対して常に同じ結果を返す(決定的)", () => {
    const state = gameStateAfter([]);

    expect(buildStateResponseWithPlan(state, undefined).plan.nextConsiderations).toEqual(
      buildStateResponseWithPlan(state, undefined).plan.nextConsiderations,
    );
  });

  it("さまざまな局面で例外を投げず、常に配列を返す(対局本体を止めない)", () => {
    const states = [
      gameStateAfter([]),
      gameStateAfter(["7g7f", "3c3d"]),
      gameStateAfter(["7i7h", "3c3d", "5i6h", "8c8d"]),
    ];

    for (const state of states) {
      expect(() => buildStateResponseWithPlan(state, undefined)).not.toThrow();
      expect(Array.isArray(buildStateResponseWithPlan(state, undefined).plan.nextConsiderations)).toBe(true);
    }
  });

  it("既存のUnit1〜3のフィールドを壊さない", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    expect(response.plan.routes.length).toBeGreaterThan(0);
    expect(response.plan.targetShapeProgress).not.toBeNull();
    expect(response.plan.lastMoveOutcome).toBeNull();
    expect(response.coach).toEqual(buildStateResponse(state).coach);
  });
});

// ζ-4a: 内部状態(GameState)と公開状態(StateResponseBody)の境界を、許可リスト方式
// (toPublicGameState)で確立したことの検証。docs/ARCHITECTURE.md 6.「公開境界」参照。
describe("公開境界(内部状態とAPIレスポンスの分離、ζ-4a)", () => {
  // buildStateResponseが返すキーが、公開してよいと定めた6件ちょうどであること
  // (許可リスト方式であることの直接の確認)。forcedPliesUsedはSTEP ζ-4c-1(C-6、
  // 人間承認済み)により非公開へ移した(下記「forcedPliesUsedが公開されない」参照)。
  const PUBLIC_KEYS = ["coach", "legalMoves", "moveHistory", "moveHistoryJapanese", "sfen", "status"];

  it("buildStateResponseのキーが公開許可リストの6件と完全一致する", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponse(state);

    expect(Object.keys(response).sort()).toEqual([...PUBLIC_KEYS].sort());
  });

  it("buildStateResponseWithPlanのキーが公開許可リスト6件+planの7件と完全一致する", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined);

    expect(Object.keys(response).sort()).toEqual([...PUBLIC_KEYS, "plan"].sort());
  });

  // STEP ζ-4c-1(C-6): forcedPliesUsedはGameStateに存在するが、レスポンスには一切現れない。
  it("forcedPliesUsedはGameStateに存在するが、レスポンスには一切現れない", () => {
    const state = gameStateAfter([]);
    expect(state.forcedPliesUsed).toBe(0);

    const response = buildStateResponse(state);
    const responseWithPlan = buildStateResponseWithPlan(state, undefined);

    expect(response).not.toHaveProperty("forcedPliesUsed");
    expect(responseWithPlan).not.toHaveProperty("forcedPliesUsed");
  });

  it("GameStateにscenario/wasLastOpponentMoveForcedを設定しても、レスポンスはそれらを持たない", () => {
    // scenario(相手AI制御用シナリオ識別子)・wasLastOpponentMoveForced(強制進行の
    // 確定事実)は、いずれも相手AIの制御に関わる内部情報であり、ユーザーへ非開示とする
    // (docs/PHASES.md Phase 7 Unit 1「選んだものはユーザーに開示しない」)。
    const state: GameState = {
      ...gameStateAfter([]),
      scenario: "hayajikake",
      wasLastOpponentMoveForced: true,
    };

    const response = buildStateResponse(state);
    const responseWithPlan = buildStateResponseWithPlan(state, undefined);

    expect(response).not.toHaveProperty("scenario");
    expect(response).not.toHaveProperty("wasLastOpponentMoveForced");
    expect(responseWithPlan).not.toHaveProperty("scenario");
    expect(responseWithPlan).not.toHaveProperty("wasLastOpponentMoveForced");
  });

  // STEP ζ-4c-1: GameState.opponentControl(相手AI制御の内部状態。seed・選択済み
  // variantId・movesUsed)は、GameState経由でもAPI経由でも一切公開しない。
  it("GameStateにopponentControlを設定しても、レスポンスにopponentControl/seed/selectedVariantId/movesUsedが一切現れない", () => {
    const state: GameState = {
      ...gameStateAfter([]),
      opponentControl: { seed: 123456, selectedVariantId: "ibisha/boh_gin", movesUsed: 2 },
    };

    const response = buildStateResponse(state);
    const responseWithPlan = buildStateResponseWithPlan(state, undefined);

    expect(response).not.toHaveProperty("opponentControl");
    expect(responseWithPlan).not.toHaveProperty("opponentControl");

    const responseJson = JSON.stringify(response);
    const responseWithPlanJson = JSON.stringify(responseWithPlan);
    for (const secret of ["opponentControl", "selectedVariantId", "movesUsed", "123456", "ibisha/boh_gin"]) {
      expect(responseJson).not.toContain(secret);
      expect(responseWithPlanJson).not.toContain(secret);
    }
  });

  // 【本STEPの中心】将来GameStateに未知のフィールド(Unit 1が足しうる制御情報を
  // 模したもの)を追加しても、許可リスト方式(toPublicGameState)により既定では
  // 公開されないことを直接確認する。除外リスト方式(...currentをそのまま展開する
  // 実装)であれば、この未知フィールドはそのままレスポンスへ漏れてしまう。
  it("GameStateに未知のフィールドを追加しても、レスポンスのキー構成は変わらない(将来のフィールド追加が漏れないことの担保)", () => {
    const stateWithUnknownField = {
      ...gameStateAfter([]),
      futureOpponentControlSecret: "この値は絶対に公開されてはならない",
    } as GameState;

    const response = buildStateResponse(stateWithUnknownField);
    const responseWithPlan = buildStateResponseWithPlan(stateWithUnknownField, undefined);

    expect(Object.keys(response).sort()).toEqual([...PUBLIC_KEYS].sort());
    expect(Object.keys(responseWithPlan).sort()).toEqual([...PUBLIC_KEYS, "plan"].sort());
    expect(response).not.toHaveProperty("futureOpponentControlSecret");
  });

  // 回帰確認: 非開示にするのは「制御側」(相手AIが実際に選んだシナリオ等)の情報であり、
  // 「認識側」(指し手の観測から推定した戦法名・狙いの説明、coach)は
  // docs/PHASES.md Phase 1 の完了条件どおり引き続き公開する(両者を混同しない)。
  it("scenario/wasLastOpponentMoveForcedを設定した状態でも、認識側のcoach出力は引き続き含まれる", () => {
    const moveHistory = interleaveWithSenteFillers(HAYAJIKAKE_GOTE_MOVES_FULL);
    const state: GameState = {
      ...gameStateAfter(moveHistory),
      scenario: "hayajikake",
      wasLastOpponentMoveForced: false,
    };

    const response = buildStateResponse(state);

    expect(response.coach).toBeDefined();
    const opponentIntent = findStage(response.coach!, "opponent_intent");
    expect(opponentIntent.reason).toContain("早仕掛けの形になっています");
  });
});
