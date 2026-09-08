// ShapeFormationResult[](Unit5, shapeFormationAnalyzer.ts) + TargetPurposeAdjustment[]
// (⑤, targetPurposeSelector.ts) -> ⑥「目指せる形」のランキング への変換。
// docs/DATA_MODEL.md の教育用データパイプライン⑥を実装する。⑤同様、⑥も
// 「ロジック側が実行時に算出し、静的データとしては持たない」ものであるため、
// data/配下への新規追加は行わない。
//
// 【将棋知識・数値重みについて】
// このモジュールは新しい将棋知識も、根拠のない数値的な重み付けも導入しない。
// 並び順は次の2つの「既存データがそのまま持っている値」だけを使った、厳密な
// 辞書式順序(lexicographic order)で決める。合成のための係数・加重平均などの
// 新しい計算式は一切用いない。
//
//   1. 調整区分(tier): ⑤(targetPurposeSelector.ts)が返すadjustmentの
//      "prioritize" / (調整なし) / "deprioritize" という3値を、その言葉の意味
//      どおりの順序(優先 < 中立 < 後回し)で並べるだけ。これはintents.schema.jsonの
//      affects_target_shapes.adjustmentという既存フィールドの値そのものの意味を
//      読み替えているだけであり、prioritize/deprioritizeの間に何らかの数値差
//      (例: 2倍優先する等)を新しく設定するものではない。
//   2. 同tier内はmatchScore降順: shapeDetector.ts(Unit1)が既に算出している
//      「必須駒のうち一致した割合」をそのまま再利用する。新しいスコア計算式は
//      追加していない。
//   3. 最終的な同点はshapeId昇順で決定的にする。これはshapeDetector.ts/
//      intentDetector.tsが既に採用しているタイブレーク規約と同じもの。
//
// 【側(side)によるフィルタ】
// side="opponent"のshape(相手陣形判定専用)は、自分が目指す形にはなり得ないため
// 候補から除外する。これはshapes.schema.jsonのsideフィールドの定義
// (self=自分の目標になり得る/opponent=相手陣形の判定用/both=両方)をそのまま
// 適用しているだけで、新しい知識ではない。
//
// 【completed除外】
// 既に完成している形は「これから目指す形」ではないため候補から除外する
// (ユーザー指示、およびshapes.required_pieces/parent_shape_idの発展関係から
// 自然に導かれる: 完成済みの形をさらに"目指す"必要はない)。
//
// 【候補手・API/UI・MultiPVについて】
// このモジュールは⑦(候補手)・エンジンとの安全確認・API/UIへの接続を一切行わない
// (Phase2 Unit1のスコープ外)。返すのはランキング済みのshape一覧のみ。

import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import type { TargetPurposeAdjustment } from "./targetPurposeSelector.js";

export interface RankedReachableShape {
  shapeId: string;
  name: string;
  family: string;
  parentShapeId: string | null;
  /** shapeFormationAnalyzer.tsの判定結果(completedは事前に除外されるため forming/none のみ)。 */
  status: ShapeFormationResult["status"];
  matchScore: number;
  /** ⑤由来の調整。対応するintentの兆候が無い場合はnull(=中立)。 */
  adjustment: TargetPurposeAdjustment["adjustment"] | null;
  /** adjustmentがnullでない場合の根拠(intents.affects_target_shapes[].reason)。中立の場合はnull。 */
  reason: string | null;
  /** adjustmentの根拠となったintentのid。中立の場合はnull。 */
  sourceIntentId: string | null;
  /** data/shapes/*.json の review_status をそのまま引き継ぐ。名前を出してよいかの
   * 判断はanalysis/nameExposure.tsに集約し、このモジュールでは判断しない。 */
  reviewStatus: ShapeFormationResult["reviewStatus"];
}

// tierの数値は「並べ替え用の内部順序」であり、prioritize/deprioritizeの間の
// 度合いを表す重みではない(常にこの3値のみ、加算も乗算もしない)。
function adjustmentTier(adjustment: TargetPurposeAdjustment["adjustment"] | null): 0 | 1 | 2 {
  if (adjustment === "prioritize") return 0;
  if (adjustment === "deprioritize") return 2;
  return 1;
}

/**
 * targetPurposeから、shapeIdごとの調整(1件)を引く索引を作る。
 * 同じshapeIdに対して複数件のadjustmentが渡された場合(想定外の入力)は、
 * 配列内で最初に現れたものを採用し、後続は無視する(何を採用したか常に
 * 決定的になるようにするための安全策。合算・上書きによる不定な挙動を避ける)。
 */
function indexTargetPurposeByShapeId(
  targetPurpose: TargetPurposeAdjustment[],
): Map<string, TargetPurposeAdjustment> {
  const index = new Map<string, TargetPurposeAdjustment>();
  for (const entry of targetPurpose) {
    if (!index.has(entry.shapeId)) {
      index.set(entry.shapeId, entry);
    }
  }
  return index;
}

/**
 * Unit5(analyzeShapeFormation)の判定結果と⑤(selectTargetPurpose)の出力から、
 * ⑥「目指せる形」の候補をランキングする。
 *
 * - side="opponent"のshapeは除外する(自分が目指す形にはなり得ないため)
 * - status="completed"のshapeは除外する(既に完成しているため)
 * - 残ったshapeを 調整区分(prioritize<中立<deprioritize) → matchScore降順 →
 *   shapeId昇順 の順で並べる(新しい数値重みは導入しない。上記コメント参照)
 *
 * shapeResultsが空、または候補が0件になった場合は空配列を返す(安全なフォールバック)。
 * 同じ入力に対しては常に同じ結果を返す(決定的)。
 */
export function rankReachableShapes(
  shapeResults: ShapeFormationResult[],
  targetPurpose: TargetPurposeAdjustment[],
): RankedReachableShape[] {
  const adjustmentByShapeId = indexTargetPurposeByShapeId(targetPurpose);

  const candidates = shapeResults
    .filter((r) => r.side !== "opponent")
    .filter((r) => r.status !== "completed")
    .map((r): RankedReachableShape => {
      const purpose = adjustmentByShapeId.get(r.shapeId);
      return {
        shapeId: r.shapeId,
        name: r.name,
        family: r.family,
        parentShapeId: r.parentShapeId,
        status: r.status,
        matchScore: r.matchScore,
        adjustment: purpose?.adjustment ?? null,
        reason: purpose?.reason ?? null,
        sourceIntentId: purpose?.sourceIntentId ?? null,
        reviewStatus: r.reviewStatus,
      };
    });

  return candidates.sort((a, b) => {
    const tierDiff = adjustmentTier(a.adjustment) - adjustmentTier(b.adjustment);
    if (tierDiff !== 0) return tierDiff;
    if (a.matchScore !== b.matchScore) return b.matchScore - a.matchScore;
    return a.shapeId.localeCompare(b.shapeId);
  });
}
