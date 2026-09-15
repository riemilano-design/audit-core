// STEP D2.5(docs/STEP_D2.5_PLAN_2026-09-15.md §4 の P-10)。評価 1 つの形勢の状態と、組の状態の並び。**エンジンは起動しない。**
//
// 【正解の置き方】期待は計画書 4. の表のまま手で書いた(実装の出力から写さない)。
// 【この試験が確かめないこと】Failure Event・diagnosis-moment の行への配線(lib/failureEvent.test.ts・lib/diagnosisMoment.test.ts)。

import { describe, expect, it } from "vitest";
import type { Evaluation } from "./failureEvent.js";
import { standingOf, standingPairOf, type StandingBounds } from "./standing.js";

const BOUNDS: StandingBounds = { aheadCp: 300, behindCp: -300 };
const measured = (scoreCp: number | null, mate: number | null = null): Evaluation => ({
  state: "measured",
  scoreCp,
  mate,
  bestmove: null,
  afterPassScoreCp: null,
  afterPassMate: null,
  dropCp: null,
});

describe("standingOf(計画 §1 の M-5)", () => {
  it("P-10: +300 / +299 / −299 / −300 / mate +3 / mate −1 / mate 0 / measured でない 5 状態", () => {
    const table: Array<[Evaluation, unknown]> = [
      [measured(300), "ahead"],
      [measured(299), "level"],
      [measured(-299), "level"],
      [measured(-300), "behind"],
      [measured(null, 3), "ahead"],
      [measured(null, -1), "behind"],
      [measured(null, 0), { undetermined: "mateZero" }],
      [{ state: "notMeasuredGameEnd" }, { undetermined: "notMeasuredGameEnd" }],
      [{ state: "notMeasuredInCheck" }, { undetermined: "notMeasuredInCheck" }],
      [{ state: "notMeasurable" }, { undetermined: "notMeasurable" }],
      [{ state: "unrecorded" }, { undetermined: "unrecorded" }],
      [{ state: "notEvaluation" }, { undetermined: "notEvaluation" }],
    ];
    expect(table.map(([evaluation]) => standingOf(evaluation, BOUNDS))).toStrictEqual(table.map(([, standing]) => standing));
  });

  it("境は呼び出し側が渡した値で分ける(+300 / −300 に決め打ちしない): 境 ±200 なら +250 は ahead、−250 は behind", () => {
    const narrow: StandingBounds = { aheadCp: 200, behindCp: -200 };
    expect([standingOf(measured(250), narrow), standingOf(measured(-250), narrow), standingOf(measured(250), BOUNDS)]).toStrictEqual(["ahead", "behind", "level"]);
  });

  it("measured で scoreCp も mate も null の評価は黙って level にせず例外(evaluationOf は notMeasurable にするので、本番では来ない)", () => {
    expect(() => standingOf(measured(null, null), BOUNDS)).toThrow("measured の評価に scoreCp も mate も無い");
  });
});

describe("standingPairOf(計画 §1 の M-6)", () => {
  it("直前と直後の状態を並べるだけ(判定語は持たない): +700 → +200 は ahead → level、+100 → 測っていない は level → undetermined", () => {
    expect(standingPairOf(measured(700), measured(200), BOUNDS)).toStrictEqual({ before: "ahead", after: "level" });
    expect(standingPairOf(measured(100), { state: "unrecorded" }, BOUNDS)).toStrictEqual({ before: "level", after: { undetermined: "unrecorded" } });
  });
});
