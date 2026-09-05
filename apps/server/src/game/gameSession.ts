// 四間飛車(自分=先手)vs居飛車(AI=後手)の対局を1局分だけ進行させる、
// Phase 0時点での最小限のゲームセッション。
// legalMoves/applyMove(合法手判定)・forcedOpponentOpening(相手の最小序盤進行)・
// scenarioOpponentOpening(検証用シナリオ進行)・UsiEngine(エンジンのbestmove)を束ねる。

import { makeSfen, parseSfen } from "shogiops/sfen";
import type { Outcome } from "shogiops/types";
import type { UsiEngine } from "../engine/usiEngine.js";
import { pickForcedOpponentMove } from "../engine/forcedOpponentOpening.js";
import { pickScenarioMove, type ScenarioId } from "../engine/scenarioOpponentOpening.js";
import { applyMove, IllegalMoveError } from "../rules/applyMove.js";
import { getGameOutcome, isGameOver } from "../rules/gameStatus.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

export interface GameState {
  sfen: string;
  moveHistory: string[];
  forcedPliesUsed: number;
  /**
   * 検証用シナリオ(scenarioOpponentOpening.ts)を指定した対局かどうか。
   * 通常対局(undefined)では従来通りforcedOpponentOpeningを使う。
   */
  scenario?: ScenarioId;
}

export interface GameStatus {
  isEnd: boolean;
  outcome: Outcome | undefined;
}

export class HumanMoveError extends Error {}

export function createInitialGameState(scenario?: ScenarioId): GameState {
  return { sfen: INITIAL_SFEN, moveHistory: [], forcedPliesUsed: 0, scenario };
}

export function getStatus(state: GameState): GameStatus {
  return { isEnd: isGameOver(state.sfen), outcome: getGameOutcome(state.sfen) };
}

/**
 * 人間(四間飛車=先手)の一手を適用する。非合法な手はHumanMoveErrorを投げる
 * (呼び出し側でユーザーへのエラー表示に使う想定)。
 */
export function playHumanMove(state: GameState, moveUsi: string): GameState {
  let nextSfen: string;
  try {
    nextSfen = applyMove(state.sfen, moveUsi);
  } catch (err) {
    if (err instanceof IllegalMoveError) throw new HumanMoveError(err.message);
    throw err;
  }
  return {
    sfen: nextSfen,
    moveHistory: [...state.moveHistory, moveUsi],
    forcedPliesUsed: state.forcedPliesUsed,
    scenario: state.scenario,
  };
}

// UsiEngineのうち、この関数が実際に使うメソッドのみを要求する
// (テストで実プロセスを起動せずモックに差し替えられるようにするため)。
export type OpponentEngine = Pick<UsiEngine, "position" | "go">;

/**
 * 居飛車(相手=後手)の一手を、強制進行(forcedOpponentOpening、または
 * state.scenario指定時はscenarioOpponentOpening)またはエンジンのbestmoveから
 * 選び適用する。既に終局している場合は何もせずstateをそのまま返す。
 */
export async function playOpponentMove(state: GameState, engine: OpponentEngine): Promise<GameState> {
  if (isGameOver(state.sfen)) return state;

  const forcedMove = state.scenario
    ? pickScenarioMove(state.sfen, state.forcedPliesUsed, state.scenario)
    : pickForcedOpponentMove(state.sfen, state.forcedPliesUsed);

  let moveUsi: string;
  let forcedPliesUsed = state.forcedPliesUsed;

  if (forcedMove) {
    moveUsi = forcedMove;
    forcedPliesUsed += 1;
  } else {
    engine.position(state.sfen);
    const { bestmove } = await engine.go({ movetimeMs: 1000 });
    if (!bestmove || bestmove === "resign" || bestmove === "win") {
      // エンジンが指し手を返さない(投了等)場合は局面を変えずそのまま返す。
      // 終局判定自体はgetStatus側(isGameOver)に委ねる。
      return state;
    }
    moveUsi = bestmove;
  }

  const nextSfen = applyMove(state.sfen, moveUsi);
  return {
    sfen: nextSfen,
    moveHistory: [...state.moveHistory, moveUsi],
    forcedPliesUsed,
    scenario: state.scenario,
  };
}
