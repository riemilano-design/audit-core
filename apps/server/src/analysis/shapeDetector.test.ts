import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import type { Color, Role } from "shogiops/types";
import { parseSquareName } from "shogiops/util";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { describe, expect, it } from "vitest";
import { detectShapes, InvalidSfenError, type ShapeDetectionResult } from "./shapeDetector.js";
import type { ShapeDefinition } from "./shapeRepository.js";
import { getShapes } from "./shapeRepository.js";

const STARTPOS_SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

interface PieceFixture {
  square: string;
  color: Color;
  role: Role;
}

// data/shapes/mino_*.json はMVP座標規約(docs/DATA_MODEL.md: self=先手固定)により
// 先手側絶対座標で記録されているため、テストのSFENも先手駒として組み立てる
// (prototypes/shape-matcher/shape-matcher.sente-shapes.test.mjs と同じ方針)。
function buildSfen(pieces: PieceFixture[]): string {
  let board = Board.empty();
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square in test fixture: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

function findResult(results: ShapeDetectionResult[], shapeId: string): ShapeDetectionResult {
  const found = results.find((r) => r.shapeId === shapeId);
  if (!found) throw new Error(`shape not found in results: ${shapeId}`);
  return found;
}

function firstResult(results: ShapeDetectionResult[]): ShapeDetectionResult {
  const [first] = results;
  if (!first) throw new Error("results is empty");
  return first;
}

// テスト専用の最小shape定義(data/shapes/配下の本番データは変更しない)。
// 本美濃囲いの必須駒配置(2h玉・3h銀・4i金・5h金)をそのまま使う。
const TEST_HONMINO: ShapeDefinition = {
  id: "test_honmino",
  name: "本美濃囲い(テスト用)",
  name_kana: "ほんみのがこい",
  side: "self",
  family: "美濃系",
  parent_shape_id: null,
  required_pieces: [
    { piece: "玉", square: "2h", optional: false },
    { piece: "銀", square: "3h", optional: false },
    { piece: "金", square: "4i", optional: false },
    { piece: "金", square: "5h", optional: false },
  ],
  characteristics: "",
  confidence_level: "medium",
  review_status: "human_reviewed",
};

const HONMINO_COMPLETE_PIECES: PieceFixture[] = [
  { square: "2h", color: "sente", role: "king" },
  { square: "3h", color: "sente", role: "silver" },
  { square: "4i", color: "sente", role: "gold" },
  { square: "5h", color: "sente", role: "gold" },
];

describe("detectShapes", () => {
  it("形がまったく無い局面 -> status: none, matchScore: 0", () => {
    const sfen = buildSfen([{ square: "1a", color: "sente", role: "king" }]);
    const result = firstResult(detectShapes(sfen, [TEST_HONMINO]));
    expect(result.status).toBe("none");
    expect(result.matchScore).toBe(0);
    expect(result.matchedSquares).toEqual([]);
  });

  it("形成中の局面(必須駒の一部のみ一致) -> status: forming, 0 < matchScore < 1", () => {
    const partial = HONMINO_COMPLETE_PIECES.filter((p) => p.square === "2h" || p.square === "3h");
    const sfen = buildSfen(partial);
    const result = firstResult(detectShapes(sfen, [TEST_HONMINO]));

    expect(result.status).toBe("forming");
    expect(result.matchScore).toBeCloseTo(0.5);
    expect(result.matchedSquares.sort()).toEqual(["2h", "3h"]);
    expect(result.missingSquares.sort()).toEqual(["4i", "5h"]);
  });

  it("形が成立している局面 -> status: completed, matchScore: 1", () => {
    const sfen = buildSfen(HONMINO_COMPLETE_PIECES);
    const result = firstResult(detectShapes(sfen, [TEST_HONMINO]));

    expect(result.status).toBe("completed");
    expect(result.matchScore).toBe(1);
    expect(result.missingSquares).toEqual([]);
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => detectShapes("not-a-valid-sfen", [TEST_HONMINO])).toThrow(InvalidSfenError);
  });

  it("複数Shape候補がある場合、それぞれ独立にstatus/matchScoreを返し、一致度が高い順に並ぶ", () => {
    // 本美濃が完成している局面は、高美濃(4g金・3g桂が未配置)・銀冠(2g銀・3h金が不一致)
    // からは見ると「まだ途中/ほぼ無関係」に見える、という現実の形の親子関係を再現する。
    const realShapes = getShapes();
    const sfen = buildSfen(HONMINO_COMPLETE_PIECES);
    const results = detectShapes(sfen, realShapes);

    const honmino = findResult(results, "mino_honmino");
    const takamino = findResult(results, "mino_takamino");
    const ginkanmuri = findResult(results, "mino_ginkanmuri");

    expect(honmino.status).toBe("completed");
    expect(takamino.status).toBe("forming");
    expect(ginkanmuri.status === "forming" || ginkanmuri.status === "none").toBe(true);

    // 一致度の高い順(降順)に並んでいることを確認する。
    const scores = results.map((r) => r.matchScore);
    for (let i = 1; i < scores.length; i++) {
      expect(scores[i - 1] ?? 0).toBeGreaterThanOrEqual(scores[i] ?? 0);
    }
    expect(firstResult(results).shapeId).toBe("mino_honmino");
  });

  it("同じ局面に対して常に同じ結果を返す(決定的)", () => {
    const sfen = buildSfen(HONMINO_COMPLETE_PIECES);
    const realShapes = getShapes();
    const first = detectShapes(sfen, realShapes);
    const second = detectShapes(sfen, realShapes);
    expect(second).toEqual(first);
  });

  it("初期局面(startpos)でも例外にならず、既存の全shapeについて結果を返す", () => {
    const realShapes = getShapes();
    const results = detectShapes(STARTPOS_SFEN, realShapes);
    expect(results).toHaveLength(realShapes.length);
    for (const result of results) {
      expect(["none", "forming", "completed"]).toContain(result.status);
    }
  });
});
