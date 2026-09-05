import { describe, expect, it } from "vitest";
import {
  explainMoveOutcome,
  explainMoveOutcomeFact,
  NO_NOTABLE_CHANGE_TEXT,
} from "./moveOutcomeExplanation.js";
import type { MoveOutcome, MoveOutcomeFact, MoveOutcomeFactKind } from "./moveOutcomeDetector.js";

function makeFact(kind: MoveOutcomeFactKind, overrides: Partial<MoveOutcomeFact> = {}): MoveOutcomeFact {
  return {
    kind,
    targetSquare: overrides.targetSquare ?? null,
    targetPiece: overrides.targetPiece ?? null,
    remainingStepsBefore: overrides.remainingStepsBefore ?? null,
    remainingStepsAfter: overrides.remainingStepsAfter ?? null,
    blockingSquare: overrides.blockingSquare ?? null,
    candidateKind: overrides.candidateKind ?? null,
    cause: overrides.cause ?? null,
  };
}

const ALL_KINDS: MoveOutcomeFactKind[] = [
  "target_shape_changed",
  "played_candidate",
  "played_non_candidate",
  "square_completed",
  "square_lost",
  "route_advanced",
  "route_completed",
  "route_lost",
  "route_lengthened",
  "route_first_move_unavailable",
  "route_first_move_available",
  "preparation_required",
  "preparation_resolved",
  "route_assignee_changed",
];

describe("explainMoveOutcomeFact", () => {
  it("1. 経路の完成を、マス目の日本語表記で説明する", () => {
    const message = explainMoveOutcomeFact(
      makeFact("route_completed", { targetSquare: "7h", targetPiece: "銀", remainingStepsAfter: 0 }),
    );

    expect(message.text).toBe("この手で銀が７八に入り、この道のりは終わりました。");
  });

  it("2. 経路の進行を、残り手数つきで説明する", () => {
    const message = explainMoveOutcomeFact(
      makeFact("route_advanced", {
        targetSquare: "8h",
        targetPiece: "玉",
        remainingStepsBefore: 3,
        remainingStepsAfter: 2,
      }),
    );

    expect(message.text).toBe("玉を８八へ運ぶ道のりが、残り3手から残り2手になりました。");
  });

  it("3. 準備手が必要になったことを、塞いでいるマスつきで説明する", () => {
    const message = explainMoveOutcomeFact(
      makeFact("preparation_required", { targetSquare: "7g", targetPiece: "桂", blockingSquare: "7g" }),
    );

    expect(message.text).toBe("桂を７七へ進めるには、先に７七にある自分の駒を動かす必要が出てきました。");
  });

  it("4. 準備手が不要になったことを説明する(どのマスが空いたかは断定しない)", () => {
    const message = explainMoveOutcomeFact(
      makeFact("preparation_resolved", { targetSquare: "7g", targetPiece: "桂", blockingSquare: "7g" }),
    );

    expect(message.text).toBe("桂を７七へ進めるのに、先に他の駒を動かす必要はなくなりました。");
  });

  it("4-2. 準備手が不要になった理由(どのマスが空いたか)を断定しない", () => {
    // 準備手が不要になる理由は「塞いでいた駒がどいた」だけでなく「経路自体が
    // 別ルートに変わった」場合もあり、後者ではそのマスは空いていない。
    // したがって文言はblockingSquareに依存してはならない。
    const movedAway = explainMoveOutcomeFact(
      makeFact("preparation_resolved", { targetSquare: "7h", targetPiece: "銀", blockingSquare: "7f" }),
    );
    const routeChanged = explainMoveOutcomeFact(
      makeFact("preparation_resolved", { targetSquare: "7h", targetPiece: "銀", blockingSquare: "8g" }),
    );

    expect(movedAway.text).toBe(routeChanged.text);
    expect(movedAway.text).not.toContain("空");
    expect(movedAway.text).not.toContain("７六");
    expect(routeChanged.text).not.toContain("８七");
  });

  it("5. causeが確定している場合のみ、原因の文言を添える", () => {
    const withCause = explainMoveOutcomeFact(
      makeFact("route_lost", { targetSquare: "7h", targetPiece: "銀", cause: "candidate_piece_captured" }),
    );
    const withoutCause = explainMoveOutcomeFact(
      makeFact("route_lost", { targetSquare: "7h", targetPiece: "銀" }),
    );

    expect(withCause.text).toContain("予定していた駒が、相手の手によって取られました。");
    // causeがnullの場合は原因に一切触れない(推測しない)。
    expect(withoutCause.text).toBe("銀を７八へ運ぶ道のりが、今の局面では続けられなくなりました。");
  });

  it("6. 候補手だったかどうかを、種類に応じて言い分ける", () => {
    expect(explainMoveOutcomeFact(makeFact("played_candidate", { candidateKind: "route_step" })).text).toBe(
      "この手は、直前に表示していた候補手の一つです。",
    );
    expect(explainMoveOutcomeFact(makeFact("played_candidate", { candidateKind: "preparation" })).text).toBe(
      "この手は、直前に表示していた準備手の候補の一つです。",
    );
    expect(explainMoveOutcomeFact(makeFact("played_non_candidate")).text).toBe(
      "この手は、直前に表示していた候補手には含まれていませんでした。",
    );
  });

  it("7. どの種類の説明も、評価語やエンジン評価値を含まない", () => {
    const forbidden = ["最善", "おすすめ", "安全", "悪手", "形勢", "評価値", "cp", "正解です", "良い手"];

    for (const kind of ALL_KINDS) {
      const fact = makeFact(kind, {
        targetSquare: "7h",
        targetPiece: "銀",
        blockingSquare: "7g",
        remainingStepsBefore: 2,
        remainingStepsAfter: 1,
        candidateKind: "route_step",
        cause: "candidate_piece_captured",
      });
      const { text } = explainMoveOutcomeFact(fact);

      expect(text.length, kind).toBeGreaterThan(0);
      for (const word of forbidden) {
        expect(text, `${kind} / ${word}`).not.toContain(word);
      }
    }
  });

  it("8. 同じ入力に対しては常に同じ結果を返す(決定的)", () => {
    const fact = makeFact("route_advanced", {
      targetSquare: "8h",
      targetPiece: "玉",
      remainingStepsBefore: 3,
      remainingStepsAfter: 2,
    });

    expect(explainMoveOutcomeFact(fact)).toEqual(explainMoveOutcomeFact(fact));
  });
});

describe("explainMoveOutcome", () => {
  it("9. 事実が無い場合は「特に大きな変化はありませんでした」を1件返す(無言にしない)", () => {
    const outcome: MoveOutcome = { playedMoveUsi: "1g1f", opponentMoveUsi: "1c1d", facts: [] };

    const messages = explainMoveOutcome(outcome);

    expect(messages).toEqual([{ kind: "no_notable_change", text: NO_NOTABLE_CHANGE_TEXT }]);
  });

  it("10. 事実の順序をそのまま保ってメッセージに変換する", () => {
    const outcome: MoveOutcome = {
      playedMoveUsi: "7i7h",
      opponentMoveUsi: "1c1d",
      facts: [
        makeFact("played_candidate", { candidateKind: "route_step" }),
        makeFact("route_completed", { targetSquare: "7h", targetPiece: "銀" }),
      ],
    };

    const messages = explainMoveOutcome(outcome);

    expect(messages.map((m) => m.kind)).toEqual(["played_candidate", "route_completed"]);
  });
});
