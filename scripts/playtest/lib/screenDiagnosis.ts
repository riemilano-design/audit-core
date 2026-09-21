// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §2・§3・§11)。段 2 の記録(rescreen.ts が書いた、meta に `screen` を持つ記録)を
// 診断で読むときの判断を 1 か所に置く。failureEvent.ts・diagnosisMoment.ts・diagnose.ts は、ここで決めた出どころを受けて使うだけにする。
//
// 【このファイルがやること】
// - 段 2 の記録の不変条件を確かめる(§2・§11。破れていれば InvalidScreenRecordError。buildDiagnosisReport が「数えられなかった」にする ― S-8・S-23)
// - 組ごとに、深い値を使うか軽い値を使うかを決める(§3。**2 行とも深く測れていれば 2 行とも深い値、そうでなければ 2 行とも軽い値**)。
//   深い組は、評価も読み筋も同じ読み直しの探索から取る(§11。行の engineReference・searchPvs を深い欄に差し替えた行として渡す)
// - 深く測れなかった行を含む組を数える(deepUnavailable ― S-7)
// - 段 2 とその段 1 を一緒に渡した入力を見つける(§3・S-14)
// - Markdown の読み筋の節の見出しと、読み直しの節(screen のある入力があるときだけ ― S-22・K-8)
//
// 【このファイルが絶対にやらないこと】
// - 閾値を変えること。1 つの組の中で深い値と軽い値を混ぜること
// - screen の無い記録の値を変えること(screen の無い記録にはここの関数を呼ばない)
// - check.ts・不変条件の読む値を変えること(段 2 でも engineReference(軽い値)を読む ― §3)

import type { MetaLine, RecordLine } from "../invariants/types.js";
import type { Counterfactual } from "./counterfactual.js";
import { evaluationOf, pairEvaluations, type DiagnosisRow, type EvaluatedRow, type EvaluationPair, type EvaluationSource } from "./failureEvent.js";
import type { ScreenMeta } from "./rescreen.js";

export type { EvaluationSource };

/** 段 2 の不変条件(計画 §2・§11)を満たさない記録。**数えない** */
export class InvalidScreenRecordError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidScreenRecordError";
  }
}

/** 段 2 の記録とその段 1 を一緒に渡した(計画 §3・S-14)。二重に数えないため diagnose.ts が止める */
export class ScreenInputConflictError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ScreenInputConflictError";
  }
}

// ---- 不変条件(計画 §2・§11)----

const isPositiveInteger = (value: unknown): value is number => typeof value === "number" && Number.isInteger(value) && value > 0;
const isIntegerArray = (value: unknown): value is number[] => Array.isArray(value) && value.every((item) => typeof item === "number" && Number.isInteger(item));
const RULE_KEYS = ["dropCp", "advantageCp", "advantageDropCp", "before", "after"] as const;

function screenShapeProblems(screen: unknown): string[] {
  if (typeof screen !== "object" || screen === null) return ["screen が object でない"];
  const s = screen as Record<string, unknown>;
  const problems: string[] = [];
  if (!isPositiveInteger(s.lightNodes)) problems.push("screen.lightNodes が正の整数でない");
  if (!isPositiveInteger(s.deepNodes)) problems.push("screen.deepNodes が正の整数でない");
  const rule = s.rule as Record<string, unknown> | null | undefined;
  if (typeof rule !== "object" || rule === null || !RULE_KEYS.every((key) => typeof rule[key] === "number")) problems.push("screen.rule の形が違う");
  // 校正の床(rescreen の allPlies)だけ true を書き、ほかはキーを出さない(監査 N-6)
  if (s.allPlies !== undefined && s.allPlies !== true) problems.push("screen.allPlies が true でない");
  if (!isIntegerArray(s.deepPlies)) problems.push("screen.deepPlies が整数の配列でない");
  if (typeof s.sourceSha256 !== "string" || !/^[0-9a-f]{64}$/.test(s.sourceSha256)) problems.push("screen.sourceSha256 が 64 桁の小文字の 16 進でない");
  const run = s.deepRun as Record<string, unknown> | null | undefined;
  if (typeof run !== "object" || run === null) {
    problems.push("screen.deepRun が object でない");
    return problems;
  }
  if (!(typeof run.gitHead === "string" || run.gitHead === null)) problems.push("screen.deepRun.gitHead が文字列か null でない");
  if (!(typeof run.dirty === "boolean" || run.dirty === null)) problems.push("screen.deepRun.dirty が boolean か null でない");
  if (typeof run.enginePath !== "string") problems.push("screen.deepRun.enginePath が文字列でない");
  if (!isPositiveInteger(run.threads)) problems.push("screen.deepRun.threads が正の整数でない");
  if (typeof run.startedAt !== "string") problems.push("screen.deepRun.startedAt が文字列でない");
  if (run.order !== "plyAscending") problems.push('screen.deepRun.order が "plyAscending" でない');
  if (!isIntegerArray(run.measuredOrder)) problems.push("screen.deepRun.measuredOrder が整数の配列でない");
  return problems;
}

const sortedUnique = (values: readonly number[]): number[] => [...new Set(values)].sort((a, b) => a - b);
const sameSet = (a: readonly number[], b: readonly number[]): boolean => sortedUnique(a).join(",") === sortedUnique(b).join(",");

/**
 * 記録の meta の screen を読み、段 2 の不変条件を確かめる。screen が無ければ undefined(ただし深い欄を持つ行があれば止める)。
 * 破れていれば、記録の kifuId と食い違いを全部並べて InvalidScreenRecordError を投げる。
 */
export function screenOfRecord(kifuId: string, meta: MetaLine | undefined, records: readonly RecordLine[]): ScreenMeta | undefined {
  const raw = (meta as unknown as Record<string, unknown> | undefined)?.screen;
  const hasDeep = (record: RecordLine): boolean => Object.hasOwn(record, "engineReferenceDeep");
  const hasPvsDeep = (record: RecordLine): boolean => Object.hasOwn(record, "searchPvsDeep");
  const fail = (problems: string[]): never => {
    throw new InvalidScreenRecordError(`記録 ${kifuId} は段 2 の記録の不変条件(計画 §2・§11)を満たさない: ${problems.join(" / ")}`);
  };

  if (raw === undefined) {
    const withDeep = records.filter((record) => hasDeep(record) || hasPvsDeep(record)).map((record) => record.ply);
    if (withDeep.length > 0) fail([`meta に screen が無いのに、深い欄を持つ行がある(ply ${withDeep.join(",")})`]);
    return undefined;
  }
  const shape = screenShapeProblems(raw);
  if (shape.length > 0) fail(shape);
  const screen = raw as ScreenMeta;

  const problems: string[] = [];
  const deepRowPlies: number[] = [];
  for (const record of records) {
    if (record.phase !== "ready") {
      if (hasDeep(record) || hasPvsDeep(record)) problems.push(`ready でない行(ply ${record.ply})に深い欄がある`);
      continue;
    }
    if (hasDeep(record) !== hasPvsDeep(record)) problems.push(`ply ${record.ply} の engineReferenceDeep と searchPvsDeep の欄の有無が食い違う`);
    if (record.engineReference && record.engineReference.nodes !== screen.lightNodes) {
      problems.push(`ply ${record.ply} の engineReference.nodes が ${record.engineReference.nodes}(screen.lightNodes は ${screen.lightNodes})`);
    }
    if (hasDeep(record)) {
      deepRowPlies.push(record.ply);
      const deep = record.engineReferenceDeep;
      if (deep && deep.nodes !== screen.deepNodes) problems.push(`ply ${record.ply} の engineReferenceDeep.nodes が ${deep.nodes}(screen.deepNodes は ${screen.deepNodes})`);
    }
  }
  if (!sameSet(deepRowPlies, screen.deepPlies)) problems.push(`深い欄を持つ ready 行(${sortedUnique(deepRowPlies).join(",")})が screen.deepPlies(${sortedUnique(screen.deepPlies).join(",")})と違う`);
  if (screen.deepRun.measuredOrder.length !== screen.deepPlies.length || !sameSet(screen.deepRun.measuredOrder, screen.deepPlies)) {
    problems.push(`screen.deepRun.measuredOrder(${screen.deepRun.measuredOrder.join(",")})が screen.deepPlies と同じ行の集まりでない`);
  }
  if (problems.length > 0) fail(problems);
  return screen;
}

// ---- 組ごとの出どころ(計画 §3)----

/** 組 1 つ。`from`・`to` は選んだ出どころの行(深い組は engineReference・searchPvs を深い欄に差し替えた行)、`pair` はその 2 行の組 */
export interface ChosenPair {
  source: EvaluationSource;
  from: EvaluatedRow;
  to: EvaluatedRow;
  pair: EvaluationPair;
  /** 読み直したのに深く測れなかった行(深い状態が notMeasurable・notEvaluation)を含む組。王手中・終局で測らなかった行は含めない */
  deepUnavailable: boolean;
}

/** 行を深い値の行にする。読み直していない行(欄が無い)は null。
 * STEP FILL 作業 X: `checkBaseline` も `checkBaselineDeep` に差し替える(王手中でない行・欄の無い行は
 * `checkBaselineDeep` が undefined なので、差し替え後も `checkBaseline` は undefined のまま ― evaluationOf の読みは変わらない)。 */
function deepRowOf(row: EvaluatedRow): EvaluatedRow | null {
  if (!Object.hasOwn(row.record, "engineReferenceDeep")) return null;
  const record: RecordLine = {
    ...row.record,
    engineReference: row.record.engineReferenceDeep,
    searchPvs: row.record.searchPvsDeep,
    checkBaseline: row.record.checkBaselineDeep,
  };
  return { ply: row.ply, record, evaluation: evaluationOf(record) };
}

/** 軽い値の行(readEvaluations の結果)から、組ごとの出どころを決める。並びと数は pairEvaluations(rows) と同じ */
export function choosePairSources(rows: readonly EvaluatedRow[]): ChosenPair[] {
  const deepRows = rows.map(deepRowOf);
  return pairEvaluations(rows).map((lightPair, index) => {
    const deepFrom = deepRows[index];
    const deepTo = deepRows[index + 1];
    if (deepFrom && deepTo && deepFrom.evaluation.state === "measured" && deepTo.evaluation.state === "measured") {
      return { source: "deep", from: deepFrom, to: deepTo, pair: pairEvaluations([deepFrom, deepTo])[0]!, deepUnavailable: false };
    }
    const deepUnavailable = [deepFrom, deepTo].some(
      (deep) => deep !== null && deep !== undefined && (deep.evaluation.state === "notMeasurable" || deep.evaluation.state === "notEvaluation"),
    );
    return { source: "light", from: rows[index]!, to: rows[index + 1]!, pair: lightPair, deepUnavailable };
  });
}

/** counterfactual に、比べた読み筋の出どころを state の直後に書く(screen のある記録だけ ― §11) */
export function withPvSource(counterfactual: Counterfactual, source: EvaluationSource): Counterfactual {
  const { state, ...rest } = counterfactual;
  return { state, pvSource: source, ...rest } as Counterfactual;
}

export interface ScreenCounts {
  lightNodes: number;
  deepNodes: number;
  /** 読み直した ready 行の数 */
  deepPlies: number;
  /** 2 行とも深い値で比べた組 */
  deepPairs: number;
  /** 2 行とも軽い値の組 */
  lightPairs: number;
  /** 軽い組のうち、深く測れなかった行を含む組 */
  deepUnavailable: number;
}

export function screenCountsOf(screen: ScreenMeta, chosen: readonly ChosenPair[]): ScreenCounts {
  return {
    lightNodes: screen.lightNodes,
    deepNodes: screen.deepNodes,
    deepPlies: screen.deepPlies.length,
    deepPairs: chosen.filter((pair) => pair.source === "deep").length,
    lightPairs: chosen.filter((pair) => pair.source === "light").length,
    deepUnavailable: chosen.filter((pair) => pair.deepUnavailable).length,
  };
}

// ---- 段 2 とその段 1(計画 §3・S-14)----

export interface ScreenInputEntry {
  /** 表示に使う名前(ファイルのパス) */
  name: string;
  kifuId: string;
  /** 入力のファイルのバイト列の sha256 */
  sha256: string;
  meta: MetaLine | undefined;
}

/**
 * 一緒に渡してはいけない入力の組を、1 件 1 文で返す(空なら通す)。
 * (i) screen のある入力の sourceSha256 が、別の入力の sha256 と同じ (ii) 同じ kifuId に、screen のある入力と無い入力がある。
 * **screen の無い記録どうし(records/d-cost の同じ kifuId の 3 本など)・screen のある記録どうしは止めない**(1e の再読み K-1、司令塔の決定 (a))。
 */
export function screenInputConflicts(entries: readonly ScreenInputEntry[]): string[] {
  const screenOf = (entry: ScreenInputEntry): Record<string, unknown> | undefined =>
    (entry.meta as unknown as Record<string, unknown> | undefined)?.screen as Record<string, unknown> | undefined;
  const conflicts: string[] = [];
  for (const entry of entries) {
    const screen = screenOf(entry);
    if (screen === undefined) continue;
    for (const other of entries) {
      if (other !== entry && other.sha256 === screen.sourceSha256) {
        conflicts.push(`段 2 の記録 ${entry.name} と、その段 1 の記録 ${other.name} を一緒に渡している(screen.sourceSha256 が一致)`);
      }
    }
  }
  const kifuIds = [...new Set(entries.map((entry) => entry.kifuId))];
  for (const kifuId of kifuIds) {
    const same = entries.filter((entry) => entry.kifuId === kifuId);
    const withScreen = same.filter((entry) => screenOf(entry) !== undefined);
    const withoutScreen = same.filter((entry) => screenOf(entry) === undefined);
    if (withScreen.length > 0 && withoutScreen.length > 0) {
      conflicts.push(
        `同じ kifuId ${kifuId} に、screen のある記録(${withScreen.map((entry) => entry.name).join("、")})と無い記録(${withoutScreen.map((entry) => entry.name).join("、")})を一緒に渡している`,
      );
    }
  }
  return conflicts;
}

// ---- Markdown(計画 §11・S-22・K-8)----

type CountedRow = DiagnosisRow & { result: Extract<DiagnosisRow["result"], { kind: "counted" }> };
const countedRows = (rows: readonly DiagnosisRow[]): CountedRow[] => rows.filter((row): row is CountedRow => row.result.kind === "counted");

/**
 * 読み筋の節の見出し。**screen のある入力が 1 本も無ければ null**(呼び出し側は今の見出しのまま ― screen の無い入力はバイト一致)。
 * light・deep の件数は screen のある記録の Event だけを数え、screen の無い記録の Event があれば件数を分けて足す(K-8 の決め)。
 */
export function screenCounterfactualHeading(rows: readonly DiagnosisRow[]): string | null {
  const counted = countedRows(rows);
  const screenRows = counted.filter((row) => row.result.screen !== undefined);
  if (screenRows.length === 0) return null;
  const events = screenRows.flatMap((row) => row.result.events);
  const light = events.filter((event) => event.branch.evaluationSource === "light").length;
  const deep = events.filter((event) => event.branch.evaluationSource === "deep").length;
  const plain = counted.filter((row) => row.result.screen === undefined).flatMap((row) => row.result.events).length;
  return `## 実戦の続きと読み筋(STEP D2・D-SCREEN。事実の並びだけ。軽い組の読み筋は③の探索、深い組の読み筋は読み直しの探索(評価値と同じ探索)。light ${light} 件・deep ${deep} 件${plain > 0 ? `・screen の無い記録 ${plain} 件` : ""})`;
}

/** 読み直しの節。**screen のある入力が 1 本も無ければ空**(表はバイト一致) */
export function renderScreenSection(rows: readonly DiagnosisRow[]): string[] {
  const counted = countedRows(rows);
  const screenRows = counted.filter((row) => row.result.screen !== undefined);
  if (screenRows.length === 0) return [];
  const lines: string[] = ["## 読み直し(STEP D-SCREEN。meta に screen のある記録だけ)", ""];
  lines.push("- 深い組 = 2 行とも深く測れた組(2 行とも読み直しの値で比べた)。軽い組 = それ以外(2 行とも段 1 の値)。1 つの組の中で値を混ぜない");
  lines.push("- 深く測れなかった行を含む組 = 軽い組のうち、読み直したのに測れなかった行(測れなかった・評価値でない)を含む組。王手中・終局で測らなかった行は含めない");
  lines.push("- 「評価の状態と組」の表の行の件数(ready 行・測った…)は段 1 の値で数えている。組の件数と Failure Event は組ごとの出どころで数えている");
  const plain = counted.filter((row) => row.result.screen === undefined).map((row) => row.kifuId);
  if (plain.length > 0) lines.push(`- screen の無い記録(読み直していない): ${plain.join("、")}`);
  lines.push("");
  lines.push("| 対象 | 軽いノード数 | 深いノード数 | 読み直した行 | 深い組 | 軽い組 | うち深く測れなかった行を含む組 |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const row of screenRows) {
    const s = row.result.screen!;
    lines.push(`| ${row.kifuId} | ${s.lightNodes} | ${s.deepNodes} | ${s.deepPlies} | ${s.deepPairs} | ${s.lightPairs} | ${s.deepUnavailable} |`);
  }
  if (screenRows.length > 1) {
    const sum = (key: "deepPlies" | "deepPairs" | "lightPairs" | "deepUnavailable") => screenRows.reduce((total, row) => total + row.result.screen![key], 0);
    lines.push(`| 合計 | - | - | ${sum("deepPlies")} | ${sum("deepPairs")} | ${sum("lightPairs")} | ${sum("deepUnavailable")} |`);
  }
  lines.push("");
  return lines;
}
