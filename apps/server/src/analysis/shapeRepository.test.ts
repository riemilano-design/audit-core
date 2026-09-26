import { describe, expect, it } from "vitest";
import { DEFAULT_SHAPES_DIR, getShapes, loadShapes, ShapeRepositoryError } from "./shapeRepository.js";

describe("shapeRepository", () => {
  it("data/shapes/ から既存の全shapeを読み込む", () => {
    const shapes = loadShapes();
    const ids = shapes.map((s) => s.id);
    expect(ids).toContain("mino_honmino");
    expect(ids).toContain("mino_takamino");
    expect(ids).toContain("mino_ginkanmuri");
  });

  it("id昇順の決定的な順序で返す", () => {
    const first = loadShapes();
    const second = loadShapes();
    expect(second.map((s) => s.id)).toEqual(first.map((s) => s.id));
    expect(first.map((s) => s.id)).toEqual([...first.map((s) => s.id)].sort());
  });

  it("存在しないディレクトリに対してShapeRepositoryErrorを投げる", () => {
    expect(() => loadShapes(`${DEFAULT_SHAPES_DIR}-does-not-exist`)).toThrow(ShapeRepositoryError);
  });

  it("存在しないディレクトリに対する例外の文は、渡したパスを含み、固定のディレクトリ名を含まない", () => {
    const missingDir = `${DEFAULT_SHAPES_DIR}-does-not-exist`;
    try {
      loadShapes(missingDir);
      throw new Error("loadShapesが例外を投げなかった");
    } catch (err) {
      const message = (err as Error).message;
      expect(message).toContain(missingDir);
      expect(message).not.toContain("data/shapes/");
    }
  });

  it("getShapesはキャッシュされ、同じ内容を返す", () => {
    expect(getShapes()).toEqual(getShapes());
  });
});
