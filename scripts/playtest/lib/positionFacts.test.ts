// STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §4 の P-1〜P-9)。玉の区域に利きが届く駒の枚数と升の数。**エンジンは起動しない。**
//
// 【正解の置き方】期待は計画書 4. の表のまま、盤を手で描いて導いた値(実装の出力から写さない)。盤の図は計画書の実装の節に残す。
// SFEN の段は a(後手の側)から i(先手の側)、筋は 9 から 1 の順に書く。
// 【この試験が確かめないこと】Failure Event・diagnosis-moment の行への配線(lib/failureEvent.test.ts・lib/counterfactual.test.ts・lib/diagnosisMoment.test.ts)。
// スキーマの変種と境目(lib/failureEventSchema.test.ts)。

import { describe, expect, it } from "vitest";
import { positionFactsDiff, positionFactsOf, type PositionFacts, type PositionFactsRules } from "./positionFacts.js";

const RULES: PositionFactsRules = { zone: "king_and_eight_neighbors", reach: "non_king_pieces", control: "squares" };
const factsOf = (sfen: string): PositionFacts => positionFactsOf(sfen, RULES);
const counts = (bySente: number, byGote: number) => ({ bySente, byGote });
const ZERO = counts(0, 0);

const INIT = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
/** P-3: 先手玉 9i・後手玉 5a・先手飛 5e・後手金 5b だけ(先手番) */
const P3 = "4k4/4g4/9/9/4R4/9/9/9/K8 b - 1";
/** P-4: P-3 の後手金を 5c に */
const P4 = "4k4/9/4g4/9/4R4/9/9/9/K8 b - 1";

describe("positionFactsOf(計画 §4 の P-1〜P-9)", () => {
  it("P-1 平手の初期局面: 区域の升 6 と 6。区域に届く相手の駒は両側 0、味方の駒は先手 5(金 4i・6i、銀 3i・7i、飛 2h)・後手 5。先手玉の区域に先手の利きが届く升は 4(4h・5h・6h・5i)", () => {
    expect(factsOf(INIT)).toStrictEqual({
      zoneSquares: { ownKingZone: 6, opponentKingZone: 6 },
      zonePieces: { ownKingZone: counts(5, 0), opponentKingZone: counts(0, 5) },
      zoneControl: { ownKingZone: counts(4, 0), opponentKingZone: counts(0, 4) },
    });
  });

  it("P-2 先手玉 9i・後手玉 5e だけ: 区域の升 4 と 9、ほかはすべて 0(玉の利きは数えない)", () => {
    expect(factsOf("9/9/9/9/4k4/9/9/9/K8 b - 1")).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 9 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: ZERO },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: ZERO },
    });
  });

  it("P-3 飛は 5d・5c・5b で止まり 5b を含む: 後手玉の区域に先手の駒 1・升 1(5b)、後手の駒 1・升 3(金の利き 4b・6b・5a)。先手玉の区域は 0", () => {
    expect(factsOf(P3)).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 6 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(1, 1) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(1, 3) },
    });
  });

  it("P-4 後手金を 5c に置くと飛は 5d・5c で止まる: 後手玉の区域に先手の駒 0・升 0、後手の駒 1・升 1(5b)", () => {
    expect(factsOf(P4)).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 6 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(0, 1) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(0, 1) },
    });
  });

  it("P-5 玉が盤に無い側は 3 つの欄とも null(0 にしない)。差もその側は null", () => {
    const noSenteKing = factsOf("4k4/9/9/9/9/9/9/9/9 b - 1");
    expect(noSenteKing).toStrictEqual({
      zoneSquares: { ownKingZone: null, opponentKingZone: 6 },
      zonePieces: { ownKingZone: null, opponentKingZone: ZERO },
      zoneControl: { ownKingZone: null, opponentKingZone: ZERO },
    });
    expect(factsOf("9/9/9/9/9/9/9/9/K8 b - 1")).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: null },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: null },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: null },
    });
    expect(positionFactsDiff(noSenteKing, factsOf(INIT))).toStrictEqual({
      zonePieces: { ownKingZone: null, opponentKingZone: counts(0, -5) },
      zoneControl: { ownKingZone: null, opponentKingZone: counts(0, -4) },
    });
  });

  it("P-6 P-3 に先手の持ち駒の金を足しても P-3 と同じ(持ち駒は数えない)", () => {
    expect(factsOf("4k4/4g4/9/9/4R4/9/9/9/K8 b G 1")).toStrictEqual(factsOf(P3));
  });

  it("P-7 先手のと 4c・6c が後手玉の区域の 5b に 2 枚とも届く: 駒 2・升 3(4b・5b・6b。延べ数なら 4)", () => {
    expect(factsOf("4k4/9/3+P1+P3/9/9/9/9/9/K8 b - 1")).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 6 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(2, 0) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(3, 0) },
    });
  });

  it("P-8 先手の馬 6c: 後手玉の区域の升 3(6b = 玉の形、5b・4a = 線。線だけと取り違えると 2)", () => {
    expect(factsOf("4k4/9/3+B5/9/9/9/9/9/K8 b - 1")).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 6 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(1, 0) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(3, 0) },
    });
  });

  it("P-9 先手のと金 4c: 後手玉の区域の升 2(4b・5b = 金の形。歩の形と取り違えると 1)", () => {
    expect(factsOf("4k4/9/5+P3/9/9/9/9/9/K8 b - 1")).toStrictEqual({
      zoneSquares: { ownKingZone: 4, opponentKingZone: 6 },
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(1, 0) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(2, 0) },
    });
  });
});

describe("positionFactsDiff", () => {
  it("P-3 − P-4: 後手玉の区域の駒の差 (1, 0)・升の差 (1, 2)、先手玉の区域の差 (0, 0)。向きは minuend − subtrahend", () => {
    expect(positionFactsDiff(factsOf(P3), factsOf(P4))).toStrictEqual({
      zonePieces: { ownKingZone: ZERO, opponentKingZone: counts(1, 0) },
      zoneControl: { ownKingZone: ZERO, opponentKingZone: counts(1, 2) },
    });
  });
});
