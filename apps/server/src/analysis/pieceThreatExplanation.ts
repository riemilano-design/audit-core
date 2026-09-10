// pieceThreatDetector.ts が確定させた「駒が当たっている」事実を、初心者向けの
// 日本語(STEP 4-3・2026-09-10 人間承認: C-1)へ変換する。事実 → 文言の対応表であり、
// 新しい判断は一切行わない([../../../../docs/ARCHITECTURE.md](../../../../docs/ARCHITECTURE.md) 4.3)。
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

/** [0]「今すぐ対処が必要なこと」に出す、駒が当たっている事実のメッセージ種別。 */
export type PieceThreatMessageKind = "piece_attacked";

export interface PieceThreatMessage {
  kind: PieceThreatMessageKind;
  text: string;
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

/**
 * 事実1件を文言へ変換する。自分の駒・攻め駒のいずれの名前も解決できない場合はnullを返し、
 * 呼び出し側がその事実を表示しない(推測して名前を補わない)。
 */
function factText(fact: PieceThreatFact): string | null {
  const ownName = pieceName(fact.role);
  if (ownName === null) return null;

  const attackers = toNamedAttackers(fact.attackers);
  if (attackers.length === 0) return null;

  const ownSquare = toJapaneseSquare(fact.square);
  return `あなたの${ownSquare}の${ownName}に、${attackerPhrase(attackers)}当たっています(次の相手の手で取られる可能性があります)。`;
}

/**
 * pieceThreatDetector.ts が確定させた並び順(D)を、そのままの順序で文言へ変換する。
 * 並び替え・フィルタはdetector側の責務であり、ここでは行わない。
 */
export function explainPieceThreats(facts: PieceThreatFact[]): PieceThreatMessage[] {
  const messages: PieceThreatMessage[] = [];
  for (const fact of facts) {
    const text = factText(fact);
    if (text === null) continue;
    messages.push({ kind: "piece_attacked", text });
  }
  return messages;
}
