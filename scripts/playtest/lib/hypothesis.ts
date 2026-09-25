// STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2、設計案 docs/DESIGN_OBSERVATION_LAYER_2026-09.md §7・§7.2)。
// 仮説の記録形式(契約 hypothesis)のスキーマ読み込みと、機械検査 H-1〜H-8。
// 版は v0.1 と v0.2 の 2 つ(STEP EXPO-1 §12.9。v0.2 は `knowledge.reviewStatus` に `expired` を足しただけ)。
// **照合に使う版は行の `schemaVersion` が決める**(古い記録は v0.1 のまま今までどおり通る)。
//
// 【このファイルがやること】
// - `loadHypothesisSchema()`: スキーマのファイル(../schemas/hypothesis.v<version>.schema.json)を読む。
// - `loadObsRegistry(mdPath)`: `docs/OBSERVATION_ITEMS.md` の §1(`## 1.` から `## 2.` の手前)の表の先頭欄にある
//   `obs.*` を全部 + `obs.timeSearch.col.` × `SEARCH_COLUMNS`(30 本。列の全部が表に書かれていないため、
//   `lib/timeSearch.ts` の実物から作る)。
// - `validateHypothesisLine(line, opts)`: スキーマ照合(lib/eventSchema.ts)+ H-1〜H-8 を**全部回して全部返す**
//   (最初の失敗で止めない)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・仮説の妥当性の判断(機械で検査できる「形式」だけを見る。F-1 の型 ― 設計案 §7.2 の注記)。
// - ファイルの書き換え。エンジンの起動。
// - 検査 3(禁止語)の一覧を書き写して 2 か所で持つこと(`HYPOTHESIS_BANNED_WORDS` は
//   `report-pdf/check_answer.py` の `BANNED_WORDS` とパリティ試験で一致を見る。lib/hypothesis.test.ts)。

import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import { HYPOTHESIS_SCHEMA_VERSION, KNOWN_HYPOTHESIS_SCHEMA_VERSIONS } from "./schemaVersions.js";
import { SEARCH_COLUMNS } from "./timeSearch.js";

export type HypothesisSchemaVersion = (typeof KNOWN_HYPOTHESIS_SCHEMA_VERSIONS)[number];

/** 行の `schemaVersion` がスキーマのファイルがある版かどうか(未知の版は照合の相手を選べない)。 */
export function isKnownHypothesisSchemaVersion(value: unknown): value is HypothesisSchemaVersion {
  return typeof value === "string" && (KNOWN_HYPOTHESIS_SCHEMA_VERSIONS as readonly string[]).includes(value);
}

/** 契約 hypothesis の 1 行(観測 → 仮説 → 反証 → 予測)。設計案 §7.1。値の中身は検査 H-1〜H-8 が見る。 */
export interface HypothesisLine {
  /** 0.1 か 0.2。0.2 は `knowledge.reviewStatus` に `expired` を足した版(STEP EXPO-1) */
  schemaVersion: HypothesisSchemaVersion;
  hypothesisId: string;
  subject: { customer: string; groups: string[]; gamesCount: number };
  scope: "this_user" | "beginners_general";
  lane: "time" | "side" | "shape" | "prior" | "alternative";
  statement: string;
  observations: HypothesisObservation[];
  counterEvidence: {
    attempted: boolean;
    items: Array<{ kind: "counterexample" | "denominator" | "alternative"; text: string; observations: HypothesisItemObservation[] }>;
    result: "stands" | "weakened" | "refuted" | "none_found";
    provenance: { inputs: string[] };
  };
  prediction: {
    writtenAt: string;
    window: string;
    metric: string;
    comparator: "<=" | "<" | ">=" | ">" | "==";
    value: number;
    alsoRequires: Array<{ metric: string; comparator: "<=" | "<" | ">=" | ">" | "=="; value: number }>;
  };
  status: "proposed" | "stands_after_refutation" | "weak" | "refuted" | "verified" | "missed" | "partial" | "unmeasured" | "expired";
  knowledge: {
    kind: "shogi" | "discovered" | "coaching";
    /** `expired`(失効)は版 0.2 から。露出は `draft` と同じで、H-7 は expired を beginners_general に上げない */
    reviewStatus: "draft" | "human_reviewed" | "expert_verified" | "expired";
    origin: { kifu: string; lane: string };
    range: "this_user" | "beginners_general";
  };
  provenance: { gitHead: string | null; inputs: string[]; excludedInputs: string[] };
}

export interface HypothesisObservation {
  obsId: string;
  path: string;
  value: unknown;
  unit?: string;
  derived?: {
    kind: "percent" | "share10" | "ratio";
    numerator: { obsId: string; value: number };
    denominator: { obsId: string; value: number };
  };
}

export interface HypothesisItemObservation {
  obsId: string;
  path?: string;
  value: unknown;
  unit?: string;
}

/** 検査 3(禁止語・表現)。`report-pdf/check_answer.py` の `BANNED_WORDS`(26 語)と並びまで同じ(パリティ試験で見る)。 */
export const HYPOTHESIS_BANNED_WORDS: readonly string[] = [
  "悪手",
  "弱点",
  "癖",
  "型",
  "傾向",
  "原因",
  "ミス",
  "見落とし",
  "改善",
  "練習",
  "必ず",
  "明らか",
  "あなた",
  "ご自身",
  "いつも",
  "がち",
  "クセ",
  "パターン",
  "すべき",
  "した方がよい",
  "すれば直る",
  "間違いなく",
  "危ない",
  "確実",
  "絶対",
  "安い",
];

export function loadHypothesisSchema(version: HypothesisSchemaVersion = HYPOTHESIS_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/hypothesis.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/**
 * `docs/OBSERVATION_ITEMS.md` の §1(`existing`)を登録簿にする(H-2 の検査 H-2 が引く集合)。
 * §1 の表の行のうち `| \`obs.` で始まる行の先頭欄にある `obs.*` を全部(1 セルに複数ある行は全部)、
 * + `obs.timeSearch.col.` × `SEARCH_COLUMNS`(30 本。§1.7 の表は 5〜6 本ずつ束ねて書いてあり、
 * 先頭以外は `.name` の略記で `obs.` を持たないため、正本の `SEARCH_COLUMNS` から作る)。
 */
export function loadObsRegistry(mdPath: string): Set<string> {
  const text = readFileSync(mdPath, "utf-8");
  const lines = text.split("\n");
  const startIndex = lines.findIndex((line) => line.startsWith("## 1. "));
  if (startIndex === -1) throw new Error(`${mdPath}: "## 1. " の見出しが無い`);
  const endOffset = lines.slice(startIndex + 1).findIndex((line) => line.startsWith("## 2. "));
  const endIndex = endOffset === -1 ? lines.length : startIndex + 1 + endOffset;
  const ids = new Set<string>();
  for (const line of lines.slice(startIndex, endIndex)) {
    if (!line.startsWith("| `obs.")) continue;
    const firstCell = line.split("|")[1] ?? "";
    for (const match of firstCell.matchAll(/obs\.[\w.]+/g)) ids.add(match[0]);
  }
  for (const column of SEARCH_COLUMNS) ids.add(`obs.timeSearch.col.${column}`);
  return ids;
}

export type HypothesisCheckName = "schema" | "H-1" | "H-2" | "H-3" | "H-4" | "H-5" | "H-6" | "H-7" | "H-8";

export interface CheckResult {
  check: HypothesisCheckName;
  ok: boolean;
  messages: string[];
}

// ---- 小さな安全なアクセサ(型が違っても例外を投げず、通れなかった理由を messages に積む側で使う) ----

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function get(value: unknown, path: readonly string[]): unknown {
  let cur: unknown = value;
  for (const key of path) {
    if (!isRecord(cur)) return undefined;
    cur = cur[key];
  }
  return cur;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asStringArray(value: unknown): string[] {
  return asArray(value).filter((item): item is string => typeof item === "string");
}

// ---- H-1: 数の実在 ----

function collectValueNumbers(value: unknown, out: Set<number>): void {
  if (typeof value === "boolean") return;
  if (typeof value === "number") {
    if (Number.isFinite(value)) {
      out.add(Math.abs(Math.round(value)));
      out.add(value);
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectValueNumbers(item, out);
    return;
  }
  if (isRecord(value)) {
    for (const item of Object.values(value)) collectValueNumbers(item, out);
  }
}

function buildAllowedNumberSet(line: unknown): Set<number> {
  const out = new Set<number>();
  for (const obs of asArray(get(line, ["observations"]))) collectValueNumbers(get(obs, ["value"]), out);
  for (const item of asArray(get(line, ["counterEvidence", "items"]))) {
    for (const obs of asArray(get(item, ["observations"]))) collectValueNumbers(get(obs, ["value"]), out);
  }
  return out;
}

type RatioKind = "percent" | "share10" | "ratio";

function ratioKindOfWord(word: string): RatioKind | null {
  if (word === "%" || word === "%") return "percent";
  if (word === "％") return "percent";
  if (word === "割") return "share10";
  if (word === "倍") return "ratio";
  return null;
}

function normalizeFullWidthDigits(text: string): string {
  return text.replace(/[０-９]/g, (ch) => String.fromCharCode(ch.charCodeAt(0) - 0xff10 + 0x30));
}

interface ExtractedNumber {
  raw: string;
  value: number;
  ratioKind: RatioKind | null;
}

function extractNumbers(text: string): ExtractedNumber[] {
  const normalized = normalizeFullWidthDigits(text);
  const out: ExtractedNumber[] = [];
  const re = /\d+(?:\.\d+)?/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(normalized)) !== null) {
    const raw = match[0];
    const isDecimal = raw.includes(".");
    const value = isDecimal ? Number.parseFloat(raw) : Math.abs(Number.parseInt(raw, 10));
    const after = normalized.slice(match.index + raw.length);
    const wordMatch = /^\s*(%|％|割|倍)/.exec(after);
    const ratioKind = wordMatch ? ratioKindOfWord(wordMatch[1]!) : null;
    out.push({ raw, value, ratioKind });
  }
  return out;
}

function recomputeDerived(derived: unknown, kind: RatioKind): number | undefined {
  if (!isRecord(derived) || derived.kind !== kind) return undefined;
  const n = get(derived, ["numerator", "value"]);
  const d = get(derived, ["denominator", "value"]);
  if (typeof n !== "number" || typeof d !== "number" || d === 0) return undefined;
  switch (kind) {
    case "percent":
      return Math.round((100 * n) / d);
    case "share10":
      return Math.round((10 * n) / d);
    case "ratio":
      return Math.round((n / d) * 10) / 10;
  }
}

function checkH1(line: unknown): CheckResult {
  const messages: string[] = [];
  const statement = asString(get(line, ["statement"])) ?? "";
  const texts: Array<{ source: string; text: string }> = [{ source: "statement", text: statement }];
  asArray(get(line, ["counterEvidence", "items"])).forEach((item, index) => {
    const text = asString(get(item, ["text"]));
    if (text !== undefined) texts.push({ source: `counterEvidence.items[${index}].text`, text });
  });
  const allowed = buildAllowedNumberSet(line);
  const derivedList = asArray(get(line, ["observations"])).map((obs) => get(obs, ["derived"]));

  for (const { source, text } of texts) {
    for (const num of extractNumbers(text)) {
      if (num.ratioKind !== null) {
        const matched = derivedList.some((derived) => recomputeDerived(derived, num.ratioKind!) === num.value);
        if (!matched) messages.push(`${source}: 「${num.raw}」に一致する derived の再計算が無い(組が無い)`);
      } else if (!allowed.has(num.value)) {
        messages.push(`${source}: 数「${num.raw}」が observations の値に無い`);
      }
    }
  }
  return { check: "H-1", ok: messages.length === 0, messages };
}

// ---- H-2: ID の登録 ----

function extractObsIdTokens(text: string): string[] {
  return Array.from(text.matchAll(/obs\.[\w.]+/g)).map((match) => match[0]);
}

function collectObsIdsForH2(line: unknown): string[] {
  const ids: string[] = [];
  for (const obs of asArray(get(line, ["observations"]))) {
    const obsId = asString(get(obs, ["obsId"]));
    if (obsId !== undefined) ids.push(obsId);
    const derived = get(obs, ["derived"]);
    if (isRecord(derived)) {
      const numeratorId = asString(get(derived, ["numerator", "obsId"]));
      const denominatorId = asString(get(derived, ["denominator", "obsId"]));
      if (numeratorId !== undefined) ids.push(numeratorId);
      if (denominatorId !== undefined) ids.push(denominatorId);
    }
  }
  for (const item of asArray(get(line, ["counterEvidence", "items"]))) {
    for (const obs of asArray(get(item, ["observations"]))) {
      const obsId = asString(get(obs, ["obsId"]));
      if (obsId !== undefined) ids.push(obsId);
    }
  }
  const metric = asString(get(line, ["prediction", "metric"]));
  if (metric !== undefined) ids.push(...extractObsIdTokens(metric));
  for (const req of asArray(get(line, ["prediction", "alsoRequires"]))) {
    const reqMetric = asString(get(req, ["metric"]));
    if (reqMetric !== undefined) ids.push(...extractObsIdTokens(reqMetric));
  }
  return ids;
}

function checkH2(line: unknown, registry: Set<string>): CheckResult {
  const unknownIds = [...new Set(collectObsIdsForH2(line))].filter((id) => !registry.has(id));
  return {
    check: "H-2",
    ok: unknownIds.length === 0,
    messages: unknownIds.length === 0 ? [] : [`登録簿に無い obsId: ${unknownIds.join(", ")}`],
  };
}

// ---- H-3: 反証を試みたことの記録(「無い」を空で埋めない) ----

function checkH3(line: unknown): CheckResult {
  const messages: string[] = [];
  const attempted = asBoolean(get(line, ["counterEvidence", "attempted"]));
  const items = asArray(get(line, ["counterEvidence", "items"]));
  const result = asString(get(line, ["counterEvidence", "result"]));
  if (attempted !== true) messages.push("counterEvidence.attempted が true でない");
  if (items.length === 0) {
    if (result !== "none_found") messages.push('items が空なのに counterEvidence.result が "none_found" でない');
  } else if (result === "none_found") {
    messages.push('items があるのに counterEvidence.result が "none_found"');
  }
  return { check: "H-3", ok: messages.length === 0, messages };
}

// ---- H-4: 予測は数で、測る前に書く ----

const PREDICTION_REQUIRED_FIELDS = ["metric", "comparator", "value", "window", "writtenAt"] as const;
const ALSO_REQUIRES_FIELDS = ["metric", "comparator", "value"] as const;

function checkH4(line: unknown, today: string): CheckResult {
  const messages: string[] = [];
  const prediction = get(line, ["prediction"]);
  if (!isRecord(prediction)) {
    return { check: "H-4", ok: false, messages: ["prediction が無い"] };
  }
  for (const field of PREDICTION_REQUIRED_FIELDS) {
    if (!Object.hasOwn(prediction, field) || prediction[field] === undefined) messages.push(`prediction.${field} が無い`);
  }
  const writtenAt = asString(prediction.writtenAt);
  if (writtenAt !== undefined && !(writtenAt <= today)) {
    messages.push(`prediction.writtenAt(${writtenAt})が --today(${today})より後`);
  }
  asArray(prediction.alsoRequires).forEach((req, index) => {
    for (const field of ALSO_REQUIRES_FIELDS) {
      if (!isRecord(req) || !Object.hasOwn(req, field) || req[field] === undefined) {
        messages.push(`prediction.alsoRequires[${index}].${field} が無い`);
      }
    }
  });
  return { check: "H-4", ok: messages.length === 0, messages };
}

// ---- H-5: 禁止語・断定しない形 ----

function checkH5(line: unknown): CheckResult {
  const messages: string[] = [];
  const statement = asString(get(line, ["statement"])) ?? "";
  const texts: Array<{ source: string; text: string }> = [{ source: "statement", text: statement }];
  asArray(get(line, ["counterEvidence", "items"])).forEach((item, index) => {
    const text = asString(get(item, ["text"]));
    if (text !== undefined) texts.push({ source: `counterEvidence.items[${index}].text`, text });
  });
  for (const { source, text } of texts) {
    for (const word of HYPOTHESIS_BANNED_WORDS) {
      if (text.includes(word)) messages.push(`${source}: 禁止語「${word}」を含む`);
    }
  }
  if (!(statement.includes("という読みです") || statement.includes("可能性があります"))) {
    messages.push('statement が「という読みです」「可能性があります」の形でない');
  }
  return { check: "H-5", ok: messages.length === 0, messages };
}

// ---- H-6: 盲検(反証レーンに他レーンの出力・本人の言葉を渡さない) ----

const H6_FORBIDDEN_WORDS = ["本人の言葉", "hypothes", "統合", "integrat"] as const;

function checkH6(line: unknown): CheckResult {
  const messages: string[] = [];
  const topInputs = asStringArray(get(line, ["provenance", "inputs"]));
  const ceInputs = asStringArray(get(line, ["counterEvidence", "provenance", "inputs"]));
  const topSet = new Set(topInputs);
  for (const input of ceInputs) {
    if (!topSet.has(input)) messages.push(`counterEvidence.provenance.inputs の「${input}」が provenance.inputs の部分集合でない`);
  }
  for (const input of [...topInputs, ...ceInputs]) {
    for (const word of H6_FORBIDDEN_WORDS) {
      if (input.includes(word)) messages.push(`inputs の「${input}」に盲検の禁止語「${word}」を含む`);
    }
  }
  const excluded = asStringArray(get(line, ["provenance", "excludedInputs"]));
  for (const path of excluded) {
    if (path.includes("本人の言葉") && topSet.has(path)) {
      messages.push(`provenance.excludedInputs の「${path}」が provenance.inputs にもある`);
    }
  }
  return { check: "H-6", ok: messages.length === 0, messages };
}

// ---- H-7: 昇格は human_reviewed 以上だけ ----

function checkH7(line: unknown): CheckResult {
  const messages: string[] = [];
  const scope = asString(get(line, ["scope"]));
  const reviewStatus = asString(get(line, ["knowledge", "reviewStatus"]));
  const range = asString(get(line, ["knowledge", "range"]));
  if (scope === "beginners_general" && reviewStatus !== "human_reviewed" && reviewStatus !== "expert_verified") {
    messages.push("scope が beginners_general なのに knowledge.reviewStatus が human_reviewed / expert_verified でない");
  }
  if (scope !== undefined && range !== undefined && range !== scope) {
    messages.push(`knowledge.range(${range})が scope(${scope})と一致しない`);
  }
  return { check: "H-7", ok: messages.length === 0, messages };
}

// ---- H-8: 人名・絶対パスを持たない ----

function collectStringsForH8(line: unknown): Array<{ path: string; value: string }> {
  const out: Array<{ path: string; value: string }> = [];
  const hypothesisId = asString(get(line, ["hypothesisId"]));
  if (hypothesisId !== undefined) out.push({ path: "hypothesisId", value: hypothesisId });
  const customer = asString(get(line, ["subject", "customer"]));
  if (customer !== undefined) out.push({ path: "subject.customer", value: customer });

  const collectRecursive = (value: unknown, path: string): void => {
    if (typeof value === "string") {
      out.push({ path, value });
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item, index) => collectRecursive(item, `${path}[${index}]`));
      return;
    }
    if (isRecord(value)) {
      for (const [key, item] of Object.entries(value)) collectRecursive(item, `${path}.${key}`);
    }
  };
  collectRecursive(get(line, ["provenance"]), "provenance");
  collectRecursive(get(line, ["knowledge", "origin"]), "knowledge.origin");
  collectRecursive(get(line, ["counterEvidence", "provenance", "inputs"]), "counterEvidence.provenance.inputs");
  return out;
}

function checkH8(line: unknown): CheckResult {
  const messages: string[] = [];
  for (const { path, value } of collectStringsForH8(line)) {
    if (value.startsWith("/")) messages.push(`${path} が絶対パス「${value}」`);
    if (value.includes("@")) messages.push(`${path} にメールの記号を含む「${value}」`);
    if (value.includes("~")) messages.push(`${path} に「~」を含む「${value}」`);
  }
  return { check: "H-8", ok: messages.length === 0, messages };
}

/**
 * 行の `schemaVersion` に対応するスキーマを選ぶ(STEP EXPO-1)。
 * `opts.schema` が渡されたときはそれを使う(呼び出し側が版を固定したい試験のための差し替え口)。
 * 版がスキーマのファイルの一覧に無いときは照合の相手が決まらないので、そのことを message にして返す。
 */
function resolveSchema(line: unknown, override?: JsonSchema): { schema: JsonSchema } | { error: string } {
  if (override !== undefined) return { schema: override };
  const version = isRecord(line) ? line.schemaVersion : undefined;
  if (!isKnownHypothesisSchemaVersion(version)) {
    return {
      error: `schemaVersion が版の一覧(${KNOWN_HYPOTHESIS_SCHEMA_VERSIONS.join(" / ")})に無い: ${JSON.stringify(version)}`,
    };
  }
  return { schema: loadHypothesisSchema(version) };
}

/** スキーマ照合 + H-1〜H-8 を全部回して全部返す(最初で止めない)。スキーマが落ちても H は回す。 */
export function validateHypothesisLine(line: unknown, opts: { today: string; registry: Set<string>; schema?: JsonSchema }): CheckResult[] {
  const resolved = resolveSchema(line, opts.schema);
  const schemaErrors = "error" in resolved ? [resolved.error] : validate(line, resolved.schema);
  return [
    { check: "schema", ok: schemaErrors.length === 0, messages: schemaErrors },
    checkH1(line),
    checkH2(line, opts.registry),
    checkH3(line),
    checkH4(line, opts.today),
    checkH5(line),
    checkH6(line),
    checkH7(line),
    checkH8(line),
  ];
}
