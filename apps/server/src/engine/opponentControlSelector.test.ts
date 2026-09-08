import { describe, expect, it } from "vitest";
import { generateOpponentControlSeed, selectVariant } from "./opponentControlSelector.js";

describe("selectVariant", () => {
  const variants = ["a", "b", "c", "d"];

  it("同じseedと同じ候補列であれば常に同じ結果になる(決定性)", () => {
    const results = Array.from({ length: 20 }, () => selectVariant(variants, 12345));
    expect(new Set(results).size).toBe(1);
    expect(results[0]).toBe(selectVariant(variants, 12345));
  });

  it("候補が0件ならundefinedを返す", () => {
    expect(selectVariant([], 1)).toBeUndefined();
    expect(selectVariant([], 999999)).toBeUndefined();
  });

  it("候補が1件なら常にその1件を返す", () => {
    expect(selectVariant(["only"], 1)).toBe("only");
    expect(selectVariant(["only"], 999999)).toBe("only");
  });

  it("異なるseedによって、複数の候補が選ばれうる(均等選択であることの簡易確認。厳密な分布検定はしない)", () => {
    const seen = new Set<string>();
    for (let seed = 0; seed < 200; seed++) {
      const picked = selectVariant(variants, seed);
      if (picked !== undefined) seen.add(picked);
    }
    expect(seen.size).toBeGreaterThan(1);
  });
});

describe("generateOpponentControlSeed", () => {
  it("注入したnow()の値からseedを生成する(テストから決定的に呼べる)", () => {
    expect(generateOpponentControlSeed(() => 42)).toBe(42);
  });

  it("nowを省略するとDate.now()ベースの値を返す(呼ぶたびに例外を投げず、数値を返す)", () => {
    const seed = generateOpponentControlSeed();
    expect(typeof seed).toBe("number");
    expect(Number.isInteger(seed)).toBe(true);
  });
});
