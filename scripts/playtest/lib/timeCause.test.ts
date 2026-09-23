// STEP TIME-CAUSE(docs/STEP_TIME_CAUSE_PLAN_2026-09-24.md §2・§3)。lib/timeCause.ts の単体試験。
// **エンジンは起動しない**(合成の入力だけを使う)。実データ(tatsunami3・tatsunami20・tatsunami-long)での
// 確認は、実装担当の報告に書く一回限りの手作業(out/ は gitignore で、このリポジトリのほかの試験も
// gitignore の実データには依存していない ― lib/finalPosition.test.ts と同じ流儀)。

import { describe, expect, it } from "vitest";

import { DEFAULT_INITIAL_SFEN } from "../../../apps/server/src/analysis/moveHistory.js";
import { phaseOf, phaseSpentOfGame } from "./reportData.js";
import {
  buildGameTimeCause,
  buildGroupTimeCause,
  buildTimeCauseFile,
  medianOf,
  rookOnInitialFileOf,
  sfenBeforeOriginalKifPly,
  type GameTimeCause,
  type TimeCauseFixedKifu,
  type TimeCauseWhatifPositionInput,
} from "./timeCause.js";

// 合成の局(実在の 30 手の対局〈scripts/playtest/kifu/2026-09-12-live-30moves-claude-1.json〉の最初の 24 手。
// 全て合法手で、applyMove で最後まで進められる)。7 手目 "2h1h" が先手の飛車を 2 筋から動かす手 ― rookMark の
// 「動いた」側の材料に使う。
const MOVES_24: readonly string[] = [
  "4i5h",
  "1a1b",
  "5i4h",
  "6c6d",
  "4h3h",
  "3c3d",
  "2h1h", // 7 手目: 先手の飛車が 2 筋から離れる
  "7a6b",
  "3h2h",
  "6b6c",
  "3i3h",
  "6c7d",
  "6i5i",
  "7d7e",
  "5i4i",
  "8c8d",
  "4g4f",
  "8d8e",
  "8g8f",
  "8e8f",
  "1g1f",
  "8f8g+",
  "1f1e",
  "8g8h",
];

function mt(spentSec: number, totalSec: number): { spentSec: number; totalSec: number } {
  return { spentSec, totalSec };
}

// ---- 合成局 A(先手・mirrored: false。timeUpLoss。組「3 分」) ----
// total = 24。1/3 = 8・2/3 = 16 なので、早い = recordPly 1〜7・中 = 8〜15・遅い = 16〜24(phaseOf の定義どおり)。
// 本人(先手)は奇数手。early: 1,3,5,7 / mid: 9,11,13,15 / late: 17,19,21,23。
const FIXED_A: TimeCauseFixedKifu = {
  id: "synthetic-a",
  mirrored: false,
  moves: MOVES_24,
  moveSeconds: [
    mt(2, 2), // 1 早
    mt(1, 1), // 2 相手
    mt(10, 12), // 3 早・長考
    mt(1, 2), // 4 相手
    mt(11, 23), // 5 早・長考(3 と連続する長考)
    mt(1, 3), // 6 相手
    mt(3, 26), // 7 早
    mt(1, 4), // 8 相手
    mt(10, 36), // 9 中・長考
    mt(1, 5), // 10 相手
    mt(5, 41), // 11 中・中考(5〜9 秒)
    mt(1, 6), // 12 相手
    mt(25, 66), // 13 中・長考(最長の手)
    mt(1, 7), // 14 相手
    mt(1, 67), // 15 中
    mt(1, 8), // 16 相手
    mt(6, 73), // 17 遅・中考
    mt(1, 9), // 18 相手
    mt(10, 83), // 19 遅・長考
    mt(1, 10), // 20 相手
    mt(10, 93), // 21 遅・長考(19 と連続する長考)
    mt(1, 11), // 22 相手
    mt(0, 93), // 23 遅
    mt(1, 12), // 24 相手
  ],
};

// whatif-v2: 長考の手(recordPly 3・5・9・13・19・21)のうち 3・5・9・13 だけに position 行がある
// (19・21 は結合できない長考 ― 分母に数えない)。
const WHATIF_A: TimeCauseWhatifPositionInput[] = [
  { ply: 3, fork: true, top1Side: "attack", actualSide: "defense" }, // 長考・分かれ道・側が逆
  { ply: 5, fork: false, top1Side: "none", actualSide: "none" }, // 長考だが分かれ道でない
  { ply: 9, fork: true, top1Side: "defense", actualSide: "defense" }, // 長考・分かれ道・側は同じ
  { ply: 13, fork: false, top1Side: "none", actualSide: "none" },
];

// ---- 合成局 B(後手・mirrored: true。timeUpLoss ではない。組「10 分」) ----
// 本人(後手)は偶数手。early: 2,4,6,8 / mid: 10,12,14,16 / late: 18,20,22,24。whatif-v2 は無い組(null)。
const FIXED_B: TimeCauseFixedKifu = {
  id: "synthetic-b",
  mirrored: true,
  plyOffset: 1,
  originalMoves: MOVES_24,
  moves: MOVES_24, // このファイルが読む関数は originalMoves がある限り moves を読まない(originalMovesOf)
  moveSeconds: [
    mt(1, 1), // 1 相手
    mt(1, 1), // 2 早
    mt(1, 2), // 3 相手
    mt(10, 11), // 4 早・長考
    mt(1, 3), // 5 相手
    mt(2, 13), // 6 早
    mt(1, 4), // 7 相手
    mt(5, 18), // 8 早・中考
    mt(1, 5), // 9 相手
    mt(12, 30), // 10 中・長考
    mt(1, 6), // 11 相手
    mt(12, 42), // 12 中・長考(10 と連続する長考)
    mt(1, 7), // 13 相手
    mt(2, 44), // 14 中
    mt(1, 8), // 15 相手
    mt(1, 45), // 16 中
    mt(1, 9), // 17 相手
    mt(30, 75), // 18 遅・長考(最長の手)
    mt(1, 10), // 19 相手
    mt(1, 76), // 20 遅
    mt(1, 11), // 21 相手
    mt(8, 84), // 22 遅・中考
    mt(1, 12), // 23 相手
    mt(0, 84), // 24 遅
  ],
};

describe("buildGameTimeCause", () => {
  it("合成局 A(先手): C1〜C9・remainingSec・midMoveSeconds を正しく分解する", () => {
    const game = buildGameTimeCause(FIXED_A, 1, "3 分", 180, true, WHATIF_A);

    expect(game.gameNo).toBe(1);
    expect(game.kifuId).toBe("synthetic-a");
    expect(game.group).toBe("3 分");
    expect(game.timeUpLoss).toBe(true);
    expect(game.total).toBe(24);

    // C1・C2(+ late)
    expect(game.phaseSpentSec).toEqual({ early: 26, mid: 41, late: 26 });

    // C3
    expect(game.longThinkCountByPhase).toEqual({ early: 2, mid: 2, late: 2 });
    expect(game.longThinkTotal).toBe(6);

    // C4
    expect(game.longestMove).toEqual({ sec: 25, kifPly: 13 });

    // C5(3・5 と 19・21 の 2 組)
    expect(game.longThinkStreakCount).toBe(2);

    // C6
    expect(game.midThinkByPhase).toEqual({ early: { count: 0, sec: 0 }, mid: { count: 1, sec: 5 }, late: { count: 1, sec: 6 } });
    expect(game.midThinkTotal).toEqual({ count: 2, sec: 11 });

    // C7: 長考 6 のうち結合できたのは 4(3・5・9・13)、分かれ道は 2(3・9)
    expect(game.forkAmongLongThink).toEqual({ numerator: 2, denominator: 4 });

    // C8: 長考かつ分かれ道は 2(3・9)、側が逆は 1(3 だけ。9 は top1=defense/actual=defense で「同じ」)
    expect(game.oppositeSideAmongForkLongThink).toEqual({ numerator: 1, denominator: 2 });

    // C9: 7 手目で先手の飛車が 2 筋を離れるので、9 手目(中盤の最初の本人の手)の直前には own が false
    expect(game.rookMark).toEqual({ own: false, opponent: true });

    // remainingSec = 180 − 93(最後に読めた本人の手の累積)
    expect(game.remainingSec).toBe(87);

    // 中盤の手ごとの秒の列(9・11・13・15 手目)。9・13 は fork: true/false(whatif-v2 と結合)、11・15 は未結合(null)
    expect(game.midMoveSeconds).toEqual([
      { kifPly: 9, sec: 10, fork: true },
      { kifPly: 11, sec: 5, fork: null },
      { kifPly: 13, sec: 25, fork: false },
      { kifPly: 15, sec: 1, fork: null },
    ]);
  });

  it("合成局 B(後手・mirrored: true): whatif-v2 が無い組では C7・C8・midMoveSeconds の fork が null", () => {
    const game = buildGameTimeCause(FIXED_B, 2, "10 分", 600, false, null);

    expect(game.kifuId).toBe("synthetic-b");
    expect(game.timeUpLoss).toBe(false);
    expect(game.total).toBe(24);

    expect(game.phaseSpentSec).toEqual({ early: 18, mid: 27, late: 39 });
    expect(game.longThinkCountByPhase).toEqual({ early: 1, mid: 2, late: 1 });
    expect(game.longThinkTotal).toBe(4);
    expect(game.longestMove).toEqual({ sec: 30, kifPly: 18 });
    expect(game.longThinkStreakCount).toBe(1); // 10・12 手目
    expect(game.midThinkByPhase).toEqual({ early: { count: 1, sec: 5 }, mid: { count: 0, sec: 0 }, late: { count: 1, sec: 8 } });
    expect(game.midThinkTotal).toEqual({ count: 2, sec: 13 });

    expect(game.forkAmongLongThink).toBeNull();
    expect(game.oppositeSideAmongForkLongThink).toBeNull();

    // C9: 本人(後手)は 8 筋の飛車を動かしていないので own は true。相手(先手)は 7 手目に動いたので false。
    expect(game.rookMark).toEqual({ own: true, opponent: false });

    expect(game.remainingSec).toBe(600 - 84);

    expect(game.midMoveSeconds.every((m) => m.fork === null)).toBe(true);
    expect(game.midMoveSeconds.map((m) => m.kifPly)).toEqual([10, 12, 14, 16]);
  });

  it("moveSeconds が無い固定棋譜は例外を投げる(秒の読めない棋譜は扱わない)", () => {
    expect(() => buildGameTimeCause({ id: "no-seconds", mirrored: false, moves: MOVES_24 }, 1, "3 分", 180, false, null)).toThrow();
  });
});

describe("phaseOf の境界(reportData.ts の phaseSpentOfGame と同じ側に落ちることの突き合わせ)", () => {
  it("合成局 A・B の early/mid/late が、reportData.ts の phaseSpentOfGame(同じ既存関数)の結果と一致する", () => {
    const gameA = buildGameTimeCause(FIXED_A, 1, "3 分", 180, true, WHATIF_A);
    // phaseSpentOfGame は game.side・game.plyOffset だけを読む(lib/reportData.ts のコメント参照)。
    const crossA = phaseSpentOfGame({ side: "先手", plyOffset: 0 } as never, FIXED_A.moveSeconds!, 24);
    expect(gameA.phaseSpentSec).toEqual(crossA);

    const gameB = buildGameTimeCause(FIXED_B, 2, "10 分", 600, false, null);
    const crossB = phaseSpentOfGame({ side: "後手", plyOffset: 1 } as never, FIXED_B.moveSeconds!, 24);
    expect(gameB.phaseSpentSec).toEqual(crossB);
  });

  it("境界の recordPly(total=24 で 8・16)が early/mid・mid/late のどちら側に落ちるかを phaseOf そのもので確かめる", () => {
    expect(phaseOf(7, 24)).toBe("early");
    expect(phaseOf(8, 24)).toBe("mid"); // 8/24 = 1/3 ちょうどは mid 側(fraction < 1/3 でなくなる)
    expect(phaseOf(15, 24)).toBe("mid");
    expect(phaseOf(16, 24)).toBe("late"); // 16/24 = 2/3 ちょうどは late 側
  });
});

describe("rookOnInitialFileOf・sfenBeforeOriginalKifPly", () => {
  it("初期局面(0 手)は先手 2 筋・後手 8 筋のどちらにも飛車が居る", () => {
    const sfen = sfenBeforeOriginalKifPly(MOVES_24, 1); // 1 手目の直前 = 0 手進めた局面
    expect(sfen).toBe(DEFAULT_INITIAL_SFEN);
    expect(rookOnInitialFileOf(sfen, "先手")).toBe(true);
    expect(rookOnInitialFileOf(sfen, "後手")).toBe(true);
  });

  it("7 手目 '2h1h' の直後(8 手目の直前)は先手の飛車が 2 筋に居ない", () => {
    const sfen = sfenBeforeOriginalKifPly(MOVES_24, 8);
    expect(rookOnInitialFileOf(sfen, "先手")).toBe(false);
    expect(rookOnInitialFileOf(sfen, "後手")).toBe(true);
  });
});

describe("medianOf", () => {
  it("空配列は null、奇数個は中央値、偶数個は中央 2 件の平均", () => {
    expect(medianOf([])).toBeNull();
    expect(medianOf([5])).toBe(5);
    expect(medianOf([1, 3, 2])).toBe(2);
    expect(medianOf([1, 2, 3, 4])).toBe(2.5);
  });
});

describe("buildGroupTimeCause・buildTimeCauseFile(組ごとの集計)", () => {
  // 盤面を伴わない合成の GameTimeCause(直接値を置く。aggregation のロジックだけを確かめる)。
  function fakeGame(overrides: Partial<GameTimeCause>): GameTimeCause {
    return {
      gameNo: 1,
      kifuId: "fake",
      group: "3 分",
      timeLimitSec: 180,
      timeUpLoss: false,
      total: 50,
      phaseSpentSec: { early: 10, mid: 20, late: 10 },
      longThinkCountByPhase: { early: 0, mid: 1, late: 0 },
      longThinkTotal: 1,
      longestMove: { sec: 15, kifPly: 20 },
      longThinkStreakCount: 0,
      midThinkByPhase: { early: { count: 0, sec: 0 }, mid: { count: 0, sec: 0 }, late: { count: 0, sec: 0 } },
      midThinkTotal: { count: 0, sec: 0 },
      forkAmongLongThink: { numerator: 1, denominator: 2 },
      oppositeSideAmongForkLongThink: { numerator: 0, denominator: 1 },
      rookMark: { own: true, opponent: true },
      remainingSec: 100,
      midMoveSeconds: [],
      ...overrides,
    };
  }

  it("subgroupSummaryOf 相当(buildGroupTimeCause 経由): 時間負けと他の局を分け、中央値・分数を計算する", () => {
    const timeUp1 = fakeGame({ gameNo: 1, kifuId: "t1", timeUpLoss: true, phaseSpentSec: { early: 10, mid: 84, late: 20 } });
    const timeUp2 = fakeGame({ gameNo: 2, kifuId: "t2", timeUpLoss: true, phaseSpentSec: { early: 20, mid: 77, late: 10 } });
    const other1 = fakeGame({ gameNo: 3, kifuId: "o1", timeUpLoss: false, phaseSpentSec: { early: 30, mid: 14, late: 5 }, rookMark: { own: false, opponent: true } });

    const group = buildGroupTimeCause("3 分", 180, [timeUp1, timeUp2, other1]);

    expect(group.games).toBe(3);
    expect(group.timeUpLoss.games).toBe(2);
    expect(group.timeUpLoss.medianMidSec).toBe((84 + 77) / 2);
    expect(group.other.games).toBe(1);
    expect(group.other.medianMidSec).toBe(14);

    // C7・C8 の分数は局をまたいで合算(timeUp1・timeUp2 の forkAmongLongThink を足す。other1 は「時間負け」側の
    // 集計には入らない)
    expect(group.timeUpLoss.forkFraction).toEqual({ numerator: 2, denominator: 4 });
    expect(group.timeUpLoss.oppositeSideFraction).toEqual({ numerator: 0, denominator: 2 });

    // C9: own×opponent の 2×2(timeUp1・timeUp2 は own:true/opp:true、other1 は own:false/opp:true)
    const cellTT = group.rookMarkBreakdown.find((c) => c.own && c.opponent)!;
    expect(cellTT.games).toBe(2);
    const cellFT = group.rookMarkBreakdown.find((c) => !c.own && c.opponent)!;
    expect(cellFT.games).toBe(1);

    // C10: 局ごとの表(相関は出さない。並べるだけ)
    expect(group.c10Table).toEqual([
      { gameNo: 1, earlySec: 10, midSec: 84, remainingSec: 100 },
      { gameNo: 2, earlySec: 20, midSec: 77, remainingSec: 100 },
      { gameNo: 3, earlySec: 30, midSec: 14, remainingSec: 100 },
    ]);
  });

  it("forkAmongLongThink が全局 null(whatif-v2 の無い組)なら forkFraction は null", () => {
    const g = fakeGame({ forkAmongLongThink: null, oppositeSideAmongForkLongThink: null });
    const group = buildGroupTimeCause("10 分", 600, [g]);
    expect(group.other.forkFraction).toBeNull();
    expect(group.other.oppositeSideFraction).toBeNull();
  });

  it("buildTimeCauseFile: group(文字列)ごとに集計をまとめ、games には全局を通しで残す", () => {
    const a = fakeGame({ gameNo: 1, kifuId: "a", group: "3 分", timeLimitSec: 180 });
    const b = fakeGame({ gameNo: 1, kifuId: "b", group: "10 分", timeLimitSec: 600 });
    const file = buildTimeCauseFile([a, b]);
    expect(file.games).toEqual([a, b]);
    expect(file.groups.map((g) => g.group)).toEqual(["3 分", "10 分"]);
    expect(file.groups[0]!.games).toBe(1);
    expect(file.groups[1]!.games).toBe(1);
  });
});
