import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import {
  analyzeShapeFormation,
  InvalidSfenError,
  ShapeFormationAnalysisError,
  type ShapeFormationResult,
} from "./shapeFormationAnalyzer.js";
import { DEFAULT_INITIAL_SFEN, replayMoveHistory } from "./moveHistory.js";

function findResult(results: ShapeFormationResult[], shapeId: string): ShapeFormationResult {
  const found = results.find((r) => r.shapeId === shapeId);
  if (!found) throw new Error(`shape not found in results: ${shapeId}`);
  return found;
}

// 本美濃(mino_honmino)の完成配置(2h玉・3h銀・4i金・5h金)を、指し手を経由せず
// 直接盤面へ配置したSFEN(「completedはformation_evidenceの有無を問わない」ことの検証用)。
function honminoCompletedSfen(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "2h", role: "king" },
    { square: "3h", role: "silver" },
    { square: "4i", role: "gold" },
    { square: "5h", role: "gold" },
  ];
  for (const { square, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color: "sente", role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("analyzeShapeFormation", () => {
  it("初期局面(1手も指していない): 4九金の偶然の一致だけではforming扱いにしない(status: none)", () => {
    const results = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    const honmino = findResult(results, "mino_honmino");

    // shape_match(静的な一致)としては4九金が一致していることは正しく検出する
    expect(honmino.matchedSquares).toContain("4i");
    // しかし指し手履歴が空なので、shape_formation_evidence(実際に動いた証拠)は無い
    expect(honmino.formationEvidence).toEqual([]);
    // その結果、プロダクト向けのstatusは"forming"ではなく"none"になる
    expect(honmino.status).toBe("none");
  });

  it("required_piecesが1個だけ偶然一致する局面: 他のshapeも同様にnone扱いになる", () => {
    const results = analyzeShapeFormation(DEFAULT_INITIAL_SFEN, []);
    for (const result of results) {
      if (result.matchedSquares.length > 0 && result.formationEvidence.length === 0) {
        expect(result.status).toBe("none");
      }
    }
  });

  it("Shape形成へ向かう手が複数観測される局面: 実際に動いた駒だけがformation_evidenceに載り、status: forming", () => {
    // 銀(3i->3h)・金(6i->5h、斜め前へ)を実際に動かす。どちらも本美濃囲いの必須マスへの移動。
    // 相手(gote)の手は無関係な手でよい(findMoveEvidenceはperspectiveColor=senteの手しか見ない)。
    const moveHistory = ["3i3h", "3c3d", "6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);

    const results = analyzeShapeFormation(finalSfen, moveHistory);
    const honmino = findResult(results, "mino_honmino");

    expect(honmino.matchedSquares.sort()).toEqual(["3h", "4i", "5h"]);
    expect(honmino.missingSquares).toEqual(["2h"]);
    // 実際に動かした2枚(3h銀・5h金)がformation_evidenceに載る。
    // 4i金は動いていない(偶然の一致のまま)ためformation_evidenceには含まれない。
    const evidencedSquares = honmino.formationEvidence.map((e) => e.square).sort();
    expect(evidencedSquares).toEqual(["3h", "5h"]);
    expect(honmino.formationEvidence.find((e) => e.square === "3h")?.evidence.moveUsi).toBe("3i3h");
    expect(honmino.formationEvidence.find((e) => e.square === "5h")?.evidence.moveUsi).toBe("6i5h");
    expect(honmino.status).toBe("forming");
  });

  it("Shapeが完成した局面: formation_evidenceが無くても(直接配置でも)completedと判定する", () => {
    const sfen = honminoCompletedSfen();
    const results = analyzeShapeFormation(sfen, [], { initialSfen: sfen });
    const honmino = findResult(results, "mino_honmino");

    expect(honmino.status).toBe("completed");
    expect(honmino.missingSquares).toEqual([]);
    // completedはevidenceの有無を問わない設計であることの確認(このケースでは実際に0件)。
    expect(honmino.formationEvidence).toEqual([]);
  });

  it("Shapeとは無関係な局面: どのshapeも forming/completed にならない", () => {
    const moveHistory = ["1g1f", "3c3d", "2g2f", "8c8d"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const results = analyzeShapeFormation(finalSfen, moveHistory);

    for (const result of results) {
      expect(result.status).toBe("none");
    }
  });

  it("不正なSFENに対してInvalidSfenErrorを投げる", () => {
    expect(() => analyzeShapeFormation("not-a-valid-sfen", [])).toThrow(InvalidSfenError);
  });

  it("sfenとmoveHistoryの組み合わせが矛盾している場合、ShapeFormationAnalysisErrorを投げる", () => {
    expect(() => analyzeShapeFormation(DEFAULT_INITIAL_SFEN, ["7g7f"])).toThrow(ShapeFormationAnalysisError);
  });

  it("同じ入力に対して常に同じ結果を返す(決定的)", () => {
    const moveHistory = ["3i3h", "3c3d", "6i5h"];
    const { finalSfen } = replayMoveHistory(moveHistory, DEFAULT_INITIAL_SFEN);
    const first = analyzeShapeFormation(finalSfen, moveHistory);
    const second = analyzeShapeFormation(finalSfen, moveHistory);
    expect(second).toEqual(first);
  });
});
