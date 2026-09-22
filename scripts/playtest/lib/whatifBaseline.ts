// STEP WHATIF 作業 3(docs/STEP_WHATIF_PLAN_2026-09-22.md §8.1-2)。`baselineTable.ts` に足す任意の 6 行
// (whatif.ts の summary から集めた 5 つの率 + 1 行)を組む純粋関数。**candidate/lower の判定は付けない**(v1)。
// pool の合計の率と、pool の 1 人ごとの最小〜最大を添えて並べるだけ。
//
// 【このファイルがやること】
// - `--whatif-material`(person)・`--whatif-pool`(pool)の入力の確かめ(`whatifInputProblems`):
//   - 各ファイルの最後の行が summary であること(無ければ問題として返す。数えられないため)
//   - すべてのファイルの `values`(meta 行の WHATIF_VALUES の写し)が一致すること(計画: person と pool で違えば exit 1。
//     ここでは material・pool のすべてのファイルの間で一致を見る ― 1 回の集計の中で同じ判断的知識の値だけを使うため、
//     baselineInputProblems の referenceNodes の確かめと同じ考え方)
//   - `--whatif-pool` のラベルの集合が、通常の `--pool`(baselineTable.ts の PoolSpec)のラベルの集合と一致すること
//     (計画: 「`--pool` と同じ流儀でラベルは一致させる」。ここでは集合として完全に一致することを求める ― 崩れ率の
//     基準値と同じ pool の人数・構成で whatif の基準値を出すため)
// - 6 行の集計(`whatifRateRowsOf`): 分母は `positionsRead`(5 行目までの率)・`scenesRead`(6 行目)の合計。
//   pool 合計はすべての pool のファイルを合わせた率、pool の人ごとの最小〜最大はラベルごとに合わせた率の範囲
//   (分母 0 の人はこの範囲の比べから除く ― baselineTable.ts の eligiblePool と同じ判断)
//
// 【このファイルが絶対にやらないこと】
// - candidate/lower のような判定・閾値を新しく置くこと(「一致率が高い/低い」を断定しないv1のまま、計画 §8.1-2)
// - エンジン・ファイルの読み書き・名前/手/局面を持つ値を扱うこと(呼び出し側が集計済みの数だけを渡す)
//
// 【判断的知識】無い。ここに新しい閾値・判定語は無い。WHATIF_VALUES(の一致確認)は呼び出し側(whatif.ts)がすでに
// 1 か所に置いた値をそのまま比べるだけ(ここで値を確定しない)。

export interface WhatifSummaryCounts {
  positionsRead: number;
  matchesTop1: number;
  withinMultiPv: number;
  forkCount: number;
  narrowHeldCount: number;
  chanceHeldCount: number;
  scenesRead: number;
  attackNoLegalMoveCount: number;
}

export interface WhatifFileEntry {
  /** 表示に使う名前(ファイルのパス) */
  name: string;
  /** 作業ツリーの根からの相対パス */
  path: string;
  kifuId: string;
  sha256: string;
  /** meta 行の values(WHATIF_VALUES の写し)。中身は解釈せず、一致の確かめにだけ使う。meta 行が無ければ undefined */
  values: unknown;
  /** summary 行から集めた数。最後の行が summary でなければ undefined(問題として返す) */
  summary: WhatifSummaryCounts | undefined;
}

export interface WhatifInputGroup {
  label: string;
  entries: readonly WhatifFileEntry[];
}

/**
 * `--whatif-material`(material)・`--whatif-pool`(whatifPools)の入力の確かめ。
 * `poolLabels` は通常の `--pool` のラベルの集合(baselineTable.ts の PoolSpec から作る)。
 * 問題を 1 件 1 文で返す(空なら通す)。
 */
export function whatifInputProblems(material: readonly WhatifFileEntry[], whatifPools: readonly WhatifInputGroup[], poolLabels: readonly string[]): string[] {
  const problems: string[] = [];
  if (material.length === 0) problems.push("--whatif-material の記録が無い");
  for (const group of whatifPools) if (group.entries.length === 0) problems.push(`--whatif-pool ${group.label} の記録が無い`);

  const whatifPoolLabels = whatifPools.map((group) => group.label);
  const duplicateLabel = whatifPoolLabels.find((label, index) => whatifPoolLabels.indexOf(label) !== index);
  if (duplicateLabel !== undefined) problems.push(`--whatif-pool に同じラベルが 2 回ある: ${duplicateLabel}`);

  // ラベルの一致(--pool と --whatif-pool)。集合として完全に一致すること
  const poolLabelSet = new Set(poolLabels);
  const whatifPoolLabelSet = new Set(whatifPoolLabels);
  for (const label of whatifPoolLabelSet) if (!poolLabelSet.has(label)) problems.push(`--whatif-pool のラベルが --pool に無い: ${label}`);
  for (const label of poolLabelSet) if (!whatifPoolLabelSet.has(label)) problems.push(`--pool のラベルに対応する --whatif-pool が無い: ${label}`);

  const all = [...material, ...whatifPools.flatMap((group) => group.entries)];
  for (const entry of all) {
    if (entry.summary === undefined) problems.push(`${entry.name} の最後の行が summary でない(whatif.ts の出力でない)`);
  }
  for (const key of ["name", "sha256", "kifuId"] as const) {
    const seen = new Map<string, number>();
    for (const entry of all) seen.set(entry[key], (seen.get(entry[key]) ?? 0) + 1);
    for (const [value, count] of seen) if (count > 1) problems.push(`同じ ${key} の whatif 記録が ${count} 本ある(--whatif-material と --whatif-pool の重なりを含む): ${value}`);
  }

  // values の一致(計画: person と pool で違えば exit 1。ここでは material・pool の全ファイルの間で見る)
  const withValues = all.filter((entry) => entry.summary !== undefined);
  if (withValues.length > 0) {
    const first = withValues[0]!;
    const firstJson = JSON.stringify(first.values);
    for (const entry of withValues) {
      if (JSON.stringify(entry.values) !== firstJson) {
        problems.push(`whatif の values が記録の間でそろわない(${first.name} と ${entry.name})`);
        break;
      }
    }
  }

  return problems;
}

// ---- 6 行の集計(計画 §8.1-2) ----

export interface WhatifRateCell {
  collapsed: number;
  denominator: number;
  ratePercent: number | null;
}

export interface WhatifPoolRange {
  /** 分母が 0 の人を除いた、pool の人ごとの率(%)の最小。誰も対象がいなければ null */
  minPercent: number | null;
  /** 同じく最大 */
  maxPercent: number | null;
}

export interface WhatifRateRow {
  id: string;
  label: string;
  subject: WhatifRateCell;
  poolTotal: WhatifRateCell;
  poolRange: WhatifPoolRange;
}

interface RowSpec {
  id: string;
  label: string;
  numeratorOf: (s: WhatifSummaryCounts) => number;
  denominatorOf: (s: WhatifSummaryCounts) => number;
}

/** 計画 §8.1-2 の 6 行。分母は 5 行目までが positionsRead の合計、6 行目だけ scenesRead の合計。 */
const ROWS: readonly RowSpec[] = [
  { id: "whatif_matchesTop1", label: "第 1 候補と同じ", numeratorOf: (s) => s.matchesTop1, denominatorOf: (s) => s.positionsRead },
  { id: "whatif_withinMultiPv", label: "上位 5 つの中に入った", numeratorOf: (s) => s.withinMultiPv, denominatorOf: (s) => s.positionsRead },
  { id: "whatif_fork", label: "分かれ道(fork)", numeratorOf: (s) => s.forkCount, denominatorOf: (s) => s.positionsRead },
  { id: "whatif_narrowHeld", label: "選択肢が限られた局面で第 1 候補と同じ(narrowHeld)", numeratorOf: (s) => s.narrowHeldCount, denominatorOf: (s) => s.positionsRead },
  { id: "whatif_chanceHeld", label: "相手の手の後の機会に第 1 候補と同じ(chanceHeld)", numeratorOf: (s) => s.chanceHeldCount, denominatorOf: (s) => s.positionsRead },
  { id: "whatif_attackNoLegalMove", label: "攻めの側に合法手が無かった場面", numeratorOf: (s) => s.attackNoLegalMoveCount, denominatorOf: (s) => s.scenesRead },
];

function percentOf(collapsed: number, denominator: number): number | null {
  return denominator === 0 ? null : (100 * collapsed) / denominator;
}

function cellOf(summaries: readonly WhatifSummaryCounts[], row: RowSpec): WhatifRateCell {
  const collapsed = summaries.reduce((sum, s) => sum + row.numeratorOf(s), 0);
  const denominator = summaries.reduce((sum, s) => sum + row.denominatorOf(s), 0);
  return { collapsed, denominator, ratePercent: percentOf(collapsed, denominator) };
}

/**
 * material(person)・whatifPools(pool)の入力から、6 行の表を組む(計画 §8.1-2)。
 * `whatifInputProblems` が空であること(呼び出し側がすでに確かめてから呼ぶ)を前提にする。
 */
export function whatifRateRowsOf(material: readonly WhatifFileEntry[], whatifPools: readonly WhatifInputGroup[]): WhatifRateRow[] {
  const subjectSummaries = material.map((entry) => entry.summary).filter((s): s is WhatifSummaryCounts => s !== undefined);
  const poolByLabel = whatifPools.map((group) => ({
    label: group.label,
    summaries: group.entries.map((entry) => entry.summary).filter((s): s is WhatifSummaryCounts => s !== undefined),
  }));
  const poolAllSummaries = poolByLabel.flatMap((group) => group.summaries);

  return ROWS.map((row) => {
    const subject = cellOf(subjectSummaries, row);
    const poolTotal = cellOf(poolAllSummaries, row);
    const memberRates = poolByLabel.map((group) => cellOf(group.summaries, row)).filter((cell) => cell.denominator > 0);
    const percents = memberRates.map((cell) => cell.ratePercent!);
    const poolRange: WhatifPoolRange = { minPercent: percents.length > 0 ? Math.min(...percents) : null, maxPercent: percents.length > 0 ? Math.max(...percents) : null };
    return { id: row.id, label: row.label, subject, poolTotal, poolRange };
  });
}

// ---- Markdown(呼び出し側の renderBaselineMarkdown に追記する行。名前・手・局面は出さない) ----

const rateCell = (cell: WhatifRateCell): string => (cell.denominator === 0 ? `${cell.collapsed} / 0` : `${cell.collapsed} / ${cell.denominator}(${cell.ratePercent!.toFixed(1)}%)`);
const rangeCell = (range: WhatifPoolRange): string => (range.minPercent === null || range.maxPercent === null ? "―" : `${range.minPercent.toFixed(1)}%〜${range.maxPercent.toFixed(1)}%`);

/** 計画 §8.1-2 の 6 行の Markdown(見出し行を含む)。`renderBaselineMarkdown` の出力の末尾に足す。 */
export function renderWhatifRateMarkdown(rows: readonly WhatifRateRow[]): string[] {
  return [
    "",
    "## whatif(重要な局面の分かれ道)の率(STEP WHATIF 作業 3。candidate/lower の判定は付けない)",
    "",
    "| 項目 | その人 | pool 合計 | pool の人ごとの範囲 |",
    "|---|---|---|---|",
    ...rows.map((row) => `| ${row.label} | ${rateCell(row.subject)} | ${rateCell(row.poolTotal)} | ${rangeCell(row.poolRange)} |`),
  ];
}
