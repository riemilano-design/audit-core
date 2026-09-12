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
import type { PieceThreatMessage } from "../analysis/pieceThreatExplanation.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../analysis/moveHistory.js";
import type { MoveOutcomeFact } from "../analysis/moveOutcomeDetector.js";
import { explainMoveOutcome, NO_NOTABLE_CHANGE_TEXT } from "../analysis/moveOutcomeExplanation.js";
import { applyMove } from "../rules/applyMove.js";
import { isInCheck } from "../rules/gameStatus.js";
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
  filterMoveOutcomeFactsForDisplay,
  filterNextConsiderationsForDisplay,
  partitionUrgentMessages,
  filterContradictoryConsiderations,
  resolveRecognizedDirection,
  GAME_END_SELF_CHECKMATE_TEXT,
  GAME_END_OPPONENT_CHECKMATE_TEXT,
  GAME_END_OTHER_TEXT,
  type MoveOutcome,
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
    { square: "2h", role: "king" },
    { square: "3h", role: "silver" },
    { square: "4i", role: "gold" },
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

    // opponent_next_aim(STEP 4-4、人間承認R-1、2026-09-10): formingの段階でも
    // ステージは落とさず、既存の汎用文(戦法名を含まない)を出す。ζ-5が禁止したのは
    // 戦法名を含むnext_aim_explanationの表示であり、この汎用文は禁止範囲に含まれない。
    const opponentNextAim = findStage(response.coach!, "opponent_next_aim");
    expect(opponentNextAim.status).toBe("forming");
    expect(opponentNextAim.reason).toBe(
      "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
    );
    for (const intent of getIntents()) {
      expect(opponentNextAim.reason).not.toContain(intent.name);
    }
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
    // 本美濃(king2h)は初期配置の飛車(2h)を動かしてから組む必要があり、実対局の
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

function multiPvResult(lines: MultiPvGoResult["lines"], bestmove = "3i2h"): MultiPvGoResult {
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

// 本美濃囲い(mino_honmino)のうち、玉だけが3iにあり(2hへ1手で届く)、
// 銀3h・金4i・金5hは既に揃っている局面。missingSquares=["2h"]、
// typical_build_order上の対象マスは"2h"(玉)になり、3i2hという合法な候補手が1件だけ存在する。
function honminoOneMoveFromCompleteSfen(): string {
  return customSfen([
    { square: "3i", color: "sente", role: "king" },
    { square: "3h", color: "sente", role: "silver" },
    { square: "4i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
  ]);
}

// 玉2h・金4i・金5hは既に揃い、対象マスは3h(銀)。4g・2gの2枚の銀からそれぞれ
// 1手(斜め後退)で3hへ到達できる(複数候補の検証用。将棋の実戦性は問わない、
// 合法手抽出ロジックの検証が目的)。4iの金も物理的には3hへ動けるが、対象マスの
// 駒種(銀)と一致しないためpathPlanner.tsの駒種フィルタで候補から除外される。
function honminoMultipleCandidatesSfen(): string {
  return customSfen([
    { square: "2h", color: "sente", role: "king" },
    { square: "4i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "4g", color: "sente", role: "silver" },
    { square: "2g", color: "sente", role: "silver" },
  ]);
}

function customGameState(sfen: string): GameState {
  return { sfen, moveHistory: [], forcedPliesUsed: 0 };
}

/**
 * STEP 4-5: customSfenと同じ方式で、手番(turn)だけ指定できる版。
 * 「相手を詰ませた」局面(手番=gote)を組み立てるために必要(customSfen自体は
 * 既存テストの前提を変えないため、turnを常にsenteに固定したまま変更しない)。
 */
function customSfenWithTurn(
  pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }>,
  turn: "sente" | "gote",
): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn, moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

// honminoMultipleCandidatesSfen()と同じ駒配置に、相手(gote)が指せる無害な歩(9c)を
// 追加したもの。Phase3の既知課題(兄弟候補の誤検知)の統合テスト専用
// (相手がこの計画と無関係な手(9c9d)を指すシナリオを構成するために必要)。
function honminoMultipleCandidatesWithOpponentPawnSfen(): string {
  return customSfen([
    { square: "2h", color: "sente", role: "king" },
    { square: "4i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "4g", color: "sente", role: "silver" },
    { square: "2g", color: "sente", role: "silver" },
    { square: "9c", color: "gote", role: "pawn" },
  ]);
}

// honminoMultipleCandidatesSfen()と同じ駒配置に、ユーザーが指せる無害な歩(9g)と、
// 4gの銀を直接捕獲できる相手(gote)の桂馬(3e)を追加したもの
// (planChangeCaptureFixtureSfenと同じ考え方だが、兄弟候補(2g3h)が生き残る
// ことを確認するために複数候補の局面を使う)。
function honminoMultipleCandidatesWithCaptureFixtureSfen(): string {
  return customSfen([
    { square: "2h", color: "sente", role: "king" },
    { square: "4i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "4g", color: "sente", role: "silver" },
    { square: "2g", color: "sente", role: "silver" },
    { square: "9g", color: "sente", role: "pawn" },
    { square: "3e", color: "gote", role: "knight" },
  ]);
}

// Phase3 Unit1(計画崩れの検知)専用の局面。honminoOneMoveFromCompleteSfen()と同じ
// 「王が3iにあり2hへ1手(3i2h)で本美濃が完成する」局面に、
// - ユーザーが提案手(3i2h)以外に指せる、無関係な歩(9g)
// - 相手(gote)が打てる飛車1枚(持ち駒)
// を追加したもの。相手が飛車を2筋へ打つと、王が2hへ動けば飛車の利きに入るため
// (王手放置)、候補手3i2hが機械的に非合法になる(=相手の手による崩れの検証に使う)。
function planChangeFixtureSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "3i", role: "king" },
    { square: "3h", role: "silver" },
    { square: "4i", role: "gold" },
    { square: "5h", role: "gold" },
    { square: "9g", role: "pawn" },
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

// Phase3 Unit2(計画崩れの理由分類)専用の局面。玉2h・金4i・金5hは既に揃い、
// 対象マスは3h(銀)。銀は4gの1枚のみ(候補手は"4g3h"の1件)、
// ユーザーが無関係な歩(9g)を指せるようにし、相手(gote)には桂馬を3eに配置する
// (3eの桂馬は4g・2gのどちらにも1手で到達でき、4gの銀を直接取れる)。
function planChangeCaptureFixtureSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; color: "sente" | "gote"; role: Role }> = [
    { square: "2h", color: "sente", role: "king" },
    { square: "4i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "4g", color: "sente", role: "silver" },
    { square: "9g", color: "sente", role: "pawn" },
    { square: "3e", color: "gote", role: "knight" },
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
    expect(response.plan.targetShapeProgress?.matchedSquareLabels).toEqual(["４九"]);
    expect(response.plan.targetShapeProgress?.missingSquareLabels).toEqual(["２八", "３八", "５八"]);
    // STEP 5-4(S-2): USI形式のマス目が、日本語表記のラベル配列と同じ順で入ること。
    expect(response.plan.targetShapeProgress?.matchedSquares).toEqual(["4i"]);
    expect(response.plan.targetShapeProgress?.missingSquares).toEqual(["2h", "3h", "5h"]);

    // 「未達成マス → 現在の局面からの経路 → 今指せる最初の一手があるか」を辿れること。
    const kingRoute = response.plan.routes.find((r) => r.targetSquare === "2h");
    expect(kingRoute?.targetPiece).toBe("玉");
    expect(kingRoute?.targetSquareLabel).toBe("２八");
    expect(kingRoute?.routeLabel).toBe("５九→４八→３八→２八");
    expect(kingRoute?.remainingSteps).toBe(3);
    expect(kingRoute?.hasPlayableFirstMove).toBe(true);
    expect(kingRoute?.blockingSquareLabel).toBe("２八");

    // Phase 7 Unit 3(詰まりの可視化): 「何が塞いでいるか」「その駒に指せる手があるか」。
    // 駒名は現在の盤(SFEN)の2hを読んだ結果(初期局面の2hは先手の飛車)であり、
    // 形の定義(required_pieces)の駒種ではない。
    expect(kingRoute?.blockingPieceName).toBe("飛");
    // 初期局面の2hの飛車は、h段の空きマスへ動けるため合法手がある
    // (「合法手が1つも無い場合にfalseになる」ことは routePlanner.test.ts 3-2 で検証する)。
    expect(kingRoute?.blockingSquareHasLegalMove).toBe(true);

    // 塞いでいるマスが無い経路では、どちらもnullになる(推測で値を埋めない)。
    const silverRoute = response.plan.routes.find((r) => r.targetSquare === "3h");
    expect(silverRoute?.blockingSquareLabel).toBeNull();
    expect(silverRoute?.blockingPieceName).toBeNull();
    expect(silverRoute?.blockingSquareHasLegalMove).toBeNull();
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [], lowerbound: false, upperbound: false }]), // 候補7i8h
    ]);

    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
    const cachedPlan: CachedReachablePlan = { sfen, targetShapeId: computed.targetShapeId, plan: computed };

    const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen }, "mino_honmino");

    expect(response.plan.candidateMoveState).toBe("ready");
    expect(response.plan.candidateMove?.status).toBe("ready");
    expect(response.plan.candidateMove?.explanations.map((e) => e.move)).toEqual(["3i2h"]);
  });

  it("cachedPlanにfocusTextがある場合、候補手がunavailable(未選択)でもresponse.plan.focusTextに反映される(STEP 5-F, H-9)", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const cachedPlan: CachedReachablePlan = {
      sfen,
      targetShapeId: undefined,
      plan: {
        reachableShapes: [],
        candidateMove: undefined,
        focusText: "このまま何もしないと、あなたの２八の飛が取られる可能性があります。",
      },
    };

    // 目標形を選択しないため候補手はunavailableになるが、③(focusText)は
    // candidateMoveの有無とは独立に反映されること(H-9の核心)。
    const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen });

    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.focusText).toBe("このまま何もしないと、あなたの２八の飛が取られる可能性があります。");
  });

  it("cachedPlanが無い場合・sfenが一致しない(stale)場合、response.plan.focusTextはnullになる", () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);

    const withoutCache = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });
    expect(withoutCache.plan.focusText).toBeNull();

    const staleCachedPlan: CachedReachablePlan = {
      sfen: DEFAULT_INITIAL_SFEN,
      targetShapeId: undefined,
      plan: { reachableShapes: [], candidateMove: undefined, focusText: "古い局面の文言" },
    };
    const withStale = buildStateResponseWithPlan(state, staleCachedPlan, { initialSfen: sfen });
    expect(withStale.plan.focusText).toBeNull();
  });

  // STEP 5-F(A-3、人間承認済み。H-15): focusTextのnullは「まだ計算していない」と
  // 「計算した結果、言うことが無い」の2つを兼ねていた。focusTextStateはこれを分ける。
  // 人間の指示により、cachedPlanの3通り(無し / 古いsfen / 一致)を数えて確かめる。
  describe("focusTextState(STEP 5-F, A-3)", () => {
    it("cachedPlanが無いときは\"pending\"(まだ計算していない)", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const response = buildStateResponseWithPlan(customGameState(sfen), undefined, {
        initialSfen: sfen,
      });
      expect(response.plan.focusTextState).toBe("pending");
    });

    it("cachedPlanのsfenが古いときも\"pending\"(前の局面の解析は答えになっていない)", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const staleCachedPlan: CachedReachablePlan = {
        sfen: DEFAULT_INITIAL_SFEN,
        targetShapeId: undefined,
        plan: { reachableShapes: [], candidateMove: undefined, focusText: "古い局面の文言" },
      };
      const response = buildStateResponseWithPlan(customGameState(sfen), staleCachedPlan, {
        initialSfen: sfen,
      });
      expect(response.plan.focusTextState).toBe("pending");
      expect(response.plan.focusText).toBeNull();
    });

    it("cachedPlanのsfenが一致すれば\"ready\"", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const cachedPlan: CachedReachablePlan = {
        sfen,
        targetShapeId: undefined,
        plan: {
          reachableShapes: [],
          candidateMove: undefined,
          focusText: "このまま何もしないと、あなたの２八の飛が取られる可能性があります。",
        },
      };
      const response = buildStateResponseWithPlan(customGameState(sfen), cachedPlan, {
        initialSfen: sfen,
      });
      expect(response.plan.focusTextState).toBe("ready");
    });

    // ここが新しい欄の存在理由そのもの。解析は終わっているが、言うことが無い
    // (王手中・終局・詰み・帯1件と同じマスの重複)。画面はこのとき「計算中」の文を
    // 出してはいけない ―― 確かめていないのに確かめていると言うことになるため。
    it("sfenが一致していればfocusTextがnullでも\"ready\"(計算した結果、言うことが無い)", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const cachedPlan: CachedReachablePlan = {
        sfen,
        targetShapeId: undefined,
        plan: { reachableShapes: [], candidateMove: undefined, focusText: null },
      };
      const response = buildStateResponseWithPlan(customGameState(sfen), cachedPlan, {
        initialSfen: sfen,
      });
      expect(response.plan.focusTextState).toBe("ready");
      expect(response.plan.focusText).toBeNull();
    });

    it("focusTextとfocusTextStateは同じ判定から決まる(readyなのに文だけ落ちる、が起きない)", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const text = "このまま何もしないと、あなたの２八の飛が取られる可能性があります。";
      const cachedPlan: CachedReachablePlan = {
        sfen,
        targetShapeId: undefined,
        plan: { reachableShapes: [], candidateMove: undefined, focusText: text },
      };
      const response = buildStateResponseWithPlan(customGameState(sfen), cachedPlan, {
        initialSfen: sfen,
      });
      expect(response.plan.focusTextState).toBe("ready");
      expect(response.plan.focusText).toBe(text);
    });
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }], "4g3h"),
    );

    const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
    expect(computed.candidateMove?.explanations.map((e) => e.move).sort()).toEqual(["2g3h", "4g3h"]);

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

  // STEP 5-1(A-1〜A-3、人間承認済み。LP-1): 候補手が安全確認(candidateMoveReferenceFilter.ts)で
  // 全件除外されたとき、道のり([4])の指示形と矢印(candidateMoveLabels)を出さず、
  // 除外の事実をnextConsiderations先頭に加える。
  describe("STEP 5-1: 候補手が全件除外されたとき(candidatesExcluded)", () => {
    function excludedCachedPlan(sfen: string): CachedReachablePlan {
      return {
        sfen,
        targetShapeId: "mino_honmino",
        plan: {
          reachableShapes: [],
          candidateMove: {
            status: "not_ready",
            notReadyReason: "excluded_by_reference_evaluation",
            explanations: [],
            sharedNotes: [],
          },
        },
      };
    }

    it("除外時: routes/candidateMoveLabelsが空になり、nextConsiderations先頭に除外の事実が入り、targetShapeProgressは残る", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const state = customGameState(sfen);

      const response = buildStateResponseWithPlan(
        state,
        excludedCachedPlan(sfen),
        { initialSfen: sfen },
        "mino_honmino",
      );

      expect(response.plan.candidateMoveState).toBe("ready");
      expect(response.plan.candidateMove?.status).toBe("not_ready");
      expect(response.plan.routes).toEqual([]);
      expect(response.plan.candidateMoveLabels).toEqual({});
      expect(response.plan.targetShapeProgress).not.toBeNull();
      expect(response.plan.nextConsiderations[0]).toEqual({
        kind: "candidate_moves_excluded",
        text: "候補手は、指した後の局面を確かめた結果、今は表示していません。",
      });
    });

    it("pending(cachedPlanなし)では従来どおりroutesが残り、除外の事実は出ない", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const state = customGameState(sfen);

      const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

      expect(response.plan.candidateMoveState).toBe("pending");
      expect(response.plan.routes.length).toBeGreaterThan(0);
      expect(response.plan.candidateMoveLabels).not.toEqual({});
      expect(response.plan.nextConsiderations.some((m) => m.kind === "candidate_moves_excluded")).toBe(false);
    });

    it("ready(除外されていない)では従来どおりroutesが残り、除外の事実は出ない", async () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const state = customGameState(sfen);
      const engine = makeMockLowPriorityEngine([
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]),
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [], lowerbound: false, upperbound: false }]),
      ]);
      const computed = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");
      const cachedPlan: CachedReachablePlan = { sfen, targetShapeId: computed.targetShapeId, plan: computed };

      const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen }, "mino_honmino");

      expect(response.plan.candidateMoveState).toBe("ready");
      expect(response.plan.candidateMove?.status).toBe("ready");
      expect(response.plan.routes.length).toBeGreaterThan(0);
      expect(response.plan.candidateMoveLabels).not.toEqual({});
      expect(response.plan.nextConsiderations.some((m) => m.kind === "candidate_moves_excluded")).toBe(false);
    });

    it("他のnotReadyReason(insufficient_engine_data)では除外扱いにならず、routesが残る", () => {
      const sfen = honminoOneMoveFromCompleteSfen();
      const state = customGameState(sfen);
      const cachedPlan: CachedReachablePlan = {
        sfen,
        targetShapeId: "mino_honmino",
        plan: {
          reachableShapes: [],
          candidateMove: {
            status: "not_ready",
            notReadyReason: "insufficient_engine_data",
            explanations: [],
            sharedNotes: [],
          },
        },
      };

      const response = buildStateResponseWithPlan(state, cachedPlan, { initialSfen: sfen }, "mino_honmino");

      expect(response.plan.candidateMoveState).toBe("ready");
      expect(response.plan.candidateMove?.notReadyReason).toBe("insufficient_engine_data");
      expect(response.plan.routes.length).toBeGreaterThan(0);
      expect(response.plan.candidateMoveLabels).not.toEqual({});
      expect(response.plan.nextConsiderations.some((m) => m.kind === "candidate_moves_excluded")).toBe(false);
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
  // 出ないが、reachableShapes は引き続き提供する(Unit 3 で選択UIは廃止したが、
  // ランキング自体は [5]「参考になる囲い」の材料として残っている)。
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [], lowerbound: false, upperbound: false }]),
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 10 }, pv: [], lowerbound: false, upperbound: false }]), // 候補7i8h
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]), // baseline
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 25 }, pv: [], lowerbound: false, upperbound: false }]), // 候補7i8h
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
      multiPvResult([{ multipv: 1, score: { type: "cp", value: 5 }, pv: [], lowerbound: false, upperbound: false }]),
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

  // STEP 5-F(A-2b)。③(相手の次の狙い)の配線テスト。
  describe("focusText(STEP 5-F, A-2b)", () => {
    it("focusEngineを渡さない場合、focusTextはundefinedになる(engineには一切問い合わせない)", async () => {
      const state = gameStateAfter(["7g7f"]);
      const engine = makeMockLowPriorityEngine([]);

      const result = await computeReachablePlan(state, engine);

      expect(result.focusText).toBeUndefined();
    });

    it("候補手が0件の局面でも、focusEngineを渡せば③(focusText)が計算される(H-9の核心)", async () => {
      // 玉(5i)・飛(2h)のみのsente、玉(5a)のみのgote。目標形を選択していないため
      // (selectedTargetShapeId省略)、候補手は計算されない(既存のunavailableと同じ経路)。
      const sfen = customSfen([
        { square: "5i", color: "sente", role: "king" },
        { square: "2h", color: "sente", role: "rook" },
        { square: "5a", color: "gote", role: "king" },
      ]);
      const state = customGameState(sfen);
      // 安全確認(candidateMoveSafetyCheck)側のengineには一切問い合わせが行かないこと。
      const engine = makeMockLowPriorityEngine([]);
      // ③専用のfocusEngine(baseline→afterPassの順で2回呼ばれる)。
      const focusEngine = makeMockLowPriorityEngine([
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 0 }, pv: [], lowerbound: false, upperbound: false }]), // baseline
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 400 }, pv: [], lowerbound: false, upperbound: false }], "8h2h"), // afterPass(dropCp=400、bestmoveの移動先2hに自分の飛がいる)
      ]);

      const result = await computeReachablePlan(state, engine, { initialSfen: sfen }, undefined, focusEngine);

      expect(result.candidateMove).toBeUndefined(); // 候補手は依然として0件のまま
      expect(engine.goMultiPv).not.toHaveBeenCalled(); // 安全確認側は呼ばれない
      expect(focusEngine.goMultiPv).toHaveBeenCalledTimes(2); // baseline + afterPassの2回
      expect(result.focusText).toBe("このまま何もしないと、あなたの２八の飛が取られる可能性があります。");
    });
  });

  it("同一入力に対して常に同じ結果を返す(決定的)", async () => {
    const sfen = honminoOneMoveFromCompleteSfen();
    const state = customGameState(sfen);
    const makeEngine = () =>
      makeMockLowPriorityEngine([
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 1 }, pv: [], lowerbound: false, upperbound: false }]), // baseline
        multiPvResult([{ multipv: 1, score: { type: "cp", value: 1 }, pv: [], lowerbound: false, upperbound: false }]), // 候補7i8h
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

    const sfenAfterUserMove = applyMove(sfenBefore, "3i2h");
    const stateAfter: GameState = { sfen: sfenAfterUserMove, moveHistory: ["3i2h"], forcedPliesUsed: 0 };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "3i2h",
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

    const sfenAfterUserMove = applyMove(sfenBefore, "4g3h"); // 複数候補のうち1つをそのまま指す
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "9c9d"); // 相手はこの計画と無関係な手
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["4g3h", "9c9d"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "4g3h",
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
      "4g3h",
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

    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f"); // 提案手以外の無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "3e4g"); // 桂馬が4gの銀を取る(2gの銀は無傷)
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "3e4g"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(reason).toBeNull();
  });

  it("ユーザーが提案手以外を指し、相手の手が残存候補を機械的に非合法にした場合はplanChanged: trueになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f"); // 提案手(7i8h)とは無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*2a"); // 相手が飛車を2筋へ打つ
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "R*2a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);
  });

  it("ユーザーが提案手以外を指したが、相手の手が計画に無関係な場合はplanChanged: falseのままになる", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeFixtureSfen();
    const stateBefore = customGameState(sfenBefore);

    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*9a"); // 2筋に利きが無い場所へ打つ
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "R*9a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
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
    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*2a");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "R*2a"],
      forcedPliesUsed: 0,
    };

    const first = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    const second = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
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

    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f"); // 提案手(6g7h)とは無関係な手
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "3e4g"); // 桂馬が銀を取る
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "3e4g"],
      forcedPliesUsed: 0,
    };

    // 前提確認: このシナリオでは実際にplanChangedがtrueになる(computePlanChangeAfterMove、
    // Unit1のロジックは今回変更していないため、既存の挙動としてそのまま成立する)。
    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
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

    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "R*2a");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "R*2a"],
      forcedPliesUsed: 0,
    };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(true);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
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
    const sfenAfterUserMove = applyMove(sfenBefore, "3i2h");
    const stateAfter: GameState = { sfen: sfenAfterUserMove, moveHistory: ["3i2h"], forcedPliesUsed: 0 };

    const planChanged = computePlanChangeAfterMove(
      stateBefore,
      stateAfter,
      "3i2h",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    expect(planChanged).toBe(false);

    const reason = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "3i2h",
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
    const sfenAfterUserMove = applyMove(sfenBefore, "9g9f");
    const sfenAfterOpponentMove = applyMove(sfenAfterUserMove, "3e4g");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponentMove,
      moveHistory: ["9g9f", "3e4g"],
      forcedPliesUsed: 0,
    };

    const first = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    const second = computePlanChangeReasonAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
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
    const stateAfter = gameStateAfter(["3i3h", "1c1d"]);

    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", "1c1d", {}, "mino_honmino");

    expect(outcome?.playedMoveUsi).toBe("3i3h");
    expect(outcome?.opponentMoveUsi).toBe("1c1d");
    expect(outcome?.facts.map((f) => f.kind)).toContain("route_completed");
    expect(outcome?.facts.map((f) => f.kind)).toContain("played_candidate");
  });

  it("相手が応手しておらず手番が自分に戻っていない場合は、差分を取らずnullを返す", () => {
    // 相手の手番の局面ではroutePlanner.tsが経路を返さないため、差分を取ると
    // 「経路が全て失われた」という誤った事実になる。比較自体を行わない。
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter(["3i3h"]);

    expect(
      computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", null, {}, "mino_honmino"),
    ).toBeNull();
  });

  it("planChangeReasonをそのまま原因として引き継ぐ(自前で理由を判定しない)", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const sfenBefore = planChangeCaptureFixtureSfen();
    const stateBefore = customGameState(sfenBefore);
    const sfenAfterUser = applyMove(sfenBefore, "9g9f");
    const sfenAfterOpponent = applyMove(sfenAfterUser, "3e4g");
    const stateAfter: GameState = {
      sfen: sfenAfterOpponent,
      moveHistory: ["9g9f", "3e4g"],
      forcedPliesUsed: 0,
    };

    const outcome = computeMoveOutcomeAfterMove(
      stateBefore,
      stateAfter,
      "9g9f",
      "3e4g",
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

  // STEP 5-1(B-1、人間承認済み。LP-2): displayedPlan引数(三値)による、
  // 「実際に表示していた候補手」との照合。
  describe("displayedPlan(実際に表示していた候補手との照合)", () => {
    function candidateReadyPlan(sfen: string, moveUsi: string): CachedReachablePlan {
      return {
        sfen,
        targetShapeId: "mino_honmino",
        plan: {
          reachableShapes: [],
          candidateMove: {
            status: "ready",
            notReadyReason: null,
            explanations: [
              {
                id: "candidate_test",
                stage: "candidate_move",
                purpose: "テスト用",
                move: moveUsi,
                reason: "テスト用",
                refers_to_shape_id: null,
                refers_to_intent_id: null,
                confidence_level: "low",
                glossary_terms: [],
                template_id: "candidate_test",
              },
            ],
            sharedNotes: [],
          },
        },
      };
    }

    it("displayedPlanを省略(undefined)した場合は、従来どおりroutePlannerの候補でplayed_candidateが出る", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);

      const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", "1c1d", {}, "mino_honmino");

      expect(outcome?.facts.map((f) => f.kind)).toContain("played_candidate");
    });

    it("displayedPlanのsfen・targetShapeIdが一致しstatus:readyで、その手を含む場合はplayed_candidateが出る", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
      const displayedPlan = candidateReadyPlan(stateBefore.sfen, "3i3h");

      const outcome = computeMoveOutcomeAfterMove(
        stateBefore,
        stateAfter,
        "3i3h",
        "1c1d",
        {},
        "mino_honmino",
        null,
        displayedPlan,
      );

      expect(outcome?.facts.map((f) => f.kind)).toContain("played_candidate");
    });

    it("displayedPlanのsfenが一致しない場合は、表示していなかった扱いになりplayed_candidateが出ない", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
      const displayedPlan = candidateReadyPlan(honminoOneMoveFromCompleteSfen(), "3i3h"); // 別の局面

      const outcome = computeMoveOutcomeAfterMove(
        stateBefore,
        stateAfter,
        "3i3h",
        "1c1d",
        {},
        "mino_honmino",
        null,
        displayedPlan,
      );

      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_candidate");
      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_non_candidate");
    });

    it("displayedPlanのtargetShapeIdが一致しない場合は、表示していなかった扱いになりplayed_candidateが出ない", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
      const displayedPlan: CachedReachablePlan = {
        ...candidateReadyPlan(stateBefore.sfen, "3i3h"),
        targetShapeId: "mino_takamino",
      };

      const outcome = computeMoveOutcomeAfterMove(
        stateBefore,
        stateAfter,
        "3i3h",
        "1c1d",
        {},
        "mino_honmino",
        null,
        displayedPlan,
      );

      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_candidate");
      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_non_candidate");
    });

    it("displayedPlan.plan.candidateMove.statusがnot_readyの場合は、表示していなかった扱いになりplayed_candidateが出ない", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
      const displayedPlan: CachedReachablePlan = {
        sfen: stateBefore.sfen,
        targetShapeId: "mino_honmino",
        plan: {
          reachableShapes: [],
          candidateMove: {
            status: "not_ready",
            notReadyReason: "excluded_by_reference_evaluation",
            explanations: [],
            sharedNotes: [],
          },
        },
      };

      const outcome = computeMoveOutcomeAfterMove(
        stateBefore,
        stateAfter,
        "3i3h",
        "1c1d",
        {},
        "mino_honmino",
        null,
        displayedPlan,
      );

      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_candidate");
      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_non_candidate");
    });

    it("displayedPlanがnull(表示していた計画が無い)の場合は、played_candidateが出ない", () => {
      const stateBefore = gameStateAfter([]);
      const stateAfter = gameStateAfter(["3i3h", "1c1d"]);

      const outcome = computeMoveOutcomeAfterMove(
        stateBefore,
        stateAfter,
        "3i3h",
        "1c1d",
        {},
        "mino_honmino",
        null,
        null,
      );

      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_candidate");
      expect(outcome?.facts.map((f) => f.kind)).not.toContain("played_non_candidate");
    });
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

  // STEP 4-3(2026-09-10人間承認 D): 第3引数pieceThreatsは、王手のあとに連結する。
  const pieceAttacked = {
    kind: "piece_attacked",
    text: "あなたの８八の角に、相手の８七の金が当たっています(次の相手の手で取られる可能性があります)。",
    square: "8h",
    attackerSquares: ["8g"],
  } satisfies PieceThreatMessage;

  it("王手と当たりの両方があるとき、王手(in_check)を先頭にして当たりをそのあとに連結する", () => {
    const result = partitionUrgentMessages([checkReceived, captured], [inCheck, routeNote], [pieceAttacked]);

    expect(result.urgent).toEqual([inCheck, pieceAttacked]);
  });

  it("王手(check_received経路)と当たりの両方があるとき、check_receivedを先頭にして当たりをそのあとに連結する", () => {
    const result = partitionUrgentMessages([checkReceived, captured], [], [pieceAttacked]);

    expect(result.urgent).toEqual([checkReceived, pieceAttacked]);
  });

  it("当たりだけがあるとき(王手なし)は、当たりだけを[0]に出す", () => {
    const result = partitionUrgentMessages([captured], [routeNote], [pieceAttacked]);

    expect(result.urgent).toEqual([pieceAttacked]);
  });

  it("第3引数を省略した場合は既存の2引数呼び出しと同じ結果になる(後方互換)", () => {
    const withoutThirdArg = partitionUrgentMessages([checkReceived, captured], [inCheck, routeNote]);
    const withEmptyThirdArg = partitionUrgentMessages([checkReceived, captured], [inCheck, routeNote], []);

    expect(withoutThirdArg).toEqual(withEmptyThirdArg);
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

// 人間が承認した規則(2026-09-10、P-1: 方向の後退を止める): everCompletedShapeIds
// (これまでに一度でもcompletedになった形の集合)が空でないときは、そのうち他の要素の
// 祖先でない形M(=最も発展した完了形)を求め、forming のうちMの子孫だけを候補にする。
// M自身へのフォールバックは行わず(none)、review_statusによる除外も行わない
// (draftの銀冠も候補に含める)。
describe("STEP 4-1: resolveRecognizedDirection(everCompletedShapeIdsで方向の後退を止める)", () => {
  type Shape = Pick<ShapeFormationResult, "shapeId" | "status" | "parentShapeId">;
  const shape = (
    shapeId: string,
    status: "none" | "forming" | "completed",
    parentShapeId: string | null,
  ): Shape => ({ shapeId, status, parentShapeId });

  const honmino = (status: "none" | "forming" | "completed") => shape("mino_honmino", status, null);
  const takamino = (status: "none" | "forming" | "completed") =>
    shape("mino_takamino", status, "mino_honmino");
  const ginkanmuri = (status: "none" | "forming" | "completed") =>
    shape("mino_ginkanmuri", status, "mino_takamino");

  it("everCompleted={本美濃}、本美濃forming+高美濃formingのときは高美濃を対象にする(P-1の核心)", () => {
    const result = resolveRecognizedDirection(
      [honmino("forming"), takamino("forming")],
      new Set(["mino_honmino"]),
    );

    expect(result).toEqual({ shapeId: "mino_takamino", reason: "single", formingCount: 2 });
  });

  it("everCompleted={本美濃, 高美濃}、銀冠(draft)formingのみのときは銀冠を対象にする", () => {
    // 入力は shapeResults(全形)である前提のため、completed に転じた本美濃・高美濃も
    // (祖先の鎖をたどるために)一緒に渡す。ranked.slice(0,3) 由来の一部だけを渡すと、
    // ancestorIdsOfが親を辿れず誤ってambiguousになる。
    const result = resolveRecognizedDirection(
      [honmino("completed"), takamino("completed"), ginkanmuri("forming")],
      new Set(["mino_honmino", "mino_takamino"]),
    );

    expect(result).toEqual({ shapeId: "mino_ginkanmuri", reason: "single", formingCount: 1 });
  });

  it("everCompleted={本美濃}、本美濃だけforming(子孫のformingが無い)のときはnone(M自身へフォールバックしない)", () => {
    const result = resolveRecognizedDirection([honmino("forming")], new Set(["mino_honmino"]));

    expect(result).toEqual({ shapeId: undefined, reason: "none", formingCount: 1 });
  });

  it("everCompleted={本美濃}、本美濃の子2件(兄弟)がformingのときはambiguous(順位付けを発明しない)", () => {
    const result = resolveRecognizedDirection(
      [
        shape("family_a_child", "forming", "mino_honmino"),
        shape("family_b_child", "forming", "mino_honmino"),
      ],
      new Set(["mino_honmino"]),
    );

    expect(result).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });
  });
});

// STEP U6-F(docs/STEP_UNIT6_PLAN_2026-09-12.md 10.7): resolveRecognizedDirection に
// 追加した rule・ranked 引数の単体テスト。既定 rule="current" は上記の既存テストで
// 一切変えていないことが確認済みのため、ここでは他の3規則(rankedHeadUnique /
// rankedHeadAlways / familyCollapse)だけを対象にする。ranked は
// rankReachableShapes の戻り値を模した最小の値({shapeId, matchScore, adjustment})を
// 手で組み立てる(実際のランキング計算はここでは呼ばない)。
describe("STEP U6-F: resolveRecognizedDirection(directionRuleの規則)", () => {
  type Shape = Pick<ShapeFormationResult, "shapeId" | "status" | "parentShapeId">;
  const shape = (
    shapeId: string,
    status: "none" | "forming" | "completed",
    parentShapeId: string | null,
  ): Shape => ({ shapeId, status, parentShapeId });

  const honmino = (status: "none" | "forming" | "completed") => shape("mino_honmino", status, null);
  const takamino = (status: "none" | "forming" | "completed") =>
    shape("mino_takamino", status, "mino_honmino");
  const ginkanmuri = (status: "none" | "forming" | "completed") =>
    shape("mino_ginkanmuri", status, "mino_takamino");

  type RankedEntry = { shapeId: string; matchScore: number; adjustment: "prioritize" | "deprioritize" | null };
  const ranked = (shapeId: string, matchScore: number, adjustment: RankedEntry["adjustment"] = null): RankedEntry => ({
    shapeId,
    matchScore,
    adjustment,
  });

  it("観点1: 候補が1件(祖先鎖)に決まる場合は、3規則とも既定(current)と同じ結果になる", () => {
    const shapes = [honmino("forming"), takamino("forming"), ginkanmuri("forming")];
    const rankedList = [ranked("mino_honmino", 0.75), ranked("mino_takamino", 0.5), ranked("mino_ginkanmuri", 0.25)];

    const current = resolveRecognizedDirection(shapes);
    expect(current).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 3 });

    for (const rule of ["rankedHeadUnique", "rankedHeadAlways", "familyCollapse"] as const) {
      const result = resolveRecognizedDirection(shapes, undefined, rule, rankedList);
      expect(result).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 3 });
    }
  });

  it("観点2: 同点(adjustment・matchScoreとも同じ2件)のとき、rankedHeadUniqueはambiguous、rankedHeadAlwaysは決まる", () => {
    const shapes = [shape("family_a_root", "forming", null), shape("family_b_root", "forming", null)];
    const rankedList = [ranked("family_a_root", 0.5), ranked("family_b_root", 0.5)];

    const uniqueResult = resolveRecognizedDirection(shapes, undefined, "rankedHeadUnique", rankedList);
    expect(uniqueResult).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });

    const alwaysResult = resolveRecognizedDirection(shapes, undefined, "rankedHeadAlways", rankedList);
    expect(alwaysResult).toEqual({ shapeId: "family_a_root", reason: "single", formingCount: 2 });
  });

  it("観点3: 系統が2つ以上のとき、familyCollapseはambiguous、rankedHead*(同点でない)は決まる", () => {
    const shapes = [shape("family_a_root", "forming", null), shape("family_b_root", "forming", null)];
    const rankedList = [ranked("family_a_root", 0.7), ranked("family_b_root", 0.3)];

    const collapseResult = resolveRecognizedDirection(shapes, undefined, "familyCollapse", rankedList);
    expect(collapseResult).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });

    const uniqueResult = resolveRecognizedDirection(shapes, undefined, "rankedHeadUnique", rankedList);
    expect(uniqueResult).toEqual({ shapeId: "family_a_root", reason: "single", formingCount: 2 });

    const alwaysResult = resolveRecognizedDirection(shapes, undefined, "rankedHeadAlways", rankedList);
    expect(alwaysResult).toEqual({ shapeId: "family_a_root", reason: "single", formingCount: 2 });
  });

  it("観点4: everCompletedShapeIdsが空のブランチでも規則が効く(観点2・3で確認済み。ここでは対照としてcurrentがambiguousのままであることを確かめる)", () => {
    const shapes = [shape("family_a_root", "forming", null), shape("family_b_root", "forming", null)];
    const current = resolveRecognizedDirection(shapes);
    expect(current).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });
  });

  it("観点4: everCompletedShapeIdsが非空のブランチでも規則が効く(STEP 4-1の兄弟ambiguousケースにrankedHeadAlwaysを適用すると決まる)", () => {
    const shapes = [
      shape("family_a_child", "forming", "mino_honmino"),
      shape("family_b_child", "forming", "mino_honmino"),
    ];
    const everCompleted = new Set(["mino_honmino"]);
    const rankedList = [ranked("family_a_child", 0.6), ranked("family_b_child", 0.4)];

    const current = resolveRecognizedDirection(shapes, everCompleted);
    expect(current).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 2 });

    const alwaysResult = resolveRecognizedDirection(shapes, everCompleted, "rankedHeadAlways", rankedList);
    expect(alwaysResult).toEqual({ shapeId: "family_a_child", reason: "single", formingCount: 2 });
  });

  it("観点5: rootMostCompleted.length !== 1(567)のambiguityは、どの規則でも変わらない", () => {
    const shapes = [
      shape("family_a_root", "completed", null),
      shape("family_b_root", "completed", null),
      shape("family_a_root_child", "forming", "family_a_root"),
    ];
    const everCompleted = new Set(["family_a_root", "family_b_root"]);
    const rankedList = [ranked("family_a_root_child", 0.9)];

    for (const rule of ["current", "rankedHeadUnique", "rankedHeadAlways", "familyCollapse"] as const) {
      const result = resolveRecognizedDirection(shapes, everCompleted, rule, rankedList);
      expect(result).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 1 });
    }
  });

  it("観点6: 候補がrankedに1件も無いとき(既定の空配列)は、非currentの3規則ともambiguousになる", () => {
    const shapes = [honmino("forming"), takamino("forming"), ginkanmuri("forming")];

    const current = resolveRecognizedDirection(shapes);
    expect(current).toEqual({ shapeId: "mino_honmino", reason: "single", formingCount: 3 });

    for (const rule of ["rankedHeadUnique", "rankedHeadAlways", "familyCollapse"] as const) {
      const result = resolveRecognizedDirection(shapes, undefined, rule);
      expect(result).toEqual({ shapeId: undefined, reason: "ambiguous", formingCount: 3 });
    }
  });
});

// STEP 4-1 の配線(computeRankedPlanContext内でbuildRecognitionTimelineの出力と
// 現在completedのidを集合として組み立てる部分)を担保する統合テスト。
// 単体テスト(直前のdescribe)は組み立て済みの集合を渡すため、配線のバグを検出できない。
describe("STEP 4-1: buildStateResponseWithPlan(P-1手順の実測。方向が本美濃へ後退しない)", () => {
  // P-1(docs/PHASES.md「ランク別実機プレイ検証の記録(2026-09-10)」)で観測された手順。
  // 先手が本美濃囲い(2h玉・3h銀・4i金・5h金)を組んだあと、5八の金を4七へ進めて
  // 高美濃囲い(2h玉・3h銀・4i金・4g金・3g桂)へ発展させようとする途中の局面を辿る。
  // 4g4fで4七の歩を退かしてから5h4gで金を進めるため、5h4g直後は本美濃の必須マス(5h)が
  // 崩れてforming に戻る。このとき対象が本美濃へ後退しないことがSTEP 4-1の検証対象。
  // 後手の手は形の判定に関与しない歩突きで、ファイルごとに1手ずつ別々に埋める
  // (合法性はreplayMoveHistoryで確認済み。香の往復のような非合法な埋め手は使わない)。
  const FULL_HISTORY = [
    "7g7f", "1c1d",
    "6g6f", "2c2d",
    "2h6h", "3c3d",
    "5i4h", "4c4d",
    "4h3h", "5c5d",
    "3h2h", "6c6d",
    "3i3h", "7c7d",
    "6i5h", "8c8d",
    "4g4f", "9c9d",
    "5h4g",
  ];

  it("6i5h直後(本美濃completed、まだ4七金なし)は高美濃を対象にする", () => {
    const state = gameStateAfter(FULL_HISTORY.slice(0, 15));
    const response = buildStateResponseWithPlan(state, undefined, {});

    expect(response.plan.resolvedTargetShapeId).toBe("mino_takamino");
  });

  it("4g4f直後(5h4gの前。本美濃はまだcompletedのまま)も高美濃を対象にする", () => {
    const state = gameStateAfter(FULL_HISTORY.slice(0, 17));
    const response = buildStateResponseWithPlan(state, undefined, {});

    expect(response.plan.resolvedTargetShapeId).toBe("mino_takamino");
  });

  it("5h4g直後(本美濃がformingへ戻る)でも高美濃を対象にし続ける(P-1: 本美濃へ後退しない)", () => {
    const state = gameStateAfter(FULL_HISTORY);
    const response = buildStateResponseWithPlan(state, undefined, {});

    expect(response.plan.resolvedTargetShapeId).toBe("mino_takamino");
  });
});

describe("STEP 4-4: buildStateResponseWithPlan(forming時もopponent_next_aimを含める、人間承認R-1)", () => {
  // 実機検証で観測された手順(docs/PHASES.md「ランク別実機プレイ検証の記録」P-1局)。
  // 14手目の歩6d(相手)で早仕掛けがforming判定になる。
  const P1_MOVE_HISTORY = [
    "7g7f", "8c8d",
    "6g6f", "4a3b",
    "2h6h", "7c7d",
    "5i4h", "3c3d",
    "4h3h", "6a6b",
    "3h2h", "7a7b",
    "3i3h", "6c6d",
  ];

  it("14手目(歩6d、早仕掛けforming)で、coachにopponent_next_aimの段がstatus forming・汎用文で含まれ、戦法名を含まない", () => {
    const state = gameStateAfter(P1_MOVE_HISTORY);
    const response = buildStateResponseWithPlan(state, undefined, {});

    const opponentNextAim = findStage(response.coach!, "opponent_next_aim");
    expect(opponentNextAim.status).toBe("forming");
    expect(opponentNextAim.reason).toBe(
      "相手の狙いがまだ定まっていないため、次に何をしてきそうかも現時点では判断できません。",
    );
    for (const intent of getIntents()) {
      expect(opponentNextAim.reason).not.toContain(intent.name);
    }
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
    text: "今の局面では、その形へ向かう道のりの一手目を、どれも指すことができません。",
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
  // 正本座標(2h玉・3h銀・4i金・5h金)の本美濃を初期局面から作る手順。
  // 2hには先手の飛車がいるため、まず飛車を6八へ振って2hを空ける(採用資料S8の手順)。
  // 玉 5i→4h→3h→2h、銀 3i→3h、金 6i→5h。4iの金は初期位置のまま必須マスを満たす。
  const HONMINO_COMPLETED_MOVES = [
    "2h6h", "1c1d",
    "5i4h", "2c2d",
    "4h3h", "3c3d",
    "3h2h", "4c4d",
    "3i3h", "5c5d",
    "6i5h",
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
    const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", "1c1d");

    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, undefined, false, null, outcome);

    expect(response.plan.lastMoveOutcome?.playedMoveLabel).toBe("３八銀");
    expect(response.plan.lastMoveOutcome?.opponentMoveLabel).toBe("１四歩");
    // Unit 3(情報構造の整理・既知事項 U0-1): 目標形が未選択(selectedTargetShapeId:
    // undefined)のときは「今の陣形に近い形について特に大きな変化はありませんでした」を
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
    const stateAfter = gameStateAfter([...history, "3i3h", "1f1g+"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", "1f1g+", {}, "mino_honmino");
    const events = computeBoardEventsAfterMove(stateBefore, "3i3h", "1f1g+");

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
    const stateAfter = gameStateAfter(["3i3h", "1c1d"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "3i3h", "1c1d", {}, "mino_honmino");

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
  // STEP 4-6(D、人間承認済み): route_first_move_playable・ordering_noteは候補手の
  // 「次の一歩・この先」と重複するため、[4]では表示側フィルタ(filterNextConsiderationsForDisplay)
  // で落とすようになった。旧期待値(件数・末尾kind・先頭text)はこの変更で成立しなくなったため、
  // 「フィルタ後は空配列になる」という新しい期待値に置き換える。
  it("現在の局面について分かっていること: route_first_move_playable/ordering_noteはD(STEP 4-6)により表示されない", () => {
    // Phase 7 Unit 0: 目標形は自動選択されない(明示的に選択してから検証する)。
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    // 初期局面では経路の一手目が複数指せる状態だが、D(STEP 4-6)によりその案内・並び順の
    // 注記は[4]に出さない(候補手側の「次の一歩・この先」に一本化)。
    expect(response.plan.nextConsiderations).toEqual([]);
  });

  it("目標形が決まっていない場合は空配列", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, { shapes: [] });

    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.nextConsiderations).toEqual([]);
  });

  // STEP 4-5(2026-09-10人間承認、計画レビューでの指摘により書き直し): この局面
  // (両玉+飛車だけ)ではresolvedTargetShapeIdが常にnullになり、if文の中身が一度も
  // 実行されないまま「合格」していた(空洞化)。加えて、旧い期待値
  // (nextConsiderations[0].kindがin_check)自体が、partitionUrgentMessagesの既存挙動
  // (in_checkはurgentMessages([0])へ移り、nextConsiderationsには残らない)と矛盾していた。
  // 形が実際に認識される新しいSFEN(本美濃囲いの銀3h・金4i・金5hが揃い、玉だけ3i)を使い、
  // 「王手の制約は[0]の先頭に出て、[4]([1]のnextConsiderations)には残らない」という
  // 正しい内容で書き直す(STEP 4-5の主題そのものであるため、下記の新describeでも
  // 同じ局面をより広く検証する)。
  it("王手を受けている局面では、ルール上の制約を[0]の先頭に述べ、nextConsiderationsには残らない", () => {
    const sfen = customSfen([
      { square: "3i", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "5h", color: "sente", role: "gold" },
      { square: "4g", color: "gote", role: "knight" },
    ]);
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

    // STEP 4-5(X-1): 王手中は出力のresolvedTargetShapeIdをnullにする([4]非表示のため)。
    // 内部では実際に認識されている(urgentMessages/coachが機能していることで確認できる)。
    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.urgentMessages[0]?.kind).toBe("in_check");
    expect(response.plan.urgentMessages[0]?.text).toContain("王手を解消する手しか指せません");
    expect(response.plan.nextConsiderations).toEqual([]);
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

// STEP 4-3(2026-09-10人間承認): [0]「今すぐ対処が必要なこと」に「駒が当たっている」
// 事実を加える。事実の抽出・文言生成そのものはrules/attackedPieces.test.ts /
// analysis/pieceThreatDetector.test.ts / analysis/pieceThreatExplanation.test.ts が担当し、
// ここで確認するのは配線(目標形の有無に依存しないこと・終局後は出さないこと)だけ。
describe("buildStateResponseWithPlan: 駒が当たっている(STEP 4-3)", () => {
  it("目標形が無い局面でも、urgentMessagesに当たりが出る(A局30手目)", () => {
    const moves =
      "7g7f 4a4b 6g6f 3c3d 2h6h 4b3c 5i4h 3c4d 4h3h 5c5d 3h2h 5d5e 3i3h 7c7d 6i5h 7a6b 4g4f 8c8d 5h4g 6b5c 3g3f 4d5d 2i3g 5c6d 6f6e 5d6e 7i7h 6e7f 7h7g 7f8g".split(
        " ",
      );
    const state = gameStateAfter(moves);

    // 目標形が無い局面であること(shapes: []で明示的に形データを与えない)。
    const response = buildStateResponseWithPlan(state, undefined, { shapes: [] });

    expect(response.plan.resolvedTargetShapeId).toBeNull();
    const attackedMessages = response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked");
    expect(attackedMessages.map((m) => m.text)).toEqual([
      "あなたの８八の角に、相手の８七の金が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの７七の銀に、相手の８七の金が当たっています(次の相手の手で取られる可能性があります)。",
    ]);
    // 歩(９七)への当たりはB-1の対象外なので出ない。
    expect(response.plan.urgentMessages.some((m) => m.text.includes("９七の歩"))).toBe(false);
  });

  it("経路の候補手が無い実戦局面(C局30手目)でも、桂への当たりが出る", () => {
    const moves =
      "7g7f 3c3d 6g6f 5c5d 2h6h 3a4b 5i4h 8b5b 4h3h 5d5e 3h2h 4c4d 3i3h 7c7d 6i5h 4d4e 7i7h 4b5c 7h6g 4a4b 3g3f 5c4d 2i3g 3d3e 3f3e 4b3c 4g4f 4e4f P*4g P*3f".split(
        " ",
      );
    const state = gameStateAfter(moves);

    const response = buildStateResponseWithPlan(state, undefined, {});

    const attackedMessages = response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked");
    expect(attackedMessages.map((m) => m.text)).toEqual([
      "あなたの３七の桂に、相手の３六の歩が当たっています(次の相手の手で取られる可能性があります)。",
    ]);
  });

  it("成駒(と金)が攻め駒の実戦局面(P-1局22手目)で、銀・桂・香の3件が並ぶ", () => {
    const moves =
      "7g7f 8c8d 6g6f 4a4b 2h6h 3c3d 5i4h 2b3c 4h3h 5c5d 3h2h 4b5c 3i3h 7c7d 6i5h 8d8e 4g4f 8e8f 5h4g 8f8g+ 3g3f 8g8h"
        .split(" ")
        .slice(0, 22);
    const state = gameStateAfter(moves);

    const response = buildStateResponseWithPlan(state, undefined, {});

    const attackedMessages = response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked");
    // STEP 5-E(H-2): 銀(7i)・香(9i)は合法手の移動先すべてに相手の駒が届くため
    // 一文が付く(7i7h・7i8h、9i9hのいずれも届く)。桂(8i)は8i7gが届かないため付かない。
    expect(attackedMessages.map((m) => m.text)).toEqual([
      "あなたの７九の銀に、相手の８八のと金が当たっています(次の相手の手で取られる可能性があります)。この駒が動けるマスは、どれも相手の駒が届いています。",
      "あなたの８九の桂に、相手の８八のと金が当たっています(次の相手の手で取られる可能性があります)。",
      "あなたの９九の香に、相手の８八のと金が当たっています(次の相手の手で取られる可能性があります)。この駒が動けるマスは、どれも相手の駒が届いています。",
    ]);
  });

  it("通常の駒組みの局面(P-1局6〜16手目)では当たりが出ない(角道に入った歩を含めない)", () => {
    const allMoves =
      "7g7f 8c8d 6g6f 4a4b 2h6h 3c3d 5i4h 2b3c 4h3h 5c5d 3h2h 4b5c 3i3h 7c7d 6i5h 8d8e".split(" ");

    for (const ply of [6, 8, 10, 12, 14, 16]) {
      const state = gameStateAfter(allMoves.slice(0, ply));
      const response = buildStateResponseWithPlan(state, undefined, {});
      expect(response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked")).toEqual([]);
    }
  });

  // 王手と当たりが同時にある局面での並び順(王手が先頭)は、partitionUrgentMessagesの
  // 単体テスト(上のdescribe「Unit 3: partitionUrgentMessages」)で確認済み。

  it("終局局面(詰み)では、当たりを出さない", () => {
    // 先手の知将棋(gote)が7cの桂に8eの銀を取られる状態にありつつ、gote自身は
    // 1iの香による王手から一切逃れられない(詰み)局面。
    const sfen = "7pk/7p1/2n6/9/1S7/9/9/9/K7L w - 1";
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };

    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.status.isEnd).toBe(true);
    expect(response.plan.urgentMessages.filter((m) => m.kind === "piece_attacked")).toEqual([]);
  });
});

// STEP 5-E(S-2、2026-09-12人間承認): escapeSquareThreatsは、legalMovesのうち
// 「指した後、移動先に相手の駒が届く」ものだけを抜き出したUSI形式の配列。
// 判定そのものはanalysis/escapeSquareThreat.test.tsが担当し、ここでは配線
// (buildStateResponseが実際の局面に対して正しい部分集合を返すこと)だけを確認する。
describe("buildStateResponse: escapeSquareThreats(STEP 5-E)", () => {
  it("A局30手目: 銀(7g)は8fへ動くと届くが、7f・6fへは届かない。角の移動先(7i)は届かない", () => {
    const moves =
      "7g7f 4a4b 6g6f 3c3d 2h6h 4b3c 5i4h 3c4d 4h3h 5c5d 3h2h 5d5e 3i3h 7c7d 6i5h 7a6b 4g4f 8c8d 5h4g 6b5c 3g3f 4d5d 2i3g 5c6d 6f6e 5d6e 7i7h 6e7f 7h7g 7f8g".split(
        " ",
      );
    const state = gameStateAfter(moves);

    const response = buildStateResponse(state);

    expect(response.legalMoves).toContain("7g8f");
    expect(response.legalMoves).toContain("7g7f");
    expect(response.legalMoves).toContain("8h7i");

    expect(response.escapeSquareThreats).toContain("7g8f");
    expect(response.escapeSquareThreats).not.toContain("7g7f");
    expect(response.escapeSquareThreats).not.toContain("8h7i");

    // escapeSquareThreatsは常にlegalMovesの部分集合である。
    for (const move of response.escapeSquareThreats) {
      expect(response.legalMoves).toContain(move);
    }
  });

  it("通常の駒組みの局面(P-1局6手目)では、少なくとも1件は届かない手が含まれる(空配列固定ではない)", () => {
    const moves = "7g7f 8c8d 6g6f 4a4b 2h6h 3c3d".split(" ");
    const state = gameStateAfter(moves);

    const response = buildStateResponse(state);

    expect(response.escapeSquareThreats.length).toBeLessThan(response.legalMoves.length);
  });

  it("終局局面(詰み)では、legalMoves・escapeSquareThreatsとも空配列", () => {
    const sfen = "7pk/7p1/2n6/9/1S7/9/9/9/K7L w - 1";
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };

    const response = buildStateResponse(state, { initialSfen: sfen });

    expect(response.legalMoves).toEqual([]);
    expect(response.escapeSquareThreats).toEqual([]);
  });
});

/**
 * 双方が捕獲する局面を作るための最小構成(5筋・3筋にそれぞれ向き合う歩を1組ずつ置く)。
 * boardEventDetector.test.ts / captureSummary.test.ts と同じ方式(両玉+指定駒)。
 */
function buildMutualCaptureSfen(): string {
  let board = Board.empty();
  const place = (square: string, color: "sente" | "gote", role: Role): void => {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  };
  place("9i", "sente", "king");
  place("1a", "gote", "king");
  place("5e", "sente", "pawn");
  place("5d", "gote", "pawn");
  place("3e", "sente", "pawn");
  place("3d", "gote", "pawn");

  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

// STEP 4-3b(2026-09-10人間承認): [1]の末尾に「駒の得喪」(N-3)の集約を1行加える。
// 集約そのもの(J・K-1・L-1・O)の網羅的なテストはanalysis/captureSummary.test.tsが担当し、
// ここで確認するのは配線(current.moveHistory全体から毎回再計算され、[1]の末尾に付くこと・
// 目標形の有無に依存しないこと)だけ。
describe("buildStateResponseWithPlan: 駒の得喪の集約(STEP 4-3b)", () => {
  it("P-1局24手目: 相手のみが複数駒種を取っている(K-1の正規化・L-1の固定順)", () => {
    const moves22 =
      "7g7f 8c8d 6g6f 4a4b 2h6h 3c3d 5i4h 2b3c 4h3h 5c5d 3h2h 4b5c 3i3h 7c7d 6i5h 8d8e 4g4f 8e8f 5h4g 8f8g+ 3g3f 8g8h"
        .split(" ");
    const stateBefore = gameStateAfter(moves22);
    const moves24 = [...moves22, "2i3g", "8h9i"];
    const stateAfter = gameStateAfter(moves24);

    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "2i3g", "8h9i");
    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, undefined, false, null, outcome);

    const captureMessages = response.plan.lastMoveOutcome!.messages.filter((m) => m.kind === "capture_summary");
    expect(captureMessages.map((m) => m.text)).toEqual([
      "ここまでに、相手があなたの角を1枚、香を1枚、歩を1枚取っています。あなたはまだ駒を取っていません。",
    ]);
  });

  it("A局32手目: 相手のみが複数駒種を取っている(香1枚・歩3枚)", () => {
    const moves30 =
      "7g7f 4a4b 6g6f 3c3d 2h6h 4b3c 5i4h 3c4d 4h3h 5c5d 3h2h 5d5e 3i3h 7c7d 6i5h 7a6b 4g4f 8c8d 5h4g 6b5c 3g3f 4d5d 2i3g 5c6d 6f6e 5d6e 7i7h 6e7f 7h7g 7f8g"
        .split(" ");
    const stateBefore = gameStateAfter(moves30);
    const moves32 = [...moves30, "9i9h", "8g9h"];
    const stateAfter = gameStateAfter(moves32);

    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "9i9h", "8g9h");
    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, undefined, false, null, outcome);

    const captureMessages = response.plan.lastMoveOutcome!.messages.filter((m) => m.kind === "capture_summary");
    expect(captureMessages.map((m) => m.text)).toEqual([
      "ここまでに、相手があなたの香を1枚、歩を3枚取っています。あなたはまだ駒を取っていません。",
    ]);
  });

  it("双方が取った局面では、双方の文言になる", () => {
    const sfen = buildMutualCaptureSfen();
    const stateBefore: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const moveHistory = ["5e5d", "3d3e"];
    const stateAfter: GameState = {
      sfen: replayMoveHistory(moveHistory, sfen).finalSfen,
      moveHistory,
      forcedPliesUsed: 0,
    };

    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "5e5d", "3d3e", { initialSfen: sfen });
    const response = buildStateResponseWithPlan(
      stateAfter,
      undefined,
      { initialSfen: sfen },
      undefined,
      false,
      null,
      outcome,
    );

    const captureMessages = response.plan.lastMoveOutcome!.messages.filter((m) => m.kind === "capture_summary");
    expect(captureMessages.map((m) => m.text)).toEqual([
      "ここまでに、あなたは相手の歩を1枚、相手はあなたの歩を1枚取っています。",
    ]);
  });

  it("0枚のときはcapture_summaryの行が無い", () => {
    const stateBefore = gameStateAfter([]);
    const stateAfter = gameStateAfter(["7g7f", "3c3d"]);
    const outcome = computeMoveOutcomeAfterMove(stateBefore, stateAfter, "7g7f", "3c3d");

    const response = buildStateResponseWithPlan(stateAfter, undefined, {}, undefined, false, null, outcome);

    expect(response.plan.lastMoveOutcome!.messages.some((m) => m.kind === "capture_summary")).toBe(false);
  });
});

// ζ-4a: 内部状態(GameState)と公開状態(StateResponseBody)の境界を、許可リスト方式
// (toPublicGameState)で確立したことの検証。docs/ARCHITECTURE.md 6.「公開境界」参照。
describe("公開境界(内部状態とAPIレスポンスの分離、ζ-4a)", () => {
  // buildStateResponseが返すキーが、公開してよいと定めた7件ちょうどであること
  // (許可リスト方式であることの直接の確認)。forcedPliesUsedはSTEP ζ-4c-1(C-6、
  // 人間承認済み)により非公開へ移した(下記「forcedPliesUsedが公開されない」参照)。
  // escapeSquareThreatsはSTEP 5-E(S-2、2026-09-12人間承認)で追加した公開フィールド。
  const PUBLIC_KEYS = [
    "coach",
    "escapeSquareThreats",
    "legalMoves",
    "moveHistory",
    "moveHistoryJapanese",
    "sfen",
    "status",
  ];

  it("buildStateResponseのキーが公開許可リストの7件と完全一致する", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponse(state);

    expect(Object.keys(response).sort()).toEqual([...PUBLIC_KEYS].sort());
  });

  it("buildStateResponseWithPlanのキーが公開許可リスト7件+planの7件と完全一致する", () => {
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

// STEP 4-5(2026-09-10人間承認済み): 終局・王手中の表示。
// 終局・詰み・王手の判定はすべてrules/gameStatus.tsの既存関数(isGameOver/getGameOutcome/
// isInCheck)に委ねる。自作の詰み判定・王手判定は一切追加しない。
// 人間指定テスト12項目のうち、web側のテスト10(gameApi.test.ts)を除く項目をここで扱う。
describe("STEP 4-5: 終局・王手中の表示", () => {
  // 人間指定テスト1: 自分(先手)が詰まされた終局。
  // 玉9a・自分の歩8a(逃げ場を塞ぐ)。王手側: 飛車9c(王手そのもの、9bは素通し)・
  // 金8b(9aの逃げ場を塞ぐ・銀7aに守られている)・銀7a(8bを守る)。
  function selfCheckmateSfen(): string {
    return customSfen([
      { square: "9a", color: "sente", role: "king" },
      { square: "8a", color: "sente", role: "pawn" },
      { square: "9c", color: "gote", role: "rook" },
      { square: "8b", color: "gote", role: "gold" },
      { square: "7a", color: "gote", role: "silver" },
    ]);
  }

  // 人間指定テスト2: 相手(後手)を詰ませた終局。selfCheckmateSfenを左右反転・先後反転しただけ
  // (同じ構成を後手側に置き、手番をgoteにする)。
  function opponentCheckmateSfen(): string {
    return customSfenWithTurn(
      [
        { square: "1a", color: "gote", role: "king" },
        { square: "2a", color: "gote", role: "pawn" },
        { square: "1c", color: "sente", role: "rook" },
        { square: "2b", color: "sente", role: "gold" },
        { square: "3a", color: "sente", role: "silver" },
      ],
      "gote",
    );
  }

  // 人間指定テスト3: 詰み以外の終局(stalemate)。
  // 玉9aの逃げ場3マス(8a・9b・8b)を後手の桂馬3枚が塞ぎ、いずれも捕獲すると
  // 別の遠隔駒(飛車5a・9e、角6d)に取り返されるため実質捕獲できない(=移動不可)。
  // 桂馬自体は隣接マスを攻撃しないため、現時点で玉に王手はかかっていない。
  function stalemateSfen(): string {
    return customSfen([
      { square: "9a", color: "sente", role: "king" },
      { square: "8a", color: "gote", role: "knight" },
      { square: "9b", color: "gote", role: "knight" },
      { square: "8b", color: "gote", role: "knight" },
      { square: "5a", color: "gote", role: "rook" },
      { square: "9e", color: "gote", role: "rook" },
      { square: "6d", color: "gote", role: "bishop" },
    ]);
  }

  // 人間指定テスト4・8: 非終局の王手局面。本美濃囲いの銀3h・金4i・金5hは既に揃い、
  // 玉だけ3i(missing: 2h)。後手の桂馬4gが3iへ桂馬跳びで王手する(3i2h等へ逃げられるため
  // 詰みではない)。selectedTargetShapeId="mino_honmino"により、王手中でも内部の
  // resolvedTargetShapeIdが実際に解決されることを確認できる(単なる両玉だけの局面では
  // 検証にならないため、計画レビューで指摘された)。
  function checkNotMateSfen(): string {
    return customSfen([
      { square: "3i", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "5h", color: "sente", role: "gold" },
      { square: "4g", color: "gote", role: "knight" },
    ]);
  }

  // 成果監査REVISE(2026-09-10、修正1): 本美濃囲い(mino_honmino)が完成した状態のまま、
  // 桂馬の王手で詰まされた局面(監査担当が実機で再現)。玉2h・銀3h・金4i・金5hの
  // 本美濃完成に、桂3f(王手そのもの)・香1a(1g/1h/1iを制圧)・角4h(3g/3iを制圧)・
  // 銀1h(2g/2iを制圧。捕獲しても香1aの利きが引き続き玉に届くため王手が続く)を加え、
  // 玉の全逃げ場を塞いだ(shogiopsのisEnd/outcomeで検証済み)。
  function honminoCompletedCheckmateSfen(): string {
    return customSfen([
      { square: "2h", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "5h", color: "sente", role: "gold" },
      { square: "1a", color: "gote", role: "lance" },
      { square: "1h", color: "gote", role: "silver" },
      { square: "4h", color: "gote", role: "bishop" },
      { square: "3f", color: "gote", role: "knight" },
    ]);
  }

  // 成果監査REVISE: 上記と同じ本美濃完成の駒配置に、王手をかける桂3fだけを加えた
  // 非終局の局面(玉2hには他に逃げ場があるため詰みではない)。削りすぎ防止用
  // (王手中でも[3]shapeWeaknessは出続けることを確認する)。
  function honminoCompletedCheckedNotMateSfen(): string {
    return customSfen([
      { square: "2h", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "5h", color: "sente", role: "gold" },
      { square: "3f", color: "gote", role: "knight" },
    ]);
  }

  it("1: 自分が詰まされた局面では、urgentMessagesに詰みの文(自分側)だけが入り、[2][3][4]も出ない", () => {
    const sfen = selfCheckmateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.status.isEnd).toBe(true);
    expect(response.status.outcome?.result).toBe("checkmate");
    expect(response.status.outcome?.winner).toBe("gote");
    expect(response.plan.urgentMessages).toEqual([{ kind: "game_end", text: GAME_END_SELF_CHECKMATE_TEXT }]);
    expect(response.coach).toEqual([]);
    expect(response.plan.routes).toEqual([]);
    expect(response.plan.targetShapeProgress).toBeNull();
    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.candidateMove).toBeUndefined();
    expect(response.plan.candidateMoveLabels).toEqual({});
    expect(response.plan.directionNote).toBeNull();
    // 成果監査REVISE(W-1の漏れ): 終局時は[3](shapeWeakness)も出さない。
    expect(response.plan.shapeWeakness).toBeNull();
  });

  // STEP 5-F(A-3): 終局時はfocusTextStateを"ready"(言うことが無い)に倒す。
  // 素通しにすると、最終手の応答は必ず"pending"になり(cachedPlanが最終局面に
  // 追いつく前)、③に「急ぐことがないか、いま確かめています。」が出たまま残る。
  // 終局後は再取得しない(web側のshouldRetryPlanRefreshがisEndで止まる)ため、
  // その文は消えない。coach・shapeWeaknessと同じガードをここにも置く。
  it('A-3: 終局時はfocusTextStateが"ready"になり、③に「計算中」の文が残らない', () => {
    const sfen = selfCheckmateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };

    // cachedPlanが無い(＝素通しなら"pending"になる)状況でも"ready"であること。
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.status.isEnd).toBe(true);
    expect(response.plan.focusTextState).toBe("ready");
    expect(response.plan.focusText).toBeNull();
  });

  it("2: 相手を詰ませた局面では、urgentMessagesに詰みの文(相手側)だけが入る", () => {
    const sfen = opponentCheckmateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.status.isEnd).toBe(true);
    expect(response.status.outcome?.result).toBe("checkmate");
    expect(response.status.outcome?.winner).toBe("sente");
    expect(response.plan.urgentMessages).toEqual([{ kind: "game_end", text: GAME_END_OPPONENT_CHECKMATE_TEXT }]);
    expect(response.coach).toEqual([]);
    // 成果監査REVISE(W-1の漏れ): 終局時は[3](shapeWeakness)も出さない。
    expect(response.plan.shapeWeakness).toBeNull();
  });

  it("3: 詰み以外の終局(stalemate)では、urgentMessagesに「対局は終了しました。」だけが入る", () => {
    const sfen = stalemateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen });

    expect(response.status.isEnd).toBe(true);
    expect(response.status.outcome?.result).not.toBe("checkmate");
    expect(response.plan.urgentMessages).toEqual([{ kind: "game_end", text: GAME_END_OTHER_TEXT }]);
    expect(response.coach).toEqual([]);
    // 成果監査REVISE(W-1の漏れ): 終局時は[3](shapeWeakness)も出さない。
    expect(response.plan.shapeWeakness).toBeNull();
  });

  it("4・8・11: 非終局の王手局面では、[0]に既存の王手の文が入り、nextConsiderations/[4]は空、coachにopponent_intentが残る", () => {
    const sfen = checkNotMateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

    expect(response.status.isEnd).toBe(false);
    expect(response.plan.urgentMessages).toEqual([
      {
        kind: "in_check",
        text: "今、あなたの玉に王手がかかっています。ルール上、王手を解消する手しか指せません。",
      },
    ]);
    // nextConsiderationsが空であること(in_checkが「だけ」残るのではなく、
    // in_check自体がpartitionUrgentMessagesにより[0]へ移り、ここには何も残らない。
    // 計画レビュー2回目の訂正どおり)。
    expect(response.plan.nextConsiderations).toEqual([]);
    expect(response.plan.routes).toEqual([]);
    expect(response.plan.targetShapeProgress).toBeNull();
    expect(response.plan.resolvedTargetShapeId).toBeNull();
    expect(response.plan.candidateMoveState).toBe("unavailable");
    expect(response.plan.candidateMove).toBeUndefined();
    expect(response.plan.candidateMoveLabels).toEqual({});
    // [2][3]は王手中も現行どおり出る(coachは空にしない)。opponent_intentの残存を確認する。
    expect(response.coach?.map((c) => c.stage)).toContain("opponent_intent");
  });

  it("5: 王手を玉移動で回避した局面では、square_lostが出ない(V-1)", () => {
    const sfenBefore = customSfen([
      { square: "2h", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "2b", color: "gote", role: "lance" },
    ]);
    // 2b の香で2h の玉に王手がかかっている(2h3iが唯一の逃げ方の一つ)。
    expect(isInCheck(sfenBefore, "sente")).toBe(true);

    const sfenAfterUser = applyMove(sfenBefore, "2h3i");
    const sfenAfter = applyMove(sfenAfterUser, "2b2c");

    const stateBefore: GameState = { sfen: sfenBefore, moveHistory: [], forcedPliesUsed: 0 };
    const stateAfter: GameState = { sfen: sfenAfter, moveHistory: ["2h3i", "2b2c"], forcedPliesUsed: 0 };

    const outcome = computeMoveOutcomeAfterMove(
      stateBefore,
      stateAfter,
      "2h3i",
      "2b2c",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );
    // 判定(moveOutcomeDetector.ts)自体は変えていないため、square_lostの事実は
    // そのまま検出される(玉が2hから離れ、本美濃囲いの必須マスの一つが崩れたため)。
    expect(outcome?.facts.map((f) => f.kind)).toEqual(["square_lost"]);

    const events = computeBoardEventsAfterMove(stateBefore, "2h3i", "2b2c");
    const response = buildStateResponseWithPlan(
      stateAfter,
      undefined,
      { initialSfen: sfenBefore },
      "mino_honmino",
      false,
      null,
      outcome,
      events,
    );

    // 表示側フィルタ(V-1)により、square_lostは[1]に出ない。
    expect(response.plan.lastMoveOutcome?.messages).toEqual([]);
  });

  it("6: 王手と無関係な通常の玉移動では、square_lostが従来どおり出る", () => {
    const sfenBefore = customSfen([
      { square: "2h", color: "sente", role: "king" },
      { square: "3h", color: "sente", role: "silver" },
      { square: "4i", color: "sente", role: "gold" },
      { square: "9c", color: "gote", role: "pawn" },
    ]);
    expect(isInCheck(sfenBefore, "sente")).toBe(false);

    const sfenAfterUser = applyMove(sfenBefore, "2h1h");
    const sfenAfter = applyMove(sfenAfterUser, "9c9d");

    const stateBefore: GameState = { sfen: sfenBefore, moveHistory: [], forcedPliesUsed: 0 };
    const stateAfter: GameState = { sfen: sfenAfter, moveHistory: ["2h1h", "9c9d"], forcedPliesUsed: 0 };

    const outcome = computeMoveOutcomeAfterMove(
      stateBefore,
      stateAfter,
      "2h1h",
      "9c9d",
      { initialSfen: sfenBefore },
      "mino_honmino",
    );

    const events = computeBoardEventsAfterMove(stateBefore, "2h1h", "9c9d");
    const response = buildStateResponseWithPlan(
      stateAfter,
      undefined,
      { initialSfen: sfenBefore },
      "mino_honmino",
      false,
      null,
      outcome,
      events,
    );

    expect(response.plan.lastMoveOutcome?.messages.map((m) => m.kind)).toContain("square_lost");
  });

  it("7・12: 終局時は[2][3][4]が出ず、[1]の盤面事実・得喪の集約は現行どおり出る(形の差分文だけが落ちる)", () => {
    // toCaptureSummaryMessages/computeBoardEventsAfterMoveは current.moveHistory と
    // options.initialSfen だけから計算する既存の配線であり、current.sfen(終局判定に
    // 使う局面)とは独立している。これを利用し、「双方が取った局面」(既存テストと
    // 同じ構成)から得た本物の盤面イベント・得喪集約に、手動構成したsquare_lost
    // (形・道のりの差分文の代表例)を混ぜ、終局状態(current.sfen=詰みの局面)で
    // どちらが残りどちらが落ちるかを検証する。
    // 【注記】current.sfenとcurrent.moveHistoryが意図的に不整合(sfenは詰みの局面、
    // moveHistoryは無関係な捕獲の履歴)なため、buildStateResponse内部のcoach生成・
    // ⑤⑥⑦計算(analyzeShapeFormationの整合性チェック)がShapeFormationAnalysisErrorを
    // 投げるが、これは既存のsafeExplainPosition/safeComputeRankedPlanContextが
    // console.errorに留めて安全に空へ倒す想定どおりの経路であり(対局本体を止めない、
    // Phase1以来の既存方針)、このテスト自体が検証したい[1]のフィルタ結果には影響しない。
    // 実行時にこのエラーログが標準エラー出力に出るのは既知・想定内である。
    const captureBaseSfen = buildMutualCaptureSfen();
    const moveHistory = ["5e5d", "3d3e"];
    const boardEvents = computeBoardEventsAfterMove(
      { sfen: captureBaseSfen, moveHistory: [], forcedPliesUsed: 0 },
      "5e5d",
      "3d3e",
    );
    const lastMoveOutcome: MoveOutcome = {
      playedMoveUsi: "5e5d",
      opponentMoveUsi: "3d3e",
      facts: [
        {
          kind: "square_lost",
          targetSquare: "3h",
          targetPiece: null,
          remainingStepsBefore: null,
          remainingStepsAfter: null,
          blockingSquare: null,
          candidateKind: null,
          cause: null,
        },
      ],
    };

    const state: GameState = { sfen: selfCheckmateSfen(), moveHistory, forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(
      state,
      undefined,
      { initialSfen: captureBaseSfen },
      "mino_honmino",
      false,
      null,
      lastMoveOutcome,
      boardEvents,
    );

    expect(response.status.isEnd).toBe(true);
    // [2][3][4]
    expect(response.coach).toEqual([]);
    expect(response.plan.routes).toEqual([]);
    expect(response.plan.targetShapeProgress).toBeNull();
    expect(response.plan.candidateMoveState).toBe("unavailable");
    // 成果監査REVISE(W-1の漏れ): 終局時は[3](shapeWeakness)も出さない。
    expect(response.plan.shapeWeakness).toBeNull();
    // [1]: 盤面イベント・得喪の集約は残り、形の差分文(square_lost)は落ちる。
    const kinds = response.plan.lastMoveOutcome!.messages.map((m) => m.kind);
    expect(kinds).toContain("captured_by_you");
    expect(kinds).toContain("captured_by_opponent");
    expect(kinds).toContain("capture_summary");
    expect(kinds).not.toContain("square_lost");
  });

  it("9: 王手中・終局時は、computeReachablePlanがエンジン(MultiPV)を一切呼ばない", async () => {
    const sfen = checkNotMateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const engine = makeMockLowPriorityEngine([]);

    const result = await computeReachablePlan(state, engine, { initialSfen: sfen }, "mino_honmino");

    // 王手中でなければ候補手が存在するはずの局面であることの確認
    // (suppressPlanが無ければcandidateMoveが計算されていたはずの局面、という前提の担保)。
    expect(result.targetShapeId).toBe("mino_honmino");
    expect(result.candidateMove).toBeUndefined();
    expect(engine.goMultiPv).not.toHaveBeenCalled();

    const endSfen = selfCheckmateSfen();
    const endState: GameState = { sfen: endSfen, moveHistory: [], forcedPliesUsed: 0 };
    const endResult = await computeReachablePlan(endState, engine, { initialSfen: endSfen });
    expect(endResult.candidateMove).toBeUndefined();
    expect(engine.goMultiPv).not.toHaveBeenCalled();
  });

  it("成果監査REVISE: 本美濃囲いが完成したまま詰まされた局面では、shapeWeaknessもnullになる(W-1の漏れの回帰テスト)", () => {
    const sfen = honminoCompletedCheckmateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

    expect(response.status.isEnd).toBe(true);
    expect(response.status.outcome?.result).toBe("checkmate");
    expect(response.status.outcome?.winner).toBe("gote");
    expect(response.plan.urgentMessages).toEqual([{ kind: "game_end", text: GAME_END_SELF_CHECKMATE_TEXT }]);
    expect(response.coach).toEqual([]);
    expect(response.plan.shapeWeakness).toBeNull();
  });

  it("成果監査REVISE(削りすぎ防止): 本美濃囲いが完成したまま王手を受けている(非終局)局面では、shapeWeaknessは従来どおり残る", () => {
    const sfen = honminoCompletedCheckedNotMateSfen();
    const state: GameState = { sfen, moveHistory: [], forcedPliesUsed: 0 };
    const response = buildStateResponseWithPlan(state, undefined, { initialSfen: sfen }, "mino_honmino");

    expect(response.status.isEnd).toBe(false);
    expect(isInCheck(sfen, "sente")).toBe(true);
    expect(response.plan.shapeWeakness?.shapeId).toBe("mino_honmino");
  });
});

// STEP 4-6(A・B、人間承認済み): [1]に出す前に、MoveOutcomeFactの段階で表示側フィルタを
// 掛ける。moveOutcomeDetector.tsの判定・explainMoveOutcomeの文言生成そのものは変えない
// (このテストではfactsを直接組み立てて検証する)。
describe("STEP 4-6: filterMoveOutcomeFactsForDisplay(A・B)", () => {
  function fact(kind: MoveOutcomeFact["kind"], overrides: Partial<MoveOutcomeFact> = {}): MoveOutcomeFact {
    return {
      kind,
      targetSquare: null,
      targetPiece: null,
      remainingStepsBefore: null,
      remainingStepsAfter: null,
      blockingSquare: null,
      candidateKind: null,
      cause: null,
      ...overrides,
    };
  }

  function outcomeWith(facts: MoveOutcomeFact[]): MoveOutcome {
    return { playedMoveUsi: "7g7f", opponentMoveUsi: "3c3d", facts };
  }

  it("A(2026-09-10人間判断d): preparation_resolvedが単独で立つ場合でも出さない", () => {
    const outcome = outcomeWith([fact("preparation_resolved")]);
    expect(filterMoveOutcomeFactsForDisplay(outcome).facts).toEqual([]);
  });

  it("A-1: route_first_move_available・preparation_resolved・準備手のplayed_candidateが併存するときは、route_first_move_availableだけ残す", () => {
    const outcome = outcomeWith([
      fact("played_candidate", { candidateKind: "preparation" }),
      fact("route_first_move_available"),
      fact("preparation_resolved"),
    ]);
    expect(filterMoveOutcomeFactsForDisplay(outcome).facts.map((f) => f.kind)).toEqual([
      "route_first_move_available",
    ]);
  });

  it("A-1: 準備手のplayed_candidateが単独で立つ場合は残す", () => {
    const outcome = outcomeWith([fact("played_candidate", { candidateKind: "preparation" })]);
    expect(filterMoveOutcomeFactsForDisplay(outcome).facts.map((f) => f.kind)).toEqual(["played_candidate"]);
  });

  it("準備手でないplayed_candidateは、route_first_move_availableと併存しても残す(A-1の対象外)", () => {
    const outcome = outcomeWith([
      fact("played_candidate", { candidateKind: "route_step" }),
      fact("route_first_move_available"),
    ]);
    expect(filterMoveOutcomeFactsForDisplay(outcome).facts.map((f) => f.kind)).toEqual([
      "played_candidate",
      "route_first_move_available",
    ]);
  });

  it("B: played_non_candidateが単独で立つ場合、フィルタ後は空になりexplainMoveOutcomeの既存文(no_notable_change)になる", () => {
    const outcome = outcomeWith([fact("played_non_candidate")]);
    const filtered = filterMoveOutcomeFactsForDisplay(outcome);
    expect(filtered.facts).toEqual([]);
    expect(explainMoveOutcome(filtered)).toEqual([{ kind: "no_notable_change", text: NO_NOTABLE_CHANGE_TEXT }]);
  });

  it("フィルタの対象外の事実(route_advancedなど)はそのまま残る", () => {
    const outcome = outcomeWith([fact("route_advanced", { remainingStepsBefore: 3, remainingStepsAfter: 2 })]);
    expect(filterMoveOutcomeFactsForDisplay(outcome).facts).toEqual(outcome.facts);
  });
});

// STEP 4-6(D、人間承認済み): [4]のroute_first_move_playable・ordering_note・
// shape_completedを表示側で落とす。no_playable_route_first_move・in_checkは対象外。
describe("STEP 4-6: filterNextConsiderationsForDisplay(D)", () => {
  const playable = {
    kind: "route_first_move_playable",
    text: "７七桂は、道のりの一手目です。",
  } satisfies NextConsiderationMessage;
  const ordering = { kind: "ordering_note", text: "並び順の注記。" } satisfies NextConsiderationMessage;
  const completed = {
    kind: "shape_completed",
    text: "この形に必要なマスは、すべて埋まっています。",
  } satisfies NextConsiderationMessage;
  const noPlayable = {
    kind: "no_playable_route_first_move",
    text: "今の局面では、その形へ向かう道のりの一手目を、どれも指すことができません。",
  } satisfies NextConsiderationMessage;
  const inCheck = {
    kind: "in_check",
    text: "今、あなたの玉に王手がかかっています。",
  } satisfies NextConsiderationMessage;

  it("route_first_move_playable・ordering_note・shape_completedを落とす", () => {
    expect(filterNextConsiderationsForDisplay([playable, ordering, completed])).toEqual([]);
  });

  it("no_playable_route_first_move・in_checkは対象外(既存規則のまま残す)", () => {
    expect(filterNextConsiderationsForDisplay([noPlayable, inCheck])).toEqual([noPlayable, inCheck]);
  });
});

// STEP U6-H(計測用): suppressTargetShapeProgressオプション。
// targetShapeProgressだけをnullにし、resolvedTargetShapeId・道のり(candidateMoveLabels)・
// candidateMoveStateは変えない(docs/STEP_UNIT6_PLAN_2026-09-12.md 13.2)。
describe("STEP U6-H: StateResponseOptions.suppressTargetShapeProgress", () => {
  it("既定(オプションを渡さない)ではtargetShapeProgressが今までどおり出る", () => {
    const state = gameStateAfter([]);
    const response = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");

    expect(response.plan.targetShapeProgress).not.toBeNull();
    expect(response.plan.targetShapeProgress?.shapeId).toBe(response.plan.resolvedTargetShapeId);
  });

  it("suppressTargetShapeProgress: trueのときtargetShapeProgressがnullになり、resolvedTargetShapeIdは変わらない", () => {
    const state = gameStateAfter([]);
    const withoutSuppress = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");
    const withSuppress = buildStateResponseWithPlan(
      state,
      undefined,
      { suppressTargetShapeProgress: true },
      "mino_honmino",
    );

    expect(withSuppress.plan.targetShapeProgress).toBeNull();
    expect(withSuppress.plan.resolvedTargetShapeId).toBe(withoutSuppress.plan.resolvedTargetShapeId);
    expect(withSuppress.plan.resolvedTargetShapeId).not.toBeNull();
  });

  it("suppressTargetShapeProgress: trueでもcandidateMoveLabels(道のり)とcandidateMoveStateが変わらない", () => {
    const state = gameStateAfter([]);
    const withoutSuppress = buildStateResponseWithPlan(state, undefined, {}, "mino_honmino");
    const withSuppress = buildStateResponseWithPlan(
      state,
      undefined,
      { suppressTargetShapeProgress: true },
      "mino_honmino",
    );

    expect(withSuppress.plan.candidateMoveLabels).toEqual(withoutSuppress.plan.candidateMoveLabels);
    expect(withSuppress.plan.candidateMoveState).toBe(withoutSuppress.plan.candidateMoveState);
  });
});
