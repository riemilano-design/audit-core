// pieceThreatDetector.ts が確定させた「駒が当たっている」事実を、初心者向けの
// 日本語(STEP 4-3・2026-09-10 人間承認: C-1)へ変換する。事実 → 文言の対応表であり、
// 新しい判断は一切行わない([../../../../docs/ARCHITECTURE.md](../../../../docs/ARCHITECTURE.md) 4.3)。
//
// 【STEP 5-E(H-2・2026-09-12人間承認)で追加した「どちらもできない」の一文】
// 帯が名指しした駒について、次の2つの事実のときだけ、文の末尾に1文を足す。
// - その駒の合法手が1つも無い: 「この駒は今、動かせるマスがありません。」
// - 合法手はあるが、移動先すべてに相手の駒が届く:
//   「この駒が動けるマスは、どれも相手の駒が届いています。」
// 判定(合法手の有無・移動先が届くかどうか)は一切ここで行わない。
// analysis/escapeSquareThreat.ts が既に集計した結果(PieceEscapeSquareStatus)を
// square(自分の駒のマス)ごとの対応表として引数で受け取り、このモジュールは
// その結果からどちらの文言を足すか(あるいは何も足さないか)を選ぶだけ。
//
// 【文言の方針(C-1)】
// 「あなたの{マス}の{駒名}に、相手の{マス}の{駒名}が当たっています
// (次の相手の手で取られる可能性があります)。」
// 相手の駒が複数のときは「相手の{マス}の{駒名}と{マス}の{駒名}が」と「と」で並べる。
// 「危険」「取り返せる」「守る」といった評価語は使わない(このモジュールはそれを
// 判断できる情報を受け取っていない)。
//
// 【駒名の表記(H-1・2026-09-10 人間承認)】
// 基本駒8種は既存の analysis/pieceMapping.ts の roleToJapanese を使う(共有の対応表は
// 変更しない)。成駒6種(龍・馬・と金・成銀・成桂・成香)は、そのままの標準的な駒名を
// このモジュール内の小さな表で表示する。自分の駒・相手の攻め駒の両方に同じ表を使う。
// 名前が解決できない役職(標準将棋には現れない想定外の役職)は、その事実の行を出さない
// (推測して名前を付けない)。
//
// 【座標の表記】
// マス目は notation/japaneseSquare.ts の toJapaneseSquare で変換する
// (docs/DATA_MODEL.md の座標表記の規約)。

import type { Role } from "shogiops/types";
import { toJapaneseSquare } from "../notation/japaneseSquare.js";
import { roleToJapanese } from "./pieceMapping.js";
import type { PieceThreatAttacker, PieceThreatFact } from "./pieceThreatDetector.js";
import type { PieceEscapeSquareStatus } from "./escapeSquareThreat.js";

/** [0]「今すぐ対処が必要なこと」に出す、駒が当たっている事実のメッセージ種別。 */
export type PieceThreatMessageKind = "piece_attacked";

export interface PieceThreatMessage {
  kind: PieceThreatMessageKind;
  text: string;
  /** 当たっている自分の駒のマス(USI形式)。fact.squareをそのまま写す。 */
  square: string;
  /**
   * 当てている相手の駒のマス(USI形式)。fact.attackersの並び順のまま。
   * 名前が解決できず文から落ちた攻め駒(toNamedAttackersの結果)は除く。
   */
  attackerSquares: string[];
}

/**
 * 成駒6種の日本語表記(H-1)。analysis/pieceMapping.ts の ROLE_TO_JAPANESE(基本駒8種のみ)
 * を変更せず、成駒はこの新モジュール内の別表で扱う。
 */
const PROMOTED_ROLE_TO_JAPANESE: Partial<Record<Role, string>> = {
  dragon: "龍",
  horse: "馬",
  tokin: "と金",
  promotedsilver: "成銀",
  promotedknight: "成桂",
  promotedlance: "成香",
};

/**
 * 役職を日本語の駒名へ変換する。基本駒8種はroleToJapanese、成駒6種はPROMOTED_ROLE_TO_JAPANESE。
 * どちらにも無い役職はnull(呼び出し側はその事実を表示しない)。
 */
function pieceName(role: Role): string | null {
  return roleToJapanese(role) ?? PROMOTED_ROLE_TO_JAPANESE[role] ?? null;
}

interface NamedAttacker {
  square: string;
  name: string;
}

function toNamedAttackers(attackers: PieceThreatAttacker[]): NamedAttacker[] {
  return attackers
    .map((attacker) => {
      const name = pieceName(attacker.role);
      return name === null ? null : { square: attacker.square, name };
    })
    .filter((attacker): attacker is NamedAttacker => attacker !== null);
}

/** 「相手の{マス}の{駒名}と{マス}の{駒名}が」の部分を組み立てる(1件でも複数でも対応)。 */
function attackerPhrase(attackers: NamedAttacker[]): string {
  const parts = attackers.map((attacker) => `${toJapaneseSquare(attacker.square)}の${attacker.name}`);
  return `相手の${parts.join("と")}が`;
}

interface FactMessage {
  text: string;
  attackerSquares: string[];
}

/**
 * STEP 5-E(H-2)。「どちらもできない」の一文(人間承認済み。一字も変えないこと)。
 * 「利いています」は使わない(「利き」は将棋用語のためルール2番に当たる。帯の既存文
 * 「当たっています」に合わせて「届いています」にする、という2026-09-12人間決定)。
 */
const NO_LEGAL_MOVES_TEXT = "この駒は今、動かせるマスがありません。";
const ALL_DESTINATIONS_ATTACKED_TEXT = "この駒が動けるマスは、どれも相手の駒が届いています。";

/**
 * escapeStatusが示す2つの事実のうち、どちらかに当てはまれば末尾に1文を足す。
 * どちらにも当てはまらない(escapeStatusが無い場合を含む)ときは何も足さない。
 * 判定(合法手の有無・移動先が届くか)は一切ここで行わず、既に計算済みの
 * escapeStatusを読むだけ。
 */
function appendEscapeSquareSentence(text: string, escapeStatus: PieceEscapeSquareStatus | undefined): string {
  if (escapeStatus === undefined) return text;
  if (escapeStatus.hasNoLegalMoves) return `${text}${NO_LEGAL_MOVES_TEXT}`;
  if (escapeStatus.allDestinationsAttacked) return `${text}${ALL_DESTINATIONS_ATTACKED_TEXT}`;
  return text;
}

/**
 * 事実1件を文言へ変換する。自分の駒・攻め駒のいずれの名前も解決できない場合はnullを返し、
 * 呼び出し側がその事実を表示しない(推測して名前を補わない)。
 */
function factText(fact: PieceThreatFact, escapeStatus: PieceEscapeSquareStatus | undefined): FactMessage | null {
  const ownName = pieceName(fact.role);
  if (ownName === null) return null;

  const attackers = toNamedAttackers(fact.attackers);
  if (attackers.length === 0) return null;

  const ownSquare = toJapaneseSquare(fact.square);
  const baseText = `あなたの${ownSquare}の${ownName}に、${attackerPhrase(attackers)}当たっています(次の相手の手で取られる可能性があります)。`;
  const text = appendEscapeSquareSentence(baseText, escapeStatus);
  return { text, attackerSquares: attackers.map((attacker) => attacker.square) };
}

/**
 * pieceThreatDetector.ts が確定させた並び順(D)を、そのままの順序で文言へ変換する。
 * 並び替え・フィルタはdetector側の責務であり、ここでは行わない。
 *
 * escapeStatusesは、STEP 5-E(H-2)の一文を足すかどうかの判定材料(square →
 * PieceEscapeSquareStatus)。呼び出し側(analysis/escapeSquareThreat.ts の
 * summarizeEscapeSquareThreatsForSquare)が既に計算した結果をそのまま渡すだけで、
 * このモジュール自身は合法手や利きの判定を一切行わない。渡さない場合は何も足さない
 * (STEP 4-3時点の既存呼び出しとの後方互換)。
 */
export function explainPieceThreats(
  facts: PieceThreatFact[],
  escapeStatuses: ReadonlyMap<string, PieceEscapeSquareStatus> = new Map(),
): PieceThreatMessage[] {
  const messages: PieceThreatMessage[] = [];
  for (const fact of facts) {
    const result = factText(fact, escapeStatuses.get(fact.square));
    if (result === null) continue;
    messages.push({
      kind: "piece_attacked",
      text: result.text,
      square: fact.square,
      attackerSquares: result.attackerSquares,
    });
  }
  return messages;
}
