// I-8(結果、draft)のテスト。2026-09-12 の人間決定(帯を adviceSource に足す)。
// 局面の組み立て方は i6-advice-then-loss.test.ts と同じ
// (両玉を置いたうえで指定した駒を並べ、detectBoardEvents が実際に動く合法な局面を使う)。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i8BandPieceThenCaptured } from "./i8-band-piece-then-captured.js";
import type { RecordLine } from "./types.js";

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

/** 先手の歩を5f、後手の歩を5dに置く。先手が5f5eと動かすと、後手は5d5eで
 * その歩を「移動先で」取れる(= I-8が対象にする形)。 */
function buildMoveThenCapturedSfen(): string {
  return buildSfen([
    { square: "5f", color: "sente", role: "pawn" },
    { square: "5d", color: "gote", role: "pawn" },
  ]);
}

function basePlan(): ReachablePlanBody {
  return {
    reachableShapes: [],
    routes: [],
    targetShapeProgress: null,
    candidateMoveLabels: {},
    lastMoveOutcome: null,
    nextConsiderations: [],
    candidateMoveState: "unavailable",
    candidateMove: undefined,
    pendingReviewNote: null,
    resolvedTargetShapeId: null,
    shapeWeakness: null,
    urgentMessages: [],
    referenceShapes: [],
    directionNote: null,
    planChanged: false,
    planChangeReason: null,
  };
}

function baseResponse(sfen: string, planOverrides: Partial<ReachablePlanBody>): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    // STEP 5-E(S-2): StateResponseBodyWithPlan に必須で足された欄。
    // 判定には使わないため、この土台では空配列にする。
    escapeSquareThreats: [],
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

/** 帯([0])が squares の駒を名指ししているプラン。text は本番と同じ体裁の固定文
 * (このテストの入力であり、画面に出る文言を新しく決めるものではない)。 */
function bandPlan(squares: string[]): Partial<ReachablePlanBody> {
  return {
    urgentMessages: squares.map((square) => ({
      kind: "piece_attacked",
      text: `あなたの${square}の駒に、相手の駒が当たっています(次の相手の手で取られる可能性があります)。`,
      square,
      attackerSquares: [],
    })) as unknown as ReachablePlanBody["urgentMessages"],
  };
}

function makePreviousRecord(ply: number, sfen: string, planOverrides: Partial<ReachablePlanBody>): RecordLine {
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response: baseResponse(sfen, planOverrides),
  };
}

function makeCurrentRecord(ply: number, sfen: string, senteMove: string, goteMove: string): RecordLine {
  return {
    kind: "record",
    ply,
    sfen,
    senteMove,
    goteMove,
    phase: "ready",
    elapsedMs: 0,
    response: baseResponse(sfen, {}),
  };
}

describe("I-8 band piece then captured", () => {
  it("発火する: 帯が名指しした駒を動かし、その直後に移動先で取られた", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]));
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    const findings = i8BandPieceThenCaptured.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.ply).toBe(30);
    expect(findings[0]?.condition).toBe("band");
    expect(findings[0]?.detail).toContain("5e");
  });

  it("発火する: 帯が2件を名指ししていても、動かした駒がそのうちの1つなら対象", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["9i", "5f"]));
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    expect(i8BandPieceThenCaptured.check([previous, current])).toHaveLength(1);
  });

  it("発火しない: 帯が名指ししていない駒を動かした", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["9i"]));
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    expect(i8BandPieceThenCaptured.check([previous, current])).toEqual([]);
  });

  it("発火しない: 帯が名指しした駒を動かしたが、取られていない", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]));
    const current = makeCurrentRecord(30, sfen, "5f5e", "1a2a");

    expect(i8BandPieceThenCaptured.check([previous, current])).toEqual([]);
  });

  it("発火しない: 帯が空(名指しが無い)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, {});
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    expect(i8BandPieceThenCaptured.check([previous, current])).toEqual([]);
  });

  it("発火しない: 直前のready行(t-2)が無い", () => {
    const sfen = buildMoveThenCapturedSfen();
    const current = makeCurrentRecord(2, sfen, "5f5e", "5d5e");

    expect(i8BandPieceThenCaptured.check([current])).toEqual([]);
  });

  it("重なり: 同じ手が候補手にも載っていれば condition は candidate(bandで隠さない)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, {
      ...bandPlan(["5f"]),
      candidateMoveState: "ready",
      candidateMove: {
        status: "ready",
        notReadyReason: null,
        explanations: [
          {
            id: "e1",
            stage: "candidate_move",
            purpose: "p",
            move: "5f5e",
            reason: "r",
            refers_to_shape_id: null,
            refers_to_intent_id: null,
            confidence_level: "low",
            glossary_terms: [],
            template_id: "t",
          },
        ],
        sharedNotes: [],
      },
    });
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    const findings = i8BandPieceThenCaptured.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("candidate");
  });
});
