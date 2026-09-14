// STEP D-COST(docs/STEP_D-COST_PLAN_2026-09-15.md)。同じ棋譜を深い走査(nodes 4,000,000)と軽い走査
// (nodes 100,000 など)で再生した 2 つの記録を、組(直前と直後の ready 行)ごとに突き合わせ、
// 深い走査の急落候補を軽い走査が「拾えた / 取りこぼし / 比べられなかった / 測っていない」かを数える(計画 2.2)。
//
// 【このファイルがやること】
// - 急落候補かどうかは **D1 の diagnoseRecords に決めさせる**(規則を 2 か所に持たない)。ここは突き合わせるだけ
// - 比べる前に G-1(行ごとの engineReference.nodes)・G-2(同じ ply の sfen)・G-3(meta の enginePath)を確かめ、
//   満たさない棋譜は「数えられなかった」にする(計画 7.1。規則 11.1)
// - 「比べられなかった」「測っていない」を取りこぼしに畳まない。率の分母にも入れない(規則 11.6。計画 2.2)
// - 見積もりの式(計画 5.・3.)を関数にする
//
// 【このファイルが絶対にやらないこと】
// - エンジンを回すこと。記録を読むだけ
// - 急落の閾値を変えること・軽い走査の閾値を緩めること(計画 Q-7。規則は呼び出し側が DRAFT_RULE_1 を渡す)
// - 並列の効率 e(p) を仮定した見積もり(測っていない。計画 L-5)・円への換算(計画 L-9)

import type { MetaLine, RecordLine } from "../invariants/types.js";
import {
  diagnoseRecords,
  pairEvaluations,
  readEvaluations,
  type DiagnosisRule,
  type EvaluationState,
  type NotComparedReason,
} from "./failureEvent.js";

// ---- 1 つの記録の見え方 ----

type DropKind = "cpDrop" | "mateDrop";

type PairState =
  | { kind: "drop"; kinds: DropKind[]; diffCp: number | null }
  | { kind: "notDrop"; diffCp: number | null }
  | { kind: "notCompared"; reason: NotComparedReason };

interface ScanView {
  /** 組(`from->to`)ごとの状態。記録に無い組はここに無い(「測っていない」) */
  pairs: Map<string, PairState>;
  /** 直後の行でパスすると詰まされる読みがあった組 */
  matedIfPass: Set<string>;
  /** ply ごとの評価の状態 */
  rowStates: Map<number, EvaluationState>;
  /** 死因①(draft)の候補が付いた Failure Event の数 */
  cause1: number;
}

const pairKey = (fromPly: number, toPly: number): string => `${fromPly}->${toPly}`;
const toPlyOf = (key: string): number => Number(key.split("->")[1]);

function viewOf(kifuId: string, records: readonly RecordLine[], rule: DiagnosisRule): ScanView {
  const rows = readEvaluations(records);
  const { events } = diagnoseRecords(kifuId, records, rule);
  const eventByKey = new Map(events.map((event) => [pairKey(event.fromReadyPly, event.toReadyPly), event]));
  const pairs = new Map<string, PairState>();
  for (const pair of pairEvaluations(rows)) {
    const key = pairKey(pair.fromPly, pair.toPly);
    if (pair.kind === "notCompared") {
      pairs.set(key, { kind: "notCompared", reason: pair.reason });
      continue;
    }
    const diffCp = pair.kind === "compared" ? pair.diffCp : null;
    const kinds = (eventByKey.get(key)?.branch.kinds ?? []).filter((kind): kind is DropKind => kind !== "matedIfPass");
    pairs.set(key, kinds.length > 0 ? { kind: "drop", kinds, diffCp } : { kind: "notDrop", diffCp });
  }
  return {
    pairs,
    matedIfPass: new Set(
      events.filter((event) => event.branch.kinds.includes("matedIfPass")).map((event) => pairKey(event.fromReadyPly, event.toReadyPly)),
    ),
    rowStates: new Map(rows.map((row) => [row.ply, row.evaluation.state])),
    cause1: events.filter((event) => event.candidateModes.length > 0).length,
  };
}

// ---- 突き合わせ ----

/** 基準の側で当たった組を、もう一方の側で分けた数(計画 2.2 の 4 区分) */
export interface DirectionCounts {
  /** 基準の側で当たった組の数 */
  base: number;
  /** もう一方でも当たった */
  found: number;
  /** もう一方で比べたが当たらなかった(深い → 軽いなら「取りこぼし」、軽い → 深いなら「余計に拾った」) */
  notFound: number;
  /** もう一方で比べられなかった(理由ごとの内訳つき) */
  notComparable: number;
  notComparableReasons: Record<string, number>;
  /** もう一方の記録にその組が無い */
  notMeasured: number;
}

function emptyCounts(): DirectionCounts {
  return { base: 0, found: 0, notFound: 0, notComparable: 0, notComparableReasons: {}, notMeasured: 0 };
}

function addReason(counts: DirectionCounts, reason: string): void {
  counts.notComparable += 1;
  counts.notComparableReasons[reason] = (counts.notComparableReasons[reason] ?? 0) + 1;
}

function compareDrops(
  base: ScanView,
  other: ScanView,
): { counts: DirectionCounts; kindMismatch: number; notFoundKeys: string[]; foundKeys: string[] } {
  const counts = emptyCounts();
  let kindMismatch = 0;
  const notFoundKeys: string[] = [];
  const foundKeys: string[] = [];
  for (const [key, state] of base.pairs) {
    if (state.kind !== "drop") continue;
    counts.base += 1;
    const otherState = other.pairs.get(key);
    if (otherState === undefined) {
      counts.notMeasured += 1;
    } else if (otherState.kind === "drop") {
      counts.found += 1;
      foundKeys.push(key);
      if ([...state.kinds].sort().join("+") !== [...otherState.kinds].sort().join("+")) kindMismatch += 1;
    } else if (otherState.kind === "notDrop") {
      counts.notFound += 1;
      notFoundKeys.push(key);
    } else {
      addReason(counts, otherState.reason);
    }
  }
  return { counts, kindMismatch, notFoundKeys, foundKeys };
}

function compareMatedIfPass(base: ScanView, other: ScanView): DirectionCounts {
  const counts = emptyCounts();
  for (const key of base.matedIfPass) {
    counts.base += 1;
    if (other.matedIfPass.has(key)) {
      counts.found += 1;
    } else if (!other.pairs.has(key)) {
      counts.notMeasured += 1;
    } else {
      const state = other.rowStates.get(toPlyOf(key));
      if (state === "measured") counts.notFound += 1;
      else addReason(counts, state ?? "unrecorded");
    }
  }
  return counts;
}

export interface ScanInput {
  records: readonly RecordLine[];
  meta: MetaLine | undefined;
  /** この記録の engineReference を測ったはずのノード数(G-1) */
  expectedNodes: number;
}

export type NotCountedReason = "nodes_mismatch" | "sfen_mismatch" | "engine_path_mismatch" | "meta_missing";

export type ScanComparison =
  | {
      kind: "counted";
      kifuId: string;
      /** 深い走査の急落候補を、軽い走査で分けた数 */
      drops: DirectionCounts;
      /** 拾えた組のうち、急落の種類(cpDrop / mateDrop)が食い違ったもの */
      kindMismatch: number;
      /** 軽い走査の急落候補を、深い走査で分けた数(notFound が「余計に拾った」) */
      extras: DirectionCounts;
      matedIfPass: { deepToLight: DirectionCounts; lightToDeep: DirectionCounts };
      /** 拾えた組のうち両方に差があるものの |軽い − 深い| */
      diffGaps: number[];
      /** 深い走査で比べた組のうち、差が閾値 ± nearBandCp にあるもの / そのうち取りこぼしたもの */
      nearThreshold: { deepPairs: number; missed: number };
      cause1: { deep: number; light: number };
    }
  | { kind: "notCounted"; kifuId: string; reason: NotCountedReason | "exception"; detail: string };

function guard(deep: ScanInput, light: ScanInput): { reason: NotCountedReason; detail: string } | null {
  // G-1: 行ごとの engineReference.nodes
  for (const [label, side] of [["深い", deep], ["軽い", light]] as const) {
    for (const record of side.records) {
      if (record.phase !== "ready" || !record.engineReference) continue;
      if (record.engineReference.nodes !== side.expectedNodes) {
        return {
          reason: "nodes_mismatch",
          detail: `${label}走査の ply ${record.ply} の engineReference.nodes が ${record.engineReference.nodes}(期待 ${side.expectedNodes})`,
        };
      }
    }
  }
  // G-2: 同じ ply の sfen
  const deepSfen = new Map(deep.records.filter((record) => record.phase === "ready").map((record) => [record.ply, record.sfen]));
  for (const record of light.records) {
    if (record.phase !== "ready") continue;
    const sfen = deepSfen.get(record.ply);
    if (sfen !== undefined && sfen !== record.sfen) {
      return { reason: "sfen_mismatch", detail: `ply ${record.ply} の sfen が 2 つの記録で違う` };
    }
  }
  // G-3: meta の enginePath(評価関数の違いは meta から分からない ― P-43)
  if (deep.meta === undefined || light.meta === undefined) {
    return { reason: "meta_missing", detail: `meta 行が無い(深い: ${deep.meta ? "あり" : "無し"}、軽い: ${light.meta ? "あり" : "無し"})` };
  }
  if (deep.meta.enginePath !== light.meta.enginePath) {
    return { reason: "engine_path_mismatch", detail: `enginePath が違う(深い: ${deep.meta.enginePath}、軽い: ${light.meta.enginePath})` };
  }
  return null;
}

/**
 * 同じ棋譜の深い記録と軽い記録を突き合わせる。**第 2 引数が深い走査、第 3 引数が軽い走査**。
 * 規則(`rule`)と閾値の近くの幅(`nearBandCp`)は呼び出し側が渡す(既定値を置かない)。
 */
export function compareScans(
  kifuId: string,
  deep: ScanInput,
  light: ScanInput,
  rule: DiagnosisRule,
  nearBandCp: number,
): ScanComparison {
  const failed = guard(deep, light);
  if (failed) return { kind: "notCounted", kifuId, ...failed };

  const deepView = viewOf(kifuId, deep.records, rule);
  const lightView = viewOf(kifuId, light.records, rule);
  const deepToLight = compareDrops(deepView, lightView);
  const lightToDeep = compareDrops(lightView, deepView);

  const diffGaps: number[] = [];
  for (const key of deepToLight.foundKeys) {
    const deepState = deepView.pairs.get(key);
    const lightState = lightView.pairs.get(key);
    if (deepState?.kind === "drop" && lightState?.kind === "drop" && deepState.diffCp !== null && lightState.diffCp !== null) {
      diffGaps.push(Math.abs(lightState.diffCp - deepState.diffCp));
    }
  }

  const isNear = (state: PairState | undefined): boolean =>
    state !== undefined && state.kind !== "notCompared" && state.diffCp !== null && Math.abs(state.diffCp - rule.dropCp) <= nearBandCp;
  const deepPairsNear = [...deepView.pairs.values()].filter(isNear).length;
  const missedNear = deepToLight.notFoundKeys.filter((key) => isNear(deepView.pairs.get(key))).length;

  return {
    kind: "counted",
    kifuId,
    drops: deepToLight.counts,
    kindMismatch: deepToLight.kindMismatch,
    extras: lightToDeep.counts,
    matedIfPass: { deepToLight: compareMatedIfPass(deepView, lightView), lightToDeep: compareMatedIfPass(lightView, deepView) },
    diffGaps,
    nearThreshold: { deepPairs: deepPairsNear, missed: missedNear },
    cause1: { deep: deepView.cause1, light: lightView.cause1 },
  };
}

// ---- 率と合計 ----

export interface Rate {
  numerator: number;
  denominator: number;
  /** 分母が 0 なら null(0% にしない) */
  value: number | null;
}

function rateOf(numerator: number, denominator: number): Rate {
  return { numerator, denominator, value: denominator === 0 ? null : numerator / denominator };
}

/** 取りこぼし率 = 取りこぼし ÷(拾えた + 取りこぼし)。比べられなかった・測っていないは分母に入れない(計画 2.2) */
export function missRate(counts: DirectionCounts): Rate {
  return rateOf(counts.notFound, counts.found + counts.notFound);
}

function mergeCounts(a: DirectionCounts, b: DirectionCounts): DirectionCounts {
  const reasons = { ...a.notComparableReasons };
  for (const [reason, count] of Object.entries(b.notComparableReasons)) reasons[reason] = (reasons[reason] ?? 0) + count;
  return {
    base: a.base + b.base,
    found: a.found + b.found,
    notFound: a.notFound + b.notFound,
    notComparable: a.notComparable + b.notComparable,
    notComparableReasons: reasons,
    notMeasured: a.notMeasured + b.notMeasured,
  };
}

type Counted = Extract<ScanComparison, { kind: "counted" }>;

/** 数えられた棋譜を足し合わせる。**率は足した数から出し直す**(棋譜ごとの率を平均しない) */
export function sumComparisons(rows: readonly ScanComparison[]): Counted {
  const counted = rows.filter((row): row is Counted => row.kind === "counted");
  return counted.reduce<Counted>(
    (total, row) => ({
      kind: "counted",
      kifuId: "合計",
      drops: mergeCounts(total.drops, row.drops),
      kindMismatch: total.kindMismatch + row.kindMismatch,
      extras: mergeCounts(total.extras, row.extras),
      matedIfPass: {
        deepToLight: mergeCounts(total.matedIfPass.deepToLight, row.matedIfPass.deepToLight),
        lightToDeep: mergeCounts(total.matedIfPass.lightToDeep, row.matedIfPass.lightToDeep),
      },
      diffGaps: [...total.diffGaps, ...row.diffGaps],
      nearThreshold: {
        deepPairs: total.nearThreshold.deepPairs + row.nearThreshold.deepPairs,
        missed: total.nearThreshold.missed + row.nearThreshold.missed,
      },
      cause1: { deep: total.cause1.deep + row.cause1.deep, light: total.cause1.light + row.cause1.light },
    }),
    {
      kind: "counted",
      kifuId: "合計",
      drops: emptyCounts(),
      kindMismatch: 0,
      extras: emptyCounts(),
      matedIfPass: { deepToLight: emptyCounts(), lightToDeep: emptyCounts() },
      diffGaps: [],
      nearThreshold: { deepPairs: 0, missed: 0 },
      cause1: { deep: 0, light: 0 },
    },
  );
}

// ---- 報告 ----

export interface ScanPairInput {
  kifuId: string;
  deep: ScanInput;
  light: ScanInput;
}

type Compare = typeof compareScans;

/** 棋譜ごとに突き合わせる。**例外を外へ出さない**(`diagnose.ts` と同じ)。`compare` は試験専用 */
export function buildScanReport(
  inputs: readonly ScanPairInput[],
  rule: DiagnosisRule,
  nearBandCp: number,
  compare: Compare = compareScans,
): ScanComparison[] {
  return inputs.map((input) => {
    try {
      return compare(input.kifuId, input.deep, input.light, rule, nearBandCp);
    } catch (error) {
      return {
        kind: "notCounted",
        kifuId: input.kifuId,
        reason: "exception",
        detail: error instanceof Error ? `${error.constructor.name}: ${error.message}` : String(error),
      };
    }
  });
}

function rateCell(rate: Rate): string {
  return rate.value === null ? "分母 0" : `${rate.numerator}/${rate.denominator}(${(rate.value * 100).toFixed(1)}%)`;
}

function reasonsCell(counts: DirectionCounts): string {
  const entries = Object.entries(counts.notComparableReasons).sort(([a], [b]) => a.localeCompare(b));
  return entries.length === 0 ? `${counts.notComparable}` : `${counts.notComparable}(${entries.map(([r, n]) => `${r} ${n}`).join("・")})`;
}

function median(values: readonly number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[mid]! : (sorted[mid - 1]! + sorted[mid]!) / 2;
}

const NOTES = [
  "- **この件数は道具の確認用であり、軽い走査の良し悪しの判定ではない。** 深い走査どうしも揺れる(P-33)ので、深い走査をもう 1 回回した対照との比べを並べて読む",
  "- **「比べられなかった」「測っていない」は取りこぼしではない。** 取りこぼし率の分母に入れない",
  "- 急落候補の規則は D1 の仮置き(差 ≤ −400 など)のまま。取りこぼし率はこの規則に依存する",
  "- 評価関数の種類は記録の meta に残らない(P-43)。記録の README の nn.bin の sha256 で確かめる",
];

/**
 * 表を描く。`onlyDeep` / `onlyLight` は、片方のフォルダにしか無かった記録のファイル名(棋譜ごと「測っていない」)。
 */
export function renderScanReport(
  rows: readonly ScanComparison[],
  missing: { onlyDeep: readonly string[]; onlyLight: readonly string[] },
): string[] {
  const lines: string[] = ["# 軽い走査と深い走査の比べ(STEP D-COST。道具の確認用)", "", ...NOTES, ""];
  const total = sumComparisons(rows);
  const counted = [...rows.filter((row): row is Counted => row.kind === "counted"), total];

  lines.push("## 急落候補(深い走査 → 軽い走査)", "");
  lines.push("| 対象 | 深い走査の急落候補 | 拾えた | 取りこぼし | 比べられなかった | 測っていない | 取りこぼし率 | 種類の食い違い |");
  lines.push("|---|---|---|---|---|---|---|---|");
  for (const row of counted) {
    const c = row.drops;
    lines.push(`| ${row.kifuId} | ${c.base} | ${c.found} | ${c.notFound} | ${reasonsCell(c)} | ${c.notMeasured} | ${rateCell(missRate(c))} | ${row.kindMismatch} |`);
  }
  lines.push("");

  lines.push("## 余計に拾った(軽い走査 → 深い走査)", "");
  lines.push("| 対象 | 軽い走査の急落候補 | 深い走査でも急落 | 余計に拾った | 比べられなかった | 測っていない | 余計に拾った率 |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const row of counted) {
    const c = row.extras;
    lines.push(`| ${row.kifuId} | ${c.base} | ${c.found} | ${c.notFound} | ${reasonsCell(c)} | ${c.notMeasured} | ${rateCell(missRate(c))} |`);
  }
  lines.push("");

  lines.push("## パスすると詰まされる読み(matedIfPass。急落候補とは別に数える)", "");
  lines.push("| 対象 | 深い走査で当たった | 軽い走査でも | 軽い走査で比べて無し | 比べられなかった | 測っていない | 軽い走査だけで当たった |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const row of counted) {
    const d = row.matedIfPass.deepToLight;
    lines.push(`| ${row.kifuId} | ${d.base} | ${d.found} | ${d.notFound} | ${reasonsCell(d)} | ${d.notMeasured} | ${row.matedIfPass.lightToDeep.notFound} |`);
  }
  lines.push("");

  lines.push("## 差の分布と閾値の近く", "");
  lines.push("| 対象 | 拾えた組の差の食い違い(中央値) | 同(最大) | 深い走査で閾値の近くにある組 | うち取りこぼし | 死因①(深い) | 死因①(軽い) |");
  lines.push("|---|---|---|---|---|---|---|");
  for (const row of counted) {
    const mid = median(row.diffGaps);
    const max = row.diffGaps.length === 0 ? null : Math.max(...row.diffGaps);
    lines.push(
      `| ${row.kifuId} | ${mid ?? "組が無い"} | ${max ?? "組が無い"} | ${row.nearThreshold.deepPairs} | ${row.nearThreshold.missed} | ${row.cause1.deep} | ${row.cause1.light} |`,
    );
  }
  lines.push("");

  const notCounted = rows.filter((row): row is Extract<ScanComparison, { kind: "notCounted" }> => row.kind === "notCounted");
  lines.push("## 数えなかった記録", "");
  if (notCounted.length === 0 && missing.onlyDeep.length === 0 && missing.onlyLight.length === 0) lines.push("- 無し");
  for (const row of notCounted) lines.push(`- 数えられなかった: ${row.kifuId}(${row.reason}: ${row.detail})`);
  for (const name of missing.onlyDeep) lines.push(`- 深い走査にしか無い(軽い走査は測っていない): ${name}`);
  for (const name of missing.onlyLight) lines.push(`- 軽い走査にしか無い(深い走査は測っていない): ${name}`);
  lines.push("");
  return lines;
}

// ---- 見積もりの式(計画 5.・3.。数字は測った後に入れる)----

/** 1 局(1 段): T_局 = t_boot + R × t_row */
export function singleStageSeconds(input: { tBootSec: number; readyRows: number; tRowSec: number }): number {
  return input.tBootSec + input.readyRows * input.tRowSec;
}

/** N 局(1 プロセス): T_N = N × T_局。**並列の効率は測っていないので、p > 1 の式は置かない**(計画 L-5) */
export function batchSeconds(input: { games: number; perGameSec: number }): number {
  return input.games * input.perGameSec;
}

/** 二段・案 (ii): T = t_boot + R × t_row(軽) + K × 2 × (t_ref(深) − t_ref(軽))。組 1 つにつき 2 行を深くする */
export function twoStageReferencePliesSeconds(input: {
  tBootSec: number;
  readyRows: number;
  tRowLightSec: number;
  candidates: number;
  tRefDeepSec: number;
  tRefLightSec: number;
}): number {
  return input.tBootSec + input.readyRows * input.tRowLightSec + input.candidates * 2 * (input.tRefDeepSec - input.tRefLightSec);
}

/** 二段・案 (i): T = t_boot + R × t_imm + K × 2 × t_row(深) */
export function twoStageTargetPliesSeconds(input: {
  tBootSec: number;
  readyRows: number;
  tImmSec: number;
  candidates: number;
  tRowDeepSec: number;
}): number {
  return input.tBootSec + input.readyRows * input.tImmSec + input.candidates * 2 * input.tRowDeepSec;
}
