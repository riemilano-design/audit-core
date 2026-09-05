// ShapeFormationResult(shapeFormationAnalyzer.ts) + Shape定義(shapeRepository.ts) +
// 合法手(rules/legalMoves.ts) -> 「選択した形の未達成マスそれぞれへ向かう経路」と、
// 「その経路のうち現在局面で実際に指せる最初の一手」への変換。
// docs/PHASES.md Phase6 Unit1(経路計画)に対応する。
//
// 【なぜこのモジュールが必要か】
// 既存のpathPlanner.ts(Phase2)は「typical_build_order上、最初に見つかった未達成マス1つ」
// について「そのマスへ1手で直接到達できる合法手」だけを候補にする。実測の結果、
// 現在の3形(本美濃・高美濃・銀冠)はいずれもtypical_build_orderの先頭が8h(玉)であり、
// 初期局面では玉が8hまで3手かかる(さらに8hは角の初期位置)ため、序盤のほぼ全域で
// 候補手が1件も出せないことを確認した(docs/PHASES.md Phase5「実対局確認で判明した
// 設計上の限界」)。本モジュールは、複数の未達成マスを同時に扱い、複数手の経路を
// 考えたうえで「今指せる最初の一手」を返すことでこれを解消する。
// pathPlanner.tsは削除も変更もしない(既存の呼び出し・テストはそのまま動く)。
//
// 【このモジュールが絶対にしないこと】
// 「この手が最善」「この手を指すべき」「この手は悪手」「この手が安全」
// 「候補Aより候補Bが優れている」といった評価・順位付けは一切行わない
// (pathPlanner.tsと同じ方針)。エンジンにも一切依存しない。
// エンジンの最善手(bestmove)を経路の候補にすることもしない。ここで返すのは
// あくまで「既存のshapeデータ上、その形の未達成部分へ向かう経路として説明できる合法手」
// の列挙に過ぎず、ユーザーに提示してよいかどうかはCLAUDE.mdルール3番のとおり
// candidateMoveSafetyCheck.tsによる参考評価を経てから呼び出し側が判断する。
//
// 【新しい将棋知識を作らないこと】
// 使うのは (1) data/shapes/*.json のrequired_pieces(駒種とマス、人間レビュー済み)、
// (2) typical_build_order(「典型的な組み方の順序の一例」。唯一の正解手順としては
// 扱わない)、(3) shogiopsが提供する将棋のルールそのもの(attacks/合法手判定)だけである。
// 「この退避先が良い」「この経路が優れている」といった将棋的な価値判断は一切追加しない。
//
// 【経路探索の既知の単純化(意図的)】
// - 盤上の他の駒は静的な障害物として扱う(相手の応手や、他の駒が動くことは考慮しない)。
//   経路は毎手つど再計算される前提であり、「今この瞬間に説明できる経路」に留める。
// - ある駒の経路が、別の必須マスを通過することはあり得る(例: 銀冠で銀が7hを経由する)。
//   これは typical_build_order の順序に従って処理することで自然に解消される場合が多いが、
//   衝突の解決を保証するものではない(毎手の再計算に委ねる)。

import { attacks } from "shogiops/attacks";
import { SquareSet } from "shogiops/square-set";
import type { Color, Role, Square } from "shogiops/types";
import { isDrop, makeSquareName, opposite, parseSquareName, parseUsi } from "shogiops/util";
import { getLegalMoves } from "../rules/legalMoves.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { japaneseToRole, UnknownPieceNameError } from "./pieceMapping.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { getShapes, type ShapeDefinition } from "./shapeRepository.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";

/**
 * 1つの目標マスにつき候補手として採る上限。
 * これは candidateMoveSafetyCheck.ts が候補手1件につきエンジン解析を1回ずつ直列実行する
 * ことによる待ち時間の上限であり、将棋的な良し悪しによる選別ではない。
 * 上限で切る際の順序はUSI昇順という機械的・決定的な規則のみで決める。
 */
export const MAX_CANDIDATES_PER_TARGET = 2;

/** 全体の候補手上限。理由はMAX_CANDIDATES_PER_TARGETと同じ(エンジンコストの上限)。 */
export const MAX_CANDIDATES_TOTAL = 6;

/**
 * 経路・候補手が得られなかった場合の理由。いずれも「エラーで対局を止める」のではなく
 * 「候補手なし」として安全に扱うための分類(pathPlanner.tsと同じ考え方)。
 */
export type RouteUnresolvedReason =
  /** targetShapeIdに対応するShapeFormationResultが見つからない */
  | "shape_result_not_found"
  /** targetShapeIdに対応するShape定義(data/shapes/*.json)が見つからない */
  | "shape_definition_not_found"
  /** side="opponent"のshapeは自分が目指す形にはなり得ないため対象外 */
  | "shape_not_self_side"
  /** 既に完成している形は、これ以上目指す必要がない */
  | "already_completed"
  /** missing_squaresが空(完成していないのに埋めるべきマスがない、データ不整合) */
  | "no_missing_squares"
  /** 現在の局面が自分(side="self"の視点色)の手番ではない */
  | "not_self_turn"
  /** 未達成マスの表記がUSI形式として解釈できない(データ不整合) */
  | "target_square_invalid"
  /** 未達成マスに対応するrequired_piecesのエントリが見つからない(square文字列一致で解決できない) */
  | "piece_mapping_unresolved"
  /** required_pieces.pieceの表記がpieceMapping.tsで未対応(未知の駒種表記) */
  | "unknown_piece_name"
  /** どの未達成マスについても、そこへ向かう経路を持つ自駒が見つからない */
  | "no_route_for_any_square"
  /** 経路は求まったが、現在局面で指せる最初の一手(準備手を含む)が1つも無い */
  | "no_playable_first_move";

/** 経路の最初の一手が指せない理由。指せる場合はnull。 */
export type RouteBlockedReason = "occupied_by_own_piece";

/** 同じ目標マスへ向かう、1つの駒ぶんの経路。 */
export interface ShapeSquareRouteOption {
  /** この目標マスへ向かわせる自駒の、現在の位置(USI形式) */
  fromSquare: string;
  /** 経路(fromSquareからtargetSquareまで、USI形式のマスの並び) */
  routeSquares: string[];
  /** 経路の1手目に相当する、現在局面の合法手(USI形式、昇順) */
  firstMoveUsis: string[];
}

/** 未達成マス1つ分の経路計画。 */
export interface ShapeSquareRoute {
  /** 目標マス(USI形式、data/shapes/*.jsonのrequired_pieces.squareそのまま) */
  targetSquare: string;
  /** 目標マスに置く駒種(日本語表記、data/shapes/*.jsonそのまま) */
  targetPiece: string;
  /** この目標マスへ向かわせる自駒の、現在の位置(USI形式) */
  fromSquare: string;
  /** 経路(fromSquareからtargetSquareまで、USI形式のマスの並び)。要素数は2以上。 */
  routeSquares: string[];
  /** 目標マスまでの残り手数(routeSquares.length - 1)。 */
  remainingSteps: number;
  /** 経路の1手目に相当する、現在局面の合法手(USI形式、昇順)。指せない場合は空配列。 */
  firstMoveUsis: string[];
  /**
   * 同じ目標マスへ、同じ手数で到達できる別の駒の経路(1手目が現在指せるものだけ)。
   * 「7hへは6gの銀でも8gの銀でも1手で行ける」のように、どの駒を使うかが一意に
   * 決まらない場合に、候補をどちらか一方に勝手に絞り込まないためのもの。
   * どちらが良いかという将棋的な判断はしない(どちらも同じ手数、という事実のみ)。
   * 進捗表示にはfromSquare/routeSquares(代表の1件)だけを使い、こちらは候補手の
   * 生成にのみ使う。候補手はそれぞれ自分自身の経路を持つ(説明文が実際の経路と
   * 食い違わないようにするため)。
   */
  alternativeRoutes: ShapeSquareRouteOption[];
  /** 経路上で最初に自分の駒が居るマス(USI形式)。無ければnull。 */
  blockingSquare: string | null;
  /** 1手目が指せない理由。指せる場合・理由が特定できない場合はnull。 */
  blockedReason: RouteBlockedReason | null;
  /**
   * blockedReason==="occupied_by_own_piece"の場合の準備手(blockingSquareの自駒を
   * 動かす合法手、USI昇順)。どこへ動かすのが良いかという将棋的な判断は一切しない
   * (合法手をそのまま機械的に並べるだけ)。
   */
  preparatoryMoveUsis: string[];
}

/**
 * ユーザーに提示する候補手1件。
 * moveUsiを持つため、candidateMoveSafetyCheck.tsのPathPlanCandidateMoveと構造互換
 * (安全確認側の変更なしにそのまま渡せる)。
 */
export interface RouteCandidateMove {
  /** USI形式の指し手(rules/legalMoves.tsが返す合法手のうちの1つ) */
  moveUsi: string;
  /**
   * - "route_step": 目標マスへ向かう経路そのものの1手目
   * - "preparation": 経路を塞いでいる自分の駒をどかすための手
   */
  kind: "route_step" | "preparation";
  /** この手が向かっている(あるいは空けようとしている)目標マス */
  targetSquare: string;
  /** 目標マスに置く駒種(日本語表記) */
  targetPiece: string;
  /** 目標マスまでの経路(説明用) */
  routeSquares: string[];
  /** この手を指した後の、目標マスまでの残り手数。kind==="preparation"の場合はnull。 */
  remainingStepsAfter: number | null;
  /** kind==="preparation"の場合、どのマスを空けるための手か。それ以外はnull。 */
  clearingSquare: string | null;
}

export interface ShapeRoutePlanResult {
  shapeId: string;
  /** 未達成マスごとの経路。typical_build_orderの順に並ぶ。 */
  routes: ShapeSquareRoute[];
  /** 現在局面で実際に指せる候補手(重複除去済み、決定的な順序)。 */
  candidateMoves: RouteCandidateMove[];
  /** candidateMovesが空の場合の理由。1件以上ある場合はnull。 */
  unresolvedReason: RouteUnresolvedReason | null;
}

export interface PlanRoutesOptions {
  shapes?: ShapeDefinition[];
}

/**
 * 実際に盤上に存在する81マスの集合。
 *
 * shogiopsのattacks()は、盤の内部表現(1段=16マス幅)の都合上、盤の外にあたるマスを
 * 含んだ利きを返すことがある(例: 5iの銀の「後ろ斜め」として、九段目より下の6j・4jが
 * 返る)。Positionの合法手生成は内部でこれを盤の範囲に絞っているが、本モジュールは
 * attacks()を直接使うため、自分で盤の外を除外する必要がある
 * (除外しないと「３九→４八→５九→6j→７九→７八」のように、存在しないマスを
 * 通り抜ける経路が作られ、手数も実際より短く出てしまう)。
 *
 * 盤の範囲は docs/DATA_MODEL.md の座標表記の規約(筋1〜9・段a〜i)そのままで、
 * 段の内部的な幅などの実装詳細には依存しない形で組み立てる。
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

function emptyResult(shapeId: string, unresolvedReason: RouteUnresolvedReason): ShapeRoutePlanResult {
  return { shapeId, routes: [], candidateMoves: [], unresolvedReason };
}

type ParsedPosition = ReturnType<typeof parsePosition>;

/**
 * 駒1枚を、盤上の他の駒を静的な障害物とみなしてBFSで動かし、fromからtargetまでの
 * 最短経路(マスの並び)を求める。将棋のルール(どの駒がどこへ動けるか)は
 * shogiopsのattacks()にそのまま委ね、独自の移動規則は一切持たない。
 *
 * passOwnPieces=falseのとき、自分の駒があるマスは通過できない。ただし目標マスだけは
 * 例外として経路の終点に許可する(そこに居る自駒が後で動く可能性があるため。
 * 実際に今その手が指せるかどうかは、合法手との突き合わせ側で判定する)。
 * passOwnPieces=trueのとき、自分の駒は「後でどく」ものとして通過できるものとして扱う
 * (経路を塞いでいる自駒を特定するための2回目の探索で使う)。
 *
 * 同じ入力に対しては常に同じ結果を返す(SquareSetの走査順がマス番号昇順で決定的なため)。
 */
function findRoute(
  pos: ParsedPosition,
  from: Square,
  role: Role,
  target: Square,
  selfColor: Color,
  passOwnPieces: boolean,
): Square[] | null {
  if (from === target) return null;

  const ownSquares = pos.board.color(selfColor).without(from);
  const staticOccupied = passOwnPieces
    ? pos.board.color(opposite(selfColor))
    : pos.board.occupied.without(from);

  const previous = new Map<Square, Square>();
  const visited = new Set<Square>([from]);
  let frontier: Square[] = [from];

  while (frontier.length > 0) {
    const nextFrontier: Square[] = [];
    for (const square of frontier) {
      // 「その駒が今squareに居る」と仮定した利き。走り駒(将来shapeに飛角香が
      // 含まれた場合)でも、attacks()が占有状況を見て正しく扱う。
      for (const to of attacks({ color: selfColor, role }, square, staticOccupied.with(square))) {
        // 盤の外は経路にしない(BOARD_SQUARESのコメント参照)。
        if (!BOARD_SQUARES.has(to)) continue;
        if (visited.has(to)) continue;
        if (!passOwnPieces && ownSquares.has(to) && to !== target) continue;

        visited.add(to);
        previous.set(to, square);

        if (to === target) {
          const route: Square[] = [to];
          let cursor: Square = to;
          while (previous.has(cursor)) {
            cursor = previous.get(cursor)!;
            route.unshift(cursor);
          }
          return route;
        }

        nextFrontier.push(to);
      }
    }
    frontier = nextFrontier;
  }

  return null;
}

interface RouteSearchResult {
  from: Square;
  route: Square[];
}

/**
 * 目標マスへ向かわせられる自駒の経路を、最短のものだけ返す(同じ手数の駒が複数あれば
 * すべて返す。先頭が代表)。
 *
 * - frozenSquares(既にその形の一部として成立しているマス)に居る駒は選ばない
 *   (形を壊す候補手を作らないため)。
 * - assignedSquares(既に別の目標へ代表として割り当てた駒)も選ばない
 *   (同じ駒を複数の目標へ二重に割り当てないため)。
 * - まず自駒を通過できない経路(=今の盤面で実際に通れる道)を探し、見つからない場合に
 *   限り自駒を通過できる「理想の経路」を探す(経路を塞いでいる自駒を特定するため)。
 * - 並び順は経路の短い順、同じ長さならマス名の昇順(どちらが将棋的に良いかは判断しない。
 *   決定的な順序を得るためだけの規則)。
 */
function findBestRoutes(
  pos: ParsedPosition,
  role: Role,
  target: Square,
  selfColor: Color,
  frozenSquares: Set<Square>,
  assignedSquares: Set<Square>,
): RouteSearchResult[] {
  const sources = [...pos.board.role(role).intersect(pos.board.color(selfColor))].filter(
    (square) => !frozenSquares.has(square) && !assignedSquares.has(square) && square !== target,
  );

  for (const passOwnPieces of [false, true]) {
    const found: RouteSearchResult[] = [];
    for (const from of sources) {
      const route = findRoute(pos, from, role, target, selfColor, passOwnPieces);
      if (route) found.push({ from, route });
    }
    if (found.length === 0) continue;

    found.sort(
      (a, b) => a.route.length - b.route.length || makeSquareName(a.from).localeCompare(makeSquareName(b.from)),
    );
    const shortest = found[0]!.route.length;
    return found.filter((r) => r.route.length === shortest);
  }

  return [];
}

/**
 * 経路の1手目(from -> to)に相当する合法手を集める。
 *
 * 成る手は採用しない。成ると駒種が変わり、shapes.required_piecesが指定する駒種を
 * 満たさなくなるため(data/schemas/shapes.schema.jsonの定義からの帰結であり、
 * 将棋的な良し悪しの判断ではない)。
 */
function collectFirstMoveUsis(
  pos: ParsedPosition,
  legalMoves: string[],
  from: Square,
  to: Square,
  role: Role,
  selfColor: Color,
): string[] {
  const result: string[] = [];
  for (const moveUsi of legalMoves) {
    const move = parseUsi(moveUsi);
    if (!move || isDrop(move)) continue;
    if (move.from !== from || move.to !== to) continue;
    if (move.promotion) continue;

    const piece = pos.board.get(move.from);
    if (!piece || piece.color !== selfColor || piece.role !== role) continue;

    result.push(moveUsi);
  }
  return result.sort();
}

/** 経路上(1マス目以降)で最初に自分の駒が居るマスを返す。無ければundefined。 */
function findFirstOwnBlocker(pos: ParsedPosition, route: Square[], selfColor: Color): Square | undefined {
  const ownSquares = pos.board.color(selfColor);
  for (let i = 1; i < route.length; i++) {
    const square = route[i]!;
    if (ownSquares.has(square)) return square;
  }
  return undefined;
}

/**
 * 経路を塞いでいる自駒を動かす合法手(準備手)を集める。
 *
 * どこへ動かすのが良いかという将棋的な評価は一切行わず、合法手をそのまま昇順で返す
 * (呼び出し側は上限件数で機械的に切る)。ただし次の2つだけは機械的な理由で除外する:
 * - 既にその形の一部として成立している駒(frozenSquares)は動かさない
 * - 成る手は採らない(駒種が変わるため。collectFirstMoveUsisと同じ理由)
 */
function collectPreparatoryMoveUsis(
  legalMoves: string[],
  blockingSquare: Square,
  frozenSquares: Set<Square>,
): string[] {
  if (frozenSquares.has(blockingSquare)) return [];

  const result: string[] = [];
  for (const moveUsi of legalMoves) {
    const move = parseUsi(moveUsi);
    if (!move || isDrop(move)) continue;
    if (move.from !== blockingSquare) continue;
    if (move.promotion) continue;
    result.push(moveUsi);
  }
  return result.sort();
}

/**
 * typical_build_orderを「どのマスから埋めていくかのヒント」として、未達成マスを並べ替える。
 * typical_build_orderは唯一の正解手順ではないため、ここでも順序のヒントとしてのみ使い、
 * 「build orderの先頭1マスだけを見る」という扱い(pathPlanner.tsの挙動)はしない。
 * build orderに現れないマスは末尾へ回し、最後はマス名昇順で決定的にする。
 */
function orderMissingSquares(missingSquares: string[], buildOrder: string[]): string[] {
  const indexOf = (square: string): number => {
    const index = buildOrder.indexOf(square);
    return index === -1 ? buildOrder.length : index;
  };
  return [...missingSquares].sort((a, b) => indexOf(a) - indexOf(b) || a.localeCompare(b));
}

/**
 * 選択された形(targetShapeId)について、未達成マスそれぞれへ向かう経路と、
 * 現在局面で実際に指せる最初の一手を求める。
 *
 * 【責務の範囲】
 * - 未達成マスを typical_build_order 順に並べ、それぞれへ向かわせる自駒を割り当てる
 * - 各目標マスへの経路(複数手)を求める
 * - 経路の1手目に相当する合法手を抽出する(無ければ、経路を塞ぐ自駒の準備手を抽出する)
 * - 候補が得られない場合も例外を投げず、unresolvedReasonつきの安全な結果を返す
 *
 * 【対象外】
 * 候補手の安全性評価・最善手判定・エンジンとの突き合わせ・説明生成・API/UI統合は
 * 一切行わない(それぞれ別モジュールの責務)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function planRoutesToShape(
  sfen: string,
  shapeResults: ShapeFormationResult[],
  targetShapeId: string,
  options: PlanRoutesOptions = {},
): ShapeRoutePlanResult {
  const shapeResult = shapeResults.find((r) => r.shapeId === targetShapeId);
  if (!shapeResult) return emptyResult(targetShapeId, "shape_result_not_found");

  // side="opponent"は自分が目指す形にはなり得ないため、誤って候補生成に使わない。
  if (shapeResult.side === "opponent") return emptyResult(targetShapeId, "shape_not_self_side");

  // 既に完成している形は、これ以上「目指す」候補手を出さない。
  if (shapeResult.status === "completed") return emptyResult(targetShapeId, "already_completed");

  if (shapeResult.missingSquares.length === 0) {
    // completedではないのにmissingSquaresが空(データ不整合)。推測せず未解決とする。
    return emptyResult(targetShapeId, "no_missing_squares");
  }

  const shapes = options.shapes ?? getShapes();
  const shapeDefinition = shapes.find((s) => s.id === targetShapeId);
  if (!shapeDefinition) return emptyResult(targetShapeId, "shape_definition_not_found");

  // sfen自体の妥当性チェックはparsePosition/getLegalMoves内部で行われる
  // (不正なSFENに対してはInvalidSfenErrorがそのまま伝播する。呼び出し側の責務)。
  const pos = parsePosition(sfen);
  const selfColor = shapeResult.perspectiveColor;
  if (pos.turn !== selfColor) {
    // 相手の手番の局面では、自分側の形成に向かう手を提示しない(安全なフォールバック)。
    return emptyResult(targetShapeId, "not_self_turn");
  }

  // 既にその形の一部として成立しているマスの駒は、動かすと形が壊れるため凍結する
  // (例: 本美濃囲いで既に6iに居る金を5hへ動かす"6i5h"のような候補を作らない)。
  const frozenSquares = new Set<Square>();
  for (const squareName of shapeResult.matchedSquares) {
    const square = parseSquareName(squareName);
    if (square !== undefined) frozenSquares.add(square);
  }

  const legalMoves = getLegalMoves(sfen);
  const orderedMissing = orderMissingSquares(shapeResult.missingSquares, shapeDefinition.typical_build_order ?? []);

  const routes: ShapeSquareRoute[] = [];
  const assignedSquares = new Set<Square>();
  // 個々の目標マスを処理できなかった理由(routesが1件も作れなかった場合にのみ使う)。
  const skippedReasons: RouteUnresolvedReason[] = [];

  for (const targetSquareName of orderedMissing) {
    const targetSquare = parseSquareName(targetSquareName);
    if (targetSquare === undefined) {
      skippedReasons.push("target_square_invalid");
      continue;
    }

    const requiredPiece = shapeDefinition.required_pieces.find(
      (p) => !p.optional && p.square === targetSquareName,
    );
    if (!requiredPiece) {
      skippedReasons.push("piece_mapping_unresolved");
      continue;
    }

    let role: Role;
    try {
      role = japaneseToRole(requiredPiece.piece);
    } catch (err) {
      if (err instanceof UnknownPieceNameError) {
        skippedReasons.push("unknown_piece_name");
        continue;
      }
      throw err;
    }

    const found = findBestRoutes(pos, role, targetSquare, selfColor, frozenSquares, assignedSquares);
    const primary = found[0];
    if (!primary) {
      skippedReasons.push("no_route_for_any_square");
      continue;
    }
    // 代表の1枚だけを「割り当て済み」にする(同じ駒が別の目標の代表になるのを防ぐ)。
    assignedSquares.add(primary.from);

    const toOption = (result: RouteSearchResult): ShapeSquareRouteOption => ({
      fromSquare: makeSquareName(result.from),
      routeSquares: result.route.map((square) => makeSquareName(square)),
      firstMoveUsis: collectFirstMoveUsis(
        pos,
        legalMoves,
        result.route[0]!,
        result.route[1]!,
        role,
        selfColor,
      ),
    });

    const primaryOption = toOption(primary);
    // 1手目が今すぐ指せる代替経路だけを残す(指せないものを並べても候補は増えないため)。
    const alternativeRoutes = found.slice(1).map(toOption).filter((o) => o.firstMoveUsis.length > 0);

    const blockingSquare = findFirstOwnBlocker(pos, primary.route, selfColor);
    const blocked =
      primaryOption.firstMoveUsis.length === 0 && alternativeRoutes.length === 0 && blockingSquare !== undefined;

    routes.push({
      targetSquare: targetSquareName,
      targetPiece: requiredPiece.piece,
      fromSquare: primaryOption.fromSquare,
      routeSquares: primaryOption.routeSquares,
      remainingSteps: primary.route.length - 1,
      firstMoveUsis: primaryOption.firstMoveUsis,
      alternativeRoutes,
      blockingSquare: blockingSquare === undefined ? null : makeSquareName(blockingSquare),
      blockedReason: blocked ? "occupied_by_own_piece" : null,
      preparatoryMoveUsis: blocked ? collectPreparatoryMoveUsis(legalMoves, blockingSquare, frozenSquares) : [],
    });
  }

  pruneConflictingAlternatives(routes, legalMoves, frozenSquares);
  const candidateMoves = buildCandidateMoves(routes);

  let unresolvedReason: RouteUnresolvedReason | null = null;
  if (candidateMoves.length === 0) {
    unresolvedReason =
      routes.length === 0 ? (skippedReasons[0] ?? "no_route_for_any_square") : "no_playable_first_move";
  }

  return { shapeId: targetShapeId, routes, candidateMoves, unresolvedReason };
}

/**
 * 別の目標マスの代表として既に使われている駒を、他の目標の代替経路から取り除く。
 *
 * 代替経路は目標マスごとに独立して求めるため、ある目標の代替に選ばれた駒が、
 * 後続の目標の代表にもなり得る(例: 銀冠で6九の金が「6七へ向かう代替」と
 * 「7八へ向かう代表」の両方に現れる)。この状態のまま候補手を作ると、
 * 同じ駒について行き先の違う候補手が2つ並び、「なぜこの手が出ているのか」を
 * 追跡できなくなる。1つの駒は1つの目標にだけ結びつける。
 *
 * 代替経路が取り除かれた結果、その目標について指せる1手目が無くなった場合は、
 * 経路を塞ぐ自駒の準備手を作り直す(取り除く前の判定のまま放置しない)。
 */
function pruneConflictingAlternatives(
  routes: ShapeSquareRoute[],
  legalMoves: string[],
  frozenSquares: Set<Square>,
): void {
  const primaryFromSquares = new Set(routes.map((route) => route.fromSquare));

  for (const route of routes) {
    const kept = route.alternativeRoutes.filter((option) => !primaryFromSquares.has(option.fromSquare));
    if (kept.length === route.alternativeRoutes.length) continue;

    route.alternativeRoutes = kept;
    if (route.firstMoveUsis.length > 0 || kept.length > 0 || route.blockingSquare === null) continue;

    const blockingSquare = parseSquareName(route.blockingSquare);
    if (blockingSquare === undefined) continue;
    route.blockedReason = "occupied_by_own_piece";
    route.preparatoryMoveUsis = collectPreparatoryMoveUsis(legalMoves, blockingSquare, frozenSquares);
  }
}

/**
 * 経路一覧から、実際に提示する候補手を組み立てる。
 * 経路の1手目が指せるならそれを、指せず準備手があるなら準備手を採る。
 * 上限(MAX_CANDIDATES_PER_TARGET / MAX_CANDIDATES_TOTAL)はエンジン参考評価の
 * コスト上限であり、将棋的な選別ではない(上限で切る順序はUSI昇順)。
 */
function buildCandidateMoves(routes: ShapeSquareRoute[]): RouteCandidateMove[] {
  const candidateMoves: RouteCandidateMove[] = [];
  const seenMoveUsis = new Set<string>();

  for (const route of routes) {
    if (candidateMoves.length >= MAX_CANDIDATES_TOTAL) break;

    // 代表の経路と、同じ手数で到達できる別の駒の経路をまとめて扱う。
    // 各候補手は自分自身の経路を持つ(説明文が実際の経路と食い違わないようにするため)。
    const options: ShapeSquareRouteOption[] = [
      { fromSquare: route.fromSquare, routeSquares: route.routeSquares, firstMoveUsis: route.firstMoveUsis },
      ...route.alternativeRoutes,
    ];
    const stepMoves = options.flatMap((option) =>
      option.firstMoveUsis.map((moveUsi) => ({ moveUsi, routeSquares: option.routeSquares })),
    );
    // 経路の1手目が1つも指せない場合に限り、経路を塞ぐ自駒をどかす準備手を候補にする。
    const isRouteStep = stepMoves.length > 0;
    const sourceMoves = isRouteStep
      ? stepMoves
      : route.preparatoryMoveUsis.map((moveUsi) => ({ moveUsi, routeSquares: route.routeSquares }));

    let addedForThisTarget = 0;
    for (const { moveUsi, routeSquares } of sourceMoves) {
      if (addedForThisTarget >= MAX_CANDIDATES_PER_TARGET) break;
      if (candidateMoves.length >= MAX_CANDIDATES_TOTAL) break;
      if (seenMoveUsis.has(moveUsi)) continue;

      seenMoveUsis.add(moveUsi);
      candidateMoves.push({
        moveUsi,
        kind: isRouteStep ? "route_step" : "preparation",
        targetSquare: route.targetSquare,
        targetPiece: route.targetPiece,
        routeSquares,
        remainingStepsAfter: isRouteStep ? routeSquares.length - 2 : null,
        clearingSquare: isRouteStep ? null : route.blockingSquare,
      });
      addedForThisTarget++;
    }
  }

  return candidateMoves;
}
