// nextConsiderationDetector.ts(Phase6 Unit4)のテスト。
//
// 並び順・候補手との対応は、実データ(data/shapes/*.json)と実際の局面から
// shapeFormationAnalyzer.ts / routePlanner.ts の出力をそのまま使って検証する
// (手作りの値ではなく、本番で流れるのと同じ材料で固定する)。
// 実局面では作りにくい状況(準備手しか指せない・経路が計算できない等)についてのみ、
// routePlanner.tsの型に沿った最小限の値を組み立てて検証する。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import {
  detectNextConsiderations,
  type NextConsiderationInput,
} from "./nextConsiderationDetector.js";
import { planRoutesToShape } from "./routePlanner.js";
import type { RouteCandidateMove, ShapeSquareRoute } from "./routePlanner.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

/** 実データ・実局面から、detectorへ渡す入力を組み立てる。 */
function inputFor(
  shapeId: string,
  overrides: Partial<NextConsiderationInput> = {},
  sfen: string = INITIAL_SFEN,
  history: string[] = [],
): NextConsiderationInput {
  const shapeResults = analyzeShapeFormation(sfen, history, { initialSfen: INITIAL_SFEN });
  const shapeResult = shapeResults.find((r) => r.shapeId === shapeId);
  const plan = planRoutesToShape(sfen, shapeResults, shapeId);
  return {
    targetShapeId: shapeId,
    shapeName: shapeResult?.name ?? null,
    shapeReviewStatus: shapeResult?.reviewStatus ?? null,
    missingSquares: shapeResult?.missingSquares ?? [],
    routes: plan.routes,
    candidateMoves: plan.candidateMoves,
    isGameEnd: false,
    inCheck: false,
    ...overrides,
  };
}

/** 実局面では作りにくい状況を組み立てるための、最小限の経路。 */
function route(overrides: Partial<ShapeSquareRoute> = {}): ShapeSquareRoute {
  return {
    targetSquare: "7h",
    targetPiece: "銀",
    fromSquare: "7i",
    routeSquares: ["7i", "7h"],
    remainingSteps: 1,
    firstMoveUsis: [],
    alternativeRoutes: [],
    blockingSquare: null,
    blockingSquareHasLegalMove: null,
    blockedReason: null,
    preparatoryMoveUsis: [],
    ...overrides,
  };
}

function candidate(overrides: Partial<RouteCandidateMove> = {}): RouteCandidateMove {
  return {
    moveUsi: "7i7h",
    kind: "route_step",
    targetSquare: "7h",
    targetPiece: "銀",
    routeSquares: ["7i", "7h"],
    remainingStepsAfter: 0,
    clearingSquare: null,
    ...overrides,
  };
}

describe("detectNextConsiderations", () => {
  describe("王手", () => {
    it("王手を受けている場合、in_checkを先頭に置く", () => {
      const facts = detectNextConsiderations(inputFor("mino_honmino", { inCheck: true }));

      expect(facts[0]?.kind).toBe("in_check");
      // 王手の事実は特定のマス・駒・形に紐づかない。
      expect(facts[0]).toEqual({
        kind: "in_check",
        moveUsi: null,
        targetSquare: null,
        targetPiece: null,
        shapeName: null,
        shapeReviewStatus: null,
      });
      // 王手があっても、指せる一手の対応は引き続き述べる。
      expect(facts.some((f) => f.kind === "route_first_move_playable")).toBe(true);
    });

    it("王手を受けていない場合、in_checkを出さない", () => {
      const facts = detectNextConsiderations(inputFor("mino_honmino", { inCheck: false }));

      expect(facts.some((f) => f.kind === "in_check")).toBe(false);
    });
  });

  describe("指せる一手と目標マスの対応", () => {
    it("残り手数の少ない順に並べる(銀冠・初期局面)", () => {
      const facts = detectNextConsiderations(inputFor("mino_ginkanmuri"));
      const steps = facts.filter((f) => f.kind === "route_first_move_playable");

      // routePlanner.tsが返す候補手(routes順): 5i6h(8hへ・残り2) / 4i5h(6gへ・残り1) /
      // 7i7h(8gへ・残り1) / 6i7h(7hへ・残り0)。これを残り手数の少ない順に並べ替える。
      expect(steps.map((f) => f.moveUsi)).toEqual(["6i7h", "4i5h", "7i7h", "5i6h"]);
      expect(steps.map((f) => f.targetSquare)).toEqual(["7h", "6g", "8g", "8h"]);
    });

    it("残り手数が同じ場合、routePlanner.tsのroutesの順序を保つ(銀冠・初期局面)", () => {
      const facts = detectNextConsiderations(inputFor("mino_ginkanmuri"));
      const steps = facts.filter((f) => f.kind === "route_first_move_playable");

      // 4i5h(6gへ)と7i7h(8gへ)はどちらも残り1手。routesでは6gが8gより先に並ぶため、
      // その順序をそのまま保つ(どちらが良いかという判断はしない)。
      const sameSteps = steps.slice(1, 3).map((f) => f.targetSquare);
      expect(sameSteps).toEqual(["6g", "8g"]);
    });

    it("残り手数が同じ場合、routesの順序を保つ(本美濃・初期局面)", () => {
      const facts = detectNextConsiderations(inputFor("mino_honmino"));
      const steps = facts.filter((f) => f.kind === "route_first_move_playable");

      // 7i7h(7hへ・残り0)と4i5h(5hへ・残り0)は同数。routesでは7hが5hより先。
      expect(steps.map((f) => f.moveUsi)).toEqual(["7i7h", "4i5h", "5i6h"]);
      expect(steps.map((f) => f.targetSquare)).toEqual(["7h", "5h", "8h"]);
    });

    it("目標マスと駒種を、routePlanner.tsの値そのまま持つ", () => {
      const facts = detectNextConsiderations(inputFor("mino_honmino"));
      const step = facts.find((f) => f.kind === "route_first_move_playable");

      expect(step).toEqual({
        kind: "route_first_move_playable",
        moveUsi: "7i7h",
        targetSquare: "7h",
        targetPiece: "銀",
        shapeName: null,
        shapeReviewStatus: null,
      });
    });

    it("準備手(preparation)は扱わない(高美濃・初期局面)", () => {
      // 高美濃の初期局面には、7gへの経路を塞ぐ駒をどかす準備手(7g7f)が候補手に含まれる。
      const input = inputFor("mino_takamino");
      expect(input.candidateMoves.some((c) => c.kind === "preparation")).toBe(true);

      const facts = detectNextConsiderations(input);
      const moveUsis = facts.filter((f) => f.kind === "route_first_move_playable").map((f) => f.moveUsi);

      expect(moveUsis).not.toContain("7g7f");
      expect(moveUsis).toEqual(["7i7h", "4i5h", "5i6h"]);
    });
  });

  describe("経路そのものの一手目が指せない場合", () => {
    it("準備手しか指せない場合、総括を1件だけ出す", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", {
          routes: [
            route({ blockingSquare: "7g", blockedReason: "occupied_by_own_piece", preparatoryMoveUsis: ["7g7f"] }),
          ],
          candidateMoves: [
            candidate({ moveUsi: "7g7f", kind: "preparation", remainingStepsAfter: null, clearingSquare: "7g" }),
          ],
        }),
      );

      expect(facts).toEqual([
        {
          kind: "no_playable_route_first_move",
          moveUsi: null,
          targetSquare: null,
          targetPiece: null,
          shapeName: null,
          shapeReviewStatus: null,
        },
      ]);
    });

    it("総括に、準備手・塞いでいるマス等の原因を含めない(原因を推測・断定しない)", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", {
          routes: [
            route({ blockingSquare: "7g", blockedReason: "occupied_by_own_piece", preparatoryMoveUsis: ["7g7f"] }),
          ],
          candidateMoves: [],
        }),
      );

      const summary = facts.find((f) => f.kind === "no_playable_route_first_move");
      expect(summary?.moveUsi).toBeNull();
      expect(summary?.targetSquare).toBeNull();
      expect(summary?.targetPiece).toBeNull();
      expect(summary?.shapeName).toBeNull();
    });

    it("王手を受けている場合は、王手のあとに総括を置く", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", { routes: [route()], candidateMoves: [], inCheck: true }),
      );

      expect(facts.map((f) => f.kind)).toEqual(["in_check", "no_playable_route_first_move"]);
    });

    it("経路が1件も無い場合(経路を計算できなかった場合)は、総括を出さない", () => {
      // 経路が計算できなかったことはUnit 1の経路ブロックが既に表示しているため、
      // Unit 4では扱わない(重複させない)。
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", { routes: [], candidateMoves: [] }),
      );

      expect(facts).toEqual([]);
    });
  });

  describe("形が完成している場合", () => {
    it("未達成マスが0件なら、形完成だけを単独で出す", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", { missingSquares: [], inCheck: true }),
      );

      expect(facts).toEqual([
        {
          kind: "shape_completed",
          moveUsi: null,
          targetSquare: null,
          targetPiece: null,
          shapeName: "本美濃囲い",
          shapeReviewStatus: "human_reviewed",
        },
      ]);
    });

    it("形の名前が分からない場合は、推測せず何も出さない", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", { missingSquares: [], shapeName: null }),
      );

      expect(facts).toEqual([]);
    });

    // STEP ζ-5: shapeReviewStatusは、選択中の形(実データ)のreview_statusを
    // そのまま引き継ぐだけで、このモジュール自体は名前を出してよいかを判断しない
    // (判断はanalysis/nameExposure.tsに集約する)。
    it("shapeReviewStatusは、実データ(inputFor)のreview_statusをそのまま引き継ぐ(銀冠はdraft)", () => {
      const facts = detectNextConsiderations(inputFor("mino_ginkanmuri", { missingSquares: [] }));

      expect(facts).toEqual([
        {
          kind: "shape_completed",
          moveUsi: null,
          targetSquare: null,
          targetPiece: null,
          shapeName: "銀冠",
          shapeReviewStatus: "draft",
        },
      ]);
    });
  });

  describe("表示しないケース", () => {
    it("目標形が決まっていない場合は空配列", () => {
      const facts = detectNextConsiderations(
        inputFor("mino_honmino", { targetShapeId: undefined, inCheck: true }),
      );

      expect(facts).toEqual([]);
    });

    it("対局が終了している場合は空配列", () => {
      const facts = detectNextConsiderations(inputFor("mino_honmino", { isGameEnd: true, inCheck: true }));

      expect(facts).toEqual([]);
    });
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const input = inputFor("mino_ginkanmuri", { inCheck: true });

    expect(detectNextConsiderations(input)).toEqual(detectNextConsiderations(input));
  });

  it("入力のcandidateMoves配列を書き換えない", () => {
    const input = inputFor("mino_ginkanmuri");
    const before = input.candidateMoves.map((c) => c.moveUsi);

    detectNextConsiderations(input);

    expect(input.candidateMoves.map((c) => c.moveUsi)).toEqual(before);
  });
});
