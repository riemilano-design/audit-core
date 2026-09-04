// SFEN(局面) -> Shape判定 の本実装。
// docs/DATA_MODEL.md の教育用データパイプライン②(戦型・形)のうち、
// 「形」判定を担当する。将棋知識(どの駒がどこにあれば何の形か)は一切ここで判断せず、
// data/shapes/*.json (shapeRepository.ts経由)に確定した内容をそのままshogiopsの盤面と
// 突き合わせるだけに責務を限定する(prototypes/shape-matcher/shape-matcher.mjs の設計を踏襲)。
//
// 座標視点(perspectiveColor)は docs/DATA_MODEL.md のMVP確定仕様に従い、
// side="self"は先手(sente)、side="opponent"は後手(gote)に固定する。
// side="both"は現時点でdata/shapes/に存在しないが、将来追加された場合に備えて
// 両視点を判定し、より一致度の高い方を採用する(知識データの追加ではなく判定ロジックの一般化)。

import type { Color } from "shogiops/types";
import { parseSquareName } from "shogiops/util";
import { parsePosition } from "../rules/sfenPosition.js";
import { japaneseToRole } from "./pieceMapping.js";
import { getShapes, type ShapeDefinition, type ShapeRequiredPiece } from "./shapeRepository.js";

export { InvalidSfenError } from "../rules/sfenPosition.js";

export type ShapeStatus = "none" | "forming" | "completed";

export interface ShapeDetectionResult {
  shapeId: string;
  name: string;
  side: ShapeDefinition["side"];
  family: string;
  parentShapeId: string | null;
  perspectiveColor: Color;
  status: ShapeStatus;
  /** 必須駒(optional:falseのrequired_pieces)のうち一致した割合。0〜1。決定的な値(同じ局面なら常に同じ値)。 */
  matchScore: number;
  matchedSquares: string[];
  missingSquares: string[];
  optionalMatchedSquares: string[];
  /** data/shapes/*.json 側の「この知識データ自体への自信度」(検知の確信度とは別概念)。intentDetector.tsのdataConfidenceLevelと対応。 */
  dataConfidenceLevel: ShapeDefinition["confidence_level"];
  /** 後続(説明生成)処理がそのまま使えるよう、shape定義からそのまま引き継ぐ初心者向け特徴説明 */
  characteristics: string;
}

export class ShapeDetectorError extends Error {}

function perspectiveColorsForSide(side: ShapeDefinition["side"]): Color[] {
  // docs/DATA_MODEL.md: MVPでは role=self→sente固定、role=opponent→gote固定。
  if (side === "self") return ["sente"];
  if (side === "opponent") return ["gote"];
  return ["sente", "gote"];
}

interface PieceCheckResult {
  square: string;
  present: boolean;
}

function checkRequiredPiece(
  pos: ReturnType<typeof parsePosition>,
  requiredPiece: ShapeRequiredPiece,
  perspectiveColor: Color,
): PieceCheckResult {
  const square = parseSquareName(requiredPiece.square);
  if (square === undefined) {
    throw new ShapeDetectorError(`Shapeデータのマス目表記が不正です: "${requiredPiece.square}"`);
  }
  const expectedRole = japaneseToRole(requiredPiece.piece);
  const actual = pos.board.get(square);
  const present = actual !== undefined && actual.color === perspectiveColor && actual.role === expectedRole;
  return { square: requiredPiece.square, present };
}

function evaluateShapeForPerspective(
  pos: ReturnType<typeof parsePosition>,
  shape: ShapeDefinition,
  perspectiveColor: Color,
): ShapeDetectionResult {
  const requiredNonOptional = shape.required_pieces.filter((p) => !p.optional);
  const optional = shape.required_pieces.filter((p) => p.optional);

  const matchedSquares: string[] = [];
  const missingSquares: string[] = [];
  for (const piece of requiredNonOptional) {
    const { square, present } = checkRequiredPiece(pos, piece, perspectiveColor);
    (present ? matchedSquares : missingSquares).push(square);
  }

  const optionalMatchedSquares: string[] = [];
  for (const piece of optional) {
    const { square, present } = checkRequiredPiece(pos, piece, perspectiveColor);
    if (present) optionalMatchedSquares.push(square);
  }

  // required_piecesが全てoptionalな(現状のdata/shapes/には存在しない)場合の0除算回避。
  // その場合、必須駒による判定ができないため常に'none'/matchScore=0とする
  // (optional駒だけでは形が「成立している」とは言えないという安全側の判断)。
  const matchScore = requiredNonOptional.length === 0 ? 0 : matchedSquares.length / requiredNonOptional.length;

  let status: ShapeStatus;
  if (requiredNonOptional.length === 0 || matchedSquares.length === 0) {
    status = "none";
  } else if (missingSquares.length === 0) {
    status = "completed";
  } else {
    status = "forming";
  }

  return {
    shapeId: shape.id,
    name: shape.name,
    side: shape.side,
    family: shape.family,
    parentShapeId: shape.parent_shape_id ?? null,
    perspectiveColor,
    status,
    matchScore,
    matchedSquares,
    missingSquares,
    optionalMatchedSquares,
    dataConfidenceLevel: shape.confidence_level,
    characteristics: shape.characteristics,
  };
}

/**
 * 1つのSFEN局面に対して、指定した(または既定の)Shape一覧すべてを判定する。
 * 同じ局面・同じshapes一覧に対しては常に同じ結果を返す(決定的)。
 * side="both"のshapeは sente/gote 両視点で判定し、matchScoreが高い方(同点ならsente優先)を採用する。
 */
export function detectShapes(sfen: string, shapes: ShapeDefinition[] = getShapes()): ShapeDetectionResult[] {
  const pos = parsePosition(sfen);

  const results = shapes.map((shape) => {
    const candidates = perspectiveColorsForSide(shape.side).map((color) =>
      evaluateShapeForPerspective(pos, shape, color),
    );
    // 複数視点候補がある場合(side="both")、matchScoreが最も高いものを採用する。
    // 同点はcandidatesの並び順(sente優先)を保つためreduceで厳密な">"のみ更新する。
    return candidates.reduce((best, cur) => (cur.matchScore > best.matchScore ? cur : best));
  });

  // 呼び出し側(将来のIntent判定・UI)が扱いやすいよう、一致度が高い順・同点ならshapeId昇順で安定ソートする。
  return results.sort((a, b) => b.matchScore - a.matchScore || a.shapeId.localeCompare(b.shapeId));
}

/**
 * 指定したidのShape1件だけを判定する。将来のIntent判定などで
 * 「特定の形についてだけ知りたい」場合に使う想定。
 */
export function detectShape(
  sfen: string,
  shapeId: string,
  shapes: ShapeDefinition[] = getShapes(),
): ShapeDetectionResult | undefined {
  const shape = shapes.find((s) => s.id === shapeId);
  if (!shape) return undefined;
  return detectShapes(sfen, [shape])[0];
}
