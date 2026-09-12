// STEP U6-M: エンジンの読み筋(USIの指し手の列)を再生して、解説の材料 1〜12 を数える。
// 計画は docs/STEP_U6-M_PLAN_2026-09-13.md、設計は docs/DESIGN_REVIEW_2026-09-13.md 4.。
//
// 【このモジュールがやること】
// 読み筋を root 局面から1手ずつ再生し、「何手目に何が起きたか」だけを数える。
// 同じ入力に対して常に同じ結果を返す(決定的な純粋関数)。
//
// 【このモジュールが絶対にやらないこと】
// - エンジンを呼ばない。読み筋は引数で受け取る(計画 3.1)。
//   2026-09-13 の観測で、同じ局面・同じノード数でも別々の探索は別の読み筋を返しうる
//   ことが分かっている(記録に載った engineReference と③が使ったそれが別物だった行が3行)。
//   **探索の内部状態の違いは、境目の数cpではなく読み筋そのものを変えうる。**
//   そのため本モジュールは「どの読み筋を渡されたか」だけに依存させ、同一性の問題は
//   読み筋を記録に載せる側(U6-L)に閉じ込める。
// - LLMを使わない(CLAUDE.mdルール5)。将棋の事実判断はすべてルールエンジンに委ねる。
// - 「有利」「不利」「損」「得」「互角」等の評価語を持たない。**駒の価値表を作らない。**
//   **取った枚数の差引き(スカラー)も作らない**(analysis/captureSummary.ts 冒頭の
//   人間承認済みの制約。設計文書 4.0 で材料3の定義がこれに合わせて訂正された)。
// - 材料の値から「仕掛ける/攻めてくる」へ写さない(設計書 4.1 は判断的知識。計画 2.2)。
// - 画面・APIへ出さない。本モジュールはどこからも import されていない(計画 4.)。
//
// 【「無い」の扱い ― このモジュールの最重要の約束】
// 出来事の材料は boolean ではなく「起きた ply」か null で表す。null は
// **「この読み筋の中では起きなかった」であって「起きない」ではない。**
// 読み筋が短ければ、起きるはずのことも見えない。そのため戻り値は常に usablePlies を持ち、
// **null と usablePlies の両方を見なければ「無い」と言えない**形にしてある。
// null を「無い」と読み替えるのは文を組み立てる段(設計案 (え))の責任であり、ここでは行わない。

import { attacks } from "shogiops/attacks";
import { SquareSet } from "shogiops/square-set";
import type { Color, Role, Square } from "shogiops/types";
import { isDrop, opposite, parseSquareName, parseUsi, squareRank } from "shogiops/util";
import { applyMove } from "../rules/applyMove.js";
import { isLegalMove } from "../rules/legalMoves.js";
import { listAttackedPieces } from "../rules/attackedPieces.js";
import { isInCheck } from "../rules/gameStatus.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { normalizeRole } from "./pieceThreatDetector.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";

/**
 * 材料の定義のうち、**判定結果を変えるもの**(判断的知識。CLAUDE.mdルール4)。
 *
 * **既定値を置かない。** 呼び出し側が必ず選ぶ(`?` を付けないことで型が強制する)。
 * 規約で「気をつけろ」と書くのではなく、気をつけなくても済む形にしてある
 * (docs/STEP_UNIT6_PLAN_2026-09-12.md 13.11 の一般則)。
 *
 * 2026-09-13 時点で司令塔が承認したのは**この構造**であって、どの値を選ぶかは未確定である
 * (計画 7.1 の H-2)。選択肢が今1つしかない軸も、既定値を作らないために欄を残してある。
 */
export interface PvMaterialRules {
  /**
   * 材料2「駒がぶつかる」の定義。
   * - `capture_available`: 手番側に「相手の駒がある升へ動く合法手」が存在する最初の局面
   * - `mutual_attack`: どちらかの駒(玉を除く)が相手の利きに入っている最初の局面
   */
  contact: "capture_available" | "mutual_attack";
  /** 材料5「玉の周り」の定義。`eight_neighbors` = 玉の8近傍。 */
  kingNeighborhood: "eight_neighbors";
  /** 材料11「上がる/下がる」の定義。`rank_delta` = 段の増減(手番の向きで符号を合わせる)。 */
  advance: "rank_delta";
  /** 材料12「利き」の定義。`sliding_attack_count` = 飛角香(成含む)の利き升数の合計。 */
  reach: "sliding_attack_count";
}

/** 材料12で数える「線で利く駒」。成香・成銀等は金と同じ動きなので含めない。 */
const SLIDING_ROLES: Role[] = ["rook", "bishop", "lance", "dragon", "horse"];

/**
 * 実際に盤上に存在する81マスの集合。
 *
 * shogiopsのattacks()は、盤の内部表現(1段=16マス幅)の都合上、盤の外にあたるマスを
 * 含んだ利きを返す。本モジュールで実測した例(空の盤・先手):
 * - 9九の角 → size() は 29 を返す(実際の利きは8マス)。10j・16b・2p 等を含む
 * - 5五の飛 → size() は 23 を返す(実際は16マス)。16e 等を含む
 *
 * **線で利く駒だけの問題ではない。** 玉も隅では盤外を返す(9九の玉は素の size() が 8、
 * 交差後は 3)。ただし countKingNeighbors は最後に「自分の駒」と交差させており、
 * **盤外の升には駒が置けない**ため数には出ない(あちらの交差は現状では冗長である)。
 * **将来 空き升を数える形に変えるなら、あちらの交差が効き始める。**
 * いま実際に数が狂うのは材料12(利きの升数をそのまま数える)であり、
 * **素の size() を信じると線で利く駒だけが静かに過大になる。**
 *
 * **同じ集合が analysis/routePlanner.ts にもある**(あちらは経路探索で同じ罠を踏むため)。
 * あちらは module-local で export されておらず、本STEPは既存ファイルを変更しない方針の
 * ため、ここでは同じ作り方で持つ。**共通化は既存ファイルに触るので別STEPの判断とする。**
 *
 * 盤の範囲は docs/DATA_MODEL.md の座標表記の規約(筋1〜9・段a〜i)そのままで、
 * 段の内部的な幅などの実装詳細には依存しない形で組み立てる(routePlanner.ts と同じ)。
 */
const BOARD_SQUARES: SquareSet = (() => {
  let squares = SquareSet.empty();
  for (const file of "123456789") {
    for (const rank of "abcdefghi") {
      const square = parseSquareName(`${file}${rank}`);
      if (square !== undefined) squares = squares.with(square);
    }
  }
  return squares;
})();

/** 起きた手の位置と、どちらが指したか。`byUs` は root 局面の手番から見た「こちら」。 */
export interface PvEventRef {
  /** 読み筋の何手目か(`pv[0]` を1とする) */
  ply: number;
  /** root 局面の手番(= `pv[0]` を指す側)が指した手なら true */
  byUs: boolean;
}

export interface PvCaptureRef extends PvEventRef {
  /** 取られた駒の種類。成駒は元の駒種に正規化済み(K-1 と同じ基準) */
  role: Role;
}

export interface PvRoleCounts {
  /** root 局面の手番側 */
  us: Map<Role, number>;
  /** その相手 */
  opponent: Map<Role, number>;
}

export interface PvDirectionCounts {
  /** 前へ出た手の数 */
  up: number;
  /** 後ろへ引いた手の数 */
  down: number;
  /** 横へ動いた手の数 */
  side: number;
}

export interface PvMaterials {
  /** 材料1: 最初に駒を取った手。打つ手は捕獲に数えない */
  firstCapture: PvCaptureRef | null;
  /**
   * 材料2: 駒が最初にぶつかった ply(定義は rules.contact)。
   *
   * **`0` と `null` は別物である。**
   * - `0` = **root 局面で既にぶつかっている**(1手目より前。読み筋を1手も進めなくても接触がある)
   * - `null` = この読み筋の中では一度もぶつからなかった
   *
   * **`0` は falsy なので、`if (firstContactPly)` と書くと `0` が `null` と同じ扱いになり、
   * 「既にぶつかっている」が「起きなかった」に化ける。** 下流では必ず `=== null` で判定すること
   * (「無い」の扱いについては冒頭の約束を参照)。
   */
  firstContactPly: number | null;
  /**
   * 材料3: 読み筋の中でそれぞれが取った駒の、駒種ごとの枚数。
   * **差引きの合計も駒の価値も持たない**(captureSummary.ts の制約)。
   */
  capturedRoles: PvRoleCounts;
  /**
   * 材料4: 持ち駒の正味の増減(取った駒 − 打った駒)。材料3とは別の量である。
   * 取って打てば持ち駒は戻るため、材料3から復元できない(計画 7.1 の H-4)。
   */
  handDelta: PvRoleCounts;
  /** 材料5: 玉の8近傍にある自分の駒の枚数の、root と末端の差(負なら減った) */
  kingNeighborDelta: { us: number; opponent: number };
  /** 材料6: 最初に王手がかかった手 */
  firstCheck: PvEventRef | null;
  /** 材料7: 最初の成り */
  firstPromotion: (PvEventRef & { role: Role }) | null;
  /** 材料8: 双方が角を1枚ずつ取り終えた ply(角交換が成立した瞬間) */
  bishopExchangePly: number | null;
  /** 材料9: 最初に駒を打った手 */
  firstDrop: (PvEventRef & { role: Role }) | null;
  /** 材料10: 玉が動いた手の ply の並び(昇順) */
  kingMovePlies: { us: number[]; opponent: number[] };
  /** 材料11: 前後横それぞれへ動いた手の数。打つ手は数えない(移動元が無いため) */
  advanceRetreat: { us: PvDirectionCounts; opponent: PvDirectionCounts };
  /** 材料12: 線で利く駒の利き升数の合計の、root と末端の差 */
  slidingReachDelta: { us: number; opponent: number };
}

export type PvMaterialsResult =
  | {
      kind: "insufficient";
      /** 渡された読み筋の長さ */
      pvLength: number;
      /** 実際に再生できた手数 */
      usablePlies: number;
      reason: "pv_too_short";
    }
  | {
      kind: "measured";
      pvLength: number;
      usablePlies: number;
      /** 非合法手で打ち切った位置(1始まり)。最後まで再生できたなら null */
      truncatedAtPly: number | null;
      materials: PvMaterials;
    };

/** 再生の1手ぶん。判定に必要な「着手前の局面」と「着手後の局面」を両方持つ。 */
interface ReplayStep {
  ply: number;
  color: Color;
  byUs: boolean;
  moveUsi: string;
  beforeSfen: string;
  afterSfen: string;
}

function increment(counts: Map<Role, number>, role: Role): void {
  counts.set(role, (counts.get(role) ?? 0) + 1);
}

function decrement(counts: Map<Role, number>, role: Role): void {
  const next = (counts.get(role) ?? 0) - 1;
  if (next === 0) counts.delete(role);
  else counts.set(role, next);
}

/**
 * その局面で、手番側に「相手の駒がある升へ動く合法手」があるか。
 * 合法性の判定は shogiops の isLegal にそのまま委ねる(独自のルールを持たない)。
 */
function hasCaptureAvailable(sfen: string): boolean {
  const pos = parsePosition(sfen);
  const ctx = pos.ctx();
  const theirs = pos.board.color(opposite(pos.turn));
  for (const [from, toSquares] of pos.allMoveDests(ctx)) {
    for (const to of toSquares.intersect(theirs)) {
      if (pos.isLegal({ from, to, promotion: false }, ctx)) return true;
      if (pos.isLegal({ from, to, promotion: true }, ctx)) return true;
    }
  }
  return false;
}

/** その局面で、どちらかの駒(玉を除く)が相手の利きに入っているか。 */
function hasMutualAttack(sfen: string): boolean {
  return listAttackedPieces(sfen, "sente").length > 0 || listAttackedPieces(sfen, "gote").length > 0;
}

/**
 * 規則の網羅性を型で守るための番人。
 *
 * **必須引数にするだけでは足りない**(2026-09-13 の監査と司令塔の決定)。
 * 受け取った値を三項や if で読むと、未知の値が**静かに既定へ落ちる**か
 * **静かにゼロになる**。この関数を default に置くと、選択肢が増えたときに
 * **使っていない箇所がコンパイルエラーになる。** 入口を型で縛り、出口も型で縛る。
 */
function assertNeverRule(value: never): never {
  throw new Error(`未知の規則です: ${JSON.stringify(value)}`);
}

function isContact(sfen: string, rule: PvMaterialRules["contact"]): boolean {
  switch (rule) {
    case "capture_available":
      return hasCaptureAvailable(sfen);
    case "mutual_attack":
      return hasMutualAttack(sfen);
    default:
      return assertNeverRule(rule);
  }
}

/** 玉の8近傍にある、その色自身の駒の枚数。玉が居ない局面(詰将棋用の盤等)では0。 */
function countKingNeighbors(
  sfen: string,
  color: Color,
  rule: PvMaterialRules["kingNeighborhood"],
): number {
  switch (rule) {
    case "eight_neighbors": {
      const pos = parsePosition(sfen);
      const kingSquare: Square | undefined = pos.board.pieces(color, "king").first();
      if (kingSquare === undefined) return 0;
      const neighborhood = attacks({ role: "king", color }, kingSquare, pos.board.occupied).intersect(
        BOARD_SQUARES,
      );
      return neighborhood.intersect(pos.board.color(color)).size();
    }
    default:
      return assertNeverRule(rule);
  }
}

/** 線で利く駒(飛角香・竜馬)の利き升数の合計。 */
function countSlidingReach(sfen: string, color: Color, rule: PvMaterialRules["reach"]): number {
  switch (rule) {
    case "sliding_attack_count": {
      const pos = parsePosition(sfen);
      let total = 0;
      for (const role of SLIDING_ROLES) {
        for (const square of pos.board.pieces(color, role)) {
          total += attacks({ role, color }, square, pos.board.occupied).intersect(BOARD_SQUARES).size();
        }
      }
      return total;
    }
    default:
      return assertNeverRule(rule);
  }
}

/**
 * 前へ出たか後ろへ引いたか。
 * shogiops の段は a=0 … i=8 であり、先手は段が減る向きが前である
 * (7g(段6) → 7f(段5))。後手はその逆。
 */
function classifyDirection(color: Color, from: Square, to: Square): keyof PvDirectionCounts {
  const rankFrom = squareRank(from);
  const rankTo = squareRank(to);
  const forward = color === "sente" ? rankFrom - rankTo : rankTo - rankFrom;
  if (forward > 0) return "up";
  if (forward < 0) return "down";
  return "side";
}

/**
 * 読み筋を root 局面から再生する。**非合法手で例外を投げない。**
 *
 * replayMoveHistory(analysis/moveHistory.ts)は非合法手で例外を投げるが、あれは
 * **ユーザーが実際に指した履歴**を扱うものなので正しい。読み筋はエンジンの予想にすぎず、
 * 古い局面のものが混ざりうるため、同じ扱いにはしない(計画 1.3)。
 * 打ち切った位置は truncatedAtPly として呼び出し側へ返す。
 */
function replayPv(rootSfen: string, pv: string[], us: Color): { steps: ReplayStep[]; truncatedAtPly: number | null } {
  const steps: ReplayStep[] = [];
  let sfen = rootSfen;

  for (const [index, moveUsi] of pv.entries()) {
    if (!isLegalMove(sfen, moveUsi)) {
      return { steps, truncatedAtPly: index + 1 };
    }
    const color = parsePosition(sfen).turn;
    const afterSfen = applyMove(sfen, moveUsi);
    steps.push({
      ply: index + 1,
      color,
      byUs: color === us,
      moveUsi,
      beforeSfen: sfen,
      afterSfen,
    });
    sfen = afterSfen;
  }

  return { steps, truncatedAtPly: null };
}

/**
 * 読み筋から材料 1〜12 を数える。**決定的な純粋関数**(エンジン・LLMに依存しない)。
 *
 * @param rootSfen 読み筋の起点の局面。`pv[0]` はこの局面で指される手である
 * @param pv USI形式の指し手の列(エンジンの読み筋)
 * @param rules 判断的知識にあたる定義。**既定値なし。呼び出し側が必ず選ぶ**
 * @param minPlies これ未満の手数しか再生できなければ材料を1つも立てない。
 *   **既定値なし。** 閾値は判断的知識であり、2026-09-13 時点で確定していない
 *   (計画 7.1 の H-1。提案値は4だが、U6-L が読み筋の長さの分布を出してから確定させる)。
 *   **そのためこのモジュールの中に具体的な数を書かない。**
 */
export function computePvMaterials(
  rootSfen: string,
  pv: string[],
  rules: PvMaterialRules,
  minPlies: number,
): PvMaterialsResult {
  const us = parsePosition(rootSfen).turn;
  const them = opposite(us);
  const { steps, truncatedAtPly } = replayPv(rootSfen, pv, us);
  const usablePlies = steps.length;

  if (usablePlies < minPlies) {
    return { kind: "insufficient", pvLength: pv.length, usablePlies, reason: "pv_too_short" };
  }

  const capturedRoles: PvRoleCounts = { us: new Map(), opponent: new Map() };
  const handDelta: PvRoleCounts = { us: new Map(), opponent: new Map() };
  const kingMovePlies = { us: [] as number[], opponent: [] as number[] };
  const advanceRetreat = {
    us: { up: 0, down: 0, side: 0 },
    opponent: { up: 0, down: 0, side: 0 },
  };

  let firstCapture: PvCaptureRef | null = null;
  let firstContactPly: number | null = null;
  let firstCheck: PvEventRef | null = null;
  let firstPromotion: (PvEventRef & { role: Role }) | null = null;
  let firstDrop: (PvEventRef & { role: Role }) | null = null;
  let bishopExchangePly: number | null = null;
  let usTookBishop = false;
  let themTookBishop = false;

  // 材料2は「着手前の局面」で判定する。root 局面(まだ1手も指していない状態)から見る。
  if (isContact(rootSfen, rules.contact)) firstContactPly = 0;

  for (const step of steps) {
    const side = step.byUs ? "us" : "opponent";
    const move = parseUsi(step.moveUsi);
    // isLegalMove を通っているので move は必ず解釈できる。推測はしない。
    if (!move) continue;

    const before = parsePosition(step.beforeSfen);

    // 材料1・3・4・8: 捕獲(着手前の局面で移動先に相手の駒がある。打つ手は対象外)
    if (!isDrop(move)) {
      const target = before.board.get(move.to);
      if (target && target.color !== step.color) {
        const role = normalizeRole(target.role);
        increment(capturedRoles[side], role);
        increment(handDelta[side], role);
        if (firstCapture === null) {
          firstCapture = { ply: step.ply, byUs: step.byUs, role };
        }
        if (role === "bishop") {
          if (step.byUs) usTookBishop = true;
          else themTookBishop = true;
          if (bishopExchangePly === null && usTookBishop && themTookBishop) {
            bishopExchangePly = step.ply;
          }
        }
      }

      // 材料7: 成り
      if (move.promotion === true && firstPromotion === null) {
        const moved = before.board.get(move.from);
        if (moved) {
          firstPromotion = { ply: step.ply, byUs: step.byUs, role: moved.role };
        }
      }

      // 材料10: 玉が動いた手
      if (before.board.get(move.from)?.role === "king") {
        kingMovePlies[side].push(step.ply);
      }

      // 材料11: 前後横
      switch (rules.advance) {
        case "rank_delta":
          advanceRetreat[side][classifyDirection(step.color, move.from, move.to)] += 1;
          break;
        default:
          assertNeverRule(rules.advance);
      }
    } else {
      // 材料9: 打つ手。材料4では持ち駒が減る。
      if (firstDrop === null) {
        firstDrop = { ply: step.ply, byUs: step.byUs, role: move.role };
      }
      decrement(handDelta[side], move.role);
    }

    // 材料6: 王手(指した後の局面で、相手の玉に王手がかかっているか)
    if (firstCheck === null && isInCheck(step.afterSfen, opposite(step.color))) {
      firstCheck = { ply: step.ply, byUs: step.byUs };
    }

    // 材料2: ぶつかった最初の局面
    if (firstContactPly === null && isContact(step.afterSfen, rules.contact)) {
      firstContactPly = step.ply;
    }
  }

  // steps が空になりうるのは minPlies が0のときだけ。その場合の「末尾」は root 局面である。
  const finalSfen = steps[steps.length - 1]?.afterSfen ?? rootSfen;

  return {
    kind: "measured",
    pvLength: pv.length,
    usablePlies,
    truncatedAtPly,
    materials: {
      firstCapture,
      firstContactPly,
      capturedRoles,
      handDelta,
      kingNeighborDelta: {
        us:
          countKingNeighbors(finalSfen, us, rules.kingNeighborhood) -
          countKingNeighbors(rootSfen, us, rules.kingNeighborhood),
        opponent:
          countKingNeighbors(finalSfen, them, rules.kingNeighborhood) -
          countKingNeighbors(rootSfen, them, rules.kingNeighborhood),
      },
      firstCheck,
      firstPromotion,
      bishopExchangePly,
      firstDrop,
      kingMovePlies,
      advanceRetreat,
      slidingReachDelta: {
        us: countSlidingReach(finalSfen, us, rules.reach) - countSlidingReach(rootSfen, us, rules.reach),
        opponent:
          countSlidingReach(finalSfen, them, rules.reach) - countSlidingReach(rootSfen, them, rules.reach),
      },
    },
  };
}
