// I-10(結果、draft)のテスト。2026-09-12 の人間決定
// (docs/STEP_5-E_PLAN_2026-09-12.md A-4)。
// 局面の組み立て方は i8-band-piece-then-captured.test.ts と同じ
// (両玉を置いたうえで指定した駒を並べ、detectBoardEvents が実際に動く合法な局面を使う)。

import { Board } from "shogiops/board";
import { Hands } from "shogiops/hands";
import { makeSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import type { Color, Role } from "shogiops/types";
import { describe, expect, it } from "vitest";
import type { ReachablePlanBody, StateResponseBodyWithPlan } from "../../../apps/server/src/api/stateResponse.js";
import { i10EscapeSquareNotShown } from "./i10-escape-square-not-shown.js";
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
 * その歩を「移動先で」取れる(= I-8/I-10が対象にする形)。 */
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
    // STEP 5-F(A-3): ③の背景解析の状態。この土台は③について何も言わないため
    // "pending"(まだ計算していない)を既定にする。
    focusTextState: "pending",
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

function baseResponse(
  sfen: string,
  planOverrides: Partial<ReachablePlanBody>,
  escapeSquareThreats: string[] = [],
): StateResponseBodyWithPlan {
  return {
    sfen,
    moveHistory: [],
    status: { isEnd: false, outcome: undefined },
    coach: undefined,
    legalMoves: [],
    escapeSquareThreats,
    moveHistoryJapanese: [],
    plan: { ...basePlan(), ...planOverrides },
  };
}

/** 帯([0])が squares の駒を名指ししているプラン。 */
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

function makePreviousRecord(
  ply: number,
  sfen: string,
  planOverrides: Partial<ReachablePlanBody>,
  escapeSquareThreats?: string[],
): RecordLine {
  const response = baseResponse(sfen, planOverrides, escapeSquareThreats ?? []);
  if (escapeSquareThreats === undefined) {
    // フィールドが無い古い記録を再現する(意図的にプロパティ自体を削除する)。
    delete (response as { escapeSquareThreats?: string[] }).escapeSquareThreats;
  }
  return {
    kind: "record",
    ply,
    sfen,
    senteMove: null,
    goteMove: null,
    phase: "ready",
    elapsedMs: 0,
    response,
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

describe("I-10 escape square not shown", () => {
  it("発火する: escapeSquareThreatsフィールドが無い古い記録(情報が無かったとして検出)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]), undefined);
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    const findings = i10EscapeSquareNotShown.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.ply).toBe(30);
    expect(findings[0]?.condition).toBe("band");
    expect(findings[0]?.detail).toContain("5e");
    expect(findings[0]?.detail).toContain("示していません");
  });

  it("発火しない: escapeSquareThreatsに当該手が含まれている(画面が示していた)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]), ["5f5e"]);
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    expect(i10EscapeSquareNotShown.check([previous, current])).toEqual([]);
  });

  it("発火しない: escapeSquareThreatsが空配列で、当該手を含まない他の手だけがある", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]), []);
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    // 空配列であっても、I-8と同じ選定条件を満たす手であれば検出する
    // (「情報が無かった」の一種。含まれていないことに変わりはない)。
    expect(i10EscapeSquareNotShown.check([previous, current])).toHaveLength(1);
  });

  it("発火しない: I-8が発火しない行(帯が名指ししていない駒を動かした)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["9i"]), undefined);
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    expect(i10EscapeSquareNotShown.check([previous, current])).toEqual([]);
  });

  it("発火しない: I-8が発火しない行(帯が名指しした駒を動かしたが取られていない)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(28, sfen, bandPlan(["5f"]), undefined);
    const current = makeCurrentRecord(30, sfen, "5f5e", "1a2a");

    expect(i10EscapeSquareNotShown.check([previous, current])).toEqual([]);
  });

  it("発火しない: 直前のready行(t-2)が無い", () => {
    const sfen = buildMoveThenCapturedSfen();
    const current = makeCurrentRecord(2, sfen, "5f5e", "5d5e");

    expect(i10EscapeSquareNotShown.check([current])).toEqual([]);
  });

  it("重なり: 同じ手が候補手にも載っていれば condition は candidate(I-8と同じ挙動)", () => {
    const sfen = buildMoveThenCapturedSfen();
    const previous = makePreviousRecord(
      28,
      sfen,
      {
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
      },
      undefined,
    );
    const current = makeCurrentRecord(30, sfen, "5f5e", "5d5e");

    const findings = i10EscapeSquareNotShown.check([previous, current]);

    expect(findings).toHaveLength(1);
    expect(findings[0]?.condition).toBe("candidate");
  });
});
