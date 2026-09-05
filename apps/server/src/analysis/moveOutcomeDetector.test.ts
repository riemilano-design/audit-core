// moveOutcomeDetector.ts(Phase6 Unit2)のテスト。
// スナップショットは実データ(data/shapes/*.json)と実際の局面から、
// shapeFormationAnalyzer.ts / routePlanner.ts の出力をそのまま使って組み立てる
// (手作りの値ではなく、実際に本番で流れるのと同じ材料で固定する)。

import { Board } from "shogiops/board";
import { Hand, Hands } from "shogiops/hands";
import { makeSfen, parseSfen } from "shogiops/sfen";
import { Shogi } from "shogiops/variant/shogi";
import { parseSquareName } from "shogiops/util";
import { describe, expect, it } from "vitest";
import { detectMoveOutcome, type MoveOutcomeSnapshot } from "./moveOutcomeDetector.js";
import { analyzeShapeFormation } from "./shapeFormationAnalyzer.js";
import { planRoutesToShape } from "./routePlanner.js";
import { applyMove } from "../rules/applyMove.js";

const INITIAL_SFEN = makeSfen(parseSfen("standard", "startpos").unwrap());

function snapshot(
  sfen: string,
  history: string[],
  shapeId: string,
  initialSfen = INITIAL_SFEN,
): MoveOutcomeSnapshot {
  const results = analyzeShapeFormation(sfen, history, { initialSfen });
  const shapeResult = results.find((r) => r.shapeId === shapeId);
  const plan = planRoutesToShape(sfen, results, shapeId);
  return {
    targetShapeId: shapeId,
    matchedSquares: shapeResult?.matchedSquares ?? [],
    routes: plan.routes,
    candidateMoves: plan.candidateMoves,
  };
}

/** ユーザーの手 → 相手の手 を適用し、着手前後のスナップショットを返す。 */
function playPair(
  sfen: string,
  history: string[],
  shapeId: string,
  userMove: string,
  opponentMove: string,
  initialSfen = INITIAL_SFEN,
) {
  const before = snapshot(sfen, history, shapeId, initialSfen);
  const afterUser = applyMove(sfen, userMove);
  const afterOpponent = applyMove(afterUser, opponentMove);
  const nextHistory = [...history, userMove, opponentMove];
  const after = snapshot(afterOpponent, nextHistory, shapeId, initialSfen);
  return { before, after, sfen: afterOpponent, history: nextHistory };
}

function kinds(facts: { kind: string }[]): string[] {
  return facts.map((f) => f.kind);
}

/** 玉8h・金6i・金5hが揃い、7h(銀)だけが未達成。銀は6gの1枚のみで、相手の桂が7eにいる。 */
function silverCaptureFixture(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; color: "sente" | "gote"; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "8h", color: "sente", role: "king" },
    { square: "6i", color: "sente", role: "gold" },
    { square: "5h", color: "sente", role: "gold" },
    { square: "6g", color: "sente", role: "silver" },
    { square: "1g", color: "sente", role: "pawn" },
    { square: "7e", color: "gote", role: "knight" },
  ];
  for (const { square, color, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color, role });
  }
  const pos = Shogi.from({ board, hands: Hands.empty(), turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

/** 玉7i・銀7h・金6i・金5h。あと7i8hで本美濃が完成する。相手は持ち駒に飛車1枚。 */
function rookDropFixture(): string {
  let board = Board.empty();
  const pieces: Array<{ square: string; role: Parameters<typeof board.set>[1]["role"] }> = [
    { square: "7i", role: "king" },
    { square: "7h", role: "silver" },
    { square: "6i", role: "gold" },
    { square: "5h", role: "gold" },
    { square: "1g", role: "pawn" },
  ];
  for (const { square, role } of pieces) {
    const sq = parseSquareName(square);
    if (sq === undefined) throw new Error(`invalid square: ${square}`);
    board = board.clone();
    board.set(sq, { color: "sente", role });
  }
  const hands = Hands.from(Hand.empty(), Hand.from([["rook", 1]]));
  const pos = Shogi.from({ board, hands, turn: "sente", moveNumber: 1 }, false).unwrap();
  return makeSfen(pos);
}

describe("detectMoveOutcome", () => {
  it("1. 候補手を指して目標マスが完成した場合、played_candidateとroute_completedを返す", () => {
    // 初期局面で7i7h(銀を7hへ)は候補手であり、この手で本美濃の7hが完成する。
    const { before, after } = playPair(INITIAL_SFEN, [], "mino_honmino", "7i7h", "1c1d");

    const outcome = detectMoveOutcome(before, after, "7i7h", "1c1d");

    expect(kinds(outcome.facts)).toContain("played_candidate");
    expect(kinds(outcome.facts)).toContain("route_completed");
    const completed = outcome.facts.find((f) => f.kind === "route_completed");
    expect(completed?.targetSquare).toBe("7h");
    expect(completed?.targetPiece).toBe("銀");
    expect(completed?.remainingStepsAfter).toBe(0);
    // 経路があった目標マスの完成はroute_completedだけで表し、二重に報告しない。
    expect(kinds(outcome.facts)).not.toContain("square_completed");
    expect(kinds(outcome.facts)).not.toContain("route_lost");
  });

  it("2. 候補外の手を指した場合、played_non_candidateだけを返し他の事実を作らない", () => {
    const { before, after } = playPair(INITIAL_SFEN, [], "mino_honmino", "1g1f", "1c1d");

    const outcome = detectMoveOutcome(before, after, "1g1f", "1c1d");

    expect(kinds(outcome.facts)).toEqual(["played_non_candidate"]);
  });

  it("3. 経路の1手目を指した場合、route_advancedになり route_assignee_changed は出ない", () => {
    // 玉8hの経路は 5i→6h→7h→8h。5i6hで残り3手→2手になるが、担当は同じ玉のまま。
    const { before, after } = playPair(INITIAL_SFEN, [], "mino_honmino", "5i6h", "1c1d");

    const outcome = detectMoveOutcome(before, after, "5i6h", "1c1d");

    const advanced = outcome.facts.find((f) => f.kind === "route_advanced");
    expect(advanced?.targetSquare).toBe("8h");
    expect(advanced?.remainingStepsBefore).toBe(3);
    expect(advanced?.remainingStepsAfter).toBe(2);
    // fromSquareは5i→6hに変わるが、これは同じ玉が進んだだけであり担当変更ではない。
    expect(kinds(outcome.facts)).not.toContain("route_assignee_changed");
  });

  it("4. 経路上の駒が相手に取られた場合、route_lostになりcauseに確定分類が入る", () => {
    const sfen = silverCaptureFixture();
    const { before, after } = playPair(sfen, [], "mino_honmino", "1g1f", "7e6g", sfen);

    const outcome = detectMoveOutcome(before, after, "1g1f", "7e6g", "candidate_piece_captured");

    const lost = outcome.facts.find((f) => f.kind === "route_lost");
    expect(lost?.targetSquare).toBe("7h");
    expect(lost?.targetPiece).toBe("銀");
    expect(lost?.cause).toBe("candidate_piece_captured");
    // 完成ではないので、route_completedにはならない。
    expect(kinds(outcome.facts)).not.toContain("route_completed");
  });

  it("5. 経路の1手目が指せなくなった場合、route_first_move_unavailableになる", () => {
    const sfen = rookDropFixture();
    const { before, after } = playPair(sfen, [], "mino_honmino", "1g1f", "R*8a", sfen);

    const outcome = detectMoveOutcome(before, after, "1g1f", "R*8a", "candidate_move_illegal_due_to_check");

    const unavailable = outcome.facts.find((f) => f.kind === "route_first_move_unavailable");
    expect(unavailable?.targetSquare).toBe("8h");
    expect(unavailable?.cause).toBe("candidate_move_illegal_due_to_check");
    // 経路自体は残っている(玉は7iのまま)ので、route_lostにはしない。
    expect(kinds(outcome.facts)).not.toContain("route_lost");
  });

  it("6. 塞いでいた自分の駒がどいた場合、preparation_resolvedになる", () => {
    // 高美濃の桂7gは、初期局面では自分の歩(7g)に塞がれている。7g7fでその歩がどく。
    const { before, after } = playPair(INITIAL_SFEN, [], "mino_takamino", "7g7f", "1c1d");

    const outcome = detectMoveOutcome(before, after, "7g7f", "1c1d");

    const resolved = outcome.facts.find((f) => f.kind === "preparation_resolved");
    expect(resolved?.targetSquare).toBe("7g");
    expect(resolved?.targetPiece).toBe("桂");
    expect(resolved?.blockingSquare).toBe("7g");
    // 1手目が指せるようになったことも同時に事実として出る。
    expect(kinds(outcome.facts)).toContain("route_first_move_available");
  });

  it("7. 目標形が変わった場合、target_shape_changedだけを返し形・経路の差分を一切出さない", () => {
    const before = snapshot(INITIAL_SFEN, [], "mino_honmino");
    const after = snapshot(INITIAL_SFEN, [], "mino_ginkanmuri");

    const outcome = detectMoveOutcome(before, after, "7i7h", "1c1d");

    expect(kinds(outcome.facts)).toEqual(["target_shape_changed"]);
    // 形ごとに必須マスが違うため、比較すると誤った「崩れた」等の事実になる。
    expect(kinds(outcome.facts)).not.toContain("square_lost");
    expect(kinds(outcome.facts)).not.toContain("route_lost");
  });

  it("8. 相手の応手で特筆すべき変化がない場合、経路に関する事実を1件も作らない", () => {
    // 一度指した後の局面から、さらに無関係な手を指す(経路には何も起きない)。
    const first = playPair(INITIAL_SFEN, [], "mino_honmino", "1g1f", "1c1d");
    const { before, after } = playPair(first.sfen, first.history, "mino_honmino", "9g9f", "1d1e");

    const outcome = detectMoveOutcome(before, after, "9g9f", "1d1e");

    expect(kinds(outcome.facts)).toEqual(["played_non_candidate"]);
  });

  it("9. 直前に候補手が1件も無かった場合、候補手だったかどうかに言及しない", () => {
    const before: MoveOutcomeSnapshot = {
      targetShapeId: "mino_honmino",
      matchedSquares: [],
      routes: [],
      candidateMoves: [],
    };
    const after: MoveOutcomeSnapshot = { ...before };

    const outcome = detectMoveOutcome(before, after, "1g1f", "1c1d");

    expect(outcome.facts).toEqual([]);
  });

  it("10. planChangeReasonが\"unknown\"の場合、原因を断定せずcause: nullにする", () => {
    const sfen = silverCaptureFixture();
    const { before, after } = playPair(sfen, [], "mino_honmino", "1g1f", "7e6g", sfen);

    const outcome = detectMoveOutcome(before, after, "1g1f", "7e6g", "unknown");

    expect(outcome.facts.find((f) => f.kind === "route_lost")?.cause).toBeNull();
  });

  it("11. planChangeReasonが渡されない場合もcause: nullで、事実だけを返す", () => {
    const sfen = silverCaptureFixture();
    const { before, after } = playPair(sfen, [], "mino_honmino", "1g1f", "7e6g", sfen);

    const outcome = detectMoveOutcome(before, after, "1g1f", "7e6g");

    expect(outcome.facts.find((f) => f.kind === "route_lost")?.cause).toBeNull();
  });

  it("12. 相手が応手していない場合(opponentMoveUsi: null)もそのまま扱える", () => {
    const before = snapshot(INITIAL_SFEN, [], "mino_honmino");

    const outcome = detectMoveOutcome(before, before, "1g1f", null);

    expect(outcome.opponentMoveUsi).toBeNull();
    expect(outcome.playedMoveUsi).toBe("1g1f");
  });

  it("13. 同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    const { before, after } = playPair(INITIAL_SFEN, [], "mino_honmino", "7i7h", "1c1d");

    expect(detectMoveOutcome(before, after, "7i7h", "1c1d")).toEqual(
      detectMoveOutcome(before, after, "7i7h", "1c1d"),
    );
  });
});
