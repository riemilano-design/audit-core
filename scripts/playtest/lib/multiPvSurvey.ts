// STEP U6-T((あ′)。docs/STEP_U6-T_PLAN_2026-09-13.md)。
// 回帰の局面に MultiPV の探索を当て、読み筋の本数・長さ・標識(lowerbound / upperbound)の
// 分布を出すための部品。**本番の挙動を変えない。apps/ のファイルを 1 行も変えない。**
//
// 【この部品を CLI から切り離して lib/ に置く理由(計画 §6.2)】
// 走らせる部品・門番・集計・式を CLI の中に閉じると、試験を置けない
// (U6-R の R-8/R-9、P-32)。「実物で 1 回確かめた」は見張りではない(規則 11.8)。
// そこでエンジンを差し込める形にし、K-1〜K-6 をすべて単体試験で見張る。
//
// 【本番から import するもの(司令塔の決定。計画 §8)】
// - エンジン層の型(LowPriorityEngine・GoOptions・MultiPvGoResult)
// - analysis/searchPv.ts の toSearchPvObservations ― 標識・長さの定義を U6-L の記録と揃える
// - analysis/pvMaterials.ts の computePvMaterials ― 門番が実際に見る usablePlies を得る
// 本番の導線(状態応答・候補手の安全確認・画面)は通さない。
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断。読み筋が良いか、5 本の性格が違うかは見ない(計画 §7.1)
// - 評価値の差を候補手除外の 300cp で切ること(承認された閾値を別の量に当てない。計画 §7.1)
// - 判断的知識の値を既定値として持つこと(minPlies・許容 5% は呼び出し側が渡す)
// - D-3 の判定(成り立つ / 成り立たない)を出すこと(2026-09-14 の司令塔の決定。分布だけを出す。計画 §3 D-3)

import type { LowPriorityEngine } from "../../../apps/server/src/engine/prioritizedEngine.js";
import type { GoOptions, MultiPvGoResult } from "../../../apps/server/src/engine/usiEngine.js";
import {
  toSearchPvObservations,
  type SearchPvObservation,
} from "../../../apps/server/src/analysis/searchPv.js";
import { computePvMaterials, type PvMaterialRules } from "../../../apps/server/src/analysis/pvMaterials.js";
import { PV_LENGTH_BUCKETS, pvLengthBucket, type PvLengthBucket } from "./searchPvStats.js";

// ---- 局面(計画 §1.5)----

export interface SurveyOrigin {
  kifuId: string;
  ply: number;
}

export interface SurveyRoot {
  /** 代表の sfen(最初に現れた行のもの) */
  sfen: string;
  /** この局面が現れた元の行すべて。重複した局面は全部並べる */
  origins: SurveyOrigin[];
}

/** 計画 §1.5 の規則: sfen の手数欄(4 つ目)を除いた「盤・手番・持ち駒」で同じ局面とみなす。 */
export function positionKey(sfen: string): string {
  return sfen.split(" ").slice(0, 3).join(" ");
}

/** 同じ局面を 1 つに畳む。並びは最初に現れた順(決定的)。 */
export function dedupeRoots(rows: ReadonlyArray<{ kifuId: string; ply: number; sfen: string }>): SurveyRoot[] {
  const byKey = new Map<string, SurveyRoot>();
  for (const row of rows) {
    const key = positionKey(row.sfen);
    const existing = byKey.get(key);
    if (existing) existing.origins.push({ kifuId: row.kifuId, ply: row.ply });
    else byKey.set(key, { sfen: row.sfen, origins: [{ kifuId: row.kifuId, ply: row.ply }] });
  }
  return [...byKey.values()];
}

// ---- 探索の条件(計画 §4)----

export type SurveyCondition =
  | { multiPv: number; mode: "nodes"; nodes: number }
  | { multiPv: number; mode: "movetime"; movetimeMs: number };

/** 条件から go の引数を作る。**ここで作った値だけをエンジンへ渡す**(K-2 の見張りの対象)。 */
export function goOptionsFor(condition: SurveyCondition): GoOptions {
  switch (condition.mode) {
    case "nodes":
      return { nodes: condition.nodes };
    case "movetime":
      return { movetimeMs: condition.movetimeMs };
    default: {
      const unknown: never = condition;
      throw new Error(`未知の条件です: ${JSON.stringify(unknown)}`);
    }
  }
}

export function conditionKey(condition: SurveyCondition): string {
  return condition.mode === "nodes"
    ? `MultiPV${condition.multiPv}/nodes${condition.nodes}`
    : `MultiPV${condition.multiPv}/movetime${condition.movetimeMs}`;
}

/**
 * 局面ごとに条件の順序を交互にする(計画 §4)。偶数番目は [a, b]、奇数番目は [b, a]。
 * 置換表の持ち越しは消していない。**どちらかの条件が常に得をする形にしないだけ**である。
 */
export function conditionOrder<T>(rootIndex: number, pair: readonly [T, T]): [T, T] {
  return rootIndex % 2 === 0 ? [pair[0], pair[1]] : [pair[1], pair[0]];
}

// ---- 1 探索 1 行(計画 §2.1)----

/**
 * 1 本の読み筋。**U6-L の `toSearchPvObservations` の変換をそのまま借りる**(標識・長さ・
 * 評価値の読み方を記録と同じにするため)。
 *
 * `source`・`sfen`・`moveUsi` は捨てる。`source` の値域は apps/ にあり、**apps/ を変えずに
 * この計測用の値を足せない。**別の値を付けたまま残すと 1 つの欄が 2 つの意味を持つので、
 * 変換の直後に取り除く。局面は行の `rootSfen` が持つ。
 */
export type SurveyLine = Omit<SearchPvObservation, "source" | "sfen" | "moveUsi"> & {
  /** 門番(U6-M)が実際に見る手数。非合法手で打ち切る前までに再生できた手数 */
  usablePlies: number;
  /** 非合法手に当たった位置(1 始まり)。最後まで再生できたなら null */
  truncatedAtPly: number | null;
};

/**
 * `{ kind, status }` で「無い」を 3 種類に分ける(規則 11.6。計画 §2.1)。
 * - その条件で探索していない → **行が無い**
 * - 探索したが失敗した → `status: "failed"`・`lines: null`
 * - 探索して読み筋が 1 本も返らなかった → `status: "ok"`・`lines: []`
 */
export type SurveySearchRow = {
  kind: "search";
  rootIndex: number;
  rootSfen: string;
  origins: SurveyOrigin[];
  condition: SurveyCondition;
  /** その局面で何番目に行った探索か(0 始まり) */
  order: number;
  /**
   * エンジンの探索(go)を送ってから返る(または失敗する)までの時間。失敗の行にも書く。
   * **段 B(movetime)でだけ意味を持つ**(CPU の取り合いを見る。計画 §4 段 B の 4)。
   * 段 A はノード固定なので、時間は結果に影響せず、集計にも出さない(buildSurveyReport)。
   */
  elapsedMs: number;
} & ({ status: "ok"; lines: SurveyLine[] } | { status: "failed"; lines: null; error: string });

export type OkSurveyRow = Extract<SurveySearchRow, { status: "ok" }>;

/**
 * 再生に使う規則。**usablePlies と truncatedAtPly はこの規則に依存しない**
 * (規則が変えるのは材料の中身だけ)。型が必須なので 1 つ選んでいるにすぎない。
 */
const REPLAY_RULES: PvMaterialRules = {
  contact: "capture_available",
  kingNeighborhood: "eight_neighbors",
  advance: "rank_delta",
  reach: "sliding_attack_count",
};

/** 探索 1 回の結果を読み筋の行へ写す。`computePvMaterials` は **minPlies = 0** で呼び、門番で隠さない。 */
export function toSurveyLines(rootSfen: string, result: MultiPvGoResult): SurveyLine[] {
  return toSearchPvObservations("candidate_baseline", rootSfen, null, result.lines).map((observation) => {
    const { source: _source, sfen: _sfen, moveUsi: _moveUsi, ...rest } = observation;
    const replay = computePvMaterials(rootSfen, rest.pv, REPLAY_RULES, 0);
    if (replay.kind !== "measured") {
      // minPlies = 0 なので usablePlies < 0 にはならず、ここへは来ないはず。来たら黙らない。
      throw new Error("minPlies = 0 で insufficient が返りました");
    }
    return { ...rest, usablePlies: replay.usablePlies, truncatedAtPly: replay.truncatedAtPly };
  });
}

// ---- 走らせる部品(計画 §4・§4.1)----

export interface RunSurveyParams {
  roots: readonly SurveyRoot[];
  conditions: readonly [SurveyCondition, SurveyCondition];
  /**
   * 条件ごとのエンジンのハンドルを返す。**最初に条件ごとに 1 回ずつ呼び、以後その条件の探索は
   * そのハンドルだけで行う**(MultiPV の設定が条件をまたがないようにする。H-9 と同じ)。
   */
  engineFor: (condition: SurveyCondition) => LowPriorityEngine;
  /** 1 行できるたびに呼ぶ(途中で止まっても、そこまでの行を書き出せるように) */
  onRow?: (row: SurveySearchRow) => void;
  /**
   * 所要時間を測る時計(ミリ秒)。**既定値を置かない**(試験では偽の時計を渡し、CLI は
   * `Date.now` を渡す。既定値があると、試験が本物の時計に依存しても気づけない)。
   */
  clock: () => number;
}

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export interface RunSurveyResult {
  rows: SurveySearchRow[];
  /** 失敗が出て、その時点で止めたか */
  stoppedAfterFailure: boolean;
}

/**
 * 局面 × 条件の探索を順に行う。
 *
 * **失敗が 1 件でも出たら、その時点で止め、それ以降の探索をしない**(計画 §4.1・K-6)。
 * 時間切れは待ち手を外して reject するだけで stop を送らないので(`usiEngine.ts:131-133`)、
 * 同じエンジンで続けると、まだ走っている探索の出力が次の探索の読み筋として返りうる。
 * **続ければ、この道具自身の記録が汚れる。**
 */
export async function runSurvey(params: RunSurveyParams): Promise<RunSurveyResult> {
  const handles = new Map<SurveyCondition, LowPriorityEngine>();
  for (const condition of params.conditions) handles.set(condition, params.engineFor(condition));
  // 条件ごとに別のハンドルでなければ、MultiPV の設定が条件をまたぐ(H-9)。
  // CLI の側に試験は無いので、ここで止める(同じハンドルが返ってきたら探索を 1 本もしない)。
  if (new Set(handles.values()).size !== handles.size) {
    throw new Error("engineFor が 2 つの条件に同じハンドルを返しました。条件ごとに別のハンドルが要ります");
  }

  const rows: SurveySearchRow[] = [];
  for (const [rootIndex, root] of params.roots.entries()) {
    for (const [order, condition] of conditionOrder(rootIndex, params.conditions).entries()) {
      const engine = handles.get(condition);
      if (!engine) throw new Error(`条件のハンドルがありません: ${conditionKey(condition)}`);
      const base = { kind: "search" as const, rootIndex, rootSfen: root.sfen, origins: root.origins, condition, order };

      // 時間は go が決着した直後に測る(読み筋の再生の時間を探索の時間に混ぜない)。
      const started = params.clock();
      let result: MultiPvGoResult | undefined;
      let searchError: unknown;
      try {
        engine.setMultiPv(condition.multiPv);
        engine.position(root.sfen);
        result = await engine.goMultiPv(goOptionsFor(condition));
      } catch (err) {
        searchError = err;
      }
      const elapsedMs = params.clock() - started;

      let row: SurveySearchRow;
      if (result === undefined) {
        row = { ...base, elapsedMs, status: "failed", lines: null, error: errorMessage(searchError) };
      } else {
        try {
          row = { ...base, elapsedMs, status: "ok", lines: toSurveyLines(root.sfen, result) };
        } catch (err) {
          row = { ...base, elapsedMs, status: "failed", lines: null, error: errorMessage(err) };
        }
      }

      rows.push(row);
      params.onRow?.(row);
      if (row.status === "failed") return { rows, stoppedAfterFailure: true };
    }
  }
  return { rows, stoppedAfterFailure: false };
}

// ---- 門番(計画 §3。標識が先、長さが後)----

export type GateVerdict = "usable" | "rejected_bound" | "rejected_length";

/**
 * 門番の判定。**標識を先に見る**(U6-L で司令塔が確定した「標識第一」)。
 * 長さは `pv.length` ではなく **`usablePlies`**(U6-M の門番が実際に見る量)で判定する。
 * `minPlies` は判断的知識なので既定値を持たない。
 */
export function classifyLine(
  line: Pick<SurveyLine, "lowerbound" | "upperbound" | "usablePlies">,
  minPlies: number,
): GateVerdict {
  if (line.lowerbound || line.upperbound) return "rejected_bound";
  if (line.usablePlies < minPlies) return "rejected_length";
  return "usable";
}

// ---- 集計(判断はしない。計画 §2.2)----

export function okRows(rows: readonly SurveySearchRow[]): OkSurveyRow[] {
  return rows.filter((row): row is OkSurveyRow => row.status === "ok");
}

export function linesOf(rows: readonly SurveySearchRow[]): SurveyLine[] {
  return okRows(rows).flatMap((row) => row.lines);
}

export function isBounded(line: Pick<SurveyLine, "lowerbound" | "upperbound">): boolean {
  return line.lowerbound || line.upperbound;
}

/** S-1: 条件ごとの探索数・失敗数・返った本数の分布・要求本数と違った探索の数。 */
export interface ConditionSummary {
  condition: string;
  searches: number;
  failed: number;
  linesReturned: Record<number, number>;
  requestedMismatch: number;
}

export function summarizeConditions(rows: readonly SurveySearchRow[]): ConditionSummary[] {
  const byKey = new Map<string, ConditionSummary>();
  for (const row of rows) {
    const key = conditionKey(row.condition);
    const summary =
      byKey.get(key) ?? { condition: key, searches: 0, failed: 0, linesReturned: {}, requestedMismatch: 0 };
    summary.searches += 1;
    if (row.status === "failed") summary.failed += 1;
    else {
      const count = row.lines.length;
      summary.linesReturned[count] = (summary.linesReturned[count] ?? 0) + 1;
      if (count !== row.condition.multiPv) summary.requestedMismatch += 1;
    }
    byKey.set(key, summary);
  }
  return [...byKey.values()];
}

/** S-2: multipv 番号ごとの標識の数。 */
export function boundsByIndex(
  lines: readonly SurveyLine[],
): Array<{ multipv: number; lines: number; lowerbound: number; upperbound: number }> {
  const byIndex = new Map<number, { multipv: number; lines: number; lowerbound: number; upperbound: number }>();
  for (const line of lines) {
    const entry = byIndex.get(line.multipv) ?? { multipv: line.multipv, lines: 0, lowerbound: 0, upperbound: 0 };
    entry.lines += 1;
    if (line.lowerbound) entry.lowerbound += 1;
    if (line.upperbound) entry.upperbound += 1;
    byIndex.set(line.multipv, entry);
  }
  return [...byIndex.values()].sort((a, b) => a.multipv - b.multipv);
}

/** S-3: 標識の有無 × 長さ。区切りは U6-L の searchPvStats と同じものを使う(定義を 2 か所に持たない)。 */
export function boundLengthTable(
  lines: readonly SurveyLine[],
  measure: "pvLength" | "usablePlies",
): { bound: Record<PvLengthBucket, number>; unbounded: Record<PvLengthBucket, number> } {
  const empty = (): Record<PvLengthBucket, number> =>
    Object.fromEntries(PV_LENGTH_BUCKETS.map((bucket) => [bucket, 0])) as Record<PvLengthBucket, number>;
  const bound = empty();
  const unbounded = empty();
  for (const line of lines) {
    const length = measure === "pvLength" ? line.pv.length : line.usablePlies;
    (isBounded(line) ? bound : unbounded)[pvLengthBucket(length)] += 1;
  }
  return { bound, unbounded };
}

/** S-4: 標識なしの本を、控えの候補それぞれで切ったときに落ちる本数(1 つの値だけを出さない)。 */
export function unboundedLossByThreshold(
  lines: readonly SurveyLine[],
  thresholds: readonly number[],
): Array<{ threshold: number; lost: number; unboundedTotal: number }> {
  const unbounded = lines.filter((line) => !isBounded(line));
  return thresholds.map((threshold) => ({
    threshold,
    lost: unbounded.filter((line) => line.usablePlies < threshold).length,
    unboundedTotal: unbounded.length,
  }));
}

/** S-6: 打ち切り・空の読み筋・1 探索の中で先頭の手が重複した本の数。 */
export function summarizeAnomalies(
  rows: readonly SurveySearchRow[],
): { truncated: number; emptyPv: number; duplicateFirstMoves: number } {
  let truncated = 0;
  let emptyPv = 0;
  let duplicateFirstMoves = 0;
  for (const row of okRows(rows)) {
    const seen = new Set<string>();
    for (const line of row.lines) {
      if (line.truncatedAtPly !== null) truncated += 1;
      const first = line.pv[0];
      if (first === undefined) {
        emptyPv += 1;
        continue;
      }
      if (seen.has(first)) duplicateFirstMoves += 1;
      seen.add(first);
    }
  }
  return { truncated, emptyPv, duplicateFirstMoves };
}

// ---- 決め方(計画 §3)----

/** D-1: 標識付きなのに usablePlies が minLength 以上の本の数。 */
export function boundedLongLines(lines: readonly SurveyLine[], minLength: number): number {
  return lines.filter((line) => isBounded(line) && line.usablePlies >= minLength).length;
}

/** D-2 の結果。**3 つの「決められない」を別の値にする**(規則 11.6)。 */
export type MinPliesDecision =
  | { kind: "no_bounded_lines"; unboundedTotal: number }
  | { kind: "no_unbounded_lines"; value: number; boundedMaxUsablePlies: number }
  | {
      kind: "value" | "loss_exceeds_tolerance";
      value: number;
      boundedMaxUsablePlies: number;
      unboundedLost: number;
      unboundedTotal: number;
      lossRatio: number;
    };

/**
 * D-2: **minPlies = 標識付きの本の usablePlies の最大値 + 1**
 * ― 長さの門番だけで標識付きの本をすべて落とせる、最小の値。
 *
 * **この式は「門番が標識を見られない(今の U6-M の引数のまま)」ときの値である**(計画 §3 D-2 の頭)。
 * その値で落ちる標識なしの本の割合が `tolerance` を超えたら `loss_exceeds_tolerance` とし、
 * 値を確定させない。`tolerance`(承認値は 5%)は判断的知識なので既定値を持たない。
 */
export function decideMinPlies(lines: readonly SurveyLine[], tolerance: number): MinPliesDecision {
  const bounded = lines.filter((line) => isBounded(line));
  const unbounded = lines.filter((line) => !isBounded(line));
  if (bounded.length === 0) return { kind: "no_bounded_lines", unboundedTotal: unbounded.length };

  const boundedMaxUsablePlies = Math.max(...bounded.map((line) => line.usablePlies));
  const value = boundedMaxUsablePlies + 1;
  if (unbounded.length === 0) return { kind: "no_unbounded_lines", value, boundedMaxUsablePlies };

  const unboundedLost = unbounded.filter((line) => line.usablePlies < value).length;
  const lossRatio = unboundedLost / unbounded.length;
  return {
    kind: lossRatio > tolerance ? "loss_exceeds_tolerance" : "value",
    value,
    boundedMaxUsablePlies,
    unboundedLost,
    unboundedTotal: unbounded.length,
    lossRatio,
  };
}

export function median(values: readonly number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[mid]! : (sorted[mid - 1]! + sorted[mid]!) / 2;
}

/**
 * D-3(と S-5): 局面ごとに門番を通る本数の分布。**判定(成り立つ / 成り立たない)は出さない。**
 * 2026-09-14 の司令塔の決定で、(お) の前提の判定から「反事実の比較(実戦手の読み筋と最善手の
 * 読み筋)に使える読み筋が、局面ごとに何本あるか」の分布へ読み替えた(計画 §3 D-3)。
 * **0 本・1 本の局面の数は、閾値を置かずに必ず並べる。** 行が 1 つも無ければ median は null。
 */
export function summarizeUsableCounts(
  rows: readonly SurveySearchRow[],
  minPlies: number,
): {
  roots: number;
  histogram: Record<number, number>;
  median: number | null;
  zero: number;
  one: number;
} {
  const counts = okRows(rows).map(
    (row) => row.lines.filter((line) => classifyLine(line, minPlies) === "usable").length,
  );
  const histogram: Record<number, number> = {};
  for (const count of counts) histogram[count] = (histogram[count] ?? 0) + 1;
  const mid = median(counts);
  return {
    roots: counts.length,
    histogram,
    median: mid,
    zero: counts.filter((count) => count === 0).length,
    one: counts.filter((count) => count === 1).length,
  };
}

// ---- 報告の組み立て(計画 §2.2・§3。CLI の中に閉じると試験を置けない ― P-32)----

/** 判断的知識の値。**すべて呼び出し側が渡す**(承認値は計画 §3・§9.1。ここに既定値を置かない)。 */
export interface SurveyReportParams {
  /** D-1 で「長い」とみなす usablePlies(承認値 3) */
  d1MinLength: number;
  /** D-2 の許容(承認値 0.05) */
  tolerance: number;
  /** S-4 で試す控えの候補(計画 §2.2。2〜6) */
  lossThresholds: readonly number[];
}

export interface ConditionReport {
  condition: string;
  mode: SurveyCondition["mode"];
  summary: ConditionSummary;
  boundsByIndex: ReturnType<typeof boundsByIndex>;
  boundLength: {
    pvLength: ReturnType<typeof boundLengthTable>;
    usablePlies: ReturnType<typeof boundLengthTable>;
  };
  lossByThreshold: ReturnType<typeof unboundedLossByThreshold>;
  anomalies: ReturnType<typeof summarizeAnomalies>;
  d1BoundedLongLines: number;
  d2: MinPliesDecision;
  /** D-2 が値を出したときだけ計算する。出さなかったときは、その理由(測っていないことを「成り立たない」にしない) */
  d3:
    | { kind: "computed"; minPlies: number; counts: ReturnType<typeof summarizeUsableCounts> }
    | { kind: "not_computed"; reason: Exclude<MinPliesDecision["kind"], "value"> };
  /** movetime の条件だけ。所要時間の分布(閾値は置かない)。nodes の条件では null */
  elapsedMs: { min: number; median: number | null; max: number } | null;
}

/** 条件ごとに S-1〜S-6・D-1〜D-3 を組み立てる。条件の並びは行に最初に現れた順。 */
export function buildSurveyReport(rows: readonly SurveySearchRow[], params: SurveyReportParams): ConditionReport[] {
  const groups = new Map<string, SurveySearchRow[]>();
  for (const row of rows) {
    const key = conditionKey(row.condition);
    const group = groups.get(key) ?? [];
    group.push(row);
    groups.set(key, group);
  }

  return [...groups.entries()].map(([key, group]) => {
    const lines = linesOf(group);
    const d2 = decideMinPlies(lines, params.tolerance);
    const mode = group[0]!.condition.mode;
    const elapsed = group.map((row) => row.elapsedMs);
    return {
      condition: key,
      mode,
      summary: summarizeConditions(group)[0]!,
      boundsByIndex: boundsByIndex(lines),
      boundLength: { pvLength: boundLengthTable(lines, "pvLength"), usablePlies: boundLengthTable(lines, "usablePlies") },
      lossByThreshold: unboundedLossByThreshold(lines, params.lossThresholds),
      anomalies: summarizeAnomalies(group),
      d1BoundedLongLines: boundedLongLines(lines, params.d1MinLength),
      d2,
      d3:
        d2.kind === "value"
          ? { kind: "computed", minPlies: d2.value, counts: summarizeUsableCounts(group, d2.value) }
          : { kind: "not_computed", reason: d2.kind },
      elapsedMs:
        mode === "movetime" && elapsed.length > 0
          ? { min: Math.min(...elapsed), median: median(elapsed), max: Math.max(...elapsed) }
          : null,
    };
  });
}

/**
 * 段 A の校正に使う対照の行を選ぶ(2026-09-14 の独立監査 A の必須 2。CLI の中で選ぶと試験を置けない)。
 * **対照は `multiPv === 1` の条件**である。条件の並び(`conditions[0]` か `[1]` か)には依存しない。
 * `conditions` のうち `multiPv === 1` の条件が**ちょうど 1 つでなければ例外**(0 個なら対照が無い、
 * 2 個以上ならどれが対照か決まらない。黙ってどちらかを選ばない)。
 * 行が 0 本でも例外にはせず空の配列を返す(測っていないことは `checkCalibration` が null で表す)。
 */
export function controlRowsOf(
  rows: readonly SurveySearchRow[],
  conditions: readonly SurveyCondition[],
): SurveySearchRow[] {
  const controls = conditions.filter((condition) => condition.multiPv === 1);
  if (controls.length !== 1) {
    throw new Error(`MultiPV 1 の条件がちょうど 1 つではありません(${controls.length} 個)。校正の対照を決められません`);
  }
  const controlKey = conditionKey(controls[0]!);
  return rows.filter((row) => conditionKey(row.condition) === controlKey);
}

/** 段 A の対照(MultiPV 1)に当てる既知の値(計画 §1.7・§4・E-12)。**呼び出し側が渡す。** */
export interface CalibrationExpectation {
  /** 既知の標識付きの割合(56 局面に畳んだ値 28/56) */
  boundRate: number;
  /** 許容の幅(± 15 ポイント = 0.15) */
  boundRateTolerance: number;
  /** 標識付きの本の pv.length の上限(2) */
  maxBoundedPvLength: number;
  /** D-2 の式が出すはずの値(E-12。3) */
  minPlies: number;
}

/**
 * 校正の既知の値の出どころ(2026-09-14 の司令塔の決定。計画 §4)。**3 つとも書けないものは校正に使わない。**
 * 評価関数が違えば記録の対象が違う(規則 11.1)ので、どの記録・どのコード・どの評価関数から取った値かを持つ。
 */
export interface CalibrationSource {
  /** 値を数えた記録のフォルダ(リポジトリの根からの相対パス。例: scripts/playtest/records/d0-nnue) */
  recordsDir: string;
  /** その記録の meta 行の gitHead(記録を取ったときのコード) */
  gitHead: string;
  /** その記録をリポジトリにコミットしたコミット(記録そのものの版。U6-T2 で足した) */
  recordsCommit: string;
  /** 評価関数の識別(nn.bin の sha256 など。どこで確かめたかも書く) */
  evaluator: string;
}

/**
 * 段 A の校正の値の元。**記録を観測した数**(標識付きの数と局面数・標識付きの本の最大の長さ・D-2 の式の値)と、
 * その出どころ。幅(± 何ポイント)は観測ではなく選んだ許容なので、ここには入れず `calibrationGate` に別に渡す。
 */
export interface CalibrationBaseline {
  /** 56 局面に畳んだときの標識付きの局面の数 */
  marked: number;
  /** 畳んだ局面の数 */
  total: number;
  maxBoundedPvLength: number;
  minPlies: number;
  /** **null の間は段 A を始めない**(取り直しを忘れた日に止めるため) */
  source: CalibrationSource | null;
}

export type CalibrationGate =
  | { kind: "ready"; expectation: CalibrationExpectation; source: CalibrationSource }
  | { kind: "missing_source"; reason: string };

/**
 * 段 A を始めてよいかを決める(2026-09-14 の司令塔の決定「出どころが明示されていなければ始めない」)。
 * `source` が null、または 3 つの欄のどれかが空文字なら `missing_source`。**CLI はエンジンを起動する前に呼び、
 * `missing_source` なら理由を出して非 0 で止まる。**
 */
export function calibrationGate(baseline: CalibrationBaseline, boundRateTolerance: number): CalibrationGate {
  const { source } = baseline;
  if (source === null || source.recordsDir === "" || source.gitHead === "" || source.recordsCommit === "" || source.evaluator === "") {
    return {
      kind: "missing_source",
      reason:
        "校正の値の出どころ(source: recordsDir・gitHead・recordsCommit・evaluator)が書かれていません。" +
        "段 A は始めません。D0-NNUE の記録から 56 局面に畳んだ値を取り直し、出どころを埋めてください(計画 §4)",
    };
  }
  return {
    kind: "ready",
    source,
    expectation: {
      boundRate: baseline.marked / baseline.total,
      boundRateTolerance,
      maxBoundedPvLength: baseline.maxBoundedPvLength,
      minPlies: baseline.minPlies,
    },
  };
}

/** 校正の値を記録から数えるときの入力(ready 行 1 行ぶん。記録の JSONL をそのまま渡す) */
export interface CalibrationRecordRow {
  kifuId: string;
  ply: number;
  sfen: string;
  /** その行の searchPvs(U6-L)。欄が無ければ undefined */
  searchPvs:
    | ReadonlyArray<Pick<SearchPvObservation, "source" | "multipv" | "scoreCp" | "mate" | "pv" | "lowerbound" | "upperbound">>
    | undefined;
}

export interface ObservedCalibration {
  /** 畳んだ局面のうち、代表の行の focus_baseline の読み筋に標識が付いていた数 */
  marked: number;
  /** 畳んだ局面のうち、代表の行に focus_baseline の読み筋があった数(分母) */
  total: number;
  /** 標識付きの本の pv.length の最大。標識付きが無ければ null */
  maxBoundedPvLength: number | null;
  /** D-2 の式の結果(値が出たかどうかも含めて返す) */
  minPlies: MinPliesDecision;
  /** 代表の行に focus_baseline の読み筋が無かった局面の数(分母に入れない。0 に化けさせない) */
  withoutFocusBaseline: number;
}

/**
 * 校正の値を記録から数える(U6-T2。計画 §1.7 と同じ定義)。
 * 局面は `dedupeRoots` で畳み(代表は最初に現れた行)、代表の行の **focus_baseline**(MultiPV 1 の探索)の
 * 読み筋 1 本を見る。**定数を手で書き写すのではなく、この関数で記録から出した値と定数を試験で突き合わせる。**
 */
export function observeCalibrationBaseline(rows: readonly CalibrationRecordRow[], tolerance: number): ObservedCalibration {
  const byOrigin = new Map(rows.map((row) => [`${row.kifuId}#${row.ply}`, row]));
  const lines: SurveyLine[] = [];
  let withoutFocusBaseline = 0;
  for (const root of dedupeRoots(rows)) {
    const first = root.origins[0]!;
    const row = byOrigin.get(`${first.kifuId}#${first.ply}`)!;
    const observation = row.searchPvs?.find((pv) => pv.source === "focus_baseline");
    if (observation === undefined) {
      withoutFocusBaseline += 1;
      continue;
    }
    // 評価値は校正に使わない(標識と長さだけを見る)。型を満たすために写すだけ
    const score = observation.mate !== null ? { type: "mate" as const, value: observation.mate } : { type: "cp" as const, value: observation.scoreCp ?? 0 };
    lines.push(
      ...toSurveyLines(row.sfen, {
        bestmove: observation.pv[0],
        ponder: undefined,
        infoLines: [],
        lines: [{ multipv: observation.multipv, score, pv: [...observation.pv], lowerbound: observation.lowerbound, upperbound: observation.upperbound }],
      }),
    );
  }
  const bounded = lines.filter((line) => isBounded(line));
  return {
    marked: bounded.length,
    total: lines.length,
    maxBoundedPvLength: bounded.length === 0 ? null : Math.max(...bounded.map((line) => line.pv.length)),
    minPlies: decideMinPlies(lines, tolerance),
    withoutFocusBaseline,
  };
}

export interface CalibrationResult {
  /** 観測できなければ observed も ok も null(測っていないことを「合格」「不合格」にしない) */
  boundRate: { observed: number | null; ok: boolean | null };
  boundedPvLength: { observedMax: number | null; ok: boolean | null };
  minPlies: { observed: MinPliesDecision; ok: boolean };
  /** 3 項目すべてが true のときだけ true。**1 つでも null なら false**(校正できていない) */
  passed: boolean;
}

/**
 * 段 A の対照が既知の値と合うかを見る(規則 11.7 の校正)。**行ごとの一致は見ない**
 * (別々の探索は同じ局面・同じノード数でも 118 組中 0 組しか一致しなかった。計画 §4)。
 */
export function checkCalibration(
  controlRows: readonly SurveySearchRow[],
  tolerance: number,
  expected: CalibrationExpectation,
): CalibrationResult {
  const lines = linesOf(controlRows);
  const bounded = lines.filter((line) => isBounded(line));
  const observedRate = lines.length === 0 ? null : bounded.length / lines.length;
  const observedMax = bounded.length === 0 ? null : Math.max(...bounded.map((line) => line.pv.length));
  const d2 = decideMinPlies(lines, tolerance);

  const boundRate = {
    observed: observedRate,
    ok: observedRate === null ? null : Math.abs(observedRate - expected.boundRate) <= expected.boundRateTolerance,
  };
  const boundedPvLength = {
    observedMax,
    ok: observedMax === null ? null : observedMax <= expected.maxBoundedPvLength,
  };
  const minPlies = { observed: d2, ok: d2.kind === "value" && d2.value === expected.minPlies };
  return {
    boundRate,
    boundedPvLength,
    minPlies,
    passed: boundRate.ok === true && boundedPvLength.ok === true && minPlies.ok,
  };
}

