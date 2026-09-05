// planChangeDetector.ts(Unit1)がplanChanged=trueと判定した場合にのみ呼び出すことを
// 想定した、崩れた理由の分類(Phase3 Unit2、人間承認済み)。
//
// 【判定条件(承認済み・最小仕様)】
// - candidate_piece_captured: 前回PlanSnapshot.candidateMoveUsisからplayedMoveUsiを
//   除外した残りの候補手について、その移動元マス(通常手のみ、ドロップは対象外)に
//   あった自分の駒が、相手の着手後の局面に存在しなくなっている場合。
//   stateBeforeMoveからstateAfterMoveまでの間に起きた自分側の駒の変化は、
//   ユーザー自身の着手(playedMoveUsi、既に除外済み)以外にはあり得ないため、
//   この消失は相手の着手による捕獲だと機械的に判定できる(新しい将棋知識ではなく、
//   手番交代というルールそのものから導ける事実)。
// - unknown: 上記のように断定できない場合すべて(王手放置・駒の利きによる非合法化・
//   下記の「Unit1の既知課題」に該当する場合等を含む)。「候補手が非合法になった」を
//   無条件に「相手が原因」と断定しないための安全側の既定値。
//
// 【Unit1の既知課題との関係(重要・今回は修正しない)】
// 複数の候補手が同一targetSquareを狙うケースでは、ユーザーがそのうち1つを
// 指しただけで、相手の着手と無関係に残りの候補が非合法になり得る
// (detectPlanChangeの既知の未解決課題、人間承認済み)。この場合、残存候補の
// 移動元には自分の駒がそのまま残っている(自分の駒は動いていないため)ため、
// 下記のcaptured判定には該当せず、安全にunknownへ落ちる
// (=誤ってcandidate_piece_capturedと断定することはない)。
//
// 【今回実装しないこと(承認済み)】
// target_square_occupied_by_own_piece・王手や駒の利きによる理由判定・
// エンジン評価値・cp値・MultiPV順位・LLMによる理由判定はいずれも実装しない。
// detectPlanChange自体(planChangeDetector.ts)も変更しない。

import { isDrop, parseUsi } from "shogiops/util";
import { parsePosition } from "../rules/sfenPosition.js";
import type { PlanSnapshot } from "./planChangeDetector.js";

export type PlanChangeReason = "candidate_piece_captured" | "unknown";

/**
 * detectPlanChangeがtrueを返した場合にのみ呼び出すことを想定する
 * (呼び出し元がplanChanged===trueを確認済みであることが前提。falseの場合の
 * 呼び出しは想定していない)。
 *
 * 純粋関数(決定的)。エンジン・LLMには一切依存しない。
 */
export function classifyPlanChangeReason(
  previous: PlanSnapshot,
  playedMoveUsi: string,
  afterSfen: string,
): PlanChangeReason {
  const remaining = previous.candidateMoveUsis.filter((usi) => usi !== playedMoveUsi);
  const pos = parsePosition(afterSfen);
  const selfColor = pos.turn;

  for (const usi of remaining) {
    const move = parseUsi(usi);
    if (!move || isDrop(move)) continue; // ドロップは移動元が無いため対象外(unknown側)。
    const occupant = pos.board.get(move.from);
    if (!occupant || occupant.color !== selfColor) {
      // 除外済みの着手以外で、移動元にあったはずの自分の駒が無い
      // (あるいは相手の駒に置き換わっている)= 相手の着手による捕獲。
      return "candidate_piece_captured";
    }
  }

  return "unknown";
}
