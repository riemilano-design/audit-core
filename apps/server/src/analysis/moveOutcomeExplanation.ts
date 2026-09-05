// moveOutcomeDetector.ts が抽出した事実(MoveOutcomeFact)を、初心者向けの日本語へ変換する
// (Phase6 Unit2)。事実 → 文言の対応表であり、新しい判断は一切行わない。
//
// 【文言の方針(既存の説明生成と同じ)】
// - 「最善」「おすすめ」「安全」「悪手」「形勢が良くなった」等の評価語は使わない。
//   このモジュールはエンジンの評価値を受け取らないため、そもそも評価できない。
// - 原因は、moveOutcomeDetector.tsがcauseとして確定させたものだけを述べる
//   (causeがnullなら原因に触れず、変化した事実だけを述べる)。
// - 相手の狙いの推定はしない(既存のintentDetector.ts/explanationGenerator.tsの責務)。
//
// 【座標表記】
// docs/DATA_MODEL.md「座標表記の規約」に従い、マス目はnotation/japaneseSquare.tsで
// 日本語表記へ変換する(内部データのUSI形式はそのまま保持される)。
//
// 【data/schemas/explanations.schema.json について】
// 本モジュールはschema準拠のExplanationを作らない(stageのenumに該当する値が無く、
// スキーマ変更は仕様変更にあたるため)。ShapeRouteSummaryと同じ、API/UI表示専用の型を返す。

import { toJapaneseSquare } from "../notation/japaneseSquare.js";
import type { PlanChangeReason } from "./planChangeReason.js";
import type { MoveOutcome, MoveOutcomeFact, MoveOutcomeFactKind } from "./moveOutcomeDetector.js";

export type MoveOutcomeMessageKind = MoveOutcomeFactKind | "no_notable_change";

export interface MoveOutcomeMessage {
  kind: MoveOutcomeMessageKind;
  text: string;
}

/** 事実が1件も無い場合の文言(無理に何かを言わない)。 */
export const NO_NOTABLE_CHANGE_TEXT =
  "この手のあと、目標にしている形について特に大きな変化はありませんでした。";

/**
 * 原因の文言。planChangeReason.tsが確定分類した3種のみを扱う
 * ("unknown"はmoveOutcomeDetector.ts側でnullに倒されるため、ここには来ない)。
 * 文言はweb側の既存表示(gameApi.tsのgetPlanChangeReasonMessage)と揃えている。
 */
function causeText(cause: PlanChangeReason | null): string {
  switch (cause) {
    case "candidate_piece_captured":
      return "予定していた駒が、相手の手によって取られました。";
    case "candidate_move_illegal_due_to_check":
      return "相手の手によって、予定していた玉の移動ができなくなりました。";
    case "candidate_piece_pinned":
      return "相手の手によって、予定していた駒が動かせなくなりました。";
    default:
      return "";
  }
}

/** 「銀を７八へ」のような、駒種+マスの言い回し。駒種が不明な場合はマスだけにする。 */
function pieceToSquare(fact: MoveOutcomeFact): string {
  const square = fact.targetSquare ? toJapaneseSquare(fact.targetSquare) : "";
  if (!fact.targetPiece) return square;
  return `${fact.targetPiece}を${square}へ`;
}

function factText(fact: MoveOutcomeFact): string {
  const square = fact.targetSquare ? toJapaneseSquare(fact.targetSquare) : "";
  const blocking = fact.blockingSquare ? toJapaneseSquare(fact.blockingSquare) : "";

  switch (fact.kind) {
    case "target_shape_changed":
      return "目標にする形が変わりました。ここからは新しい形について道のりを表示します。";

    case "played_candidate":
      return fact.candidateKind === "preparation"
        ? "この手は、直前に表示していた準備手の候補の一つです。"
        : "この手は、直前に表示していた候補手の一つです。";

    case "played_non_candidate":
      return "この手は、直前に表示していた候補手には含まれていませんでした。";

    case "square_completed":
      return `${square}が埋まり、この形に必要な配置の一つができました。`;

    case "square_lost":
      return `${square}にあった駒がいなくなり、この形に必要な配置の一つが崩れました。`;

    case "route_completed":
      return `この手で${fact.targetPiece ?? "駒"}が${square}に入り、この道のりは終わりました。`;

    case "route_advanced":
      return `${pieceToSquare(fact)}運ぶ道のりが、残り${fact.remainingStepsBefore}手から残り${fact.remainingStepsAfter}手になりました。`;

    case "route_lengthened":
      return `${pieceToSquare(fact)}運ぶ道のりが、残り${fact.remainingStepsBefore}手から残り${fact.remainingStepsAfter}手に増えました。`;

    case "route_lost":
      return `${pieceToSquare(fact)}運ぶ道のりが、今の局面では続けられなくなりました。`;

    case "route_first_move_unavailable":
      return `${pieceToSquare(fact)}運ぶ道のりの一手目が、今の局面では指せなくなりました。`;

    case "route_first_move_available":
      return `${pieceToSquare(fact)}運ぶ道のりの一手目が、指せるようになりました。`;

    case "preparation_required":
      return `${pieceToSquare(fact)}進めるには、先に${blocking}にある自分の駒を動かす必要が出てきました。`;

    case "preparation_resolved":
      // 「どのマスが空いたか」は述べない。準備手が不要になる理由は「塞いでいた駒が
      // どいた」だけでなく「経路自体が別ルートに変わった」場合もあり、後者では
      // そのマスは空いていない(実対局で確認済み)。検出できているのは
      // 「先に他の駒を動かす必要がなくなった」という事実までなので、そこに留める。
      return `${pieceToSquare(fact)}進めるのに、先に他の駒を動かす必要はなくなりました。`;

    case "route_assignee_changed":
      return `${square}へ向かう駒が、別の駒に変わりました。`;
  }
}

/**
 * 1件の事実を、原因の文言(あれば)を添えた1つのメッセージにする。
 * causeがnullの場合は原因に一切触れない(推測しない)。
 */
export function explainMoveOutcomeFact(fact: MoveOutcomeFact): MoveOutcomeMessage {
  const cause = causeText(fact.cause);
  const text = cause ? `${factText(fact)}${cause}` : factText(fact);
  return { kind: fact.kind, text };
}

/**
 * 直前の一手の事実一覧を、表示用のメッセージ一覧へ変換する。
 * 事実が1件も無い場合は「特に大きな変化はありませんでした」の1件を返す
 * (無言にせず、かつ推測もしない)。
 *
 * 同じ入力に対しては常に同じ結果を返す(決定的。LLMによる自由作文は行わない)。
 */
export function explainMoveOutcome(outcome: MoveOutcome): MoveOutcomeMessage[] {
  if (outcome.facts.length === 0) {
    return [{ kind: "no_notable_change", text: NO_NOTABLE_CHANGE_TEXT }];
  }
  return outcome.facts.map((fact) => explainMoveOutcomeFact(fact));
}
