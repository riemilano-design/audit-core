// STEP FILL 作業 X(docs/STEP_FILL_PLAN_2026-09-22.md §2)。evaluationOf が checkBaseline を読む規則を見張る。
// **エンジンは起動しない**(record を直接組み立てるだけ)。既存の evaluationOf の試験(engineReference を読む側)は
// failureEvent.test.ts にあり、ここでは触らない。

import { describe, expect, it } from "vitest";
import type { CheckBaseline } from "./checkBaseline.js";
import { evaluationOf, NOT_EVALUATION_CP } from "./failureEvent.js";
import type { RecordLine } from "../invariants/types.js";

/** 5七の後手の飛車が、5九の先手玉に王手をかけている局面(王手中・非終局)。apps/server/src/rules/gameStatus.test.ts と同じ構成。 */
const SENTE_IN_CHECK_SFEN = "4k4/9/9/9/9/9/4r4/9/4K4 b - 1";

function checkRecord(fields: { engineReference?: null; checkBaseline?: CheckBaseline | null }): RecordLine {
  const record = {
    kind: "record",
    ply: 2,
    sfen: SENTE_IN_CHECK_SFEN,
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 0,
    response: {} as RecordLine["response"],
    engineReference: fields.engineReference === undefined ? null : fields.engineReference,
  } as RecordLine;
  if ("checkBaseline" in fields) record.checkBaseline = fields.checkBaseline;
  return record;
}

describe("evaluationOf: checkBaseline(STEP FILL 作業 X)", () => {
  it("engineReference が null・王手中・checkBaseline に値があれば measured(afterPass 側・dropCp は null)", () => {
    const record = checkRecord({ checkBaseline: { scoreCp: -700, mate: null, bestmove: "5i5h", nodes: 4_000_000 } });
    expect(evaluationOf(record)).toEqual({
      state: "measured",
      scoreCp: -700,
      mate: null,
      bestmove: "5i5h",
      afterPassScoreCp: null,
      afterPassMate: null,
      dropCp: null,
    });
  });

  it("mate の checkBaseline も measured として読む", () => {
    const record = checkRecord({ checkBaseline: { scoreCp: null, mate: -2, bestmove: null, nodes: 4_000_000 } });
    expect(evaluationOf(record)).toEqual({
      state: "measured",
      scoreCp: null,
      mate: -2,
      bestmove: null,
      afterPassScoreCp: null,
      afterPassMate: null,
      dropCp: null,
    });
  });

  it("checkBaseline の欄が無い(古い記録・王手中でない行・referenceNodes 0)行は notMeasuredInCheck のまま", () => {
    const record = checkRecord({});
    expect(evaluationOf(record)).toEqual({ state: "notMeasuredInCheck" });
  });

  it("checkBaseline が null(王手中で測ろうとして測れなかった)行も notMeasuredInCheck のまま", () => {
    const record = checkRecord({ checkBaseline: null });
    expect(evaluationOf(record)).toEqual({ state: "notMeasuredInCheck" });
  });

  it("checkBaseline.scoreCp と mate が両方 null なら notMeasurable(standing.ts の例外を防ぐ)", () => {
    const record = checkRecord({ checkBaseline: { scoreCp: null, mate: null, bestmove: null, nodes: 4_000_000 } });
    expect(evaluationOf(record)).toEqual({ state: "notMeasurable" });
  });

  it("|scoreCp| >= NOT_EVALUATION_CP の checkBaseline は notEvaluation(engineReference と同じ扱い ― 計画 §2)", () => {
    const record = checkRecord({ checkBaseline: { scoreCp: NOT_EVALUATION_CP, mate: null, bestmove: null, nodes: 4_000_000 } });
    expect(evaluationOf(record)).toEqual({ state: "notEvaluation" });
    const negative = checkRecord({ checkBaseline: { scoreCp: -NOT_EVALUATION_CP, mate: null, bestmove: null, nodes: 4_000_000 } });
    expect(evaluationOf(negative)).toEqual({ state: "notEvaluation" });
  });
});
