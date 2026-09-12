// STEP U6-S。BOARD_SQUARES(盤の81マス)のテスト。
//
// 【何を見張っているか】
// この集合は「盤の外を除外する」ためだけに存在する。**1マス多くても少なくても、
// 経路探索(routePlanner)と利きの升数(pvMaterials)の両方が静かに狂う。**
// そこで、**作り方とは違う道筋で**81マスを数え直して突き合わせる
// (同じ作り方で数え直しても、写し間違いしか見つからない)。

import { describe, expect, it } from "vitest";
import { SquareSet } from "shogiops/square-set";
import { attacks } from "shogiops/attacks";
import { makeSquareName, parseSquareName } from "shogiops/util";
import { BOARD_SQUARES } from "./boardSquares.js";

/** docs/DATA_MODEL.md の座標表記(筋1〜9・段a〜i)の81個の名前。 */
const ALL_NAMES: string[] = [...Array(9).keys()].flatMap((f) =>
  [...Array(9).keys()].map((r) => `${f + 1}${"abcdefghi"[r]!}`),
);

describe("BOARD_SQUARES", () => {
  it("81マスちょうど", () => {
    expect(BOARD_SQUARES.size()).toBe(81);
    expect(ALL_NAMES).toHaveLength(81);
  });

  it("盤の内部表現を総当たりしても、含まれるのは81個の名前と完全に一致する", () => {
    // 作り方(名前から parseSquareName する)とは逆向きに、
    // 内部表現の番号を総当たりして名前へ戻す道筋で突き合わせる。
    const inSet: string[] = [];
    for (const square of BOARD_SQUARES) inSet.push(makeSquareName(square));
    expect([...inSet].sort()).toEqual([...ALL_NAMES].sort());
  });

  it("この集合が存在する理由そのものを固定する: attacks() は盤の外を返し、交差すると消える", () => {
    // 9九の角。shogiops の attacks() は内部表現(1段=16マス幅)の都合で
    // 盤の外にあたるマスを含んだ利きを返す。**素の size() を信じると過大になる。**
    const square = parseSquareName("9i");
    expect(square).toBeDefined();
    const raw = attacks({ role: "bishop", color: "sente" }, square!, SquareSet.empty());

    expect(raw.size()).toBe(29); // 盤の外を含んだ数
    expect(raw.intersect(BOARD_SQUARES).size()).toBe(8); // 実際の利き

    // 落ちたマスが本当に盤の外であること(名前が 1〜9 / a〜i に収まらない)。
    const dropped = [...raw].filter((s) => !BOARD_SQUARES.has(s)).map(makeSquareName);
    expect(dropped.length).toBe(21);
    for (const name of dropped) expect(name).not.toMatch(/^[1-9][a-i]$/);
  });

  it("5i の1つ下(内部表現には在るが盤の上には無い升)を含まない", () => {
    const goban5i = parseSquareName("5i");
    expect(goban5i).toBeDefined();
    const below = goban5i! + 16; // 1段=16マス幅。段が1つ進むと番号が16変わる
    expect(BOARD_SQUARES.has(below)).toBe(false);
  });

  it("81個の名前はすべて含まれる", () => {
    for (const name of ALL_NAMES) {
      const square = parseSquareName(name);
      expect(square).toBeDefined();
      expect(BOARD_SQUARES.has(square!)).toBe(true);
    }
  });
});
