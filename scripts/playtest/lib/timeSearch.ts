// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.3・§7.5)。「時間を使った手に共通する条件」を
// 機械に探索させる段の純粋関数。**測る段だけ**(CLI は scripts/playtest/timeSearch.ts、PDF は
// report-pdf/render_time_cause.py の追加ページ)。
//
// 【このファイルがやること】
// - `lib/timeFeatures.ts` の `MoveFeatureRow[]`(発見用・検証用)を受け取り、条件(列 = 値)の単独・2 条件・
//   3 条件の組を全列挙する(`SEARCH_COLUMNS` に無い列・null の値は条件に使わない ― 計画 §7.3 の 1.)。
// - 各組の該当する手の数 n と長考率 p を数え、全体の長考率 p0 と比べて採用候補(n ≥ `FINDING_VALUES.minPairs`
//   かつ p ≥ p0 × `FINDING_VALUES.ratio`)を選ぶ(計画 §7.3 の 2.)。
// - 採用候補を検証用の表でも数え直し、n ≥ `TIME_SEARCH_VALUES.validateMinN` かつ p ≥ p0(検証用) ×
//   `FINDING_VALUES.ratio` なら「再現した」とする(計画 §7.3 の 3.)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンを起動すること(CLI の役目)
// - 決定木・回帰などのモデルを使うこと(条件の列挙と分数だけ ― 計画 §7.6)
// - 4 条件以上の組を作ること
// - 「原因」「傾向」と呼ぶこと(レベル 1 は「一緒に起きている条件」)
//
// 【判断的知識】`TIME_SEARCH_VALUES.validateMinN`(= 10)は計画 §7.3 で確定した、この計画で唯一の新しい値
// (「14 局では 20 に届かないため」。計画の文言そのまま)。それ以外は `FINDING_VALUES`(minPairs・ratio)の使い回し。

import { FINDING_VALUES } from "./reportData.js";
import type { MoveFeatureRow } from "./timeFeatures.js";

/** この計画で唯一の新しい値(計画 §7.3 の 3.)。1 か所にまとめる(CLAUDE.md 4 番)。 */
export const TIME_SEARCH_VALUES = { validateMinN: 10 } as const;

/**
 * 条件に使う列(実装担当の判断)。`kifuId`・`group`・`gameNo`・`kifPly` は識別子であって特徴ではない。
 * `spentSec`・`spentBucket`・`longThink` は目的変数そのもの、またはその生の形の離散化であり、
 * `spentBucket`(境目 9〈秒〉超)は `longThink`(10 秒以上)とほぼ同義になるため、条件に使うと
 * 「長考は長考と一緒に起きている」という自明な組を「発見」してしまう(トートロジー)。この 3 列 + 識別子
 * 4 列を除いた残りを探索の対象にする。
 */
export const SEARCH_COLUMNS = [
  "prevOwnSpentBucket",
  "prev3SumBucket",
  "prev5SumBucket",
  "afterLongThink",
  "remainingBucket",
  "phase",
  "evalBand",
  "evalChangePrev",
  "inCheck",
  "fork",
  "top1Side",
  "actualSide",
  "lossBand",
  "inTop5",
  "actualCapture",
  "actualDrop",
  "actualGivesCheck",
  "actualSacrifice",
  "actualRetreat",
  "top1Capture",
  "top1Drop",
  "top1GivesCheck",
  "top1Sacrifice",
  "top1Retreat",
  "oppPrevCapture",
  "oppPrevDrop",
  "oppPrevGivesCheck",
  "oppPrevPromotion",
  "ownRookMoved",
  "oppRookMoved",
] as const satisfies readonly (keyof MoveFeatureRow)[];

export type SearchColumn = (typeof SEARCH_COLUMNS)[number];
export type ConditionValue = Exclude<MoveFeatureRow[SearchColumn], null>;

export interface ConditionTerm {
  column: SearchColumn;
  value: ConditionValue;
}

/** 条件(列 = 値 の組。長さ 1〜3、列は重複しない)。 */
export type Condition = readonly ConditionTerm[];

export interface ConditionStats {
  /** 該当する手の数(分母)。 */
  n: number;
  /** そのうち長考(`longThink`)だった手の数。 */
  longThink: number;
  /** n が 0 なら 0(呼び出し側は n を見て「該当なし」を扱う)。 */
  p: number;
}

export interface SearchCandidate {
  depth: 1 | 2 | 3;
  condition: Condition;
  discover: ConditionStats;
}

export interface ReproducedCandidate extends SearchCandidate {
  validate: ConditionStats;
}

export interface DepthSummary {
  depth: 1 | 2 | 3;
  /** その深さで実際に手に出会った組の数(列の値の組み合わせのうち、n ≥ 1 だったもの)。 */
  tried: number;
  adopted: number;
  reproduced: number;
}

export interface SearchResult {
  discover: { moves: number; longThinkRate: number };
  validate: { moves: number; longThinkRate: number };
  depths: DepthSummary[];
  /** 採用候補で、検証用でも再現した組(条件・発見用の n/p・検証用の n/p)。 */
  reproduced: ReproducedCandidate[];
  /** 採用候補で、検証用では再現しなかった組(条件と、発見用・検証用の数)。 */
  notReproduced: ReproducedCandidate[];
}

function valueOfColumn(row: MoveFeatureRow, column: SearchColumn): ConditionValue | null {
  return row[column] as ConditionValue | null;
}

function conditionKeyOf(terms: readonly ConditionTerm[]): string {
  return terms.map((t) => `${t.column}=${String(t.value)}`).join("&");
}

/** `rows` のうち `condition` の全項目に一致する手だけで n・長考の数・p を数える(null の列は一致しない ― 計画の「null の列は条件に使わない」)。 */
export function statsOf(rows: readonly MoveFeatureRow[], condition: Condition): ConditionStats {
  let n = 0;
  let longThink = 0;
  for (const row of rows) {
    let matches = true;
    for (const term of condition) {
      if (valueOfColumn(row, term.column) !== term.value) {
        matches = false;
        break;
      }
    }
    if (!matches) continue;
    n += 1;
    if (row.longThink) longThink += 1;
  }
  return { n, longThink, p: n === 0 ? 0 : longThink / n };
}

/** `columns` から `k` 個を選ぶ組み合わせ(列の並び順のまま。重複なし)。 */
function combinationsOf<T>(items: readonly T[], k: number): T[][] {
  if (k === 0) return [[]];
  if (items.length < k) return [];
  const [head, ...tail] = items;
  const withHead = combinationsOf(tail, k - 1).map((rest) => [head!, ...rest]);
  const withoutHead = combinationsOf(tail, k);
  return [...withHead, ...withoutHead];
}

/**
 * `depth` 個の列を選ぶすべての組み合わせについて、`rows` に実際に出た(n ≥ 1 の)値の組を集める
 * (実装担当の判断: 列の値域どうしの直積〈n = 0 の組も含む〉ではなく、実際に手に出会った組だけを数える
 * ― 「試した組」を「実際に起きた条件の組」として扱う。組み合わせ爆発も避けられる)。
 */
export function enumerateCandidatesOf(rows: readonly MoveFeatureRow[], depth: 1 | 2 | 3): SearchCandidate[] {
  const candidates: SearchCandidate[] = [];
  for (const columns of combinationsOf(SEARCH_COLUMNS, depth)) {
    const groups = new Map<string, { condition: ConditionTerm[]; n: number; longThink: number }>();
    for (const row of rows) {
      const terms: ConditionTerm[] = [];
      let ok = true;
      for (const column of columns) {
        const value = valueOfColumn(row, column);
        if (value === null) {
          ok = false;
          break;
        }
        terms.push({ column, value });
      }
      if (!ok) continue;
      const key = conditionKeyOf(terms);
      let group = groups.get(key);
      if (group === undefined) {
        group = { condition: terms, n: 0, longThink: 0 };
        groups.set(key, group);
      }
      group.n += 1;
      if (row.longThink) group.longThink += 1;
    }
    for (const group of groups.values()) {
      candidates.push({ depth, condition: group.condition, discover: { n: group.n, longThink: group.longThink, p: group.n === 0 ? 0 : group.longThink / group.n } });
    }
  }
  return candidates;
}

/**
 * 採用候補か(n ≥ minPairs かつ p ≥ p0 × ratio)。割り算ではなく掛け算で比べる(浮動小数点の丸め誤差を避ける
 * ― `lib/reportData.ts` の `timeSpentFinding` と同じ考え方)。`baseMoves` が 0(材料が無い)なら常に false。
 */
export function isAdoptedOf(stats: ConditionStats, baseMoves: number, baseLongThink: number): boolean {
  if (baseMoves === 0) return false;
  return stats.n >= FINDING_VALUES.minPairs && stats.longThink * baseMoves >= baseLongThink * FINDING_VALUES.ratio * stats.n;
}

/** 検証用で「再現した」か(n ≥ validateMinN かつ p ≥ p0(検証用) × ratio。ratio は発見用と同じ値を使い回す)。 */
export function isReproducedOf(stats: ConditionStats, baseMoves: number, baseLongThink: number): boolean {
  if (baseMoves === 0) return false;
  return stats.n >= TIME_SEARCH_VALUES.validateMinN && stats.longThink * baseMoves >= baseLongThink * FINDING_VALUES.ratio * stats.n;
}

/** 発見用・検証用の表から、深さ 1〜3 の探索の結果を組む(計画「作るもの」2.)。 */
export function searchOf(discoverRows: readonly MoveFeatureRow[], validateRows: readonly MoveFeatureRow[]): SearchResult {
  const discoverMoves = discoverRows.length;
  const discoverLongThink = discoverRows.filter((row) => row.longThink).length;
  const validateMoves = validateRows.length;
  const validateLongThink = validateRows.filter((row) => row.longThink).length;

  const depths: DepthSummary[] = [];
  const reproduced: ReproducedCandidate[] = [];
  const notReproduced: ReproducedCandidate[] = [];

  for (const depth of [1, 2, 3] as const) {
    const candidates = enumerateCandidatesOf(discoverRows, depth);
    const adopted = candidates.filter((candidate) => isAdoptedOf(candidate.discover, discoverMoves, discoverLongThink));
    let reproducedCount = 0;
    for (const candidate of adopted) {
      const validate = statsOf(validateRows, candidate.condition);
      const entry: ReproducedCandidate = { ...candidate, validate };
      if (isReproducedOf(validate, validateMoves, validateLongThink)) {
        reproducedCount += 1;
        reproduced.push(entry);
      } else {
        notReproduced.push(entry);
      }
    }
    depths.push({ depth, tried: candidates.length, adopted: adopted.length, reproduced: reproducedCount });
  }

  return {
    discover: { moves: discoverMoves, longThinkRate: discoverMoves === 0 ? 0 : discoverLongThink / discoverMoves },
    validate: { moves: validateMoves, longThinkRate: validateMoves === 0 ? 0 : validateLongThink / validateMoves },
    depths,
    reproduced,
    notReproduced,
  };
}
