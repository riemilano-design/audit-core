// 「指し手履歴の中に、特定の手番・駒種・移動先に一致する手が存在するか」という
// 判定だけを担う共通ヘルパー。
//
// intentDetector.ts(Unit2: intents.recognition_patternとの一致判定)と
// shapeFormationAnalyzer.ts(Unit5: shapes.required_piecesへ向かう実際の駒の動きの
// 証拠判定)の両方が、本質的に同じ「駒種+移動先が指し手履歴のどこかに存在するか
// (順序は問わない)」という判定を必要とするため、ここに1箇所へ集約する
// (docs/ROLES.mdの言う「重複ロジックを作らない」に対応)。

import type { Color, Role } from "shogiops/types";
import type { MoveEvent } from "./moveHistory.js";

export interface SignatureEvidence {
  ply: number;
  moveUsi: string;
}

/**
 * 指し手履歴(MoveEvent[])の中から、指定した手番・駒種・移動先に一致する手を探す。
 * 一致する手が複数ある場合は最初に見つかったもの(手数が早い方)を返す。
 * 順序(いつ起きたか)そのものは問わない、断片的な証拠探しである点に注意
 * (intents.recognition_patternが「順不同でも良い断片的なシグネチャ」であるのと同じ考え方)。
 */
export function findMoveEvidence(
  events: MoveEvent[],
  color: Color,
  role: Role,
  toSquare: string,
): SignatureEvidence | undefined {
  const match = events.find((event) => event.color === color && event.role === role && event.toSquare === toSquare);
  return match ? { ply: match.ply, moveUsi: match.moveUsi } : undefined;
}
