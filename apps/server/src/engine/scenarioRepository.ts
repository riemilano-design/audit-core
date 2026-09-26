// data/openings/*.json (将棋知識としての唯一のソース、docs/DATA_MODEL.md参照) のうち、
// 相手AI制御用データ(openings.scenario)を読み込む。
//
// ①これは制御用データの読み込みであり、docs/SCENARIOS.mdが分離を求める
// 「認識用データ(analysis/intentRepository.ts等が読むrecognition_pattern)」とは別物。
// analysis/配下の各repositoryが読み込む認識用データと本モジュールを混同しないこと。
// ②`verification_status === "human_approved"` の variant だけを候補として返すことが、
// docs/KIND3_VERIFICATION.md が定める実運用ゲートである(Kind 3の人間承認要件)。
// ③data/を読み込むモジュールがengine/配下に置かれるのはこれが最初(従来は
// analysis/配下のshapeRepository.ts・intentRepository.tsのみだった)。
//
// shapeRepository.ts / intentRepository.tsと同じ設計方針: ファイルの読み込みと
// 最低限の形式チェックのみを行い、将棋知識としての正しさの判断は一切行わない
// (それは人間のレビュー + data/schemas/openings.schema.json +
// scripts/validate-data.mjs の役割)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// apps/server/src/engine -> apps/server/src -> apps/server -> apps -> リポジトリルート
export const DEFAULT_OPENINGS_DIR = path.join(__dirname, "..", "..", "..", "..", "data", "openings");

/**
 * 承認済み(verification_status === "human_approved")のvariantから、
 * 相手AI制御に必要な最小限の情報だけを取り出したもの。
 * verification_record(検証記録)はここでは持ち出さない(非公開情報のため、
 * 必要になるまで公開境界に近い層へ持ち込まない)。
 */
export interface ApprovedScenarioVariant {
  openingId: string;
  variantId: string;
  targetIntentId: string;
  moves: string[];
}

export class ScenarioRepositoryError extends Error {}

interface RawScenarioVariant {
  id: string;
  target_intent_id: string;
  moves: string[];
  verification_status: string;
}

interface RawOpeningWithScenario {
  id: string;
  scenario: { variants: RawScenarioVariant[] } | null;
}

function isRawScenarioVariant(value: unknown): value is RawScenarioVariant {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.target_intent_id === "string" &&
    Array.isArray(v.moves) &&
    v.moves.every((m) => typeof m === "string") &&
    typeof v.verification_status === "string"
  );
}

function isRawOpeningWithScenario(value: unknown): value is RawOpeningWithScenario {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  if (typeof v.id !== "string") return false;
  if (v.scenario === null || v.scenario === undefined) return true;
  if (typeof v.scenario !== "object") return false;
  const scenario = v.scenario as Record<string, unknown>;
  return Array.isArray(scenario.variants) && scenario.variants.every(isRawScenarioVariant);
}

/**
 * data/openings/ 配下の全JSONファイルを読み込み、`verification_status === "human_approved"`
 * のvariantだけをApprovedScenarioVariant[]として返す。
 * `scenario` が null/undefinedのopening、およびhuman_approved以外のvariantは候補に含めない。
 */
export function loadApprovedScenarioVariants(
  dir: string = DEFAULT_OPENINGS_DIR,
): ApprovedScenarioVariant[] {
  let files: string[];
  try {
    files = readdirSync(dir).filter((f) => f.endsWith(".json"));
  } catch (err) {
    throw new ScenarioRepositoryError(
      `シナリオのディレクトリを読み込めません: "${dir}" (${(err as Error).message})`,
    );
  }

  const variants: ApprovedScenarioVariant[] = [];
  for (const file of files.sort()) {
    const fullPath = path.join(dir, file);
    let parsed: unknown;
    try {
      parsed = JSON.parse(readFileSync(fullPath, "utf-8"));
    } catch (err) {
      throw new ScenarioRepositoryError(
        `Openingデータの読み込みに失敗しました: "${fullPath}" (${(err as Error).message})`,
      );
    }
    if (!isRawOpeningWithScenario(parsed)) {
      throw new ScenarioRepositoryError(`Openingデータの形式が不正です(必須フィールド不足): "${fullPath}"`);
    }
    for (const variant of parsed.scenario?.variants ?? []) {
      if (variant.verification_status !== "human_approved") continue;
      variants.push({
        openingId: parsed.id,
        variantId: variant.id,
        targetIntentId: variant.target_intent_id,
        moves: variant.moves,
      });
    }
  }

  // ファイル名(readdirSync)のソート順に依存せず、openingId→variantId昇順で決定的な順序にする。
  return variants.sort(
    (a, b) => a.openingId.localeCompare(b.openingId) || a.variantId.localeCompare(b.variantId),
  );
}

let cachedApprovedScenarioVariants: ApprovedScenarioVariant[] | undefined;

/**
 * 既定のdata/openings/を読み込み結果をプロセス内でキャッシュして返す。
 * データファイルはプロセス起動中に変わらない前提(getShapes/getIntentsと同じ方針)。
 */
export function getApprovedScenarioVariants(): ApprovedScenarioVariant[] {
  if (!cachedApprovedScenarioVariants) {
    cachedApprovedScenarioVariants = loadApprovedScenarioVariants();
  }
  return cachedApprovedScenarioVariants;
}
