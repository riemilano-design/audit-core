// D-2b(audit-core/docs/CLAIM_DECOMPOSITION_D2B_PLAN_2026-10-07.md §2(c)(d))。
// 分解器の出力を照合器(`decompositionCompare.ts`)に通し、gold 4 本それぞれと合計を出す経路。
//
// 【このファイルがやること】
// - `runDecomposerOverGold`: gold fixture を順に 1 本ずつ分解器(`decomposeOriginalText`)に渡し、
//   成功した(present:true)ものだけを `compareClaimDecomposition` に通す。費用の累計は gold をまたいで
//   引き継ぐ(`runSlot` と同じ規律 ― 上限に当たったら残りの gold は送らない)。
// - `sumDecompositionCompare`: `compareClaimDecomposition` の結果(複数本)の**件数だけ**を合計する。
//   指標の定義・計算そのもの(`decompositionCompare.ts`)は変えない ― 足すだけ。
//
// 【このファイルが絶対にやらないこと】
// - `decompositionCompare`・`decomposeOriginalText`・`runSlot` の挙動を変えること。
// - 「どちらが正しいか」の判定(集合演算・合計だけ)。

import { decomposeOriginalText, type DecomposeConfig } from "./claimDecomposer.js";
import { compareClaimDecomposition, type DecompositionCompareResult, type GoldFixtureLike } from "./decompositionCompare.js";
import type { SlotDeps, SlotRunResult } from "./seatRun.js";

export interface GoldFixtureFile extends GoldFixtureLike {
  /** gold_01 のようなファイル名から作った id(報告の見出しに使う。照合の計算には使わない)。 */
  id: string;
}

export interface DecomposerGoldRunResult {
  goldId: string;
  slot: SlotRunResult;
  /** `slot.present` のときだけ存在する(空席には比べる相手の実測が無い)。 */
  compare?: DecompositionCompareResult;
}

/**
 * gold を順に 1 本ずつ分解器へ渡す。**gold をまたいで費用を累計**し、上限に当たったら
 * (`slot.capReached`)残りの gold は送らない(送る前に止める ― 上限を越えた費用は発生しない)。
 */
export async function runDecomposerOverGold(
  golds: readonly GoldFixtureFile[],
  instruction: string,
  cfg: DecomposeConfig,
  deps: SlotDeps,
): Promise<DecomposerGoldRunResult[]> {
  const results: DecomposerGoldRunResult[] = [];
  let cumulative = cfg.cumulativeCostUsd ?? 0;
  for (const gold of golds) {
    const slot = await decomposeOriginalText(gold.original_text, instruction, { ...cfg, cumulativeCostUsd: cumulative }, deps);
    cumulative = slot.cumulativeCostUsd;
    const compare = slot.present && slot.llm !== undefined ? compareClaimDecomposition(slot.llm, gold) : undefined;
    results.push({ goldId: gold.id, slot, ...(compare === undefined ? {} : { compare }) });
    if (slot.capReached) break;
  }
  return results;
}

export interface DecompositionTotals {
  spanIntersection: number;
  spanExpectedOnly: number;
  spanActualOnly: number;
  spanMatchedCount: number;
  valueMatchCount: number;
  formMatchCount: number;
  formBreakdown: Record<string, { total: number; matched: number }>;
  uncoveredIntersection: number;
  uncoveredExpectedOnly: number;
  uncoveredActualOnly: number;
}

/** `compareClaimDecomposition` の結果(複数件)を**件数だけ**合計する。空配列には全部 0 の totals を返す。 */
export function sumDecompositionCompare(results: readonly DecompositionCompareResult[]): DecompositionTotals {
  const totals: DecompositionTotals = {
    spanIntersection: 0, spanExpectedOnly: 0, spanActualOnly: 0, spanMatchedCount: 0,
    valueMatchCount: 0, formMatchCount: 0, formBreakdown: {},
    uncoveredIntersection: 0, uncoveredExpectedOnly: 0, uncoveredActualOnly: 0,
  };
  for (const r of results) {
    totals.spanIntersection += r.span.intersection.length;
    totals.spanExpectedOnly += r.span.expectedOnly.length;
    totals.spanActualOnly += r.span.actualOnly.length;
    totals.spanMatchedCount += r.spanMatchedCount;
    totals.valueMatchCount += r.valueMatchCount;
    totals.formMatchCount += r.formMatchCount;
    for (const [form, entry] of Object.entries(r.formBreakdown)) {
      const existing = totals.formBreakdown[form] ?? { total: 0, matched: 0 };
      totals.formBreakdown[form] = { total: existing.total + entry.total, matched: existing.matched + entry.matched };
    }
    totals.uncoveredIntersection += r.uncovered.intersection.length;
    totals.uncoveredExpectedOnly += r.uncovered.expectedOnly.length;
    totals.uncoveredActualOnly += r.uncovered.actualOnly.length;
  }
  return totals;
}
