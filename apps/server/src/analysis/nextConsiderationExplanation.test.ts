// nextConsiderationExplanation.ts(Phase6 Unit4)のテスト。
// 事実 → 文言の対応表であることを確認する(新しい判断が入っていないこと、
// 評価語が現れないこと、表記が既存の日本語表記規約に従っていること)。

import { makeSfen, parseSfen } from "shogiops/sfen";
import { describe, expect, it } from "vitest";
import {
  detectNextConsiderations,
  type NextConsiderationFact,
  type NextConsiderationKind,
} from "./nextConsiderationDetector.js";
import { explainNextConsiderations } from "./nextConsiderationExplanation.js";
import { planRoutesToShape } from "./routePlanner.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

/** 人間承認済みの禁止語(評価・推奨・損得を表す語)。 */
const FORBIDDEN_WORDS = [
  "最善",
  "おすすめ",
  "悪手",
  "危険",
  "警戒",
  "取り返",
  "有利",
  "不利",
  "損",
  "良い手",
];

function fact(kind: NextConsiderationKind, overrides: Partial<NextConsiderationFact> = {}): NextConsiderationFact {
  return {
    kind,
    moveUsi: null,
    targetSquare: null,
    targetPiece: null,
    shapeName: null,
    shapeReviewStatus: null,
    ...overrides,
  };
}

/** 実データ・実局面から事実を作る(本番と同じ材料で文言を確認する)。 */
function factsFor(shapeId: string, sfen: string = INITIAL_SFEN): NextConsiderationFact[] {
  const shapeResults = analyzeShapeFormation(sfen, [], { initialSfen: INITIAL_SFEN });
  const shapeResult = shapeResults.find((r) => r.shapeId === shapeId);
  const plan = planRoutesToShape(sfen, shapeResults, shapeId);
  return detectNextConsiderations({
    targetShapeId: shapeId,
    shapeName: shapeResult?.name ?? null,
    shapeReviewStatus: shapeResult?.reviewStatus ?? null,
    missingSquares: shapeResult?.missingSquares ?? [],
    routes: plan.routes,
    candidateMoves: plan.candidateMoves,
    isGameEnd: false,
    inCheck: false,
  });
}

describe("explainNextConsiderations", () => {
  it("すべての事実の種類に文言が対応している", () => {
    const all: NextConsiderationFact[] = [
      fact("in_check"),
      fact("route_first_move_playable", { moveUsi: "7i7h", targetSquare: "7h", targetPiece: "銀" }),
      fact("no_playable_route_first_move"),
      fact("shape_completed", { shapeName: "本美濃囲い", shapeReviewStatus: "human_reviewed" }),
    ];

    const messages = explainNextConsiderations(all, INITIAL_SFEN);

    expect(messages.map((m) => m.kind)).toEqual([
      "in_check",
      "route_first_move_playable",
      "no_playable_route_first_move",
      "shape_completed",
    ]);
    for (const message of messages) {
      expect(message.text.length).toBeGreaterThan(0);
    }
  });

  it("王手の文言は承認済みのとおり", () => {
    const messages = explainNextConsiderations([fact("in_check")], INITIAL_SFEN);

    expect(messages[0]?.text).toBe(
      "今、あなたの玉に王手がかかっています。ルール上、王手を解消する手しか指せません。",
    );
  });

  it("指せる一手は、棋譜表記と目標マスの対応で述べる", () => {
    const messages = explainNextConsiderations(
      [fact("route_first_move_playable", { moveUsi: "7i7h", targetSquare: "7h", targetPiece: "銀" })],
      INITIAL_SFEN,
    );

    expect(messages[0]?.text).toBe("７八銀は、銀を７八へ向かわせる道のりの一手目です。");
  });

  it("玉の経路でも同じ文型で述べる", () => {
    const messages = explainNextConsiderations(
      [fact("route_first_move_playable", { moveUsi: "5i6h", targetSquare: "8h", targetPiece: "玉" })],
      INITIAL_SFEN,
    );

    expect(messages[0]?.text).toBe("６八玉は、玉を８八へ向かわせる道のりの一手目です。");
  });

  it("棋譜表記を作れない手は、マス目表記へフォールバックする(表記を推測しない)", () => {
    const messages = explainNextConsiderations(
      // USIとしては解釈できるが、その局面の駒が居ないマスからの手(棋譜表記が作れない)。
      [fact("route_first_move_playable", { moveUsi: "5e5d", targetSquare: "7h", targetPiece: "銀" })],
      INITIAL_SFEN,
    );

    expect(messages[0]?.text).toContain("５五→５四");
  });

  it("総括の文言は承認済みのとおり", () => {
    const messages = explainNextConsiderations([fact("no_playable_route_first_move")], INITIAL_SFEN);

    expect(messages[0]?.text).toBe(
      "今の局面では、その形へ向かう道のりの一手目を、どれも指すことができません。",
    );
  });

  it("形完成の文言は承認済みのとおり", () => {
    const messages = explainNextConsiderations(
      [fact("shape_completed", { shapeName: "本美濃囲い", shapeReviewStatus: "human_reviewed" })],
      INITIAL_SFEN,
    );

    expect(messages[0]?.text).toBe("「本美濃囲い」に必要なマスは、すべて埋まっています。");
  });

  describe("並び順の注記", () => {
    it("指せる一手を2件以上並べるときだけ、末尾に付ける", () => {
      const messages = explainNextConsiderations(factsFor("mino_honmino"), INITIAL_SFEN);

      expect(messages[messages.length - 1]).toEqual({
        kind: "ordering_note",
        text: "残り手数の少ない順に並べています。手の良し悪しの順ではありません。",
      });
    });

    it("指せる一手が1件だけなら付けない", () => {
      const messages = explainNextConsiderations(
        [fact("route_first_move_playable", { moveUsi: "7i7h", targetSquare: "7h", targetPiece: "銀" })],
        INITIAL_SFEN,
      );

      expect(messages.map((m) => m.kind)).toEqual(["route_first_move_playable"]);
    });

    it("指せる一手が無ければ付けない", () => {
      const messages = explainNextConsiderations(
        [fact("in_check"), fact("no_playable_route_first_move")],
        INITIAL_SFEN,
      );

      expect(messages.some((m) => m.kind === "ordering_note")).toBe(false);
    });
  });

  describe("値が欠けている事実", () => {
    it("指し手・目標マス・駒種が欠けている場合は、その事実を表示しない", () => {
      const messages = explainNextConsiderations([fact("route_first_move_playable")], INITIAL_SFEN);

      expect(messages).toEqual([]);
    });

    it("形の名前が欠けている場合は、その事実を表示しない", () => {
      const messages = explainNextConsiderations([fact("shape_completed")], INITIAL_SFEN);

      expect(messages).toEqual([]);
    });
  });

  describe("表記と禁止語", () => {
    it("マス目が日本語表記(全角)になっている", () => {
      const messages = explainNextConsiderations(factsFor("mino_ginkanmuri"), INITIAL_SFEN);
      const texts = messages.map((m) => m.text).join("");

      expect(texts).toContain("７八");
      expect(texts).toContain("８八");
      // USI形式のマス目("7h"等)がそのまま文言に混ざらないこと。
      expect(texts).not.toMatch(/[1-9][a-i]/);
    });

    it("評価語・推奨・損得を表す語が現れない", () => {
      const allTexts = [
        ...explainNextConsiderations(factsFor("mino_honmino"), INITIAL_SFEN),
        ...explainNextConsiderations(factsFor("mino_takamino"), INITIAL_SFEN),
        ...explainNextConsiderations(factsFor("mino_ginkanmuri"), INITIAL_SFEN),
        ...explainNextConsiderations(
          [
            fact("in_check"),
            fact("no_playable_route_first_move"),
            fact("shape_completed", { shapeName: "本美濃囲い", shapeReviewStatus: "human_reviewed" }),
          ],
          INITIAL_SFEN,
        ),
      ]
        .map((m) => m.text)
        .join("");

      for (const word of FORBIDDEN_WORDS) {
        expect(allTexts).not.toContain(word);
      }
    });
  });

  it("事実が空なら文言も空", () => {
    expect(explainNextConsiderations([], INITIAL_SFEN)).toEqual([]);
  });

  // STEP ζ-5: 露出経路5(必要なマスの説明)。review_statusが"draft"の場合にだけ
  // 注記("内容を確認中")が付く(analysis/nameExposure.tsのsite="squares")。
  describe("review_statusによる名前の露出制御(STEP ζ-5)", () => {
    it("draftの形の場合、名前に(内容を確認中)の注記が付く", () => {
      const messages = explainNextConsiderations(
        [fact("shape_completed", { shapeName: "銀冠", shapeReviewStatus: "draft" })],
        INITIAL_SFEN,
      );

      expect(messages[0]?.text).toBe("「銀冠」(内容を確認中)に必要なマスは、すべて埋まっています。");
    });

    it("human_reviewedの形の場合、注記は付かない", () => {
      const messages = explainNextConsiderations(
        [fact("shape_completed", { shapeName: "本美濃囲い", shapeReviewStatus: "human_reviewed" })],
        INITIAL_SFEN,
      );

      expect(messages[0]?.text).toBe("「本美濃囲い」に必要なマスは、すべて埋まっています。");
    });

    it("expert_verifiedの形の場合も、注記は付かない(human_reviewedと区別しない)", () => {
      const messages = explainNextConsiderations(
        [fact("shape_completed", { shapeName: "本美濃囲い", shapeReviewStatus: "expert_verified" })],
        INITIAL_SFEN,
      );

      expect(messages[0]?.text).toBe("「本美濃囲い」に必要なマスは、すべて埋まっています。");
    });
  });
});
