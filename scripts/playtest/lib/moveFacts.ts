// STEP D2.6(docs/STEP_D2.6_PLAN_2026-09-17.md §1・§2)。局面で指す手 1 つについての事実(U-1〜U-9)を数える純粋関数。
// counterfactual の実戦の側(本人の手)と読み筋の側(読み筋の 1 手目)に、同じ根で同じように当てる(lib/counterfactual.ts の sequenceFacts)。
//
// 【このファイルがやること】
// - 手の駒種(指す前)・打つ手か・取った駒種(盤の上の駒種のまま ― Q-2)・成ったか(USI の + ― Q-9)・玉の手か
// - 動かす前の升 / 動かした後の升が玉の区域にあるか(区域は lib/positionFacts.ts の kingZoneOf。指す前の升は指す前の盤、後の升は指した後の盤)
// - 動かした駒 1 枚だけの、自玉の区域に利きが届く升の数の「指す前 − 指した後」(Q-6。打つ手の前は 0 ― Q-3。玉の手は null ― Q-4)
// - 「自玉」は手番の側の玉(記録は本人 = 先手に回してあり、根は先手番 ― 計画 E-2)
//
// 【このファイルが絶対にやらないこと】
// - 「攻め・守り・逃げ・受け」などの役割の語や評価語を欄にすること。ほかの駒の線の開閉を数えること(Q-6)
// - 玉の利きを数えること(D2.5 Q-7)。持ち駒の利きを数えること。合法でない手を指すこと(例外にする)
//
// 【判断的知識】区域の形と玉の利きを数えないことは D2.5 の人間承認(2026-09-15)。欄の選び方(Q-1〜Q-9)は司令塔の決定(2026-09-17)。

import { attacks } from "shogiops/attacks";
import type { SquareSet } from "shogiops/square-set";
import type { Piece, Role, Square } from "shogiops/types";
import { isDrop, opposite, parseUsi } from "shogiops/util";
import { isLegalMove } from "../../../apps/server/src/rules/legalMoves.js";
import { parsePosition } from "../../../apps/server/src/rules/sfenPosition.js";
import { kingZoneOf, type PositionFactsRules } from "./positionFacts.js";

/** 本将棋の駒種(盤上の駒種 8 + 成駒 6)。スキーマの列挙と同じ並び */
export const STANDARD_ROLES = ["king", "rook", "bishop", "gold", "silver", "knight", "lance", "pawn", "dragon", "horse", "promotedsilver", "promotedknight", "promotedlance", "tokin"] as const;
export type StandardRole = (typeof STANDARD_ROLES)[number];

export interface UserMoveFacts {
  /** U-1: 動かした駒の、指す前の駒種(打つ手は打った駒種) */
  role: StandardRole;
  /** U-2: 持ち駒を打った手か */
  drop: boolean;
  /** U-3: 取った駒の、取られる前の盤の上の駒種。null = 取っていない */
  capturedRole: StandardRole | null;
  /** U-4: 成った手か(USI の末尾 +) */
  promotion: boolean;
  /** U-5: 玉を動かした手か */
  kingMove: boolean;
  /** U-6: 動かす前の升が指す前の盤の自玉の区域にあるか。null = 打つ手、または指す前の盤に自玉が無い(同じ行の drop で区別できる) */
  fromInOwnKingZone: boolean | null;
  /** U-7: 動かした後の升が指した後の盤の自玉の区域にあるか。null = 指した後の盤に自玉が無い */
  toInOwnKingZone: boolean | null;
  /** U-8: 動かした後の升が指した後の盤の相手玉の区域にあるか。null = 指した後の盤に相手玉が無い */
  toInOpponentKingZone: boolean | null;
  /** U-9: 動かした駒 1 枚の、自玉の区域に利きが届く升の数の「指す前 − 指した後」。null = 玉の手、または指す前か後の盤に自玉が無い(同じ行の kingMove で区別できる) */
  ownKingZoneReachBeforeMinusAfter: number | null;
}

export class MoveFactsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "MoveFactsError";
  }
}

function standardRoleOf(role: Role): StandardRole {
  if (!(STANDARD_ROLES as readonly string[]).includes(role)) throw new MoveFactsError(`本将棋の駒種でない: ${role}`);
  return role as StandardRole;
}

/** 駒 1 枚が、その升から区域の升のうち何升に利くか(占有は渡した盤のもの。線の駒は止めた升を含む ― D2.5 の E-1) */
function reachInZone(piece: Piece, square: Square, occupied: SquareSet, zone: SquareSet): number {
  return attacks(piece, square, occupied).intersect(zone).size();
}

/** `sfen` の局面で `moveUsi` を指したときの事実(計画 §1)。合法でない手・読めない手は例外 */
export function moveFactsOf(sfen: string, moveUsi: string, rules: PositionFactsRules): UserMoveFacts {
  // 利きの規則は D2.5 と同じ値だけを受ける(玉の利きを数えない・升数で数える)。ほかの値は、この関数の数え方と食い違う
  if (rules.reach !== "non_king_pieces" || rules.control !== "squares") throw new MoveFactsError(`この関数が扱わない規則: ${JSON.stringify(rules)}`);
  const move = parseUsi(moveUsi);
  if (move === undefined) throw new MoveFactsError(`USI の手として読めない: ${moveUsi}`);
  if (!isLegalMove(sfen, moveUsi)) throw new MoveFactsError(`合法でない手: ${moveUsi}(局面 ${sfen})`);

  const before = parsePosition(sfen);
  const own = before.turn;
  const after = before.clone();
  after.play(move);

  const drop = isDrop(move);
  const moved: Piece | undefined = drop ? { role: move.role, color: own } : before.board.get(move.from);
  if (moved === undefined) throw new MoveFactsError(`動かす駒が無い: ${moveUsi}`);
  const captured = drop ? undefined : before.board.get(move.to);
  const movedAfter = after.board.get(move.to);
  if (movedAfter === undefined) throw new MoveFactsError(`指した後の升に駒が無い: ${moveUsi}`);

  const ownZoneBefore = kingZoneOf(before, own, rules.zone);
  const ownZoneAfter = kingZoneOf(after, own, rules.zone);
  const opponentZoneAfter = kingZoneOf(after, opposite(own), rules.zone);
  const kingMove = moved.role === "king";

  let reachChange: number | null = null;
  if (!kingMove && ownZoneBefore !== null && ownZoneAfter !== null) {
    const reachBefore = drop ? 0 : reachInZone(moved, move.from, before.board.occupied, ownZoneBefore);
    const reachAfter = reachInZone(movedAfter, move.to, after.board.occupied, ownZoneAfter);
    reachChange = reachBefore - reachAfter;
  }

  return {
    role: standardRoleOf(moved.role),
    drop,
    capturedRole: captured === undefined ? null : standardRoleOf(captured.role),
    promotion: !drop && move.promotion === true,
    kingMove,
    fromInOwnKingZone: drop || ownZoneBefore === null ? null : ownZoneBefore.has(move.from),
    toInOwnKingZone: ownZoneAfter === null ? null : ownZoneAfter.has(move.to),
    toInOpponentKingZone: opponentZoneAfter === null ? null : opponentZoneAfter.has(move.to),
    ownKingZoneReachBeforeMinusAfter: reachChange,
  };
}
