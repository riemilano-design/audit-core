// routePlanner.ts(Phase6 Unit1)のテスト。
// 実データ(data/shapes/*.json の本美濃・高美濃・銀冠)をそのまま使えるケースはそうし、
// 異常系・境界だけをカスタムのShapeDefinition/局面で検証する(pathPlanner.test.tsと同じ方針)。
//
// 期待値は「現在のshapeデータ + 将棋のルール」から機械的に決まる値であり、
// 将棋的な良し悪しの主張ではない(どの手が良いかはこのモジュールの責務外)。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import {
  MAX_CANDIDATES_PER_TARGET,
  MAX_CANDIDATES_TOTAL,
  planRoutesToShape,
} from "./routePlanner.js";
import { analyzeShapeFormation, type ShapeFormationResult } from "./shapeFormationAnalyzer.js";
import type { ShapeDefinition } from "./shapeRepository.js";
import { applyMove } from "../rules/applyMove.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

const ALL_SHAPE_IDS = ["mino_honmino", "mino_takamino", "mino_ginkanmuri"] as const;

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

/** 局面制約(両玉の存在)を満たす最小限の盤面を組み立てる。 */
function buildCustomSfen(
  pieces: Array<{ square: string; piece: Parameters<typeof Board.prototype.set>[1] }>,
  senteKingSquare = "9i",
): string {
  let board = Board.empty();
  board = setPiece(board, senteKingSquare, { color: "sente", role: "king" });
  board = setPiece(board, "1a", { color: "gote", role: "king" });
  for (const { square, piece } of pieces) {
    board = setPiece(board, square, piece);
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

/** 初期局面についての、実データを使ったShapeFormationResult一覧。 */
function initialShapeResults(): ShapeFormationResult[] {
  return analyzeShapeFormation(INITIAL_SFEN, []);
}

function routeFor(shapeId: string, targetSquare: string) {
  const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), shapeId);
  return plan.routes.find((r) => r.targetSquare === targetSquare);
}

describe("planRoutesToShape", () => {
  it("1. 本美濃囲い: 初期局面で未達成マスすべての経路が typical_build_order 順に返る", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_honmino");

    // data/shapes/mino_honmino.json: typical_build_order = ["8h","7h","6i","5h"]。
    // 初期局面では6i(金)だけが一致しているため、未達成は 8h / 7h / 5h の3件。
    expect(plan.routes.map((r) => r.targetSquare)).toEqual(["8h", "7h", "5h"]);
    expect(plan.unresolvedReason).toBeNull();
  });

  it("2. 本美濃囲い: 玉は8八まで3手の経路を持ち、その1手目が現在局面で指せる", () => {
    const route = routeFor("mino_honmino", "8h");

    expect(route?.targetPiece).toBe("玉");
    expect(route?.fromSquare).toBe("5i");
    expect(route?.routeSquares).toEqual(["5i", "6h", "7h", "8h"]);
    expect(route?.remainingSteps).toBe(3);
    // pathPlanner.ts(1手先読み)ではここが候補ゼロになっていた局面。
    expect(route?.firstMoveUsis).toEqual(["5i6h"]);
  });

  it("3. 本美濃囲い: 目標マス8hを自分の駒(角)が占有していることを検出する", () => {
    const route = routeFor("mino_honmino", "8h");

    // 8hは先手の角の初期位置。1手目自体は指せるため、blockedReasonはnullのまま
    // 「経路上に自分の駒がいる」という事実だけをblockingSquareで持つ。
    expect(route?.blockingSquare).toBe("8h");
    expect(route?.blockedReason).toBeNull();
  });

  it("4. 本美濃囲い: 銀・金も経路を持ち、1手で到達できる場合は残り手数0になる", () => {
    const silver = routeFor("mino_honmino", "7h");
    const gold = routeFor("mino_honmino", "5h");

    expect(silver?.routeSquares).toEqual(["7i", "7h"]);
    expect(silver?.firstMoveUsis).toEqual(["7i7h"]);
    expect(gold?.routeSquares).toEqual(["4i", "5h"]);
    expect(gold?.firstMoveUsis).toEqual(["4i5h"]);
  });

  it("5. 本美濃囲い: 既に達成済みのマス(6i)の金を動かす候補(6i5h)を生成しない", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_honmino");
    const goldRoute = plan.routes.find((r) => r.targetSquare === "5h");

    // 6iの金は既に本美濃囲いの一部として成立しているため、動かすと形が壊れる。
    // 5hへ向かわせる金は、必ず未使用の4iの金でなければならない。
    expect(goldRoute?.fromSquare).toBe("4i");
    expect(goldRoute?.firstMoveUsis).not.toContain("6i5h");
    expect(plan.candidateMoves.map((c) => c.moveUsi)).not.toContain("6i5h");
    for (const route of plan.routes) {
      expect(route.fromSquare).not.toBe("6i");
    }
  });

  it("6. 高美濃囲い: 初期局面から経路が生成され、金6gは2手の経路になる", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_takamino");
    const gold = plan.routes.find((r) => r.targetSquare === "6g");

    expect(plan.routes.length).toBeGreaterThan(0);
    expect(gold?.fromSquare).toBe("4i");
    expect(gold?.routeSquares).toEqual(["4i", "5h", "6g"]);
    expect(gold?.remainingSteps).toBe(2);
    expect(gold?.firstMoveUsis).toEqual(["4i5h"]);
  });

  it("7. 高美濃囲い: 目標マスを自分の歩が塞ぐ桂7gについて、準備手(7g7f)を生成する", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_takamino");
    const knight = plan.routes.find((r) => r.targetSquare === "7g");

    expect(knight?.fromSquare).toBe("8i");
    expect(knight?.firstMoveUsis).toEqual([]);
    expect(knight?.blockedReason).toBe("occupied_by_own_piece");
    expect(knight?.blockingSquare).toBe("7g");
    expect(knight?.preparatoryMoveUsis).toEqual(["7g7f"]);

    const preparation = plan.candidateMoves.find((c) => c.moveUsi === "7g7f");
    expect(preparation?.kind).toBe("preparation");
    expect(preparation?.clearingSquare).toBe("7g");
    expect(preparation?.remainingStepsAfter).toBeNull();
  });

  it("8. 銀冠: 初期局面から経路が生成され、銀8gは2手の経路になる", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_ginkanmuri");
    const silver = plan.routes.find((r) => r.targetSquare === "8g");

    expect(plan.routes.length).toBeGreaterThan(0);
    expect(silver?.fromSquare).toBe("7i");
    expect(silver?.routeSquares).toEqual(["7i", "7h", "8g"]);
    expect(silver?.firstMoveUsis).toEqual(["7i7h"]);
  });

  it("9. 銀冠: 同じ駒種が複数必要でも、同一の駒を2つの目標へ二重に割り当てない", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_ginkanmuri");
    const goldRoutes = plan.routes.filter((r) => r.targetPiece === "金");

    // 銀冠は金を2枚(7h・6g)必要とする。別々の駒が割り当てられていること。
    expect(goldRoutes).toHaveLength(2);
    expect(new Set(goldRoutes.map((r) => r.fromSquare)).size).toBe(2);

    const fromSquares = plan.routes.map((r) => r.fromSquare);
    expect(new Set(fromSquares).size).toBe(fromSquares.length);
  });

  it("9-2. 1つの駒が、行き先の違う複数の候補手に同時に現れない(銀冠の6九の金)", () => {
    // 銀冠では6九の金が「6七へ向かう代替経路」と「7八へ向かう代表」の両方になり得る。
    // そのまま候補手にすると同じ駒に行き先の違う候補が2つ並び、なぜその手が出ているのかを
    // 追跡できなくなるため、代替経路側を取り除く。
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_ginkanmuri");

    expect(plan.candidateMoves.map((c) => c.moveUsi)).not.toContain("6i5h");
    expect(plan.candidateMoves).toContainEqual(expect.objectContaining({ moveUsi: "6i7h" }));

    const fromSquares = plan.candidateMoves.map((c) => c.routeSquares[0]);
    expect(new Set(fromSquares).size).toBe(fromSquares.length);
  });

  it("10. 3形すべてで、初期局面から候補手が1件以上生成される", () => {
    for (const shapeId of ALL_SHAPE_IDS) {
      const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), shapeId);
      expect(plan.candidateMoves.length, shapeId).toBeGreaterThan(0);
      expect(plan.unresolvedReason, shapeId).toBeNull();
    }
  });

  it("11. 候補手は、どの目標マスへ向かう経路の何手目かを追跡できる情報を持つ", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), "mino_honmino");
    const kingStep = plan.candidateMoves.find((c) => c.moveUsi === "5i6h");

    expect(kingStep?.kind).toBe("route_step");
    expect(kingStep?.targetSquare).toBe("8h");
    expect(kingStep?.targetPiece).toBe("玉");
    expect(kingStep?.routeSquares).toEqual(["5i", "6h", "7h", "8h"]);
    // 3手の経路の1手目なので、指した後の残りは2手。
    expect(kingStep?.remainingStepsAfter).toBe(2);
    expect(kingStep?.clearingSquare).toBeNull();
  });

  it("12. 候補手の件数は、1目標あたり・全体それぞれの上限を超えない", () => {
    for (const shapeId of ALL_SHAPE_IDS) {
      const plan = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), shapeId);
      expect(plan.candidateMoves.length).toBeLessThanOrEqual(MAX_CANDIDATES_TOTAL);

      const countByTarget = new Map<string, number>();
      for (const candidate of plan.candidateMoves) {
        countByTarget.set(candidate.targetSquare, (countByTarget.get(candidate.targetSquare) ?? 0) + 1);
      }
      for (const count of countByTarget.values()) {
        expect(count).toBeLessThanOrEqual(MAX_CANDIDATES_PER_TARGET);
      }
    }
  });

  it("13. 準備手が多数ある場合でも、1目標あたりの上限件数までしか候補にしない", () => {
    // 玉を5eへ動かしたいが、5eには自分の飛車が居るため直接は指せない。
    // 飛車は多数の合法手を持つが、候補として採るのは上限件数まで。
    const sfen = buildCustomSfen(
      [{ square: "5e", piece: { color: "sente", role: "rook" } }],
      "5f",
    );
    const shape: ShapeDefinition = {
      id: "test_king_blocked",
      name: "テスト用(玉の目標マスが自駒で塞がれている)",
      name_kana: "てすとよう",
      side: "self",
      family: "test",
      parent_shape_id: null,
      required_pieces: [{ piece: "玉", square: "5e", optional: false }],
      typical_build_order: ["5e"],
      characteristics: "",
      confidence_level: "medium",
      review_status: "human_reviewed",
    };
    const shapeResults = [makeShapeResult({ shapeId: shape.id, missingSquares: ["5e"] })];

    const plan = planRoutesToShape(sfen, shapeResults, shape.id, { shapes: [shape] });
    const route = plan.routes[0];

    expect(route?.blockedReason).toBe("occupied_by_own_piece");
    expect(route?.blockingSquare).toBe("5e");
    expect(route!.preparatoryMoveUsis.length).toBeGreaterThan(MAX_CANDIDATES_PER_TARGET);
    expect(plan.candidateMoves).toHaveLength(MAX_CANDIDATES_PER_TARGET);
    expect(plan.candidateMoves.every((c) => c.kind === "preparation")).toBe(true);
  });

  it("14. 成る手は経路の1手目として採用しない(駒種が変わり、目標の駒種を満たさなくなるため)", () => {
    // 5dの銀は5cへ「成らずに」も「成って」も動けるが、成ると銀ではなくなる。
    const sfen = buildCustomSfen([{ square: "5d", piece: { color: "sente", role: "silver" } }]);
    const shape: ShapeDefinition = {
      id: "test_silver_promotion",
      name: "テスト用(成りの除外)",
      name_kana: "てすとよう",
      side: "self",
      family: "test",
      parent_shape_id: null,
      required_pieces: [{ piece: "銀", square: "5c", optional: false }],
      typical_build_order: ["5c"],
      characteristics: "",
      confidence_level: "medium",
      review_status: "human_reviewed",
    };
    const shapeResults = [makeShapeResult({ shapeId: shape.id, missingSquares: ["5c"] })];

    const plan = planRoutesToShape(sfen, shapeResults, shape.id, { shapes: [shape] });

    expect(plan.routes[0]?.firstMoveUsis).toEqual(["5d5c"]);
    expect(plan.candidateMoves.map((c) => c.moveUsi)).not.toContain("5d5c+");
  });

  it("15. 相手の手番では候補を返さない(not_self_turn)", () => {
    const sfen = applyMove(INITIAL_SFEN, "7g7f");
    const shapeResults = analyzeShapeFormation(sfen, ["7g7f"]);

    const plan = planRoutesToShape(sfen, shapeResults, "mino_honmino");

    expect(plan.unresolvedReason).toBe("not_self_turn");
    expect(plan.routes).toEqual([]);
    expect(plan.candidateMoves).toEqual([]);
  });

  it("16. 経路を持つ駒が1枚も無い場合、例外を投げずunresolvedReasonを返す", () => {
    // 盤上に金が1枚も無い状態で、金の目標マスを要求する。
    const sfen = buildCustomSfen([]);
    const shape: ShapeDefinition = {
      id: "test_no_gold",
      name: "テスト用(該当する駒が盤上に無い)",
      name_kana: "てすとよう",
      side: "self",
      family: "test",
      parent_shape_id: null,
      required_pieces: [{ piece: "金", square: "5e", optional: false }],
      typical_build_order: ["5e"],
      characteristics: "",
      confidence_level: "medium",
      review_status: "human_reviewed",
    };
    const shapeResults = [makeShapeResult({ shapeId: shape.id, missingSquares: ["5e"] })];

    const plan = planRoutesToShape(sfen, shapeResults, shape.id, { shapes: [shape] });

    expect(plan.routes).toEqual([]);
    expect(plan.candidateMoves).toEqual([]);
    expect(plan.unresolvedReason).toBe("no_route_for_any_square");
  });

  it("17. 同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    for (const shapeId of ALL_SHAPE_IDS) {
      const first = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), shapeId);
      const second = planRoutesToShape(INITIAL_SFEN, initialShapeResults(), shapeId);
      expect(second).toEqual(first);
    }
  });

  it("17-2. 経路に盤の外のマスが含まれない(shogiopsのattacksが返す盤外マスを除外する)", () => {
    // 実対局で「銀を７八へ … ３九→４八→５九→6j→７九→７八」という、
    // 九段目より下の存在しないマス(6j)を通る経路が出た局面。
    const sfen = "lnsgkgsnl/1r5b1/pppppppp1/9/9/2P6/PPSPPPPP1/1B1K3Rp/LN1G1GSNL b p 11";
    const shapeResults = analyzeShapeFormation(sfen, [], { initialSfen: sfen });

    for (const shapeId of ALL_SHAPE_IDS) {
      const plan = planRoutesToShape(sfen, shapeResults, shapeId);
      for (const route of plan.routes) {
        for (const square of [...route.routeSquares, route.fromSquare, route.targetSquare]) {
          expect(square, `${shapeId} / ${route.targetSquare}`).toMatch(/^[1-9][a-i]$/);
        }
      }
    }

    // 盤外を通れないため、この局面の銀7hの経路は7g→7f→6g→7hの3手になる。
    const takamino = planRoutesToShape(sfen, shapeResults, "mino_takamino");
    const silver = takamino.routes.find((r) => r.targetSquare === "7h");
    expect(silver?.routeSquares).toEqual(["7g", "7f", "6g", "7h"]);
    expect(silver?.remainingSteps).toBe(3);
  });

  it("18. 対象のShapeFormationResultが無い場合は例外を投げずshape_result_not_foundを返す", () => {
    const plan = planRoutesToShape(INITIAL_SFEN, [], "mino_honmino");

    expect(plan.unresolvedReason).toBe("shape_result_not_found");
    expect(plan.candidateMoves).toEqual([]);
  });

  it("19. side=opponentのshapeは対象外(shape_not_self_side)", () => {
    const shapeResults = [makeShapeResult({ shapeId: "mino_honmino", side: "opponent", missingSquares: ["8h"] })];

    const plan = planRoutesToShape(INITIAL_SFEN, shapeResults, "mino_honmino");

    expect(plan.unresolvedReason).toBe("shape_not_self_side");
  });

  it("20. 既に完成している形は候補を出さない(already_completed)", () => {
    const shapeResults = [
      makeShapeResult({ shapeId: "mino_honmino", status: "completed", missingSquares: [] }),
    ];

    const plan = planRoutesToShape(INITIAL_SFEN, shapeResults, "mino_honmino");

    expect(plan.unresolvedReason).toBe("already_completed");
  });

  it("21. Shape定義(data/shapes)が見つからない場合はshape_definition_not_foundを返す", () => {
    const shapeResults = [makeShapeResult({ shapeId: "test_unknown_shape", missingSquares: ["5e"] })];

    const plan = planRoutesToShape(INITIAL_SFEN, shapeResults, "test_unknown_shape", { shapes: [] });

    expect(plan.unresolvedReason).toBe("shape_definition_not_found");
  });
});
