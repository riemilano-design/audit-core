import { describe, expect, it } from "vitest";
import { Prng } from "./prng.js";

describe("Prng", () => {
  it("同じ種からは同じ列を返す(決定性)", () => {
    const a = new Prng(1);
    const b = new Prng(1);
    const seqA = [a.next(), a.next(), a.next(), a.next()];
    const seqB = [b.next(), b.next(), b.next(), b.next()];
    expect(seqA).toEqual(seqB);
  });

  it("異なる種からは異なる列を返す", () => {
    const a = new Prng(1);
    const b = new Prng(2);
    expect(a.next()).not.toBe(b.next());
  });

  it("next()は常に[0,1)の範囲を返す", () => {
    const p = new Prng(42);
    for (let i = 0; i < 200; i++) {
      const v = p.next();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("nextInt(max)は[0,max)の整数を返し、同じ種からは同じ列を返す", () => {
    const a = new Prng(7);
    const b = new Prng(7);
    const seqA = Array.from({ length: 30 }, () => a.nextInt(10));
    const seqB = Array.from({ length: 30 }, () => b.nextInt(10));
    expect(seqA).toEqual(seqB);
    for (const v of seqA) {
      expect(Number.isInteger(v)).toBe(true);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(10);
    }
  });

  it("種0でも(内部で振り替えて)無限に0を返し続けたりしない", () => {
    const p = new Prng(0);
    const values = new Set([p.next(), p.next(), p.next()]);
    expect(values.size).toBeGreaterThan(1);
  });
});
