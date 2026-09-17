// STEP D4(docs/STEP_D4_PLAN_2026-09-15.md §4・§5・§8)。崩れの数え方と Gate の判定の固定例 G-F1〜G-F7・G-F9・G-F11〜G-F14 と、
// 司令塔の決定 T-1・T-4・T-5・T-9・T-10 の見張り。**エンジンは起動しない。**
//
// 【正解の置き方】期待は計画書 §8 の表と、植えた件数から手で導いた整数(実装の出力から写さない)。
// 集計の固定例は、崩れの数え方が読む欄(standingPair・fromReadyPly・branchPly・counterfactual.state)だけを持つ組の行と、手で置いた判定で作る。
// judgePairs は、型どおりの行と試験だけの架空の定義で 1 本当てる。

import { describe, expect, it } from "vitest";
import { checkCondition, type ConditionDefinition, type ConditionJudgement, type PairRow, type PvSideJudgement } from "./condition.js";
import type { CounterfactualComparison, SequenceFacts } from "./counterfactual.js";
import type { Evaluation, Trigger } from "./failureEvent.js";
import {
  appliesToPairs,
  baselineTallyOf,
  collapseOf,
  GATE_TEXT,
  GATE_VALUES,
  gateOf,
  gateTallyOf,
  gateVerdictOf,
  inverseRatioOf,
  judgePairs,
  rateDiffMet,
  rateRatioMet,
  within5Of,
  type GatePairsGame,
  type GateTally,
  type JudgedPair,
} from "./gate.js";
import type { PositionFacts } from "./positionFacts.js";
import type { Standing } from "./standing.js";

// ---- 組の行と判定 ----

const U = (reason: "notMeasurable" | "notEvaluation" = "notMeasurable"): Standing => ({ undetermined: reason });

/** 崩れの数え方が読む欄だけの組の行 */
const stub = (kifuId: string, from: number, before: Standing, after: Standing, counterfactualState = "compared"): PairRow =>
  ({ kifuId, pairKind: "compared", branchPly: from + 1, fromReadyPly: from, toReadyPly: from + 2, standingPair: { before, after }, counterfactual: { state: counterfactualState } }) as unknown as PairRow;

/** 行の状態は、渡さなければ組の直前・直後から作る */
function gameOf(kifuId: string, pairs: PairRow[], rowStandings?: Array<{ ply: number; standing: Standing }>, movesMissing = 0): GatePairsGame {
  const rows = new Map<number, Standing>();
  for (const pair of pairs) {
    rows.set(pair.fromReadyPly, pair.standingPair.before);
    rows.set(pair.toReadyPly, pair.standingPair.after);
  }
  return { kifuId, pairs, movesMissing, rowStandings: rowStandings ?? [...rows].sort((a, b) => a[0] - b[0]).map(([ply, standing]) => ({ ply, standing })) };
}

type Side = "match" | "noMatch" | "undecidable";
const actualOf = (side: Side): ConditionJudgement =>
  side === "undecidable" ? { state: "undecidable", missing: [{ path: "trigger.focus.state", reason: { kind: "gate", gatePath: "trigger.focus.state", actual: "pending" } }] } : { state: side, usedValues: {} };
const pvOf = (side: Side | "notApplicable"): PvSideJudgement => (side === "notApplicable" ? { state: "notApplicable", reasons: [{ reason: "noActualPath" }] } : actualOf(side));
const J = (actual: Side, pv: Side | "notApplicable" = "noMatch"): JudgedPair => ({ actual: actualOf(actual), pv: pvOf(pv) });

/** n 組(うち collapsed 組が ahead→level、残りは ahead→ahead)を games 局に順に配る。組ごとに ply を離して窓を重ねない */
function population(prefix: string, n: number, collapsed: number, games: number, judged: JudgedPair): { games: GatePairsGame[]; judged: JudgedPair[][] } {
  const perGame: PairRow[][] = Array.from({ length: games }, () => []);
  for (let index = 0; index < n; index += 1) {
    const g = index % games;
    perGame[g]!.push(stub(`${prefix}${g}`, perGame[g]!.length * 100, "ahead", index < collapsed ? "level" : "ahead"));
  }
  const kept = perGame.map((pairs, g) => ({ pairs, g })).filter(({ pairs }) => pairs.length > 0);
  return { games: kept.map(({ pairs, g }) => gameOf(`${prefix}${g}`, pairs)), judged: kept.map(({ pairs }) => pairs.map(() => judged)) };
}

interface TallySpec {
  trueN: number;
  trueC: number;
  trueGames?: number;
  falseN: number;
  falseC: number;
  falseGames?: number;
}
function tallyOf(spec: TallySpec): GateTally {
  const t = population("t", spec.trueN, spec.trueC, spec.trueGames ?? 3, J("match"));
  const f = population("f", spec.falseN, spec.falseC, spec.falseGames ?? 3, J("noMatch"));
  return gateTallyOf([...t.games, ...f.games], [...t.judged, ...f.judged]);
}

const item = (verdict: ReturnType<typeof gateVerdictOf>, id: string) => verdict.items.find((entry) => entry.item === id)!;
/** 材料の側で G-1〜G-3 を満たす集計(真 20 組・崩れ 10、偽 100 組・崩れ 10) */
const MATERIAL_OK = (): GateTally => tallyOf({ trueN: 20, trueC: 10, falseN: 100, falseC: 10 });
/** 試す側で G-4 を満たす集計(真 3 組・崩れ 2、偽 10 組・崩れ 1。符号は正) */
const TEST_OK = (): GateTally => tallyOf({ trueN: 3, trueC: 2, trueGames: 1, falseN: 10, falseC: 1, falseGames: 1 });

// ---- 崩れ(計画 §4)----

describe("collapseOf・崩れの内訳(計画 §4、G-F1・G-F13・T-4)", () => {
  it("G-F1 9 通りの遷移 → 崩れ 3・崩れでない 2・cannotFall 2・未定 2", () => {
    const transitions: Array<[Standing, Standing]> = [
      ["ahead", "level"],
      ["level", "behind"],
      ["ahead", "behind"],
      ["level", "level"],
      ["ahead", "ahead"],
      ["behind", "behind"],
      ["behind", "level"],
      [U(), "level"],
      ["ahead", U("notEvaluation")],
    ];
    const games = transitions.map(([before, after], index) => gameOf(`g${index}`, [stub(`g${index}`, 10, before, after)]));
    const { all } = baselineTallyOf(games);
    expect([all.pairs, all.collapsed, all.denominator - all.collapsed]).toEqual([9, 3, 2]);
    expect(all.excluded).toEqual({ beforeUndetermined: 1, afterUndetermined: 1, cannotFall: 2 });
    expect(all.transitions).toEqual({ aheadToLevel: 1, levelToBehind: 1, aheadToBehind: 1 });
    expect(all.byBefore).toEqual({ ahead: { collapsed: 2, denominator: 3 }, level: { collapsed: 1, denominator: 2 } });
    expect([all.gamesWithCollapse, all.gamesWithDenominator, all.gamesWithPairs]).toEqual([3, 5, 9]);
  });

  it("T-4 理由の順: 直前が未定 → 直後が未定 → cannotFall(直前 behind・直後が未定は afterUndetermined)", () => {
    expect(collapseOf({ before: U(), after: U() })).toEqual({ counted: false, reason: "beforeUndetermined" });
    expect(collapseOf({ before: U(), after: "behind" })).toEqual({ counted: false, reason: "beforeUndetermined" });
    expect(collapseOf({ before: "behind", after: U() })).toEqual({ counted: false, reason: "afterUndetermined" });
    expect(collapseOf({ before: "behind", after: "ahead" })).toEqual({ counted: false, reason: "cannotFall" });
    expect(collapseOf({ before: "level", after: "ahead" })).toEqual({ counted: true, before: "level", transition: null });
  });

  it("G-F13 直前の状態ごと: 真の組が全部 ahead・偽の組が ahead と level に分かれる。behind の組は cannotFall にだけ数える", () => {
    const truePairs = [stub("a", 10, "ahead", "level"), stub("a", 20, "ahead", "ahead"), stub("a", 30, "behind", "behind")];
    const falsePairs = [stub("b", 10, "ahead", "behind"), stub("b", 20, "level", "behind"), stub("b", 30, "level", "level"), stub("b", 40, "behind", "level")];
    const tally = gateTallyOf([gameOf("a", truePairs, []), gameOf("b", falsePairs, [])], [truePairs.map(() => J("match")), falsePairs.map(() => J("noMatch"))]);
    expect(tally.truePairs.byBefore).toEqual({ ahead: { collapsed: 1, denominator: 2 }, level: { collapsed: 0, denominator: 0 } });
    expect(tally.falsePairs.byBefore).toEqual({ ahead: { collapsed: 1, denominator: 1 }, level: { collapsed: 1, denominator: 2 } });
    expect([tally.truePairs.excluded.cannotFall, tally.falsePairs.excluded.cannotFall]).toEqual([1, 1]);
    expect([tally.truePairs.denominator, tally.falsePairs.denominator]).toEqual([2, 3]);
  });
});

describe("5 手以内(参考。計画 §4、G-F7・T-1)", () => {
  it("G-F7 隣り合う 2 つの真の組が同じ行(ply 40)で下がる → 下がった組 2・崩れの件 1・局ごと 1", () => {
    const rows: Array<{ ply: number; standing: Standing }> = [36, 38, 40, 42, 44].map((ply) => ({ ply, standing: ply < 40 ? "ahead" : "level" }));
    const pairs = [stub("g", 36, "ahead", "ahead"), stub("g", 38, "ahead", "level")];
    const tally = gateTallyOf([gameOf("g", pairs, rows)], [pairs.map(() => J("match"))]);
    expect(tally.truePairs.within5).toEqual({
      dropped: 2,
      denominator: 2,
      excluded: { beforeUndetermined: 0, cannotFall: 0, windowShort: 0 },
      distinctDrops: 1,
      distinctDropsByGame: [{ kifuId: "g", drops: 1 }],
    });
  });

  it("T-1 窓の行(+2・+4・+6)が 1 つでも無ければ windowShort で分母から外す。窓の中の未定の行は下がったに数えない。直前 behind・未定は外す", () => {
    const rows = new Map<number, Standing>([
      [10, "ahead"],
      [12, U()],
      [14, "ahead"],
      [16, "level"],
    ]);
    expect(within5Of(10, "ahead", rows)).toEqual({ counted: true, dropPly: 16 });
    expect(within5Of(12, "ahead", rows)).toEqual({ counted: false, reason: "windowShort" });
    expect(within5Of(10, "behind", rows)).toEqual({ counted: false, reason: "cannotFall" });
    expect(within5Of(10, U(), rows)).toEqual({ counted: false, reason: "beforeUndetermined" });
    expect(within5Of(10, "level", new Map([...rows, [16, "level"]]))).toEqual({ counted: true, dropPly: null });
  });
});

// ---- 集計の形(計画 §4)----

describe("gateTallyOf(計画 §4)", () => {
  it("判定の数・判定不能の理由・movesMissing。判定不能の組は真にも偽にも入らず、全ての組には入る", () => {
    const pairs = [stub("g", 10, "ahead", "level"), stub("g", 20, "ahead", "ahead"), stub("g", 30, "level", "behind")];
    const tally = gateTallyOf([gameOf("g", pairs, [], 2)], [[J("match"), J("noMatch"), J("undecidable")]]);
    expect(tally.judgements).toEqual({ match: 1, noMatch: 1, undecidable: 1, undecidableReasons: [{ path: "trigger.focus.state", reason: "trigger.focus.state=pending", rows: 1 }], movesMissing: 2 });
    expect([tally.all.pairs, tally.truePairs.pairs, tally.falsePairs.pairs]).toEqual([3, 1, 1]);
    expect(tally.all.collapsed).toBe(2);
  });

  it("G-F14 真と判定された組 12(3 局)のうち cannotFall 4 → tn 8。G-1 notMet、出力に真の総数 12 と tn 8 が両方出る", () => {
    const games: GatePairsGame[] = [];
    const judged: JudgedPair[][] = [];
    for (let g = 0; g < 3; g += 1) {
      const pairs = [0, 1, 2, 3].map((k) => stub(`t${g}`, k * 100, k === 0 || (g === 0 && k === 1) ? "behind" : "ahead", "ahead"));
      games.push(gameOf(`t${g}`, pairs));
      judged.push(pairs.map(() => J("match")));
    }
    const f = population("f", 100, 10, 3, J("noMatch"));
    const tally = gateTallyOf([...games, ...f.games], [...judged, ...f.judged]);
    expect([tally.truePairs.pairs, tally.truePairs.excluded.cannotFall, tally.truePairs.denominator, tally.truePairs.gamesWithPairs, tally.truePairs.gamesWithDenominator]).toEqual([12, 4, 8, 3, 3]);
    const g1 = item(gateVerdictOf(tally, TEST_OK()), "G-1");
    expect(g1).toMatchObject({ result: "notMet", reasons: ["truePairsBelowMin"], values: { truePairsDenominator: 8, truePairsTotal: 12 } });
  });

  it("G-F14b 読み (4): G-1 の局の数は崩れを決められる真の組のある局で数える。tn 10 が 2 局・cannotFall だけの真の組が 3 局目 → gamesBelowMin", () => {
    const counted = [0, 1].map((g) => gameOf(`t${g}`, [0, 1, 2, 3, 4].map((k) => stub(`t${g}`, k * 100, "ahead", k === 0 ? "level" : "ahead"))));
    const onlyCannotFall = gameOf("t2", [stub("t2", 0, "behind", "behind"), stub("t2", 100, "behind", "level")]);
    const truth = [...counted, onlyCannotFall];
    const f = population("f", 100, 10, 3, J("noMatch"));
    const tally = gateTallyOf([...truth, ...f.games], [...truth.map((game) => game.pairs.map(() => J("match"))), ...f.judged]);
    expect([tally.truePairs.denominator, tally.truePairs.gamesWithDenominator, tally.truePairs.gamesWithPairs]).toEqual([10, 2, 3]);
    expect(item(gateVerdictOf(tally, TEST_OK()), "G-1")).toMatchObject({ result: "notMet", reasons: ["gamesBelowMin"] });
  });

  it("C-2 読み (4): G-4 の真の組は試す側の tn で数える。真 3 組のうち cannotFall 1 → tn 2 で testTruePairsBelowMin", () => {
    const pairs = [stub("s", 0, "ahead", "level"), stub("s", 100, "ahead", "ahead"), stub("s", 200, "behind", "behind")];
    const f = population("sf", 10, 1, 1, J("noMatch"));
    const test = gateTallyOf([gameOf("s", pairs), ...f.games], [pairs.map(() => J("match")), ...f.judged]);
    expect([test.truePairs.pairs, test.truePairs.denominator]).toEqual([3, 2]);
    expect(item(gateVerdictOf(MATERIAL_OK(), test), "G-4")).toMatchObject({ result: "notMet", reasons: ["testTruePairsBelowMin"] });
  });

  it("G-F5・T-9 読み筋の側: 揃えた集合 n は compared で両側が判定できた組だけ。実戦 10・読み筋 5 → met / 読み筋 6 → notMet", () => {
    const pvSide = (pvTrue: number) => {
      const pairs = Array.from({ length: 50 }, (_, k) => stub("g", k * 100, "ahead", "ahead"));
      const judged = pairs.map((_, k) => J(k < 10 ? "match" : "noMatch", k < pvTrue ? "match" : "noMatch"));
      // n の外: compared でない組(読み筋が真)・読み筋の側が判定不能の組・実戦の側が判定不能の組
      const outside = [stub("h", 0, "ahead", "ahead", "noPv"), stub("h", 100, "ahead", "ahead"), stub("h", 200, "ahead", "ahead")];
      return gateTallyOf([gameOf("g", pairs), gameOf("h", outside)], [judged, [J("match", "match"), J("match", "undecidable"), J("undecidable", "match")]]);
    };
    expect(pvSide(5).pvSide).toEqual({ state: "applicable", n: 50, actualTrue: 10, pvTrue: 5 });
    expect(item(gateVerdictOf(pvSide(5), TEST_OK()), "G-3")).toMatchObject({ result: "met", reasons: [] });
    expect(item(gateVerdictOf(pvSide(6), TEST_OK()), "G-3")).toMatchObject({ result: "notMet", reasons: ["pvTooHigh"] });
  });

  it("G-3 読み筋の側を当てられない定義 → notEvaluable。集合が空 → notEvaluable", () => {
    const pairs = [stub("g", 0, "ahead", "level")];
    const notApplicable = gateTallyOf([gameOf("g", pairs)], [[J("match", "notApplicable")]]);
    expect(notApplicable.pvSide).toEqual({ state: "notApplicable", reasons: [{ reason: "noActualPath" }] });
    expect(item(gateVerdictOf(notApplicable, TEST_OK()), "G-3")).toMatchObject({ result: "notEvaluable", reasons: ["pvSideNotApplicable"] });
    const empty = gateTallyOf([gameOf("g", pairs)], [[J("match", "undecidable")]]);
    expect(item(gateVerdictOf(empty, TEST_OK()), "G-3")).toMatchObject({ result: "notEvaluable", reasons: ["pvSetEmpty"] });
  });

  it("止める: 判定しない行(pair を含まない定義)・判定の数の食い違い・同じ kifuId が 2 本", () => {
    const pairs = [stub("g", 0, "ahead", "level")];
    const notJudged: JudgedPair = { actual: { state: "notJudged", reason: "kindNotApplied" }, pv: { state: "notJudged", reason: "kindNotApplied" } };
    expect(() => gateTallyOf([gameOf("g", pairs)], [[notJudged]])).toThrow(/判定していない/);
    expect(() => gateTallyOf([gameOf("g", pairs)], [[]])).toThrow(/判定の数/);
    expect(() => gateTallyOf([gameOf("g", pairs)], [])).toThrow(/局の数/);
    expect(() => gateTallyOf([gameOf("g", pairs), gameOf("g", pairs)], [[J("match")], [J("match")]])).toThrow(/同じ kifuId/);
  });
});

// ---- Gate(計画 §5)----

describe("gateVerdictOf(計画 §5)", () => {
  it("G-F2 真 20(崩れ 4)・偽 100(崩れ 10): 比 400 ≥ 400・差 20000 ≥ 20000 → G-2 met(境を含む)", () => {
    expect(item(gateVerdictOf(tallyOf({ trueN: 20, trueC: 4, falseN: 100, falseC: 10 }), TEST_OK()), "G-2")).toMatchObject({ result: "met", reasons: [] });
  });

  it("G-F3 (a) 真 20(3)・偽 100(10) → 比 notMet (b) 100(11)・100(2) → 差だけ notMet (c) 100(12)・100(2) → met (d) 100(25)・100(15) → 比だけ notMet", () => {
    const g2 = (trueN: number, trueC: number, falseN: number, falseC: number) => item(gateVerdictOf(tallyOf({ trueN, trueC, falseN, falseC }), TEST_OK()), "G-2");
    expect(g2(20, 3, 100, 10)).toMatchObject({ result: "notMet", reasons: ["ratioNotMet", "diffNotMet"] });
    expect(g2(100, 11, 100, 2)).toMatchObject({ result: "notMet", reasons: ["diffNotMet"] });
    expect(g2(100, 12, 100, 2)).toMatchObject({ result: "met", reasons: [] });
    expect(g2(100, 25, 100, 15)).toMatchObject({ result: "notMet", reasons: ["ratioNotMet"] });
  });

  it("G-F4 tn 10 組が 3 局 → met / 10 組が 2 局 → notMet / 9 組が 5 局 → notMet", () => {
    const g1 = (trueN: number, trueGames: number) => item(gateVerdictOf(tallyOf({ trueN, trueC: 5, trueGames, falseN: 100, falseC: 10 }), TEST_OK()), "G-1");
    expect(g1(10, 3)).toMatchObject({ result: "met", reasons: [], values: { truePairsDenominator: 10, gamesWithTrueDenominator: 3 } });
    expect(g1(10, 2)).toMatchObject({ result: "notMet", reasons: ["gamesBelowMin"] });
    expect(g1(9, 5)).toMatchObject({ result: "notMet", reasons: ["truePairsBelowMin"] });
  });

  it("G-2 真か偽の分母が 0 → notEvaluable", () => {
    const tally = tallyOf({ trueN: 0, trueC: 0, falseN: 10, falseC: 1 });
    expect(item(gateVerdictOf(tally, TEST_OK()), "G-2")).toMatchObject({ result: "notEvaluable", reasons: ["trueDenominatorZero"] });
  });

  it("R-3 偽の分母が 0 → G-2 notEvaluable(偽の崩れ 0 の Q-5 で met にしない)", () => {
    const tally = tallyOf({ trueN: 10, trueC: 1, falseN: 0, falseC: 0 });
    expect(item(gateVerdictOf(tally, TEST_OK()), "G-2")).toMatchObject({ result: "notEvaluable", reasons: ["falseDenominatorZero"] });
  });

  it("R-3 材料の側の偽の分母が 0 → G-4 notEvaluable(materialDenominatorZero)。試す側は満たす形", () => {
    const material = tallyOf({ trueN: 10, trueC: 1, falseN: 0, falseC: 0 });
    expect(item(gateVerdictOf(material, TEST_OK()), "G-4")).toMatchObject({ result: "notEvaluable", reasons: ["materialDenominatorZero"] });
  });

  it("S-3 G-3 は整数 2·p ≤ a で比べる(0.5 の逆数 2)。逆数が整数でない値は受けない", () => {
    expect(inverseRatioOf(GATE_VALUES.maxPvToActualRatio)).toBe(2);
    expect(() => inverseRatioOf(0.3)).toThrow(/整数でない/);
  });

  it("G-F6・T-10 試す側: 真 3 組・同じ符号 → met / 真 2 組 → notMet / 符号が逆 → notMet / 0 → notMet / 偽の分母 0 → notEvaluable", () => {
    const g4 = (test: TallySpec) => item(gateVerdictOf(MATERIAL_OK(), tallyOf({ trueGames: 1, falseGames: 1, ...test })), "G-4");
    expect(g4({ trueN: 3, trueC: 2, falseN: 10, falseC: 1 })).toMatchObject({ result: "met", reasons: [], values: { testCrossDiff: 17 } });
    expect(g4({ trueN: 2, trueC: 2, falseN: 10, falseC: 1 })).toMatchObject({ result: "notMet", reasons: ["testTruePairsBelowMin"] });
    expect(g4({ trueN: 3, trueC: 0, falseN: 10, falseC: 5 })).toMatchObject({ result: "notMet", reasons: ["signDiffers"] });
    expect(g4({ trueN: 3, trueC: 0, falseN: 10, falseC: 0 })).toMatchObject({ result: "notMet", reasons: ["testSignZero"] });
    expect(g4({ trueN: 3, trueC: 1, falseN: 0, falseC: 0 })).toMatchObject({ result: "notEvaluable", reasons: ["testFalseDenominatorZero"] });
    // 分母 0 を先に見る(真 0 組は「3 組未満」でなく notEvaluable)
    expect(g4({ trueN: 0, trueC: 0, falseN: 10, falseC: 1 })).toMatchObject({ result: "notEvaluable", reasons: ["testTrueDenominatorZero"] });
  });

  it("G-4 材料の側の差が 0 → 試す側が正でも notMet(materialSignZero)", () => {
    const material = tallyOf({ trueN: 20, trueC: 2, falseN: 100, falseC: 10 });
    expect(item(gateVerdictOf(material, TEST_OK()), "G-4")).toMatchObject({ result: "notMet", reasons: ["materialSignZero"] });
  });

  it("G-F9 4 項目 met → meets と候補の文 / G-4 だけ notEvaluable → insufficient と根拠不足の文 / draft の定義 → notJudged で文なし", () => {
    const meets = gateVerdictOf(MATERIAL_OK(), TEST_OK());
    expect(meets.items.map((entry) => entry.result)).toEqual(["met", "met", "met", "met"]);
    expect([meets.verdict, meets.text]).toEqual(["meets", "追加検証する価値のある個人パターン候補"]);

    const onlyG4 = gateVerdictOf(MATERIAL_OK(), tallyOf({ trueN: 3, trueC: 1, trueGames: 1, falseN: 0, falseC: 0 }));
    expect(onlyG4.items.map((entry) => entry.result)).toEqual(["met", "met", "met", "notEvaluable"]);
    expect([onlyG4.verdict, onlyG4.text]).toEqual(["insufficient", "現データでは個人パターンとして採用する根拠が不足"]);

    expect(gateOf("draft", MATERIAL_OK(), TEST_OK())).toEqual({ notJudged: "draft" });
    expect(gateOf("approved", MATERIAL_OK(), TEST_OK())).toEqual(meets);
    expect(GATE_TEXT).toEqual({ meets: "追加検証する価値のある個人パターン候補", insufficient: "現データでは個人パターンとして採用する根拠が不足" });
  });

  it("G-F11・T-5 偽 100(崩れ 0)・真 100(崩れ 10) → 比の条件を満たし差 10 → met(表示の比は null)/ 偽 100(0)・真 100(0) → 比も差も notMet", () => {
    const withTen = tallyOf({ trueN: 100, trueC: 10, falseN: 100, falseC: 0 });
    expect(item(gateVerdictOf(withTen, TEST_OK()), "G-2")).toMatchObject({ result: "met", reasons: [] });
    expect(withTen.rates).toEqual({ truePercent: 10, falsePercent: 0, ratio: null, diffPoints: 10 });
    const zero = tallyOf({ trueN: 100, trueC: 0, falseN: 100, falseC: 0 });
    expect(item(gateVerdictOf(zero, TEST_OK()), "G-2")).toMatchObject({ result: "notMet", reasons: ["ratioNotMet", "diffNotMet"] });
    expect(rateRatioMet({ collapsed: 0, denominator: 100 }, { collapsed: 0, denominator: 100 }, 2)).toBe(false);
    expect(rateRatioMet({ collapsed: 1, denominator: 100 }, { collapsed: 0, denominator: 100 }, 2)).toBe(true);
  });

  it("G-F12 差の関数に 真 3/10・偽 10/50 → true(浮動小数では 10 未満)。G-2 全体は比 1.5 で notMet。真 10/67・偽 33/670 → G-2 met(浮動小数では差が 10 未満)", () => {
    expect(rateDiffMet({ collapsed: 3, denominator: 10 }, { collapsed: 10, denominator: 50 }, 10)).toBe(true);
    expect(100 * (3 / 10 - 10 / 50)).toBeLessThan(10);
    expect(item(gateVerdictOf(tallyOf({ trueN: 10, trueC: 3, falseN: 50, falseC: 10 }), TEST_OK()), "G-2")).toMatchObject({ result: "notMet", reasons: ["ratioNotMet"] });

    expect(item(gateVerdictOf(tallyOf({ trueN: 67, trueC: 10, falseN: 670, falseC: 33 }), TEST_OK()), "G-2")).toMatchObject({ result: "met", reasons: [] });
    expect(100 * (10 / 67 - 33 / 670)).toBeLessThan(10);
  });

  it("GATE_VALUES は人間の確定(2fe81c3)の値", () => {
    expect(GATE_VALUES).toEqual({ minTruePairs: 10, minGames: 3, minRateRatio: 2, minRateDiffPoints: 10, maxPvToActualRatio: 0.5, minTestTruePairs: 3 });
  });
});

// ---- judgePairs(型どおりの行と試験だけの定義)----

const measured = (scoreCp: number): Evaluation => ({ state: "measured", scoreCp, mate: null, bestmove: "2g2f", afterPassScoreCp: 100, afterPassMate: null, dropCp: 50 });
const counts = (bySente: number, byGote: number) => ({ bySente, byGote });
const positionFacts = (): PositionFacts => ({
  zoneSquares: { ownKingZone: 6, opponentKingZone: 6 },
  zonePieces: { ownKingZone: counts(5, 0), opponentKingZone: counts(0, 5) },
  zoneControl: { ownKingZone: counts(4, 0), opponentKingZone: counts(0, 4) },
});
const sequence = (kingEscapes: number): SequenceFacts => ({
  capturedRoles: { us: {}, opponent: {} },
  checks: { byUs: [], byOpponent: [] },
  mate: null,
  gameEnd: null,
  kingSurroundingsEnd: { squares: 5, own: 3 },
  positionFactsEnd: positionFacts(),
  kingEscapesEnd: { state: "counted", count: kingEscapes },
  userMoveFacts: { role: "pawn", drop: false, capturedRole: null, promotion: false, kingMove: false, fromInOwnKingZone: false, toInOwnKingZone: false, toInOpponentKingZone: false, ownKingZoneReachBeforeMinusAfter: 0 },
});
const comparison = (): CounterfactualComparison => ({
  state: "compared",
  comparedPlies: 6,
  windowPlies: 5,
  actualPlies: 6,
  pvLength: 8,
  pvUsablePlies: 8,
  pvTruncatedAtPly: null,
  pvBounded: { lowerbound: false, upperbound: false },
  pvFirstMove: "2g2f",
  pvFirstMoveIsBestmoveAtBefore: true,
  pvFirstMoveIsPlayedMove: false,
  kingEscapesRoot: { state: "counted", count: 2 },
  actual: sequence(1),
  pv: sequence(3),
  pvMinusActual: {
    capturedRoles: { us: {}, opponent: {} },
    kingSurroundingsOwn: 0,
    positionFacts: { zonePieces: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) }, zoneControl: { ownKingZone: counts(0, 0), opponentKingZone: counts(0, 0) } },
    kingEscapes: 2,
  },
  kingEscapesChangeFromRoot: { actual: -1, pv: 1 },
});
const trigger = (): Trigger => ({
  evaluationBefore: measured(500),
  opponentIntent: { classification: { column: "noCandidate" }, refersToIntentId: null },
  shape: { state: "recorded", status: "forming", refersToShapeId: null },
  focus: { state: "nothingToSay" },
  kingSurroundings: { squares: 5, own: 3 },
  positionFacts: positionFacts(),
});
const fullPair = (branchPly: number): PairRow => ({
  kifuId: "g",
  pairKind: "compared",
  branchPly,
  fromReadyPly: branchPly - 1,
  toReadyPly: branchPly + 1,
  trigger: trigger(),
  moves: { userMove: "7g7f", opponentMove: "3c3d" },
  userBestmoveAtBefore: "2g2f",
  opponentBestmove: { state: "notInRecord" },
  evaluationAfter: measured(0),
  standingPair: { before: "ahead", after: "level" },
  failureEventBranchPly: null,
  consequences: { checks: [], mate: null, windowPlies: 5, windowShort: false },
  counterfactual: comparison(),
});
const definition = (patch: Partial<ConditionDefinition>): ConditionDefinition => ({
  id: "test_only_gate",
  label: "試験だけの定義(仮)",
  status: "draft",
  definitionText: "試験だけ",
  uses: ["counterfactual.actual.kingEscapesEnd.count"],
  thresholds: {},
  appliesTo: ["pair"],
  approval: null,
  evaluate: (view) => ((view.counterfactual as { actual: { kingEscapesEnd: { count: number } } }).actual.kingEscapesEnd.count <= 1),
  ...patch,
});

describe("judgePairs・appliesToPairs", () => {
  it("実戦の側は actual の逃げ道 1 → match、読み筋の側は pv の逃げ道 3 → noMatch。並びは入力の組と同じ", () => {
    const loaded = checkCondition(definition({}), new Uint8Array([1]));
    const judged = judgePairs(loaded, [fullPair(11), fullPair(13)]);
    expect(judged.map((entry) => [entry.actual.state, entry.pv.state])).toEqual([
      ["match", "noMatch"],
      ["match", "noMatch"],
    ]);
  });

  it("pair を含まない定義は Gate に当てない(T-3)", () => {
    expect(appliesToPairs(definition({}))).toBe(true);
    expect(appliesToPairs(definition({ appliesTo: ["failureEvent"], uses: ["trigger.focus.state"] }))).toBe(false);
  });
});
