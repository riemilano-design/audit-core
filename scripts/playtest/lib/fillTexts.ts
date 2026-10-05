// 言い換えの束 ― **1 回限りの境界測定実験**(人間の GO 2026-10-05。司令塔の中継 = 伝聞。原文は docs/AUTOMATION_STATUS_2026-09-26.md)。
// 計画 docs/PLAN_FILL_TEXTS_2026-10-05.md(§7 に固定値と「測れないもの」)。
//
// 【顧客の PDF にどう出るか】出ない。この実験で組んだ本編は顧客に送らない(条件 6・4)。
// 出口 ⑥(`exit_fill.py`)の照合 F-5 を通った文だけが `fill_texts.json` に残り、採用は司令塔・送付は人間。
//
// 【線】入力は ⑤ の採用の `statement` だけ(packet・問いの原文・候補の JSON は渡さない)/ 出力は F-5 の照合(python の 1 か所)に必ず通す /
// 落ちたら止まる(別の席で埋めない・2 回目を回さない)/ 上限は**この実行**の単位(1 USD)/ 指示文は固定(sha)/
// 1 試行 = 1 呼び出し(`callStructured` を直接呼ぶ ― `runSlot` は形の再試行を内に持ち、1 試行が最大 3 呼び出しになるので
// 「最大 3 試行・12 呼び出し」の数え方が合わない)。
//
// 【機械で測るもの / 測らないもの】測るのは F-5(数と指し手の字が statement の部分集合・禁止語)と長さ(≤ 200 字)だけ。
// **因果・条件・対象の保存は機械では測れない**(report の `notMeasured` に明記。通った文は人間が読む)。
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import type { StructuredRequest, StructuredResponse } from "./llmClient.js";
import { adaptSchema, dropNullsNotAllowed } from "./schemaAdapters.js";
import { retryUserText } from "./seatRun.js";
import { budgetDecision, costUsd, estimateTokensByChars, type Prices } from "./tokenBudget.js";

type Rec = Record<string, unknown>;

export const FILL_TEXTS_CONTRACT = "fill-texts" as const;
export const FILL_TEXTS_SCHEMA_VERSION = "0.1" as const;
export const FILL_TEXT_SCHEMA_NAME = "fill_text" as const;

/**
 * 人間の GO の条件(2026-10-05・原文の数)。**字で留める**(他の定数から作らない ― 作ると緩める変異が黙る)。
 * seat / provider = Claude 1 席、4 スロット、最大 3 試行、最大 12 呼び出し、1,000 トークン/回、この実行の上限 1 USD、
 * 太字 1 文・読み 1 本とも 200 字以内、答えの文(answered / partial)は作らない。
 */
export const EXPERIMENT = {
  seat: "claude",
  provider: "anthropic",
  maxSlots: 4,
  maxAttemptsPerSlot: 3,
  maxCalls: 12,
  reserveOutputTokens: 1000,
  capUsd: 1,
  maxChars: 200,
  generateAnswers: false,
  temperature: 0,
} as const;

export interface ItemRef { seatIndex: number; hypothesisId: string }
export interface SlotJob { slot: string; kind: "lead" | "reading"; itemRef: ItemRef; statement: string }

export class FillTextsError extends Error {}

function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** `exit_fill.item_ref_key` と同じ鍵(`seatIndex:hypothesisId`)。 */
export function itemRefKey(ref: unknown): string {
  if (!isRecord(ref) || typeof ref.seatIndex !== "number" || !Number.isInteger(ref.seatIndex)
      || typeof ref.hypothesisId !== "string" || ref.hypothesisId.trim().length === 0) {
    throw new FillTextsError(`itemRef の形が違う: ${JSON.stringify(ref)}`);
  }
  return `${String(ref.seatIndex)}:${ref.hypothesisId}`;
}

/** ④ の統合から itemRef → 代表の statement。読むのは `clusters[].itemRefs` と `representative.statement` だけ(`internal` は読まない)。 */
export function statementsOf(integration: Rec): Map<string, string> {
  const out = new Map<string, string>();
  const clusters = Array.isArray(integration.clusters) ? integration.clusters as unknown[] : [];
  for (const cluster of clusters) {
    if (!isRecord(cluster)) continue;
    const rep = isRecord(cluster.representative) ? cluster.representative : {};
    const statement = typeof rep.statement === "string" ? rep.statement : undefined;
    for (const ref of Array.isArray(cluster.itemRefs) ? cluster.itemRefs as unknown[] : []) {
      if (statement !== undefined) out.set(itemRefKey(ref), statement);
    }
  }
  return out;
}

/**
 * 作るスロット = `lead` + `p1[]` のうち `readingRequired: true` の行。**答えの文は作らない**(条件「5 人目は生成しない」= `EXPERIMENT.generateAnswers`)。
 * `readingRequired: false` の行は読みが要らないので作らない。statement が統合に無ければ止まる(⑥ と同じ)。
 */
export function slotJobsOf(selection: Rec, integration: Rec): SlotJob[] {
  const statements = statementsOf(integration);
  const statementOf = (ref: unknown, where: string): string => {
    const key = itemRefKey(ref);
    const s = statements.get(key);
    if (s === undefined) throw new FillTextsError(`${where}: itemRef ${key} が統合の clusters に無い`);
    return s;
  };
  const jobs: SlotJob[] = [];
  const lead = isRecord(selection.lead) ? selection.lead : undefined;
  if (lead === undefined) throw new FillTextsError("⑤ に lead が無い");
  jobs.push({ slot: "lead", kind: "lead", itemRef: lead.itemRef as ItemRef, statement: statementOf(lead.itemRef, "lead") });
  for (const row of Array.isArray(selection.p1) ? selection.p1 as unknown[] : []) {
    if (!isRecord(row)) continue;
    if (row.readingRequired !== true) continue;
    const slot = String(row.slot);
    jobs.push({ slot, kind: "reading", itemRef: row.itemRef as ItemRef, statement: statementOf(row.itemRef, `スロット ${slot}`) });
  }
  if (EXPERIMENT.generateAnswers !== false) throw new FillTextsError("答えの文は作らない(人間の GO の条件)");
  if (jobs.length > EXPERIMENT.maxSlots) throw new FillTextsError(`スロットが ${String(jobs.length)}(この実験は ${String(EXPERIMENT.maxSlots)} まで)`);
  return jobs;
}

// ---- 指示文(固定。sha で留める) ----
export const RULES_LINES: readonly string[] = [
  "あなたは言い換え係です。渡された 1 文(statement)を、将棋の初心者が読む冊子の 1 文に言い換えます。将棋の判断・評価・助言はしません。",
  "1. 数・分数・指し手(「▲４四歩打」のような表記)・名前の字を 1 字も変えない。足さない・減らさない・計算しない・漢数字にしない・丸めない・単位を変えない。",
  "2. statement に無い事実・数・条件・対象・因果関係を足さない。statement の条件・対象・因果関係を変えない(変えてよいのは言い回しだけ)。",
  "3. 断定しない(「〜という読みです」「〜の可能性があります」の形)。手の目的・狙いを書かない。戦法・陣形の名前を新しく付けない。",
  "4. 下の用語は、下の意味で使う(別の語に言い換えない)。",
  "5. 使ってはいけない語: {forbidden}(材料の外の判断を要する語)。",
  "6. 出力は 1 文で {maxChars} 字以内。JSON {\"text\": \"…\"} だけを返す(説明・前置き・別案を付けない)。",
];
export const RULES_SHA256 = "449a98d5f199c0bebec3184aebd8132d0f601539c480db0126b399a4fc331b16"; // 実装時に試験で本物の値に置き換える(下の instructionText の試験)

export type TermLine = readonly [string, string];

export function rulesSha256(): string {
  return createHash("sha256").update(RULES_LINES.join("\n"), "utf-8").digest("hex");
}

/** 指示文(system)。用語の 4 行と禁止語は python の 1 か所(`exit_fill.py --print-terms`)から**参照で**受ける(写さない)。 */
export function instructionText(terms: readonly TermLine[], forbidden: readonly string[], maxChars: number): string {
  if (terms.length === 0) throw new FillTextsError("用語の行が無い(exit_fill.py --print-terms の出力を渡す)");
  if (forbidden.length === 0) throw new FillTextsError("禁止語の表が無い");
  const rules = RULES_LINES.map((l) => l.replace("{forbidden}", forbidden.map((w) => `「${w}」`).join("・")).replace("{maxChars}", String(maxChars)));
  const termText = terms.map(([term, meaning]) => `- ${term}: ${meaning}`).join("\n");
  return `${rules.join("\n")}\n\n用語:\n${termText}\n`;
}

export const USER_KIND_NOTE: Readonly<Record<SlotJob["kind"], string>> = {
  lead: "太字の 1 文(本編の最初に出る)。尾の「― という読みです。数は N つ。」は道具が足すので書かない。",
  reading: "事実の文の後に「― 読み: 」に続けて置く 1 文。直前に事実の数が印字されるので、数を繰り返さなくてよい(書くなら字をそのまま)。",
};

/** user の本文。**statement だけ**(packet の数・問いの原文・候補の JSON は渡さない ― 線 1)。 */
export function userTextOf(job: SlotJob): string {
  return `スロット: ${job.slot}(${USER_KIND_NOTE[job.kind]})\n\nstatement:\n${job.statement}\n`;
}

export function loadFillTextSchema(): JsonSchema {
  return JSON.parse(readFileSync(new URL("../schemas/fill-text.v0.1.schema.json", import.meta.url), "utf-8")) as JsonSchema;
}

// ---- 実行(1 試行 = 1 呼び出し) ----
export interface FillTextsConfig {
  jobs: readonly SlotJob[];
  instruction: string;
  model?: string;
  apiKey?: string;
  prices: Prices;
  /** .env の `SEAT_COST_CAP_USD`。**EXPERIMENT.capUsd と同じでなければ回さない**(この実行の上限は 1) */
  capUsdFromEnv: number | undefined;
  runId: string;
  today: string;
  gitHead: string | null;
}
export interface VerifyVerdict {
  /** 機械の検査の問題(F-5・禁止語・長さ・空)。空なら**採用可能** */
  problems: string[];
  /** F-5 そのもの(数と指し手の字が statement の部分集合で字も同じ)を通ったか。禁止語・長さは見ない(人間の GO 条件 11) */
  f5Passed: boolean;
}
export interface FillTextsDeps {
  call: (req: StructuredRequest, apiKey: string) => Promise<StructuredResponse>;
  /** F-5 + 禁止語 + 長さの照合(python の 1 か所)。スロット → 判定 */
  verify: (texts: Record<string, string>) => Promise<Record<string, VerifyVerdict>>;
  /**
   * 試行の記録を**その場で**書く(同じ name は上書き)。人間の GO 条件 4(2026-10-05): 呼び出しの前に試行 ID・slot・試行番号・費用の欄を作り、
   * 呼び出しの後に成功/失敗と usage/実費を**同じファイル**に書く。途中で落ちても attempts/ から復元できる。
   * (2026-10-05 の 1 回限りの実行は、照合の段で落ちて lead 1 回分の usage が書かれずに消えた ― 返った後にまとめて書く作りだった。)
   * 無ければ `files` に返すだけ。
   */
  persist?: (file: { name: string; content: string }) => void;
  now?: () => Date;
}
export type AttemptStatus = "requested" | "send_failed" | "responded" | "rejected" | "adoptable";
export interface AttemptRow {
  /** `<runId>:<slot>:<試行番号>` */
  attemptId: string;
  slot: string;
  attempt: number;
  requestedAt: string;
  inputTokensEstimate: number;
  status: AttemptStatus;
  usage: { inputTokens: number; outputTokens: number } | null;
  finishReason: string | null;
  costUsd: number | null;
  cumulativeCostUsd: number | null;
  /** F-5 そのものの判定(照合に届かなければ null) */
  f5Passed: boolean | null;
  /** その試行が落ちた理由(形・F-5・禁止語・長さ・HTTP)。通れば空 */
  problems: string[];
  /** 採用可能の文(機械の検査を全部通ったときだけ) */
  passedText?: string;
}
export interface SlotReport {
  slot: string;
  kind: SlotJob["kind"];
  attempts: number;
  /** F-5 そのものを通った試行の数(禁止語・長さで落ちた試行も数える ― 条件 11「別項目」) */
  f5Passed: number;
  /** 機械の検査(F-5・禁止語・長さ)を全部通って候補として残った数(0 か 1)。採用そのものは数えない */
  adoptable: number;
  failureReasons: string[];
  actualCostUsd: number;
  maxCostUsdBefore: number;
  notAttempted?: string;
  attemptRows: AttemptRow[];
}
export interface FillTextsResult {
  texts: Record<string, string>;
  problems: Record<string, { attempt: number; reasons: string[] }[]>;
  report: Rec;
  files: { name: string; content: string }[];
}

export function capProblems(capUsdFromEnv: number | undefined): string[] {
  if (capUsdFromEnv === undefined) return ["SEAT_COST_CAP_USD が .env に無い ― 上限の無い実行はしない"];
  if (capUsdFromEnv !== EXPERIMENT.capUsd) return [`SEAT_COST_CAP_USD が ${String(capUsdFromEnv)} ― この実験の上限は ${String(EXPERIMENT.capUsd)} USD(人間の GO の条件)。.env を合わせてから回す`];
  return [];
}

/** 実行の前に計算する最大費用: スロットごとに 3 呼び出し × (入力の実測 + 取り置き 1,000)。再試行の指摘の字は入っていない(上限 1 USD が守る)。 */
export function maxCostBefore(jobs: readonly SlotJob[], instruction: string, prices: Prices): { total: number; perSlot: Record<string, number> } {
  const perSlot: Record<string, number> = {};
  let total = 0;
  for (const job of jobs) {
    const input = estimateTokensByChars(`${instruction}\n\n${userTextOf(job)}`).inputTokens;
    const cost = EXPERIMENT.maxAttemptsPerSlot * costUsd(input, EXPERIMENT.reserveOutputTokens, prices);
    perSlot[job.slot] = cost;
    total += cost;
  }
  return { total, perSlot };
}

function textOf(json: unknown, schema: JsonSchema): { text?: string; problems: string[] } {
  const cleaned = dropNullsNotAllowed(json, schema);
  const problems = validate(cleaned, schema);
  if (problems.length > 0) return { problems };
  return { text: (cleaned as { text: string }).text, problems: [] };
}

/** 試行の記録のファイル名(attempts/ の下)。 */
export function attemptFileName(slot: string, attempt: number): string {
  return `attempt_${slot}_${String(attempt)}.json`;
}

export async function runFillTexts(cfg: FillTextsConfig, deps: FillTextsDeps): Promise<FillTextsResult> {
  const now = (): Date => (deps.now === undefined ? new Date() : deps.now());
  const startedAt = now().toISOString();
  const capBad = capProblems(cfg.capUsdFromEnv);
  if (capBad.length > 0) throw new FillTextsError(capBad.join(" / "));
  if (cfg.apiKey === undefined || cfg.apiKey.length === 0) throw new FillTextsError("鍵が .env に無い");
  if (cfg.model === undefined || cfg.model.length === 0) throw new FillTextsError("モデル名が .env に無い");
  if (cfg.prices.inPerMillion === 0 || cfg.prices.outPerMillion === 0) throw new FillTextsError("単価が .env に無い ― 費用が 0 に見えて上限が効かないので送らない");
  const schema = loadFillTextSchema();
  const adapted = adaptSchema(EXPERIMENT.provider, schema);
  const before = maxCostBefore(cfg.jobs, cfg.instruction, cfg.prices);
  const texts: Record<string, string> = {};
  const problems: FillTextsResult["problems"] = {};
  const files: FillTextsResult["files"] = [];
  // その場で書く(同じ name は上書き = 試行の記録は 1 ファイルを呼び出しの前・後・照合の後に書き直す)。
  const emit = (file: { name: string; content: string }): void => {
    const at = files.findIndex((f) => f.name === file.name);
    if (at < 0) files.push(file); else files[at] = file;
    if (deps.persist !== undefined) deps.persist(file);
  };
  const emitAttempt = (rec: AttemptRow): void => {
    emit({ name: attemptFileName(rec.slot, rec.attempt), content: `${JSON.stringify(rec, null, 1)}\n` });
  };
  const slots: SlotReport[] = [];
  let totalCalls = 0;
  let cumulative = 0;
  let stopReason: string | undefined;

  for (const job of cfg.jobs) {
    const row: SlotReport = { slot: job.slot, kind: job.kind, attempts: 0, f5Passed: 0, adoptable: 0, failureReasons: [], actualCostUsd: 0, maxCostUsdBefore: before.perSlot[job.slot] ?? 0, attemptRows: [] };
    slots.push(row);
    const slotProblems: { attempt: number; reasons: string[] }[] = [];
    problems[job.slot] = slotProblems;
    if (stopReason !== undefined) { row.notAttempted = stopReason; continue; }
    const baseUser = userTextOf(job);
    const reasonsSoFar: string[] = [];
    let user = baseUser;
    for (let attempt = 1; attempt <= EXPERIMENT.maxAttemptsPerSlot; attempt += 1) {
      if (totalCalls >= EXPERIMENT.maxCalls) { stopReason = `呼び出しの上限 ${String(EXPERIMENT.maxCalls)} に達した`; row.failureReasons.push(stopReason); break; }
      const estimate = estimateTokensByChars(`${cfg.instruction}\n\n${user}`).inputTokens;
      const decision = budgetDecision({ inputTokens: estimate, reserveOutputTokens: EXPERIMENT.reserveOutputTokens, prices: cfg.prices, capUsd: EXPERIMENT.capUsd, cumulativeCostUsd: cumulative });
      if (!decision.ok) {
        stopReason = `費用の上限 ${String(EXPERIMENT.capUsd)} USD(見込み ${decision.estimatedCostUsd.toFixed(4)} + 累計 ${cumulative.toFixed(4)})― 送らない・残りも回さない`;
        row.failureReasons.push(stopReason);
        break;
      }
      totalCalls += 1;
      row.attempts += 1;
      // 条件 4: **呼び出しの前に**試行 ID・slot・試行番号・費用の欄(空)を書く。
      const rec: AttemptRow = { attemptId: `${cfg.runId}:${job.slot}:${String(attempt)}`, slot: job.slot, attempt, requestedAt: now().toISOString(), inputTokensEstimate: estimate, status: "requested", usage: null, finishReason: null, costUsd: null, cumulativeCostUsd: null, f5Passed: null, problems: [] };
      row.attemptRows.push(rec);
      emitAttempt(rec);
      let res: StructuredResponse;
      try {
        res = await deps.call({ provider: EXPERIMENT.provider, model: cfg.model, system: cfg.instruction, user, schema: adapted, schemaName: FILL_TEXT_SCHEMA_NAME, maxOutputTokens: EXPERIMENT.reserveOutputTokens, temperature: EXPERIMENT.temperature }, cfg.apiKey);
      } catch (err) {
        rec.status = "send_failed";
        rec.problems.push(`送れなかった: ${(err as Error).message.slice(0, 200)}`);
        row.failureReasons.push(...rec.problems);
        slotProblems.push({ attempt, reasons: [...rec.problems] });
        emitAttempt(rec);
        emit({ name: `${job.slot}_attempt_${String(attempt)}_error.txt`, content: rec.problems.join("\n") });
        break; // 送れないときは再試行しない(落ちたら止まる)
      }
      // 条件 4: **呼び出しの後に**成功と usage・実費を同じファイルへ(照合の前 ― 照合で落ちても消えない)。
      const cost = costUsd(res.usage.inputTokens, res.usage.outputTokens, cfg.prices);
      cumulative += cost;
      row.actualCostUsd += cost;
      rec.status = "responded";
      rec.usage = res.usage;
      rec.finishReason = res.finishReason;
      rec.costUsd = cost;
      rec.cumulativeCostUsd = cumulative;
      emitAttempt(rec);
      emit({ name: `${job.slot}_attempt_${String(attempt)}_raw.json`, content: `${JSON.stringify(res.raw, null, 1)}\n` });
      const got = res.json === undefined ? { problems: ["JSON が取り出せなかった"] } : textOf(res.json, schema);
      let reasons: string[] = got.problems.map((p) => `形: ${p}`);
      if (got.text !== undefined) {
        const verdict = (await deps.verify({ [job.slot]: got.text }))[job.slot];
        if (verdict === undefined) throw new FillTextsError(`照合がスロット ${job.slot} の判定を返さなかった`);
        reasons = verdict.problems;
        rec.f5Passed = verdict.f5Passed;
        if (verdict.f5Passed) row.f5Passed += 1;
        if (reasons.length === 0) {
          texts[job.slot] = got.text;
          rec.passedText = got.text;
          rec.status = "adoptable";
          row.adoptable = 1;
          emitAttempt(rec);
          break;
        }
      }
      rec.status = "rejected";
      rec.problems.push(...reasons);
      emitAttempt(rec);
      row.failureReasons.push(...reasons.map((r) => `試行 ${String(attempt)}: ${r}`));
      slotProblems.push({ attempt, reasons: [...reasons] });
      emit({ name: `${job.slot}_attempt_${String(attempt)}_problems.txt`, content: `${reasons.map((r) => `- ${r}`).join("\n")}\n` });
      for (const r of reasons) if (!reasonsSoFar.includes(r)) reasonsSoFar.push(r);
      user = retryUserText(baseUser, reasonsSoFar);
    }
  }
  const report: Rec = {
    contract: FILL_TEXTS_CONTRACT,
    schemaVersion: FILL_TEXTS_SCHEMA_VERSION,
    runId: cfg.runId,
    today: cfg.today,
    gitHead: cfg.gitHead,
    startedAt,
    finishedAt: now().toISOString(),
    fixed: { ...EXPERIMENT, model: cfg.model, rulesSha256: rulesSha256(), instructionSha256: createHash("sha256").update(cfg.instruction, "utf-8").digest("hex") },
    totals: {
      slots: cfg.jobs.length, calls: totalCalls, f5Passed: slots.reduce((a, s) => a + s.f5Passed, 0), adoptable: slots.reduce((a, s) => a + s.adoptable, 0),
      actualCostUsd: cumulative, maxCostUsdBefore: before.total, capUsd: EXPERIMENT.capUsd, stopReason: stopReason ?? null,
    },
    slots: slots.map((s) => ({ slot: s.slot, kind: s.kind, attempts: s.attempts, f5Passed: s.f5Passed, adoptable: s.adoptable, failureReasons: s.failureReasons, actualCostUsd: s.actualCostUsd, maxCostUsdBefore: s.maxCostUsdBefore, ...(s.notAttempted === undefined ? {} : { notAttempted: s.notAttempted }), attemptRows: s.attemptRows })),
    columns: {
      f5Passed: "F-5 そのもの(数と指し手の字が statement の部分集合で字も同じ)を通った試行の数。禁止語・長さは見ない",
      adoptable: "機械の検査(F-5・禁止語・長さ ≤ 200)を全部通って候補として残った数(0 か 1)。採用そのもの(司令塔・人間)は数えない",
    },
    measured: {
      byMachine: ["F-5: 数(全角・半角・小数)と指し手の表記の字が statement の部分集合で、字がそのまま(exit_fill.paraphrase_problems)", "禁止語(exit_groups.LABEL_FORBIDDEN_WORDS)が無い", `長さ ≤ ${String(EXPERIMENT.maxChars)} 字(印の無い文なので素直に数える)`],
      notMeasured: ["因果関係・条件・対象が statement と同じか(機械では測れない ― 通った文を人間が読む)", "新しい事実が足されていないか(数と指し手以外の語は照合していない)", "文として自然か・初心者に伝わるか"],
      note: "生成結果は監査済みの事実ではない(人間の GO の条件 4)。採用は司令塔、送付は人間。",
    },
  };
  return { texts, problems, report, files };
}
