// data/shapes/*.json (将棋知識としての唯一のソース、docs/DATA_MODEL.md参照) を読み込む。
// このモジュールはファイルの読み込みと最低限の形式チェックのみを行い、
// 将棋知識としての正しさの判断(内容が正しいか)は一切行わない
// (それは人間のレビュー + data/schemas/shapes.schema.json + scripts/validate-data.mjs の役割)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// apps/server/src/analysis -> apps/server/src -> apps/server -> apps -> リポジトリルート
export const DEFAULT_SHAPES_DIR = path.join(__dirname, "..", "..", "..", "..", "data", "shapes");

export interface ShapeRequiredPiece {
  piece: string;
  square: string;
  optional: boolean;
}

export interface ShapeDefinition {
  id: string;
  name: string;
  name_kana: string;
  side: "self" | "opponent" | "both";
  family: string;
  parent_shape_id: string | null;
  required_pieces: ShapeRequiredPiece[];
  typical_build_order?: string[];
  characteristics: string;
  /** data/schemas/shapes.schema.json では必須ではないため optional。
   * 「この囲いは何に弱いか」を初心者向けに述べた既存の文で、新規に作るものではない。 */
  weak_against?: string;
  confidence_level: "high" | "medium" | "low";
  /** 知識を追加してよいかと、ユーザーへ見せてよいかを分離する運用区分
   * (data/schemas/shapes.schema.json参照)。名前を出してよいかの判断は
   * analysis/nameExposure.tsに集約し、このモジュールでは判断しない。 */
  review_status: "draft" | "human_reviewed" | "expert_verified" | "expired";
  [key: string]: unknown;
}

export class ShapeRepositoryError extends Error {}

function isShapeDefinition(value: unknown): value is ShapeDefinition {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    typeof v.side === "string" &&
    typeof v.family === "string" &&
    Array.isArray(v.required_pieces) &&
    typeof v.review_status === "string"
  );
}

/**
 * data/shapes/ 配下の全JSONファイルを読み込み、ShapeDefinitionの配列として返す。
 * 内容の詳細な妥当性(スキーマ準拠)はscripts/validate-data.mjs側の責務のため、
 * ここでは「本モジュールが最低限読み書きに必要とする形」であることのみを確認する。
 */
export function loadShapes(dir: string = DEFAULT_SHAPES_DIR): ShapeDefinition[] {
  let files: string[];
  try {
    files = readdirSync(dir).filter((f) => f.endsWith(".json"));
  } catch (err) {
    throw new ShapeRepositoryError(
      `data/shapes/ ディレクトリを読み込めません: "${dir}" (${(err as Error).message})`,
    );
  }

  const shapes: ShapeDefinition[] = [];
  for (const file of files.sort()) {
    const fullPath = path.join(dir, file);
    let parsed: unknown;
    try {
      parsed = JSON.parse(readFileSync(fullPath, "utf-8"));
    } catch (err) {
      throw new ShapeRepositoryError(`Shapeデータの読み込みに失敗しました: "${fullPath}" (${(err as Error).message})`);
    }
    if (!isShapeDefinition(parsed)) {
      throw new ShapeRepositoryError(`Shapeデータの形式が不正です(必須フィールド不足): "${fullPath}"`);
    }
    shapes.push(parsed);
  }

  // ファイル名(readdirSync)のソート順に依存せず、id昇順で決定的な順序にする。
  return shapes.sort((a, b) => a.id.localeCompare(b.id));
}

let cachedShapes: ShapeDefinition[] | undefined;

/**
 * 既定のdata/shapes/を読み込み結果をプロセス内でキャッシュして返す。
 * データファイルはプロセス起動中に変わらない前提(将来ホットリロードが必要になれば別途設計)。
 */
export function getShapes(): ShapeDefinition[] {
  if (!cachedShapes) {
    cachedShapes = loadShapes();
  }
  return cachedShapes;
}
