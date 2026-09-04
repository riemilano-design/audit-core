import { describe, expect, it } from "vitest";
import { DEFAULT_INTENTS_DIR, getIntents, IntentRepositoryError, loadIntents } from "./intentRepository.js";

describe("intentRepository", () => {
  it("data/intents/ から既存の全intentを読み込む", () => {
    const intents = loadIntents();
    const ids = intents.map((i) => i.id);
    expect(ids).toContain("boh_gin");
    expect(ids).toContain("naname_bogin");
    expect(ids).toContain("hayajikake");
  });

  it("id昇順の決定的な順序で返す", () => {
    const first = loadIntents();
    const second = loadIntents();
    expect(second.map((i) => i.id)).toEqual(first.map((i) => i.id));
    expect(first.map((i) => i.id)).toEqual([...first.map((i) => i.id)].sort());
  });

  it("存在しないディレクトリに対してIntentRepositoryErrorを投げる", () => {
    expect(() => loadIntents(`${DEFAULT_INTENTS_DIR}-does-not-exist`)).toThrow(IntentRepositoryError);
  });

  it("getIntentsはキャッシュされ、同じ内容を返す", () => {
    expect(getIntents()).toEqual(getIntents());
  });
});
