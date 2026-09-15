// STEP D0-SIDE 段 2(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の F-S7・Q-2・Q-8)。**期待値は試験を回す前に手で書いた**(規則 11.1)。
// **名前はすべて架空**(実棋譜の名前を使わない)。`@` の赤の例 (a)〜(h) は KIF と CSA の両方で見る。

import { describe, expect, it } from "vitest";

import { importCsa, importKif, type KifuFormat } from "./kifuImport.js";
import { comparableName, decideUserSide, InvalidUserSideChoiceError, validateMeArgument, type UserSideDecision } from "./userSide.js";

const headerOf = (format: KifuFormat, sente: string | null, gote: string | null): string[] => [
  ...(sente === null ? [] : [format === "kif" ? `先手：${sente}` : `N+${sente}`]),
  ...(gote === null ? [] : [format === "kif" ? `後手：${gote}` : `N-${gote}`]),
];
const decide = (format: KifuFormat, sente: string | null, gote: string | null, me: string): UserSideDecision =>
  decideUserSide(format, headerOf(format, sente, gote), { me });

const decided = (side: "sente" | "gote", userHeaderRaw: string): UserSideDecision => ({ kind: "decided", side, decidedBy: "me", userHeaderRaw });
const unknown: UserSideDecision = { kind: "notDecided", reason: "user_side_unknown" };

describe.each(["kif", "csa"] as const)("decideUserSide ― %s のヘッダ(F-S7)", (format) => {
  it("--me が先手の名前だけに一致 → 先手(回さない)。本人の側の生の値だけを返す", () => {
    expect(decide(format, "テスト太郎", "相手役", "テスト太郎")).toStrictEqual(decided("sente", "テスト太郎"));
  });

  it("--me が後手の名前だけに一致 → 後手(回す)", () => {
    expect(decide(format, "相手役", "テスト太郎", "テスト太郎")).toStrictEqual(decided("gote", "テスト太郎"));
  });

  it("どちらにも一致しない → user_side_unknown", () => {
    expect(decide(format, "相手役", "別の相手", "テスト太郎")).toStrictEqual(unknown);
  });

  it("@ の規則: 「テスト太郎@▲4八銀」は --me テスト太郎 に一致し、生の値は @ 以降を含む", () => {
    expect(decide(format, "テスト太郎@▲4八銀", "相手役", "テスト太郎")).toStrictEqual(decided("sente", "テスト太郎@▲4八銀"));
  });

  it("「テスト太郎2」は --me テスト太郎 に一致しない", () => {
    expect(decide(format, "テスト太郎2", "相手役", "テスト太郎")).toStrictEqual(unknown);
  });

  it("(i) 前方一致・部分一致は一致にしない(abc2・xabc は --me abc に不一致)", () => {
    expect(decide(format, "abc2", "xabc", "abc")).toStrictEqual(unknown);
  });

  it("(ii)(h) 名前の後ろの空白・CR と、@ の前の空白は落としてから比べる(ファイルの形式の揺れ)", () => {
    expect(decide(format, "abc \r", "相手役", "abc")).toStrictEqual(decided("sente", "abc \r"));
    expect(decide(format, "相手役", "abc @x", "abc")).toStrictEqual(decided("gote", "abc @x"));
    expect(decide(format, "　abc　", "相手役", "abc")).toStrictEqual(decided("sente", "　abc　"));
  });

  it("(iii) 先手・後手の行が無いときは、名前が違うときと理由を分ける(user_side_no_header)", () => {
    expect(decide(format, null, null, "abc")).toStrictEqual({ kind: "notDecided", reason: "user_side_no_header" });
    expect(decide(format, "abc", null, "abc")).toStrictEqual({ kind: "notDecided", reason: "user_side_no_header" });
    expect(decide(format, null, "abc", "abc")).toStrictEqual({ kind: "notDecided", reason: "user_side_no_header" });
  });

  it("(iv) 先手の行が 2 本ある → user_side_unknown(どちらを採るか推測しない)", () => {
    const headers = [...headerOf(format, "abc", "相手役"), ...headerOf(format, "abc", null)];
    expect(decideUserSide(format, headers, { me: "abc" })).toStrictEqual(unknown);
  });

  it("(v) 大文字小文字だけ違う → 不一致", () => {
    expect(decide(format, "ABC", "相手役", "abc")).toStrictEqual(unknown);
  });

  it("(vi) --me で決まった側と --as が食い違う → user_side_conflict。一致すれば --me で決める。--as だけなら --as で決める", () => {
    const headers = headerOf(format, "相手役", "abc");
    expect(decideUserSide(format, headers, { me: "abc", as: "sente" })).toStrictEqual({ kind: "notDecided", reason: "user_side_conflict" });
    expect(decideUserSide(format, headers, { me: "abc", as: "gote" })).toStrictEqual(decided("gote", "abc"));
    expect(decideUserSide(format, headers, { as: "sente" })).toStrictEqual({ kind: "decided", side: "sente", decidedBy: "as", userHeaderRaw: null });
  });

  it("(a) 「@abc」は落とすと空の文字列で、--me abc に一致しない", () => {
    expect(decide(format, "@abc", "相手役", "abc")).toStrictEqual(unknown);
  });

  it("(b) @ の無い「abc」は文字列全体と完全一致", () => {
    expect(decide(format, "相手役", "abc", "abc")).toStrictEqual(decided("gote", "abc"));
  });

  it("(c) 両方の名前の @ より前が同じ(abc@▲… と abc@△…)→ 一致 2 で user_side_unknown", () => {
    expect(decide(format, "abc@▲7六歩", "abc@△3四歩", "abc")).toStrictEqual(unknown);
  });

  it("(d) 片方だけに @ があり、落とすと同じになる(abc と abc@x)→ 一致 2 で user_side_unknown", () => {
    expect(decide(format, "abc", "abc@x", "abc")).toStrictEqual(unknown);
  });

  it("(e) @ が 2 つ(a@b@c)→ 最初の @ で切って a", () => {
    expect(decide(format, "a@b@c", "相手役", "a")).toStrictEqual(decided("sente", "a@b@c"));
    expect(decide(format, "a@b@c", "相手役", "a@b".replace("@", "")).kind).toBe("notDecided");
  });

  it("(g) 全角の「＠」は @ として扱わない(abc＠x は --me abc に不一致、--me abc＠x に一致)", () => {
    expect(decide(format, "abc＠x", "相手役", "abc")).toStrictEqual(unknown);
    expect(decide(format, "abc＠x", "相手役", "abc＠x")).toStrictEqual(decided("sente", "abc＠x"));
  });
});

describe("--me そのものを確かめる(Q-8)", () => {
  it("(a)(f) 空・空白だけ・半角の @ を含む --me は止める", () => {
    for (const bad of ["", " ", "\t", "　", "abc@x", "@", "a@b"]) {
      expect(() => validateMeArgument(bad), JSON.stringify(bad)).toThrow(InvalidUserSideChoiceError);
      expect(() => decideUserSide("kif", headerOf("kif", "abc", "相手役"), { me: bad }), JSON.stringify(bad)).toThrow(InvalidUserSideChoiceError);
    }
  });

  it("全角の ＠ を含む --me は止めない", () => {
    expect(() => validateMeArgument("abc＠x")).not.toThrow();
  });

  it("--me も --as も無ければ止める", () => {
    expect(() => decideUserSide("kif", headerOf("kif", "abc", "相手役"), {})).toThrow(InvalidUserSideChoiceError);
  });
});

describe("comparableName", () => {
  it("最初の半角 @ より前を取り、前後の空白・タブ・CR・全角の空白を落とす。名前の中の空白は残す", () => {
    expect(comparableName("テスト 太郎@▲4八銀")).toBe("テスト 太郎");
    expect(comparableName(" \tabc\r")).toBe("abc");
    expect(comparableName("a@b@c")).toBe("a");
    expect(comparableName("@abc")).toBe("");
    expect(comparableName("abc＠x")).toBe("abc＠x");
  });
});

describe("(vii) 取り込みの結果のヘッダ行から決める(kifuImport を通す)", () => {
  it("KIF(CRLF): 後手の名前が --me に一致 → 後手", () => {
    const kif = ["先手：相手役", "後手：テスト太郎@△3四歩", "手合割：平手", "手数----指手---------消費時間--", "   1 ７六歩(77)", "   2 ３四歩(33)", "   3 投了", "まで2手で後手の勝ち", ""].join("\r\n");
    const result = importKif(kif);
    expect(result.kind).toBe("imported");
    const headers = result.lines.unused.filter((line) => line.kind === "header").map((line) => line.text);
    expect(decideUserSide("kif", headers, { me: "テスト太郎" })).toStrictEqual(decided("gote", "テスト太郎@△3四歩"));
  });

  it("CSA: 先手の名前が --me に一致 → 先手", () => {
    const csa = ["V2.2", "N+テスト太郎", "N-相手役", "PI", "+", "+7776FU", "-3334FU", "%TORYO", ""].join("\n");
    const result = importCsa(csa);
    expect(result.kind).toBe("imported");
    const headers = result.lines.unused.filter((line) => line.kind === "header").map((line) => line.text);
    expect(decideUserSide("csa", headers, { me: "テスト太郎" })).toStrictEqual(decided("sente", "テスト太郎"));
  });
});
