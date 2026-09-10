// 初期局面から始まる対局を1局分だけ進行させる、サーバー側のゲームセッション。
// legalMoves/applyMove(合法手判定)・scenarioOpponentOpening(検証用シナリオ進行)・
// UsiEngine(エンジンのbestmove)を束ねる。
//
// STEP ζ-4c-1: 相手AI制御機構(opponentControlSelector.ts・scenarioRepository.ts)を
// 追加した。ただし承認済み(verification_status: human_approved)のscenario variantは
// 実データとして存在しない(data/openings/*.jsonのscenarioはnullのまま)ため、
// 現時点では常に候補0件であり、この経路が実際に発動することはない。
//
// Phase 7 Unit 0: forcedOpponentOpening(居飛車強制)は本番導線から外した
// ([../../../../CLAUDE.md](../../../../CLAUDE.md) の「絶対的な上位原則」)。
// state.scenario指定時(開発モード ?scenario=)のみscenarioOpponentOpeningを使い、
// 通常対局ではエンジンのbestmoveへ落ちる。forcedOpponentOpening.ts自体は
// 削除せず、開発・検証用およびテスト用に残す。

import { makeSfen, parseSfen } from "shogiops/sfen";
import type { Outcome } from "shogiops/types";
import type { UsiEngine } from "../engine/usiEngine.js";
import { generateOpponentControlSeed, selectVariant } from "../engine/opponentControlSelector.js";
import { pickScenarioMove, type ScenarioId } from "../engine/scenarioOpponentOpening.js";
import type { ApprovedScenarioVariant } from "../engine/scenarioRepository.js";
import { applyMove, IllegalMoveError } from "../rules/applyMove.js";
import { getGameOutcome, isGameOver } from "../rules/gameStatus.js";
import { isLegalMove } from "../rules/legalMoves.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

/** ApprovedScenarioVariantを一意に識別するための内部キー(openingId・variantIdの組)。 */
function variantKey(variant: ApprovedScenarioVariant): string {
  return `${variant.openingId}/${variant.variantId}`;
}

export interface GameState {
  sfen: string;
  moveHistory: string[];
  forcedPliesUsed: number;
  /**
   * 検証用シナリオ(scenarioOpponentOpening.ts)を指定した対局かどうか。
   * 通常対局(undefined)ではforcedOpponentOpeningを使わず、エンジンのbestmoveへ落ちる。
   */
  scenario?: ScenarioId;
  /**
   * 直近の相手の着手が、次の2経路のいずれかによって実際に選択・採用された
   * 手だったかどうかの確定事実。
   * - 経路1: 承認済みvariant(opponentControl)による選択
   * - 経路2: state.scenario指定時(開発・検証モード専用)のscenarioOpponentOpeningによる選択
   * forcedPliesUsedから推測しない(forcedPliesUsedは「王手を飛車でしか
   * 回避できない」等でpickScenarioMoveがundefinedを返した回には増えないまま
   * エンジンのbestmoveが採用されることがあり、その値だけでは直近の一手が
   * 本当にforcedだったかを再現できないため)。playOpponentMove内で
   * forcedMoveの有無をその場で確認し、その結果だけを記録する。
   * 相手がまだ一度も指していない場合(初期状態)や、人間の着手ではこの値は
   * 変化しない。省略時(古いテストフィクスチャ等)はfalse相当として扱われる。
   */
  wasLastOpponentMoveForced?: boolean;
  /**
   * 相手AIの制御状態(サーバー内部専用)。承認済みvariantが1件も無い場合や、
   * createInitialGameStateにcontrolを渡さなかった場合(既存呼び出し)はundefined。
   */
  opponentControl?: OpponentControlState;
}

/**
 * 相手AIの制御状態(サーバー内部専用)。
 * docs/PHASES.md Phase 4「その後の変更」により、相手AIが選んだ狙いはユーザーへ開示しない。
 * GameState はサーバー内部の型であり、api/stateResponse.ts の toPublicGameState() を
 * 通らない限り公開されない(docs/ARCHITECTURE.md 6. の公開境界)。
 */
export interface OpponentControlState {
  /** 選択の再現に使う乱数シード。公開しない */
  seed: number;
  /** 選ばれた variant。承認済み候補が0件なら undefined */
  selectedVariantId?: string;
  /** 選ばれた variant の moves を何手消費したか */
  movesUsed: number;
}

export interface GameStatus {
  isEnd: boolean;
  outcome: Outcome | undefined;
}

export class HumanMoveError extends Error {}

/**
 * STEP 4-7B(P-11。人間承認 H-1): IllegalMoveErrorのmessage(開発用。
 * 末尾に"(局面: "…SFEN…")"を含む)から、ユーザー向けのHumanMoveErrorに渡す文だけを
 * 作る純粋関数。末尾の"(局面: "…")"を取り除くだけで、それ以外の文言は一切変えない
 * (新しい文言を作らない)。該当する末尾が無ければそのまま返す
 * (例: applyMove.tsの「指し手の解析に失敗しました: "…"」はSFENを含まないため無変更)。
 */
export function toHumanMoveErrorMessage(message: string): string {
  return message.replace(/\(局面: ".*"\)$/, "").trimEnd();
}

export interface OpponentControlOptions {
  /** 相手AI制御の候補(承認済みvariantのみ)。省略時はopponentControlを作らない。 */
  variants?: ApprovedScenarioVariant[];
  /** 選択に使うseed。省略時はgenerateOpponentControlSeed()で生成する(テストからは注入できる)。 */
  seed?: number;
}

/**
 * 相手AI制御の候補(control.variants)から、seed付きランダムで1件を均等に選び、
 * OpponentControlStateを組み立てる。control.variantsが渡されなければundefined
 * (既存の呼び出し・既存の挙動を変えない)。
 */
function buildOpponentControlState(control?: OpponentControlOptions): OpponentControlState | undefined {
  if (!control?.variants) return undefined;
  const seed = control.seed ?? generateOpponentControlSeed();
  const selected = selectVariant(control.variants, seed);
  return { seed, selectedVariantId: selected ? variantKey(selected) : undefined, movesUsed: 0 };
}

export function createInitialGameState(scenario?: ScenarioId, control?: OpponentControlOptions): GameState {
  return {
    sfen: INITIAL_SFEN,
    moveHistory: [],
    forcedPliesUsed: 0,
    scenario,
    wasLastOpponentMoveForced: false,
    opponentControl: buildOpponentControlState(control),
  };
}

export function getStatus(state: GameState): GameStatus {
  return { isEnd: isGameOver(state.sfen), outcome: getGameOutcome(state.sfen) };
}

/**
 * 人間(先手)の一手を適用する。非合法な手はHumanMoveErrorを投げる
 * (呼び出し側でユーザーへのエラー表示に使う想定)。
 */
export function playHumanMove(state: GameState, moveUsi: string): GameState {
  let nextSfen: string;
  try {
    nextSfen = applyMove(state.sfen, moveUsi);
  } catch (err) {
    if (err instanceof IllegalMoveError) throw new HumanMoveError(toHumanMoveErrorMessage(err.message));
    throw err;
  }
  return {
    sfen: nextSfen,
    moveHistory: [...state.moveHistory, moveUsi],
    forcedPliesUsed: state.forcedPliesUsed,
    scenario: state.scenario,
    // 人間の着手では「直近の相手の着手がforcedだったか」という事実は変わらないため、
    // そのまま引き継ぐ(Phase4)。
    wasLastOpponentMoveForced: state.wasLastOpponentMoveForced,
    // STEP ζ-4c-1: opponentControl(選択済みvariant・movesUsed)も、人間の着手では
    // 一切変化しない事実であるため、そのまま引き継ぐ。この関数はスプレッド(...state)
    // ではなくフィールドを個別列挙しているため、引き継ぎを書き忘れるとコンパイルは
    // 通ったまま、人間が1手指すたびに選択済みvariantが消える静かなバグになる
    // (opponentControlがオプショナルフィールドのため型エラーにならない)。
    opponentControl: state.opponentControl,
  };
}

// UsiEngineのうち、この関数が実際に使うメソッドのみを要求する
// (テストで実プロセスを起動せずモックに差し替えられるようにするため)。
export type OpponentEngine = Pick<UsiEngine, "position" | "go">;

/**
 * state.opponentControlが選んでいるvariantの、まだ使っていない手(moves[movesUsed])を、
 * 現局面で合法な場合に限り返す。次のいずれかに該当する場合はundefined
 * (呼び出し側は経路2以降へフォールバックする。movesUsedは増やさない):
 * - 承認済みvariantが選ばれていない(選択候補が0件だった)
 * - approvedVariantsの中に該当するvariantが見つからない
 * - variantのmovesを使い切った
 * - 次の手が、人間側の着手により非合法になった
 */
function pickOpponentControlMove(
  state: GameState,
  approvedVariants: readonly ApprovedScenarioVariant[],
): string | undefined {
  const selectedVariantId = state.opponentControl?.selectedVariantId;
  if (!selectedVariantId) return undefined;
  const variant = approvedVariants.find((v) => variantKey(v) === selectedVariantId);
  if (!variant) return undefined;
  const moveUsi = variant.moves[state.opponentControl!.movesUsed];
  if (moveUsi === undefined) return undefined;
  if (!isLegalMove(state.sfen, moveUsi)) return undefined;
  return moveUsi;
}

/**
 * 相手の一手を選び適用する。既に終局している場合は何もせずstateを
 * そのまま返す。優先順位は次の3段階(上から順に試し、得られなければ次へ
 * フォールバックする。STEP ζ-4c-1で経路1を追加した):
 *   1. state.opponentControlが選んでいるvariantの手(現局面で合法な場合のみ)
 *   2. state.scenario指定時のみscenarioOpponentOpening(開発モード ?scenario= 専用)
 *   3. エンジンのbestmove(通常対局はここが既定経路になる。Phase 7 Unit 0)
 *
 * forcedOpponentOpening(旧・居飛車強制の経路)は本番導線から外れており、
 * この関数からは呼ばれない([../../../../CLAUDE.md](../../../../CLAUDE.md) の
 * 「絶対的な上位原則」)。ファイル自体は開発・検証用およびテスト用に残す。
 *
 * approvedVariantsは、経路1の実体(moves)を解決するために必要な承認済みvariant一覧
 * (server.tsがscenarioRepository.tsから取得して渡す想定)。省略時(空配列)は
 * 経路1が発動せず、経路2→3のみになる。
 */
export async function playOpponentMove(
  state: GameState,
  engine: OpponentEngine,
  approvedVariants: ApprovedScenarioVariant[] = [],
): Promise<GameState> {
  if (isGameOver(state.sfen)) return state;

  const controlMove = pickOpponentControlMove(state, approvedVariants);

  let moveUsi: string;
  let forcedPliesUsed = state.forcedPliesUsed;
  let opponentControl = state.opponentControl;
  // Phase4: forcedMove/controlMoveの有無(=強制進行/相手AI制御の手が実際に
  // 採用されたか)を、その場で確定的に記録する。forcedPliesUsedからの
  // 逆算・推測はしない(GameState.wasLastOpponentMoveForcedのコメント参照)。
  let wasLastOpponentMoveForced: boolean;

  if (controlMove) {
    // 経路1: 相手AI制御(承認済みvariant)の手。
    moveUsi = controlMove;
    wasLastOpponentMoveForced = true;
    opponentControl = { ...state.opponentControl!, movesUsed: state.opponentControl!.movesUsed + 1 };
  } else {
    // Phase 7 Unit 0: forcedOpponentOpening(旧・経路3)は本番導線から外す。
    // state.scenario指定時(開発モード ?scenario=)のみscenarioOpponentOpeningを使う。
    // 通常対局(state.scenarioが無い)ではforcedMoveは常にundefinedとなり、
    // 経路3(エンジンのbestmove)へ落ちる。pickForcedOpponentMove自体・
    // forcedOpponentOpening.tsは削除せず、開発・検証用およびテスト用に残す。
    const forcedMove = state.scenario
      ? pickScenarioMove(state.sfen, state.forcedPliesUsed, state.scenario)
      : undefined;

    if (forcedMove) {
      // 経路2: state.scenario指定時のscenarioOpponentOpening(開発モード専用)。
      moveUsi = forcedMove;
      forcedPliesUsed += 1;
      wasLastOpponentMoveForced = true;
    } else {
      // 経路3: エンジンのbestmove。
      engine.position(state.sfen);
      const { bestmove } = await engine.go({ movetimeMs: 1000 });
      if (!bestmove || bestmove === "resign" || bestmove === "win") {
        // エンジンが指し手を返さない(投了等)場合は局面を変えずそのまま返す。
        // 終局判定自体はgetStatus側(isGameOver)に委ねる。実際に着手が行われて
        // いないため、wasLastOpponentMoveForced・opponentControlも含め既存状態を
        // そのまま維持する。
        return state;
      }
      moveUsi = bestmove;
      wasLastOpponentMoveForced = false;
    }
  }

  const nextSfen = applyMove(state.sfen, moveUsi);
  return {
    sfen: nextSfen,
    moveHistory: [...state.moveHistory, moveUsi],
    forcedPliesUsed,
    scenario: state.scenario,
    wasLastOpponentMoveForced,
    opponentControl,
  };
}
