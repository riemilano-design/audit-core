// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の 1.・F-S7・Q-2・Q-8)。棋譜のヘッダの名前から、本人が先手か後手かを決める。
//
// 【比べ方(司令塔の決定)】
// - KIF は `先手：` / `後手：`(半角の `:` も同じ)、CSA は `N+` / `N-` の行の値を使う
// - 値から**最初の半角 `@` 以降を落とし**、**前後の空白・タブ・CR・全角の空白を落として**から、`--me` と**完全一致**で比べる
//   (空白と CR を落とすのはファイルの形式の揺れであって、名前の表記ゆれの吸収ではない。大文字小文字などは吸収しない)
// - **全角の `＠` は `@` として扱わない**
// - 先手・後手の行のどちらかが無い → `user_side_no_header`。どちらかが 2 本以上ある・一致が 0 か 2 → `user_side_unknown`
//   (推測しない)。`--me` で決まった側と `--as` が食い違う → `user_side_conflict`
// - `--me` が空・空白だけ・半角の `@` を含む → **止める**(`InvalidUserSideChoiceError`)
//
// 【このファイルが絶対にやらないこと】
// - 相手の名前を返すこと。**返すのは本人の側の生の値だけ**(`userHeaderRaw`)。相手の名前は記録にも報告にも残さない(計画 8.)
// - `--me` で決まらなかった局を `--as` で決め直すこと(`--me` を渡したなら `--me` の結果に従う)

import type { KifuFormat } from "./kifuImport.js";

export type UserSide = "sente" | "gote";

export type UserSideNotDecidedReason = "user_side_unknown" | "user_side_no_header" | "user_side_conflict";

export type UserSideDecision =
  /** `userHeaderRaw` は `--me` で決めたときの本人の側のヘッダの値(落とす前の生の文字列)。`--as` だけで決めたときは null(ヘッダを見ていない) */
  | { kind: "decided"; side: UserSide; decidedBy: "me" | "as"; userHeaderRaw: string | null }
  | { kind: "notDecided"; reason: UserSideNotDecidedReason };

export class InvalidUserSideChoiceError extends Error {}

const NAME_LINES: Record<KifuFormat, Record<UserSide, RegExp>> = {
  // 値は [\s\S]* で取る(. は CR にも一致しないので、行末に CR が残った行を名前の行として読み落とす)
  kif: { sente: /^\s*先手[：:]([\s\S]*)$/, gote: /^\s*後手[：:]([\s\S]*)$/ },
  csa: { sente: /^N\+([\s\S]*)$/, gote: /^N-([\s\S]*)$/ },
};

const EDGE_BLANKS = /^[ \t\r　]+|[ \t\r　]+$/g;

/** ヘッダの行(kifuImport の「読んだが使わない」header の text)から、先手・後手の名前の値を行の順に取り出す。 */
export function nameHeaderValues(format: KifuFormat, headerTexts: readonly string[]): Record<UserSide, string[]> {
  const pick = (side: UserSide) =>
    headerTexts.flatMap((text) => {
      const match = NAME_LINES[format][side].exec(text);
      return match ? [match[1]!] : [];
    });
  return { sente: pick("sente"), gote: pick("gote") };
}

/** 比べる部分: 最初の半角 `@` より前を取り、前後の空白・タブ・CR・全角の空白を落とす。 */
export function comparableName(value: string): string {
  const at = value.indexOf("@");
  return (at >= 0 ? value.slice(0, at) : value).replace(EDGE_BLANKS, "");
}

/** `--me` の値を確かめる。空・空白だけ・半角の `@` を含むなら止める(Q-8)。 */
export function validateMeArgument(me: string): void {
  if (me.replace(EDGE_BLANKS, "").length === 0) throw new InvalidUserSideChoiceError("--me が空か空白だけです");
  if (me.includes("@")) throw new InvalidUserSideChoiceError(`--me に半角の @ が入っています(名前の後ろを @ で切る規則とぶつかるので、推測せずに止めます): "${me}"`);
}

export function decideUserSide(
  format: KifuFormat,
  headerTexts: readonly string[],
  choice: { me?: string; as?: UserSide },
): UserSideDecision {
  if (choice.me === undefined) {
    if (choice.as === undefined) throw new InvalidUserSideChoiceError("--me か --as のどちらかを渡してください");
    return { kind: "decided", side: choice.as, decidedBy: "as", userHeaderRaw: null };
  }
  validateMeArgument(choice.me);

  const values = nameHeaderValues(format, headerTexts);
  if (values.sente.length === 0 || values.gote.length === 0) return { kind: "notDecided", reason: "user_side_no_header" };
  if (values.sente.length > 1 || values.gote.length > 1) return { kind: "notDecided", reason: "user_side_unknown" };

  const senteMatches = comparableName(values.sente[0]!) === choice.me;
  const goteMatches = comparableName(values.gote[0]!) === choice.me;
  if (senteMatches === goteMatches) return { kind: "notDecided", reason: "user_side_unknown" };

  const side: UserSide = senteMatches ? "sente" : "gote";
  if (choice.as !== undefined && choice.as !== side) return { kind: "notDecided", reason: "user_side_conflict" };
  return { kind: "decided", side, decidedBy: "me", userHeaderRaw: values[side][0]! };
}
