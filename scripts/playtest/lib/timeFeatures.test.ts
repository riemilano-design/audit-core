// STEP TIME-CAUSE-2(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §7.2・§7.5)。lib/timeFeatures.ts の単体試験。
// **エンジンは起動しない**(合成の 1 局〈先手〉だけを使う。実データ〈tatsunami20・tatsunami3〉での確認は、
// 実装担当の報告に書く一回限りの手作業 ― lib/timeCause.test.ts と同じ流儀)。
//
// 【正解の置き方】列の値は、moveSeconds・評価(engineRef)・whatif の入力から手で計算し(コメントに書く)、
// 実装の出力から写さない。局面・合法性は `plantedRecords`(既存の試験専用ヘルパー、GAME01_MOVES の最初の
// 16 手 ― 実在の対局から取った合法手)に任せる。

import { describe, expect, it } from "vitest";
import { GAME01_MOVES, engineRef, plantedRecords } from "./failureEventFixtures.js";
import { buildGameMoveFeatureRows, type MoveFeatureWhatifPosition } from "./timeFeatures.js";
import type { TimeCauseFixedKifu } from "./timeCause.js";

// GAME01_MOVES の最初の 16 手(先手・mirrored: false)。total = 16。
// phaseOf(branchPly, 16): early は branchPly/16 < 1/3 ⇔ branchPly ≤ 5、mid は < 2/3 ⇔ branchPly ≤ 10、
// それ以外が late。本人(先手)は奇数手: 1・3・5(早)/7・9(中)/11・13・15(遅)。
const MOVES_16: readonly string[] = GAME01_MOVES.slice(0, 16);

function mt(spentSec: number): { spentSec: number; totalSec: number } {
  return { spentSec, totalSec: spentSec }; // totalSec はこの段では使わない(実装担当の判断。値は仮)
}

// 本人(先手)の消費秒。kifPly: 1=3, 3=10(長考), 5=6, 7=1, 9=4, 11=12(長考), 13=2, 15=8。
// spentBucketsSec = [1, 4, 9] なので段は ≤1 / ≤4 / ≤9 / >9。
const MOVE_SECONDS = [
  mt(3), // 1(own, early): ≤4
  mt(1), // 2(opp)
  mt(10), // 3(own, early): >9・長考
  mt(1), // 4(opp)
  mt(6), // 5(own, early): ≤9
  mt(1), // 6(opp)
  mt(1), // 7(own, mid): ≤1
  mt(1), // 8(opp)
  mt(4), // 9(own, mid): ≤4
  mt(1), // 10(opp)
  mt(12), // 11(own, late): >9・長考
  mt(1), // 12(opp)
  mt(2), // 13(own, late): ≤4
  mt(1), // 14(opp)
  mt(8), // 15(own, late): ≤9
  mt(1), // 16(opp)
];

const FIXED: TimeCauseFixedKifu = {
  id: "synthetic-features",
  mirrored: false,
  moves: MOVES_16,
  moveSeconds: MOVE_SECONDS,
};

// 評価(baseline.scoreCp)。本人の手の「直前の行」(ply = recordPly − 1)に植える。
// STANDING_BOUNDS = { aheadCp: 300, behindCp: -300 }。
const PLANT = {
  0: engineRef(50), // kifPly1 の直前 → level
  2: engineRef(400), // kifPly3 の直前 → ahead
  4: engineRef(300), // kifPly5 の直前 → ahead
  6: engineRef(350), // kifPly7 の直前 → ahead
  8: engineRef(-400), // kifPly9 の直前 → behind
  10: engineRef(0), // kifPly11 の直前 → level
  12: engineRef(310), // kifPly13 の直前 → ahead
  14: engineRef(1000), // kifPly15 の直前 → ahead
};

const RECORDS = plantedRecords(MOVES_16 as string[], PLANT);
const sfenAt = (ply: number): string => RECORDS.find((r) => r.ply === ply && r.phase === "ready")!.sfen;

// whatif-v2 の position 行(2 手ぶんだけ与える。実戦の手 = 第 1 候補にして印の対称性を保つ ― 実装担当の判断、
// 「取る/打つ/王手/捨て駒/引く」の値そのものは lib/read.test.ts が別に確かめている。ここでは配線〈正しい
// sfen・正しい手を moveMarksOf に渡し、列に正しく写す〉だけを確かめる)。
const WHATIF: MoveFeatureWhatifPosition[] = [
  {
    ply: 9, // kifPly9(recordPly = kifPly。mirrored でないので plyOffset 0)
    sfen: sfenAt(8),
    fork: true,
    top1Side: "attack",
    actualSide: "defense",
    top1Move: MOVES_16[8]!, // "2f2e"
    actualMove: MOVES_16[8]!,
    actualRank: 3,
    lossCpValue: 500,
    lossIsLowerBound: false,
  },
  {
    ply: 13,
    sfen: sfenAt(12),
    fork: true,
    top1Side: "none",
    actualSide: "none",
    top1Move: MOVES_16[12]!, // "3i3h"
    actualMove: MOVES_16[12]!,
    actualRank: null,
    lossCpValue: null,
    lossIsLowerBound: true,
  },
];

const ROWS = buildGameMoveFeatureRows(FIXED, 1, "discover", 90, RECORDS, WHATIF);
const rowAt = (kifPly: number) => ROWS.find((r) => r.kifPly === kifPly)!;

describe("buildGameMoveFeatureRows: 行の数・識別子", () => {
  it("本人(先手)の 8 手ぶん、kifPly 1・3・5・7・9・11・13・15 の順で並ぶ", () => {
    expect(ROWS.map((r) => r.kifPly)).toEqual([1, 3, 5, 7, 9, 11, 13, 15]);
    for (const row of ROWS) {
      expect(row.kifuId).toBe("synthetic-features");
      expect(row.group).toBe("discover");
      expect(row.gameNo).toBe(1);
    }
  });
});

describe("buildGameMoveFeatureRows: 時間(spentBucket・直前の手・直前 3/5 手の合計・afterLongThink)", () => {
  it("kifPly1(初手): 直前の手が無いので prevOwn 系はすべて null", () => {
    const row = rowAt(1);
    expect(row.spentSec).toBe(3);
    expect(row.spentBucket).toBe("≤4");
    expect(row.prevOwnSpentBucket).toBeNull();
    expect(row.prev3SumBucket).toBeNull();
    expect(row.prev5SumBucket).toBeNull();
    expect(row.afterLongThink).toBeNull();
    expect(row.longThink).toBe(false);
  });

  it("kifPly3: 直前の手(kifPly1・3 秒)がある。prev3・prev5 はまだ足りない", () => {
    const row = rowAt(3);
    expect(row.spentBucket).toBe(">9");
    expect(row.longThink).toBe(true);
    expect(row.prevOwnSpentBucket).toBe("≤4"); // 3 秒
    expect(row.afterLongThink).toBe(false); // 3 秒 < 10
    expect(row.prev3SumBucket).toBeNull();
    expect(row.prev5SumBucket).toBeNull();
  });

  it("kifPly5: 直前(kifPly3・10 秒)は長考。prev3 はまだ 2 手しか無いので null", () => {
    const row = rowAt(5);
    expect(row.prevOwnSpentBucket).toBe(">9"); // 10 秒
    expect(row.afterLongThink).toBe(true); // 10 秒 ≥ 10
    expect(row.prev3SumBucket).toBeNull();
  });

  it("kifPly7: 直前 3 手(5・3・1 手目 = 6+10+3 = 19 秒)がそろう。直前 5 手はまだ", () => {
    const row = rowAt(7);
    expect(row.spentBucket).toBe("≤1");
    expect(row.prevOwnSpentBucket).toBe("≤9"); // 6 秒
    expect(row.prev3SumBucket).toBe(">9"); // 19 秒
    expect(row.prev5SumBucket).toBeNull();
  });

  it("kifPly11: 直前 5 手(9・7・5・3・1 手目 = 4+1+6+10+3 = 24 秒)がそろう", () => {
    const row = rowAt(11);
    expect(row.spentBucket).toBe(">9");
    expect(row.longThink).toBe(true);
    expect(row.prevOwnSpentBucket).toBe("≤4"); // 9 手目 4 秒
    expect(row.prev3SumBucket).toBe(">9"); // 9+7+5 手目 = 4+1+6 = 11 秒
    expect(row.prev5SumBucket).toBe(">9"); // 24 秒
  });

  it("kifPly13: 直前(11 手目・12 秒)は長考", () => {
    const row = rowAt(13);
    expect(row.prevOwnSpentBucket).toBe(">9");
    expect(row.afterLongThink).toBe(true);
    expect(row.prev3SumBucket).toBe(">9"); // 11+9+7 手目 = 12+4+1 = 17 秒
    expect(row.prev5SumBucket).toBe(">9"); // 11+9+7+5+3 手目 = 12+4+1+6+10 = 33 秒
  });
});

describe("buildGameMoveFeatureRows: 残り秒(--time-limit-sec 90)", () => {
  it("kifPly1: 直前の消費が 0 なので残り 90 → 60〜119", () => {
    expect(rowAt(1).remainingBucket).toBe("60-119");
  });

  it("kifPly15: 直前までの本人の消費の合計(1+3+5+7+9+11+13 手目 = 3+10+6+1+4+12+2 = 38 秒)。残り 52 → 60 未満", () => {
    expect(rowAt(15).remainingBucket).toBe("<60");
  });
});

describe("buildGameMoveFeatureRows: 局面(phase・evalBand・evalChangePrev・inCheck)", () => {
  it("phase は early: 1・3・5 / mid: 7・9 / late: 11・13・15", () => {
    expect(ROWS.map((r) => r.phase)).toEqual(["early", "early", "early", "mid", "mid", "late", "late", "late"]);
  });

  it("evalBand は植えた評価(STANDING_BOUNDS ±300)のとおり", () => {
    expect(rowAt(1).evalBand).toBe("level"); // 50
    expect(rowAt(3).evalBand).toBe("ahead"); // 400
    expect(rowAt(9).evalBand).toBe("behind"); // -400
    expect(rowAt(11).evalBand).toBe("level"); // 0
  });

  it("evalChangePrev は直前の自分の手番からの評価の差(上/同/下)。kifPly1 は直前が無いので null", () => {
    expect(rowAt(1).evalChangePrev).toBeNull();
    expect(rowAt(3).evalChangePrev).toBe("up"); // 400 − 50 = 350 ≥ 300
    expect(rowAt(5).evalChangePrev).toBe("same"); // 300 − 400 = −100
    expect(rowAt(7).evalChangePrev).toBe("same"); // 350 − 300 = 50
    expect(rowAt(9).evalChangePrev).toBe("down"); // −400 − 350 = −750 ≤ −300
    expect(rowAt(11).evalChangePrev).toBe("up"); // 0 − (−400) = 400 ≥ 300
  });

  it("inCheck: この合成局は王手を挟まない(実在の対局の冒頭 16 手)ので、すべて false", () => {
    for (const row of ROWS) expect(row.inCheck).toBe(false);
  });
});

describe("buildGameMoveFeatureRows: 選択(whatif-v2 がある手だけ)", () => {
  it("kifPly1: whatif-v2 が無いので、選択の列はすべて null", () => {
    const row = rowAt(1);
    expect(row.fork).toBeNull();
    expect(row.top1Side).toBeNull();
    expect(row.actualSide).toBeNull();
    expect(row.lossBand).toBeNull();
    expect(row.inTop5).toBeNull();
    expect(row.actualCapture).toBeNull();
    expect(row.top1Capture).toBeNull();
  });

  it("kifPly9: loss.cpValue = 500(≥ 300 → over300)、actualRank = 3(候補内 → inTop5)", () => {
    const row = rowAt(9);
    expect(row.fork).toBe(true);
    expect(row.top1Side).toBe("attack");
    expect(row.actualSide).toBe("defense");
    expect(row.lossBand).toBe("over300");
    expect(row.inTop5).toBe(true);
    // 実戦の手 = 第 1 候補(同じ手)なので、actual と top1 の印は一致する
    expect(row.actualCapture).toBe(row.top1Capture);
    expect(row.actualDrop).toBe(row.top1Drop);
    expect(row.actualGivesCheck).toBe(row.top1GivesCheck);
    expect(row.actualSacrifice).toBe(row.top1Sacrifice);
    expect(row.actualRetreat).toBe(row.top1Retreat);
    // 2f2e(序盤の歩の前進。打つ手でも成る手でもなく、この局面で捨て駒・王手にもならない)
    expect(row.actualCapture).toBe(false);
    expect(row.actualDrop).toBe(false);
    expect(row.actualGivesCheck).toBe(false);
    expect(row.actualRetreat).toBe(false);
  });

  it("kifPly13: isLowerBound(候補に無い)なので lossBand は outOfCandidates、inTop5 は false", () => {
    const row = rowAt(13);
    expect(row.fork).toBe(true);
    expect(row.lossBand).toBe("outOfCandidates");
    expect(row.inTop5).toBe(false);
  });
});

describe("buildGameMoveFeatureRows: 相手(直前の手の印)", () => {
  it("kifPly3 の直前(kifPly2・1c1d、ただの歩の前進)は取る/打つ/王手/成るのいずれでもない", () => {
    const row = rowAt(3);
    expect(row.oppPrevCapture).toBe(false);
    expect(row.oppPrevDrop).toBe(false);
    expect(row.oppPrevGivesCheck).toBe(false);
    expect(row.oppPrevPromotion).toBe(false);
  });

  it("kifPly1: 直前の相手の手が無い(初手)ので null", () => {
    const row = rowAt(1);
    expect(row.oppPrevCapture).toBeNull();
    expect(row.oppPrevDrop).toBeNull();
    expect(row.oppPrevGivesCheck).toBeNull();
    expect(row.oppPrevPromotion).toBeNull();
  });
});

describe("buildGameMoveFeatureRows: 形(C9。全行に同じ値)", () => {
  it("序盤の終わり(最初の中盤の手 = kifPly7)の直前まで、両者の飛車とも初期の筋のまま(動いていない)", () => {
    // MOVES_16 の最初の 6 手(2g2f・1c1d・7g7f・8c8d・7i7h・3c3d)はどちらの飛車も動かさない。
    for (const row of ROWS) {
      expect(row.ownRookMoved).toBe(false);
      expect(row.oppRookMoved).toBe(false);
    }
  });
});
