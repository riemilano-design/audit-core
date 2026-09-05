import { describe, expect, it } from "vitest";
import { detectPlanChange, type PlanSnapshot } from "./planChangeDetector.js";

describe("detectPlanChange", () => {
  it("previous snapshotが無い場合はfalse", () => {
    expect(detectPlanChange(undefined, "7g7f", "mino_honmino", ["7g7f"])).toBe(false);
  });

  it("targetShapeIdが前回と異なる場合はfalse(目標形変更・フォールバック変化を崩れと混同しない)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_takamino", [])).toBe(false);
  });

  it("提案手をそのまま指した(候補が1件のみ)場合、除外後の残存候補が0件になりfalse", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    // プレイした手自体は現在局面にはもう存在しない(駒が既に動いた)ことが通常だが、
    // 除外によって比較対象自体が無くなるため、legalMovesの中身に関わらずfalseになる。
    expect(detectPlanChange(previous, "7i8h", "mino_honmino", [])).toBe(false);
  });

  it("複数候補のうち1つを指した場合、残りの候補を対象に判定する(残りが合法ならfalse)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    // 6g7hを指した後、残る8g7hが現在も合法手に含まれている。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["8g7h"])).toBe(false);
  });

  it("複数候補のうち1つを指した場合、残りの候補が現在すべて非合法ならtrue", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    // 6g7hを指した後、残る8g7hが現在の合法手に含まれていない(相手の手等で失われた)。
    expect(detectPlanChange(previous, "6g7h", "mino_honmino", ["1g1f"])).toBe(true);
  });

  it("ユーザーが提案手以外を指し、残存候補がすべて現在非合法な場合はtrue", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_honmino", ["1f1e"])).toBe(true);
  });

  it("ユーザーが提案手以外を指し、残存候補が現在も合法な場合はfalse", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(detectPlanChange(previous, "1g1f", "mino_honmino", ["7i8h", "1f1e"])).toBe(false);
  });
});
