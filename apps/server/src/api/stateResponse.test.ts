import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import type { CoachExplanation } from "../analysis/explanationGenerator.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "../analysis/moveHistory.js";
import type { GameState } from "../game/gameSession.js";
import { buildStateResponse } from "./stateResponse.js";

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
