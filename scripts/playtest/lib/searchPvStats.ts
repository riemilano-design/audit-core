// STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md 3.5)。
// 記録(JSONL)の ready 行に載った読み筋(searchPvs)を数えるだけの純粋関数。
//
// 【このファイルがやること】
// - 探索の本数を source 別に数える
// - 読み筋の長さの分布を数える(0 / 1 / 2 / 3 / 4〜9 / 10以上)
// - lowerbound が立った探索・pv が空の探索・multipv が 2 以上の探索を数える
//
// 【このファイルが絶対にやらないこと】
// - 将棋の判断・新しい閾値・文言。「何手未満を読み筋として使わないか」の門番は
//   使う側(U6-M)が持つのであって、ここでは持たない(計画書 1.2)。
// - 「異常」の判定。ここで数えるのは観測の集計であり、不変条件ではない
//   (docs/AGENT_PROTOCOL.md 11.、lib/denominators.ts と同じ立て方)。
//
// 【3つの状態を別々に数える】
// - 欄が無い(undefined) … U6-L より前の記録 → rowsWithoutField
// - null … 本番の解析そのものが失敗した(測れなかった) → rowsFailed
// - [] … 測ったが1本も取れなかった → rowsWithEmptyField
// **一つの値に二つの意味を持たせない**ので、数える側も3つを混ぜない
// (2026-09-13 の独立監査の指摘、必須3)。

import type { SearchPvObservation, SearchPvSource } from "../../../apps/server/src/analysis/searchPv.js";
import type { RecordLine } from "../invariants/types.js";

/** 長さの分布の区切り(観測の都合の区切りであり、閾値ではない)。 */
export type PvLengthBucket = "0" | "1" | "2" | "3" | "4-9" | "10+";

export const PV_LENGTH_BUCKETS: readonly PvLengthBucket[] = ["0", "1", "2", "3", "4-9", "10+"];

export function pvLengthBucket(length: number): PvLengthBucket {
  if (length <= 0) return "0";
  if (length === 1) return "1";
  if (length === 2) return "2";
  if (length === 3) return "3";
  if (length <= 9) return "4-9";
  return "10+";
}

export interface SearchPvStats {
  /** searchPvs の欄がある ready 行の数。 */
  rowsWithField: number;
  /** searchPvs の欄が無い ready 行の数(U6-L より前に取った記録)。 */
  rowsWithoutField: number;
  /** searchPvs が null だった ready 行の数(本番の解析が失敗し、**測れなかった**)。 */
  rowsFailed: number;
  /** 欄はあるが空配列だった ready 行の数(測ったが1本も取れなかった)。 */
  rowsWithEmptyField: number;
  /** 観測(探索1本)の総数。 */
  observations: number;
  /** source 別の本数。 */
  bySource: Record<SearchPvSource, number>;
  /** 読み筋の長さの分布。 */
  byLength: Record<PvLengthBucket, number>;
  /** lowerbound が立っていた本数。 */
  lowerbound: number;
  /** upperbound が立っていた本数。 */
  upperbound: number;
  /** pv が空だった本数(計画書 2.2 の上書きが起きたかどうかの材料)。 */
  emptyPv: number;
  /** multipv が 2 以上だった本数。**0 でなければ計画書 2.1 の読みが誤り**。 */
  multipvAtLeast2: number;
}

function emptyStats(): SearchPvStats {
  return {
    rowsWithField: 0,
    rowsWithoutField: 0,
    rowsFailed: 0,
    rowsWithEmptyField: 0,
    observations: 0,
    bySource: {
      focus_baseline: 0,
      focus_after_pass: 0,
      candidate_baseline: 0,
      candidate_after_move: 0,
    },
    byLength: { "0": 0, "1": 0, "2": 0, "3": 0, "4-9": 0, "10+": 0 },
    lowerbound: 0,
    upperbound: 0,
    emptyPv: 0,
    multipvAtLeast2: 0,
  };
}

function countObservation(stats: SearchPvStats, observation: SearchPvObservation): void {
  stats.observations += 1;
  stats.bySource[observation.source] += 1;
  stats.byLength[pvLengthBucket(observation.pv.length)] += 1;
  if (observation.lowerbound) stats.lowerbound += 1;
  if (observation.upperbound) stats.upperbound += 1;
  if (observation.pv.length === 0) stats.emptyPv += 1;
  if (observation.multipv >= 2) stats.multipvAtLeast2 += 1;
}

/** phase:"ready" の record 行だけを数える(immediate 行は探索していないため対象外)。 */
export function countSearchPvs(records: RecordLine[]): SearchPvStats {
  const stats = emptyStats();
  for (const record of records) {
    if (record.phase !== "ready") continue;
    const observations = record.searchPvs;
    if (observations === undefined) {
      stats.rowsWithoutField += 1;
      continue;
    }
    if (observations === null) {
      // 測れなかった(解析の失敗)。0本と混ぜない。
      stats.rowsFailed += 1;
      continue;
    }
    stats.rowsWithField += 1;
    if (observations.length === 0) stats.rowsWithEmptyField += 1;
    for (const observation of observations) countObservation(stats, observation);
  }
  return stats;
}

export interface SearchPvStatsRow {
  label: string;
  stats: SearchPvStats;
}

export interface SearchPvStatsInput {
  kifuId: string;
  records: RecordLine[];
}

export interface SearchPvStatsReport {
  perInput: SearchPvStatsRow[];
  total: SearchPvStats;
}

export function buildSearchPvStatsReport(inputs: SearchPvStatsInput[]): SearchPvStatsReport {
  const perInput = inputs.map((input) => ({ label: input.kifuId, stats: countSearchPvs(input.records) }));
  const total = countSearchPvs(inputs.flatMap((input) => input.records));
  return { perInput, total };
}
