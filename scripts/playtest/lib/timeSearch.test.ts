// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.3・§7.5)。lib/timeSearch.ts の単体試験。
// **エンジンは起動しない**(合成の表だけを使う)。

import { describe, expect, it } from "vitest";
import type { MoveFeatureRow } from "./timeFeatures.js";
import {
  TIME_SEARCH_VALUES,
  chanceLineProbabilityOf,
  enumerateCandidatesOf,
  isAdoptedOf,
  isCollapseAdoptedOf,
  isCollapseReproducedOf,
  isReproducedOf,
  kindOf,
  searchOf,
  statsOf,
  type Condition,
} from "./timeSearch.js";

// 列挙・採用候補・再現の判定に要らない欄をすべて null/false で埋めた行を作る(4 列だけを動かす ― 計画
// 「試験」5.「合成の表〈60 行、列 4 つ〉」)。
function row(overrides: Partial<MoveFeatureRow> & { phase: MoveFeatureRow["phase"]; longThink: boolean }): MoveFeatureRow {
  return {
    kifuId: "synthetic",
    group: "g",
    gameNo: 1,
    kifPly: 1,
    spentSec: 0,
    spentBucket: "≤1",
    prevOwnSpentBucket: null,
    prev3SumBucket: null,
    prev5SumBucket: null,
    afterLongThink: null,
    remainingBucket: null,
    evalBand: null,
    evalChangePrev: null,
    inCheck: null,
    // STEP TIME-CAUSE-3(計画 §9.1)。既定は null(崩れの分母に入らない)。崩れを動かす試験は
    // overrides で明示的に collapse を渡す(row() の呼び出し側)。
    collapse: null,
    fork: null,
    top1Side: null,
    actualSide: null,
    lossBand: null,
    inTop5: null,
    actualCapture: null,
    actualDrop: null,
    actualGivesCheck: null,
    actualSacrifice: null,
    actualRetreat: null,
    top1Capture: null,
    top1Drop: null,
    top1GivesCheck: null,
    top1Sacrifice: null,
    top1Retreat: null,
    oppPrevCapture: null,
    oppPrevDrop: null,
    oppPrevGivesCheck: null,
    oppPrevPromotion: null,
    ownRookMoved: null,
    oppRookMoved: null,
    ...overrides,
  };
}

// ==== 60 行・4 列(phase・fork・inCheck・afterLongThink)の合成の表(発見用) ====
//
// グループ 1(30 行): phase=mid・fork=true・inCheck=false・afterLongThink=false。longThink は 15 true・15 false
//   (n=30・p=0.5)。この 4 列の値はここでしか出ない(phase=mid も fork=true も inCheck=false も
//   afterLongThink=false も、グループ 2・3 には出ない)ので、単独条件の n・p はグループ全体と一致する。
// グループ 2(15 行): phase=early・fork=false・inCheck=true・afterLongThink=null(← 条件に使われないことを試す)。longThink はすべて false。
// グループ 3(15 行): phase=late・fork=false・inCheck=true・afterLongThink=null。longThink はすべて false。
//
// p0(発見用)= 15 / 60 = 0.25。FINDING_VALUES = { minPairs: 20, ratio: 2 } なので、採用候補は n ≥ 20 かつ p ≥ 0.5。
const DISCOVER_ROWS: MoveFeatureRow[] = [
  ...Array.from({ length: 30 }, (_, i) => row({ phase: "mid", fork: true, inCheck: false, afterLongThink: false, longThink: i < 15 })),
  ...Array.from({ length: 15 }, () => row({ phase: "early", fork: false, inCheck: true, afterLongThink: null, longThink: false })),
  ...Array.from({ length: 15 }, () => row({ phase: "late", fork: false, inCheck: true, afterLongThink: null, longThink: false })),
];

// STEP TIME-CAUSE-3(計画 §9.1 の 2.)。DISCOVER_ROWS はどの行も collapse: null(既定)なので、崩れの分母
// (collapseCounted)は常に 0、崩れ(collapsed)は 0、q は null になる(0 除算にしない既定 ― null であって 0 ではない)。
const NO_COLLAPSE = { collapseCounted: 0, collapsed: 0, q: null } as const;

describe("statsOf: 手で数えた n・長考の数・p と一致する", () => {
  it("空の条件(全行)。n=60, longThink=15, p=0.25", () => {
    expect(statsOf(DISCOVER_ROWS, [])).toEqual({ n: 60, longThink: 15, p: 0.25, ...NO_COLLAPSE });
  });

  it("単独条件 phase=mid。n=30, longThink=15, p=0.5", () => {
    const condition: Condition = [{ column: "phase", value: "mid" }];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 30, longThink: 15, p: 0.5, ...NO_COLLAPSE });
  });

  it("afterLongThink=false は mid のグループだけに出る(early・late は null なので一致しない)。n=30", () => {
    const condition: Condition = [{ column: "afterLongThink", value: false }];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 30, longThink: 15, p: 0.5, ...NO_COLLAPSE });
  });

  it("該当 0 件の組は n=0, p=0(0 除算にならない)", () => {
    const condition: Condition = [
      { column: "phase", value: "mid" },
      { column: "fork", value: false },
    ];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 0, longThink: 0, p: 0, ...NO_COLLAPSE });
  });
});

describe("statsOf: 崩れの分母・崩れ・q(collapse 列を動かした行)", () => {
  // phase=mid の 10 行(row() の longThink はここでは使わない)。collapse: 6 true・2 false・2 null。
  // 分母(collapseCounted)は null を除いた 8、崩れ(collapsed)は 6、q = 6/8 = 0.75。
  const rows: MoveFeatureRow[] = [
    ...Array.from({ length: 6 }, () => row({ phase: "mid", longThink: false, collapse: true })),
    ...Array.from({ length: 2 }, () => row({ phase: "mid", longThink: false, collapse: false })),
    ...Array.from({ length: 2 }, () => row({ phase: "mid", longThink: false, collapse: null })),
  ];

  it("collapseCounted は collapse が null でない手だけ(10 行中 8 行)、collapsed は 6、q = 0.75", () => {
    const stats = statsOf(rows, [{ column: "phase", value: "mid" }]);
    expect(stats.collapseCounted).toBe(8);
    expect(stats.collapsed).toBe(6);
    expect(stats.q).toBe(0.75);
  });

  it("該当 0 件の組は collapseCounted=0, collapsed=0, q=null(0 除算にしない)", () => {
    const stats = statsOf(rows, [{ column: "phase", value: "early" }]);
    expect(stats.collapseCounted).toBe(0);
    expect(stats.collapsed).toBe(0);
    expect(stats.q).toBeNull();
  });
});

describe("enumerateCandidatesOf: 列挙の数(組合せの数と合う。null の値は候補にしない)", () => {
  it("深さ 1: phase(3) + fork(2) + inCheck(2) + afterLongThink(null を除くと 1 = false だけ) = 8 通り", () => {
    const candidates = enumerateCandidatesOf(DISCOVER_ROWS, 1);
    expect(candidates).toHaveLength(8);
    // afterLongThink は "false" の 1 通りだけ(null は候補にならない)
    const afterLongThinkValues = candidates.filter((c) => c.condition[0]!.column === "afterLongThink").map((c) => c.condition[0]!.value);
    expect(afterLongThinkValues).toEqual([false]);
  });

  it("深さ 2: 6 通りの列の組合せ(C(4,2))それぞれで実際に出た値の組だけを数え、合計 11", () => {
    const candidates = enumerateCandidatesOf(DISCOVER_ROWS, 2);
    // phase×afterLongThink は「mid×false」の 1 通りだけ(early・late は afterLongThink=null で除外)
    const phaseByAfterLongThink = candidates.filter((c) => c.condition.some((t) => t.column === "phase") && c.condition.some((t) => t.column === "afterLongThink"));
    expect(phaseByAfterLongThink).toHaveLength(1);
    // phase×fork は 3 通り(mid×true, early×false, late×false)
    const phaseByFork = candidates.filter((c) => c.condition.some((t) => t.column === "phase") && c.condition.some((t) => t.column === "fork"));
    expect(phaseByFork).toHaveLength(3);
    expect(candidates).toHaveLength(11); // 3(phase×fork) + 3(phase×inCheck) + 1(phase×afterLongThink) + 2(fork×inCheck) + 1(fork×afterLongThink) + 1(inCheck×afterLongThink)
  });

  it("深さ 3: 4 通りの列の組合せ(C(4,3))それぞれで 1 通りずつ(mid のグループ)+ phase の 3 列組だけ early・late も出る = 6", () => {
    const candidates = enumerateCandidatesOf(DISCOVER_ROWS, 3);
    expect(candidates).toHaveLength(6); // {phase,fork,inCheck}=3 + {phase,fork,ALT}=1 + {phase,inCheck,ALT}=1 + {fork,inCheck,ALT}=1
  });

  it("同じ列を 2 回使わない(3 条件はすべて異なる列)", () => {
    for (const candidate of enumerateCandidatesOf(DISCOVER_ROWS, 3)) {
      const columns = candidate.condition.map((t) => t.column);
      expect(new Set(columns).size).toBe(columns.length);
    }
  });
});

describe("isAdoptedOf: n ≥ minPairs(20) かつ p ≥ p0 × ratio(2)", () => {
  const baseMoves = 60;
  const baseLongThink = 15; // p0 = 0.25

  it("n=30, p=0.5(閾値ちょうど)は採用候補", () => {
    expect(isAdoptedOf({ n: 30, longThink: 15, p: 0.5, ...NO_COLLAPSE }, baseMoves, baseLongThink)).toBe(true);
  });

  it("n=19(20 未満)は p が高くても採用しない", () => {
    expect(isAdoptedOf({ n: 19, longThink: 19, p: 1, ...NO_COLLAPSE }, baseMoves, baseLongThink)).toBe(false);
  });

  it("n=30 でも p が閾値未満(0.25 未満)なら採用しない", () => {
    expect(isAdoptedOf({ n: 30, longThink: 7, p: 7 / 30, ...NO_COLLAPSE }, baseMoves, baseLongThink)).toBe(false);
  });
});

describe("isReproducedOf: n ≥ validateMinN(10) かつ p ≥ p0(検証用) × ratio(2)", () => {
  it("TIME_SEARCH_VALUES.validateMinN は 10", () => {
    expect(TIME_SEARCH_VALUES.validateMinN).toBe(10);
  });

  const baseMoves = 24;
  const baseLongThink = 6; // p0 = 0.25

  it("n=10(ちょうど境界)・p=0.5 は再現", () => {
    expect(isReproducedOf({ n: 10, longThink: 5, p: 0.5, ...NO_COLLAPSE }, baseMoves, baseLongThink)).toBe(true);
  });

  it("n=9(10 未満)は p が高くても再現しない", () => {
    expect(isReproducedOf({ n: 9, longThink: 9, p: 1, ...NO_COLLAPSE }, baseMoves, baseLongThink)).toBe(false);
  });
});

describe("isCollapseAdoptedOf・isCollapseReproducedOf: 崩れ版(collapseCounted・collapsed を使う)", () => {
  // isAdoptedOf・isReproducedOf の崩れ版。baseCollapseCounted=60・baseCollapsed=15(q0=0.25)で、
  // 発見用と同じ「20 以上・q0 の 2 倍以上」を確かめる(時間の枝と対称)。
  it("collapseCounted=30, collapsed=15(q=0.5、閾値ちょうど)は採用候補", () => {
    const stats = { n: 0, longThink: 0, p: 0, collapseCounted: 30, collapsed: 15, q: 0.5 };
    expect(isCollapseAdoptedOf(stats, 60, 15)).toBe(true);
  });

  it("collapseCounted=19(20 未満)は q が高くても採用しない", () => {
    const stats = { n: 0, longThink: 0, p: 0, collapseCounted: 19, collapsed: 19, q: 1 };
    expect(isCollapseAdoptedOf(stats, 60, 15)).toBe(false);
  });

  it("collapseCounted=10(ちょうど境界)・q=0.5 は再現(baseCollapseCounted=24・baseCollapsed=6・q0=0.25)", () => {
    const stats = { n: 0, longThink: 0, p: 0, collapseCounted: 10, collapsed: 5, q: 0.5 };
    expect(isCollapseReproducedOf(stats, 24, 6)).toBe(true);
  });

  it("collapseCounted=9(10 未満)は q が高くても再現しない", () => {
    const stats = { n: 0, longThink: 0, p: 0, collapseCounted: 9, collapsed: 9, q: 1 };
    expect(isCollapseReproducedOf(stats, 24, 6)).toBe(false);
  });
});

describe("searchOf: 発見用・検証用の 2 つの表から、深さごとの試した数・採用候補・再現の数を組む", () => {
  // 検証用(24 行)。グループ V1(12 行)は発見用のグループ 1 と同じ 4 列の値(mid・true・false・false)、
  // longThink は 6 true・6 false(n=12, p=0.5)。グループ V2(3 行)は phase=mid だが fork=false・inCheck=true・
  // afterLongThink=null にして、「phase=mid」単独の p だけを薄める(fork=true・inCheck=false・afterLongThink=false は
  // 汚さない)。グループ V3(9 行)は phase=late・fork=false・inCheck=true・afterLongThink=null。
  // p0(検証用)= 6 / 24 = 0.25(発見用と同じ)。
  const validateRows: MoveFeatureRow[] = [
    ...Array.from({ length: 12 }, (_, i) => row({ phase: "mid", fork: true, inCheck: false, afterLongThink: false, longThink: i < 6 })),
    ...Array.from({ length: 3 }, () => row({ phase: "mid", fork: false, inCheck: true, afterLongThink: null, longThink: false })),
    ...Array.from({ length: 9 }, () => row({ phase: "late", fork: false, inCheck: true, afterLongThink: null, longThink: false })),
  ];

  const result = searchOf(DISCOVER_ROWS, validateRows);

  // STEP TIME-CAUSE-3。この 2 つの表はどちらも collapse: null(既定)しか持たないので、崩れの分母は 0・
  // collapseRate は null(0 除算にしない既定)。偶然の目安(chanceReproduced)は検証用の長考率(0.25)・
  // validateMinN(10)・ratio(2)から計算される二項分布の裾 × 深さごとの採用候補の数(searchOf と同じ
  // `chanceLineProbabilityOf` を、既知の p0/n/ratio で直接呼んで確かめる)。
  const chanceProbability = chanceLineProbabilityOf(0.25, 10, 2);

  it("発見用・検証用の手の数と長考率(崩れの分母は 0、collapseRate は null)", () => {
    expect(result.discover).toEqual({ moves: 60, longThinkRate: 0.25, collapseCounted: 0, collapsed: 0, collapseRate: null });
    expect(result.validate).toEqual({ moves: 24, longThinkRate: 0.25, collapseCounted: 0, collapsed: 0, collapseRate: null });
  });

  it("深さごとの試した組の数・採用候補の数・偶然の目安(enumerateCandidatesOf・isAdoptedOf・chanceLineProbabilityOf と同じ数)", () => {
    expect(result.depths).toEqual([
      { depth: 1, tried: 8, adopted: 4, reproduced: 3, chanceReproduced: 4 * chanceProbability },
      { depth: 2, tried: 11, adopted: 6, reproduced: 6, chanceReproduced: 6 * chanceProbability },
      { depth: 3, tried: 6, adopted: 4, reproduced: 4, chanceReproduced: 4 * chanceProbability },
    ]);
  });

  it("深さ 1 で再現しないのは phase=mid だけ(検証用で fork=true・inCheck=false・afterLongThink=false と結び付かない 3 行が混ざり、p が 0.4 に薄まる)。崩れが無いので kind は null", () => {
    const notReproducedDepth1 = result.notReproduced.filter((c) => c.depth === 1);
    expect(notReproducedDepth1).toHaveLength(1);
    expect(notReproducedDepth1[0]!.condition).toEqual([{ column: "phase", value: "mid" }]);
    expect(notReproducedDepth1[0]!.validate).toEqual({ n: 15, longThink: 6, p: 6 / 15, ...NO_COLLAPSE });
    expect(notReproducedDepth1[0]!.kind).toBeNull();
  });

  it("再現した組の合計は 13(4+6+4 の採用候補のうち、phase=mid だけが外れる)", () => {
    expect(result.reproduced).toHaveLength(13);
    expect(result.notReproduced).toHaveLength(1);
  });

  it("再現した組は発見用・検証用の両方の n/p を持つ。崩れの分母が 0(両組)なので時間だけの A", () => {
    const forkTrue = result.reproduced.find((c) => c.depth === 1 && c.condition[0]!.column === "fork");
    expect(forkTrue).toBeDefined();
    expect(forkTrue!.discover).toEqual({ n: 30, longThink: 15, p: 0.5, ...NO_COLLAPSE });
    expect(forkTrue!.validate).toEqual({ n: 12, longThink: 6, p: 0.5, ...NO_COLLAPSE });
    expect(forkTrue!.kind).toBe("A");
  });

  it("崩れの探索(collapseSearch)は崩れの分母が 0 なので、どの深さでも採用候補が無い", () => {
    expect(result.collapseSearch.depths.every((d) => d.adopted === 0 && d.reproduced === 0)).toBe(true);
    expect(result.collapseSearch.reproduced).toHaveLength(0);
    expect(result.collapseSearch.notReproduced).toHaveLength(0);
  });

  it("共通因子の表(factors)は崩れが無いので、どの部品も timeAndCollapse・quickCollapse は null", () => {
    expect(result.factors.length).toBeGreaterThan(0);
    for (const factor of result.factors) {
      expect(factor.explains.timeAndCollapse).toBeNull();
      expect(factor.explains.quickCollapse).toBeNull();
    }
    // fork=true は単独で時間の線を越える(discover: n=30,p=0.5 ≥ 20・0.5。validate: n=12,p=0.5 ≥ 10・0.5)ので single。
    const forkFactor = result.factors.find((f) => f.column === "fork" && f.value === true);
    expect(forkFactor).toBeDefined();
    expect(forkFactor!.explains.longThink).toBe("single");
    expect(forkFactor!.singleOverLine).toEqual({ discover: true, validate: true });
  });
});

// ==== kindOf: 発見用・検証用の両方で「時間」「崩れ」を判定し、一致したときだけ A/B/C を付ける ====

describe("kindOf: 発見用・検証用が一致したときだけ A/B/C、一致しなければ null", () => {
  const discoverBase = { moves: 100, longThink: 25, collapseCounted: 100, collapsed: 25 }; // p0=0.25, q0=0.25
  const validateBase = { moves: 40, longThink: 10, collapseCounted: 40, collapsed: 10 }; // p0=0.25, q0=0.25

  it("時間・崩れとも両組で線を越えれば B", () => {
    const stats = { n: 20, longThink: 12, p: 0.6, collapseCounted: 20, collapsed: 12, q: 0.6 }; // p=q=0.6 ≥ 0.5(=0.25×2)
    expect(kindOf(stats, stats, discoverBase, validateBase)).toBe("B");
  });

  it("時間だけ両組で線を越えれば A(崩れは両組とも越えない)", () => {
    const stats = { n: 20, longThink: 12, p: 0.6, collapseCounted: 20, collapsed: 2, q: 0.1 }; // q=0.1 < 0.5
    expect(kindOf(stats, stats, discoverBase, validateBase)).toBe("A");
  });

  it("崩れだけ両組で線を越えれば C(時間は両組とも越えない)", () => {
    const stats = { n: 20, longThink: 2, p: 0.1, collapseCounted: 20, collapsed: 12, q: 0.6 }; // p=0.1 < 0.5
    expect(kindOf(stats, stats, discoverBase, validateBase)).toBe("C");
  });

  it("どちらも越えなければ null", () => {
    const stats = { n: 20, longThink: 2, p: 0.1, collapseCounted: 20, collapsed: 2, q: 0.1 };
    expect(kindOf(stats, stats, discoverBase, validateBase)).toBeNull();
  });

  it("発見用は B・検証用は A(崩れが検証用で外れる)なら null(一致していない)", () => {
    const discover = { n: 20, longThink: 12, p: 0.6, collapseCounted: 20, collapsed: 12, q: 0.6 }; // B
    const validate = { n: 20, longThink: 12, p: 0.6, collapseCounted: 20, collapsed: 2, q: 0.1 }; // A
    expect(kindOf(discover, validate, discoverBase, validateBase)).toBeNull();
  });
});

// ==== chanceLineProbabilityOf: 二項分布の裾(既知の値で確かめる。計画の「試験」に指定された値) ====

describe("chanceLineProbabilityOf: 偶然でも線を越える確率(二項分布の裾)", () => {
  it("p0=0.058, n=10, ratio=2 → 2 回以上(ceil(0.058×2×10)=2)の確率 ≈ 0.111", () => {
    expect(chanceLineProbabilityOf(0.058, 10, 2)).toBeCloseTo(0.111, 3);
  });

  it("p0=0.5, n=10, ratio=2 → k=ceil(10)=10(全部)の確率は 0.5^10", () => {
    expect(chanceLineProbabilityOf(0.5, 10, 2)).toBeCloseTo(0.5 ** 10, 10);
  });

  it("p0=0(基準率 0) → k=0 なので、必ず線を越える(確率 1)", () => {
    expect(chanceLineProbabilityOf(0, 10, 2)).toBe(1);
  });
});

// ==== searchOf: 崩れ(collapse)が実際に動く合成の表。kind B/C・collapseSearch・factors の explains を確かめる ====
//
// SEARCH_COLUMNS のうち「phase」だけを動かす(他の列はすべて既定の null のままなので、深さ 2・3 の候補は
// 0 になる ― enumerateCandidatesOf は「実際に手に出会った値の組」しか数えないため)。
// discover: MID(n=40, phase=mid, longThink 24t/16f=p0.6, collapse 24t/16f=q0.6) / EARLY(n=40, phase=early,
// longThink 全 false=p0, collapse 24t/16f=q0.6) / LATE(n=120, phase=late, longThink 全 false, collapse 全 false
// だが数える=collapseCounted 120・collapsed 0)。
// 合計 200 手: p0(全体)=24/200=0.12, q0(全体)=48/200=0.24。
// validate: MID_V(n=20, longThink 12t/8f=p0.6, collapse 12t/8f=q0.6) / EARLY_V(n=20, longThink 全 false,
// collapse 12t/8f=q0.6) / LATE_V(n=60, longThink 全 false, collapse 全 false だが数える=60/0)。
// 合計 100 手: p0=12/100=0.12, q0=24/100=0.24(発見用と同じ基準率になるよう揃えた)。
describe("searchOf: 崩れが動く合成の表(kind B・C、collapseSearch、factors の explains)", () => {
  const discoverRows: MoveFeatureRow[] = [
    ...Array.from({ length: 24 }, () => row({ phase: "mid", longThink: true, collapse: true })),
    ...Array.from({ length: 16 }, () => row({ phase: "mid", longThink: false, collapse: false })),
    ...Array.from({ length: 24 }, () => row({ phase: "early", longThink: false, collapse: true })),
    ...Array.from({ length: 16 }, () => row({ phase: "early", longThink: false, collapse: false })),
    ...Array.from({ length: 120 }, () => row({ phase: "late", longThink: false, collapse: false })),
  ];
  const validateRows: MoveFeatureRow[] = [
    ...Array.from({ length: 12 }, () => row({ phase: "mid", longThink: true, collapse: true })),
    ...Array.from({ length: 8 }, () => row({ phase: "mid", longThink: false, collapse: false })),
    ...Array.from({ length: 12 }, () => row({ phase: "early", longThink: false, collapse: true })),
    ...Array.from({ length: 8 }, () => row({ phase: "early", longThink: false, collapse: false })),
    ...Array.from({ length: 60 }, () => row({ phase: "late", longThink: false, collapse: false })),
  ];

  const result = searchOf(discoverRows, validateRows);

  it("全体の長考率・崩れ率(p0=0.12, q0=0.24。両組とも)", () => {
    expect(result.discover.longThinkRate).toBe(0.12);
    expect(result.discover.collapseRate).toBe(0.24);
    expect(result.validate.longThinkRate).toBe(0.12);
    expect(result.validate.collapseRate).toBe(0.24);
  });

  it("phase=mid は時間・崩れとも両組で線を越えるので、長考の探索で再現し kind=B", () => {
    const mid = result.reproduced.find((c) => c.depth === 1 && c.condition[0]!.value === "mid");
    expect(mid).toBeDefined();
    expect(mid!.kind).toBe("B");
  });

  it("phase=early は長考の採用候補にならない(discover の p=0 < 線)ので、長考の探索には出ない", () => {
    const early = [...result.reproduced, ...result.notReproduced].find((c) => c.depth === 1 && c.condition[0]!.value === "early");
    expect(early).toBeUndefined();
  });

  it("崩れを目的変数にした探索(collapseSearch)では、phase=mid(B)・phase=early(C)がともに再現する", () => {
    const mid = result.collapseSearch.reproduced.find((c) => c.depth === 1 && c.condition[0]!.value === "mid");
    const early = result.collapseSearch.reproduced.find((c) => c.depth === 1 && c.condition[0]!.value === "early");
    expect(mid).toBeDefined();
    expect(mid!.kind).toBe("B");
    expect(early).toBeDefined();
    expect(early!.kind).toBe("C");
  });

  it("phase=late は時間・崩れとも線を越えないので、どちらの探索にも出ない", () => {
    const lateInTime = [...result.reproduced, ...result.notReproduced].find((c) => c.condition[0]!.value === "late");
    const lateInCollapse = [...result.collapseSearch.reproduced, ...result.collapseSearch.notReproduced].find((c) => c.condition[0]!.value === "late");
    expect(lateInTime).toBeUndefined();
    expect(lateInCollapse).toBeUndefined();
  });

  it("深さ 2・3 は候補が無い(phase 以外の列がすべて既定の null のまま)", () => {
    expect(result.depths[1]!.tried).toBe(0);
    expect(result.depths[2]!.tried).toBe(0);
    expect(result.collapseSearch.depths[1]!.tried).toBe(0);
    expect(result.collapseSearch.depths[2]!.tried).toBe(0);
  });

  it("factors: phase=mid は longThink・timeAndCollapse とも single、phase=early は timeAndCollapse は null で quickCollapse が single", () => {
    const midFactor = result.factors.find((f) => f.column === "phase" && f.value === "mid");
    const earlyFactor = result.factors.find((f) => f.column === "phase" && f.value === "early");
    expect(midFactor).toBeDefined();
    expect(midFactor!.explains).toEqual({ longThink: "single", timeAndCollapse: "single", quickCollapse: null });
    expect(earlyFactor).toBeDefined();
    expect(earlyFactor!.explains).toEqual({ longThink: null, timeAndCollapse: null, quickCollapse: "single" });
  });

  it("factors: inReproduced・inCollapseReproduced・inKindB・inKindC は深さ 1 に 1 件ずつ(2・3 条件の組が無いため)", () => {
    const midFactor = result.factors.find((f) => f.column === "phase" && f.value === "mid")!;
    expect(midFactor.inReproduced).toEqual({ depth1: 1, depth2: 0, depth3: 0, total: 1 });
    expect(midFactor.inKindB).toBe(1);
    expect(midFactor.inCollapseReproduced).toEqual({ depth1: 1, depth2: 0, depth3: 0, total: 1 });

    const earlyFactor = result.factors.find((f) => f.column === "phase" && f.value === "early")!;
    expect(earlyFactor.inReproduced).toEqual({ depth1: 0, depth2: 0, depth3: 0, total: 0 });
    expect(earlyFactor.inKindB).toBe(0);
    expect(earlyFactor.inCollapseReproduced).toEqual({ depth1: 1, depth2: 0, depth3: 0, total: 1 });
    expect(earlyFactor.inKindC).toBe(1);
  });

  it("factors の並びは single の数 → combo の数 → inReproduced.total の多い順(mid は single が 2、early は single が 1)", () => {
    const midIndex = result.factors.findIndex((f) => f.column === "phase" && f.value === "mid");
    const earlyIndex = result.factors.findIndex((f) => f.column === "phase" && f.value === "early");
    expect(midIndex).toBeGreaterThanOrEqual(0);
    expect(earlyIndex).toBeGreaterThan(midIndex);
  });
});
