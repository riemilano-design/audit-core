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

  it("存在しないディレクトリに対する例外の文は、渡したパスを含み、固定のディレクトリ名を含まない", () => {
    const missingDir = `${DEFAULT_INTENTS_DIR}-does-not-exist`;
    try {
      loadIntents(missingDir);
      throw new Error("loadIntentsが例外を投げなかった");
    } catch (err) {
      const message = (err as Error).message;
      expect(message).toContain(missingDir);
      expect(message).not.toContain("data/intents/");
    }
  });

  it("getIntentsはキャッシュされ、同じ内容を返す", () => {
    expect(getIntents()).toEqual(getIntents());
  });
});
