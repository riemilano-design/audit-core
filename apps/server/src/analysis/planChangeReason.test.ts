import { Board } from "shogiops/board";
import { Hand, Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import { classifyPlanChangeReason } from "./planChangeReason.js";
import type { PlanSnapshot } from "./planChangeDetector.js";
import { applyMove } from "../rules/applyMove.js";

/** 任意の駒配置(+持ち駒)からSFENを組み立てる(stateResponse.test.tsのcustomSfen()と同じ方式)。 */
function customSfen(
  pieces: Array<{ square: string; color: "sente" | "gote"; role: Parameters<Board["set"]>[1]["role"] }>,
  hands: Hands = Hands.empty(),
): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands, turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("classifyPlanChangeReason", () => {
  it("残存候補の移動元にあった自駒が相手の着手後に無くなっている場合はcandidate_piece_captured", () => {
    // 8g8hは6g7hと異なる移動先マス(8h)を持つため兄弟候補として除外されない。
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h", "8g8h"] };
    // 6g7hはユーザーが指した(除外対象)。残る8g8hの移動元(8g)には、
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

  // 【今回追加(候補C: 王手放置)】実際のSFEN・applyMoveを使い、相手の飛車によって
  // 候補手(玉の移動)が非合法になるケースを再現する(Unit1の実機再現フィクスチャと同型)。
  it("相手の飛車によって候補手(玉の移動)が相手の利きに入り非合法になった場合はcandidate_move_illegal_due_to_check", () => {
    const sfenBefore = customSfen(
      [
        { square: "7i", color: "sente", role: "king" },
        { square: "7h", color: "sente", role: "silver" },
        { square: "6i", color: "sente", role: "gold" },
        { square: "5h", color: "sente", role: "gold" },
        { square: "1g", color: "sente", role: "pawn" },
      ],
      Hands.from(Hand.empty(), Hand.from([["rook", 1]])),
    );
    const sfenAfterUser = applyMove(sfenBefore, "1g1f"); // 候補手(7i8h)とは無関係な手
    const sfenAfterOpponent = applyMove(sfenAfterUser, "R*8a"); // 相手が飛車を8筋へ打つ

    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["7i8h"] };
    expect(classifyPlanChangeReason(previous, "1g1f", sfenAfterOpponent)).toBe("candidate_move_illegal_due_to_check");
  });

  // 【今回追加(候補D: ピン)】実際のSFEN・applyMoveを使い、相手の飛車によって
  // 候補駒(銀)がピンされ、候補手が非合法になるケースを再現する。
  it("相手の飛車によって候補駒(銀)がピンされ候補手が非合法になった場合はcandidate_piece_pinned", () => {
    // 玉6i・銀6g(同じ6筋)を用意し、相手が飛車を6筋上(6a)へ打つとピンが発生する。
    const sfenBefore = customSfen(
      [
        { square: "6i", color: "sente", role: "king" },
        { square: "6g", color: "sente", role: "silver" },
        { square: "1g", color: "sente", role: "pawn" },
      ],
      Hands.from(Hand.empty(), Hand.from([["rook", 1]])),
    );
    const sfenAfterUser = applyMove(sfenBefore, "1g1f"); // 候補手(6g7h)とは無関係な手
    const sfenAfterOpponent = applyMove(sfenAfterUser, "R*6a"); // 相手が飛車を6筋へ打ち、銀をピンする

    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h"] };
    expect(classifyPlanChangeReason(previous, "1g1f", sfenAfterOpponent)).toBe("candidate_piece_pinned");
  });

  // ピンされている駒でも、移動先マスが相手駒の捕獲を伴う場合は安全側でunknownに倒す
  // (discovered attack等の追加考慮が必要になるため、今回の判定範囲には含めない、承認済み)。
  it("ピンされている駒の移動先が相手駒の捕獲を伴う場合は、安全側でunknownのままになる", () => {
    const sfenBefore = customSfen(
      [
        { square: "6i", color: "sente", role: "king" },
        { square: "6g", color: "sente", role: "silver" },
        { square: "7h", color: "gote", role: "pawn" }, // 6g7hの移動先(7h)に相手の歩を配置
        { square: "1g", color: "sente", role: "pawn" },
      ],
      Hands.from(Hand.empty(), Hand.from([["rook", 1]])),
    );
    const sfenAfterUser = applyMove(sfenBefore, "1g1f");
    const sfenAfterOpponent = applyMove(sfenAfterUser, "R*6a");

    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["6g7h"] };
    // 6g7hは(捕獲を伴うため)判定対象から外れ、他に残存候補が無いのでunknownになる。
    expect(classifyPlanChangeReason(previous, "1g1f", sfenAfterOpponent)).toBe("unknown");
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const previous: PlanSnapshot = { targetShapeId: "mino_honmino", candidateMoveUsis: ["8g7h"] };
    const afterSfen = customSfen([{ square: "8h", color: "sente", role: "king" }]);
    const first = classifyPlanChangeReason(previous, "1g1f", afterSfen);
    const second = classifyPlanChangeReason(previous, "1g1f", afterSfen);
    expect(second).toBe(first);
  });
});
