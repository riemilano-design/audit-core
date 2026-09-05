// planChangeDetector.ts(Unit1)がplanChanged=trueと判定した場合にのみ呼び出すことを
// 想定した、崩れた理由の分類(Phase3 Unit2、人間承認済み。今回はUnit2の追加分類)。
//
// 【判定条件(承認済み)】
// - candidate_piece_captured: 前回PlanSnapshot.candidateMoveUsisからplayedMoveUsiと
//   兄弟候補(下記参照)を除外した残りの候補手について、その移動元マス(通常手のみ、
//   ドロップは対象外)にあった自分の駒が、相手の着手後の局面に存在しなくなっている
//   場合。stateBeforeMoveからstateAfterMoveまでの間に起きた自分側の駒の変化は、
//   ユーザー自身の着手(playedMoveUsi、既に除外済み)以外にはあり得ないため、
//   この消失は相手の着手による捕獲だと機械的に判定できる(新しい将棋知識ではなく、
//   手番交代というルールそのものから導ける事実)。
// - candidate_move_illegal_due_to_check(今回追加): 残存候補が玉の移動であり、
//   移動先マスが現在空いていて(相手駒の捕獲でも自駒の占有でもなく)、かつ
//   shogiopsの既存API pos.squareAttackers(to, 相手の色, occupied) がそのマスへの
//   相手の利きを検出した場合。「玉が相手の利きに入るため動けない(王手放置)」という
//   将棋の基本ルールそのものであり、新しい閾値・評価値は一切導入しない。
// - candidate_piece_pinned(今回追加): 残存候補の駒が玉ではなく、移動先マスが
//   現在空いていて、かつshogiopsの既存API pos.ctx().blockers(現在ピンされている
//   駒の集合)にその移動元マスが含まれる場合。「その駒を動かすと自玉が王手になる
//   ため動けない(ピン)」という将棋の基本ルールそのものである。
// - unknown: 上記のいずれにも安全に断定できない場合すべて(打ち歩詰め等の特殊な
//   ケース、移動先が捕獲・自駒占有を伴う場合、下記の「既知課題」に該当する場合等を
//   含む)。「候補手が非合法になった」を無条件に「相手が原因」と断定しないための
//   安全側の既定値。捕獲・王手放置・ピンのいずれとも確実に言えない場合は、必ず
//   unknownに倒す(人間承認済み方針)。
//
// 【今回追加した2分類の判定範囲について(安全側の制限、重要)】
// candidate_move_illegal_due_to_check・candidate_piece_pinnedは、いずれも
// 「移動先マスが現在空いている(相手駒の捕獲でも自駒の占有でもない)」場合のみを
// 対象とする。移動先が相手駒の捕獲を伴う場合、捕獲によって新たな利きが生じる
// (discovered attack)可能性等があり、shogiopsのsquareAttackers(occupied)の
// 引数を捕獲後の状態に置き換えるような追加の考慮が必要になる。今回はそこまでの
// 判定は行わず、断定できないケースとして安全にunknownへ倒す(意図的な保守的制限)。
//
// 【Unit1の既知課題との関係(修正済み)】
// 複数の候補手が同一targetSquareを狙うケースでは、ユーザーがそのうち1つを
// 指しただけで、相手の着手と無関係に残りの候補(兄弟候補)が非合法になり得る
// (detectPlanChangeの既知課題、fix: prevent sibling candidate false positiveで
// detectPlanChange側は修正済み)。本モジュールのremaining計算も、同じ移動先マスを
// 持つ兄弟候補を除外するよう合わせてある(detectPlanChangeがtrueを返す時点で、
// 兄弟候補が実際にremainingへ紛れ込む場面は無い設計上の不変条件があるため、
// この対応自体は現状の挙動を変えないが、将来pathPlanner.tsの前提が変わった場合の
// 保険として、detectPlanChangeと同じ判定基準に揃えておく)。
//
// 【今回も実装しないこと(承認済み)】
// target_square_occupied_by_own_piece・エンジン評価値・cp値・MultiPV順位・
// LLMによる理由判定はいずれも実装しない。独自の利き判定アルゴリズムは作らず、
// shogiopsの既存公開API(squareAttackers/ctx().blockers)のみを使う。
// detectPlanChange自体(planChangeDetector.ts)も変更しない。

import { isDrop, opposite, parseUsi } from "shogiops/util";
import { parsePosition } from "../rules/sfenPosition.js";
import type { PlanSnapshot } from "./planChangeDetector.js";

export type PlanChangeReason =
  | "candidate_piece_captured"
  | "candidate_move_illegal_due_to_check"
  | "candidate_piece_pinned"
  | "unknown";

/**
 * candidateUsiが、playedMoveUsiと同じ移動先マス(to)または同じ移動元マス(from)を持つ
 * 「兄弟候補」かどうかを判定する。planChangeDetector.ts の isSiblingCandidate と
 * 同じ判定基準を、同じ理由(両者が同じremainingを見るため)でここでも独立に適用する
 * (移動元による判定を加えた理由はplanChangeDetector.tsのファイル冒頭コメント参照。
 * Phase6 Unit1でroutePlanner.tsが準備手を候補にするようになったことへの対応)。
 * いずれかのパースに失敗した場合は安全側に倒し、兄弟候補とは判定しない。
 */
function isSiblingCandidate(candidateUsi: string, playedMoveUsi: string): boolean {
  const playedMove = parseUsi(playedMoveUsi);
  if (!playedMove) return false;
  const candidateMove = parseUsi(candidateUsi);
  if (!candidateMove) return false;
  if (candidateMove.to === playedMove.to) return true;
  if (isDrop(candidateMove) || isDrop(playedMove)) return false;
  return candidateMove.from === playedMove.from;
}

/**
 * detectPlanChangeがtrueを返した場合にのみ呼び出すことを想定する
 * (呼び出し元がplanChanged===trueを確認済みであることが前提。falseの場合の
 * 呼び出しは想定していない)。
 *
 * 純粋関数(決定的)。エンジン・LLMには一切依存しない。shogiopsの既存公開API
 * (squareAttackers/ctx().blockers)のみを使い、独自の利き判定・評価は行わない。
 */
export function classifyPlanChangeReason(
  previous: PlanSnapshot,
  playedMoveUsi: string,
  afterSfen: string,
): PlanChangeReason {
  const remaining = previous.candidateMoveUsis.filter(
    (usi) => usi !== playedMoveUsi && !isSiblingCandidate(usi, playedMoveUsi),
  );
  const pos = parsePosition(afterSfen);
  const selfColor = pos.turn;

  // 1. 捕獲判定(既存、最優先)。
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

  // 2. 王手放置・ピン判定(今回追加)。捕獲されていない駒についてのみ判定する。
  const opponentColor = opposite(selfColor);
  const blockers = pos.ctx().blockers;
  for (const usi of remaining) {
    const move = parseUsi(usi);
    if (!move || isDrop(move)) continue; // ドロップは対象外(unknown側、安全側の制限)。

    const occupant = pos.board.get(move.from);
    if (!occupant || occupant.color !== selfColor) continue; // 1.で既に判定済みのはず(安全側の確認)。

    // 移動先が空いている場合のみを対象とする(捕獲・自駒占有を伴う場合は
    // discovered attack等の追加考慮が必要になるため、安全側でunknownに倒す)。
    if (pos.board.get(move.to)) continue;

    if (occupant.role === "king") {
      if (pos.squareAttackers(move.to, opponentColor, pos.board.occupied).nonEmpty()) {
        return "candidate_move_illegal_due_to_check";
      }
    } else if (blockers.has(move.from)) {
      return "candidate_piece_pinned";
    }
  }

  return "unknown";
}
