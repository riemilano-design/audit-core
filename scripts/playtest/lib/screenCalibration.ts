// STEP D-SCREEN-2(docs/STEP_D-SCREEN_PLAN_2026-09-15.md §5・§11 の床)。校正で数える量を、記録を読むだけの純粋関数にする。
// **エンジンは回さない**(回すのは rescreen.ts と measure-twice.ts。数えるのは screen-calibrate.ts がこのファイルを呼んで行う)。
//
// 【このファイルがやること】
// - 本番の形(§5 の 1.)と床の (ii): 比べる相手の記録(4M 一律・段 1)と段 2 の記録の Failure Event を組 (fromReadyPly, toReadyPly) で突き合わせ、
//   一致・当たり方だけ違う・取りこぼし・余計を数え、もう片方の同じ組が比べられない・組が無い Event は理由つきで別に並べる(D-COST §2.2。監査 R-1)。
//   死因①(draft)の一致も並べる
// - 同じ分岐点の counterfactual.state の一致を、段 2 の pvSource ごとに分子・分母で数える(§5 の 1.・§11)
// - 深い組で pvFirstMoveIsBestmoveAtBefore が false の数 / 深い組の compared の数を、標識の有無で分けて数える(§11 の (vii))
// - 床の行(§5 の 0. (i)・§11 の (vi)): 読み直した行の engineReferenceDeep と、相手の同じ ply の engineReference の一致。深い focus_baseline と相手の
//   searchPvs の focus_baseline の長さ・標識・1 手目の一致
// - 2 回の rescreen(§5 の 0. (iii)・§11 の (iv)): record 行のバイト一致と searchPvsDeep の一致。meta は deepRun の startedAt・gitHead・dirty を除いて比べる
//   (回すたびに変わる欄。2 回が同じコードで回ったかは報告を読む人が gitHead で見る)
// - 同じ局面を続けて 2 回測った結果の比べ(§11 の (v)。measure-twice.ts の出力を読む)
//
// 【このファイルが絶対にやらないこと】
// - 4M 一律をやめるかの判断・閾値を変えること(校正の結果を見て人間が決める ― §9)
// - 「比べられなかった」「相手に無い」を一致・不一致に畳むこと(分母に入れない)

import type { EngineReferenceMeasurement } from "../../../apps/server/src/analysis/engineReference.js";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { MetaLine, RecordLine } from "../invariants/types.js";
import { diagnoseRecords, pairEvaluations, readEvaluations, type DiagnosisRule, type EvaluationPair, type FailureEvent, type NotComparedReason } from "./failureEvent.js";
import { choosePairSources, screenOfRecord, type ScreenCounts } from "./screenDiagnosis.js";
import { initialSfenOf } from "./sideAlignment.js";

export interface Rate {
  numerator: number;
  denominator: number;
}

const rateOf = (numerator: number, denominator: number): Rate => ({ numerator, denominator });

// ---- Failure Event の集合(§5 の 1.・床の (ii)。D-COST §2.2 の分け方 ― 監査 R-1)----

/** もう片方の同じ組が比べられなかった理由(組の notCompared の reason)か、同じ組が無い(記録が途中で終わった等) */
export type UncomparableReason = NotComparedReason | "noPair";

export interface UncomparableEvent {
  /** `分岐点:kinds` */
  key: string;
  reason: UncomparableReason;
}

export interface EventSetComparison {
  /** 相手(4M 一律・段 1)の Event の数 */
  base: number;
  /** 段 2 の Event の数 */
  stage2: number;
  /** 同じ組 (fromReadyPly, toReadyPly) に両方の Event があり、kinds(並べ替えて比べる)が同じ数 */
  common: number;
  /** 同じ組に両方の Event があり、kinds だけ違う(取りこぼし・余計に入れない)。`分岐点:相手の kinds→段 2 の kinds` */
  kindsDiffer: string[];
  /** 取りこぼし: 相手にだけあり、段 2 の同じ組は比べられた(差を取った・直後が詰み)。`分岐点:kinds` */
  missed: string[];
  /** 相手にだけあり、段 2 の同じ組が比べられない・組が無い(取りこぼしに入れない) */
  missedUncomparable: UncomparableEvent[];
  /** 余計: 段 2 にだけあり、相手の同じ組は比べられた */
  extra: string[];
  /** 段 2 にだけあり、相手の同じ組が比べられない・組が無い(余計に入れない) */
  extraUncomparable: UncomparableEvent[];
  /** 取りこぼし ÷(取りこぼし + 一致 + 当たり方だけ違う) */
  missRate: Rate;
  /** 余計 ÷(余計 + 一致 + 当たり方だけ違う) */
  extraRate: Rate;
}

/** 片側の Event と、その記録の組(段 2 は組ごとに選んだ出どころの組) */
export interface EventSide {
  events: readonly FailureEvent[];
  pairs: readonly EvaluationPair[];
}

const kindsOf = (event: FailureEvent): string => [...event.branch.kinds].sort().join("+");
const eventKey = (event: FailureEvent): string => `${event.branchPly}:${kindsOf(event)}`;
const pairKey = (fromPly: number, toPly: number): string => `${fromPly}-${toPly}`;
const eventPairKey = (event: FailureEvent): string => pairKey(event.fromReadyPly, event.toReadyPly);

/** 片側にだけある Event を、もう片方の同じ組の状態で「比べられた」と「比べられない(理由つき)」に分ける */
function splitOneSided(events: readonly FailureEvent[], otherPairs: readonly EvaluationPair[]): { compared: string[]; uncomparable: UncomparableEvent[] } {
  const pairByKey = new Map(otherPairs.map((pair) => [pairKey(pair.fromPly, pair.toPly), pair]));
  const compared: string[] = [];
  const uncomparable: UncomparableEvent[] = [];
  for (const event of events) {
    const pair = pairByKey.get(eventPairKey(event));
    if (pair === undefined) uncomparable.push({ key: eventKey(event), reason: "noPair" });
    else if (pair.kind === "notCompared") uncomparable.push({ key: eventKey(event), reason: pair.reason });
    else compared.push(eventKey(event));
  }
  return { compared, uncomparable };
}

export function compareEventSets(base: EventSide, stage2: EventSide): EventSetComparison {
  const baseByPair = new Map(base.events.map((event) => [eventPairKey(event), event]));
  const stage2ByPair = new Map(stage2.events.map((event) => [eventPairKey(event), event]));
  let common = 0;
  const kindsDiffer: string[] = [];
  for (const [key, event] of baseByPair) {
    const counterpart = stage2ByPair.get(key);
    if (counterpart === undefined) continue;
    if (kindsOf(counterpart) === kindsOf(event)) common += 1;
    else kindsDiffer.push(`${event.branchPly}:${kindsOf(event)}→${kindsOf(counterpart)}`);
  }
  const missed = splitOneSided(base.events.filter((event) => !stage2ByPair.has(eventPairKey(event))), stage2.pairs);
  const extra = splitOneSided(stage2.events.filter((event) => !baseByPair.has(eventPairKey(event))), base.pairs);
  const matched = common + kindsDiffer.length;
  return {
    base: base.events.length,
    stage2: stage2.events.length,
    common,
    kindsDiffer,
    missed: missed.compared,
    missedUncomparable: missed.uncomparable,
    extra: extra.compared,
    extraUncomparable: extra.uncomparable,
    missRate: rateOf(missed.compared.length, missed.compared.length + matched),
    extraRate: rateOf(extra.compared.length, extra.compared.length + matched),
  };
}

export interface RecordInput {
  meta: MetaLine | undefined;
  records: readonly RecordLine[];
}

export interface StageComparison {
  kifuId: string;
  events: EventSetComparison;
  /** 死因①(draft)の候補が付いた Event の数と、同じ分岐点で両方に付いた数 */
  cause1: { base: number; stage2: number; common: number };
  /** 同じ分岐点の Event の counterfactual.state が一致した数 / 比べた数(段 2 の pvSource ごと) */
  counterfactualState: { light: Rate; deep: Rate };
  /** 深い組の compared のうち pvFirstMoveIsBestmoveAtBefore が false の数(§11 の (vii))。標識付き(lowerbound か upperbound)の分を別に持つ */
  deepFirstMove: { notBestmove: Rate; boundedNotBestmove: Rate; unboundedNotBestmove: Rate };
  screen: ScreenCounts;
}

/**
 * 比べる相手の記録(4M 一律。床では段 1)と段 2 の記録を、同じ規則で診断して突き合わせる。
 * 段 2 の記録は不変条件を確かめてから使う(破れていれば InvalidScreenRecordError。呼び出し側が「数えられなかった」にする)。
 */
export function compareWithStage2(kifuId: string, base: RecordInput, stage2: RecordInput, rule: DiagnosisRule): StageComparison {
  const screen = screenOfRecord(kifuId, stage2.meta, stage2.records);
  if (screen === undefined) throw new Error(`段 2 の記録 ${kifuId} の meta に screen が無い`);
  if (screenOfRecord(kifuId, base.meta, base.records) !== undefined) throw new Error(`比べる相手の記録 ${kifuId} の meta に screen がある(相手は 4M 一律か段 1 の記録)`);
  const baseEvents = diagnoseRecords(kifuId, base.records, rule, initialSfenOf(base.meta)).events;
  const stage2Result = diagnoseRecords(kifuId, stage2.records, rule, initialSfenOf(stage2.meta), screen);
  const stage2Events = stage2Result.events;
  // 突き合わせの組: 相手は記録の組、段 2 は組ごとに選んだ出どころの組(diagnoseRecords と同じ選び方)
  const basePairs = pairEvaluations(readEvaluations(base.records));
  const stage2Pairs = choosePairSources(readEvaluations(stage2.records)).map((chosen) => chosen.pair);

  const baseByPly = new Map(baseEvents.map((event) => [event.branchPly, event]));
  const state = { light: rateOf(0, 0), deep: rateOf(0, 0) };
  const firstMove = { notBestmove: rateOf(0, 0), boundedNotBestmove: rateOf(0, 0), unboundedNotBestmove: rateOf(0, 0) };
  let cause1Common = 0;
  for (const event of stage2Events) {
    const source = event.branch.evaluationSource ?? "light";
    const counterpart = baseByPly.get(event.branchPly);
    if (counterpart !== undefined) {
      state[source].denominator += 1;
      if (counterpart.counterfactual.state === event.counterfactual.state) state[source].numerator += 1;
      if (counterpart.candidateModes.length > 0 && event.candidateModes.length > 0) cause1Common += 1;
    }
    const counterfactual = event.counterfactual;
    if (source === "deep" && counterfactual.state === "compared") {
      const bounded = counterfactual.pvBounded.lowerbound || counterfactual.pvBounded.upperbound;
      const miss = counterfactual.pvFirstMoveIsBestmoveAtBefore ? 0 : 1;
      firstMove.notBestmove.denominator += 1;
      firstMove.notBestmove.numerator += miss;
      const side = bounded ? firstMove.boundedNotBestmove : firstMove.unboundedNotBestmove;
      side.denominator += 1;
      side.numerator += miss;
    }
  }

  return {
    kifuId,
    events: compareEventSets({ events: baseEvents, pairs: basePairs }, { events: stage2Events, pairs: stage2Pairs }),
    cause1: {
      base: baseEvents.filter((event) => event.candidateModes.length > 0).length,
      stage2: stage2Events.filter((event) => event.candidateModes.length > 0).length,
      common: cause1Common,
    },
    counterfactualState: state,
    deepFirstMove: firstMove,
    screen: stage2Result.screen!,
  };
}

// ---- 床の行(§5 の 0. (i)・§11 の (vi))----

export interface DeepRowComparison {
  /** 読み直した ready 行の数 */
  deepRows: number;
  /** 相手の同じ ply の行が無い(比べられない) */
  noCounterpart: number;
  /** engineReferenceDeep と相手の engineReference が同じ(JSON の文字列で比べる。同じ関数が組み立てた値なので欄の並びは揃う) */
  referenceEqual: number;
  /** 両方に focus_baseline(multipv 1)がある行 */
  pvCompared: number;
  pvLengthEqual: number;
  pvBoundsEqual: number;
  pvFirstMoveEqual: number;
}

const focusOf = (observations: readonly SearchPvObservation[] | null | undefined): SearchPvObservation | undefined =>
  observations?.find((observation) => observation.source === "focus_baseline" && observation.multipv === 1);

/** 段 2 の記録の読み直した行を、相手の記録(床では段 1 の 4M 一律、本番の形では別に回した 4M 一律)の同じ ply の行と比べる */
export function compareDeepRows(stage2Records: readonly RecordLine[], baseRecords: readonly RecordLine[]): DeepRowComparison {
  const baseByPly = new Map(baseRecords.filter((record) => record.phase === "ready").map((record) => [record.ply, record]));
  const counts: DeepRowComparison = { deepRows: 0, noCounterpart: 0, referenceEqual: 0, pvCompared: 0, pvLengthEqual: 0, pvBoundsEqual: 0, pvFirstMoveEqual: 0 };
  for (const record of stage2Records) {
    if (record.phase !== "ready" || !Object.hasOwn(record, "engineReferenceDeep")) continue;
    counts.deepRows += 1;
    const counterpart = baseByPly.get(record.ply);
    if (counterpart === undefined) {
      counts.noCounterpart += 1;
      continue;
    }
    if (JSON.stringify(record.engineReferenceDeep) === JSON.stringify(counterpart.engineReference ?? null)) counts.referenceEqual += 1;
    const deepFocus = focusOf(record.searchPvsDeep);
    const baseFocus = focusOf(counterpart.searchPvs);
    if (deepFocus === undefined || baseFocus === undefined) continue;
    counts.pvCompared += 1;
    if (deepFocus.pv.length === baseFocus.pv.length) counts.pvLengthEqual += 1;
    if (deepFocus.lowerbound === baseFocus.lowerbound && deepFocus.upperbound === baseFocus.upperbound) counts.pvBoundsEqual += 1;
    if (deepFocus.pv[0] !== undefined && deepFocus.pv[0] === baseFocus.pv[0]) counts.pvFirstMoveEqual += 1;
  }
  return counts;
}

// ---- 2 回の rescreen(§5 の 0. (iii)・§11 の (iv))----

export interface RescreenRunComparison {
  /** meta(deepRun の startedAt・gitHead・dirty を除く)が同じ */
  metaEqual: boolean;
  /** record 行の数(2 回で違えば多いほう) */
  recordLines: number;
  /** 同じ位置の record 行がバイト一致した数 */
  recordLinesEqual: number;
  /** 1 回目で searchPvsDeep を持つ行の数 */
  deepRows: number;
  /** そのうち、2 回目の同じ位置の行の searchPvsDeep が同じ数 */
  searchPvsDeepEqual: number;
}

const RUN_VARYING_KEYS = ["startedAt", "gitHead", "dirty"] as const;

function metaWithoutRunKeys(line: Record<string, unknown>): string {
  const copy = JSON.parse(JSON.stringify(line)) as { screen?: { deepRun?: Record<string, unknown> } };
  for (const key of RUN_VARYING_KEYS) delete copy.screen?.deepRun?.[key];
  return JSON.stringify(copy);
}

export function compareRescreenRuns(first: string, second: string): RescreenRunComparison {
  const split = (text: string) => text.split("\n").filter((line) => line.trim().length > 0);
  const kindOf = (line: string) => (JSON.parse(line) as { kind?: unknown }).kind;
  const a = split(first);
  const b = split(second);
  const metaA = a.find((line) => kindOf(line) === "meta");
  const metaB = b.find((line) => kindOf(line) === "meta");
  const recordsA = a.filter((line) => kindOf(line) === "record");
  const recordsB = b.filter((line) => kindOf(line) === "record");
  let recordLinesEqual = 0;
  let deepRows = 0;
  let searchPvsDeepEqual = 0;
  recordsA.forEach((line, index) => {
    const other = recordsB[index];
    if (other === line) recordLinesEqual += 1;
    const parsed = JSON.parse(line) as { searchPvsDeep?: unknown };
    if (!Object.hasOwn(parsed, "searchPvsDeep")) return;
    deepRows += 1;
    if (other !== undefined && JSON.stringify((JSON.parse(other) as { searchPvsDeep?: unknown }).searchPvsDeep) === JSON.stringify(parsed.searchPvsDeep)) searchPvsDeepEqual += 1;
  });
  return {
    metaEqual: metaA !== undefined && metaB !== undefined && metaWithoutRunKeys(JSON.parse(metaA) as Record<string, unknown>) === metaWithoutRunKeys(JSON.parse(metaB) as Record<string, unknown>),
    recordLines: Math.max(recordsA.length, recordsB.length),
    recordLinesEqual,
    deepRows,
    searchPvsDeepEqual,
  };
}

// ---- 同じ局面を続けて 2 回測る(§11 の (v))----

export interface MeasurementPairComparison {
  /** 参考評価(EngineReference)が同じ */
  referenceEqual: boolean;
  /** 両方に focus_baseline(multipv 1)がある */
  focusCompared: boolean;
  focusPvEqual: boolean;
  focusBoundsEqual: boolean;
}

export function compareMeasurementPair(first: EngineReferenceMeasurement, second: EngineReferenceMeasurement): MeasurementPairComparison {
  const a = focusOf(first.searchPvs);
  const b = focusOf(second.searchPvs);
  const focusCompared = a !== undefined && b !== undefined;
  return {
    referenceEqual: JSON.stringify(first.reference) === JSON.stringify(second.reference),
    focusCompared,
    focusPvEqual: focusCompared && JSON.stringify(a.pv) === JSON.stringify(b.pv),
    focusBoundsEqual: focusCompared && a.lowerbound === b.lowerbound && a.upperbound === b.upperbound,
  };
}

export interface MeasureTwicePlan {
  kifuId: string;
  /** 測る ready 行(昇順・重なりなし) */
  plies: number[];
  sfenByPly: Map<number, string>;
}

/**
 * measure-twice.ts が測る行を決める(エンジンを起こす前に呼ぶ)。`plies` を渡さなければ、記録の Failure Event の根(fromReadyPly)。
 * 渡した ply が ready 行に無ければ例外(書く前に止める)。
 */
export function planMeasureTwice(kifuId: string, input: RecordInput, rule: DiagnosisRule, plies?: readonly number[]): MeasureTwicePlan {
  const ready = input.records.filter((record) => record.phase === "ready");
  const sfenByPly = new Map(ready.map((record) => [record.ply, record.sfen]));
  const chosen = plies ?? diagnoseRecords(kifuId, input.records, rule, initialSfenOf(input.meta)).events.map((event) => event.fromReadyPly);
  const sorted = [...new Set(chosen)].sort((a, b) => a - b);
  const missing = sorted.filter((ply) => !sfenByPly.has(ply));
  if (missing.length > 0) throw new Error(`記録 ${kifuId} に ply ${missing.join(",")} の ready 行が無い`);
  return { kifuId, plies: sorted, sfenByPly };
}

// ---- 報告 ----

const rateCell = (rate: Rate): string => (rate.denominator === 0 ? "分母 0" : `${rate.numerator}/${rate.denominator}`);
const sumRates = (rates: readonly Rate[]): Rate => rates.reduce((total, rate) => rateOf(total.numerator + rate.numerator, total.denominator + rate.denominator), rateOf(0, 0));

const UNCOMPARABLE_LABELS: Record<UncomparableReason, string> = {
  notMeasuredGameEnd: "終局",
  notMeasuredInCheck: "王手中",
  notMeasurable: "測れなかった",
  unrecorded: "評価を記録していない",
  notEvaluation: "評価値でない",
  mateBefore: "直前が詰み",
  noPair: "組が無い",
};
const listCell = (keys: readonly string[]): string => `${keys.length}${keys.length > 0 ? `(${keys.join("・")})` : ""}`;
const uncomparableCell = (events: readonly UncomparableEvent[]): string =>
  `${events.length}${events.length > 0 ? `(${events.map((event) => `${event.key} ${UNCOMPARABLE_LABELS[event.reason]}`).join("・")})` : ""}`;
/** 合計の行: 件数と、理由ごとの件数(出てきた順) */
function uncomparableSumCell(events: readonly UncomparableEvent[]): string {
  if (events.length === 0) return "0";
  const counts = new Map<string, number>();
  for (const event of events) counts.set(UNCOMPARABLE_LABELS[event.reason], (counts.get(UNCOMPARABLE_LABELS[event.reason]) ?? 0) + 1);
  return `${events.length}(${[...counts].map(([label, count]) => `${label} ${count}`).join("・")})`;
}

export type StageRow = { kind: "counted"; comparison: StageComparison; deepRows: DeepRowComparison } | { kind: "notCounted"; kifuId: string; detail: string };

const NOTES = [
  "- **この件数は校正の材料であり、4M 一律をやめるかの判断ではない**(人間が承認する ― 計画 §9)",
  "- 突き合わせは組(直前の ready 行 → 直後の ready 行)で行う(D-COST §2.2)。同じ組に両方の Event があり当たり方が同じなら一致、当たり方だけ違えば「当たり方だけ違う」(取りこぼし・余計に入れない)",
  "- 「取りこぼし」は相手にだけある Event のうち、段 2 の同じ組を比べられた(差を取った・直後が詰み)もの。「余計」は逆向き(段 2 にだけあり、相手の同じ組を比べられたもの)",
  "- 「比べられない」は、もう片方の同じ組が比べられなかった(理由を並べる)か、組が無い(記録が途中で終わった等)。取りこぼし・余計にも率の分母にも入れない",
  "- 取りこぼし率 = 取りこぼし ÷(取りこぼし + 一致 + 当たり方だけ違う)。余計率も同じ形。計画 予-1 の外れ(取りこぼし 3 件以上)は「取りこぼし」の件数で判定する",
  "- counterfactual の状態の一致は、同じ分岐点に両方の Event があるものだけを分母にする(片方にしか無い Event は入れない)",
  "- 床(相手が段 1 そのもの)では、エンジンの状態の並びが本番の段 2 と違う(K-2)。行ごとの一致を保証するものではない",
];

export function renderScreenCalibration(rows: readonly StageRow[], runs: ReadonlyArray<{ kifuId: string; comparison: RescreenRunComparison }>, missing: { onlyBase: readonly string[]; onlyStage2: readonly string[] }): string[] {
  const lines: string[] = ["# 読み直し(D-SCREEN)の校正(STEP D-SCREEN-2。記録を読むだけ)", "", ...NOTES, ""];
  const counted = rows.filter((row): row is Extract<StageRow, { kind: "counted" }> => row.kind === "counted");

  lines.push("## Failure Event の集合(相手 → 段 2)", "");
  lines.push("| 対象 | 相手の Event | 段 2 の Event | 一致 | 当たり方だけ違う | 取りこぼし | 取りこぼし率 | 比べられない(相手にだけある) | 余計 | 余計率 | 比べられない(段 2 にだけある) | 死因①(相手) | 死因①(段 2) | 死因①の一致 |");
  lines.push("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
  for (const { comparison: c } of counted) {
    const e = c.events;
    lines.push(
      `| ${c.kifuId} | ${e.base} | ${e.stage2} | ${e.common} | ${listCell(e.kindsDiffer)} | ${listCell(e.missed)} | ${rateCell(e.missRate)} | ${uncomparableCell(e.missedUncomparable)} | ${listCell(e.extra)} | ${rateCell(e.extraRate)} | ${uncomparableCell(e.extraUncomparable)} | ${c.cause1.base} | ${c.cause1.stage2} | ${c.cause1.common} |`,
    );
  }
  if (counted.length > 1) {
    const sum = (pick: (c: StageComparison) => number) => counted.reduce((total, row) => total + pick(row.comparison), 0);
    const rates = (pick: (c: StageComparison) => Rate) => rateCell(sumRates(counted.map((row) => pick(row.comparison))));
    const all = (pick: (c: StageComparison) => readonly UncomparableEvent[]) => counted.flatMap((row) => pick(row.comparison));
    lines.push(
      `| 合計 | ${sum((c) => c.events.base)} | ${sum((c) => c.events.stage2)} | ${sum((c) => c.events.common)} | ${sum((c) => c.events.kindsDiffer.length)} | ${sum((c) => c.events.missed.length)} | ${rates((c) => c.events.missRate)} | ${uncomparableSumCell(all((c) => c.events.missedUncomparable))} | ${sum((c) => c.events.extra.length)} | ${rates((c) => c.events.extraRate)} | ${uncomparableSumCell(all((c) => c.events.extraUncomparable))} | ${sum((c) => c.cause1.base)} | ${sum((c) => c.cause1.stage2)} | ${sum((c) => c.cause1.common)} |`,
    );
  }
  lines.push("");

  lines.push("## 読み筋(counterfactual の状態の一致・深い組の 1 手目)", "");
  lines.push("| 対象 | 状態の一致(light) | 状態の一致(deep) | 深い組で 1 手目が bestmove と違う | うち標識付き | うち標識なし | 深い組 | 軽い組 | 深く測れなかった行を含む組 |");
  lines.push("|---|---|---|---|---|---|---|---|---|");
  for (const { comparison: c } of counted) {
    lines.push(
      `| ${c.kifuId} | ${rateCell(c.counterfactualState.light)} | ${rateCell(c.counterfactualState.deep)} | ${rateCell(c.deepFirstMove.notBestmove)} | ${rateCell(c.deepFirstMove.boundedNotBestmove)} | ${rateCell(c.deepFirstMove.unboundedNotBestmove)} | ${c.screen.deepPairs} | ${c.screen.lightPairs} | ${c.screen.deepUnavailable} |`,
    );
  }
  if (counted.length > 1) {
    const rates = (pick: (c: StageComparison) => Rate) => rateCell(sumRates(counted.map((row) => pick(row.comparison))));
    const sum = (pick: (c: StageComparison) => number) => counted.reduce((total, row) => total + pick(row.comparison), 0);
    lines.push(
      `| 合計 | ${rates((c) => c.counterfactualState.light)} | ${rates((c) => c.counterfactualState.deep)} | ${rates((c) => c.deepFirstMove.notBestmove)} | ${rates((c) => c.deepFirstMove.boundedNotBestmove)} | ${rates((c) => c.deepFirstMove.unboundedNotBestmove)} | ${sum((c) => c.screen.deepPairs)} | ${sum((c) => c.screen.lightPairs)} | ${sum((c) => c.screen.deepUnavailable)} |`,
    );
  }
  lines.push("");

  lines.push("## 読み直した行と相手の同じ行(床の (i)・(vi))", "");
  lines.push("| 対象 | 読み直した行 | 相手に行が無い | 参考評価が同じ | 読み筋を比べた行 | 長さが同じ | 標識が同じ | 1 手目が同じ |");
  lines.push("|---|---|---|---|---|---|---|---|");
  for (const row of counted) {
    const d = row.deepRows;
    lines.push(`| ${row.comparison.kifuId} | ${d.deepRows} | ${d.noCounterpart} | ${d.referenceEqual} | ${d.pvCompared} | ${d.pvLengthEqual} | ${d.pvBoundsEqual} | ${d.pvFirstMoveEqual} |`);
  }
  lines.push("");

  if (runs.length > 0) {
    lines.push("## 同じ入力で 2 回回した rescreen(床の (iii)・(iv))", "");
    lines.push("| 対象 | meta が同じ(deepRun の startedAt・gitHead・dirty を除く) | record 行 | バイト一致 | 読み直した行 | searchPvsDeep が同じ |");
    lines.push("|---|---|---|---|---|---|");
    for (const { kifuId, comparison: r } of runs) {
      lines.push(`| ${kifuId} | ${r.metaEqual ? "同じ" : "違う"} | ${r.recordLines} | ${r.recordLinesEqual} | ${r.deepRows} | ${r.searchPvsDeepEqual} |`);
    }
    lines.push("");
  }

  lines.push("## 数えなかった記録", "");
  const notCounted = rows.filter((row): row is Extract<StageRow, { kind: "notCounted" }> => row.kind === "notCounted");
  if (notCounted.length === 0 && missing.onlyBase.length === 0 && missing.onlyStage2.length === 0) lines.push("- 無し");
  for (const row of notCounted) lines.push(`- 数えられなかった: ${row.kifuId}(${row.detail})`);
  for (const name of missing.onlyBase) lines.push(`- 相手にしか無い(段 2 は回していない): ${name}`);
  for (const name of missing.onlyStage2) lines.push(`- 段 2 にしか無い(相手は回していない): ${name}`);
  lines.push("");
  return lines;
}
