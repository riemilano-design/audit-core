// data/openings の recognition_pattern(戦型の「駒 × マス」の対)を、shapes の
// required_pieces と同じ形へ写し、**既存の shapeFormationAnalyzer をそのまま呼ぶ**だけの薄い層。
//
// 【このモジュールが新しく足していないもの(重要)】
// 新しい判定・閾値・数え方・将棋知識は一切足していない。盤の占有の判定は
// shapeDetector.ts、動いた証拠の判定は shapeFormationAnalyzer.ts / signatureEvidence.ts の
// 既存実装をそのまま使う。3段階の値の名前も形と同じ none / forming / completed で、
// 狙い(intentDetector.ts)の matched とは混ぜない(docs/DATA_MODEL.md「2つの尺度を統合しない」)。
//
// 【なぜ required_pieces へ写せるのか】
// data/schemas/openings.schema.json の recognition_pattern は {piece, to, order_hint?} の
// 配列であり、data/schemas/shapes.schema.json の required_pieces {piece, square, optional} と
// 同じ「駒 × マス」の対である。写すのは piece と to(→ square)だけで、optional は常に false。
//
// 【読まないもの(明記)】
// - order_hint(手順の順序。現在どこからも読まれていない)
// - leads_to_shape_ids(つながる形の一覧)
// - scenario(開発・検証専用の制御用データ。docs/SCENARIOS.md)
// recognition_pattern を持たない opening は「認識の候補にならない」(スキーマの記述どおり)ため、
// 適合器は null を返す。
//
// 【本体の経路にはつながっていない】
// 既定のディレクトリ定数を持たない(loadOpeningsFromDir は dir を必ず受け取る)。
// recognitionTimeline.ts・api/stateResponse.ts からは呼ばれておらず、戦型の名前が
// ユーザーへ出る経路は増えていない(docs/DATA_MODEL.md の「data/openings は実行時に
// 読み込まれていない」は、本番の認識の経路としては引き続き真)。

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import type { MoveEvent } from "./moveHistory.js";
import {
  analyzeShapeFormationFromEvents,
  type ShapeFormationResult,
} from "./shapeFormationAnalyzer.js";
import type { ShapeDefinition } from "./shapeRepository.js";

/** data/schemas/openings.schema.json の recognition_pattern の1要素。 */
export interface OpeningRecognitionPatternEntry {
  /** 動く駒(日本語駒名。shapes.required_pieces.piece と同じ表記) */
  piece: string;
  /** 移動先のマス目(USI形式)。shapes.required_pieces.square に対応する */
  to: string;
  /** 手順の中でのおおよその順序(任意)。**このモジュールは読まない** */
  order_hint?: number;
}

/** data/schemas/openings.schema.json に対応する型。必須欄はスキーマの required と同じ。 */
export interface OpeningDefinition {
  id: string;
  name: string;
  name_kana: string;
  /** openings.schema.json の enum は self / opponent の2値(shapes と違い both は無い) */
  side: "self" | "opponent";
  family: string;
  leads_to_shape_ids: string[];
  /** 対局シナリオ(開発・検証専用の制御用データ)。**このモジュールは読まない** */
  scenario?: unknown;
  /** 任意フィールド。値を持たない戦型は認識の候補にならない(スキーマの記述) */
  recognition_pattern?: OpeningRecognitionPatternEntry[];
  source: string;
  confidence_level: "high" | "medium" | "low";
  review_status: "draft" | "human_reviewed" | "expert_verified" | "expired";
  [key: string]: unknown;
}

/** analyzeOpeningFormationFromEvents の結果。ShapeFormationResult の欄はそのまま。 */
export interface OpeningFormationResult extends ShapeFormationResult {
  /** 判定のもとになった opening の id(shapeId と同じ値を、出所が分かる名前でも持つ) */
  openingId: string;
}

export class OpeningRepositoryError extends Error {}

/**
 * recognition_pattern を shapes の required_pieces へ写した ShapeDefinition を返す。
 * recognition_pattern が無い(または空の)opening は認識の候補にならないため null を返す。
 *
 * 写すのは形の判定に要る欄だけで、新しい値は作らない:
 * - required_pieces … {piece, square: to, optional: false}
 * - parent_shape_id … null(openings に親子関係の欄が無いため)
 * - characteristics … opening に同名の欄があれば写し、無ければ空文字(文言を発明しない)
 */
export function openingToShapeDefinition(opening: OpeningDefinition): ShapeDefinition | null {
  const pattern = opening.recognition_pattern;
  if (!Array.isArray(pattern) || pattern.length === 0) return null;

  return {
    id: opening.id,
    name: opening.name,
    name_kana: opening.name_kana,
    side: opening.side,
    family: opening.family,
    parent_shape_id: null,
    required_pieces: pattern.map((entry) => ({
      piece: entry.piece,
      square: entry.to,
      optional: false,
    })),
    characteristics: typeof opening.characteristics === "string" ? opening.characteristics : "",
    confidence_level: opening.confidence_level,
    review_status: opening.review_status,
  };
}

/**
 * 既に再生済みの MoveEvent を受け取り、opening の recognition_pattern を
 * 形の判定(盤の占有 + 動いた証拠)にかけた結果を返す。
 *
 * 第1引数は analyzeShapeFormationFromEvents と同じく「判定する局面の SFEN」で、
 * events はその局面までの再生結果である(整合の担保は呼び出し側の責務。
 * shapeFormationAnalyzer.ts の analyzeShapeFormationFromEvents と同じ約束)。
 *
 * 判定そのものは analyzeShapeFormationFromEvents に委ね、このモジュールは
 * 適合(openingToShapeDefinition)と openingId を付けることしか行わない。
 * 並び順も委譲先のまま(matchScore 降順・id 昇順)である。
 */
export function analyzeOpeningFormationFromEvents(
  sfen: string,
  events: MoveEvent[],
  openings: OpeningDefinition[],
): OpeningFormationResult[] {
  const shapes: ShapeDefinition[] = [];
  for (const opening of openings) {
    const shape = openingToShapeDefinition(opening);
    if (shape) shapes.push(shape);
  }

  // options は shapes だけ(委譲先が読むのは shapes のみ。監査の指摘で、効かない渡り口 initialSfen はレーン長が外した)
  const results = analyzeShapeFormationFromEvents(sfen, events, { shapes });
  return results.map((result) => ({ ...result, openingId: result.shapeId }));
}

function isOpeningDefinition(value: unknown): value is OpeningDefinition {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  if (
    typeof v.id !== "string" ||
    typeof v.name !== "string" ||
    typeof v.name_kana !== "string" ||
    typeof v.side !== "string" ||
    typeof v.family !== "string" ||
    !Array.isArray(v.leads_to_shape_ids) ||
    typeof v.review_status !== "string"
  ) {
    return false;
  }
  if (v.recognition_pattern === undefined) return true;
  return (
    Array.isArray(v.recognition_pattern) &&
    v.recognition_pattern.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as Record<string, unknown>).piece === "string" &&
        typeof (entry as Record<string, unknown>).to === "string",
    )
  );
}

/**
 * 指定したディレクトリ配下の全 JSON を OpeningDefinition として読み込む。
 * shapeRepository.ts の loadShapes と同じく、読み込みと最低限の形式チェックだけを行う
 * (スキーマ準拠の検証は scripts/validate-data.mjs の責務)。
 *
 * **既定のディレクトリを持たない。** 呼び出し側が必ず dir を渡す
 * (本番の認識の経路は data/openings を読まないままにするため)。
 */
export function loadOpeningsFromDir(dir: string): OpeningDefinition[] {
  let files: string[];
  try {
    files = readdirSync(dir).filter((f) => f.endsWith(".json"));
  } catch (err) {
    throw new OpeningRepositoryError(
      `openings のディレクトリを読み込めません: "${dir}" (${(err as Error).message})`,
    );
  }

  const openings: OpeningDefinition[] = [];
  for (const file of files.sort()) {
    const fullPath = path.join(dir, file);
    let parsed: unknown;
    try {
      parsed = JSON.parse(readFileSync(fullPath, "utf-8"));
    } catch (err) {
      throw new OpeningRepositoryError(
        `Openingデータの読み込みに失敗しました: "${fullPath}" (${(err as Error).message})`,
      );
    }
    if (!isOpeningDefinition(parsed)) {
      throw new OpeningRepositoryError(`Openingデータの形式が不正です(必須フィールド不足): "${fullPath}"`);
    }
    openings.push(parsed);
  }

  // ファイル名(readdirSync)のソート順に依存せず、id昇順で決定的な順序にする(loadShapes と同じ)。
  return openings.sort((a, b) => a.id.localeCompare(b.id));
}
