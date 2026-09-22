// STEP TYPE(docs/STEP_TYPE_PLAN_2026-09-23.md)。lib/type.ts の単体試験。
// **エンジンは起動しない**(合成の入力だけを使う)。

import { describe, expect, it } from "vitest";
import {
  TYPE_VALUES,
  TypeStepError,
  medianSecondsBySideOf,
  natureBucketOf,
  repeatedGroupsOf,
  retreatGameCountOf,
  sideBucketOf,
  sizeBucketOf,
  spentSecOfDisplayPly,
  typeForkOf,
  typeGroupCountsOf,
  typeKeyOf,
  type TypeFork,
  type TypeGame,
  type TypeValues,
} from "./type.js";

// ---- TYPE_VALUES(判断的知識の仮置き。値そのものを確かめる) ----

describe("TYPE_VALUES", () => {
  it("計画の仮置きの値(2026-09-23)", () => {
    expect(TYPE_VALUES.nodeShallowMaxNodes).toBe(10_000);
    expect(TYPE_VALUES.nodeDeepMinNodes).toBe(50_000);
    expect(TYPE_VALUES.repeatMinGames).toBe(3);
  });
});

// ---- 軸 A: 大きさ ----

describe("sizeBucketOf", () => {
  it("null は none", () => {
    expect(sizeBucketOf(null)).toBe("none");
  });
  it("2000・10000 は shallow(計画の 2000〜10000)", () => {
    expect(sizeBucketOf(2_000)).toBe("shallow");
    expect(sizeBucketOf(10_000)).toBe("shallow");
  });
  it("50000・200000・1000000 は deep(計画の 50000 以上)", () => {
    expect(sizeBucketOf(50_000)).toBe("deep");
    expect(sizeBucketOf(200_000)).toBe("deep");
    expect(sizeBucketOf(1_000_000)).toBe("deep");
  });
  it("計画が定義していない区間(10000 と 50000 の間)は例外(保守的側。計画にない判断)", () => {
    expect(() => sizeBucketOf(20_000)).toThrow(TypeStepError);
  });
});

// ---- 軸 B: 側 ----

describe("sideBucketOf", () => {
  it("第 1 候補が攻め・実戦が守り", () => {
    expect(sideBucketOf("attack", "defense")).toBe("top1AttackActualDefense");
  });
  it("第 1 候補が守り・実戦が攻め", () => {
    expect(sideBucketOf("defense", "attack")).toBe("top1DefenseActualAttack");
  });
  it("同じ側(攻め・攻め)", () => {
    expect(sideBucketOf("attack", "attack")).toBe("same");
  });
  it("同じ側(守り・守り)", () => {
    expect(sideBucketOf("defense", "defense")).toBe("same");
  });
  it("どちらかが none", () => {
    expect(sideBucketOf("none", "attack")).toBe("eitherNone");
    expect(sideBucketOf("defense", "none")).toBe("eitherNone");
    expect(sideBucketOf("none", "none")).toBe("eitherNone");
  });
  it("「両方」は集合が交わるかで判定する(計画にない判断): 第 1 候補が both・実戦が攻めなら同じ側", () => {
    expect(sideBucketOf("both", "attack")).toBe("same");
    expect(sideBucketOf("both", "defense")).toBe("same");
    expect(sideBucketOf("attack", "both")).toBe("same");
    expect(sideBucketOf("defense", "both")).toBe("same");
    expect(sideBucketOf("both", "both")).toBe("same");
  });
});

// ---- 軸 C: 性質(優先順は retreat → 駒得の見た目 → drop → それ以外) ----

describe("natureBucketOf", () => {
  it("retreat が最優先(駒得・drop も true でも retreat)", () => {
    expect(natureBucketOf({ retreat: true, drop: true, sacrifice: false }, 5)).toBe("retreat");
  });
  it("retreat でなければ、駒得の見た目(materialLook > 0 かつ sacrifice でない)", () => {
    expect(natureBucketOf({ retreat: false, drop: true, sacrifice: false }, 3)).toBe("materialGain");
  });
  it("materialLook > 0 でも sacrifice なら駒得にしない(drop へ)", () => {
    expect(natureBucketOf({ retreat: false, drop: true, sacrifice: true }, 3)).toBe("drop");
  });
  it("materialLook <= 0 なら駒得にしない(drop へ)", () => {
    expect(natureBucketOf({ retreat: false, drop: true, sacrifice: false }, 0)).toBe("drop");
    expect(natureBucketOf({ retreat: false, drop: true, sacrifice: false }, -2)).toBe("drop");
  });
  it("どれにも当たらなければ other", () => {
    expect(natureBucketOf({ retreat: false, drop: false, sacrifice: false }, 0)).toBe("other");
    expect(natureBucketOf({ retreat: false, drop: false, sacrifice: true }, 5)).toBe("other");
  });
});

// ---- typeKeyOf / typeForkOf ----

describe("typeKeyOf・typeForkOf", () => {
  it("key は 3 軸を | でつなぐ", () => {
    expect(typeKeyOf({ size: "shallow", side: "same", nature: "drop" })).toBe("shallow|same|drop");
  });
  it("typeForkOf は 3 軸すべてを付け、手・SFEN・評価値を持たない", () => {
    const fork = typeForkOf({
      ply: 23,
      displayPly: 23,
      firstVisibleNodes: 2_000,
      top1Side: "attack",
      actualSide: "defense",
      actualTags: { retreat: false, drop: true, sacrifice: false },
      actualMaterialLook: 3,
      spentSec: 12,
    });
    expect(fork).toStrictEqual<TypeFork>({
      ply: 23,
      displayPly: 23,
      size: "shallow",
      side: "top1AttackActualDefense",
      nature: "materialGain",
      key: "shallow|top1AttackActualDefense|materialGain",
      spentSec: 12,
    });
    expect(Object.keys(fork)).not.toContain("sfen");
    expect(Object.keys(fork)).not.toContain("scoreCp");
    expect(Object.keys(fork)).not.toContain("move");
  });
});

// ---- spentSecOfDisplayPly(moveSeconds[displayPly - 1]。後手の局の添字合わせ) ----

describe("spentSecOfDisplayPly", () => {
  it("displayPly - 1 の添字を読む", () => {
    const moveSeconds = [{ spentSec: 1, totalSec: 1 }, { spentSec: 5, totalSec: 6 }, { spentSec: 9, totalSec: 15 }];
    expect(spentSecOfDisplayPly(moveSeconds, 1)).toBe(1);
    expect(spentSecOfDisplayPly(moveSeconds, 2)).toBe(5);
    expect(spentSecOfDisplayPly(moveSeconds, 3)).toBe(9);
  });
  it("後手の局(plyOffset = 1)を想定: 記録の ply=5 → displayPly=6 のとき、moveSeconds[5](= 6 手目)を読む", () => {
    // originalMoves(KIF の手数どおり)の消費時間。6 手目 = 添字 5。
    const moveSeconds = [
      { spentSec: 1, totalSec: 1 }, // 1 手目
      { spentSec: 2, totalSec: 3 }, // 2 手目
      { spentSec: 3, totalSec: 6 }, // 3 手目
      { spentSec: 4, totalSec: 10 }, // 4 手目
      { spentSec: 5, totalSec: 15 }, // 5 手目
      { spentSec: 42, totalSec: 57 }, // 6 手目(displayPly = 6)
    ];
    const ply = 5;
    const plyOffset = 1;
    const displayPly = ply + plyOffset;
    expect(displayPly).toBe(6);
    expect(spentSecOfDisplayPly(moveSeconds, displayPly)).toBe(42);
  });
  it("moveSeconds が無ければ null", () => {
    expect(spentSecOfDisplayPly(undefined, 3)).toBeNull();
    expect(spentSecOfDisplayPly(null, 3)).toBeNull();
  });
  it("その手数の要素が null、または配列の長さが足りなければ null", () => {
    expect(spentSecOfDisplayPly([{ spentSec: 1 }, null], 2)).toBeNull();
    expect(spentSecOfDisplayPly([{ spentSec: 1 }], 5)).toBeNull();
  });
});

// ---- typeGroupCountsOf / repeatedGroupsOf(3 局以上の判定) ----

function forkOf(overrides: Partial<TypeFork> & { key: string }): TypeFork {
  return { ply: 1, displayPly: 1, size: "shallow", side: "same", nature: "other", spentSec: null, ...overrides };
}

describe("typeGroupCountsOf・repeatedGroupsOf", () => {
  const keyA = "shallow|same|other";
  const keyB = "deep|top1AttackActualDefense|retreat";

  it("組ごとの局数(1 局 1 回)と回数(延べ)を数える", () => {
    const games: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: keyA }), forkOf({ key: keyA })] }, // keyA が 1 局に 2 回
      { id: "g2", forks: [forkOf({ key: keyA })] },
      { id: "g3", forks: [forkOf({ key: keyB })] },
    ];
    const counts = typeGroupCountsOf(games);
    const a = counts.find((c) => c.key === keyA)!;
    const b = counts.find((c) => c.key === keyB)!;
    expect(a.games).toBe(2);
    expect(a.occurrences).toBe(3);
    expect(b.games).toBe(1);
    expect(b.occurrences).toBe(1);
  });

  it("2 局では「3 局以上の組」に出ず、3 局で出る", () => {
    const twoGames: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: keyA })] },
      { id: "g2", forks: [forkOf({ key: keyA })] },
    ];
    expect(repeatedGroupsOf(typeGroupCountsOf(twoGames))).toHaveLength(0);

    const threeGames: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: keyA })] },
      { id: "g2", forks: [forkOf({ key: keyA })] },
      { id: "g3", forks: [forkOf({ key: keyA })] },
    ];
    const repeated = repeatedGroupsOf(typeGroupCountsOf(threeGames));
    expect(repeated).toHaveLength(1);
    expect(repeated[0]!.key).toBe(keyA);
    expect(repeated[0]!.games).toBe(3);
  });

  it("同じ局に同じ組が 2 回出ても、局数は 1 のまま(1 局 1 回で数える)", () => {
    const games: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: keyA }), forkOf({ key: keyA }), forkOf({ key: keyA })] },
      { id: "g2", forks: [forkOf({ key: keyA })] },
    ];
    const counts = typeGroupCountsOf(games);
    expect(counts.find((c) => c.key === keyA)!.games).toBe(2);
    expect(counts.find((c) => c.key === keyA)!.occurrences).toBe(4);
    expect(repeatedGroupsOf(counts)).toHaveLength(0); // 2 局なので繰り返しには入らない
  });

  it("repeatMinGames を渡せば境目を変えられる", () => {
    const games: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: keyA })] },
      { id: "g2", forks: [forkOf({ key: keyA })] },
    ];
    const counts = typeGroupCountsOf(games);
    const looserValues: TypeValues = { ...TYPE_VALUES, repeatMinGames: 2 };
    expect(repeatedGroupsOf(counts, looserValues)).toHaveLength(1);
  });
});

// ---- T4: 側ごとの秒の中央値 ----

describe("medianSecondsBySideOf", () => {
  it("側(軸 B)ごとに秒が読めた分かれ道の中央値を出す", () => {
    const games: TypeGame[] = [
      {
        id: "g1",
        forks: [
          forkOf({ key: "a", side: "top1AttackActualDefense", spentSec: 10 }),
          forkOf({ key: "a", side: "top1AttackActualDefense", spentSec: 30 }),
          forkOf({ key: "a", side: "same", spentSec: 2 }),
        ],
      },
      { id: "g2", forks: [forkOf({ key: "a", side: "top1AttackActualDefense", spentSec: 20 })] },
    ];
    const medians = medianSecondsBySideOf(games);
    const attack = medians.find((m) => m.side === "top1AttackActualDefense")!;
    expect(attack.n).toBe(3);
    expect(attack.medianSec).toBe(20); // [10, 20, 30] の中央
    const same = medians.find((m) => m.side === "same")!;
    expect(same.n).toBe(1);
    expect(same.medianSec).toBe(2);
    const defense = medians.find((m) => m.side === "top1DefenseActualAttack")!;
    expect(defense.n).toBe(0);
    expect(defense.medianSec).toBeNull();
  });
  it("秒が null の分かれ道は分母に入れない", () => {
    const games: TypeGame[] = [{ id: "g1", forks: [forkOf({ key: "a", side: "same", spentSec: null }), forkOf({ key: "a", side: "same", spentSec: 8 })] }];
    const same = medianSecondsBySideOf(games).find((m) => m.side === "same")!;
    expect(same.n).toBe(1);
    expect(same.medianSec).toBe(8);
  });
});

// ---- T5: 実戦が retreat の分かれ道が出る局数 ----

describe("retreatGameCountOf", () => {
  it("実戦が retreat の分かれ道が 1 つでもある局を数える(局あたり複数あっても 1 局)", () => {
    const games: TypeGame[] = [
      { id: "g1", forks: [forkOf({ key: "a", nature: "retreat" }), forkOf({ key: "a", nature: "retreat" })] },
      { id: "g2", forks: [forkOf({ key: "a", nature: "other" })] },
      { id: "g3", forks: [forkOf({ key: "a", nature: "drop" }), forkOf({ key: "a", nature: "retreat" })] },
    ];
    expect(retreatGameCountOf(games)).toBe(2);
  });
  it("分かれ道が無い局は数えない", () => {
    expect(retreatGameCountOf([{ id: "g1", forks: [] }])).toBe(0);
  });
});
