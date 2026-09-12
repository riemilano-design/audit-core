// STEP U6-L(docs/STEP_U6-L_PLAN_2026-09-13.md 3.5)。読み筋の観測を数える純粋関数のテスト。
// 将棋の判断は一切しない。数え方だけを固定する。

import { describe, expect, it } from "vitest";
import type { SearchPvObservation } from "../../../apps/server/src/analysis/searchPv.js";
import type { RecordLine } from "../invariants/types.js";
import { countSearchPvs, pvLengthBucket } from "./searchPvStats.js";

const SFEN = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";

function observation(overrides: Partial<SearchPvObservation> = {}): SearchPvObservation {
  return {
    source: "focus_baseline",
    sfen: SFEN,
    moveUsi: null,
    multipv: 1,
    scoreCp: 0,
    mate: null,
    pv: ["7g7f", "3c3d"],
    lowerbound: false,
    upperbound: false,
    ...overrides,
  };
}

/** searchPvs の欄を持つ / 持たない ready 行を作る。
 * 欄を持たない行は、U6-L より前に取った古い記録を再現する(意図的にキーを作らない)。 */
function readyRecord(searchPvs: SearchPvObservation[] | null | undefined): RecordLine {
  const record = {
    kind: "record",
    ply: 2,
    sfen: SFEN,
    senteMove: "7g7f",
    goteMove: "3c3d",
    phase: "ready",
    elapsedMs: 0,
    response: {} as RecordLine["response"],
  } as RecordLine;
  if (searchPvs !== undefined) record.searchPvs = searchPvs;
  return record;
}

function immediateRecord(): RecordLine {
  return { ...readyRecord([observation()]), phase: "immediate" };
}

describe("pvLengthBucket", () => {
  it("区切りは 0 / 1 / 2 / 3 / 4-9 / 10+", () => {
    expect([0, 1, 2, 3, 4, 9, 10, 40].map(pvLengthBucket)).toEqual([
      "0",
      "1",
      "2",
      "3",
      "4-9",
      "4-9",
      "10+",
      "10+",
    ]);
  });
});

describe("countSearchPvs", () => {
  it("source 別・長さ別に数える", () => {
    const stats = countSearchPvs([
      readyRecord([
        observation({ source: "focus_baseline", pv: ["7g7f"] }),
        observation({ source: "focus_after_pass", pv: [] }),
        observation({ source: "candidate_baseline", pv: ["1a1b", "2a2b", "3a3b", "4a4b"] }),
        observation({ source: "candidate_after_move", moveUsi: "7g7f", pv: new Array(12).fill("7g7f") }),
      ]),
    ]);

    expect(stats.observations).toBe(4);
    expect(stats.bySource).toEqual({
      focus_baseline: 1,
      focus_after_pass: 1,
      candidate_baseline: 1,
      candidate_after_move: 1,
    });
    expect(stats.byLength).toEqual({ "0": 1, "1": 1, "2": 0, "3": 0, "4-9": 1, "10+": 1 });
    expect(stats.emptyPv).toBe(1);
  });

  it("3つの状態を別々に数える: 欄なし(古い記録) / null(測れなかった) / 空配列(測って0本)", () => {
    const stats = countSearchPvs([
      readyRecord(undefined),
      readyRecord(null),
      readyRecord([]),
      readyRecord([observation()]),
    ]);

    expect(stats.rowsWithoutField).toBe(1);
    expect(stats.rowsFailed).toBe(1);
    expect(stats.rowsWithEmptyField).toBe(1);
    expect(stats.rowsWithField).toBe(2);
    expect(stats.observations).toBe(1);
  });

  it("null の行は「欄あり」にも「空配列」にも数えない(測れなかったことと0本を混ぜない)", () => {
    const stats = countSearchPvs([readyRecord(null)]);

    expect(stats.rowsFailed).toBe(1);
    expect(stats.rowsWithField).toBe(0);
    expect(stats.rowsWithEmptyField).toBe(0);
  });

  it("lowerbound / upperbound を数える", () => {
    const stats = countSearchPvs([
      readyRecord([
        observation({ lowerbound: true }),
        observation({ upperbound: true }),
        observation(),
      ]),
    ]);

    expect(stats.lowerbound).toBe(1);
    expect(stats.upperbound).toBe(1);
  });

  it("multipv が 2 以上の本数を数える(0 でなければ計画書 2.1 の読みが誤り)", () => {
    const stats = countSearchPvs([readyRecord([observation({ multipv: 1 }), observation({ multipv: 2 })])]);

    expect(stats.multipvAtLeast2).toBe(1);
  });

  it("immediate 行は数えない(探索していないため)", () => {
    const stats = countSearchPvs([immediateRecord()]);

    expect(stats.rowsWithField).toBe(0);
    expect(stats.rowsWithoutField).toBe(0);
    expect(stats.observations).toBe(0);
  });
});
