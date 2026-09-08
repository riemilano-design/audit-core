// nextConsiderationDetector.ts が確定させた「今の局面で分かっていること」を、
// 初心者向けの日本語へ変換する(Phase6 Unit4)。事実 → 文言の対応表であり、
// 新しい判断は一切行わない。
//
// 【文言の方針】
// 現在の局面について確定していることだけを述べる。「最善」「おすすめ」「悪手」
// 「危険」「警戒」「取り返す」「有利/不利」「損得」といった評価・推奨は一切しない
// (このモジュールはそれを判断できる情報を受け取っていない)。エンジンの評価値にも
// 触れない。相手の意図・狙いにも触れない(Phase1のcoachブロックの責務)。
//
// 【並び順の注記について】
// 指せる一手を複数並べるとき、その順序が「手の良し悪しの順」だと誤解されないよう、
// 並び順の根拠を明記する注記を最後に付ける(人間承認済みの文言)。
// 注記は局面についての事実ではなく表示上の説明のため、detector側の事実には含めず、
// このモジュールが表示の一部として付け足す。
//
// 【座標・指し手の表記】
// docs/DATA_MODEL.md の座標表記の規約に従い、マス目は notation/japaneseSquare.ts、
// 指し手は notation/japaneseMove.ts で日本語表記へ変換する(内部データのUSI形式は
// そのまま)。表記ロジックはこのモジュールには持たない。
//
// 【data/schemas/explanations.schema.json について】
// moveOutcomeExplanation.ts / boardEventExplanation.ts と同じ理由で、schema準拠の
// Explanationは作らない(stageのenumに該当する値が無く、スキーマ変更は仕様変更に
// あたるため)。API/UI表示専用の型を返す。

import { toJapaneseMove } from "../notation/japaneseMove.js";
import { toJapaneseMoveSquares, toJapaneseSquare } from "../notation/japaneseSquare.js";
import type { NextConsiderationFact, NextConsiderationKind } from "./nextConsiderationDetector.js";
import { exposeName } from "./nameExposure.js";

/** 表示メッセージの種類。事実の種類に、表示上の注記(ordering_note)を加えたもの。 */
export type NextConsiderationMessageKind = NextConsiderationKind | "ordering_note";

export interface NextConsiderationMessage {
  kind: NextConsiderationMessageKind;
  text: string;
}

/** 並び順の注記を出す最小件数(「複数」= 2件以上)。 */
const ORDERING_NOTE_MIN_COUNT = 2;

/**
 * 指し手の表示表記を決める。棋譜表記(例: "７八銀")が作れる場合はそれを使い、
 * 作れない場合のみマス目表記(例: "７九→７八")へフォールバックする
 * (どちらも既存の変換関数で、推測した表記は作らない)。
 */
function moveLabel(sfen: string, moveUsi: string): string {
  return toJapaneseMove(sfen, moveUsi) ?? toJapaneseMoveSquares(moveUsi);
}

/**
 * 事実1件を文言へ変換する。文言を組み立てるのに必要な値が欠けている場合はnullを返し、
 * 欠けた部分を推測して補わない(呼び出し側がその事実を表示しない)。
 */
function factText(fact: NextConsiderationFact, sfen: string): string | null {
  switch (fact.kind) {
    case "in_check":
      return "今、あなたの玉に王手がかかっています。ルール上、王手を解消する手しか指せません。";

    case "route_first_move_playable": {
      if (fact.moveUsi === null || fact.targetPiece === null || fact.targetSquare === null) return null;
      const square = toJapaneseSquare(fact.targetSquare);
      return `${moveLabel(sfen, fact.moveUsi)}は、${fact.targetPiece}を${square}へ向かわせる道のりの一手目です。`;
    }

    case "no_playable_route_first_move":
      return "今の局面では、選んだ形へ向かう道のりの一手目を、どれも指すことができません。";

    case "shape_completed": {
      if (fact.shapeName === null) return null;
      // fact.shapeNameがある場合、契約上fact.shapeReviewStatusも必ず伴う
      // (nextConsiderationDetector.ts参照)。名前を出してよいかの判断は
      // analysis/nameExposure.tsに集約する(露出経路5、STEP ζ-5)。
      const exposed = exposeName(fact.shapeName, fact.shapeReviewStatus ?? "draft", "squares");
      const suffix = exposed.pendingNote === null ? "" : `(${exposed.pendingNote})`;
      return `「${exposed.name}」${suffix}に必要なマスは、すべて埋まっています。`;
    }
  }
}

/**
 * 事実の並び(detectorが確定させた表示順)を、そのままの順序で文言へ変換する。
 * 指せる一手を2件以上並べる場合のみ、末尾に並び順の注記を付ける。
 *
 * sfen は、指し手を棋譜表記へ変換するための現在の局面(その手を指す前の局面)。
 */
export function explainNextConsiderations(
  facts: NextConsiderationFact[],
  sfen: string,
): NextConsiderationMessage[] {
  const messages: NextConsiderationMessage[] = [];

  for (const fact of facts) {
    const text = factText(fact, sfen);
    if (text === null) continue;
    messages.push({ kind: fact.kind, text });
  }

  const playableCount = messages.filter((m) => m.kind === "route_first_move_playable").length;
  if (playableCount >= ORDERING_NOTE_MIN_COUNT) {
    messages.push({
      kind: "ordering_note",
      text: "残り手数の少ない順に並べています。手の良し悪しの順ではありません。",
    });
  }

  return messages;
}
