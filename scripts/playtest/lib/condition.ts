// STEP D3-COND の骨組み(docs/STEP_D3-COND_PLAN_2026-09-15.md §2・§3。D4 計画 docs/STEP_D4_PLAN_2026-09-15.md §3 の改訂を含む)。
// 名前つきの条件式(定義)を、Failure Event・上がり・最大の下がりの組の行・全ての手の組の行に当てて「該当 / 非該当 / 判定不能」に分け、
// 1 人ぶんを数える純粋関数。
//
// 【このファイルがやること】
// - 定義の読み込みと確かめ(`checkCondition`・`loadCondition`。§2 の R-4 と D4 §3 の種類の列・書けない欄)。`definitionSha256` は定義のファイルのバイト列から作る
// - 読める欄の表 `READABLE_FIELDS`(パスごとに、持つ行の種類・門・null の意味)。表に無いパスは読まない
// - 判定(`judgeCondition`): 門と null の意味で読み、`uses` のパスだけを持つ写し(view)を `evaluate` に渡す(入力を丸ごと渡さない)
// - 読み筋の側の判定(`judgeConditionPvSide`。D4 §3 の Q-4): `counterfactual.actual.*` を `counterfactual.pv.*` に置き換えた view に同じ `evaluate` を当てる
// - 1 人ぶんの集計(`conditionTallyOf`)と試す側の集計(`testSideTallyOf`。先手の局と後手の局を別の列に)。§7.2 用の列(急落の Event だけ)
//
// 【このファイルが絶対にやらないこと】
// - 条件式の中身・閾値を置くこと(定義は lib/conditions/ に 1 件 1 ファイル。人間の承認の後に別 STEP で足す ― 計画 §5)
// - 「3 件以上か」「20 局以上か」を判定語にすること。評価語・「この人は〜した」(出すのは「該当」「非該当」「判定不能」と数だけ)
// - 判定不能を非該当に畳むこと・分母に入れること。LLM・エンジン
// - 全ての手の組の作り方(`allPairsOf`)と Gate(D4 本体)。出力の契約 diagnosis-condition v0.1 と diagnose.ts の口(D-SCREEN-2 の後に足す)
//
// 【判断的知識】無い。表の行(どの欄を読めるか・門・null の意味)は計画の骨組み(監査を経て足す)。定義は draft の判断的知識(CLAUDE.md ルール 4)。

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import type { MaxDropMoment, MomentPairFields, RiseMoment } from "./diagnosisMoment.js";
import type { BranchKind, EvaluationPair, FailureEvent } from "./failureEvent.js";
import type { FixedKifuEnding } from "./kifuImport.js";

// ---- 行と定義の型(計画 §2)----

/** 定義が当たる行の種類(`appliesTo` の値)。`pair` は全ての手の組(D4 §3) */
export type ConditionRowKind = "failureEvent" | "rise" | "maxDropPair" | "pair";
export const CONDITION_ROW_KINDS: readonly ConditionRowKind[] = ["failureEvent", "rise", "maxDropPair", "pair"];

/** 全ての手の組の行(D4 §2 の形。作る関数 `allPairsOf` は D4 で足す) */
export type PairRow = { kifuId: string; pairKind: EvaluationPair["kind"] } & MomentPairFields;

/** 判定に渡す 1 行。`maxDrop` は組の行(`maxDropPair`)と状態の行(noDrop・noComparedPair)の両方を受ける */
export type ConditionInput =
  | { kind: "failureEvent"; row: FailureEvent }
  | { kind: "rise"; row: RiseMoment }
  | { kind: "maxDrop"; row: MaxDropMoment }
  | { kind: "pair"; row: PairRow };

/** `evaluate` に渡す写し。`uses` のパスだけを持つ(外の欄は undefined) */
export type ConditionView = { readonly [key: string]: unknown };

export interface ConditionApproval {
  approvedBy: string;
  date: string;
  record: string;
}

export interface ConditionDefinition {
  id: string;
  /** 必ず「(仮)」を含む */
  label: string;
  status: "draft" | "approved";
  definitionText: string;
  /** 読む欄のパス(`READABLE_FIELDS` の `path`) */
  uses: readonly string[];
  thresholds: Readonly<Record<string, number>>;
  appliesTo: readonly ConditionRowKind[];
  /** draft は null */
  approval: ConditionApproval | null;
  evaluate(view: ConditionView): boolean;
}

export interface LoadedCondition {
  definition: ConditionDefinition;
  /** 定義のファイルのバイト列の sha256(16 進) */
  definitionSha256: string;
}

// ---- 読める欄の表(計画 §2 の R-1、D4 §3 で種類の列・D2.5 の行・書けない欄を足した)----

/** 値を読む前に満たすべき祖先の状態。`passes` に無い値なら判定不能(理由 = 実際の値) */
export interface ReadableGate {
  path: string;
  passes: readonly (string | boolean)[];
}

export interface ReadableField {
  path: string;
  /** そのパスを持つ行の種類(D4 §3。N-1 を閉じる) */
  kinds: readonly ConditionRowKind[];
  /** 前から順に確かめる */
  gates: readonly ReadableGate[];
  /** null の意味。`notNullable` は型が null を持たない欄(null が来たら例外) */
  nullMeans: "value" | "undecidable" | "notNullable";
  /** 値が `{ undetermined }`(形勢の状態が未定)なら判定不能(D4 §3 の D2.5 の行) */
  undeterminedIsUndecidable?: true;
  /** D4 §3 (i): 直後の行の評価から作られる欄。`pair` を含む定義の `uses` に書けない */
  afterRow?: true;
  /** D4 §3 (ii): 読み筋の側の置き換えで実戦の事実のまま読まれる欄。`pair` を含む定義の `uses` に書けない */
  actualKept?: true;
}

const ALL_KINDS: readonly ConditionRowKind[] = CONDITION_ROW_KINDS;
const EVENT_KINDS: readonly ConditionRowKind[] = ["failureEvent"];
const MOMENT_PAIR_KINDS: readonly ConditionRowKind[] = ["rise", "maxDropPair", "pair"];
const CHANGE_KINDS: readonly ConditionRowKind[] = ["rise", "maxDropPair"];

const MEASURED = (base: string): ReadableGate => ({ path: `${base}.state`, passes: ["measured"] });
const COMPARED: ReadableGate = { path: "counterfactual.state", passes: ["compared"] };
const COUNTED = (base: string): ReadableGate => ({ path: `${base}.state`, passes: ["counted"] });
const WINDOW_NOT_SHORT: ReadableGate = { path: "consequences.windowShort", passes: [false] };

const EVALUATION_VALUES = ["scoreCp", "mate", "bestmove", "afterPassScoreCp", "afterPassMate", "dropCp"] as const;
const ZONES = ["ownKingZone", "opponentKingZone"] as const;
const BY_SIDES = ["bySente", "byGote"] as const;

/** 玉の区域の数の葉(D2.5)。`withSquares` は zoneSquares を含むか(差は持たない) */
function zoneLeaves(base: string, withSquares: boolean): string[] {
  const leaves: string[] = [];
  if (withSquares) for (const zone of ZONES) leaves.push(`${base}.zoneSquares.${zone}`);
  for (const group of ["zonePieces", "zoneControl"]) {
    for (const zone of ZONES) for (const side of BY_SIDES) leaves.push(`${base}.${group}.${zone}.${side}`);
  }
  return leaves;
}

function field(path: string, kinds: readonly ConditionRowKind[], gates: readonly ReadableGate[], nullMeans: ReadableField["nullMeans"], flags: Pick<ReadableField, "undeterminedIsUndecidable" | "afterRow" | "actualKept"> = {}): ReadableField {
  return { path, kinds, gates, nullMeans, ...flags };
}

function sequenceFields(side: "actual" | "pv"): ReadableField[] {
  const base = `counterfactual.${side}`;
  return [
    field(`${base}.capturedRoles.us`, ALL_KINDS, [COMPARED], "notNullable"),
    field(`${base}.capturedRoles.opponent`, ALL_KINDS, [COMPARED], "notNullable"),
    field(`${base}.checks.byUs`, ALL_KINDS, [COMPARED], "notNullable"),
    field(`${base}.checks.byOpponent`, ALL_KINDS, [COMPARED], "notNullable"),
    field(`${base}.mate`, ALL_KINDS, [COMPARED], "value"),
    field(`${base}.gameEnd`, ALL_KINDS, [COMPARED], "value"),
    field(`${base}.kingSurroundingsEnd.squares`, ALL_KINDS, [COMPARED], "value"),
    field(`${base}.kingSurroundingsEnd.own`, ALL_KINDS, [COMPARED], "value"),
    ...zoneLeaves(`${base}.positionFactsEnd`, true).map((path) => field(path, ALL_KINDS, [COMPARED], "undecidable")),
    field(`${base}.kingEscapesEnd.count`, ALL_KINDS, [COMPARED, COUNTED(`${base}.kingEscapesEnd`)], "notNullable"),
  ];
}

export const READABLE_FIELDS: readonly ReadableField[] = [
  // trigger(直前の行。すべての種類が持つ)
  ...EVALUATION_VALUES.map((name) => field(`trigger.evaluationBefore.${name}`, ALL_KINDS, [MEASURED("trigger.evaluationBefore")], "value")),
  field("trigger.focus.state", ALL_KINDS, [{ path: "trigger.focus.state", passes: ["stated", "nothingToSay"] }], "notNullable"),
  field("trigger.shape.status", ALL_KINDS, [{ path: "trigger.shape.state", passes: ["recorded"] }], "notNullable"),
  field("trigger.opponentIntent.classification", ALL_KINDS, [], "notNullable"),
  field("trigger.kingSurroundings.squares", ALL_KINDS, [], "value"),
  field("trigger.kingSurroundings.own", ALL_KINDS, [], "value"),
  ...zoneLeaves("trigger.positionFacts", true).map((path) => field(path, ALL_KINDS, [], "undecidable")),

  // Failure Event だけ(action・branch)
  field("action.playedMove", EVENT_KINDS, [], "value"),
  field("action.bestmoveAtBefore", EVENT_KINDS, [], "value"),
  field("branch.kinds", EVENT_KINDS, [], "notNullable", { afterRow: true }),
  field("branch.diffCp", EVENT_KINDS, [], "undecidable", { afterRow: true }),
  field("branch.mateAfter", EVENT_KINDS, [], "undecidable", { afterRow: true }),
  field("branch.matedIfPassAfter", EVENT_KINDS, [], "notNullable", { afterRow: true }),
  ...EVALUATION_VALUES.map((name) => field(`branch.evaluationAfter.${name}`, EVENT_KINDS, [MEASURED("branch.evaluationAfter")], "value", { afterRow: true })),
  field("branch.standingPair.before", EVENT_KINDS, [], "notNullable", { undeterminedIsUndecidable: true }),
  field("branch.standingPair.after", EVENT_KINDS, [], "notNullable", { undeterminedIsUndecidable: true, afterRow: true }),

  // 組の行(上がり・最大の下がりの組の行・全ての手の組)だけ
  field("moves.userMove", MOMENT_PAIR_KINDS, [], "notNullable"),
  field("moves.opponentMove", MOMENT_PAIR_KINDS, [], "notNullable"),
  field("userBestmoveAtBefore", MOMENT_PAIR_KINDS, [], "value"),
  ...EVALUATION_VALUES.map((name) => field(`evaluationAfter.${name}`, MOMENT_PAIR_KINDS, [MEASURED("evaluationAfter")], "value", { afterRow: true })),
  field("standingPair.before", MOMENT_PAIR_KINDS, [], "notNullable", { undeterminedIsUndecidable: true }),
  field("standingPair.after", MOMENT_PAIR_KINDS, [], "notNullable", { undeterminedIsUndecidable: true, afterRow: true }),
  field("failureEventBranchPly", MOMENT_PAIR_KINDS, [], "value", { afterRow: true }),

  // 上がり・最大の下がりの組の行だけ(change)
  field("change.kind", CHANGE_KINDS, [], "notNullable", { afterRow: true }),
  field("change.diffCp", CHANGE_KINDS, [{ path: "change.kind", passes: ["cp"] }], "notNullable", { afterRow: true }),
  field("change.mateAfter", CHANGE_KINDS, [{ path: "change.kind", passes: ["mateAfter"] }], "notNullable", { afterRow: true }),

  // 実戦の続き(分岐の手の後の窓。すべての種類が持つ)
  field("consequences.checks", ALL_KINDS, [WINDOW_NOT_SHORT], "notNullable", { actualKept: true }),
  field("consequences.mate", ALL_KINDS, [WINDOW_NOT_SHORT], "value", { actualKept: true }),

  // 反事実(すべての種類が持つ)
  field("counterfactual.state", ALL_KINDS, [], "notNullable"),
  field("counterfactual.comparedPlies", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.windowPlies", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.actualPlies", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvLength", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvUsablePlies", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvTruncatedAtPly", ALL_KINDS, [COMPARED], "value"),
  field("counterfactual.pvBounded.lowerbound", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvBounded.upperbound", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvFirstMove", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvFirstMoveIsBestmoveAtBefore", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.pvFirstMoveIsPlayedMove", ALL_KINDS, [COMPARED], "notNullable"),
  field("counterfactual.kingEscapesRoot.count", ALL_KINDS, [COMPARED, COUNTED("counterfactual.kingEscapesRoot")], "notNullable"),
  ...sequenceFields("actual"),
  ...sequenceFields("pv"),
  field("counterfactual.pvMinusActual.capturedRoles.us", ALL_KINDS, [COMPARED], "undecidable", { actualKept: true }),
  field("counterfactual.pvMinusActual.capturedRoles.opponent", ALL_KINDS, [COMPARED], "undecidable", { actualKept: true }),
  field("counterfactual.pvMinusActual.kingSurroundingsOwn", ALL_KINDS, [COMPARED], "undecidable", { actualKept: true }),
  field("counterfactual.pvMinusActual.kingEscapes", ALL_KINDS, [COMPARED], "undecidable", { actualKept: true }),
  ...zoneLeaves("counterfactual.pvMinusActual.positionFacts", false).map((path) => field(path, ALL_KINDS, [COMPARED], "undecidable", { actualKept: true })),
  field("counterfactual.kingEscapesChangeFromRoot.actual", ALL_KINDS, [COMPARED], "undecidable", { actualKept: true }),
  field("counterfactual.kingEscapesChangeFromRoot.pv", ALL_KINDS, [COMPARED], "undecidable"),
];

const FIELD_BY_PATH: ReadonlyMap<string, ReadableField> = new Map(READABLE_FIELDS.map((entry) => [entry.path, entry]));

// ---- 読み込み(計画 §2 の R-4、D4 §3)----

export type ConditionLoadProblem =
  | { code: "malformed"; detail: string }
  | { code: "approvedWithoutApproval" }
  | { code: "draftWithApproval" }
  | { code: "labelWithoutProvisional" }
  | { code: "emptyAppliesTo" }
  | { code: "unknownPath"; path: string }
  | { code: "pathNotInKind"; path: string; kind: ConditionRowKind }
  | { code: "afterRowFieldWithPair"; path: string }
  | { code: "actualKeptFieldWithPair"; path: string };

export class ConditionLoadError extends Error {
  constructor(readonly problems: readonly ConditionLoadProblem[]) {
    super(`条件式の定義を読み込めない: ${problems.map((problem) => JSON.stringify(problem)).join(" / ")}`);
    this.name = "ConditionLoadError";
  }
}

const PROVISIONAL = "(仮)";

function malformedProblems(value: unknown): ConditionLoadProblem[] {
  const problems: ConditionLoadProblem[] = [];
  const bad = (detail: string) => problems.push({ code: "malformed", detail });
  if (typeof value !== "object" || value === null) {
    bad("定義がオブジェクトでない");
    return problems;
  }
  const d = value as Record<string, unknown>;
  for (const key of ["id", "label", "definitionText"]) if (typeof d[key] !== "string" || d[key] === "") bad(`${key} が空でない文字列でない`);
  if (d.status !== "draft" && d.status !== "approved") bad("status が draft・approved でない");
  if (!Array.isArray(d.uses) || !d.uses.every((path) => typeof path === "string")) bad("uses が文字列の配列でない");
  if (typeof d.thresholds !== "object" || d.thresholds === null || !Object.values(d.thresholds).every((v) => typeof v === "number")) bad("thresholds が数の表でない");
  if (!Array.isArray(d.appliesTo) || !d.appliesTo.every((kind) => CONDITION_ROW_KINDS.includes(kind as ConditionRowKind))) bad("appliesTo が行の種類の配列でない");
  const approval = d.approval as Record<string, unknown> | null | undefined;
  if (approval !== null && (typeof approval !== "object" || !["approvedBy", "date", "record"].every((key) => typeof approval[key] === "string"))) bad("approval が null でも承認の記録でもない");
  if (typeof d.evaluate !== "function") bad("evaluate が関数でない");
  return problems;
}

/** 読み込んだ定義を確かめる(純粋関数)。問題が 1 つでもあれば全部を並べて ConditionLoadError */
export function checkCondition(value: unknown, fileBytes: Uint8Array): LoadedCondition {
  const malformed = malformedProblems(value);
  if (malformed.length > 0) throw new ConditionLoadError(malformed);
  const definition = value as ConditionDefinition;
  const problems: ConditionLoadProblem[] = [];
  if (definition.status === "approved" && definition.approval === null) problems.push({ code: "approvedWithoutApproval" });
  if (definition.status === "draft" && definition.approval !== null) problems.push({ code: "draftWithApproval" });
  if (!definition.label.includes(PROVISIONAL)) problems.push({ code: "labelWithoutProvisional" });
  if (definition.appliesTo.length === 0) problems.push({ code: "emptyAppliesTo" });
  const withPair = definition.appliesTo.includes("pair");
  for (const path of definition.uses) {
    const entry = FIELD_BY_PATH.get(path);
    if (entry === undefined) {
      problems.push({ code: "unknownPath", path });
      continue;
    }
    for (const kind of definition.appliesTo) if (!entry.kinds.includes(kind)) problems.push({ code: "pathNotInKind", path, kind });
    if (withPair && entry.afterRow) problems.push({ code: "afterRowFieldWithPair", path });
    if (withPair && entry.actualKept) problems.push({ code: "actualKeptFieldWithPair", path });
  }
  if (problems.length > 0) throw new ConditionLoadError(problems);
  return { definition, definitionSha256: createHash("sha256").update(fileBytes).digest("hex") };
}

/** 定義のファイル(`export default` に定義)を読み込む。sha256 は読み込んだファイルのバイト列から */
export async function loadCondition(filePath: string): Promise<LoadedCondition> {
  const absolute = resolve(filePath);
  const fileBytes = readFileSync(absolute);
  const module = (await import(pathToFileURL(absolute).href)) as { default?: unknown };
  return checkCondition(module.default, fileBytes);
}

// ---- 判定(計画 §2)----

export type MissingReason =
  /** 門を満たさない(`actual` は門の実際の値) */
  | { kind: "gate"; gatePath: string; actual: string | boolean }
  /** null が判定不能の欄で null だった */
  | { kind: "null" }
  /** 形勢の状態が未定 */
  | { kind: "undetermined"; undetermined: string };

export type ConditionJudgement =
  /** 判定しない(行を作らない。数だけ出す) */
  | { state: "notJudged"; reason: "kindNotApplied" | "maxDropState" }
  | { state: "undecidable"; missing: Array<{ path: string; reason: MissingReason }> }
  | { state: "match" | "noMatch"; usedValues: ConditionView };

/** 読み筋の側を当てられない(D4 §3 の Q-4。G-3 notEvaluable の元) */
export type PvSideJudgement =
  | ConditionJudgement
  | { state: "notApplicable"; reasons: Array<{ reason: "noActualPath" } | { reason: "pathNotReplaceable"; paths: string[] }> };

type AnyRow = FailureEvent | RiseMoment | MaxDropMoment | PairRow;

function rowKindOf(input: ConditionInput): ConditionRowKind {
  return input.kind === "maxDrop" ? "maxDropPair" : input.kind;
}

/** パスを辿る。途中が null なら null(null の意味は欄の表で決める)。キーが無いのは表と行の種類の食い違いなので例外 */
function walk(row: AnyRow, path: string): unknown {
  let current: unknown = row;
  for (const segment of path.split(".")) {
    if (current === null) return null;
    if (typeof current !== "object" || !(segment in current)) throw new Error(`行に ${path} が無い(読める欄の表と行の種類が食い違う)`);
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}

type Read = { ok: true; value: unknown } | { ok: false; reason: MissingReason };

function readField(entry: ReadableField, row: AnyRow): Read {
  for (const gate of entry.gates) {
    const actual = walk(row, gate.path);
    if (!gate.passes.includes(actual as string | boolean)) return { ok: false, reason: { kind: "gate", gatePath: gate.path, actual: actual as string | boolean } };
  }
  const value = walk(row, entry.path);
  if (value === null) {
    if (entry.nullMeans === "value") return { ok: true, value };
    if (entry.nullMeans === "undecidable") return { ok: false, reason: { kind: "null" } };
    throw new Error(`${entry.path} は null を持たない欄だが null だった`);
  }
  if (entry.undeterminedIsUndecidable && typeof value === "object" && "undetermined" in value) {
    return { ok: false, reason: { kind: "undetermined", undetermined: String((value as { undetermined: unknown }).undetermined) } };
  }
  return { ok: true, value };
}

function setPath(view: Record<string, unknown>, path: string, value: unknown): void {
  const segments = path.split(".");
  let current = view;
  for (const segment of segments.slice(0, -1)) {
    current[segment] ??= {};
    current = current[segment] as Record<string, unknown>;
  }
  current[segments[segments.length - 1]!] = value;
}

function deepFreeze<T>(value: T): T {
  if (typeof value === "object" && value !== null) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

/** `reads` の各 (view のパス, 行から読むパス) を表で読み、揃えば view を `evaluate` に渡す */
function judgeReads(definition: ConditionDefinition, row: AnyRow, reads: ReadonlyArray<{ usePath: string; readPath: string }>): ConditionJudgement {
  const missing: Array<{ path: string; reason: MissingReason }> = [];
  const view: Record<string, unknown> = {};
  for (const { usePath, readPath } of reads) {
    const entry = FIELD_BY_PATH.get(readPath);
    if (entry === undefined) throw new Error(`${readPath} は読める欄の表に無い(loadCondition を通していない定義)`);
    const read = readField(entry, row);
    if (read.ok) setPath(view, usePath, structuredClone(read.value));
    else missing.push({ path: usePath, reason: read.reason });
  }
  if (missing.length > 0) return { state: "undecidable", missing };
  const frozen = deepFreeze(view);
  const result = definition.evaluate(frozen);
  if (typeof result !== "boolean") throw new Error(`条件式 ${definition.id} の evaluate が真偽値を返さない`);
  return { state: result ? "match" : "noMatch", usedValues: frozen };
}

function notJudgedOf(definition: ConditionDefinition, input: ConditionInput): ConditionJudgement | null {
  if (!definition.appliesTo.includes(rowKindOf(input))) return { state: "notJudged", reason: "kindNotApplied" };
  if (input.kind === "maxDrop" && "state" in input.row) return { state: "notJudged", reason: "maxDropState" };
  return null;
}

export function judgeCondition(definition: ConditionDefinition, input: ConditionInput): ConditionJudgement {
  return notJudgedOf(definition, input) ?? judgeReads(definition, input.row, definition.uses.map((path) => ({ usePath: path, readPath: path })));
}

const ACTUAL_PREFIX = "counterfactual.actual.";
const PV_PREFIX = "counterfactual.pv.";
/** 読み筋の側でもそのまま読む欄(組の前の事実・共通の欄。D4 §3 の Q-4) */
const PV_SIDE_KEPT_PREFIXES = ["trigger.", "moves."];
const PV_SIDE_KEPT_PATHS = ["standingPair.before", "userBestmoveAtBefore", "counterfactual.state", "counterfactual.comparedPlies", "counterfactual.kingEscapesRoot.count"];

/**
 * 読み筋の側の判定(D4 §3 の Q-4)。`counterfactual.actual.*` を `counterfactual.pv.*` から読み、view には元のパスの名前で置く。
 * 置き換えの表のどちらにも無い欄を使う定義と、`counterfactual.actual.*` を 1 つも使わない定義は当てられない
 */
export function judgeConditionPvSide(definition: ConditionDefinition, input: ConditionInput): PvSideJudgement {
  const notJudged = notJudgedOf(definition, input);
  if (notJudged !== null) return notJudged;
  const reasons: Extract<PvSideJudgement, { state: "notApplicable" }>["reasons"] = [];
  if (!definition.uses.some((path) => path.startsWith(ACTUAL_PREFIX))) reasons.push({ reason: "noActualPath" });
  const notReplaceable = definition.uses.filter(
    (path) => !path.startsWith(ACTUAL_PREFIX) && !PV_SIDE_KEPT_PREFIXES.some((prefix) => path.startsWith(prefix)) && !PV_SIDE_KEPT_PATHS.includes(path),
  );
  if (notReplaceable.length > 0) reasons.push({ reason: "pathNotReplaceable", paths: notReplaceable });
  if (reasons.length > 0) return { state: "notApplicable", reasons };
  return judgeReads(
    definition,
    input.row,
    definition.uses.map((path) => ({ usePath: path, readPath: path.startsWith(ACTUAL_PREFIX) ? PV_PREFIX + path.slice(ACTUAL_PREFIX.length) : path })),
  );
}

// ---- 集計(計画 §3)----

export type UserSide = "sente" | "gote";

/**
 * meta の `mirrored`・`originalUserSide` から本人の側(計画 §3。`originalUserSide` が無ければ先手)。
 * 2 つの欄が食い違えば例外(lib/sideAlignment.ts の読み込みと同じ組み合わせだけを通す)
 */
export function userSideOf(meta: { mirrored?: boolean; originalUserSide?: "gote" } | undefined): UserSide {
  if (meta?.mirrored === true) {
    if (meta.originalUserSide !== "gote") throw new Error("mirrored が true なのに originalUserSide が gote でない");
    return "gote";
  }
  if (meta?.originalUserSide !== undefined) throw new Error("mirrored が true でないのに originalUserSide がある");
  return "sente";
}

/** 1 局ぶんの入力。§7.2 の「落としたか」の材料は呼び出し側が局ごとに渡す(計画 §9 の N-4) */
export interface ConditionGameInput {
  kifuId: string;
  userSide: UserSide;
  /** 固定棋譜 JSON の `ending`。キーが無い古い JSON は undefined、終局の行が無い棋譜は null(どちらも「記録に無い」) */
  ending: FixedKifuEnding | null | undefined;
  /** README の勝ち負け(棋譜を用意した側の一覧)。載っていなければ null */
  listedResult: "win" | "loss" | null;
  events: readonly FailureEvent[];
  rises: readonly RiseMoment[];
  maxDrop: MaxDropMoment;
}

export type Within5 = "present" | "absent" | "windowShort";
export type LostByEnding = "lost" | "notLost" | "undetermined" | "notInRecord";

export interface Section72Match {
  kifuId: string;
  branchPly: number;
  kinds: BranchKind[];
  /** 5 手以内の王手・詰み(consequences) */
  within5: Within5;
  lostByEnding: LostByEnding;
  listedResult: "win" | "loss" | "notListed";
  /** 終局から決めた値と README の表を並べる(どちらかに寄せない) */
  agreement: "agree" | "mismatch" | "notComparable";
}

export interface ConditionTally {
  person: string;
  condition: { id: string; label: string; status: ConditionDefinition["status"]; definitionSha256: string };
  /** 入力の局の数と先手 / 後手の内訳(§7.2 の「20 局以上」はこの数。判定語にしない) */
  games: { total: number; sente: number; gote: number };
  /** 数えた入力の種類(`appliesTo` のうち、この集計が受ける種類。全ての手の組は D4) */
  countedRowKinds: ConditionRowKind[];
  overall: {
    match: number;
    noMatch: number;
    /** 該当 + 非該当(判定不能は入れない) */
    denominator: number;
    undecidable: number;
    /** 判定不能の理由の内訳(欄と理由ごとの行の数。1 行が複数の欄で判定不能なら、それぞれに数える) */
    undecidableReasons: Array<{ path: string; reason: string; rows: number }>;
    notJudged: { kindNotApplied: number; maxDropState: number };
    /** 同じ組 (kifuId, branchPly) を 2 回目以降に見て数えなかった行 */
    duplicatePairsSkipped: number;
    matches: Array<{ kifuId: string; rowKind: ConditionRowKind; branchPly: number }>;
    gamesWithMatch: number;
  };
  /** §7.2 用の列(kinds に cpDrop か mateDrop がある Failure Event だけ。R-3) */
  section72: {
    failureEventApplied: boolean;
    match: number;
    noMatch: number;
    undecidable: number;
    matches: Section72Match[];
    gamesWithMatch: number;
  };
}

/** 本人がその局を落としたと言える終局の種類(計画 §3) */
const LOSS_ENDINGS: ReadonlySet<string> = new Set(["resign", "timeUp", "mate"]);

export function lostByEndingOf(ending: FixedKifuEnding | null | undefined, userSide: UserSide): LostByEnding {
  if (ending === undefined || ending === null) return "notInRecord";
  if (!LOSS_ENDINGS.has(ending.kind) || ending.ply === null) return "undetermined";
  const sideToMove: UserSide = ending.ply % 2 === 1 ? "sente" : "gote";
  return sideToMove === userSide ? "lost" : "notLost";
}

function within5Of(event: FailureEvent): Within5 {
  const { checks, mate, windowShort } = event.consequences;
  if (checks.length > 0 || mate !== null) return "present";
  return windowShort ? "windowShort" : "absent";
}

function agreementOf(lost: LostByEnding, listed: "win" | "loss" | null): Section72Match["agreement"] {
  if (listed === null || (lost !== "lost" && lost !== "notLost")) return "notComparable";
  return (lost === "lost") === (listed === "loss") ? "agree" : "mismatch";
}

function reasonKey(reason: MissingReason): string {
  switch (reason.kind) {
    case "gate":
      return `${reason.gatePath}=${String(reason.actual)}`;
    case "null":
      return "null";
    case "undetermined":
      return `undetermined:${reason.undetermined}`;
  }
}

const isDropEvent = (event: FailureEvent) => event.branch.kinds.some((kind) => kind === "cpDrop" || kind === "mateDrop");

/** 1 人ぶんの集計(計画 §3)。人は呼び出し側がラベルで渡す(推測しない)。同じ kifuId が 2 本あれば例外 */
export function conditionTallyOf(person: string, games: readonly ConditionGameInput[], loaded: LoadedCondition): ConditionTally {
  const seenKifu = new Set<string>();
  for (const game of games) {
    if (seenKifu.has(game.kifuId)) throw new Error(`同じ人(${person})の入力に同じ kifuId が 2 本ある: ${game.kifuId}`);
    seenKifu.add(game.kifuId);
  }
  const { definition } = loaded;
  const countedRowKinds = (["failureEvent", "rise", "maxDropPair"] as const).filter((kind) => definition.appliesTo.includes(kind));

  const overall: ConditionTally["overall"] = {
    match: 0,
    noMatch: 0,
    denominator: 0,
    undecidable: 0,
    undecidableReasons: [],
    notJudged: { kindNotApplied: 0, maxDropState: 0 },
    duplicatePairsSkipped: 0,
    matches: [],
    gamesWithMatch: 0,
  };
  const reasonRows = new Map<string, { path: string; reason: string; rows: number }>();
  const section72: ConditionTally["section72"] = { failureEventApplied: definition.appliesTo.includes("failureEvent"), match: 0, noMatch: 0, undecidable: 0, matches: [], gamesWithMatch: 0 };

  for (const game of games) {
    // 同じ組は 1 回だけ(Failure Event → 最大の下がりの組 → 上がりの順に先に見たものを数える)。判定の値が食い違えば例外
    const judgedPairs = new Map<number, string>();
    const inputs: ConditionInput[] = [
      ...game.events.map((row): ConditionInput => ({ kind: "failureEvent", row })),
      { kind: "maxDrop", row: game.maxDrop },
      ...game.rises.map((row): ConditionInput => ({ kind: "rise", row })),
    ];
    for (const input of inputs) {
      const judgement = judgeCondition(definition, input);
      if (judgement.state === "notJudged") {
        overall.notJudged[judgement.reason] += 1;
        continue;
      }
      const branchPly = (input.row as { branchPly: number }).branchPly;
      const signature = JSON.stringify(judgement);
      const earlier = judgedPairs.get(branchPly);
      if (earlier !== undefined) {
        if (earlier !== signature) throw new Error(`${game.kifuId} の組 ${branchPly} で、行の種類によって判定が食い違う`);
        overall.duplicatePairsSkipped += 1;
        continue;
      }
      judgedPairs.set(branchPly, signature);
      if (judgement.state === "undecidable") {
        overall.undecidable += 1;
        for (const { path, reason } of judgement.missing) {
          const key = `${path} ${reasonKey(reason)}`;
          const entry = reasonRows.get(key) ?? { path, reason: reasonKey(reason), rows: 0 };
          entry.rows += 1;
          reasonRows.set(key, entry);
        }
      } else {
        overall[judgement.state] += 1;
        if (judgement.state === "match") overall.matches.push({ kifuId: game.kifuId, rowKind: rowKindOf(input), branchPly });
      }
      if (input.kind === "failureEvent" && isDropEvent(input.row)) {
        if (judgement.state === "undecidable") section72.undecidable += 1;
        else section72[judgement.state] += 1;
        if (judgement.state === "match") {
          const lostByEnding = lostByEndingOf(game.ending, game.userSide);
          section72.matches.push({
            kifuId: game.kifuId,
            branchPly,
            kinds: [...input.row.branch.kinds],
            within5: within5Of(input.row),
            lostByEnding,
            listedResult: game.listedResult ?? "notListed",
            agreement: agreementOf(lostByEnding, game.listedResult),
          });
        }
      }
    }
  }
  overall.denominator = overall.match + overall.noMatch;
  overall.undecidableReasons = [...reasonRows.values()].sort((a, b) => (a.path === b.path ? a.reason.localeCompare(b.reason) : a.path.localeCompare(b.path)));
  overall.gamesWithMatch = new Set(overall.matches.map((match) => match.kifuId)).size;
  section72.gamesWithMatch = new Set(section72.matches.map((match) => match.kifuId)).size;

  return {
    person,
    condition: { id: definition.id, label: definition.label, status: definition.status, definitionSha256: loaded.definitionSha256 },
    games: { total: games.length, sente: games.filter((game) => game.userSide === "sente").length, gote: games.filter((game) => game.userSide === "gote").length },
    countedRowKinds,
    overall,
    section72,
  };
}

/**
 * 試す側の集計(計画 §4 の 2。R-2)。先手の局と後手の局を**別の列**に出す(混ぜた合計を作らない)。
 * 列と本人の側が食い違う局、2 つの列にまたがる同じ kifuId は例外
 */
export function testSideTallyOf(
  person: string,
  games: { sente: readonly ConditionGameInput[]; gote: readonly ConditionGameInput[] },
  loaded: LoadedCondition,
): { sente: ConditionTally; gote: ConditionTally } {
  for (const side of ["sente", "gote"] as const) {
    const wrong = games[side].find((game) => game.userSide !== side);
    if (wrong !== undefined) throw new Error(`試す側の ${side} の列に、本人が ${wrong.userSide} の局がある: ${wrong.kifuId}`);
  }
  const senteIds = new Set(games.sente.map((game) => game.kifuId));
  const shared = games.gote.find((game) => senteIds.has(game.kifuId));
  if (shared !== undefined) throw new Error(`同じ kifuId が先手と後手の列の両方にある: ${shared.kifuId}`);
  return { sente: conditionTallyOf(person, games.sente, loaded), gote: conditionTallyOf(person, games.gote, loaded) };
}
