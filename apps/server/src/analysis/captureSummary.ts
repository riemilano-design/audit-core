// 対局開始からの指し手履歴全体を毎回再生し、「駒の得喪」(N-3・ζ-3で文言確定済み)を
// 事実として集約する(Phase 7 Unit 4 / STEP 4-3b・2026-09-10人間承認)。
//
// 【このモジュールがやること】
// 指し手履歴を毎回最初から再生し、各手について「着手前の局面で移動先に相手の駒が
// あったか」(既存 boardEventDetector.ts の捕獲判定と同じ基準)だけで捕獲を数える。
// 状態は一切保持せず、同じ履歴に対しては常に同じ結果を返す(決定的)。持ち駒の枚数は
// 使わない(打った駒が差し引かれるため、取った事実の集約にならない)。
//
// 【boardEventDetector.ts の BoardEvent を再利用しない理由】
// BoardEvent.piece は成駒を取った場合にnullになる(推測して名前を付けない方針のため)。
// 本モジュールは人間承認済みK-1(取られた成駒は元の駒種で数える)を満たす必要があり、
// BoardEventを経由すると成駒の捕獲を黙って数え落としてしまう。そのため、着手前の局面の
// 生のRoleを直接見て、成駒はここで正規化してから数える。
//
// 【このモジュールが絶対にやらないこと】
// - 「有利」「不利」「損」「得」「互角」等の評価語は使わない。
// - 差引きの合計(取った枚数 - 取られた枚数)は述べない。
// - 持ち駒の枚数からの逆算はしない。
// - エンジン・LLMには一切依存しない(決定的な純粋関数)。

import type { Color, Role } from "shogiops/types";
import { isDrop, parseUsi } from "shogiops/util";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { normalizeRole } from "./pieceThreatDetector.js";
import { roleToJapanese } from "./pieceMapping.js";

export interface CaptureCounts {
  /** あなた(先手)が相手から取った駒種ごとの枚数(成駒は元の駒種に正規化済み)。 */
  you: Map<Role, number>;
  /** 相手(後手)があなたから取った駒種ごとの枚数(成駒は元の駒種に正規化済み)。 */
  opponent: Map<Role, number>;
}

/**
 * 対局開始からの全手について、既存の捕獲判定(着手前の局面で移動先に相手の駒が
 * あった。打つ手は対象外)で「取った側」と「取られた駒の駒種」を数える。
 * moveHistoryから毎回再計算し、状態は持たない。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。エンジン・LLMには依存しない)。
 */
export function countCaptures(
  moveHistory: string[],
  initialSfen: string = DEFAULT_INITIAL_SFEN,
): CaptureCounts {
  const { sfens } = replayMoveHistory(moveHistory, initialSfen);
  const you = new Map<Role, number>();
  const opponent = new Map<Role, number>();

  moveHistory.forEach((moveUsi, index) => {
    const move = parseUsi(moveUsi);
    // 解釈できない指し手について推測はしない(replayMoveHistoryが既に例外を
    // 投げているはずだが、念のため何も数えない)。
    if (!move || isDrop(move)) return;

    // sfensの要素数はmoveHistory.length + 1(moveHistory.tsの仕様)であり、
    // indexは常に範囲内(recognitionTimeline.tsと同じ前提)。
    const positionBefore = parsePosition(sfens[index]!);
    const captured = positionBefore.board.get(move.to);
    if (!captured) return;

    const moverColor: Color = positionBefore.turn;
    if (captured.color === moverColor) return;

    const role = normalizeRole(captured.role);
    // MVP確定仕様: sente=自分、gote=相手(moveHistory.tsのMoveEventコメントと同じ前提)。
    const taker = moverColor === "sente" ? you : opponent;
    taker.set(role, (taker.get(role) ?? 0) + 1);
  });

  return { you, opponent };
}

/** L-1で確定した固定順(飛→角→金→銀→桂→香→歩)。将棋としての重要度ではない。 */
const ROLE_ORDER: readonly Role[] = ["rook", "bishop", "gold", "silver", "knight", "lance", "pawn"];

function roleOrderIndex(role: Role): number {
  const index = ROLE_ORDER.indexOf(role);
  return index === -1 ? ROLE_ORDER.length : index;
}

/**
 * 「{駒名}を{n}枚」をL-1の固定順に並べ、読点で連結する。
 * 対応表に無い駒種(理論上は玉のみだが、合法な対局では玉は取られない)は
 * 推測して名前を付けず、その駒種を除いて連結する。
 */
function joinPieceCounts(counts: Map<Role, number>): string {
  return [...counts.entries()]
    .sort((a, b) => roleOrderIndex(a[0]) - roleOrderIndex(b[0]))
    .map(([role, n]) => {
      const name = roleToJapanese(role);
      return name ? `${name}を${n}枚` : null;
    })
    .filter((segment): segment is string => segment !== null)
    .join("、");
}

export type CaptureSummaryMessageKind = "capture_summary";

export interface CaptureSummaryMessage {
  kind: CaptureSummaryMessageKind;
  text: string;
}

function totalOf(counts: Map<Role, number>): number {
  return [...counts.values()].reduce((sum, n) => sum + n, 0);
}

/**
 * 駒の得喪の集約を、ζ-3で確定した4文言(docs/PHASES.md「駒の得喪(N-3)」)へ変換する。
 * 双方0枚のときはこの文を出さない(N-1)。それ以外は毎回この1件を返す。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function explainCaptureSummary(
  moveHistory: string[],
  initialSfen: string = DEFAULT_INITIAL_SFEN,
): CaptureSummaryMessage[] {
  const { you, opponent } = countCaptures(moveHistory, initialSfen);
  const youTotal = totalOf(you);
  const opponentTotal = totalOf(opponent);

  if (youTotal === 0 && opponentTotal === 0) return [];

  let text: string;
  if (youTotal > 0 && opponentTotal === 0) {
    text = `ここまでに、あなたが相手の${joinPieceCounts(you)}取っています。相手はまだ駒を取っていません。`;
  } else if (youTotal === 0 && opponentTotal > 0) {
    text = `ここまでに、相手があなたの${joinPieceCounts(opponent)}取っています。あなたはまだ駒を取っていません。`;
  } else {
    text = `ここまでに、あなたは相手の${joinPieceCounts(you)}、相手はあなたの${joinPieceCounts(opponent)}取っています。`;
  }

  return [{ kind: "capture_summary", text }];
}
