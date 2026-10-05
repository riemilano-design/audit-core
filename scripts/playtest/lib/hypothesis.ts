// STEP OBS-2(docs/LANE_DIAG_LOG_2026-09.md §12.2、設計案 docs/DESIGN_OBSERVATION_LAYER_2026-09.md §7・§7.2)。
// 仮説の記録形式(契約 hypothesis)のスキーマ読み込みと、機械検査 H-1〜H-8。
// 版は v0.1・v0.2・v0.3 の 3 つ(STEP EXPO-1 §12.9。v0.2 は `knowledge.reviewStatus` に `expired` を足しただけ。
// v0.3 は `lane` の enum に `reply`・`fork` を足しただけ ― 契約の仮説 v0.3、2026-09-26)。
// **照合に使う版は行の `schemaVersion` が決める**(古い記録は v0.1・v0.2 のまま今までどおり通る)。
//
// 【このファイルがやること】
// - `loadHypothesisSchema()`: スキーマのファイル(../schemas/hypothesis.v<version>.schema.json)を読む。
// - `loadObsRegistry(mdPath, extraIds?)`: `docs/OBSERVATION_ITEMS.md` の §1(`## 1.` から `## 2.` の手前)の表の先頭欄にある
//   `obs.*` を全部 + 表から読めない id の補い `extraIds`(既定は仕様データ `../schemas/obs-registry.extra-ids.json`。
//   中身は §1.7 の 30 列。Audit Core T-3 で `lib/timeSearch.ts` の `SEARCH_COLUMNS` の import を外した ―
//   この lib は将棋側の module を読まず、正本との一致は `lib/hypothesis.test.ts` のパリティ試験が固定する)。
// - `validateHypothesisLine(line, opts)`: スキーマ照合(lib/eventSchema.ts)+ H-1〜H-8 を**全部回して全部返す**
//   (最初の失敗で止めない)。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・仮説の妥当性の判断(機械で検査できる「形式」だけを見る。F-1 の型 ― 設計案 §7.2 の注記)。
// - ファイルの書き換え。エンジンの起動。
// - 検査 3(禁止語)の一覧を書き写して 2 か所で持つこと。**一覧は `data/governance/banned_words.json` だけが持ち**、
//   この lib は `loadHypothesisBannedWords()` で、`report-pdf/check_answer.py` は `BANNED_WORDS` でそれを読む
//   (STEP H5-SYNC、§12.9。Audit Core T-3 で Python のソースを正規表現で読む形から JSON に移した。
//   人間の決定 `f715da2` で語を外すときも、直す場所は 1 か所)。
//   **読めないときは黙って空にせず例外を投げる**(「検査したが 0 件」と「検査していない」を
//   同じ結果にしない。docs/AGENT_PROTOCOL.md 11.6)。

import { readFileSync } from "node:fs";
import { validate, type JsonSchema } from "./eventSchema.js";
import { recountRowProblems } from "./observationAggregates.js";
import { canonicalJson, resolvePacketPath } from "./observationPacket.js";
import { AGGREGATE_PARTS, PACKET_OBS_ID_PREFIX, isPacketObsId, packetRefPathProblems } from "./packetRef.js";
import { HYPOTHESIS_SCHEMA_VERSION, KNOWN_HYPOTHESIS_SCHEMA_VERSIONS } from "./schemaVersions.js";

export type HypothesisSchemaVersion = (typeof KNOWN_HYPOTHESIS_SCHEMA_VERSIONS)[number];

/** 行の `schemaVersion` がスキーマのファイルがある版かどうか(未知の版は照合の相手を選べない)。 */
export function isKnownHypothesisSchemaVersion(value: unknown): value is HypothesisSchemaVersion {
  return typeof value === "string" && (KNOWN_HYPOTHESIS_SCHEMA_VERSIONS as readonly string[]).includes(value);
}

/** 契約 hypothesis の 1 行(観測 → 仮説 → 反証 → 予測)。設計案 §7.1。値の中身は検査 H-1〜H-8 が見る。 */
export interface HypothesisLine {
  /** 0.1・0.2・0.3・0.4。0.2 は `knowledge.reviewStatus` に `expired` を足した版(STEP EXPO-1)。0.3 は `lane` に `reply`・`fork` を足した版。0.4 は席の出力の欄を足した版(STEP R2。下の任意の欄) */
  schemaVersion: HypothesisSchemaVersion;
  /** 0.4 から。項目の種類(無ければ hypothesis) */
  kind?: HypothesisKind;
  /** 0.4 から。事実と読みの区別(無ければ hypothesis) */
  factOrHypothesis?: "fact" | "hypothesis";
  origin?: { seat: "gpt" | "gemini" | "claude" | "integrator" | "human"; itemId?: string };
  requestRef?: { questionId: string };
  actionCandidate?: { text: string; derivedFrom: string[]; menuMatch: string | null };
  neededObservation?: { what: string; whyNotInPacket: string; howToMeasure: string };
  /** 席の自由分析。**検査は読まない**。下流の器は欄を持たない(人間の決定 2026-09-30) */
  internal?: { reasoning: string; namesOutsideVocabulary?: string[] };
  hypothesisId: string;
  subject: { customer: string; groups: string[]; gamesCount: number };
  scope: "this_user" | "beginners_general";
  /** `reply`・`fork` は版 0.3 から(それ以前の版の行では出ない) */
  lane: "time" | "side" | "shape" | "prior" | "alternative" | "reply" | "fork";
  statement: string;
  observations: HypothesisObservation[];
  counterEvidence: {
    attempted: boolean;
    items: Array<{ kind: "counterexample" | "denominator" | "alternative"; text: string; observations: HypothesisItemObservation[] }>;
    result: "stands" | "weakened" | "refuted" | "none_found";
    provenance: { inputs: string[] };
  };
  /** 0.4 では schema 上は任意。H-4 が kind で必須を決める(hypothesis / answer_candidate は必須) */
  prediction?: {
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

export type HypothesisKind = "finding" | "hypothesis" | "answer_candidate" | "action_candidate" | "unanswerable" | "needed_observation";

export interface HypothesisObservation {
  obsId: string;
  path: string;
  value: unknown;
  unit?: string;
  /** 0.4 から。packet の中の場所(文法は lib/packetRef.ts。実在は H-9 = 自動化レーンの検証器) */
  packetRef?: { path: string; provenanceId?: string };
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

/** 禁止語の一覧の出どころ(governance の仕様データ)。写しを持たないための 1 か所。Python 側の検査 3 も同じファイルを読む。 */
const BANNED_WORDS_JSON = new URL("../../../data/governance/banned_words.json", import.meta.url);

/** 登録簿の表から読めない id の補い(仕様データ)。`loadObsRegistry` の `extraIds` の既定値。 */
const OBS_REGISTRY_EXTRA_IDS_JSON = new URL("../schemas/obs-registry.extra-ids.json", import.meta.url);

/** 仕様データ(JSON)の `key` にある文字列の配列を返す。無い・形が違う・JSON でないときは undefined(呼ぶ側が例外にする)。 */
function stringListOf(source: string, key: string): readonly string[] | undefined {
  let parsed: unknown;
  try {
    parsed = JSON.parse(source);
  } catch {
    return undefined;
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) return undefined;
  const value = (parsed as Record<string, unknown>)[key];
  return Array.isArray(value) && value.every((v) => typeof v === "string") ? (value as string[]) : undefined;
}

/** 禁止語の一覧を読めなかったとき(ファイルが無い・`BANNED_WORDS` が見つからない)。 */
export class HypothesisBannedWordsError extends Error {}

/** 1 回読んだら覚えておく(同じ実行の中でファイルを何度も読まない)。 */
let bannedWordsCache: readonly string[] | undefined;

/**
 * 検査 H-5(禁止語)の一覧を `data/governance/banned_words.json` の `words` から読む(STEP H5-SYNC → Audit Core T-3)。
 *
 * **一覧の写しをこのファイルに持たない。** 2026-09-25 の人間の決定(`f715da2`)で語を外すときも、
 * 直すのは JSON 1 か所で、この lib と python 側(`check_answer.py`)は読むだけになる。
 * **一覧が空になっても H-5 は消えない** ― 「という読みです / 可能性があります の形」の検査は残る。
 *
 * 読めないとき(ファイルが無い・`words` が見つからない)は**例外**にする。
 * 黙って空の一覧にすると「語が 0 件だった」と「検査していない」が見分けられなくなるため。
 */
export function loadHypothesisBannedWords(jsonPath: URL | string = BANNED_WORDS_JSON): readonly string[] {
  let source: string;
  try {
    source = readFileSync(jsonPath, "utf-8");
  } catch (err) {
    throw new HypothesisBannedWordsError(`禁止語の一覧を読めません: ${String(jsonPath)}(${(err as Error).message})`);
  }
  const words = stringListOf(source, "words");
  if (words === undefined) {
    throw new HypothesisBannedWordsError(`禁止語の一覧(words)が見つかりません: ${String(jsonPath)}`);
  }
  return words;
}

/** 登録簿の補いの一覧を読めなかったとき(ファイルが無い・`ids` が見つからない)。 */
export class ObsRegistryExtraIdsError extends Error {}

/** 1 回読んだら覚えておく(同じ実行の中でファイルを何度も読まない)。 */
let obsRegistryExtraIdsCache: readonly string[] | undefined;

/**
 * 登録簿(§1 の表)から読めない id の補いを仕様データ `../schemas/obs-registry.extra-ids.json` の `ids` から読む。
 * 中身は §1.7 の 30 列(`obs.timeSearch.col.<列名>`)で、正本 `lib/timeSearch.ts` の `SEARCH_COLUMNS` との一致は
 * `lib/hypothesis.test.ts` のパリティ試験が固定する(この lib は将棋側の module を import しない ― Audit Core T-3)。
 * 読めないときは**例外**(黙って空にすると「補いが 0 件」と「読んでいない」が見分けられない)。
 */
export function loadObsRegistryExtraIds(jsonPath: URL | string = OBS_REGISTRY_EXTRA_IDS_JSON): readonly string[] {
  let source: string;
  try {
    source = readFileSync(jsonPath, "utf-8");
  } catch (err) {
    throw new ObsRegistryExtraIdsError(`登録簿の補いを読めません: ${String(jsonPath)}(${(err as Error).message})`);
  }
  const ids = stringListOf(source, "ids");
  if (ids === undefined) {
    throw new ObsRegistryExtraIdsError(`登録簿の補い(ids)が見つかりません: ${String(jsonPath)}`);
  }
  return ids;
}

/** 既定の補い(1 回だけ読む)。`loadObsRegistry` に `extraIds` が渡されたときはそちらを使う。 */
function defaultObsRegistryExtraIds(): readonly string[] {
  obsRegistryExtraIdsCache ??= loadObsRegistryExtraIds();
  return obsRegistryExtraIdsCache;
}

/** 既定の一覧(1 回だけ読む)。`opts.bannedWords` が渡されたときはそちらを使う。 */
function defaultBannedWords(): readonly string[] {
  bannedWordsCache ??= loadHypothesisBannedWords();
  return bannedWordsCache;
}

export function loadHypothesisSchema(version: HypothesisSchemaVersion = HYPOTHESIS_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/hypothesis.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/**
 * `docs/OBSERVATION_ITEMS.md` の §1(`existing`)を登録簿にする(H-2 の検査 H-2 が引く集合)。
 * §1 の表の行のうち `| \`obs.` で始まる行の先頭欄にある `obs.*` を全部(1 セルに複数ある行は全部)、
 * + `extraIds`(表から読めない id の補い。§1.7 の表は 5〜6 本ずつ束ねて書いてあり、先頭以外は `.name` の略記で
 * `obs.` を持たないため、30 列は仕様データ `../schemas/obs-registry.extra-ids.json` が持つ ― 既定値はそれを読む。
 * 呼ぶ側が渡せば(注入口)そちらを使う)。
 */
export function loadObsRegistry(mdPath: string, extraIds: Iterable<string> = defaultObsRegistryExtraIds()): Set<string> {
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
  for (const id of extraIds) ids.add(id);
  return ids;
}

export type HypothesisCheckName = "schema" | "H-1" | "H-2" | "H-3" | "H-4" | "H-5" | "H-6" | "H-7" | "H-8" | "H-9" | "H-10" | "H-11";

export interface CheckResult {
  check: HypothesisCheckName;
  ok: boolean;
  messages: string[];
  /**
   * **回していない**(材料が渡されていないので判定できない)。`ok` は true だが**緑ではない** ―
   * 読む側(道具・人)に「見ていない」と見せるための印(H-9 は packet が無ければ照合できない)。
   * **無い検査を「通った」と読ませない**ためにこの欄を足した(束 V-a。2026-09-30)。
   */
  skipped?: boolean;
  /** 落とさないが採る側(⑤)に見せること(例: 数え直せない集計行を根拠にしている。司令塔の決定 2026-09-30) */
  notes?: string[];
}

/**
 * 検査 1 件を**人が読む行**にする(呼ぶ側が状態の語を自分で組まない)。
 *
 * **`skipped` を「ok」と書かない。**この行はレーンの記録(`02-check.txt`)に残って人が読むので、
 * 「packet と照合して通った」と「照合していない」が同じ語に見えると、**無い検査を通ったと読む** ―
 * この束(V-a)が閉じようとしている穴そのものである(独立監査の指摘。2026-09-30)。
 * `notes`(落とさないが採る側に見せること)も**落とさない** ― 黙ると「数え直せない行を根拠にした」が消える。
 */
export function checkResultLines(result: CheckResult): string[] {
  const state = result.skipped === true ? "skip" : result.ok ? "ok" : "NG";
  const lines = [`${result.check} ${state} ${result.messages.join(" / ")}`.trimEnd()];
  for (const note of result.notes ?? []) lines.push(`  (報告) ${note}`);
  return lines;
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

// ---- 版と kind(0.4 の分岐に使う。0.1〜0.3 の行の判定は変えない) ----

/** 0.4 以上の行か(版の分岐は「0.4 から」だけ。版の一覧に無い版は false) */
function isV04OrLater(line: unknown): boolean {
  const version = asString(get(line, ["schemaVersion"]));
  return version !== undefined && isKnownHypothesisSchemaVersion(version) && version >= "0.4";
}

/** 0.4 の行の kind(無ければ hypothesis ― 司令塔の判断 2026-09-30) */
function kindOf(line: unknown): string {
  return asString(get(line, ["kind"])) ?? "hypothesis";
}

/** 事実の行か(factOrHypothesis: fact または kind: finding) */
function isFactLine(line: unknown): boolean {
  return asString(get(line, ["factOrHypothesis"])) === "fact" || kindOf(line) === "finding";
}

/** 予測が要らない kind(発見・行動候補・答えられない・追加の観測に「動く数」を書かせない) */
const KINDS_WITHOUT_PREDICTION = new Set(["finding", "action_candidate", "unanswerable", "needed_observation"]);

/** 事実の文に混ぜない読みの語 */
const READING_WORDS = ["という読み", "可能性", "のでは", "と思われ", "かもしれ"] as const;

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

/**
 * 0.4 の分岐: `packet.` で始まる obsId は登録簿でなく **packetRef.path の文法**で見る(司令塔の判断 2026-09-30、STEP R2 §3)。
 * obsId = `packet.` + path であること・path が文法に合うこと。**path が packet に実在するかは見ない**(H-9 = 自動化レーン)。
 * 0.3 以前の行では `packet.` の obsId も今までどおり登録簿で落ちる(判定を変えない)。
 *
 * **歩く先は 3 か所**(2026-09-30 に R4 で見つけた抜けを閉じた): `observations[]`・`observations[].derived` の分子分母・
 * `counterEvidence.items[].observations[]`。collectObsIdsForH2 が集める場所と同じにしないと、**反証や分数の中の `packet.` の id が
 * 登録簿の側へ落ちて、正しい席の行が落ちる**(封筒では反証の観測は packetRef を持たず `path` を持つので、そこを見る)。
 */
function packetObsIdProblems(line: unknown): { messages: string[]; packetIds: Set<string> } {
  const messages: string[] = [];
  const packetIds = new Set<string>();
  const visit = (obs: unknown, label: string, path: unknown): void => {
    const obsId = get(obs, ["obsId"]);
    if (!isPacketObsId(obsId)) return;
    packetIds.add(String(obsId));
    const problems = packetRefPathProblems(path);
    for (const problem of problems) messages.push(`${label}: ${problem}`);
    if (problems.length === 0 && obsId !== `${PACKET_OBS_ID_PREFIX}${String(path)}`) {
      messages.push(`${label}: obsId「${String(obsId)}」が packet. + path「${String(path)}」と違う`);
    }
  };
  asArray(get(line, ["observations"])).forEach((obs, index) => {
    visit(obs, `observations[${index}]`, get(obs, ["packetRef", "path"]));
    const derived = get(obs, ["derived"]);
    if (!isRecord(derived)) return;
    // 分数の分子・分母は封筒では path を持たない(obsId だけ)。文法は obsId の後ろで見る
    for (const side of ["numerator", "denominator"]) {
      const sideObs = get(derived, [side]);
      const sideId = get(sideObs, ["obsId"]);
      if (!isPacketObsId(sideId)) continue;
      visit(sideObs, `observations[${index}].derived.${side}`, String(sideId).slice(PACKET_OBS_ID_PREFIX.length));
    }
  });
  asArray(get(line, ["counterEvidence", "items"])).forEach((item, i) => {
    asArray(get(item, ["observations"])).forEach((obs, j) => {
      // 封筒の反証の観測は packetRef を持たず path を持つ(seatOutput.completeSeatOutput)
      visit(obs, `counterEvidence.items[${i}].observations[${j}]`, get(obs, ["path"]));
    });
  });
  return { messages, packetIds };
}

function checkH2(line: unknown, registry: Set<string>): CheckResult {
  const ids = [...new Set(collectObsIdsForH2(line))];
  if (!isV04OrLater(line)) {
    const unknownIds = ids.filter((id) => !registry.has(id));
    return { check: "H-2", ok: unknownIds.length === 0, messages: unknownIds.length === 0 ? [] : [`登録簿に無い obsId: ${unknownIds.join(", ")}`] };
  }
  const packet = packetObsIdProblems(line);
  const messages = [...packet.messages];
  // packet. の id は**歩いた 3 か所(observations・その derived の分子分母・counterEvidence の観測)で文法を見たもの**だけ。
  // そこに無い packet. の id(どこからも裏づかない字)は登録簿の側へ回して落とす。
  const unknownIds = ids.filter((id) => (isPacketObsId(id) ? !packet.packetIds.has(id) : !registry.has(id)));
  if (unknownIds.length > 0) messages.push(`登録簿に無い obsId(packet. は observations・derived・counterEvidence の場所で裏づく): ${unknownIds.join(", ")}`);
  return { check: "H-2", ok: messages.length === 0, messages };
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
    // 0.4 の分岐: 発見・行動候補・答えられない・追加の観測には予測が要らない(STEP R2 §3)。在れば今までどおり見る
    if (isV04OrLater(line) && KINDS_WITHOUT_PREDICTION.has(kindOf(line))) return { check: "H-4", ok: true, messages: [] };
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

function checkH5(line: unknown, bannedWords: readonly string[]): CheckResult {
  const messages: string[] = [];
  const statement = asString(get(line, ["statement"])) ?? "";
  const texts: Array<{ source: string; text: string }> = [{ source: "statement", text: statement }];
  asArray(get(line, ["counterEvidence", "items"])).forEach((item, index) => {
    const text = asString(get(item, ["text"]));
    if (text !== undefined) texts.push({ source: `counterEvidence.items[${index}].text`, text });
  });
  for (const { source, text } of texts) {
    for (const word of bannedWords) {
      if (text.includes(word)) messages.push(`${source}: 禁止語「${word}」を含む`);
    }
  }
  if (isV04OrLater(line) && isFactLine(line)) {
    // 0.4 の分岐: 事実の行(factOrHypothesis: fact / kind: finding)は読みの形を要らない代わりに、読みの語を混ぜたら落ちる(STEP R2 §3)
    for (const word of READING_WORDS) {
      if (statement.includes(word)) messages.push(`事実の行(fact / finding)の statement に読みの語「${word}」を含む`);
    }
  } else if (!(statement.includes("という読みです") || statement.includes("可能性があります"))) {
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

// ---- H-9: packetRef の実在と値の一致(自動化レーンの検証器。束 V-a) ----
//
// 【何を見るか】席が「packet にこの数が在る」と言った場所を**こちらが packet を開いて確かめる。**
//   (a) path が引き当てられる、(b) `observations[].value` が packet の値と同じ、
//   (c) 集計の行を根拠にしたなら**その行を数え直す**(束 D の数え直しを 1 行に絞って呼ぶ)。
// 【文法は見ない】path の文法は `lib/packetRef.ts`(実験席の module)が 1 か所で持ち、**H-2 が見る。**
//   ここは**実在と値**だけ ― 同じ規則を 2 か所に置かない(司令塔の条件 2026-09-30)。
// 【観測は 1 つの数】集計の行を指す path は `.numerator` / `.denominator` / `.value` まで書く
//   (司令塔の決定 2026-09-30)。**引き当ての規則は `resolvePacketPath` の側**に書いてある。
// 【packet が渡されなければ回さない】`skipped` の印を付けて返す ― **緑にはしない。**

/** packetRef を持つ観測を全部集める(本体の観測と、反証の項目の観測) */
function packetRefObservations(line: unknown): Array<{ at: string; path: string; value: unknown }> {
  const out: Array<{ at: string; path: string; value: unknown }> = [];
  const collect = (list: unknown, at: string): void => {
    asArray(list).forEach((obs, index) => {
      const path = asString(get(obs, ["packetRef", "path"]));
      if (path === undefined) return;
      out.push({ at: `${at}[${index}]`, path, value: get(obs, ["value"]) });
    });
  };
  collect(get(line, ["observations"]), "observations");
  asArray(get(line, ["counterEvidence", "items"])).forEach((item, index) => {
    collect(get(item, ["observations"]), `counterEvidence.items[${index}].observations`);
  });
  return out;
}

function checkH9(line: unknown, packet: unknown): CheckResult {
  const observations = packetRefObservations(line);
  if (packet === undefined || packet === null) {
    return {
      check: "H-9",
      ok: true,
      skipped: true,
      messages: [`未照合: packet が渡されていないので packetRef を照合していない(参照 ${observations.length} 件)`],
    };
  }
  const messages: string[] = [];
  const notes: string[] = [];
  for (const observation of observations) {
    const resolved = resolvePacketPath(packet, observation.path);
    if (!resolved.ok) {
      messages.push(`${observation.at}: ${resolved.reason}`);
      continue;
    }
    if (canonicalJson(observation.value) !== canonicalJson(resolved.value)) {
      messages.push(`${observation.at}: value が packet と違う(行 ${JSON.stringify(observation.value)} / packet ${JSON.stringify(resolved.value)})`);
    }
    // 集計の行を根拠にしたなら、その行を数え直す(母集団のとおりに数えた数か)
    const aggregateId = aggregateIdOf(observation.path);
    if (aggregateId !== undefined) {
      const recount = recountRowProblems(packet as { facts?: unknown; aggregates?: unknown }, aggregateId);
      for (const problem of recount.problems) messages.push(`${observation.at}: ${problem}`);
      for (const note of recount.notes) notes.push(`${observation.at}: ${note}`);
    }
  }
  const result: CheckResult = { check: "H-9", ok: messages.length === 0, messages };
  if (notes.length > 0) result.notes = notes;
  return result;
}

/** `aggregates.<id>.numerator` → `<id>`(集計の行を指していなければ undefined) */
function aggregateIdOf(path: string): string | undefined {
  if (!path.startsWith("aggregates.")) return undefined;
  const parts = path.slice("aggregates.".length).split(".");
  const last = parts[parts.length - 1];
  if (last === undefined || !(AGGREGATE_PARTS as readonly string[]).includes(last)) return undefined;
  const id = parts.slice(0, -1).join(".");
  return id === "" ? undefined : id;
}

// ---- H-10: 形・戦法の名前が、その顧客の局で認識された名前か(束 V-b) ----
//
// 【何を見るか】席が文に書いた名前を、**packet の認識(`facts.recognition`)と突き合わせる。**
//   名前の表 = `definitions[].name` / `nameKana` / `id`(**文字として**探す)。
//   通す条件 = その名前を持つ定義の `name` が、**この顧客の局の `rows[].names` に在る**こと。
// 【決めないこと】「どの定義か」は決めない ― 実測(2026-09-30)で**同名の定義が 6 件**あり、
//   名前から定義は 1 対 1 でない。だから「名前が顧客の局の認識に在るか」だけを見る。
// 【各位置で最長一致】実測で**他の名前の中に丸ごと入る名前が 49 組**(中飛車 ⊂ ゴキゲン中飛車)。
//   素朴な部分一致は同じ文字列を 2 つの名前として数えるので、各位置で最長の語を採る。
// 【通っても顧客に出せる名前ではない】`reviewStatus` は**定義の側**にあり、**顧客に出す段が見る**
//   (実物は 114 件すべて `draft`)。H-10 は「使った名前が顧客の局の認識に在るか」だけの検査である。
//   司令塔の指示(2026-09-30・伝聞)。
// 【捕まえられない穴(埋めずに書き残す。司令塔了承)】
//   - 名前の表に**無い**名前(席が作った名前・表に無い戦法名)は文字として一致しないので落ちない。
//   - かな の短い語(`ひらめ` など)は**ふつうの日本語の中に偶然出る**ことがある(偽の当たり)。
//     だから苦情には**当たった語と欄**を書き、人が見て分かる形にする。
// 【見る欄は表で決める】下の 2 つの表(散文 / 機械の欄)で schema の文字列の欄を**全部**分類する。
//   schema に欄が増えたら試験が赤くなる ― **黙って見ない欄が増える道を消すため。**

/** H-10 が名前を探す欄(散文。人が読む文) */
export const H10_PROSE_FIELDS = [
  "statement",
  "counterEvidence.items[].text",
  "actionCandidate.text",
  "neededObservation.what",
  "neededObservation.whyNotInPacket",
  "neededObservation.howToMeasure",
] as const;

/**
 * H-10 が名前を探さない欄(機械の欄・内部の欄)。**理由つきで分類する。**
 * - `internal.reasoning`: 内部の自由分析。**顧客の文へ流れる道が構造で消えている**(規則 8 の (3))。
 *   ここを見ると、顧客に届かない文で門が止まる。
 * - `internal.namesOutsideVocabulary[]`: 席の自己申告。**申告を証拠にしない**(申告があっても通さない・
 *   無くても落とさない)。見ると申告そのものを苦情にしてしまう。
 * - 残りは id・path・単位・日付・入力のファイル名など、**人が読む文でない**欄。
 */
export const H10_NON_PROSE_FIELDS = [
  "hypothesisId",
  "subject.customer",
  "subject.groups[]",
  "origin.itemId",
  "requestRef.questionId",
  "observations[].obsId",
  "observations[].path",
  "observations[].value",
  "observations[].unit",
  "observations[].derived.numerator.obsId",
  "observations[].derived.denominator.obsId",
  "observations[].packetRef.path",
  "observations[].packetRef.provenanceId",
  "counterEvidence.items[].observations[].obsId",
  "counterEvidence.items[].observations[].path",
  "counterEvidence.items[].observations[].value",
  "counterEvidence.items[].observations[].unit",
  "counterEvidence.provenance.inputs[]",
  "prediction.writtenAt",
  "prediction.window",
  "prediction.metric",
  "prediction.alsoRequires[].metric",
  "actionCandidate.derivedFrom[]",
  "internal.reasoning",
  "internal.namesOutsideVocabulary[]",
  "knowledge.origin.kifu",
  "knowledge.origin.lane",
  "provenance.inputs[]",
  "provenance.excludedInputs[]",
] as const;

/** 欄の道(`counterEvidence.items[].text` の形)をたどって、そこに在る文字列を全部集める */
export function stringsAtField(line: unknown, field: string): Array<{ at: string; text: string }> {
  let current: Array<{ at: string; value: unknown }> = [{ at: "", value: line }];
  for (const step of field.split(".")) {
    const isList = step.endsWith("[]");
    const key = isList ? step.slice(0, -2) : step;
    const next: Array<{ at: string; value: unknown }> = [];
    for (const node of current) {
      const value = get(node.value, [key]);
      const at = node.at === "" ? key : `${node.at}.${key}`;
      if (!isList) {
        if (value !== undefined) next.push({ at, value });
        continue;
      }
      asArray(value).forEach((item, index) => next.push({ at: `${at}[${index}]`, value: item }));
    }
    current = next;
  }
  const out: Array<{ at: string; text: string }> = [];
  for (const node of current) {
    if (typeof node.value === "string") out.push({ at: node.at, text: node.value });
  }
  return out;
}

/** 名前の表(語 → その語を持つ定義の `name` の集合)。packet の認識の定義から作る */
export function recognitionNameCorpus(packet: unknown): Map<string, Set<string>> {
  const corpus = new Map<string, Set<string>>();
  for (const definition of asArray(get(packet, ["facts", "recognition", "definitions"]))) {
    const name = asString(get(definition, ["name"]));
    if (name === undefined) continue;
    for (const key of ["name", "nameKana", "id"] as const) {
      const word = asString(get(definition, [key]));
      if (word === undefined || word === "") continue;
      const names = corpus.get(word) ?? new Set<string>();
      names.add(name);
      corpus.set(word, names);
    }
  }
  return corpus;
}

/** この顧客の局で認識された名前(`facts.recognition.rows[].names` の合併) */
export function recognizedNames(packet: unknown): Set<string> {
  const names = new Set<string>();
  for (const row of asArray(get(packet, ["facts", "recognition", "rows"]))) {
    for (const name of asArray(get(row, ["names"]))) {
      const value = asString(name);
      if (value !== undefined) names.add(value);
    }
  }
  return names;
}

/** 文の中の名前を**各位置で最長一致**で拾う(同じ文字列を 2 つの名前として数えない) */
export function namesInText(text: string, corpus: Map<string, Set<string>>): Array<{ at: number; word: string }> {
  const out: Array<{ at: number; word: string }> = [];
  let index = 0;
  while (index < text.length) {
    let longest: string | undefined;
    for (const word of corpus.keys()) {
      if (!text.startsWith(word, index)) continue;
      if (longest === undefined || word.length > longest.length) longest = word;
    }
    if (longest === undefined) {
      index += 1;
      continue;
    }
    out.push({ at: index, word: longest });
    index += longest.length;
  }
  return out;
}

function checkH10(line: unknown, packet: unknown): CheckResult {
  if (packet === undefined || packet === null) {
    return {
      check: "H-10",
      ok: true,
      skipped: true,
      messages: ["未照合: packet が渡されていないので名前を照合していない"],
    };
  }
  const corpus = recognitionNameCorpus(packet);
  const recognized = recognizedNames(packet);
  const messages: string[] = [];
  if (corpus.size === 0) {
    return { check: "H-10", ok: true, skipped: true, messages: ["未照合: packet に認識の定義が無いので名前を照合していない"] };
  }
  for (const field of H10_PROSE_FIELDS) {
    for (const node of stringsAtField(line, field)) {
      for (const hit of namesInText(node.text, corpus)) {
        const names = [...(corpus.get(hit.word) ?? new Set<string>())];
        if (names.some((name) => recognized.has(name))) continue;
        messages.push(
          `${node.at}: 名前「${hit.word}」(${hit.at} 文字目)はこの顧客の局で認識されていない` +
            `(認識された名前 ${recognized.size} 件のどれにも当たらない)`,
        );
      }
    }
  }
  return { check: "H-10", ok: messages.length === 0, messages };
}

// ---- H-11(接続設計案 ③(e)): 名前を顧客に出せる段か ― **落とさない。印だけ** ----
//
// 【何のために在るか(顧客の PDF にどう出るか)】この検査は**顧客に見える文字を決めない。**
//   渡すのは「この名前を顧客に出すなら『〜のような形』か群の呼び名に落とす」という**印**だけで、
//   落とす判定は作らない(正本の「判定は作らない。印だけ」)。
//   実物は定義 114 件すべて `draft` なので、**名前に触れれば必ず印が付く**(それが今の正しい状態)。
// 【正本の読み替え】接続設計案は `facts.recognition.rows[].reviewStatus` と書くが、
//   **`rows[]` に `reviewStatus` は無く `definitions[]` に在る**(実測。司令塔の指示で読み替え。2026-09-30)。
// 【H-10 と混ぜない】H-10 は落とす検査(その顧客の局で認識された名前か)、こちらは落とさない印。
//   1 か所にまとめると「印が付いたから落ちた」と読める。名前を探す道具だけ共有する。
// 【群の呼び名には印を付けない】群は `signatureClass` の機械の呼び名(材料では「多数の核」「それ以外」
//   「署名なし」)で `reviewStatus` を持たず、**「〜のような形」に落とす先がそもそも群の呼び名**である。
//   名前の表に無いので、この検査の対象にもならない(計画 §3.2。司令塔へ 1 行で伝えた)。

/** 顧客に出せる段(`draft` は含めない。`expired` は期限切れなので含めない ― `data/` の規則) */
export const APPROVED_REVIEW_STATUSES = ["human_reviewed", "expert_verified"] as const;

/**
 * 承認済みの定義を持つ語(名前・かな・id)。**1 つでも承認済みなら承認済みに数える** ―
 * 同じ語に複数の定義が付く(実物で同名の定義 6 組)ので、H-10 の「どれかが在れば」と同じ緩い側に合わせる。
 */
export function approvedRecognitionWords(packet: unknown): Set<string> {
  const approved = new Set<string>();
  for (const definition of asArray(get(packet, ["facts", "recognition", "definitions"]))) {
    const status = asString(get(definition, ["reviewStatus"]));
    if (status === undefined || !(APPROVED_REVIEW_STATUSES as readonly string[]).includes(status)) continue;
    for (const key of ["name", "nameKana", "id"] as const) {
      const word = asString(get(definition, [key]));
      if (word !== undefined && word !== "") approved.add(word);
    }
  }
  return approved;
}

function checkH11(line: unknown, packet: unknown): CheckResult {
  if (packet === undefined || packet === null) {
    return { check: "H-11", ok: true, skipped: true, messages: ["未照合: packet が渡されていないので名前の段を見ていない"] };
  }
  const corpus = recognitionNameCorpus(packet);
  if (corpus.size === 0) {
    return { check: "H-11", ok: true, skipped: true, messages: ["未照合: packet に認識の定義が無いので名前の段を見ていない"] };
  }
  const approved = approvedRecognitionWords(packet);
  const notes: string[] = [];
  for (const field of H10_PROSE_FIELDS) {
    for (const node of stringsAtField(line, field)) {
      for (const hit of namesInText(node.text, corpus)) {
        if (approved.has(hit.word)) continue;
        notes.push(
          `${node.at}: 名前「${hit.word}」に承認済みの定義が無い` +
            `(顧客に出すなら「〜のような形」か群の呼び名に落とす)`,
        );
      }
    }
  }
  // **落とさない**(ok は常に true)。印だけを返す
  const result: CheckResult = { check: "H-11", ok: true, messages: [] };
  if (notes.length > 0) result.notes = notes;
  return result;
}

/**
 * スキーマ照合 + H-1〜H-11 を全部回して全部返す(最初で止めない)。スキーマが落ちても H は回す。
 *
 * `opts.bannedWords` は H-5 の一覧の差し替え口(試験用)。渡されなければ
 * `data/governance/banned_words.json` の `words` を読む(STEP H5-SYNC → Audit Core T-3)。
 */
export function validateHypothesisLine(
  line: unknown,
  opts: { today: string; registry: Set<string>; schema?: JsonSchema; bannedWords?: readonly string[]; packet?: unknown },
): CheckResult[] {
  const resolved = resolveSchema(line, opts.schema);
  const schemaErrors = "error" in resolved ? [resolved.error] : validate(line, resolved.schema);
  return [
    { check: "schema", ok: schemaErrors.length === 0, messages: schemaErrors },
    checkH1(line),
    checkH2(line, opts.registry),
    checkH3(line),
    checkH4(line, opts.today),
    checkH5(line, opts.bannedWords ?? defaultBannedWords()),
    checkH6(line),
    checkH7(line),
    checkH8(line),
    checkH9(line, opts.packet),
    checkH10(line, opts.packet),
    checkH11(line, opts.packet),
  ];
}
