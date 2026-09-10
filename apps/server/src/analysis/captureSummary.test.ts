// captureSummary.ts(Phase 7 Unit 4 STEP 4-3b・2026-09-10人間承認)のテスト。
// 人間承認済みJ・K-1・L-1・N-1・Oの仕様どおりに、対局開始からの全手を毎回再生して
// 「駒の得喪」を集約できているかを確認する。良し悪し・評価語は一切扱わない。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import { countCaptures, explainCaptureSummary } from "./captureSummary.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

/** 両玉を置いたうえで、指定した駒を並べた局面を作る(先手番)。boardEventDetector.test.tsと同じ方式。 */
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

describe("countCaptures / explainCaptureSummary", () => {
  it("双方0枚のときは何も返さない(N-1)", () => {
    expect(explainCaptureSummary([], INITIAL_SFEN)).toEqual([]);

    const counts = countCaptures([], INITIAL_SFEN);
    expect(counts.you.size).toBe(0);
    expect(counts.opponent.size).toBe(0);
  });

  it("自分のみ取っている場合の文言(ζ-3)", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    const counts = countCaptures(["5e5d"], sfen);
    expect(counts.you.get("pawn")).toBe(1);
    expect(counts.opponent.size).toBe(0);

    expect(explainCaptureSummary(["5e5d"], sfen)).toEqual([
      {
        kind: "capture_summary",
        text: "ここまでに、あなたが相手の歩を1枚取っています。相手はまだ駒を取っていません。",
      },
    ]);
  });

  it("相手のみ取っている場合の文言(ζ-3)", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);

    // 自分は無関係な手(玉を動かす)、相手が5d5eで歩を取る。
    const moveHistory = ["9i8i", "5d5e"];

    const counts = countCaptures(moveHistory, sfen);
    expect(counts.you.size).toBe(0);
    expect(counts.opponent.get("pawn")).toBe(1);

    expect(explainCaptureSummary(moveHistory, sfen)).toEqual([
      {
        kind: "capture_summary",
        text: "ここまでに、相手があなたの歩を1枚取っています。あなたはまだ駒を取っていません。",
      },
    ]);
  });

  it("双方が取っている場合の文言(ζ-3)", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
      { square: "3e", color: "sente", role: "pawn" },
      { square: "3d", color: "gote", role: "pawn" },
    ]);

    // 1手目: 自分が5筋の歩を取る。2手目: 相手が3筋の歩を取り返す。
    const moveHistory = ["5e5d", "3d3e"];

    const counts = countCaptures(moveHistory, sfen);
    expect(counts.you.get("pawn")).toBe(1);
    expect(counts.opponent.get("pawn")).toBe(1);

    expect(explainCaptureSummary(moveHistory, sfen)).toEqual([
      {
        kind: "capture_summary",
        text: "ここまでに、あなたは相手の歩を1枚、相手はあなたの歩を1枚取っています。",
      },
    ]);
  });

  it("K-1: 取られた成駒(と金)は元の駒種(歩)で数える", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "tokin" },
    ]);

    const counts = countCaptures(["5e5d"], sfen);
    expect(counts.you.get("pawn")).toBe(1);
    expect(counts.you.has("tokin" as Role)).toBe(false);

    expect(explainCaptureSummary(["5e5d"], sfen)).toEqual([
      {
        kind: "capture_summary",
        text: "ここまでに、あなたが相手の歩を1枚取っています。相手はまだ駒を取っていません。",
      },
    ]);
  });

  it("L-1: 複数駒種は飛→角→金→銀→桂→香→歩の固定順で連結する(取られた時系列順ではない)", () => {
    // 相手(gote)の飛車が5e→5d→5cと進み、香(5d)→桂(5c)の順に取る
    // (取った時系列は香が先・桂が後)。固定順(桂→香)どおりに並ぶことを確認する。
    const sfen = buildSfen([
      { square: "5c", color: "sente", role: "knight" },
      { square: "5d", color: "sente", role: "lance" },
      { square: "5e", color: "gote", role: "rook" },
    ]);

    const moveHistory = ["9i9h", "5e5d", "9h9i", "5d5c"];

    const counts = countCaptures(moveHistory, sfen);
    expect(counts.opponent.get("lance")).toBe(1);
    expect(counts.opponent.get("knight")).toBe(1);
    expect(counts.you.size).toBe(0);

    expect(explainCaptureSummary(moveHistory, sfen)).toEqual([
      {
        kind: "capture_summary",
        text: "ここまでに、相手があなたの桂を1枚、香を1枚取っています。あなたはまだ駒を取っていません。",
      },
    ]);
  });

  it("打つ手(ドロップ)は捕獲として数えない", () => {
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
    const sfen = makeSfen(pos);

    const counts = countCaptures(["P*5e"], sfen);
    expect(counts.you.size).toBe(0);
    expect(counts.opponent.size).toBe(0);
    expect(explainCaptureSummary(["P*5e"], sfen)).toEqual([]);
  });

  it("同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    const sfen = buildSfen([
      { square: "5e", color: "sente", role: "pawn" },
      { square: "5d", color: "gote", role: "pawn" },
    ]);
    const moveHistory = ["5e5d"];

    expect(explainCaptureSummary(moveHistory, sfen)).toEqual(explainCaptureSummary(moveHistory, sfen));
    expect(countCaptures(moveHistory, sfen)).toEqual(countCaptures(moveHistory, sfen));
  });
});
