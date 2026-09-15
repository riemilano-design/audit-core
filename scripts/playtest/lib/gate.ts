// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §4・§5)。全ての手の組(lib/diagnosisMoment.ts の allPairsOf)に条件式 1 本を当てた判定から、
// 真の組と偽の組の崩れ率を件数で数え(`gateTallyOf`)、人間が確定した Gate の値で「満たす / 根拠不足」を出す(`gateVerdictOf`)純粋関数。
//
// 【このファイルがやること】
// - 崩れ(第一の定義): 組の直前の状態が ahead・level で、直後の状態が順序 ahead > level > behind で下なら崩れ。分母から外す組は理由つきで数える
//   (理由の順は 直前が未定 → 直後が未定 → 直前が behind(`cannotFall`)。司令塔の決定 T-4)
// - 5 手以内(参考): 直前の行に対して ply +2・+4・+6 の行のどれかで状態が下がったか。窓の行が足りない組は `windowShort` で外す(T-1)
// - 崩れ率の比べは件数の整数で(R-4)。偽の崩れが 0 のとき、比の条件は真の崩れ ≥ 1 で満たす(Q-5 の文どおり。T-5)
// - Gate の 4 項目(G-1〜G-4)と verdict の文 2 つ
//
// 【このファイルが絶対にやらないこと】
// - 条件式の中身・閾値を置くこと(定義は lib/conditions/。Gate の値は人間の確定 2fe81c3 を GATE_VALUES に写しただけ)
// - Gate の文のほかの評価語・「この人は〜」。draft の定義に verdict を出すこと(Q-7)
// - 率を浮動小数で引いて比べること(表示用の率は別に並べる)。エンジン・LLM・ファイルの読み書き
//
// 【判断的知識】Gate の値と「崩れ」の定義は人間の承認(2fe81c3・359961d・e64407b)。司令塔の読み (1)〜(4) と T-1〜T-10 は計画 §10・§13。

import { judgeCondition, judgeConditionPvSide, type ConditionDefinition, type ConditionJudgement, type LoadedCondition, type MissingReason, type PairRow, type PvSideJudgement } from "./condition.js";
import type { Standing, StandingPair } from "./standing.js";

// ---- 崩れ(計画 §4)----

type Rank = "ahead" | "level" | "behind";
const RANK_ORDER: Readonly<Record<Rank, number>> = { ahead: 2, level: 1, behind: 0 };
const isRank = (standing: Standing | undefined): standing is Rank => typeof standing === "string";

export type CollapseExcludedReason = "beforeUndetermined" | "afterUndetermined" | "cannotFall";
export type CollapseTransition = "aheadToLevel" | "levelToBehind" | "aheadToBehind";

export type Collapse =
  /** 分母に入る組。`transition` が null なら崩れでない */
  | { counted: true; before: "ahead" | "level"; transition: CollapseTransition | null }
  | { counted: false; reason: CollapseExcludedReason };

export function collapseOf(pair: StandingPair): Collapse {
  const { before, after } = pair;
  if (!isRank(before)) return { counted: false, reason: "beforeUndetermined" };
  if (!isRank(after)) return { counted: false, reason: "afterUndetermined" };
  if (before === "behind") return { counted: false, reason: "cannotFall" };
  if (RANK_ORDER[after] >= RANK_ORDER[before]) return { counted: true, before, transition: null };
  if (before === "level") return { counted: true, before, transition: "levelToBehind" };
  return { counted: true, before, transition: after === "level" ? "aheadToLevel" : "aheadToBehind" };
}

export type Within5ExcludedReason = "beforeUndetermined" | "cannotFall" | "windowShort";
/** 5 手以内(参考)で見る行の、直前の行からの ply の差(ready 行の間隔 2 に依る ― L-2) */
export const WITHIN5_OFFSETS = [2, 4, 6] as const;

export type Within5 =
  /** `dropPly` は最初に下がった行の ply。下がらなければ null */
  | { counted: true; dropPly: number | null }
  | { counted: false; reason: Within5ExcludedReason };

/** 窓の中の行が未定なら、その行は「下がった」に数えない */
export function within5Of(fromReadyPly: number, before: Standing, rowStandings: ReadonlyMap<number, Standing>): Within5 {
  if (!isRank(before)) return { counted: false, reason: "beforeUndetermined" };
  if (before === "behind") return { counted: false, reason: "cannotFall" };
  const plies = WITHIN5_OFFSETS.map((offset) => fromReadyPly + offset);
  if (plies.some((ply) => !rowStandings.has(ply))) return { counted: false, reason: "windowShort" };
  const dropPly = plies.find((ply) => {
    const standing = rowStandings.get(ply);
    return isRank(standing) && RANK_ORDER[standing] < RANK_ORDER[before];
  });
  return { counted: true, dropPly: dropPly ?? null };
}

// ---- 集計(計画 §4)----

/** 1 局ぶんの組(allPairsOf の戻り) */
export interface GatePairsGame {
  kifuId: string;
  pairs: readonly PairRow[];
  movesMissing: number;
  rowStandings: ReadonlyArray<{ ply: number; standing: Standing }>;
}

export interface RateCount {
  collapsed: number;
  denominator: number;
}

export interface CollapseTally {
  /** この群の組の数(分母から外した組を含む) */
  pairs: number;
  collapsed: number;
  denominator: number;
  excluded: Record<CollapseExcludedReason, number>;
  transitions: Record<CollapseTransition, number>;
  /** 直前の状態ごと(R-2 (a)) */
  byBefore: { ahead: RateCount; level: RateCount };
  /** 分母に入る組がある局の数と、局ごとのその組の数(読み (4)。数が 0 の局は並べない) */
  gamesWithDenominator: number;
  denominatorByGame: Array<{ kifuId: string; pairs: number }>;
  /** 組がある局の数(分母から外した組を含む。C-2 で別に並べる) */
  gamesWithPairs: number;
  /** 崩れが 1 組以上ある局の数(予-4) */
  gamesWithCollapse: number;
  within5: {
    dropped: number;
    denominator: number;
    excluded: Record<Within5ExcludedReason, number>;
    /** 同じ崩れ (kifuId, 最初に下がった行の ply) を 1 件に数えた件数 */
    distinctDrops: number;
    distinctDropsByGame: Array<{ kifuId: string; drops: number }>;
  };
}

export interface JudgedPair {
  actual: ConditionJudgement;
  pv: PvSideJudgement;
}

export type PvSideTally =
  /** `counterfactual.state` が compared で、実戦の側と読み筋の側の両方が判定できた組 `n` と、その中の実戦の真 `actualTrue`・読み筋の真 `pvTrue` */
  | { state: "applicable"; n: number; actualTrue: number; pvTrue: number }
  | { state: "notApplicable"; reasons: Extract<PvSideJudgement, { state: "notApplicable" }>["reasons"] };

export interface GateTally {
  games: number;
  judgements: {
    match: number;
    noMatch: number;
    undecidable: number;
    /** (欄, 理由) ごとの行の数。1 行が複数の欄で判定不能なら、それぞれに数える */
    undecidableReasons: Array<{ path: string; reason: string; rows: number }>;
    movesMissing: number;
  };
  /** 全ての組(判定に依らない基準値。T-6) */
  all: CollapseTally;
  truePairs: CollapseTally;
  falsePairs: CollapseTally;
  /** 表示用(比べには使わない)。分母が 0 なら null。`ratio` は偽の崩れが 0 のとき null */
  rates: { truePercent: number | null; falsePercent: number | null; ratio: number | null; diffPoints: number | null };
  pvSide: PvSideTally;
}

type Entry = { kifuId: string; pair: PairRow; rows: ReadonlyMap<number, Standing> };

function emptyCollapseTally(): CollapseTally {
  return {
    pairs: 0,
    collapsed: 0,
    denominator: 0,
    excluded: { beforeUndetermined: 0, afterUndetermined: 0, cannotFall: 0 },
    transitions: { aheadToLevel: 0, levelToBehind: 0, aheadToBehind: 0 },
    byBefore: { ahead: { collapsed: 0, denominator: 0 }, level: { collapsed: 0, denominator: 0 } },
    gamesWithDenominator: 0,
    denominatorByGame: [],
    gamesWithPairs: 0,
    gamesWithCollapse: 0,
    within5: { dropped: 0, denominator: 0, excluded: { beforeUndetermined: 0, cannotFall: 0, windowShort: 0 }, distinctDrops: 0, distinctDropsByGame: [] },
  };
}

function collapseTallyOf(entries: readonly Entry[]): CollapseTally {
  const tally = emptyCollapseTally();
  const denominatorByGame = new Map<string, number>();
  const gamesWithPairs = new Set<string>();
  const gamesWithCollapse = new Set<string>();
  const drops = new Map<string, Set<number>>();
  for (const { kifuId, pair, rows } of entries) {
    tally.pairs += 1;
    gamesWithPairs.add(kifuId);
    const collapse = collapseOf(pair.standingPair);
    if (!collapse.counted) {
      tally.excluded[collapse.reason] += 1;
    } else {
      tally.denominator += 1;
      tally.byBefore[collapse.before].denominator += 1;
      denominatorByGame.set(kifuId, (denominatorByGame.get(kifuId) ?? 0) + 1);
      if (collapse.transition !== null) {
        tally.collapsed += 1;
        gamesWithCollapse.add(kifuId);
        tally.byBefore[collapse.before].collapsed += 1;
        tally.transitions[collapse.transition] += 1;
      }
    }
    const within5 = within5Of(pair.fromReadyPly, pair.standingPair.before, rows);
    if (!within5.counted) {
      tally.within5.excluded[within5.reason] += 1;
    } else {
      tally.within5.denominator += 1;
      if (within5.dropPly !== null) {
        tally.within5.dropped += 1;
        const plies = drops.get(kifuId) ?? new Set<number>();
        plies.add(within5.dropPly);
        drops.set(kifuId, plies);
      }
    }
  }
  tally.denominatorByGame = [...denominatorByGame].map(([kifuId, pairs]) => ({ kifuId, pairs }));
  tally.gamesWithDenominator = tally.denominatorByGame.length;
  tally.gamesWithPairs = gamesWithPairs.size;
  tally.gamesWithCollapse = gamesWithCollapse.size;
  tally.within5.distinctDropsByGame = [...drops].map(([kifuId, plies]) => ({ kifuId, drops: plies.size }));
  tally.within5.distinctDrops = tally.within5.distinctDropsByGame.reduce((sum, game) => sum + game.drops, 0);
  return tally;
}

function entriesOf(games: readonly GatePairsGame[]): Entry[][] {
  const seen = new Set<string>();
  return games.map((game) => {
    if (seen.has(game.kifuId)) throw new Error(`同じ kifuId が 2 本ある: ${game.kifuId}`);
    seen.add(game.kifuId);
    const rows = new Map(game.rowStandings.map((row) => [row.ply, row.standing]));
    return game.pairs.map((pair) => ({ kifuId: game.kifuId, pair, rows }));
  });
}

/** 条件式の無い基準値(全ての組の崩れの内訳。T-6) */
export function baselineTallyOf(games: readonly GatePairsGame[]): { games: number; pairs: number; movesMissing: number; all: CollapseTally } {
  const all = collapseTallyOf(entriesOf(games).flat());
  return { games: games.length, pairs: all.pairs, movesMissing: games.reduce((sum, game) => sum + game.movesMissing, 0), all };
}

/** 1 人ぶんの組に条件式 1 本を当てる(実戦の側と読み筋の側)。並びは入力の組と同じ */
export function judgePairs(loaded: LoadedCondition, pairs: readonly PairRow[]): JudgedPair[] {
  return pairs.map((row) => ({ actual: judgeCondition(loaded.definition, { kind: "pair", row }), pv: judgeConditionPvSide(loaded.definition, { kind: "pair", row }) }));
}

/** Gate に当てられる定義か(`appliesTo` に pair がある。無ければ司令塔の決定 T-3 の pairNotApplied) */
export const appliesToPairs = (definition: Pick<ConditionDefinition, "appliesTo">): boolean => definition.appliesTo.includes("pair");

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

const isJudged = (judgement: ConditionJudgement | PvSideJudgement): judgement is Extract<ConditionJudgement, { state: "match" | "noMatch" }> =>
  judgement.state === "match" || judgement.state === "noMatch";

/**
 * 条件式 1 本ぶんの集計(計画 §4)。`judged[i][j]` は `games[i].pairs[j]` の判定(judgePairs の戻り)。
 * 並びの長さが食い違う・同じ kifuId が 2 本・判定しない行(pair を含まない定義)があれば例外
 */
export function gateTallyOf(games: readonly GatePairsGame[], judged: ReadonlyArray<readonly JudgedPair[]>): GateTally {
  if (judged.length !== games.length) throw new Error(`判定の局の数(${judged.length})が組の局の数(${games.length})と違う`);
  const perGame = entriesOf(games);
  const all: Entry[] = [];
  const truePairs: Entry[] = [];
  const falsePairs: Entry[] = [];
  const judgements: GateTally["judgements"] = { match: 0, noMatch: 0, undecidable: 0, undecidableReasons: [], movesMissing: 0 };
  const reasonRows = new Map<string, { path: string; reason: string; rows: number }>();
  let pvNotApplicable: Extract<PvSideJudgement, { state: "notApplicable" }> | undefined;
  let n = 0;
  let actualTrue = 0;
  let pvTrue = 0;

  perGame.forEach((entries, gameIndex) => {
    const game = games[gameIndex]!;
    const judgedGame = judged[gameIndex]!;
    if (judgedGame.length !== entries.length) throw new Error(`${game.kifuId} の判定の数(${judgedGame.length})が組の数(${entries.length})と違う`);
    judgements.movesMissing += game.movesMissing;
    entries.forEach((entry, pairIndex) => {
      const { actual, pv } = judgedGame[pairIndex]!;
      if (actual.state === "notJudged" || pv.state === "notJudged") throw new Error(`${game.kifuId} の組 ${entry.pair.branchPly} を判定していない(pair を含まない定義は Gate に当てない)`);
      all.push(entry);
      if (actual.state === "undecidable") {
        judgements.undecidable += 1;
        for (const { path, reason } of actual.missing) {
          const key = `${path} ${reasonKey(reason)}`;
          const row = reasonRows.get(key) ?? { path, reason: reasonKey(reason), rows: 0 };
          row.rows += 1;
          reasonRows.set(key, row);
        }
      } else {
        judgements[actual.state] += 1;
        (actual.state === "match" ? truePairs : falsePairs).push(entry);
      }
      if (pv.state === "notApplicable") {
        pvNotApplicable ??= pv;
      } else if (entry.pair.counterfactual.state === "compared" && isJudged(actual) && isJudged(pv)) {
        n += 1;
        if (actual.state === "match") actualTrue += 1;
        if (pv.state === "match") pvTrue += 1;
      }
    });
  });
  judgements.undecidableReasons = [...reasonRows.values()].sort((a, b) => (a.path === b.path ? a.reason.localeCompare(b.reason) : a.path.localeCompare(b.path)));

  const trueTally = collapseTallyOf(truePairs);
  const falseTally = collapseTallyOf(falsePairs);
  const percent = (count: RateCount): number | null => (count.denominator === 0 ? null : (100 * count.collapsed) / count.denominator);
  const truePercent = percent(trueTally);
  const falsePercent = percent(falseTally);
  return {
    games: games.length,
    judgements,
    all: collapseTallyOf(all),
    truePairs: trueTally,
    falsePairs: falseTally,
    rates: {
      truePercent,
      falsePercent,
      ratio: truePercent === null || falsePercent === null || falseTally.collapsed === 0 ? null : truePercent / falsePercent,
      diffPoints: truePercent === null || falsePercent === null ? null : truePercent - falsePercent,
    },
    // 読み筋の側を当てられないかは定義で決まる(組に依らない)ので、1 つでもあれば定義ごと当てられない
    pvSide: pvNotApplicable !== undefined ? { state: "notApplicable", reasons: pvNotApplicable.reasons } : { state: "applicable", n, actualTrue, pvTrue },
  };
}

// ---- Gate(計画 §5)----

/** 人間の確定(2fe81c3)の値を 1 か所に。draft を付けない */
export const GATE_VALUES = {
  minTruePairs: 10,
  minGames: 3,
  minRateRatio: 2,
  minRateDiffPoints: 10,
  maxPvToActualRatio: 0.5,
  minTestTruePairs: 3,
} as const;
export type GateValues = { readonly [K in keyof typeof GATE_VALUES]: number };

/** verdict の文。**ほかの語を出さない** */
export const GATE_TEXT = {
  meets: "追加検証する価値のある個人パターン候補",
  insufficient: "現データでは個人パターンとして採用する根拠が不足",
} as const;

/** 比の条件 `tc·fn ≥ minRatio·fc·tn`(整数)。偽の崩れが 0 なら真の崩れ ≥ 1 で満たす(Q-5・T-5)。分母は呼び出し側が 0 でないことを確かめる */
export function rateRatioMet(truePairs: RateCount, falsePairs: RateCount, minRatio: number): boolean {
  if (falsePairs.collapsed === 0) return truePairs.collapsed >= 1;
  return truePairs.collapsed * falsePairs.denominator >= minRatio * falsePairs.collapsed * truePairs.denominator;
}

/** 差の条件 `100·(tc·fn − fc·tn) ≥ minPoints·tn·fn`(整数。境を含む) */
export function rateDiffMet(truePairs: RateCount, falsePairs: RateCount, minPoints: number): boolean {
  return 100 * crossDiff(truePairs, falsePairs) >= minPoints * truePairs.denominator * falsePairs.denominator;
}

/** `tc·fn − fc·tn`(率の差の符号と同じ符号の整数) */
export const crossDiff = (truePairs: RateCount, falsePairs: RateCount): number =>
  truePairs.collapsed * falsePairs.denominator - falsePairs.collapsed * truePairs.denominator;

/** G-3 の `p ≤ ratio·a` を整数の `p·(1/ratio) ≤ a` にする(0.5 なら 2·p ≤ a ― 計画 §5 の字面。監査 93 の S-3)。1/ratio が整数でなければ例外 */
export function inverseRatioOf(ratio: number): number {
  const inverse = 1 / ratio;
  if (!Number.isInteger(inverse)) throw new Error(`maxPvToActualRatio の逆数が整数でない(${ratio})`);
  return inverse;
}

export type GateItemId = "G-1" | "G-2" | "G-3" | "G-4";
export type GateItemResult = "met" | "notMet" | "notEvaluable";

export interface GateItem {
  item: GateItemId;
  values: Record<string, number>;
  threshold: Record<string, number>;
  result: GateItemResult;
  /** met なら空。notMet・notEvaluable の理由(英字の記号) */
  reasons: string[];
}

export type GateVerdict =
  | { items: GateItem[]; verdict: "meets"; text: typeof GATE_TEXT.meets }
  | { items: GateItem[]; verdict: "insufficient"; text: typeof GATE_TEXT.insufficient };

const itemOf = (item: GateItemId, values: Record<string, number>, threshold: Record<string, number>, notEvaluable: string[], notMet: string[]): GateItem => ({
  item,
  values,
  threshold,
  result: notEvaluable.length > 0 ? "notEvaluable" : notMet.length > 0 ? "notMet" : "met",
  reasons: notEvaluable.length > 0 ? notEvaluable : notMet,
});

/** Gate の 4 項目と verdict(計画 §5)。`material` は材料の側、`test` は試す側の集計 */
export function gateVerdictOf(material: GateTally, test: GateTally, values: GateValues = GATE_VALUES): GateVerdict {
  const t = material.truePairs;
  const f = material.falsePairs;

  // G-1: 崩れを決められる真の組 tn と、その組のある局(読み (4))
  const g1 = itemOf(
    "G-1",
    { truePairsDenominator: t.denominator, gamesWithTrueDenominator: t.gamesWithDenominator, truePairsTotal: t.pairs, gamesWithTruePairs: t.gamesWithPairs },
    { minTruePairs: values.minTruePairs, minGames: values.minGames },
    [],
    [...(t.denominator >= values.minTruePairs ? [] : ["truePairsBelowMin"]), ...(t.gamesWithDenominator >= values.minGames ? [] : ["gamesBelowMin"])],
  );

  // G-2: 比の条件かつ差の条件(整数)
  const g2Values = { trueCollapsed: t.collapsed, trueDenominator: t.denominator, falseCollapsed: f.collapsed, falseDenominator: f.denominator };
  const g2Threshold = { minRateRatio: values.minRateRatio, minRateDiffPoints: values.minRateDiffPoints };
  const g2NotEvaluable = [...(t.denominator === 0 ? ["trueDenominatorZero"] : []), ...(f.denominator === 0 ? ["falseDenominatorZero"] : [])];
  const g2 = itemOf(
    "G-2",
    g2Values,
    g2Threshold,
    g2NotEvaluable,
    g2NotEvaluable.length > 0 ? [] : [...(rateRatioMet(t, f, values.minRateRatio) ? [] : ["ratioNotMet"]), ...(rateDiffMet(t, f, values.minRateDiffPoints) ? [] : ["diffNotMet"])],
  );

  // G-3: 読み筋の側 p ≤ maxPvToActualRatio · a(揃えた集合 n で。境を含む)
  const pv = material.pvSide;
  const g3 =
    pv.state === "notApplicable"
      ? itemOf("G-3", {}, { maxPvToActualRatio: values.maxPvToActualRatio }, ["pvSideNotApplicable"], [])
      : itemOf(
          "G-3",
          { n: pv.n, actualTrue: pv.actualTrue, pvTrue: pv.pvTrue },
          { maxPvToActualRatio: values.maxPvToActualRatio },
          pv.n === 0 ? ["pvSetEmpty"] : [],
          pv.pvTrue * inverseRatioOf(values.maxPvToActualRatio) <= pv.actualTrue ? [] : ["pvTooHigh"],
        );

  // G-4: 試す側 tn ≥ minTestTruePairs かつ tc·fn − fc·tn が材料の側と同じ符号で 0 でない(読み (1)・(4))。分母 0 を先に見る(T-10)
  const tt = test.truePairs;
  const tf = test.falsePairs;
  const testCross = crossDiff(tt, tf);
  const materialCross = crossDiff(t, f);
  const g4NotEvaluable = [
    ...(tt.denominator === 0 ? ["testTrueDenominatorZero"] : []),
    ...(tf.denominator === 0 ? ["testFalseDenominatorZero"] : []),
    ...(t.denominator === 0 || f.denominator === 0 ? ["materialDenominatorZero"] : []),
  ];
  const g4 = itemOf(
    "G-4",
    { testTruePairsDenominator: tt.denominator, testTrueCollapsed: tt.collapsed, testFalseCollapsed: tf.collapsed, testFalseDenominator: tf.denominator, testCrossDiff: testCross, materialCrossDiff: materialCross },
    { minTestTruePairs: values.minTestTruePairs },
    g4NotEvaluable,
    g4NotEvaluable.length > 0
      ? []
      : [
          ...(tt.denominator >= values.minTestTruePairs ? [] : ["testTruePairsBelowMin"]),
          ...(testCross === 0 ? ["testSignZero"] : materialCross === 0 ? ["materialSignZero"] : Math.sign(testCross) !== Math.sign(materialCross) ? ["signDiffers"] : []),
        ],
  );

  const items = [g1, g2, g3, g4];
  return items.every((item) => item.result === "met") ? { items, verdict: "meets", text: GATE_TEXT.meets } : { items, verdict: "insufficient", text: GATE_TEXT.insufficient };
}

/** 定義の状態ごとの Gate の欄(Q-7: draft は集計だけで verdict を出さない) */
export function gateOf(status: ConditionDefinition["status"], material: GateTally, test: GateTally, values: GateValues = GATE_VALUES): GateVerdict | { notJudged: "draft" } {
  return status === "draft" ? { notJudged: "draft" } : gateVerdictOf(material, test, values);
}
