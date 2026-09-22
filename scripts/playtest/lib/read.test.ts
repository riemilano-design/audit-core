// STEP READ(docs/STEP_READ_PLAN_2026-09-22.md)。lib/read.ts の単体試験。
// **エンジンは起動しない**(2.1 の各段の評価は `ReadLadderLevelInput` の読みを差し替えて渡す)。
//
// 【正解の置き方】盤の図・区域の決め方から手で導く(実装の出力から写さない)。
// 合法性は `isLegalMove`(apps/server、既存・確定済み)で先に確かめてある(退く・成らず・捨て駒・
// 損得の各 1 つ以上を、盤の図から手計算した期待値とともに確かめる ― 計画 §3)。

import { describe, expect, it } from "vitest";
import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isInCheck } from "../../../apps/server/src/rules/gameStatus.js";
import { evalValueOf } from "./whatif.js";
import {
  READ_TAG_NAMES,
  READ_VALUES,
  firstVisibleNodesBucketsOf,
  firstVisibleNodesOf,
  ladderLevelOf,
  materialLookOf,
  materialLookSummaryOf,
  moveMarksOf,
  opponentReplyMatchesPvCountOf,
  opponentReplyMatchesPvOf,
  readForkPositionOf,
  readGameSummaryOf,
  tagCrossTableOf,
  type ReadForkPosition,
  type ReadLadderLevel,
  type ReadLadderLevelInput,
  type ReadMoveMarks,
} from "./read.js";

// ---- READ_VALUES(判断的知識の仮置き。値そのものを直接確かめる) ----

describe("READ_VALUES", () => {
  it("計画の仮置きの値(2026-09-22)", () => {
    expect(READ_VALUES.nodeLadder).toEqual([2_000, 10_000, 50_000, 200_000, 1_000_000]);
    expect(READ_VALUES.minLossCp).toBe(600);
    expect(READ_VALUES.pieceValues).toStrictEqual({
      pawn: 1,
      lance: 3,
      knight: 4,
      silver: 5,
      gold: 6,
      bishop: 8,
      rook: 10,
      tokin: 2,
      promotedlance: 4,
      promotedknight: 5,
      promotedsilver: 6,
      horse: 9,
      dragon: 11,
      king: 0,
    });
  });
});

// ---- 2.2 手の性質(moveMarksOf)。盤の図から手で導いた正解 ----
//
// 【局面】4k4/9/9/9/9/9/4G4/9/4K4 b - 1(gote 王 5a・sente 金 5g・sente 王 5i。whatif.test.ts の
// 「defense(ownKingZone)」と同じ局面。金は成れない駒なので declinesPromotion は常に false)。

const GOLD_SFEN = "4k4/9/9/9/9/9/4G4/9/4K4 b - 1";

describe("moveMarksOf: none(印が立たない基準)", () => {
  it("金が 5g から 5f へ進む(取らない・引かない・王手にならない・利きの外)", () => {
    expect(isInCheck(applyMove(GOLD_SFEN, "5g5f"), "gote")).toBe(false);
    expect(moveMarksOf(GOLD_SFEN, "5g5f")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: false,
      retreat: false,
      declinesPromotion: false,
      sacrifice: false,
      kingMove: false,
      givesCheck: false,
    });
  });
});

describe("moveMarksOf: retreat(自陣の側 = 段が大きくなる方向)", () => {
  it("金が 5g(6 段目)から 5h(7 段目)へ下がる: retreat=true", () => {
    expect(moveMarksOf(GOLD_SFEN, "5g5h").retreat).toBe(true);
  });

  it("金が 5g から 5f(5 段目)へ進む: retreat=false(段が小さくなる)", () => {
    expect(moveMarksOf(GOLD_SFEN, "5g5f").retreat).toBe(false);
  });

  it("打つ手は retreat=false(段の変化を考えない)", () => {
    const sfen = "4k4/9/9/9/9/9/9/9/4K4 b G 1";
    expect(moveMarksOf(sfen, "G*4h").retreat).toBe(false);
    expect(moveMarksOf(sfen, "G*4h").drop).toBe(true);
  });
});

describe("moveMarksOf: declinesPromotion(成れるのに成らない)", () => {
  // 角 2h が銀(1b、成っていない)を取って 8b へ。8b は敵陣(1〜3 段目)なので成りは任意(角は強制成りの駒でない)。
  // 8b は後手玉(7a)から 1 マス(隣)にあるので、成り・不成りどちらでも玉に取り返される
  // (moveFactsOf.test.ts の F-5 と同じ局面。capturedRole=silver は既存試験で確認済み)。
  const BISHOP_SFEN = "2k6/1s7/9/9/9/9/9/7B1/4K4 b - 1";

  it("2h8b(成らない): declinesPromotion=true・capture=true・sacrifice=true(玉に取り返される、角 8 > 銀 5)", () => {
    expect(isInCheck(applyMove(BISHOP_SFEN, "2h8b"), "gote")).toBe(true); // 前提: 角が玉に王手をかける
    expect(moveMarksOf(BISHOP_SFEN, "2h8b")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: true,
      retreat: false,
      declinesPromotion: true,
      sacrifice: true,
      kingMove: false,
      givesCheck: true,
    });
    expect(materialLookOf(BISHOP_SFEN, "2h8b")).toBe(5 - 8); // 取った銀(5) − 動かした角(8、利きにあるので引く)
  });

  it("2h8b+(成る): declinesPromotion=false・movedValue は馬(9)になり、材料の損得はさらに悪化", () => {
    expect(moveMarksOf(BISHOP_SFEN, "2h8b+")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: true,
      retreat: false,
      declinesPromotion: false,
      sacrifice: true,
      kingMove: false,
      givesCheck: true,
    });
    expect(materialLookOf(BISHOP_SFEN, "2h8b+")).toBe(5 - 9); // 取った銀(5) − 成った馬(9)
  });

  it("金は成れない駒なので、敵陣へ入っても declinesPromotion=false のまま", () => {
    expect(moveMarksOf(GOLD_SFEN, "5g5f").declinesPromotion).toBe(false);
  });
});

describe("moveMarksOf・materialLookOf: sacrifice(捨て駒)と見た目の損得", () => {
  it("銀が、後手の歩の利きの中(空升)へ進む: sacrifice=true・materialLook=0-5=-5(取っていないのに動かした駒の価値だけ引かれる)", () => {
    // 後手歩 5d は、前方(後手にとっての前 = 段が大きくなる方向)の 5e に利く。銀は 5f → 5e(取らない)。
    const sfen = "4k4/9/9/4p4/9/4S4/9/9/4K4 b - 1";
    expect(moveMarksOf(sfen, "5f5e")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: false,
      retreat: false, // f(6段目) → e(5段目)は進む方向
      declinesPromotion: false, // 5e は敵陣(1〜3段目)の外なので、そもそも成れない
      sacrifice: true,
      kingMove: false,
      givesCheck: false,
    });
    expect(materialLookOf(sfen, "5f5e")).toBe(0 - 5);
  });

  it("同じ銀の手でも、利きに当たらなければ sacrifice=false(取り返されない捨て駒とは呼ばない)", () => {
    // 後手の歩を 1 マス遠ざけ、5e に利かないようにする(5c から見て 5e には利かない)。
    const sfen = "4k4/9/4p4/9/9/4S4/9/9/4K4 b - 1";
    expect(moveMarksOf(sfen, "5f5e").sacrifice).toBe(false);
    expect(materialLookOf(sfen, "5f5e")).toBe(0);
  });

  it("銀が後手の歩をただで取る(取り返されない): capture=true・sacrifice=false・materialLook=1(駒得に見える)", () => {
    const sfen = "4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1";
    expect(moveMarksOf(sfen, "5f5e")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: true,
      retreat: false,
      declinesPromotion: false,
      sacrifice: false,
      kingMove: false,
      givesCheck: false,
    });
    expect(materialLookOf(sfen, "5f5e")).toBe(1);
  });
});

describe("moveMarksOf: kingMove・givesCheck", () => {
  it("玉を動かす手は kingMove=true", () => {
    const sfen = "4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1";
    expect(moveMarksOf(sfen, "5i5h")).toEqual<ReadMoveMarks>({
      drop: false,
      capture: false,
      retreat: false, // i(9段目) → h(8段目)は進む方向
      declinesPromotion: false,
      sacrifice: false,
      kingMove: true,
      givesCheck: false,
    });
  });

  it("飛が遠くから王手をかける: givesCheck=true", () => {
    const sfen = "4k4/9/9/9/8R/9/9/9/4K4 b - 1"; // whatif.test.ts の givesCheck の局面と同じ
    expect(moveMarksOf(sfen, "1e5e").givesCheck).toBe(true);
  });
});

// ---- 2.1 浅い探索でも分かる崩れか(エンジンを起動せず、生の読みを差し替える) ----

describe("ladderLevelOf・firstVisibleNodesOf", () => {
  it("差が cp 同士なら evalValueOf の単純な引き算(既存の evalValueOf を再利用)", () => {
    const level = ladderLevelOf({ nodes: 10_000, top: { scoreCp: 200, mate: null }, actual: { scoreCp: -500, mate: null, pv: ["7g7f"] } });
    expect(level).toEqual<ReadLadderLevel>({
      nodes: 10_000,
      topScoreCp: 200,
      topMate: null,
      actualScoreCp: -500,
      actualMate: null,
      diffValue: 200 - -500,
    });
    expect(level.diffValue).toBe(700);
  });

  it("片方でも測れなかった(null)なら diffValue は null", () => {
    expect(ladderLevelOf({ nodes: 2_000, top: null, actual: { scoreCp: 0, mate: null, pv: ["7g7f"] } }).diffValue).toBeNull();
    expect(ladderLevelOf({ nodes: 2_000, top: { scoreCp: 0, mate: null }, actual: null }).diffValue).toBeNull();
  });

  it("詰みが絡む差も evalValueOf 経由でそのまま通す(数直線に乗った値の差)", () => {
    const level = ladderLevelOf({ nodes: 1_000_000, top: { scoreCp: null, mate: 3 }, actual: { scoreCp: 100, mate: null, pv: ["7g7f"] } });
    const topValue = evalValueOf({ scoreCp: null, mate: 3 });
    expect(topValue).not.toBeNull();
    expect(level.diffValue).toBe(topValue! - 100);
    expect(level.diffValue! >= READ_VALUES.minLossCp).toBe(true);
  });

  it("最小の段を選ぶ(昇順の levels のうち、最初に閾値以上になった段)", () => {
    const levels: ReadLadderLevel[] = [
      { nodes: 2_000, topScoreCp: 50, topMate: null, actualScoreCp: 40, actualMate: null, diffValue: 10 },
      { nodes: 10_000, topScoreCp: 200, topMate: null, actualScoreCp: -500, actualMate: null, diffValue: 700 },
      { nodes: 50_000, topScoreCp: 210, topMate: null, actualScoreCp: -510, actualMate: null, diffValue: 720 },
    ];
    expect(firstVisibleNodesOf(levels, 600)).toBe(10_000);
  });

  it("差がちょうど閾値(600)なら、その段を選ぶ(600 以上。600 未満ではない)", () => {
    const levels: ReadLadderLevel[] = [{ nodes: 2_000, topScoreCp: 600, topMate: null, actualScoreCp: 0, actualMate: null, diffValue: 600 }];
    expect(firstVisibleNodesOf(levels, 600)).toBe(2_000);
  });

  it("どの段でも閾値に届かなければ null", () => {
    const levels: ReadLadderLevel[] = [
      { nodes: 2_000, topScoreCp: 50, topMate: null, actualScoreCp: 40, actualMate: null, diffValue: 10 },
      { nodes: 10_000, topScoreCp: 60, topMate: null, actualScoreCp: 50, actualMate: null, diffValue: 10 },
    ];
    expect(firstVisibleNodesOf(levels, 600)).toBeNull();
  });

  it("測れなかった段(diffValue null)は飛ばして、次の段で判定できる", () => {
    const levels: ReadLadderLevel[] = [
      { nodes: 2_000, topScoreCp: null, topMate: null, actualScoreCp: null, actualMate: null, diffValue: null },
      { nodes: 10_000, topScoreCp: 200, topMate: null, actualScoreCp: -500, actualMate: null, diffValue: 700 },
    ];
    expect(firstVisibleNodesOf(levels, 600)).toBe(10_000);
  });
});

describe("opponentReplyMatchesPvOf", () => {
  it("読み筋の 2 手目と、次に相手が実際に指した手が同じなら true", () => {
    expect(opponentReplyMatchesPvOf(["7g7f", "3c3d"], "3c3d")).toBe(true);
  });

  it("違えば false", () => {
    expect(opponentReplyMatchesPvOf(["7g7f", "3c3d"], "8c8d")).toBe(false);
  });

  it("読み筋が無い(測れなかった)・次の手が無い(対局の最後の手)・読み筋が 1 手しかない、はどれも null", () => {
    expect(opponentReplyMatchesPvOf(null, "3c3d")).toBeNull();
    expect(opponentReplyMatchesPvOf(["7g7f", "3c3d"], null)).toBeNull();
    expect(opponentReplyMatchesPvOf(["7g7f"], "3c3d")).toBeNull();
  });
});

// ---- 1 局面ぶんの組み立て(readForkPositionOf) ----

describe("readForkPositionOf", () => {
  // 局面: 4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1(後手歩 5e・先手銀 5f・先手玉 5i・後手玉 5a)。
  // 第 1 候補 = 5f5e(銀が歩をただで取る)、実戦の手 = 5i5h(玉が引く)。
  const SFEN = "4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1";
  const TOP1_MOVE = "5f5e";
  const ACTUAL_MOVE = "5i5h";

  function ladderLevels(): ReadLadderLevelInput[] {
    return [
      { nodes: 2_000, top: { scoreCp: 50, mate: null }, actual: { scoreCp: 40, mate: null, pv: [ACTUAL_MOVE] } },
      { nodes: 10_000, top: { scoreCp: 200, mate: null }, actual: { scoreCp: -500, mate: null, pv: [ACTUAL_MOVE, "1a1b"] } },
      { nodes: 50_000, top: { scoreCp: 210, mate: null }, actual: { scoreCp: -510, mate: null, pv: [ACTUAL_MOVE] } },
      { nodes: 200_000, top: { scoreCp: 220, mate: null }, actual: { scoreCp: -520, mate: null, pv: [ACTUAL_MOVE] } },
      { nodes: 1_000_000, top: { scoreCp: 230, mate: null }, actual: { scoreCp: -530, mate: null, pv: [ACTUAL_MOVE, "2b3c"] } },
    ];
  }

  it("印・見た目の損得は moveMarksOf・materialLookOf と同じ値になる(二重に実装しない)", () => {
    const position = readForkPositionOf({
      ply: 21,
      displayPly: 21,
      sfen: SFEN,
      actualMove: ACTUAL_MOVE,
      top1Move: TOP1_MOVE,
      nextActualMove: "2b3c",
      ladderLevels: ladderLevels(),
    });
    expect(position.top1Tags).toEqual(moveMarksOf(SFEN, TOP1_MOVE));
    expect(position.actualTags).toEqual(moveMarksOf(SFEN, ACTUAL_MOVE));
    expect(position.top1MaterialLook).toBe(materialLookOf(SFEN, TOP1_MOVE));
    expect(position.actualMaterialLook).toBe(materialLookOf(SFEN, ACTUAL_MOVE));
    expect(position.ply).toBe(21);
    expect(position.displayPly).toBe(21);
    expect(position.sfen).toBe(SFEN);
    expect(position.actualMove).toBe(ACTUAL_MOVE);
    expect(position.top1Move).toBe(TOP1_MOVE);
  });

  it("firstVisibleNodes は 10000 段目(差 700 が最初に 600 以上になる段)", () => {
    const position = readForkPositionOf({
      ply: 21,
      displayPly: 21,
      sfen: SFEN,
      actualMove: ACTUAL_MOVE,
      top1Move: TOP1_MOVE,
      nextActualMove: "2b3c",
      ladderLevels: ladderLevels(),
    });
    expect(position.firstVisibleNodes).toBe(10_000);
    expect(position.ladder).toHaveLength(5);
  });

  it("opponentReplyMatchesPv は、いちばん深い段(1,000,000)の読み筋の 2 手目と比べる", () => {
    const matched = readForkPositionOf({
      ply: 21,
      displayPly: 21,
      sfen: SFEN,
      actualMove: ACTUAL_MOVE,
      top1Move: TOP1_MOVE,
      nextActualMove: "2b3c",
      ladderLevels: ladderLevels(),
    });
    expect(matched.opponentReplyMatchesPv).toBe(true);

    const mismatched = readForkPositionOf({
      ply: 21,
      displayPly: 21,
      sfen: SFEN,
      actualMove: ACTUAL_MOVE,
      top1Move: TOP1_MOVE,
      nextActualMove: "9i9h",
      ladderLevels: ladderLevels(),
    });
    expect(mismatched.opponentReplyMatchesPv).toBe(false);

    const gameEnded = readForkPositionOf({
      ply: 21,
      displayPly: 21,
      sfen: SFEN,
      actualMove: ACTUAL_MOVE,
      top1Move: TOP1_MOVE,
      nextActualMove: null,
      ladderLevels: ladderLevels(),
    });
    expect(gameEnded.opponentReplyMatchesPv).toBeNull();
  });
});

// ---- 1 局ぶんのまとめ ----

describe("firstVisibleNodesBucketsOf", () => {
  it("nodeLadder の各段 + none の件数(0 件の段も 0 として出す)", () => {
    const buckets = firstVisibleNodesBucketsOf([{ firstVisibleNodes: 10_000 }, { firstVisibleNodes: 10_000 }, { firstVisibleNodes: null }, { firstVisibleNodes: 1_000_000 }]);
    expect(buckets).toStrictEqual({
      "2000": 0,
      "10000": 2,
      "50000": 0,
      "200000": 0,
      "1000000": 1,
      none: 1,
    });
  });
});

describe("opponentReplyMatchesPvCountOf", () => {
  it("null は measured に数えない", () => {
    expect(opponentReplyMatchesPvCountOf([{ opponentReplyMatchesPv: true }, { opponentReplyMatchesPv: false }, { opponentReplyMatchesPv: null }, { opponentReplyMatchesPv: true }])).toStrictEqual({
      matched: 2,
      measured: 3,
    });
  });
});

const NO_MARKS: ReadMoveMarks = { drop: false, capture: false, retreat: false, declinesPromotion: false, sacrifice: false, kingMove: false, givesCheck: false };

describe("tagCrossTableOf", () => {
  it("複数の印に当たってよいので、1 局面が複数のセルへ数えられる", () => {
    const positions = [
      { top1Tags: { ...NO_MARKS, capture: true, retreat: true }, actualTags: { ...NO_MARKS, sacrifice: true, kingMove: true } },
      { top1Tags: { ...NO_MARKS, capture: true }, actualTags: { ...NO_MARKS, capture: true } },
    ];
    const table = tagCrossTableOf(positions);
    expect(table.capture.sacrifice).toBe(1);
    expect(table.capture.kingMove).toBe(1);
    expect(table.retreat.sacrifice).toBe(1);
    expect(table.retreat.kingMove).toBe(1);
    expect(table.capture.capture).toBe(1); // 2 局面目
    expect(table.retreat.capture).toBe(0);
    expect(table.declinesPromotion.givesCheck).toBe(0);
    // 全部のマスが揃っている(7 x 7)
    expect(Object.keys(table)).toEqual([...READ_TAG_NAMES]);
    for (const row of READ_TAG_NAMES) expect(Object.keys(table[row])).toEqual([...READ_TAG_NAMES]);
  });
});

describe("materialLookSummaryOf", () => {
  it("実戦が駒得に見える・第 1 候補が駒損に見える・両方、を数える", () => {
    const summary = materialLookSummaryOf([
      { actualMaterialLook: 1, top1MaterialLook: -1 }, // 両方
      { actualMaterialLook: 1, top1MaterialLook: 0 }, // 実戦だけ
      { actualMaterialLook: 0, top1MaterialLook: -2 }, // 第 1 候補だけ
      { actualMaterialLook: 0, top1MaterialLook: 0 }, // どちらでもない
    ]);
    expect(summary).toStrictEqual({ actualPositiveCount: 2, top1NegativeCount: 2, bothCount: 1 });
  });
});

describe("readGameSummaryOf", () => {
  it("局面が 0 件なら、すべての件数が 0(手・評価値・SFEN を含まない)", () => {
    const summary = readGameSummaryOf([]);
    expect(summary.forkPositionsRead).toBe(0);
    expect(summary.firstVisibleNodesBuckets).toStrictEqual({ "2000": 0, "10000": 0, "50000": 0, "200000": 0, "1000000": 0, none: 0 });
    expect(summary.opponentReplyMatchesPv).toStrictEqual({ matched: 0, measured: 0 });
    expect(summary.materialLook).toStrictEqual({ actualPositiveCount: 0, top1NegativeCount: 0, bothCount: 0 });
    expect(JSON.stringify(summary)).not.toMatch(/[0-9][a-i]|sfen/i); // 手・SFEN らしき文字列を含まない
  });

  it("実際の局面を積んだときの合算(readForkPositionOf の出力をそのまま渡す)", () => {
    const sfen = "4k4/9/9/9/4p4/4S4/9/9/4K4 b - 1";
    const levels: ReadLadderLevelInput[] = [
      { nodes: 2_000, top: { scoreCp: 50, mate: null }, actual: { scoreCp: 40, mate: null, pv: ["5i5h"] } },
      { nodes: 10_000, top: { scoreCp: 200, mate: null }, actual: { scoreCp: -500, mate: null, pv: ["5i5h", "1a1b"] } },
      { nodes: 50_000, top: { scoreCp: 210, mate: null }, actual: { scoreCp: -510, mate: null, pv: ["5i5h"] } },
      { nodes: 200_000, top: { scoreCp: 220, mate: null }, actual: { scoreCp: -520, mate: null, pv: ["5i5h"] } },
      { nodes: 1_000_000, top: { scoreCp: 230, mate: null }, actual: { scoreCp: -530, mate: null, pv: ["5i5h", "1a1b"] } },
    ];
    const position = readForkPositionOf({ ply: 21, displayPly: 21, sfen, actualMove: "5i5h", top1Move: "5f5e", nextActualMove: "1a1b", ladderLevels: levels });
    const summary = readGameSummaryOf([position]);
    expect(summary.forkPositionsRead).toBe(1);
    expect(summary.firstVisibleNodesBuckets["10000"]).toBe(1);
    expect(summary.opponentReplyMatchesPv).toStrictEqual({ matched: 1, measured: 1 });
    expect(summary.tagCrossTable.capture.kingMove).toBe(1); // 第 1 候補(5f5e、取る)× 実戦(5i5h、玉の手)
    expect(summary.materialLook.actualPositiveCount).toBe(0); // 実戦(5i5h)の materialLook は 0
    expect(summary.materialLook.top1NegativeCount).toBe(0); // 第 1 候補(5f5e、ただ取り)の materialLook は 1(正)
  });
});
