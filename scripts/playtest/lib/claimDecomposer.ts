// D-2b(audit-core/docs/CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §2(a))。
// 「分解器」― `original_text`(文字列)だけを受け取り、LLM を 1 回呼んで claim-decomposition v0.1 文書を作る。
//
// 【範囲】計画 §1「範囲を絞る」のとおり、packet も席(seat)の封筒も使わない。分解層だけを純粋に測る。
//   `lib/seatRun.ts` の `runSlot`(1 回の LLM 呼び出しの器 ― 送る前の費用上限の判定・`countTokens` の概算・
//   schema 再試行・理由の累積・保存物)をそのまま再利用する(新しく書き直さない)。
// 【唯一の出口】`checkClaimDecomposition` を通ったものだけを返す ― schema と `decompositionProblems` の
//   **両方**。`runSlot` の `ctx.validateLlm` に `checkClaimDecomposition(...).problems` をそのまま渡す。
// 【再試行】`runSlot` の `SCHEMA_RETRY_LIMIT`(= 2。計 3 試行)をそのまま使う ― 新しい上限を作らない。
//   理由は `runSlot` 内で**累積**される(前回の返答は渡さない。直前の理由だけでなくこれまでの理由を
//   全部渡す ― 2026-10-01 の実測で「直前の分だけでは往復する」ことが分かっているため)。
// 【落ちた試行の理由】`runSlot` が `files`(`SavedFile[]`)として `*_problems.txt` を返す。呼び出し側
//   (CLI)がそれを保存する。
// 【費用】上限は呼び出し側(CLI)が環境変数 `DECOMPOSE_COST_CAP_USD` から読み、`capUsd` に渡す。
//   上限に達したら `runSlot` が `capReached: true` の空席として返す(送らない)。このファイルは
//   上限の値そのものには関与しない(環境変数を読むのは CLI の責務)。
// 【original_text の書き写し】schema は `original_text` を LLM の出力にも含めることを要求する
//   (`checkClaimDecomposition` が、申告された span が「その doc の `original_text`」に実在するかを
//   確かめるため)。LLM が一字一句正確に書き写さなかった場合、span の実在チェックが**真の原文**に対して
//   行われていないことになるため、`validateDecomposerOutput` は schema 検査の前に
//   `original_text === 入力した原文` を確かめ、不一致なら再試行させる。
//
// 【このファイルが絶対にやらないこと】
// - `runSlot`・`checkClaimDecomposition`・`decompositionCompare` の挙動を変えること(呼ぶだけ)。
// - LLM の呼び出し(このファイルは関数を提供するだけで、実行は呼び出し側 CLI が行う)。
// - 実際の API 呼び出し(このファイル自身は `deps.fetch` を注入されるだけで、どの fetch を使うかは関与しない)。

import { createHash } from "node:crypto";
import { checkClaimDecomposition, loadClaimDecompositionSchema } from "./claimDecomposition.js";
import { runSlot, type SlotConfig, type SlotDeps, type SlotRunResult } from "./seatRun.js";

type Rec = Record<string, unknown>;

function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/**
 * 分解器の指示文の sha256(司令塔ではなく実装担当が固定。2026-10-07)。
 * **1 バイトでも変えるなら版名を上げる ― 同じ版名で中身を差し替えない**(`lib/seatRun.ts` の
 * `FIXED_INSTRUCTION_SHA256` と同じ規律。ただしあちらの表は seat 向けの指示文専用のため、
 * 分解器の指示文はこの表を別に持つ)。
 */
export const DECOMPOSER_INSTRUCTION_SHA256: Readonly<Record<string, string>> = {
  "CLAIM_DECOMPOSER_INSTRUCTION_v1_2026-10-07.md": "d5bbde9999d9fbdbaa4b92f224bb6126f44ce5e7d88be8341308388522f46843",
};

/** 指示文 1 本の sha を固定値と照合する。表に無い名前も誤り(固定していない文で分解器に聞かない)。 */
export function decomposerInstructionShaProblems(basename: string, content: Buffer | string): string[] {
  const expected = DECOMPOSER_INSTRUCTION_SHA256[basename];
  const actual = createHash("sha256")
    .update(typeof content === "string" ? Buffer.from(content, "utf-8") : content)
    .digest("hex");
  if (expected === undefined) return [`${basename}: この指示文の sha が固定されていない(固定してから配る。版名を上げたら表に足す)`];
  if (expected !== actual) {
    return [`${basename}: sha が固定値と違う(${actual.slice(0, 8)}… / 固定 ${expected.slice(0, 8)}…)。1 バイトでも変えるなら版名を上げる`];
  }
  return [];
}

export const DECOMPOSER_SCHEMA_NAME = "submit_claim_decomposition" as const;

/**
 * user 本文の決まった前後(定数で固定し、`decomposerUserText` と `originalTextFromDecomposerUserText` の
 * 両方がこの同じ定数を見る ― 片方だけ直して食い違う事故を防ぐ。下見(`claimDecomposerDryRun.ts`)が
 * 「どの原文を聞かれたか」を HTTP 要求の本文から復元するのに使う)。
 */
export const DECOMPOSER_USER_PREFIX =
  "分解してほしい原文(original_text)は次のとおりです。これを 1 文字も変えずに `original_text` へ書き写し、`claims[]` を作ってください。\n\n---\n";
export const DECOMPOSER_USER_SUFFIX = "\n---\n";

/** LLM へ渡す user 本文(原文をそのまま後ろに続ける)。 */
export function decomposerUserText(originalText: string): string {
  return `${DECOMPOSER_USER_PREFIX}${originalText}${DECOMPOSER_USER_SUFFIX}`;
}

/**
 * `decomposerUserText` の逆操作。前後の決まった文で挟まれていない(= この関数が作った形ではない)
 * 文字列を渡されたら `undefined`(下見のダミー応答作りだけに使う。本番の判定には使わない)。
 */
export function originalTextFromDecomposerUserText(userText: string): string | undefined {
  if (!userText.startsWith(DECOMPOSER_USER_PREFIX) || !userText.endsWith(DECOMPOSER_USER_SUFFIX)) return undefined;
  if (userText.length < DECOMPOSER_USER_PREFIX.length + DECOMPOSER_USER_SUFFIX.length) return undefined;
  return userText.slice(DECOMPOSER_USER_PREFIX.length, userText.length - DECOMPOSER_USER_SUFFIX.length);
}

/**
 * 分解器の出力を検査する関数を作る(`runSlot` の `ctx.validateLlm` に渡す形)。
 * (1) `original_text` が入力した原文と一字一句一致するか、(2) `checkClaimDecomposition`
 * (schema + decompositionProblems の両方)を確かめる。問題が 1 つも無いときだけ `runSlot` は成功を返す。
 */
export function validateDecomposerOutput(originalText: string): (json: unknown) => string[] {
  return (json: unknown): string[] => {
    if (!isRecord(json)) return ["doc がオブジェクトではない"];
    const problems: string[] = [];
    if (typeof json.original_text !== "string") {
      problems.push("original_text が文字列ではない");
    } else if (json.original_text !== originalText) {
      problems.push("original_text が入力した原文と一致しない(原文を 1 文字も変えずに書き写すこと)");
    }
    problems.push(...checkClaimDecomposition(json).problems);
    return problems;
  };
}

export interface DecomposeConfig extends SlotConfig {
  capUsd: number;
  /** この呼び出しより前に使った見込み(複数本を続けて呼ぶときの累計上限のため)。既定 0。 */
  cumulativeCostUsd?: number;
}

/**
 * 単価が `.env` に無いまま本番へ進まないための門(`runSeats.ts` の `seatsMissingPrices` → 呼び出し元の
 * `throw` と同じ規律の個別席版。独立監査の所見 2026-10-07: この門が無いと `costUsd` が常に 0 を返し、
 * `budgetDecision` の上限判定が永久に `ok` になる)。呼び出し元(CLI の `productionConfigOf`)が積んだ
 * `warnings` を渡す ― ここは判定するだけで、警告の作成はしない。
 */
export function assertPricesPresent(seatName: string, warnings: readonly string[]): void {
  if (warnings.length > 0) {
    throw new Error(`単価が .env に無い(${seatName})― 費用が 0 に見えて上限が効かないので送らない`);
  }
}

/**
 * `originalText` を分解する。`runSlot` をそのまま呼ぶ薄い関数 ― schema 再試行・理由の累積・
 * 費用の上限判定・保存物はすべて `runSlot` の責務(ここで作り直さない)。
 */
export async function decomposeOriginalText(
  originalText: string,
  instruction: string,
  cfg: DecomposeConfig,
  deps: SlotDeps,
): Promise<SlotRunResult> {
  return runSlot(
    cfg,
    {
      label: "decompose",
      system: instruction,
      user: decomposerUserText(originalText),
      canonicalSchema: loadClaimDecompositionSchema() as Rec,
      schemaName: DECOMPOSER_SCHEMA_NAME,
      validateLlm: validateDecomposerOutput(originalText),
      capUsd: cfg.capUsd,
      cumulativeCostUsd: cfg.cumulativeCostUsd ?? 0,
    },
    deps,
  );
}
