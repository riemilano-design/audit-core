// data/intents/*.json (将棋知識としての唯一のソース、docs/DATA_MODEL.md参照) を読み込む。
// shapeRepository.tsと同じ設計方針: ファイルの読み込みと最低限の形式チェックのみを行い、
// 将棋知識としての正しさの判断は一切行わない(それは人間のレビュー +
// data/schemas/intents.schema.json + scripts/validate-data.mjs の役割)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// apps/server/src/analysis -> apps/server/src -> apps/server -> apps -> リポジトリルート
export const DEFAULT_INTENTS_DIR = path.join(__dirname, "..", "..", "..", "..", "data", "intents");

export interface RecognitionPatternEntry {
  piece: string;
  to: string;
  order_hint?: number;
}

export interface AffectsTargetShape {
  shape_id: string;
  adjustment: "prioritize" | "deprioritize";
  reason?: string;
}

export interface IntentDefinition {
  id: string;
  name: string;
  opening_id: string;
  recognition_pattern: RecognitionPatternEntry[];
  current_aim_explanation: string;
  next_aim_explanation: string;
  affects_target_shapes?: AffectsTargetShape[];
  confidence_level: "high" | "medium" | "low";
  /** 知識を追加してよいかと、ユーザーへ見せてよいかを分離する運用区分
   * (data/schemas/intents.schema.json参照)。名前を出してよいかの判断は
   * analysis/nameExposure.tsに集約し、このモジュールでは判断しない。 */
  review_status: "draft" | "human_reviewed" | "expert_verified" | "expired";
  [key: string]: unknown;
}

export class IntentRepositoryError extends Error {}

function isIntentDefinition(value: unknown): value is IntentDefinition {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    typeof v.opening_id === "string" &&
    Array.isArray(v.recognition_pattern) &&
    typeof v.review_status === "string"
  );
}

/**
 * data/intents/ 配下の全JSONファイルを読み込み、IntentDefinitionの配列として返す。
 * 内容の詳細な妥当性(スキーマ準拠)はscripts/validate-data.mjs側の責務のため、
 * ここでは「本モジュールが最低限読み書きに必要とする形」であることのみを確認する。
 */
export function loadIntents(dir: string = DEFAULT_INTENTS_DIR): IntentDefinition[] {
  let files: string[];
  try {
    files = readdirSync(dir).filter((f) => f.endsWith(".json"));
  } catch (err) {
    throw new IntentRepositoryError(
      `狙いのディレクトリを読み込めません: "${dir}" (${(err as Error).message})`,
    );
  }

  const intents: IntentDefinition[] = [];
  for (const file of files.sort()) {
    const fullPath = path.join(dir, file);
    let parsed: unknown;
    try {
      parsed = JSON.parse(readFileSync(fullPath, "utf-8"));
    } catch (err) {
      throw new IntentRepositoryError(`Intentデータの読み込みに失敗しました: "${fullPath}" (${(err as Error).message})`);
    }
    if (!isIntentDefinition(parsed)) {
      throw new IntentRepositoryError(`Intentデータの形式が不正です(必須フィールド不足): "${fullPath}"`);
    }
    intents.push(parsed);
  }

  // ファイル名(readdirSync)のソート順に依存せず、id昇順で決定的な順序にする。
  return intents.sort((a, b) => a.id.localeCompare(b.id));
}

let cachedIntents: IntentDefinition[] | undefined;

/**
 * 既定のdata/intents/を読み込み結果をプロセス内でキャッシュして返す。
 * データファイルはプロセス起動中に変わらない前提(将来ホットリロードが必要になれば別途設計)。
 */
export function getIntents(): IntentDefinition[] {
  if (!cachedIntents) {
    cachedIntents = loadIntents();
  }
  return cachedIntents;
}
