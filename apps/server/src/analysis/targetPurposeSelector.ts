// IntentDetectionResult[] (Unit2, intentDetector.ts) -> ⑤自分の目的 への変換。
// docs/DATA_MODEL.md の教育用データパイプライン⑤(自分の目的)を実装する。
// ⑤⑥はDATA_MODEL.mdが明記する通り「ロジック側が実行時に算出し、静的データとしては
// 持たない」ため、data/配下への新規追加は行わない。
//
// 【将棋知識について】このモジュールは新しい将棋知識を一切作らない。
// data/intents/*.json の affects_target_shapes(人間レビュー済み・既存フィールド)を
// そのまま読み替えるだけであり、優先度の意味づけ(prioritize/deprioritizeが何を
// 意味するか)は intents データ自体が既に持っている。
//
// 【「どの意図を採用するか」の設計判断】
// 複数のintentが同時にmatchScore>0(=何らかの兆候がある)状態になり得るが、
// それらのaffects_target_shapesを無条件に合算すると「複数の意図をどう重み付けして
// 混ぜるか」という、既存データからは導けない新しい判断が必要になってしまう
// (ユーザー指示: 根拠のない数値的な重み付けを勝手に導入しない)。
// そこで、explanationGenerator.ts の buildOpponentIntentStage が③(相手の意図)の
// 説明として「最も一致度の高い1件」だけを採用しているのと同じ設計方針を踏襲し、
// ⑤(自分の目的)も「その1件のintentが示すaffects_target_shapes」だけを採用する。
// これにより③→⑤の対応が一貫し、新しい合成ルールを発明せずに済む。
//
// 「最も一致度の高い1件」の決定は、intentDetector.tsの既存のソート規約
// (matchScore降順、同点はintentId昇順)と同じ基準で本モジュール内でも決定的に行う
// (呼び出し側がdetectIntents()のソート済み結果を渡すとは限らないため、
// ソート順に依存せず本モジュール内で選び直す)。

import type { AffectsTargetShape } from "./intentRepository.js";
import type { IntentDetectionResult } from "./intentDetector.js";

export interface TargetPurposeAdjustment {
  /** data/shapes/*.json の shapes.id */
  shapeId: string;
  adjustment: AffectsTargetShape["adjustment"];
  /** intents.affects_target_shapes[].reason(既存データそのまま、無ければ空文字) */
  reason: string;
  /** この調整の根拠となったintentのid(data/intents/*.json のintents.id) */
  sourceIntentId: string;
}

/**
 * matchScore>0のintentのうち、最も一致度の高い1件を選ぶ。
 * intentDetector.tsのdetectIntents()と同じ基準(matchScore降順、同点はintentId昇順)で
 * 決定的に選ぶ。matchScore>0のintentが1つも無ければundefinedを返す
 * (=相手の意図がまだ何も観測されていない場合の安全なフォールバック)。
 */
function selectBestIntent(intentResults: IntentDetectionResult[]): IntentDetectionResult | undefined {
  const candidates = intentResults.filter((r) => r.matchScore > 0);
  if (candidates.length === 0) return undefined;

  return candidates.reduce((best, cur) => {
    if (cur.matchScore > best.matchScore) return cur;
    if (cur.matchScore < best.matchScore) return best;
    return cur.intentId < best.intentId ? cur : best;
  });
}

/**
 * Unit2(detectIntents)の判定結果から、⑤「自分の目的」を組み立てる。
 * 「今、自分がどの形を優先的に目指すべきか/後回しにすべきか」を、最も一致度の高い
 * intentのaffects_target_shapesからそのまま導く。
 *
 * intentResultsが空、またはmatchScore>0のintentが1つも無い場合は空配列を返す
 * (=特定の意図が観測されていないときは、目的の調整も行わない安全なフォールバック)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。新しい将棋知識・数値重みは追加しない)。
 */
export function selectTargetPurpose(intentResults: IntentDetectionResult[]): TargetPurposeAdjustment[] {
  const best = selectBestIntent(intentResults);
  if (!best) return [];

  const affectsTargetShapes = best.affectsTargetShapes ?? [];
  return affectsTargetShapes.map((entry) => ({
    shapeId: entry.shape_id,
    adjustment: entry.adjustment,
    reason: entry.reason ?? "",
    sourceIntentId: best.intentId,
  }));
}
