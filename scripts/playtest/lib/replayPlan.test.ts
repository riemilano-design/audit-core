// STEP D0-SIDE 段 1(docs/STEP_D0-SIDE_PLAN_2026-09-15.md の F-S9・F-S9a の (i)(ii)(iv-a)(v))。
// **期待値は試験を回す前に手で書いた**(規則 11.1)。手順は短い平手の出だしと、手で作った 1 手詰の局面だけで、実棋譜は使わない。
// meta の形(司令塔の決定): `trailingMoveTruncated` を常に持ち、`truncatedTrailingMove` は true のときだけ持つ。null は使わない。
// **欄が無いことと undefined の欄を区別するため、toStrictEqual で比べる**(toEqual は undefined の欄を無視する)。

import { describe, expect, it } from "vitest";

import { applyMove } from "../../../apps/server/src/rules/applyMove.js";
import { isGameOver } from "../../../apps/server/src/rules/gameStatus.js";
import { actualContinuation } from "./failureEvent.js";
import { planReplayMoves, truncationMetaFields } from "./replayPlan.js";

describe("planReplayMoves(R-8)", () => {
  it("F-S9a (i): 手数が偶数なら何も落とさず、trailingMoveTruncated は false で、落とした手の欄を持たない", () => {
    expect(Object.hasOwn(planReplayMoves(["7g7f", "3c3d"]), "truncatedTrailingMove")).toBe(false);
    expect(planReplayMoves(["7g7f", "3c3d", "2g2f", "8c8d"])).toStrictEqual({
      kind: "replay",
      moves: ["7g7f", "3c3d", "2g2f", "8c8d"],
      trailingMoveTruncated: false,
    });
  });

  it("F-S9・F-S9a (ii): 手数が奇数なら最後の 1 手だけを落とし、落とした手を返す(最初の手は残る。再生する手数は偶数)", () => {
    const plan = planReplayMoves(["7g7f", "3c3d", "2g2f", "8c8d", "2f2e"]);
    expect(plan).toStrictEqual({ kind: "replay", moves: ["7g7f", "3c3d", "2g2f", "8c8d"], trailingMoveTruncated: true, truncatedTrailingMove: "2f2e" });
    // replay.ts は ply 0 に 1 本と 2 手ごとに 1 本の ready 行を書くので、5 手の棋譜は (5 − 1) / 2 + 1 = 3 本になる(計画 F-S9。本数は段 R の記録で見る)
    if (plan.kind === "replay") expect(plan.moves.length / 2 + 1).toBe(3);
  });

  it("入力の配列を書き換えない", () => {
    const moves = ["7g7f", "3c3d", "2g2f"];
    planReplayMoves(moves);
    expect(moves).toStrictEqual(["7g7f", "3c3d", "2g2f"]);
  });

  it("F-S9a (iv-a): 元が 1 手だけの局は、落とすと 0 手なので再生しない(no_moves_to_replay。落とした手は残す)", () => {
    expect(planReplayMoves(["7g7f"])).toStrictEqual({
      kind: "noMovesToReplay",
      reason: "no_moves_to_replay",
      trailingMoveTruncated: true,
      truncatedTrailingMove: "7g7f",
    });
  });

  it("手数 0 の棋譜も再生しない(落とした手は無い)", () => {
    expect(planReplayMoves([])).toStrictEqual({ kind: "noMovesToReplay", reason: "no_moves_to_replay", trailingMoveTruncated: false });
  });
});

describe("truncationMetaFields(R-3。meta に書く欄)", () => {
  it("落とさなかったときは trailingMoveTruncated: false の欄だけを持ち、落とした手の欄を持たない(null も undefined の欄も作らない)", () => {
    const fields = truncationMetaFields(planReplayMoves(["7g7f", "3c3d"]));
    expect(fields).toStrictEqual({ trailingMoveTruncated: false });
    expect(Object.keys(fields)).toStrictEqual(["trailingMoveTruncated"]);
    expect(Object.hasOwn(fields, "truncatedTrailingMove")).toBe(false);
    expect(JSON.stringify(fields)).toBe('{"trailingMoveTruncated":false}');
  });

  it("落としたときは trailingMoveTruncated: true と落とした手の USI を持つ", () => {
    const fields = truncationMetaFields(planReplayMoves(["7g7f", "3c3d", "2g2f"]));
    expect(fields).toStrictEqual({ trailingMoveTruncated: true, truncatedTrailingMove: "2g2f" });
    expect(JSON.stringify(fields)).toBe('{"trailingMoveTruncated":true,"truncatedTrailingMove":"2g2f"}');
  });
});

describe("R-8 の限界(計画 3.1。F-S9a (v))", () => {
  // 手で作った局面: 先手の玉 9i・持ち駒の金、後手の玉 5a・歩 1a、先手の歩 5c。
  // 9i9h(先手)→ 1a1b(後手)→ G*5b(先手)で後手の玉が詰む(金は 5c の歩が守り、逃げ場 4a・6a・4b・6b はどれも金が利く)。
  const START = "4k3p/9/4P4/9/9/9/9/9/K8 b G 1";
  const MOVES = ["9i9h", "1a1b", "G*5b"];

  it("前提: この手順は合法で、最後の G*5b で終局する(手で導いた局面を rules/ で確かめる)", () => {
    const afterTwo = applyMove(applyMove(START, MOVES[0]!), MOVES[1]!);
    expect(isGameOver(afterTwo)).toBe(false);
    expect(isGameOver(applyMove(afterTwo, MOVES[2]!))).toBe(true);
  });

  it("落とした手が詰ませた手なら、元の手順では窓の中で終局するのに、落とした手順では「窓が足りない」になる", () => {
    const plan = planReplayMoves(MOVES);
    expect(plan).toStrictEqual({ kind: "replay", moves: ["9i9h", "1a1b"], trailingMoveTruncated: true, truncatedTrailingMove: "G*5b" });
    if (plan.kind !== "replay") return;
    expect(actualContinuation(MOVES, 1, 5, START)).toStrictEqual({ checks: [], mate: null, windowPlies: 5, windowShort: false });
    expect(actualContinuation(plan.moves, 1, 5, START)).toStrictEqual({ checks: [], mate: null, windowPlies: 5, windowShort: true });
  });
});
