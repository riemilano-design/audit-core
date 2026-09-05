import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import { classifyPlanChangeReason } from "./planChangeReason.js";
import type { PlanSnapshot } from "./planChangeDetector.js";

/** 任意の駒配置からSFENを組み立てる(stateResponse.test.tsのcustomSfen()と同じ方式)。 */
function customSfen(pieces: Array<{ square: string; color: "sente" | "gote"; role: Parameters<Board["set"]>[1]["role"] }>): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("classifyPlanChangeReason", () => {
  it("残存候補の移動元にあった自駒が相手の着手後に無くなっている場合はcandidate_piece_captured", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    // 6g7hはユーザーが指した(除外対象)。残る8g7hの移動元(8g)には、
    // 相手の着手で自分の銀が取られたため何も無い局面を想定する。
    const afterSfen = customSfen([{ square: "8h", color: "sente", role: "king" }]);
    expect(classifyPlanChangeReason(previous, "6g7h", afterSfen)).toBe("candidate_piece_captured");
  });

  it("残存候補の移動元に別の駒(相手の駒)が入れ替わっている場合もcandidate_piece_captured", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["8g7h"] };
    const afterSfen = customSfen([
      { square: "8h", color: "sente", role: "king" },
      { square: "8g", color: "gote", role: "silver" }, // 捕獲した相手の駒がそのまま居座っている想定
    ]);
    expect(classifyPlanChangeReason(previous, "1g1f", afterSfen)).toBe("candidate_piece_captured");
  });

  it("駒が取られていない(移動元に自駒がそのまま残っている)場合はunknown", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    // 7i8hが非合法になった原因(王手放置等)が何であれ、移動元(7i)に自駒(玉)が
    // そのまま残っている場合は、捕獲以外の理由(=既存コードでは断定できない)。
    const afterSfen = customSfen([{ square: "7i", color: "sente", role: "king" }]);
    expect(classifyPlanChangeReason(previous, "1g1f", afterSfen)).toBe("unknown");
  });

  it("複数候補が同一targetSquareを狙うケース(Unit1の既知課題)でもcandidate_piece_capturedと誤断定しない", () => {
    // Unit1のdetectPlanChangeは、ユーザーが複数候補のうち1つ(6g7h)を指しただけで
    // 相手の着手と無関係にplanChanged=trueになり得る(既知課題、今回は修正しない)。
    // この場合、残存候補(8g7h)の移動元(8g)には自分の銀がそのまま残っている
    // (自分は動いていないため)。誤ってcandidate_piece_capturedと断定しないことを確認する。
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g7h"] };
    const afterSfen = customSfen([
      { square: "8h", color: "sente", role: "king" },
      { square: "7h", color: "sente", role: "silver" }, // 6g7hを指した結果、自分の銀で埋まった
      { square: "8g", color: "sente", role: "silver" }, // 8gの銀はまだ動いていない
    ]);
    expect(classifyPlanChangeReason(previous, "6g7h", afterSfen)).toBe("unknown");
  });

  it("除外後の残存候補にドロップ(移動元が無い手)しかない場合はunknown", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["P*5e"] };
    const afterSfen = customSfen([{ square: "8h", color: "sente", role: "king" }]);
    expect(classifyPlanChangeReason(previous, "1g1f", afterSfen)).toBe("unknown");
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["8g7h"] };
    const afterSfen = customSfen([{ square: "8h", color: "sente", role: "king" }]);
    const first = classifyPlanChangeReason(previous, "1g1f", afterSfen);
    const second = classifyPlanChangeReason(previous, "1g1f", afterSfen);
    expect(second).toBe(first);
  });
});
