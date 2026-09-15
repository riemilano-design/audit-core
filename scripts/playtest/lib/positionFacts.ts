// STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §1・§2)。局面 1 つから、両方の玉の区域(玉の升と、盤の中の 8 近傍)に
// 利きが届く駒の枚数と升の数を数える純粋関数(M-1〜M-3)。全ての手の組(D4)にもそのまま当てられる形にしてある。
//
// 【このファイルがやること】
// - 盤上の**玉以外の**駒 1 枚ずつに shogiops の attacks(piece, square, occupied)を当て、区域と交わらせて数える
//   (線の駒は occupied で止まり、止めた駒の升は色を問わず利きに含む ― 計画 E-1。利きは手番に依らない)
// - 区域の升の数も返す(端・隅で分母が変わる。kingSurroundings.squares は玉の升を含まないので 1 違う)
// - 2 つの局面の数の差(Failure Event の pvMinusActual 用。玉がどちらかの局面で無い側は null)
//
// 【このファイルが絶対にやらないこと】
// - 玉自身の利きを数えること(計画 Q-7。pos.squareAttackers は玉の利きを含むので使わない ― E-1・R-2)。持ち駒を数えること
// - ピン・取り返し・守りを見ること(幾何だけ。rules/attackedPieces.ts と同じ方針)
// - 評価語や「攻め」「守り」の役割の語を欄に入れること(計画 Q-8)。閾値を置くこと
// - 規則の既定値を置くこと(PvMaterialRules と同じく呼び出し側が選ぶ)。玉の無い側を 0 で埋めること(null にする)
//
// 【判断的知識】区域の形(玉の升 + 盤の中の 8 近傍)と、玉自身の利きを数えないことは人間の承認済み(2026-09-15、2fe81c3)。
// 持ち駒を数えない・「届く」駒で数える・升数で数える、は計画の推奨どおりの仮置き(draft。結果の表と一緒に人間に確認する ― 計画 §1・Q-2)

import { attacks } from "shogiops/attacks";
import { SquareSet } from "shogiops/square-set";
import type { Color } from "shogiops/types";
import type { Position } from "shogiops/variant/position";
import { BOARD_SQUARES } from "../../../apps/server/src/rules/boardSquares.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";

/**
 * 数え方の規則(計画 §2)。**選べる値は今 1 つずつ**だが、既定値を作らないために欄を残す(apps/server/src/analysis/pvMaterials.ts の PvMaterialRules と同じ形)。
 */
export interface PositionFactsRules {
  /** 区域の形。`king_and_eight_neighbors` = 玉の升と、盤の中の 8 近傍(中央 9・端 6・隅 4) */
  zone: "king_and_eight_neighbors";
  /** 利きを当てる駒。`non_king_pieces` = 盤上の玉以外の駒(玉自身の利きと持ち駒は数えない) */
  reach: "non_king_pieces";
  /** 区域の升の数え方。`squares` = 利きが届く升の数(1 升に何枚届いても 1) */
  control: "squares";
}

/** 先手の駒 / 後手の駒ごとの数 */
export interface ZoneCounts {
  bySente: number;
  byGote: number;
}

/** 両方の玉の区域の数。`ownKingZone` = 先手玉(記録は本人 = 先手)の区域、`opponentKingZone` = 後手玉の区域。玉が盤上に無い側は 3 つの欄とも null */
export interface PositionFacts {
  /** 区域の升の数(9・6・4) */
  zoneSquares: { ownKingZone: number | null; opponentKingZone: number | null };
  /** M-1・M-2: 区域の升に利きが 1 升以上届く駒(玉を除く)の枚数 */
  zonePieces: { ownKingZone: ZoneCounts | null; opponentKingZone: ZoneCounts | null };
  /** M-3: 区域の升のうち、利き(玉を除く駒)が届く升の数 */
  zoneControl: { ownKingZone: ZoneCounts | null; opponentKingZone: ZoneCounts | null };
}

/** 2 つの局面の `zonePieces`・`zoneControl` の差。玉がどちらかの局面で無い側は null */
export interface PositionFactsDiff {
  zonePieces: { ownKingZone: ZoneCounts | null; opponentKingZone: ZoneCounts | null };
  zoneControl: { ownKingZone: ZoneCounts | null; opponentKingZone: ZoneCounts | null };
}

function assertNeverRule(value: never): never {
  throw new Error(`未知の規則です: ${JSON.stringify(value)}`);
}

/** その色の玉の区域。玉が盤上に無ければ null */
function zoneOf(pos: Position, color: Color, rule: PositionFactsRules["zone"]): SquareSet | null {
  switch (rule) {
    case "king_and_eight_neighbors": {
      const king = pos.board.pieces(color, "king").first();
      if (king === undefined) return null;
      // 玉の形の利きは 8 近傍そのもの(盤の外の升は除く)。区域は玉の升を足したもの
      return attacks({ role: "king", color }, king, SquareSet.empty()).intersect(BOARD_SQUARES).with(king);
    }
    default:
      return assertNeverRule(rule);
  }
}

/** その色の、利きを当てる駒 1 枚ずつの利きの升 */
function reachesOf(pos: Position, color: Color, rule: PositionFactsRules["reach"]): SquareSet[] {
  switch (rule) {
    case "non_king_pieces": {
      const reaches: SquareSet[] = [];
      for (const square of pos.board.color(color)) {
        const piece = pos.board.get(square);
        if (piece === undefined || piece.role === "king") continue;
        reaches.push(attacks(piece, square, pos.board.occupied));
      }
      return reaches;
    }
    default:
      return assertNeverRule(rule);
  }
}

function controlOf(zone: SquareSet, reaches: readonly SquareSet[], rule: PositionFactsRules["control"]): number {
  switch (rule) {
    case "squares":
      return reaches.reduce((reached, reach) => reached.union(reach.intersect(zone)), SquareSet.empty()).size();
    default:
      return assertNeverRule(rule);
  }
}

export function positionFactsOf(sfen: string, rules: PositionFactsRules): PositionFacts {
  const pos = parsePosition(sfen);
  const reaches = { sente: reachesOf(pos, "sente", rules.reach), gote: reachesOf(pos, "gote", rules.reach) };
  const sideOf = (color: Color) => {
    const zone = zoneOf(pos, color, rules.zone);
    if (zone === null) return null;
    const pieces = (list: readonly SquareSet[]) => list.filter((reach) => reach.intersects(zone)).length;
    return {
      squares: zone.size(),
      pieces: { bySente: pieces(reaches.sente), byGote: pieces(reaches.gote) },
      control: { bySente: controlOf(zone, reaches.sente, rules.control), byGote: controlOf(zone, reaches.gote, rules.control) },
    };
  };
  const own = sideOf("sente");
  const opponent = sideOf("gote");
  return {
    zoneSquares: { ownKingZone: own === null ? null : own.squares, opponentKingZone: opponent === null ? null : opponent.squares },
    zonePieces: { ownKingZone: own === null ? null : own.pieces, opponentKingZone: opponent === null ? null : opponent.pieces },
    zoneControl: { ownKingZone: own === null ? null : own.control, opponentKingZone: opponent === null ? null : opponent.control },
  };
}

function countsDiff(minuend: ZoneCounts | null, subtrahend: ZoneCounts | null): ZoneCounts | null {
  if (minuend === null || subtrahend === null) return null;
  return { bySente: minuend.bySente - subtrahend.bySente, byGote: minuend.byGote - subtrahend.byGote };
}

/** `minuend − subtrahend`(向きは呼び出し側が名前に書く。Failure Event では読み筋 − 実戦) */
export function positionFactsDiff(minuend: PositionFacts, subtrahend: PositionFacts): PositionFactsDiff {
  return {
    zonePieces: {
      ownKingZone: countsDiff(minuend.zonePieces.ownKingZone, subtrahend.zonePieces.ownKingZone),
      opponentKingZone: countsDiff(minuend.zonePieces.opponentKingZone, subtrahend.zonePieces.opponentKingZone),
    },
    zoneControl: {
      ownKingZone: countsDiff(minuend.zoneControl.ownKingZone, subtrahend.zoneControl.ownKingZone),
      opponentKingZone: countsDiff(minuend.zoneControl.opponentKingZone, subtrahend.zoneControl.opponentKingZone),
    },
  };
}
