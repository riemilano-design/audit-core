// boardEventDetector.ts(Phase6 Unit3)のテスト。
// 盤面イベントは将棋のルールだけから決まるため、shapeデータには一切依存しない。
// 期待値は「実際に指された手で何が起きたか」という事実のみで、良し悪しは一切含まない。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import { detectBoardEvents } from "./boardEventDetector.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

/** 両玉を置いたうえで、指定した駒を並べた局面を作る(先手番)。 */
function buildSfen(
  pieces: Array<{ square: string; color: Color; role: Role }>,
  kings: { sente: string; gote: string } = { sente: "9i", gote: "1a" },
): string {
  let board = Board.empty();
  const place = (square: string, color: Color, role: Role): void => {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  };
  place(kings.sente, "sente", "king");
  place(kings.gote, "gote", "king");
  for (const { square, color, role } of pieces) place(square, color, role);

  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("detectBoardEvents", () => {
  it("1. 自分が相手の駒を取った場合、captured_by_youを駒種・マスつきで返す", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    const events = detectBoardEvents(sfen, "5e5d", null);

    expect(events).toEqual([{ kind: "captured_by_you", piece: "歩", square: "5d" }]);
  });

  it("2. 相手が自分の駒を取った場合、captured_by_opponentを返す", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    // 自分は無関係な手(玉を動かす)、相手が5d5eで歩を取る。
    const events = detectBoardEvents(sfen, "9i8i", "5d5e");

    expect(events).toEqual([{ kind: "captured_by_opponent", piece: "歩", square: "5e" }]);
  });

  it("3. 自分の手で王手がかかった場合、check_givenを返す", () => {
    // 4eの飛車を5eへ寄せると、5筋が通って5aの後手玉に王手がかかる。
    const sfen = buildSfen([{ square: "4e", color: "sente", role: "rook" }], { sente: "9i", gote: "5a" });

    const events = detectBoardEvents(sfen, "4e5e", null);

    expect(events).toEqual([{ kind: "check_given", piece: null, square: null }]);
  });

  it("4. 相手の手で王手がかかった場合、check_receivedを返す", () => {
    // 自分が玉を6九へ寄せたあと、4一の後手飛車が4九へ下りると、九段目が通って
    // 6九の先手玉に王手がかかる。
    const sfen = buildSfen([{ square: "4a", color: "gote", role: "rook" }], { sente: "5i", gote: "1a" });

    const events = detectBoardEvents(sfen, "5i6i", "4a4i");

    expect(events.map((e) => e.kind)).toContain("check_received");
  });

  it("5. 自分の手が成りだった場合、promoted_by_youを返す", () => {
    const sfen = buildSfen([{ square: "5d", color: "sente", role: "pawn" }]);

    const events = detectBoardEvents(sfen, "5d5c+", null);

    expect(events).toEqual([{ kind: "promoted_by_you", piece: "歩", square: "5c" }]);
  });

  it("6. 相手の手が成りだった場合、promoted_by_opponentを返す", () => {
    const sfen = buildSfen([{ square: "5f", color: "gote", role: "pawn" }]);

    const events = detectBoardEvents(sfen, "9i8i", "5f5g+");

    expect(events).toEqual([{ kind: "promoted_by_opponent", piece: "歩", square: "5g" }]);
  });

  it("7. 何も起きていない手では、イベントを1件も返さない", () => {
    const events = detectBoardEvents(INITIAL_SFEN, "7g7f", "1c1d");

    expect(events).toEqual([]);
  });

  it("8. 駒種が対応表に無い場合(成駒を取った場合)は、駒種を推測せずnullにする", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "tokin" },
    ]);

    const events = detectBoardEvents(sfen, "5e5d", null);

    expect(events).toEqual([{ kind: "captured_by_you", piece: null, square: "5d" }]);
  });

  it("9. 捕獲と成りが同時に起きた場合、両方を返す", () => {
    const sfen = buildSfen([
      { square: "5d", color: "sente", role: "pawn" },
      { square: "5c", color: "gote", role: "silver" },
    ]);

    const events = detectBoardEvents(sfen, "5d5c+", null);

    expect(events).toEqual([
      { kind: "captured_by_you", piece: "銀", square: "5c" },
      { kind: "promoted_by_you", piece: "歩", square: "5c" },
    ]);
  });

  it("10. 相手が応手していない場合(null)は、自分の手の分だけを返す", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    const events = detectBoardEvents(sfen, "5e5d", null);

    expect(events).toHaveLength(1);
    expect(events[0]?.kind).toBe("captured_by_you");
  });

  it("11. 同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    expect(detectBoardEvents(sfen, "5e5d", null)).toEqual(detectBoardEvents(sfen, "5e5d", null));
  });

  it("12. 打つ手(ドロップ)を捕獲・成りとして扱わない", () => {
    // 打つ手は駒のあるマスへは打てないため、捕獲は起こり得ない。
    let board = Board.empty();
    const place = (square: string, color: Color, role: Role): void => {
      const sq = parseSquareName(square)!;
      board = board.clone();
      board.set(sq, { color, role });
    };
    place("9i", "sente", "king");
    place("1a", "gote", "king");
    const hands = Hands.empty();
    hands.color("sente").capture("pawn");
    const pos = Shogi.from({ board, hands, turn: "sente", moveNumber: 1 }, false).unwrap();

    const events = detectBoardEvents(makeSfen(pos), "P*5e", null);

    expect(events).toEqual([]);
  });
});
