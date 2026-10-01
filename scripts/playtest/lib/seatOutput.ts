// 3 席 LLM API の束 R2 ― 席の出力の封筒 seat-output.v0.1(計画 docs/STEP_LLM_SEATS_R2_CONTRACT_2026-09-30.md §4・§5)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。席の出力を「機械で落とせる形」にする契約と検査だけ。
// 【この module は packet を読まない】packetRef の実在(H-9)・語彙(H-10)は自動化レーンの検証器。ここは形・文法・封筒の整合だけ。
//   observationPacket*.ts を import しない(試験が import の一覧を見る)。
// 【数を作らない】completeSeatOutput が埋めるのは id・版・出どころ・日付だけ。値は席が packet から写したまま。
// 【LLM を呼ばない・鍵を読まない】
import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import { loadObsRegistry, validateHypothesisLine, type CheckResult } from "./hypothesis.js";
import { packetObsIdOf, packetRefPathProblems } from "./packetRef.js";
import { normalizeLastKey, type SeatInputMeta } from "./seatInput.js";

export const SEAT_OUTPUT_CONTRACT = "seat-output" as const;
export const SEAT_OUTPUT_SCHEMA_VERSION = "0.1" as const;
export const SEAT_HYPOTHESIS_SCHEMA_VERSION = "0.4" as const;
export type Seat = "gpt" | "gemini" | "claude";
/** 席の行の provenance.excludedInputs(現行ルートの出力は席に渡していない ― H-6 の盲検の記録) */
export const SEAT_EXCLUDED_INPUTS: readonly string[] = ["answer_menu.json", "exit_candidates.json", "9_本編.md"];
export const SEAT_INPUT_PROVENANCE_PREFIX = "seat_input:" as const;

export class SeatOutputError extends Error {
  readonly problems: readonly string[];
  constructor(problems: readonly string[]) {
    super(`席の出力を封筒にできない(${problems.length} 件):\n${problems.map((p) => `  - ${p}`).join("\n")}`);
    this.name = "SeatOutputError";
    this.problems = problems;
  }
}

export function loadSeatOutputSchema(): JsonSchema {
  return JSON.parse(readFileSync(new URL("../schemas/seat-output.v0.1.schema.json", import.meta.url), "utf-8")) as JsonSchema;
}
export function loadSeatOutputLlmSchema(): JsonSchema {
  return JSON.parse(readFileSync(new URL("../schemas/seat-output.llm.v0.1.schema.json", import.meta.url), "utf-8")) as JsonSchema;
}

/** 席が返した JSON が「席が書く形」か(schema だけ) */
export function validateSeatOutputLlm(json: unknown, schema: JsonSchema = loadSeatOutputLlmSchema()): string[] {
  return validate(json, schema);
}
export function validateSeatOutputEnvelope(envelope: unknown, schema: JsonSchema = loadSeatOutputSchema()): string[] {
  return validate(envelope, schema);
}

export interface CompleteContext {
  runId: string;
  seat: Seat;
  model: string;
  modelVersion?: string;
  meta: SeatInputMeta;
  /** 予測の writtenAt(実行日。席には書かせない ― 司令塔の判断 2026-09-30) */
  today: string;
  gitHead: string | null;
  usage: { inputTokens: number; outputTokens: number };
  finishReason: string;
  attempts: number;
  requestedAt: string;
}

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}
function asArray(x: unknown): unknown[] {
  return Array.isArray(x) ? x : [];
}

/** hypothesisId の真ん中の区切り(席 + runId の先頭 4。契約の pattern `[a-z0-9]+` に合わせて小文字英数だけ) */
export function seatRunToken(seat: Seat, runId: string): string {
  return `${seat}${runId.toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 4)}`;
}

/**
 * 席が書いた形 → 封筒。**決定的**(同じ入力なら同じ封筒)。数は 1 つも作らない。
 * 席の itemId(`S-001`)は hypothesisId に写し替え、answers[].itemIds・actionCandidate.derivedFrom の参照も同じ対応で置き換える
 * (対応の無い参照はそのまま残し、E-3 が落とす)。元の itemId は origin.itemId に残す。
 */
export function completeSeatOutput(llm: unknown, ctx: CompleteContext): Rec {
  const schemaProblems = validateSeatOutputLlm(llm);
  if (schemaProblems.length > 0) throw new SeatOutputError(schemaProblems.map((p) => `席が書く形: ${p}`));
  // 席の JSON を写してから組む(封筒の中に席の object を参照のまま入れない ― 1 か所を直すと別の場所も変わる、を起こさない)
  const src = structuredClone(llm) as Rec;
  const items = asArray(src.items) as Rec[];
  const ids = items.map((item) => String(item.itemId));
  const dup = ids.filter((id, i) => ids.indexOf(id) !== i);
  if (dup.length > 0) throw new SeatOutputError([`itemId が重複: ${[...new Set(dup)].join(", ")}`]);
  const token = seatRunToken(ctx.seat, ctx.runId);
  const idMap = new Map<string, string>();
  ids.forEach((id, i) => idMap.set(id, `H-${ctx.meta.customerRef}-${token}-${String(i + 1).padStart(3, "0")}`));
  const mapId = (id: unknown): unknown => (typeof id === "string" && idMap.has(id) ? idMap.get(id) : id);
  const inputs = [`${SEAT_INPUT_PROVENANCE_PREFIX}${ctx.meta.seatInputSha256}`];

  const completeObs = (obs: Rec): Rec => {
    const path = String((obs.packetRef as Rec | undefined)?.path ?? "");
    const out: Rec = { obsId: packetObsIdOf(path), path: typeof obs.path === "string" ? obs.path : path, value: obs.value };
    if (obs.unit !== undefined) out.unit = obs.unit;
    if (isRecord(obs.derived)) {
      const d = obs.derived;
      const side = (s: unknown): Rec => {
        const r = isRecord(s) ? s : {};
        return { obsId: packetObsIdOf(String(r.path ?? "")), value: r.value };
      };
      out.derived = { kind: d.kind, numerator: side(d.numerator), denominator: side(d.denominator) };
    }
    out.packetRef = obs.packetRef;
    return out;
  };

  const lines = items.map((item, i) => {
    const line: Rec = {
      schemaVersion: SEAT_HYPOTHESIS_SCHEMA_VERSION,
      hypothesisId: idMap.get(ids[i]!),
      subject: { customer: ctx.meta.customerRef, groups: [`${ctx.meta.timeLimitSec} 秒`], gamesCount: ctx.meta.games },
      scope: "this_user",
      lane: item.lane,
      kind: item.kind,
      factOrHypothesis: item.factOrHypothesis,
      origin: { seat: ctx.seat, itemId: ids[i] },
      statement: item.statement,
      observations: (asArray(item.observations) as Rec[]).map(completeObs),
      counterEvidence: (() => {
        const ce = isRecord(item.counterEvidence) ? item.counterEvidence : {};
        return {
          attempted: ce.attempted,
          items: (asArray(ce.items) as Rec[]).map((ci) => ({
            kind: ci.kind,
            text: ci.text,
            observations: (asArray(ci.observations) as Rec[]).map((obs) => {
              const path = String((obs.packetRef as Rec | undefined)?.path ?? "");
              const o: Rec = { obsId: packetObsIdOf(path), path: typeof obs.path === "string" ? obs.path : path, value: obs.value };
              if (obs.unit !== undefined) o.unit = obs.unit;
              return o;
            }),
          })),
          result: ce.result,
          provenance: { inputs: [...inputs] },
        };
      })(),
      status: "proposed",
      knowledge: { kind: "discovered", reviewStatus: "draft", origin: { kifu: ctx.meta.customerRef, lane: "llm-seat" }, range: "this_user" },
      provenance: { gitHead: ctx.gitHead, inputs: [...inputs], excludedInputs: [...SEAT_EXCLUDED_INPUTS] },
    };
    if (isRecord(item.prediction)) line.prediction = { writtenAt: ctx.today, ...item.prediction };
    if (item.requestRef !== undefined) line.requestRef = item.requestRef;
    if (isRecord(item.actionCandidate)) {
      line.actionCandidate = { ...item.actionCandidate, derivedFrom: asArray(item.actionCandidate.derivedFrom).map(mapId) };
    }
    if (item.neededObservation !== undefined) line.neededObservation = item.neededObservation;
    if (item.internal !== undefined) line.internal = item.internal;
    return line;
  });

  const run: Rec = {
    runId: ctx.runId, seat: ctx.seat, model: ctx.model, inputSha256: ctx.meta.seatInputSha256, instructionSha256: ctx.meta.instructionSha256,
    requestedAt: ctx.requestedAt, usage: ctx.usage, finishReason: ctx.finishReason, attempts: ctx.attempts,
  };
  if (ctx.modelVersion !== undefined) run.modelVersion = ctx.modelVersion;
  return {
    contract: SEAT_OUTPUT_CONTRACT,
    schemaVersion: SEAT_OUTPUT_SCHEMA_VERSION,
    run,
    reach: src.reach,
    items: lines,
    answers: (asArray(src.answers) as Rec[]).map((a) => ({ ...a, itemIds: asArray(a.itemIds).map(mapId) })),
    selfComputedNumbers: src.selfComputedNumbers,
    omissions: src.omissions,
  };
}

// ---- 封筒の検査 E-1〜E-7(packet を読まない) ----

export interface SeatOutputCheckOptions {
  meta: SeatInputMeta;
  request: unknown;
  today: string;
  registry?: Set<string>;
  bannedWords?: readonly string[];
  obsItemsPath?: string;
}

const NUMBER_RE = /-?\d+(?:\.\d+)?/g;
function numberTokensOf(text: string): Set<string> {
  return new Set(Array.from(text.matchAll(NUMBER_RE)).map((m) => m[0]));
}

function walkKeys(x: unknown, path: string, onKey: (key: string, path: string) => void): void {
  if (Array.isArray(x)) x.forEach((item, i) => walkKeys(item, `${path}[${i}]`, onKey));
  else if (isRecord(x)) for (const [k, v] of Object.entries(x)) { onKey(k, `${path}.${k}`); walkKeys(v, `${path}.${k}`, onKey); }
}

/** 封筒の検査。空なら通った。各項目の H-1〜H-8 も回して `items[i] H-n: …` で返す */
export function seatOutputProblems(envelope: unknown, opts: SeatOutputCheckOptions): string[] {
  const problems: string[] = [];
  const schemaProblems = validateSeatOutputEnvelope(envelope);
  if (schemaProblems.length > 0) return schemaProblems.map((p) => `schema: ${p}`);
  const env = envelope as Rec;
  const meta = opts.meta;
  const items = asArray(env.items) as Rec[];
  const itemIds = new Set(items.map((it) => String(it.hypothesisId)));

  // E-1 到達
  const reach = env.reach as Rec;
  if (reach.passphrase !== meta.passphrase) problems.push(`E-1: 合言葉が違う(席「${String(reach.passphrase)}」/ meta「${meta.passphrase}」)― 届いていない`);
  const metaSections = new Map(meta.sections.map((s) => [s.section, s.lastKey]));
  const seen = new Set<string>();
  const headingSections = new Set(meta.headingSections ?? []);
  for (const s of asArray(reach.sections) as Rec[]) {
    const sec = String(s.section);
    // **両側に同じ正規化**を掛ける(箇条書きの印と末尾の `:` は鍵ではない。2026-10-01 の司令塔の決定)
    const key = normalizeLastKey(String(s.lastKey));
    const expectedRaw = metaSections.get(sec);
    const expected = expectedRaw === undefined ? undefined : normalizeLastKey(expectedRaw);
    // 見出しだけの節(データの行が無い)は「読んだ」と言えるだけで、最後の鍵名を持たない。
    // **在ることだけ見る** ― 束にも無い節名は下の行で落ちるので、捏造は通らない(司令塔の決定 2026-09-30)。
    if (expected === undefined && headingSections.has(sec)) continue;
    if (expected === undefined) { problems.push(`E-1: 席の reach.sections に meta にも束の見出しにも無い節「${sec}」`); continue; }
    seen.add(sec);
    // **空の鍵は両側で落とす。** 片側(席)だけ守ると、meta の鍵が正規化で空になった束
    // (例: `provenance.inputs[].path` が ":" の 1 字)で `key.startsWith("")` が常に真になり、
    // **その節の E-1 がどんな鍵でも素通りする**(2026-10-01 の独立監査が実物で再現した穴)。
    if (key.length === 0 || expected.length === 0 || !(expected.startsWith(key) || key.startsWith(expected))) problems.push(`E-1: 節「${sec}」の lastKey が meta と前方一致しない(席「${key}」/ meta「${expected}」)`);
  }
  const omissions = asArray(env.omissions).map(String);
  for (const sec of metaSections.keys()) {
    if (!seen.has(sec) && !omissions.some((o) => o.includes(sec))) problems.push(`E-1: 節「${sec}」を席が reach.sections に写しておらず、omissions にも無い`);
  }

  // E-2 答え
  const questions = asArray((opts.request as Rec | undefined)?.customerQuestions) as Rec[];
  const answers = asArray(env.answers) as Rec[];
  for (const q of questions) {
    const n = answers.filter((a) => a.questionId === q.id).length;
    if (n !== 1) problems.push(`E-2: 問い ${String(q.id)} への answers が ${n} 行(ちょうど 1 行が要る)`);
  }
  const qids = new Set(questions.map((q) => String(q.id)));
  answers.forEach((a, i) => {
    if (!qids.has(String(a.questionId))) problems.push(`E-2: answers[${i}] の questionId「${String(a.questionId)}」が request に無い`);
    const missing = asArray(a.missing) as Rec[];
    if ((a.status === "partial" || a.status === "unanswerable") && missing.length === 0) problems.push(`E-2: answers[${i}](${String(a.status)})の missing が空 ― 何が無いかを空で埋めない`);
    missing.forEach((m, j) => {
      for (const field of ["what", "howToMeasure"]) {
        if (numberTokensOf(String(m[field] ?? "")).size > 0) problems.push(`E-2: answers[${i}].missing[${j}].${field} に数を含む`);
      }
    });
    for (const id of asArray(a.itemIds)) if (!itemIds.has(String(id))) problems.push(`E-2: answers[${i}].itemIds の「${String(id)}」が items に無い`);
  });

  // E-3 行(schema v0.4 + H-1〜H-8 + kind の必須)・E-4 文法
  const registry = opts.registry ?? loadObsRegistry(opts.obsItemsPath ?? new URL("../../../docs/OBSERVATION_ITEMS.md", import.meta.url).pathname);
  const seenIds = new Set<string>();
  items.forEach((item, i) => {
    const id = String(item.hypothesisId);
    if (seenIds.has(id)) problems.push(`E-3: items[${i}] の hypothesisId「${id}」が重複`);
    seenIds.add(id);
    const results: CheckResult[] = validateHypothesisLine(item, { today: opts.today, registry, ...(opts.bannedWords === undefined ? {} : { bannedWords: opts.bannedWords }) });
    for (const r of results) if (!r.ok) for (const m of r.messages) problems.push(`E-3: items[${i}] ${r.check}: ${m}`);
    const kind = typeof item.kind === "string" ? item.kind : "hypothesis";
    if ((kind === "answer_candidate" || kind === "unanswerable") && !isRecord(item.requestRef)) problems.push(`E-3: items[${i}](${kind})に requestRef が無い`);
    if ((kind === "unanswerable" || kind === "needed_observation") && !isRecord(item.neededObservation)) problems.push(`E-3: items[${i}](${kind})に neededObservation が無い`);
    if (kind === "action_candidate" && !isRecord(item.actionCandidate)) problems.push(`E-3: items[${i}](action_candidate)に actionCandidate が無い`);
    if (isRecord(item.requestRef) && !qids.has(String(item.requestRef.questionId))) problems.push(`E-3: items[${i}] の requestRef「${String(item.requestRef.questionId)}」が request に無い`);
    if (isRecord(item.actionCandidate)) {
      for (const ref of asArray(item.actionCandidate.derivedFrom)) if (!itemIds.has(String(ref))) problems.push(`E-3: items[${i}].actionCandidate.derivedFrom の「${String(ref)}」が items に無い`);
    }
    if (isRecord(item.neededObservation)) {
      for (const field of ["what", "howToMeasure"]) if (numberTokensOf(String(item.neededObservation[field] ?? "")).size > 0) problems.push(`E-3: items[${i}].neededObservation.${field} に数を含む`);
    }
    (asArray(item.observations) as Rec[]).forEach((obs, j) => {
      if (!isRecord(obs.packetRef)) { problems.push(`E-4: items[${i}].observations[${j}] に packetRef が無い(席の観測は packet の場所を持つ)`); return; }
      for (const p of packetRefPathProblems(obs.packetRef.path)) problems.push(`E-4: items[${i}].observations[${j}] ${p}`);
    });
  });

  // E-5 隔離
  const texts: string[] = [];
  for (const item of items) {
    texts.push(String(item.statement ?? ""));
    for (const ci of asArray((item.counterEvidence as Rec | undefined)?.items) as Rec[]) texts.push(String(ci.text ?? ""));
  }
  for (const a of answers) { texts.push(String(a.reason ?? "")); for (const m of asArray(a.missing) as Rec[]) texts.push(`${String(m.what ?? "")} ${String(m.howToMeasure ?? "")}`); }
  const textTokens = new Set<string>();
  for (const t of texts) for (const tok of numberTokensOf(t)) textTokens.add(tok);
  (asArray(env.selfComputedNumbers) as Rec[]).forEach((s, i) => {
    const token = JSON.stringify(s.value);
    if (textTokens.has(token)) problems.push(`E-5: selfComputedNumbers[${i}] の値「${token}」が statement / answers の文に出ている(隔離欄の数を文に持ち込まない)`);
  });

  // E-6 内部
  for (const [k, v] of Object.entries(env)) {
    if (k === "items") continue;
    walkKeys(v, k, (key, path) => { if (key === "internal") problems.push(`E-6: 「internal」が items の外(${path})に在る`); });
  }

  // E-7 run
  const run = env.run as Rec;
  if (run.inputSha256 !== meta.seatInputSha256) problems.push("E-7: run.inputSha256 が meta の seat_input の sha と違う(別の入力で得た出力)");
  if (run.instructionSha256 !== meta.instructionSha256) problems.push("E-7: run.instructionSha256 が meta の指示文の sha と違う");
  items.forEach((item, i) => {
    const inputs = asArray((item.provenance as Rec | undefined)?.inputs).map(String);
    if (!inputs.includes(`${SEAT_INPUT_PROVENANCE_PREFIX}${meta.seatInputSha256}`)) problems.push(`E-7: items[${i}].provenance.inputs に seat_input の sha が無い`);
  });
  return problems;
}
