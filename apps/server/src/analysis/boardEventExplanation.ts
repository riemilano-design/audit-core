// boardEventDetector.ts が確定させた盤面の出来事(捕獲・王手・成り)を、
// 初心者向けの日本語へ変換する(Phase6 Unit3)。事実 → 文言の対応表であり、
// 新しい判断は一切行わない。
//
// 【文言の方針】
// 起きたことだけを述べる。「損をした」「危険です」「取り返しましょう」「良い手」
// といった評価・推奨・損得の判断は一切しない(このモジュールはそれを判断できる情報を
// 受け取っていない)。エンジンの評価値にも触れない。
//
// 【座標表記】
// docs/DATA_MODEL.md の座標表記の規約に従い、マス目はnotation/japaneseSquare.tsで
// 日本語表記へ変換する(内部データのUSI形式はそのまま)。
//
// 【data/schemas/explanations.schema.json について】
// moveOutcomeExplanation.tsと同じ理由で、schema準拠のExplanationは作らない
// (stageのenumに該当する値が無く、スキーマ変更は仕様変更にあたるため)。
// API/UI表示専用の型を返す。

import { toJapaneseSquare } from "../notation/japaneseSquare.js";
import type { BoardEvent, BoardEventKind } from "./boardEventDetector.js";

export interface BoardEventMessage {
  kind: BoardEventKind;
  text: string;
}

/** 「７六の歩」のような言い回し。駒種が確定していない場合はマスだけにする。 */
function squareAndPiece(event: BoardEvent): string {
  const square = event.square ? toJapaneseSquare(event.square) : "";
  if (!event.piece) return `${square}にあった駒`;
  return `${square}の${event.piece}`;
}

function eventText(event: BoardEvent): string {
  switch (event.kind) {
    case "captured_by_you":
      return `この手で、相手の${squareAndPiece(event)}を取りました。`;

    case "captured_by_opponent":
      return `相手の手で、あなたの${squareAndPiece(event)}が取られました。`;

    case "check_given":
      return "この手で、相手の玉に王手がかかりました。";

    case "check_received":
      return "相手の手で、あなたの玉に王手がかかっています。";

    case "promoted_by_you": {
      const square = event.square ? toJapaneseSquare(event.square) : "";
      return event.piece
        ? `この手で、${event.piece}が${square}で成りました。`
        : `この手で、${square}の駒が成りました。`;
    }

    case "promoted_by_opponent": {
      const square = event.square ? toJapaneseSquare(event.square) : "";
      return event.piece
        ? `相手の手で、${event.piece}が${square}で成りました。`
        : `相手の手で、${square}の駒が成りました。`;
    }
  }
}

/** 出来事1件を表示用メッセージに変換する。 */
export function explainBoardEvent(event: BoardEvent): BoardEventMessage {
  return { kind: event.kind, text: eventText(event) };
}

/**
 * 盤面の出来事の一覧を、表示用メッセージの一覧へ変換する。
 * 出来事が無ければ空配列を返す(何も無かったことをここで言葉にはしない。
 * 「特に変化なし」の文言はmoveOutcomeExplanation.tsが担当する)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function explainBoardEvents(events: BoardEvent[]): BoardEventMessage[] {
  return events.map((event) => explainBoardEvent(event));
}
