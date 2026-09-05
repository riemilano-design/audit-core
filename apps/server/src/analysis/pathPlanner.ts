// ShapeFormationResult(Unit5) + shapeRepositoryのShape定義 + legalMoves(rules層)
// -> ⑦「候補手」の前半(=目標shapeへ近づくために合法な候補手を列挙するだけ)への変換。
// docs/DATA_MODEL.md の教育用データパイプライン⑦の前段を実装する。
//
// 【このモジュールが絶対にしないこと】
// 「この手が最善」「この手を指すべき」「この手は悪手」「この手が安全」
// 「候補Aより候補Bが優れている」といった評価・順位付けは一切行わない。
// これはMultiPVによる安全確認(将来のUnit、engine-integration領域)の責務であり、
// CLAUDE.mdルール3番(将棋エンジンによる安全確認を経ていない候補手をユーザーに見せない)
// にも関わるため、本モジュール単体でユーザーに「候補手」として提示してはならない。
// ここで返すのはあくまで「既存データ上、その形成に向かう経路として候補になり得る
// 合法手」の列挙に過ぎない。
//
// 【typical_build_orderの解釈について】
// typical_build_orderは「唯一の正解手順」ではなく、data/schemas/shapes.schema.json
// が説明する通り「典型的な組み方の順序の一例」である。本モジュールもこれを
// 「次に埋めるべき"候補"マスの一例」としてのみ扱い、断定的な言い回し
// (「正解」「必ずこの手」等)をコード・コメント・返り値のいずれにも含めない。
//
// 【typical_build_orderとrequired_piecesの対応について(重要・検証済み)】
// 実装前に data/shapes/*.json 全3件を確認したところ、
// 「typical_build_orderのN番目 == required_piecesのN番目」というインデックス対応は
// 保証されていない(mino_ginkanmuri.jsonはtypical_build_orderの並び順が
// required_piecesの並び順と異なる)。一方、data/schemas/shapes.schema.jsonの
// typical_build_orderの説明「required_piecesのsquareを順番に並べる」が示す通り、
// 「typical_build_orderの各要素は、required_pieces側のどれかのsquareと文字列として
// 一致する」という対応は3件全てで成立する(値としての集合が完全一致することを
// 機械的に確認済み)。
// したがって本モジュールは、インデックスではなく「square文字列の一致」でのみ
// required_pieces側のpiece(駒種)を引く。この対応が見つからない場合
// (=将来追加されるデータがこの前提を満たさない場合)は、駒種を推測せず
// 未解決(unresolvedReason)として安全に候補なしを返す。
//
// 【合法手について】
// 候補手は必ずrules/legalMoves.ts(既存の合法手判定)が返す手だけから選ぶ。
// 独自の合法性判定は行わない。局面の読み取りも、moveHistory.tsが既に採用している
// パターン(parseUsi + pos.board.get(from)で駒種を確認)を踏襲するのみで、
// 局面遷移(指し手の適用)は行わない(このUnitでは1手先の局面を必要としないため)。

import { isDrop, parseSquareName, parseUsi } from "shogiops/util";
import type { Square } from "shogiops/types";
import { getLegalMoves } from "../rules/legalMoves.js";
import { parsePosition } from "../rules/sfenPosition.js";
import { japaneseToRole, UnknownPieceNameError } from "./pieceMapping.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { getShapes, type ShapeDefinition } from "./shapeRepository.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";

/**
 * 候補手が得られなかった場合の理由。いずれも「エラーで対局を止める」のではなく
 * 「候補手なし」として安全に扱うための分類(docs/PHASES.md Phase1完了条件
 * 「無言・エラーにならず穏当な表示に落ちる」の考え方をPhase2でも踏襲する)。
 */
export type PathPlanUnresolvedReason =
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
  /** shape定義にtypical_build_orderが無い(任意フィールドのため未設定の場合がある) */
  | "build_order_unavailable"
  /** typical_build_order上のどの要素もmissingSquaresと一致せず、次の対象マスを決定できない */
  | "target_square_undetermined"
  /** 対象マスに対応するrequired_pieces側のエントリが見つからない(square文字列一致で解決できない) */
  | "piece_mapping_unresolved"
  /** required_pieces.pieceの表記がpieceMapping.tsで未対応(未知の駒種表記) */
  | "unknown_piece_name"
  /** 現在の局面が自分(side="self"の視点色)の手番ではない */
  | "not_self_turn"
  /** 対象マスへ実際に移動できる合法手が1つも無い */
  | "no_legal_move_to_target";

export interface PathPlanCandidateMove {
  /** USI形式の指し手(rules/legalMoves.tsが返す合法手のうちの1つ) */
  moveUsi: string;
}

export interface PathPlanResult {
  shapeId: string;
  /**
   * typical_build_order上、次に埋める候補として決定されたマス(USI形式)。
   * 決定できなかった場合はnull(unresolvedReasonを参照)。
   */
  targetSquare: string | null;
  /**
   * targetSquareに置く駒種(data/shapes/*.jsonのrequired_pieces.piece、日本語表記そのまま)。
   * 決定できなかった場合はnull。
   */
  targetPiece: string | null;
  /**
   * targetSquareへ実際に移動できる合法手の候補一覧。優劣・推奨度は一切付けない
   * (どれが良いかはこの段階では判定しない)。
   */
  candidateMoves: PathPlanCandidateMove[];
  /** 候補手が得られなかった場合の理由。候補手が1件以上ある場合はnull。 */
  unresolvedReason: PathPlanUnresolvedReason | null;
}

export interface PlanPathOptions {
  shapes?: ShapeDefinition[];
}

function emptyResult(shapeId: string, unresolvedReason: PathPlanUnresolvedReason): PathPlanResult {
  return { shapeId, targetSquare: null, targetPiece: null, candidateMoves: [], unresolvedReason };
}

/**
 * typical_build_orderを順に見て、まだ埋まっていない(missingSquaresに含まれる)
 * 最初のマスを「次に埋める候補」として決定する。
 * typical_build_order自体は「典型的な進め方の一例」であり、これを唯一の正解として
 * 断定するものではない(このモジュール全体の方針、ファイル冒頭コメント参照)。
 */
function findNextTargetSquare(buildOrder: string[], missingSquares: string[]): string | undefined {
  const missingSet = new Set(missingSquares);
  return buildOrder.find((square) => missingSet.has(square));
}

/**
 * 対象マスのpiece(駒種)を、required_pieces側からsquare文字列の一致で引く。
 * インデックス対応は使わない(ファイル冒頭コメントの検証結果を参照)。
 * 一致するエントリが無い場合はundefined(=推測せず未解決として扱う)。
 */
function findRequiredPieceBySquare(
  shapeDef: ShapeDefinition,
  targetSquare: string,
): ShapeDefinition["required_pieces"][number] | undefined {
  return shapeDef.required_pieces.find((p) => !p.optional && p.square === targetSquare);
}

/**
 * Unit5(analyzeShapeFormation)の判定結果とshapeRepositoryのShape定義から、
 * 「targetShapeIdへ近づくために、現在の局面から実際に移動できる合法手」を列挙する。
 *
 * 【責務の範囲】
 * - typical_build_order上の次の対象マスを決定する(唯一の正解としてではなく候補として)
 * - そのマスへの合法手をrules/legalMoves.tsから抽出する(独自の合法性判定はしない)
 * - 複数候補があれば全て保持する(優劣は付けない)
 * - 候補が得られない場合は例外を投げず、unresolvedReasonつきの安全な結果を返す
 *
 * 【対象外】
 * 候補手の安全性評価・最善手判定・エンジンとの突き合わせ・説明生成・API/UI統合は
 * 一切行わない(将来の別Unitの責務)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function planPathToShape(
  sfen: string,
  shapeResults: ShapeFormationResult[],
  targetShapeId: string,
  options: PlanPathOptions = {},
): PathPlanResult {
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
  const shapeDef = shapes.find((s) => s.id === targetShapeId);
  if (!shapeDef) return emptyResult(targetShapeId, "shape_definition_not_found");

  const buildOrder = shapeDef.typical_build_order;
  if (!buildOrder || buildOrder.length === 0) {
    return emptyResult(targetShapeId, "build_order_unavailable");
  }

  const targetSquare = findNextTargetSquare(buildOrder, shapeResult.missingSquares);
  if (!targetSquare) return emptyResult(targetShapeId, "target_square_undetermined");

  const requiredPiece = findRequiredPieceBySquare(shapeDef, targetSquare);
  if (!requiredPiece) return emptyResult(targetShapeId, "piece_mapping_unresolved");

  let expectedRole: ReturnType<typeof japaneseToRole>;
  try {
    expectedRole = japaneseToRole(requiredPiece.piece);
  } catch (err) {
    if (err instanceof UnknownPieceNameError) {
      return emptyResult(targetShapeId, "unknown_piece_name");
    }
    throw err;
  }

  // sfen自体の妥当性チェックはparsePosition/getLegalMoves内部で行われる
  // (不正なSFENに対してはInvalidSfenErrorがそのまま伝播する。呼び出し側の責務)。
  const pos = parsePosition(sfen);
  if (pos.turn !== shapeResult.perspectiveColor) {
    // 相手の手番の局面では、自分側の形成に向かう手を提示しない(安全なフォールバック)。
    return emptyResult(targetShapeId, "not_self_turn");
  }

  const targetSquareValue: Square | undefined = parseSquareName(targetSquare);
  if (targetSquareValue === undefined) {
    // shapes.schema.json上squareは常にUSI形式のはずだが、型上の安全のため確認する。
    return emptyResult(targetShapeId, "target_square_undetermined");
  }

  const legalMoves = getLegalMoves(sfen);
  const candidateMoves: PathPlanCandidateMove[] = [];

  for (const moveUsi of legalMoves) {
    const move = parseUsi(moveUsi);
    if (!move) continue; // legalMoves.tsが返した手のはずだが、型上の安全のため確認する。
    if (move.to !== targetSquareValue) continue;

    // moveHistory.ts(Unit2/Unit5共通の既存パターン)と同じ方法で、この合法手が
    // 動かす駒種を読み取る(ドロップならmove.role、通常の移動なら移動元の駒)。
    const role = isDrop(move) ? move.role : pos.board.get(move.from)?.role;
    if (role !== expectedRole) continue;

    candidateMoves.push({ moveUsi });
  }

  if (candidateMoves.length === 0) {
    return {
      shapeId: targetShapeId,
      targetSquare,
      targetPiece: requiredPiece.piece,
      candidateMoves: [],
      unresolvedReason: "no_legal_move_to_target",
    };
  }

  return {
    shapeId: targetShapeId,
    targetSquare,
    targetPiece: requiredPiece.piece,
    candidateMoves,
    unresolvedReason: null,
  };
}
