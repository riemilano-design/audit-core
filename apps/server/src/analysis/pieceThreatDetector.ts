// rules/attackedPieces.ts が返した「自分の駒に相手の駒の利きが届いている」という
// 幾何上の事実から、STEP 4-3(2026-09-10 人間承認)の対象駒種・並び順だけを
// 機械的に選び・並べる(Phase 7 Unit 4「[0] 今すぐ対処が必要なこと」)。
//
// 【このモジュールがやること】
// - 対象駒種のフィルタ(B-1): 飛・角・金・銀・桂・香のみ。玉(王手で扱う)と歩は除く。
//   成駒(龍・馬・成銀・成桂・成香・と金)は元の駒種に正規化してから判定する
//   (と金は歩として除外)。
// - 並び順(D): 自分の駒(行)を 飛→角→金→銀→桂→香 の固定順、同じ駒種は
//   筋(1〜9)の大きい順で並べる。
// - 1行内の攻め駒の並び順(決定 I-1): 正規化後の駒種で 飛→角→金→銀→桂→香→歩→玉 の
//   固定順、同じ駒種は筋の大きい順。攻め駒には駒種フィルタを適用しない(歩・玉も含む)。
//
// いずれも機械的な順序であり、将棋としての重要度・良し悪しを表すものではない
// (rules/attackedPieces.ts のコメント、および人間承認済みの D・I-1 の注記のとおり)。
//
// 【このモジュールが絶対にやらないこと】
// - 守りの有無・取り返しの可否・駒の価値・「危険」等の評価は一切しない。
// - 候補手の移動先の利きは扱わない(4-2の範囲)。囲い内部の相手駒は扱わない(4-5の範囲)。
// - エンジン・LLMには依存しない(決定的な純粋関数)。

import type { Role } from "shogiops/types";
import type { AttackedPiece } from "../rules/attackedPieces.js";

export interface PieceThreatAttacker {
  /** 攻めている相手の駒があるマス(USI形式)。 */
  square: string;
  /** 攻めている相手の駒の役職(成駒はそのまま。表示側で名前を解決する)。 */
  role: Role;
}

export interface PieceThreatFact {
  /** 自分の駒があるマス(USI形式)。 */
  square: string;
  /** 自分の駒の役職(成駒はそのまま。表示側で名前を解決する)。 */
  role: Role;
  /** このマスへ利きが届いている相手の駒。決定 I-1 の順に並べ済み。1件以上。 */
  attackers: PieceThreatAttacker[];
}

/**
 * B-1 で対象とする自分の駒種(正規化後)。飛・角・金・銀・桂・香のみ。
 * 玉(王手で扱う)と歩は含めない。
 */
const TARGET_ROLES_AFTER_NORMALIZATION: ReadonlySet<Role> = new Set([
  "rook",
  "bishop",
  "gold",
  "silver",
  "knight",
  "lance",
]);

/**
 * 成駒を元の駒種へ正規化する(B-1・I-1 の判定・並び順のためだけに使う内部表)。
 * 表示名は変えない(表示名は analysis/pieceThreatExplanation.ts の別の表が担当する)。
 * ここに無い役職(玉・歩・成駒6種以外の基本駒)はそのまま返す。
 */
function normalizeRole(role: Role): Role {
  switch (role) {
    case "dragon":
      return "rook";
    case "horse":
      return "bishop";
    case "promotedsilver":
      return "silver";
    case "promotedknight":
      return "knight";
    case "promotedlance":
      return "lance";
    case "tokin":
      return "pawn";
    default:
      return role;
  }
}

/** D・I-1で共通の「並び順」を決める駒種の固定順(正規化後)。飛→角→金→銀→桂→香→歩→玉。 */
const ROLE_ORDER: readonly Role[] = ["rook", "bishop", "gold", "silver", "knight", "lance", "pawn", "king"];

function roleOrderIndex(role: Role): number {
  const index = ROLE_ORDER.indexOf(normalizeRole(role));
  // ROLE_ORDERに無い役職(標準将棋のB-1対象・攻め駒として現れ得ない役職)は
  // 並び順を発明せず末尾へ送る。
  return index === -1 ? ROLE_ORDER.length : index;
}

/** USI形式のマス目(例: "8h")から筋(1〜9)を取り出す。解釈できない場合は0を返し末尾扱いにする。 */
function fileOf(usiSquare: string): number {
  const file = Number(usiSquare[0]);
  return Number.isFinite(file) ? file : 0;
}

/**
 * 決定的な並び替え。駒種の固定順を優先し、同じ駒種は筋の大きい順(降順)にする。
 * どちらも機械的な規則であり、将棋としての重要度・良し悪しを表さない。
 */
function byRoleOrderThenFileDescending<T extends { square: string; role: Role }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const roleDiff = roleOrderIndex(a.role) - roleOrderIndex(b.role);
    if (roleDiff !== 0) return roleDiff;
    return fileOf(b.square) - fileOf(a.square);
  });
}

/**
 * rules/attackedPieces.ts が返した幾何上の事実から、B-1 の対象駒種だけを選び、
 * D・I-1 の固定順に並べ替える。新しい判定は一切しない(選ぶ・並べるだけ)。
 *
 * 決定的な純粋関数(同じ入力に対しては常に同じ結果を返す)。
 */
export function detectPieceThreats(attackedPieces: AttackedPiece[]): PieceThreatFact[] {
  const targeted = attackedPieces.filter((piece) => TARGET_ROLES_AFTER_NORMALIZATION.has(normalizeRole(piece.role)));

  const facts: PieceThreatFact[] = targeted.map((piece) => ({
    square: piece.square,
    role: piece.role,
    attackers: byRoleOrderThenFileDescending(piece.attackers),
  }));

  return byRoleOrderThenFileDescending(facts);
}
