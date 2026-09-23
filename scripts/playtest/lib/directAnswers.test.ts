// STEP ANSWER 追加作業 ANSWER-DIRECT(docs/STEP_ANSWER_PLAN_2026-09-23.md §9.2)。lib/directAnswers.ts の単体試験。
// **エンジンは起動しない**(合成の whatif-v2 3 行 + read 3 行だけを使う)。

import { describe, expect, it } from "vitest";
import { actualGapCpOf, buildDirectAnswersFile, directAnswersCountsOf, joinDirectAnswersGame, sortDirectAnswers, type DirectAnswer } from "./directAnswers.js";
import { READ_TAG_NAMES, type ReadMoveMarks } from "./read.js";

function tags(overrides: Partial<ReadMoveMarks> = {}): ReadMoveMarks {
  return {
    drop: false,
    capture: false,
    retreat: false,
    declinesPromotion: false,
    sacrifice: false,
    kingMove: false,
    givesCheck: false,
    ...overrides,
  };
}

describe("actualGapCpOf", () => {
  it("loss が null なら null", () => {
    expect(actualGapCpOf(null)).toBeNull();
  });
  it("isLowerBound が true(実戦の手が候補に無い)なら null(少なくともこれだけ、の下限値のため)", () => {
    expect(actualGapCpOf({ cpValue: 400, isLowerBound: true })).toBeNull();
  });
  it("isLowerBound が false かつ cpValue があればそのまま", () => {
    expect(actualGapCpOf({ cpValue: 250, isLowerBound: false })).toBe(250);
  });
  it("isLowerBound が false でも cpValue が null(詰みが絡む)なら null", () => {
    expect(actualGapCpOf({ cpValue: null, isLowerBound: false })).toBeNull();
  });
});

describe("joinDirectAnswersGame", () => {
  it("1 万ちょうどは含み、null と 1 万超は除く(選別)。read に無い行は forkCount に数えない。group を通す", () => {
    const whatifPositions = [
      {
        ply: 17,
        displayPly: 17,
        sfen: "sfenA",
        top1Move: "7g7f",
        pv: ["7g7f", "3c3d"],
        top1Side: "attack" as const,
        actualMove: "2g2f",
        actualSide: "defense" as const,
        topGapCp: 120,
        loss: { cpValue: 400, isLowerBound: false },
        fork: true,
      },
      {
        ply: 19,
        displayPly: 19,
        sfen: "sfenB",
        top1Move: "8h2b+",
        pv: ["8h2b+"],
        top1Side: "attack" as const,
        actualMove: "3c3d",
        actualSide: "none" as const,
        topGapCp: null,
        loss: null,
        fork: true,
      },
      {
        ply: 21,
        displayPly: 21,
        sfen: "sfenC",
        top1Move: "5i5h",
        pv: ["5i5h"],
        top1Side: "defense" as const,
        actualMove: "5a5b",
        actualSide: "defense" as const,
        topGapCp: 300,
        loss: { cpValue: 300, isLowerBound: false },
        fork: true,
      },
      // read に無い行(read.ts 側で除外された、計画に無い理論上の状態)。forkCount に数えない。
      {
        ply: 23,
        displayPly: 23,
        sfen: "sfenD",
        top1Move: "1g1f",
        pv: ["1g1f"],
        top1Side: "none" as const,
        actualMove: "1c1d",
        actualSide: "none" as const,
        topGapCp: 50,
        loss: { cpValue: 50, isLowerBound: false },
        fork: true,
      },
      // scenes.fork が false の行(選別の対象外)。
      {
        ply: 25,
        displayPly: 25,
        sfen: "sfenE",
        top1Move: "6g6f",
        pv: ["6g6f"],
        top1Side: "none" as const,
        actualMove: "6g6f",
        actualSide: "none" as const,
        topGapCp: 10,
        loss: { cpValue: 10, isLowerBound: false },
        fork: false,
      },
    ];
    const readPositions = [
      { ply: 17, firstVisibleNodes: 10_000, top1Tags: tags({ capture: true }), actualTags: tags({ retreat: true }) },
      { ply: 19, firstVisibleNodes: null, top1Tags: tags(), actualTags: tags() },
      { ply: 21, firstVisibleNodes: 10_001, top1Tags: tags(), actualTags: tags() },
    ];

    const result = joinDirectAnswersGame("g1", 1, "3 分", whatifPositions, readPositions);

    expect(result.answers).toHaveLength(1);
    expect(result.answers[0]!.group).toBe("3 分");
    expect(result.answers[0]!.displayPly).toBe(17);
    expect(result.answers[0]!.firstVisibleNodes).toBe(10_000);
    expect(result.answers[0]!.top1Tags.capture).toBe(true);
    expect(result.answers[0]!.actualTags.retreat).toBe(true);
    expect(result.answers[0]!.top1Side).toBe("attack");
    expect(result.answers[0]!.actualSide).toBe("defense");
    expect(result.answers[0]!.topGapCp).toBe(120);
    expect(result.answers[0]!.actualGapCp).toBe(400);
    // read と結合できた 3 件(ply 17・19・21)だけを数える。read に無い ply 23 は数えない。fork:false の ply 25 も数えない。
    expect(result.forkCount).toBe(3);
  });
});

describe("sortDirectAnswers", () => {
  const base: Omit<DirectAnswer, "displayPly" | "actualGapCp"> = {
    group: "3 分",
    kifuId: "g1",
    gameNo: 1,
    sfen: "s",
    actualMove: "2g2f",
    top1Move: "7g7f",
    pv: ["7g7f"],
    top1Tags: tags(),
    top1Side: "none",
    actualTags: tags(),
    actualSide: "none",
    topGapCp: 999, // 表には出さない値。並び順に使われないことも確かめる
    firstVisibleNodes: 2_000,
  };

  it("actualGapCp の大きい順。null は最後(topGapCp は並び順に使わない)", () => {
    const answers: DirectAnswer[] = [
      { ...base, displayPly: 1, actualGapCp: 100 },
      { ...base, displayPly: 2, actualGapCp: null },
      { ...base, displayPly: 3, actualGapCp: 300 },
      { ...base, displayPly: 4, actualGapCp: 200, topGapCp: 1 }, // topGapCp が小さくても actualGapCp で並ぶ
    ];
    const sorted = sortDirectAnswers(answers);
    expect(sorted.map((a) => a.displayPly)).toEqual([3, 4, 1, 2]);
  });
});

describe("directAnswersCountsOf・buildDirectAnswersFile", () => {
  it("印の数(tags・side ごと)と局数・総数・分かれ道の総数を、局をまたいで合算する(組が違っても合算する)", () => {
    const g1Whatif = [
      {
        ply: 17,
        displayPly: 17,
        sfen: "sA",
        top1Move: "7g7f",
        pv: ["7g7f"],
        top1Side: "attack" as const,
        actualMove: "2g2f",
        actualSide: "defense" as const,
        topGapCp: 100,
        loss: { cpValue: 100, isLowerBound: false },
        fork: true,
      },
      {
        ply: 19,
        displayPly: 19,
        sfen: "sB",
        top1Move: "8h2b+",
        pv: ["8h2b+"],
        top1Side: "attack" as const,
        actualMove: "3c3d",
        actualSide: "none" as const,
        topGapCp: 200,
        loss: { cpValue: 200, isLowerBound: false },
        fork: true,
      },
    ];
    const g1Read = [
      { ply: 17, firstVisibleNodes: 2_000, top1Tags: tags({ capture: true }), actualTags: tags({ retreat: true }) },
      { ply: 19, firstVisibleNodes: 5_000, top1Tags: tags({ drop: true }), actualTags: tags({ sacrifice: true }) },
    ];
    const g2Whatif = [
      {
        ply: 33,
        displayPly: 33,
        sfen: "sC",
        top1Move: "5i5h",
        pv: ["5i5h"],
        top1Side: "defense" as const,
        actualMove: "5a5b",
        actualSide: "defense" as const,
        topGapCp: 50,
        loss: { cpValue: 50, isLowerBound: false },
        fork: true,
      },
    ];
    const g2Read = [{ ply: 33, firstVisibleNodes: 10_000, top1Tags: tags({ capture: true }), actualTags: tags({ capture: true }) }];

    const game1 = joinDirectAnswersGame("g1", 1, "3 分", g1Whatif, g1Read);
    const game2 = joinDirectAnswersGame("g2", 1, "10 分", g2Whatif, g2Read);
    const file = buildDirectAnswersFile([game1, game2]);

    expect(file.answers).toHaveLength(3);
    expect(new Set(file.answers.map((a) => a.group))).toEqual(new Set(["3 分", "10 分"]));
    expect(file.counts.totalCount).toBe(3);
    expect(file.counts.gamesCount).toBe(2);
    expect(file.counts.totalForkCount).toBe(3); // 2 局分の forkCount(2 + 1)
    expect(file.counts.top1SideCounts).toEqual({ attack: 2, defense: 1, both: 0, none: 0 });
    expect(file.counts.top1TagCounts.capture).toBe(2); // g1 の 1 件 + g2 の 1 件
    expect(file.counts.top1TagCounts.drop).toBe(1);
    expect(file.counts.actualTagCounts.retreat).toBe(1);
    expect(file.counts.actualTagCounts.sacrifice).toBe(1);
    expect(file.counts.actualTagCounts.capture).toBe(1);
    // READ_TAG_NAMES のすべてが欄に出る(0 件でも欄はある)
    for (const tag of READ_TAG_NAMES) {
      expect(file.counts.top1TagCounts[tag]).toBeGreaterThanOrEqual(0);
      expect(file.counts.actualTagCounts[tag]).toBeGreaterThanOrEqual(0);
    }
  });

  it("局をまたいだ answers が 0 件でも例外にならない(gamesCount・totalForkCount は 0)", () => {
    const file = buildDirectAnswersFile([]);
    expect(file.answers).toHaveLength(0);
    expect(file.counts.gamesCount).toBe(0);
    expect(file.counts.totalForkCount).toBe(0);
  });
});
