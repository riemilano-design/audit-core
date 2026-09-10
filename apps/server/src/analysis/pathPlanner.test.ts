import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import {
  InvalidSfenError,
  planPathToShape,
  type PathPlanResult,
} from "./pathPlanner.js";
import type { ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";
import { detectIntents } from "./intentDetector.js";
import { selectTargetPurpose } from "./targetPurposeSelector.js";
import { rankReachableShapes } from "./shapeGraphRanking.js";
import { DEFAULT_INITIAL_SFEN } from "./moveHistory.js";
import { getShapes, type ShapeDefinition } from "./shapeRepository.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

// 単体テスト用の最小フィクスチャ。実データ(getShapes())をそのまま流用できる
// ケースはそうし、対応関係の異常系だけカスタムのShapeDefinitionを使う。
function makeShapeResult(overrides: Partial<ShapeFormationResult> & { shapeId: string }): ShapeFormationResult {
  return {
    shapeId: overrides.shapeId,
    name: overrides.name ?? overrides.shapeId,
    side: overrides.side ?? "self",
    family: overrides.family ?? "test",
    parentShapeId: overrides.parentShapeId ?? null,
    perspectiveColor: overrides.perspectiveColor ?? "sente",
    status: overrides.status ?? "forming",
    matchScore: overrides.matchScore ?? 0.5,
    matchedSquares: overrides.matchedSquares ?? [],
    missingSquares: overrides.missingSquares ?? [],
    optionalMatchedSquares: overrides.optionalMatchedSquares ?? [],
    dataConfidenceLevel: overrides.dataConfidenceLevel ?? "medium",
    reviewStatus: overrides.reviewStatus ?? "human_reviewed",
    characteristics: overrides.characteristics ?? "",
    weakAgainst: overrides.weakAgainst,
    formationEvidence: overrides.formationEvidence ?? [],
  };
}

function setPiece(board: Board, square: string, piece: Parameters<typeof board.set>[1]): Board {
  const sq = parseSquareName(square);
  if (sq === undefined) throw new Error(`invalid square: ${square}`);
  const next = board.clone();
  next.set(sq, piece);
  return next;
}

/** 局面制約(玉の存在)を満たすための最小限のダミー玉を、影響しない場所に置く。 */
function buildCustomSfen(pieces: Array<{ square: string; piece: Parameters<typeof Board.prototype.set>[1] }>): string {
  let board = Board.empty();
  board = setPiece(board, "9i", { color: "sente", role: "king" });
  board = setPiece(board, "1a", { color: "gote", role: "king" });
  for (const { square, piece } of pieces) {
    board = setPiece(board, square, piece);
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

// 「対象マスへ複数の合法手が存在する」ケース用のカスタムshape定義。
// 将棋知識としての実在性は問わない(合法手の抽出ロジック自体の検証が目的)。
const MULTI_GOLD_SHAPE: ShapeDefinition = {
  id: "test_multi_gold",
  name: "テスト用(金複数候補)",
  name_kana: "てすとよう",
  side: "self",
  family: "test",
  parent_shape_id: null,
  required_pieces: [{ piece: "金", square: "5e", optional: false }],
  typical_build_order: ["5e"],
  characteristics: "",
  weakAgainst: undefined,
  confidence_level: "medium",
  review_status: "human_reviewed",
};

describe("planPathToShape", () => {
  it("1. 本美濃囲いの未完成局面から、typical_build_order上の次の対象マスを正しく特定できる", () => {
    const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    const result = planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, "mino_honmino");

    // data/shapes/mino_honmino.json: typical_build_order = ["2h","3h","4i","5h"]。
    // 初期局面では4i(金)だけが偶然一致しているため、missingSquares = [2h,3h,5h]。
    // buildOrder中で最初にmissingへ一致するのは"2h"。
    expect(result.targetSquare).toBe("2h");
    expect(result.targetPiece).toBe("玉");
  });

  it("2. 対象マスへ実際に移動できる合法手だけが候補として返る(駒種の異なる手は除外される)", () => {
    // 5e(金)を対象マスとし、4e(金・到達可能)と5f(銀・直進で5eへ到達可能だが駒種違い)を配置。
    const sfen = buildCustomSfen([
      { square: "4e", piece: { color: "sente", role: "gold" } },
      { square: "5f", piece: { color: "sente", role: "silver" } },
    ]);
    const shapeResults = [
      makeShapeResult({ shapeId: "test_multi_gold", missingSquares: ["5e"], status: "forming" }),
    ];

    const result = planPathToShape(sfen, shapeResults, "test_multi_gold", { shapes: [MULTI_GOLD_SHAPE] });

    expect(result.unresolvedReason).toBeNull();
    expect(result.candidateMoves.map((c) => c.moveUsi)).toEqual(["4e5e"]);
  });

  it("3. 複数の合法手が存在する場合、複数候補を保持する", () => {
    // 4e(金)・6e(金)のどちらも横に1マス動くだけで5eへ到達できる。
    const sfen = buildCustomSfen([
      { square: "4e", piece: { color: "sente", role: "gold" } },
      { square: "6e", piece: { color: "sente", role: "gold" } },
    ]);
    const shapeResults = [
      makeShapeResult({ shapeId: "test_multi_gold", missingSquares: ["5e"], status: "forming" }),
    ];

    const result = planPathToShape(sfen, shapeResults, "test_multi_gold", { shapes: [MULTI_GOLD_SHAPE] });

    expect(result.unresolvedReason).toBeNull();
    expect(result.candidateMoves.map((c) => c.moveUsi).sort()).toEqual(["4e5e", "6e5e"]);
  });

  it("4. 既に完成しているshapeは候補手を返さない", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", status: "completed" })];
    const result = planPathToShape(INITIAL_SFEN, shapeResults, "mino_honmino");

    expect(result.candidateMoves).toEqual([]);
    expect(result.targetSquare).toBeNull();
    expect(result.unresolvedReason).toBe("already_completed");
  });

  it("5. 対象マスへ合法手が存在しない場合、安全に空結果になる", () => {
    // 5eに到達できる駒を一切配置しない。
    const sfen = buildCustomSfen([]);
    const shapeResults = [
      makeShapeResult({ shapeId: "test_multi_gold", missingSquares: ["5e"], status: "forming" }),
    ];

    const result = planPathToShape(sfen, shapeResults, "test_multi_gold", { shapes: [MULTI_GOLD_SHAPE] });

    expect(result.candidateMoves).toEqual([]);
    expect(result.targetSquare).toBe("5e");
    expect(result.unresolvedReason).toBe("no_legal_move_to_target");
  });

  it("6. side=opponentのshapeは候補生成の対象にしない", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "some_opponent_shape", side: "opponent", missingSquares: ["5e"], status: "forming" }),
    ];

    const result = planPathToShape(INITIAL_SFEN, shapeResults, "some_opponent_shape");

    expect(result.candidateMoves).toEqual([]);
    expect(result.unresolvedReason).toBe("shape_not_self_side");
  });

  it("6b. shapeResultsに存在しない無関係なshapeIdを指定した場合も安全に未解決を返す", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", missingSquares: ["2h"] })];
    const result = planPathToShape(INITIAL_SFEN, shapeResults, "nonexistent_shape");

    expect(result.candidateMoves).toEqual([]);
    expect(result.unresolvedReason).toBe("shape_result_not_found");
  });

  it("7. typical_build_orderがrequired_piecesと対応づけられない場合、勝手な対応づけをせず未解決にする", () => {
    // buildOrderが"9a"を指しているが、required_piecesには"9a"のエントリが無い
    // (=データ不整合を模したケース)。推測でpieceを補わず未解決として扱う。
    const brokenShape: ShapeDefinition = {
      ...MULTI_GOLD_SHAPE,
      id: "test_broken_correspondence",
      required_pieces: [{ piece: "金", square: "5e", optional: false }],
      typical_build_order: ["9a"],
    };
    const shapeResults = [
      makeShapeResult({ shapeId: "test_broken_correspondence", missingSquares: ["9a"], status: "forming" }),
    ];

    const result = planPathToShape(INITIAL_SFEN, shapeResults, "test_broken_correspondence", {
      shapes: [brokenShape],
    });

    expect(result.candidateMoves).toEqual([]);
    expect(result.targetPiece).toBeNull();
    expect(result.unresolvedReason).toBe("piece_mapping_unresolved");
  });

  it("7b. typical_build_orderがmissingSquaresのどれとも一致しない場合、対象マスを決定できない", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "test_multi_gold", missingSquares: ["1a"], status: "forming" }),
    ];
    const result = planPathToShape(INITIAL_SFEN, shapeResults, "test_multi_gold", { shapes: [MULTI_GOLD_SHAPE] });

    expect(result.unresolvedReason).toBe("target_square_undetermined");
  });

  it("8. 不正なSFENの場合、rules層のInvalidSfenErrorをそのまま伝播させる(独自エラーに置き換えない)", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", missingSquares: ["2h"] })];
    expect(() => planPathToShape("not a valid sfen", shapeResults, "mino_honmino")).toThrow(InvalidSfenError);
  });

  it("9. 同一入力に対して結果が決定的である", () => {
    const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    const a = planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, "mino_honmino");
    const b = planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, "mino_honmino");
    expect(a).toEqual(b);
  });

  it("10. Unit1(shapeGraphRanking)のランキング結果を、変換なしでそのまま入力として利用できる", () => {
    const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    const intentResults = detectIntents(DEFAULT_INITIAL_SFEN, []);
    const targetPurpose = selectTargetPurpose(intentResults);
    const ranked = rankReachableShapes(shapeResults, targetPurpose);

    expect(ranked.length).toBeGreaterThan(0);
    const topShapeId = ranked[0]!.shapeId;

    // rankReachableShapesが返すshapeId(RankedReachableShape.shapeId)をそのまま
    // planPathToShapeのtargetShapeIdへ渡せる(型変換・追加加工は不要)。
    const result: PathPlanResult = planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, topShapeId);
    expect(result.shapeId).toBe(topShapeId);
  });

  describe("Phase1データとの整合性(回帰確認)", () => {
    it("data/shapes/の全shapeについて、実データを渡してもエラーにならず安全な結果を返す", () => {
      const shapeResults = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
      for (const shape of getShapes()) {
        expect(() => planPathToShape(DEFAULT_INITIAL_SFEN, shapeResults, shape.id)).not.toThrow();
      }
    });
  });
});
