// STEP BASE(docs/STEP_BASE_PLAN_2026-09-21.md §1・§2)。向きを逆にした物差し: まず pool(その人を除いた全員)の組を合わせて
// 枠ごとの崩れ率を基準値にし、その人の率が基準値から外れている枠を候補として出す純粋関数。
//
// 【このファイルがやること】
// - 計画 §1.1 の 24 の枠(A 2・B 3・A×B 6・C 7・優勢×C 6)への組の振り分け(`FRAMES`)。
//   崩れ・分母・分母から外す理由は lib/gate.ts の `collapseTallyOf`・`entriesOf` をそのまま再利用する(数え方をここで複製しない)。
// - B(時期)は lib/reportData.ts の `phaseOf`(early < 1/3・mid < 2/3・late。境の扱いも phaseOf のまま)をそのまま使う。
// - C(手の種類)は `counterfactual.actual.userMoveFacts` を、lib/conditions/ahead_move_into_own_king_zone_v1.ts と同じ欄・同じ門
//   (`counterfactual.state === "compared"`)で読む。欄が null な組は、その軸(C 全体)では数えず、件数を別に出す。
// - 外れの印(candidate・lower)の 3 条件(計画 §2)。値は `GATE_VALUES` を読むだけ(ここに数を置かない)。
//   比・差の計算は lib/gate.ts の `rateRatioMet`・`rateDiffMet`(G-2 と同じ整数の式)をそのまま使う。
// - pool の人ごとの比べ(条件 3)は、分母 0 の人をその枠の比べから外す(README に書く)。
//
// 【このファイルが絶対にやらないこと】
// - 新しい閾値・判定語を置くこと(GATE_VALUES 以外の数を書かない)。エンジン・LLM・ファイルの読み書き
// - 枠を結果を見てから足すこと(24 で固定)。名前・手・局面・SFEN を欄に持つこと
//
// 【判断的知識】無い。GATE_VALUES・崩れの定義・条件式の欄の読み方は、承認済みの既存の値をそのまま読むだけ(新しく確定しない)。

import { isAbsolute } from "node:path";
import type { MetaLine } from "../invariants/types.js";
import type { PairRow } from "./condition.js";
import {
  collapseTallyOf,
  entriesOf,
  GATE_VALUES,
  rateDiffMet,
  rateRatioMet,
  type CollapseTally,
  type Entry,
  type GatePairsGame,
  type GateValues,
  type RateCount,
} from "./gate.js";
import { PERSON_LABEL } from "./gateOutput.js";
import { phaseOf } from "./reportData.js";

// ---- 入力(1 局ぶん・1 人ぶん)----

/** `lib/gate.ts` の `GatePairsGame` に、軸 B(時期)が読む総手数を足しただけ(組の作り方は変えない)。 */
export interface BaselineGame extends GatePairsGame {
  /** `branchPly` と同じ向き(記録の ply。本人の向きへ戻す前)の総手数。取れなければ null(計画 §1.1 の B、件数を別に出す)。 */
  totalMoves: number | null;
}

export interface BaselinePerson {
  label: string;
  games: readonly BaselineGame[];
}

// ---- 軸の枠(計画 §1.1。24 で固定)----

export type AxisAKey = "ahead" | "level";
export type AxisBKey = "early" | "mid" | "late";
export type AxisCKey = "drop" | "capture" | "promotion" | "kingMove" | "ownZone" | "oppZone" | "none";

export const AXIS_A_KEYS: readonly AxisAKey[] = ["ahead", "level"];
export const AXIS_B_KEYS: readonly AxisBKey[] = ["early", "mid", "late"];
export const AXIS_C_KEYS: readonly AxisCKey[] = ["drop", "capture", "promotion", "kingMove", "ownZone", "oppZone", "none"];
const AXIS_C_KEYS_WITHOUT_NONE: readonly AxisCKey[] = AXIS_C_KEYS.filter((key) => key !== "none");

const AXIS_A_LABEL: Readonly<Record<AxisAKey, string>> = { ahead: "優勢", level: "互角" };
const AXIS_B_LABEL: Readonly<Record<AxisBKey, string>> = { early: "早い", mid: "中", late: "遅い" };
const AXIS_C_LABEL: Readonly<Record<AxisCKey, string>> = {
  drop: "打つ手",
  capture: "駒を取る手",
  promotion: "成る手",
  kingMove: "玉を動かす手",
  ownZone: "自玉のそばへ動かす手",
  oppZone: "相手玉のそばへ動かす手",
  none: "どれでもない手",
};

/** `standingPair.before` が ahead・level のどちらでもなければ null(behind・未定は軸 A の枠に入れない ― lib/gate.ts の collapseOf と同じ判断)。 */
function axisAOf(pair: PairRow): AxisAKey | null {
  const before = pair.standingPair.before;
  return before === "ahead" || before === "level" ? before : null;
}

/** `phaseOf`(lib/reportData.ts)をそのまま使う。総手数が無い・0 以下なら null。 */
function axisBOf(pair: PairRow, totalMoves: number | null): AxisBKey | null {
  if (totalMoves === null || totalMoves <= 0) return null;
  return phaseOf(pair.branchPly, totalMoves);
}

interface AxisCFacts {
  drop: boolean;
  capture: boolean;
  promotion: boolean;
  kingMove: boolean;
  ownZone: boolean;
  oppZone: boolean;
}

/**
 * `counterfactual.actual.userMoveFacts` から 6 つの事実を読む。門は lib/conditions/ahead_move_into_own_king_zone_v1.ts と同じ
 * `counterfactual.state === "compared"`。zone の 2 欄(toInOwnKingZone・toInOpponentKingZone)が null なら、
 * 「どれでもない手」を含め軸 C 全体を判定できない(計画: 欄が null な組は、その軸では数えない)。
 */
function axisCFactsOf(pair: PairRow): AxisCFacts | null {
  if (pair.counterfactual.state !== "compared") return null;
  const facts = pair.counterfactual.actual.userMoveFacts;
  if (facts.toInOwnKingZone === null || facts.toInOpponentKingZone === null) return null;
  return {
    drop: facts.drop,
    capture: facts.capturedRole !== null,
    promotion: facts.promotion,
    kingMove: facts.kingMove,
    ownZone: facts.toInOwnKingZone,
    oppZone: facts.toInOpponentKingZone,
  };
}

/** C は重なってよい(計画 §1.1)。「どれでもない手」は 6 つとも偽のときだけ。 */
function axisCKeysOf(facts: AxisCFacts): AxisCKey[] {
  const keys: AxisCKey[] = [];
  if (facts.drop) keys.push("drop");
  if (facts.capture) keys.push("capture");
  if (facts.promotion) keys.push("promotion");
  if (facts.kingMove) keys.push("kingMove");
  if (facts.ownZone) keys.push("ownZone");
  if (facts.oppZone) keys.push("oppZone");
  if (keys.length === 0) keys.push("none");
  return keys;
}

type Membership = "in" | "out" | "unclassifiable";

function membershipOfA(pair: PairRow, key: AxisAKey): Membership {
  const a = axisAOf(pair);
  return a === null ? "unclassifiable" : a === key ? "in" : "out";
}

function membershipOfB(pair: PairRow, totalMoves: number | null, key: AxisBKey): Membership {
  const b = axisBOf(pair, totalMoves);
  return b === null ? "unclassifiable" : b === key ? "in" : "out";
}

function membershipOfC(pair: PairRow, key: AxisCKey): Membership {
  const facts = axisCFactsOf(pair);
  return facts === null ? "unclassifiable" : axisCKeysOf(facts).includes(key) ? "in" : "out";
}

function combine(a: Membership, b: Membership): Membership {
  if (a === "unclassifiable" || b === "unclassifiable") return "unclassifiable";
  return a === "in" && b === "in" ? "in" : "out";
}

export type FrameAxis = "A" | "B" | "AxB" | "C" | "AxC";

interface FrameSpec {
  id: string;
  axis: FrameAxis;
  label: string;
  classify: (pair: PairRow, totalMoves: number | null) => Membership;
}

/** 計画 §1.1 の 24 の枠。結果を見てから足さない(計画 §6)。 */
export const FRAMES: readonly FrameSpec[] = [
  ...AXIS_A_KEYS.map((key): FrameSpec => ({ id: `A_${key}`, axis: "A", label: AXIS_A_LABEL[key], classify: (pair) => membershipOfA(pair, key) })),
  ...AXIS_B_KEYS.map((key): FrameSpec => ({ id: `B_${key}`, axis: "B", label: AXIS_B_LABEL[key], classify: (pair, total) => membershipOfB(pair, total, key) })),
  ...AXIS_A_KEYS.flatMap((a) =>
    AXIS_B_KEYS.map(
      (b): FrameSpec => ({
        id: `AxB_${a}_${b}`,
        axis: "AxB",
        label: `${AXIS_A_LABEL[a]}・${AXIS_B_LABEL[b]}`,
        classify: (pair, total) => combine(membershipOfA(pair, a), membershipOfB(pair, total, b)),
      }),
    ),
  ),
  ...AXIS_C_KEYS.map((key): FrameSpec => ({ id: `C_${key}`, axis: "C", label: AXIS_C_LABEL[key], classify: (pair) => membershipOfC(pair, key) })),
  ...AXIS_C_KEYS_WITHOUT_NONE.map(
    (key): FrameSpec => ({
      id: `AxC_ahead_${key}`,
      axis: "AxC",
      label: `優勢・${AXIS_C_LABEL[key]}`,
      classify: (pair) => combine(membershipOfA(pair, "ahead"), membershipOfC(pair, key)),
    }),
  ),
];

if (FRAMES.length !== 24) throw new Error(`枠は 24 で固定(計画 §1.1)。今 ${FRAMES.length}`);

// ---- 集計(組 → 枠 → 崩れ)----

interface Sample {
  entry: Entry;
  totalMoves: number | null;
}

/** `entriesOf`(lib/gate.ts)で組を並べ、局ごとの総手数を添える。同じ kifuId が 2 本あれば `entriesOf` が例外(既存の不変条件)。 */
function samplesOf(games: readonly BaselineGame[]): Sample[] {
  const totalByKifuId = new Map(games.map((game) => [game.kifuId, game.totalMoves]));
  return entriesOf(games)
    .flat()
    .map((entry) => ({ entry, totalMoves: totalByKifuId.get(entry.kifuId) ?? null }));
}

function percentOf(count: { collapsed: number; denominator: number }): number | null {
  return count.denominator === 0 ? null : (100 * count.collapsed) / count.denominator;
}

function bucketTallyOf(samples: readonly Sample[], classify: FrameSpec["classify"]): CollapseTally {
  return collapseTallyOf(samples.filter((sample) => classify(sample.entry.pair, sample.totalMoves) === "in").map((sample) => sample.entry));
}

/** `a` の率が `b` の率より真に高いか(整数の交差の積。両方の分母が正であること)。 */
function rateGreaterThan(a: RateCount, b: RateCount): boolean {
  return a.collapsed * b.denominator > b.collapsed * a.denominator;
}

// ---- 出力 ----

export interface FrameRate {
  collapsed: number;
  denominator: number;
  ratePercent: number | null;
}

export interface FrameSubjectRate extends FrameRate {
  gamesWithCollapse: number;
}

export interface FramePoolMemberRate extends FrameRate {
  label: string;
}

export interface FrameResult {
  id: string;
  axis: FrameAxis;
  label: string;
  subject: FrameSubjectRate;
  baseline: FrameRate;
  poolByPerson: FramePoolMemberRate[];
  candidate: boolean;
  lower: boolean;
  /** candidate が false のときに満たさなかった条件(candidate が true なら空)。 */
  reasonsCandidateNotMet: string[];
  /** lower が false のときに満たさなかった条件(lower が true なら空)。 */
  reasonsLowerNotMet: string[];
}

export interface UnclassifiedCounts {
  /** その軸のどの枠にも入らなかった組の数(person・pool 合わせた件数を分けて出す)。 */
  subjectPairs: number;
  poolPairs: number;
}

export interface BaselineReport {
  person: { label: string; games: number };
  pool: Array<{ label: string; games: number }>;
  gateValues: GateValues;
  frames: FrameResult[];
  unclassified: {
    A: UnclassifiedCounts;
    B: UnclassifiedCounts & { subjectGames: number; poolGames: number };
    C: UnclassifiedCounts;
  };
}

function reasonsOf(cond1Denominator: boolean, cond1Games: boolean, ratioMet: boolean, diffMet: boolean, poolMet: boolean, poolReason: string): string[] {
  return [
    ...(cond1Denominator ? [] : ["subjectDenominatorBelowMin"]),
    ...(cond1Games ? [] : ["subjectGamesWithCollapseBelowMin"]),
    ...(ratioMet ? [] : ["ratioNotMet"]),
    ...(diffMet ? [] : ["diffNotMet"]),
    ...(poolMet ? [] : [poolReason]),
  ];
}

/**
 * STEP BASE(計画 §2)。`person` を除いた `pool` を合わせて基準値にし、枠ごとに `person` が外れているかを出す。
 * `pool` に `person` と同じラベルがある・`pool` の中で同じラベルが 2 回ある・`person` と `pool` に同じ kifuId の局があれば例外
 * (呼び出し側の CLI で止める入力の確かめと同じ判断を、ここでも純粋関数の不変条件として確かめる)。
 */
export function baselineReportOf(person: BaselinePerson, pool: readonly BaselinePerson[], values: GateValues = GATE_VALUES): BaselineReport {
  if (!PERSON_LABEL.test(person.label)) throw new Error(`person のラベルが p1・p2 の形でない: ${person.label}`);
  for (const group of pool) {
    if (!PERSON_LABEL.test(group.label)) throw new Error(`pool のラベルが p1・p2 の形でない: ${group.label}`);
    if (group.label === person.label) throw new Error(`pool に person と同じラベルがある: ${person.label}`);
  }
  const poolLabels = pool.map((group) => group.label);
  const duplicateLabel = poolLabels.find((label, index) => poolLabels.indexOf(label) !== index);
  if (duplicateLabel !== undefined) throw new Error(`pool に同じラベルが 2 回ある: ${duplicateLabel}`);
  const subjectKifuIds = new Set(person.games.map((game) => game.kifuId));
  const overlap = pool.flatMap((group) => group.games).find((game) => subjectKifuIds.has(game.kifuId));
  if (overlap !== undefined) throw new Error(`person と pool に同じ kifuId の記録がある: ${overlap.kifuId}`);

  const subjectSamples = samplesOf(person.games);
  const poolSamplesByPerson = pool.map((group) => ({ label: group.label, samples: samplesOf(group.games) }));
  const poolSamplesAll = poolSamplesByPerson.flatMap((group) => group.samples);

  const frames: FrameResult[] = FRAMES.map((frame) => {
    const subjectTally = bucketTallyOf(subjectSamples, frame.classify);
    const baselineTally = bucketTallyOf(poolSamplesAll, frame.classify);
    const subjectRC: RateCount = { collapsed: subjectTally.collapsed, denominator: subjectTally.denominator };
    const baselineRC: RateCount = { collapsed: baselineTally.collapsed, denominator: baselineTally.denominator };

    const poolByPerson: FramePoolMemberRate[] = poolSamplesByPerson.map((group) => {
      const tally = bucketTallyOf(group.samples, frame.classify);
      return { label: group.label, collapsed: tally.collapsed, denominator: tally.denominator, ratePercent: percentOf(tally) };
    });
    const eligiblePool = poolByPerson.filter((member) => member.denominator > 0);

    const cond1Denominator = subjectRC.denominator >= values.minTruePairs;
    const cond1Games = subjectTally.gamesWithCollapse >= values.minGames;

    const candidateRatio = rateRatioMet(subjectRC, baselineRC, values.minRateRatio);
    const candidateDiff = rateDiffMet(subjectRC, baselineRC, values.minRateDiffPoints);
    const candidatePool = eligiblePool.every((member) => rateGreaterThan(subjectRC, { collapsed: member.collapsed, denominator: member.denominator }));
    const reasonsCandidateNotMet = reasonsOf(cond1Denominator, cond1Games, candidateRatio, candidateDiff, candidatePool, "poolMemberEqualOrHigher");

    const lowerRatio = rateRatioMet(baselineRC, subjectRC, values.minRateRatio);
    const lowerDiff = rateDiffMet(baselineRC, subjectRC, values.minRateDiffPoints);
    const lowerPool = eligiblePool.every((member) => rateGreaterThan({ collapsed: member.collapsed, denominator: member.denominator }, subjectRC));
    const reasonsLowerNotMet = reasonsOf(cond1Denominator, cond1Games, lowerRatio, lowerDiff, lowerPool, "poolMemberEqualOrLower");

    return {
      id: frame.id,
      axis: frame.axis,
      label: frame.label,
      subject: { collapsed: subjectRC.collapsed, denominator: subjectRC.denominator, ratePercent: percentOf(subjectRC), gamesWithCollapse: subjectTally.gamesWithCollapse },
      baseline: { collapsed: baselineRC.collapsed, denominator: baselineRC.denominator, ratePercent: percentOf(baselineRC) },
      poolByPerson,
      candidate: reasonsCandidateNotMet.length === 0,
      lower: reasonsLowerNotMet.length === 0,
      reasonsCandidateNotMet,
      reasonsLowerNotMet,
    };
  });

  const countUnclassified = (samples: readonly Sample[], axisOf: (pair: PairRow, totalMoves: number | null) => unknown): number =>
    samples.filter((sample) => axisOf(sample.entry.pair, sample.totalMoves) === null).length;
  const countGamesWithoutTotal = (games: readonly BaselineGame[]): number => games.filter((game) => game.totalMoves === null || game.totalMoves <= 0).length;

  return {
    person: { label: person.label, games: person.games.length },
    pool: pool.map((group) => ({ label: group.label, games: group.games.length })),
    gateValues: values,
    frames,
    unclassified: {
      A: { subjectPairs: countUnclassified(subjectSamples, (pair) => axisAOf(pair)), poolPairs: countUnclassified(poolSamplesAll, (pair) => axisAOf(pair)) },
      B: {
        subjectPairs: countUnclassified(subjectSamples, (pair, total) => axisBOf(pair, total)),
        poolPairs: countUnclassified(poolSamplesAll, (pair, total) => axisBOf(pair, total)),
        subjectGames: countGamesWithoutTotal(person.games),
        poolGames: countGamesWithoutTotal(pool.flatMap((group) => group.games)),
      },
      C: { subjectPairs: countUnclassified(subjectSamples, (pair) => axisCFactsOf(pair)), poolPairs: countUnclassified(poolSamplesAll, (pair) => axisCFactsOf(pair)) },
    },
  };
}

// ---- 入力の確かめ(CLI 側が読んだ記録を渡す。gate.ts の gateInputProblems と同じ流儀。計画 §2・§6)----

export interface BaselineInputEntry {
  /** 表示に使う名前(ファイルのパス) */
  name: string;
  /** 作業ツリーの根からの相対パス */
  path: string;
  kifuId: string;
  sha256: string;
  meta: MetaLine | undefined;
  errorLines: number;
}

export interface BaselineInputGroup {
  label: string;
  entries: readonly BaselineInputEntry[];
}

/**
 * 入力の確かめ(gate.ts の `gateInputProblems` と同じ判断を、person 1 つ + pool 複数の形に合わせて書き直したもの)。
 * 問題を 1 件 1 文で返す(空なら通す)。referenceNodes は person・pool のすべての記録でそろうこと。そろえば `referenceNodes` を返す。
 */
export function baselineInputProblems(person: BaselineInputGroup, pool: readonly BaselineInputGroup[]): { problems: string[]; referenceNodes: number | null } {
  const problems: string[] = [];
  if (!PERSON_LABEL.test(person.label)) problems.push(`--person は p1・p2 の形の記号(名前を書かない): ${JSON.stringify(person.label)}`);
  for (const group of pool) {
    if (!PERSON_LABEL.test(group.label)) problems.push(`--pool のラベルは p1・p2 の形の記号(名前を書かない): ${JSON.stringify(group.label)}`);
  }
  if (pool.some((group) => group.label === person.label)) problems.push(`--pool に --person と同じラベルがある: ${person.label}`);
  const poolLabels = pool.map((group) => group.label);
  const duplicateLabel = poolLabels.find((label, index) => poolLabels.indexOf(label) !== index);
  if (duplicateLabel !== undefined) problems.push(`--pool に同じラベルが 2 回ある: ${duplicateLabel}`);
  if (person.entries.length === 0) problems.push("--material の記録が無い");
  for (const group of pool) if (group.entries.length === 0) problems.push(`--pool ${group.label} の記録が無い`);

  const all = [person, ...pool].flatMap((group) => group.entries);
  // gateOutput.ts の gateInputProblems と同じ確かめ(監査 93 の R-1)
  for (const entry of all) {
    if (isAbsolute(entry.path) || /^\.\.(\/|\\|$)/.test(entry.path)) problems.push(`${entry.name} は作業ツリーの根の外にある(根の外のパスを記録に書かない): ${entry.path}`);
  }
  for (const key of ["name", "sha256", "kifuId"] as const) {
    const seen = new Map<string, number>();
    for (const entry of all) seen.set(entry[key], (seen.get(entry[key]) ?? 0) + 1);
    for (const [value, count] of seen) if (count > 1) problems.push(`同じ ${key} の記録が ${count} 本ある(--material と --pool の重なりを含む): ${value}`);
  }

  const nodes = new Set<unknown>();
  for (const entry of all) {
    if (entry.meta === undefined) {
      problems.push(`${entry.name} に meta の行が無い`);
      continue;
    }
    const referenceNodes = (entry.meta as { referenceNodes?: unknown }).referenceNodes;
    if (typeof referenceNodes !== "number" || !Number.isInteger(referenceNodes) || referenceNodes <= 0) problems.push(`${entry.name} の meta.referenceNodes が正の整数でない`);
    nodes.add(referenceNodes);
    if (entry.errorLines > 0) problems.push(`${entry.name} に error 行が ${entry.errorLines} 行ある(途中で止まった記録は数えない)`);
  }
  if (nodes.size > 1) problems.push(`referenceNodes がそろわない(${[...nodes].map(String).join(", ")})。1 回の集計の中で同じ探索の値だけを使う`);
  const only = [...nodes][0];
  return { problems, referenceNodes: nodes.size === 1 && typeof only === "number" && Number.isInteger(only) && only > 0 ? only : null };
}

// ---- Markdown(標準出力。計画 §2: 名前・手・局面は出さない)----

const rateCell = (rate: FrameRate): string => (rate.denominator === 0 ? `${rate.collapsed} / 0` : `${rate.collapsed} / ${rate.denominator}(${rate.ratePercent!.toFixed(1)}%)`);

export function renderBaselineMarkdown(report: BaselineReport): string[] {
  const lines: string[] = [
    "# 全員に共通の基準値と、その人が外れている所(STEP BASE)",
    "",
    `- 人のラベル: ${report.person.label}(記録 ${report.person.games} 局)`,
    `- pool: ${report.pool.map((group) => `${group.label}(${group.games} 局)`).join("・")}`,
    `- GATE_VALUES: minTruePairs ${report.gateValues.minTruePairs}・minGames ${report.gateValues.minGames}・minRateRatio ${report.gateValues.minRateRatio}・minRateDiffPoints ${report.gateValues.minRateDiffPoints}`,
    `- 判定できなかった組: A(その人 ${report.unclassified.A.subjectPairs}・pool ${report.unclassified.A.poolPairs})・B(その人 ${report.unclassified.B.subjectPairs}・pool ${report.unclassified.B.poolPairs}・総手数の無い局 その人 ${report.unclassified.B.subjectGames}・pool ${report.unclassified.B.poolGames})・C(その人 ${report.unclassified.C.subjectPairs}・pool ${report.unclassified.C.poolPairs})`,
    "",
    "| 枠 | 軸 | その人 崩れ/分母(率) | 崩れのある局 | 基準値 崩れ/分母(率) | candidate | lower | 満たさなかった条件 |",
    "|---|---|---|---|---|---|---|---|",
  ];
  for (const frame of report.frames) {
    const reasons = frame.candidate && frame.lower ? "―" : [...(frame.candidate ? [] : frame.reasonsCandidateNotMet.map((r) => `候補:${r}`)), ...(frame.lower ? [] : frame.reasonsLowerNotMet.map((r) => `低め:${r}`))].join("・") || "―";
    lines.push(`| ${frame.label} | ${frame.axis} | ${rateCell(frame.subject)} | ${frame.subject.gamesWithCollapse} | ${rateCell(frame.baseline)} | ${frame.candidate} | ${frame.lower} | ${reasons} |`);
  }
  return lines;
}
