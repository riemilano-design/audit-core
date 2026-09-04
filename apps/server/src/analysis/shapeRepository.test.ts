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

  it("getShapesはキャッシュされ、同じ内容を返す", () => {
    expect(getShapes()).toEqual(getShapes());
  });
});
