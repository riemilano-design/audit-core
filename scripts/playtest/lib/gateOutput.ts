// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §5・§6・§7)。gate.ts の出力の組み立て(契約 diagnosis-gate v0.1 の行・Markdown)と、
// 入力の確かめ・条件式の置き場の読み込み・棄却の記録の追記。集計と判定は lib/gate.ts(ここは数えない)。
//
// 【このファイルがやること】
// - 契約 diagnosis-gate v0.1 の 1 行(条件式 1 本 × 1 回)を組み立て、スキーマに照らす
// - 入力の確かめ(人のラベル・referenceNodes がそろうか・同じ記録の重なり・試す側の先手 / 後手・error 行)。問題は全部並べる
// - 棄却の記録 records/gate/<person>.jsonl への**追記だけ**(pair を含まない定義の行は追記しない ― T-3)
// - Markdown(条件式ごとの status と「(仮)」・Gate の各項目の値と閾値・直前の状態ごとの崩れ率・verdict の文。基準値の表 ― T-6)
//
// 【このファイルが絶対にやらないこと】
// - 評価語を足すこと(Gate の 2 つの文のほかに判定の語を出さない)。人の名前を書くこと(ラベルは p1・p2 の記号だけ ― S-8)
// - 棄却の記録を上書き・並べ替え・消すこと。エンジン・LLM

import { appendFileSync, existsSync, mkdirSync, readdirSync, readFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";
import type { MetaLine } from "../invariants/types.js";
import { loadCondition, userSideOf, type LoadedCondition } from "./condition.js";
import { validate, type JsonSchema } from "./eventSchema.js";
import { baselineTallyOf, type CollapseTally, type GateItem, type GateTally, type GateValues, type GateVerdict } from "./gate.js";
import { DIAGNOSIS_GATE_SCHEMA_VERSION, KNOWN_DIAGNOSIS_GATE_SCHEMA_VERSIONS } from "./schemaVersions.js";

export const DIAGNOSIS_GATE_CONTRACT = "diagnosis-gate" as const;
export { DIAGNOSIS_GATE_SCHEMA_VERSION };
export type DiagnosisGateSchemaVersion = (typeof KNOWN_DIAGNOSIS_GATE_SCHEMA_VERSIONS)[number];

// ---- 行(契約 diagnosis-gate v0.1)----

export interface GateInputFile {
  /** 根からの相対パス */
  path: string;
  sha256: string;
}

export interface GateTestSet {
  /** `sente<n>` か `sente<n>+gote<m>`(計画 Q-10) */
  set: string;
  /** 後手の局を入れていなければ true */
  provisional: boolean;
}

interface GateLineBase {
  contract: typeof DIAGNOSIS_GATE_CONTRACT;
  schemaVersion: typeof DIAGNOSIS_GATE_SCHEMA_VERSION;
  /** 材料の側の人のラベル(p1・p2 の記号) */
  person: string;
  /** 試す側の人のラベル(司令塔の決定 T-8) */
  testPerson: string;
  condition: { id: string; label: string; status: "draft" | "approved"; definitionSha256: string };
  source: { referenceNodes: number; evaluation: "light" };
}

interface GateLineTail {
  gateValues: GateValues;
  /** この実行で Gate に当てた定義の数(pair を含まない定義は数えない ― T-3) */
  conditionsInRun: number;
  provenance: { gitHead: string | null; dirty: boolean | null };
}

export type GateLine =
  | (GateLineBase & {
      material: { inputs: GateInputFile[]; tally: GateTally };
      test: GateTestSet & { inputs: GateInputFile[]; tally: GateTally };
      gate: GateVerdict | { notJudged: "draft" };
    } & GateLineTail)
  | (GateLineBase & {
      material: { inputs: GateInputFile[] };
      test: GateTestSet & { inputs: GateInputFile[] };
      gate: { notJudged: "pairNotApplied" };
    } & GateLineTail);

export interface GateRunContext {
  person: string;
  testPerson: string;
  referenceNodes: number;
  materialInputs: GateInputFile[];
  test: GateTestSet & { inputs: GateInputFile[] };
  gateValues: GateValues;
  conditionsInRun: number;
  provenance: { gitHead: string | null; dirty: boolean | null };
}

/** 行を組み立てる(欄の順はスキーマの properties と同じ)。`judged` が null なら pair を含まない定義の行 */
export function gateLineOf(
  context: GateRunContext,
  loaded: LoadedCondition,
  judged: { material: GateTally; test: GateTally; gate: GateVerdict | { notJudged: "draft" } } | null,
): GateLine {
  const { definition, definitionSha256 } = loaded;
  const base: GateLineBase = {
    contract: DIAGNOSIS_GATE_CONTRACT,
    schemaVersion: DIAGNOSIS_GATE_SCHEMA_VERSION,
    person: context.person,
    testPerson: context.testPerson,
    condition: { id: definition.id, label: definition.label, status: definition.status, definitionSha256 },
    source: { referenceNodes: context.referenceNodes, evaluation: "light" },
  };
  const tail: GateLineTail = { gateValues: { ...context.gateValues }, conditionsInRun: context.conditionsInRun, provenance: context.provenance };
  const testSet = { set: context.test.set, provisional: context.test.provisional, inputs: context.test.inputs };
  if (judged === null) {
    return { ...base, material: { inputs: context.materialInputs }, test: testSet, gate: { notJudged: "pairNotApplied" }, ...tail };
  }
  return { ...base, material: { inputs: context.materialInputs, tally: judged.material }, test: { ...testSet, tally: judged.test }, gate: judged.gate, ...tail };
}

export function loadDiagnosisGateSchema(version: DiagnosisGateSchemaVersion = DIAGNOSIS_GATE_SCHEMA_VERSION): JsonSchema {
  return JSON.parse(readFileSync(new URL(`../schemas/diagnosis-gate.v${version}.schema.json`, import.meta.url), "utf-8")) as JsonSchema;
}

/** 1 行(JSON.parse した値)を契約のスキーマに照らす。誤りを 1 件 1 行で返す(空なら通った) */
export function validateDiagnosisGateLine(line: unknown, schema: JsonSchema = loadDiagnosisGateSchema()): string[] {
  return validate(line, schema);
}

/** 試す側の集合の名前(計画 Q-10) */
export const testSetOf = (senteGames: number, goteGames: number): GateTestSet =>
  goteGames === 0 ? { set: `sente${senteGames}`, provisional: true } : { set: `sente${senteGames}+gote${goteGames}`, provisional: false };

// ---- 入力の確かめ(計画 §2 の Q-2・§6・T-7・T-8)----

export class GateInputError extends Error {
  constructor(readonly problems: readonly string[]) {
    super(`gate.ts の入力を受け付けない: ${problems.join(" / ")}`);
    this.name = "GateInputError";
  }
}

export interface GateInputEntry {
  /** 表示に使う名前(ファイルのパス) */
  name: string;
  /** 作業ツリーの根からの相対パス(契約の行の inputs[].path に書く値) */
  path: string;
  kifuId: string;
  sha256: string;
  meta: MetaLine | undefined;
  errorLines: number;
}

export const PERSON_LABEL = /^p[0-9]+$/;

/** 問題を 1 件 1 文で返す(空なら通す)。referenceNodes は材料と試す側のすべてでそろうこと。そろえば `referenceNodes` を返す */
export function gateInputProblems(input: {
  person: string;
  testPerson: string;
  material: readonly GateInputEntry[];
  testSente: readonly GateInputEntry[];
  testGote: readonly GateInputEntry[];
}): { problems: string[]; referenceNodes: number | null } {
  const problems: string[] = [];
  for (const [flag, label] of [["--person", input.person], ["--test-person", input.testPerson]] as const) {
    if (!PERSON_LABEL.test(label)) problems.push(`${flag} は p1・p2 の形の記号(名前を書かない): ${JSON.stringify(label)}`);
  }
  if (input.person === input.testPerson) problems.push(`材料と試す側が同じ人のラベル(${input.person})`);
  if (input.material.length === 0) problems.push("--material の記録が無い");
  if (input.testSente.length === 0) problems.push("--test-sente の記録が無い");
  // 監査 93 の R-1: 根の外のパス(.. で始まる・絶対パス)を契約の行と棄却の記録に書かない
  for (const entry of [...input.material, ...input.testSente, ...input.testGote]) {
    if (isAbsolute(entry.path) || /^\.\.(\/|\\|$)/.test(entry.path)) problems.push(`${entry.name} は作業ツリーの根の外にある(根の外のパスを記録に書かない): ${entry.path}`);
  }

  const all = [...input.material, ...input.testSente, ...input.testGote];
  for (const key of ["name", "sha256", "kifuId"] as const) {
    const seen = new Map<string, number>();
    for (const entry of all) seen.set(entry[key], (seen.get(entry[key]) ?? 0) + 1);
    for (const [value, count] of seen) if (count > 1) problems.push(`同じ ${key} の記録が ${count} 本ある(材料と試す側の重なりを含む): ${value}`);
  }

  const nodes = new Set<unknown>();
  for (const entry of all) {
    if (entry.meta === undefined) {
      problems.push(`${entry.name} に meta の行が無い`);
      continue;
    }
    const referenceNodes = (entry.meta as { referenceNodes?: unknown }).referenceNodes;
    if (typeof referenceNodes !== "number" || !Number.isInteger(referenceNodes) || referenceNodes <= 0) problems.push(`${entry.name} の meta.referenceNodes が正の整数でない`);
    nodes.add(referenceNodes);
    if (entry.errorLines > 0) problems.push(`${entry.name} に error 行が ${entry.errorLines} 行ある(途中で止まった記録は数えない)`);
  }
  if (nodes.size > 1) problems.push(`referenceNodes がそろわない(${[...nodes].map(String).join(", ")})。1 回の集計の中で同じ探索の値だけを使う(Q-2)`);

  for (const [side, entries] of [["sente", input.testSente], ["gote", input.testGote]] as const) {
    for (const entry of entries) {
      if (entry.meta === undefined) continue;
      try {
        const actual = userSideOf(entry.meta as { mirrored?: boolean; originalUserSide?: "gote" });
        if (actual !== side) problems.push(`--test-${side} の ${entry.name} は本人が ${actual} の記録`);
      } catch (error) {
        problems.push(`${entry.name} の本人の側を読めない: ${(error as Error).message}`);
      }
    }
  }
  const only = [...nodes][0];
  return { problems, referenceNodes: nodes.size === 1 && typeof only === "number" && Number.isInteger(only) && only > 0 ? only : null };
}

/** 後手の局を入れる実行は、Gate に入る定義がすべて approved のときだけ(N-5・T-7)。問題の文を返す */
export function testGoteProblems(testGote: number, conditions: readonly LoadedCondition[]): string[] {
  if (testGote === 0) return [];
  if (conditions.length === 0) return ["--test-gote は承認された定義を 1 本以上当てる実行でだけ受ける(定義が 0 本)"];
  const drafts = conditions.filter((loaded) => loaded.definition.status !== "approved").map((loaded) => loaded.definition.id);
  return drafts.length === 0 ? [] : [`--test-gote は定義がすべて approved のときだけ受ける(draft: ${drafts.join(", ")})`];
}

// ---- 条件式の置き場 ----

/** 置き場の `*.ts`(`*.test.ts` を除く)を名前の順に読み込む。同じ id が 2 本あれば止める。0 本でもよい(T-6) */
export async function loadConditionsDir(dir: string): Promise<LoadedCondition[]> {
  if (!existsSync(dir)) throw new GateInputError([`--conditions の置き場が無い: ${dir}`]);
  const files = readdirSync(dir)
    .filter((name) => name.endsWith(".ts") && !name.endsWith(".test.ts"))
    .sort();
  const loaded: LoadedCondition[] = [];
  for (const name of files) loaded.push(await loadCondition(join(dir, name)));
  const ids = new Map<string, number>();
  for (const entry of loaded) ids.set(entry.definition.id, (ids.get(entry.definition.id) ?? 0) + 1);
  const duplicated = [...ids].filter(([, count]) => count > 1).map(([id]) => id);
  if (duplicated.length > 0) throw new GateInputError([`同じ id の定義が 2 本以上ある: ${duplicated.join(", ")}`]);
  return loaded;
}

// ---- 棄却の記録(計画 §5 の Q-8)----

const recordsPathOf = (dir: string, person: string): string => {
  if (!PERSON_LABEL.test(person)) throw new GateInputError([`棄却の記録のラベルが p1・p2 の形でない: ${JSON.stringify(person)}`]);
  return join(dir, `${person}.jsonl`);
};

/** これまでの行の数と、当てた条件式の数(definitionSha256 の種類)。ファイルが無ければ 0 */
export function gateRecordsSummary(dir: string, person: string): { rows: number; conditions: number } {
  const file = recordsPathOf(dir, person);
  if (!existsSync(file)) return { rows: 0, conditions: 0 };
  const lines = readFileSync(file, "utf-8")
    .split("\n")
    .filter((line) => line.trim() !== "")
    .map((line) => JSON.parse(line) as { condition?: { definitionSha256?: unknown } });
  return { rows: lines.length, conditions: new Set(lines.map((line) => line.condition?.definitionSha256)).size };
}

/**
 * 追記だけ(上書きしない)。pair を含まない定義の行は追記しない(T-3)。draft の定義の行は追記する(集計を見た定義も数える ― 計画 §13 の J-4)。
 * 追記する行が 0 ならファイルもディレクトリも作らない。戻り値は追記した行の数
 */
export function appendGateRecords(dir: string, person: string, lines: readonly GateLine[]): number {
  const file = recordsPathOf(dir, person);
  const kept = lines.filter((line) => !("notJudged" in line.gate && line.gate.notJudged === "pairNotApplied"));
  if (kept.length === 0) return 0;
  mkdirSync(dir, { recursive: true });
  appendFileSync(file, kept.map((line) => `${JSON.stringify(line)}\n`).join(""), "utf-8");
  return kept.length;
}

// ---- Markdown(計画 §7)----

const ratio = (count: { collapsed: number; denominator: number }): string =>
  count.denominator === 0 ? `${count.collapsed} / 0` : `${count.collapsed} / ${count.denominator}(${((100 * count.collapsed) / count.denominator).toFixed(1)}%)`;

const COLLAPSE_HEADER = [
  "| 群 | 組 | 崩れ / 分母 | ahead→level | level→behind | ahead→behind | 直前 behind(外した) | 直前が未定 | 直後が未定 | 直前 ahead | 直前 level | 5 手以内 下がった / 分母 | 窓が足りない | 5 手以内の下がりの件(重なりを除く) | 崩れのある局 | 分母の組がある局 |",
  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
];

function collapseRow(label: string, tally: CollapseTally): string {
  const w = tally.within5;
  return `| ${label} | ${tally.pairs} | ${ratio(tally)} | ${tally.transitions.aheadToLevel} | ${tally.transitions.levelToBehind} | ${tally.transitions.aheadToBehind} | ${tally.excluded.cannotFall} | ${tally.excluded.beforeUndetermined} | ${tally.excluded.afterUndetermined} | ${ratio(tally.byBefore.ahead)} | ${ratio(tally.byBefore.level)} | ${ratio({ collapsed: w.dropped, denominator: w.denominator })} | ${w.excluded.windowShort} | ${w.distinctDrops} | ${tally.gamesWithCollapse} | ${tally.gamesWithDenominator} |`;
}

const formatValues = (values: Record<string, number>): string => Object.entries(values).map(([key, value]) => `${key} ${value}`).join("・") || "―";

function itemRows(items: readonly GateItem[]): string[] {
  return ["| 項目 | 値 | 閾値 | 結果 | 理由 |", "|---|---|---|---|---|", ...items.map((item) => `| ${item.item} | ${formatValues(item.values)} | ${formatValues(item.threshold)} | ${item.result} | ${item.reasons.join("・") || "―"} |`)];
}

export interface GateMarkdownInput {
  person: string;
  testPerson: string;
  referenceNodes: number;
  material: { files: number; baseline: ReturnType<typeof baselineTallyOf> };
  test: GateTestSet & { files: number; baseline: ReturnType<typeof baselineTallyOf> };
  lines: readonly GateLine[];
  recordsBefore: { rows: number; conditions: number };
}

export function renderGateMarkdown(input: GateMarkdownInput): string[] {
  const applied = input.lines.filter((line) => !("notJudged" in line.gate && line.gate.notJudged === "pairNotApplied"));
  const notApplied = input.lines.filter((line) => "notJudged" in line.gate && line.gate.notJudged === "pairNotApplied");
  const lines: string[] = [
    "# 全ての手の組の崩れと Gate(STEP D4)",
    "",
    `- 人のラベル: 材料 ${input.person}・試す側 ${input.testPerson}`,
    `- 出どころ: referenceNodes ${input.referenceNodes}・軽い値(engineReference・searchPvs)`,
    `- 材料: 記録 ${input.material.files} 本・組 ${input.material.baseline.pairs}・窓の手が棋譜に無い組 ${input.material.baseline.movesMissing}`,
    `- 試す側(${input.test.set}${input.test.provisional ? "・仮" : ""}): 記録 ${input.test.files} 本・組 ${input.test.baseline.pairs}・窓の手が棋譜に無い組 ${input.test.baseline.movesMissing}`,
    `- この実行で Gate に当てた条件式: ${applied.length} 本 / 棄却の記録にある、これまでに当てた条件式: ${input.recordsBefore.conditions} 本(行 ${input.recordsBefore.rows})`,
    "",
    "## 全ての組の崩れ(条件式なし)",
    "",
    "崩れ = 組の直後の行で形勢の状態が 1 段以上下がった組。分母は直前が ahead・level で前後とも未定でない組。5 手以内は参考(窓の行が足りない組は分母から外す)。",
    "",
    ...COLLAPSE_HEADER,
    collapseRow("材料", input.material.baseline.all),
    collapseRow(`試す側(${input.test.set})`, input.test.baseline.all),
    "",
  ];
  if (notApplied.length > 0) {
    lines.push("## appliesTo に pair を含まない定義(Gate に当てていない)", "");
    for (const line of notApplied) lines.push(`- ${line.condition.id}(${line.condition.status})`);
    lines.push("");
  }
  lines.push("## 条件式ごと", "");
  if (applied.length === 0) lines.push("- Gate に当てた条件式が無い", "");
  for (const line of applied) {
    if ("notJudged" in line.gate && line.gate.notJudged === "pairNotApplied") continue;
    const judged = line as Extract<GateLine, { material: { tally: GateTally } }>;
    const m = judged.material.tally;
    const t = judged.test.tally;
    lines.push(`### ${line.condition.id} ${line.condition.label}(${line.condition.status})`, "");
    lines.push(`- 材料の判定: 真 ${m.judgements.match}・偽 ${m.judgements.noMatch}・判定不能 ${m.judgements.undecidable}`);
    lines.push(`- 試す側の判定: 真 ${t.judgements.match}・偽 ${t.judgements.noMatch}・判定不能 ${t.judgements.undecidable}`);
    const falseZero = m.falsePairs.collapsed === 0 ? `偽の組の崩れ 0 / ${m.falsePairs.denominator}` : `比 ${m.rates.ratio === null ? "―" : m.rates.ratio.toFixed(2)}`;
    lines.push(`- 材料の崩れ率: 真 ${ratio(m.truePairs)}・偽 ${ratio(m.falsePairs)}・${falseZero}・差 ${m.rates.diffPoints === null ? "―" : `${m.rates.diffPoints.toFixed(1)} ポイント`}`);
    lines.push(
      m.pvSide.state === "applicable"
        ? `- 読み筋の側(揃えた組 ${m.pvSide.n}): 実戦の側の真 ${m.pvSide.actualTrue}・読み筋の側の真 ${m.pvSide.pvTrue}`
        : `- 読み筋の側: 当てられない(${m.pvSide.reasons.map((reason) => reason.reason).join("・")})`,
    );
    lines.push("", ...COLLAPSE_HEADER, collapseRow("材料 真", m.truePairs), collapseRow("材料 偽", m.falsePairs), collapseRow("試す側 真", t.truePairs), collapseRow("試す側 偽", t.falsePairs), "");
    if ("notJudged" in judged.gate) {
      lines.push("- draft の定義なので Gate の判定を出さない", "");
    } else {
      lines.push(...itemRows(judged.gate.items), "", `- ${judged.gate.text}`, "");
    }
  }
  return lines;
}
