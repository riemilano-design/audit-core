// pieceThreatDetector.ts(Phase 7 Unit 4 STEP 4-3)のテスト。
// rules/attackedPieces.ts が返した幾何上の事実から、B-1(対象駒種)・D(自分の駒の並び順)・
// 決定 I-1(1行内の攻め駒の並び順)を機械的に適用しているかだけを確認する。

import { describe, expect, it } from "vitest";
import type { AttackedPiece } from "../rules/attackedPieces.js";
import { detectPieceThreats } from "./pieceThreatDetector.js";

describe("detectPieceThreats", () => {
  it("B-1: 玉・歩・と金(=歩)を除き、飛角金銀桂香(成駒を含む)を対象にする", () => {
    const attacked: AttackedPiece[] = [
      { square: "1a", role: "king", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "2a", role: "pawn", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "3a", role: "tokin", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "9a", role: "rook", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "8b", role: "dragon", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "5b", role: "bishop", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "6c", role: "horse", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "4a", role: "gold", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "3b", role: "silver", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "2b", role: "promotedsilver", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "7a", role: "knight", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "6a", role: "promotedknight", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "8a", role: "lance", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "1c", role: "promotedlance", attackers: [{ square: "9i", role: "pawn" }] },
    ];

    const result = detectPieceThreats(attacked);
    const squares = result.map((fact) => fact.square);

    expect(squares).not.toContain("1a"); // 玉
    expect(squares).not.toContain("2a"); // 歩
    expect(squares).not.toContain("3a"); // と金(歩として除外)
    expect(squares).toEqual(
      expect.arrayContaining(["9a", "8b", "6c", "5b", "4a", "3b", "2b", "7a", "6a", "8a", "1c"]),
    );
    expect(result).toHaveLength(11);
  });

  it("D: 飛→角→金→銀→桂→香の固定順、同じ駒種は筋の大きい順で並べる", () => {
    // わざと逆順・混在した並びで入力し、Dの固定順に並び替わることを確認する。
    const attacked: AttackedPiece[] = [
      { square: "5a", role: "lance", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "9a", role: "lance", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "3a", role: "knight", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "4a", role: "silver", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "2a", role: "gold", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "1a", role: "bishop", attackers: [{ square: "9i", role: "pawn" }] },
      { square: "6a", role: "rook", attackers: [{ square: "9i", role: "pawn" }] },
    ];

    const result = detectPieceThreats(attacked);

    expect(result.map((fact) => fact.square)).toEqual(["6a", "1a", "2a", "4a", "3a", "9a", "5a"]);
  });

  it("1行内の攻め駒は決定Ⅰ-1の順(飛→角→金→銀→桂→香→歩→玉、同駒種は筋の大きい順)に並ぶ", () => {
    const attacked: AttackedPiece[] = [
      {
        square: "5e",
        role: "gold",
        attackers: [
          { square: "1a", role: "king" },
          { square: "2a", role: "pawn" },
          { square: "3a", role: "silver" },
          { square: "9a", role: "rook" },
          { square: "4a", role: "pawn" },
        ],
      },
    ];

    const result = detectPieceThreats(attacked);

    expect(result[0]!.attackers).toEqual([
      { square: "9a", role: "rook" },
      { square: "3a", role: "silver" },
      { square: "4a", role: "pawn" },
      { square: "2a", role: "pawn" },
      { square: "1a", role: "king" },
    ]);
  });

  it("1つの攻め駒が複数の自分の駒に当たる場合は、駒ごとに別の件になる(P-1局22手目のと金の例)", () => {
    // 実際の対局(P-1局22手目)で観測された、と金(8h)が銀・桂・香の3駒に当たっている局面。
    const attacked: AttackedPiece[] = [
      { square: "6f", role: "pawn", attackers: [{ square: "3c", role: "bishop" }] },
      { square: "7i", role: "silver", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "8i", role: "knight", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "9i", role: "lance", attackers: [{ square: "8h", role: "tokin" }] },
    ];

    expect(detectPieceThreats(attacked)).toEqual([
      { square: "7i", role: "silver", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "8i", role: "knight", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "9i", role: "lance", attackers: [{ square: "8h", role: "tokin" }] },
    ]);
  });

  it("決定的: 同じ入力に対して常に同じ結果を返す", () => {
    const attacked: AttackedPiece[] = [
      { square: "7i", role: "silver", attackers: [{ square: "8h", role: "tokin" }] },
      { square: "8i", role: "knight", attackers: [{ square: "8h", role: "tokin" }] },
    ];

    expect(detectPieceThreats(attacked)).toEqual(detectPieceThreats(attacked));
  });
});
