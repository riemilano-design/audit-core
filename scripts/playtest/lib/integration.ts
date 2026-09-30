// 3 席 LLM API の束 R3 ― 統合(整理役)の契約: integration_input.v0.1 / integration.v0.1(計画 docs/STEP_LLM_SEATS_R3_INTEGRATION_2026-09-30.md)。
//
// 【顧客の PDF にどう出るか】今は何も変わらない。固定するのは 3 つの線:
//   (1) 整理役は席の名前を知らない(seatIndex だけ。対応表は run のログ = seatOrderRef)。
//   (2) 一致の数(seatCount)は記録であって証拠ではない(evidence は schema で const false。検証器・採用はこの欄を読まない)。
//   (3) 席の項目は黙って消えない(clusters ∪ dropped が全項目にちょうど 1 回)。forVerification から外す束は全部 heldBack に理由つき
//       (理由は seatCount を参照しない ― 司令塔 2026-09-30。3 席一致だけを特別扱いすると一致の数が再び信号になる)。
// 【internal は構造で拒む】入力の器に欄が無い(additionalProperties: false)。写す関数は許した欄だけを写す。
// 【packet を読まない】packetDigest は呼び出し側が渡す packet の JSON から写す(R1 と同じ写しの規則)。検査は packet を読まない(実在は H-9)。
// 【LLM を呼ばない・鍵を読まない・数を作らない】seatCount の value(異なる seatIndex の数)と answersByQuestion の summary は席の欄から機械で決まる。
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import { loadObsRegistry, validateHypothesisLine } from "./hypothesis.js";
import { aggregateRef, packetObsIdOf, packetRefPathProblems } from "./packetRef.js";
import { Prng } from "./prng.js";
import type { Seat } from "./seatOutput.js";

export const INTEGRATION_INPUT_CONTRACT = "integration-input" as const;
export const INTEGRATION_CONTRACT = "integration" as const;
export const INTEGRATION_SCHEMA_VERSION = "0.1" as const;
/**
 * 代表の行の provenance.inputs の形: `seat_item:<seatIndex>:<匿名 id>`(束の成員そのもの)。
 * 「integration_input:<sha>」にすると H-6(盲検: 反証の側に統合の出力を渡さない)の禁止語「integrat」に当たる ― 代表は席の項目から
 * 作られるので、入力として正直なのは成員の列。器の sha は run.inputSha256 が持つ(I-8 が見る)。
 */
export const SEAT_ITEM_PROVENANCE_PREFIX = "seat_item:" as const;
export function seatItemRef(seatIndex: unknown, hypothesisId: unknown): string {
  return `${SEAT_ITEM_PROVENANCE_PREFIX}${String(seatIndex)}:${String(hypothesisId)}`;
}
export const INTEGRATOR_EXCLUDED_INPUTS: readonly string[] = ["answer_menu.json", "exit_candidates.json", "9_本編.md", "seat names"];
/** 出力に席の名前が出ていないことを見る語(run.model は除く) */
export const SEAT_NAME_RE = /gpt|gemini|claude|openai|anthropic|google/i;
/** heldBack の理由が一致の数を参照していないことを見る */
export const SEAT_COUNT_REFERENCE_RE = /seatCount|一致|[0-9０-９]\s*席|複数の席|全席|三席|二席/;

export class IntegrationError extends Error {
  readonly problems: readonly string[];
  constructor(problems: readonly string[]) {
    super(`統合の器にできない(${problems.length} 件):\n${problems.map((p) => `  - ${p}`).join("\n")}`);
    this.name = "IntegrationError";
    this.problems = problems;
  }
}

type Rec = Record<string, unknown>;
function isRecord(x: unknown): x is Rec {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}
function asArray(x: unknown): unknown[] {
  return Array.isArray(x) ? x : [];
}
/** 鍵の順にそろえた JSON(配列の順は変えない)。observationPacket.ts の canonicalJson と同じ規則だが、packet の module を import しないためにここに持つ */
export function canonicalJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (isRecord(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}
function sha256Of(value: unknown): string {
  return createHash("sha256").update(canonicalJson(value), "utf-8").digest("hex");
}

function loadSchema(name: string): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/${name}`, import.meta.url), "utf-8")) as JsonSchema;
}
export function validateIntegrationInput(input: unknown): string[] {
  return validate(input, loadSchema("integration-input.v0.1.schema.json"));
}
export function validateIntegration(output: unknown): string[] {
  return validate(output, loadSchema("integration.v0.1.schema.json"));
}
export function validateIntegrationLlm(json: unknown): string[] {
  return validate(json, loadSchema("integration.llm.v0.1.schema.json"));
}

// ---- 席の順(runId から決定的。司令塔の判断 2026-09-30) ----

export function seedOfRunId(runId: string): number {
  return Number.parseInt(createHash("sha256").update(runId, "utf-8").digest("hex").slice(0, 8), 16) | 0;
}

/** 0..n-1 の置換(Fisher–Yates、Prng は xorshift32)。同じ runId なら同じ順 */
export function seatPermutation(runId: string, n: number): number[] {
  const prng = new Prng(seedOfRunId(runId));
  const order = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i -= 1) {
    const j = prng.nextInt(i + 1);
    [order[i], order[j]] = [order[j]!, order[i]!];
  }
  return order;
}

// ---- 入力(席の封筒 → 器) ----

export interface SeatSlot {
  seat: Seat;
  /** seat-output.v0.1 の封筒。無ければ absentReason */
  envelope?: Rec;
  absentReason?: string;
}

export interface BuildInputContext {
  runId: string;
  packet: Rec;
  request: Rec;
  seatOrderRef: string;
}

const ITEM_COPY_KEYS = ["hypothesisId", "kind", "factOrHypothesis", "lane", "statement", "observations", "counterEvidence", "prediction", "requestRef", "actionCandidate", "neededObservation"] as const;
const OBS_COPY_KEYS = ["obsId", "path", "value", "unit", "derived", "packetRef"] as const;

/** 席の行を、許した欄だけ写す(internal・origin.seat・subject・knowledge・provenance・status は写さない) */
export function copySeatItem(item: Rec): Rec {
  const out: Rec = {};
  for (const key of ITEM_COPY_KEYS) if (item[key] !== undefined) out[key] = structuredClone(item[key]);
  out.observations = (asArray(item.observations) as Rec[]).map((obs) => {
    const o: Rec = {};
    for (const key of OBS_COPY_KEYS) if (obs[key] !== undefined) o[key] = structuredClone(obs[key]);
    return o;
  });
  if (isRecord(item.counterEvidence)) {
    const ce = item.counterEvidence;
    out.counterEvidence = { attempted: ce.attempted, items: structuredClone(ce.items), result: ce.result };
  }
  const itemId = isRecord(item.origin) ? item.origin.itemId : undefined;
  if (typeof itemId === "string") out.origin = { itemId };
  return out;
}

/** packet の写し(線の組・集計 37 行・局の表だけ。値は写すだけ) */
export function packetDigestOf(packet: Rec): Rec {
  const provenance = packet.provenance as Rec;
  const facts = packet.facts as Rec;
  const aggregates: Rec[] = [];
  for (const a of asArray(packet.aggregates) as Rec[]) {
    const id = String(a.id);
    const base = (part: "numerator" | "denominator" | "value", value: unknown): Rec => {
      const row: Rec = { packetRef: aggregateRef(id, part), value, unit: a.unit };
      return row;
    };
    if (typeof a.value === "number") aggregates.push({ ...base("value", a.value), name: a.name });
    else {
      aggregates.push({ ...base("numerator", a.numerator), name: a.name });
      aggregates.push(base("denominator", a.denominator));
    }
  }
  return {
    thresholds: (asArray(provenance.thresholds) as Rec[]).map((t) => ({ id: t.id, value: t.value, unit: t.unit, from: t.from })),
    aggregates,
    games: (asArray(facts.games) as Rec[]).map((g) => ({ gameId: g.gameId, side: g.side, result: g.result, totalPlyCount: g.totalPlyCount })),
  };
}

export interface ItemMapRow {
  seatIndex: number;
  /** 器の中の匿名の id(`I-<seatIndex>-<連番>`) */
  anonId: string;
  /** 席の封筒の hypothesisId(席名を含みうるので器には入れない) */
  hypothesisId: string;
}

/**
 * 封筒 → 器。席の順は runId から決定的に並べ替え、**席の名前と、席名を含みうる id を器に入れない**:
 * 席の hypothesisId(R2 の形 `H-c5-gpt….`)は席名を埋め込むので、器では `I-<seatIndex>-<連番>` に写し替え、対応表(itemMap)は
 * seatOrder と一緒に run のログ(seatOrderRef)へ。answers[].itemIds も同じ対応で置き換える。
 */
export function buildIntegrationInput(slots: SeatSlot[], ctx: BuildInputContext): { input: Rec; seatOrder: Array<{ seatIndex: number; seat: Seat }>; itemMap: ItemMapRow[] } {
  if (slots.length === 0) throw new IntegrationError(["席が 0"]);
  const order = seatPermutation(ctx.runId, slots.length);
  const seatOrder: Array<{ seatIndex: number; seat: Seat }> = [];
  const itemMap: ItemMapRow[] = [];
  const seats: Rec[] = [];
  order.forEach((slotIndex, position) => {
    const slot = slots[slotIndex]!;
    const seatIndex = position + 1;
    seatOrder.push({ seatIndex, seat: slot.seat });
    if (slot.envelope === undefined) {
      seats.push({ seatIndex, present: false, reason: slot.absentReason ?? "absent" });
      return;
    }
    const env = slot.envelope;
    const idMap = new Map<string, string>();
    (asArray(env.items) as Rec[]).forEach((item, i) => {
      const anonId = `I-${seatIndex}-${String(i + 1).padStart(3, "0")}`;
      idMap.set(String(item.hypothesisId), anonId);
      itemMap.push({ seatIndex, anonId, hypothesisId: String(item.hypothesisId) });
    });
    const mapId = (id: unknown): unknown => (typeof id === "string" && idMap.has(id) ? idMap.get(id) : id);
    seats.push({
      seatIndex,
      present: true,
      items: (asArray(env.items) as Rec[]).map((item) => {
        const copy = copySeatItem(item);
        copy.hypothesisId = mapId(item.hypothesisId);
        if (isRecord(copy.actionCandidate)) copy.actionCandidate = { ...copy.actionCandidate, derivedFrom: asArray(copy.actionCandidate.derivedFrom).map(mapId) };
        return copy;
      }),
      answers: (asArray(env.answers) as Rec[]).map((a) => ({ ...structuredClone(a), itemIds: asArray(a.itemIds).map(mapId) })),
      omissions: structuredClone(env.omissions),
      selfComputedNumbers: structuredClone(env.selfComputedNumbers),
    });
  });
  const request = ctx.request;
  const input: Rec = {
    contract: INTEGRATION_INPUT_CONTRACT,
    schemaVersion: INTEGRATION_SCHEMA_VERSION,
    runId: ctx.runId,
    packetId: String(ctx.packet.packetId),
    requestSha256: sha256Of(request),
    seats,
    packetDigest: packetDigestOf(ctx.packet),
    request: { customerQuestions: structuredClone(request.customerQuestions), requestedScope: structuredClone(request.requestedScope) },
    seatOrderRef: ctx.seatOrderRef,
  };
  const problems = validateIntegrationInput(input);
  if (problems.length > 0) throw new IntegrationError(problems.map((p) => `入力の器: ${p}`));
  return { input, seatOrder, itemMap };
}

// ---- 出力(整理役が書いた形 → 器) ----

export interface CompleteIntegrationContext {
  input: Rec;
  customerRef: string;
  timeLimitSec: number;
  games: number;
  today: string;
  gitHead: string | null;
  model: string;
  modelVersion?: string;
  usage: { inputTokens: number; outputTokens: number };
  finishReason: string;
  attempts: number;
  requestedAt: string;
}

function summaryOf(statuses: string[]): string {
  if (statuses.length === 0) return "no_seat";
  const set = new Set(statuses);
  if (set.size === 1) return statuses[0]!;
  return "mixed";
}

/** 席の答えの内訳と summary(機械で決まる。多数決で unanswerable を消さない: 1 席でも違えば mixed) */
export function answersByQuestionOf(input: Rec): Rec[] {
  const questions = asArray((input.request as Rec).customerQuestions) as Rec[];
  const seats = (asArray(input.seats) as Rec[]).filter((s) => s.present === true);
  return questions.map((q) => {
    const bySeat = seats.map((s) => {
      const a = (asArray(s.answers) as Rec[]).find((x) => x.questionId === q.id);
      return a === undefined
        ? { seatIndex: s.seatIndex, status: "unanswerable", itemRefs: [], missing: [{ what: "この問いへの答えの行", howToMeasure: "席の answers を確かめる" }] }
        : { seatIndex: s.seatIndex, status: a.status, itemRefs: asArray(a.itemIds).map(String), missing: structuredClone(a.missing) };
    });
    return { questionId: q.id, bySeat, summary: summaryOf(bySeat.map((b) => String(b.status))) };
  });
}

export function completeIntegration(llm: unknown, ctx: CompleteIntegrationContext): Rec {
  const schemaProblems = validateIntegrationLlm(llm);
  if (schemaProblems.length > 0) throw new IntegrationError(schemaProblems.map((p) => `整理役が書く形: ${p}`));
  const src = structuredClone(llm) as Rec;
  const inputSha = sha256Of(ctx.input);
  const runToken = `integ${String(ctx.input.runId).toLowerCase().replace(/[^a-z0-9]/g, "").slice(0, 4)}`;
  const completeObs = (obs: Rec): Rec => {
    const path = String((obs.packetRef as Rec | undefined)?.path ?? "");
    const out: Rec = { obsId: packetObsIdOf(path), path: typeof obs.path === "string" ? obs.path : path, value: obs.value };
    if (obs.unit !== undefined) out.unit = obs.unit;
    if (isRecord(obs.derived)) {
      const side = (s: unknown): Rec => ({ obsId: packetObsIdOf(String(isRecord(s) ? s.path ?? "" : "")), value: isRecord(s) ? s.value : undefined });
      out.derived = { kind: obs.derived.kind, numerator: side(obs.derived.numerator), denominator: side(obs.derived.denominator) };
    }
    out.packetRef = obs.packetRef;
    return out;
  };
  const clusters = (asArray(src.clusters) as Rec[]).map((c, i) => {
    const rep = c.representative as Rec;
    const inputs = (asArray(c.itemRefs) as Rec[]).map((r) => seatItemRef(r.seatIndex, r.hypothesisId));
    const line: Rec = {
      schemaVersion: "0.4",
      hypothesisId: `H-${ctx.customerRef}-${runToken}-${String(i + 1).padStart(3, "0")}`,
      subject: { customer: ctx.customerRef, groups: [`${ctx.timeLimitSec} 秒`], gamesCount: ctx.games },
      scope: "this_user",
      lane: rep.lane,
      kind: rep.kind,
      factOrHypothesis: rep.factOrHypothesis,
      origin: { seat: "integrator" },
      statement: rep.statement,
      observations: (asArray(rep.observations) as Rec[]).map(completeObs),
      counterEvidence: (() => {
        const ce = isRecord(rep.counterEvidence) ? rep.counterEvidence : {};
        return {
          attempted: ce.attempted,
          items: (asArray(ce.items) as Rec[]).map((ci) => ({
            kind: ci.kind, text: ci.text,
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
      knowledge: { kind: "discovered", reviewStatus: "draft", origin: { kifu: ctx.customerRef, lane: "llm-integrator" }, range: "this_user" },
      provenance: { gitHead: ctx.gitHead, inputs: [...inputs], excludedInputs: [...INTEGRATOR_EXCLUDED_INPUTS] },
    };
    if (isRecord(rep.prediction)) line.prediction = { writtenAt: ctx.today, ...rep.prediction };
    if (rep.requestRef !== undefined) line.requestRef = rep.requestRef;
    if (rep.neededObservation !== undefined) line.neededObservation = rep.neededObservation;
    const seatIndexes = new Set((asArray(c.itemRefs) as Rec[]).map((r) => Number(r.seatIndex)));
    return { clusterId: c.clusterId, packetRefs: c.packetRefs, itemRefs: c.itemRefs, seatCount: { value: seatIndexes.size, evidence: false }, representative: line };
  });
  const answersByQuestion = answersByQuestionOf(ctx.input);
  for (const note of asArray(src.answerNotes) as Rec[]) {
    const row = answersByQuestion.find((a) => a.questionId === note.questionId);
    if (row !== undefined) row.note = note.text;
  }
  const selfComputedNumbers: Rec[] = [];
  for (const s of asArray(ctx.input.seats) as Rec[]) for (const n of asArray(s.selfComputedNumbers) as Rec[]) selfComputedNumbers.push({ seatIndex: s.seatIndex, ...n });
  const run: Rec = { model: ctx.model, inputSha256: inputSha, requestedAt: ctx.requestedAt, usage: ctx.usage, finishReason: ctx.finishReason, attempts: ctx.attempts };
  if (ctx.modelVersion !== undefined) run.modelVersion = ctx.modelVersion;
  return {
    contract: INTEGRATION_CONTRACT,
    schemaVersion: INTEGRATION_SCHEMA_VERSION,
    runId: ctx.input.runId,
    seatOrderRef: ctx.input.seatOrderRef,
    run,
    clusters,
    contradictions: src.contradictions,
    dropped: src.dropped,
    heldBack: src.heldBack,
    forVerification: src.forVerification,
    answersByQuestion,
    selfComputedNumbers,
  };
}

// ---- 検査 I-1〜I-8(packet を読まない) ----

export interface IntegrationCheckOptions {
  today: string;
  registry?: Set<string>;
  bannedWords?: readonly string[];
  obsItemsPath?: string;
}

const NUMBER_RE = /-?\d+(?:\.\d+)?/g;
function numberTokensOf(text: string): Set<string> {
  return new Set(Array.from(text.matchAll(NUMBER_RE)).map((m) => m[0]));
}
function refKey(r: Rec): string {
  return `${String(r.seatIndex)}:${String(r.hypothesisId)}`;
}
function walkStrings(x: unknown, path: string, onString: (value: string, path: string) => void): void {
  if (typeof x === "string") onString(x, path);
  else if (Array.isArray(x)) x.forEach((item, i) => walkStrings(item, `${path}[${i}]`, onString));
  else if (isRecord(x)) for (const [k, v] of Object.entries(x)) walkStrings(v, `${path}.${k}`, onString);
}

export function integrationProblems(output: unknown, input: unknown, opts: IntegrationCheckOptions): string[] {
  const problems: string[] = [];
  const schemaProblems = validateIntegration(output);
  if (schemaProblems.length > 0) return schemaProblems.map((p) => `schema: ${p}`);
  const inputProblems = validateIntegrationInput(input);
  if (inputProblems.length > 0) return inputProblems.map((p) => `入力の器: ${p}`);
  const out = output as Rec;
  const inp = input as Rec;

  // 入力の項目の索引(present の席だけ)
  const itemsByKey = new Map<string, { seatIndex: number; item: Rec; paths: Set<string> }>();
  for (const s of asArray(inp.seats) as Rec[]) {
    if (s.present !== true) continue;
    for (const item of asArray(s.items) as Rec[]) {
      const paths = new Set((asArray(item.observations) as Rec[]).map((o) => String((o.packetRef as Rec | undefined)?.path ?? "")));
      itemsByKey.set(`${String(s.seatIndex)}:${String(item.hypothesisId)}`, { seatIndex: Number(s.seatIndex), item, paths });
    }
  }
  const clusters = asArray(out.clusters) as Rec[];
  const dropped = asArray(out.dropped) as Rec[];

  // I-1 全項目がちょうど 1 回
  const seen = new Map<string, number>();
  const bump = (key: string, where: string): void => {
    if (!itemsByKey.has(key)) problems.push(`I-1: ${where} の項目「${key}」が入力に無い`);
    seen.set(key, (seen.get(key) ?? 0) + 1);
  };
  clusters.forEach((c) => (asArray(c.itemRefs) as Rec[]).forEach((r) => bump(refKey(r), `clusters[${String(c.clusterId)}]`)));
  dropped.forEach((d, i) => bump(refKey(d.itemRef as Rec), `dropped[${i}]`));
  for (const key of itemsByKey.keys()) {
    const n = seen.get(key) ?? 0;
    if (n === 0) problems.push(`I-1: 入力の項目「${key}」が clusters にも dropped にも無い(黙って落とさない)`);
    if (n > 1) problems.push(`I-1: 入力の項目「${key}」が ${n} 回現れる`);
  }

  // I-2 束の根・I-3 一致は証拠でない・I-4 代表の行
  const registry = opts.registry ?? loadObsRegistry(opts.obsItemsPath ?? new URL("../../../docs/OBSERVATION_ITEMS.md", import.meta.url).pathname);
  const clusterIds = new Set<string>();
  const forVerification = asArray(out.forVerification).map(String);
  const heldBack = asArray(out.heldBack) as Rec[];
  const heldIds = new Set(heldBack.map((h) => String(h.clusterId)));
  clusters.forEach((c) => {
    const cid = String(c.clusterId);
    if (clusterIds.has(cid)) problems.push(`I-2: clusterId「${cid}」が重複`);
    clusterIds.add(cid);
    const roots = asArray(c.packetRefs).map(String);
    for (const root of roots) for (const p of packetRefPathProblems(root)) problems.push(`I-2: ${cid} の packetRefs: ${p}`);
    const members = (asArray(c.itemRefs) as Rec[]).map((r) => itemsByKey.get(refKey(r))).filter((m): m is NonNullable<typeof m> => m !== undefined);
    for (const m of members) {
      if (!roots.some((root) => m.paths.has(root))) problems.push(`I-2: ${cid} の成員「${m.seatIndex}:${String(m.item.hypothesisId)}」が束の根(${roots.join(", ")})を根拠に持たない`);
    }
    const distinct = new Set(members.map((m) => m.seatIndex)).size;
    const sc = c.seatCount as Rec;
    if (sc.value !== distinct) problems.push(`I-3: ${cid} の seatCount.value が ${String(sc.value)}(成員の席は ${distinct})`);
    const inFor = forVerification.includes(cid);
    const inHeld = heldIds.has(cid);
    if (inFor === inHeld) problems.push(`I-3: ${cid} が forVerification と heldBack の${inFor ? "両方に在る" : "どちらにも無い(外すなら理由つきで heldBack へ)"}`);
    // I-4
    const rep = c.representative as Rec;
    const results = validateHypothesisLine(rep, { today: opts.today, registry, ...(opts.bannedWords === undefined ? {} : { bannedWords: opts.bannedWords }) });
    for (const r of results) if (!r.ok) for (const m of r.messages) problems.push(`I-4: ${cid} の representative ${r.check}: ${m}`);
    const union = new Set<string>();
    for (const m of members) for (const p of m.paths) union.add(p);
    for (const o of asArray(rep.observations) as Rec[]) {
      const p = String((o.packetRef as Rec | undefined)?.path ?? "");
      if (!union.has(p)) problems.push(`I-4: ${cid} の representative の観測「${p}」が成員の観測に無い(整理役が根拠を足した)`);
    }
    const kinds = new Set(members.map((m) => String(m.item.kind ?? "hypothesis")));
    if (!kinds.has(String(rep.kind ?? "hypothesis"))) problems.push(`I-4: ${cid} の representative の kind「${String(rep.kind)}」が成員の kind(${[...kinds].join(", ")})に無い`);
    if (isRecord(rep.origin) && rep.origin.seat !== "integrator") problems.push(`I-7: ${cid} の representative.origin.seat が integrator でない`);
  });
  for (const id of forVerification) if (!clusterIds.has(id)) problems.push(`I-3: forVerification の「${id}」が clusters に無い`);
  heldBack.forEach((h, i) => {
    if (!clusterIds.has(String(h.clusterId))) problems.push(`I-3: heldBack[${i}] の「${String(h.clusterId)}」が clusters に無い`);
    const reason = String(h.reason ?? "");
    if (reason.trim().length === 0) problems.push(`I-3: heldBack[${i}] の理由が空`);
    if (SEAT_COUNT_REFERENCE_RE.test(reason)) problems.push(`I-3: heldBack[${i}] の理由が一致の数を参照している(seatCount は理由にしない)`);
  });

  // I-5 問い(機械で決まる内訳と一致)
  const expected = answersByQuestionOf(inp);
  const actual = asArray(out.answersByQuestion) as Rec[];
  const stripNote = (rows: Rec[]): string => canonicalJson(rows.map((r) => ({ questionId: r.questionId, bySeat: r.bySeat, summary: r.summary })));
  if (stripNote(actual) !== stripNote(expected)) problems.push("I-5: answersByQuestion が席の answers から機械で決まる内訳・summary と違う(多数決で答えを変えない)");

  // I-6 隔離
  const texts: string[] = [];
  for (const c of clusters) {
    const rep = c.representative as Rec;
    texts.push(String(rep.statement ?? ""));
    for (const ci of asArray((rep.counterEvidence as Rec | undefined)?.items) as Rec[]) texts.push(String(ci.text ?? ""));
  }
  for (const x of asArray(out.contradictions) as Rec[]) texts.push(String(x.text ?? ""));
  for (const a of actual) texts.push(String(a.note ?? ""));
  const tokens = new Set<string>();
  for (const t of texts) for (const tok of numberTokensOf(t)) tokens.add(tok);
  (asArray(out.selfComputedNumbers) as Rec[]).forEach((s, i) => {
    const token = JSON.stringify(s.value);
    if (tokens.has(token)) problems.push(`I-6: selfComputedNumbers[${i}] の値「${token}」が代表の文・矛盾・注に出ている`);
  });

  // I-7 席名
  walkStrings(out, "output", (value, path) => {
    if (path === "output.run.model" || path === "output.run.modelVersion") return;
    if (SEAT_NAME_RE.test(value)) problems.push(`I-7: ${path} に席の名前らしい語(${value.match(SEAT_NAME_RE)![0]})`);
  });
  if (typeof out.seatOrderRef !== "string" || out.seatOrderRef.length === 0) problems.push("I-7: seatOrderRef が無い");

  // I-8 run
  const inputSha = sha256Of(inp);
  const run = out.run as Rec;
  if (run.inputSha256 !== inputSha) problems.push("I-8: run.inputSha256 が入力の器の sha と違う(別の入力で得た出力)");
  clusters.forEach((c) => {
    const inputs = new Set(asArray(((c.representative as Rec).provenance as Rec | undefined)?.inputs).map(String));
    const expected = new Set((asArray(c.itemRefs) as Rec[]).map((r) => seatItemRef(r.seatIndex, r.hypothesisId)));
    const same = inputs.size === expected.size && [...expected].every((x) => inputs.has(x));
    if (!same) problems.push(`I-8: ${String(c.clusterId)} の representative.provenance.inputs が束の成員(seat_item:…)と一致しない`);
  });
  return problems;
}
