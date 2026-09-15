// STEP D6(docs/STEP_D6_PLAN_2026-09-16.md)。D4 の Gate の行(契約 diagnosis-gate v0.1)を、事実だけの文に組む純粋関数。
//
// 【このファイルがやること】
// - 入力の確かめ(計画 5.1): 形・版・人の記号・パス・verdict と items・件数・gateValues・項目の再計算(D4 の実装の式 ― 13.2 の決定 2)・
//   test.set と provisional・tally.games と inputs の本数・定義の sha と readableText・採った行どうしの局の数と conditionsInRun
// - 同じ条件式の行から採る行を決める(計画 2.3。set の段が大きい行、同じ段なら後ろの行。pairNotApplied は比べない)
// - 文を組む(計画 3.。差し込み口ごとに固定の欄 ― 3.0)と、出力の確かめ(計画 5.2。固定文の照合・禁止語・文の終わり・数)
// - 契約 diagnosis-report v0.1 の行と Markdown(audience dev / person ― 計画 2.1・6.)
//
// 【このファイルが絶対にやらないこと】
// - Gate を判定し直すこと(再計算は照合だけで、結果を変えない)。名前・性格・因果・練習の語を足すこと。LLM・エンジン。ファイルの読み書き
// - 読む行の型を D4 の lib から import すること(型はここに持つ ― 計画 13.1。定数 GATE_VALUES・GATE_TEXT と G-3 の inverseRatioOf だけは D4 の lib/gate.ts から import する ― 13.4)

import { createHash } from "node:crypto";
import {
  ALLOWED_LITERAL_DIGITS,
  ENDINGS,
  FIXED_TEMPLATES,
  FORBIDDEN_WORDS,
  ITEM_DESCRIPTIONS,
  NUMBER_CHECKED_TEMPLATES,
  rateText,
  signedCpText,
  SLOT_DERIVED_BY,
  SLOT_FIELDS,
  STANDING_BOUNDS_APPROVED_ON,
  TEMPLATES,
  TERMS,
  TERMS_PREFIX,
  TERMS_SEPARATOR,
  type SentenceKind,
  type SlotName,
  type TemplateKey,
} from "./reportTemplates.js";
import { GATE_TEXT, GATE_VALUES, inverseRatioOf, type GateValues } from "./gate.js";
import { DIAGNOSIS_REPORT_SCHEMA_VERSION } from "./schemaVersions.js";
import type { StandingBounds } from "./standing.js";

export const DIAGNOSIS_REPORT_CONTRACT = "diagnosis-report" as const;
export { DIAGNOSIS_REPORT_SCHEMA_VERSION };

/** 読める diagnosis-gate の版 */
export const KNOWN_GATE_SCHEMA_VERSIONS: readonly string[] = ["0.1"];
/** 受け付ける試す側の集合(計画 5.1・13.2 の決定 3) */
export const KNOWN_TEST_SETS: readonly string[] = ["sente6", "sente6+gote4"];
const GATE_CONTRACT = "diagnosis-gate";
const PERSON_LABEL = /^p[0-9]+$/;
const SHA256 = /^[0-9a-f]{64}$/;
const PROVISIONAL = "(仮)";
const GATE_ITEM_IDS = ["G-1", "G-2", "G-3", "G-4"] as const;

// ---- 読む行の型(計画 13.1。D4 の実装の欄の名前)----

export type GateItemId = (typeof GATE_ITEM_IDS)[number];
export type GateItemResult = "met" | "notMet" | "notEvaluable";
export interface GateRateCountIn {
  collapsed: number;
  denominator: number;
}
export interface GateCollapseTallyIn {
  pairs: number;
  collapsed: number;
  denominator: number;
  excluded: Record<string, number>;
  transitions: Record<string, number>;
  byBefore: { ahead: GateRateCountIn; level: GateRateCountIn };
  gamesWithDenominator: number;
  within5: { dropped: number; denominator: number };
}
export type GatePvSideIn = { state: "applicable"; n: number; actualTrue: number; pvTrue: number } | { state: "notApplicable"; reasons: unknown[] };
export interface GateTallyIn {
  games: number;
  truePairs: GateCollapseTallyIn;
  falsePairs: GateCollapseTallyIn;
  pvSide: GatePvSideIn;
}
export interface GateItemIn {
  item: GateItemId;
  values: Record<string, number>;
  threshold: Record<string, number>;
  result: GateItemResult;
  reasons: string[];
}
export interface GateInputFileIn {
  path: string;
  sha256: string;
}
export type GateJudgedIn = { items: GateItemIn[]; verdict: "meets" | "insufficient"; text: string } | { notJudged: "draft" };
interface GateLineCommon {
  contract: typeof GATE_CONTRACT;
  schemaVersion: string;
  person: string;
  testPerson: string;
  condition: { id: string; label: string; status: "draft" | "approved"; definitionSha256: string };
  gateValues: Record<string, number>;
  conditionsInRun: number;
}
export type GateLineJudgedIn = GateLineCommon & {
  material: { inputs: GateInputFileIn[]; tally: GateTallyIn };
  test: { set: string; provisional: boolean; inputs: GateInputFileIn[]; tally: GateTallyIn };
  gate: GateJudgedIn;
};
export type GateLinePairNotAppliedIn = GateLineCommon & {
  material: { inputs: GateInputFileIn[] };
  test: { set: string; provisional: boolean; inputs: GateInputFileIn[] };
  gate: { notJudged: "pairNotApplied" };
};
export type GateLineIn = GateLineJudgedIn | GateLinePairNotAppliedIn;
export interface NumberedGateLine {
  line: number;
  value: GateLineIn;
}

/** 条件式の定義から D6 が読むもの(`loadCondition` の結果から作る) */
export interface ReportDefinition {
  id: string;
  label: string;
  status: "draft" | "approved";
  readableText?: string;
  definitionSha256: string;
}

export class ReportInputError extends Error {
  constructor(readonly problems: readonly string[]) {
    super(`Gate の行を文にできない(入力): ${problems.join(" / ")}`);
    this.name = "ReportInputError";
  }
}

export class ReportOutputError extends Error {
  constructor(readonly problems: readonly string[]) {
    super(`組んだ文が契約に合わない(出力): ${problems.join(" / ")}`);
    this.name = "ReportOutputError";
  }
}

const isPairNotApplied = (line: GateLineIn): line is GateLinePairNotAppliedIn => "notJudged" in line.gate && line.gate.notJudged === "pairNotApplied";

// ---- 入力の形と確かめ(計画 5.1)----

type Obj = Record<string, unknown>;
const isObj = (value: unknown): value is Obj => typeof value === "object" && value !== null && !Array.isArray(value);
const isCount = (value: unknown): value is number => typeof value === "number" && Number.isInteger(value) && value >= 0;

function rateCountProblems(value: unknown, where: string): string[] {
  if (!isObj(value) || !isCount(value.collapsed) || !isCount(value.denominator)) return [`${where} が件数の組でない`];
  return value.collapsed > value.denominator ? [`${where}.collapsed が denominator より大きい`] : [];
}

function collapseTallyProblems(value: unknown, where: string): string[] {
  if (!isObj(value)) return [`${where} が無い`];
  const problems: string[] = [];
  for (const key of ["pairs", "collapsed", "denominator", "gamesWithDenominator"]) if (!isCount(value[key])) problems.push(`${where}.${key} が 0 以上の整数でない`);
  if (problems.length === 0) {
    if ((value.collapsed as number) > (value.denominator as number)) problems.push(`${where}.collapsed が denominator より大きい`);
    if ((value.denominator as number) > (value.pairs as number)) problems.push(`${where}.denominator が pairs より大きい`);
  }
  for (const key of ["excluded", "transitions"]) {
    const table = value[key];
    if (!isObj(table) || !Object.values(table).every(isCount)) problems.push(`${where}.${key} が件数の表でない`);
  }
  const byBefore = value.byBefore;
  if (!isObj(byBefore)) problems.push(`${where}.byBefore が無い`);
  else problems.push(...rateCountProblems(byBefore.ahead, `${where}.byBefore.ahead`), ...rateCountProblems(byBefore.level, `${where}.byBefore.level`));
  const within5 = value.within5;
  if (!isObj(within5) || !isCount(within5.dropped) || !isCount(within5.denominator)) problems.push(`${where}.within5 が件数の組でない`);
  return problems;
}

function tallyProblems(value: unknown, where: string): string[] {
  if (!isObj(value)) return [`${where} が無い`];
  const problems: string[] = [];
  if (!isCount(value.games)) problems.push(`${where}.games が 0 以上の整数でない`);
  problems.push(...collapseTallyProblems(value.truePairs, `${where}.truePairs`), ...collapseTallyProblems(value.falsePairs, `${where}.falsePairs`));
  const pv = value.pvSide;
  if (!isObj(pv)) problems.push(`${where}.pvSide が無い`);
  else if (pv.state === "applicable") {
    if (!isCount(pv.n) || !isCount(pv.actualTrue) || !isCount(pv.pvTrue)) problems.push(`${where}.pvSide の n・actualTrue・pvTrue が 0 以上の整数でない`);
    else if (pv.actualTrue > pv.n || pv.pvTrue > pv.n) problems.push(`${where}.pvSide の actualTrue か pvTrue が n より大きい`);
  } else if (pv.state !== "notApplicable" || !Array.isArray(pv.reasons)) problems.push(`${where}.pvSide の形が違う`);
  return problems;
}

function inputsProblems(value: unknown, where: string): string[] {
  if (!Array.isArray(value)) return [`${where} が配列でない`];
  const problems: string[] = [];
  value.forEach((entry, index) => {
    if (!isObj(entry) || typeof entry.path !== "string" || typeof entry.sha256 !== "string" || !SHA256.test(entry.sha256)) problems.push(`${where}[${index}] が { path, sha256 } でない`);
    else if (entry.path.startsWith("/") || /^\.\.(\/|\\|$)/.test(entry.path)) problems.push(`${where}[${index}].path が絶対パスか根の外(リポジトリ相対でない ― R-10・D4 の R-1)`);
  });
  return problems;
}

/** 項目の結果を tally と gateValues から整数で計算し直す(計画 5.1。D4 の実装の式 ― 13.2 の決定 2) */
export function recomputeItemResults(material: GateTallyIn, test: GateTallyIn, values: GateValues): Record<GateItemId, GateItemResult> {
  const t = material.truePairs;
  const f = material.falsePairs;
  const g1: GateItemResult = t.denominator >= values.minTruePairs && t.gamesWithDenominator >= values.minGames ? "met" : "notMet";

  let g2: GateItemResult;
  if (t.denominator === 0 || f.denominator === 0) g2 = "notEvaluable";
  else {
    const ratio = f.collapsed === 0 ? t.collapsed >= 1 : t.collapsed * f.denominator >= values.minRateRatio * f.collapsed * t.denominator;
    const diff = 100 * (t.collapsed * f.denominator - f.collapsed * t.denominator) >= values.minRateDiffPoints * t.denominator * f.denominator;
    g2 = ratio && diff ? "met" : "notMet";
  }

  const pv = material.pvSide;
  // D4 の実装(1fc4f67)と同じ整数の式 pvTrue·(1/ratio) ≤ actualTrue(計画 13.4)
  const g3: GateItemResult = pv.state === "notApplicable" || pv.n === 0 ? "notEvaluable" : pv.pvTrue * inverseRatioOf(values.maxPvToActualRatio) <= pv.actualTrue ? "met" : "notMet";

  const tt = test.truePairs;
  const tf = test.falsePairs;
  let g4: GateItemResult;
  if (tt.denominator === 0 || tf.denominator === 0 || t.denominator === 0 || f.denominator === 0) g4 = "notEvaluable";
  else {
    const testCross = crossOf(tt, tf);
    const materialCross = crossOf(t, f);
    g4 = tt.denominator >= values.minTestTruePairs && testCross !== 0 && materialCross !== 0 && Math.sign(testCross) === Math.sign(materialCross) ? "met" : "notMet";
  }
  return { "G-1": g1, "G-2": g2, "G-3": g3, "G-4": g4 };
}

/** `tc·fn − fc·tn`(率の差と同じ符号の整数) */
const crossOf = (truePairs: GateRateCountIn, falsePairs: GateRateCountIn): number => truePairs.collapsed * falsePairs.denominator - falsePairs.collapsed * truePairs.denominator;

function gateValuesProblems(value: unknown, where: string): string[] {
  if (!isObj(value)) return [`${where} が無い`];
  const expectedKeys = Object.keys(GATE_VALUES).sort();
  const keys = Object.keys(value).sort();
  const same = keys.join(",") === expectedKeys.join(",") && expectedKeys.every((key) => value[key] === GATE_VALUES[key as keyof typeof GATE_VALUES]);
  return same ? [] : [`${where} が人間の確定値(GATE_VALUES)と違う`];
}

/** 1 行の形と、その行だけで決まる確かめ。問題があれば null(問題は `problems` に足す) */
function readGateLine(value: unknown, line: number, problems: string[]): GateLineIn | null {
  const at = `行 ${line}`;
  const before = problems.length;
  if (!isObj(value)) {
    problems.push(`${at} がオブジェクトでない`);
    return null;
  }
  if (value.contract !== GATE_CONTRACT) problems.push(`${at}: contract が ${GATE_CONTRACT} でない`);
  if (typeof value.schemaVersion !== "string" || !KNOWN_GATE_SCHEMA_VERSIONS.includes(value.schemaVersion)) problems.push(`${at}: schemaVersion が知っている版でない`);
  for (const key of ["person", "testPerson"]) if (typeof value[key] !== "string" || !PERSON_LABEL.test(value[key] as string)) problems.push(`${at}: ${key} が p と数字の記号でない`);
  const condition = value.condition;
  if (!isObj(condition) || typeof condition.id !== "string" || condition.id === "" || typeof condition.label !== "string" || (condition.status !== "draft" && condition.status !== "approved") || typeof condition.definitionSha256 !== "string" || !SHA256.test(condition.definitionSha256)) {
    problems.push(`${at}: condition の形が違う`);
  }
  problems.push(...gateValuesProblems(value.gateValues, `${at}: gateValues`));
  if (!isCount(value.conditionsInRun)) problems.push(`${at}: conditionsInRun が 0 以上の整数でない`);

  const material = value.material;
  const test = value.test;
  const gate = value.gate;
  if (!isObj(material)) problems.push(`${at}: material が無い`);
  else problems.push(...inputsProblems(material.inputs, `${at}: material.inputs`));
  if (!isObj(test)) problems.push(`${at}: test が無い`);
  else {
    problems.push(...inputsProblems(test.inputs, `${at}: test.inputs`));
    if (typeof test.set !== "string" || !KNOWN_TEST_SETS.includes(test.set)) problems.push(`${at}: test.set が ${KNOWN_TEST_SETS.join("・")} のどれでもない`);
    else if (test.provisional !== !test.set.includes("+gote")) problems.push(`${at}: test.provisional が test.set と食い違う(R-5 (e))`);
  }
  if (!isObj(gate)) {
    problems.push(`${at}: gate が無い`);
    return null;
  }
  if (problems.length > before || !isObj(material) || !isObj(test) || !isObj(condition)) return null;

  const pairNotApplied = gate.notJudged === "pairNotApplied";
  const draft = gate.notJudged === "draft";
  if ("notJudged" in gate && !pairNotApplied && !draft) problems.push(`${at}: gate.notJudged が draft・pairNotApplied でない`);
  if ("notJudged" in gate && "verdict" in gate) problems.push(`${at}: gate に notJudged と verdict が両方ある`);
  if (!("notJudged" in gate) && !("verdict" in gate)) problems.push(`${at}: gate に notJudged も verdict も無い`);

  if (pairNotApplied) {
    if ("tally" in material || "tally" in test) problems.push(`${at}: pairNotApplied の行に tally がある`);
    return problems.length > before ? null : (value as unknown as GateLinePairNotAppliedIn);
  }
  if (!("tally" in material) || !("tally" in test)) problems.push(`${at}: pairNotApplied でない行に tally が無い`);
  problems.push(...tallyProblems(material.tally, `${at}: material.tally`), ...tallyProblems(test.tally, `${at}: test.tally`));
  if (problems.length > before) return null;
  const typedMaterial = material as unknown as GateLineJudgedIn["material"];
  const typedTest = test as unknown as GateLineJudgedIn["test"];
  if (typedMaterial.tally.games !== typedMaterial.inputs.length) problems.push(`${at}: material.tally.games と material.inputs の本数が違う`);
  if (typedTest.tally.games !== typedTest.inputs.length) problems.push(`${at}: test.tally.games と test.inputs の本数が違う`);

  const status = (condition as { status: string }).status;
  if (draft) {
    if (status === "approved") problems.push(`${at}: approved の定義なのに notJudged: draft(R-5 (d))`);
    return problems.length > before ? null : (value as unknown as GateLineJudgedIn);
  }
  if (status === "draft") problems.push(`${at}: draft の定義なのに verdict がある(R-5 (d))`);
  if (gate.verdict !== "meets" && gate.verdict !== "insufficient") problems.push(`${at}: gate.verdict が meets・insufficient でない`);
  const items = gate.items;
  if (!Array.isArray(items) || items.length !== GATE_ITEM_IDS.length || !items.every((item, index) => isObj(item) && item.item === GATE_ITEM_IDS[index] && ["met", "notMet", "notEvaluable"].includes(item.result as string) && Array.isArray(item.reasons))) {
    problems.push(`${at}: gate.items が G-1〜G-4 の 4 項目でない`);
    return null;
  }
  const typedItems = items as GateItemIn[];
  const allMet = typedItems.every((item) => item.result === "met");
  if (gate.verdict === "meets" && !allMet) problems.push(`${at}: verdict が meets なのに met でない項目がある`);
  if (gate.verdict === "insufficient" && allMet) problems.push(`${at}: verdict が insufficient なのに全部の項目が met`);
  const expectedText = gate.verdict === "meets" ? GATE_TEXT.meets : GATE_TEXT.insufficient;
  if (gate.text !== expectedText) problems.push(`${at}: gate.text が verdict の文と違う`);
  if (problems.length > before) return null;
  const recomputed = recomputeItemResults(typedMaterial.tally, typedTest.tally, GATE_VALUES);
  for (const item of typedItems) {
    if (item.result !== recomputed[item.item]) problems.push(`${at}: ${item.item} の結果 ${item.result} が、tally と gateValues から計算し直した ${recomputed[item.item]} と違う(R-5 (c))`);
  }
  return problems.length > before ? null : (value as unknown as GateLineJudgedIn);
}

// ---- 採る行(計画 2.3)----

export interface TakenRow {
  row: NumberedGateLine;
  /** 同じ condition.id のほかの行の数 */
  rowsNotTaken: number;
}

/** 条件 id ごとに採る行を決め、id の昇順に並べる。**行の並びだけでは決めない**(set の段が大きい行、同じ段なら後ろの行) */
export function chooseRows(rows: readonly NumberedGateLine[]): TakenRow[] {
  const byId = new Map<string, NumberedGateLine[]>();
  for (const row of rows) {
    const group = byId.get(row.value.condition.id) ?? [];
    group.push(row);
    byId.set(row.value.condition.id, group);
  }
  const tier = (row: NumberedGateLine): number => (row.value.test.set.includes("+gote") ? 1 : 0);
  return [...byId.keys()]
    .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
    .map((id) => {
      const group = byId.get(id)!;
      const judged = group.filter((row) => !isPairNotApplied(row.value));
      const candidates = judged.length > 0 ? judged : group;
      const taken = candidates.reduce((best, row) => (tier(row) > tier(best) || (tier(row) === tier(best) && row.line > best.line) ? row : best));
      return { row: taken, rowsNotTaken: group.length - 1 };
    });
}

// ---- 文(計画 3.)----

export interface SentenceSource {
  slot: SlotName;
  field: string;
  value: string | number;
  derivedBy?: "pct" | "sign" | "count" | "signedCp";
}

export interface ReportSentence {
  kind: SentenceKind;
  /** 使った文の型(`terms` は N-3 の用語の並び) */
  template: TemplateKey | "terms";
  text: string;
  sources: SentenceSource[];
}

interface Slot {
  text: string;
  source: SentenceSource;
}

function slot(name: SlotName, value: string | number, text?: string): Slot {
  const derivedBy = SLOT_DERIVED_BY[name];
  return { text: text ?? String(value), source: { slot: name, field: SLOT_FIELDS[name], value, ...(derivedBy === undefined ? {} : { derivedBy }) } };
}

/** 差し込み口の値の文字列(出力の確かめで型を作り直すときにも使う) */
export function slotText(source: SentenceSource): string {
  return source.derivedBy === "signedCp" ? signedCpText(source.value as number) : String(source.value);
}

function fillTemplate(key: TemplateKey, textOf: (name: string) => string): string {
  return TEMPLATES[key].text.replace(/\{(\w+)\}/g, (_match, name: string) => textOf(name));
}

function render(key: TemplateKey, slots: readonly Slot[]): ReportSentence {
  const byName = new Map(slots.map((entry) => [entry.source.slot as string, entry]));
  const text = fillTemplate(key, (name) => {
    const entry = byName.get(name);
    if (entry === undefined) throw new Error(`文の型 ${key} の差し込み口 {${name}} の値が無い`);
    return entry.text;
  });
  return { kind: TEMPLATES[key].kind, template: key, text, sources: slots.map((entry) => entry.source) };
}

export type Audience = "dev" | "person";
export type OmittedReason = "insufficient" | "draft" | "pairNotApplied";
/** F-4 を出したか(dev の表 ― 計画 3.2 F-4) */
export type TestDirectionNote = "shown" | "noDifference" | "notComparable" | "notApplicable";

interface ConditionOutcome {
  sentences: ReportSentence[];
  /** person に出すか */
  shownForPerson: boolean;
  omittedForPerson: OmittedReason | null;
  testDirection: TestDirectionNote;
}

/** 真と偽で「直前が優勢の組の割合」の差が 10 ポイント以上(計画 3.2 F-2b。整数の交差乗算。注記の条件で Gate ではない) */
export function beforeDistributionDiffers(truePairs: GateCollapseTallyIn, falsePairs: GateCollapseTallyIn): boolean {
  const tn = truePairs.denominator;
  const fn = falsePairs.denominator;
  if (tn === 0 || fn === 0) return false;
  return 100 * Math.abs(truePairs.byBefore.ahead.denominator * fn - falsePairs.byBefore.ahead.denominator * tn) >= 10 * tn * fn;
}

function headingOf(definition: ReportDefinition): ReportSentence {
  return definition.readableText === undefined
    ? render("headingIdOnly", [slot("id", definition.id)])
    : render("headingWithText", [slot("id", definition.id), slot("readableText", definition.readableText)]);
}

function factSentences(row: GateLineJudgedIn, audience: Audience, verdict: "meets" | "insufficient"): { sentences: ReportSentence[]; testDirection: TestDirectionNote } {
  const tally = row.material.tally;
  const t = tally.truePairs;
  const f = tally.falsePairs;
  const recomputed = recomputeItemResults(tally, row.test.tally, GATE_VALUES);
  const sentences: ReportSentence[] = [
    render("F-1", [slot("tn", t.denominator), slot("tnGames", t.gamesWithDenominator), slot("tc", t.collapsed), slot("tcPct", rateText(t.collapsed, t.denominator))]),
    render("F-2", [slot("fn", f.denominator), slot("fc", f.collapsed), slot("fcPct", rateText(f.collapsed, f.denominator))]),
  ];
  if (beforeDistributionDiffers(t, f)) sentences.push(render("F-2b", []));
  const pv = tally.pvSide;
  sentences.push(recomputed["G-3"] === "notEvaluable" || pv.state === "notApplicable" ? render("F-3-notEvaluable", []) : render("F-3", [slot("p", pv.pvTrue), slot("a", pv.actualTrue), slot("n", pv.n)]));

  const tt = row.test.tally.truePairs;
  const tf = row.test.tally.falsePairs;
  let testDirection: TestDirectionNote;
  if (tt.denominator === 0 || tf.denominator === 0) testDirection = "notComparable";
  else {
    const cross = crossOf(tt, tf);
    if (cross === 0) testDirection = "noDifference";
    else if (audience === "person" && verdict !== "meets") testDirection = "notApplicable";
    else {
      testDirection = "shown";
      sentences.push(render("F-4", [slot("testGames", row.test.inputs.length), slot("testTn", tt.denominator), slot("direction", cross > 0 ? "高い" : "低い")]));
    }
  }
  if (!row.test.set.includes("+gote")) sentences.push(render("F-5", [slot("testGames", row.test.inputs.length)]));
  if (recomputed["G-1"] === "met") sentences.push(render("F-6", [slot("tnGames", t.gamesWithDenominator)]));
  return { sentences, testDirection };
}

function conditionOutcome(row: GateLineIn, definition: ReportDefinition, options: ReportOptions): ConditionOutcome {
  const heading = headingOf(definition);
  if (isPairNotApplied(row)) {
    return { sentences: [heading, render("pairNotApplied", [])], shownForPerson: false, omittedForPerson: "pairNotApplied", testDirection: "notApplicable" };
  }
  const gate = row.gate;
  if ("notJudged" in gate) {
    return { sentences: [heading, render("draft", [])], shownForPerson: false, omittedForPerson: "draft", testDirection: "notApplicable" };
  }
  if (options.audience === "person") {
    if (gate.verdict === "insufficient") {
      return { sentences: [heading, render("insufficient", [])], shownForPerson: options.includeInsufficient === true, omittedForPerson: "insufficient", testDirection: "notApplicable" };
    }
    const facts = factSentences(row, "person", "meets");
    return { sentences: [heading, ...facts.sentences, render("meets", [])], shownForPerson: true, omittedForPerson: null, testDirection: facts.testDirection };
  }
  const facts = factSentences(row, "dev", gate.verdict);
  return {
    sentences: [heading, ...facts.sentences, render(gate.verdict, [])],
    shownForPerson: gate.verdict === "meets" || options.includeInsufficient === true,
    omittedForPerson: gate.verdict === "meets" ? null : "insufficient",
    testDirection: facts.testDirection,
  };
}

function termsSentence(texts: readonly string[]): ReportSentence | null {
  const entries = TERMS.filter(({ term }) => texts.some((text) => text.includes(term))).map(({ text }) => text);
  return entries.length === 0 ? null : { kind: "N-3", template: "terms", text: `${TERMS_PREFIX}${entries.join(TERMS_SEPARATOR)}`, sources: [] };
}

// ---- 出力の確かめ(計画 5.2。実行時にも当てる ― R-6)----

/** 「。」で文に区切る。括弧(「(」「)」)と鉤括弧の中の「。」では区切らない */
export function splitSentences(text: string): string[] {
  const sentences: string[] = [];
  let depth = 0;
  let current = "";
  for (const char of text) {
    current += char;
    if (char === "(" || char === "「") depth += 1;
    else if ((char === ")" || char === "」") && depth > 0) depth -= 1;
    else if (char === "。" && depth === 0) {
      sentences.push(current);
      current = "";
    }
  }
  if (current !== "") sentences.push(current);
  return sentences;
}

/** 禁止語・label の照合の前にそろえる(監査 93 の S-1): NFKC で揃え、空白(全角を含む)とゼロ幅文字を除く */
export function normalizeForMatch(text: string): string {
  return text.normalize("NFKC").replace(/[\s\u200B-\u200D\u2060\uFEFF]/gu, "");
}

/** 出す文に 5.2 の確かめを当て、問題を並べる(空なら通った)。`labels` は入力の condition.label */
export function outputProblems(sentences: readonly ReportSentence[], labels: readonly string[]): string[] {
  const problems: string[] = [];
  const labelWords = [...new Set(labels.flatMap((label) => [label, label.split(PROVISIONAL).join("")]).filter((word) => word.length > 0))];
  sentences.forEach((sentence, index) => {
    const at = `文 ${index}(${sentence.template})`;
    if (sentence.template === "terms") {
      const body = sentence.text.startsWith(TERMS_PREFIX) ? sentence.text.slice(TERMS_PREFIX.length) : null;
      const allowed = TERMS.map(({ text }) => text) as string[];
      if (body === null || !body.split(TERMS_SEPARATOR).every((entry) => allowed.includes(entry))) problems.push(`${at}: 用語の並びが型と違う`);
      return;
    }
    const key = sentence.template;
    const bySlot = new Map(sentence.sources.map((source) => [source.slot as string, source]));
    // 1. 固定文は型とバイト一致を確かめてから取り除く(禁止語は数えない)
    if (FIXED_TEMPLATES.includes(key)) {
      let rebuilt: string | null;
      try {
        rebuilt = fillTemplate(key, (name) => {
          const source = bySlot.get(name);
          if (source === undefined) throw new Error("slot");
          return slotText(source);
        });
      } catch {
        rebuilt = null;
      }
      if (rebuilt !== sentence.text) problems.push(`${at}: 固定文が型と違う`);
    } else {
      // 2. 残りの文に禁止語・label・位置を限る語
      // 監査 93 の S-1: 空白・ゼロ幅文字で割った語や半角の語も止めるため、文と語の両方をそろえてから照合する
      const normalized = normalizeForMatch(sentence.text);
      for (const word of [...FORBIDDEN_WORDS, ...labelWords]) if (normalized.includes(normalizeForMatch(word))) problems.push(`${at}: 「${word}」を含む`);
    }
    // 3. 文の終わり(位置の検査)
    const endings = ENDINGS[key];
    if (endings !== null) {
      const parts = splitSentences(sentence.text);
      const ok = parts.length === endings.length && parts.every((part, i) => {
        const ending = endings[i]!;
        return typeof ending === "string" ? part.endsWith(ending) : ending.test(part);
      });
      if (!ok) problems.push(`${at}: 文の終わりが型の位置と違う`);
    }
    // 4. 数(文の本文の数字は差し込み口の値か許す直書きだけ)
    if (NUMBER_CHECKED_TEMPLATES.includes(key)) {
      const pool = [...sentence.sources.flatMap((source) => slotText(source).match(/[0-9]+/g) ?? []), ...(ALLOWED_LITERAL_DIGITS[key] ?? [])];
      for (const digits of sentence.text.match(/[0-9]+/g) ?? []) {
        const i = pool.indexOf(digits);
        if (i === -1) problems.push(`${at}: 数字 ${digits} が差し込み口の値でも許す直書きでもない`);
        else pool.splice(i, 1);
      }
    }
  });
  return problems;
}

// ---- 報告(計画 6.)----

export interface ReportOptions {
  audience: Audience;
  /** person の報告に insufficient の行を載せる(報告ごとに司令塔が決める ― Q-3) */
  includeInsufficient?: boolean;
}

export interface ReportContext {
  definitions: readonly ReportDefinition[];
  standingBounds: StandingBounds;
  /** 読んだ Gate の記録(path はリポジトリ相対) */
  input: { path: string; sha256: string };
  provenance: { gitHead: string | null; dirty: boolean | null };
}

export interface ContractRules {
  templatesSha256: string;
  forbiddenWordsSha256: string;
}

export interface ReportItem extends GateItemIn {
  description: string;
}

export interface ReportConditionLine {
  contract: typeof DIAGNOSIS_REPORT_CONTRACT;
  schemaVersion: typeof DIAGNOSIS_REPORT_SCHEMA_VERSION;
  audience: Audience;
  lineKind: "condition";
  condition: { id: string; status: "draft" | "approved"; definitionSha256: string };
  verdict: "meets" | "insufficient" | "notJudged";
  notJudged?: "draft" | "pairNotApplied";
  test: { set: string };
  sentences: ReportSentence[];
  /** dev だけ */
  dev?: { label: string; items: ReportItem[]; rowsNotTaken: number; omittedForPerson: OmittedReason | null; testDirection: TestDirectionNote };
  input: { path: string; sha256: string; line: number };
  contractRules: ContractRules;
  provenance: { gitHead: string | null; dirty: boolean | null };
}

export interface ReportSummaryLine {
  contract: typeof DIAGNOSIS_REPORT_CONTRACT;
  schemaVersion: typeof DIAGNOSIS_REPORT_SCHEMA_VERSION;
  audience: Audience;
  lineKind: "summary";
  sentences: ReportSentence[];
  /** dev だけ */
  dev?: { conditions: number; shownForPerson: number; omittedForPerson: number; rowsNotTaken: number };
  input: { path: string; sha256: string };
  contractRules: ContractRules;
  provenance: { gitHead: string | null; dirty: boolean | null };
}

export type ReportLine = ReportConditionLine | ReportSummaryLine;

export interface DiagnosisReport {
  lines: ReportLine[];
  markdown: string[];
}

const sha256Of = (value: unknown): string => createHash("sha256").update(JSON.stringify(value)).digest("hex");

/** 使った文の型と禁止語の一覧の版(計画 6. の contractRules) */
export function contractRulesOf(): ContractRules {
  const endings = Object.fromEntries(Object.entries(ENDINGS).map(([key, list]) => [key, list === null ? null : list.map(String)]));
  return { templatesSha256: sha256Of({ TEMPLATES, ENDINGS: endings, TERMS, SLOT_FIELDS, SLOT_DERIVED_BY }), forbiddenWordsSha256: sha256Of(FORBIDDEN_WORDS) };
}

const RESULT_LABELS: Record<GateItemResult, string> = { met: "満たした", notMet: "満たさなかった", notEvaluable: "測れなかった" };
const DIRECTION_LABELS: Record<TestDirectionNote, string> = { shown: "文を出した", noDifference: "差なし", notComparable: "比べられない", notApplicable: "文の対象外" };

/** Gate の行(JSON.parse した値と行番号)から、audience の報告を組む。確かめに当たれば ReportInputError / ReportOutputError で止める(書かない) */
export function buildDiagnosisReport(entries: ReadonlyArray<{ line: number; value: unknown }>, context: ReportContext, options: ReportOptions): DiagnosisReport {
  const problems: string[] = [];
  if (entries.length === 0) throw new ReportInputError(["入力に行が 1 つも無い"]);
  if (context.input.path.startsWith("/") || /^\.\.(\/|\\|$)/.test(context.input.path)) problems.push("入力の path が絶対パスか根の外(リポジトリ相対でない ― R-10。監査 93 の C-2)");
  const rows: NumberedGateLine[] = [];
  for (const entry of entries) {
    const value = readGateLine(entry.value, entry.line, problems);
    if (value !== null) rows.push({ line: entry.line, value });
  }
  if (problems.length > 0) throw new ReportInputError(problems);

  const taken = chooseRows(rows);
  const definitionBySha = new Map(context.definitions.map((definition) => [definition.definitionSha256, definition]));
  for (const { row } of taken) {
    const at = `行 ${row.line}`;
    const condition = row.value.condition;
    const definition = definitionBySha.get(condition.definitionSha256);
    if (definition === undefined) {
      problems.push(`${at}: definitionSha256 の定義のファイルが無い(条件 ${condition.id})`);
      continue;
    }
    if (definition.id !== condition.id || definition.label !== condition.label || definition.status !== condition.status) problems.push(`${at}: 定義のファイルの id・label・status が行と違う`);
    if (definition.status === "approved" && definition.readableText === undefined) problems.push(`${at}: approved の定義に readableText が無い`);
    if (definition.readableText !== undefined && (definition.readableText === "" || definition.readableText.includes(PROVISIONAL))) problems.push(`${at}: readableText が空か「(仮)」を含む`);
  }
  const games = new Set(taken.map(({ row }) => row.value.material.inputs.length));
  const inRun = new Set(taken.map(({ row }) => row.value.conditionsInRun));
  if (games.size > 1) problems.push(`採った行どうしで material.inputs の本数が違う(${[...games].join("・")} ― C-2)`);
  if (inRun.size > 1) problems.push(`採った行どうしで conditionsInRun が違う(${[...inRun].join("・")} ― C-2)`);
  if (problems.length > 0) throw new ReportInputError(problems);

  const rules = contractRulesOf();
  const lines: ReportLine[] = [];
  const allSentences: ReportSentence[] = [];
  const outcomes = taken.map((entry) => ({ entry, definition: definitionBySha.get(entry.row.value.condition.definitionSha256)!, outcome: conditionOutcome(entry.row.value, definitionBySha.get(entry.row.value.condition.definitionSha256)!, options) }));

  for (const { entry, definition, outcome } of outcomes) {
    if (options.audience === "person" && !outcome.shownForPerson) continue;
    const value = entry.row.value;
    const gate = value.gate;
    const verdict = "verdict" in gate ? gate.verdict : "notJudged";
    allSentences.push(...outcome.sentences);
    lines.push({
      contract: DIAGNOSIS_REPORT_CONTRACT,
      schemaVersion: DIAGNOSIS_REPORT_SCHEMA_VERSION,
      audience: options.audience,
      lineKind: "condition",
      condition: { id: value.condition.id, status: value.condition.status, definitionSha256: value.condition.definitionSha256 },
      verdict,
      ...("notJudged" in gate ? { notJudged: gate.notJudged } : {}),
      test: { set: value.test.set },
      sentences: outcome.sentences,
      ...(options.audience === "dev"
        ? {
            dev: {
              label: definition.label,
              items: "items" in gate ? gate.items.map((item) => ({ ...item, description: ITEM_DESCRIPTIONS[item.item] })) : [],
              rowsNotTaken: entry.rowsNotTaken,
              omittedForPerson: outcome.omittedForPerson,
              testDirection: outcome.testDirection,
            },
          }
        : {}),
      input: { path: context.input.path, sha256: context.input.sha256, line: entry.row.line },
      contractRules: rules,
      provenance: context.provenance,
    });
  }

  const shownConditions = lines.length;
  const summary: ReportSentence[] = [];
  if (options.audience === "person" && shownConditions === 0) summary.push(render("none", []));
  if (allSentences.some((sentence) => sentence.template === "F-1" || sentence.template === "F-2" || sentence.template === "F-2b")) {
    summary.push(
      render("N-1", [
        slot("aheadCp", context.standingBounds.aheadCp, signedCpText(context.standingBounds.aheadCp)),
        slot("behindCp", context.standingBounds.behindCp, signedCpText(context.standingBounds.behindCp)),
        slot("approvedOn", STANDING_BOUNDS_APPROVED_ON),
      ]),
    );
  }
  const first = taken[0]!.row.value;
  summary.push(render("N-2", [slot("games", first.material.inputs.length), slot("conditionsInRun", first.conditionsInRun)]));
  const terms = termsSentence([...allSentences, ...summary].map((sentence) => sentence.text));
  if (terms !== null) summary.push(terms);

  const labels = taken.map(({ row }) => row.value.condition.label);
  const outputIssues = outputProblems([...allSentences, ...summary], labels);
  if (outputIssues.length > 0) throw new ReportOutputError(outputIssues);

  const shownForPerson = outcomes.filter(({ outcome }) => outcome.shownForPerson).length;
  lines.push({
    contract: DIAGNOSIS_REPORT_CONTRACT,
    schemaVersion: DIAGNOSIS_REPORT_SCHEMA_VERSION,
    audience: options.audience,
    lineKind: "summary",
    sentences: summary,
    ...(options.audience === "dev"
      ? { dev: { conditions: taken.length, shownForPerson, omittedForPerson: taken.length - shownForPerson, rowsNotTaken: taken.reduce((sum, entry) => sum + entry.rowsNotTaken, 0) } }
      : {}),
    input: { path: context.input.path, sha256: context.input.sha256 },
    contractRules: rules,
    provenance: context.provenance,
  });

  return { lines, markdown: renderMarkdown(lines, outcomes, options.audience) };
}

function renderMarkdown(lines: readonly ReportLine[], outcomes: ReadonlyArray<{ entry: TakenRow; outcome: ConditionOutcome }>, audience: Audience): string[] {
  const out: string[] = [audience === "dev" ? "# 診断の報告(STEP D6・dev)" : "# 診断の報告", ""];
  for (const line of lines) {
    if (line.lineKind !== "condition") continue;
    const [heading, ...rest] = line.sentences;
    out.push(`## ${heading!.text}`, "");
    for (const sentence of rest) out.push(sentence.text, "");
    if (audience !== "dev" || line.dev === undefined) continue;
    out.push(`- 定義の label: ${line.dev.label}(status ${line.condition.status})`);
    if (line.dev.items.length > 0) {
      out.push("", "| 項目 | 説明 | 値 | 閾値 | 結果 | 理由 |", "|---|---|---|---|---|---|");
      for (const item of line.dev.items) {
        const values = Object.entries(item.values).map(([key, value]) => `${key} ${value}`).join("・");
        const threshold = Object.entries(item.threshold).map(([key, value]) => `${key} ${value}`).join("・");
        out.push(`| ${item.item} | ${item.description} | ${values} | ${threshold} | ${RESULT_LABELS[item.result]} | ${item.reasons.join("・") || "―"} |`);
      }
      out.push("");
    }
    const found = outcomes.find(({ entry }) => entry.row.line === line.input.line);
    const value = found?.entry.row.value;
    if (value !== undefined && "tally" in value.material) {
      const t = value.material.tally.truePairs;
      const f = value.material.tally.falsePairs;
      out.push(
        "| 群 | 直前が優勢(崩れ / 分母) | 直前が互角(崩れ / 分母) | 5 手以内(参考) |",
        "|---|---|---|---|",
        `| 当てはまる組 | ${t.byBefore.ahead.collapsed} / ${t.byBefore.ahead.denominator} | ${t.byBefore.level.collapsed} / ${t.byBefore.level.denominator} | ${t.within5.dropped} / ${t.within5.denominator} |`,
        `| 当てはまらない組 | ${f.byBefore.ahead.collapsed} / ${f.byBefore.ahead.denominator} | ${f.byBefore.level.collapsed} / ${f.byBefore.level.denominator} | ${f.within5.dropped} / ${f.within5.denominator} |`,
        "",
      );
    }
    out.push(`- 試す側の向き(F-4): ${DIRECTION_LABELS[line.dev.testDirection]}`, `- 採らなかった行: ${line.dev.rowsNotTaken}`, `- person に出さない理由: ${line.dev.omittedForPerson ?? "―(出す)"}`, "");
  }
  const summary = lines.find((line): line is ReportSummaryLine => line.lineKind === "summary");
  if (summary !== undefined) {
    const [maybeNone, ...notes] = summary.sentences;
    if (maybeNone !== undefined && maybeNone.template === "none") out.push(maybeNone.text, "");
    out.push("## 注記", "");
    for (const sentence of maybeNone !== undefined && maybeNone.template === "none" ? notes : summary.sentences) out.push(sentence.text, "");
    if (audience === "dev" && summary.dev !== undefined) {
      out.push(`- 条件式 ${summary.dev.conditions} 本・person に出す ${summary.dev.shownForPerson} 本・出さない ${summary.dev.omittedForPerson} 本・採らなかった行 ${summary.dev.rowsNotTaken}`, "");
    }
  }
  return out;
}
