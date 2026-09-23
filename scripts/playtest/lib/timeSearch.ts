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
// 【STEP TIME-CAUSE-3(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §9.1)が足したこと】
// - `ConditionStats` に崩れの分母・崩れ・崩れ率(`collapseCounted`・`collapsed`・`q`)を足した(2.)。
// - 各条件に、発見用・検証用の両方で判定して一致したときだけ付く `kind`(A = 時間だけ/B = 時間 + 崩れ/
//   C = 時間でない + 崩れ/それ以外は null)を足した(3.)。C は「崩れを目的変数にした 2 回目の探索」
//   (`collapseSearch`)からしか出ない(長考の採用候補は時間で選んでいるため)。
// - 部品(単独条件)ごとに、3 つのアウトカム(長考・時間 + 崩れ・速く指して崩れ)を「単独で線を越えるか」
//   「組でだけ再現した組に入るか」で `explains` に分類する共通因子の表(`factorSummaryOf`、4.)。
// - 偶然でも残る数の目安(`chanceReproduced`。二項分布の裾、5.)。
//
// 【このファイルが絶対にやらないこと】
// - ファイルの読み書き・エンジンを起動すること(CLI の役目)
// - 決定木・回帰などのモデルを使うこと(条件の列挙と分数だけ ― 計画 §7.6・§9.3)
// - 4 条件以上の組を作ること
// - 「原因」「傾向」「型」と呼ぶこと(レベル 1 は「一緒に起きている条件」。`kind` の値〈A/B/C〉はコードの識別子
//   であって、文言に「型」を使ってよいという意味ではない ― PDF 側〈render_time_cause.py〉の役目)
//
// 【判断的知識】`TIME_SEARCH_VALUES.validateMinN`(= 10)は計画 §7.3 で確定した、この計画で唯一の新しい値
// (「14 局では 20 に届かないため」。計画の文言そのまま)。それ以外は `FINDING_VALUES`(minPairs・ratio)の使い回し。
// 崩れの採用候補・再現の線(`isCollapseAdoptedOf`・`isCollapseReproducedOf`)も同じ値を使い回す(計画 §9.1 の 3.)。

import { FINDING_VALUES } from "./reportData.js";
import type { MoveFeatureRow } from "./timeFeatures.js";

/** この計画で唯一の新しい値(計画 §7.3 の 3.)。1 か所にまとめる(CLAUDE.md 4 番)。 */
export const TIME_SEARCH_VALUES = { validateMinN: 10 } as const;

/**
 * 条件に使う列(実装担当の判断)。`kifuId`・`group`・`gameNo`・`kifPly` は識別子であって特徴ではない。
 * `spentSec`・`spentBucket`・`longThink` は目的変数そのもの、またはその生の形の離散化であり、
 * `spentBucket`(境目 9〈秒〉超)は `longThink`(10 秒以上)とほぼ同義になるため、条件に使うと
 * 「長考は長考と一緒に起きている」という自明な組を「発見」してしまう(トートロジー)。この 3 列 + 識別子
 * 4 列を除いた残りを探索の対象にする。`collapse`(STEP TIME-CAUSE-3 で足した列)も同じ理由で除く ―
 * 崩れの探索(2 回目の探索)の目的変数そのものであり、条件に使うと同じトートロジーになる(実装担当の判断)。
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
  /** STEP TIME-CAUSE-3(計画 §9.1 の 2.): 崩れの分母(`collapse` が null でない手の数)。 */
  collapseCounted: number;
  /** そのうち崩れた(`collapse === true`)手の数。 */
  collapsed: number;
  /** `collapsed / collapseCounted`。`collapseCounted` が 0 なら null(0 除算にしない。p とは既定が異なる)。 */
  q: number | null;
}

/** STEP TIME-CAUSE-3(計画 §9.1 の 3.)。A = 時間だけ/B = 時間 + 崩れ/C = 時間でない + 崩れ/それ以外は null。 */
export type Kind = "A" | "B" | "C" | null;

export interface SearchCandidate {
  depth: 1 | 2 | 3;
  condition: Condition;
  discover: ConditionStats;
}

export interface ReproducedCandidate extends SearchCandidate {
  validate: ConditionStats;
  /** STEP TIME-CAUSE-3(計画 §9.1 の 3.)。発見用・検証用の判定が一致したときだけ A/B/C、それ以外は null。 */
  kind: Kind;
}

export interface DepthSummary {
  depth: 1 | 2 | 3;
  /** その深さで実際に手に出会った組の数(列の値の組み合わせのうち、n ≥ 1 だったもの)。 */
  tried: number;
  adopted: number;
  reproduced: number;
  /**
   * STEP TIME-CAUSE-3(計画 §9.1 の 5.)。偶然でも残る数の目安(採用候補の数 × 二項の裾)。
   * 裾は検証用の基準率(p0 または q0)のもとで、n = `TIME_SEARCH_VALUES.validateMinN` の手が
   * 線(基準率 × `FINDING_VALUES.ratio`)を越える確率(`chanceLineProbabilityOf`)。
   */
  chanceReproduced: number;
}

/** 発見用・検証用それぞれの全体の数(計画 §9.1 の 2.: 全体の q0 も両組で)。 */
export interface SearchRoleSummary {
  moves: number;
  longThinkRate: number;
  collapseCounted: number;
  collapsed: number;
  /** `collapsed / collapseCounted`。`collapseCounted` が 0 なら null。 */
  collapseRate: number | null;
}

/** STEP TIME-CAUSE-3(計画 §9.1 の 4.)。「単独で越える」「組でだけ再現した組に入る」のどちらでもなければ null。 */
export type ExplainLevel = "single" | "combo" | null;

export interface FactorDepthCounts {
  depth1: number;
  depth2: number;
  depth3: number;
  total: number;
}

/**
 * STEP TIME-CAUSE-3(計画 §9.1 の 4.、2026-09-25 の人間の修正)。部品(単独条件)ごとの共通因子の表の 1 行。
 * `single` は部品 1 つだけの条件の数(採用候補でなくても出す)。`explains` は「よく登場するか」ではなく
 * 「どのアウトカムを説明する部品か」を機械で分類したもの(登場数だけでは共通因子と呼ばない ― 人間の修正)。
 */
export interface FactorEntry {
  column: SearchColumn;
  value: ConditionValue;
  /** 長考の探索(§9.1 の 3. の元の探索)で再現した組に入る数(深さ別・合計)。 */
  inReproduced: FactorDepthCounts;
  single: { discover: ConditionStats; validate: ConditionStats };
  /** 部品 1 つで時間の線を越えるか(発見用・検証用それぞれ)。 */
  singleOverLine: { discover: boolean; validate: boolean };
  /** この部品を含む、長考の探索で再現した組のうち B 型(時間 + 崩れ)の数。 */
  inKindB: number;
  /** 崩れを目的変数にした探索で再現した組に入る数(深さ別・合計)。 */
  inCollapseReproduced: FactorDepthCounts;
  /** この部品を含む、崩れの探索で再現した組のうち C 型(速く指して崩れ)の数。 */
  inKindC: number;
  /**
   * 3 つのアウトカムそれぞれについて、この部品が「単独で線を越える」(single)/「単独では越えないが、
   * そのアウトカムの再現した組に組み合わせとして 1 つ以上入る」(combo)/どちらでもない(null)。
   */
  explains: { longThink: ExplainLevel; timeAndCollapse: ExplainLevel; quickCollapse: ExplainLevel };
}

export interface SearchResult {
  discover: SearchRoleSummary;
  validate: SearchRoleSummary;
  depths: DepthSummary[];
  /** 採用候補で、検証用でも再現した組(条件・発見用の n/p・検証用の n/p)。長考を目的変数にした探索。 */
  reproduced: ReproducedCandidate[];
  /** 採用候補で、検証用では再現しなかった組(条件と、発見用・検証用の数)。 */
  notReproduced: ReproducedCandidate[];
  /**
   * STEP TIME-CAUSE-3(計画 §9.1 の 3.)。崩れを目的変数にした 2 回目の探索(長考の探索と同じ列挙・同じ線、
   * 目的変数だけ `longThink` → `collapse` に替えたもの)。
   */
  collapseSearch: { depths: DepthSummary[]; reproduced: ReproducedCandidate[]; notReproduced: ReproducedCandidate[] };
  /** STEP TIME-CAUSE-3(計画 §9.1 の 4.)。部品ごとの共通因子の表(並びは `factorSummaryOf` を見る)。 */
  factors: FactorEntry[];
}

function valueOfColumn(row: MoveFeatureRow, column: SearchColumn): ConditionValue | null {
  return row[column] as ConditionValue | null;
}

function conditionKeyOf(terms: readonly ConditionTerm[]): string {
  return terms.map((t) => `${t.column}=${String(t.value)}`).join("&");
}

/**
 * `rows` のうち `condition` の全項目に一致する手だけで n・長考の数・p・崩れの分母・崩れ・q を数える
 * (null の列は一致しない ― 計画の「null の列は条件に使わない」。`collapse` が null の手は崩れの分母に
 * 入れない ― STEP TIME-CAUSE-3 §9.1 の 1.「分母に入らない」と同じ扱い)。
 */
export function statsOf(rows: readonly MoveFeatureRow[], condition: Condition): ConditionStats {
  let n = 0;
  let longThink = 0;
  let collapseCounted = 0;
  let collapsed = 0;
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
    if (row.collapse !== null) {
      collapseCounted += 1;
      if (row.collapse) collapsed += 1;
    }
  }
  return { n, longThink, p: n === 0 ? 0 : longThink / n, collapseCounted, collapsed, q: collapseCounted === 0 ? null : collapsed / collapseCounted };
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
    const groups = new Map<string, { condition: ConditionTerm[]; n: number; longThink: number; collapseCounted: number; collapsed: number }>();
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
        group = { condition: terms, n: 0, longThink: 0, collapseCounted: 0, collapsed: 0 };
        groups.set(key, group);
      }
      group.n += 1;
      if (row.longThink) group.longThink += 1;
      if (row.collapse !== null) {
        group.collapseCounted += 1;
        if (row.collapse) group.collapsed += 1;
      }
    }
    for (const group of groups.values()) {
      candidates.push({
        depth,
        condition: group.condition,
        discover: {
          n: group.n,
          longThink: group.longThink,
          p: group.n === 0 ? 0 : group.longThink / group.n,
          collapseCounted: group.collapseCounted,
          collapsed: group.collapsed,
          q: group.collapseCounted === 0 ? null : group.collapsed / group.collapseCounted,
        },
      });
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

/**
 * STEP TIME-CAUSE-3(計画 §9.1 の 3.)。崩れの採用候補か(`collapseCounted` ≥ minPairs かつ
 * q ≥ q0 × ratio)。`isAdoptedOf` の崩れ版(同じ値の使い回し、掛け算で比べる考え方も同じ)。
 */
export function isCollapseAdoptedOf(stats: ConditionStats, baseCollapseCounted: number, baseCollapsed: number): boolean {
  if (baseCollapseCounted === 0) return false;
  return (
    stats.collapseCounted >= FINDING_VALUES.minPairs && stats.collapsed * baseCollapseCounted >= baseCollapsed * FINDING_VALUES.ratio * stats.collapseCounted
  );
}

/** STEP TIME-CAUSE-3(計画 §9.1 の 3.)。崩れの再現か(`collapseCounted` ≥ validateMinN かつ q ≥ q0(検証用) × ratio)。 */
export function isCollapseReproducedOf(stats: ConditionStats, baseCollapseCounted: number, baseCollapsed: number): boolean {
  if (baseCollapseCounted === 0) return false;
  return (
    stats.collapseCounted >= TIME_SEARCH_VALUES.validateMinN &&
    stats.collapsed * baseCollapseCounted >= baseCollapsed * FINDING_VALUES.ratio * stats.collapseCounted
  );
}

/** A/B/C の判定(片方の役割ぶん)。時間・崩れのどちらも満たせば B、時間だけなら A、崩れだけなら C、どちらも満たさなければ null。 */
function kindFrom(time: boolean, collapse: boolean): Kind {
  if (time && collapse) return "B";
  if (time) return "A";
  if (collapse) return "C";
  return null;
}

/** 発見用・検証用それぞれの全体の数(cross-multiplication に使う生の件数。`SearchRoleSummary` の元)。 */
interface RoleBase {
  moves: number;
  longThink: number;
  collapseCounted: number;
  collapsed: number;
}

function roleBaseOf(rows: readonly MoveFeatureRow[]): RoleBase {
  let moves = 0;
  let longThink = 0;
  let collapseCounted = 0;
  let collapsed = 0;
  for (const row of rows) {
    moves += 1;
    if (row.longThink) longThink += 1;
    if (row.collapse !== null) {
      collapseCounted += 1;
      if (row.collapse) collapsed += 1;
    }
  }
  return { moves, longThink, collapseCounted, collapsed };
}

function roleSummaryOf(base: RoleBase): SearchRoleSummary {
  return {
    moves: base.moves,
    longThinkRate: base.moves === 0 ? 0 : base.longThink / base.moves,
    collapseCounted: base.collapseCounted,
    collapsed: base.collapsed,
    collapseRate: base.collapseCounted === 0 ? null : base.collapsed / base.collapseCounted,
  };
}

/**
 * STEP TIME-CAUSE-3(計画 §9.1 の 3.)。ある条件の kind(A/B/C/null)を、発見用・検証用それぞれで
 * 「時間」「崩れ」を判定し、両方が一致したときだけ確定する(一致しなければ null)。
 */
export function kindOf(discover: ConditionStats, validate: ConditionStats, discoverBase: RoleBase, validateBase: RoleBase): Kind {
  const discoverKind = kindFrom(
    isAdoptedOf(discover, discoverBase.moves, discoverBase.longThink),
    isCollapseAdoptedOf(discover, discoverBase.collapseCounted, discoverBase.collapsed),
  );
  const validateKind = kindFrom(
    isReproducedOf(validate, validateBase.moves, validateBase.longThink),
    isCollapseReproducedOf(validate, validateBase.collapseCounted, validateBase.collapsed),
  );
  return discoverKind === validateKind ? discoverKind : null;
}

/** `n` 個から `k` 個を選ぶ場合の数(小さい `n` だけを想定。二項係数)。 */
function nCkOf(n: number, k: number): number {
  if (k < 0 || k > n) return 0;
  let result = 1;
  for (let i = 0; i < k; i++) result = (result * (n - i)) / (i + 1);
  return result;
}

/**
 * STEP TIME-CAUSE-3(計画 §9.1 の 5.、§8.3 の計算を道具にしたもの)。二項分布 Binomial(n, p0) で、
 * 線(p0 × ratio 以上)を越える確率(裾)。越えるために要る回数 `k = ceil(p0 × ratio × n)` 以上になる確率。
 */
export function chanceLineProbabilityOf(p0: number, n: number, ratio: number): number {
  const k = Math.ceil(p0 * ratio * n);
  let probability = 0;
  for (let i = Math.max(0, k); i <= n; i++) {
    probability += nCkOf(n, i) * p0 ** i * (1 - p0) ** (n - i);
  }
  return probability;
}

/** 目的変数(長考 or 崩れ)ごとの、採用候補・再現の判定と「検証用の基準率」の 3 点セット。 */
interface Objective {
  isAdopted: (stats: ConditionStats, base: RoleBase) => boolean;
  isReproduced: (stats: ConditionStats, base: RoleBase) => boolean;
  rateOf: (base: RoleBase) => number;
}

const TIME_OBJECTIVE: Objective = {
  isAdopted: (stats, base) => isAdoptedOf(stats, base.moves, base.longThink),
  isReproduced: (stats, base) => isReproducedOf(stats, base.moves, base.longThink),
  rateOf: (base) => (base.moves === 0 ? 0 : base.longThink / base.moves),
};

const COLLAPSE_OBJECTIVE: Objective = {
  isAdopted: (stats, base) => isCollapseAdoptedOf(stats, base.collapseCounted, base.collapsed),
  isReproduced: (stats, base) => isCollapseReproducedOf(stats, base.collapseCounted, base.collapsed),
  rateOf: (base) => (base.collapseCounted === 0 ? 0 : base.collapsed / base.collapseCounted),
};

interface RunSearchResult {
  depths: DepthSummary[];
  reproduced: ReproducedCandidate[];
  notReproduced: ReproducedCandidate[];
}

/**
 * 深さ 1〜3 の探索を 1 回ぶん(目的変数 `objective` で採用候補・再現を判定する。`kind` は目的変数によらず
 * 常に「時間」「崩れ」の両方で計算する ― STEP TIME-CAUSE-3 §9.1 の 3.「同じ関数で目的変数を替えて一般化」)。
 */
function runSearchOf(
  discoverRows: readonly MoveFeatureRow[],
  validateRows: readonly MoveFeatureRow[],
  discoverBase: RoleBase,
  validateBase: RoleBase,
  objective: Objective,
): RunSearchResult {
  const depths: DepthSummary[] = [];
  const reproduced: ReproducedCandidate[] = [];
  const notReproduced: ReproducedCandidate[] = [];
  const chanceProbability = chanceLineProbabilityOf(objective.rateOf(validateBase), TIME_SEARCH_VALUES.validateMinN, FINDING_VALUES.ratio);

  for (const depth of [1, 2, 3] as const) {
    const candidates = enumerateCandidatesOf(discoverRows, depth);
    const adopted = candidates.filter((candidate) => objective.isAdopted(candidate.discover, discoverBase));
    let reproducedCount = 0;
    for (const candidate of adopted) {
      const validate = statsOf(validateRows, candidate.condition);
      const kind = kindOf(candidate.discover, validate, discoverBase, validateBase);
      const entry: ReproducedCandidate = { ...candidate, validate, kind };
      if (objective.isReproduced(validate, validateBase)) {
        reproducedCount += 1;
        reproduced.push(entry);
      } else {
        notReproduced.push(entry);
      }
    }
    depths.push({ depth, tried: candidates.length, adopted: adopted.length, reproduced: reproducedCount, chanceReproduced: adopted.length * chanceProbability });
  }

  return { depths, reproduced, notReproduced };
}

function containsTerm(condition: Condition, term: ConditionTerm): boolean {
  return condition.some((t) => t.column === term.column && t.value === term.value);
}

function depthCountsOf(list: readonly ReproducedCandidate[], term: ConditionTerm): FactorDepthCounts {
  let depth1 = 0;
  let depth2 = 0;
  let depth3 = 0;
  for (const candidate of list) {
    if (!containsTerm(candidate.condition, term)) continue;
    if (candidate.depth === 1) depth1 += 1;
    else if (candidate.depth === 2) depth2 += 1;
    else depth3 += 1;
  }
  return { depth1, depth2, depth3, total: depth1 + depth2 + depth3 };
}

/**
 * STEP TIME-CAUSE-3(計画 §9.1 の 4.、2026-09-25 の人間の修正)。部品(単独条件)ごとの共通因子の表。
 * 並びは `explains` が "single" の数 → "combo" の数 → `inReproduced.total` の多い順(人間の指示どおり)。
 */
export function factorSummaryOf(
  discoverRows: readonly MoveFeatureRow[],
  validateRows: readonly MoveFeatureRow[],
  discoverBase: RoleBase,
  validateBase: RoleBase,
  timeReproduced: readonly ReproducedCandidate[],
  collapseReproduced: readonly ReproducedCandidate[],
): FactorEntry[] {
  const singles = enumerateCandidatesOf(discoverRows, 1);
  const entries: FactorEntry[] = singles.map((single) => {
    const term = single.condition[0]!;
    const validateStats = statsOf(validateRows, single.condition);
    const singleOverLine = {
      discover: isAdoptedOf(single.discover, discoverBase.moves, discoverBase.longThink),
      validate: isReproducedOf(validateStats, validateBase.moves, validateBase.longThink),
    };
    const singleKind = kindOf(single.discover, validateStats, discoverBase, validateBase);
    const inReproduced = depthCountsOf(timeReproduced, term);
    const inKindB = timeReproduced.filter((c) => c.kind === "B" && containsTerm(c.condition, term)).length;
    const inCollapseReproduced = depthCountsOf(collapseReproduced, term);
    const inKindC = collapseReproduced.filter((c) => c.kind === "C" && containsTerm(c.condition, term)).length;

    const explains: FactorEntry["explains"] = {
      longThink: singleOverLine.discover && singleOverLine.validate ? "single" : inReproduced.total > 0 ? "combo" : null,
      timeAndCollapse: singleKind === "B" ? "single" : inKindB > 0 ? "combo" : null,
      quickCollapse: singleKind === "C" ? "single" : inKindC > 0 ? "combo" : null,
    };

    return {
      column: term.column,
      value: term.value,
      inReproduced,
      single: { discover: single.discover, validate: validateStats },
      singleOverLine,
      inKindB,
      inCollapseReproduced,
      inKindC,
      explains,
    };
  });

  const countOf = (entry: FactorEntry, level: ExplainLevel): number =>
    [entry.explains.longThink, entry.explains.timeAndCollapse, entry.explains.quickCollapse].filter((x) => x === level).length;

  return entries.sort((a, b) => {
    const singleDiff = countOf(b, "single") - countOf(a, "single");
    if (singleDiff !== 0) return singleDiff;
    const comboDiff = countOf(b, "combo") - countOf(a, "combo");
    if (comboDiff !== 0) return comboDiff;
    return b.inReproduced.total - a.inReproduced.total;
  });
}

/** 発見用・検証用の表から、深さ 1〜3 の探索の結果を組む(計画「作るもの」2.。STEP TIME-CAUSE-3 で崩れの探索・共通因子・偶然の目安を足した)。 */
export function searchOf(discoverRows: readonly MoveFeatureRow[], validateRows: readonly MoveFeatureRow[]): SearchResult {
  const discoverBase = roleBaseOf(discoverRows);
  const validateBase = roleBaseOf(validateRows);

  const time = runSearchOf(discoverRows, validateRows, discoverBase, validateBase, TIME_OBJECTIVE);
  const collapse = runSearchOf(discoverRows, validateRows, discoverBase, validateBase, COLLAPSE_OBJECTIVE);
  const factors = factorSummaryOf(discoverRows, validateRows, discoverBase, validateBase, time.reproduced, collapse.reproduced);

  return {
    discover: roleSummaryOf(discoverBase),
    validate: roleSummaryOf(validateBase),
    depths: time.depths,
    reproduced: time.reproduced,
    notReproduced: time.notReproduced,
    collapseSearch: collapse,
    factors,
  };
}
