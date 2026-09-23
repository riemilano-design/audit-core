// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.3・§7.5)。lib/timeSearch.ts の単体試験。
// **エンジンは起動しない**(合成の表だけを使う)。

import { describe, expect, it } from "vitest";
import type { MoveFeatureRow } from "./timeFeatures.js";
import { TIME_SEARCH_VALUES, enumerateCandidatesOf, isAdoptedOf, isReproducedOf, searchOf, statsOf, type Condition } from "./timeSearch.js";

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

describe("statsOf: 手で数えた n・長考の数・p と一致する", () => {
  it("空の条件(全行)。n=60, longThink=15, p=0.25", () => {
    expect(statsOf(DISCOVER_ROWS, [])).toEqual({ n: 60, longThink: 15, p: 0.25 });
  });

  it("単独条件 phase=mid。n=30, longThink=15, p=0.5", () => {
    const condition: Condition = [{ column: "phase", value: "mid" }];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 30, longThink: 15, p: 0.5 });
  });

  it("afterLongThink=false は mid のグループだけに出る(early・late は null なので一致しない)。n=30", () => {
    const condition: Condition = [{ column: "afterLongThink", value: false }];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 30, longThink: 15, p: 0.5 });
  });

  it("該当 0 件の組は n=0, p=0(0 除算にならない)", () => {
    const condition: Condition = [
      { column: "phase", value: "mid" },
      { column: "fork", value: false },
    ];
    expect(statsOf(DISCOVER_ROWS, condition)).toEqual({ n: 0, longThink: 0, p: 0 });
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
    expect(isAdoptedOf({ n: 30, longThink: 15, p: 0.5 }, baseMoves, baseLongThink)).toBe(true);
  });

  it("n=19(20 未満)は p が高くても採用しない", () => {
    expect(isAdoptedOf({ n: 19, longThink: 19, p: 1 }, baseMoves, baseLongThink)).toBe(false);
  });

  it("n=30 でも p が閾値未満(0.25 未満)なら採用しない", () => {
    expect(isAdoptedOf({ n: 30, longThink: 7, p: 7 / 30 }, baseMoves, baseLongThink)).toBe(false);
  });
});

describe("isReproducedOf: n ≥ validateMinN(10) かつ p ≥ p0(検証用) × ratio(2)", () => {
  it("TIME_SEARCH_VALUES.validateMinN は 10", () => {
    expect(TIME_SEARCH_VALUES.validateMinN).toBe(10);
  });

  const baseMoves = 24;
  const baseLongThink = 6; // p0 = 0.25

  it("n=10(ちょうど境界)・p=0.5 は再現", () => {
    expect(isReproducedOf({ n: 10, longThink: 5, p: 0.5 }, baseMoves, baseLongThink)).toBe(true);
  });

  it("n=9(10 未満)は p が高くても再現しない", () => {
    expect(isReproducedOf({ n: 9, longThink: 9, p: 1 }, baseMoves, baseLongThink)).toBe(false);
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

  it("発見用・検証用の手の数と長考率", () => {
    expect(result.discover).toEqual({ moves: 60, longThinkRate: 0.25 });
    expect(result.validate).toEqual({ moves: 24, longThinkRate: 0.25 });
  });

  it("深さごとの試した組の数・採用候補の数(enumerateCandidatesOf・isAdoptedOf と同じ数)", () => {
    expect(result.depths).toEqual([
      { depth: 1, tried: 8, adopted: 4, reproduced: 3 },
      { depth: 2, tried: 11, adopted: 6, reproduced: 6 },
      { depth: 3, tried: 6, adopted: 4, reproduced: 4 },
    ]);
  });

  it("深さ 1 で再現しないのは phase=mid だけ(検証用で fork=true・inCheck=false・afterLongThink=false と結び付かない 3 行が混ざり、p が 0.4 に薄まる)", () => {
    const notReproducedDepth1 = result.notReproduced.filter((c) => c.depth === 1);
    expect(notReproducedDepth1).toHaveLength(1);
    expect(notReproducedDepth1[0]!.condition).toEqual([{ column: "phase", value: "mid" }]);
    expect(notReproducedDepth1[0]!.validate).toEqual({ n: 15, longThink: 6, p: 6 / 15 });
  });

  it("再現した組の合計は 13(4+6+4 の採用候補のうち、phase=mid だけが外れる)", () => {
    expect(result.reproduced).toHaveLength(13);
    expect(result.notReproduced).toHaveLength(1);
  });

  it("再現した組は発見用・検証用の両方の n/p を持つ", () => {
    const forkTrue = result.reproduced.find((c) => c.depth === 1 && c.condition[0]!.column === "fork");
    expect(forkTrue).toBeDefined();
    expect(forkTrue!.discover).toEqual({ n: 30, longThink: 15, p: 0.5 });
    expect(forkTrue!.validate).toEqual({ n: 12, longThink: 6, p: 0.5 });
  });
});
