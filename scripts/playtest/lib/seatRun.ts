// 束 R4 ― 1 席の実行と 1 回の実行の器(計画 docs/STEP_LLM_SEATS_R4_CALLSEAT_2026-09-30.md §1・§3・§4・§5)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。ここで得るのは検証(H-9・H-10)と採用(司令塔)の前の材料で、顧客の文には 1 字も出ない。
// 【止まる条件は全部「空席」にする】鍵が無い・モデル名が無い・費用の上限・入力の上限・合言葉が違う・schema を 2 回通らない。
//   **空席を他の席で埋めない**(司令塔の先決め 3)。空席は封筒の代わりに理由を持ち、器(R3)には present:false の席として残る。
// 【費用の上限は実行単位】1 席でも cost_cap で止まったら、**残りの席も送らない**(capReached)。送る前に止めるので、上限を越えた費用は発生しない。
// 【鍵】`.env` から読んだ値を引数で受け取り、保存物・run_summary・例外の文に出さない(最後の網として保存の直前に redactSecrets を通す)。
// 【数を作らない】ここが作るのはトークンの概算と費用の見込みだけ(観測の数は 1 つも作らない)。
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { redactSecrets } from "./env.js";
import { LlmHttpError, SENDS_TEMPERATURE, callStructured, countTokens, type ClientDeps, type Provider, type StructuredResponse } from "./llmClient.js";
import {
  buildIntegrationInput, canonicalJson, completeIntegration, integrationProblems, validateIntegrationLlm,
  type ItemMapRow, type SeatSlot,
} from "./integration.js";
import { adaptSchema, dropNullsNotAllowed, effectiveValueShape } from "./schemaAdapters.js";
import { renderSeatInput, type SeatInputMeta } from "./seatInput.js";
import { completeSeatOutput, loadSeatOutputLlmSchema, seatOutputProblems, validateSeatOutputLlm, type Seat } from "./seatOutput.js";
import { budgetDecision, costUsd, estimateTokensByChars, type Prices } from "./tokenBudget.js";

type Rec = Record<string, unknown>;

export const RUN_SUMMARY_CONTRACT = "llm-seats-run-summary" as const;
export const RUN_SUMMARY_SCHEMA_VERSION = "0.1" as const;
/** 席の取り置き(計画 §2)。整理役は 2 万 */
export const SEAT_RESERVE_OUTPUT_TOKENS = 30_000;
export const INTEGRATOR_RESERVE_OUTPUT_TOKENS = 20_000;
/** schema を通らなかったときの再依頼の上限(計画 §4)。会話にしない ― 新しい 1 通に「前回はこの欄で落ちた」を足す */
export const SCHEMA_RETRY_LIMIT = 2;
/** 途中で切れたときに取り置きを増やして送り直す回数と倍率 */
export const LENGTH_RETRY_LIMIT = 1;
export const LENGTH_RETRY_FACTOR = 1.5;

/**
 * 司令塔が固定した指示文の sha256(2026-09-30)。**1 バイトでも変えるなら版名を上げる ― 同じ版名で中身を差し替えない。**
 * 周をまたいで席の答えを比べるとき、「どの文で聞いたか」が分からなくなるのを防ぐ(司令塔の記録)。
 * 席の指示文は render(R1)が照合し、**整理役の指示文はここが照合する**(render を通らないので)。
 */
export const FIXED_INSTRUCTION_SHA256: Readonly<Record<string, string>> = {
  "LLM_SEATS_INSTRUCTION_v1_2026-09-30.md": "3b09bec22b7ea95c1a7e7a3cce1087b1c3c9f54ad2583d35f2d00e46242b2f88",
  "LLM_SEATS_INSTRUCTION_v1.1_2026-09-30.md": "11d1f533c74ec6dcecbd9010fb512546961bc753f57e45e88b34157b8cdb148b",
  "LLM_SEATS_INTEGRATOR_INSTRUCTION_v1_2026-09-30.md": "5118a6949862a104942f6975191dd3d16b00ca834f18b4bba5807aeaf2d7d94a",
};

/** 指示文 1 本の sha を固定値と照合する。**表に無い名前も誤り**(固定していない文で席に聞かない) */
export function fixedShaProblems(basename: string, content: Buffer | string): string[] {
  const expected = FIXED_INSTRUCTION_SHA256[basename];
  const actual = createHash("sha256").update(typeof content === "string" ? Buffer.from(content, "utf-8") : content).digest("hex");
  if (expected === undefined) return [`${basename}: この指示文の sha が固定されていない(固定してから配る。版名を上げたら表に足す)`];
  if (expected !== actual) return [`${basename}: sha が固定値と違う(${actual.slice(0, 8)}… / 固定 ${expected.slice(0, 8)}…)。1 バイトでも変えるなら版名を上げる`];
  return [];
}

export type AbsentReason = "no_key" | "no_model" | "cost_cap" | "input_limit" | "http_failed" | "schema_failed" | "reach_failed" | "no_json";

export interface SlotConfig {
  provider: Provider;
  model?: string;
  apiKey?: string;
  prices: Prices;
  inputLimit?: number;
  reserveOutputTokens: number;
  temperature?: number;
  seed?: number;
  baseUrl?: string;
}
export interface SeatConfig extends SlotConfig {
  seat: Seat;
}

export interface AttemptRecord {
  attempt: number;
  kind: "first" | "schema_retry" | "length_retry";
  requestedAt: string;
  /** llmClient の中の再送(429/5xx/接続)を含めた HTTP の回数 */
  httpAttempts: number;
  httpStatus?: number;
  finishReason?: string;
  finishReasonRaw?: string;
  usage?: { inputTokens: number; outputTokens: number };
  reserveOutputTokens: number;
  /** その返答が落ちた理由(schema・合言葉)。通れば空 */
  problems: string[];
  /** 送れなかったとき(HTTP の失敗)の理由。鍵は redact 済み */
  error?: string;
}

export interface SavedFile {
  name: string;
  content: string;
}

export interface SlotRunResult {
  present: boolean;
  absentReason?: AbsentReason;
  absentNote?: string;
  /** 席が書いた形(null の後始末の後・正本を通ったもの) */
  llm?: Rec;
  last?: StructuredResponse;
  attempts: AttemptRecord[];
  estimate: { inputTokens: number; method: "api" | "chars/3" };
  estimatedCostUsd: number;
  actualCostUsd: number;
  /** この席の後の累計の見込み(上限の判定に使う) */
  cumulativeCostUsd: number;
  /** cost_cap に当たったか(当たったら残りの席も送らない) */
  capReached: boolean;
  files: SavedFile[];
  requestedAt?: string;
  modelVersion?: string;
  usage: { inputTokens: number; outputTokens: number };
  finishReason?: string;
  elapsedMs: number;
}

export interface SlotDeps {
  fetch: typeof fetch;
  sleep?: (ms: number) => Promise<void>;
  /** 時刻(試験で固定する) */
  now?: () => Date;
}

function nowOf(deps: SlotDeps): Date {
  return deps.now === undefined ? new Date() : deps.now();
}
function sha256Of(text: string): string {
  return createHash("sha256").update(text, "utf-8").digest("hex");
}
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** 前回落ちた理由を足した 1 通(会話にしない。**前の出力は渡さない** ― 直させるのではなく、同じ束から書き直させる) */
export function retryUserText(baseUser: string, problems: readonly string[]): string {
  const lines = problems.slice(0, 20).map((p) => `- ${p}`).join("\n");
  return `${baseUser}\n\n---\n(前回の返答は次の欄で形が合わず受け取れませんでした。同じ束から、同じ形でもう一度書いてください。前回の返答そのものは渡していません ― 下は機械の検査が落とした欄と理由です。)\n${lines}\n`;
}

/**
 * 1 つの席(または整理役)を呼ぶ。**送る前に上限で止める**・**落ちたら空席にする**。
 * 判定は正本の検証器(validateLlm)だけ。各社向けの写しは「その形で書きやすくする」ためで、受理は正本で決める。
 */
export async function runSlot(
  cfg: SlotConfig,
  ctx: {
    label: string;
    system: string;
    user: string;
    canonicalSchema: Rec;
    schemaName: string;
    validateLlm: (json: unknown) => string[];
    capUsd: number;
    cumulativeCostUsd: number;
    /** 形が通った後の追加の検査(合言葉など)。落ちたら再試行しない理由を返す */
    afterValidate?: (llm: Rec) => { absentReason: AbsentReason; problems: string[] } | undefined;
  },
  deps: SlotDeps,
): Promise<SlotRunResult> {
  const started = nowOf(deps).getTime();
  const files: SavedFile[] = [];
  const attempts: AttemptRecord[] = [];
  const zero = { inputTokens: 0, outputTokens: 0 };
  const absent = (absentReason: AbsentReason, absentNote: string, estimate: SlotRunResult["estimate"], estimatedCostUsd: number, capReached = false): SlotRunResult => ({
    present: false, absentReason, absentNote, attempts, estimate, estimatedCostUsd, actualCostUsd: actual(), cumulativeCostUsd: ctx.cumulativeCostUsd + actual(), capReached, files, usage: usedTotal(), elapsedMs: nowOf(deps).getTime() - started,
  });
  const usedTotal = (): { inputTokens: number; outputTokens: number } =>
    attempts.reduce((acc, a) => ({ inputTokens: acc.inputTokens + (a.usage?.inputTokens ?? 0), outputTokens: acc.outputTokens + (a.usage?.outputTokens ?? 0) }), { ...zero });
  const actual = (): number => costUsd(usedTotal().inputTokens, usedTotal().outputTokens, cfg.prices);

  if (cfg.apiKey === undefined || cfg.apiKey.length === 0) return absent("no_key", `${ctx.label}: 鍵が .env に無い`, { inputTokens: 0, method: "chars/3" }, 0);
  if (cfg.model === undefined || cfg.model.length === 0) return absent("no_model", `${ctx.label}: モデル名が .env に無い`, { inputTokens: 0, method: "chars/3" }, 0);

  const clientDeps: ClientDeps = { fetch: deps.fetch, apiKey: cfg.apiKey, ...(cfg.baseUrl === undefined ? {} : { baseUrl: cfg.baseUrl }), ...(deps.sleep === undefined ? {} : { sleep: deps.sleep }) };
  const schema = adaptSchema(cfg.provider, ctx.canonicalSchema);

  // 送る前の数え(Anthropic・Gemini は API、OpenAI は chars/3)
  let estimate: SlotRunResult["estimate"] = estimateTokensByChars(`${ctx.system}\n\n${ctx.user}`);
  try {
    const counted = await countTokens({ provider: cfg.provider, model: cfg.model, system: ctx.system, user: ctx.user }, clientDeps);
    if (counted !== undefined) estimate = { inputTokens: counted, method: "api" };
  } catch (err) {
    // 数えられなくても chars/3 で続ける(越えたら送らない側に倒れる)
    files.push({ name: `${ctx.label}_count_tokens_error.txt`, content: redactSecrets((err as Error).message, [cfg.apiKey]) });
  }

  let user = ctx.user;
  let reserve = cfg.reserveOutputTokens;
  let schemaRetries = 0;
  let lengthRetries = 0;
  let lastEstimate = estimate;
  let lastDecision = budgetDecision({ inputTokens: estimate.inputTokens, reserveOutputTokens: reserve, prices: cfg.prices, capUsd: ctx.capUsd, cumulativeCostUsd: ctx.cumulativeCostUsd, ...(cfg.inputLimit === undefined ? {} : { inputLimit: cfg.inputLimit }) });

  for (let attempt = 1; ; attempt += 1) {
    const kind: AttemptRecord["kind"] = attempt === 1 ? "first" : attempts[attempts.length - 1]?.finishReason === "length" ? "length_retry" : "schema_retry";
    if (attempt > 1) {
      lastEstimate = estimateTokensByChars(`${ctx.system}\n\n${user}`).inputTokens > estimate.inputTokens ? { inputTokens: Math.max(estimate.inputTokens, estimateTokensByChars(`${ctx.system}\n\n${user}`).inputTokens), method: estimate.method } : estimate;
      lastDecision = budgetDecision({ inputTokens: lastEstimate.inputTokens, reserveOutputTokens: reserve, prices: cfg.prices, capUsd: ctx.capUsd, cumulativeCostUsd: ctx.cumulativeCostUsd + actual(), ...(cfg.inputLimit === undefined ? {} : { inputLimit: cfg.inputLimit }) });
    }
    if (!lastDecision.ok) {
      const reason = lastDecision.reason === "cost_cap" ? "cost_cap" : "input_limit";
      return absent(reason, `${ctx.label}: ${reason === "cost_cap" ? `見込み ${lastDecision.estimatedCostUsd.toFixed(4)} ドルで上限 ${ctx.capUsd} ドルを越えるので送らない` : `入力 ${lastEstimate.inputTokens} + 取り置き ${reserve} が上限 ${String(cfg.inputLimit)} を越えるので送らない`}`, lastEstimate, lastDecision.estimatedCostUsd, reason === "cost_cap");
    }
    const requestedAt = nowOf(deps).toISOString();
    const record: AttemptRecord = { attempt, kind, requestedAt, httpAttempts: 0, reserveOutputTokens: reserve, problems: [] };
    let res: StructuredResponse;
    try {
      res = await callStructured({
        provider: cfg.provider, model: cfg.model, system: ctx.system, user, schema, schemaName: ctx.schemaName, maxOutputTokens: reserve,
        ...(cfg.temperature === undefined ? {} : { temperature: cfg.temperature }), ...(cfg.seed === undefined ? {} : { seed: cfg.seed }),
      }, clientDeps);
    } catch (err) {
      record.httpAttempts = err instanceof LlmHttpError ? err.attempts : 1;
      if (err instanceof LlmHttpError) record.httpStatus = err.status;
      record.error = redactSecrets(err instanceof LlmHttpError ? `HTTP ${err.status}: ${err.bodyText}` : (err as Error).message, [cfg.apiKey]);
      attempts.push(record);
      files.push({ name: `${ctx.label}_attempt_${attempt}_error.txt`, content: record.error });
      return absent("http_failed", `${ctx.label}: 送れなかった(${record.error.slice(0, 120)})`, lastEstimate, lastDecision.estimatedCostUsd);
    }
    record.httpAttempts = res.attempts;
    record.httpStatus = res.httpStatus;
    record.finishReason = res.finishReason;
    record.finishReasonRaw = res.finishReasonRaw;
    record.usage = res.usage;
    attempts.push(record);
    files.push({ name: `${ctx.label}_attempt_${attempt}_raw.json`, content: `${JSON.stringify(res.raw, null, 1)}\n` });
    files.push({ name: `${ctx.label}_attempt_${attempt}_raw.txt`, content: res.text });

    // 途中で切れた → 取り置きを 1.5 倍にして 1 回だけ
    if (res.finishReason === "length" && lengthRetries < LENGTH_RETRY_LIMIT) {
      lengthRetries += 1;
      reserve = Math.ceil(reserve * LENGTH_RETRY_FACTOR);
      record.problems.push("途中で切れた(length)― 取り置きを増やして送り直す");
      continue;
    }
    if (res.json === undefined) {
      record.problems.push("JSON が取り出せなかった");
      if (schemaRetries < SCHEMA_RETRY_LIMIT) { schemaRetries += 1; user = retryUserText(ctx.user, record.problems); continue; }
      return absent("no_json", `${ctx.label}: ${SCHEMA_RETRY_LIMIT + 1} 回とも JSON にならなかった`, lastEstimate, lastDecision.estimatedCostUsd);
    }
    const cleaned = dropNullsNotAllowed(res.json, ctx.canonicalSchema);
    const problems = ctx.validateLlm(cleaned);
    if (problems.length > 0) {
      record.problems.push(...problems);
      if (schemaRetries < SCHEMA_RETRY_LIMIT) { schemaRetries += 1; user = retryUserText(ctx.user, problems); continue; }
      return absent("schema_failed", `${ctx.label}: ${SCHEMA_RETRY_LIMIT + 1} 回とも形が合わなかった(最後は ${problems.length} 件)`, lastEstimate, lastDecision.estimatedCostUsd);
    }
    const after = ctx.afterValidate?.(cleaned as Rec);
    if (after !== undefined) {
      record.problems.push(...after.problems);
      // 合言葉が違う = 入力が届いていない。**再試行しない**(計画 §4)
      return absent(after.absentReason, `${ctx.label}: ${after.problems.join(" / ")}`, lastEstimate, lastDecision.estimatedCostUsd);
    }
    return {
      present: true, llm: cleaned as Rec, last: res, attempts, estimate: lastEstimate, estimatedCostUsd: lastDecision.estimatedCostUsd,
      actualCostUsd: actual(), cumulativeCostUsd: ctx.cumulativeCostUsd + actual(), capReached: false, files, requestedAt,
      ...(res.modelVersion === undefined ? {} : { modelVersion: res.modelVersion }),
      usage: usedTotal(), finishReason: res.finishReason, elapsedMs: nowOf(deps).getTime() - started,
    };
  }
}

// ---- 1 席(封筒まで) ----

export interface SeatRunResult extends SlotRunResult {
  seat: Seat;
  /** 封筒(seat-output.v0.1)。空席なら無い */
  envelope?: Rec;
}

export async function runSeat(
  cfg: SeatConfig,
  ctx: { seatInput: string; meta: SeatInputMeta; instruction: string; today: string; gitHead: string | null; capUsd: number; cumulativeCostUsd: number },
  deps: SlotDeps,
): Promise<SeatRunResult> {
  const slot = await runSlot(cfg, {
    label: `seat_${cfg.seat}`,
    system: ctx.instruction,
    user: ctx.seatInput,
    canonicalSchema: loadSeatOutputLlmSchema() as Rec,
    schemaName: "submit_seat_output",
    validateLlm: (json) => validateSeatOutputLlm(json),
    capUsd: ctx.capUsd,
    cumulativeCostUsd: ctx.cumulativeCostUsd,
    afterValidate: (llm) => {
      const reach = isRecord(llm.reach) ? llm.reach : {};
      if (reach.passphrase === ctx.meta.passphrase) return undefined;
      return { absentReason: "reach_failed", problems: ["合言葉が束の末尾と違う ― 束が最後まで届いていない(再試行しない)"] };
    },
  }, deps);
  if (!slot.present || slot.llm === undefined || slot.last === undefined) return { ...slot, seat: cfg.seat };
  const envelope = completeSeatOutput(slot.llm, {
    runId: ctx.meta.runId, seat: cfg.seat, model: cfg.model ?? "", ...(slot.modelVersion === undefined ? {} : { modelVersion: slot.modelVersion }),
    meta: ctx.meta, today: ctx.today, gitHead: ctx.gitHead, usage: slot.last.usage, finishReason: slot.last.finishReasonRaw,
    attempts: slot.attempts.length, requestedAt: slot.requestedAt ?? ctx.today,
  });
  return { ...slot, seat: cfg.seat, envelope, files: [...slot.files, { name: `seat_${cfg.seat}.json`, content: `${JSON.stringify(envelope, null, 1)}\n` }] };
}

// ---- 1 回の実行 ----

export interface IntegratorConfig extends SlotConfig {
  instruction: string;
}

export interface RunAllConfig {
  runId: string;
  packet: Rec;
  request: Rec;
  /** 席の指示文(バイト列そのまま。sha は render が固定値と照合する) */
  instruction: Buffer;
  instructionSha256?: string;
  today: string;
  gitHead: string | null;
  seats: SeatConfig[];
  integrator?: IntegratorConfig;
  capUsd: number;
  /**
   * この実行を始める前までに使った見込み(揺れの床の 2 回目のため。人間の決定 2026-09-30: **上限は実行の累計に掛ける**)。
   * 2 回目に入る前に累計が上限を越える見込みなら、2 回目の席は 1 通も送らず cost_cap の空席として残る。
   */
  cumulativeCostUsdBefore?: number;
  forbid?: readonly string[];
  obsItemsPath?: string;
  /** 保存物から消す値(鍵)。最後の網 */
  secrets?: readonly (string | undefined)[];
}

export interface RunAllResult {
  meta: SeatInputMeta;
  seats: SeatRunResult[];
  integrationInput?: Rec;
  seatOrder?: Array<{ seatIndex: number; seat: Seat }>;
  itemMap?: ItemMapRow[];
  integration?: Rec;
  integrator?: SlotRunResult;
  checks: { seats: Array<{ seat: Seat; problems: string[] }>; integration?: { problems: string[] } };
  summary: Rec;
  files: SavedFile[];
}

/**
 * render(R1)→ 席を順に(並行しない ― 上限の判定を 1 本ずつ)→ 器(R3)→ 整理役 → 検査(R2・R3)→ run_summary。
 * **どこで止まっても、そこまでの原文と理由を残す**(files)。整理役が失敗しても席の封筒と器は残る(統合は後から回し直せる)。
 */
export async function runAll(cfg: RunAllConfig, deps: SlotDeps): Promise<RunAllResult> {
  const { text: seatInput, meta } = renderSeatInput({
    packet: cfg.packet, request: cfg.request, instruction: cfg.instruction, runId: cfg.runId,
    ...(cfg.instructionSha256 === undefined ? {} : { instructionSha256: cfg.instructionSha256 }),
    ...(cfg.forbid === undefined ? {} : { forbid: cfg.forbid }),
  });
  const files: SavedFile[] = [
    { name: "seat_input.md", content: seatInput },
    { name: "seat_input.meta.json", content: `${JSON.stringify(meta, null, 1)}\n` },
  ];
  const instruction = cfg.instruction.toString("utf-8");
  const seats: SeatRunResult[] = [];
  let cumulative = cfg.cumulativeCostUsdBefore ?? 0;
  let capReached = false;
  for (const seatCfg of cfg.seats) {
    if (capReached) {
      seats.push({
        seat: seatCfg.seat, present: false, absentReason: "cost_cap", absentNote: `seat_${seatCfg.seat}: この実行は費用の上限に達したので送らない(上限は実行単位)`,
        attempts: [], estimate: { inputTokens: 0, method: "chars/3" }, estimatedCostUsd: 0, actualCostUsd: 0, cumulativeCostUsd: cumulative, capReached: true, files: [], usage: { inputTokens: 0, outputTokens: 0 }, elapsedMs: 0,
      });
      continue;
    }
    const result = await runSeat(seatCfg, { seatInput, meta, instruction, today: cfg.today, gitHead: cfg.gitHead, capUsd: cfg.capUsd, cumulativeCostUsd: cumulative }, deps);
    cumulative = result.cumulativeCostUsd;
    if (result.capReached) capReached = true;
    seats.push(result);
    files.push(...result.files);
  }

  const slots: SeatSlot[] = seats.map((s) => (s.present && s.envelope !== undefined
    ? { seat: s.seat, envelope: s.envelope }
    : { seat: s.seat, absentReason: `${s.absentReason ?? "unknown"}: ${s.absentNote ?? ""}`.trim() }));
  const built = buildIntegrationInput(slots, { runId: cfg.runId, packet: cfg.packet, request: cfg.request, seatOrderRef: "seat_order.json" });
  files.push({ name: "integration_input.json", content: `${JSON.stringify(built.input, null, 1)}\n` });
  files.push({ name: "seat_order.json", content: `${JSON.stringify({ runId: cfg.runId, seatOrder: built.seatOrder, itemMap: built.itemMap }, null, 1)}\n` });

  const checks: RunAllResult["checks"] = {
    seats: seats.map((s) => ({
      seat: s.seat,
      problems: s.present && s.envelope !== undefined
        ? seatOutputProblems(s.envelope, { meta, request: cfg.request, today: cfg.today, ...(cfg.obsItemsPath === undefined ? {} : { obsItemsPath: cfg.obsItemsPath }) })
        : [],
    })),
  };

  let integration: Rec | undefined;
  let integrator: SlotRunResult | undefined;
  if (cfg.integrator !== undefined) {
    const scope = cfg.request.requestedScope as Rec;
    integrator = await runSlot(cfg.integrator, {
      label: "integrator",
      system: cfg.integrator.instruction,
      user: `${JSON.stringify(built.input, null, 1)}\n`,
      canonicalSchema: loadIntegrationLlmSchema(),
      schemaName: "submit_integration",
      validateLlm: (json) => validateIntegrationLlm(json),
      capUsd: cfg.capUsd,
      cumulativeCostUsd: cumulative,
    }, deps);
    cumulative = integrator.cumulativeCostUsd;
    files.push(...integrator.files);
    if (integrator.present && integrator.llm !== undefined && integrator.last !== undefined) {
      integration = completeIntegration(integrator.llm, {
        input: built.input, customerRef: meta.customerRef, timeLimitSec: Number(scope.timeLimitSec), games: Number(scope.games),
        today: cfg.today, gitHead: cfg.gitHead, model: cfg.integrator.model ?? "", ...(integrator.modelVersion === undefined ? {} : { modelVersion: integrator.modelVersion }),
        usage: integrator.last.usage, finishReason: integrator.last.finishReasonRaw, attempts: integrator.attempts.length, requestedAt: integrator.requestedAt ?? cfg.today,
      });
      files.push({ name: "integration.json", content: `${JSON.stringify(integration, null, 1)}\n` });
      checks.integration = { problems: integrationProblems(integration, built.input, { today: cfg.today, ...(cfg.obsItemsPath === undefined ? {} : { obsItemsPath: cfg.obsItemsPath }) }) };
    }
  }

  const summary = summaryOf({ cfg, meta, seats, integrator, integration, checks, cumulative, inputSha256: sha256Of(canonicalJson(built.input)) });
  files.push({ name: "checks.json", content: `${JSON.stringify(checks, null, 1)}\n` });
  files.push({ name: "run_summary.json", content: `${JSON.stringify(summary, null, 1)}\n` });
  const secrets = cfg.secrets ?? [];
  return {
    meta, seats, integrationInput: built.input, seatOrder: built.seatOrder, itemMap: built.itemMap,
    ...(integration === undefined ? {} : { integration }), ...(integrator === undefined ? {} : { integrator }),
    checks, summary,
    files: files.map((f) => ({ name: f.name, content: redactSecrets(f.content, secrets) })),
  };
}

/** 整理役の正本 schema(写しを作るためだけに読む。判定は integration.ts の validateIntegrationLlm) */
function loadIntegrationLlmSchema(): Rec {
  return JSON.parse(readFileSync(new URL("../schemas/integration.llm.v0.1.schema.json", import.meta.url), "utf-8")) as Rec;
}

function summaryOf(args: {
  cfg: RunAllConfig; meta: SeatInputMeta; seats: SeatRunResult[]; integrator?: SlotRunResult; integration?: Rec;
  checks: RunAllResult["checks"]; cumulative: number; inputSha256: string;
}): Rec {
  const { cfg, meta, seats, integrator, checks } = args;
  return {
    contract: RUN_SUMMARY_CONTRACT,
    schemaVersion: RUN_SUMMARY_SCHEMA_VERSION,
    runId: cfg.runId,
    customerRef: meta.customerRef,
    packetId: meta.packetId,
    today: cfg.today,
    gitHead: cfg.gitHead,
    capUsd: cfg.capUsd,
    cumulativeCostUsdBefore: round4(cfg.cumulativeCostUsdBefore ?? 0),
    seatInput: { sha256: meta.seatInputSha256, bytes: meta.bytes, chars: meta.chars, tokenEstimate: meta.tokenEstimate, instructionSha256: meta.instructionSha256 },
    seats: seats.map((s) => ({
      seat: s.seat, present: s.present, ...(s.absentReason === undefined ? {} : { absentReason: s.absentReason }), ...(s.absentNote === undefined ? {} : { absentNote: s.absentNote }),
      provider: cfg.seats.find((c) => c.seat === s.seat)?.provider, model: cfg.seats.find((c) => c.seat === s.seat)?.model ?? null,
      // 「温度 0 で回した」と読ませない ― Anthropic は temperature を受け付けないので送っていない(2026-09-30 の実測)
      temperatureSent: temperatureSentOf(cfg.seats.find((c) => c.seat === s.seat)),
      // その社の写しで観測の値に書ける形(席をまたいで比べるとき「入力の形が同じか」を先に見る)
      valueShape: valueShapeOf(cfg.seats.find((c) => c.seat === s.seat)),
      ...(s.modelVersion === undefined ? {} : { modelVersion: s.modelVersion }),
      estimate: s.estimate, estimatedCostUsd: round4(s.estimatedCostUsd), actualCostUsd: round4(s.actualCostUsd), usage: s.usage,
      attempts: s.attempts.map((a) => ({ attempt: a.attempt, kind: a.kind, httpAttempts: a.httpAttempts, ...(a.httpStatus === undefined ? {} : { httpStatus: a.httpStatus }), ...(a.finishReasonRaw === undefined ? {} : { finishReason: a.finishReasonRaw }), reserveOutputTokens: a.reserveOutputTokens, problems: a.problems.length, ...(a.error === undefined ? {} : { error: a.error }) })),
      elapsedMs: s.elapsedMs,
      items: s.envelope === undefined ? null : (s.envelope.items as unknown[]).length,
      checkProblems: checks.seats.find((c) => c.seat === s.seat)?.problems.length ?? null,
    })),
    integration: integrator === undefined ? null : {
      present: integrator.present, ...(integrator.absentReason === undefined ? {} : { absentReason: integrator.absentReason }), ...(integrator.absentNote === undefined ? {} : { absentNote: integrator.absentNote }),
      provider: cfg.integrator?.provider, model: cfg.integrator?.model ?? null, temperatureSent: temperatureSentOf(cfg.integrator),
      ...(integrator.modelVersion === undefined ? {} : { modelVersion: integrator.modelVersion }),
      inputSha256: args.inputSha256,
      estimate: integrator.estimate, estimatedCostUsd: round4(integrator.estimatedCostUsd), actualCostUsd: round4(integrator.actualCostUsd), usage: integrator.usage,
      attempts: integrator.attempts.length, elapsedMs: integrator.elapsedMs,
      clusters: args.integration === undefined ? null : (args.integration.clusters as unknown[]).length,
      checkProblems: checks.integration?.problems.length ?? null,
    },
    totals: {
      seatsPresent: seats.filter((s) => s.present).length,
      /**
       * 3 席の**有効な形がそろっているか**(司令塔の条件 2026-09-30)。false なら席の間の一致・不一致を
       * 実力差として読めない ― 比較の表に「入力の形が違う」注記を付ける材料。
       */
      valueShapeSame: new Set(cfg.seats.map((seat) => JSON.stringify(valueShapeOf(seat)))).size === 1,
      cumulativeCostUsd: round4(args.cumulative),
      capReached: seats.some((s) => s.absentReason === "cost_cap"),
    },
  };
}
/** その席の写しで観測の値に書ける形(社ごとの狭さの差を記録に出す) */
function valueShapeOf(cfg: SlotConfig | undefined): string[] {
  return cfg === undefined ? [] : effectiveValueShape(cfg.provider, loadSeatOutputLlmSchema() as Rec);
}

/** その席に temperature を送ったか(社が受け付け、かつ値が渡されたときだけ true) */
function temperatureSentOf(cfg: SlotConfig | undefined): boolean {
  return cfg !== undefined && cfg.temperature !== undefined && SENDS_TEMPERATURE[cfg.provider];
}
function round4(n: number): number {
  return Math.round(n * 10_000) / 10_000;
}
